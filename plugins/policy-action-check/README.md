# Policy Action Check

Compile the constraints in a policy into a **bundle of two files**:

- **Generator** (`generator.json`): how to write an action as a short code, for example
  `claim-auto: act=biz hr=ins scope=ind fav=part rev=n disc=y`.
- **Judge** (`judge.json`): how to judge a code. It says which terms the code violates, what is
  required next, and the smallest fix (`rev=n -> rev=y`).

Every code is the readable surface of a vector: one coordinate per key, and a missing key is
unknown. Terms are regions in that space, so judging is exact. The same code always gets the
same verdict.

**Using the bundle needs no model.** At build time Claude identifies policy clauses,
structures them as a term tree, and independently parses exact phrases into objective keys
twice. A deterministic compiler writes the rules, the term map and conformance tests.
The term map or keyword lookup writes a code; a deterministic engine judges it and prints
a fixed report. See [format 2.0](references/SPEC.md); the engine and reader also support 1.x.
History is optional evaluation after the bundle is frozen, not build input.

People click choices or type numbers to build the vector. Presets for other parties' duties
are visible and can be overridden. They can add a note to any choice
or to the whole action; notes are shown in the report and never affect the verdict.

An action that does several things at once lists them all on one key (`pur=data+track`). Each
result lists **what you must do** (binding requirements) apart from **what is still unknown**
(facts nobody stated), and shows where every fact came from.

Every 1.5 or newer bundle includes a generated `BUNDLE.md` with the term map (case map for 1.x), features, rules, examples
and self-exam badge. Open it directly or use the **Guide** link in the offline reader.
`pac.py guide` regenerates it; `pac.py guide --check` checks whether it is current.

The bundle tracks definitions and links between policy clauses. `pac.py terms-lint`
checks the links, and `pac.py terms-context <clause-id>` shows what a clause depends on.
Compilation embeds the cited sources before the exam and manifest. Reports and the guide can then quote the terms without
reopening the policy or calling a model. Only embed text you are allowed to distribute.

To grow an existing bundle, ask to refine it, optionally with a focus such as "privacy".
`pac.py gaps --write` finds gaps. The build-time refiner proposes a patch, and
`pac.py apply-patch --dry-run` validates it without writing. `pac.py apply-patch` applies the
patch, reruns the exam and records the round. Gap detection, patch application and guide
generation are deterministic and use neither a model nor the network.

## Install (Claude Code)

```
/plugin install policy-action-check --marketplace oceanszoo/policy-action-check-v2
```

## Use

Just ask. You don't pick skills or commands.

- "Build a policy bundle from `terms.md`, then evaluate `history.csv` against it."
- "Can our claims bot auto-deny claims under our service terms?"
- "`act=biz pur=std hr=emp scope=ind fav=part rev=n`: is this ok?"

A prompt hook starts the pipeline. Scope questions ask about policy sections and, once
per build, which party or parties you are. Use `--single-parse` to opt out of the second
model parse; the build then reports agreement as unmeasured.

```
policy ─▶ filter ─▶ scope ─▶ term tree ─▶ frozen vocabulary ─▶ parse ×2 ─▶ verify
       ─▶ compile ─▶ exam ─▶ bundle
optional history ─▶ encode using the frozen bundle ─▶ evaluate
action code ─▶ judge ─▶ outcome
```

| Part | What it does |
|---|---|
| `skills/policy-pipeline` | orchestrates the build, evaluation, and use |
| `agents/term-filter` | separates normative terms, definitions, and descriptive material |
| `agents/scope-planner` | prepares section scope and duty questions using terms alone |
| `agents/term-tree`, `agents/key-parser` | propose the term tree and frozen vocabulary, and parse anchored keys |
| `agents/space-verifier` | resolves disagreements between the independent parses |
| `agents/action-encoder` | optional words-to-code convenience and post-build history encoding |
| `scripts/pac.py` | deterministic compiler, examiner, evaluator and judge; standard-library Python |
| `hooks/hooks.json` | intent, stage, and optional tool-call guards |
| `examples/sample-service-terms` | example bundle built from an invented "Sample Service Terms" policy |

### Settings

| Setting | Values | Default |
|---|---|---|
| Guard tool calls (`guard_mode`) | `off`, `warn` (ask you), `enforce` (deny violations) | `warn` |
| Bundle folder (`space_dir`) | a folder name | `policy_space` |
| Judge as of date (`policy_date`) | `YYYY-MM-DD` | today |

The tool-call guard does something only when the bundle's generator has a `tool_map`, which
maps tool calls (such as an MCP tool that sends claim decisions) to codes.

## Self-exam

Before a bundle is finished, `pac.py exam` tests it the way open-source software is tested, with
no model: term and rule coverage, anchor and parse agreement, references, map reach, mutation
testing, and property checks. History replay and map fit are separate, with no effect on the badge. `pac.py manifest` stamps the result into `bundle.json`, so
your own software can refuse a bundle that failed.

```sh
python3 scripts/pac.py --space policy_space exam
```

## Use a bundle without Claude (no model)

```sh
python3 scripts/pac.py --space examples/sample-service-terms form
python3 scripts/pac.py --space examples/sample-service-terms lookup "privacy"
python3 scripts/pac.py --space examples/sample-service-terms validate
python3 scripts/pac.py --space examples/sample-service-terms guide --check
```

Use a code shown in the generated guide with `check`, `panel`, or `report`. Cases can be composed
with `&` (same time) and `>` (step by step). The offline reader displays the term map for 2.0 and
the category page for older bundles.

## Develop

```sh
python3 -m pytest plugins/policy-action-check/tests
claude plugin validate plugins/policy-action-check
```

To add a policy, add an example bundle under `examples/<policy>/` with a README, and make sure
`pac.py validate` passes. Every compiled rule needs a source term and conformance coverage. See [CONTRIBUTING.md](CONTRIBUTING.md).

This is a structured self-check, not legal advice.
