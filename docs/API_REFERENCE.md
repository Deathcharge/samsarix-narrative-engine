# API reference

The public API is exported from `samsarix_narrative_engine`. Everything else is an implementation detail
unless documented here.

## Core workflow

### `NarrativeEngine(provider)`

Constructs an engine with one object satisfying the `Provider` protocol. Provider selection is explicit
and immutable for the engine instance.

### `await NarrativeEngine.generate(prompt, options=None)`

Validates input and the complete plan before the first provider call, runs stages in order, and returns a
`NarrativeResult`. It raises an exception on failure and never represents a partial draft as success.

### `await generate_narrative(prompt, provider, options=None)`

Convenience equivalent to constructing `NarrativeEngine(provider)` for one run.

### `await generateNarrative(prompt, options=None, provider=None)`

Compatibility alias for the original camel-case entry point. When `provider` is omitted it reads
`SAMSARIX_PROVIDER` (default `openai`) and associated environment configuration. New code should prefer the
explicit `generate_narrative` form.

## Options and plans

### `GenerationOptions`

Immutable dataclass fields:

| Field | Default | Validation |
| --- | ---: | --- |
| `preset` | `balanced` | `quick`, `balanced`, or `polished` |
| `timeout_seconds` | `90.0` | greater than 0, at most 600; applied per stage |
| `max_prompt_chars` | `12000` | 1–100000 |
| `max_calls` | `7` | 1–20 and at least the selected plan's calls |
| `max_total_output_tokens` | `10000` | 1–100000 and at least the plan's summed caps |

### `build_plan(preset)`

Returns a `GenerationPlan` without constructing a provider or making a network request. Its
`max_calls`, `max_output_tokens`, and ordered `PlannedStage` values are suitable for user confirmation,
policy checks, and UI display.

### Registries

`AGENTS` and `PRESETS` are immutable mappings. `get_agent`, `get_all_agents`, `get_preset`, and
`get_all_presets` provide read access. A preset is an ordered tuple of stage identifiers, not a dynamic
model router.

## Results

### `NarrativeResult`

Immutable fields:

- `generation_id`: random `nar_` identifier; not a database key or proof of persistence;
- `created_at`: UTC ISO-8601 completion timestamp;
- `preset`, `title`, `content`;
- `stages`: ordered tuple of `StageResult` artifacts.

`usage` sums provider-reported `TokenUsage` across stages. A zero count means “not reported,” not zero
cost. `to_dict()` includes the final narrative, aggregate usage, and complete stage artifacts.

`estimated_cost(input_per_million, output_per_million)` calculates from caller-supplied finite,
nonnegative prices and returns `None` if both input and output usage were unreported. It is an arithmetic
convenience, not a bill.

### `StageResult`

Contains `stage_id`, human-readable `role`, generated `content`, `provider`, `model`, `usage`, elapsed
`duration_ms`, and the request's `max_output_tokens`. Durations use the local monotonic clock and are
observational, not service-level guarantees.

### `TokenUsage`

Contains nonnegative `input_tokens`, `output_tokens`, and `total_tokens`. Providers normalize their own
SDK fields; custom providers must not invent counts. Supports addition and `to_dict()`.

## Provider contract

```python
from collections.abc import Sequence
from typing import Protocol

from samsarix_narrative_engine import Message, ProviderResponse


class Provider(Protocol):
    name: str

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse: ...
```

The engine adds its own per-stage timeout. A provider should also set network-level timeouts, honor the
output cap, avoid hidden retries, return only normalized text, and avoid logging credentials/content.

### Built-in adapters

- `OpenAIProvider(model="gpt-5-mini", ..., timeout_seconds=90)` uses the Responses API
  with `store=False` and requires the `openai` extra plus `OPENAI_API_KEY`.
- `AnthropicProvider(model="claude-sonnet-5", ...)` uses the Messages API and requires the `anthropic`
  extra plus `ANTHROPIC_API_KEY`.
- `OpenAICompatibleProvider(name, model, base_url, api_key, ...)` is an explicit Chat Completions
  adapter for approved compatible endpoints; it does not discover or trust arbitrary URLs.
- `build_provider(name, ...)` supports CLI names `openai`, `anthropic`, `xai`, and `perplexity`.
- `provider_from_env()` reads `SAMSARIX_PROVIDER` and `SAMSARIX_MODEL`.

No built-in adapter silently fails over to another provider.

## Exceptions

All expected package failures inherit `NarrativeEngineError`:

| Exception | Meaning |
| --- | --- |
| `ConfigurationError` | Missing/invalid provider SDK, model, key, or timeout configuration |
| `InputValidationError` | Invalid prompt or engine option; raised before calls |
| `BudgetExceededError` | The selected plan exceeds caller call/output limits; raised before calls |
| `ProviderError` | Sanitized SDK, timeout, response-shape, or empty-response failure |
| `OutputError` | CLI persistence would be unsafe or failed |

`ProviderError.__cause__` can hold the original exception for trusted debugging. Its public string
contains only the provider name and exception/reason category, never the original SDK message.

Cancellation is not converted into success. Normal asyncio cancellation propagates; the CLI maps user
interrupts to exit 130.

## Compatibility surface

`getAgentConfig`, `applyPresetMode`, `PRESET_MODES`, `generateNarrative`, and
`NarrativeGenerationResult` remain as bounded compatibility names. They do not restore removed provider
defaults, arbitrary multiplicity, fake metrics, or the old returned-error object. New integrations should
use snake_case names and typed dataclasses.
