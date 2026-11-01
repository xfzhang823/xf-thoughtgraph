# Thought generation

This package owns the canonical synchronous generation and traversal path for concept-first thought graphs.

## Responsibilities

- `ThoughtGraphEngine`: provider-backed horizontal generation, vertical expansion, adaptive exploration, traversal, and graph assembly.
- `generation.py` and `expansion.py`: provider request construction and response-to-model conversion.
- `ranking.py`: optional clustering and ranking of generated ideas.
- `validation.py`, `parsing.py`, and `indexing.py`: deterministic response handling and graph/index helpers.
- `reader.py`: typed readers for generated thought models.
- `requests.py`: typed horizontal and vertical generation request contracts.
- `adaptive_policy.py`: deterministic lexical/profile policy helpers used by
  adaptive traversal.
- `adaptive_traversal.py`: stateful adaptive graph traversal, safety accounting,
  and exploration trace recording.

## Boundaries

This package does not own provider SDK adapters, domain models, prompt constants, persistence implementations, or interview/application workflows.
It orchestrates those package-level contracts; callers should use the root `generate_thought_graph()` function for the normal workflow and this package's
`ThoughtGraphEngine` for advanced controls.

Dependencies point to `models`, `prompts`, `providers`, `storage`, and the core decomposition capability in `reflection`. Generation behavior and traversal remain here; reflection makes the decomposition decision but does not recurse through the graph.
