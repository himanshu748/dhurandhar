import { Composition } from "remotion";
import { DhurandharDemo } from "./DhurandharDemo";
import { DURATION_IN_FRAMES, FPS, HEIGHT, WIDTH } from "./scenes";

export function RemotionRoot() {
  return (
    <Composition
      id="DhurandharDemo"
      component={DhurandharDemo}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
}
