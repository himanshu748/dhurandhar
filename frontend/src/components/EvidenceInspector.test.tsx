import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ReplayEvent } from "../types";
import { EvidenceInspector } from "./EvidenceInspector";

const liveEvent: ReplayEvent = {
  id: "evt-live-codex",
  sequence: 12,
  occurredAt: "2026-07-15T09:30:00Z",
  actor: "prism",
  role: "Frontend Engineer",
  type: "code.generated",
  title: "Codex implemented bounded change",
  summary: "Added provenance rendering",
  status: "success",
  rationale: "The live worktree change passed its bounded checks.",
  evidence: [],
  usage: { inputTokens: 1450, outputTokens: 620, credits: 31 },
  provenance: {
    mode: "live",
    runtime: "codex",
    requestedModel: "gpt-5.5",
    model: "gpt-5.5",
    sandbox: "workspace-write",
    threadId: "thread_live_123",
    inputTokens: 1450,
    cachedInputTokens: 700,
    outputTokens: 620,
    reasoningOutputTokens: 210,
    commands: [{ command: "npm test -- --run", status: "passed", exitCode: 0 }],
    checks: [{ command: "frontend contract", status: "passed" }],
    changedFiles: ["frontend/src/components/EvidenceInspector.tsx"],
    diff: {
      sha256: "abc123def456",
      files: ["frontend/src/components/EvidenceInspector.tsx"],
      linesAdded: 42,
      linesDeleted: 3,
      preview: "+ <section>Live provenance</section>\n- <p>Fixture only</p>",
    },
    finalMessage: "Implemented and verified the provenance panel.",
  },
};

describe("EvidenceInspector provenance", () => {
  it("renders live model identity, session, usage, outcomes, changed files, and diff proof", () => {
    render(<EvidenceInspector event={liveEvent} runMode="codex" />);

    expect(screen.getByText("Live call provenance")).toBeInTheDocument();
    expect(screen.getByText("Requested model")).toBeInTheDocument();
    expect(screen.getByText("Not emitted by JSONL")).toBeInTheDocument();
    expect(screen.getByText("gpt-5.5")).toBeInTheDocument();
    expect(screen.getByText("thread_live_123")).toBeInTheDocument();
    expect(screen.getByText("workspace-write")).toBeInTheDocument();
    expect(screen.getByText("npm test -- --run")).toBeInTheDocument();
    expect(screen.getByText("frontend contract")).toBeInTheDocument();
    expect(screen.getByText("frontend/src/components/EvidenceInspector.tsx")).toBeInTheDocument();
    expect(screen.getByText("abc123def456")).toBeInTheDocument();
    expect(screen.getByText("Implemented and verified the provenance panel.")).toBeInTheDocument();
    expect(screen.getByLabelText("Model token usage")).toHaveTextContent("1,450");
    expect(screen.getByLabelText("Model token usage")).toHaveTextContent("700");
    expect(screen.getByLabelText("Model token usage")).toHaveTextContent("620");
    expect(screen.getByLabelText("Model token usage")).toHaveTextContent("210");
  });
});
