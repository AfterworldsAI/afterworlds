"""CRD Issue 2b: the RPG turn lease and commit recheck at the orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.orm.dnd5e_state import RpgTurnLeaseORM
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.services.dnd5e_state import store
from afterworlds.services.dnd5e_state.turn import RpgTurnHold, TurnCharacter
from tests.pipeline.orchestrator.test_service import (
    _SOJOURNER,
    _make_orchestrator_with_adjudication,
    _make_rpg_session_and_sheet,
)
from tests.rpg_characters import BINDING, turn_character


def _leases(session_factory: Any, story_id: UUID) -> int:
    with session_factory() as s:
        return int(
            s.execute(
                sa.select(sa.func.count())
                .select_from(RpgTurnLeaseORM)
                .where(RpgTurnLeaseORM.story_id == str(story_id))
            ).scalar_one()
        )


def _persisted(session_factory: Any, story_id: UUID) -> store.StoredCharacter:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    template = turn_character(story_id=story_id)
    with session_factory() as s:
        create_rpg_base_sheet(
            s,
            RpgCharacterSheetBase(
                sheet_id=template.sheet_id,
                story_id=story_id,
                character_name="Aldric",
                created_at=now,
                updated_at=now,
            ),
        )
        stored = store.create_character_state(
            s, template.sheet_id, template.stored.state, BINDING, now="t"
        )
        s.commit()
    return stored


def _hold(session_factory: Any) -> RpgTurnHold:
    return RpgTurnHold(session_factory, lambda: datetime.now(UTC).isoformat())


def test_an_rpg_turn_holds_a_durable_lease_while_it_runs(
    session_factory: Any, seeded_story: tuple[UUID, UUID]
) -> None:
    story_id, node_id = seeded_story
    orch = _make_orchestrator_with_adjudication(session_factory)
    orch._rpg_turn_hold = _hold(session_factory)  # type: ignore[attr-defined]
    seen: list[int] = []
    session_state, _ = _make_rpg_session_and_sheet()
    sheet = TurnCharacter(_persisted(session_factory, story_id), ())

    def resolver(sid: UUID) -> tuple[object, object]:
        seen.append(_leases(session_factory, sid))
        return session_state, sheet

    orch._rpg_session_sheet_resolver = resolver  # type: ignore[attr-defined]
    result = orch.orchestrate_turn(
        story_id, node_id, "I attack.", _SOJOURNER, RuntimeAccessPath.HOSTED
    )
    assert result.disposition is PipelineDisposition.DELIVERED
    assert seen and all(n == 1 for n in seen)  # committed before any binding read
    assert _leases(session_factory, story_id) == 0  # released after the turn


def test_a_turn_whose_lease_cannot_be_taken_fails_typed_before_any_work(
    session_factory: Any, seeded_story: tuple[UUID, UUID]
) -> None:
    story_id, node_id = seeded_story
    orch = _make_orchestrator_with_adjudication(session_factory)

    class Broken:
        def acquire(self, _story_id: UUID) -> str:
            raise RuntimeError("database is locked")

    called: list[UUID] = []
    orch._rpg_turn_hold = Broken()  # type: ignore[attr-defined]
    orch._rpg_session_sheet_resolver = lambda sid: called.append(sid)  # type: ignore[attr-defined]
    result = orch.orchestrate_turn(
        story_id, node_id, "I attack.", _SOJOURNER, RuntimeAccessPath.HOSTED
    )
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert result.pipeline_error_summary is not None
    assert "lease" in result.pipeline_error_summary
    assert called == []


def test_work_computed_against_a_character_that_changed_mid_turn_cannot_commit(
    session_factory: Any, seeded_story: tuple[UUID, UUID]
) -> None:
    story_id, node_id = seeded_story
    stored = _persisted(session_factory, story_id)
    session_state, _ = _make_rpg_session_and_sheet()
    orch = _make_orchestrator_with_adjudication(session_factory)
    orch._rpg_turn_hold = _hold(session_factory)  # type: ignore[attr-defined]

    def resolver(_sid: UUID) -> tuple[object, object]:
        read = TurnCharacter(stored, ())
        # A concurrent writer lands after the turn read the character.
        with session_factory() as s:
            store.save_state(
                s,
                "character",
                stored.sheet_id,
                stored.state,
                expected_revision=stored.revision,
                expected_binding=stored.binding,
                now="t",
            )
            s.commit()
        return session_state, read

    orch._rpg_session_sheet_resolver = resolver  # type: ignore[attr-defined]
    result = orch.orchestrate_turn(
        story_id, node_id, "I attack.", _SOJOURNER, RuntimeAccessPath.HOSTED
    )
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert result.pipeline_error_summary is not None
    assert "changed during the turn" in result.pipeline_error_summary
    assert _leases(session_factory, story_id) == 0


def test_an_in_play_character_that_is_not_ready_fails_the_turn_typed(
    session_factory: Any, seeded_story: tuple[UUID, UUID]
) -> None:
    """Mechanics are never skipped silently: missing state names itself."""
    story_id, node_id = seeded_story
    orch = _make_orchestrator_with_adjudication(session_factory, adjudicable=False)
    session_state, _ = _make_rpg_session_and_sheet()
    sheet = turn_character(story_id=story_id, ready=False)
    orch._rpg_session_sheet_resolver = lambda _sid: (session_state, sheet)  # type: ignore[attr-defined]
    result = orch.orchestrate_turn(
        story_id, node_id, "I attack.", _SOJOURNER, RuntimeAccessPath.HOSTED
    )
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert result.pipeline_error_summary is not None
    assert "not ready" in result.pipeline_error_summary
    assert "missing_state at feats" in result.pipeline_error_summary
