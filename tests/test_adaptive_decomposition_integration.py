from dataclasses import dataclass
import json
import re

import pytest

from xf_thoughtgraph import ThoughtGraphEngine
from xf_thoughtgraph.providers import GenerationRequest, GenerationResult


def horizontal_response(*names):
    thoughts = ",".join(
        f'{{"thought":"{name}","description":"A direction"}}' for name in names
    )
    return '{"idea":"Clinical research recruitment","thoughts":[' + thoughts + "]}"


def vertical_response(*names):
    children = ",".join(
        f'{{"name":"{name}","description":"Useful concept"}}' for name in names
    )
    return (
        '{"idea":"Clinical research recruitment","thought":"parent",'
        f'"sub_thoughts":[{children}]}}'
    )


@dataclass
class DecompositionProvider:
    vertical_responses: list[str]
    decisions: dict[str, bool] | None = None
    decomposition_response: str | None = None
    decomposition_failure: Exception | None = None

    def __post_init__(self):
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        if "Decide whether each retained thought" in request.prompt:
            if self.decomposition_failure is not None:
                raise self.decomposition_failure
            if self.decomposition_response is not None:
                response = self.decomposition_response
            else:
                ids = re.findall(r"- id: ([^\n]+)", request.prompt)
                decisions = self.decisions or {}
                response = json.dumps(
                    {
                        "decisions": [
                            {
                                "candidate_id": candidate_id,
                                "decompose": decisions.get(candidate_id, True),
                                "reason": "test decision",
                            }
                            for candidate_id in reversed(ids)
                        ]
                    }
                )
            return GenerationResult(response, "fake", request.model)
        if not self.vertical_responses:
            raise RuntimeError("unexpected generation call")
        return GenerationResult(self.vertical_responses.pop(0), "fake", request.model)


def test_mixed_decisions_retain_terminals_and_recurse_only_true_candidates():
    provider = DecompositionProvider(
        [
            horizontal_response("Architecture"),
            vertical_response("Recruitment planning", "Recruitment outcomes"),
            vertical_response(),
        ],
        decisions={"child-1": False, "child-2": True},
    )

    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    children = graph.root.children[0].children
    assert [child.name for child in children] == [
        "Recruitment planning",
        "Recruitment outcomes",
    ]
    assert children[0].children == []
    assert len([r for r in provider.requests if "Decide whether" in r.prompt]) == 1
    assert len(provider.requests) == 4


def test_decision_mapping_is_independent_of_response_order():
    provider = DecompositionProvider(
        [
            horizontal_response("Architecture"),
            vertical_response("Recruitment strategy", "Recruitment outcomes"),
            vertical_response(),
        ],
        decomposition_response=(
            '{"decisions":['
            '{"candidate_id":"child-2","decompose":false,"reason":"terminal"},'
            '{"candidate_id":"child-1","decompose":true,"reason":"useful"}]}'
        ),
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert any(
        "Recruitment strategy" in request.prompt
        for request in provider.requests
        if "vertically expanding" in request.prompt
    )
    assert graph.root.children[0].children[1].children == []


def test_evaluator_failure_falls_back_to_deterministic_continuation():
    provider = DecompositionProvider(
        [horizontal_response("Architecture"), vertical_response("Recruitment planning"), vertical_response()],
        decomposition_failure=TimeoutError("timed out"),
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert graph.root.children[0].children[0].name == "Recruitment planning"
    assert any(
        decision.reason == "decomposition_fallback"
        for decision in engine.last_exploration_trace
    )


@pytest.mark.parametrize(
    "response",
    [
        '{"decisions":[{"candidate_id":"child-1","decompose":true,"reason":"missing"}]}',
        '{"decisions":[{"candidate_id":"child-1","decompose":true,"reason":"one"},{"candidate_id":"child-1","decompose":false,"reason":"duplicate"}]}',
        '{"decisions":[{"candidate_id":"unknown","decompose":true,"reason":"unknown"},{"candidate_id":"child-2","decompose":true,"reason":"known"}]}',
    ],
)
def test_malformed_decision_ids_use_fallback(response):
    provider = DecompositionProvider(
        [
            horizontal_response("Architecture"),
            vertical_response("Recruitment planning", "Recruitment outcomes"),
            vertical_response(),
            vertical_response(),
        ],
        decomposition_response=response,
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert len(graph.root.children[0].children[0].children) == 0
    assert any(
        decision.reason == "decomposition_fallback"
        for decision in engine.last_exploration_trace
    )


def test_no_eligible_candidates_means_no_decomposition_call(monkeypatch):
    monkeypatch.setattr(
        ThoughtGraphEngine,
        "_is_relevant_candidate",
        classmethod(lambda cls, *args, **kwargs: False),
    )
    provider = DecompositionProvider(
        [horizontal_response("Architecture"), vertical_response("Recruitment planning")]
    )
    engine = ThoughtGraphEngine(provider)
    engine.generate_thought_graph("Clinical research recruitment", exploration="rich")

    assert not any("Decide whether" in request.prompt for request in provider.requests)


@pytest.mark.parametrize("guard", ["endpoint", "branch", "relevance"])
def test_existing_authoritative_guards_prevent_evaluation(monkeypatch, guard):
    if guard == "relevance":
        monkeypatch.setattr(
            ThoughtGraphEngine,
            "_is_relevant_candidate",
            classmethod(lambda cls, *args, **kwargs: False),
        )
        child = "Strategy operations"
        exploration = "rich"
    elif guard == "branch":
        child = "Recruitment strategy"
        exploration = "focused"
    else:
        child = "Final summary"
        exploration = "balanced"

    provider = DecompositionProvider(
        [horizontal_response("Architecture"), vertical_response(child)]
    )
    ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment", exploration=exploration
    )

    assert len(provider.requests) == 2
    assert not any("Decide whether" in request.prompt for request in provider.requests)


def test_profiles_do_not_create_fixed_graph_dimensions():
    depths = []
    calls = []
    for profile in ("focused", "balanced", "rich"):
        provider = DecompositionProvider(
            [horizontal_response("Architecture"), vertical_response("Strategy operations")],
            decisions={"child-1": False},
        )
        graph = ThoughtGraphEngine(provider).generate_thought_graph(
            "Clinical research recruitment", exploration=profile
        )
        depths.append(graph.depth)
        calls.append(len(provider.requests))

    assert depths == [2, 2, 2]
    assert calls == [3, 3, 3]


def test_decomposition_call_counts_against_adaptive_provider_budget(monkeypatch):
    monkeypatch.setattr(ThoughtGraphEngine, "_ADAPTIVE_MAX_PROVIDER_CALLS", 3)
    provider = DecompositionProvider(
        [horizontal_response("Architecture"), vertical_response("Recruitment planning")],
        decisions={"child-1": False},
    )
    engine = ThoughtGraphEngine(provider)
    engine.generate_thought_graph("Clinical research recruitment", exploration="balanced")

    assert len(provider.requests) == 3
    assert engine._adaptive_provider_calls == 3
