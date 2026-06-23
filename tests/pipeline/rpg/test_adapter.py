"""Unit tests for D20RulesSystemAdapter — CRD Issue 15 remediation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
)
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter, PlayerRollValueError

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_sheet(
    *,
    skills: dict[str, int] | None = None,
    level: int = 5,
    dex: int = 16,
) -> Dnd5eCharacterSheet:
    return Dnd5eCharacterSheet(
        story_id=uuid4(),
        rules_package_id="dnd5e-v1",
        character_name="Test Hero",
        created_at=_NOW,
        updated_at=_NOW,
        character_class="rogue",
        background="criminal",
        level=level,
        ability_scores=Dnd5eAbilityScores(
            strength=10,
            dexterity=dex,
            constitution=14,
            intelligence=12,
            wisdom=13,
            charisma=10,
        ),
        skills=skills or {},
        current_hp=30,
        maximum_hp=30,
    )


def _make_proposal(
    label: str | None = "stealth",
    visibility: RollVisibility = RollVisibility.SHOWN,
    subsystem_tag: str = "skill_check",
) -> RollProposal:
    return RollProposal(
        check_label=f"{label or 'unknown'} check",
        subsystem_tag=subsystem_tag,
        skill_or_attribute_label=label,
        visibility=visibility,
    )


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


def test_shown_roll_preserves_check_label() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(
        check_label="Athletics check", visibility=RollVisibility.SHOWN
    )
    view = adapter.to_writer_view(record)
    assert view.check_label == "Athletics check"
    assert view.total == 14
    assert view.dc == 12
    assert view.outcome == "success"


def test_player_roll_preserves_all_fields() -> None:
    adapter = D20RulesSystemAdapter()
    record = _make_record(
        check_label="Persuasion check",
        visibility=RollVisibility.PLAYER,
        total=18,
        dc=15,
        outcome="success",
    )
    view = adapter.to_writer_view(record)
    assert view.check_label == "Persuasion check"
    assert view.total == 18
    assert view.dc == 15
    assert view.outcome == "success"
    assert "18" in view.player_facing_summary


# ---------------------------------------------------------------------------
# Trust boundary: _verify_dc always returns None (Fix 2)
# ---------------------------------------------------------------------------


def test_verify_dc_returns_none_regardless_of_subsystem_tag() -> None:
    """_verify_dc must never parse a DC from model-authored subsystem_tag."""
    adapter = D20RulesSystemAdapter()
    assert adapter._verify_dc(None, []) is None  # noqa: SLF001


def test_verify_dc_returns_none_for_dc_tag() -> None:
    """Even a subsystem_tag like 'skill_check dc 15' must return None."""
    adapter = D20RulesSystemAdapter()
    assert adapter._verify_dc(None, []) is None  # noqa: SLF001


def test_verify_dc_outcome_is_undetermined_when_dc_absent() -> None:
    """When _verify_dc returns None, resolve_roll produces outcome='undetermined'."""
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 7})
    proposal = _make_proposal(
        "stealth", RollVisibility.SHOWN, subsystem_tag="skill_check dc 5"
    )
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=12, raw_rolls=(12,))
    record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
    assert record.dc is None
    assert record.outcome == "undetermined"


# ---------------------------------------------------------------------------
# Skill modifier: uses stored computed modifier (Fix 1)
# ---------------------------------------------------------------------------


def test_skill_in_sheet_uses_stored_modifier() -> None:
    """stealth: 7, Dex +3, level 5 — adapter must use stored +7, not recomputed +6."""
    adapter = D20RulesSystemAdapter()
    # Dex 16 → raw modifier +3; proficiency at level 5 = +3 → recomputed would be +6.
    # The sheet stores +7 (e.g. from Expertise), so the adapter must use +7.
    sheet = _make_sheet(skills={"stealth": 7}, level=5, dex=16)
    proposal = _make_proposal("stealth", RollVisibility.SHOWN)
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
    record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
    # total = 10 (die) + 7 (stored modifier) = 17
    assert record.total == 17
    breakdown = json.loads(record.modifiers_json)
    assert breakdown["breakdown"]["stealth_modifier"] == 7


def test_skill_not_in_sheet_falls_back_to_ability_mod() -> None:
    """When a skill is missing from sheet.skills, fall back to governing ability mod."""
    adapter = D20RulesSystemAdapter()
    # Dex 16 → +3; stealth not in skills dict
    sheet = _make_sheet(skills={}, dex=16)
    proposal = _make_proposal("stealth", RollVisibility.SHOWN)
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
    record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
    # total = 10 + 3 (Dex mod) = 13
    assert record.total == 13
    breakdown = json.loads(record.modifiers_json)
    assert breakdown["breakdown"]["dexterity_modifier"] == 3


def test_skill_modifier_differs_from_recomputed_value() -> None:
    """Stored modifier 9 is used verbatim even when ability+prof differs."""
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 9}, level=5, dex=16)
    proposal = _make_proposal("stealth", RollVisibility.SHOWN)
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=5, raw_rolls=(5,))
    record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
    assert record.total == 14  # 5 + 9


# ---------------------------------------------------------------------------
# Advantage/disadvantage parsing: word-boundary fix (Round 5 Fix 1)
# ---------------------------------------------------------------------------


def _make_adv_proposal(subsystem_tag: str) -> RollProposal:
    return RollProposal(
        check_label="Stealth check",
        subsystem_tag=subsystem_tag,
        skill_or_attribute_label="stealth",
        visibility=RollVisibility.SHOWN,
    )


def test_advantage_tag_selects_2d20kh1() -> None:
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 3})
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=15, raw_rolls=(15, 10))
    adapter.resolve_roll(
        _make_adv_proposal("skill_check advantage"), sheet, None, [], dice_svc, False
    )
    dice_svc.roll.assert_called_once_with("2d20kh1")


def test_disadvantage_tag_selects_2d20kl1() -> None:
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 3})
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=8, raw_rolls=(8, 15))
    adapter.resolve_roll(
        _make_adv_proposal("skill_check disadvantage"), sheet, None, [], dice_svc, False
    )
    dice_svc.roll.assert_called_once_with("2d20kl1")


def test_disadvantage_containing_advantage_substring_selects_2d20kl1() -> None:
    """'saving_throw disadvantage' must not trigger advantage (substring trap)."""
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet()
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=5, raw_rolls=(5, 12))
    adapter.resolve_roll(
        _make_adv_proposal("saving_throw disadvantage"),
        sheet,
        None,
        [],
        dice_svc,
        False,
    )
    dice_svc.roll.assert_called_once_with("2d20kl1")


def test_plain_tag_selects_1d20() -> None:
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 3})
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=12, raw_rolls=(12,))
    adapter.resolve_roll(
        _make_adv_proposal("skill_check"), sheet, None, [], dice_svc, False
    )
    dice_svc.roll.assert_called_once_with("1d20")


def test_both_advantage_and_disadvantage_cancel_to_1d20() -> None:
    adapter = D20RulesSystemAdapter()
    sheet = _make_sheet(skills={"stealth": 3})
    dice_svc = MagicMock()
    dice_svc.roll.return_value = MagicMock(chosen=12, raw_rolls=(12,))
    adapter.resolve_roll(
        _make_adv_proposal("skill_check advantage disadvantage"),
        sheet,
        None,
        [],
        dice_svc,
        False,
    )
    dice_svc.roll.assert_called_once_with("1d20")


# ---------------------------------------------------------------------------
# consume_player_roll validation: raw die range check (Round 5 Fix 2)
# ---------------------------------------------------------------------------


def _make_pending(
    *,
    expression: str = "1d20",
    visible_mod: int | None = None,
) -> PendingRollRequest:
    return PendingRollRequest(
        request_id=uuid4(),
        story_id=uuid4(),
        session_id=uuid4(),
        character_id=uuid4(),
        check_label="Stealth check",
        player_facing_instruction=f"Roll {expression}",
        expected_value_shape="integer",
        visible_modifier_note=f"+{visible_mod}" if visible_mod else None,
        visibility=RollVisibility.PLAYER,
        source_proposal_ref="skill_check/Stealth check",
        originating_turn_id=uuid4(),
        created_at=_NOW,
        roll_expression=expression,
        visible_modifier_total=visible_mod,
        visible_modifier_breakdown_json=None,
    )


def test_consume_valid_total_accepted() -> None:
    """reported_total=15 with no modifier → raw_die=15 which is in [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending()
    record = adapter.consume_player_roll(pending, 15, None, [], False)
    assert record.total == 15
    assert record.raw_rolls == (15,)


def test_consume_min_die_accepted() -> None:
    adapter = D20RulesSystemAdapter()
    pending = _make_pending()
    record = adapter.consume_player_roll(pending, 1, None, [], False)
    assert record.raw_rolls == (1,)


def test_consume_max_die_accepted() -> None:
    adapter = D20RulesSystemAdapter()
    pending = _make_pending()
    record = adapter.consume_player_roll(pending, 20, None, [], False)
    assert record.raw_rolls == (20,)


def test_consume_total_zero_raw_die_rejected() -> None:
    """reported_total=0 → raw_die=0, outside [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending()
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 0, None, [], False)


def test_consume_total_implies_raw_die_above_max_rejected() -> None:
    """reported_total=21 with no modifier → raw_die=21, outside [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending()
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 21, None, [], False)


def test_consume_with_modifier_valid() -> None:
    """reported_total=18, visible_mod=5 → raw_die=13, in [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(visible_mod=5)
    record = adapter.consume_player_roll(pending, 18, None, [], False)
    assert record.raw_rolls == (13,)


def test_consume_with_modifier_raw_die_too_low_rejected() -> None:
    """reported_total=5, visible_mod=7 → raw_die=-2, outside [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(visible_mod=7)
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 5, None, [], False)


def test_consume_advantage_expression_accepted() -> None:
    """2d20kh1 total=17, mod=0 → raw_die=17, in [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kh1")
    record = adapter.consume_player_roll(pending, 17, None, [], False)
    assert record.raw_rolls == (17,)


def test_consume_disadvantage_expression_accepted() -> None:
    """2d20kl1 total=4, mod=0 → raw_die=4, in [1,20]."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kl1")
    record = adapter.consume_player_roll(pending, 4, None, [], False)
    assert record.raw_rolls == (4,)


def test_consume_unsupported_expression_rejected() -> None:
    """Unsupported multi-die-sum expression must fail-closed."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="3d6")
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 10, None, [], False)


# ---------------------------------------------------------------------------
# consume_player_roll boundary cases with visible modifier (Round 6 spec)
# ---------------------------------------------------------------------------


def test_consume_1d20_mod5_max_boundary_accepted() -> None:
    """1d20 + mod=5, total=25 → raw=20, accepted (exact max)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="1d20", visible_mod=5)
    record = adapter.consume_player_roll(pending, 25, None, [], False)
    assert record.raw_rolls == (20,)


def test_consume_1d20_mod5_min_boundary_accepted() -> None:
    """1d20 + mod=5, total=6 → raw=1, accepted (exact min)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="1d20", visible_mod=5)
    record = adapter.consume_player_roll(pending, 6, None, [], False)
    assert record.raw_rolls == (1,)


def test_consume_1d20_mod5_one_over_max_rejected() -> None:
    """1d20 + mod=5, total=26 → raw=21, rejected (one over max)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="1d20", visible_mod=5)
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 26, None, [], False)


def test_consume_1d20_mod5_one_under_min_rejected() -> None:
    """1d20 + mod=5, total=5 → raw=0, rejected (one under min)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="1d20", visible_mod=5)
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 5, None, [], False)


def test_consume_kh1_mod5_max_boundary_accepted() -> None:
    """2d20kh1 + mod=5, total=25 → raw=20, accepted (exact max)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kh1", visible_mod=5)
    record = adapter.consume_player_roll(pending, 25, None, [], False)
    assert record.raw_rolls == (20,)


def test_consume_kh1_mod5_one_over_max_rejected() -> None:
    """2d20kh1 + mod=5, total=26 → raw=21, rejected (one over max)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kh1", visible_mod=5)
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 26, None, [], False)


def test_consume_kl1_mod5_min_boundary_accepted() -> None:
    """2d20kl1 + mod=5, total=6 → raw=1, accepted (exact min)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kl1", visible_mod=5)
    record = adapter.consume_player_roll(pending, 6, None, [], False)
    assert record.raw_rolls == (1,)


def test_consume_kl1_mod5_one_under_min_rejected() -> None:
    """2d20kl1 + mod=5, total=5 → raw=0, rejected (one under min)."""
    adapter = D20RulesSystemAdapter()
    pending = _make_pending(expression="2d20kl1", visible_mod=5)
    with pytest.raises(PlayerRollValueError):
        adapter.consume_player_roll(pending, 5, None, [], False)


# ---------------------------------------------------------------------------
# Skill key normalization: display-case and whitespace tolerance (Round 13)
# ---------------------------------------------------------------------------


class TestSkillKeyNormalization:
    """Skill-key normalization: display-case/whitespace sheet keys resolve correctly."""

    def test_display_case_single_word_key_uses_stored_modifier(self) -> None:
        """sheet.skills={'Stealth': 7}: display-case key finds stored +7, not Dex +3."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"Stealth": 7}, dex=16)
        proposal = _make_proposal("stealth", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 17  # 10 + 7; pre-fix would be 10 + 3 = 13
        data = json.loads(record.modifiers_json)
        assert data["breakdown"]["stealth_modifier"] == 7

    def test_multiword_sleight_of_hand_display_case(self) -> None:
        """{'Sleight of Hand': 6}: multiword display key finds stored +6, not Dex +3."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"Sleight of Hand": 6}, dex=16)
        proposal = _make_proposal("Sleight of Hand", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 16  # 10 + 6; pre-fix would be 10 + 3 = 13
        data = json.loads(record.modifiers_json)
        assert data["breakdown"]["sleight_of_hand_modifier"] == 6

    def test_multiword_animal_handling_display_case(self) -> None:
        """{'Animal Handling': 5}: multiword display key finds stored +5, not Wis +1."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"Animal Handling": 5})  # wis=13 default → mod +1
        proposal = _make_proposal("Animal Handling", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=8, raw_rolls=(8,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 13  # 8 + 5; pre-fix would be 8 + 1 = 9
        data = json.loads(record.modifiers_json)
        assert data["breakdown"]["animal_handling_modifier"] == 5

    def test_leading_trailing_whitespace_in_sheet_key_normalized(self) -> None:
        """{'  stealth  ': 7}: key with extra whitespace is stripped and found."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"  stealth  ": 7}, dex=16)
        proposal = _make_proposal("stealth", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 17  # 10 + 7; pre-fix would be 10 + 3 = 13

    def test_absent_skill_fallback_unaffected_by_normalization(self) -> None:
        """When skill is absent from sheet.skills, ability-mod fallback still fires."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={}, dex=16)
        proposal = _make_proposal("stealth", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 13  # 10 + 3 (Dex fallback)
        data = json.loads(record.modifiers_json)
        assert data["breakdown"]["dexterity_modifier"] == 3

    def test_announce_display_case_key_visible_modifier_and_note(self) -> None:
        """Announce: display-case sheet key produces correct visible_modifier_total."""
        from uuid import uuid4 as _uuid4

        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"Stealth": 7}, dex=16)
        proposal = _make_proposal("stealth", RollVisibility.PLAYER)
        pending, _view = adapter.prepare_player_roll_announce(
            proposal, sheet, None, [], _uuid4(), _uuid4(), _uuid4()
        )
        assert pending.visible_modifier_total == 7  # pre-fix would be 3 (Dex fallback)
        assert pending.visible_modifier_note == "+7"

    def test_resolve_roll_display_case_modifiers_json_structure(self) -> None:
        """resolve_roll: Perception key gives correct visible_total/breakdown."""
        adapter = D20RulesSystemAdapter()
        # Perception is Wis-governed; wisdom=13 → mod +1 fallback; stored +8.
        sheet = _make_sheet(skills={"Perception": 8})  # wis=13 default
        proposal = _make_proposal("Perception", RollVisibility.SHOWN)
        dice_svc = MagicMock()
        dice_svc.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
        record = adapter.resolve_roll(proposal, sheet, None, [], dice_svc, False)
        assert record.total == 18  # 10 + 8; pre-fix would be 10 + 1 = 11
        data = json.loads(record.modifiers_json)
        assert data["visible_total"] == 8
        assert data["breakdown"]["perception_modifier"] == 8
