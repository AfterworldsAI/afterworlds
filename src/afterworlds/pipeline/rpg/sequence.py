"""ActionResolutionService — CRD Issue 15b.

Owns deterministic ActionResolutionSequence transitions only. Never returns
``OrchestrationResult`` and never invokes the pipeline (15b-21) — HTTP
handlers and the orchestrator's resume seam consume this service's typed
results, they do not reach into sequence/pending-roll ORM state directly.

v1 scope, honestly bounded by the "Rules Package carries no structured
numeric/mechanical data" Known Unknown: every sequence created here is a
single-step check/save/attack roll (``ActionResolutionService.start_sequence``
via ``D20RulesSystemAdapter.build_check_instruction``). Multi-step linked
sequences (multiattack, attack-then-damage) are representable by this
service's persistence and advancement logic — nothing here assumes exactly
one step — but nothing in Phase 2 currently *generates* a second step, since
that requires structured damage-dice data the curated Rules Package does not
have. ``apply_adjustment`` and ``submit_decision`` are implemented against
the real typed contract but always resolve to their "not offered"/"invalid"
error in v1, because no adapter path populates adjustment options or raises
a mechanical decision yet.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    ActionResolutionStatus,
    DiceSelectionRule,
    ResolvedStepKind,
    RollContribution,
    RollSubmissionSource,
    RpgInteractionPhase,
    SequenceInteractionKind,
)
from afterworlds.models.rpg import (
    ActionResolutionAdvanceResult,
    ActionResolutionEvent,
    AdjustmentEventPayload,
    DerivedRollTermResult,
    PlayerAdjustmentOptionView,
    PlayerModifierView,
    PlayerRollInstructionView,
    PlayerRollTermView,
    ReadyActionResolutionBundle,
    ResolvedSequenceStep,
    RollEventPayload,
    RollInstructionSnapshot,
    SequenceProgressView,
)
from afterworlds.pipeline.rpg.models import (
    ActionAdjustmentNotAllowedError,
    ActionSequenceAlreadyCompletedError,
    ActionSequenceNotFoundError,
    ActionSequenceStateConflictError,
    MechanicalDecisionInvalidError,
    PendingRollInvalidAggregateError,
    PendingRollInvalidValueError,
    PendingRollNotFoundError,
    PendingRollNotPlayerVisibleError,
    PendingRollRevisionMismatchError,
    PendingRollTermMismatchError,
    SequenceNotReadyForNarrationError,
)
from afterworlds.pipeline.rpg.pending import PendingRollAlreadyConsumedError

if TYPE_CHECKING:
    from afterworlds.models.character_sheet import Dnd5eCharacterSheet
    from afterworlds.models.rpg import (
        PhysicalAggregateRollSubmission,
        RawPlayerRollSubmission,
        RollProposal,
    )
    from afterworlds.models.rules_package import ActiveRuleSlice, RuleOverride
    from afterworlds.persistence.orm.rpg import (
        ActionResolutionSequenceORM,
    )
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.dice import DiceService


class _PendingHandle(NamedTuple):
    """Detached, minimal view of a loaded PendingRollRequestORM row."""

    sequence_id: UUID
    step_id: UUID


class UnresolvedSequenceHandle(NamedTuple):
    """Detached summary of an unresolved sequence for the orchestrator's gate.

    CRD Issue 15b — generalizes ADR-015 Decision 10's single-pending-roll
    intercept to any unresolved sequence state (pending roll, pending
    mechanical decision, or ready_for_narration).
    """

    sequence_id: UUID
    interaction_phase: RpgInteractionPhase
    redirect_message: str


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class ActionResolutionService:
    """Deterministic ActionResolutionSequence lifecycle manager (CRD Issue 15b).

    Args:
        adapter: D20RulesSystemAdapter for instruction building/resolution.
        dice_service: DiceService for AI/hidden/backend-generated term rolls.
        session_factory: factory returning a fresh SQLAlchemy Session, used
            only by ``load_unresolved_for_story`` (opens/closes its own
            read session, mirroring
            ``PendingRollRequestService.load_pending_for_story`` — must run
            before the outer transaction opens). Every other method receives
            the caller's outer-transaction session explicitly.
    """

    def __init__(
        self,
        adapter: D20RulesSystemAdapter,
        dice_service: DiceService,
        session_factory: Callable[[], Session],
    ) -> None:
        self._adapter = adapter
        self._dice_service = dice_service
        self._session_factory = session_factory

    def load_unresolved_for_story(
        self, story_id: UUID
    ) -> UnresolvedSequenceHandle | None:
        """Return a summary of the story's unresolved sequence, or None.

        Opens and closes its own read session so this does not participate
        in the outer transaction. Must be called before the outer
        transaction opens (pre-transaction intercept in the orchestrator).
        """
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        session = self._session_factory()
        try:
            seq_row = (
                session.query(ActionResolutionSequenceORM)
                .filter(
                    ActionResolutionSequenceORM.story_id == str(story_id),
                    ActionResolutionSequenceORM.status.in_(
                        ("active", "ready_for_narration")
                    ),
                )
                .first()
            )
            if seq_row is None:
                return None
            if seq_row.status == ActionResolutionStatus.READY_FOR_NARRATION.value:
                phase = RpgInteractionPhase.READY_FOR_NARRATION
                message = "A resolved action is ready to narrate — resuming."
            elif (
                seq_row.current_interaction_kind
                == SequenceInteractionKind.DECISION.value
            ):
                phase = RpgInteractionPhase.PENDING_MECHANICAL_DECISION
                message = "A mechanical decision is pending."
            else:
                phase = RpgInteractionPhase.PENDING_ROLL
                message = "Roll the requested check to continue."
                if seq_row.current_pending_roll_request_id is not None:
                    from afterworlds.persistence.orm.rpg import (
                        PendingRollRequestORM,
                    )

                    pending_row = (
                        session.query(PendingRollRequestORM)
                        .filter_by(request_id=seq_row.current_pending_roll_request_id)
                        .one_or_none()
                    )
                    if (
                        pending_row is not None
                        and pending_row.instruction_snapshot_json
                    ):
                        snapshot = RollInstructionSnapshot.model_validate_json(
                            pending_row.instruction_snapshot_json
                        )
                        message = (
                            f"Roll needed: {snapshot.display_expression} "
                            f"for {snapshot.display_label}"
                        )
            return UnresolvedSequenceHandle(
                sequence_id=UUID(seq_row.sequence_id),
                interaction_phase=phase,
                redirect_message=message,
            )
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # start_sequence
    # -----------------------------------------------------------------------

    def start_sequence(
        self,
        session: Session,
        *,
        story_id: UUID,
        node_id: UUID,
        character_id: UUID,
        session_id: UUID,
        originating_turn_id: UUID,
        proposal: RollProposal,
        sheet: Dnd5eCharacterSheet,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
    ) -> ActionResolutionAdvanceResult:
        """Create a new ActionResolutionSequence and its first pending roll.

        Must run inside the caller's outer transaction, immediately before
        commit, so the uniqueness check and write are atomic (mirrors
        ``PendingRollRequestService.check_no_pending_for_story``'s pattern).
        Raises ``ActionSequenceStateConflictError`` if an unresolved sequence
        already exists for the story — the partial unique index on
        ``action_resolution_sequences`` is the DB-level backstop for this.
        """
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        existing = (
            session.query(ActionResolutionSequenceORM)
            .filter(
                ActionResolutionSequenceORM.story_id == str(story_id),
                ActionResolutionSequenceORM.status.in_(
                    ("active", "ready_for_narration")
                ),
            )
            .first()
        )
        if existing is not None:
            raise ActionSequenceStateConflictError(
                f"Story {story_id} already has an unresolved sequence "
                f"{existing.sequence_id!r}; cannot start another"
            )

        sequence_id = uuid4()
        step_id = uuid4()
        instruction_id = uuid4()

        instruction = self._adapter.build_check_instruction(
            proposal,
            sheet,
            rule_slice,
            overrides,
            sequence_id=sequence_id,
            step_id=step_id,
            instruction_id=instruction_id,
        )

        now = _now_iso()
        sequence_row = ActionResolutionSequenceORM(
            sequence_id=str(sequence_id),
            story_id=str(story_id),
            node_id=str(node_id),
            character_id=str(character_id),
            originating_turn_id=str(originating_turn_id),
            session_id=str(session_id),
            status=ActionResolutionStatus.ACTIVE.value,
            current_interaction_kind=SequenceInteractionKind.ROLL.value,
            current_pending_roll_request_id=None,  # set below once request_id exists
            resolved_steps_json="[]",
            projected_state_json="{}",
            provisional_effects_json="[]",
            created_at=now,
            updated_at=now,
        )
        session.add(sequence_row)
        session.flush()

        request_id = uuid4()
        pending_row = PendingRollRequestORM(
            request_id=str(request_id),
            story_id=str(story_id),
            session_id=str(session_id),
            character_id=str(character_id),
            originating_turn_id=str(originating_turn_id),
            visibility=proposal.visibility.value,
            source_proposal_ref=f"{proposal.subsystem_tag}/{proposal.check_label}",
            status="pending",
            created_at=now,
            adapter_context_hash=None,
            sequence_id=str(sequence_id),
            step_id=str(step_id),
            instruction_id=str(instruction_id),
            instruction_revision=instruction.instruction_revision,
            instruction_schema_version=instruction.schema_version,
            instruction_snapshot_json=json.dumps(instruction.model_dump(mode="json")),
        )
        session.add(pending_row)
        sequence_row.current_pending_roll_request_id = str(request_id)
        session.flush()

        return ActionResolutionAdvanceResult(
            sequence_id=sequence_id,
            interaction_phase=RpgInteractionPhase.PENDING_ROLL,
            pending_roll=_to_player_roll_view(instruction, request_id, step_index=1),
        )

    # -----------------------------------------------------------------------
    # apply_adjustment
    # -----------------------------------------------------------------------

    def apply_adjustment(
        self, session: Session, *, pending_roll_request_id: UUID, option_id: str
    ) -> ActionResolutionAdvanceResult:
        """Apply a typed adjustment to the current pending roll.

        v1: no adapter path populates ``adjustment_options`` (advantage/
        disadvantage is decided at instruction-build time from the model's
        proposal text, not offered as a post-hoc player choice; parameterized
        mechanics like spell-slot upcasting are explicitly deferred — see the
        "Parameterized adjustments" Known Unknown). Every call therefore
        raises ``ActionAdjustmentNotAllowedError`` today, but the lookup
        logic is real: it will accept a match the moment an adapter path
        populates a non-empty ``adjustment_options`` tuple.
        """
        pending, instruction = self._load_pending_and_instruction(
            session, pending_roll_request_id
        )
        match = next(
            (o for o in instruction.adjustment_options if o.option_id == option_id),
            None,
        )
        if match is None:
            raise ActionAdjustmentNotAllowedError(
                f"Option {option_id!r} is not offered on pending roll "
                f"{pending_roll_request_id!r}"
            )
        # Unreachable in v1 (adjustment_options is always empty), but shaped
        # for the day an adapter path offers one: bump instruction_revision.
        revised = instruction.model_copy(
            update={"instruction_revision": instruction.instruction_revision + 1}
        )
        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        row = (
            session.query(PendingRollRequestORM)
            .filter_by(request_id=str(pending_roll_request_id))
            .one()
        )
        row.instruction_revision = revised.instruction_revision
        row.instruction_snapshot_json = json.dumps(revised.model_dump(mode="json"))
        session.flush()

        seq_row = (
            session.query(ActionResolutionSequenceORM)
            .filter_by(sequence_id=str(pending.sequence_id))
            .one()
        )
        _append_event(
            session,
            sequence_id=pending.sequence_id,
            step_id=pending.step_id,
            story_id=UUID(seq_row.story_id),
            session_id=UUID(seq_row.session_id),
            character_id=UUID(seq_row.character_id),
            kind=ResolvedStepKind.ADJUSTMENT,
            provisional_effects_json="[]",
            payload=AdjustmentEventPayload(
                resulting_instruction_snapshot=revised,
                accepted_adjustment_option_id=option_id,
            ),
        )
        session.flush()

        step_index = _step_index_for(session, pending.sequence_id)
        return ActionResolutionAdvanceResult(
            sequence_id=revised.sequence_id,
            interaction_phase=RpgInteractionPhase.PENDING_ROLL,
            pending_roll=_to_player_roll_view(
                revised, pending_roll_request_id, step_index=step_index
            ),
        )

    # -----------------------------------------------------------------------
    # submit_decision
    # -----------------------------------------------------------------------

    def submit_decision(
        self,
        session: Session,
        *,
        sequence_id: UUID,
        decision_request_id: UUID,
        option_id: str,
    ) -> ActionResolutionAdvanceResult:
        """Submit a mechanical-decision selection.

        v1: no adapter path ever sets ``current_interaction_kind=DECISION`` —
        no curated mechanic requires a mandatory pre-roll choice beyond the
        adjustments already excluded above. Always raises
        ``MechanicalDecisionInvalidError`` today; shaped for real use once a
        decision-generating adapter path exists.
        """
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        seq = (
            session.query(ActionResolutionSequenceORM)
            .filter_by(sequence_id=str(sequence_id))
            .one_or_none()
        )
        if seq is None:
            raise ActionSequenceNotFoundError(f"Sequence {sequence_id!r} not found")
        if (
            seq.current_interaction_kind != SequenceInteractionKind.DECISION.value
            or seq.current_decision_request_id != str(decision_request_id)
        ):
            raise MechanicalDecisionInvalidError(
                f"Sequence {sequence_id!r} has no pending decision "
                f"{decision_request_id!r}"
            )
        raise MechanicalDecisionInvalidError(
            f"Option {option_id!r} rejected: no decision-generating adapter "
            "path exists in v1"
        )

    # -----------------------------------------------------------------------
    # consume_roll
    # -----------------------------------------------------------------------

    def consume_roll(
        self,
        session: Session,
        *,
        submission: RawPlayerRollSubmission | PhysicalAggregateRollSubmission,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        gm_cheating: bool,
    ) -> ActionResolutionAdvanceResult:
        """Validate, resolve, and atomically consume a player roll submission.

        Advances the owning sequence. v1: every sequence is single-step, so
        a successful consume always transitions the sequence straight to
        ``READY_FOR_NARRATION`` — see the module docstring for why (no
        adapter path generates a second linked step yet).
        """
        pending, instruction = self._load_pending_and_instruction(
            session, submission.pending_roll_request_id
        )
        if instruction.instruction_revision != submission.expected_instruction_revision:
            raise PendingRollRevisionMismatchError(
                f"Pending roll {submission.pending_roll_request_id!r} is at "
                f"revision {instruction.instruction_revision}, submission "
                f"expected {submission.expected_instruction_revision}"
            )

        from afterworlds.models.rpg import (
            PhysicalAggregateRollSubmission,
            PlayerRollTermResult,
        )

        submitted_term_results: tuple[PlayerRollTermResult, ...] | None = None
        reported_aggregate: int | None = None
        derived_term_results: tuple[DerivedRollTermResult, ...] = ()
        raw_input_json: str | None = None
        aggregate_input_json: str | None = None
        subtotal: int | None = None

        if isinstance(submission, PhysicalAggregateRollSubmission):
            min_total, max_total = self._adapter.aggregate_range(instruction)
            if not (min_total <= submission.reported_aggregate <= max_total):
                raise PendingRollInvalidAggregateError(
                    f"Reported aggregate {submission.reported_aggregate} outside "
                    f"legal range [{min_total}, {max_total}] for instruction "
                    f"{instruction.instruction_id!r}"
                )
            record = self._adapter.resolve_aggregate_snapshot(
                instruction=instruction,
                reported_aggregate=submission.reported_aggregate,
                rule_slice=rule_slice,
                overrides=overrides,
                gm_cheating=gm_cheating,
            )
            raw_values_complete = False
            submission_source = RollSubmissionSource.PHYSICAL_SELF_REPORT
            reported_aggregate = submission.reported_aggregate
            # Aggregate-only physical reports carry no per-die values — no raw
            # selection is derivable, and dice/modifier are not decomposable
            # from a single reported number (ADR-015b's Aggregate-only
            # physical-report projection).
            aggregate_input_json = json.dumps(
                {"reported_aggregate": submission.reported_aggregate}
            )
        else:
            term_results = self._validate_raw_submission(instruction, submission)
            record = self._adapter.resolve_snapshot(
                instruction=instruction,
                term_results=term_results,
                rule_slice=rule_slice,
                overrides=overrides,
                source="player",
                gm_cheating=gm_cheating,
            )
            raw_values_complete = True
            submission_source = (
                RollSubmissionSource.INLINE_UI
                if submission.source == "inline_ui"
                else RollSubmissionSource.PHYSICAL_SELF_REPORT
            )
            submitted_term_results = submission.term_results
            derived_term_results = _build_derived_term_results(
                instruction, term_results
            )
            raw_input_json = json.dumps(
                [r.model_dump(mode="json") for r in submission.term_results]
            )
            subtotal = sum(
                t.contribution_applied_subtotal for t in derived_term_results
            )

        derived_selections_json = json.dumps(
            [t.model_dump(mode="json") for t in derived_term_results]
        )

        writer_view = self._adapter.to_writer_view(record)

        from afterworlds.persistence.orm.rpg import (
            ActionResolutionSequenceORM,
            PendingRollRequestORM,
        )

        # Atomic conditional consume: two concurrent transactions can both
        # load this row as 'pending' via _load_pending_and_instruction above
        # before either commits. An unconditional status assignment would
        # let both proceed and both append an event. The WHERE status =
        # 'pending' predicate plus rowcount check makes the second writer
        # lose cleanly instead — mirrors the retired mark_consumed path's
        # atomic guard.
        result = session.execute(
            sa.update(PendingRollRequestORM)
            .where(
                PendingRollRequestORM.request_id
                == str(submission.pending_roll_request_id),
                PendingRollRequestORM.status == "pending",
            )
            .values(status="consumed")
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise PendingRollAlreadyConsumedError(
                f"Pending roll {submission.pending_roll_request_id!r} was "
                "consumed by a concurrent request"
            )
        session.flush()

        seq_row = (
            session.query(ActionResolutionSequenceORM)
            .filter_by(sequence_id=str(pending.sequence_id))
            .one()
        )
        step = ResolvedSequenceStep(
            sequence_id=pending.sequence_id,
            step_id=pending.step_id,
            step_index=_step_index_for(session, pending.sequence_id),
            kind=ResolvedStepKind.PLAYER_ROLL,
            instruction_snapshot=instruction,
            submission_source=submission_source,
            submitted_term_results=submitted_term_results,
            reported_aggregate=reported_aggregate,
            raw_values_complete=raw_values_complete,
            derived_term_results=derived_term_results,
            authoritative_total=record.total,
            internal_outcome=record.outcome,
            writer_view=writer_view,
            provisional_effects=record.sheet_effects,
        )

        resolved_steps = _load_resolved_steps(seq_row)
        resolved_steps.append(step)
        seq_row.resolved_steps_json = json.dumps(
            [s.model_dump(mode="json") for s in resolved_steps]
        )
        provisional = json.loads(seq_row.provisional_effects_json or "[]")
        provisional.extend(e.model_dump(mode="json") for e in record.sheet_effects)
        seq_row.provisional_effects_json = json.dumps(provisional)

        _append_event(
            session,
            sequence_id=pending.sequence_id,
            step_id=pending.step_id,
            story_id=UUID(seq_row.story_id),
            session_id=UUID(seq_row.session_id),
            character_id=UUID(seq_row.character_id),
            kind=ResolvedStepKind.PLAYER_ROLL,
            provisional_effects_json=json.dumps(
                [e.model_dump(mode="json") for e in record.sheet_effects]
            ),
            payload=RollEventPayload(
                kind=ResolvedStepKind.PLAYER_ROLL,
                instruction_snapshot=instruction,
                submission_source=submission_source,
                pending_roll_request_id=submission.pending_roll_request_id,
                raw_input_json=raw_input_json,
                aggregate_input_json=aggregate_input_json,
                derived_selections_json=derived_selections_json,
                subtotal=subtotal,
                total=record.total,
                outcome=record.outcome,
                gm_cheating_at_roll=record.gm_cheating_at_roll,
            ),
        )

        # v1: no code path generates a second linked step (see module
        # docstring) — a resolved roll always completes the sequence.
        seq_row.status = ActionResolutionStatus.READY_FOR_NARRATION.value
        seq_row.current_interaction_kind = SequenceInteractionKind.NONE.value
        seq_row.current_pending_roll_request_id = None
        seq_row.updated_at = _now_iso()
        session.flush()

        return ActionResolutionAdvanceResult(
            sequence_id=pending.sequence_id,
            interaction_phase=RpgInteractionPhase.READY_FOR_NARRATION,
        )

    def _validate_raw_submission(
        self,
        instruction: RollInstructionSnapshot,
        submission: RawPlayerRollSubmission,
    ) -> dict[UUID, tuple[int, ...]]:
        expected_ids = {t.term_id for t in instruction.terms}
        submitted_ids = [r.term_id for r in submission.term_results]
        if set(submitted_ids) != expected_ids or len(submitted_ids) != len(
            expected_ids
        ):
            raise PendingRollTermMismatchError(
                f"Submitted term IDs {submitted_ids} do not exactly match "
                f"instruction terms {sorted(expected_ids)}"
            )
        by_id = {r.term_id: r.values for r in submission.term_results}
        terms_by_id = {t.term_id: t for t in instruction.terms}
        for term_id, values in by_id.items():
            term = terms_by_id[term_id]
            if len(values) != term.count:
                raise PendingRollInvalidValueError(
                    f"Term {term_id} expects {term.count} value(s), got {len(values)}"
                )
            if any(not (1 <= v <= term.sides) for v in values):
                raise PendingRollInvalidValueError(
                    f"Term {term_id} values {values} outside [1, {term.sides}]"
                )
        return by_id

    # -----------------------------------------------------------------------
    # get_ready_bundle
    # -----------------------------------------------------------------------

    def get_ready_bundle(
        self, session: Session, *, sequence_id: UUID
    ) -> ReadyActionResolutionBundle:
        """Load the complete internal bundle for a READY_FOR_NARRATION sequence."""
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        seq_row = (
            session.query(ActionResolutionSequenceORM)
            .filter_by(sequence_id=str(sequence_id))
            .one_or_none()
        )
        if seq_row is None:
            raise ActionSequenceNotFoundError(f"Sequence {sequence_id!r} not found")
        if seq_row.status == ActionResolutionStatus.COMPLETED.value:
            raise ActionSequenceAlreadyCompletedError(
                f"Sequence {sequence_id!r} is already completed"
            )
        if seq_row.status != ActionResolutionStatus.READY_FOR_NARRATION.value:
            raise SequenceNotReadyForNarrationError(
                f"Sequence {sequence_id!r} is {seq_row.status!r}, "
                "not ready_for_narration"
            )

        resolved_steps = _load_resolved_steps(seq_row)
        writer_views = tuple(s.writer_view for s in resolved_steps if s.writer_view)
        provisional = tuple(
            e for step in resolved_steps for e in step.provisional_effects
        )
        turn_row = session.execute(
            sa.text("SELECT user_input FROM turns WHERE turn_id = :tid"),
            {"tid": seq_row.originating_turn_id},
        ).fetchone()
        originating_user_input = turn_row.user_input if turn_row is not None else ""

        return ReadyActionResolutionBundle(
            sequence_id=sequence_id,
            story_id=UUID(seq_row.story_id),
            node_id=UUID(seq_row.node_id),
            character_id=UUID(seq_row.character_id),
            session_id=UUID(seq_row.session_id),
            originating_turn_id=UUID(seq_row.originating_turn_id),
            originating_user_input=originating_user_input,
            resolved_steps=tuple(resolved_steps),
            writer_views=writer_views,
            accumulated_provisional_effects=provisional,
        )

    def mark_completed(self, session: Session, *, sequence_id: UUID) -> None:
        """Mark a sequence COMPLETED after its final narration has committed.

        Called by the orchestrator's shared transactional-resolution method,
        inside the same outer transaction as the Turn/audit/effects commit.
        """
        from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

        seq_row = (
            session.query(ActionResolutionSequenceORM)
            .filter_by(sequence_id=str(sequence_id))
            .one()
        )
        seq_row.status = ActionResolutionStatus.COMPLETED.value
        seq_row.updated_at = _now_iso()

    # -----------------------------------------------------------------------
    # internal helpers
    # -----------------------------------------------------------------------

    def _load_pending_and_instruction(
        self, session: Session, pending_roll_request_id: UUID
    ) -> tuple[_PendingHandle, RollInstructionSnapshot]:
        from afterworlds.persistence.orm.rpg import PendingRollRequestORM

        pending = (
            session.query(PendingRollRequestORM)
            .filter_by(request_id=str(pending_roll_request_id))
            .one_or_none()
        )
        if pending is None:
            raise PendingRollNotFoundError(
                f"Pending roll {pending_roll_request_id!r} not found"
            )
        if pending.status != "pending":
            raise PendingRollAlreadyConsumedError(
                f"Pending roll {pending_roll_request_id!r} is {pending.status!r}, "
                "not pending"
            )
        if pending.visibility != "player":
            raise PendingRollNotPlayerVisibleError(
                f"Pending roll {pending_roll_request_id!r} is not player-visible"
            )
        if pending.instruction_snapshot_json is None:
            raise PendingRollNotFoundError(
                f"Pending roll {pending_roll_request_id!r} has no structured "
                "instruction snapshot (legacy or corrupt row)"
            )
        instruction = RollInstructionSnapshot.model_validate_json(
            pending.instruction_snapshot_json
        )
        handle = _PendingHandle(
            sequence_id=UUID(pending.sequence_id), step_id=UUID(pending.step_id)
        )
        return handle, instruction


def _step_index_for(session: Session, sequence_id: UUID) -> int:
    from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM

    seq_row = (
        session.query(ActionResolutionSequenceORM)
        .filter_by(sequence_id=str(sequence_id))
        .one()
    )
    return len(_load_resolved_steps(seq_row)) + 1


def _load_resolved_steps(
    seq_row: ActionResolutionSequenceORM,
) -> list[ResolvedSequenceStep]:
    raw = json.loads(seq_row.resolved_steps_json or "[]")
    return [ResolvedSequenceStep.model_validate(item) for item in raw]


# CRD Issue 15b (ADR-015b 15b-34) — the d20 system is the only adapter that
# exists today; this identifies which rules engine produced an event, for a
# future multi-system codebase. The ADR types the field but does not define
# its content beyond "provenance".
_MECHANICAL_PROVENANCE = "d20_rules_system_adapter"


def _build_derived_term_results(
    instruction: RollInstructionSnapshot,
    term_results: dict[UUID, tuple[int, ...]],
) -> tuple[DerivedRollTermResult, ...]:
    """Reconstruct per-term selected-die provenance from already-decided values.

    Independent of ``D20RulesSystemAdapter._reduce_term``'s subtotal/crit-die
    computation — this only re-serializes *which* indices were kept, for the
    event ledger's ``derived_selections_json`` and
    ``ResolvedSequenceStep.derived_term_results``. It makes no adjudication
    decision and cannot diverge from ``_reduce_term``'s sum for any term:
    KEEP_HIGHEST/KEEP_LOWEST select the same multiset of values (ties are
    immaterial to the sum), and SUM_ALL always selects every index.
    """
    results: list[DerivedRollTermResult] = []
    for term in instruction.terms:
        values = term_results.get(term.term_id, ())
        if term.selection_rule is DiceSelectionRule.SUM_ALL:
            selected_indices = tuple(range(len(values)))
        else:
            keep_n = term.keep_count or 1
            order = sorted(
                range(len(values)),
                key=lambda i: values[i],
                reverse=(term.selection_rule is DiceSelectionRule.KEEP_HIGHEST),
            )
            selected_indices = tuple(sorted(order[:keep_n]))
        subtotal = sum(values[i] for i in selected_indices)
        signed_subtotal = (
            subtotal if term.contribution is RollContribution.ADD else -subtotal
        )
        results.append(
            DerivedRollTermResult(
                term_id=term.term_id,
                values=values,
                selected_indices=selected_indices,
                contribution_applied_subtotal=signed_subtotal,
            )
        )
    return tuple(results)


def _next_event_order(session: Session, sequence_id: UUID) -> int:
    result = session.execute(
        sa.text(
            "SELECT COALESCE(MAX(event_order), 0) FROM action_resolution_events "
            "WHERE sequence_id = :sid"
        ),
        {"sid": str(sequence_id)},
    ).scalar_one()
    return int(result) + 1


def _append_event(
    session: Session,
    *,
    sequence_id: UUID,
    step_id: UUID,
    story_id: UUID,
    session_id: UUID,
    character_id: UUID,
    kind: ResolvedStepKind,
    provisional_effects_json: str,
    payload: RollEventPayload | AdjustmentEventPayload,
) -> None:
    """Validate and persist one ActionResolutionEvent (ADR-015b 15b-34).

    Must run inside the caller's outer (intermediate) transaction, alongside
    the sequence-advancing write — both commit or neither does. The unique
    ``(sequence_id, event_order)`` index is the DB-level backstop against a
    duplicate or racing write for the same sequence position.
    """
    from afterworlds.persistence.orm.rpg import ActionResolutionEventORM

    event = ActionResolutionEvent(
        event_id=uuid4(),
        sequence_id=sequence_id,
        step_id=step_id,
        story_id=story_id,
        session_id=session_id,
        character_id=character_id,
        event_order=_next_event_order(session, sequence_id),
        kind=kind,
        mechanical_provenance=_MECHANICAL_PROVENANCE,
        provisional_effects_json=provisional_effects_json,
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
            payload_json=json.dumps(event.payload.model_dump(mode="json")),
        )
    )


def _to_player_roll_view(
    instruction: RollInstructionSnapshot,
    pending_roll_request_id: UUID,
    *,
    step_index: int,
) -> PlayerRollInstructionView:
    from afterworlds.models.enums import ModifierVisibility

    visible_modifiers = tuple(
        PlayerModifierView(modifier_id=m.modifier_id, label=m.label, value=m.value)
        for m in instruction.modifier_components
        if m.visibility is ModifierVisibility.PLAYER_VISIBLE
    )
    return PlayerRollInstructionView(
        pending_roll_request_id=pending_roll_request_id,
        sequence_id=instruction.sequence_id,
        instruction_id=instruction.instruction_id,
        instruction_revision=instruction.instruction_revision,
        purpose=instruction.purpose,
        interaction_phase=RpgInteractionPhase.PENDING_ROLL,
        progress=SequenceProgressView(
            step_index=step_index,
            known_step_count=step_index,
            step_label=instruction.display_label,
            sequence_label=None,
        ),
        display_label=instruction.display_label,
        display_expression=instruction.display_expression,
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
            for t in instruction.terms
        ),
        visible_modifiers=visible_modifiers,
        visible_modifier_total=sum(m.value for m in visible_modifiers),
        adjustment_options=tuple(
            PlayerAdjustmentOptionView(
                option_id=o.option_id,
                player_visible_label=o.player_visible_label,
                resource_preview=o.resource_preview,
            )
            for o in instruction.adjustment_options
        ),
    )


__all__ = ["ActionResolutionService"]
