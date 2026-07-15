import { FlaskConical, Radio, Waypoints } from "lucide-react";
import type { ReplayEvent, RunSummary } from "../types";

type ProvenanceKind = "live-model" | "orchestration" | "fixture";

interface BadgeContent {
  kind: ProvenanceKind;
  label: string;
  description: string;
}

function badgeContent(event: ReplayEvent, runMode: RunSummary["mode"]): BadgeContent {
  const provenance = event.provenance;

  if (provenance?.mode === "live") {
    const reportedModel = provenance.model ?? "model not reported";
    return {
      kind: "live-model",
      label: `LIVE MODEL · ${reportedModel}${provenance.sandbox ? ` · ${provenance.sandbox}` : ""}`,
      description: provenance.sandbox
        ? `Direct live model evidence. Reported sandbox: ${provenance.sandbox}.`
        : "Direct live model evidence. Sandbox was not reported.",
    };
  }

  if (provenance?.mode === "deterministic" || runMode === "deterministic") {
    return {
      kind: "fixture",
      label: "FIXTURE · DETERMINISTIC",
      description: "Deterministic fixture event; no model call produced this event.",
    };
  }

  return {
    kind: "orchestration",
    label: "LIVE JOURNAL · ORCHESTRATION",
    description: "Recorded in a live Codex run; no model invocation is attached to this event.",
  };
}

export function ProvenanceBadge({
  event,
  runMode,
  className,
}: {
  event: ReplayEvent;
  runMode: RunSummary["mode"];
  className?: string;
}) {
  const content = badgeContent(event, runMode);
  const Icon = content.kind === "live-model" ? Radio : content.kind === "orchestration" ? Waypoints : FlaskConical;

  return (
    <span
      className={["provenance-badge", `provenance-badge-${content.kind}`, className].filter(Boolean).join(" ")}
      data-provenance-kind={content.kind}
      title={content.description}
      aria-label={content.description}
    >
      <Icon size={12} strokeWidth={2} aria-hidden="true" />
      <span>{content.label}</span>
    </span>
  );
}
