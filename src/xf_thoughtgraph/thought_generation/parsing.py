"""Provider-response parsing for thought-generation outputs."""

import json
import re
from typing import Any


def extract_json(response_text: str) -> Any:
    """Extract and decode the first JSON object from provider text."""
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValueError("Provider returned an empty response")
    match = re.search(r"{.*}", response_text, re.DOTALL)
    if not match:
        raise ValueError("Provider response did not contain a JSON object")
    candidate = match.group(0)
    candidate = re.sub(r"\s*//[^\n]*", "", candidate)
    candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
    candidate = re.sub(r"([{\[])\s*,", r"\1", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError("Provider response contained invalid JSON") from exc
