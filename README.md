# Samsarix Narrative Engine

Samsarix Narrative Engine is a local-first Python SDK and command-line tool for running deterministic,
reviewable narrative-production workflows. Built-in presets produce short-story drafts; portable custom
workflows can produce editorial revisions, game-quest implementation packets, or other staged narrative
artifacts. It is for developers, studios, and technically comfortable writers who need inspectable
intermediates and a known ceiling on provider calls before spending API credits.

Current maturity: **0.1 release candidate**. The local package, deterministic workflow, and provider
contracts are tested. Publishing and Samsarix-funded live-provider smoke tests are still external release
gates; no PyPI release or hosted service is claimed.

## Why this exists

General agent frameworks already solve open-ended delegation. Narrative Engine does something narrower:

- `quick`, `balanced`, and `polished` plans always run known stages in a known order;
- strict `samsarix.workflow/v1` files let teams define their own bounded stages and explicit context
  dependencies without writing orchestration code;
- `samsarix-narrative plan` shows the exact maximum call count and requested output-token total without a
  key;
- one explicitly selected provider is enough for a run, with no surprise fallback spending;
- the result contains the blueprint, editorial notes, draft/revision, model IDs, durations, caps, and
  provider-reported token usage;
- versioned run bundles can be edited between stages and resumed as traceable branches without paying
  to regenerate accepted work;
- completed bundles can be compared through deterministic A/B packets, private unblinding keys, strict
  score sheets, and evidence-backed Markdown/JSON reports;
- the core package has no runtime dependency and accepts custom async providers.

It is a package and CLI, not a web service. Authentication, databases, subscriptions, cloud deployment,
and a frontend are deliberately out of scope.

## Fastest successful setup

Prerequisites: Python 3.10–3.14 and `pip`. Clone the repository, then create an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` on PowerShell or `source .venv/bin/activate` on macOS and
Linux. Install one provider extra from the repository:

```bash
python -m pip install -e ".[openai]"
```

Inspect the default workflow without credentials:

```bash
samsarix-narrative plan --preset balanced
```

Set one key in your shell—do not put it in source code—and generate a story:

```powershell
$env:OPENAI_API_KEY = "your-key"
samsarix-narrative generate --prompt "A lighthouse receives a reply from the future." --preset balanced --output story.md --artifacts story.json
```

On macOS/Linux, use `export OPENAI_API_KEY="your-key"`. The CLI refuses to replace either output file
unless `--force` is present, and it performs that check before creating a provider or making a paid call.

No PyPI publication is asserted. Source installation is the supported evaluation path until Samsarix LLC
publishes a signed release.

## Providers and configuration

Provider SDKs are optional. Install only what a deployment uses:

| CLI provider | Install extra | Key | Default model |
| --- | --- | --- | --- |
| `openai` | `.[openai]` | `OPENAI_API_KEY` | `gpt-5-mini` |
| `anthropic` | `.[anthropic]` | `ANTHROPIC_API_KEY` | `claude-sonnet-5` |
| `xai` | `.[openai]` | `XAI_API_KEY` | `grok-4.5` |
| `perplexity` | `.[openai]` | `PERPLEXITY_API_KEY` (or legacy `SONAR_API_KEY`) | `sonar-pro` |

Override a model with `--model MODEL_ID` or `SAMSARIX_MODEL`. Set `SAMSARIX_PROVIDER` to change the CLI
default. `.env.example` documents variable names, but the package does not automatically read `.env`
files or retain keys itself. Account/model access still depends on the selected provider.

OpenAI requests use the Responses API with response storage disabled. Anthropic uses the Messages API.
xAI and Perplexity use their explicitly named OpenAI-compatible Chat Completions endpoints. The engine
does not silently route between them.

## CLI workflow

```text
samsarix-narrative --help
samsarix-narrative --version
samsarix-narrative plan --preset polished --json
samsarix-narrative plan --preset polished --from-stage writer --json
samsarix-narrative generate --prompt-file brief.txt --provider anthropic --preset quick
samsarix-narrative resume --artifacts-in run.json --from-stage writer --artifacts-out branch.json
samsarix-narrative evaluate prepare --manifest evaluation/manifest.json --packet packet.md --key key.json --scores scores.json
samsarix-narrative evaluate report --key key.json --scores scores.json --output report.md --json-output report.json
```

`--prompt-file -` reads UTF-8 text from standard input. Without `--output`, the final stage output is
written to standard output and status/accounting goes to standard error, which makes non-interactive
pipelines predictable. `--artifacts` writes the full result as UTF-8 JSON.

Meaningful exits are:

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Unexpected internal failure |
| `2` | Invalid input, configuration, or generation budget |
| `3` | Provider failure or timeout |
| `4` | Unsafe or failed output operation |
| `130` | User cancellation |

Use `samsarix-narrative generate --help` for all bounds and output options.

## Custom workflow definitions

A workflow is portable JSON with an ID, display name, and 1–20 ordered stages. Every stage declares its
role, system prompt, output-token cap, and the earlier artifacts it receives through `context_from`.
Unknown fields, forward/self references, duplicate IDs, unsafe strings, per-stage caps above 32,768, and
aggregate caps above 100,000 are rejected before provider construction.

Two executable examples are checked in:

- [game-quest-production.json](examples/workflows/game-quest-production.json) produces a quest
  implementation packet from constraints, beats, branching dialogue, and continuity review;
- [editorial-scene-revision.json](examples/workflows/editorial-scene-revision.json) turns a scene brief
  or draft into a complete revision after developmental and character passes.

Plan and run either without changing Python code:

```bash
samsarix-narrative plan --workflow examples/workflows/game-quest-production.json --json
samsarix-narrative generate --workflow examples/workflows/game-quest-production.json --prompt-file quest-brief.md --output quest-packet.md --artifacts quest-run.json --max-calls 5 --max-total-output-tokens 7600
```

The last stage is the run's primary output. Every completed run embeds the exact workflow definition and
its SHA-256 fingerprint, so the bundle remains executable even when the original workflow file moves.
The machine-readable contracts are [workflow-v1.schema.json](schemas/workflow-v1.schema.json) and
[run-v1.schema.json](schemas/run-v1.schema.json); the dependency-order and aggregate-budget invariants
are additionally enforced by the runtime. See [CUSTOM_WORKFLOWS.md](docs/CUSTOM_WORKFLOWS.md) for the
contract, evolution rules, and integration examples.

## Editable run bundles and branching

`--artifacts` writes a portable `samsarix.run/v1` JSON bundle containing the creative brief, exact
embedded workflow definition and fingerprint, stage outputs, provider/model metadata, timing, and
provider-reported usage. This makes a human editorial checkpoint a normal workflow rather than a
restart:

```bash
samsarix-narrative generate --prompt-file brief.md --preset polished --output draft.md --artifacts run.json
# Review run.json and edit an accepted upstream stage such as character or world content.
samsarix-narrative plan --preset polished --from-stage writer
samsarix-narrative resume --artifacts-in run.json --from-stage writer --output revised.md --artifacts-out branch.json --max-calls 3 --max-total-output-tokens 6600
```

The resumed run reuses only the ordered stages before `--from-stage`, applies call/token limits to the
new suffix, and records `parent_generation_id` plus `resumed_from_stage`. It refuses a changed workflow
fingerprint unless `--allow-workflow-change` is explicitly supplied after prompt changes are reviewed.
The input and output bundles must be different files, preserving the parent as a rollback point.

## Blinded evaluation

Compare two workflow, model, provider, or prompt treatments without exposing their identities to the
reviewer. A strict `samsarix.evaluation/v1` manifest references completed run bundles for the same
creative brief, declares a fixed seed and 1-8 criteria, and uses the same two treatment IDs across every
case.

```bash
samsarix-narrative evaluate prepare --manifest evaluation/manifest.json --packet evaluation/packet.md --key evaluation/private-key.json --scores evaluation/scores.json
# Give packet.md and scores.json to the reviewer, but keep private-key.json private.
samsarix-narrative evaluate report --key evaluation/private-key.json --scores evaluation/scores.json --output evaluation/report.md --json-output evaluation/report.json
```

Preparation and reporting are local, deterministic, and credential-free. The report recomputes an
evidence fingerprint before unblinding, then summarizes rubric means, preferences/ties, calls, requested
output caps, provider-reported tokens, and durations. These are descriptive results, not statistical
proof of general quality. See [EVALUATION.md](docs/EVALUATION.md) for the complete method, privacy
boundary, checked-in template, and interpretation limits.

## Python API

```python
import asyncio

from samsarix_narrative_engine import (
    GenerationOptions,
    NarrativeEngine,
    OpenAIProvider,
    WorkflowRunOptions,
    load_run_bundle,
    load_workflow,
)


async def main() -> None:
    provider = OpenAIProvider(model="gpt-5-mini")  # reads OPENAI_API_KEY
    engine = NarrativeEngine(provider)
    result = await engine.generate(
        "A cartographer discovers a city that moves every night.",
        GenerationOptions(preset="balanced", max_calls=4, max_total_output_tokens=5_200),
    )
    print(result.content)
    print(result.usage.to_dict())  # zero values mean the provider did not report usage
    for stage in result.stages:
        print(stage.stage_id, stage.model, stage.duration_ms)

    custom = load_workflow("examples/workflows/editorial-scene-revision.json")
    custom_result = await engine.run(
        "Revise a tense reunion scene while preserving a restrained voice.",
        custom,
        WorkflowRunOptions(max_calls=4, max_total_output_tokens=5_500),
    )
    print(custom_result.workflow_fingerprint, custom_result.content)

    # After a human edits an upstream stage in the saved JSON bundle:
    previous = load_run_bundle("run.json")
    branch = await engine.resume(
        previous,
        "writer",
        GenerationOptions(preset=previous.preset, max_calls=3, max_total_output_tokens=6_600),
    )
    print(branch.parent_generation_id, branch.content)


asyncio.run(main())
```

Custom providers implement one small async protocol:

```python
from collections.abc import Sequence

from samsarix_narrative_engine import Message, ProviderResponse


class MyProvider:
    name = "my-provider"

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        # Call a local model or an approved API, respecting max_output_tokens.
        return ProviderResponse(content="# Title\nStory", provider=self.name, model="local-v1")
```

See [API_REFERENCE.md](docs/API_REFERENCE.md) for the deliberate public surface and exception contract.

## Plans and cost control

| Preset | Stages | Calls | Maximum requested output tokens |
| --- | --- | ---: | ---: |
| `quick` | architect → writer | 2 | 3,600 |
| `balanced` | architect → character → world → writer | 4 | 5,200 |
| `polished` | architect → character → world → originality → writer → critic → reviser | 7 | 9,500 |

These are output ceilings, not cost quotes. Input tokens depend on the brief and preceding artifacts.
Use current provider pricing with `result.estimated_cost(input_price_per_million,
output_price_per_million)`. It returns `None` if the provider reports no token counts. Configure provider
account budgets/rate limits as a second control plane.

Built-in adapters set SDK retries to zero so the plan's call ceiling is not silently multiplied. Each
stage has a 90-second default timeout and the engine stops on the first failed stage. Retry a failed run
explicitly after checking provider status and account usage. The engine does not return partial work as
a successful story. `Ctrl+C` cancels the CLI.

## Development and verification

Install the complete development environment:

```bash
python -m pip install -e ".[dev,openai,anthropic]"
```

Run the release checks:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy samsarix_narrative_engine
python -m pytest
python -m pip_audit
python -m build
python -m twine check dist/*
```

Tests use deterministic injected clients and do not spend API credits. Live-provider smoke tests require
Samsarix credentials and budget approval. CI checks the supported Python endpoints on Windows and Linux,
plus Python 3.12 on Linux. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## Architecture

- `agents.py` contains immutable stage definitions and presets.
- `artifacts.py` validates portable, size-bounded run bundles.
- `evaluation.py` prepares deterministic blind packets and validates/unblinds completed score sheets.
- `workflows.py` strictly loads portable definitions and builds full or suffix plans.
- `engine.py` validates the entire plan before running code-orchestrated stages.
- `providers.py` defines the provider protocol and optional bounded adapters.
- `models.py` contains immutable, serializable plans, usage, stages, and results.
- `cli.py` handles non-interactive input, status separation, exit codes, and atomic persistence.
- `schemas/` contains JSON Schema 2020-12 workflow, run, evaluation, and score-sheet contracts.

There is no hidden persistence, cache, telemetry, background worker, or Samsarix service dependency.

## Security, privacy, and output limitations

- Keys are read from environment variables, are not accepted as CLI arguments, and are never logged.
- Prompts and generated content are sent to the explicitly selected provider and are subject to that
  provider's terms, retention controls, and the user's account configuration.
- The package writes generated content only when an output/artifact path is explicitly supplied. A full
  run bundle contains the original creative brief, generated content, and lineage; store or share it as
  private story material.
- Blinded packets still contain creative briefs and generated content. Keep evaluation keys private
  during review; evidence fingerprints detect inconsistent edits but are not signatures.
- User story material is serialized as text context. The engine exposes no tools, shell execution,
  retrieval, or filesystem access to models.
- Custom workflow system prompts are executable configuration. Review workflow files like code and do
  not run untrusted definitions merely because they pass structural validation.
- Provider errors are sanitized at the package boundary; inspect chained exceptions only in trusted
  developer environments because SDK exceptions may contain request metadata.
- Generated text can be wrong, biased, derivative, or unsuitable. The editorial review is not factual
  verification, legal clearance, or an ethical/safety certification.

Report security issues using [SECURITY.md](SECURITY.md). The threat boundaries and remaining release gates
are tracked in [PRODUCTIZATION.md](docs/PRODUCTIZATION.md).
The evidence-backed product direction and validation plan are in
[COMPETITIVE_RESEARCH.md](docs/COMPETITIVE_RESEARCH.md).

## Project status, license, and trademarks

Copyright © 2026 Samsarix LLC and contributors. The source is licensed under the standard
[Mozilla Public License 2.0](LICENSE). Modified MPL-covered files must remain available under MPL-2.0
when distributed, while larger proprietary works may use the package under their own terms. See
[LICENSING.md](LICENSING.md) and [NOTICE](NOTICE) for practical attribution details.

The software license does not grant permission to use the Samsarix names, logos, or product branding
except as needed for accurate attribution. See [TRADEMARKS.md](TRADEMARKS.md). Questions may be sent to
[contact@samsarix.com](mailto:contact@samsarix.com); support and private security reports may be sent to
[support@samsarix.com](mailto:support@samsarix.com).

Contributions are welcome under [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). No hosted support SLA, public package release, or production-ready
claim is made.
