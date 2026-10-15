"""Generic two-participant contests — CRD Issue 15b, ADR-015b Group 17.

The Owner adopted the SRD 5.1 contest procedure as the explicit supplement S1
(``play.d20_tests/contest``): both participants make a check, code compares
the authoritative totals, the higher total wins, and equal totals preserve the
situation that existed before the contest. A contest establishes a winner or
a tie and nothing else: no sheet, condition, damage, movement, attitude or
resource change. Specific SRD 5.2.1 mechanics (Hide/Search, Influence,
Grapple, Shove) keep their own operations.

* **Authority.** The operation is certified with S1's component in its
  governing set (:mod:`.capability`): a binding without S1 refuses as missing
  authority; one that changes it, as incompatible certification. Each
  participant is certified under its own binding.
* **A character's check** is the unchanged 15c check procedure
  (:func:`.checks.contest_check`), with no target.
* **A creature's check** reads its C9 printed Skills entry: a listed skill
  with its usual ability is the printed total, with nothing added (never the
  ability modifier, Proficiency Bonus or Expertise again); a listed skill with
  another ability refuses before any die (decomposing the total is not
  established); an unlisted skill under the complete list, or no skill, is
  the ability modifier; a profile with no Skills fact refuses as missing
  authority when a skill is named.
* **Order.** The acting character's participant rolls first. Both
  instructions are frozen when the contest is created; the other
  participant's dice are drawn only when the first result is accepted, so no
  opposing total exists while the player's roll is pending.
* **Visibility.** Each participant's roll is shown or hidden. When the
  acting character does not perceive the opposition, its own check is
  presented as an ordinary check and the Writer is told only whether the
  effort succeeded.
* **Action accounting** is :mod:`.economy`'s: the initiator's one action in an
  active turn, none outside one; the resisting check costs nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Literal
from uuid import UUID, uuid5

from afterworlds.ingestion.mechanical.representation import (
    SKILL_ABILITY,
    AbilityScore,
    CreatureAbilityScoreFact,
    CreatureRollModifierFact,
    CreatureSkillsFact,
    RecordKind,
    RollActor,
    RollContext,
    Skill,
)
from afterworlds.models.enums import RollPurpose, RollVisibility
from afterworlds.models.rpg import (
    ContestLinkage,
    ContestParticipant,
    ContestParticipantResult,
    ContestResolution,
    ContestSelection,
    ResolvedAdjudicationRecord,
    RollProposal,
    SubjectRef,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg import checks, ids
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
    certify_template,
)
from afterworlds.pipeline.rpg.defense import facts_of
from afterworlds.pipeline.rpg.defense import template as template_of
from afterworlds.pipeline.rpg.dice import DiceService, RollRequest, request
from afterworlds.pipeline.rpg.mastery import other_effects
from afterworlds.pipeline.rpg.models import ActionSequenceIntegrityError
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = [
    "PreparedContest",
    "PreparedParticipant",
    "compare",
    "prepare",
    "roll",
    "writer_view",
]


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _title(value: str) -> str:
    return value.replace("_", " ").capitalize()


@dataclass(frozen=True)
class PreparedParticipant:
    """One participant's check, every input fixed, no die rolled."""

    ref: SubjectRef
    subject: TurnSubject
    ability: AbilityScore
    skill: Skill | None
    modifier: int
    breakdown: dict[str, int]
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    certificate: Certificate
    roll_hidden: bool
    templates: dict[str, str] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        if adv and not dis:
            return "2d20kh1"
        if dis and not adv:
            return "2d20kl1"
        return "1d20"

    @property
    def key(self) -> tuple[str, str]:
        return self.ref.kind, str(self.ref.subject_id)

    def label(self, noun: str) -> str:
        skill = f" ({_title(self.skill.value)})" if self.skill else ""
        return f"{_title(self.ability.value)}{skill} {noun}"


@dataclass(frozen=True)
class PreparedContest:
    selection: ContestSelection
    initiator: PreparedParticipant
    resister: PreparedParticipant
    #: The acting character's participant, if it is one (its view of the
    #: contest is what the player and the Writer see).
    actor: Literal["initiator", "resister"] | None
    certificate: Certificate


def _member[E: (AbilityScore, Skill)](vocabulary: type[E], value: str) -> E:
    try:
        return vocabulary(value)
    except ValueError:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{value!r} is not a {vocabulary.__name__}"
        ) from None


def _subject(
    ref: SubjectRef,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> TurnSubject:
    if ref.kind == "character" and ref.subject_id == actor.subject_id:
        return actor
    found = subjects.get((ref.kind, str(ref.subject_id)))
    if found is None or found.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"{ref.kind} {ref.subject_id} was not read"
        )
    return found


def _creature(
    creature: TurnCreature,
    ability: AbilityScore,
    skill: Skill | None,
    certificate: Certificate,
    participant: ContestParticipant,
) -> PreparedParticipant:
    """A creature's check from its printed abilities and C9 Skills entry."""
    index = creature.index
    assert index is not None
    template = template_of(creature)
    digest = certify_template(index, template)
    unexecuted = other_effects(creature)
    if unexecuted:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"active effect {unexecuted[0].source.record_key} can change this check "
            "and is not executable here",
        )
    for item in creature.items:
        if index.kind(item.record_key) is RecordKind.MAGIC_ITEM and (
            item.equipped or item.attuned_subject_id
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"magic item {item.record_key} is not executable here",
            )
    facts = facts_of(index, template)
    for fact in facts:
        if isinstance(fact, CreatureRollModifierFact) and any(
            e.roll.actor is RollActor.SUBJECT
            and e.roll.context in (RollContext.ABILITY_CHECK, RollContext.D20_TEST)
            for e in fact.effects
        ):
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{template}/{fact.entry} can change this check and is not "
                "executable here",
            )
    rows = [
        f
        for f in facts
        if isinstance(f, CreatureAbilityScoreFact) and f.ability is ability
    ]
    if len(rows) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{template} prints no single {ability.value} ability row",
        )
    row = rows[0]
    ability_modifier = (
        row.modifier if row.modifier is not None else (row.score - 10) // 2
    )
    modifier = ability_modifier
    breakdown = {f"{ability.value}_modifier": ability_modifier}
    # Group 17: a profile without its (complete) Skills fact refuses as missing
    # authority, whatever the check names: without it, no skill's absence is
    # established either.
    listed = [f for f in facts if isinstance(f, CreatureSkillsFact)]
    if len(listed) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{template} records no single Skills entry (C9) for this check",
        )
    if skill is not None:
        entry = next((s for s in listed[0].skills if s.skill is skill), None)
        if entry is not None:
            if entry.ability is not ability:
                raise _refuse(
                    RefusalKind.UNSUPPORTED_CAPABILITY,
                    f"{template} prints {skill.value} for {entry.ability.value}; "
                    f"its {ability.value} use is not established by the printed total",
                )
            # The printed total is the complete bonus: nothing is added.
            modifier = entry.bonus
            breakdown = {f"{skill.value}_printed": entry.bonus}
    advantage, disadvantage = checks._advantage(  # noqa: SLF001
        creature,  # type: ignore[arg-type]
        index,
        ability,
        skill,
    )
    return PreparedParticipant(
        ref=participant.subject,
        subject=creature,
        ability=ability,
        skill=skill,
        modifier=modifier,
        breakdown=breakdown,
        advantage_sources=advantage,
        disadvantage_sources=disadvantage,
        certificate=certificate,
        roll_hidden=participant.roll_hidden,
        templates={f"creature:{creature.subject_id}": digest},
    )


def _participant(
    participant: ContestParticipant,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedParticipant:
    subject = _subject(participant.subject, actor, subjects)
    assert subject.index is not None
    certificate = certify(Operation.CONTEST, subject.index)
    ability = _member(AbilityScore, participant.ability)
    skill = _member(Skill, participant.skill) if participant.skill else None
    if isinstance(subject, TurnCreature):
        return _creature(subject, ability, skill, certificate, participant)
    if skill is not None and SKILL_ABILITY[skill] is not ability:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{skill.value} is governed by {SKILL_ABILITY[skill].value}, not "
            f"{ability.value}",
        )
    check = checks.contest_check(subject, ability, skill, certificate)
    return PreparedParticipant(
        ref=participant.subject,
        subject=subject,
        ability=ability,
        skill=skill,
        modifier=check.modifier,
        breakdown=check.breakdown,
        advantage_sources=check.advantage_sources,
        disadvantage_sources=check.disadvantage_sources,
        certificate=certificate,
        roll_hidden=participant.roll_hidden,
    )


def prepare(
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> PreparedContest:
    """Validate a ``contest`` and derive both checks, or refuse (typed)."""
    sel = proposal.contest
    if sel is None:
        raise _refuse(RefusalKind.INVALID_SELECTION, "a contest names its participants")
    if actor.index is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, "the acting character's authority")
    certificate = certify(Operation.CONTEST, actor.index)
    if sel.initiator.subject == sel.resister.subject:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, "a contest has two distinct participants"
        )
    me = SubjectRef(kind="character", subject_id=actor.subject_id)
    side: Literal["initiator", "resister"] | None = (
        "initiator"
        if sel.initiator.subject == me
        else "resister" if sel.resister.subject == me else None
    )
    if not sel.counterpart_perceived:
        if side is None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "whether the opposition is perceived is the acting character's, "
                "who is not a participant",
            )
        other = sel.resister if side == "initiator" else sel.initiator
        if not other.roll_hidden:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "an unperceived counterpart's roll is hidden",
            )
    own = {"initiator": sel.initiator, "resister": sel.resister}.get(side or "")
    if side is not None and (
        proposal.visibility is RollVisibility.HIDDEN
        or (own is not None and own.roll_hidden)
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "the acting character's own check in a contest is not hidden from "
            "them; hide the counterpart's roll instead",
        )
    return PreparedContest(
        selection=sel,
        initiator=_participant(sel.initiator, actor, subjects),
        resister=_participant(sel.resister, actor, subjects),
        actor=side,
        certificate=certificate,
    )


def compare(
    contest_id: UUID,
    first: tuple[SubjectRef, UUID, int],
    second: tuple[SubjectRef, UUID, int],
    certificate: dict[str, str],
) -> ContestResolution:
    """S1's comparison, computed once: the higher total wins; equal totals
    are a tie with no winner (the prior situation is unchanged)."""
    a = ContestParticipantResult(subject=first[0], step_id=first[1], total=first[2])
    b = ContestParticipantResult(subject=second[0], step_id=second[1], total=second[2])
    if a.total == b.total:
        return ContestResolution(
            contest_id=contest_id,
            participants=(a, b),
            result="tie",
            winner=None,
            certificate=certificate,
        )
    return ContestResolution(
        contest_id=contest_id,
        participants=(a, b),
        result="win",
        winner=(a if a.total > b.total else b).subject,
        certificate=certificate,
    )


def _request(
    contest: PreparedContest,
    mine: PreparedParticipant,
    other: PreparedParticipant,
    contest_id: UUID,
    actor_side: bool,
) -> RollRequest:
    perceived = contest.selection.counterpart_perceived
    ordinary = actor_side and not perceived
    purpose = (
        (RollPurpose.SKILL_CHECK if mine.skill else RollPurpose.ABILITY_CHECK)
        if ordinary
        else RollPurpose.CONTESTED
    )
    return RollRequest(
        purpose=purpose,
        roller=mine.key,
        label=mine.label("check" if ordinary else "contest"),
        modifiers=tuple(
            (_title(k), v, Operation.CONTEST.value) for k, v in mine.breakdown.items()
        ),
        source_refs=("play.d20_tests/contest",),
        contest=ContestLinkage(
            contest_id=contest_id,
            participant=mine.ref,
            counterpart=other.ref,
            counterpart_perceived=perceived,
            certificate=mine.certificate.as_json(),
        ),
        hidden=mine.roll_hidden,
    )


def roll(
    contest: PreparedContest,
    dice: DiceService,
    proposal: RollProposal,
    gm_cheating: bool,
) -> ResolvedAdjudicationRecord:
    """Both checks, the acting character's first, then the comparison.

    The first request carries the second's, so a sequence freezes both
    instructions when the contest is created; the second's dice are drawn
    only after the first result is accepted."""
    contest_id = ids.new_uuid()
    first, second = (
        (contest.resister, contest.initiator)
        if contest.actor == "resister"
        else (contest.initiator, contest.resister)
    )
    first_request = _request(
        contest, first, second, contest_id, contest.actor is not None
    )
    second_request = _request(contest, second, first, contest_id, False)
    first_dice = request(
        dice,
        first.expression,
        replace(first_request, counterpart=(second.expression, second_request)),
    )
    second_dice = request(dice, second.expression, second_request)
    first_total = first_dice.chosen + first.modifier
    second_total = second_dice.chosen + second.modifier
    resolution = compare(
        contest_id,
        (first.ref, uuid5(contest_id, "first"), first_total),
        (second.ref, uuid5(contest_id, "second"), second_total),
        contest.certificate.as_json(),
    )
    # In an action-resolution sequence the combined resolution is the one on
    # the contest-completing event, identified by the participants' actual
    # steps: the record reuses it, never a second, competing one. Outside a
    # sequence (every die the backend's) the record's own is the only one.
    sequenced = _sequenced(dice, contest_id)
    if sequenced is not None:
        if (
            sequenced.result,
            sequenced.winner,
            [(r.subject, r.total) for r in sequenced.participants],
        ) != (
            resolution.result,
            resolution.winner,
            [(r.subject, r.total) for r in resolution.participants],
        ):
            raise ActionSequenceIntegrityError(
                f"contest {contest_id}'s recorded resolution is not reproduced"
            )
        resolution = sequenced
    rolled = {
        first.key: (first_total, first_dice.raw_rolls),
        second.key: (second_total, second_dice.raw_rolls),
    }

    def side(p: PreparedParticipant) -> dict[str, object]:
        total, raw = rolled[p.key]
        return {
            "subject": p.ref.model_dump(mode="json"),
            "ability": p.ability.value,
            "skill": p.skill.value if p.skill else None,
            "modifier": p.modifier,
            "breakdown": p.breakdown,
            "advantage_sources": list(p.advantage_sources),
            "disadvantage_sources": list(p.disadvantage_sources),
            "raw_rolls": list(raw),
            "total": total,
            "roll_hidden": p.roll_hidden,
            "certificate": p.certificate.as_json(),
            "templates": p.templates,
        }

    provenance = {
        "operation": Operation.CONTEST.value,
        "stakes": contest.selection.stakes,
        "counterpart_perceived": contest.selection.counterpart_perceived,
        "actor": contest.actor,
        "initiator": side(contest.initiator),
        "resister": side(contest.resister),
        "result": resolution.result,
        "winner": (
            resolution.winner.model_dump(mode="json") if resolution.winner else None
        ),
        "certificate": contest.certificate.as_json(),
    }
    # The record is the first participant's view: the acting character's,
    # else the initiator's.
    total, raw = rolled[first.key]
    return ResolvedAdjudicationRecord(
        check_label=proposal.check_label,
        visibility=proposal.visibility,
        expression=first.expression,
        raw_rolls=tuple(raw),
        modifiers_json=json.dumps(provenance, sort_keys=True),
        total=total,
        dc=None,
        outcome="undetermined",
        sheet_effects=(),
        source="hidden" if proposal.visibility is RollVisibility.HIDDEN else "ai",
        gm_cheating_at_roll=gm_cheating,
        contest_resolution=resolution,
    )


def _sequenced(dice: DiceService, contest_id: UUID) -> ContestResolution | None:
    method = getattr(type(dice), "contest_resolution", None)
    if method is None:
        return None
    found: ContestResolution | None = method(dice, contest_id)
    return found


def writer_view(record: ResolvedAdjudicationRecord) -> WriterAdjudicationView:
    """What the Writer may know of a contest, from the acting character's
    side (the initiator's when it is not a participant): its own total, the
    counterpart's only when shown, and the result. An unperceived counterpart
    is never disclosed: the check reads as an effort that succeeded or not.
    A tie is the prior situation unchanged."""
    provenance = json.loads(record.modifiers_json)
    me_role = provenance["actor"] or "initiator"
    other_role = "resister" if me_role == "initiator" else "initiator"
    me, other = provenance[me_role], provenance[other_role]
    skill = f" ({_title(me['skill'])})" if me["skill"] else ""
    name = f"{_title(me['ability'])}{skill}"
    won = provenance["winner"] == me["subject"]
    result = provenance["result"]
    # A participant's numbers reach the Writer only when its roll is shown.
    mine = None if me["roll_hidden"] else me["total"]
    rolled = "" if mine is None else f": rolled {mine}"
    if not provenance["counterpart_perceived"]:
        # The acting character's own check (never hidden from it), read as an
        # ordinary effort: no counterpart, no comparison, no tie.
        outcome: Literal["success", "failure"] = "success" if won else "failure"
        return WriterAdjudicationView(
            check_label=f"{name} check",
            visibility=record.visibility,
            player_facing_summary=f"{name} check{rolled} — {outcome}",
            total=mine,
            outcome=outcome,
        )
    against = "" if other["roll_hidden"] else f" against {other['total']}"
    if mine is None:
        against = ""
    if result == "tie":
        what = "a tie: the situation is unchanged"
    else:
        what = "won" if won else "lost"
    return WriterAdjudicationView(
        check_label=f"{name} contest",
        visibility=record.visibility,
        player_facing_summary=f"{name} contest{rolled}{against} — {what}",
        total=mine,
    )
