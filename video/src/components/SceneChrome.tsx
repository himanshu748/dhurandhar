import { interpolate, useCurrentFrame } from "remotion";

export function SceneChrome({ number, label }: { number: string; label: string }) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div className="scene-chrome" style={{ opacity }}>
      <span>{number}</span>
      <strong>{label}</strong>
      <i>RECORDED EVIDENCE</i>
    </div>
  );
}
