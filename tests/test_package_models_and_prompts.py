from xf_thoughtgraph.models import (
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    IndexedSubThoughtJSONModel,
    IndexedThoughtJSONModel,
)
from xf_thoughtgraph.prompts import THOUGHT_GENERATION_PROMPT


def test_thought_model_defaults_and_serialization():
    model = IdeaJSONModel(idea="climate")
    assert model.thoughts is None
    assert model.model_dump() == {"idea": "climate", "thoughts": None}


def test_indexed_thought_hierarchy_is_validated():
    model = IndexedIdeaJSONModel(
        idea="systems",
        thoughts=[
            IndexedThoughtJSONModel(
                thought_index=0,
                thought="requirements",
                sub_thoughts=[
                    IndexedSubThoughtJSONModel(
                        sub_thought_index=0,
                        name="scope",
                        description="Define scope.",
                    )
                ],
            )
        ],
    )
    assert model.thoughts[0].sub_thoughts[0].sub_thought_index == 0


def test_prompt_exports_and_rendering():
    rendered = THOUGHT_GENERATION_PROMPT.format(idea="AI", num_sub_thoughts=3)
    assert '"idea": "AI"' in rendered
    assert "{num_sub_thoughts}" not in rendered
