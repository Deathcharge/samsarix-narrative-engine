# Helix Narrative Engine

**Multi-LLM creative content generation with agent specialization**

A Python library for generating high-quality narrative content through coordinated multi-agent workflows. Perfect for creative AI applications, story generation, and content automation.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## Features

- **Multi-LLM Support**: Seamlessly switch between OpenAI, Anthropic, Google Gemini, xAI (Grok), and Perplexity
- **Specialized Agents**: 7 specialized agents for different creative roles (Oracle, Lumina, Gemini, Agni, Researcher, Claude, Kavach)
- **Preset Modes**: Pre-configured agent combinations for common use cases (Balanced, Creative, Quality, Fast, Research-Backed)
- **Automatic Fallback**: Intelligent fallback chain if primary LLM provider fails
- **Quality Assessment**: Built-in quality scoring and ethical compliance checking
- **UCF Integration**: Universal Coordination Field metrics for state tracking
- **Async/Await**: Full async support for non-blocking operations

---

## Installation

### From PyPI (Coming Soon)

```bash
pip install helix-narrative-engine
```

### From GitHub

```bash
git clone https://github.com/Deathcharge/helix-narrative-engine.git
cd helix-narrative-engine
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Basic Usage

```python
import asyncio
from helix_narrative_engine import generateNarrative, GenerationOptions

async def main():
    result = await generateNarrative(
        "A hacker discovers a conspiracy in a megacity",
        GenerationOptions(preset="balanced")
    )
    
    if result.success:
        print(f"Title: {result.title}")
        print(f"Content:\n{result.content}")
        print(f"Quality Score: {result.metadata.qualityScore}")
        print(f"Ethical Approval: {result.metadata.ethicalApproval}")
    else:
        print(f"Error: {result.error}")

asyncio.run(main())
```

### Custom Agent Configuration

```python
from helix_narrative_engine import generateNarrative, GenerationOptions

result = await generateNarrative(
    "A detective investigates a time-travel murder",
    GenerationOptions(
        customAgents=[
            {"agentId": "oracle", "provider": "openai", "temperature": 0.8},
            {"agentId": "lumina", "provider": "anthropic", "temperature": 0.75},
            {"agentId": "gemini", "provider": "google", "temperature": 0.7},
            {"agentId": "agni", "provider": "openai", "temperature": 0.9},
        ]
    )
)
```

### Using Different Presets

```python
# Fast generation with fewer agents
result = await generateNarrative(
    "A cyberpunk heist story",
    GenerationOptions(preset="fast")
)

# Quality-focused with assessment
result = await generateNarrative(
    "A philosophical exploration of consciousness",
    GenerationOptions(preset="quality")
)

# Research-backed with real-world grounding
result = await generateNarrative(
    "A near-future tech thriller",
    GenerationOptions(preset="research")
)
```

---

## Environment Variables

The library requires API keys for the LLM providers you want to use:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GEMINI_API_KEY="AIza..."

# xAI (Grok)
export XAI_API_KEY="xai-..."

# Perplexity
export SONAR_API_KEY="pplx-..."
```

---

## API Reference

### `generateNarrative(prompt, options)`

Main entry point for narrative generation.

**Parameters:**
- `prompt` (str): The creative prompt or story concept
- `options` (GenerationOptions, optional): Configuration options

**Returns:**
- `NarrativeGenerationResult`: Complete generation result with metadata

**Example:**
```python
result = await generateNarrative(
    "A mysterious signal from deep space",
    GenerationOptions(preset="creative")
)
```

---

## Agent Roles

### Oracle - Plot Architect
Crafts compelling plot structures with clear three-act progressions, meaningful character arcs, and satisfying resolutions.

### Lumina - Character Specialist
Develops rich, complex characters with believable motivations, fears, and desires. Creates emotional arcs that resonate.

### Gemini - World-Builder
Creates immersive, believable worlds with rich sensory details, consistent internal logic, and compelling systems.

### Agni - Creative Catalyst
Injects unexpected twists, novel combinations, and creative risks. Challenges conventions and pushes boundaries.

### Researcher - Fact-Checker
Verifies plausibility, finds real-world parallels, and provides credible references for authenticity.

### Claude - Quality Assessor
Evaluates stories on narrative coherence, character development, prose quality, pacing, and originality.

### Kavach - Ethical Guardian
Reviews stories for ethical compliance: nonmaleficence, autonomy, compassion, and humility.

---

## Preset Modes

### Balanced
All agents working together for comprehensive storytelling.
- Agents: Oracle, Lumina, Gemini, Agni, Researcher, Claude, Kavach

### Creative Focus
Emphasizes creativity and originality with less constraint.
- Agents: Oracle, Agni, Lumina, Gemini

### Quality First
Prioritizes quality assessment and ethical compliance.
- Agents: Oracle, Lumina, Gemini, Claude, Kavach

### Fast Generation
Minimal agents for quick story generation.
- Agents: Oracle, Lumina, Agni

### Research-Backed
Emphasizes research and plausibility.
- Agents: Oracle, Lumina, Gemini, Researcher, Claude

---

## Result Structure

```python
@dataclass
class NarrativeGenerationResult:
    success: bool                          # Whether generation succeeded
    generationId: str                      # Unique generation ID
    title: str                             # Generated story title
    content: str                           # Full story content
    metadata: GenerationMetadata           # Metadata about generation
    error: Optional[str]                   # Error message if failed

@dataclass
class GenerationMetadata:
    generationId: str                      # Unique generation ID
    title: str                             # Story title
    genre: str                             # Story genre
    wordCount: int                         # Word count
    qualityScore: float                    # Quality score (0.0-1.0)
    ethicalApproval: bool                  # Ethical compliance
    agentContributions: Dict               # Per-agent contributions
    ucfSnapshot: UCFSnapshot               # State metrics
```

---

## Integration with Helix Spirals

The Narrative Engine integrates seamlessly with [Helix Spirals](https://github.com/Deathcharge/helix-spirals) for workflow automation:

```python
from helix_narrative_engine import generateNarrative
from helix_spirals import createWorkflow

# Generate narrative
story = await generateNarrative("A cyberpunk heist")

# Automate distribution via Spirals
workflow = createWorkflow({
    "trigger": "manual",
    "steps": [
        {"type": "generate", "engine": "narrative", "prompt": story.title},
        {"type": "format", "target": "twitter"},
        {"type": "publish", "platform": "twitter"},
        {"type": "archive", "platform": "notion"},
    ]
})
```

---

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black helix_narrative_engine/ tests/

# Sort imports
isort helix_narrative_engine/ tests/

# Lint
flake8 helix_narrative_engine/ tests/

# Type checking
mypy helix_narrative_engine/
```

### Building Documentation

```bash
cd docs/
sphinx-build -b html . _build/
```

---

## Architecture

### Generation Pipeline

1. **Agent Setup** - Configure agents based on preset or custom config
2. **Oracle Phase** - Generate plot structure
3. **Lumina Phase** - Develop character arcs
4. **Gemini Phase** - Build world details
5. **Agni Phase** - Inject creative twists
6. **Researcher Phase** - Verify plausibility
7. **Synthesis** - Combine all elements into final narrative
8. **Assessment** - Quality scoring and ethical review

### Multi-LLM Routing

- Primary provider selection based on agent config
- Automatic fallback chain: OpenAI → Anthropic → Google → Perplexity → xAI
- Graceful degradation if providers fail

### State Tracking

UCF (Universal Coordination Field) metrics track:
- **Harmony**: Narrative coherence (0.0-1.0)
- **Prana**: Creative energy (0.0-1.0)
- **Drishti**: Focus/clarity (0.0-1.0)
- **Klesha**: Ethical concerns (0.0-1.0)
- **Resilience**: Robustness (0.5-2.0)
- **Zoom**: Scope/scale (0.5-2.0)

---

## Performance

- **Typical generation time**: 30-60 seconds (depends on LLM providers)
- **Token usage**: ~3,000-5,000 tokens per generation
- **Concurrent generations**: Limited by API rate limits

---

## Troubleshooting

### Missing API Keys
```
ValueError: OPENAI_API_KEY environment variable not set
```
Solution: Set the required API key in your environment variables.

### Provider Failures
```
RuntimeError: All LLM providers failed
```
Solution: Check your API keys and internet connection. Ensure at least one provider is configured.

### Timeout Issues
```
asyncio.TimeoutError
```
Solution: Increase timeout or use a faster preset (e.g., "fast" instead of "balanced").

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

## Citation

If you use Helix Narrative Engine in your research or project, please cite:

```bibtex
@software{helix_narrative_engine,
  author = {Helix Team},
  title = {Helix Narrative Engine: Multi-LLM Creative Content Generation},
  year = {2024},
  url = {https://github.com/Deathcharge/helix-narrative-engine}
}
```

---

## Roadmap

- [ ] Streaming support for real-time generation
- [ ] Custom agent templates
- [ ] Story continuation and series generation
- [ ] Multi-language support
- [ ] Web UI dashboard
- [ ] Integration with more LLM providers
- [ ] Advanced caching and optimization
- [ ] Batch generation API

---

## Support

- **Documentation**: [GitHub Wiki](https://github.com/Deathcharge/helix-narrative-engine/wiki)
- **Issues**: [GitHub Issues](https://github.com/Deathcharge/helix-narrative-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Deathcharge/helix-narrative-engine/discussions)

---

**Built with ❤️ by the Helix Team**
