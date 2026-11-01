"""Provider-neutral request, result, and protocol contracts."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class GenerationRequest:
    """A provider-independent text-generation request."""

    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1056
    timeout: float | None = None

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("model must not be empty")
        if self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be positive when provided")


@dataclass(frozen=True)
class GenerationResult:
    """Normalized provider output.

    ``text`` is the final answer visible to callers. ``reasoning_content`` is
    optional provider-specific metadata and must remain separate from ``text``.
    """

    text: str
    provider: str
    model: str
    reasoning_content: str | None = None


class ProviderError(RuntimeError):
    """Base exception for provider failures."""


class ProviderRequestError(ProviderError):
    """Raised when a provider rejects or cannot process a request."""


class ProviderResponseError(ProviderError):
    """Raised when a provider response cannot be normalized."""


@runtime_checkable
class LLMProvider(Protocol):
    """Synchronous provider contract."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate one normalized result."""


@runtime_checkable
class AsyncLLMProvider(Protocol):
    """Asynchronous provider contract."""

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate one normalized result asynchronously."""
