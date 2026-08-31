# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Portable custom workflow loading, planning, and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ._inputs import parse_json_object, read_utf8_file
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

    decoded = parse_json_object(payload, max_bytes=MAX_WORKFLOW_BYTES, label="workflow")
    try:
        return WorkflowDefinition.from_dict(decoded)
    except ValueError as error:
        raise InputValidationError(f"invalid workflow: {error}") from error


def load_workflow(path: str | Path) -> WorkflowDefinition:
    """Load one UTF-8 workflow file with a fixed size ceiling."""

    payload = read_utf8_file(path, max_bytes=MAX_WORKFLOW_BYTES, label="workflow")
    return loads_workflow(payload)
