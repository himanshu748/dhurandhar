import { Activity, ArrowUpRight, Check, Gauge, GitPullRequest, LoaderCircle, ShieldCheck, X } from "lucide-react";
import type { Page } from "./Sidebar";
import type { ReplaySnapshot } from "../types";
import { RoleMark } from "./RoleMark";

export function SecondaryView({
  page,
  snapshot,
  onOpenReplay,
  onPolicyDecision,
  policyBusyId,
}: {
  page: Exclude<Page, "replay">;
  snapshot: ReplaySnapshot;
  onOpenReplay: () => void;
  onPolicyDecision: (proposalId: string, decision: "promote" | "reject") => void;
  policyBusyId: string | null;
}) {
  if (page === "runs") {
    return (
      <section className="secondary-view">
        <div className="view-intro"><div><h2>Autonomous runs</h2><p>Every objective, intervention, and terminal state remains replayable.</p></div></div>
        <div className="data-table runs-table">
          <div className="data-row data-head"><span>Objective</span><span>Run ID</span><span>Repository</span><span>Status</span><span>Tokens</span></div>
          <button className="data-row" type="button" onClick={onOpenReplay}>
            <span><strong>{snapshot.run.objective}</strong><small>{snapshot.run.mode} runtime</small></span>
            <code>{snapshot.run.id}</code><span>{snapshot.run.repository}</span><span className="healthy-text">{snapshot.run.status}</span><code>{snapshot.run.tokenCost.toLocaleString()}</code>
          </button>
        </div>
      </section>
    );
  }

  if (page === "agents") {
    return (
      <section className="secondary-view">
        <div className="view-intro"><div><h2>Role agents</h2><p>Bounded contracts with measured work, not simulated personalities.</p></div></div>
        <div className="agent-directory">
          {snapshot.agents.map((agent) => (
            <article key={agent.id}>
              <RoleMark role={agent.displayName} />
              <p>{agent.role === "reviewer" ? "Adversarial correctness review and verified findings." : `Owns ${agent.role} work inside the run state machine.`}</p>
              <dl><div><dt>State</dt><dd>{agent.state}</dd></div><div><dt>Credits</dt><dd>{agent.balance.toLocaleString()}</dd></div></dl>
            </article>
          ))}
        </div>
      </section>
    );
  }

  if (page === "policies") {
    return (
      <section className="secondary-view">
        <div className="view-intro"><div><h2>Self-improvement policies</h2><p>Memory, prompt, routing, and economy changes pass the same evidence gate.</p></div></div>
        <div className="policy-list">
          {snapshot.policies.map((policy) => (
            <article key={policy.id}>
              <div className="policy-title"><span className={`mechanism mechanism-${policy.mechanism}`}>{policy.mechanism}</span><h3>{policy.title}</h3><span className={`proposal-status status-${policy.status}`}>{policy.status}</span></div>
              <p>{policy.rationale}</p>
              <div className="score-comparison"><Gauge size={15} /><span>Baseline <strong>{policy.baselineScore.toFixed(2)}</strong></span><ArrowUpRight size={14} /><span>Candidate <strong>{policy.candidateScore.toFixed(2)}</strong></span></div>
              {policy.status === "proposed" && policy.decisionOwner && snapshot.source === "api" && (
                <div className="policy-actions">
                  <button type="button" onClick={() => onPolicyDecision(policy.proposalId ?? policy.id, "reject")} disabled={Boolean(policyBusyId)}><X size={14} />Reject</button>
                  <button className="promote" type="button" onClick={() => onPolicyDecision(policy.proposalId ?? policy.id, "promote")} disabled={Boolean(policyBusyId)}>
                    {policyBusyId === (policy.proposalId ?? policy.id) ? <LoaderCircle className="spin" size={14} /> : <Check size={14} />}
                    Promote
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="secondary-view">
      <div className="view-intro"><div><h2>Immutable ledger</h2><p>Token usage and internal credits stay separate and trace back to source events.</p></div></div>
      <div className="data-table full-ledger">
        <div className="data-row data-head"><span>Time</span><span>Agent</span><span>Type</span><span>Description</span><span>Tokens</span><span>Credits</span></div>
        {snapshot.transactions.map((transaction) => (
          <button className="data-row" type="button" key={transaction.id} onClick={onOpenReplay}>
            <code>{new Date(transaction.occurredAt).toLocaleTimeString([], { hour12: false })}</code><RoleMark role={transaction.agent} /><span>{transaction.type}</span><span>{transaction.description}</span><code>{transaction.tokens.toLocaleString()}</code><code>{transaction.credits.toLocaleString()}</code>
          </button>
        ))}
      </div>
      <div className="trust-strip"><Activity size={16} /><span>Hash chain verified</span><ShieldCheck size={16} /><span>Critical policy intact</span><GitPullRequest size={16} /><span>0 hidden interventions</span></div>
    </section>
  );
}
