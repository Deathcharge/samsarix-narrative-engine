# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Portable custom workflow loading, planning, and validation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

from .exceptions import InputValidationError
from .models import GenerationPlan, PlannedStage, WorkflowDefinition

MAX_WORKFLOW_BYTES = 1024 * 1024


def build_workflow_plan(
    workflow: WorkflowDefinition,
    from_stage: Optional[str] = None,
) -> GenerationPlan:
    """Build a complete workflow plan or a suffix beginning at from_stage."""

    if not isinstance(workflow, WorkflowDefinition):
        raise TypeError("workflow must be a WorkflowDefinition")
    start = 0
    if from_stage is not None:
        if not isinstance(from_stage, str) or not from_stage.strip():
            raise InputValidationError("from_stage must be a non-empty string")
        stage_ids = tuple(stage.stage_id for stage in workflow.stages)
        try:
            start = stage_ids.index(from_stage)
        except ValueError as error:
            choices = ", ".join(stage_ids)
            raise InputValidationError(
                f"stage '{from_stage}' is not in workflow '{workflow.workflow_id}'; "
                f"choose one of: {choices}"
            ) from error
    stages = tuple(
        PlannedStage(
            stage_id=stage.stage_id,
            role=stage.role,
            max_output_tokens=stage.max_output_tokens,
        )
        for stage in workflow.stages[start:]
    )
    return GenerationPlan(preset=workflow.workflow_id, stages=stages)


def dumps_workflow(workflow: WorkflowDefinition, *, indent: int = 2) -> str:
    """Serialize one validated workflow as human-editable JSON."""

    if not isinstance(workflow, WorkflowDefinition):
        raise TypeError("workflow must be a WorkflowDefinition")
    payload = json.dumps(workflow.to_dict(), ensure_ascii=False, indent=indent) + "\n"
    if len(payload.encode("utf-8")) > MAX_WORKFLOW_BYTES:
        raise InputValidationError(f"workflow exceeds {MAX_WORKFLOW_BYTES} bytes")
    return payload


def loads_workflow(payload: str) -> WorkflowDefinition:
    """Load one strict workflow definition from JSON text."""

    if not isinstance(payload, str):
        raise InputValidationError("workflow payload must be text")
    if len(payload.encode("utf-8")) > MAX_WORKFLOW_BYTES:
        raise InputValidationError(f"workflow exceeds {MAX_WORKFLOW_BYTES} bytes")
    try:
        decoded: Any = json.loads(payload)
    except json.JSONDecodeError as error:
        raise InputValidationError(
            f"invalid workflow JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(decoded, Mapping):
        raise InputValidationError("workflow must contain a JSON object")
    try:
        return WorkflowDefinition.from_dict(decoded)
    except ValueError as error:
        raise InputValidationError(f"invalid workflow: {error}") from error


def load_workflow(path: str | Path) -> WorkflowDefinition:
    """Load one UTF-8 workflow file with a fixed size ceiling."""

    selected = Path(path)
    try:
        if selected.stat().st_size > MAX_WORKFLOW_BYTES:
            raise InputValidationError(f"workflow exceeds {MAX_WORKFLOW_BYTES} bytes")
        payload = selected.read_text(encoding="utf-8")
    except InputValidationError:
        raise
    except (OSError, UnicodeError) as error:
        raise InputValidationError(
            f"cannot read UTF-8 workflow ({type(error).__name__})"
        ) from error
    return loads_workflow(payload)
