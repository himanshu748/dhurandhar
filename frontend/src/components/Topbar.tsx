import { ChevronDown, KeyRound, LockKeyhole, Plus, Radio } from "lucide-react";

const titles = {
  runs: "Runs",
  replay: "Change Replay",
  agents: "Agents",
  policies: "Policies",
  ledger: "Ledger",
} as const;

export function Topbar({
  page,
  source,
  operatorEnabled,
  model,
  modelLabel,
  provenance,
  sandbox,
  onNewObjective,
  onOperatorAccess,
}: {
  page: keyof typeof titles;
  source: "api" | "snapshot";
  operatorEnabled: boolean;
  model?: string;
  modelLabel?: "OBSERVED" | "REQUESTED";
  provenance: "live" | "fixture";
  sandbox?: string;
  onNewObjective: () => void;
  onOperatorAccess: () => void;
}) {
  return (
    <header className="topbar">
      <h1>{titles[page]}</h1>
      <div className="topbar-actions">
        <div className="forensic-signals" aria-label="Kernel, provenance, and model status">
          <button className="kernel-status" type="button" title="Runtime and journal health">
          <span className={source === "api" ? "health-dot" : "health-dot snapshot"} />
          <span>{source === "api" ? "Kernel online" : "Snapshot fallback"}</span>
          </button>
          <span className={`topbar-provenance is-${provenance}`}><Radio size={11} />{provenance === "live" ? "RECORDED LIVE" : "FIXTURE"}</span>
          <span className="topbar-model"><small>{modelLabel ?? "MODEL"}</small><code>{model ?? (provenance === "fixture" ? "none" : "unreported")}</code></span>
          {sandbox && <span className="topbar-model"><small>MODE</small><code>{sandbox}</code></span>}
        </div>
        <button
          className={`operator-access ${operatorEnabled ? "is-loaded" : ""}`}
          type="button"
          onClick={onOperatorAccess}
          aria-label={operatorEnabled ? "Operator token loaded" : "Read-only — load operator token"}
          title={operatorEnabled ? "Token is held in this tab's memory" : "Mutations require an operator token"}
        >
          {operatorEnabled ? <KeyRound size={14} /> : <LockKeyhole size={14} />}
          <span>{operatorEnabled ? "Token loaded" : "Read-only"}</span>
        </button>
        <button
          className="primary-action"
          type="button"
          onClick={onNewObjective}
          disabled={!operatorEnabled}
          title={operatorEnabled ? "Create a new objective" : "Load an operator token to create objectives"}
        >
          <span className="new-objective-label">New objective</span>
          <Plus size={17} aria-hidden="true" />
          <span className="button-divider" aria-hidden="true" />
          <ChevronDown size={15} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
