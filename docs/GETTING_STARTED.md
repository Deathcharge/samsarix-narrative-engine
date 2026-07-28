# Getting started

This guide takes a new user from a source checkout to one inspectable narrative run. It does not assume
a published PyPI package or any private Helix infrastructure.

## 1. Create an isolated environment

Helix Narrative Engine supports Python 3.10–3.14. Python 3.9 is intentionally unsupported because its
official security support ended in October 2025.

```bash
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the core and the one provider you intend to use:

```bash
python -m pip install -e ".[openai]"
```

Use `.[anthropic]` for Anthropic. xAI and Perplexity use the `.[openai]` compatibility adapter. The
base package has no runtime dependencies and is sufficient for custom provider implementations.

## 2. Inspect the run before spending

The plan command needs no API key and makes no network request:

```bash
helix-narrative plan --preset balanced
```

Expected structure:

```text
Preset: balanced
1. architect - Story architect (max 1000 output tokens)
2. character - Character editor (max 800 output tokens)
3. world - World and continuity editor (max 800 output tokens)
4. writer - Draft writer (max 2600 output tokens)
Maximum provider calls: 4
Maximum requested output tokens: 5200
Input tokens are provider-dependent and are not estimated by this command.
```

Use `--json` for machine-readable output.

## 3. Configure one provider

Set the key in the current shell. PowerShell example:

```powershell
$env:OPENAI_API_KEY = "your-key"
```

macOS/Linux example:

```bash
export OPENAI_API_KEY="your-key"
```

The package does not load `.env` automatically. `.env.example` is a names-only template. If your own
application loads a secrets file, keep it out of version control and restrict its filesystem access.

## 4. Generate and persist one story

Create `brief.txt` as UTF-8 text, for example:

```text
A cartographer discovers that a city moves every night. Write a hopeful speculative story in which
solving the map requires trusting a former rival. Avoid a chosen-one reveal.
```

Run:

```bash
helix-narrative generate --prompt-file brief.txt --preset balanced --output story.md --artifacts run.json
```

`story.md` contains only the final model output. `run.json` contains the final story plus every stage,
model ID, duration, configured output cap, and provider-reported token count. The original brief is not
persisted by the engine, although generated artifacts can repeat its content.

If a destination already exists, generation exits with code 4 before provider construction or paid API
use. Add `--force` only when replacement is intentional.

## 5. Handle ordinary failures

- Missing key or optional SDK: exit 2 with the required environment variable or install extra.
- Empty/oversized prompt or insufficient call/token budget: exit 2 before a provider call.
- Rate limit, provider error, empty response, or timeout: exit 3; no partial result is presented as
  success.
- Existing/invalid/unwritable output: exit 4; pre-existing content is preserved unless `--force` was
  explicit.
- `Ctrl+C`: exit 130.

Provider errors are intentionally sanitized. In a trusted Python integration, the original SDK
exception remains available as the exception cause for debugging; do not expose it to end users without
review.

## 6. Use the Python API

```python
import asyncio

from helix_narrative_engine import GenerationOptions, NarrativeEngine, OpenAIProvider


async def main() -> None:
    engine = NarrativeEngine(OpenAIProvider())
    result = await engine.generate(
        "A botanist finds a flower that remembers extinct languages.",
        GenerationOptions(preset="quick", max_calls=2, max_total_output_tokens=3_600),
    )
    print(result.title)
    print(result.content)
    print(result.usage.to_dict())


asyncio.run(main())
```

Read [API_REFERENCE.md](API_REFERENCE.md) for the full supported surface.

## Troubleshooting

### `helix-narrative` is not found

Confirm the virtual environment is active and the editable install succeeded:

```bash
python -m helix_narrative_engine --version
```

The module form and console command expose the same CLI.

### The model is unavailable to the account

List/select a model through the provider's own dashboard or documentation, then pass its exact ID:

```bash
helix-narrative generate --prompt-file brief.txt --model YOUR_MODEL_ID
```

Model aliases, access, prices, and retirement dates are provider-controlled and can change after this
package release.

### The request times out

The default timeout is 90 seconds per stage. First try `quick`. If the provider normally needs longer,
set a deliberate cap up to 600 seconds:

```bash
helix-narrative generate --prompt-file brief.txt --preset quick --timeout 180
```

Increasing a timeout can also increase the time before a failed paid request is noticed. Built-in
adapters disable automatic SDK retries so the plan's call count remains the actual request ceiling.
Retry a failed run explicitly after checking provider status and account usage.

### Cost is unclear

Use `plan` first, check current provider pricing, inspect reported usage in `run.json`, and enforce
provider-account budgets. The package does not freeze volatile price tables. The Python result method
`estimated_cost()` accepts current input/output prices per million tokens.
