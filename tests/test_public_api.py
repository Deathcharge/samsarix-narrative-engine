"""Public package shape and model behavior tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import helix_narrative_engine as helix
from helix_narrative_engine.models import NarrativeResult, StageResult, TokenUsage


def test_public_api_version_and_exports() -> None:
    assert helix.__version__ == "0.1.0"
    assert "NarrativeEngine" in helix.__all__
    assert "OpenAIProvider" in helix.__all__
    assert Path(helix.__file__).with_name("py.typed").is_file()


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
