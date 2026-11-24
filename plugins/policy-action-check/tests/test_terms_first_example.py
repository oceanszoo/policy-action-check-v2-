"""End-to-end checks for the shipped 2.0 example, separate from legacy regressions."""

from test_pac import ROOT, SAMPLE, pac

EXAMPLE = ROOT / "examples" / "sample-service-terms"


def test_shipped_example_validates_and_keeps_the_original_terms():
    assert pac.validate(EXAMPLE) == []
    before = pac.Space(SAMPLE).judge["terms"]
    after = pac.Space(EXAMPLE).judge["terms"]
    assert set(after) == set(before)
    for cid, term in before.items():
        assert {k: after[cid][k] for k in term} == term


def test_shipped_example_privacy_quote_and_child_age_boundary():
    bundle = pac.Space(EXAMPLE)
    result = pac.check("pur=data cons=n", bundle)
    assert "T-c007" in result["violated"]
    quote = next(entry for entry in result["terms"] if entry["rule"] == "T-c007")["terms"][0]
    assert quote["id"] == "c007" and quote["text"] == "Do not disclose another person's personal data unless that person has agreed."
    assert quote["text"] in pac.render_report(result, bundle)

    before = pac.check("pur=grooming age=17", bundle)
    at = pac.check("pur=grooming age=18", bundle)
    assert "T-c008" in before["violated"]
    assert "T-c008" not in at["violated"]
    child = next(entry for entry in before["terms"] if entry["rule"] == "T-c008")["terms"]
    assert any(term["id"] == "c009" and term["role"] == "definition" for term in child)
