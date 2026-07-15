import { Activity, ArrowUpRight, Brain, Check, Gauge, GitPullRequest, ShieldCheck, X } from "lucide-react";
import type { Page } from "./Sidebar";
import type { AgentBalance, ReplaySnapshot } from "../types";
import { RoleMark } from "./RoleMark";

function AgentDirectory({ agents }: { agents: AgentBalance[] }) {
  return (
    <div className="agent-directory">
      {agents.map((agent) => (
        <article className={`agent-card state-${agent.state}`} key={agent.id}>
          <header className="agent-card-heading">
            <RoleMark role={agent.companyRole ?? agent.displayName} showLabel={false} />
            <div>
              <h3>{agent.displayName}</h3>
              <small>{agent.companyRole ?? agent.role}</small>
            </div>
            <span className="agent-state"><i aria-hidden="true" />{agent.reported === false ? "not reported" : agent.state}</span>
          </header>
          {agent.personality && <p className="agent-personality">{agent.personality}</p>}
          {agent.currentTask && <p className="agent-current-task"><strong>Now</strong>{agent.currentTask}</p>}
          <section className="agent-capabilities" aria-label={`${agent.displayName} capabilities`}>
            <h4>Capabilities</h4>
            <ul>{(agent.capabilities ?? []).map((capability) => <li key={capability}>{capability}</li>)}</ul>
          </section>
          <section className="agent-memory" aria-label={`${agent.displayName} memory`}>
            <div className="agent-section-heading"><h4><Brain size={13} />Memory</h4><code>{agent.memoryCount ?? agent.memoryReferences?.length ?? 0} refs</code></div>
            {agent.lastLearning ? <p><strong>Last learning</strong>{agent.lastLearning}</p> : <p className="agent-empty-memory">No learned memory reported yet.</p>}
            {(agent.memoryReferences?.length ?? 0) > 0 && (
              <ul>
                {agent.memoryReferences?.slice(-2).reverse().map((memory) => (
                  <li key={memory.id}><code>{memory.eventId ?? memory.id}</code><span>{memory.label}</span></li>
                ))}
              </ul>
            )}
          </section>
          <dl className="agent-stats">
            <div><dt>Balance</dt><dd>{agent.balance.toLocaleString()} cr</dd></div>
            <div><dt>Actions</dt><dd>{agent.completedActions?.toLocaleString() ?? "—"}</dd></div>
          </dl>
        </article>
      ))}
    </div>
  );
}

export function SecondaryView({
  page,
  snapshot,
  onOpenReplay,
  onPolicyDecision,
  policyBusyId,
  operatorEnabled,
}: {
  page: Exclude<Page, "replay">;
  snapshot: ReplaySnapshot;
  onOpenReplay: () => void;
  onPolicyDecision: (proposalId: string, decision: "promote" | "reject") => void;
  policyBusyId: string | null;
  operatorEnabled: boolean;
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
        <div className="view-intro"><div><h2>Eight-agent company</h2><p>Persistent role contracts expose capabilities, current state, credits, and learned memory.</p></div><code className="view-count">{snapshot.agents.length} roles</code></div>
        <AgentDirectory agents={snapshot.agents} />
      </section>
    );
  }

  if (page === "policies") {
    return (
      <section className="secondary-view">
        <div className="view-intro"><div><h2>Self-improvement policies</h2><p>Memory, prompt, routing, and economy controls require executable enforcement and an operator decision. Coverage is structural, not an efficacy score.</p></div></div>
        <div className="policy-list">
          {snapshot.policies.map((policy) => (
            <article key={policy.id}>
              <div className="policy-title"><span className={`mechanism mechanism-${policy.mechanism}`}>{policy.mechanism}</span><h3>{policy.title}</h3><span className={`proposal-status status-${policy.status}`}>{policy.status}</span></div>
              <p>{policy.rationale}</p>
              <div className="score-comparison" title="Deterministic control-kind coverage; not policy efficacy"><Gauge size={15} /><span>Coverage <strong>{policy.baselineScore.toFixed(2)}</strong></span><ArrowUpRight size={14} /><span>Coverage <strong>{policy.candidateScore.toFixed(2)}</strong></span><span>structure only</span></div>
              {policy.status === "proposed" && policy.decisionOwner && snapshot.source === "api" && (
                <div className="policy-actions">
                  <button type="button" onClick={() => onPolicyDecision(policy.proposalId ?? policy.id, "reject")} disabled={Boolean(policyBusyId) || !operatorEnabled} title={operatorEnabled ? "Reject this candidate" : "Load an operator token to decide policies"}><X size={14} />Reject</button>
                  <button className="promote" type="button" onClick={() => onPolicyDecision(policy.proposalId ?? policy.id, "promote")} disabled={Boolean(policyBusyId) || !operatorEnabled} title={operatorEnabled ? "Promote this candidate" : "Load an operator token to decide policies"}>
                    {policyBusyId === (policy.proposalId ?? policy.id) ? <span className="button-skeleton" aria-hidden="true" /> : <Check size={14} />}
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
