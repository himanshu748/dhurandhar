# Dhurandhar — submission draft

## One-line pitch

Dhurandhar turns a software objective into an auditable delivery-and-recovery run, then improves how the next run operates using benchmark-gated memory, prompt, routing, and economy changes.

## Category

Developer Tools

## Short description

Most coding agents stop at a patch. Dhurandhar is the control plane around the patch: product scope, implementation runtime, independent review, QA, release, monitoring, rollback, internal resource accounting, and self-improvement all become typed events in one replayable hash chain.

The demo starts with Dhurandhar's own monitored pulse endpoint. A judge can inject a controlled HTTP 500 from the UI. Sentinel detects the error-budget breach; Shipwright restores the known-good version; Aegis records root cause and evaluates a four-case shadow benchmark; Atlas proposes one change in each bounded improvement class. Promotion is refused unless the candidate beats baseline and has zero critical regressions, and it still requires a human click. The next objective visibly inherits those mechanisms and changes its deployment strategy to a canary.

## Inspiration

Agent demos often show an impressive transcript but leave the consequential questions unanswered: What exactly changed? Which evidence justified the next transition? What happened after deployment? Who can weaken the policy? Could the system learn from a failure without silently rewriting itself?

Dhurandhar treats those questions as the product. The interface is an operations console, not an agent chat room.

## What it does

- accepts arbitrary bounded software objectives and strict acceptance criteria;
- coordinates product, engineer, reviewer, QA/reliability, release, and policy roles;
- invokes a deterministic fixture by default or an explicitly enabled Codex CLI runtime;
- records all material actions in an append-only SHA-256-linked JSONL journal;
- reconstructs objectives, runs, agent state, balances, policies, and replay frames from events;
- provides Change Replay with playback, keyboard seek, evidence inspection, artifacts, tokens, and credits;
- injects a controlled post-release regression and automatically detects the error-budget breach;
- rolls back to the known-good version and records root-cause evidence;
- proposes exactly four improvement mechanisms: memory, prompt, routing, and economy;
- requires candidate score > baseline, zero critical regressions, and human approval;
- applies an approved policy to future runs, including a visible canary strategy;
- ships as one non-root Docker container with safe deterministic defaults.

## How it was built

- FastAPI and Pydantic v2 for the strict control-plane API;
- an append-only JSONL event store with canonical serialization and SHA-256 chain verification;
- a deterministic event reducer for runs, replay frames, agents, internal credits, and policies;
- React 19, TypeScript, Vite, and Lucide for the Change Replay interface;
- an optional Codex CLI adapter with read-only default and triple-opt-in workspace writes;
- Vitest/Testing Library and Pytest for contract, policy-gate, runtime, reducer, and UI coverage;
- a multi-stage Docker build that serves the compiled UI from the FastAPI process;
- Render and Docker Compose release configurations.

## OpenAI use

The implemented OpenAI boundary is the optional Codex CLI runtime. Read-only use requires both `DHURANDHAR_RUNTIME=codex` and `DHURANDHAR_ENABLE_CODEX_RUNTIME=true`. Worktree edits require the independent third flag `DHURANDHAR_CODEX_APPLY_CHANGES=true` and a configured Git worktree. The adapter does not commit, push, merge, deploy, or enable approval bypasses.

The zero-secret judge path is deterministic and makes no model call. Deterministic role events must not be presented as GPT-5.6 output. Before submission, capture one live Codex worktree run and attach its repository diff plus the required Codex session/feedback identifier; do not substitute configuration screenshots for usage evidence.

## Challenges

- separating internal credits from actual model-token usage without implying fake economics;
- making replay order deterministic even when wall-clock timestamps collide;
- allowing self-improvement without allowing a proposal to silently weaken its own gate;
- presenting dense SDLC evidence in a three-minute, screenshot-legible interface;
- keeping the default demo useful without secrets while preserving an honest live-runtime boundary.

## Accomplishments

- a full objective → release → monitor → incident → rollback → benchmark → policy → inherited-next-run loop;
- four explicit improvement classes with executable approval guards;
- a verifiable event chain and source-linked internal ledger;
- one-click recovery and policy-promotion flows tested in a real browser;
- responsive UI with zero console errors and no horizontal overflow at 390 px;
- 26 automated tests, a clean TypeScript build, and a verified non-root production container.

## What comes next

1. Per-run Git worktree creation plus independent diff, command, check, token, and commit capture.
2. GitHub branch/PR and CI-result adapters with exact repository allowlists.
3. A direct GPT-5.6 role runtime whose decisions and measured usage appear as first-class evidence.
4. Real deployment-provider and monitor ingestion instead of deterministic deployment events.
5. Authentication, durable external event storage, signed provenance, and multi-tenant isolation.

## Three-minute judge script

1. Open **Replay** and explain the ordered, hash-chained self-hosting run.
2. Click **Run recovery drill**; select the HTTP 500 alert, rollback, root-cause, and benchmark events.
3. Open **Policies**; show all four mechanisms and the `0.25 → 1.00` evidence, then click **Promote**.
4. Create the prefilled objective and return to Replay.
5. Select the inherited-policy event and the deployment artifact containing `canary-10-percent`.
6. End on tokens versus credits and state the bootstrap boundary plainly.

## Last-mile submission checklist

- [ ] Publish the repository with a tagged release.
- [ ] Deploy the deterministic demo and verify persistent storage expectations.
- [ ] Record a 2–3 minute video following the judge script.
- [ ] Capture one real Codex run against a disposable worktree.
- [ ] Add the required Codex session/feedback identifier.
- [ ] Add direct live-demo, repository, and video links.
- [ ] Use the implementation screenshot, not the generated concept, as the cover image.
- [ ] Re-run `make test`, `make lint`, `make build`, and the Docker smoke test from the release commit.
