// Policy Action Reader: the page. All judging is done by pac.js; this file only draws it.
import * as pac from "./pac.js";
import { EXAMPLE } from "./example-bundle.js";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const inline = (s) => esc(s).replace(/`([^`]+)`/g, "<code>$1</code>");

const state = { termOrder: "map", space: null, name: "", result: null, cases: [], picking: true, catPath: [], arrange: false, order: { cats: {}, folders: [], values: {} } };

// ------------------------------------------------------------------ display order
// People may move likely categories, folders and features to the top. This changes only what is
// shown first, never the judgement. It is kept per bundle in this browser.

const orderKey = () => `pac-reader-order:${state.name}`;
function loadOrder() {
  try { state.order = { cats: {}, folders: [], values: {}, ...JSON.parse(localStorage.getItem(orderKey()) || "{}") }; }
  catch { state.order = { cats: {}, folders: [], values: {} }; }
}
function saveOrder() { try { localStorage.setItem(orderKey(), JSON.stringify(state.order)); } catch { /* order lasts this visit only */ } }
function ordered(items, id, saved) {
  const rank = new Map((saved || []).map((x, i) => [x, i]));
  return items.map((it, i) => [it, i]).sort((a, b) => (rank.get(id(a[0])) ?? 1e6 + a[1]) - (rank.get(id(b[0])) ?? 1e6 + b[1])).map(([it]) => it);
}
function moveIn(list, item, dir) {
  const i = list.indexOf(item), j = i + dir;
  if (i < 0 || j < 0 || j >= list.length) return list;
  const out = [...list];
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}
const mover = (kind, scope, id) => state.arrange
  ? `<span class="mover"><span role="button" tabindex="0" class="mv" data-mv="${kind}" data-scope="${esc(scope)}" data-id="${esc(id)}" data-dir="-1" title="Move up">↑</span><span role="button" tabindex="0" class="mv" data-mv="${kind}" data-scope="${esc(scope)}" data-id="${esc(id)}" data-dir="1" title="Move down">↓</span></span>` : "";

const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
const compactDock = window.matchMedia("(max-width: 600px)");
const scrollBehavior = () => motion.matches ? "instant" : "smooth";
const verdictTexts = () => ({ ...pac.DEFAULT_TEXTS.verdict, ...((state.space.judge.texts || {}).verdict || {}) });
const STATUS_ORDER = ["satisfied", "required_next", "violated", "not_applicable", "open"];

function ripple(e) {
  const button = e.target.closest(".btn,.val,.term-node > .folder");
  if (!button || motion.matches || button.disabled) return;
  const box = button.getBoundingClientRect();
  const x = e.detail && e.clientX >= box.left && e.clientX <= box.right ? e.clientX : box.left + box.width / 2;
  const y = e.detail && e.clientY >= box.top && e.clientY <= box.bottom ? e.clientY : box.top + box.height / 2;
  const clip = document.createElement("span");
  clip.setAttribute("aria-hidden", "true");
  Object.assign(clip.style, { position: "fixed", pointerEvents: "none", overflow: "hidden", zIndex: 10,
    top: box.top + "px", left: box.left + "px", width: box.width + "px", height: box.height + "px",
    borderRadius: getComputedStyle(button).borderRadius, color: getComputedStyle(button).color });
  const wave = document.createElement("span");
  wave.className = "click-ripple";
  const size = Math.hypot(box.width, box.height) * 2;
  Object.assign(wave.style, { position: "absolute", left: (x - box.left - size / 2) + "px",
    top: (y - box.top - size / 2) + "px", width: size + "px", height: size + "px",
    borderRadius: "50%", background: "currentColor" });
  clip.append(wave);
  document.body.append(clip);
  setTimeout(() => clip.remove(), 600);
}

function showExample() {
  const info = $("bundle-info");
  info.innerHTML = '<span class="skeleton" aria-hidden="true"></span><span class="skeleton" aria-hidden="true"></span>';
  info.hidden = false;
  info.setAttribute("aria-busy", "true");
  $("work").hidden = true;
  setDockVisible(false);
  $("result").hidden = true;
  // Give the skeleton a paint before the digest and first map render.
  requestAnimationFrame(() => requestAnimationFrame(() => openBundle(EXAMPLE, "example")));
}

function updateCodeTokens() {
  const holder = $("build-code");
  const previous = [...holder.querySelectorAll(".code-token")].map((node) => node.textContent);
  const tokens = flowCode().trim().split(/\s+/).filter(Boolean);
  holder.replaceChildren();
  if (!tokens.length) {
    holder.textContent = "(nothing set yet)";
    return;
  }
  for (const [i, text] of tokens.entries()) {
    if (i) holder.append(" ");
    const token = document.createElement("span");
    token.className = "code-token";
    token.textContent = text;
    const key = text.split("=")[0];
    if (previous[i] !== text && !previous.includes(text)) {
      token.classList.add(previous.some((old) => old.startsWith(key + "=")) ? "changed" : "new");
    }
    holder.append(token);
  }
}

function updateDockClearance() {
  const bar = $("build-bar");
  const height = bar.hidden ? 0 : bar.getBoundingClientRect().height;
  const bottom = bar.hidden ? 0 : parseFloat(getComputedStyle(bar).bottom) || 0;
  document.documentElement.style.setProperty("--dock-height", `${height}px`);
  document.documentElement.style.setProperty("--dock-clearance", `${height + bottom}px`);
}

function setDockVisible(visible) {
  $("build-bar").hidden = !visible;
  $("case-actions").hidden = !visible || !compactDock.matches;
  updateDockClearance();
}

function updateDockTerms() {
  const open = Number($("dock-left").textContent);
  $("dock-terms").textContent = open === 0
    ? "All terms answered"
    : open + (open === 1 ? " term left" : " terms left") + (compactDock.matches ? "" : " to answer");
}

function syncDockLayout() {
  const button = $("add-case");
  const where = compactDock.matches ? $("case-actions") : $("build-bar").querySelector(".dock-actions");
  const wasFocused = document.activeElement === button;
  if (button.parentNode !== where) {
    if (compactDock.matches) where.append(button);
    else where.prepend(button);
    if (wasFocused) button.focus({ preventScroll: true });
  }
  setDockVisible(!$("build-bar").hidden);
  updateDockTerms();
}

function renderBuildDock(counts = {}, { settled = false } = {}) {
  const bar = $("build-bar");
  const v2 = state.space.v2;
  bar.classList.toggle("legacy", !v2);
  bar.classList.toggle("ready", v2 && ((counts.open || 0) === 0 || settled));
  updateCodeTokens();
  if (!v2) return;
  const total = STATUS_ORDER.reduce((n, key) => n + (counts[key] || 0), 0);
  const open = counts.open || 0;
  const left = $("dock-left");
  if (left.textContent !== String(open)) {
    left.textContent = String(open);
    left.classList.remove("tick");
    if (!motion.matches) { left.getBoundingClientRect(); left.classList.add("tick"); }
  }
  $("dock-progress").style.strokeDasharray = (total ? 100 * (total - open) / total : 100) + " 100";
  updateDockTerms();
  const stack = $("dock-stack");
  if (!stack.children.length) stack.innerHTML = STATUS_ORDER.map((status) => '<span data-status="' + status + '"></span>').join("");
  for (const seg of stack.children) seg.style.setProperty("--size", (total ? (counts[seg.dataset.status] || 0) * 100 / total : 0) + "%");
  const result = pac.checkFlow(flowCode(), state.space, judgeDate(), caseNotes());
  $("dock-verdict").className = "dock-verdict " + result.verdict;
  const verdict = "So far: " + (verdictTexts()[result.verdict] ?? result.verdict);
  $("dock-verdict").textContent = verdict;
  $("dock-verdict").title = verdict;
}

// ------------------------------------------------------------------ loading

async function loadFiles(fileList) {
  const files = {};
  for (const f of fileList) {
    const base = f.name.split("/").pop();
    if (/^(generator|judge|bundle)\.json$|^(records|conformance)\.jsonl$|^BUNDLE\.md$/.test(base)) files[base] = await f.text();
  }
  const folder = fileList[0] && fileList[0].webkitRelativePath ? fileList[0].webkitRelativePath.split("/")[0] : "";
  await openBundle(files, folder);
}

async function openBundle(files, label) {
  $("load-error").hidden = true;
  try {
    if (!files["generator.json"] || !files["judge.json"]) throw new Error("The bundle needs generator.json and judge.json.");
    state.space = pac.Space.fromTexts(files["generator.json"], files["judge.json"], files["records.jsonl"] || "");
  } catch (e) {
    $("load-error").textContent = `Can't open this bundle: ${e.message}`;
    $("load-error").hidden = false;
    return;
  }
  const manifest = files["bundle.json"] ? JSON.parse(files["bundle.json"]) : null;
  const check = manifest ? await pac.verifyManifest(manifest, files) : null;
  const g = state.space.generator;
  const policy = (g.policy && (g.policy.name || g.policy.source)) || (manifest && manifest.name) || label || "policy bundle";
  state.name = policy;
  state.termOrder = g.order === "split" ? "split" : "map";
  $("arrange").hidden = state.space.v2;
  $("reset-order").hidden = true;
  $("work").classList.remove("arranging");
  state.arrange = false;
  $("arrange").setAttribute("aria-pressed", "false");
  $("arrange").textContent = "Arrange order";
  loadOrder();
  let exam = '<span class="badge warn">no self-exam</span>';
  if (check && check.exam) {
    exam = check.exam.passed ? '<span class="badge ok stamp">self-exam passed</span>'
      : `<span class="badge bad">self-exam failed: ${esc((check.exam.failed || []).join(", "))}</span>`;
  }
  const changed = check ? check.mismatched.filter((name) => !check.crlf_only.includes(name)) : [];
  const digests = !manifest ? '<span class="badge warn">no bundle.json</span>'
    : check.digests_ok ? '<span class="badge ok stamp">files match bundle.json</span>' : [
      changed.length && `<span class="badge bad">changed since bundle.json: ${esc(changed.join(", "))}</span>`,
      check.crlf_only.length && `<span class="badge bad">line endings changed (Windows checkout?): ${esc(check.crlf_only.join(", "))}</span>`,
    ].filter(Boolean).join(" ");
  $("bundle-info").innerHTML = `<div><strong>${esc(policy)}</strong> <span class="muted">format ${esc(g.version)}</span></div>
    <div class="muted">${state.space.dimensions.length} questions · ${state.space.rules.length} rules · ${state.space.history.length} past records</div>
    <div>${exam} ${digests}</div>
    ${files["BUNDLE.md"] !== undefined ? '<details class="bundle-guide"><summary>Guide</summary><pre></pre></details>' : ""}
    ${check && check.exam && !check.exam.passed ? '<div class="error">This bundle failed its self-exam. Results may be incomplete.</div>' : ""}`;
  const guide = $("bundle-info").querySelector(".bundle-guide pre");
  if (guide) guide.textContent = files["BUNDLE.md"];
  $("bundle-info").removeAttribute("aria-busy");
  $("bundle-info").hidden = false;
  $("work").hidden = false;
  restart();
}

// ------------------------------------------------------------------ start over

function judgeDate() { return $("judge-date").value || null; }

function restart() {
  state.result = null;
  state.cases = state.space?.v2 ? [newTermCase()] : [];
  state.picking = !state.space?.v2; state.catPath = [];
  $("result").hidden = true;
  renderCases();
}

// ------------------------------------------------------------------ case builder
// Step 1: open the case map (a tree of categories, as deep as the bundle makes it) and pick a node.
// Step 2: open feature folders and choose features; folders nest (dimension `under`); an empty
// folder is skipped. Step 3: say how each case relates to the one before: at the same time (&) or
// after it (>). Only the code is judged.

function newCase(cat, names) {
  const sp = state.space;
  const values = {};
  const preset = pac.parseCode(cat.preset, sp).features;
  for (const [k, v] of Object.entries(preset)) values[k] = v.split("+");
  return { cat, title: names.join(" › "), name: "", values, more: false, open: new Set(cat.features.slice(0, 1)), note: "", rel: "then" };
}

function caseFeats(c) {
  if (state.space.v2) return { ...c.facts };
  const out = {};
  for (const d of state.space.dimensions) {
    const on = c.values[d.key] || [];
    if (on.length) out[d.key] = Object.keys(d.values).filter((v) => on.includes(v)).join("+");
  }
  return out;
}

// A 2.0 answer is kept unless every term using it is ruled out. Retain the
// explanation separately so the builder and the final report both show the removal.
function prune(c) {
  if (state.space.v2) {
    const { core, dropped } = pac.termCore(c.facts, state.space);
    for (const item of dropped) {
      delete c.answeredUnder[item.key];
      c.dropped.set(item.key, item);
    }
    c.facts = core;
    for (const [key, item] of c.dropped) {
      const probe = pac.termCore({ ...core, [key]: item.value }, state.space);
      if (own(probe.core, key)) c.dropped.delete(key);
    }
    return;
  }
  for (let changed = true; changed;) {
    changed = false;
    const feats = caseFeats(c);
    for (const d of state.space.dimensions) {
      if (d.under && (c.values[d.key] || []).length && pac.evalCond(d.under, feats) !== 1) { c.values[d.key] = []; changed = true; }
    }
  }
}

function caseCode(c) {
  const feats = caseFeats(c);
  const body = Object.entries(feats).map(([k, v]) => `${k}=${v}`).join(" ");
  const name = c.name.trim().replace(/\s+/g, "-").replace(/[^A-Za-z0-9_.-]/g, "");
  return name ? `${name}: ${body}` : body;
}

function flowCode() {
  return state.cases.map((c, i) => (i === 0 ? "" : c.rel === "same" ? " & " : " > ") + caseCode(c)).join("");
}

function categoryPicker() {
  const tree = pac.categories(state.space);
  const trail = [];
  let level = tree;
  for (const id of state.catPath) { const n = level.find((x) => x.id === id); if (!n) break; trail.push(n); level = n.children; }
  const scope = trail.length ? trail[trail.length - 1].path : "";
  level = ordered(level, (x) => x.id, state.order.cats[scope]);
  const here = trail[trail.length - 1];
  const n = state.cases.length;
  const crumbs = [`<button class="crumb" data-depth="0" type="button">All categories</button>`]
    .concat(trail.map((t, d) => `<button class="crumb" data-depth="${d + 1}" type="button">${esc(t.name)}</button>`)).join(" › ");
  $("pick-category").innerHTML = `<p class="step-label">Step 1 · ${n ? `Case ${n + 1}: ` : ""}choose a category</p>
    <div class="crumbs">${crumbs}</div>
    ${here ? `<div class="row" style="margin:0 0 10px"><button id="use-here" class="btn primary" type="button">Use “${esc(here.name)}”</button>
      <span class="muted" style="align-self:center">or open a narrower category below</span></div>` : ""}
    <div class="cats">${level.map((c, i) => `<div class="cat-wrap"><button class="cat" data-cat="${i}" type="button"><strong>${esc(c.name)}</strong>${c.description ? `<span>${esc(c.description)}</span>` : ""}${c.children.length ? `<em class="sub">▸ ${c.children.length} narrower</em>` : ""}</button>${mover("cat", scope, c.id)}</div>`).join("")}</div>
    ${n ? '<div class="row"><button id="cancel-pick" class="btn ghost small" type="button">Cancel</button></div>' : ""}`;
  const choose = (node, path) => {
    state.cases.push(newCase(node, path.map((t) => t.name)));
    state.picking = false; state.catPath = [];
    renderCases();
  };
  for (const b of $("pick-category").querySelectorAll(".cat")) {
    b.addEventListener("click", () => {
      const i = Number(b.dataset.cat);
      if (level[i].children.length) { state.catPath.push(level[i].id); categoryPicker(); } else choose(level[i], [...trail, level[i]]);
    });
  }
  for (const b of $("pick-category").querySelectorAll(".crumb")) {
    b.addEventListener("click", () => { state.catPath = state.catPath.slice(0, Number(b.dataset.depth)); categoryPicker(); });
  }
  if ($("use-here")) $("use-here").addEventListener("click", () => choose(here, trail));
  if ($("cancel-pick")) $("cancel-pick").addEventListener("click", () => { state.picking = false; state.catPath = []; renderCases(); });
  for (const m of $("pick-category").querySelectorAll(".mv")) {
    m.addEventListener("click", () => {
      state.order.cats[scope] = moveIn(level.map((x) => x.id), m.dataset.id, Number(m.dataset.dir));
      saveOrder(); categoryPicker();
    });
  }
}

// Step 2 is a directory: the category is the root folder, each feature group (dimension) is a
// folder, and its features (values) are the entries you choose. Folders for facts that only make
// sense after a choice sit inside that folder once the choice is made.
function folderHtml(c, ci, key, feats, kids, sibs) {
  const d = state.space.dims[key];
  const on = c.values[key] || [];
  const open = c.open.has(key);
  const chosen = on.length ? on.map((v) => d.values[v] ?? v).join(", ")
    : (d.default != null ? `not chosen: ${d.values[d.default] ?? d.default} is assumed` : "not chosen");
  const inner = byFolderOrder((kids[key] || []).filter((k) => pac.evalCond(state.space.dims[k].under, feats) === 1));
  const vals = ordered(Object.entries(d.values), ([v]) => v, state.order.values[key]);
  const leaves = open ? `<div class="leaves">${vals.map(([v, m]) => `<span class="leaf"><button class="val${on.includes(v) ? " on" : ""}" role="${d.multi ? "checkbox" : "radio"}" aria-checked="${on.includes(v)}" data-case="${ci}" data-key="${esc(key)}" data-value="${esc(v)}" type="button" title="${esc(`${key}=${v}`)}">${esc(m)}</button>${mover("value", `${key}|${vals.map(([x]) => x).join(",")}`, v)}</span>`).join("")}</div>`
    + (inner.length ? `<ul>${inner.map((k) => folderHtml(c, ci, k, feats, kids, inner)).join("")}</ul>` : "") : "";
  const more = !open && inner.length ? ` · ${inner.length} inside` : "";
  return `<li class="node${open ? " open" : ""}"><button class="folder" data-case="${ci}" data-open="${esc(key)}" type="button" aria-expanded="${open}" title="${esc(d.question || "")}">
      <span class="twisty">${open ? "▾" : "▸"}</span><span class="fname">${esc(d.name || key)}</span><span class="fval${on.length ? " set" : ""}">${esc(chosen + more)}</span></button>${mover("folder", sibs.join(","), key)}${leaves}</li>`;
}

// Format 2.0 uses policy terms as the only map. Code facts are shared across all their keys.
function newTermCase() {
  return { name: "", facts: {}, answeredUnder: {}, dropped: new Map(), open: new Set(), dutyOpen: new Set(), otherOpen: new Set(), note: "", rel: "then" };
}
const TERM_STATUS = {
  violated: "Violated", required_next: "Required next", satisfied: "Satisfied",
  open: "Open", not_applicable: "Not applicable",
};
const own = (obj, key) => Object.hasOwn(obj, key);

function termLeaves(keys) {
  return (keys || []).flatMap((k) => k.any || [k]);
}
const termCaseIds = new WeakMap();
let nextTermCaseId = 0;
function termCaseId(c) {
  if (!termCaseIds.has(c)) termCaseIds.set(c, ++nextTermCaseId);
  return termCaseIds.get(c);
}

function focusAttr(...parts) {
  return `data-focus="${esc(JSON.stringify(parts))}"`;
}

function termValueData(ci, term, key, action, slot, opt = "") {
  return `data-case="${ci}" data-term="${esc(term)}" data-key="${esc(key)}" data-term-action="${action}" ${focusAttr(termCaseId(state.cases[ci]), term, key, action, slot, opt)}`;
}

function termChevron() {
  return '<svg class="twisty term-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 4 4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>';
}

function chipMark(multi) {
  const shape = multi ? '<rect x="1.5" y="1.5" width="13" height="13" rx="3"/>' : '<circle cx="8" cy="8" r="6.5"/>';
  return `<svg class="chip-mark" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5">${shape}<path class="val-check" pathLength="1" d="m4.5 8 2.25 2.25 4.75-4.75" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

function newStatusCounts() {
  return Object.fromEntries(Object.keys(TERM_STATUS).map((status) => [status, 0]));
}

function termCountTotal(counts) {
  return Object.values(counts).reduce((a, b) => a + b, 0);
}

function sectionStats(counts, key) {
  const total = termCountTotal(counts), answered = total - counts.open;
  const bars = Object.entries(counts).map(([status, n]) =>
    `<span data-status="${status}" data-meter-id="${key}-${status}" style="--size:${total ? 100 * n / total : 0}%"></span>`).join("");
  return `<span class="term-stack" aria-hidden="true">${bars}</span><span class="term-count" aria-label="${answered} answered of ${total} visible terms">${answered}/${total}</span>`;
}

function numberMeter(leaf, d, value, id) {
  if (!limitHint(leaf, d)) return "";
  const set = value != null && value !== "?" && Number.isFinite(Number(value));
  const outside = set && pac.evalCond(leaf, { [leaf.dim]: value }) === 0;
  const limits = leaf.between || [leaf.lt ?? leaf.le ?? leaf.gt ?? leaf.ge];
  const ratios = limits.map((limit) => set && limit !== 0
    ? 100 * Math.max(0, Math.min(1, Number(value) / limit)) : 0);
  const fills = ratios.map((ratio, i) => `<i data-meter-id="${esc(id)}-${i}" style="--ratio:${ratio}%"></i>`).join("");
  return `<div class="term-meter" aria-hidden="true" data-outside="${outside}">${fills}</div>`;
}

function limitHint(k, d) {
  const ops = { lt: "<", le: "≤", gt: ">", ge: "≥" };
  if (k.between) return `Limit: ${k.between[0]}–${k.between[1]} ${d.unit || ""} (inclusive)`;
  const op = Object.keys(ops).find((x) => own(k, x));
  return op ? `Limit: ${ops[op]} ${k[op]} ${d.unit || ""}` : "";
}

function termLeafHtml(c, ci, term, leaf, lx, preset) {
  const sp = state.space, key = leaf.dim, d = sp.dims[key];
  if (!d) return "";
  const stated = own(c.facts, key), value = stated ? c.facts[key] : preset?.value;
  const on = value == null || value === "?" ? [] : String(value).split("+");
  const source = c.answeredUnder[key];
  const title = d.question || d.name || key;
  const option = (v) => `<button class="val${on.includes(v) ? " on" : ""}" type="button" ${termValueData(ci, term, key, "value", lx, v)}
    data-value="${esc(v)}" aria-pressed="${on.includes(v)}">${chipMark(sp.multi(key))}${esc(d.values[v])}${!stated && v === d.default ? ' <span class="muted">(default)</span>' : ""}</button>`;
  const group = (label, vs) => !vs.length ? "" : `<div class="term-options"><strong>${label}</strong><div class="leaves">${vs.map(option).join("")}</div></div>`;
  const otherId = `${term}:${lx}`;
  let body;
  if (d.type === "number") {
    const id = `num-${termCaseId(c)}-${term}-${lx}`;
    body = `<form class="term-number" data-number="${esc(key)}" data-term="${esc(term)}" data-case="${ci}">
      <label for="${esc(id)}">Value${d.unit ? ` (${esc(d.unit)})` : ""}</label>
      <input id="${esc(id)}" ${focusAttr(termCaseId(c), term, key, "number", lx)} type="text" inputmode="${d.integer ? "numeric" : "decimal"}" value="${esc(value === "?" ? "" : value)}">
      <button class="btn small" ${focusAttr(termCaseId(c), term, key, "number-submit", lx)} type="submit">Set value</button>
      <small class="muted term-limit">${esc(limitHint(leaf, d))}</small><small class="error number-error" aria-live="polite"></small>
      ${numberMeter(leaf, d, value, id)}
    </form>`;
  } else {
    const vals = Object.keys(d.values || {});
    const meets = vals.filter((v) => pac.evalCond(leaf, { [key]: v }) === 1);
    const doesNot = vals.filter((v) => !meets.includes(v)), long = doesNot.length > 6;
    const toggle = `<button type="button" class="btn ghost small" ${termValueData(ci, term, key, "others", lx)} data-other="${esc(otherId)}"
       aria-expanded="${c.otherOpen.has(otherId)}">Something else</button>`;
    body = group("Meets this term", meets)
      + (long ? toggle + (c.otherOpen.has(otherId) ? group("Doesn't meet this term", doesNot) : "")
        : group("Doesn't meet this term", doesNot));
  }
  const reason = preset ? (preset.why === "stated"
    ? `Pre-selected: stated in term ${preset.term}`
    : `Pre-selected: this is ${preset.binds}'s duty (term ${preset.term})`) : "";
  return `<div class="term-key">
    <div><strong>${esc(title)}</strong> ${source && source !== term ? `<span class="muted">answered under ${esc(sp.generator.term_map.nodes[source]?.title || source)}</span>` : ""}</div>
    ${reason ? `<small class="muted">${!stated ? '<span class="preset-pill" aria-hidden="true">◆ Pre-selected</span> ' : ""}${esc(reason)}${stated ? " (overridden)" : ""}</small>` : ""}
    ${body}
    <button class="btn ghost small" type="button" ${termValueData(ci, term, key, "skip", lx)} aria-pressed="${stated && value === "?"}">Don't know (skip)</button>
    ${preset && stated ? `<button type="button" class="btn ghost small" ${termValueData(ci, term, key, "reset", lx)}>Reset to pre-selected</button>` : ""}
    ${!preset && stated ? `<button type="button" class="btn ghost small" ${termValueData(ci, term, key, "reset", lx)}>Clear answer</button>` : ""}
  </div>`;
}

function termTreeHtml(c, ci, counts, flags) {
  const sp = state.space, tm = sp.generator.term_map || {}, nodes = tm.nodes || {};
  const { visible, chosen } = pac.termVisibility(c.facts, sp);
  const decisions = pac.evaluate(c.facts, sp, judgeDate());
  const presets = pac.presetEntries(sp), seen = new Set();
  const active = new Map(pac.activeRules(sp, judgeDate()).map((r) => [r.term, r]));
  const rules = new Map(sp.rules.map((r) => [r.term, r])), full = pac.effectiveFeatures(c.facts, sp);
  const parties = sp.generator.duty?.parties || [];
  const binds = (id) => nodes[id]?.binds || sp.judge.terms?.[id]?.binds;
  const outOfDuty = (id) => parties.length > 0 && binds(id) && !parties.includes(binds(id));
  let sectionCounts;
  function drawTerm(id, trail) {
    if (seen.has(id) || trail.has(id) || !visible.has(id) || !own(nodes, id)) return "";
    seen.add(id);
    const n = nodes[id], selected = chosen.has(id), open = c.open.has(id), rule = active.get(id);
    const gate = { all: (n.keys || []).filter((k) => k.role === "gate") };
    const status = rule ? decisions.statuses[rule.id] : rules.has(id) ? "not_applicable"
      : selected ? "satisfied" : pac.evalCond(gate, full) === 0.5 ? "open" : "not_applicable";
    if (own(counts, status)) { counts[status] += 1; sectionCounts[status] += 1; }
    const badge = status === "violated" ? "bad" : status === "satisfied" ? "ok" : "warn";
    const children = (n.children || []).filter((x) => visible.has(x));
    const locked = (n.children || []).filter((x) => !visible.has(x)).length;
    const lockedHtml = locked && pac.evalCond(gate, full) === 0.5
      ? `<div class="term-locked"><span>${locked} more term${locked === 1 ? "" : "s"} unlock here</span><span aria-hidden="true"><i></i><i></i><i></i></span></div>` : "";
    const pending = new Set();
    if (!selected && pac.evalCond(gate, full) === 0.5) {
      const hidden = new Set();
      function collect(child) {
        if (visible.has(child) || hidden.has(child)) return;
        hidden.add(child);
        const descendant = nodes[child];
        for (const { dim } of termLeaves(descendant.keys)) if (own(c.facts, dim)) pending.add(dim);
        const childGate = { all: (descendant.keys || []).filter((k) => k.role === "gate") };
        if (pac.evalCond(childGate, full) !== 0) {
          for (const next of descendant.children || []) collect(next);
        }
      }
      for (const child of n.children || []) collect(child);
    }
    const pendingHtml = [...pending].map((dim) => `<p class="muted term-pending"><code>${esc(dim)}=${esc(c.facts[dim])}</code> answered, applies once ${esc(n.title || id)} holds</p>`).join("");
    const citations = selected && open ? pac.citationsForTerm(id, rule, c.facts, sp) : [];
    const matched = selected ? `<div class="term-matched"><strong>${esc(n.title || rule?.title || id)}</strong>
      ${rule?.next_step || n.next_step ? `<p>${esc(rule?.next_step || n.next_step)}</p>` : ""}
      ${citations.map(citationHtml).join("")}</div>` : "";
    const nextTrail = new Set([...trail, id]);
    const body = open ? (n.keys || []).map((k, i) => {
      const leaves = termLeaves([k]).map((leaf, j) => termLeafHtml(c, ci, id, leaf, `${i}-${j}`, presets[leaf.dim])).join("");
      return k.any ? `<div class="term-alternatives"><small>${esc(k.role || "gate")} · any of these</small>${leaves}</div>` : leaves;
    }).join("") : "";
    return `<article class="term-node" data-node="${esc(id)}" data-status="${esc(status)}">
      <button class="folder" data-case="${ci}" data-term="${esc(id)}" data-term-action="term" ${focusAttr(termCaseId(c), id, "term")} aria-expanded="${open}" type="button">${termChevron()}
        <span class="fname">${esc(n.title || id)}</span><span class="badge term-badge ${badge}"><i class="status-dot" aria-hidden="true"></i>${TERM_STATUS[status] || "Open"}</span></button>
      ${open ? `<div class="term-body">${matched}${body}</div>` : ""}${pendingHtml}${lockedHtml}${children.length ? `<div class="term-children">${drawGroup(children, id, nextTrail)}</div>` : ""}</article>`;
  }
  function drawGroup(ids, scope, trail = new Set()) {
    const rest = ids.filter((id) => outOfDuty(id) && visible.has(id) && !seen.has(id));
    const main = ids.filter((id) => !rest.includes(id)).map((id) => drawTerm(id, trail)).join("");
    const duty = c.dutyOpen.has(scope);
    return main + (rest.length ? `<div class="term-duty"><button type="button" class="folder" data-case="${ci}" data-term-action="duty"
      data-scope="${esc(scope)}" ${focusAttr(termCaseId(c), scope, "duty")} aria-expanded="${duty}">${termChevron()} Other parties' duties</button>
      ${duty ? rest.map((id) => drawTerm(id, trail)).join("") : ""}</div>` : "");
  }
  const guided = state.termOrder === "split" ? guidedHtml(c, ci, flags) : "";
  const notices = [...c.dropped.values()].map((item) => `<p class="muted term-dropped">${inline(pac.droppedLine(item, sp))}</p>`).join("");
  return notices + guided + (tm.sections || []).map((sec, i) => {
    sectionCounts = newStatusCounts();
    const group = drawGroup(sec.terms || [], `section-${i}`);
    return `<section class="term-section"><h4 class="term-section-head"><span class="term-section-name">${esc(sec.name)}</span>
      <span class="term-section-stats">${sectionStats(sectionCounts, `section-${termCaseId(c)}-${i}`)}</span></h4>${group}</section>`;
  }).join("");
}

function guidedHtml(c, ci, flags) {
  const sp = state.space;
  const guide = pac.guidedTerm(c.facts, sp, judgeDate());
  const forced = guide.forced?.length ? `<p class="muted">Auto-skipped: ${esc(guide.forced.map((x) => `${x.key}=${x.value} (fixed by the bundle)`).join("; "))}</p>` : "";
  flags.settled &&= Boolean(guide.settled);
  const settled = guide.settled ? `<p class="muted">The verdict won't change. You can stop here.</p>` : "";
  return `<div class="guided-terms">${forced}${settled}${guide.leaf ? '<strong>Suggested next question</strong>'
    + termLeafHtml(c, ci, guide.term, guide.leaf, "guided", pac.presetEntries(sp)[guide.leaf.dim]) : ""}</div>`;
}

function setTermFact(c, term, key, value) {
  c.facts[key] = value; c.answeredUnder[key] = term; c.dropped.delete(key);
  prune(c);
}

function onTermAction(t, c) {
  const { termAction: act, term, key, value, scope, other } = t.dataset;
  if (act === "term" || act === "duty" || act === "others") {
    const [set, val] = act === "term" ? [c.open, term] : act === "duty" ? [c.dutyOpen, scope] : [c.otherOpen, other];
    if (set.has(val)) set.delete(val); else set.add(val);
  } else if (act === "reset") {
    delete c.facts[key]; delete c.answeredUnder[key]; prune(c);
  } else if (act === "skip") setTermFact(c, term, key, "?");
  else if (act === "value") {
    const sp = state.space;
    if (sp.multi(key)) {
      const current = c.facts[key] ?? pac.presetEntries(sp)[key]?.value ?? "?";
      const vals = current === "?" ? [] : String(current).split("+");
      const selected = vals.includes(value) ? vals.filter((v) => v !== value) : [...vals, value];
      setTermFact(c, term, key, Object.keys(sp.dims[key].values).filter((v) => selected.includes(v)).join("+") || "?");
    } else setTermFact(c, term, key, value);
  }
  renderCases();
}

const byFolderOrder = (keys) => ordered(keys, (k) => k, state.order.folders);

function treeHtml(c, ci, counts, flags) {
  if (state.space.v2) return termTreeHtml(c, ci, counts, flags);
  const sp = state.space;
  const feats = caseFeats(c);
  const kids = pac.nestedUnder(sp);
  const rootOf = (k) => { const seen = new Set(); while (sp.dims[k].under && !seen.has(k)) { seen.add(k); k = sp.dims[k].under.dim; } return k; };
  const nestedIn = (k, set) => { let x = k; const seen = new Set(); while (sp.dims[x].under && !seen.has(x)) { seen.add(x); x = sp.dims[x].under.dim; if (set.includes(x)) return true; } return false; };
  const shown = byFolderOrder(c.cat.features.filter((k) => !nestedIn(k, c.cat.features)));
  const offered = pac.dimensionOrder(sp).filter((k) => c.cat.features.includes(k) || nestedIn(k, c.cat.features));
  const others = pac.dimensionOrder(sp).filter((k) => !offered.includes(k));
  const otherTop = byFolderOrder(others.filter((k) => !nestedIn(k, others) && !offered.includes(rootOf(k))));
  const otherSet = others.filter((k) => (c.values[k] || []).length).length;
  return `<ul class="tree"><li class="node open root"><div class="folder rootname"><span class="twisty">▾</span><span class="fname">${esc(c.title)}</span></div>
    <ul>${shown.map((k) => folderHtml(c, ci, k, feats, kids, shown)).join("")}
    ${otherTop.length ? `<li class="node${c.more ? " open" : ""}"><button class="folder" data-case="${ci}" data-more="${ci}" type="button" aria-expanded="${!!c.more}">
        <span class="twisty">${c.more ? "▾" : "▸"}</span><span class="fname">Other features</span><span class="fval${otherSet ? " set" : ""}">${otherTop.length} groups${otherSet ? `, ${otherSet} chosen` : ""}</span></button>
        ${c.more ? `<ul>${otherTop.map((k) => folderHtml(c, ci, k, feats, kids, otherTop)).join("")}</ul>` : ""}</li>` : ""}
    </ul></li></ul>`;
}

const termReducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function termSnapshot(root) {
  const nodes = new Map(), values = new Map(), meters = new Map();
  for (const el of root.querySelectorAll("[data-node]")) {
    const id = `${el.closest("[data-term-case]").dataset.termCase}:${el.dataset.node}`;
    nodes.set(id, {
      status: el.dataset.status,
      open: !!el.querySelector(":scope > .term-body"),
      children: !!el.querySelector(":scope > .term-children"),
    });
  }
  for (const el of root.querySelectorAll(".val[data-focus]")) values.set(el.dataset.focus, el.classList.contains("on"));
  for (const el of root.querySelectorAll("[data-meter-id]")) {
    const prop = el.matches(".term-meter > i") ? "--ratio" : "--size";
    meters.set(el.dataset.meterId, el.style.getPropertyValue(prop));
  }
  return { nodes, values, meters };
}

function animateTermDiff(root, before) {
  if (termReducedMotion()) return;
  let entered = 0;
  for (const el of root.querySelectorAll("[data-node]")) {
    const id = `${el.closest("[data-term-case]").dataset.termCase}:${el.dataset.node}`;
    const old = before.nodes.get(id);
    if (!old) {
      el.classList.add("enter");
      el.style.setProperty("--i", Math.min(entered++, 12));
      continue;
    }
    if (old.status !== el.dataset.status) {
      el.classList.add("changed");
      if (el.dataset.status === "violated") el.classList.add("became-violated");
      if (el.dataset.status === "satisfied") el.classList.add("became-satisfied");
    }
    if (!old.open) el.querySelector(":scope > .term-body")?.classList.add("unfold");
    if (!old.children) el.querySelector(":scope > .term-children")?.classList.add("grow");
  }
  if (!before.nodes.size) return; // First render animates only the entering cards.
  for (const el of root.querySelectorAll(".val.on[data-focus]")) {
    if (before.values.get(el.dataset.focus) === false) el.classList.add("picked");
  }
  for (const el of root.querySelectorAll("[data-meter-id]")) {
    const previous = before.meters.get(el.dataset.meterId);
    if (previous == null) continue;
    const prop = el.matches(".term-meter > i") ? "--ratio" : "--size";
    const next = el.style.getPropertyValue(prop);
    if (previous === next) continue;
    el.style.setProperty(prop, previous);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (el.isConnected) el.style.setProperty(prop, next);
    }));
  }
}

function renderCases() {
  if (!state.space) return;
  const sp = state.space, root = $("cases"), counts = newStatusCounts();
  const flags = { settled: sp.v2 && state.termOrder === "split" && state.cases.length > 0 };
  const active = document.activeElement;
  const focus = sp.v2 && root.contains(active) ? active.dataset.focus : null;
  const before = sp.v2 ? termSnapshot(root) : null;
  const oldX = scrollX, oldY = scrollY;
  root.innerHTML = (sp.v2 ? `<div class="row">
    <label class="field">Question order <select id="term-order" ${focusAttr("term-order")}><option value="map"${state.termOrder === "map" ? " selected" : ""}>Term map</option><option value="split"${state.termOrder === "split" ? " selected" : ""}>Split</option></select></label>
    </div>` : "") + state.cases.map((c, ci) => {
    const rel = ci === 0 ? "" : `<div class="relation"><span class="step-label" style="margin:0">Step 3 · relationship</span> Case ${ci + 1} happens
      <span class="seg"><button data-rel="then" data-case="${ci}" ${focusAttr(termCaseId(c), "then")} class="${c.rel === "then" ? "on" : ""}" type="button">after case ${ci}</button><button data-rel="same" data-case="${ci}" ${focusAttr(termCaseId(c), "same")} class="${c.rel === "same" ? "on" : ""}" type="button">at the same time as case ${ci}</button></span></div>`;
    return `${rel}<div class="case" data-term-case="${termCaseId(c)}">
      <div class="case-head"><h3>Case ${ci + 1}: ${esc(c.cat?.name || "Policy terms")}</h3>
        <input data-name="${ci}" ${focusAttr(termCaseId(c), "name")} type="text" placeholder="name (optional)" value="${esc(c.name)}" aria-label="Case name">
        <span class="tools">
          ${ci > 0 ? `<button class="btn small ghost" data-move="${ci}" data-dir="-1" ${focusAttr(termCaseId(c), "up")} type="button" title="Move up">↑</button>` : ""}
          ${ci < state.cases.length - 1 ? `<button class="btn small ghost" data-move="${ci}" data-dir="1" ${focusAttr(termCaseId(c), "down")} type="button" title="Move down">↓</button>` : ""}
          <button class="btn small ghost" data-remove="${ci}" ${focusAttr(termCaseId(c), "remove")} type="button">Remove</button>
        </span></div>
      <p class="step-label">${sp.v2 ? "Open a term and choose its constraints, or skip facts you can't confirm." : "Step 2 · open a folder and choose the features this case has (skip any you can't confirm)"}</p>
      ${treeHtml(c, ci, counts, flags)}
      <label class="field">Note for this case (shown in the report, never judged)<input data-note="${ci}" ${focusAttr(termCaseId(c), "note")} type="text" value="${esc(c.note)}"></label>
    </div>`;
  }).join("");
  $("pick-category").hidden = !state.picking;
  if (state.picking) categoryPicker();
  renderBuildDock(counts, flags);
  $("build-error").hidden = true;
  setDockVisible(Boolean(state.cases.length) && !state.picking);
  if (before) {
    animateTermDiff(root, before);
    if (focus) [...root.querySelectorAll("[data-focus]")].find((el) => el.dataset.focus === focus)?.focus({ preventScroll: true });
    if (scrollX !== oldX || scrollY !== oldY) scrollTo({ left: oldX, top: oldY, behavior: "instant" });
  }
}

function onMove(m) {
  const dir = Number(m.dataset.dir), id = m.dataset.id;
  if (m.dataset.mv === "value") {
    const [key, list] = m.dataset.scope.split("|");
    state.order.values[key] = moveIn(list.split(","), id, dir);
  } else if (m.dataset.mv === "folder") {
    const sibs = m.dataset.scope.split(",");
    const moved = moveIn(sibs, id, dir);
    const all = byFolderOrder(pac.dimensionOrder(state.space));
    const slots = all.map((k, i) => (sibs.includes(k) ? i : -1)).filter((i) => i >= 0);
    slots.forEach((slot, n) => { all[slot] = moved[n]; });
    state.order.folders = all;
  }
  saveOrder();
  renderCases();
}

function onCasesClick(e) {
  const mv = e.target.closest(".mv");
  if (mv) return onMove(mv);
  const t = e.target.closest("button");
  if (!t) return;
  const ci = Number(t.dataset.case ?? t.dataset.move ?? t.dataset.remove ?? t.dataset.more);
  if (t.dataset.termAction) { onTermAction(t, state.cases[ci]); return; }
  if (t.dataset.value !== undefined) {
    const c = state.cases[ci], key = t.dataset.key, v = t.dataset.value;
    const on = c.values[key] || [];
    if (state.space.multi(key)) c.values[key] = on.includes(v) ? on.filter((x) => x !== v) : [...on, v];
    else c.values[key] = on.includes(v) ? [] : [v];
    prune(c);
    if (c.values[key].length) for (const k of pac.nestedUnder(state.space)[key] || []) c.open.add(k);
  } else if (t.dataset.open !== undefined) {
    const o = state.cases[ci].open;
    if (o.has(t.dataset.open)) o.delete(t.dataset.open); else o.add(t.dataset.open);
  } else if (t.dataset.more !== undefined) {
    state.cases[ci].more = !state.cases[ci].more;
  } else if (t.dataset.rel) {
    state.cases[ci].rel = t.dataset.rel;
  } else if (t.dataset.move !== undefined) {
    const j = ci + Number(t.dataset.dir);
    [state.cases[ci], state.cases[j]] = [state.cases[j], state.cases[ci]];
  } else if (t.dataset.remove !== undefined) {
    state.cases.splice(ci, 1);
    if (!state.cases.length) {
      if (state.space.v2) state.cases.push(newTermCase()); else state.picking = true;
    }
  } else return;
  renderCases();
}

function caseNotes() {
  const notes = state.cases.map((c, i) => (c.note.trim() ? `Case ${i + 1}: ${c.note.trim()}` : "")).filter(Boolean).join("; ");
  return notes ? { _action: notes } : null;
}

function judgeCases() {
  const empty = state.space.v2 ? -1 : state.cases.findIndex((c) => !Object.values(c.values).some((v) => v.length));
  if (empty >= 0) {
    $("build-error").textContent = `Case ${empty + 1} has no facts yet. Pick at least one, or remove the case.`;
    $("build-error").hidden = false;
    return;
  }
  const result = pac.checkFlow(flowCode(), state.space, judgeDate(), caseNotes());
  if (state.space.v2) (result.flow || [result]).forEach((step, i) => {
    const dropped = state.cases[i].dropped;
    if (dropped.size) step.dropped = [...dropped.values()];
  });
  showResult(result);
}

// ------------------------------------------------------------------ result

function actionHtml(a, i) {
  return `<li style="--i:${i}"><span class="kind" data-kind="${esc(a.kind)}">${esc(a.kind)}</span> ${esc(a.action)}${a.code_change ? ` <code>${esc(a.code_change)}</code>` : ""}${a.terms?.length ? ` (${esc(a.terms.join(", "))})` : ""}</li>`;
}

function citationHtml(q) {
  const label = pac.termRoleLabel(q);
  const attribution = [q.section, q.id].filter(Boolean).join(", ");
  const { text, summary } = pac.termContent(q);
  if (summary !== undefined) {
    const summaryLabel = label ? `${label}: Summary (not a quote)` : "Summary (not a quote)";
    return `<div class="term-summary"><strong>${esc(summaryLabel)}: </strong><span>${esc(summary)}</span><cite>${esc(attribution)}</cite></div>`;
  }
  return `<blockquote>${label ? `<strong>${esc(label)}: </strong>` : ""}<span>${esc(text)}</span><cite>${esc(attribution)}</cite></blockquote>`;
}

const VERDICT_ICON = {
  compliant: "M32 44l8 8 15-16", violates: "M33 33l20 20m0-20L33 53",
  invalid_code: "M33 33l20 20m0-20L33 53", needs_info: "M36 36a7 7 0 1 1 10 6q-3 2-3 5m0 7h.1",
  compliant_if_requirements_met: "M43 32v15m0 7h.1",
};

function verdictHero(r, label, reading = "") {
  const burst = !motion.matches && r.verdict === "compliant"
    ? '<span aria-hidden="true" class="verdict-burst">' + Array.from({ length: 18 }, (_, i) => `<i style="--angle:${i * 20}deg;--piece:${i % 4}"></i>`).join("") + '</span>' : "";
  return `<div class="verdict-hero ${esc(r.verdict)}">
    <div class="verdict-emblem">${burst}<svg class="verdict-ring" viewBox="0 0 86 86" width="86" height="86" aria-hidden="true">
      <circle cx="43" cy="43" r="36" fill="none" pathLength="100"></circle>
      <path class="verdict-icon" d="${VERDICT_ICON[r.verdict] || VERDICT_ICON.needs_info}" pathLength="100"></path>
    </svg></div>
    <div class="verdict ${esc(r.verdict)}" role="status">${esc(label)}${reading ? `<p class="muted verdict-reading">${esc(reading)}</p>` : ""}</div>
  </div>`;
}

function resultStats(result) {
  const steps = result.flow || [result];
  const labels = { violated: "Violated terms", required_next: "Required next", open: "Open terms" };
  if (steps.every((r) => Array.isArray(r.satisfied))) labels.satisfied = "Satisfied";
  return '<div class="verdict-stats">' + Object.entries(labels).map(([key, label]) => {
    const total = steps.reduce((sum, r) => sum + (r[key]?.length || 0), 0);
    return `<div class="verdict-stat" data-status="${key}"><strong aria-label="${total}" data-target="${total}">${motion.matches ? total : 0}</strong><span>${label}</span></div>`;
  }).join("") + '</div>';
}

function countStats() {
  const tiles = [...$("report").querySelectorAll("[data-target]")];
  if (motion.matches) return;
  const start = performance.now();
  function frame(now) {
    if (!tiles.some((t) => t.isConnected) || $("result").hidden) return;
    const time = motion.matches ? 1 : Math.max(0, Math.min(1, (now - start - 470) / 600));
    for (const tile of tiles) tile.textContent = Math.round(Number(tile.dataset.target) * (1 - (1 - time) ** 3));
    if (time < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function oneResultHtml(r, seenDefinitions = new Set(), step = false) {
  const sp = state.space;
  const vt = verdictTexts();
  const h = { ...pac.DEFAULT_TEXTS.headings, ...((sp.judge.texts || {}).headings || {}) };
  const label = vt[r.verdict] ?? r.verdict;
  return `${step ? `<div class="verdict ${esc(r.verdict)}">${esc(label)}</div>` : verdictHero(r, label, r.reading) + resultStats(r)}
    <h3>${esc(h.next)}</h3><ol class="verdict-actions">${r.next_actions.map(actionHtml).join("")}</ol>
    <h3>${esc(h.code)}</h3><div class="action-code">${esc(r.code || "(nothing set)")}</div>
    ${step ? `<p class="muted">${esc(r.reading)}</p>` : ""}
    ${(r.dropped || []).map((item) => `<p class="muted">${inline(pac.droppedLine(item, sp))}</p>`).join("")}
    ${pac.reportSections(r, sp, seenDefinitions).map((s) => `<h3>${esc(s.heading)}</h3><ul>${s.items.map((x, i) => `<li>${inline(x)}${(s.citations?.[i] || []).map(citationHtml).join("")}</li>`).join("")}</ul>`).join("")}`;
}

function showResult(result) {
  state.result = result;
  const sp = state.space;
  const disclaimer = (sp.judge.texts || {}).disclaimer ?? pac.DEFAULT_TEXTS.disclaimer;
  let html;
  if (result.flow) {
    const vt = verdictTexts();
    const stages = result.stages || result.flow.map((_, i) => [i]);
    const together = stages.some((st) => st.length > 1);
    const seenDefinitions = new Set();
    html = verdictHero(result, `Flow of ${result.flow.length} actions: ${vt[result.verdict] ?? result.verdict}`) + resultStats(result)
      + stages.map((stage, n) => (together ? `<p class="stage-head">Step ${n + 1}${stage.length > 1 ? `: ${stage.length} actions at the same time` : ""}</p>` : "")
        + stage.map((i) => { const s = result.flow[i]; return `<div class="flow-step" style="--i:${i}"><h3>Action ${i + 1}${s.step ? `: ${esc(s.step)}` : ""}</h3>${oneResultHtml(s, seenDefinitions, true)}</div>`; }).join("")).join("");
  } else {
    html = oneResultHtml(result);
  }
  $("report").innerHTML = `<div class="report">${html}<p class="muted"><em>${esc(disclaimer)}</em></p></div>`;
  $("result").hidden = false;
  setDockVisible(false);
  countStats();
  $("result").scrollIntoView({ behavior: scrollBehavior(), block: "start" });
}

function download(name, text, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// ------------------------------------------------------------------ wiring

$("pick-folder").addEventListener("change", (e) => loadFiles([...e.target.files]));
$("pick-files").addEventListener("change", (e) => loadFiles([...e.target.files]));
$("load-example").addEventListener("click", showExample);
const drop = $("drop");
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); loadFiles([...e.dataTransfer.files]); });
$("judge-date").value = pac.today();
syncDockLayout();
compactDock.addEventListener("change", syncDockLayout);
new ResizeObserver(updateDockClearance).observe($("build-bar"));
document.addEventListener("click", ripple, true);
$("cases").addEventListener("click", onCasesClick);
$("arrange").addEventListener("click", () => {
  state.arrange = !state.arrange;
  $("arrange").setAttribute("aria-pressed", String(state.arrange));
  $("arrange").textContent = state.arrange ? "Done arranging" : "Arrange order";
  $("reset-order").hidden = !state.arrange;
  $("work").classList.toggle("arranging", state.arrange);
  renderCases();
});
document.addEventListener("keydown", (e) => { if (e.target.classList && e.target.classList.contains("mv") && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); e.target.click(); } });
$("reset-order").addEventListener("click", () => { state.order = { cats: {}, folders: [], values: {} }; saveOrder(); renderCases(); });
$("cases").addEventListener("input", (e) => {
  const t = e.target;
  if (t.dataset.name !== undefined) { state.cases[Number(t.dataset.name)].name = t.value; updateCodeTokens(); }
  if (t.dataset.note !== undefined) state.cases[Number(t.dataset.note)].note = t.value;
  if (t.closest("form[data-number]") && t.hasAttribute("aria-invalid")) {
    t.removeAttribute("aria-invalid");
    t.classList.remove("invalid-entry");
    t.closest("form").querySelector(".number-error").textContent = "";
  }
});
$("cases").addEventListener("change", (e) => {
  if (e.target.id === "term-order") { state.termOrder = e.target.value; renderCases(); }
});
function normalizeNumberInput(raw, unit) {
  let value = raw.normalize("NFKC").replace(/[。．]/g, ".").trim();
  const suffix = String(unit ?? "").normalize("NFKC").trim();
  if (suffix && value.toLowerCase().endsWith(suffix.toLowerCase())) {
    value = value.slice(0, -suffix.length).trimEnd();
  }
  // Only valid thousands grouping is removed; malformed commas still fail parseCode.
  if (/^-?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?$/.test(value)) value = value.replaceAll(",", "");
  return value;
}

$("cases").addEventListener("submit", (e) => {
  const f = e.target;
  if (f.dataset.number === undefined) return;
  e.preventDefault();
  const { number: key, case: ci, term } = f.dataset, c = state.cases[Number(ci)];
  const input = f.querySelector("input"), error = f.querySelector(".number-error");
  function fail(message) {
    error.textContent = message;
    input.classList.remove("invalid-entry");
    if (!motion.matches) { input.getBoundingClientRect(); input.classList.add("invalid-entry"); }
    input.setAttribute("aria-invalid", "true");
  }
  const value = normalizeNumberInput(input.value, state.space.dims[key].unit);
  // A number input controls exactly one fact; it cannot append a second code token.
  if (/\s/.test(value)) { fail("Enter just one number."); return; }
  const parsed = pac.parseCode(`${key}=${value}`, state.space);
  if (parsed.errors.length || parsed.features[key] === "?") {
    fail(parsed.errors[0]?.message || "Enter a number, or choose Don't know.");
    return;
  }
  setTermFact(c, term, key, parsed.features[key]); renderCases();
});
$("judge-date").addEventListener("change", () => { if (state.space?.v2) renderCases(); });
$("add-case").addEventListener("click", () => {
  if (state.space?.v2) state.cases.push(newTermCase());
  else { state.picking = true; state.catPath = []; }
  renderCases();
  const el = state.space?.v2 ? $("cases").lastElementChild : $("pick-category");
  el?.scrollIntoView({ behavior: scrollBehavior(), block: "start" });
});
$("judge-cases").addEventListener("click", judgeCases);
$("restart").addEventListener("click", () => { restart(); window.scrollTo({ top: 0, behavior: scrollBehavior() }); });
$("copy-code").addEventListener("click", () => {
  const r = state.result;
  const code = r.flow ? (r.stages || r.flow.map((_, i) => [i])).map((st) => st.map((i) => r.flow[i].code).join(" & ")).join(" > ") : r.code;
  navigator.clipboard && navigator.clipboard.writeText(code);
});
$("dl-md").addEventListener("click", () => download("policy-check.md", pac.renderReport(state.result, state.space), "text/markdown"));
$("dl-json").addEventListener("click", () => download("policy-check.json", JSON.stringify(state.result, null, 2), "application/json"));
