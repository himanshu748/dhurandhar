from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings


DEFAULT_CODEX_MODEL = "gpt-5.5"


class RuntimeCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    command: str
    status: str
    exit_code: int | None = None


class RuntimeFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    kind: str
    status: str


class DiffNumstat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    additions: int | None
    deletions: int | None
    binary: bool = False


class GitDiffMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name_only: list[str] = Field(default_factory=list)
    numstat: list[DiffNumstat] = Field(default_factory=list)
    sha256: str
    preview: str = ""
    preview_truncated: bool = False
    baseline_head: str | None = None
    head_after: str | None = None
    baseline_clean: bool | None = None
    baseline_status_sha256: str | None = None


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"
    summary: str
    file: str | None = None
    line: int | None = None


class RuntimeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime: str
    provenance: Literal["fixture", "live"] = "fixture"
    summary: str
    change_id: str
    tests: list[str] = Field(default_factory=list)
    raw_output: str | None = None
    write_mode: bool = False
    thread_id: str | None = None
    model: str | None = None
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    commands: list[RuntimeCommand] = Field(default_factory=list)
    file_changes: list[RuntimeFileChange] = Field(default_factory=list)
    final_message: str | None = None
    raw_event_count: int = 0
    diff: GitDiffMetadata | None = None
    verdict: Literal["approved", "changes_requested", "unknown"] | None = None
    findings: list[ReviewFinding] = Field(default_factory=list)


class RuntimeAdapter(Protocol):
    name: str

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult: ...

    def review(self, *, brief: str, run_id: str, diff_context: str) -> RuntimeResult: ...


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

    def review(self, *, brief: str, run_id: str, diff_context: str) -> RuntimeResult:
        digest = hashlib.sha256(
            f"review:{run_id}:{brief}:{diff_context}".encode("utf-8")
        ).hexdigest()
        return RuntimeResult(
            runtime=self.name,
            summary="Deterministic reviewer approved the fixture change.",
            change_id=f"review_{digest[:12]}",
            final_message=(
                '{"verdict":"approved","findings":[]}'
            ),
            verdict="approved",
        )


class CodexRuntimeDisabled(RuntimeError):
    pass


class _ParsedCodexStream(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    commands: list[RuntimeCommand] = Field(default_factory=list)
    file_changes: list[RuntimeFileChange] = Field(default_factory=list)
    final_message: str | None = None
    raw_event_count: int


@dataclass(frozen=True)
class _GitBaseline:
    head: str
    status: bytes
    status_sha256: str


class CodexCliRuntime:
    """Structured, opt-in Codex CLI adapter with bounded workspace writes.

    The process is invoked without a shell, receives a reduced environment, emits
    JSONL, and stays read-only unless the independent write flag is enabled. A
    successful write run is followed by evidence-only Git commands; this adapter
    never commits, pushes, merges, deploys, or grants a sandbox bypass.

    Workspace-write invocations start only from a Git-clean baseline. If the Codex
    process itself fails, Git-visible tracked and untracked paths created by that
    invocation are restored while HEAD is unchanged. A HEAD mutation or incomplete
    cleanup fails loudly and requires manual recovery; a later invocation will never
    fold a dirty pre-existing worktree into its evidence.
    """

    name = "codex"
    _MAX_PROMPT_CHARS = 12_000
    _MAX_COMMAND_CHARS = 2_000
    _MAX_PATH_CHARS = 1_000
    _MAX_DIFF_PREVIEW_BYTES = 8_000
    _GIT_TIMEOUT_SECONDS = 30

    def __init__(
        self,
        *,
        enabled: bool,
        executable: str,
        workdir: Path,
        timeout_seconds: int,
        apply_changes: bool = False,
        implementation_model: str = DEFAULT_CODEX_MODEL,
        reviewer_model: str = DEFAULT_CODEX_MODEL,
    ) -> None:
        self.enabled = enabled
        self.executable = executable
        self.workdir = workdir.resolve()
        self.timeout_seconds = timeout_seconds
        self.apply_changes = apply_changes
        self.implementation_model = implementation_model
        self.reviewer_model = reviewer_model
        self._implementation_threads: dict[str, str] = {}

    def generate(self, *, brief: str, run_id: str) -> RuntimeResult:
        self._validate_enabled()
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
        result = self._invoke(
            prompt=prompt,
            model=self.implementation_model,
            write_mode=self.apply_changes,
            change_prefix="codex",
        )
        if result.thread_id is None:  # live JSONL parsing requires this already
            raise RuntimeError("Codex implementation provenance has no thread id")
        self._implementation_threads[run_id] = result.thread_id
        return result.model_copy(
            update={
                "summary": (
                    "Codex implemented the bounded change in the configured worktree."
                    if self.apply_changes
                    else "Codex produced a read-only implementation proposal."
                )
            }
        )

    def review(self, *, brief: str, run_id: str, diff_context: str) -> RuntimeResult:
        """Run an independent read-only Codex review with structured final output."""

        self._validate_enabled()
        prompt = (
            "You are the independent reviewer in a supervised software delivery run. "
            "Inspect the repository and the bounded diff context read-only. Never edit "
            "files, reveal secrets, approve your own implementation, or weaken tests. "
            "Your final message must be only one JSON object with this exact shape: "
            '{"verdict":"approved|changes_requested","findings":['
            '{"severity":"info|low|medium|high|critical","summary":"...",'
            '"file":null,"line":null}]}.\n\n'
            f"Run: {run_id}\nReview brief: {brief}\nDiff context:\n{diff_context}"
        )[: self._MAX_PROMPT_CHARS]
        result = self._invoke(
            prompt=prompt,
            model=self.reviewer_model,
            write_mode=False,
            change_prefix="review",
        )
        implementation_thread = self._implementation_threads.get(run_id)
        if (
            implementation_thread is not None
            and result.thread_id == implementation_thread
        ):
            raise RuntimeError(
                "independent Codex review reused the implementation thread id"
            )
        self._implementation_threads.pop(run_id, None)
        verdict, findings = self._parse_review(result.final_message)
        return result.model_copy(
            update={
                "summary": (
                    "Codex reviewer approved the bounded change."
                    if verdict == "approved"
                    else "Codex reviewer requested changes."
                    if verdict == "changes_requested"
                    else "Codex reviewer returned an unstructured verdict."
                ),
                "verdict": verdict,
                "findings": findings,
            }
        )

    def _validate_enabled(self) -> None:
        if not self.enabled:
            raise CodexRuntimeDisabled(
                "Codex runtime requires DHURANDHAR_ENABLE_CODEX_RUNTIME=true"
            )
        if shutil.which(self.executable) is None:
            raise FileNotFoundError(f"Codex executable not found: {self.executable}")

    def _invoke(
        self,
        *,
        prompt: str,
        model: str,
        write_mode: bool,
        change_prefix: str,
    ) -> RuntimeResult:
        executable = shutil.which(self.executable)
        if executable is None:  # protected by _validate_enabled; keeps this method total
            raise FileNotFoundError(f"Codex executable not found: {self.executable}")
        command = [
            executable,
            "exec",
            "--ignore-user-config",
            "--config",
            'model_reasoning_effort="medium"',
            "--json",
            "--model",
            model,
            "--sandbox",
            "workspace-write" if write_mode else "read-only",
        ]
        if not write_mode:
            command.append("--skip-git-repo-check")
        command.append("-")
        baseline = self._capture_clean_baseline() if write_mode else None
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                cwd=self.workdir,
                env=self._codex_environment(),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            parsed: _ParsedCodexStream | None = None
            parse_error: RuntimeError | None = None
            try:
                parsed = self._parse_jsonl(completed.stdout)
            except RuntimeError as exc:
                parse_error = exc
            if completed.returncode != 0:
                diagnostic = completed.stderr.strip()[-500:]
                if not diagnostic and parse_error is not None:
                    diagnostic = str(parse_error)
                raise RuntimeError(
                    f"Codex exited with status {completed.returncode}: {diagnostic}"
                )
            if parse_error is not None:
                raise parse_error
            assert parsed is not None

            diff = (
                self._capture_git_diff(baseline=baseline)
                if baseline is not None
                else None
            )
            file_changes = list(parsed.file_changes)
            if diff is not None:
                known_paths = {item.path for item in file_changes}
                file_changes.extend(
                    RuntimeFileChange(
                        path=path, kind="git_diff", status="completed"
                    )
                    for path in diff.name_only
                    if path not in known_paths
                )
            digest = hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest()
            return RuntimeResult(
                runtime=self.name,
                provenance="live",
                summary="Codex completed the bounded task.",
                change_id=f"{change_prefix}_{digest[:12]}",
                tests=[],
                raw_output=None,
                write_mode=write_mode,
                thread_id=parsed.thread_id,
                model=model,
                input_tokens=parsed.input_tokens,
                cached_input_tokens=parsed.cached_input_tokens,
                output_tokens=parsed.output_tokens,
                reasoning_output_tokens=parsed.reasoning_output_tokens,
                commands=parsed.commands,
                file_changes=file_changes,
                final_message=parsed.final_message,
                raw_event_count=parsed.raw_event_count,
                diff=diff,
            )
        except Exception as exc:
            if baseline is not None:
                cleanup_error = self._restore_failed_write(baseline)
                if cleanup_error is not None:
                    raise RuntimeError(
                        "Codex write invocation failed and automatic Git cleanup "
                        f"was incomplete: {cleanup_error}. Manual recovery is required "
                        "before another write run."
                    ) from exc
            raise

    @staticmethod
    def _codex_environment() -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USER", "TMPDIR"}
        }
        environment["NO_COLOR"] = "1"
        return environment

    @classmethod
    def _parse_jsonl(cls, output: str) -> _ParsedCodexStream:
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(output.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Codex returned invalid JSONL at line {line_number}"
                ) from exc
            if not isinstance(event, dict):
                raise RuntimeError(
                    f"Codex returned a non-object JSONL event at line {line_number}"
                )
            events.append(event)
        if not events:
            raise RuntimeError("Codex returned no JSONL events")

        thread_id: str | None = None
        input_tokens = 0
        cached_input_tokens = 0
        output_tokens = 0
        reasoning_output_tokens = 0
        turn_completed = False
        final_message: str | None = None
        commands: dict[str, RuntimeCommand] = {}
        file_changes: dict[str, RuntimeFileChange] = {}
        terminal_error: str | None = None

        for event_index, event in enumerate(events):
            event_type = str(event.get("type", ""))
            if event_type == "thread.started" and isinstance(
                event.get("thread_id"), str
            ):
                thread_id = event["thread_id"]
            elif event_type == "turn.completed":
                turn_completed = True
                usage = event.get("usage")
                if isinstance(usage, dict):
                    input_tokens += cls._as_nonnegative_int(usage.get("input_tokens"))
                    cached = usage.get("cached_input_tokens")
                    details = usage.get("input_tokens_details")
                    if cached is None and isinstance(details, dict):
                        cached = details.get("cached_tokens")
                    cached_input_tokens += cls._as_nonnegative_int(cached)
                    output_tokens += cls._as_nonnegative_int(
                        usage.get("output_tokens")
                    )
                    reasoning = usage.get("reasoning_output_tokens")
                    output_details = usage.get("output_tokens_details")
                    if reasoning is None and isinstance(output_details, dict):
                        reasoning = output_details.get("reasoning_tokens")
                    reasoning_output_tokens += cls._as_nonnegative_int(reasoning)
            elif event_type in {"turn.failed", "error"}:
                error = event.get("error")
                if isinstance(error, dict):
                    terminal_error = str(error.get("message") or error.get("code") or error)
                else:
                    terminal_error = str(event.get("message") or error or event_type)

            if event_type not in {"item.started", "item.updated", "item.completed"}:
                continue
            item = event.get("item")
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or f"event_{event_index}")
            item_type = item.get("type")
            if item_type == "command_execution":
                commands[item_id] = RuntimeCommand(
                    id=item_id,
                    command=str(item.get("command") or "")[: cls._MAX_COMMAND_CHARS],
                    status=str(item.get("status") or event_type.removeprefix("item.")),
                    exit_code=cls._optional_int(
                        item.get("exit_code", item.get("exitCode"))
                    ),
                )
            elif item_type == "file_change":
                changes = item.get("changes")
                if not isinstance(changes, list):
                    changes = [item]
                for change_index, change in enumerate(changes):
                    if not isinstance(change, dict):
                        continue
                    path = change.get("path") or change.get("file")
                    if not isinstance(path, str) or not path:
                        continue
                    key = f"{item_id}:{change_index}:{path}"
                    file_changes[key] = RuntimeFileChange(
                        path=path[: cls._MAX_PATH_CHARS],
                        kind=str(change.get("kind") or change.get("type") or "changed"),
                        status=str(item.get("status") or event_type.removeprefix("item.")),
                    )
            elif item_type == "agent_message" and event_type == "item.completed":
                text = item.get("text")
                if isinstance(text, str):
                    final_message = text

        if terminal_error:
            raise RuntimeError(f"Codex turn failed: {terminal_error[-500:]}")
        if thread_id is None:
            raise RuntimeError("Codex JSONL did not include thread.started")
        if not turn_completed:
            raise RuntimeError("Codex JSONL did not include turn.completed")
        return _ParsedCodexStream(
            thread_id=thread_id,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            reasoning_output_tokens=reasoning_output_tokens,
            commands=list(commands.values()),
            file_changes=list(file_changes.values()),
            final_message=final_message,
            raw_event_count=len(events),
        )

    @staticmethod
    def _as_nonnegative_int(value: Any) -> int:
        parsed = CodexCliRuntime._optional_int(value)
        return max(parsed or 0, 0)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def _capture_clean_baseline(self) -> _GitBaseline:
        head = self._git_head(operation="Git baseline capture")
        status = self._run_git(
            [
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignore-submodules=none",
            ],
            operation="Git baseline capture",
        )
        if status:
            raise CodexRuntimeDisabled(
                "workspace-write mode requires a clean Git worktree at invocation "
                "start (tracked, staged, submodule, and untracked changes are refused)"
            )
        return _GitBaseline(
            head=head,
            status=status,
            status_sha256=hashlib.sha256(status).hexdigest(),
        )

    def _git_head(self, *, operation: str) -> str:
        raw = self._run_git(
            ["rev-parse", "--verify", "HEAD"], operation=operation
        )
        head = raw.decode("ascii", errors="strict").strip()
        if len(head) not in {40, 64} or any(
            character not in "0123456789abcdefABCDEF" for character in head
        ):
            raise RuntimeError(f"{operation} returned an invalid HEAD object id")
        return head.lower()

    def _restore_failed_write(self, baseline: _GitBaseline) -> str | None:
        """Restore Git-visible invocation changes when HEAD is still the baseline.

        The clean preflight makes every tracked/staged/untracked status entry belong
        to this invocation. Ignored files are intentionally outside both evidence and
        automatic deletion. Empty directories may remain, but a non-clean Git status
        after cleanup is treated as a hard failure.
        """

        try:
            current_head = self._git_head(operation="Git cleanup")
            if current_head != baseline.head:
                return (
                    f"HEAD changed from {baseline.head} to {current_head}; refusing "
                    "to rewrite Git history automatically"
                )
            tracked = self._decode_nul_paths(
                self._run_git(
                    [
                        "diff",
                        "--name-only",
                        "-z",
                        "--no-ext-diff",
                        "--no-renames",
                        baseline.head,
                        "--",
                    ],
                    operation="Git cleanup",
                )
            )
            for offset in range(0, len(tracked), 100):
                paths = tracked[offset : offset + 100]
                self._run_git(
                    [
                        "restore",
                        f"--source={baseline.head}",
                        "--staged",
                        "--worktree",
                        "--",
                        *paths,
                    ],
                    operation="Git cleanup",
                )

            untracked = self._decode_nul_paths(
                self._run_git(
                    ["ls-files", "--others", "--exclude-standard", "-z", "--"],
                    operation="Git cleanup",
                )
            )
            for relative in untracked:
                relative_path = Path(relative)
                if relative_path.is_absolute() or ".." in relative_path.parts:
                    return f"Git reported an unsafe untracked path: {relative!r}"
                path = self.workdir / relative_path
                try:
                    path.parent.resolve().relative_to(self.workdir)
                except ValueError:
                    return f"untracked path has a parent outside the worktree: {relative!r}"
                try:
                    path.unlink()
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    return f"could not remove untracked path {relative!r}: {exc}"

            remaining = self._run_git(
                [
                    "status",
                    "--porcelain=v1",
                    "-z",
                    "--untracked-files=all",
                    "--ignore-submodules=none",
                ],
                operation="Git cleanup",
            )
            if remaining:
                return "Git-visible changes remain after cleanup"
            return None
        except (OSError, RuntimeError, UnicodeError) as exc:
            return str(exc)[:500]

    def _capture_git_diff(
        self, *, baseline: _GitBaseline | None = None
    ) -> GitDiffMetadata:
        baseline_head = (
            baseline.head
            if baseline is not None
            else self._git_head(operation="Git diff evidence capture")
        )
        head_after = self._git_head(operation="Git diff evidence capture")
        if baseline is not None and head_after != baseline.head:
            raise RuntimeError(
                "Codex changed Git HEAD during a workspace-write invocation; "
                "the change cannot be attributed as an uncommitted bounded diff"
            )
        tracked_names = self._run_git(
            [
                "diff",
                "--name-only",
                "-z",
                "--no-ext-diff",
                "--no-renames",
                baseline_head,
                "--",
            ]
        )
        untracked_names = self._run_git(
            ["ls-files", "--others", "--exclude-standard", "-z", "--"]
        )
        name_only = self._decode_nul_paths(tracked_names)
        for path in self._decode_nul_paths(untracked_names):
            if path not in name_only:
                name_only.append(path)

        raw_numstat = self._run_git(
            [
                "diff",
                "--numstat",
                "-z",
                "--no-ext-diff",
                "--no-renames",
                baseline_head,
                "--",
            ]
        )
        numstat = self._parse_numstat(raw_numstat)
        tracked_paths = {item.path for item in numstat}
        raw_diff = self._run_git(
            [
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--no-color",
                "--unified=3",
                "--no-renames",
                baseline_head,
                "--",
            ]
        )

        digest = hashlib.sha256()
        digest.update(raw_diff)
        preview = bytearray(raw_diff[: self._MAX_DIFF_PREVIEW_BYTES])
        preview_truncated = len(raw_diff) > self._MAX_DIFF_PREVIEW_BYTES
        for relative in name_only:
            if relative in tracked_paths:
                continue
            marker = f"\n--- /dev/null\n+++ b/{relative}\n".encode("utf-8")
            digest.update(b"\0untracked\0")
            digest.update(relative.encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0")
            path = (self.workdir / relative).resolve()
            try:
                path.relative_to(self.workdir)
            except ValueError as exc:
                raise RuntimeError("Git reported a path outside the configured worktree") from exc
            additions = 0
            binary = False
            saw_bytes = False
            ended_with_newline = False
            remaining = self._MAX_DIFF_PREVIEW_BYTES - len(preview)
            if remaining > 0:
                preview.extend(marker[:remaining])
            if len(marker) > remaining:
                preview_truncated = True
            with path.open("rb") as handle:
                while chunk := handle.read(64 * 1024):
                    saw_bytes = True
                    binary = binary or b"\0" in chunk
                    additions += chunk.count(b"\n")
                    ended_with_newline = chunk.endswith(b"\n")
                    digest.update(chunk)
                    remaining = self._MAX_DIFF_PREVIEW_BYTES - len(preview)
                    if remaining > 0 and not binary:
                        preview.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        preview_truncated = True
            if saw_bytes and not ended_with_newline:
                additions += 1
            numstat.append(
                DiffNumstat(
                    path=relative,
                    additions=None if binary else additions,
                    deletions=None if binary else 0,
                    binary=binary,
                )
            )
        return GitDiffMetadata(
            name_only=name_only,
            numstat=numstat,
            sha256=digest.hexdigest(),
            preview=bytes(preview).decode("utf-8", errors="replace"),
            preview_truncated=preview_truncated,
            baseline_head=baseline_head,
            head_after=head_after,
            baseline_clean=True if baseline is not None else None,
            baseline_status_sha256=(
                baseline.status_sha256 if baseline is not None else None
            ),
        )

    def _run_git(
        self,
        arguments: list[str],
        *,
        operation: str = "Git diff evidence capture",
    ) -> bytes:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USER", "TMPDIR"}
        }
        environment.update({"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"})
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.workdir,
            env=environment,
            capture_output=True,
            text=False,
            timeout=self._GIT_TIMEOUT_SECONDS,
            check=False,
        )
        if completed.returncode != 0:
            diagnostic = completed.stderr.decode("utf-8", errors="replace").strip()[-500:]
            raise RuntimeError(f"{operation} failed: {diagnostic}")
        return completed.stdout

    @staticmethod
    def _decode_nul_paths(value: bytes) -> list[str]:
        return [
            item.decode("utf-8", errors="surrogateescape")
            for item in value.split(b"\0")
            if item
        ]

    @staticmethod
    def _parse_numstat(value: bytes) -> list[DiffNumstat]:
        results: list[DiffNumstat] = []
        for record in value.split(b"\0"):
            if not record:
                continue
            parts = record.split(b"\t", 2)
            if len(parts) != 3:
                raise RuntimeError("Git returned malformed numstat evidence")
            additions_raw, deletions_raw, path_raw = parts
            binary = additions_raw == b"-" or deletions_raw == b"-"
            results.append(
                DiffNumstat(
                    path=path_raw.decode("utf-8", errors="surrogateescape"),
                    additions=None if binary else int(additions_raw),
                    deletions=None if binary else int(deletions_raw),
                    binary=binary,
                )
            )
        return results

    @staticmethod
    def _parse_review(
        message: str | None,
    ) -> tuple[Literal["approved", "changes_requested", "unknown"], list[ReviewFinding]]:
        if not message:
            return "unknown", []
        candidate = message.strip()
        if candidate.startswith("```") and candidate.endswith("```"):
            lines = candidate.splitlines()
            candidate = "\n".join(lines[1:-1]).strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return "unknown", []
        if not isinstance(payload, dict):
            return "unknown", []
        raw_verdict = str(payload.get("verdict", "unknown")).lower()
        verdict: Literal["approved", "changes_requested", "unknown"]
        if raw_verdict == "approved":
            verdict = "approved"
        elif raw_verdict in {"changes_requested", "request_changes", "rejected"}:
            verdict = "changes_requested"
        else:
            verdict = "unknown"
        findings: list[ReviewFinding] = []
        raw_findings = payload.get("findings", [])
        if isinstance(raw_findings, list):
            for item in raw_findings[:50]:
                if isinstance(item, str):
                    findings.append(ReviewFinding(summary=item[:1_000]))
                    continue
                if not isinstance(item, dict):
                    continue
                severity = str(item.get("severity", "medium")).lower()
                if severity not in {"info", "low", "medium", "high", "critical"}:
                    severity = "medium"
                summary = item.get("summary") or item.get("title")
                if not isinstance(summary, str) or not summary.strip():
                    continue
                line = CodexCliRuntime._optional_int(item.get("line"))
                findings.append(
                    ReviewFinding(
                        severity=severity,  # type: ignore[arg-type]
                        summary=summary[:1_000],
                        file=str(item["file"])[:1_000]
                        if item.get("file") is not None
                        else None,
                        line=line if line is None or line > 0 else None,
                    )
                )
        return verdict, findings


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
            implementation_model=settings.implementation_model,
            reviewer_model=settings.reviewer_model,
        )
    return DeterministicRuntime()
