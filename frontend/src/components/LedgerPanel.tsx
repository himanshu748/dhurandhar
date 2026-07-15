import { ArrowUpRight } from "lucide-react";
import type { AgentBalance, LedgerTransaction } from "../types";
import { RoleMark } from "./RoleMark";

const formatTime = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

export function LedgerPanel({
  agents,
  transactions,
  onTransaction,
}: {
  agents: AgentBalance[];
  transactions: LedgerTransaction[];
  onTransaction: (eventId?: string) => void;
}) {
  return (
    <section className="ledger-panel" aria-label="Agent balances and recent ledger transactions">
      <div className="agent-balances">
        <div className="ledger-heading"><h2>Agent balances</h2></div>
        <div className="balance-table">
          <div className="table-head"><span>Agent</span><span>Balance (credits)</span></div>
          {agents.slice(0, 4).map((agent) => (
            <div className="balance-row" key={agent.id}>
              <RoleMark role={agent.displayName} />
              <code>{agent.balance.toLocaleString()}</code>
            </div>
          ))}
        </div>
        <button className="text-link" type="button">View all agents <ArrowUpRight size={13} /></button>
      </div>
      <div className="recent-transactions">
        <div className="ledger-heading"><h2>Recent transactions</h2></div>
        <div className="transaction-table">
          <div className="transaction-row table-head">
            <span>Time</span><span>Agent</span><span>Type</span><span>Description</span><span>Tokens</span><span>Credits</span>
          </div>
          {transactions.slice(0, 5).map((transaction) => (
            <button className="transaction-row" key={transaction.id} type="button" onClick={() => onTransaction(transaction.eventId)}>
              <code>{formatTime(transaction.occurredAt)}</code>
              <RoleMark role={transaction.agent} />
              <span className={`tx-${transaction.type}`}>{transaction.type}</span>
              <span>{transaction.description}</span>
              <code>{transaction.tokens.toLocaleString()}</code>
              <code>{transaction.credits.toLocaleString()}</code>
            </button>
          ))}
        </div>
        <button className="text-link align-right" type="button">View full ledger <ArrowUpRight size={13} /></button>
      </div>
    </section>
  );
}
