from __future__ import annotations

import fcntl
import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, TextIO

from pydantic import ValidationError

from app.models.domain import ChainState, EventDraft, StoredEvent


GENESIS_HASH = "0" * 64


class EventStoreCorruption(RuntimeError):
    """Raised when the on-disk event chain cannot be verified."""


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _event_payload(event: StoredEvent) -> dict[str, Any]:
    return event.model_dump(mode="json", exclude={"hash"})


class JsonlEventStore:
    """Thread-safe append-only JSONL store protected by a SHA-256 hash chain.

    The file is the source of truth. Every event includes the prior event hash,
    allowing a judge or client to independently verify ordering and tampering.
    """

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._events = self._load()
        self._verify_or_raise(self._events)

    @staticmethod
    def _load_handle(handle: TextIO) -> list[StoredEvent]:
        events: list[StoredEvent] = []
        try:
            handle.seek(0)
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    events.append(StoredEvent.model_validate_json(line))
                except (ValidationError, ValueError) as exc:
                    raise EventStoreCorruption(
                        f"invalid event at line {line_number}: {exc}"
                    ) from exc
        except UnicodeDecodeError as exc:
            raise EventStoreCorruption("event log is not valid UTF-8") from exc
        return events

    def _load(self) -> list[StoredEvent]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                return self._load_handle(handle)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _accept_verified(self, events: list[StoredEvent]) -> list[StoredEvent]:
        """Accept a verified reload only when the cached append-only prefix remains."""
        self._verify_or_raise(events)
        if len(events) < len(self._events):
            raise EventStoreCorruption("event log was truncated")
        if any(
            previous.hash != current.hash
            for previous, current in zip(self._events, events, strict=False)
        ):
            raise EventStoreCorruption("verified event history changed on disk")
        self._events = events
        return events

    def _reload_verified(self) -> list[StoredEvent]:
        """Reload the source-of-truth journal and fail before exposing corrupt data."""
        return self._accept_verified(self._load())

    @staticmethod
    def _verify_or_raise(events: Iterable[StoredEvent]) -> None:
        previous_hash = GENESIS_HASH
        expected_sequence = 1
        for event in events:
            if event.sequence != expected_sequence:
                raise EventStoreCorruption(
                    f"sequence {event.sequence} does not follow {expected_sequence - 1}"
                )
            if event.previous_hash != previous_hash:
                raise EventStoreCorruption(
                    f"event {event.id} does not reference the prior hash"
                )
            expected_hash = _hash_payload(_event_payload(event))
            if event.hash != expected_hash:
                raise EventStoreCorruption(f"event {event.id} hash mismatch")
            previous_hash = event.hash
            expected_sequence += 1

    def append(self, draft: EventDraft) -> StoredEvent:
        with self._lock:
            # Verification and append share one OS-level exclusive lock. This
            # prevents separate store instances or workers from issuing the same
            # sequence number after observing an identical head.
            with self.path.open("a+", encoding="utf-8") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    self._accept_verified(self._load_handle(handle))
                    sequence = len(self._events) + 1
                    previous_hash = (
                        self._events[-1].hash if self._events else GENESIS_HASH
                    )
                    timestamp = draft.timestamp or datetime.now(timezone.utc)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    else:
                        timestamp = timestamp.astimezone(timezone.utc)

                    identity_material = "|".join(
                        (
                            str(sequence),
                            draft.run_id or "global",
                            draft.type,
                            draft.actor,
                            draft.summary,
                        )
                    )
                    event_id = "evt_" + hashlib.sha256(
                        identity_material.encode("utf-8")
                    ).hexdigest()[:16]
                    unhashed = StoredEvent(
                        sequence=sequence,
                        id=event_id,
                        run_id=draft.run_id,
                        objective_id=draft.objective_id,
                        timestamp=timestamp,
                        type=draft.type,
                        actor=draft.actor,
                        summary=draft.summary,
                        data=draft.data,
                        previous_hash=previous_hash,
                        hash=GENESIS_HASH,
                    )
                    event = unhashed.model_copy(
                        update={"hash": _hash_payload(_event_payload(unhashed))}
                    )
                    serialized = json.dumps(
                        event.model_dump(mode="json"),
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    handle.seek(0, os.SEEK_END)
                    handle.write(serialized + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    self._events.append(event)
                    return event
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def all(self) -> list[StoredEvent]:
        with self._lock:
            return list(self._reload_verified())

    def query(
        self,
        *,
        run_id: str | None = None,
        objective_id: str | None = None,
        event_type: str | None = None,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> list[StoredEvent]:
        with self._lock:
            verified_events = self._reload_verified()
            events = (
                event
                for event in verified_events
                if event.sequence > after_sequence
                and (run_id is None or event.run_id == run_id)
                and (objective_id is None or event.objective_id == objective_id)
                and (event_type is None or event.type == event_type)
            )
            return list(events)[:limit]

    def verify(self) -> ChainState:
        with self._lock:
            try:
                self._reload_verified()
            except EventStoreCorruption:
                return ChainState(
                    valid=False,
                    head_hash=self._events[-1].hash if self._events else GENESIS_HASH,
                    event_count=len(self._events),
                )
            return ChainState(
                valid=True,
                head_hash=self._events[-1].hash if self._events else GENESIS_HASH,
                event_count=len(self._events),
            )
