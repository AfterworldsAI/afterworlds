"""Exact governing spans on mechanical prose bindings.

CRD Issue 5d (#137), production-authoring PR. #137 contract 3 requires a
prose-bound component to resolve its *accepted governing span*, not the whole
passage that happens to contain it. A binding therefore names the accepted
classification span it governs, plus that span's half-open offsets into the
bound ``RuleChunk``'s own text, so runtime resolution slices exactly the
governing clause without re-reading the 5c projection relation.

The authoritative text still comes from the immutable 5c ``RuleChunk``. Nothing
here copies source prose into a second store, and no 5c table is touched.

Additive only, and additive to an empty table in every environment: no accepted
production oracle exists yet, so no mechanical projection has ever been
published and ``rp_mech_prose_bindings`` carries no rows outside a test
database. The columns are created ``NOT NULL`` with a server default so a
development row set survives the upgrade; the default is inert afterwards
because every writer supplies all three values.

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "rp_mech_prose_bindings"


def upgrade() -> None:
    op.add_column(
        _TABLE,
        sa.Column("span_id", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        _TABLE,
        sa.Column("chunk_char_start", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        _TABLE,
        sa.Column("chunk_char_end", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index(f"ix_{_TABLE}_span_id", _TABLE, ["span_id"])


def downgrade() -> None:
    op.drop_index(f"ix_{_TABLE}_span_id", table_name=_TABLE)
    for column in ("chunk_char_end", "chunk_char_start", "span_id"):
        op.drop_column(_TABLE, column)
