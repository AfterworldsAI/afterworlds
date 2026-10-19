"""turns.intent_classification_result — CRD Issue 9.

Adds a nullable JSON column ``intent_classification_result`` to the ``turns``
table.  This column stores the full typed IntentClassificationResult produced
by the Writer pass (Issue 9), enabling downstream consumers to access the
complete classification payload — not just the intent type enum value that was
already persisted in ``intent_classification``.

Pre-Issue-9 rows have NULL in this column; the model treats NULL as None.

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "turns",
        sa.Column("intent_classification_result", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("turns", "intent_classification_result")
