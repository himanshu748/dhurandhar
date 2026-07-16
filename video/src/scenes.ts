export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const DURATION_IN_FRAMES = 5250;

export type CaptionCue = {
  from: number;
  duration: number;
  text: string;
};

export type EvidenceFrame = {
  file: string;
  from: number;
  duration: number;
  focusX: number;
  focusY: number;
  scaleFrom?: number;
  scaleTo?: number;
};

export type DemoScene = {
  id: string;
  number: string;
  label: string;
  from: number;
  duration: number;
  captionPosition?: "top" | "bottom";
  narration: string;
  captions: CaptionCue[];
  frames: EvidenceFrame[];
};

// NARRATION SLOT 01, verbatim from docs/VIDEO_SHOT_LIST.md.
// The final voiceover must also identify the primary Codex collaboration session:
// 019f6172-596f-7d50-a842-b839fd16af3e.
const objectiveNarration =
  "Dhurandhar turns one bounded software objective into an auditable company run: allocation, implementation, independent review, verification, recovery, and learning.";

// NARRATION SLOT 02, verbatim from docs/VIDEO_SHOT_LIST.md.
const auctionNarration =
  "Forge, Prism, and Rivet all paid to bid. Forge and Prism were cheaper or tied but lacked the required container capability; Rivet was the lowest eligible bid, so Atlas locked the 40-credit bounty in escrow.";

// NARRATION SLOT 03A and 03B, verbatim from docs/VIDEO_SHOT_LIST.md.
const boundariesNarration =
  "This invocation requested the authenticated gpt-5.6-sol slug in a bounded workspace-write session. Codex's JSONL supplied the exact thread, token categories, commands, and files; Git evidence was computed by the kernel. The stream did not echo the model back, and the evidence document names that limitation. Aegis invoked Codex again requesting the same slug, but in a separate read-only thread. The implementing session cannot approve itself.";

// NARRATION SLOT 04, verbatim from docs/VIDEO_SHOT_LIST.md.
const diffNarration =
  "The write is proved by Git metadata computed outside the model. Aegis then returned a structured approval from an independent read-only thread.";

// NARRATION SLOT 05, verbatim from docs/VIDEO_SHOT_LIST.md.
const gateNarration =
  "Sentinel—not the reviewer—ran the static-allowlist release test with a real exit code of zero. Shipwright promoted only to the reversible demo sandbox, never to external infrastructure, and all 40 escrow credits are visibly conserved.";

// NARRATION SLOT 06, verbatim from docs/VIDEO_SHOT_LIST.md.
const recoveryNarration =
  "A controlled regression assigns liability across implementation, review, QA, and release, restores the known-good sandbox, and proposes four runtime-backed controls. Only a human can activate them.";

// NARRATION SLOT 07, verbatim from docs/VIDEO_SHOT_LIST.md.
// The guide also requires the closing sentence below. It is printed on the end card
// because the locked 15-second scene cannot carry both passages at a natural pace.
const publicNarration =
  "The deployed Render URL is an intentionally read-only, no-secret deterministic viewer. It makes no model calls now; it replays the same committed 89-event journal whose implementation and review calls each requested gpt-5.6-sol.";

export const closingSentence =
  "Dhurandhar does not ask you to trust an agent transcript. It shows who did what, which evidence allowed the next step, what failure cost, and exactly where the human still decides.";

export const scenes: DemoScene[] = [
  {
    id: "objective",
    number: "01",
    label: "Objective filed",
    from: 0,
    duration: 540,
    narration: objectiveNarration,
    captions: [
      {
        from: 84,
        duration: 206,
        text: "Dhurandhar turns one bounded software objective into an auditable company run:",
      },
      {
        from: 290,
        duration: 250,
        text: "allocation, implementation, independent review, verification, recovery, and learning.",
      },
    ],
    frames: [
      { file: "00-local-landing.png", from: 0, duration: 104, focusX: 50, focusY: 40, scaleFrom: 1, scaleTo: 1.025 },
      { file: "01-objective-seq033.png", from: 88, duration: 452, focusX: 62, focusY: 34, scaleFrom: 1.015, scaleTo: 1.075 },
    ],
  },
  {
    id: "auction",
    number: "02",
    label: "Three-bid auction and escrow",
    from: 540,
    duration: 720,
    narration: auctionNarration,
    captions: [
      { from: 20, duration: 185, text: "Forge, Prism, and Rivet all paid to bid." },
      {
        from: 205,
        duration: 290,
        text: "Forge and Prism were cheaper or tied but lacked the required container capability;",
      },
      {
        from: 495,
        duration: 225,
        text: "Rivet was the lowest eligible bid, so Atlas locked the 40-credit bounty in escrow.",
      },
    ],
    frames: [
      { file: "02-auction-seq049.png", from: 0, duration: 720, focusX: 74, focusY: 48, scaleFrom: 1.015, scaleTo: 1.085 },
    ],
  },
  {
    id: "boundaries",
    number: "03",
    label: "Two recorded Codex boundaries",
    from: 1260,
    duration: 1140,
    narration: boundariesNarration,
    captions: [
      {
        from: 20,
        duration: 250,
        text: "This invocation requested the authenticated gpt-5.6-sol slug in a bounded workspace-write session.",
      },
      {
        from: 270,
        duration: 300,
        text: "Codex's JSONL supplied the exact thread, token categories, commands, and files; Git evidence was computed by the kernel.",
      },
      {
        from: 570,
        duration: 230,
        text: "The stream did not echo the model back, and the evidence document names that limitation.",
      },
      {
        from: 800,
        duration: 220,
        text: "Aegis invoked Codex again requesting the same slug, but in a separate read-only thread.",
      },
      { from: 1020, duration: 120, text: "The implementing session cannot approve itself." },
    ],
    frames: [
      { file: "03-implementation-model-seq052.png", from: 0, duration: 688, focusX: 78, focusY: 48, scaleFrom: 1.01, scaleTo: 1.08 },
      { file: "05-review-model-seq055.png", from: 672, duration: 468, focusX: 78, focusY: 48, scaleFrom: 1.015, scaleTo: 1.08 },
    ],
  },
  {
    id: "diff-review",
    number: "04",
    label: "Git evidence and independent verdict",
    from: 2400,
    duration: 840,
    narration: diffNarration,
    captions: [
      { from: 36, duration: 360, text: "The write is proved by Git metadata computed outside the model." },
      {
        from: 396,
        duration: 444,
        text: "Aegis then returned a structured approval from an independent read-only thread.",
      },
    ],
    frames: [
      { file: "04-implementation-diff-seq052.png", from: 0, duration: 430, focusX: 76, focusY: 58, scaleFrom: 1.015, scaleTo: 1.08 },
      { file: "06-review-verdict-seq055.png", from: 414, duration: 426, focusX: 78, focusY: 55, scaleFrom: 1.015, scaleTo: 1.08 },
    ],
  },
  {
    id: "gate-settlement",
    number: "05",
    label: "Release gate, promotion and settlement",
    from: 3240,
    duration: 900,
    captionPosition: "top",
    narration: gateNarration,
    captions: [
      {
        from: 20,
        duration: 330,
        text: "Sentinel—not the reviewer—ran the static-allowlist release test with a real exit code of zero.",
      },
      {
        from: 350,
        duration: 300,
        text: "Shipwright promoted only to the reversible demo sandbox, never to external infrastructure,",
      },
      { from: 650, duration: 250, text: "and all 40 escrow credits are visibly conserved." },
    ],
    frames: [
      { file: "07-sentinel-gate-seq057.png", from: 0, duration: 278, focusX: 72, focusY: 48, scaleFrom: 1.01, scaleTo: 1.07 },
      { file: "08-sentinel-hash-seq057.png", from: 262, duration: 112, focusX: 87, focusY: 56, scaleFrom: 1.02, scaleTo: 1.075 },
      { file: "08b-sentinel-hash-tail-seq057.png", from: 358, duration: 96, focusX: 87, focusY: 56, scaleFrom: 1.02, scaleTo: 1.075 },
      { file: "09-promotion-seq060.png", from: 438, duration: 174, focusX: 86, focusY: 54, scaleFrom: 1.015, scaleTo: 1.075 },
      { file: "10-settlement-seq067.png", from: 596, duration: 166, focusX: 62, focusY: 75, scaleFrom: 1.01, scaleTo: 1.065 },
      { file: "10b-settlement-rivet-seq067.png", from: 746, duration: 154, focusX: 62, focusY: 75, scaleFrom: 1.01, scaleTo: 1.065 },
    ],
  },
  {
    id: "recovery",
    number: "06",
    label: "Recovery and human authority",
    from: 4140,
    duration: 660,
    captionPosition: "top",
    narration: recoveryNarration,
    captions: [
      {
        from: 16,
        duration: 300,
        text: "A controlled regression assigns liability across implementation, review, QA, and release,",
      },
      {
        from: 316,
        duration: 230,
        text: "restores the known-good sandbox, and proposes four runtime-backed controls.",
      },
      { from: 546, duration: 114, text: "Only a human can activate them." },
    ],
    frames: [
      { file: "11-recovery-regression-seq079.png", from: 0, duration: 78, focusX: 72, focusY: 52, scaleFrom: 1.015, scaleTo: 1.055 },
      { file: "12-recovery-alert-seq080.png", from: 66, duration: 78, focusX: 74, focusY: 52, scaleFrom: 1.015, scaleTo: 1.055 },
      { file: "13-recovery-rivet-seq081.png", from: 132, duration: 54, focusX: 72, focusY: 60, scaleFrom: 1.02, scaleTo: 1.06 },
      { file: "14-recovery-aegis-seq082.png", from: 174, duration: 54, focusX: 72, focusY: 60, scaleFrom: 1.02, scaleTo: 1.06 },
      { file: "15-recovery-sentinel-seq083.png", from: 216, duration: 54, focusX: 72, focusY: 60, scaleFrom: 1.02, scaleTo: 1.06 },
      { file: "16-recovery-shipwright-seq084.png", from: 258, duration: 54, focusX: 72, focusY: 60, scaleFrom: 1.02, scaleTo: 1.06 },
      { file: "17-recovery-start-seq085.png", from: 300, duration: 72, focusX: 72, focusY: 54, scaleFrom: 1.015, scaleTo: 1.06 },
      { file: "18-recovery-restored-seq086.png", from: 360, duration: 84, focusX: 72, focusY: 54, scaleFrom: 1.015, scaleTo: 1.06 },
      { file: "19-recovery-analysis-seq087.png", from: 432, duration: 66, focusX: 72, focusY: 54, scaleFrom: 1.015, scaleTo: 1.06 },
      { file: "20-recovery-benchmark-seq088.png", from: 486, duration: 66, focusX: 72, focusY: 54, scaleFrom: 1.015, scaleTo: 1.06 },
      { file: "21-recovery-proposal-seq089.png", from: 540, duration: 58, focusX: 72, focusY: 54, scaleFrom: 1.015, scaleTo: 1.06 },
      { file: "22-recovery-human-gate-seq089.png", from: 586, duration: 74, focusX: 74, focusY: 72, scaleFrom: 1.015, scaleTo: 1.065 },
    ],
  },
  {
    id: "public-viewer",
    number: "07",
    label: "Public read-only viewer",
    from: 4800,
    duration: 450,
    narration: publicNarration,
    captions: [
      {
        from: 10,
        duration: 215,
        text: "The deployed Render URL is an intentionally read-only, no-secret deterministic viewer.",
      },
      {
        from: 225,
        duration: 225,
        text: "It makes no model calls now; it replays the same committed 89-event journal whose implementation and review calls each requested gpt-5.6-sol.",
      },
    ],
    frames: [
      { file: "23-deployed-landing.png", from: 0, duration: 224, focusX: 50, focusY: 38, scaleFrom: 1.005, scaleTo: 1.045 },
      { file: "24-deployed-replay.png", from: 208, duration: 152, focusX: 64, focusY: 36, scaleFrom: 1.01, scaleTo: 1.055 },
      { file: "00-local-landing.png", from: 344, duration: 106, focusX: 50, focusY: 40, scaleFrom: 1.02, scaleTo: 1.04 },
    ],
  },
];
