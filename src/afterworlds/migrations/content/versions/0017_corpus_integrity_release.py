"""SRD corpus-integrity release tables — CRD Issue 5c (#132), ADR-005c Contract A.

Adds the persistence for the frozen source ledger, the frozen reconciliation
policy, the reconciliation member, the leaf/output declared-projection linkage,
and the external release/publication record. RuleChunk (Issue 5a) is unextended;
the projection linkage references ``chunk_id`` from its own table.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rp_corpus_releases",
        sa.Column("package_uuid", sa.String(36), primary_key=True),
        sa.Column("release_version", sa.String(64), nullable=False),
        sa.Column("authoritative_source_hash", sa.String(64), nullable=False),
        sa.Column("transform_config_hash", sa.String(64), nullable=False),
        sa.Column("bundle_root_hash", sa.String(64), nullable=False),
        # Post-persistence proof identities (Component K steps d/e/f): NULL on
        # the initial draft insert (the leaf/chunk/projection rows they are
        # computed from do not exist yet), set exactly once by
        # ``persistence.finalize_release`` from the actual persisted and
        # reconstructed state before the final gate runs.
        sa.Column("evidence_report_hash", sa.String(64), nullable=True),
        sa.Column("persisted_corpus_digest", sa.String(64), nullable=True),
        sa.Column("ledger_hash", sa.String(64), nullable=False),
        sa.Column("policy_hash", sa.String(64), nullable=False),
        sa.Column("reconciliation_hash", sa.String(64), nullable=False),
        sa.Column("corpus_report_reference", sa.String(64), nullable=True),
        sa.Column("transform_config", sa.JSON, nullable=False),
        sa.Column("report_payload", sa.JSON, nullable=True),
        sa.Column("publication_status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_packages.rules_package_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("package_uuid", name="uq_rp_corpus_releases_package"),
    )

    op.create_table(
        "rp_source_ledgers",
        sa.Column("package_uuid", sa.String(36), primary_key=True),
        sa.Column("ledger_hash", sa.String(64), nullable=False),
        sa.Column("source_document", sa.Text, nullable=False),
        sa.Column("source_version", sa.String(32), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("extraction_config", sa.JSON, nullable=False),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "rp_ledger_containers",
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("package_uuid", sa.String(36), nullable=False),
        sa.Column("container_id", sa.String(36), nullable=False),
        sa.Column("container_type", sa.String(32), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("printed_page", sa.Integer, nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_rp_ledger_containers_package", "rp_ledger_containers", ["package_uuid"]
    )

    op.create_table(
        "rp_ledger_leaves",
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("package_uuid", sa.String(36), nullable=False),
        sa.Column("leaf_id", sa.String(36), nullable=False),
        sa.Column("printed_page", sa.Integer, nullable=False),
        sa.Column("page_index", sa.Integer, nullable=False),
        sa.Column("leaf_type", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("char_start", sa.Integer, nullable=False),
        sa.Column("char_end", sa.Integer, nullable=False),
        sa.Column("occurrence_index", sa.Integer, nullable=False),
        sa.Column("container_path", sa.JSON, nullable=False),
        sa.Column("disposition", sa.String(32), nullable=False),
        sa.Column("exclusion_reason_code", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_rp_ledger_leaves_package", "rp_ledger_leaves", ["package_uuid"])
    op.create_index("ix_rp_ledger_leaves_leaf", "rp_ledger_leaves", ["leaf_id"])

    op.create_table(
        "rp_reconciliation_policies",
        sa.Column("package_uuid", sa.String(36), primary_key=True),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("policy_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "rp_reconciliations",
        sa.Column("package_uuid", sa.String(36), primary_key=True),
        sa.Column("policy_hash", sa.String(64), nullable=False),
        sa.Column("inventoried_leaves", sa.Integer, nullable=False),
        sa.Column("represented_leaves", sa.Integer, nullable=False),
        sa.Column("excluded_leaves", sa.Integer, nullable=False),
        sa.Column("unresolved_leaves", sa.Integer, nullable=False),
        sa.Column("findings", sa.JSON, nullable=False),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "rp_corpus_projections",
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("package_uuid", sa.String(36), nullable=False),
        sa.Column("projection_id", sa.String(36), nullable=False),
        sa.Column("leaf_id", sa.String(36), nullable=False),
        sa.Column("chunk_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("cover_start", sa.Integer, nullable=False),
        sa.Column("cover_end", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["package_uuid"],
            ["rp_corpus_releases.package_uuid"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_rp_corpus_projections_package", "rp_corpus_projections", ["package_uuid"]
    )
    op.create_index(
        "ix_rp_corpus_projections_leaf", "rp_corpus_projections", ["leaf_id"]
    )
    op.create_index(
        "ix_rp_corpus_projections_chunk", "rp_corpus_projections", ["chunk_id"]
    )


def downgrade() -> None:
    op.drop_table("rp_corpus_projections")
    op.drop_table("rp_reconciliations")
    op.drop_table("rp_reconciliation_policies")
    op.drop_table("rp_ledger_leaves")
    op.drop_table("rp_ledger_containers")
    op.drop_table("rp_source_ledgers")
    op.drop_table("rp_corpus_releases")
