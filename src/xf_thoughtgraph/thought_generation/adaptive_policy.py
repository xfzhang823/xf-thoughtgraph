"""Deterministic policy helpers used by adaptive graph traversal."""

import re

from xf_thoughtgraph.models import ThoughtNode


PROFILE_OVERLAP_LIMITS = {
    "focused": 0.25,
    "balanced": 0.50,
    "rich": 0.75,
}
BRANCH_OVERLAP_LIMITS = {
    "focused": 0.05,
    "balanced": 0.25,
    "rich": 0.50,
}
RELEVANCE_LIMITS = {
    "focused": 0.20,
    "balanced": 0.08,
    "rich": 0.04,
}
MARGINAL_VALUE_LIMITS = {
    "focused": 0.55,
    "balanced": 0.35,
    "rich": 0.20,
}

DETAIL_TERMS = frozenset(
    {
        "assess", "assessment", "check", "checking", "choose", "clarify",
        "conduct", "configure", "configuration", "confirm", "define",
        "document", "documentation", "detail", "criteria", "criterion",
        "establish", "further", "handle", "handling", "identify",
        "installation", "install", "logistics", "measurement", "monitor",
        "monitoring", "obtain", "plan", "planning", "procedure", "process",
        "protocol", "record", "review", "rule", "rules", "screen",
        "screening", "select", "set", "setup", "specify", "specification",
        "status", "tracking", "verify", "workflow",
    }
)
PROCEDURAL_TERMS = frozenset(
    {
        "assess", "choose", "clarify", "conduct", "configure", "confirm",
        "define", "document", "establish", "identify", "implement", "obtain",
        "plan", "record", "review", "screen", "select", "set", "specify",
        "verify",
    }
)
NATURAL_ENDPOINT_TERMS = frozenset(
    {"completed", "conclusion", "done", "endpoint", "finished"}
)
NATURAL_ENDPOINT_PHRASES = frozenset(
    {
        "conclusion", "done", "final answer", "final result", "final step",
        "final summary", "finished", "natural endpoint", "project complete",
        "work complete",
    }
)
TOKEN_STOP_WORDS = frozenset(
    {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
)


def profile_overlap_limit(exploration: str) -> float:
    return PROFILE_OVERLAP_LIMITS[exploration]


def profile_branch_overlap_limit(exploration: str) -> float:
    return BRANCH_OVERLAP_LIMITS[exploration]


def profile_relevance_limit(exploration: str) -> float:
    return RELEVANCE_LIMITS[exploration]


def profile_marginal_value_limit(exploration: str) -> float:
    return MARGINAL_VALUE_LIMITS[exploration]


def is_marginally_valuable_candidate(
    concept: str,
    path: list[str],
    candidate: str,
    description: str | None,
    *,
    exploration: str,
) -> bool:
    """Require new conceptual structure before spending another call."""
    root_tokens = tokens(concept)
    candidate_tokens = tokens(f"{candidate} {description or ''}")
    if not candidate_tokens:
        return False

    detail_tokens = candidate_tokens & DETAIL_TERMS
    candidate_concepts = candidate_tokens - root_tokens - DETAIL_TERMS
    path_tokens = set().union(*(tokens(item) for item in path[1:]))
    established_concepts = path_tokens - root_tokens - DETAIL_TERMS

    if not candidate_concepts:
        score = 0.15 if detail_tokens else 0.0
    else:
        new_concepts = candidate_concepts - established_concepts
        conceptual_gain = len(new_concepts) / len(candidate_concepts)
        non_detail_signal = 1.0 - len(detail_tokens) / len(candidate_tokens)
        score = 0.75 * conceptual_gain + 0.25 * non_detail_signal

        current_is_procedural = bool(candidate_tokens & PROCEDURAL_TERMS)
        prior_procedural_levels = sum(
            bool(tokens(item) & PROCEDURAL_TERMS) for item in path[1:]
        )
        if current_is_procedural and prior_procedural_levels >= 1:
            score *= 0.45
            if prior_procedural_levels >= 2:
                score *= 0.45

    return score >= profile_marginal_value_limit(exploration)


def is_relevant_candidate(
    concept: str,
    path: list[str],
    candidate: str,
    description: str | None,
    *,
    exploration: str,
) -> bool:
    """Require enough root-goal evidence before recursively expanding."""
    candidate_name_tokens = tokens(candidate)
    candidate_content_tokens = tokens(f"{candidate} {description or ''}")
    concept_tokens = tokens(concept)
    if not candidate_content_tokens or not concept_tokens:
        return False

    direct_name_signal = token_overlap(candidate_name_tokens, concept_tokens)
    direct_content_signal = token_overlap(candidate_content_tokens, concept_tokens)
    direct_signal = max(direct_name_signal, direct_content_signal)

    ancestor_names = path[1:]
    if not ancestor_names:
        return True
    ancestor_tokens = [tokens(ancestor) for ancestor in ancestor_names]
    parent_signal = token_overlap(candidate_content_tokens, ancestor_tokens[-1])
    ancestor_signal = max(
        token_overlap(candidate_content_tokens, ancestor_tokens_item)
        for ancestor_tokens_item in ancestor_tokens
    )

    anchored = [
        token_overlap(item_tokens, concept_tokens) > 0
        for item_tokens in ancestor_tokens
    ]
    if direct_signal == 0.0 and not any(anchored):
        return True

    if direct_signal > 0.0:
        score = 0.65 * direct_signal + 0.25 * parent_signal + 0.10 * ancestor_signal
    else:
        unanchored_suffix = 0
        for is_anchored in reversed(anchored):
            if is_anchored:
                break
            unanchored_suffix += 1
        continuity = max(parent_signal, ancestor_signal)
        if unanchored_suffix <= 1:
            score = 0.50 + 0.30 * continuity
        else:
            score = 0.35 * continuity / unanchored_suffix

    return score >= profile_relevance_limit(exploration)


def is_meaningful_candidate(
    candidate: str,
    existing: list[str],
    *,
    overlap_limit: float,
) -> bool:
    candidate_tokens = tokens(candidate)
    if not candidate_tokens:
        return False
    return all(
        token_overlap(candidate_tokens, tokens(item)) <= overlap_limit
        for item in existing
    )


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in TOKEN_STOP_WORDS
    }


def token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def is_natural_endpoint(value: str) -> bool:
    normalized = " ".join(re.findall(r"[a-z0-9]+", value.lower()))
    if normalized in NATURAL_ENDPOINT_PHRASES:
        return True
    return bool(tokens(value) & NATURAL_ENDPOINT_TERMS)


def graph_depth(node: ThoughtNode) -> int:
    """Return generated child-level depth using the public graph meaning."""
    if not node.children:
        return 0
    return 1 + max(graph_depth(child) for child in node.children)
