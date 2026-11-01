# Agent Policy Boundary

`xf-thoughtgraph` is a reusable thought-generation library. The canonical execution path is:

`ThoughtGraphEngine` -> horizontal/vertical generation -> prompt -> provider -> parsing -> `ThoughtGraph`

That path stays in this repository.

## Keep here

- `ThoughtGraphEngine`
- `ProgressionType` and progression semantics
- provider abstractions and lazy SDK adapters
- thought-generation prompts directly required for graph construction
- `Thought`, `ThoughtArray`, `ThoughtNode`, `ThoughtGraph`
- parsing, validation, serialization
- reusable evaluation/scoring/ranking mechanisms
- reusable interview-domain services that are mechanism-like rather than policy-like

## Keep outside the core library surface

- `EvaluatorAgent`
- `ReflectAgent`
- `InterviewAgent`
- `PlannerAgent`
- facilitator/controller agents
- application-specific orchestration loops such as generate -> evaluate -> reflect -> regenerate
- retry/revision policy
- conversation strategy
- application/domain-specific memory and state

## Evaluation mechanism vs agent

The library keeps reusable evaluation mechanisms such as:

- `EvaluationService`
- scoring and threshold helpers
- ranking and overlap utilities

Those are different from an `EvaluatorAgent`, which would own application policy, decision loops, or autonomous control flow. The package should provide the scoring primitive; the consuming application should decide when to call it and how to react.

## Reflection and retry boundary

Reflection helpers that decide what to do next are only acceptable here when they remain reusable, deterministic, and directly tied to a library mechanism. A consuming application should own:

- whether to retry
- when to regenerate
- how many cycles to run
- how to combine critique, reflection, and regeneration

That control logic is application policy and should not be embedded in `ThoughtGraphEngine`.

## Dependency direction

Dependency direction should stay one-way:

`consuming application / agents` -> `xf-thoughtgraph`

The package should not depend on controller agents, application pipelines, or runtime state owned by the consumer.

## Legacy compatibility

The repository still contains interview and orchestration modules for compatibility and reuse, but the package root no longer re-exports the thin controller/policy wrappers. The canonical public API stays centered on thought generation.

