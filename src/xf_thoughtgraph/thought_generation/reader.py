"""In-memory readers for validated idea hierarchies."""

from collections.abc import Mapping
from typing import Any

from xf_thoughtgraph.models import IdeaJSONModel, IndexedIdeaJSONModel

from .validation import validate_idea, validate_indexed_idea


class ThoughtReader:
    """Read an already supplied unindexed model without filesystem access."""

    def __init__(self, data: Mapping[str, Any] | IdeaJSONModel) -> None:
        """Validate ``data`` for read-only access; raises on invalid input."""
        self.idea_instance = validate_idea(data)

    def get_idea(self) -> str:
        """Return the root idea string."""
        return self.idea_instance.idea

    def get_thoughts(self) -> list[str]:
        """Return top-level thought names."""
        return [item.thought for item in self.idea_instance.thoughts or []]

    def get_thoughts_and_descriptions(self) -> list[dict[str, Any]]:
        """Return ``{thought, description}`` dicts per top-level thought."""
        return [
            {"thought": item.thought, "description": item.description}
            for item in self.idea_instance.thoughts or []
        ]

    def get_sub_thoughts_for_thought(self, thought_name: str) -> list[dict[str, Any]]:
        """Return sub-thought dicts for ``thought_name``; empty if not found."""
        for thought in self.idea_instance.thoughts or []:
            if thought.thought == thought_name:
                return [
                    {
                        "name": item.name,
                        "description": item.description,
                        "importance": item.importance,
                        "connection_to_next": item.connection_to_next,
                    }
                    for item in thought.sub_thoughts or []
                ]
        return []


class IndexedThoughtReader:
    """Read an already supplied indexed model without filesystem access."""

    def __init__(self, data: Mapping[str, Any] | IndexedIdeaJSONModel) -> None:
        """Validate ``data`` for read-only access; raises on invalid input."""
        self.idea_instance = validate_indexed_idea(data)

    def get_idea(self) -> str:
        """Return the root idea string."""
        return self.idea_instance.idea

    def get_thoughts(self) -> list[dict[str, Any]]:
        """Return ``{thought_index, thought}`` dicts per top-level thought."""
        return [
            {"thought_index": item.thought_index, "thought": item.thought}
            for item in self.idea_instance.thoughts or []
        ]

    def get_thoughts_and_descriptions(self) -> list[dict[str, Any]]:
        """Return ``{thought_index, thought, description}`` dicts per thought."""
        return [
            {
                "thought_index": item.thought_index,
                "thought": item.thought,
                "description": item.description,
            }
            for item in self.idea_instance.thoughts or []
        ]

    def get_sub_thoughts_for_thought(self, thought_index: int) -> list[dict[str, Any]]:
        """Return sub-thought dicts for ``thought_index``; empty if not found."""
        for thought in self.idea_instance.thoughts or []:
            if thought.thought_index == thought_index:
                return [
                    {
                        "sub_thought_index": item.sub_thought_index,
                        "name": item.name,
                        "description": item.description,
                        "importance": item.importance,
                        "connection_to_next": item.connection_to_next,
                    }
                    for item in thought.sub_thoughts or []
                ]
        return []

    def dump_all(self) -> dict[str, Any]:
        """Return the full validated model as a dict."""
        return self.idea_instance.model_dump()
