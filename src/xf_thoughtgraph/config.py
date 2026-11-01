"""Explicit typed package configuration with no implicit loading."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """Explicit settings for one provider invocation boundary."""

    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1056
    timeout: float | None = None


@dataclass(frozen=True)
class ThoughtGraphConfig:
    """Optional package configuration; storage is deliberately not implicit."""

    provider: ProviderConfig | None = None
