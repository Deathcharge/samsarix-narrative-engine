# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Typed request, response, plan, and usage models."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional

MessageRole = Literal["system", "user", "assistant"]
RUN_BUNDLE_SCHEMA = "samsarix.run/v1"
MAX_BUNDLE_TEXT_CHARS = 2_000_000


def _required_string(
    data: Mapping[str, Any],
    key: str,
    *,
    max_chars: int = MAX_BUNDLE_TEXT_CHARS,
) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    if "\x00" in value:
        raise ValueError(f"{key} cannot contain null bytes")
    if len(value) > max_chars:
        raise ValueError(f"{key} exceeds {max_chars} characters")
    return value


def _optional_string(data: Mapping[str, Any], key: str, *, max_chars: int = 160) -> Optional[str]:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be null or a non-empty string")
    if "\x00" in value or len(value) > max_chars:
        raise ValueError(f"{key} is invalid")
    return value


def _integer(data: Mapping[str, Any], key: str, *, minimum: int = 0) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{key} must be an integer greater than or equal to {minimum}")
    return value


@dataclass(frozen=True)
class Message:
    """A provider-neutral text message."""

    role: MessageRole
    content: str


@dataclass(frozen=True)
class TokenUsage:
    """Token counts reported by a provider.

    A zero value means that the provider did not report that count; it is not an
    estimate.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if min(self.input_tokens, self.output_tokens, self.total_tokens) < 0:
            raise ValueError("token counts cannot be negative")

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-serializable representation."""

        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TokenUsage:
        """Load strictly validated provider-reported token counts."""

        if not isinstance(data, Mapping):
            raise ValueError("usage must be an object")
        return cls(
            input_tokens=_integer(data, "input_tokens"),
            output_tokens=_integer(data, "output_tokens"),
            total_tokens=_integer(data, "total_tokens"),
        )


@dataclass(frozen=True)
class ProviderResponse:
    """Normalized response from one provider request."""

    content: str
    provider: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass(frozen=True)
class GenerationOptions:
    """Bounded controls for one workflow run."""

    preset: str = "balanced"
    timeout_seconds: float = 90.0
    max_prompt_chars: int = 12_000
    max_calls: int = 7
    max_total_output_tokens: int = 10_000


@dataclass(frozen=True)
class PlannedStage:
    """One provider call in a generation plan."""

    stage_id: str
    role: str
    max_output_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "stage_id": self.stage_id,
            "role": self.role,
            "max_output_tokens": self.max_output_tokens,
        }


@dataclass(frozen=True)
class GenerationPlan:
    """A preflight view of calls and maximum output-token exposure."""

    preset: str
    stages: tuple[PlannedStage, ...]

    @property
    def max_calls(self) -> int:
        """Number of provider calls in the plan."""

        return len(self.stages)

    @property
    def max_output_tokens(self) -> int:
        """Sum of provider output caps across the plan."""

        return sum(stage.max_output_tokens for stage in self.stages)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "preset": self.preset,
            "max_calls": self.max_calls,
            "max_output_tokens": self.max_output_tokens,
            "stages": [stage.to_dict() for stage in self.stages],
        }


@dataclass(frozen=True)
class StageResult:
    """Inspectable artifact and accounting for one completed stage."""

    stage_id: str
    role: str
    content: str
    provider: str
    model: str
    usage: TokenUsage
    duration_ms: int
    max_output_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "stage_id": self.stage_id,
            "role": self.role,
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage.to_dict(),
            "duration_ms": self.duration_ms,
            "max_output_tokens": self.max_output_tokens,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StageResult:
        """Load one strictly validated stage artifact."""

        if not isinstance(data, Mapping):
            raise ValueError("each stage must be an object")
        usage = data.get("usage")
        if not isinstance(usage, Mapping):
            raise ValueError("stage usage must be an object")
        return cls(
            stage_id=_required_string(data, "stage_id", max_chars=128),
            role=_required_string(data, "role", max_chars=256),
            content=_required_string(data, "content"),
            provider=_required_string(data, "provider", max_chars=128),
            model=_required_string(data, "model", max_chars=256),
            usage=TokenUsage.from_dict(usage),
            duration_ms=_integer(data, "duration_ms"),
            max_output_tokens=_integer(data, "max_output_tokens", minimum=1),
        )


@dataclass(frozen=True)
class NarrativeResult:
    """Successful narrative workflow output."""

    generation_id: str
    created_at: str
    preset: str
    title: str
    content: str
    stages: tuple[StageResult, ...]
    creative_brief: str = ""
    workflow_fingerprint: str = ""
    parent_generation_id: Optional[str] = None
    resumed_from_stage: Optional[str] = None

    @property
    def usage(self) -> TokenUsage:
        """Aggregate provider-reported usage across completed stages."""

        total = TokenUsage()
        for stage in self.stages:
            total = total + stage.usage
        return total

    def to_dict(self) -> dict[str, Any]:
        """Return the narrative and all intermediate artifacts as JSON data."""

        return {
            "schema": RUN_BUNDLE_SCHEMA,
            "generation_id": self.generation_id,
            "parent_generation_id": self.parent_generation_id,
            "resumed_from_stage": self.resumed_from_stage,
            "created_at": self.created_at,
            "preset": self.preset,
            "workflow_fingerprint": self.workflow_fingerprint,
            "creative_brief": self.creative_brief,
            "title": self.title,
            "content": self.content,
            "usage": self.usage.to_dict(),
            "stages": [stage.to_dict() for stage in self.stages],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> NarrativeResult:
        """Load a versioned run bundle without coercing malformed fields."""

        if not isinstance(data, Mapping):
            raise ValueError("run bundle must be an object")
        if data.get("schema") != RUN_BUNDLE_SCHEMA:
            raise ValueError(f"schema must be '{RUN_BUNDLE_SCHEMA}'")

        generation_id = _required_string(data, "generation_id", max_chars=128)
        created_at = _required_string(data, "created_at", max_chars=64)
        try:
            parsed_created_at = datetime.fromisoformat(created_at)
        except ValueError as error:
            raise ValueError("created_at must be an ISO-8601 timestamp") from error
        if parsed_created_at.tzinfo is None:
            raise ValueError("created_at must include a timezone")

        fingerprint = _required_string(data, "workflow_fingerprint", max_chars=71)
        if re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint) is None:
            raise ValueError("workflow_fingerprint must be a sha256 digest")

        raw_stages = data.get("stages")
        if not isinstance(raw_stages, list) or not raw_stages:
            raise ValueError("stages must be a non-empty array")
        stages = tuple(StageResult.from_dict(stage) for stage in raw_stages)
        if len(stages) > 20:
            raise ValueError("stages cannot contain more than 20 entries")
        stage_ids = tuple(stage.stage_id for stage in stages)
        if len(set(stage_ids)) != len(stage_ids):
            raise ValueError("stage identifiers must be unique")

        parent_generation_id = _optional_string(data, "parent_generation_id", max_chars=128)
        resumed_from_stage = _optional_string(data, "resumed_from_stage", max_chars=128)
        if (parent_generation_id is None) != (resumed_from_stage is None):
            raise ValueError(
                "parent_generation_id and resumed_from_stage must either both be set "
                "or both be null"
            )

        result = cls(
            generation_id=generation_id,
            created_at=created_at,
            preset=_required_string(data, "preset", max_chars=128),
            title=_required_string(data, "title", max_chars=160),
            content=_required_string(data, "content"),
            stages=stages,
            creative_brief=_required_string(data, "creative_brief", max_chars=100_000),
            workflow_fingerprint=fingerprint,
            parent_generation_id=parent_generation_id,
            resumed_from_stage=resumed_from_stage,
        )
        raw_usage = data.get("usage")
        if not isinstance(raw_usage, Mapping):
            raise ValueError("usage must be an object")
        if TokenUsage.from_dict(raw_usage) != result.usage:
            raise ValueError("aggregate usage does not match stage usage")
        return result

    def estimated_cost(
        self, input_per_million: float, output_per_million: float
    ) -> Optional[float]:
        """Estimate cost from caller-supplied current provider prices.

        Returns ``None`` when the provider did not report any token counts.
        """

        if (
            not math.isfinite(input_per_million)
            or not math.isfinite(output_per_million)
            or input_per_million < 0
            or output_per_million < 0
        ):
            raise ValueError("token prices must be finite and nonnegative")
        if self.usage.input_tokens == 0 and self.usage.output_tokens == 0:
            return None
        return (
            self.usage.input_tokens * input_per_million
            + self.usage.output_tokens * output_per_million
        ) / 1_000_000
