"""Story Bible service — CRUD and context assembly for narrative canon.

This module owns:
  - The Events Ledger tiered inclusion policy (``EVENTS_LEDGER_N``,
    ``ALWAYS_INCLUDE_SIGNIFICANCE``).  These constants are the single source
    of truth for tiered inclusion behaviour; callers must not reimplement
    the policy.
  - Confirmation enforcement for static-partition field updates.
  - Soft-delete semantics: Story Bible records are never hard-deleted through
    this service.
  - Dynamic field versioning: every ``update_dynamic_field`` call records the
    prior value in ``sb_dynamic_field_history`` before writing the new value.
    See ADR-0006.
  - The ``get_active_context_window`` method that the Context Builder
    (Issue 8) will call.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    EventKind,
    EventSignificance,
    ProposalStatus,
    ProposalType,
    TargetDomain,
    ThreadStatus,
)
from afterworlds.models.extractor import (
    EventProposal,
    ExtractorProposalSet,
    ExtractorRoutingSummary,
    LockedFactProposal,
    SoftFactProposal,
    TransientStateProposal,
    UnresolvedThreadProposal,
)
from afterworlds.models.story_bible import (
    CastEntry,
    DynamicFieldHistory,
    Event,
    ForbiddenFact,
    LockedFact,
    ProvisionalProposal,
    RelationshipLedger,
    StoryBibleContext,
    StoryBibleSetting,
    UnresolvedThread,
)
from afterworlds.persistence.orm.story_bible import (
    SBCastEntryORM,
    SBDynamicFieldHistoryORM,
    SBEventORM,
    SBForbiddenFactORM,
    SBLockedFactORM,
    SBProvisionalStagingORM,
    SBRelationshipLedgerORM,
    SBSettingORM,
    SBUnresolvedThreadORM,
)

# ---------------------------------------------------------------------------
# Tiered inclusion policy constants
# ---------------------------------------------------------------------------

#: Starting value for the Events Ledger N window.  Configurable — tune with
#: testing.  See ADR-0005 and known_unknowns.md.
EVENTS_LEDGER_N: int = 15

#: Significance values that qualify for always-include in the tiered inclusion
#: policy.  This frozenset is the *single source of truth* — callers must not
#: reimplement this set.  See ADR-0005.
ALWAYS_INCLUDE_SIGNIFICANCE: frozenset[EventSignificance] = frozenset(
    {
        EventSignificance.CHARACTER_DEATH,
        EventSignificance.LOCKED_FACT_ESTABLISHED,
        EventSignificance.MAJOR_PLOT_TURN,
        EventSignificance.RELATIONSHIP_CHANGE,
        EventSignificance.WORLD_STATE_CHANGE,
        EventSignificance.FORBIDDEN_FACT_ESTABLISHED,
    }
)

# ---------------------------------------------------------------------------
# Field partition sets for CastEntry
# ---------------------------------------------------------------------------

#: Static fields on CastEntry — require Sojourner confirmation to change.
_CAST_STATIC_FIELDS: frozenset[str] = frozenset(
    {"name", "role", "traits", "goals", "secrets", "background"}
)

#: Dynamic fields on CastEntry — Extractor-maintained; prior values
#: preserved in history on every update.
_CAST_DYNAMIC_FIELDS: frozenset[str] = frozenset(
    {"current_location", "current_status", "is_alive", "notes"}
)

#: Required Python type per (domain-value, field) pair.
#: Enforced by the routing layer before any canon write.
#: bool is NOT a subclass of str, so isinstance checks are unambiguous.
_FIELD_VALUE_TYPES: dict[tuple[str, str], type] = {
    ("character", "is_alive"): bool,
    ("character", "current_location"): str,
    ("character", "current_status"): str,
    ("character", "notes"): str,
    ("relationship", "current_status_description"): str,
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ConfirmationRequiredError(Exception):
    """Raised when a static field update or locked-fact ratification is
    attempted without an explicit confirmation signal."""


class EntityNotFoundError(Exception):
    """Raised when a required entity cannot be located."""


# ---------------------------------------------------------------------------
# ORM ↔ Pydantic conversion helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _setting_orm_to_model(row: SBSettingORM) -> StoryBibleSetting:
    return StoryBibleSetting(
        setting_id=UUID(row.setting_id),
        story_id=UUID(row.story_id),
        summary=row.summary,
        world_rules=tuple(row.world_rules),
        geography=row.geography,
        time_period=row.time_period,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _cast_orm_to_model(row: SBCastEntryORM) -> CastEntry:
    from afterworlds.models.enums import CastRole

    return CastEntry(
        cast_id=UUID(row.cast_id),
        story_id=UUID(row.story_id),
        name=row.static_name,
        role=CastRole(row.static_role),
        traits=tuple(row.static_traits),
        goals=tuple(row.static_goals),
        secrets=tuple(row.static_secrets),
        background=row.static_background,
        current_location=row.dynamic_current_location,
        current_status=row.dynamic_current_status,
        is_alive=row.dynamic_is_alive,
        notes=row.dynamic_notes,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
        source_turn_id=row.source_turn_id,
    )


def _locked_fact_orm_to_model(row: SBLockedFactORM) -> LockedFact:
    return LockedFact(
        locked_fact_id=UUID(row.locked_fact_id),
        story_id=UUID(row.story_id),
        fact_text=row.fact_text,
        source_turn_id=row.source_turn_id,
        confirmation_timestamp=(
            datetime.fromisoformat(row.confirmation_timestamp)
            if row.confirmation_timestamp
            else None
        ),
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _forbidden_fact_orm_to_model(row: SBForbiddenFactORM) -> ForbiddenFact:
    return ForbiddenFact(
        forbidden_fact_id=UUID(row.forbidden_fact_id),
        story_id=UUID(row.story_id),
        fact_text=row.fact_text,
        source=row.source,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _event_orm_to_model(row: SBEventORM) -> Event:
    return Event(
        event_id=UUID(row.event_id),
        story_id=UUID(row.story_id),
        description=row.description,
        significance=EventSignificance(row.significance),
        event_kind=EventKind(row.event_kind),
        source_turn_id=row.source_turn_id,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _relationship_orm_to_model(row: SBRelationshipLedgerORM) -> RelationshipLedger:
    from afterworlds.models.enums import RelationshipType

    return RelationshipLedger(
        relationship_id=UUID(row.relationship_id),
        story_id=UUID(row.story_id),
        subject_cast_id=UUID(row.subject_cast_id),
        object_cast_id=UUID(row.object_cast_id),
        relationship_type=RelationshipType(row.relationship_type),
        current_status_description=row.current_status_description,
        source_turn_id=row.source_turn_id,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
        updated_at=datetime.fromisoformat(row.updated_at),
    )


def _thread_orm_to_model(row: SBUnresolvedThreadORM) -> UnresolvedThread:
    return UnresolvedThread(
        thread_id=UUID(row.thread_id),
        story_id=UUID(row.story_id),
        description=row.description,
        source_turn_id=row.source_turn_id,
        status=ThreadStatus(row.status),
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _proposal_orm_to_model(row: SBProvisionalStagingORM) -> ProvisionalProposal:
    return ProvisionalProposal(
        proposal_id=UUID(row.proposal_id),
        story_id=UUID(row.story_id),
        proposal_type=ProposalType(row.proposal_type),
        target_entity_type=row.target_entity_type,
        target_entity_id=row.target_entity_id,
        proposed_value=dict(row.proposed_value),
        source_turn_id=row.source_turn_id,
        status=ProposalStatus(row.status),
        requires_confirmation=row.requires_confirmation,
        is_active=row.is_active,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _history_orm_to_model(row: SBDynamicFieldHistoryORM) -> DynamicFieldHistory:
    old: object = None
    if row.old_value is not None:
        old = json.loads(row.old_value)
    return DynamicFieldHistory(
        history_id=UUID(row.history_id),
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        field_name=row.field_name,
        old_value=old,
        changed_at=datetime.fromisoformat(row.changed_at),
        source_turn_id=row.source_turn_id,
    )


# ---------------------------------------------------------------------------
# StoryBibleService
# ---------------------------------------------------------------------------


class StoryBibleService:
    """Service layer for the Story Bible.

    All mutation methods enforce partition semantics:
    - Static fields require ``confirmed=True``.
    - Dynamic field updates preserve prior values via history table.
    - Story Bible records are never hard-deleted.
    - Provisional entries are never returned as ratified canon.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Context window assembly
    # ------------------------------------------------------------------

    def get_active_context_window(self, story_id: UUID) -> StoryBibleContext:
        """Assemble the Story Bible context payload for the stable prefix.

        Applies the Events Ledger tiered inclusion policy:
        returns the ``EVENTS_LEDGER_N`` most recent events *plus* any events
        whose significance is in ``ALWAYS_INCLUDE_SIGNIFICANCE`` regardless
        of recency.

        This is the method the Context Builder (Issue 8) will call.
        Returns a structured, typed payload — not a raw result set.
        """
        sid = str(story_id)

        # Setting
        setting_row = (
            self._session.execute(
                select(SBSettingORM)
                .where(
                    SBSettingORM.story_id == sid,
                    SBSettingORM.is_active.is_(True),
                )
                .order_by(SBSettingORM.created_at.desc())
            )
            .scalars()
            .first()
        )
        setting = _setting_orm_to_model(setting_row) if setting_row else None

        # Cast (active entries only, deterministic order)
        cast_rows = (
            self._session.execute(
                select(SBCastEntryORM)
                .where(
                    SBCastEntryORM.story_id == sid,
                    SBCastEntryORM.is_active.is_(True),
                )
                .order_by(SBCastEntryORM.created_at.asc(), SBCastEntryORM.cast_id.asc())
            )
            .scalars()
            .all()
        )
        cast = tuple(_cast_orm_to_model(r) for r in cast_rows)

        # Locked facts
        locked_facts = self.get_locked_facts(story_id)

        # Forbidden facts
        forbidden_facts = self.get_forbidden_facts(story_id)

        # Relationship ledger (active entries, deterministic order)
        # Only include relationships where both cast members are still active,
        # so ctx.cast and ctx.relationship_ledger are self-consistent.
        active_cast_ids = {str(c.cast_id) for c in cast}
        rel_rows = (
            self._session.execute(
                select(SBRelationshipLedgerORM)
                .where(
                    SBRelationshipLedgerORM.story_id == sid,
                    SBRelationshipLedgerORM.is_active.is_(True),
                )
                .order_by(SBRelationshipLedgerORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        relationship_ledger = tuple(
            _relationship_orm_to_model(r)
            for r in rel_rows
            if r.subject_cast_id in active_cast_ids
            and r.object_cast_id in active_cast_ids
        )

        # Active plot threads (open, active, deterministic order)
        thread_rows = (
            self._session.execute(
                select(SBUnresolvedThreadORM)
                .where(
                    SBUnresolvedThreadORM.story_id == sid,
                    SBUnresolvedThreadORM.status == ThreadStatus.OPEN.value,
                    SBUnresolvedThreadORM.is_active.is_(True),
                )
                .order_by(SBUnresolvedThreadORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        active_plot_threads = tuple(_thread_orm_to_model(r) for r in thread_rows)

        # Events Ledger — tiered inclusion
        events = self._get_tiered_events(sid)

        return StoryBibleContext(
            story_id=story_id,
            setting=setting,
            cast=cast,
            locked_facts=tuple(locked_facts),
            forbidden_facts=tuple(forbidden_facts),
            relationship_ledger=relationship_ledger,
            active_plot_threads=active_plot_threads,
            events=tuple(events),
        )

    def _get_tiered_events(self, story_id_str: str) -> list[Event]:
        """Apply tiered inclusion policy and return the events subset.

        Policy (single source of truth):
        1. The N most recent active events (ordered by created_at DESC).
        2. Any active event whose significance is in
           ``ALWAYS_INCLUDE_SIGNIFICANCE``, regardless of recency.
        3. Deduplication: an event in both sets appears only once.
        """
        all_rows = (
            self._session.execute(
                select(SBEventORM)
                .where(
                    SBEventORM.story_id == story_id_str,
                    SBEventORM.is_active.is_(True),
                )
                .order_by(SBEventORM.created_at.desc(), SBEventORM.event_id.asc())
            )
            .scalars()
            .all()
        )

        included_ids: set[str] = set()
        result: list[Event] = []

        # Pass 1 — N most recent
        for row in all_rows[:EVENTS_LEDGER_N]:
            included_ids.add(row.event_id)
            result.append(_event_orm_to_model(row))

        # Pass 2 — always-include by significance (dedup by ID)
        for row in all_rows:
            if (
                row.event_id not in included_ids
                and EventSignificance(row.significance) in ALWAYS_INCLUDE_SIGNIFICANCE
            ):
                included_ids.add(row.event_id)
                result.append(_event_orm_to_model(row))

        return result

    # ------------------------------------------------------------------
    # Fact queries
    # ------------------------------------------------------------------

    def get_locked_facts(self, story_id: UUID) -> list[LockedFact]:
        """Return all active locked facts for a story as a distinct set."""
        rows = (
            self._session.execute(
                select(SBLockedFactORM)
                .where(
                    SBLockedFactORM.story_id == str(story_id),
                    SBLockedFactORM.is_active.is_(True),
                )
                .order_by(SBLockedFactORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [_locked_fact_orm_to_model(r) for r in rows]

    def get_forbidden_facts(self, story_id: UUID) -> list[ForbiddenFact]:
        """Return all active forbidden facts for a story as a distinct set."""
        rows = (
            self._session.execute(
                select(SBForbiddenFactORM)
                .where(
                    SBForbiddenFactORM.story_id == str(story_id),
                    SBForbiddenFactORM.is_active.is_(True),
                )
                .order_by(SBForbiddenFactORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [_forbidden_fact_orm_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Cast
    # ------------------------------------------------------------------

    def get_character(self, story_id: UUID, character_id: UUID) -> CastEntry | None:
        """Return the full cast entry, or None if not found or inactive."""
        row = self._session.get(SBCastEntryORM, str(character_id))
        if row is None or row.story_id != str(story_id) or not row.is_active:
            return None
        return _cast_orm_to_model(row)

    def update_static_field(
        self,
        story_id: UUID,
        entity_id: UUID,
        field: str,
        value: object,
        *,
        confirmed: bool = False,
    ) -> CastEntry:
        """Update a static-partition field on a CastEntry.

        Raises ``ConfirmationRequiredError`` if ``confirmed`` is False.
        Raises ``ValueError`` if ``field`` is not a recognised static field.
        Raises ``EntityNotFoundError`` if the cast entry does not exist.
        """
        if not confirmed:
            raise ConfirmationRequiredError(
                f"Updating static field '{field}' requires explicit Sojourner "
                "confirmation.  Pass confirmed=True to proceed."
            )
        if field not in _CAST_STATIC_FIELDS:
            raise ValueError(
                f"'{field}' is not a static field on CastEntry.  "
                f"Static fields: {sorted(_CAST_STATIC_FIELDS)}"
            )
        row = self._session.get(SBCastEntryORM, str(entity_id))
        if row is None or row.story_id != str(story_id) or not row.is_active:
            raise EntityNotFoundError(
                f"CastEntry {entity_id} not found for story {story_id}."
            )
        col_name = f"static_{field}"
        old_val = getattr(row, col_name)
        _set_cast_column(row, col_name, value)
        try:
            model = _cast_orm_to_model(row)
        except (ValueError, KeyError) as exc:
            # Restore the original value so the ORM object stays consistent.
            setattr(row, col_name, old_val)
            raise ValueError(
                f"Invalid value {value!r} for static field '{field}': {exc}"
            ) from exc
        self._session.flush()
        return model

    def update_dynamic_field(
        self,
        story_id: UUID,
        entity_id: UUID,
        field: str,
        value: object,
        *,
        source_turn_id: str | None = None,
        session: Session | None = None,
    ) -> CastEntry:
        """Update a dynamic-partition field on a CastEntry.

        No confirmation required.  The prior value is preserved in
        ``sb_dynamic_field_history`` before the update is applied.
        See ADR-0006.

        Args:
            session: optional caller-supplied SQLAlchemy session (Issue 12c).
                When supplied, all reads and writes go through that session
                so the operation participates in the caller's outer
                transaction or SAVEPOINT.  When ``None``, the
                constructor-injected ``self._session`` is used (Issue 4
                standalone behavior).  The session is never stored on the
                service instance.

        Raises ``ValueError`` if ``field`` is not a recognised dynamic field.
        Raises ``EntityNotFoundError`` if the cast entry does not exist.
        """
        target = session if session is not None else self._session
        if field not in _CAST_DYNAMIC_FIELDS:
            raise ValueError(
                f"'{field}' is not a dynamic field on CastEntry.  "
                f"Dynamic fields: {sorted(_CAST_DYNAMIC_FIELDS)}"
            )
        row = target.get(SBCastEntryORM, str(entity_id))
        if row is None or row.story_id != str(story_id) or not row.is_active:
            raise EntityNotFoundError(
                f"CastEntry {entity_id} not found for story {story_id}."
            )
        col_name = f"dynamic_{field}"
        old_val: object = getattr(row, col_name)
        _set_cast_column(row, col_name, value)
        # Validate the candidate state before writing anything to the session.
        try:
            model = _cast_orm_to_model(row)
        except (ValueError, KeyError) as exc:
            # Restore the original value so the ORM object stays consistent
            # and no mutation or history row reaches the session.
            setattr(row, col_name, old_val)
            raise ValueError(
                f"Invalid value {value!r} for dynamic field '{field}': {exc}"
            ) from exc
        # Validation passed — record history and flush.
        history_row = SBDynamicFieldHistoryORM(
            history_id=str(uuid4()),
            entity_type="cast_entry",
            entity_id=str(entity_id),
            field_name=field,
            old_value=json.dumps(old_val) if old_val is not None else None,
            changed_at=_now_iso(),
            source_turn_id=source_turn_id,
        )
        target.add(history_row)
        target.flush()
        return model

    # ------------------------------------------------------------------
    # Events Ledger
    # ------------------------------------------------------------------

    def add_event(
        self,
        story_id: UUID,
        event: Event,
        *,
        session: Session | None = None,
    ) -> Event:
        """Append an event to the Events Ledger.  Never overwrites.

        Args:
            session: optional caller-supplied SQLAlchemy session (Issue 12c).
                When supplied, the append goes through that session so it
                participates in the caller's outer transaction.  When
                ``None``, ``self._session`` is used.  The session is never
                stored on the service instance.
        """
        target = session if session is not None else self._session
        row = SBEventORM(
            event_id=str(event.event_id),
            story_id=str(story_id),
            description=event.description,
            significance=event.significance.value,
            event_kind=event.event_kind.value,
            source_turn_id=event.source_turn_id,
            is_active=True,
            created_at=event.created_at.isoformat(),
        )
        target.add(row)
        target.flush()
        return _event_orm_to_model(row)

    # ------------------------------------------------------------------
    # Provisional staging
    # ------------------------------------------------------------------

    def stage_proposed_update(
        self, story_id: UUID, proposal: ProvisionalProposal
    ) -> ProvisionalProposal:
        """Write a proposal to the provisional staging area.

        Does NOT touch ratified canon.  The proposal status is set to
        PENDING regardless of what the caller passed.
        """
        requires_conf = proposal.proposal_type == ProposalType.LOCKED_FACT
        row = SBProvisionalStagingORM(
            proposal_id=str(proposal.proposal_id),
            story_id=str(story_id),
            proposal_type=proposal.proposal_type.value,
            target_entity_type=proposal.target_entity_type,
            target_entity_id=proposal.target_entity_id,
            proposed_value=proposal.proposed_value,
            source_turn_id=proposal.source_turn_id,
            status=ProposalStatus.PENDING.value,
            requires_confirmation=requires_conf,
            is_active=True,
            created_at=proposal.created_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _proposal_orm_to_model(row)

    def ratify_update(
        self, proposal_id: UUID, *, confirmed: bool = False
    ) -> ProvisionalProposal:
        """Promote a staged proposal to ratified canon.

        For ``locked_fact`` proposals, ``confirmed=True`` is required;
        raises ``ConfirmationRequiredError`` otherwise.

        Ratification effects by type:
        - ``locked_fact``:  creates a ``LockedFact`` entry in
          ``sb_locked_facts`` after confirmation.
        - ``unresolved_thread``: creates an ``UnresolvedThread`` in
          ``sb_unresolved_threads``.
        - ``soft_fact`` / ``transient_state``: marks the proposal
          ``RATIFIED`` only.  Dynamic field application is performed by
          ``route_extractor_proposals``; these proposal types arriving here
          are treated as already-applied audit rows.

        Events are not ratified through this method; ``EventProposal``
        instances bypass staging and go directly to ``add_event`` via
        ``route_extractor_proposals``.

        Raises ``EntityNotFoundError`` if the proposal does not exist.
        """
        row = self._session.get(SBProvisionalStagingORM, str(proposal_id))
        if row is None:
            raise EntityNotFoundError(f"Proposal {proposal_id} not found.")

        if not row.is_active:
            raise EntityNotFoundError(
                f"Proposal {proposal_id} has been soft-deleted and cannot be ratified."
            )

        if row.status != ProposalStatus.PENDING.value:
            raise ValueError(
                f"Proposal {proposal_id} is already {row.status}; cannot ratify."
            )

        ptype = ProposalType(row.proposal_type)
        if ptype == ProposalType.LOCKED_FACT and not confirmed:
            raise ConfirmationRequiredError(
                "Ratifying a locked_fact proposal requires explicit confirmation.  "
                "Pass confirmed=True to proceed."
            )

        now = _now_iso()

        if ptype == ProposalType.LOCKED_FACT:
            fact_text = row.proposed_value.get("fact_text", "")
            if not fact_text:
                raise ValueError(
                    f"Proposal {proposal_id} is missing required 'fact_text' "
                    "in proposed_value; cannot write blank canon entry."
                )
            row.status = ProposalStatus.RATIFIED.value
            lf_row = SBLockedFactORM(
                locked_fact_id=str(uuid4()),
                story_id=row.story_id,
                fact_text=fact_text,
                source_turn_id=row.source_turn_id,
                confirmation_timestamp=now,
                is_active=True,
                created_at=now,
            )
            self._session.add(lf_row)

        elif ptype == ProposalType.UNRESOLVED_THREAD:
            description = row.proposed_value.get("description", "")
            if not description:
                raise ValueError(
                    f"Proposal {proposal_id} is missing required 'description' "
                    "in proposed_value; cannot write blank canon entry."
                )
            row.status = ProposalStatus.RATIFIED.value
            thread_row = SBUnresolvedThreadORM(
                thread_id=str(uuid4()),
                story_id=row.story_id,
                description=description,
                source_turn_id=row.source_turn_id,
                status=ThreadStatus.OPEN.value,
                is_active=True,
                created_at=now,
            )
            self._session.add(thread_row)

        else:
            # soft_fact / transient_state: mark RATIFIED only.
            # Dynamic field application is handled by route_extractor_proposals;
            # these proposals arrive here as already-applied audit rows.
            row.status = ProposalStatus.RATIFIED.value

        self._session.flush()
        return _proposal_orm_to_model(row)

    def reject_update(self, proposal_id: UUID) -> ProvisionalProposal:
        """Mark a staged proposal as rejected.

        The proposal record is retained (never deleted).
        Raises ``EntityNotFoundError`` if the proposal does not exist.
        """
        row = self._session.get(SBProvisionalStagingORM, str(proposal_id))
        if row is None:
            raise EntityNotFoundError(f"Proposal {proposal_id} not found.")
        if not row.is_active:
            raise EntityNotFoundError(
                f"Proposal {proposal_id} has been soft-deleted and cannot be rejected."
            )
        if row.status != ProposalStatus.PENDING.value:
            raise ValueError(
                f"Proposal {proposal_id} is already {row.status}; cannot reject."
            )
        row.status = ProposalStatus.REJECTED.value
        self._session.flush()
        return _proposal_orm_to_model(row)

    def list_pending_locked_fact_proposals(
        self, story_id: UUID
    ) -> list[ProvisionalProposal]:
        """Return active PENDING LOCKED_FACT proposals for a story.

        These are the proposals that require Sojourner confirmation before the
        locked fact becomes canon.  Other proposal types are excluded.
        """
        rows = (
            self._session.execute(
                select(SBProvisionalStagingORM)
                .where(
                    SBProvisionalStagingORM.story_id == str(story_id),
                    SBProvisionalStagingORM.proposal_type
                    == ProposalType.LOCKED_FACT.value,
                    SBProvisionalStagingORM.status == ProposalStatus.PENDING.value,
                    SBProvisionalStagingORM.is_active.is_(True),
                )
                .order_by(SBProvisionalStagingORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [_proposal_orm_to_model(r) for r in rows]

    def get_writable_fields(self, target_domain: TargetDomain) -> frozenset[str]:
        """Return the set of writable field names for a target domain.

        CHARACTER domain exposes the dynamic field allowlist.
        RELATIONSHIP domain exposes ``current_status_description`` only.
        WORLD domain is not writable in v1 — returns an empty frozenset.
        """
        if target_domain == TargetDomain.CHARACTER:
            return _CAST_DYNAMIC_FIELDS
        elif target_domain == TargetDomain.RELATIONSHIP:
            return frozenset({"current_status_description"})
        else:
            return frozenset()

    def find_character_by_name(
        self,
        story_id: UUID,
        name: str,
        *,
        session: Session | None = None,
    ) -> UUID:
        """Return the cast_id for a character matching ``name`` (case-insensitive).

        Args:
            session: optional caller-supplied SQLAlchemy session (Issue 12c).
                When supplied, the read goes through that session so it
                sees in-flight writes from the caller's outer transaction.
                When ``None``, ``self._session`` is used.

        Raises ``EntityNotFoundError`` if no active cast entry matches or if
        multiple active entries match (ambiguous — caller cannot safely pick one).
        """
        target = session if session is not None else self._session
        rows = (
            target.execute(
                select(SBCastEntryORM).where(
                    SBCastEntryORM.story_id == str(story_id),
                    func.lower(SBCastEntryORM.static_name) == name.lower(),
                    SBCastEntryORM.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            raise EntityNotFoundError(
                f"No active cast entry with name {name!r} found in story {story_id}."
            )
        if len(rows) > 1:
            raise EntityNotFoundError(
                f"Ambiguous character name {name!r}: {len(rows)} active cast entries "
                f"match case-insensitively in story {story_id}. "
                "Natural-key resolution requires a unique match."
            )
        return UUID(rows[0].cast_id)

    def route_extractor_proposals(
        self,
        story_id: UUID,
        turn_id: UUID,
        proposal_set: ExtractorProposalSet,
        *,
        session: Session | None = None,
    ) -> ExtractorRoutingSummary:
        """Route all Extractor proposals transactionally.

        Session and transaction semantics (Issue 12c):
        - ``session is None`` (default): preserve Issue 10 standalone
          behavior.  All writes go through ``self._session`` and the method
          commits at the end on success.  Caller is responsible for rollback
          on error.
        - ``session`` supplied: route under ``session.begin_nested()`` so the
          Extractor's writes become a SQLite SAVEPOINT inside the caller's
          outer transaction.  All writes are performed against the supplied
          session (NOT against ``self._session``).  The SAVEPOINT is
          committed iff routing succeeds; an exception causes the SAVEPOINT
          to roll back (Extractor side effects undone) without affecting
          the outer transaction.  The outer transaction's commit / rollback
          remains the caller's responsibility — typically the Issue 12c
          orchestrator at the Contradiction gate.

        Routing policy:
        - ``LockedFactProposal``: staged as PENDING — requires Sojourner
          confirmation via ``ratify_update`` before becoming canon.
        - ``SoftFactProposal`` / ``TransientStateProposal``: natural key resolved,
          dynamic field applied, staged as RATIFIED audit row.
        - ``UnresolvedThreadProposal``: canonical thread created, staged as
          RATIFIED audit row.
        - ``EventProposal``: written directly to ``sb_events`` via ``add_event``;
          no staging row created.
        """
        if session is not None:
            # Caller-supplied session: route under a SAVEPOINT inside the
            # caller's outer transaction.  Thread the session explicitly
            # through every read/write — never mutate ``self._session``.
            # Doing so would race with concurrent turns sharing the same
            # service instance (Codex P1 from PR #87 first round).
            with session.begin_nested():
                return self._execute_routing_body(
                    story_id, turn_id, proposal_set, session, commit=False
                )
        # Standalone path (Issue 10): use ``self._session`` and commit at end.
        return self._execute_routing_body(
            story_id, turn_id, proposal_set, self._session, commit=True
        )

    def _execute_routing_body(
        self,
        story_id: UUID,
        turn_id: UUID,
        proposal_set: ExtractorProposalSet,
        target_session: Session,
        *,
        commit: bool,
    ) -> ExtractorRoutingSummary:
        """Routing body parameterized over the target session.

        All reads, writes, and helper-method calls thread ``target_session``
        through explicitly.  ``self._session`` is NEVER mutated during
        routing — that pattern would create a thread-safety race if the
        same service instance handled concurrent turns under FastAPI or
        any other concurrent caller.  When ``commit`` is True the standalone
        Issue 10 behavior commits the session at the end; when False the
        caller's transaction or SAVEPOINT owns the commit boundary.
        """
        locked_fact_staged_ids: list[UUID] = []
        soft_fact_staged_ids: list[UUID] = []
        transient_state_staged_ids: list[UUID] = []
        unresolved_thread_staged_ids: list[UUID] = []
        event_ids: list[UUID] = []

        now = _now_iso()
        turn_id_str = str(turn_id)
        story_id_str = str(story_id)

        for proposal in proposal_set.proposals:
            if isinstance(proposal, LockedFactProposal):
                proposal_id = uuid4()
                staging_row = SBProvisionalStagingORM(
                    proposal_id=str(proposal_id),
                    story_id=story_id_str,
                    proposal_type=ProposalType.LOCKED_FACT.value,
                    proposed_value={"fact_text": proposal.fact_text},
                    source_turn_id=turn_id_str,
                    status=ProposalStatus.PENDING.value,
                    requires_confirmation=True,
                    is_active=True,
                    created_at=now,
                )
                target_session.add(staging_row)
                target_session.flush()
                locked_fact_staged_ids.append(proposal_id)

            elif isinstance(proposal, (SoftFactProposal, TransientStateProposal)):
                is_soft = isinstance(proposal, SoftFactProposal)
                ptype = (
                    ProposalType.SOFT_FACT if is_soft else ProposalType.TRANSIENT_STATE
                )

                writable = self.get_writable_fields(proposal.target_domain)
                if proposal.target_field not in writable:
                    raise ValueError(
                        f"Field '{proposal.target_field}' is not writable for domain "
                        f"'{proposal.target_domain}'. "
                        f"Writable fields: {sorted(writable) if writable else '(none)'}"
                    )

                _check_field_value_type(
                    proposal.target_domain,
                    proposal.target_field,
                    proposal.proposed_value,
                )

                if proposal.target_domain == TargetDomain.CHARACTER:
                    entity_uuid = self.find_character_by_name(
                        story_id,
                        proposal.target_natural_key,
                        session=target_session,
                    )
                    self.update_dynamic_field(
                        story_id,
                        entity_uuid,
                        proposal.target_field,
                        proposal.proposed_value,
                        source_turn_id=turn_id_str,
                        session=target_session,
                    )
                    entity_id_str = str(entity_uuid)

                else:
                    subject_name, object_name = _parse_relationship_natural_key(
                        proposal.target_natural_key
                    )
                    subject_uuid = self.find_character_by_name(
                        story_id, subject_name, session=target_session
                    )
                    object_uuid = self.find_character_by_name(
                        story_id, object_name, session=target_session
                    )
                    rel_row = self._find_relationship_row(
                        story_id,
                        subject_uuid,
                        object_uuid,
                        session=target_session,
                    )
                    self._update_relationship_field(
                        rel_row,
                        proposal.target_field,
                        proposal.proposed_value,
                        turn_id_str,
                        session=target_session,
                    )
                    entity_id_str = rel_row.relationship_id

                proposal_id = uuid4()
                audit_row = SBProvisionalStagingORM(
                    proposal_id=str(proposal_id),
                    story_id=story_id_str,
                    proposal_type=ptype.value,
                    target_entity_id=entity_id_str,
                    proposed_value={
                        "target_domain": proposal.target_domain.value,
                        "target_natural_key": proposal.target_natural_key,
                        "target_field": proposal.target_field,
                        "proposed_value": proposal.proposed_value,
                    },
                    source_turn_id=turn_id_str,
                    status=ProposalStatus.RATIFIED.value,
                    requires_confirmation=False,
                    is_active=True,
                    created_at=now,
                )
                target_session.add(audit_row)
                target_session.flush()

                if is_soft:
                    soft_fact_staged_ids.append(proposal_id)
                else:
                    transient_state_staged_ids.append(proposal_id)

            elif isinstance(proposal, UnresolvedThreadProposal):
                thread_id = uuid4()
                thread_row = SBUnresolvedThreadORM(
                    thread_id=str(thread_id),
                    story_id=story_id_str,
                    description=proposal.description,
                    source_turn_id=turn_id_str,
                    status=ThreadStatus.OPEN.value,
                    is_active=True,
                    created_at=now,
                )
                target_session.add(thread_row)

                proposal_id = uuid4()
                audit_row = SBProvisionalStagingORM(
                    proposal_id=str(proposal_id),
                    story_id=story_id_str,
                    proposal_type=ProposalType.UNRESOLVED_THREAD.value,
                    proposed_value={"description": proposal.description},
                    source_turn_id=turn_id_str,
                    status=ProposalStatus.RATIFIED.value,
                    requires_confirmation=False,
                    is_active=True,
                    created_at=now,
                )
                target_session.add(audit_row)
                target_session.flush()
                unresolved_thread_staged_ids.append(proposal_id)

            elif isinstance(proposal, EventProposal):
                event = Event(
                    story_id=story_id,
                    description=proposal.description,
                    significance=proposal.significance,
                    event_kind=proposal.event_kind,
                    source_turn_id=turn_id_str,
                    created_at=datetime.now(UTC),
                )
                saved = self.add_event(story_id, event, session=target_session)
                event_ids.append(saved.event_id)

        if commit:
            target_session.commit()
        return ExtractorRoutingSummary(
            locked_fact_staged_ids=locked_fact_staged_ids,
            soft_fact_staged_ids=soft_fact_staged_ids,
            transient_state_staged_ids=transient_state_staged_ids,
            unresolved_thread_staged_ids=unresolved_thread_staged_ids,
            event_ids=event_ids,
        )

    def _find_relationship_row(
        self,
        story_id: UUID,
        subject_uuid: UUID,
        object_uuid: UUID,
        *,
        session: Session | None = None,
    ) -> SBRelationshipLedgerORM:
        """Find the active relationship row.

        Args:
            session: optional caller-supplied SQLAlchemy session (Issue 12c).
                When supplied, the read goes through that session so it
                sees in-flight writes from the caller's outer transaction.
                When ``None``, ``self._session`` is used.
        """
        target = session if session is not None else self._session
        rows = (
            target.execute(
                select(SBRelationshipLedgerORM).where(
                    SBRelationshipLedgerORM.story_id == str(story_id),
                    SBRelationshipLedgerORM.subject_cast_id == str(subject_uuid),
                    SBRelationshipLedgerORM.object_cast_id == str(object_uuid),
                    SBRelationshipLedgerORM.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            raise EntityNotFoundError(
                f"No active relationship from '{subject_uuid}' to '{object_uuid}' "
                f"in story {story_id}."
            )
        if len(rows) > 1:
            raise EntityNotFoundError(
                f"Ambiguous relationship: {len(rows)} active rows from "
                f"'{subject_uuid}' to '{object_uuid}' in story {story_id}. "
                "Natural-key resolution requires a unique match."
            )
        return rows[0]

    def _update_relationship_field(
        self,
        row: SBRelationshipLedgerORM,
        field: str,
        value: bool | str,
        source_turn_id: str,
        *,
        session: Session | None = None,
    ) -> None:
        """Apply a relationship-ledger field update with history.

        Args:
            session: optional caller-supplied SQLAlchemy session (Issue 12c).
                When supplied, the history row and flush go through that
                session so the write joins the caller's outer transaction.
                When ``None``, ``self._session`` is used.
        """
        target = session if session is not None else self._session
        if not hasattr(row, field):
            raise ValueError(f"SBRelationshipLedgerORM has no attribute '{field}'.")
        old_val = getattr(row, field)
        history_row = SBDynamicFieldHistoryORM(
            history_id=str(uuid4()),
            entity_type="relationship_ledger",
            entity_id=row.relationship_id,
            field_name=field,
            old_value=json.dumps(old_val) if old_val is not None else None,
            changed_at=_now_iso(),
            source_turn_id=source_turn_id,
        )
        target.add(history_row)
        setattr(row, field, value)
        row.updated_at = _now_iso()
        target.flush()

    # ------------------------------------------------------------------
    # Domain-specific creation helpers
    # ------------------------------------------------------------------

    def create_setting(
        self, story_id: UUID, setting: StoryBibleSetting, *, confirmed: bool = False
    ) -> StoryBibleSetting:
        """Persist a new Story Bible setting entry.

        If an active setting already exists for the story, ``confirmed=True``
        is required; raises ``ConfirmationRequiredError`` otherwise.  The prior
        active setting is deactivated (soft-deleted) before the new one is
        written, so only one active setting exists per story at a time.
        """
        sid = str(story_id)
        existing_rows = (
            self._session.execute(
                select(SBSettingORM).where(
                    SBSettingORM.story_id == sid,
                    SBSettingORM.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        if existing_rows and not confirmed:
            raise ConfirmationRequiredError(
                "Replacing an active setting requires explicit Sojourner "
                "confirmation.  Pass confirmed=True to proceed."
            )
        for existing in existing_rows:
            existing.is_active = False
        row = SBSettingORM(
            setting_id=str(setting.setting_id),
            story_id=str(story_id),
            summary=setting.summary,
            world_rules=setting.world_rules,
            geography=setting.geography,
            time_period=setting.time_period,
            is_active=True,
            created_at=setting.created_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _setting_orm_to_model(row)

    def add_cast_entry(self, story_id: UUID, entry: CastEntry) -> CastEntry:
        """Persist a new cast entry."""
        row = SBCastEntryORM(
            cast_id=str(entry.cast_id),
            story_id=str(story_id),
            static_name=entry.name,
            static_role=entry.role.value,
            static_traits=entry.traits,
            static_goals=entry.goals,
            static_secrets=entry.secrets,
            static_background=entry.background,
            dynamic_current_location=entry.current_location,
            dynamic_current_status=entry.current_status,
            dynamic_is_alive=entry.is_alive,
            dynamic_notes=entry.notes,
            is_active=True,
            created_at=entry.created_at.isoformat(),
            source_turn_id=entry.source_turn_id,
        )
        self._session.add(row)
        self._session.flush()
        return _cast_orm_to_model(row)

    def add_locked_fact(self, story_id: UUID, fact: LockedFact) -> LockedFact:
        """Persist a new locked fact directly (e.g. created at story setup)."""
        row = SBLockedFactORM(
            locked_fact_id=str(fact.locked_fact_id),
            story_id=str(story_id),
            fact_text=fact.fact_text,
            source_turn_id=fact.source_turn_id,
            confirmation_timestamp=(
                fact.confirmation_timestamp.isoformat()
                if fact.confirmation_timestamp
                else None
            ),
            is_active=True,
            created_at=fact.created_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _locked_fact_orm_to_model(row)

    def add_forbidden_fact(self, story_id: UUID, fact: ForbiddenFact) -> ForbiddenFact:
        """Persist a new forbidden fact."""
        row = SBForbiddenFactORM(
            forbidden_fact_id=str(fact.forbidden_fact_id),
            story_id=str(story_id),
            fact_text=fact.fact_text,
            source=fact.source,
            is_active=True,
            created_at=fact.created_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _forbidden_fact_orm_to_model(row)

    def add_unresolved_thread(
        self, story_id: UUID, thread: UnresolvedThread
    ) -> UnresolvedThread:
        """Persist a new unresolved thread."""
        row = SBUnresolvedThreadORM(
            thread_id=str(thread.thread_id),
            story_id=str(story_id),
            description=thread.description,
            source_turn_id=thread.source_turn_id,
            status=thread.status.value,
            is_active=True,
            created_at=thread.created_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _thread_orm_to_model(row)

    def add_relationship(
        self, story_id: UUID, ledger: RelationshipLedger
    ) -> RelationshipLedger:
        """Persist a new relationship ledger entry.

        Raises ``EntityNotFoundError`` if either cast member does not exist
        as an active entry in this story.
        """
        sid = str(story_id)
        for cast_id in (ledger.subject_cast_id, ledger.object_cast_id):
            cast_row = self._session.get(SBCastEntryORM, str(cast_id))
            if cast_row is None or cast_row.story_id != sid or not cast_row.is_active:
                raise EntityNotFoundError(
                    f"CastEntry {cast_id} not found for story {story_id}."
                )
        row = SBRelationshipLedgerORM(
            relationship_id=str(ledger.relationship_id),
            story_id=str(story_id),
            subject_cast_id=str(ledger.subject_cast_id),
            object_cast_id=str(ledger.object_cast_id),
            relationship_type=ledger.relationship_type.value,
            current_status_description=ledger.current_status_description,
            source_turn_id=ledger.source_turn_id,
            is_active=True,
            created_at=ledger.created_at.isoformat(),
            updated_at=ledger.updated_at.isoformat(),
        )
        self._session.add(row)
        self._session.flush()
        return _relationship_orm_to_model(row)

    def soft_delete(self, entity_type: str, entity_id: UUID) -> None:
        """Mark a Story Bible entity as inactive (soft-delete).

        Story Bible records are never hard-deleted through this service.
        The record remains in SQLite with ``is_active = False``.
        """
        orm_map: dict[str, type] = {
            "setting": SBSettingORM,
            "cast_entry": SBCastEntryORM,
            "locked_fact": SBLockedFactORM,
            "forbidden_fact": SBForbiddenFactORM,
            "event": SBEventORM,
            "relationship": SBRelationshipLedgerORM,
            "thread": SBUnresolvedThreadORM,
            "proposal": SBProvisionalStagingORM,
        }
        cls = orm_map.get(entity_type)
        if cls is None:
            raise ValueError(f"Unknown entity_type '{entity_type}'.")
        row = self._session.get(cls, str(entity_id))
        if row is not None:
            row.is_active = False
            self._session.flush()

    def get_dynamic_field_history(
        self, entity_type: str, entity_id: UUID
    ) -> list[DynamicFieldHistory]:
        """Return the full change history for a dynamic entity."""
        rows = (
            self._session.execute(
                select(SBDynamicFieldHistoryORM).where(
                    SBDynamicFieldHistoryORM.entity_type == entity_type,
                    SBDynamicFieldHistoryORM.entity_id == str(entity_id),
                )
            )
            .scalars()
            .all()
        )
        return [_history_orm_to_model(r) for r in rows]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_field_value_type(
    target_domain: TargetDomain,
    target_field: str,
    proposed_value: bool | str,
) -> None:
    """Raise ValueError if proposed_value's Python type is wrong for target_field.

    Called by route_extractor_proposals before any staging or canon write so that
    a type mismatch aborts the entire transaction rather than reaching the ORM.
    """
    expected = _FIELD_VALUE_TYPES.get((target_domain.value, target_field))
    if expected is None:
        return  # unknown field — the writable-field check already handles this
    if not isinstance(proposed_value, expected):
        raise ValueError(
            f"Field '{target_field}' in domain '{target_domain.value}' requires "
            f"a {expected.__name__} value; "
            f"got {type(proposed_value).__name__!r}."
        )


def _set_cast_column(row: SBCastEntryORM, col_name: str, value: object) -> None:
    """Set an attribute on a SBCastEntryORM row by column name."""
    if not hasattr(row, col_name):
        raise ValueError(f"SBCastEntryORM has no attribute '{col_name}'.")
    setattr(row, col_name, value)


def _parse_relationship_natural_key(key: str) -> tuple[str, str]:
    """Parse a ``'<subject> -> <object>'`` relationship natural key.

    The delimiter is exactly the four-character sequence `` -> `` (space, dash,
    greater-than, space).  Zero or more than one delimiter raises ``ValueError``,
    which the caller translates to a transaction failure.
    """
    parts = key.split(" -> ")
    if len(parts) != 2:
        raise ValueError(
            f"Relationship natural key must contain exactly one ' -> ' delimiter; "
            f"got {key!r}."
        )
    subject, obj = parts[0].strip(), parts[1].strip()
    if not subject or not obj:
        raise ValueError(
            f"Relationship natural key subject and object must be non-empty; "
            f"got {key!r}."
        )
    return subject, obj
