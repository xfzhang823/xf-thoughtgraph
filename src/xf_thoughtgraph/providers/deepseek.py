"""DeepSeek adapters using the OpenAI-compatible endpoint."""

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


_SPEC = OpenAICompatibleSpec(
    provider_name="deepseek",
    api_key_env="DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com",
)


def _thinking_extra_body(thinking: bool | None) -> dict[str, dict[str, str]] | None:
    """Build DeepSeek's optional V4 thinking-mode payload."""
    if thinking is None:
        return None
    if not isinstance(thinking, bool):
        raise TypeError("thinking must be True, False, or None")
    return {"thinking": {"type": "enabled" if thinking else "disabled"}}


class DeepSeekProvider(LLMProvider):
    """Synchronous DeepSeek adapter that preserves reasoning metadata."""

    provider_name = "deepseek"

    def __init__(
        self,
        client: OpenAI | None = None,
        *,
        api_key: str | None = None,
        thinking: bool | None = None,
    ):
        _thinking_extra_body(thinking)
        self.client = build_sync_client(_SPEC, client=client, api_key=api_key)
        self.thinking = thinking

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            response = self.client.chat.completions.create(
                **build_chat_completion_kwargs(
                    request, extra_body=_thinking_extra_body(self.thinking)
                )
            )
            return parse_chat_completion_response(response, provider_name=self.provider_name, model=request.model)
        except ProviderResponseError:
            raise
        except ProviderRequestError:
            raise
        except Exception as exc:
            raise ProviderRequestError("DeepSeek generation failed") from exc


class AsyncDeepSeekProvider(AsyncLLMProvider):
    """Asynchronous DeepSeek adapter that preserves reasoning metadata."""

    provider_name = "deepseek"

    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        *,
        api_key: str | None = None,
        thinking: bool | None = None,
    ):
        _thinking_extra_body(thinking)
        self.client = build_async_client(_SPEC, client=client, api_key=api_key)
        self.thinking = thinking

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            response = await self.client.chat.completions.create(
                **build_chat_completion_kwargs(
                    request, extra_body=_thinking_extra_body(self.thinking)
                )
            )
            return parse_chat_completion_response(response, provider_name=self.provider_name, model=request.model)
        except ProviderResponseError:
            raise
        except ProviderRequestError:
            raise
        except Exception as exc:
            raise ProviderRequestError("DeepSeek generation failed") from exc
