"""Mechanical-projection publication evidence and activation — CRD Issue 5d (#137).

Adds the publication half of the Decision 8 lifecycle:

* four nullable evidence columns on ``rp_mech_projections`` — accepted-oracle
  identity, evidence-report hash, report payload, and publication time. Every
  one of them is a *post-gate* value derived from reconstructed persisted
  state, so none can exist while the projection is still a draft; they follow
  the same NULL-through-draft rule the header already documents for
  ``persisted_state_digest``.
* ``rp_mech_active_projections``, whose primary key is ``package_uuid``. One
  active projection per package is a database constraint rather than an
  application convention, so competing activation cannot split active
  authority.

Additive only. Nothing existing is altered or dropped, no projection becomes
active by migrating, and the legacy ``MechanicalEntity`` path is untouched.

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EVIDENCE_COLUMNS = (
    sa.Column("oracle_identity", sa.String(64), nullable=True),
    sa.Column("evidence_report_hash", sa.String(64), nullable=True),
    sa.Column("report_payload", sa.JSON, nullable=True),
    sa.Column("published_at", sa.String(64), nullable=True),
)


def upgrade() -> None:
    for column in _EVIDENCE_COLUMNS:
        op.add_column("rp_mech_projections", column)

    op.create_table(
        "rp_mech_active_projections",
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("activated_at", sa.String(64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rp_mech_active_projections")
    for column in _EVIDENCE_COLUMNS:
        op.drop_column("rp_mech_projections", column.name)
