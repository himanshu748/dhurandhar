import { Check, Copy, ExternalLink, FileCode2, X } from "lucide-react";
import { useState } from "react";
import type { ReplayEvent } from "../types";

const time = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

function Diff({ content }: { content: string }) {
  return (
    <pre className="diff-view">
      {content.split("\n").map((line, index) => (
        <span key={`${index}-${line}`} className={line.startsWith("+") ? "diff-add" : line.startsWith("-") ? "diff-remove" : ""}>
          {line || " "}
        </span>
      ))}
    </pre>
  );
}

export function EvidenceInspector({ event, onClose }: { event: ReplayEvent; onClose?: () => void }) {
  const [copied, setCopied] = useState(false);
  const copyArtifact = async () => {
    if (!event.artifact) return;
    await navigator.clipboard?.writeText(event.artifact.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <aside className="inspector" aria-label="Selected event evidence">
      <div className="inspector-heading">
        <div>
          <h2>{event.title}</h2>
          <code>{time(event.occurredAt)} · {event.role}</code>
        </div>
        {onClose && <button className="icon-button" type="button" onClick={onClose} aria-label="Close inspector"><X size={17} /></button>}
      </div>
      <section className="inspector-section rationale">
        <h3>Decision rationale</h3>
        <p>{event.rationale}</p>
      </section>
      <section className="inspector-section">
        <h3>Evidence</h3>
        <div className="evidence-list">
          {event.evidence.length ? event.evidence.map((item) => (
            <a key={item.id} href={item.href ?? "#artifact"} onClick={(e) => !item.href && e.preventDefault()}>
              <span className={`evidence-icon evidence-${item.kind}`}>{item.kind === "test" ? <X size={14} /> : <Check size={14} />}</span>
              <span><strong>{item.label}</strong>{item.detail && <small>{item.detail}</small>}</span>
              {item.href && <ExternalLink size={14} />}
            </a>
          )) : <p className="empty-copy">No attached evidence.</p>}
        </div>
      </section>
      {event.artifact && (
        <section className="inspector-section artifact" id="artifact">
          <div className="section-title-row">
            <h3>Artifact</h3>
            <button className="icon-button subtle" type="button" onClick={copyArtifact} aria-label="Copy artifact">
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
          <div className="artifact-frame">
            <div className="artifact-path"><FileCode2 size={13} />{event.artifact.path ?? event.artifact.kind}</div>
            <Diff content={event.artifact.content} />
          </div>
        </section>
      )}
      <section className="inspector-section usage">
        <h3>Cost &amp; credits</h3>
        <dl>
          <div><dt>Tokens (in)</dt><dd>{event.usage.inputTokens.toLocaleString()}</dd></div>
          <div><dt>Tokens (out)</dt><dd>{event.usage.outputTokens.toLocaleString()}</dd></div>
          <div className="usage-total"><dt>Total tokens</dt><dd>{(event.usage.inputTokens + event.usage.outputTokens).toLocaleString()}</dd></div>
          <div className="credits-total"><dt>Credits charged</dt><dd>{event.usage.credits.toLocaleString()}</dd></div>
        </dl>
      </section>
    </aside>
  );
}
