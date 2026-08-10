# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Specialist stage definitions and bounded workflow presets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Optional

from .models import (
    GenerationPlan,
    WorkflowDefinition,
    WorkflowStage,
)
from .workflows import build_workflow_plan


@dataclass(frozen=True)
class AgentDefinition:
    """A deterministic workflow stage powered by the configured provider."""

    agent_id: str
    name: str
    role: str
    system_prompt: str
    max_output_tokens: int
    context_from: tuple[str, ...] = ()


_AGENTS = {
    "architect": AgentDefinition(
        agent_id="architect",
        name="Oracle",
        role="Story architect",
        system_prompt=(
            "You are a story architect. Turn the supplied creative brief into a compact, "
            "actionable blueprint with premise, protagonist goal, central conflict, three-act "
            "progression, climax, resolution, tone, and continuity constraints. Preserve the "
            "author's intent. Do not claim to have researched facts or sources."
        ),
        max_output_tokens=1_000,
    ),
    "character": AgentDefinition(
        agent_id="character",
        name="Lumina",
        role="Character editor",
        system_prompt=(
            "You are a character editor. Based only on the supplied brief and blueprint, define "
            "the protagonist's motivation, fear, contradiction, relationships, choices, and "
            "emotional change. Flag continuity risks instead of inventing external facts."
        ),
        max_output_tokens=800,
        context_from=("architect",),
    ),
    "world": AgentDefinition(
        agent_id="world",
        name="Gemini",
        role="World and continuity editor",
        system_prompt=(
            "You are a world and continuity editor. Establish a small set of concrete setting "
            "details, rules, pressures, and sensory motifs that support the blueprint. Keep the "
            "world internally consistent. Do not fabricate citations or imply factual research."
        ),
        max_output_tokens=800,
        context_from=("architect",),
    ),
    "provocateur": AgentDefinition(
        agent_id="provocateur",
        name="Agni",
        role="Originality editor",
        system_prompt=(
            "You are an originality editor. Suggest at most three specific, usable changes that "
            "avoid cliche while preserving the established ending, character agency, tone, and "
            "world rules. Prefer one strong choice over a pile of random twists."
        ),
        max_output_tokens=600,
        context_from=("architect", "character", "world"),
    ),
    "writer": AgentDefinition(
        agent_id="writer",
        name="Scribe",
        role="Draft writer",
        system_prompt=(
            "You are the draft writer. Write a complete short story from the supplied brief and "
            "editorial artifacts. Start with a single Markdown H1 title, then the story. Do not "
            "include planning notes, analysis, scores, citations, or meta-commentary. Resolve the "
            "central conflict and respect every explicit content constraint in the brief."
        ),
        max_output_tokens=2_600,
        context_from=("architect", "character", "world", "provocateur"),
    ),
    "critic": AgentDefinition(
        agent_id="critic",
        name="Kavach",
        role="Revision editor",
        system_prompt=(
            "You are a revision editor, not a safety certifier. Review the supplied draft for "
            "coherence, pacing, character agency, continuity, avoidable stereotypes, and alignment "
            "with the author's brief. Return a prioritized revision memo with concrete fixes. Do "
            "not output a numeric quality score or claim ethical approval."
        ),
        max_output_tokens=900,
        context_from=("writer",),
    ),
    "reviser": AgentDefinition(
        agent_id="reviser",
        name="Scribe",
        role="Final reviser",
        system_prompt=(
            "You are the final reviser. Apply only revision notes that improve alignment with the "
            "author's brief. Return the complete revised story, beginning with one Markdown H1 "
            "title. Do not mention the workflow, the memo, or any quality or safety judgment."
        ),
        max_output_tokens=2_800,
        context_from=("architect", "writer", "critic"),
    ),
}

AGENTS: Mapping[str, AgentDefinition] = MappingProxyType(_AGENTS)

_PRESETS = {
    "quick": ("architect", "writer"),
    "balanced": ("architect", "character", "world", "writer"),
    "polished": (
        "architect",
        "character",
        "world",
        "provocateur",
        "writer",
        "critic",
        "reviser",
    ),
}

PRESETS: Mapping[str, tuple[str, ...]] = MappingProxyType(_PRESETS)


def get_agent(agent_id: str) -> Optional[AgentDefinition]:
    """Return an agent definition, or ``None`` for an unknown identifier."""

    return AGENTS.get(agent_id)


def get_all_agents() -> Mapping[str, AgentDefinition]:
    """Return the immutable public agent registry."""

    return AGENTS


def get_preset(preset: str) -> Optional[tuple[str, ...]]:
    """Return a preset's ordered stage identifiers."""

    return PRESETS.get(preset)


def get_all_presets() -> Mapping[str, tuple[str, ...]]:
    """Return the immutable public preset registry."""

    return PRESETS


def workflow_for_preset(preset: str) -> WorkflowDefinition:
    """Return a portable workflow definition for one built-in preset."""

    stage_ids = get_preset(preset)
    if stage_ids is None:
        choices = ", ".join(PRESETS)
        raise ValueError(f"unknown preset '{preset}'; choose one of: {choices}")
    return WorkflowDefinition(
        workflow_id=preset,
        name=f"Samsarix {preset.title()}",
        stages=tuple(
            WorkflowStage(
                stage_id=agent_id,
                role=AGENTS[agent_id].role,
                system_prompt=AGENTS[agent_id].system_prompt,
                max_output_tokens=AGENTS[agent_id].max_output_tokens,
                context_from=tuple(
                    dependency
                    for dependency in AGENTS[agent_id].context_from
                    if dependency in stage_ids
                ),
            )
            for agent_id in stage_ids
        ),
    )


def build_plan(preset: str) -> GenerationPlan:
    """Build the exact provider-call plan for a preset.

    Raises:
        ValueError: If ``preset`` is unknown.
    """

    return build_workflow_plan(workflow_for_preset(preset))


def build_resume_plan(preset: str, from_stage: str) -> GenerationPlan:
    """Build the suffix of a preset that will be rerun from ``from_stage``."""

    return build_workflow_plan(workflow_for_preset(preset), from_stage)


def workflow_fingerprint(selection: str | WorkflowDefinition) -> str:
    """Return the stable digest of a built-in or explicit workflow."""

    workflow = workflow_for_preset(selection) if isinstance(selection, str) else selection
    return workflow.fingerprint


# Compatibility helpers for the original 1.0 surface. New code should use the
# snake_case functions and immutable dataclasses above.
def getAgentConfig(agent_id: str) -> Optional[dict[str, Any]]:
    """Return an old-style agent mapping for compatibility."""

    agent = get_agent(agent_id)
    if agent is None:
        return None
    return {
        "agentId": agent.agent_id,
        "name": agent.name,
        "role": agent.role,
        "systemPrompt": agent.system_prompt,
        "maxOutputTokens": agent.max_output_tokens,
        "contextFrom": list(agent.context_from),
    }


def applyPresetMode(preset_id: str) -> dict[str, dict[str, Any]]:
    """Return a bounded old-style preset mapping for compatibility."""

    preset = get_preset(preset_id)
    if preset is None:
        preset = PRESETS["balanced"]
    return {
        agent_id: {
            "config": getAgentConfig(agent_id),
            "maxOutputTokens": AGENTS[agent_id].max_output_tokens,
        }
        for agent_id in preset
    }


PRESET_MODES = PRESETS
