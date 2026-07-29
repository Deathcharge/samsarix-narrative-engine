# Contributing

Thank you for improving Samsarix Narrative Engine. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md)
and keep changes focused on the repository's narrow package/CLI product.

## Development setup

Prerequisites are Python 3.10–3.14 and Git.

```bash
python -m venv .venv
```

Activate the environment (`.venv\Scripts\Activate.ps1` on PowerShell or `source .venv/bin/activate` on
macOS/Linux), then install the project and development/provider extras:

```bash
python -m pip install -e ".[dev,openai,anthropic]"
```

No API key is needed for the test suite. Confirm the local interface:

```bash
samsarix-narrative --version
samsarix-narrative plan --preset balanced
```

## Working agreement

- Create a branch and preserve unrelated worktree changes.
- Keep the core dependency-free. Provider SDKs belong in named optional extras.
- Do not add a provider fallback, paid call, network integration, persistence behavior, or destructive
  output action without explicit configuration, limits, tests, and documentation.
- Never commit keys, private prompts, generated private content, recordings, or provider responses.
- Treat model output as untrusted text. Do not expose tool execution or claim model review is factual,
  legal, ethical, or safety certification.
- Maintain Python 3.10 syntax and typed public APIs.
- Add deterministic tests that exercise production code. Live tests must be separately marked, opt-in,
  and never run in ordinary CI.
- Update `CHANGELOG.md`, README/API docs, and `docs/PRODUCTIZATION.md` when behavior or release gates
  change.

## Required checks

Run these from the repository root:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy samsarix_narrative_engine
python -m pytest
python -m pip_audit
python -m build
python -m twine check dist/*
```

Coverage is enforced with branch coverage at 90%. A passing mock-only test is not meaningful; assertions
must reach the engine, adapter, CLI, or package boundary that the change affects.

For packaging changes, also install the built wheel into a new environment and run its `--version` and
`plan` commands as described in [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md).

## Code style

Ruff is the formatter, import sorter, and linter. Mypy runs in strict mode for the package. Prefer:

- immutable dataclasses for public values;
- explicit exceptions over returned error strings;
- small provider-neutral protocols over framework dependencies;
- preflight validation before network or filesystem side effects;
- monotonic timing and bounded async waits;
- sanitized user-facing errors with chained internal causes for trusted debugging.

Compatibility aliases are documented in `docs/API_REFERENCE.md`. Do not expand that legacy surface.

## Tests

The suite is organized by product boundary:

- `test_agents.py`: immutable registries and exact plan budgets;
- `test_engine.py`: end-to-end presets, validation, accounting, timeouts, and failures;
- `test_providers.py`: SDK payload/response contracts and secret-safe errors using injected clients;
- `test_cli.py`: commands, exit codes, streams, overwrite preflight, and atomic persistence;
- `test_public_api.py`: exported package shape and value objects.

When fixing a bug, write a failing regression test first where practical. Use deterministic fixture
providers; do not add sleep-based tests except tightly bounded timeout behavior.

## Pull requests

Explain the user problem, the product decision, commands run with actual outcomes, new risks, and any
company/external gate. Keep commits logically separated (for example core, tests, documentation, CI) and
do not mix generated build/coverage artifacts into commits.

Contributions are accepted under MPL-2.0 and must preserve applicable license and copyright notices.
License, trademark, pricing, publication, and production-infrastructure decisions require Samsarix LLC
approval. Do not infer or rewrite them in a contribution. Contact `contact@samsarix.com` when a change
needs a company decision.
