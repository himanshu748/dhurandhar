from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import router
from app.core.config import Settings
from app.models.domain import HealthResponse
from app.services.event_store import JsonlEventStore
from app.services.orchestrator import DomainConflict, DomainNotFound, Orchestrator
from app.services.runtime import build_runtime


logger = logging.getLogger("dhurandhar.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        store = JsonlEventStore(configured.event_log_path)
        runtime = build_runtime(configured)
        orchestrator = Orchestrator(store=store, runtime=runtime)
        application.state.settings = configured
        application.state.event_store = store
        application.state.orchestrator = orchestrator
        if configured.seed_demo:
            orchestrator.bootstrap_seeded_run()
        orchestrator.bootstrap_company()
        orchestrator.reconcile_interrupted_runs()
        yield

    application = FastAPI(
        title=configured.app_name,
        version=__version__,
        description=(
            "Event-sourced API for an eight-agent autonomous software company. "
            "Every material action and model claim is stored in a verifiable hash chain."
        ),
        lifespan=lifespan,
        openapi_tags=[
            {"name": "system", "description": "Health and self-hosted artifact"},
            {"name": "objectives", "description": "Customer intent"},
            {"name": "runs", "description": "Autonomous delivery runs"},
            {"name": "audit", "description": "Events and deterministic replay"},
            {"name": "company", "description": "Agents, credits, and policies"},
            {"name": "recovery", "description": "Failure injection and recovery"},
        ],
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(configured.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "X-Request-ID",
            "X-Dhurandhar-Operator-Token",
        ],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1_000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return response

    @application.exception_handler(DomainNotFound)
    async def not_found(request: Request, exc: DomainNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    @application.exception_handler(DomainConflict)
    async def conflict(request: Request, exc: DomainConflict) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    @application.get("/health", response_model=HealthResponse, include_in_schema=False)
    def root_health(request: Request) -> HealthResponse:
        orchestrator: Orchestrator = request.app.state.orchestrator
        chain = orchestrator.chain_state()
        return HealthResponse(
            status="ok",
            service=application.title,
            version=application.version,
            event_chain_valid=chain.valid,
            events=chain.event_count,
            runtime=orchestrator.runtime.name,
        )

    application.include_router(router)
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.joinpath("index.html").is_file():
        application.mount(
            "/",
            StaticFiles(directory=frontend_dist, html=True),
            name="frontend",
        )
    return application


app = create_app()
