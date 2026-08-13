# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Command-level tests for help, planning, generation, and safe persistence."""

from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path
from typing import Any

import pytest

from samsarix_narrative_engine import (
    NarrativeEngine,
    dumps_run_bundle,
    load_run_bundle,
)
from samsarix_narrative_engine.cli import main
from samsarix_narrative_engine.exceptions import ProviderError

from .conftest import ScriptedProvider


def _factory(provider: ScriptedProvider) -> Any:
    def build(*_args: Any, **_kwargs: Any) -> ScriptedProvider:
        return provider

    return build


def test_cli_help_and_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(("--help",))
    assert help_exit.value.code == 0
    assert "cost-bounded" in capsys.readouterr().out

    with pytest.raises(SystemExit) as version_exit:
        main(("--version",))
    assert version_exit.value.code == 0
    version_output = capsys.readouterr().out
    assert "samsarix-narrative" in version_output
    assert "0.1.0" in version_output


def test_cli_plan_needs_no_provider(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(("plan", "--preset", "quick")) == 0
    output = capsys.readouterr().out
    assert "Maximum provider calls: 2" in output
    assert "3600" in output

    assert main(("plan", "--preset", "balanced", "--json")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["max_calls"] == 4
    assert payload["stages"][-1]["stage_id"] == "writer"

    assert main(("plan", "--preset", "balanced", "--from-stage", "writer", "--json")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["from_stage"] == "writer"
    assert payload["max_calls"] == 1
    assert payload["max_output_tokens"] == 2_600

    assert main(("plan", "--preset", "quick", "--from-stage", "critic")) == 2
    assert "not in workflow" in capsys.readouterr().err


def test_cli_generate_writes_story_and_artifacts_atomically(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = ScriptedProvider(("Blueprint", "# CLI Story\nBody"))
    story = tmp_path / "nested" / "story.md"
    artifacts = tmp_path / "nested" / "story.json"

    exit_code = main(
        (
            "generate",
            "--prompt",
            "A clock repairs its maker.",
            "--preset",
            "quick",
            "--output",
            str(story),
            "--artifacts",
            str(artifacts),
        ),
        provider_factory=_factory(provider),
    )

    assert exit_code == 0
    assert story.read_text(encoding="utf-8") == "# CLI Story\nBody\n"
    payload = json.loads(artifacts.read_text(encoding="utf-8"))
    assert payload["title"] == "CLI Story"
    assert len(payload["stages"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "30 total tokens" in captured.err


def test_cli_generate_can_read_stdin_and_write_story_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = ScriptedProvider(("Blueprint", "# Standard Output\nBody"))
    monkeypatch.setattr("samsarix_narrative_engine.cli.sys.stdin", io.StringIO("Prompt from stdin"))
    assert (
        main(
            ("generate", "--prompt-file", "-", "--preset", "quick"),
            provider_factory=_factory(provider),
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.out == "# Standard Output\nBody\n"
    assert "standard output" in captured.err


def test_existing_output_refuses_before_provider_creation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    story = tmp_path / "story.md"
    story.write_text("keep", encoding="utf-8")
    factory_calls = 0

    def factory(*_args: Any, **_kwargs: Any) -> ScriptedProvider:
        nonlocal factory_calls
        factory_calls += 1
        return ScriptedProvider(())

    assert (
        main(
            ("generate", "--prompt", "Prompt", "--preset", "quick", "--output", str(story)),
            provider_factory=factory,
        )
        == 4
    )
    assert story.read_text(encoding="utf-8") == "keep"
    assert factory_calls == 0
    assert "--force" in capsys.readouterr().err


def test_force_replaces_only_explicit_output(tmp_path: Path) -> None:
    story = tmp_path / "story.md"
    story.write_text("old", encoding="utf-8")
    sibling = tmp_path / "sibling.md"
    sibling.write_text("untouched", encoding="utf-8")
    provider = ScriptedProvider(("Blueprint", "# Replacement\nNew"))

    assert (
        main(
            (
                "generate",
                "--prompt",
                "Prompt",
                "--preset",
                "quick",
                "--output",
                str(story),
                "--force",
            ),
            provider_factory=_factory(provider),
        )
        == 0
    )
    assert story.read_text(encoding="utf-8").endswith("New\n")
    assert sibling.read_text(encoding="utf-8") == "untouched"


@pytest.mark.parametrize("target_exists", (False, True))
def test_cli_rejects_final_output_symlinks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target_exists: bool,
) -> None:
    target = tmp_path / "outside.md"
    if target_exists:
        target.write_text("keep", encoding="utf-8")
    output = tmp_path / "story.md"
    try:
        output.symlink_to(target)
    except OSError as error:
        pytest.skip(f"file symlinks are unavailable: {error}")
    provider_calls = 0

    def factory(*_args: Any, **_kwargs: Any) -> ScriptedProvider:
        nonlocal provider_calls
        provider_calls += 1
        return ScriptedProvider(("Blueprint", "# Story\nBody"))

    arguments = [
        "generate",
        "--prompt",
        "Prompt",
        "--preset",
        "quick",
        "--output",
        str(output),
    ]
    if target_exists:
        arguments.append("--force")

    assert main(arguments, provider_factory=factory) == 4
    assert provider_calls == 0
    assert output.is_symlink()
    assert target.exists() is target_exists
    if target_exists:
        assert target.read_text(encoding="utf-8") == "keep"
    assert "symbolic link or reparse point" in capsys.readouterr().err


def test_output_created_during_generation_is_not_overwritten(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    story = tmp_path / "story.md"

    class RacingProvider(ScriptedProvider):
        async def complete(self, *args: Any, **kwargs: Any) -> Any:
            response = await super().complete(*args, **kwargs)
            if len(self.calls) == 2:
                story.write_text("created concurrently", encoding="utf-8")
            return response

    provider = RacingProvider(("Blueprint", "# Generated\nBody"))
    assert (
        main(
            ("generate", "--prompt", "Prompt", "--preset", "quick", "--output", str(story)),
            provider_factory=_factory(provider),
        )
        == 4
    )
    assert story.read_text(encoding="utf-8") == "created concurrently"
    assert "FileExistsError" in capsys.readouterr().err


def test_same_output_and_artifact_path_is_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "same"
    assert (
        main(
            (
                "generate",
                "--prompt",
                "Prompt",
                "--output",
                str(destination),
                "--artifacts",
                str(destination),
            ),
            provider_factory=_factory(ScriptedProvider(())),
        )
        == 4
    )


def test_prompt_file_errors_are_sanitized(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"\xff\xfe")
    assert (
        main(
            ("generate", "--prompt-file", str(invalid)),
            provider_factory=_factory(ScriptedProvider(())),
        )
        == 2
    )
    assert "UnicodeDecodeError" in capsys.readouterr().err


def test_cli_maps_provider_and_internal_failures_to_exit_codes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    failed_provider = ScriptedProvider((), error=ProviderError("fixture", "rate limit"))
    assert (
        main(
            ("generate", "--prompt", "Prompt", "--preset", "quick"),
            provider_factory=_factory(failed_provider),
        )
        == 3
    )
    assert "provider error" in capsys.readouterr().err

    def broken_factory(*_args: Any, **_kwargs: Any) -> ScriptedProvider:
        raise RuntimeError("private details")

    assert (
        main(
            ("generate", "--prompt", "Prompt", "--preset", "quick"),
            provider_factory=broken_factory,
        )
        == 1
    )
    error = capsys.readouterr().err
    assert "RuntimeError" in error
    assert "private details" not in error


def test_cli_budget_errors_return_usage_exit(capsys: pytest.CaptureFixture[str]) -> None:
    provider = ScriptedProvider(())
    assert (
        main(
            (
                "generate",
                "--prompt",
                "Prompt",
                "--preset",
                "polished",
                "--max-calls",
                "2",
            ),
            provider_factory=_factory(provider),
        )
        == 2
    )
    assert provider.calls == []
    assert "requires 7 calls" in capsys.readouterr().err


def test_cli_provider_error_type_is_public() -> None:
    assert issubclass(ProviderError, Exception)


def test_cli_resume_branches_an_edited_bundle_atomically(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    previous = asyncio.run(
        NarrativeEngine(
            ScriptedProvider(("Blueprint", "Characters", "World", "# Original\nDraft"))
        ).generate("A city whose laws change at midnight.")
    )
    source = tmp_path / "original.json"
    source.write_text(dumps_run_bundle(previous), encoding="utf-8")
    data = json.loads(source.read_text(encoding="utf-8"))
    data["stages"][2]["content"] = "Edited canon: laws change only at dawn."
    source.write_text(json.dumps(data), encoding="utf-8")

    provider = ScriptedProvider(("# Branched\nNew story",))
    story = tmp_path / "branched.md"
    bundle = tmp_path / "branched.json"
    assert (
        main(
            (
                "resume",
                "--artifacts-in",
                str(source),
                "--from-stage",
                "writer",
                "--output",
                str(story),
                "--artifacts-out",
                str(bundle),
                "--max-calls",
                "1",
                "--max-total-output-tokens",
                "2600",
            ),
            provider_factory=_factory(provider),
        )
        == 0
    )

    branched = load_run_bundle(bundle)
    assert story.read_text(encoding="utf-8") == "# Branched\nNew story\n"
    assert branched.parent_generation_id == previous.generation_id
    assert branched.resumed_from_stage == "writer"
    assert branched.stages[2].content.startswith("Edited canon")
    assert len(provider.calls) == 1
    status = capsys.readouterr().err
    assert "1 new calls" in status
    assert "15 new total tokens" in status


def test_cli_resume_refuses_unsafe_paths_and_invalid_input_before_provider_creation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}", encoding="utf-8")
    factory_calls = 0

    def factory(*_args: Any, **_kwargs: Any) -> ScriptedProvider:
        nonlocal factory_calls
        factory_calls += 1
        return ScriptedProvider(())

    assert (
        main(
            (
                "resume",
                "--artifacts-in",
                str(source),
                "--from-stage",
                "writer",
                "--artifacts-out",
                str(source),
                "--force",
            ),
            provider_factory=factory,
        )
        == 4
    )
    assert factory_calls == 0
    assert "different files" in capsys.readouterr().err

    assert (
        main(
            (
                "resume",
                "--artifacts-in",
                str(source),
                "--from-stage",
                "writer",
            ),
            provider_factory=factory,
        )
        == 2
    )
    assert factory_calls == 0
    assert "invalid run bundle" in capsys.readouterr().err
