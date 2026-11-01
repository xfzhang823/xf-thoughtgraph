"""Anthropic adapters kept separate from the OpenAI-compatible providers."""

import os
from typing import Any

from anthropic import AsyncAnthropic, Anthropic

from xf_thoughtgraph._env import load_repository_env

from .contracts import (
    AsyncLLMProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderRequestError,
    ProviderResponseError,
)


def _extract_text(response: Any) -> str:
    try:
        block = response.content[0]
        text = block.text
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise ProviderResponseError("Anthropic response did not contain message text") from exc
    if not isinstance(text, str):
        raise ProviderResponseError("Anthropic response message text was not a string")
    return text


class AnthropicProvider(LLMProvider):
    """Synchronous Anthropic adapter with explicit or env-backed client setup."""

    provider_name = "anthropic"

    def __init__(self, client: Anthropic | None = None, *, api_key: str | None = None):
        load_repository_env()
        if client is None:
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
            if not api_key:
                raise ValueError("api_key or an Anthropic client is required")
            client = Anthropic(api_key=api_key)
        self.client = client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            kwargs: dict[str, Any] = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "messages": [{"role": "user", "content": request.prompt}],
                "temperature": request.temperature,
            }
            if request.timeout is not None:
                kwargs["timeout"] = request.timeout
            response = self.client.messages.create(**kwargs)
            return GenerationResult(_extract_text(response), self.provider_name, request.model)
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("Anthropic generation failed") from exc


class AsyncAnthropicProvider(AsyncLLMProvider):
    """Asynchronous Anthropic adapter with explicit or env-backed client setup."""

    provider_name = "anthropic"

    def __init__(self, client: AsyncAnthropic | None = None, *, api_key: str | None = None):
        load_repository_env()
        if client is None:
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
            if not api_key:
                raise ValueError("api_key or an Anthropic client is required")
            client = AsyncAnthropic(api_key=api_key)
        self.client = client

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            kwargs: dict[str, Any] = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "messages": [{"role": "user", "content": request.prompt}],
                "temperature": request.temperature,
            }
            if request.timeout is not None:
                kwargs["timeout"] = request.timeout
            response = await self.client.messages.create(**kwargs)
            return GenerationResult(_extract_text(response), self.provider_name, request.model)
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("Anthropic generation failed") from exc
