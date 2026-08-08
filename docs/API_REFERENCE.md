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

### `await NarrativeEngine.resume(previous, from_stage, options=None, *, allow_workflow_change=False)`

Creates a new branch from a loaded or in-memory `NarrativeResult`. Stages before `from_stage` are reused;
that stage and every successor in the preset execute again. The previous result is never mutated. Call
and output-token limits apply to the new suffix only.

Resume validates that prior stages form the exact ordered preset prefix and that the recorded workflow
fingerprint matches the installed prompts, context edges, roles, and token caps. Set
`allow_workflow_change=True` only after reviewing those changes. The result records
`parent_generation_id` and `resumed_from_stage`.

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

### `build_resume_plan(preset, from_stage)`

Returns the exact suffix that a resume operation will execute. It supports approval and remaining-spend
preflight without constructing a provider.

### `workflow_fingerprint(preset)`

Returns a stable SHA-256 digest over the ordered built-in stages, prompts, context edges, roles, and
output caps. It detects semantic workflow drift; it is not a signature or proof of authorship.

### Registries

`AGENTS` and `PRESETS` are immutable mappings. `get_agent`, `get_all_agents`, `get_preset`, and
`get_all_presets` provide read access. A preset is an ordered tuple of stage identifiers, not a dynamic
model router.

## Results

### `NarrativeResult`

Immutable fields:

- `generation_id`: random `nar_` identifier; not a database key or proof of persistence;
- `created_at`: UTC ISO-8601 completion timestamp;
- `preset`, `title`, `content`, and the original `creative_brief`;
- `workflow_fingerprint`: exact built-in workflow digest;
- `parent_generation_id` and `resumed_from_stage`: both null for an original run and both populated for
  a branch;
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

## Run bundles

### `dumps_run_bundle(result)`

Returns UTF-8-compatible JSON text for a strictly valid `samsarix.run/v1` bundle. It includes the
creative brief and all generated content, so callers must treat it as private story material.

### `loads_run_bundle(payload)` / `load_run_bundle(path)`

Strictly validate and load a JSON string or UTF-8 file into `NarrativeResult`. Loading does not contact a
provider. Bundles are limited to 16 MiB; fields are not type-coerced; stage identifiers must be unique;
aggregate usage must match stage usage; and malformed schema, timestamps, lineage, content, or token
counts raise `InputValidationError`.

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
