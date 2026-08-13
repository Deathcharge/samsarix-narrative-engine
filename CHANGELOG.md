# Changelog

All notable changes are documented here. This project follows semantic versioning once a release is
published.

## 0.1.0 - Unreleased

### Added

- Typed, dependency-free narrative workflow core with injectable providers.
- Bounded `quick`, `balanced`, and `polished` generation plans.
- Optional OpenAI Responses, Anthropic Messages, xAI, and Perplexity adapters.
- `samsarix-narrative` plan and generate CLI with atomic output and artifact persistence.
- Production-path tests, strict typing, formatting/linting, package verification, and CI.
- Versioned `samsarix.run/v1` bundles with strict UTF-8, schema, lineage, stage, and usage validation.
- Editable resume branches through the Python API and CLI, with suffix-only budget preflight.
- Stable workflow fingerprints that require explicit approval before resuming across workflow changes.
- Strict `samsarix.workflow/v1` definitions, embedded executable provenance, full/suffix planning, and
  custom workflow execution through the Python API and CLI.
- JSON Schema 2020-12 contracts plus checked-in editorial scene-revision and game quest-production
  workflows.
- Deterministic `samsarix.evaluation/v1` pairwise manifests, blinded Markdown review packets, private
  unblinding evidence, strict `samsarix.scores/v1` score sheets, and Markdown/JSON comparison reports.

### Changed

- Reset the package maturity from the broken, unpublished 1.0 claim to an honest 0.1 product line.
- Consolidated package and dependency metadata in `pyproject.toml`.
- Replaced fabricated quality, ethical approval, usage, and UCF metrics with inspectable artifacts and
  provider-reported usage.
- Disabled automatic SDK retries so advertised call ceilings are not silently multiplied.
- Closed the output preflight race with atomic no-clobber publication unless `--force` is explicit.
- Adopted the Samsarix LLC identity across the distribution, Python namespace, CLI, configuration, and
  support contacts.
- Replaced the customized BSL text with the standard MPL-2.0 license, copyright notice, and trademark
  guidance.

### Removed

- Unbounded agent multiplicity and silent paid-provider fallback.
- Unpackaged placeholder caching, monitoring, resilience, service, and deployment surfaces.
- Conflicting legacy setup and requirements files.
