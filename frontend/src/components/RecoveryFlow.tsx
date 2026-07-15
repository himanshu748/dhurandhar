import { useLayoutEffect, useMemo, useRef } from "react";
import { gsap, ScrollTrigger } from "../lib/gsap";
import { useReducedMotion } from "../hooks/useReducedMotion";
import type { PolicyProposal, ReplayEvent } from "../types";

type PolicyDecision = "promote" | "reject";

interface RecoveryLedgerEvidence {
  kind?: string;
  amount?: number;
  fromAgent?: string;
  from_agent?: string;
  toAgent?: string;
  to_agent?: string;
  reason?: string;
}

interface RecoveryStep {
  id: string;
  kind: "regression" | "alert" | "penalty" | "restore" | "proposal";
  label: string;
  sequence: number;
  events: ReplayEvent[];
}

export interface RecoveryFlowProps {
  events: ReplayEvent[];
  currentSequence: number;
  policies: PolicyProposal[];
  operatorEnabled: boolean;
  policyBusyId: string | null;
  onPolicyDecision: (proposalId: string, decision: PolicyDecision) => void;
  onOpenPolicies: () => void;
}

const ledgerEvidence = (event: ReplayEvent): RecoveryLedgerEvidence | undefined =>
  (event as ReplayEvent & { ledger?: RecoveryLedgerEvidence }).ledger;

const eventTime = (event: ReplayEvent) => new Date(event.occurredAt).toLocaleTimeString([], {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

const proposalMatchesEvent = (policy: PolicyProposal, event: ReplayEvent) => {
  const proposalId = policy.proposalId;
  if (!proposalId) return false;
  return event.artifact?.content.includes(proposalId)
    || event.evidence.some((evidence) => evidence.label.includes(proposalId) || evidence.detail?.includes(proposalId));
};

export function RecoveryFlow({
  events,
  currentSequence,
  policies,
  operatorEnabled,
  policyBusyId,
  onPolicyDecision,
  onOpenPolicies,
}: RecoveryFlowProps) {
  const rootRef = useRef<HTMLElement>(null);
  const reducedMotion = useReducedMotion();

  const { steps, proposalPolicy } = useMemo(() => {
    const ordered = [...events].sort((left, right) => left.sequence - right.sequence);
    const regressionEvents = ordered.filter((event) =>
      event.type === "regression.injected" || event.type === "monitor.regression",
    );
    const alertEvents = ordered.filter((event) => event.type === "monitor.alert");
    const penaltyEvents = ordered.filter((event) =>
      event.type === "ledger.transaction" && ledgerEvidence(event)?.kind === "penalty",
    );
    const restoreEvents = ordered.filter((event) => event.type === "rollback.completed");
    const proposalEvents = ordered.filter((event) => event.type === "policy.proposed");

    const nextSteps: RecoveryStep[] = [];
    const addStep = (kind: RecoveryStep["kind"], label: string, matchingEvents: ReplayEvent[]) => {
      if (!matchingEvents.length) return;
      nextSteps.push({
        id: `${kind}-${matchingEvents[0].id}`,
        kind,
        label,
        sequence: matchingEvents[matchingEvents.length - 1].sequence,
        events: matchingEvents,
      });
    };

    addStep("regression", "Regression observed", regressionEvents);
    addStep("alert", "Alert raised", alertEvents);
    addStep("penalty", "Liability assigned", penaltyEvents);
    addStep("restore", "Known-good restored", restoreEvents);
    addStep("proposal", "Policy proposed", proposalEvents);

    const decisionPolicies = policies.filter((policy) =>
      policy.decisionOwner === true && Boolean(policy.proposalId),
    );
    const matchedPolicy = proposalEvents.length
      ? decisionPolicies.find((policy) => proposalEvents.some((event) => proposalMatchesEvent(policy, event)))
        ?? (decisionPolicies.length === 1 ? decisionPolicies[0] : undefined)
      : undefined;

    return { steps: nextSteps, proposalPolicy: matchedPolicy };
  }, [events, policies]);

  const activeStepIndex = steps.reduce(
    (latest, step, index) => step.sequence <= currentSequence ? index : latest,
    -1,
  );
  const animationKey = steps.map((step) => step.id).join("|");

  useLayoutEffect(() => {
    const root = rootRef.current;
    if (!root || reducedMotion || !animationKey) return;

    const context = gsap.context(() => {
      const stepElements = gsap.utils.toArray<HTMLElement>("[data-recovery-step]");
      const gate = root.querySelector<HTMLElement>("[data-human-gate]");
      const scroller = root.closest<HTMLElement>(".timeline") ?? undefined;
      gsap.set(stepElements, { opacity: 0, y: 16 });
      if (gate) gsap.set(gate, { opacity: 0, y: 10, scale: 0.985 });

      const timeline = gsap.timeline({
        defaults: { duration: 0.42, ease: "power3.out" },
        scrollTrigger: {
          trigger: root,
          scroller,
          start: "top 78%",
          once: true,
        },
      });
      timeline.to(stepElements, { opacity: 1, y: 0, stagger: 0.1 });
      if (gate) timeline.to(gate, { opacity: 1, y: 0, scale: 1, duration: 0.5 }, "-=0.12");

      ScrollTrigger.refresh();
    }, root);

    return () => context.revert();
  }, [animationKey, proposalPolicy?.proposalId, reducedMotion]);

  if (!steps.length) return null;

  const proposalId = proposalPolicy?.proposalId;
  const decisionBusy = Boolean(proposalId && policyBusyId === proposalId);
  const decisionPending = proposalPolicy?.status === "proposed";

  return (
    <section className="recovery-flow" ref={rootRef} aria-labelledby="recovery-flow-title">
      <header className="recovery-flow__header">
        <div>
          <p className="recovery-flow__eyebrow">Recorded recovery chain</p>
          <h2 id="recovery-flow-title">Regression containment</h2>
        </div>
        <p>Only events present in this run are shown.</p>
      </header>

      <ol className="recovery-flow__sequence" aria-label="Observed recovery sequence">
        {steps.map((step, index) => {
          const state = index < activeStepIndex ? "reached" : index === activeStepIndex ? "current" : "pending";
          const firstEvent = step.events[0];
          const lastEvent = step.events[step.events.length - 1];
          const totalPenalty = step.kind === "penalty"
            ? step.events.reduce((total, event) => total + Number(ledgerEvidence(event)?.amount ?? 0), 0)
            : 0;

          return (
            <li
              className={`recovery-step recovery-step--${step.kind} is-${state}`}
              data-recovery-step
              data-state={state}
              key={step.id}
              aria-current={state === "current" ? "step" : undefined}
            >
              <div className="recovery-step__rail" aria-hidden="true">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <i />
              </div>
              <article className="recovery-step__body">
                <header>
                  <div>
                    <p>{step.label}</p>
                    <strong className="recovery-step__title">{firstEvent.title}</strong>
                  </div>
                  <div className="recovery-step__coordinates">
                    <code>SEQ {firstEvent.sequence}{lastEvent.sequence !== firstEvent.sequence ? `–${lastEvent.sequence}` : ""}</code>
                    <time dateTime={firstEvent.occurredAt}>{eventTime(firstEvent)}</time>
                  </div>
                </header>

                {step.kind === "penalty" ? (
                  <div className="recovery-penalties">
                    <p className="recovery-penalties__total">
                      <strong>{step.events.length}</strong> liability {step.events.length === 1 ? "entry" : "entries"}
                      {totalPenalty > 0 && <><span aria-hidden="true"> / </span><strong>{totalPenalty} cr</strong></>}
                    </p>
                    <ul aria-label="Recorded liability penalties">
                      {step.events.map((event) => {
                        const ledger = ledgerEvidence(event);
                        const liableAgent = ledger?.fromAgent ?? ledger?.from_agent;
                        return (
                          <li key={event.id}>
                            <span>{liableAgent ?? event.summary}</span>
                            {typeof ledger?.amount === "number" && <code>−{ledger.amount} cr</code>}
                            {liableAgent && <small>{ledger?.reason ?? event.summary}</small>}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ) : (
                  <>
                    <p className="recovery-step__summary">{firstEvent.rationale}</p>
                    {step.events.length > 1 && (
                      <ul className="recovery-step__evidence" aria-label={`${step.label} evidence`}>
                        {step.events.map((event) => <li key={event.id}>{event.summary}</li>)}
                      </ul>
                    )}
                  </>
                )}

                <footer>
                  <span>{firstEvent.actor}</span>
                  <code>{firstEvent.type}</code>
                </footer>
              </article>
            </li>
          );
        })}
      </ol>

      {proposalPolicy && proposalId && (
        <section className="human-gate" data-human-gate aria-labelledby="human-gate-title">
          <div className="human-gate__signal" aria-hidden="true">HUMAN</div>
          <div className="human-gate__content">
            <p className="human-gate__eyebrow">Authority boundary · {decisionPending ? "operator decision required" : "human decision recorded"}</p>
            <h3 id="human-gate-title">{decisionPending ? "The company cannot promote this policy itself." : `Human gate resolved: ${proposalPolicy.status}.`}</h3>
            <p>{proposalPolicy.title}</p>
            <dl>
              <div><dt>Proposal</dt><dd><code>{proposalId}</code></dd></div>
              <div><dt>Decision owner</dt><dd>Human operator</dd></div>
              <div><dt>Status</dt><dd>{decisionBusy ? "Decision in progress" : decisionPending ? "Awaiting decision" : proposalPolicy.status}</dd></div>
            </dl>
            {decisionPending && !operatorEnabled && (
              <p className="human-gate__locked" role="status">Load an operator token to unlock this decision boundary.</p>
            )}
            <div className="human-gate__actions">
              <button type="button" onClick={onOpenPolicies}>Inspect policy</button>
              {decisionPending ? (
                <>
                  <button
                    type="button"
                    onClick={() => onPolicyDecision(proposalId, "reject")}
                    disabled={!operatorEnabled || Boolean(policyBusyId)}
                  >
                    Reject
                  </button>
                  <button
                    className="human-gate__promote"
                    type="button"
                    onClick={() => onPolicyDecision(proposalId, "promote")}
                    disabled={!operatorEnabled || Boolean(policyBusyId)}
                  >
                    {decisionBusy ? "Promoting…" : "Approve and promote"}
                  </button>
                </>
              ) : <code className={`human-gate__resolution is-${proposalPolicy.status}`}>DECISION · {proposalPolicy.status.toUpperCase()}</code>}
            </div>
          </div>
        </section>
      )}
    </section>
  );
}
