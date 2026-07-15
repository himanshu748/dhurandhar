from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ObjectivePriority(str, Enum):
    STANDARD = "standard"
    URGENT = "urgent"


class ObjectiveStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    DEGRADED = "degraded"
    RECOVERED = "recovered"
    FAILED = "failed"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    DEGRADED = "degraded"
    RECOVERED = "recovered"
    FAILED = "failed"


class PolicyStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"


class ObjectiveCreate(ApiModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2_000)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=8)
    priority: ObjectivePriority = ObjectivePriority.STANDARD

    @field_validator("title", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_criteria(cls, values: list[str]) -> list[str]:
        cleaned = [" ".join(value.split()) for value in values if value.strip()]
        if any(len(value) > 240 for value in cleaned):
            raise ValueError("each acceptance criterion must be at most 240 characters")
        return cleaned


class Objective(ApiModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: ObjectivePriority
    status: ObjectiveStatus
    run_id: str
    created_at: datetime


class EventDraft(ApiModel):
    run_id: str | None = None
    objective_id: str | None = None
    timestamp: datetime | None = None
    type: str = Field(min_length=3, max_length=80)
    actor: str = Field(min_length=2, max_length=80)
    summary: str = Field(min_length=3, max_length=500)
    data: dict[str, Any] = Field(default_factory=dict)


class StoredEvent(ApiModel):
    sequence: int = Field(ge=1)
    id: str
    run_id: str | None = None
    objective_id: str | None = None
    timestamp: datetime
    type: str
    actor: str
    summary: str
    data: dict[str, Any]
    previous_hash: str = Field(min_length=64, max_length=64)
    hash: str = Field(min_length=64, max_length=64)


class ChainState(ApiModel):
    valid: bool
    head_hash: str
    event_count: int = Field(ge=0)


class EventsPage(ApiModel):
    items: list[StoredEvent]
    count: int = Field(ge=0)
    chain: ChainState


class RunSummary(ApiModel):
    id: str
    objective_id: str
    objective_title: str
    status: RunStatus
    phase: str
    progress: int = Field(ge=0, le=100)
    current_version: str | None = None
    stable_version: str | None = None
    health: Literal["unknown", "healthy", "degraded", "recovering"]
    event_count: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime | None = None


class RunDetail(ApiModel):
    run: RunSummary
    events: list[StoredEvent]


class ReplayFrame(ApiModel):
    sequence: int
    timestamp: datetime
    phase: str
    status: RunStatus
    active_agent: str | None = None
    summary: str
    version: str | None = None
    health: Literal["unknown", "healthy", "degraded", "recovering"]
    ledger_delta: int = 0


class Replay(ApiModel):
    run: RunSummary
    events: list[StoredEvent]
    frames: list[ReplayFrame]
    chain: ChainState


class Agent(ApiModel):
    id: str
    name: str
    role: str
    status: Literal["idle", "working", "reviewing", "testing", "monitoring"]
    credits: int
    current_task: str | None = None
    completed_actions: int = Field(ge=0)
    last_seen: datetime | None = None
    memory: list[str] = Field(default_factory=list)


class AgentsResponse(ApiModel):
    items: list[Agent]
    count: int


class LedgerTransaction(ApiModel):
    event_id: str
    sequence: int
    timestamp: datetime
    kind: Literal["issue", "escrow", "payout", "penalty", "refund"]
    from_agent: str | None = None
    to_agent: str | None = None
    amount: int = Field(gt=0)
    reason: str
    run_id: str | None = None


class LedgerResponse(ApiModel):
    balances: dict[str, int]
    transactions: list[LedgerTransaction]
    total_issued: int = Field(ge=0)
    conserved: bool


class PolicyMechanism(ApiModel):
    id: str
    kind: Literal["memory", "prompt", "routing", "economy"]
    name: str
    description: str
    enforcement: str

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_kind(cls, value: Any) -> Any:
        """Keep proposals stored before mechanism kinds were introduced readable."""
        if not isinstance(value, dict) or value.get("kind") is not None:
            return value
        legacy_kinds = {
            "contract-gate": "prompt",
            "canary-window": "routing",
            "error-budget-gate": "economy",
            "rollback-quarantine": "memory",
        }
        mechanism_id = value.get("id")
        if mechanism_id in legacy_kinds:
            return {**value, "kind": legacy_kinds[mechanism_id]}
        return value


class PolicyProposal(ApiModel):
    id: str
    run_id: str
    title: str
    rationale: str
    mechanisms: list[PolicyMechanism] = Field(min_length=4, max_length=4)
    benchmark_id: str = "legacy-unbenchmarked"
    benchmark_metric: str = "pass_rate"
    benchmark_cases: int = Field(default=0, ge=0)
    baseline_score: float = Field(default=0.0, ge=0.0, le=1.0)
    candidate_score: float = Field(default=0.0, ge=0.0, le=1.0)
    critical_regressions: int = Field(default=1, ge=0)
    status: PolicyStatus
    created_at: datetime
    decided_at: datetime | None = None

    @field_validator("mechanisms")
    @classmethod
    def require_all_improvement_kinds(
        cls, mechanisms: list[PolicyMechanism]
    ) -> list[PolicyMechanism]:
        kinds = {mechanism.kind for mechanism in mechanisms}
        required = {"memory", "prompt", "routing", "economy"}
        if kinds != required:
            raise ValueError(
                "mechanisms must contain exactly one memory, prompt, routing, "
                "and economy change"
            )
        return mechanisms


class PoliciesResponse(ApiModel):
    items: list[PolicyProposal]
    active_mechanisms: list[PolicyMechanism]
    count: int


class RegressionInjection(ApiModel):
    reason: str = Field(
        default="A release changes /pulse to return HTTP 500.",
        min_length=3,
        max_length=240,
    )
    error_rate: float = Field(default=0.42, ge=0.01, le=1.0)


class RollbackRequest(ApiModel):
    reason: str = Field(
        default="Health policy breached; restore the last known-good release.",
        min_length=3,
        max_length=240,
    )


class RecoveryResponse(ApiModel):
    run: RunSummary
    proposal: PolicyProposal
    appended_events: list[StoredEvent]


class PolicyDecisionRequest(ApiModel):
    decision: Literal["approve", "reject"]
    decided_by: str = Field(default="human-customer", min_length=2, max_length=80)


class HealthResponse(ApiModel):
    status: Literal["ok"]
    service: str
    version: str
    event_chain_valid: bool
    events: int
    runtime: str


class PulseResponse(ApiModel):
    status: Literal["operational"]
    release: str
    monitored_by: str
    self_hosted_objective: str


class ApiError(ApiModel):
    detail: str
    request_id: str | None = None
