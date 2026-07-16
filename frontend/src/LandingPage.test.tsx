import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LandingPage from "./LandingPage";

const IMPLEMENTATION_THREAD = "019f693d-e649-7a91-8dd3-f2cf1a772516";
const REVIEW_THREAD = "019f6940-61f5-7ea2-85e8-d20a1afaaf6f";
const DIFF_SHA256 = "40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33";

describe("judge-facing landing page", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("states the hosted boundary before offering the replay", () => {
    render(<LandingPage />);

    expect(screen.getByRole("note", { name: "Hosted replay disclosure" })).toHaveTextContent(
      "This hosted instance runs in deterministic replay mode.",
    );
    expect(screen.getByRole("note", { name: "Hosted replay disclosure" })).toHaveTextContent(
      "It executes no model calls.",
    );
    expect(screen.getByText("FIXTURE · DETERMINISTIC")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open Change Replay/i })).toHaveAttribute("href", "/replay");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("renders the exact captured identifiers and reproduction boundary", () => {
    render(<LandingPage />);

    expect(screen.getByRole("button", { name: `Copy Implementation thread ID: ${IMPLEMENTATION_THREAD}` })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: `Copy Independent review thread ID: ${REVIEW_THREAD}` })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: `Copy diff SHA-256: ${DIFF_SHA256}` })).toBeInTheDocument();
    expect(screen.getByText(/333,511 input · 294,400 cached · 6,297 output · 2,150 reasoning/)).toBeInTheDocument();
    expect(screen.getByText(/361,206 input · 315,904 cached · 3,566 output · 2,103 reasoning/)).toBeInTheDocument();

    const command = screen.getByLabelText("Live Codex runtime command");
    expect(command).toHaveTextContent("DHURANDHAR_RUNTIME=codex");
    expect(command).toHaveTextContent("DHURANDHAR_IMPLEMENTATION_MODEL=gpt-5.6-sol");
    expect(command).toHaveTextContent("DHURANDHAR_REVIEWER_MODEL=gpt-5.6-sol");
    expect(command).toHaveTextContent("make dev-backend");
    expect(screen.getByText(/Requires Codex CLI 0.144.0\+/)).toBeInTheDocument();
  });

  it("names all eight roles and links every enforcement claim to source lines", () => {
    render(<LandingPage />);

    for (const name of ["Atlas", "Forge", "Prism", "Rivet", "Aegis", "Sentinel", "Shipwright", "Chronicle"]) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
    for (const role of [
      "Product manager",
      "Backend engineer",
      "Frontend engineer",
      "Platform engineer",
      "Adversarial reviewer",
      "QA and saboteur",
      "Release and recovery",
      "Historian",
    ]) {
      expect(screen.getByText(role)).toBeInTheDocument();
    }

    for (const label of ["Reviewer isolation", "Sentinel allowlist", "Git evidence capture", "Hash-chain verification"]) {
      expect(screen.getByRole("link", { name: new RegExp(label, "i") })).toHaveAttribute(
        "href",
        expect.stringMatching(/github\.com\/himanshu748\/dhurandhar\/blob\/main\/backend\/app\/services\/.+#L\d+/),
      );
    }
  });

  it("labels unfinished submission artifacts instead of inventing them", () => {
    render(<LandingPage />);

    expect(screen.getByRole("link", { name: /PENDING · recording guide/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /NOT TAGGED · v1.0.0 draft/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Copy feedback session ID: 019f6172-596f-7d50-a842-b839fd16af3e/i })).toBeInTheDocument();
  });
});
