from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.models.domain import ObjectiveCreate, PolicyProposal
from app.services.event_store import JsonlEventStore
from app.services.orchestrator import SEED_OBJECTIVE_ID, SEED_RUN_ID, Orchestrator
from app.services.runtime import DeterministicRuntime, RuntimeResult


class BriefCapturingRuntime(DeterministicRuntime):
    def __init__(self) -> None:
        self.implementation_briefs: list[str] = []
        self.review_briefs: list[str] = []

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult:
        self.implementation_briefs.append(brief)
        return super().generate(brief=brief, run_id=run_id)

    def review(
        self, *, brief: str, run_id: str, diff_context: str
    ) -> RuntimeResult:
        self.review_briefs.append(brief)
        return super().review(
            brief=brief,
            run_id=run_id,
            diff_context=diff_context,
        )


def test_legacy_policy_events_remain_readable_but_unbenchmarked() -> None:
    mechanisms = [
        mechanism.model_dump(exclude={"kind"})
        for mechanism in Orchestrator._mechanisms()
    ]

    proposal = PolicyProposal.model_validate(
        {
            "id": "policy_legacy",
            "run_id": SEED_RUN_ID,
            "title": "Legacy proposal",
            "rationale": "Created before benchmark metadata was persisted.",
            "mechanisms": mechanisms,
            "status": "proposed",
            "created_at": datetime.now(timezone.utc),
        }
    )

    assert {mechanism.kind for mechanism in proposal.mechanisms} == {
        "memory",
        "prompt",
        "routing",
        "economy",
    }
    assert proposal.benchmark_id == "legacy-unbenchmarked"
    assert proposal.candidate_score == proposal.baseline_score
    assert proposal.critical_regressions == 1


def _append_proposal(
    orchestrator: Orchestrator,
    *,
    proposal_id: str,
    baseline_score: float,
    candidate_score: float,
    critical_regressions: int,
) -> None:
    proposal = PolicyProposal(
        id=proposal_id,
        run_id=SEED_RUN_ID,
        title="Benchmark gate test proposal",
        rationale="Exercise the policy promotion guard through the public API.",
        mechanisms=orchestrator._mechanisms(),
        benchmark_id="gate-test-v1",
        benchmark_metric="pass_rate",
        benchmark_cases=4,
        baseline_score=baseline_score,
        candidate_score=candidate_score,
        critical_regressions=critical_regressions,
        status="proposed",
        created_at=datetime.now(timezone.utc),
    )
    orchestrator._append(
        event_type="policy.proposed",
        actor="atlas",
        summary=proposal.title,
        run_id=SEED_RUN_ID,
        objective_id=SEED_OBJECTIVE_ID,
        data={"proposal": proposal.model_dump(mode="json")},
        timestamp=proposal.created_at,
    )


def test_policy_approval_requires_candidate_to_beat_baseline(
    client: TestClient,
) -> None:
    orchestrator: Orchestrator = client.app.state.orchestrator
    _append_proposal(
        orchestrator,
        proposal_id="policy_equal_score",
        baseline_score=0.8,
        candidate_score=0.8,
        critical_regressions=0,
    )

    response = client.post(
        "/api/policies/proposals/policy_equal_score/decision",
        json={"decision": "approve"},
    )

    assert response.status_code == 409
    assert "candidate score must be greater" in response.json()["detail"]


def test_policy_approval_requires_zero_critical_regressions(
    client: TestClient,
) -> None:
    orchestrator: Orchestrator = client.app.state.orchestrator
    _append_proposal(
        orchestrator,
        proposal_id="policy_critical_regression",
        baseline_score=0.5,
        candidate_score=0.9,
        critical_regressions=1,
    )

    response = client.post(
        "/api/policies/proposals/policy_critical_regression/decision",
        json={"decision": "approve"},
    )

    assert response.status_code == 409
    assert "critical regressions must be zero" in response.json()["detail"]


def test_new_active_policy_supersedes_each_mechanism_kind(
    client: TestClient,
) -> None:
    orchestrator: Orchestrator = client.app.state.orchestrator
    for proposal_id, candidate_score in (("policy_active_1", 0.8), ("policy_active_2", 0.9)):
        _append_proposal(
            orchestrator,
            proposal_id=proposal_id,
            baseline_score=0.5,
            candidate_score=candidate_score,
            critical_regressions=0,
        )
        approved = client.post(
            f"/api/policies/proposals/{proposal_id}/decision",
            json={"decision": "approve"},
        )
        assert approved.status_code == 200

    policies = client.get("/api/policies").json()
    active = policies["active_mechanisms"]
    assert len(active) == 4
    assert [mechanism["kind"] for mechanism in active] == [
        "memory",
        "prompt",
        "routing",
        "economy",
    ]


def test_approved_incident_controls_are_inherited_by_both_runtime_briefs(
    tmp_path: Path,
) -> None:
    runtime = BriefCapturingRuntime()
    orchestrator = Orchestrator(
        JsonlEventStore(tmp_path / "events.jsonl"),
        runtime,
    )
    orchestrator.bootstrap_seeded_run()
    _append_proposal(
        orchestrator,
        proposal_id="policy_runtime_brief",
        baseline_score=0.0,
        candidate_score=1.0,
        critical_regressions=0,
    )
    orchestrator.decide_policy(
        "policy_runtime_brief",
        decision="approve",
        decided_by="operator-test",
    )
    objective = orchestrator.create_objective(
        ObjectiveCreate(title="Exercise inherited incident controls")
    )

    orchestrator.execute_objective(objective)

    assert orchestrator.run_summary(objective.run_id).status == "completed"
    assert len(runtime.implementation_briefs) == 1
    assert len(runtime.review_briefs) == 1
    expected_ids = {mechanism.id for mechanism in orchestrator._mechanisms()}
    for brief in [*runtime.implementation_briefs, *runtime.review_briefs]:
        assert "Operator-approved incident controls inherited by this run:" in brief
        assert all(mechanism_id in brief for mechanism_id in expected_ids)
    inherited = next(
        event
        for event in orchestrator.run_detail(objective.run_id).events
        if event.type == "policy.inherited"
    )
    assert inherited.data["runtime_brief_injection"] is True
    assert set(inherited.data["mechanism_ids"]) == expected_ids
    assert {item["id"] for item in inherited.data["mechanisms"]} == expected_ids
