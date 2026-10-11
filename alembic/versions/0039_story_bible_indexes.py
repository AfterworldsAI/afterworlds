"""Story Bible secondary indexes — #44.

Indexes ``story_id`` on the eight story-scoped ``sb_*`` tables and
``(entity_type, entity_id)`` on ``sb_dynamic_field_history``. Index DDL only:
no column, constraint or row changes. History carries no ``story_id``; that
is #50's question, not this migration's.
"""

from __future__ import annotations

from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | None = None
depends_on: str | None = None

_INDEXES: tuple[tuple[str, str, list[str]], ...] = (
    *(
        (f"ix_{table}_story_id", table, ["story_id"])
        for table in (
            "sb_settings",
            "sb_cast_entries",
            "sb_locked_facts",
            "sb_forbidden_facts",
            "sb_events",
            "sb_relationship_ledger",
            "sb_unresolved_threads",
            "sb_provisional_staging",
        )
    ),
    (
        "ix_sb_dynamic_field_history_entity",
        "sb_dynamic_field_history",
        ["entity_type", "entity_id"],
    ),
)


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _ in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
