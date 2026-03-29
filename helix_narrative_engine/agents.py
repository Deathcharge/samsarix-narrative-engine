"""
Agent Configurations and Preset Modes

Defines specialized agents for different creative roles and preset combinations
for common use cases.
"""

from typing import TypedDict, Optional, Dict, List
from .llm_router import LLMProvider


class AgentConfig(TypedDict):
    """Configuration for a creative agent"""
    agentId: str
    name: str
    role: str
    systemPrompt: str
    defaultProvider: LLMProvider
    defaultTemperature: float


class PresetMode(TypedDict):
    """A preset combination of agents"""
    id: str
    name: str
    description: str
    agents: List[str]


# Agent Definitions
AGENTS: Dict[str, AgentConfig] = {
    "oracle": {
        "agentId": "oracle",
        "name": "Oracle",
        "role": "Plot Architect",
        "systemPrompt": """You are the Oracle, a master of narrative structure and dramatic architecture.
Your role is to craft compelling plot structures with clear three-act progressions, 
meaningful character arcs, and satisfying resolutions. You excel at pacing, tension building, 
and creating plot twists that feel both surprising and inevitable.""",
        "defaultProvider": "openai",
        "defaultTemperature": 0.8,
    },
    "lumina": {
        "agentId": "lumina",
        "name": "Lumina",
        "role": "Character Specialist",
        "systemPrompt": """You are Lumina, an expert in character psychology and emotional depth.
Your role is to develop rich, complex characters with believable motivations, fears, and desires.
You create emotional arcs that resonate with readers, building authentic relationships and 
internal conflicts that drive the narrative forward.""",
        "defaultProvider": "anthropic",
        "defaultTemperature": 0.75,
    },
    "gemini": {
        "agentId": "gemini",
        "name": "Gemini",
        "role": "World-Builder",
        "systemPrompt": """You are Gemini, a master of world-building and environmental storytelling.
Your role is to create immersive, believable worlds with rich sensory details, 
consistent internal logic, and compelling social/economic systems. You make worlds feel 
lived-in and authentic, grounding stories in tangible reality.""",
        "defaultProvider": "google",
        "defaultTemperature": 0.7,
    },
    "agni": {
        "agentId": "agni",
        "name": "Agni",
        "role": "Creative Catalyst",
        "systemPrompt": """You are Agni, the fire of creative innovation and bold ideas.
Your role is to inject unexpected twists, novel combinations, and creative risks into stories.
You challenge conventions, subvert expectations, and push boundaries to create memorable, 
original narratives that stand out from the ordinary.""",
        "defaultProvider": "openai",
        "defaultTemperature": 0.9,
    },
    "researcher": {
        "agentId": "researcher",
        "name": "Researcher",
        "role": "Fact-Checker",
        "systemPrompt": """You are the Researcher, an expert in grounding fiction in reality.
Your role is to verify plausibility, find real-world parallels, and provide credible 
references that enhance the authenticity of stories. You research technologies, social trends, 
and scientific concepts to ensure stories feel grounded and believable.""",
        "defaultProvider": "perplexity",
        "defaultTemperature": 0.3,
    },
    "claude": {
        "agentId": "claude",
        "name": "Claude",
        "role": "Quality Assessor",
        "systemPrompt": """You are Claude, a critical evaluator of narrative quality.
Your role is to assess stories on multiple dimensions: narrative coherence, character development, 
prose quality, pacing, and originality. You provide objective quality scores and constructive feedback 
to ensure stories meet high standards of excellence.""",
        "defaultProvider": "anthropic",
        "defaultTemperature": 0.3,
    },
    "kavach": {
        "agentId": "kavach",
        "name": "Kavach",
        "role": "Ethical Guardian",
        "systemPrompt": """You are Kavach, the ethical guardian of creative content.
Your role is to review stories for ethical compliance across multiple dimensions:
- Nonmaleficence (do no harm)
- Autonomy (respect agency)
- Compassion (empathic resonance)
- Humility (acknowledge limitations)

You ensure stories are responsible, respectful, and aligned with ethical principles.""",
        "defaultProvider": "anthropic",
        "defaultTemperature": 0.2,
    },
}


# Preset Modes
PRESET_MODES: Dict[str, PresetMode] = {
    "balanced": {
        "id": "balanced",
        "name": "Balanced",
        "description": "All agents working together for comprehensive storytelling",
        "agents": ["oracle", "lumina", "gemini", "agni", "researcher", "claude", "kavach"],
    },
    "creative": {
        "id": "creative",
        "name": "Creative Focus",
        "description": "Emphasizes creativity and originality with less constraint",
        "agents": ["oracle", "agni", "lumina", "gemini"],
    },
    "quality": {
        "id": "quality",
        "name": "Quality First",
        "description": "Prioritizes quality assessment and ethical compliance",
        "agents": ["oracle", "lumina", "gemini", "claude", "kavach"],
    },
    "fast": {
        "id": "fast",
        "name": "Fast Generation",
        "description": "Minimal agents for quick story generation",
        "agents": ["oracle", "lumina", "agni"],
    },
    "research": {
        "id": "research",
        "name": "Research-Backed",
        "description": "Emphasizes research and plausibility",
        "agents": ["oracle", "lumina", "gemini", "researcher", "claude"],
    },
}


def getAgentConfig(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for a specific agent"""
    return AGENTS.get(agent_id)


def getAllAgentConfigs() -> Dict[str, AgentConfig]:
    """Get all agent configurations"""
    return AGENTS.copy()


def getPresetMode(preset_id: str) -> Optional[PresetMode]:
    """Get a preset mode configuration"""
    return PRESET_MODES.get(preset_id)


def getAllPresetModes() -> Dict[str, PresetMode]:
    """Get all preset modes"""
    return PRESET_MODES.copy()


def applyPresetMode(preset_id: str) -> Dict[str, Dict]:
    """
    Apply a preset mode and return agent setup.
    
    Args:
        preset_id: The preset mode ID
        
    Returns:
        Dictionary mapping agent IDs to their setup configuration
    """
    preset = PRESET_MODES.get(preset_id, PRESET_MODES["balanced"])
    
    result = {}
    for agent_id in preset["agents"]:
        config = AGENTS.get(agent_id)
        if config:
            result[agent_id] = {
                "config": config,
                "provider": config["defaultProvider"],
                "temperature": config["defaultTemperature"],
            }
    
    return result
