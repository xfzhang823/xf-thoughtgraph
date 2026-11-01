"""Deterministic models for indexed thought graphs."""

from typing import List, Optional

from pydantic import BaseModel, Field


class IndexedSubThoughtJSONModel(BaseModel):
    sub_thought_index: int = Field(..., description="Index of this sub-thought")
    name: str = Field(..., description="The name of the sub-thought")
    description: str = Field(..., description="A description of the sub-thought")
    importance: Optional[str] = Field(None, description="Importance of the sub-thought")
    connection_to_next: Optional[str] = Field(None, description="Connection to next sub-thought")


class IndexedThoughtJSONModel(BaseModel):
    thought_index: int = Field(..., description="Index of this main thought")
    thought: str = Field(..., description="The main thought or concept")
    description: Optional[str] = Field(None, description="Description of the main thought")
    sub_thoughts: Optional[List[IndexedSubThoughtJSONModel]] = Field(
        None, description="List of indexed sub-thoughts"
    )


class IndexedIdeaJSONModel(BaseModel):
    idea: str = Field(..., description="The overarching theme or idea")
    thoughts: Optional[List[IndexedThoughtJSONModel]] = Field(
        None, description="List of indexed thoughts for the idea"
    )
