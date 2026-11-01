"""Deterministic hierarchy indexing."""

from xf_thoughtgraph.models import (
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    IndexedSubThoughtJSONModel,
    IndexedThoughtJSONModel,
)


def index_idea(idea_model: IdeaJSONModel) -> IndexedIdeaJSONModel:
    """Add zero-based thought and sub-thought indices in source order."""
    indexed_thoughts = []
    for thought_index, thought in enumerate(idea_model.thoughts or []):
        indexed_sub_thoughts = [
            IndexedSubThoughtJSONModel(
                sub_thought_index=sub_index,
                name=sub_thought.name,
                description=sub_thought.description,
                importance=sub_thought.importance,
                connection_to_next=sub_thought.connection_to_next,
            )
            for sub_index, sub_thought in enumerate(thought.sub_thoughts or [])
        ]
        indexed_thoughts.append(
            IndexedThoughtJSONModel(
                thought_index=thought_index,
                thought=thought.thought,
                description=thought.description,
                sub_thoughts=indexed_sub_thoughts,
            )
        )
    return IndexedIdeaJSONModel(idea=idea_model.idea, thoughts=indexed_thoughts)
