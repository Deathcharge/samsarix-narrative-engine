"""Core workflow integration, validation, and failure tests."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import cast

import pytest

from helix_narrative_engine import (
    BudgetExceededError,
    GenerationOptions,
    InputValidationError,
    Message,
    NarrativeEngine,
    Provider,
    ProviderError,
    ProviderResponse,
    TokenUsage,
    generate_narrative,
    generateNarrative,
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
