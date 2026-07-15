import { demoSnapshot } from "./data/demo";
import { mergeCompanyRoster } from "./data/roster";
import type {
  AgentBalance,
  Artifact,
  CommandOutcome,
  EvidenceItem,
  EventStatus,
  LedgerTransaction,
  ModelProvenance,
  ObjectiveInput,
  PolicyProposal,
  ReplayEvent,
  ReplaySnapshot,
  ReviewEvidence,
  RunStatus,
  RunSummary,
  TaskAuction,
  TaskBid,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const OPERATOR_HEADER = "X-Dhurandhar-Operator-Token";

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const joinedPath = API_BASE.endsWith("/api") && path.startsWith("/api/") ? path.slice(4) : path;
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${joinedPath}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    throw new Error(`Dhurandhar API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
};

const mutate = <T>(path: string, operatorToken: string, init: RequestInit): Promise<T> => {
  const token = operatorToken.trim();
  if (!token) return Promise.reject(new Error("Load an operator token before changing company state."));
  const headers = new Headers(init.headers);
  headers.set(OPERATOR_HEADER, token);
  return request<T>(path, {
    ...init,
    headers,
  });
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
  capabilities?: unknown;
  personality?: string;
  memory_count?: number;
  memory?: unknown;
  memory_references?: unknown;
  last_learning?: string;
  current_task?: string | null;
  completed_actions?: number;
  last_seen?: string | null;
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
  atlas: "Product Manager",
  forge: "Backend Engineer",
  prism: "Frontend Engineer",
  rivet: "Platform Engineer",
  aegis: "Adversarial Reviewer",
  sentinel: "QA & Saboteur",
  shipwright: "Release & Recovery",
  chronicle: "Historian",
  orchestrator: "Kernel",
  ledger: "Ledger",
  "human-customer": "Founder",
  "failure-injector": "Failure Injector",
};

const agentCodenames: Record<string, string> = {
  atlas: "Atlas",
  forge: "Forge",
  prism: "Prism",
  rivet: "Rivet",
  aegis: "Aegis",
  sentinel: "Sentinel",
  shipwright: "Shipwright",
  chronicle: "Chronicle",
};

const eventTitles: Record<string, string> = {
  "objective.created": "Objective accepted",
  "run.started": "Autonomous run started",
  "planning.completed": "PM scoped objective",
  "auction.opened": "Implementation auction opened",
  "bid.submitted": "Engineer submitted bid",
  "auction.awarded": "Implementation auction awarded",
  "task.assigned": "Implementation assigned",
  "runtime.invoked": "Implementation runtime invoked",
  "code.generated": "Engineer implemented",
  "pull_request.opened": "Change opened for review",
  "review.completed": "Reviewer completed evidence check",
  "review.approved": "Reviewer approved change",
  "tests.passed": "QA verified",
  "tests.unverified": "Checks require human verification",
  "deployment.started": "Deployment gate entered",
  "deployment.succeeded": "Promoted to demo environment",
  "monitor.healthy": "Monitor verified release",
  "memory.updated": "Operational memory updated",
  "memory.recalled": "Prior learning recalled",
  "changelog.written": "Historian recorded the change",
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

const asRecord = (value: unknown): Json | undefined =>
  value && typeof value === "object" && !Array.isArray(value) ? value as Json : undefined;

const asString = (value: unknown): string | undefined =>
  typeof value === "string" && value.trim() ? value : undefined;

const stringList = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.flatMap((item) => {
      if (typeof item === "string") return item.trim() ? [item] : [];
      const record = asRecord(item);
      const label = asString(record?.label) ?? asString(record?.name) ?? asString(record?.path) ?? asString(record?.summary);
      return label ? [label] : [];
    })
    : [];

const agentLabel = (agentId: string) => agentNames[agentId] ?? titleCase(agentId);
const agentIdentity = (agentId: string) => agentCodenames[agentId]
  ? `${agentCodenames[agentId]} · ${agentLabel(agentId)}`
  : agentLabel(agentId);

const normalizeOutcome = (value: unknown, fallbackStatus = "reported"): CommandOutcome | undefined => {
  if (typeof value === "string") return { command: value, status: fallbackStatus };
  const record = asRecord(value);
  if (!record) return undefined;
  const argv = Array.isArray(record.argv) ? stringList(record.argv).join(" ") : undefined;
  const command = asString(record.command) ?? argv ?? asString(record.allowlist_id) ?? asString(record.check) ?? asString(record.name) ?? asString(record.label);
  if (!command) return undefined;
  const exitCode = typeof record.exit_code === "number" ? record.exit_code
    : typeof record.exitCode === "number" ? record.exitCode : undefined;
  return {
    command,
    status: asString(record.status) ?? (exitCode === undefined ? fallbackStatus : exitCode === 0 ? "passed" : "failed"),
    exitCode,
    detail: asString(record.detail) ?? asString(record.output) ?? asString(record.summary),
  };
};

const normalizeOutcomes = (value: unknown, fallbackStatus?: string): CommandOutcome[] =>
  Array.isArray(value)
    ? value.flatMap((item) => {
      const outcome = normalizeOutcome(item, fallbackStatus);
      return outcome ? [outcome] : [];
    })
    : [];

const eventStatus = (type: string): EventStatus => {
  if (type === "tests.unverified") return "blocked";
  if (type === "monitor.alert" || type === "regression.injected" || type === "run.failed") return "regression";
  if (type.includes("blocked")) return "blocked";
  if (type === "policy.proposed") return "proposed";
  if (type.endsWith(".started") || type === "runtime.invoked" || type === "auction.opened" || type === "bid.submitted") return "active";
  return "success";
};

const roleForEvent = (event: RawEvent) => {
  return agentLabel(event.actor);
};

const provenanceForEvent = (event: RawEvent): ModelProvenance | undefined => {
  const data = event.data ?? {};
  const declared = data.provenance;
  const declaredRecord = asRecord(declared);
  const runtime = asString(data.runtime) ?? asString(declaredRecord?.runtime);
  const model = asString(data.model) ?? asString(declaredRecord?.model);
  const threadId = asString(data.thread_id) ?? asString(declaredRecord?.thread_id);
  const sessionId = asString(data.session_id) ?? asString(declaredRecord?.session_id);
  const hasModelBoundary = ["runtime.invoked", "code.generated", "review.completed"].includes(event.type)
    || Boolean(runtime || model || threadId || sessionId);
  if (!hasModelBoundary) return undefined;

  const declaration = typeof declared === "string"
    ? declared.toLowerCase()
    : (asString(declaredRecord?.mode) ?? asString(declaredRecord?.kind) ?? "").toLowerCase();
  const deterministic = runtime === "deterministic"
    || declaration.includes("deterministic")
    || declaration.includes("fixture")
    || declaration.includes("offline");
  const usage = asRecord(data.usage) ?? asRecord(declaredRecord?.usage) ?? {};
  const diff = asRecord(data.diff) ?? asRecord(declaredRecord?.diff);
  const numstat = Array.isArray(diff?.numstat) ? diff.numstat.flatMap((item) => {
    const record = asRecord(item);
    return record ? [record] : [];
  }) : [];
  const sumNumstat = (key: "additions" | "deletions") => numstat.reduce(
    (total, item) => total + (typeof item[key] === "number" ? Number(item[key]) : 0),
    0,
  );
  const changedFiles = [...new Set([
    ...stringList(data.files_changed),
    ...stringList(data.file_changes),
    ...stringList(declaredRecord?.files_changed),
    ...stringList(diff?.files),
    ...stringList(diff?.name_only),
  ])];
  const diffPreview = asString(diff?.preview);
  const commands = normalizeOutcomes(data.commands ?? declaredRecord?.commands);
  const explicitChecks = normalizeOutcomes(
    data.check_outcomes ?? data.checks ?? declaredRecord?.check_outcomes ?? declaredRecord?.checks,
  );
  const checks = explicitChecks.length ? explicitChecks : commands.filter((outcome) =>
    /(test|pytest|vitest|lint|build|typecheck|tsc)/i.test(outcome.command),
  );

  const explicitWriteMode = data.write_mode === true ? "workspace-write"
    : data.write_mode === false ? "read-only"
      : declaredRecord?.write_mode === true ? "workspace-write"
        : declaredRecord?.write_mode === false ? "read-only" : undefined;

  return {
    mode: deterministic ? "deterministic" : "live",
    runtime,
    model,
    sandbox: asString(data.sandbox) ?? asString(declaredRecord?.sandbox) ?? explicitWriteMode,
    threadId,
    sessionId,
    inputTokens: Number(usage.input_tokens ?? 0),
    cachedInputTokens: Number(usage.cached_input_tokens ?? 0),
    outputTokens: Number(usage.output_tokens ?? 0),
    reasoningOutputTokens: Number(usage.reasoning_output_tokens ?? 0),
    commands,
    checks,
    changedFiles,
    diff: diff ? {
      sha256: asString(diff.sha256),
      files: stringList(diff.files).length ? stringList(diff.files) : stringList(diff.name_only).length ? stringList(diff.name_only) : changedFiles,
      linesAdded: typeof diff.lines_added === "number" ? diff.lines_added : numstat.length ? sumNumstat("additions") : undefined,
      linesDeleted: typeof diff.lines_deleted === "number" ? diff.lines_deleted : numstat.length ? sumNumstat("deletions") : undefined,
      preview: diffPreview,
    } : undefined,
    finalMessage: asString(data.final_message) ?? asString(declaredRecord?.final_message),
  };
};

const bidFromEvent = (event: RawEvent): TaskBid => {
  const data = event.data ?? {};
  const bidderId = asString(data.bidder) ?? event.actor;
  return {
    bidderId,
    bidder: agentIdentity(bidderId),
    amount: Number(data.amount ?? 0),
    plan: asString(data.plan),
    credibility: typeof data.credibility === "number" ? data.credibility : undefined,
    evidence: stringList(data.evidence),
  };
};

const auctionSnapshot = (auction: TaskAuction): TaskAuction => ({
  ...auction,
  eligibleEngineers: [...auction.eligibleEngineers],
  bids: auction.bids.map((bid) => ({ ...bid, evidence: [...bid.evidence] })),
});

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
    add(
      "policy",
      `Structural coverage ${baseline.toFixed(2)} → ${candidate.toFixed(2)}`,
      "Deterministic structure check; not efficacy evidence",
    );
  }
  if (event.type === "ledger.transaction" && typeof data.amount === "number") {
    add("review", `${data.kind ?? "transfer"}: ${data.amount} credits`);
  }
  if (event.type === "benchmark.completed") {
    add(
      "policy",
      `Structural coverage: ${Number(data.baseline_score ?? 0).toFixed(2)} → ${Number(data.candidate_score ?? 0).toFixed(2)}`,
      `${Number(data.cases ?? 0)} required control kinds · structure only, not efficacy`,
    );
  }
  if (event.type === "auction.opened" && typeof data.bounty === "number") {
    add("review", `${data.bounty} credit implementation bounty`, `${stringList(data.eligible_engineers).length} eligible engineers`);
  }
  if (event.type === "bid.submitted") {
    add("review", `${agentLabel(asString(data.bidder) ?? event.actor)} bid ${Number(data.amount ?? 0)} credits`, asString(data.plan));
  }
  if (event.type === "auction.awarded") {
    add("review", `Winner: ${agentLabel(asString(data.winner) ?? "unknown")}`, `${Number(data.bids_considered ?? 0)} bids considered`);
  }
  const provenance = provenanceForEvent(event);
  if (provenance?.mode === "live") {
    add("review", provenance.model ? `Live model: ${provenance.model}` : "Live model invocation", provenance.threadId ?? provenance.sessionId);
  } else if (provenance?.mode === "deterministic") {
    add("review", "Deterministic fallback", "No model call was made");
  }
  return evidence;
};

const artifactForEvent = (event: RawEvent): Artifact | undefined => {
  if (!event.data || Object.keys(event.data).length === 0) return undefined;
  const diff = asRecord(event.data.diff);
  const preview = asString(diff?.preview);
  if (preview) {
    return {
      kind: "diff",
      path: (stringList(diff?.files).length ? stringList(diff?.files) : stringList(diff?.name_only)).join(", ") || "Codex worktree diff",
      language: "diff",
      content: preview,
    };
  }
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
  if (event.type === "monitor.alert") return "The controlled release-health signal crossed the configured error-budget threshold, so the kernel moved the run into recovery.";
  if (event.type === "rollback.completed") return "Dhurandhar restored the last known-good version before proposing any change to its operating policy.";
  if (event.type === "policy.proposed") return "The incident evidence produced four runtime-backed controls across memory, prompt, routing, and economy. A deterministic check covers structure only; operator approval is still required.";
  if (event.type === "auction.opened") return `Atlas opened a bounded implementation bounty to ${stringList(data.eligible_engineers).length} eligible engineers.`;
  if (event.type === "bid.submitted") return asString(data.plan) ?? "The engineer submitted a priced implementation plan with credibility evidence.";
  if (event.type === "auction.awarded") return `${agentLabel(asString(data.winner) ?? "unknown")} won after ${Number(data.bids_considered ?? 0)} bids were compared.`;
  if (event.type === "review.completed") {
    const findings = stringList(data.findings);
    return findings.length ? findings.join(" ") : `Reviewer verdict: ${asString(data.verdict) ?? "recorded"}.`;
  }
  return event.summary;
};

const reviewForEvent = (event: RawEvent): ReviewEvidence | undefined => {
  const data = event.data ?? {};
  const verdict = asString(data.verdict) ?? (event.type === "review.approved" ? "approved" : undefined);
  const findings = Array.isArray(data.findings) ? data.findings.flatMap((item) => {
    if (typeof item === "string") return [{ severity: "unreported", summary: item }];
    const finding = asRecord(item);
    if (!finding) return [];
    const summary = asString(finding.summary) ?? asString(finding.message) ?? asString(finding.detail);
    if (!summary) return [];
    return [{
      severity: asString(finding.severity) ?? "unreported",
      summary,
      file: asString(finding.file) ?? asString(finding.path),
      line: typeof finding.line === "number" ? finding.line : undefined,
    }];
  }) : [];
  return verdict || findings.length ? { verdict, findings } : undefined;
};

const normalizeEvent = (event: RawEvent): ReplayEvent => {
  const usage = event.data?.usage && typeof event.data.usage === "object" ? event.data.usage as Json : {};
  const inputTokens = Number(usage.input_tokens ?? 0);
  const outputTokens = Number(usage.output_tokens ?? 0);
  const credits = event.type === "ledger.transaction" ? Number(event.data.amount ?? 0) : Number(usage.credits ?? 0);
  const status = event.type === "review.completed" && event.data.verdict === "changes_requested"
    ? "blocked" as const
    : eventStatus(event.type);
  return {
    id: event.id,
    sequence: event.sequence,
    occurredAt: event.timestamp,
    actor: event.actor,
    role: roleForEvent(event),
    type: event.type,
    title: eventTitles[event.type] ?? titleCase(event.type),
    summary: event.summary,
    status,
    rationale: rationaleForEvent(event),
    evidence: evidenceForEvent(event),
    artifact: artifactForEvent(event),
    usage: { inputTokens, outputTokens, credits },
    provenance: provenanceForEvent(event),
    review: reviewForEvent(event),
    ledger: event.type === "ledger.transaction" && typeof event.data.amount === "number" ? {
      kind: asString(event.data.kind) ?? "unreported",
      amount: Number(event.data.amount),
      fromAgent: asString(event.data.from_agent),
      toAgent: asString(event.data.to_agent),
      reason: asString(event.data.reason),
    } : undefined,
    checks: normalizeOutcomes(event.data.check_outcomes ?? event.data.checks),
    hash: event.hash,
    previousHash: event.previous_hash,
  };
};

const normalizeEvents = (events: RawEvent[]): ReplayEvent[] => {
  let auction: TaskAuction | undefined;
  return events.map((event) => {
    const data = event.data ?? {};
    if (event.type === "auction.opened") {
      auction = {
        task: asString(data.task) ?? "Implementation task",
        bounty: typeof data.bounty === "number" ? data.bounty : undefined,
        eligibleEngineers: stringList(data.eligible_engineers),
        bids: [],
        status: "opened",
      };
    } else if (event.type === "bid.submitted") {
      auction ??= {
        task: asString(data.task) ?? "Implementation task",
        eligibleEngineers: [],
        bids: [],
        status: "bidding",
      };
      const bid = bidFromEvent(event);
      const existing = auction.bids.findIndex((item) => item.bidderId === bid.bidderId);
      if (existing >= 0) auction.bids[existing] = bid;
      else auction.bids.push(bid);
      auction.status = "bidding";
    } else if (event.type === "auction.awarded") {
      const winnerId = asString(data.winner) ?? "unknown";
      auction ??= {
        task: asString(data.task) ?? "Implementation task",
        eligibleEngineers: [],
        bids: [],
        status: "awarded",
      };
      auction.winnerId = winnerId;
      auction.winner = agentIdentity(winnerId);
      auction.winningAmount = typeof data.amount === "number" ? data.amount : undefined;
      auction.winningPlan = asString(data.plan);
      auction.bidsConsidered = typeof data.bids_considered === "number" ? data.bids_considered : auction.bids.length;
      auction.status = "awarded";
      auction.bids = auction.bids.map((bid) => ({ ...bid, winner: bid.bidderId === winnerId }));
      if (!auction.bids.some((bid) => bid.bidderId === winnerId)) {
        auction.bids.push({
          bidderId: winnerId,
          bidder: agentIdentity(winnerId),
          amount: Number(data.amount ?? 0),
          plan: asString(data.plan),
          evidence: [],
          winner: true,
        });
      }
    } else if (event.type === "task.assigned" && !auction) {
      const winnerId = asString(data.assignee) ?? "unknown";
      auction = {
        task: asString(data.task) ?? "Implementation task",
        bounty: typeof data.bounty === "number" ? data.bounty : undefined,
        eligibleEngineers: [],
        bids: [],
        winnerId,
        winner: agentIdentity(winnerId),
        winningAmount: typeof data.bounty === "number" ? data.bounty : undefined,
        bidsConsidered: 0,
        status: "awarded",
      };
    }

    const normalized = normalizeEvent(event);
    if (auction && ["auction.opened", "bid.submitted", "auction.awarded", "task.assigned", "runtime.invoked", "code.generated"].includes(event.type)) {
      normalized.auction = auctionSnapshot(auction);
    }
    return normalized;
  });
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
  const mode = events.some((event) => provenanceForEvent(event)?.mode === "live") ? "codex" : "deterministic";
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

const agentRole = (role: string): string => {
  const normalized = role.toLowerCase();
  if (normalized.includes("product")) return "product";
  if (normalized.includes("frontend")) return "frontend";
  if (normalized.includes("backend") || normalized.includes("implementation")) return "backend";
  if (normalized.includes("platform")) return "platform";
  if (normalized.includes("review")) return "reviewer";
  if (normalized.includes("release") || normalized.includes("recovery")) return "release";
  if (normalized.includes("histor") || normalized.includes("document")) return "historian";
  return "qa";
};

const agentState = (status: string): AgentBalance["state"] => {
  if (status === "idle" || status === "available") return "available";
  if (["bidding", "working", "reviewing", "testing", "deploying", "monitoring", "documenting", "dormant"].includes(status)) {
    return status as AgentBalance["state"];
  }
  return "working";
};

const normalizeAgent = (agent: RawAgent): AgentBalance => {
  const rawMemory = Array.isArray(agent.memory_references) ? agent.memory_references : Array.isArray(agent.memory) ? agent.memory : [];
  const memoryReferences = rawMemory.flatMap((item, index) => {
    if (typeof item === "string") return [{ id: `${agent.id}-memory-${index}`, label: item }];
    const record = asRecord(item);
    const label = asString(record?.label) ?? asString(record?.summary) ?? asString(record?.memory);
    return label ? [{
      id: asString(record?.id) ?? `${agent.id}-memory-${index}`,
      label,
      eventId: asString(record?.event_id),
    }] : [];
  });
  return {
    id: agent.id,
    role: agentRole(agent.role),
    displayName: agent.name,
    companyRole: agent.role,
    balance: agent.credits,
    state: agentState(agent.status),
    capabilities: stringList(agent.capabilities),
    personality: agent.personality,
    memoryCount: typeof agent.memory_count === "number" ? agent.memory_count : memoryReferences.length,
    memoryReferences,
    lastLearning: agent.last_learning ?? memoryReferences.at(-1)?.label,
    currentTask: agent.current_task ?? undefined,
    completedActions: agent.completed_actions,
    lastSeen: agent.last_seen ?? undefined,
    reported: true,
  };
};

const normalizeTransaction = (transaction: RawLedgerTransaction): LedgerTransaction => {
  const agentId = transaction.to_agent ?? transaction.from_agent ?? "ledger";
  const type: LedgerTransaction["type"] = transaction.kind === "penalty" ? "penalty"
    : transaction.kind === "clawback" ? "clawback"
      : ["payout", "refund", "issue", "salary"].includes(transaction.kind) ? "reward"
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
    kind: transaction.kind,
    fromAgent: transaction.from_agent ?? undefined,
    toAgent: transaction.to_agent ?? undefined,
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
      events: normalizeEvents(replay.events),
      agents: mergeCompanyRoster(agents.items.map(normalizeAgent)),
      transactions: [...ledger.transactions].reverse().map(normalizeTransaction),
      policies: normalizePolicies(policies.items),
      source: "api",
    };
  } catch {
    return demoSnapshot;
  }
};

export const createObjective = (input: ObjectiveInput, operatorToken: string) =>
  mutate<RawObjective>("/api/objectives", operatorToken, {
    method: "POST",
    body: JSON.stringify({
      title: input.title,
      description: input.description,
      acceptance_criteria: input.acceptanceCriteria,
      priority: input.priority,
    }),
  });

export const injectRegression = (runId: string, operatorToken: string) =>
  mutate<unknown>(`/api/runs/${encodeURIComponent(runId)}/inject-regression`, operatorToken, { method: "POST", body: "{}" });

export const rollbackRun = (runId: string, operatorToken: string) =>
  mutate<unknown>(`/api/runs/${encodeURIComponent(runId)}/rollback`, operatorToken, { method: "POST", body: "{}" });

export const runRecoveryDrill = async (runId: string, operatorToken: string) => {
  await injectRegression(runId, operatorToken);
  return rollbackRun(runId, operatorToken);
};

export const decidePolicy = (proposalId: string, decision: "promote" | "reject", operatorToken: string) =>
  mutate<unknown>(`/api/policies/proposals/${encodeURIComponent(proposalId)}/decision`, operatorToken, {
    method: "POST",
    body: JSON.stringify({ decision: decision === "promote" ? "approve" : "reject", decided_by: "human-customer" }),
  });
