"""Mechanical-authority projection tables — CRD Issue 5d (#137).

Adds the ``rp_mech_*`` family: one projection header bound to an exact
published CRD Issue 5c release, plus typed rows for accepted spans, retained
acceptance evidence (batches, resolved scope, canonical diff, acceptance
actions), records, components, typed facts, prose bindings, relationships,
build-time-resolved references, and exact leaf-subspan provenance.

Additive only. Nothing existing is altered or dropped: the ``MechanicalEntity``
authority path stays exactly as it is, and no projection is publishable or
reachable as runtime authority at this revision.

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _scoped(*columns: sa.Column) -> tuple[sa.Column, ...]:
    """Standard leading columns for a projection-scoped table."""
    return (
        sa.Column("row_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "projection_uuid",
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        *columns,
    )


def upgrade() -> None:
    op.create_table(
        "rp_mech_projections",
        sa.Column("projection_uuid", sa.String(36), primary_key=True),
        sa.Column(
            "package_uuid",
            sa.String(36),
            sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("release_version", sa.String(64), nullable=False),
        sa.Column("authoritative_source_hash", sa.String(64), nullable=False),
        sa.Column("transform_config_hash", sa.String(64), nullable=False),
        sa.Column("bundle_root_hash", sa.String(64), nullable=False),
        sa.Column("persisted_corpus_digest", sa.String(64), nullable=False),
        sa.Column("semantic_policy_version", sa.String(64), nullable=False),
        sa.Column("semantic_policy_hash", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        # NULL through the draft phase; set once from reconstructed state.
        sa.Column("persisted_state_digest", sa.String(64), nullable=True),
        sa.Column(
            "publication_status", sa.String(32), nullable=False, server_default="draft"
        ),
        sa.Column("created_at", sa.String(64), nullable=False),
    )

    op.create_table(
        "rp_mech_spans",
        *_scoped(
            sa.Column("span_id", sa.String(36), nullable=False, index=True),
            sa.Column("leaf_id", sa.String(64), nullable=False, index=True),
            sa.Column("char_start", sa.Integer, nullable=False),
            sa.Column("char_end", sa.Integer, nullable=False),
            sa.Column("disposition", sa.String(32), nullable=False),
            sa.Column("review_state", sa.String(16), nullable=False),
            sa.Column("non_mechanical_reason_code", sa.String(64), nullable=True),
        ),
    )

    op.create_table(
        "rp_mech_acceptance_batches",
        *_scoped(
            sa.Column("batch_id", sa.String(64), nullable=False, index=True),
            sa.Column("rule", sa.Text, nullable=False),
            sa.Column("semantic_diff_hash", sa.String(64), nullable=False),
        ),
        # The logical identity scope and diff rows are matched on. Defence in
        # depth; reconstruction proves the relation regardless.
        sa.UniqueConstraint(
            "projection_uuid", "batch_id", name="uq_rp_mech_batch_identity"
        ),
    )

    op.create_table(
        "rp_mech_batch_scope",
        *_scoped(
            sa.Column("batch_id", sa.String(64), nullable=False, index=True),
            sa.Column("span_id", sa.String(36), nullable=False),
            sa.Column("ordinal", sa.Integer, nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_batch_diff",
        *_scoped(
            sa.Column("batch_id", sa.String(64), nullable=False, index=True),
            sa.Column("span_id", sa.String(36), nullable=False),
            sa.Column("prior_disposition", sa.String(32), nullable=True),
            sa.Column("prior_reason_code", sa.String(64), nullable=True),
            sa.Column("accepted_disposition", sa.String(32), nullable=False),
            sa.Column("accepted_reason_code", sa.String(64), nullable=True),
        ),
    )

    op.create_table(
        "rp_mech_acceptances",
        *_scoped(
            sa.Column("span_id", sa.String(36), nullable=False, index=True),
            sa.Column("batch_id", sa.String(64), nullable=True),
            sa.Column("reviewer", sa.String(255), nullable=False),
            sa.Column("accepted_at", sa.String(64), nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_records",
        *_scoped(
            sa.Column("record_id", sa.String(36), nullable=False, index=True),
            sa.Column("semantic_key", sa.String(255), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False),
            sa.Column("parent_key", sa.String(255), nullable=True),
        ),
    )

    op.create_table(
        "rp_mech_components",
        *_scoped(
            sa.Column("component_id", sa.String(36), nullable=False, index=True),
            sa.Column("record_key", sa.String(255), nullable=False, index=True),
            sa.Column("semantic_key", sa.String(255), nullable=False),
            sa.Column("handling", sa.String(16), nullable=False),
            sa.Column("irreducibility_reason_code", sa.String(64), nullable=True),
        ),
    )

    op.create_table(
        "rp_mech_facts",
        *_scoped(
            sa.Column("fact_id", sa.String(36), nullable=False, index=True),
            sa.Column("record_key", sa.String(255), nullable=False, index=True),
            sa.Column("component_key", sa.String(255), nullable=False),
            sa.Column("fact_key", sa.String(32), nullable=False),
            # Closed-union discriminator; the payload is that family's
            # validated field set, rebuilt into its declared dataclass on read.
            sa.Column("family", sa.String(64), nullable=False, index=True),
            sa.Column("payload", sa.JSON, nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_prose_bindings",
        *_scoped(
            sa.Column("record_key", sa.String(255), nullable=False, index=True),
            sa.Column("component_key", sa.String(255), nullable=False),
            sa.Column("chunk_id", sa.String(64), nullable=False, index=True),
            sa.Column("irreducibility_reason_code", sa.String(64), nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_relationships",
        *_scoped(
            sa.Column("source_record_key", sa.String(255), nullable=False, index=True),
            sa.Column("target_record_key", sa.String(255), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_references",
        *_scoped(
            sa.Column("from_record_key", sa.String(255), nullable=False, index=True),
            sa.Column("from_component_key", sa.String(255), nullable=False),
            sa.Column("source_text", sa.Text, nullable=False),
            sa.Column("scope_key", sa.String(255), nullable=False, index=True),
            sa.Column("target_record_key", sa.String(255), nullable=False),
        ),
    )

    op.create_table(
        "rp_mech_provenance",
        *_scoped(
            sa.Column("target_kind", sa.String(32), nullable=False, index=True),
            sa.Column("target_key", sa.JSON, nullable=False),
            sa.Column("span_id", sa.String(36), nullable=False, index=True),
            sa.Column("role", sa.String(16), nullable=False),
        ),
    )


def downgrade() -> None:
    for table in (
        "rp_mech_provenance",
        "rp_mech_references",
        "rp_mech_relationships",
        "rp_mech_prose_bindings",
        "rp_mech_facts",
        "rp_mech_components",
        "rp_mech_records",
        "rp_mech_acceptances",
        "rp_mech_batch_diff",
        "rp_mech_batch_scope",
        "rp_mech_acceptance_batches",
        "rp_mech_spans",
        "rp_mech_projections",
    ):
        op.drop_table(table)
