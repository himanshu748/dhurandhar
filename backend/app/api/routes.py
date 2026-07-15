from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status

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


@router.get("/pulse", response_model=PulseResponse, tags=["system"])
def pulse(request: Request) -> PulseResponse:
    """The tiny artifact created by the deterministic self-hosting run."""
    return PulseResponse(
        status="operational",
        release=request.app.version,
        monitored_by="sentinel",
        self_hosted_objective=SEED_OBJECTIVE_ID,
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
) -> PolicyProposal:
    return orchestrator.decide_policy(
        proposal_id,
        decision=payload.decision,
        decided_by=payload.decided_by,
    )
