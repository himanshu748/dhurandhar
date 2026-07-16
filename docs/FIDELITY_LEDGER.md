# Dhurandhar visual fidelity ledger

Replay comparison completed on 2026-07-15 at the 1440 × 1000 desktop demo target. The judge-facing landing route was added on 2026-07-16; its final production-browser capture remains part of the current release QA pass.

- Visual north star: [`design-concept.png`](./design-concept.png)
- Live replay capture: [`../output/browser/dhurandhar-cinema-live-1440x1000.png`](../output/browser/dhurandhar-cinema-live-1440x1000.png)
- Live auction capture: [`../output/browser/dhurandhar-auction-live-1440x1000.png`](../output/browser/dhurandhar-auction-live-1440x1000.png)
- Live recovery capture: [`../output/browser/dhurandhar-recovery-live-1440x1000.png`](../output/browser/dhurandhar-recovery-live-1440x1000.png)

> [!IMPORTANT]
> These release-candidate captures use the recorded live event journal in `output/evidence/codex-live-run-2026-07-15.jsonl`. They demonstrate UI fidelity and captured Codex evidence. They are not proof of a public deployment or an external production recovery.

## Gap closure

| Gap found before this pass | Implemented result | Evidence / disposition |
| --- | --- | --- |
| A judge landed directly inside a dense control plane with no explanation of provenance or playback limits | `/` is now a compact judge briefing; the existing control plane moved to `/replay`. The first screen states that the current process is deterministic, performs no model calls, and replays the committed 89-event record. It links the exact threads, tokens, diff digest, live-evidence document, and one-command local path without presenting playback as a new invocation. | Closed in implementation; final browser capture pending release QA. The landing `fixture` badge labels the playback process while replay cards preserve historical event provenance. |
| Replay was a dense dashboard table with no cinematic causal reveal | Consequential records project into 39 vertical evidence cards controlled by one scrubber-owned GSAP timeline. Cards reveal with transform/opacity, SVG links draw by stroke offset, and predecessor hashes pulse in order. | Closed; 38 visible predecessor links plus the genesis record make the append-only chain legible. |
| Provenance was easy to miss and fixture output could resemble live output | Every run and card carries a persistent provenance badge. Live model boundaries show model and sandbox; live journal-only orchestration has a distinct state; fixtures are neutral gray and explicitly say no model call. | Closed without inferring provenance from generic fields. |
| Codex evidence was hidden in a side inspector | The implementation moment presents the recorded thread, requested model, token categories, commands, exit codes, file/numstat evidence, and SHA-256 in the primary card. | Closed. Historical cards retain their recorded values. For the final `gpt-5.6-sol` record, badges, timeline facts, top bar, and inspector all say the slug was CLI-requested and not stream-observed; the stream supplied the thread/tokens but no model echo. |
| Auction outcome was summarized rather than experienced | Forge, Prism, and Rivet render side-by-side with exact cost, credibility, and citations. GSAP Flip promotes the recorded winner; the two losers recede. Participation fees and escrow use animated counters. | Closed; the live journal shows three 1-credit fees and the 40-credit lock. |
| Economy panel exposed only a transaction list and a partial roster | The ledger shows all eight agents, state, balance bar, and cursor-time balance. Settlement plays as winner/Aegis/Sentinel/Shipwright/Chronicle/refund transfers and proves the sum beside escrow. Penalties use restrained red and a 2 px shake; dormant agents grayscale. | Closed; captured settlement is `19 + 5 + 5 + 3 + 2 + 6 = 40`. |
| Recovery was buried among general replay records | Regression, alert, four recorded liability penalties, known-good restore, policy proposal, and the human decision form a guided recovery rail. | Closed; the captured proposal was rejected, so the UI truthfully renders a resolved human gate instead of fabricating a pending action. |
| Global state did not keep provenance/model/operator mode in view | Kernel health, run provenance, model, exact read-only/workspace-write boundary, and operator state remain in the top bar. | Closed. |
| Loading and copy affordances were inconsistent | Boot and inline pending states use skeleton blocks. Hashes, IDs, thread/session values, and SHA-256 use JetBrains Mono, middle-out truncation, full-value tooltips, and copy-on-click status. | Closed. |
| Old theme still contained blue/purple AI styling, a gradient scrubber, and spinners | Surfaces use near-black `#0B0C0E`, hairline 8%-white borders, amber `#FFB000`, cyan `#22D3EE`, and red only for failure/liability. Gradient, purple role color, emoji iconography, and spinner keyframes were removed. | Closed. |

## Concept comparison

| Comparison point | Concept intent | Release-candidate result | Disposition |
| --- | --- | --- | --- |
| Command-center shell | Fixed left rail, compact global header, replay center, inspector right, ledger below | The five-region desktop shell and information density remain intact. Replay is the dominant lens while inspector and economy stay concurrently visible. | Match |
| Forensic density | A high-signal operational instrument rather than a consumer dashboard | Hairline dividers, compact typography, literal status labels, command evidence, and numeric columns replace decorative dashboard chrome. | Match, refined |
| Selected evidence coupling | Timeline selection should drive the right-hand proof surface | Clicking or scrubbing a card updates the selected event, inspector, balances, hash state, and auction/recovery moment from one cursor. | Match |
| Causal replay | Ordered records connected by an explicit spine | The concept row spine became a card-and-connector filmstrip because the current brief requires replay as cinema. | Deliberate current-brief override |
| Palette | Original concept used graphite/blue-black with broader role color | The current brief supersedes it with exact near-black, amber economy, cyan activity, and failure-only red. | Deliberate current-brief override |
| Agent company | Concept exposed a smaller roster and compact balances | All eight PRD agents are always available and settlement roles are individually visible. | Product truth extension |
| Recovery and governance | Failure, rollback, and proposed policy should remain auditable | The guided recovery rail ends at a visually weighted human gate and never implies autonomous policy activation. | Stronger safety story |
| Desktop framing | Control-room composition intended for a recorded desktop demo | The layout is optimized for 1280 px and above as requested. No additional sub-1280 redesign was added in this pass. | Intentional scope boundary |

## Motion and truth constraints

- `ScrollTrigger` and `Flip` register once in `src/lib/gsap.ts`.
- Effect-owned motion is scoped with `gsap.context()` and reverted during cleanup.
- `prefers-reduced-motion` removes sequencing and presents the evidence immediately.
- Landing sections use the same centralized GSAP registration and reduced-motion boundary, and the landing route is lazy-loaded independently from `/replay`.
- Scrubbing mutates GSAP timeline progress, SVG stroke state, transforms, and opacity; it does not write React state on animation frames or tween layout properties.
- The final captured journal contains 89 raw records and the run view projects 38 consequential cards. Every run record remains available through the API and the complete store is reloaded and hash-verified before reads return.
- The implementation and independent-review cards are the two model-thread boundaries. Runtime, Git, Sentinel, ledger, recovery, and policy records remain visibly separate orchestration evidence.
- Missing evidence renders as unavailable or fixture data; the UI does not synthesize hashes, verdicts, test exits, policy states, or production claims.
- The final 89-event journal is never rewritten to add `observed_model`; the landing links to the documented requested-versus-observed limitation instead.

## Verification notes

- Production Vite preview was inspected in the in-app browser at 1440 × 1000 against the recorded live journal.
- The production build's eager entry plus modulepreloaded runtime/React JavaScript totals 192,908 raw bytes; the 87,488-byte replay chunk is absent from the landing document and is loaded only at `/replay`.
- Dedicated captures cover the implementation hero, three-way auction, and complete recovery/human-gate story.
- Frontend type-check, Vitest suite, production build, and browser console checks are required to pass before the branch is published.
- The final submission recording and video URL remain pending. Recording should describe the hosted process as deterministic, read-only playback of the committed 89-event live journal with no new model call, while keeping the separate synthetic 78-event fixture mode distinct.
- No release tag has been created.
