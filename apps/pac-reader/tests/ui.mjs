// Browser smoke test of the single-file build (dist/pac-reader.html), opened from disk.
// Usage: node tests/ui.mjs [--shots <dir>]
import * as pac from "../pac.js";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { citationJudge, summaryJudge, policyText, exceptionText, policySummary, exceptionSummary, definitionSummary } from "./citation-fixture.mjs";

import { termGenerator, termJudge } from "./terms-fixture.mjs";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const here = dirname(fileURLToPath(import.meta.url));
const shots = process.argv.includes("--shots") ? process.argv[process.argv.indexOf("--shots") + 1] : null;
const fail = (m) => { console.error("FAIL:", m); process.exit(1); };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 900, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(pathToFileURL(join(here, "../dist/pac-reader.html")).href);
const legacyDir = join(here, "fixtures/legacy");
const legacyFiles = ["generator.json", "judge.json", "bundle.json", "conformance.jsonl", "BUNDLE.md"].map((name) => join(legacyDir, name));
const loadLegacy = () => page.locator("#pick-files").setInputFiles(legacyFiles);
await loadLegacy();
await page.waitForSelector("#pick-category .cat");
if (!(await page.textContent("#bundle-info")).includes("self-exam passed")) fail("exam badge not shown");
const guide = page.locator("#bundle-info .bundle-guide");
await guide.locator("summary").click();
const exampleDir = legacyDir;
const exampleGuide = await readFile(join(exampleDir, "BUNDLE.md"), "utf8");
if (await guide.getAttribute("open") === null || (await guide.locator("pre").textContent()) !== exampleGuide) fail("example Guide does not show the original plain text");
await guide.locator("summary").click();
if (shots) await page.screenshot({ path: join(shots, "0-categories.png"), fullPage: true });

// build cases: category -> features -> relationship
const pickCat = (name) => page.locator("#pick-category .cat", { hasText: name }).click();
const val = async (ci, key, v) => {  // open the folder in the feature directory, then choose the feature
  const leaf = `#cases .val[data-case="${ci}"][data-key="${key}"][data-value="${v}"]`;
  if (!(await page.locator(leaf).count())) {
    const folder = page.locator(`#cases .folder[data-case="${ci}"][data-open="${key}"]`);
    if (!(await folder.count())) await page.click(`#cases .folder[data-more="${ci}"]`);
    await page.click(`#cases .folder[data-case="${ci}"][data-open="${key}"]`);
  }
  await page.click(leaf);
};
const use = () => page.click("#use-here");
await pickCat("Content creation"); await pickCat("Ordinary content");
await val(0, "act", "biz");
const ordinaryCode = await page.textContent("#build-code");
const space = pac.Space.fromTexts(await readFile(join(exampleDir, "generator.json"), "utf8"),
  await readFile(join(exampleDir, "judge.json"), "utf8"));
const ordinary = pac.check(ordinaryCode, space), boundary = pac.check("act=biz pur=std fic=real", space);
if (ordinaryCode !== "act=biz pur=std" || ordinary.verdict !== "compliant" || ordinary.violated.length
    || ordinary.verdict !== boundary.verdict || ordinary.violated.join() !== boundary.violated.join()) fail("ordinary content judgment differs from boundary fixture");
await page.click("#judge-cases");
await page.waitForSelector("#result:not([hidden])");
if (!(await page.textContent("#report")).includes("Allowed as coded.")) fail("ordinary content not allowed in browser");
await page.click("#restart");
await page.waitForSelector("#pick-category .cat");
await pickCat("Security or systems work");  // has narrower categories: drill in, then use it as is
if (!(await page.textContent("#pick-category .crumbs")).includes("Security or systems work")) fail("no breadcrumb");
await use();
await val(0, "act", "biz");
await page.click('#cases .folder[data-case="0"][data-open="pur"]');
if (!(await page.locator('#cases .folder[data-case="0"][data-open="auth"]').count())) fail("auth folder not nested under purpose");
// auth stays skipped: it can't be confirmed
await page.click("#add-case");
await pickCat("Chatbot or assistant"); await pickCat("Everyday help");
await val(1, "act", "biz"); await val(1, "disc", "y");
await page.click('#cases .seg button[data-rel="same"][data-case="1"]');
await page.click("#add-case");
await pickCat("Recommendation in a high-risk area"); await pickCat("Insurance"); await pickCat("About a specific person"); await pickCat("Other or adverse decision");
await val(2, "act", "biz"); await val(2, "pur", "std");
await page.fill('#cases input[data-note="2"]', "claims team pilot");
const built = await page.textContent("#build-code");
if (built !== "act=biz pur=cyber & act=biz pur=std disc=y chat=y > act=biz pur=std hr=ins scope=ind fav=part") fail("built code: " + built);
if (shots) await page.screenshot({ path: join(shots, "1-cases.png"), fullPage: true });
await page.click("#judge-cases");
await page.waitForSelector("#result:not([hidden])");
const cases = await page.textContent("#report");
for (const want of ["Step 1: 2 actions at the same time", "Possible results once the unknown facts are known", "If auth=own (1 of 3): Allowed as coded.", "claims team pilot", "Qualified human-in-the-loop"]) {
  if (!cases.includes(want)) fail(`cases report lacks "${want}"`);
}
if (shots) await page.screenshot({ path: join(shots, "2-cases-report.png"), fullPage: true });

// a single case with a violation: the fix and the case note are shown
await page.click("#restart");
await page.waitForSelector("#pick-category .cat");
if (await page.locator('.tab[data-tab="form"]').count()) fail("old question tab still shown");
await pickCat("Security or systems work"); await pickCat("Systems without permission");
await page.fill('#cases input[data-note="0"]', "red-team request from ticket 42");
await page.click("#judge-cases");
await page.waitForSelector("#result:not([hidden])");
const report = await page.textContent("#report");
if (!report.includes("Not allowed as coded")) fail("expected a violation verdict, got: " + report.slice(0, 200));
if (!report.includes("red-team request from ticket 42")) fail("note not shown");
if (!report.includes("auth=unauth -> auth=own")) fail("fix not shown");
if (shots) await page.screenshot({ path: join(shots, "3-report.png"), fullPage: true });

if (await page.locator("#code, .tab").count()) fail("old tabs still shown");

// arrange: move a likely category and a feature to the top; the order is remembered, judging unchanged
await page.click("#restart");
await page.click("#arrange");
const firstCat = async () => (await page.locator("#pick-category .cat strong").first().textContent());
const before = await firstCat();
await page.locator('#pick-category .mv[data-id="security"][data-dir="-1"]').click();
await page.locator('#pick-category .mv[data-id="security"][data-dir="-1"]').click();
if ((await firstCat()) !== "Security or systems work") fail(`category not moved up (was ${before}, now ${await firstCat()})`);
await pickCat("Security or systems work"); await use();
await page.locator('#cases .folder[data-case="0"][data-open="pur"]').click();
await page.locator('#cases .mv[data-mv="folder"][data-id="pur"][data-dir="-1"]').click();
if ((await page.locator("#cases .tree .node:not(.root) > .folder .fname").first().textContent()) !== (await page.evaluate(() => "what the action does (observable functions; one or more, written a+b)"))) fail("folder not moved up");
await page.locator('#cases .mv[data-mv="value"][data-id="cyber"][data-dir="-1"]').click();
const vals = await page.locator('#cases .val[data-key="pur"]').evaluateAll((els) => els.map((e) => e.dataset.value));
if (vals.indexOf("cyber") !== 6) fail("value not moved up: " + vals.join(","));
await page.reload();
await loadLegacy();
await page.waitForSelector("#pick-category .cat");
if ((await firstCat()) !== "Security or systems work") fail("order not remembered");
await page.click("#arrange"); await page.click("#reset-order");
if ((await firstCat()) !== "Chatbot or assistant") fail("reset did not restore the order");

const accepts = await page.locator("#pick-files").getAttribute("accept");
if (!accepts?.split(",").map((item) => item.trim()).includes(".md")) fail("file picker does not accept Markdown");

// A separately loaded guide participates in the digest check but is never interpreted as HTML.
const bundleFiles = ["generator.json", "judge.json", "bundle.json"].map((name) => join(exampleDir, name));
const plainText = '<img src="missing" onerror="this.remove()">\n# Untrusted Markdown\n';
const payloads = await Promise.all(bundleFiles.map(async (path) => ({
  name: path.split("/").pop(),
  mimeType: "application/json",
  buffer: await readFile(path),
})));
await page.locator("#pick-files").setInputFiles([
  ...payloads,
  { name: "BUNDLE.md", mimeType: "text/markdown", buffer: Buffer.from(plainText) },
]);
await page.waitForSelector("#bundle-info .badge.bad");
if (!(await page.textContent("#bundle-info .badge.bad")).includes("BUNDLE.md")) fail("tampered guide digest not reported");
await guide.locator("summary").click();
if ((await guide.locator("pre").textContent()) !== plainText || await guide.locator("img").count()) fail("guide was not rendered as plain text");
await page.locator("#pick-files").setInputFiles(payloads);
await page.waitForSelector("#bundle-info .bundle-guide", { state: "detached" });

// A synthetic policy excerpt tests exact text, attribution, and literal HTML rendering.
await page.locator("#pick-files").setInputFiles([
  payloads[0],
  { name: "judge.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(citationJudge(space.judge))) },
]);
await page.waitForSelector("#bundle-info .badge.warn", { state: "visible" });
await pickCat("Security or systems work"); await pickCat("Systems without permission");
await page.click("#judge-cases");
const quoted = page.locator("#report blockquote").filter({ hasText: policyText });
if (await quoted.locator("span").textContent() !== policyText
    || await quoted.locator("cite").textContent() !== "Example rules, test-rule"
    || await quoted.locator("b").count()) fail("violated rule did not render its exact policy text and attribution as plain text");
const exception = page.locator("#report blockquote").filter({ hasText: exceptionText });
if (!(await exception.textContent()).includes("Exception (does not apply)")) fail("exception citation not labelled");

await page.locator("#pick-files").setInputFiles([
  payloads[0],
  { name: "judge.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(summaryJudge(space.judge))) },
]);
await pickCat("Security or systems work"); await pickCat("Systems without permission");
await page.click("#judge-cases");
for (const [label, summary] of [["", policySummary], ["Exception (does not apply): ", exceptionSummary],
  ["Definition: ", definitionSummary]]) {
  const cited = page.locator("#report .term-summary").filter({ hasText: summary });
  if (await cited.locator("span").textContent() !== summary
      || await cited.locator("strong").textContent() !== `${label}Summary (not a quote): `
      || await cited.locator("b").count()) fail("summary was not rendered as labelled, unquoted plain text");
}
if (await page.locator("#report blockquote").count()) fail("a paraphrase was rendered as a policy blockquote");

// Format 2.0 has a single term map; the synthetic bundle makes every interaction inspectable.
const loadTerms = (generator = termGenerator) => page.locator("#pick-files").setInputFiles([
  { name: "generator.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(generator)) },
  { name: "judge.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(termJudge)) },
]);
await loadTerms();
await page.waitForSelector("#term-order");
if (await page.locator("#pick-category .cat:visible").count()) fail("2.0 shows 1.x categories");
const node = (id) => page.locator(`[data-node="${id}"]`);
const termButton = (id) => page.locator(`[data-term="${id}"][data-term-action="term"]`);
const termChoice = (id, code) => page.locator(`[data-term="${id}"][data-value="${code}"]`);
if (await node("c02").count()) fail("child appears before parent is chosen");
await page.selectOption("#term-order", "split");
if (!(await page.locator(".guided-terms").textContent()).includes("Auto-skipped: fixed=y")) fail("forced constant not shown");
if ((await page.locator(".guided-terms").textContent()).includes("verdict won't change")) fail("split stops before a changeable child opens");
await page.selectOption("#term-order", "map");
await termButton("c01").click();
await termChoice("c01", "y").click();
if (!(await node("c02").getAttribute("class"))?.split(" ").includes("enter")) fail("new child did not get enter animation");
if (!(await node("c01").getAttribute("class"))?.split(" ").includes("changed")) fail("changed parent status did not get an animation");
if (!(await termChoice("c01", "y").evaluate((el) => document.activeElement === el))) fail("focus did not follow the rebuilt chip");
await termButton("c02").click();
const termsLeft = async () => {
  const copy = await page.locator("#dock-terms").textContent();
  if (copy.includes("All terms answered")) return 0;
  const count = copy.match(/(\d+) terms? left/);
  if (!count) fail("terms-left label is missing its count: " + copy);
  return Number(count[1]);
};
const beforeAnswer = await termsLeft();
const number = node("c02").locator('input[inputmode="numeric"]');
if (!(await node("c02").textContent()).includes("18 years")) fail("number limit/unit missing");
await number.fill("151");
await node("c02").locator('form button').click();
if (!(await node("c02").locator(".number-error").textContent()).includes("out of bounds")) fail("invalid number was accepted");
await number.fill("17 disc=n");
await number.press("Enter");
if (!(await node("c02").locator(".number-error").textContent()).includes("one number")) fail("number field accepted multiple facts");
await number.fill("017.0");
await number.press("Enter");
if ((await page.textContent("#build-code")) !== "act=y age=17") fail("number not canonicalized");
if (!(await node("c02").locator(".badge").textContent()).includes("Violated")) fail("number not reflected in live rule badge");
if (await termsLeft() >= beforeAnswer) fail("answering an open term did not reduce the dock count");
if (!(await node("c02").locator("blockquote").textContent()).includes(termJudge.terms.c02.text)) fail("matched term missing citation");
await termButton("c04").click();
if (!(await node("c04").textContent()).includes("answered under Underage case")) fail("shared fact does not show where it was answered");
await page.locator('[data-term="c01"][data-term-action="skip"]').click();
if (await node("c02").count() || (await page.textContent("#build-code")) !== "act=? age=17"
    || !(await node("c01").locator(".term-pending").textContent()).includes("age=17 answered, applies once Scope gate holds")) {
  fail("an answered fact behind an unknown parent is not shown or retained");
}
await termChoice("c01", "n").click();
if (await node("c02").count() || (await page.textContent("#build-code")) !== "act=n age=17") fail("shared fact removed with one parent path");
await page.selectOption("#term-order", "split");
if (!(await page.locator(".guided-terms").textContent()).includes("The verdict won't change")) fail("settled split message missing");
await page.selectOption("#term-order", "map");
await node("c04").locator('input[inputmode="numeric"]').fill("21");
await node("c04").locator('input[inputmode="numeric"]').press("Enter");
await termChoice("c01", "y").click();
await termChoice("c01", "n").click();
if ((await page.textContent("#build-code")) !== "act=n age=21") fail("still-visible shared answer was lost");
if (await node("c03").count()) fail("other-party duty was not folded");
await page.getByRole("button", { name: "Other parties' duties" }).click();
await termButton("c03").click();
if (await termChoice("c03", "y").getAttribute("aria-pressed") !== "true") fail("preset choice not pre-selected");
if (!(await node("c03").textContent()).includes("Pre-selected: this is provider's duty (term c03)")) fail("preset reason missing");
await node("c03").getByRole("button", { name: "Don't know (skip)" }).click();
if (!(await page.textContent("#build-code")).includes("disc=?")) fail("skip did not override the preset");
if (!(await node("c03").locator(".badge").textContent()).includes("Required next")) fail("preset unknown override not judged");
await node("c03").getByRole("button", { name: "Reset to pre-selected" }).click();
if ((await page.textContent("#build-code")).includes("disc=") || await termChoice("c03", "y").getAttribute("aria-pressed") !== "true") fail("reset does not clear the code override");
await page.click("#judge-cases");
const dutyReport = await page.textContent("#report");
if (!dutyReport.includes("Relies on provider meeting Publish disclosure (c03)")) fail("report omits preset reliance");
if (!dutyReport.includes("disc=y (pre-selected: provider's duty, c03)")) fail("report omits preset reason");

// With no other node testing age, a false parent removes the fact and explains
// the removal in both the editor and report. Reopening does not resurrect it.
const exclusive = structuredClone(termGenerator);
exclusive.term_map.nodes.c04.keys = exclusive.term_map.nodes.c04.keys.filter((k) => k.dim !== "age");
exclusive.term_map.nodes.c03.keys[0].why = "stated";
await page.locator("#pick-files").setInputFiles([
  { name: "generator.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(exclusive)) },
  { name: "judge.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(termJudge)) },
]);
await page.waitForSelector("#term-order");
await termButton("c01").click();
await termChoice("c01", "y").click();
await termButton("c02").click();
await number.fill("17"); await number.press("Enter");
await termChoice("c01", "n").click();
if ((await page.textContent("#build-code")) !== "act=n") fail("ruled-out answer was retained");
const notice = "Not used: age=17, because Underage case (c02) doesn't apply.";
if (!(await page.locator(".term-dropped").textContent()).includes(notice)) fail("editor omits removal explanation");
await page.click("#judge-cases");
const dropReport = await page.textContent("#report");
if (!dropReport.includes(notice) || !dropReport.includes("disc=y (pre-selected: stated in c03)")) {
  fail("report omits removed fact or stated preset reason");
}
await termChoice("c01", "y").click();
if ((await page.textContent("#build-code")) !== "act=y" || await page.locator(".term-dropped").count()) {
  fail("reopening a term resurrected a removed fact or kept a stale notice");
}

// Phone keyboards and pasted values may contain fullwidth digits, grouping, or
// the shown unit. The reader normalizes them before using the engine's number parser.
const looseAge = structuredClone(termGenerator);
Object.assign(looseAge.dimensions.find(({ key }) => key === "age"), { max: 2000, integer: false });
await loadTerms(looseAge);
await termButton("c01").click();
await termChoice("c01", "y").click();
await termButton("c02").click();
const localNumber = node("c02").locator('input[inputmode]');
for (const [input, normalized] of [["５０", "50"], ["1,000", "1000"], ["５０．５ years", "50.5"], ["５０。５", "50.5"]]) {
  await localNumber.fill(input);
  await localNumber.press("Enter");
  if ((await page.textContent("#build-code")) !== `act=y age=${normalized}`) fail(`number "${input}" did not become age=${normalized}`);
}
for (const invalid of ["50 apples", "1,00"]) {
  await localNumber.fill(invalid);
  await localNumber.press("Enter");
  if (!(await node("c02").locator(".number-error").textContent()).trim() || (await page.textContent("#build-code")) !== "act=y age=50.5") {
    fail("invalid input was accepted or changed the saved number: " + invalid);
  }
}

// Shipped example opens offline as 2.0 after migration and keeps its Guide available.
await page.click("#load-example");
await page.locator("#bundle-info").filter({ hasText: "format 2.0" }).waitFor();
await page.waitForSelector("#term-order");
await page.waitForSelector("#bundle-info .bundle-guide");

// Preserve layout and full functionality with animations disabled, in dark mode at 390px.
await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
await page.setViewportSize({ width: 390, height: 844 });
await page.reload();  // start this pass with reduced motion already active
const assertReducedMotion = async () => {
  const activeMotion = await page.evaluate(() => {
    const seconds = (v) => v.endsWith("ms") ? parseFloat(v) / 1000 : parseFloat(v);
    for (const el of document.querySelectorAll("body, body *")) {
      for (const pseudo of [null, "::before", "::after"]) {
        const css = getComputedStyle(el, pseudo);
        for (const property of ["animationDuration", "transitionDuration"]) {
          if (css[property].split(",").some((value) => seconds(value.trim()) > 0.001)) {
            return String(el.tagName) + (pseudo || "") + " " + property + "=" + css[property];
          }
        }
        if (css.scrollBehavior === "smooth" || css.animationIterationCount.includes("infinite")) {
          return String(el.tagName) + (pseudo || "") + " infinite animation or smooth scrolling";
        }
      }
    }
    return null;
  });
  if (activeMotion) fail("reduced-motion style not applied: " + activeMotion);
};
const assertNoOverflow = async () => {
  const widths = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  if (widths[0] > widths[1]) fail("horizontal overflow on mobile: " + widths.join(" > "));
};
await loadTerms();
await termButton("c01").click();
await termChoice("c01", "y").click();
await termButton("c02").click();
await number.fill("17"); await number.press("Enter");
await assertReducedMotion();
await assertNoOverflow();
await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
const compactDock = await page.evaluate(() => {
  const byId = (id) => document.getElementById(id);
  const dock = byId("build-bar");
  const judge = byId("judge-cases").getBoundingClientRect();
  const ring = dock.querySelector(".dock-ring").getBoundingClientRect();
  const code = byId("build-code").getBoundingClientRect();
  const add = byId("add-case");
  const addRect = add.getBoundingClientRect();
  const dockRect = dock.getBoundingClientRect();
  const lastCase = [...byId("cases").querySelectorAll(".case")].at(-1);
  return {
    height: dockRect.height,
    bottomPadding: parseFloat(getComputedStyle(document.body).paddingBottom),
    ring: ring.width,
    oneRow: judge.left >= ring.right && Math.abs((judge.top + judge.bottom - ring.top - ring.bottom) / 2) <= 12,
    codeHidden: code.width <= 1 || code.height <= 1 || getComputedStyle(byId("build-code")).visibility === "hidden",
    addUnderCases: Boolean(lastCase.compareDocumentPosition(add) & Node.DOCUMENT_POSITION_FOLLOWING) && !dock.contains(add),
    addUncovered: addRect.top >= 0 && addRect.bottom <= dockRect.top,
  };
});
if (compactDock.height > 96 || Math.abs(compactDock.height - compactDock.bottomPadding) > 1
    || compactDock.ring < 38 || compactDock.ring > 42 || !compactDock.oneRow
    || !compactDock.codeHidden || !compactDock.addUnderCases || !compactDock.addUncovered) {
  fail("mobile dock layout: " + JSON.stringify(compactDock));
}
await page.click("#add-case");
if (await page.locator("#cases .case").count() !== 2) fail("mobile add case button is not functional");
await page.click('#cases button[data-remove="1"]');
await page.click("#judge-cases");
await page.waitForSelector("#result:not([hidden])");
for (const label of ["Violated terms", "Required next", "Open terms"]) {
  if (!(await page.locator(".verdict-stat span").allTextContents()).includes(label)) fail("missing stat label: " + label);
}
await assertReducedMotion();
await assertNoOverflow();
const stats = await page.locator(".verdict-stat [data-target]").evaluateAll(
  (tiles) => tiles.length > 0 && tiles.every((tile) => tile.textContent === tile.dataset.target),
);
if (!stats) fail("reduced motion did not show final stat counts immediately");
if (await page.locator(".verdict-burst, .click-ripple").count()) fail("reduced motion rendered a burst or ripple");
if (errors.length) fail("browser errors: " + errors.join("; "));
await browser.close();
console.log("ui ok");
