from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models.domain import (
    Agent,
    AgentsResponse,
    ChainState,
    EventDraft,
    LedgerResponse,
    LedgerTransaction,
    Objective,
    ObjectiveCreate,
    ObjectiveStatus,
    PoliciesResponse,
    PolicyMechanism,
    PolicyProposal,
    PolicyStatus,
    Replay,
    ReplayFrame,
    RunDetail,
    RunStatus,
    RunSummary,
    StoredEvent,
)
from app.services.company import (
    ENGINEER_IDS,
    AgentStatus as CompanyAgentStatus,
    AuctionError,
    AuctionResult,
    AuctionTask,
    Bid,
    CredibilityEvidence,
    run_auction,
    seed_agents,
)
from app.services.event_store import JsonlEventStore
from app.services.runtime import DeterministicRuntime, RuntimeAdapter, RuntimeResult


SEED_OBJECTIVE_ID = "obj_seed_self_hosting_v1"
SEED_RUN_ID = "run_seed_self_hosting_v1"
SEED_TIME = datetime(2026, 7, 14, 3, 30, tzinfo=timezone.utc)
POLICY_BENCHMARK_ID = "deterministic-structural-control-coverage-v1"
POLICY_BENCHMARK_METRIC = "deterministic_structural_control_coverage"
POLICY_MECHANISM_KINDS = ("memory", "prompt", "routing", "economy")
BID_FEE = 1
SENTINEL_TEST_TIMEOUT_SECONDS = 120


AGENT_PROFILES = tuple(seed_agents().values())
AGENT_IDS = {profile.id for profile in AGENT_PROFILES}


class DomainNotFound(LookupError):
    pass


class DomainConflict(RuntimeError):
    pass


class Orchestrator:
    """Event-sourced deterministic delivery loop used by the API and demo."""

    def __init__(self, store: JsonlEventStore, runtime: RuntimeAdapter) -> None:
        self.store = store
        self.runtime = runtime
        self._run_lock = threading.RLock()

    def _append(
        self,
        *,
        event_type: str,
        actor: str,
        summary: str,
        run_id: str | None = None,
        objective_id: str | None = None,
        data: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> StoredEvent:
        return self.store.append(
            EventDraft(
                run_id=run_id,
                objective_id=objective_id,
                timestamp=timestamp,
                type=event_type,
                actor=actor,
                summary=summary,
                data=data or {},
            )
        )

    def _ledger_event(
        self,
        *,
        kind: str,
        amount: int,
        reason: str,
        from_agent: str | None = None,
        to_agent: str | None = None,
        run_id: str | None = None,
        objective_id: str | None = None,
        timestamp: datetime | None = None,
        source_event_ids: list[str] | None = None,
    ) -> StoredEvent:
        if amount <= 0:
            raise DomainConflict("ledger transaction amount must be positive")
        if from_agent is None and to_agent is None:
            raise DomainConflict("ledger transaction needs a source or destination")
        if from_agent is not None and from_agent == to_agent:
            raise DomainConflict(
                "ledger transaction cannot transfer to the same account"
            )
        if from_agent is not None:
            available = self.ledger().balances.get(from_agent, 0)
            if amount > available:
                raise DomainConflict(
                    f"ledger transaction would overdraw {from_agent}: "
                    f"available {available}, requested {amount}"
                )
        data: dict[str, Any] = {
            "kind": kind,
            "amount": amount,
            "reason": reason,
            "from_agent": from_agent,
            "to_agent": to_agent,
        }
        if source_event_ids:
            data["source_event_ids"] = source_event_ids
        return self._append(
            event_type="ledger.transaction",
            actor="ledger",
            summary=f"{kind.title()}: {amount} credits — {reason}",
            run_id=run_id,
            objective_id=objective_id,
            timestamp=timestamp,
            data=data,
        )

    def _run_account_balance(self, run_id: str, account: str) -> int:
        balance = 0
        for event in self.store.all():
            if event.run_id != run_id:
                continue
            if event.type != "ledger.transaction":
                continue
            amount = int(event.data["amount"])
            if event.data.get("from_agent") == account:
                balance -= amount
            if event.data.get("to_agent") == account:
                balance += amount
        if balance < 0:
            raise DomainConflict(
                f"run {run_id} contains an overdrawn {account} account"
            )
        return balance

    def _capped_debit_event(
        self,
        *,
        kind: str,
        amount: int,
        reason: str,
        from_agent: str,
        to_agent: str,
        run_id: str,
        objective_id: str | None,
        timestamp: datetime,
        allow_partial: bool,
    ) -> StoredEvent:
        if amount <= 0:
            raise DomainConflict("capped debit amount must be positive")
        available = self.ledger().balances.get(from_agent, 0)
        charged = min(amount, available) if allow_partial else amount
        if available < charged:
            charged = 0
        if charged == 0:
            return self._append(
                event_type="ledger.debit_skipped",
                actor="ledger",
                summary=f"Skipped {kind}: {from_agent} had no spendable credits",
                run_id=run_id,
                objective_id=objective_id,
                timestamp=timestamp,
                data={
                    "kind": kind,
                    "requested_amount": amount,
                    "reason": reason,
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "available": available,
                },
            )
        return self._ledger_event(
            kind=kind,
            amount=charged,
            reason=reason,
            from_agent=from_agent,
            to_agent=to_agent,
            run_id=run_id,
            objective_id=objective_id,
            timestamp=timestamp,
        )

    @staticmethod
    def _engaged_agent_ids(events: list[StoredEvent]) -> set[str]:
        engaged: set[str] = set()
        for event in events:
            if event.actor in AGENT_IDS:
                engaged.add(event.actor)
            for key in ("agent_id", "bidder", "assignee", "winner"):
                candidate = event.data.get(key)
                if isinstance(candidate, str) and candidate in AGENT_IDS:
                    engaged.add(candidate)
        return engaged

    def _append_agent_releases(
        self,
        *,
        run_id: str,
        objective_id: str | None,
        agent_ids: set[str],
        reason: str,
        timestamp_factory: Callable[[], datetime],
    ) -> list[StoredEvent]:
        released: list[StoredEvent] = []
        for profile in AGENT_PROFILES:
            if profile.id not in agent_ids:
                continue
            released.append(
                self._append(
                    event_type="agent.released",
                    actor="orchestrator",
                    summary=f"{profile.name} released from the terminal run",
                    run_id=run_id,
                    objective_id=objective_id,
                    timestamp=timestamp_factory(),
                    data={"agent_id": profile.id, "reason": reason},
                )
            )
        return released

    def _bootstrap_company(
        self, *, timestamp_factory: Callable[[], datetime]
    ) -> None:
        """Append missing company identity, memory, and balance events.

        Existing journals are migrated only by appending evidence. No historical
        event or hash is rewritten.
        """

        existing = self.store.all()
        registered = {
            str(event.data.get("agent_id"))
            for event in existing
            if event.type == "agent.registered"
        }
        genesis_balances = {
            str(event.data.get("to_agent"))
            for event in existing
            if event.type == "ledger.transaction"
            and event.data.get("kind") == "issue"
            and event.data.get("reason") == "Genesis operating balance"
        }
        seeded_memories = {
            (str(event.data.get("agent_id")), str(event.data.get("memory")))
            for event in existing
            if event.type == "memory.seeded"
        }

        for profile in AGENT_PROFILES:
            if profile.id not in registered:
                self._append(
                    event_type="agent.registered",
                    actor="orchestrator",
                    summary=f"{profile.name} joined the persistent company roster",
                    data={
                        "agent_id": profile.id,
                        "name": profile.name,
                        "role": profile.role,
                        "capabilities": list(profile.capabilities),
                        "personality": profile.personality,
                    },
                    timestamp=timestamp_factory(),
                )
            for memory in profile.memory_seed:
                if (profile.id, memory) in seeded_memories:
                    continue
                self._append(
                    event_type="memory.seeded",
                    actor="chronicle",
                    summary=f"Seeded durable operating memory for {profile.name}",
                    data={
                        "agent_id": profile.id,
                        "memory": memory,
                        "kind": "seed",
                        "references": [f"agent-profile:{profile.id}"],
                    },
                    timestamp=timestamp_factory(),
                )
            if profile.id not in genesis_balances:
                self._ledger_event(
                    kind="issue",
                    amount=profile.balance,
                    reason="Genesis operating balance",
                    to_agent=profile.id,
                    timestamp=timestamp_factory(),
                )

    def bootstrap_company(self) -> None:
        with self._run_lock:
            self._bootstrap_company(
                timestamp_factory=lambda: datetime.now(timezone.utc)
            )

    def bootstrap_seeded_run(self) -> None:
        """Create one fixed self-hosting run when the log is brand new."""
        with self._run_lock:
            if self.store.all():
                return
            tick = 0

            def seeded_time() -> datetime:
                nonlocal tick
                value = SEED_TIME + timedelta(seconds=tick * 20)
                tick += 1
                return value

            self._bootstrap_company(timestamp_factory=seeded_time)

            objective = Objective(
                id=SEED_OBJECTIVE_ID,
                title="Ship Dhurandhar's own monitored pulse endpoint",
                description=(
                    "Add a typed endpoint that exposes this service's release and "
                    "operational state, then test, review, deploy, and monitor it."
                ),
                acceptance_criteria=[
                    "GET /api/pulse returns HTTP 200 with release metadata",
                    "A contract test protects the response",
                    "The deployment is observed by Sentinel",
                ],
                priority="standard",
                status="queued",
                run_id=SEED_RUN_ID,
                created_at=seeded_time(),
            )
            self._append(
                event_type="objective.created",
                actor="human-customer",
                summary=objective.title,
                run_id=objective.run_id,
                objective_id=objective.id,
                timestamp=objective.created_at,
                data={
                    "title": objective.title,
                    "description": objective.description,
                    "acceptance_criteria": objective.acceptance_criteria,
                    "priority": objective.priority,
                },
            )
            self._execute_pipeline(
                objective,
                runtime=DeterministicRuntime(),
                timestamp_factory=seeded_time,
            )

    def create_objective(self, payload: ObjectiveCreate) -> Objective:
        now = datetime.now(timezone.utc)
        suffix = uuid4().hex[:12]
        objective = Objective(
            id=f"obj_{suffix}",
            title=payload.title,
            description=payload.description,
            acceptance_criteria=payload.acceptance_criteria,
            priority=payload.priority,
            status="queued",
            run_id=f"run_{suffix}",
            created_at=now,
        )
        self._append(
            event_type="objective.created",
            actor="human-customer",
            summary=objective.title,
            run_id=objective.run_id,
            objective_id=objective.id,
            timestamp=now,
            data={
                "title": objective.title,
                "description": objective.description,
                "acceptance_criteria": objective.acceptance_criteria,
                "priority": objective.priority,
            },
        )
        return objective

    def _reconcile_interrupted_run(
        self,
        run_id: str,
        run_events: list[StoredEvent],
        *,
        timestamp_factory: Callable[[], datetime],
    ) -> list[StoredEvent]:
        terminal_types = {"run.completed", "run.failed", "rollback.completed"}
        if not any(event.type == "run.started" for event in run_events):
            return []
        if any(event.type in terminal_types for event in run_events):
            return []

        objective_id = next(
            (event.objective_id for event in run_events if event.objective_id), None
        )
        last_event = run_events[-1]
        appended: list[StoredEvent] = []
        escrow_balance = self._run_account_balance(run_id, "escrow")
        if escrow_balance:
            appended.append(
                self._ledger_event(
                    kind="refund",
                    amount=escrow_balance,
                    reason="Interrupted run escrow returned during startup reconciliation",
                    from_agent="escrow",
                    to_agent="atlas",
                    run_id=run_id,
                    objective_id=objective_id,
                    timestamp=timestamp_factory(),
                )
            )
        appended.extend(
            self._append_agent_releases(
                run_id=run_id,
                objective_id=objective_id,
                agent_ids=self._engaged_agent_ids(run_events),
                reason="startup_interrupted",
                timestamp_factory=timestamp_factory,
            )
        )
        appended.append(
            self._append(
                event_type="run.failed",
                actor="orchestrator",
                summary="Interrupted run closed without replaying side effects",
                run_id=run_id,
                objective_id=objective_id,
                timestamp=timestamp_factory(),
                data={
                    "reason": "startup_interrupted",
                    "last_event_id": last_event.id,
                    "last_event_type": last_event.type,
                    "resumed": False,
                },
            )
        )
        return appended

    def reconcile_interrupted_runs(self) -> list[StoredEvent]:
        """Fail incomplete runs after restart without replaying external side effects."""

        with self._run_lock:
            events = self.store.all()
            run_ids = list(
                dict.fromkeys(
                    event.run_id
                    for event in events
                    if event.run_id and event.type == "run.started"
                )
            )
            appended: list[StoredEvent] = []
            for run_id in run_ids:
                run_events = [event for event in events if event.run_id == run_id]
                appended.extend(
                    self._reconcile_interrupted_run(
                        run_id,
                        run_events,
                        timestamp_factory=lambda: datetime.now(timezone.utc),
                    )
                )
            return appended

    def execute_objective(self, objective: Objective) -> None:
        with self._run_lock:
            run_events = [
                event
                for event in self.store.all()
                if event.run_id == objective.run_id
            ]
            if any(event.type == "run.started" for event in run_events):
                self._reconcile_interrupted_run(
                    objective.run_id,
                    run_events,
                    timestamp_factory=lambda: datetime.now(timezone.utc),
                )
                return
            self._execute_pipeline(
                objective,
                runtime=self.runtime,
                timestamp_factory=lambda: datetime.now(timezone.utc),
            )

    @staticmethod
    def _required_capabilities(objective: Objective) -> tuple[str, ...]:
        text = " ".join(
            (
                objective.title,
                objective.description,
                *objective.acceptance_criteria,
            )
        ).lower()
        if any(term in text for term in ("frontend", "react", "interface", "ui", "css")):
            return ("implementation", "react")
        if any(
            term in text
            for term in (
                "deploy",
                "container",
                "docker",
                "ci",
                "observability",
                "infrastructure",
            )
        ):
            return ("implementation", "containers")
        if any(term in text for term in ("api", "backend", "python", "fastapi", "endpoint")):
            return ("implementation", "python")
        return ("implementation",)

    def _auction_for(self, objective: Objective, *, bounty: int) -> AuctionResult:
        seeded = seed_agents()
        balances = self.ledger().balances
        agents = {
            agent_id: agent.model_copy(
                update={
                    "balance": balances.get(agent_id, agent.balance),
                    "status": (
                        CompanyAgentStatus.DORMANT
                        if balances.get(agent_id, agent.balance) <= BID_FEE
                        else CompanyAgentStatus.AVAILABLE
                    ),
                }
            )
            for agent_id, agent in seeded.items()
        }
        task = AuctionTask(
            id=objective.id,
            title=objective.title,
            required_capabilities=self._required_capabilities(objective),
            max_budget=bounty,
        )
        evidence_scores = {"forge": 0.91, "prism": 0.89, "rivet": 0.92}
        plans = {
            "forge": "Implement typed backend changes and executable contract checks.",
            "prism": "Implement accessible interface changes and focused component tests.",
            "rivet": "Implement reversible delivery changes and verify health evidence.",
        }
        evidence = [
            CredibilityEvidence(
                id=f"credibility:{engineer_id}:seed",
                agent_id=engineer_id,
                score=score,
                summary="Prior role evidence supports this bounded bid.",
                references=(f"agent-profile:{engineer_id}",),
            )
            for engineer_id, score in evidence_scores.items()
        ]
        bids: list[Bid] = []
        for engineer_id in ENGINEER_IDS:
            jitter = int(
                hashlib.sha256(
                    f"{objective.id}:{engineer_id}".encode("utf-8")
                ).hexdigest()[:2],
                16,
            ) % 7
            bids.append(
                Bid(
                    task_id=objective.id,
                    engineer_id=engineer_id,
                    amount=18 + jitter,
                    plan=plans[engineer_id],
                    credibility=evidence_scores[engineer_id] - 0.03,
                    evidence_refs=(f"credibility:{engineer_id}:seed",),
                )
            )
        return run_auction(task, bids, agents, evidence)

    def _memories_for_agent(self, agent_id: str, *, limit: int = 3) -> list[dict[str, str]]:
        memories: list[dict[str, str]] = []
        for event in self.store.all():
            if event.type not in {"memory.seeded", "memory.updated"}:
                continue
            target = event.data.get("agent_id") or event.actor
            if target != agent_id:
                continue
            content = event.data.get("memory") or event.data.get("content")
            if isinstance(content, str) and content:
                memories.append({"event_id": event.id, "content": content})
        return memories[-limit:]

    @staticmethod
    def _runtime_evidence(result: RuntimeResult) -> dict[str, Any]:
        diff = result.diff.model_dump(mode="json") if result.diff else None
        files_changed = (
            result.diff.name_only
            if result.diff
            else list(dict.fromkeys(change.path for change in result.file_changes))
        )
        evidence = {
            "change_id": result.change_id,
            "runtime": result.runtime,
            "provenance": result.provenance,
            "model": result.model,
            "thread_id": result.thread_id,
            "write_mode": result.write_mode,
            "declared_tests": result.tests,
            "usage": {
                "input_tokens": result.input_tokens,
                "cached_input_tokens": result.cached_input_tokens,
                "output_tokens": result.output_tokens,
                "reasoning_output_tokens": result.reasoning_output_tokens,
            },
            "commands": [item.model_dump(mode="json") for item in result.commands],
            "file_changes": [
                item.model_dump(mode="json") for item in result.file_changes
            ],
            "files_changed": files_changed,
            "diff": diff,
            "final_message": result.final_message,
            "raw_event_count": result.raw_event_count,
        }
        if result.provenance == "live":
            evidence.update(
                {
                    "requested_model": result.requested_model,
                    "observed_model": result.observed_model,
                    "invocation_argv": result.invocation_argv,
                    "codex_version": result.codex_version,
                }
            )
        return evidence

    @staticmethod
    def _sentinel_environment() -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USER", "TMPDIR"}
        }
        environment.update({"CI": "1", "NO_COLOR": "1"})
        return environment

    @staticmethod
    def _output_provenance(value: bytes | str | None) -> dict[str, Any]:
        if value is None:
            raw = b""
        elif isinstance(value, bytes):
            raw = value
        else:
            raw = value.encode("utf-8", errors="replace")
        return {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    @classmethod
    def _sentinel_checks(
        cls, runtime: RuntimeAdapter, result: RuntimeResult
    ) -> list[dict[str, Any]]:
        """Execute repository-owned checks selected from a static argv allowlist.

        Runtime-reported command strings are evidence about the implementation turn,
        never executable instructions and never release-gate proof.
        """

        empty_output = cls._output_provenance(b"")

        def not_run(
            allowlist_id: str, reason: str, *, cwd: Path | None = None
        ) -> dict[str, Any]:
            return {
                "allowlist_id": allowlist_id,
                "executor": "sentinel",
                "command_source": "static-allowlist",
                "argv": [],
                "cwd": str(cwd) if cwd else None,
                "shell": False,
                "status": "not_run",
                "exit_code": None,
                "failure_reason": reason,
                "stdout": empty_output,
                "stderr": empty_output,
            }

        workdir = getattr(runtime, "workdir", None)
        if workdir is None:
            return [not_run("sentinel-configuration", "runtime-workdir-missing")]
        try:
            root = Path(workdir).expanduser().resolve(strict=True)
        except (OSError, RuntimeError):
            return [not_run("sentinel-configuration", "runtime-workdir-invalid")]

        changed_paths = result.diff.name_only if result.diff else []
        if any(
            Path(path).is_absolute() or ".." in Path(path).parts
            for path in changed_paths
        ):
            return [not_run("sentinel-configuration", "unsafe-diff-path", cwd=root)]

        frontend_changed = any(path.startswith("frontend/") for path in changed_paths)
        backend_changed = any(path.startswith("backend/") for path in changed_paths)
        other_changed = any(
            not path.startswith(("backend/", "frontend/"))
            for path in changed_paths
        )
        require_backend = backend_changed or other_changed or not frontend_changed
        require_frontend = frontend_changed

        environment = cls._sentinel_environment()
        specs: list[tuple[str, list[str], Path]] = []
        configuration_errors: list[dict[str, Any]] = []
        if require_backend:
            if (root / "pyproject.toml").is_file():
                backend_dir = root
            elif (root / "backend" / "pyproject.toml").is_file():
                backend_dir = root / "backend"
            else:
                backend_dir = root / "backend" if (root / "backend").is_dir() else root
                configuration_errors.append(
                    not_run(
                        "backend-pytest",
                        "trusted-backend-check-unavailable",
                        cwd=backend_dir,
                    )
                )
            if (backend_dir / "pyproject.toml").is_file():
                specs.append(
                    (
                        "backend-pytest",
                        [str(Path(sys.executable).resolve()), "-m", "pytest", "-q"],
                        backend_dir,
                    )
                )
        if require_frontend:
            frontend_dir = root / "frontend" if (root / "frontend").is_dir() else root
            npm = shutil.which("npm", path=environment.get("PATH"))
            if not (frontend_dir / "package.json").is_file() or npm is None:
                configuration_errors.append(
                    not_run(
                        "frontend-vitest",
                        "trusted-frontend-check-unavailable",
                        cwd=frontend_dir,
                    )
                )
            else:
                specs.append(
                    (
                        "frontend-vitest",
                        [npm, "run", "test", "--", "--run"],
                        frontend_dir,
                    )
                )
        if configuration_errors:
            return configuration_errors

        configured_timeout = getattr(runtime, "timeout_seconds", None)
        timeout_seconds = (
            min(SENTINEL_TEST_TIMEOUT_SECONDS, max(10, configured_timeout))
            if isinstance(configured_timeout, int)
            else SENTINEL_TEST_TIMEOUT_SECONDS
        )
        outcomes: list[dict[str, Any]] = []
        for allowlist_id, argv, cwd in specs:
            try:
                completed = subprocess.run(
                    argv,
                    cwd=cwd,
                    env=environment,
                    capture_output=True,
                    text=False,
                    timeout=timeout_seconds,
                    check=False,
                    shell=False,
                )
                outcome = {
                    "allowlist_id": allowlist_id,
                    "executor": "sentinel",
                    "command_source": "static-allowlist",
                    "argv": argv,
                    "cwd": str(cwd),
                    "shell": False,
                    "timeout_seconds": timeout_seconds,
                    "environment_keys": sorted(environment),
                    "status": "passed" if completed.returncode == 0 else "failed",
                    "exit_code": completed.returncode,
                    "failure_reason": None,
                    "stdout": cls._output_provenance(completed.stdout),
                    "stderr": cls._output_provenance(completed.stderr),
                }
            except subprocess.TimeoutExpired as exc:
                outcome = {
                    "allowlist_id": allowlist_id,
                    "executor": "sentinel",
                    "command_source": "static-allowlist",
                    "argv": argv,
                    "cwd": str(cwd),
                    "shell": False,
                    "timeout_seconds": timeout_seconds,
                    "environment_keys": sorted(environment),
                    "status": "timed_out",
                    "exit_code": None,
                    "failure_reason": "timeout",
                    "stdout": cls._output_provenance(exc.stdout),
                    "stderr": cls._output_provenance(exc.stderr),
                }
            except OSError as exc:
                outcome = {
                    "allowlist_id": allowlist_id,
                    "executor": "sentinel",
                    "command_source": "static-allowlist",
                    "argv": argv,
                    "cwd": str(cwd),
                    "shell": False,
                    "timeout_seconds": timeout_seconds,
                    "environment_keys": sorted(environment),
                    "status": "not_run",
                    "exit_code": None,
                    "failure_reason": type(exc).__name__,
                    "stdout": empty_output,
                    "stderr": empty_output,
                }
            outcomes.append(outcome)
        return outcomes

    @staticmethod
    def _review_gate(
        runtime: RuntimeAdapter,
        implementation: RuntimeResult,
        review: RuntimeResult,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        if implementation.provenance == "fixture":
            if (
                implementation.runtime != "deterministic"
                or runtime.name != "deterministic"
            ):
                reasons.append("fixture-implementation-runtime-mismatch")
            if review.provenance != "fixture" or review.runtime != "deterministic":
                reasons.append("fixture-review-runtime-mismatch")
            return {
                "eligible": not reasons,
                "mode": "fixture",
                "reasons": reasons,
                "implementation_thread_id": implementation.thread_id,
                "review_thread_id": review.thread_id,
                "review_read_only": not review.write_mode,
            }

        if implementation.runtime != runtime.name:
            reasons.append("implementation-runtime-mismatch")
        if not implementation.thread_id:
            reasons.append("implementation-thread-missing")
        if review.provenance != "live":
            reasons.append("review-provenance-not-live")
        if review.runtime != implementation.runtime:
            reasons.append("review-runtime-mismatch")
        if not review.thread_id:
            reasons.append("review-thread-missing")
        elif review.thread_id == implementation.thread_id:
            reasons.append("review-reused-implementation-thread")
        if review.write_mode:
            reasons.append("review-not-read-only")
        if review.diff is not None or review.file_changes:
            reasons.append("review-produced-write-evidence")
        expected_model = getattr(runtime, "reviewer_model", None)
        if isinstance(expected_model, str) and review.model != expected_model:
            reasons.append("reviewer-model-mismatch")
        return {
            "eligible": not reasons,
            "mode": "live",
            "reasons": reasons,
            "implementation_thread_id": implementation.thread_id,
            "review_thread_id": review.thread_id,
            "review_read_only": not review.write_mode,
            "review_provenance": review.provenance,
            "review_model": review.model,
            "expected_reviewer_model": expected_model,
        }

    def _execute_pipeline(
        self,
        objective: Objective,
        *,
        runtime: RuntimeAdapter,
        timestamp_factory: Callable[[], datetime],
    ) -> None:
        context = {
            "run_id": objective.run_id,
            "objective_id": objective.id,
        }

        def emit(
            event_type: str,
            actor: str,
            summary: str,
            data: dict[str, Any] | None = None,
        ) -> StoredEvent:
            return self._append(
                event_type=event_type,
                actor=actor,
                summary=summary,
                data=data,
                timestamp=timestamp_factory(),
                **context,
            )

        bounty = 40
        engaged_agents: set[str] = {"atlas"}

        def recall(agent_id: str, purpose: str) -> list[dict[str, str]]:
            engaged_agents.add(agent_id)
            memories = self._memories_for_agent(agent_id)
            emit(
                "memory.recalled",
                agent_id,
                f"{seed_agents()[agent_id].name} recalled durable operating memory",
                {
                    "agent_id": agent_id,
                    "purpose": purpose,
                    "memories": memories,
                    "references": [item["event_id"] for item in memories],
                },
            )
            return memories

        def fail_run(
            summary: str,
            data: dict[str, Any],
            *,
            responsible_agent: str | None = None,
        ) -> None:
            if responsible_agent:
                self._capped_debit_event(
                    kind="penalty",
                    amount=3,
                    reason="Delivery evidence failed an independent gate",
                    from_agent=responsible_agent,
                    to_agent="treasury",
                    run_id=objective.run_id,
                    objective_id=objective.id,
                    timestamp=timestamp_factory(),
                    allow_partial=True,
                )
            escrow_balance = self._run_account_balance(objective.run_id, "escrow")
            if escrow_balance:
                self._ledger_event(
                    kind="refund",
                    amount=escrow_balance,
                    reason="Unreleased delivery bounty returned to Atlas",
                    from_agent="escrow",
                    to_agent="atlas",
                    timestamp=timestamp_factory(),
                    **context,
                )
            self._append_agent_releases(
                run_id=objective.run_id,
                objective_id=objective.id,
                agent_ids=engaged_agents,
                reason="run_failed",
                timestamp_factory=timestamp_factory,
            )
            emit("run.failed", "orchestrator", summary, data)

        emit(
            "run.started",
            "orchestrator",
            "Eight-agent autonomous delivery run started",
            {"mode": runtime.name, "company_size": len(AGENT_PROFILES)},
        )
        active_mechanisms = self.policies().active_mechanisms
        if active_mechanisms:
            emit(
                "policy.inherited",
                "orchestrator",
                "This run inherited operator-approved incident controls",
                {
                    "mechanism_ids": [item.id for item in active_mechanisms],
                    "mechanism_kinds": [item.kind for item in active_mechanisms],
                    "mechanisms": [
                        item.model_dump(mode="json") for item in active_mechanisms
                    ],
                    "runtime_brief_injection": True,
                },
            )
        self._ledger_event(
            kind="issue",
            amount=bounty,
            reason="Customer-funded objective budget",
            to_agent="atlas",
            timestamp=timestamp_factory(),
            **context,
        )
        atlas_memories = recall("atlas", "scope the objective and define evidence")
        planning_event = emit(
            "planning.completed",
            "atlas",
            "Objective decomposed into one independently verifiable change",
            {
                "task": objective.title,
                "acceptance_criteria": objective.acceptance_criteria,
                "memory_references": [item["event_id"] for item in atlas_memories],
            },
        )

        engaged_agents.update(ENGINEER_IDS)
        try:
            auction = self._auction_for(objective, bounty=bounty)
        except AuctionError as exc:
            fail_run(
                "Implementation auction ended without an eligible bidder",
                {
                    "error_type": "AuctionError",
                    "message": str(exc)[:300],
                    "reason": "no_eligible_bidder",
                },
            )
            return
        eligible_engineers = [
            item.bid.engineer_id for item in auction.assessments if item.eligible
        ]
        emit(
            "auction.opened",
            "atlas",
            "Atlas opened a three-engineer evidence-backed auction",
            {
                "task": objective.title,
                "bounty": bounty,
                "eligible_engineers": eligible_engineers,
                "required_capabilities": list(auction.task.required_capabilities),
            },
        )
        for assessment in auction.assessments:
            bid = assessment.bid
            recall(bid.engineer_id, "prepare an evidence-backed implementation bid")
            emit(
                "bid.submitted",
                bid.engineer_id,
                f"{seed_agents()[bid.engineer_id].name} bid {bid.amount} credits",
                {
                    "task": objective.title,
                    "bidder": bid.engineer_id,
                    "amount": bid.amount,
                    "plan": bid.plan,
                    "credibility": bid.credibility,
                    "evidence": list(bid.evidence_refs),
                    "evidence_score": assessment.evidence_score,
                    "eligible": assessment.eligible,
                    "reasons": list(assessment.reasons),
                },
            )
            self._capped_debit_event(
                kind="bid_fee",
                amount=BID_FEE,
                reason="Credibility-backed auction participation fee",
                from_agent=bid.engineer_id,
                to_agent="treasury",
                run_id=objective.run_id,
                objective_id=objective.id,
                timestamp=timestamp_factory(),
                allow_partial=False,
            )

        self._ledger_event(
            kind="escrow",
            amount=bounty,
            reason="Delivery bounty locked pending tests and review",
            from_agent="atlas",
            to_agent="escrow",
            timestamp=timestamp_factory(),
            **context,
        )
        winner = auction.winner
        emit(
            "auction.awarded",
            "atlas",
            f"{seed_agents()[winner.engineer_id].name} won the implementation auction",
            {
                "task": objective.title,
                "winner": winner.engineer_id,
                "amount": winner.amount,
                "plan": winner.plan,
                "bids_considered": len(auction.assessments),
                "evidence": list(winner.evidence_refs),
            },
        )
        emit(
            "task.assigned",
            "atlas",
            f"{seed_agents()[winner.engineer_id].name} accepted the bounded delivery task",
            {
                "task": objective.title,
                "assignee": winner.engineer_id,
                "bounty": winner.amount,
            },
        )
        implementation_model = getattr(runtime, "implementation_model", None)
        implementation_sandbox = (
            "workspace-write"
            if bool(getattr(runtime, "apply_changes", False))
            else "fixture"
            if runtime.name == "deterministic"
            else "read-only"
        )
        emit(
            "runtime.invoked",
            winner.engineer_id,
            f"{runtime.name.title()} implementation runtime invoked",
            {
                "runtime": runtime.name,
                "model": implementation_model,
                "sandbox": implementation_sandbox,
                "agent_id": winner.engineer_id,
                "provenance": "fixture" if runtime.name == "deterministic" else "live",
                "inherited_mechanism_ids": [
                    item.id for item in active_mechanisms
                ],
            },
        )
        winner_memories = self._memories_for_agent(winner.engineer_id)
        brief_lines = [
            objective.title,
            objective.description,
            *objective.acceptance_criteria,
            "Persistent operating memories:",
            *[f"- {item['content']}" for item in winner_memories],
        ]
        if active_mechanisms:
            brief_lines.extend(
                [
                    "Operator-approved incident controls inherited by this run:",
                    *[
                        f"- [{item.kind}] {item.id}: {item.enforcement}"
                        for item in active_mechanisms
                    ],
                ]
            )
        brief = "\n".join(brief_lines)
        try:
            result = runtime.generate(brief=brief, run_id=objective.run_id)
        except Exception as exc:  # runtime boundary is deliberately contained
            fail_run(
                "Implementation runtime failed safely",
                {"error_type": type(exc).__name__, "message": str(exc)[:300]},
            )
            return

        code_event = emit(
            "code.generated",
            winner.engineer_id,
            result.summary,
            self._runtime_evidence(result),
        )
        change_event = emit(
            "change.evidence_captured",
            winner.engineer_id,
            "Captured repository evidence without claiming an external pull request",
            {
                "change_id": result.change_id,
                "provenance": result.provenance,
                "files_changed": self._runtime_evidence(result)["files_changed"],
                "diff_sha256": result.diff.sha256 if result.diff else None,
                "source_event_ids": [code_event.id],
            },
        )

        aegis_memories = recall("aegis", "independently challenge the bounded change")
        diff_context = (
            "\n".join(
                [
                    f"Diff SHA-256: {result.diff.sha256}",
                    f"Changed files: {', '.join(result.diff.name_only)}",
                    result.diff.preview,
                ]
            )
            if result.diff
            else "Deterministic fixture change; no live repository diff was produced."
        )
        try:
            review = runtime.review(
                brief=brief,
                run_id=objective.run_id,
                diff_context=diff_context,
            )
        except Exception as exc:  # independent review is also a contained boundary
            fail_run(
                "Independent review runtime failed safely",
                {"error_type": type(exc).__name__, "message": str(exc)[:300]},
                responsible_agent=winner.engineer_id,
            )
            return

        review_gate = self._review_gate(runtime, result, review)
        review_event = emit(
            "review.completed",
            "aegis",
            review.summary,
            {
                "approved": review.verdict == "approved" and review_gate["eligible"],
                "verdict": review.verdict or "unknown",
                "findings": [item.model_dump(mode="json") for item in review.findings],
                "release_gate": review_gate,
                "memory_references": [item["event_id"] for item in aegis_memories],
                "source_event_ids": [code_event.id, change_event.id],
                **self._runtime_evidence(review),
            },
        )
        if not review_gate["eligible"]:
            unverified_review = emit(
                "review.unverified",
                "aegis",
                "Aegis rejected reviewer provenance that was not independent and read-only",
                {
                    **review_gate,
                    "source_event_ids": [
                        code_event.id,
                        change_event.id,
                        review_event.id,
                    ],
                },
            )
            fail_run(
                "Release gate rejected unverified reviewer provenance",
                {
                    "reason": "review_provenance_unverified",
                    "review_event_id": review_event.id,
                    "unverified_event_id": unverified_review.id,
                },
                responsible_agent=winner.engineer_id,
            )
            return
        if review.verdict != "approved":
            fail_run(
                "Aegis blocked release because independent review did not approve",
                {
                    "verdict": review.verdict or "unknown",
                    "review_event_id": review_event.id,
                },
                responsible_agent=winner.engineer_id,
            )
            return

        sentinel_memories = recall(
            "sentinel", "falsify implementation and release claims"
        )
        live_change_present = bool(
            result.write_mode and result.diff and result.diff.name_only
        )
        check_outcomes = (
            []
            if result.provenance == "fixture" or not live_change_present
            else self._sentinel_checks(runtime, result)
        )
        tests_verified = (
            bool(result.tests)
            if result.provenance == "fixture"
            else (
                live_change_present
                and bool(check_outcomes)
                and all(
                    outcome["status"] == "passed" and outcome["exit_code"] == 0
                    for outcome in check_outcomes
                )
            )
        )
        if not tests_verified:
            unverified_event = emit(
                "tests.unverified",
                "sentinel",
                "Sentinel blocked release because executable evidence was incomplete",
                {
                    "provenance": result.provenance,
                    "write_mode": result.write_mode,
                    "live_change_present": live_change_present,
                    "check_outcomes": check_outcomes,
                    "agent_declared_commands": [
                        item.model_dump(mode="json") for item in result.commands
                    ],
                    "command_policy": "agent-declared commands are never executed or trusted",
                    "source_event_ids": [code_event.id, review_event.id],
                    "memory_references": [
                        item["event_id"] for item in sentinel_memories
                    ],
                },
            )
            fail_run(
                "Release gate rejected unverified implementation evidence",
                {"tests_event_id": unverified_event.id},
                responsible_agent=winner.engineer_id,
            )
            return

        tests_event = emit(
            "tests.passed",
            "sentinel",
            "Sentinel accepted executable verification evidence",
            {
                "passed": (
                    len(result.tests)
                    if result.provenance == "fixture"
                    else len(check_outcomes)
                ),
                "failed": 0,
                "tests": result.tests or [
                    str(item["allowlist_id"]) for item in check_outcomes
                ],
                "check_outcomes": check_outcomes,
                "provenance": result.provenance,
                "executor": "fixture" if result.provenance == "fixture" else "sentinel",
                "command_policy": "static-allowlist-no-shell",
                "source_event_ids": [code_event.id, review_event.id],
                "memory_references": [item["event_id"] for item in sentinel_memories],
            },
        )
        version_number = 1 + len(
            {
                event.data.get("version")
                for event in self.store.all()
                if event.type == "deployment.succeeded"
                and event.data.get("version")
            }
        )
        version = f"v1.0.{version_number}"
        shipwright_memories = recall(
            "shipwright", "promote a reversible release into the demo sandbox"
        )
        deployment_started = emit(
            "deployment.started",
            "shipwright",
            f"Release {version} entered the reversible demo-sandbox gate",
            {
                "version": version,
                "strategy": (
                    "policy-gated-demo-sandbox"
                    if active_mechanisms
                    else "standard-demo-sandbox"
                ),
                "enforced_mechanisms": [item.id for item in active_mechanisms],
                "environment": "demo-sandbox",
                "external_deployment": False,
                "memory_references": [
                    item["event_id"] for item in shipwright_memories
                ],
                "source_event_ids": [tests_event.id],
            },
        )
        deployment_event = emit(
            "deployment.succeeded",
            "shipwright",
            f"Release {version} promoted inside the demo sandbox",
            {
                "version": version,
                "url": "/api/pulse",
                "environment": "demo-sandbox",
                "external_deployment": False,
                "source_event_ids": [deployment_started.id, tests_event.id],
            },
        )
        monitor_event = emit(
            "monitor.healthy",
            "sentinel",
            "Test-backed sandbox evidence satisfied the release health gate",
            {
                "version": version,
                "error_rate": 0.0,
                "environment": "demo-sandbox",
                "external_observation": False,
                "source": "verified-test-evidence",
                "source_event_ids": [tests_event.id, deployment_event.id],
            },
        )
        release_evidence_ids = [
            tests_event.id,
            deployment_event.id,
            monitor_event.id,
        ]
        if not (
            monitor_event.type == "monitor.healthy"
            and monitor_event.data.get("version") == version
            and tests_event.id in monitor_event.data.get("source_event_ids", [])
            and deployment_event.id in monitor_event.data.get("source_event_ids", [])
        ):
            fail_run(
                "Escrow remained locked because release health evidence was incomplete",
                {
                    "reason": "healthy_release_evidence_missing",
                    "version": version,
                    "monitor_event_id": monitor_event.id,
                },
                responsible_agent="shipwright",
            )
            return
        self._ledger_event(
            kind="payout",
            amount=winner.amount,
            reason="Winning implementation bid released after verification",
            from_agent="escrow",
            to_agent=winner.engineer_id,
            timestamp=timestamp_factory(),
            source_event_ids=release_evidence_ids,
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=5,
            reason="Independent review completed",
            from_agent="escrow",
            to_agent="aegis",
            timestamp=timestamp_factory(),
            source_event_ids=release_evidence_ids,
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=5,
            reason="Release verification completed",
            from_agent="escrow",
            to_agent="sentinel",
            timestamp=timestamp_factory(),
            source_event_ids=release_evidence_ids,
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=3,
            reason="Reversible sandbox promotion completed",
            from_agent="escrow",
            to_agent="shipwright",
            timestamp=timestamp_factory(),
            source_event_ids=release_evidence_ids,
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=2,
            reason="Delivery account allocation released after monitored health evidence",
            from_agent="escrow",
            to_agent="chronicle",
            timestamp=timestamp_factory(),
            source_event_ids=release_evidence_ids,
            **context,
        )
        remainder = bounty - winner.amount - 5 - 5 - 3 - 2
        if remainder:
            self._ledger_event(
                kind="refund",
                amount=remainder,
                reason="Unused delivery bounty returned after settlement",
                from_agent="escrow",
                to_agent="atlas",
                timestamp=timestamp_factory(),
                source_event_ids=release_evidence_ids,
                **context,
            )

        chronicle_memories = recall(
            "chronicle", "write a source-linked account of the completed delivery"
        )
        source_event_ids = [
            planning_event.id,
            code_event.id,
            review_event.id,
            tests_event.id,
            deployment_event.id,
            monitor_event.id,
        ]
        changelog_event = emit(
            "changelog.written",
            "chronicle",
            "Chronicle recorded what changed and which evidence supports it",
            {
                "version": version,
                "winner": winner.engineer_id,
                "change_id": result.change_id,
                "source_event_ids": source_event_ids,
                "memory_references": [
                    item["event_id"] for item in chronicle_memories
                ],
            },
        )

        lessons = {
            "atlas": "Name acceptance evidence before opening the implementation auction.",
            "forge": f"The {winner.engineer_id} bid won only after capability and credibility checks.",
            "prism": f"The {winner.engineer_id} bid won only after capability and credibility checks.",
            "rivet": f"The {winner.engineer_id} bid won only after capability and credibility checks.",
            "aegis": "A release requires an independent verdict tied to captured change evidence.",
            "sentinel": "Live changes require both a repository diff and successful executable checks.",
            "shipwright": "Sandbox promotion is not an external deployment and must be labeled explicitly.",
            "chronicle": "A durable delivery account links planning, code, review, tests, and release events.",
        }
        memory_source_ids = [*source_event_ids, changelog_event.id]
        for agent_id in AGENT_IDS:
            emit(
                "memory.updated",
                agent_id,
                f"{seed_agents()[agent_id].name} retained a source-linked delivery lesson",
                {
                    "agent_id": agent_id,
                    "memory": lessons[agent_id],
                    "kind": "delivery-lesson",
                    "references": memory_source_ids,
                },
            )
        emit(
            "run.completed",
            "orchestrator",
            "Objective verified and promoted into the monitored demo sandbox",
            {
                "version": version,
                "winner": winner.engineer_id,
                "change_id": result.change_id,
                "environment": "demo-sandbox",
                "external_deployment": False,
                "source_event_ids": [changelog_event.id],
            },
        )

    def objectives(self) -> list[Objective]:
        results: list[Objective] = []
        for event in self.store.all():
            if event.type != "objective.created" or not event.objective_id or not event.run_id:
                continue
            try:
                run = self.run_summary(event.run_id)
                status = ObjectiveStatus(run.status)
            except DomainNotFound:
                status = ObjectiveStatus.QUEUED
            results.append(
                Objective(
                    id=event.objective_id,
                    title=event.data["title"],
                    description=event.data.get("description", ""),
                    acceptance_criteria=event.data.get("acceptance_criteria", []),
                    priority=event.data.get("priority", "standard"),
                    status=status,
                    run_id=event.run_id,
                    created_at=event.timestamp,
                )
            )
        return sorted(results, key=lambda item: item.created_at, reverse=True)

    def objective(self, objective_id: str) -> Objective:
        for objective in self.objectives():
            if objective.id == objective_id:
                return objective
        raise DomainNotFound(f"objective {objective_id} was not found")

    def run_summary(self, run_id: str) -> RunSummary:
        events = self.store.query(run_id=run_id, limit=500)
        if not events:
            raise DomainNotFound(f"run {run_id} was not found")
        return self._reduce_run(events)

    def run_detail(self, run_id: str) -> RunDetail:
        events = self.store.query(run_id=run_id, limit=500)
        if not events:
            raise DomainNotFound(f"run {run_id} was not found")
        return RunDetail(run=self._reduce_run(events), events=events)

    def runs(self) -> list[RunSummary]:
        run_ids = {
            event.run_id
            for event in self.store.all()
            if event.run_id is not None
        }
        return sorted(
            (self.run_summary(run_id) for run_id in run_ids),
            key=lambda run: run.started_at,
            reverse=True,
        )

    def _reduce_run(self, events: list[StoredEvent]) -> RunSummary:
        objective_event = next(
            (event for event in events if event.type == "objective.created"), None
        )
        if objective_event is None or objective_event.objective_id is None:
            raise DomainNotFound("run has no objective event")
        status = RunStatus.QUEUED
        phase = "queued"
        progress = 0
        health: str = "unknown"
        current_version: str | None = None
        stable_version: str | None = None
        completed_at: datetime | None = None

        for event in events:
            if event.type == "run.started":
                status, phase, progress = RunStatus.RUNNING, "planning", 5
            elif event.type == "planning.completed":
                phase, progress = "planning", 15
            elif event.type in {"auction.opened", "bid.submitted"}:
                phase, progress = "auction", 22
            elif event.type == "auction.awarded":
                phase, progress = "auction", 28
            elif event.type in {"task.assigned", "runtime.invoked"}:
                phase, progress = "implementation", 30
            elif event.type in {"code.generated", "change.evidence_captured"}:
                phase, progress = "implementation", 48
            elif event.type in {"pull_request.opened", "review.approved", "review.completed"}:
                phase, progress = "review", 65
            elif event.type == "tests.passed":
                phase, progress = "verification", 78
            elif event.type == "tests.unverified":
                phase, progress = "verification", 72
            elif event.type == "deployment.started":
                phase, progress = "deployment", 88
                current_version = event.data.get("version", current_version)
            elif event.type == "deployment.succeeded":
                phase, progress = "monitoring", 94
                current_version = event.data.get("version", current_version)
                stable_version = current_version
            elif event.type == "monitor.healthy":
                health, progress = "healthy", 98
            elif event.type == "changelog.written":
                phase, progress = "documentation", 99
            elif event.type == "run.completed":
                status, phase, progress = RunStatus.COMPLETED, "completed", 100
                completed_at = event.timestamp
            elif event.type == "run.failed":
                status, phase = RunStatus.FAILED, "failed"
                health = "degraded"
                completed_at = event.timestamp
            elif event.type == "regression.injected":
                status, phase = RunStatus.DEGRADED, "incident"
                health = "degraded"
                current_version = event.data.get("bad_version", current_version)
            elif event.type == "monitor.alert":
                status, phase, health = RunStatus.DEGRADED, "incident", "degraded"
            elif event.type == "rollback.started":
                status, phase, health = RunStatus.DEGRADED, "recovery", "recovering"
            elif event.type == "rollback.completed":
                status, phase, health = RunStatus.RECOVERED, "self-improvement", "healthy"
                current_version = event.data.get("restored_version", stable_version)
                completed_at = event.timestamp
            elif event.type in {"policy.proposed", "policy.approved", "policy.activated"}:
                phase = "self-improvement"

        return RunSummary(
            id=events[0].run_id or "",
            objective_id=objective_event.objective_id,
            objective_title=objective_event.data.get("title", objective_event.summary),
            status=status,
            phase=phase,
            progress=progress,
            current_version=current_version,
            stable_version=stable_version,
            health=health,
            event_count=len(events),
            started_at=events[0].timestamp,
            completed_at=completed_at,
        )

    def replay(self, run_id: str) -> Replay:
        events = self.store.query(run_id=run_id, limit=500)
        if not events:
            raise DomainNotFound(f"run {run_id} was not found")
        frames: list[ReplayFrame] = []
        for index, event in enumerate(events, start=1):
            snapshot = self._reduce_run(events[:index])
            ledger_delta = 0
            if event.type == "ledger.transaction":
                amount = int(event.data["amount"])
                ledger_delta = amount if event.data.get("to_agent") else -amount
            frames.append(
                ReplayFrame(
                    sequence=event.sequence,
                    timestamp=event.timestamp,
                    phase=snapshot.phase,
                    status=snapshot.status,
                    active_agent=event.actor if event.actor in AGENT_IDS else None,
                    summary=event.summary,
                    version=snapshot.current_version,
                    health=snapshot.health,
                    ledger_delta=ledger_delta,
                )
            )
        chain = self.store.verify()
        return Replay(
            run=self._reduce_run(events),
            events=events,
            frames=frames,
            chain=ChainState(
                valid=chain.valid,
                head_hash=chain.head_hash,
                event_count=chain.event_count,
            ),
        )

    def ledger(self) -> LedgerResponse:
        balances: dict[str, int] = {}
        transactions: list[LedgerTransaction] = []
        total_issued = 0
        for event in self.store.all():
            if event.type != "ledger.transaction":
                continue
            data = event.data
            amount = int(data["amount"])
            if amount <= 0:
                raise DomainConflict(
                    f"ledger event {event.id} has a non-positive amount"
                )
            from_agent = data.get("from_agent")
            to_agent = data.get("to_agent")
            kind = data["kind"]
            if from_agent is not None:
                available = balances.get(from_agent, 0)
                if amount > available:
                    raise DomainConflict(
                        f"ledger event {event.id} overdraws {from_agent}: "
                        f"available {available}, requested {amount}"
                    )
                balances[from_agent] = available - amount
            if to_agent is not None:
                balances[to_agent] = balances.get(to_agent, 0) + amount
            if kind == "issue":
                total_issued += amount
            transactions.append(
                LedgerTransaction(
                    event_id=event.id,
                    sequence=event.sequence,
                    timestamp=event.timestamp,
                    kind=kind,
                    from_agent=from_agent,
                    to_agent=to_agent,
                    amount=amount,
                    reason=data["reason"],
                    run_id=event.run_id,
                )
            )
        return LedgerResponse(
            balances=balances,
            transactions=transactions,
            total_issued=total_issued,
            conserved=sum(balances.values()) == total_issued,
        )

    def agents(self) -> AgentsResponse:
        ledger = self.ledger()
        events = self.store.all()
        run_ids = {event.run_id for event in events if event.run_id}
        lifecycle_types = {
            "run.started",
            "run.completed",
            "run.failed",
            "regression.injected",
            "monitor.alert",
            "rollback.started",
            "rollback.completed",
        }
        last_lifecycle: dict[str, str] = {}
        for event in events:
            if event.run_id and event.type in lifecycle_types:
                last_lifecycle[event.run_id] = event.type
        terminal_run_ids = {
            run_id
            for run_id, event_type in last_lifecycle.items()
            if event_type in {"run.completed", "run.failed", "rollback.completed"}
        }
        active_run_ids = run_ids - terminal_run_ids
        items: list[Agent] = []
        for profile in AGENT_PROFILES:
            agent_events = [
                event
                for event in events
                if event.actor == profile.id
                or event.data.get("agent_id") == profile.id
                or event.data.get("bidder") == profile.id
                or event.data.get("assignee") == profile.id
                or event.data.get("winner") == profile.id
            ]
            last = agent_events[-1] if agent_events else None
            active_agent_events = [
                event for event in agent_events if event.run_id in active_run_ids
            ]
            status = "idle"
            current_task: str | None = None
            balance = ledger.balances.get(profile.id, profile.balance)
            for event in reversed(active_agent_events):
                candidate = event.data.get("task")
                if isinstance(candidate, str) and candidate:
                    current_task = candidate
                    break
            meaningful = next(
                (
                    event
                    for event in reversed(active_agent_events)
                    if event.type
                    not in {
                        "agent.registered",
                        "memory.seeded",
                        "memory.updated",
                        "memory.recalled",
                        "ledger.transaction",
                    }
                ),
                None,
            )
            if balance <= 0:
                status = "dormant"
            elif meaningful is not None:
                if meaningful.type == "bid.submitted":
                    status = "bidding"
                elif meaningful.type.startswith("review."):
                    status = "reviewing"
                elif meaningful.type.startswith("tests."):
                    status = "testing"
                elif meaningful.type.startswith("deployment."):
                    status = "deploying"
                elif meaningful.type.startswith("monitor."):
                    status = "monitoring"
                elif meaningful.type == "changelog.written":
                    status = "documenting"
                elif meaningful.type in {
                    "task.assigned",
                    "runtime.invoked",
                    "code.generated",
                    "change.evidence_captured",
                }:
                    status = "working"
            memories = [
                str(event.data["memory"])
                for event in agent_events
                if event.type in {"memory.seeded", "memory.updated"}
                and "memory" in event.data
                and (event.data.get("agent_id") or event.actor) == profile.id
            ]
            items.append(
                Agent(
                    id=profile.id,
                    name=profile.name,
                    role=profile.role,
                    status=status,
                    credits=balance,
                    current_task=current_task,
                    completed_actions=len(agent_events),
                    last_seen=last.timestamp if last else None,
                    memory=memories[-3:],
                    memory_count=len(memories),
                    capabilities=list(profile.capabilities),
                    personality=profile.personality,
                )
            )
        return AgentsResponse(items=items, count=len(items))

    @staticmethod
    def _mechanisms() -> list[PolicyMechanism]:
        return [
            PolicyMechanism(
                id="independent-review-gate",
                kind="prompt",
                name="Independent read-only reviewer contract",
                description=(
                    "Require a separate live reviewer invocation to challenge the "
                    "captured change without workspace-write authority."
                ),
                enforcement=(
                    "The release gate rejects a reviewer that reuses the implementation "
                    "thread, lacks live provenance, runs in write mode, emits change "
                    "evidence, or does not use the configured reviewer model."
                ),
            ),
            PolicyMechanism(
                id="sentinel-static-check-gate",
                kind="routing",
                name="Sentinel trusted-check routing gate",
                description=(
                    "Route changed backend and frontend scopes to Sentinel's static "
                    "verification allowlist before sandbox promotion."
                ),
                enforcement=(
                    "Sentinel selects pytest and/or Vitest from changed paths, executes "
                    "argument vectors with shell disabled, and blocks promotion unless "
                    "every selected command exits successfully."
                ),
            ),
            PolicyMechanism(
                id="health-evidence-escrow",
                kind="economy",
                name="Health-evidence escrow release",
                description=(
                    "Keep the delivery bounty in escrow until the sandbox release has "
                    "test, deployment, and healthy-monitor evidence."
                ),
                enforcement=(
                    "Every escrow payout is appended after monitor.healthy and carries "
                    "source links to tests.passed, deployment.succeeded, and the healthy "
                    "monitor event; failed gates refund unreleased escrow."
                ),
            ),
            PolicyMechanism(
                id="incident-policy-memory",
                kind="memory",
                name="Approved incident-policy memory",
                description=(
                    "Carry operator-approved incident controls into later implementation "
                    "and independent-review briefs."
                ),
                enforcement=(
                    "Future runs emit policy.inherited with the serialized controls and "
                    "append each approved mechanism's kind, identifier, and enforcement "
                    "text to the runtime brief used by both invocations."
                ),
            ),
        ]

    @staticmethod
    def _structural_control_coverage(
        mechanisms: list[PolicyMechanism],
    ) -> tuple[float, list[str]]:
        covered = [
            kind
            for kind in POLICY_MECHANISM_KINDS
            if any(mechanism.kind == kind for mechanism in mechanisms)
        ]
        return len(covered) / len(POLICY_MECHANISM_KINDS), covered

    def inject_regression(
        self, run_id: str, *, reason: str, error_rate: float
    ) -> list[StoredEvent]:
        with self._run_lock:
            run = self.run_summary(run_id)
            if run.status not in {RunStatus.COMPLETED, RunStatus.RECOVERED}:
                raise DomainConflict("only a stable run can receive a regression")
            if run.stable_version is None:
                raise DomainConflict("run has no stable release to protect")
            incident_number = 1 + sum(
                event.type == "regression.injected"
                for event in self.store.query(run_id=run_id, limit=500)
            )
            bad_version = f"{run.stable_version}-regression.{incident_number}"
            objective_id = run.objective_id
            first = self._append(
                event_type="regression.injected",
                actor="failure-injector",
                summary=reason,
                run_id=run_id,
                objective_id=objective_id,
                data={
                    "bad_version": bad_version,
                    "stable_version": run.stable_version,
                    "injection": "pulse-http-500",
                },
            )
            second = self._append(
                event_type="monitor.alert",
                actor="sentinel",
                summary="Sentinel detected an error-budget breach",
                run_id=run_id,
                objective_id=objective_id,
                data={
                    "version": bad_version,
                    "http_status": 500,
                    "error_rate": error_rate,
                    "threshold": 0.01,
                },
            )
            run_events = self.store.query(run_id=run_id, limit=500)
            auction_event = next(
                (
                    event
                    for event in reversed(run_events)
                    if event.type == "auction.awarded"
                ),
                None,
            )
            assignment_event = next(
                (
                    event
                    for event in reversed(run_events)
                    if event.type == "task.assigned"
                ),
                None,
            )
            implementing_engineer = (
                auction_event.data.get("winner")
                if auction_event
                else assignment_event.data.get("assignee")
                if assignment_event
                else "forge"
            )
            liabilities = (
                (
                    str(implementing_engineer),
                    4,
                    "Implemented the regression that escaped independent gates",
                ),
                (
                    "aegis",
                    3,
                    "Approved a change that later produced an escaped regression",
                ),
                (
                    "sentinel",
                    2,
                    "Verification evidence failed to predict the regression",
                ),
                (
                    "shipwright",
                    2,
                    "Unhealthy release escaped the promotion gate",
                ),
            )
            penalties = [
                self._capped_debit_event(
                    kind="penalty",
                    amount=amount,
                    reason=liability,
                    from_agent=agent_id,
                    to_agent="incident-escrow",
                    run_id=run_id,
                    objective_id=objective_id,
                    timestamp=datetime.now(timezone.utc),
                    allow_partial=True,
                )
                for agent_id, amount, liability in liabilities
            ]
            return [first, second, *penalties]

    def rollback(self, run_id: str, *, reason: str) -> tuple[RunSummary, PolicyProposal, list[StoredEvent]]:
        with self._run_lock:
            run = self.run_summary(run_id)
            if run.status != RunStatus.DEGRADED:
                raise DomainConflict("rollback requires a degraded run")
            if not run.stable_version:
                raise DomainConflict("run has no known-good release")
            events: list[StoredEvent] = []
            common = {"run_id": run_id, "objective_id": run.objective_id}
            events.append(
                self._append(
                    event_type="rollback.started",
                    actor="shipwright",
                    summary=reason,
                    data={"target_version": run.stable_version},
                    **common,
                )
            )
            events.append(
                self._append(
                    event_type="rollback.completed",
                    actor="shipwright",
                    summary=f"Restored known-good release {run.stable_version}",
                    data={"restored_version": run.stable_version},
                    **common,
                )
            )
            events.append(
                self._append(
                    event_type="incident.analyzed",
                    actor="aegis",
                    summary="The regression bypassed a missing promotion gate",
                    data={
                        "root_cause": "Health contract was checked before deploy but not during promotion.",
                        "lesson": "Release confidence must combine prevention, detection, and recovery.",
                    },
                    **common,
                )
            )
            proposal_index = 1 + sum(
                event.type == "policy.proposed"
                for event in self.store.query(run_id=run_id, limit=500)
            )
            proposal_id = f"policy_{run_id}_{proposal_index}"
            active_mechanisms = self.policies().active_mechanisms
            proposed_mechanisms = self._mechanisms()
            baseline_score, baseline_kinds = self._structural_control_coverage(
                active_mechanisms
            )
            candidate_score, candidate_kinds = self._structural_control_coverage(
                proposed_mechanisms
            )
            proposal = PolicyProposal(
                id=proposal_id,
                run_id=run_id,
                title="Record the executable release-control set",
                rationale=(
                    "The incident identified four controls that already have executable "
                    "release-path enforcement and should be explicit in future briefs."
                ),
                mechanisms=proposed_mechanisms,
                benchmark_id=POLICY_BENCHMARK_ID,
                benchmark_metric=POLICY_BENCHMARK_METRIC,
                benchmark_cases=len(POLICY_MECHANISM_KINDS),
                baseline_score=baseline_score,
                candidate_score=candidate_score,
                critical_regressions=0,
                status="proposed",
                created_at=datetime.now(timezone.utc),
            )
            events.append(
                self._append(
                    event_type="benchmark.completed",
                    actor="aegis",
                    summary=(
                        "Deterministic structural control-coverage check compared "
                        "active and proposed mechanism kinds"
                    ),
                    data={
                        "benchmark_id": proposal.benchmark_id,
                        "metric": proposal.benchmark_metric,
                        "cases": proposal.benchmark_cases,
                        "baseline_score": proposal.baseline_score,
                        "candidate_score": proposal.candidate_score,
                        "critical_regressions": proposal.critical_regressions,
                        "required_mechanism_kinds": list(POLICY_MECHANISM_KINDS),
                        "baseline_mechanism_kinds": baseline_kinds,
                        "candidate_mechanism_kinds": candidate_kinds,
                        "evaluation_scope": "structure-only-not-efficacy",
                        "deterministic": True,
                    },
                    timestamp=proposal.created_at,
                    **common,
                )
            )
            events.append(
                self._append(
                    event_type="policy.proposed",
                    actor="atlas",
                    summary="Proposed four runtime-backed incident controls",
                    data={"proposal": proposal.model_dump(mode="json")},
                    timestamp=proposal.created_at,
                    **common,
                )
            )
            return self.run_summary(run_id), proposal, events

    def policies(self) -> PoliciesResponse:
        proposals: dict[str, PolicyProposal] = {}
        active_ids: set[str] = set()
        for event in self.store.all():
            if event.type == "policy.proposed":
                proposal = PolicyProposal.model_validate(event.data["proposal"])
                proposals[proposal.id] = proposal
            elif event.type in {"policy.approved", "policy.rejected", "policy.activated"}:
                proposal_id = event.data.get("proposal_id")
                if proposal_id not in proposals:
                    continue
                if event.type == "policy.approved":
                    proposals[proposal_id] = proposals[proposal_id].model_copy(
                        update={"status": PolicyStatus.APPROVED, "decided_at": event.timestamp}
                    )
                elif event.type == "policy.rejected":
                    proposals[proposal_id] = proposals[proposal_id].model_copy(
                        update={"status": PolicyStatus.REJECTED, "decided_at": event.timestamp}
                    )
                else:
                    proposals[proposal_id] = proposals[proposal_id].model_copy(
                        update={"status": PolicyStatus.ACTIVE}
                    )
                    active_ids.add(proposal_id)
        active_by_kind: dict[str, PolicyMechanism] = {}
        active_proposals = sorted(
            (proposals[proposal_id] for proposal_id in active_ids),
            key=lambda proposal: proposal.created_at,
        )
        for proposal in active_proposals:
            for mechanism in proposal.mechanisms:
                active_by_kind[mechanism.kind] = mechanism
        kind_order = {"memory": 0, "prompt": 1, "routing": 2, "economy": 3}
        active_mechanisms = sorted(
            active_by_kind.values(),
            key=lambda mechanism: kind_order[mechanism.kind],
        )
        items = sorted(proposals.values(), key=lambda item: item.created_at, reverse=True)
        return PoliciesResponse(
            items=items,
            active_mechanisms=active_mechanisms,
            count=len(items),
        )

    def decide_policy(
        self, proposal_id: str, *, decision: str, decided_by: str
    ) -> PolicyProposal:
        with self._run_lock:
            policies = {policy.id: policy for policy in self.policies().items}
            proposal = policies.get(proposal_id)
            if proposal is None:
                raise DomainNotFound(f"policy proposal {proposal_id} was not found")
            if proposal.status != PolicyStatus.PROPOSED:
                raise DomainConflict("policy proposal has already been decided")
            if decision == "approve":
                if proposal.candidate_score <= proposal.baseline_score:
                    raise DomainConflict(
                        "policy benchmark gate failed: candidate score must be greater "
                        "than the baseline score"
                    )
                if proposal.critical_regressions != 0:
                    raise DomainConflict(
                        "policy benchmark gate failed: critical regressions must be zero"
                    )
            event_type = "policy.approved" if decision == "approve" else "policy.rejected"
            self._append(
                event_type=event_type,
                actor=decided_by,
                summary=(
                    "Policy proposal approved"
                    if decision == "approve"
                    else "Policy proposal rejected"
                ),
                run_id=proposal.run_id,
                objective_id=self.run_summary(proposal.run_id).objective_id,
                data={"proposal_id": proposal_id},
            )
            if decision == "approve":
                self._append(
                    event_type="policy.activated",
                    actor="orchestrator",
                    summary=(
                        "Four operator-approved, runtime-backed incident controls "
                        "recorded for future runs"
                    ),
                    run_id=proposal.run_id,
                    objective_id=self.run_summary(proposal.run_id).objective_id,
                    data={
                        "proposal_id": proposal_id,
                        "mechanism_ids": [item.id for item in proposal.mechanisms],
                        "mechanism_kinds": [item.kind for item in proposal.mechanisms],
                        "benchmark_id": proposal.benchmark_id,
                        "baseline_score": proposal.baseline_score,
                        "candidate_score": proposal.candidate_score,
                        "critical_regressions": proposal.critical_regressions,
                        "evaluation_scope": "structure-only-not-efficacy",
                    },
                )
                self._append(
                    event_type="self_improvement.scheduled",
                    actor="atlas",
                    summary="Future objectives inherit the learned release policy",
                    run_id=proposal.run_id,
                    objective_id=self.run_summary(proposal.run_id).objective_id,
                    data={"proposal_id": proposal_id, "applies_to": "future-runs"},
                )
            updated = {policy.id: policy for policy in self.policies().items}[proposal_id]
            return updated

    def chain_state(self) -> ChainState:
        return self.store.verify()

    @staticmethod
    def objective_fingerprint(payload: ObjectiveCreate) -> str:
        material = payload.model_dump_json()
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
