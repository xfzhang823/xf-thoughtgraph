"""Stateful adaptive graph traversal used by :class:`ThoughtGraphEngine`."""

from collections import deque
from dataclasses import dataclass
from enum import Enum

from xf_thoughtgraph.models import (
    AdaptiveExplorationSummary,
    ProgressionType,
    ThoughtNode,
)
from xf_thoughtgraph.prompts import (
    ADAPTIVE_CONCEPT_DETAIL_GENERATION_PROMPT,
    ADAPTIVE_CONCEPT_SUBTOPIC_GENERATION_PROMPT,
)

from .adaptive_policy import (
    graph_depth,
    is_marginally_valuable_candidate,
    is_meaningful_candidate,
    is_natural_endpoint,
    is_relevant_candidate,
    profile_branch_overlap_limit,
    profile_marginal_value_limit,
    profile_overlap_limit,
    profile_relevance_limit,
    token_overlap,
    tokens,
)
from .requests import _DEFAULT_MAX_TOKENS


class _ExplorationReason(str, Enum):
    """Stable internal categories for adaptive continuation diagnostics."""

    BRANCH_PRUNED = "branch_pruned"
    CALL_BUDGET = "call_budget"
    DEPTH_LIMIT = "depth_limit"
    EXPANSION_BUDGET = "expansion_budget"
    INSUFFICIENT_DISTINCTNESS = "insufficient_distinctness"
    INSUFFICIENT_NOVELTY = "insufficient_novelty"
    INSUFFICIENT_RELEVANCE = "insufficient_relevance"
    INSUFFICIENT_MARGINAL_VALUE = "insufficient_marginal_value"
    DECOMPOSITION_FALLBACK = "decomposition_fallback"
    DECOMPOSITION_TERMINAL = "decomposition_terminal"
    INTERNAL_CANDIDATE_LIMIT = "internal_candidate_limit"
    MATERIAL_DISTINCT = "materially_distinct"
    MEANINGFUL_CHILDREN = "meaningful_children"
    NATURAL_ENDPOINT = "natural_endpoint"
    NO_CANDIDATE = "no_candidate"
    NO_CHILDREN = "no_children"
    NODE_BUDGET = "node_budget"


@dataclass(frozen=True)
class _ExplorationDecision:
    """Recorded adaptive continuation decision for diagnostics and tests."""

    axis: str
    action: str
    reason: _ExplorationReason
    level: int
    thought: str | None = None


class AdaptiveTraversalMixin:
    """Implement adaptive traversal against the engine's existing state/API."""

    def _generate_adaptive_graph(
        self,
        concept: str,
        *,
        exploration: str,
        model: str | None,
        progression_type: ProgressionType,
    ) -> ThoughtNode:
        root = ThoughtNode(name=concept)
        self._adaptive_node_count = 1
        root.children = self._generate_adaptive_horizontal(
            concept, exploration=exploration, model=model
        )
        pending = deque(
            (child, 1, [concept, child.name]) for child in root.children
        )
        while pending and not self._adaptive_safety_stopped:
            node, level, path = pending.popleft()
            next_children = self._expand_adaptive_node(
                node,
                concept,
                exploration=exploration,
                level=level,
                path=path,
                model=model,
                progression_type=progression_type,
            )
            pending.extend(
                (child, level + 1, [*path, child.name])
                for child in next_children
            )
        return root

    def _generate_adaptive_horizontal(
        self, concept: str, *, exploration: str, model: str | None
    ) -> list[ThoughtNode]:
        selected: list[ThoughtNode] = []
        overlap_limit = self._profile_overlap_limit(exploration)

        while len(selected) < self._ADAPTIVE_MAX_HORIZONTAL:
            if self._adaptive_safety_stopped:
                break
            if not self._consume_adaptive_work(level=0):
                break
            batch_size = self._ADAPTIVE_MAX_HORIZONTAL - len(selected)
            array = self._generate_array_of_thoughts_result(
                concept,
                max_subtopics=self._ADAPTIVE_MAX_HORIZONTAL,
                max_tokens=_DEFAULT_MAX_TOKENS,
                ranked=False,
                model=model,
                prompt_template=ADAPTIVE_CONCEPT_SUBTOPIC_GENERATION_PROMPT,
            )
            if not array.thoughts:
                self._record_horizontal("stop", _ExplorationReason.NO_CANDIDATE)
                break

            existing_names = [item.name for item in selected]
            accepted = 0
            first_rejection: str | None = None
            batch_saturated = False
            for candidate in array.thoughts:
                if batch_saturated:
                    self._record_horizontal(
                        "skip", _ExplorationReason.INSUFFICIENT_DISTINCTNESS,
                        candidate.name,
                    )
                    continue
                if not self._is_meaningful_candidate(
                    candidate.name, existing_names, overlap_limit=overlap_limit
                ):
                    first_rejection = first_rejection or candidate.name
                    self._record_horizontal(
                        "skip", _ExplorationReason.INSUFFICIENT_DISTINCTNESS,
                        candidate.name,
                    )
                    batch_saturated = True
                    continue

                if self._adaptive_node_count >= self._adaptive_max_nodes:
                    self._record_safety_stop(
                        _ExplorationReason.NODE_BUDGET,
                        level=0,
                        thought=candidate.name,
                    )
                    break
                selected.append(
                    ThoughtNode(name=candidate.name, description=candidate.description)
                )
                existing_names.append(candidate.name)
                self._adaptive_node_count += 1
                accepted += 1
                self._record_horizontal(
                    "continue", _ExplorationReason.MATERIAL_DISTINCT, candidate.name
                )

            if self._adaptive_safety_stopped:
                break
            if accepted == 0:
                self._record_horizontal(
                    "stop", _ExplorationReason.INSUFFICIENT_DISTINCTNESS,
                    first_rejection,
                )
                break
            if first_rejection is not None or len(array.thoughts) < batch_size:
                self._record_horizontal(
                    "stop", _ExplorationReason.INSUFFICIENT_DISTINCTNESS,
                    first_rejection,
                )
                break

        if len(selected) >= self._ADAPTIVE_MAX_HORIZONTAL:
            self._adaptive_ceiling_reason = _ExplorationReason.INTERNAL_CANDIDATE_LIMIT
            self._record_horizontal(
                "stop", _ExplorationReason.INTERNAL_CANDIDATE_LIMIT
            )
        return selected

    def _expand_adaptive_node(
        self,
        node: ThoughtNode,
        concept: str,
        *,
        exploration: str,
        level: int,
        path: list[str],
        model: str | None,
        progression_type: ProgressionType,
    ) -> list[ThoughtNode]:
        if level >= self.MAX_FACADE_DEPTH:
            self._adaptive_depth_limit_reached = True
            self._record_vertical(
                "stop", _ExplorationReason.DEPTH_LIMIT, level=level, thought=node.name
            )
            return []
        if self._is_natural_endpoint(node.name):
            self._record_vertical(
                "stop", _ExplorationReason.NATURAL_ENDPOINT,
                level=level, thought=node.name,
            )
            return []

        if not self._consume_adaptive_work(level=level, thought=node.name):
            return []

        result = self._expand_subtopic_result(
            concept,
            node.name,
            max_details=self._ADAPTIVE_MAX_VERTICAL_OUTPUT,
            max_tokens=_DEFAULT_MAX_TOKENS,
            model=model,
            progression_type=progression_type,
            prompt_template=ADAPTIVE_CONCEPT_DETAIL_GENERATION_PROMPT,
        )
        overlap_limit = self._profile_overlap_limit(exploration)
        children = []
        generated_children = result.sub_thoughts or []
        if len(generated_children) > self._ADAPTIVE_MAX_VERTICAL_OUTPUT:
            self._adaptive_ceiling_reason = _ExplorationReason.INTERNAL_CANDIDATE_LIMIT
        for item in generated_children[:self._ADAPTIVE_MAX_VERTICAL_OUTPUT]:
            candidate_context = [*path, *(child.name for child in children)]
            if self._is_meaningful_candidate(
                item.name, candidate_context, overlap_limit=overlap_limit
            ):
                if self._adaptive_node_count >= self._adaptive_max_nodes:
                    self._record_safety_stop(
                        _ExplorationReason.NODE_BUDGET,
                        level=level,
                        thought=item.name,
                    )
                    break
                children.append(
                    ThoughtNode(name=item.name, description=item.description)
                )
                self._adaptive_node_count += 1

        if not children:
            reason = (
                _ExplorationReason.NO_CHILDREN
                if not result.sub_thoughts
                else _ExplorationReason.INSUFFICIENT_NOVELTY
            )
            self._record_vertical("stop", reason, level=level, thought=node.name)
            node.children = []
            return []

        node.children = children
        self._record_vertical(
            "continue", _ExplorationReason.MEANINGFUL_CHILDREN,
            level=level, thought=node.name,
        )
        eligible_children: list[ThoughtNode] = []
        eligible_candidates = []
        for child in node.children:
            if self._adaptive_safety_stopped:
                break
            if self._is_natural_endpoint(child.name):
                self._record_vertical(
                    "retain", _ExplorationReason.NATURAL_ENDPOINT,
                    level=level + 1, thought=child.name,
                )
                continue
            branch_limit = self._profile_branch_overlap_limit(exploration)
            if not self._is_meaningful_candidate(
                child.name, path, overlap_limit=branch_limit
            ):
                self._record_vertical(
                    "retain", _ExplorationReason.BRANCH_PRUNED,
                    level=level + 1, thought=child.name,
                )
                continue
            if not self._is_relevant_candidate(
                concept, path, child.name, child.description, exploration=exploration
            ):
                self._record_vertical(
                    "retain", _ExplorationReason.INSUFFICIENT_RELEVANCE,
                    level=level + 1, thought=child.name,
                )
                continue
            if not self._is_marginally_valuable_candidate(
                concept, path, child.name, child.description, exploration=exploration
            ):
                self._record_vertical(
                    "retain", _ExplorationReason.INSUFFICIENT_MARGINAL_VALUE,
                    level=level + 1, thought=child.name,
                )
                continue
            eligible_children.append(child)
            eligible_candidates.append((f"child-{len(eligible_children)}", child))

        if not eligible_children:
            return []

        decisions = self._evaluate_adaptive_decomposition(
            path=path,
            candidates=eligible_candidates,
            exploration=exploration,
            level=level + 1,
            model=model,
        )
        next_children: list[ThoughtNode] = []
        for candidate_id, child in eligible_candidates:
            if self._adaptive_safety_stopped:
                break
            if decisions.get(candidate_id, True) is False:
                self._record_vertical(
                    "retain", _ExplorationReason.DECOMPOSITION_TERMINAL,
                    level=level + 1, thought=child.name,
                )
                continue
            next_children.append(child)
        return next_children

    def _evaluate_adaptive_decomposition(
        self,
        *,
        path: list[str],
        candidates: list[tuple[str, ThoughtNode]],
        exploration: str,
        level: int,
        model: str | None,
    ) -> dict[str, bool]:
        if not self._consume_adaptive_provider_call(level=level, thought=path[-1]):
            for _, child in candidates:
                self._record_vertical(
                    "retain", _ExplorationReason.DECOMPOSITION_FALLBACK,
                    level=level, thought=child.name,
                )
            return {candidate_id: True for candidate_id, _ in candidates}

        try:
            from xf_thoughtgraph.reflection import (
                DecompositionCandidate,
                DecompositionEvaluationRequest,
                DecompositionEvaluationService,
            )

            result = DecompositionEvaluationService(
                self.provider,
                model=model or self.model,
                max_tokens=_DEFAULT_MAX_TOKENS,
            ).evaluate(
                DecompositionEvaluationRequest(
                    ancestor_path=tuple(path),
                    candidates=tuple(
                        DecompositionCandidate(
                            id=candidate_id,
                            thought=child.name,
                            description=child.description,
                        )
                        for candidate_id, child in candidates
                    ),
                    exploration=exploration,
                )
            )
        except Exception:
            for _, child in candidates:
                self._record_vertical(
                    "continue", _ExplorationReason.DECOMPOSITION_FALLBACK,
                    level=level, thought=child.name,
                )
            return {candidate_id: True for candidate_id, _ in candidates}

        return {
            decision.candidate_id: decision.decompose
            for decision in result.decisions
        }

    def _start_adaptive_run(
        self,
        *,
        max_calls: int | None = None,
        max_nodes: int | None = None,
    ) -> None:
        self._adaptive_provider_calls = 0
        self._adaptive_node_count = 0
        self._adaptive_expansion_attempts = 0
        self._adaptive_safety_stopped = False
        self._adaptive_stop_reason: _ExplorationReason | None = None
        self._adaptive_depth_limit_reached = False
        self._adaptive_ceiling_reason: _ExplorationReason | None = None
        self._adaptive_max_provider_calls = (
            max_calls if max_calls is not None else self._ADAPTIVE_MAX_PROVIDER_CALLS
        )
        self._adaptive_max_nodes = (
            max_nodes if max_nodes is not None else self._ADAPTIVE_MAX_NODES
        )

    def _adaptive_exploration_summary(self) -> AdaptiveExplorationSummary:
        if self._adaptive_safety_stopped:
            reason = self._adaptive_stop_reason.value
        elif self._adaptive_depth_limit_reached:
            reason = _ExplorationReason.DEPTH_LIMIT.value
        elif self._adaptive_ceiling_reason is not None:
            reason = self._adaptive_ceiling_reason.value
        else:
            reason = "semantic_completion"
        return AdaptiveExplorationSummary(
            actual_calls=self._adaptive_provider_calls,
            actual_nodes=self._adaptive_node_count,
            expansion_attempts=self._adaptive_expansion_attempts,
            completed=reason == "semantic_completion",
            stop_reason=reason,
            max_calls=self._adaptive_max_provider_calls,
            max_nodes=self._adaptive_max_nodes,
        )

    def _consume_adaptive_work(self, *, level: int, thought: str | None = None) -> bool:
        if not self._consume_adaptive_provider_call(level=level, thought=thought):
            return False
        if self._adaptive_expansion_attempts >= self._ADAPTIVE_MAX_EXPANSIONS:
            self._adaptive_provider_calls -= 1
            self._record_safety_stop(
                _ExplorationReason.EXPANSION_BUDGET,
                level=level,
                thought=thought,
            )
            return False
        self._adaptive_expansion_attempts += 1
        return True

    def _consume_adaptive_provider_call(
        self, *, level: int, thought: str | None = None
    ) -> bool:
        if self._adaptive_safety_stopped:
            return False
        if self._adaptive_provider_calls >= self._adaptive_max_provider_calls:
            self._record_safety_stop(
                _ExplorationReason.CALL_BUDGET,
                level=level,
                thought=thought,
            )
            return False
        self._adaptive_provider_calls += 1
        return True

    def _record_safety_stop(
        self,
        reason: _ExplorationReason,
        *,
        level: int,
        thought: str | None = None,
    ) -> None:
        if self._adaptive_safety_stopped:
            return
        self._adaptive_safety_stopped = True
        self._adaptive_stop_reason = reason
        self._record_exploration_decision(
            axis="global", action="stop", reason=reason,
            level=level, thought=thought,
        )

    def _record_exploration_decision(
        self,
        *,
        axis: str,
        action: str,
        reason: _ExplorationReason,
        level: int,
        thought: str | None = None,
    ) -> None:
        self.last_exploration_trace.append(
            _ExplorationDecision(
                axis=axis,
                action=action,
                reason=reason,
                level=level,
                thought=thought,
            )
        )

    def _record_horizontal(
        self,
        action: str,
        reason: _ExplorationReason,
        thought: str | None = None,
    ) -> None:
        self._record_exploration_decision(
            axis="horizontal", action=action, reason=reason,
            level=0, thought=thought,
        )

    def _record_vertical(
        self,
        action: str,
        reason: _ExplorationReason,
        *,
        level: int,
        thought: str | None = None,
    ) -> None:
        self._record_exploration_decision(
            axis="vertical", action=action, reason=reason,
            level=level, thought=thought,
        )

    _profile_overlap_limit = staticmethod(profile_overlap_limit)
    _profile_branch_overlap_limit = staticmethod(profile_branch_overlap_limit)
    _profile_relevance_limit = staticmethod(profile_relevance_limit)
    _profile_marginal_value_limit = staticmethod(profile_marginal_value_limit)
    _is_marginally_valuable_candidate = staticmethod(
        is_marginally_valuable_candidate
    )
    _is_relevant_candidate = staticmethod(is_relevant_candidate)
    _is_meaningful_candidate = staticmethod(is_meaningful_candidate)
    _tokens = staticmethod(tokens)
    _token_overlap = staticmethod(token_overlap)
    _is_natural_endpoint = staticmethod(is_natural_endpoint)
    _graph_depth = staticmethod(graph_depth)


__all__ = ["AdaptiveTraversalMixin"]
