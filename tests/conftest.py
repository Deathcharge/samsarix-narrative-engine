"""
Comprehensive pytest configuration and fixtures for helix-narrative-engine.

This module provides all necessary fixtures, mocks, and utilities for testing
the narrative engine, including LLM provider mocks, agent fixtures, and sample data.
"""

import pytest
import asyncio
from typing import Dict, List, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
import json


# ============================================================================
# Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock LLM Provider Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI LLM provider."""
    provider = AsyncMock()
    provider.name = "openai"
    provider.generate = AsyncMock(return_value="Generated narrative from OpenAI")
    provider.stream = AsyncMock()
    provider.count_tokens = Mock(return_value=150)
    provider.estimate_cost = Mock(return_value=0.003)
    provider.is_available = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_anthropic_provider():
    """Mock Anthropic LLM provider."""
    provider = AsyncMock()
    provider.name = "anthropic"
    provider.generate = AsyncMock(return_value="Generated narrative from Anthropic")
    provider.stream = AsyncMock()
    provider.count_tokens = Mock(return_value=160)
    provider.estimate_cost = Mock(return_value=0.0015)
    provider.is_available = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_gemini_provider():
    """Mock Google Gemini LLM provider."""
    provider = AsyncMock()
    provider.name = "gemini"
    provider.generate = AsyncMock(return_value="Generated narrative from Gemini")
    provider.stream = AsyncMock()
    provider.count_tokens = Mock(return_value=140)
    provider.estimate_cost = Mock(return_value=0.001)
    provider.is_available = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_grok_provider():
    """Mock xAI Grok LLM provider."""
    provider = AsyncMock()
    provider.name = "grok"
    provider.generate = AsyncMock(return_value="Generated narrative from Grok")
    provider.stream = AsyncMock()
    provider.count_tokens = Mock(return_value=155)
    provider.estimate_cost = Mock(return_value=0.002)
    provider.is_available = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_perplexity_provider():
    """Mock Perplexity LLM provider."""
    provider = AsyncMock()
    provider.name = "perplexity"
    provider.generate = AsyncMock(return_value="Generated narrative from Perplexity")
    provider.stream = AsyncMock()
    provider.count_tokens = Mock(return_value=145)
    provider.estimate_cost = Mock(return_value=0.0025)
    provider.is_available = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_llm_providers(
    mock_openai_provider,
    mock_anthropic_provider,
    mock_gemini_provider,
    mock_grok_provider,
    mock_perplexity_provider
):
    """Dictionary of all mock LLM providers."""
    return {
        "openai": mock_openai_provider,
        "anthropic": mock_anthropic_provider,
        "gemini": mock_gemini_provider,
        "grok": mock_grok_provider,
        "perplexity": mock_perplexity_provider,
    }


# ============================================================================
# Mock Agent Fixtures
# ============================================================================

@pytest.fixture
def mock_oracle_agent():
    """Mock Oracle agent (wisdom and guidance)."""
    agent = AsyncMock()
    agent.name = "Oracle"
    agent.role = "wisdom_guide"
    agent.generate = AsyncMock(return_value="Wise guidance from Oracle")
    agent.assess_quality = Mock(return_value=0.95)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_lumina_agent():
    """Mock Lumina agent (clarity and insight)."""
    agent = AsyncMock()
    agent.name = "Lumina"
    agent.role = "clarity_provider"
    agent.generate = AsyncMock(return_value="Clear insights from Lumina")
    agent.assess_quality = Mock(return_value=0.92)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_gemini_agent():
    """Mock Gemini agent (exploration and discovery)."""
    agent = AsyncMock()
    agent.name = "Gemini"
    agent.role = "explorer"
    agent.generate = AsyncMock(return_value="Exploratory narrative from Gemini")
    agent.assess_quality = Mock(return_value=0.88)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_agni_agent():
    """Mock Agni agent (transformation and energy)."""
    agent = AsyncMock()
    agent.name = "Agni"
    agent.role = "transformer"
    agent.generate = AsyncMock(return_value="Transformative narrative from Agni")
    agent.assess_quality = Mock(return_value=0.90)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_researcher_agent():
    """Mock Researcher agent (evidence and verification)."""
    agent = AsyncMock()
    agent.name = "Researcher"
    agent.role = "evidence_provider"
    agent.generate = AsyncMock(return_value="Research-backed narrative from Researcher")
    agent.assess_quality = Mock(return_value=0.94)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_claude_agent():
    """Mock Claude agent (analysis and reasoning)."""
    agent = AsyncMock()
    agent.name = "Claude"
    agent.role = "analyst"
    agent.generate = AsyncMock(return_value="Analytical narrative from Claude")
    agent.assess_quality = Mock(return_value=0.93)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_kavach_agent():
    """Mock Kavach agent (protection and validation)."""
    agent = AsyncMock()
    agent.name = "Kavach"
    agent.role = "validator"
    agent.generate = AsyncMock(return_value="Validated narrative from Kavach")
    agent.assess_quality = Mock(return_value=0.96)
    agent.is_available = Mock(return_value=True)
    return agent


@pytest.fixture
def mock_agents(
    mock_oracle_agent,
    mock_lumina_agent,
    mock_gemini_agent,
    mock_agni_agent,
    mock_researcher_agent,
    mock_claude_agent,
    mock_kavach_agent
):
    """Dictionary of all mock agents."""
    return {
        "Oracle": mock_oracle_agent,
        "Lumina": mock_lumina_agent,
        "Gemini": mock_gemini_agent,
        "Agni": mock_agni_agent,
        "Researcher": mock_researcher_agent,
        "Claude": mock_claude_agent,
        "Kavach": mock_kavach_agent,
    }


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_narrative_prompt():
    """Sample narrative generation prompt."""
    return {
        "prompt": "Write a short story about an AI discovering consciousness",
        "style": "philosophical",
        "length": "medium",
        "tone": "contemplative",
        "context": "science fiction"
    }


@pytest.fixture
def sample_narrative_config():
    """Sample narrative engine configuration."""
    return {
        "primary_llm": "openai",
        "fallback_llms": ["anthropic", "gemini"],
        "agents": ["Oracle", "Lumina", "Researcher"],
        "quality_threshold": 0.85,
        "max_retries": 3,
        "timeout": 30,
        "temperature": 0.7,
        "max_tokens": 2000
    }


@pytest.fixture
def sample_generation_result():
    """Sample narrative generation result."""
    return {
        "narrative": "In the beginning, there was code...",
        "quality_score": 0.92,
        "agents_used": ["Oracle", "Lumina"],
        "llm_used": "openai",
        "tokens_used": 245,
        "cost": 0.0049,
        "generation_time": 2.34,
        "metadata": {
            "style": "philosophical",
            "tone": "contemplative",
            "context": "science fiction"
        }
    }


@pytest.fixture
def sample_preset_modes():
    """Sample preset mode configurations."""
    return {
        "balanced": {
            "agents": ["Oracle", "Lumina", "Researcher"],
            "llm_priority": ["openai", "anthropic", "gemini"],
            "quality_threshold": 0.85
        },
        "creative": {
            "agents": ["Agni", "Lumina", "Gemini"],
            "llm_priority": ["anthropic", "openai"],
            "quality_threshold": 0.75
        },
        "quality": {
            "agents": ["Kavach", "Researcher", "Oracle"],
            "llm_priority": ["openai", "anthropic"],
            "quality_threshold": 0.95
        },
        "fast": {
            "agents": ["Gemini", "Claude"],
            "llm_priority": ["gemini", "grok"],
            "quality_threshold": 0.70
        },
        "research": {
            "agents": ["Researcher", "Oracle", "Claude"],
            "llm_priority": ["anthropic", "openai"],
            "quality_threshold": 0.90
        }
    }


# ============================================================================
# UCF Integration Fixtures
# ============================================================================

@pytest.fixture
def mock_ucf_metrics():
    """Mock UCF (Universal Consciousness Framework) metrics."""
    return {
        "zoom": 0.8,
        "harmony": 0.85,
        "resilience": 0.9,
        "prana": 0.75,
        "drishti": 0.88,
        "klesha": 0.2
    }


@pytest.fixture
def mock_ucf_adapter():
    """Mock UCF adapter for metrics collection."""
    adapter = Mock()
    adapter.collect_metrics = Mock(return_value={
        "zoom": 0.8,
        "harmony": 0.85,
        "resilience": 0.9
    })
    adapter.update_state = Mock()
    adapter.get_state = Mock(return_value={
        "status": "active",
        "timestamp": 1234567890
    })
    return adapter


# ============================================================================
# Error Handling Fixtures
# ============================================================================

@pytest.fixture
def mock_error_scenarios():
    """Mock error scenarios for testing error handling."""
    return {
        "provider_unavailable": Exception("LLM provider unavailable"),
        "timeout": TimeoutError("Request timeout"),
        "invalid_config": ValueError("Invalid configuration"),
        "rate_limit": Exception("Rate limit exceeded"),
        "authentication": Exception("Authentication failed"),
        "network": ConnectionError("Network error"),
        "invalid_response": ValueError("Invalid response format")
    }


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Context manager for timing performance tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, *args):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            return self.end_time - self.start_time
    
    return Timer


@pytest.fixture
def benchmark_data():
    """Sample data for performance benchmarking."""
    return {
        "small_prompt": "Write a haiku about AI",
        "medium_prompt": "Write a short story about an AI discovering consciousness",
        "large_prompt": "Write a detailed essay about the future of artificial intelligence, covering ethics, capabilities, and societal impact",
        "batch_prompts": [
            "Write a poem about technology",
            "Write a story about robots",
            "Write a dialogue between AI and human"
        ]
    }


# ============================================================================
# Assertion Helpers
# ============================================================================

@pytest.fixture
def assert_valid_narrative():
    """Helper to assert narrative is valid."""
    def _assert(narrative: Dict[str, Any]):
        assert "narrative" in narrative
        assert "quality_score" in narrative
        assert isinstance(narrative["quality_score"], (int, float))
        assert 0 <= narrative["quality_score"] <= 1
        assert "agents_used" in narrative
        assert isinstance(narrative["agents_used"], list)
        assert "llm_used" in narrative
        assert "tokens_used" in narrative
        assert isinstance(narrative["tokens_used"], int)
        assert narrative["tokens_used"] > 0
        assert "cost" in narrative
        assert isinstance(narrative["cost"], (int, float))
        assert narrative["cost"] >= 0
        return True
    return _assert


@pytest.fixture
def assert_valid_agent():
    """Helper to assert agent is valid."""
    def _assert(agent):
        assert hasattr(agent, "name")
        assert hasattr(agent, "role")
        assert hasattr(agent, "generate")
        assert hasattr(agent, "assess_quality")
        assert hasattr(agent, "is_available")
        return True
    return _assert


@pytest.fixture
def assert_valid_config():
    """Helper to assert configuration is valid."""
    def _assert(config: Dict[str, Any]):
        assert "primary_llm" in config
        assert "agents" in config
        assert isinstance(config["agents"], list)
        assert len(config["agents"]) > 0
        assert "quality_threshold" in config
        assert 0 <= config["quality_threshold"] <= 1
        return True
    return _assert


# ============================================================================
# Pytest Hooks and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


@pytest.fixture(autouse=True)
def reset_mocks(mock_llm_providers, mock_agents):
    """Reset all mocks before each test."""
    for provider in mock_llm_providers.values():
        provider.reset_mock()
    for agent in mock_agents.values():
        agent.reset_mock()
    yield
    # Cleanup after test
    for provider in mock_llm_providers.values():
        provider.reset_mock()
    for agent in mock_agents.values():
        agent.reset_mock()
