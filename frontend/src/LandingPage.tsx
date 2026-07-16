import {
  ArrowRight,
  ExternalLink,
  GitBranch,
  LockKeyhole,
  Scale,
  ShieldCheck,
  TerminalSquare,
  TestTube2,
  Waypoints,
} from "lucide-react";
import { useLayoutEffect, useRef, type ReactNode } from "react";
import { CopyableValue } from "./components/CopyableValue";
import { ProvenanceBadge } from "./components/ProvenanceBadge";
import { companyRoster } from "./data/roster";
import { useReducedMotion } from "./hooks/useReducedMotion";
import heroScreenshot from "./assets/dhurandhar-auction-live-1440x1000.jpg";

const REPOSITORY = "https://github.com/himanshu748/dhurandhar";
const LIVE_EVIDENCE = `${REPOSITORY}/blob/main/docs/LIVE_EVIDENCE.md`;
const LIVE_RUNBOOK = `${REPOSITORY}/blob/main/README.md#2-start-dhurandhar-with-all-write-gates-explicit`;
const VIDEO_GUIDE = `${REPOSITORY}/blob/main/docs/VIDEO_SHOT_LIST.md`;
const RELEASE_NOTES = `${REPOSITORY}/blob/main/docs/RELEASE_NOTES.md`;

const IMPLEMENTATION_THREAD = "019f693d-e649-7a91-8dd3-f2cf1a772516";
const REVIEW_THREAD = "019f6940-61f5-7ea2-85e8-d20a1afaaf6f";
const FEEDBACK_SESSION = "019f6172-596f-7d50-a842-b839fd16af3e";
const DIFF_SHA256 = "40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33";
const LIVE_COMMAND = [
  "source .venv/bin/activate",
  "DHURANDHAR_OPERATOR_TOKEN=dhurandhar-demo-operator-token \\",
  "DHURANDHAR_RUNTIME=codex \\",
  "DHURANDHAR_ENABLE_CODEX_RUNTIME=true \\",
  "DHURANDHAR_CODEX_APPLY_CHANGES=true \\",
  "DHURANDHAR_CODEX_WORKDIR=/tmp/misconception-debugger-dhurandhar-demo \\",
  "DHURANDHAR_EVENT_LOG=/tmp/dhurandhar-misconception-demo-events.jsonl \\",
  "DHURANDHAR_SEED_DEMO=false \\",
  "DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.6-sol \\",
  "DHURANDHAR_REVIEWER_MODEL=gpt-5.6-sol \\",
  "DHURANDHAR_CODEX_TIMEOUT_SECONDS=600 \\",
  "make dev-backend",
].join("\n");

const enforcementClaims = [
  {
    icon: LockKeyhole,
    claim: "The implementer cannot approve itself.",
    mechanism: "Aegis runs as a second Codex invocation, in a read-only sandbox, and a reused implementation thread is rejected.",
    href: `${REPOSITORY}/blob/main/backend/app/services/runtime.py#L250-L327`,
    linkLabel: "Reviewer isolation",
  },
  {
    icon: TestTube2,
    claim: "Model-claimed tests are not release proof.",
    mechanism: "Sentinel selects repository-owned pytest or Vitest argv from a static allowlist and executes it with shell=false.",
    href: `${REPOSITORY}/blob/main/backend/app/services/orchestrator.py#L674-L841`,
    linkLabel: "Sentinel allowlist",
  },
  {
    icon: GitBranch,
    claim: "The diff is not model testimony.",
    mechanism: "The kernel calls Git for changed paths, numstat and raw bytes, then computes SHA-256 outside the model process.",
    href: `${REPOSITORY}/blob/main/backend/app/services/runtime.py#L747-L865`,
    linkLabel: "Git evidence capture",
  },
  {
    icon: Waypoints,
    claim: "History is tamper-evident on every read.",
    mechanism: "The event store reloads and verifies sequence, predecessor hash and event hash before returning journal records.",
    href: `${REPOSITORY}/blob/main/backend/app/services/event_store.py#L73-L197`,
    linkLabel: "Hash-chain verification",
  },
];

const journalStats = [
  { value: "89", label: "chained events" },
  { value: "2", label: "Codex threads" },
  { value: "5", label: "changed files" },
  { value: "+226", label: "lines" },
  { value: "40/40", label: "credits conserved" },
  { value: "1", label: "executed release gate" },
];

const lifecycleStages = [
  { stage: "Objective", agent: "Atlas", action: "Scopes the objective and runs the auction." },
  { stage: "Bid", agent: "Forge · Prism · Rivet", action: "Each pays 1 CR to submit evidence-backed work." },
  { stage: "Implement", agent: "Rivet", action: "The winner invokes Codex in workspace-write." },
  { stage: "Review", agent: "Aegis", action: "Invokes Codex read-only in a separate thread." },
  { stage: "Verify", agent: "Sentinel", action: "Executes the real allowlisted release test command." },
  { stage: "Promote", agent: "Shipwright", action: "Promotes only to the reversible demo sandbox." },
  { stage: "Settle", agent: "Atlas", action: "Escrow pays out with 40/40 credits conserved." },
  { stage: "Learn", agent: "Chronicle", action: "Records outcomes as regressions assign liability; only a human can approve proposed controls." },
];

const LANDING_ANIMATION_TARGETS = "[data-landing-hero-item], [data-landing-reveal], [data-landing-hero-parallax]";
const LANDING_ANIMATION_DEADLINE_MS = 1_500;

function ExternalAnchor({ href, children, className }: { href: string; children: ReactNode; className?: string }) {
  return <a className={className} href={href} target="_blank" rel="noreferrer">{children}<ExternalLink size={13} aria-hidden="true" /></a>;
}

function EvidenceBoundary({
  label,
  sandbox,
  thread,
  tokens,
}: {
  label: string;
  sandbox: string;
  thread: string;
  tokens: string;
}) {
  return (
    <div className="landing-boundary">
      <div><strong>{label}</strong><code>{sandbox}</code></div>
      <CopyableValue value={thread} label={`${label} thread ID`} head={14} tail={10} />
      <p>{tokens}</p>
    </div>
  );
}

export default function LandingPage() {
  const root = useRef<HTMLElement | null>(null);
  const reducedMotion = useReducedMotion();

  useLayoutEffect(() => {
    const element = root.current;
    if (!element || reducedMotion) return undefined;
    let cancelled = false;
    let safetyExpired = false;
    let context: { revert: () => void } | undefined;
    let entryFrame: number | undefined;
    const revealFrames = new Set<number>();
    const deadline = window.performance.now() + LANDING_ANIMATION_DEADLINE_MS;
    let killTweens: ((targets: HTMLElement[]) => void) | undefined;

    const animationTargets = () => Array.from(element.querySelectorAll<HTMLElement>(LANDING_ANIMATION_TARGETS));

    const clearInlineAnimationState = () => {
      animationTargets().forEach((target) => {
        target.style.removeProperty("opacity");
        target.style.removeProperty("transform");
        target.style.removeProperty("translate");
        target.style.removeProperty("visibility");
      });
    };

    const cancelAnimationFrames = () => {
      if (entryFrame !== undefined) {
        window.cancelAnimationFrame(entryFrame);
        entryFrame = undefined;
      }
      revealFrames.forEach((frame) => window.cancelAnimationFrame(frame));
      revealFrames.clear();
    };

    const stopAnimations = () => {
      cancelAnimationFrames();
      killTweens?.(animationTargets());
      context?.revert();
      context = undefined;
      clearInlineAnimationState();
    };

    const isExpired = () => cancelled || safetyExpired || window.performance.now() >= deadline;
    const expireAnimations = () => {
      if (cancelled) return;
      safetyExpired = true;
      stopAnimations();
    };

    const safetyTimer = window.setTimeout(expireAnimations, LANDING_ANIMATION_DEADLINE_MS);

    void import("./lib/gsap").then(({ gsap, ScrollTrigger }) => {
      if (isExpired() || !root.current) {
        expireAnimations();
        return;
      }
      killTweens = (targets) => gsap.killTweensOf(targets);

      entryFrame = window.requestAnimationFrame(() => {
        entryFrame = undefined;
        if (isExpired() || !root.current) {
          expireAnimations();
          return;
        }

        context = gsap.context(() => {
          const heroItems = gsap.utils.toArray<HTMLElement>("[data-landing-hero-item]");
          gsap.set(heroItems, { opacity: 0, y: 20 });
          gsap.to(heroItems, {
            opacity: 1,
            y: 0,
            duration: 0.78,
            stagger: 0.1,
            ease: "power3.out",
          });

          const heroScreenshot = root.current?.querySelector<HTMLElement>("[data-landing-hero-parallax]");
          if (heroScreenshot) {
            gsap.set(heroScreenshot, { yPercent: -1.25 });
            gsap.to(heroScreenshot, {
              yPercent: 1.25,
              ease: "none",
              scrollTrigger: {
                trigger: heroScreenshot,
                start: "top bottom",
                end: "bottom top",
                scrub: 0.6,
              },
            });
          }

          gsap.utils.toArray<HTMLElement>("[data-landing-reveal]").forEach((section) => {
            ScrollTrigger.create({
              trigger: section,
              start: "top 86%",
              once: true,
              onEnter: () => {
                if (isExpired()) {
                  expireAnimations();
                  return;
                }
                const frame = window.requestAnimationFrame(() => {
                  revealFrames.delete(frame);
                  if (isExpired()) {
                    expireAnimations();
                    return;
                  }
                  gsap.set(section, { opacity: 0, y: 22 });
                  gsap.to(section, {
                    opacity: 1,
                    y: 0,
                    duration: 0.7,
                    ease: "power3.out",
                  });
                });
                revealFrames.add(frame);
              },
            });
          });
        }, element);
      });
    }).catch(() => expireAnimations());

    return () => {
      cancelled = true;
      window.clearTimeout(safetyTimer);
      cancelAnimationFrames();
      killTweens?.(animationTargets());
      context?.revert();
    };
  }, [reducedMotion]);

  return (
    <main className="landing" ref={root}>
      <header className="landing-nav">
        <a className="landing-brand" href="/" aria-label="Dhurandhar home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span>Dhurandhar</span>
        </a>
        <a className="landing-replay-cta" href="/replay" aria-label="Open replay navigation">Open Change Replay<ArrowRight size={15} aria-hidden="true" /></a>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-grid">
          <div className="landing-hero-copy">
            <h1 data-landing-hero-item>An AI software company that shows receipts.</h1>
            <p className="landing-hero-subtext" data-landing-hero-item>AI agents ship code on faith. Dhurandhar earns trust with auctions, independent review, a real test gate and hash-chained evidence.</p>
            <div className="landing-hero-actions" data-landing-hero-item>
              <a className="landing-hero-primary" href="/replay">Open Change Replay<ArrowRight size={16} aria-hidden="true" /></a>
              <ExternalAnchor className="landing-hero-secondary" href={REPOSITORY}>View source on GitHub</ExternalAnchor>
            </div>
          </div>
          <a className="landing-hero-visual" href="/replay" aria-label="Inspect the replay screenshot" data-landing-hero-item>
            <img
              src={heroScreenshot}
              alt="Dhurandhar Change Replay showing the three-engineer auction and evidence ledger"
              width="1440"
              height="1000"
              decoding="async"
              fetchPriority="high"
              data-landing-hero-parallax
            />
          </a>
        </div>
        <div className="landing-disclosure" role="note" aria-label="Hosted replay disclosure">
          <ProvenanceBadge runMode="deterministic" />
          <div>
            <strong>This hosted instance runs in deterministic replay mode.</strong>
            <p>It executes no model calls. It replays the immutable <code>89</code>-event journal captured from the completed live run.</p>
          </div>
          <div className="landing-disclosure-links">
            <ExternalAnchor href={LIVE_EVIDENCE}>Live gpt-5.6-sol evidence</ExternalAnchor>
            <ExternalAnchor href={LIVE_RUNBOOK}>One-command live-runtime launch</ExternalAnchor>
          </div>
        </div>
        <div className="landing-run-strip" aria-label="Recorded run summary">
          <span>This real objective was implemented live by Codex, independently reviewed, test-gated and settled.</span>
          <a href="/replay">Replay every recorded event at /replay.<ArrowRight size={14} aria-hidden="true" /></a>
        </div>
        <p className="landing-codex-boundary" aria-label="Codex sandbox boundary">
          Implementation and review were two live Codex CLI invocations in separate sandboxes: <code>workspace-write</code> and <code>read-only</code>.
        </p>
      </section>

      <section className="landing-journal-stats" data-landing-reveal aria-label="Recorded run facts">
        {journalStats.map((stat) => (
          <div key={stat.label}><strong>{stat.value}</strong><span>{stat.label}</span></div>
        ))}
      </section>

      <section className="landing-lifecycle" data-landing-reveal aria-labelledby="lifecycle-title">
        <div className="landing-lifecycle-heading">
          <span>RECORDED RUN LIFECYCLE</span>
          <h2 id="lifecycle-title">From objective to human authority</h2>
          <p>Every handoff is backed by a journal event and an enforced boundary.</p>
        </div>
        <ol className="landing-lifecycle-flow">
          {lifecycleStages.map((item, index) => (
            <li className="landing-lifecycle-step" key={item.stage}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <code>{item.agent.includes("·") ? "AGENTS" : "AGENT"} · {item.agent}</code>
              <h3>{item.stage}</h3>
              <p>{item.action}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="landing-section landing-verify" data-landing-reveal aria-labelledby="verify-title">
        <div className="landing-section-heading">
          <h2 id="verify-title">Verify it yourself</h2>
          <p>Three independent ways to inspect the same claim boundary.</p>
        </div>
        <div className="landing-proof-grid">
          <article className="landing-proof">
            <span className="landing-proof-number">01</span>
            <h3>Replay the recorded run</h3>
            <p>Inspect the auction, model boundaries, Git evidence, independent gate, settlement, recovery and human authority in source order.</p>
            <a className="landing-primary-link" href="/replay">Open the 89-event replay<ArrowRight size={14} aria-hidden="true" /></a>
          </article>

          <article className="landing-proof landing-proof-evidence">
            <span className="landing-proof-number">02</span>
            <h3>Read the live evidence</h3>
            <p>The requested model slug was accepted by Codex CLI; thread IDs and token totals were parsed from its JSONL stream.</p>
            <EvidenceBoundary
              label="Implementation"
              sandbox="workspace-write"
              thread={IMPLEMENTATION_THREAD}
              tokens="333,511 input · 294,400 cached · 6,297 output · 2,150 reasoning"
            />
            <EvidenceBoundary
              label="Independent review"
              sandbox="read-only"
              thread={REVIEW_THREAD}
              tokens="361,206 input · 315,904 cached · 3,566 output · 2,103 reasoning"
            />
            <div className="landing-diff-proof"><span>Diff SHA-256</span><CopyableValue value={DIFF_SHA256} label="diff SHA-256" head={14} tail={12} /></div>
            <ExternalAnchor className="landing-text-link" href={LIVE_EVIDENCE}>Inspect the complete evidence record</ExternalAnchor>
          </article>

          <article className="landing-proof landing-proof-command">
            <span className="landing-proof-number">03</span>
            <h3>Run it live yourself</h3>
            <p>After the linked isolated-worktree prerequisites, this launches the live runtime against your own Codex authentication.</p>
            <pre aria-label="Live Codex runtime command"><code>{LIVE_COMMAND}</code></pre>
            <p className="landing-command-note"><TerminalSquare size={13} aria-hidden="true" />Requires Codex CLI 0.144.0+ and produces your own thread IDs after you file an objective.</p>
          </article>
        </div>
      </section>

      <section className="landing-section landing-enforcement" data-landing-reveal aria-labelledby="enforcement-title">
        <div className="landing-section-heading">
          <h2 id="enforcement-title">Why it is not a demo of prompts</h2>
          <p>Each claim has an executable enforcement mechanism.</p>
        </div>
        <div className="landing-claim-list">
          {enforcementClaims.map(({ icon: Icon, claim, mechanism, href, linkLabel }, index) => (
            <article className="landing-claim" key={claim}>
              <div className="landing-claim-index"><Icon size={17} aria-hidden="true" /><code>{String(index + 1).padStart(2, "0")}</code></div>
              <div><h3>{claim}</h3><p>{mechanism}</p></div>
              <ExternalAnchor href={href}>{linkLabel}</ExternalAnchor>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section landing-economy" data-landing-reveal aria-labelledby="economy-title">
        <div className="landing-section-heading">
          <h2 id="economy-title">Eight roles, one conserved ledger</h2>
          <p>Credits make allocation, participation, responsibility and recovery inspectable.</p>
        </div>
        <div className="landing-economy-layout">
          <div className="landing-roster" aria-label="Eight-agent roster">
            {companyRoster.map((agent, index) => (
              <div className="landing-agent" key={agent.id}>
                <code>{String(index + 1).padStart(2, "0")}</code>
                <span><strong>{agent.displayName}</strong><small>{agent.companyRole}</small></span>
              </div>
            ))}
          </div>
          <div className="landing-ledger-explainer">
            <div><Scale size={18} aria-hidden="true" /><span><small>Participation</small><strong>Forge −1 · Prism −1 · Rivet −1</strong></span></div>
            <div><ShieldCheck size={18} aria-hidden="true" /><span><small>Escrow</small><strong>Atlas locks 40 CR before implementation</strong></span></div>
            <div><GitBranch size={18} aria-hidden="true" /><span><small>Verified settlement</small><strong>24 + 5 + 5 + 3 + 2 + 1 = 40 CR</strong></span></div>
            <div className="is-liability"><LockKeyhole size={18} aria-hidden="true" /><span><small>Escaped-regression liability</small><strong>Implementer 4 · Aegis 3 · Sentinel 2 · Shipwright 2</strong></span></div>
          </div>
        </div>
      </section>

      <footer className="landing-footer" data-landing-reveal>
        <div><span>Repository</span><ExternalAnchor href={REPOSITORY}>github.com/himanshu748/dhurandhar</ExternalAnchor></div>
        <div><span>Live evidence</span><ExternalAnchor href={LIVE_EVIDENCE}>2026-07-16 journal</ExternalAnchor></div>
        <div><span>Video</span><ExternalAnchor href={VIDEO_GUIDE}>PENDING · recording guide</ExternalAnchor></div>
        <div><span>/feedback session</span><CopyableValue value={FEEDBACK_SESSION} label="feedback session ID" head={12} tail={10} /></div>
        <div><span>Release tag</span><ExternalAnchor href={RELEASE_NOTES}>NOT TAGGED · v1.0.0 draft</ExternalAnchor></div>
      </footer>
    </main>
  );
}
