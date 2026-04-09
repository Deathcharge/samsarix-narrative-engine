# Contributing to Helix Narrative Engine

Thank you for your interest in contributing to the Helix Narrative Engine! This document provides guidelines and instructions for contributing to the project.

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- pip or uv package manager

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Deathcharge/helix-narrative-engine.git
cd helix-narrative-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
pip install -r requirements-test.txt

# Verify installation
pytest --version
python -m helix_narrative_engine --help
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, readable code following PEP 8
- Add type hints to all functions
- Include comprehensive docstrings
- Write tests for new functionality
- Update documentation as needed

### 3. Run Tests and Linting

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/helix_narrative_engine

# Format code
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/

# Import sorting
isort src/ tests/
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new narrative generation feature

- Describe what was added
- Explain why it was added
- Reference any related issues (#123)"
```

**Commit Message Format**:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring
- `perf:` for performance improvements
- `chore:` for maintenance tasks

### 5. Push and Create Pull Request

```bash
# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
# - Provide clear description
# - Reference any related issues
# - Ensure all checks pass
```

---

## Code Style Guidelines

### Python Code Style

Follow PEP 8 with these specific guidelines:

```python
# Good: Clear, descriptive names
def generate_narrative_with_quality_check(
    prompt: str,
    style: str = "balanced",
    max_retries: int = 3
) -> dict[str, Any]:
    """Generate narrative with quality assessment.
    
    Args:
        prompt: The narrative prompt
        style: Generation style (balanced, creative, quality)
        max_retries: Maximum retry attempts
        
    Returns:
        Dictionary with narrative and metadata
        
    Raises:
        ValueError: If prompt is empty
        TimeoutError: If generation exceeds timeout
    """
    # Implementation
    pass

# Bad: Unclear names, no type hints
def gen_narr(p, s="b", r=3):
    # Implementation
    pass
```

### Type Hints

Always include type hints:

```python
from typing import Optional, Dict, List, Any

def process_narratives(
    narratives: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    """Process multiple narratives."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def generate_narrative(
    prompt: str,
    agent: str = "balanced"
) -> str:
    """Generate a narrative from a prompt.
    
    Uses the specified agent to generate creative content based on
    the provided prompt. Supports multiple generation styles and
    quality levels.
    
    Args:
        prompt: The narrative prompt (max 10,000 characters)
        agent: Agent to use (balanced, creative, quality, fast)
        
    Returns:
        Generated narrative text
        
    Raises:
        ValueError: If prompt is empty or exceeds max length
        TimeoutError: If generation exceeds timeout
        
    Example:
        >>> narrative = generate_narrative("Once upon a time...")
        >>> print(narrative)
    """
    pass
```

---

## Testing Guidelines

### Writing Tests

```python
import pytest
from helix_narrative_engine import NarrativeEngine

class TestNarrativeGeneration:
    """Tests for narrative generation."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return NarrativeEngine()
    
    def test_generate_basic_narrative(self, engine):
        """Test basic narrative generation."""
        prompt = "Once upon a time"
        result = engine.generate(prompt)
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_with_style(self, engine):
        """Test narrative generation with style."""
        prompt = "A mysterious forest"
        result = engine.generate(prompt, style="creative")
        
        assert result is not None
        assert len(result) > len(prompt)
    
    @pytest.mark.asyncio
    async def test_generate_async(self, engine):
        """Test async narrative generation."""
        prompt = "In a galaxy far away"
        result = await engine.generate_async(prompt)
        
        assert result is not None
```

### Test Coverage

- Aim for 80%+ code coverage
- Test both success and error paths
- Include edge cases
- Use fixtures for common setup

```bash
# Check coverage
pytest --cov=src/helix_narrative_engine --cov-report=html
```

---

## Documentation Guidelines

### Updating Documentation

1. **API Documentation**: Update `docs/API_REFERENCE.md` for API changes
2. **Getting Started**: Update `docs/GETTING_STARTED.md` for new features
3. **Examples**: Add examples to `examples/` directory
4. **Docstrings**: Include docstrings in all code

### Documentation Format

- Use Markdown for all documentation
- Include code examples where appropriate
- Keep language clear and concise
- Update table of contents for major changes

---

## Performance Considerations

### Optimization Guidelines

1. **Caching**: Use caching for repeated operations
2. **Async/Await**: Use async for I/O operations
3. **Batch Processing**: Support batch operations
4. **Memory**: Monitor memory usage for large operations

```python
# Good: Efficient caching
@cache.cached(ttl=3600)
def get_agent_config(agent_name: str) -> Dict:
    """Get cached agent configuration."""
    pass

# Good: Async operations
async def generate_batch(prompts: List[str]) -> List[str]:
    """Generate narratives concurrently."""
    tasks = [generate_narrative(p) for p in prompts]
    return await asyncio.gather(*tasks)
```

---

## Security Considerations

### API Key Management

- Never commit API keys
- Use environment variables
- Rotate keys regularly
- Use `.env` files (not in git)

### Input Validation

- Validate all user input
- Set reasonable limits (max length, max requests)
- Sanitize prompts before processing

```python
def validate_prompt(prompt: str, max_length: int = 10000) -> None:
    """Validate narrative prompt."""
    if not prompt:
        raise ValueError("Prompt cannot be empty")
    if len(prompt) > max_length:
        raise ValueError(f"Prompt exceeds max length: {max_length}")
```

---

## Submitting Changes

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

### Review Process

1. Submit pull request with clear description
2. Address review comments
3. Ensure all CI checks pass
4. Wait for approval from maintainers
5. Merge when approved

---

## Reporting Issues

### Bug Reports

Include the following information:

- Python version
- Package versions
- Minimal code to reproduce
- Expected behavior
- Actual behavior
- Error traceback (if applicable)

### Feature Requests

Describe:

- Use case and motivation
- Proposed solution
- Alternative approaches
- Potential impact

---

## Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and discuss ideas
- **Discord**: Join our community server (link in README)

---

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

## Recognition

Contributors will be recognized in:

- CHANGELOG.md
- GitHub contributors page
- Release notes

---

Thank you for contributing to the Helix Narrative Engine!

**Last Updated**: April 2026  
**Version**: 1.0.0
