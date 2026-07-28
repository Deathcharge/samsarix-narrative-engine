"""Deterministic provider fixtures used by production-path tests."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Optional

import pytest

from helix_narrative_engine.models import Message, ProviderResponse, TokenUsage


class ScriptedProvider:
    """A deterministic provider that records every real engine request."""

    name = "scripted"

    def __init__(
        self,
        responses: Sequence[str],
        *,
        delay_seconds: float = 0,
        error: Optional[Exception] = None,
    ) -> None:
        self.responses = list(responses)
        self.delay_seconds = delay_seconds
        self.error = error
        self.calls: list[tuple[Sequence[Message], int]] = []

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        self.calls.append((messages, max_output_tokens))
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.error is not None:
            raise self.error
        content = self.responses.pop(0) if self.responses else "# Default\nStory"
        return ProviderResponse(
            content=content,
            provider=self.name,
            model="fixture-v1",
            usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        )


@pytest.fixture
def scripted_provider() -> ScriptedProvider:
    return ScriptedProvider(
        (
            "Blueprint",
            "Character notes",
            "World notes",
            "# The Signal\nA complete story.",
        )
    )
