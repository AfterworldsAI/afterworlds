"""Assembles the real ``OrchestratorService`` for ``create_app()``.

This is assembly of already-shipped seams (Issues 3-14a), not new
orchestration/provider/entitlement policy: every constructor call below uses
an existing typed class with its own ``.from_env()`` / factory function.

Mode-specific pass SERVICES (RPG adjudication, Branching writer, Writing OOC
extractors) are wired in Phase 3 alongside the mode surfaces they serve --
``OrchestratorService`` already treats them as optional and falls back to the
generic prose Writer path when absent (ADR-016 Decision 3). The three session
RESOLVER callables (rpg_session_sheet_resolver, branching_session_resolver,
writing_session_resolver) are a different thing -- plain typed reads of
already-persisted session state via existing CRUD, not new pass logic -- and
are wired here because the orchestrator hard-requires them per mode (a real
E2E smoke test surfaced this: an unwired writing_session_resolver produces
PIPELINE_ERROR "cannot determine play status or inject persona context" for
every WRITING turn, not a graceful degrade).

Architecture Note (Round 6 remediation, PR #126 P1): Intent Classification is
a model call and is routed through the selected access path in the product
path, exactly like Planner/Writer/Extractor/Contradiction. Earlier revisions
wired ``IntentClassifierService`` to a standalone ``_default_intent_model_caller``
that read ``ANTHROPIC_API_KEY`` directly and called Anthropic outside
``ProviderResolver`` -- for BYOK turns this either failed (no hosted key) or
silently spent a hosted/server key outside the Sojourner's BYOK pool,
crossing the hosted/BYOK boundary. ``IntentClassifierService`` here is
constructed with ``_unrouted_intent_caller`` only as a constructor-required
placeholder that is never actually invoked: the orchestrator resolves
``TurnProviderBinding`` once per turn (step 0 of ``orchestrate_turn``) and
supplies a provider-routed caller built from ``binding.adapter`` as a
per-call override on every ``classify()`` call (see
``_make_intent_classifier_caller`` in ``pipeline/orchestrator/service.py``),
uniformly in both fake and real provider mode -- fake mode's
``FakeProviderResolver`` already resolves to ``FakeProviderAdapter``, which
now has an ``"intent_classifier"`` branch reusing ``fake_intent_model_caller``'s
canned response. If ``_unrouted_intent_caller`` is ever actually called, that
is itself a defect (a missing per-call override), so it fails loudly rather
than silently reading process credentials or returning a fake response.

``_PerTurnContextBuilder`` (P1 remediation, PR #126 review round 1): the
context builder previously shared one app-lifetime SQLAlchemy Session across
every turn and every story, which is unsafe once real turns run in
``asyncio.to_thread`` with cross-story concurrency permitted (Binding
Decision 8). It now opens one short-lived session per ``assemble()`` call,
mirroring the per-call session pattern the mode session resolvers already
use below. This is wiring/lifecycle correction, not a change to Context
Builder semantics -- stable-prefix-once-per-turn is unaffected.

Retrieval query/write services and ``writing_visible_state_service`` (P1
remediation, PR #126 review round 2): these were left at their ``None``
defaults, so production turns silently ran without the Issue 18 Retrieval
Memory layer and any Writing story already in ``IN_PLAY`` returned
``PIPELINE_ERROR`` (``writing_visible_state_service`` is a hard persona-
validation gate for IN_PLAY Writing turns, unlike ``rpg_visible_state_service``/
``branching_visible_state_service``, which the orchestrator treats as
optional enrichment -- see the ``is not None`` guards around each in
``pipeline/orchestrator/service.py``). All three are existing Issue 17/18
classes, wired here exactly as they already exist:
``RetrievalMemoryWriteService`` and ``ChromaRetrievalMemoryProvider`` share
one Chroma client/config; ``RetrievalQueryBuilder`` needs a session-bound
``SQLiteRecentTurnsProvider``, so it gets the same per-call-session
treatment as ``_PerTurnContextBuilder`` (a shared, app-lifetime session here
would reintroduce the identical cross-story-concurrency defect); and
``WritingVisibleStateService`` is constructed from the existing
``get_default_registry()`` singleton, the same factory ``api/visible_state.py``
and ``api/routes/personas.py`` already use. RPG/Branching mode-specific pass
SERVICES (adjudication, BranchingWriterService) remain deliberately unwired
per the module docstring above -- this is required product wiring for
already-optional-but-load-bearing dependencies, not new mode policy.

``_make_rpg_session_resolver`` / ``rpg_session_resolver`` (P1 remediation, PR
#126 round 3): ``_make_rpg_session_sheet_resolver`` requires a completed
``Dnd5eCharacterSheet``, which does not exist yet during RPG setup (only
``RpgCharacterSheetBase`` is bootstrapped at story creation) -- wiring it as
the *only* RPG session resolver made every RPG setup turn's mandatory
retrieval-marker classification fail closed as ``PIPELINE_ERROR``, since the
orchestrator only needs ``play_status`` for that classification, not a
sheet. ``_make_rpg_session_resolver`` is a session-state-only sibling of the
existing Writing/Branching session resolvers above (same pattern, no new
CRUD); the orchestrator now prefers it for play-status resolution and falls
back to the sheet resolver only when the newer one is not wired (see its
docstring in ``pipeline/orchestrator/service.py``). The sheet resolver is
still wired and still required for genuinely sheet-dependent paths
(adjudication, pending-roll consume) -- none of which are reachable through
Issue 19's product wiring today, since RPG adjudication remains unwired.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.fake_pipeline import FakeProviderResolver
from afterworlds.models.character_sheet import Dnd5eCharacterSheet
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.retrieval import RetrievalQueryRequest
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.models.session import (
    BranchingSessionState,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.models.turn import Turn
from afterworlds.modes.personas.registry import get_default_registry
from afterworlds.persistence.crud.character_sheet import get_dnd5e_sheet
from afterworlds.persistence.crud.session_state import (
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
)
from afterworlds.pipeline.contradiction.config import ContradictionConfig
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.extractor.config import ExtractorConfig
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.planner.config import PlannerConfig
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.provider import (
    CapabilityProfileAwareSafetyPolicy,
    HostedRoutingConfig,
    ProviderResolver,
)
from afterworlds.pipeline.provider.credentials import make_credential_store
from afterworlds.pipeline.retrieval.chroma_provider import ChromaRetrievalMemoryProvider
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.query_builder import RetrievalQueryBuilder
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService
from afterworlds.pipeline.safety.config import SafetyConfig
from afterworlds.pipeline.safety.service import SafetyService
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.service import WriterService
from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService
from afterworlds.services.context_builder import (
    ContextBuilderService,
    RetrievalMemoryProvider,
    SQLiteRecentTurnsProvider,
)
from afterworlds.services.intent_classifier import IntentClassifierService
from afterworlds.services.rolling_summary import RollingSummaryService
from afterworlds.services.rules_package import RulesPackageService
from afterworlds.services.story_bible import StoryBibleService


def _unrouted_intent_caller(prompt: str) -> str:
    """Constructor-required placeholder for ``IntentClassifierService`` --
    never actually invoked in the product path.

    The orchestrator always supplies a provider-routed caller as a per-call
    ``classify(..., model_caller=...)`` override (see the module docstring's
    Architecture Note). If this placeholder is ever called, that means the
    override was missed -- fail loudly instead of silently reading process
    credentials or returning a canned response.
    """
    raise RuntimeError(
        "IntentClassifierService's constructor-default model_caller was "
        "invoked directly -- the product path must always supply a "
        "provider-routed model_caller override via orchestrate_turn()."
    )


def _fake_provider_enabled() -> bool:
    """DoR-B: "faked provider passes, no real provider calls in default CI".

    Env-gated, never true in the product/dev path -- only the E2E CI job
    (frontend/playwright.config.ts) and equivalent test harnesses set this.
    """
    return os.environ.get("AFTERWORLDS_FAKE_PROVIDER", "").lower() in (
        "1",
        "true",
        "yes",
    )


def _make_writing_session_resolver(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], WritingSessionState | None]:
    def _resolve(story_id: UUID) -> WritingSessionState | None:
        session = session_factory()
        try:
            return get_writing_session_state_by_story(session, story_id)
        finally:
            session.close()

    return _resolve


def _make_branching_session_resolver(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], BranchingSessionState | None]:
    def _resolve(story_id: UUID) -> BranchingSessionState | None:
        session = session_factory()
        try:
            return get_branching_session_state_by_story(session, story_id)
        finally:
            session.close()

    return _resolve


def _make_rpg_session_resolver(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], RpgSessionState | None]:
    """Session-state-only RPG resolver -- never requires a concrete sheet.

    P1 remediation (PR #126 round 3): the orchestrator's mandatory RPG
    turn-retrieval-marker classification needs only ``RpgSessionState.
    play_status``, not a completed ``Dnd5eCharacterSheet``. During RPG setup
    (before Issue 15's conversational character-creation pipeline completes),
    only ``RpgCharacterSheetBase`` exists -- ``_make_rpg_session_sheet_resolver``
    below correctly raises in that state for its own (sheet-requiring)
    callers, but wiring that resolver for play-status resolution made every
    RPG setup turn fail closed as PIPELINE_ERROR. This resolver is wired into
    ``rpg_session_resolver`` instead, which the orchestrator now prefers for
    that purpose (see its docstring in ``pipeline/orchestrator/service.py``).
    """

    def _resolve(story_id: UUID) -> RpgSessionState | None:
        session = session_factory()
        try:
            return get_rpg_session_state_by_story(session, story_id)
        finally:
            session.close()

    return _resolve


def _make_rpg_session_sheet_resolver(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], tuple[RpgSessionState, Dnd5eCharacterSheet]]:
    def _resolve(story_id: UUID) -> tuple[RpgSessionState, Dnd5eCharacterSheet]:
        session = session_factory()
        try:
            state = get_rpg_session_state_by_story(session, story_id)
            if state is None:
                raise ValueError(f"no RpgSessionState for story {story_id}")
            sheet = get_dnd5e_sheet(session, state.character_sheet_id)
            if sheet is None:
                # Expected during RPG setup, before Issue 15's conversational
                # character-creation pipeline has produced a full sheet --
                # callers of THIS resolver (adjudication/pending-roll/sheet-
                # dependent paths) correctly need a concrete sheet and fail
                # closed here. Play-status-only resolution no longer uses
                # this resolver -- see _make_rpg_session_resolver above.
                raise ValueError(
                    f"no Dnd5eCharacterSheet yet for story {story_id}"
                    " (character creation not complete)"
                )
            return state, sheet
        finally:
            session.close()

    return _resolve


class _PerTurnContextBuilder:
    """Assembles context via a fresh SQLAlchemy Session per ``assemble()`` call.

    ``ContextBuilderService`` itself takes already-session-bound service
    instances at construction time. The orchestrator is app-lifetime and
    ``POST /turns`` runs real turn work in ``asyncio.to_thread``; Binding
    Decision 8 deliberately permits concurrent turns for *different* stories
    to run without serializing against each other. A single shared
    SQLAlchemy ``Session`` is not thread-safe and can also hold a stale
    SQLite read snapshot across turns. This wrapper opens one short-lived
    session per call, builds a throwaway session-bound ``ContextBuilderService``
    from it, delegates immediately, and closes the session -- mirroring the
    per-call session pattern already used by the mode session resolvers
    below. Stable-prefix-once-per-turn is unaffected: ``assemble()`` still
    calls ``build_stable_prefix``/``build_volatile_suffix`` exactly once per
    invocation, and the orchestrator calls ``assemble()`` exactly once per
    turn (see ``_build_context`` in ``pipeline/orchestrator/service.py``).

    Not a ``ContextBuilderService`` subclass -- a narrow, duck-typed
    ``assemble()`` substitution (the same pattern already used for
    ``FakeProviderResolver`` below), passed with a documented
    ``# type: ignore[arg-type]``.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        retrieval_memory: RetrievalMemoryProvider,
    ) -> None:
        self._session_factory = session_factory
        self._retrieval_memory = retrieval_memory

    def assemble(
        self,
        story_id: UUID,
        mode: StoryMode,
        current_input: str,
        classified_intent: IntentClassificationResult,
        rule_slice_request: RuleSliceRequest | None = None,
        retrieval_query_request: RetrievalQueryRequest | None = None,
    ) -> AssembledContext:
        session = self._session_factory()
        try:
            per_turn_builder = ContextBuilderService(
                story_bible_service=StoryBibleService(session),
                rolling_summary_service=RollingSummaryService(
                    session,
                    generator=lambda _prior, _texts: "",
                ),
                recent_turns_provider=SQLiteRecentTurnsProvider(session),
                retrieval_memory=self._retrieval_memory,
                rules_package_service=RulesPackageService(session),
            )
            return per_turn_builder.assemble(
                story_id,
                mode,
                current_input,
                classified_intent,
                rule_slice_request,
                retrieval_query_request,
            )
        finally:
            session.close()


class _PerTurnRecentTurnsProvider:
    """``get_recent_turns()`` duck-type opening a fresh Session per call.

    ``RetrievalQueryBuilder`` is constructed once at app-lifetime, but its
    ``recent_turns_provider`` dependency (``SQLiteRecentTurnsProvider``)
    requires a session-bound instance. Binding a single shared session to it
    here would reintroduce the exact cross-story-concurrency defect
    ``_PerTurnContextBuilder`` above already fixes. Mirrors that class's
    pattern instead: open, delegate, close, once per ``get_recent_turns()``
    call. ``RetrievalQueryBuilder.build_query_request()`` calls this exactly
    once per turn, before context assembly.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_recent_turns(
        self, story_id: UUID, limit: int, *, exclude_ooc: bool = True
    ) -> list[Turn]:
        session = self._session_factory()
        try:
            return SQLiteRecentTurnsProvider(session).get_recent_turns(
                story_id, limit, exclude_ooc=exclude_ooc
            )
        finally:
            session.close()


def build_orchestrator(session_factory: sessionmaker[Session]) -> OrchestratorService:
    """Assemble the real OrchestratorService from existing typed seams."""
    use_fake_provider = _fake_provider_enabled()
    # Uniform in both fake and real mode: the orchestrator always supplies a
    # provider-routed model_caller override per call (see module docstring's
    # Architecture Note) -- fake mode's FakeProviderResolver already resolves
    # to FakeProviderAdapter, which answers pass_id="intent_classifier".
    intent_classifier = IntentClassifierService(_unrouted_intent_caller)

    retrieval_config = RetrievalMemoryConfig.from_env()
    # One Chroma client shared by the read (ChromaRetrievalMemoryProvider) and
    # write (RetrievalMemoryWriteService) sides of Retrieval Memory -- both
    # operate on the same story_memory collection under the same config.
    chroma_client = build_chroma_client(retrieval_config)
    retrieval_memory = ChromaRetrievalMemoryProvider(
        client=chroma_client, config=retrieval_config
    )
    retrieval_write_service = RetrievalMemoryWriteService(
        client=chroma_client, config=retrieval_config
    )
    retrieval_query_builder = RetrievalQueryBuilder(
        recent_turns_provider=_PerTurnRecentTurnsProvider(session_factory),
        session_factory=session_factory,
    )

    def _story_bible_service(session: Session) -> StoryBibleService:
        return StoryBibleService(session)

    context_builder = _PerTurnContextBuilder(session_factory, retrieval_memory)
    writing_visible_state_service = WritingVisibleStateService(get_default_registry())

    provider_resolver: ProviderResolver | FakeProviderResolver
    if use_fake_provider:
        provider_resolver = FakeProviderResolver()
    else:
        hosted_config = HostedRoutingConfig(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        )
        provider_resolver = ProviderResolver(
            credential_store=make_credential_store(),
            hosted_config=hosted_config,
            session_factory=session_factory,
        )

    # WriterService/ExtractorService require a Session at construction, but
    # the orchestrator always passes its own per-turn outer-transaction
    # session explicitly at call time (session=session, see service.py
    # writer/extractor call sites) -- the constructor-time session below is
    # never used for real turn processing, just a required placeholder.
    placeholder_session = session_factory()

    return OrchestratorService(
        intent_classifier=intent_classifier,
        # _PerTurnContextBuilder duck-types assemble() only (fresh Session per
        # call, see its docstring) -- not a ContextBuilderService subclass, a
        # deliberate, narrow protocol substitution mirroring the
        # FakeProviderResolver pattern below.
        context_builder=context_builder,  # type: ignore[arg-type]
        safety_service=SafetyService(SafetyConfig.from_env()),
        planner_service=PlannerService(PlannerConfig.from_env()),
        writer_service=WriterService(placeholder_session, WriterConfig.from_env()),
        extractor_service=ExtractorService(
            placeholder_session,
            _story_bible_service(placeholder_session),
            ExtractorConfig.from_env(),
        ),
        contradiction_service=ContradictionService(ContradictionConfig.from_env()),
        session_factory=session_factory,
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        # FakeProviderResolver duck-types resolve_for_turn only (E2E/CI-only,
        # gated by AFTERWORLDS_FAKE_PROVIDER) -- not a ProviderResolver
        # subclass, so this is a deliberate, narrow protocol substitution.
        provider_resolver=provider_resolver,  # type: ignore[arg-type]
        rpg_session_sheet_resolver=_make_rpg_session_sheet_resolver(session_factory),
        rpg_session_resolver=_make_rpg_session_resolver(session_factory),
        branching_session_resolver=_make_branching_session_resolver(session_factory),
        writing_session_resolver=_make_writing_session_resolver(session_factory),
        writing_visible_state_service=writing_visible_state_service,
        retrieval_write_service=retrieval_write_service,
        retrieval_query_builder=retrieval_query_builder,
    )


__all__ = ["build_orchestrator"]
