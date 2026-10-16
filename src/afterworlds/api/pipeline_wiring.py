"""Assembles the real ``OrchestratorService`` for ``create_app()``.

This is assembly of already-shipped seams (Issues 3-14a), not new
orchestration/provider/entitlement policy: every constructor call below uses
an existing typed class with its own ``.from_env()`` / factory function.

Mode-specific pass SERVICES (Branching writer, Writing OOC extractors) are
wired in Phase 3 alongside the mode surfaces they serve; RPG adjudication and
its dice service are wired by CRD Issue 15c (backend rolls only) --
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
SERVICES (BranchingWriterService) remain deliberately unwired
per the module docstring above -- this is required product wiring for
already-optional-but-load-bearing dependencies, not new mode policy.

``_make_rpg_session_resolver`` / ``rpg_session_resolver`` (P1 remediation, PR
#126 round 3): ``_make_rpg_session_sheet_resolver`` requires recorded CRD
Issue 2b character state, which does not exist yet during RPG setup (only
``RpgCharacterSheetBase`` is bootstrapped at story creation) -- wiring it as
the *only* RPG session resolver made every RPG setup turn's mandatory
retrieval-marker classification fail closed as ``PIPELINE_ERROR``, since the
orchestrator only needs ``play_status`` for that classification, not a
sheet. ``_make_rpg_session_resolver`` is a session-state-only sibling of the
existing Writing/Branching session resolvers above (same pattern, no new
CRUD); the orchestrator now prefers it for play-status resolution and falls
back to the sheet resolver only when the newer one is not wired (see its
docstring in ``pipeline/orchestrator/service.py``). The sheet resolver is
still wired and still required for genuinely sheet-dependent paths:
adjudication, which CRD Issue 15c wires, and the action-resolution sequence
service of CRD Issue 15b, which re-reads the acting character at every
advancement. The legacy total-only pending-roll consume path is retired.

``build_pipeline`` (CRD Issue 15b Phase 3) returns that one
``ActionResolutionService`` alongside the orchestrator that owns it, so
``create_app`` can expose the same instance to the thin RPG action routes
without reaching into the orchestrator or constructing a second one.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.fake_pipeline import FakeProviderResolver
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.retrieval import RetrievalQueryRequest
from afterworlds.models.rpg import SubjectRef
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.models.session import (
    BranchingSessionState,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.models.turn import Turn
from afterworlds.modes.personas.registry import get_default_registry
from afterworlds.persistence.crud.session_state import (
    get_branching_session_state_by_story,
    get_rpg_session_state_by_story,
    get_writing_session_state_by_story,
)
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCharacterStateORM,
    Dnd5eCreatureORM,
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
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.config import AdjudicationConfig
from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
from afterworlds.pipeline.rpg.scene import render as render_scene
from afterworlds.pipeline.rpg.sequence import ActionResolutionService
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
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
from afterworlds.services.dnd5e_state.coordination import (
    StoredCoordination,
)
from afterworlds.services.dnd5e_state.coordination import read as read_coordination
from afterworlds.services.dnd5e_state.turn import (
    RpgTurnHold,
    TurnCharacter,
    TurnSubject,
    load_turn_character,
    load_turn_creature,
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


def fake_provider_enabled() -> bool:
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
    play_status``, not recorded character state. During RPG setup
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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _make_rpg_session_sheet_resolver(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], tuple[RpgSessionState, TurnCharacter]]:
    """The session state and the bound character an adjudicating turn reads.

    Refuses (raises, which the orchestrator turns into a typed
    ``PIPELINE_ERROR``) when the story has no recorded character state yet, or
    when the character's recorded binding is not the package's current exact
    binding: stale, unpublished, quarantined or invalid authority is never
    read as though it were current (CRD Issue 2b). Readiness is computed here
    and carried on the result; it is not legality.
    """

    def _resolve(story_id: UUID) -> tuple[RpgSessionState, TurnCharacter]:
        session = session_factory()
        try:
            state = get_rpg_session_state_by_story(session, story_id)
            if state is None:
                raise ValueError(f"no RpgSessionState for story {story_id}")
            character = load_turn_character(
                session, state.character_sheet_id, now=_utc_now()
            )
            # Resolution retained the current override-set version; keep it so
            # a later replay of this exact binding can read it.
            session.commit()
            return state, character
        finally:
            session.close()

    return _resolve


def _make_rpg_subject_loader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID, SubjectRef], TurnSubject]:
    """Reads a character or creature an operation names (CRD Issue 15c), with
    its own exact binding and revision. Refuses one of another story or under
    a non-current binding, as the acting character's resolver does; the
    orchestrator rechecks its revision and binding at commit."""

    def _load(story_id: UUID, ref: SubjectRef) -> TurnSubject:
        session = session_factory()
        try:
            if ref.kind == "creature":
                subject: TurnSubject = load_turn_creature(
                    session, story_id, ref.subject_id, now=_utc_now()
                )
            else:
                subject = load_turn_character(session, ref.subject_id, now=_utc_now())
                if subject.stored.story_id != story_id:
                    raise ValueError(
                        f"character {ref.subject_id} is not in story {story_id}"
                    )
            session.commit()
            return subject
        finally:
            session.close()

    return _load


def _make_rpg_coordination_loader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], StoredCoordination]:
    """Reads a story's actor-turn coordination (CRD Issue 15c, contract G1);
    the orchestrator commits the turn's edges by compare-and-swap on it."""

    def _load(story_id: UUID) -> StoredCoordination:
        session = session_factory()
        try:
            return read_coordination(session, story_id)
        finally:
            session.close()

    return _load


def _bounded_by(document: Any, ref: SubjectRef) -> bool:
    """Whether a state document holds an effect bounded by *ref*'s turn."""
    if not isinstance(document, dict):
        document = json.loads(document)
    held = (
        *(document.get("active_effects") or ()),
        *(document.get("conditions") or ()),
    )
    for effect in held:
        turn = (effect.get("ends") or {}).get("turn")
        if turn and turn["of"] == {"kind": ref.kind, "subject_id": str(ref.subject_id)}:
            return True
    return False


def _make_rpg_bounded_loader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID, SubjectRef], list[TurnSubject]]:
    """Reads every character and creature of a story holding an effect bounded
    by a subject's turn (CRD Issue 15c, contract G2): an edge of that turn ends
    them, and the orchestrator rechecks each one at commit."""

    def _load(story_id: UUID, ref: SubjectRef) -> list[TurnSubject]:
        session = session_factory()
        try:
            found: list[TurnSubject] = []
            characters = session.execute(
                sa.select(
                    Dnd5eCharacterStateORM.sheet_id, Dnd5eCharacterStateORM.document
                ).where(Dnd5eCharacterStateORM.story_id == str(story_id))
            ).all()
            for sheet_id, document in characters:
                if _bounded_by(document, ref):
                    found.append(
                        load_turn_character(session, UUID(sheet_id), now=_utc_now())
                    )
            creatures = session.execute(
                sa.select(
                    Dnd5eCreatureORM.creature_id, Dnd5eCreatureORM.document
                ).where(Dnd5eCreatureORM.story_id == str(story_id))
            ).all()
            for creature_id, document in creatures:
                if _bounded_by(document, ref):
                    found.append(
                        load_turn_creature(
                            session, story_id, UUID(creature_id), now=_utc_now()
                        )
                    )
            session.commit()
            return found
        finally:
            session.close()

    return _load


def _make_rpg_discovery_reader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], frozenset[tuple[str, str, int]]]:
    """The story snapshot discovery scans rest on (CRD Issue 15c)."""
    from afterworlds.services.dnd5e_state.turn import story_revisions

    def _read(story_id: UUID) -> frozenset[tuple[str, str, int]]:
        session = session_factory()
        try:
            return story_revisions(session, story_id)
        finally:
            session.close()

    return _read


def _make_rpg_aura_loader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID], list[TurnCharacter]]:
    """Reads every character of a story, so a save another character's aura
    could change is found (CRD Issue 15c, bystanders)."""

    def _load(story_id: UUID) -> list[TurnCharacter]:
        session = session_factory()
        try:
            now = _utc_now()
            sheets = session.execute(
                sa.select(Dnd5eCharacterStateORM.sheet_id).where(
                    Dnd5eCharacterStateORM.story_id == str(story_id)
                )
            ).all()
            found = [load_turn_character(session, UUID(s), now=now) for (s,) in sheets]
            session.commit()
            return found
        finally:
            session.close()

    return _load


def _make_rpg_scene_loader(
    session_factory: sessionmaker[Session],
) -> Callable[[UUID, TurnCharacter], str]:
    """Renders the story's mechanical scene for the GameMaster (CRD Issue
    15c): every character and creature of the story with the ids a proposal
    may name, and the active turn."""

    def _load(story_id: UUID, actor: TurnCharacter) -> str:
        session = session_factory()
        try:
            now = _utc_now()
            others: list[TurnSubject] = []
            for (sheet_id,) in session.execute(
                sa.select(Dnd5eCharacterStateORM.sheet_id).where(
                    Dnd5eCharacterStateORM.story_id == str(story_id)
                )
            ).all():
                if UUID(sheet_id) != actor.sheet_id:
                    others.append(load_turn_character(session, UUID(sheet_id), now=now))
            for (creature_id,) in session.execute(
                sa.select(Dnd5eCreatureORM.creature_id).where(
                    Dnd5eCreatureORM.story_id == str(story_id)
                )
            ).all():
                others.append(
                    load_turn_creature(session, story_id, UUID(creature_id), now=now)
                )
            coordination = read_coordination(session, story_id).document
            session.commit()
            return render_scene(actor, others, coordination)
        finally:
            session.close()

    return _load


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
            assembled = per_turn_builder.assemble(
                story_id,
                mode,
                current_input,
                classified_intent,
                rule_slice_request,
                retrieval_query_request,
            )
            # Context assembly reads only, except that resolving a rule slice's
            # binding retains its override-set version in this session
            # (ADR-005d Decision 9: the caller owns that commit). Committing it
            # keeps the binding the stable prefix names replayable. This runs
            # before the orchestrator opens the turn's outer transaction.
            if assembled.stable_prefix.rules_package_slice is not None:
                session.commit()
            return assembled
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
    return build_pipeline(session_factory)[0]


def build_pipeline(
    session_factory: sessionmaker[Session],
) -> tuple[OrchestratorService, ActionResolutionService]:
    """The real OrchestratorService and the ActionResolutionService it owns."""
    use_fake_provider = fake_provider_enabled()
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

    # CRD Issue 15c: the RPG adjudication pass runs after Planner and before
    # Writer on in-play turns. CRD Issue 15b: a turn whose resolution needs
    # the Sojourner (their own die, or a result-triggered decision) becomes a
    # persisted action-resolution sequence, which the orchestrator starts on
    # its announce Turn, gates in-character input on, and narrates through
    # orchestrate_rpg_resume. The sequence service shares the adjudication
    # service's readers, dice and resolver.
    rpg_adjudication = RpgAdjudicationPassService(
        D20RulesSystemAdapter(),
        AdjudicationConfig.from_env(),
        subject_loader=_make_rpg_subject_loader(session_factory),
        coordination_loader=_make_rpg_coordination_loader(session_factory),
        bounded_loader=_make_rpg_bounded_loader(session_factory),
        scene_loader=_make_rpg_scene_loader(session_factory),
        aura_loader=_make_rpg_aura_loader(session_factory),
        discovery_reader=_make_rpg_discovery_reader(session_factory),
    )
    rpg_dice = SystemRandomDiceService()
    rpg_sheet_resolver = _make_rpg_session_sheet_resolver(session_factory)
    rpg_sequences = ActionResolutionService(
        rpg_adjudication,
        D20RulesSystemAdapter(),
        rpg_dice,
        session_factory,
        rpg_sheet_resolver,
    )

    orchestrator = OrchestratorService(
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
        rpg_adjudication_service=rpg_adjudication,
        rpg_dice_service=rpg_dice,
        rpg_session_sheet_resolver=rpg_sheet_resolver,
        rpg_sequence_service=rpg_sequences,
        rpg_turn_hold=RpgTurnHold(session_factory, _utc_now),
        rpg_session_resolver=_make_rpg_session_resolver(session_factory),
        branching_session_resolver=_make_branching_session_resolver(session_factory),
        writing_session_resolver=_make_writing_session_resolver(session_factory),
        writing_visible_state_service=writing_visible_state_service,
        retrieval_write_service=retrieval_write_service,
        retrieval_query_builder=retrieval_query_builder,
    )
    return orchestrator, rpg_sequences


__all__ = ["build_orchestrator", "build_pipeline"]
