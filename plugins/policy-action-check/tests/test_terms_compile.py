"""Compiled format 2.0 bundles behave deterministically from their source keys."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pac


def write(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


@pytest.fixture
def terms_first(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    clauses = [
        {"id": "c1", "class": "condition_scope", "confidence": "high",
         "section": "Delivery", "text": "These restrictions apply when sending a file."},
        {"id": "c2", "class": "prohibition", "confidence": "high",
         "section": "Delivery", "binds": "deployer", "text": "Do not send to anyone under 18 years."},
        {"id": "c3", "class": "permission_exception", "confidence": "high",
         "section": "Delivery", "text": "The age restriction does not apply with recorded permission.",
         "refs": [{"kind": "modifies", "to": "c2", "text": "does not apply"}]},
        {"id": "c4", "class": "obligation", "confidence": "high",
         "section": "Records", "binds": "provider",
         "summary": "When a record exists, retain it for no longer than 30.5 days."},
    ]

    def dim(key, values=None, **extras):
        return {
            "key": key, "question": f"What is {key}?", "evidence": "Intake records",
            **({"values": values} if values else {}), **extras,
        }

    def term(role, title, gate, parents=(), **extras):
        return {
            "role": role, "title": title, "gate": gate, "parents": list(parents),
            **extras,
        }

    keys = {
        "dimensions": [
            dim("act", {"send": "send a file", "store": "store a file"}, fixable=False),
            dim("age", type="number", unit="years", integer=True, min=0, max=150),
            dim("permit", {"yes": "permission recorded", "no": "permission not recorded"}),
            dim("record", {"yes": "record exists", "no": "no record"}, fixable=False),
            dim("ret", type="number", unit="days", min=0, max=365, default="10", fixable=True),
        ],
        "terms": {
            "c1": term("scope", "Sending files",
                       [{"id": "k1", "dim": "act", "in": ["send"], "anchor": "sending a file"}]),
            "c2": term("prohibition", "Minimum age",
                       [{"id": "k1", "dim": "age", "lt": 18, "anchor": "under 18 years"}],
                       ("c1",), binds="deployer", next_step="Do not send the file."),
            "c3": term("exception", "Recorded permission",
                       [{"id": "k1", "dim": "permit", "in": ["yes"], "anchor": "recorded permission"}],
                       ("c2",)),
            "c4": term("obligation", "Record retention",
                       [{"id": "k1", "dim": "record", "in": ["yes"], "anchor": "a record exists"}],
                       binds="provider", next_step="Shorten the record retention.",
                       require=[{"id": "r1", "dim": "ret", "le": 30.5, "anchor": "30.5 days"}]),
        },
    }
    # A typed numeric default is the JSON value; its action-code representation is a string.
    keys["dimensions"][-1]["default"] = 10
    write(work / "keys.json", keys)
    write(work / "terms.json", {"source": "Synthetic Terms", "clauses": clauses})
    write(work / "scope.json", {"duty": {"parties": ["deployer"]}})
    return tmp_path


def compile_space(root):
    report = pac.compile_bundle(root)
    assert report["rules"] == 2
    assert report["dimensions"] == 5
    return pac.Space(root)


def test_compile_emits_term_map_rules_and_boundary_vectors(terms_first):
    sp = compile_space(terms_first)
    assert sp.generator["version"] == sp.judge["version"] == "2.0"
    assert sp.judge["semantics"] == "kleene-3v-2"
    assert "categories" not in sp.generator and "ask_order" not in sp.generator
    assert sp.generator["order"] == "map"
    tmap = sp.generator["term_map"]
    assert tmap["sections"] == [
        {"name": "Delivery", "terms": ["c1"]},
        {"name": "Records", "terms": ["c4"]},
    ]
    assert tmap["nodes"]["c1"]["children"] == ["c2"]
    assert tmap["nodes"]["c2"]["parents"] == ["c1"]
    assert tmap["nodes"]["c3"]["parents"] == ["c2"]
    assert tmap["nodes"]["c2"]["keys"] == [{"id": "k1", "role": "gate", "dim": "age", "lt": 18}]
    restriction, retention = sp.judge["rules"]
    assert restriction["id"] == "T-c2"
    assert restriction["term"] == "c2"
    assert restriction["source_terms"] == ["c1", "c2", "c3"]
    assert restriction["exceptions"][0]["source_terms"] == ["c3"]
    assert retention["source_terms"] == ["c4"]
    assert sp.judge["terms"]["c4"]["summary"].endswith("30.5 days.")
    assert "text" not in sp.judge["terms"]["c4"]
    assert {"phrase": "sending a file", "token": "act=send"} in sp.generator["lexicon"]
    vectors = [
        json.loads(line)
        for line in (terms_first / "conformance.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all(any(f"age={v}" in row["code"] for row in vectors) for v in (17, 18, 19))
    assert all(any(f"ret={v}" in row["code"] for row in vectors) for v in (30.49, 30.5, 30.51))
    for row in vectors:
        result = pac.check(row["code"], sp)
        assert row["expected"] == {key: result[key] for key in row["expected"]}


def test_numbers_strict_tokens_inclusive_comparison_and_parent_drop(terms_first):
    sp = compile_space(terms_first)
    assert pac.check("act=send age=17 permit=no record=no", sp)["violated"] == ["T-c2"]
    assert pac.check("act=send age=18 record=no", sp)["verdict"] == "compliant"
    assert pac.check("act=send age=17 permit=yes record=no", sp)["verdict"] == "compliant"
    assert pac.check("act=send age=? record=no", sp)["verdict"] == "needs_info"
    parsed = pac.check("act=send age=017.00 permit=yes record=yes ret=030.500", sp)
    assert set(parsed["code"].split()) == {"act=send", "age=17", "permit=yes", "record=yes", "ret=30.5"}
    for token in ("age=151", "age=-1", "age=17.5", "age=teen", "age=1e1", "act=17"):
        assert pac.check(token, sp)["verdict"] == "invalid_code"
    pending = pac.check("act=send record=no permit=no", sp)
    assert pending["features"]["permit"] == "no"
    assert "dropped" not in pending
    assert "Establish permit" not in pac.render_report(pending, sp)

    moved = pac.check("act=store age=17 permit=yes record=no", sp)
    assert moved["verdict"] == "compliant"
    assert moved["features"] == {"act": "store", "record": "no"}
    assert moved["dropped"] == [
        {"key": "age", "value": "17", "because": ["c2"]},
        {"key": "permit", "value": "yes", "because": ["c3"]},
    ]
    assert "Not used: `permit=yes`, because Recorded permission (c3) doesn't apply." in (
        pac.render_report(moved, sp)
    )
    assert pac.fit_detail({"act": "store", "age": "17", "permit": "yes"}, sp)["dropped"] == [
        "age", "permit",
    ]


def test_example_keeps_unknown_scope_fact_until_parent_is_ruled_out():
    sp = pac.Space(ROOT / "examples" / "sample-service-terms")
    pending = pac.check("fic=y", sp)
    assert pending["code"] == "fic=y"
    assert pending["verdict"] == "needs_info"
    assert "dropped" not in pending
    ruled_out = pac.check("pur=std fic=y", sp)
    assert ruled_out["code"] == "pur=std"
    assert ruled_out["dropped"] == [{"key": "fic", "value": "y", "because": ["c012"]}]
    assert "Not used: `fic=y`, because " in pac.render_report(ruled_out, sp)


def test_any_possible_parent_path_keeps_a_fact(terms_first):
    sp = compile_space(terms_first)
    nodes = sp.generator["term_map"]["nodes"]
    nodes["c3"]["parents"].append("c4")
    nodes["c4"]["children"].append("c3")
    # The c2 path is false, but c4 can still open. An answered no on c3's own
    # gate is evidence, not authorization to discard it.
    pending = pac.check("act=store permit=no", sp)
    assert pending["features"]["permit"] == "no"
    assert "c3" not in pac.term_map_state(pending["features"], sp)[0]
    assert pac.check("act=store record=yes permit=no", sp)["features"]["permit"] == "no"
    assert pac.check("act=store record=no permit=no", sp)["dropped"] == [
        {"key": "permit", "value": "no", "because": ["c3"]},
    ]


def test_duty_preset_order_override_report_and_nearest_fix(terms_first):
    sp = compile_space(terms_first)
    mapped = sp.generator["term_map"]["nodes"]["c4"]["keys"][-1]
    assert mapped == {
        "id": "r1", "role": "require", "dim": "ret", "le": 30.5,
        "preset": "30.5", "why": "duty", "binds": "provider",
    }
    relied = pac.check("act=store record=yes", sp)
    assert relied["verdict"] == "compliant"
    assert next(fact for fact in relied["facts"] if fact["key"] == "ret") == {
        "key": "ret", "value": "30.5", "from": "preset", "assumed": True,
        "why": "duty", "binds": "provider", "term": "c4",
    }
    assert "`ret=30.5` (pre-selected: provider's duty, c4)" in pac.render_report(relied, sp)
    stated = {**relied, "facts": [{**fact, "why": "stated"} if fact["key"] == "ret" else fact
                                 for fact in relied["facts"]]}
    assert "`ret=30.5` (pre-selected: stated in c4)" in pac.render_report(stated, sp)
    assert "Relies on provider meeting Record retention (c4)" in pac.render_report(relied, sp)
    unknown = pac.check("act=store record=yes ret=?", sp)
    assert unknown["verdict"] == "compliant_if_requirements_met"
    assert next(fact for fact in unknown["facts"] if fact["key"] == "ret")["value"] == "?"
    contradicted = pac.check("act=store record=yes ret=31", sp)
    assert contradicted["violated"] == ["T-c4"]
    assert contradicted["fix"] == [["ret=31 -> ret=30.5"]]
    assert unknown["fix"] == [["ret=? -> ret=30.5"]]

    sp.generator["constants"]["ret"] = "32"
    constant = pac.check("act=store record=yes", sp)
    assert constant["violated"] == ["T-c4"]
    assert not constant["fix"]
    fact = next(fact for fact in constant["facts"] if fact["key"] == "ret")
    assert (fact["from"], fact["value"]) == ("constant", "32")
    assert pac.check("act=store record=yes ret=30", sp)["verdict"] == "compliant"


def test_compile_rejects_missing_anchor(terms_first):
    path = terms_first / "work" / "keys.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["terms"]["c2"]["gate"][0]["anchor"] = "fictional wording"
    write(path, data)
    with pytest.raises(pac.SpaceError, match="anchor not found"):
        pac.compile_bundle(terms_first)
    assert not (terms_first / "judge.json").exists()
