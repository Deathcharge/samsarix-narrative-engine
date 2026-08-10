# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Samsarix Narrative Engine public API."""

from .agents import (
    AGENTS,
    PRESETS,
    AgentDefinition,
    applyPresetMode,
    build_plan,
    build_resume_plan,
    get_agent,
    get_all_agents,
    get_all_presets,
    get_preset,
    getAgentConfig,
    workflow_fingerprint,
    workflow_for_preset,
)
from .artifacts import dumps_run_bundle, load_run_bundle, loads_run_bundle
from .engine import (
    NarrativeEngine,
    NarrativeGenerationResult,
    generate_narrative,
    generateNarrative,
)
from .exceptions import (
    BudgetExceededError,
    ConfigurationError,
    InputValidationError,
    NarrativeEngineError,
    OutputError,
    ProviderError,
)
from .models import (
    RUN_BUNDLE_SCHEMA,
    WORKFLOW_SCHEMA,
    GenerationOptions,
    GenerationPlan,
    Message,
    NarrativeResult,
    ProviderResponse,
    StageResult,
    TokenUsage,
    WorkflowDefinition,
    WorkflowRunOptions,
    WorkflowStage,
)
from .providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    Provider,
    build_provider,
    provider_from_env,
)
from .workflows import (
    build_workflow_plan,
    dumps_workflow,
    load_workflow,
    loads_workflow,
)

__version__ = "0.1.0"

__all__ = [
    "AGENTS",
    "PRESETS",
    "AgentDefinition",
    "AnthropicProvider",
    "BudgetExceededError",
    "ConfigurationError",
    "GenerationOptions",
    "GenerationPlan",
    "InputValidationError",
    "Message",
    "NarrativeEngine",
    "NarrativeEngineError",
    "NarrativeGenerationResult",
    "NarrativeResult",
    "OpenAICompatibleProvider",
    "OpenAIProvider",
    "OutputError",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "StageResult",
    "TokenUsage",
    "RUN_BUNDLE_SCHEMA",
    "applyPresetMode",
    "build_plan",
    "WORKFLOW_SCHEMA",
    "WorkflowDefinition",
    "WorkflowRunOptions",
    "WorkflowStage",
    "build_resume_plan",
    "build_provider",
    "generate_narrative",
    "generateNarrative",
    "build_workflow_plan",
    "getAgentConfig",
    "get_agent",
    "get_all_agents",
    "get_all_presets",
    "get_preset",
    "dumps_run_bundle",
    "load_run_bundle",
    "loads_run_bundle",
    "provider_from_env",
    "dumps_workflow",
    "workflow_fingerprint",
    "load_workflow",
    "loads_workflow",
    "workflow_for_preset",
]
