"""ORM models for mode-specific session states."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RpgSessionStateORM(Base):
    """Persisted RpgSessionState row — one active row per story."""

    __tablename__ = "rpg_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_rpg_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    character_sheet_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rpg_character_sheet_bases.sheet_id", ondelete="RESTRICT"),
        nullable=False,
    )
    dice_handling: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    play_status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="setup"
    )
    setup_phase: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default="world_setup"
    )
    gm_cheating: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default="1"
    )
    tone: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="balanced"
    )
    session_type: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default="open_ended"
    )
    genre_flavor: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    house_rules: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    acceptable_content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    active_quests: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    combat_context: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class BranchingSessionStateORM(Base):
    """Persisted BranchingSessionState row — one active row per story."""

    __tablename__ = "branching_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_branching_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )
    pacing_stage: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    branch_tree: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    plot_thread_tracker: Mapped[list[Any]] = mapped_column(sa.JSON, nullable=False)
    current_node_id: Mapped[str | None] = mapped_column(
        sa.String(36),
        sa.ForeignKey("nodes.node_id", ondelete="SET NULL"),
        nullable=True,
    )
    # Issue 16: interaction configuration columns.  All nullable so existing rows
    # are never silently backfilled to freeform_only (conservative backfill rule).
    interaction_style: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    branching_cadence: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    length_preference: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    branch_count_range: Mapped[str | None] = mapped_column(sa.String(8), nullable=True)
    play_status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="setup"
    )
    world_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    story_seeds: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    character_concept: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    supporting_cast: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    world_constraints: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    pacing_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    acceptable_content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)


class WritingSessionStateORM(Base):
    """Persisted WritingSessionState row — one active row per story.

    Migration 0013 adds all Issue 17 fields. New columns are nullable so
    existing rows are never silently promoted to a state they were not
    configured for (conservative backfill rule).
    """

    __tablename__ = "writing_session_states"
    __table_args__ = (
        sa.UniqueConstraint("story_id", name="uq_writing_session_states_story_id"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Persona provenance (Issue 17) — nullable for pre-17 rows
    persona_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    persona_registry_version: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    persona_profile_version: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    persona_prompt_fingerprint: Mapped[str | None] = mapped_column(
        sa.String(128), nullable=True
    )

    # Play status — server_default="setup" so existing rows remain in SETUP
    play_status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="setup"
    )

    # Authoring controls (Issue 17) — all nullable
    reading_interests: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    writing_interests: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    form: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    form_other: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    specific_goals: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=""
    )
    critique_intensity: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="balanced"
    )
    tense: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    pov: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    style_density: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, server_default="balanced"
    )
    dialogue_narration_ratio: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True
    )
    genre_conventions: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    acceptable_content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Beat constraints and version pointers (renamed from legacy fields)
    beat_constraints: Mapped[list[Any]] = mapped_column(
        sa.JSON, nullable=False, server_default="[]"
    )
    version_pointers: Mapped[list[Any]] = mapped_column(
        sa.JSON, nullable=False, server_default="[]"
    )
