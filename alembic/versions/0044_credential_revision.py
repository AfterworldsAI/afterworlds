"""Credential revision token for BYOK settings — CRD Issue 20.

Adds ``credential_revision`` to ``provider_credential_metadata``: an opaque,
non-secret token replaced on every credential write. Explicit validation
records its result only if the token it captured is still current, so a late
result cannot validate a replacement key or revive a removed one. Existing
rows get ``""`` (no write recorded since this column existed).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "provider_credential_metadata",
        sa.Column(
            "credential_revision", sa.String(36), nullable=False, server_default=""
        ),
    )


def downgrade() -> None:
    with op.batch_alter_table("provider_credential_metadata") as batch:
        batch.drop_column("credential_revision")
