"""Add session_id to action_resolution_sequences — CRD Issue 15b (ADR-015b 15b-34).

``session_id`` is required so RPG session identity survives on the durable
sequence itself: without it, deriving final audit rows after a
blocked/failed narration and resume would have to re-read mutable
``RpgSessionState`` rather than reconstruct from durable mechanical records,
and ``AI_ROLL``/``HIDDEN_ROLL`` events have no ``PendingRollRequest`` row to
recover it from.

Nullable at the ORM/column layer only: SQLite's ``ALTER TABLE ADD COLUMN``
refuses a ``NOT NULL`` column without a ``DEFAULT``, and there is no
sensible placeholder UUID. This is the same posture migration 0017 already
used for ``pending_roll_requests``'s ``sequence_id``/``step_id``/
``instruction_id`` additions. No backfill is needed or attempted: the
project's working database carries zero rows in ``action_resolution_sequences``
(table did not exist before 0017, and 0017 itself confirmed zero rows in
the sibling ``pending_roll_requests`` table it backfills from) — every row
created after this migration is populated by
``ActionResolutionService.start_sequence``.

A single direct ``ALTER TABLE ... ADD COLUMN`` — no rebuild, no batch mode.
``session_id`` participates in no index or foreign key on this table.

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "action_resolution_sequences"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("session_id", sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_column(_TABLE, "session_id")
