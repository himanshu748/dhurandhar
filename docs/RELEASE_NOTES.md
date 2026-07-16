# Dhurandhar v1.0.0 release notes — draft

> This draft is not a tagged release. The video URL and cover image remain pending; the release gates and current public-link audit are complete.

## Build Week evidence

- Primary Codex collaboration session ID: `019f6172-596f-7d50-a842-b839fd16af3e`.
- Live implementation: `gpt-5.6-sol`, thread `019f693d-e649-7a91-8dd3-f2cf1a772516`, `workspace-write`.
- Independent review: `gpt-5.6-sol`, thread `019f6940-61f5-7ea2-85e8-d20a1afaaf6f`, read-only, verdict `approved`.
- Full evidence: [Live Codex evidence](LIVE_EVIDENCE.md).
- Chain-verifiable final journal: [`output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl`](../output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl).
- Verified public demo: [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com).
- Source repository: [https://github.com/himanshu748/dhurandhar](https://github.com/himanshu748/dhurandhar).
- Render deployment: Blueprint `exs-d9c6rmm1a83c73bsov5g`, service `srv-d9c6rt3tqb8s73agu030`, deploy `dep-d9c821vavr4c73airodg`, source commit `e1c689b1033b476e560a18c78425859726044d87`.
- Recording guide: [Evidence-based video shot list](VIDEO_SHOT_LIST.md).

## Release validation

Version scopes are separate: the API currently reports `0.1.0`, this repository
release is drafted as `v1.0.0`, and the captured internal demo-sandbox artifact
is `v1.0.1`.

- Backend: 66 tests passed.
- Frontend: 6 test files and 23 tests passed.
- Backend compilation, available lint checks, TypeScript validation, and the Vite production build passed.
- The production Docker image built successfully, and its release-container smoke test verified health, objectives, runs, replay, frontend HTML, and fail-closed `503` mutation behavior.
- The final journal independently verified at 89 events with head `e0653356f2bb00f3b355344fc0474e71c4446856a5d696d2d2d589b6459df9a2` and file checksum `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`.

## Release highlights

- Eight persistent agents coordinate a real three-engineer auction, implementation, independent review, verification, internal promotion, monitoring, recovery, and human-gated learning.
- Change Replay exposes exact model/thread provenance, four token categories, commands, file changes, full numstat, diff hash, review findings, Sentinel exit evidence, ledger settlement, and recovery causality.
- The final `gpt-5.6-sol` run produced a five-file, 226-insertion diff, passed Sentinel's independent static-allowlist gate, conserved the complete 40-credit escrow, restored the known-good sandbox after a controlled regression, and stopped at an unapproved policy proposal.
- The verified public deployment is an intentionally read-only deterministic replay; it must not be presented as the live model run.
