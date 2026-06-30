"""Shared fixtures and fakes for OrchestratorService tests — CRD Issue 12c.

These fixtures build a real SQLite session factory (so SAVEPOINT semantics
can be proved against an actual database) and provide fake pass services
that record their calls.  No real provider calls are made.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest

# Ensure all ORM models populate Base.metadata.
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import CastRole, IntentType, StoryMode
from afterworlds.models.intent_classification import (
    IntentClassificationError,
    IntentClassificationResult,
)
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    StateDelta,
)
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.story_bible import CastEntry, StoryBibleContext
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_node
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionResult,
    ContradictionVerdict,
    ContradictionViolation,
)
from afterworlds.pipeline.extractor.models import ExtractorResult
from afterworlds.pipeline.planner.models import (
    PlannerOutput,
    PlannerResult,
)
from afterworlds.pipeline.safety.models import (
    SafetyReport,
    SafetyResult,
    SafetyTarget,
)
from afterworlds.pipeline.writer.models import WriterResult

# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """File-backed SQLite engine so SAVEPOINT semantics behave realistically."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    """Session factory the orchestrator can call to open one session per turn."""
    return create_session_factory(engine)


@pytest.fixture()
def session(session_factory):  # type: ignore[no-untyped-def]
    sess = session_factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def seeded_story(session) -> tuple[UUID, UUID]:  # type: ignore[no-untyped-def]
    """Persist a Story / Arc / Chapter / Node chain; return (story_id, node_id)."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Orchestrator Test Story",
        mode=StoryMode.BRANCHING,
        created_at=now,
        updated_at=now,
    )
    create_story(session, story)
    arc = Arc(story_id=story.story_id, title="Arc 1", order=0)
    create_arc(session, arc)
    chapter = Chapter(arc_id=arc.arc_id, title="Chapter 1", order=0)
    create_chapter(session, chapter)
    node = Node(
        chapter_id=chapter.chapter_id,
        content="",
        state_delta=StateDelta(),
        branching_logic=[],
        intent_type=IntentType.IN_CHARACTER_ACTION,
        metadata=NodeMetadata(timestamp=now),
        mode_metadata=BranchingNodeMetadata(),
    )
    create_node(session, node)
    session.commit()
    return story.story_id, node.node_id


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------


def make_intent(
    intent_type: IntentType = IntentType.IN_CHARACTER_ACTION,
    raw_input: str = "I open the door.",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent_type,
        confidence=0.95,
        raw_input=raw_input,
        ambiguous=False,
    )


def make_stable_prefix(story_id: UUID) -> StablePrefix:
    return StablePrefix(
        system_prompt="You are the story architect.",
        story_bible_context=StoryBibleContext(
            story_id=story_id,
            setting=None,
            cast=(
                CastEntry(
                    story_id=story_id,
                    name="Aldric",
                    role=CastRole.PROTAGONIST,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
            ),
            locked_facts=(),
            forbidden_facts=(),
            relationship_ledger=(),
            active_plot_threads=(),
            events=(),
        ),
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )


def make_assembled(
    story_id: UUID, intent: IntentClassificationResult | None = None
) -> AssembledContext:
    icr = intent if intent is not None else make_intent()
    return AssembledContext(
        stable_prefix=make_stable_prefix(story_id),
        volatile_suffix=VolatileSuffix(
            recent_turns=[],
            current_input=icr.raw_input,
            classified_intent=icr,
        ),
        pass_forward_ledger=PassForwardLedger(),
    )


# ---------------------------------------------------------------------------
# Fake pass services
# ---------------------------------------------------------------------------


@dataclass
class FakeIntentClassifier:
    intent: IntentClassificationResult
    raise_error: bool = False
    raise_exc: Exception | None = None
    calls: list[tuple[str, UUID]] = field(default_factory=list)

    def classify(
        self, raw_input: str, story_id: UUID, hints: Any = None
    ) -> IntentClassificationResult:
        self.calls.append((raw_input, story_id))
        if self.raise_exc is not None:
            raise self.raise_exc
        if self.raise_error:
            raise IntentClassificationError("synthetic failure")
        # Override raw_input to match the actual submitted input.
        return self.intent.model_copy(update={"raw_input": raw_input})


@dataclass
class FakeContextBuilder:
    contexts: dict[UUID, AssembledContext] = field(default_factory=dict)
    calls: list[tuple[UUID, StoryMode, str]] = field(default_factory=list)

    def assemble(
        self,
        story_id: UUID,
        mode: StoryMode,
        current_input: str,
        classified_intent: IntentClassificationResult,
        rule_slice_request: Any = None,
    ) -> AssembledContext:
        self.calls.append((story_id, mode, current_input))
        if story_id not in self.contexts:
            self.contexts[story_id] = make_assembled(story_id, classified_intent)
        ctx = self.contexts[story_id]
        # Bind a fresh volatile suffix carrying the actual current input + intent
        # and a fresh ledger so the orchestrator's "append Planner output" works
        # without leaking between tests.
        return AssembledContext(
            stable_prefix=ctx.stable_prefix,
            volatile_suffix=VolatileSuffix(
                recent_turns=list(ctx.volatile_suffix.recent_turns),
                current_input=current_input,
                classified_intent=classified_intent,
            ),
            pass_forward_ledger=PassForwardLedger(),
        )


@dataclass
class FakeSafetyService:
    """Programmable Safety fake — different verdicts/errors per target."""

    input_verdict: SafetyResult | Callable[[], SafetyResult] | Exception | None = None
    output_verdict: SafetyResult | Callable[[], SafetyResult] | Exception | None = None
    calls: list[tuple[SafetyTarget, str]] = field(default_factory=list)

    def check(
        self,
        built_context: AssembledContext,
        text: str,
        target: SafetyTarget,
        *,
        provider: Any = None,
    ) -> SafetyResult:
        self.calls.append((target, text))
        cfg = (
            self.input_verdict if target is SafetyTarget.INPUT else self.output_verdict
        )
        if cfg is None:
            return SafetyResult(
                report=SafetyReport(concerns=[]),
                target=target,
            )
        if isinstance(cfg, Exception):
            raise cfg
        if callable(cfg):
            return cfg()
        return cfg


@dataclass
class FakePlannerService:
    result: PlannerResult | None = None
    raise_exc: Exception | None = None
    calls: list[AssembledContext] = field(default_factory=list)

    def plan(
        self, built_context: AssembledContext, *, provider: Any = None
    ) -> PlannerResult:
        self.calls.append(built_context)
        if self.raise_exc is not None:
            raise self.raise_exc
        if self.result is None:
            return PlannerResult(
                plan=PlannerOutput(
                    scene_goal="advance scene",
                    next_beat="player acts",
                    facts_needed=["world state"],
                    notes=None,
                ),
                model_identifier="anthropic:fake-haiku",
                latency_ms=5,
                input_token_count=100,
                output_token_count=20,
                cache_read_token_count=80,
                cache_creation_token_count=0,
            )
        return self.result


@dataclass
class FakeWriterService:
    """Fake Writer that persists a Turn via the supplied session."""

    raise_exc: Exception | None = None
    assistant_output: str = "Narrator: the door swings open."
    calls: list[tuple[AssembledContext, UUID, UUID, Any]] = field(default_factory=list)
    # When supplied, override turn_id used during persistence (tests rarely
    # need this; the default new UUID matches real behavior).
    _config: Any = field(default=None)

    def write(
        self,
        built_context: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        *,
        provider: Any = None,
        session: Any = None,
        turn_id: UUID | None = None,
    ) -> WriterResult:
        self.calls.append((built_context, story_id, node_id, session))
        if self.raise_exc is not None:
            raise self.raise_exc
        if session is None:
            raise AssertionError(
                "Orchestrator must forward its outer session to Writer"
            )
        from uuid import uuid4

        icr = built_context.volatile_suffix.classified_intent
        effective_turn_id = turn_id if turn_id is not None else uuid4()
        turn = Turn(
            turn_id=effective_turn_id,
            user_input=built_context.volatile_suffix.current_input,
            assistant_output=self.assistant_output,
            timestamp=datetime.now(UTC),
            intent_classification=icr.intent_type,
            node_id=node_id,
            intent_classification_result=icr,
        )
        from afterworlds.persistence.crud.node import create_turn

        create_turn(session, turn)
        return WriterResult(
            turn_id=turn.turn_id,
            assistant_output=self.assistant_output,
            model_identifier="anthropic:fake-sonnet",
            latency_ms=10,
            input_token_count=200,
            output_token_count=50,
            cache_read_token_count=180,
            cache_creation_token_count=0,
        )


@dataclass
class FakeExtractorService:
    """Fake Extractor that calls StoryBibleService.route_extractor_proposals.

    Used in real-SQLite SAVEPOINT integration tests through the real
    StoryBibleService.  Unit tests can supply a no-op fake that just
    returns a stub result.
    """

    raise_exc: Exception | None = None
    delay_seconds: float = 0.0
    thread_observation: dict[str, int] = field(default_factory=dict)
    calls: list[tuple[AssembledContext, str, UUID, UUID, Any]] = field(
        default_factory=list
    )
    canned_result: ExtractorResult | None = None
    # When supplied, perform real Story Bible writes via this service.  When
    # None, returns canned_result without any DB I/O.
    story_bible_service: Any = None
    proposal_set_factory: Callable[[], Any] | None = None

    def extract(
        self,
        built_context: AssembledContext,
        writer_output: str,
        story_id: UUID,
        turn_id: UUID,
        *,
        provider: Any = None,
        session: Any = None,
        skip_story_bible_routing: bool = False,
    ) -> ExtractorResult:
        self.calls.append((built_context, writer_output, story_id, turn_id, session))
        self.thread_observation["extractor"] = threading.get_ident()
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.raise_exc is not None:
            raise self.raise_exc
        if (
            self.story_bible_service is not None
            and self.proposal_set_factory is not None
        ):
            proposal_set = self.proposal_set_factory()
            routed = self.story_bible_service.route_extractor_proposals(
                story_id, turn_id, proposal_set, session=session
            )
            return ExtractorResult(
                proposal_set=proposal_set,
                routed=routed,
                input_token_count=10,
                output_token_count=5,
                cache_read_token_count=0,
                cache_creation_token_count=0,
            )
        if self.canned_result is not None:
            return self.canned_result
        from afterworlds.models.extractor import (
            ExtractorProposalSet,
            ExtractorRoutingSummary,
        )

        return ExtractorResult(
            proposal_set=ExtractorProposalSet(proposals=[]),
            routed=ExtractorRoutingSummary(
                locked_fact_staged_ids=[],
                soft_fact_staged_ids=[],
                transient_state_staged_ids=[],
                unresolved_thread_staged_ids=[],
                event_ids=[],
            ),
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=0,
            cache_creation_token_count=0,
        )


@dataclass
class FakeContradictionService:
    violations: list[ContradictionViolation] | None = None
    raise_exc: Exception | None = None
    delay_seconds: float = 0.0
    thread_observation: dict[str, int] = field(default_factory=dict)
    calls: list[tuple[AssembledContext, str]] = field(default_factory=list)

    def check(
        self,
        built_context: AssembledContext,
        writer_output: str,
        *,
        provider: Any = None,
    ) -> ContradictionResult:
        self.calls.append((built_context, writer_output))
        self.thread_observation["contradiction"] = threading.get_ident()
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        if self.raise_exc is not None:
            raise self.raise_exc
        violations = self.violations or []
        verdict = (
            ContradictionVerdict.BLOCKED if violations else ContradictionVerdict.CLEAR
        )
        return ContradictionResult(
            verdict=verdict,
            violations=violations,
            model_identifier="anthropic:fake-haiku",
            latency_ms=5,
            input_token_count=100,
            output_token_count=10,
            cache_read_token_count=0,
            cache_creation_token_count=0,
        )


# ---------------------------------------------------------------------------
# Test-construction helpers
# ---------------------------------------------------------------------------


def make_refusal(pass_id: PassIdentifier) -> ProviderRefusalError:
    return ProviderRefusalError(
        ProviderRefusal(
            provider="anthropic",
            model="fake-haiku",
            pass_identifier=pass_id,
            coarse_reason="content policy",
            raw_response_excerpt="model declined",
        )
    )


def collect_user_text_blocks(payload: dict[str, Any]) -> list[str]:
    """Pull user-message text blocks out of an Anthropic-style payload."""
    msgs = payload["messages"]
    content = msgs[0]["content"]
    return [b["text"] for b in content]


def find_cache_breakpoint(payload: dict[str, Any]) -> int | None:
    content = payload["messages"][0]["content"]
    for i, b in enumerate(content):
        if b.get("cache_control") is not None:
            return i
    return None


# ---------------------------------------------------------------------------
# Mode resolver
# ---------------------------------------------------------------------------


def fixed_mode_resolver(mode: StoryMode = StoryMode.BRANCHING):  # type: ignore[no-untyped-def]
    def resolve(story_id: UUID) -> StoryMode:
        return mode

    return resolve
