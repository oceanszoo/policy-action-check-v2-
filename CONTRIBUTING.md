# Contributing

Thanks for helping. Issues and pull requests are welcome.

## Ground rules

- **The engine is the judge.** Verdicts come only from `plugins/policy-action-check/scripts/pac.py`
  running on the bundle files. If a verdict is wrong, fix the bundle, not the prose around it.
- **Spec first.** A change to the bundle format updates `references/SPEC.md`, the version number
  (minor if compatible, major if not), the engine, the reader and the tests, all together.
- **Standard library only** for `pac.py`, and no dependencies for `apps/pac-reader/pac.js`, so a
  bundle can be judged anywhere.
- **The two engines agree.** `pac.js` must give exactly the same outputs as `pac.py`;
  `apps/pac-reader/tests/parity.mjs` checks it.
- **Every rule cites its source.** Keys quote an exact phrase of their term, and the compiler
  writes conformance vectors for every rule, key and exception.
- **Unknown is never "no".** Requirement dimensions must not have defaults.
- **Only embed policy text you may distribute.** Prefer clearly labelled summaries.

## Adding a policy example

1. Build it with the plugin (or write `work/terms.json`, `work/scope.json` and `work/keys.json`
   by hand), then run `pac.py --space <folder> compile`, `exam` and `manifest --policy <url>`.
2. Ship `generator.json`, `judge.json`, `conformance.jsonl`, `bundle.json`, `BUNDLE.md` and a
   `README.md` (source, effective date, scope, and a not-affiliated note) under
   `plugins/policy-action-check/examples/<policy-id>/`. Leave `work/` out.
3. Run `python3 plugins/policy-action-check/scripts/pac.py --space <folder> validate` and the tests.

## Before you open a pull request

```sh
ruff check .
pytest
node apps/pac-reader/build.mjs --check   # dist/ must be current; rebuild and commit it if not
```

If you change the plugin, also run `claude plugin validate plugins/policy-action-check` when the
Claude Code CLI is available.

Bundle files and the reader are stored with LF line endings (see `.gitattributes`); keep them
byte-identical, because bundles carry digests.
