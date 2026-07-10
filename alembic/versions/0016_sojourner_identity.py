"""Sojourner identity — DoR-A (CRD Issue 19).

Adds ``sojourner_identity``, a singleton table (constant primary key = 1)
holding the single local Sojourner's identity UUID. Not a user/account table
and not the start of one: no credentials, no profile, no multi-user
semantics, no authentication. The row is created lazily on first API access
(see ``persistence/crud/identity.py::get_or_create_sojourner_identity``), not
by this migration.

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sojourner_identity",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sojourner_id", sa.String(36), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sojourner_identity")
