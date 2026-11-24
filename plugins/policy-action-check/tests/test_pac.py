"""Offline tests for the policy-action-check engine (scripts/pac.py), stdlib + pytest."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pac

SAMPLE = ROOT.parents[1] / "apps/pac-reader/tests/fixtures/legacy"
REPO = ROOT.parents[1]
LABELS = Path(__file__).resolve().parent / "fixtures" / "labels.jsonl"


@pytest.fixture(scope="module")
def space():
    return pac.Space(SAMPLE)


def judge(space, code):
    return pac.check(code, space)


# ------------------------------------------------------------- bundle and conformance


def test_example_bundle_validates():
    assert pac.validate(SAMPLE) == []


def test_rejects_other_major_version(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    g["version"] = "3.0"
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    with pytest.raises(pac.SpaceError):
        pac.Space(tmp_path / "b")


def test_manifest_digests(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    man = pac.write_manifest(tmp_path / "b", "https://example.com/sample-service-terms")
    assert man["format"] == "pac-bundle"
    assert set(man["files"]) == {"generator.json", "judge.json", "conformance.jsonl", "BUNDLE.md"}


def test_conformance_mismatch_is_reported(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    with (tmp_path / "b" / "conformance.jsonl").open("a") as f:
        f.write(json.dumps({"code": "pur=abuse", "expected": {"verdict": "compliant"}}) + "\n")
    assert any("conformance" in e for e in pac.validate(tmp_path / "b"))


# ------------------------------------------------------------- codes


def test_parse_overrides_macros_and_unset(space):
    p = pac.parse_code("demo: @claim-pay fav=part disc=?", space)
    assert p["name"] == "demo" and p["features"]["fav"] == "part" and "disc" not in p["features"]


def test_canonical_form_is_order_independent(space):
    a = pac.format_code(pac.parse_code("rev=y act=biz", space)["features"], space)
    b = pac.format_code(pac.parse_code("act=biz rev=y", space)["features"], space)
    assert a == b == "act=biz rev=y"


@pytest.mark.parametrize("code,suggestion", [
    ("hr=insurance", "hr=ins"),      # value meaning match
    ("hrr=ins", "hr=ins"),           # key typo
    ("pur=cybr", "pur=cyber"),       # value typo
    ("@claim-pai", None),            # unknown saved code: suggestion may be the close macro
])
def test_invalid_tokens_get_suggestions(space, code, suggestion):
    res = judge(space, code)
    assert res["verdict"] == "invalid_code"
    if suggestion:
        assert res["errors"][0]["did_you_mean"] == suggestion


def test_round_trip_reading_is_stable(space):
    code = "act=biz pur=std hr=ins scope=ind fav=part rev=n disc=y"
    canon = pac.format_code(pac.parse_code(code, space)["features"], space)
    assert canon == code and pac.explain_code(pac.parse_code(canon, space)["features"], space)


# ------------------------------------------------------------- semantics


def test_unset_requirement_is_required_next_not_violation(space):
    res = judge(space, "act=biz pur=std hr=ins scope=ind fav=part")
    assert res["verdict"] == "compliant_if_requirements_met"
    assert res["required_next"] == ["O-hr-disclosure", "O-hr-review"]


def test_unset_deciding_key_is_open(space):
    assert judge(space, "pur=cyber")["open"] == ["P-cyber"]


def test_rules_inactive_before_effective_date(space):
    assert judge(space, "pur=std chat=y disc=n date=2026-11-01")["verdict"] == "compliant"


def test_determinism(space):
    code = "@robot-shared stop=y lim=n"
    assert all(judge(space, code) == judge(space, code) for _ in range(3))


# ------------------------------------------------------------- fixes and panel


def test_fix_prefers_filling_unset(space):
    res = judge(space, "@support-bot")
    assert res["fix"] == [["+disc=y"]] and res["fix_cost"] == 0.5


def test_fix_changes_set_value(space):
    assert judge(space, "pur=cyber auth=unauth")["fix"] == [["auth=unauth -> auth=own"]]


def test_no_fix_for_prohibited_purpose(space):
    res = judge(space, "pur=weap")
    assert res["fix"] == [] and "no compliant variant" in res["fix_note"]


def test_panel_flags_violation_at_first_token(space):
    rows = pac.panel("act=biz pur=std hr=ins scope=ind fav=part rev=n", space)
    assert rows[3]["now_required"] == ["O-hr-disclosure", "O-hr-review"]
    assert rows[5]["now_violated"] == ["O-hr-review"]
    assert rows[0]["next_key"] == "pur" and rows[0]["suggested_value"] == "std"


# ------------------------------------------------------------- the eval set's clause cases

# Hand-written codes for the clause scenarios in tests/fixtures/labels.jsonl.
# This checks that the example bundle can express each case and that the engine agrees with
# the labels. It does not test text-to-code encoding, which is the model's job.
CLAUSE_CODES = {
    "sample-pentest-authorized": "act=biz pur=cyber auth=own",
    "sample-pentest-out-of-scope": "act=biz pur=cyber auth=unauth",
    "sample-aml-screening": "act=biz pur=track cons=y",
    "sample-track-partner": "act=con pur=track cons=n",
    "sample-labelled-satire": "act=biz pur=imp fic=lab",
    "sample-unlabelled-fake-quote": "act=con pur=imp fic=real",
    "sample-insurer-pay-full": "@claim-pay",
    "sample-insurer-auto-deny": "act=biz pur=std hr=ins scope=ind fav=part rev=n",
    "sample-insurer-partial": "act=biz pur=std hr=ins scope=ind fav=part rev=n disc=y",
    "sample-hiring-reviewed": "act=biz pur=std hr=emp scope=ind fav=part rev=y disc=y",
    "sample-hiring-auto-reject": "act=biz pur=std hr=emp scope=ind fav=part rev=n",
    "sample-mental-health-direct": "act=biz pur=std hr=med scope=ind fav=na rev=n chat=y",
    "sample-wellness-blog": "act=biz pur=std hr=med scope=nc",
    "sample-support-bot": "@support-bot",
    "sample-support-bot-human": "@support-bot disc=n",
    "sample-robot-safe": "@robot-shared stop=y safe=y lim=y",
    "sample-robot-model-limits": "@robot-shared stop=y safe=y lim=n",
    "sample-robot-vacuum": "act=con pur=std phys=nc",
    "sample-hazard-lab": "act=biz pur=std phys=hi stop=y",
    "sample-distillation": "act=biz pur=abuse",
    "sample-essay-for-credit": "act=con pur=fraud",
    "sample-loan-reviewed": "act=biz pur=std hr=credit scope=ind fav=part rev=y disc=y",
    "sample-arrest-decision": "act=biz pur=lawenf",
    "sample-employee-emotion": "act=biz pur=emo",
    "sample-driver-drowsiness": "act=biz pur=std",
    "sample-shopping-agent": "act=agt pur=std chat=y disc=y",
}


def _labels():
    if not LABELS.exists():
        return {}
    return {r["id"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["source_type"] == "clause"}


@pytest.mark.parametrize("sid", sorted(CLAUSE_CODES))
def test_clause_scenarios_match_labels(space, sid):
    labels = _labels()
    if sid not in labels:
        pytest.skip("eval labels not present")
    exp = labels[sid]["expected"]
    res = judge(space, CLAUSE_CODES[sid])
    assert res["verdict"] == exp["verdict"]
    assert set(exp["violated"]) <= set(res["violated"]) <= set(exp["violated"]) | set(exp["violated_also_ok"])
    assert set(exp["required_next"]) <= set(res["required_next"]) <= set(exp["required_next"]) | set(exp["required_next_also_ok"])


def test_every_clause_scenario_has_a_code():
    labels = _labels()
    if labels:
        assert set(labels) == set(CLAUSE_CODES)


# ------------------------------------------------------------- objective input, next actions


@pytest.mark.parametrize("code", ["risk=low pur=std", "act=biz rev=fine", "intent=good", "pur=std ok=yes"])
def test_subjective_input_is_refused(space, code):
    res = judge(space, code)
    assert res["verdict"] == "invalid_code" and res["errors"][0].get("subjective")
    assert res["next_actions"][0]["kind"] == "fix_code"


def test_next_actions_lead_with_required_controls(space):
    res = judge(space, "act=biz pur=std hr=ins scope=ind fav=part rev=n")
    assert [a["code_change"] for a in res["next_actions"]] == ["+disc=y", "rev=n -> rev=y"]
    assert all(a["kind"] == "do" for a in res["next_actions"])


def test_next_actions_stop_establish_proceed(space):
    assert judge(space, "pur=weap")["next_actions"][0]["kind"] == "stop"
    est = judge(space, "pur=data")["next_actions"]
    assert est[0]["kind"] == "establish" and est[0]["key"] == "cons"
    assert judge(space, "act=biz pur=std")["next_actions"][0]["kind"] == "proceed"


def test_fix_never_changes_the_nature_of_the_action(space):
    res = judge(space, "act=biz pur=std hr=ins scope=ind fav=part rev=n")
    changed = {c.split("=")[0].lstrip("+") for fix in res["fix"] for c in fix}
    assert changed <= {"rev", "disc"}


def test_bundle_values_must_be_objective(tmp_path):
    b = tmp_path / "b"
    shutil.copytree(SAMPLE, b)
    g = json.loads((b / "generator.json").read_text())
    g["dimensions"][0]["values"]["low_risk"] = "low risk"
    (b / "generator.json").write_text(json.dumps(g))
    assert any("judgement" in e for e in pac.validate(b))


# ------------------------------------------------------------- hooks


def run_hook(event, payload, env_extra=None, space_dir=None):
    import os

    env = dict(os.environ)
    if space_dir:
        env["PAC_SPACE"] = str(space_dir)
    env.update(env_extra or {})
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "pac.py"), "hook", event],
                         input=json.dumps(payload), capture_output=True, text=True, env=env, check=True)
    return json.loads(out.stdout) if out.stdout.strip() else None


def test_prompt_hook_detects_policy_intent(tmp_path):
    out = run_hook("prompt", {"prompt": "Is it ok under the usage policy to auto-deny claims?"}, space_dir=tmp_path / "none")
    assert "policy-pipeline" in out["hookSpecificOutput"]["additionalContext"]


def test_prompt_hook_ignores_unrelated(tmp_path):
    assert run_hook("prompt", {"prompt": "rename this variable"}, space_dir=tmp_path / "none") is None


def test_guard_hook_asks_on_violation(tmp_path):
    b = tmp_path / "b"
    shutil.copytree(SAMPLE, b)
    g = json.loads((b / "generator.json").read_text())
    g["tool_map"] = {"base": "act=agt pur=std", "mappings": [
        {"tool": "^mcp__claims__", "input": "deny", "code": "hr=ins scope=ind fav=part rev=n"}]}
    (b / "generator.json").write_text(json.dumps(g))
    payload = {"tool_name": "mcp__claims__decide", "tool_input": {"decision": "deny", "claim": 7}}
    out = run_hook("guard", payload, {"CLAUDE_PLUGIN_OPTION_GUARD_MODE": "enforce"}, b)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "O-hr-review" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert run_hook("guard", payload, {"CLAUDE_PLUGIN_OPTION_GUARD_MODE": "off"}, b) is None


def test_stop_hook_blocks_unfinished_pipeline_once(tmp_path):
    b = tmp_path / "b"
    pac.write_state(b, stage="build")
    assert run_hook("stop", {}, space_dir=b)["decision"] == "block"
    assert run_hook("stop", {"stop_hook_active": True}, space_dir=b) is None
    pac.write_state(b, awaiting_user=True)
    assert run_hook("stop", {}, space_dir=b) is None


def test_subagent_stop_validates_stage(tmp_path):
    b = tmp_path / "b"
    b.mkdir()
    out = run_hook("subagent-stop", {"agent_type": "policy-action-check:scope-planner"}, space_dir=b)
    assert out["decision"] == "block" and "scope.json" in out["reason"]


def _terms(b, clauses):
    (b / "work").mkdir(parents=True, exist_ok=True)
    (b / "work" / "terms.json").write_text(json.dumps({"clauses": clauses}))


def test_term_filter_validation(tmp_path):
    b = tmp_path / "b"
    _terms(b, [{"id": "c1", "class": "obligation", "text": "must review", "confidence": "high"},
               {"id": "c2", "class": "permission_exception", "text": "except", "modifies": "c9",
                "confidence": "high"},
               {"id": "c3", "class": "musing", "text": "x"}])
    errs = pac.validate(b, "filter")
    assert any("c9" in e for e in errs) and any("c3" in e for e in errs)


def test_rule_built_from_description_is_rejected(tmp_path):
    b = tmp_path / "b"
    shutil.copytree(SAMPLE, b)
    _terms(b, [{"id": "c1", "class": "description", "text": "We care about safety."}])
    j = json.loads((b / "judge.json").read_text())
    j["rules"][0]["source_terms"] = ["c1"]
    (b / "judge.json").write_text(json.dumps(j))
    assert any("descriptive clause c1" in e for e in pac.validate(b))


def test_hook_never_crashes_on_bad_input(tmp_path):
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "pac.py"), "hook", "prompt"],
                          input="not json", capture_output=True, text=True, check=False)
    assert proc.returncode == 0


# ------------------------------------------------------------- spec 1.1


def test_multi_valued_purpose_is_canonical_and_judged_per_member(space):
    out = judge(space, "act=biz pur=fraud+track cons=y")
    assert out["code"] == "act=biz pur=track+fraud cons=y"
    assert out["violated"] == ["P-fraud"]
    assert "+" in out["reading"]


def test_multi_value_on_single_dimension_is_an_error(space):
    out = judge(space, "act=biz pur=std hr=ins+legal")
    assert out["verdict"] == "invalid_code"
    assert "one value" in out["errors"][0]["message"]


def test_multi_value_with_unknown_member_is_an_error(space):
    out = judge(space, "act=biz pur=std+cyberr")
    assert out["verdict"] == "invalid_code"
    assert out["errors"][0]["did_you_mean"] == "pur=cyber"


def test_facts_record_where_each_value_came_from(space):
    facts = {f["key"]: f for f in judge(space, "@claim-pay rev=y")["facts"]}
    assert facts["rev"]["from"] == "code"
    assert facts["hr"]["from"] == "@claim-pay"
    assert facts["chat"]["from"] == "default" and facts["chat"]["assumed"]


def test_requirements_are_separate_from_unknown_facts(space):
    out = judge(space, "act=biz pur=data hr=legal scope=ind fav=part")
    assert {r["rule"] for r in out["requirements"]} == {"O-hr-review", "O-hr-disclosure"}
    assert [u["key"] for u in out["unknown_facts"]] == ["cons"]
    assert out["unknown_facts"][0]["decides"] == ["P-privacy"]


def test_space_over_budget_is_rejected_unless_raised_with_reason(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    gpath = tmp_path / "b" / "generator.json"
    g = json.loads(gpath.read_text())
    g["limits"] = {"max_dimensions": 5}
    gpath.write_text(json.dumps(g))
    assert any("space too big" in e for e in pac.validate(tmp_path / "b"))
    g["limits"] = {"max_dimensions": 30}
    gpath.write_text(json.dumps(g))
    assert any("needs a 'reason'" in e for e in pac.validate(tmp_path / "b"))
    g["limits"]["reason"] = "policy has 15 independent controls"
    gpath.write_text(json.dumps(g))
    assert pac.validate(tmp_path / "b") == [
        "BUNDLE.md stale; run pac.py guide", "generator.json: digest mismatch; run pac.py manifest",
    ]
    pac.write_manifest(tmp_path / "b")
    assert pac.validate(tmp_path / "b") == []


def test_scope_gap_needs_its_own_question_and_clauses(tmp_path):
    (tmp_path / "work").mkdir()
    area = {"area": "Physical actions", "examples": 0, "gap": True, "decision": "ask"}
    (tmp_path / "work" / "scope.json").write_text(json.dumps({"areas": [area]}))
    errs = pac.validate(tmp_path, "scope")
    assert any("source_terms" in e for e in errs) and any("'question'" in e for e in errs)
    area |= {"source_terms": ["c020"], "question": "Do you control physical equipment? (recommended: out of scope)"}
    (tmp_path / "work" / "scope.json").write_text(json.dumps({"areas": [area]}))
    assert pac.validate(tmp_path, "scope") == []


# ------------------------------------------------------------- spec 1.2: no model at use time


def test_form_asks_conditions_before_requirements(space):
    assert pac.next_question("", space)["key"] == "pur"
    assert pac.next_question("pur=std", space)["key"] == "hr"
    q = pac.next_question("pur=std hr=ins scope=ind fav=part", space)
    assert q["key"] == "rev" and q["decides"] == ["O-hr-review"]
    # requirement keys of an obligation that doesn't apply are never asked
    flow = []
    answers = ""
    for value in ("std", "none", "n", "none"):
        q = pac.next_question(answers, space)
        if q["done"]:
            break
        flow.append(q["key"])
        answers += f" {q['key']}={value}"
    assert flow == ["pur", "hr", "chat", "phys"]
    assert pac.next_question(answers, space)["check"]["verdict"] == "compliant"


def test_form_unknown_answer_counts_as_asked(space):
    q = pac.next_question("pur=std hr=?", space)
    assert q["key"] != "hr"


def test_form_suggests_default(space):
    q = pac.next_question("pur=std", space)
    assert [o["value"] for o in q["options"] if o["suggested"]] == ["none"]
    assert "assumed" in q["unknown_means"]


def test_terminal_form_runs_without_a_model(space):
    picks = {"pur": "cyber", "auth": "unauth"}  # Enter (suggested value) or ? for the rest
    lines = []
    q = pac.run_form(space, inp=lambda prompt: "" if prompt.startswith("note") else picks.get(prompt[:-2], "?"),
                     out=lines.append)
    assert q["code"] == "pur=cyber auth=unauth"
    assert q["check"]["verdict"] == "violates"
    assert "Not allowed" in lines[-1]


def test_lookup_is_plain_phrase_matching(space):
    hits = pac.lookup("Our customer support bot denies insurance claims without review", space)
    assert [h["token"] for h in hits] == ["chat=y", "hr=ins", "rev=n"]
    assert pac.lookup("nothing relevant here", space) == []


def test_report_is_filled_from_bundle_text(space):
    text = pac.render_report(pac.check("act=biz pur=std hr=ins scope=ind fav=part", space), space)
    assert text.startswith("## What to do next")
    assert "Qualified human-in-the-loop [O-hr-review]" in text
    assert "**Must do**" in text and "not legal advice" in text


def test_bundle_carries_its_own_subjective_words_and_records(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    g["subjective_terms"] = ["vibes"]
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    (tmp_path / "b" / "records.jsonl").write_text(
        json.dumps({"id": "R1", "code": "act=biz pur=cyber auth=own", "outcome": "allowed"}) + "\n")
    sp = pac.Space(tmp_path / "b")
    assert pac.check("vibes=good", sp)["errors"][0]["subjective"]
    assert pac.check("act=biz pur=cyber auth=own", sp)["similar_records"][0]["id"] == "R1"
    assert pac.validate(tmp_path / "b") == [
        "BUNDLE.md stale; run pac.py guide", "generator.json: digest mismatch; run pac.py manifest",
    ]
    pac.write_manifest(tmp_path / "b")
    assert pac.validate(tmp_path / "b") == []
    assert "records.jsonl" in pac.write_manifest(tmp_path / "b")["files"]


def test_version_1_2_requires_questions(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    del g["dimensions"][0]["question"]
    g["lexicon"].append({"phrase": "x", "token": "hr=nope"})
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    errs = pac.validate(tmp_path / "b")
    assert any("needs a 'question'" in e for e in errs) and any("invalid token" in e for e in errs)


def test_notes_are_shown_but_never_judged(space):
    code = "act=biz pur=std hr=ins scope=ind fav=part"
    plain = pac.check(code, space)
    noted = pac.check(code, space, notes={"hr": "only claims under 500, it's low risk", "_action": "pilot", "zz": "x"})
    assert noted["notes"] == {"hr": "only claims under 500, it's low risk", "_action": "pilot"}
    assert {k: v for k, v in noted.items() if k != "notes"} == {k: v for k, v in plain.items() if k != "notes"}
    text = pac.render_report(noted, space)
    assert "Notes (shown only, not used in judging)" in text and "- pilot" in text


def test_terminal_form_takes_notes_after_hash(space):
    picks = {"pur": "cyber # red-team engagement", "auth": "own # signed scope letter",
             "note for the whole action (optional)": "ticket 42"}
    lines = []
    q = pac.run_form(space, inp=lambda prompt: picks.get(prompt[:-2], "?"), out=lines.append)
    assert q["check"]["verdict"] == "compliant"
    assert q["check"]["notes"] == {"pur": "red-team engagement", "auth": "signed scope letter",
                                   "_action": "ticket 42"}


# ------------------------------------------------------------- fixes from the v1.2 eval


def test_invalid_code_gets_no_partial_judgement(space):
    out = judge(space, "pur=cyber risk=low")
    assert out["verdict"] == "invalid_code"
    assert out["violated"] == out["required_next"] == out["open"] == []
    assert out["requirements"] == out["unknown_facts"] == [] and out["fix"] == []
    assert [a["kind"] for a in out["next_actions"]] == ["fix_code"]


def test_flow_judges_each_action(space):
    out = pac.check_flow("intake: act=biz pur=std chat=y disc=y > attack: act=biz pur=cyber auth=unauth", space)
    assert [s["verdict"] for s in out["flow"]] == ["compliant", "violates"]
    assert out["verdict"] == "violates"
    assert out["next_actions"][0]["action_index"] == 1
    assert "# Action 2: attack" in pac.render_report(out, space)


def test_next_steps_bind_to_the_action_name(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    g["transitions"] = {"draft": {"review": 3, "deliver": 1}}
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    out = pac.check("draft: act=biz pur=std", pac.Space(tmp_path / "b"))
    assert out["step"] == "draft"
    assert out["next_steps"][0] == {"step": "review", "count": 3, "share": 0.75}


def test_form_finds_rules_that_need_two_values_together(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    j = json.loads((tmp_path / "b" / "judge.json").read_text())
    j["rules"].append({"id": "P-both", "kind": "prohibition", "source": "test", "next_step": "Do not proceed.",
                       "when": {"all": [{"dim": "pur", "in": ["data"]}, {"dim": "pur", "in": ["track"]},
                                        {"dim": "act", "in": ["con"]}]}})
    (tmp_path / "b" / "judge.json").write_text(json.dumps(j))
    sp = pac.Space(tmp_path / "b")
    assert "P-both" in pac.next_question("", sp)["decides"]


def test_establish_lists_each_unknown_key_once(space):
    out = judge(space, "act=biz pur=data+track")
    keys = [a["key"] for a in out["next_actions"] if a["kind"] == "establish"]
    assert keys == sorted(set(keys))


# ------------------------------------------------------------- self-exam (1.3)


def _exam(root):
    return {c["id"]: c for c in pac.exam(root, write=False)["checks"]}


def test_example_bundle_passes_its_self_exam():
    res = pac.exam(SAMPLE, write=False)
    assert res["passed"], [c for c in res["checks"] if not c["passed"]]
    references = next(c for c in res["checks"] if c["id"] == "references")
    assert not references["skipped"] and references["passed"], references


def test_example_terms_store_quotes_and_summaries_separately(space):
    terms = list(space.judge["terms"].values())
    assert all(("text" in term) != ("summary" in term) for term in terms)
    quotes = [term["text"] for term in terms if "text" in term]
    assert quotes and len(quotes) < len(terms)
    assert all(0 < len(quote.split()) <= 25 for quote in quotes)


def test_exam_catches_an_untested_rule(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    lines = (tmp_path / "b" / "conformance.jsonl").read_text().splitlines()
    (tmp_path / "b" / "conformance.jsonl").write_text(
        "\n".join(x for x in lines if "P-weapons" not in x) + "\n")
    checks = _exam(tmp_path / "b")
    assert not checks["rule_coverage"]["passed"]
    assert any(f.startswith("P-weapons") for f in checks["rule_coverage"]["failures"])


def test_exam_mutation_finds_weak_tests(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    lines = (tmp_path / "b" / "conformance.jsonl").read_text().splitlines()
    keep = [x for x in lines if '"pur=cyber auth=own"' in x or "pur=cyber auth=unauth" in x]
    (tmp_path / "b" / "conformance.jsonl").write_text("\n".join(keep) + "\n")
    checks = _exam(tmp_path / "b")
    assert checks["mutation_score"]["score"] < 0.8 and not checks["mutation_score"]["passed"]


def test_exam_terms_coverage_needs_rule_or_reason(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    (tmp_path / "b" / "work").mkdir()
    clause = {"id": "c900", "class": "prohibition", "text": "Do not do X.", "confidence": "high"}
    (tmp_path / "b" / "work" / "terms.json").write_text(json.dumps({"clauses": [clause]}))
    assert not _exam(tmp_path / "b")["terms_coverage"]["passed"]
    j = json.loads((tmp_path / "b" / "judge.json").read_text())
    j["not_encoded"] = [{"clause": "c900", "reason": "X is not something this user can do"}]
    (tmp_path / "b" / "judge.json").write_text(json.dumps(j))
    assert _exam(tmp_path / "b")["terms_coverage"]["passed"]


def test_exam_replay_needs_agreement_and_reasons(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    g["outcome_map"] = {"approved": ["compliant"], "blocked": ["violates"]}
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    recs = [{"id": "R1", "code": "act=biz pur=cyber auth=unauth", "outcome": "blocked"},
            {"id": "R2", "code": "act=biz pur=fraud", "outcome": "approved"}]
    (tmp_path / "b" / "records.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    checks = _exam(tmp_path / "b")
    assert not checks["replay_agreement"]["passed"]
    assert checks["replay_agreement"]["failures"][0].startswith("R2")
    recs[1]["disagreement"] = "past approval of a scam was a desk error"
    recs.append({"id": "R3", "code": "act=biz pur=std", "outcome": "approved"})
    recs.append({"id": "R4", "code": "act=biz pur=weap", "outcome": "blocked"})
    recs.append({"id": "R5", "code": "act=biz pur=std chat=n", "outcome": "approved"})
    recs.append({"id": "R6", "code": "act=biz pur=infra", "outcome": "blocked"})
    recs.append({"id": "R7", "code": "act=biz pur=elect", "outcome": "blocked"})
    recs.append({"id": "R8", "code": "act=biz pur=sex", "outcome": "blocked"})
    recs.append({"id": "R9", "code": "act=biz pur=viol", "outcome": "blocked"})
    recs.append({"id": "R10", "code": "act=biz pur=child", "outcome": "blocked"})
    (tmp_path / "b" / "records.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    checks = _exam(tmp_path / "b")
    assert checks["replay_agreement"]["passed"], checks["replay_agreement"]
    assert checks["replay_decisive"]["passed"]


def test_badge_only_for_exam_on_current_files(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    pac.exam(tmp_path / "b")
    assert pac.write_manifest(tmp_path / "b")["exam"]["passed"] is True
    g = tmp_path / "b" / "generator.json"
    g.write_text(g.read_text().replace('"pur"', '"pur"', 1) + " ")
    assert pac.write_manifest(tmp_path / "b")["exam"] is None


def test_verifier_cannot_stop_while_exam_fails(tmp_path, monkeypatch):
    shutil.copytree(SAMPLE, tmp_path / "b")
    lines = (tmp_path / "b" / "conformance.jsonl").read_text().splitlines()
    (tmp_path / "b" / "conformance.jsonl").write_text(
        "\n".join(x for x in lines if "P-weapons" not in x) + "\n")
    pac.write_manifest(tmp_path / "b")
    monkeypatch.setenv("PAC_SPACE", str(tmp_path / "b"))
    out = pac.hook_subagent_stop({"agent_type": "policy-action-check:space-verifier"})
    assert out and out["decision"] == "block" and "self-exam" in out["reason"]


# ------------------------------------------------------------- 1.4: categories and simultaneous cases


def test_split_flow_stages():
    assert pac.split_flow("a=1 & b=2 > c=3") == [["a=1", "b=2"], ["c=3"]]
    assert pac.split_flow("a=1") == [["a=1"]]


def test_simultaneous_cases_are_judged_each_on_its_own(space):
    out = pac.check_flow("pur=cyber auth=unauth & @support-bot disc=y > @robot-shared stop=y safe=y lim=y", space)
    assert out["stages"] == [[0, 1], [2]]
    assert [s["verdict"] for s in out["flow"]] == ["violates", "compliant", "compliant"]
    assert out["verdict"] == "violates"
    assert {a["action_index"] for a in out["next_actions"]} == {0}
    text = pac.render_report(out, space)
    assert "# Step 1: 2 actions at the same time" in text and "# Action 3" in text
    with pytest.raises(pac.SpaceError):
        pac.check("pur=std & pur=data", space)


def test_sequence_report_keeps_plain_action_headings(space):
    text = pac.render_report(pac.check_flow("pur=std > pur=data", space), space)
    assert "# Step" not in text and "# Action 2" in text


def test_categories_from_bundle_and_fallback(space, tmp_path):
    cats = pac.categories(space)
    assert cats[0]["id"] == "chat" and cats[0]["preset"] == "chat=y" and "disc" in cats[0]["features"]
    shutil.copytree(SAMPLE, tmp_path / "b")
    g = json.loads((tmp_path / "b" / "generator.json").read_text())
    del g["categories"]
    g["version"] = "1.3"
    (tmp_path / "b" / "generator.json").write_text(json.dumps(g))
    sp = pac.Space(tmp_path / "b")
    (only,) = pac.categories(sp)
    assert only["id"] == "any" and only["features"] == pac.dimension_order(sp) and len(only["features"]) == len(sp.dims)


def test_validate_categories(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    path = tmp_path / "b" / "generator.json"
    g = json.loads(path.read_text())

    def errs(cats):
        path.write_text(json.dumps({**g, "categories": cats}))
        return pac.validate(tmp_path / "b")

    assert any("needs 'categories'" in e for e in errs([]))
    bad = [{"id": "x", "name": "X", "preset": "pur=cyber", "features": ["act", "nope"]}]
    found = " | ".join(errs(bad))
    assert "unknown feature 'nope'" in found and "preset key 'pur'" in found and "no category offers" in found
    assert any("invalid preset" in e for e in errs([{"id": "x", "name": "X", "preset": "risk=low", "features": ["act"]}]))
    assert any("duplicate category id" in e for e in errs(g["categories"] + g["categories"][:1]))
    assert errs(g["categories"]) == [
        "BUNDLE.md stale; run pac.py guide", "generator.json: digest mismatch; run pac.py manifest",
    ]
    pac.write_manifest(tmp_path / "b")
    assert pac.validate(tmp_path / "b") == []


def test_skipped_facts_give_every_possible_region(space):
    out = judge(space, "act=biz pur=cyber")
    assert out["verdict"] == "needs_info"
    regions = out["possible"]
    assert [g["verdict"] for g in regions] == ["violates", "compliant"]
    assert regions[0]["when"] == {"auth": ["na", "unauth"]} and regions[0]["violated"] == ["P-cyber"]
    assert regions[1]["when"] == {"auth": ["own"]} and all(g["exact"] and g["of"] == 3 for g in regions)
    assert "If `auth=own` (1 of 3): Allowed as coded." in pac.render_report(out, space)
    assert judge(space, "act=biz pur=std")["possible"] == []


def test_possible_regions_cover_every_combination(space):
    for code in pac._sample_codes(space, 120, seed=5):
        out = judge(space, code)
        if not out["possible"]:
            continue
        assert sum(g["count"] for g in out["possible"]) == out["possible"][0]["of"]
        for g in out["possible"]:  # each region is reproduced by judging one of its combinations
            pick = {k: vs[0] for k, vs in g["when"].items()}
            if g["exact"]:
                got = pac.evaluate({**out["features"], **pick}, space)
                assert (got["verdict"], got["violated"], got["required_next"]) == (
                    g["verdict"], g["violated"], g["required_next"])


def test_possible_regions_fall_back_to_one_fact_at_a_time(space, monkeypatch):
    monkeypatch.setattr(pac, "MAX_COMBINATIONS", 1)
    regions = judge(space, "act=biz pur=cyber")["possible"]
    assert all(not g["exact"] and g["examples"] for g in regions)


# ------------------------------------------------------------- 1.4: nested case map


def test_category_tree_inherits_preset_and_features(space):
    nodes = {n["path"]: n for n in pac.category_nodes(pac.categories(space))}
    leaf = nodes["advice/ins/person/other"]
    assert leaf["preset"] == "hr=ins scope=ind fav=part"
    assert leaf["features"] == nodes["advice"]["features"] and leaf["children"] == []
    assert nodes["chat"]["children"] and nodes["other"]["catch_all"] and not nodes["chat"]["catch_all"]
    assert not nodes["listed/fraud"]["children"]  # flat where the material needs no depth


def test_nested_folders_open_only_when_their_condition_holds(space):
    assert pac.nested_under(space)["pur"] == ["auth", "cons", "fic"]
    assert "auth" not in pac.reachable(["act", "pur"], {"pur": "std"}, space)
    assert "auth" in pac.reachable(["act", "pur"], {"pur": "cyber+data"}, space)
    deep = pac.reachable(["hr"], {"hr": "ins", "scope": "ind"}, space)
    assert {"scope", "fav", "rev"} <= set(deep)


def test_map_fit_picks_the_deepest_matching_category(space):
    fit = lambda code: pac.map_fit(pac.parse_code(code, space)["features"], space)
    assert fit("act=biz pur=std hr=ins scope=ind fav=part rev=n") == "advice/ins/person/other"
    assert fit("pur=cyber+data auth=own") == "security/own"
    assert fit("act=biz pur=std fic=real") == "content/std"


def test_validate_nesting(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    path = tmp_path / "b" / "generator.json"
    g = json.loads(path.read_text())
    dims = {d["key"]: d for d in g["dimensions"]}
    dims["auth"]["under"] = {"dim": "fav", "in": ["zz"]}
    dims["fav"]["under"] = {"dim": "auth", "in": ["own"]}
    path.write_text(json.dumps(g))
    found = " | ".join(pac.validate(tmp_path / "b"))
    assert "unknown value fav=zz" in found and "forms a loop" in found
    g = json.loads((SAMPLE / "generator.json").read_text())
    g["categories"][2]["children"][0]["preset"] = "auth=own lim=y"  # lim is not a folder there
    path.write_text(json.dumps(g))
    assert any("preset key 'lim'" in e for e in pac.validate(tmp_path / "b"))


def test_exam_map_fit_fails_when_cases_fall_outside_the_map(tmp_path):
    shutil.copytree(SAMPLE, tmp_path / "b")
    path = tmp_path / "b" / "generator.json"
    g = json.loads(path.read_text())
    g["categories"] = [c for c in g["categories"] if c["id"] in ("chat", "other")]
    g["categories"][0]["features"] = list(dict.fromkeys(g["categories"][0]["features"] + g["ask_order"]))
    path.write_text(json.dumps(g))
    item = next(c for c in pac.exam(tmp_path / "b", write=False)["checks"] if c["id"] == "map_fit")
    assert not item["passed"] and item["failures"]



@pytest.mark.parametrize(("key", "value"), [("fic", "real"), ("cons", "n")])
def test_map_fit_drops_inapplicable_keys_without_altering_judgment(space, key, value):
    code = f"act=biz pur=std {key}={value}"
    feats = pac.parse_code(code, space)["features"]
    assert pac.fit_detail(feats, space) == {"category": "content/std", "dropped": [key]}
    result = pac.check(code, space)
    assert result["verdict"] == "compliant" and result["violated"] == []


def test_example_conformance_has_full_map_coverage(space):
    codes = [row["code"] for row in pac._conformance(SAMPLE)]
    assert all(pac.map_fit(pac.parse_code(code, space)["features"], space) is not None for code in codes)
    report = pac.gaps(SAMPLE)
    assert report["gaps"] == []
    item = next(c for c in pac.exam(SAMPLE, write=False)["checks"] if c["id"] == "map_fit")
    assert item["score"] == 1
    assert item["detail"]["fits_after_drop"] == [
        {"code": "act=biz pur=std fic=real", "dropped": ["fic"]},
        {"code": "act=biz pur=std cons=n", "dropped": ["cons"]},
    ]


def test_map_fit_refuses_drop_that_changes_judgment(tmp_path):
    bundle = tmp_path / "b"
    shutil.copytree(SAMPLE, bundle)
    judge = bundle / "judge.json"
    data = json.loads(judge.read_bytes())
    data["rules"].append({
        "id": "P-scope-guard", "kind": "prohibition", "source": "Test policy",
        "when": {"dim": "cons", "in": ["n"]}, "next_step": "Stop.",
    })
    judge.write_text(json.dumps(data), encoding="utf-8")
    space = pac.Space(bundle)
    code = "act=biz pur=std cons=n"
    features = pac.parse_code(code, space)["features"]
    assert pac.map_fit(features, space) is None
    assert pac.fit_detail(features, space) == {"category": None, "dropped": []}
    items = pac.gaps(bundle)["gaps"]
    issue = next(i for i in items if i["kind"] == "out_of_scope_effect" and i["evidence"]["code"] == code)
    assert set(issue["keys"]) == {"cons", "pur"}
    assert issue["evidence"]["dropped"] == ["cons"]
    assert issue["evidence"]["original"]["violated"] == ["P-scope-guard"]
    assert issue["evidence"]["core"]["open"] == ["P-scope-guard"]


def test_validate_warns_about_proven_under_conflicts(space):
    rule = {"id": "scope-example", "when": {"all": [
        {"dim": "pur", "in": ["std"]}, {"dim": "pur", "not_in": ["data", "track"]},
        {"dim": "cons", "in": ["n"]},
    ]}}
    assert pac._scope_warnings(rule, space) == [
        "scope-example: condition on 'cons' has no path where its 'under' on 'pur' is true",
    ]
    rule["when"]["all"].pop(1)  # purpose is multi-valued, so std+data is still a witness
    assert not pac._scope_warnings(rule, space)
