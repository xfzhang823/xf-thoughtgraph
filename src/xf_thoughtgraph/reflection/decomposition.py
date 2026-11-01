"""Provider-backed evaluation of whether thoughts merit another level."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from xf_thoughtgraph.providers import GenerationRequest, LLMProvider, ProviderResponseError

from .shared import generate_structured


ExplorationProfile = Literal["focused", "balanced", "rich"]


class DecompositionCandidate(BaseModel):
    """A retained thought that may be decomposed further."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    thought: str = Field(min_length=1)
    description: str | None = None


class DecompositionEvaluationRequest(BaseModel):
    """The path and retained candidates evaluated in one provider call."""

    model_config = ConfigDict(extra="forbid")

    ancestor_path: tuple[str, ...] = Field(min_length=1)
    candidates: tuple[DecompositionCandidate, ...] = Field(min_length=1)
    exploration: ExplorationProfile

    @model_validator(mode="after")
    def candidate_ids_are_unique(self) -> "DecompositionEvaluationRequest":
        ids = [candidate.id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate IDs must be unique")
        return self


class DecompositionDecision(BaseModel):
    """The decomposition decision for one stable candidate ID."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    decompose: StrictBool
    reason: str = Field(min_length=1)


class DecompositionEvaluationResult(BaseModel):
    """Batch decomposition decisions returned by the provider."""

    model_config = ConfigDict(extra="forbid")

    decisions: tuple[DecompositionDecision, ...] = Field(min_length=1)


DECOMPOSITION_EVALUATION_PROMPT = """\
Decide whether each retained thought below is worth decomposing one additional
vertical level. Judge only the expected value of another decomposition step:
whether useful insight remains that justifies another provider call.

Do not judge general candidate quality or relevance, generate children, predict
the number of children, or apply a fixed depth, width, or graph-size rule.

The root is the first item in ancestor_path. The current parent is the last
item in ancestor_path.

Exploration profile:
- focused: decompose only when another level has clear/high value
- balanced: decompose when another level has meaningful value
- rich: decompose when additional useful insight remains

Profile wording changes the evidence threshold only. It must not imply a fixed
depth, width, child count, or graph size.

ancestor_path: {ancestor_path}
root: {root}
current_parent: {current_parent}
candidates:
{candidates}

Return JSON only in this exact shape, with exactly one decision for every
candidate ID and no other IDs:
{{"decisions":[{{"candidate_id":"...","decompose":true,"reason":"..."}}]}}
"""


class DecompositionEvaluationService:
    """Evaluate a complete retained-candidate batch for further decomposition."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1056,
        timeout: float | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def evaluate(self, request: DecompositionEvaluationRequest) -> DecompositionEvaluationResult:
        prompt = DECOMPOSITION_EVALUATION_PROMPT.format(
            ancestor_path=" -> ".join(request.ancestor_path),
            root=request.ancestor_path[0],
            current_parent=request.ancestor_path[-1],
            candidates="\n".join(
                f'- id: {candidate.id}\n  thought: {candidate.thought}\n'
                f'  description: {candidate.description or ""}'
                for candidate in request.candidates
            ),
        )
        result = generate_structured(
            self.provider,
            GenerationRequest(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            ),
            DecompositionEvaluationResult.model_validate,
            error_message="Provider returned an invalid decomposition evaluation",
        )
        expected = {candidate.id for candidate in request.candidates}
        returned = [decision.candidate_id for decision in result.decisions]
        if len(returned) != len(expected) or set(returned) != expected or len(set(returned)) != len(returned):
            raise ProviderResponseError(
                "Provider returned malformed decomposition decisions: candidate IDs must match exactly"
            )
        return result

