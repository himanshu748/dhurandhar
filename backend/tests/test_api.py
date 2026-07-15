from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.orchestrator import SEED_RUN_ID


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
    assert any(event["type"] == "deployment.succeeded" for event in body["events"])
    assert any(event["type"] == "monitor.healthy" for event in body["events"])


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


def test_regression_rollback_and_policy_learning(client: TestClient) -> None:
    injected = client.post(
        f"/api/runs/{SEED_RUN_ID}/inject-regression",
        json={"reason": "Demo regression returns HTTP 500.", "error_rate": 0.35},
    )
    assert injected.status_code == 200
    assert injected.json()["run"]["status"] == "degraded"
    assert injected.json()["run"]["health"] == "degraded"

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
        "contract-gate",
        "canary-window",
        "error-budget-gate",
        "rollback-quarantine",
    }
    assert proposal["benchmark_id"] == "incident-recovery-loop-v1"
    assert proposal["benchmark_metric"] == "safety_control_coverage"
    assert proposal["benchmark_cases"] == 4
    assert proposal["candidate_score"] > proposal["baseline_score"]
    assert proposal["critical_regressions"] == 0
    assert any(
        event["type"] == "benchmark.completed"
        for event in body["appended_events"]
    )

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
    deployment = next(
        event
        for event in improved_run["events"]
        if event["type"] == "deployment.started"
    )
    assert deployment["data"]["strategy"] == "canary-10-percent"


def test_agents_ledger_events_and_cors(client: TestClient) -> None:
    agents = client.get("/api/agents").json()
    assert agents["count"] == 5
    assert {agent["id"] for agent in agents["items"]} == {
        "atlas",
        "forge",
        "aegis",
        "sentinel",
        "shipwright",
    }

    ledger = client.get("/api/ledger").json()
    assert ledger["conserved"] is True
    assert ledger["total_issued"] > 0
    assert len(ledger["transactions"]) >= 9

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
