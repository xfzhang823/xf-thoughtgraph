"""In-memory optional repository."""

from copy import deepcopy
from typing import Any


class MemoryRepository:
    """Store values only for the lifetime of this instance."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def load(self, key: str) -> Any:
        return deepcopy(self._values[key])

    def save(self, key: str, value: Any) -> None:
        self._values[key] = deepcopy(value)
