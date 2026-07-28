"""Provider protocol and bounded optional SDK adapters."""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from typing import Any, Optional, Protocol, runtime_checkable

from .exceptions import ConfigurationError, ProviderError
from .models import Message, ProviderResponse, TokenUsage


@runtime_checkable
class Provider(Protocol):
    """Minimal provider contract required by :class:`NarrativeEngine`."""

    name: str

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        """Generate one bounded text response."""


def _required_key(explicit: Optional[str], environment_name: str) -> str:
    value = explicit if explicit is not None else os.getenv(environment_name)
    if value is None or not value.strip():
        raise ConfigurationError(f"set {environment_name} before using this provider")
    return value.strip()


def _safe_count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _validate_timeout(value: float) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value <= 0
        or value > 600
    ):
        raise ConfigurationError("timeout_seconds must be between 0 and 600")


class OpenAIProvider:
    """OpenAI Responses API adapter.

    The adapter disables response storage and automatic SDK retries, and never
    logs prompts, responses, or keys.
    """

    name = "openai"

    def __init__(
        self,
        *,
        model: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        timeout_seconds: float = 90.0,
        client: Optional[Any] = None,
    ) -> None:
        if not model.strip():
            raise ConfigurationError("OpenAI model cannot be empty")
        _validate_timeout(timeout_seconds)
        self.model = model.strip()
        if client is not None:
            self._client = client
            return

        key = _required_key(api_key, "OPENAI_API_KEY")
        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise ConfigurationError(
                "OpenAI support is optional; install with "
                'pip install "helix-narrative-engine[openai]"'
            ) from error
        self._client = AsyncOpenAI(
            api_key=key,
            timeout=timeout_seconds,
            max_retries=0,
        )

    def __repr__(self) -> str:
        return f"OpenAIProvider(model={self.model!r})"

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        try:
            response = await self._client.responses.create(
                model=self.model,
                input=[{"role": message.role, "content": message.content} for message in messages],
                max_output_tokens=max_output_tokens,
                store=False,
            )
        except Exception as error:
            raise ProviderError(self.name, type(error).__name__) from error

        usage = getattr(response, "usage", None)
        input_tokens = _safe_count(getattr(usage, "input_tokens", 0))
        output_tokens = _safe_count(getattr(usage, "output_tokens", 0))
        total_tokens = _safe_count(getattr(usage, "total_tokens", 0))
        return ProviderResponse(
            content=str(getattr(response, "output_text", "") or ""),
            provider=self.name,
            model=str(getattr(response, "model", self.model)),
            usage=TokenUsage(input_tokens, output_tokens, total_tokens),
        )


class AnthropicProvider:
    """Anthropic Messages API adapter with a timeout and no automatic retries."""

    name = "anthropic"

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-5",
        api_key: Optional[str] = None,
        timeout_seconds: float = 90.0,
        client: Optional[Any] = None,
    ) -> None:
        if not model.strip():
            raise ConfigurationError("Anthropic model cannot be empty")
        _validate_timeout(timeout_seconds)
        self.model = model.strip()
        if client is not None:
            self._client = client
            return

        key = _required_key(api_key, "ANTHROPIC_API_KEY")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as error:
            raise ConfigurationError(
                "Anthropic support is optional; install with "
                'pip install "helix-narrative-engine[anthropic]"'
            ) from error
        self._client = AsyncAnthropic(
            api_key=key,
            timeout=timeout_seconds,
            max_retries=0,
        )

    def __repr__(self) -> str:
        return f"AnthropicProvider(model={self.model!r})"

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        system = "\n\n".join(message.content for message in messages if message.role == "system")
        conversation = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role != "system"
        ]
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_output_tokens,
                system=system,
                messages=conversation,
            )
        except Exception as error:
            raise ProviderError(self.name, type(error).__name__) from error

        text_blocks = [
            str(getattr(block, "text", ""))
            for block in getattr(response, "content", ())
            if getattr(block, "type", None) == "text"
        ]
        usage = getattr(response, "usage", None)
        input_tokens = _safe_count(getattr(usage, "input_tokens", 0))
        output_tokens = _safe_count(getattr(usage, "output_tokens", 0))
        return ProviderResponse(
            content="".join(text_blocks),
            provider=self.name,
            model=str(getattr(response, "model", self.model)),
            usage=TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens),
        )


class OpenAICompatibleProvider:
    """Chat Completions adapter for explicitly configured compatible APIs."""

    def __init__(
        self,
        *,
        name: str,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 90.0,
        client: Optional[Any] = None,
    ) -> None:
        if not name.strip() or not model.strip() or not base_url.strip():
            raise ConfigurationError("compatible provider name, model, and base_url are required")
        if not api_key.strip() and client is None:
            raise ConfigurationError(f"set an API key before using {name}")
        _validate_timeout(timeout_seconds)
        self.name = name.strip()
        self.model = model.strip()
        if client is not None:
            self._client = client
            return

        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise ConfigurationError(
                'OpenAI-compatible support requires pip install "helix-narrative-engine[openai]"'
            ) from error
        self._client = AsyncOpenAI(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            timeout=timeout_seconds,
            max_retries=0,
        )

    def __repr__(self) -> str:
        return f"OpenAICompatibleProvider(name={self.name!r}, model={self.model!r})"

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        max_output_tokens: int,
    ) -> ProviderResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": message.role, "content": message.content} for message in messages
                ],
                max_tokens=max_output_tokens,
            )
        except Exception as error:
            raise ProviderError(self.name, type(error).__name__) from error

        choices = getattr(response, "choices", ())
        content = ""
        if choices:
            content = str(getattr(getattr(choices[0], "message", None), "content", "") or "")
        usage = getattr(response, "usage", None)
        input_tokens = _safe_count(getattr(usage, "prompt_tokens", 0))
        output_tokens = _safe_count(getattr(usage, "completion_tokens", 0))
        total_tokens = _safe_count(getattr(usage, "total_tokens", 0))
        return ProviderResponse(
            content=content,
            provider=self.name,
            model=str(getattr(response, "model", self.model)),
            usage=TokenUsage(input_tokens, output_tokens, total_tokens),
        )


def build_provider(
    name: str,
    *,
    model: Optional[str] = None,
    timeout_seconds: float = 90.0,
) -> Provider:
    """Build a supported provider exclusively from explicit names and environment keys."""

    normalized = name.strip().lower()
    selected_model = model or os.getenv("HELIX_MODEL")
    if normalized == "openai":
        return OpenAIProvider(
            model=selected_model or "gpt-5-mini",
            timeout_seconds=timeout_seconds,
        )
    if normalized == "anthropic":
        return AnthropicProvider(
            model=selected_model or "claude-sonnet-5",
            timeout_seconds=timeout_seconds,
        )
    if normalized == "xai":
        return OpenAICompatibleProvider(
            name="xai",
            model=selected_model or "grok-4.5",
            base_url="https://api.x.ai/v1",
            api_key=_required_key(None, "XAI_API_KEY"),
            timeout_seconds=timeout_seconds,
        )
    if normalized == "perplexity":
        key = os.getenv("PERPLEXITY_API_KEY") or os.getenv("SONAR_API_KEY")
        return OpenAICompatibleProvider(
            name="perplexity",
            model=selected_model or "sonar-pro",
            base_url="https://api.perplexity.ai",
            api_key=_required_key(key, "PERPLEXITY_API_KEY"),
            timeout_seconds=timeout_seconds,
        )
    raise ConfigurationError("unknown provider; choose openai, anthropic, xai, or perplexity")


def provider_from_env(*, timeout_seconds: float = 90.0) -> Provider:
    """Build a provider from ``HELIX_PROVIDER`` (defaults to ``openai``)."""

    return build_provider(
        os.getenv("HELIX_PROVIDER", "openai"),
        timeout_seconds=timeout_seconds,
    )
