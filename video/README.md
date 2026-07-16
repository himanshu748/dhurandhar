# Dhurandhar demo video

This isolated Remotion project renders the Build Week evidence video at 1920x1080, 30fps and exactly 2:55. The application dependencies in `frontend/` are not changed.

## Capture

First follow the immutable playback preflight in `docs/VIDEO_SHOT_LIST.md`. Both journal copies must have SHA-256 `cc6cad770642bbc667ed3d4c3a9de789717b720710bf54801659000e6ae0d8b5`, the playback API must report 89 valid deterministic events and an unauthenticated objective POST must return 503.

With the local landing and playback servers running:

```bash
npm install
npx playwright install chromium
LANDING_URL=http://127.0.0.1:4173 \
REPLAY_URL=http://127.0.0.1:8000/replay \
DEPLOYED_URL=https://dhurandhar-asc.onrender.com \
REQUIRE_DEPLOYED=true \
npm run capture
```

The capture script fails closed on the journal health, objective, selected sequence and proof fields before writing each frame. It never clicks the policy approval control.

## Render

```bash
npm run typecheck
npm run render
```

The output is `video/out/dhurandhar-demo.mp4`. `video/out/` is ignored and must not be committed.

The committed WAV is intentionally silent. Replace it with recorded narration later without changing the seven scene boundaries. Every shot-list narration passage is retained verbatim beside a `NARRATION SLOT` comment in `src/scenes.ts`.

The shot list also requires a separate closing sentence after the public-viewer narration. Those two passages do not fit naturally inside the locked final 15 seconds. The closing sentence is therefore present on the end card, and the voiceover editor must resolve that timing conflict rather than dropping or paraphrasing either passage.
