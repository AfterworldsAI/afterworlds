"""Table-cell positions on ledger leaves — CRD Issue 5c (#132), PR #134.

Adds ``table_id`` / ``table_row`` / ``table_col`` to ``rp_ledger_leaves`` so the
reconstructed table structure of ``TABLE_CELL`` leaves (Component F table
fidelity) is persisted, not flattened into paragraphs. All three are nullable —
they are set only for table-cell leaves and NULL for every other leaf.

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("rp_ledger_leaves") as batch:
        batch.add_column(sa.Column("table_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("table_row", sa.Integer, nullable=True))
        batch.add_column(sa.Column("table_col", sa.Integer, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("rp_ledger_leaves") as batch:
        batch.drop_column("table_col")
        batch.drop_column("table_row")
        batch.drop_column("table_id")
