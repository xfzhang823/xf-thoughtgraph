"""Provider and structured-response plumbing shared by reflection capabilities."""

from collections.abc import Callable
from typing import Any, TypeVar

from xf_thoughtgraph.providers import GenerationRequest, LLMProvider, ProviderResponseError
from xf_thoughtgraph.thought_generation.parsing import extract_json


T = TypeVar("T")


def generate_structured(
    provider: LLMProvider,
    request: GenerationRequest,
    parse: Callable[[Any], T],
    *,
    error_message: str,
) -> T:
    """Generate, decode, and validate one structured reflection response."""

    result = provider.generate(request)
    try:
        return parse(extract_json(result.text))
    except Exception as exc:
        raise ProviderResponseError(error_message) from exc
