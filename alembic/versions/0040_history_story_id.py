"""Durable ``story_id`` on ``sb_dynamic_field_history`` — #50.

Adds a non-null ``story_id`` without a Story FK (Owner Decision 2026-10-11):
history outlives its target entity and Story, as ADR-0006 requires. Existing
rows are backfilled from the target entity row named by ``entity_type`` /
``entity_id``. Rows whose owner cannot be resolved stop the upgrade before any
DDL runs, leaving rows and the 0039 schema untouched; no ID is invented.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | None = None
depends_on: str | None = None

_OWNER = (
    "CASE h.entity_type"
    " WHEN 'cast_entry' THEN (SELECT c.story_id FROM sb_cast_entries c"
    " WHERE c.cast_id = h.entity_id)"
    " WHEN 'relationship_ledger' THEN (SELECT r.story_id FROM"
    " sb_relationship_ledger r WHERE r.relationship_id = h.entity_id)"
    " END"
)


def upgrade() -> None:
    conn = op.get_bind()
    orphans = conn.execute(
        sa.text(
            "SELECT h.history_id, h.entity_type, h.entity_id"
            f" FROM sb_dynamic_field_history h WHERE ({_OWNER}) IS NULL"
            " ORDER BY h.history_id"
        )
    ).all()
    if orphans:
        sample = ", ".join(f"{h} ({t} {e})" for h, t, e in orphans[:10])
        raise RuntimeError(
            f"0040: {len(orphans)} sb_dynamic_field_history row(s) have no "
            f"resolvable owning story; nothing was changed. First: {sample}"
        )

    op.add_column("sb_dynamic_field_history", sa.Column("story_id", sa.String(36)))
    conn.execute(
        sa.text(f"UPDATE sb_dynamic_field_history AS h SET story_id = {_OWNER}")
    )
    with op.batch_alter_table("sb_dynamic_field_history") as batch:
        batch.alter_column("story_id", existing_type=sa.String(36), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("sb_dynamic_field_history") as batch:
        batch.drop_column("story_id")
