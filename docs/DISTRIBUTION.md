# Distribution and release

This repository produces a pure-Python source distribution and universal wheel. It is not a server or
container image and has no deployment target.

## Local release-candidate verification

From an isolated development environment:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy helix_narrative_engine
python -m pytest
python -m pip_audit
python -m build
python -m twine check dist/*
```

Then install the wheel into a new environment and verify the installed—not source-tree—shape:

```bash
python -m venv wheel-check
wheel-check/Scripts/python -m pip install dist/helix_narrative_engine-0.1.0-py3-none-any.whl
wheel-check/Scripts/helix-narrative --version
wheel-check/Scripts/helix-narrative plan --preset balanced
```

On macOS/Linux, executables are under `wheel-check/bin/`. Remove the temporary environment only after
confirming its resolved path is the intended test directory.

## Artifact contents

The wheel must contain the `helix_narrative_engine` modules and `py.typed`, but no tests, credentials,
`.env`, coverage output, generated stories, or duplicate `src` package. The source distribution includes
license and user documentation needed to evaluate the work.

## Owner-controlled publication gates

Do not publish until the owner has:

1. confirmed the BSL text names this repository and reviewed its custom terms;
2. selected a package registry and confirmed the name;
3. configured a trusted publisher or scoped token and release signing/attestation policy;
4. approved current version/release notes;
5. funded live smoke tests for every adapter advertised in the release;
6. configured private security reporting and a Code of Conduct contact.

When those gates are satisfied, prefer the registry's trusted-publisher workflow over a long-lived token.
Publication is intentionally not automated from untrusted pull requests and is not performed as part of
repository productization.

## Versioning

`0.1.0` is the first honest product line because no tag or PyPI release exists and the earlier `1.0.0`
claim could not install or import. After the first owner-approved publication, follow semantic versioning
for the documented public API and update `CHANGELOG.md` in the same change.
