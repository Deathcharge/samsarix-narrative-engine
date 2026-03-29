"""
Multi-LLM Router

Supports OpenAI, Anthropic, xAI (Grok), Google (Gemini), and Perplexity
"""

from typing import Literal, TypedDict, Optional, List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai", "anthropic", "xai", "google", "perplexity"]


class LLMMessage(TypedDict):
    """LLM message format"""
    role: Literal["system", "user", "assistant"]
    content: str


class LLMResponse(TypedDict):
    """LLM response format"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, int]]


DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus-20240229",
    "xai": "grok-2",
    "google": "gemini-2.0-flash",
    "perplexity": "sonar-pro",
}


async def callLLM(
    provider: LLMProvider,
    messages: List[LLMMessage],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    stream: bool = False,
) -> LLMResponse:
    """
    Call an LLM provider with the given messages.
    
    Args:
        provider: The LLM provider to use
        messages: List of messages in conversation
        temperature: Sampling temperature (0.0 - 1.0)
        max_tokens: Maximum tokens in response
        stream: Whether to stream the response
        
    Returns:
        LLM response with content and metadata
    """
    if provider == "openai":
        return await _callOpenAI(messages, temperature, max_tokens)
    elif provider == "anthropic":
        return await _callAnthropic(messages, temperature, max_tokens)
    elif provider == "xai":
        return await _callXAI(messages, temperature, max_tokens)
    elif provider == "google":
        return await _callGoogle(messages, temperature, max_tokens)
    elif provider == "perplexity":
        return await _callPerplexity(messages, temperature, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def callLLMWithFallback(
    messages: List[LLMMessage],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    log_errors: bool = False,
) -> LLMResponse:
    """
    Call LLM with automatic fallback chain.
    
    Tries providers in order: openai → anthropic → google → perplexity → xai
    
    Args:
        messages: List of messages in conversation
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        log_errors: Whether to log errors
        
    Returns:
        LLM response from first successful provider
    """
    providers: List[LLMProvider] = ["openai", "anthropic", "google", "perplexity", "xai"]
    
    for provider in providers:
        try:
            logger.info(f"[LLM Router] Trying {provider}...")
            response = await callLLM(provider, messages, temperature, max_tokens)
            logger.info(f"[LLM Router] {provider} succeeded")
            return response
        except Exception as e:
            if log_errors:
                logger.warning(f"[LLM Router] {provider} failed: {e}")
            continue
    
    raise RuntimeError("All LLM providers failed")


async def _callOpenAI(
    messages: List[LLMMessage],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call OpenAI API"""
    try:
        import openai
    except ImportError:
        raise ImportError("openai package required: pip install openai")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    response = await client.chat.completions.create(
        model=DEFAULT_MODELS["openai"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return {
        "content": response.choices[0].message.content or "",
        "provider": "openai",
        "model": response.model,
        "usage": {
            "promptTokens": response.usage.prompt_tokens,
            "completionTokens": response.usage.completion_tokens,
            "totalTokens": response.usage.total_tokens,
        } if response.usage else None,
    }


async def _callAnthropic(
    messages: List[LLMMessage],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call Anthropic API"""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package required: pip install anthropic")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    response = await client.messages.create(
        model=DEFAULT_MODELS["anthropic"],
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    
    return {
        "content": response.content[0].text if response.content else "",
        "provider": "anthropic",
        "model": response.model,
        "usage": {
            "promptTokens": response.usage.input_tokens,
            "completionTokens": response.usage.output_tokens,
            "totalTokens": response.usage.input_tokens + response.usage.output_tokens,
        } if response.usage else None,
    }


async def _callXAI(
    messages: List[LLMMessage],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call xAI (Grok) API"""
    try:
        from xai_sdk import Client
    except ImportError:
        raise ImportError("xai-sdk package required: pip install xai-sdk")
    
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable not set")
    
    client = Client(api_key=api_key)
    
    response = await client.chat.create(
        model=DEFAULT_MODELS["xai"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return {
        "content": response.choices[0].message.content or "",
        "provider": "xai",
        "model": response.model,
        "usage": None,
    }


async def _callGoogle(
    messages: List[LLMMessage],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call Google Gemini API"""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("google-generativeai package required: pip install google-generativeai")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(DEFAULT_MODELS["google"])
    
    response = await model.generate_content_async(
        contents=messages,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    
    return {
        "content": response.text or "",
        "provider": "google",
        "model": DEFAULT_MODELS["google"],
        "usage": None,
    }


async def _callPerplexity(
    messages: List[LLMMessage],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call Perplexity API"""
    try:
        import openai
    except ImportError:
        raise ImportError("openai package required: pip install openai")
    
    api_key = os.getenv("SONAR_API_KEY")
    if not api_key:
        raise ValueError("SONAR_API_KEY environment variable not set")
    
    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai",
    )
    
    response = await client.chat.completions.create(
        model=DEFAULT_MODELS["perplexity"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return {
        "content": response.choices[0].message.content or "",
        "provider": "perplexity",
        "model": response.model,
        "usage": {
            "promptTokens": response.usage.prompt_tokens,
            "completionTokens": response.usage.completion_tokens,
            "totalTokens": response.usage.total_tokens,
        } if response.usage else None,
    }
