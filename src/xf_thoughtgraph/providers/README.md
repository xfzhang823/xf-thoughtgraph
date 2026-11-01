# Providers

This package defines the provider boundary used by thought generation and
reflection.

## Responsibilities

- `contracts.py`: `LLMProvider`, `AsyncLLMProvider`, generation request/result
  types, and normalized provider errors.
- `create_provider()` and `default_model()`: named-provider construction and
  existing model-default/environment-override resolution.
- Provider modules: synchronous and asynchronous OpenAI, Anthropic, Gemini,
  and DeepSeek adapters.
- `openai_compatible.py`: shared request/response behavior for compatible
  provider APIs.

## Boundaries

Providers do not decide graph structure, exploration profiles, decomposition,
prompt semantics, persistence, or traversal. The engine supplies a normalized
`GenerationRequest`; adapters return a normalized `GenerationResult`.

SDK adapter modules are lazy, while provider construction is explicit through
the engine, `create_provider()`, or direct adapter injection. This package may
load repository environment values without overriding existing variables, but
it does not make a provider request during package import.
