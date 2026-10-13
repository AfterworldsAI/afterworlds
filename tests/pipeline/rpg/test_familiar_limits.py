"""CRD Issue 15c (codex-c8-execution-review) — a familiar's source limits hold
before any die, on every path that could reach them.

Find Familiar: "A familiar can't attack"; at 0 Hit Points it disappears,
leaving what it carried; it can be dismissed to a pocket dimension. C8 types
a familiar but executes none of that, so attacks by it, anything naming an
absent one, damage to it and its zero-HP operations refuse. Ordinary
creatures are unaffected (the existing suites).
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from afterworlds.models.dnd5e_state import (
    CreaturePresence,
    GrantSource,
    SummonOrigin,
)
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.models.rpg import LifecycleAttestation
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_actor_turns import _dying
from tests.pipeline.rpg.test_creature_attacks import _bite, _medium_wizard
from tests.pipeline.rpg.test_creature_effects import _breath, _edge, _wyrmling
from tests.pipeline.rpg.test_weapon_attacks import CLUB, _attacker, _creature, _proposal
from tests.pipeline.rpg.test_zero_hp_lifecycle import _op, _stable

FAMILIAR = SummonOrigin(source=GrantSource(record_key="spells.find_familiar"))


def _familiar(
    base: TurnCreature | None = None,
    presence: CreaturePresence | None = CreaturePresence.PRESENT,
) -> TurnCreature:
    cat = base if base is not None else _creature("animals.cat", hp=1)
    state = cat.stored.state.model_copy(
        update={
            "summon": FAMILIAR,
            "creature_type": CreatureType.FEY,
            "presence": presence,
        }
    )
    return dataclasses.replace(cat, stored=dataclasses.replace(cat.stored, state=state))


def _refused(
    proposal: Any, actor: Any, *creatures: TurnCreature
) -> AdjudicationRefusal:
    subjects = {("creature", str(c.subject_id)): c for c in creatures}
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(proposal, actor, subjects)
    return caught.value


def test_a_familiar_cannot_attack() -> None:
    cat, wizard = _familiar(), _medium_wizard()
    refusal = _refused(
        _bite(cat, wizard, entry="Scratch", target_within_5_feet=True), wizard, cat
    )
    assert refusal.kind is RefusalKind.INVALID_SELECTION
    assert "can't attack" in refusal.detail


@pytest.mark.parametrize(
    ("presence", "kind"),
    [
        (None, RefusalKind.MISSING_STATE),
        (CreaturePresence.POCKET_DIMENSION, RefusalKind.INVALID_SELECTION),
        (CreaturePresence.GONE, RefusalKind.INVALID_SELECTION),
    ],
)
def test_an_absent_or_unrecorded_familiar_is_not_a_target(
    presence: CreaturePresence | None, kind: RefusalKind
) -> None:
    ghoul, cat = _creature("monsters.ghoul.ghoul", hp=40), _familiar(presence=presence)
    proposal = _bite(ghoul, cat, entry="Claw", target_within_5_feet=True)
    assert _refused(proposal, _medium_wizard(), ghoul, cat).kind is kind


def test_damage_to_a_present_familiar_is_held_on_every_damage_path() -> None:
    cat = _familiar()
    ghoul = _creature("monsters.ghoul.ghoul", hp=40)
    claw = _refused(
        _bite(ghoul, cat, entry="Claw", target_within_5_feet=True),
        _medium_wizard(),
        ghoul,
        cat,
    )
    club = _refused(_proposal(cat), _attacker(CLUB), cat)
    dragon = _wyrmling()
    breath = _refused(_breath(dragon, cat), _medium_wizard(), dragon, cat)
    for refusal in (claw, club, breath):
        assert refusal.kind is RefusalKind.UNSUPPORTED_CAPABILITY, refusal
        assert "disappears" in refusal.detail


def test_a_familiars_zero_hp_operations_are_held() -> None:
    gone = _familiar(_dying(), CreaturePresence.GONE)
    present = _familiar(_dying())
    # First aid, a death save at its turn's start, a recovery attestation.
    first_aid = _refused(_op(present, "stabilize"), _attacker(), present)
    assert first_aid.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    begin = _refused(_edge(gone, "begin_turn"), _attacker(), gone)
    assert begin.kind is RefusalKind.INVALID_SELECTION  # it is not present
    death_save = _refused(_edge(present, "begin_turn"), _attacker(), present)
    assert death_save.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    stable = _familiar(_stable(), CreaturePresence.GONE)
    recovery = _refused(
        _op(
            stable,
            "stable_recovery",
            LifecycleAttestation(instance_id="rec", elapsed_hours=4),
        ),
        _attacker(),
        stable,
    )
    assert recovery.kind is RefusalKind.INVALID_SELECTION
