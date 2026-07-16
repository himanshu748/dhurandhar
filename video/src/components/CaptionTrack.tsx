import { Sequence } from "remotion";
import type { CaptionCue } from "../scenes";

export function CaptionTrack({ cues, position = "bottom" }: { cues: CaptionCue[]; position?: "top" | "bottom" }) {
  return (
    <>
      {cues.map((cue) => (
        <Sequence key={`${cue.from}-${cue.text}`} from={cue.from} durationInFrames={cue.duration} layout="none">
          <div className={`caption-shell caption-shell-${position}`}>
            <p>{cue.text}</p>
          </div>
        </Sequence>
      ))}
    </>
  );
}
