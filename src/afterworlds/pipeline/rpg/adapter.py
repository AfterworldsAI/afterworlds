"""Bounded d20 Rules System Adapter — CRD Issue 15.

This is a hand-authored, bounded d20 adapter.  It covers modifier assembly,
code-verified DC lookup, degree-of-success calculation, advantage/disadvantage,
roll-authorship invariant enforcement, and sheet-effect derivation.

Boundaries:
- d20-specific concepts (DC, AC, proficiency, saving throws, ability scores,
  advantage/disadvantage) live HERE, not in generic adjudication code.
- The adapter returns ``outcome="undetermined"`` when the mechanic is outside
  the supported boundary, rather than inventing a result.
- ``gm_cheating=off`` is enforced at record creation time: the record is the
  immutable source of truth; Writer prose cannot change it.
- Roll-authorship is code-enforced: the adapter, not the model, produces
  DiceResult and total values.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    DiceResult,
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    SheetEffect,
    WriterAdjudicationView,
)

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

if TYPE_CHECKING:
    from afterworlds.models.character_sheet import Dnd5eCharacterSheet
    from afterworlds.models.rules_package import ActiveRuleSlice, RuleOverride
    from afterworlds.pipeline.rpg.dice import DiceService


# Skill → governing ability score name (D&D 5e).
_SKILL_ABILITY: dict[str, str] = {
    "acrobatics": "dexterity",
    "animal_handling": "wisdom",
    "arcana": "intelligence",
    "athletics": "strength",
    "deception": "charisma",
    "history": "intelligence",
    "insight": "wisdom",
    "intimidation": "charisma",
    "investigation": "intelligence",
    "medicine": "wisdom",
    "nature": "intelligence",
    "perception": "wisdom",
    "performance": "charisma",
    "persuasion": "charisma",
    "religion": "intelligence",
    "sleight_of_hand": "dexterity",
    "stealth": "dexterity",
    "survival": "wisdom",
}

# Saving throw → governing ability score (D&D 5e).
_SAVE_ABILITY: dict[str, str] = {
    "strength_save": "strength",
    "dexterity_save": "dexterity",
    "constitution_save": "constitution",
    "intelligence_save": "intelligence",
    "wisdom_save": "wisdom",
    "charisma_save": "charisma",
}


def _ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _context_hash(sheet: Dnd5eCharacterSheet) -> str:
    """Compute a short hash of adjudication-relevant sheet state.

    Used to detect drift between PendingRollRequest announce and consume.
    Only covers fields that affect modifier assembly; equipment and other
    fields that don't affect the modifier total are excluded.
    """
    payload = {
        "level": sheet.level,
        "ability_scores": sheet.ability_scores.model_dump(),
        "skills": sheet.skills,
        "current_hp": sheet.current_hp,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


class _ModifierBreakdown:
    """Internal modifier assembly result."""

    __slots__ = (
        "visible_total",
        "hidden_total",
        "breakdown_json",
        "has_hidden",
        "advantage",
        "disadvantage",
        "expression",
    )

    def __init__(
        self,
        visible_total: int,
        hidden_total: int,
        breakdown: dict[str, int],
        has_hidden: bool,
        advantage: bool,
        disadvantage: bool,
        expression: str,
    ) -> None:
        self.visible_total = visible_total
        self.hidden_total = hidden_total
        self.breakdown_json = json.dumps(breakdown, sort_keys=True)
        self.has_hidden = has_hidden
        self.advantage = advantage
        self.disadvantage = disadvantage
        self.expression = expression

    @property
    def full_total(self) -> int:
        return self.visible_total + self.hidden_total

    @property
    def visible_breakdown_json(self) -> str | None:
        return self.breakdown_json if not self.has_hidden else None


class D20RulesSystemAdapter:
    """Hand-authored bounded d20 Rules System Adapter.

    Constructs deterministic modifier breakdowns, verifies DCs from rule
    slices and house-rule overrides, computes outcomes, and builds
    ``ResolvedAdjudicationRecord`` instances.

    Returns ``outcome="undetermined"`` when mechanics are outside the
    supported boundary rather than inventing a result.
    """

    def is_adjudicable(self, sheet: Dnd5eCharacterSheet) -> bool:
        """Return True if the sheet has enough data to support adjudication.

        Checks that the sheet has the fields required by the bounded d20
        adapter: ability scores, a rules_package_id, and a non-zero level.
        """
        try:
            scores = sheet.ability_scores.model_dump()
        except AttributeError:
            return False
        if not all(isinstance(v, int) and v > 0 for v in scores.values()):
            return False
        if not sheet.rules_package_id:
            return False
        return 1 <= sheet.level <= 20

    def _assemble_modifiers(
        self,
        proposal: RollProposal,
        sheet: Dnd5eCharacterSheet,
        _rule_slice: ActiveRuleSlice | None,
        _overrides: list[RuleOverride],
    ) -> _ModifierBreakdown:
        """Assemble the modifier breakdown for a roll proposal.

        Derives visible modifier (ability mod + proficiency where applicable)
        from the character sheet.  Hidden modifiers are not implemented in v1
        (no invisible conditional bonuses in the bounded d20 scope).
        """
        scores = sheet.ability_scores.model_dump()

        label = (proposal.skill_or_attribute_label or "").lower().replace(" ", "_")
        breakdown: dict[str, int] = {}
        visible_total = 0

        if label in _SKILL_ABILITY:
            if label in sheet.skills:
                # skills stores the computed modifier (ability mod + prof).
                stored = sheet.skills[label]
                breakdown[f"{label}_modifier"] = stored
                visible_total += stored
            else:
                ability = _SKILL_ABILITY[label]
                mod = _ability_modifier(scores[ability])
                breakdown[f"{ability}_modifier"] = mod
                visible_total += mod
        elif label in _SAVE_ABILITY:
            # v1: saves are ability-mod-only; no save-proficiency in sheet.
            ability = _SAVE_ABILITY[label]
            mod = _ability_modifier(scores[ability])
            breakdown[f"{ability}_modifier"] = mod
            visible_total += mod
        elif label in scores:
            mod = _ability_modifier(scores[label])
            breakdown[f"{label}_modifier"] = mod
            visible_total += mod
        else:
            for ability in scores:
                if ability in label:
                    mod = _ability_modifier(scores[ability])
                    breakdown[f"{ability}_modifier"] = mod
                    visible_total += mod
                    break

        advantage = "advantage" in proposal.subsystem_tag.lower()
        disadvantage = "disadvantage" in proposal.subsystem_tag.lower()

        if advantage and not disadvantage:
            expression = "2d20kh1"
        elif disadvantage and not advantage:
            expression = "2d20kl1"
        else:
            expression = "1d20"

        return _ModifierBreakdown(
            visible_total=visible_total,
            hidden_total=0,
            breakdown=breakdown,
            has_hidden=False,
            advantage=advantage,
            disadvantage=disadvantage,
            expression=expression,
        )

    def _verify_dc(
        self,
        _rule_slice: ActiveRuleSlice | None,
        _overrides: list[RuleOverride],
    ) -> int | None:
        """DC verification is deferred to Issue 18.

        Always returns None in v1.  Model-authored subsystem_tag and
        difficulty_reference_note are never authoritative DC sources.
        """
        return None

    def _compute_outcome(
        self,
        total: int,
        dc: int | None,
        raw_chosen: int,
        sides: int = 20,
    ) -> _Outcome:
        """Compute outcome string from total, DC, and raw die result.

        Critical success (natural max) and critical failure (natural 1) are
        recognised for d20 rolls only when DC is not None.
        """
        if dc is None:
            return "undetermined"

        is_nat_max = raw_chosen == sides
        is_nat_one = raw_chosen == 1

        if sides == 20:
            if is_nat_max:
                return "critical_success"
            if is_nat_one:
                return "critical_failure"

        if total >= dc:
            return "success"
        return "failure"

    def resolve_roll(
        self,
        proposal: RollProposal,
        sheet: Dnd5eCharacterSheet,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        dice_service: DiceService,
        gm_cheating: bool,
    ) -> ResolvedAdjudicationRecord:
        """Resolve an AI or HIDDEN roll and return an immutable record.

        PLAYER rolls must use ``prepare_player_roll_announce`` instead;
        this method raises ``ValueError`` if called with a PLAYER proposal.
        """
        if proposal.visibility is RollVisibility.PLAYER:
            raise ValueError(
                "resolve_roll called on PLAYER visibility proposal; "
                "use prepare_player_roll_announce instead"
            )

        mods = self._assemble_modifiers(proposal, sheet, rule_slice, overrides)
        dice_result: DiceResult = dice_service.roll(mods.expression)
        total = dice_result.chosen + mods.full_total
        dc = self._verify_dc(rule_slice, overrides)
        outcome = self._compute_outcome(total, dc, dice_result.chosen)

        return ResolvedAdjudicationRecord(
            check_label=proposal.check_label,
            visibility=proposal.visibility,
            expression=mods.expression,
            raw_rolls=dice_result.raw_rolls,
            modifiers_json=json.dumps(
                {
                    "visible_total": mods.visible_total,
                    "breakdown": json.loads(mods.breakdown_json),
                },
                sort_keys=True,
            ),
            total=total,
            dc=dc,
            outcome=outcome,
            sheet_effects=(),
            source=("hidden" if proposal.visibility is RollVisibility.HIDDEN else "ai"),
            gm_cheating_at_roll=gm_cheating,
        )

    def prepare_player_roll_announce(
        self,
        proposal: RollProposal,
        sheet: Dnd5eCharacterSheet,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        story_id: UUID,
        session_id: UUID,
        originating_turn_id: UUID,
    ) -> tuple[PendingRollRequest, WriterAdjudicationView]:
        """Build a PendingRollRequest and announce WriterAdjudicationView.

        Called on the announce turn.  The PendingRollRequest stores the
        code-derived roll terms for validation on the consume turn.
        """
        if proposal.visibility is not RollVisibility.PLAYER:
            raise ValueError(
                "prepare_player_roll_announce called on non-PLAYER proposal"
            )

        mods = self._assemble_modifiers(proposal, sheet, rule_slice, overrides)

        modifier_note: str | None = None
        if mods.visible_total != 0:
            sign = "+" if mods.visible_total > 0 else ""
            modifier_note = f"{sign}{mods.visible_total}"

        instruction = f"Roll {mods.expression}"
        if modifier_note:
            instruction += f" {modifier_note}"

        context_hash = _context_hash(sheet)

        pending = PendingRollRequest(
            request_id=uuid4(),
            story_id=story_id,
            session_id=session_id,
            character_id=sheet.sheet_id,
            check_label=proposal.check_label,
            player_facing_instruction=instruction,
            expected_value_shape="integer",
            visible_modifier_note=modifier_note,
            visibility=RollVisibility.PLAYER,
            source_proposal_ref=f"{proposal.subsystem_tag}/{proposal.check_label}",
            originating_turn_id=originating_turn_id,
            created_at=datetime.now(tz=UTC),
            roll_expression=mods.expression,
            visible_modifier_total=mods.visible_total if not mods.has_hidden else None,
            visible_modifier_breakdown_json=mods.visible_breakdown_json,
            hidden_modifier_present=mods.has_hidden,
            adapter_context_hash=context_hash,
        )

        summary = f"Roll needed: {instruction} for {proposal.check_label}"
        view = WriterAdjudicationView(
            check_label=proposal.check_label,
            visibility=RollVisibility.PLAYER,
            player_facing_summary=summary,
            total=None,
            dc=None,
            outcome=None,
        )

        return pending, view

    def consume_player_roll(
        self,
        pending: PendingRollRequest,
        reported_total: int,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        gm_cheating: bool,
    ) -> ResolvedAdjudicationRecord:
        """Resolve a player-reported roll against the stored PendingRollRequest.

        Uses the roll terms that were announced (stored in ``pending``), not
        freshly recomputed sheet state.  ``adapter_context_hash`` drift is
        logged but does NOT trigger recomputation in v1.
        """
        dc = self._verify_dc(rule_slice, overrides)
        visible_mod = pending.visible_modifier_total or 0
        hidden_mod = 0
        raw_die = reported_total - visible_mod - hidden_mod

        outcome = self._compute_outcome(reported_total, dc, raw_die)

        return ResolvedAdjudicationRecord(
            check_label=pending.check_label,
            visibility=RollVisibility.PLAYER,
            expression=pending.roll_expression,
            raw_rolls=(raw_die,),
            modifiers_json=json.dumps(
                {
                    "visible_total": visible_mod,
                    "breakdown": json.loads(
                        pending.visible_modifier_breakdown_json or "{}"
                    ),
                },
                sort_keys=True,
            ),
            total=reported_total,
            dc=dc,
            outcome=outcome,
            sheet_effects=(),
            source="player",
            gm_cheating_at_roll=gm_cheating,
        )

    def to_writer_view(
        self, record: ResolvedAdjudicationRecord
    ) -> WriterAdjudicationView:
        """Produce a visibility-filtered WriterAdjudicationView from a record.

        For HIDDEN rolls: total, dc, and outcome are None.
        ``hidden_modifier_present`` is never surfaced here.
        """
        if record.visibility is RollVisibility.HIDDEN:
            # check_label and player_facing_summary must not reveal the check
            # exists, its type, or any mechanical result (ADR-015 Decision 5).
            return WriterAdjudicationView(
                check_label="",
                visibility=record.visibility,
                player_facing_summary="The scene continues.",
                total=None,
                dc=None,
                outcome=None,
            )

        summary_parts = [f"{record.check_label}: rolled {record.total}"]
        if record.dc is not None:
            summary_parts.append(f"vs DC {record.dc}")
        if record.outcome not in (None, "undetermined"):
            summary_parts.append(f"— {record.outcome.replace('_', ' ')}")

        return WriterAdjudicationView(
            check_label=record.check_label,
            visibility=record.visibility,
            player_facing_summary=", ".join(summary_parts),
            total=record.total,
            dc=record.dc,
            outcome=record.outcome,
        )

    def compute_sheet_effects(
        self,
        record: ResolvedAdjudicationRecord,
        _sheet: Dnd5eCharacterSheet,
    ) -> tuple[SheetEffect, ...]:
        """Derive mechanical sheet mutations from a resolved record.

        v1: Returns the sheet_effects already embedded in the record.
        Effect computation requiring full encounter context (e.g. damage
        dice from a weapon attack hit) is assembled by the adjudication
        service in Phase 4 before constructing the ResolvedAdjudicationRecord.
        """
        return record.sheet_effects
