import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const videoDirectory = path.resolve(scriptDirectory, "..");
const manifestPath = path.join(videoDirectory, "capture-manifest.json");
const outputDirectory = path.join(videoDirectory, "public", "frames");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

const landingUrl = process.env.LANDING_URL ?? "http://127.0.0.1:4173";
const replayUrl = process.env.REPLAY_URL ?? "http://127.0.0.1:8000/replay";
const deployedUrl = process.env.DEPLOYED_URL?.trim() || undefined;
const requireDeployed = /^(1|true|yes)$/i.test(process.env.REQUIRE_DEPLOYED ?? "false");
const captureFrame = process.env.CAPTURE_FRAME?.trim() || undefined;
const captureTimeoutMs = Number(process.env.CAPTURE_TIMEOUT_MS ?? 90_000);
const expectedObjective = "Add privacy-safe session evidence export API";
const expectedModel = "gpt-5.6-sol";
const implementationThread = "019f693d-e649-7a91-8dd3-f2cf1a772516";
const reviewThread = "019f6940-61f5-7ea2-85e8-d20a1afaaf6f";
const diffSha256 = "40eae170d3cadfa956810ab3a4c47467b0f14eea1fab232f1b9e55a90a176b33";
const sentinelStdoutSha256 = "e808f9e27f781515bf11c4fd490d7c7757ce086ef58c6d4a9582a6cad6d521d6";

const normalizeSpace = (value) => value.replace(/\s+/g, " ").trim();

const urlAt = (base, pathname) => {
  const url = new URL(base);
  url.pathname = pathname;
  url.search = "";
  url.hash = "";
  return url.toString();
};

const assertLocatorContains = async (locator, expectedValues, label) => {
  const count = await locator.count();
  assert.ok(count > 0, `${label} was not found`);
  const text = normalizeSpace(await locator.first().innerText());
  for (const expected of expectedValues ?? []) {
    assert.ok(
      text.toLocaleLowerCase().includes(normalizeSpace(expected).toLocaleLowerCase()),
      `${label} did not contain ${JSON.stringify(expected)}. Actual text: ${text}`,
    );
  }
};

const assertCopyableValue = async (page, value, label) => {
  const copyButton = page.locator(`button[title="${value}"]`);
  assert.ok(await copyButton.count() > 0, `${label} ${value} was not exposed as a full copyable value`);
};

const waitForFonts = async (page) => {
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map((image) => {
      if (image.complete) return undefined;
      return new Promise((resolve, reject) => {
        image.addEventListener("load", resolve, { once: true });
        image.addEventListener("error", reject, { once: true });
      });
    }));
  });
};

const assertHealth = async (page, baseUrl, label) => {
  const healthUrl = urlAt(baseUrl, "/api/health");
  const response = await page.request.get(healthUrl, { timeout: captureTimeoutMs });
  assert.equal(response.status(), 200, `${label} health returned HTTP ${response.status()}`);
  const health = await response.json();
  assert.equal(health.runtime, "deterministic", `${label} runtime must be deterministic`);
  assert.equal(health.event_chain_valid, true, `${label} event chain must be valid`);
  assert.equal(health.events, 89, `${label} must expose exactly 89 events`);
  return health;
};

const assertLanding = async (page, url, { local }) => {
  await page.goto(url, { waitUntil: "networkidle" });
  await waitForFonts(page);

  const disclosure = page.getByRole("note", { name: "Hosted replay disclosure" });
  await disclosure.waitFor({ state: "visible" });
  await assertLocatorContains(disclosure, [
    "This hosted instance runs in deterministic replay mode.",
    "It executes no model calls.",
  ], "hosted replay disclosure");
  await assertLocatorContains(page.locator("body"), ["FIXTURE · DETERMINISTIC"], "fixture provenance badge");

  const replayLinks = page.locator('a[href="/replay"]');
  assert.ok(await replayLinks.count() > 0, "landing page did not expose a /replay action");
  const evidenceLink = page.getByRole("link", { name: /Live gpt-5\.6-sol evidence/i });
  assert.ok(await evidenceLink.count() > 0, "landing page did not expose the live evidence link");

  if (local) {
    const heading = page.getByRole("heading", { level: 1, name: manifest.localLanding.headline, exact: true });
    await heading.waitFor({ state: "visible" });
    const primaryCta = page.getByRole("link", { name: "Open Change Replay", exact: true });
    assert.ok(await primaryCta.count() > 0, "local landing page did not expose the primary replay CTA");
    const heroImage = page.getByRole("img", { name: /Dhurandhar Change Replay showing the three-engineer auction/i });
    await heroImage.waitFor({ state: "visible" });
    const imageLoaded = await heroImage.evaluate((image) => image.complete && image.naturalWidth > 0 && image.naturalHeight > 0);
    assert.equal(imageLoaded, true, "the real product screenshot did not load");
  } else {
    await assertLocatorContains(page.locator("body"), ["Replay the recorded run"], "deployed replay action");
  }
};

const assertReplayShell = async (page) => {
  await page.getByRole("heading", { name: expectedObjective, exact: true }).waitFor({ state: "visible" });
  await assertLocatorContains(page.locator(".topbar"), ["Kernel online", "RECORDED LIVE", "REQUESTED", expectedModel], "replay top bar");
  await assertLocatorContains(page.locator(".run-header"), [expectedObjective, "LIVE RUN · MODEL EVIDENCE"], "run header");
  const slider = page.getByRole("slider", { name: "Replay position" });
  await slider.waitFor({ state: "visible" });
  assert.equal(await slider.getAttribute("max"), "37", "cinema view must expose exactly 38 positions");
};

const waitForSliderValue = async (page, expected) => {
  await page.waitForFunction(
    (value) => document.querySelector('input[aria-label="Replay position"]')?.value === value,
    String(expected),
    { timeout: 10_000 },
  );
};

const navigateToPosition = async (page, position) => {
  assert.ok(position >= 1 && position <= 38, `invalid replay position ${position}`);
  await page.getByRole("button", { name: "Reset replay" }).click();
  await waitForSliderValue(page, 0);

  const next = page.getByRole("button", { name: "Next", exact: true });
  for (let index = 1; index < position; index += 1) {
    await next.click();
    await waitForSliderValue(page, index);
  }
};

const assertPosition = async (page, frame) => {
  const slider = page.getByRole("slider", { name: "Replay position" });
  assert.equal(await slider.inputValue(), String(frame.position - 1), `${frame.file} has the wrong slider value`);
  const positionText = `${String(frame.position).padStart(2, "0")} / 38`;
  await assertLocatorContains(page.locator(".replay-time"), [positionText], `${frame.file} position label`);

  const selected = page.locator(
    `[data-event-id="${frame.eventId}"][data-sequence="${frame.sequence}"][aria-current="step"]`,
  );
  await selected.waitFor({ state: "visible" });
  assert.equal(await selected.count(), 1, `${frame.file} did not select one exact event card`);
  await assertLocatorContains(selected, [`SEQ ${String(frame.sequence).padStart(3, "0")}`, frame.title, ...(frame.selectedProof ?? [])], `${frame.file} selected event`);

  if (frame.inspectorProof?.length) {
    await assertLocatorContains(page.locator(".inspector"), frame.inspectorProof, `${frame.file} inspector`);
  }
  if (frame.pageProof?.length) {
    await assertLocatorContains(page.locator("body"), frame.pageProof, `${frame.file} page proof`);
  }
  return selected;
};

const assertSpecialProof = async (page, frame, selected) => {
  switch (frame.kind) {
    case "objective":
      await assertLocatorContains(selected, ["Objective accepted", "LIVE JOURNAL · ORCHESTRATION"], "objective proof");
      break;
    case "auction": {
      const cards = selected.locator("[data-bid-card]");
      assert.equal(await cards.count(), 3, "auction must expose exactly three bidder cards");
      await assertLocatorContains(selected.locator('[data-bidder="forge"]'), ["22 CR", "0.88", "1"], "Forge bid");
      await assertLocatorContains(selected.locator('[data-bidder="prism"]'), ["24 CR", "0.86", "1"], "Prism bid");
      await assertLocatorContains(selected.locator('[data-bidder="rivet"]'), ["24 CR", "0.89", "selected", "1"], "Rivet bid");
      const economyRows = selected.locator(".auction-economy > div");
      assert.equal(await economyRows.count(), 4, "auction must expose three bid fees and one escrow movement");
      const economyText = normalizeSpace((await economyRows.allInnerTexts()).join(" ")).toLocaleLowerCase();
      assert.equal((economyText.match(/bid fee/g) ?? []).length, 3, "auction must expose three participation fees");
      assert.ok(economyText.includes("escrow") && economyText.includes("−40 cr"), "auction must expose the 40-credit escrow lock");
      break;
    }
    case "implementation-model":
      await assertCopyableValue(page, implementationThread, "implementation thread");
      await assertLocatorContains(page.locator(".inspector .provenance-usage"), ["333,511", "294,400", "6,297", "2,150"], "implementation token boxes");
      break;
    case "implementation-diff":
      await assertCopyableValue(page, diffSha256, "implementation diff SHA-256");
      await assertLocatorContains(selected.locator(".diff-proof"), ["5 changed files", "+226", "−0"], "Git diff proof");
      await assertLocatorContains(page.locator(".inspector .provenance-diff"), ["Diff SHA-256", "+226", "-0", "diff --git"], "inspector diff proof");
      break;
    case "review-model":
      await assertCopyableValue(page, reviewThread, "review thread");
      await assertLocatorContains(page.locator(".inspector .provenance-usage"), ["361,206", "315,904", "3,566", "2,103"], "review token boxes");
      assert.notEqual(implementationThread, reviewThread, "implementation and review thread IDs must be distinct");
      break;
    case "review-verdict":
      await assertLocatorContains(selected.locator(".approval-seal"), ["AEGIS", "APPROVED", "independent verdict"], "Aegis approval seal");
      await assertLocatorContains(page.locator(".inspector .model-final-message"), ['{"verdict":"approved","findings":[]}'], "review final message");
      break;
    case "sentinel-gate":
      await assertLocatorContains(selected.locator(".test-gate-proof"), [
        "SENTINEL RELEASE GATE PASSED",
        "1 executable check",
        "/opt/anaconda3/bin/python3.13 -m pytest -q",
        "EXIT 0",
      ], "Sentinel gate");
      break;
    case "sentinel-hash":
      assert.equal(sentinelStdoutSha256, frame.inspectorProof[0], "manifest Sentinel hash must be exact");
      await assertLocatorContains(page.locator(".inspector .artifact-frame"), [sentinelStdoutSha256], "Sentinel stdout hash");
      break;
    case "promotion":
      await assertLocatorContains(page.locator(".inspector .artifact-frame"), [
        '"environment": "demo-sandbox"',
        '"external_deployment": false',
      ], "internal promotion proof");
      break;
    case "settlement": {
      const ledger = page.locator(".ledger-panel");
      await assertLocatorContains(ledger.locator(".conservation-badge.is-conserved"), ["CONSERVED", "40/40 CR"], "ledger conservation badge");
      const transactions = normalizeSpace((await ledger.locator(".transaction-table").innerText()));
      for (const proof of ["24 CR", "5 CR", "3 CR", "2 CR", "1 CR", "payout", "refund"]) {
        assert.ok(transactions.toLowerCase().includes(proof.toLowerCase()), `settlement table did not contain ${proof}`);
      }
      break;
    }
    case "human-gate": {
      const gate = page.locator(".human-gate");
      await assertLocatorContains(gate, ["The company cannot promote this policy itself.", "Awaiting decision"], "human authority gate");
      const approve = gate.getByRole("button", { name: /Approve(?: and promote)?/i });
      if (await approve.count() > 0) {
        assert.equal(await approve.isDisabled(), true, "policy Approve must remain disabled in read-only playback");
      }
      break;
    }
    default:
      break;
  }
};

const focusProofRegions = async (page, selectors) => {
  const inspector = page.locator(".inspector");
  if (await inspector.count()) await inspector.evaluate((element) => { element.scrollTop = 0; });
  for (const selector of selectors ?? []) {
    const locator = page.locator(selector).first();
    await locator.waitFor({ state: "visible" });
    await locator.evaluate((element) => element.scrollIntoView({ block: "center", inline: "nearest" }));
  }
  await page.waitForTimeout(100);
};

const revealArtifactLine = async (page, value, side = "start") => {
  const artifact = page.locator(".inspector .artifact-frame .diff-view");
  await artifact.evaluate((element, { needle, horizontalSide }) => {
    const line = Array.from(element.querySelectorAll("span")).find((candidate) => candidate.textContent?.includes(needle));
    if (!line) throw new Error(`artifact line containing ${needle} was not found`);
    const elementRect = element.getBoundingClientRect();
    const lineRect = line.getBoundingClientRect();
    element.scrollTop += lineRect.top - elementRect.top - ((element.clientHeight - lineRect.height) / 2);
    element.scrollLeft = horizontalSide === "end" ? element.scrollWidth : 0;
  }, { needle: value, horizontalSide: side });
};

const revealSettlementTail = async (page) => {
  await page.locator(".ledger-panel .transaction-table").evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
};

const captureViewport = async (page, file) => {
  const target = path.join(outputDirectory, file);
  await page.screenshot({
    path: target,
    type: "png",
    fullPage: false,
    animations: "disabled",
    caret: "hide",
  });
  process.stdout.write(`captured ${file}\n`);
};

const captureReplayFrames = async (page) => {
  await assertHealth(page, replayUrl, "local replay");
  await page.goto(replayUrl, { waitUntil: "networkidle" });
  await waitForFonts(page);
  await assertReplayShell(page);

  const requestedFrames = captureFrame
    ? manifest.replay.filter((frame) => frame.file === captureFrame || frame.tailFile === captureFrame)
    : manifest.replay;
  if (captureFrame) assert.equal(requestedFrames.length, 1, `CAPTURE_FRAME ${captureFrame} did not match one manifest entry`);

  for (const frame of requestedFrames) {
    await navigateToPosition(page, frame.position);
    const selected = await assertPosition(page, frame);
    await assertSpecialProof(page, frame, selected);
    await focusProofRegions(page, frame.focus);
    if (frame.kind === "sentinel-hash") await revealArtifactLine(page, sentinelStdoutSha256, "start");
    await captureViewport(page, frame.file);
    if (frame.kind === "sentinel-hash" && frame.tailFile) {
      await revealArtifactLine(page, sentinelStdoutSha256, "end");
      await captureViewport(page, frame.tailFile);
    }
    if (frame.kind === "settlement" && frame.tailFile) {
      await revealSettlementTail(page);
      await captureViewport(page, frame.tailFile);
    }
  }
};

const captureDeployed = async (page, baseUrl) => {
  await assertHealth(page, baseUrl, "deployed replay");
  await assertLanding(page, urlAt(baseUrl, "/"), { local: false });
  await captureViewport(page, manifest.deployed.landingFile);

  await page.goto(urlAt(baseUrl, "/replay"), { waitUntil: "networkidle" });
  await waitForFonts(page);
  await assertReplayShell(page);
  await assertLocatorContains(page.locator(".topbar"), ["MODE", "read-only"], "deployed read-only boundary");
  await captureViewport(page, manifest.deployed.replayFile);
};

await mkdir(outputDirectory, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: {
    width: manifest.viewport.width,
    height: manifest.viewport.height,
  },
  screen: {
    width: manifest.viewport.width,
    height: manifest.viewport.height,
  },
  deviceScaleFactor: manifest.viewport.deviceScaleFactor,
  reducedMotion: manifest.viewport.reducedMotion,
  colorScheme: "dark",
});

try {
  const page = await context.newPage();
  page.setDefaultTimeout(captureTimeoutMs);
  page.setDefaultNavigationTimeout(captureTimeoutMs);

  await assertLanding(page, landingUrl, { local: true });
  await captureViewport(page, manifest.localLanding.file);
  await captureReplayFrames(page);

  if (deployedUrl) {
    await captureDeployed(page, deployedUrl);
  } else if (requireDeployed) {
    throw new Error("REQUIRE_DEPLOYED=true but DEPLOYED_URL is not set");
  } else {
    process.stdout.write("skipped deployed frames because DEPLOYED_URL is not set\n");
  }
} finally {
  await context.close();
  await browser.close();
}
