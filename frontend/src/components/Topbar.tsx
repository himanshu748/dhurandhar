import { ChevronDown, KeyRound, LockKeyhole, Plus } from "lucide-react";

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
  onNewObjective,
  onOperatorAccess,
}: {
  page: keyof typeof titles;
  source: "api" | "snapshot";
  operatorEnabled: boolean;
  onNewObjective: () => void;
  onOperatorAccess: () => void;
}) {
  return (
    <header className="topbar">
      <h1>{titles[page]}</h1>
      <div className="topbar-actions">
        <button className="kernel-status" type="button" title="Runtime and journal health">
          <span className={source === "api" ? "health-dot" : "health-dot snapshot"} />
          {source === "api" ? "Kernel online" : "Replay snapshot"}
        </button>
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
