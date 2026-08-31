# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Shared bounded file reads and unambiguous JSON input handling."""

from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path
from typing import Any

from .exceptions import InputValidationError

MAX_JSON_DEPTH = 64
MAX_JSON_INTEGER_DIGITS = 64


def read_utf8_file(path: str | Path, *, max_bytes: int, label: str) -> str:
    """Read a regular file once, never buffering more than max_bytes + 1 bytes."""

    try:
        # O_NONBLOCK prevents a POSIX FIFO from blocking before fstat can reject it.
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise InputValidationError(f"{label} must be a regular file")
            if metadata.st_size > max_bytes:
                raise InputValidationError(f"{label} exceeds {max_bytes} bytes")
            content = bytearray()
            while len(content) <= max_bytes:
                chunk = os.read(descriptor, min(65_536, max_bytes + 1 - len(content)))
                if not chunk:
                    break
                content.extend(chunk)
            if len(content) > max_bytes:
                raise InputValidationError(f"{label} exceeds {max_bytes} bytes")
        finally:
            os.close(descriptor)
        # Preserve the universal-newline behavior of Path.read_text.
        return content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except InputValidationError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise InputValidationError(f"cannot read UTF-8 {label} ({type(error).__name__})") from error


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("nonfinite JSON number")


def _bounded_integer(value: str) -> int:
    # Leave ample headroom for sums and JSON/report conversion after parsing.
    # Real call, duration, and token counts fit far below this transport ceiling.
    if len(value.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
        raise ValueError("JSON integer digit limit exceeded")
    return int(value)


def _validate_json_values(value: Any, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise ValueError("JSON nesting limit exceeded")
    if isinstance(value, str):
        value.encode("utf-8")  # Reject decoded unpaired surrogates, including object keys.
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite JSON number")
    elif isinstance(value, dict):
        for key, child in value.items():
            key.encode("utf-8")
            _validate_json_values(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _validate_json_values(child, depth + 1)


def parse_json_object(payload: str, *, max_bytes: int, label: str) -> dict[str, Any]:
    """Reject ambiguous/unsupported JSON before schema validation or fingerprinting."""

    if not isinstance(payload, str):
        raise InputValidationError(f"{label} payload must be text")
    try:
        # Avoid encoding an arbitrarily large SDK-provided string just to reject it.
        if len(payload) > max_bytes or len(payload.encode("utf-8")) > max_bytes:
            raise InputValidationError(f"{label} exceeds {max_bytes} bytes")
        decoded: Any = json.loads(
            payload,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_int=_bounded_integer,
        )
        _validate_json_values(decoded)
    except InputValidationError:
        raise
    except json.JSONDecodeError as error:
        raise InputValidationError(
            f"invalid {label} JSON at line {error.lineno}, column {error.colno}"
        ) from error
    except (ValueError, RecursionError) as error:
        raise InputValidationError(f"invalid {label} JSON ({type(error).__name__})") from error
    if not isinstance(decoded, dict):
        raise InputValidationError(f"{label} must contain a JSON object")
    return decoded
