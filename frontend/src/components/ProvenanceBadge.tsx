import { FlaskConical, Radio, Waypoints } from "lucide-react";
import type { ReplayEvent, RunSummary } from "../types";

type ProvenanceKind = "live-model" | "orchestration" | "fixture";

interface BadgeContent {
  kind: ProvenanceKind;
  label: string;
  description: string;
}

function badgeContent(event: ReplayEvent | undefined, runMode: RunSummary["mode"]): BadgeContent {
  const provenance = event?.provenance;

  if (provenance?.mode === "live") {
    const observed = provenance.observedModel;
    const requested = provenance.requestedModel ?? provenance.model;
    const displayedModel = observed ?? requested ?? "model not reported";
    const proof = observed ? "OBSERVED" : requested ? "REQUESTED" : "UNREPORTED";
    return {
      kind: "live-model",
      label: `LIVE CALL · ${proof} ${displayedModel}${provenance.sandbox ? ` · ${provenance.sandbox}` : ""}`,
      description: observed
        ? `Live call with stream-observed model ${displayedModel}${provenance.sandbox ? ` and reported sandbox ${provenance.sandbox}` : ""}.`
        : requested
          ? `Live call requested model ${displayedModel} through the CLI; the JSONL stream did not echo a model${provenance.sandbox ? `. Reported sandbox: ${provenance.sandbox}` : ""}.`
          : "Live call evidence; no model identifier was reported.",
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
  event?: ReplayEvent;
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
