"""Declared representation-schema identity on the mechanical projection header.

CRD Issue 5d (#137), PR #153 review remediation. ADR-005d Decisions 4 and 6
require the closed typed union to be versioned and the projection identity to
bind the representation schema. Without that binding, a projection whose facts
all belong to families a schema change did not touch keeps exactly the same
UUID across two different union contracts, and a recorded binding cannot say
which contract governs the authority it names.

These two columns are the projection's own declaration of the union it was
built under — the exact counterpart of the ``semantic_policy_version`` /
``semantic_policy_hash`` pair beside them, and deliberately separate from it:
the semantic policy identifies the closed *classification* catalogs, this
identifies the closed *representation* contract, and they change for different
reasons. Reconstruction reads these columns rather than current constants, so a
projection built under an earlier union reconstructs as what it was and a later
mismatch is detectable instead of erased.

**No declaration is ever fabricated for an existing row.** A projection
persisted before this column existed was built under an unrecorded union; the
one thing that must not happen is stamping it with today's schema identity,
which would assert that it reconstructs under a contract nothing can show it
agreed to — the precise failure these columns exist to prevent. The upgrade
therefore refuses to run against a table that already holds rows, under
ADR-005c's pre-release clean-baseline authority: no accepted production oracle
exists, so no mechanical projection has ever been published, and any such rows
are development state to be rebuilt rather than migrated.

SQLite cannot add a ``NOT NULL`` column without a default, so an empty-string
default satisfies the dialect. The guard above means it can never be written,
and both the strict oracle loader and ``validate_schema_binding`` reject a blank
or mismatched declaration if it somehow were.

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "rp_mech_projections"


class LegacyProjectionSchemaError(RuntimeError):
    """Raised when existing projections carry no representation-schema identity."""


def upgrade() -> None:
    existing = (
        op.get_bind()
        .execute(sa.text(f"SELECT COUNT(*) FROM {_TABLE}"))  # noqa: S608 - fixed identifier
        .scalar_one()
    )
    if existing:
        raise LegacyProjectionSchemaError(
            f"{_TABLE} holds {existing} projection row(s) built before the "
            "representation-schema declaration existed. There is nothing honest "
            "to record for them: the union they were built under was never "
            "captured, so they cannot be shown to reconstruct under any declared "
            "schema. Under ADR-005c's pre-release clean-baseline authority these "
            "are development rows — drop and rebuild the projection rather than "
            "migrating a fabricated declaration."
        )

    with op.batch_alter_table(_TABLE) as batch:
        batch.add_column(
            sa.Column(
                "representation_schema_version",
                sa.String(64),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "representation_schema_hash",
                sa.String(64),
                nullable=False,
                server_default="",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table(_TABLE) as batch:
        batch.drop_column("representation_schema_hash")
        batch.drop_column("representation_schema_version")
