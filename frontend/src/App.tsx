import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { decidePolicy, runRecoveryDrill } from "./api";
import { EvidenceInspector } from "./components/EvidenceInspector";
import { LedgerPanel } from "./components/LedgerPanel";
import { NewObjectiveDialog } from "./components/NewObjectiveDialog";
import { OperatorAccessDialog } from "./components/OperatorAccessDialog";
import { RunHeader } from "./components/RunHeader";
import { Sidebar, type Page } from "./components/Sidebar";
import { Timeline } from "./components/Timeline";
import { Topbar } from "./components/Topbar";
import { useReplay } from "./hooks/useReplay";
import { selectCinematicEvents } from "./lib/replay";

const RecoveryFlow = lazy(() => import("./components/RecoveryFlow")
  .then((module) => ({ default: module.RecoveryFlow })));
const SecondaryView = lazy(() => import("./components/SecondaryView")
  .then((module) => ({ default: module.SecondaryView })));

function BootSkeleton() {
  return (
    <main className="skeleton-shell" aria-label="Loading Dhurandhar control plane" aria-busy="true">
      <div className="skeleton-sidebar"><span className="brand-mark large">D</span>{Array.from({ length: 5 }, (_, index) => <i key={index} />)}</div>
      <div className="skeleton-topbar"><i /><i /><i /></div>
      <div className="skeleton-replay"><i className="wide" />{Array.from({ length: 4 }, (_, index) => <article key={index}><i /><i /><i /></article>)}</div>
      <div className="skeleton-inspector"><i />{Array.from({ length: 6 }, (_, index) => <i key={index} />)}</div>
      <p>Verifying journal chain and evidence provenance…</p>
    </main>
  );
}

function SurfaceSkeleton({ surface }: { surface: "recovery" | "secondary" }) {
  return (
    <section
      className={`${surface === "secondary" ? "secondary-view " : ""}skeleton-replay`}
      aria-label={`Loading ${surface} evidence`}
      aria-busy="true"
    >
      <i className="wide" />
      {Array.from({ length: surface === "secondary" ? 4 : 2 }, (_, index) => (
        <article key={index}><i /><i /><i /></article>
      ))}
    </section>
  );
}

export default function App() {
  const { snapshot, loading, refresh } = useReplay();
  const [page, setPage] = useState<Page>("replay");
  const [cursor, setCursor] = useState(0);
  const [selectedId, setSelectedId] = useState<string>("");
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drillRunning, setDrillRunning] = useState(false);
  const [policyBusyId, setPolicyBusyId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [operatorToken, setOperatorToken] = useState("");
  const [operatorDialogOpen, setOperatorDialogOpen] = useState(false);
  const operatorEnabled = operatorToken.length > 0;
  const cinematicEvents = useMemo(() => selectCinematicEvents(snapshot?.events ?? []), [snapshot]);
  const latestProvenance = useMemo(() => [...(snapshot?.events ?? [])].reverse().find((event) => event.provenance?.mode === "live")?.provenance
    ?? [...(snapshot?.events ?? [])].reverse().find((event) => event.provenance)?.provenance, [snapshot]);

  useEffect(() => {
    if (!snapshot) return;
    const liveImplementation = cinematicEvents.findIndex((event) => event.type === "code.generated" && event.provenance?.mode === "live");
    const openingIndex = liveImplementation >= 0 ? liveImplementation : Math.max(0, cinematicEvents.length - 1);
    setCursor(openingIndex);
    setSelectedId(cinematicEvents[openingIndex]?.id ?? "");
  }, [cinematicEvents, snapshot]);

  useEffect(() => {
    if (!playing || !cinematicEvents.length) return;
    const timer = window.setInterval(() => {
      setCursor((current) => {
        if (current >= cinematicEvents.length - 1) {
          setPlaying(false);
          return current;
        }
        const next = current + 1;
        setSelectedId(cinematicEvents[next].id);
        return next;
      });
    }, 1100 / speed);
    return () => window.clearInterval(timer);
  }, [cinematicEvents, playing, speed]);

  useEffect(() => {
    const keyboard = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target instanceof Element && target.matches("input, textarea, select, button")) return;
      if (event.code === "Space") {
        event.preventDefault();
        setPlaying((value) => !value);
      }
      if (!cinematicEvents.length) return;
      if (event.key === "Home") {
        setCursor(0);
        setSelectedId(cinematicEvents[0]?.id ?? "");
      }
      if (event.key === "End") {
        const last = cinematicEvents.length - 1;
        setCursor(last);
        setSelectedId(cinematicEvents[last]?.id ?? "");
      }
      if (event.key === "ArrowLeft") {
        setCursor((value) => {
          const next = Math.max(0, value - 1);
          setSelectedId(cinematicEvents[next]?.id ?? "");
          return next;
        });
      }
      if (event.key === "ArrowRight") {
        setCursor((value) => {
          const next = Math.min(cinematicEvents.length - 1, value + 1);
          setSelectedId(cinematicEvents[next]?.id ?? "");
          return next;
        });
      }
    };
    window.addEventListener("keydown", keyboard);
    return () => window.removeEventListener("keydown", keyboard);
  }, [cinematicEvents]);

  const selectedEvent = useMemo(
    () => cinematicEvents.find((event) => event.id === selectedId) ?? cinematicEvents[0],
    [cinematicEvents, selectedId],
  );

  const seek = (index: number) => {
    if (!snapshot) return;
    const next = Math.max(0, Math.min(cinematicEvents.length - 1, index));
    setCursor(next);
    setSelectedId(cinematicEvents[next].id);
  };

  if (loading && !snapshot) {
    return <BootSkeleton />;
  }

  if (!snapshot || !selectedEvent) {
    return <main className="boot-screen"><p>No objectives yet. The company is idle.</p><button className="primary-action simple" onClick={() => void refresh()}>Retry evidence sync</button></main>;
  }

  const selectTransaction = (eventId?: string) => {
    const index = eventId ? cinematicEvents.findIndex((event) => event.id === eventId) : -1;
    if (index >= 0) seek(index);
    setPage("replay");
  };

  const runDrill = async () => {
    if (snapshot.source !== "api") return;
    setDrillRunning(true);
    setActionMessage("Injecting a controlled fault and restoring the last known-good release…");
    try {
      await runRecoveryDrill(snapshot.run.id, operatorToken);
      await refresh();
      setActionMessage("Recovery verified. A structurally covered control set is ready for operator review; efficacy is not claimed.");
    } catch (cause) {
      setActionMessage(cause instanceof Error ? cause.message : "Recovery drill failed");
    } finally {
      setDrillRunning(false);
    }
  };

  const reviewPolicy = async (proposalId: string, decision: "promote" | "reject") => {
    setPolicyBusyId(proposalId);
    setActionMessage(null);
    try {
      await decidePolicy(proposalId, decision, operatorToken);
      await refresh();
      setActionMessage(decision === "promote" ? "Operator-approved controls will be inherited by future runs." : "Policy candidate rejected.");
    } catch (cause) {
      setActionMessage(cause instanceof Error ? cause.message : "Policy decision failed");
    } finally {
      setPolicyBusyId(null);
    }
  };

  return (
    <div className={`app-shell ${page !== "replay" ? "secondary-shell" : ""}`}>
      <Sidebar active={page} onSelect={setPage} />
      <Topbar
        page={page}
        source={snapshot.source}
        operatorEnabled={operatorEnabled}
        model={latestProvenance?.model}
        provenance={snapshot.run.mode === "codex" ? "live" : "fixture"}
        sandbox={latestProvenance?.sandbox}
        onNewObjective={() => setDialogOpen(true)}
        onOperatorAccess={() => setOperatorDialogOpen(true)}
      />

      {page === "replay" ? (
        <>
          <RunHeader
            run={snapshot.run}
            current={cursor}
            total={cinematicEvents.length}
            playing={playing}
            speed={speed}
            onToggle={() => setPlaying((value) => !value)}
            onSeek={seek}
            onSpeed={setSpeed}
            onRecoveryDrill={() => void runDrill()}
            drillRunning={drillRunning}
            drillDisabled={snapshot.source !== "api" || !operatorEnabled}
            drillDisabledReason={snapshot.source !== "api" ? "Recovery drills require a live API" : "Load an operator token to run a recovery drill"}
          />
          <Timeline
            events={cinematicEvents}
            allEvents={snapshot.events}
            selectedId={selectedEvent.id}
            cursor={cursor}
            runMode={snapshot.run.mode}
            onSelect={(_event, index) => seek(index)}
          >
            <Suspense fallback={<SurfaceSkeleton surface="recovery" />}>
              <RecoveryFlow
                events={snapshot.events}
                currentSequence={selectedEvent.sequence}
                policies={snapshot.policies}
                operatorEnabled={operatorEnabled}
                policyBusyId={policyBusyId}
                onPolicyDecision={(proposalId, decision) => void reviewPolicy(proposalId, decision)}
                onOpenPolicies={() => setPage("policies")}
              />
            </Suspense>
          </Timeline>
          <EvidenceInspector event={selectedEvent} runMode={snapshot.run.mode} />
          <LedgerPanel
            agents={snapshot.agents}
            transactions={snapshot.transactions}
            events={snapshot.events}
            currentSequence={selectedEvent.sequence}
            currentEventId={selectedEvent.id}
            onTransaction={selectTransaction}
          />
        </>
      ) : (
        <Suspense fallback={<SurfaceSkeleton surface="secondary" />}>
          <SecondaryView
            page={page}
            snapshot={snapshot}
            onOpenReplay={() => setPage("replay")}
            onPolicyDecision={(proposalId, decision) => void reviewPolicy(proposalId, decision)}
            policyBusyId={policyBusyId}
            operatorEnabled={operatorEnabled}
          />
        </Suspense>
      )}

      {actionMessage && <div className="action-toast" role="status" onClick={() => setActionMessage(null)}>{actionMessage}</div>}

      <NewObjectiveDialog
        open={dialogOpen}
        operatorToken={operatorToken}
        onClose={() => setDialogOpen(false)}
        onCreated={() => void refresh()}
      />
      <OperatorAccessDialog
        open={operatorDialogOpen}
        tokenLoaded={operatorEnabled}
        onClose={() => setOperatorDialogOpen(false)}
        onLoadToken={(token) => {
          setOperatorToken(token);
          setOperatorDialogOpen(false);
          setActionMessage("Operator token loaded into this tab's memory. Mutation controls are enabled.");
        }}
        onForgetToken={() => {
          setOperatorToken("");
          setDialogOpen(false);
          setOperatorDialogOpen(false);
          setActionMessage("Operator token forgotten. The control plane is read-only.");
        }}
      />
    </div>
  );
}
