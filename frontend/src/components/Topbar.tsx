import { ChevronDown, Plus } from "lucide-react";

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
  onNewObjective,
}: {
  page: keyof typeof titles;
  source: "api" | "snapshot";
  onNewObjective: () => void;
}) {
  return (
    <header className="topbar">
      <h1>{titles[page]}</h1>
      <div className="topbar-actions">
        <button className="kernel-status" type="button" title="Runtime and journal health">
          <span className={source === "api" ? "health-dot" : "health-dot snapshot"} />
          {source === "api" ? "Kernel online" : "Replay snapshot"}
        </button>
        <button className="primary-action" type="button" onClick={onNewObjective}>
          <span>New objective</span>
          <Plus size={17} aria-hidden="true" />
          <span className="button-divider" aria-hidden="true" />
          <ChevronDown size={15} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
