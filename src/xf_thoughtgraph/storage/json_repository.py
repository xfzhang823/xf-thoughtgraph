"""Explicit-directory JSON repository."""

import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class JsonRepository:
    """Persist JSON values under a caller-selected directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def _path_for(self, key: str) -> Path:
        if not key or Path(key).name != key or key in {".", ".."}:
            raise ValueError("key must be a non-empty filename without path components")
        return self.directory / f"{key}.json"

    def load(self, key: str) -> Any:
        path = self._path_for(key)
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)

    def save(self, key: str, value: Any) -> None:
        path = self._path_for(key)
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(
                value,
                default=_json_default,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.directory, delete=False
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
