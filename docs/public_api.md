# Public API

The stable top-level entry points are:

- `generate_thought_graph` for the normal complex-topic disaggregation workflow.
- `ThoughtGraphEngine` for concept-first horizontal subtopics, vertical expansion, bounded thought graphs, named-provider or provider-injected generation, indexing, and explicit saving.
- `Thought`, `ThoughtArray`, `ThoughtNode`, and `ThoughtGraph` as the structured concept-first result models, plus the `ProgressionType` vertical-progression enum.
- `LLMProvider` and `AsyncLLMProvider` protocols for custom providers.
- `MemoryRepository` and `JsonRepository` for optional caller-selected persistence.

Requests, models, policies, and adapter classes are available from their subpackages. Provider SDK adapters are lazy and require the `providers` extra; fake/custom providers require no SDK client construction.

The package is synchronous at its public engine boundary. It has no global clients, repository-root discovery, automatic persistence, or import-time network/filesystem behavior. Callers may extend it by implementing `LLMProvider` or `Repository` and injecting those objects.

## External consumer workflow

The preferred simple API delegates to the canonical `ThoughtGraphEngine`:

```python
from xf_thoughtgraph import ProgressionType, generate_thought_graph

graph = generate_thought_graph(
    "hospital emergency department operations",
    exploration="balanced",
    progression_type=ProgressionType.PREREQUISITE_DEPENDENCY,
    provider="openai",
)
```

`provider` is explicit because the package does not select an arbitrary
provider when it is omitted. For a named provider, `model=None` uses the
existing provider default and `<PROVIDER>_MODEL` environment override. The
optional `progression_type` selects the semantic relationship used by vertical
child generation; it defaults to `ProgressionType.IMPLEMENTATION_STEPS` and
does not affect horizontal generation or exploration shape. The returned
object is the canonical `ThoughtGraph`.

For advanced controls, use the existing `ThoughtGraphEngine` façade:

```python
from xf_thoughtgraph import ThoughtGraphEngine

generator = ThoughtGraphEngine(
    provider="deepseek",
    model="deepseek-v4-flash",
)

graph = generator.generate_thought_graph(
    topic="clinical research participant recruitment",
    horizontal=5,
    vertical=3,
)
```

`provider` accepts `"openai"`, `"gemini"`, `"deepseek"`, or `"anthropic"`. Named providers are created through the existing provider factory. Set `model=None` to use the package default, with `<PROVIDER>_MODEL` taking precedence. Defaults are resolved by `xf_thoughtgraph.providers.default_model(provider)`: OpenAI `gpt-5.6-luna`, Gemini `gemini-3.6-flash`, DeepSeek `deepseek-v4-flash`, Anthropic `claude-3-5-sonnet-20241022`. The returned value is always the package-owned `ThoughtGraph` model, independent of the provider SDK.

`horizontal` is the maximum number of root-level peer directions retained;
`vertical` is the maximum number of generated child levels beneath the root.
`vertical=1` returns the root plus its first horizontal layer; `vertical=2`
adds one vertical expansion beneath each first-level thought. Explicit
horizontal and vertical values are independent, and the horizontal value is
not reused as the vertical child-count limit. New vertical values are bounded
by `ThoughtGraphEngine.MAX_FACADE_DEPTH`. When neither bound is supplied, the
engine uses adaptive exploration. Vertical expansion accepts
`progression_type=` (default `ProgressionType.IMPLEMENTATION_STEPS`). Results
use Pydantic's standard `model_dump()` and `model_dump_json()` serialization.

Direct provider-object injection remains supported:

```python
engine = ThoughtGraphEngine(provider, model="your-model")
```

## Concept-first workflow

```python
engine = ThoughtGraphEngine(provider, model="your-model")
subtopics = engine.generate_subtopics("Clinical research recruitment")
details = engine.expand_subtopic(
    "Clinical research recruitment",
    "Participant eligibility",
)
thought_array = engine.generate_array_of_thoughts("Clinical research recruitment")
graph = engine.generate_thought_graph(
    "Clinical research recruitment", horizontal=2, vertical=8
)
```

Horizontal methods produce sibling-level major dimensions. Vertical expansion produces direct, more-specific children of one subtopic. `ThoughtArray` contains the concept and typed first-level `Thought` items. `ThoughtGraph` contains the concept, a `ThoughtNode` root, and recursive child nodes. `vertical=1` means root plus first-level subtopics; `vertical=2` adds one vertical expansion under each subtopic. `horizontal` caps root-level peer directions, while explicit vertical mode uses an independent internal child cap. Graph generation performs one provider call for the horizontal expansion plus one call per expanded node and never persists implicitly.

The graph therefore follows a two-stage conceptual structure: horizontal
generation identifies broad, parallel dimensions, and vertical generation
decomposes each dimension into more-specific children. With
`progression_type=ProgressionType.PROBLEM_SOLUTION`, for example:

```text
Participant recruitment
├── Recruitment strategy
│   ├── Low awareness → targeted outreach
│   ├── Limited referrals → clinic partnerships
│   └── Ineffective messaging → plain-language materials
└── Participant eligibility
    ├── Eligibility confusion → clear screening criteria
    └── Screening burden → a streamlined prescreening process
```

These problem-solution items are sibling thoughts under each horizontal
dimension. `ProgressionType` describes the semantic relationship among the
vertical children; it does not itself add tree depth or alter the horizontal
layer. Tree depth is controlled by `vertical` or adaptive exploration. In
adaptive mode, `focused`, `balanced`, and `rich` control
whether a branch continues, while `progression_type` controls the meaning of
the children generated when it does continue.

When no graph-shape bounds are supplied, `generate_thought_graph()` uses the
`balanced` adaptive exploration profile. The `exploration=` argument accepts
`"focused"`, `"balanced"`, or `"rich"`; profiles control continuation and
stopping decisions rather than mapping to fixed graph sizes. Adaptive profiles
cannot be combined with explicit `horizontal=`/`vertical=` arguments.

Adaptive calls also accept optional `max_calls=` and `max_nodes=` budgets.
`max_calls` includes generation and continuation-evaluation provider calls;
`max_nodes` includes the root. Budgets may lower but not exceed the engine's
internal safety ceilings. Adaptive traversal uses a breadth-first frontier so
later root branches receive opportunities before earlier branches continue
deeper. The returned `ThoughtGraph.exploration_summary` reports actual calls,
nodes, expansion attempts, completion status, configured budgets, and the stop
reason.

Adaptive horizontal exploration probes small bounded candidate batches and
evaluates distinctness and marginal value locally before requesting further
coverage. The batch strategy is internal and does not expose a horizontal
width control.

Adaptive traversal can retain a useful generated child while pruning it from further recursive expansion. Semantic stopping remains distinct from internal safety stopping; if an internal guard is reached, the engine returns the valid partial graph and records the safety category in its exploration trace. Guard values are internal and are not public graph-shape controls.

Set `ranked=True` on horizontal or graph methods to use the existing clustering/ranking path. `expand_subtopic()` and `generate_thought_graph()` accept `progression_type=` (a `ProgressionType` member or its string value; default `ProgressionType.IMPLEMENTATION_STEPS`) to select the parent→child semantic relationship. `ProgressionType` (`implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, `prerequisite_dependency`) is exported from `xf_thoughtgraph` and `xf_thoughtgraph.models`. Vertical expansion preserves provider order.

## Advanced typed API

The existing request-based API remains supported for explicit controls:

```python
from xf_thoughtgraph.thought_generation import HorizontalGenerationRequest

result = engine.generate(
    HorizontalGenerationRequest(
        idea="embedded systems", model="your-model", num_thoughts=10
    )
)
```

The graph engine owns clustering, persistence boundaries, and generation
behavior directly. Persistence is optional and explicit.
