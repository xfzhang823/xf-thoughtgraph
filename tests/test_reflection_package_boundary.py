import os
import subprocess
import sys
from pathlib import Path

from xf_thoughtgraph.reflection import (
    DecompositionEvaluationService,
)


ROOT = Path(__file__).resolve().parents[1]


def test_core_reflection_owns_decomposition():
    assert DecompositionEvaluationService.__module__ == (
        "xf_thoughtgraph.reflection.decomposition"
    )


def test_root_graph_import_does_not_eagerly_load_interview():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    code = """
import sys
import xf_thoughtgraph

assert not any(
    name == "xf_thoughtgraph.interview"
    or name.startswith("xf_thoughtgraph.interview.")
    for name in sys.modules
)
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def test_interview_namespace_is_not_available():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util; assert importlib.util.find_spec('xf_thoughtgraph.interview') is None",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def test_thought_generation_has_no_interview_reflection_import():
    thought_generation = ROOT / "src" / "xf_thoughtgraph" / "thought_generation"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in thought_generation.rglob("*.py")
    )
    assert "xf_thoughtgraph.interview.reflection" not in source
    assert "xf_thoughtgraph.reflection" in source
