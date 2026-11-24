"""Reference coverage is deterministic and independent of the judgment engine."""

import json
import shutil
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import pac


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def clause(ident, cls, text, **kw):
    return {"id": ident, "class": cls, "confidence": "high", "section": "Example", "text": text, **kw}


def ref(target, kind, text, **kw):
    return {"to": target, "kind": kind, "text": text, **kw}


@pytest.fixture
def bundle(tmp_path):
    example = PLUGIN.parents[1] / "apps/pac-reader/tests/fixtures/legacy"
    root = tmp_path / "space"
    shutil.copytree(example, root, ignore=shutil.ignore_patterns("work"))
    judge = json.loads((root / "judge.json").read_text(encoding="utf-8"))
    rule = next(r for r in judge["rules"] if r["id"] == "P-privacy")
    rule["source_terms"] = ["c2"]
    clauses = [
        clause("c1", "definition", "High-Risk Use Case means a case with a direct material effect."),
        clause("c2", "prohibition", "Do not disclose a record in a High-Risk Use Case.",
               refs=[ref("c1", "uses_definition", "High-Risk Use Case")]),
        clause("c3", "permission_exception", "Do not apply the disclosure ban to approved summaries.",
               refs=[ref("c2", "modifies", "the disclosure ban")]),
        clause("c4", "prohibition", "Forwarding is covered by the same limit above.",
               refs=[ref("c2", "incorporates", "the same limit above")]),
        clause("c5", "condition_scope", "Release is subject to the Commercial Terms.",
               refs=[ref(None, "subject_to", "subject to the Commercial Terms", external="Commercial Terms")]),
    ]
    terms = {"clauses": clauses, "glossary": [{"term": "High-Risk Use Case", "defined_in": "c1"}]}
    write(root / "work/terms.json", terms)
    write(root / "judge.json", judge)
    return root, terms, judge, rule


def exam(root):
    return pac.exam_references(root, pac.Space(root), pac.EXAM_THRESHOLDS)


def test_uncited_backlink_is_a_gap_after_uncovered_clauses(bundle):
    root, _, _, _ = bundle
    check = exam(root)
    assert check["threshold"] == 1.0
    assert not check["passed"]
    assert check["score"] == 0
    assert check["failure_count"] == 1
    assert "c3" in check["failures"][0]
    items = pac.gaps(root, check_manifest=False)["gaps"]
    references = [item for item in items if item["kind"] == "unresolved_reference"]
    assert len(references) == 1
    item = references[0]
    assert item["evidence"] == {
        "rule": "P-privacy", "clause": "c2", "linked_clause": "c3",
        "kind": "modifies", "phrase": "the disclosure ban",
    }
    space = pac.Space(root)
    rule = next(r for r in space.rules["rules"] if r["id"] == "P-privacy")
    assert set(item["keys"]) == set(pac.rule_dims(rule))
    assert all(items.index(i) < items.index(item) for i in items if i["kind"] == "uncovered_clause")


@pytest.mark.parametrize("disposition", ["cited", "not_encoded"])
def test_backlink_accounted_for_and_definitions_not_required(bundle, disposition):
    root, _, judge, rule = bundle
    if disposition == "cited":
        rule["source_terms"].append("c3")
    else:
        judge["not_encoded"] = [{"clause": "c3", "reason": "Handled in a separate system"}]
    write(root / "judge.json", judge)
    check = exam(root)
    assert check["passed"] and check["score"] == 1.0
    assert check["failures"] == []


@pytest.mark.parametrize("kind", ["incorporates", "overrides", "subject_to"])
def test_cited_clauses_must_account_for_outgoing_links(bundle, kind):
    root, terms, judge, rule = bundle
    rule["source_terms"] = ["c4"]
    terms["clauses"][3]["refs"][0]["kind"] = kind
    write(root / "judge.json", judge)
    write(root / "work/terms.json", terms)
    assert not exam(root)["passed"]
    judge["not_encoded"] = [{"clause": "c2", "reason": "Out of scope"}]
    write(root / "judge.json", judge)
    assert exam(root)["passed"]


@pytest.mark.parametrize("kind", ["overrides", "subject_to"])
def test_other_backlinks_are_accounted_for(bundle, kind):
    root, terms, judge, rule = bundle
    rule["source_terms"] = ["c2", "c3"]
    terms["clauses"][3]["refs"][0]["kind"] = kind
    write(root / "judge.json", judge)
    write(root / "work/terms.json", terms)
    assert "c4" in exam(root)["failures"][0]


def test_unresolved_reference_needs_its_own_reason(bundle):
    root, _, judge, rule = bundle
    rule["source_terms"] = ["c5"]
    write(root / "judge.json", judge)
    assert not exam(root)["passed"]
    for waiver in [
        {"clause": "c5", "ref": "subject to the Commercial Terms", "reason": "Not available"},
        {"clause": "c5", "reason": "External coverage is outside this bundle"},
    ]:
        judge["not_encoded"] = [waiver]
        write(root / "judge.json", judge)
        assert exam(root)["passed"]


def test_reference_exam_skips_legacy_only_but_reads_legacy_link_when_active(bundle):
    root, terms, _, _ = bundle
    for c in terms["clauses"]:
        c.pop("refs", None)
    terms["clauses"][2]["modifies"] = "c2"
    glossary = terms.pop("glossary")
    write(root / "work/terms.json", terms)
    assert exam(root)["skipped"]
    terms["glossary"] = glossary
    write(root / "work/terms.json", terms)
    check = exam(root)
    assert not check["skipped"]
    assert check["failures"] == ["P-privacy: c2 needs c3 (modifies)"]


def test_revise_rule_can_supply_source_terms(bundle):
    root, _, _, _ = bundle
    space = pac.Space(root)
    report = pac.gaps(root, check_manifest=False)
    gap = next(i for i in report["gaps"] if i["kind"] == "unresolved_reference")
    patch = {"ops": [{"op": "revise_rule", "rule": "P-privacy",
                     "changes": {"source_terms": ["c2", "c3"]}, "expected_changes": [],
                     "reason": "The approved-summary exception is part of this rule.",
                     "gaps": [gap["id"]]}]}
    pac._patch_ops(patch, report, space.generator, space.judge, [], [])
    write(root / "judge.json", space.judge)
    assert exam(root)["passed"]
