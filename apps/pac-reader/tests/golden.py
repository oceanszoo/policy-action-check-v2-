"""Dump reference outputs of pac.py for one bundle, for the JS parity test (stdout: JSON)."""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins" / "policy-action-check" / "scripts"))
import pac

DATE = "2026-11-19"


def main() -> None:
    root = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    sp = pac.Space(root)
    codes = [x["code"] for x in pac._conformance(root)] + pac._sample_codes(sp, n, seed=7)
    rng = random.Random(3)
    keys = list(sp.dims)
    first_choices = list(sp.dims[keys[0]].get("values", {}))
    def first_value():
        return rng.choice(first_choices) if first_choices else "?"

    codes += [f"{keys[0]}={first_value()} {k}=zz{k[:2]}" for k in keys[:5]]  # typos
    codes += [f"risk=low {keys[min(1, len(keys) - 1)]}=?", "unknownkey=1", "@nosuchcode", f"step1: {codes[0]}"]
    codes += [f"{codes[i]} > {codes[i + 1]}" for i in range(0, min(10, len(codes) - 1), 2)]
    codes += [f"{codes[i]} & {codes[i + 1]}" for i in range(1, min(11, len(codes) - 1), 2)]  # 1.4: same time
    codes += [f"{codes[i]} & {codes[i + 1]} > {codes[i + 2]}" for i in range(2, min(12, len(codes) - 2), 3)]
    # Keep the historical 1.x test date; 2.0 rules may be effective after it.
    day = DATE
    if sp.is_terms_first():
        day = max((r.get("effective_from") or DATE for r in sp.rules["rules"]), default=DATE)
    checks = [{"code": c, "out": pac.check_flow(c, sp, day, {"_action": "n", keys[0]: " x "})} for c in codes]
    reports = [{"code": c["code"], "text": pac.render_report(c["out"], sp)} for c in checks[:60] + checks[-20:]]
    forms = []
    for code in pac._sample_codes(sp, max(20, n // 4), seed=11):
        feats = pac.parse_code(code, sp)["features"]
        answers, seq = [], []
        for _ in range(len(sp.dims) + 1):
            q = pac.next_question(" ".join(answers), sp, day)
            seq.append(q)
            if q.get("done"):
                break
            answers.append(f"{q['key']}={feats.get(q['key'], '?')}")
        forms.append({"code": code, "seq": seq})
    texts = [" ".join(e["phrase"] for e in sp.generator.get("lexicon", [])[i:i + 4]) for i in range(0, 40, 4)]
    lookups = [{"text": t, "out": pac.lookup(t, sp)} for t in texts + ["Nothing relevant HERE."]]
    manifest = pac._read_json(root / "bundle.json", {})
    files = pac._bundle_bytes(root, (*pac._BUNDLE_FILES, "BUNDLE.md"))
    crlf = {name: data.replace(b"\n", b"\r\n") for name, data in files.items()}
    edited = {**crlf, "generator.json": crlf["generator.json"] + b" "}
    verification = {label: pac.verify_manifest(manifest, inputs)
                    for label, inputs in (("exact", files), ("crlf", crlf), ("edited", edited))}
    fits = []
    for c in checks:
        if "features" not in c["out"]:
            continue
        # For 2.0, check() prunes hidden child keys. Test fit on the original input
        # instead, so its dropped-key diagnostics are compared too.
        feats = pac.parse_code(c["code"], sp)["features"]
        fits.append({"code": c["code"], "fit": pac.map_fit(feats, sp, day),
                     "detail": pac.fit_detail(feats, sp, day)})
    json.dump({"verification": verification, "date": day, "checks": checks, "reports": reports, "forms": forms,
               "lookups": lookups, "categories": pac.categories(sp), "fits": fits},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
