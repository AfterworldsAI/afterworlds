"""The kind of a held Gaming Set or Musical Instrument — CRD Issue 15c.

Adds a nullable ``tool_variant`` to ``dnd5e_item_instances``: one of the tool
component's typed variants, each kind its own proficiency. Existing rows keep
``NULL`` (no kind recorded); no row is read or changed.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "dnd5e_item_instances", sa.Column("tool_variant", sa.Text, nullable=True)
    )


def downgrade() -> None:
    with op.batch_alter_table("dnd5e_item_instances") as batch:
        batch.drop_column("tool_variant")
