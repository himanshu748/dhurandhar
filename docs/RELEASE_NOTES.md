# Dhurandhar v1.0.0 release notes

> The final video and cover image are published. The automated release gates passed on 2026-07-19.

## Build Week evidence

- Primary Codex collaboration session ID: `019f6172-596f-7d50-a842-b839fd16af3e`.
- Live implementation: requested `gpt-5.6-sol` through `--model`; stream-derived thread `019f693d-e649-7a91-8dd3-f2cf1a772516`; `workspace-write`.
- Independent review: requested `gpt-5.6-sol` through `--model`; stream-derived thread `019f6940-61f5-7ea2-85e8-d20a1afaaf6f`; read-only; verdict `approved`.
- Model limitation: the historical `codex exec --json` stdout did not echo a model identifier. The journal model value is the requested slug accepted by the CLI, not an observed stream field. The journal was not backfilled. Future runs record requested/nullable-observed model, full invocation argv, and `codex --version`, and fail closed on model conflict or mismatch.
- Full evidence: [Live Codex evidence](LIVE_EVIDENCE.md).
- Chain-verifiable final journal: [`output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl`](../output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl).
- Verified public judge URL: [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com).
- Source repository: [https://github.com/himanshu748/dhurandhar](https://github.com/himanshu748/dhurandhar).
- Demo video: [https://youtu.be/FFN0SHpwWFQ](https://youtu.be/FFN0SHpwWFQ) (2:58).
- Cover image: [SEQ 052 implementation evidence](assets/dhurandhar-build-week-cover.png) (1920x1080).
- Render source commit: `55aae7648c2357ae9679ecd5523fb61556a16b0d`; deployment: `dep-d9c9drjbc2fs73bipqqg` (`live` at 2026-07-16T08:32:41Z). Earlier seeded-fixture deployments are not release evidence for this 89-event playback.
- Recording guide: [Evidence-based video shot list](VIDEO_SHOT_LIST.md).

## Release validation

Version scopes are separate: the API currently reports `0.1.0`, this repository
release is tagged as `v1.0.0`, and the captured internal demo-sandbox artifact
is `v1.0.1`.

- Backend/frontend tests, Python compilation, TypeScript lint, production build, Blueprint validation, and the adversarial Docker smoke all passed on the hardened release candidate. On 2026-07-19, the final `make test`, `make lint`, `make build`, and `make submission-check` gates passed after media integration; the submission guard reported no release blockers. The Makefile's optional Ruff branch reported that Ruff was not installed and skipped that additional check.
- Required Docker/public behavior: `/` and `/replay` serve, GET routes remain readable, health verifies the immutable 89-event chain under `runtime: deterministic`, and unauthenticated mutation remains fail-closed with `503`.
- The final journal independently verified at 89 events with head `e0653356f2bb00f3b355344fc0474e71c4446856a5d696d2d2d589b6459df9a2` and file checksum `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`.

## Release highlights

- Eight persistent agents coordinate a real three-engineer auction, implementation, independent review, verification, internal promotion, monitoring, recovery, and human-gated learning.
- Change Replay exposes requested-model and stream-derived thread/token provenance, commands, file changes, full numstat, diff hash, review findings, Sentinel exit evidence, ledger settlement, and recovery causality.
- The final run requested `gpt-5.6-sol` for both Codex boundaries, produced a five-file, 226-insertion diff, passed Sentinel's independent static-allowlist gate, conserved the complete 40-credit escrow, restored the known-good sandbox after a controlled regression, and stopped at an unapproved policy proposal.
- The release target is an intentionally read-only deterministic playback of that committed 89-event journal. It executes no new model calls and must not be presented as a new live model run. The separate seeded-fixture mode remains synthetic and distinct.
