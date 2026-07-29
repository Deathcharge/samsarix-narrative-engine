# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Generate a story with one explicitly configured OpenAI provider."""

import asyncio

from samsarix_narrative_engine import GenerationOptions, NarrativeEngine, OpenAIProvider


async def main() -> None:
    engine = NarrativeEngine(OpenAIProvider())
    result = await engine.generate(
        "A lighthouse receives a reply from the future.",
        GenerationOptions(preset="quick", max_calls=2, max_total_output_tokens=3_600),
    )
    print(result.content)
    print(result.usage.to_dict())


if __name__ == "__main__":
    asyncio.run(main())
