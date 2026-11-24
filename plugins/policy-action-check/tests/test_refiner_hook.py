"""Checks for the space-refiner subagent stop hook."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pac


@pytest.mark.parametrize("refused", [False, True])
def test_space_refiner_stop_hook_dry_runs_patch(tmp_path, monkeypatch, refused):
    monkeypatch.setenv("PAC_SPACE", str(tmp_path))
    calls = []

    def simulate_apply_patch(root, dry_run=False):
        calls.append((root, dry_run))
        if refused:
            raise pac.SpaceError("gaps changed, re-run gaps")
        return {}

    monkeypatch.setattr(pac, "apply_patch", simulate_apply_patch)
    result = pac.hook_subagent_stop({"agent_type": "policy-action-check:space-refiner"})
    assert calls == [(tmp_path, True)]
    if refused:
        assert result["decision"] == "block"
        assert "gaps changed, re-run gaps" in result["reason"]
    else:
        assert result is None
