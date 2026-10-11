"""Bounded d20 Rules System Adapter — CRD Issue 15.

This is a hand-authored, bounded d20 adapter.  It covers modifier assembly,
code-verified DC lookup, degree-of-success calculation, advantage/disadvantage,
roll-authorship invariant enforcement, and sheet-effect derivation.

Boundaries:
- d20-specific concepts (DC, AC, proficiency, saving throws, ability scores,
  advantage/disadvantage) live HERE, not in generic adjudication code.
- The adapter returns ``outcome="undetermined"`` only where no DC is verified
  (DC verification is deferred). A check it cannot assemble faithfully is
  refused instead: skill checks, saving throws and every other
  proficiency-aware or unrecognized check raise
  :class:`UnsupportedCheckError` (CRD Issue 2b) rather than becoming an
  ability-only roll. Proficiency application, modifier derivation and
  adjudication are CRD Issue 15c's.
- ``gm_cheating=off`` is enforced at record creation time: the record is the
  immutable source of truth; Writer prose cannot change it.
- Roll-authorship is code-enforced: the adapter, not the model, produces
  DiceResult and total values.
"""

from __future__ import annotations

import hashlib
import json
import re
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
from afterworlds.pipeline.rpg.dice import chosen_die_range

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

# Word-boundary patterns so "disadvantage" doesn't trigger the advantage branch.
_ADV_RE = re.compile(r"\badvantage\b", re.IGNORECASE)
_DISADV_RE = re.compile(r"\bdisadvantage\b", re.IGNORECASE)


def _normalize_skill_key(value: str) -> str:
    """Normalize a skill key to lowercase underscore form for case-insensitive lookup.

    Strips leading/trailing whitespace, collapses repeated internal whitespace
    and hyphens to underscores, and lowercases, so "Sleight of Hand", "stealth",
    and "animal_handling" all map to the same canonical key form used in
    _SKILL_ABILITY.
    """
    return re.sub(r"[\s\-]+", "_", value.strip()).lower()


class PlayerRollValueError(ValueError):
    """Raised when a player-reported total implies a die value outside legal range."""


class UnsupportedCheckError(ValueError):
    """A check this adapter cannot assemble without inventing mechanics.

    Raised for proficiency-aware checks (skills, saving throws, tools, attacks),
    for unrecognized check labels, and for an ability whose recorded score has
    sourced adjustments (the total is a 15c derivation). Callers surface it as
    a visible typed failure, never as an ability-only roll.
    """


if TYPE_CHECKING:
    from afterworlds.models.rules_package import ActiveRuleSlice
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.services.dnd5e_state.turn import TurnCharacter


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


def _context_hash(character: TurnCharacter) -> str:
    """A short hash of the exact state a roll was announced against.

    Covers the state revision and its exact binding, so any recorded change
    between announce and consume is detectable.
    """
    stored = character.stored
    payload = {
        "sheet_id": str(stored.sheet_id),
        "revision": stored.revision,
        "binding": stored.binding.model_dump(mode="json"),
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
    slices, computes outcomes, and builds
    ``ResolvedAdjudicationRecord`` instances.

    Returns ``outcome="undetermined"`` when mechanics are outside the
    supported boundary rather than inventing a result.
    """

    def is_adjudicable(self, character: TurnCharacter) -> bool:
        """True when the character's recorded state is ready for its binding.

        Readiness is completeness of recorded inputs, not legality.
        """
        return character.ready

    def _assemble_modifiers(
        self,
        proposal: RollProposal,
        character: TurnCharacter,
        _rule_slice: ActiveRuleSlice | None,
    ) -> _ModifierBreakdown:
        """Assemble the modifier breakdown for a pure ability check.

        Only an ability check on an unadjusted base score is assembled here.
        Every proficiency-aware or unrecognized check is refused.
        """
        label = _normalize_skill_key(proposal.skill_or_attribute_label or "")
        if label in _SKILL_ABILITY or label in _SAVE_ABILITY:
            raise UnsupportedCheckError(
                f"{proposal.check_label!r} is a proficiency-aware check "
                f"({label}); applying proficiency is CRD Issue 15c's, and it is "
                "not rolled as an ability-only check"
            )
        state = character.stored.state
        if state.ability_scores is None:
            raise UnsupportedCheckError("the character records no ability scores")
        scores = state.ability_scores.model_dump()
        abilities = [a for a in scores if a == label] or [
            a for a in scores if a in label.split("_")
        ]
        if len(abilities) != 1 or label not in (
            abilities[0],
            f"{abilities[0]}_check",
            f"{abilities[0]}_ability_check",
        ):
            raise UnsupportedCheckError(
                f"{proposal.check_label!r} ({label or 'no label'}) is not a "
                "recognized pure ability check"
            )
        ability = abilities[0]
        if any(a.ability.value == ability for a in state.ability_adjustments or ()):
            raise UnsupportedCheckError(
                f"{ability} has sourced adjustments; its total is a CRD Issue 15c "
                "derivation"
            )
        mod = _ability_modifier(scores[ability])
        breakdown = {f"{ability}_modifier": mod}
        visible_total = mod

        tag = proposal.subsystem_tag
        advantage = bool(_ADV_RE.search(tag))
        disadvantage = bool(_DISADV_RE.search(tag))

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
        character: TurnCharacter,
        rule_slice: ActiveRuleSlice | None,
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

        mods = self._assemble_modifiers(proposal, character, rule_slice)
        dice_result: DiceResult = dice_service.roll(mods.expression)
        total = dice_result.chosen + mods.full_total
        dc = self._verify_dc(rule_slice)
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
        character: TurnCharacter,
        rule_slice: ActiveRuleSlice | None,
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

        mods = self._assemble_modifiers(proposal, character, rule_slice)

        modifier_note: str | None = None
        if mods.visible_total != 0:
            sign = "+" if mods.visible_total > 0 else ""
            modifier_note = f"{sign}{mods.visible_total}"

        instruction = f"Roll {mods.expression}"
        if modifier_note:
            instruction += f" {modifier_note}"

        context_hash = _context_hash(character)

        pending = PendingRollRequest(
            request_id=uuid4(),
            story_id=story_id,
            session_id=session_id,
            character_id=character.sheet_id,
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
        gm_cheating: bool,
    ) -> ResolvedAdjudicationRecord:
        """Resolve a player-reported roll against the stored PendingRollRequest.

        Uses the roll terms that were announced (stored in ``pending``), not
        freshly recomputed sheet state.  ``adapter_context_hash`` drift is
        logged but does NOT trigger recomputation in v1.
        """
        dc = self._verify_dc(rule_slice)
        visible_mod = pending.visible_modifier_total or 0
        hidden_mod = 0
        raw_die = reported_total - visible_mod - hidden_mod

        try:
            min_die, max_die = chosen_die_range(pending.roll_expression)
        except ValueError as exc:
            raise PlayerRollValueError(
                f"Cannot validate roll: unsupported expression "
                f"{pending.roll_expression!r}"
            ) from exc
        if not (min_die <= raw_die <= max_die):
            raise PlayerRollValueError(
                f"Player-reported total {reported_total} implies raw die {raw_die}, "
                f"outside [{min_die}, {max_die}] for {pending.roll_expression!r}"
            )

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
        _character: TurnCharacter,
    ) -> tuple[SheetEffect, ...]:
        """Derive mechanical sheet mutations from a resolved record.

        v1: Returns the sheet_effects already embedded in the record.
        Effect computation requiring full encounter context (e.g. damage
        dice from a weapon attack hit) is assembled by the adjudication
        service in Phase 4 before constructing the ResolvedAdjudicationRecord.
        """
        return record.sheet_effects
