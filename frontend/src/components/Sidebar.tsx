import { Bot, Database, FileClock, PlayCircle, ScrollText, TerminalSquare } from "lucide-react";

export type Page = "runs" | "replay" | "agents" | "policies" | "ledger";

const nav = [
  { id: "runs" as const, label: "Runs", icon: FileClock },
  { id: "replay" as const, label: "Replay", icon: PlayCircle },
  { id: "agents" as const, label: "Agents", icon: Bot },
  { id: "policies" as const, label: "Policies", icon: ScrollText },
  { id: "ledger" as const, label: "Ledger", icon: Database },
];

export function Sidebar({ active, onSelect }: { active: Page; onSelect: (page: Page) => void }) {
  return (
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Open Dhurandhar overview">
        <span className="brand-mark" aria-hidden="true">D</span>
        <span className="brand-name">Dhurandhar</span>
      </a>

      <nav className="nav-list" aria-label="Primary navigation">
        {nav.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${active === id ? "is-active" : ""}`}
            onClick={() => onSelect(id)}
            aria-current={active === id ? "page" : undefined}
            aria-label={label}
          >
            <Icon size={18} strokeWidth={1.9} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="owner-switcher" aria-label="Current workspace">
        <TerminalSquare size={17} aria-hidden="true" />
        <span>
          <strong>founder@local</strong>
          <small>Owner · demo mode</small>
        </span>
      </div>
    </aside>
  );
}
