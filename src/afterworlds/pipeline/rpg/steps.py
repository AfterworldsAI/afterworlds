"""Action-resolution steps: the sequence dice source and its snapshots.

CRD Issue 15b. A turn's operations are resolved by the same 15c code whoever
rolls. :class:`SequenceDice` is the dice source an adjudicating turn and an
action-resolution sequence give that code. For each described die
(:func:`.dice.request`) it builds the structured
:class:`~afterworlds.models.rpg.RollInstructionSnapshot`, then:

* serves a die the sequence already accepted, after checking the instruction
  it rebuilds equals the stored one (a mismatch is an integrity failure,
  never a silent replacement);
* serves the Sojourner's validated submission for the pending die;
* pauses (:class:`~.models.PlayerInputRequired`) when the die is the acting
  character's to roll and the story's dice are player-rolled;
* otherwise rolls it with the backend dice service, as an AI or hidden step.

Result-triggered decisions (:func:`.dice.decide`) are served or paused the same
way. Identities are deterministic per sequence and operation
(:mod:`.ids`), so an operation computed again yields the same instruction,
decision options and effects.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from afterworlds.models.enums import (
    DiceSelectionRule,
    ModifierVisibility,
    ResolvedStepKind,
    RollAdjustmentTiming,
    RollContribution,
    RollVisibility,
    RpgInteractionPhase,
)
from afterworlds.models.rpg import (
    ContestLinkage,
    ContestResolution,
    DiceResult,
    MechanicalDecisionOption,
    MechanicalDecisionOptionSnapshot,
    MechanicalDecisionSnapshot,
    NaturalOutcome,
    PendingMechanicalDecisionView,
    PlayerAdjustmentOptionView,
    PlayerModifierView,
    PlayerRollInstructionView,
    PlayerRollTermView,
    ResolvedAdjudicationRecord,
    RollAdjustmentOption,
    RollInstructionSnapshot,
    RollModifierComponent,
    RollProposal,
    SequenceProgressView,
    SubjectRef,
    WriterAdjudicationView,
)
from afterworlds.pipeline.rpg import ids
from afterworlds.pipeline.rpg.dice import (
    DecisionRequest,
    DiceService,
    RollRequest,
    modifier_total,
    term_of,
)
from afterworlds.pipeline.rpg.models import (
    ActionSequenceIntegrityError,
    PlayerInputRequired,
)

__all__ = [
    "AcceptedDecision",
    "AcceptedRoll",
    "NewStep",
    "SequenceDice",
    "SequenceStart",
    "decision_view",
    "roll_view",
]


def _signed(value: int) -> str:
    return f"+ {value}" if value >= 0 else f"- {-value}"


def build_snapshot(
    expression: str,
    request: RollRequest,
    *,
    sequence_id: UUID,
    operation: int,
    die: int,
    revision: int,
) -> RollInstructionSnapshot:
    """The structured instruction of one described die, with identities
    derived from its place in the sequence."""
    base = f"{operation}:{die}"
    term = term_of(expression, ids.derived(sequence_id, f"term:{base}:0"))
    modifiers = tuple(
        RollModifierComponent(
            modifier_id=ids.derived(sequence_id, f"modifier:{base}:{i}"),
            label=label,
            value=value,
            visibility=ModifierVisibility.PLAYER_VISIBLE,
            source_kind="rule",
            source_reference=source,
        )
        for i, (label, value, source) in enumerate(request.modifiers)
        if value
    )
    kind, subject = request.roller
    contest = request.contest
    snapshot = RollInstructionSnapshot(
        instruction_id=ids.derived(sequence_id, f"instruction:{base}"),
        instruction_revision=revision,
        purpose=request.purpose,
        terms=(term,),
        modifier_components=modifiers,
        display_label=request.label,
        dc=request.dc,
        source_rule_refs=request.source_refs,
        adjustment_options=tuple(
            RollAdjustmentOption(
                option_id=option_id,
                ability_id=ability_id,
                timing=RollAdjustmentTiming.PRE_ROLL,
                player_visible_label=label,
            )
            for option_id, ability_id, label in request.options
        ),
        sequence_id=sequence_id,
        step_id=ids.derived(sequence_id, f"step:{base}"),
        roller=SubjectRef(kind=kind, subject_id=UUID(subject)),  # type: ignore[arg-type]
        operation_index=operation,
        die_index=die,
        natural_outcomes=tuple(
            NaturalOutcome(face=face, outcome=outcome)  # type: ignore[arg-type]
            for face, outcome in request.naturals
        ),
        critical_on_success=request.critical_on_success,
        contest=_linkage(contest, request, sequence_id, operation, die),
        display_expression="",
    )
    return snapshot.model_copy(
        update={"display_expression": player_expression(snapshot)}
    )


def _linkage(
    contest: object,
    request: RollRequest,
    sequence_id: UUID,
    operation: int,
    die: int,
) -> ContestLinkage | None:
    """A contest participant's backend-only linkage; the first participant's
    carries the counterpart's instruction, frozen now (Group 17)."""
    if not isinstance(contest, ContestLinkage):
        return None
    if request.counterpart is None:
        return contest
    expression, counterpart = request.counterpart
    frozen = build_snapshot(
        expression,
        counterpart,
        sequence_id=sequence_id,
        operation=operation,
        die=die + 1,
        revision=1,
    )
    return contest.model_copy(update={"counterpart_instruction": frozen})


def build_decision(
    described: DecisionRequest,
    *,
    sequence_id: UUID,
    operation: int,
    index: int,
) -> MechanicalDecisionSnapshot:
    base = f"{operation}:{index}"
    return MechanicalDecisionSnapshot(
        decision_id=ids.derived(sequence_id, f"decision:{base}"),
        decision_revision=1,
        prompt=described.prompt,
        options=tuple(
            MechanicalDecisionOptionSnapshot(
                option_id=o.option_id,
                player_visible_label=o.label,
                source_rule_ref=(
                    described.source_refs[0] if described.source_refs else None
                ),
                provisional_effects_json=json.dumps(
                    [e.model_dump(mode="json") for e in o.effects], sort_keys=True
                ),
            )
            for o in described.options
        ),
        source_rule_refs=described.source_refs,
        sequence_id=sequence_id,
        step_id=ids.derived(sequence_id, f"decision-step:{base}"),
    )


@dataclass(frozen=True)
class AcceptedRoll:
    """A validated roll for the pending die: the stored snapshot it was
    validated against, the dice it yields, and its provenance."""

    snapshot: RollInstructionSnapshot
    result: DiceResult
    kind: ResolvedStepKind
    pending_roll_request_id: UUID | None = None
    #: ``{term_id: values}`` when raw values were supplied.
    raw_values: dict[str, list[int]] | None = None
    reported_aggregate: int | None = None
    source: str = "backend_dice_service"
    #: On a contest-completing roll: the combined result (Group 17).
    contest_resolution: ContestResolution | None = None


@dataclass(frozen=True)
class AcceptedDecision:
    snapshot: MechanicalDecisionSnapshot
    option_id: str
    operation: int
    index: int


@dataclass(frozen=True)
class NewStep:
    """A step accepted in this run, in the order it happened."""

    roll: AcceptedRoll | None = None
    decision: AcceptedDecision | None = None

    @property
    def operation(self) -> int:
        if self.roll is not None:
            return self.roll.snapshot.operation_index
        assert self.decision is not None
        return self.decision.operation


@dataclass
class SequenceDice:
    """The dice and decision source of an adjudicating turn or sequence.

    ``rolls``/``decisions`` are what the sequence already accepted, by
    operation, in order. ``accept`` is the pending die's validated roll, or
    the pending decision's choice. ``revisions`` holds each adjusted
    instruction's current revision.
    """

    backend: DiceService
    sequence_id: UUID
    actor: tuple[str, str]
    player_rolls: bool
    rolls: dict[int, list[AcceptedRoll]] = field(default_factory=dict)
    decisions: dict[int, list[AcceptedDecision]] = field(default_factory=dict)
    accept: AcceptedRoll | AcceptedDecision | None = None
    revisions: dict[str, int] = field(default_factory=dict)
    new_steps: list[NewStep] = field(default_factory=list)
    _operation: int = -1
    _hidden: bool = False
    _die: int = 0
    _decision: int = 0
    #: This run's dice of the current operation: ``die -> (snapshot, dice)``.
    _served: dict[int, tuple[RollInstructionSnapshot, DiceResult]] = field(
        default_factory=dict
    )
    #: Each contest's one combined resolution, accepted or new.
    _resolutions: dict[UUID, ContestResolution] = field(default_factory=dict)

    @contextmanager
    def operation(self, index: int, hidden: bool) -> Iterator[None]:
        """Resolve operation *index* (its dice, decisions and identities)."""
        self._operation, self._hidden = index, hidden
        self._die = self._decision = 0
        self._served = {}
        with ids.scoped(ids.derived(self.sequence_id, f"operation:{index}")):
            yield

    def roll(self, expression: str) -> DiceResult:
        raise ActionSequenceIntegrityError(
            f"an undescribed {expression} roll in a turn's resolution: every die "
            "is a described request"
        )

    def roll_described(self, expression: str, request: RollRequest) -> DiceResult:
        op, die = self._operation, self._die
        self._die += 1
        snapshot = build_snapshot(
            expression,
            request,
            sequence_id=self.sequence_id,
            operation=op,
            die=die,
            revision=self.revisions.get(f"{op}:{die}", 1),
        )
        frozen = self._frozen(die)
        if frozen is not None and frozen != snapshot:
            raise ActionSequenceIntegrityError(
                "a contest participant's instruction is not the one frozen when "
                "the contest was created"
            )
        done = self.rolls.get(op, [])
        if die < len(done):
            if done[die].snapshot != snapshot:
                raise ActionSequenceIntegrityError(
                    "an accepted roll's instruction is not reproduced by the "
                    "current state"
                )
            accepted = done[die].contest_resolution
            if accepted is not None:
                self._resolutions[accepted.contest_id] = accepted
            return self._serve(die, snapshot, done[die].result)
        accept = self.accept
        if (
            isinstance(accept, AcceptedRoll)
            and accept.snapshot.operation_index == op
            and accept.snapshot.die_index == die
        ):
            if accept.snapshot != snapshot:
                raise ActionSequenceIntegrityError(
                    "the pending instruction is not reproduced by the current state"
                )
            self._record(NewStep(roll=accept))
            return self._serve(die, snapshot, accept.result)
        if self.player_owned(request):
            raise PlayerInputRequired(roll=snapshot)
        result = self.backend.roll(expression)
        hidden = self._hidden or request.hidden
        kind = ResolvedStepKind.HIDDEN_ROLL if hidden else ResolvedStepKind.AI_ROLL
        resolution = self._resolution(die, snapshot, result)
        if resolution is not None:
            self._resolutions[resolution.contest_id] = resolution
        self._record(
            NewStep(
                roll=AcceptedRoll(snapshot, result, kind, contest_resolution=resolution)
            )
        )
        return self._serve(die, snapshot, result)

    def contest_resolution(self, contest_id: UUID) -> ContestResolution | None:
        """The contest's combined resolution as its completing event holds it
        (the participants' actual steps): the one the record reuses."""
        return self._resolutions.get(contest_id)

    def _serve(
        self, die: int, snapshot: RollInstructionSnapshot, result: DiceResult
    ) -> DiceResult:
        self._served[die] = (snapshot, result)
        return result

    def _frozen(self, die: int) -> RollInstructionSnapshot | None:
        """The instruction a contest's first participant froze for this die."""
        earlier = self._served.get(die - 1)
        if earlier is None or earlier[0].contest is None:
            return None
        return earlier[0].contest.counterpart_instruction

    def _resolution(
        self, die: int, snapshot: RollInstructionSnapshot, result: DiceResult
    ) -> ContestResolution | None:
        """The contest's combined result, when this die completes one: both
        authoritative totals compared once (Group 17)."""
        from afterworlds.pipeline.rpg.contests import compare

        if snapshot.contest is None or snapshot.contest.counterpart_instruction:
            return None
        first = self._served.get(die - 1)
        if first is None or first[0].contest is None:
            raise ActionSequenceIntegrityError("a contest lost its first participant")
        before, dice_before = first
        assert before.contest is not None
        return compare(
            snapshot.contest.contest_id,
            (before.roller, before.step_id, _total(before, dice_before)),
            (snapshot.roller, snapshot.step_id, _total(snapshot, result)),
            before.contest.certificate,
        )

    def decide(self, described: DecisionRequest) -> str:
        op, index = self._operation, self._decision
        self._decision += 1
        snapshot = build_decision(
            described, sequence_id=self.sequence_id, operation=op, index=index
        )
        done = self.decisions.get(op, [])
        if index < len(done):
            if done[index].snapshot != snapshot:
                raise ActionSequenceIntegrityError(
                    "an accepted decision is not reproduced by the current state"
                )
            return done[index].option_id
        accept = self.accept
        if isinstance(accept, AcceptedDecision) and (
            accept.operation,
            accept.index,
        ) == (
            op,
            index,
        ):
            if accept.snapshot != snapshot:
                raise ActionSequenceIntegrityError(
                    "the pending decision is not reproduced by the current state"
                )
            self._record(NewStep(decision=accept))
            return accept.option_id
        raise PlayerInputRequired(decision=(snapshot, op, index))

    def player_owned(self, request: RollRequest) -> bool:
        """The die is the acting character's own and the story's dice are
        player-rolled; a hidden die is always the backend's."""
        return (
            self.player_rolls
            and not (self._hidden or request.hidden)
            and request.roller == self.actor
        )

    def _record(self, step: NewStep) -> None:
        self.new_steps.append(step)
        if self.accept is not None and (
            step.roll is self.accept or step.decision is self.accept
        ):
            self.accept = None


@dataclass(frozen=True)
class SequenceStart:
    """A turn whose resolution paused for the Sojourner (CRD Issue 15b):
    everything the announce transaction persists as a new sequence. Nothing
    here is sheet, audit or delivered-result authority yet."""

    sequence_id: UUID
    #: The turn's code-validated proposals (identities only, never numbers).
    proposals: tuple[RollProposal, ...]
    #: What the work rests on (``PreparedTurn.reads``), required unchanged.
    reads: dict[str, Any]
    gm_cheating: bool
    player_rolls: bool
    #: Operations resolved before the pause, in order.
    records: tuple[ResolvedAdjudicationRecord, ...]
    #: Backend dice drawn before the pause, in order.
    steps: tuple[NewStep, ...]
    pause: PlayerInputRequired

    def announcement(self) -> WriterAdjudicationView:
        """The announce Turn's Writer view: what the Sojourner is asked for,
        as the player sees it, and no result."""
        roll = self.pause.roll
        if isinstance(roll, RollInstructionSnapshot):
            label = roll.display_label
            summary = f"Roll needed: {label} ({player_expression(roll)})"
        else:
            decision = self.pause.decision
            assert decision is not None
            label = "Decision"
            summary = f"Decision needed: {decision[0].prompt}"
        return WriterAdjudicationView(
            check_label=label,
            visibility=RollVisibility.PLAYER,
            player_facing_summary=summary,
        )


def roll_view(
    snapshot: RollInstructionSnapshot,
    pending_roll_request_id: UUID,
    *,
    step_index: int,
    known_step_count: int | None = None,
) -> PlayerRollInstructionView:
    """The player-visible projection: no hidden modifier or its existence,
    no target, roller, linkage or rule reference (15b-17)."""
    visible = tuple(
        PlayerModifierView(modifier_id=m.modifier_id, label=m.label, value=m.value)
        for m in snapshot.modifier_components
        if m.visibility is ModifierVisibility.PLAYER_VISIBLE
    )
    return PlayerRollInstructionView(
        pending_roll_request_id=pending_roll_request_id,
        sequence_id=snapshot.sequence_id,
        instruction_id=snapshot.instruction_id,
        instruction_revision=snapshot.instruction_revision,
        purpose=snapshot.purpose,
        interaction_phase=RpgInteractionPhase.PENDING_ROLL,
        progress=SequenceProgressView(
            step_index=step_index,
            known_step_count=known_step_count,
            step_label=snapshot.display_label,
        ),
        display_label=snapshot.display_label,
        display_expression=player_expression(snapshot),
        terms=tuple(
            PlayerRollTermView(
                term_id=t.term_id,
                count=t.count,
                sides=t.sides,
                selection_rule=t.selection_rule,
                keep_count=t.keep_count,
                contribution=t.contribution,
                label=t.label,
            )
            for t in snapshot.terms
        ),
        visible_modifiers=visible,
        visible_modifier_total=sum(m.value for m in visible),
        adjustment_options=tuple(
            PlayerAdjustmentOptionView(
                option_id=o.option_id,
                player_visible_label=o.player_visible_label,
                resource_preview=o.resource_preview,
            )
            for o in snapshot.adjustment_options
        ),
    )


def _total(snapshot: RollInstructionSnapshot, result: DiceResult) -> int:
    """A die's authoritative total: its kept dice and every modifier."""
    return (
        result.chosen
        + modifier_total(snapshot, visible=True)
        + modifier_total(snapshot, visible=False)
    )


def player_expression(snapshot: RollInstructionSnapshot) -> str:
    """The dice and the visible modifier total, as the player sees them: a
    hidden modifier changes neither the text nor its sign (15b-17)."""
    parts = []
    for i, t in enumerate(snapshot.terms):
        keep = ""
        if t.keep_count is not None:
            rule = "kh" if t.selection_rule is DiceSelectionRule.KEEP_HIGHEST else "kl"
            keep = f"{rule}{t.keep_count}"
        text = f"{t.count}d{t.sides}{keep}"
        if i:
            sign = "-" if t.contribution is RollContribution.SUBTRACT else "+"
            text = f"{sign} {text}"
        elif t.contribution is RollContribution.SUBTRACT:
            text = f"-{text}"
        parts.append(text)
    visible = modifier_total(snapshot, visible=True)
    if visible:
        parts.append(_signed(visible))
    return " ".join(parts)


def decision_view(
    snapshot: MechanicalDecisionSnapshot,
) -> PendingMechanicalDecisionView:
    """Only the prompt and each option's id and label reach the player."""
    return PendingMechanicalDecisionView(
        decision_request_id=snapshot.decision_id,
        sequence_id=snapshot.sequence_id,
        decision_revision=snapshot.decision_revision,
        interaction_phase=RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
        prompt=snapshot.prompt,
        options=tuple(
            MechanicalDecisionOption(
                option_id=o.option_id, player_visible_label=o.player_visible_label
            )
            for o in snapshot.options
        ),
    )
