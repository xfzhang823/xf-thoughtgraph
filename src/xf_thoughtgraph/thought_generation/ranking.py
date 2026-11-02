"""Provider-backed cluster selection and deterministic cluster conversion."""

from typing import Any

from pydantic import ValidationError

from xf_thoughtgraph.models import (
    IdeaClusterJSONModel,
    IdeaJSONModel,
    ThoughtJSONModel,
)
from xf_thoughtgraph.prompts import RECLUSTER_AND_PICK_TOP_CLUSTER_PROMPT
from xf_thoughtgraph.providers import GenerationRequest, LLMProvider

from .parsing import extract_json


def convert_clusters_to_idea(cluster_model: IdeaClusterJSONModel) -> IdeaJSONModel:
    """Convert selected clusters to ordered top-level thoughts."""
    if not cluster_model.clusters:
        raise ValueError("The input IdeaClusterJSONModel contains no clusters.")
    thoughts = []
    for cluster in cluster_model.clusters:
        if not cluster.name or not cluster.description:
            raise ValueError("Cluster must have a name and description.")
        if not cluster.thoughts:
            raise ValueError(f"Cluster '{cluster.name}' must contain at least one thought.")
        thoughts.append(
            ThoughtJSONModel(
                thought=cluster.name,
                description=cluster.description,
                sub_thoughts=None,
            )
        )
    return IdeaJSONModel(idea=cluster_model.idea, thoughts=thoughts)


def select_clusters(
    provider: LLMProvider,
    thoughts: IdeaJSONModel,
    *,
    model: str,
    num_clusters: int,
    top_n: int,
    temperature: float = 0.7,
    max_tokens: int = 1056,
    timeout: float | None = None,
) -> IdeaClusterJSONModel:
    """Ask the provider to group thoughts and validate the returned clusters."""
    thoughts_list = [
        {"thought": item.thought, "description": item.description}
        for item in thoughts.thoughts or []
    ]
    prompt = RECLUSTER_AND_PICK_TOP_CLUSTER_PROMPT.format(
        idea=thoughts.idea,
        thoughts_list=thoughts_list,
        num_clusters=num_clusters,
        top_n=top_n,
    )
    result = provider.generate(
        GenerationRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    )
    data: Any = extract_json(result.text)
    try:
        return IdeaClusterJSONModel.model_validate(data)
    except (TypeError, ValidationError) as exc:
        raise ValueError("Invalid cluster response") from exc
