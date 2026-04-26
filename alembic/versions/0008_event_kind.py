"""sb_events.event_kind — CRD Issue 10.

Adds a ``event_kind`` column to the ``sb_events`` table.  This column stores
the functional classification of an event (e.g. ``death``, ``location_change``)
as defined by ``EventKind`` in ``models/enums.py``.

Pre-Issue-10 rows receive ``server_default="routine"`` so existing data is
backfilled without a separate data migration.

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-25
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sb_events",
        sa.Column(
            "event_kind",
            sa.String(64),
            nullable=False,
            server_default="routine",
        ),
    )


def downgrade() -> None:
    op.drop_column("sb_events", "event_kind")
