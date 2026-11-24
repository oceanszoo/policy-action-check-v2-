"""Deterministic checks for the term filter's cross-reference graph."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pac


@pytest.fixture
def terms(tmp_path):
    doc = {
        "source": "Example Policy",
        "glossary": [
            {"term": "High-Risk Use Case", "defined_in": "c1", "aliases": ["elevated use"]},
        ],
        "clauses": [
            {
                "id": "c1", "class": "definition",
                "text": "High-Risk Use Case means a decision affecting access to an essential service.",
            },
            {
                "id": "c2", "class": "prohibition", "confidence": "high",
                "text": "Do not automate a HIGH-RISK   USE CASE without review.",
                "refs": [{"to": "c1", "kind": "uses_definition", "text": "High-Risk Use Case"}],
            },
            {
                "id": "c3", "class": "permission_exception", "confidence": "high",
                "text": "This restriction does not apply to wholly favorable decisions.",
                "refs": [{"to": "c2", "kind": "modifies", "text": "does not apply"}],
            },
            {
                "id": "c4", "class": "obligation", "confidence": "high",
                "text": "Document any of the restricted uses listed above.",
                "refs": [{"to": "c2", "kind": "incorporates", "text": "restricted uses listed above"}],
            },
            {
                "id": "c5", "class": "condition_scope", "confidence": "high",
                "text": "Access is subject to the Commercial Terms.",
                "refs": [
                    {"to": None, "kind": "subject_to", "text": "subject to the Commercial Terms",
                     "external": "Commercial Terms"},
                ],
            },
        ],
    }
    (tmp_path / "work").mkdir()
    _write(tmp_path, doc)
    return tmp_path, doc


def _write(root, doc):
    (root / "work" / "terms.json").write_text(json.dumps(doc), encoding="utf-8")


def _find(doc, cid):
    return next(c for c in doc["clauses"] if c["id"] == cid)


def test_terms_lint_and_filter_stage(terms, capsys):
    root, _ = terms
    assert pac.main(["--space", str(root), "terms-lint"]) == 0
    lint = json.loads(capsys.readouterr().out)
    assert lint["errors"] == []
    assert lint["warnings"] == [
        "c5: unresolved ref 'subject to the Commercial Terms': Commercial Terms",
    ]
    assert pac.main(["--space", str(root), "validate", "--stage", "filter"]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True, **lint}


@pytest.mark.parametrize(
    "change,expected",
    [
        ("missing-definition-link", "missing uses_definition ref to c1"),
        ("missing-alias-link", "missing uses_definition ref to c1"),
        ("missing-signal-link", "unlinked reference phrase 'notwithstanding'"),
        ("dangling", "incorporates unknown clause c99"),
        ("wrong-text", "ref text not found in clause"),
        ("cycle", "incorporates cycle: c1 -> c4 -> c2 -> c1"),
        ("not-a-definition", "defined_in c2 is not a known definition clause"),
        ("unknown-definition", "defined_in c99 is not a known definition clause"),
        ("no-resolution", "unresolved ref needs external or reason"),
        ("no-waiver-reason", "ref kind none needs a reason"),
    ],
)
def test_terms_lint_errors(terms, change, expected, capsys):
    root, doc = terms
    c1, c2, c4, c5 = (_find(doc, cid) for cid in ("c1", "c2", "c4", "c5"))
    if change in ("missing-definition-link", "missing-alias-link"):
        c2["refs"].clear()
        if change == "missing-alias-link":
            c2["text"] = "Do not automate an elevated use without review."
    elif change == "missing-signal-link":
        c2["text"] += " Notwithstanding review delays, notify the customer."
    elif change == "dangling":
        c4["refs"][0]["to"] = "c99"
    elif change == "wrong-text":
        c2["refs"][0]["text"] = "A different term"
    elif change == "cycle":
        c1["refs"] = [{"to": "c4", "kind": "incorporates", "text": "essential service"}]
        c2["refs"].append({"to": "c1", "kind": "incorporates", "text": "without review"})
    elif change in ("not-a-definition", "unknown-definition"):
        doc["glossary"][0]["defined_in"] = "c2" if change == "not-a-definition" else "c99"
    elif change == "no-resolution":
        del c5["refs"][0]["external"]
    elif change == "no-waiver-reason":
        c5["refs"][0]["kind"] = "none"
    _write(root, doc)
    assert pac.main(["--space", str(root), "terms-lint"]) == 1
    errors = json.loads(capsys.readouterr().out)["errors"]
    assert any(expected in error for error in errors)
    assert pac.validate(root, "filter") == errors


def test_lint_warnings_and_signal_waiver(terms):
    root, doc = terms
    c2, c3, c4, c5 = (_find(doc, cid) for cid in ("c2", "c3", "c4", "c5"))
    c2["text"] = 'Do not automate decisions in the "Special Review Queue".'
    c2["refs"].clear()
    c3["text"] += " Label the outcome Special Review Queue."
    c4["text"] += " Place the log below the header."
    c4["refs"].append({
        "to": None, "kind": "none", "text": "below", "reason": "Refers to a location, not a clause.",
    })
    c5["refs"][0] = {
        "to": None, "kind": "subject_to", "text": "subject to the Commercial Terms",
        "reason": "Referenced document not supplied.",
    }
    _write(root, doc)
    lint = pac.terms_lint(root)
    assert lint["errors"] == []
    assert any("orphan definition 'High-Risk Use Case'" in w for w in lint["warnings"])
    assert "concept without a page: 'Special Review Queue' (c2, c3)" in lint["warnings"]
    assert any("Referenced document not supplied." in w for w in lint["warnings"])
    assert not any("below" in w for w in lint["warnings"])
    assert pac.terms_context(root, "c4")["unresolved"] == []


def test_context_has_definitions_through_refs_and_exceptions_through_backlinks(terms, capsys):
    root, _ = terms
    assert pac.main(["--space", str(root), "terms-context", "c4"]) == 0
    data = json.loads(capsys.readouterr().out)
    entries = {item["clause"]["id"]: item for item in data["clauses"]}
    assert data["clause"] == "c4"
    assert entries["c4"]["path"] == "c4"
    assert entries["c2"]["path"] == "c4 -incorporates-> c2"
    assert entries["c1"]["path"] == "c4 -incorporates-> c2 -uses_definition-> c1"
    assert entries["c3"]["path"] == "c4 -incorporates-> c2 <-modifies- c3"
    assert entries["c2"]["backlinks"] == [
        {"clause": "c3", "kind": "modifies", "text": "does not apply"},
        {"clause": "c4", "kind": "incorporates", "text": "restricted uses listed above"},
    ]
    assert data["unresolved"] == []
    missing = pac.terms_context(root, "c5")["unresolved"]
    assert missing[0]["ref"]["external"] == "Commercial Terms"


def test_legacy_modifies_and_no_new_lint_for_legacy_terms(terms):
    root, doc = terms
    del doc["glossary"]
    for clause in doc["clauses"]:
        clause.pop("refs", None)
    c3 = _find(doc, "c3")
    c3["modifies"] = "c2"
    _write(root, doc)
    assert pac.terms_lint(root) == {"errors": [], "warnings": []}
    assert pac.terms_context(root, "c3")["clauses"][1]["path"] == "c3 -modifies-> c2"
    assert pac.terms_context(root, "c2")["clauses"][1]["path"] == "c2 <-modifies- c3"
    c3["modifies"] = "not-a-clause"
    _write(root, doc)
    assert pac.validate(root, "filter") == ["c3: modifies unknown clause not-a-clause"]


def test_glossary_requires_whole_words_and_accepts_case_and_whitespace(terms):
    root, doc = terms
    c2 = _find(doc, "c2")
    c2["text"] = "Do not automate elevated users without review."
    c2["refs"].clear()
    _write(root, doc)
    assert pac.terms_lint(root)["errors"] == []
    c2["text"] = "Do not automate an ELEVATED\n\tUSE without review."
    c2["refs"] = [{"to": "c1", "kind": "uses_definition", "text": "elevated use"}]
    _write(root, doc)
    assert pac.terms_lint(root)["errors"] == []
