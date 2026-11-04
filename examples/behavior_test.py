"""Behavioral harness for the public thought-generation API.

Example:
    ```bash
    python examples/behavior_test.py \
        --topic "clinical research participant recruitment" \
        --provider deepseek \
        --model deepseek-v4-flash \
        --vertical 2 \
        --horizontal 5 \
        --progression implementation_steps
    ```

The script prints the selected configuration and a readable tree view of the
generated thought graph.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from xf_thoughtgraph import ProgressionType, ThoughtGraphEngine
from xf_thoughtgraph.providers import (
    GenerationRequest,
    GenerationResult,
    create_provider,
    default_model,
)
from xf_thoughtgraph.thought_generation.parsing import extract_json

try:
    from .support import FakeProvider
except ImportError:  # pragma: no cover - direct script execution
    from support import FakeProvider

DEFAULT_TOPIC = "clinical research participant recruitment"
DEFAULT_PROVIDER = "openai"
DEFAULT_VERTICAL = 2
DEFAULT_HORIZONTAL = 5
DEFAULT_PROGRESSION = ProgressionType.IMPLEMENTATION_STEPS


@dataclass(frozen=True)
class RuntimeConfig:
    topic: str
    provider: str
    model: str | None
    vertical: int
    horizontal: int
    progression_type: ProgressionType
    exploration: str | None
    output: str | None


class CountingProvider:
    """Transparent provider wrapper used only to collect behavior metrics."""

    def __init__(self, provider):
        self.provider = provider
        self.requests: list[GenerationRequest] = []
        self.decomposition_records: list[dict] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        result = self.provider.generate(request)
        if "Decide whether each retained thought" in request.prompt:
            candidates = [
                {
                    "id": candidate_id,
                    "thought": thought,
                    "description": description,
                }
                for candidate_id, thought, description in re.findall(
                    r"- id: ([^\n]+)\n  thought: ([^\n]+)\n  description: ([^\n]*)",
                    request.prompt,
                )
            ]
            ancestor_line = re.search(r"^ancestor_path: (.+)$", request.prompt, re.MULTILINE)
            self.decomposition_records.append(
                {
                    "ancestor_path": (
                        ancestor_line.group(1).split(" -> ") if ancestor_line else []
                    ),
                    "candidates": candidates,
                    "result": extract_json(result.text),
                }
            )
        return result


def _env_default(name: str, fallback: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else fallback


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def parse_deepseek_thinking() -> bool | None:
    """Parse the optional DeepSeek thinking-mode harness setting."""
    value = os.getenv("DEEPSEEK_THINKING")
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "enabled":
        return True
    if normalized == "disabled":
        return False
    raise ValueError("Use 'enabled' or 'disabled' for DEEPSEEK_THINKING")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a public thought-graph behavior check with one graph output."
    )
    parser.add_argument(
        "--topic",
        default=_env_default("BEHAVIOR_TEST_TOPIC", DEFAULT_TOPIC),
        help="Root topic to expand.",
    )
    parser.add_argument(
        "--provider",
        default=_env_default("THOUGHT_GRAPH_PROVIDER", DEFAULT_PROVIDER),
        choices=["openai", "gemini", "deepseek", "anthropic", "fake"],
        help="LLM provider to use.",
    )
    parser.add_argument(
        "--model",
        default=_env_optional("THOUGHT_GRAPH_MODEL"),
        help=(
            "Optional provider model override. When omitted, the provider's "
            "default model is used."
        ),
    )
    parser.add_argument(
        "--vertical",
        type=int,
        default=int(_env_default("BEHAVIOR_TEST_VERTICAL", str(DEFAULT_VERTICAL))),
        help="Maximum generated child levels beneath the root.",
    )
    parser.add_argument(
        "--horizontal",
        type=int,
        default=int(_env_default("BEHAVIOR_TEST_HORIZONTAL", str(DEFAULT_HORIZONTAL))),
        help="Maximum root-level peer directions retained.",
    )
    parser.add_argument(
        "--progression",
        default=_env_default("BEHAVIOR_TEST_PROGRESSION", DEFAULT_PROGRESSION.value),
        choices=[item.value for item in ProgressionType],
        help="Vertical progression type for graph expansion.",
    )
    parser.add_argument(
        "--exploration",
        choices=["focused", "balanced", "rich"],
        default=_env_optional("BEHAVIOR_TEST_EXPLORATION"),
        help="Run adaptive exploration with the selected semantic profile.",
    )
    parser.add_argument(
        "--output",
        default=_env_optional("BEHAVIOR_TEST_OUTPUT"),
        help="Optional JSON path for the graph and behavior metrics.",
    )
    return parser


def resolve_config(argv: list[str] | None = None) -> RuntimeConfig:
    args = build_parser().parse_args(argv)
    return RuntimeConfig(
        topic=args.topic,
        provider=args.provider,
        model=args.model,
        vertical=args.vertical,
        horizontal=args.horizontal,
        progression_type=ProgressionType(args.progression),
        exploration=args.exploration,
        output=args.output,
    )


def _fake_response_sequence(topic: str, vertical: int, horizontal: int) -> list[str]:
    horizontal_payload = {
        "idea": topic,
        "thoughts": [
            {
                "thought": f"subtopic-{index + 1}",
                "description": f"Auto-generated subtopic {index + 1}",
            }
            for index in range(horizontal)
        ],
    }
    vertical_payload = {
        "idea": topic,
        "thought": "subtopic-1",
        "sub_thoughts": [
            {
                "name": f"detail-{index + 1}",
                "description": f"Auto-generated detail {index + 1}",
            }
            for index in range(7)
        ],
    }
    vertical_calls = 0
    nodes_at_level = horizontal
    for _ in range(1, vertical):
        vertical_calls += nodes_at_level
        nodes_at_level *= 7
    return [json.dumps(horizontal_payload)] + [json.dumps(vertical_payload)] * vertical_calls


def build_provider(config: RuntimeConfig):
    if config.provider == "fake":
        return FakeProvider(
            _fake_response_sequence(config.topic, config.vertical, config.horizontal)
        )
    return create_provider(config.provider)


def print_header(config: RuntimeConfig, resolved_model: str) -> None:
    print("Thought Graph Behavioral Test")
    print("=============================")
    print()
    print(f"Topic:        {config.topic}")
    print(f"Provider:     {config.provider}")
    print(f"Model:        {resolved_model}")
    if config.exploration:
        print(f"Exploration:  {config.exploration}")
    else:
        print(f"Vertical:     {config.vertical}")
        print(f"Horizontal:   {config.horizontal}")
    print(f"Progression:  {config.progression_type.value}")
    print()


def print_tree(node, *, prefix: str = "", is_last: bool = True, is_root: bool = False) -> None:
    if is_root:
        print(node.name)
        if node.description:
            for line in node.description.splitlines():
                print(f"    {line}")
        child_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{node.name}")
        if node.description:
            description_prefix = f"{prefix}{'    ' if is_last else '│   '}"
            for line in node.description.splitlines():
                print(f"{description_prefix}{line}")
        child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
    for index, child in enumerate(node.children):
        print_tree(child, prefix=child_prefix, is_last=index == len(node.children) - 1)


def main(argv: list[str] | None = None) -> None:
    """Run one public thought-graph generation and print it.

    Example:
        ```bash
        python examples/behavior_test.py --help
        ```
    """
    config = resolve_config(argv)
    provider = CountingProvider(build_provider(config))
    resolved_model = (
        config.model
        or (default_model(config.provider) if config.provider != "fake" else "example-model")
    )
    engine = ThoughtGraphEngine(
        provider=provider,
        model=resolved_model,
    )
    if config.exploration:
        graph = engine.generate_thought_graph(
            topic=config.topic,
            exploration=config.exploration,
            progression_type=config.progression_type,
        )
    else:
        graph = engine.generate_thought_graph(
            topic=config.topic,
            vertical=config.vertical,
            horizontal=config.horizontal,
            progression_type=config.progression_type,
        )

    def count_nodes(node):
        return 1 + sum(count_nodes(child) for child in node.children)

    def tree_data(node):
        return {
            "name": node.name,
            "description": node.description,
            "children": [tree_data(child) for child in node.children],
        }

    trace_reasons = {}
    for decision in engine.last_exploration_trace:
        reason = decision.reason.value
        trace_reasons[reason] = trace_reasons.get(reason, 0) + 1
    metrics = {
        "concept": config.topic,
        "profile": config.exploration,
        "provider": config.provider,
        "model": engine.model,
        "maximum_depth": engine._graph_depth(graph.root),
        "retained_nodes": count_nodes(graph.root) - 1,
        "expanded_nodes": sum(
            1
            for request in provider.requests
            if "vertically expanding one subtopic" in request.prompt
        ),
        "total_provider_calls": len(provider.requests),
        "decomposition_evaluation_calls": sum(
            1
            for request in provider.requests
            if "Decide whether each retained thought" in request.prompt
        ),
        "decomposition_terminal_count": trace_reasons.get("decomposition_terminal", 0),
        "decomposition_fallback_count": trace_reasons.get("decomposition_fallback", 0),
        "stop_reasons": trace_reasons,
        "decomposition_evidence": [
            {**record, "profile": config.exploration}
            for record in provider.decomposition_records
        ],
        "tree": tree_data(graph.root),
    }

    print_header(config, engine.model)
    print_tree(graph.root, is_root=True)
    print()
    print("Metrics:")
    print(json.dumps({key: value for key, value in metrics.items() if key != "tree"}, indent=2))
    if config.output:
        output_path = Path(config.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(f"Persisted:    {output_path}")


if __name__ == "__main__":
    main()
