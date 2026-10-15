"""Unit tests for D20RulesSystemAdapter — CRD Issues 15, 15c and 15b.

The legacy total-only announce/consume methods and their label-based
assembler are retired (CRD Issue 15b, 15b-25); their validation successors
are in ``test_roll_engine.py`` and the action-resolution sequence tests.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import ResolvedAdjudicationRecord, RollProposal
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCharacter
from tests.rpg_characters import turn_character

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_sheet(*, dex: int = 16, wis: int = 13) -> TurnCharacter:
    return turn_character(dex=dex, wis=wis)


def _make_record(
    check_label: str = "Perception check",
    visibility: RollVisibility = RollVisibility.SHOWN,
    total: int = 14,
    dc: int | None = 12,
    outcome: str = "success",
) -> ResolvedAdjudicationRecord:
    return ResolvedAdjudicationRecord(
        check_label=check_label,
        visibility=visibility,
        expression="1d20+2",
        raw_rolls=(12,),
        modifiers_json=json.dumps({"perception": 2}),
        total=total,
        dc=dc,
        outcome=outcome,
        sheet_effects=(),
        source="ai",
        gm_cheating_at_roll=True,
    )


# ---------------------------------------------------------------------------
# HIDDEN roll — Fix 3 (ADR-015 Decision 5)
# ---------------------------------------------------------------------------


def test_hidden_roll_check_label_scrubbed() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(check_label="Stealth check", visibility=RollVisibility.HIDDEN)
    view = adapter.to_writer_view(record)
    assert view.check_label == ""
    assert "Stealth" not in view.check_label
    assert "stealth" not in view.check_label.lower()


def test_hidden_roll_player_facing_summary_does_not_leak_label() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(
        check_label="Perception check", visibility=RollVisibility.HIDDEN
    )
    view = adapter.to_writer_view(record)
    assert "Perception" not in view.player_facing_summary
    assert "perception" not in view.player_facing_summary.lower()
    assert "hidden" not in view.player_facing_summary.lower()


def test_hidden_roll_mechanical_fields_are_none() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(visibility=RollVisibility.HIDDEN, total=19, dc=12)
    view = adapter.to_writer_view(record)
    assert view.total is None
    assert view.dc is None
    assert view.outcome is None


def test_hidden_roll_serialized_ledger_does_not_leak_skill() -> None:
    """The full JSON serialization (as it reaches the Writer ledger) must not
    contain the original check_label string.  The visibility enum value
    'hidden' is permitted as a structural field."""
    adapter = D20RulesSystemAdapter()
    record = _make_record(check_label="Arcana check", visibility=RollVisibility.HIDDEN)
    view = adapter.to_writer_view(record)
    serialized = view.model_dump_json()
    # The skill name must not appear anywhere
    assert "Arcana" not in serialized
    assert "arcana" not in serialized.lower()
    # The player_facing_summary must not contain mechanical labels
    assert "hidden" not in view.player_facing_summary.lower()
    assert "check" not in view.player_facing_summary.lower()


# ---------------------------------------------------------------------------
# SHOWN roll — ensure normal path is unaffected
# ---------------------------------------------------------------------------


def test_a_shown_roll_takes_a_code_derived_public_label() -> None:
    """The GameMaster's check_label is backend-only (CRD Issue 15c)."""
    adapter = D20RulesSystemAdapter()
    record = _make_record(
        check_label="Athletics check", visibility=RollVisibility.SHOWN
    ).model_copy(
        update={
            "modifiers_json": json.dumps(
                {
                    "operation": "difficulty_check",
                    "ability": "strength",
                    "skill": "athletics",
                }
            )
        }
    )
    view = adapter.to_writer_view(record)
    assert view.check_label == "Strength (Athletics) check"
    assert view.total == 14
    assert view.dc == 12
    assert view.outcome == "success"


def test_player_roll_keeps_its_numbers_under_a_public_label() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(
        check_label="Persuasion check",
        visibility=RollVisibility.PLAYER,
        total=18,
        dc=15,
        outcome="success",
    )
    view = adapter.to_writer_view(record)
    assert view.check_label == "Check"
    assert view.total == 18
    assert view.dc == 15
    assert view.outcome == "success"
    assert "18" in view.player_facing_summary


def test_a_secret_in_the_gamemasters_label_never_reaches_the_writer() -> None:
    """The GameMaster saw a hidden condition in the scene and wrote it into
    a shown roll's label; the Writer view carries none of it."""
    adapter = D20RulesSystemAdapter()
    secret = "Strike the secretly Poisoned wolf (instance c-poisoned)"
    for operation, extra in (
        ("weapon_attack", {"weapon": "equipment.weapons.club"}),
        ("creature_attack", {"entry": "Bite"}),
        ("begin_turn", {}),
    ):
        record = _make_record(check_label=secret).model_copy(
            update={"modifiers_json": json.dumps({"operation": operation, **extra})}
        )
        view = adapter.to_writer_view(record)
        public = f"{view.check_label} {view.player_facing_summary}"
        assert "Poisoned" not in public and "c-poisoned" not in public, public


# ---------------------------------------------------------------------------
# CRD Issue 15c: backend rolls need a roster operation; labels never suffice
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tag", "check", "label"),
    [
        ("saving_throw", "Dexterity Saving Throw", "dexterity"),
        ("weapon_attack", "Longsword Attack", "dexterity"),
        ("skill_check", "Stealth Check", "dexterity"),
        ("ability_check", "Dexterity Check", "dexterity"),
        ("ability_check advantage", "Dexterity Check", "dexterity"),
        ("", "Dexterity Check", None),
    ],
)
@pytest.mark.parametrize("visibility", list(RollVisibility))
def test_a_label_only_proposal_is_refused_not_rolled(
    tag: str, check: str, label: str | None, visibility: RollVisibility
) -> None:
    """Labels and tags are display text: without a roster operation nothing
    rolls, whoever would roll it (CRD Issue 15c AC3; 15b)."""
    adapter = D20RulesSystemAdapter()
    proposal = RollProposal(
        check_label=check,
        subsystem_tag=tag,
        skill_or_attribute_label=label,
        visibility=visibility,
    )
    dice_svc = MagicMock()
    for call in (
        lambda: adapter.require_supported(proposal, _make_sheet()),
        lambda: adapter.resolve_roll(proposal, _make_sheet(), None, dice_svc, False),
    ):
        with pytest.raises(AdjudicationRefusal) as caught:
            call()
        assert caught.value.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    dice_svc.roll.assert_not_called()


def test_readiness_is_the_adjudicable_gate() -> None:
    adapter = D20RulesSystemAdapter()
    assert adapter.is_adjudicable(turn_character())
    assert not adapter.is_adjudicable(turn_character(ready=False))
