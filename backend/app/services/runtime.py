from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings


class RuntimeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime: str
    summary: str
    change_id: str
    tests: list[str] = Field(default_factory=list)
    raw_output: str | None = None
    write_mode: bool = False


class RuntimeAdapter(Protocol):
    name: str

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult: ...


class DeterministicRuntime:
    """Offline runtime used by default for reliable demos and tests."""

    name = "deterministic"

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult:
        digest = hashlib.sha256(f"{run_id}:{brief}".encode("utf-8")).hexdigest()
        return RuntimeResult(
            runtime=self.name,
            summary="Implemented a minimal, typed change with health instrumentation.",
            change_id=f"change_{digest[:12]}",
            tests=[
                "contract::pulse_returns_200",
                "unit::release_metadata_is_stable",
                "monitor::error_budget_below_threshold",
            ],
        )


class CodexRuntimeDisabled(RuntimeError):
    pass


class CodexCliRuntime:
    """Opt-in Codex CLI adapter that remains read-only unless triple enabled.

    It never invokes a shell, never enables dangerous approval bypasses, caps the
    prompt and timeout, and defaults to a read-only sandbox. Workspace writes require
    an explicit third flag and a Git worktree; commit, push, merge, and deploy remain
    outside this adapter.
    """

    name = "codex"
    _MAX_PROMPT_CHARS = 12_000

    def __init__(
        self,
        *,
        enabled: bool,
        executable: str,
        workdir: Path,
        timeout_seconds: int,
        apply_changes: bool = False,
    ) -> None:
        self.enabled = enabled
        self.executable = executable
        self.workdir = workdir.resolve()
        self.timeout_seconds = timeout_seconds
        self.apply_changes = apply_changes

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult:
        if not self.enabled:
            raise CodexRuntimeDisabled(
                "Codex runtime requires DHURANDHAR_ENABLE_CODEX_RUNTIME=true"
            )
        executable = shutil.which(self.executable)
        if executable is None:
            raise FileNotFoundError(f"Codex executable not found: {self.executable}")
        if self.apply_changes and not (self.workdir / ".git").exists():
            raise CodexRuntimeDisabled(
                "workspace-write mode requires DHURANDHAR_CODEX_WORKDIR to be a Git "
                "worktree"
            )
        if self.apply_changes:
            instructions = (
                "Implement the bounded objective directly in this Git worktree and run "
                "the smallest relevant checks. Stay inside the worktree. Do not commit, "
                "push, merge, deploy, access the network, or reveal secrets. Return a "
                "concise summary of changed files and test results."
            )
        else:
            instructions = (
                "Inspect the repository read-only and return a concise implementation "
                "plan, the files that would change, and tests. Do not reveal secrets."
            )
        prompt = (
            "You are an implementation agent in a supervised software delivery run. "
            f"{instructions}\n\nRun: {run_id}\nObjective: {brief}"
        )[: self._MAX_PROMPT_CHARS]
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USER", "TMPDIR", "OPENAI_API_KEY"}
        }
        environment["NO_COLOR"] = "1"
        command = [
            executable,
            "exec",
            "--sandbox",
            "workspace-write" if self.apply_changes else "read-only",
        ]
        if not self.apply_changes:
            command.append("--skip-git-repo-check")
        command.append("-")
        completed = subprocess.run(
            command,
            input=prompt,
            cwd=self.workdir,
            env=environment,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        output = completed.stdout.strip()
        if completed.returncode != 0:
            diagnostic = completed.stderr.strip()[-500:]
            raise RuntimeError(
                f"Codex exited with status {completed.returncode}: {diagnostic}"
            )
        digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
        return RuntimeResult(
            runtime=self.name,
            summary=(
                "Codex implemented the bounded change in the configured worktree."
                if self.apply_changes
                else "Codex produced a read-only implementation proposal."
            ),
            change_id=f"codex_{digest[:12]}",
            tests=[],
            raw_output=output[-4_000:] if output else None,
            write_mode=self.apply_changes,
        )


def build_runtime(settings: Settings) -> RuntimeAdapter:
    if settings.runtime == "codex":
        if not settings.enable_codex_runtime:
            raise CodexRuntimeDisabled(
                "DHURANDHAR_RUNTIME=codex also requires "
                "DHURANDHAR_ENABLE_CODEX_RUNTIME=true"
            )
        return CodexCliRuntime(
            enabled=True,
            executable=settings.codex_bin,
            workdir=settings.codex_workdir,
            timeout_seconds=settings.codex_timeout_seconds,
            apply_changes=settings.codex_apply_changes,
        )
    return DeterministicRuntime()
