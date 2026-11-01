# Vertical Thought Progression Audit

## 1. Executive Summary

The current implementation has five progression types, represented by the public `ProgressionType(str, Enum)`:

1. `implementation_steps`
2. `simple_to_complex`
3. `chronological`
4. `problem_solution`
5. `prerequisite_dependency`

`implementation_steps` is the explicit default for lower-level expansion, `expand_subtopic()`, and recursive `generate_thought_graph()` expansion. Raw strings remain accepted at public boundaries and are normalized to the enum. The former generic child-expansion label has been removed.

The main current limitation is semantic rather than type-related: all modes are represented as ordinary `ThoughtNode.children` edges, so sequence, procedure, problem-solution, and prerequisite relationships are not preserved as edge metadata.

## 2. Current Progression Types in the Repository

### `implementation_steps`

Exact value: `"implementation_steps"`.

This is the default for `VerticalGenerationRequest`, `expand_vertical()`, `expand_idea()`, `expand_all()`, `expand_subtopic()`, and `generate_thought_graph()`. The prompt asks for implementation-oriented key areas or steps. The direction is parent thought -> implementation areas or steps, but strict ordering and prerequisite semantics are not guaranteed.

It is workflow- and implementation-oriented, and is reachable through both the lower-level API and the public façade. Its value is interpolated into the vertical prompt and is not stored in the result models.

### `simple_to_complex`

Exact value: `"simple_to_complex"`.

The prompt asks the model to start with basic concepts and gradually introduce more advanced ideas. Its direction is lower conceptual complexity -> higher conceptual complexity. It is primarily conceptual and explanatory. It is accepted by the enum and public generation methods, but it does not create a typed complexity edge in the graph.

### `chronological`

Exact value: `"chronological"`.

The prompt asks for evolution or historical development. Its direction is earlier state/event -> later state/event, although strict next-step workflow ordering is not validated. It is temporal and useful for lifecycle analysis.

### `problem_solution`

Exact value: `"problem_solution"`.

The prompt asks for problems or challenges followed by solutions or approaches. The intended direction is problem -> solution, but the prompt does not guarantee that every generated child is a solution or distinguish causes, analysis, and remediation steps.

### `prerequisite_dependency`

Exact value: `"prerequisite_dependency"`.

The prompt requires strict, directional prerequisites or dependencies: a child must be satisfied, completed, or understood before the parent thought can proceed. This is the clearest current mode for prerequisite-oriented workflow analysis, although the output graph still stores the relationship as a generic child edge.

## 3. Current Code Locations and Call Paths

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

## 4. Current Semantic Behavior

The lower-level and public façade paths now use the same typed progression contract and the selected value reaches prompt construction. The public detail prompt retains implementation-step wording by default and adds explicit prerequisite guidance when `prerequisite_dependency` is selected.

The implementation does not validate the semantic relationship of provider output. It validates JSON shape and constructs package-owned models, but it does not prove that generated children are chronological, causal, or required prerequisites.

## 5. Current Type Comparison

| Current type | Meaning | Direction | Publicly selectable? | Workflow relevance | Main limitation |
| --- | --- | --- | --- | --- | --- |
| `implementation_steps` | Implementation areas or steps | Parent -> implementation area/step | Yes; default | High | Order and prerequisites are not guaranteed |
| `simple_to_complex` | Basic concepts to advanced concepts | Less complex -> more complex | Yes | Moderate | Conceptual progression is not necessarily a process edge |
| `chronological` | Evolution or historical development | Earlier -> later | Yes | High | History is not always an actionable next-step sequence |
| `problem_solution` | Challenges followed by solutions/approaches | Problem -> possible solution | Yes | High | Causes, analysis, and remediation are not separated |
| `prerequisite_dependency` | Strict prerequisites/dependencies | Required condition -> dependent work/parent | Yes | High | Edge direction is not stored separately in the graph |

## 6. Public Façade vs Lower-Level Progression System

The earlier split between a lower-level progression selector and a generic public child-expansion mode has been removed. `expand_subtopic()` and recursive graph expansion now use the same enum and prompt pathway as lower-level vertical generation.

The façade defaults explicitly to `ProgressionType.IMPLEMENTATION_STEPS`, so omitted values no longer depend on an unnamed or generic mode. Callers may select another enum member or pass its string value.

## 7. Workflow Requirements Analysis

- `implementation_steps` answers “How is this carried out?” and is the best default for implementation and requirements discovery.
- `chronological` answers “What happens next?” but should not be treated as a validated process ordering.
- `problem_solution` supports incident, remediation, and requirements-gap analysis, but does not guarantee a strict problem-to-resolution chain.
- `prerequisite_dependency` answers “What must be satisfied before this can proceed?” and is the strongest mode for dependency discovery.
- `simple_to_complex` helps elaborate a workflow from an overview toward more detailed concepts, but does not represent execution order.

Together these modes support basic workflow discovery across business, clinical, operational, manufacturing, software incident, and requirements contexts. They do not model branching, parallelism, joins, or typed edge provenance.

## 8. Semantic Overlap and Ambiguity

### `implementation_steps` vs `chronological`

Implementation steps may be ordered in practice, but the current prompt asks for implementation areas or steps without requiring “after” relationships. `chronological` explicitly concerns evolution or history. They overlap for sequential processes but are not equivalent.

### `simple_to_complex` vs `implementation_steps`

Both can add detail. `simple_to_complex` orders concepts by explanatory complexity, while `implementation_steps` organizes work or implementation areas. Neither guarantees a constituent-part hierarchy.

### `problem_solution` directionality

The intended direction is problem -> solution, but the prompt allows a mixture of challenges, analysis, and approaches. Behavioral evaluation is needed if a strict transition is required.

### `prerequisite_dependency` vs `chronological`

Prerequisites are conditions for proceeding; chronological steps are events in time. A prerequisite can occur earlier, but not every earlier event is required. These should remain distinct.

## 9. Current Graph-Edge Semantics

`ThoughtGraph` stores relationships as untyped `ThoughtNode.children` edges. It does not store the selected progression type on `Thought`, `ThoughtNode`, or `ThoughtGraph`, and it does not distinguish procedural, temporal, problem-solution, or prerequisite edges.

This is acceptable for a generic generated tree, but consumers must not infer that every edge means decomposition. If provenance or graph analysis becomes a requirement, graph-level progression metadata or typed edges should be considered in a separate change.

## 10. Gaps in the Existing Progression Set

The current set now explicitly includes prerequisite/dependency semantics. A strict causal mode remains a possible gap: `problem_solution` does not guarantee causality, and `chronological` does not imply causality.

Other possible future relationships—evidence, diagnostic reasoning, and goal-means—would likely require additional role or provenance semantics rather than only another label. Contrast is generally better modeled horizontally.

## 11. Possible Future Normalization

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

## 12. Backward Compatibility

The five current enum values remain available. Existing callers may pass either enum members or equivalent strings, for example:

```python
from bot0_thought_graph import ProgressionType, ThoughtGraphEngine

engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    horizontal=5,
    vertical=2,
    progression_type=ProgressionType.PREREQUISITE_DEPENDENCY,
)

engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    horizontal=5,
    vertical=2,
    progression_type="prerequisite_dependency",
)
```

When omitted, the façade uses the explicit `ProgressionType.IMPLEMENTATION_STEPS` default. Invalid strings fail clearly with `ValueError` instead of silently selecting a different mode.

## 13. Public API Recommendation

The canonical façade shape is:

```python
graph = engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    horizontal=5,
    vertical=3,
    progression_type=ProgressionType.IMPLEMENTATION_STEPS,
)
```

The API should continue accepting strings for convenience while documenting the enum as the preferred typed form. All five modes can currently be passed through the same provider-independent graph path, with the limitation that the result remains an untyped tree.

## 14. Prompt Architecture Implications

The shared prompt layer receives `progression_type.value`, so prompt text is provider-independent. The lower-level and façade vertical prompts both receive the normalized value. The prerequisite prompt guidance explicitly requires strict directional dependencies.

Future prompt work should keep one central progression-instruction mapping and avoid provider-specific progression implementations. Prompt guidance should remain short, directional, and behaviorally testable.

## 15. Testing Gaps

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

## 16. Recommended Next Step

Keep the current five enum-backed modes stable. If workflow consumers need stronger guarantees, the next focused design change should define graph-edge metadata or a provenance field rather than adding more loosely defined labels.

## 17. Final Recommendation

- Keep all five current values unchanged.
- Use `ProgressionType.IMPLEMENTATION_STEPS` as the explicit default.
- Prefer enum members for typed callers while preserving string compatibility.
- Keep progression semantics provider-independent and prompt-driven.
- Treat graph edges as generic unless progression metadata is added explicitly.
- Defer new modes such as `causal`, `evidence`, and `diagnostic` until a concrete use case and behavioral contract are defined.

No production functionality was changed by this documentation update.
