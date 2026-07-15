import { Check, CircleDot, CircleX, MinusCircle, TriangleAlert } from "lucide-react";
import type { EventStatus } from "../types";

const labels: Record<EventStatus, string> = {
  success: "Success",
  active: "Active",
  blocked: "Blocked",
  regression: "Regression",
  proposed: "Proposed",
  cancelled: "Cancelled",
};

export function StatusMark({ status, compact = false }: { status: EventStatus; compact?: boolean }) {
  const Icon =
    status === "success"
      ? Check
      : status === "active"
        ? CircleDot
        : status === "proposed"
          ? TriangleAlert
          : status === "cancelled"
            ? MinusCircle
            : CircleX;

  return (
    <span className={`status-mark status-${status}`} aria-label={labels[status]}>
      <Icon size={compact ? 13 : 15} strokeWidth={2.2} aria-hidden="true" />
      {!compact && <span>{labels[status]}</span>}
    </span>
  );
}
