"""turns.mode_metadata — CRD Issue 17 remediation (PR #116).

Adds a nullable JSON column ``mode_metadata`` to the ``turns`` table.

``NodeORM.turns`` is a list — multiple Turns can link to the same Node — so a
Node-level ``mode_metadata`` field alone lets a later Writing turn's
provenance snapshot (persona, work_product_kind, canon_eligibility,
authoring-control snapshot, version pointer refs) overwrite an earlier turn's
snapshot on the same Node. This column gives each Turn its own durable
per-turn snapshot, independent of Node.mode_metadata, so ADR-017's
Rolling-Summary-filtering provenance survives multiple Writing turns per Node.

Pre-this-migration rows have NULL in this column; the model treats NULL as
None (no mode-specific metadata recorded for that Turn).

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-01
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "turns",
        sa.Column("mode_metadata", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("turns", "mode_metadata")
