"""Provider-backed horizontal thought generation."""

from xf_thoughtgraph.models import IdeaJSONModel
from xf_thoughtgraph.prompts import THOUGHT_GENERATION_PROMPT
from xf_thoughtgraph.providers import GenerationRequest, LLMProvider

from .validation import parse_idea


def generate_horizontal(
    provider: LLMProvider,
    *,
    idea: str,
    model: str,
    num_thoughts: int = 10,
    temperature: float = 0.7,
    max_tokens: int = 1056,
    timeout: float | None = None,
    prompt_template: str | None = None,
) -> IdeaJSONModel:
    """Generate and validate high-level thoughts using an injected provider."""
    prompt_template = prompt_template or THOUGHT_GENERATION_PROMPT
    prompt = prompt_template.format(idea=idea, num_sub_thoughts=num_thoughts)
    result = provider.generate(
        GenerationRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    )
    return parse_idea(result.text)
