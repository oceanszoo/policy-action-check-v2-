"""Format 2.0 exam and history remain separate deterministic operations."""

import json

from test_terms_compile import compile_space, pac, write
from test_terms_compile import terms_first as _terms_first

terms_first = _terms_first


def test_compile_does_not_use_history_and_evaluate_does_not_write_rules(terms_first):
    sp = compile_space(terms_first)
    work = terms_first / "work"
    paths = [terms_first / name for name in ("generator.json", "judge.json", "conformance.jsonl")]
    frozen = [path.read_bytes() for path in paths]
    history = work / "history_encoded.jsonl"
    rows = [
        {"id": "yes", "code": "act=send age=17 permit=no record=no", "outcome": "block"},
        {"id": "missing", "code": "extra=x", "outcome": "unknown"},
    ]
    history.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    write(work / "outcome_map.json", {"block": "violates"})
    sp = compile_space(terms_first)
    assert set(sp.dims) == {"act", "age", "permit", "record", "ret"}
    assert [path.read_bytes() for path in paths] == frozen
    evaluated = pac.evaluate_history(terms_first, history)
    assert evaluated["replay_agreement"] == {"agreed": 1, "mapped": 1, "score": 1}
    assert evaluated["missing_dimensions"] == [{"record": "missing", "dimensions": ["extra"]}]
    assert json.loads((work / "eval.json").read_text(encoding="utf-8")) == evaluated
    assert [path.read_bytes() for path in paths] == frozen


def test_exam_keeps_history_off_badge_and_checks_numeric_mutants(terms_first, capsys):
    work = terms_first / "work"
    first = work / "keys.json"
    second = work / "keys-parse-b.json"
    other = json.loads(first.read_text(encoding="utf-8"))
    other["terms"]["c2"]["gate"][0]["id"] = "other-parser-id"
    write(second, other)
    assert pac.main([
        "--space", str(terms_first), "keys-diff", str(first), str(second), "--write",
    ]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 1.0
    sp = compile_space(terms_first)
    assert pac._numeric_bounds(sp, "age")[0] == 18
    possibilities = pac.check("act=send age=? record=no", sp)["possible"]
    assert possibilities
    assert any("age" in region.get("when", "") for region in possibilities)
    rule = sp.judge["rules"][0]
    mutants = list(pac._mutants(rule, sp=sp))
    assert any("parent" in name for name, _ in mutants)
    assert any("age" in name and "bound" in name for name, _ in mutants)
    report = pac.exam(terms_first)
    checks = {check["id"]: check for check in report["checks"]}
    assert checks["validate"]["passed"], checks["validate"]
    for check in ("terms_coverage", "key_anchors", "key_agreement", "map_reach"):
        assert checks[check]["passed"], checks[check]
    for omitted in ("map_fit", "replay_agreement", "replay_decisive"):
        assert omitted not in checks
    assert checks["map_reach"]["score"] == 1.0
    assert not checks["key_agreement"]["skipped"]
    assert checks["key_agreement"]["score"] == 1.0
    assert checks["key_agreement"]["threshold"] == 0.8

    write(work / "key_agreement.json", {"single_parse": True})
    compile_space(terms_first)
    single = {c["id"]: c for c in pac.exam(terms_first)["checks"]}["key_agreement"]
    assert single["skipped"]
    assert single["score"] is None
    assert "single parse requested" in single["detail"]


def test_refine_requires_source_anchor_and_recompiles(terms_first):
    import hashlib

    import pytest

    compile_space(terms_first)
    work = terms_first / "work"
    paths = [terms_first / name for name in ("generator.json", "judge.json", "conformance.jsonl")]
    frozen = [path.read_bytes() for path in paths]
    history = work / "history_encoded.jsonl"
    history.write_text('{"id":"old","code":"record=yes ret=45","outcome":"allow"}\n', encoding="utf-8")
    write(work / "outcome_map.json", {"allow": "compliant"})
    pac.evaluate_history(terms_first, history)
    gaps = pac.gaps(terms_first, "retention", write=True)
    replay = next(g for g in gaps["gaps"] if g["kind"] == "replay_disagreement")
    op = {"op": "revise_key", "term": "c4", "part": "require",
          "key": {"id": "r1", "dim": "ret", "le": 30.5, "anchor": "invented 30.5 days"},
          "reason": "Choose the most precise source wording.", "gaps": [replay["id"]]}
    patch = {"based_on": hashlib.sha256((work / "gaps.json").read_bytes()).hexdigest(),
             "focus": "retention", "ops": [op]}
    write(work / "refine_patch.json", patch)
    with pytest.raises(pac.SpaceError, match="anchor"):
        pac.apply_patch(terms_first)
    assert [path.read_bytes() for path in paths] == frozen
    op["key"]["anchor"] = "no longer than 30.5 days"
    write(work / "refine_patch.json", patch)
    assert "judge.json" in pac.apply_patch(terms_first, dry_run=True)["files"]
    assert [path.read_bytes() for path in paths] == frozen


def test_evaluate_judges_all_actions_in_a_history_flow(terms_first):
    compile_space(terms_first)
    work = terms_first / "work"
    history = work / "history_encoded.jsonl"
    code = "act=store record=no & act=send age=17 permit=no record=no > act=store record=no"
    row = {"id": "flow", "code": code, "outcome": "block"}
    history.write_text(json.dumps(row) + "\n", encoding="utf-8")
    write(work / "outcome_map.json", {"block": "violates"})
    report = pac.evaluate_history(terms_first, history)
    assert report["judged"] == 1
    assert report["replay_agreement"]["agreed"] == 1
    assert report["map_misses"] == []
    assert [decision["category"] for decision in report["replay"][0]["map_fit"]["actions"]] == ["c1"] * 3
