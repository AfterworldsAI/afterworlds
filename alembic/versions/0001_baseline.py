"""Baseline schema — all tables for Issue 3 SQLite persistence.

Revision ID: 0001
Revises:
Create Date: 2026-03-31

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # stories
    # ------------------------------------------------------------------
    op.create_table(
        "stories",
        sa.Column("story_id", sa.String(36), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # arcs
    # ------------------------------------------------------------------
    op.create_table(
        "arcs",
        sa.Column("arc_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
    )

    # ------------------------------------------------------------------
    # chapters
    # ------------------------------------------------------------------
    op.create_table(
        "chapters",
        sa.Column("chapter_id", sa.String(36), primary_key=True),
        sa.Column(
            "arc_id",
            sa.String(36),
            sa.ForeignKey("arcs.arc_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
    )

    # ------------------------------------------------------------------
    # nodes
    # ------------------------------------------------------------------
    op.create_table(
        "nodes",
        sa.Column("node_id", sa.String(36), primary_key=True),
        sa.Column(
            "chapter_id",
            sa.String(36),
            sa.ForeignKey("chapters.chapter_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("state_delta", sa.JSON, nullable=False),
        sa.Column("branching_logic", sa.JSON, nullable=False),
        sa.Column("intent_type", sa.String(64), nullable=False),
        sa.Column("metadata", sa.JSON, nullable=False),
        sa.Column("mode_metadata", sa.JSON, nullable=True),
    )

    # ------------------------------------------------------------------
    # turns
    # ------------------------------------------------------------------
    op.create_table(
        "turns",
        sa.Column("turn_id", sa.String(36), primary_key=True),
        sa.Column(
            "node_id",
            sa.String(36),
            sa.ForeignKey("nodes.node_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_input", sa.Text, nullable=False),
        sa.Column("assistant_output", sa.Text, nullable=False),
        sa.Column("timestamp", sa.String(64), nullable=False),
        sa.Column("intent_classification", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # world_states
    # ------------------------------------------------------------------
    op.create_table(
        "world_states",
        sa.Column("world_state_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("static_setting_name", sa.Text, nullable=False),
        sa.Column("static_world_rules", sa.JSON, nullable=False),
        sa.Column("static_geography", sa.Text, nullable=True),
        sa.Column("static_time_period", sa.Text, nullable=True),
        sa.Column("dynamic_current_location", sa.Text, nullable=True),
        sa.Column("dynamic_time_of_day", sa.Text, nullable=True),
        sa.Column("dynamic_weather", sa.Text, nullable=True),
        sa.Column("dynamic_faction_standings", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
        sa.UniqueConstraint("story_id", name="uq_world_states_story_id"),
    )

    # ------------------------------------------------------------------
    # character_states
    # ------------------------------------------------------------------
    op.create_table(
        "character_states",
        sa.Column("character_state_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("static_character_name", sa.Text, nullable=False),
        sa.Column("dynamic_current_location", sa.Text, nullable=True),
        sa.Column("dynamic_status_effects", sa.JSON, nullable=False),
        sa.Column("dynamic_relationship_meters", sa.JSON, nullable=False),
        sa.Column("dynamic_inventory", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
        sa.UniqueConstraint("story_id", name="uq_character_states_story_id"),
    )

    # ------------------------------------------------------------------
    # rpg_session_states
    # ------------------------------------------------------------------
    op.create_table(
        "rpg_session_states",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("character_sheet_id", sa.String(36), nullable=False),
        sa.Column("dice_handling", sa.String(32), nullable=False),
        sa.Column("active_quests", sa.JSON, nullable=False),
        sa.Column("combat_context", sa.JSON, nullable=False),
        sa.UniqueConstraint("story_id", name="uq_rpg_session_states_story_id"),
    )

    # ------------------------------------------------------------------
    # branching_session_states
    # ------------------------------------------------------------------
    op.create_table(
        "branching_session_states",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pacing_stage", sa.String(32), nullable=False),
        sa.Column("branch_tree", sa.JSON, nullable=False),
        sa.Column("plot_thread_tracker", sa.JSON, nullable=False),
        sa.Column("current_node_id", sa.String(36), nullable=True),
        sa.UniqueConstraint(
            "story_id", name="uq_branching_session_states_story_id"
        ),
    )

    # ------------------------------------------------------------------
    # writing_session_states
    # ------------------------------------------------------------------
    op.create_table(
        "writing_session_states",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("beat_constraints", sa.JSON, nullable=False),
        sa.Column("version_history_pointers", sa.JSON, nullable=False),
        sa.Column("persona", sa.String(32), nullable=True),
        sa.UniqueConstraint(
            "story_id", name="uq_writing_session_states_story_id"
        ),
    )

    # ------------------------------------------------------------------
    # rpg_character_sheet_bases
    # ------------------------------------------------------------------
    op.create_table(
        "rpg_character_sheet_bases",
        sa.Column("sheet_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rules_package_id", sa.Text, nullable=False),
        sa.Column("character_name", sa.Text, nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )

    # ------------------------------------------------------------------
    # dnd5e_character_sheets
    # ------------------------------------------------------------------
    op.create_table(
        "dnd5e_character_sheets",
        sa.Column(
            "sheet_id",
            sa.String(36),
            sa.ForeignKey(
                "rpg_character_sheet_bases.sheet_id", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column("character_class", sa.Text, nullable=False),
        sa.Column("background", sa.Text, nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("ability_scores", sa.JSON, nullable=False),
        sa.Column("skills", sa.JSON, nullable=False),
        sa.Column("equipment", sa.JSON, nullable=False),
        sa.Column("current_hp", sa.Integer, nullable=False),
        sa.Column("maximum_hp", sa.Integer, nullable=False),
        sa.Column("spell_slots", sa.JSON, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("dnd5e_character_sheets")
    op.drop_table("rpg_character_sheet_bases")
    op.drop_table("writing_session_states")
    op.drop_table("branching_session_states")
    op.drop_table("rpg_session_states")
    op.drop_table("character_states")
    op.drop_table("world_states")
    op.drop_table("turns")
    op.drop_table("nodes")
    op.drop_table("chapters")
    op.drop_table("arcs")
    op.drop_table("stories")
