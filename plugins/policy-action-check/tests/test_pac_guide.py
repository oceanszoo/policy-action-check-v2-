"""Tests for the self-contained bundle guide."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "pac.py"
sys.path.insert(0, str(ENGINE.parent))
import pac


@pytest.fixture
def bundle(tmp_path):
    return shutil.copytree(ROOT.parents[1] / "apps/pac-reader/tests/fixtures/legacy", tmp_path / "bundle")


def guide_cli(bundle, *args):
    return subprocess.run([sys.executable, str(ENGINE), "--space", str(bundle), "guide", *args],
                          capture_output=True, text=True, check=False)


def test_guide_deterministic_and_detects_even_invisible_generator_edit(bundle):
    path = bundle / "BUNDLE.md"
    path.unlink()
    assert guide_cli(bundle, "--check").returncode == 1
    assert any("BUNDLE.md missing" in e for e in pac.validate(bundle))
    assert guide_cli(bundle).returncode == 0
    first = path.read_bytes()
    assert first.endswith(b"\n") and not first.endswith(b"\n\n") and b"\r" not in first
    assert guide_cli(bundle).returncode == 0
    assert guide_cli(bundle, "--check").returncode == 0
    assert path.read_bytes() == first
    generator = bundle / "generator.json"
    generator.write_bytes(generator.read_bytes() + b" ")
    assert guide_cli(bundle, "--check").returncode == 1
    assert any("BUNDLE.md stale" in e for e in pac.validate(bundle))


def test_guide_shows_every_path_feature_and_rule(bundle):
    sp = pac.Space(bundle)
    text = pac.render_guide(bundle).decode("utf-8")
    for marker in ("Case map", "Features", "Rules", "Examples", "Saved codes", "Self-exam"):
        assert f"## {marker}\n" in text
    paths = [node["path"] for node in pac.category_nodes(pac.categories(sp))]
    positions = [text.index(f"`{path}`") for path in paths]
    assert positions == sorted(positions)
    assert all(f"- `{key}`" in text for key in sp.dims)
    assert all(f"| `{rule['id']}` |" in text for rule in sp.rules["rules"])
    assert "self-exam: passed" in text
    assert "not legal advice" in text


def test_manifest_regenerates_guide_and_includes_its_digest(bundle):
    (bundle / "BUNDLE.md").write_text("stale\n", encoding="utf-8")
    assert any("BUNDLE.md stale" in e for e in pac.validate(bundle))
    assert not pac.exam(bundle, write=False)["passed"]
    pac.write_manifest(bundle)
    assert pac.exam(bundle)["passed"]
    man = pac.write_manifest(bundle)
    expected_hash = hashlib.sha256((bundle / "BUNDLE.md").read_bytes()).hexdigest()
    assert man["files"]["BUNDLE.md"] == expected_hash
    assert json.loads((bundle / "bundle.json").read_bytes())["files"]["BUNDLE.md"] == expected_hash
    assert guide_cli(bundle, "--check").returncode == 0
    assert not pac.validate(bundle)



def test_crlf_copy_fails_exact_digest_and_guide_checks_with_windows_hint(bundle):
    names = ("generator.json", "judge.json", "conformance.jsonl", "BUNDLE.md")
    for path in bundle.iterdir():
        if path.suffix in {".json", ".jsonl", ".md"}:
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    errs = pac.validate(bundle)
    assert len(errs) == len(names)
    for name in names:
        assert any(err.startswith(f"{name}: line endings changed (CRLF)") and ".gitattributes" in err for err in errs)
    result = guide_cli(bundle, "--check")
    assert result.returncode == 1 and "BUNDLE.md: line endings changed (CRLF)" in result.stderr
    exam = pac.exam(bundle, write=False)
    assert not exam["passed"]
    assert {err.split(":")[0] for err in exam["checks"][0]["failures"]} == set(names)
    assert all("line endings changed (CRLF)" in err for err in exam["checks"][0]["failures"])


def test_real_content_edit_is_not_a_crlf_only_mismatch(bundle):
    path = bundle / "generator.json"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b" ")
    errs = pac.validate(bundle)
    assert any("generator.json: digest mismatch" in err for err in errs)
    assert not any("line endings changed" in err for err in errs)
    result = guide_cli(bundle, "--check")
    assert result.returncode == 1 and "BUNDLE.md stale" in result.stderr
    assert "line endings changed" not in result.stderr



def test_guide_check_identifies_crlf_in_only_a_core_file(bundle):
    path = bundle / "judge.json"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    result = guide_cli(bundle, "--check")
    assert result.returncode == 1
    assert result.stderr.startswith("judge.json: line endings changed (CRLF)")
    assert "BUNDLE.md stale" not in result.stderr
