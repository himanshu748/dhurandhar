import type { AgentBalance, LedgerTransaction, ReplayEvent } from "../types";

const CINEMATIC_EVENT_TYPES = new Set([
  "objective.created",
  "brief.accepted",
  "planning.completed",
  "scope.accepted",
  "auction.opened",
  "bid.submitted",
  "auction.awarded",
  "task.assigned",
  "runtime.invoked",
  "code.generated",
  "implementation.ready",
  "implementation.repaired",
  "pull_request.opened",
  "merge.blocked",
  "review.completed",
  "review.approved",
  "tests.passed",
  "tests.unverified",
  "verification.passed",
  "deployment.started",
  "deployment.succeeded",
  "deployment.completed",
  "run.failed",
  "monitor.healthy",
  "monitor.regression",
  "regression.injected",
  "monitor.alert",
  "rollback.started",
  "rollback.completed",
  "incident.analyzed",
  "policy.proposed",
  "benchmark.completed",
  "policy.approved",
  "policy.rejected",
  "policy.activated",
  "run.completed",
]);

export const selectCinematicEvents = (events: ReplayEvent[]) => events.filter((event) =>
  CINEMATIC_EVENT_TYPES.has(event.type)
  || event.type === "ledger.transaction"
  || Boolean(event.provenance)
  || ["blocked", "regression", "proposed"].includes(event.status),
);

export const balancesAtSequence = (
  agents: AgentBalance[],
  transactions: LedgerTransaction[],
  events: ReplayEvent[],
  sequence: number,
) => {
  const balances = new Map(agents.map((agent) => [agent.id, agent.balance]));
  const eventSequence = new Map(events.map((event) => [event.id, event.sequence]));

  for (const transaction of transactions) {
    const transactionSequence = transaction.eventId ? eventSequence.get(transaction.eventId) : undefined;
    if (transactionSequence === undefined || transactionSequence <= sequence) continue;
    if (transaction.fromAgent && balances.has(transaction.fromAgent)) {
      balances.set(transaction.fromAgent, (balances.get(transaction.fromAgent) ?? 0) + transaction.credits);
    }
    if (transaction.toAgent && balances.has(transaction.toAgent)) {
      balances.set(transaction.toAgent, (balances.get(transaction.toAgent) ?? 0) - transaction.credits);
    }
  }

  return agents.map((agent) => ({ ...agent, balance: balances.get(agent.id) ?? agent.balance }));
};

export const transactionSequence = (transaction: LedgerTransaction, events: ReplayEvent[]) =>
  events.find((event) => event.id === transaction.eventId)?.sequence;

export const settlementProof = (events: ReplayEvent[]) => {
  const ledger = events.flatMap((event) => event.ledger ? [{ ...event.ledger, eventId: event.id, sequence: event.sequence }] : []);
  const escrow = ledger.find((item) => item.kind === "escrow" || item.kind === "escrow_lock");
  const outputs = ledger.filter((item) => ["payout", "refund", "settlement"].includes(item.kind));
  const outputTotal = outputs.reduce((total, item) => total + item.amount, 0);
  return {
    escrow,
    outputs,
    outputTotal,
    conserved: Boolean(escrow && outputs.length && Math.abs(escrow.amount - outputTotal) < 0.0001),
  };
};
