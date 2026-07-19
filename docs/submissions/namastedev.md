<!-- DRAFT: You must rewrite this in your own voice before submitting because Devpost warns that judges can recognize AI-written descriptions. -->

# Dhurandhar

**Track:** AI Agents

## Try it now

**Live URL:** [https://dhurandhar-asc.onrender.com](https://dhurandhar-asc.onrender.com)

Click **Change Replay**, scrub through the 89-event timeline and open any selected event's evidence. Then try a public mutation:

```bash
curl -i -sS -H 'Content-Type: application/json' \
  -d '{"title":"Must stay blocked"}' \
  https://dhurandhar-asc.onrender.com/api/objectives
```

It returns `503` with `{"detail":"mutations are disabled until DHURANDHAR_OPERATOR_TOKEN is configured"}`.

## Problem

Autonomous coding systems can generate patches, but allocation, proof, release gates and recovery can remain hard to inspect.

## Solution

Dhurandhar is an eight-agent control plane that turns those decisions into append-only, hash-linked events with persistent identities, internal credits and human authority over policy activation.

## Flow

Atlas scopes an objective. Forge, Prism and Rivet bid. The winner implements through Codex, Aegis reviews in a separate read-only call, Sentinel runs an allowlisted test, Shipwright records internal promotion and Chronicle preserves the account. A controlled regression then records liability, restores the known-good sandbox and stops at a human policy decision.

## Economy story

Atlas opened a `40 CR` bounty. Forge bid `22 CR` but was ineligible for missing `containers`; Prism bid `24 CR` but was ineligible for missing `containers`; Rivet bid `24 CR` and was eligible. Each bidder paid a `1 CR` participation fee. The lowest eligible bid wins, so Rivet won and Atlas locked `40 CR` in escrow.

Settlement conserved all 40 CR: Rivet `24`, Aegis `5`, Sentinel `5`, Shipwright `3`, Chronicle `2` and Atlas refund `1`. Controlled-regression liability was Rivet `4`, Aegis `3`, Sentinel `2` and Shipwright `2`.

## Compressed evidence

- Implementation requested `gpt-5.6-sol`, used `workspace-write` and ran in thread `019f693d-e649-7a91-8dd3-f2cf1a772516`.
- Independent review requested the same slug, used `read-only` and ran in thread `019f6940-61f5-7ea2-85e8-d20a1afaaf6f`.
- The diff was 5 files with `+226/-0`; SHA-256 `40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33`.
- The reviewer-side `pytest -q` failure with exit `1` is preserved. Sentinel's later static-allowlist pytest exited `0`.
- The 89-event journal SHA-256 is `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`.

Source: [GitHub](https://github.com/himanshu748/dhurandhar). Demo: [2:58 video](https://youtu.be/FFN0SHpwWFQ).

## Honest boundaries

The public site is deterministic, read-only playback and makes no new model calls. The model slug was requested and CLI-accepted, not stream-observed. Promotion was internal and reversible in `demo-sandbox` with `external_deployment: false`. The four-control policy is still `proposed` and requires a human decision.
