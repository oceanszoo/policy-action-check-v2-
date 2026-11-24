# Contributing

## Ground rules

- **The engine is the judge.** Verdicts come only from `scripts/pac.py` running on the bundle
  files. If a verdict is wrong, fix the bundle, not the prose around it.
- **Spec first.** A change to the bundle format updates `references/SPEC.md`, the version
  number (minor if compatible, major if not), the engine, and the tests, all together.
- **Standard library only** for `pac.py`, so the bundle can be judged anywhere.
- **Every rule cites its source** and has at least one conformance vector. Exceptions need
  vectors on both sides.
- **Unknown is never "no".** Requirement dimensions must not have defaults.

## Adding a policy example

1. Create `examples/<policy-id>/` with `generator.json`, `judge.json`, `conformance.jsonl` and
   a `README.md` (the source URL, effective date, and what is in and out of scope).
2. Write conformance vectors from the policy text, not from the engine's output.
3. Run `python3 scripts/pac.py --space examples/<policy-id> validate` and the tests.

## Changing the engine

Add a test in `tests/test_pac.py` for the behaviour, keep `ruff check .` clean, and run
`claude plugin validate plugins/policy-action-check`.
