# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Portable, bounded serialization for editable narrative run bundles."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .exceptions import InputValidationError
from .models import NarrativeResult

MAX_RUN_BUNDLE_BYTES = 16 * 1024 * 1024


def dumps_run_bundle(result: NarrativeResult, *, indent: int = 2) -> str:
    """Serialize a result as a portable, human-editable run bundle."""

    if not isinstance(result, NarrativeResult):
        raise TypeError("result must be a NarrativeResult")
    data = result.to_dict()
    try:
        NarrativeResult.from_dict(data)
    except ValueError as error:
        raise InputValidationError(f"result cannot form a run bundle: {error}") from error
    payload = json.dumps(data, ensure_ascii=False, indent=indent) + "\n"
    if len(payload.encode("utf-8")) > MAX_RUN_BUNDLE_BYTES:
        raise InputValidationError(f"run bundle exceeds {MAX_RUN_BUNDLE_BYTES} bytes")
    return payload


def loads_run_bundle(payload: str) -> NarrativeResult:
    """Load and strictly validate one run bundle from JSON text."""

    if not isinstance(payload, str):
        raise InputValidationError("run bundle payload must be text")
    if len(payload.encode("utf-8")) > MAX_RUN_BUNDLE_BYTES:
        raise InputValidationError(f"run bundle exceeds {MAX_RUN_BUNDLE_BYTES} bytes")
    try:
        decoded: Any = json.loads(payload)
    except json.JSONDecodeError as error:
        raise InputValidationError(
            f"invalid run bundle JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(decoded, Mapping):
        raise InputValidationError("run bundle must contain a JSON object")
    try:
        return NarrativeResult.from_dict(decoded)
    except ValueError as error:
        raise InputValidationError(f"invalid run bundle: {error}") from error


def load_run_bundle(path: str | Path) -> NarrativeResult:
    """Load one UTF-8 run bundle from disk with a fixed size ceiling."""

    selected = Path(path)
    try:
        if selected.stat().st_size > MAX_RUN_BUNDLE_BYTES:
            raise InputValidationError(f"run bundle exceeds {MAX_RUN_BUNDLE_BYTES} bytes")
        payload = selected.read_text(encoding="utf-8")
    except InputValidationError:
        raise
    except (OSError, UnicodeError) as error:
        raise InputValidationError(
            f"cannot read UTF-8 run bundle ({type(error).__name__})"
        ) from error
    return loads_run_bundle(payload)
