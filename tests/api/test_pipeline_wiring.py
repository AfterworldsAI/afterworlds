"""P1 regression: context assembly uses a fresh Session per turn.

Prior to this fix, ``build_orchestrator()`` opened one SQLAlchemy Session at
app-construction time and shared it, captured inside StoryBibleService /
RollingSummaryService / SQLiteRecentTurnsProvider / RulesPackageService, for
every subsequent turn across every story. Real turns run inside
``asyncio.to_thread`` and Binding Decision 8 permits concurrent turns for
*different* stories to run without serializing -- a shared, non-thread-safe
Session is unsafe under that concurrency model and can also hold a stale
SQLite read snapshot. ``_PerTurnContextBuilder`` replaces it with one
short-lived session per ``assemble()`` call.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.api.pipeline_wiring import _PerTurnContextBuilder
from afterworlds.models.enums import IntentType, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.services.context_builder import NullRetrievalMemoryProvider as _NullRM


def _classified_intent() -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.9,
        raw_input="look around",
        ambiguous=False,
        secondary_intent=None,
    )


@pytest.fixture()
def _spying_session_factory():  # type: ignore[no-untyped-def]
    """A session_factory that records every Session it creates and each close()."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    real_factory = create_session_factory(engine)

    created: list[object] = []
    closed: list[object] = []

    def factory():  # type: ignore[no-untyped-def]
        session = real_factory()
        created.append(session)
        real_close = session.close

        def _tracking_close() -> None:
            closed.append(session)
            real_close()

        session.close = _tracking_close  # type: ignore[method-assign]
        return session

    yield factory, created, closed
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_assemble_opens_a_fresh_session_per_call(_spying_session_factory) -> None:  # type: ignore[no-untyped-def]
    factory, created, closed = _spying_session_factory
    builder = _PerTurnContextBuilder(factory, _NullRM())

    story_id = uuid4()
    builder.assemble(story_id, StoryMode.WRITING, "hello", _classified_intent())
    builder.assemble(story_id, StoryMode.WRITING, "hello again", _classified_intent())

    assert len(created) == 2, "each assemble() call must open its own Session"
    assert created[0] is not created[1], "the two calls must not share one Session"
    assert set(closed) == set(created), "every opened Session must be closed"


def test_assemble_closes_session_even_on_failure(
    _spying_session_factory,  # type: ignore[no-untyped-def]
    tmp_path,  # type: ignore[no-untyped-def]
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    """An UnknownModeError mid-assemble must not leak the per-call Session."""
    import afterworlds.services.context_builder as context_builder_module
    from afterworlds.services.context_builder import UnknownModeError

    # No mode-contract files exist under this empty tmp_path -> load_mode_contract
    # raises UnknownModeError before any DB work happens.
    monkeypatch.setattr(context_builder_module, "_PROMPT_DIR", tmp_path)

    factory, created, closed = _spying_session_factory
    builder = _PerTurnContextBuilder(factory, _NullRM())

    with pytest.raises(UnknownModeError):
        builder.assemble(uuid4(), StoryMode.WRITING, "hello", _classified_intent())

    assert len(created) == 1
    assert closed == created, "the session must be closed even when assemble() raises"


def test_concurrent_stories_get_independent_sessions(_spying_session_factory) -> None:  # type: ignore[no-untyped-def]
    """Two different stories' assemble() calls never observe each other's Session."""
    factory, created, closed = _spying_session_factory
    builder = _PerTurnContextBuilder(factory, _NullRM())

    story_a, story_b = uuid4(), uuid4()
    builder.assemble(story_a, StoryMode.WRITING, "a", _classified_intent())
    builder.assemble(story_b, StoryMode.BRANCHING, "b", _classified_intent())

    assert len(created) == 2
    assert created[0] is not created[1]
    assert set(closed) == set(created)
