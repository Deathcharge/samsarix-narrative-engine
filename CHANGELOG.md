# Changelog

All notable changes are documented here. This project follows semantic versioning once a release is
published.

## 0.1.0 - Unreleased

### Added

- Typed, dependency-free narrative workflow core with injectable providers.
- Bounded `quick`, `balanced`, and `polished` generation plans.
- Optional OpenAI Responses, Anthropic Messages, xAI, and Perplexity adapters.
- `helix-narrative` plan and generate CLI with atomic output and artifact persistence.
- Production-path tests, strict typing, formatting/linting, package verification, and CI.

### Changed

- Reset the package maturity from the broken, unpublished 1.0 claim to an honest 0.1 product line.
- Consolidated package and dependency metadata in `pyproject.toml`.
- Replaced fabricated quality, ethical approval, usage, and UCF metrics with inspectable artifacts and
  provider-reported usage.
- Disabled automatic SDK retries so advertised call ceilings are not silently multiplied.
- Closed the output preflight race with atomic no-clobber publication unless `--force` is explicit.

### Removed

- Unbounded agent multiplicity and silent paid-provider fallback.
- Unpackaged placeholder caching, monitoring, resilience, service, and deployment surfaces.
- Conflicting legacy setup and requirements files.
