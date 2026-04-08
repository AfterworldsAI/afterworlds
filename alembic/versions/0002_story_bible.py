"""Story Bible schema — all sb_* tables for Issue 4.

Story Bible tables carry a ``sb_`` prefix to make their separation from prose
history tables (nodes, turns, arcs, chapters) structurally visible and
machine-verifiable.  No ``sb_*`` table carries a FK to any prose history
table.  Provenance references to turns are plain nullable strings.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-06

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # sb_settings — Story Bible setting entry (static partition)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_settings",
        sa.Column("setting_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("world_rules", sa.JSON, nullable=False),
        sa.Column("geography", sa.Text, nullable=True),
        sa.Column("time_period", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_cast_entries — cast members with static/dynamic column split
    # ------------------------------------------------------------------
    op.create_table(
        "sb_cast_entries",
        sa.Column("cast_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Static partition
        sa.Column("static_name", sa.Text, nullable=False),
        sa.Column("static_role", sa.String(32), nullable=False),
        sa.Column("static_traits", sa.JSON, nullable=False),
        sa.Column("static_goals", sa.JSON, nullable=False),
        sa.Column("static_secrets", sa.JSON, nullable=False),
        sa.Column("static_background", sa.Text, nullable=True),
        # Dynamic partition
        sa.Column("dynamic_current_location", sa.Text, nullable=True),
        sa.Column("dynamic_current_status", sa.Text, nullable=True),
        sa.Column("dynamic_is_alive", sa.Boolean, nullable=False, default=True),
        sa.Column("dynamic_notes", sa.Text, nullable=True),
        # Metadata
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
    )

    # ------------------------------------------------------------------
    # sb_locked_facts — facts that cannot be undone (static partition)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_locked_facts",
        sa.Column("locked_fact_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_text", sa.Text, nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
        sa.Column("confirmation_timestamp", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_forbidden_facts — facts that cannot happen (static partition)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_forbidden_facts",
        sa.Column("forbidden_fact_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_text", sa.Text, nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_events — Events Ledger (append-only)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("significance", sa.String(64), nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_relationship_ledger — directional current-state records (dynamic)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_relationship_ledger",
        sa.Column("relationship_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Plain strings — no FK to sb_cast_entries.
        sa.Column("subject_cast_id", sa.String(36), nullable=False),
        sa.Column("object_cast_id", sa.String(36), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("current_status_description", sa.Text, nullable=True),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_unresolved_threads — plot threads queued by Extractor
    # ------------------------------------------------------------------
    op.create_table(
        "sb_unresolved_threads",
        sa.Column("thread_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, default="open"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_provisional_staging — Extractor proposals pending ratification
    # ------------------------------------------------------------------
    op.create_table(
        "sb_provisional_staging",
        sa.Column("proposal_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("proposal_type", sa.String(32), nullable=False),
        sa.Column("target_entity_type", sa.String(64), nullable=True),
        sa.Column("target_entity_id", sa.String(36), nullable=True),
        sa.Column("proposed_value", sa.JSON, nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, default="pending"),
        sa.Column("requires_confirmation", sa.Boolean, nullable=False, default=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # sb_dynamic_field_history — append-only version history for dynamic
    # fields (implements the versioning mechanism from ADR-0006)
    # ------------------------------------------------------------------
    op.create_table(
        "sb_dynamic_field_history",
        sa.Column("history_id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("changed_at", sa.String(64), nullable=False),
        # Provenance — plain string, NOT a FK to turns.
        sa.Column("source_turn_id", sa.String(36), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sb_dynamic_field_history")
    op.drop_table("sb_provisional_staging")
    op.drop_table("sb_unresolved_threads")
    op.drop_table("sb_relationship_ledger")
    op.drop_table("sb_events")
    op.drop_table("sb_forbidden_facts")
    op.drop_table("sb_locked_facts")
    op.drop_table("sb_cast_entries")
    op.drop_table("sb_settings")
