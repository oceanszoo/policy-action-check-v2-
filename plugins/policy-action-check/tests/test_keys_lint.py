"""Regression tests for format 2.0's text-anchored parse and term tree."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pac
from pac_keys import gate_witness, keys_diff, lint_keys, witness


def choice(name, *values, multi=False):
    return {
        "key": name,
        "name": name,
        "values": {v: v for v in values},
        "question": f"What is {name}?",
        "evidence": "Intake form",
        **({"multi": True} if multi else {}),
    }


def age_dimension():
    return {
        "key": "age",
        "type": "number",
        "unit": "years",
        "integer": True,
        "min": 0,
        "max": 150,
        "question": "What age in years is stated?",
        "evidence": "Intake form",
    }


def key(ident, dim, anchor, **compare):
    return {"id": ident, "dim": dim, "anchor": anchor, **compare}


@pytest.fixture
def docs():
    terms = {
        "clauses": [
            {"id": "d1", "class": "definition", "text": "Filed means stored in the ledger."},
            {"id": "c1", "class": "prohibition", "confidence": "high", "binds": "provider",
             "summary": "Audio recordings cannot be sent to people under EIGHTEEN years."},
            {"id": "c2", "class": "permission_exception", "confidence": "medium",
             "text": "The restriction does not apply to a teaching transcript.",
             "refs": [{"kind": "modifies", "to": "c1", "text": "does not apply"}]},
            {"id": "c3", "class": "obligation", "confidence": "high", "binds": "user",
             "text": "For audio recordings, file a record.",
             "refs": [{"kind": "uses_definition", "to": "d1", "text": "file"}]},
        ],
    }
    keys = {
        "dimensions": [choice("medium", "aud", "txt"), age_dimension(),
                       choice("edu", "yes", "no"), choice("filed", "yes", "no")],
        "terms": {
            "c1": {"role": "prohibition", "parents": [], "title": "Audio",
                   "binds": "provider", "next_step": "Do not send.",
                   "gate": [key("k1", "medium", "audio recordings", **{"in": ["aud"]}),
                            key("k2", "age", "under   eighteen YEARS", lt=18)]},
            "c2": {"role": "exception", "parents": ["c1"], "title": "Teaching",
                   "gate": [key("k1", "edu", "teaching transcript", **{"in": ["yes"]})]},
            "c3": {"role": "obligation", "parents": [], "title": "File",
                   "binds": "user", "next_step": "File the record.",
                   "gate": [key("k1", "medium", "audio recordings", **{"in": ["aud"]})],
                   "require": [key("r1", "filed", "stored in the ledger", **{"in": ["yes"]})]},
        },
    }
    return keys, terms


def test_summary_and_definition_anchors_coverage_and_warnings(docs):
    keys, terms = docs
    report = lint_keys(keys, terms, duty={"parties": ["user"]}, subjective=pac.DEFAULT_SUBJECTIVE)
    assert not report["errors"]
    assert report["metrics"] == {
        "terms_coverage": {"score": 1.0, "total": 3, "matched": 3},
        "key_anchors": {"score": 1.0, "total": 5, "matched": 5},
    }
    assert "dimensions edu and filed have the same value set" in report["warnings"]
    assert any("words outside key anchors:" in warning for warning in report["warnings"])
    assert any("shared with a term that binds the user" in warning for warning in report["warnings"])
    assert gate_witness(keys, "c2") == {"medium": "aud", "age": "0", "edu": "yes"}


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("anchor", "anchor not found"),
        ("link", "anchor not found"),
        ("dim", "unknown dimension"),
        ("value", "unknown values"),
        ("ids", "duplicate key id"),
        ("role", "role must be"),
        ("require", "obligation needs require"),
        ("omitted", "normative clause has no keys or not_encoded reason"),
        ("empty_disposition", "nonempty reason"),
        ("subjective", "subjective word"),
        ("empty_or", "any must be a nonempty"),
        ("units", "anchor unit does not match"),
        ("number", "number 19 not found in anchor"),
        ("parent", "missing parent"),
        ("exc_parent", "exception parents must equal"),
        ("cycle", "term tree cycle"),
        ("unsatisfiable", "child gate cannot be satisfied"),
        ("numeric_multi", "cannot be multi"),
        ("numeric_values", "number dimensions have no values"),
    ],
)
def test_lint_findings(docs, change, expected):
    keys, terms = docs
    c1, c2, c3 = (keys["terms"][cid] for cid in ("c1", "c2", "c3"))
    if change == "anchor":
        c1["gate"][0]["anchor"] = "not in the rule"
    elif change == "link":
        terms["clauses"][3]["refs"] = []
    elif change == "dim":
        c1["gate"][0]["dim"] = "missing"
    elif change == "value":
        c1["gate"][0]["in"] = ["missing"]
    elif change == "ids":
        c3["require"][0]["id"] = "k1"
    elif change == "role":
        c1["role"] = "scope"
    elif change == "require":
        c3["require"] = []
    elif change == "omitted":
        del keys["terms"]["c3"]
    elif change == "empty_disposition":
        del keys["terms"]["c3"]
        keys["not_encoded"] = [{"clause": "c3", "reason": " "}]
    elif change == "subjective":
        keys["dimensions"].append(choice("risky", "yes", "no"))
    elif change == "empty_or":
        c1["gate"][0] = {"id": "k1", "any": []}
    elif change == "units":
        keys["dimensions"][1]["unit"] = "days"
    elif change == "number":
        c1["gate"][1]["lt"] = 19
    elif change == "parent":
        c2["parents"] = ["missing"]
    elif change == "exc_parent":
        c2["parents"] = ["c3"]
    elif change == "cycle":
        c1["parents"] = ["c2"]
    elif change == "unsatisfiable":
        c2["gate"][0].update({"dim": "medium", "in": ["txt"]})
    elif change == "numeric_multi":
        keys["dimensions"][1]["multi"] = True
    elif change == "numeric_values":
        keys["dimensions"][1]["values"] = {"a": "10"}
    assert any(expected in m for m in lint_keys(keys, terms, subjective=pac.DEFAULT_SUBJECTIVE)["errors"])


def test_disposition_and_legacy_exception_parent(docs):
    keys, terms = docs
    c2 = terms["clauses"][2]
    c2.pop("refs")
    c2["modifies"] = "c1"
    del keys["terms"]["c3"]
    keys["not_encoded"] = [{"clause": "c3", "reason": "Needs human assessment."}]
    assert not lint_keys(keys, terms)["errors"]


def test_number_words_between_and_stated_hard_bounds(docs):
    keys, terms = docs
    c1 = terms["clauses"][1]
    c1["summary"] = "Audio recordings involving people between five and eighteen years."
    leaf = key("k2", "age", "between five and eighteen years", between=[5, 18])
    keys["terms"]["c1"]["gate"][1] = leaf
    assert not lint_keys(keys, terms)["errors"]
    assert gate_witness(keys, "c1") == {"medium": "aud", "age": "5"}
    leaf.update({"preset": 5, "why": "stated"})
    assert not lint_keys(keys, terms)["errors"]
    leaf["preset"] = 151
    assert any("invalid numeric preset" in issue for issue in lint_keys(keys, terms)["errors"])


def test_tree_accepts_one_parent_path_and_any_with_multi_choices(docs):
    keys, terms = docs
    keys["dimensions"][0]["multi"] = True
    c2 = keys["terms"]["c2"]
    c2["parents"].append("c3")
    terms["clauses"][2]["refs"].append({"kind": "modifies", "to": "c3"})
    c2["gate"] = [{"id": "k1", "any": [
        {"dim": "medium", "in": ["txt"], "anchor": "teaching transcript"},
        {"dim": "age", "ge": 18, "anchor": "eighteen years"},
    ]}]
    terms["clauses"][2]["text"] += " This applies from eighteen years."
    keys["terms"]["c1"]["gate"].append(
        key("k3", "medium", "audio recordings", not_in=["txt"])
    )
    assert not lint_keys(keys, terms)["errors"]
    assert gate_witness(keys, "c2") == {"medium": "aud+txt"}


def test_subject_to_unlinked_parent_warning(docs):
    keys, terms = docs
    terms["clauses"][3]["refs"].append({"kind": "subject_to", "to": "c1"})
    report = lint_keys(keys, terms)
    assert not report["errors"]
    assert any("c3: possible parent relation to c1" in issue for issue in report["warnings"])


def test_number_witness_detects_disjoint_open_intervals():
    dims = {"age": age_dimension()}
    leaves = [{"dim": "age", "gt": 17}, {"dim": "age", "lt": 18}]
    assert witness(leaves, dims) is None
    dims["age"]["integer"] = False
    assert witness(leaves, dims) == {"age": "17.5"}


def test_keys_diff_canonicalizes_ids_order_and_values(docs):
    keys, _ = docs
    first = keys["terms"]["c1"]
    first["gate"].append({"id": "k3", "any": [
        {"dim": "medium", "in": ["aud", "txt"], "anchor": "audio recordings"},
        {"dim": "edu", "not_in": ["no"], "anchor": "something else"},
    ]})
    second = copy.deepcopy(keys)
    reordered = second["terms"]["c1"]
    reordered["gate"].reverse()
    reorder_or = reordered["gate"][0]
    reorder_or.update({"id": "new-id", "any": list(reversed(reorder_or["any"]))})
    reorder_or["any"][1]["in"].reverse()
    reordered["gate"][1].update({"lt": 18.0, "anchor": "another anchor"})
    assert keys_diff(keys, second) == {"score": 1, "total": 3, "matched": 3, "differences": []}
    reordered["gate"][1]["lt"] = 17
    del second["terms"]["c3"]
    report = keys_diff(keys, second)
    assert report["score"] == 1 / 3
    assert [d["term"] for d in report["differences"]] == ["c1", "c3"]
    assert report["differences"][1]["b"] is None


def test_short_number_anchor_can_detect_a_unit_stated_next_to_it(docs):
    keys, terms = docs
    keys["terms"]["c1"]["gate"][1]["anchor"] = "under eighteen"
    assert not lint_keys(keys, terms)["errors"]
    terms["clauses"][1]["summary"] = terms["clauses"][1]["summary"].replace("years", "months")
    assert any("unit does not match" in issue for issue in lint_keys(keys, terms)["errors"])


def test_cli_lint_and_diff(docs, tmp_path, capsys):
    keys, terms = docs
    work = tmp_path / "work"
    work.mkdir()
    a, b = work / "keys.json", work / "keys-b.json"
    a.write_text(json.dumps(keys), encoding="utf-8")
    (work / "terms.json").write_text(json.dumps(terms), encoding="utf-8")
    assert pac.main(["--space", str(tmp_path), "keys-lint"]) == 0
    assert json.loads(capsys.readouterr().out)["errors"] == []
    keys["terms"]["c1"]["gate"][1]["lt"] = 17
    b.write_text(json.dumps(keys), encoding="utf-8")
    assert pac.main(["--space", str(tmp_path), "keys-lint", "--keys", str(b)]) == 1
    bad = json.loads(capsys.readouterr().out)
    assert any("number 17 not found" in issue for issue in bad["errors"])
    assert pac.main(["--space", str(tmp_path), "keys-diff", str(a), str(b)]) == 0
    diff = json.loads(capsys.readouterr().out)
    assert diff["matched"] == 2 and diff["differences"][0]["term"] == "c1"
