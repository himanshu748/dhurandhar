# Dhurandhar visual fidelity ledger

Compared on 2026-07-15 at the 1440 × 900 implementation target.

- Concept: [`design-concept.png`](./design-concept.png)
- Existing implementation capture: [`../output/playwright/dhurandhar-desktop-1440x900.png`](../output/playwright/dhurandhar-desktop-1440x900.png)

> [!NOTE]
> The existing capture is a UI/fidelity artifact from the deterministic API-driven flow. It is not evidence of a Codex invocation, GPT-5.5 or GPT-5.6 use, a public deployment, or the final submission recording. Replace it with a release-candidate capture after the live hero run.

| Comparison point | Concept intent | Implemented result | Disposition |
| --- | --- | --- | --- |
| Command-center shell | Fixed left rail, compact global header, timeline center, inspector right, ledger across the bottom | The five-region shell is preserved. At desktop size, replay owns the primary area while the evidence inspector and ledger remain visible. | Match |
| Visual language | Graphite/blue-black surfaces, hairline borders, orange interaction accent, semantic green/red/amber | CSS tokens reproduce the palette and status roles. Status includes an icon and label, not color alone. | Match |
| Causal replay | Dense numbered rows connected by a causal spine, with one selected event | Hash-chained events render in sequence order. The timeline includes planning, three bids, implementation, review, tests, sandbox promotion, ledger, memory, recovery, and policy events. | Match with real-data extension |
| Exact company | Stable agent identities and balances | The Agents surface exposes Atlas, Forge, Prism, Rivet, Aegis, Sentinel, Shipwright, and Chronicle with role, capability, memory, balance, and activity. | Product-specific extension |
| Auction | Allocation should be understandable before implementation | Forge, Prism, and Rivet each produce an evidence-backed bid; the replay shows eligibility, fees, escrow, winner, and settlement. | Product-specific extension |
| Evidence inspector | Decision rationale, evidence, artifact/diff, and separate cost/credit accounting | Fixture events are labeled as such. Live-capable events expose model, implementation/reviewer thread, token categories, commands, files, Git diff metadata, verdict, and final message when present. | Stronger evidence contract |
| Recovery story | Monitor failure, repair or rollback, then proposed policy | The API-driven deterministic drill appends a controlled sandbox regression, alert, four liability penalties, known-good restoration, benchmark, and human-gated proposal. It does not claim external production recovery. | Match with honest sandbox boundary |
| Bottom ledger | Agent balances plus recent source-linked transactions | Balances and issue, bid-fee, escrow, payout, refund, and penalty transactions are backed by the API ledger. Model tokens and credits remain separate. | Match |
| Brand and navigation | Dhurandhar mark plus Runs, Replay, Agents, Policies, and Ledger | The same literal navigation and brand hierarchy are implemented with accessible controls and current-page state. | Match |
| Objective action | High-contrast orange primary action | `New objective` opens a modal with objective, context, line-separated acceptance criteria, and priority. Runtime and configured worktree remain host-controlled. | Deliberate safety boundary |
| Run density | Curated proof events visible in one frame | Real runs contain roster, memory, auction, evidence, and settlement events, so the timeline scrolls independently and can filter to consequential evidence. | Deliberate truth-over-curation delta |
| Responsive behavior | Desktop first; collapse rail and stack inspector below 900 px | Existing captures cover 900 × 900 and 390 × 844. The rail collapses, the inspector stacks, and the narrow layout avoids document overflow. | Match |

## Verification notes

- Existing desktop capture: 1440 × 900, deterministic FastAPI data.
- Existing responsive captures: 900 × 900 and 390 × 844.
- The generated concept is a visual north star, not a screenshot of product behavior.
- A new capture is required after the final live Codex implementation/reviewer run.
- The final evidence inspector must visibly show live provenance, model, two distinct thread IDs, tokens, commands, files, diff, and reviewer verdict.
- The final video must state that `demo-sandbox` promotion is not external deployment.
