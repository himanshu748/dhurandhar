export type EventStatus =
  | "success"
  | "active"
  | "blocked"
  | "regression"
  | "proposed"
  | "cancelled";

export type RunStatus = "running" | "blocked" | "deployed" | "recovered" | "completed";

export interface EvidenceItem {
  id: string;
  /** Nested evidence category. Replay events themselves are discriminated by ReplayEvent.type. */
  kind: "test" | "review" | "commit" | "deployment" | "monitor" | "policy";
  label: string;
  detail?: string;
  href?: string;
}

export interface Artifact {
  /** Nested artifact category. Replay events themselves are discriminated by ReplayEvent.type. */
  kind: "diff" | "plan" | "command" | "log";
  path?: string;
  language?: string;
  content: string;
}

export interface Usage {
  inputTokens: number;
  outputTokens: number;
  credits: number;
}

export interface MemoryReference {
  id: string;
  label: string;
  eventId?: string;
}

export interface CommandOutcome {
  command: string;
  status: string;
  exitCode?: number;
  detail?: string;
}

export interface DiffProvenance {
  sha256?: string;
  files: string[];
  linesAdded?: number;
  linesDeleted?: number;
  preview?: string;
}

export interface ModelProvenance {
  mode: "live" | "deterministic";
  runtime?: string;
  requestedModel?: string;
  observedModel?: string;
  /** Backward-compatible display value; requestedModel/observedModel carry proof semantics. */
  model?: string;
  sandbox?: string;
  threadId?: string;
  sessionId?: string;
  inputTokens: number;
  cachedInputTokens: number;
  outputTokens: number;
  reasoningOutputTokens: number;
  commands: CommandOutcome[];
  checks: CommandOutcome[];
  changedFiles: string[];
  diff?: DiffProvenance;
  finalMessage?: string;
}

export interface TaskBid {
  bidderId: string;
  bidder: string;
  amount: number;
  plan?: string;
  credibility?: number;
  evidence: string[];
  winner?: boolean;
}

export interface TaskAuction {
  task: string;
  bounty?: number;
  eligibleEngineers: string[];
  bids: TaskBid[];
  winnerId?: string;
  winner?: string;
  winningAmount?: number;
  winningPlan?: string;
  bidsConsidered?: number;
  status: "opened" | "bidding" | "awarded";
}

export interface ReviewFinding {
  severity: string;
  summary: string;
  file?: string;
  line?: number;
}

export interface ReviewEvidence {
  verdict?: string;
  findings: ReviewFinding[];
}

export interface LedgerEvidence {
  /** Nested ledger transaction category carried by a ledger.transaction event. */
  kind: string;
  amount: number;
  fromAgent?: string;
  toAgent?: string;
  reason?: string;
}

export interface ReplayEvent {
  id: string;
  sequence: number;
  occurredAt: string;
  actor: string;
  role: string;
  /** Canonical API event discriminator. */
  type: string;
  title: string;
  summary: string;
  status: EventStatus;
  rationale: string;
  evidence: EvidenceItem[];
  artifact?: Artifact;
  usage: Usage;
  provenance?: ModelProvenance;
  auction?: TaskAuction;
  review?: ReviewEvidence;
  ledger?: LedgerEvidence;
  checks?: CommandOutcome[];
  hash?: string;
  previousHash?: string;
}

export interface RunSummary {
  id: string;
  objectiveId?: string;
  objective: string;
  status: RunStatus;
  startedAt: string;
  completedAt?: string;
  durationSeconds: number;
  interventions: number;
  tokenCost: number;
  repository: string;
  mode: "deterministic" | "codex";
}

export interface AgentBalance {
  id: string;
  role: string;
  displayName: string;
  companyRole?: string;
  balance: number;
  state:
    | "available"
    | "bidding"
    | "working"
    | "reviewing"
    | "testing"
    | "deploying"
    | "monitoring"
    | "documenting"
    | "dormant";
  capabilities?: string[];
  personality?: string;
  memoryCount?: number;
  memoryReferences?: MemoryReference[];
  lastLearning?: string;
  currentTask?: string;
  completedActions?: number;
  lastSeen?: string;
  reported?: boolean;
  color?: string;
}

export interface LedgerTransaction {
  id: string;
  occurredAt: string;
  agentId: string;
  agent: string;
  type: "charge" | "reward" | "penalty" | "clawback";
  description: string;
  tokens: number;
  credits: number;
  eventId?: string;
  /** Nested ledger category; not an event discriminator. */
  kind?: string;
  fromAgent?: string;
  toAgent?: string;
}

export interface PolicyProposal {
  id: string;
  proposalId?: string;
  decisionOwner?: boolean;
  runId: string;
  title: string;
  mechanism: "memory" | "prompt" | "routing" | "economy";
  status: "proposed" | "promoted" | "rejected";
  baselineScore: number;
  candidateScore: number;
  rationale: string;
}

export interface ReplaySnapshot {
  run: RunSummary;
  events: ReplayEvent[];
  agents: AgentBalance[];
  transactions: LedgerTransaction[];
  policies: PolicyProposal[];
  source: "api" | "snapshot";
}

export interface ObjectiveInput {
  title: string;
  description: string;
  acceptanceCriteria: string[];
  priority: "standard" | "urgent";
}
