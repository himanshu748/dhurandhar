# Clean-machine README audit

- **Audit date:** 2026-07-15
- **Audited commit:** `a9f56bc8d5f91edb15a04611df6de3d9a59b73a1`
- **Source:** fresh clone of `agent/finalize-dhurandhar` from `https://github.com/himanshu748/dhurandhar.git` into a new `/tmp` directory
**Result:** pass for the documented prerequisites/install, deterministic Docker fallback, Make-based local development, verification, and fail-closed release guard

The audit used the README commands in their published order and did not reuse this repository's virtual environment, `node_modules`, event volumes, or build output. The clone remained clean according to `git status --short`; generated environments and build artifacts are intentionally ignored.

## Audit environment

| Tool | Observed version | Documented floor |
| --- | --- | --- |
| Python | `3.13.5` | `3.12+` |
| Node.js | `22.22.3` in the audit shell | `22.13+` |
| npm | `11.6.0` | npm required |
| GNU Make | `3.81` | GNU Make required |
| Docker | `29.5.3` | Docker Engine/Desktop required |
| Docker Compose | `v5.1.4` | Compose v2 with `up --wait` support |

## Full command transcript

### 1. Remote provenance

```bash
git clone --branch agent/finalize-dhurandhar --single-branch \
  https://github.com/himanshu748/dhurandhar.git \
  /tmp/dhurandhar-clean-audit.uHinmj/remote-a9f56bc
cd /tmp/dhurandhar-clean-audit.uHinmj/remote-a9f56bc
git status --short
git rev-parse HEAD
```

Result: clone succeeded; `git status --short` printed nothing; `git rev-parse HEAD` printed the audited commit above.

### 2. Prerequisites and fresh install

```bash
python --version
node --version
docker compose version
python -m venv .venv
source .venv/bin/activate
make install
```

Observed output:

```text
Python 3.13.5
v22.22.3
Docker Compose version v5.1.4
python -m pip install -r backend/requirements-dev.txt
Successfully installed ... pytest-8.4.2 ...
cd frontend && npm ci
added 169 packages ...
found 0 vulnerabilities
```

The first `make install` attempt was intentionally made in the default network-isolated audit sandbox and reached the correct `backend/requirements-dev.txt` file, then failed because registry DNS was blocked. Repeating the same command in the same fresh virtual environment with scoped outbound package-registry access exited `0`. No package or command was added manually.

Immediate post-install verification:

```bash
make test
```

Result: exit `0`; 66 backend tests passed and 6 frontend files / 23 frontend tests passed on the cold install.

### 3. Deterministic Docker fallback

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

Observed health response:

```json
{"status":"ok","service":"Dhurandhar API","version":"0.1.0","event_chain_valid":true,"events":78,"runtime":"deterministic"}
```

Both GET collections returned the seeded objective/run with HTTP `200`. The mutation probe printed:

```text
503
{"detail":"mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured"}
```

This was run after copying `.env.example`; Compose still resolved `DHURANDHAR_ENV=production`, `DHURANDHAR_RUNTIME=deterministic`, seeding enabled, both Codex gates disabled, and no operator-token entry. That specifically proves the README path cannot silently become mutable because `.env.example` contains a local-development environment value.

```bash
docker compose down --volumes
```

Result: exit `0`; the isolated container, network, and both audit volumes were removed.

### 4. Local development Make targets

Terminal 1:

```bash
source .venv/bin/activate
make dev-backend
```

Terminal 2:

```bash
make dev-frontend
```

Observed startup:

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete.
VITE v8.1.4 ready
Local: http://localhost:5173/
```

Smoke probes used while both documented commands were running:

```bash
curl -fsS http://localhost:8000/api/health
curl -fsS http://localhost:5173/
curl -fsS http://localhost:5173/api/health
```

Result: all exited `0`; the frontend returned the Dhurandhar HTML shell and its Vite proxy returned the same healthy deterministic API payload. Both processes then stopped cleanly with `Ctrl-C` as the README instructs.

The restricted runner initially denied Uvicorn's reload watcher and Vite's localhost bind. The exact Make targets passed when granted scoped host watcher/port permission; no code, flag, or undocumented startup command was substituted.

### 5. Verification section

```bash
source .venv/bin/activate
make test
make lint
make build
make docker
```

Results:

| Command | Exit | Evidence |
| --- | ---: | --- |
| `make test` | `0` | 66 backend tests; 6/6 frontend files and 23/23 tests |
| `make lint` | `0` | backend byte-compilation and frontend `tsc --noEmit`; optional Ruff check reported not installed and skipped as designed |
| `make build` | `0` | Vite production build completed; app chunk `99.88 kB` raw, React and GSAP split into vendor chunks, recovery/secondary views emitted as lazy chunks |
| `make docker` | `0` | production image `dhurandhar:local` built successfully |

Production build chunk evidence:

```text
RecoveryFlow-CFS4YOVp.js       6.47 kB
SecondaryView-D2AHp62H.js      8.07 kB
index-CX98k20Y.js             99.88 kB
vendor-gsap-vTK-RkEg.js      137.39 kB
vendor-react-DieaS26h.js     189.65 kB
```

## Additional release checks

```bash
make submission-check
```

Result: intentionally failed with the 14 currently open release blockers: one missing collaboration-session identifier, three historical-model README claims that must be refreshed after the final model run, and ten unchecked pre-tag evidence/publishing items. The release/tag instructions put this guard before tag creation, so the repository cannot truthfully report release readiness yet.

Static consistency checks also passed:

- `backend/pyproject.toml` declares Python `>=3.12`;
- its three runtime dependencies match `backend/requirements.txt` exactly and in order;
- `.env.example` contains one GPT-5.6 migration-gate comment while both completed-evidence defaults remain unchanged;
- the requested docs and TypeScript types use `type` as the replay-event discriminator, with `kind` only in explicitly nested records;
- `docker compose config` resolves production/read-only deterministic mode even with the copied README `.env` file.

## Browser smoke evidence

The same frontend revision was also exercised in the in-app browser against the production container at 1280px or wider. The fixture/read-only provenance was visible, **New objective** was disabled, the lazy-loaded **Agents** route rendered the eight-agent company, and the browser console contained no warnings or errors.

## Scope boundary

The deterministic/read-only judge path and local development path are fully reproduced above. The separate live Codex hero run is deliberately not represented as part of this no-secret audit: it requires an authenticated Codex CLI, a disposable Misconception Debugger worktree, a configured operator token, and the still-open final-model evidence. `make submission-check` correctly keeps those release claims blocked.
