import {
  Check,
  Coins,
  FileCode2,
  Gavel,
  GitCommitHorizontal,
  Link2,
  LockKeyhole,
  Radio,
  Rocket,
  ShieldAlert,
  ShieldCheck,
  TerminalSquare,
  TestTube2,
  Trophy,
  X,
} from "lucide-react";
import { useLayoutEffect, useMemo, useRef, type ReactNode } from "react";
import { useReducedMotion } from "../hooks/useReducedMotion";
import { Flip, gsap } from "../lib/gsap";
import type { LedgerEvidence, ReplayEvent, RunSummary, TaskAuction } from "../types";
import { AnimatedNumber } from "./AnimatedNumber";
import { CopyableValue } from "./CopyableValue";
import { ProvenanceBadge } from "./ProvenanceBadge";
import { RoleMark } from "./RoleMark";
import { StatusMark } from "./StatusMark";

const time = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

const category = (event: ReplayEvent) => {
  if (event.type.startsWith("auction") || event.type.startsWith("bid")) return "auction";
  if (event.type === "ledger.transaction") return "economy";
  if (event.type.startsWith("review") || event.type.includes("merge.blocked")) return "review";
  if (event.type.startsWith("tests") || event.type.startsWith("verification")) return "gate";
  if (event.type.startsWith("deployment")) return "release";
  if (event.type.startsWith("monitor") || event.type.startsWith("regression") || event.type.startsWith("rollback")) return "recovery";
  if (event.type.startsWith("policy") || event.type.startsWith("benchmark")) return "policy";
  if (event.provenance) return "codex";
  return "evidence";
};

function EventIcon({ event }: { event: ReplayEvent }) {
  const kind = category(event);
  if (event.type === "auction.awarded") return <Trophy size={16} />;
  if (kind === "auction") return <Gavel size={16} />;
  if (kind === "economy") return <Coins size={16} />;
  if (kind === "review") return <ShieldCheck size={16} />;
  if (kind === "gate") return <TestTube2 size={16} />;
  if (kind === "release") return <Rocket size={16} />;
  if (kind === "recovery") return <ShieldAlert size={16} />;
  if (kind === "codex") return <TerminalSquare size={16} />;
  if (kind === "policy") return <LockKeyhole size={16} />;
  return <GitCommitHorizontal size={16} />;
}

function AuctionMoment({ auction, economy }: { auction: TaskAuction; economy: LedgerEvidence[] }) {
  const root = useRef<HTMLDivElement | null>(null);
  const reducedMotion = useReducedMotion();
  const awarded = auction.status === "awarded" && Boolean(auction.winnerId);

  useLayoutEffect(() => {
    const element = root.current;
    if (!element || !awarded) return undefined;
    const cards = Array.from(element.querySelectorAll<HTMLElement>("[data-bid-card]"));
    const context = gsap.context(() => {
      const state = Flip.getState(cards);
      cards.forEach((card) => {
        const winner = card.dataset.bidder === auction.winnerId;
        card.classList.toggle("is-winner", winner);
        card.classList.toggle("is-loser", !winner);
      });
      if (!reducedMotion) {
        Flip.from(state, { duration: 0.7, ease: "power3.inOut", stagger: 0.045, absolute: false });
      }
    }, element);
    return () => {
      context.revert();
      cards.forEach((card) => card.classList.remove("is-winner", "is-loser"));
    };
  }, [auction.winnerId, awarded, reducedMotion]);

  return (
    <div className="auction-stage" ref={root}>
      <div className="auction-stage-heading">
        <span>Competitive implementation auction</span>
        <code>{auction.bids.length} bids · {auction.bounty !== undefined ? `${auction.bounty} CR bounty` : "bounty unreported"}</code>
      </div>
      <div className="bid-grid">
        {auction.bids.map((bid) => (
          <article className="bid-card" data-bid-card data-bidder={bid.bidderId} key={bid.bidderId}>
            <div className="bid-card-heading">
              <RoleMark role={bid.bidder} />
              {bid.winner && <span className="winner-label"><Trophy size={11} /> selected</span>}
            </div>
            <AnimatedNumber value={bid.amount} suffix=" CR" className="bid-price" />
            <dl className="bid-metrics">
              <div><dt>Credibility</dt><dd>{bid.credibility === undefined ? "unreported" : bid.credibility.toFixed(2)}</dd></div>
              <div><dt>Citations</dt><dd>{bid.evidence.length}</dd></div>
            </dl>
            {bid.plan && <p>{bid.plan}</p>}
            {bid.evidence.length > 0 && (
              <ul className="bid-citations">
                {bid.evidence.map((citation) => <li key={citation}><Link2 size={10} /><span>{citation}</span></li>)}
              </ul>
            )}
          </article>
        ))}
      </div>
      {economy.length > 0 ? (
        <div className="auction-economy" aria-label="Observed auction ledger movements">
          {economy.map((entry, index) => (
            <div className={entry.kind.includes("escrow") ? "is-escrow" : ""} key={`${entry.kind}-${entry.fromAgent}-${index}`}>
              <span>{entry.kind.replaceAll("_", " ")}</span>
              <AnimatedNumber value={entry.amount} prefix="−" suffix=" CR" />
              <small>{entry.fromAgent ?? "ledger"}{entry.toAgent ? ` → ${entry.toAgent}` : ""}</small>
            </div>
          ))}
        </div>
      ) : (
        <p className="evidence-unavailable">Auction ledger movements are not present in this evidence source.</p>
      )}
    </div>
  );
}

function VerdictMoment({ event }: { event: ReplayEvent }) {
  const root = useRef<HTMLDivElement | null>(null);
  const reducedMotion = useReducedMotion();
  const verdict = event.review?.verdict?.toLowerCase();
  const approved = verdict === "approved" || verdict === "approve";
  const changesRequested = verdict === "changes_requested";

  useLayoutEffect(() => {
    const element = root.current;
    if (!element) return undefined;
    const context = gsap.context(() => {
      if (reducedMotion) {
        gsap.set(element.querySelectorAll("[data-verdict-motion]"), { opacity: 1, x: 0, y: 0, scale: 1, rotate: 0 });
        return;
      }
      if (approved) {
        gsap.fromTo("[data-approval-seal]", { opacity: 0, scale: 1.45, rotate: -5 }, {
          opacity: 1,
          scale: 1,
          rotate: 0,
          duration: 0.62,
          ease: "back.out(1.7)",
        });
      }
      if (changesRequested) {
        gsap.fromTo("[data-finding-row]", { opacity: 0, x: 18 }, {
          opacity: 1,
          x: 0,
          stagger: 0.08,
          duration: 0.42,
          ease: "power3.out",
        });
      }
    }, element);
    return () => context.revert();
  }, [approved, changesRequested, reducedMotion]);

  if (!verdict && !event.review?.findings.length) return null;
  return (
    <div className={`verdict-moment ${changesRequested ? "is-changes-requested" : approved ? "is-approved" : ""}`} ref={root}>
      {approved && (
        <div className="approval-seal" data-approval-seal data-verdict-motion>
          <ShieldCheck size={20} />
          <span>AEGIS</span>
          <strong>APPROVED</strong>
          <small>independent verdict</small>
        </div>
      )}
      {changesRequested && (
        <div className="findings-panel" data-verdict-motion>
          <div className="findings-heading"><ShieldAlert size={15} /><strong>CHANGES REQUESTED</strong><span>{event.review?.findings.length ?? 0} findings</span></div>
          <div className="finding-table">
            <div className="finding-row finding-head"><span>Severity</span><span>Location</span><span>Finding</span></div>
            {event.review?.findings.map((finding, index) => (
              <div className="finding-row" data-finding-row key={`${finding.file}-${finding.line}-${index}`}>
                <code>{finding.severity}</code>
                <code>{finding.file ? `${finding.file}${finding.line !== undefined ? `:${finding.line}` : ""}` : "unreported"}</code>
                <span>{finding.summary}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {!approved && !changesRequested && <code className="verdict-raw">VERDICT · {verdict}</code>}
    </div>
  );
}

function CodexEvidence({ event }: { event: ReplayEvent }) {
  const provenance = event.provenance;
  if (!provenance) return null;
  const outcomes = [...provenance.commands, ...provenance.checks.filter((check) =>
    !provenance.commands.some((command) => command.command === check.command),
  )];
  return (
    <div className={`codex-proof ${provenance.mode === "deterministic" ? "is-fixture" : ""}`}>
      <div className="codex-proof-heading">
        <span><Radio size={13} />Codex implementation boundary</span>
        <code>{provenance.runtime ?? "runtime unreported"}</code>
      </div>
      <dl className="codex-identity-grid">
        <div><dt>Model</dt><dd>{provenance.model ?? (provenance.mode === "deterministic" ? "No model call" : "unreported")}</dd></div>
        <div><dt>Sandbox</dt><dd>{provenance.sandbox ?? "unreported"}</dd></div>
        <div><dt>Thread</dt><dd>{provenance.threadId ? <CopyableValue value={provenance.threadId} label="thread ID" /> : "unreported"}</dd></div>
        <div><dt>Tokens</dt><dd>{provenance.inputTokens.toLocaleString()} in · {provenance.cachedInputTokens.toLocaleString()} cached · {provenance.outputTokens.toLocaleString()} out · {provenance.reasoningOutputTokens.toLocaleString()} reasoning</dd></div>
      </dl>
      {provenance.diff && (
        <div className="diff-proof">
          <div><FileCode2 size={13} /><span>{provenance.diff.files.length} changed files</span><code><b>+{provenance.diff.linesAdded ?? 0}</b> <i>−{provenance.diff.linesDeleted ?? 0}</i></code></div>
          {provenance.diff.files.slice(0, 5).map((file) => <code key={file}>{file}</code>)}
          {provenance.diff.sha256 && <CopyableValue value={provenance.diff.sha256} label="diff SHA-256" />}
        </div>
      )}
      {outcomes.length > 0 && (
        <div className="exit-code-grid" aria-label="Recorded command exit codes">
          {outcomes.map((outcome, index) => {
            const passed = outcome.exitCode === 0 || /pass|success|complete|ok/i.test(outcome.status);
            return (
              <div className={passed ? "is-passed" : "is-failed"} key={`${outcome.command}-${index}`}>
                {passed ? <Check size={12} /> : <X size={12} />}
                <code>{outcome.command}</code>
                <span>{outcome.exitCode === undefined ? outcome.status : `exit ${outcome.exitCode}`}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function LedgerMoment({ ledger }: { ledger: LedgerEvidence }) {
  const penalty = ledger.kind === "penalty" || ledger.kind === "clawback";
  return (
    <div className={`ledger-moment ${penalty ? "is-penalty" : ""}`}>
      <span>{ledger.kind.replaceAll("_", " ")}</span>
      <AnimatedNumber value={ledger.amount} suffix=" CR" />
      <code>{ledger.fromAgent ?? "ledger"} → {ledger.toAgent ?? "ledger"}</code>
      {ledger.reason && <small>{ledger.reason}</small>}
    </div>
  );
}

function TestGateEvidence({ event }: { event: ReplayEvent }) {
  const checks = event.checks ?? [];
  const gateEvent = event.type.startsWith("tests") || event.type.startsWith("verification");
  if (!gateEvent && !checks.length) return null;
  const failedClosed = event.type === "tests.unverified" || event.status === "blocked" || event.status === "regression";
  return (
    <div className={`test-gate-proof ${failedClosed ? "is-failed-closed" : "is-passed"}`}>
      <div className="test-gate-heading">
        {failedClosed ? <ShieldAlert size={14} /> : <ShieldCheck size={14} />}
        <strong>{failedClosed ? "PROMOTION REFUSED · FAIL CLOSED" : "SENTINEL RELEASE GATE PASSED"}</strong>
        <code>{checks.length} executable check{checks.length === 1 ? "" : "s"}</code>
      </div>
      {checks.map((check, index) => (
        <div className="test-gate-row" key={`${check.command}-${index}`}>
          <code>{check.command}</code>
          <span>{check.exitCode === undefined ? check.status : `EXIT ${check.exitCode}`}</span>
          {check.detail && <small>{check.detail}</small>}
        </div>
      ))}
    </div>
  );
}

function EvidenceDetails({ event, auctionEconomy }: { event: ReplayEvent; auctionEconomy: LedgerEvidence[] }) {
  return (
    <div className="evidence-card-body">
      <p className="event-rationale">{event.rationale}</p>
      {event.type === "auction.awarded" && event.auction && <AuctionMoment auction={event.auction} economy={auctionEconomy} />}
      {event.type === "bid.submitted" && event.auction?.bids.at(-1) && (
        <div className="single-bid-proof">
          <Coins size={13} />
          <span>{event.auction.bids.at(-1)?.bidder}</span>
          <code>{event.auction.bids.at(-1)?.amount} CR · credibility {event.auction.bids.at(-1)?.credibility?.toFixed(2) ?? "unreported"}</code>
        </div>
      )}
      <CodexEvidence event={event} />
      <VerdictMoment event={event} />
      <TestGateEvidence event={event} />
      {event.ledger && <LedgerMoment ledger={event.ledger} />}
      {event.evidence.length > 0 && event.type !== "auction.awarded" && (
        <ul className="event-evidence-list">
          {event.evidence.map((item) => (
            <li key={item.id}><span>{item.kind}</span><strong>{item.label}</strong>{item.detail && <small>{item.detail}</small>}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function HashChainLink({ event, previousRaw, skipped }: { event: ReplayEvent; previousRaw?: ReplayEvent; skipped: number }) {
  const hasHash = Boolean(event.hash);
  if (!hasHash) {
    return <div className="hash-chain hash-unavailable"><Link2 size={11} /><span>CHAIN UNAVAILABLE IN THIS EVIDENCE SOURCE</span></div>;
  }
  const genesis = !event.previousHash;
  const verified = genesis || Boolean(previousRaw?.hash && event.previousHash === previousRaw.hash);
  return (
    <div className={`hash-chain ${verified ? "is-verified" : "is-unverified"}`} data-hash-link>
      <Link2 size={11} />
      <span>{genesis ? "GENESIS" : verified ? "APPEND-ONLY LINK VERIFIED" : "CHAIN LINK NOT VERIFIED"}</span>
      {event.previousHash && <CopyableValue value={event.previousHash} label="previous event hash" />}
      <span aria-hidden="true">→</span>
      {event.hash && <CopyableValue value={event.hash} label="event hash" />}
      {skipped > 0 && <small>{skipped} journal record{skipped === 1 ? "" : "s"} bridged by this cinema view</small>}
    </div>
  );
}

export function Timeline({
  events,
  allEvents = events,
  selectedId,
  cursor,
  runMode,
  onSelect,
  children,
}: {
  events: ReplayEvent[];
  allEvents?: ReplayEvent[];
  selectedId: string;
  cursor: number;
  runMode: RunSummary["mode"];
  onSelect: (event: ReplayEvent, index: number) => void;
  children?: ReactNode;
}) {
  const timeline = useRef<HTMLElement | null>(null);
  const master = useRef<gsap.core.Timeline | null>(null);
  const seekTween = useRef<gsap.core.Tween | null>(null);
  const reducedMotion = useReducedMotion();
  const allBySequence = useMemo(() => new Map(allEvents.map((event) => [event.sequence, event])), [allEvents]);
  const auctionEconomy = useMemo(() => allEvents.flatMap((event) =>
    event.ledger && (event.ledger.kind === "bid_fee" || event.ledger.kind.includes("escrow")) ? [event.ledger] : [],
  ), [allEvents]);

  useLayoutEffect(() => {
    const element = timeline.current;
    if (!element) return undefined;
    const context = gsap.context(() => {
      const cards = Array.from(element.querySelectorAll<HTMLElement>("[data-cinema-card]"));
      const connectors = Array.from(element.querySelectorAll<SVGPathElement>("[data-connector]"));
      const hashes = Array.from(element.querySelectorAll<HTMLElement>("[data-hash-link]"));
      if (reducedMotion) {
        if (cards.length) gsap.set(cards, { opacity: 1, y: 0 });
        if (connectors.length) gsap.set(connectors, { strokeDashoffset: 0 });
        if (hashes.length) gsap.set(hashes, { opacity: 1, scale: 1 });
        master.current = null;
        return;
      }
      if (cards.length) gsap.set(cards, { opacity: 0.14, y: 18 });
      if (connectors.length) gsap.set(connectors, { strokeDashoffset: 1 });
      if (hashes.length) gsap.set(hashes, { opacity: 0.45, scale: 0.985, transformOrigin: "left center" });
      const replay = gsap.timeline({ paused: true, defaults: { overwrite: "auto" } });
      cards.forEach((card, index) => {
        replay.addLabel(`event-${index}`);
        if (connectors[index]) replay.to(connectors[index], { strokeDashoffset: 0, duration: 0.22, ease: "none" });
        replay.to(card, { opacity: 1, y: 0, duration: 0.48, ease: "power3.out" }, index === 0 ? ">" : "<+0.03");
        if (hashes[index]) {
          replay.to(hashes[index], { opacity: 1, scale: 1, duration: 0.18, ease: "power2.out" }, "<+0.18");
          replay.to(hashes[index], { scale: 1.012, duration: 0.1, yoyo: true, repeat: 1, ease: "power1.inOut" });
        }
        replay.addLabel(`event-${index}-end`);
      });
      master.current = replay;
      replay.seek(`event-${Math.min(cursor, cards.length - 1)}-end`, false);
    }, element);
    return () => {
      seekTween.current?.kill();
      master.current?.kill();
      master.current = null;
      context.revert();
    };
  }, [events, reducedMotion]);

  useLayoutEffect(() => {
    const element = timeline.current;
    const replay = master.current;
    if (!element || !replay || reducedMotion || events.length === 0) return undefined;
    const context = gsap.context(() => {
      const label = `event-${Math.min(cursor, events.length - 1)}-end`;
      seekTween.current?.kill();
      seekTween.current = gsap.to(replay, {
        time: replay.labels[label],
        duration: 0.42,
        ease: "power3.out",
        overwrite: true,
      });
    }, element);
    return () => {
      seekTween.current?.kill();
      context.revert();
    };
  }, [cursor, events.length, reducedMotion]);

  useLayoutEffect(() => {
    const element = timeline.current;
    const selected = element?.querySelector<HTMLElement>(`[data-event-id="${CSS.escape(selectedId)}"]`);
    selected?.scrollIntoView({ block: "nearest" });
  }, [selectedId]);

  return (
    <section ref={timeline} className="timeline cinematic-timeline" aria-label="Run evidence timeline">
      <div className="cinema-intro">
        <span>CHANGE REPLAY / EVIDENCE CUT</span>
        <code>{events.length} consequential records · source order preserved</code>
      </div>
      <div className="cinema-track">
        {events.map((event, index) => {
          const previousRaw = allBySequence.get(event.sequence - 1);
          const previousCinema = events[index - 1];
          const skipped = previousCinema ? Math.max(0, event.sequence - previousCinema.sequence - 1) : 0;
          return (
            <div className="evidence-card-shell" key={event.id}>
              {index > 0 && (
                <svg className="causal-connector" viewBox="0 0 24 76" preserveAspectRatio="none" aria-hidden="true">
                  <path data-connector pathLength="1" d="M12 0 C12 24 12 50 12 76" />
                </svg>
              )}
              <article
                className={`evidence-card category-${category(event)} ${selectedId === event.id ? "is-selected" : ""} ${index > cursor ? "is-future" : ""}`}
                data-cinema-card
                data-event-id={event.id}
                data-event-type={event.type}
                data-sequence={event.sequence}
                aria-current={selectedId === event.id ? "step" : undefined}
              >
                <button className="evidence-card-select" type="button" onClick={() => onSelect(event, index)}>
                  <span className="evidence-node"><EventIcon event={event} /></span>
                  <span className="evidence-card-main">
                    <span className="evidence-kicker"><code>SEQ {String(event.sequence).padStart(3, "0")}</code><time dateTime={event.occurredAt}>{time(event.occurredAt)}</time><span>{category(event)}</span></span>
                    <strong>{event.title}</strong>
                    <span className="evidence-summary">{event.summary}</span>
                  </span>
                  <span className="evidence-card-meta">
                    <RoleMark role={event.role} />
                    <StatusMark status={event.status} />
                  </span>
                </button>
                <div className="card-provenance"><ProvenanceBadge event={event} runMode={runMode} /></div>
                <EvidenceDetails event={event} auctionEconomy={auctionEconomy} />
                <HashChainLink event={event} previousRaw={previousRaw} skipped={skipped} />
              </article>
            </div>
          );
        })}
      </div>
      {children}
    </section>
  );
}
