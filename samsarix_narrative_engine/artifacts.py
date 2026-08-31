# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Portable, bounded serialization for editable narrative run bundles."""

from __future__ import annotations

import json
from pathlib import Path

from ._inputs import parse_json_object, read_utf8_file
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

    decoded = parse_json_object(payload, max_bytes=MAX_RUN_BUNDLE_BYTES, label="run bundle")
    try:
        return NarrativeResult.from_dict(decoded)
    except ValueError as error:
        raise InputValidationError(f"invalid run bundle: {error}") from error


def load_run_bundle(path: str | Path) -> NarrativeResult:
    """Load one UTF-8 run bundle from disk with a fixed size ceiling."""

    payload = read_utf8_file(path, max_bytes=MAX_RUN_BUNDLE_BYTES, label="run bundle")
    return loads_run_bundle(payload)
