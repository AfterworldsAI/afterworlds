"""Bounded d20 Rules System Adapter — CRD Issues 15, 2b and 15c.

This is a hand-authored, bounded d20 adapter.  It covers modifier assembly,
code-verified DC lookup, degree-of-success calculation, advantage/disadvantage,
roll-authorship invariant enforcement, and sheet-effect derivation.

Boundaries:
- d20-specific concepts (DC, AC, proficiency, saving throws, ability scores,
  advantage/disadvantage) live HERE, not in generic adjudication code.
- Backend (shown/hidden) rolls run only through the CRD Issue 15c capability
  manifest: :meth:`require_supported` and :meth:`resolve_roll` validate the
  proposal's roster operation and admitted identity, certify the operation
  against the character's exact binding (:mod:`.capability`) and derive every
  number from typed authority (:mod:`.checks`). Anything else refuses with a
  typed :class:`~afterworlds.pipeline.rpg.capability.AdjudicationRefusal`; no
  backend roll resolves ``undetermined``.
- Player-rolled dice are not 15c's: the adjudication service refuses them
  before any pending request exists. The label-based assembler below survives
  only for the legacy announce/consume methods, whose retirement belongs to
  CRD Issue 15b (ADR-015b Group 9).
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
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    SheetEffect,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg import checks
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.dice import chosen_die_range

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

# Word-boundary patterns so "disadvantage" doesn't trigger the advantage branch.
_ADV_RE = re.compile(r"\badvantage\b", re.IGNORECASE)
_DISADV_RE = re.compile(r"\bdisadvantage\b", re.IGNORECASE)


def _normalize_skill_key(value: str) -> str:
    """Normalize a label to lowercase underscore form for comparison.

    Strips leading/trailing whitespace, collapses repeated internal whitespace
    and hyphens to underscores, and lowercases, so "Dexterity Check" and
    "dexterity_check" compare equal.
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


_ABILITIES = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)
_PURE_CHECK_KIND = "ability_check"
_TAG_QUALIFIERS = frozenset({"advantage", "disadvantage"})


def _pure_ability_check(proposal: RollProposal) -> str:
    """The ability of a supported pure ability check, or a typed refusal.

    The supported shape is closed (CRD Issue 2b): the check kind is
    ``ability_check`` (optionally qualified by ``advantage``/``disadvantage``),
    the governing label is one ability, and the check label names that same
    ability and nothing else. Any other kind, label or combination - a skill,
    save, attack, tool, initiative, or a label that contradicts its kind - is
    proficiency-aware or unknown and is refused, never rolled ability-only.
    """
    kind, *qualifiers = proposal.subsystem_tag.lower().split() or [""]
    label = _normalize_skill_key(proposal.skill_or_attribute_label or "")
    check = _normalize_skill_key(proposal.check_label)
    ability = next((a for a in _ABILITIES if label in _ability_forms(a)), None)
    if (
        kind != _PURE_CHECK_KIND
        or not set(qualifiers) <= _TAG_QUALIFIERS
        or ability is None
        or check not in _ability_forms(ability)
    ):
        raise UnsupportedCheckError(
            f"{proposal.check_label!r} ({proposal.subsystem_tag!r}, "
            f"{proposal.skill_or_attribute_label!r}) is not a supported pure "
            "ability check; proficiency-aware and unrecognized checks are CRD "
            "Issue 15c's and are not rolled as ability-only checks"
        )
    return ability


def _ability_forms(ability: str) -> tuple[str, ...]:
    return (ability, f"{ability}_check", f"{ability}_ability_check")


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

    def require_supported(
        self, proposal: RollProposal, character: TurnCharacter
    ) -> None:
        """Raise a typed refusal unless *proposal* can run as a backend roll.

        Pure: no dice, pending roll or record. Callers check every proposal of
        a turn before any of them has an effect.
        """
        if proposal.visibility is RollVisibility.PLAYER:
            raise AdjudicationRefusal(
                RefusalKind.PLAYER_ROLL_UNSUPPORTED,
                "player-rolled dice are CRD Issue 15b/19b's; 15c resolves "
                "backend shown/hidden rolls only",
            )
        checks.prepare(proposal, character)

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
        ability = _pure_ability_check(proposal)
        state = character.stored.state
        if state.ability_scores is None:
            raise UnsupportedCheckError("the character records no ability scores")
        scores = state.ability_scores.model_dump()
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
        """Resolve a backend (shown or hidden) roll into an immutable record.

        The record carries the code-derived DC, outcome and full provenance
        (operation, identity, modifier breakdown, Advantage sources and the
        certificate). ``rule_slice`` is unused: authority is the character's
        exact binding. A PLAYER proposal raises ``ValueError``.
        """
        if proposal.visibility is RollVisibility.PLAYER:
            raise ValueError(
                "resolve_roll called on PLAYER visibility proposal; "
                "use prepare_player_roll_announce instead"
            )

        rolled = checks.roll(checks.prepare(proposal, character), dice_service)
        outcomes: dict[str, _Outcome] = {
            "success": "success",
            "failure": "failure",
            # Initiative: a total with no comparison (#191 AC5).
            "undetermined": "undetermined",
        }
        outcome = outcomes[rolled.outcome]

        return ResolvedAdjudicationRecord(
            check_label=proposal.check_label,
            visibility=proposal.visibility,
            expression=rolled.prepared.expression,
            raw_rolls=rolled.raw_rolls,
            modifiers_json=rolled.provenance_json(),
            total=rolled.total,
            dc=rolled.prepared.dc,
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
