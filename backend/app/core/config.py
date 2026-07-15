from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    """Runtime settings with intentionally conservative defaults."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    app_name: str = "Dhurandhar API"
    environment: str = "development"
    event_log_path: Path = BACKEND_ROOT / "data" / "events.jsonl"
    seed_demo: bool = True
    runtime: Literal["deterministic", "codex"] = "deterministic"
    enable_codex_runtime: bool = False
    codex_apply_changes: bool = False
    codex_bin: str = "codex"
    codex_workdir: Path = BACKEND_ROOT
    codex_timeout_seconds: int = Field(default=120, ge=10, le=300)
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    @field_validator("codex_workdir")
    @classmethod
    def validate_codex_workdir(cls, value: Path) -> Path:
        resolved = value.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise ValueError("codex_workdir must be an existing directory")
        return resolved

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.getenv("DHURANDHAR_CORS_ORIGINS")
        return cls(
            environment=os.getenv("DHURANDHAR_ENV", "development"),
            event_log_path=Path(
                os.getenv(
                    "DHURANDHAR_EVENT_LOG",
                    str(BACKEND_ROOT / "data" / "events.jsonl"),
                )
            ),
            seed_demo=_as_bool(os.getenv("DHURANDHAR_SEED_DEMO"), True),
            runtime=os.getenv("DHURANDHAR_RUNTIME", "deterministic"),
            enable_codex_runtime=_as_bool(
                os.getenv("DHURANDHAR_ENABLE_CODEX_RUNTIME"), False
            ),
            codex_apply_changes=_as_bool(
                os.getenv("DHURANDHAR_CODEX_APPLY_CHANGES"), False
            ),
            codex_bin=os.getenv("DHURANDHAR_CODEX_BIN", "codex"),
            codex_workdir=Path(
                os.getenv("DHURANDHAR_CODEX_WORKDIR", str(BACKEND_ROOT))
            ),
            codex_timeout_seconds=int(
                os.getenv("DHURANDHAR_CODEX_TIMEOUT_SECONDS", "120")
            ),
            cors_origins=tuple(
                origin.strip()
                for origin in origins.split(",")
                if origin.strip()
            )
            if origins
            else cls.model_fields["cors_origins"].default,
        )
