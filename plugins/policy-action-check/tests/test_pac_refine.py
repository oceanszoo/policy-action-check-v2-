"""CLI regression tests for deterministic bundle refinement."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "scripts" / "pac.py"
EXAMPLE = PLUGIN.parents[1] / "apps/pac-reader/tests/fixtures/legacy"
PRIVACY_CODE = "act=biz pur=std pr_meta=n"
FRAMING_CODE = "act=biz pur=std fr_meta=y"
VIOLATION_CODE = "act=biz pur=data cons=n"
PRIVACY_EXCEPTION = {"all": [{"dim": "act", "in": ["biz"]}, {"dim": "cons", "in": ["n"]}]}


@pytest.fixture
def bundle(tmp_path):
    root = Path(shutil.copytree(EXAMPLE, tmp_path / "space", ignore=shutil.ignore_patterns("work")))
    # Exercise refinement with genuine coverage misses, not inapplicable boundary facts.
    gen = root / "generator.json"
    data = json.loads(gen.read_bytes())
    for key, value, name in [("fr_meta", "y", "Framing metadata"), ("pr_meta", "n", "Privacy metadata")]:
        data["dimensions"].append({"key": key, "name": name, "values": {value: "Recorded"},
                                   "question": f"Record {name}?", "evidence": "Test record"})
    gen.write_text(json.dumps(data), encoding="utf-8")
    with (root / "conformance.jsonl").open("a", encoding="utf-8") as stream:
        for code in [FRAMING_CODE, PRIVACY_CODE]:
            stream.write(json.dumps({"code": code, "expected": {"verdict": "compliant"}}) + "\n")
    run(root, "manifest")
    return root


def run(bundle, *args, check=True):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--space", str(bundle), *args],
        capture_output=True, text=True, check=check,
    )


def snapshot(bundle):
    return {p.relative_to(bundle): p.read_bytes() for p in bundle.rglob("*") if p.is_file()}


def gaps(bundle, *args):
    return json.loads(run(bundle, "gaps", *args).stdout)


def write_patch(bundle, ops, *, focus=None, based_on=None):
    work = bundle / "work"
    based_on = based_on or hashlib.sha256((work / "gaps.json").read_bytes()).hexdigest()
    (work / "refine_patch.json").write_text(json.dumps({
        "focus": focus,
        "based_on": based_on,
        "ops": ops,
    }), encoding="utf-8")


def map_misses(result):
    return [item for item in result["gaps"] if item["kind"] == "map_miss"]


def operation(bundle, op, **fields):
    result = gaps(bundle, "--write")
    return {
        "op": op,
        "reason": "Exercise the corresponding refine operation on the example.",
        "gaps": [map_misses(result)[-1]["id"]],
        **fields,
    }


def privacy_category(bundle):
    return operation(bundle, "add_category", parent="", node={
        "id": "ordinary-privacy-metadata",
        "name": "Ordinary task with privacy metadata",
        "preset": "pur=std pr_meta=n",
        "features": ["act", "pur", "pr_meta"],
    })


def disagreement_error(process):
    assert process.returncode != 0
    return process.stdout + process.stderr


def test_gaps_includes_all_known_map_misses_even_with_passing_exam(bundle):
    before = snapshot(bundle)
    result = gaps(bundle)
    assert result["exam_passed"]
    misses = map_misses(result)
    assert {item["evidence"]["code"] for item in misses} == {
        FRAMING_CODE, PRIVACY_CODE,
    }
    assert len(misses) == 2
    for item in misses:
        nearest = item["evidence"]["nearest"]
        assert nearest["path"]
        assert isinstance(nearest["preset_conflicts"], list)
        assert isinstance(nearest["unreachable"], list)
    assert snapshot(bundle) == before
    written = gaps(bundle, "--write")
    assert json.loads((bundle / "work" / "gaps.json").read_text()) == written == result


def test_focused_and_unmatched_gaps(bundle):
    result = gaps(bundle, "--focus", "insurance")
    assert "hr" in result["focus_keys"]
    assert all("hr" in item["keys"] for item in result["gaps"])
    process = run(bundle, "gaps", "--focus", "zzzpacinvalidfocus", check=False)
    assert process.returncode == 2
    assert "zzzpacinvalidfocus" in process.stdout + process.stderr


def test_apply_category_records_refinement_and_preserves_exam(bundle):
    write_patch(bundle, [privacy_category(bundle)])
    run(bundle, "apply-patch")
    remaining = map_misses(gaps(bundle))
    assert [item["evidence"]["code"] for item in remaining] == [FRAMING_CODE]
    manifest = json.loads((bundle / "bundle.json").read_text())
    logs = (bundle / "work" / "refine_log.jsonl").read_text().splitlines()
    assert len(logs) == 1
    log = json.loads(logs[0])
    assert log["ops"] == {"add_category": 1}
    assert log["gaps_before"]["map_miss"] == 2
    assert log["gaps_after"]["map_miss"] == 1
    assert log["exam_passed"] is True
    assert manifest["refined"] == [{k: log[k] for k in ("date", "round", "focus", "ops")}]
    assert (bundle / "work" / "refine_backup" / str(log["round"]) / "generator.json").is_file()


def test_dry_run_and_stale_patch_do_not_write(bundle):
    op = privacy_category(bundle)
    write_patch(bundle, [op])
    before = snapshot(bundle)
    output = run(bundle, "apply-patch", "--dry-run").stdout
    assert "generator.json" in output
    assert "shrink" in output.lower() or "shrank" in output.lower()
    assert snapshot(bundle) == before
    write_patch(bundle, [op], based_on="0" * 64)
    before = snapshot(bundle)
    assert "gaps changed, re-run gaps" in disagreement_error(run(bundle, "apply-patch", check=False))
    assert snapshot(bundle) == before


def test_reapplying_same_patch_refuses_changed_bundle_without_writes(bundle):
    write_patch(bundle, [privacy_category(bundle)])
    work = bundle / "work"
    stored = json.loads((work / "gaps.json").read_bytes())
    assert stored["files"] == {
        name: hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        for name in ("generator.json", "judge.json", "conformance.jsonl")
    }
    run(bundle, "apply-patch")
    before = snapshot(bundle)
    for args in ((), ("--dry-run",)):
        result = run(bundle, "apply-patch", *args, check=False)
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"] == "bundle changed since gaps, re-run gaps"
        assert snapshot(bundle) == before


def test_unguarded_conformance_change_refused_without_writes(bundle):
    op = operation(bundle, "add_exception", rule="P-privacy",
                   exception=PRIVACY_EXCEPTION)
    write_patch(bundle, [op])
    before = snapshot(bundle)
    assert VIOLATION_CODE in disagreement_error(run(bundle, "apply-patch", check=False))
    assert snapshot(bundle) == before


def test_revise_rule_changes_only_authorized_conformance(bundle):
    expected = {"verdict": "compliant", "violated": [], "required_next": [], "open": []}
    op = operation(bundle, "revise_rule", rule="P-privacy",
                   changes={"exceptions": [PRIVACY_EXCEPTION]},
                   expected_changes=[{"code": VIOLATION_CODE, "expected": expected}])
    write_patch(bundle, [op])
    run(bundle, "apply-patch")
    path = bundle / "conformance.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert [row["expected"] for row in rows if row["code"] == VIOLATION_CODE] == [expected]


@pytest.mark.parametrize(("op", "fields", "error"), [
    ("add_value", {"dim": "not-a-dim", "value": "x", "meaning": "Value X"}, "not-a-dim"),
    ("add_category", {"parent": "", "node": {"id": "chat", "name": "Duplicate"}}, "chat"),
    ("add_rule", {"rule": {
        "id": "P-no-source", "kind": "prohibition", "source_terms": ["privacy"],
        "next_step": "Stop.", "title": "Missing source", "when": {"dim": "pur", "in": ["data"]},
    }}, "source"),
])
def test_invalid_op_leaves_bundle_unchanged(bundle, op, fields, error):
    valid = privacy_category(bundle)
    invalid = operation(bundle, op, **fields)
    write_patch(bundle, [valid, invalid])
    before = snapshot(bundle)
    assert error in disagreement_error(run(bundle, "apply-patch", check=False))
    assert snapshot(bundle) == before


def test_incorrect_expected_change_refused_without_writes(bundle):
    expected = {"verdict": "needs_info", "violated": [], "required_next": [], "open": []}
    op = operation(bundle, "revise_rule", rule="P-privacy",
                   changes={"exceptions": [PRIVACY_EXCEPTION]},
                   expected_changes=[{"code": VIOLATION_CODE, "expected": expected}])
    write_patch(bundle, [op])
    before = snapshot(bundle)
    assert VIOLATION_CODE in disagreement_error(run(bundle, "apply-patch", check=False))
    assert snapshot(bundle) == before


@pytest.mark.parametrize("field", ["reason", "gaps"])
def test_op_metadata_is_required(bundle, field):
    op = privacy_category(bundle)
    del op[field]
    write_patch(bundle, [op])
    before = snapshot(bundle)
    assert field in disagreement_error(run(bundle, "apply-patch", check=False))
    assert snapshot(bundle) == before
