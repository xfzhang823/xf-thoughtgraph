# Cleanup Plan — bot0-thought-graph

> Historical cleanup plan: subsequent legacy source retirement completed the
> deferred legacy-scope work described in this document.
>
> Historical naming is retained in the plan entries below. The current
> package identity is `XF ThoughtGraph` / `xf-thoughtgraph` / `xf_thoughtgraph`.
> The later simplification cleanup also removed the interview-era package
> surfaces and legacy graph-parameter compatibility described below.

## Scope and Method

- Date: 2026-08-08. Every item below was verified against the live working tree (grep / read / git / directory listings) — no assumptions.
- Source of truth: `docs/MASTER_AUDIT.md` (consolidated 2026-08-08) plus a re-scan performed today because the codebase moved again after the audit was written (see Drift note in Cross-Reference).
- Scope: whole repository, including the retained legacy layer (`src/agents`, `src/pipelines`, `src/models`, root scripts). Items touching legacy code are marked "legacy scope decision" — the package itself (`src/bot0_thought_graph/`) is clean of TODO/FIXME and deprecated model strings.
- Working tree state at scan time: HEAD `08caa9cd`; uncommitted user work in `docs/vertical_progression_audit.md` and `examples/behavior_test.py` is NOT a cleanup target.

## Priority Levels

- **Critical** — known defect or blocked test suite; fix first.
- **High** — misleading user-facing docs or environment that breaks standard dev workflow.
- **Medium** — dead code / doc sync / coverage gaps; safe but needs care.
- **Low** — artifacts, scratch files, legacy-scope decisions; no urgency.

## Quick Wins

5-minute items, no behavior risk:

| ID | Priority | Category | Action | Item | Details/Verification | Status | Owner |
|----|----------|----------|--------|------|----------------------|--------|-------|
| CW-01 | High | Files | Delete | Debug artifact `repro_interview.py` (repo root) | `git status --short` shows `?? repro_interview.py`. Its findings are captured in MASTER_AUDIT §5 and will be covered by regression tests T-01. Removed 2026-08-10. | Done | |
| CW-02 | Low | Files | Delete | Empty `sandbox/` directory | `ls -A sandbox` → no entries. Directory already absent 2026-08-10. | Done | |
| CW-03 | Low | Files | Delete | Stub-only test dirs `tests/unit/` and `tests/integration/` | Each contains only `__init__.py`. Delete or populate; no test lives there. Removed 2026-08-10. | Done | |
| CW-04 | Medium | Docs | Update | Deprecated model strings (`deepseek-chat`, `deepseek-reasoner`, `gemini-2.0-flash`) | **ZERO hits repo-wide** (case-insensitive grep). Nothing to update — deprecated names named in the task do not exist anywhere. Current names used: `deepseek-v4-flash`, `gemini-2.5-flash`/`gemini-3.6-flash`, `gpt-5.6-luna`, `gpt-5-mini-2025-08-07` (doc only). Re-verified 2026-08-10: zero source hits. | Done | |
| CW-05 | Low | Files | Delete | Build artifacts `dist/` and `build/` | `dist/` contains `bot0_thought_graph-0.1.0-py3-none-any.whl`, two `.tar.gz`; `build/` contains `bdist.linux-x86_64/` + `lib/`. Rebuildable via `uv build`. Removed 2026-08-10. | Done | |

## Cleanup Items

| ID | Priority | Category | Action | Item | Details/Verification | Status | Owner |
|----|----------|----------|--------|------|----------------------|--------|-------|
| C-01 | Critical | Code | Refactor | `interview/engine.py`: follow-up conversation logs are not chronological | Repro run: follow-up prompt contains `Agent: Initial / Agent: Follow-1 / User: answer one / User: answer two` — all questions before all answers. `logs = [agent...] + [user...]` (engine.py ~line 86-87) must interleave per turn. Also feeds `TopicExhaustionPolicy.set_scoped_logs` (should receive pre-turn logs; current self-overlap inflates redundancy — first answer scores 0.5). Fixed + verified 2026-08-10. | Done | |
| C-02 | Critical | Code | Refactor | `interview/engine.py`: topic exhaustion on the last sub-thought never completes the session | `if exhaustion["is_exhausted"] and location is not None` skips the override when no topic remains; low-scoring answers loop follow-ups forever (repro: 7 identical answers, still not completed). Exhausted + no location should complete the session. Fixed + verified 2026-08-10. | Done | |
| T-01 | Critical | Tests | Test | Regression tests for C-01 and C-02 | Add to `tests/test_interview_orchestration.py`: chronological-pair assertion on the follow-up prompt; exhaustion-completes-session on a single-sub-thought graph; policy reset between sessions (keywords leak across `start()` calls). Landed 2026-08-10 — 3 tests, interview suite 8 passed. | Done | |
| D-01 | High | Dependencies | Update | Sync venv: `uv sync --extra providers --extra dev` (installs `anthropic`) | `.venv/bin/python -c "import anthropic"` → `ModuleNotFoundError`. Consequences: 3 provider tests skip (`test_provider_storage.py` `importorskip`, lines 62/129/246) and 3 legacy test files fail collection (`test_question_generator_async*.py`, `test_question_loading.py`). `uv run pytest` also fails to spawn. Done 2026-08-10: `uv sync` installed `anthropic==0.120.0`; 3 provider skips and the 2 anthropic-based legacy collection errors are resolved. | Done | |
| DOC-01 | High | Docs | Update | README.md claims that are now stale | (1) "no defaults are hard-coded into the adapters" — false: `providers/__init__.py` now defines `_DEFAULT_MODELS` (`gpt-5.6-luna`, `gemini-3.6-flash`, `deepseek-v4-flash`, `claude-3-5-sonnet-20241022`) and `default_model()` with `<PROVIDER>_MODEL` env override; (2) top-level exports now include `ProgressionType`; (3) façade `generate_thought_graph()` gained `topic=` alias and `progression_type=`; `expand_subtopic()` gained `progression_type=`. Done 2026-08-10. | Done | |
| C-03 | High | Files | Delete | `src/models/society_of_agents_models.py` (132 lines) | Zero importers repo-wide (grep for module name and contents). Docstring says "TODO: planned for the next phase". Dead code. Done 2026-08-10. Deleted via git rm. | Done | |
| C-04 | High | Files | Delete | `src/models/openai_claude_llama_response_basemodels.py` (255 lines) | Zero importers; only reference is a commented-out import at `src/utils/llm_api_utils.py:33`. Done 2026-08-10. Deleted via git rm. | Done | |
| C-05 | Medium | Files | Move | `src/models/user_state_models.py` + 4 re-export shims | `user_state_models.py` is real legacy code used only by `src/agents/state_management.py`; shims (`thought_models`, `evaluation_models`, `indexed_thought_models`, `llm_response_models`) re-export package classes for legacy importers and the parity test (`tests/test_package_models_and_prompts.py:26-27` asserts identity). Keep while legacy is retained; revisit when legacy is retired. Done 2026-08-10. Kept — reviewed, legacy compat. Keep — documented in ROADMAP.md. | Done | |
| C-06 | Low | Files | Move | Root scratch/app files with no importers: `tree.py`, `picklethisfile.py`, `remove_unwanted_packages.py`, `startstuff.sh`, `install.sh`, `resume_service.py`, `llm_service.py` | No imports found (grep). `resume_service.py` is a FastAPI app — FastAPI is an explicit non-goal (README). Move to `legacy_data/` or delete after owner decision. Done 2026-08-10. Moved to legacy_data/root_scripts/ (git mv, 7 files). | Done | |
| C-07 | Low | Files | Delete | Frontend remnants `index.js`, `package.json`, `package-lock.json` | Legacy React frontend was removed in commit `16155df5`. Check for references before deleting (docs/README mentions none). Done 2026-08-10. Deleted via git rm. | Done | |
| C-08 | Low | Files | Move | `src/evals_and_comparisons/` (`compute_similarity.py`, `text_similarity_finder.py`) | No importers; only a docstring mention of `compute_similarity_and_cluster` in legacy `src/thought_generation/thought_generator.py:114`. Legacy scope decision. Done 2026-08-10. Moved to legacy_data/evals_and_comparisons/ (git mv, 3 files). | Done | |
| D-02 | Medium | Dependencies | Update | Review `_DEFAULT_MODELS` currency | `claude-3-5-sonnet-20241022` is a 2024 model — verify against the current Anthropic lineup. OpenAI/Gemini/DeepSeek defaults (`gpt-5.6-luna`, `gemini-3.6-flash`, `deepseek-v4-flash`) look current. Owner decision. Done 2026-08-10: reviewed — Anthropic's current lineup is the Claude 5 family (Sonnet 5 / Opus 5 / Fable 5 / Mythos 5), so `claude-3-5-sonnet-20241022` is three generations behind. Recommendation: update the anthropic default to the current Sonnet 5 model ID once the exact dated ID is confirmed against the docs. | Done | |
| D-03 | Low | Dependencies | Delete | Node dependencies in `package.json` | Frontend remnant (see C-07). Remove when the manifest goes. Done 2026-08-10: no action needed — `package.json`/`package-lock.json` were removed in C-07. | Done | |
| DOC-02 | Medium | Docs | Update | `docs/public_api.md`: document `topic=` alias, `progression_type=`, `default_model()`, `ProgressionType` | Cross-check against current signatures (verified in `engine.py` lines 486+ and `providers/__init__.py` lines 31-77). Done 2026-08-10. | Done | |
| DOC-03 | Medium | Docs | Update | Refresh MASTER_AUDIT.md drift section | Audit (2026-08-08 morning) predates further drift: `_DEFAULT_MODELS`/`default_model()`, `topic=` alias, `progression_type` on façade, `ProgressionType` top-level export, CLI harness `examples/behavior_test.py`, commits `f73c34f7`…`08caa9cd`. Done 2026-08-10. | Done | |
| DOC-04 | Low | Docs | Update | Add `CHANGELOG.md` | Cross-ref MASTER_AUDIT P2 (release hygiene). No changelog exists. Done 2026-08-10. | Done | |
| T-02 | Medium | Tests | Test | Tests for `default_model()` and `<PROVIDER>_MODEL` env override | Add to `tests/test_provider_storage.py` (module already imports providers + `_env`). Currently untested (grep of tests shows no `default_model` reference). Done 2026-08-10: 2 tests landed in `test_provider_storage.py` (defaults + env override + unknown provider). | Done | |
| T-03 | Medium | Tests | Test | Coverage for package modules with no direct test imports | Verified via grep of `tests/`: `orchestration/coordinator.py`, `orchestration/policies.py`, `interview/state.py`, `thought_generation/reader.py`, `thought_generation/ranking.py`, `thought_generation/parsing.py` (parsing is exercised indirectly via evaluation). Done 2026-08-10: coverage added — `interview/state.py`, `orchestration/coordinator.py`, `orchestration/policies.py` direct tests; reader surface and ranking edge cases (6 new tests; parsing already covered). | Done | |
| T-04 | Low | Tests | Refactor | Legacy test debt | `test_question_loading.py`: hard-coded Windows paths, `os.chdir`, unittest-style. `test_question_generator_async.py` duplicates its integration twin. Legacy scope decision. Done 2026-08-10: reviewed and deferred (legacy scope). Note: `tests/test_behavior_test.py` has 4 pre-existing failures (`test_parse_deepseek_thinking*`) caused by the uncommitted `examples/behavior_test.py` CLI-harness rewrite; 3 legacy test files still fail collection on undeclared `tenacity`/`fastapi` deps. Deferred — in ROADMAP.md. | Done | |
| CODE-01 | Medium | Code | Refactor | Legacy TODO/FIXME sweep | 20 hits, all in legacy `src/` (agents, pipelines, thought_generation, run_*.py, `interviewagent_xf_edit_2.py`, `society_of_agents_models.py`). Package and tests: zero hits. Legacy scope decision. Deferred — in ROADMAP.md. | Pending | |
| CODE-02 | Low | Code | Update | Legacy hard-coded model strings | `gpt-4-turbo` (`src/agents/facilitator_agent_async.py:104`, `src/pipelines/interview_pipeline_async.py:61`, `src/pipelines/interviewing_pipeline_template_async.py:112,167`), `gpt-3.5-turbo` (`src/test_thought_generation.py:35`), `claude-3-5-sonnet-20241022` (`src/utils/llm_api_utils_async.py:241`), `GPT_4_TURBO`/`CLAUDE_SONNET` constants (`src/run_*.py`). Legacy scope decision. Deferred — in ROADMAP.md. | Pending | |

## Cross-Reference: MASTER_AUDIT.md

| MASTER_AUDIT item | Plan items | Status note |
|-------------------|------------|-------------|
| P0: fix the two reproduced interview bugs + regression tests | C-01, C-02, T-01 | Done — fixes and tests landed 2026-08-10 |
| P0: remove `repro_interview.py` | CW-01 | Done — removed 2026-08-10 (T-01 landed) |
| P1: remove dead `src/models` files | C-03, C-04 | Pending; C-05 keeps shims + `user_state_models.py` for legacy |
| P1: sync docs with ProgressionType | DOC-01, DOC-02 | Pending — docs also need `_DEFAULT_MODELS`/`default_model()` which post-date the audit |
| P1: commit provider WIP | — | Done — landed in `36914401` and later commits (HEAD `08caa9cd`) |
| P2: install anthropic + sync dev group | D-01 | Pending |
| P2: add CHANGELOG | DOC-04 | Pending |
| Done since audit: pydantic Config→ConfigDict migration | — | Done — zero `class Config:` under `src/bot0_thought_graph` |
| Done since audit: README rewrite | DOC-01 | Done, but already stale again (see DOC-01) |

**Drift note**: the audit's Drift Detection section was written before today's further evolution of the package (default model registry, `topic=` alias, `progression_type` on façade methods, `ProgressionType` in top-level exports, CLI behavior harness). This plan's verification was performed against the current tree; where the audit and the tree disagree, the tree wins.

## Verification Notes

Commands/evidence used for this plan (all run 2026-08-08):

- `git status --short` — untracked `repro_interview.py`, `docs/MASTER_AUDIT.md`; modified `docs/vertical_progression_audit.md`, `examples/behavior_test.py` (user work, excluded from plan).
- `git log -1` — HEAD `08caa9cd` ("added a progression type and removed direct_child").
- `ls -A` on `sandbox/` (empty), `tests/unit/` + `tests/integration/` (only `__init__.py`), `dist/`, `build/`, `logs/` (`xzhang_app.log`), `src/evals_and_comparisons/`.
- Grep (case-insensitive) `deepseek-chat|deepseek-reasoner|gemini-2.0-flash` → zero matches; `gpt-3.5|gpt-4|claude-3|claude-4` → hits only in legacy `src/` (file:line listed in CODE-02).
- Grep `TODO|FIXME|HACK|XXX` → 20 hits, all legacy `src/`; zero in package and tests.
- Grep for importer names (`society_of_agents_models`, `openai_claude_llama_response_basemodels`, `user_state_models`, `compute_similarity`, `youtube_transcriber`, `QA_loader`, `picklethisfile`, `tree.py`, `resume_service`, `llm_service`) → no live importers (only self-references and one commented-out import).
- Grep `from bot0_thought_graph` in `tests/` → coverage map for T-03.
- `.venv/bin/python -c "import anthropic"` → `ModuleNotFoundError`; `import pydantic, pandas, openai, pytest` → pydantic 2.13.4, pandas 3.0.5, openai OK, pytest 9.1.1.
- Live repro of interview bugs (`repro_interview.py`, pre-fix): BUG A log ordering and BUG B non-completion both confirmed.
