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

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import TurnCoordination
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    SheetEffect,
    TurnEdge,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg import (
    attacks,
    checks,
    creature_attacks,
    creature_effects,
    lifecycle,
    mastery,
)
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.dice import chosen_die_range
from afterworlds.services.dnd5e_state.turn import TurnCreature

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

# Word-boundary patterns so "disadvantage" doesn't trigger the advantage branch.
_ADV_RE = re.compile(r"\badvantage\b", re.IGNORECASE)
_DISADV_RE = re.compile(r"\bdisadvantage\b", re.IGNORECASE)


_EDGES = (Operation.BEGIN_TURN.value, Operation.END_TURN.value)
_ATTESTATIONS = (Operation.STABLE_RECOVERY.value, Operation.KNOCKOUT_RECOVERY.value)
#: Operations whose validity turns on a subject's zero-HP lifecycle state.
_LIFECYCLE = (Operation.STABILIZE.value, *_ATTESTATIONS)


def _edge_subject(
    proposal: RollProposal,
    character: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> TurnSubject:
    """The subject an actor-turn edge names, read for this turn, and the
    edge operation certified under its binding."""
    ref = proposal.subject
    if ref is None:
        raise AdjudicationRefusal(
            RefusalKind.INVALID_SELECTION, f"{proposal.operation} names no subject"
        )
    key = (ref.kind, str(ref.subject_id))
    subject = (
        character
        if key == ("character", str(character.subject_id))
        else subjects.get(key)
    )
    if subject is None or subject.index is None:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE, f"{ref.kind} {ref.subject_id} was not read"
        )
    certify(Operation(proposal.operation or ""), subject.index)
    return subject


def _title(key: str) -> str:
    return key.rsplit(".", 1)[-1].replace("_", " ").capitalize()


#: The public name of each operation that names nothing more specific.
_OPERATION_LABELS = {
    Operation.BEGIN_TURN.value: "Turn begins",
    Operation.END_TURN.value: "Turn ends",
    Operation.INITIATIVE.value: "Initiative",
    Operation.STABLE_RECOVERY.value: "Recovery",
    Operation.KNOCKOUT_RECOVERY.value: "Recovery",
    Operation.DEATH_SAVING_THROW.value: "Death saving throw",
}


def public_label(record: ResolvedAdjudicationRecord) -> str:
    """A visibility-safe label for the Writer, derived in code from the
    record's operation and its admitted identities (CRD Issue 15c).

    The GameMaster's ``check_label`` is free text written after seeing hidden
    state, so it stays backend-only (the audit row): a public label never
    carries it.
    """
    provenance = json.loads(record.modifiers_json)
    operation = provenance.get("operation", "")
    if operation in _OPERATION_LABELS:
        return _OPERATION_LABELS[operation]
    if operation == Operation.WEAPON_ATTACK.value:
        return f"{_title(provenance.get('weapon', 'weapon'))} attack"
    if operation in (
        Operation.CREATURE_ATTACK.value,
        Operation.CREATURE_SAVE_EFFECT.value,
    ):
        return str(provenance.get("entry", "Attack"))
    if provenance.get("first_aid"):
        return "First aid"
    skill, ability = provenance.get("skill"), provenance.get("ability")
    if skill:
        return f"{_title(str(ability))} ({_title(str(skill))}) check"
    if ability:
        return f"{_title(str(ability))} check"
    return "Check"


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
    from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnSubject


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
        self,
        proposal: RollProposal,
        character: TurnCharacter,
        subjects: dict[tuple[str, str], TurnSubject] | None = None,
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
        if proposal.operation == Operation.WEAPON_ATTACK.value:
            attacks.prepare(proposal, character, subjects or {})
            return
        if proposal.operation in _EDGES:
            subject = _edge_subject(proposal, character, subjects or {})
            # The preflight view carries every condition earlier operations
            # could apply: an Unconscious subject may be dying by the time its
            # turn begins, so its death save is checked now.
            unconscious = any(
                c.condition is ConditionKind.UNCONSCIOUS
                for c in subject.stored.state.conditions or ()
            )
            if proposal.operation == Operation.BEGIN_TURN.value and (
                lifecycle.dying(subject) or unconscious
            ):
                lifecycle.prepare(subject)
            return
        if proposal.operation == Operation.CREATURE_ATTACK.value:
            creature_attacks.prepare(proposal, character, subjects or {})
            return
        if proposal.operation == Operation.CREATURE_SAVE_EFFECT.value:
            creature_effects.prepare(proposal, character, subjects or {})
            return
        if proposal.operation == Operation.STABILIZE.value:
            lifecycle.prepare_first_aid(proposal, character, subjects or {})
            return
        if proposal.operation in _ATTESTATIONS:
            lifecycle.attest(proposal, character, subjects or {})
            return
        if proposal.operation == Operation.DEATH_SAVING_THROW.value:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                "a death save is made when a dying subject's turn begins "
                "(begin_turn), never named alone",
            )
        checks.prepare(proposal, character)

    def possible_conditions(
        self,
        proposal: RollProposal,
        _character: TurnCharacter,
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> dict[tuple[str, str], frozenset[ConditionKind]]:
        """Every condition *proposal* could apply, by subject, whatever its
        dice give: the preflight checks the turn's later operations with
        them present. Checks change no state."""
        if proposal.operation == Operation.WEAPON_ATTACK.value:
            return attacks.possible_conditions(proposal, subjects)
        if proposal.operation == Operation.CREATURE_ATTACK.value:
            return creature_attacks.possible_conditions(proposal, _character, subjects)
        if proposal.operation == Operation.CREATURE_SAVE_EFFECT.value:
            return creature_effects.possible_conditions(proposal, _character, subjects)
        if proposal.operation in (Operation.STABILIZE.value, *_ATTESTATIONS):
            # Ending a knockout's or a regained creature's Unconscious leaves
            # it Prone.
            ref = proposal.subject
            if ref is not None:
                return {
                    (ref.kind, str(ref.subject_id)): frozenset({ConditionKind.PRONE})
                }
        if proposal.operation == Operation.BEGIN_TURN.value:
            subject = _edge_subject(proposal, _character, subjects)
            if lifecycle.dying(subject):
                # A natural 20 ends Unconscious and leaves the subject Prone.
                return {attacks.subject_key(subject): frozenset({ConditionKind.PRONE})}
        return {}

    def not_triggered(
        self, proposal: RollProposal, gm_cheating: bool, what: str = "cleave"
    ) -> ResolvedAdjudicationRecord:
        """An extra attack when the attack before it did not hit (Cleave's,
        or a creature entry's follow-up): no die, no effect, and Cleave's
        once-per-turn use is not taken."""
        return ResolvedAdjudicationRecord(
            check_label=proposal.check_label,
            visibility=proposal.visibility,
            expression="",
            raw_rolls=(),
            modifiers_json=json.dumps(
                {"operation": proposal.operation, what: "not_triggered"}
            ),
            total=0,
            outcome="undetermined",
            sheet_effects=(),
            source=("hidden" if proposal.visibility is RollVisibility.HIDDEN else "ai"),
            gm_cheating_at_roll=gm_cheating,
        )

    def lifecycle_changes(self, proposal: RollProposal) -> set[tuple[str, str]]:
        """Subjects whose hit points, death state or recovery instances
        *proposal* could change, whatever its dice give."""
        sel = proposal.weapon_attack or proposal.creature_attack
        if sel is not None:
            return {(sel.target.kind, str(sel.target.subject_id))}
        if proposal.creature_save_effect is not None:
            return {
                (r.kind, str(r.subject_id))
                for r in proposal.creature_save_effect.targets
            }
        if proposal.operation in (*_EDGES, *_LIFECYCLE) and proposal.subject:
            ref = proposal.subject
            return {(ref.kind, str(ref.subject_id))}
        return set()

    def lifecycle_reads(self, proposal: RollProposal) -> set[tuple[str, str]]:
        """Subjects whose dying, knocked-out or recovery-instance state
        *proposal*'s validity turns on."""
        if proposal.operation in _LIFECYCLE and proposal.subject is not None:
            ref = proposal.subject
            return {(ref.kind, str(ref.subject_id))}
        return set()

    def savers(
        self,
        proposal: RollProposal,
        character: TurnCharacter,
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> list[tuple[str, str]]:
        """The subjects *proposal* could force to save: Topple's target, a
        creature hit effect's save target, a save effect's targets."""
        area = proposal.creature_save_effect
        if area is not None:
            return [(r.kind, str(r.subject_id)) for r in area.targets]
        attack = proposal.creature_attack
        if attack is not None:
            creature = subjects.get(
                (attack.attacker.kind, str(attack.attacker.subject_id))
            )
            if isinstance(creature, TurnCreature):
                try:
                    rider = creature_attacks._attack_fact(
                        creature, attack.entry
                    ).hit_effect
                except AdjudicationRefusal:
                    return []
                if rider is not None and rider.rider_save is not None:
                    return [(attack.target.kind, str(attack.target.subject_id))]
            return []
        weapon = proposal.weapon_attack
        if weapon is not None and weapon.mastery and attacks.topples(character, weapon):
            return [(weapon.target.kind, str(weapon.target.subject_id))]
        return []

    def moved_subjects(self, proposal: RollProposal) -> set[tuple[str, str]]:
        """Subjects *proposal* could move (Push)."""
        if proposal.operation == Operation.WEAPON_ATTACK.value:
            return attacks.moved_subjects(proposal)
        return set()

    def spatial_subjects(
        self, proposal: RollProposal, character: TurnCharacter
    ) -> set[tuple[str, str]]:
        """Subjects *proposal*'s spatial facts are about."""
        if proposal.operation == Operation.WEAPON_ATTACK.value:
            return attacks.spatial_subjects(proposal, character)
        sel = proposal.creature_attack
        if sel is not None:
            return {
                (sel.attacker.kind, str(sel.attacker.subject_id)),
                (sel.target.kind, str(sel.target.subject_id)),
            }
        area = proposal.creature_save_effect
        if area is not None:
            return {(area.source.kind, str(area.source.subject_id))} | {
                (r.kind, str(r.subject_id)) for r in area.targets
            }
        return set()

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
        subjects: dict[tuple[str, str], TurnSubject] | None = None,
        coordination: TurnCoordination | None = None,
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

        source: Literal["hidden", "ai"] = (
            "hidden" if proposal.visibility is RollVisibility.HIDDEN else "ai"
        )
        if proposal.operation in _EDGES:
            return self._resolve_edge(
                proposal,
                character,
                dice_service,
                gm_cheating,
                subjects or {},
                coordination,
            )
        if proposal.operation == Operation.CREATURE_ATTACK.value:
            struck = creature_attacks.roll(
                creature_attacks.prepare(proposal, character, subjects or {}),
                dice_service,
                coordination,
            )
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression=struck.prepared.expression,
                raw_rolls=struck.raw_rolls,
                modifiers_json=struck.provenance_json(),
                total=struck.total,
                dc=struck.prepared.target_ac,
                outcome=(
                    "critical_success"
                    if struck.critical
                    else "success" if struck.hit else "failure"
                ),
                sheet_effects=struck.effects,
                source=source,
                gm_cheating_at_roll=gm_cheating,
            )
        if proposal.operation == Operation.CREATURE_SAVE_EFFECT.value:
            effect = creature_effects.roll(
                creature_effects.prepare(proposal, character, subjects or {}),
                dice_service,
                coordination,
            )
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression="",
                raw_rolls=(),
                modifiers_json=effect.provenance_json(),
                total=0,
                outcome="undetermined",
                sheet_effects=effect.effects,
                source=source,
                gm_cheating_at_roll=gm_cheating,
            )
        if proposal.operation == Operation.STABILIZE.value:
            aid = lifecycle.roll_first_aid(
                lifecycle.prepare_first_aid(proposal, character, subjects or {}),
                dice_service,
            )
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression=aid.prepared.check.expression,
                raw_rolls=aid.rolled.raw_rolls,
                modifiers_json=aid.provenance_json(),
                total=aid.rolled.total,
                dc=aid.prepared.check.dc,
                outcome="success" if aid.rolled.outcome == "success" else "failure",
                sheet_effects=aid.effects,
                source=source,
                gm_cheating_at_roll=gm_cheating,
            )
        if proposal.operation in _ATTESTATIONS:
            attested = lifecycle.attest(proposal, character, subjects or {})
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression="",
                raw_rolls=(),
                modifiers_json=attested.provenance_json(proposal),
                total=0,
                outcome="undetermined",
                sheet_effects=attested.effects,
                source=source,
                gm_cheating_at_roll=gm_cheating,
            )
        if proposal.operation == Operation.WEAPON_ATTACK.value:
            attack = attacks.roll(
                attacks.prepare(proposal, character, subjects or {}),
                dice_service,
                character,
                coordination,
            )
            attack_outcomes: dict[str, _Outcome] = {
                "success": "success",
                "failure": "failure",
                "critical_success": "critical_success",
            }
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression=attack.prepared.expression,
                raw_rolls=attack.raw_rolls,
                modifiers_json=attack.provenance_json(),
                total=attack.total,
                dc=attack.prepared.target_ac,
                outcome=attack_outcomes[attack.outcome],
                sheet_effects=attack.effects,
                source=source,
                gm_cheating_at_roll=gm_cheating,
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

    def _resolve_edge(
        self,
        proposal: RollProposal,
        character: TurnCharacter,
        dice_service: DiceService,
        gm_cheating: bool,
        subjects: dict[tuple[str, str], TurnSubject],
        coordination: TurnCoordination | None,
    ) -> ResolvedAdjudicationRecord:
        """An actor-turn edge; a dying subject's turn begins with its death
        save (contract G1). Every turn-bounded mastery effect this edge ends,
        on any subject the turn read, ends with it (contract G2). The
        coordination transition itself is validated and threaded by the
        service."""
        subject = _edge_subject(proposal, character, subjects)
        kind: Literal["begin", "end"] = (
            "begin" if proposal.operation == Operation.BEGIN_TURN.value else "end"
        )
        assert proposal.subject is not None
        edge = TurnEdge(kind=kind, subject=proposal.subject)
        source: Literal["hidden", "ai"] = (
            "hidden" if proposal.visibility is RollVisibility.HIDDEN else "ai"
        )
        ref = mastery.reference(subject)
        active = coordination.active if coordination is not None else None
        instance = active.instance if active is not None else 0
        expired: tuple[SheetEffect, ...] = tuple(
            e
            for holder in (character, *subjects.values())
            for e in mastery.expiring(holder, kind, ref, instance)
        )
        recharges: list[dict[str, object]] = []
        if kind == "begin" and isinstance(subject, TurnCreature):
            recharged, recharges = creature_effects.recharge(subject, dice_service)
            expired = (*expired, *recharged)
        if kind == "begin" and lifecycle.dying(subject):
            saved = lifecycle.roll(lifecycle.prepare(subject), dice_service)
            outcomes: dict[str, _Outcome] = {
                "regained_hit_points": "critical_success",
                "stable": "success",
                "success": "success",
                "died": "failure",
                "failure": "failure",
            }
            outcome = outcomes[saved.outcome]
            if saved.chosen == 1:
                outcome = "critical_failure"
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression=saved.prepared.expression,
                raw_rolls=saved.raw_rolls,
                modifiers_json=saved.provenance_json(),
                total=saved.chosen,
                dc=saved.prepared.rule.success_minimum,
                outcome=outcome,
                sheet_effects=(*expired, *saved.effects),
                source=source,
                gm_cheating_at_roll=gm_cheating,
                turn_edge=edge,
            )
        return ResolvedAdjudicationRecord(
            check_label=proposal.check_label,
            visibility=proposal.visibility,
            expression="",
            raw_rolls=(),
            modifiers_json=json.dumps(
                {
                    "operation": proposal.operation,
                    "subject": proposal.subject.model_dump(mode="json"),
                    "recharge": recharges,
                },
                sort_keys=True,
            ),
            total=0,
            outcome="undetermined",
            sheet_effects=expired,
            source=source,
            gm_cheating_at_roll=gm_cheating,
            turn_edge=edge,
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

        if not record.expression:  # an edge or attestation: no roll, no number
            return WriterAdjudicationView(
                check_label=public_label(record),
                visibility=record.visibility,
                player_facing_summary=public_label(record),
                total=None,
                dc=None,
                outcome=None,
            )
        # A weapon attack's comparison target is the target's Armor Class: the
        # target's state, not the actor's, so the Writer gets the outcome only.
        target_state = json.loads(record.modifiers_json).get("operation") in (
            Operation.WEAPON_ATTACK.value,
            Operation.CREATURE_ATTACK.value,
        )
        dc = None if target_state else record.dc
        label = public_label(record)
        summary_parts = [f"{label}: rolled {record.total}"]
        if dc is not None:
            summary_parts.append(f"vs DC {dc}")
        if record.outcome not in (None, "undetermined"):
            summary_parts.append(f"— {record.outcome.replace('_', ' ')}")

        return WriterAdjudicationView(
            check_label=label,
            visibility=record.visibility,
            player_facing_summary=", ".join(summary_parts),
            total=record.total,
            dc=dc,
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
