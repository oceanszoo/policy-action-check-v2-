# Policy Action Reader

A no-model app for policy-action-check bundles. Open a bundle (`generator.json` + `judge.json`,
optionally `bundle.json`, `records.jsonl`, and `BUNDLE.md`), build your cases, and get the
report: what to do next, the verdict, must-do steps, unknown facts,
the possible results while facts are unknown, the smallest fix and your notes. Nothing is uploaded
and no model is used: the page runs entirely in the browser.

For a format 1.5 or newer bundle, open **Guide** to read its bundled `BUNDLE.md` as plain text.
If a bundle at format 1.6 or later includes source terms, the report quotes them under the relevant
rules, with their clause IDs and sections. Summaries are labelled rather than quoted.
If the manifest lists a digest for the guide, the reader verifies the loaded guide alongside the
other files. Bundle authors can generate the guide with `pac.py --space <bundle> guide`.

**Build cases** in format 2.0 starts with the policy's sections and root terms. Open a term and
choose the values that meet or do not meet each of its keys. Number keys take a typed value and
show the unit and limit. Selecting a parent opens its child terms; keys shared by multiple
terms only need one answer. Check a term's live badge for its status, and open the term to see
its next step and citations when matched.

The **Other parties' duties** group contains assumptions about what someone else will
do. Override an assumed answer by picking another value or **Don't know (skip)**. Use
**Reset to pre-selected** to restore the assumption. The report identifies when the result
relies on one of these duties.

While you build, the bottom dock keeps **Judge** and your current code in reach. For 2.0 bundles
it also shows how many visible terms are left to answer and a **So far** verdict for the code as it
stands. The preview uses the same judgment as **Judge**; it can change as you answer more terms.
For 1.x bundles, the dock shows the code and **Judge** without term counts.

The default order is the term map. In **Split** order the reader suggests a next key by how
many unsettled terms use it. It points out choices fixed by the bundle and lets you stop
when further answers cannot change the verdict. You may still continue or skip a fact.

**Build cases** for 1.x bundles works in three steps. First, open the case map, a tree of categories
as deep as the bundle's material needs, and pick a category at any level. Second, open its feature
folders and choose features; folders for facts that only matter after a choice sit inside that
choice's folder, and an empty folder is skipped when you can't confirm the fact. Third, with
several cases, say whether each one happens after the one before (`>`) or at the same time (`&`).

**Arrange order** lets each person move likely categories, feature folders and features to the top
(and rarely used ones down). It changes only what is shown first, never the result, and is kept per
bundle in that browser; **Reset order** goes back to the bundle's order. Skipped facts don't block
the result: the report lists every region the case could land in, for example
"If `auth=own`: Allowed; if `auth=na` or `auth=unauth`: Not allowed".

## Use it

- **Easiest:** open [`dist/pac-reader.html`](dist/pac-reader.html) in a browser (double-click it). It is one
  self-contained file and works offline. Press "Try the example" or open your own bundle folder.
- **Host it:** put the `dist/` file on any static host (GitHub Pages works).

What it shows when a bundle loads:
- whether the bundle passed its **self-exam** (`bundle.json` `exam`), and warns if it failed;
- whether the files still match the digests in `bundle.json`.

## How it works

| file | role |
|---|---|
| `pac.js` | the engine: parse codes, judge (three-valued rules), smallest fix, question form, keyword lookup, report. Plain JavaScript, no dependencies, browser and Node |
| `app.js`, `index.html`, `styles.css` | the page |
| `build.mjs` | writes `example-bundle.js` and the single-file `dist/pac-reader.html` |

`pac.js` follows `plugins/policy-action-check/references/SPEC.md` and must agree exactly with the
reference engine `plugins/policy-action-check/scripts/pac.py`.

## Develop

```sh
node apps/pac-reader/build.mjs            # rebuild example-bundle.js and dist/pac-reader.html
node apps/pac-reader/tests/parity.mjs     # JS vs pac.py on every bundle in the repo (needs python3)
node apps/pac-reader/tests/ui.mjs         # browser smoke test of the built page (needs playwright)
```

`tests/parity.mjs` compares every output (judgement, fixes, next actions, facts, form questions,
lookups, report text) for conformance codes, generated codes, typos, flows and full form runs.
Pass bundle folders as arguments to check others. To serve the source files during development
(ES modules need http), run `python3 -m http.server` in this folder and open `index.html`.
