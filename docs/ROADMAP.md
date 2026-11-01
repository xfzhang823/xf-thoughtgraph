# Roadmap — xf-thoughtgraph

> Historical roadmap: the legacy source layer referenced below was retired in
> the final legacy architecture cleanup. The canonical package is now the only
> supported implementation under `src/`.

Status: 2026-08-10. Companion documents: `docs/MASTER_AUDIT.md` (audit) and `docs/CLEANUP_PLAN.md` (executed cleanup items).

## Completed cleanup (2026-08-07 → 2026-08-10)

- Interview engine fixes: chronological conversation logs, topic-exhaustion session completion, per-session policy reset (C-01, C-02, T-01).
- Quick wins: removed the `repro_interview.py` debug artifact, the empty `sandbox/`, the stub-only `tests/unit` + `tests/integration` packages, and the `dist/` + `build/` artifacts (CW-01..CW-05).
- Dead code removal: `src/models/society_of_agents_models.py` and `src/models/openai_claude_llama_response_basemodels.py` deleted; root scratch files moved to `legacy_data/root_scripts/`; `src/evals_and_comparisons/` moved to `legacy_data/evals_and_comparisons/` (C-03..C-08).
- Docs: README and `docs/public_api.md` synced with the current API (`_DEFAULT_MODELS`/`default_model()`, `topic=`/`progression_type=`, `ProgressionType`); `docs/MASTER_AUDIT.md` drift section refreshed; `CHANGELOG.md` created (DOC-01..DOC-04).
- Environment and tests: `uv sync` installed `anthropic` (D-01); provider default-model tests and module-coverage tests added (T-02, T-03).

## Deferred items (legacy scope)

- CODE-01: Legacy TODO/FIXME sweep — 20 hits across legacy `src/` (agents, pipelines, thought_generation, `run_*.py`, `interviewagent_xf_edit_2.py`). The package and tests are clean.
- CODE-02: Legacy hard-coded model strings — `gpt-4-turbo` / `gpt-3.5-turbo` / `claude-3-5-sonnet-20241022` defaults in legacy `src/` modules.
- T-04: Legacy test debt — `test_question_loading.py` (hard-coded Windows paths, `os.chdir`) and `test_question_generator_async.py` (duplicates its integration twin). Note: `tests/test_behavior_test.py` has 4 pre-existing failures pending the `examples/behavior_test.py` CLI-harness rewrite.

## Legacy compatibility cleanup

The package no longer retains interview-era models, prompts, response-model
exports, or legacy graph-parameter aliases. Historical audit records may still
mention the removed surfaces, but they are not supported package APIs.

## Open recommendations

- D-02: update the anthropic default model (`claude-3-5-sonnet-20241022` → current Claude 5 Sonnet model ID once confirmed against the provider docs).
