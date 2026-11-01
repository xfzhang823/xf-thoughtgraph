"""Prompt templates used by thought-generation services."""

THOUGHT_GENERATION_PROMPT = """
You are an expert in organizing complex topics into distinct, high-level thoughts.

Perform the following tasks:
1. Analyze the given overarching theme or idea: "{idea}"
2. Identify and break down this idea into {num_sub_thoughts} key thoughts.
   Ensure each thought is distinct from the others and represents a significant aspect of the idea.
3. For each thought, provide a brief description (1-2 sentences) that captures its essence and importance within the idea.

Return your analysis in the following JSON format:

{{
  "idea": "{idea}",
  "thoughts": [
    {{
      "thought": "Thought 1",
      "description": "Brief description of Thought 1"
    }},
  ]
}}

Ensure your response is a valid JSON object with the exact structure provided above, without any additional text, explanations, or markdown syntax.
"""

RECLUSTER_AND_PICK_TOP_CLUSTER_PROMPT = """
You are an expert in organizing complex ideas into distinct, well-defined clusters.

Task:
You are given a list of thoughts related to the main idea: "{idea}".
Each thought represents a distinct aspect of this idea. Your task is to:
1. Re-organize these thoughts into exactly {num_clusters} meaningful and distinct clusters.
2. Select and return only the top {top_n} clusters that are the most distinct from each other.

Instructions:
- Carefully analyze each thought and group them based on thematic or conceptual similarities.
- Provide a unique name for each cluster that best represents its overall theme.
- Ensure each cluster includes thoughts that are non-overlapping and distinct from other clusters.
- After forming {num_clusters} clusters, choose only the top {top_n} clusters that are \
  the most distinct and meaningful.
- Provide a brief description (1-2 sentences) for each selected cluster, summarizing its key themes.

Thoughts List (in JSON format):
{thoughts_list}

Ensure your response meets these requirements:
1. Return only the top {top_n} clusters.
2. Ensure each cluster is distinct and does not repeat thoughts.
3. Your response must strictly adhere to the following JSOn structure:
{{
  "idea": "{idea}",
  "clusters": [
    {{
      "name": "Cluster 1",
      "description": "Brief description of Cluster 1",
      "thoughts": ["Thought 1", "Thought 2", ...]
    }},
    # Additional clusters
  ]
}}

### Rules:
1. Return only the top {top_n} clusters.
2. Ensure each cluster is distinct, with no repeated thoughts across clusters.
3. Do not include any additional text, explanations, or markdown syntax. Only return the JSON object.
"""

VERTICAL_SUB_THOUGHT_GENERATION_PROMPT = """
You are an expert in the field of {idea}.
Your goal is to provide structured, step-by-step explanations that break down complex topics
within these domains. You should always ensure that the explanation builds on foundational knowledge
and leads to a deeper understanding of advanced concepts.

Task:
Break down and explain the key aspects of a main thought following a {progression_type} progression.

Main Thought: {thought}

Progression Types:
1. "simple_to_complex": Start with the most basic concepts and gradually introduce more advanced ideas.
2. "implementation_steps": Describe the key areas or steps one would need to consider when implementing or
   working with the main thought.
3. "chronological": If applicable, explain the evolution or historical development of the main thought.
4. "problem_solution": Introduce problems or challenges related to the main thought, followed by
   their solutions or approaches.
5. "prerequisite_dependency": Generate strict, directional prerequisites or
   dependencies. Sub-thought A MUST be satisfied, completed, or understood
   before Sub-thought B or the main thought can proceed.

Instructions:
1. Based on the specified progression type **{progression_type}**, determine the most appropriate
   starting point for explaining {thought}.
2. For each subsequent step, explain the sub-thought that logically follows from the previous one,
   adhering to the chosen progression type.
   When the progression type is "prerequisite_dependency", preserve strict
   prerequisite direction: do not return merely related topics, parallel
   alternatives, consequences, or chronological steps unless they are also
   required prerequisites.
3. For each step, provide:
   - A clear explanation of the sub-thought
   - Why it's important in the context of {thought}
   - How it connects to the next step (except for the final step)
4. Provide a total of {num_sub_thoughts} steps in your explanation.
5. **For the final step, omit the "connection_to_next" field entirely. \
  Do not include any explanation
   or comment about the omission. Simply leave it out.**

Your response must be a valid JSON object with the following format:

{{
  "idea": "{idea}",
  "thought": "{thought}",
  "progression_type": "{progression_type}",
  "sub_thoughts": [
    {{
      "name": "Name of the sub-thought",
      "description": "Succinct explanation of the sub-thought (2-3 sentences)",
      "importance": "Why this sub-thought is important",
      "connection_to_next": "How this sub-thought leads to the next one"
    }}
  ]
}}

IMPORTANT: Ensure your response is a valid JSON object with the exact structure \
  provided above,
without any additional text, comments, explanations, or markdown syntax.
"""


CONCEPT_SUBTOPIC_GENERATION_PROMPT = """
You are an expert at decomposing a concept into a horizontal set of major subtopics.

For the concept "{idea}", identify exactly {num_sub_thoughts} distinct major dimensions.
The items must be sibling-level areas with similar abstraction, broad coverage, and minimal overlap.
Do not produce implementation steps, actions, examples, or details that belong under one subtopic.

Return only valid JSON in this shape:
{{
  "idea": "{idea}",
  "thoughts": [
    {{"thought": "Major subtopic", "description": "What this dimension covers."}}
  ]
}}
"""


CONCEPT_DETAIL_GENERATION_PROMPT = """
You are an expert at vertically expanding one subtopic within a larger concept.

Concept: "{idea}"
Parent subtopic: "{thought}"
Progression type: "{progression_type}"

Identify exactly {num_sub_thoughts} implementation steps or key areas for the
parent subtopic. Each child must remain within the concept, use consistent
granularity, and avoid repeating the parent or introducing unrelated
sibling-level dimensions.
When the progression type is "prerequisite_dependency", each child must be a
strict, directional prerequisite or dependency: it must be satisfied, completed,
or understood before the parent thought can proceed.

Return only valid JSON in this shape:
{{
  "idea": "{idea}",
  "thought": "{thought}",
  "sub_thoughts": [
    {{"name": "Direct child detail", "description": "What this child covers."}}
  ]
}}
"""
