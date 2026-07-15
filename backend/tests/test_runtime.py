from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from app.core.config import Settings
from app.services import runtime as runtime_module
from app.services.runtime import (
    CodexCliRuntime,
    CodexRuntimeDisabled,
    DeterministicRuntime,
    GitDiffMetadata,
    build_runtime,
)


def _jsonl(*events: dict[str, object]) -> str:
    return "\n".join(json.dumps(event) for event in events)


def _successful_stream(
    final_message: str = "Implemented safely",
    *,
    thread_id: str = "thread_live_123",
) -> str:
    return _jsonl(
        {"type": "thread.started", "thread_id": thread_id},
        {"type": "turn.started"},
        {
            "type": "item.started",
            "item": {
                "id": "cmd_1",
                "type": "command_execution",
                "command": "pytest -q",
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd_1",
                "type": "command_execution",
                "command": "pytest -q",
                "status": "completed",
                "exit_code": 0,
                "aggregated_output": "secret output is intentionally not retained",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "change_1",
                "type": "file_change",
                "status": "completed",
                "changes": [
                    {"path": "backend/app/example.py", "kind": "update"},
                    {"path": "backend/tests/test_example.py", "kind": "add"},
                ],
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "message_1",
                "type": "agent_message",
                "text": final_message,
            },
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1200,
                "cached_input_tokens": 900,
                "output_tokens": 240,
                "reasoning_output_tokens": 80,
            },
        },
    )


def test_deterministic_runtime_repeats_and_reviews_exactly() -> None:
    runtime = DeterministicRuntime()
    first = runtime.generate(brief="Add health endpoint", run_id="run_1")
    second = runtime.generate(brief="Add health endpoint", run_id="run_1")
    review = runtime.review(
        brief="Review health endpoint", run_id="run_1", diff_context="fixture diff"
    )

    assert first == second
    assert first.runtime == "deterministic"
    assert first.provenance == "fixture"
    assert len(first.tests) == 3
    assert review.verdict == "approved"
    assert review.provenance == "fixture"


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


def test_read_only_codex_run_parses_structured_jsonl_and_reduces_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured["command"] = command
        captured["input"] = kwargs["input"]
        captured["env"] = kwargs["env"]
        return CompletedProcess(command, 0, stdout=_successful_stream(), stderr="")

    monkeypatch.setenv("DHURANDHAR_SHOULD_NOT_LEAK", "sensitive")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("GITHUB_TOKEN", "github-secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret")
    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        implementation_model="gpt-5.5",
    )

    result = runtime.generate(brief="Add a health signal", run_id="run_read_only")

    assert captured["command"] == [
        "/usr/bin/codex",
        "exec",
        "--ignore-user-config",
        "--config",
        'model_reasoning_effort="medium"',
        "--json",
        "--model",
        "gpt-5.5",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-",
    ]
    assert "Inspect the repository read-only" in str(captured["input"])
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert "DHURANDHAR_SHOULD_NOT_LEAK" not in environment
    assert "OPENAI_API_KEY" not in environment
    assert "GITHUB_TOKEN" not in environment
    assert "AWS_SECRET_ACCESS_KEY" not in environment
    assert "ANTHROPIC_API_KEY" not in environment
    assert result.write_mode is False
    assert result.provenance == "live"
    assert result.thread_id == "thread_live_123"
    assert result.model == "gpt-5.5"
    assert result.input_tokens == 1200
    assert result.cached_input_tokens == 900
    assert result.output_tokens == 240
    assert result.reasoning_output_tokens == 80
    assert result.raw_event_count == 7
    assert result.final_message == "Implemented safely"
    assert result.raw_output is None
    assert result.commands[0].command == "pytest -q"
    assert result.commands[0].status == "completed"
    assert result.commands[0].exit_code == 0
    assert [item.path for item in result.file_changes] == [
        "backend/app/example.py",
        "backend/tests/test_example.py",
    ]


def test_codex_workspace_write_requires_git_worktree(
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


def test_workspace_write_uses_model_json_and_attaches_diff_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(tmp_path, "init", "-q")
    _git(
        tmp_path,
        "-c",
        "user.name=Dhurandhar Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "--allow-empty",
        "-qm",
        "seed",
    )
    captured: dict[str, object] = {}
    real_run = subprocess.run

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        if command[0] == "git":
            return real_run(command, **kwargs)  # type: ignore[return-value]
        captured["command"] = command
        return CompletedProcess(command, 0, stdout=_successful_stream(), stderr="")

    evidence = GitDiffMetadata(
        name_only=["new.py"],
        numstat=[],
        sha256="a" * 64,
        preview="+++ b/new.py\n+print('ok')",
    )
    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        CodexCliRuntime, "_capture_git_diff", lambda _, **__: evidence
    )
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
        implementation_model="gpt-5.5",
    )

    result = runtime.generate(brief="Implement this", run_id="run_write")

    assert captured["command"] == [
        "/usr/bin/codex",
        "exec",
        "--ignore-user-config",
        "--config",
        'model_reasoning_effort="medium"',
        "--json",
        "--model",
        "gpt-5.5",
        "--sandbox",
        "workspace-write",
        "-",
    ]
    assert result.write_mode is True
    assert result.diff == evidence
    assert any(item.path == "new.py" and item.kind == "git_diff" for item in result.file_changes)


def test_reviewer_is_read_only_uses_reviewer_model_and_parses_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}
    message = json.dumps(
        {
            "verdict": "changes_requested",
            "findings": [
                {
                    "severity": "high",
                    "summary": "Missing authorization check",
                    "file": "backend/app/api.py",
                    "line": 42,
                }
            ],
        }
    )

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured["command"] = command
        captured["input"] = kwargs["input"]
        return CompletedProcess(
            command, 0, stdout=_successful_stream(message), stderr=""
        )

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        reviewer_model="gpt-5.5-review",
        apply_changes=True,
    )

    result = runtime.review(
        brief="Review the candidate", run_id="run_review", diff_context="diff --git"
    )

    assert captured["command"] == [
        "/usr/bin/codex",
        "exec",
        "--ignore-user-config",
        "--config",
        'model_reasoning_effort="medium"',
        "--json",
        "--model",
        "gpt-5.5-review",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-",
    ]
    assert "Diff context:\ndiff --git" in str(captured["input"])
    assert result.write_mode is False
    assert result.verdict == "changes_requested"
    assert result.findings[0].severity == "high"
    assert result.findings[0].line == 42


def test_jsonl_parser_rejects_malformed_missing_or_failed_streams() -> None:
    with pytest.raises(RuntimeError, match="invalid JSONL at line 2"):
        CodexCliRuntime._parse_jsonl('{"type":"thread.started"}\nnot-json')
    with pytest.raises(RuntimeError, match="thread.started"):
        CodexCliRuntime._parse_jsonl(_jsonl({"type": "turn.completed", "usage": {}}))
    with pytest.raises(RuntimeError, match="turn.completed"):
        CodexCliRuntime._parse_jsonl(
            _jsonl({"type": "thread.started", "thread_id": "thread_1"})
        )
    with pytest.raises(RuntimeError, match="quota exhausted"):
        CodexCliRuntime._parse_jsonl(
            _jsonl(
                {"type": "thread.started", "thread_id": "thread_1"},
                {"type": "turn.failed", "error": {"message": "quota exhausted"}},
            )
        )


def test_nonzero_codex_exit_is_contained_without_stdout_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str], **_: object) -> CompletedProcess[str]:
        return CompletedProcess(
            command,
            7,
            stdout="not-json possibly sensitive",
            stderr="authentication failed",
        )

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
    )

    with pytest.raises(RuntimeError, match="status 7: authentication failed") as exc:
        runtime.generate(brief="Inspect", run_id="run_fail")
    assert "possibly sensitive" not in str(exc.value)


def test_codex_timeout_propagates_as_runtime_boundary_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str], **_: object) -> CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, 30)

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
    )

    with pytest.raises(subprocess.TimeoutExpired):
        runtime.generate(brief="Inspect", run_id="run_timeout")


def _git(workdir: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments], cwd=workdir, check=True, capture_output=True, text=True
    )


def _seed_clean_worktree(workdir: Path) -> Path:
    _git(workdir, "init", "-q")
    tracked = workdir / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    _git(workdir, "add", "tracked.txt")
    _git(
        workdir,
        "-c",
        "user.name=Dhurandhar Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "-qm",
        "seed",
    )
    return tracked


@pytest.mark.parametrize("dirty_kind", ["tracked", "staged", "untracked"])
def test_workspace_write_refuses_every_git_visible_dirty_prestate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dirty_kind: str,
) -> None:
    tracked = _seed_clean_worktree(tmp_path)
    if dirty_kind == "tracked":
        tracked.write_text("dirty\n", encoding="utf-8")
    elif dirty_kind == "staged":
        tracked.write_text("staged\n", encoding="utf-8")
        _git(tmp_path, "add", "tracked.txt")
    else:
        (tmp_path / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    with pytest.raises(CodexRuntimeDisabled, match="clean Git worktree"):
        runtime.generate(brief="Must not start", run_id=f"run_dirty_{dirty_kind}")


def test_workspace_write_records_clean_baseline_and_refuses_reattribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracked = _seed_clean_worktree(tmp_path)
    real_run = subprocess.run
    baseline_head = real_run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    codex_calls = 0

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        nonlocal codex_calls
        if command[0] == "git":
            return real_run(command, **kwargs)  # type: ignore[return-value]
        codex_calls += 1
        tracked.write_text("changed by this invocation\n", encoding="utf-8")
        (tmp_path / "created.py").write_text("print('created')\n", encoding="utf-8")
        return CompletedProcess(command, 0, stdout=_successful_stream(), stderr="")

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    result = runtime.generate(brief="Make one change", run_id="run_baseline")

    assert result.diff is not None
    assert result.diff.baseline_head == baseline_head
    assert result.diff.head_after == baseline_head
    assert result.diff.baseline_clean is True
    assert result.diff.baseline_status_sha256 == hashlib.sha256(b"").hexdigest()
    assert result.diff.name_only == ["tracked.txt", "created.py"]
    assert codex_calls == 1

    with pytest.raises(CodexRuntimeDisabled, match="clean Git worktree"):
        runtime.generate(brief="Do not reattribute", run_id="run_second")
    assert codex_calls == 1


def test_failed_workspace_write_restores_only_git_visible_invocation_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracked = _seed_clean_worktree(tmp_path)
    real_run = subprocess.run

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        if command[0] == "git":
            return real_run(command, **kwargs)  # type: ignore[return-value]
        tracked.write_text("failed tracked change\n", encoding="utf-8")
        staged = tmp_path / "staged.py"
        staged.write_text("print('staged')\n", encoding="utf-8")
        (tmp_path / "untracked.py").write_text("print('untracked')\n", encoding="utf-8")
        real_run(
            ["git", "add", "tracked.txt", "staged.py"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return CompletedProcess(command, 7, stdout="", stderr="model process failed")

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    with pytest.raises(RuntimeError, match="status 7: model process failed"):
        runtime.generate(brief="Fail after editing", run_id="run_cleanup")

    assert tracked.read_text(encoding="utf-8") == "baseline\n"
    assert not (tmp_path / "staged.py").exists()
    assert not (tmp_path / "untracked.py").exists()
    status = real_run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout == ""


def test_workspace_write_that_mutates_head_fails_closed_for_manual_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_clean_worktree(tmp_path)
    real_run = subprocess.run
    baseline_head = real_run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    def fake_run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        if command[0] == "git":
            return real_run(command, **kwargs)  # type: ignore[return-value]
        (tmp_path / "committed.py").write_text("print('unsafe')\n", encoding="utf-8")
        real_run(
            ["git", "add", "committed.py"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        real_run(
            [
                "git",
                "-c",
                "user.name=Dhurandhar Tests",
                "-c",
                "user.email=tests@example.invalid",
                "commit",
                "-qm",
                "forbidden commit",
            ],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return CompletedProcess(command, 0, stdout=_successful_stream(), stderr="")

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    with pytest.raises(RuntimeError, match="Manual recovery is required"):
        runtime.generate(brief="Must not commit", run_id="run_head_mutation")

    current_head = real_run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert current_head != baseline_head


def test_reviewer_must_use_a_distinct_codex_thread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str], **_: object) -> CompletedProcess[str]:
        return CompletedProcess(
            command,
            0,
            stdout=_successful_stream(
                '{"verdict":"approved","findings":[]}',
                thread_id="thread_reused",
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime_module.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
    )
    implementation = runtime.generate(brief="Inspect", run_id="run_same_thread")
    assert implementation.thread_id == "thread_reused"

    with pytest.raises(RuntimeError, match="reused the implementation thread id"):
        runtime.review(
            brief="Review",
            run_id="run_same_thread",
            diff_context="bounded diff",
        )


def test_git_diff_capture_includes_tracked_and_untracked_files(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("old\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(
        tmp_path,
        "-c",
        "user.name=Dhurandhar Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "-qm",
        "seed",
    )
    tracked.write_text("new\nsecond\n", encoding="utf-8")
    (tmp_path / "new.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    evidence = runtime._capture_git_diff()

    assert evidence.name_only == ["tracked.txt", "new.txt"]
    assert len(evidence.sha256) == 64
    stats = {item.path: item for item in evidence.numstat}
    assert stats["tracked.txt"].additions == 2
    assert stats["tracked.txt"].deletions == 1
    assert stats["new.txt"].additions == 2
    assert stats["new.txt"].deletions == 0
    assert "diff --git a/tracked.txt b/tracked.txt" in evidence.preview
    assert "+++ b/new.txt" in evidence.preview


def test_git_diff_preview_is_bounded(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(
        tmp_path,
        "-c",
        "user.name=Dhurandhar Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "--allow-empty",
        "-qm",
        "seed",
    )
    (tmp_path / "large.txt").write_text("x" * 20_000, encoding="utf-8")
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    evidence = runtime._capture_git_diff()

    assert len(evidence.preview.encode("utf-8")) <= runtime._MAX_DIFF_PREVIEW_BYTES
    assert evidence.preview_truncated is True


def test_git_diff_capture_failure_is_explicit(tmp_path: Path) -> None:
    runtime = CodexCliRuntime(
        enabled=True,
        executable="codex",
        workdir=tmp_path,
        timeout_seconds=30,
        apply_changes=True,
    )

    with pytest.raises(RuntimeError, match="Git diff evidence capture failed"):
        runtime._capture_git_diff()


def test_factory_and_environment_propagate_models_and_write_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DHURANDHAR_RUNTIME", "codex")
    monkeypatch.setenv("DHURANDHAR_ENABLE_CODEX_RUNTIME", "true")
    monkeypatch.setenv("DHURANDHAR_CODEX_APPLY_CHANGES", "true")
    monkeypatch.setenv("DHURANDHAR_CODEX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("DHURANDHAR_IMPLEMENTATION_MODEL", "gpt-5.5-impl")
    monkeypatch.setenv("DHURANDHAR_REVIEWER_MODEL", "gpt-5.5-review")

    settings = Settings.from_env()
    runtime = build_runtime(settings)

    assert settings.runtime == "codex"
    assert settings.enable_codex_runtime is True
    assert settings.codex_apply_changes is True
    assert settings.implementation_model == "gpt-5.5-impl"
    assert settings.reviewer_model == "gpt-5.5-review"
    assert isinstance(runtime, CodexCliRuntime)
    assert runtime.apply_changes is True
    assert runtime.implementation_model == "gpt-5.5-impl"
    assert runtime.reviewer_model == "gpt-5.5-review"


def test_blank_operator_token_from_compose_normalizes_to_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DHURANDHAR_OPERATOR_TOKEN", "")

    settings = Settings.from_env()

    assert settings.operator_token is None
