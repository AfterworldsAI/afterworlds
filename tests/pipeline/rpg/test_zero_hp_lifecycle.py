"""CRD Issue 15c — the rest of the zero-HP lifecycle: the knockout
alternative, first aid (the Help action), and the GameMaster's recovery
attestations (OD-15c-2), each from typed authority with code-held results."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest

from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    DeathState,
    GrantSource,
    HitPoints,
    StableRecovery,
)
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.models.rpg import LifecycleAttestation, RollProposal, SubjectRef
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_actor_turns import CHARACTER, _dying
from tests.pipeline.rpg.test_weapon_attacks import (
    CLUB,
    DAGGER,
    _attacker,
    _creature,
    _dice,
    _proposal,
    _run,
)

_KNOCKOUT = GrantSource(
    record_key="play.damage_and_healing", component_key="knocking_out"
)


def _with(creature: TurnCreature, **state: Any) -> TurnCreature:
    new = creature.stored.state.model_copy(update=state)
    return dataclasses.replace(
        creature, stored=dataclasses.replace(creature.stored, state=new)
    )


def _knocked_out() -> TurnCreature:
    return _with(
        _creature(hp=11, treatment=CHARACTER),
        hit_points=HitPoints(current=1, maximum=11, temporary=0),
        conditions=(
            ConditionInstance(
                instance_id="ko",
                condition="unconscious",  # type: ignore[arg-type]
                visibility=ConditionVisibility.VISIBLE,
                source=_KNOCKOUT,
            ),
        ),
    )


def _stable(interval: int = 3) -> TurnCreature:
    dying = _dying()
    return _with(
        dying,
        death_state=DeathState(
            successes=0,
            failures=0,
            stable=True,
            dead=False,
            stable_recovery=StableRecovery(
                instance_id="rec", interval=interval, unit="hour"  # type: ignore[arg-type]
            ),
        ),
    )


def _op(subject: TurnCreature, operation: str, attestation: Any = None) -> RollProposal:
    return RollProposal(
        check_label=operation,
        subsystem_tag="lifecycle",
        visibility=RollVisibility.SHOWN,
        operation=operation,
        subject=SubjectRef(kind="creature", subject_id=subject.subject_id),
        attestation=attestation,
    )


def _resolve(
    subject: TurnCreature, proposal: RollProposal, *dice: tuple[int, ...]
) -> Any:
    roller = _dice(*dice) if dice else _dice((10,))
    return (
        D20RulesSystemAdapter().resolve_roll(
            proposal,
            _attacker(),
            None,
            roller,
            gm_cheating=False,
            subjects={("creature", str(subject.subject_id)): subject},
        ),
        roller,
    )


def _refused(subject: TurnCreature, proposal: RollProposal) -> AdjudicationRefusal:
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            proposal, _attacker(), {("creature", str(subject.subject_id)): subject}
        )
    return caught.value


def _targets(record: Any) -> dict[str, Any]:
    return {e.target: json.loads(e.value_json) for e in record.sheet_effects}


# ---------------------------------------------------------------------------
# The knockout alternative
# ---------------------------------------------------------------------------


def test_a_melee_attack_can_knock_out_instead_of_reducing_to_0() -> None:
    wolf = _creature(hp=2)
    record = _run(
        _attacker(CLUB), wolf, _proposal(wolf, knock_out=True), _dice((15,), (3,))
    )
    effects = _targets(record)
    assert json.loads(record.modifiers_json)["damage"]["outcome"] == "knocked_out"
    assert effects["current_hp"] == 1
    assert effects["unconscious"]["source"]["component_key"] == "knocking_out"
    assert "death_state" not in effects


def test_only_a_melee_attack_knocks_out() -> None:
    wolf = _creature()
    proposal = _proposal(
        wolf,
        DAGGER,
        range="within_normal_range",
        thrown=True,
        hostiles_within_5_feet=(),
        ability="dexterity",
        knock_out=True,
    )
    with pytest.raises(AdjudicationRefusal) as caught:
        _run(_attacker(DAGGER), wolf, proposal, _dice((15,), (3,)))
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


# ---------------------------------------------------------------------------
# First aid
# ---------------------------------------------------------------------------


def test_first_aid_stabilizes_a_dying_creature_with_a_rolled_recovery() -> None:
    wolf = _dying()
    record, dice = _resolve(wolf, _op(wolf, "stabilize"), (15,), (2,))
    assert dice.calls == ["1d20", "1d4"]
    assert (record.dc, record.outcome) == (10, "success")
    after = DeathState.model_validate(_targets(record)["death_state"])
    assert after.stable and after.stable_recovery is not None
    assert after.stable_recovery.interval == 2


def test_failed_first_aid_changes_nothing() -> None:
    wolf = _dying()
    record, _ = _resolve(wolf, _op(wolf, "stabilize"), (2,))
    assert (record.outcome, record.sheet_effects) == ("failure", ())


def test_first_aid_ends_a_knockout_leaving_the_creature_prone() -> None:
    wolf = _knocked_out()
    record, _ = _resolve(wolf, _op(wolf, "stabilize"), (15,))
    effects = _targets(record)
    assert effects["unconscious"] == {"instance_id": "ko"}
    assert effects["prone"]["condition"] == "prone"


def test_first_aid_needs_a_dying_or_knocked_out_creature() -> None:
    wolf = _creature()
    assert _refused(wolf, _op(wolf, "stabilize")).kind is RefusalKind.INVALID_SELECTION


# ---------------------------------------------------------------------------
# Attestations (OD-15c-2)
# ---------------------------------------------------------------------------


def test_stable_recovery_waits_for_the_rolled_interval() -> None:
    wolf = _stable(interval=3)
    early = LifecycleAttestation(instance_id="rec", elapsed_hours=2)
    record, dice = _resolve(wolf, _op(wolf, "stable_recovery", early))
    assert (
        record.sheet_effects == ()
        and json.loads(record.modifiers_json)["result"] == "not_yet"
    )
    dice.roll.assert_not_called()

    due = LifecycleAttestation(instance_id="rec", elapsed_hours=3)
    record, _ = _resolve(wolf, _op(wolf, "stable_recovery", due))
    effects = _targets(record)
    assert effects["current_hp"] == 1
    assert DeathState.model_validate(effects["death_state"]).stable_recovery is None
    assert effects["unconscious"] == {"instance_id": "fell"}
    assert effects["prone"]["condition"] == "prone"


@pytest.mark.parametrize(
    "attestation",
    [
        LifecycleAttestation(instance_id="other", elapsed_hours=4),
        LifecycleAttestation(instance_id="rec"),
    ],
)
def test_a_stable_recovery_attestation_names_the_current_instance_and_hours(
    attestation: LifecycleAttestation,
) -> None:
    wolf = _stable()
    refusal = _refused(wolf, _op(wolf, "stable_recovery", attestation))
    assert refusal.kind is RefusalKind.INVALID_SELECTION


def test_a_completed_short_rest_ends_the_knockout_once() -> None:
    wolf = _knocked_out()
    record, _ = _resolve(
        wolf, _op(wolf, "knockout_recovery", LifecycleAttestation(instance_id="ko"))
    )
    assert _targets(record)["unconscious"] == {"instance_id": "ko"}
    for attestation in (
        LifecycleAttestation(instance_id="fell"),
        LifecycleAttestation(instance_id="ko", elapsed_hours=1),
    ):
        refusal = _refused(wolf, _op(wolf, "knockout_recovery", attestation))
        assert refusal.kind is RefusalKind.INVALID_SELECTION


# ---------------------------------------------------------------------------
# Lifecycle state an earlier operation of the turn can change is not
# preflightable: such an operation refuses before any die (needs a later turn)
# ---------------------------------------------------------------------------


def _turn_of(
    subject: TurnCreature, *proposals: RollProposal, reason: str = "later turn"
) -> AdjudicationRefusal:
    from unittest.mock import MagicMock

    from afterworlds.models.enums import DiceHandling
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from tests.pipeline.rpg.test_adjudication_service import (
        _STORY_ID,
        _TURN_ID,
        _FakeProvider,
        _make_assembled,
        _make_session,
    )
    from tests.pipeline.rpg.test_turn_sequencing import actor_turn

    dice = MagicMock()
    actor = _attacker(CLUB)
    with pytest.raises(AdjudicationRefusal) as caught:
        RpgAdjudicationPassService(
            adapter=D20RulesSystemAdapter(),
            subject_loader=lambda _story, _ref: subject,
            coordination_loader=actor_turn(actor),
            bounded_loader=lambda _story, _ref: [],
        ).adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            actor,
            dice,
            provider=_FakeProvider(
                [p.model_dump(mode="json", exclude_none=True) for p in proposals]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    dice.roll.assert_not_called()
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert reason in caught.value.detail
    return caught.value


def test_an_attack_then_a_recovery_attestation_on_its_target_refuses() -> None:
    stable = _stable()
    _turn_of(
        stable,
        _proposal(stable, CLUB),
        _op(
            stable,
            "stable_recovery",
            LifecycleAttestation(instance_id="rec", elapsed_hours=4),
        ),
    )


def test_a_death_save_then_first_aid_on_the_same_subject_refuses() -> None:
    wolf = _dying()
    begin = RollProposal(
        check_label="Turn",
        subsystem_tag="turn",
        visibility=RollVisibility.SHOWN,
        operation="begin_turn",
        subject=SubjectRef(kind="creature", subject_id=wolf.subject_id),
    )
    # The dying subject's turn begins (its death save), so first aid, the
    # acting character's action, is not on its turn: refused before any die.
    _turn_of(wolf, begin, _op(wolf, "stabilize"), reason="still active")


def test_first_aid_then_the_knockouts_short_rest_refuses() -> None:
    wolf = _knocked_out()
    _turn_of(
        wolf,
        _op(wolf, "stabilize"),
        _op(wolf, "knockout_recovery", LifecycleAttestation(instance_id="ko")),
    )


def test_an_attack_then_first_aid_on_its_target_refuses() -> None:
    wolf = _creature(hp=2, treatment=CHARACTER)
    # Both need the turn's one action, which refuses first, before any die.
    _turn_of(wolf, _proposal(wolf, CLUB), _op(wolf, "stabilize"), reason="already used")


# ---------------------------------------------------------------------------
# CRD Issue 15b: the knockout is the Sojourner's stored decision
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("facts", "visibility", "detail"),
    [
        ({"knock_out": True}, RollVisibility.SHOWN, "never preselected"),
        ({}, RollVisibility.HIDDEN, "without revealing the hit"),
    ],
    ids=["preselected", "hidden-melee"],
)
def test_a_sequence_never_takes_the_knockout_decision_from_the_sojourner(
    facts: dict[str, Any], visibility: RollVisibility, detail: str
) -> None:
    """Where decisions can be offered (an action-resolution sequence), a
    GameMaster knockout preselection and a hidden melee attack (whose decision
    would reveal the hit) refuse before any die. Under unchanged wiring
    (``decisions=False``) the 15c preselection still stands."""
    from afterworlds.models.dnd5e_state import (
        ActiveTurn,
        SubjectReference,
        TurnCoordination,
    )
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.services.dnd5e_state.coordination import StoredCoordination
    from tests.pipeline.rpg.test_adjudication_service import _STORY_ID

    wolf, attacker = _creature(hp=2), _attacker(CLUB)
    mine = SubjectReference(kind="character", subject_id=attacker.subject_id)
    turn = TurnCoordination(
        active=ActiveTurn(subject=mine, instance=1), next_instance=2
    )
    proposal = _proposal(wolf, **facts).model_copy(update={"visibility": visibility})
    service = RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _s, _r: wolf,
        coordination_loader=lambda _s: StoredCoordination(_STORY_ID, 1, turn),
    )
    with pytest.raises(AdjudicationRefusal) as caught:
        service.prepare_turn(_STORY_ID, attacker, [proposal], decisions=True)
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert detail in caught.value.detail
    service.prepare_turn(_STORY_ID, attacker, [proposal], decisions=False)
