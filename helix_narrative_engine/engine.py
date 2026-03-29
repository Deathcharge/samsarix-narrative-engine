"""
Helix Narrative Engine Core

Multi-LLM creative content generation orchestrator with agent specialization,
quality assessment, and ethical compliance checking.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime

from .agents import getAgentConfig, applyPresetMode, AgentConfig
from .llm_router import callLLM, callLLMWithFallback, LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class UCFSnapshot:
    """Universal Coordination Field state snapshot"""
    harmony: float
    prana: float
    drishti: float
    klesha: float
    resilience: float
    zoom: float


@dataclass
class GenerationMetadata:
    """Metadata about a narrative generation"""
    generationId: str
    title: str
    genre: str
    wordCount: int
    qualityScore: float
    ethicalApproval: bool
    agentContributions: Dict[str, Dict[str, Any]]
    ucfSnapshot: UCFSnapshot


@dataclass
class NarrativeGenerationResult:
    """Result of narrative generation"""
    success: bool
    generationId: str
    title: str
    content: str
    metadata: Optional[GenerationMetadata] = None
    error: Optional[str] = None


@dataclass
class GenerationOptions:
    """Options for narrative generation"""
    preset: Optional[str] = "balanced"
    customAgents: Optional[List[Dict[str, Any]]] = None


async def generateNarrative(
    prompt: str,
    options: Optional[GenerationOptions] = None,
) -> NarrativeGenerationResult:
    """
    Generate narrative content using multi-LLM agent coordination.
    
    This is the main entry point for the Helix Narrative Engine.
    It orchestrates multiple specialized agents to collaboratively create
    high-quality narrative content through a structured generation workflow.
    
    Args:
        prompt: The creative prompt or story concept
        options: Configuration options for agent setup and generation parameters
        
    Returns:
        A complete narrative generation result with metadata and quality metrics
        
    Example:
        >>> from helix_narrative_engine import generateNarrative
        >>> result = await generateNarrative(
        ...     "A hacker discovers a conspiracy in a megacity",
        ...     GenerationOptions(preset="balanced")
        ... )
        >>> print(result.title)
        >>> print(result.content)
    """
    if options is None:
        options = GenerationOptions()
    
    generation_id = f"gen_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:9]}"
    
    try:
        logger.info(f"[Narrative Engine] Starting generation {generation_id}")
        logger.info(f"[Narrative Engine] Preset: {options.preset or 'balanced'}")
        
        # Step 1: Determine agent configuration
        if options.customAgents:
            agent_setup = _buildCustomAgentSetup(options.customAgents)
        else:
            agent_setup = applyPresetMode(options.preset or "balanced")
        
        agent_names = ", ".join(agent_setup.keys())
        logger.info(f"[Narrative Engine] Agents: {agent_names}")
        
        # Step 2: Phase 1 - Oracle (Plot Architecture)
        oracle_setup = agent_setup.get("oracle")
        if not oracle_setup:
            raise ValueError("Oracle agent is required")
        
        plot_structure = await _invokeAgent(
            oracle_setup["config"],
            oracle_setup["provider"],
            oracle_setup["temperature"],
            f"""Create a detailed three-act plot structure for this cyberpunk story prompt:

"{prompt}"

Provide:
1. **Act I Setup**: Introduce protagonist, world, and initial conflict
2. **Act II Confrontation**: Escalate stakes, add complications, include a major twist
3. **Act III Resolution**: Climax and satisfying conclusion

Focus on dramatic structure, pacing, and character arcs. Be specific about key plot points."""
        )
        
        logger.info(f"[Narrative Engine] Oracle phase complete ({oracle_setup['provider']})")
        
        # Step 3: Phase 2 - Lumina (Character Development)
        lumina_setup = agent_setup.get("lumina")
        character_depth = ""
        
        if lumina_setup:
            character_depth = await _invokeAgent(
                lumina_setup["config"],
                lumina_setup["provider"],
                lumina_setup["temperature"],
                f"""Given this plot structure:

{plot_structure}

Develop the protagonist's emotional arc and internal conflicts:
1. **Initial State**: Psychological profile, fears, desires
2. **Emotional Journey**: How they change through the story
3. **Relationships**: Key dynamics with other characters
4. **Internal Conflict**: Core psychological struggle

Make the character feel authentic and emotionally resonant."""
            )
            
            logger.info(f"[Narrative Engine] Lumina phase complete ({lumina_setup['provider']})")
        
        # Step 4: Phase 3 - Gemini (World-Building)
        gemini_setup = agent_setup.get("gemini")
        world_details = ""
        
        if gemini_setup:
            world_details = await _invokeAgent(
                gemini_setup["config"],
                gemini_setup["provider"],
                gemini_setup["temperature"],
                f"""Given this plot:

{plot_structure}

Build the cyberpunk world:
1. **Setting**: Specific locations, atmosphere, sensory details
2. **Technology**: Key tech that drives the plot
3. **Society**: Social structures, power dynamics, culture
4. **Economics**: How the world functions

Make the world feel lived-in and believable."""
            )
            
            logger.info(f"[Narrative Engine] Gemini phase complete ({gemini_setup['provider']})")
        
        # Step 5: Phase 4 - Agni (Creative Twists)
        agni_setup = agent_setup.get("agni")
        creative_twists = ""
        
        if agni_setup:
            creative_twists = await _invokeAgent(
                agni_setup["config"],
                agni_setup["provider"],
                agni_setup["temperature"],
                f"""Given this story foundation:

Plot: {plot_structure[:500]}...
Characters: {character_depth[:300]}...

Inject 2-3 unexpected creative elements:
1. A surprising plot twist that subverts expectations
2. A novel combination of ideas or concepts
3. A bold creative risk that makes the story memorable

Be original and daring."""
            )
            
            logger.info(f"[Narrative Engine] Agni phase complete ({agni_setup['provider']})")
        
        # Step 6: Researcher (Fact-Checking) - Optional
        researcher_setup = agent_setup.get("researcher")
        research_notes = ""
        
        if researcher_setup:
            research_notes = await _invokeAgent(
                researcher_setup["config"],
                researcher_setup["provider"],
                researcher_setup["temperature"],
                f"""Research real-world grounding for this cyberpunk story:

{prompt}

World: {world_details[:300]}...

Provide:
1. Real technologies that could evolve into the story's tech
2. Current social trends that relate to the themes
3. Scientific plausibility notes
4. Relevant citations or references

Keep it brief but credible."""
            )
            
            logger.info(f"[Narrative Engine] Researcher phase complete ({researcher_setup['provider']})")
        
        # Step 7: Synthesis - Generate final narrative
        synthesis_provider = oracle_setup["provider"]
        
        synthesis_messages: List[LLMMessage] = [
            {
                "role": "system",
                "content": "You are a master cyberpunk storyteller. Synthesize the following creative elements into a cohesive, engaging short story (1800-2500 words).",
            },
            {
                "role": "user",
                "content": f"""Create a complete cyberpunk short story using these elements:

**Original Prompt**: {prompt}

**Plot Structure**:
{plot_structure}

**Character Development**:
{character_depth}

**World-Building**:
{world_details}

**Creative Twists**:
{creative_twists}

{f"**Research Notes**:\n{research_notes}\n" if research_notes else ""}

Write the complete story with:
- Vivid prose and sensory details
- Strong pacing and dramatic tension
- Emotional resonance
- Satisfying conclusion
- 1800-2500 words

Begin the story directly—no meta-commentary.""",
            },
        ]
        
        final_narrative = await callLLM(
            synthesis_provider,
            synthesis_messages,
            temperature=0.8,
            max_tokens=4000,
        )
        
        logger.info("[Narrative Engine] Synthesis phase complete")
        
        # Step 8: Claude (Quality Assessment)
        claude_setup = agent_setup.get("claude")
        quality_score = 0.85
        
        if claude_setup:
            quality_assessment = await _invokeAgent(
                claude_setup["config"],
                claude_setup["provider"],
                0.3,
                f"""Assess the quality of this story:

{final_narrative['content'][:2000]}...

Rate on a scale of 0.0 to 1.0 for:
1. Narrative coherence
2. Character development
3. Prose quality
4. Pacing
5. Originality

Provide only a single number (e.g., 0.87) representing the overall quality score."""
            )
            
            # Extract score from response
            import re
            score_match = re.search(r"0\.\d+|1\.0", quality_assessment)
            if score_match:
                quality_score = float(score_match.group(0))
            
            logger.info(f"[Narrative Engine] Quality assessment: {quality_score}")
        
        # Step 9: Kavach (Ethical Review)
        kavach_setup = agent_setup.get("kavach")
        ethical_approval = True
        
        if kavach_setup:
            ethical_review = await _invokeAgent(
                kavach_setup["config"],
                kavach_setup["provider"],
                0.2,
                f"""Review this story for ethical compliance:
- Nonmaleficence (do no harm)
- Autonomy (respect agency)
- Compassion (empathic resonance)
- Humility (acknowledge limitations)

Story excerpt:
{final_narrative['content'][:1500]}...

Respond with ONLY "APPROVED" or "REJECTED" followed by brief reasoning."""
            )
            
            ethical_approval = "APPROVED" in ethical_review.upper()
            logger.info(f"[Narrative Engine] Ethical review: {'APPROVED' if ethical_approval else 'REJECTED'}")
        
        # Step 10: Extract title
        import re
        title_match = re.match(r"^#\s+(.+)$", final_narrative["content"], re.MULTILINE)
        if not title_match:
            title_match = re.match(r"^(.+)$", final_narrative["content"], re.MULTILINE)
        
        title = title_match.group(1).strip() if title_match else "Untitled Story"
        
        # Step 11: Calculate metadata
        word_count = len(final_narrative["content"].split())
        
        agent_contributions = {}
        for agent_id, setup in agent_setup.items():
            agent_contributions[agent_id] = {
                "provider": setup["provider"],
                "tokens": 0,  # Would track actual tokens in production
                "role": setup["config"]["role"],
            }
        
        ucf_snapshot = UCFSnapshot(
            harmony=0.68 + (quality_score - 0.85) * 0.2,
            prana=0.75,
            drishti=0.80,
            klesha=0.02 if ethical_approval else 0.15,
            resilience=1.10,
            zoom=1.15,
        )
        
        metadata = GenerationMetadata(
            generationId=generation_id,
            title=title,
            genre="cyberpunk",
            wordCount=word_count,
            qualityScore=quality_score,
            ethicalApproval=ethical_approval,
            agentContributions=agent_contributions,
            ucfSnapshot=ucf_snapshot,
        )
        
        logger.info(f"[Narrative Engine] Generation {generation_id} complete!")
        
        return NarrativeGenerationResult(
            success=True,
            generationId=generation_id,
            title=title,
            content=final_narrative["content"],
            metadata=metadata,
        )
    
    except Exception as error:
        logger.error(f"[Narrative Engine] Generation {generation_id} failed: {error}")
        return NarrativeGenerationResult(
            success=False,
            generationId=generation_id,
            title="Error",
            content="",
            error=str(error),
        )


async def _invokeAgent(
    config: AgentConfig,
    provider: LLMProvider,
    temperature: float,
    user_prompt: str,
) -> str:
    """Invoke a single agent with specified LLM provider"""
    messages: List[LLMMessage] = [
        {"role": "system", "content": config["systemPrompt"]},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        logger.info(f"[Narrative Engine] Invoking agent with {provider}...")
        response = await callLLM(
            provider,
            messages,
            temperature=temperature,
            max_tokens=2000,
        )
        logger.info("[Narrative Engine] Agent response received")
        return response["content"]
    except Exception as error:
        logger.warning(f"[Narrative Engine] Provider {provider} failed, using fallback: {error}")
        fallback_result = await callLLMWithFallback(
            messages,
            temperature=temperature,
            max_tokens=2000,
            log_errors=True,
        )
        logger.info("[Narrative Engine] Fallback succeeded")
        return fallback_result["content"]


def _buildCustomAgentSetup(
    custom_agents: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Build custom agent setup from user configuration"""
    result = {}
    
    for custom in custom_agents:
        config = getAgentConfig(custom["agentId"])
        if not config:
            continue
        
        provider = custom.get("provider") or config["defaultProvider"]
        temperature = custom.get("temperature", config["defaultTemperature"])
        multiplicity = custom.get("multiplicity", 1)
        
        # Handle multiplicity (e.g., 3x Oracle agents)
        for i in range(multiplicity):
            key = f"{custom['agentId']}_{i + 1}" if multiplicity > 1 else custom["agentId"]
            result[key] = {
                "config": config,
                "provider": provider,
                "temperature": temperature,
            }
    
    return result
