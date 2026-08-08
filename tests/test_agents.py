# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Agent registry and plan tests."""

from __future__ import annotations

import pytest

from samsarix_narrative_engine.agents import (
    AGENTS,
    PRESETS,
    applyPresetMode,
    build_plan,
    build_resume_plan,
    get_agent,
    get_all_agents,
    get_all_presets,
    get_preset,
    getAgentConfig,
    workflow_fingerprint,
)


def test_agent_registry_is_complete_and_immutable() -> None:
    assert set(AGENTS) == {
        "architect",
        "character",
        "world",
        "provocateur",
        "writer",
        "critic",
        "reviser",
    }
    assert get_all_agents() is AGENTS
    with pytest.raises(TypeError):
        AGENTS["new"] = AGENTS["writer"]  # type: ignore[index]


def test_presets_have_exact_bounded_plans() -> None:
    assert get_all_presets() is PRESETS
    assert get_preset("quick") == ("architect", "writer")
    assert build_plan("quick").max_calls == 2
    assert build_plan("quick").max_output_tokens == 3_600
    assert build_plan("balanced").max_calls == 4
    assert build_plan("balanced").max_output_tokens == 5_200
    assert build_plan("polished").max_calls == 7
    assert build_plan("polished").max_output_tokens == 9_500
    assert build_resume_plan("polished", "critic").max_calls == 2
    assert build_resume_plan("polished", "critic").max_output_tokens == 3_700
    assert workflow_fingerprint("quick").startswith("sha256:")
    assert len(workflow_fingerprint("quick")) == 71


def test_unknown_registry_values_are_explicit() -> None:
    assert get_agent("missing") is None
    assert get_preset("missing") is None
    with pytest.raises(ValueError, match="unknown preset"):
        build_plan("missing")
    with pytest.raises(ValueError, match="not in preset"):
        build_resume_plan("quick", "critic")


def test_compatibility_helpers_return_bounded_copies() -> None:
    architect = getAgentConfig("architect")
    assert architect is not None
    assert architect["agentId"] == "architect"
    assert architect["contextFrom"] == []
    assert getAgentConfig("missing") is None

    fallback = applyPresetMode("missing")
    assert tuple(fallback) == PRESETS["balanced"]
    fallback["architect"]["maxOutputTokens"] = 1
    assert AGENTS["architect"].max_output_tokens == 1_000
