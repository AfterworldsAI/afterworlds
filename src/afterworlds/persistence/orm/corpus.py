"""ORM models for the Issue 5c corpus-integrity release (prefix ``rp_``).

These tables persist the frozen source ledger, the frozen reconciliation policy,
the reconciliation member, the leaf/output declared-projection linkage, and the
external release/publication record for a corpus release (Completion Contract A).

They do **not** extend ``RuleChunk`` or any Issue 5a model — the authoritative
source-text records still persist into the existing ``rp_chunks`` table, and the
projection linkage lives in its own table referencing ``chunk_id``. All tables
are intra-subsystem (``rp_*``) and carry no cross-subsystem FKs.

The persisted-corpus digest is recomputable from these rows, so tampering with
any persisted disposition, reason, policy reference, projection link, or finding
changes the recomputed digest and fails publication (Component I).
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class CorpusReleaseORM(Base):
    """External release/publication record — five top-level hashes (A/I)."""

    __tablename__ = "rp_corpus_releases"
    __table_args__ = (
        sa.UniqueConstraint("package_uuid", name="uq_rp_corpus_releases_package"),
    )

    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_packages.rules_package_id", ondelete="CASCADE"),
        primary_key=True,
    )
    release_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    authoritative_source_hash: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    transform_config_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    bundle_root_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # These three are the post-persistence proof identities (Component K steps
    # d/e/f): they cannot be known when the draft row is first inserted, before
    # the leaf/chunk/projection rows exist to reconstruct and digest. They stay
    # NULL from insertion through the draft phase and are set exactly once, by
    # ``persistence.finalize_release``, from the actual persisted/reconstructed
    # state — never defaulted, never caller-supplied as evidence of persistence.
    evidence_report_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    persisted_corpus_digest: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    # Versioned, direct SQLite trust seam consumed by CRD Issue 5d.  These are
    # post-persistence values and remain nullable only so migration 0022 can
    # represent pre-amendment releases until 5c verified reuse backfills them.
    corpus_contract_version: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    operational_corpus_digest: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    ledger_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    reconciliation_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    corpus_report_reference: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    transform_config: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)
    report_payload: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
    publication_status: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, default="draft"
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class SourceLedgerORM(Base):
    """Frozen source-ledger header — one row per release (Component C)."""

    __tablename__ = "rp_source_ledgers"

    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    ledger_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    source_document: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_sha256: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    extraction_config: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class LedgerContainerORM(Base):
    """A structural container of the frozen ledger (Component C)."""

    __tablename__ = "rp_ledger_containers"

    row_id: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    container_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    container_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    printed_page: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)


class LedgerLeafORM(Base):
    """An atomic coverage leaf with its final disposition (Components C/D)."""

    __tablename__ = "rp_ledger_leaves"

    row_id: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leaf_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    printed_page: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    page_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    leaf_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    char_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    occurrence_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    container_path: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False)
    disposition: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    exclusion_reason_code: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    # Table position for TABLE_CELL leaves (Component F, PR #134 table fidelity):
    # the reconstructed table's id and the cell's 0-based row/column. NULL for
    # every non-table leaf. Persisting these attests table structure so it is not
    # flattened into paragraphs, and the digest binds them via the ledger payload.
    table_id: Mapped[str | None] = mapped_column(sa.String(36), nullable=True)
    table_row: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    table_col: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    # Page-segment index of a page-spanning logical table (0 = first page, 1+ =
    # continuation); NULL for non-table leaves. A repeated continuation header is
    # ``table_row == 0`` with ``table_segment > 0`` (PR #134 R15 F3).
    table_segment: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)


class ReconciliationPolicyORM(Base):
    """The frozen reconciliation policy as applied (Component B)."""

    __tablename__ = "rp_reconciliation_policies"

    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    policy_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class ReconciliationORM(Base):
    """The reconciliation member header + findings (Component D)."""

    __tablename__ = "rp_reconciliations"

    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    inventoried_leaves: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    represented_leaves: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    excluded_leaves: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    unresolved_leaves: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    findings: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class CorpusProjectionORM(Base):
    """A declared-projection edge: leaf -> chunk under a policy role (D/G).

    References ``chunk_id`` without extending ``RuleChunk``.
    """

    __tablename__ = "rp_corpus_projections"

    row_id: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    projection_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    leaf_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    chunk_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    cover_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    cover_end: Mapped[int] = mapped_column(sa.Integer, nullable=False)
