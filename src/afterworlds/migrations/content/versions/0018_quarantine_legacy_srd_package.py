"""Delete the incomplete legacy SRD package — CRD Issue 5c (#132).

Pre-release clean baseline (Issue 5c Rev7 / Issue 18 Rev6): Afterworlds is
pre-release, so persistence created before Issue 5c gets no upgrade/preservation
guarantee. This targeted deletion removes any active-store rows bound to the
incomplete legacy SRD package (name ``D&D SRD 5.2.1``, version ``5.2.1``); the
delete cascades to that package's sources, chunks, mechanical entities, and
manifest via existing ``ondelete=CASCADE`` foreign keys.

Its random package UUID is NOT recorded or handed off for any later cross-store
cleanup — the corrected corpus is a clean rebuild and the development Chroma
store is reset in full by an explicit one-time step (see
``scripts/reset_corpus_baseline.py``), not by tracking legacy UUIDs.

Idempotent and a no-op on a fresh database (no migration ever seeded the legacy
package; it could only enter via the removed legacy ingestion default). Never
matches the new corpus release (name ``SRD 5.2.1 Corpus``, version
``5.2.1-corpus.*``).

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEGACY_NAME = "D&D SRD 5.2.1"
_LEGACY_VERSION = "5.2.1"


def upgrade() -> None:
    # Enable FK cascade on SQLite for this connection so dependent rows go too.
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        bind.exec_driver_sql("PRAGMA foreign_keys=ON")
    op.execute(
        sa.text(
            "DELETE FROM rp_packages "
            "WHERE name = :name AND version = :version "
            "AND rules_package_id NOT IN (SELECT package_uuid FROM rp_corpus_releases)"
        ).bindparams(name=_LEGACY_NAME, version=_LEGACY_VERSION)
    )


def downgrade() -> None:
    # The legacy package is defective and intentionally non-restorable
    # (Owner Decision 1: never eligible for regeneration). No-op.
    pass
