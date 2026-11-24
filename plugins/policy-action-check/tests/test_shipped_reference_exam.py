"""The references exam can run on shipped terms with no pipeline work files."""

import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import pac


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_references_exam_reads_embedded_links_and_waivers(tmp_path):
    root = tmp_path / "space"
    write(root / "generator.json", {"format": "pac-generator", "version": "1.6", "dimensions": []})
    judge = {"format": "pac-judge", "version": "1.6",
             "rules": [{"id": "P-release", "source_terms": ["base"]}]}
    path = root / "judge.json"
    write(path, judge)
    terms = root / "work/terms.json"
    write(terms, {"source": "Release handbook", "clauses": [
        {"id": "base", "class": "prohibition", "text": "Release is subject to the Supplier Agreement.",
         "refs": [{"to": None, "kind": "subject_to", "text": "subject to the Supplier Agreement",
                   "external": "Supplier Agreement"}]},
        {"id": "exception", "class": "permission_exception", "text": "Allow release to auditors.",
         "refs": [{"to": "base", "kind": "modifies", "text": "Allow release to auditors"}]},
    ]})

    def exam():
        return pac.exam_references(root, pac.Space(root), pac.EXAM_THRESHOLDS)

    before = exam()
    assert before["failure_count"] == 2
    pac.embed_terms(root)
    terms.unlink()
    assert exam() == before
    embedded = json.loads(path.read_text(encoding="utf-8"))
    embedded["not_encoded"] = [
        {"clause": "base", "ref": "subject to the Supplier Agreement", "reason": "Separately checked."},
        {"clause": "exception", "reason": "Auditors are not in the scope of this bundle."},
    ]
    write(path, embedded)
    check = exam()
    assert check["passed"] and check["score"] == 1.0
    assert not check["skipped"]
