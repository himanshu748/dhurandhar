# Live Codex evidence

## Final Build Week run — 2026-07-16 (`gpt-5.6-sol`)

This is the final recorded live path for Dhurandhar. It used the exact authenticated catalog slug `gpt-5.6-sol` for a workspace-write implementation and a separate read-only review, then required Sentinel's own static-allowlist test command before internal sandbox promotion and settlement. A controlled regression subsequently exercised liability, known-good recovery, structural policy analysis, and the human decision gate.

### Run identity

- Objective: `Add privacy-safe session evidence export API`
- Objective ID: `obj_8f98814a95fb`
- Run ID: `run_8f98814a95fb`
- Target: fresh disposable Misconception Debugger worktree on branch `demo/dhurandhar-gpt56-sol-final-20260716-r1`
- Clean baseline commit: `3332982b5cdb8e2e697e63d0e30797134c307c06`
- Winner: Rivet
- Completed internal release: `v1.0.1` in `demo-sandbox`; `external_deployment` was `false`
- Final run state after the drill: `recovered`, healthy, with policy `policy_run_8f98814a95fb_1` still `proposed`

### Three-engineer auction

| Engineer | Bid | Credibility | Evidence score | Evidence citation | Eligible | Result |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Forge | 22 | 0.88 | 0.91 | `credibility:forge:seed` | No | Missing `containers` capability |
| Prism | 24 | 0.86 | 0.89 | `credibility:prism:seed` | No | Missing `containers` capability |
| Rivet | 24 | 0.89 | 0.92 | `credibility:rivet:seed` | Yes | Winner |

Forge, Prism, and Rivet each paid the recorded 1-credit participation fee. Atlas then locked the complete 40-credit objective budget in escrow before the runtime invocation.

### Codex provenance

| Stage | Exact model | Sandbox | Thread ID | Input | Cached input | Output | Reasoning output | Raw JSONL events |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Implementation | `gpt-5.6-sol` | `workspace-write` | `019f693d-e649-7a91-8dd3-f2cf1a772516` | 333,511 | 294,400 | 6,297 | 2,150 | 28 |
| Independent review | `gpt-5.6-sol` | `read-only` | `019f6940-61f5-7ea2-85e8-d20a1afaaf6f` | 361,206 | 315,904 | 3,566 | 2,103 | 21 |

Both events record `provenance: live`. The implementation records `write_mode: true`; the reviewer records `write_mode: false`, no diff, and no file changes. The release gate records the two distinct thread IDs, exact expected reviewer model, read-only status, and `eligible: true` with no reasons.

### Commands recorded from the implementation thread

The raw journal retains every complete command string. These are all seven implementation command events, in order:

| ID | Operation | Status | Exit |
| --- | --- | --- | ---: |
| `item_2` | `pwd` and bounded repository file listing with `rg --files` | completed | 0 |
| `item_3` | `git status --short` and inspection of `main.py`, `schemas.py`, `service.py`, and `db.py` | completed | 0 |
| `item_4` | Inspection of remaining database code, backend tests, fixtures, runtime tests, and `pyproject.toml` | completed | 0 |
| `item_6` | Evidence/aggregate search across README, docs, backend, and frontend; runtime inspection | completed | 0 |
| `item_10` | `pytest -q backend/tests/test_api.py -k 'session_evidence'` | completed | 0 |
| `item_12` | `pytest -q` | completed | 0 |
| `item_13` | `git diff --check`, `git status --short`, and bounded diff inspection | completed | 0 |

The implementation final message reported the new strict schemas, read-only SQL aggregation, service response construction, endpoint, and privacy-focused tests. It reported two focused tests and 13 tests in its full-suite invocation. Those model-thread commands are provenance, not Sentinel release evidence.

### Commands recorded from the reviewer thread

These are all eight reviewer command events, in order:

| ID | Operation | Status | Exit |
| --- | --- | --- | ---: |
| `item_1` | `pwd` and bounded agent/backend file listing | completed | 0 |
| `item_2` | `git status --short`, `git diff --check`, bounded full diff, and test-file inspection | completed | 0 |
| `item_3` | Inspection of changed application files, fixtures, and persistence/provenance references | completed | 0 |
| `item_4` | `pytest -q` | failed | 1 |
| `item_5` | Repository setup, dependency, README, and configuration inspection | completed | 0 |
| `item_6` | Focused source inspection, `git diff --numstat`, and `git diff --check` | completed | 0 |
| `item_7` | Read-only Python AST parsing plus Pydantic strict-schema inspection | completed | 0 |
| `item_8` | Focused runtime, database, and test line inspection | completed | 0 |

The reviewer returned the exact final object `{"verdict":"approved","findings":[]}`. Its failed model-thread pytest command is retained rather than hidden. Dhurandhar does not treat reviewer-declared commands as the release gate; Sentinel independently executed the trusted repository check after the approved, read-only verdict.

### Git change evidence

| File | Additions | Deletions | Binary |
| --- | ---: | ---: | --- |
| `backend/app/db.py` | 44 | 0 | No |
| `backend/app/main.py` | 12 | 0 | No |
| `backend/app/schemas.py` | 22 | 0 | No |
| `backend/app/service.py` | 23 | 0 | No |
| `backend/tests/test_api.py` | 125 | 0 | No |

- Total: 5 files, 226 insertions, 0 deletions.
- Diff SHA-256: `40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33`.
- Baseline was clean; empty status SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Baseline and post-run HEAD both remained `3332982b5cdb8e2e697e63d0e30797134c307c06`; the adapter did not commit or rewrite history.
- A post-run adapter recomputation reproduced the same five paths, complete numstat, and diff SHA-256.

### Independent Sentinel gate

Sentinel ignored the model-thread command claims and selected one repository-owned command from its static allowlist:

| Field | Recorded value |
| --- | --- |
| Allowlist ID | `backend-pytest` |
| Argv | `/opt/anaconda3/bin/python3.13 -m pytest -q` |
| Executor / source | `sentinel` / `static-allowlist` |
| Shell | `false` |
| Status / exit | `passed` / `0` |
| Stdout | 483 bytes; SHA-256 `e808f9e27f781515bf11c4fd490d7c7757ce086ef58c6d4a9582a6cad6d521d6` |
| Stderr | 0 bytes; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Raw command output is intentionally not persisted. Its byte count and digest are sealed by the event chain.

### Promotion and conserved settlement

Sentinel's accepted test event at sequence 57 causally preceded `deployment.started` at 59, internal `deployment.succeeded` at 60, and `monitor.healthy` at 61. All release events name `v1.0.1`; promotion remained inside `demo-sandbox` with `external_deployment: false`.

| Escrow release | Credits |
| --- | ---: |
| Rivet — winning implementation bid | 24 |
| Aegis — independent review | 5 |
| Sentinel — release verification | 5 |
| Shipwright — reversible promotion | 3 |
| Chronicle — monitored delivery account | 2 |
| Atlas — unused bounty refund | 1 |
| **Total released** | **40** |

The reconstructed ledger reports `conserved: true` and an escrow balance of zero.

### Recovery and human gate

The operator observed `/api/pulse` move from HTTP 200 to 503 and back to 200 while the journal recorded:

1. sequence 79: controlled regression `v1.0.1-regression.1`;
2. sequence 80: Sentinel alert with error rate `0.42` over threshold `0.01`;
3. sequences 81–84: penalties of 4 credits to Rivet, 3 to Aegis, 2 to Sentinel, and 2 to Shipwright;
4. sequences 85–86: rollback start and known-good restoration to `v1.0.1`;
5. sequence 87: source-linked incident analysis;
6. sequence 88: deterministic structural coverage only, explicitly `structure-only-not-efficacy`;
7. sequence 89: four-control proposal `policy_run_8f98814a95fb_1`.

The proposal remains `proposed`, `decided_at` is null, and there are no active mechanisms. This is the recorded proof that the autonomous run cannot approve its own policy change.

### Final raw journal

The append-only journal is stored at [`output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl`](../output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl).

- Chain verification: `valid: true`.
- Full journal events: 89; events linked to `run_8f98814a95fb`: 57.
- Chain head: `e0653356f2bb00f3b355344fc0474e71c4446856a5d696d2d2d589b6459df9a2`.
- Journal SHA-256: `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`.
- Secret scan found no local operator token, OpenAI key pattern, GitHub token pattern, or Render key pattern.

The failed 120-second rehearsal is not copied into the repository and is not used by any claim above.

## Historical development run — 2026-07-15 (`gpt-5.5`)

This is captured development evidence for Dhurandhar's hero path. It proves that the control plane invoked Codex to change a separate repository, captured the resulting Git diff, required an independent Codex reviewer, ran its own trusted test command, promoted only after the gates passed, and exercised a recoverable internal sandbox.

It is historical, not the final Build Week artifact. Both completed model calls recorded `gpt-5.5`; the separate final `gpt-5.6-sol` evidence is documented above.

### Historical run identity

- Objective: `Add privacy-safe session evidence export API`
- Objective ID: `obj_a39e0f892c1f`
- Run ID: `run_a39e0f892c1f`
- Target: disposable worktree of the separate Misconception Debugger repository
- Clean baseline commit: `3332982b5cdb8e2e697e63d0e30797134c307c06`
- Winning agent: Forge, selected from three evidence-backed engineering bids
- Internal release: `v1.0.1` in `demo-sandbox`; no external deployment was claimed

### Historical Codex provenance

| Stage | Model | Thread ID | Input | Cached input | Output | Reasoning output |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Implementation | `gpt-5.5` | `019f64e4-79ae-7161-8d15-739b5b57620a` | 943,703 | 882,560 | 7,597 | 1,642 |
| Independent review | `gpt-5.5` | `019f64e8-40e0-7962-b886-164b7bf305b7` | 166,593 | 128,896 | 1,710 | 778 |

The implementation ran with `workspace-write`; the reviewer ran read-only, used a distinct thread, produced no write evidence, and returned `approved` with no blocking finding.

### Historical change and verification

- Changed files: `README.md`, three backend application files, and two backend test files.
- Diff: 293 insertions and 1 deletion.
- Diff SHA-256: `11384f142672d0c342aab346a2e9ff9925a1ee698068d66edc83e85c3eff1cf2`.
- Baseline and post-run HEAD were identical, proving the adapter did not commit or rewrite history.
- Sentinel ignored the model's declared commands and independently executed the static, no-shell `python -m pytest -q` gate.
- Sentinel result: exit `0`; the target suite independently passed 16 tests.
- Captured stdout SHA-256: `1776e95184229560bd866aa226e920bacd82724290d18e30fd72b390acb32e06`.

### Historical recovery and human gate

After promotion, the controlled demo-sandbox pulse moved through:

1. `operational` / HTTP `200`;
2. injected regression and Sentinel alert;
3. `degraded` / HTTP `503`;
4. known-good rollback to `v1.0.1`;
5. `operational` / HTTP `200`.

The first generated improvement proposal overstated several prototype controls. The operator rejected it through the human decision gate as `human-truth-audit`; it was never activated. The implementation was then corrected so policy mechanisms describe executable internal controls and its score is a computed structural coverage check, not a claimed efficacy benchmark or traffic replay.

### Historical raw journal

The append-only journal is stored at [`output/evidence/codex-live-run-2026-07-15.jsonl`](../output/evidence/codex-live-run-2026-07-15.jsonl).

- Journal events: 90
- Journal SHA-256: `bcb6219ebb6f2aaa0e8c822428630d466f9923aef3a50bfc28932f91599c90ef`
- Secret scan: no operator token, OpenAI key, GitHub token, or cloud credential value is present.

The journal intentionally retains the rejected proposal: rejection is evidence that autonomous policy text is reviewable and cannot silently change the company.
