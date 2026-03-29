"""
Helix Narrative Engine
Multi-LLM creative content generation with agent specialization

A Python library for generating high-quality narrative content through
coordinated multi-agent workflows. Perfect for creative AI applications,
story generation, and content automation.
"""

from .engine import (
    generateNarrative,
    NarrativeGenerationResult,
    GenerationMetadata,
    GenerationOptions,
)
from .agents import (
    getAgentConfig,
    applyPresetMode,
    PRESET_MODES,
)

__version__ = "1.0.0"
__author__ = "Helix Team"
__license__ = "Apache 2.0"

__all__ = [
    "generateNarrative",
    "NarrativeGenerationResult",
    "GenerationMetadata",
    "GenerationOptions",
    "getAgentConfig",
    "applyPresetMode",
    "PRESET_MODES",
]
