# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Typed request, response, plan, and usage models."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

MessageRole = Literal["system", "user", "assistant"]


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


@dataclass(frozen=True)
class NarrativeResult:
    """Successful narrative workflow output."""

    generation_id: str
    created_at: str
    preset: str
    title: str
    content: str
    stages: tuple[StageResult, ...]

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
            "generation_id": self.generation_id,
            "created_at": self.created_at,
            "preset": self.preset,
            "title": self.title,
            "content": self.content,
            "usage": self.usage.to_dict(),
            "stages": [stage.to_dict() for stage in self.stages],
        }

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
