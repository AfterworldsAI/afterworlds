"""Add the versioned operational corpus trust seam — CRD Issue 5c (#145).

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("rp_corpus_releases") as batch:
        batch.add_column(
            sa.Column("corpus_contract_version", sa.String(64), nullable=True)
        )
        batch.add_column(
            sa.Column("operational_corpus_digest", sa.String(64), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("rp_corpus_releases") as batch:
        batch.drop_column("operational_corpus_digest")
        batch.drop_column("corpus_contract_version")
