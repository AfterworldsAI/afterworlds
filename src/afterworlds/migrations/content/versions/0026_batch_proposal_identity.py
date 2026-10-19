"""Reviewed-proposal identity on retained batch-acceptance evidence.

CRD Issue 5d (#137), PR #151 review remediation. A batch's scope and semantic
diff record which spans were accepted and what their disposition became. They
say nothing about the records, components, facts, prose bindings, relationships,
references, or provenance that acceptance also draws into the projection — two
proposals can agree on every span and state entirely different mechanical
authority. Each batch therefore also retains the content-derived identity of the
exact complete proposal that was reviewed, so the evidence can establish that the
accepted representation is one somebody actually looked at.

Retained evidence, never identity: this column is covered by the persisted-state
digest and is deliberately absent from the projection and oracle identity
payloads, so re-reviewing an unchanged classification still cannot remint a
projection.

**No identity is ever fabricated for a legacy row.** There is nothing honest to
put in this column for a batch recorded before the evidence existed — inventing
one would assert a review that cannot be shown to have happened, which is the
precise failure this column exists to prevent. The upgrade therefore refuses to
run against a table that already holds rows, under ADR-005c's pre-release
clean-baseline authority: no accepted production oracle exists, so no mechanical
projection has ever been published, and any such rows are development state to be
rebuilt rather than migrated. SQLite cannot add a ``NOT NULL`` column without a
default, so an empty-string default satisfies the dialect; the guard above means
it can never be written, and both the strict loader and acceptance validation
reject a blank identity if it somehow were.

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "rp_mech_acceptance_batches"


class LegacyAcceptanceEvidenceError(RuntimeError):
    """Raised when existing batch rows carry no reviewed-proposal identity."""


def upgrade() -> None:
    existing = op.get_bind().execute(
        sa.text(f"SELECT COUNT(*) FROM {_TABLE}")  # noqa: S608 - fixed identifier
    ).scalar_one()
    if existing:
        raise LegacyAcceptanceEvidenceError(
            f"{_TABLE} holds {existing} batch row(s) recorded before "
            "reviewed-proposal identity was retained. There is no honest value "
            "for this column on those rows, and fabricating one would assert a "
            "review that cannot be shown to have happened. No mechanical "
            "projection has ever been published, so rebuild this development "
            "state under the pre-release clean baseline rather than migrating it."
        )

    op.add_column(
        _TABLE,
        sa.Column("proposal_identity", sa.String(64), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column(_TABLE, "proposal_identity")
