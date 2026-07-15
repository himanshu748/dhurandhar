import { describe, expect, it } from "vitest";
import type { AgentBalance, LedgerTransaction, ReplayEvent } from "../types";
import { balancesAtSequence, selectCinematicEvents, settlementProof } from "./replay";

const event = (
  id: string,
  sequence: number,
  type: string,
  ledger?: ReplayEvent["ledger"],
): ReplayEvent => ({
  id,
  sequence,
  occurredAt: `2026-07-15T00:00:${String(sequence).padStart(2, "0")}Z`,
  actor: "atlas",
  role: "product",
  type,
  title: type,
  summary: type,
  status: "success",
  rationale: type,
  evidence: [],
  usage: { inputTokens: 0, outputTokens: 0, credits: 0 },
  ledger,
});

describe("replay evidence projection", () => {
  it("keeps consequential and provenance-bearing events without inventing filler", () => {
    const events = [
      event("noise", 1, "agent.heartbeat"),
      event("auction", 2, "auction.opened"),
      { ...event("runtime", 3, "custom.runtime"), provenance: {
        mode: "live" as const,
        inputTokens: 1,
        cachedInputTokens: 0,
        outputTokens: 1,
        reasoningOutputTokens: 0,
        commands: [],
        checks: [],
        changedFiles: [],
      } },
    ];

    expect(selectCinematicEvents(events).map(({ id }) => id)).toEqual(["auction", "runtime"]);
  });

  it("reconstructs balances at the selected evidence sequence", () => {
    const agents: AgentBalance[] = [
      { id: "atlas", role: "product", displayName: "Atlas", balance: 60, state: "available" },
      { id: "forge", role: "backend", displayName: "Forge", balance: 40, state: "available" },
    ];
    const events = [event("escrow", 2, "ledger.transaction"), event("payout", 4, "ledger.transaction")];
    const transactions: LedgerTransaction[] = [
      { id: "escrow", eventId: "escrow", occurredAt: "", agentId: "atlas", agent: "Atlas", type: "charge", description: "lock", tokens: 0, credits: 40, fromAgent: "atlas" },
      { id: "payout", eventId: "payout", occurredAt: "", agentId: "forge", agent: "Forge", type: "reward", description: "payout", tokens: 0, credits: 20, toAgent: "forge" },
    ];

    const balances = balancesAtSequence(agents, transactions, events, 2);
    expect(balances.find(({ id }) => id === "atlas")?.balance).toBe(60);
    expect(balances.find(({ id }) => id === "forge")?.balance).toBe(20);
  });

  it("proves conservation only when recorded settlement outputs equal escrow", () => {
    const events = [
      event("escrow", 1, "ledger.transaction", { kind: "escrow", amount: 40, fromAgent: "atlas" }),
      event("forge", 2, "ledger.transaction", { kind: "payout", amount: 19, toAgent: "forge" }),
      event("aegis", 3, "ledger.transaction", { kind: "payout", amount: 5, toAgent: "aegis" }),
      event("sentinel", 4, "ledger.transaction", { kind: "payout", amount: 5, toAgent: "sentinel" }),
      event("shipwright", 5, "ledger.transaction", { kind: "payout", amount: 3, toAgent: "shipwright" }),
      event("chronicle", 6, "ledger.transaction", { kind: "payout", amount: 2, toAgent: "chronicle" }),
      event("atlas", 7, "ledger.transaction", { kind: "refund", amount: 6, toAgent: "atlas" }),
    ];

    expect(settlementProof(events)).toMatchObject({ outputTotal: 40, conserved: true });
    expect(settlementProof(events.slice(0, -1))).toMatchObject({ outputTotal: 34, conserved: false });
  });
});
