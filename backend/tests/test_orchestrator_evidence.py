from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from app.models.domain import ObjectiveCreate, StoredEvent
from app.services import orchestrator as orchestrator_module
from app.services.event_store import JsonlEventStore
from app.services.orchestrator import DomainConflict, Orchestrator
from app.services.runtime import (
    DeterministicRuntime,
    DiffNumstat,
    GitDiffMetadata,
    RuntimeCommand,
    RuntimeResult,
)


class LiveEvidenceRuntime:
    name = "codex"
    implementation_model = "gpt-5.5"
    reviewer_model = "gpt-5.5"
    apply_changes = True

    timeout_seconds = 30

    def __init__(
        self,
        *,
        verified: bool,
        workdir: Path,
        declared_command: str = "pytest -q backend/tests/test_pulse.py",
        implementation_thread_id: str | None = "thread_impl_verified",
        review_thread_id: str | None = "thread_review_verified",
        review_write_mode: bool = False,
        review_provenance: str = "live",
    ) -> None:
        self.verified = verified
        self.workdir = workdir
        self.declared_command = declared_command
        self.implementation_thread_id = implementation_thread_id
        self.review_thread_id = review_thread_id
        self.review_write_mode = review_write_mode
        self.review_provenance = review_provenance

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult:
        if not self.verified:
            return RuntimeResult(
                runtime="codex",
                provenance="live",
                summary="Codex returned without executable change evidence.",
                change_id="codex_unverified",
                write_mode=True,
                thread_id="thread_impl_unverified",
                model=self.implementation_model,
            )
        return RuntimeResult(
            runtime="codex",
            provenance="live",
            summary="Codex implemented and checked a bounded API change.",
            change_id="codex_verified",
            write_mode=True,
            thread_id=self.implementation_thread_id,
            requested_model=self.implementation_model,
            observed_model=None,
            model=self.implementation_model,
            invocation_argv=[
                "/usr/bin/codex",
                "exec",
                "--json",
                "--model",
                self.implementation_model,
                "-",
            ],
            codex_version="codex-cli 0.144.5",
            input_tokens=120,
            output_tokens=48,
            commands=[
                RuntimeCommand(
                    id="cmd_tests",
                    command=self.declared_command,
                    status="completed",
                    exit_code=0,
                )
            ],
            diff=GitDiffMetadata(
                name_only=["backend/app/pulse.py", "backend/tests/test_pulse.py"],
                numstat=[
                    DiffNumstat(path="backend/app/pulse.py", additions=8, deletions=0),
                    DiffNumstat(
                        path="backend/tests/test_pulse.py", additions=12, deletions=0
                    ),
                ],
                sha256="a" * 64,
                preview="+def pulse():\n+    return {'status': 'ok'}",
            ),
            final_message="Implemented the endpoint and its contract test.",
            raw_event_count=9,
        )

    def review(self, *, brief: str, run_id: str, diff_context: str) -> RuntimeResult:
        return RuntimeResult(
            runtime="codex",
            provenance=self.review_provenance,
            summary="Codex reviewer approved the bounded change.",
            change_id="review_verified",
            write_mode=self.review_write_mode,
            thread_id=self.review_thread_id,
            requested_model=self.reviewer_model,
            observed_model=None,
            model=self.reviewer_model,
            invocation_argv=[
                "/usr/bin/codex",
                "exec",
                "--json",
                "--model",
                self.reviewer_model,
                "-",
            ],
            codex_version="codex-cli 0.144.5",
            verdict="approved",
            final_message='{"verdict":"approved","findings":[]}',
            raw_event_count=4,
        )


def _worktree(tmp_path: Path) -> Path:
    worktree = tmp_path / "worktree"
    backend = worktree / "backend"
    backend.mkdir(parents=True)
    (backend / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-q"\n', encoding="utf-8"
    )
    return worktree


def _run(
    tmp_path: Path, *, verified: bool, **runtime_options: object
) -> tuple[Orchestrator, str]:
    worktree = _worktree(tmp_path)
    orchestrator = Orchestrator(
        JsonlEventStore(tmp_path / "events.jsonl"),
        LiveEvidenceRuntime(
            verified=verified,
            workdir=worktree,
            **runtime_options,
        ),
    )
    orchestrator.bootstrap_company()
    objective = orchestrator.create_objective(
        ObjectiveCreate(
            title="Add a typed backend API endpoint",
            description="Implement one bounded FastAPI contract.",
            acceptance_criteria=["A focused pytest check exits successfully"],
        )
    )
    orchestrator.execute_objective(objective)
    return orchestrator, objective.run_id


def _install_sentinel_runner(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int,
    stdout: bytes = b"1 passed",
    stderr: bytes = b"",
) -> list[tuple[list[str], dict[str, object]]]:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(argv: list[str], **kwargs: object) -> CompletedProcess[bytes]:
        calls.append((argv, kwargs))
        return CompletedProcess(argv, returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(orchestrator_module.subprocess, "run", fake_run)
    return calls


def test_live_run_requires_and_preserves_structured_codex_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sentinel_runner(monkeypatch, returncode=0)
    orchestrator, run_id = _run(tmp_path, verified=True)

    detail = orchestrator.run_detail(run_id)
    assert detail.run.status == "completed"
    generated = next(event for event in detail.events if event.type == "code.generated")
    assert generated.data["provenance"] == "live"
    assert generated.data["thread_id"] == "thread_impl_verified"
    assert generated.data["model"] == "gpt-5.5"
    assert generated.data["requested_model"] == "gpt-5.5"
    assert generated.data["observed_model"] is None
    assert generated.data["invocation_argv"] == [
        "/usr/bin/codex",
        "exec",
        "--json",
        "--model",
        "gpt-5.5",
        "-",
    ]
    assert generated.data["codex_version"] == "codex-cli 0.144.5"
    assert generated.data["diff"]["sha256"] == "a" * 64
    assert generated.data["commands"][0]["exit_code"] == 0

    review = next(event for event in detail.events if event.type == "review.completed")
    assert review.data["thread_id"] == "thread_review_verified"
    assert review.data["verdict"] == "approved"
    assert review.data["release_gate"]["eligible"] is True
    tests = next(event for event in detail.events if event.type == "tests.passed")
    outcome = tests.data["check_outcomes"][0]
    assert outcome["allowlist_id"] == "backend-pytest"
    assert outcome["executor"] == "sentinel"
    assert outcome["command_source"] == "static-allowlist"
    trusted_argv = [str(Path(sys.executable).resolve()), "-m", "pytest", "-q"]
    assert outcome["argv"] == trusted_argv
    assert outcome["shell"] is False
    assert outcome["exit_code"] == 0
    assert outcome["stdout"] == {
        "bytes": len(b"1 passed"),
        "sha256": hashlib.sha256(b"1 passed").hexdigest(),
    }
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == trusted_argv
    assert kwargs["shell"] is False
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["cwd"] == tmp_path / "worktree" / "backend"
    assert "OPENAI_API_KEY" not in kwargs["env"]
    monitor = next(event for event in detail.events if event.type == "monitor.healthy")
    escrow_releases = [
        event
        for event in detail.events
        if event.type == "ledger.transaction"
        and event.data["from_agent"] == "escrow"
    ]
    assert escrow_releases
    assert all(event.sequence > monitor.sequence for event in escrow_releases)
    assert all(
        monitor.id in event.data["source_event_ids"]
        for event in escrow_releases
    )
    assert any(event.type == "changelog.written" for event in detail.events)
    assert not any(event.type == "pull_request.opened" for event in detail.events)


def test_live_run_without_diff_and_successful_checks_is_blocked(
    tmp_path: Path,
) -> None:
    orchestrator, run_id = _run(tmp_path, verified=False)

    detail = orchestrator.run_detail(run_id)
    assert detail.run.status == "failed"
    assert any(event.type == "tests.unverified" for event in detail.events)
    assert not any(event.type == "deployment.succeeded" for event in detail.events)
    assert any(
        transaction.kind == "penalty"
        for transaction in orchestrator.ledger().transactions
        if transaction.run_id == run_id
    )
    assert orchestrator.ledger().conserved is True


def test_escrow_stays_locked_until_version_matched_health_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = _deterministic_orchestrator(tmp_path)
    original_append = orchestrator._append

    def append_with_mismatched_health_version(**kwargs: object) -> StoredEvent:
        if kwargs.get("event_type") == "monitor.healthy":
            data = dict(kwargs.get("data") or {})
            data["version"] = "mismatched-version"
            kwargs["data"] = data
        return original_append(**kwargs)

    monkeypatch.setattr(
        orchestrator,
        "_append",
        append_with_mismatched_health_version,
    )
    objective = orchestrator.create_objective(
        ObjectiveCreate(title="Require health evidence before escrow release")
    )

    orchestrator.execute_objective(objective)

    detail = orchestrator.run_detail(objective.run_id)
    assert detail.run.status == "failed"
    assert detail.events[-1].data["reason"] == "healthy_release_evidence_missing"
    assert not any(
        event.type == "ledger.transaction"
        and event.data["kind"] == "payout"
        and event.data["from_agent"] == "escrow"
        for event in detail.events
    )
    assert any(
        event.type == "ledger.transaction"
        and event.data["kind"] == "refund"
        and event.data["from_agent"] == "escrow"
        for event in detail.events
    )


def test_sentinel_prefers_root_pyproject_for_target_shaped_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worktree = tmp_path / "misconception-debugger-worktree"
    (worktree / "backend").mkdir(parents=True)
    (worktree / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-q"\n', encoding="utf-8"
    )
    runtime = LiveEvidenceRuntime(verified=True, workdir=worktree)
    calls = _install_sentinel_runner(monkeypatch, returncode=0)

    outcomes = Orchestrator._sentinel_checks(
        runtime,
        runtime.generate(brief="Target-shaped check", run_id="run_target"),
    )

    assert outcomes[0]["status"] == "passed"
    assert outcomes[0]["cwd"] == str(worktree)
    assert calls[0][1]["cwd"] == worktree


def test_echo_pytest_cannot_substitute_for_sentinel_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sentinel_runner(
        monkeypatch,
        returncode=1,
        stdout=b"",
        stderr=b"2 failed",
    )
    orchestrator, run_id = _run(
        tmp_path,
        verified=True,
        declared_command="echo pytest",
    )

    detail = orchestrator.run_detail(run_id)
    assert detail.run.status == "failed"
    generated = next(event for event in detail.events if event.type == "code.generated")
    assert generated.data["commands"][0]["command"] == "echo pytest"
    unverified = next(
        event for event in detail.events if event.type == "tests.unverified"
    )
    outcome = unverified.data["check_outcomes"][0]
    assert outcome["argv"] == [
        str(Path(sys.executable).resolve()),
        "-m",
        "pytest",
        "-q",
    ]
    assert outcome["exit_code"] == 1
    assert outcome["status"] == "failed"
    assert outcome["stderr"]["sha256"] == hashlib.sha256(b"2 failed").hexdigest()
    assert len(calls) == 1
    assert calls[0][1]["shell"] is False
    assert not any(event.type == "deployment.succeeded" for event in detail.events)
    assert detail.events[-1].type == "run.failed"


@pytest.mark.parametrize(
    ("runtime_options", "expected_reason"),
    [
        (
            {"review_thread_id": "thread_impl_verified"},
            "review-reused-implementation-thread",
        ),
        ({"implementation_thread_id": None}, "implementation-thread-missing"),
        ({"review_thread_id": None}, "review-thread-missing"),
        ({"review_write_mode": True}, "review-not-read-only"),
        ({"review_provenance": "fixture"}, "review-provenance-not-live"),
    ],
)
def test_live_review_requires_independent_read_only_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime_options: dict[str, object],
    expected_reason: str,
) -> None:
    calls = _install_sentinel_runner(monkeypatch, returncode=0)
    orchestrator, run_id = _run(
        tmp_path,
        verified=True,
        **runtime_options,
    )

    detail = orchestrator.run_detail(run_id)
    assert detail.run.status == "failed"
    review = next(event for event in detail.events if event.type == "review.completed")
    assert review.data["approved"] is False
    assert expected_reason in review.data["release_gate"]["reasons"]
    assert any(event.type == "review.unverified" for event in detail.events)
    assert not any(event.type.startswith("tests.") for event in detail.events)
    assert not any(event.type == "deployment.succeeded" for event in detail.events)
    assert any(event.type == "agent.released" for event in detail.events)
    assert detail.events[-1].type == "run.failed"
    assert calls == []


def _deterministic_orchestrator(tmp_path: Path) -> Orchestrator:
    orchestrator = Orchestrator(
        JsonlEventStore(tmp_path / "events.jsonl"),
        DeterministicRuntime(),
    )
    orchestrator.bootstrap_company()
    return orchestrator


def _drain_agent(orchestrator: Orchestrator, agent_id: str) -> None:
    balance = orchestrator.ledger().balances[agent_id]
    orchestrator._ledger_event(
        kind="clawback",
        amount=balance,
        reason="Adversarial test balance depletion",
        from_agent=agent_id,
        to_agent="treasury",
    )


def test_no_eligible_bidder_terminally_fails_and_releases_agents(
    tmp_path: Path,
) -> None:
    orchestrator = _deterministic_orchestrator(tmp_path)
    for engineer_id in ("forge", "prism", "rivet"):
        _drain_agent(orchestrator, engineer_id)
    objective = orchestrator.create_objective(
        ObjectiveCreate(title="Implement one bounded generic change")
    )

    orchestrator.execute_objective(objective)

    detail = orchestrator.run_detail(objective.run_id)
    assert detail.run.status == "failed"
    assert detail.events[-1].type == "run.failed"
    assert detail.events[-1].data["reason"] == "no_eligible_bidder"
    assert not any(event.type == "auction.awarded" for event in detail.events)
    assert not any(event.type == "deployment.succeeded" for event in detail.events)
    assert {
        event.data["agent_id"]
        for event in detail.events
        if event.type == "agent.released"
    } == {
        "atlas",
        "forge",
        "prism",
        "rivet",
    }
    ledger = orchestrator.ledger()
    assert ledger.conserved is True
    assert min(ledger.balances.values()) >= 0
    projected = {agent.id: agent for agent in orchestrator.agents().items}
    assert all(agent.current_task is None for agent in projected.values())
    assert {projected[item].status for item in ("forge", "prism", "rivet")} == {
        "dormant"
    }

    event_count = len(orchestrator.store.all())
    orchestrator.execute_objective(objective)
    assert len(orchestrator.store.all()) == event_count


def test_zero_balance_bidders_pay_no_fee_and_remain_dormant(
    tmp_path: Path,
) -> None:
    orchestrator = _deterministic_orchestrator(tmp_path)
    _drain_agent(orchestrator, "forge")
    _drain_agent(orchestrator, "prism")
    objective = orchestrator.create_objective(
        ObjectiveCreate(title="Implement one bounded generic change")
    )

    orchestrator.execute_objective(objective)

    detail = orchestrator.run_detail(objective.run_id)
    assert detail.run.status == "completed"
    run_transactions = [
        item
        for item in orchestrator.ledger().transactions
        if item.run_id == objective.run_id and item.kind == "bid_fee"
    ]
    assert {item.from_agent for item in run_transactions} == {"rivet"}
    skipped = [event for event in detail.events if event.type == "ledger.debit_skipped"]
    assert {event.data["from_agent"] for event in skipped} == {"forge", "prism"}
    ledger = orchestrator.ledger()
    assert ledger.conserved is True
    assert min(ledger.balances.values()) >= 0
    projected = {agent.id: agent for agent in orchestrator.agents().items}
    assert projected["forge"].status == "dormant"
    assert projected["prism"].status == "dormant"


def test_raw_ledger_transfer_rejects_overdraft_without_appending(
    tmp_path: Path,
) -> None:
    orchestrator = _deterministic_orchestrator(tmp_path)
    balance = orchestrator.ledger().balances["forge"]
    count = len(orchestrator.store.all())

    with pytest.raises(DomainConflict, match="would overdraw forge"):
        orchestrator._ledger_event(
            kind="bid_fee",
            amount=balance + 1,
            reason="Malformed oversized fee",
            from_agent="forge",
            to_agent="treasury",
        )

    assert len(orchestrator.store.all()) == count
    assert orchestrator.ledger().balances["forge"] == balance


def test_incident_penalty_is_capped_at_zero_in_api_ledger(
    tmp_path: Path,
) -> None:
    orchestrator = Orchestrator(
        JsonlEventStore(tmp_path / "events.jsonl"),
        DeterministicRuntime(),
    )
    orchestrator.bootstrap_seeded_run()
    run = orchestrator.run_detail("run_seed_self_hosting_v1")
    awarded = next(event for event in run.events if event.type == "auction.awarded")
    winner = str(awarded.data["winner"])
    balance = orchestrator.ledger().balances[winner]
    orchestrator._ledger_event(
        kind="clawback",
        amount=balance - 2,
        reason="Adversarial test leaves two credits",
        from_agent=winner,
        to_agent="treasury",
    )

    orchestrator.inject_regression(
        "run_seed_self_hosting_v1",
        reason="Exercise capped incident liability",
        error_rate=0.2,
    )

    ledger = orchestrator.ledger()
    assert ledger.balances[winner] == 0
    assert min(ledger.balances.values()) >= 0
    incident_penalty = next(
        item
        for item in reversed(ledger.transactions)
        if item.from_agent == winner
        and item.kind == "penalty"
        and item.reason.startswith("Implemented the regression")
    )
    assert incident_penalty.amount == 2
    projected = {agent.id: agent for agent in orchestrator.agents().items}
    assert projected[winner].status == "dormant"

    orchestrator.rollback(
        "run_seed_self_hosting_v1",
        reason="Restore before a repeated incident",
    )
    orchestrator.inject_regression(
        "run_seed_self_hosting_v1",
        reason="Repeat liability at zero balance",
        error_rate=0.2,
    )
    repeated_ledger = orchestrator.ledger()
    assert repeated_ledger.balances[winner] == 0
    assert min(repeated_ledger.balances.values()) >= 0
    assert any(
        event.type == "ledger.debit_skipped"
        and event.data["from_agent"] == winner
        and event.data["kind"] == "penalty"
        for event in orchestrator.store.all()
    )


def test_restart_reconciliation_fails_without_replaying_side_effects(
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "events.jsonl"
    original = Orchestrator(JsonlEventStore(event_path), DeterministicRuntime())
    original.bootstrap_company()
    objective = original.create_objective(
        ObjectiveCreate(title="Interrupted release candidate")
    )
    original._append(
        event_type="run.started",
        actor="orchestrator",
        summary="Run began before process interruption",
        run_id=objective.run_id,
        objective_id=objective.id,
    )
    original._ledger_event(
        kind="issue",
        amount=40,
        reason="Customer-funded objective budget",
        to_agent="atlas",
        run_id=objective.run_id,
        objective_id=objective.id,
    )
    original._ledger_event(
        kind="escrow",
        amount=40,
        reason="Delivery bounty locked before interruption",
        from_agent="atlas",
        to_agent="escrow",
        run_id=objective.run_id,
        objective_id=objective.id,
    )
    original._append(
        event_type="task.assigned",
        actor="atlas",
        summary="Forge received the interrupted task",
        run_id=objective.run_id,
        objective_id=objective.id,
        data={"agent_id": "forge", "assignee": "forge"},
    )
    interrupted_event_id = original.store.all()[-1].id

    restarted = Orchestrator(JsonlEventStore(event_path), DeterministicRuntime())
    appended = restarted.reconcile_interrupted_runs()

    detail = restarted.run_detail(objective.run_id)
    assert detail.run.status == "failed"
    assert detail.events[-1].type == "run.failed"
    assert detail.events[-1].data == {
        "reason": "startup_interrupted",
        "last_event_id": interrupted_event_id,
        "last_event_type": "task.assigned",
        "resumed": False,
    }
    assert any(
        event.type == "agent.released" and event.data["agent_id"] == "forge"
        for event in appended
    )
    assert any(
        event.type == "ledger.transaction"
        and event.data["kind"] == "refund"
        and event.data["amount"] == 40
        for event in appended
    )
    assert not any(event.type.startswith("deployment.") for event in detail.events)
    assert restarted._run_account_balance(objective.run_id, "escrow") == 0
    count = len(restarted.store.all())
    assert restarted.reconcile_interrupted_runs() == []
    assert len(restarted.store.all()) == count


def test_execute_objective_reconciles_existing_nonterminal_run(
    tmp_path: Path,
) -> None:
    orchestrator = _deterministic_orchestrator(tmp_path)
    objective = orchestrator.create_objective(
        ObjectiveCreate(title="Do not resume this interrupted run")
    )
    orchestrator._append(
        event_type="run.started",
        actor="orchestrator",
        summary="Interrupted before implementation",
        run_id=objective.run_id,
        objective_id=objective.id,
    )

    orchestrator.execute_objective(objective)

    detail = orchestrator.run_detail(objective.run_id)
    assert detail.run.status == "failed"
    assert detail.events[-1].data["reason"] == "startup_interrupted"
    assert not any(event.type == "runtime.invoked" for event in detail.events)
