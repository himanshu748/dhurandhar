<!-- DRAFT: You must rewrite this in your own voice before submitting because Devpost warns that judges can recognize AI-written descriptions. -->

# Dhurandhar

**Category:** Developer Tools

## What it is

Dhurandhar turns a bounded software objective into an auditable company run across eight persistent agents. It auctions work, invokes Codex, reviews the diff, verifies tests, promotes to an internal sandbox, monitors the result and records recovery with a human policy gate.

## Problem

Agent demos often ask judges to take generated work on trust. Dhurandhar replaces that trust with receipts for allocation, independent review, release evidence and post-failure accountability.

## How Codex and GPT-5.6 were used

Inside the product, Dhurandhar ran Codex CLI headlessly for a scoped `workspace-write` implementation, then made a separate `read-only` review call. Both calls requested `gpt-5.6-sol`: implementation thread `019f693d-e649-7a91-8dd3-f2cf1a772516` and reviewer thread `019f6940-61f5-7ea2-85e8-d20a1afaaf6f`.

Codex also collaborated on the Dhurandhar build across architecture, implementation, testing and claim review. The primary collaboration session ID is `019f6172-596f-7d50-a842-b839fd16af3e`.

## Verifiable evidence

- The captured journal has 89 SHA-256-chained events; its file checksum is `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`.
- The kernel computed a 5-file, `+226/-0` diff from Git; its SHA-256 is `40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33`.
- The reviewer returned `approved`, while its reviewer-side `pytest -q` failure with exit `1` remains in the evidence. Sentinel later ran the repository-owned static-allowlist pytest and exited `0`.
- Settlement conserved the 40 CR escrow: `24/5/5/3/2/refund 1`.

## How judges test it

Open the [live demo](https://dhurandhar-asc.onrender.com), click Change Replay and scrub the recorded run. Health reports deterministic runtime, 89 events and a valid chain. An unauthenticated objective mutation returns `503`. The [repository](https://github.com/himanshu748/dhurandhar) contains the journal, evidence document and verification commands; the [video](https://youtu.be/FFN0SHpwWFQ) is 2:58. For a mutable run, complete the documented prerequisites, then use the README's live-runtime command and runbook with your own authenticated Codex CLI.

## Honest limitations

The public site is deterministic, read-only playback of the committed historical live journal and makes no new model call. `gpt-5.6-sol` was the requested slug accepted by the CLI, but it was not stream-observed. Promotion was internal and reversible in `demo-sandbox` with `external_deployment: false`; the policy remains proposed for a human decision.
