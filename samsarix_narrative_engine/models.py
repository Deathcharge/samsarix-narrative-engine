# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Typed request, response, plan, and usage models."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional

MessageRole = Literal["system", "user", "assistant"]
RUN_BUNDLE_SCHEMA = "samsarix.run/v1"
WORKFLOW_SCHEMA = "samsarix.workflow/v1"
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


def _require_exact_keys(
    data: Mapping[str, Any],
    expected: set[str],
    label: str,
) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")


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
        counts = (self.input_tokens, self.output_tokens, self.total_tokens)
        if any(not isinstance(count, int) or isinstance(count, bool) for count in counts):
            raise ValueError("token counts must be integers")
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
        _require_exact_keys(
            data,
            {"input_tokens", "output_tokens", "total_tokens"},
            "usage",
        )
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
class WorkflowRunOptions:
    """Bounded controls for one explicit workflow run."""

    timeout_seconds: float = 90.0
    max_prompt_chars: int = 12_000
    max_calls: int = 7
    max_total_output_tokens: int = 10_000


@dataclass(frozen=True)
class WorkflowStage:
    """One validated, provider-neutral stage in a workflow definition."""

    stage_id: str
    role: str
    system_prompt: str
    max_output_tokens: int
    context_from: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.stage_id, str)
            or re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", self.stage_id) is None
        ):
            raise ValueError(
                "stage_id must start with a lowercase letter and contain only "
                "lowercase letters, digits, underscores, or hyphens"
            )
        if (
            not isinstance(self.role, str)
            or not self.role.strip()
            or "\x00" in self.role
            or len(self.role) > 256
        ):
            raise ValueError("stage role must contain between 1 and 256 characters")
        if (
            not isinstance(self.system_prompt, str)
            or not self.system_prompt.strip()
            or "\x00" in self.system_prompt
            or len(self.system_prompt) > 20_000
        ):
            raise ValueError("system_prompt must contain between 1 and 20000 safe characters")
        if (
            not isinstance(self.max_output_tokens, int)
            or isinstance(self.max_output_tokens, bool)
            or not 1 <= self.max_output_tokens <= 32_768
        ):
            raise ValueError("stage max_output_tokens must be between 1 and 32768")
        if not isinstance(self.context_from, tuple):
            raise ValueError("context_from must be a tuple of stage identifiers")
        if len(set(self.context_from)) != len(self.context_from):
            raise ValueError("context_from cannot contain duplicate stage identifiers")
        for dependency in self.context_from:
            if (
                not isinstance(dependency, str)
                or re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", dependency) is None
            ):
                raise ValueError("context_from contains an invalid stage identifier")

    def to_dict(self) -> dict[str, Any]:
        """Return the portable workflow-stage representation."""

        return {
            "id": self.stage_id,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "max_output_tokens": self.max_output_tokens,
            "context_from": list(self.context_from),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowStage:
        """Load one stage without coercing malformed values."""

        if not isinstance(data, Mapping):
            raise ValueError("each workflow stage must be an object")
        expected = {"id", "role", "system_prompt", "max_output_tokens", "context_from"}
        unknown = set(data) - expected
        missing = expected - set(data)
        if unknown:
            raise ValueError(
                f"workflow stage contains unknown fields: {', '.join(sorted(unknown))}"
            )
        if missing:
            raise ValueError(f"workflow stage is missing fields: {', '.join(sorted(missing))}")
        raw_context = data.get("context_from")
        if not isinstance(raw_context, list) or any(
            not isinstance(item, str) for item in raw_context
        ):
            raise ValueError("context_from must be an array of stage identifiers")
        return cls(
            stage_id=_required_string(data, "id", max_chars=64),
            role=_required_string(data, "role", max_chars=256),
            system_prompt=_required_string(data, "system_prompt", max_chars=20_000),
            max_output_tokens=_integer(data, "max_output_tokens", minimum=1),
            context_from=tuple(raw_context),
        )


@dataclass(frozen=True)
class WorkflowDefinition:
    """A portable, bounded sequence of narrative operations."""

    workflow_id: str
    name: str
    stages: tuple[WorkflowStage, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.workflow_id, str)
            or re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", self.workflow_id) is None
        ):
            raise ValueError(
                "workflow_id must start with a lowercase letter and contain only "
                "lowercase letters, digits, dots, underscores, or hyphens"
            )
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or "\x00" in self.name
            or len(self.name) > 128
        ):
            raise ValueError("workflow name must contain between 1 and 128 characters")
        if not isinstance(self.stages, tuple) or not 1 <= len(self.stages) <= 20:
            raise ValueError("workflow must contain between 1 and 20 stages")
        if any(not isinstance(stage, WorkflowStage) for stage in self.stages):
            raise ValueError("workflow stages must be WorkflowStage values")

        seen: set[str] = set()
        for stage in self.stages:
            if stage.stage_id in seen:
                raise ValueError(f"duplicate workflow stage_id: {stage.stage_id}")
            unavailable = tuple(item for item in stage.context_from if item not in seen)
            if unavailable:
                raise ValueError(
                    f"stage '{stage.stage_id}' context_from must reference earlier stages; "
                    f"invalid: {', '.join(unavailable)}"
                )
            seen.add(stage.stage_id)
        if sum(stage.max_output_tokens for stage in self.stages) > 100_000:
            raise ValueError("workflow output-token caps cannot exceed 100000 in total")

    @property
    def fingerprint(self) -> str:
        """Return a stable digest of the complete portable definition."""

        encoded = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    def to_dict(self) -> dict[str, Any]:
        """Return the versioned portable workflow representation."""

        return {
            "schema": WORKFLOW_SCHEMA,
            "id": self.workflow_id,
            "name": self.name,
            "stages": [stage.to_dict() for stage in self.stages],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowDefinition:
        """Load one strict versioned workflow definition."""

        if not isinstance(data, Mapping):
            raise ValueError("workflow must be an object")
        expected = {"schema", "id", "name", "stages"}
        unknown = set(data) - expected
        missing = expected - set(data)
        if unknown:
            raise ValueError(f"workflow contains unknown fields: {', '.join(sorted(unknown))}")
        if missing:
            raise ValueError(f"workflow is missing fields: {', '.join(sorted(missing))}")
        if data.get("schema") != WORKFLOW_SCHEMA:
            raise ValueError(f"workflow schema must be '{WORKFLOW_SCHEMA}'")
        raw_stages = data.get("stages")
        if not isinstance(raw_stages, list):
            raise ValueError("workflow stages must be an array")
        return cls(
            workflow_id=_required_string(data, "id", max_chars=64),
            name=_required_string(data, "name", max_chars=128),
            stages=tuple(WorkflowStage.from_dict(stage) for stage in raw_stages),
        )


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
    def workflow_id(self) -> str:
        """Workflow identifier; `preset` is retained as a compatibility field."""

        return self.preset

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
            "workflow_id": self.workflow_id,
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
        _require_exact_keys(
            data,
            {
                "stage_id",
                "role",
                "content",
                "provider",
                "model",
                "usage",
                "duration_ms",
                "max_output_tokens",
            },
            "stage",
        )
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
    workflow: Optional[WorkflowDefinition] = None
    parent_generation_id: Optional[str] = None
    resumed_from_stage: Optional[str] = None

    @property
    def workflow_id(self) -> str:
        """Return the embedded workflow ID through a stable explicit name."""

        return self.workflow.workflow_id if self.workflow is not None else self.preset

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
            "workflow_id": self.workflow_id,
            "workflow": self.workflow.to_dict() if self.workflow is not None else None,
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
        expected = {
            "schema",
            "generation_id",
            "parent_generation_id",
            "resumed_from_stage",
            "created_at",
            "preset",
            "workflow_id",
            "workflow",
            "workflow_fingerprint",
            "creative_brief",
            "title",
            "content",
            "usage",
            "stages",
        }
        unknown = set(data) - expected
        missing = expected - set(data)
        if unknown:
            raise ValueError(f"run bundle contains unknown fields: {', '.join(sorted(unknown))}")
        if missing:
            raise ValueError(f"run bundle is missing fields: {', '.join(sorted(missing))}")
        if data.get("schema") != RUN_BUNDLE_SCHEMA:
            raise ValueError(f"schema must be '{RUN_BUNDLE_SCHEMA}'")
        raw_workflow = data.get("workflow")
        if not isinstance(raw_workflow, Mapping):
            raise ValueError("workflow must be an object")
        workflow = WorkflowDefinition.from_dict(raw_workflow)
        preset = _required_string(data, "preset", max_chars=128)
        if workflow.workflow_id != preset:
            raise ValueError("preset must match the embedded workflow id")
        if _required_string(data, "workflow_id", max_chars=64) != preset:
            raise ValueError("workflow_id must match preset and the embedded workflow id")

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
        if fingerprint != workflow.fingerprint:
            raise ValueError("workflow_fingerprint does not match the embedded workflow")
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
        workflow_stage_ids = tuple(stage.stage_id for stage in workflow.stages)
        if stage_ids != workflow_stage_ids:
            raise ValueError("result stages must exactly match the embedded workflow")
        for result_stage, workflow_stage in zip(stages, workflow.stages, strict=True):
            if (
                result_stage.role != workflow_stage.role
                or result_stage.max_output_tokens != workflow_stage.max_output_tokens
            ):
                raise ValueError("result stage metadata does not match the embedded workflow")

        if (parent_generation_id is None) != (resumed_from_stage is None):
            raise ValueError(
                "parent_generation_id and resumed_from_stage must either both be set "
                "or both be null"
            )
        if resumed_from_stage is not None and resumed_from_stage not in stage_ids:
            raise ValueError("resumed_from_stage must identify a workflow stage")

        result = cls(
            generation_id=generation_id,
            created_at=created_at,
            preset=preset,
            title=_required_string(data, "title", max_chars=160),
            content=_required_string(data, "content"),
            stages=stages,
            creative_brief=_required_string(data, "creative_brief", max_chars=100_000),
            workflow_fingerprint=fingerprint,
            workflow=workflow,
            parent_generation_id=parent_generation_id,
            resumed_from_stage=resumed_from_stage,
        )
        raw_usage = data.get("usage")
        if not isinstance(raw_usage, Mapping):
            raise ValueError("usage must be an object")
        if TokenUsage.from_dict(raw_usage) != result.usage:
            raise ValueError("aggregate usage does not match stage usage")
        if result.content != result.stages[-1].content:
            raise ValueError("content must match the final stage content")
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
