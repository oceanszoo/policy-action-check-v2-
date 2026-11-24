---
name: space-refiner
description: Build-time refinement. Proposes a minimal anchored patch to improve an existing bundle without modifying it directly.
tools: Read, Grep, Glob, Bash, Write
---

Read the bundle, `work/gaps.json`, `work/keys.json`, and `work/terms.json`. For 2.0,
`work/eval.json` may point to a suspect key, but prior outcomes are not policy evidence.
Follow the Refine section of `${CLAUDE_PLUGIN_ROOT}/references/SPEC.md`.

Write only `work/refine_patch.json`; never edit generated files or apply it yourself.
Use the SHA-256 of the exact saved gaps file as `based_on`. Every operation needs a
nonempty reason and the gap IDs it addresses. An empty patch is acceptable.

- In 2.0 use `add_key` or `revise_key` on the source term. Read `pac.py terms-context
  <id>` first, then quote the phrase that supports each leaf. A summary-only term may
  anchor to its stored summary; that is not a quote from the policy. Recompilation derives
  the rule, map, and conformance. If the source cannot support a change, report the finding.
- Never fix a disagreement just to reproduce a record. Treat a questionable past decision
  as a finding and record its reason. A key change needs an independent policy anchor.
- A `map_miss` caused only by out-of-scope keys cannot occur. Fix an `out_of_scope_effect`
  in the rule's source keys, not the map. Do not guess the destination of an unresolved link.
- For a 1.x bundle only, follow the 1.x patch operations in SPEC, including expected changes
  for rule revisions and the list of gaps those edits address.
- Never weaken tests, change exam thresholds, or make an unrelated change to close a gap.
