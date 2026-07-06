"""DB-level tests for the Retrieval Memory RPG turn-marker sidecar.

CRD Issue 18 / ADR-018 D6. Covers the marker table, the era-boundary
singleton, and the full DB-integrated eligibility gather path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.enums import (
    IntentType,
    RollVisibility,
    RpgTurnRetrievalCategory,
    StoryMode,
)
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.node import create_turn
from afterworlds.persistence.crud.retrieval import (
    create_rpg_turn_retrieval_marker,
    get_era_boundary_timestamp,
    get_rpg_turn_retrieval_marker,
    has_pending_roll_request_originating_from_turn,
    is_post_boundary,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.retrieval import RetrievalMarkerEraBoundaryORM
from afterworlds.persistence.orm.rpg import PendingRollRequestORM
from afterworlds.pipeline.retrieval.eligibility import gather_turn_eligibility_for_turn
from tests.persistence.conftest import make_story

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _seed_pending_roll_request(
    session, story_id, originating_turn_id  # type: ignore[no-untyped-def]
) -> None:
    """Persist a minimal PendingRollRequest row whose originating_turn_id is
    *originating_turn_id* — exercises the FK to rpg_character_sheet_bases
    that the announce path (orchestrator) also writes against."""
    sheet = RpgCharacterSheetBase(
        story_id=story_id,
        rules_package_id="dnd5e-v1",
        character_name="Test Character",
        created_at=_NOW,
        updated_at=_NOW,
    )
    create_rpg_base_sheet(session, sheet)
    session.add(
        PendingRollRequestORM(
            request_id=str(uuid4()),
            story_id=str(story_id),
            session_id=str(uuid4()),
            character_id=str(sheet.sheet_id),
            originating_turn_id=str(originating_turn_id),
            check_label="Stealth Check",
            player_facing_instruction="Roll a Stealth Check and report the total!",
            expected_value_shape="d20",
            visibility=RollVisibility.PLAYER.value,
            source_proposal_ref="roll_0",
            status="pending",
            created_at=_NOW.isoformat(),
            schema_version=1,
            roll_expression="1d20+5",
        )
    )
    session.commit()


@pytest.fixture()
def session_factory(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


def _make_turn(**kwargs: object) -> Turn:
    defaults: dict[str, object] = {
        "user_input": "swing my sword",
        "assistant_output": "The blade connects with a satisfying thud.",
        "timestamp": _NOW,
        "intent_classification": IntentType.IN_CHARACTER_ACTION,
        "node_id": None,
    }
    defaults.update(kwargs)
    return Turn(**defaults)  # type: ignore[arg-type]


class TestMarkerRoundTrip:
    def test_create_and_read(self, session) -> None:  # type: ignore[no-untyped-def]
        story = make_story()
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn()
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()

        create_rpg_turn_retrieval_marker(
            session,
            turn_id=turn.turn_id,
            story_id=story.story_id,
            category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
            created_at=_NOW.isoformat(),
        )
        session.commit()

        result = get_rpg_turn_retrieval_marker(session, turn.turn_id)
        assert result is RpgTurnRetrievalCategory.ORDINARY_NARRATIVE

    def test_missing_marker_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        assert get_rpg_turn_retrieval_marker(session, uuid4()) is None

    def test_duplicate_marker_raises(self, session) -> None:  # type: ignore[no-untyped-def]
        story = make_story()
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn()
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()

        create_rpg_turn_retrieval_marker(
            session,
            turn_id=turn.turn_id,
            story_id=story.story_id,
            category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
            created_at=_NOW.isoformat(),
        )
        session.commit()

        with pytest.raises(IntegrityError):
            create_rpg_turn_retrieval_marker(
                session,
                turn_id=turn.turn_id,
                story_id=story.story_id,
                category=RpgTurnRetrievalCategory.ROLL_REQUEST,
                created_at=_NOW.isoformat(),
            )


class TestEraBoundary:
    def test_no_boundary_row_returns_none(self, session) -> None:  # type: ignore[no-untyped-def]
        assert get_era_boundary_timestamp(session) is None

    def test_none_boundary_means_every_turn_is_post_boundary(self) -> None:
        assert is_post_boundary("2020-01-01T00:00:00+00:00", None) is True

    def test_timestamp_after_boundary_is_post_boundary(self) -> None:
        boundary = "2026-01-01T00:00:00+00:00"
        assert is_post_boundary("2026-06-01T00:00:00+00:00", boundary) is True

    def test_timestamp_at_boundary_is_not_post_boundary(self) -> None:
        boundary = "2026-01-01T00:00:00+00:00"
        assert is_post_boundary(boundary, boundary) is False

    def test_timestamp_before_boundary_is_not_post_boundary(self) -> None:
        boundary = "2026-06-01T00:00:00+00:00"
        assert is_post_boundary("2026-01-01T00:00:00+00:00", boundary) is False

    def test_get_era_boundary_reads_persisted_row(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        session.add(
            RetrievalMarkerEraBoundaryORM(
                id=1, boundary_timestamp="2026-01-01T00:00:00+00:00"
            )
        )
        session.commit()
        assert get_era_boundary_timestamp(session) == "2026-01-01T00:00:00+00:00"


class TestHasPendingRollRequestOriginatingFromTurn:
    def test_returns_true_when_row_exists(self, session) -> None:  # type: ignore[no-untyped-def]
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn()
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()
        _seed_pending_roll_request(session, story.story_id, turn.turn_id)

        assert has_pending_roll_request_originating_from_turn(session, turn.turn_id)

    def test_returns_false_when_no_row_exists(self, session) -> None:  # type: ignore[no-untyped-def]
        assert not has_pending_roll_request_originating_from_turn(session, uuid4())


class TestGatherEligibilityDbIntegrated:
    def test_post_boundary_markerless_rpg_turn_is_data_integrity_error(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        session.add(
            RetrievalMarkerEraBoundaryORM(
                id=1, boundary_timestamp="2020-01-01T00:00:00+00:00"
            )
        )
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn(timestamp=_NOW)  # 2026, after the 2020 boundary
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()

        decision = gather_turn_eligibility_for_turn(session, turn, StoryMode.RPG)
        assert decision.eligible is False
        assert decision.data_integrity_error is True

    def test_pre_boundary_markerless_rpg_turn_is_eligible(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        session.add(
            RetrievalMarkerEraBoundaryORM(
                id=1, boundary_timestamp="2030-01-01T00:00:00+00:00"
            )
        )
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn(timestamp=_NOW)  # 2026, before the 2030 boundary
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()

        decision = gather_turn_eligibility_for_turn(session, turn, StoryMode.RPG)
        assert decision.eligible is True
        assert decision.data_integrity_error is False

    def test_pre_boundary_markerless_rpg_turn_with_pending_roll_is_excluded(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        """Codex #119 P1: a legacy pre-marker roll-request turn predates the
        marker sidecar entirely (no marker row) but must still be excluded
        via PendingRollRequest.originating_turn_id — ADR-018 D6's
        era-boundary table, "Before persisted boundary, roll-request" row."""
        session.add(
            RetrievalMarkerEraBoundaryORM(
                id=1, boundary_timestamp="2030-01-01T00:00:00+00:00"
            )
        )
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn(timestamp=_NOW)  # 2026, before the 2030 boundary
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()
        _seed_pending_roll_request(session, story.story_id, turn.turn_id)

        decision = gather_turn_eligibility_for_turn(session, turn, StoryMode.RPG)
        assert decision.eligible is False
        assert decision.data_integrity_error is False

    def test_post_boundary_roll_request_marker_and_pending_roll_agree_is_excluded(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        """Coverage-invariant consistency (ADR-018 D6): for a post-boundary
        turn, a ROLL_REQUEST marker and a PendingRollRequest row must never
        disagree, and PendingRollRequest is what the predicate actually
        checks — proven here against a real DB row, not just the pure
        predicate's has_pending_roll_request=True flag."""
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn()
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()
        create_rpg_turn_retrieval_marker(
            session,
            turn_id=turn.turn_id,
            story_id=story.story_id,
            category=RpgTurnRetrievalCategory.ROLL_REQUEST,
            created_at=_NOW.isoformat(),
        )
        session.commit()
        _seed_pending_roll_request(session, story.story_id, turn.turn_id)

        decision = gather_turn_eligibility_for_turn(session, turn, StoryMode.RPG)
        assert decision.eligible is False
        assert decision.data_integrity_error is False

    def test_rpg_turn_with_ordinary_narrative_marker_is_eligible(
        self, session
    ) -> None:  # type: ignore[no-untyped-def]
        story = make_story(mode=StoryMode.RPG)
        create_story(session, story)  # type: ignore[arg-type]
        turn = _make_turn()
        create_turn(session, turn)  # type: ignore[arg-type]
        session.commit()
        create_rpg_turn_retrieval_marker(
            session,
            turn_id=turn.turn_id,
            story_id=story.story_id,
            category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
            created_at=_NOW.isoformat(),
        )
        session.commit()

        decision = gather_turn_eligibility_for_turn(session, turn, StoryMode.RPG)
        assert decision.eligible is True
