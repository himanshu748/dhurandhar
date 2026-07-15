# Live Codex evidence — 2026-07-15

This is captured development evidence for Dhurandhar's hero path. It proves that the control plane invoked Codex to change a separate repository, captured the resulting Git diff, required an independent Codex reviewer, ran its own trusted test command, promoted only after the gates passed, and exercised a recoverable internal sandbox.

It is **not** the final Build Week GPT-5.6 artifact. Both completed model calls recorded `gpt-5.5`; repeat the run with GPT-5.6 after account access is available.

## Run identity

- Objective: `Add privacy-safe session evidence export API`
- Objective ID: `obj_a39e0f892c1f`
- Run ID: `run_a39e0f892c1f`
- Target: disposable worktree of the separate Misconception Debugger repository
- Clean baseline commit: `3332982b5cdb8e2e697e63d0e30797134c307c06`
- Winning agent: Forge, selected from three evidence-backed engineering bids
- Internal release: `v1.0.1` in `demo-sandbox`; no external deployment was claimed

## Codex provenance

| Stage | Model | Thread ID | Input | Cached input | Output | Reasoning output |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Implementation | `gpt-5.5` | `019f64e4-79ae-7161-8d15-739b5b57620a` | 943,703 | 882,560 | 7,597 | 1,642 |
| Independent review | `gpt-5.5` | `019f64e8-40e0-7962-b886-164b7bf305b7` | 166,593 | 128,896 | 1,710 | 778 |

The implementation ran with `workspace-write`; the reviewer ran read-only, used a distinct thread, produced no write evidence, and returned `approved` with no blocking finding.

## Change and verification

- Changed files: `README.md`, three backend application files, and two backend test files.
- Diff: 293 insertions and 1 deletion.
- Diff SHA-256: `11384f142672d0c342aab346a2e9ff9925a1ee698068d66edc83e85c3eff1cf2`.
- Baseline and post-run HEAD were identical, proving the adapter did not commit or rewrite history.
- Sentinel ignored the model's declared commands and independently executed the static, no-shell `python -m pytest -q` gate.
- Sentinel result: exit `0`; the target suite independently passed 16 tests.
- Captured stdout SHA-256: `1776e95184229560bd866aa226e920bacd82724290d18e30fd72b390acb32e06`.

## Recovery and human gate

After promotion, the controlled demo-sandbox pulse moved through:

1. `operational` / HTTP `200`;
2. injected regression and Sentinel alert;
3. `degraded` / HTTP `503`;
4. known-good rollback to `v1.0.1`;
5. `operational` / HTTP `200`.

The first generated improvement proposal overstated several prototype controls. The operator rejected it through the human decision gate as `human-truth-audit`; it was never activated. The implementation was then corrected so policy mechanisms describe executable internal controls and its score is a computed structural coverage check, not a claimed efficacy benchmark or traffic replay.

## Raw journal

The append-only journal is stored at [`output/evidence/codex-live-run-2026-07-15.jsonl`](../output/evidence/codex-live-run-2026-07-15.jsonl).

- Journal events: 90
- Journal SHA-256: `bcb6219ebb6f2aaa0e8c822428630d466f9923aef3a50bfc28932f91599c90ef`
- Secret scan: no operator token, OpenAI key, GitHub token, or cloud credential value is present.

The journal intentionally retains the rejected proposal: rejection is evidence that autonomous policy text is reviewable and cannot silently change the company.
