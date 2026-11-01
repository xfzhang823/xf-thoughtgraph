"""OpenAI provider adapters built on the official SDK."""

from openai import AsyncOpenAI, OpenAI

from .contracts import (
    AsyncLLMProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderRequestError,
    ProviderResponseError,
)
from .openai_compatible import (
    OpenAICompatibleSpec,
    build_async_client,
    build_chat_completion_kwargs,
    build_sync_client,
    parse_chat_completion_response,
)

_SPEC = OpenAICompatibleSpec(provider_name="openai", api_key_env="OPENAI_API_KEY")


class OpenAIProvider(LLMProvider):
    """Synchronous OpenAI adapter using chat completions and env fallback."""

    provider_name = "openai"

    def __init__(self, client: OpenAI | None = None, *, api_key: str | None = None):
        self.client = build_sync_client(_SPEC, client=client, api_key=api_key)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            response = self.client.chat.completions.create(
                **build_chat_completion_kwargs(request)
            )
            return parse_chat_completion_response(
                response, provider_name=self.provider_name, model=request.model
            )
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("OpenAI generation failed") from exc


class AsyncOpenAIProvider(AsyncLLMProvider):
    """Asynchronous OpenAI adapter using the same chat-completions path."""

    provider_name = "openai"

    def __init__(
        self, client: AsyncOpenAI | None = None, *, api_key: str | None = None
    ):
        self.client = build_async_client(_SPEC, client=client, api_key=api_key)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            response = await self.client.chat.completions.create(
                **build_chat_completion_kwargs(request)
            )
            return parse_chat_completion_response(
                response, provider_name=self.provider_name, model=request.model
            )
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("OpenAI generation failed") from exc
