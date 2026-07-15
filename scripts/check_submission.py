#!/usr/bin/env python3
"""Block a release tag while judge-facing submission evidence is incomplete."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "docs" / "SUBMISSION.md"
README = ROOT / "README.md"
PLACEHOLDER = "TODO" + " - NOT CAPTURED"
MODEL_CLAIM = "gpt" + "-5.5"
CHECKLIST_HEADING = "### Evidence and publishing still required"
POST_GUARD_ACTION = "Create and push the tagged release."


@dataclass(frozen=True)
class Blocker:
    category: str
    path: Path
    line: int
    detail: str


def placeholder_blockers() -> list[Blocker]:
    """Search tracked release content without hydrating every worktree file."""

    blockers: list[Blocker] = []
    completed = subprocess.run(
        ["git", "grep", "-n", "-F", "-e", PLACEHOLDER, "--"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(completed.stderr.strip() or "git grep failed")
    for record in completed.stdout.splitlines():
        path_text, line_text, detail = record.split(":", maxsplit=2)
        blockers.append(
            Blocker("placeholder", ROOT / path_text, int(line_text), detail.strip())
        )
    return blockers


def readme_model_claim_blockers() -> list[Blocker]:
    """Flag prose claims while ignoring example configuration inside code fences."""

    blockers: list[Blocker] = []
    in_fence = False
    for line_number, line in enumerate(README.read_text().splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and MODEL_CLAIM in line:
            blockers.append(Blocker("README model claim", README, line_number, line.strip()))
    return blockers


def unchecked_critical_items() -> list[Blocker]:
    blockers: list[Blocker] = []
    in_critical_checklist = False
    for line_number, line in enumerate(
        SUBMISSION.read_text().splitlines(), start=1
    ):
        if line == CHECKLIST_HEADING:
            in_critical_checklist = True
            continue
        if in_critical_checklist and line.startswith("##"):
            break
        if not in_critical_checklist or not line.startswith("- [ ] "):
            continue
        item = line.removeprefix("- [ ] ").strip()
        # The guard must pass before this action can be performed.
        if item == POST_GUARD_ACTION:
            continue
        blockers.append(Blocker("critical checklist", SUBMISSION, line_number, item))
    return blockers


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    blockers = [
        *placeholder_blockers(),
        *readme_model_claim_blockers(),
        *unchecked_critical_items(),
    ]
    if not blockers:
        print("SUBMISSION CHECK: PASS")
        print("No release-blocking placeholders, model claims, or checklist items remain.")
        return 0

    print(f"SUBMISSION CHECK: FAILED ({len(blockers)} blockers)")
    for blocker in blockers:
        print(
            f"- [{blocker.category}] {relative(blocker.path)}:{blocker.line}: "
            f"{blocker.detail}"
        )
    print("Release/tagging is blocked. Resolve every item above and rerun `make submission-check`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
