"""Actor-turn coordination and its append-only edge log — CRD Issue 15c.

Creates ``rpg_turn_coordination`` (one row per story: the active turn and the
next turn instance, with a revision) and ``rpg_turn_edges`` (every applied
``begin``/``end`` edge and once-per-turn ``use``, sequenced per story, so the
coordination document is reconstructable by replay). Create-only: no existing
row is read or changed.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: str | None = None
depends_on: str | None = None


def _story(**kw: object) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        "story_id",
        sa.String(36),
        sa.ForeignKey("stories.story_id", ondelete="CASCADE"),
        **kw,  # type: ignore[arg-type]
    )


def upgrade() -> None:
    op.create_table(
        "rpg_turn_coordination",
        _story(primary_key=True),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("document", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
    )
    op.create_table(
        "rpg_turn_edges",
        sa.Column("edge_id", sa.String(36), primary_key=True),
        _story(nullable=False, index=True),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("turn_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("subject_kind", sa.String(16), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False),
        sa.Column("turn_instance", sa.Integer, nullable=False),
        sa.Column("coordination_revision", sa.Integer, nullable=False),
        sa.Column("use_key", sa.Text, nullable=True),
        sa.Column("recorded_at", sa.String(64), nullable=False),
        sa.UniqueConstraint("story_id", "sequence", name="uq_rpg_turn_edges_sequence"),
        sa.CheckConstraint(
            "kind IN ('begin', 'end', 'use')", name="ck_rpg_turn_edges_kind"
        ),
        sa.CheckConstraint(
            "(kind = 'use') = (use_key IS NOT NULL)", name="ck_rpg_turn_edges_use_key"
        ),
    )


def downgrade() -> None:
    op.drop_table("rpg_turn_edges")
    op.drop_table("rpg_turn_coordination")
