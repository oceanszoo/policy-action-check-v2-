---
name: policy-pipeline
description: Use automatically whenever someone asks whether an action, plan, workflow or tool use is allowed under a policy, terms, rules or regulation; gives policy text or action history to analyse; writes or asks about an action code; or wants a generator/judge for some terms. Runs the whole policy-action-check pipeline and returns the final outcome without asking the user to pick steps.
---

# Policy pipeline (orchestrator)

You run the whole pipeline yourself and give the user **the final outcome**. Never ask the user
to choose a skill, command or stage. Ask them only the scope questions from Stage 1, and only
when the answer changes what gets built.

Engine: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pac.py" --space <bundle dir> <command>`.
The bundle dir is the user's configured folder (default `policy_space/` in the project).
Method and formats: `${CLAUDE_PLUGIN_ROOT}/references/method.md` and
`${CLAUDE_PLUGIN_ROOT}/references/SPEC.md`.

## Terms first, model-free use

Only policy terms and their definitions go into a build. Do not read history, existing cases,
examples, similar records, or previous bundles to construct vocabulary, rules, choices,
frequencies, or scope. History can be evaluated only after the bundle is built and frozen.

The result is a **generator** (`generator.json`: dimensions, term map, code grammar, duty
and scope) and a **judge** (`judge.json`: compiled rules, cited terms, deterministic verdict,
requirements and fix). The manifest, conformance vectors, and guide travel with both files.
The term map, guided questions, keyword lookup, check and report are plain code; none needs
a model at use time. Give the engine's report rather than your own verdict.

## Decide what to run

Run `pac.py status`. If there's no bundle or the policy changed, run stages 0–7. If the
user supplied only new history for a valid existing bundle, run stage 8 only. Never treat a
history change as stale build input. If the user requests refinement, use Refine below.
To check an action with a usable bundle, run the deterministic engine without rebuilding;
a model encoder inside Claude Code is optional when the user gives prose instead of a code.
Register the policy with `pac.py state --policy <path>`. Use the `filter`, `scope`, `build`,
`encode`, `check`, and `report` phases for progress, then mark `--stage done`.

## Build a bundle

0. **Filter**: dispatch `policy-action-check:term-filter`. It writes `work/terms.json`
   with exact text, the section and party each term binds, classifications and references.
   Keep definitions and link them; descriptive examples are not build inputs. Run
   `terms-lint` and `validate --stage filter`.
1. **Scope**: dispatch `policy-action-check:scope-planner` with terms and user-stated facts
   only. Ask one specific question for each undecided policy section and ask once which
   party or parties the person is. Batch unanswered questions in one message; save scope
   and `duty.parties` in `work/scope.json`; run `validate --stage scope`. Use `state --awaiting-user` and resume with
   `state --resume` after the answer. In a noninteractive run apply scope recommendations,
   disclose them; never preset a person's duties based on a guessed party. If duty
   parties remain unknown, report the pending question rather than silently assuming none.
2. **Tree**: dispatch `policy-action-check:term-tree` to write `work/term_tree.json`.
   Exceptions have exactly the parents they modify. Record the role, parents, title,
   next step and binds. Out-of-scope terms are kept as scope context, not map nodes.
3. **Vocabulary**: dispatch a separate `policy-action-check:term-tree` pass to write
   `work/vocabulary.json` from the normative terms and definitions. Freeze the dimensions
   before either parse. Descriptive examples do not determine them.
4. **Parse**: dispatch two independent `policy-action-check:key-parser` runs, in parallel
   or without exposure to each other's output. Give both the same term tree and vocabulary.
   Each runs `terms-context <id>` and anchors every key; write `work/keys_a.json` and
   `work/keys_b.json`, and lint each with `keys-lint --keys <parse path>`. Compare the
   untouched parses with `keys-diff <parse A path> <parse B path> --write`. Supply file paths
   resolved relative to your working directory, not to `--space`.
   Only if the user explicitly passes `--single-parse`, omit the second call and mark
   agreement unmeasured; never copy A as B or claim full agreement. In a reused work
   directory replace any prior comparison with the current `{"single_parse": true}` marker
   in `work/key_agreement.json`.
5. **Verify**: send the diffs, both originals, the term contexts, and the frozen
   vocabulary to `policy-action-check:space-verifier`. The verifier may only choose one
   parse, merge supported keys from the two, or send a term to `not_encoded`. It writes
   `work/keys.json` and `work/verifier_log.md` quoting the supporting passages; run `keys-lint`
   on the final file. Don't recompute the score on reconciled keys.
6. **Compile**: run `pac.py compile`. Plain code writes the graph-derived `term_map`,
   anchored lexicon, rules and conformance. Neither the orchestrator nor an agent
   writes generated rules or conformance by hand.
7. **Exam**: run `pac.py exam`; if it fails, return to the relevant source stage and
   preserve the raw parse evidence. Never lower the thresholds or edit generated files
   to pass. After the exam, run `pac.py manifest --policy <source>`, `pac.py validate`
   and `pac.py guide --check`. Do not claim an unpassed bundle is ready.
8. **Evaluate (optional, after the build is frozen)**: dispatch
   `policy-action-check:action-encoder` to encode history in `work/history_encoded.jsonl`
   against the frozen vocabulary only. Preserve outcomes and flag facts without a
   dimension. If needed, document the permitted verdicts per outcome label separately
   in `work/outcome_map.json`; never force a mapping to improve agreement. Run `pac.py evaluate --history <encoded file>` and read `work/eval.json`.
   The report is separate from the badge. Regenerate the guide and manifest to ship
   the evaluation summary, if requested; do not change vocabulary, rules or the badge.
   Records and transitions may be attached for display only.

## Check an action

Use the term map or `pac.py ask` / `pac.py form`, `pac.py lookup` for keyword lookup,
or the supplied code. Optionally use `action-encoder` to turn user-provided prose into a
proposed code, preserving only stated facts. Run `pac.py check "<code>"` for structured
output and `pac.py report "<code>"` for the outcome; use `pac.py panel "<code>"` to show
live status while editing. Never infer facts from history or choose a verdict yourself.
A missing fact stays unset; `key=?` in 2.0 explicitly overrides a preset or default.

## Refine

Run `pac.py gaps --write`, with `--focus "<text>"` if supplied, and retain the initial
counts. Give `policy-action-check:space-refiner` the gaps, exact SHA-256 of the gaps bytes,
and source terms. Evaluation disagreements may point to a suspect key, but do not justify
changing it. In 2.0 require an anchor for each `add_key` or `revise_key`; never change a
compiled rule or map by hand. Use the documented 1.x operations only on legacy bundles.
Fix `out_of_scope_effect` in the source constraints, not by adding a path for an
inapplicable key.

The agent writes only `work/refine_patch.json`. Run `apply-patch --dry-run` before
`apply-patch`; review actionable refusal reasons rather than editing around the checks.
Stop after three rounds, or when the exam passes and gaps stop shrinking. Report before
and after counts and any outstanding problems. Never lower thresholds.

## Final outcome (what the user sees)

Keep it short. Lead with the answer.

- **For an action**: lead with **what to do next** (the engine's `next_actions`, in order:
  stop / do with the code change / establish a fact / proceed). Then give the verdict in one
  line; the code and its plain reading; what is violated
  (rule, source, the tokens that place it there); then two separate lists, never merged:
  **must do** (the engine's `requirements`, which bind) and **still unknown** (its
  `unknown_facts`, each with the evidence that settles it); any `assumed` default in `facts`
  that matters to the result; the fix as a code diff; the usual next step; similar past records; any out-of-scope or terms-only warning.
  End with "a structured self-check, not legal advice".
- **For a fresh or rebuilt bundle**: the self-exam scores (pass/fail per check), how to use it
  with no model (term map, guided form, or keyword lookup), where it is, how many clauses were real terms vs
  description, the number of dimensions and rules, the scope and duty decisions, any separate post-build evaluation findings, the remaining open
  questions, and three example codes with their verdicts. Mention both files: the generator
  (how to write codes) and the judge (how codes are judged).
- If `check` returns `invalid_code`, show the "did you mean" suggestions and don't give a
  verdict.

## Rules for you

- The engine's verdict is final. If you think it's wrong, the bundle is wrong: fix the rule or
  the code through the anchored keys and deterministic compile or refine stages, and don't override the verdict in prose.
- A fact the user didn't state is unknown, never "no".
- Context the user gives that isn't a choice (a reason, a caveat, an opinion) goes into a note
  (`--note`), which the report shows and the judge ignores. It never changes a key.
- Inputs are objective conditions only. If the user offers a judgement ("it's low risk", "we
  mean well", "should be fine"), don't encode it. Ask for the fact behind it, naming the key
  and its evidence (for example "Is there a review log showing a licensed reviewer could change
  it? → rev=y/n").
- Never invent rules. Every rule cites its source.
- Hooks may add a `[policy-action-check]` note to prompts and may ask before tool calls. Treat
  those as part of this pipeline.
