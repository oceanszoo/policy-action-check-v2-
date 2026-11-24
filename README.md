# Policy Action Check 2.0

Turn a policy or terms of use into a small **bundle of two files** that anyone can use to check an
action, with **no AI model at use time**:

- `generator.json` says how to write an action as a short code, for example
  `pur=data cons=n`, and holds the **term map** people click through to build that code.
- `judge.json` says which terms a code violates, what you must do next, and the smallest fix.

The same code always gets the same verdict. Unknown facts are reported as unknown, never as "no".

Format 2.0 builds the bundle **from the terms themselves**: each term is parsed into objective
keys, each anchored to an exact phrase of the term, and placed in a term tree (a child term opens
only once its parent applies). A deterministic compiler then writes the rules, the term map and
the conformance tests. Number keys (`age < 18`), and pre-selected duties of other parties that
you can override, are supported. Past records are optional and only used to evaluate a finished
bundle, never to build it. The engine and reader still read 1.x bundles.

This repository has two parts:

| part | what it is |
|---|---|
| [`plugins/policy-action-check/`](plugins/policy-action-check/) | A Claude Code plugin that reads a policy once and builds the bundle. It also ships the reference engine `scripts/pac.py` (Python standard library only). |
| [`apps/pac-reader/`](apps/pac-reader/) | **Policy Action Reader**, a single-file web app that opens a bundle, lets you build cases on the term map, and shows the report. It runs entirely in the browser and uploads nothing. |

The bundle format is specified in
[`plugins/policy-action-check/references/SPEC.md`](plugins/policy-action-check/references/SPEC.md)
(version 2.0), so other software can read bundles too.

## Quick start

**Try the reader.** Download [`apps/pac-reader/dist/pac-reader.html`](apps/pac-reader/dist/pac-reader.html),
open it in a browser and press **Try the example**. The example is built from an invented
"Sample Service Terms" policy; see [its README](plugins/policy-action-check/examples/sample-service-terms/README.md).

**Build your own bundle (Claude Code).**

```
/plugin marketplace add oceanszoo/policy-action-check-v2
/plugin install policy-action-check@oceanszoo-plugins
```

Then ask, for example: "Build a policy bundle from `terms.md`."

**Judge a code from the command line.**

```sh
python3 plugins/policy-action-check/scripts/pac.py --space plugins/policy-action-check/examples/sample-service-terms report "pur=data cons=n"
```

## Layout

```
.claude-plugin/marketplace.json   Claude Code marketplace entry
plugins/policy-action-check/      plugin: agents, hooks, skill, engine (scripts/pac.py), spec, example bundle, tests
apps/pac-reader/                  web reader: pac.js engine (same behaviour as pac.py), page, build, tests
tests/                            cross-checks between the reader and the Python engine
```

## Development

```sh
python -m pip install -e '.[dev]'
pytest                      # needs Node.js 18+ for the reader tests
node apps/pac-reader/build.mjs   # rebuild dist/pac-reader.html after changing the reader
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

Bundles are aids for reasoning about policies, not legal advice; the official policy text always
controls. The example policy is invented for demonstration and is not any real organisation's policy.

## License

[MIT](LICENSE)
