from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.orchestrator import SEED_RUN_ID


def test_frontend_index_and_direct_replay_route_serve_the_same_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    index = "<!doctype html><title>Dhurandhar route shell</title>"
    frontend_dist.joinpath("index.html").write_text(index, encoding="utf-8")
    monkeypatch.setattr("app.main.FRONTEND_DIST", frontend_dist)

    settings = Settings(
        event_log_path=tmp_path / "route-events.jsonl",
        seed_demo=False,
    )
    with TestClient(create_app(settings)) as route_client:
        assert route_client.get("/").text == index
        assert route_client.get("/replay").text == index
        assert route_client.get("/replay/").text == index


def test_seeded_state_exposes_complete_auditable_run(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["event_chain_valid"] is True
    assert health.json()["events"] >= 20

    objectives = client.get("/api/objectives").json()
    assert len(objectives) == 1
    assert objectives[0]["status"] == "completed"

    replay = client.get(f"/api/replay/{SEED_RUN_ID}")
    assert replay.status_code == 200
    body = replay.json()
    assert body["run"]["status"] == "completed"
    assert body["run"]["health"] == "healthy"
    assert body["run"]["current_version"] == body["run"]["stable_version"]
    assert len(body["frames"]) == len(body["events"])
    assert body["chain"]["valid"] is True
    assert any(event["type"] == "auction.opened" for event in body["events"])
    assert sum(event["type"] == "bid.submitted" for event in body["events"]) == 3
    assert any(event["type"] == "auction.awarded" for event in body["events"])
    assert not any(event["type"] == "pull_request.opened" for event in body["events"])
    generated = next(
        event for event in body["events"] if event["type"] == "code.generated"
    )
    assert generated["data"]["provenance"] == "fixture"
    assert generated["data"]["thread_id"] is None
    review = next(
        event for event in body["events"] if event["type"] == "review.completed"
    )
    assert review["data"]["verdict"] == "approved"
    assert review["data"]["provenance"] == "fixture"
    assert any(event["type"] == "deployment.succeeded" for event in body["events"])
    assert any(event["type"] == "monitor.healthy" for event in body["events"])
    deployment = next(
        event for event in body["events"] if event["type"] == "deployment.succeeded"
    )
    assert deployment["data"]["environment"] == "demo-sandbox"
    assert deployment["data"]["external_deployment"] is False
    assert any(event["type"] == "changelog.written" for event in body["events"])
    pulse = client.get("/api/pulse")
    assert pulse.status_code == 200
    assert pulse.json() == {
        "status": "operational",
        "release": "0.1.0",
        "monitored_by": "sentinel",
        "self_hosted_objective": "obj_seed_self_hosting_v1",
        "evidence_scope": "demo-sandbox",
        "external_observation": False,
    }


def test_objective_executes_in_background(client: TestClient) -> None:
    response = client.post(
        "/api/objectives",
        json={
            "title": "Add a dependency readiness signal",
            "description": "Expose dependency health without leaking configuration.",
            "acceptance_criteria": [
                "Response is typed",
                "Contract test passes",
            ],
            "priority": "urgent",
        },
    )
    assert response.status_code == 202
    created = response.json()
    assert created["status"] == "queued"

    run = client.get(f"/api/runs/{created['run_id']}")
    assert run.status_code == 200
    assert run.json()["run"]["status"] == "completed"
    assert run.json()["run"]["progress"] == 100
    assert any(
        event["type"] == "runtime.invoked" for event in run.json()["events"]
    )
    recalled = [
        event for event in run.json()["events"] if event["type"] == "memory.recalled"
    ]
    assert {event["actor"] for event in recalled} == {
        "atlas",
        "forge",
        "prism",
        "rivet",
        "aegis",
        "sentinel",
        "shipwright",
        "chronicle",
    }
    assert any(
        any("acceptance evidence" in item["content"].lower() for item in event["data"]["memories"])
        for event in recalled
    )


def test_regression_rollback_and_policy_learning(client: TestClient) -> None:
    injected = client.post(
        f"/api/runs/{SEED_RUN_ID}/inject-regression",
        json={"reason": "Demo regression returns HTTP 500.", "error_rate": 0.35},
    )
    assert injected.status_code == 200
    assert injected.json()["run"]["status"] == "degraded"
    assert injected.json()["run"]["health"] == "degraded"
    degraded_pulse = client.get("/api/pulse")
    assert degraded_pulse.status_code == 503
    assert degraded_pulse.json()["status"] == "degraded"
    assert degraded_pulse.json()["external_observation"] is False
    incident_penalties = [
        transaction
        for transaction in client.get("/api/ledger").json()["transactions"]
        if transaction["run_id"] == SEED_RUN_ID
        and transaction["kind"] == "penalty"
    ]
    awarded = next(
        event
        for event in client.get(f"/api/runs/{SEED_RUN_ID}").json()["events"]
        if event["type"] == "auction.awarded"
    )
    assert {transaction["from_agent"] for transaction in incident_penalties} == {
        awarded["data"]["winner"],
        "aegis",
        "sentinel",
        "shipwright",
    }

    duplicate = client.post(
        f"/api/runs/{SEED_RUN_ID}/inject-regression",
        json={"reason": "Should not stack incidents."},
    )
    assert duplicate.status_code == 409

    recovery = client.post(
        f"/api/runs/{SEED_RUN_ID}/rollback",
        json={"reason": "Restore the measured known-good release."},
    )
    assert recovery.status_code == 200
    body = recovery.json()
    assert body["run"]["status"] == "recovered"
    assert body["run"]["health"] == "healthy"
    recovered_pulse = client.get("/api/pulse")
    assert recovered_pulse.status_code == 200
    assert recovered_pulse.json()["status"] == "operational"
    proposal = body["proposal"]
    assert proposal["status"] == "proposed"
    assert len(proposal["mechanisms"]) == 4
    assert {item["kind"] for item in proposal["mechanisms"]} == {
        "memory",
        "prompt",
        "routing",
        "economy",
    }
    assert {item["id"] for item in proposal["mechanisms"]} == {
        "independent-review-gate",
        "sentinel-static-check-gate",
        "health-evidence-escrow",
        "incident-policy-memory",
    }
    assert proposal["benchmark_id"] == "deterministic-structural-control-coverage-v1"
    assert (
        proposal["benchmark_metric"]
        == "deterministic_structural_control_coverage"
    )
    assert proposal["benchmark_cases"] == 4
    assert proposal["baseline_score"] == 0.0
    assert proposal["candidate_score"] == 1.0
    assert proposal["critical_regressions"] == 0
    benchmark = next(
        event
        for event in body["appended_events"]
        if event["type"] == "benchmark.completed"
    )
    assert benchmark["summary"].startswith(
        "Deterministic structural control-coverage check"
    )
    assert benchmark["data"]["evaluation_scope"] == "structure-only-not-efficacy"
    assert benchmark["data"]["deterministic"] is True
    assert benchmark["data"]["baseline_mechanism_kinds"] == []
    assert benchmark["data"]["candidate_mechanism_kinds"] == [
        "memory",
        "prompt",
        "routing",
        "economy",
    ]

    approved = client.post(
        f"/api/policies/proposals/{proposal['id']}/decision",
        json={"decision": "approve", "decided_by": "demo-operator"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"

    policies = client.get("/api/policies").json()
    assert policies["count"] == 1
    assert len(policies["active_mechanisms"]) == 4
    assert client.post(
        f"/api/policies/proposals/{proposal['id']}/decision",
        json={"decision": "reject"},
    ).status_code == 409

    improved = client.post(
        "/api/objectives",
        json={"title": "Ship through the learned release policy"},
    ).json()
    improved_run = client.get(f"/api/runs/{improved['run_id']}").json()
    inherited = [
        event
        for event in improved_run["events"]
        if event["type"] == "policy.inherited"
    ]
    assert len(inherited) == 1
    assert len(inherited[0]["data"]["mechanism_ids"]) == 4
    assert inherited[0]["data"]["runtime_brief_injection"] is True
    assert {
        item["id"] for item in inherited[0]["data"]["mechanisms"]
    } == set(inherited[0]["data"]["mechanism_ids"])
    deployment = next(
        event
        for event in improved_run["events"]
        if event["type"] == "deployment.started"
    )
    assert deployment["data"]["strategy"] == "policy-gated-demo-sandbox"

    reinjected = client.post(
        f"/api/runs/{improved['run_id']}/inject-regression",
        json={"reason": "Recheck structural policy coverage.", "error_rate": 0.2},
    )
    assert reinjected.status_code == 200
    second_recovery = client.post(
        f"/api/runs/{improved['run_id']}/rollback",
        json={"reason": "Restore and recompute from the active mechanism kinds."},
    )
    assert second_recovery.status_code == 200
    second_proposal = second_recovery.json()["proposal"]
    assert second_proposal["baseline_score"] == 1.0
    assert second_proposal["candidate_score"] == 1.0
    not_an_improvement = client.post(
        f"/api/policies/proposals/{second_proposal['id']}/decision",
        json={"decision": "approve", "decided_by": "demo-operator"},
    )
    assert not_an_improvement.status_code == 409
    assert "candidate score must be greater" in not_an_improvement.json()["detail"]


def test_agents_ledger_events_and_cors(client: TestClient) -> None:
    agents = client.get("/api/agents").json()
    assert agents["count"] == 8
    assert {agent["id"] for agent in agents["items"]} == {
        "atlas",
        "forge",
        "prism",
        "rivet",
        "aegis",
        "sentinel",
        "shipwright",
        "chronicle",
    }
    assert all(agent["capabilities"] for agent in agents["items"])
    assert all(agent["personality"] for agent in agents["items"])
    assert all(agent["memory_count"] >= 3 for agent in agents["items"])
    assert {agent["status"] for agent in agents["items"]} == {"idle"}
    assert all(agent["current_task"] is None for agent in agents["items"])

    ledger = client.get("/api/ledger").json()
    assert ledger["conserved"] is True
    assert ledger["total_issued"] > 0
    assert len(ledger["transactions"]) >= 19
    assert sum(
        transaction["kind"] == "bid_fee"
        for transaction in ledger["transactions"]
    ) == 3

    filtered = client.get(
        "/api/events",
        params={"run_id": SEED_RUN_ID, "type": "tests.passed", "limit": 5},
    ).json()
    assert filtered["count"] == 1
    assert filtered["items"][0]["actor"] == "sentinel"

    preflight = client.options(
        "/api/objectives",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_validation_and_missing_resources_are_explicit(client: TestClient) -> None:
    invalid = client.post("/api/objectives", json={"title": "x"})
    assert invalid.status_code == 422
    missing = client.get("/api/replay/run_missing")
    assert missing.status_code == 404
    assert "not found" in missing.json()["detail"]


def test_production_mutations_are_disabled_without_operator_token(
    tmp_path: Path,
) -> None:
    settings = Settings(
        environment="production",
        event_log_path=tmp_path / "production.jsonl",
        seed_demo=True,
    )
    with TestClient(create_app(settings)) as production:
        assert production.get("/api/replay/run_seed_self_hosting_v1").status_code == 200
        blocked = production.post(
            "/api/objectives",
            json={"title": "This must not execute"},
        )
        assert blocked.status_code == 503
        assert "mutations are disabled" in blocked.json()["detail"]


def test_operator_token_protects_mutations_without_entering_payloads(
    tmp_path: Path,
) -> None:
    token = "operator-token-for-focused-tests"
    settings = Settings(
        environment="production",
        event_log_path=tmp_path / "protected.jsonl",
        seed_demo=True,
        operator_token=token,
    )
    with TestClient(create_app(settings)) as production:
        payload = {"title": "Authorized bounded objective"}
        assert production.post("/api/objectives", json=payload).status_code == 403
        assert production.post(
            "/api/objectives",
            json=payload,
            headers={"X-Dhurandhar-Operator-Token": "wrong-token-value"},
        ).status_code == 403
        allowed = production.post(
            "/api/objectives",
            json=payload,
            headers={"X-Dhurandhar-Operator-Token": token},
        )
        assert allowed.status_code == 202
        events = production.get(
            "/api/events",
            params={"objective_id": allowed.json()["id"]},
        ).json()["items"]
        assert all(token not in str(event) for event in events)
