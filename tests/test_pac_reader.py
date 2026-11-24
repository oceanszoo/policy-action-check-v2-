"""The JS bundle reader (apps/pac-reader) must agree exactly with pac.py, and its build must be current."""

import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "apps" / "pac-reader"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def run(*args):
    return subprocess.run([NODE, *args], cwd=APP, capture_output=True, text=True, timeout=600, check=False)


def test_build_outputs_are_current():
    res = run("build.mjs", "--check")
    assert res.returncode == 0, res.stderr


def test_js_reader_matches_reference_engine():
    res = run("tests/parity.mjs")
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize("filename", ["index.html", "dist/pac-reader.html"])
def test_file_picker_accepts_bundle_guides(filename):
    class Picker(HTMLParser):
        accepts = ""

        def handle_starttag(self, tag, attrs):
            fields = dict(attrs)
            if tag == "input" and fields.get("id") == "pick-files":
                self.accepts = fields.get("accept", "")

    html = Picker()
    html.feed((APP / filename).read_text(encoding="utf-8"))
    assert ".md" in {item.strip() for item in html.accepts.split(",")}
