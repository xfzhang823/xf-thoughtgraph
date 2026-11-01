"""Optional, caller-selected persistence boundaries and implementations."""

from .contracts import Repository
from .json_repository import JsonRepository
from .memory_repository import MemoryRepository

__all__ = ["JsonRepository", "MemoryRepository", "Repository"]
