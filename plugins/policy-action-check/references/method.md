# Method

## The idea

**The plugin pre-cooks; the bundle runs alone.** Models parse the terms into anchored constraints at build time,
and plain code compiles their parses. The bundle (generator + judge) is used with no model at all: a question form
or keyword lookup writes the code, and the engine judges it and fills a fixed report. People
build the vector only by clicking choices; they may add notes, which travel with the result for
people to read and are never judged. A number key is typed rather than clicked. Anything a
model would have to decide at use time is compiled into the bundle or left out.

An action is a point in a small feature space that **you build**, and every dimension in it has a
name and a meaning. Policy terms are regions in that space. Where an action sits tells you
which terms it violates, which requirements it has triggered, and the smallest move that makes
it compliant.

This looks like an embedding space, but it isn't one. Text similarity can't decide compliance:
"monitor staff with consent" and "monitor staff without consent" read almost the same, but only
one of them is allowed. Similarity is used only to propose codes from words and to find
similar past records.

**An action code is the readable surface of a vector.** Each key is one coordinate. A missing
key is an unset coordinate, so a code stands for a region of possible vectors, not a single
point. Rules are regions. Checking is three-valued over unset coordinates. A fix is a move to
the nearest vector outside every violation region, written as a code diff. Similar past records
are nearby vectors.

**Inputs are objective conditions. The output is what to do next.** Every dimension is a fact
that evidence can settle: what the action does, what exists, who agreed, what was recorded.
Opinions, intentions and risk ratings are refused. The engine rejects them, and the encoder
turns them into a question about the underlying fact. The judge leads with `next_actions`:
stop, do (with the code change), establish a missing fact, or proceed.

## Pipeline

```
policy ─▶ 0 filter ─▶ 1 scope ─▶ 2 term tree ─▶ 3 freeze vocabulary
       ─▶ 4 two independent key parses ─▶ 5 verify differences ─▶ 6 compile ─▶ 7 exam
optional history (after build) ─▶ 8 evaluate ─▶ findings, not a release gate
```

### Filter and scope (0–1)

Split each policy section into normative clauses (prohibitions, obligations, exceptions
or scope conditions), definitions, and other descriptive material. Preserve exact wording,
heading, source, confidence, and the party each normative clause binds. Record typed
references and their targets. Definitions inform vocabulary and may anchor keys, but
descriptions, examples, and history never supply facts or rules. Cite all sources.

Ask the person what policy sections apply and once which party or parties they are.
An `in_scope` or `terms_only` decision is built from terms; `out_of_scope` never adds
a rule or map route, and should not be passed off as policy compliance. Retain scope
warnings. Constants are independently established fixed facts, not inferences from records.

### Tree, frozen vocabulary and independent parsing (2–5)

Put rooted terms into sections in policy order. A child is available only if one of its
parent paths is chosen. A term is chosen when its gate and all gates along an ancestor
path are true. Each exception must name exactly its modifies targets as parents. Pure
scope parents contribute gates without generating rules of their own.

Before parsing, decide one objective dimension per fact and freeze those dimensions for
both parses. Include a question and the evidence that settles it. Many policy clauses may
test the same dimension. Use multi-valued choices for several concurrent values, and a
typed number for measurable thresholds. Keep subjective labels out. A requirement should
not be assumed from silence; only establish a default if the policy supports one. Only a
control the person can change is fixable, never their age or another immutable fact.

For each term, read `pac.py terms-context <id>`, then extract only its applicability
keys (`gate`) and, for obligations, its compliance keys (`require`). Quote the phrase
in the source or its linked definition for each leaf. A summary-only term anchors to
the stored summary, not to invented policy text. Keep hard-to-operationalize terms in
`not_encoded` with a reason.

Run two isolated parses against the same vocabulary and compare their canonical keys
before reconciliation. Differences go to an independent verifier, who can pick one,
merge source-supported material from both, or mark the term not encoded, with exact
support and a recorded reason. `--single-parse` skips the independent measurement,
not the source grounding or lint.

### Compile and examine (6–7)

Plain code compiles rules, term map and order, conformance cases, and lexicon seeds.
The rule gate incorporates the chosen ancestor path; exception children narrow the
parent's prohibition or obligation. A number comparison uses explicit open/closed
bounds. Duty presets assume other parties meet their requirements or avoid their
prohibited conduct, only when the tested dimension is not shared with a term that
binds the person. Code can override any preset with a value or explicit unknown.

`pac.py exam` checks term coverage, key anchors, pre-verification agreement, references,
rule coverage, mutation testing, properties, and map reach without a model.
Compiled vector expectations check reader compatibility, not an independent interpretation
of the policy; the independent second parse and verifier supply that. Thresholds are not
a repair knob. The manifest stamps the badge and generates the guide.

### Evaluate history (8), optionally refine

Encode records only against the frozen vocabulary, then use the deterministic evaluator.
Use disagreements, decisive share, unreachable values and missing dimensions as findings,
not a release gate or authority to change the policy. A refiner may propose an anchored
`add_key` or `revise_key` for a real omission; a recorded action or outcome is not an anchor.
Optional attached records and transitions are display-only.

### Use (no model)

The term map shows a section's roots and opens children when a parent is chosen. One
click chooses a value for one key; confirm a typed number for a number key. Shared
dimensions are answered once. An explicit unknown overrides any earlier source; a
reset removes the token and restores the preset. A note can travel with any choice
without affecting the verdict. The guided walk and keyword lookup are deterministic.
Inside Claude Code a separate convenience encoder can propose a code from words; it
must preserve evidence and leave unstated facts unset, never guess from prior records.

## Judge

The engine (`scripts/pac.py`) is the only judge, so the same code always gets the same verdict.

| status | meaning |
|---|---|
| `violated` | the vector is inside the rule's violation region whatever the unset keys are |
| `required_next` | an obligation is triggered and its required key is unset |
| `open` | an unset key decides whether a prohibition applies |
| `satisfied` | the rule applies and is met, or an exception holds |
| `not_applicable` | the rule's region can't contain this vector |

The verdict is `violates` if anything is violated, else `compliant_if_requirements_met` if
anything is required, else `needs_info` if anything is open, else `compliant`. A code with
errors is `invalid_code`.

The judge also reports, kept apart: `facts` (every value used and where it came from: the code,
a saved code, a constant, an assumed preset, or an assumed default), `requirements` (obligations the action has
triggered, which bind) and `unknown_facts` (unstated facts that decide an open rule).

**Fix.** The cheapest change (filling an unset key costs 0.5, changing a set key costs 1) that
leaves no violated or required rule, using fixable keys only. Leave presets alone unless overridden by the code. If only non-fixable
keys decide, there is no compliant variant.

**Live panel.** After each token: what is now violated, what is now required, what is still
open, and the next visible key. No frequencies suggest an answer. Optional split order favors the
dimension that helps settle the most unsettled visible terms.

## Writing the outcome for a person

Lead with the verdict. Then give: the code and its plain reading, what's violated with its
source, the binding requirements and the unknown facts as two separate lists, any assumed
defaults that matter, the fix as a code diff, the usual next step, similar past
records, and any scope warning. It is a structured self-check, not legal advice.
