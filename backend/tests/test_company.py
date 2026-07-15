from __future__ import annotations

import pytest

from app.services.company import (
    ENGINEER_IDS,
    PERSISTENT_AGENT_IDS,
    AgentStatus,
    AuctionError,
    AuctionTask,
    Bid,
    CompanyInvariantError,
    CredibilityEvidence,
    apply_company_event,
    auction_awarded_event,
    cycle_events,
    escaped_regression_events,
    initial_company_state,
    make_company_event,
    make_economy_event,
    memory_for_agent,
    memory_update_event,
    reconstruct_company,
    run_auction,
    seed_agents,
    task_completed_event,
    transactions_from_events,
)


def _task() -> AuctionTask:
    return AuctionTask(
        id="task_replay_filter",
        title="Add an evidence filter to Change Replay",
        required_capabilities=("implementation",),
        max_budget=30,
        minimum_credibility=0.65,
    )


def _evidence() -> list[CredibilityEvidence]:
    return [
        CredibilityEvidence(
            id="proof_forge_contracts",
            agent_id="forge",
            score=0.86,
            summary="Three prior backend contracts passed without regression.",
            references=("event_backend_checks",),
        ),
        CredibilityEvidence(
            id="proof_prism_ui",
            agent_id="prism",
            score=0.95,
            summary="Replay interaction tests and accessibility checks passed.",
            references=("event_ui_checks",),
        ),
        CredibilityEvidence(
            id="proof_rivet_delivery",
            agent_id="rivet",
            score=0.79,
            summary="Two container releases passed health verification.",
            references=("event_release_checks",),
        ),
    ]


def _bids() -> list[Bid]:
    return [
        Bid(
            task_id="task_replay_filter",
            engineer_id="forge",
            amount=12,
            plan="Add the typed filter and protect the API contract.",
            credibility=0.82,
            evidence_refs=("proof_forge_contracts",),
        ),
        Bid(
            task_id="task_replay_filter",
            engineer_id="prism",
            amount=9,
            plan="Add the filter control and verify keyboard interaction.",
            credibility=0.60,
            evidence_refs=("proof_prism_ui",),
        ),
        Bid(
            task_id="task_replay_filter",
            engineer_id="rivet",
            amount=11,
            plan="Add a platform-side filter with focused verification.",
            credibility=0.75,
            evidence_refs=("proof_rivet_delivery",),
        ),
    ]


def test_company_has_exactly_eight_complete_persistent_agents() -> None:
    agents = seed_agents()

    assert tuple(agents) == PERSISTENT_AGENT_IDS
    assert len(agents) == 8
    assert ENGINEER_IDS == ("forge", "prism", "rivet")
    assert [agents[agent_id].name for agent_id in PERSISTENT_AGENT_IDS] == [
        "Atlas",
        "Forge",
        "Prism",
        "Rivet",
        "Aegis",
        "Sentinel",
        "Shipwright",
        "Chronicle",
    ]
    assert all(agent.role for agent in agents.values())
    assert all(agent.capabilities for agent in agents.values())
    assert all(agent.personality for agent in agents.values())
    assert all(agent.memory_seed for agent in agents.values())
    assert all(agent.balance > 0 for agent in agents.values())
    assert all(agent.status == AgentStatus.AVAILABLE for agent in agents.values())


def test_initial_state_materializes_each_agents_memory_seed() -> None:
    state = initial_company_state()

    assert len(state.memories) == 16
    for agent in state.agents.values():
        assert [record.content for record in memory_for_agent(state, agent.id)] == list(
            agent.memory_seed
        )


def test_lowest_evidence_backed_credible_bid_wins() -> None:
    result = run_auction(_task(), _bids(), seed_agents(), _evidence())

    assert result.winner.engineer_id == "rivet"
    assert result.winner.amount == 11
    assessments = {item.bid.engineer_id: item for item in result.assessments}
    assert assessments["prism"].eligible is False
    assert "credibility-below-threshold" in assessments["prism"].reasons
    assert assessments["rivet"].evidence_score == pytest.approx(0.79)


def test_auction_rejects_claimed_credibility_without_own_evidence() -> None:
    bids = _bids()
    bids[0] = bids[0].model_copy(
        update={
            "amount": 1,
            "credibility": 0.99,
            "evidence_refs": ("proof_prism_ui",),
        }
    )

    result = run_auction(_task(), bids, seed_agents(), _evidence())

    forge = next(
        item for item in result.assessments if item.bid.engineer_id == "forge"
    )
    assert forge.eligible is False
    assert "foreign-evidence:proof_prism_ui" in forge.reasons
    assert "credibility-not-supported" in forge.reasons
    assert result.winner.engineer_id == "rivet"


def test_auction_requires_all_three_persistent_engineers() -> None:
    with pytest.raises(AuctionError, match="Forge, Prism, and Rivet"):
        run_auction(_task(), _bids()[:2], seed_agents(), _evidence())


def test_auction_event_is_deterministic_and_reconstructs_working_status() -> None:
    result = run_auction(_task(), _bids(), seed_agents(), _evidence())
    first = auction_awarded_event(result, sequence=7)
    second = auction_awarded_event(result, sequence=7)

    assert first == second
    assert first.references == ("proof_rivet_delivery",)
    state = reconstruct_company([first])
    assert state.agents["rivet"].status == AgentStatus.WORKING


def test_reward_and_penalty_rules_are_reconstructable_from_events() -> None:
    initial = initial_company_state()
    reward = make_economy_event(
        initial,
        rule_id="task-delivered",
        agent_id="forge",
        amount=17,
        sequence=1,
        task_id="task_api",
        references=("tests_passed", "review_approved"),
    )
    rewarded = apply_company_event(initial, reward)
    penalty = make_economy_event(
        rewarded,
        rule_id="task-rejected",
        agent_id="forge",
        sequence=2,
        task_id="task_api",
        references=("acceptance_failed",),
    )

    rebuilt = reconstruct_company([penalty, reward])
    transactions = transactions_from_events([penalty, reward])

    assert rebuilt.agents["forge"].balance == 69
    assert [transaction.delta for transaction in transactions] == [17, -8]
    assert transactions[0].references == ("tests_passed", "review_approved")


def test_escaped_regression_penalizes_engineer_and_reviewer() -> None:
    state = initial_company_state()
    engineer_event, reviewer_event = escaped_regression_events(
        state,
        engineer_id="prism",
        start_sequence=10,
        regression_event_id="monitor_http_500",
        task_id="task_replay",
    )

    rebuilt = reconstruct_company([reviewer_event, engineer_event])

    assert engineer_event.data["rule_id"] == "escaped-regression-engineer"
    assert reviewer_event.data["rule_id"] == "reviewer-escaped-regression"
    assert engineer_event.data["delta"] == -12
    assert reviewer_event.data["delta"] == -15
    assert rebuilt.agents["prism"].balance == 48
    assert rebuilt.agents["aegis"].balance == 45
    assert reviewer_event.references == ("monitor_http_500", engineer_event.id)


def test_penalty_is_capped_at_zero_then_agent_skips_cycle_dormant() -> None:
    initial = initial_company_state()
    agents = dict(initial.agents)
    agents["forge"] = agents["forge"].model_copy(update={"balance": 5})
    low_balance = initial.model_copy(update={"agents": agents})
    penalty = make_economy_event(
        low_balance,
        rule_id="task-rejected",
        agent_id="forge",
        sequence=1,
        references=("acceptance_failed",),
    )
    depleted = apply_company_event(low_balance, penalty)

    events = cycle_events(depleted, cycle_id="cycle_42", start_sequence=2)
    after_cycle = depleted
    for event in events:
        after_cycle = apply_company_event(after_cycle, event)

    assert penalty.data["delta"] == -5
    assert depleted.agents["forge"].balance == 0
    assert [event.type for event in events] == [
        "agent.status-changed",
        "cycle.skipped",
    ]
    assert after_cycle.agents["forge"].status == AgentStatus.DORMANT
    assert after_cycle.skipped_cycles[0].cycle_id == "cycle_42"


def test_dormant_agent_reactivates_on_the_cycle_after_funding() -> None:
    initial = initial_company_state()
    agents = dict(initial.agents)
    agents["chronicle"] = agents["chronicle"].model_copy(
        update={"balance": 0, "status": AgentStatus.DORMANT}
    )
    dormant = initial.model_copy(update={"agents": agents})
    funded = make_economy_event(
        dormant,
        rule_id="history-committed",
        agent_id="chronicle",
        sequence=1,
        references=("history_entry",),
    )
    state = apply_company_event(dormant, funded)

    events = cycle_events(state, cycle_id="cycle_43", start_sequence=2)
    reactivated = apply_company_event(state, events[0])

    assert state.agents["chronicle"].balance == 4
    assert events[0].data["status_after"] == "available"
    assert reactivated.agents["chronicle"].status == AgentStatus.AVAILABLE


def test_memory_update_preserves_source_references_through_reconstruction() -> None:
    event = memory_update_event(
        agent_id="aegis",
        content="Challenge promotion health after deploy, not only before it.",
        references=("incident_17", "benchmark_17"),
        sequence=3,
    )

    rebuilt = reconstruct_company([event])
    memory = memory_for_agent(rebuilt, "aegis")[-1]

    assert memory.content.startswith("Challenge promotion health")
    assert memory.references == ("incident_17", "benchmark_17")
    assert memory.source_event_id == event.id


def test_task_completion_returns_funded_worker_to_available() -> None:
    result = run_auction(_task(), _bids(), seed_agents(), _evidence())
    awarded = auction_awarded_event(result, sequence=1)
    working = apply_company_event(initial_company_state(), awarded)
    completed = task_completed_event(
        working,
        agent_id="rivet",
        task_id=_task().id,
        sequence=2,
        references=("checks_passed",),
    )

    final = apply_company_event(working, completed)

    assert final.agents["rivet"].status == AgentStatus.AVAILABLE
    assert completed.task_id == _task().id


def test_reconstruction_rejects_duplicate_event_sequences() -> None:
    first = make_company_event(
        sequence=1,
        event_type="note.recorded",
        actor="chronicle",
        summary="First note",
    )
    second = make_company_event(
        sequence=1,
        event_type="note.recorded",
        actor="chronicle",
        summary="Second note",
    )

    with pytest.raises(CompanyInvariantError, match="sequences must be unique"):
        reconstruct_company([first, second])
