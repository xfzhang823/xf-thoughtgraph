"""Tests for the thin root-level consumer API."""

import pytest

import xf_thoughtgraph.public_api as public_api
from xf_thoughtgraph import ProgressionType


class _FakeEngine:
    instances = []

    def __init__(self, provider, *, model=None):
        self.provider = provider
        self.model = model
        self.calls = []
        self.instances.append(self)

    def generate_thought_graph(self, **kwargs):
        self.calls.append(kwargs)
        return object()


def test_root_export_is_importable():
    from xf_thoughtgraph import ThoughtGraphEngine, generate_thought_graph

    assert callable(generate_thought_graph)
    assert ThoughtGraphEngine is not None


def test_root_function_delegates_topic_exploration_provider_and_model(monkeypatch):
    monkeypatch.setattr(public_api, "ThoughtGraphEngine", _FakeEngine)
    provider = object()

    result = public_api.generate_thought_graph(
        "hospital emergency department operations",
        exploration="focused",
        provider=provider,
        model="test-model",
    )

    engine = _FakeEngine.instances[-1]
    assert result is not None
    assert engine.provider is provider
    assert engine.model == "test-model"
    assert engine.calls == [{
        "topic": "hospital emergency department operations",
        "exploration": "focused",
        "progression_type": ProgressionType.IMPLEMENTATION_STEPS,
    }]


def test_root_function_forwards_explicit_progression_type(monkeypatch):
    monkeypatch.setattr(public_api, "ThoughtGraphEngine", _FakeEngine)
    provider = object()

    public_api.generate_thought_graph(
        "hospital emergency department operations",
        progression_type=ProgressionType.PREREQUISITE_DEPENDENCY,
        provider=provider,
    )

    engine = _FakeEngine.instances[-1]
    assert engine.calls == [{
        "topic": "hospital emergency department operations",
        "exploration": "balanced",
        "progression_type": ProgressionType.PREREQUISITE_DEPENDENCY,
    }]


def test_root_function_defaults_to_implementation_steps(monkeypatch):
    monkeypatch.setattr(public_api, "ThoughtGraphEngine", _FakeEngine)

    public_api.generate_thought_graph("systems", provider="openai")

    assert _FakeEngine.instances[-1].calls == [{
        "topic": "systems",
        "exploration": "balanced",
        "progression_type": ProgressionType.IMPLEMENTATION_STEPS,
    }]


def test_root_function_preserves_engine_result_identity(monkeypatch):
    sentinel = object()

    class ResultEngine(_FakeEngine):
        def generate_thought_graph(self, **kwargs):
            self.calls.append(kwargs)
            return sentinel

    monkeypatch.setattr(public_api, "ThoughtGraphEngine", ResultEngine)

    assert public_api.generate_thought_graph("systems", provider="openai") is sentinel


def test_provider_is_required_when_no_provider_configuration_is_available(monkeypatch):
    constructor_called = False

    def fail_constructor(*args, **kwargs):
        nonlocal constructor_called
        constructor_called = True
        raise AssertionError("engine should not be constructed")

    monkeypatch.setattr(public_api, "ThoughtGraphEngine", fail_constructor)

    with pytest.raises(ValueError, match="provider is required"):
        public_api.generate_thought_graph("systems")

    assert constructor_called is False
