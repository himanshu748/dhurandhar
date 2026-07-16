import { AbsoluteFill, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import type { EvidenceFrame } from "../scenes";

const CROSSFADE_FRAMES = 16;

function KenBurnsFrame({ frame, isFirst, isLast }: { frame: EvidenceFrame; isFirst: boolean; isLast: boolean }) {
  const localFrame = useCurrentFrame();
  const scale = interpolate(
    localFrame,
    [0, Math.max(1, frame.duration - 1)],
    [frame.scaleFrom ?? 1.015, frame.scaleTo ?? 1.075],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const opacity = interpolate(
    localFrame,
    [0, CROSSFADE_FRAMES, Math.max(CROSSFADE_FRAMES, frame.duration - CROSSFADE_FRAMES), frame.duration],
    [isFirst ? 1 : 0, 1, 1, isLast ? 1 : 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity }}>
      <Img
        src={staticFile(`frames/${frame.file}`)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: `${frame.focusX}% ${frame.focusY}%`,
        }}
      />
    </AbsoluteFill>
  );
}
export function EvidenceShot({ frames }: { frames: EvidenceFrame[] }) {
  return (
    <AbsoluteFill className="evidence-stack">
      {frames.map((frame, index) => (
        <Sequence key={`${frame.file}-${frame.from}`} from={frame.from} durationInFrames={frame.duration} layout="none">
          <KenBurnsFrame frame={frame} isFirst={index === 0} isLast={index === frames.length - 1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
}
