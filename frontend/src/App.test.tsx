import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("Dhurandhar replay", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  });

  it("renders the captured self-hosting run and reviewer evidence", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText("Build the Change Replay interface")).toBeInTheDocument());
    expect((await screen.findAllByText("Reviewer blocked merge")).length).toBeGreaterThan(0);
    expect(await screen.findByText("test_replay_preserves_event_order")).toBeInTheDocument();
  });

  it("selects a different event from the causal timeline", async () => {
    render(<App />);
    const row = await screen.findByText("Replay endpoint breached latency contract");
    fireEvent.click(row.closest("button")!);
    expect(screen.getByRole("heading", { name: "Monitor detected regression" })).toBeInTheDocument();
  });

  it("opens the objective creation dialog", async () => {
    render(<App />);
    const createButtons = await screen.findAllByRole("button", { name: /new objective/i });
    fireEvent.click(createButtons[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText("Objective")).toBeInTheDocument();
  });

  it("keeps the cursor and evidence inspector together during keyboard seek", async () => {
    render(<App />);
    await screen.findByText("Build the Change Replay interface");

    fireEvent.keyDown(window, { key: "Home" });

    expect(screen.getByRole("slider", { name: "Replay position" })).toHaveValue("0");
    expect(screen.getByRole("heading", { name: "Brief accepted" })).toBeInTheDocument();
  });
});
