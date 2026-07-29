# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Provider adapter contract and secret-safety tests."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from samsarix_narrative_engine import (
    AnthropicProvider,
    ConfigurationError,
    Message,
    OpenAICompatibleProvider,
    OpenAIProvider,
    ProviderError,
    build_provider,
    provider_from_env,
)


class RecordingMethod:
    def __init__(self, response: Any = None, error: Optional[Exception] = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


async def test_openai_responses_adapter_disables_storage_and_normalizes_usage() -> None:
    method = RecordingMethod(
        SimpleNamespace(
            output_text="story",
            model="gpt-test",
            usage=SimpleNamespace(input_tokens=12, output_tokens=8, total_tokens=20),
        )
    )
    provider = OpenAIProvider(model="gpt-test", client=SimpleNamespace(responses=method))
    response = await provider.complete(
        (Message("system", "instructions"), Message("user", "brief")),
        max_output_tokens=50,
    )

    assert response.content == "story"
    assert response.usage.total_tokens == 20
    assert method.kwargs["store"] is False
    assert method.kwargs["max_output_tokens"] == 50
    assert "api" not in repr(provider).lower()


async def test_openai_adapter_sanitizes_sdk_error() -> None:
    method = RecordingMethod(error=RuntimeError("api-key-secret"))
    provider = OpenAIProvider(client=SimpleNamespace(responses=method))
    with pytest.raises(ProviderError) as caught:
        await provider.complete((Message("user", "private"),), max_output_tokens=10)
    assert "api-key-secret" not in str(caught.value)
    assert caught.value.__cause__ is not None


async def test_anthropic_adapter_separates_system_and_text_blocks() -> None:
    method = RecordingMethod(
        SimpleNamespace(
            content=(
                SimpleNamespace(type="text", text="first"),
                SimpleNamespace(type="tool_use", text="ignored"),
                SimpleNamespace(type="text", text=" second"),
            ),
            model="claude-test",
            usage=SimpleNamespace(input_tokens=7, output_tokens=3),
        )
    )
    provider = AnthropicProvider(model="claude-test", client=SimpleNamespace(messages=method))
    response = await provider.complete(
        (Message("system", "rules"), Message("user", "brief")),
        max_output_tokens=25,
    )

    assert response.content == "first second"
    assert response.usage.total_tokens == 10
    assert method.kwargs["system"] == "rules"
    assert method.kwargs["messages"] == [{"role": "user", "content": "brief"}]
    assert "api" not in repr(provider).lower()


async def test_anthropic_adapter_sanitizes_sdk_error() -> None:
    method = RecordingMethod(error=RuntimeError("private-content"))
    provider = AnthropicProvider(client=SimpleNamespace(messages=method))
    with pytest.raises(ProviderError) as caught:
        await provider.complete((Message("user", "private"),), max_output_tokens=10)
    assert "private-content" not in str(caught.value)


async def test_openai_compatible_adapter_normalizes_chat_completion() -> None:
    method = RecordingMethod(
        SimpleNamespace(
            choices=(SimpleNamespace(message=SimpleNamespace(content="result")),),
            model="compatible-test",
            usage=SimpleNamespace(prompt_tokens=4, completion_tokens=6, total_tokens=10),
        )
    )
    provider = OpenAICompatibleProvider(
        name="local",
        model="compatible-test",
        base_url="https://example.invalid/v1",
        api_key="unused-with-injected-client",
        client=SimpleNamespace(chat=SimpleNamespace(completions=method)),
    )
    response = await provider.complete((Message("user", "brief"),), max_output_tokens=20)
    assert response.content == "result"
    assert response.usage.total_tokens == 10
    assert method.kwargs["max_tokens"] == 20
    assert "unused" not in repr(provider)


async def test_openai_compatible_empty_choices_and_error_paths() -> None:
    empty = RecordingMethod(SimpleNamespace(choices=(), model="m", usage=None))
    provider = OpenAICompatibleProvider(
        name="local",
        model="m",
        base_url="https://example.invalid/v1",
        api_key="key",
        client=SimpleNamespace(chat=SimpleNamespace(completions=empty)),
    )
    assert (await provider.complete((Message("user", "x"),), max_output_tokens=1)).content == ""

    failed = RecordingMethod(error=RuntimeError("credential"))
    provider = OpenAICompatibleProvider(
        name="local",
        model="m",
        base_url="https://example.invalid/v1",
        api_key="key",
        client=SimpleNamespace(chat=SimpleNamespace(completions=failed)),
    )
    with pytest.raises(ProviderError) as caught:
        await provider.complete((Message("user", "x"),), max_output_tokens=1)
    assert "credential" not in str(caught.value)


@pytest.mark.parametrize(
    ("constructor", "kwargs", "message"),
    (
        (OpenAIProvider, {"model": ""}, "model cannot be empty"),
        (AnthropicProvider, {"model": ""}, "model cannot be empty"),
        (OpenAIProvider, {"timeout_seconds": 0}, "timeout_seconds"),
        (OpenAIProvider, {"timeout_seconds": float("nan")}, "timeout_seconds"),
        (AnthropicProvider, {"timeout_seconds": 601}, "timeout_seconds"),
    ),
)
def test_provider_configuration_validation(
    constructor: Any,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        constructor(client=object(), **kwargs)


def test_compatible_provider_configuration_validation() -> None:
    with pytest.raises(ConfigurationError, match="required"):
        OpenAICompatibleProvider(name="", model="m", base_url="u", api_key="k", client=object())
    with pytest.raises(ConfigurationError, match="API key"):
        OpenAICompatibleProvider(name="x", model="m", base_url="u", api_key="")
    with pytest.raises(ConfigurationError, match="timeout_seconds"):
        OpenAICompatibleProvider(
            name="x", model="m", base_url="u", api_key="k", timeout_seconds=0, client=object()
        )


def test_built_in_sdk_clients_disable_automatic_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, dict[str, Any]] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            created["openai"] = kwargs

    class FakeAnthropic:
        def __init__(self, **kwargs: Any) -> None:
            created["anthropic"] = kwargs

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeOpenAI))
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(AsyncAnthropic=FakeAnthropic))

    OpenAIProvider(api_key="test-key")
    AnthropicProvider(api_key="test-key")
    OpenAICompatibleProvider(
        name="compatible",
        model="test-model",
        base_url="https://example.invalid/v1",
        api_key="test-key",
    )

    assert created["openai"]["max_retries"] == 0
    assert created["anthropic"]["max_retries"] == 0


def test_build_provider_requires_explicit_supported_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "XAI_API_KEY",
        "PERPLEXITY_API_KEY",
        "SONAR_API_KEY",
        "SAMSARIX_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        build_provider("openai")
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_provider("anthropic")
    with pytest.raises(ConfigurationError, match="XAI_API_KEY"):
        build_provider("xai")
    with pytest.raises(ConfigurationError, match="PERPLEXITY_API_KEY"):
        build_provider("perplexity")
    with pytest.raises(ConfigurationError, match="unknown provider"):
        build_provider("other")


def test_samsarix_environment_selects_provider_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, Any] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            created.update(kwargs)

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeOpenAI))
    monkeypatch.setenv("SAMSARIX_PROVIDER", "openai")
    monkeypatch.setenv("SAMSARIX_MODEL", "samsarix-test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    provider = provider_from_env(timeout_seconds=12)
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "samsarix-test-model"
    assert created["timeout"] == 12
