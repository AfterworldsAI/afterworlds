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

The one net-new piece is ``_default_intent_model_caller``: the Issue 7
classifier's ``ModelCallerT`` (``Callable[[str], str]``) is a deliberately
minimal seam with no ``PipelinePassId`` of its own -- it does not go through
``ProviderResolver``/``ProviderAdapter`` like the other passes. Wiring it to
a real (lightweight) Anthropic call is narrow, mechanical assembly, not a
routing/entitlement/safety decision.

``_PerTurnContextBuilder`` (P1 remediation, PR #126 review round 1): the
context builder previously shared one app-lifetime SQLAlchemy Session across
every turn and every story, which is unsafe once real turns run in
``asyncio.to_thread`` with cross-story concurrency permitted (Binding
Decision 8). It now opens one short-lived session per ``assemble()`` call,
mirroring the per-call session pattern the mode session resolvers already
use below. This is wiring/lifecycle correction, not a change to Context
Builder semantics -- stable-prefix-once-per-turn is unaffected.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.fake_pipeline import FakeProviderResolver, fake_intent_model_caller
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
from afterworlds.pipeline.safety.config import SafetyConfig
from afterworlds.pipeline.safety.service import SafetyService
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.service import WriterService
from afterworlds.services.context_builder import (
    ContextBuilderService,
    RetrievalMemoryProvider,
    SQLiteRecentTurnsProvider,
)
from afterworlds.services.intent_classifier import IntentClassifierService
from afterworlds.services.rolling_summary import RollingSummaryService
from afterworlds.services.rules_package import RulesPackageService
from afterworlds.services.story_bible import StoryBibleService


def _default_intent_model_caller() -> Callable[[str], str]:
    """A minimal, standalone model caller for the Issue 7 classifier.

    Deliberately lightweight per known_unknowns.md ("Intent classifier
    approach: Lightweight model call") -- no ProviderAdapter, no pass id, no
    cache markers, no capability routing. Reads the key lazily on each call
    so app construction never fails when the key is unset (dev/CI without
    live credentials); the call itself fails loudly if invoked without one.
    """

    def _call(prompt: str) -> str:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set; cannot perform intent classification."
            )
        client = anthropic.Anthropic(api_key=api_key, max_retries=0)
        response = client.messages.create(
            model=os.environ.get(
                "AFTERWORLDS_INTENT_CLASSIFIER_MODEL", "claude-haiku-4-5-20251001"
            ),
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        first_block = response.content[0]
        return getattr(first_block, "text", "")

    return _call


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
                # the orchestrator catches this and returns a typed
                # PIPELINE_ERROR rather than crashing.
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


def build_orchestrator(session_factory: sessionmaker[Session]) -> OrchestratorService:
    """Assemble the real OrchestratorService from existing typed seams."""
    use_fake_provider = _fake_provider_enabled()
    intent_classifier = IntentClassifierService(
        fake_intent_model_caller
        if use_fake_provider
        else _default_intent_model_caller()
    )

    retrieval_config = RetrievalMemoryConfig.from_env()
    retrieval_memory = ChromaRetrievalMemoryProvider(
        client=build_chroma_client(retrieval_config), config=retrieval_config
    )

    def _story_bible_service(session: Session) -> StoryBibleService:
        return StoryBibleService(session)

    context_builder = _PerTurnContextBuilder(session_factory, retrieval_memory)

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
        branching_session_resolver=_make_branching_session_resolver(session_factory),
        writing_session_resolver=_make_writing_session_resolver(session_factory),
    )


__all__ = ["build_orchestrator"]
