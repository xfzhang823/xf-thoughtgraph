"""Provider exports, lazy adapter loading, and named provider selection."""

from importlib import import_module
import os

from xf_thoughtgraph._env import load_repository_env

from .contracts import (
    AsyncLLMProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderError,
    ProviderRequestError,
    ProviderResponseError,
)

load_repository_env()

_LAZY_ADAPTERS = {
    "AnthropicProvider": (".anthropic", "AnthropicProvider"),
    "AsyncAnthropicProvider": (".anthropic", "AsyncAnthropicProvider"),
    "AsyncDeepSeekProvider": (".deepseek", "AsyncDeepSeekProvider"),
    "AsyncGeminiProvider": (".gemini", "AsyncGeminiProvider"),
    "AsyncOpenAIProvider": (".openai", "AsyncOpenAIProvider"),
    "DeepSeekProvider": (".deepseek", "DeepSeekProvider"),
    "GeminiProvider": (".gemini", "GeminiProvider"),
    "OpenAIProvider": (".openai", "OpenAIProvider"),
}

_DEFAULT_MODELS = {
    "openai": "gpt-5.6-luna",
    "gemini": "gemini-3.6-flash",
    "deepseek": "deepseek-v4-flash",
    "anthropic": "claude-3-5-sonnet-20241022",
}


def __getattr__(name: str):
    """Lazily import SDK-backed adapter classes on first access."""
    if name not in _LAZY_ADAPTERS:
        raise AttributeError(name)
    module_name, attribute = _LAZY_ADAPTERS[name]
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value


def create_provider(provider: str, **kwargs):
    """Instantiate one configured provider by normalized provider name."""
    normalized = provider.strip().lower()
    class_map = {
        "anthropic": "AnthropicProvider",
        "claude": "AnthropicProvider",
        "deepseek": "DeepSeekProvider",
        "gemini": "GeminiProvider",
        "openai": "OpenAIProvider",
    }
    try:
        class_name = class_map[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider}") from exc
    module = import_module(__name__)
    return getattr(module, class_name)(**kwargs)


def default_model(provider: str) -> str:
    """Resolve the public façade's default model for a provider.

    An explicit ``<PROVIDER>_MODEL`` environment variable takes precedence.
    """
    normalized = provider.strip().lower()
    try:
        fallback = _DEFAULT_MODELS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider}") from exc
    return os.getenv(f"{normalized.upper()}_MODEL", fallback)

__all__ = [
    "AnthropicProvider", "AsyncAnthropicProvider", "AsyncDeepSeekProvider",
    "AsyncGeminiProvider", "AsyncLLMProvider", "AsyncOpenAIProvider",
    "DeepSeekProvider", "GenerationRequest", "GenerationResult", "GeminiProvider",
    "LLMProvider", "OpenAIProvider", "ProviderError", "ProviderRequestError",
    "ProviderResponseError", "create_provider", "default_model",
]
