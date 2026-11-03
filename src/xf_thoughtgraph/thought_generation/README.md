# Thought generation

This package owns the canonical synchronous generation and traversal path for concept-first thought graphs. It also exposes the compatibility idea-model façade used for horizontal thought arrays, one-shot vertical expansion, deterministic indexing, provider-mediated cluster selection, and in-memory readers.

## Entry points

- `generate_thought_graph()` in the package root: the normal workflow. It always uses adaptive exploration, requires an explicit provider, and accepts optional `max_calls` and `max_nodes` adaptive budgets.
- `ThoughtGraphEngine`: advanced façade for explicit graph bounds, adaptive profiles, typed requests, expansion, indexing, readers, and explicit saving.
- `HorizontalGenerationRequest` and `VerticalGenerationRequest`: typed configuration for direct horizontal and vertical calls.
- `extract_json`, `parse_idea`, `parse_thought`, `validate_idea`, `validate_indexed_idea`, and `index_idea`: deterministic helpers.

```python
from xf_thoughtgraph import ThoughtGraphEngine

engine = ThoughtGraphEngine("deepseek")
graph = engine.generate_thought_graph(
    "clinical research participant recruitment",
    horizontal=5,
    vertical=3,
)
```

The same engine can run adaptive exploration by omitting both bounds:

```python
graph = engine.generate_thought_graph(
    "clinical research participant recruitment",
    exploration="balanced",
    max_calls=24,
    max_nodes=40,
)
print(graph.exploration_summary)
```

## Operating model

Two mutually exclusive modes shape `generate_thought_graph()`:

- **Explicit bounds.** Supplying `horizontal` or `vertical` selects a bounded graph. Defaults are breadth 6 and depth 2. Depth must be at most `MAX_FACADE_DEPTH` (8). Explicit vertical expansion uses an internal child cap of 7 that is independent of `horizontal`.
- **Adaptive exploration.** Supplying neither bound selects adaptive mode; `exploration` defaults to `"balanced"`. The profiles `"focused"`, `"balanced"`, and `"rich"` change continuation thresholds but not fixed graph sizes. Passing `exploration` together with either bound raises `ValueError`, and `max_calls`/`max_nodes` are valid only in adaptive mode.

Adaptive traversal uses a breadth-first frontier: root directions are expanded level by level, so a deep early branch cannot block later root branches. It retains at most 8 root directions, caps adaptive vertical responses at 16 retained children per node as a safety limit (the prompt asks for the natural set, not a target), and stops at depth 8. The internal ceilings are 64 provider calls, 128 retained nodes (including the root), and 64 expansion attempts. Optional `max_calls=` and `max_nodes=` budgets may lower the first two ceilings but cannot exceed them.

A safety stop is sticky within a run and is recorded in `last_exploration_trace`. The active profile is available as `last_exploration_profile`. A completed adaptive run exposes its accounting as `ThoughtGraph.exploration_summary` and `last_exploration_summary`, including actual calls, retained nodes, expansion attempts, configured budgets, completion, and stop reason.

`vertical=1` returns the root plus its first horizontal layer. Each expanded node below that consumes one vertical provider call. In explicit mode, `ranked=True` adds one clustering call and affects only the first-level horizontal subtopics. Adaptive mode ignores `ranked`; horizontal probing always runs unranked. Adaptive runs also spend provider-call budget on decomposition-evaluation calls.

All generation remains in memory. Persistence is opt-in through `save()`, which raises `RuntimeError` when no repository was supplied. The engine never persists implicitly.

Provider, parsing, and validation failures raise. If adaptive decomposition evaluation fails, decisions default to decompose. If the provider-call budget is exhausted while evaluating, the safety stop halts traversal and remaining candidates stay retained as leaves. A provider name resolves through `create_provider()` and `default_model()`; an injected `LLMProvider` defaults its model to `"default"` unless one is supplied.

## Module structure

The package is flat; the tree below shows the file layout and primary role of each module.

```text
thought_generation/
├── README.md                # this document
├── __init__.py              # public package exports
├── engine.py                # ThoughtGraphEngine and explicit graph path
├── requests.py              # typed horizontal and vertical request contracts
├── generation.py            # provider-backed horizontal generation
├── expansion.py             # provider-backed vertical expansion
├── ranking.py               # provider-mediated cluster selection/conversion
├── validation.py            # schema validation and parse entry points
├── parsing.py               # tolerant JSON extraction
├── indexing.py              # deterministic zero-based index assignment
├── reader.py                # in-memory validating idea readers
├── adaptive_policy.py       # deterministic adaptive policy helpers
└── adaptive_traversal.py    # breadth-first adaptive traversal and accounting
```

## Responsibilities

- `engine.py`: the public `ThoughtGraphEngine` façade, which inherits `AdaptiveTraversalMixin` and dispatches between explicit and adaptive generation; it owns the typed `generate()`/`expand()`/`expand_all()` request API, the convenience `generate_subtopics()`/`expand_subtopic()`/`generate_array_of_thoughts()` methods, bounded explicit graph construction and metadata, provider/model resolution, argument and adaptive-budget validation, indexing, and explicit `save()` persistence.
- `adaptive_traversal.py`: `AdaptiveTraversalMixin`, the default adaptive execution path; it runs breadth-first frontier traversal across retained root directions, probes horizontal candidates, expands eligible nodes vertically with the deterministic `adaptive_policy` filters, batches children through `reflection.DecompositionEvaluationService`, enforces the depth ceiling and provider-call/node/expansion budgets, falls back to decompose when evaluation fails, and records `_ExplorationDecision` traces plus the final `AdaptiveExplorationSummary` with stop reason and accounting.
- `adaptive_policy.py`: deterministic lexical and profile policy helpers used by adaptive traversal.
- `generation.py` and `expansion.py`: provider request construction, prompt formatting and defaulting, and response-to-model conversion.
- `ranking.py`: provider-mediated cluster selection plus deterministic cluster-to-idea conversion. The model performs ranking; this module validates the response and converts clusters.
- `validation.py`, `parsing.py`, and `indexing.py`: deterministic response parsing, schema validation, and zero-based index assignment.
- `reader.py`: in-memory validating readers for `IdeaJSONModel` and `IndexedIdeaJSONModel`; no filesystem access and no `ThoughtGraph` traversal.
- `requests.py`: typed horizontal and vertical generation request contracts.

## Boundaries

This package does not own provider SDK adapters, domain models, prompt constants, persistence implementations, or interview/application workflows. It orchestrates those package-level contracts; callers should use the root `generate_thought_graph()` function for the normal workflow and this package's `ThoughtGraphEngine` for advanced controls.

Dependencies point to `models`, `prompts`, `providers`, `storage`, and the core decomposition capability in `reflection`. Generation behavior and traversal remain here; reflection makes the decomposition decision but does not recurse through the graph.

## Known limitations

- Adaptive vertical responses are truncated to 16 retained children per node. This is a safety ceiling; the prompt asks for the natural set, not that target.
- Decomposition-evaluation failures degrade toward more expansion, not less.
- `parsing.py` intentionally tolerates provider noise: it strips `//` comments and trailing commas before decoding JSON.
- The readers validate idea hierarchies; they do not read or traverse a `ThoughtGraph`.

## Related docs

- `docs/public_api.md`: consumer-facing workflow, provider defaults, budgets, and graph semantics.
- `docs/thought_generation/adaptive_exploration_audit.md`: reference audit and rationale for the breadth-first frontier and budget reporting.
- `docs/thought_generation/adaptive_decomposition_validation_report.md`: decomposition evaluation validation.
- `tests/test_thought_generation_package.py` and `tests/test_adaptive_decomposition_integration.py`: behavioral coverage.
