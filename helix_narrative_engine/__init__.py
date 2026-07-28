"""Helix Narrative Engine public API."""

from .agents import (
    AGENTS,
    PRESETS,
    AgentDefinition,
    applyPresetMode,
    build_plan,
    get_agent,
    get_all_agents,
    get_all_presets,
    get_preset,
    getAgentConfig,
)
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
    GenerationOptions,
    GenerationPlan,
    Message,
    NarrativeResult,
    ProviderResponse,
    StageResult,
    TokenUsage,
)
from .providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    Provider,
    build_provider,
    provider_from_env,
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
    "applyPresetMode",
    "build_plan",
    "build_provider",
    "generate_narrative",
    "generateNarrative",
    "getAgentConfig",
    "get_agent",
    "get_all_agents",
    "get_all_presets",
    "get_preset",
    "provider_from_env",
]
