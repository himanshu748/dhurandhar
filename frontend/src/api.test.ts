import { afterEach, describe, expect, it, vi } from "vitest";
import { createObjective, decidePolicy, fetchReplay } from "./api";

const response = (payload: unknown) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
}) as Response;

afterEach(() => vi.unstubAllGlobals());

describe("Dhurandhar API adapter", () => {
  it("uses the objective run_id and normalizes the event-sourced API", async () => {
    const fetch = vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path === "/api/objectives") return response([{ id: "obj_1", run_id: "run_1" }]);
      if (path === "/api/replay/run_1") return response({
        run: {
          id: "run_1",
          objective_id: "obj_1",
          objective_title: "Ship a monitored change",
          status: "recovered",
          started_at: "2026-07-14T03:30:00Z",
          completed_at: "2026-07-14T03:31:00Z",
        },
        events: [{
          id: "evt_1",
          sequence: 1,
          timestamp: "2026-07-14T03:30:00Z",
          type: "monitor.alert",
          actor: "sentinel",
          summary: "Error budget breached",
          data: { http_status: 500, error_rate: 0.42 },
          previous_hash: "0".repeat(64),
          hash: "1".repeat(64),
        }],
      });
      if (path === "/api/agents") return response({ items: [{ id: "sentinel", name: "Sentinel", role: "QA and reliability", status: "monitoring", credits: 81 }] });
      if (path === "/api/ledger") return response({ transactions: [{ event_id: "evt_1", timestamp: "2026-07-14T03:30:00Z", kind: "penalty", from_agent: "shipwright", to_agent: "escrow", amount: 5, reason: "Escaped regression" }] });
      if (path === "/api/policies") return response({ items: [{
        id: "policy_1",
        run_id: "run_1",
        title: "Close loop",
        rationale: "Incident evidence",
        status: "proposed",
        baseline_score: 0.71,
        candidate_score: 0.94,
        mechanisms: [
          { id: "m1", kind: "memory", name: "Memory", description: "Remember incident.", enforcement: "Persist evidence." },
          { id: "m2", kind: "prompt", name: "Prompt", description: "Add a gate.", enforcement: "Require it." },
          { id: "m3", kind: "routing", name: "Routing", description: "Route to QA.", enforcement: "Block without QA." },
          { id: "m4", kind: "economy", name: "Economy", description: "Claw back credit.", enforcement: "Apply penalty." },
        ],
      }] });
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetch);

    const snapshot = await fetchReplay();

    expect(fetch).toHaveBeenCalledWith("/api/replay/run_1", expect.any(Object));
    expect(snapshot.source).toBe("api");
    expect(snapshot.run.status).toBe("recovered");
    expect(snapshot.events[0]).toMatchObject({ role: "Monitor Agent", status: "regression", title: "Monitor detected regression" });
    expect(snapshot.policies.map((policy) => policy.mechanism)).toEqual(["memory", "prompt", "routing", "economy"]);
    expect(snapshot.transactions[0]).toMatchObject({ type: "penalty", credits: 5, tokens: 0 });
  });

  it("sends only the strict objective contract", async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => response({ id: "obj_2", run_id: "run_2" }));
    vi.stubGlobal("fetch", fetch);

    await createObjective({
      title: "Harden replay",
      description: "Keep ordering deterministic.",
      acceptanceCriteria: ["Collision test passes"],
      priority: "urgent",
    });

    const init = fetch.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({
      title: "Harden replay",
      description: "Keep ordering deterministic.",
      acceptance_criteria: ["Collision test passes"],
      priority: "urgent",
    });
  });

  it("translates promote to the backend approval decision", async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => response({ status: "approved" }));
    vi.stubGlobal("fetch", fetch);

    await decidePolicy("policy_1", "promote");

    const init = fetch.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({ decision: "approve", decided_by: "human-customer" });
  });
});
