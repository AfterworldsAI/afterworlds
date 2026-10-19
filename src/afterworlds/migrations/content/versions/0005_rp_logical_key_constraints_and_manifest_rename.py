"""rp_* logical-key uniqueness constraints and manifest table rename — CRD Issue 5a follow-up (#60).

Changes:
  1. rp_packages — add UNIQUE constraint on (name, version, system): the logical
     identity key already used by IngestionService._upsert_package().
  2. rp_sources — add UNIQUE constraint on (rules_package_id, name): the logical
     identity key already used by IngestionService._upsert_source().
     The existing uq_rp_sources_package_source constraint on
     (rules_package_id, source_id) is kept because it is required as a composite
     FK target by rp_chunks and rp_mechanical_entities.
  3. rules_package_manifests → rp_manifests: aligns the manifest table with the
     rp_* naming family.  Rename was deferred from Issue 5b because that issue
     explicitly required the old name; this follow-up is the owner-approved
     home for the rename.

SQLite note: SQLite does not support ALTER TABLE ADD CONSTRAINT.  Constraints
must be added via Alembic batch mode, which copies the table to a new
definition and drops the old one.  The rename for the manifest table is done
via op.rename_table(), which SQLite supports natively.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. rp_packages — logical-identity uniqueness on (name, version, system)
    #    Batch mode is required for SQLite (no ALTER TABLE ADD CONSTRAINT).
    # ------------------------------------------------------------------
    with op.batch_alter_table("rp_packages") as batch_op:
        batch_op.create_unique_constraint(
            "uq_rp_packages_name_version_system",
            ["name", "version", "system"],
        )

    # ------------------------------------------------------------------
    # 2. rp_sources — logical-identity uniqueness on (rules_package_id, name)
    #    Batch mode is required for SQLite.
    # ------------------------------------------------------------------
    with op.batch_alter_table("rp_sources") as batch_op:
        batch_op.create_unique_constraint(
            "uq_rp_sources_name",
            ["rules_package_id", "name"],
        )

    # ------------------------------------------------------------------
    # 3. Rename rules_package_manifests → rp_manifests
    #
    # SQLite supports ALTER TABLE ... RENAME TO natively, which Alembic
    # wraps as op.rename_table().  The internal DDL retains the old
    # constraint name (uq_rules_package_manifests_package) because SQLite
    # does not expose ALTER CONSTRAINT; this has no effect on runtime
    # behaviour.  New rows written by the ORM use the ORM's constraint
    # name (uq_rp_manifests_package), which is equivalent.
    # ------------------------------------------------------------------
    op.rename_table("rules_package_manifests", "rp_manifests")


def downgrade() -> None:
    op.rename_table("rp_manifests", "rules_package_manifests")

    with op.batch_alter_table("rp_sources") as batch_op:
        batch_op.drop_constraint("uq_rp_sources_name", type_="unique")

    with op.batch_alter_table("rp_packages") as batch_op:
        batch_op.drop_constraint(
            "uq_rp_packages_name_version_system", type_="unique"
        )
