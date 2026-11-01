"""Run the concept-first thought-generation workflow offline."""

import json

from support import FakeProvider

from xf_thoughtgraph import ProgressionType, ThoughtGraphEngine, generate_thought_graph


HORIZONTAL = (
    '{"idea":"systems","thoughts":['
    '{"thought":"hardware","description":"Physical design"},'
    '{"thought":"software","description":"Program logic"}]}'
)
VERTICAL = (
    '{"idea":"systems","thought":"hardware","sub_thoughts":['
    '{"name":"requirements","description":"Define needs"},'
    '{"name":"design","description":"Choose structure"}]}'
)


# The fake provider makes this example deterministic and network-free.
provider = FakeProvider([HORIZONTAL, VERTICAL, HORIZONTAL, HORIZONTAL, VERTICAL, VERTICAL])
engine = ThoughtGraphEngine(provider, model="example-model")

subtopics = engine.generate_subtopics("systems", max_subtopics=2)
details = engine.expand_subtopic("systems", "hardware", max_details=2)
thought_array = engine.generate_array_of_thoughts("systems", max_subtopics=2)
graph = engine.generate_thought_graph("systems", horizontal=2, vertical=2)

print("subtopics:", subtopics)
print("details:", details)
print("thought_array:")
print(thought_array.model_dump_json(indent=2))
print("thought_graph:")
print(json.dumps(graph.model_dump(), indent=2))

# The root-level convenience API delegates to the same canonical engine.
simple_provider = FakeProvider([
    '{"idea":"systems","thoughts":[{"thought":"hardware",'
    '"description":"Physical design"}]}',
    '{"idea":"systems","thought":"hardware","sub_thoughts":[]}',
])
simple_graph = generate_thought_graph(
    "systems",
    exploration="balanced",
    progression_type=ProgressionType.PREREQUISITE_DEPENDENCY,
    provider=simple_provider,
    model="example-model",
)
print("simple thought_graph:")
print(json.dumps(simple_graph.model_dump(), indent=2))
