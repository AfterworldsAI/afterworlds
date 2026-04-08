"""ORM models for the Story Bible — structured narrative canon.

ARCHITECTURE INVARIANT:
  Story Bible tables (prefix ``sb_``) are structurally separate from prose
  history tables (nodes, turns, arcs, chapters).  No foreign key constraint
  exists between any ``sb_*`` table and the prose history tables.

  Provenance references to Turns are stored as plain nullable ``String(36)``
  columns WITHOUT a ForeignKey constraint.  This is an intentional decoupling
  choice: Story Bible reads must not require traversal of prose history to
  understand present canon state.  See Issue 4 PR Architecture Notes.

  ``story_id`` columns carry a FK to ``stories.story_id`` (the top-level
  story hierarchy) — this is NOT prose history and is explicitly permitted.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class SBSettingORM(Base):
    """Persisted Story Bible setting entry.

    Partition: static.  One active entry per Story.
    """

    __tablename__ = "sb_settings"

    setting_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(sa.Text, nullable=False)
    world_rules: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    geography: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    time_period: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBCastEntryORM(Base):
    """Persisted cast entry with explicit static / dynamic column prefix.

    Static columns (``static_*``) require Sojourner confirmation to change.
    Dynamic columns (``dynamic_*``) are Extractor-maintained; every update
    records the prior value in ``sb_dynamic_field_history``.
    """

    __tablename__ = "sb_cast_entries"

    cast_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Static partition
    static_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    static_role: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    static_traits: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    static_goals: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    static_secrets: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    static_background: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Dynamic partition
    dynamic_current_location: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_current_status: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dynamic_is_alive: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=True
    )
    dynamic_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Metadata
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)


class SBLockedFactORM(Base):
    """Persisted locked fact entry.

    Partition: static.  Distinct from ForbiddenFact.
    """

    __tablename__ = "sb_locked_facts"

    locked_fact_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    confirmation_timestamp: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBForbiddenFactORM(Base):
    """Persisted forbidden fact entry.

    Partition: static.  Distinct from LockedFact.
    An empty table is a valid and normal state.
    """

    __tablename__ = "sb_forbidden_facts"

    forbidden_fact_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    fact_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBEventORM(Base):
    """Persisted Events Ledger entry — append-only.

    ``significance`` drives the tiered inclusion policy; see
    ``services.story_bible.ALWAYS_INCLUDE_SIGNIFICANCE``.
    """

    __tablename__ = "sb_events"

    event_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    significance: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBRelationshipLedgerORM(Base):
    """Persisted directional relationship record.

    Partition: dynamic.  Each row is one character's view of a relationship.
    Asymmetric relationships are represented as separate rows.
    Prior values recorded in ``sb_dynamic_field_history`` on update.
    """

    __tablename__ = "sb_relationship_ledger"

    relationship_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Plain strings — no FK to sb_cast_entries; service enforces integrity.
    subject_cast_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    object_cast_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    relationship_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    current_status_description: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True
    )
    # Provenance for last update — plain string, NOT a FK to turns.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBUnresolvedThreadORM(Base):
    """Persisted unresolved plot thread.

    Threads with ``status = 'open'`` are the active plot threads loaded into
    the context window per service policy.
    """

    __tablename__ = "sb_unresolved_threads"

    thread_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False, default="open")
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBProvisionalStagingORM(Base):
    """Persisted provisional staging entry.

    Staging entries are NOT canon.  They become canon only after ratification
    via ``ratify_update``.  All four Extractor routes are representable:
    locked_fact, soft_fact, transient_state, unresolved_thread.
    """

    __tablename__ = "sb_provisional_staging"

    proposal_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    proposal_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    target_entity_type: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    target_entity_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    proposed_value: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, default="pending"
    )
    requires_confirmation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SBDynamicFieldHistoryORM(Base):
    """Immutable record of a dynamic field change — append-only version history.

    Written on every ``update_dynamic_field`` call.  Never hard-deleted.
    This is the versioning mechanism for the dynamic partition.
    See ADR-0006 for rationale.
    """

    __tablename__ = "sb_dynamic_field_history"

    history_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    field_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    old_value: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    changed_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # Provenance — plain string, NOT a FK to turns. Traceability only.
    source_turn_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
