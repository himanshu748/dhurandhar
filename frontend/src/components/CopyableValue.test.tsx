import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CopyableValue, truncateMiddle } from "./CopyableValue";

describe("CopyableValue", () => {
  it("truncates long values from the middle without changing short values", () => {
    expect(truncateMiddle("short-value", 8, 6)).toBe("short-value");
    expect(truncateMiddle("abcdefghijklmnopqrstuvwxyz", 6, 5)).toBe("abcdef…vwxyz");
  });

  it("copies the full value while displaying a middle-out abbreviation", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    const value = "sha256:0123456789abcdefghijklmnopqrstuvwxyz";
    render(<CopyableValue value={value} label="diff hash" head={8} tail={7} />);

    const copyButton = screen.getByRole("button", { name: `Copy diff hash: ${value}` });
    expect(copyButton).toHaveAttribute("title", value);
    expect(screen.getByText(truncateMiddle(value, 8, 7))).toBeInTheDocument();

    fireEvent.click(copyButton);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(value));
    expect(await screen.findByRole("status")).toHaveTextContent("diff hash copied");
  });
});
