"""Offline provider and graph fixtures shared by the runnable examples."""

from dataclasses import dataclass

from xf_thoughtgraph.models import IndexedIdeaJSONModel
from xf_thoughtgraph.providers import GenerationRequest, GenerationResult


@dataclass
class FakeProvider:
    responses: list[str]

    def generate(self, request: GenerationRequest) -> GenerationResult:
        del request
        return GenerationResult(self.responses.pop(0), "fake", "example-model")


def graph() -> IndexedIdeaJSONModel:
    return IndexedIdeaJSONModel.model_validate(
        {
            "idea": "systems",
            "thoughts": [
                {
                    "thought_index": 0,
                    "thought": "hardware",
                    "description": "Physical design",
                    "sub_thoughts": [
                        {
                            "sub_thought_index": 0,
                            "name": "requirements",
                            "description": "Define needs",
                        }
                    ],
                }
            ],
        }
    )
