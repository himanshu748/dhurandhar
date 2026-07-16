import { interpolate, useCurrentFrame } from "remotion";
import { closingSentence } from "../scenes";

export function EndCard({ startsAt }: { startsAt: number }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [startsAt, startsAt + 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div className="end-card" style={{ opacity }}>
      <div className="end-card-inner">
        <div className="title-mark">D</div>
        <p className="end-kicker">AUDIT THE RUN</p>
        <h2>{closingSentence}</h2>
        <div className="end-links">
          <span>github.com/himanshu748/dhurandhar</span>
          <span>dhurandhar-asc.onrender.com</span>
        </div>
      </div>
    </div>
  );
}
