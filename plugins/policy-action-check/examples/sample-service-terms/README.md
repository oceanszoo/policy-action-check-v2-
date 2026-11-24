# Example bundle: Sample Service Terms (invented)

Open [BUNDLE.md](BUNDLE.md) for the terms map, features, rules and self-exam.
`generator.json` and `judge.json` run the bundle without a model. `conformance.jsonl`
checks that readers reproduce the compiled results. No historical records were
used to build this example.

"Sample Service Terms" is an invented policy written for this repository; it is not
any real organisation's policy, and `https://example.com/sample-service-terms` is a
placeholder address. Most terms are stored as a short `summary` and are shown as
“Summary (not a quote).”

The keys were written as a single parse, so the self-exam reports key agreement as
not measured. Three definitions inform the keys but do not become rules, and two
exceptions are recorded as `not_encoded` with a reason.

Try it:

```sh
python3 scripts/pac.py --space examples/sample-service-terms map
python3 scripts/pac.py --space examples/sample-service-terms report "pur=data cons=n"
python3 scripts/pac.py --space examples/sample-service-terms report "pur=grooming age=17"
```
