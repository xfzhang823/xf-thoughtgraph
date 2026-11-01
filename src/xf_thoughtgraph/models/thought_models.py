"""Deterministic models for thought graphs and generated thought data."""

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)


class ProgressionType(str, Enum):
    """Supported semantic modes for vertical thought generation."""

    IMPLEMENTATION_STEPS = "implementation_steps"
    SIMPLE_TO_COMPLEX = "simple_to_complex"
    CHRONOLOGICAL = "chronological"
    PROBLEM_SOLUTION = "problem_solution"
    PREREQUISITE_DEPENDENCY = "prerequisite_dependency"


class Thought(BaseModel):
    """A named conceptual thought returned by the concept-first API."""

    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class ThoughtArray(BaseModel):
    """One horizontal expansion of a concept."""

    concept: str = Field(..., min_length=1)
    thoughts: List[Thought] = Field(default_factory=list)


class ThoughtNode(Thought):
    """A thought with zero or more vertically expanded child thoughts."""

    children: List["ThoughtNode"] = Field(default_factory=list)


class ThoughtGraph(BaseModel):
    """A bounded hierarchy rooted at the requested concept."""

    concept: str = Field(..., min_length=1)
    root: ThoughtNode
    depth: int = Field(..., ge=1)
    breadth: int = Field(..., ge=1)


ThoughtNode.model_rebuild()


class SubThoughtJSONModel(BaseModel):
    name: str = Field(..., description="The name of the sub-thought")
    description: str = Field(..., description="A description of the sub-thought")
    importance: Optional[str] = Field(None, description="The importance of the sub-thought, optional")
    connection_to_next: Optional[str] = Field(
        None, description="Description of how this sub-thought connects to the next, optional"
    )


class ThoughtJSONModel(BaseModel):
    thought: str = Field(..., description="The main thought or concept")
    description: Optional[str] = Field(None, description="A description of the main thought")
    sub_thoughts: Optional[List[SubThoughtJSONModel]] = Field(
        None, description="An optional list of sub-thoughts associated with the main thought"
    )

    model_config = ConfigDict(from_attributes=True)


class ClusterJSONModel(BaseModel):
    name: str = Field(..., description="Name of the cluster")
    description: Optional[str] = Field(None, description="Description of the cluster")
    thoughts: List[str] = Field(..., description="List of thought names within the cluster")

    model_config = ConfigDict(from_attributes=True)


class IdeaClusterJSONModel(BaseModel):
    idea: str = Field(..., description="The overarching theme or idea")
    clusters: List[ClusterJSONModel] = Field(..., description="List of clusters")


class IdeaJSONModel(BaseModel):
    idea: str = Field(..., description="The overarching theme or idea.")
    thoughts: Optional[List[ThoughtJSONModel]] = Field(
        None, description="A list of individual thoughts without clustering."
    )

    model_config = ConfigDict(from_attributes=True)


def validate_thought_batch(thought_data_batch: List[dict]) -> List[ThoughtJSONModel]:
    """Validate each thought and return only valid entries."""
    validated_thoughts = []
    for idx, data in enumerate(thought_data_batch):
        try:
            validated_thoughts.append(ThoughtJSONModel(**data))
        except ValidationError as exc:
            logger.error("Validation error in batch item at index %s: %s", idx, exc)
    return validated_thoughts


