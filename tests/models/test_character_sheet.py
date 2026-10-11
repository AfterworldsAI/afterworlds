"""Unit tests for the RPG character identity model.

The character's mechanical state is the CRD Issue 2b typed state
(``tests/services/dnd5e_state``). What stays here: the identity row is a
distinct typed model, carries no rule-adjudication semantics or HP/ability
fields, and no longer carries a free-text Rules Package reference — the exact
binding lives on the typed state. ``Dnd5eAbilityScores`` keeps ADR-0003's D&D
5e-scoped 1–30 range.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.dnd5e_state import Dnd5eAbilityScores


def _base(**overrides: object) -> RpgCharacterSheetBase:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "story_id": uuid4(),
        "character_name": "Elowen",
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return RpgCharacterSheetBase(**values)  # type: ignore[arg-type]


def test_identity_instantiates_and_mints_distinct_ids() -> None:
    assert _base().character_name == "Elowen"
    assert _base().sheet_id != _base().sheet_id


def test_identity_carries_no_mechanics_and_no_package_reference() -> None:
    fields = set(RpgCharacterSheetBase.model_fields)
    assert fields == {
        "sheet_id",
        "story_id",
        "character_name",
        "created_at",
        "updated_at",
    }


@pytest.mark.parametrize("value", [0, 31])
def test_dnd5e_ability_scores_keep_the_dnd5e_range(value: int) -> None:
    scores = dict(
        strength=10,
        dexterity=12,
        constitution=14,
        intelligence=8,
        wisdom=13,
        charisma=11,
    )
    with pytest.raises(ValidationError):
        Dnd5eAbilityScores(**{**scores, "strength": value})
    assert Dnd5eAbilityScores(**{**scores, "strength": 30}).strength == 30
