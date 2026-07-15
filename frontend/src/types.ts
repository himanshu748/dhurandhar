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
  kind: "test" | "review" | "commit" | "deployment" | "monitor" | "policy";
  label: string;
  detail?: string;
  href?: string;
}

export interface Artifact {
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

export interface ReplayEvent {
  id: string;
  sequence: number;
  occurredAt: string;
  actor: string;
  role: string;
  type: string;
  title: string;
  summary: string;
  status: EventStatus;
  rationale: string;
  evidence: EvidenceItem[];
  artifact?: Artifact;
  usage: Usage;
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
  balance: number;
  state: "available" | "working" | "dormant";
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
