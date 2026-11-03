# Adaptive exploration audit

## Scope and reference run

Reference notebook: `/home/xzhang/dev/AgenticAICompass/notebooks/xf_thoughtgraph_example.ipynb`

Audited configuration from the saved notebook:

- API: `ThoughtGraphEngine.generate_thought_graph()`
- `topic="Assess Claim Documentation Completeness"`
- `exploration="balanced"`
- `progression_type="implementation_steps"`
- `model="gpt-5.6-luna"`
- provider: `openai`

The notebook output was read as saved; no provider or paid LLM calls were made for this audit. The notebook's adaptive graph metadata reports `breadth=3`, `depth=8`, and the graph contains exactly 128 nodes.

## Observed behavior

The three root branches and their saved-output sizes are:

| Root branch | Maximum depth | Nodes in branch | Observation |
|---|---:|---:|---|
| Required Information Coverage | 8 | 97 | Deep, highly expanded branch; includes repeated claim/document mapping, identifier normalization, consistency, and resolution details. |
| Evidence and Attachment Sufficiency | 6 | 29 | Substantially expanded, but less deeply than the first branch. |
| Consistency and Documentation Quality | 1 | 1 | Retained as a root child but has no generated children. |

Depth distribution for the whole saved graph is: depth 0: 1, depth 1: 3, depth 2: 8, depth 3: 8, depth 4: 12, depth 5: 20, depth 6: 44, depth 7: 20, depth 8: 12. The first two branches account for 126 nodes; the root and the third root child account for the remaining two.

The graph visibly contains granular implementation detail. Examples include `Normalize identifier formats`, `Map source identifiers`, `Check transformation mapping coverage`, `Verify transformation accuracy`, and `Document validation results`, alongside similarly granular amount, file-format, and resolution checks. Some of this is useful operational decomposition. Some sequences appear to restate the same review operation at progressively narrower levels. The output alone does not establish that every level is valueless, but it does establish that the current run reached the configured maximum depth and retained a large amount of detail before later branches were visited.

## Execution flow and source references

1. `ThoughtGraphEngine.generate_thought_graph()` validates the topic and exploration profile, normalizes `progression_type`, resets adaptive state, and calls `_generate_adaptive_graph()` (`src/xf_thoughtgraph/thought_generation/engine.py:524-552`).
2. `_generate_adaptive_graph()` creates the root, generates root-level horizontal candidates, then iterates `root.children` in list order (`src/xf_thoughtgraph/thought_generation/adaptive_traversal.py:60-85`).
3. `_generate_adaptive_horizontal()` probes batches of three candidates, keeps materially distinct names, and stops on a duplicate/insufficient-distinctness signal, the eight-child internal candidate limit, or a safety stop (`adaptive_traversal.py:87-167`). The saved run retained three root branches.
4. `_expand_adaptive_node()` is recursive depth-first traversal. It checks the depth ceiling and natural endpoints, consumes adaptive work, calls vertical generation with `max_details=4`, filters generated children for meaningful novelty, then evaluates the eligible children as a batch (`adaptive_traversal.py:169-303`).
5. Candidate eligibility uses deterministic token heuristics for distinctness, root relevance, marginal value, and natural endpoints (`adaptive_policy.py:81-117`, `120-170`, `173-206`). The marginal-value heuristic deliberately discounts repeated procedural levels, but it is lexical rather than domain-semantic.
6. `DecompositionEvaluationService` asks the provider whether each retained child merits one further level; its prompt explicitly says not to choose width or apply a fixed depth/width rule (`src/xf_thoughtgraph/reflection/decomposition.py:60-88`). The service validates that every candidate receives a decision (`decomposition.py:91-138`).
7. A `decompose=false` decision retains the child and does not recurse. Evaluation failure is caught by `_evaluate_adaptive_decomposition()`, recorded as `decomposition_fallback`, and defaults to continuing (`adaptive_traversal.py:305-358`).
8. Work accounting is global to the run. `_consume_adaptive_work()` consumes a provider-call slot and an expansion-attempt slot; `_consume_adaptive_provider_call()` enforces the provider-call budget (`adaptive_traversal.py:366-393`). The configured limits are 64 provider calls, 64 expansion attempts, 128 retained nodes, maximum depth 8, maximum horizontal branches 8, and four requested adaptive vertical children (`engine.py:74-101`).

## Findings

### Strongly indicated, but not directly recorded: the third branch was cut off by global traversal state

The saved graph has exactly the configured `_ADAPTIVE_MAX_NODES = 128`, and the first two branches plus the root and third child consume all 128 retained-node slots. Node counting starts at one for the root and increments for every retained child (`adaptive_traversal.py:69`, `138-143`, `217-220`). When the next child would exceed the limit, `_record_safety_stop(NODE_BUDGET, ...)` sets the global `_adaptive_safety_stopped` flag (`adaptive_traversal.py:210-215`, `395-408`). The outer root-child loop stops when that flag is set (`adaptive_traversal.py:73-75`).

Therefore the third branch was not shown to be rejected by the decomposition evaluator, relevance policy, marginal-value policy, or a provider token error. It was retained horizontally, and its recursive expansion was either skipped after earlier depth-first work exhausted the global node budget or ended before producing children. The notebook does not serialize `last_exploration_trace`, so the exact stop record is not present in the saved output. The exact 128-node match and guard ordering make node-budget exhaustion the strongest explanation, but it should be treated as highly supported rather than directly proven from the notebook alone. A saved trace or a no-call diagnostic rerun with the same recorded responses would make this definitive.

### Confirmed: traversal is unfair to later sibling branches

Expansion is depth-first and ordered by the provider-selected root-child list. There is no per-branch reservation, round-robin scheduling, frontier queue, or fairness adjustment. A large early branch can consume the global node, expansion, and provider-call budgets before later branches receive their first expansion. This directly explains the observed 97/29/1 distribution and is a structural property, not a random evaluator decision.

### Confirmed: breadth is capped, but not adaptively selected

Adaptive vertical generation always requests at most four children (`engine.py:83-84`, `adaptive_traversal.py:195-201`). It retains every returned child passing the novelty filter until the global node budget is reached (`adaptive_traversal.py:203-220`). The decomposition evaluator is called after children have already been generated and returns only `decompose: bool`; it controls recursive depth, not how many siblings are retained (`decomposition.py:42-50`, `91-138`). Thus current breadth control is a fixed request cap plus lexical filtering, not a meaningful-value choice of child count.

The horizontal side is similarly bounded by a fixed maximum of eight, with three-candidate probing and distinctness filtering (`adaptive_traversal.py:93-167`). That is a safety mechanism, not a model-assisted breadth decision.

### Confirmed: depth controls are mixed with global safety controls

Semantic continuation has several gates: natural endpoint, relevance, marginal value, novelty, and model-assisted decomposition. Safety termination is separate in code and has distinct reasons: `call_budget`, `expansion_budget`, and `node_budget`. The maximum depth is a hard ceiling at eight (`adaptive_traversal.py:180-183`, `engine.py:86`).

The saved run reached depth 8, so the depth ceiling permitted the deepest observed path. Some individual nodes at depth 8 may have stopped because of `DEPTH_LIMIT`; the notebook does not include the trace needed to count those stops. The global node cap, however, is confirmed by the exact 128-node result.

### Hypothesis: some deep detail has diminishing value

The first branch contains plausible operational detail, but repeated patterns such as extracting, normalizing, mapping, validating, reconciling, and recording may represent implementation-level duplication rather than new decision value in every descendant. This is a quality hypothesis, not a confirmed evaluator failure. The existing marginal-value heuristic attempts to suppress repeated procedural decomposition by discounting procedural terms at prior levels (`adaptive_policy.py:108-117`), and the model evaluator is explicitly instructed to judge the value of one additional level (`decomposition.py:60-77`). The observed depth alone is not evidence that all deep nodes should be removed.

### Not evidenced: provider token-limit termination

All adaptive generation and decomposition requests use `max_tokens=1056` (`requests.py:8`, `adaptive_traversal.py:195-201`, `329-345`). The saved notebook contains no provider error or response-truncation diagnostic for this graph. A provider response failure would enter the decomposition fallback path only for the evaluator, while a failure in horizontal/vertical generation would propagate from the generation functions (`generation.py:10-31`, `expansion.py:10-41`). Nothing in the saved graph distinguishes or supports token-limit exhaustion; the exact node-budget match is the stronger explanation.

## Evaluation of current controls

Current controls are adequate for bounded execution and basic adaptive depth selection, but not for balanced graph coverage or adaptive breadth selection.

- Depth: reasonably layered. Deterministic novelty/relevance/marginal-value checks precede the existing evaluator, and evaluator rejection is distinct from safety stops. The lexical policy can still misjudge domain value, and the hard depth ceiling is global rather than branch-aware.
- Breadth: under-controlled semantically. Four children are requested for every expanded node, and all eligible children are retained. The evaluator cannot say that two of four children are useful while the other two are redundant.
- Traversal fairness: inadequate. DFS plus global budgets makes earlier branches first-class and later branches best-effort. This is the confirmed structural mechanism that can cause the observed unexpanded third branch; the saved notebook does not retain the final stop event itself.
- Diagnostics: mostly present in memory via `last_exploration_trace` and counters, but not included in `ThoughtGraph` or the notebook's serialized graph. This makes post-run attribution harder than necessary.
- Budget separation: conceptually clear in the implementation, but provider-call budget includes both generation and decomposition-evaluation calls. A run can therefore spend capacity on evaluation calls as well as child generation. The current code records the category when a safety stop occurs, so tests can distinguish these paths, but the saved reference run did not preserve that trace.

## Recommendations, smallest coherent scope first

1. **Fix sibling fairness before changing semantic thresholds.** Replace the single recursive DFS walk with a small existing-state traversal adjustment that gives each retained root branch an opportunity to expand before continuing deeply into the next level (for example, a frontier/round-robin queue while preserving `_expand_adaptive_node()`'s existing filters and evaluator). Keep the global safety budgets. This addresses the confirmed 97/29/1 and 1-node third branch without imposing an arbitrary per-branch depth limit.
2. **Make adaptive breadth an evaluator-visible decision.** Reuse `DecompositionEvaluationService`, but extend its existing candidate decision contract so the evaluation can mark generated children as useful to retain or terminal/redundant, or otherwise return a selected subset/count. Apply that decision before recursive expansion while preserving useful detailed children. This is a larger but still local change to the existing evaluator path; simply lowering the adaptive output safety cap would be an arbitrary breadth restriction and would not satisfy the design principle.
3. **Improve stop observability.** Persist a compact adaptive summary/trace with the returned graph or provide a documented diagnostic accessor containing final counters and the first global safety-stop reason. This is especially useful for distinguishing evaluator rejection, `node_budget`, `expansion_budget`, `call_budget`, depth limit, and provider failures in future notebook runs.
4. **Only then tune semantic policy if fixtures show false continuation.** Use representative deterministic fixtures to assess whether procedural discounting or relevance thresholds reject genuinely useful domain detail. Do not globally deduplicate similar subtasks or remove deep decomposition solely because it resembles another branch.

## Regression tests needed

- A three-root-branch fixture with a small node budget proving that traversal gives every root branch at least one expansion opportunity, and that later branches are not silently left as leaves solely because an earlier branch is deep.
- A trace assertion for the reference-shaped failure: a global `node_budget` stop is recorded, the third branch is retained, and no `decomposition_terminal` decision is falsely attributed to it.
- Separate fixtures for `call_budget`, `expansion_budget`, `node_budget`, `depth_limit`, `decomposition_terminal`, `decomposition_fallback`, and provider generation failure/token-response failure. Assert both graph shape and stop reason.
- A breadth-selection fixture where vertical generation returns four candidates but only a meaningful subset is selected for retention/expansion, while a justified four-child result remains intact.
- A fairness fixture with one highly expandable early branch and one shallow later branch, asserting that the later branch receives work before the global budget is exhausted.
- A no-regression fixture for legitimate deep decomposition reaching depth 8 when every level is valuable, proving that fairness changes do not introduce arbitrary depth restrictions.
- A provider-call accounting test that counts both generation and decomposition-evaluation calls and verifies the documented budget semantics.
- A saved-run diagnostic test ensuring the adaptive summary can explain why a branch stopped without requiring a paid provider rerun.

## Phase 1 migration update

Phase 1 removes predetermined child-count instructions from adaptive generation only. Adaptive horizontal and vertical calls now use dedicated prompt templates in `src/xf_thoughtgraph/prompts/thought_generation_prompt_templates.py` that ask the model to choose the natural number of meaningful, distinct children, maintain sibling granularity, avoid artificial grouping or invented detail, and return an empty list when no meaningful decomposition exists. The vertical adaptive prompt preserves the existing `progression_type` semantics, including strict directional prerequisites for `prerequisite_dependency`.

The implementation reuses `HorizontalGenerationRequest`, `VerticalGenerationRequest`, the existing generation/expansion services, model validation, novelty/relevance filters, and the existing decomposition continuation evaluator. Adaptive responses are still bounded by internal safety limits (eight retained horizontal root directions and sixteen children from one vertical response); these are truncation guards, not prompt targets. The existing adaptive execution budgets and traversal scheduling were not changed.

Explicit APIs retain their original count-bearing prompts and behavior: `generate_subtopics()`, `generate_array_of_thoughts()`, `expand_subtopic()`, and explicit bounded graph generation remain backward compatible.

Deterministic coverage was added for variable adaptive counts, including fewer and more than four horizontal/vertical children, empty vertical output, count-free adaptive prompts, explicit-count compatibility, and prerequisite prompt semantics. Phase 1 does not implement fair traversal, per-branch budget reservation, or a separate breadth evaluator. Those remain Phase 2 work, along with the audit's prior recommendation to improve stop diagnostics.

## Phase 2 migration update

Phase 2 replaces adaptive recursive depth-first traversal with a breadth-first frontier in `src/xf_thoughtgraph/thought_generation/adaptive_traversal.py`. Retained root children enter the frontier together; each node is expanded once per frontier round, and evaluator-approved children are queued for later rounds. This preserves unequal natural depths and existing semantic filters while ensuring an early branch cannot consume all shared capacity before later sibling branches receive an expansion opportunity.

Adaptive graph generation now accepts optional `max_calls` and `max_nodes` controls on `ThoughtGraphEngine.generate_thought_graph()` and the top-level `generate_thought_graph()` function. `max_calls` counts provider calls for generation and decomposition evaluation; `max_nodes` includes the root and every retained child. Both values must be positive and may lower, but not exceed, the internal absolute ceilings. Explicit horizontal/vertical graph calls and the existing count-based APIs are unchanged.

Adaptive results expose `ThoughtGraph.exploration_summary` and `ThoughtGraphEngine.last_exploration_summary` with `actual_calls`, `actual_nodes`, `expansion_attempts`, configured `max_calls` and `max_nodes`, a boolean `completed`, and `stop_reason`. Natural completion reports `semantic_completion`; budget or internal safety termination reports its specific category such as `call_budget`, `node_budget`, `expansion_budget`, `depth_limit`, or `internal_candidate_limit`. Evaluation continuation and all Phase 1 LLM-determined child-count prompts remain unchanged.

Deterministic tests cover fair root-branch scheduling, unequal branch depth, variable child counts, user call/node budgets, expansion/call/node safety stops, evaluator-call accounting, diagnostic accuracy, public API forwarding, and explicit graph compatibility. Phase 2 does not introduce per-branch quotas, a breadth evaluator, new evaluation services, or changes to the global absolute safety ceilings.

