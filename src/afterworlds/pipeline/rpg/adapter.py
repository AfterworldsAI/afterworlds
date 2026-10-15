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
- Player-rolled dice (CRD Issue 15b): the same operations run whoever rolls.
  Each die is a described request (:func:`.dice.request`); an
  action-resolution sequence decides whether the Sojourner or the backend
  rolls it and persists it as a structured instruction. The legacy
  total-only announce/consume methods and their label-based assembler are
  retired (ADR-015b Group 9).
- ``gm_cheating=off`` is enforced at record creation time: the record is the
  immutable source of truth; Writer prose cannot change it.
- Roll-authorship is code-enforced: the adapter, not the model, produces
  DiceResult and total values.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Literal

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.dnd5e_state import TurnCoordination
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    ResolvedAdjudicationRecord,
    RollProposal,
    SheetEffect,
    TurnEdge,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg import (
    attacks,
    checks,
    contests,
    creature_attacks,
    creature_effects,
    creature_types,
    familiars,
    lifecycle,
    mastery,
)
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.services.dnd5e_state.turn import TurnCreature

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

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
    familiars.require_present(subject)
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
    Operation.CREATURE_SPECIES.value: "Species noted",
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


if TYPE_CHECKING:
    from afterworlds.models.rules_package import ActiveRuleSlice
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnSubject


def context_hash(character: TurnCharacter) -> str:
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
        if proposal.operation == Operation.CREATURE_SPECIES.value:
            creature_types.prepare_species(proposal, subjects or {})
            return
        if proposal.operation == Operation.CONTEST.value:
            contests.prepare(proposal, character, subjects or {})
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
            named = (
                *(sel.hostiles_within_5_feet or ()),
                *(sel.allies_within_5_feet_of_target or ()),
                *(sel.auras_in_range or ()),
            )
            return {
                (sel.attacker.kind, str(sel.attacker.subject_id)),
                (sel.target.kind, str(sel.target.subject_id)),
                *((r.kind, str(r.subject_id)) for r in named),
            }
        area = proposal.creature_save_effect
        if area is not None:
            return {(area.source.kind, str(area.source.subject_id))} | {
                (r.kind, str(r.subject_id))
                for r in (
                    *area.targets,
                    *(area.auras_in_range or ()),
                    *(area.enemies_in_area or ()),
                )
            }
        return set()

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
        exact binding. A ``PLAYER`` proposal resolves like a shown one: who
        rolls each die is the dice source's concern (CRD Issue 15b).
        """
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
        if proposal.operation == Operation.CONTEST.value:
            return contests.roll(
                contests.prepare(proposal, character, subjects or {}),
                dice_service,
                proposal,
                gm_cheating,
            )
        if proposal.operation == Operation.CREATURE_SPECIES.value:
            recorded, provenance = creature_types.record_species(
                creature_types.prepare_species(proposal, subjects or {})
            )
            return ResolvedAdjudicationRecord(
                check_label=proposal.check_label,
                visibility=proposal.visibility,
                expression="",
                raw_rolls=(),
                modifiers_json=provenance,
                total=0,
                outcome="undetermined",
                sheet_effects=(recorded,),
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
        rolled = checks.roll(
            checks.prepare(proposal, character),
            dice_service,
            ("character", str(character.subject_id)),
        )
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

    def to_writer_view(
        self, record: ResolvedAdjudicationRecord
    ) -> WriterAdjudicationView:
        """Produce a visibility-filtered WriterAdjudicationView from a record.

        For HIDDEN rolls: total, dc, and outcome are None.
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

        if record.contest_resolution is not None:
            return contests.writer_view(record)
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
