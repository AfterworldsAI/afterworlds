"""A fall's damage and Prone, recorded by Sojourn (issue #211, ADR-015).

Movement adjudication rolls a fall on the dice rails (``movement._fall``) and
the mapper only saves where the mover ended. What the fall does to the mover
is Sojourn's: this module turns the rolled fall into one resolved record,
whose audit row and sheet effects the Turn writes atomically with the
delivered Turn, like any other roll (Fork B1). It reads the rules through the
mover's authority (``damage.take_damage``) and writes nothing itself.
"""

from __future__ import annotations

import json

from afterworlds.ingestion.mechanical.representation import (
    ApplicabilityKind,
    ConditionKind,
    DamageOutcome,
    DamageType,
)
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.models.rpg import (
    ResolvedAdjudicationRecord,
    SheetEffect,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.damage import take_damage
from afterworlds.pipeline.rpg.defense import condition_immune
from afterworlds.pipeline.rpg.ids import new_id
from afterworlds.pipeline.rpg.movement import FallRoll
from afterworlds.services.dnd5e_state.turn import TurnCharacter

#: Damage outcomes after which nothing lands Prone.
_DEAD = frozenset({"died", "died_massive_damage", "died_by_attack", "already_dead"})

#: The sheet fields a fall's damage sets; another record of the same Turn
#: setting one would be overwritten, so the Turn refuses that pairing.
HIT_POINT_TARGETS = frozenset({"current_hp", "temporary_hp", "death_state"})


def fall_record(
    fall: FallRoll, mover: TurnCharacter, *, gm_cheating: bool
) -> tuple[ResolvedAdjudicationRecord, WriterAdjudicationView]:
    """The fall's record and Writer view for *mover*, or a typed refusal
    (``AdjudicationRefusal``) when its authority can't settle the damage."""
    effects: list[SheetEffect] = []
    damage: dict[str, object] | None = None
    outcome = "none"
    taken = 0
    if fall.total > 0:
        result = take_damage(mover, fall.total, DamageType.BLUDGEONING, critical=False)
        effects.extend(result.effects)
        damage = result.provenance()
        outcome = result.outcome
        taken = result.taken
    prone = "not_applicable"
    if fall.prone:
        if not _prone_needs_damage(mover):
            raise AdjudicationRefusal(
                RefusalKind.MISSING_AUTHORITY,
                "glossary.falling › prone_on_landing: not Prone on any damage",
            )
        if taken == 0:
            # "lands Prone unless it avoids taking any damage from the fall"
            prone = "no_damage"
        elif outcome in _DEAD:
            prone = "dead"
        elif condition_immune(mover, ConditionKind.PRONE):
            prone = "immune"
        elif any(
            c.condition is ConditionKind.PRONE
            for c in mover.stored.state.conditions or ()
        ):
            prone = "already_prone"
        else:
            prone = "applied"
            effects.append(
                SheetEffect(
                    target="prone",
                    operation="apply_condition",
                    value_json=json.dumps(
                        {
                            "instance_id": new_id(),
                            "condition": ConditionKind.PRONE.value,
                            "visibility": ConditionVisibility.VISIBLE.value,
                            "source": {
                                "record_key": "glossary.falling",
                                "component_key": "prone_on_landing",
                            },
                        }
                    ),
                    subject_kind="character",
                    subject_id=mover.sheet_id,
                )
            )
    label = f"Falling {fall.depth_ft} ft"
    record = ResolvedAdjudicationRecord(
        check_label=label,
        visibility=RollVisibility.SHOWN,
        expression=fall.expression,
        raw_rolls=fall.raw_rolls,
        modifiers_json=json.dumps(
            {
                "operation": "fall",
                "depth_ft": fall.depth_ft,
                "damage_type": DamageType.BLUDGEONING.value,
                "damage": damage,
                "prone": prone,
                "source_refs": ["glossary.falling"],
            },
            sort_keys=True,
        ),
        total=fall.total,
        outcome="undetermined",
        sheet_effects=tuple(effects),
        source="ai",
        gm_cheating_at_roll=gm_cheating,
    )
    return record, WriterAdjudicationView(
        check_label=label,
        visibility=RollVisibility.SHOWN,
        player_facing_summary=_summary(fall, damage, outcome, prone),
        total=fall.total,
    )


def _prone_needs_damage(mover: TurnCharacter) -> bool:
    """Whether the mover's authority lands it Prone on any damage from the
    fall: ``prone_on_landing`` applies on the ``any_damage`` outcome."""
    index = mover.index
    record = index.record("glossary.falling") if index is not None else None
    if record is None:
        return False
    whens = [
        c.applies_when
        for c in record.components
        if c.semantic_key == "prone_on_landing"
    ]
    return (
        len(whens) == 1
        and whens[0] is not None
        and whens[0].kind is ApplicabilityKind.DAMAGE_OUTCOME
        and whens[0].damage_outcome is DamageOutcome.ANY_DAMAGE
        and not whens[0].negated
    )


def _summary(
    fall: FallRoll, damage: dict[str, object] | None, outcome: str, prone: str
) -> str:
    parts = [f"Fell {fall.depth_ft} ft"]
    if damage is not None:
        parts.append(f"took {damage['taken']} bludgeoning damage")
        follows = {
            "unconscious_and_dying": "dropped to 0 Hit Points, Unconscious",
            "death_save_failure": "already at 0 Hit Points, failed a death save",
            "died": "died",
            "died_massive_damage": "died",
            "already_dead": "was already dead",
        }.get(outcome)
        if follows is not None:
            parts.append(follows)
    if prone == "applied":
        parts.append("landed Prone")
    return ", ".join(parts) + "."
