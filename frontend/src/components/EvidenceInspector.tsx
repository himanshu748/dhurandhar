import { Check, Copy, ExternalLink, FileCode2, Radio, TerminalSquare, X } from "lucide-react";
import { useState } from "react";
import type { CommandOutcome, ModelProvenance, ReplayEvent, RunSummary, TaskAuction } from "../types";
import { CopyableValue } from "./CopyableValue";
import { RoleMark } from "./RoleMark";

const time = (value: string) =>
  new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(
    new Date(value),
  );

function Diff({ content, maxHeight = false }: { content: string; maxHeight?: boolean }) {
  return (
    <pre className={`diff-view ${maxHeight ? "diff-view-tall" : ""}`}>
      {content.split("\n").map((line, index) => (
        <span key={`${index}-${line}`} className={line.startsWith("+") ? "diff-add" : line.startsWith("-") ? "diff-remove" : ""}>
          {line || " "}
        </span>
      ))}
    </pre>
  );
}

const outcomePassed = (outcome: CommandOutcome) => {
  const status = outcome.status.toLowerCase();
  return outcome.exitCode === 0 || ["passed", "success", "succeeded", "completed", "ok"].some((value) => status.includes(value));
};

function OutcomeList({ title, outcomes }: { title: string; outcomes: CommandOutcome[] }) {
  if (!outcomes.length) return null;
  return (
    <div className="provenance-outcomes">
      <h4>{title}</h4>
      {outcomes.map((outcome, index) => {
        const passed = outcomePassed(outcome);
        return (
          <div className={`outcome-row ${passed ? "is-passed" : "is-attention"}`} key={`${outcome.command}-${index}`}>
            <span className="outcome-icon">{passed ? <Check size={12} /> : <X size={12} />}</span>
            <code>{outcome.command}</code>
            <span>{outcome.status}{outcome.exitCode !== undefined ? ` · exit ${outcome.exitCode}` : ""}</span>
            {outcome.detail && <small>{outcome.detail}</small>}
          </div>
        );
      })}
    </div>
  );
}

function AuctionEvidence({ auction }: { auction: TaskAuction }) {
  return (
    <section className="inspector-section auction-evidence">
      <div className="section-title-row">
        <h3>Task auction</h3>
        <span className={`auction-status status-${auction.status}`}>{auction.status}</span>
      </div>
      <p className="auction-task">{auction.task}</p>
      <dl className="auction-facts">
        <div><dt>Bounty</dt><dd>{auction.bounty?.toLocaleString() ?? "—"} credits</dd></div>
        <div><dt>Eligible</dt><dd>{auction.eligibleEngineers.length || "—"}</dd></div>
        <div><dt>Bids considered</dt><dd>{auction.bidsConsidered ?? auction.bids.length}</dd></div>
      </dl>
      {auction.winner && (
        <div className="auction-winner">
          <RoleMark role={auction.winner} />
          <span><small>Winning engineer</small><strong>{auction.winningAmount?.toLocaleString() ?? "—"} credits</strong></span>
        </div>
      )}
      <div className="bid-list">
        {auction.bids.length ? auction.bids.map((bid) => (
          <article className={bid.winner ? "is-winner" : ""} key={bid.bidderId}>
            <header><RoleMark role={bid.bidder} /><code>{bid.amount.toLocaleString()} cr</code></header>
            {bid.plan && <p>{bid.plan}</p>}
            <footer>
              {bid.credibility !== undefined && <span>Credibility {bid.credibility.toFixed(2)}</span>}
              {bid.evidence.length > 0 && <span>{bid.evidence.length} evidence refs</span>}
            </footer>
          </article>
        )) : <p className="empty-copy">No competitive bids were attached to this legacy assignment.</p>}
      </div>
    </section>
  );
}

function ProvenanceEvidence({ provenance, runMode }: { provenance?: ModelProvenance; runMode: RunSummary["mode"] }) {
  if (!provenance) {
    const deterministic = runMode === "deterministic";
    return (
      <section className={`inspector-section provenance-summary provenance-${deterministic ? "deterministic" : "orchestration"}`}>
        <div><Radio size={14} /><strong>{deterministic ? "Deterministic fallback" : "Orchestration event"}</strong></div>
        <p>{deterministic ? "No model call produced this event; it comes from the reproducible fixture runtime." : "This event has no direct model invocation attached. Select a generated-code or review event for live provenance."}</p>
      </section>
    );
  }

  const live = provenance.mode === "live";
  const observedModel = provenance.observedModel;
  const requestedModel = provenance.requestedModel ?? provenance.model;
  const displayedModel = observedModel ?? requestedModel;
  return (
    <section className={`inspector-section model-provenance provenance-${provenance.mode}`}>
      <div className="provenance-heading">
        <span><Radio size={14} /><strong>{live ? "Live call provenance" : "Deterministic fallback"}</strong></span>
        <code>{live ? "MODEL CALL" : "NO MODEL CALL"}</code>
      </div>
      <p>{live
        ? observedModel
          ? "The JSONL stream echoed the model identifier and it matched the requested slug."
          : "Thread and token evidence came from JSONL; the requested CLI model was not echoed by the stream."
        : "This event was produced by the deterministic fixture and carries no live model claim."}</p>
      <dl className="provenance-facts">
        <div><dt>Runtime</dt><dd>{provenance.runtime ?? "Not reported"}</dd></div>
        <div><dt>{live ? observedModel ? "Observed model" : "Requested model" : "Model"}</dt><dd>{displayedModel ?? (live ? "Not reported" : "None")}</dd></div>
        {live && <div><dt>Stream model</dt><dd>{observedModel ? "Observed in JSONL" : "Not emitted by JSONL"}</dd></div>}
        <div><dt>Thread / session</dt><dd>{provenance.threadId || provenance.sessionId ? <CopyableValue value={provenance.threadId ?? provenance.sessionId ?? ""} label="thread or session ID" /> : "Not reported"}</dd></div>
        <div><dt>Sandbox</dt><dd>{provenance.sandbox ?? "Not reported"}</dd></div>
      </dl>
      <div className="provenance-usage" aria-label="Model token usage">
        <div><span>Input</span><strong>{provenance.inputTokens.toLocaleString()}</strong></div>
        <div><span>Cached</span><strong>{provenance.cachedInputTokens.toLocaleString()}</strong></div>
        <div><span>Output</span><strong>{provenance.outputTokens.toLocaleString()}</strong></div>
        <div><span>Reasoning</span><strong>{provenance.reasoningOutputTokens.toLocaleString()}</strong></div>
      </div>
      <OutcomeList title="Commands" outcomes={provenance.commands} />
      <OutcomeList title="Check outcomes" outcomes={provenance.checks} />
      {provenance.changedFiles.length > 0 && (
        <div className="changed-files">
          <h4>Changed files</h4>
          <ul>{provenance.changedFiles.map((file) => <li key={file}><FileCode2 size={11} /><code>{file}</code></li>)}</ul>
        </div>
      )}
      {provenance.diff && (provenance.diff.sha256 || provenance.diff.preview) && (
        <div className="provenance-diff">
          <div className="provenance-diff-meta">
            <span>Diff SHA-256</span>{provenance.diff.sha256 ? <CopyableValue value={provenance.diff.sha256} label="diff SHA-256" /> : <code>Not reported</code>}
            {(provenance.diff.linesAdded !== undefined || provenance.diff.linesDeleted !== undefined) && (
              <small><b>+{provenance.diff.linesAdded ?? 0}</b> / <i>-{provenance.diff.linesDeleted ?? 0}</i></small>
            )}
          </div>
          {provenance.diff.preview && <Diff content={provenance.diff.preview} maxHeight />}
        </div>
      )}
      {provenance.finalMessage && <div className="model-final-message"><h4>Final message</h4><p>{provenance.finalMessage}</p></div>}
    </section>
  );
}

export function EvidenceInspector({
  event,
  runMode = "deterministic",
  onClose,
}: {
  event: ReplayEvent;
  runMode?: RunSummary["mode"];
  onClose?: () => void;
}) {
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
      <ProvenanceEvidence provenance={event.provenance} runMode={runMode} />
      <section className="inspector-section rationale">
        <h3>Decision rationale</h3>
        <p>{event.rationale}</p>
      </section>
      {event.auction && <AuctionEvidence auction={event.auction} />}
      <section className="inspector-section">
        <h3>Evidence</h3>
        <div className="evidence-list">
          {event.evidence.length ? event.evidence.map((item) => (
            <a key={item.id} href={item.href ?? "#artifact"} onClick={(e) => !item.href && e.preventDefault()}>
              <span className={`evidence-icon evidence-${item.kind}`}><Check size={14} /></span>
              <span><strong>{item.label}</strong>{item.detail && <small>{item.detail}</small>}</span>
              {item.href && <ExternalLink size={14} />}
            </a>
          )) : <p className="empty-copy">No attached evidence.</p>}
        </div>
      </section>
      {event.artifact && !event.provenance?.diff?.preview && (
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
        <h3><TerminalSquare size={13} />Cost &amp; credits</h3>
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
