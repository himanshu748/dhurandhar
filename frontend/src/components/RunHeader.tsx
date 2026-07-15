import { Clock3, Coins, Copy, LoaderCircle, Pause, Play, RotateCcw, ShieldAlert, SkipBack, SkipForward, UserRound } from "lucide-react";
import type { CSSProperties } from "react";
import type { RunSummary } from "../types";

const duration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(secs).padStart(2, "0")}s`;
};

export function RunHeader({
  run,
  current,
  total,
  playing,
  speed,
  onToggle,
  onSeek,
  onSpeed,
  onRecoveryDrill,
  drillRunning = false,
  drillDisabled = false,
}: {
  run: RunSummary;
  current: number;
  total: number;
  playing: boolean;
  speed: number;
  onToggle: () => void;
  onSeek: (index: number) => void;
  onSpeed: (speed: number) => void;
  onRecoveryDrill?: () => void;
  drillRunning?: boolean;
  drillDisabled?: boolean;
}) {
  const percent = total > 1 ? (current / (total - 1)) * 100 : 0;
  return (
    <section className="run-header" aria-labelledby="run-objective">
      <div className="run-title-line">
        <div>
          <h2 id="run-objective">{run.objective}</h2>
          <div className="run-identity">
            <code>{run.id.toUpperCase()}</code>
            <button
              className="icon-button subtle"
              type="button"
              onClick={() => void navigator.clipboard?.writeText(run.id)}
              aria-label="Copy run ID"
            >
              <Copy size={13} />
            </button>
            <span className="run-state"><span>✓</span>{run.status}</span>
          </div>
        </div>
        <div className="run-actions">
          {onRecoveryDrill && (
            <button className="drill-action" type="button" onClick={onRecoveryDrill} disabled={drillRunning || drillDisabled}>
              {drillRunning ? <LoaderCircle className="spin" size={14} /> : <ShieldAlert size={14} />}
              {drillRunning ? "Recovering…" : "Run recovery drill"}
            </button>
          )}
          <dl className="run-metrics">
          <div><Clock3 size={14} /><dt>Duration</dt><dd>{duration(run.durationSeconds)}</dd></div>
          <div><UserRound size={14} /><dt>Interventions</dt><dd>{run.interventions}</dd></div>
          <div><Coins size={14} /><dt>Token cost</dt><dd>{run.tokenCost.toLocaleString()}</dd></div>
          </dl>
        </div>
      </div>
      <div className="playback" aria-label="Replay controls">
        <div className="playback-cluster">
          <button className="play-button" type="button" onClick={onToggle} aria-label={playing ? "Pause replay" : "Play replay"}>
            {playing ? <Pause size={17} fill="currentColor" /> : <Play size={17} fill="currentColor" />}
          </button>
          <button className="icon-button" type="button" onClick={() => onSeek(0)} aria-label="Reset replay">
            <RotateCcw size={16} />
          </button>
        </div>
        <input
          className="replay-range"
          type="range"
          min="0"
          max={Math.max(0, total - 1)}
          value={current}
          onChange={(event) => onSeek(Number(event.currentTarget.value))}
          style={{ "--progress": `${percent}%` } as CSSProperties}
          aria-label="Replay position"
        />
        <code className="replay-time">{String(current + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}</code>
        <div className="seek-actions">
          <button type="button" onClick={() => onSeek(Math.max(0, current - 1))}><SkipBack size={14} />Prev</button>
          <button type="button" onClick={() => onSeek(Math.min(total - 1, current + 1))}>Next<SkipForward size={14} /></button>
          <select value={speed} onChange={(event) => onSpeed(Number(event.target.value))} aria-label="Replay speed">
            {[0.5, 1, 2, 4].map((value) => <option key={value} value={value}>{value}×</option>)}
          </select>
        </div>
      </div>
    </section>
  );
}
