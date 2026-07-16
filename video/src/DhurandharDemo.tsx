import { Audio } from "@remotion/media";
import { AbsoluteFill, Sequence, staticFile } from "remotion";
import { CaptionTrack } from "./components/CaptionTrack";
import { EndCard } from "./components/EndCard";
import { EvidenceShot } from "./components/EvidenceShot";
import { SceneChrome } from "./components/SceneChrome";
import { TitleCard } from "./components/TitleCard";
import { scenes } from "./scenes";
import "./styles.css";

export function DhurandharDemo() {
  return (
    <AbsoluteFill className="video-root">
      {/* Silent audio bed. Replace this source with the final narration without changing scene timing. */}
      <Audio src={staticFile("audio/narration-placeholder.wav")} loop />
      {scenes.map((scene) => (
        <Sequence key={scene.id} from={scene.from} durationInFrames={scene.duration} name={`${scene.number} ${scene.label}`}>
          <AbsoluteFill>
            <EvidenceShot frames={scene.frames} />
            <SceneChrome number={scene.number} label={scene.label} />
            <CaptionTrack cues={scene.captions} position={scene.captionPosition} />
            {scene.id === "objective" ? <TitleCard /> : null}
            {scene.id === "public-viewer" ? <EndCard startsAt={344} /> : null}
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
}
