# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Core workflow integration, validation, and failure tests."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from typing import cast

import pytest

from samsarix_narrative_engine import (
    BudgetExceededError,
    GenerationOptions,
    InputValidationError,
    Message,
    NarrativeEngine,
    NarrativeResult,
    Provider,
    ProviderError,
    ProviderResponse,
    TokenUsage,
    dumps_run_bundle,
    generate_narrative,
    generateNarrative,
    loads_run_bundle,
    workflow_fingerprint,
)

from .conftest import ScriptedProvider


@pytest.mark.integration
async def test_quick_journey_returns_story_artifacts_and_real_usage(
    scripted_provider: ScriptedProvider,
) -> None:
    result = await NarrativeEngine(scripted_provider).generate("A lighthouse hears a signal.")

    assert result.title == "The Signal"
    assert result.content == "# The Signal\nA complete story."
    assert [stage.stage_id for stage in result.stages] == [
        "architect",
        "character",
        "world",
        "writer",
    ]
    assert result.usage == TokenUsage(input_tokens=40, output_tokens=20, total_tokens=60)
    assert result.generation_id.startswith("nar_")
    assert result.creative_brief == "A lighthouse hears a signal."
    assert result.workflow_fingerprint == workflow_fingerprint("balanced")
    assert result.to_dict()["stages"][0]["content"] == "Blueprint"
    assert len(scripted_provider.calls) == 4


@pytest.mark.integration
async def test_polished_journey_uses_revised_story() -> None:
    provider = ScriptedProvider(
        (
            "Blueprint",
            "Character notes",
            "World notes",
            "Originality notes",
            "# Draft Title\nDraft",
            "Revision memo",
            "# Final Title\nFinal story",
        )
    )
    result = await NarrativeEngine(provider).generate(
        "A courier crosses a flooded city.",
        GenerationOptions(preset="polished"),
    )
    assert result.title == "Final Title"
    assert result.content.endswith("Final story")
    assert len(result.stages) == 7
    assert provider.calls[-1][1] == 2_800


async def test_quick_plan_uses_two_calls_and_fallback_title() -> None:
    provider = ScriptedProvider(("Blueprint", "A titleless first line\nStory"))
    result = await generate_narrative(
        "A small prompt",
        provider,
        GenerationOptions(preset="quick"),
    )
    assert result.title == "A titleless first line"
    assert len(provider.calls) == 2


async def test_compatibility_generation_accepts_explicit_provider() -> None:
    provider = ScriptedProvider(("Blueprint", "# Compatibility\nStory"))
    result = await generateNarrative(
        "Prompt",
        GenerationOptions(preset="quick"),
        provider,
    )
    assert result.title == "Compatibility"


@pytest.mark.parametrize(
    ("prompt", "options", "message"),
    (
        ("", GenerationOptions(), "cannot be empty"),
        (" \n", GenerationOptions(), "cannot be empty"),
        ("bad\x00prompt", GenerationOptions(), "null bytes"),
        ("abcd", GenerationOptions(max_prompt_chars=3), "maximum is 3"),
        ("ok", GenerationOptions(max_prompt_chars=0), "max_prompt_chars"),
        ("ok", GenerationOptions(max_prompt_chars=100_001), "max_prompt_chars"),
        ("ok", GenerationOptions(timeout_seconds=0), "timeout_seconds"),
        ("ok", GenerationOptions(timeout_seconds=float("nan")), "timeout_seconds"),
        ("ok", GenerationOptions(timeout_seconds=601), "timeout_seconds"),
        ("ok", GenerationOptions(max_calls=0), "max_calls"),
        ("ok", GenerationOptions(max_calls=True), "max_calls"),
        ("ok", GenerationOptions(max_calls=21), "max_calls"),
        ("ok", GenerationOptions(max_total_output_tokens=0), "max_total_output_tokens"),
        ("ok", GenerationOptions(max_total_output_tokens=100_001), "max_total_output_tokens"),
        ("ok", GenerationOptions(preset="missing"), "unknown preset"),
        ("ok", GenerationOptions(preset=cast(str, 42)), "preset must be a string"),
    ),
)
async def test_invalid_input_fails_before_provider_call(
    prompt: str,
    options: GenerationOptions,
    message: str,
) -> None:
    provider = ScriptedProvider(())
    with pytest.raises(InputValidationError, match=message):
        await NarrativeEngine(provider).generate(prompt, options)
    assert provider.calls == []


async def test_non_string_prompt_is_rejected() -> None:
    provider = ScriptedProvider(())
    with pytest.raises(InputValidationError, match="must be a string"):
        await NarrativeEngine(provider).generate(cast(str, 42))


@pytest.mark.parametrize(
    "options",
    (
        GenerationOptions(preset="balanced", max_calls=3),
        GenerationOptions(preset="polished", max_total_output_tokens=9_499),
    ),
)
async def test_budget_failure_occurs_before_spend(options: GenerationOptions) -> None:
    provider = ScriptedProvider(())
    with pytest.raises(BudgetExceededError):
        await NarrativeEngine(provider).generate("Prompt", options)
    assert provider.calls == []


async def test_provider_failure_is_sanitized() -> None:
    provider = ScriptedProvider((), error=RuntimeError("secret prompt and credential"))
    with pytest.raises(ProviderError) as caught:
        await NarrativeEngine(provider).generate("Prompt", GenerationOptions(preset="quick"))
    assert "secret" not in str(caught.value)
    assert "RuntimeError" in str(caught.value)


async def test_empty_provider_response_is_an_error() -> None:
    provider = ScriptedProvider(("",))
    with pytest.raises(ProviderError, match="empty response"):
        await NarrativeEngine(provider).generate("Prompt", GenerationOptions(preset="quick"))


async def test_stage_timeout_is_bounded() -> None:
    provider = ScriptedProvider(("late",), delay_seconds=0.05)
    with pytest.raises(ProviderError, match="timeout"):
        await NarrativeEngine(provider).generate(
            "Prompt",
            GenerationOptions(preset="quick", timeout_seconds=0.001),
        )


async def test_invalid_custom_provider_response_is_rejected() -> None:
    class InvalidProvider:
        name = "invalid"

        async def complete(self, *_args: object, **_kwargs: object) -> str:
            return "not normalized"

    provider = cast(Provider, InvalidProvider())
    with pytest.raises(ProviderError, match="invalid response type"):
        await NarrativeEngine(provider).generate("Prompt", GenerationOptions(preset="quick"))


async def test_invalid_custom_provider_fields_are_rejected() -> None:
    class InvalidFieldsProvider:
        name = "invalid"

        async def complete(
            self,
            _messages: Sequence[Message],
            *,
            max_output_tokens: int,
        ) -> ProviderResponse:
            del max_output_tokens
            return ProviderResponse(
                content=cast(str, 42),
                provider="invalid",
                model="fixture",
            )

    with pytest.raises(ProviderError, match="invalid response fields"):
        await NarrativeEngine(InvalidFieldsProvider()).generate(
            "Prompt", GenerationOptions(preset="quick")
        )


async def test_missing_metadata_is_normalized_and_partial_usage_can_be_priced() -> None:
    class PartialUsageProvider(ScriptedProvider):
        async def complete(
            self,
            messages: Sequence[Message],
            *,
            max_output_tokens: int,
        ) -> ProviderResponse:
            self.calls.append((messages, max_output_tokens))
            return ProviderResponse(
                content="# Story\nBody",
                provider="",
                model="",
                usage=TokenUsage(input_tokens=100, output_tokens=20),
            )

    result = await NarrativeEngine(PartialUsageProvider(())).generate(
        "Prompt", GenerationOptions(preset="quick")
    )
    assert result.stages[0].provider == "scripted"
    assert result.stages[0].model == "unknown"
    assert result.estimated_cost(2.0, 10.0) == pytest.approx(0.0008)


def test_provider_protocol_is_required() -> None:
    with pytest.raises(TypeError, match="Provider protocol"):
        NarrativeEngine(cast(Provider, object()))


def test_cost_estimate_uses_caller_prices(scripted_provider: ScriptedProvider) -> None:
    result = asyncio.run(
        NarrativeEngine(scripted_provider).generate(
            "Prompt",
            GenerationOptions(preset="quick"),
        )
    )
    assert result.estimated_cost(2.0, 10.0) == pytest.approx(0.00014)
    with pytest.raises(ValueError, match="finite and nonnegative"):
        result.estimated_cost(-1, 2)
    with pytest.raises(ValueError, match="finite and nonnegative"):
        result.estimated_cost(float("nan"), 2)


def test_cost_estimate_is_none_without_usage() -> None:
    response = ProviderResponse(content="x", provider="p", model="m")
    assert response.usage.total_tokens == 0


@pytest.mark.integration
async def test_resume_reuses_edited_artifacts_and_only_spends_on_the_suffix() -> None:
    original_provider = ScriptedProvider(
        ("Blueprint", "Character notes", "World notes", "# Original\nDraft")
    )
    previous = await NarrativeEngine(original_provider).generate("A city remembers its visitors.")
    editable = json.loads(dumps_run_bundle(previous))
    editable["stages"][2]["content"] = "Edited world rule: memories fade at sunrise."
    edited = loads_run_bundle(json.dumps(editable))

    resume_provider = ScriptedProvider(("# Branched\nRewritten draft",))
    result = await NarrativeEngine(resume_provider).resume(
        edited,
        "writer",
        GenerationOptions(preset="balanced", max_calls=1, max_total_output_tokens=2_600),
    )

    assert len(resume_provider.calls) == 1
    assert "Edited world rule" in resume_provider.calls[0][0][1].content
    assert result.content == "# Branched\nRewritten draft"
    assert result.parent_generation_id == previous.generation_id
    assert result.resumed_from_stage == "writer"
    assert [stage.stage_id for stage in result.stages] == [
        "architect",
        "character",
        "world",
        "writer",
    ]
    assert result.stages[2].content.startswith("Edited world rule")


async def test_resume_rejects_changed_workflow_without_explicit_review() -> None:
    previous = await NarrativeEngine(ScriptedProvider(("Blueprint", "# Story\nDraft"))).generate(
        "Prompt", GenerationOptions(preset="quick")
    )
    changed = NarrativeResult(
        generation_id=previous.generation_id,
        created_at=previous.created_at,
        preset=previous.preset,
        title=previous.title,
        content=previous.content,
        stages=previous.stages,
        creative_brief=previous.creative_brief,
        workflow_fingerprint="sha256:" + "0" * 64,
    )
    provider = ScriptedProvider(("# Changed\nStory",))
    with pytest.raises(InputValidationError, match="workflow differs"):
        await NarrativeEngine(provider).resume(changed, "writer")
    assert provider.calls == []

    result = await NarrativeEngine(provider).resume(
        changed,
        "writer",
        allow_workflow_change=True,
    )
    assert result.content.endswith("Story")
    assert result.workflow_fingerprint == workflow_fingerprint("quick")


@pytest.mark.parametrize(
    ("from_stage", "options", "message"),
    (
        ("missing", GenerationOptions(preset="quick"), "not in workflow"),
        ("writer", GenerationOptions(preset="balanced"), "must match"),
        ("", GenerationOptions(preset="quick"), "non-empty"),
    ),
)
async def test_resume_validation_prevents_provider_calls(
    from_stage: str,
    options: GenerationOptions,
    message: str,
) -> None:
    previous = await NarrativeEngine(ScriptedProvider(("Blueprint", "# Story\nDraft"))).generate(
        "Prompt", GenerationOptions(preset="quick")
    )
    provider = ScriptedProvider(())
    with pytest.raises(InputValidationError, match=message):
        await NarrativeEngine(provider).resume(previous, from_stage, options)
    assert provider.calls == []


async def test_resume_requires_the_complete_prior_stage_prefix() -> None:
    previous = await NarrativeEngine(
        ScriptedProvider(("Blueprint", "Characters", "World", "# Story\nDraft"))
    ).generate("Prompt")
    incomplete = NarrativeResult(
        generation_id=previous.generation_id,
        created_at=previous.created_at,
        preset=previous.preset,
        title=previous.title,
        content=previous.content,
        stages=previous.stages[:1],
        creative_brief=previous.creative_brief,
        workflow_fingerprint=previous.workflow_fingerprint,
    )
    provider = ScriptedProvider(())
    with pytest.raises(InputValidationError, match="missing stages"):
        await NarrativeEngine(provider).resume(incomplete, "writer")
    assert provider.calls == []
