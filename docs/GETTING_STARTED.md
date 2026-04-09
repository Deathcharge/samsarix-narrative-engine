# Helix Narrative Engine: Getting Started Guide

**Get up and running with multi-LLM creative content generation in minutes**

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Installation

### Prerequisites

- Python 3.8+
- pip or poetry
- API keys for at least one LLM provider

### From PyPI (Recommended)

```bash
pip install helix-narrative-engine
```

### From Source

```bash
git clone https://github.com/Deathcharge/helix-narrative-engine.git
cd helix-narrative-engine
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/Deathcharge/helix-narrative-engine.git
cd helix-narrative-engine
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Set Up API Keys

Create a `.env` file in your project directory:

```bash
# OpenAI (Recommended for best results)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic (Excellent alternative)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus

# Google Gemini (Cost-effective option)
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-pro

# xAI Grok (Fast option)
GROK_API_KEY=...
GROK_MODEL=grok-1

# Perplexity (Research-focused)
PERPLEXITY_API_KEY=...
PERPLEXITY_MODEL=pplx-7b-online
```

### 2. Create Your First Script

```python
import asyncio
from helix_narrative_engine import NarrativeEngine

async def main():
    # Initialize the engine
    engine = NarrativeEngine()
    
    # Generate a narrative
    result = await engine.generate(
        prompt="Write a short story about an AI discovering consciousness",
        style="philosophical",
        tone="contemplative"
    )
    
    # Print results
    print("Generated Narrative:")
    print(result['narrative'])
    print(f"\nQuality Score: {result['quality_score']}")
    print(f"Cost: ${result['cost']:.4f}")

# Run the script
asyncio.run(main())
```

### 3. Run Your Script

```bash
python your_script.py
```

---

## Configuration

### Basic Configuration

```python
from helix_narrative_engine import NarrativeEngine

engine = NarrativeEngine(
    primary_llm="openai",           # Primary LLM provider
    fallback_llms=["anthropic"],    # Fallback providers
    agents=["Oracle", "Lumina"],    # Agents to use
    quality_threshold=0.85,         # Minimum quality score
    max_retries=3,                  # Retry attempts
    timeout=30                      # Request timeout
)
```

### Advanced Configuration

```python
config = {
    # LLM Configuration
    "primary_llm": "openai",
    "fallback_llms": ["anthropic", "gemini"],
    
    # Agent Configuration
    "agents": ["Oracle", "Lumina", "Researcher"],
    
    # Quality Settings
    "quality_threshold": 0.85,
    "max_retries": 3,
    "timeout": 30,
    
    # Generation Settings
    "temperature": 0.7,
    "max_tokens": 2000,
    
    # Performance Settings
    "batch_size": 5,
    "cache_enabled": True,
    "cache_ttl": 3600,
    
    # Monitoring
    "enable_metrics": True,
    "log_level": "INFO"
}

engine = NarrativeEngine(**config)
```

### Using Configuration Files

```python
import json
from helix_narrative_engine import NarrativeEngine

# Load configuration from file
with open("config.json") as f:
    config = json.load(f)

engine = NarrativeEngine(**config)
```

---

## Basic Usage

### 1. Simple Text Generation

```python
import asyncio
from helix_narrative_engine import NarrativeEngine

async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write a haiku about technology"
    )
    
    print(result['narrative'])

asyncio.run(main())
```

### 2. Styled Generation

```python
async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write about the future of AI",
        style="technical",
        tone="optimistic",
        length="medium"
    )
    
    print(result['narrative'])

asyncio.run(main())
```

### 3. Using Preset Modes

```python
async def main():
    engine = NarrativeEngine()
    
    # Balanced mode: Good quality, reasonable cost
    engine.set_preset_mode("balanced")
    result = await engine.generate("Write a story")
    
    # Creative mode: Emphasis on creativity
    engine.set_preset_mode("creative")
    result = await engine.generate("Write a poem")
    
    # Quality mode: Highest quality
    engine.set_preset_mode("quality")
    result = await engine.generate("Write an article")
    
    # Fast mode: Quick generation
    engine.set_preset_mode("fast")
    result = await engine.generate("Write a summary")
    
    # Research mode: Evidence-backed
    engine.set_preset_mode("research")
    result = await engine.generate("Research AI ethics")

asyncio.run(main())
```

### 4. Batch Processing

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
        print(f"\n--- Result {i+1} ---")
        print(result['narrative'])

asyncio.run(main())
```

### 5. Quality Assessment

```python
async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write about consciousness"
    )
    
    # Check quality score
    if result['quality_score'] >= 0.85:
        print("High quality narrative generated!")
    else:
        print("Regenerating for better quality...")
        result = await engine.generate(
            prompt="Write about consciousness",
            quality_threshold=0.95
        )

asyncio.run(main())
```

---

## Advanced Usage

### 1. Custom Agent Selection

```python
async def main():
    # Use specific agents for specific tasks
    engine = NarrativeEngine(
        agents=["Researcher", "Oracle", "Claude"]
    )
    
    result = await engine.generate(
        prompt="Write a research-backed article about AI ethics"
    )
    
    print(f"Agents used: {result['agents_used']}")

asyncio.run(main())
```

### 2. Error Handling and Recovery

```python
from helix_narrative_engine.exceptions import (
    NarrativeEngineError,
    LLMProviderError,
    QualityAssessmentError
)

async def main():
    engine = NarrativeEngine()
    
    try:
        result = await engine.generate(
            prompt="Write about consciousness"
        )
    except LLMProviderError as e:
        print(f"LLM provider error: {e}")
        print("Retrying with fallback provider...")
    except QualityAssessmentError as e:
        print(f"Quality assessment failed: {e}")
    except NarrativeEngineError as e:
        print(f"Narrative engine error: {e}")

asyncio.run(main())
```

### 3. Cost Optimization

```python
async def main():
    # Use fast mode for cost-sensitive applications
    engine = NarrativeEngine()
    engine.set_preset_mode("fast")
    
    result = await engine.generate(
        prompt="Generate a summary"
    )
    
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Tokens used: {result['tokens_used']}")

asyncio.run(main())
```

### 4. Performance Monitoring

```python
async def main():
    engine = NarrativeEngine()
    
    result = await engine.generate(
        prompt="Write a detailed article"
    )
    
    # Monitor performance metrics
    print(f"Generation time: {result['generation_time']:.2f}s")
    print(f"Tokens used: {result['tokens_used']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Quality score: {result['quality_score']}")
    print(f"LLM used: {result['llm_used']}")

asyncio.run(main())
```

### 5. Streaming Generation

```python
async def main():
    engine = NarrativeEngine()
    
    # Stream narrative generation
    async for chunk in engine.stream_generate(
        prompt="Write a long story"
    ):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

---

## Troubleshooting

### Issue: API Key Not Found

**Error:** `KeyError: 'OPENAI_API_KEY'`

**Solution:** Ensure your `.env` file is in the correct location and contains the API key:

```bash
# Check if .env file exists
ls -la .env

# Verify API key is set
echo $OPENAI_API_KEY
```

### Issue: Quality Score Too Low

**Error:** `QualityAssessmentError: Quality score below threshold`

**Solution:** Adjust quality threshold or use a different preset mode:

```python
# Lower quality threshold
engine = NarrativeEngine(quality_threshold=0.75)

# Or use a different preset
engine.set_preset_mode("balanced")
```

### Issue: Request Timeout

**Error:** `TimeoutError: Request timeout`

**Solution:** Increase timeout or use a faster LLM:

```python
# Increase timeout
engine = NarrativeEngine(timeout=60)

# Or use fast mode
engine.set_preset_mode("fast")
```

### Issue: Rate Limiting

**Error:** `LLMProviderError: Rate limit exceeded`

**Solution:** Implement exponential backoff:

```python
import asyncio

async def generate_with_backoff(engine, prompt, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await engine.generate(prompt)
        except LLMProviderError:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
```

### Issue: High Costs

**Error:** Unexpected high costs from API usage

**Solution:** Monitor and optimize token usage:

```python
# Use smaller max_tokens
engine = NarrativeEngine(max_tokens=1000)

# Use fast mode
engine.set_preset_mode("fast")

# Monitor costs
result = await engine.generate(prompt)
print(f"Cost: ${result['cost']:.4f}")
```

---

## Next Steps

### 1. Explore Advanced Features

- Read the [API Reference](API_REFERENCE.md)
- Check out [Best Practices](BEST_PRACTICES.md)
- Review [Architecture Guide](ARCHITECTURE.md)

### 2. Integrate with Your Application

```python
# Example: Flask integration
from flask import Flask, request
from helix_narrative_engine import NarrativeEngine

app = Flask(__name__)
engine = NarrativeEngine()

@app.route('/generate', methods=['POST'])
async def generate():
    data = request.json
    result = await engine.generate(data['prompt'])
    return result
```

### 3. Set Up Monitoring

```python
# Enable metrics collection
engine = NarrativeEngine(enable_metrics=True)

# Monitor performance
result = await engine.generate(prompt)
print(f"Generation time: {result['generation_time']:.2f}s")
print(f"Cost: ${result['cost']:.4f}")
```

### 4. Run Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=helix_narrative_engine tests/
```

### 5. Join the Community

- [GitHub Discussions](https://github.com/Deathcharge/helix-narrative-engine/discussions)
- [Report Issues](https://github.com/Deathcharge/helix-narrative-engine/issues)
- [Contributing Guide](../CONTRIBUTING.md)

---

## Resources

- **GitHub Repository**: https://github.com/Deathcharge/helix-narrative-engine
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Best Practices**: [BEST_PRACTICES.md](BEST_PRACTICES.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Last Updated**: April 2026  
**Version**: 1.0.0  
**Author**: Manus AI
