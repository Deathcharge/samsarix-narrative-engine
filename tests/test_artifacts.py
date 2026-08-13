# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Versioned run-bundle serialization and validation tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from samsarix_narrative_engine import (
    RUN_BUNDLE_SCHEMA,
    InputValidationError,
    NarrativeResult,
    StageResult,
    TokenUsage,
    dumps_run_bundle,
    load_run_bundle,
    loads_run_bundle,
    workflow_fingerprint,
    workflow_for_preset,
)


def _result() -> NarrativeResult:
    return NarrativeResult(
        generation_id="nar_fixture",
        created_at="2026-08-08T12:00:00+00:00",
        preset="quick",
        title="Fixture",
        content="# Fixture\nStory",
        stages=(
            StageResult(
                stage_id="architect",
                role="Story architect",
                content="Blueprint",
                provider="fixture",
                model="fixture-v1",
                usage=TokenUsage(10, 5, 15),
                duration_ms=1,
                max_output_tokens=1_000,
            ),
            StageResult(
                stage_id="writer",
                role="Draft writer",
                content="# Fixture\nStory",
                provider="fixture",
                model="fixture-v1",
                usage=TokenUsage(20, 10, 30),
                duration_ms=2,
                max_output_tokens=2_600,
            ),
        ),
        creative_brief="A reproducible fixture.",
        workflow_fingerprint=workflow_fingerprint("quick"),
        workflow=workflow_for_preset("quick"),
    )


def test_run_bundle_round_trip_and_file_loading(tmp_path: Path) -> None:
    original = _result()
    payload = dumps_run_bundle(original)
    assert json.loads(payload)["schema"] == RUN_BUNDLE_SCHEMA
    assert loads_run_bundle(payload) == original

    path = tmp_path / "run.json"
    path.write_text(payload, encoding="utf-8")
    assert load_run_bundle(path) == original


@pytest.mark.parametrize(
    ("update", "message"),
    (
        ({"schema": "unknown"}, "schema"),
        ({"unexpected": True}, "unknown fields"),
        ({"created_at": "not-a-time"}, "created_at"),
        ({"workflow_fingerprint": "sha256:nope"}, "workflow_fingerprint"),
        ({"workflow_id": "other"}, "workflow_id"),
        ({"creative_brief": ""}, "creative_brief"),
        ({"stages": []}, "stages"),
        ({"usage": {"input_tokens": 999, "output_tokens": 0, "total_tokens": 0}}, "usage"),
        ({"usage": None}, "usage"),
    ),
)
def test_run_bundle_rejects_invalid_top_level_fields(update: dict[str, Any], message: str) -> None:
    data = _result().to_dict()
    data.update(update)
    with pytest.raises(InputValidationError, match=message):
        loads_run_bundle(json.dumps(data))


def test_run_bundle_rejects_duplicate_and_invalid_stage_fields() -> None:
    data = _result().to_dict()
    data["stages"].append(dict(data["stages"][0]))
    with pytest.raises(InputValidationError, match="unique"):
        loads_run_bundle(json.dumps(data))

    data = _result().to_dict()
    data["stages"][0]["duration_ms"] = True
    with pytest.raises(InputValidationError, match="duration_ms"):
        loads_run_bundle(json.dumps(data))

    data = _result().to_dict()
    data["stages"][0]["unexpected"] = True
    with pytest.raises(InputValidationError, match="unknown fields"):
        loads_run_bundle(json.dumps(data))

    data = _result().to_dict()
    data["usage"]["unexpected"] = 0
    with pytest.raises(InputValidationError, match="unknown fields"):
        loads_run_bundle(json.dumps(data))


def test_run_bundle_rejects_embedded_workflow_and_final_content_mismatches() -> None:
    data = _result().to_dict()
    data["workflow"]["name"] = "Tampered"
    with pytest.raises(InputValidationError, match="does not match"):
        loads_run_bundle(json.dumps(data))

    data = _result().to_dict()
    data["content"] = "Different from the final stage"
    with pytest.raises(InputValidationError, match="final stage"):
        loads_run_bundle(json.dumps(data))


def test_run_bundle_json_file_and_size_errors_are_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(InputValidationError, match="line 1, column 2"):
        loads_run_bundle("{")
    with pytest.raises(InputValidationError, match="JSON object"):
        loads_run_bundle("[]")
    with pytest.raises(InputValidationError, match="must be text"):
        loads_run_bundle(42)  # type: ignore[arg-type]

    invalid_utf8 = tmp_path / "invalid.json"
    invalid_utf8.write_bytes(b"\xff")
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_run_bundle(invalid_utf8)
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_run_bundle(tmp_path / "missing.json")

    monkeypatch.setattr(
        "samsarix_narrative_engine.artifacts.MAX_RUN_BUNDLE_BYTES",
        10,
    )
    with pytest.raises(InputValidationError, match="exceeds 10 bytes"):
        loads_run_bundle(dumps_run_bundle(_result()))


def test_bundle_serialization_requires_a_result() -> None:
    with pytest.raises(TypeError, match="NarrativeResult"):
        dumps_run_bundle(object())  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="cannot form"):
        dumps_run_bundle(replace(_result(), creative_brief=""))


def test_run_bundle_lineage_fields_are_atomic() -> None:
    data = _result().to_dict()
    data["parent_generation_id"] = "nar_parent"
    with pytest.raises(InputValidationError, match="both be set"):
        loads_run_bundle(json.dumps(data))
