import { ArrowUpRight, Check, Coins, Minus, ShieldAlert } from "lucide-react";
import { useLayoutEffect, useMemo, useRef } from "react";
import { useReducedMotion } from "../hooks/useReducedMotion";
import { gsap } from "../lib/gsap";
import { balancesAtSequence, settlementProof, transactionSequence } from "../lib/replay";
import type { AgentBalance, LedgerTransaction, ReplayEvent } from "../types";
import { AnimatedNumber } from "./AnimatedNumber";
import { RoleMark } from "./RoleMark";

const formatTime = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

function BalanceBar({ value, maximum }: { value: number; maximum: number }) {
  const bar = useRef<HTMLSpanElement | null>(null);
  const reducedMotion = useReducedMotion();
  const scale = maximum > 0 ? Math.max(0, Math.min(1, value / maximum)) : 0;

  useLayoutEffect(() => {
    const node = bar.current;
    if (!node) return undefined;
    const context = gsap.context(() => {
      gsap.to(node, { scaleX: scale, duration: reducedMotion ? 0 : 0.55, ease: "power3.out", overwrite: true });
    }, node);
    return () => context.revert();
  }, [reducedMotion, scale]);

  return <span className="balance-bar" aria-hidden="true"><span ref={bar} /></span>;
}

export function LedgerPanel({
  agents,
  transactions,
  events,
  currentSequence,
  currentEventId,
  onTransaction,
}: {
  agents: AgentBalance[];
  transactions: LedgerTransaction[];
  events: ReplayEvent[];
  currentSequence: number;
  currentEventId?: string;
  onTransaction: (eventId?: string) => void;
}) {
  const panel = useRef<HTMLElement | null>(null);
  const reducedMotion = useReducedMotion();
  const balances = useMemo(
    () => balancesAtSequence(agents, transactions, events, currentSequence),
    [agents, currentSequence, events, transactions],
  );
  const maximum = Math.max(1, ...balances.map((agent) => agent.balance));
  const visibleTransactions = useMemo(() => transactions
    .filter((transaction) => {
      const sequence = transactionSequence(transaction, events);
      return sequence === undefined || sequence <= currentSequence;
    })
    .sort((left, right) => new Date(right.occurredAt).getTime() - new Date(left.occurredAt).getTime())
    .slice(0, 8), [currentSequence, events, transactions]);
  const proof = useMemo(() => settlementProof(events), [events]);
  const visibleOutputs = proof.outputs.filter((output) => output.sequence <= currentSequence);
  const visibleOutputTotal = visibleOutputs.reduce((total, output) => total + output.amount, 0);
  const conservationReached = proof.escrow !== undefined
    && proof.escrow.sequence <= currentSequence
    && proof.conserved
    && visibleOutputs.length === proof.outputs.length;

  useLayoutEffect(() => {
    const root = panel.current;
    if (!root || reducedMotion || !currentEventId) return undefined;
    const row = root.querySelector<HTMLElement>(`[data-transaction-event="${CSS.escape(currentEventId)}"].is-penalty`);
    if (!row) return undefined;
    const context = gsap.context(() => {
      gsap.fromTo(row, { x: -2 }, { x: 0, duration: 0.3, ease: "rough({ strength: 0.45, points: 5, template: none.out })" });
      gsap.fromTo(row.querySelector(".penalty-flash"), { opacity: 0.32 }, { opacity: 0, duration: 0.48, ease: "power2.out" });
    }, root);
    return () => context.revert();
  }, [currentEventId, reducedMotion]);

  return (
    <section ref={panel} className="ledger-panel forensic-ledger" aria-label="Eight-agent economy and ledger transactions">
      <div className="agent-balances">
        <div className="ledger-heading">
          <div><span>COMPANY ROSTER</span><h2>Eight-agent economy</h2></div>
          <code>{balances.length}/8 reporting</code>
        </div>
        <div className="balance-grid">
          {balances.map((agent) => (
            <article className={`balance-card state-${agent.state}`} key={agent.id}>
              <div className="balance-identity">
                <RoleMark role={agent.displayName} />
                <span>{agent.companyRole ?? agent.role}</span>
                <i>{agent.state}</i>
              </div>
              <div className="balance-value"><AnimatedNumber value={agent.balance} suffix=" CR" /></div>
              <BalanceBar value={agent.balance} maximum={maximum} />
            </article>
          ))}
        </div>
      </div>

      <div className="recent-transactions">
        <div className="ledger-heading settlement-heading">
          <div><span>APPEND-ONLY LEDGER</span><h2>Settlement and liability</h2></div>
          {proof.escrow ? (
            <div className={`conservation-badge ${conservationReached ? "is-conserved" : ""}`}>
              {conservationReached ? <Check size={12} /> : <Coins size={12} />}
              <span>{conservationReached ? "CONSERVED" : "SETTLING"}</span>
              <code>{visibleOutputTotal}/{proof.escrow.amount} CR</code>
            </div>
          ) : (
            <div className="conservation-badge is-incomplete"><Minus size={12} /><span>CONSERVATION DATA INCOMPLETE</span></div>
          )}
        </div>
        <div className="transaction-table">
          <div className="transaction-row table-head">
            <span>Time</span><span>Transfer</span><span>Kind</span><span>Reason</span><span>Credits</span>
          </div>
          {visibleTransactions.length > 0 ? visibleTransactions.map((transaction) => {
            const penalty = transaction.kind === "penalty" || transaction.type === "penalty" || transaction.type === "clawback";
            return (
              <button
                className={`transaction-row ${penalty ? "is-penalty" : ""}`}
                data-transaction-event={transaction.eventId}
                key={transaction.id}
                type="button"
                onClick={() => onTransaction(transaction.eventId)}
              >
                <span className="penalty-flash" aria-hidden="true" />
                <code>{formatTime(transaction.occurredAt)}</code>
                <span className="tx-transfer">
                  {penalty && <ShieldAlert size={11} />}
                  <code>{transaction.fromAgent ?? transaction.agentId}</code><span>→</span><code>{transaction.toAgent ?? "ledger"}</code>
                </span>
                <span className={`tx-${transaction.type}`}>{transaction.kind ?? transaction.type}</span>
                <span>{transaction.description}</span>
                <AnimatedNumber value={transaction.credits} suffix=" CR" />
              </button>
            );
          }) : (
            <div className="ledger-empty">No ledger movement at this replay position.</div>
          )}
        </div>
        <button className="text-link align-right" type="button">Inspect full ledger <ArrowUpRight size={13} /></button>
      </div>
    </section>
  );
}
