"""ActionResolutionService — persisted action-resolution sequences (CRD Issue 15b).

A turn whose resolution needs the Sojourner (their own die in a player-rolled
story, or a result-triggered decision) becomes a sequence when its announce
Turn is delivered (:meth:`ActionResolutionService.start`). Each later roll,
adjustment or decision advances it by a deterministic intermediate operation:
no provider call, no Turn, no settlement (15b-20, 15b-27, 15b-28).

Every advancement:

1. **validates the submission against the stored snapshot only**: the pending
   roll's ``RollInstructionSnapshot``, or the pending
   ``MechanicalDecisionSnapshot`` (15b-35). Nothing live is read to judge it;
2. **reads**: reloads the acting character and every subject, repeats the
   turn's dice-free preflight and requires everything it rests on unchanged
   (revisions, exact bindings, holdings, coordination, discovery). It then
   resolves the turn's operations again, folding those already resolved from
   their records and serving the accepted dice and decisions to the one in
   flight. Whatever it rebuilds must equal the stored authority
   (:mod:`.steps`);
3. **commits atomically**: one append-only event per accepted step and the
   sequence's advancement, under compare-and-swap guards on the sequence, the
   pending request and every subject read. An invalid, stale, duplicate or
   concurrent submission commits neither (15b-34).

The final narration is the orchestrator's (``orchestrate_rpg_resume``). This
service never invokes the pipeline (15b-21): :meth:`prepare_delivery` hands it
the ready bundle and the resolved records, rebuilt from the event ledger
alone, and :meth:`complete` writes the delivered-result audit from the ledger
in the delivery transaction.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    ActionResolutionStatus,
    ResolvedStepKind,
    RollPurpose,
    RollSubmissionSource,
    RollVisibility,
    RpgInteractionPhase,
    SequenceInteractionKind,
)
from afterworlds.models.rpg import (
    ActionResolutionAdvanceResult,
    ActionResolutionEvent,
    AdjustmentEventPayload,
    DerivedRollTermResult,
    DiceResult,
    MechanicalDecisionEventPayload,
    MechanicalDecisionSnapshot,
    MechanicalDecisionSubmission,
    PhysicalAggregateRollSubmission,
    RawPlayerRollSubmission,
    ReadyActionResolutionBundle,
    ResolvedAdjudicationRecord,
    ResolvedSequenceStep,
    RollEventPayload,
    RollInstructionSnapshot,
    RollProposal,
    SheetEffect,
)
from afterworlds.pipeline.rpg import dice as dice_engine
from afterworlds.pipeline.rpg.capability import ADAPTER_VERSION, AdjudicationRefusal
from afterworlds.pipeline.rpg.models import (
    ActionAdjustmentIneligibleError,
    ActionAdjustmentNotAllowedError,
    ActionSequenceAlreadyCompletedError,
    ActionSequenceIntegrityError,
    ActionSequenceNotFoundError,
    ActionSequenceStateConflictError,
    AdjudicationPassError,
    MechanicalDecisionInvalidError,
    MechanicalDecisionRevisionMismatchError,
    PendingRollAlreadyConsumedError,
    PendingRollInvalidAggregateError,
    PendingRollInvalidValueError,
    PendingRollNotFoundError,
    PendingRollNotPlayerVisibleError,
    PendingRollRevisionMismatchError,
    PendingRollTermMismatchError,
    PlayerInputRequired,
    SequenceNotReadyForNarrationError,
)
from afterworlds.pipeline.rpg.steps import (
    AcceptedDecision,
    AcceptedRoll,
    NewStep,
    SequenceDice,
    SequenceStart,
    decision_view,
    player_expression,
    roll_view,
)
from afterworlds.services.dnd5e_state.errors import StaleRevisionError
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind
from afterworlds.services.dnd5e_state.turn import (
    TurnCreature,
    advanced,
    require_holdings_unchanged,
    require_story_unchanged,
    require_unchanged,
)

if TYPE_CHECKING:
    from afterworlds.models.session import RpgSessionState
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.pipeline.rpg.service import (
        PreparedTurn,
        RpgAdjudicationPassService,
    )
    from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnSubject

__all__ = [
    "ActionResolutionService",
    "Delivery",
    "UnresolvedSequence",
    "audit_rows",
]

#: What produced an event: the adapter version (ADR-015b 15b-34 provenance).
_PROVENANCE = f"d20_rules_system_adapter/{ADAPTER_VERSION}"
_UNRESOLVED = (
    ActionResolutionStatus.ACTIVE.value,
    ActionResolutionStatus.READY_FOR_NARRATION.value,
)
#: Purposes whose instruction is a single check, save or contest die.
_ONE_DIE = (
    RollPurpose.ABILITY_CHECK,
    RollPurpose.SKILL_CHECK,
    RollPurpose.CONTESTED,
)


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class UnresolvedSequence:
    """A story's unresolved sequence, as the in-character gate and the OOC
    handler see it: player-visible text only."""

    sequence_id: UUID
    interaction_phase: RpgInteractionPhase
    redirect_message: str


@dataclass
class Delivery:
    """A ready sequence's facts for its final narration, rebuilt from the
    event ledger: the bundle, the resolved records in operation order, and the
    subjects and coordination re-read at the revisions the work rests on."""

    bundle: ReadyActionResolutionBundle
    records: tuple[ResolvedAdjudicationRecord, ...]
    events: tuple[ActionResolutionEvent, ...]
    prepared: PreparedTurn
    revision: int


@dataclass
class _Run:
    prepared: PreparedTurn
    records: list[ResolvedAdjudicationRecord]
    steps: list[NewStep]
    pause: PlayerInputRequired | None


@dataclass
class _Plan:
    """A sequence's code-validated proposals and resolution settings."""

    proposals: list[RollProposal]
    gm_cheating: bool
    player_rolls: bool
    revisions: dict[str, int] = field(default_factory=dict)
    pending_decision: tuple[int, int] | None = None

    def dump(self) -> str:
        return _dump(
            {
                "proposals": [p.model_dump(mode="json") for p in self.proposals],
                "gm_cheating": self.gm_cheating,
                "player_rolls": self.player_rolls,
                "revisions": self.revisions,
                "pending_decision": (
                    list(self.pending_decision) if self.pending_decision else None
                ),
            }
        )

    @classmethod
    def load(cls, raw: str) -> _Plan:
        data = json.loads(raw)
        pending = data.get("pending_decision")
        return cls(
            proposals=[RollProposal.model_validate(p) for p in data["proposals"]],
            gm_cheating=bool(data["gm_cheating"]),
            player_rolls=bool(data["player_rolls"]),
            revisions={k: int(v) for k, v in data["revisions"].items()},
            pending_decision=(int(pending[0]), int(pending[1])) if pending else None,
        )


def _records(raw: str) -> list[ResolvedAdjudicationRecord]:
    return [ResolvedAdjudicationRecord.model_validate(r) for r in json.loads(raw)]


def _dump_records(records: list[ResolvedAdjudicationRecord]) -> str:
    return _dump([r.model_dump(mode="json") for r in records])


def _event_from(row: Any) -> ActionResolutionEvent:
    """An event reconstructed from its own persisted row only (AC46)."""
    return ActionResolutionEvent.model_validate(
        {
            "event_id": row.event_id,
            "sequence_id": row.sequence_id,
            "step_id": row.step_id,
            "story_id": row.story_id,
            "session_id": row.session_id,
            "character_id": row.character_id,
            "event_order": row.event_order,
            "kind": row.kind,
            "mechanical_provenance": row.mechanical_provenance,
            "provisional_effects_json": row.provisional_effects_json,
            "created_at": row.created_at,
            "payload": json.loads(row.payload_json),
        }
    )


def _accepted_roll(event: ActionResolutionEvent) -> AcceptedRoll:
    """The dice an accepted roll event yields when its operation is resolved
    again: exactly its recorded values, never a new roll."""
    payload = event.payload
    assert isinstance(payload, RollEventPayload)
    snapshot = payload.instruction_snapshot
    if payload.raw_input_json is not None:
        derived = [
            DerivedRollTermResult.model_validate(d)
            for d in json.loads(payload.derived_selections_json)
        ]
        values = tuple(v for d in derived for v in d.values)
        chosen = sum(d.contribution_applied_subtotal for d in derived)
        raw: dict[str, list[int]] | None = {
            str(d.term_id): list(d.values) for d in derived
        }
        aggregate = None
    else:
        aggregate = json.loads(payload.aggregate_input_json or "{}")[
            "reported_aggregate"
        ]
        values = ()
        chosen = aggregate - dice_engine.modifier_total(snapshot, visible=True)
        raw = None
    return AcceptedRoll(
        snapshot=snapshot,
        result=DiceResult(
            expression=snapshot.display_expression, raw_rolls=values, chosen=chosen
        ),
        kind=payload.kind,
        pending_roll_request_id=payload.pending_roll_request_id,
        raw_values=raw,
        reported_aggregate=aggregate,
        source=payload.submission_source.value,
        contest_resolution=payload.contest_resolution,
    )


class ActionResolutionService:
    """Deterministic ActionResolutionSequence transitions (CRD Issue 15b).

    Args:
        adjudication: the RPG adjudication service whose dice-free
            :meth:`~.service.RpgAdjudicationPassService.prepare_turn` and
            :meth:`~.service.RpgAdjudicationPassService.resolve_turn` the
            sequence repeats; it owns the subject, coordination and discovery
            readers.
        adapter: the bounded d20 adapter (Writer views of records).
        dice_service: backend dice for AI and hidden steps.
        session_factory: a fresh SQLAlchemy session per read or transaction.
        sheet_resolver: the story's RPG session and acting character, under
            its exact binding (the orchestrator's resolver).
    """

    def __init__(
        self,
        adjudication: RpgAdjudicationPassService,
        adapter: D20RulesSystemAdapter,
        dice_service: DiceService,
        session_factory: Callable[[], Session],
        sheet_resolver: Callable[[UUID], tuple[RpgSessionState, TurnCharacter]],
    ) -> None:
        self._adjudication = adjudication
        self._adapter = adapter
        self._dice = dice_service
        self._factory = session_factory
        self._sheet = sheet_resolver

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def unresolved(self, story_id: UUID) -> UnresolvedSequence | None:
        """The story's unresolved sequence, for the in-character gate (15b-31):
        ordinary in-character input is blocked while one exists in any state."""
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        with self._factory() as session:
            row = session.execute(
                sa.select(ActionResolutionSequenceORM).where(
                    ActionResolutionSequenceORM.story_id == str(story_id),
                    ActionResolutionSequenceORM.status.in_(_UNRESOLVED),
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            if row.status == ActionResolutionStatus.READY_FOR_NARRATION.value:
                return UnresolvedSequence(
                    UUID(row.sequence_id),
                    RpgInteractionPhase.READY_FOR_NARRATION,
                    "The resolved action is ready to be narrated.",
                )
            if row.current_interaction_kind == SequenceInteractionKind.DECISION.value:
                assert row.current_decision_snapshot_json is not None
                decision = MechanicalDecisionSnapshot.model_validate_json(
                    row.current_decision_snapshot_json
                )
                return UnresolvedSequence(
                    UUID(row.sequence_id),
                    RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
                    f"Decision needed: {decision.prompt}",
                )
            pending = session.get(
                PendingRollRequestORM, row.current_pending_roll_request_id
            )
            assert pending is not None and pending.instruction_snapshot_json
            snapshot = RollInstructionSnapshot.model_validate_json(
                pending.instruction_snapshot_json
            )
            return UnresolvedSequence(
                UUID(row.sequence_id),
                RpgInteractionPhase.PENDING_ROLL,
                f"Roll needed: {snapshot.display_label} "
                f"({player_expression(snapshot)})",
            )

    def current(self, story_id: UUID) -> ActionResolutionAdvanceResult | None:
        """The story's pending interaction as the player sees it, or ``None``
        with no unresolved sequence: the backend seam the pending-interaction
        read uses (15b-31)."""
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        with self._factory() as session:
            row = session.execute(
                sa.select(ActionResolutionSequenceORM).where(
                    ActionResolutionSequenceORM.story_id == str(story_id),
                    ActionResolutionSequenceORM.status.in_(_UNRESOLVED),
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            return self._advance_result(session, row)

    # ------------------------------------------------------------------
    # Start (announce Turn's transaction)
    # ------------------------------------------------------------------

    def start(
        self,
        session: Session,
        start: SequenceStart,
        *,
        story_id: UUID,
        session_id: UUID,
        node_id: UUID,
        character_id: UUID,
        originating_turn_id: UUID,
    ) -> ActionResolutionAdvanceResult:
        """Persist a paused turn as a new sequence inside the announce
        Turn's transaction: the backend dice drawn before the pause as events,
        and its first pending interaction. Commits or rolls back with that
        Turn; the partial unique index admits one unresolved sequence per
        story."""
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        existing = session.execute(
            sa.select(ActionResolutionSequenceORM.sequence_id).where(
                ActionResolutionSequenceORM.story_id == str(story_id),
                ActionResolutionSequenceORM.status.in_(_UNRESOLVED),
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ActionSequenceStateConflictError(
                f"story {story_id} already has an unresolved sequence {existing}"
            )
        now = _now()
        plan = _Plan(
            proposals=list(start.proposals),
            gm_cheating=start.gm_cheating,
            player_rolls=start.player_rolls,
        )
        row = ActionResolutionSequenceORM(
            sequence_id=str(start.sequence_id),
            story_id=str(story_id),
            session_id=str(session_id),
            node_id=str(node_id),
            character_id=str(character_id),
            originating_turn_id=str(originating_turn_id),
            status=ActionResolutionStatus.ACTIVE.value,
            current_interaction_kind=SequenceInteractionKind.NONE.value,
            plan_json=plan.dump(),
            reads_json=_dump(start.reads),
            records_json="[]",
            unattached_json="[]",
            resolved_steps_json="[]",
            projected_state_json="{}",
            provisional_effects_json="[]",
            revision=0,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        self._commit_run(
            session,
            row,
            plan,
            records=list(start.records),
            steps=list(start.steps),
            pause=start.pause,
            projected=None,
        )
        return self._advance_result(session, row)

    # ------------------------------------------------------------------
    # Intermediate operations
    # ------------------------------------------------------------------

    def consume_roll(
        self, submission: RawPlayerRollSubmission | PhysicalAggregateRollSubmission
    ) -> ActionResolutionAdvanceResult:
        """Validate a roll submission against the stored instruction, then
        accept it: one event per accepted step and the sequence's advancement,
        together. Invalid input changes nothing (#127 Validation 1–10)."""
        with self._factory() as session:
            pending, row = self._pending(session, submission.pending_roll_request_id)
            snapshot = RollInstructionSnapshot.model_validate_json(
                pending.instruction_snapshot_json
            )
            if (
                snapshot.instruction_revision
                != submission.expected_instruction_revision
            ):
                raise PendingRollRevisionMismatchError(
                    f"pending roll {submission.pending_roll_request_id} is at "
                    f"revision {snapshot.instruction_revision}; the submission "
                    f"expected {submission.expected_instruction_revision}"
                )
            accepted = _validate_roll(snapshot, submission)
            expected = row.revision
        return self._advance(
            UUID(row.sequence_id),
            expected,
            accept=accepted,
            consume=(submission.pending_roll_request_id, snapshot.instruction_revision),
        )

    def apply_adjustment(
        self,
        pending_roll_request_id: UUID,
        expected_instruction_revision: int,
        option_id: str,
    ) -> ActionResolutionAdvanceResult:
        """Apply a parameterless pre-roll option of the pending roll: the
        revised instruction (``instruction_revision`` + 1) is returned in the
        same ``PENDING_ROLL`` phase, with an ``ADJUSTMENT`` event (15b-9 to
        15b-13). An option not offered, a stale revision or an option the
        rules no longer admit changes nothing."""
        with self._factory() as session:
            pending, row = self._pending(session, pending_roll_request_id)
            snapshot = RollInstructionSnapshot.model_validate_json(
                pending.instruction_snapshot_json
            )
            # Exact integers only: ``True`` or ``1.0`` is no revision (#127
            # Validation 5's ingress rule, as for the roll submissions).
            if (
                type(expected_instruction_revision) is not int
                or snapshot.instruction_revision != expected_instruction_revision
            ):
                raise PendingRollRevisionMismatchError(
                    f"pending roll {pending_roll_request_id} is at revision "
                    f"{snapshot.instruction_revision}; the adjustment expected "
                    f"{expected_instruction_revision}"
                )
            option = next(
                (o for o in snapshot.adjustment_options if o.option_id == option_id),
                None,
            )
            if option is None or option.timing.value != "pre_roll":
                raise ActionAdjustmentNotAllowedError(
                    f"{option_id!r} is not a pre-roll option of this roll"
                )
            plan = _Plan.load(row.plan_json)
            expected = row.revision
        adjusted = _adjusted(plan, snapshot, option_id)
        return self._advance(
            UUID(row.sequence_id),
            expected,
            plan=adjusted,
            adjustment=(pending_roll_request_id, snapshot, option_id),
        )

    def submit_decision(
        self, submission: MechanicalDecisionSubmission
    ) -> ActionResolutionAdvanceResult:
        """Accept the Sojourner's choice of the pending decision, validated
        purely against its stored snapshot (15b-35, AC41)."""
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        with self._factory() as session:
            row = session.execute(
                sa.select(ActionResolutionSequenceORM).where(
                    ActionResolutionSequenceORM.current_decision_request_id
                    == str(submission.decision_request_id)
                )
            ).scalar_one_or_none()
            if row is None or row.current_decision_snapshot_json is None:
                raise MechanicalDecisionInvalidError(
                    f"no pending decision {submission.decision_request_id}"
                )
            snapshot = MechanicalDecisionSnapshot.model_validate_json(
                row.current_decision_snapshot_json
            )
            if snapshot.decision_revision != submission.expected_decision_revision:
                raise MechanicalDecisionRevisionMismatchError(
                    f"decision {snapshot.decision_id} is at revision "
                    f"{snapshot.decision_revision}; the submission expected "
                    f"{submission.expected_decision_revision}"
                )
            if submission.option_id not in {o.option_id for o in snapshot.options}:
                raise MechanicalDecisionInvalidError(
                    f"{submission.option_id!r} is not an option of this decision"
                )
            plan = _Plan.load(row.plan_json)
            assert plan.pending_decision is not None
            operation, index = plan.pending_decision
            expected = row.revision
        return self._advance(
            UUID(row.sequence_id),
            expected,
            accept=AcceptedDecision(snapshot, submission.option_id, operation, index),
        )

    # ------------------------------------------------------------------
    # Final delivery (orchestrator-owned resume)
    # ------------------------------------------------------------------

    def get_ready_bundle(
        self, story_id: UUID, sequence_id: UUID, node_id: UUID
    ) -> ReadyActionResolutionBundle:
        return self.prepare_delivery(story_id, sequence_id, node_id).bundle

    def prepare_delivery(
        self, story_id: UUID, sequence_id: UUID, node_id: UUID
    ) -> Delivery:
        """A ready sequence's delivery facts, or a typed refusal: not found,
        already completed (15b-32), not ready, or another story/node (15b-23).
        Audit facts and effects come from the event ledger alone; the subjects
        are re-read and must be exactly what the work rests on."""
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionEventORM,
            ActionResolutionSequenceORM,
        )

        with self._factory() as session:
            row = session.get(ActionResolutionSequenceORM, str(sequence_id))
            if row is None:
                raise ActionSequenceNotFoundError(f"sequence {sequence_id} not found")
            if row.story_id != str(story_id):
                raise ActionSequenceNotFoundError(
                    f"sequence {sequence_id} is not this story's"
                )
            if row.status == ActionResolutionStatus.COMPLETED.value:
                raise ActionSequenceAlreadyCompletedError(
                    f"sequence {sequence_id} was already narrated"
                )
            if row.status != ActionResolutionStatus.READY_FOR_NARRATION.value:
                raise SequenceNotReadyForNarrationError(
                    f"sequence {sequence_id} still awaits the Sojourner"
                )
            if row.node_id != str(node_id):
                raise ActionSequenceStateConflictError(
                    f"sequence {sequence_id} was declared at another node than the "
                    "story's current one"
                )
            events = tuple(
                _event_from(e)
                for e in session.execute(
                    sa.select(ActionResolutionEventORM)
                    .where(ActionResolutionEventORM.sequence_id == str(sequence_id))
                    .order_by(ActionResolutionEventORM.event_order)
                ).scalars()
            )
            plan = _Plan.load(row.plan_json)
            reads = json.loads(row.reads_json)
            user_input = session.execute(
                sa.text("SELECT user_input FROM turns WHERE turn_id = :t"),
                {"t": row.originating_turn_id},
            ).scalar_one()
            identity = (
                UUID(row.session_id),
                UUID(row.character_id),
                UUID(row.originating_turn_id),
                row.revision,
            )
        records = _ledger_records(events, len(plan.proposals))
        _check_contests(events, records)
        prepared = self._read(story_id, identity[1], plan, reads)
        views = tuple(self._adapter.to_writer_view(r) for r in records)
        bundle = ReadyActionResolutionBundle(
            sequence_id=sequence_id,
            story_id=story_id,
            session_id=identity[0],
            node_id=node_id,
            character_id=identity[1],
            originating_turn_id=identity[2],
            originating_user_input=str(user_input),
            resolved_steps=tuple(_step(e, i) for i, e in enumerate(events, 1)),
            writer_views=views,
            accumulated_provisional_effects=tuple(
                SheetEffect.model_validate(x)
                for e in events
                for x in json.loads(e.provisional_effects_json)
            ),
        )
        return Delivery(bundle, records, events, prepared, identity[3])

    def complete(self, session: Session, delivery: Delivery, turn_id: UUID) -> None:
        """Inside the delivery transaction: the final ``rpg_roll_audit`` rows
        from the roll events alone (Final Audit Projection), and the sequence
        completed by compare-and-swap. Rolls back with the Turn."""
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        result = session.execute(
            sa.update(ActionResolutionSequenceORM)
            .where(
                ActionResolutionSequenceORM.sequence_id
                == str(delivery.bundle.sequence_id),
                ActionResolutionSequenceORM.status
                == ActionResolutionStatus.READY_FOR_NARRATION.value,
                ActionResolutionSequenceORM.revision == delivery.revision,
            )
            .values(
                status=ActionResolutionStatus.COMPLETED.value,
                revision=delivery.revision + 1,
                updated_at=_now(),
            )
        )
        if result.rowcount != 1:  # type: ignore[attr-defined]
            raise ActionSequenceAlreadyCompletedError(
                f"sequence {delivery.bundle.sequence_id} was narrated concurrently"
            )
        for audit in audit_rows(delivery.events, turn_id):
            session.add(audit)
        session.flush()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _pending(self, session: Session, request_id: UUID) -> tuple[Any, Any]:
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        pending = session.get(PendingRollRequestORM, str(request_id))
        if pending is None or pending.instruction_snapshot_json is None:
            raise PendingRollNotFoundError(f"pending roll {request_id} not found")
        if pending.status != "pending":
            raise PendingRollAlreadyConsumedError(
                f"pending roll {request_id} is {pending.status}"
            )
        if pending.visibility != RollVisibility.PLAYER.value:
            raise PendingRollNotPlayerVisibleError(
                f"pending roll {request_id} is not the player's"
            )
        row = session.get(ActionResolutionSequenceORM, pending.sequence_id)
        if (
            row is None
            or row.status != ActionResolutionStatus.ACTIVE.value
            or row.current_pending_roll_request_id != str(request_id)
        ):
            raise ActionSequenceStateConflictError(
                f"pending roll {request_id} is not its sequence's pending interaction"
            )
        return pending, row

    def _read(
        self,
        story_id: UUID,
        character_id: UUID,
        plan: _Plan,
        reads: dict[str, Any],
    ) -> PreparedTurn:
        """Reload and re-check the turn before any die; refuse when what the
        sequence rests on has moved (typed, nothing changed)."""
        _, sheet = self._sheet(story_id)
        if sheet.sheet_id != character_id:
            raise ActionSequenceStateConflictError(
                "the story's acting character is not the sequence's"
            )
        try:
            prepared = self._adjudication.prepare_turn(
                story_id, sheet, list(plan.proposals)
            )
        except AdjudicationPassError as exc:
            raise ActionSequenceStateConflictError(
                f"the sequence's operations no longer pass their checks: {exc}"
            ) from exc
        # Compared canonically: the stored reads are JSON (tuples are lists).
        if json.loads(_dump(prepared.reads())) != reads:
            raise ActionSequenceStateConflictError(
                "a subject, its holdings, the turn coordination or the story "
                "changed after the sequence read them"
            )
        return prepared

    def _replay(
        self,
        session: Session,
        row: Any,
        plan: _Plan,
        accept: AcceptedRoll | AcceptedDecision | None,
        prepared: PreparedTurn,
    ) -> _Run:
        from afterworlds.persistence.orm.rpg import ActionResolutionEventORM

        events = [
            _event_from(e)
            for e in session.execute(
                sa.select(ActionResolutionEventORM)
                .where(ActionResolutionEventORM.sequence_id == row.sequence_id)
                .order_by(ActionResolutionEventORM.event_order)
            ).scalars()
        ]
        rolls: dict[int, list[AcceptedRoll]] = {}
        decisions: dict[int, list[AcceptedDecision]] = {}
        for event in events:
            provenance = json.loads(event.mechanical_provenance)
            if isinstance(event.payload, RollEventPayload):
                op = event.payload.instruction_snapshot.operation_index
                rolls.setdefault(op, []).append(_accepted_roll(event))
            elif isinstance(event.payload, MechanicalDecisionEventPayload):
                op, index = provenance["operation_index"], provenance["decision_index"]
                decisions.setdefault(op, []).append(
                    AcceptedDecision(
                        event.payload.decision_snapshot,
                        event.payload.accepted_decision_option_id,
                        op,
                        index,
                    )
                )
        dice = SequenceDice(
            backend=self._dice,
            sequence_id=UUID(row.sequence_id),
            actor=("character", row.character_id),
            player_rolls=plan.player_rolls,
            rolls=rolls,
            decisions=decisions,
            accept=accept,
            revisions=dict(plan.revisions),
        )
        records = _records(row.records_json)
        pause: PlayerInputRequired | None = None
        try:
            self._adjudication.resolve_turn(prepared, plan.gm_cheating, dice, records)
        except PlayerInputRequired as exc:
            pause = exc
        except (AdjudicationPassError, AdjudicationRefusal) as exc:
            raise ActionSequenceIntegrityError(
                f"the sequence's resolution failed: {exc}"
            ) from exc
        if dice.accept is not None:
            raise ActionSequenceIntegrityError(
                "the submission was not reached by the sequence's resolution"
            )
        return _Run(prepared, records, dice.new_steps, pause)

    def _advance(
        self,
        sequence_id: UUID,
        expected_revision: int,
        *,
        accept: AcceptedRoll | AcceptedDecision | None = None,
        plan: _Plan | None = None,
        consume: tuple[UUID, int] | None = None,
        adjustment: tuple[UUID, RollInstructionSnapshot, str] | None = None,
    ) -> ActionResolutionAdvanceResult:
        """Accept one submission in one intermediate transaction, or nothing.

        The turn is first prepared again, dice-free, through the adjudication
        service's own readers (their sessions, never this transaction's). The
        transaction then claims the sequence: a compare-and-swap of the
        revision the submission was validated against (and, for a roll, the
        conditional consume of the pending request). That takes SQLite's write
        lock, so a concurrent or stale submission fails here, before any die.
        Every read the preparation rests on (subjects, holdings, discovery,
        coordination) is then rechecked, so state that moved after the
        preparation also refuses before any die. Only then is the sequence
        resolved again, and any backend (AI or hidden) die it needs, such as a
        contest counterpart's, is drawn inside this same transaction (ADR-015b
        Group 17); its events and the advancement commit with it. Any failure
        rolls everything back, those dice included: they never become
        authority. No provider is called and nothing is
        settled."""
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        with self._factory() as session:
            read = session.get(ActionResolutionSequenceORM, str(sequence_id))
            if read is None or read.revision != expected_revision:
                raise ActionSequenceStateConflictError(
                    f"sequence {sequence_id} advanced concurrently"
                )
            plan = plan or _Plan.load(read.plan_json)
            ids = (UUID(read.story_id), UUID(read.character_id))
            reads = json.loads(read.reads_json)
        # Outside the write transaction: the readers may record what they
        # resolve (binding retention) in their own sessions. The claim below
        # proves the plan and reads are still the ones prepared here.
        prepared = self._read(*ids, plan, reads)
        with self._factory() as session, session.begin():
            claimed = session.execute(
                sa.update(ActionResolutionSequenceORM)
                .where(
                    ActionResolutionSequenceORM.sequence_id == str(sequence_id),
                    ActionResolutionSequenceORM.revision == expected_revision,
                    ActionResolutionSequenceORM.status
                    == ActionResolutionStatus.ACTIVE.value,
                )
                .values(revision=expected_revision + 1)
            )
            if claimed.rowcount != 1:  # type: ignore[attr-defined]
                raise ActionSequenceStateConflictError(
                    f"sequence {sequence_id} advanced concurrently"
                )
            if consume is not None:
                request_id, revision = consume
                updated = session.execute(
                    sa.update(PendingRollRequestORM)
                    .where(
                        PendingRollRequestORM.request_id == str(request_id),
                        PendingRollRequestORM.status == "pending",
                        PendingRollRequestORM.instruction_revision == revision,
                    )
                    .values(status="consumed")
                )
                if updated.rowcount != 1:  # type: ignore[attr-defined]
                    raise PendingRollAlreadyConsumedError(
                        f"pending roll {request_id} was consumed concurrently"
                    )
            # Before any die: every read the preparation rests on is still
            # current. State that moved after preparation refuses here, with
            # no draw; holding the write lock, nothing moves after it.
            _recheck(session, prepared)
            row = session.get(ActionResolutionSequenceORM, str(sequence_id))
            assert row is not None
            run = self._replay(session, row, plan, accept, prepared)
            if adjustment is not None:
                request_id, before, option_id = adjustment
                revised = run.pause.roll if run.pause is not None else None
                if not (
                    isinstance(revised, RollInstructionSnapshot)
                    and revised.instruction_id == before.instruction_id
                    and revised.instruction_revision == before.instruction_revision + 1
                    and not run.steps
                ):
                    raise ActionAdjustmentIneligibleError(
                        f"{option_id!r} does not yield a revision of the pending roll"
                    )
                updated = session.execute(
                    sa.update(PendingRollRequestORM)
                    .where(
                        PendingRollRequestORM.request_id == str(request_id),
                        PendingRollRequestORM.status == "pending",
                        PendingRollRequestORM.instruction_revision
                        == before.instruction_revision,
                    )
                    .values(
                        instruction_revision=revised.instruction_revision,
                        instruction_snapshot_json=revised.model_dump_json(),
                    )
                )
                if updated.rowcount != 1:  # type: ignore[attr-defined]
                    raise PendingRollRevisionMismatchError(
                        f"pending roll {request_id} changed concurrently"
                    )
                _append(
                    session,
                    row,
                    ResolvedStepKind.ADJUSTMENT,
                    revised.step_id,
                    AdjustmentEventPayload(
                        resulting_instruction_snapshot=revised,
                        accepted_adjustment_option_id=option_id,
                    ),
                    {"operation_index": revised.operation_index},
                    [],
                )
            self._commit_run(
                session,
                row,
                plan,
                records=run.records,
                steps=run.steps,
                pause=run.pause,
                projected=run.prepared,
                adjusted=adjustment is not None,
                claimed=True,
            )
            return self._advance_result(session, row)

    def _commit_run(
        self,
        session: Session,
        row: Any,
        plan: _Plan,
        *,
        records: list[ResolvedAdjudicationRecord],
        steps: list[NewStep],
        pause: PlayerInputRequired | None,
        projected: PreparedTurn | None,
        adjusted: bool = False,
        claimed: bool = False,
    ) -> None:
        """Write the run's steps as events (each carrying the records of the
        operations its acceptance completed) and advance the sequence."""
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        done = _records(row.records_json)
        queue = [
            (int(i), ResolvedAdjudicationRecord.model_validate(r))
            for i, r in json.loads(row.unattached_json)
        ]
        queue += [(i, r) for i, r in enumerate(records) if i >= len(done)]
        attached: list[list[tuple[int, ResolvedAdjudicationRecord]]] = [
            [] for _ in steps
        ]
        if steps:
            for index, record in queue:
                earlier = [k for k, s in enumerate(steps) if s.operation <= index]
                attached[earlier[-1] if earlier else 0].append((index, record))
            queue = []
        for step, mine in zip(steps, attached, strict=True):
            effects = [
                e.model_dump(mode="json") for _, r in mine for e in r.sheet_effects
            ]
            provenance: dict[str, Any] = {
                "records": [
                    {"operation_index": i, "record": r.model_dump(mode="json")}
                    for i, r in mine
                ]
            }
            if step.roll is not None:
                snapshot = step.roll.snapshot
                provenance["operation_index"] = snapshot.operation_index
                provenance["die_index"] = snapshot.die_index
                _append(
                    session,
                    row,
                    step.roll.kind,
                    snapshot.step_id,
                    _roll_payload(step.roll, plan.gm_cheating),
                    provenance,
                    effects,
                )
            else:
                decision = step.decision
                assert decision is not None
                provenance["operation_index"] = decision.operation
                provenance["decision_index"] = decision.index
                _append(
                    session,
                    row,
                    ResolvedStepKind.MECHANICAL_DECISION,
                    decision.snapshot.step_id,
                    MechanicalDecisionEventPayload(
                        decision_snapshot=decision.snapshot,
                        accepted_decision_option_id=decision.option_id,
                    ),
                    provenance,
                    effects,
                )
        row.records_json = _dump_records(records)
        row.unattached_json = _dump([[i, r.model_dump(mode="json")] for i, r in queue])
        row.provisional_effects_json = _dump(
            [e.model_dump(mode="json") for r in records for e in r.sheet_effects]
        )
        if projected is not None:
            row.projected_state_json = _dump(_projected(projected, records))
        row.resolved_steps_json = _dump(
            [
                s.model_dump(mode="json")
                for s in (
                    _step(e, i) for i, e in enumerate(_events(session, row), start=1)
                )
            ]
        )
        plan.pending_decision = None
        row.current_pending_roll_request_id = None
        row.current_decision_request_id = None
        row.current_decision_snapshot_json = None
        if pause is None:
            row.status = ActionResolutionStatus.READY_FOR_NARRATION.value
            row.current_interaction_kind = SequenceInteractionKind.NONE.value
        elif isinstance(pause.roll, RollInstructionSnapshot):
            snapshot = pause.roll
            row.current_interaction_kind = SequenceInteractionKind.ROLL.value
            existing = session.execute(
                sa.select(PendingRollRequestORM).where(
                    PendingRollRequestORM.sequence_id == row.sequence_id,
                    PendingRollRequestORM.instruction_id
                    == str(snapshot.instruction_id),
                    PendingRollRequestORM.status == "pending",
                )
            ).scalar_one_or_none()
            if existing is None:
                if adjusted:
                    raise ActionSequenceIntegrityError(
                        "an adjusted roll lost its request"
                    )
                existing = PendingRollRequestORM(
                    request_id=str(uuid4()),
                    story_id=row.story_id,
                    session_id=row.session_id,
                    character_id=row.character_id,
                    originating_turn_id=row.originating_turn_id,
                    visibility=RollVisibility.PLAYER.value,
                    source_proposal_ref=(
                        f"{row.sequence_id}/{snapshot.operation_index}/"
                        f"{snapshot.die_index}"
                    ),
                    status="pending",
                    created_at=_now(),
                    schema_version=2,
                    sequence_id=row.sequence_id,
                    step_id=str(snapshot.step_id),
                    instruction_id=str(snapshot.instruction_id),
                    instruction_revision=snapshot.instruction_revision,
                    instruction_schema_version=snapshot.schema_version,
                    instruction_snapshot_json=snapshot.model_dump_json(),
                )
                session.add(existing)
            elif existing.instruction_snapshot_json != snapshot.model_dump_json():
                raise ActionSequenceIntegrityError(
                    "the pending roll's stored instruction is not reproduced"
                )
            row.current_pending_roll_request_id = existing.request_id
            plan.revisions[f"{snapshot.operation_index}:{snapshot.die_index}"] = (
                snapshot.instruction_revision
            )
        else:
            assert pause.decision is not None
            snapshot_d: MechanicalDecisionSnapshot = pause.decision[0]
            op, index = int(pause.decision[1]), int(pause.decision[2])
            row.current_interaction_kind = SequenceInteractionKind.DECISION.value
            row.current_decision_request_id = str(snapshot_d.decision_id)
            row.current_decision_snapshot_json = snapshot_d.model_dump_json()
            plan.pending_decision = (op, index)
        row.plan_json = plan.dump()
        if not claimed:  # an advancement already moved it when it claimed
            row.revision += 1
        row.updated_at = _now()
        session.flush()

    def _advance_result(
        self, session: Session, row: Any
    ) -> ActionResolutionAdvanceResult:
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        sequence_id = UUID(row.sequence_id)
        if row.status == ActionResolutionStatus.READY_FOR_NARRATION.value:
            return ActionResolutionAdvanceResult(
                sequence_id=sequence_id,
                interaction_phase=RpgInteractionPhase.READY_FOR_NARRATION,
            )
        step_index = 1 + sum(
            1
            for e in _events(session, row)
            if e.kind
            in (ResolvedStepKind.PLAYER_ROLL, ResolvedStepKind.MECHANICAL_DECISION)
        )
        if row.current_interaction_kind == SequenceInteractionKind.DECISION.value:
            assert row.current_decision_snapshot_json is not None
            snapshot = MechanicalDecisionSnapshot.model_validate_json(
                row.current_decision_snapshot_json
            )
            return ActionResolutionAdvanceResult(
                sequence_id=sequence_id,
                interaction_phase=RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
                pending_decision=decision_view(snapshot),
            )
        pending = session.get(
            PendingRollRequestORM, row.current_pending_roll_request_id
        )
        assert pending is not None and pending.instruction_snapshot_json is not None
        roll = RollInstructionSnapshot.model_validate_json(
            pending.instruction_snapshot_json
        )
        plan = _Plan.load(row.plan_json)
        known = (
            step_index
            if len(plan.proposals) == 1 and roll.purpose in _ONE_DIE
            else None
        )
        return ActionResolutionAdvanceResult(
            sequence_id=sequence_id,
            interaction_phase=RpgInteractionPhase.PENDING_ROLL,
            pending_roll=roll_view(
                roll,
                UUID(pending.request_id),
                step_index=step_index,
                known_step_count=known,
            ),
        )


# ---------------------------------------------------------------------------
# Validation (stored snapshot only)
# ---------------------------------------------------------------------------


def _validate_roll(
    snapshot: RollInstructionSnapshot,
    submission: RawPlayerRollSubmission | PhysicalAggregateRollSubmission,
) -> AcceptedRoll:
    """Validate *submission* against the stored *snapshot* alone and derive
    the dice it yields (#127 Validation 3–8). Raises a typed error and
    changes nothing on any mismatch."""
    if isinstance(submission, PhysicalAggregateRollSubmission):
        low, high = dice_engine.aggregate_range(snapshot)
        if not low <= submission.reported_aggregate <= high:
            raise PendingRollInvalidAggregateError(
                f"a reported total of {submission.reported_aggregate} is outside "
                f"[{low}, {high}]"
            )
        return AcceptedRoll(
            snapshot=snapshot,
            result=DiceResult(
                expression=snapshot.display_expression,
                raw_rolls=(),
                chosen=submission.reported_aggregate
                - dice_engine.modifier_total(snapshot, visible=True),
            ),
            kind=ResolvedStepKind.PLAYER_ROLL,
            pending_roll_request_id=submission.pending_roll_request_id,
            reported_aggregate=submission.reported_aggregate,
            source=RollSubmissionSource.PHYSICAL_SELF_REPORT.value,
        )
    expected = {t.term_id: t for t in snapshot.terms}
    submitted = [r.term_id for r in submission.term_results]
    if len(submitted) != len(set(submitted)) or set(submitted) != set(expected):
        raise PendingRollTermMismatchError(
            "each of the instruction's terms is submitted exactly once"
        )
    values: dict[object, tuple[int, ...]] = {}
    for result in submission.term_results:
        term = expected[result.term_id]
        if len(result.values) != term.count:
            raise PendingRollInvalidValueError(
                f"term {term.term_id} takes {term.count} value(s), got "
                f"{len(result.values)}"
            )
        if any(type(v) is not int or not 1 <= v <= term.sides for v in result.values):
            raise PendingRollInvalidValueError(
                f"term {term.term_id} takes integers from 1 to {term.sides}"
            )
        values[result.term_id] = tuple(result.values)
    derived = dice_engine.derive(snapshot, values)
    return AcceptedRoll(
        snapshot=snapshot,
        result=DiceResult(
            expression=snapshot.display_expression,
            raw_rolls=tuple(v for d in derived for v in d.values),
            chosen=sum(d.contribution_applied_subtotal for d in derived),
        ),
        kind=ResolvedStepKind.PLAYER_ROLL,
        pending_roll_request_id=submission.pending_roll_request_id,
        raw_values={str(d.term_id): list(d.values) for d in derived},
        source=submission.source,
    )


def _adjusted(plan: _Plan, snapshot: RollInstructionSnapshot, option_id: str) -> _Plan:
    """The sequence's plan with a pre-roll option applied to the operation it
    belongs to. The only admitted option is a Finesse weapon attack's choice
    of ability (``finesse_<ability>``); the same ability then serves its
    damage, since both are derived from the one selection."""
    op = snapshot.operation_index
    proposal = plan.proposals[op]
    selection = proposal.weapon_attack
    prefix = "finesse_"
    if selection is None or not option_id.startswith(prefix):
        raise ActionAdjustmentNotAllowedError(
            f"{option_id!r} is not an adjustment this adapter executes"
        )
    proposals = list(plan.proposals)
    proposals[op] = proposal.model_copy(
        update={
            "weapon_attack": selection.model_copy(
                update={"ability": option_id.removeprefix(prefix)}
            )
        }
    )
    key = f"{op}:{snapshot.die_index}"
    return _Plan(
        proposals=proposals,
        gm_cheating=plan.gm_cheating,
        player_rolls=plan.player_rolls,
        revisions={**plan.revisions, key: snapshot.instruction_revision + 1},
        pending_decision=plan.pending_decision,
    )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def _roll_payload(roll: AcceptedRoll, gm_cheating: bool) -> RollEventPayload:
    snapshot = roll.snapshot
    hidden = dice_engine.modifier_total(snapshot, visible=False)
    if roll.reported_aggregate is not None:
        total = roll.reported_aggregate + hidden
        face = (
            total - dice_engine.modifier_total(snapshot, visible=True) - hidden
            if dice_engine.single_face(snapshot)
            else None
        )
        return RollEventPayload(
            kind=roll.kind,  # type: ignore[arg-type]
            instruction_snapshot=snapshot,
            submission_source=RollSubmissionSource(roll.source),
            pending_roll_request_id=roll.pending_roll_request_id,
            raw_input_json=None,
            aggregate_input_json=_dump({"reported_aggregate": roll.reported_aggregate}),
            derived_selections_json="[]",
            subtotal=None,
            total=total,
            outcome=dice_engine.outcome(snapshot, total, face),  # type: ignore[arg-type]
            gm_cheating_at_roll=gm_cheating,
            contest_resolution=roll.contest_resolution,
        )
    if roll.raw_values is not None:
        values: dict[object, tuple[int, ...]] = {
            UUID(k): tuple(v) for k, v in roll.raw_values.items()
        }
    else:
        # A backend die: the dice service's raw values, which must be the
        # term's whole pool and reproduce its kept total.
        term = snapshot.terms[0]
        raw = roll.result.raw_rolls
        if len(snapshot.terms) != 1 or len(raw) != term.count:
            raise ActionSequenceIntegrityError(
                f"the dice service returned {len(raw)} value(s) for {term.count}"
            )
        values = {term.term_id: tuple(raw)}
    derived = dice_engine.derive(snapshot, values)
    subtotal = sum(d.contribution_applied_subtotal for d in derived)
    if subtotal != roll.result.chosen:
        raise ActionSequenceIntegrityError(
            "the dice's kept total does not match their selection"
        )
    total = (
        subtotal
        + dice_engine.modifier_total(snapshot, visible=True)
        + dice_engine.modifier_total(snapshot, visible=False)
    )
    face = (
        derived[0].values[derived[0].selected_indices[0]]
        if dice_engine.single_face(snapshot)
        else None
    )
    return RollEventPayload(
        kind=roll.kind,  # type: ignore[arg-type]
        instruction_snapshot=snapshot,
        submission_source=RollSubmissionSource(roll.source),
        pending_roll_request_id=roll.pending_roll_request_id,
        raw_input_json=_dump(
            [{"term_id": str(d.term_id), "values": list(d.values)} for d in derived]
        ),
        aggregate_input_json=None,
        derived_selections_json=_dump([d.model_dump(mode="json") for d in derived]),
        subtotal=subtotal,
        total=total,
        outcome=dice_engine.outcome(snapshot, total, face),  # type: ignore[arg-type]
        gm_cheating_at_roll=gm_cheating,
        contest_resolution=roll.contest_resolution,
    )


def _events(session: Session, row: Any) -> list[ActionResolutionEvent]:
    from afterworlds.persistence.orm.rpg import ActionResolutionEventORM

    session.flush()
    return [
        _event_from(e)
        for e in session.execute(
            sa.select(ActionResolutionEventORM)
            .where(ActionResolutionEventORM.sequence_id == row.sequence_id)
            .order_by(ActionResolutionEventORM.event_order)
        ).scalars()
    ]


def _append(
    session: Session,
    row: Any,
    kind: ResolvedStepKind,
    step_id: UUID,
    payload: RollEventPayload | AdjustmentEventPayload | MechanicalDecisionEventPayload,
    provenance: dict[str, Any],
    effects: list[Any],
) -> None:
    """Validate and add one event (committed with the advancement)."""
    from afterworlds.persistence.orm.rpg import ActionResolutionEventORM

    session.flush()
    order = (
        session.execute(
            sa.select(sa.func.max(ActionResolutionEventORM.event_order)).where(
                ActionResolutionEventORM.sequence_id == row.sequence_id
            )
        ).scalar()
        or 0
    ) + 1
    event = ActionResolutionEvent(
        event_id=uuid4(),
        sequence_id=UUID(row.sequence_id),
        step_id=step_id,
        story_id=UUID(row.story_id),
        session_id=UUID(row.session_id),
        character_id=UUID(row.character_id),
        event_order=order,
        kind=kind,
        mechanical_provenance=_dump({"adapter": _PROVENANCE, **provenance}),
        provisional_effects_json=_dump(effects),
        created_at=datetime.now(tz=UTC),
        payload=payload,
    )
    session.add(
        ActionResolutionEventORM(
            event_id=str(event.event_id),
            sequence_id=str(event.sequence_id),
            step_id=str(event.step_id),
            story_id=str(event.story_id),
            session_id=str(event.session_id),
            character_id=str(event.character_id),
            event_order=event.event_order,
            kind=event.kind.value,
            mechanical_provenance=event.mechanical_provenance,
            provisional_effects_json=event.provisional_effects_json,
            created_at=event.created_at.isoformat(),
            payload_json=event.payload.model_dump_json(),
        )
    )
    session.flush()


def _ledger_records(
    events: tuple[ActionResolutionEvent, ...], count: int
) -> tuple[ResolvedAdjudicationRecord, ...]:
    """Every operation's record, from the events that completed them, in
    operation order; incomplete or duplicated coverage is an integrity
    failure, never patched."""
    found: dict[int, ResolvedAdjudicationRecord] = {}
    for event in events:
        for item in json.loads(event.mechanical_provenance).get("records", []):
            index = int(item["operation_index"])
            if index in found:
                raise ActionSequenceIntegrityError(f"operation {index} completed twice")
            found[index] = ResolvedAdjudicationRecord.model_validate(item["record"])
    if sorted(found) != list(range(count)):
        raise ActionSequenceIntegrityError(
            "the event ledger does not complete every operation of the sequence"
        )
    return tuple(found[i] for i in range(count))


def _check_contests(
    events: tuple[ActionResolutionEvent, ...],
    records: tuple[ResolvedAdjudicationRecord, ...],
) -> None:
    """Every contest's one resolution: stored on its completing event, what
    its two immutable participant events reproduce (step identities
    included), and the very one its record carries (ADR-015b Group 17). A
    mismatch or a competing copy is an integrity failure, never patched."""
    from afterworlds.pipeline.rpg.contests import compare

    pairs: dict[UUID, list[ActionResolutionEvent]] = {}
    for event in events:
        payload = event.payload
        if (
            isinstance(payload, RollEventPayload)
            and payload.instruction_snapshot.contest
        ):
            pairs.setdefault(
                payload.instruction_snapshot.contest.contest_id, []
            ).append(event)
    for contest_id, pair in pairs.items():
        if len(pair) != 2:
            raise ActionSequenceIntegrityError(f"contest {contest_id} is incomplete")
        first, second = (e.payload for e in pair)
        assert isinstance(first, RollEventPayload)
        assert isinstance(second, RollEventPayload)
        link = first.instruction_snapshot.contest
        assert link is not None
        recomputed = compare(
            contest_id,
            (first.instruction_snapshot.roller, pair[0].step_id, first.total),
            (second.instruction_snapshot.roller, pair[1].step_id, second.total),
            link.certificate,
        )
        if first.contest_resolution is not None or (
            second.contest_resolution != recomputed
        ):
            raise ActionSequenceIntegrityError(
                f"contest {contest_id}'s resolution is not reproduced by its events"
            )
    stored = {
        e.payload.contest_resolution.contest_id: e.payload.contest_resolution
        for e in events
        if isinstance(e.payload, RollEventPayload) and e.payload.contest_resolution
    }
    for record in records:
        copy = record.contest_resolution
        if copy is not None and stored.get(copy.contest_id) != copy:
            raise ActionSequenceIntegrityError(
                f"contest {copy.contest_id}'s record disagrees with its "
                "completing event"
            )


def _step(event: ActionResolutionEvent, index: int) -> ResolvedSequenceStep:
    payload = event.payload
    effects = tuple(
        SheetEffect.model_validate(x)
        for x in json.loads(event.provisional_effects_json)
    )
    if isinstance(payload, RollEventPayload):
        derived = tuple(
            DerivedRollTermResult.model_validate(d)
            for d in json.loads(payload.derived_selections_json)
        )
        return ResolvedSequenceStep(
            sequence_id=event.sequence_id,
            step_id=event.step_id,
            step_index=index,
            kind=event.kind,
            instruction_snapshot=payload.instruction_snapshot,
            submission_source=payload.submission_source,
            reported_aggregate=(
                json.loads(payload.aggregate_input_json)["reported_aggregate"]
                if payload.aggregate_input_json
                else None
            ),
            raw_values_complete=payload.raw_input_json is not None,
            derived_term_results=derived,
            authoritative_total=payload.total,
            internal_outcome=payload.outcome,
            provisional_effects=effects,
        )
    if isinstance(payload, MechanicalDecisionEventPayload):
        return ResolvedSequenceStep(
            sequence_id=event.sequence_id,
            step_id=event.step_id,
            step_index=index,
            kind=event.kind,
            decision_snapshot=payload.decision_snapshot,
            accepted_option_id=payload.accepted_decision_option_id,
            provisional_effects=effects,
        )
    return ResolvedSequenceStep(
        sequence_id=event.sequence_id,
        step_id=event.step_id,
        step_index=index,
        kind=event.kind,
        instruction_snapshot=payload.resulting_instruction_snapshot,
        provisional_effects=effects,
    )


def _projected(
    prepared: PreparedTurn, records: list[ResolvedAdjudicationRecord]
) -> dict[str, Any]:
    """Each subject's state after the provisional effects so far: the
    projection later steps read, never Character Sheet authority (AC23)."""
    actor, subjects = advanced(
        prepared.sheet,
        prepared.subjects,
        tuple(e for r in records for e in r.sheet_effects),
    )

    def summary(subject: TurnSubject) -> dict[str, Any]:
        state = subject.stored.state
        return {
            "hit_points": (
                state.hit_points.model_dump(mode="json") if state.hit_points else None
            ),
            "death_state": (
                state.death_state.model_dump(mode="json") if state.death_state else None
            ),
            "conditions": sorted(c.condition.value for c in state.conditions or ()),
        }

    out = {f"character:{actor.subject_id}": summary(actor)}
    for (kind, sid), subject in sorted(subjects.items()):
        out[f"{kind}:{sid}"] = summary(subject)
    return out


def _recheck(session: Session, prepared: PreparedTurn) -> None:
    """Inside the write transaction: every subject, holding, the discovery
    snapshot and the coordination are still what the run read."""
    from afterworlds.services.dnd5e_state import coordination

    try:
        for subject in (prepared.sheet, *prepared.subjects.values()):
            creature = isinstance(subject, TurnCreature)
            require_unchanged(
                session,
                subject.subject_id,
                subject.stored.revision,
                subject.stored.binding,
                kind="creature" if creature else "character",
            )
            require_holdings_unchanged(
                session,
                Holder(
                    HolderKind.CREATURE if creature else HolderKind.CHARACTER,
                    subject.subject_id,
                ),
                subject.items,
            )
        if prepared.discovery is not None:
            require_story_unchanged(session, *prepared.discovery)
        if prepared.coordination is not None:
            now = coordination.read(session, prepared.coordination.story_id)
            if now.revision != prepared.coordination.revision:
                raise StaleRevisionError("the turn coordination changed")
    except StaleRevisionError as exc:
        raise ActionSequenceStateConflictError(str(exc)) from exc


def audit_rows(events: tuple[ActionResolutionEvent, ...], turn_id: UUID) -> list[Any]:
    """The final ``rpg_roll_audit`` rows: one per roll event, every column
    from that event's envelope, payload or embedded snapshot alone (ADR-015b
    Final Audit Projection). Adjustment and decision events never produce
    one."""
    from afterworlds.persistence.orm.rpg import RpgRollAuditORM

    visibility = {
        ResolvedStepKind.PLAYER_ROLL: (RollVisibility.PLAYER.value, "player"),
        ResolvedStepKind.AI_ROLL: (RollVisibility.SHOWN.value, "ai"),
        ResolvedStepKind.HIDDEN_ROLL: (RollVisibility.HIDDEN.value, "hidden"),
    }
    rows = []
    for event in events:
        payload = event.payload
        if not isinstance(payload, RollEventPayload):
            continue
        snapshot = payload.instruction_snapshot
        complete = payload.raw_input_json is not None
        raw = (
            [
                v
                for d in json.loads(payload.derived_selections_json)
                for v in d["values"]
            ]
            if complete
            else []
        )
        shown, source = visibility[event.kind]
        rows.append(
            RpgRollAuditORM(
                turn_id=str(turn_id),
                story_id=str(event.story_id),
                session_id=str(event.session_id),
                character_id=str(event.character_id),
                check_label=snapshot.display_label,
                visibility=shown,
                expression=snapshot.display_expression,
                raw_rolls_json=json.dumps(raw),
                modifiers_json=json.dumps(
                    [m.model_dump(mode="json") for m in snapshot.modifier_components]
                ),
                total=payload.total,
                dc=snapshot.dc,
                outcome=payload.outcome,
                source=source,
                gm_cheating_at_roll=payload.gm_cheating_at_roll,
                sheet_effects_json=event.provisional_effects_json,
                created_at=event.created_at.isoformat(),
                sequence_id=str(event.sequence_id),
                step_id=str(event.step_id),
                pending_roll_request_id=(
                    str(payload.pending_roll_request_id)
                    if payload.pending_roll_request_id
                    else None
                ),
                instruction_id=str(snapshot.instruction_id),
                instruction_revision=snapshot.instruction_revision,
                instruction_schema_version=snapshot.schema_version,
                instruction_snapshot_json=snapshot.model_dump_json(),
                submission_source=payload.submission_source.value,
                raw_values_complete=complete,
                contest_resolution_json=(
                    payload.contest_resolution.model_dump_json()
                    if payload.contest_resolution
                    else None
                ),
            )
        )
    return rows
