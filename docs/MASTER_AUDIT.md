# Master Audit — bot0-thought-graph

> Historical audit record. References to `bot0-thought-graph` and
> `bot0_thought_graph` below describe the repository state at the time of the
> audit and are intentionally preserved. The current project identity is
> `XF ThoughtGraph` / `xf-thoughtgraph` / `xf_thoughtgraph`.

## Executive Summary

`bot0-thought-graph` is a standalone reusable package at version v0.1.0 using a `src/` layout (`src/bot0_thought_graph/`). The package contains the reusable deterministic models and prompts, provider-neutral contracts and lazy SDK adapters, optional storage, the thought-generation engine, the headless interview engine, and thin orchestration. Legacy `agents`, `pipelines`, `utils`, `project_config`, `input_output`, frontend, VoiceAssist, FastAPI, and terminal code remain outside the package boundary.

Key strengths: no imports from legacy application code; typed, provider-neutral contracts with lazy SDK adapters; optional persistence requiring an injected repository; a headless, typed interview engine; and a unified `ProgressionType(str, Enum)` progression system shared by the lower-level API and the public façade. The three source audits (migration, behavioral test, vertical progression) are consolidated here in full; their content is preserved verbatim with coordinator notes added where the code state has moved on.

## Last Updated

2026-08-08

## 1. Migration Audit

> Note (2026-08-08): Source file `docs/migration_audit.md` (28 lines), preserved in full below with section headings promoted by one level. Coordinator note: the "Remaining technical debt" item about class-based `Config` deprecation warnings is now stale — the pydantic `ConfigDict` migration completed on 2026-08-07 and zero `class Config:` blocks remain in `src/bot0_thought_graph` (verified by grep on 2026-08-08).

### Final package boundary

`src/bot0_thought_graph/` now contains the reusable deterministic models and prompts, provider-neutral contracts and lazy SDK adapters, optional storage, thought-generation engine, headless interview engine, and thin orchestration. It has no imports from legacy `agents`, `pipelines`, `utils`, `project_config`, `input_output`, frontend, VoiceAssist, FastAPI, or terminal code.

### Intentional semantic differences

- Thought-engine clustering is explicit through request options.
- Interview processing is typed and headless rather than console-driven.
- The migrated interview engine is synchronous.
- Persistence is optional and requires an injected repository plus an explicit save call.
- Legacy facilitator retries and file-backed conversation logging are not included.

### Retained legacy surfaces

Legacy agents, pipelines, utilities, project configuration, root services, generated data, frontend, experiments, backups, and binaries remain outside the package. The former VoiceAssist prototype was extracted to the separate `voice-assist` repository. These surfaces are application/deployment code or deferred behavior with unresolved coupling. The legacy topic-exhaustion module is now a compatibility shim to the package policy.

### Remaining technical debt

- The legacy test suite still contains application-specific tests with path mutation and hard-coded Windows fixtures; those are not package tests.
- Migrated Pydantic models emit existing class-based `Config` deprecation warnings.

> Note (2026-08-08): the previous bullet is now resolved — the pydantic `ConfigDict` migration was completed on 2026-08-07 and no `class Config:` blocks remain under `src/bot0_thought_graph` (verified by grep, 2026-08-08). The original text is kept for historical accuracy.

- Historical generated data remains in this repository where previously tracked; VoiceAssist assets now live in the separate `voice-assist` repository and are outside this package.
- Provider adapters require the optional `providers` extra; custom/fake providers require no SDK adapter import.

> Note (2026-08-08): the provider adapter set now includes OpenAI, Anthropic, Gemini, and DeepSeek (OpenAI-compatible) plus the `openai_compatible` helper module; the Gemini/DeepSeek adapters were added in commit `36914401` ("Add OpenAI-compatible Gemini and DeepSeek providers").

### Readiness

The package is ready to serve as a standalone reusable package for its migrated scope. Application integrations and deferred legacy behavior require separate migration work.

## 2. Behavioral Audit

> Note (2026-08-08): Source file `docs/behavioral_test_audit.md` (99 lines), preserved in full below. Commit-hash check (performed 2026-08-08): the cited commit `36914401aed44291ddad31652a99e1870848ed28` DOES exist in repository history (`git log -1 36914401...` resolves to it — "Add OpenAI-compatible Gemini and DeepSeek providers"); it is not HEAD. Current HEAD is `08caa9cd05e622e6435957a6f6e72efc44fc6431` (6 commits later: "added a progression type and removed direct_child"). The audit's live-run result fields were still placeholders at consolidation time.

Date: 2026-08-07

Git branch: `main`

Git commit hash: `36914401aed44291ddad31652a99e1870848ed28`

Provider implementation: `OpenAIProvider` from `src/bot0_thought_graph/providers/openai.py`

Selected model: `gpt-5-mini-2025-08-07`

Relevant API/configuration path:

`OPENAI_API_KEY` -> `bot0_thought_graph._env.load_repository_env()` -> `bot0_thought_graph.providers.build_sync_client()` -> `OpenAIProvider()` -> `ThoughtGraphEngine(provider, model=MODEL)` -> `generate_array_of_thoughts(...)` / `expand_subtopic(...)`

Test concept: `Clinical research recruitment`

Methods being tested:

- `ThoughtGraphEngine.generate_array_of_thoughts("Clinical research recruitment", max_subtopics=6)`
- `ThoughtGraphEngine.expand_subtopic(concept="Clinical research recruitment", subtopic=<selected>, max_details=6)`

Behavioral expectations:

Horizontal behavior:

- sibling consistency
- distinctness
- coverage
- concept relevance
- granularity consistency

Vertical direct-child behavior:

- parent-child relationship
- specificity
- scope control
- distinctness
- granularity consistency

Scoring rubric:

- 0 = failure
- 1 = partially satisfactory
- 2 = satisfactory

Targets:

- Horizontal: `>= 8/10`
- Vertical: `>= 8/10`

Failure categories to track:

- mixed abstraction levels
- sibling overlap
- horizontal item is actually a task
- vertical child belongs to another branch
- parent repeated as child
- near-duplicate thoughts
- concept drift
- missing major dimension
- uneven granularity

Raw horizontal output:

<!-- populate after live run -->

Horizontal score:

<!-- populate after live run -->

Horizontal failure observations:

<!-- populate after live run -->

Selected vertical parent:

<!-- populate after live run -->

Raw vertical output:

<!-- populate after live run -->

Vertical score:

<!-- populate after live run -->

Vertical failure observations:

<!-- populate after live run -->

Overall conclusion:

<!-- populate after live run -->

Follow-up action:

<!-- populate after live run -->

## 3. Vertical Progression Audit

> Note (2026-08-08): Source file `docs/vertical_progression_audit.md` (329 lines), preserved in full below; section headings promoted by one level. Enum-match check (performed 2026-08-08): the current `ProgressionType(str, Enum)` in `src/bot0_thought_graph/models/thought_models.py` (lines 12-19) has EXACTLY the five members the document describes — `implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, `prerequisite_dependency` — so the document matches the code. The enum is exported from the models package and the package root, and is used as the typed default `ProgressionType.IMPLEMENTATION_STEPS` in `expansion.py` and in `VerticalGenerationRequest` / `generate_thought_graph` in `engine.py`. Also note: `docs/vertical_progression_audit.md` itself has uncommitted working-tree changes (the version consolidated here is the current working-tree version; HEAD still contains the older pre-enum revision).

### 1. Executive Summary

The current implementation has five progression types, represented by the public `ProgressionType(str, Enum)`:

1. `implementation_steps`
2. `simple_to_complex`
3. `chronological`
4. `problem_solution`
5. `prerequisite_dependency`

`implementation_steps` is the explicit default for lower-level expansion, `expand_subtopic()`, and recursive `generate_thought_graph()` expansion. Raw strings remain accepted at public boundaries and are normalized to the enum. The former generic child-expansion label has been removed.

The main current limitation is semantic rather than type-related: all modes are represented as ordinary `ThoughtNode.children` edges, so sequence, procedure, problem-solution, and prerequisite relationships are not preserved as edge metadata.

### 2. Current Progression Types in the Repository

#### `implementation_steps`

Exact value: `"implementation_steps"`.

This is the default for `VerticalGenerationRequest`, `expand_vertical()`, `expand_idea()`, `expand_all()`, `expand_subtopic()`, and `generate_thought_graph()`. The prompt asks for implementation-oriented key areas or steps. The direction is parent thought -> implementation areas or steps, but strict ordering and prerequisite semantics are not guaranteed.

It is workflow- and implementation-oriented, and is reachable through both the lower-level API and the public façade. Its value is interpolated into the vertical prompt and is not stored in the result models.

#### `simple_to_complex`

Exact value: `"simple_to_complex"`.

The prompt asks the model to start with basic concepts and gradually introduce more advanced ideas. Its direction is lower conceptual complexity -> higher conceptual complexity. It is primarily conceptual and explanatory. It is accepted by the enum and public generation methods, but it does not create a typed complexity edge in the graph.

#### `chronological`

Exact value: `"chronological"`.

The prompt asks for evolution or historical development. Its direction is earlier state/event -> later state/event, although strict next-step workflow ordering is not validated. It is temporal and useful for lifecycle analysis.

#### `problem_solution`

Exact value: `"problem_solution"`.

The prompt asks for problems or challenges followed by solutions or approaches. The intended direction is problem -> solution, but the prompt does not guarantee that every generated child is a solution or distinguish causes, analysis, and remediation steps.

#### `prerequisite_dependency`

Exact value: `"prerequisite_dependency"`.

The prompt requires strict, directional prerequisites or dependencies: a child must be satisfied, completed, or understood before the parent thought can proceed. This is the clearest current mode for prerequisite-oriented workflow analysis, although the output graph still stores the relationship as a generic child edge.

### 3. Current Code Locations and Call Paths

The enum is defined in:

```text
src/bot0_thought_graph/models/thought_models.py
```

It is exported from the package root, models package, and thought-generation package. The primary call paths are:

```text
ThoughtGraphEngine.expand(VerticalGenerationRequest)
    -> expansion.expand_vertical()
    -> normalize ProgressionType
    -> VERTICAL_SUB_THOUGHT_GENERATION_PROMPT.format(..., progression_type=value)
    -> provider.generate()
    -> parse_thought()
```

```text
ThoughtGraphEngine.expand_all()
    -> expansion.expand_idea()
    -> expansion.expand_vertical() for each thought
```

```text
ThoughtGraphEngine.generate_thought_graph()
    -> horizontal generation for the first-level children
    -> _expand_graph_node() recursively
    -> _expand_subtopic_result()
    -> VerticalGenerationRequest(..., progression_type=selected enum)
    -> expansion.expand_vertical()
    -> CONCEPT_DETAIL_GENERATION_PROMPT
    -> provider.generate()
    -> parse_thought()
    -> ThoughtNode children
```

`ProgressionType(value)` normalization occurs in the request dataclass and at the relevant method/function boundaries. Invalid values raise `ValueError`.

### 4. Current Semantic Behavior

The lower-level and public façade paths now use the same typed progression contract and the selected value reaches prompt construction. The public detail prompt retains implementation-step wording by default and adds explicit prerequisite guidance when `prerequisite_dependency` is selected.

The implementation does not validate the semantic relationship of provider output. It validates JSON shape and constructs package-owned models, but it does not prove that generated children are chronological, causal, or required prerequisites.

### 5. Current Type Comparison

| Current type | Meaning | Direction | Publicly selectable? | Workflow relevance | Main limitation |
| --- | --- | --- | --- | --- | --- |
| `implementation_steps` | Implementation areas or steps | Parent -> implementation area/step | Yes; default | High | Order and prerequisites are not guaranteed |
| `simple_to_complex` | Basic concepts to advanced concepts | Less complex -> more complex | Yes | Moderate | Conceptual progression is not necessarily a process edge |
| `chronological` | Evolution or historical development | Earlier -> later | Yes | High | History is not always an actionable next-step sequence |
| `problem_solution` | Challenges followed by solutions/approaches | Problem -> possible solution | Yes | High | Causes, analysis, and remediation are not separated |
| `prerequisite_dependency` | Strict prerequisites/dependencies | Required condition -> dependent work/parent | Yes | High | Edge direction is not stored separately in the graph |

### 6. Public Façade vs Lower-Level Progression System

The earlier split between a lower-level progression selector and a generic public child-expansion mode has been removed. `expand_subtopic()` and recursive graph expansion now use the same enum and prompt pathway as lower-level vertical generation.

The façade defaults explicitly to `ProgressionType.IMPLEMENTATION_STEPS`, so omitted values no longer depend on an unnamed or generic mode. Callers may select another enum member or pass its string value.

### 7. Workflow Requirements Analysis

- `implementation_steps` answers “How is this carried out?” and is the best default for implementation and requirements discovery.
- `chronological` answers “What happens next?” but should not be treated as a validated process ordering.
- `problem_solution` supports incident, remediation, and requirements-gap analysis, but does not guarantee a strict problem-to-resolution chain.
- `prerequisite_dependency` answers “What must be satisfied before this can proceed?” and is the strongest mode for dependency discovery.
- `simple_to_complex` helps elaborate a workflow from an overview toward more detailed concepts, but does not represent execution order.

Together these modes support basic workflow discovery across business, clinical, operational, manufacturing, software incident, and requirements contexts. They do not model branching, parallelism, joins, or typed edge provenance.

### 8. Semantic Overlap and Ambiguity

#### `implementation_steps` vs `chronological`

Implementation steps may be ordered in practice, but the current prompt asks for implementation areas or steps without requiring “after” relationships. `chronological` explicitly concerns evolution or history. They overlap for sequential processes but are not equivalent.

#### `simple_to_complex` vs `implementation_steps`

Both can add detail. `simple_to_complex` orders concepts by explanatory complexity, while `implementation_steps` organizes work or implementation areas. Neither guarantees a constituent-part hierarchy.

#### `problem_solution` directionality

The intended direction is problem -> solution, but the prompt allows a mixture of challenges, analysis, and approaches. Behavioral evaluation is needed if a strict transition is required.

#### `prerequisite_dependency` vs `chronological`

Prerequisites are conditions for proceeding; chronological steps are events in time. A prerequisite can occur earlier, but not every earlier event is required. These should remain distinct.

### 9. Current Graph-Edge Semantics

`ThoughtGraph` stores relationships as untyped `ThoughtNode.children` edges. It does not store the selected progression type on `Thought`, `ThoughtNode`, or `ThoughtGraph`, and it does not distinguish procedural, temporal, problem-solution, or prerequisite edges.

This is acceptable for a generic generated tree, but consumers must not infer that every edge means decomposition. If provenance or graph analysis becomes a requirement, graph-level progression metadata or typed edges should be considered in a separate change.

### 10. Gaps in the Existing Progression Set

The current set now explicitly includes prerequisite/dependency semantics. A strict causal mode remains a possible gap: `problem_solution` does not guarantee causality, and `chronological` does not imply causality.

Other possible future relationships—evidence, diagnostic reasoning, and goal-means—would likely require additional role or provenance semantics rather than only another label. Contrast is generally better modeled horizontally.

### 11. Possible Future Normalization

Everything in this section is **PROPOSED / NOT IMPLEMENTED**.

| Proposed name | Relationship to current type | Possible treatment |
| --- | --- | --- |
| `temporal` | Clearer alternative to `chronological` | Alias only if strict process time is intended |
| `implementation` | Shorter form of `implementation_steps` | Optional future alias |
| `decomposition` | Could describe constituent-part generation | New semantic mode only if required |
| `refinement` | Could describe narrower/more-specific generation | New semantic mode only if required |
| `causal` | Not guaranteed by any current mode | Add only for directional effects |
| `abstraction` | Broader/generalization movement | Likely a separate upward operation |
| `goal_means` | Partially overlaps implementation steps | Possibly application-specific |
| `evidence` | Not represented by current modes | Requires provenance/argument support |
| `diagnostic` | Partially overlaps problem-solution | Specialized reasoning mode |
| `contrast` | Alternative or opposing views | Better modeled horizontally |

No normalization should silently rename or remove the five current enum values.

### 12. Backward Compatibility

The five current enum values remain available. Existing callers may pass either enum members or equivalent strings, for example:

```python
from bot0_thought_graph import ProgressionType, ThoughtGraphEngine

engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    depth=2,
    breadth=5,
    progression_type=ProgressionType.PREREQUISITE_DEPENDENCY,
)

engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    depth=2,
    breadth=5,
    progression_type="prerequisite_dependency",
)
```

When omitted, the façade uses the explicit `ProgressionType.IMPLEMENTATION_STEPS` default. Invalid strings fail clearly with `ValueError` instead of silently selecting a different mode.

### 13. Public API Recommendation

The canonical façade shape is:

```python
graph = engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    depth=3,
    breadth=5,
    progression_type=ProgressionType.IMPLEMENTATION_STEPS,
)
```

The API should continue accepting strings for convenience while documenting the enum as the preferred typed form. All five modes can currently be passed through the same provider-independent graph path, with the limitation that the result remains an untyped tree.

### 14. Prompt Architecture Implications

The shared prompt layer receives `progression_type.value`, so prompt text is provider-independent. The lower-level and façade vertical prompts both receive the normalized value. The prerequisite prompt guidance explicitly requires strict directional dependencies.

Future prompt work should keep one central progression-instruction mapping and avoid provider-specific progression implementations. Prompt guidance should remain short, directional, and behaviorally testable.

### 15. Testing Gaps

Current deterministic tests cover:

- enum defaulting and raw-string normalization;
- invalid progression values;
- prerequisite prompt guidance;
- graph propagation of the explicit implementation-step default; and
- graph propagation of an explicitly selected prerequisite mode.

Future behavioral tests should evaluate relationships rather than exact model strings:

- implementation steps: actionable implementation areas;
- simple to complex: increasing conceptual complexity;
- chronological: defensible temporal ordering;
- problem solution: distinguishable problem and solution roles; and
- prerequisite dependency: strict required-before relationships.

### 16. Recommended Next Step

Keep the current five enum-backed modes stable. If workflow consumers need stronger guarantees, the next focused design change should define graph-edge metadata or a provenance field rather than adding more loosely defined labels.

### 17. Final Recommendation

- Keep all five current values unchanged.
- Use `ProgressionType.IMPLEMENTATION_STEPS` as the explicit default.
- Prefer enum members for typed callers while preserving string compatibility.
- Keep progression semantics provider-independent and prompt-driven.
- Treat graph edges as generic unless progression metadata is added explicitly.
- Defer new modes such as `causal`, `evidence`, and `diagnostic` until a concrete use case and behavioral contract are defined.

No production functionality was changed by this documentation update.

## 4. Drift Detection

> Note (2026-08-08): every item below was re-verified against the repository on 2026-08-08 before being written. Items marked "[Coordinator note]" flag facts that changed since the coordinator's earlier same-day verification.

- `ProgressionType` is now implemented in code. The enum `ProgressionType(str, Enum)` exists at `src/bot0_thought_graph/models/thought_models.py:12-19` with exactly the five members the vertical audit describes (`implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, `prerequisite_dependency`). It is exported from `src/bot0_thought_graph/models/__init__.py` (lines 21, 31) and the package root `src/bot0_thought_graph/__init__.py` (lines 4, 17), and it is the typed default `ProgressionType.IMPLEMENTATION_STEPS` in `src/bot0_thought_graph/thought_generation/expansion.py` (lines 16, 49) and in `VerticalGenerationRequest` and graph methods in `src/bot0_thought_graph/thought_generation/engine.py` (lines 94, 271, 386, 493, 647). The vertical audit therefore matches the code; the doc is no longer aspirational.
- `repro_interview.py` was an untracked debug artifact at the repository root (90 lines) containing three labeled checks: "BUG A" (follow-up conversation logs ordered questions-then-answers), "BUG B" (exhaustion on the LAST sub-thought never completing), and "BUG C" (exhaustion policy keyword leak across sessions). All three were confirmed and subsequently FIXED on 2026-08-10 (`interview/engine.py`: chronologically interleaved logs, session completion when exhausted with no remaining topic, per-session policy reset); the artifact was then deleted and the fixes are covered by three regression tests in `tests/test_interview_orchestration.py` (8 tests pass). (refreshed 2026-08-10)
- `_DEFAULT_MODELS` and `default_model(provider)` exist in `src/bot0_thought_graph/providers/__init__.py` (lines 31-36, 67-77): per-provider defaults `gpt-5.6-luna` (openai), `gemini-3.6-flash` (gemini), `deepseek-v4-flash` (deepseek), `claude-3-5-sonnet-20241022` (anthropic), with a `<PROVIDER>_MODEL` environment variable taking precedence. (refreshed 2026-08-10)
- `ThoughtGraphEngine` now accepts a provider NAME string (`provider: LLMProvider | str`, engine.py ~line 141): named providers are resolved through `providers.create_provider`, and `model=None` resolves the per-provider default via `default_model()`. (refreshed 2026-08-10)
- `generate_thought_graph()` now takes `topic=` as the canonical root-concept parameter with the legacy `concept=` retained as an alias (only one may be supplied), and both `expand_subtopic()` and `generate_thought_graph()` accept `progression_type=` (default `ProgressionType.IMPLEMENTATION_STEPS`). (refreshed 2026-08-10)
- `examples/behavior_test.py` is now a CLI harness with `--topic/--provider/--model/--depth/--breadth/--progression` flags. (refreshed 2026-08-10)
- Commit-hash drift: the behavioral audit cites `36914401aed44291ddad31652a99e1870848ed28`, which DOES exist in history ("Add OpenAI-compatible Gemini and DeepSeek providers") but is 6 commits behind the current HEAD `08caa9cd05e622e6435957a6f6e72efc44fc6431` ("added a progression type and removed direct_child").
- Pydantic `Config` -> `ConfigDict` migration is complete: `grep "class Config:"` under `src/bot0_thought_graph` returns zero matches (42 files searched). The migration-audit debt line about class-based `Config` deprecation warnings is now stale (see Section 1 note).
- Uncommitted-change picture (git status --short on 2026-08-08) is small: `M docs/vertical_progression_audit.md` (the audit rewrite itself is uncommitted — HEAD still holds the older pre-enum revision), `M examples/behavior_test.py`, `M .deepseek/state/subagents.v1.json`, and untracked `?? repro_interview.py`. [Coordinator note: the earlier same-day finding of uncommitted provider WIP (untracked `deepseek.py`, `gemini.py`, `openai_compatible.py`, `_env.py`) and a rewritten README no longer holds — re-verified on 2026-08-08 those files are all committed (providers landed in `36914401` and later commits) and README.md is clean. Only `repro_interview.py` remains untracked.] (refreshed 2026-08-10: the working tree now carries modified `src/bot0_thought_graph/interview/engine.py` (annotations + the C-01/C-02 fixes), modified `tests/test_interview_orchestration.py` (T-01), deleted `tests/unit/__init__.py` + `tests/integration/__init__.py`, and untracked `docs/MASTER_AUDIT.md` + `docs/CLEANUP_PLAN.md`; `repro_interview.py` is deleted.)
- Anthropic SDK is missing from the venv (`.venv/bin/python -c "import anthropic"` -> ModuleNotFoundError). `tests/test_provider_storage.py` uses `pytest.importorskip("bot0_thought_graph.providers.anthropic")` at lines 63, 130, and 327, so 3 provider tests skip. `pytest --collect-only -q tests/` reports "68 tests collected, 3 errors": the legacy files `tests/test_question_generator_async.py` and `tests/test_question_generator_async_integration.py` fail collection on the missing `anthropic` import, and `tests/test_question_loading.py` fails on `import interviewagent_xf_edit_2` -> missing `fastapi`.
- No `CHANGELOG.md` exists anywhere in the repository (verified by file search).
- `docs/` contains no other audit files: the only audits are `migration_audit.md`, `behavioral_test_audit.md`, and `vertical_progression_audit.md` (other docs are `clinical_recruitment_aot_provider_comparison.md`, `excluded_components.md`, `public_api.md`, `release_readiness_v0.1.0.md`, `target_architecture.md`, `voice_implementation_comparison.md`).
- `src/models` shim/dead-file situation: `src/models/__init__.py` is an empty docstring-only module; four files are pure re-export shims ("Legacy compatibility exports ... from bot0_thought_graph.models.X import *"): `thought_models.py`, `llm_response_models.py`, `indexed_thought_models.py`, `evaluation_models.py`. `user_state_models.py` is a real legacy-only model (imported solely by `src/agents/state_management.py:11`). `society_of_agents_models.py` and `openai_claude_llama_response_basemodels.py` have ZERO importers anywhere (the only reference to the latter is a commented-out import at `src/utils/llm_api_utils.py:33`).

## 5. Current Issues

- Code drift (see Section 4): the ProgressionType implementation landed after the older audit text was written; the vertical audit itself is still uncommitted; the behavioral audit's cited commit is not HEAD; the migration audit's `Config`-warning debt line is stale.
- Debug artifacts: `repro_interview.py` sits untracked at the repository root and must not be committed as-is (it hardcodes provider stubs and debug output).
- Known interview bugs (reproduced via `repro_interview.py`, NOT yet fixed):
  - Follow-up prompt conversation logs are ordered questions-then-answers instead of chronologically interleaved (BUG A).
  - Topic exhaustion on the last sub-thought never completes the session (BUG B).
  - A third check — exhaustion policy keyword leak across sessions (BUG C) — was not completed.
- Pydantic `ConfigDict` migration is now complete; the only remaining migration-debt items are the legacy test suite (path mutation, Windows fixtures) and historical generated data.
- Test-suite inconsistency: the venv lacks the `anthropic` SDK, so 3 provider tests skip and 3 legacy test files fail collection; the full suite is not runnable in the current environment.
- Dead code in `src/models`: four re-export shims plus two zero-importer legacy model files (`society_of_agents_models.py`, `openai_claude_llama_response_basemodels.py`) and one legacy-only model (`user_state_models.py`).

## 6. Action Items

Prioritized cleanup (P0 = must fix, P1 = should fix, P2 = nice to have):

- P0: Fix the two reproduced interview bugs in `src/bot0_thought_graph/interview/engine.py` (follow-up log ordering; last sub-thought exhaustion never completing) and land regression tests; then remove `repro_interview.py` (or replace it with a real test) so the debug artifact does not linger untracked.
- P1: Remove or archive the dead `src/models` files (`society_of_agents_models.py`, `openai_claude_llama_response_basemodels.py`, and the four pure re-export shims once legacy importers are migrated; keep `user_state_models.py` only while `src/agents/state_management.py` needs it).
- P1: Sync docs with code — update `docs/public_api.md` and README to document `ProgressionType` as the typed progression API, and commit the rewritten `docs/vertical_progression_audit.md`.
- P1: Commit the provider work if anything remains staged-worthy, and add `repro_interview.py` handling (test vs. delete) so the working tree is clean; review `examples/behavior_test.py` changes.
- P2: Install the `anthropic` SDK and sync the dev dependency group so all provider tests run (un-skips 3 tests) and the 3 legacy collection failures are addressed (either fix their imports or move them out of the package test suite).
- P2: Add a `CHANGELOG.md` and keep it updated for the v0.1.0 release and subsequent changes.

