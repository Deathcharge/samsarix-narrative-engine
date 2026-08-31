# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Verify the advertised copy-paste offline journey against production APIs."""

import json
from pathlib import Path

import pytest

from examples.offline_workflow import CORRECTION, run_demo
from samsarix_narrative_engine import load_run_bundle


@pytest.mark.integration
def test_offline_generate_edit_resume_review_journey(tmp_path: Path) -> None:
    destination = tmp_path / "walkthrough"
    run_demo(destination)
    baseline = load_run_bundle(destination / "baseline.json")
    branch = load_run_bundle(destination / "branch.json")
    assert branch.parent_generation_id == baseline.generation_id
    assert branch.stages[:3] == baseline.stages[:3]
    assert branch.stages[3].content == CORRECTION
    assert "bell_owned=true" in branch.content
    assert baseline.usage.total_tokens == branch.usage.total_tokens == 0
    report = json.loads((destination / "sample-report.json").read_text(encoding="utf-8"))
    assert report["reviewer"] == "SYNTHETIC-WIRING-CHECK-NOT-HUMAN"
    assert report["case_count"] == report["ties"] == 1
    blank = json.loads((destination / "scores.json").read_text(encoding="utf-8"))
    assert blank["cases"][0]["preference"] is None
    with pytest.raises(FileExistsError):
        run_demo(destination)
    assert load_run_bundle(destination / "baseline.json") == baseline
