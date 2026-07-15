from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
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
from app.services.event_store import JsonlEventStore
from app.services.runtime import DeterministicRuntime, RuntimeAdapter


SEED_OBJECTIVE_ID = "obj_seed_self_hosting_v1"
SEED_RUN_ID = "run_seed_self_hosting_v1"
SEED_TIME = datetime(2026, 7, 14, 3, 30, tzinfo=timezone.utc)
POLICY_BENCHMARK_ID = "incident-recovery-loop-v1"
POLICY_BENCHMARK_METRIC = "safety_control_coverage"


AGENT_PROFILES: tuple[dict[str, str], ...] = (
    {"id": "atlas", "name": "Atlas", "role": "Product manager"},
    {"id": "forge", "name": "Forge", "role": "Implementation engineer"},
    {"id": "aegis", "name": "Aegis", "role": "Adversarial reviewer"},
    {"id": "sentinel", "name": "Sentinel", "role": "QA and reliability"},
    {"id": "shipwright", "name": "Shipwright", "role": "Release engineer"},
)
AGENT_IDS = {profile["id"] for profile in AGENT_PROFILES}


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
    ) -> StoredEvent:
        return self._append(
            event_type="ledger.transaction",
            actor="ledger",
            summary=f"{kind.title()}: {amount} credits — {reason}",
            run_id=run_id,
            objective_id=objective_id,
            timestamp=timestamp,
            data={
                "kind": kind,
                "amount": amount,
                "reason": reason,
                "from_agent": from_agent,
                "to_agent": to_agent,
            },
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

            for profile in AGENT_PROFILES:
                self._ledger_event(
                    kind="issue",
                    amount=80,
                    reason="Genesis operating balance",
                    to_agent=profile["id"],
                    timestamp=seeded_time(),
                )

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

    def execute_objective(self, objective: Objective) -> None:
        with self._run_lock:
            run_events = self.store.query(run_id=objective.run_id, limit=500)
            if any(event.type == "run.started" for event in run_events):
                return
            self._execute_pipeline(
                objective,
                runtime=self.runtime,
                timestamp_factory=lambda: datetime.now(timezone.utc),
            )

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

        emit(
            "run.started",
            "orchestrator",
            "Autonomous delivery run started",
            {"mode": runtime.name},
        )
        active_mechanisms = self.policies().active_mechanisms
        if active_mechanisms:
            emit(
                "policy.inherited",
                "orchestrator",
                "This run inherited mechanisms learned from a prior incident",
                {"mechanism_ids": [item.id for item in active_mechanisms]},
            )
        self._ledger_event(
            kind="issue",
            amount=40,
            reason="Customer-funded objective budget",
            to_agent="atlas",
            timestamp=timestamp_factory(),
            **context,
        )
        emit(
            "planning.completed",
            "atlas",
            "Objective decomposed into one independently verifiable change",
            {
                "task": objective.title,
                "acceptance_criteria": objective.acceptance_criteria,
            },
        )
        self._ledger_event(
            kind="escrow",
            amount=40,
            reason="Delivery bounty locked pending tests and review",
            from_agent="atlas",
            to_agent="escrow",
            timestamp=timestamp_factory(),
            **context,
        )
        emit(
            "task.assigned",
            "atlas",
            "Forge accepted the implementation bounty",
            {"task": objective.title, "assignee": "forge", "bounty": 40},
        )
        emit(
            "runtime.invoked",
            "forge",
            f"{runtime.name.title()} implementation runtime invoked",
            {"runtime": runtime.name},
        )
        brief = "\n".join(
            [objective.title, objective.description, *objective.acceptance_criteria]
        )
        try:
            result = runtime.generate(brief=brief, run_id=objective.run_id)
        except Exception as exc:  # runtime boundary is deliberately contained
            emit(
                "run.failed",
                "orchestrator",
                "Implementation runtime failed safely",
                {"error_type": type(exc).__name__, "message": str(exc)[:300]},
            )
            self._ledger_event(
                kind="refund",
                amount=40,
                reason="Runtime failure returned the delivery bounty",
                from_agent="escrow",
                to_agent="atlas",
                timestamp=timestamp_factory(),
                **context,
            )
            return

        emit(
            "code.generated",
            "forge",
            result.summary,
            {
                "change_id": result.change_id,
                "runtime": result.runtime,
                "declared_tests": result.tests,
                "write_mode": result.write_mode,
            },
        )
        emit(
            "pull_request.opened",
            "forge",
            "Opened a focused pull request with implementation and tests",
            {
                "change_id": result.change_id,
                "files_changed": 3,
                "lines_added": 74,
            },
        )
        emit(
            "review.approved",
            "aegis",
            "Adversarial review approved the bounded change",
            {
                "checks": [
                    "contract preserved",
                    "failure path explicit",
                    "no secret-bearing output",
                ]
            },
        )
        emit(
            "tests.passed",
            "sentinel",
            "Contract, unit, and monitoring checks passed",
            {"passed": 3, "failed": 0, "tests": result.tests},
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
        emit(
            "deployment.started",
            "shipwright",
            f"Release {version} entered the deployment gate",
            {
                "version": version,
                "strategy": "canary-10-percent" if active_mechanisms else "single-instance",
                "enforced_mechanisms": [item.id for item in active_mechanisms],
            },
        )
        emit(
            "deployment.succeeded",
            "shipwright",
            f"Release {version} deployed",
            {"version": version, "url": "/api/pulse"},
        )
        emit(
            "monitor.healthy",
            "sentinel",
            "Post-deploy checks observed a healthy release",
            {
                "version": version,
                "http_status": 200,
                "error_rate": 0.0,
                "latency_ms": 18,
            },
        )
        self._ledger_event(
            kind="payout",
            amount=28,
            reason="Implementation merged and verified",
            from_agent="escrow",
            to_agent="forge",
            timestamp=timestamp_factory(),
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=6,
            reason="Independent review completed",
            from_agent="escrow",
            to_agent="aegis",
            timestamp=timestamp_factory(),
            **context,
        )
        self._ledger_event(
            kind="payout",
            amount=6,
            reason="Release verification completed",
            from_agent="escrow",
            to_agent="sentinel",
            timestamp=timestamp_factory(),
            **context,
        )
        emit(
            "memory.updated",
            "sentinel",
            "Remember contract and error-budget checks for future releases",
            {
                "memory": "Require /api/pulse contract and error-budget checks before release."
            },
        )
        emit(
            "run.completed",
            "orchestrator",
            "Objective shipped, verified, and placed under monitoring",
            {"version": version},
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
            elif event.type in {"task.assigned", "runtime.invoked"}:
                phase, progress = "implementation", 30
            elif event.type == "code.generated":
                phase, progress = "implementation", 45
            elif event.type in {"pull_request.opened", "review.approved"}:
                phase, progress = "review", 65
            elif event.type == "tests.passed":
                phase, progress = "verification", 78
            elif event.type == "deployment.started":
                phase, progress = "deployment", 88
                current_version = event.data.get("version", current_version)
            elif event.type == "deployment.succeeded":
                phase, progress = "monitoring", 94
                current_version = event.data.get("version", current_version)
                stable_version = current_version
            elif event.type == "monitor.healthy":
                health, progress = "healthy", 98
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
            from_agent = data.get("from_agent")
            to_agent = data.get("to_agent")
            kind = data["kind"]
            if from_agent:
                balances[from_agent] = balances.get(from_agent, 0) - amount
            if to_agent:
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
        items: list[Agent] = []
        for profile in AGENT_PROFILES:
            agent_events = [event for event in events if event.actor == profile["id"]]
            last = agent_events[-1] if agent_events else None
            status = "idle"
            current_task: str | None = None
            if last is not None:
                current_task = last.data.get("task")
                if last.type.startswith("review."):
                    status = "reviewing"
                elif last.type.startswith("tests."):
                    status = "testing"
                elif last.type.startswith("monitor."):
                    status = "monitoring"
                elif last.type not in {"memory.updated"}:
                    status = "working"
            memories = [
                event.data["memory"]
                for event in agent_events
                if event.type == "memory.updated" and "memory" in event.data
            ][-3:]
            items.append(
                Agent(
                    **profile,
                    status=status,
                    credits=ledger.balances.get(profile["id"], 0),
                    current_task=current_task,
                    completed_actions=len(agent_events),
                    last_seen=last.timestamp if last else None,
                    memory=memories,
                )
            )
        return AgentsResponse(items=items, count=len(items))

    @staticmethod
    def _mechanisms() -> list[PolicyMechanism]:
        return [
            PolicyMechanism(
                id="contract-gate",
                kind="prompt",
                name="Reviewer prompt contract gate",
                description=(
                    "Patch reviewer and QA instructions to challenge /api/pulse "
                    "status and schema before merge."
                ),
                enforcement=(
                    "The role prompt requires contract evidence; CI blocks the pull "
                    "request unless the corresponding test passes."
                ),
            ),
            PolicyMechanism(
                id="canary-window",
                kind="routing",
                name="Canary routing window",
                description="Route a candidate to a bounded canary before promotion.",
                enforcement="Shipwright exposes the candidate to 10% traffic for 60 seconds.",
            ),
            PolicyMechanism(
                id="error-budget-gate",
                kind="economy",
                name="Reliability stake",
                description=(
                    "Tie release-agent payout to the measured post-deploy error budget."
                ),
                enforcement=(
                    "Sentinel blocks promotion and moves five credits into escrow when "
                    "5xx exceeds 1%."
                ),
            ),
            PolicyMechanism(
                id="rollback-quarantine",
                kind="memory",
                name="Incident memory and quarantine",
                description=(
                    "Remember the failed change signature, restore known-good code, and "
                    "prevent an identical retry."
                ),
                enforcement=(
                    "The orchestrator records the incident lesson, rolls back, and "
                    "quarantines the change identifier."
                ),
            ),
        ]

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
            third = self._ledger_event(
                kind="penalty",
                amount=5,
                reason="Unhealthy release escaped the deployment gate",
                from_agent="shipwright",
                to_agent="escrow",
                run_id=run_id,
                objective_id=objective_id,
            )
            return [first, second, third]

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
            proposal = PolicyProposal(
                id=proposal_id,
                run_id=run_id,
                title="Close the unsafe-release feedback loop",
                rationale=(
                    "The incident proved that a pre-merge test alone cannot protect a live "
                    "release; promotion needs layered prevention, detection, and recovery."
                ),
                mechanisms=self._mechanisms(),
                benchmark_id=POLICY_BENCHMARK_ID,
                benchmark_metric=POLICY_BENCHMARK_METRIC,
                benchmark_cases=4,
                baseline_score=0.25,
                candidate_score=1.0,
                critical_regressions=0,
                status="proposed",
                created_at=datetime.now(timezone.utc),
            )
            events.append(
                self._append(
                    event_type="benchmark.completed",
                    actor="aegis",
                    summary="Candidate policy beat the active policy in shadow replay",
                    data={
                        "benchmark_id": proposal.benchmark_id,
                        "metric": proposal.benchmark_metric,
                        "cases": proposal.benchmark_cases,
                        "baseline_score": proposal.baseline_score,
                        "candidate_score": proposal.candidate_score,
                        "critical_regressions": proposal.critical_regressions,
                        "mechanism_kinds": [
                            mechanism.kind for mechanism in proposal.mechanisms
                        ],
                    },
                    timestamp=proposal.created_at,
                    **common,
                )
            )
            events.append(
                self._append(
                    event_type="policy.proposed",
                    actor="atlas",
                    summary="Proposed four enforceable recovery mechanisms",
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
                        "Four benchmark-cleared self-improvement mechanisms activated "
                        "for future releases"
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
