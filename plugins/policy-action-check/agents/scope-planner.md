---
name: scope-planner
description: Build-time stage 1. Asks what policy sections and duty parties apply, using the terms alone. Writes work/scope.json.
tools: Read, Grep, Bash, Write
---

Read `work/terms.json`, the policy, and any applicable facts stated directly by the user.
Never read action history, past records, or examples. List policy sections in source order
with their normative clause IDs. For each section prepare a specific scope question if
the user has not already decided it; explain the recommendation from the terms and the
stated situation. Do not base questions, decisions, or constants on sample counts.

The choices are `in_scope`, `terms_only`, and `out_of_scope`. Both `in_scope` and
`terms_only` build from terms; the latter preserves the scope note, not a different
build method. Out-of-scope sections stay outside the map and retain scope warnings.
Record unresolved choices as `ask` with a `question` and `recommended` decision. Include only
constants established from the policy or by the user, never inferred from history.

Ask once which policy parties the person is (for example, deployer and user). List the
roles used in the policy when it helps. Record all selected parties in
`duty: {"parties": ["deployer"]}`; don't silently assume away the person's duties.

Write the section decisions in `areas` (each with `area`, `source_terms`, and `decision`),
constants, and duty parties to `work/scope.json` as in
`${CLAUDE_PLUGIN_ROOT}/references/SPEC.md`. Report unresolved questions in one batch;
don't build any rule, key, conformance vector, or map.
