"""Typed request contracts for the provider-backed generation façade."""

from dataclasses import dataclass

from xf_thoughtgraph.models import ProgressionType


_DEFAULT_MAX_TOKENS = 1056


@dataclass(frozen=True)
class HorizontalGenerationRequest:
    """Configuration for generating sibling-level thoughts about an idea."""

    idea: str
    model: str
    num_thoughts: int = 10
    num_clusters: int | None = None
    top_n: int | None = None
    temperature: float = 0.7
    max_tokens: int = _DEFAULT_MAX_TOKENS
    timeout: float | None = None
    prompt_template: str | None = None


@dataclass(frozen=True)
class VerticalGenerationRequest:
    """Configuration for expanding one thought into more-specific children."""

    idea: str
    thought: str
    model: str
    progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS
    num_sub_thoughts: int = 7
    temperature: float = 0.7
    max_tokens: int = _DEFAULT_MAX_TOKENS
    timeout: float | None = None
    prompt_template: str | None = None

    def __post_init__(self) -> None:
        """Normalize compatible raw strings to the public enum."""
        if not isinstance(self.progression_type, ProgressionType):
            object.__setattr__(
                self, "progression_type", ProgressionType(self.progression_type)
            )


__all__ = [
    "HorizontalGenerationRequest",
    "VerticalGenerationRequest",
]
