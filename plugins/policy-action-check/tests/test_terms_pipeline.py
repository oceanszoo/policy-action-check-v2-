"""Terms-first scope and verifier regressions independent of any shipped bundle."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pac


def write_work(root, name, doc):
    path = root / "work" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def test_terms_first_scope_ask_requires_specific_question(tmp_path):
    section = {"area": "Site access", "source_terms": ["c001"], "decision": "ask"}
    scope = {"version": "2.0", "duty": {"parties": ["visitor"]}, "areas": [section]}
    write_work(tmp_path, "scope.json", scope)
    assert any("question" in e for e in pac.validate(tmp_path, "scope"))

    section["question"] = "Do visitors access the equipment room?"
    write_work(tmp_path, "scope.json", scope)
    assert pac.validate(tmp_path, "scope") == []


def test_terms_first_verifier_checks_keys_before_compilation(tmp_path, monkeypatch):
    monkeypatch.setenv("PAC_SPACE", str(tmp_path))
    write_work(tmp_path, "scope.json", {
        "version": "2.0", "duty": {"parties": ["visitor"]}, "areas": [],
    })
    write_work(tmp_path, "terms.json", {"clauses": [{
        "id": "c001", "class": "prohibition", "confidence": "high", "binds": "visitor",
        "text": "Visitors must not enter the red room.",
    }]})
    key = {"id": "k1", "dim": "room", "in": ["red"], "anchor": "enter the red room"}
    keys = {
        "dimensions": [{
            "key": "room", "name": "room", "values": {"red": "red room", "blue": "blue room"},
            "question": "Which room?", "evidence": "The room assignment",
        }],
        "terms": {"c001": {
            "role": "prohibition", "parents": [], "binds": "visitor",
            "title": "Red room", "next_step": "Do not enter.", "gate": [key],
        }},
    }
    write_work(tmp_path, "keys.json", keys)
    payload = {"agent_type": "policy-action-check:space-verifier"}
    assert not (tmp_path / "generator.json").exists()
    assert pac.hook_subagent_stop(payload) is None

    key["anchor"] = "a phrase absent from the policy"
    write_work(tmp_path, "keys.json", keys)
    result = pac.hook_subagent_stop(payload)
    assert result["decision"] == "block"
    assert "anchor" in result["reason"]
