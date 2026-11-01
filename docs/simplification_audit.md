# XF ThoughtGraph Simplification Audit

Status: implementation completed for the approved cleanup scope. This document
records the original findings and remains the rationale for the changes.

Completed decisions:

- Removed interview-era models, prompts, exports, tests, and dedicated
  documentation.
- Removed legacy graph parameter aliases and the unused repository/evaluator
  aliases.
- Removed `pandas` from the package and moved `pylint` to development
  dependencies.
- Removed confirmed dead imports and corrected the indirect parsing import.

This audit evaluates opportunities to reduce unnecessary code, duplication,
abstractions, tests, dependencies, and maintenance overhead while preserving
the public API, horizontal generation semantics, adaptive vertical
decomposition, evaluator-driven continuation, provider-specific behavior,
output schemas, and deterministic invariants.

## Baseline

- Source: 3,576 lines across `src/xf_thoughtgraph`.
- Tests: 2,547 lines across 11 Python test files.
- Test count: 161 collected tests.
- Latest full-suite result: `161 passed`.
- Largest source modules:
  - `thought_generation/engine.py`: 840 lines.
  - `thought_generation/adaptive_traversal.py`: 468 lines.
  - `thought_generation/adaptive_policy.py`: 213 lines.
  - `prompts/thought_generation_prompt_templates.py`: 171 lines.
  - `reflection/decomposition.py`: 141 lines.
- Largest test modules:
  - `tests/test_concept_first_api.py`: 1,249 lines.
  - `tests/test_provider_storage.py`: 397 lines.
  - `tests/test_adaptive_decomposition_integration.py`: 234 lines.
  - `tests/test_thought_generation_package.py`: 217 lines.

## Prioritized findings

### P0 — Remove clearly dead imports

Finding: three unused imports are confirmed by static analysis.

- Files:
  - `src/xf_thoughtgraph/providers/contracts.py`
  - `src/xf_thoughtgraph/thought_generation/engine.py`
  - `src/xf_thoughtgraph/thought_generation/ranking.py`
- Evidence:
  - Pylint reports unused `Any`.
  - Pylint reports unused `_ExplorationReason`.
  - Pylint reports unused `validate_idea`.
  - `ranking.py` also obtains `extract_json` indirectly through the validation
    module instead of importing it from `parsing.py`.
- Recommended action: delete the unused imports and make the parsing import
  direct.
- Estimated benefit: approximately 3–5 source lines and clearer dependencies.
- Risk: low.
- Public behavior change: no.

### P1 — Simplify dependency declarations

Finding: provider SDK dependencies are declared both as core dependencies and
as optional provider dependencies.

- Files: `pyproject.toml`, `uv.lock`.
- Evidence:
  - `anthropic` and `openai` appear in `[project].dependencies`.
  - The same packages appear in the `providers` optional extra.
  - Provider adapter modules are lazily imported; the core package can import
    without constructing or importing provider adapters.
- Recommended action: decide whether the documented optional-provider policy
  is authoritative. If so, move the SDKs exclusively to the `providers` extra
  and validate both core-only and provider-enabled installations.
- Estimated benefit: smaller core installations and clearer packaging; no
  meaningful source LOC reduction.
- Risk: medium, because existing users may rely on SDKs being installed by the
  base distribution.
- Public behavior change: yes for installation behavior.

### P1 — Move `pylint` out of runtime dependencies

Finding: `pylint` is a development tool but is currently a core dependency.

- Files: `pyproject.toml`, `uv.lock`.
- Evidence: `pylint` appears in `[project].dependencies`, while the project
  already has development dependency groups.
- Recommended action: move it to the development dependency group.
- Estimated benefit: smaller runtime installation and cleaner metadata.
- Risk: low.
- Public behavior change: no intended runtime change.

### P1 candidate — Decide the fate of interview-era compatibility surfaces

Finding: evaluation models and question-generation prompts remain exported by
the package even though graph generation does not use them internally.

- Files:
  - `src/xf_thoughtgraph/models/evaluation_models.py`
  - `src/xf_thoughtgraph/prompts/evaluation_prompt_templates.py`
  - `src/xf_thoughtgraph/models/llm_response_models.py`
- Evidence:
  - The graph runtime does not import these surfaces.
  - They remain exported from package `__init__.py` files and documented in
    `README.md`.
  - Package tests explicitly validate evaluation models and prompt exports.
- Recommended action: do not remove them immediately. First decide whether
  they are supported public compatibility contracts. If they are not, add a
  deprecation path before removal.
- Estimated benefit if eventually removed: approximately 200–230 source lines,
  plus possible removal of the `pandas` dependency.
- Risk: high.
- Public behavior change: yes.

### P1 candidate — Review generic response models and `pandas`

Finding: provider-neutral response models are mostly unused internally.

- File: `src/xf_thoughtgraph/models/llm_response_models.py`.
- Evidence:
  - `TextResponse`, `JSONResponse`, `TabularResponse`, and `CodeResponse`
    have no graph-runtime consumers.
  - `TabularResponse` is the only source use of `pandas`.
  - These models are nevertheless exported and documented.
- Recommended action: preserve them until the public API decision above is
  made. If compatibility is not required, move them to a compatibility module
  or remove them only in an explicitly breaking release.
- Estimated benefit: approximately 35 source lines and removal of `pandas` if
  no other public model requires it.
- Risk: high.
- Public behavior change: yes.

### P2 — Avoid resetting adaptive counters in explicit mode

Finding: explicit fixed-width graph generation calls adaptive-run state reset
logic even though adaptive counters are not used by that path.

- Files:
  - `src/xf_thoughtgraph/thought_generation/engine.py`
  - `src/xf_thoughtgraph/thought_generation/adaptive_traversal.py`
- Evidence: `generate_thought_graph()` calls `_start_adaptive_run()` in both
  adaptive and explicit branches. The explicit branch uses neither adaptive
  provider-call accounting nor adaptive node/expansion accounting.
- Recommended action: remove the explicit-mode reset only after confirming
  that no supported diagnostic behavior depends on private counters between
  calls.
- Estimated benefit: approximately 4 source lines and slightly clearer mode
  separation.
- Risk: low to medium.
- Public behavior change: no intended change.

### P2 — Consolidate small test helpers

Finding: several tests repeat fake-provider scaffolding and tree-depth helper
functions.

- Files:
  - `tests/test_concept_first_api.py`
  - `tests/test_thought_generation_package.py`
  - `tests/test_reflection_decomposition.py`
  - `tests/test_adaptive_decomposition_integration.py`
- Evidence: multiple local `FakeProvider` or provider stub classes and repeated
  `leaf_depth()`-style helpers exist.
- Recommended action: consolidate only small, stable helpers into test support
  code. Retain all tests and their distinct fixtures.
- Estimated benefit: approximately 20–40 test lines.
- Risk: low.
- Public behavior change: no.

### P2 candidate — Review the size of the engine façade

Finding: `ThoughtGraphEngine` combines typed low-level APIs, concept-first
wrappers, legacy bounds, explicit graph generation, and adaptive dispatch.

- File: `src/xf_thoughtgraph/thought_generation/engine.py` — 840 lines.
- Evidence: the module contains both the public compatibility façade and the
  bounded graph path, while adaptive behavior lives in an adjacent mixin.
- Recommended action: do not split the module automatically. If maintenance
  becomes difficult, extract only clearly independent validation or request
  normalization helpers and preserve the façade class and method contracts.
- Estimated benefit: potentially 50–100 lines of local complexity, but no
  guaranteed net reduction.
- Risk: medium to high.
- Public behavior change: none intended, but regression risk is significant.

### P2 candidate — Review repeated provider adapter flow

Finding: synchronous and asynchronous provider adapters repeat setup,
request, and exception-translation patterns.

- Files:
  - `providers/openai.py`
  - `providers/gemini.py`
  - `providers/deepseek.py`
  - `providers/anthropic.py`
- Evidence: OpenAI-compatible client creation, request translation, response
  normalization, and exception handling repeat across adapters. Existing shared
  plumbing already covers client construction and response parsing.
- Recommended action: retain provider-specific classes. Consider a narrow
  internal helper only if more compatible providers are added or the repeated
  code becomes a demonstrated maintenance problem.
- Estimated benefit: potentially 40–80 source lines.
- Risk: medium.
- Public behavior change: none intended.

## Protected complexity

### Adaptive policy and evaluator continuation

The adaptive path contains distinct gates rather than duplicate continuation
implementations:

1. lexical novelty filtering;
2. root and ancestor relevance filtering;
3. marginal-value filtering;
4. natural-endpoint detection;
5. evaluator-driven decomposition decisions;
6. provider, node, expansion, and depth safety limits;
7. fallback behavior and exploration trace recording.

These should remain separate. Removing the deterministic filters would change
provider-call volume and graph shape, while removing evaluator decisions would
violate the evaluator-driven continuation contract.

### Fixed-width generation

The fixed-width path is not obsolete merely because adaptive generation exists.
It protects deterministic provider-call behavior, legacy `depth`/`breadth`
compatibility, independent `horizontal`/`vertical` semantics, ranking behavior,
and stable graph metadata.

### Provider differences

The shared OpenAI-compatible infrastructure is already appropriately factored.
DeepSeek's thinking metadata and Anthropic's separate API are meaningful
provider-specific behavior and should not be hidden behind a broad generic
abstraction.

### Tests and documentation

`tests/test_concept_first_api.py` is large, but its tests cover distinct
contracts: legacy bounds, new bounds, adaptive profiles, safety budgets,
semantic stops, provider-call behavior, serialization, and aliases. There is
not enough evidence to delete tests based only on overlapping filenames.

Historical audits, validation reports, and architecture records contain unique
evidence and should not be deleted merely because newer implementation paths
exist.

## Recommended implementation sequence

1. Remove the confirmed unused imports and make parsing imports direct.
2. Decide the supported-install policy for provider SDKs.
3. Move `pylint` to development dependencies and, if approved, move provider
   SDKs exclusively to the provider extra.
4. Validate core-only installation, provider-extra installation, package
   imports, and the full test suite.
5. Consolidate only repeated test helpers.
6. Decide whether compatibility models and prompts are supported public API;
   deprecate before removing anything.
7. Leave adaptive traversal, evaluator decisions, fixed-width generation, and
   provider-specific adapters unchanged unless later evidence justifies a
   narrowly scoped refactor.

The highest-value low-risk cleanup is therefore small: remove unused imports,
correct dependency metadata, and optionally consolidate test helpers. The
larger apparent opportunities involve public compatibility surfaces and should
not be removed implicitly.
