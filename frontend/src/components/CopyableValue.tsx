import { Check, Copy, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export function truncateMiddle(value: string, head = 10, tail = 8) {
  const leadingCharacters = Math.max(1, Math.floor(head));
  const trailingCharacters = Math.max(1, Math.floor(tail));
  if (value.length <= leadingCharacters + trailingCharacters + 1) return value;
  return `${value.slice(0, leadingCharacters)}…${value.slice(-trailingCharacters)}`;
}

type CopyState = "idle" | "copied" | "error";

export interface CopyableValueProps {
  value: string;
  label?: string;
  className?: string;
  head?: number;
  tail?: number;
}

export function CopyableValue({
  value,
  label = "value",
  className,
  head = 10,
  tail = 8,
}: CopyableValueProps) {
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const resetTimer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(resetTimer.current), []);

  const copy = async () => {
    window.clearTimeout(resetTimer.current);
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(value);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
    resetTimer.current = window.setTimeout(() => setCopyState("idle"), 1800);
  };

  const status = copyState === "copied" ? `${label} copied` : copyState === "error" ? `Could not copy ${label}` : "";
  const Icon = copyState === "copied" ? Check : copyState === "error" ? X : Copy;

  return (
    <span className={["copyable-value", className].filter(Boolean).join(" ")}>
      <button
        className="copyable-value-trigger"
        type="button"
        title={value}
        aria-label={`Copy ${label}: ${value}`}
        data-copy-state={copyState}
        onClick={copy}
      >
        <code>{truncateMiddle(value, head, tail)}</code>
        <Icon size={12} strokeWidth={2} aria-hidden="true" />
      </button>
      <span className="copyable-value-status" role="status" aria-live="polite" aria-atomic="true">
        {status}
      </span>
    </span>
  );
}
