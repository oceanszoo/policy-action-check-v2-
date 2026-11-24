# Changelog

## 0.8.0 - format 2.0

- Bundles are built from the terms: each term is parsed into anchored objective keys, placed in a
  term tree, and compiled into rules, a term map and conformance tests by deterministic code.
- Number keys (`lt`, `le`, `gt`, `ge`, `between`) and pre-selected duties of other parties
  (`key=?` marks a fact as explicitly unknown).
- History is evaluation only, after the bundle is frozen.
- Policy Action Reader: term map for 2.0 bundles, live term status, number entry; 1.x bundles
  still open on the category page.
- Example bundle: invented "Sample Service Terms".

## Bundle format history

See [SPEC.md](plugins/policy-action-check/references/SPEC.md) for details.

- **2.0**: terms-first build (term tree, anchored keys, compiled rules and term map), number keys, duty presets, semantics `kleene-3v-2`.
- **1.6**: typed clause references and a glossary; reference lint, context lookup; embedded source terms and exact citations in results and guides.
- **1.5**: deterministic refinement (gaps, patches) and a generated `BUNDLE.md` guide in every bundle.
- **1.4**: case map (`categories`, nested folders), generator page, `a & b` and `a > b` cases, every possible result when facts are skipped.
- **1.3**: bundle self-exam (`exam`, `outcome_map`, `not_encoded`).
- **1.2**: question form, keyword lookup, records, fixed report layout, next-step lookup, notes. No model needed at use time.
- **1.1**: multi-valued dimensions, size limits, `facts` / `requirements` / `unknown_facts` in judge output.
- **1.0**: first format: generator, judge, conformance vectors.
