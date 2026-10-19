"""Cross-page table segment index on ledger leaves — CRD Issue 5c (#132), PR #134.

Adds ``table_segment`` to ``rp_ledger_leaves``: the page-segment index of a
page-spanning logical table (0 = first page, 1+ = continuation), so cross-page
table structure survives persistence, digest reconstruction, publication, and
reuse (R15 F3). NULL for non-table leaves. A repeated continuation header is
``table_row == 0`` with ``table_segment > 0``.

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("rp_ledger_leaves") as batch:
        batch.add_column(sa.Column("table_segment", sa.Integer, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("rp_ledger_leaves") as batch:
        batch.drop_column("table_segment")
