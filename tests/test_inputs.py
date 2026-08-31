# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Bounded transport and strict JSON regressions shared by all input surfaces."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from samsarix_narrative_engine import InputValidationError, loads_run_bundle, loads_workflow
from samsarix_narrative_engine._inputs import parse_json_object, read_utf8_file
from samsarix_narrative_engine.cli import main
from samsarix_narrative_engine.evaluation import _read_json_object

from .conftest import ScriptedProvider
from .test_workflows import _workflow


def test_file_exact_byte_limit_unicode_and_universal_newlines(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    content = "🌱\r\nCafé\rnext".encode()
    path.write_bytes(content)
    assert read_utf8_file(path, max_bytes=len(content), label="fixture") == "🌱\nCafé\nnext"
    with pytest.raises(InputValidationError, match="exceeds"):
        read_utf8_file(path, max_bytes=len(content) - 1, label="fixture")
    path.write_bytes(b"")
    assert read_utf8_file(path, max_bytes=0, label="fixture") == ""


def test_read_is_bounded_even_with_understated_metadata_and_closes_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "growing.txt"
    path.write_bytes(b"x" * 1_000)
    original_stat, original_read, original_close = os.fstat, os.read, os.close
    sizes: list[int] = []
    closed: list[int] = []

    def understate(fd: int) -> SimpleNamespace:
        return SimpleNamespace(st_mode=original_stat(fd).st_mode, st_size=0)

    def read(fd: int, size: int) -> bytes:
        sizes.append(size)
        return original_read(fd, size)

    def close(fd: int) -> None:
        closed.append(fd)
        original_close(fd)

    monkeypatch.setattr(os, "fstat", understate)
    monkeypatch.setattr(os, "read", read)
    monkeypatch.setattr(os, "close", close)
    with pytest.raises(InputValidationError, match="exceeds 10 bytes"):
        read_utf8_file(path, max_bytes=10, label="fixture")
    assert sizes == [11]
    assert len(closed) == 1
    with pytest.raises(OSError):
        original_stat(closed[0])


def test_read_rejects_nonregular_missing_and_invalid_utf8(tmp_path: Path) -> None:
    with pytest.raises(InputValidationError):
        read_utf8_file(tmp_path, max_bytes=100, label="fixture")
    with pytest.raises(InputValidationError, match="regular file"):
        read_utf8_file(os.devnull, max_bytes=100, label="fixture")
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        read_utf8_file(tmp_path / "missing", max_bytes=100, label="fixture")
    path = tmp_path / "invalid"
    path.write_bytes(b"\xff")
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        read_utf8_file(path, max_bytes=100, label="fixture")


def test_input_symlink_to_regular_file_remains_supported(tmp_path: Path) -> None:
    path, alias = tmp_path / "regular", tmp_path / "alias"
    path.write_text("ordinary input", encoding="utf-8")
    try:
        alias.symlink_to(path)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")
    assert read_utf8_file(alias, max_bytes=100, label="fixture") == "ordinary input"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO boundary")
def test_fifo_without_writer_is_rejected_without_waiting(tmp_path: Path) -> None:
    path = tmp_path / "fifo"
    os.mkfifo(path)
    script = (
        "from samsarix_narrative_engine import load_workflow, InputValidationError\n"
        "import sys\n"
        "try: load_workflow(sys.argv[1])\n"
        "except InputValidationError as error:\n"
        "    assert 'regular file' in str(error)\n"
        "else: raise AssertionError('FIFO accepted')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "payload",
    (
        '{"name":"first","na\\u006de":"second"}',
        '{"value":NaN}',
        '{"value":Infinity}',
        '{"value":1e9999}',
        '{"value":"\\ud800"}',
        '{"\\udfff":"key"}',
        '{"value":"\ud800"}',
        '{"value":' + "9" * 5_000 + "}",
        '{"value":' + "[" * 80 + "0" + "]" * 80 + "}",
        '{"value":' + "[" * 10_000 + "0" + "]" * 10_000 + "}",
    ),
    ids=(
        "duplicate",
        "nan",
        "infinity",
        "overflow",
        "surrogate",
        "key-surrogate",
        "literal-surrogate",
        "integer",
        "depth",
        "parser-recursion",
    ),
)
@pytest.mark.parametrize("surface", ("workflow", "run", "evaluation"))
def test_all_json_surfaces_reject_ambiguous_or_unencodable_data(
    payload: str, surface: str, tmp_path: Path
) -> None:
    with pytest.raises(InputValidationError):
        if surface == "workflow":
            loads_workflow(payload)
        elif surface == "run":
            loads_run_bundle(payload)
        else:
            path = tmp_path / "manifest.json"
            path.write_bytes(payload.encode("utf-8", errors="surrogatepass"))
            _read_json_object(path, "evaluation manifest")


def test_json_accepts_valid_surrogate_pair_and_boundary_bytes() -> None:
    payload = '{"emoji":"\\ud83c\\udf31"}'
    assert parse_json_object(payload, max_bytes=len(payload), label="fixture") == {"emoji": "🌱"}
    workflow = _workflow().to_dict()
    workflow["name"] = "Café 🌱"
    loaded = loads_workflow(json.dumps(workflow))
    assert loaded.name == "Café 🌱"
    assert loaded.fingerprint.startswith("sha256:")


@pytest.mark.parametrize("sign", ("", "-"))
def test_json_integer_transport_ceiling_leaves_aggregation_headroom(sign: str) -> None:
    payload = '{"value":' + sign + "9" * 64 + "}"
    value = parse_json_object(payload, max_bytes=1_000, label="fixture")["value"]
    assert value == int(sign + "9" * 64)
    assert json.dumps({"sum": value * 100})
    with pytest.raises(InputValidationError):
        parse_json_object('{"value":' + sign + "9" * 65 + "}", max_bytes=1_000, label="fixture")


class ChunkedInput(io.StringIO):
    def __init__(self, content: str, chunk_size: int = 3) -> None:
        super().__init__(content)
        self.chunk_size = chunk_size
        self.sizes: list[int] = []

    def read(self, size: int = -1) -> str:
        assert size > 0, "stdin reads must have a finite positive bound"
        self.sizes.append(size)
        return super().read(min(size, self.chunk_size))


def test_cli_stdin_short_reads_preserve_trimmed_unicode_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = ChunkedInput("    Café 🌱    ")
    monkeypatch.setattr("sys.stdin", stream)
    provider = ScriptedProvider(("Plan", "# Story\nBody"))
    assert (
        main(
            ("generate", "--prompt-file", "-", "--preset", "quick", "--max-prompt-chars", "6"),
            provider_factory=lambda *_args, **_kwargs: provider,
        )
        == 0
    )
    assert len(stream.sizes) > 2
    assert "Café" in provider.calls[0][0][1].content
    assert "    Café" not in provider.calls[0][0][1].content


@pytest.mark.parametrize("limit", ("0", "-1", "100001", "1000000000000"))
def test_invalid_prompt_limit_is_rejected_before_read_or_provider(
    limit: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    stream = ChunkedInput("not read")
    monkeypatch.setattr("sys.stdin", stream)

    def factory(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("invalid prompt must not construct a provider")

    assert (
        main(
            ("generate", "--prompt-file", "-", "--max-prompt-chars", limit),
            provider_factory=factory,
        )
        == 2
    )
    assert stream.sizes == []


@pytest.mark.parametrize("source", ("stdin", "file", "argv"))
def test_oversized_prompt_is_rejected_before_provider_construction(
    source: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = "x" * 100_002
    stream = ChunkedInput(content, 65_536)
    monkeypatch.setattr("sys.stdin", stream)
    path = tmp_path / "prompt.txt"
    path.write_text(content, encoding="utf-8")
    arguments = (
        ("--prompt", content)
        if source == "argv"
        else ("--prompt-file", "-" if source == "stdin" else str(path))
    )

    def factory(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("oversized prompt must not construct a provider")

    assert main(("generate", *arguments), provider_factory=factory) == 2
    if source == "stdin":
        assert stream.tell() == 100_001


@pytest.mark.parametrize("prompt", ("", "   ", "bad\x00text", "\ud800", "x" * 12_001))
def test_invalid_brief_is_rejected_before_provider(prompt: str) -> None:
    def factory(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("invalid brief must not construct a provider")

    assert main(("generate", "--prompt", prompt), provider_factory=factory) == 2
