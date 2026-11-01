"""Public provider-injected thought-generation engine."""

# This module intentionally houses the public compatibility façade and the
# explicit bounded graph path. Adaptive traversal is implemented by the
# adjacent mixin while retaining the same engine API.
# pylint: disable=too-many-lines,too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-locals,too-many-branches

from typing import Any

from xf_thoughtgraph.models import (
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    ProgressionType,
    Thought,
    ThoughtArray,
    ThoughtGraph,
    ThoughtJSONModel,
    ThoughtNode,
)
from xf_thoughtgraph.prompts import (
    CONCEPT_DETAIL_GENERATION_PROMPT,
    CONCEPT_SUBTOPIC_GENERATION_PROMPT,
)
from xf_thoughtgraph.providers import LLMProvider, create_provider, default_model
from xf_thoughtgraph.storage import Repository

from .expansion import expand_idea, expand_vertical
from .generation import generate_horizontal
from .indexing import index_idea
from .ranking import convert_clusters_to_idea, select_clusters
from .requests import (
    HorizontalGenerationRequest,
    VerticalGenerationRequest,
    _DEFAULT_MAX_TOKENS,
)
from .adaptive_traversal import (
    AdaptiveTraversalMixin,
    _ExplorationDecision,
)


class ThoughtGraphEngine(AdaptiveTraversalMixin):
    """Generate, expand, organize, and optionally persist thought structures.

    ``ThoughtGraphEngine`` is the primary public façade for exploring a concept
    as an array or hierarchy of related thoughts.

    The engine supports two complementary workflows:

    1. A concept-first façade for generating major subtopics, expanding one
       subtopic into more-specific details, producing typed thought arrays, and
       constructing bounded thought graphs.
    2. A lower-level typed API based on ``HorizontalGenerationRequest`` and
       ``VerticalGenerationRequest`` for callers that need direct control over
       model settings, prompts, progression types, clustering, or ranking.

    Horizontal generation produces sibling-level dimensions of an idea.
    Vertical generation produces more-specific children beneath a selected
    thought.

    All generation and expansion operations remain in memory. Supplying a
    repository does not enable automatic persistence; callers must invoke
    ``save`` explicitly.

    Attributes:
        provider: Language-model provider used for generation, expansion,
            clustering, and ranking.
        repository: Optional repository used only by explicit ``save`` calls.
        model: Default provider-specific model identifier used by the
            concept-first façade.
    """

    DEFAULT_FACADE_DEPTH = 2
    """Default number of generated child levels beneath the root."""

    DEFAULT_FACADE_BREADTH = 6
    """Default number of root-level horizontal thoughts retained."""

    _DEFAULT_VERTICAL_CHILDREN = 7
    """Internal child cap for new explicit horizontal/vertical graph calls."""

    _ADAPTIVE_VERTICAL_CHILDREN = 4
    """Smaller internal child request used only by adaptive expansion."""

    MAX_FACADE_DEPTH = 8
    """Maximum number of generated child levels supported by new mode."""

    _ADAPTIVE_MAX_HORIZONTAL = 8
    """Internal guard against unbounded retained horizontal directions."""

    _ADAPTIVE_HORIZONTAL_CANDIDATES = 3
    """Small internal candidate batch used by adaptive horizontal probing."""

    _ADAPTIVE_MAX_PROVIDER_CALLS = 64
    """Internal profile-independent provider-call guard."""

    _ADAPTIVE_MAX_NODES = 128
    """Internal profile-independent retained-node guard."""

    _ADAPTIVE_MAX_EXPANSIONS = 64
    """Internal profile-independent expansion-attempt guard."""

    def __init__(
        self,
        provider: LLMProvider | str,
        repository: Repository[Any] | None = None,
        *,
        model: str | None = None,
    ) -> None:
        """Initialize the thought-graph engine.

        Args:
            provider: Provider implementation responsible for language-model
                calls, or a supported provider name. Named providers are
                created through ``xf_thoughtgraph.providers.create_provider``.
            repository: Optional persistence adapter. Results are not persisted
                unless ``save`` is called explicitly.
            model: Default model identifier used by façade methods when a
                per-call model override is not supplied. When omitted for a
                named provider, the package's provider default is used; when
                omitted for an injected provider, ``"default"`` preserves the
                existing injected-engine behavior.

        Raises:
            ValueError: If ``model`` is not a non-empty string.
        """
        if isinstance(provider, str):
            provider_name = self._require_text(provider, "provider").lower()
            self.provider = create_provider(provider_name)
            resolved_model = (
                model if model is not None else default_model(provider_name)
            )
        else:
            self.provider = provider
            resolved_model = model if model is not None else "default"
        self.repository = repository
        self.model = self._require_text(resolved_model, "model")
        self.last_exploration_trace: list[_ExplorationDecision] = []
        self.last_exploration_profile: str | None = None
        self._adaptive_provider_calls = 0
        self._adaptive_node_count = 0
        self._adaptive_expansion_attempts = 0
        self._adaptive_safety_stopped = False

    def generate(self, request: HorizontalGenerationRequest) -> IdeaJSONModel:
        """Generate sibling-level thoughts using the typed horizontal API.

        The method first performs horizontal thought generation. When both
        ``request.num_clusters`` and ``request.top_n`` are supplied, the
        generated thoughts are passed through the existing clustering and
        ranking pipeline.

        ``num_clusters`` and ``top_n`` must either both be omitted or both be
        supplied. Generation does not persist the result.

        Args:
            request: Complete horizontal-generation configuration, including
                the source idea, model, number of thoughts, provider settings,
                and optional ranking parameters.

        Returns:
            An ``IdeaJSONModel`` containing the generated thoughts. When
            clustering is enabled, the model contains the selected cluster
            representatives converted back into the standard idea structure.

        Raises:
            ValueError: If exactly one of ``num_clusters`` and ``top_n`` is
                supplied.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
        result = generate_horizontal(
            self.provider,
            idea=request.idea,
            model=request.model,
            num_thoughts=request.num_thoughts,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
            prompt_template=request.prompt_template,
        )
        if request.num_clusters is None and request.top_n is None:
            return result
        if request.num_clusters is None or request.top_n is None:
            raise ValueError("num_clusters and top_n must be supplied together")
        clusters = select_clusters(
            self.provider,
            result,
            model=request.model,
            num_clusters=request.num_clusters,
            top_n=request.top_n,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )
        return convert_clusters_to_idea(clusters)

    def expand(self, request: VerticalGenerationRequest) -> ThoughtJSONModel:
        """Expand one thought using the typed vertical API.

        The selected thought is expanded within the context of the root idea.
        ``request.progression_type`` defines the intended relationship between
        the parent thought and its generated children, such as implementation
        steps, direct conceptual children, or strict prerequisites.

        This method performs one vertical expansion operation and does not
        persist the result.

        Args:
            request: Complete vertical-expansion configuration, including the
                root idea, selected thought, model, progression type, provider
                settings, and optional prompt override.

        Returns:
            The vertical-expansion result produced by ``expand_vertical``. The
            returned object includes the selected thought and its generated
            sub-thoughts.

        Raises:
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        return expand_vertical(
            self.provider,
            idea=request.idea,
            thought=request.thought,
            model=request.model,
            progression_type=request.progression_type,
            num_sub_thoughts=request.num_sub_thoughts,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
            prompt_template=request.prompt_template,
        )

    def expand_all(
        self,
        idea: IdeaJSONModel,
        *,
        model: str,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
        num_sub_thoughts: int = 5,
        temperature: float = 0.7,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        timeout: float | None = None,
    ) -> IdeaJSONModel:
        """Expand every top-level thought in an idea.

        Thoughts are processed in their existing source order. Each thought is
        expanded according to the requested progression type. Depending on the
        underlying implementation, expansion may require one provider call per
        top-level thought.

        The operation remains in memory and does not persist the expanded idea.

        Args:
            idea: Idea model whose top-level thoughts should be expanded.
            model: Provider-specific model identifier.
            progression_type: Semantic relationship expected between each
                parent thought and its generated children.
            num_sub_thoughts: Maximum number of children requested for each
                top-level thought.
            temperature: Sampling temperature used for provider calls.
            max_tokens: Maximum number of response tokens allowed per call.
            timeout: Optional provider-call timeout in seconds.

        Returns:
            An ``IdeaJSONModel`` containing the original thoughts and their
            generated vertical expansions.

        Raises:
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        progression_type = ProgressionType(progression_type)
        return expand_idea(
            self.provider,
            idea,
            model=model,
            progression_type=progression_type,
            num_sub_thoughts=num_sub_thoughts,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    @staticmethod
    def index(idea: IdeaJSONModel) -> IndexedIdeaJSONModel:
        """Assign deterministic zero-based indices to an idea hierarchy.

        Indexing preserves the source ordering of thoughts and sub-thoughts.
        The operation is deterministic, does not call the language-model
        provider, and does not persist the result.

        Args:
            idea: Unindexed idea model.

        Returns:
            An ``IndexedIdeaJSONModel`` containing the same logical structure
            with deterministic zero-based indices.
        """
        return index_idea(idea)

    def generate_subtopics(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        ranked: bool = False,
        model: str | None = None,
    ) -> list[str]:
        """Generate major sibling-level dimensions of a concept.

        This is the simplest horizontal-expansion method. It asks the provider
        to identify broad, peer-level areas of the concept rather than
        procedural steps or lower-level details.

        When ``ranked`` is true, the generated thoughts are passed through the
        existing clustering and ranking pipeline before their names are
        returned.

        Args:
            concept: Concept to explore horizontally.
            max_subtopics: Maximum number of subtopic names to return.
            ranked: Whether to cluster and rank the generated subtopics.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A list of generated subtopic names in source or ranked order.

        Raises:
            ValueError: If ``concept`` is empty, ``max_subtopics`` is not a
                positive integer, or the resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
        return [
            item.name
            for item in self.generate_array_of_thoughts(
                concept,
                max_subtopics=max_subtopics,
                ranked=ranked,
                model=model,
            ).thoughts
        ]

    def expand_subtopic(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int = 8,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        model: str | None = None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
    ) -> list[str]:
        """Generate direct, more-specific children of one subtopic.

        This is the simplest vertical-expansion method. The generated details
        should remain within the context of ``concept`` while representing a
        lower level of abstraction beneath ``subtopic``.

        The method performs one provider expansion call and does not persist
        the result.

        Args:
            concept: Root concept that constrains the expansion.
            subtopic: Existing subtopic to expand vertically.
            max_details: Maximum number of direct-child names to return.
            max_tokens: Maximum number of provider response tokens.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.
            progression_type: Semantic relationship used for generated
                children. Raw strings are normalized to ``ProgressionType``.

        Returns:
            A list containing the names of the generated direct children.

        Raises:
            ValueError: If ``concept`` or ``subtopic`` is empty,
                ``max_details`` is not a positive integer, or the resolved model
                identifier is empty.
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        result = self._expand_subtopic_result(
            concept,
            subtopic,
            max_details=max_details,
            max_tokens=max_tokens,
            model=model,
            progression_type=progression_type,
        )
        return [item.name for item in result.sub_thoughts or []]

    def generate_array_of_thoughts(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtArray:
        """Generate a typed horizontal array of thoughts for a concept.

        Unlike ``generate_subtopics``, which returns only names, this method
        preserves each generated thought as a public ``Thought`` object,
        including its description when one is available.

        The generated thoughts are intended to be sibling-level dimensions:
        broad areas that collectively describe the concept at a similar level
        of abstraction.

        Args:
            concept: Concept to explore horizontally.
            max_subtopics: Maximum number of thoughts included in the returned
                array.
            max_tokens: Maximum number of provider response tokens.
            ranked: Whether to cluster and rank the generated thoughts before
                constructing the array.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A ``ThoughtArray`` containing the normalized concept and its
            generated sibling-level thoughts.

        Raises:
            ValueError: If ``concept`` is empty, ``max_subtopics`` is not a
                positive integer, or the resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
        concept = self._require_text(concept, "concept")
        max_subtopics = self._require_positive(max_subtopics, "max_subtopics")
        request = HorizontalGenerationRequest(
            idea=concept,
            model=self._resolve_model(model),
            num_thoughts=max_subtopics,
            max_tokens=max_tokens,
            num_clusters=max_subtopics if ranked else None,
            top_n=max_subtopics if ranked else None,
            prompt_template=CONCEPT_SUBTOPIC_GENERATION_PROMPT,
        )
        result = self.generate(request)
        return ThoughtArray(
            concept=concept,
            thoughts=[
                Thought(name=item.thought, description=item.description)
                for item in (result.thoughts or [])[:max_subtopics]
            ],
        )

    def generate_thought_graph(
        self,
        topic: str,
        *,
        horizontal: int | None = None,
        vertical: int | None = None,
        exploration: str | None = None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtGraph:
        """Generate a bounded hierarchical thought graph.

        The graph begins with ``topic`` as its root node. The first child
        level is generated horizontally as a set of sibling-level subtopics.
        Each deeper level is generated vertically by expanding each node into
        direct, more-specific children.

        ``horizontal`` limits root-level peer directions, while ``vertical``
        limits generated child levels beneath the root. Explicit calls use an
        internal vertical child cap independent of ``horizontal``.

        When no graph-shape bounds are supplied, ``exploration`` defaults to
        ``"balanced"`` and continuation is evaluated as the graph develops.
        Adaptive continuation requires both sufficient novelty and a
        provider-neutral root-goal relevance signal.
        Adaptive exploration cannot be combined with explicit graph-shape
        bounds.

        Explicit graph generation begins with one horizontal provider call.
        Adaptive generation may make additional bounded horizontal candidate
        calls while evaluating continuation. Each node expanded below the
        first level requires an additional vertical provider call. Provider-
        call volume can therefore grow quickly as the graph expands.

        Ranking applies only to the initial horizontal subtopics. Generated
        graphs remain in memory and are not persisted automatically.

        Args:
            topic: Root concept represented by the graph.
            horizontal: Maximum number of root-level peer directions retained.
            vertical: Maximum number of generated child levels beneath the
                root.
            exploration: Adaptive continuation profile: ``"focused"``,
                ``"balanced"``, or ``"rich"``. When omitted without graph
                bounds, ``"balanced"`` is used. It cannot be combined with
                ``horizontal`` or ``vertical``.
            progression_type: Semantic relationship used for every vertical
                graph expansion. Raw strings are normalized to
                ``ProgressionType``.
            ranked: Whether to cluster and rank the first-level horizontal
                subtopics.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A ``ThoughtGraph`` containing the root node, generated hierarchy,
            and the resolved depth and breadth metadata. In new explicit mode,
            those metadata fields correspond to ``vertical`` and ``horizontal``.

        Raises:
            ValueError: If ``topic`` is empty, a bound is not a positive
                integer, ``vertical`` exceeds ``MAX_FACADE_DEPTH``, or the
                resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, ranking, or validation
                exception raised during graph generation.
        """
        topic = self._require_text(topic, "topic")
        shape_bounds_supplied = horizontal is not None or vertical is not None
        if exploration is not None:
            exploration = self._require_exploration_profile(exploration)
        elif not shape_bounds_supplied:
            exploration = "balanced"

        if exploration is not None and shape_bounds_supplied:
            raise ValueError(
                "exploration cannot be combined with horizontal/vertical"
            )

        progression_type = ProgressionType(progression_type)
        if exploration is not None:
            self.last_exploration_trace = []
            self.last_exploration_profile = exploration
            self._start_adaptive_run()
            root = self._generate_adaptive_graph(
                topic,
                exploration=exploration,
                model=model,
                progression_type=progression_type,
            )
            return ThoughtGraph(
                concept=topic,
                root=root,
                depth=max(1, self._graph_depth(root)),
                breadth=len(root.children),
            )

        self.last_exploration_trace = []
        self.last_exploration_profile = None
        horizontal = self._require_positive(
            horizontal if horizontal is not None else self.DEFAULT_FACADE_BREADTH,
            "horizontal",
        )
        vertical = self._require_positive(
            vertical if vertical is not None else self.DEFAULT_FACADE_DEPTH,
            "vertical",
        )
        if vertical > self.MAX_FACADE_DEPTH:
            raise ValueError(f"vertical must be <= {self.MAX_FACADE_DEPTH}")

        array = self.generate_array_of_thoughts(
            topic,
            max_subtopics=horizontal,
            ranked=ranked,
            model=model,
        )
        root = ThoughtNode(
            name=topic,
            children=[
                ThoughtNode(name=item.name, description=item.description)
                for item in array.thoughts[:horizontal]
            ],
        )
        if vertical >= 2:
            for child in root.children:
                self._expand_graph_node(
                    child,
                    topic,
                    depth=vertical,
                    level=1,
                    vertical_child_limit=self._DEFAULT_VERTICAL_CHILDREN,
                    model=model,
                    progression_type=progression_type,
                )
        return ThoughtGraph(
            concept=topic, root=root, depth=vertical, breadth=horizontal
        )

    @staticmethod
    def _require_exploration_profile(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("exploration must be 'focused', 'balanced', or 'rich'")
        normalized = value.strip().lower()
        if normalized not in {"focused", "balanced", "rich"}:
            raise ValueError("exploration must be 'focused', 'balanced', or 'rich'")
        return normalized

    def _expand_graph_node(
        self,
        node: ThoughtNode,
        concept: str,
        *,
        depth: int,
        level: int,
        vertical_child_limit: int,
        model: str | None,
        progression_type: ProgressionType,
    ) -> None:
        """Recursively populate descendants beneath one thought-graph node.

        The method stops when ``level`` reaches ``depth``. Otherwise, it
        performs a direct-child vertical expansion, replaces ``node.children``
        with the generated children, and recursively expands each child.

        Args:
            node: Graph node whose descendants should be generated.
            concept: Root concept used to constrain every vertical expansion.
            depth: Maximum generated child depth beneath the root.
            level: Current depth of ``node`` relative to the root.
            vertical_child_limit: Internal maximum number of children retained
                for each vertical expansion.
            model: Optional provider-specific model override.
            progression_type: Semantic relationship used for generated children.

        Notes:
            This method mutates ``node.children`` in place. Each node expanded
            by this method results in one provider call.
        """
        if level >= depth:
            return
        result = self._expand_subtopic_result(
            concept,
            node.name,
            max_details=vertical_child_limit,
            max_tokens=_DEFAULT_MAX_TOKENS,
            model=model,
            progression_type=progression_type,
        )
        node.children = [
            ThoughtNode(name=item.name, description=item.description)
            for item in (result.sub_thoughts or [])[:vertical_child_limit]
        ]
        for child in node.children:
            self._expand_graph_node(
                child,
                concept,
                depth=depth,
                level=level + 1,
                vertical_child_limit=vertical_child_limit,
                model=model,
                progression_type=progression_type,
            )

    def _expand_subtopic_result(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int,
        max_tokens: int,
        model: str | None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
    ) -> ThoughtJSONModel:
        """Generate the typed vertical-expansion result for one subtopic.

        This helper validates the façade arguments and translates them into a
        ``VerticalGenerationRequest`` configured for the requested progression
        type.

        Args:
            concept: Root concept that constrains the expansion.
            subtopic: Parent thought to expand.
            max_details: Maximum number of direct children to request.
            max_tokens: Maximum number of provider response tokens.
            model: Optional provider-specific model override.
            progression_type: Semantic relationship used for generated children.

        Returns:
            The typed vertical-expansion result returned by ``expand``.

        Raises:
            ValueError: If ``concept`` or ``subtopic`` is empty,
                ``max_details`` is not a positive integer, or the resolved model
                identifier is empty.
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        concept = self._require_text(concept, "concept")
        subtopic = self._require_text(subtopic, "subtopic")
        max_details = self._require_positive(max_details, "max_details")
        return self.expand(
            VerticalGenerationRequest(
                idea=concept,
                thought=subtopic,
                model=self._resolve_model(model),
                progression_type=progression_type,
                num_sub_thoughts=max_details,
                max_tokens=max_tokens,
                prompt_template=CONCEPT_DETAIL_GENERATION_PROMPT,
            )
        )

    def _resolve_model(self, model: str | None) -> str:
        """Resolve and validate the model identifier for a façade call.

        Args:
            model: Optional per-call model override.

        Returns:
            The normalized override when supplied; otherwise, the engine's
            default model identifier.

        Raises:
            ValueError: If the resolved model identifier is empty.
        """
        return self._require_text(model or self.model, "model")

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        """Validate and normalize a required text argument.

        Args:
            value: Candidate string value.
            name: Parameter name included in validation errors.

        Returns:
            The input string with surrounding whitespace removed.

        Raises:
            ValueError: If ``value`` is not a string or contains only
                whitespace.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _require_positive(value: int, name: str) -> int:
        """Validate that a value is a positive, non-Boolean integer.

        Booleans are rejected explicitly even though ``bool`` is a subclass of
        ``int`` in Python.

        Args:
            value: Candidate integer value.
            name: Parameter name included in validation errors.

        Returns:
            The validated positive integer.

        Raises:
            ValueError: If ``value`` is Boolean, is not an integer, or is less
                than one.
        """
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value

    def save(self, key: str, value: Any) -> None:
        """Persist a value through the explicitly configured repository.

        Persistence is opt-in. Generation, expansion, indexing, and graph
        construction never invoke this method automatically.

        Values exposing a Pydantic-style ``model_dump`` method are converted to
        plain Python data before being passed to the repository. Other values
        are forwarded unchanged.

        Args:
            key: Repository key under which the value should be stored.
            value: Generated result or arbitrary payload to persist.

        Raises:
            RuntimeError: If the engine was initialized without a repository.
            Exception: Any repository-specific exception raised by the save
                operation.
        """
        if self.repository is None:
            raise RuntimeError("No repository was supplied; results remain in memory")
        payload = value.model_dump() if hasattr(value, "model_dump") else value
        self.repository.save(key, payload)
