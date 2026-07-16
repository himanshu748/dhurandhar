import { afterEach, describe, expect, it, vi } from "vitest";
import { createObjective, decidePolicy, fetchReplay, runRecoveryDrill } from "./api";

const response = (payload: unknown) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
}) as Response;

afterEach(() => vi.unstubAllGlobals());

describe("Dhurandhar API adapter", () => {
  it("uses the objective run_id and normalizes the event-sourced API", async () => {
    const fetch = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
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
        baseline_score: 0,
        candidate_score: 1,
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
    for (const [, init] of fetch.mock.calls) {
      expect(new Headers(init?.headers).get("X-Dhurandhar-Operator-Token")).toBeNull();
    }
    expect(snapshot.source).toBe("api");
    expect(snapshot.run.status).toBe("recovered");
    expect(snapshot.events[0]).toMatchObject({ role: "QA & Saboteur", status: "regression", title: "Monitor detected regression" });
    expect(snapshot.policies.map((policy) => policy.mechanism)).toEqual(["memory", "prompt", "routing", "economy"]);
    expect(snapshot.transactions[0]).toMatchObject({ type: "penalty", credits: 5, tokens: 0 });
  });

  it("normalizes auctions, the eight-role roster, and live Codex provenance", async () => {
    const events = [
      { id: "evt_1", sequence: 1, timestamp: "2026-07-15T03:30:00Z", type: "auction.opened", actor: "atlas", summary: "Auction opened", data: { task: "Add provenance", bounty: 40, eligible_engineers: ["forge", "prism", "rivet"] } },
      { id: "evt_2", sequence: 2, timestamp: "2026-07-15T03:30:01Z", type: "bid.submitted", actor: "forge", summary: "Forge bid", data: { bidder: "forge", amount: 35, plan: "Backend-first plan", credibility: 0.89, evidence: ["API tests"] } },
      { id: "evt_3", sequence: 3, timestamp: "2026-07-15T03:30:02Z", type: "bid.submitted", actor: "prism", summary: "Prism bid", data: { bidder: "prism", amount: 31, plan: "UI plus browser proof", credibility: 0.96, evidence: ["UI tests"] } },
      { id: "evt_4", sequence: 4, timestamp: "2026-07-15T03:30:03Z", type: "auction.awarded", actor: "atlas", summary: "Prism won", data: { winner: "prism", amount: 31, plan: "UI plus browser proof", bids_considered: 2 } },
      { id: "evt_5", sequence: 5, timestamp: "2026-07-15T03:30:04Z", type: "runtime.invoked", actor: "prism", summary: "Codex invoked", data: { runtime: "codex", model: "gpt-5.5", sandbox: "workspace-write", agent_id: "prism", provenance: "live" } },
      {
        id: "evt_6",
        sequence: 6,
        timestamp: "2026-07-15T03:30:05Z",
        type: "code.generated",
        actor: "prism",
        summary: "Codex changed the worktree",
        data: {
          change_id: "codex_abc123",
          runtime: "codex",
          requested_model: "gpt-5.5",
          observed_model: null,
          model: "gpt-5.5",
          thread_id: "thread_abc123",
          write_mode: true,
          provenance: "live",
          usage: { input_tokens: 1200, cached_input_tokens: 500, output_tokens: 450, reasoning_output_tokens: 125 },
          commands: [{ command: "npm test -- --run", status: "passed", exit_code: 0 }],
          checks: [{ check: "frontend tests", status: "passed" }],
          files_changed: ["frontend/src/App.tsx"],
          diff: { sha256: "diff_sha_123", name_only: ["frontend/src/App.tsx"], numstat: [{ path: "frontend/src/App.tsx", additions: 10, deletions: 2, binary: false }], preview: "+ provenance" },
          final_message: "Implemented provenance.",
        },
      },
    ];
    const fetch = vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path === "/api/objectives") return response([{ id: "obj_live", run_id: "run_live" }]);
      if (path === "/api/replay/run_live") return response({
        run: { id: "run_live", objective_id: "obj_live", objective_title: "Add provenance", status: "completed", started_at: "2026-07-15T03:30:00Z", completed_at: "2026-07-15T03:31:00Z" },
        events,
      });
      if (path === "/api/agents") return response({ items: [{ id: "prism", name: "Prism", role: "Frontend engineer", status: "working", credits: 31, capabilities: ["React interfaces", "Browser verification"], personality: "Evidence-first UI", memory_count: 2, memory: ["Keep cursor synchronized"], current_task: "Add provenance", completed_actions: 4, last_seen: "2026-07-15T03:30:05Z" }] });
      if (path === "/api/ledger") return response({ transactions: [] });
      if (path === "/api/policies") return response({ items: [] });
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetch);

    const snapshot = await fetchReplay();
    const award = snapshot.events.find((event) => event.type === "auction.awarded");
    const generated = snapshot.events.find((event) => event.type === "code.generated");
    const prism = snapshot.agents.find((agent) => agent.id === "prism");

    expect(snapshot.run.mode).toBe("codex");
    expect(snapshot.agents).toHaveLength(8);
    expect(prism).toMatchObject({ displayName: "Prism", companyRole: "Frontend engineer", memoryCount: 2, lastLearning: "Keep cursor synchronized", state: "working" });
    expect(award?.auction).toMatchObject({ winnerId: "prism", winner: "Prism · Frontend Engineer", bidsConsidered: 2, status: "awarded" });
    expect(award?.auction?.bids).toHaveLength(2);
    expect(award?.auction?.bids.find((bid) => bid.winner)?.bidderId).toBe("prism");
    expect(generated?.provenance).toMatchObject({
      mode: "live",
      runtime: "codex",
      requestedModel: "gpt-5.5",
      observedModel: undefined,
      model: "gpt-5.5",
      threadId: "thread_abc123",
      inputTokens: 1200,
      cachedInputTokens: 500,
      outputTokens: 450,
      reasoningOutputTokens: 125,
      changedFiles: ["frontend/src/App.tsx"],
      diff: { sha256: "diff_sha_123", preview: "+ provenance", linesAdded: 10, linesDeleted: 2 },
    });
    expect(generated?.provenance?.commands[0]).toMatchObject({ command: "npm test -- --run", status: "passed", exitCode: 0 });
    expect(generated?.provenance?.checks[0]).toMatchObject({ command: "frontend tests", status: "passed" });
  });

  it("sends only the strict objective contract", async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => response({ id: "obj_2", run_id: "run_2" }));
    vi.stubGlobal("fetch", fetch);

    const operatorToken = "operator-token-123456789";
    await createObjective({
      title: "Harden replay",
      description: "Keep ordering deterministic.",
      acceptanceCriteria: ["Collision test passes"],
      priority: "urgent",
    }, operatorToken);

    const init = fetch.mock.calls[0][1] as RequestInit;
    expect(new Headers(init.headers).get("X-Dhurandhar-Operator-Token")).toBe(operatorToken);
    expect(JSON.parse(String(init.body))).toEqual({
      title: "Harden replay",
      description: "Keep ordering deterministic.",
      acceptance_criteria: ["Collision test passes"],
      priority: "urgent",
    });
    expect(String(init.body)).not.toContain(operatorToken);
  });

  it("translates promote to the backend approval decision", async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => response({ status: "approved" }));
    vi.stubGlobal("fetch", fetch);

    const operatorToken = "operator-token-123456789";
    await decidePolicy("policy_1", "promote", operatorToken);

    const init = fetch.mock.calls[0][1] as RequestInit;
    expect(new Headers(init.headers).get("X-Dhurandhar-Operator-Token")).toBe(operatorToken);
    expect(JSON.parse(String(init.body))).toEqual({ decision: "approve", decided_by: "human-customer" });
    expect(String(init.body)).not.toContain(operatorToken);
  });

  it("uses the in-memory operator header for both recovery mutations", async () => {
    const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => response({ status: "ok" }));
    vi.stubGlobal("fetch", fetch);
    const operatorToken = "operator-token-123456789";

    await runRecoveryDrill("run_1", operatorToken);

    expect(fetch).toHaveBeenCalledTimes(2);
    for (const [, init] of fetch.mock.calls) {
      expect(new Headers(init?.headers).get("X-Dhurandhar-Operator-Token")).toBe(operatorToken);
      expect(String(init?.body)).not.toContain(operatorToken);
    }
  });

  it("refuses a mutation before making a request when no operator token is loaded", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);

    await expect(decidePolicy("policy_1", "promote", "")).rejects.toThrow(/operator token/i);
    expect(fetch).not.toHaveBeenCalled();
  });
});
