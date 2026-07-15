# Dhurandhar visual specification

This specification translates the design concept into an implementable UI contract. The product is a developer control plane, not an agent simulation.

![Dhurandhar Change Replay design concept](./design-concept.png)

## 1. Experience goal

Within ten seconds, a maintainer should be able to answer:

1. What objective is this run pursuing?
2. Which of the three engineers won the evidence-backed auction, and why?
3. Is the implementation live Codex evidence or a deterministic fixture?
4. Where is it in the delivery lifecycle?
5. Is the current state healthy, blocked, or awaiting approval?
6. What evidence supports the last consequential decision?
7. What did the run cost, and can it be stopped or recovered?

The interface should feel like a calm operations console: dense enough for engineering evidence, restrained enough that status remains legible during a three-minute demo.

## 2. Design north star

`docs/design-concept.png` is the visual north star for the hackathon build. It establishes:

- a dark, desktop-first command-center shell;
- a persistent left navigation rail;
- a compact global status and objective action bar;
- an ordered Change Replay timeline as the primary surface;
- a right evidence inspector tied to the selected event;
- an allocation and transaction ledger along the bottom;
- orange as the interaction accent, with semantic green, red, and amber statuses.

The implementation should preserve this information hierarchy even if spacing or component details change.

## 3. Product principles

### Evidence before personality

Show the exact persistent identity, role, action, status, and evidence. Do not add chat bubbles, simulated emotions, office metaphors, or celebratory “agent society” animations. Atlas, Forge, Prism, Rivet, Aegis, Sentinel, Shipwright, and Chronicle must not collapse into anonymous generic roles.

### One run, one causal story

The screen should make the lifecycle readable from top to bottom. A selected event explains why the next event occurred.

### Status must survive screenshots

Never encode status through color alone. Pair color with an icon and a concise label such as `Success`, `Blocked`, `Regression`, or `Proposed`.

### Measured cost, clearly labeled

Tokens are measured usage. Credits are internal allocation units. Place them near each other for comparison but never merge them into one number or imply monetary value.

### No hidden intervention

Human approval, cancellation, retry, or repair must appear as first-class timeline events.

## 4. Desktop layout

Target canvas: **1440 × 900** and larger. The reference image is wider; the layout must remain usable at the target size.

| Region | Target size | Content |
| --- | ---: | --- |
| Navigation | 192–200 px wide | Brand, Runs, Replay, Agents, Policies, Ledger, account/context switcher |
| Global header | 58–64 px high | Page title, kernel health, new-objective action |
| Run header | 132–150 px high | Objective, run ID, state, duration, interventions, token cost, playback controls |
| Timeline | Flexible, minimum 620 px wide | Ordered event rows and causal spine |
| Evidence inspector | 360–390 px wide | Rationale, evidence, artifact/diff, usage and credits |
| Bottom ledger | 210–230 px high | Agent balances and recent transactions |

The timeline owns the largest share of the screen. The ledger may collapse on shorter viewports, but the selected event inspector must remain available.

At widths below 1180 px, collapse navigation to icons and convert the inspector into an overlay drawer. Below 900 px, stack the inspector under the timeline. Mobile authoring is not a hackathon priority, but replay must remain readable.

## 5. Navigation and global header

### Navigation

Order:

1. Runs
2. Replay
3. Agents
4. Policies
5. Ledger

The active item uses a low-contrast filled surface and a 3 px orange leading indicator. Keep labels literal; avoid fictional department names.

### Kernel status

The global header displays one of:

- `Kernel online` — green dot;
- `Degraded` — amber triangle;
- `Read only` — neutral lock;
- `Offline` — red status icon.

The label opens a small panel with API health, storage health, adapter mode, and last event time. “Online” must not imply that repository writes are enabled.

### New objective

The MVP orange `New objective` button opens a focused form containing objective, context, line-separated acceptance criteria, and priority. Runtime/write mode is configured by the host so a browser action cannot silently expand authority.

The future repository adapter may extend the form with:

- objective;
- acceptance criteria;
- repository selection from the allowlist;
- live/fixture mode;
- budget ceiling;
- merge policy.

The final action summarizes consequences: `Start fixture run`, `Start read-only Codex run`, or `Start workspace-write run`. Branch and pull-request actions must not appear until corresponding adapters exist. Never use a generic `Go` label.

## 6. Change Replay

The API event discriminator is `type`. UI code must not rename it to `kind`; `kind` is reserved for explicitly nested evidence, artifact, ledger, file-change, and policy records.

### Run header

Display:

- objective as the dominant heading;
- copyable run ID;
- explicit terminal/current state;
- elapsed duration;
- number of human interventions;
- measured total tokens;
- provenance (`fixture` or `live`) and sandbox mode;
- configured implementation model and thread ID when present.

The state label uses sentence case. `Recovered` means a regression occurred and rollback or repair completed; it must not be styled as if no incident happened.

### Playback controls

Required controls:

- play/pause;
- stop/reset to first event;
- seek bar with elapsed and total run time;
- 10-second backward/forward controls;
- playback speed: 0.5×, 1×, 2×, 4×;
- keyboard: Space play/pause, arrows seek, Home/End first/last event.

Playback is a view operation. It must not rerun models, repeat writes, or mutate the run.

### Timeline row

Each row includes, in order:

1. stable sequence number;
2. causal spine marker;
3. wall-clock timestamp;
4. role icon and label;
5. concise action summary;
6. semantic status;
7. disclosure chevron.

Rows use monotonic event sequence, not timestamp sorting. The selected row receives an orange left edge and a slightly elevated surface. Keep every row at least 54 px high and keyboard-focusable.

Recommended semantic statuses:

| Status | Color | Icon | Meaning |
| --- | --- | --- | --- |
| Success | Green | Check in circle | Required transition completed |
| Active | Orange | Pulsing ring | Work is currently in progress |
| Blocked | Red | X in circle | Policy, review, or check prevents progress |
| Regression | Red | X in circle | Post-release health failed |
| Proposed | Amber | Warning triangle | Requires evaluation or approval |
| Cancelled | Neutral | Slash in circle | Intentionally terminated |

Animate only the active marker and playback cursor. Respect `prefers-reduced-motion`.

## 7. Evidence inspector

The inspector title describes the event, not the agent. Show timestamp and actor beneath it.

Section order:

1. **Provenance** — fixture/live, sandbox, agent, model, thread ID, token categories, and raw event count.
2. **Decision rationale** — two to five concise sentences; collapsed if lengthy.
3. **Evidence** — bid assessment, command exits, test checks, independent-review verdict and findings, sandbox promotion, or monitor signals.
4. **Artifact** — unified diff preview, changed files, numstat, diff SHA-256, file excerpt, or structured plan.
5. **Cost & credits** — measured model tokens and separately labeled credits charged, escrowed, paid, refunded, or penalized.

Evidence cards must display source type and stable identifier. Implementation and review thread IDs must remain visibly distinct. External links use an explicit external-link icon. Copy actions confirm success without a toast storm.

### Diff presentation

- monospace text at 12–13 px;
- file path and line range above code;
- red removed lines and green added lines with sufficient contrast;
- horizontal scrolling rather than wrapped code;
- display changed-file count, additions/deletions, full-diff SHA-256, and preview-truncated status above the preview;
- `Open in editor` only when a safe local link is available;
- never render unredacted secrets, environment values, or raw authorization headers.

The inspector’s empty state reads: `Select an event to inspect its evidence.`

## 8. Bottom ledger

The bottom region supports the run story but must not dominate it.

### Agent balances

Show all eight names, roles, stable color/icons, and current credit balances. Avoid leaderboards, medals, or game language. A zero balance may display `Dormant by policy`, not “bankrupt” as entertainment.

### Recent transactions

Columns:

- time;
- role;
- transaction type;
- factual description;
- measured tokens;
- internal credits.

A transaction opens the event that caused it. `View full ledger` navigates to a filterable, exportable table.

The current transaction vocabulary includes `issue`, `bid_fee`, `escrow`, `payout`, `refund`, and `penalty`. The interface must show both sides of a transfer so escrow and incident liability are understandable rather than decorative.

## 9. Supporting screens

### Runs

A table of objectives with run ID, repository, phase, health, elapsed time, tokens, intervention count, and last event. Default sort is most recent activity. Filters include status, repository, and mode.

### Agents

Show the exact eight-agent roster, role contract, capabilities, personality contract, current assignment, source-linked memory summary, measured usage, credits, and last event. The three engineers must show auction status (`bidding`, `working`, or `idle`) without implying that non-engineers may bid. Do not expose hidden chain-of-thought. “Rationale” means a concise, deliberately generated decision summary.

### Policies

Separate effective policy from proposals. Protected controls — repository allowlist, write mode, merge mode, budgets, and editable paths — require explicit approval and display who changed them.

### Ledger

Provide immutable event ordering, transaction filters, token/credit separation, CSV or JSON export, and links back to source events.

## 10. Visual tokens

Use CSS custom properties so semantic colors do not leak into component names.

```css
:root {
  --bg-canvas: #07141d;
  --bg-panel: #0b1a24;
  --bg-elevated: #12232e;
  --bg-selected: #1a2c37;
  --border-subtle: #263842;
  --text-primary: #f3f5f6;
  --text-secondary: #aeb9c0;
  --text-muted: #7f909a;
  --accent: #ff7a1a;
  --accent-hover: #ff8d3a;
  --success: #52df8b;
  --danger: #ff6659;
  --warning: #ffc342;
  --role-product: #b178ff;
  --role-engineer: #51dfa0;
  --role-reviewer: #ffc342;
  --role-qa: #62d7ff;
  --role-recovery: #6bc8ff;
  --role-history: #d49bff;
}
```

Color values may be tuned after contrast testing. Maintain at least WCAG AA contrast for text and interactive states.

### Typography

- UI: `Inter`, `Geist Sans`, or system sans-serif fallback.
- Evidence/code: `JetBrains Mono`, `IBM Plex Mono`, or system monospace fallback.
- Objective heading: 22–26 px, 600 weight.
- Page title: 20–24 px, 600 weight.
- Body: 14–15 px.
- Dense metadata: 12–13 px monospace.

Use tabular numerals for timestamps, tokens, durations, and balances.

### Shape and elevation

- 4–6 px radius for controls and evidence cards;
- 1 px borders provide most separation;
- shadows are subtle and reserved for overlays;
- avoid glassmorphism, gradients behind body text, and oversized rounded cards.

## 11. Loading, empty, and error states

- **Initial load:** render shell immediately, then skeleton rows; do not show fake events.
- **No runs:** explain fixture mode and offer `Load fixture replay` or `New objective` according to policy.
- **Disconnected stream:** preserve the last durable sequence and display reconnection state.
- **Evidence unavailable:** retain the event and state why evidence could not be loaded.
- **Write disabled:** show a persistent `Read only` indicator near any disabled state-changing action.
- **Budget reached:** mark the timeline event as blocked and show measured budget versus ceiling.

## 12. Accessibility and input

- all controls reachable by keyboard in visual order;
- visible 2 px focus ring using orange or a high-contrast neutral;
- semantic buttons rather than clickable divs;
- table headers and row labels for ledger data;
- `aria-live=polite` for newly received events, never for playback of historical rows;
- icons paired with accessible labels;
- minimum 40 × 40 px action targets;
- no essential hover-only evidence;
- reduced-motion mode disables cursor animation and smooth seeking.

## 13. Demo acceptance checklist

- [ ] At 1440 × 900, objective, playback, selected event, evidence, and cost are visible without browser zoom.
- [ ] The replay can be understood with audio muted.
- [ ] Reviewer block and post-release regression are visually distinct.
- [ ] Seeking does not reorder events or trigger side effects.
- [ ] Every highlighted claim links to source evidence and labels that evidence `live` or `fixture`.
- [ ] Human interventions appear in the timeline.
- [ ] Tokens and credits use distinct labels and data fields.
- [ ] Read-only and fixture modes are unmistakable.
- [ ] A live hero run shows model, implementation thread, reviewer thread, tokens, commands, changed files, diff, and verdict.
- [ ] All three engineer bids and the evidence-backed winner are visible.
- [ ] Sandbox promotion says `external_deployment: false` and is never narrated as a public deployment.
- [ ] Escaped-regression penalties identify the implementer, Aegis, Sentinel, and Shipwright.
- [ ] No secret or unredacted environment value appears in the inspector.
- [ ] The final frame clearly shows that Change Replay is Dhurandhar, while Misconception Debugger is the separate target worktree and Education submission.
