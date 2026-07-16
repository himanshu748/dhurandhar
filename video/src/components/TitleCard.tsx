import { interpolate, useCurrentFrame } from "remotion";

export function TitleCard() {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12, 70, 96], [1, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [0, 20], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div className="title-card" style={{ opacity }}>
      <div className="title-mark">D</div>
      <div style={{ transform: `translateY(${y}px)` }}>
        <p>OPENAI BUILD WEEK</p>
        <h1>Dhurandhar</h1>
        <h2>An AI software company that shows receipts.</h2>
      </div>
    </div>
  );
}
