"""Independent synthetic fixtures for deterministic 1.6 term citations."""

import json
import shutil
from pathlib import Path

import pytest
from test_pac import SAMPLE, pac

DATE = "2026-11-20"
SOURCE = "https://example.org/privacy-policy"
BASE = "Do not distribute employee records without consent."
EXCEPTION = "Approved archival research is exempt."
DEFINITION = "Employee records are the files listed in the personnel register."


def _change(path: Path, fn):
    doc = json.loads(path.read_text(encoding="utf-8"))
    fn(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def cited_space(tmp_path):
    bundle = tmp_path / "cited"
    shutil.copytree(SAMPLE, bundle)
    (bundle / "conformance.jsonl").unlink()
    (bundle / "work").mkdir(exist_ok=True)
    (bundle / "work/terms.json").write_text(json.dumps({
        "source": SOURCE,
        "clauses": [
            {"id": "c3", "class": "definition", "section": "Definitions", "text": DEFINITION},
            {"id": "c4", "class": "condition_scope", "section": "Archival criteria",
             "text": "Keep an archival research ledger.", "confidence": "high",
             "refs": [{"kind": "incorporates", "to": "c5", "text": "ledger"}]},
            {"id": "c1", "class": "prohibition", "section": "Privacy", "text": BASE, "confidence": "high",
             "refs": [{"kind": "uses_definition", "to": "c3", "text": "employee records"}]},
            {"id": "c2", "class": "permission_exception", "section": "Privacy", "text": EXCEPTION,
             "confidence": "high", "modifies": "c1",
             "refs": [{"kind": "incorporates", "to": "c4", "text": "archival research"}]},
            {"id": "c5", "class": "condition_scope", "section": "Ledger",
             "text": "The ledger records access dates.", "confidence": "high"},
        ],
    }), encoding="utf-8")
    _change(bundle / "generator.json", lambda d: d.update(version="1.6"))

    def update_judge(d):
        rule = next(r for r in d["rules"] if r["id"] == "P-privacy")
        rule.update(source_terms=["c2", "c1"],
                    exceptions=[{"dim": "act", "in": ["con"], "source_terms": ["c2"]}])
        d.update(version="1.6", rules=[rule])

    _change(bundle / "judge.json", update_judge)
    return bundle


def _validate(path):
    return pac.validate(path, check_guide=False, check_manifest=False)


def test_embed_projects_only_one_level_and_is_deterministic(cited_space):
    assert pac.embed_terms(cited_space) == {"terms": ["c1", "c2", "c3", "c4"]}
    out = cited_space / "judge.json"
    before = out.read_bytes()
    pac.embed_terms(cited_space)
    assert before == out.read_bytes()
    terms = json.loads(before)["terms"]
    assert terms["c2"]["refs"] == [
        {"to": "c4", "kind": "incorporates", "text": "archival research"},
        {"to": "c1", "kind": "modifies"},
    ]
    assert all(t["source"] == SOURCE for t in terms.values())
    assert terms["c4"]["refs"] == []
    assert not _validate(cited_space)


def test_validate_missing_source_terms_or_unshipped_term(cited_space):
    pac.embed_terms(cited_space)
    out = cited_space / "judge.json"
    _change(out, lambda d: d["terms"].pop("c1"))
    assert any("missing judge term c1" in e for e in _validate(cited_space))
    _change(out, lambda d: d["rules"][0].pop("source_terms"))
    assert any(e.startswith("P-privacy: source_terms must") for e in _validate(cited_space))
    _change(out, lambda d: d["rules"][0]["exceptions"][0].update(source_terms=["c9"]))
    assert "P-privacy exception 1: source_terms names missing judge term c9" in _validate(cited_space)


def test_validate_shipped_reference_needs_target_or_external(cited_space):
    pac.embed_terms(cited_space)
    out = cited_space / "judge.json"
    _change(out, lambda d: d["terms"]["c1"]["refs"].append({"kind": "subject_to", "to": None}))
    assert "judge terms c1: null reference needs external" in _validate(cited_space)
    _change(out, lambda d: d["terms"]["c1"]["refs"][-1].update(external="Records Act"))
    assert not _validate(cited_space)


def test_violated_and_excepted_prohibition_cite_constraints(cited_space):
    pac.embed_terms(cited_space)
    sp = pac.Space(cited_space)
    code = "act=biz pur=data cons=n"
    result = pac.check(code, sp, DATE)
    assert result["verdict"] == "violates"
    [entry] = result["terms"]
    assert entry["rule"] == "P-privacy"
    assert entry["status"] == "violated"
    rule, exception, definition, incorporated = entry["terms"]
    assert rule == {"id": "c1", "role": "rule", "section": "Privacy", "text": BASE}
    assert exception == {"id": "c2", "role": "exception", "applies": False,
                         "section": "Privacy", "text": EXCEPTION}
    assert definition["role"] == "definition" and definition["text"] == DEFINITION
    assert incorporated["role"] == "incorporated"
    assert result["next_actions"][0]["terms"] == ["c1"]
    text = pac.render_report(result, sp)
    assert f'> "{BASE}" (Privacy, c1)' in text
    assert f'> Exception (does not apply): "{EXCEPTION}" (Privacy, c2)' in text
    assert f'> Definition: "{DEFINITION}" (Definitions, c3)' in text
    assert text.splitlines()[1].endswith("(c1)")
    excepted = pac.check("act=con pur=data cons=n", sp, DATE)
    assert excepted["verdict"] == "compliant"
    assert excepted["terms"][0]["status"] == "excepted"
    assert excepted["terms"][0]["terms"][1]["applies"] is True
    assert '**Excepted**' in pac.render_report(excepted, sp)
    assert pac.check("this_is_invalid", sp, DATE)["terms"] == []


@pytest.fixture
def legacy_space(tmp_path):
    bundle = tmp_path / "legacy"
    shutil.copytree(SAMPLE, bundle)
    _change(bundle / "generator.json", lambda gen: gen.update(version="1.5"))

    def without_citations(judge):
        judge["version"] = "1.5"
        judge.pop("terms", None)
        for rule in judge["rules"]:
            rule.pop("source_terms", None)
            for exception in rule.get("exceptions", []):
                exception.pop("source_terms", None)

    _change(bundle / "judge.json", without_citations)
    pac.write_manifest(bundle)
    return bundle


def test_old_bundle_fallback_is_a_warning_only(legacy_space):
    warnings = []
    assert not pac.validate(legacy_space, warnings=warnings)
    assert any("older bundle" in warning for warning in warnings)
    sp = pac.Space(legacy_space)
    result = pac.check("act=biz pur=data cons=n", sp, DATE)
    [entry] = result["terms"]
    assert entry["terms"] == [{"id": None, "role": "rule",
                               "section": "General rules: privacy and identity", "text": None}]
    assert result["next_actions"][0]["terms"] == []


def test_shipped_privacy_case_reports_an_exact_policy_excerpt():
    space = pac.Space(SAMPLE)
    result = pac.check("act=biz pur=data cons=n", space, DATE)
    assert result["verdict"] == "violates"
    [entry] = result["terms"]
    assert entry["rule"] == "P-privacy"
    privacy = next(term for term in entry["terms"] if term["role"] == "rule")
    assert "personal data unless that person has agreed" in privacy["text"]
    assert "summary" not in privacy["text"].lower()
    assert space.judge["terms"][privacy["id"]]["source"] == "https://example.com/sample-service-terms"
    assert privacy["text"] in pac.render_report(result, space)


def test_flow_deduplicates_definitions_in_report(cited_space):
    pac.embed_terms(cited_space)
    sp = pac.Space(cited_space)
    code = "act=con pur=data cons=n > act=biz pur=data cons=n"
    result = pac.check_flow(code, sp, DATE)
    assert [t["status"] for t in result["terms"]] == ["violated", "excepted"]
    assert pac.render_report(result, sp).count(DEFINITION) == 1


def test_exception_applies_is_omitted_when_undetermined_or_multiply_mapped(cited_space):
    pac.embed_terms(cited_space)
    sp = pac.Space(cited_space)
    result = pac.check("pur=data cons=n", sp, DATE)
    assert result["terms"][0]["status"] == "open"
    [exception] = [term for term in result["terms"][0]["terms"] if term["role"] == "exception"]
    assert "applies" not in exception
    sp.rules["rules"][0]["exceptions"].append({"dim": "act", "in": ["biz"], "source_terms": ["c2"]})
    result = pac.check("act=con pur=data cons=n", sp, DATE)
    assert result["terms"][0]["status"] == "excepted"
    [exception] = [term for term in result["terms"][0]["terms"] if term["role"] == "exception"]
    assert "applies" not in exception


def test_manifest_writes_exact_quotes_and_links_in_guide(cited_space):
    pac.embed_terms(cited_space)
    manifest = pac.write_manifest(cited_space)
    assert manifest["version"] == "1.6"
    guide = (cited_space / "BUNDLE.md").read_text(encoding="utf-8")
    assert "| id | title | kind | what to do | source | terms |" in guide
    assert guide.index("## Rules") < guide.index("## Terms") < guide.index("## Examples")
    assert guide.index("**c1**") < guide.index("**c2**") < guide.index("**c3**")
    assert f"> {BASE}" in guide
    assert "links: uses_definition → c3" in guide
    assert not pac.validate(cited_space)
    assert pac.main(["--space", str(cited_space), "guide", "--check"]) == 0


def test_refreshing_legacy_manifest_does_not_claim_new_format(legacy_space):
    assert pac.write_manifest(legacy_space)["version"] == "1.5"
    assert not pac.validate(legacy_space)


@pytest.mark.parametrize(
    ("fields", "expected_error"),
    [
        ({"text": "  sUmMaRy (not verbatim): Example."}, "text starts with Summary"),
        ({"text": "Summaryish attempted quote."}, "text starts with Summary"),
        ({"text": BASE, "summary": "Paraphrase."}, "exactly one non-empty text or summary"),
        ({}, "exactly one non-empty text or summary"),
        ({"summary": " "}, "exactly one non-empty text or summary"),
    ],
)
def test_validate_rejects_invalid_citation_fields(cited_space, fields, expected_error):
    pac.embed_terms(cited_space)

    def replace_fields(judge):
        term = judge["terms"]["c1"]
        term.pop("text")
        term.update(fields)

    _change(cited_space / "judge.json", replace_fields)
    assert any(f"judge terms c1: {expected_error}" in error for error in _validate(cited_space))


def test_shipped_exact_excerpts_are_short():
    terms = pac.Space(SAMPLE).judge["terms"]
    quotes = [term["text"] for term in terms.values() if "text" in term]
    assert quotes and all(0 < len(quote.split()) <= 25 for quote in quotes)


def test_embed_validate_and_render_summary_citations(cited_space):
    converted = {"c1": "Paraphrased prohibition.", "c2": "Paraphrased exception.",
                 "c3": "Paraphrased definition."}

    def use_summaries(doc):
        for clause in doc["clauses"]:
            if clause["id"] in converted:
                clause.pop("text")
                clause["summary"] = converted[clause["id"]]

    _change(cited_space / "work/terms.json", use_summaries)
    pac.embed_terms(cited_space)
    warnings = []
    assert not pac.validate(cited_space, check_guide=False, check_manifest=False, warnings=warnings)
    assert [w for w in warnings if "summary" in w] == [
        f"judge terms {ident}: summary is not a verbatim quote" for ident in converted
    ]
    sp = pac.Space(cited_space)
    result = pac.check("act=biz pur=data cons=n", sp, DATE)
    [entry] = result["terms"]
    assert {term["id"]: term["summary"] for term in entry["terms"] if "summary" in term} == converted
    assert all("text" not in term for term in entry["terms"] if term["id"] in converted)
    report = pac.render_report(result, sp)
    guide = pac.render_guide(cited_space).decode("utf-8")
    for summary in converted.values():
        assert f"Summary (not a quote): {summary}" in report
        assert f"> Summary (not a quote): {summary}" in guide
        assert f'"{summary}"' not in report + guide
    assert "> Exception (does not apply): Summary (not a quote):" in report
    assert "> Definition: Summary (not a quote):" in report


def test_render_does_not_quote_old_summary_prefix_even_without_validation(cited_space):
    pac.embed_terms(cited_space)
    _change(cited_space / "judge.json",
            lambda d: d["terms"]["c1"].update(text="sUmMaRy (not verbatim): Legacy paraphrase."))
    sp = pac.Space(cited_space)
    result = pac.check("act=biz pur=data cons=n", sp, DATE)
    citation = result["terms"][0]["terms"][0]
    assert citation["summary"] == "Legacy paraphrase."
    assert "text" not in citation
    assert "> Summary (not a quote): Legacy paraphrase." in pac.render_report(result, sp)
    # Call report on an old serialized result, not only the current check output.
    citation["text"] = "Summary (not verbatim): Legacy paraphrase."
    del citation["summary"]
    assert '> "Summary' not in pac.render_report(result, sp)
    guide = pac.render_guide(cited_space).decode("utf-8")
    assert "> Summary (not a quote): Legacy paraphrase." in guide
    assert "not verbatim" not in guide
