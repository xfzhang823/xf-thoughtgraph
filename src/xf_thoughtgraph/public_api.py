"""Small convenience functions for normal package consumers."""

from xf_thoughtgraph.models import ProgressionType, ThoughtGraph
from xf_thoughtgraph.providers import LLMProvider
from xf_thoughtgraph.thought_generation import ThoughtGraphEngine


def generate_thought_graph(
    topic: str,
    *,
    exploration: str = "balanced",
    progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
    provider: LLMProvider | str | None = None,
    model: str | None = None,
) -> ThoughtGraph:
    """Generate a thought graph through the canonical engine.

    Provider selection remains explicit because the package has no implicit
    provider-selection setting.  When ``provider`` is a provider name, the
    existing engine/provider architecture resolves its default model and any
    ``<PROVIDER>_MODEL`` environment override when ``model`` is omitted.
    ``progression_type`` selects the semantic relationship used for vertical
    child generation and is forwarded to the canonical engine unchanged.

    Args:
        topic: Root concept to disaggregate into a thought graph.
        exploration: Adaptive continuation profile. Must be ``"focused"``,
            ``"balanced"``, or ``"rich"``; defaults to ``"balanced"``.
        progression_type: Semantic relationship used for vertically generated
            children. Defaults to
            ``ProgressionType.IMPLEMENTATION_STEPS``.
        provider: Provider name (``"openai"``, ``"gemini"``,
            ``"deepseek"``, or ``"anthropic"``) or an injected
            ``LLMProvider`` instance.
        model: Optional provider-specific model identifier. When omitted, the
            provider's configured default model is used.

    Returns:
        A generated ``ThoughtGraph`` containing the requested root concept and
        its horizontal and vertical thought hierarchy.

    Raises:
        ValueError: If ``provider`` is omitted or the engine rejects an
            invalid topic, exploration profile, progression type, or provider
            configuration.
    """
    if provider is None:
        raise ValueError(
            "provider is required; pass a provider name or an LLMProvider "
            "instance"
        )

    engine = ThoughtGraphEngine(provider, model=model)
    return engine.generate_thought_graph(
        topic=topic,
        exploration=exploration,
        progression_type=progression_type,
    )


__all__ = ["generate_thought_graph"]
