from dataclasses import dataclass

import pytest

from xf_thoughtgraph.reflection import (
    DecompositionCandidate,
    DecompositionEvaluationRequest,
    DecompositionEvaluationService,
)
from xf_thoughtgraph.providers import GenerationRequest, GenerationResult, ProviderResponseError


@dataclass
class FakeProvider:
    response: str

    def __post_init__(self):
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        return GenerationResult(self.response, "fake", request.model)


def request(profile="balanced"):
    return DecompositionEvaluationRequest(
        ancestor_path=("root idea", "current parent"),
        candidates=(
            DecompositionCandidate(id="c-1", thought="first", description="First thought"),
            DecompositionCandidate(id="c-2", thought="second", description="Second thought"),
            DecompositionCandidate(id="c-3", thought="third"),
        ),
        exploration=profile,
    )


@pytest.mark.parametrize(
    ("decisions", "expected"),
    [
        ([True, True, True], [True, True, True]),
        ([False, False, False], [False, False, False]),
        ([True, False, True], [True, False, True]),
    ],
)
def test_evaluates_the_full_batch(decisions, expected):
    # Deliberately return decisions in a different order than the request.
    response = {
        "decisions": [
            {"candidate_id": candidate_id, "decompose": decision, "reason": "evidence"}
            for candidate_id, decision in zip(("c-3", "c-1", "c-2"), (decisions[2], decisions[0], decisions[1]))
        ]
    }
    import json

    provider = FakeProvider(json.dumps(response))
    result = DecompositionEvaluationService(provider, model="fake-model").evaluate(request())

    assert len(provider.requests) == 1
    assert {decision.candidate_id: decision.decompose for decision in result.decisions} == dict(
        zip(("c-1", "c-2", "c-3"), expected)
    )


@pytest.mark.parametrize(
    ("profile", "phrase"),
    [("focused", "clear/high value"), ("balanced", "meaningful value"), ("rich", "useful insight")],
)
def test_profile_semantics_are_prompt_context_not_fixed_graph_controls(profile, phrase):
    provider = FakeProvider('{"decisions":[{"candidate_id":"c-1","decompose":true,"reason":"useful"},{"candidate_id":"c-2","decompose":false,"reason":"terminal"},{"candidate_id":"c-3","decompose":true,"reason":"useful"}]}')
    DecompositionEvaluationService(provider, model="fake-model").evaluate(request(profile))
    prompt = provider.requests[0].prompt
    assert f"{profile}:" in prompt
    assert phrase in prompt
    assert "fixed depth" in prompt
    assert "root: root idea" in prompt
    assert "current_parent: current parent" in prompt


@pytest.mark.parametrize(
    "response",
    [
        '{"decisions":[{"candidate_id":"c-1","decompose":true,"reason":"only one"},{"candidate_id":"c-2","decompose":false,"reason":"missing c-3"}]}',
        '{"decisions":[{"candidate_id":"c-1","decompose":true,"reason":"one"},{"candidate_id":"c-1","decompose":false,"reason":"duplicate"},{"candidate_id":"c-3","decompose":true,"reason":"unknown c-2"}]}',
        '{"decisions":[{"candidate_id":"unknown","decompose":true,"reason":"unknown"},{"candidate_id":"c-2","decompose":false,"reason":"known"},{"candidate_id":"c-3","decompose":true,"reason":"known"}]}',
        '{"decisions":[{"candidate_id":"c-1","decompose":"yes","reason":"not a boolean"},{"candidate_id":"c-2","decompose":false,"reason":"known"},{"candidate_id":"c-3","decompose":true,"reason":"known"}]}',
        "not json",
    ],
)
def test_malformed_provider_responses_are_normalized(response):
    with pytest.raises(ProviderResponseError, match="invalid decomposition evaluation|candidate IDs"):
        DecompositionEvaluationService(FakeProvider(response), model="fake-model").evaluate(request())


def test_request_rejects_empty_paths_and_duplicate_candidate_ids():
    with pytest.raises(ValueError):
        DecompositionEvaluationRequest(ancestor_path=(), candidates=(DecompositionCandidate(id="a", thought="x"),), exploration="balanced")
    with pytest.raises(ValueError, match="unique"):
        DecompositionEvaluationRequest(
            ancestor_path=("root",),
            candidates=(DecompositionCandidate(id="a", thought="x"), DecompositionCandidate(id="a", thought="y")),
            exploration="balanced",
        )
