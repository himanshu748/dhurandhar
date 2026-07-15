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

  it("stays visibly read-only until an in-memory operator token is loaded", async () => {
    render(<App />);
    const createButton = await screen.findByRole("button", { name: /new objective/i });
    expect(createButton).toBeDisabled();
    expect(screen.getByRole("button", { name: /read-only/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /read-only/i }));
    const tokenInput = screen.getByLabelText(/^operator token/i);
    expect(tokenInput).toHaveAttribute("type", "password");
    const storageWrite = vi.spyOn(Storage.prototype, "setItem");
    fireEvent.change(tokenInput, { target: { value: "operator-token-123456789" } });
    fireEvent.click(screen.getByRole("button", { name: "Load token" }));

    await waitFor(() => expect(screen.getByRole("button", { name: /operator token loaded/i })).toBeInTheDocument());
    expect(storageWrite).not.toHaveBeenCalled();
    storageWrite.mockRestore();
    expect(createButton).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /operator token loaded/i }));
    fireEvent.click(screen.getByRole("button", { name: "Forget token" }));
    await waitFor(() => expect(screen.getByRole("button", { name: /read-only/i })).toBeInTheDocument());
    expect(createButton).toBeDisabled();
  });

  it("opens the objective creation dialog after operator access is loaded", async () => {
    render(<App />);
    await screen.findByText("Build the Change Replay interface");

    fireEvent.click(screen.getByRole("button", { name: /read-only/i }));
    fireEvent.change(screen.getByLabelText(/^operator token/i), { target: { value: "operator-token-123456789" } });
    fireEvent.click(screen.getByRole("button", { name: "Load token" }));

    const createButton = await screen.findByRole("button", { name: /new objective/i });
    fireEvent.click(createButton);
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

  it("shows the complete eight-agent company with capabilities and learned memory", async () => {
    render(<App />);
    const agents = await screen.findByRole("button", { name: "Agents" });
    fireEvent.click(agents);

    expect(screen.getByRole("heading", { name: "Eight-agent company" })).toBeInTheDocument();
    for (const name of ["Atlas", "Forge", "Prism", "Rivet", "Aegis", "Sentinel", "Shipwright", "Chronicle"]) {
      expect(screen.getByRole("heading", { name })).toBeInTheDocument();
    }
    expect(screen.getByText("Browser verification")).toBeInTheDocument();
    expect(screen.getByText("Keep replay state derived from one sequence cursor.")).toBeInTheDocument();
  });

  it("replays competitive bids and the winning engineer", async () => {
    render(<App />);
    const award = await screen.findByText("Frontend implementation awarded to Prism");
    fireEvent.click(award.closest("button")!);

    expect(screen.getByRole("heading", { name: "Implementation auction awarded" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task auction" })).toBeInTheDocument();
    expect(screen.getByText("Winning engineer")).toBeInTheDocument();
    expect(screen.getAllByText("Prism · Frontend Engineer").length).toBeGreaterThan(0);
    expect(screen.getByText(/3 bids considered/)).toBeInTheDocument();
  });

  it("labels the offline replay as deterministic fallback", async () => {
    render(<App />);
    await screen.findByText("Build the Change Replay interface");
    expect(screen.getAllByText("Deterministic fallback").length).toBeGreaterThan(0);
    expect(screen.getByText(/No model call produced this event/)).toBeInTheDocument();
  });
});
