from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyInvariantError(ValueError):
    """Raised when an event cannot be applied without breaking company state."""


class AuctionError(ValueError):
    """Raised when a task auction is malformed or has no credible winner."""


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentStatus(str, Enum):
    AVAILABLE = "available"
    WORKING = "working"
    DORMANT = "dormant"


class Agent(FrozenModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    capabilities: tuple[str, ...] = Field(min_length=1)
    personality: str = Field(min_length=1)
    memory_seed: tuple[str, ...] = Field(min_length=1)
    balance: int = Field(ge=0)
    status: AgentStatus


PERSISTENT_AGENT_IDS: tuple[str, ...] = (
    "atlas",
    "forge",
    "prism",
    "rivet",
    "aegis",
    "sentinel",
    "shipwright",
    "chronicle",
)
ENGINEER_IDS: tuple[str, ...] = ("forge", "prism", "rivet")


_AGENT_SEEDS: tuple[Agent, ...] = (
    Agent(
        id="atlas",
        name="Atlas",
        role="Product manager",
        capabilities=(
            "product-strategy",
            "task-decomposition",
            "acceptance-criteria",
            "auction-management",
        ),
        personality=(
            "Outcome-first and skeptical of vague work; turns ambition into small, "
            "independently verifiable bets."
        ),
        memory_seed=(
            "A task is not ready until its acceptance evidence is named.",
            "Prefer the smallest credible bid, never the cheapest unsupported promise.",
        ),
        balance=80,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="forge",
        name="Forge",
        role="Backend engineer",
        capabilities=(
            "implementation",
            "python",
            "fastapi",
            "event-sourcing",
            "backend-testing",
        ),
        personality=(
            "Methodical and contract-driven; favors small typed changes with executable "
            "proof over broad rewrites."
        ),
        memory_seed=(
            "Preserve API contracts unless the objective explicitly changes them.",
            "Every state transition needs a deterministic test or durable event.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="prism",
        name="Prism",
        role="Frontend engineer",
        capabilities=(
            "implementation",
            "react",
            "typescript",
            "accessibility",
            "frontend-testing",
        ),
        personality=(
            "Evidence-dense but human-centered; makes complicated state legible without "
            "hiding consequential detail."
        ),
        memory_seed=(
            "A user must be able to trace every visible claim back to source evidence.",
            "Keyboard access and narrow-screen behavior are release requirements.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="rivet",
        name="Rivet",
        role="Platform engineer",
        capabilities=(
            "implementation",
            "containers",
            "ci-cd",
            "observability",
            "infrastructure",
        ),
        personality=(
            "Reliability-biased and reversible by default; treats every rollout as an "
            "experiment with an exit path."
        ),
        memory_seed=(
            "A release is incomplete until health evidence and rollback are available.",
            "Keep credentials and irreversible operations outside autonomous scope.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="aegis",
        name="Aegis",
        role="Adversarial reviewer",
        capabilities=(
            "code-review",
            "threat-modeling",
            "regression-analysis",
            "policy-review",
        ),
        personality=(
            "Constructively adversarial; looks for the strongest counterexample before "
            "allowing a change to advance."
        ),
        memory_seed=(
            "Approval is a prediction whose quality is measured by escaped regressions.",
            "Challenge evidence provenance, not just implementation style.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="sentinel",
        name="Sentinel",
        role="QA and saboteur",
        capabilities=(
            "quality-assurance",
            "fault-injection",
            "contract-testing",
            "monitoring",
        ),
        personality=(
            "Curious and destructive in controlled environments; tries to falsify every "
            "claim before users do."
        ),
        memory_seed=(
            "A passing happy path is an invitation to attack the boundary conditions.",
            "Fault injection must be bounded, observable, and paired with recovery.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="shipwright",
        name="Shipwright",
        role="Release and recovery engineer",
        capabilities=(
            "release-management",
            "sandbox-promotion",
            "rollback",
            "incident-response",
        ),
        personality=(
            "Calm under failure and biased toward restoration; earns trust through "
            "reversible releases and measured health."
        ),
        memory_seed=(
            "Restore the last known-good state before debating the next improvement.",
            "Promotion requires live health evidence, not deployment completion alone.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
    Agent(
        id="chronicle",
        name="Chronicle",
        role="Historian",
        capabilities=(
            "provenance",
            "event-reconstruction",
            "memory-curation",
            "decision-summarization",
        ),
        personality=(
            "Precise and unsentimental; preserves what happened, why it happened, and "
            "which evidence supports the account."
        ),
        memory_seed=(
            "Never collapse observed facts and later interpretation into one record.",
            "A lesson without source references is a hypothesis, not durable memory.",
        ),
        balance=60,
        status=AgentStatus.AVAILABLE,
    ),
)


def seed_agents() -> dict[str, Agent]:
    """Return a fresh mapping containing the company's exact eight agents."""

    agents = {agent.id: agent.model_copy(deep=True) for agent in _AGENT_SEEDS}
    if tuple(agents) != PERSISTENT_AGENT_IDS:
        raise CompanyInvariantError("persistent agent seed order changed")
    return agents


class MemoryRecord(FrozenModel):
    id: str
    agent_id: str
    content: str = Field(min_length=1)
    kind: str = "lesson"
    references: tuple[str, ...] = ()
    source_event_id: str | None = None


class EconomyTransaction(FrozenModel):
    event_id: str
    sequence: int = Field(ge=1)
    agent_id: str
    rule_id: str
    kind: str
    amount: int = Field(ge=0)
    delta: int
    balance_before: int = Field(ge=0)
    balance_after: int = Field(ge=0)
    task_id: str | None = None
    references: tuple[str, ...] = Field(min_length=1)


class CycleSkip(FrozenModel):
    event_id: str
    sequence: int = Field(ge=1)
    cycle_id: str
    agent_id: str
    reason: str


class CompanyEvent(FrozenModel):
    id: str
    sequence: int = Field(ge=1)
    type: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    agent_id: str | None = None
    task_id: str | None = None
    references: tuple[str, ...] = ()
    data: dict[str, Any] = Field(default_factory=dict)


class CompanyState(FrozenModel):
    agents: dict[str, Agent]
    memories: tuple[MemoryRecord, ...]
    transactions: tuple[EconomyTransaction, ...] = ()
    skipped_cycles: tuple[CycleSkip, ...] = ()
    applied_event_ids: tuple[str, ...] = ()


def initial_company_state() -> CompanyState:
    agents = seed_agents()
    memories = tuple(
        MemoryRecord(
            id=f"memory:{agent.id}:seed:{index}",
            agent_id=agent.id,
            content=content,
            kind="seed",
        )
        for agent in agents.values()
        for index, content in enumerate(agent.memory_seed, start=1)
    )
    return CompanyState(agents=agents, memories=memories)


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def make_company_event(
    *,
    sequence: int,
    event_type: str,
    actor: str,
    summary: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    references: Sequence[str] = (),
    data: Mapping[str, Any] | None = None,
) -> CompanyEvent:
    """Build a deterministic event that can be persisted by any event store."""

    material = {
        "sequence": sequence,
        "type": event_type,
        "actor": actor,
        "summary": summary,
        "agent_id": agent_id,
        "task_id": task_id,
        "references": list(references),
        "data": dict(data or {}),
    }
    digest = hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()
    return CompanyEvent(
        id=f"company_{digest[:20]}",
        sequence=sequence,
        type=event_type,
        actor=actor,
        summary=summary,
        agent_id=agent_id,
        task_id=task_id,
        references=tuple(references),
        data=dict(data or {}),
    )


class CredibilityEvidence(FrozenModel):
    id: str
    agent_id: str
    score: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)
    references: tuple[str, ...] = ()


class AuctionTask(FrozenModel):
    id: str
    title: str = Field(min_length=1)
    required_capabilities: tuple[str, ...] = Field(min_length=1)
    max_budget: int = Field(gt=0)
    minimum_credibility: float = Field(default=0.65, ge=0.0, le=1.0)


class Bid(FrozenModel):
    task_id: str
    engineer_id: str
    amount: int = Field(gt=0)
    plan: str = Field(min_length=12)
    credibility: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("plan")
    @classmethod
    def plan_must_be_substantive(cls, value: str) -> str:
        if len(value.split()) < 3:
            raise ValueError("bid plan must contain at least three words")
        return value


class BidAssessment(FrozenModel):
    bid: Bid
    eligible: bool
    evidence_score: float = Field(ge=0.0, le=1.0)
    reasons: tuple[str, ...] = ()


class AuctionResult(FrozenModel):
    task: AuctionTask
    assessments: tuple[BidAssessment, ...]
    winner: Bid


def run_auction(
    task: AuctionTask,
    bids: Sequence[Bid],
    agents: Mapping[str, Agent],
    evidence: Sequence[CredibilityEvidence],
) -> AuctionResult:
    """Select the lowest evidence-backed credible bid from all three engineers.

    Cost is the primary ordering. Credibility only breaks equal-cost ties, followed
    by the stable engineer id. A self-reported credibility score is accepted only
    when the referenced evidence for that engineer supports it.
    """

    bidder_ids = [bid.engineer_id for bid in bids]
    if len(bidder_ids) != len(set(bidder_ids)):
        raise AuctionError("each engineer may submit exactly one bid")
    if set(bidder_ids) != set(ENGINEER_IDS):
        raise AuctionError("an auction requires one bid from Forge, Prism, and Rivet")

    evidence_by_id = {item.id: item for item in evidence}
    assessments: list[BidAssessment] = []
    for bid in sorted(bids, key=lambda item: item.engineer_id):
        reasons: list[str] = []
        agent = agents.get(bid.engineer_id)
        if bid.task_id != task.id:
            reasons.append("task-mismatch")
        if agent is None or bid.engineer_id not in ENGINEER_IDS:
            reasons.append("not-a-persistent-engineer")
        elif agent.status != AgentStatus.AVAILABLE or agent.balance == 0:
            reasons.append("engineer-unavailable")
        if agent is not None:
            missing_capabilities = sorted(
                set(task.required_capabilities) - set(agent.capabilities)
            )
            if missing_capabilities:
                reasons.append(
                    "missing-capabilities:" + ",".join(missing_capabilities)
                )
        if bid.amount > task.max_budget:
            reasons.append("over-budget")
        if bid.credibility < task.minimum_credibility:
            reasons.append("credibility-below-threshold")

        supporting: list[CredibilityEvidence] = []
        for reference in bid.evidence_refs:
            item = evidence_by_id.get(reference)
            if item is None:
                reasons.append(f"missing-evidence:{reference}")
            elif item.agent_id != bid.engineer_id:
                reasons.append(f"foreign-evidence:{reference}")
            else:
                supporting.append(item)
        evidence_score = (
            sum(item.score for item in supporting) / len(supporting)
            if supporting
            else 0.0
        )
        if evidence_score < bid.credibility:
            reasons.append("credibility-not-supported")
        assessments.append(
            BidAssessment(
                bid=bid,
                eligible=not reasons,
                evidence_score=evidence_score,
                reasons=tuple(reasons),
            )
        )

    eligible = [assessment for assessment in assessments if assessment.eligible]
    if not eligible:
        raise AuctionError("auction has no evidence-backed credible bid")
    winning_assessment = min(
        eligible,
        key=lambda item: (
            item.bid.amount,
            -item.bid.credibility,
            -item.evidence_score,
            item.bid.engineer_id,
        ),
    )
    return AuctionResult(
        task=task,
        assessments=tuple(assessments),
        winner=winning_assessment.bid,
    )


def auction_awarded_event(result: AuctionResult, *, sequence: int) -> CompanyEvent:
    assessment = next(
        item
        for item in result.assessments
        if item.bid.engineer_id == result.winner.engineer_id
    )
    return make_company_event(
        sequence=sequence,
        event_type="auction.awarded",
        actor="atlas",
        agent_id=result.winner.engineer_id,
        task_id=result.task.id,
        references=result.winner.evidence_refs,
        summary=(
            f"{result.winner.engineer_id} won the task auction at "
            f"{result.winner.amount} credits"
        ),
        data={
            "winner": result.winner.model_dump(mode="json"),
            "evidence_score": assessment.evidence_score,
            "assessments": [
                item.model_dump(mode="json") for item in result.assessments
            ],
        },
    )


class RuleKind(str, Enum):
    REWARD = "reward"
    PENALTY = "penalty"


class EconomyRule(FrozenModel):
    id: str
    kind: RuleKind
    amount: int | None = Field(default=None, gt=0)
    allowed_agent_ids: tuple[str, ...] = Field(min_length=1)
    description: str


REWARD_RULES: dict[str, EconomyRule] = {
    "planning-accepted": EconomyRule(
        id="planning-accepted",
        kind=RuleKind.REWARD,
        amount=6,
        allowed_agent_ids=("atlas",),
        description="A bounded plan passed its acceptance-evidence gate.",
    ),
    "task-delivered": EconomyRule(
        id="task-delivered",
        kind=RuleKind.REWARD,
        amount=None,
        allowed_agent_ids=ENGINEER_IDS,
        description="An auctioned implementation passed its acceptance checks.",
    ),
    "review-defect-caught": EconomyRule(
        id="review-defect-caught",
        kind=RuleKind.REWARD,
        amount=8,
        allowed_agent_ids=("aegis",),
        description="Adversarial review prevented a verified defect from escaping.",
    ),
    "sabotage-found-regression": EconomyRule(
        id="sabotage-found-regression",
        kind=RuleKind.REWARD,
        amount=8,
        allowed_agent_ids=("sentinel",),
        description="A controlled QA attack exposed a real regression.",
    ),
    "recovery-succeeded": EconomyRule(
        id="recovery-succeeded",
        kind=RuleKind.REWARD,
        amount=10,
        allowed_agent_ids=("shipwright",),
        description="Recovery restored the last known-good release and health probe.",
    ),
    "history-committed": EconomyRule(
        id="history-committed",
        kind=RuleKind.REWARD,
        amount=4,
        allowed_agent_ids=("chronicle",),
        description="A source-linked decision record was added to durable memory.",
    ),
}


PENALTY_RULES: dict[str, EconomyRule] = {
    "task-rejected": EconomyRule(
        id="task-rejected",
        kind=RuleKind.PENALTY,
        amount=8,
        allowed_agent_ids=ENGINEER_IDS,
        description="Delivered work failed its stated acceptance evidence.",
    ),
    "escaped-regression-engineer": EconomyRule(
        id="escaped-regression-engineer",
        kind=RuleKind.PENALTY,
        amount=12,
        allowed_agent_ids=ENGINEER_IDS,
        description="An accepted implementation caused a confirmed regression.",
    ),
    "reviewer-escaped-regression": EconomyRule(
        id="reviewer-escaped-regression",
        kind=RuleKind.PENALTY,
        amount=15,
        allowed_agent_ids=("aegis",),
        description="Aegis approved a change that later caused a confirmed regression.",
    ),
    "qa-missed-regression": EconomyRule(
        id="qa-missed-regression",
        kind=RuleKind.PENALTY,
        amount=10,
        allowed_agent_ids=("sentinel",),
        description="The verification plan omitted a reproducible regression path.",
    ),
    "unsafe-release": EconomyRule(
        id="unsafe-release",
        kind=RuleKind.PENALTY,
        amount=10,
        allowed_agent_ids=("shipwright",),
        description="A release advanced without required health evidence.",
    ),
}


def make_economy_event(
    state: CompanyState,
    *,
    rule_id: str,
    agent_id: str,
    sequence: int,
    references: Sequence[str],
    amount: int | None = None,
    task_id: str | None = None,
) -> CompanyEvent:
    """Create one rule-governed reward or balance-capped penalty event."""

    if not references:
        raise CompanyInvariantError("economy events require evidence references")
    rule = REWARD_RULES.get(rule_id) or PENALTY_RULES.get(rule_id)
    if rule is None:
        raise CompanyInvariantError(f"unknown economy rule: {rule_id}")
    agent = state.agents.get(agent_id)
    if agent is None:
        raise CompanyInvariantError(f"unknown persistent agent: {agent_id}")
    if agent_id not in rule.allowed_agent_ids:
        raise CompanyInvariantError(
            f"economy rule {rule_id} cannot target agent {agent_id}"
        )
    if rule.amount is None:
        if amount is None or amount <= 0:
            raise CompanyInvariantError(
                f"economy rule {rule_id} requires a positive amount"
            )
        nominal_amount = amount
    else:
        if amount is not None and amount != rule.amount:
            raise CompanyInvariantError(
                f"economy rule {rule_id} has a fixed amount of {rule.amount}"
            )
        nominal_amount = rule.amount

    if rule.kind == RuleKind.REWARD:
        delta = nominal_amount
    else:
        delta = -min(nominal_amount, agent.balance)
    balance_after = agent.balance + delta
    return make_company_event(
        sequence=sequence,
        event_type=f"economy.{rule.kind.value}",
        actor="economy",
        agent_id=agent_id,
        task_id=task_id,
        references=references,
        summary=f"{agent.name}: {delta:+d} credits — {rule.description}",
        data={
            "rule_id": rule.id,
            "kind": rule.kind.value,
            "nominal_amount": nominal_amount,
            "delta": delta,
            "balance_before": agent.balance,
            "balance_after": balance_after,
        },
    )


def transaction_from_event(event: CompanyEvent) -> EconomyTransaction:
    if event.type not in {"economy.reward", "economy.penalty"}:
        raise CompanyInvariantError(f"event {event.id} is not an economy transaction")
    if event.agent_id is None:
        raise CompanyInvariantError("economy transaction has no target agent")
    return EconomyTransaction(
        event_id=event.id,
        sequence=event.sequence,
        agent_id=event.agent_id,
        rule_id=str(event.data["rule_id"]),
        kind=str(event.data["kind"]),
        amount=abs(int(event.data["delta"])),
        delta=int(event.data["delta"]),
        balance_before=int(event.data["balance_before"]),
        balance_after=int(event.data["balance_after"]),
        task_id=event.task_id,
        references=event.references,
    )


def transactions_from_events(
    events: Iterable[CompanyEvent],
) -> tuple[EconomyTransaction, ...]:
    return tuple(
        transaction_from_event(event)
        for event in sorted(events, key=lambda item: item.sequence)
        if event.type in {"economy.reward", "economy.penalty"}
    )


def escaped_regression_events(
    state: CompanyState,
    *,
    engineer_id: str,
    start_sequence: int,
    regression_event_id: str,
    task_id: str | None = None,
) -> tuple[CompanyEvent, CompanyEvent]:
    """Penalize both the implementer and Aegis for an escaped regression."""

    engineer_event = make_economy_event(
        state,
        rule_id="escaped-regression-engineer",
        agent_id=engineer_id,
        sequence=start_sequence,
        references=(regression_event_id,),
        task_id=task_id,
    )
    after_engineer = apply_company_event(state, engineer_event)
    reviewer_event = make_economy_event(
        after_engineer,
        rule_id="reviewer-escaped-regression",
        agent_id="aegis",
        sequence=start_sequence + 1,
        references=(regression_event_id, engineer_event.id),
        task_id=task_id,
    )
    return engineer_event, reviewer_event


def memory_update_event(
    *,
    agent_id: str,
    content: str,
    references: Sequence[str],
    sequence: int,
    kind: str = "lesson",
    actor: str = "chronicle",
) -> CompanyEvent:
    if agent_id not in PERSISTENT_AGENT_IDS:
        raise CompanyInvariantError(f"unknown persistent agent: {agent_id}")
    if not content.strip():
        raise CompanyInvariantError("memory content cannot be blank")
    if not references:
        raise CompanyInvariantError("durable memory requires source references")
    return make_company_event(
        sequence=sequence,
        event_type="memory.updated",
        actor=actor,
        agent_id=agent_id,
        references=references,
        summary=f"Source-linked {kind} recorded for {agent_id}",
        data={"content": content.strip(), "kind": kind},
    )


def memory_for_agent(
    state: CompanyState, agent_id: str
) -> tuple[MemoryRecord, ...]:
    if agent_id not in state.agents:
        raise CompanyInvariantError(f"unknown persistent agent: {agent_id}")
    return tuple(item for item in state.memories if item.agent_id == agent_id)


def _status_event(
    *,
    agent: Agent,
    status: AgentStatus,
    sequence: int,
    summary: str,
    references: Sequence[str] = (),
    cycle_id: str | None = None,
) -> CompanyEvent:
    return make_company_event(
        sequence=sequence,
        event_type="agent.status-changed",
        actor="orchestrator",
        agent_id=agent.id,
        references=references,
        summary=summary,
        data={
            "status_before": agent.status.value,
            "status_after": status.value,
            "cycle_id": cycle_id,
        },
    )


def cycle_events(
    state: CompanyState, *, cycle_id: str, start_sequence: int
) -> tuple[CompanyEvent, ...]:
    """Emit status and skip events for the zero-balance dormancy rule."""

    sequence = start_sequence
    events: list[CompanyEvent] = []
    for agent_id in PERSISTENT_AGENT_IDS:
        agent = state.agents[agent_id]
        if agent.balance == 0:
            if agent.status != AgentStatus.DORMANT:
                events.append(
                    _status_event(
                        agent=agent,
                        status=AgentStatus.DORMANT,
                        sequence=sequence,
                        summary=f"{agent.name} entered dormancy at zero balance",
                        cycle_id=cycle_id,
                    )
                )
                sequence += 1
            events.append(
                make_company_event(
                    sequence=sequence,
                    event_type="cycle.skipped",
                    actor="orchestrator",
                    agent_id=agent.id,
                    summary=f"{agent.name} skipped cycle {cycle_id}: zero balance",
                    data={"cycle_id": cycle_id, "reason": "zero-balance"},
                )
            )
            sequence += 1
        elif agent.status == AgentStatus.DORMANT:
            events.append(
                _status_event(
                    agent=agent,
                    status=AgentStatus.AVAILABLE,
                    sequence=sequence,
                    summary=f"{agent.name} reactivated after receiving funds",
                    cycle_id=cycle_id,
                )
            )
            sequence += 1
    return tuple(events)


def task_completed_event(
    state: CompanyState,
    *,
    agent_id: str,
    task_id: str,
    sequence: int,
    references: Sequence[str],
) -> CompanyEvent:
    agent = state.agents.get(agent_id)
    if agent is None:
        raise CompanyInvariantError(f"unknown persistent agent: {agent_id}")
    if not references:
        raise CompanyInvariantError("task completion requires evidence references")
    status = (
        AgentStatus.DORMANT if agent.balance == 0 else AgentStatus.AVAILABLE
    )
    return make_company_event(
        sequence=sequence,
        event_type="agent.status-changed",
        actor="orchestrator",
        agent_id=agent.id,
        task_id=task_id,
        references=references,
        summary=f"{agent.name} completed task {task_id}",
        data={
            "status_before": agent.status.value,
            "status_after": status.value,
            "cycle_id": None,
        },
    )


def apply_company_event(state: CompanyState, event: CompanyEvent) -> CompanyState:
    """Apply one company event without touching storage, clocks, or the network."""

    if event.id in state.applied_event_ids:
        raise CompanyInvariantError(f"event already applied: {event.id}")
    agents = dict(state.agents)
    memories = list(state.memories)
    transactions = list(state.transactions)
    skipped_cycles = list(state.skipped_cycles)

    if event.type in {"economy.reward", "economy.penalty"}:
        transaction = transaction_from_event(event)
        agent = agents.get(transaction.agent_id)
        if agent is None:
            raise CompanyInvariantError(
                f"transaction targets unknown agent: {transaction.agent_id}"
            )
        if agent.balance != transaction.balance_before:
            raise CompanyInvariantError(
                f"balance mismatch for {agent.id}: expected {agent.balance}, "
                f"event recorded {transaction.balance_before}"
            )
        if transaction.balance_after != agent.balance + transaction.delta:
            raise CompanyInvariantError("transaction balance arithmetic is invalid")
        if transaction.balance_after < 0:
            raise CompanyInvariantError("agent balance cannot become negative")
        agents[agent.id] = agent.model_copy(
            update={"balance": transaction.balance_after}
        )
        transactions.append(transaction)
    elif event.type == "memory.updated":
        if event.agent_id not in agents:
            raise CompanyInvariantError("memory event targets an unknown agent")
        if not event.references:
            raise CompanyInvariantError("durable memory has no source references")
        memories.append(
            MemoryRecord(
                id=f"memory:{event.id}",
                agent_id=event.agent_id,
                content=str(event.data["content"]),
                kind=str(event.data.get("kind", "lesson")),
                references=event.references,
                source_event_id=event.id,
            )
        )
    elif event.type == "auction.awarded":
        if event.agent_id not in ENGINEER_IDS:
            raise CompanyInvariantError("auction winner is not a persistent engineer")
        agent = agents[event.agent_id]
        if agent.balance == 0 or agent.status != AgentStatus.AVAILABLE:
            raise CompanyInvariantError("auction winner is not available")
        agents[agent.id] = agent.model_copy(update={"status": AgentStatus.WORKING})
    elif event.type == "agent.status-changed":
        if event.agent_id not in agents:
            raise CompanyInvariantError("status event targets an unknown agent")
        agent = agents[event.agent_id]
        recorded_before = AgentStatus(str(event.data["status_before"]))
        if agent.status != recorded_before:
            raise CompanyInvariantError(
                f"status mismatch for {agent.id}: expected {agent.status.value}, "
                f"event recorded {recorded_before.value}"
            )
        status_after = AgentStatus(str(event.data["status_after"]))
        if status_after != AgentStatus.DORMANT and agent.balance == 0:
            raise CompanyInvariantError("a zero-balance agent must remain dormant")
        agents[agent.id] = agent.model_copy(update={"status": status_after})
    elif event.type == "cycle.skipped":
        if event.agent_id not in agents:
            raise CompanyInvariantError("cycle skip targets an unknown agent")
        agent = agents[event.agent_id]
        if agent.balance != 0:
            raise CompanyInvariantError("only a zero-balance agent may skip a cycle")
        skipped_cycles.append(
            CycleSkip(
                event_id=event.id,
                sequence=event.sequence,
                cycle_id=str(event.data["cycle_id"]),
                agent_id=agent.id,
                reason=str(event.data["reason"]),
            )
        )

    return CompanyState(
        agents=agents,
        memories=tuple(memories),
        transactions=tuple(transactions),
        skipped_cycles=tuple(skipped_cycles),
        applied_event_ids=(*state.applied_event_ids, event.id),
    )


def reconstruct_company(events: Iterable[CompanyEvent]) -> CompanyState:
    """Rebuild the complete company snapshot from an unordered event collection."""

    ordered = sorted(events, key=lambda item: (item.sequence, item.id))
    sequences = [event.sequence for event in ordered]
    if len(sequences) != len(set(sequences)):
        raise CompanyInvariantError("company event sequences must be unique")
    event_ids = [event.id for event in ordered]
    if len(event_ids) != len(set(event_ids)):
        raise CompanyInvariantError("company event ids must be unique")
    state = initial_company_state()
    for event in ordered:
        state = apply_company_event(state, event)
    return state


__all__ = [
    "Agent",
    "AgentStatus",
    "AuctionError",
    "AuctionResult",
    "AuctionTask",
    "Bid",
    "BidAssessment",
    "CompanyEvent",
    "CompanyInvariantError",
    "CompanyState",
    "CredibilityEvidence",
    "CycleSkip",
    "EconomyRule",
    "EconomyTransaction",
    "ENGINEER_IDS",
    "MemoryRecord",
    "PENALTY_RULES",
    "PERSISTENT_AGENT_IDS",
    "REWARD_RULES",
    "apply_company_event",
    "auction_awarded_event",
    "cycle_events",
    "escaped_regression_events",
    "initial_company_state",
    "make_company_event",
    "make_economy_event",
    "memory_for_agent",
    "memory_update_event",
    "reconstruct_company",
    "run_auction",
    "seed_agents",
    "task_completed_event",
    "transaction_from_event",
    "transactions_from_events",
]
