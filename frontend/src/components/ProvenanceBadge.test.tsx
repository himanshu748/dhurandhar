import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ReplayEvent } from "../types";
import { ProvenanceBadge } from "./ProvenanceBadge";

const event = (provenance?: ReplayEvent["provenance"]): ReplayEvent => ({
  id: "evt-test",
  sequence: 1,
  occurredAt: "2026-07-15T03:30:00Z",
  actor: "Prism",
  role: "Frontend Engineer",
  type: "code.generated",
  title: "Evidence captured",
  summary: "Evidence captured",
  status: "success",
  rationale: "Test fixture",
  evidence: [],
  usage: { inputTokens: 0, outputTokens: 0, credits: 0 },
  provenance,
});

const liveProvenance: NonNullable<ReplayEvent["provenance"]> = {
  mode: "live",
  model: "gpt-5.5",
  inputTokens: 120,
  cachedInputTokens: 40,
  outputTokens: 20,
  reasoningOutputTokens: 5,
  commands: [],
  checks: [],
  changedFiles: [],
};

describe("ProvenanceBadge", () => {
  it("shows only the sandbox value actually reported by a live model event", () => {
    const { rerender } = render(
      <ProvenanceBadge event={event({ ...liveProvenance, sandbox: "danger-full-access" })} runMode="codex" />,
    );
    expect(screen.getByText("LIVE MODEL · gpt-5.5 · danger-full-access")).toBeInTheDocument();

    rerender(<ProvenanceBadge event={event(liveProvenance)} runMode="codex" />);
    expect(screen.getByText("LIVE MODEL · gpt-5.5")).toBeInTheDocument();
    expect(screen.queryByText(/workspace-write/i)).not.toBeInTheDocument();
  });

  it("labels a non-model Codex event as live orchestration", () => {
    render(<ProvenanceBadge event={event()} runMode="codex" />);
    expect(screen.getByText("LIVE JOURNAL · ORCHESTRATION")).toBeInTheDocument();
    expect(screen.getByLabelText(/no model invocation is attached/i)).toHaveAttribute(
      "data-provenance-kind",
      "orchestration",
    );
  });

  it("renders deterministic evidence as a visibly distinct fixture", () => {
    render(<ProvenanceBadge event={event()} runMode="deterministic" />);
    expect(screen.getByText("FIXTURE · DETERMINISTIC")).toBeInTheDocument();
    expect(screen.getByLabelText(/no model call produced this event/i)).toHaveAttribute(
      "data-provenance-kind",
      "fixture",
    );
  });
});
