from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)

from app.models.domain import (
    Agent,
    AgentsResponse,
    EventsPage,
    HealthResponse,
    LedgerResponse,
    Objective,
    ObjectiveCreate,
    PoliciesResponse,
    PolicyDecisionRequest,
    PolicyProposal,
    PulseResponse,
    RecoveryResponse,
    RegressionInjection,
    Replay,
    RollbackRequest,
    RunDetail,
    RunSummary,
)
from app.services.orchestrator import SEED_OBJECTIVE_ID, Orchestrator


router = APIRouter(prefix="/api")


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


OrchestratorDep = Annotated[Orchestrator, Depends(get_orchestrator)]


def require_operator(request: Request) -> None:
    """Protect every mutation whenever the app is live-capable or deployed."""
    settings = request.app.state.settings
    live_capable = (
        settings.runtime == "codex"
        or settings.enable_codex_runtime
        or settings.codex_apply_changes
    )
    deployed = settings.environment.strip().lower() != "development"
    token = settings.operator_token
    if not live_capable and not deployed and token is None:
        return
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured",
        )
    provided = request.headers.get("X-Dhurandhar-Operator-Token", "")
    if not provided or not secrets.compare_digest(provided, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="valid operator credentials are required",
        )


OperatorDep = Annotated[None, Depends(require_operator)]


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request, orchestrator: OrchestratorDep) -> HealthResponse:
    chain = orchestrator.chain_state()
    return HealthResponse(
        status="ok",
        service=request.app.title,
        version=request.app.version,
        event_chain_valid=chain.valid,
        events=chain.event_count,
        runtime=orchestrator.runtime.name,
    )


def _pulse_is_degraded(orchestrator: Orchestrator) -> bool:
    """Reduce the latest demo-sandbox health transition from the event journal."""
    health_events = {
        "fault.injected",
        "monitor.alert",
        "monitor.healthy",
        "rollback.completed",
        "run.completed",
    }
    latest = next(
        (
            event
            for event in reversed(orchestrator.store.all())
            if event.type in health_events
        ),
        None,
    )
    return latest is not None and latest.type in {"fault.injected", "monitor.alert"}


@router.get("/pulse", response_model=PulseResponse, tags=["system"])
def pulse(
    request: Request,
    response: Response,
    orchestrator: OrchestratorDep,
) -> PulseResponse:
    """Event-backed demo-sandbox pulse; it is not an external deployment probe."""
    degraded = _pulse_is_degraded(orchestrator)
    if degraded:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return PulseResponse(
        status="degraded" if degraded else "operational",
        release=request.app.version,
        monitored_by="sentinel",
        self_hosted_objective=SEED_OBJECTIVE_ID,
        evidence_scope="demo-sandbox",
        external_observation=False,
    )


@router.post(
    "/objectives",
    response_model=Objective,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["objectives"],
)
def create_objective(
    payload: ObjectiveCreate,
    background_tasks: BackgroundTasks,
    orchestrator: OrchestratorDep,
    _operator: OperatorDep,
) -> Objective:
    objective = orchestrator.create_objective(payload)
    background_tasks.add_task(orchestrator.execute_objective, objective)
    return objective


@router.get("/objectives", response_model=list[Objective], tags=["objectives"])
def list_objectives(orchestrator: OrchestratorDep) -> list[Objective]:
    return orchestrator.objectives()


@router.get(
    "/objectives/{objective_id}", response_model=Objective, tags=["objectives"]
)
def get_objective(objective_id: str, orchestrator: OrchestratorDep) -> Objective:
    return orchestrator.objective(objective_id)


@router.get("/runs", response_model=list[RunSummary], tags=["runs"])
def list_runs(orchestrator: OrchestratorDep) -> list[RunSummary]:
    return orchestrator.runs()


@router.get("/runs/{run_id}", response_model=RunDetail, tags=["runs"])
def get_run(run_id: str, orchestrator: OrchestratorDep) -> RunDetail:
    return orchestrator.run_detail(run_id)


@router.get("/events", response_model=EventsPage, tags=["audit"])
def list_events(
    orchestrator: OrchestratorDep,
    run_id: str | None = None,
    objective_id: str | None = None,
    event_type: Annotated[str | None, Query(alias="type")] = None,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> EventsPage:
    events = orchestrator.store.query(
        run_id=run_id,
        objective_id=objective_id,
        event_type=event_type,
        after_sequence=after_sequence,
        limit=limit,
    )
    return EventsPage(
        items=events,
        count=len(events),
        chain=orchestrator.chain_state(),
    )


@router.get("/replay/{run_id}", response_model=Replay, tags=["audit"])
def replay(run_id: str, orchestrator: OrchestratorDep) -> Replay:
    return orchestrator.replay(run_id)


@router.get("/agents", response_model=AgentsResponse, tags=["company"])
def agents(orchestrator: OrchestratorDep) -> AgentsResponse:
    return orchestrator.agents()


@router.get("/ledger", response_model=LedgerResponse, tags=["company"])
def ledger(orchestrator: OrchestratorDep) -> LedgerResponse:
    return orchestrator.ledger()


@router.get("/policies", response_model=PoliciesResponse, tags=["company"])
def policies(orchestrator: OrchestratorDep) -> PoliciesResponse:
    return orchestrator.policies()


@router.post(
    "/runs/{run_id}/inject-regression",
    response_model=RunDetail,
    tags=["recovery"],
)
def inject_regression(
    run_id: str,
    payload: RegressionInjection,
    orchestrator: OrchestratorDep,
    _operator: OperatorDep,
) -> RunDetail:
    orchestrator.inject_regression(
        run_id,
        reason=payload.reason,
        error_rate=payload.error_rate,
    )
    return orchestrator.run_detail(run_id)


@router.post(
    "/runs/{run_id}/rollback",
    response_model=RecoveryResponse,
    tags=["recovery"],
)
def rollback(
    run_id: str,
    payload: RollbackRequest,
    orchestrator: OrchestratorDep,
    _operator: OperatorDep,
) -> RecoveryResponse:
    run, proposal, events = orchestrator.rollback(run_id, reason=payload.reason)
    return RecoveryResponse(
        run=run,
        proposal=proposal,
        appended_events=events,
    )


@router.post(
    "/policies/proposals/{proposal_id}/decision",
    response_model=PolicyProposal,
    tags=["company"],
)
def decide_policy(
    proposal_id: str,
    payload: PolicyDecisionRequest,
    orchestrator: OrchestratorDep,
    _operator: OperatorDep,
) -> PolicyProposal:
    return orchestrator.decide_policy(
        proposal_id,
        decision=payload.decision,
        decided_by=payload.decided_by,
    )
