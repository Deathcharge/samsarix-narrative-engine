# Helix Narrative Engine: API Reference

**Comprehensive API documentation for multi-LLM creative content generation**

---

## Table of Contents

1. [Core Engine](#core-engine)
2. [Agents](#agents)
3. [LLM Router](#llm-router)
4. [Configuration](#configuration)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

---

## Core Engine

### NarrativeEngine

The main orchestrator for narrative generation using coordinated multi-agent workflows.

#### Initialization

```python
from helix_narrative_engine import NarrativeEngine

engine = NarrativeEngine(
    primary_llm="openai",
    fallback_llms=["anthropic", "gemini"],
    agents=["Oracle", "Lumina", "Researcher"],
    quality_threshold=0.85,
    max_retries=3,
    timeout=30
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primary_llm` | str | "openai" | Primary LLM provider to use |
| `fallback_llms` | List[str] | ["anthropic"] | Fallback providers if primary fails |
| `agents` | List[str] | ["Oracle", "Lumina"] | Agents to use for generation |
| `quality_threshold` | float | 0.85 | Minimum quality score (0-1) |
| `max_retries` | int | 3 | Maximum retry attempts |
| `timeout` | int | 30 | Request timeout in seconds |
| `temperature` | float | 0.7 | LLM temperature (0-1) |
| `max_tokens` | int | 2000 | Maximum tokens in response |

#### Methods

##### generate()

Generate narrative content using configured agents and LLM providers.

```python
result = await engine.generate(
    prompt="Write a story about an AI discovering consciousness",
    style="philosophical",
    tone="contemplative",
    length="medium"
)
```

**Parameters:**
- `prompt` (str): The narrative generation prompt
- `style` (str, optional): Narrative style (philosophical, technical, creative, etc.)
- `tone` (str, optional): Tone of narrative (contemplative, energetic, somber, etc.)
- `length` (str, optional): Length (short, medium, long)
- `context` (Dict, optional): Additional context for generation

**Returns:**
```python
{
    "narrative": "Generated narrative text...",
    "quality_score": 0.92,
    "agents_used": ["Oracle", "Lumina"],
    "llm_used": "openai",
    "tokens_used": 245,
    "cost": 0.0049,
    "generation_time": 2.34,
    "metadata": {
        "style": "philosophical",
        "tone": "contemplative"
    }
}
```

##### generate_batch()

Generate multiple narratives in parallel.

```python
results = await engine.generate_batch(
    prompts=[
        "Write a poem about technology",
        "Write a story about robots",
        "Write a dialogue between AI and human"
    ],
    style="creative"
)
```

**Returns:** List of generation results

##### set_preset_mode()

Use pre-configured agent and LLM combinations.

```python
engine.set_preset_mode("balanced")  # Options: balanced, creative, quality, fast, research
```

**Available Modes:**

| Mode | Agents | LLM Priority | Quality Threshold |
|------|--------|--------------|-------------------|
| balanced | Oracle, Lumina, Researcher | openai, anthropic, gemini | 0.85 |
| creative | Agni, Lumina, Gemini | anthropic, openai | 0.75 |
| quality | Kavach, Researcher, Oracle | openai, anthropic | 0.95 |
| fast | Gemini, Claude | gemini, grok | 0.70 |
| research | Researcher, Oracle, Claude | anthropic, openai | 0.90 |

##### assess_quality()

Evaluate quality of generated narrative.

```python
quality_score = engine.assess_quality(
    narrative="Generated text...",
    criteria={
        "coherence": 0.9,
        "creativity": 0.85,
        "accuracy": 0.95
    }
)
```

**Returns:** Quality score (0-1)

---

## Agents

### Available Agents

The narrative engine includes 7 specialized agents, each with unique strengths:

#### Oracle

**Role:** Wisdom Guide  
**Specialization:** Philosophical insights, guidance, and wisdom  
**Quality Score:** 0.95

```python
from helix_narrative_engine.agents import Oracle

oracle = Oracle(llm_provider="openai")
narrative = await oracle.generate("Write about consciousness")
quality = oracle.assess_quality(narrative)
```

#### Lumina

**Role:** Clarity Provider  
**Specialization:** Clear, insightful narratives  
**Quality Score:** 0.92

```python
from helix_narrative_engine.agents import Lumina

lumina = Lumina(llm_provider="anthropic")
narrative = await lumina.generate("Explain AI ethics")
```

#### Gemini

**Role:** Explorer  
**Specialization:** Exploratory narratives, discovery  
**Quality Score:** 0.88

```python
from helix_narrative_engine.agents import Gemini

gemini = Gemini(llm_provider="gemini")
narrative = await gemini.generate("Explore future possibilities")
```

#### Agni

**Role:** Transformer  
**Specialization:** Transformative, energetic narratives  
**Quality Score:** 0.90

```python
from helix_narrative_engine.agents import Agni

agni = Agni(llm_provider="openai")
narrative = await agni.generate("Transform this concept")
```

#### Researcher

**Role:** Evidence Provider  
**Specialization:** Research-backed, factual narratives  
**Quality Score:** 0.94

```python
from helix_narrative_engine.agents import Researcher

researcher = Researcher(llm_provider="anthropic")
narrative = await researcher.generate("Research AI development")
```

#### Claude

**Role:** Analyst  
**Specialization:** Analytical, reasoned narratives  
**Quality Score:** 0.93

```python
from helix_narrative_engine.agents import Claude

claude = Claude(llm_provider="openai")
narrative = await claude.generate("Analyze this topic")
```

#### Kavach

**Role:** Validator  
**Specialization:** Validation, protection, quality assurance  
**Quality Score:** 0.96

```python
from helix_narrative_engine.agents import Kavach

kavach = Kavach(llm_provider="anthropic")
narrative = await kavach.generate("Validate this narrative")
quality = kavach.assess_quality(narrative)
```

### Agent Methods

#### generate()

Generate narrative content.

```python
narrative = await agent.generate(
    prompt="Your prompt here",
    context={
        "style": "philosophical",
        "tone": "contemplative"
    }
)
```

#### assess_quality()

Assess narrative quality.

```python
quality = agent.assess_quality(
    narrative="Generated text",
    criteria={
        "coherence": 0.9,
        "creativity": 0.85
    }
)
```

#### is_available()

Check if agent is available.

```python
if agent.is_available():
    narrative = await agent.generate(prompt)
```

---

## LLM Router

### LLMRouter

Manages multi-provider LLM routing with automatic fallback.

#### Initialization

```python
from helix_narrative_engine.llm_router import LLMRouter

router = LLMRouter(
    primary="openai",
    fallback=["anthropic", "gemini", "grok", "perplexity"],
    timeout=30
)
```

#### Methods

##### route()

Route request to appropriate LLM provider.

```python
response = await router.route(
    prompt="Generate narrative",
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000
)
```

**Returns:** LLM response string

##### estimate_cost()

Estimate cost for request.

```python
cost = router.estimate_cost(
    provider="openai",
    tokens=245
)
```

**Returns:** Estimated cost in USD

##### count_tokens()

Count tokens in text.

```python
tokens = router.count_tokens(
    text="Your text here",
    provider="openai"
)
```

**Returns:** Token count (int)

##### get_available_providers()

Get list of available providers.

```python
providers = router.get_available_providers()
# Returns: ["openai", "anthropic", "gemini", ...]
```

---

## Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus

# Google Gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-pro

# xAI Grok
GROK_API_KEY=...
GROK_MODEL=grok-1

# Perplexity
PERPLEXITY_API_KEY=...
PERPLEXITY_MODEL=pplx-7b-online
```

### Configuration File

```python
from helix_narrative_engine import NarrativeEngine

config = {
    "primary_llm": "openai",
    "fallback_llms": ["anthropic", "gemini"],
    "agents": ["Oracle", "Lumina", "Researcher"],
    "quality_threshold": 0.85,
    "max_retries": 3,
    "timeout": 30,
    "temperature": 0.7,
    "max_tokens": 2000,
    "batch_size": 5,
    "cache_enabled": True,
    "cache_ttl": 3600
}

engine = NarrativeEngine(**config)
```

---

## Error Handling

### Exception Types

#### NarrativeEngineError

Base exception for all narrative engine errors.

```python
from helix_narrative_engine.exceptions import NarrativeEngineError

try:
    result = await engine.generate(prompt)
except NarrativeEngineError as e:
    print(f"Error: {e}")
```

#### LLMProviderError

LLM provider-specific errors.

```python
from helix_narrative_engine.exceptions import LLMProviderError

try:
    result = await engine.generate(prompt)
except LLMProviderError as e:
    print(f"Provider error: {e.provider}")
    print(f"Retrying with fallback...")
```

#### QualityAssessmentError

Quality assessment failures.

```python
from helix_narrative_engine.exceptions import QualityAssessmentError

try:
    quality = engine.assess_quality(narrative)
except QualityAssessmentError as e:
    print(f"Quality assessment failed: {e}")
```

#### ConfigurationError

Configuration validation errors.

```python
from helix_narrative_engine.exceptions import ConfigurationError

try:
    engine = NarrativeEngine(invalid_config)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### Error Recovery

```python
from helix_narrative_engine.exceptions import NarrativeEngineError

async def generate_with_recovery(engine, prompt, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            result = await engine.generate(prompt)
            return result
        except NarrativeEngineError as e:
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## Examples

### Example 1: Basic Narrative Generation

```python
import asyncio
from helix_narrative_engine import NarrativeEngine

async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write a short story about an AI discovering consciousness",
        style="philosophical",
        tone="contemplative"
    )
    
    print(f"Narrative: {result['narrative']}")
    print(f"Quality: {result['quality_score']}")
    print(f"Cost: ${result['cost']:.4f}")

asyncio.run(main())
```

### Example 2: Using Preset Modes

```python
async def main():
    engine = NarrativeEngine()
    
    # Use creative preset
    engine.set_preset_mode("creative")
    result = await engine.generate(
        prompt="Create an imaginative story"
    )
    
    # Use quality preset
    engine.set_preset_mode("quality")
    result = await engine.generate(
        prompt="Write a well-researched article"
    )

asyncio.run(main())
```

### Example 3: Batch Processing

```python
async def main():
    engine = NarrativeEngine()
    
    prompts = [
        "Write a poem about technology",
        "Write a story about robots",
        "Write a dialogue between AI and human"
    ]
    
    results = await engine.generate_batch(prompts)
    
    for i, result in enumerate(results):
        print(f"Result {i+1}: {result['narrative'][:100]}...")

asyncio.run(main())
```

### Example 4: Quality Assessment

```python
async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write about consciousness"
    )
    
    quality = engine.assess_quality(
        narrative=result['narrative'],
        criteria={
            "coherence": 0.9,
            "creativity": 0.85,
            "accuracy": 0.95
        }
    )
    
    print(f"Quality Score: {quality}")

asyncio.run(main())
```

### Example 5: Custom Agent Selection

```python
async def main():
    engine = NarrativeEngine(
        agents=["Researcher", "Oracle", "Claude"]
    )
    
    result = await engine.generate(
        prompt="Write a research-backed article about AI ethics"
    )
    
    print(f"Agents used: {result['agents_used']}")

asyncio.run(main())
```

---

## Best Practices

### 1. Error Handling

Always wrap generation calls in try-except blocks:

```python
try:
    result = await engine.generate(prompt)
except LLMProviderError:
    # Handle provider errors
    pass
except QualityAssessmentError:
    # Handle quality errors
    pass
```

### 2. Cost Management

Monitor costs and set appropriate limits:

```python
engine = NarrativeEngine(
    max_tokens=1000,  # Limit token usage
    quality_threshold=0.8  # Accept lower quality for cost savings
)
```

### 3. Performance Optimization

Use batch processing for multiple prompts:

```python
# Good: Batch processing
results = await engine.generate_batch(prompts)

# Avoid: Sequential processing
results = [await engine.generate(p) for p in prompts]
```

### 4. Quality Assurance

Always assess quality for production use:

```python
result = await engine.generate(prompt)
if result['quality_score'] < 0.85:
    # Regenerate or handle low quality
    pass
```

### 5. Caching

Enable caching for repeated prompts:

```python
engine = NarrativeEngine(
    cache_enabled=True,
    cache_ttl=3600  # 1 hour
)
```

### 6. Monitoring

Track metrics for optimization:

```python
result = await engine.generate(prompt)
print(f"Tokens: {result['tokens_used']}")
print(f"Cost: ${result['cost']:.4f}")
print(f"Time: {result['generation_time']:.2f}s")
```

---

## References

- [Helix Narrative Engine GitHub](https://github.com/Deathcharge/helix-narrative-engine)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude Documentation](https://docs.anthropic.com)
- [Google Gemini Documentation](https://ai.google.dev)
- [Universal Consciousness Framework](https://github.com/Deathcharge/ucf-protocol)

---

**Last Updated**: April 2026  
**Version**: 1.0.0  
**Author**: Manus AI
