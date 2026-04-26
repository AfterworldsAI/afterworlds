"""Pydantic models for the Story Bible — structured narrative canon.

The Story Bible is the contract the pipeline is bound to honor at every turn.
It is structurally separate from prose history (nodes, turns, arcs, chapters).
These models represent ratified canon; provisional entries live in
:class:`~afterworlds.models.story_bible.ProvisionalProposal`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from afterworlds.models.enums import (
    CastRole,
    EventKind,
    EventSignificance,
    ProposalStatus,
    ProposalType,
    RelationshipType,
    ThreadStatus,
)


class StoryBibleSetting(BaseModel):
    """Setting summary and world rules for a Story.

    Partition: static.  Requires Sojourner confirmation to update.
    """

    model_config = ConfigDict(frozen=True)

    setting_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    summary: str
    world_rules: tuple[str, ...] = ()
    geography: str | None = None
    time_period: str | None = None
    is_active: bool = True
    created_at: datetime


class CastEntry(BaseModel):
    """A cast member with explicit static / dynamic field separation.

    Static fields (name, role, traits, goals, secrets, background) are
    canonical profile data that require Sojourner confirmation to change.
    Dynamic fields (current_location, current_status, is_alive, notes) are
    Extractor-maintained state; prior values are preserved in the dynamic
    field history table on every update.
    """

    model_config = ConfigDict(frozen=True)

    cast_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    name: str  # static
    role: CastRole  # static
    traits: tuple[str, ...] = ()  # static
    goals: tuple[str, ...] = ()  # static
    secrets: tuple[str, ...] = ()  # static
    background: str | None = None  # static
    current_location: str | None = None  # dynamic
    current_status: str | None = None  # dynamic
    is_alive: bool = True  # dynamic
    notes: str | None = None  # dynamic — narrow escape hatch, not a catch-all
    is_active: bool = True
    created_at: datetime
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None


class LockedFact(BaseModel):
    """A fact that cannot be undone.

    Partition: static.  Distinct from ForbiddenFact; queryable as a
    distinct set via ``get_locked_facts``.
    """

    model_config = ConfigDict(frozen=True)

    locked_fact_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    fact_text: str
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None
    confirmation_timestamp: datetime | None = None
    is_active: bool = True
    created_at: datetime


class ForbiddenFact(BaseModel):
    """A fact that cannot happen.

    An exceptions ledger for explicit, non-obvious "must not happen"
    constraints stated by the Sojourner or later proposed and confirmed.
    Most stories will have zero or only a few forbidden facts; an empty
    set is normal.  Implicit genre/setting constraints are handled by the
    Contradiction Checker, not this table.

    Partition: static.  Distinct from LockedFact; queryable as a
    distinct set via ``get_forbidden_facts``.
    """

    model_config = ConfigDict(frozen=True)

    forbidden_fact_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    fact_text: str
    source: str  # "sojourner" | "confirmed_proposal"
    is_active: bool = True
    created_at: datetime


class Event(BaseModel):
    """An entry in the Events Ledger — append-only narrative record.

    The tiered inclusion policy uses ``significance`` to decide which events
    appear in the active context window beyond the most-recent-N window.
    See ``services.story_bible.ALWAYS_INCLUDE_SIGNIFICANCE`` for the
    always-include set.
    """

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    description: str
    significance: EventSignificance
    event_kind: EventKind
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None
    is_active: bool = True
    created_at: datetime


class RelationshipLedger(BaseModel):
    """Directional current-state record between two cast members.

    Partition: dynamic.  Each entry represents one character's relationship
    to another from their perspective.  Asymmetric relationships are stored
    as separate entries.  Prior values are preserved in dynamic field
    history on every update.
    """

    model_config = ConfigDict(frozen=True)

    relationship_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    subject_cast_id: UUID
    object_cast_id: UUID
    relationship_type: RelationshipType
    current_status_description: str | None = None
    # Provenance for last update: traceability only; not a FK to turns.
    source_turn_id: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UnresolvedThread(BaseModel):
    """A plot thread queued by the Extractor but not committed to canon.

    Active plot threads in the context window are the subset of
    UnresolvedThreads with status=OPEN, loaded per service policy.
    """

    model_config = ConfigDict(frozen=True)

    thread_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    description: str
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None
    status: ThreadStatus = ThreadStatus.OPEN
    is_active: bool = True
    created_at: datetime


class ProvisionalProposal(BaseModel):
    """A staged Story Bible update awaiting ratification.

    Provisional entries are NOT visible as canon until ratified.  The
    staging table is distinct from all ratified-canon tables.

    ``proposal_type`` covers all four Extractor routes:
    locked_fact, soft_fact, transient_state, unresolved_thread.

    ``requires_confirmation`` is True for locked_fact proposals; the
    ``ratify_update`` service method enforces this.
    """

    proposal_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    proposal_type: ProposalType
    target_entity_type: str | None = None
    target_entity_id: str | None = None
    proposed_value: dict[str, Any] = Field(default_factory=dict)
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None
    status: ProposalStatus = ProposalStatus.PENDING
    requires_confirmation: bool = False
    is_active: bool = True
    created_at: datetime


class DynamicFieldHistory(BaseModel):
    """Immutable record of a dynamic field change.

    Written on every ``update_dynamic_field`` call.  Never hard-deleted.
    See ADR-0006 for the versioning mechanism rationale.
    """

    history_id: UUID = Field(default_factory=uuid4)
    entity_type: str  # e.g. "cast_entry", "relationship_ledger"
    entity_id: str
    field_name: str
    old_value: Any = None
    changed_at: datetime
    # Provenance: traceability only; not a FK to the turns table.
    source_turn_id: str | None = None


class StoryBibleContext(BaseModel):
    """Structured payload returned by ``get_active_context_window``.

    This is the typed payload the Context Builder (Issue 8) will consume
    without transformation.  All fields are drawn from ratified canon;
    provisional entries are excluded.

    ``events`` contains the tiered subset: the N most recent events union
    all events whose significance qualifies for always-include, regardless
    of recency.  The N value and always-include set are defined in the
    service layer — see ``services.story_bible``.

    All collection fields are tuples so that the frozen constraint is
    deep — StablePrefix.frozen=True cannot prevent list.append() on nested
    mutable lists, but tuple fields are inherently immutable.
    """

    model_config = ConfigDict(frozen=True)

    story_id: UUID
    setting: StoryBibleSetting | None
    cast: tuple[CastEntry, ...]
    locked_facts: tuple[LockedFact, ...]
    forbidden_facts: tuple[ForbiddenFact, ...]
    relationship_ledger: tuple[RelationshipLedger, ...]
    active_plot_threads: tuple[UnresolvedThread, ...]
    events: tuple[Event, ...]
