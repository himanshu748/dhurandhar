import { ChevronRight } from "lucide-react";
import { useEffect, useRef } from "react";
import type { ReplayEvent } from "../types";
import { RoleMark } from "./RoleMark";
import { StatusMark } from "./StatusMark";

const time = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

export function Timeline({
  events,
  selectedId,
  cursor,
  onSelect,
}: {
  events: ReplayEvent[];
  selectedId: string;
  cursor: number;
  onSelect: (event: ReplayEvent) => void;
}) {
  const timeline = useRef<HTMLElement | null>(null);
  const selectedRow = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    const container = timeline.current;
    const row = selectedRow.current;
    if (!container || !row) return;
    const rowBottom = row.offsetTop + row.offsetHeight;
    const visibleBottom = container.scrollTop + container.clientHeight;
    if (row.offsetTop < container.scrollTop) container.scrollTop = row.offsetTop;
    else if (rowBottom > visibleBottom) container.scrollTop = rowBottom - container.clientHeight;
  }, [selectedId]);

  return (
    <section ref={timeline} className="timeline" aria-label="Run event timeline">
      {events.map((event, index) => (
        <button
          key={event.id}
          ref={selectedId === event.id ? selectedRow : undefined}
          type="button"
          className={`timeline-row ${selectedId === event.id ? "is-selected" : ""} ${index > cursor ? "is-future" : ""}`}
          onClick={() => onSelect(event)}
          aria-pressed={selectedId === event.id}
        >
          <span className="sequence">{String(event.sequence).padStart(2, "0")}</span>
          <span className="timeline-node"><StatusMark status={event.status} compact /></span>
          <time dateTime={event.occurredAt}>{time(event.occurredAt)}</time>
          <RoleMark role={event.role} />
          <span className="event-summary-cell">
            <span className="event-summary">{event.summary}</span>
            {event.auction && (
              <small className="auction-marker">
                {event.auction.status === "awarded" && event.auction.winner
                  ? `${event.auction.winner} won · ${event.auction.bidsConsidered ?? event.auction.bids.length} bids`
                  : event.auction.status === "bidding"
                    ? `${event.auction.bids.length} bids received`
                    : `${event.auction.eligibleEngineers.length} engineers eligible`}
              </small>
            )}
          </span>
          <StatusMark status={event.status} />
          <ChevronRight className="row-chevron" size={16} aria-hidden="true" />
        </button>
      ))}
    </section>
  );
}
