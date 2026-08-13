# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Portable custom-workflow contract and execution tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from samsarix_narrative_engine import (
    BudgetExceededError,
    InputValidationError,
    NarrativeEngine,
    TokenUsage,
    WorkflowDefinition,
    WorkflowRunOptions,
    WorkflowStage,
    build_workflow_plan,
    dumps_run_bundle,
    dumps_workflow,
    load_run_bundle,
    load_workflow,
    loads_run_bundle,
    loads_workflow,
)
from samsarix_narrative_engine.cli import main

from .conftest import ScriptedProvider


def _workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="studio.scene-revision",
        name="Studio scene revision",
        stages=(
            WorkflowStage(
                stage_id="diagnosis",
                role="Scene diagnostician",
                system_prompt=(
                    "Identify the scene goal, conflict, turn, and concrete revision risks."
                ),
                max_output_tokens=600,
            ),
            WorkflowStage(
                stage_id="revision",
                role="Scene reviser",
                system_prompt="Return the complete revised scene with one Markdown H1 title.",
                max_output_tokens=1_800,
                context_from=("diagnosis",),
            ),
        ),
    )


def test_workflow_round_trip_file_loading_and_suffix_plan(tmp_path: Path) -> None:
    workflow = _workflow()
    payload = dumps_workflow(workflow)
    assert loads_workflow(payload) == workflow
    assert workflow.fingerprint.startswith("sha256:")
    assert workflow.fingerprint != replace(workflow, name="Renamed").fingerprint

    path = tmp_path / "workflow.json"
    path.write_text(payload, encoding="utf-8")
    assert load_workflow(path) == workflow

    plan = build_workflow_plan(workflow)
    assert plan.preset == workflow.workflow_id
    assert plan.workflow_id == workflow.workflow_id
    assert plan.to_dict()["workflow_id"] == workflow.workflow_id
    assert plan.max_calls == 2
    assert plan.max_output_tokens == 2_400
    suffix = build_workflow_plan(workflow, "revision")
    assert suffix.max_calls == 1
    assert suffix.max_output_tokens == 1_800


@pytest.mark.parametrize(
    ("filename", "workflow_id", "calls", "output_tokens"),
    (
        ("game-quest-production.json", "game.quest-production", 5, 7_600),
        ("editorial-scene-revision.json", "editorial.scene-revision", 4, 5_500),
    ),
)
def test_checked_in_workflows_are_valid_and_bounded(
    filename: str,
    workflow_id: str,
    calls: int,
    output_tokens: int,
) -> None:
    path = Path(__file__).parents[1] / "examples" / "workflows" / filename
    workflow = load_workflow(path)
    plan = build_workflow_plan(workflow)
    assert workflow.workflow_id == workflow_id
    assert plan.max_calls == calls
    assert plan.max_output_tokens == output_tokens


def test_published_schemas_are_json_schema_2020_12_documents() -> None:
    schema_root = Path(__file__).parents[1] / "schemas"
    workflow_schema = json.loads((schema_root / "workflow-v1.schema.json").read_text("utf-8"))
    run_schema = json.loads((schema_root / "run-v1.schema.json").read_text("utf-8"))
    expected_dialect = "https://json-schema.org/draft/2020-12/schema"
    assert workflow_schema["$schema"] == expected_dialect
    assert run_schema["$schema"] == expected_dialect
    assert workflow_schema["properties"]["schema"]["const"] == "samsarix.workflow/v1"
    assert run_schema["properties"]["schema"]["const"] == "samsarix.run/v1"
    assert "workflow_id" in run_schema["required"]
    assert run_schema["properties"]["workflow"]["$ref"] == "./workflow-v1.schema.json"


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda data: data.update(schema="other"), "schema"),
        (lambda data: data.update(extra=True), "unknown fields"),
        (lambda data: data.update(id="Uppercase"), "workflow_id"),
        (lambda data: data.update(name=""), "name"),
        (lambda data: data["stages"][0].update(extra=True), "unknown fields"),
        (lambda data: data["stages"][0].update(id="bad.id"), "stage_id"),
        (lambda data: data["stages"][0].update(max_output_tokens=True), "integer"),
        (lambda data: data["stages"][0].update(context_from="diagnosis"), "array"),
        (
            lambda data: data["stages"][0].update(context_from=["revision"]),
            "earlier stages",
        ),
        (
            lambda data: data["stages"][1].update(context_from=["diagnosis", "diagnosis"]),
            "duplicate",
        ),
        (lambda data: data.update(stages=[]), "between 1 and 20"),
    ),
)
def test_workflow_loader_rejects_malformed_definitions(
    mutate: Any,
    message: str,
) -> None:
    data = _workflow().to_dict()
    mutate(data)
    with pytest.raises(InputValidationError, match=message):
        loads_workflow(json.dumps(data))


def test_workflow_validation_rejects_duplicates_caps_and_wrong_runtime_types() -> None:
    stage = _workflow().stages[0]
    with pytest.raises(ValueError, match="duplicate workflow stage"):
        replace(_workflow(), stages=(stage, stage))
    with pytest.raises(ValueError, match="100000"):
        replace(
            _workflow(),
            stages=tuple(
                replace(stage, stage_id=f"stage_{index}", max_output_tokens=25_001)
                for index in range(4)
            ),
        )
    with pytest.raises(ValueError, match="WorkflowStage"):
        WorkflowDefinition(
            workflow_id="invalid",
            name="Invalid",
            stages=cast(tuple[WorkflowStage, ...], ("not-a-stage",)),
        )
    with pytest.raises(ValueError, match="tuple"):
        replace(stage, context_from=cast(tuple[str, ...], ["diagnosis"]))
    with pytest.raises(ValueError, match="system_prompt"):
        replace(stage, system_prompt="bad\x00prompt")
    with pytest.raises(ValueError, match="stage role"):
        replace(stage, role="bad\x00role")
    with pytest.raises(ValueError, match="workflow name"):
        replace(_workflow(), name="bad\x00name")
    with pytest.raises(ValueError, match="32768"):
        replace(stage, max_output_tokens=32_769)
    with pytest.raises(ValueError, match="integers"):
        TokenUsage(input_tokens=True)


def test_workflow_loader_sanitizes_json_file_and_size_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(InputValidationError, match="line 1, column 2"):
        loads_workflow("{")
    with pytest.raises(InputValidationError, match="JSON object"):
        loads_workflow("[]")
    with pytest.raises(InputValidationError, match="must be text"):
        loads_workflow(42)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="WorkflowDefinition"):
        dumps_workflow(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="WorkflowDefinition"):
        build_workflow_plan(object())  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="non-empty"):
        build_workflow_plan(_workflow(), "")

    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(b"\xff")
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_workflow(invalid)
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_workflow(tmp_path / "missing.json")

    monkeypatch.setattr("samsarix_narrative_engine.workflows.MAX_WORKFLOW_BYTES", 10)
    with pytest.raises(InputValidationError, match="exceeds 10 bytes"):
        dumps_workflow(_workflow())


@pytest.mark.integration
async def test_custom_workflow_runs_round_trips_and_resumes_edited_context() -> None:
    workflow = _workflow()
    provider = ScriptedProvider(("Diagnosis artifact", "# Revised Scene\nFirst revision"))
    result = await NarrativeEngine(provider).run(
        "A diplomat must choose between peace and a true accusation.",
        workflow,
        WorkflowRunOptions(max_calls=2, max_total_output_tokens=2_400),
    )

    assert result.preset == workflow.workflow_id
    assert result.workflow_id == workflow.workflow_id
    assert result.workflow == workflow
    assert result.workflow_fingerprint == workflow.fingerprint
    assert '"diagnosis": "Diagnosis artifact"' in provider.calls[1][0][1].content
    loaded = loads_run_bundle(dumps_run_bundle(result))
    assert loaded == result

    editable = loaded.to_dict()
    editable["stages"][0]["content"] = "Edited diagnosis: the accusation risks a fragile truce."
    edited = loads_run_bundle(json.dumps(editable))
    resume_provider = ScriptedProvider(("# Revised Scene\nSecond revision",))
    branch = await NarrativeEngine(resume_provider).resume(
        edited,
        "revision",
        WorkflowRunOptions(max_calls=1, max_total_output_tokens=1_800),
    )
    assert branch.parent_generation_id == result.generation_id
    assert "Edited diagnosis" in resume_provider.calls[0][0][1].content
    assert branch.workflow == workflow


async def test_custom_workflow_budget_and_drift_checks_prevent_provider_calls() -> None:
    workflow = _workflow()
    provider = ScriptedProvider(())
    with pytest.raises(BudgetExceededError, match="requires 2 calls"):
        await NarrativeEngine(provider).run(
            "Prompt",
            workflow,
            WorkflowRunOptions(max_calls=1, max_total_output_tokens=2_400),
        )
    assert provider.calls == []

    original = await NarrativeEngine(ScriptedProvider(("Diagnosis", "# Scene\nDraft"))).run(
        "Prompt", workflow
    )
    changed = replace(
        workflow,
        stages=(
            workflow.stages[0],
            replace(workflow.stages[1], system_prompt="A reviewed changed revision prompt."),
        ),
    )
    resume_provider = ScriptedProvider(("# Scene\nChanged",))
    with pytest.raises(InputValidationError, match="differs"):
        await NarrativeEngine(resume_provider).resume(
            original,
            "revision",
            WorkflowRunOptions(max_calls=1, max_total_output_tokens=1_800),
            workflow=changed,
        )
    assert resume_provider.calls == []

    branch = await NarrativeEngine(resume_provider).resume(
        original,
        "revision",
        WorkflowRunOptions(max_calls=1, max_total_output_tokens=1_800),
        workflow=changed,
        allow_workflow_change=True,
    )
    assert branch.workflow == changed
    assert loads_run_bundle(dumps_run_bundle(branch)) == branch

    changed_prefix = replace(
        workflow,
        stages=(
            replace(workflow.stages[0], system_prompt="A changed diagnosis prompt."),
            workflow.stages[1],
        ),
    )
    prefix_provider = ScriptedProvider(("# Scene\nShould not run",))
    with pytest.raises(InputValidationError, match="changed in reused stage 'diagnosis'"):
        await NarrativeEngine(prefix_provider).resume(
            original,
            "revision",
            WorkflowRunOptions(max_calls=1, max_total_output_tokens=1_800),
            workflow=changed_prefix,
            allow_workflow_change=True,
        )
    assert prefix_provider.calls == []


def test_cli_plans_generates_and_resumes_custom_workflow(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(dumps_workflow(_workflow()), encoding="utf-8")

    assert main(("plan", "--workflow", str(workflow_path), "--json")) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["workflow_id"] == "studio.scene-revision"
    assert plan["max_calls"] == 2
    assert plan["workflow_fingerprint"] == _workflow().fingerprint

    source = tmp_path / "run.json"
    provider = ScriptedProvider(("Diagnosis", "# Scene\nDraft"))
    assert (
        main(
            (
                "generate",
                "--prompt",
                "A scene in need of revision.",
                "--workflow",
                str(workflow_path),
                "--artifacts",
                str(source),
                "--max-calls",
                "2",
                "--max-total-output-tokens",
                "2400",
            ),
            provider_factory=lambda *_args, **_kwargs: provider,
        )
        == 0
    )
    capsys.readouterr()
    assert load_run_bundle(source).workflow == _workflow()

    branch_path = tmp_path / "branch.json"
    resume_provider = ScriptedProvider(("# Scene\nBranch",))
    assert (
        main(
            (
                "resume",
                "--artifacts-in",
                str(source),
                "--from-stage",
                "revision",
                "--artifacts-out",
                str(branch_path),
                "--max-calls",
                "1",
                "--max-total-output-tokens",
                "1800",
            ),
            provider_factory=lambda *_args, **_kwargs: resume_provider,
        )
        == 0
    )
    assert (
        load_run_bundle(branch_path).parent_generation_id == load_run_bundle(source).generation_id
    )
