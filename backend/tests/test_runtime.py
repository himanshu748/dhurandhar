from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from app.core.config import Settings
from app.services import runtime as runtime_module
from app.services.runtime import (
    CodexCliRuntime,
    CodexRuntimeDisabled,
    DeterministicRuntime,
    build_runtime,
)


def test_deterministic_runtime_repeats_exactly() -> None:
    runtime = DeterministicRuntime()
    first = runtime.generate(brief="Add health endpoint", run_id="run_1")
    second = runtime.generate(brief="Add health endpoint", run_id="run_1")
    assert first == second
    assert first.runtime == "deterministic"
    assert len(first.tests) == 3


def test_codex_runtime_is_off_by_default(tmp_path: Path) -> None:
    runtime = CodexCliRuntime(
        enabled=False,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
    )
    with pytest.raises(CodexRuntimeDisabled, match="ENABLE_CODEX_RUNTIME"):
        runtime.generate(brief="No process should start", run_id="run_disabled")


def test_factory_requires_double_opt_in(tmp_path: Path) -> None:
    settings = Settings(
        event_log_path=tmp_path / "events.jsonl",
        runtime="codex",
        enable_codex_runtime=False,
        codex_workdir=tmp_path,
    )
    with pytest.raises(CodexRuntimeDisabled, match="also requires"):
        build_runtime(settings)


def test_codex_runtime_stays_read_only_without_third_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured["command"] = command
        captured["input"] = kwargs["input"]
        return CompletedProcess(command, 0, stdout="A bounded plan", stderr="")

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
    )

    result = runtime.generate(brief="Add a health signal", run_id="run_read_only")

    assert captured["command"] == [
        "/usr/bin/codex",
        "exec",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-",
    ]
    assert "Inspect the repository read-only" in str(captured["input"])
    assert result.write_mode is False


def test_codex_workspace_write_requires_third_opt_in_and_git_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )
    with pytest.raises(CodexRuntimeDisabled, match="Git worktree"):
        runtime.generate(brief="Implement this", run_id="run_write")

    (tmp_path / ".git").mkdir()
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured["command"] = command
        captured["input"] = kwargs["input"]
        return CompletedProcess(command, 0, stdout="Changed backend/app.py", stderr="")

    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    result = runtime.generate(brief="Implement this", run_id="run_write")

    assert captured["command"] == [
        "/usr/bin/codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "-",
    ]
    assert "Do not commit, push, merge, deploy" in str(captured["input"])
    assert result.write_mode is True


def test_factory_propagates_workspace_write_flag(tmp_path: Path) -> None:
    settings = Settings(
        event_log_path=tmp_path / "events.jsonl",
        runtime="codex",
        enable_codex_runtime=True,
        codex_apply_changes=True,
        codex_workdir=tmp_path,
    )

    runtime = build_runtime(settings)

    assert isinstance(runtime, CodexCliRuntime)
    assert runtime.apply_changes is True


def test_settings_load_workspace_write_flag_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DHURANDHAR_RUNTIME", "codex")
    monkeypatch.setenv("DHURANDHAR_ENABLE_CODEX_RUNTIME", "true")
    monkeypatch.setenv("DHURANDHAR_CODEX_APPLY_CHANGES", "true")
    monkeypatch.setenv("DHURANDHAR_CODEX_WORKDIR", str(tmp_path))

    settings = Settings.from_env()

    assert settings.runtime == "codex"
    assert settings.enable_codex_runtime is True
    assert settings.codex_apply_changes is True
