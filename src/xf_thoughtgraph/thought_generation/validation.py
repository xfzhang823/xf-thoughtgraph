"""Validation and in-memory reading of thought-graph structures."""

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from xf_thoughtgraph.models import (
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    ThoughtJSONModel,
)

from .parsing import extract_json


def validate_idea(data: Mapping[str, Any] | IdeaJSONModel) -> IdeaJSONModel:
    """Validate an unindexed idea without reading or writing files."""
    if isinstance(data, IdeaJSONModel):
        return data
    try:
        return IdeaJSONModel(**dict(data))
    except (TypeError, ValidationError) as exc:
        raise ValueError("Invalid idea thought graph") from exc


def validate_indexed_idea(
    data: Mapping[str, Any] | IndexedIdeaJSONModel,
) -> IndexedIdeaJSONModel:
    """Validate an indexed idea without reading or writing files."""
    if isinstance(data, IndexedIdeaJSONModel):
        return data
    try:
        return IndexedIdeaJSONModel(**dict(data))
    except (TypeError, ValidationError) as exc:
        raise ValueError("Invalid indexed thought graph") from exc


def parse_idea(response_text: str) -> IdeaJSONModel:
    """Parse and validate a provider response as an idea graph."""
    return validate_idea(extract_json(response_text))


def parse_thought(response_text: str) -> ThoughtJSONModel:
    """Parse and validate a provider response as a thought expansion."""
    data = extract_json(response_text)
    try:
        return ThoughtJSONModel(**data)
    except (TypeError, ValidationError) as exc:
        raise ValueError("Invalid vertical thought response") from exc
