"""Bounded d20 Rules System Adapter — CRD Issue 15. Revised by CRD Issue 15b.

This is a hand-authored, bounded d20 adapter.  It covers modifier assembly,
DC lookup (always None in v1 — see ``_verify_dc``), degree-of-success
calculation, advantage/disadvantage, roll-authorship invariant enforcement,
and sheet-effect derivation.

CRD Issue 15b adds structured RollInstructionSnapshot/RollTerm generation
(``build_check_instruction``) and resolution (``resolve_snapshot``) for
PLAYER rolls, superseding the retired ``prepare_player_roll_announce``/
``consume_player_roll`` total-only path (ADR-015b, 15b-25).

Boundaries:
- d20-specific concepts (DC, AC, proficiency, saving throws, ability scores,
  advantage/disadvantage) live HERE, not in generic adjudication code.
- The adapter returns ``outcome="undetermined"`` when the mechanic is outside
  the supported boundary, rather than inventing a result. In v1 this covers
  every DC-gated purpose unconditionally — see ``_verify_dc``.
- ``gm_cheating=off`` is enforced at record creation time: the record is the
  immutable source of truth; Writer prose cannot change it.
- Roll-authorship is code-enforced: the adapter, not the model, produces
  DiceResult and total values.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from afterworlds.models.enums import (
    DiceSelectionRule,
    ModifierVisibility,
    RollContribution,
    RollPurpose,
    RollVisibility,
)
from afterworlds.models.rpg import (
    DiceResult,
    ResolvedAdjudicationRecord,
    RollInstructionSnapshot,
    RollModifierComponent,
    RollProposal,
    RollTerm,
    SheetEffect,
    WriterAdjudicationView,
)

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


# Legacy 3-expression shapes, now emitted as structured RollTerm fields
# (CRD Issue 15b) instead of a display-only string. Order matches
# DiceSelectionRule; keep_count is None for a straight sum-all roll.
_CHECK_EXPRESSION_SHAPES: dict[str, tuple[int, int, DiceSelectionRule, int | None]] = {
    "1d20": (1, 20, DiceSelectionRule.SUM_ALL, None),
    "2d20kh1": (2, 20, DiceSelectionRule.KEEP_HIGHEST, 1),
    "2d20kl1": (2, 20, DiceSelectionRule.KEEP_LOWEST, 1),
}


def _reduce_term(term: RollTerm, values: tuple[int, ...]) -> tuple[int, int]:
    """Reduce one RollTerm's rolled values to (subtotal, representative_die).

    ``representative_die`` is the single value crit-recognition inspects
    (meaningful only for a ``sides==20`` term) — the sole kept die for a
    keep-highest/keep-lowest term, or the first value for a straight roll.
    Raises ``PlayerRollValueError`` if ``values`` doesn't match what the
    term's shape requires — a defensive check; primary validation belongs
    to ``ActionResolutionService`` before this is ever called.
    """
    if len(values) != term.count:
        raise PlayerRollValueError(
            f"Term {term.term_id} expects {term.count} value(s), got {len(values)}"
        )
    if term.selection_rule is DiceSelectionRule.SUM_ALL:
        return sum(values), values[0]
    keep_n = term.keep_count or 1
    ordered = sorted(
        values, reverse=(term.selection_rule is DiceSelectionRule.KEEP_HIGHEST)
    )
    kept = ordered[:keep_n]
    return sum(kept), kept[0]


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

    Constructs deterministic modifier breakdowns, computes outcomes, and
    builds ``ResolvedAdjudicationRecord`` instances. DC lookup
    (``_verify_dc``) always returns None in v1 — no DC-bearing field exists
    in the current Rules Package schema — so every DC-gated purpose resolves
    to ``outcome="undetermined"`` by construction; see the "Rules Package
    DC-data-modeling gap" Known Unknown.

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

        label = _normalize_skill_key(proposal.skill_or_attribute_label or "")
        breakdown: dict[str, int] = {}
        visible_total = 0

        # Build a normalized lookup so display-case sheet keys ("Stealth",
        # "Sleight of Hand") are found by the same underscore form used in
        # _SKILL_ABILITY and by the normalized label above.
        _skill_map = {_normalize_skill_key(k): v for k, v in sheet.skills.items()}

        if label in _SKILL_ABILITY:
            if label in _skill_map:
                # skills stores the computed modifier (ability mod + prof).
                stored = _skill_map[label]
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
        _overrides: list[RuleOverride],
    ) -> int | None:
        """Always returns None in v1 — no DC-bearing field exists to verify against.

        Model-authored subsystem_tag and difficulty_reference_note are never
        authoritative DC sources (ADR-015 Decision 3). Beyond that: the
        curated Rules Package's structured entity types (SpellEntity,
        ConditionEntity, StatBlockEntity, ActionEntity) carry no dc /
        difficulty_class / save_dc field of any kind, so there is nothing
        for a rule-slice lookup to find. ``RuleOverride`` is a non-mutating
        layered content-patch channel for chunks/entities, not a per-call
        numeric-DC channel, and does not fill this gap either. Adding a
        machine-readable DC field is a Rules Package schema change owned by
        CRD Issue 5a/5b, not CRD Issue 15b (which owns roll INSTRUCTION
        structure, not Rules Package data modeling) — see the "Rules
        Package DC-data-modeling gap" Known Unknown. Per ADR-015 Decision 7,
        the adapter returns ``outcome="undetermined"`` rather than inventing
        a result, so every DC-gated purpose (attack, saving throw, ability
        check, skill check, contested) resolves to "undetermined" by
        construction in v1; non-DC purposes (damage, healing, duration) are
        unaffected since they never compare against a DC.
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

        # ponytail: crit success/failure on a natural 20/1 applies to attack
        # purposes (and death saves) only in 5e, not saves/checks generally —
        # this branch currently fires on any d20 regardless of purpose. Dead
        # code today (dc is always None, so this function returns above
        # before reaching here); restrict to attack purpose once real DC
        # data lands (Rules Package DC-data-modeling gap, owned by 5a/5b).
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

        PLAYER rolls must use ``build_check_instruction``/``resolve_snapshot``
        instead; this method raises ``ValueError`` if called with a PLAYER
        proposal.
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

    def build_check_instruction(
        self,
        proposal: RollProposal,
        sheet: Dnd5eCharacterSheet,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        *,
        sequence_id: UUID,
        step_id: UUID,
        instruction_id: UUID,
    ) -> RollInstructionSnapshot:
        """Build a structured RollInstructionSnapshot for a PLAYER check/save/attack.

        CRD Issue 15b — replaces the retired ``prepare_player_roll_announce``
        expression-string path. Purpose is inferred from the same skill/save
        lookup ``_assemble_modifiers`` already uses (SKILL_CHECK/SAVING_THROW),
        falling back to ABILITY_CHECK — ``RollProposal`` carries no explicit
        purpose field for the adapter to read. Persistence (PendingRollRequest,
        sequence linkage) is ``ActionResolutionService``'s responsibility, not
        the adapter's; this method returns the instruction only.
        """
        if proposal.visibility is not RollVisibility.PLAYER:
            raise ValueError("build_check_instruction called on non-PLAYER proposal")

        mods = self._assemble_modifiers(proposal, sheet, rule_slice, overrides)
        count, sides, selection_rule, keep_count = _CHECK_EXPRESSION_SHAPES[
            mods.expression
        ]

        term = RollTerm(
            term_id=uuid4(),
            count=count,
            sides=sides,
            selection_rule=selection_rule,
            keep_count=keep_count,
            contribution=RollContribution.ADD,
            label=proposal.check_label,
        )

        modifier_components: list[RollModifierComponent] = []
        breakdown = json.loads(mods.breakdown_json) if mods.breakdown_json else {}
        for label, value in breakdown.items():
            modifier_components.append(
                RollModifierComponent(
                    modifier_id=uuid4(),
                    label=label,
                    value=value,
                    visibility=ModifierVisibility.PLAYER_VISIBLE,
                    source_kind="sheet_modifier",
                    source_reference=None,
                )
            )

        label = _normalize_skill_key(proposal.skill_or_attribute_label or "")
        purpose = (
            RollPurpose.SKILL_CHECK
            if label in _SKILL_ABILITY
            else (
                RollPurpose.SAVING_THROW
                if label in _SAVE_ABILITY
                else RollPurpose.ABILITY_CHECK
            )
        )

        modifier_note = ""
        if mods.visible_total != 0:
            sign = "+" if mods.visible_total > 0 else ""
            modifier_note = f" {sign}{mods.visible_total}"

        dc = self._verify_dc(rule_slice, overrides)

        return RollInstructionSnapshot(
            instruction_id=instruction_id,
            instruction_revision=1,
            purpose=purpose,
            terms=(term,),
            modifier_components=tuple(modifier_components),
            display_expression=f"{mods.expression}{modifier_note}",
            display_label=proposal.check_label,
            source_rule_refs=(),
            adjustment_options=(),
            sequence_id=sequence_id,
            step_id=step_id,
            dc=dc,
        )

    def resolve_snapshot(
        self,
        *,
        instruction: RollInstructionSnapshot,
        term_results: dict[UUID, tuple[int, ...]],
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        source: Literal["ai", "hidden", "player"],
        gm_cheating: bool,
    ) -> ResolvedAdjudicationRecord:
        """Resolve a RollInstructionSnapshot against already-rolled term values.

        CRD Issue 15b — the structured successor to ``resolve_roll`` and the
        retired ``consume_player_roll``. Callers (``ActionResolutionService``
        for player submissions, this adapter's own AI/hidden generation path)
        supply ``term_results`` keyed by ``term_id``; this method derives
        subtotals per term's ``selection_rule``, sums with modifiers, and
        computes ``outcome``. Does not roll dice itself and does not persist
        anything — pure resolution.
        """
        total = sum(m.value for m in instruction.modifier_components)
        raw_chosen_for_crit: int | None = None
        for term in instruction.terms:
            values = term_results.get(term.term_id, ())
            subtotal, chosen = _reduce_term(term, values)
            signed = (
                subtotal if term.contribution is RollContribution.ADD else -subtotal
            )
            total += signed
            if term.sides == 20 and raw_chosen_for_crit is None:
                raw_chosen_for_crit = chosen

        dc = self._verify_dc(rule_slice, overrides)
        outcome = self._compute_outcome(
            total,
            dc,
            raw_chosen_for_crit if raw_chosen_for_crit is not None else total,
            sides=20 if raw_chosen_for_crit is not None else 0,
        )

        raw_rolls = tuple(
            v for term in instruction.terms for v in term_results.get(term.term_id, ())
        )

        return ResolvedAdjudicationRecord(
            check_label=instruction.display_label,
            visibility=(
                RollVisibility.PLAYER
                if source == "player"
                else (
                    RollVisibility.HIDDEN
                    if source == "hidden"
                    else RollVisibility.SHOWN
                )
            ),
            expression=instruction.display_expression,
            raw_rolls=raw_rolls,
            modifiers_json=json.dumps(
                {
                    "visible_total": sum(
                        m.value
                        for m in instruction.modifier_components
                        if m.visibility is ModifierVisibility.PLAYER_VISIBLE
                    ),
                    "breakdown": {
                        m.label: m.value for m in instruction.modifier_components
                    },
                },
                sort_keys=True,
            ),
            total=total,
            dc=dc,
            outcome=outcome,
            sheet_effects=(),
            source=source,
            gm_cheating_at_roll=gm_cheating,
        )

    def resolve_aggregate_snapshot(
        self,
        *,
        instruction: RollInstructionSnapshot,
        reported_aggregate: int,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        gm_cheating: bool,
    ) -> ResolvedAdjudicationRecord:
        """Resolve a physical aggregate-only report: the total is authoritative.

        CRD Issue 15b (15b-15). Per-die crit recognition is unavailable
        without raw values — ``ActionResolutionService`` records
        ``raw_values_complete=False`` for this path rather than fabricating
        dice. Caller must range-validate ``reported_aggregate`` first.
        """
        dc = self._verify_dc(rule_slice, overrides)
        outcome = self._compute_outcome(
            reported_aggregate, dc, reported_aggregate, sides=0
        )
        return ResolvedAdjudicationRecord(
            check_label=instruction.display_label,
            visibility=RollVisibility.PLAYER,
            expression=instruction.display_expression,
            raw_rolls=(),
            modifiers_json=json.dumps(
                {
                    "visible_total": sum(
                        m.value for m in instruction.modifier_components
                    ),
                    "breakdown": {
                        m.label: m.value for m in instruction.modifier_components
                    },
                },
                sort_keys=True,
            ),
            total=reported_aggregate,
            dc=dc,
            outcome=outcome,
            sheet_effects=(),
            source="player",
            gm_cheating_at_roll=gm_cheating,
        )

    def aggregate_range(self, instruction: RollInstructionSnapshot) -> tuple[int, int]:
        """Return the legal (min, max) aggregate total for a RollInstructionSnapshot.

        Used to range-validate a physical aggregate-only report before
        resolution — the structured successor to the retired
        ``chosen_die_range`` (now handles arbitrary multi-term instructions,
        not just a single chosen die).

        Computed from each term's authoritative selection semantics, not raw
        dice count (Codex review, PR #129): ``SUM_ALL`` contributes every
        rolled die; ``KEEP_HIGHEST``/``KEEP_LOWEST`` contribute only
        ``keep_count`` dice regardless of how many were rolled — e.g.
        ``2d20kh1``'s legal range is ``[1, 20]``, not ``[2, 40]`` (rolling
        all 1s or all 20s and keeping one still yields 1 or 20; ADR-015b's
        own defect inventory item 2 flags exactly this shape of bug in the
        retired executor). ``SUBTRACT`` reverses which extreme becomes the
        term's min/max contribution.
        """
        modifier_total = sum(m.value for m in instruction.modifier_components)
        min_total = modifier_total
        max_total = modifier_total
        for term in instruction.terms:
            kept = (
                term.count
                if term.selection_rule is DiceSelectionRule.SUM_ALL
                else (term.keep_count or 1)
            )
            term_min = kept * 1
            term_max = kept * term.sides
            if term.contribution is RollContribution.SUBTRACT:
                term_min, term_max = -term_max, -term_min
            min_total += term_min
            max_total += term_max
        return min_total, max_total

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
