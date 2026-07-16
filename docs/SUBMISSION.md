# Dhurandhar - submission draft

> [!WARNING]
> This is not yet a complete submission. The narrated video, cover image, and video URL are **pending**, and the release is **not tagged**. The hardened deterministic public playback and release gates must be re-verified from the final candidate; the checklist at the end is the source of truth.

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
- parses structured JSONL into requested model, any stream-observed model, thread, tokens, commands, files, final message, and event count;
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

For future runs, the live event record distinguishes `requested_model` from nullable `observed_model` and also records the exact invocation argv and `codex --version`. A stream-observed model that conflicts with itself or disagrees with the request fails closed. The record also contains the thread ID, token categories, command status and exit code, files, diff metadata, final message, and raw JSONL event count. The adapter does not persist raw process or command output and does not commit, push, merge, or deploy.

### Codex collaboration used to build Dhurandhar

Codex was used throughout the repository build: translating the original autonomous-software-company brief into a testable architecture, implementing the FastAPI and React system, adding the persistent roster and auction economy, hardening the runtime/reviewer/evidence boundary, testing the result, and revising the submission so claims match the code. This is materially different from adding a late model button to a conventionally built demo.

The README and release-notes draft include the real feedback session ID returned for the primary Codex build task so judges can inspect that collaboration.

> [!NOTE]
> **Codex collaboration session ID: `019f6172-596f-7d50-a842-b839fd16af3e`.** Codex 0.144.2 returned this exact value from the official feedback upload for the primary Dhurandhar build task on 2026-07-16. The upload omitted extra app log files.

### Current model truth

On 2026-07-16, the authenticated catalog listed `gpt-5.6-sol`. The completed workspace-write implementation and distinct read-only review each requested that exact slug through `--model`, and the CLI accepted both invocations. Their thread IDs and token categories were parsed from `codex exec --json`, but the historical stdout did not echo a model field to cross-check. The requested-slug limitation, commands, Git evidence, reviewer verdict, Sentinel result, settlement, recovery, and verified journal are in [Live Codex evidence](LIVE_EVIDENCE.md).

A configuration value alone is not stream-observed model evidence. The historical journal remains immutable and has not been backfilled; every claim links the requested tier to the completed stream-derived threads/tokens and independent Git and Sentinel evidence while naming the limitation.

## Hero objective: Misconception Debugger

Use the bounded objective from the captured final 2026-07-16 run so the Codex result can be reviewed and verified inside the video:

**Title:** Add privacy-safe session evidence export API

**Description:** In this separate Education project, add a read-only endpoint that exports strict aggregate evidence for one learning session without exposing learner answers, written working, question prompts, expected answers, or diagnosis text. Do not add authentication, model calls, external storage, or deployment behavior.

**Acceptance criteria:**

1. `GET /api/sessions/{session_id}/evidence` returns session status, attempt count, three misconception counts, four provenance-mode counts, and total model tokens in a strict schema.
2. Zero-attempt and completed sessions are supported, and unknown sessions preserve the existing `404` behavior.
3. Focused tests prove both aggregate correctness and exclusion of raw learning text.

The final 2026-07-16 run produced a five-file, 226-insertion diff from the same clean baseline. A distinct read-only reviewer invocation requested `gpt-5.6-sol` and approved it, Sentinel's independent static-allowlist pytest command exited `0`, the 40-credit escrow settled completely, and the recovery drill ended at an unapproved human decision gate. The complete 89-event record and model-verification limitation are in [Live Codex evidence](LIVE_EVIDENCE.md). The earlier six-file `gpt-5.5` development run remains there as historical context. Product completion, hosted deployment, and Education-category claims belong to the separate Misconception Debugger submission.

## Safe live-run configuration for another model run

The final evidence already exists. Use the immutable playback procedure in the
[video shot list](VIDEO_SHOT_LIST.md) for recording. Use this section only if a
new model invocation is intentionally required; it creates new evidence rather
than replaying the captured final run.

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

Target length: **2:55**, narrated. Replay the captured real run from its read-only journal copy. If footage from the original model latency is removed, mark the time cut on screen rather than implying an instantaneous response.

The exact immutable-playback commands, event sequences, UI proof labels, and narration guardrails are in the [evidence-based video shot list](VIDEO_SHOT_LIST.md).

### 0:00-0:18 - Hook

Show the completed control room, then say:

> "Most coding agents stop at a patch. Dhurandhar runs the company around it: allocation, implementation, independent review, verification, recovery, and learning - all replayable."

Point to the `live` provenance badge and the Misconception Debugger objective.

### 0:18-0:42 - Persistent team and real auction

Open Agents long enough to show all eight names. Return to Replay and select the auction. Show that Forge, Prism, and Rivet all bid, one ineligible or higher bid cannot win merely by being cheap, and the lowest eligible bid is awarded. Briefly point to bid fees and bounty escrow.

### 0:42-1:20 - Live Codex is the hero

Show the moment the objective is submitted, then the resulting implementation event. In the evidence inspector, show:

- `live` + `workspace-write`;
- the historical requested-model field showing `gpt-5.6-sol`, explicitly described as requested and CLI-accepted rather than stream-echoed;
- implementation thread ID and measured token categories;
- actual commands with exit codes;
- changed files, numstat, diff SHA-256, and diff preview;
- final Codex message.

Do not use the deterministic seed for this section.

### 1:20-1:48 - Diff and independent reviewer

Keep the implementation diff evidence visible, then select Aegis's review event. Show a different thread ID, read-only sandbox, reviewer model, structured verdict, and findings. State that the implementing call cannot approve itself. Do not claim that every reviewer-side command passed; Sentinel owns the release gate.

### 1:48-2:18 - Evidence gate, settlement, and honest release semantics

Select Sentinel's verification and Shipwright's promotion. Show the independent `EXIT 0`, then advance until the ledger says `CONSERVED · 40/40 CR`. Point to `environment: demo-sandbox` and `external_deployment: false`; say explicitly that this prototype does not push, merge, or deploy externally.

### 2:18-2:40 - Recorded recovery and human authority

Replay the recorded recovery drill. Select the alert, then the four penalties: implementing engineer, Aegis, Sentinel, and Shipwright. Show the known-good sandbox restoration, source-linked incident evidence, four proposed controls, and the human decision gate. Leave the final proposal visibly `proposed`; the read-only recording server must not mutate it.

### 2:40-2:55 - Deployed read-only playback and close

Open the Render URL at its landing page. Keep the deterministic-replay disclosure, `fixture` playback badge, `NO MODEL CALL`, live-evidence link, and `/replay` action visible. Explain that the hosted process makes no new model calls and replays the committed immutable 89-event live journal; event cards preserve historical live provenance and must not be presented as a new live call. Close with:

> "Dhurandhar does not ask you to trust an agent transcript. It shows who did what, which evidence allowed the next step, what failure cost, and exactly where the human still decides."

## Deterministic playback for judges

The hosted and production-shaped Docker paths are deterministic, read-only playback of the committed immutable 89-event live-run journal. They let a judge inspect the roster, auction, economy, event chain, replay, recovery, and policy gate without credentials. The current process makes zero new model calls. Its landing-page `fixture` badge labels the playback process; the `/replay` cards preserve the captured events' historical `live` provenance, requested slug, thread IDs, and token totals.

The public Render instance and default Docker Compose stack are intentionally read-only: both load the image-baked journal, and the public-replay entrypoint removes any inherited operator token before startup. The verified release returns:

```json
{"status":"ok","service":"Dhurandhar API","version":"0.1.0","event_chain_valid":true,"events":89,"runtime":"deterministic"}
```

Representative GET routes such as `/api/objectives` and `/api/runs` return `200`; `POST /api/objectives` without an operator token returns `503` with `{"detail":"mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured"}`. The narrated mutable hero run uses the separate local-development path with a controlled server-side operator token held only in the browser tab's memory.

Playback is an accessible evidence viewer, not proof that the hosted process called Codex. The real-call evidence is the immutable historical record documented in [Live Codex evidence](LIVE_EVIDENCE.md).

The separate `make demo` path remains a synthetic 78-event seed for offline product testing. That mode is wholly `fixture`, has no threads or model tokens, and is not the hosted recorded-run playback.

### Public release verification

- Live demo: [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com)
- Source repository: [https://github.com/himanshu748/dhurandhar](https://github.com/himanshu748/dhurandhar)
- Direct verification completed 2026-07-16: deterministic health with a valid 89-event chain; `/` landing HTML `200`; `/replay` HTML `200`; GET objectives, runs, and events `200`; and unauthenticated objective creation rejected with the documented `503` response.
- Evidence storage: the committed journal is copied read-only into the image; Render's ephemeral filesystem is not used as the evidence source.
- Release source commit: `55aae7648c2357ae9679ecd5523fb61556a16b0d`; Render deployment: `dep-d9c9drjbc2fs73bipqqg` (`live` at 2026-07-16T08:32:41Z). Earlier seeded-fixture deployment identifiers are not reused.

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
- [x] Deterministic no-secret recorded-journal playback, with a separate seeded-fixture test mode.
- [x] Captured `gpt-5.5` development run with distinct implementation/review threads, diff/test hashes, and a verified raw event journal.
- [x] Captured the final run that requested `gpt-5.6-sol` for implementation and review, plus the independent Sentinel gate, settlement, recovery, and verified raw journal.

### Evidence and publishing still required

- [x] Confirm `gpt-5.6-sol` in the authenticated Codex catalog.
- [x] Run implementation and reviewer with `gpt-5.6-sol` against a fresh disposable worktree.
- [x] Capture the requested model slug, stream-derived implementation/reviewer thread IDs and tokens, commands, files, diff, verdict, final messages, settlement, and recovery evidence; document that stdout supplied no observed model field.
- [x] Add the returned primary Codex collaboration session ID to README and release notes.
- [x] Redeploy the hardened deterministic 89-event public playback and record the verified source commit and deployment identifier.
- [ ] Record and narrate the sub-three-minute live-Codex video.
- [ ] Capture a final implementation cover image from the release candidate.
- [ ] Add the final video URL alongside the verified live-demo and source-repository URLs.
- [x] Re-run `make test`, `make lint`, `make build`, `make submission-check`, and the Docker smoke test from the hardened release candidate; the submission guard now reports only unfinished human media items.
- [ ] Create and push the tagged release.
- [x] Verify every current claim, journal identifier, checksum, relative link, public repository URL, and live-demo response after the final rollout.

## Release/tag procedure

Complete and check every pre-release evidence item above first. Merge the release commit into the default `main` branch and verify that it is an ancestor of the public branch before tagging. The tag action itself is intentionally post-guard. Then run these commands in order; do not create or push a release tag unless the ancestry check and submission guard both pass:

```bash
git fetch origin main
git merge-base --is-ancestor HEAD origin/main
make submission-check
git tag -s v1.0.0 -m "Dhurandhar OpenAI Build Week submission"
git push origin v1.0.0
```

Rules references: [OpenAI Build Week rules](https://openai.devpost.com/rules) and [OpenAI Build Week](https://openai.com/build-week/).
