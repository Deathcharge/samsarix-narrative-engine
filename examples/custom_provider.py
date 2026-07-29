# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Offline provider-contract demonstration; this does not perform AI generation."""

import asyncio
from collections.abc import Sequence

from samsarix_narrative_engine import (
    GenerationOptions,
    Message,
    NarrativeEngine,
    ProviderResponse,
)


class DemonstrationProvider:
    """Return fixed artifacts so integrations can be evaluated without credentials."""

    name = "demonstration"

    def __init__(self) -> None:
        self._responses = [
            "A two-act blueprint used only for interface demonstration.",
            "# Demonstration Story\nThis fixed output verifies the local workflow contract.",
        ]

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        del messages, max_output_tokens
        return ProviderResponse(
            content=self._responses.pop(0),
            provider=self.name,
            model="fixed-fixture-v1",
        )


async def main() -> None:
    result = await NarrativeEngine(DemonstrationProvider()).generate(
        "This prompt is carried through the real engine but no network request is made.",
        GenerationOptions(preset="quick"),
    )
    print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
