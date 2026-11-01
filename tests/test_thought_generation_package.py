from dataclasses import dataclass

import pytest

from xf_thoughtgraph.models import IdeaJSONModel, ProgressionType
from xf_thoughtgraph.providers import GenerationRequest, GenerationResult, ProviderRequestError
from xf_thoughtgraph.storage import JsonRepository, MemoryRepository
from xf_thoughtgraph.thought_generation import (
    HorizontalGenerationRequest,
    ThoughtGraphEngine,
    IndexedThoughtReader,
    ThoughtReader,
    VerticalGenerationRequest,
    extract_json,
    index_idea,
)


@dataclass
class FakeProvider:
    responses: list[str]

    def __post_init__(self):
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        if not self.responses:
            raise ProviderRequestError("no fake response")
        return GenerationResult(self.responses.pop(0), "fake", request.model)


HORIZONTAL = '{"idea":"systems","thoughts":[{"thought":"hardware","description":"Physical design"},{"thought":"software","description":"Program logic"}]}'
VERTICAL = '{"idea":"systems","thought":"hardware","sub_thoughts":[{"name":"requirements","description":"Define needs"},{"name":"design","description":"Choose structure"}]}'
CLUSTERS = '{"idea":"systems","clusters":[{"name":"architecture","description":"System structure","thoughts":["hardware","software"]}]}'


def test_horizontal_generation_is_in_memory_and_provider_injected(tmp_path):
    provider = FakeProvider([HORIZONTAL])
    engine = ThoughtGraphEngine(provider)
    result = engine.generate(HorizontalGenerationRequest(idea="systems", model="fake-model"))
    assert result.idea == "systems"
    assert [thought.thought for thought in result.thoughts] == ["hardware", "software"]
    assert provider.requests[0].model == "fake-model"
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(RuntimeError):
        engine.save("graph", result)


def test_vertical_expansion_and_hierarchy_preserve_order():
    provider = FakeProvider([VERTICAL])
    engine = ThoughtGraphEngine(provider)
    result = engine.expand(
        VerticalGenerationRequest(idea="systems", thought="hardware", model="fake-model")
    )
    assert result.thought == "hardware"
    assert [item.name for item in result.sub_thoughts] == ["requirements", "design"]

    idea = IdeaJSONModel.model_validate({"idea": "systems", "thoughts": [result]})
    indexed = index_idea(idea)
    assert indexed.thoughts[0].thought_index == 0
    assert [item.sub_thought_index for item in indexed.thoughts[0].sub_thoughts] == [0, 1]
    assert ThoughtReader(idea).get_sub_thoughts_for_thought("hardware")[0]["name"] == "requirements"
    assert IndexedThoughtReader(indexed).get_sub_thoughts_for_thought(0)[1]["name"] == "design"


def test_prerequisite_dependency_progression_is_accepted_and_instructed():
    provider = FakeProvider([VERTICAL])
    engine = ThoughtGraphEngine(provider)

    engine.expand(
        VerticalGenerationRequest(
            idea="systems",
            thought="hardware",
            model="fake-model",
            progression_type="prerequisite_dependency",
        )
    )

    prompt = " ".join(provider.requests[0].prompt.split())
    assert '"prerequisite_dependency"' in prompt
    assert "MUST be satisfied, completed, or understood" in prompt
    assert "strict prerequisite direction" in prompt


def test_progression_type_defaults_and_normalizes_compatible_strings():
    default_request = VerticalGenerationRequest(
        idea="systems", thought="hardware", model="fake-model"
    )
    string_request = VerticalGenerationRequest(
        idea="systems",
        thought="hardware",
        model="fake-model",
        progression_type="prerequisite_dependency",
    )

    assert default_request.progression_type is ProgressionType.IMPLEMENTATION_STEPS
    assert string_request.progression_type is ProgressionType.PREREQUISITE_DEPENDENCY
    with pytest.raises(ValueError):
        VerticalGenerationRequest(
            idea="systems",
            thought="hardware",
            model="fake-model",
            progression_type="not-a-progression",
        )


def test_expand_all_uses_deterministic_input_order():
    provider = FakeProvider([VERTICAL.replace('"hardware"', '"hardware"', 1), VERTICAL.replace('hardware', 'software')])
    engine = ThoughtGraphEngine(provider)
    idea = IdeaJSONModel.model_validate({"idea": "systems", "thoughts": [{"thought": "hardware", "description": "Physical"}, {"thought": "software", "description": "Logic"}]})
    result = engine.expand_all(idea, model="fake-model")
    assert [request.prompt.split("Main Thought: ")[1].split("\n")[0] for request in provider.requests] == ["hardware", "software"]
    assert [item.description for item in result.thoughts] == ["Physical", "Logic"]


def test_optional_clustering_and_explicit_persistence(tmp_path):
    repository = MemoryRepository()
    provider = FakeProvider([HORIZONTAL, CLUSTERS])
    engine = ThoughtGraphEngine(provider, repository=repository)
    result = engine.generate(
        HorizontalGenerationRequest(
            idea="systems", model="fake-model", num_clusters=2, top_n=1
        )
    )
    assert result.thoughts[0].thought == "architecture"
    engine.save("graph", result)
    assert repository.load("graph")["idea"] == "systems"

    json_repository = JsonRepository(tmp_path)
    ThoughtGraphEngine(FakeProvider([]), repository=json_repository).save("empty", {"ok": True})
    assert json_repository.load("empty") == {"ok": True}


def test_parsing_rejects_empty_or_malformed_output():
    assert extract_json("prefix {\"idea\": \"x\",} suffix") == {"idea": "x"}
    with pytest.raises(ValueError):
        extract_json("")
    with pytest.raises(ValueError):
        extract_json("not json")
    with pytest.raises(ValueError):
        extract_json('{"idea":')


def test_provider_output_schema_failure_is_reported():
    engine = ThoughtGraphEngine(FakeProvider(['{"idea":"systems","thoughts":[{"description":"missing name"}]}']))
    with pytest.raises(ValueError, match="Invalid idea thought graph"):
        engine.generate(HorizontalGenerationRequest(idea="systems", model="fake-model"))


from xf_thoughtgraph.models import IdeaClusterJSONModel
from xf_thoughtgraph.thought_generation.ranking import convert_clusters_to_idea, select_clusters


def test_reader_surface_covers_idea_thoughts_and_descriptions():
    idea = IdeaJSONModel.model_validate(
        {
            "idea": "systems",
            "thoughts": [
                {
                    "thought": "hardware",
                    "description": "Physical design",
                    "sub_thoughts": [{"name": "requirements", "description": "Define needs"}],
                }
            ],
        }
    )
    reader = ThoughtReader(idea)
    assert reader.get_idea() == "systems"
    assert reader.get_thoughts() == ["hardware"]
    assert reader.get_thoughts_and_descriptions() == [
        {"thought": "hardware", "description": "Physical design"}
    ]
    indexed = IndexedThoughtReader(index_idea(idea))
    assert indexed.get_thoughts() == [{"thought_index": 0, "thought": "hardware"}]
    assert indexed.get_thoughts_and_descriptions()[0]["description"] == "Physical design"
    assert indexed.dump_all()["idea"] == "systems"


def test_ranking_helpers_validate_and_convert_clusters():
    with pytest.raises(ValueError, match="no clusters"):
        convert_clusters_to_idea(IdeaClusterJSONModel(idea="systems", clusters=[]))
    converted = convert_clusters_to_idea(
        IdeaClusterJSONModel(
            idea="systems",
            clusters=[
                {"name": "architecture", "description": "System structure", "thoughts": ["hardware", "software"]}
            ],
        )
    )
    assert converted.thoughts[0].thought == "architecture"
    assert converted.thoughts[0].sub_thoughts is None


def test_select_clusters_parses_provider_response_and_rejects_bad_shape():
    provider = FakeProvider([CLUSTERS])
    result = select_clusters(
        provider,
        IdeaJSONModel.model_validate(
            {"idea": "systems", "thoughts": [{"thought": "hardware", "description": "Physical design"}]}
        ),
        model="fake-model",
        num_clusters=1,
        top_n=1,
    )
    assert result.clusters[0].name == "architecture"

    bad = FakeProvider(['{"idea": "systems", "clusters": [{"name": "x"}]}'])
    with pytest.raises(ValueError, match="Invalid cluster response"):
        select_clusters(
            bad,
            IdeaJSONModel.model_validate(
                {"idea": "systems", "thoughts": [{"thought": "hardware", "description": "Physical design"}]}
            ),
            model="fake-model",
            num_clusters=1,
            top_n=1,
        )