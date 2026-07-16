from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
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


@pytest.mark.parametrize("read_method", ["all", "query"])
def test_existing_store_fails_closed_when_journal_is_tampered_before_read(
    tmp_path: Path,
    read_method: str,
) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)
    store.append(EventDraft(type="test.event", actor="tester", summary="Original"))
    record = json.loads(path.read_text(encoding="utf-8"))
    record["summary"] = "Changed on disk"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(EventStoreCorruption, match="hash mismatch"):
        getattr(store, read_method)()


def test_existing_store_fails_closed_when_journal_is_tampered_before_append(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)
    store.append(EventDraft(type="test.event", actor="tester", summary="Original"))
    record = json.loads(path.read_text(encoding="utf-8"))
    record["summary"] = "Changed on disk"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(EventStoreCorruption, match="hash mismatch"):
        store.append(EventDraft(type="test.second", actor="tester", summary="Blocked"))


def test_existing_store_rejects_valid_prefix_truncation(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)
    store.append(EventDraft(type="test.first", actor="tester", summary="First"))
    store.append(EventDraft(type="test.second", actor="tester", summary="Second"))
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    path.write_text(first_line + "\n", encoding="utf-8")

    with pytest.raises(EventStoreCorruption, match="truncated"):
        store.all()


def test_independent_store_instances_serialize_concurrent_appends(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    stores = [JsonlEventStore(path) for _ in range(4)]

    def append(index: int) -> int:
        event = stores[index % len(stores)].append(
            EventDraft(
                type="test.concurrent",
                actor=f"worker-{index}",
                summary=f"Concurrent append {index}",
            )
        )
        return event.sequence

    with ThreadPoolExecutor(max_workers=len(stores)) as executor:
        sequences = list(executor.map(append, range(24)))

    reloaded = JsonlEventStore(path)
    events = reloaded.all()
    assert sorted(sequences) == list(range(1, 25))
    assert [event.sequence for event in events] == list(range(1, 25))
    assert reloaded.verify().valid is True


def test_seeded_run_is_byte_for_byte_deterministic(tmp_path: Path) -> None:
    hashes: list[list[str]] = []
    for index in range(2):
        store = JsonlEventStore(tmp_path / f"events-{index}.jsonl")
        orchestrator = Orchestrator(store, DeterministicRuntime())
        orchestrator.bootstrap_seeded_run()
        hashes.append([event.hash for event in store.all()])

    assert hashes[0] == hashes[1]
    assert len(hashes[0]) >= 20
