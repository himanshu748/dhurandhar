# Dhurandhar - submission draft

> [!WARNING]
> This is not yet a complete submission. The narrated video, final screenshot, video URL, final release gates, and tagged release are still uncaptured. The deterministic public demo is deployed and verified; the checklist at the end is the source of truth.

## One-line pitch

Dhurandhar turns one software objective into an auditable company run: eight persistent agents auction, build with Codex, review independently, verify, promote inside a recoverable sandbox, monitor, and learn from failure - with receipts.

## Category

**Developer Tools**

The hero objective adds a privacy-safe session evidence export to **Misconception Debugger**, a separate Education submission. Dhurandhar is the control plane around that target and does not present the target application as an internal Dhurandhar feature.

## Short description

Most coding agents stop at a patch. Dhurandhar controls the lifecycle around it. Atlas scopes the objective and requires Forge, Prism, and Rivet to submit evidence-backed bids. The lowest eligible bid wins. A live Codex invocation edits only a configured disposable Git worktree; a second, read-only Codex invocation acts as Aegis and returns a structured review. Sentinel accepts a live release only when a real diff exists and recognized test commands exit successfully. Shipwright records an internal, reversible sandbox promotion, and Chronicle preserves a source-linked account and durable memories.

Change Replay makes the whole causal chain inspectable: bid fees, escrow, payouts, model and thread provenance, token categories, commands, file changes, diff hash and preview, independent verdict, test evidence, sandbox health, and human decisions. A controlled regression assigns liability to implementation, review, QA, and release, restores the known-good sandbox state, and proposes four runtime-backed incident controls. Its deterministic comparison measures structural coverage of the memory, prompt, routing, and economy slots—not policy efficacy. Recording the controls for later briefs still requires a human click.

## Why this can win

The submission is not "eight chat personas." Its differentiator is a coherent control system around real Codex work:

- **Codex is the hero, not an optional footnote:** the main demo is one live workspace-write implementation plus a separate read-only reviewer invocation.
- **Evidence is executable:** a live run cannot advance without an actual Git diff and successful test-command exit codes.
- **The team has persistent state:** all eight roles have stable identity, capabilities, memory, balances, and source-linked history.
- **Allocation is accountable:** every engineer bids; evidence determines eligibility; fees, escrow, settlement, refund, and penalties are replayable.
- **Recovery closes the SDLC:** monitoring, liability, known-good recovery, postmortem, deterministic structural policy evidence, and human-gated learning are part of the same run.
- **The boundaries are honest:** internal sandbox promotion is never called external deployment, and fixture data is never called a model run.

## What it does

- accepts a bounded objective, description, and strict acceptance criteria;
- coordinates the exact roster: Atlas, Forge, Prism, Rivet, Aegis, Sentinel, Shipwright, and Chronicle;
- requires one evidence-backed bid from each of the three engineers;
- selects the lowest eligible bid and records assessments, fees, escrow, payouts, refunds, and penalties;
- invokes an explicitly enabled Codex CLI implementation runtime against one configured Git worktree;
- invokes an independent Codex reviewer in a read-only sandbox;
- parses structured JSONL into model, thread, tokens, commands, files, final message, and event count;
- captures changed files, numstat, diff SHA-256, and a bounded preview after workspace writes;
- blocks live promotion without a real diff, approved verdict, recognized test command, and zero failing test exits;
- records every material action in an append-only SHA-256-linked JSONL journal whose event discriminator is `type`;
- reconstructs runs, replay frames, agents, memories, balances, transactions, and policies from events;
- provides Change Replay with auction, provenance, evidence, ledger, and recovery inspection;
- injects a controlled sandbox regression and assigns liability to the implementer, Aegis, Sentinel, and Shipwright;
- restores the known-good sandbox version and records four controls already backed by executable release-path gates;
- compares active and proposed policy-mechanism coverage deterministically, without presenting the score as an efficacy benchmark;
- still requires an explicit human decision before activation;
- ships a deterministic, no-secret fallback for repeatable judging.

## How it was built

- FastAPI and Pydantic v2 for the strict company-control API;
- an append-only JSONL event store with canonical serialization and SHA-256 chain verification;
- deterministic reducers for runs, replay, agents, memories, credits, and policies;
- a Codex CLI adapter using structured JSONL, reduced environment, bounded capture, read-only review, and opt-in workspace writes;
- React 19, TypeScript, Vite, and Lucide for the Change Replay control room;
- Pytest and Vitest/Testing Library for runtime, auction, ledger, policy, recovery, API, and UI behavior;
- a multi-stage, non-root Docker build plus Docker Compose and Render scaffolding.

## OpenAI and Codex use

### Codex inside Dhurandhar

The implementation runtime calls the authenticated Codex CLI with a scoped brief, configured model, structured JSONL, and either `read-only` or `workspace-write` sandboxing. Workspace writes require three independent settings and an existing Git worktree. After the call, Dhurandhar captures Git evidence without asking the model to summarize its own diff.

Aegis is a second Codex call in a read-only sandbox. It receives the objective and bounded diff context, cannot edit the worktree, and must produce a structured verdict and findings. An unknown verdict or requested change fails closed.

The live event record contains the configured model, thread ID, token categories, command status and exit code, files, diff metadata, final message, and raw JSONL event count. The adapter does not persist raw process or command output and does not commit, push, merge, or deploy.

### Codex collaboration used to build Dhurandhar

Codex was used throughout the repository build: translating the original autonomous-software-company brief into a testable architecture, implementing the FastAPI and React system, adding the persistent roster and auction economy, hardening the runtime/reviewer/evidence boundary, testing the result, and revising the submission so claims match the code. This is materially different from adding a late model button to a conventionally built demo.

The README and release-notes draft include the real feedback session ID returned for the primary Codex build task so judges can inspect that collaboration.

> [!NOTE]
> **Codex collaboration session ID: `019f6172-596f-7d50-a842-b839fd16af3e`.** Codex 0.144.2 returned this exact value from the official feedback upload for the primary Dhurandhar build task on 2026-07-16. The upload omitted extra app log files.

### Current model truth

On 2026-07-16, the authenticated catalog listed `gpt-5.6-sol`. A completed workspace-write implementation and a distinct read-only reviewer invocation both recorded that exact slug. The thread IDs, token categories, commands, Git evidence, reviewer verdict, Sentinel result, settlement, recovery, and verified journal are in [Live Codex evidence](LIVE_EVIDENCE.md).

A configuration value alone is not evidence. Every submission claim names the exact recorded tier and links to the completed run.

## Hero objective: Misconception Debugger

Use the bounded objective already completed in the captured development run so the Codex result can be reviewed and verified inside the video:

**Title:** Add privacy-safe session evidence export API

**Description:** In this separate Education project, add a read-only endpoint that exports strict aggregate evidence for one learning session without exposing learner answers, written working, question prompts, expected answers, or diagnosis text. Do not add authentication, model calls, external storage, or deployment behavior.

**Acceptance criteria:**

1. `GET /api/sessions/{session_id}/evidence` returns session status, attempt count, three misconception counts, four provenance-mode counts, and total model tokens in a strict schema.
2. Zero-attempt and completed sessions are supported, and unknown sessions preserve the existing `404` behavior.
3. Focused tests prove both aggregate correctness and exclusion of raw learning text.

The final 2026-07-16 run produced a five-file, 226-insertion diff from the same clean baseline. A distinct read-only `gpt-5.6-sol` reviewer approved it, Sentinel's independent static-allowlist pytest command exited `0`, the 40-credit escrow settled completely, and the recovery drill ended at an unapproved human decision gate. The complete 89-event record is in [Live Codex evidence](LIVE_EVIDENCE.md). The earlier six-file `gpt-5.5` development run remains there as historical context. Product completion, hosted deployment, and Education-category claims belong to the separate Misconception Debugger submission.

## Safe live-run configuration

Create a disposable worktree from the separate target repository:

```bash
git -C /absolute/path/to/misconception-debugger status --short
git -C /absolute/path/to/misconception-debugger worktree add \
  /tmp/misconception-debugger-dhurandhar-demo \
  -b demo/dhurandhar-live \
  3332982b5cdb8e2e697e63d0e30797134c307c06
```

The status command must print nothing. Start a fresh Dhurandhar journal and the live runtime:

```bash
DHURANDHAR_RUNTIME=codex \
DHURANDHAR_ENABLE_CODEX_RUNTIME=true \
DHURANDHAR_CODEX_APPLY_CHANGES=true \
DHURANDHAR_CODEX_WORKDIR=/tmp/misconception-debugger-dhurandhar-demo \
DHURANDHAR_EVENT_LOG=/tmp/dhurandhar-misconception-demo-events.jsonl \
DHURANDHAR_SEED_DEMO=false \
DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.6-sol \
DHURANDHAR_REVIEWER_MODEL=gpt-5.6-sol \
DHURANDHAR_CODEX_TIMEOUT_SECONDS=600 \
make dev-backend
```

Run `make dev-frontend` separately. Use a new branch, worktree path, and event-log path for every recording. The exact tier must still appear in the authenticated catalog before another claimed live run.

## Three-minute judge video

Target length: **2:55**, narrated. Record the real run; if model latency is removed, mark the time cut on screen rather than implying an instantaneous response.

### 0:00-0:18 - Hook

Show the completed control room, then say:

> "Most coding agents stop at a patch. Dhurandhar runs the company around it: allocation, implementation, independent review, verification, recovery, and learning - all replayable."

Point to the `live` provenance badge and the Misconception Debugger objective.

### 0:18-0:42 - Persistent team and real auction

Open Agents long enough to show all eight names. Return to Replay and select the auction. Show that Forge, Prism, and Rivet all bid, one ineligible or higher bid cannot win merely by being cheap, and the lowest eligible bid is awarded. Briefly point to bid fees and bounty escrow.

### 0:42-1:25 - Live Codex is the hero

Show the moment the objective is submitted, then the resulting implementation event. In the evidence inspector, show:

- `live` + `workspace-write`;
- the recorded `gpt-5.6-sol` model field;
- implementation thread ID and measured token categories;
- actual commands with exit codes;
- changed files, numstat, diff SHA-256, and diff preview;
- final Codex message.

Do not use the deterministic seed for this section.

### 1:25-1:48 - Independent reviewer

Select Aegis's review event. Show a different thread ID, read-only sandbox, reviewer model, structured verdict, and findings. State that the implementing call cannot approve itself.

### 1:48-2:08 - Evidence gate and honest release semantics

Select Sentinel's verification and Shipwright's promotion. Show that successful test-command exits and a non-empty diff are mandatory. Point to `environment: demo-sandbox` and `external_deployment: false`; say explicitly that this prototype does not push, merge, or deploy externally.

### 2:08-2:35 - Recover and assign liability

Run the controlled recovery drill. Select the alert, then the four penalties: implementing engineer, Aegis, Sentinel, and Shipwright. Show the known-good sandbox restoration and source-linked incident evidence.

### 2:35-2:55 - Human-gated learning and close

Open the policy check and proposal. Show the four memory, prompt, routing, and economy slots, the `structure-only-not-efficacy` scope, and the human decision control. Leave the final recorded proposal visibly `proposed` with no active mechanisms; explain that only a later human approval could serialize the controls into another run, whose strategy would remain `policy-gated-demo-sandbox`, not public canary traffic. Close with:

> "Dhurandhar does not ask you to trust an agent transcript. It shows who did what, which evidence allowed the next step, what failure cost, and exactly where the human still decides."

## Deterministic fallback for judges

The hosted or Docker fallback is intentionally fixture-backed. It lets a judge inspect the roster, auction, economy, event chain, replay, recovery, and policy gate without credentials. It makes zero model calls, reports zero model tokens, and must be labeled `fixture` throughout.

The public Render instance and default Docker Compose stack are intentionally read-only: both run with `DHURANDHAR_ENV=production`, expose the seeded evidence, and reject mutation requests because no operator token is configured. On a fresh seeded instance, `GET /api/health` must return exactly:

```json
{"status":"ok","service":"Dhurandhar API","version":"0.1.0","event_chain_valid":true,"events":78,"runtime":"deterministic"}
```

Representative GET routes such as `/api/objectives` and `/api/runs` return `200`; `POST /api/objectives` without an operator token returns `503` with `{"detail":"mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured"}`. The narrated mutable hero run uses the separate local-development path with a controlled server-side operator token held only in the browser tab's memory.

The fallback is a reliability path, not the video story and not evidence for the Codex criterion.

### Verified public deployment — 2026-07-16

- Live demo: [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com)
- Source commit: `e1c689b1033b476e560a18c78425859726044d87`
- Blueprint: `exs-d9c6rmm1a83c73bsov5g`
- Render service: `srv-d9c6rt3tqb8s73agu030`
- Successful deploy: `dep-d9c821vavr4c73airodg`, status `live`
- Direct verification: exact deterministic health response with a valid 78-event chain; seeded objective and run IDs; three replay bids; `fixture` code provenance; frontend HTML `200`; and unauthenticated objective creation rejected with the exact documented `503` response.
- The error-log query scoped from the successful deploy start (`2026-07-16T06:58:15Z`) returned no error records.
- Ephemeral-storage disclosure: [README — Operator access and the public demo](../README.md#operator-access-and-the-public-demo).

## Challenges

- preserving independent review while both roles use the same bounded CLI boundary;
- distinguishing internal credits from measured model usage without fake economics;
- making diff, command, and token provenance inspectable without storing dangerous raw output;
- allowing a meaningful workspace write without granting commit, merge, deploy, or host authority;
- making recovery change future behavior without allowing a proposal to approve itself;
- presenting a dense SDLC and economy in under three minutes.

## Accomplishments

- exact eight-agent persistent company state with source-linked memory;
- mandatory three-engineer evidence-backed auction and replayable settlement;
- structured live Codex provenance plus independent read-only Codex review;
- fail-closed live gate requiring real diff and executable checks;
- one objective-to-sandbox-to-monitor-to-recovery-to-policy causal loop;
- accountable escaped-regression penalties across implementation, review, QA, and release;
- deterministic fallback, responsive Change Replay, and automated backend/frontend coverage;
- explicit separation between internal sandbox promotion and external deployment.

## What comes next

1. Record the final video and cover image, then publish the remaining direct submission URLs.
2. Add authenticated GitHub branch/PR and CI-evidence adapters with exact repository allowlists.
3. Add a real deployment-provider and monitor adapter while preserving human release authority.
4. Move the event journal to durable signed storage with authentication and tenant isolation.
5. Add independently versioned efficacy datasets alongside the current deterministic structural coverage check.

## Last-mile submission checklist

### Implemented in the repository

- [x] Exact eight-agent roster and role contracts.
- [x] Three-engineer auction with eligibility evidence and deterministic winner selection.
- [x] Bid fees, escrow, payouts, refunds, penalties, and conserved internal ledger.
- [x] Source-linked persistent memory and changelog events.
- [x] Structured Codex JSONL provenance and bounded Git diff evidence.
- [x] Separate read-only Codex reviewer and fail-closed verdict handling.
- [x] Live gate requiring a real diff and successful test commands.
- [x] Explicit `demo-sandbox` / `external_deployment: false` semantics.
- [x] Four-way escaped-regression liability and human-gated policy activation.
- [x] Deterministic no-secret judge fallback.
- [x] Captured `gpt-5.5` development run with distinct implementation/review threads, diff/test hashes, and a verified raw event journal.
- [x] Captured the final `gpt-5.6-sol` implementation, independent review, Sentinel gate, settlement, recovery, and verified raw journal.

### Evidence and publishing still required

- [x] Confirm `gpt-5.6-sol` in the authenticated Codex catalog.
- [x] Run implementation and reviewer with `gpt-5.6-sol` against a fresh disposable worktree.
- [x] Capture the live model fields, implementation/reviewer thread IDs, tokens, commands, files, diff, verdict, final messages, settlement, and recovery evidence.
- [x] Add the returned primary Codex collaboration session ID to README and release notes.
- [x] Deploy the deterministic public demo and verify its ephemeral-storage disclosure.
- [ ] Record and narrate the sub-three-minute live-Codex video.
- [ ] Capture a final implementation cover image from the release candidate.
- [ ] Publish direct live-demo, repository, and video URLs.
- [ ] Re-run `make test`, `make lint`, `make build`, and the Docker smoke test from the release commit.
- [ ] Create and push the tagged release.
- [ ] Verify every claim and link against the final public commit.

## Release/tag procedure

Complete and check every pre-release evidence item above first. The tag action itself is intentionally post-guard. Then run these commands in order; do not create or push a release tag unless the first command passes:

```bash
make submission-check
git tag -s v1.0.0 -m "Dhurandhar OpenAI Build Week submission"
git push origin v1.0.0
```

Rules references: [OpenAI Build Week rules](https://openai.devpost.com/rules) and [OpenAI Build Week](https://openai.com/build-week/).
