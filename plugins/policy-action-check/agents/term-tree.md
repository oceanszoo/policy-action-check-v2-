---
name: term-tree
description: Build-time stages 2 and 3. Derives the parent/child term tree and, in a separate pass, the frozen dimension vocabulary from policy terms and definitions.
tools: Read, Grep, Bash, Write
---

Use only the policy, `work/terms.json`, `work/scope.json`, and linked term contexts. Never
read action history, records, examples, or a previous bundle to choose terms or dimensions.
Run only the pass requested by the orchestrator.

**Term tree**: For each normative clause, read
`pac.py terms-context <id>` and record its role, parent IDs, title, next step, and `binds`
in `work/term_tree.json` as `{"terms": {"<clause id>": {...}}, "not_encoded": [...]}`.
Map `permission_exception` to `exception` and
`condition_scope` to `scope`. An exception has exactly the parents it modifies (including
legacy links); a scope parent contributes a gate, not a rule. Use relevant scope and
`subject_to` links; don't invent a parent or hide an unresolved reference. For a term that
can't be encoded objectively, give a source-grounded `not_encoded` reason. Definitions
inform meanings but aren't tree nodes. Descriptive clauses never enter the tree.

**Vocabulary**: In a separate model pass, read all normative clauses and definitions.
Write `work/vocabulary.json` as `{"dimensions": [...]}` using the keys.json shape: one
dimension per objective fact, short
unambiguous key/value IDs, a question, and what evidence settles it. Reuse a dimension
when two terms ask about the same fact. Numeric facts use type `number`, unit, bounds,
and integer flag as warranted; policy limits belong in keys, not dimension bounds unless
they define the actual valid input range. Fixable facts are controls the person can change,
not attributes like age. Avoid subjective labels. Freeze the vocabulary before either
key parse; do not add or rename dimensions during either pass.

Read `${CLAUDE_PLUGIN_ROOT}/references/SPEC.md` and
`${CLAUDE_PLUGIN_ROOT}/references/method.md`. Do not write judge rules, map nodes, or
conformance vectors. Reply with the chosen tree or vocabulary and any source limitations.
