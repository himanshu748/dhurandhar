# Dhurandhar

**Give it one software objective. Eight persistent agents auction the work, build it with Codex, review it independently, verify it, promote it inside a recoverable sandbox, monitor it, and learn from failure - with receipts.**

Dhurandhar is an experimental software-company control plane for a solo founder. It turns an objective into an auditable SDLC run instead of stopping at a code patch. Its proof surface, **Change Replay**, links every consequential decision to source evidence in an append-only, SHA-256-chained event journal.

The submission story is a **live Codex workspace-write run** against a disposable Git worktree. The captured target objective adds a privacy-safe session evidence export to **Misconception Debugger**, a separate Education project. Dhurandhar is the Developer Tools entry and the control plane around that work; it does not claim Misconception Debugger as an internal Dhurandhar feature.

> [!IMPORTANT]
> Dhurandhar is a hackathon prototype, not an unattended production deployment system. A successful "promotion" is an internal, reversible `demo-sandbox` lifecycle transition. The current adapter does not commit, push, merge, or deploy to external infrastructure.

![Dhurandhar Change Replay implementation](output/playwright/dhurandhar-desktop-1440x900.png)

The image above is an implementation capture, not proof of a model call. The generated [design concept](docs/design-concept.png) and [visual fidelity ledger](docs/FIDELITY_LEDGER.md) are kept separately.

## The persistent company

Dhurandhar always starts with the same eight agents. Their identities, capabilities, balances, memory seeds, and status persist in the event-sourced company state.

| Agent | Contract | Consequential responsibility |
| --- | --- | --- |
| [Atlas](agents/roles/atlas.md) | Product manager | Scope the objective, name acceptance evidence, and run the auction |
| [Forge](agents/roles/forge.md) | Backend engineer | Bid on and implement backend-heavy objectives |
| [Prism](agents/roles/prism.md) | Frontend engineer | Bid on and implement interface-heavy objectives |
| [Rivet](agents/roles/rivet.md) | Platform engineer | Bid on and implement delivery or infrastructure-heavy objectives |
| [Aegis](agents/roles/aegis.md) | Adversarial reviewer | Run an independent, read-only review and issue a structured verdict |
| [Sentinel](agents/roles/sentinel.md) | QA and saboteur | Falsify claims, verify executable checks, and monitor sandbox health |
| [Shipwright](agents/roles/shipwright.md) | Release and recovery engineer | Gate reversible sandbox promotion and restore known-good state |
| [Chronicle](agents/roles/chronicle.md) | Historian | Preserve source-linked changelogs and durable operating memories |

The immutable operating boundary is in the [company constitution](agents/constitution.md).

## What makes the run more than agent role-play

### All three engineers bid

Every implementation auction requires exactly one bid from Forge, Prism, and Rivet. A bid is eligible only when the agent is available and funded, has the required capability, stays within budget, clears the credibility threshold, and cites evidence belonging to that engineer. Atlas selects the **lowest-cost eligible bid**; credibility, evidence score, and stable engineer ID break ties in that order.

The economy is explicit, event-sourced, and run-linked:

- the customer issues a 40-credit objective budget to Atlas;
- each engineer pays a 1-credit participation fee;
- Atlas locks the 40-credit bounty in escrow before implementation;
- after an approved review and successful verification, escrow pays the winning bid, 5 credits each to Aegis and Sentinel, 3 to Shipwright, 2 to Chronicle, and refunds the remainder to Atlas;
- failed evidence produces a penalty and refunds the unreleased bounty;
- an escaped regression penalizes the implementing engineer, Aegis, Sentinel, and Shipwright because implementation, review, verification, and promotion all failed to prevent escape.

Credits are internal allocation units, not money and not model tokens. Every transaction has a causal event and the ledger checks conservation.

### Live Codex evidence is first-class data

The Codex adapter consumes structured JSONL and records:

- provenance (`live` or `fixture`), sandbox mode, configured model, and Codex thread ID;
- input, cached-input, output, and reasoning-output tokens;
- commands, status, and exit code;
- reported file changes;
- Git changed-file list, numstat, diff SHA-256, bounded preview, and truncation status;
- final Codex message and raw JSONL event count.

Raw subprocess output is deliberately not persisted. The adapter receives a reduced environment and never gets a policy bypass.

Aegis is a **second Codex invocation** in a read-only sandbox. Its separate thread returns a structured `approved` or `changes_requested` verdict plus severity, summary, file, and line for each finding. The implementing invocation cannot approve itself.

### A live run fails closed

For `provenance=live`, Dhurandhar refuses sandbox promotion unless all of these are present:

1. workspace-write mode was explicitly enabled;
2. the Git evidence contains at least one changed file;
3. Aegis returned an approved independent verdict;
4. at least one recognized test command ran;
5. every recognized test command exited with status 0.

Missing diff or test evidence produces `tests.unverified`, an agent penalty, escrow refund, and a failed run. A prose claim that tests passed is not sufficient.

### Memory and self-improvement preserve provenance

Each agent recalls persistent operating memory before consequential work. New durable memories are append-only and carry source event IDs. Chronicle records the delivery account only after it can link planning, code, review, tests, promotion, and health evidence.

After a controlled regression, Dhurandhar can restore the known-good sandbox version and propose one runtime-backed control in each bounded class: memory, prompt, routing, and economy. Its deterministic check only measures whether the active and proposed policy sets structurally cover those four control kinds; it is not a shadow replay or an efficacy claim. Explicit human approval is still required. Approved controls are serialized into later `policy.inherited` events and runtime briefs, while release behavior remains a policy-gated `demo-sandbox` transition rather than public canary traffic.

## Architecture at a glance

```mermaid
flowchart LR
    F["Solo founder"] --> UI["Vite control plane"]
    UI --> API["FastAPI company kernel"]
    API --> A["Atlas: scope and auction"]
    A --> ENG["Forge + Prism + Rivet: three bids"]
    ENG --> C1["Codex implementation\nworkspace-write"]
    C1 --> W["Disposable Git worktree"]
    W --> C2["Independent Codex review\nread-only"]
    C2 --> G["Sentinel evidence gate"]
    G --> S["Shipwright demo-sandbox promotion"]
    S --> H["Sentinel health + recovery"]
    H --> M["Chronicle source-linked memory"]
    API --> E[("Hash-chained event ledger")]
    A --> E
    ENG --> E
    C1 --> E
    C2 --> E
    G --> E
    S --> E
    H --> E
    M --> E
    E --> UI
```

See [Architecture](docs/ARCHITECTURE.md) for the state machine, evidence contract, and trust boundaries. See [Visual specification](docs/VISUAL_SPEC.md) for the product UI contract and [Submission draft](docs/SUBMISSION.md) for the judge script and final checklist.

## Prerequisites and installation

Run all commands from the repository root. The `python` command must resolve to Python 3.12 or newer. You also need Node.js 22.13+ (or 24+), npm, Git, GNU Make, and, for the container path, Docker Engine or Docker Desktop with Docker Compose v2 and `up --wait` support.

```bash
python --version
node --version
docker compose version
python -m venv .venv
source .venv/bin/activate
make install
```

`make install` installs the backend development requirements, including pytest, and restores the locked frontend dependencies with `npm ci`.

## Hero demo: live Codex builds Misconception Debugger

This is the submission path. Run it locally because the production image does not bundle an authenticated Codex CLI.

The completed development run is documented in [Live Codex evidence](docs/LIVE_EVIDENCE.md): Forge won a three-engineer auction, a `gpt-5.5` workspace-write thread produced a six-file diff, a distinct read-only `gpt-5.5` thread approved it, and Sentinel independently passed 16 tests. The feature was then reviewed and committed to the Education repository. This is genuine Codex evidence, but it must be repeated with GPT-5.6 for the final competition recording.

### 1. Prepare an isolated target

Start from the separate Misconception Debugger Git repository and create a disposable worktree from the recorded clean baseline on a throwaway branch:

```bash
git -C /absolute/path/to/misconception-debugger status --short
git -C /absolute/path/to/misconception-debugger worktree add \
  /tmp/misconception-debugger-dhurandhar-demo \
  -b demo/dhurandhar-live \
  3332982b5cdb8e2e697e63d0e30797134c307c06
```

The first command should print nothing. Do not point workspace-write mode at Dhurandhar itself, a production checkout, or a worktree containing uncommitted work.

### 2. Start Dhurandhar with all write gates explicit

Install and authenticate the Codex CLI, complete [Prerequisites and installation](#prerequisites-and-installation), then start the backend from the Dhurandhar repository root. The operator token below is a local demo credential; replace it for any environment beyond this disposable recording:

```bash
source .venv/bin/activate
DHURANDHAR_OPERATOR_TOKEN=dhurandhar-demo-operator-token \
DHURANDHAR_RUNTIME=codex \
DHURANDHAR_ENABLE_CODEX_RUNTIME=true \
DHURANDHAR_CODEX_APPLY_CHANGES=true \
DHURANDHAR_CODEX_WORKDIR=/tmp/misconception-debugger-dhurandhar-demo \
DHURANDHAR_EVENT_LOG=/tmp/dhurandhar-misconception-demo-events.jsonl \
DHURANDHAR_SEED_DEMO=false \
DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.5 \
DHURANDHAR_REVIEWER_MODEL=gpt-5.5 \
make dev-backend
```

Use a new event-log path for every recorded run. In a second terminal:

```bash
make dev-frontend
```

Open [http://localhost:5173](http://localhost:5173). Kernel health must say `codex`, and the run evidence must say `live` and `workspace-write` before it can be used in a submission claim.

Before submitting the objective, click **Read-only** in the top bar and load the same `dhurandhar-demo-operator-token` value. It is held only in the current browser tab's React memory.

### 3. Submit the bounded objective

Use **New objective** with this demo contract:

> **Title:** Add privacy-safe session evidence export API
>
> **Description:** In this separate Education project, add a read-only endpoint that exports strict aggregate evidence for one learning session without exposing learner answers, written working, question prompts, expected answers, or diagnosis text. Do not add authentication, model calls, external storage, or deployment behavior.
>
> **Acceptance criteria:**
> 1. `GET /api/sessions/{session_id}/evidence` returns session status, attempt count, three misconception counts, four provenance-mode counts, and total model tokens in a strict schema.
> 2. Zero-attempt and completed sessions are supported, and unknown sessions preserve the existing `404` behavior.
> 3. Focused tests prove both aggregate correctness and exclusion of raw learning text.

All three engineers must bid. In Change Replay, show the winning evidence-backed bid, the implementation thread/model/tokens, actual command exit codes, changed files and diff hash/preview, then the separate reviewer thread and verdict. The run can enter the internal sandbox only after the live evidence gate succeeds.

The captured run IDs, thread IDs, token categories, diff and stdout hashes, journal checksum, and recovery sequence are published in [Live Codex evidence](docs/LIVE_EVIDENCE.md). The raw 90-event journal remains part of the repository so the proof is independently chain-verifiable.

### 4. Show recovery and accountable learning

After the run completes, use **Run recovery drill**. The API-driven drill appends a controlled sandbox regression, Sentinel alert, four liability penalties, known-good restoration, deterministic structural control-coverage check, and policy proposal. Show that activation still waits for a human click and that the next run records the approved controls in its event evidence and runtime brief.

The drill is real application behavior over the event journal, but it is not an external production outage or infrastructure rollback.

## Model status and GPT-5.6 submission requirement

As of 2026-07-15, the currently authenticated Codex catalog available to this project supports `gpt-5.5`; both adapter defaults therefore use `gpt-5.5`. No GPT-5.6 run is claimed in this repository.

Before the final submission, after the account has GPT-5.6 access:

1. set both `DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.6` and `DHURANDHAR_REVIEWER_MODEL=gpt-5.6`;
2. repeat the live disposable-worktree run;
3. verify that the implementation and reviewer events both record `gpt-5.6`;
4. capture the thread IDs, token usage, commands, diff, verdict, video, and `/feedback` session ID.

Configuration is not evidence. Do not describe the project as GPT-5.6-powered until that run has been captured.

## Codex collaboration

Codex was used as the engineering collaborator for this repository, not merely placed behind a runtime flag. It helped turn the original autonomous-software-company brief into the eight-agent architecture, implement and test the FastAPI and React control plane, harden the live JSONL/diff/reviewer boundary, and keep the submission claims aligned with executable evidence. The public commit history and final Build Week session record should make that collaboration inspectable.

Inside the product, Codex performs the bounded implementation and independent review calls described above. Dhurandhar then converts their structured outputs into evidence-bearing company events; it does not display an unverified transcript as a completed SDLC run.

The completed in-product run is inspectable in [Live Codex evidence](docs/LIVE_EVIDENCE.md). Its implementation and review thread IDs are product provenance; they do not replace the separate Build Week `/feedback` session ID required below.

> [!CAUTION]
> **Submission blocker - required Codex collaboration evidence:** the primary Codex `/feedback` session ID has not been captured. Add the real session ID here and to the tagged release notes before submission. Do not invent or reuse an unrelated identifier.

## Deterministic judge/testing fallback

The deterministic fixture remains the no-secret fallback, not the hero story.

```bash
cp .env.example .env
docker compose down --volumes
docker compose up --build --detach --wait
curl -fsS http://localhost:8000/api/health
curl -fsS http://localhost:8000/api/objectives
curl -fsS http://localhost:8000/api/runs
curl -sS -o /tmp/dhurandhar-post.json -w '%{http_code}\n' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Must stay blocked"}' \
  http://localhost:8000/api/objectives
cat /tmp/dhurandhar-post.json
```

The health response reports `runtime` as `deterministic`, both GET collections return successfully, and the POST prints status `503` plus `{"detail":"mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured"}`. Open [http://localhost:8000](http://localhost:8000). The running fallback makes no model or external-service calls and writes no repository files. Change Replay labels its provenance `fixture`, reports zero model tokens, and must never be presented as GPT-5.5, GPT-5.6, or a live Codex run.

This path lets judges inspect the company roster, three-bid auction, ledger settlement, replay ordering, seeded recovery and policy evidence, and deterministic event chain without granting credentials.

Stop the fallback and remove its seeded test volumes before starting local development:

```bash
docker compose down --volumes
```

### Operator access and the public demo

Every mutation in Codex mode or a non-development deployment requires `DHURANDHAR_OPERATOR_TOKEN` with at least 16 characters. The Render blueprint and default Docker Compose stack deliberately omit that secret, so both are read-only replays: GET routes work, while objective, recovery, and policy-decision POSTs return `503` instead of mutating shared state.

For a controlled local recording, set the server-side token before starting the API, click the **Read-only** control in the top bar, and enter the same value. The browser keeps it only in the current React memory, sends it only in `X-Dhurandhar-Operator-Token` on mutation requests, and never writes it to storage, request bodies, or the event journal. **Forget token** or a page reload clears it.

## Local development

After completing [Prerequisites and installation](#prerequisites-and-installation), run the services from the repository root in separate terminals.

Terminal 1 (API):

```bash
source .venv/bin/activate
make dev-backend
```

Terminal 2 (frontend):

```bash
make dev-frontend
```

The frontend runs at [http://localhost:5173](http://localhost:5173), the API at [http://localhost:8000](http://localhost:8000), and health at [http://localhost:8000/api/health](http://localhost:8000/api/health).

Stop both development processes with `Ctrl-C` before running the verification commands below.

## Safety boundaries

The current implementation enforces:

- deterministic/read-only defaults and independent runtime/write flags;
- a Git worktree requirement before Codex workspace writes;
- no shell interpolation, a bounded prompt and timeout, and a reduced subprocess environment;
- no adapter commit, push, merge, external deploy, or general host-environment access;
- a separate read-only Codex review invocation;
- a real-diff plus successful-test-command gate for live promotion;
- append-only ordered events and SHA-256 previous-hash verification on every journal read;
- source references on durable memories and explicit run-linked transaction events;
- human approval after a deterministic structural policy-coverage check, explicitly scoped as non-efficacy evidence;
- explicit sandbox regression, liability, recovery, and rollback events.

The repository allowlist, protected-path, budget, GitHub, and automatic-merge variables in `.env.example` describe future adapter boundaries; the current local adapter does not enforce or perform those external operations. Treat all generated code as untrusted until independently reviewed and verified.

## Repository layout

```text
.
├── agents/                  Constitution and exact eight role contracts
├── backend/                 FastAPI company kernel, Codex adapter, ledger, and tests
├── frontend/                Vite control room and Change Replay UI
├── docs/
│   ├── ARCHITECTURE.md      Components, state machine, evidence, and trust model
│   ├── VISUAL_SPEC.md       UI behavior and visual contract
│   ├── FIDELITY_LEDGER.md   Concept-to-implementation comparison
│   ├── CLEAN_MACHINE_AUDIT.md  Dated pristine-clone command transcript
│   ├── SUBMISSION.md        Judge story, runbook, and last-mile checklist
│   └── design-concept.png   Design north star
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

## Verification

```bash
source .venv/bin/activate
make test       # backend and frontend tests
make lint       # available static checks
make build      # production frontend build
make docker     # production container build
```

CI runs backend compilation/tests, frontend lint/tests/build, and a container build without application secrets.

The dated [clean-machine README audit](docs/CLEAN_MACHINE_AUDIT.md) records the pristine-clone install, Docker read-only proof, local-service smoke test, build output, and audited commit.

## Project status

Dhurandhar is an OpenAI Build Week prototype. The repository contains a completed `gpt-5.5` live run with independently verifiable evidence. The repeated GPT-5.6 run, `/feedback` session ID, deployed demo, final video, and tagged release remain explicit submission blockers in [SUBMISSION.md](docs/SUBMISSION.md).

## License

[MIT](LICENSE) © 2026 Himanshu Jha.
