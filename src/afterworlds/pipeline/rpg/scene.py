"""The mechanical scene the GameMaster selects identities from — CRD Issue 15c.

The adjudication pass names subjects, held weapons, attack entries and
recovery instances by id; :func:`render` lists the ones that exist, so every
id a proposal can name is one code put in front of the GameMaster. It is a
GameMaster-only block of the adjudication request, after the shared stable
prefix (which it never changes), and is never given to the Writer.

It carries identities and the state selection needs (hit points, the
zero-HP lifecycle, conditions, the active turn); never a DC, an AC, a
modifier or a rolled recovery interval. Hidden conditions are listed and
labelled: hidden state is backend-visible (ADR-015 Decision 5) and the
adjudication pass is backend.
"""

from __future__ import annotations

import json

from afterworlds.ingestion.mechanical.representation import (
    CreatureAttackFact,
    CreatureSaveEffectFact,
)
from afterworlds.models.dnd5e_state import TurnCoordination
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = ["render"]


def _subject(subject: TurnSubject, acting: bool) -> dict[str, object]:
    state = subject.stored.state
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    out: dict[str, object] = {"kind": kind, "subject_id": str(subject.subject_id)}
    if isinstance(subject, TurnCreature):
        out["name"] = subject.stored.display_name
        out["template"] = state.template_record_key  # type: ignore[union-attr]
        if subject.index is not None:
            facts = facts_of(subject.index, out["template"])  # type: ignore[arg-type]
            out["attack_entries"] = sorted(
                f.entry for f in facts if isinstance(f, CreatureAttackFact)
            )
            out["save_effect_entries"] = sorted(
                f.entry for f in facts if isinstance(f, CreatureSaveEffectFact)
            )
            out["spent_uses"] = sorted(
                c.counter_id.rsplit("/", 1)[-1]
                for c in state.usage_counters or ()
                if c.expended
            )
    else:
        out["name"] = subject.stored.character_name
        out["acting"] = acting
        out["weapons"] = [
            {"item_id": str(i.item_id), "record": i.record_key, "wielded": i.equipped}
            for i in subject.items
            if i.record_key.startswith("equipment.weapons.")
        ]
    hp = state.hit_points
    if hp is not None:
        out["hit_points"] = {
            "current": hp.current,
            "maximum": hp.maximum,
            "temporary": hp.temporary,
        }
    death = state.death_state
    if death is not None:
        out["zero_hp"] = (
            "dead"
            if death.dead
            else (
                "stable"
                if death.stable
                else "dying" if hp is not None and hp.current == 0 else None
            )
        )
        if death.stable_recovery is not None:
            out["stable_recovery_instance_id"] = death.stable_recovery.instance_id
    out["conditions"] = [
        {
            "instance_id": c.instance_id,
            "condition": c.condition.value,
            "visibility": c.visibility.value,
            "source": (
                f"{c.source.record_key}/{c.source.component_key or '-'}"
                if c.source is not None
                else None
            ),
        }
        for c in state.conditions or ()
    ]
    return out


def render(
    actor: TurnCharacter,
    others: list[TurnSubject],
    coordination: TurnCoordination | None,
) -> str:
    """The GameMaster-only scene block: subjects (the acting character first),
    and whose turn is active."""
    active = coordination.active if coordination is not None else None
    scene = {
        "subjects": [_subject(actor, True)]
        + [
            _subject(s, False)
            for s in others
            if not (isinstance(s, TurnCharacter) and s.subject_id == actor.subject_id)
        ],
        "active_turn": (
            {
                "kind": active.subject.kind,
                "subject_id": str(active.subject.subject_id),
            }
            if active is not None
            else None
        ),
    }
    return (
        "Mechanical scene (GameMaster only; name ids only from here):\n"
        + json.dumps(scene, sort_keys=True)
    )
