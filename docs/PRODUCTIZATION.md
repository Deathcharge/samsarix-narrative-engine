# Productization record

This document is the living engineering and product record for turning this repository into a
credible independent product. Command outcomes are recorded only when the command was actually run.

## Repository assessment

The repository began as a small Python package presented as a production-ready, multi-LLM narrative
system. The recoverable idea is useful: a code-orchestrated sequence of specialist editorial passes
can turn one story brief into an inspectable draft. The pre-productization implementation did not
provide a usable release:

- `helix_narrative_engine/engine.py` did not parse on Python 3.11 because an f-string expression
  contained a backslash.
- The 48 collected tests operated entirely on fixtures and mocks; they did not import or exercise
  production agents, the router, or the generation function.
- `setup.py`, `pyproject.toml`, and three requirements files described incompatible dependency sets.
- A duplicate `src/helix_narrative_engine/features.py` tree was not included in the built package and
  none of its advertised caching, monitoring, or resilience utilities were connected to the engine.
- The README claimed production readiness, CI, examples, MIT licensing, and documentation paths that
  did not exist.
- The longer guides documented a nonexistent `NarrativeEngine` class, server, exceptions, streaming,
  batch generation, persistence, cost data, cache, metrics, health endpoints, and deployments.
- The engine silently tried up to five paid providers, used retired model IDs, had no request timeout
  or total call/output budget, and reported invented token counts, a model-authored quality score,
  “ethical approval,” and synthetic UCF metrics as metadata.
- The owner changed `LICENSE` from Apache-2.0 to a customized BSL 1.1 document, but package metadata
  and source constants still claimed Apache-2.0. The license names the Licensed Work as “Helix
  Licensing System,” not this repository.

The initial branch was `main` at `656dbc6`, matching `origin/main`. `git status --short --branch` was
clean. One remote tracking branch existed (`origin/dependabot/pip/pip-c269d3ef21`); no tags or local
release branches existed. Productization work is isolated on `codex/productize-narrative-engine`.

## Chosen product

Samsarix Narrative Engine is a small Python SDK and CLI for deterministic, inspectable,
cost-bounded narrative-development workflows. A developer or technically comfortable writer supplies
one creative brief and one explicitly configured text-model provider. The engine runs a named sequence
of editorial stages and returns both a complete Markdown story and the intermediate artifacts with
provider-reported usage.

The primary journey is:

1. Install the package with one provider extra.
2. Run `samsarix-narrative plan` without credentials to inspect the exact call and output-token ceiling.
3. set one provider key and run `samsarix-narrative generate` with a prompt or UTF-8 prompt file;
4. receive a final story and, optionally, a JSON artifact record that identifies every provider call,
   model, duration, cap, and reported token count.

This is independently useful as a focused orchestration component and reference implementation. It
does not reproduce a broader private platform, require a private Samsarix service, or compete with general-purpose
agent frameworks.

## Target user and use case

The target user is a Python developer building a writing tool, editorial prototype, game-content
pipeline, or local authoring automation who wants more control than one opaque prompt but does not need
a general agent platform. The core use case is generating and inspecting one complete short-story draft
with a predictable maximum number of paid calls.

## Product and architecture decisions

- Orchestration is deterministic code, not model-selected delegation. The stage order, request count,
  and maximum requested output tokens are known before the first call.
- One provider is sufficient for a run. Multi-provider use is supported through a small provider
  protocol and optional adapters; fallback is never automatic because fallback can spend money on a
  provider the caller did not intend to use.
- The dependency-free core accepts custom providers. OpenAI, Anthropic, and explicitly configured
  OpenAI-compatible endpoints are optional extras.
- `quick`, `balanced`, and `polished` are bounded vertical slices. They use 2, 4, and 7 calls
  respectively. Arbitrary agent multiplicity is intentionally removed.
- Intermediate artifacts are first-class output. Synthetic UCF values, fake token counts, and
  model-authored numeric “quality” or “ethical approval” are removed.
- The review stage is an editorial memo, not a safety certification. No model can establish ethical
  compliance merely by responding with `APPROVED`.
- Prompt input is length-limited, serialized as JSON context, never executed, and never written to
  logs. Provider errors are sanitized at the public boundary.
- Provider timeouts, disabled automatic retries, call caps, output-token caps, cancellation, and
  preflighted atomic output writes bound ordinary failure and cost paths.
- The product is a package and CLI, not a network service. Authentication, databases, containers,
  Kubernetes, billing, and hosted health endpoints remain out of scope.

Current official framework documentation distinguishes deterministic workflows from autonomous agents
and recommends code orchestration for predictable cost and performance. That matches this narrow
product better than adding CrewAI, LangGraph, or the OpenAI Agents SDK. References consulted on
2026-07-28:

- [OpenAI Agents SDK orchestration](https://openai.github.io/openai-agents-python/multi_agent/)
- [LangGraph workflows and agents](https://langchain-ai.github.io/langgraph/agents/tools/)
- [CrewAI concepts](https://docs.crewai.com/index)
- [Python packaging and locked environments](https://docs.astral.sh/uv/concepts/projects/sync/)
- [pytest configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses-streaming)
- [Anthropic Python SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)
- [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/)
- [Mozilla MPL 2.0 FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)

## Assumptions and subsequent owner decisions

- On 2026-07-28, the owner identified the company as Samsarix LLC, supplied working company contacts,
  and directed a complete rebrand from Helix to Samsarix. The unpublished package, import namespace,
  CLI, configuration variables, metadata, documentation, and notices now use Samsarix.
- The owner requested a clearer license that protects credit and the work. The customized BSL was
  replaced with unmodified MPL-2.0: file-level copyleft preserves distributed modifications and
  notices while allowing the SDK in larger proprietary works. `NOTICE`, source SPDX headers, and a
  separate trademark policy identify Samsarix LLC without modifying the standard license.
- No PyPI project exists for `samsarix-narrative-engine` as of the rebrand audit (the PyPI JSON endpoint
  returned 404), so publication compatibility is not constrained by a known public artifact.
- Story prompts and generated content may be private. Local files are opt-in, and provider data
  handling remains governed by the provider/account selected by the user.
- Provider model availability and pricing change. Defaults use current stable IDs, users can override
  them, and cost estimates require caller-supplied current prices rather than hard-coded marketing data.
- Python 3.9 is not supported because CPython ended security support on 2025-10-31 and the fixed pytest
  release requires Python 3.10 or newer.

## Baseline command results

Recorded on Windows 10, Python 3.11.9, before productization edits:

| Command | Actual result |
| --- | --- |
| `git status --short --branch` | Exit 0; `## main...origin/main`; no changes. |
| `python --version` | Exit 0; `Python 3.11.9`. |
| `python -m compileall -q helix_narrative_engine src` | Exit 1; syntax error in `engine.py:263`. |
| `python -m pytest` | 48 tests collected and began passing; the captured run exceeded 30 seconds and no final exit status was recorded. Inspection confirmed the suite only asserted mock fixture behavior. |
| `python -m black --check helix_narrative_engine tests setup.py` | Exit 123; four files needed formatting and `engine.py` could not be parsed. |
| `python -m isort --check-only helix_narrative_engine tests setup.py` | Exit 1; seven files failed. |
| `python -m flake8 helix_narrative_engine tests setup.py` | Exit 1; syntax, unused import, whitespace, and line-length failures. |
| `python -m mypy helix_narrative_engine` | Exit 2; unsupported mypy target Python 3.8 and the engine syntax error. |
| isolated `.venv\\Scripts\\python -m pip install -e .` | Exit 1; `setup.py` decoded the UTF-8 README as cp1252 and raised `UnicodeDecodeError` before dependency resolution. |

The global interpreter's `pip check` also reported unrelated conflicts in globally installed packages;
final verification therefore uses the isolated project environment and fresh wheel environments.

## Findings

### P0

- [x] Replace the unparsable core and ensure every test imports production code.
- [x] Consolidate packaging metadata and remove the locale-sensitive legacy setup path.
- [x] Make the documented primary API and CLI real.
- [x] Remove misleading service/deployment and production-readiness claims.
- [x] Verify an isolated install, clean build, wheel install/import, CLI journey, and full quality suite.

### P1

- [x] Add strict prompt, timeout, call-count, and output-token bounds; disable hidden SDK retries.
- [x] Remove automatic paid-provider fallback and fabricated metrics.
- [x] Make provider dependencies optional so the base package installs without five SDKs.
- [x] Add safe output overwrite behavior and atomic writes.
- [x] Add meaningful unit, integration, provider-contract, CLI, and package-shape tests.
- [x] Add CI across supported Python versions and Windows/Linux.
- [x] Replace fictional API/getting-started/contribution documents with verified documentation.
- [x] Produce and verify a dependency lock and dependency-license inventory where practical.

### P2

- [ ] Add a Google Gen AI Interactions adapter after its rapidly changing API surface is isolated and
  contract-tested.
- [ ] Add resumable artifact input so a failed or edited workflow can restart from a named stage.
- [ ] Add optional streaming for the final writer/reviser stage without weakening atomic artifact
  persistence.
- [ ] Add a prompt/evaluation fixture corpus to compare revisions across provider/model upgrades.

## Implementation checklist

- [x] Select the product wedge and out-of-scope boundaries.
- [x] Define a minimal provider protocol and typed public results.
- [x] Implement bounded plans and preflight budget validation.
- [x] Implement the core engine and optional provider adapters.
- [x] Implement CLI plan/generate/help/version, cancellation, exit codes, and safe persistence.
- [x] Replace mock-only tests.
- [x] Consolidate developer tooling and add CI.
- [x] Rewrite README and accurate supporting docs.
- [x] Build and inspect source/wheel artifacts.
- [x] Run adversarial setup, cross-platform, privacy, cost, failure, and documentation checks.

## Release acceptance criteria

- Base editable and wheel installs work without provider SDKs.
- Each documented provider extra installs independently.
- `samsarix-narrative --help`, `--version`, and `plan` work without credentials.
- A deterministic fake-provider integration test completes each advertised preset.
- CLI output refusal occurs before any provider call, and `--force` replaces only named files.
- Empty, oversized, timed-out, failed-provider, empty-provider-response, and over-budget cases have
  meaningful errors and nonzero CLI exits.
- Ruff format/lint, strict mypy, pytest with branch coverage, build, and Twine checks pass.
- CI runs meaningful checks on Python 3.10 and 3.14 on Windows/Linux, plus Python 3.12 on Linux.
- README commands are copied from and agree with verified scripts.
- No locally actionable P0 remains.

## Completed work

- Preserved the clean initial worktree and isolated changes on a feature branch.
- Replaced the broken free-form router/orchestrator with typed provider, plan, stage, usage, and result
  contracts.
- Added explicit optional OpenAI Responses, Anthropic Messages, and OpenAI-compatible adapters with
  bounded SDK timeouts, automatic retries disabled, and sanitized errors.
- Added deterministic quick/balanced/polished workflows and removed unbounded custom multiplicity.
- Added the `samsarix-narrative` CLI with dry planning, UTF-8 input, overwrite preflight, atomic writes,
  provider accounting, and meaningful exits.
- Removed the unpackageable duplicate advanced-features module and fake metrics from the public path.
- Replaced 48 mock-only tests with 66 production-path tests covering plans, presets, bounds, adapters,
  failure sanitation, CLI behavior, public exports, and an output-creation race.
- Consolidated packaging and tooling in `pyproject.toml`, added a reproducible `uv.lock`, and configured
  least-privilege CI plus weekly dependency and Actions updates.
- Built and inspected the universal wheel and source distribution, including clean wheel-only and
  independent OpenAI/Anthropic-extra environments.
- Rebranded the unpublished distribution, import namespace, CLI, configuration variables, company
  identity, and contacts to Samsarix without carrying a misleading compatibility alias.
- Replaced the customized BSL with standard MPL-2.0, Samsarix LLC copyright/SPDX notices, redistribution
  guidance, and an explicit trademark policy.

## Final local verification

Recorded on Windows 10 with Python 3.11.9 after the final implementation changes:

| Command/check | Actual result |
| --- | --- |
| `python -m ruff format --check .` | Exit 0; 28 files already formatted. |
| `python -m ruff check .` | Exit 0; all checks passed. |
| `python -m mypy samsarix_narrative_engine` | Exit 0; no issues in 8 source files. |
| `python -m compileall -q samsarix_narrative_engine tests examples` | Exit 0. |
| `python -m pytest` | Exit 0; 66 passed; 97.40% branch coverage (90% required). |
| `python -m pip check` | Exit 0; no broken requirements. |
| `uv lock --check` | Exit 0; 83 packages resolved. |
| `python -m pip_audit --progress-spinner off` | Exit 0; no known vulnerabilities; the unpublished local package itself was skipped because it is not on PyPI. |
| credential-pattern scan | Exit 1 from `rg` because no candidate key patterns were found. |
| `python -m build` | Exit 0; built the 0.1.0 sdist and universal wheel from an isolated environment. |
| `python -m twine check` | Exit 0; both artifacts passed. |
| clean base wheel smoke | Exit 0; dependency check, package import, console version, and credential-free `quick` plan passed outside the source path. |
| independent provider extras | Exit 0; OpenAI 2.50.0 and Anthropic 0.120.2 installed/imported independently and each environment passed `uv pip check`. |
| standard-license comparison | Exit 0; `LICENSE` is byte-for-byte identical to Mozilla's unmodified MPL-2.0 text. |
| `git diff --check` | Exit 0. |

The core has no runtime dependency. Installed metadata reports Apache-2.0 for the direct optional
OpenAI SDK and MIT for the direct optional Anthropic SDK. The exact resolved dependency graph is locked;
MPL-2.0 is a standard OSI-approved license; counsel should still confirm Samsarix LLC's ownership chain
for code created before the company rebrand.

Remote CI was configured but cannot be represented as executed until the branch is pushed and GitHub
Actions runs it. Samsarix-funded live-provider calls were intentionally not made.

## Deferred and blocked work

Owner/legal decisions:

- Confirm that Samsarix LLC owns or has a written right to license all pre-company contributions under
  MPL-2.0; the repository cannot establish a corporate copyright assignment by itself.
- Decide whether and where to publish the package. PyPI publication, trusted-publisher configuration,
  signing, and release credentials are not created here.
- Obtain counsel review before relying on copyright or trademark enforcement in a specific jurisdiction.

No credentials, billing account, hosted endpoint, deployment, publication, or live infrastructure is
required for local completion and none will be fabricated.

## Known risks

- Model output is nondeterministic and may be inaccurate or inappropriate. The engine offers process
  transparency, not factual verification, copyright clearance, or safety certification.
- Full artifact JSON contains generated content. Users must choose an appropriate storage location and
  retention policy.
- Provider SDK/API/model behavior and pricing change independently of this package. Contract tests use
  deterministic clients; Samsarix-funded live smoke tests remain an external release gate for each
  advertised adapter.
- A bounded output-token request does not by itself cap provider input tokens. The fixed number of
  stages and bounded prior artifacts constrain amplification, but users must inspect current provider
  pricing and account limits.

## Distribution and sustainability

The simplest distribution is a signed source archive and universal Python wheel, then a Samsarix-approved
PyPI publication using a trusted publisher. The repository should remain useful from source with no
private dependencies. A plausible sustainability model is paid support, integration work, or—only if
Samsarix holds the necessary rights to every contribution—an alternative commercial license for customers
that do not want to satisfy MPL obligations. Running a hosted generation service or subscription is not
justified by this repository and would create privacy, abuse, authentication, and variable-cost burdens
that the narrow package avoids.
