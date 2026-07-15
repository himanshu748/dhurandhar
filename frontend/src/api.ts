import { demoSnapshot } from "./data/demo";
import type {
  AgentBalance,
  Artifact,
  EvidenceItem,
  EventStatus,
  LedgerTransaction,
  ObjectiveInput,
  PolicyProposal,
  ReplayEvent,
  ReplaySnapshot,
  RunStatus,
  RunSummary,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const joinedPath = API_BASE.endsWith("/api") && path.startsWith("/api/") ? path.slice(4) : path;
  const response = await fetch(`${API_BASE}${joinedPath}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Dhurandhar API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
};

type Json = Record<string, unknown>;

interface RawObjective extends Json {
  id: string;
  run_id: string;
}

interface RawRun extends Json {
  id: string;
  objective_id: string;
  objective_title: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
}

interface RawEvent extends Json {
  id: string;
  sequence: number;
  timestamp: string;
  type: string;
  actor: string;
  summary: string;
  data: Json;
  previous_hash?: string;
  hash?: string;
}

interface RawReplay extends Json {
  run: RawRun;
  events: RawEvent[];
}

interface RawAgent extends Json {
  id: string;
  name: string;
  role: string;
  status: string;
  credits: number;
}

interface RawLedgerTransaction extends Json {
  event_id: string;
  timestamp: string;
  kind: string;
  from_agent?: string | null;
  to_agent?: string | null;
  amount: number;
  reason: string;
}

interface RawMechanism extends Json {
  id: string;
  name: string;
  description: string;
  enforcement: string;
  kind?: string;
}

interface RawPolicy extends Json {
  id: string;
  run_id: string;
  title: string;
  rationale: string;
  status: string;
  mechanisms: RawMechanism[];
  baseline_score?: number;
  candidate_score?: number;
}

const agentNames: Record<string, string> = {
  atlas: "PM Agent",
  forge: "Engineer Agent",
  aegis: "Reviewer Agent",
  sentinel: "QA Agent",
  shipwright: "Deployer Agent",
  orchestrator: "Kernel",
  ledger: "Ledger",
  "human-customer": "Founder",
  "failure-injector": "Failure Injector",
};

const eventTitles: Record<string, string> = {
  "objective.created": "Objective accepted",
  "run.started": "Autonomous run started",
  "planning.completed": "PM scoped objective",
  "task.assigned": "Implementation assigned",
  "runtime.invoked": "Implementation runtime invoked",
  "code.generated": "Engineer implemented",
  "pull_request.opened": "Change opened for review",
  "review.approved": "Reviewer approved change",
  "tests.passed": "QA verified",
  "deployment.started": "Deployment gate entered",
  "deployment.succeeded": "Deployed to production",
  "monitor.healthy": "Monitor verified release",
  "memory.updated": "Operational memory updated",
  "run.completed": "Objective completed",
  "regression.injected": "Controlled regression injected",
  "monitor.alert": "Monitor detected regression",
  "rollback.started": "Rollback started",
  "rollback.completed": "Rollback completed",
  "incident.analyzed": "Root cause identified",
  "policy.proposed": "Policy update proposed",
  "benchmark.completed": "Policy benchmark passed",
  "policy.approved": "Policy update approved",
  "policy.rejected": "Policy update rejected",
  "policy.activated": "Policy update activated",
  "policy.inherited": "Learned policy inherited",
  "ledger.transaction": "Ledger transaction recorded",
  "run.failed": "Run failed safely",
};

const titleCase = (value: string) =>
  value
    .replace(/[._-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const eventStatus = (type: string): EventStatus => {
  if (type === "monitor.alert" || type === "regression.injected" || type === "run.failed") return "regression";
  if (type.includes("blocked")) return "blocked";
  if (type === "policy.proposed") return "proposed";
  if (type.endsWith(".started") || type === "runtime.invoked") return "active";
  return "success";
};

const roleForEvent = (event: RawEvent) => {
  if (event.actor === "sentinel" && event.type.startsWith("monitor.")) return "Monitor Agent";
  if (event.actor === "sentinel" && event.type === "memory.updated") return "Policy Agent";
  return agentNames[event.actor] ?? titleCase(event.actor);
};

const evidenceForEvent = (event: RawEvent): EvidenceItem[] => {
  const evidence: EvidenceItem[] = [];
  const data = event.data ?? {};
  const add = (kind: EvidenceItem["kind"], label: string, detail?: string) =>
    evidence.push({ id: `${event.id}-${evidence.length}`, kind, label, detail });

  if (typeof data.change_id === "string") add("commit", data.change_id);
  const tests = Array.isArray(data.tests) ? data.tests : Array.isArray(data.declared_tests) ? data.declared_tests : [];
  tests.forEach((test) => add("test", String(test)));
  if (Array.isArray(data.checks)) data.checks.forEach((check) => add("review", String(check)));
  if (typeof data.version === "string") add("deployment", data.version, typeof data.url === "string" ? data.url : undefined);
  if (typeof data.restored_version === "string") add("deployment", `Restored ${data.restored_version}`);
  if (typeof data.http_status === "number") {
    const detail = typeof data.error_rate === "number" ? `${(data.error_rate * 100).toFixed(1)}% error rate` : undefined;
    add("monitor", `HTTP ${data.http_status}`, detail);
  }
  const proposal = data.proposal;
  if (proposal && typeof proposal === "object") {
    const record = proposal as Json;
    const baseline = Number(record.baseline_score ?? 0);
    const candidate = Number(record.candidate_score ?? 0);
    add("policy", `Benchmark ${baseline.toFixed(2)} → ${candidate.toFixed(2)}`);
  }
  if (event.type === "ledger.transaction" && typeof data.amount === "number") {
    add("review", `${data.kind ?? "transfer"}: ${data.amount} credits`);
  }
  if (event.type === "benchmark.completed") {
    add(
      "policy",
      `${String(data.benchmark_id ?? "policy benchmark")}: ${Number(data.baseline_score ?? 0).toFixed(2)} → ${Number(data.candidate_score ?? 0).toFixed(2)}`,
      `${Number(data.cases ?? 0)} cases · ${Number(data.critical_regressions ?? 0)} critical regressions`,
    );
  }
  return evidence;
};

const artifactForEvent = (event: RawEvent): Artifact | undefined => {
  if (!event.data || Object.keys(event.data).length === 0) return undefined;
  return {
    kind: event.type === "planning.completed" ? "plan" : "log",
    path: event.type,
    language: "json",
    content: JSON.stringify(event.data, null, 2),
  };
};

const rationaleForEvent = (event: RawEvent) => {
  const data = event.data ?? {};
  if (typeof data.root_cause === "string") return `${data.root_cause}${typeof data.lesson === "string" ? ` ${data.lesson}` : ""}`;
  if (event.type === "review.approved") return "The independent reviewer found the change bounded, testable, and safe to continue through the delivery gate.";
  if (event.type === "monitor.alert") return "Observed production health crossed the configured error-budget threshold, so the kernel moved the run into recovery.";
  if (event.type === "rollback.completed") return "Dhurandhar restored the last known-good version before proposing any change to its operating policy.";
  if (event.type === "policy.proposed") return "The incident evidence produced a benchmark-gated candidate across memory, prompt, routing, and economy—not an unreviewed self-edit.";
  return event.summary;
};

const normalizeEvent = (event: RawEvent): ReplayEvent => {
  const usage = event.data?.usage && typeof event.data.usage === "object" ? event.data.usage as Json : {};
  const inputTokens = Number(usage.input_tokens ?? 0);
  const outputTokens = Number(usage.output_tokens ?? 0);
  const credits = event.type === "ledger.transaction" ? Number(event.data.amount ?? 0) : Number(usage.credits ?? 0);
  return {
    id: event.id,
    sequence: event.sequence,
    occurredAt: event.timestamp,
    actor: event.actor,
    role: roleForEvent(event),
    type: event.type,
    title: eventTitles[event.type] ?? titleCase(event.type),
    summary: event.summary,
    status: eventStatus(event.type),
    rationale: rationaleForEvent(event),
    evidence: evidenceForEvent(event),
    artifact: artifactForEvent(event),
    usage: { inputTokens, outputTokens, credits },
    hash: event.hash,
    previousHash: event.previous_hash,
  };
};

const mapRunStatus = (status: string): RunStatus => {
  if (status === "recovered") return "recovered";
  if (status === "completed") return "completed";
  if (status === "degraded" || status === "failed") return "blocked";
  return "running";
};

const normalizeRun = (run: RawRun, events: RawEvent[]): RunSummary => {
  const started = new Date(run.started_at).getTime();
  const completed = run.completed_at ? new Date(run.completed_at).getTime() : Date.now();
  const mode = events.find((event) => event.type === "runtime.invoked")?.data.runtime === "codex" ? "codex" : "deterministic";
  const tokenCost = events.reduce((total, event) => {
    const usage = event.data?.usage && typeof event.data.usage === "object" ? event.data.usage as Json : {};
    return total + Number(usage.input_tokens ?? 0) + Number(usage.output_tokens ?? 0);
  }, 0);
  return {
    id: run.id,
    objectiveId: run.objective_id,
    objective: run.objective_title,
    status: mapRunStatus(run.status),
    startedAt: run.started_at,
    completedAt: run.completed_at ?? undefined,
    durationSeconds: Math.max(0, Math.floor((completed - started) / 1000)),
    interventions: events.filter((event) => event.actor === "human-customer" && event.type !== "objective.created").length,
    tokenCost,
    repository: "Dhurandhar control plane",
    mode,
  };
};

const normalizeAgent = (agent: RawAgent): AgentBalance => ({
  id: agent.id,
  role: agent.role.toLowerCase().includes("product") ? "product"
    : agent.role.toLowerCase().includes("review") ? "reviewer"
      : agent.role.toLowerCase().includes("implementation") ? "engineer"
        : agent.role.toLowerCase().includes("release") ? "deployer" : "qa",
  displayName: agentNames[agent.id] ?? agent.name,
  balance: agent.credits,
  state: agent.status === "idle" ? "available" : "working",
});

const normalizeTransaction = (transaction: RawLedgerTransaction): LedgerTransaction => {
  const agentId = transaction.to_agent ?? transaction.from_agent ?? "ledger";
  const type: LedgerTransaction["type"] = transaction.kind === "penalty" ? "penalty"
    : transaction.kind === "payout" || transaction.kind === "refund" || transaction.kind === "issue" ? "reward"
      : "charge";
  return {
    id: transaction.event_id,
    occurredAt: transaction.timestamp,
    agentId,
    agent: agentNames[agentId] ?? titleCase(agentId),
    type,
    description: transaction.reason,
    tokens: 0,
    credits: transaction.amount,
    eventId: transaction.event_id,
  };
};

const mechanismKinds: PolicyProposal["mechanism"][] = ["memory", "prompt", "routing", "economy"];

const normalizePolicies = (policies: RawPolicy[]): PolicyProposal[] => policies.flatMap((policy) => {
  const normalized = policy.mechanisms.map((mechanism, index) => {
    const declaredKind = mechanism.kind;
    const kind = mechanismKinds.includes(declaredKind as PolicyProposal["mechanism"])
      ? declaredKind as PolicyProposal["mechanism"]
      : mechanismKinds[index] ?? "memory";
    const status: PolicyProposal["status"] = policy.status === "approved" || policy.status === "active"
      ? "promoted"
      : policy.status === "rejected" ? "rejected" : "proposed";
    return {
      id: `${policy.id}:${mechanism.id}`,
      proposalId: policy.id,
      runId: policy.run_id,
      title: mechanism.name,
      mechanism: kind,
      status,
      baselineScore: Number(policy.baseline_score ?? 0),
      candidateScore: Number(policy.candidate_score ?? 0),
      rationale: `${mechanism.description} ${mechanism.enforcement}`,
    };
  }).sort((left, right) => mechanismKinds.indexOf(left.mechanism) - mechanismKinds.indexOf(right.mechanism));
  return normalized.map((proposal, index) => ({ ...proposal, decisionOwner: index === 0 }));
});

export const fetchReplay = async (): Promise<ReplaySnapshot> => {
  try {
    const objectives = await request<RawObjective[]>("/api/objectives");
    const runId = objectives[0]?.run_id;
    if (!runId) return demoSnapshot;

    const [replay, agents, ledger, policies] = await Promise.all([
      request<RawReplay>(`/api/replay/${encodeURIComponent(runId)}`),
      request<{ items: RawAgent[] }>("/api/agents"),
      request<{ transactions: RawLedgerTransaction[] }>("/api/ledger"),
      request<{ items: RawPolicy[] }>("/api/policies"),
    ]);
    return {
      run: normalizeRun(replay.run, replay.events),
      events: replay.events.map(normalizeEvent),
      agents: agents.items.map(normalizeAgent),
      transactions: [...ledger.transactions].reverse().map(normalizeTransaction),
      policies: normalizePolicies(policies.items),
      source: "api",
    };
  } catch {
    return demoSnapshot;
  }
};

export const createObjective = (input: ObjectiveInput) =>
  request<RawObjective>("/api/objectives", {
    method: "POST",
    body: JSON.stringify({
      title: input.title,
      description: input.description,
      acceptance_criteria: input.acceptanceCriteria,
      priority: input.priority,
    }),
  });

export const injectRegression = (runId: string) =>
  request<unknown>(`/api/runs/${encodeURIComponent(runId)}/inject-regression`, { method: "POST", body: "{}" });

export const rollbackRun = (runId: string) =>
  request<unknown>(`/api/runs/${encodeURIComponent(runId)}/rollback`, { method: "POST", body: "{}" });

export const runRecoveryDrill = async (runId: string) => {
  await injectRegression(runId);
  return rollbackRun(runId);
};

export const decidePolicy = (proposalId: string, decision: "promote" | "reject") =>
  request<unknown>(`/api/policies/proposals/${encodeURIComponent(proposalId)}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision: decision === "promote" ? "approve" : "reject", decided_by: "human-customer" }),
  });
