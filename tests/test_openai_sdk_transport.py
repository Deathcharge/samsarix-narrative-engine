# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Exercise installed SDK request/response paths without network or paid calls."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from samsarix_narrative_engine import (
    Message,
    OpenAICompatibleProvider,
    OpenAIProvider,
    ProviderError,
)

sdk = pytest.importorskip("openai", reason="real SDK contract checks require the openai extra")
http = pytest.importorskip("httpx2" if int(sdk.__version__.split(".")[0]) >= 3 else "httpx")


def _provider(
    monkeypatch: pytest.MonkeyPatch, kind: str, handler: Callable[[Any], Any]
) -> tuple[Any, Any]:
    constructor = sdk.AsyncOpenAI
    clients: list[Any] = []

    def build(**kwargs: Any) -> Any:
        # Retain the real SDK constructor/serialization/parser. Intercept only HTTP.
        client = constructor(
            **kwargs,
            http_client=http.AsyncClient(transport=http.MockTransport(handler), trust_env=False),
        )
        clients.append(client)
        return client

    monkeypatch.setattr(sdk, "AsyncOpenAI", build)
    if kind == "responses":
        provider: Any = OpenAIProvider(
            api_key="offline-fixture-key", model="fixture-model", timeout_seconds=4.5
        )
    else:
        provider = OpenAICompatibleProvider(
            name="fixture",
            model="fixture-model",
            base_url="https://example.invalid/v1",
            api_key="offline-fixture-key",
            timeout_seconds=4.5,
        )
    assert len(clients) == 1
    assert clients[0].max_retries == 0
    assert clients[0].timeout == 4.5
    return provider, clients[0]


@pytest.mark.parametrize("kind", ("responses", "compatible"))
async def test_installed_sdk_serializes_requests_and_parses_responses(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    requests: list[Any] = []

    def handler(request: Any) -> Any:
        requests.append(request)
        assert request.method == "POST"
        body = json.loads(request.content)
        assert body["model"] == "fixture-model"
        if kind == "responses":
            assert request.url.path == "/v1/responses"
            assert body["store"] is False
            assert body["max_output_tokens"] == 25
            assert body["input"][-1] == {"role": "user", "content": "Fixture brief"}
            payload = {
                "id": "resp_fixture",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "fixture-model",
                "output": [
                    {
                        "id": "msg_fixture",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Offline SDK response",
                                "annotations": [],
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18},
            }
        else:
            assert request.url.path == "/v1/chat/completions"
            assert body["max_tokens"] == 25
            assert body["messages"][-1] == {"role": "user", "content": "Fixture brief"}
            payload = {
                "id": "chatcmpl_fixture",
                "object": "chat.completion",
                "created": 0,
                "model": "fixture-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "Offline SDK response"},
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            }
        return http.Response(200, json=payload, request=request)

    provider, client = _provider(monkeypatch, kind, handler)
    try:
        response = await provider.complete(
            (Message("user", "Fixture brief"),), max_output_tokens=25
        )
    finally:
        await client.close()
    assert len(requests) == 1
    assert response.content == "Offline SDK response"
    assert response.model == "fixture-model"
    assert response.usage.total_tokens == 18


@pytest.mark.parametrize("kind", ("responses", "compatible"))
@pytest.mark.parametrize("failure", (429, 500, "timeout"))
async def test_installed_sdk_does_not_retry_and_sanitizes_failures(
    kind: str, failure: int | str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def handler(request: Any) -> Any:
        nonlocal calls
        calls += 1
        if failure == "timeout":
            raise http.ReadTimeout("private-error-fixture", request=request)
        return http.Response(
            failure,
            request=request,
            json={"error": {"message": "private-error-fixture", "type": "fixture_error"}},
        )

    provider, client = _provider(monkeypatch, kind, handler)
    try:
        with pytest.raises(ProviderError) as caught:
            await provider.complete((Message("user", "Fixture brief"),), max_output_tokens=25)
    finally:
        await client.close()
    assert calls == 1
    assert "private-error-fixture" not in str(caught.value)
    assert isinstance(caught.value.__cause__, sdk.APIError)
