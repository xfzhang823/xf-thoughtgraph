"""Repository-local environment loading for development and tests."""

from __future__ import annotations

import os
import shlex
from pathlib import Path


def load_repository_env(filename: str = ".env") -> None:
    """Load the repository `.env` file without overriding existing env vars."""
    env_path = _find_env_file(filename)
    if env_path is None:
        return

    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        _load_env_file_fallback(env_path)
    else:
        load_dotenv(env_path, override=False)


def _find_env_file(filename: str) -> Path | None:
    """Find the first matching env file near the current working directory."""
    search_roots = [Path.cwd(), *Path.cwd().parents]
    module_root = Path(__file__).resolve().parent
    search_roots.extend([module_root, *module_root.parents])

    seen: set[Path] = set()
    for root in search_roots:
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)
        candidate = root / filename
        if candidate.is_file():
            return candidate
    return None


def _load_env_file_fallback(path: Path) -> None:
    """Minimal `.env` parser used when python-dotenv is unavailable."""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        try:
            tokens = shlex.split(line, comments=True, posix=True)
        except ValueError:
            continue
        if not tokens:
            continue
        assignment = tokens[0]
        if assignment == "export" and len(tokens) > 1:
            assignment = tokens[1]
        if "=" not in assignment:
            continue
        key, value = assignment.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value
