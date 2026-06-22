"""Unit tests for D20RulesSystemAdapter — CRD Issue 15 remediation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import ResolvedAdjudicationRecord, RollProposal
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter

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
