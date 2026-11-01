# Models

This package owns the typed domain and provider-neutral response models used
by the canonical graph package.

## Responsibilities

- `thought_models.py`: concept-first `Thought`, `ThoughtArray`, `ThoughtNode`,
  and `ThoughtGraph` models plus progression types.
- `indexed_thought_models.py`: indexed thought structures consumed by the
  canonical engine.

The package-level `__init__.py` exposes the supported model exports from one
stable subpackage boundary.

## Boundaries

Models validate and represent data; they do not call providers, build prompts,
traverse graphs, perform reflection, or persist results. Generation, reflection,
provider, prompt, and storage packages may depend on these types, but models
do not depend on the removed interview/application architecture.
