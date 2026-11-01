# Storage

This package owns optional, caller-selected persistence contracts and the two
canonical repository implementations.

## Responsibilities

- `contracts.py`: generic `Repository` and thought-repository interfaces.
- `memory_repository.py`: ephemeral in-memory storage with copy-safe values.
- `json_repository.py`: explicit atomic JSON file persistence.

## Boundaries

Storage is not part of graph generation itself and is never selected or
written implicitly by the public convenience API. `ThoughtGraphEngine` accepts
an optional repository and exposes explicit saving; callers control repository
lifetime and location.

Storage does not call providers, generate thoughts, evaluate decomposition, or
own graph traversal. It is a leaf dependency for the engine and has no
dependency on interview/application code.
