# Prompts

This package owns graph-generation prompt templates as public, overridable
constants.

## Responsibilities

- `thought_generation_prompt_templates.py`: horizontal, vertical, and
  concept/detail generation prompts.
- `__init__.py`: the stable prompt-constant exports.

Prompt templates define the provider-facing instructions and response shapes;
the engine supplies runtime concepts, progression, and model settings.

## Boundaries

Prompts do not invoke providers, parse responses, construct graph nodes, or
implement traversal/reflection policy. Graph generation consumes the horizontal,
vertical, detail, and ranking templates.
