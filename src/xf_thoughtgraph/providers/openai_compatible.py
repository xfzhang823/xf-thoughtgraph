"""Shared request/response plumbing for OpenAI-compatible providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI, OpenAI

from xf_thoughtgraph._env import load_repository_env

from .contracts import GenerationRequest, GenerationResult, ProviderResponseError


@dataclass(frozen=True)
class OpenAICompatibleSpec:
    """Provider-specific endpoint and environment configuration."""

    provider_name: str
    api_key_env: str
    base_url: str | None = None


def build_sync_client(
    spec: OpenAICompatibleSpec,
    *,
    client: OpenAI | None = None,
    api_key: str | None = None,
) -> OpenAI:
    """Build or reuse a synchronous OpenAI-compatible client."""
    load_repository_env()
    if client is not None:
        return client
    resolved_api_key = api_key or os.getenv(spec.api_key_env)
    if not resolved_api_key:
        raise ValueError(f"api_key or a {spec.provider_name} client is required")
    kwargs: dict[str, Any] = {"api_key": resolved_api_key}
    if spec.base_url is not None:
        kwargs["base_url"] = spec.base_url
    return OpenAI(**kwargs)


def build_async_client(
    spec: OpenAICompatibleSpec,
    *,
    client: AsyncOpenAI | None = None,
    api_key: str | None = None,
) -> AsyncOpenAI:
    """Build or reuse an asynchronous OpenAI-compatible client."""
    load_repository_env()
    if client is not None:
        return client
    resolved_api_key = api_key or os.getenv(spec.api_key_env)
    if not resolved_api_key:
        raise ValueError(f"api_key or an {spec.provider_name} client is required")
    kwargs: dict[str, Any] = {"api_key": resolved_api_key}
    if spec.base_url is not None:
        kwargs["base_url"] = spec.base_url
    return AsyncOpenAI(**kwargs)


def build_chat_completion_kwargs(
    request: GenerationRequest, *, extra_body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Translate a package request into OpenAI chat-completions kwargs."""
    kwargs: dict[str, Any] = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.prompt}],
    }
    if request.model.lower().startswith("gpt-5"):
        # ``minimal`` is not supported by every GPT-5-family model (for
        # example, gpt-5.6-luna). ``none`` is broadly accepted and can be
        # overridden when a caller wants the model to reason.
        kwargs["reasoning_effort"] = os.getenv("OPENAI_REASONING_EFFORT", "none")
        kwargs["max_completion_tokens"] = request.max_tokens
    else:
        kwargs["temperature"] = request.temperature
        kwargs["max_tokens"] = request.max_tokens
    if extra_body is not None:
        kwargs["extra_body"] = extra_body
    if request.timeout is not None:
        kwargs["timeout"] = request.timeout
    return kwargs


def parse_chat_completion_response(
    response: Any, *, provider_name: str, model: str
) -> GenerationResult:
    """Normalize a non-streaming OpenAI-compatible chat completion response."""
    try:
        message = response.choices[0].message
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise ProviderResponseError(
            f"{provider_name} response did not contain message text"
        ) from exc

    try:
        text = message.content
    except AttributeError as exc:
        raise ProviderResponseError(
            f"{provider_name} response did not contain message text"
        ) from exc

    if not isinstance(text, str):
        raise ProviderResponseError(
            f"{provider_name} response message text was not a string"
        )

    reasoning_content = getattr(message, "reasoning_content", None)
    if reasoning_content is not None and not isinstance(reasoning_content, str):
        raise ProviderResponseError(
            f"{provider_name} response reasoning text was not a string"
        )

    return GenerationResult(
        text=text,
        provider=provider_name,
        model=model,
        reasoning_content=reasoning_content,
    )
