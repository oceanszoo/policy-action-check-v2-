// Parity test: the JS reader must give exactly the same outputs as the reference pac.py.
// Usage: node tests/parity.mjs [bundle dir ...]   (default: the example bundle and any eval bundles)
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as pac from "../pac.js";
import { citationJudge, summaryJudge, policyText, policySummary, exceptionSummary, definitionSummary } from "./citation-fixture.mjs";

import { termGenerator, termJudge } from "./terms-fixture.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../../..");
const defaults = [
  "plugins/policy-action-check/examples/sample-service-terms",
  "apps/pac-reader/tests/fixtures/legacy",
  ...["v1_2", "v1_3"].flatMap((v) => ["built", "seeded"].map((a) => `results/skill_eval/policy_action_check/${v}/${a}/policy_space`)),
].map((p) => join(repo, p)).filter((p) => existsSync(join(p, "generator.json")));
const bundles = process.argv.length > 2 ? process.argv.slice(2) : defaults;

const read = (p) => (existsSync(p) ? readFileSync(p, "utf8") : "");
const norm = (x) => JSON.parse(JSON.stringify(x, (k, v) => (typeof v === "number" ? Number(v.toFixed(9)) : v)));
const same = (a, b) => JSON.stringify(norm(a)) === JSON.stringify(norm(b));

let failures = 0, total = 0;
function expect(label, got, want) {
  total++;
  if (!same(got, want)) {
    failures++;
    if (failures <= 10) console.error(`MISMATCH ${label}\n  js:  ${JSON.stringify(got).slice(0, 400)}\n  py:  ${JSON.stringify(want).slice(0, 400)}`);
  }
}

for (const dir of bundles) {
  const space = pac.Space.fromTexts(read(join(dir, "generator.json")), read(join(dir, "judge.json")), read(join(dir, "records.jsonl")));
  const g = JSON.parse(execFileSync("python3", [join(here, "golden.py"), dir], { maxBuffer: 1 << 28 }).toString());
  const before = failures;
  const manifest = JSON.parse(read(join(dir, "bundle.json")) || "{}");
  const files = Object.fromEntries(["generator.json", "judge.json", "conformance.jsonl", "records.jsonl", "BUNDLE.md"]
    .filter((name) => existsSync(join(dir, name))).map((name) => [name, read(join(dir, name))]));
  const crlf = Object.fromEntries(Object.entries(files).map(([name, data]) => [name, data.replace(/\n/g, "\r\n")]));
  const edited = { ...crlf, "generator.json": crlf["generator.json"] + " " };
  for (const [label, inputs] of Object.entries({ exact: files, crlf, edited })) {
    expect(`manifest ${label}`, await pac.verifyManifest(manifest, inputs), g.verification[label]);
  }
  if (dir === defaults[0]) {
    expect("example CRLF-only names", (await pac.verifyManifest(manifest, crlf)).crlf_only,
      ["generator.json", "judge.json", "conformance.jsonl", "BUNDLE.md"]);
    expect("example edited file not marked CRLF-only", (await pac.verifyManifest(manifest, edited)).crlf_only,
      ["judge.json", "conformance.jsonl", "BUNDLE.md"]);
  }
  for (const c of g.checks) {
    const k = Object.keys(space.dims)[0];
    expect(`check ${c.code}`, pac.checkFlow(c.code, space, g.date, { _action: "n", [k]: " x " }), c.out);
  }
  for (const r of g.reports) expect(`report ${r.code}`, pac.renderReport(pac.checkFlow(r.code, space, g.date, { _action: "n", [Object.keys(space.dims)[0]]: " x " }), space), r.text);
  for (const f of g.forms) {
    const feats = pac.parseCode(f.code, space).features;
    const answers = [];
    for (const want of f.seq) {
      const q = pac.nextQuestion(answers.join(" "), space, g.date);
      expect(`form ${f.code} after [${answers.join(" ")}]`, q, want);
      if (q.done || !same(q, want)) break;
      answers.push(`${q.key}=${feats[q.key] ?? "?"}`);
    }
  }
  expect("categories", pac.categories(space), g.categories);
  for (const f of g.fits) {
    const feats = pac.parseCode(f.code, space).features;
    expect(`fit ${f.code}`, pac.mapFit(feats, space, g.date), f.fit);
    expect(`fit_detail ${f.code}`, pac.fitDetail(feats, space, g.date), f.detail);
  }
  for (const l of g.lookups) expect(`lookup ${l.text}`, pac.lookup(l.text, space), l.out);
  console.log(`${dir.replace(repo + "/", "")}: ${failures === before ? "ok" : `${failures - before} mismatches`}`);
}

// Three-valued exceptions and definition deduplication across a flow also get an
// explicit parity check, independent of which references the shipped example has.
const legacyDir = join(here, "fixtures/legacy");
if (existsSync(join(legacyDir, "judge.json"))) {
  const dir = mkdtempSync(join(tmpdir(), "pac-citations-"));
  const generator = read(join(legacyDir, "generator.json"));
  const judge = JSON.stringify(citationJudge(JSON.parse(read(join(legacyDir, "judge.json")))));
  const cases = [
    "act=biz pur=cyber auth=unauth", "act=biz pur=cyber auth=own", "act=biz pur=cyber",
    "act=biz pur=cyber auth=own > act=biz pur=cyber auth=unauth", "unknownkey=1",
  ];
  try {
    writeFileSync(join(dir, "generator.json"), generator);
    writeFileSync(join(dir, "judge.json"), judge);
    writeFileSync(join(dir, "conformance.jsonl"), cases.map((code) => JSON.stringify({ code })).join("\n"));
    const getGolden = () => JSON.parse(execFileSync("python3", [join(here, "golden.py"), dir, "3"]).toString());
    const golden = getGolden();
    const space = pac.Space.fromTexts(generator, judge);
    const notes = { _action: "n", [Object.keys(space.dims)[0]]: " x " };
    const checks = cases.map((code, i) => {
      const checked = pac.checkFlow(code, space, golden.date, notes);
      expect(`cited check ${code}`, checked, golden.checks[i].out);
      expect(`cited report ${code}`, pac.renderReport(checked, space), golden.reports[i].text);
      return checked;
    });
    expect("exact text of violated rule", checks[0].terms[0].terms[0].text, policyText);
    expect("violated exception does not apply", checks[0].terms[0].terms[1].applies, false);
    expect("excepted exception applies", checks[1].terms.find((e) => e.rule === "P-cyber").terms[1].applies, true);
    expect("unknown exception omits applies", Object.hasOwn(checks[2].terms.find((e) => e.rule === "P-cyber").terms[1], "applies"), false);
    expect("flow citations use status order", checks[3].terms.map((e) => e.status), ["violated", "excepted"]);
    expect("invalid code has no citations", checks[4].terms, []);

    const withSummaries = JSON.stringify(summaryJudge(JSON.parse(judge)));
    writeFileSync(join(dir, "judge.json"), withSummaries);
    const summaryGolden = getGolden();
    const summarySpace = pac.Space.fromTexts(generator, withSummaries);
    for (const [i, code] of cases.entries()) {
      const checked = pac.checkFlow(code, summarySpace, summaryGolden.date, notes);
      expect(`summary check ${code}`, checked, summaryGolden.checks[i].out);
      expect(`summary report ${code}`, pac.renderReport(checked, summarySpace), summaryGolden.reports[i].text);
    }
    const result = pac.check(cases[0], summarySpace, summaryGolden.date, notes);
    const cited = result.terms[0].terms;
    expect("distinct summary fields without quote text", cited.map(({ summary, ...term }) => [summary, Object.hasOwn(term, "text")]),
      [[policySummary, false], [exceptionSummary, false], [definitionSummary, false]]);
    const rendered = pac.renderReport(result, summarySpace);
    for (const [label, summary] of [["", policySummary], ["Exception (does not apply): ", exceptionSummary],
      ["Definition: ", definitionSummary]]) {
      const display = summary.replaceAll("\n", " ");
      expect(`labelled and unquoted summary ${label}`, rendered.includes(`> ${label}Summary (not a quote): ${display} (`), true);
      expect(`summary not put in quote marks ${label}`, rendered.includes(`"${display}"`), false);
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}
// An explicit 2.0 fixture exercises comparisons, fresh unknowns, presets, and history-free reports.
const termDir = mkdtempSync(join(tmpdir(), "pac-terms-parity-"));
try {
  const generator = structuredClone(termGenerator), judge = structuredClone(termJudge);
  generator.order = "split";
  generator.dimensions.push({ key: "ret", type: "number", unit: "days", min: -10, max: 9007199254740994, fixable: true });
  generator.term_map.nodes.c01.children.push("c05");
  generator.term_map.nodes.c05 = { title: "Retention limit", parents: ["c01"], children: [], binds: "deployer",
    keys: [{ id: "k1", role: "gate", dim: "ret", gt: 1 }] };
  judge.terms.c05 = { section: "Example terms", text: "No longer than 1 day." };
  judge.rules.push({ id: "T-c05", term: "c05", kind: "prohibition", source_terms: ["c05"],
    title: "Retention limit", next_step: "Shorten retention.",
    when: { all: [{ dim: "act", in: ["y"] }, { dim: "ret", gt: 1 }] } });
  const termCodes = ["act=y age=17", "act=y age=18", "act=y age=?", "act=y age=3.2", "act=y age=151", "act=y age=young",
    "act=y age=017.0 ret=1.0000000000000001", "act=y ret=-1.50", "act=y ret=9007199254740993",
    "act=n age=17", "act=n ret=2", "ret=2", "act=n disc=n", "act=n disc=?", "act=n", "act=?"];
  writeFileSync(join(termDir, "generator.json"), JSON.stringify(generator));
  writeFileSync(join(termDir, "judge.json"), JSON.stringify(judge));
  writeFileSync(join(termDir, "conformance.jsonl"), termCodes.map((code) => JSON.stringify({ code })).join("\n"));
  const golden = JSON.parse(execFileSync("python3", [join(here, "golden.py"), termDir, "8"], { maxBuffer: 1 << 24 }).toString());
  const sp = new pac.Space(generator, judge), notes = { _action: "n", act: " x " };
  for (const c of golden.checks) expect(`terms check ${c.code}`, pac.checkFlow(c.code, sp, golden.date, notes), c.out);
  for (const r of golden.reports) expect(`terms report ${r.code}`, pac.renderReport(pac.checkFlow(r.code, sp, golden.date, notes), sp), r.text);
  for (const f of golden.forms) {
    const feats = pac.parseCode(f.code, sp).features, answers = [];
    for (const want of f.seq) {
      const q = pac.nextQuestion(answers.join(" "), sp, golden.date);
      expect(`terms form ${f.code} after ${answers.join(" ")}`, q, want);
      if (q.done || !same(q, want)) break;
      answers.push(`${q.key}=${feats[q.key] ?? "?"}`);
    }
  }
  expect("ruled-out numeric fact", pac.check("act=n ret=2", sp).dropped,
    [{ key: "ret", value: "2", because: ["c05"] }]);
  expect("unknown-scope numeric fact", pac.check("ret=2", sp).code, "ret=2");
  const exact = pac.check("act=y age=18 ret=1.0000000000000001", sp);
  expect("exact decimal past strict bound", exact.violated, ["T-c05"]);
  expect("numeric fix uses nearest bound", exact.fix[0], ["ret=1.0000000000000001 -> ret=1"]);
  expect("explicit preset unknown uses an objective fill", pac.check("act=n disc=?", sp).required_next, ["T-c03"]);
} finally {
  rmSync(termDir, { recursive: true, force: true });
}
console.log(`${total - failures}/${total} outputs identical`);
process.exit(failures ? 1 : 0);
