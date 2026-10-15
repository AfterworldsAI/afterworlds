"""CRD Issue 15b, ADR-015b Group 17: generic two-participant contests.

The accepted C9 authority with the Owner-adopted S1 supplement applied in
memory only (``s1_index``; nothing is activated in any store). Every number
is derived in code; the GameMaster selects identities only.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.ingestion.mechanical.representation import CreatureSkillsFact
from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    CreatureState,
    DeathState,
    HitPoints,
    SubjectReference,
    TurnCoordination,
    ZeroHitPointTreatment,
)
from afterworlds.models.enums import DiceHandling, RollPurpose, RollVisibility
from afterworlds.models.rpg import DiceResult, RollProposal
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state.coordination import StoredCoordination
from afterworlds.services.dnd5e_state.store import StoredCreature
from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnCreature
from tests.pipeline.rpg.test_adjudication_service import (
    _STORY_ID,
    _TURN_ID,
    _FakeProvider,
    _make_assembled,
    _make_session,
)
from tests.rpg_characters import srd_character
from tests.services.dnd5e_state.builders import (
    committed_inputs_for,
    complete_character,
    index_for,
    real_index,
    s1_entry,
    s1_index,
)

APE, WOLF, BAT = "animals.ape", "animals.wolf", "animals.bat"


def _creature(template: str, index: Any = None) -> TurnCreature:
    index = index or s1_index()
    stored = StoredCreature(
        creature_id=uuid4(),
        story_id=_STORY_ID,
        display_name=template,
        revision=1,
        binding=index.binding,
        state=CreatureState(
            template_record_key=template,
            hit_points=HitPoints(current=20, maximum=20, temporary=0),
            conditions=(),
            active_effects=(),
            death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
            zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster"),
        ),
    )
    return TurnCreature(stored, (), (), index)


def _wizard(index: Any = None) -> TurnCharacter:
    """Wizard 3, Str 8 (-1), Dex 14 (+2), no Athletics or Acrobatics."""
    return srd_character(index=index or s1_index())


def _ref(subject: Any) -> dict[str, str]:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return {"kind": kind, "subject_id": str(subject.subject_id)}


def _contest(
    initiator: Any,
    resister: Any,
    *,
    i: tuple[str, str | None] = ("strength", "athletics"),
    r: tuple[str, str | None] = ("strength", "athletics"),
    perceived: bool = True,
    hidden_resister: bool = False,
    hidden_initiator: bool = False,
    visibility: RollVisibility = RollVisibility.SHOWN,
) -> RollProposal:
    return RollProposal.model_validate(
        {
            "check_label": "Arm wrestling",
            "subsystem_tag": "contest",
            "visibility": visibility.value,
            "operation": "contest",
            "contest": {
                "initiator": {
                    "subject": _ref(initiator),
                    "ability": i[0],
                    "skill": i[1],
                    "roll_hidden": hidden_initiator,
                },
                "resister": {
                    "subject": _ref(resister),
                    "ability": r[0],
                    "skill": r[1],
                    "roll_hidden": hidden_resister,
                },
                "stakes": "the ring on the floor",
                "counterpart_perceived": perceived,
            },
        }
    )


def _dice(*faces: int) -> MagicMock:
    queue = list(faces)
    dice = MagicMock()

    def roll(expression: str) -> DiceResult:
        face = queue.pop(0)
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    dice.roll.side_effect = roll
    return dice


def _resolve(
    actor: TurnCharacter, other: Any, proposal: RollProposal, *faces: int
) -> Any:
    subjects = (
        {} if other is actor else {(_ref(other)["kind"], str(other.subject_id)): other}
    )
    return D20RulesSystemAdapter().resolve_roll(
        proposal, actor, None, _dice(*faces), False, subjects
    )


def _refused(
    kind: RefusalKind, actor: TurnCharacter, other: Any, proposal: RollProposal
) -> str:
    dice = MagicMock()
    subjects = {(_ref(other)["kind"], str(other.subject_id)): other}
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().resolve_roll(
            proposal, actor, None, dice, False, subjects
        )
    dice.roll.assert_not_called()
    assert caught.value.kind is kind, caught.value
    return caught.value.detail


def _sides(record: Any) -> dict[str, Any]:
    provenance = json.loads(record.modifiers_json)
    return provenance  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Comparison: the higher total wins; a tie preserves the prior situation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("wizard_face", "ape_face", "result", "winner"),
    [
        (19, 5, "win", "wizard"),  # 18 against 10
        (5, 15, "win", "ape"),  # 4 against 20
        (16, 10, "tie", None),  # 15 against 15: nobody wins
    ],
    ids=["initiator-wins", "resister-wins", "tie"],
)
def test_a_contest_compares_the_two_authoritative_totals(
    wizard_face: int, ape_face: int, result: str, winner: str | None
) -> None:
    wizard, ape = _wizard(), _creature(APE)
    record = _resolve(wizard, ape, _contest(wizard, ape), wizard_face, ape_face)
    provenance = _sides(record)
    # The wizard: Str -1, no Athletics. The Ape's printed Athletics +5 is
    # its complete bonus: its Strength +3 and Proficiency are not added again.
    assert provenance["initiator"]["modifier"] == -1
    assert provenance["resister"]["modifier"] == 5
    assert provenance["resister"]["breakdown"] == {"athletics_printed": 5}
    resolution = record.contest_resolution
    assert resolution is not None and resolution.result == result
    totals = [p.total for p in resolution.participants]
    assert totals == [wizard_face - 1, ape_face + 5]
    expected = {"wizard": wizard.subject_id, "ape": ape.subject_id, None: None}[winner]
    assert (resolution.winner.subject_id if resolution.winner else None) == expected
    # A contest applies nothing: no effect, no target number, no outcome.
    assert record.sheet_effects == () and record.dc is None
    assert record.outcome == "undetermined"


def test_athletics_against_acrobatics_between_two_characters() -> None:
    wizard = _wizard()
    # Fighter 1: no Tactical Mind (an unexecuted check contributor from 2nd).
    rival = srd_character(
        complete_character(s1_index(), "classes.fighter", 1), index=s1_index()
    )
    record = _resolve(
        wizard,
        rival,
        _contest(wizard, rival, r=("dexterity", "acrobatics")),
        10,
        10,
    )
    provenance = _sides(record)
    assert provenance["resister"]["ability"] == "dexterity"
    assert provenance["resister"]["skill"] == "acrobatics"
    assert record.contest_resolution is not None


def test_a_plain_ability_contest_uses_each_ability_modifier() -> None:
    wizard, wolf = _wizard(), _creature(WOLF)
    record = _resolve(
        wizard,
        wolf,
        _contest(wizard, wolf, i=("strength", None), r=("strength", None)),
        10,
        10,
    )
    provenance = _sides(record)
    assert provenance["initiator"]["modifier"] == -1
    assert provenance["resister"]["modifier"] == 2  # the Wolf's Str 14


def test_an_unlisted_skill_and_an_empty_list_use_the_ability_modifier() -> None:
    wizard = _wizard()
    for creature, expected in ((_creature(WOLF), 2), (_creature(BAT), None)):
        record = _resolve(wizard, creature, _contest(wizard, creature), 10, 10)
        modifier = _sides(record)["resister"]["modifier"]
        rows = _sides(record)["resister"]["breakdown"]
        assert list(rows) == ["strength_modifier"]
        if expected is not None:
            assert modifier == expected


# ---------------------------------------------------------------------------
# Refusals before any die (Group 17 "Refusals")
# ---------------------------------------------------------------------------


def test_a_missing_supplement_refuses_as_missing_authority() -> None:
    wizard, ape = _wizard(real_index()), _creature(APE, real_index())
    _refused(RefusalKind.MISSING_AUTHORITY, wizard, ape, _contest(wizard, ape))


def test_a_changed_supplement_refuses_as_incompatible_certification() -> None:
    inputs = committed_inputs_for(
        "1299484e-c72d-509b-bd8d-d0169ee1f8d2", "5.2.1-corpus.8781d4e0-a3b"
    )
    assert inputs is not None
    changed = index_for(
        inputs, (s1_entry(authored_prose="A tie goes to the initiator."),)
    )
    wizard, ape = _wizard(changed), _creature(APE, changed)
    _refused(RefusalKind.INCOMPATIBLE_CERTIFICATION, wizard, ape, _contest(wizard, ape))


def test_a_listed_skill_with_an_atypical_ability_refuses() -> None:
    """The Ape's Athletics +5 is Strength's; Dexterity (Athletics) is not
    established by the printed total."""
    wizard, ape = _wizard(), _creature(APE)
    detail = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        wizard,
        ape,
        _contest(wizard, ape, r=("dexterity", "athletics")),
    )
    assert "printed total" in detail


@pytest.mark.parametrize(
    "check",
    [("strength", "athletics"), ("strength", None), ("dexterity", "stealth")],
    ids=["listed-skill", "no-skill", "unlisted-skill"],
)
def test_a_missing_creature_skills_fact_refuses_as_missing_authority(
    check: tuple[str, str | None],
) -> None:
    """Without the (complete) Skills fact no skill's absence is established
    either: a plain ability check refuses too, not only a listed skill."""
    index = s1_index()
    record = index.records[APE]
    components = tuple(
        dataclasses.replace(
            c,
            facts=tuple(
                f for f in c.facts if not isinstance(f.fact, CreatureSkillsFact)
            ),
        )
        for c in record.components
    )
    records = dict(index.records)
    records[APE] = dataclasses.replace(record, components=components)
    without = dataclasses.replace(index, records=records)
    wizard, ape = _wizard(), _creature(APE, without)
    _refused(RefusalKind.MISSING_AUTHORITY, wizard, ape, _contest(wizard, ape, r=check))


def test_an_unexecuted_contributor_refuses() -> None:
    """A character holding a check contributor (Bard's Jack of All Trades)."""
    bard = srd_character(
        complete_character(s1_index(), "classes.bard", 3), index=s1_index()
    )
    ape = _creature(APE)
    _refused(RefusalKind.UNSUPPORTED_CAPABILITY, bard, ape, _contest(bard, ape))


def test_participants_are_distinct_and_skills_follow_their_ability() -> None:
    wizard, ape = _wizard(), _creature(APE)
    _refused(RefusalKind.INVALID_SELECTION, wizard, ape, _contest(wizard, wizard))
    _refused(
        RefusalKind.INVALID_SELECTION,
        wizard,
        ape,
        _contest(wizard, ape, i=("dexterity", "athletics")),
    )


def test_an_unperceived_counterpart_must_be_rolled_hidden() -> None:
    wizard, ape = _wizard(), _creature(APE)
    _refused(
        RefusalKind.INVALID_SELECTION,
        wizard,
        ape,
        _contest(wizard, ape, perceived=False, hidden_resister=False),
    )


# ---------------------------------------------------------------------------
# What the Writer may know
# ---------------------------------------------------------------------------


def test_a_perceived_hidden_counterpart_shows_only_its_result() -> None:
    wizard, ape = _wizard(), _creature(APE)
    record = _resolve(wizard, ape, _contest(wizard, ape, hidden_resister=True), 19, 5)
    view = D20RulesSystemAdapter().to_writer_view(record)
    assert (
        "contest" in view.player_facing_summary and "won" in view.player_facing_summary
    )
    assert "10" not in view.player_facing_summary  # the Ape's total stays hidden


@pytest.mark.parametrize("role", ["initiator", "resister"])
@pytest.mark.parametrize("whole", [False, True], ids=["roll-hidden", "whole-hidden"])
def test_the_acting_characters_own_check_is_never_hidden(
    role: str, whole: bool
) -> None:
    """In either role, neither its own roll nor the whole contest is hidden
    from the acting character: it refuses before any die."""
    wizard, ape = _wizard(), _creature(APE)
    if role == "initiator":
        proposal = _contest(wizard, ape, hidden_initiator=not whole)
    else:
        proposal = _contest(ape, wizard, hidden_resister=not whole)
    if whole:
        proposal = proposal.model_copy(update={"visibility": RollVisibility.HIDDEN})
    _refused(RefusalKind.INVALID_SELECTION, wizard, ape, proposal)


def _between(
    hidden_initiator: bool, visibility: RollVisibility = RollVisibility.SHOWN
) -> tuple[Any, Any, Any]:
    """The Ape (initiator) against the Wolf: the acting wizard watches."""
    wizard, ape, wolf = _wizard(), _creature(APE), _creature(WOLF)
    proposal = _contest(
        ape, wolf, hidden_initiator=hidden_initiator, visibility=visibility
    )
    subjects = {("creature", str(c.subject_id)): c for c in (ape, wolf)}
    record = D20RulesSystemAdapter().resolve_roll(
        proposal, wizard, None, _dice(19, 3), False, subjects
    )
    return record, D20RulesSystemAdapter().to_writer_view(record), proposal


def test_a_nonparticipant_sees_the_initiators_side_only_when_it_is_shown() -> None:
    record, view, _ = _between(hidden_initiator=False)
    assert view.total == 24 and "against 5" in view.player_facing_summary
    record, view, _ = _between(hidden_initiator=True)
    # The Ape's hidden 24 (19 + Athletics 5) and the bound the Wolf's shown
    # total would give it stay out; the result alone is told.
    assert view.total is None
    assert "24" not in view.player_facing_summary
    assert "against" not in view.player_facing_summary
    assert view.player_facing_summary.endswith("won")
    assert record.total == 24  # the backend audit keeps it


def test_a_whole_hidden_contest_between_others_tells_the_writer_nothing() -> None:
    _, view, _ = _between(hidden_initiator=False, visibility=RollVisibility.HIDDEN)
    assert view.total is None and view.check_label == ""
    assert view.player_facing_summary == "The scene continues."


def test_an_unperceived_counterpart_reads_as_an_ordinary_check() -> None:
    wizard, ape = _wizard(), _creature(APE)
    proposal = _contest(wizard, ape, perceived=False, hidden_resister=True)
    record = _resolve(wizard, ape, proposal, 5, 15)
    view = D20RulesSystemAdapter().to_writer_view(record)
    assert view.check_label == "Strength (Athletics) check"
    assert view.outcome == "failure"
    public = view.model_dump_json().lower()
    assert "contest" not in public and "ape" not in public and "20" not in public


# ---------------------------------------------------------------------------
# Action accounting (accepted Group 17 Action cost)
# ---------------------------------------------------------------------------


def _service(subject: Any, active: Any | None) -> RpgAdjudicationPassService:
    document = TurnCoordination()
    if active is not None:
        kind = "creature" if isinstance(active, TurnCreature) else "character"
        me = SubjectReference(kind=kind, subject_id=active.subject_id)
        document = TurnCoordination(
            active=ActiveTurn(subject=me, instance=1), next_instance=2
        )
    return RpgAdjudicationPassService(
        adapter=D20RulesSystemAdapter(),
        subject_loader=lambda _story, _ref: subject,
        coordination_loader=lambda _story: StoredCoordination(_STORY_ID, 1, document),
    )


def _turn(
    wizard: TurnCharacter,
    service: RpgAdjudicationPassService,
    proposal: Any,
    sequences: bool = True,
) -> Any:
    return service.adjudicate(
        _make_assembled(),
        _make_session(DiceHandling.AI_ROLLS),
        wizard,
        _Dice(10, 10),
        provider=_FakeProvider([proposal.model_dump(mode="json", exclude_none=True)]),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
        sequences=sequences,
    )


class _Dice:
    """Plain backend dice (a type with ``roll`` only)."""

    def __init__(self, *faces: int) -> None:
        self._faces = list(faces)

    def roll(self, expression: str) -> DiceResult:
        face = self._faces.pop(0)
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)


def test_an_active_turn_initiator_spends_its_action_and_the_resister_nothing() -> None:
    wizard, ape = _wizard(), _creature(APE)
    result = _turn(wizard, _service(ape, wizard), _contest(wizard, ape))
    (record,) = result.proposals
    assert [u.key for u in record.turn_uses] == ["glossary.action/action"]
    assert record.turn_uses[0].by.subject_id == wizard.subject_id


def test_an_all_backend_contest_carries_its_completed_event_ledger() -> None:
    """ADR-015b Group 17: with no player-rolled participant both dice are
    drawn in the originating turn, and the result still carries both
    participants' roll steps (the backend's) and the one combined resolution
    the completing step and the record share, for the delivered Turn to
    persist and audit from."""
    wizard, ape = _wizard(), _creature(APE)
    result = _turn(wizard, _service(ape, wizard), _contest(wizard, ape))
    (record,) = result.proposals
    done = result.completed_sequence
    assert done is not None and result.sequence is None
    first, second = (step.roll for step in done.steps)
    assert first is not None and second is not None
    assert [first.kind.value, second.kind.value] == ["ai_roll", "ai_roll"]
    assert first.contest_resolution is None
    assert second.contest_resolution == record.contest_resolution
    steps = [p.step_id for p in record.contest_resolution.participants]
    assert steps == [first.snapshot.step_id, second.snapshot.step_id]
    assert done.records == (record,)


def test_an_unwired_pass_refuses_a_contest_before_any_die() -> None:
    """Without the event ledger (no action-resolution service) a contest
    would run a weaker contract: it refuses before any die instead."""
    wizard, ape = _wizard(), _creature(APE)
    dice = _Dice()
    with pytest.raises(AdjudicationRefusal) as caught:
        wizard_service = _service(ape, wizard)
        wizard_service.adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            dice,
            provider=_FakeProvider(
                [_contest(wizard, ape).model_dump(mode="json", exclude_none=True)]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
        )
    assert caught.value.kind is RefusalKind.UNSUPPORTED_CAPABILITY
    assert "event ledger" in caught.value.detail


def test_no_use_is_recorded_outside_an_active_turn() -> None:
    wizard, ape = _wizard(), _creature(APE)
    (record,) = _turn(wizard, _service(ape, None), _contest(wizard, ape)).proposals
    assert record.turn_uses == ()


def test_an_off_turn_initiator_refuses_before_any_die() -> None:
    wizard, ape = _wizard(), _creature(APE)
    with pytest.raises(AdjudicationRefusal) as caught:
        _turn(wizard, _service(ape, ape), _contest(wizard, ape))
    assert caught.value.kind is RefusalKind.INVALID_SELECTION
    assert "Reaction" in caught.value.detail


def test_a_used_action_refuses_the_contest() -> None:
    wizard, ape = _wizard(), _creature(APE)
    service = _service(ape, wizard)
    with pytest.raises(AdjudicationRefusal) as caught:
        service.adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            wizard,
            _Dice(10, 10, 10, 10),
            provider=_FakeProvider(
                [
                    _contest(wizard, ape).model_dump(mode="json", exclude_none=True),
                    _contest(wizard, ape).model_dump(mode="json", exclude_none=True),
                ]
            ),
            story_id=_STORY_ID,
            originating_turn_id=_TURN_ID,
            sequences=True,
        )
    assert "already used" in caught.value.detail


def test_the_hidden_counterpart_purpose_is_an_ordinary_check() -> None:
    """The acting character's instruction for an unperceived opposition is an
    ordinary skill check (Group 17), not CONTESTED."""
    from afterworlds.pipeline.rpg import contests

    wizard, ape = _wizard(), _creature(APE)
    proposal = _contest(wizard, ape, perceived=False, hidden_resister=True)
    prepared = contests.prepare(
        proposal, wizard, {("creature", str(ape.subject_id)): ape}
    )
    seen: list[Any] = []

    class Recording:
        def roll(self, expression: str) -> DiceResult:
            return DiceResult(expression=expression, raw_rolls=(10,), chosen=10)

        def roll_described(self, expression: str, request: Any) -> DiceResult:
            seen.append(request)
            return self.roll(expression)

    contests.roll(prepared, Recording(), proposal, False)
    mine, theirs = seen
    assert mine.purpose is RollPurpose.SKILL_CHECK and mine.label.endswith("check")
    assert mine.counterpart is not None  # the counterpart is frozen with it
    assert theirs.purpose is RollPurpose.CONTESTED and theirs.hidden
