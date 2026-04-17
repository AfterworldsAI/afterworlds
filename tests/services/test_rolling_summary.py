"""Tests for the Rolling Summary service — CRD Issue 6 acceptance criteria.

Coverage targets:
  - Trigger threshold (should_compress): fires at N, 2N, 3N; not in between.
  - Coverage metadata: compressed_from_turn_id, compressed_through_turn_id,
    version_number populated on every row including the first.
  - Idempotency anchored to compressed_through_turn_id (service layer).
  - DB uniqueness constraint on (story_id, compressed_through_turn_id).
  - Append-only versioning: prior rows preserved, version_number monotonic.
  - Current-version invariant: exactly one is_current row per story.
  - DB partial unique index rejects a second is_current=True row.
  - Retrieval: get_current_summary returns None before first compression,
    returns current row after; get_summary_history returns ordered history.
  - Return types are structured typed payloads (RollingSummary, not ORM rows).
  - Generator dependency is injected; no real network call in tests.
  - N is readable from the module constant; changing it changes trigger
    behavior.
  - Configurability: should_compress(n=...) respects caller-supplied N.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# ---------------------------------------------------------------------------
# Import all ORMs so Base.metadata is fully populated
# ---------------------------------------------------------------------------
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rolling_summary  # noqa: F401  — register ORM
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.enums import IntentType, StoryMode
from afterworlds.models.rolling_summary import RollingSummary
from afterworlds.models.story import Story
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.rolling_summary import RollingSummaryORM
from afterworlds.services.rolling_summary import (
    ROLLING_SUMMARY_N,
    RollingSummaryService,
    should_compress,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    # Create the partial unique index (mirrors migration 0006 op.execute).
    with eng.connect() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_rs_current_per_story "
                "ON rolling_summaries (story_id) WHERE is_current = 1"
            )
        )
        conn.commit()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    """SQLAlchemy session bound to the in-memory engine."""
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def story_id(session) -> UUID:  # type: ignore[no-untyped-def]
    """Persist a minimal Story and return its UUID."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Test Story", mode=StoryMode.RPG, created_at=now, updated_at=now
    )
    create_story(session, story)
    session.commit()
    return story.story_id


def _make_turn(session, story_id: UUID, *, label: str = "t") -> UUID:  # type: ignore[no-untyped-def]
    """Persist a minimal Turn row and return its UUID.

    ``node_id`` is intentionally left as None — the FK is nullable and we do
    not need a Node hierarchy to test rolling-summary coverage anchoring.
    Foreign keys are enforced in tests (PRAGMA foreign_keys = ON), so the
    Turn row must genuinely exist; Node ancestry is not required.

    ``story_id`` is accepted for callsite clarity but is not stored on the
    Turn row directly (Turns hang off Nodes, not Stories).  It is included
    in the helper signature to make multi-story tests readable.
    """
    turn_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    session.add(
        TurnORM(
            turn_id=turn_id,
            node_id=None,
            user_input=f"Input {label}",
            assistant_output=f"Output {label}",
            timestamp=now,
            intent_classification=IntentType.ACTION.value,
        )
    )
    session.flush()
    return UUID(turn_id)


def _stub_generator(text_to_return: str = "summary text") -> MagicMock:
    """Return a MagicMock that behaves as a SummaryGeneratorT."""
    gen = MagicMock(return_value=text_to_return)
    return gen


def _make_service(session, generator=None):  # type: ignore[no-untyped-def]
    """Return a RollingSummaryService with a stub generator."""
    if generator is None:
        generator = _stub_generator()
    return RollingSummaryService(session, generator)


# ===========================================================================
# Trigger threshold tests — should_compress()
# ===========================================================================


class TestShouldCompress:
    def test_fires_at_n(self) -> None:
        assert should_compress(ROLLING_SUMMARY_N) is True

    def test_fires_at_2n(self) -> None:
        assert should_compress(ROLLING_SUMMARY_N * 2) is True

    def test_fires_at_3n(self) -> None:
        assert should_compress(ROLLING_SUMMARY_N * 3) is True

    def test_does_not_fire_between_triggers(self) -> None:
        for count in range(1, ROLLING_SUMMARY_N):
            assert should_compress(count) is False, f"should not fire at {count}"

    def test_does_not_fire_at_n_plus_1(self) -> None:
        assert should_compress(ROLLING_SUMMARY_N + 1) is False

    def test_does_not_fire_at_n_minus_1(self) -> None:
        assert should_compress(ROLLING_SUMMARY_N - 1) is False

    def test_does_not_fire_at_zero(self) -> None:
        assert should_compress(0) is False

    def test_n_constant_readable_from_module(self) -> None:
        assert ROLLING_SUMMARY_N == 10

    def test_caller_supplied_n_changes_trigger(self) -> None:
        """Changing n in the call changes trigger behavior."""
        assert should_compress(5, n=5) is True
        assert should_compress(5, n=10) is False
        assert should_compress(10, n=5) is True
        assert should_compress(10, n=10) is True

    def test_fires_at_each_multiple_of_n(self) -> None:
        n = 7  # non-default N
        for k in range(1, 6):
            assert should_compress(n * k, n=n) is True
        for offset in (1, 2, 3, 4, 5, 6):
            assert should_compress(n + offset, n=n) is False


# ===========================================================================
# Coverage metadata tests
# ===========================================================================


class TestCoverageMetadata:
    def test_from_and_through_populated_on_first_compression(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        result = svc.compress(story_id, t1, t10, ["text1", "text10"])

        assert result.compressed_from_turn_id == t1
        assert result.compressed_through_turn_id == t10

    def test_version_number_starts_at_1(self, session, story_id: UUID) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        result = svc.compress(story_id, t1, t10, ["t"] * 10)

        assert result.version_number == 1

    def test_version_number_increments_monotonically(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        t21 = _make_turn(session, story_id, label="t21")
        t30 = _make_turn(session, story_id, label="t30")
        svc = _make_service(session)

        r1 = svc.compress(story_id, t1, t10, ["t"] * 10)
        session.commit()
        r2 = svc.compress(story_id, t11, t20, ["t"] * 10)
        session.commit()
        r3 = svc.compress(story_id, t21, t30, ["t"] * 10)
        session.commit()

        assert r1.version_number == 1
        assert r2.version_number == 2
        assert r3.version_number == 3

    def test_coverage_ids_are_non_nullable_on_every_row(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        result = svc.compress(story_id, t1, t10, ["text"])

        assert result.compressed_from_turn_id is not None
        assert result.compressed_through_turn_id is not None
        assert isinstance(result.compressed_from_turn_id, UUID)
        assert isinstance(result.compressed_through_turn_id, UUID)

    def test_created_at_populated(self, session, story_id: UUID) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        result = svc.compress(story_id, t1, t10, ["text"])

        assert isinstance(result.created_at, datetime)


# ===========================================================================
# Append-only versioning — prior rows preserved
# ===========================================================================


class TestAppendOnly:
    def test_prior_summaries_preserved(self, session, story_id: UUID) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        svc = _make_service(session, _stub_generator("summary-v1"))

        svc.compress(story_id, t1, t10, ["t"] * 10)
        session.commit()

        # Replace generator for second compression
        svc._generator = _stub_generator("summary-v2")
        svc.compress(story_id, t11, t20, ["t"] * 10)
        session.commit()

        history = svc.get_summary_history(story_id)
        assert len(history) == 2
        assert history[0].text == "summary-v1"
        assert history[1].text == "summary-v2"

    def test_three_compressions_preserve_all_rows(
        self, session, story_id: UUID
    ) -> None:
        turns = [_make_turn(session, story_id, label=f"t{i}") for i in range(6)]
        svc = _make_service(session)

        svc.compress(story_id, turns[0], turns[1], ["t", "t"])
        session.commit()
        svc.compress(story_id, turns[2], turns[3], ["t", "t"])
        session.commit()
        svc.compress(story_id, turns[4], turns[5], ["t", "t"])
        session.commit()

        assert len(svc.get_summary_history(story_id)) == 3

    def test_history_ordered_by_version_number(self, session, story_id: UUID) -> None:
        turns = [_make_turn(session, story_id, label=f"t{i}") for i in range(4)]
        svc = _make_service(session)

        svc.compress(story_id, turns[0], turns[1], ["a", "b"])
        session.commit()
        svc.compress(story_id, turns[2], turns[3], ["c", "d"])
        session.commit()

        history = svc.get_summary_history(story_id)
        assert history[0].version_number < history[1].version_number


# ===========================================================================
# Idempotency tests
# ===========================================================================


class TestIdempotency:
    def test_second_compress_same_through_id_returns_existing(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        gen = _stub_generator("generated-text")
        svc = _make_service(session, gen)

        r1 = svc.compress(story_id, t1, t10, ["text"])
        session.commit()
        r2 = svc.compress(story_id, t1, t10, ["text"])

        # Same summary returned; generator called only once.
        assert r2.summary_id == r1.summary_id
        gen.assert_called_once()

    def test_no_duplicate_row_on_repeated_compress(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        svc.compress(story_id, t1, t10, ["text"])
        session.commit()
        svc.compress(story_id, t1, t10, ["text"])
        session.commit()

        assert len(svc.get_summary_history(story_id)) == 1

    def test_db_unique_constraint_rejects_duplicate_through_id(
        self, session, story_id: UUID
    ) -> None:
        """Verify the DB constraint catches a duplicate even without service logic."""
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        now = datetime.now(UTC).isoformat()
        sid = str(story_id)

        row1 = RollingSummaryORM(
            summary_id=str(uuid4()),
            story_id=sid,
            text="first",
            compressed_from_turn_id=str(t1),
            compressed_through_turn_id=str(t10),
            version_number=1,
            is_current=False,
            created_at=now,
        )
        row2 = RollingSummaryORM(
            summary_id=str(uuid4()),
            story_id=sid,
            text="second",
            compressed_from_turn_id=str(t1),
            compressed_through_turn_id=str(t10),  # same through_id — must fail
            version_number=2,
            is_current=False,
            created_at=now,
        )
        session.add(row1)
        session.flush()

        session.add(row2)
        with pytest.raises(IntegrityError):
            session.flush()


# ===========================================================================
# Current-version invariant tests
# ===========================================================================


class TestCurrentVersionInvariant:
    def test_first_compression_is_current(self, session, story_id: UUID) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        result = svc.compress(story_id, t1, t10, ["text"])
        session.commit()

        assert result.is_current is True

    def test_only_latest_compression_is_current(self, session, story_id: UUID) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        svc = _make_service(session)

        svc.compress(story_id, t1, t10, ["t"] * 10)
        session.commit()
        svc.compress(story_id, t11, t20, ["t"] * 10)
        session.commit()

        history = svc.get_summary_history(story_id)
        assert history[0].is_current is False  # v1 no longer current
        assert history[1].is_current is True  # v2 is current

    def test_exactly_one_current_across_three_compressions(
        self, session, story_id: UUID
    ) -> None:
        turns = [_make_turn(session, story_id, label=f"t{i}") for i in range(6)]
        svc = _make_service(session)

        svc.compress(story_id, turns[0], turns[1], ["t", "t"])
        session.commit()
        svc.compress(story_id, turns[2], turns[3], ["t", "t"])
        session.commit()
        svc.compress(story_id, turns[4], turns[5], ["t", "t"])
        session.commit()

        history = svc.get_summary_history(story_id)
        current_rows = [r for r in history if r.is_current]
        assert len(current_rows) == 1
        assert current_rows[0].version_number == 3

    def test_db_partial_index_rejects_second_current_row(
        self, session, story_id: UUID
    ) -> None:
        """Verify the partial unique index catches a second is_current=True row."""
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        now = datetime.now(UTC).isoformat()
        sid = str(story_id)

        row1 = RollingSummaryORM(
            summary_id=str(uuid4()),
            story_id=sid,
            text="first",
            compressed_from_turn_id=str(t1),
            compressed_through_turn_id=str(t10),
            version_number=1,
            is_current=True,
            created_at=now,
        )
        row2 = RollingSummaryORM(
            summary_id=str(uuid4()),
            story_id=sid,
            text="second",
            compressed_from_turn_id=str(t11),
            compressed_through_turn_id=str(t20),
            version_number=2,
            is_current=True,  # second current row — must fail
            created_at=now,
        )
        session.add(row1)
        session.flush()

        session.add(row2)
        with pytest.raises(IntegrityError):
            session.flush()


# ===========================================================================
# Retrieval contract tests
# ===========================================================================


class TestRetrievalContract:
    def test_get_current_summary_returns_none_before_any_compression(
        self, session, story_id: UUID
    ) -> None:
        svc = _make_service(session)
        result = svc.get_current_summary(story_id)
        assert result is None

    def test_get_current_summary_returns_summary_after_compression(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session, _stub_generator("my summary"))

        svc.compress(story_id, t1, t10, ["text"])
        session.commit()

        result = svc.get_current_summary(story_id)
        assert result is not None
        assert result.text == "my summary"

    def test_get_current_summary_returns_most_recent(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        svc = _make_service(session, _stub_generator("v1"))

        svc.compress(story_id, t1, t10, ["t"] * 10)
        session.commit()
        svc._generator = _stub_generator("v2")
        svc.compress(story_id, t11, t20, ["t"] * 10)
        session.commit()

        result = svc.get_current_summary(story_id)
        assert result is not None
        assert result.text == "v2"
        assert result.version_number == 2

    def test_get_current_summary_ignores_non_current_rows(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        svc = _make_service(session)

        svc.compress(story_id, t1, t10, ["t"] * 10)
        session.commit()
        svc.compress(story_id, t11, t20, ["t"] * 10)
        session.commit()

        current = svc.get_current_summary(story_id)
        assert current is not None
        assert current.is_current is True
        assert current.version_number == 2  # v1 is non-current and ignored

    def test_get_current_summary_return_type_is_pydantic_model(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        svc.compress(story_id, t1, t10, ["text"])
        session.commit()

        result = svc.get_current_summary(story_id)
        assert isinstance(result, RollingSummary)
        assert not isinstance(result, RollingSummaryORM)

    def test_get_summary_history_returns_empty_before_any_compression(
        self, session, story_id: UUID
    ) -> None:
        svc = _make_service(session)
        history = svc.get_summary_history(story_id)
        assert history == []

    def test_get_summary_history_returns_all_in_creation_order(
        self, session, story_id: UUID
    ) -> None:
        turns = [_make_turn(session, story_id, label=f"t{i}") for i in range(6)]
        svc = _make_service(session, _stub_generator("text"))

        svc.compress(story_id, turns[0], turns[1], ["a"])
        session.commit()
        svc.compress(story_id, turns[2], turns[3], ["b"])
        session.commit()
        svc.compress(story_id, turns[4], turns[5], ["c"])
        session.commit()

        history = svc.get_summary_history(story_id)
        assert len(history) == 3
        assert all(isinstance(r, RollingSummary) for r in history)
        assert [r.version_number for r in history] == [1, 2, 3]

    def test_get_summary_history_return_type_is_list_of_pydantic(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session)

        svc.compress(story_id, t1, t10, ["text"])
        session.commit()

        history = svc.get_summary_history(story_id)
        assert isinstance(history, list)
        assert all(isinstance(r, RollingSummary) for r in history)


# ===========================================================================
# Generator dependency tests
# ===========================================================================


class TestGeneratorDependency:
    def test_generator_called_with_none_prior_on_first_compression(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        gen = _stub_generator("result")
        svc = _make_service(session, gen)

        svc.compress(story_id, t1, t10, ["text1", "text2"])
        session.commit()

        gen.assert_called_once_with(None, ["text1", "text2"])

    def test_generator_called_with_prior_summary_text(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        t11 = _make_turn(session, story_id, label="t11")
        t20 = _make_turn(session, story_id, label="t20")
        gen = _stub_generator("v1")
        svc = _make_service(session, gen)

        svc.compress(story_id, t1, t10, ["turn-texts-1"])
        session.commit()

        gen2 = _stub_generator("v2")
        svc._generator = gen2
        svc.compress(story_id, t11, t20, ["turn-texts-2"])
        session.commit()

        # Second call receives the v1 text as the prior summary.
        gen2.assert_called_once_with("v1", ["turn-texts-2"])

    def test_generator_not_called_on_idempotent_repeat(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        gen = _stub_generator("result")
        svc = _make_service(session, gen)

        svc.compress(story_id, t1, t10, ["text"])
        session.commit()
        svc.compress(story_id, t1, t10, ["text"])  # repeat — no call

        gen.assert_called_once()  # called only the first time

    def test_generator_return_value_persisted_as_summary_text(
        self, session, story_id: UUID
    ) -> None:
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        svc = _make_service(session, _stub_generator("persisted text"))

        result = svc.compress(story_id, t1, t10, ["text"])

        assert result.text == "persisted text"

    def test_no_real_network_call_in_tests(self, session, story_id: UUID) -> None:
        """The generator is a MagicMock — no real network call is made."""
        t1 = _make_turn(session, story_id, label="t1")
        t10 = _make_turn(session, story_id, label="t10")
        gen = MagicMock(return_value="mock result")
        svc = RollingSummaryService(session, gen)

        svc.compress(story_id, t1, t10, ["turn text"])

        # gen.assert_called_once() proves a real call was not made to any
        # external service — the injected callable received the invocation.
        gen.assert_called_once()


# ===========================================================================
# Multi-story isolation
# ===========================================================================


class TestMultiStoryIsolation:
    def test_summaries_isolated_between_stories(self, session) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        story_a = Story(title="A", mode=StoryMode.RPG, created_at=now, updated_at=now)
        story_b = Story(title="B", mode=StoryMode.RPG, created_at=now, updated_at=now)
        create_story(session, story_a)
        create_story(session, story_b)
        session.commit()

        ta1 = _make_turn(session, story_a.story_id, label="a1")
        ta10 = _make_turn(session, story_a.story_id, label="a10")
        tb1 = _make_turn(session, story_b.story_id, label="b1")
        tb10 = _make_turn(session, story_b.story_id, label="b10")

        svc = _make_service(session, _stub_generator("story-A-summary"))
        svc.compress(story_a.story_id, ta1, ta10, ["a"] * 10)
        session.commit()

        svc._generator = _stub_generator("story-B-summary")
        svc.compress(story_b.story_id, tb1, tb10, ["b"] * 10)
        session.commit()

        current_a = svc.get_current_summary(story_a.story_id)
        current_b = svc.get_current_summary(story_b.story_id)

        assert current_a is not None
        assert current_a.text == "story-A-summary"
        assert current_b is not None
        assert current_b.text == "story-B-summary"

        assert svc.get_summary_history(story_a.story_id) == [current_a]
        assert svc.get_summary_history(story_b.story_id) == [current_b]
