# Reflection

This package owns reflection that is part of reusable thought-graph
generation.

## Responsibilities

- `decomposition.py`: batch evaluation of retained candidates for the semantic
  question of whether another vertical level is worthwhile.
- `shared.py`: provider invocation, JSON extraction, typed validation, and
  normalized malformed-response handling shared by reflection services.

The decomposition contract preserves stable candidate IDs, ancestor context,
exploration profiles, and decision reasons. The evaluator returns decisions;
`ThoughtGraphEngine` remains responsible for retention, recursion, terminal
nodes, safety guards, and fallback behavior.

## Boundaries

Reflection does not generate children, traverse graphs, define graph models,
or implement interview answer evaluation/policy. It depends on provider
contracts and the generation package's JSON extraction helper. Core graph
generation depends on this package directly and does not depend on an
interview namespace.
