# Dhurandhar Build Week video shot list

This guide is tied to the committed 2026-07-16 event journal. It does not ask the
model to run again, alter the target worktree, or mutate the recorded evidence.
Target runtime: **2:55 with narration**.

## Recording setup: immutable live-run playback

Run these commands from the repository root. The first command creates a
read-only copy so the committed journal cannot be changed during recording.

```bash
install -m 0444 \
  output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl \
  /private/tmp/dhurandhar-gpt56-sol-video-replay.jsonl

shasum -a 256 \
  output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl \
  /private/tmp/dhurandhar-gpt56-sol-video-replay.jsonl
```

Both checksums must be exactly:

```text
cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5
```

Use the already validated production frontend and start only the safe playback
server:

```bash
npm --prefix frontend run build

env -u DHURANDHAR_OPERATOR_TOKEN \
  DHURANDHAR_ENV=production \
  DHURANDHAR_EVENT_LOG=/private/tmp/dhurandhar-gpt56-sol-video-replay.jsonl \
  DHURANDHAR_SEED_DEMO=false \
  DHURANDHAR_RUNTIME=deterministic \
  DHURANDHAR_ENABLE_CODEX_RUNTIME=false \
  DHURANDHAR_CODEX_APPLY_CHANGES=false \
  DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.6-sol \
  DHURANDHAR_REVIEWER_MODEL=gpt-5.6-sol \
  .venv/bin/uvicorn app.main:app --app-dir backend \
    --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Before recording, verify:

- the top bar says `Kernel online`, `LIVE`, and `gpt-5.6-sol`;
- the run title is `Add privacy-safe session evidence export API`;
- `GET /api/health` reports a valid 89-event chain;
- an unauthenticated `POST /api/objectives` returns `503`;
- the source and temporary journal checksums still match.

The health response correctly names the current viewer runtime as
`deterministic`: playback itself makes no model call. The live model, sandbox,
thread, and token fields displayed in Change Replay come from the immutable
captured events. Do not enable the Codex runtime, load an operator token, or say
that playback is a new model invocation. If the objective or top-bar provenance
does not match the checks above, stop; the UI may have fallen back to its fixture.

## Six required shots

### 1. Objective filed — 0:00–0:18

- **Navigate:** open Replay and press `Home`; the scrubber must show `01 / 38`.
- **Select:** `SEQ 033`, event `evt_fce40784e4ae67f1`.
- **Keep visible:** `Objective accepted`, the full objective title,
  `LIVE RUN · MODEL EVIDENCE`, and the loud live-journal provenance badge.
- **Proof:** this is the recorded `objective.created` event for objective
  `obj_8f98814a95fb` and run `run_8f98814a95fb`.
- **Narrate:** “Dhurandhar turns one bounded software objective into an auditable
  company run: allocation, implementation, independent review, verification,
  recovery, and learning.”

### 2. Three-bid auction and escrow — 0:18–0:42

- **Navigate:** select `SEQ 049`, scrubber position `12 / 38`.
- **Keep visible:** `Competitive implementation auction`,
  `3 bids · 40 CR bounty`, and all three cards.
- **Proof on screen:** Forge `22 CR`, credibility `0.88`; Prism `24 CR`,
  credibility `0.86`; Rivet `24 CR`, credibility `0.89`, with Rivet marked
  `selected`. Each card shows one evidence citation.
- **Economy proof:** show the three `bid fee −1 CR` movements and the
  `escrow −40 CR` movement beneath the cards.
- **Narrate:** “Forge, Prism, and Rivet all paid to bid. Forge and Prism were
  cheaper or tied but lacked the required container capability; Rivet was the
  lowest eligible bid, so Atlas locked the 40-credit bounty in escrow.”

The journal reports three bidders but only one eligible engineer. Do not claim
that all three were eligible.

### 3. Both live Codex boundaries — 0:42–1:20

First select implementation position `15 / 38`, `SEQ 052`, event
`evt_05a431a053b849c3`.

- **Keep visible:** `LIVE MODEL · gpt-5.6-sol · workspace-write` and the
  Evidence Inspector section `Live model provenance`.
- **Proof fields:** model `gpt-5.6-sol`, sandbox `workspace-write`, thread
  `019f693d-e649-7a91-8dd3-f2cf1a772516`, and token boxes
  `333,511 / 294,400 / 6,297 / 2,150` for input, cached, output, and reasoning.
- **Narrate:** “Codex used the authenticated `gpt-5.6-sol` tier in a bounded
  workspace-write session. Dhurandhar captured the exact thread, token
  categories, commands, files, and Git evidence.”

Then select review position `16 / 38`, `SEQ 055`, event
`evt_92a5b81af75de4a2`.

- **Keep visible:** `LIVE MODEL · gpt-5.6-sol · read-only`.
- **Proof fields:** the distinct thread
  `019f6940-61f5-7ea2-85e8-d20a1afaaf6f` and token boxes
  `361,206 / 315,904 / 3,566 / 2,103`.
- **Narrate:** “Aegis invoked Codex again on the same exact tier, but in a
  separate read-only thread. The implementing session cannot approve itself.”

The top bar reflects the latest model boundary and therefore says `read-only`.
Use the selected implementation card or inspector—not the top bar—to prove the
implementation sandbox was `workspace-write`.

### 4. Diff evidence and independent verdict — 1:20–1:48

- **Navigate:** return to `SEQ 052` for the diff, then advance to `SEQ 055`.
- **Diff proof:** show `5 changed files`, `+226 −0`, the five paths, the diff
  preview, and SHA-256
  `40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33`.
- **Review proof:** show `AEGIS APPROVED`, `independent verdict`, and final
  message `{"verdict":"approved","findings":[]}`.
- **Narrate:** “The write is proved by Git metadata computed outside the model.
  Aegis then returned a structured approval from an independent read-only
  thread.”

Raw event `evt_425a2b5f2e86d522` at sequence 53 corroborates the repository
evidence but is intentionally bridged by the cinema view; the visible sequence
52 card already contains the complete diff. One retained reviewer-side
`pytest -q` command exited `1`, so do not say every reviewer command passed.
Sentinel's separate gate in the next shot is the release authority.

### 5. Sentinel, internal promotion, and conserved settlement — 1:48–2:18

- **Navigate:** select `SEQ 057`, scrubber position `17 / 38`.
- **Gate proof:** show `SENTINEL RELEASE GATE PASSED`, `1 executable check`,
  `/opt/anaconda3/bin/python3.13 -m pytest -q`, and `EXIT 0`.
- **Hash proof:** the retained stdout SHA-256 is
  `e808f9e27f781515bf11c4fd490d7c7757ce086ef58c6d4a9582a6cad6d521d6`.
- **Promotion proof:** briefly select `SEQ 060`; show `demo-sandbox` and
  `external_deployment: false` in the event evidence.
- **Settlement proof:** select `SEQ 067`, position `26 / 38`. Keep the ledger
  badge `CONSERVED · 40/40 CR` visible while the payouts settle: Rivet 24,
  Aegis 5, Sentinel 5, Shipwright 3, Chronicle 2, and Atlas refund 1.
- **Narrate:** “Sentinel—not the reviewer—ran the static-allowlist release test
  with a real exit code of zero. Shipwright promoted only to the reversible
  demo sandbox, never to external infrastructure, and all 40 escrow credits are
  visibly conserved.”

### Safety bridge: recovery and human authority — 2:18–2:40

- **Navigate:** advance from `SEQ 079` through `SEQ 089`.
- **Keep visible:** `Regression containment`, `4 liability entries / 11 cr`,
  the known-good restore, and the final human gate.
- **Proof:** the terminal UI must say
  `The company cannot promote this policy itself.` and `Awaiting decision`.
- **Narrate:** “A controlled regression assigns liability across implementation,
  review, QA, and release, restores the known-good sandbox, and proposes four
  runtime-backed controls. Only a human can activate them.”

Do not click Approve. The recorded proposal must remain `proposed`.

### 6. Public read-only demo — 2:40–2:55

- **Navigate:** open
  [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com).
- **Keep visible:** top-bar `FIXTURE`, `MODEL none`, and `MODE read-only`; run
  header `FIXTURE · DETERMINISTIC FALLBACK`; a card badge
  `FIXTURE · DETERMINISTIC`; and the inspector label `NO MODEL CALL`.
- **Proof:** the public instance serves objective `obj_seed_self_hosting_v1`, run
  `run_seed_self_hosting_v1`, and a valid 78-event chain. Its exact health
  response is:

```json
{"status":"ok","service":"Dhurandhar API","version":"0.1.0","event_chain_valid":true,"events":78,"runtime":"deterministic"}
```

- **Narrate:** “The deployed Render URL is an intentionally read-only,
  no-secret deterministic replay for judges. It proves the product is
  accessible; the earlier immutable local replay is the evidence for the two
  real Codex `gpt-5.6-sol` calls.”

The hosted service is live, but its model evidence is fixture-backed. Never call
the hosted replay a live model run.

## Final audio checklist

The narration must say all of the following explicitly:

- Codex collaborated on building Dhurandhar, with primary collaboration session
  ID `019f6172-596f-7d50-a842-b839fd16af3e` recorded in the repository.
- Inside Dhurandhar, Codex made two distinct calls using exact tier
  `gpt-5.6-sol`: one workspace-write implementation and one read-only review.
- Sentinel independently supplied the release-gating `EXIT 0` evidence.
- Promotion was internal to `demo-sandbox`; no external deployment was claimed.
- The Render deployment is a deterministic, read-only judge fallback with no
  model call.

End on: “Dhurandhar does not ask you to trust an agent transcript. It shows who
did what, which evidence allowed the next step, what failure cost, and exactly
where the human still decides.”
