from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.domain import EventDraft
from app.services.event_store import EventStoreCorruption, JsonlEventStore
from app.services.orchestrator import Orchestrator
from app.services.runtime import DeterministicRuntime


def test_event_store_builds_and_verifies_hash_chain(tmp_path: Path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl")
    first = store.append(
        EventDraft(
            type="test.started",
            actor="tester",
            summary="First immutable event",
            timestamp=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )
    )
    second = store.append(
        EventDraft(
            type="test.completed",
            actor="tester",
            summary="Second immutable event",
            timestamp=datetime(2026, 7, 14, 0, 1, tzinfo=timezone.utc),
        )
    )

    assert first.sequence == 1
    assert second.sequence == 2
    assert second.previous_hash == first.hash
    assert store.verify().valid is True
    assert JsonlEventStore(store.path).verify().event_count == 2


def test_event_store_rejects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)
    store.append(
        EventDraft(type="test.event", actor="tester", summary="Untampered event")
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    record["summary"] = "Tampered event"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(EventStoreCorruption, match="hash mismatch"):
        JsonlEventStore(path)


def test_seeded_run_is_byte_for_byte_deterministic(tmp_path: Path) -> None:
    hashes: list[list[str]] = []
    for index in range(2):
        store = JsonlEventStore(tmp_path / f"events-{index}.jsonl")
        orchestrator = Orchestrator(store, DeterministicRuntime())
        orchestrator.bootstrap_seeded_run()
        hashes.append([event.hash for event in store.all()])

    assert hashes[0] == hashes[1]
    assert len(hashes[0]) >= 20
