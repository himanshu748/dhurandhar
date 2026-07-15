import { LoaderCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { decidePolicy, runRecoveryDrill } from "./api";
import { EvidenceInspector } from "./components/EvidenceInspector";
import { LedgerPanel } from "./components/LedgerPanel";
import { NewObjectiveDialog } from "./components/NewObjectiveDialog";
import { RunHeader } from "./components/RunHeader";
import { SecondaryView } from "./components/SecondaryView";
import { Sidebar, type Page } from "./components/Sidebar";
import { Timeline } from "./components/Timeline";
import { Topbar } from "./components/Topbar";
import { useReplay } from "./hooks/useReplay";

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

  useEffect(() => {
    if (!snapshot) return;
    setCursor(snapshot.events.length - 1);
    const blocked = snapshot.events.find((event) => event.status === "blocked");
    const proposed = [...snapshot.events].reverse().find((event) => event.status === "proposed");
    const regression = [...snapshot.events].reverse().find((event) => event.status === "regression");
    const latest = snapshot.events.at(-1);
    setSelectedId(blocked?.id ?? proposed?.id ?? regression?.id ?? latest?.id ?? "");
  }, [snapshot]);

  useEffect(() => {
    if (!playing || !snapshot?.events.length) return;
    const timer = window.setInterval(() => {
      setCursor((current) => {
        if (current >= snapshot.events.length - 1) {
          setPlaying(false);
          return current;
        }
        const next = current + 1;
        setSelectedId(snapshot.events[next].id);
        return next;
      });
    }, 1100 / speed);
    return () => window.clearInterval(timer);
  }, [playing, snapshot, speed]);

  useEffect(() => {
    const keyboard = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target instanceof Element && target.matches("input, textarea, select, button")) return;
      if (event.code === "Space") {
        event.preventDefault();
        setPlaying((value) => !value);
      }
      if (!snapshot) return;
      if (event.key === "Home") {
        setCursor(0);
        setSelectedId(snapshot.events[0]?.id ?? "");
      }
      if (event.key === "End") {
        const last = snapshot.events.length - 1;
        setCursor(last);
        setSelectedId(snapshot.events[last]?.id ?? "");
      }
      if (event.key === "ArrowLeft") {
        setCursor((value) => {
          const next = Math.max(0, value - 1);
          setSelectedId(snapshot.events[next]?.id ?? "");
          return next;
        });
      }
      if (event.key === "ArrowRight") {
        setCursor((value) => {
          const next = Math.min(snapshot.events.length - 1, value + 1);
          setSelectedId(snapshot.events[next]?.id ?? "");
          return next;
        });
      }
    };
    window.addEventListener("keydown", keyboard);
    return () => window.removeEventListener("keydown", keyboard);
  }, [snapshot]);

  const selectedEvent = useMemo(
    () => snapshot?.events.find((event) => event.id === selectedId) ?? snapshot?.events[0],
    [selectedId, snapshot],
  );

  const seek = (index: number) => {
    if (!snapshot) return;
    const next = Math.max(0, Math.min(snapshot.events.length - 1, index));
    setCursor(next);
    setSelectedId(snapshot.events[next].id);
  };

  if (loading && !snapshot) {
    return (
      <main className="boot-screen">
        <span className="brand-mark large">D</span>
        <LoaderCircle className="spin" size={21} />
        <p>Verifying journal chain…</p>
      </main>
    );
  }

  if (!snapshot || !selectedEvent) {
    return <main className="boot-screen"><p>No replayable run found.</p><button className="primary-action simple" onClick={() => void refresh()}>Retry</button></main>;
  }

  const selectTransaction = (eventId?: string) => {
    if (eventId && snapshot.events.some((event) => event.id === eventId)) setSelectedId(eventId);
    setPage("replay");
  };

  const runDrill = async () => {
    if (snapshot.source !== "api") return;
    setDrillRunning(true);
    setActionMessage("Injecting a controlled fault and restoring the last known-good release…");
    try {
      await runRecoveryDrill(snapshot.run.id);
      await refresh();
      setActionMessage("Recovery verified. A benchmark-gated policy candidate is ready for review.");
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
      await decidePolicy(proposalId, decision);
      await refresh();
      setActionMessage(decision === "promote" ? "Policy promoted and will govern future runs." : "Policy candidate rejected.");
    } catch (cause) {
      setActionMessage(cause instanceof Error ? cause.message : "Policy decision failed");
    } finally {
      setPolicyBusyId(null);
    }
  };

  return (
    <div className={`app-shell ${page !== "replay" ? "secondary-shell" : ""}`}>
      <Sidebar active={page} onSelect={setPage} />
      <Topbar page={page} source={snapshot.source} onNewObjective={() => setDialogOpen(true)} />

      {page === "replay" ? (
        <>
          <RunHeader
            run={snapshot.run}
            current={cursor}
            total={snapshot.events.length}
            playing={playing}
            speed={speed}
            onToggle={() => setPlaying((value) => !value)}
            onSeek={seek}
            onSpeed={setSpeed}
            onRecoveryDrill={() => void runDrill()}
            drillRunning={drillRunning}
            drillDisabled={snapshot.source !== "api"}
          />
          <Timeline
            events={snapshot.events}
            selectedId={selectedEvent.id}
            cursor={cursor}
            onSelect={(event) => setSelectedId(event.id)}
          />
          <EvidenceInspector event={selectedEvent} />
          <LedgerPanel agents={snapshot.agents} transactions={snapshot.transactions} onTransaction={selectTransaction} />
        </>
      ) : (
        <SecondaryView
          page={page}
          snapshot={snapshot}
          onOpenReplay={() => setPage("replay")}
          onPolicyDecision={(proposalId, decision) => void reviewPolicy(proposalId, decision)}
          policyBusyId={policyBusyId}
        />
      )}

      {actionMessage && <div className="action-toast" role="status" onClick={() => setActionMessage(null)}>{actionMessage}</div>}

      <NewObjectiveDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={() => void refresh()}
      />
    </div>
  );
}
