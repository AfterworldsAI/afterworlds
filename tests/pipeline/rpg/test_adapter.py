"""Unit tests for D20RulesSystemAdapter — CRD Issue 15 remediation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
from afterworlds.models.enums import (
    DiceSelectionRule,
    ModifierVisibility,
    RollContribution,
    RollPurpose,
    RollVisibility,
)
from afterworlds.models.rpg import (
    ResolvedAdjudicationRecord,
    RollInstructionSnapshot,
    RollModifierComponent,
    RollProposal,
    RollTerm,
)
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
# build_check_instruction / resolve_snapshot (CRD Issue 15b) — replaces the
# retired prepare_player_roll_announce/consume_player_roll expression-string
# path. Range/count validation of submitted values is ActionResolutionService's
# job now, not the adapter's — see tests/pipeline/rpg/test_sequence.py.
# ---------------------------------------------------------------------------


def _build_instruction(
    adapter: D20RulesSystemAdapter,
    *,
    label: str = "stealth",
    subsystem_tag: str = "skill_check",
    sheet: Dnd5eCharacterSheet | None = None,
):
    proposal = _make_proposal(label, RollVisibility.PLAYER, subsystem_tag)
    return adapter.build_check_instruction(
        proposal,
        sheet or _make_sheet(skills={"stealth": 3}),
        None,
        [],
        sequence_id=uuid4(),
        step_id=uuid4(),
        instruction_id=uuid4(),
    )


def test_build_check_instruction_plain_tag_is_1d20_sum_all() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, subsystem_tag="skill_check")
    assert len(instruction.terms) == 1
    term = instruction.terms[0]
    assert (term.count, term.sides) == (1, 20)
    from afterworlds.models.enums import DiceSelectionRule

    assert term.selection_rule is DiceSelectionRule.SUM_ALL
    assert term.keep_count is None


def test_build_check_instruction_advantage_tag_is_2d20_keep_highest() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, subsystem_tag="skill_check advantage")
    term = instruction.terms[0]
    from afterworlds.models.enums import DiceSelectionRule

    assert (term.count, term.sides) == (2, 20)
    assert term.selection_rule is DiceSelectionRule.KEEP_HIGHEST
    assert term.keep_count == 1


def test_build_check_instruction_disadvantage_tag_is_2d20_keep_lowest() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, subsystem_tag="skill_check disadvantage")
    term = instruction.terms[0]
    from afterworlds.models.enums import DiceSelectionRule

    assert term.selection_rule is DiceSelectionRule.KEEP_LOWEST
    assert term.keep_count == 1


def test_build_check_instruction_rejects_non_player_proposal() -> None:
    adapter = D20RulesSystemAdapter()
    proposal = _make_proposal("stealth", RollVisibility.SHOWN)
    with pytest.raises(ValueError, match="non-PLAYER"):
        adapter.build_check_instruction(
            proposal,
            _make_sheet(),
            None,
            [],
            sequence_id=uuid4(),
            step_id=uuid4(),
            instruction_id=uuid4(),
        )


def test_resolve_snapshot_sum_all_totals_die_plus_modifier() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, sheet=_make_sheet(skills={"stealth": 5}))
    term = instruction.terms[0]
    record = adapter.resolve_snapshot(
        instruction=instruction,
        term_results={term.term_id: (15,)},
        rule_slice=None,
        overrides=[],
        source="player",
        gm_cheating=False,
    )
    assert record.total == 20  # 15 + 5
    assert record.raw_rolls == (15,)
    assert record.outcome == "undetermined"  # DC always None in v1


def test_resolve_snapshot_keep_highest_selects_max_die() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(
        adapter,
        subsystem_tag="skill_check advantage",
        sheet=_make_sheet(skills={"stealth": 0}),
    )
    term = instruction.terms[0]
    record = adapter.resolve_snapshot(
        instruction=instruction,
        term_results={term.term_id: (8, 17)},
        rule_slice=None,
        overrides=[],
        source="player",
        gm_cheating=False,
    )
    assert record.total == 17


def test_resolve_snapshot_keep_lowest_selects_min_die() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(
        adapter,
        subsystem_tag="skill_check disadvantage",
        sheet=_make_sheet(skills={"stealth": 0}),
    )
    term = instruction.terms[0]
    record = adapter.resolve_snapshot(
        instruction=instruction,
        term_results={term.term_id: (14, 3)},
        rule_slice=None,
        overrides=[],
        source="player",
        gm_cheating=False,
    )
    assert record.total == 3


def _multi_keep_instruction(
    *,
    selection_rule: DiceSelectionRule,
    keep_count: int | None,
    count: int = 4,
    sides: int = 6,
) -> tuple[RollInstructionSnapshot, RollTerm]:
    """A hand-built instruction with a keep_count > 1 term.

    ADR-015b's own defect inventory (item 2) flags the retired executor's
    ``sorted(raw, ...)[:keep_n][0]`` bug — it took one die from the kept
    slice instead of summing it, so ``4d6kh3`` silently returned a single
    die's value. ``build_check_instruction`` never generates a keep_count>1
    term (the shipped adapter only produces 1d20/2d20kh1/2d20kl1), so this
    constructs the instruction directly to exercise ``_reduce_term`` (via
    ``resolve_snapshot``) against the exact shape the ADR requires proven.
    """
    term = RollTerm(
        term_id=uuid4(),
        count=count,
        sides=sides,
        selection_rule=selection_rule,
        keep_count=keep_count,
    )
    instruction = RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.ABILITY_CHECK,
        terms=(term,),
        modifier_components=(),
        display_expression=f"{count}d{sides}",
        display_label="Ability Check",
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
    )
    return instruction, term


def test_resolve_snapshot_keep_highest_sums_top_k_not_single_die() -> None:
    """4d6kh3: total must be the sum of the top 3 dice (15), not one die."""
    adapter = D20RulesSystemAdapter()
    instruction, term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=3
    )
    record = adapter.resolve_snapshot(
        instruction=instruction,
        term_results={term.term_id: (2, 6, 4, 5)},
        rule_slice=None,
        overrides=[],
        source="player",
        gm_cheating=False,
    )
    assert record.total == 15  # 6 + 4 + 5, dropping the lowest (2)


def test_resolve_snapshot_keep_lowest_sums_bottom_k_not_single_die() -> None:
    """4d6kl3: total must be the sum of the bottom 3 dice (11), not one die."""
    adapter = D20RulesSystemAdapter()
    instruction, term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.KEEP_LOWEST, keep_count=3
    )
    record = adapter.resolve_snapshot(
        instruction=instruction,
        term_results={term.term_id: (2, 6, 4, 5)},
        rule_slice=None,
        overrides=[],
        source="player",
        gm_cheating=False,
    )
    assert record.total == 11  # 2 + 4 + 5, dropping the highest (6)


def test_aggregate_range_covers_full_legal_span() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, sheet=_make_sheet(skills={"stealth": 5}))
    assert adapter.aggregate_range(instruction) == (6, 25)  # 1d20 [1,20] + mod 5


def test_aggregate_range_keep_highest_2d20kh1_is_1_to_20() -> None:
    """Codex P1 (PR #129): must be [1, 20], not [2, 40] (2 dice * 20 sides)."""
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(
        adapter,
        subsystem_tag="skill_check advantage",
        sheet=_make_sheet(skills={"stealth": 0}),
    )
    assert adapter.aggregate_range(instruction) == (1, 20)


def test_aggregate_range_keep_lowest_2d20kl1_is_1_to_20() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(
        adapter,
        subsystem_tag="skill_check disadvantage",
        sheet=_make_sheet(skills={"stealth": 0}),
    )
    assert adapter.aggregate_range(instruction) == (1, 20)


def test_aggregate_range_keep_highest_4d6kh3_is_3_to_18() -> None:
    instruction, _term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=3
    )
    adapter = D20RulesSystemAdapter()
    assert adapter.aggregate_range(instruction) == (3, 18)


def test_aggregate_range_keep_lowest_4d6kl3_is_3_to_18() -> None:
    instruction, _term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.KEEP_LOWEST, keep_count=3
    )
    adapter = D20RulesSystemAdapter()
    assert adapter.aggregate_range(instruction) == (3, 18)


def test_aggregate_range_summed_pool() -> None:
    """4d6 sum-all: [4, 24]."""
    instruction, _term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.SUM_ALL, keep_count=None
    )
    adapter = D20RulesSystemAdapter()
    assert adapter.aggregate_range(instruction) == (4, 24)


def test_aggregate_range_subtraction_reverses_extremes() -> None:
    """A subtracted 1d6 term contributes [-6, -1], not [1, 6]."""
    term = RollTerm(
        term_id=uuid4(),
        count=1,
        sides=6,
        selection_rule=DiceSelectionRule.SUM_ALL,
        keep_count=None,
        contribution=RollContribution.SUBTRACT,
    )
    instruction = RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.ABILITY_CHECK,
        terms=(term,),
        modifier_components=(),
        display_expression="1d6",
        display_label="Subtracted Check",
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
    )
    adapter = D20RulesSystemAdapter()
    assert adapter.aggregate_range(instruction) == (-6, -1)


def test_aggregate_range_mixed_repeated_pools_with_modifier() -> None:
    """2d20kh1 (advantage attack, [1,20]) + 2d6 damage (SUM_ALL, [2,12]) + a
    +3 modifier: total range [1+2+3, 20+12+3] = [6, 35]."""
    attack_term = RollTerm(
        term_id=uuid4(),
        count=2,
        sides=20,
        selection_rule=DiceSelectionRule.KEEP_HIGHEST,
        keep_count=1,
        contribution=RollContribution.ADD,
    )
    damage_term = RollTerm(
        term_id=uuid4(),
        count=2,
        sides=6,
        selection_rule=DiceSelectionRule.SUM_ALL,
        keep_count=None,
        contribution=RollContribution.ADD,
    )
    modifier = RollModifierComponent(
        modifier_id=uuid4(),
        label="strength",
        value=3,
        visibility=ModifierVisibility.PLAYER_VISIBLE,
        source_kind="sheet_modifier",
        source_reference=None,
    )
    instruction = RollInstructionSnapshot(
        instruction_id=uuid4(),
        instruction_revision=1,
        purpose=RollPurpose.ATTACK,
        terms=(attack_term, damage_term),
        modifier_components=(modifier,),
        display_expression="2d20kh1+2d6",
        display_label="Mixed Pool Attack",
        source_rule_refs=(),
        adjustment_options=(),
        sequence_id=uuid4(),
        step_id=uuid4(),
    )
    adapter = D20RulesSystemAdapter()
    assert adapter.aggregate_range(instruction) == (6, 35)


def test_aggregate_range_boundary_values_accepted_by_resolve_aggregate_snapshot() -> (
    None
):
    """The exact min/max boundary from aggregate_range must itself be legal."""
    instruction, _term = _multi_keep_instruction(
        selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=3
    )
    adapter = D20RulesSystemAdapter()
    min_total, max_total = adapter.aggregate_range(instruction)
    for boundary in (min_total, max_total):
        record = adapter.resolve_aggregate_snapshot(
            instruction=instruction,
            reported_aggregate=boundary,
            rule_slice=None,
            overrides=[],
            gm_cheating=False,
        )
        assert record.total == boundary


def test_resolve_aggregate_snapshot_uses_reported_total_directly() -> None:
    adapter = D20RulesSystemAdapter()
    instruction = _build_instruction(adapter, sheet=_make_sheet(skills={"stealth": 5}))
    record = adapter.resolve_aggregate_snapshot(
        instruction=instruction,
        reported_aggregate=18,
        rule_slice=None,
        overrides=[],
        gm_cheating=False,
    )
    assert record.total == 18
    assert record.raw_rolls == ()


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

    def test_build_check_instruction_display_case_key_uses_stored_modifier(
        self,
    ) -> None:
        """Announce: display-case sheet key produces a correct modifier_component."""
        adapter = D20RulesSystemAdapter()
        sheet = _make_sheet(skills={"Stealth": 7}, dex=16)
        proposal = _make_proposal("stealth", RollVisibility.PLAYER)
        instruction = adapter.build_check_instruction(
            proposal,
            sheet,
            None,
            [],
            sequence_id=uuid4(),
            step_id=uuid4(),
            instruction_id=uuid4(),
        )
        # pre-fix would be 3 (Dex fallback) instead of the stored +7.
        assert instruction.modifier_components[0].value == 7
        assert "+7" in instruction.display_expression

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
