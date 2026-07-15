# Dhurandhar visual fidelity ledger

Compared on 2026-07-14 at the 1440 × 900 implementation target.

- Concept: [`design-concept.png`](./design-concept.png)
- Implementation capture: [`../output/playwright/dhurandhar-desktop-1440x900.png`](../output/playwright/dhurandhar-desktop-1440x900.png)

| Comparison point | Concept intent | Implemented result | Disposition |
| --- | --- | --- | --- |
| Command-center shell | Fixed left rail, compact global header, timeline center, inspector right, ledger across the bottom | The same five-region shell is preserved. At desktop size the ledger spans the full bottom edge and the owner context sits directly above it. | Match |
| Visual language | Graphite/blue-black surfaces, hairline borders, orange interaction accent, semantic green/red/amber | CSS tokens reproduce the palette and status roles. Status always includes an icon and label, not color alone. | Match |
| Causal replay | Dense, numbered rows connected by a causal spine, with one selected event | Real hash-chained events render in sequence order. The selected policy event gets an orange edge and elevated surface; the timeline scrolls independently to keep long runs usable. | Match with real-data extension |
| Evidence inspector | Decision rationale, evidence, artifact/diff, and separate cost/credit accounting | All four sections are present and update with the selected event. API artifacts use structured JSON when a real diff is unavailable; deterministic mode reports zero model tokens rather than inventing usage. | Intentional evidence-format delta |
| Recovery story | Reviewer/monitor failure, repair or rollback, then a proposed policy | The live capture shows injected HTTP 500 evidence, monitor detection, rollback to v1.0.1, shadow benchmark, and the four-mechanism policy proposal. | Match, using live recovery evidence |
| Bottom ledger | Agent balances plus recent source-linked transactions | Balances and transactions are backed by the API ledger. Measured tokens and internal credits remain separate columns. | Match |
| Brand and navigation | Dhurandhar mark plus Runs, Replay, Agents, Policies, and Ledger | The same literal navigation and brand hierarchy are implemented with accessible buttons and current-page state. | Match |
| Objective action | High-contrast orange primary action | `New objective` opens a native modal with objective, context, line-separated acceptance criteria, and priority. Repository/write mode remains host-configured in this safe MVP. | Deliberate safety simplification |
| Run density | Ten curated proof events visible in the concept | Real API replay contains infrastructure and ledger events as well, so long runs scroll inside the fixed timeline. The initial view follows the latest consequential policy event. | Deliberate truth-over-curation delta |
| Responsive behavior | Desktop first; collapse rail and stack inspector below 900 px | Verified at 900 × 900 and 390 × 844. The rail collapses to icons, the inspector stacks, and the 390 px view has no horizontal document overflow. | Match |

## Verification notes

- Desktop capture: 1440 × 900, real FastAPI data after a recovery drill.
- Responsive captures: 900 × 900 and 390 × 844.
- Browser console after rebuild: 0 errors, 0 warnings.
- The generated concept was used as a visual north star, not presented as a screenshot of product behavior.
