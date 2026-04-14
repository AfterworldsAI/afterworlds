"""Rules Package Manifests table — CRD Issue 5b.

Adds ``rp_manifests`` table to support the ingestion pipeline.
One manifest per package (enforced by UNIQUE constraint).  Both
``sql_ingest_complete`` and ``vector_write_complete`` must be True before
a package may be published.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rp_manifests",
        sa.Column("manifest_id", sa.String(36), primary_key=True),
        sa.Column(
            "rules_package_id",
            sa.String(36),
            sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("authoritative_source_document", sa.Text, nullable=False),
        sa.Column("authoritative_source_version", sa.Text, nullable=False),
        sa.Column("package_license", sa.Text, nullable=False),
        sa.Column("transform_status", sa.Text, nullable=False),
        sa.Column("parsing_convenience_source", sa.Text, nullable=True),
        sa.Column("attribution_text", sa.Text, nullable=False),
        sa.Column(
            "sql_ingest_complete", sa.Boolean, nullable=False, default=False
        ),
        sa.Column(
            "vector_write_complete", sa.Boolean, nullable=False, default=False
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.String(64), nullable=False),
        sa.UniqueConstraint(
            "rules_package_id",
            name="uq_rp_manifests_package",
        ),
    )


def downgrade() -> None:
    op.drop_table("rp_manifests")
