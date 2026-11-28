"""Issue #211 M1: the mapper's spatial record.

``spatial_maps`` holds one row per place in a story; ``spatial_map_revisions``
holds each immutable revision with its updates, snapshot and content hash,
pointing at the Turn that committed it.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "spatial_maps",
        sa.Column("map_id", sa.String(36), primary_key=True),
        sa.Column(
            "story_id",
            sa.String(36),
            sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("place_key", sa.String(200), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("grid_type", sa.String(16), nullable=False),
        sa.Column("seed", sa.BigInteger, nullable=False),
        sa.Column("generator_version", sa.String(64), nullable=False),
        sa.Column("style", sa.JSON, nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column(
            "created_turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.UniqueConstraint("story_id", "place_key", name="uq_spatial_maps_place"),
        sa.CheckConstraint(
            "status IN ('active', 'archived')", name="ck_spatial_maps_status"
        ),
    )
    op.create_table(
        "spatial_map_revisions",
        sa.Column(
            "map_id",
            sa.String(36),
            sa.ForeignKey("spatial_maps.map_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("revision", sa.Integer, primary_key=True),
        sa.Column("parent_revision", sa.Integer, nullable=True),
        sa.Column(
            "turn_id",
            sa.String(36),
            sa.ForeignKey("turns.turn_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("node_id", sa.String(36), nullable=True),
        sa.Column("sequence_id", sa.String(36), nullable=True),
        sa.Column("updates", sa.JSON, nullable=False),
        sa.Column("snapshot", sa.JSON, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("spatial_map_revisions")
    op.drop_table("spatial_maps")
