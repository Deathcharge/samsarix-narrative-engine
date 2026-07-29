# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Public package shape and model behavior tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import samsarix_narrative_engine as samsarix
from samsarix_narrative_engine.models import NarrativeResult, StageResult, TokenUsage


def test_public_api_version_and_exports() -> None:
    assert samsarix.__version__ == "0.1.0"
    assert "NarrativeEngine" in samsarix.__all__
    assert "OpenAIProvider" in samsarix.__all__
    assert Path(samsarix.__file__).with_name("py.typed").is_file()


def test_token_usage_addition_and_validation() -> None:
    assert TokenUsage(1, 2, 3) + TokenUsage(4, 5, 9) == TokenUsage(5, 7, 12)
    assert TokenUsage(1, 2, 3).to_dict()["total_tokens"] == 3
    with pytest.raises(ValueError, match="negative"):
        TokenUsage(-1, 0, 0)


def test_result_cost_none_without_reported_usage() -> None:
    stage = StageResult(
        stage_id="writer",
        role="writer",
        content="# T\nS",
        provider="custom",
        model="unknown",
        usage=TokenUsage(),
        duration_ms=1,
        max_output_tokens=10,
    )
    result = NarrativeResult(
        generation_id="nar_test",
        created_at=datetime.now(timezone.utc).isoformat(),
        preset="quick",
        title="T",
        content="# T\nS",
        stages=(stage,),
    )
    assert result.estimated_cost(1, 1) is None
