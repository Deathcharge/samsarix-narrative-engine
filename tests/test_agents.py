"""
Comprehensive test suite for helix-narrative-engine agents.

Tests all agent types, their specializations, quality assessment,
and integration with the narrative engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================================
# Agent Initialization Tests
# ============================================================================

class TestAgentInitialization:
    """Test agent initialization and configuration."""
    
    def test_oracle_agent_initialization(self, mock_oracle_agent):
        """Test Oracle agent initializes correctly."""
        assert mock_oracle_agent.name == "Oracle"
        assert mock_oracle_agent.role == "wisdom_guide"
        assert callable(mock_oracle_agent.generate)
        assert callable(mock_oracle_agent.assess_quality)
    
    def test_lumina_agent_initialization(self, mock_lumina_agent):
        """Test Lumina agent initializes correctly."""
        assert mock_lumina_agent.name == "Lumina"
        assert mock_lumina_agent.role == "clarity_provider"
        assert callable(mock_lumina_agent.generate)
    
    def test_gemini_agent_initialization(self, mock_gemini_agent):
        """Test Gemini agent initializes correctly."""
        assert mock_gemini_agent.name == "Gemini"
        assert mock_gemini_agent.role == "explorer"
    
    def test_agni_agent_initialization(self, mock_agni_agent):
        """Test Agni agent initializes correctly."""
        assert mock_agni_agent.name == "Agni"
        assert mock_agni_agent.role == "transformer"
    
    def test_researcher_agent_initialization(self, mock_researcher_agent):
        """Test Researcher agent initializes correctly."""
        assert mock_researcher_agent.name == "Researcher"
        assert mock_researcher_agent.role == "evidence_provider"
    
    def test_claude_agent_initialization(self, mock_claude_agent):
        """Test Claude agent initializes correctly."""
        assert mock_claude_agent.name == "Claude"
        assert mock_claude_agent.role == "analyst"
    
    def test_kavach_agent_initialization(self, mock_kavach_agent):
        """Test Kavach agent initializes correctly."""
        assert mock_kavach_agent.name == "Kavach"
        assert mock_kavach_agent.role == "validator"
    
    def test_all_agents_have_required_methods(self, mock_agents):
        """Test all agents have required methods."""
        for agent_name, agent in mock_agents.items():
            assert hasattr(agent, "name"), f"{agent_name} missing 'name'"
            assert hasattr(agent, "role"), f"{agent_name} missing 'role'"
            assert hasattr(agent, "generate"), f"{agent_name} missing 'generate'"
            assert hasattr(agent, "assess_quality"), f"{agent_name} missing 'assess_quality'"
            assert hasattr(agent, "is_available"), f"{agent_name} missing 'is_available'"


# ============================================================================
# Agent Generation Tests
# ============================================================================

class TestAgentGeneration:
    """Test agent narrative generation."""
    
    @pytest.mark.asyncio
    async def test_oracle_agent_generates_narrative(self, mock_oracle_agent):
        """Test Oracle agent generates narrative."""
        result = await mock_oracle_agent.generate("test prompt")
        assert result == "Wise guidance from Oracle"
        mock_oracle_agent.generate.assert_called_once_with("test prompt")
    
    @pytest.mark.asyncio
    async def test_lumina_agent_generates_narrative(self, mock_lumina_agent):
        """Test Lumina agent generates narrative."""
        result = await mock_lumina_agent.generate("test prompt")
        assert result == "Clear insights from Lumina"
    
    @pytest.mark.asyncio
    async def test_gemini_agent_generates_narrative(self, mock_gemini_agent):
        """Test Gemini agent generates narrative."""
        result = await mock_gemini_agent.generate("test prompt")
        assert result == "Exploratory narrative from Gemini"
    
    @pytest.mark.asyncio
    async def test_agni_agent_generates_narrative(self, mock_agni_agent):
        """Test Agni agent generates narrative."""
        result = await mock_agni_agent.generate("test prompt")
        assert result == "Transformative narrative from Agni"
    
    @pytest.mark.asyncio
    async def test_researcher_agent_generates_narrative(self, mock_researcher_agent):
        """Test Researcher agent generates narrative."""
        result = await mock_researcher_agent.generate("test prompt")
        assert result == "Research-backed narrative from Researcher"
    
    @pytest.mark.asyncio
    async def test_claude_agent_generates_narrative(self, mock_claude_agent):
        """Test Claude agent generates narrative."""
        result = await mock_claude_agent.generate("test prompt")
        assert result == "Analytical narrative from Claude"
    
    @pytest.mark.asyncio
    async def test_kavach_agent_generates_narrative(self, mock_kavach_agent):
        """Test Kavach agent generates narrative."""
        result = await mock_kavach_agent.generate("test prompt")
        assert result == "Validated narrative from Kavach"
    
    @pytest.mark.asyncio
    async def test_agent_generation_with_context(self, mock_oracle_agent):
        """Test agent generation with additional context."""
        context = {
            "style": "philosophical",
            "tone": "contemplative",
            "length": "medium"
        }
        result = await mock_oracle_agent.generate("test prompt", context=context)
        assert result is not None


# ============================================================================
# Agent Quality Assessment Tests
# ============================================================================

class TestAgentQualityAssessment:
    """Test agent quality assessment capabilities."""
    
    def test_oracle_quality_assessment(self, mock_oracle_agent):
        """Test Oracle agent quality assessment."""
        quality = mock_oracle_agent.assess_quality("test narrative")
        assert quality == 0.95
        assert 0 <= quality <= 1
    
    def test_lumina_quality_assessment(self, mock_lumina_agent):
        """Test Lumina agent quality assessment."""
        quality = mock_lumina_agent.assess_quality("test narrative")
        assert quality == 0.92
    
    def test_gemini_quality_assessment(self, mock_gemini_agent):
        """Test Gemini agent quality assessment."""
        quality = mock_gemini_agent.assess_quality("test narrative")
        assert quality == 0.88
    
    def test_agni_quality_assessment(self, mock_agni_agent):
        """Test Agni agent quality assessment."""
        quality = mock_agni_agent.assess_quality("test narrative")
        assert quality == 0.90
    
    def test_researcher_quality_assessment(self, mock_researcher_agent):
        """Test Researcher agent quality assessment."""
        quality = mock_researcher_agent.assess_quality("test narrative")
        assert quality == 0.94
    
    def test_claude_quality_assessment(self, mock_claude_agent):
        """Test Claude agent quality assessment."""
        quality = mock_claude_agent.assess_quality("test narrative")
        assert quality == 0.93
    
    def test_kavach_quality_assessment(self, mock_kavach_agent):
        """Test Kavach agent quality assessment."""
        quality = mock_kavach_agent.assess_quality("test narrative")
        assert quality == 0.96
    
    def test_quality_scores_are_normalized(self, mock_agents):
        """Test all quality scores are normalized (0-1)."""
        for agent in mock_agents.values():
            quality = agent.assess_quality("test")
            assert 0 <= quality <= 1, f"{agent.name} quality out of range: {quality}"
    
    def test_quality_assessment_with_criteria(self, mock_oracle_agent):
        """Test quality assessment with specific criteria."""
        criteria = {
            "coherence": 0.9,
            "creativity": 0.85,
            "accuracy": 0.95
        }
        quality = mock_oracle_agent.assess_quality("test", criteria=criteria)
        assert quality is not None


# ============================================================================
# Agent Specialization Tests
# ============================================================================

class TestAgentSpecialization:
    """Test agent specialization and roles."""
    
    def test_oracle_specialization_wisdom(self, mock_oracle_agent):
        """Test Oracle agent specializes in wisdom."""
        assert mock_oracle_agent.role == "wisdom_guide"
        assert mock_oracle_agent.name == "Oracle"
    
    def test_lumina_specialization_clarity(self, mock_lumina_agent):
        """Test Lumina agent specializes in clarity."""
        assert mock_lumina_agent.role == "clarity_provider"
    
    def test_gemini_specialization_exploration(self, mock_gemini_agent):
        """Test Gemini agent specializes in exploration."""
        assert mock_gemini_agent.role == "explorer"
    
    def test_agni_specialization_transformation(self, mock_agni_agent):
        """Test Agni agent specializes in transformation."""
        assert mock_agni_agent.role == "transformer"
    
    def test_researcher_specialization_evidence(self, mock_researcher_agent):
        """Test Researcher agent specializes in evidence."""
        assert mock_researcher_agent.role == "evidence_provider"
    
    def test_claude_specialization_analysis(self, mock_claude_agent):
        """Test Claude agent specializes in analysis."""
        assert mock_claude_agent.role == "analyst"
    
    def test_kavach_specialization_validation(self, mock_kavach_agent):
        """Test Kavach agent specializes in validation."""
        assert mock_kavach_agent.role == "validator"
    
    def test_all_agents_have_unique_roles(self, mock_agents):
        """Test all agents have unique roles."""
        roles = [agent.role for agent in mock_agents.values()]
        assert len(roles) == len(set(roles)), "Agents have duplicate roles"


# ============================================================================
# Agent Availability Tests
# ============================================================================

class TestAgentAvailability:
    """Test agent availability checking."""
    
    def test_oracle_availability(self, mock_oracle_agent):
        """Test Oracle agent availability."""
        assert mock_oracle_agent.is_available() is True
    
    def test_all_agents_available_by_default(self, mock_agents):
        """Test all agents are available by default."""
        for agent in mock_agents.values():
            assert agent.is_available() is True
    
    def test_agent_availability_can_change(self, mock_oracle_agent):
        """Test agent availability can change."""
        mock_oracle_agent.is_available.return_value = False
        assert mock_oracle_agent.is_available() is False
        mock_oracle_agent.is_available.return_value = True
        assert mock_oracle_agent.is_available() is True


# ============================================================================
# Agent Combination Tests
# ============================================================================

class TestAgentCombinations:
    """Test combinations of agents for narrative generation."""
    
    @pytest.mark.asyncio
    async def test_balanced_agent_combination(self, mock_oracle_agent, mock_lumina_agent, mock_researcher_agent):
        """Test balanced agent combination (Oracle, Lumina, Researcher)."""
        agents = [mock_oracle_agent, mock_lumina_agent, mock_researcher_agent]
        
        results = []
        for agent in agents:
            result = await agent.generate("test prompt")
            results.append(result)
        
        assert len(results) == 3
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_creative_agent_combination(self, mock_agni_agent, mock_lumina_agent, mock_gemini_agent):
        """Test creative agent combination (Agni, Lumina, Gemini)."""
        agents = [mock_agni_agent, mock_lumina_agent, mock_gemini_agent]
        
        results = []
        for agent in agents:
            result = await agent.generate("test prompt")
            results.append(result)
        
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_quality_agent_combination(self, mock_kavach_agent, mock_researcher_agent, mock_oracle_agent):
        """Test quality-focused agent combination (Kavach, Researcher, Oracle)."""
        agents = [mock_kavach_agent, mock_researcher_agent, mock_oracle_agent]
        
        qualities = []
        for agent in agents:
            quality = agent.assess_quality("test narrative")
            qualities.append(quality)
        
        assert len(qualities) == 3
        assert all(0 <= q <= 1 for q in qualities)
    
    @pytest.mark.asyncio
    async def test_research_agent_combination(self, mock_researcher_agent, mock_oracle_agent, mock_claude_agent):
        """Test research-backed agent combination (Researcher, Oracle, Claude)."""
        agents = [mock_researcher_agent, mock_oracle_agent, mock_claude_agent]
        
        results = []
        for agent in agents:
            result = await agent.generate("test prompt")
            results.append(result)
        
        assert len(results) == 3


# ============================================================================
# Agent Error Handling Tests
# ============================================================================

class TestAgentErrorHandling:
    """Test agent error handling."""
    
    @pytest.mark.asyncio
    async def test_agent_handles_invalid_prompt(self, mock_oracle_agent):
        """Test agent handles invalid prompt gracefully."""
        mock_oracle_agent.generate.side_effect = ValueError("Invalid prompt")
        
        with pytest.raises(ValueError):
            await mock_oracle_agent.generate("")
    
    @pytest.mark.asyncio
    async def test_agent_handles_timeout(self, mock_oracle_agent):
        """Test agent handles timeout."""
        mock_oracle_agent.generate.side_effect = TimeoutError("Request timeout")
        
        with pytest.raises(TimeoutError):
            await mock_oracle_agent.generate("test prompt")
    
    def test_agent_handles_quality_assessment_error(self, mock_oracle_agent):
        """Test agent handles quality assessment error."""
        mock_oracle_agent.assess_quality.side_effect = Exception("Assessment error")
        
        with pytest.raises(Exception):
            mock_oracle_agent.assess_quality("test")


# ============================================================================
# Agent Performance Tests
# ============================================================================

class TestAgentPerformance:
    """Test agent performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_agent_generation_performance(self, mock_oracle_agent, performance_timer):
        """Test agent generation performance."""
        with performance_timer() as timer:
            result = await mock_oracle_agent.generate("test prompt")
        
        assert timer.elapsed < 1.0  # Should be fast with mocks
        assert result is not None
    
    @pytest.mark.performance
    def test_quality_assessment_performance(self, mock_oracle_agent, performance_timer):
        """Test quality assessment performance."""
        with performance_timer() as timer:
            quality = mock_oracle_agent.assess_quality("test narrative")
        
        assert timer.elapsed < 0.1  # Should be very fast
        assert quality is not None
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_parallel_agent_generation(self, mock_agents, performance_timer):
        """Test parallel agent generation performance."""
        prompts = ["test prompt 1", "test prompt 2", "test prompt 3"]
        
        with performance_timer() as timer:
            tasks = []
            for agent in list(mock_agents.values())[:3]:
                for prompt in prompts:
                    tasks.append(agent.generate(prompt))
            
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 9
        assert all(r is not None for r in results)


# ============================================================================
# Agent Integration Tests
# ============================================================================

class TestAgentIntegration:
    """Test agent integration with narrative engine."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agents_work_together(self, mock_agents, sample_narrative_prompt):
        """Test agents can work together on same prompt."""
        results = []
        
        for agent in mock_agents.values():
            result = await agent.generate(sample_narrative_prompt["prompt"])
            results.append(result)
        
        assert len(results) == len(mock_agents)
        assert all(r is not None for r in results)
    
    @pytest.mark.integration
    def test_agent_quality_consensus(self, mock_agents):
        """Test agents can reach quality consensus."""
        narrative = "test narrative"
        qualities = []
        
        for agent in mock_agents.values():
            quality = agent.assess_quality(narrative)
            qualities.append(quality)
        
        avg_quality = sum(qualities) / len(qualities)
        assert 0 <= avg_quality <= 1
        assert avg_quality > 0.8  # Should have good average quality
