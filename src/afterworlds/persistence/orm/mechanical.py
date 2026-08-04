"""Mechanical-authority projection tables — CRD Issue 5d.

Typed, reconstructable state, not an opaque blob: every span, acceptance
record, record, component, fact, prose binding, relationship, reference, and
provenance edge is its own row, so the complete projection and its proof can be
rebuilt from the database alone (#137 contract 5).

Facts are the one place with a JSON column, and it is deliberately *not* a
generic escape hatch. ``family`` is the closed union's discriminator, and the
payload is that family's validated field set — reconstruction rebuilds the
declared frozen dataclass through it and fails on an unknown family. Storing it
this way is what lets a later PR add a typed family without a migration, which
is exactly the additive-extension capability #137 asks for; what it must never
become is a bag that accepts an undeclared shape.

Everything is scoped by ``projection_uuid`` and cascades from the projection
row, so two projections over the same 5c release coexist without collision.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class MechanicalProjectionORM(Base):
    """One mechanical-authority projection over an exact published 5c release."""

    __tablename__ = "rp_mech_projections"

    projection_uuid: Mapped[str] = mapped_column(sa.String(36), primary_key=True)

    # Exact 5c release binding (#137 contract 1). package_uuid is a real FK, so
    # a projection cannot outlive or precede the release it claims.
    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    release_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    authoritative_source_hash: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    transform_config_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    bundle_root_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    persisted_corpus_digest: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    # Declared semantic policy, retained so a historical projection states the
    # policy it was accepted under rather than being reinterpreted later.
    semantic_policy_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    semantic_policy_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    payload_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # Set exactly once, from state actually read back out of these tables. It
    # cannot be known when the draft rows are first written, so it stays NULL
    # through the draft phase and is never caller-supplied as proof.
    persisted_state_digest: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    publication_status: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, default="draft"
    )
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    # Publication evidence (#137 contract 5). All NULL through the draft phase:
    # the gate runs against reconstructed state, so none of these can exist
    # before that state does. They are written by one atomic publication and
    # never by a draft write.
    oracle_identity: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    evidence_report_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    report_payload: Mapped[dict[str, Any] | None] = mapped_column(
        sa.JSON, nullable=True
    )
    published_at: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


class MechanicalActiveProjectionORM(Base):
    """The one active mechanical projection of a Rules Package.

    ``package_uuid`` is the primary key, so active authority cannot split: the
    database itself refuses a second active row for a package rather than
    relying on application code to notice. Competing activation is therefore a
    typed rejection, not a race whose winner depends on ordering.

    Activation is a separate row rather than a flag on the projection header
    because "which projection is active" is a property of the *package*. A
    boolean per projection would let two rows both claim it, which is exactly
    the split this table forecloses.
    """

    __tablename__ = "rp_mech_active_projections"

    package_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_corpus_releases.package_uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    projection_uuid: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    activated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class _ProjectionScoped(Base):
    """Mixin base: every projection-scoped table cascades from its projection."""

    __abstract__ = True

    row_id: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )

    @staticmethod
    def _projection_fk() -> Mapped[str]:
        return mapped_column(
            sa.String(36),
            sa.ForeignKey("rp_mech_projections.projection_uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


class MechanicalSpanORM(_ProjectionScoped):
    """One accepted semantic span of the bound release."""

    __tablename__ = "rp_mech_spans"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    span_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    leaf_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    char_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    disposition: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    review_state: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    non_mechanical_reason_code: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )


class MechanicalAcceptanceBatchORM(_ProjectionScoped):
    """Retained batch-acceptance evidence header.

    ``(projection_uuid, batch_id)`` is the logical identity its scope and diff
    rows are matched on, so it is unique at the database level too. Defence in
    depth only: reconstruction still proves the relation, because a corrupted
    database or one created with constraints disabled must still be detected.
    """

    __tablename__ = "rp_mech_acceptance_batches"
    __table_args__ = (
        sa.UniqueConstraint(
            "projection_uuid", "batch_id", name="uq_rp_mech_batch_identity"
        ),
    )

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    batch_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    rule: Mapped[str] = mapped_column(sa.Text, nullable=False)
    semantic_diff_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class MechanicalBatchScopeORM(_ProjectionScoped):
    """One member of a batch's exact resolved scope."""

    __tablename__ = "rp_mech_batch_scope"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    batch_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    span_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    ordinal: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class MechanicalBatchDiffORM(_ProjectionScoped):
    """One retained transition of a batch's canonical semantic diff."""

    __tablename__ = "rp_mech_batch_diff"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    batch_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    span_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    prior_disposition: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    prior_reason_code: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    accepted_disposition: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    accepted_reason_code: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )


class MechanicalAcceptanceORM(_ProjectionScoped):
    """One explicit acceptance action."""

    __tablename__ = "rp_mech_acceptances"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    span_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    batch_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    reviewer: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    accepted_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class MechanicalRecordORM(_ProjectionScoped):
    """One semantic record."""

    __tablename__ = "rp_mech_records"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    record_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    semantic_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    parent_key: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)


class MechanicalComponentORM(_ProjectionScoped):
    """One publishable component of a record."""

    __tablename__ = "rp_mech_components"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    component_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    semantic_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    handling: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    irreducibility_reason_code: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )


class MechanicalFactORM(_ProjectionScoped):
    """One typed fact of the closed union."""

    __tablename__ = "rp_mech_facts"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    fact_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    component_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    fact_key: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    family: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)


class MechanicalProseBindingORM(_ProjectionScoped):
    """Exact governing prose bound to the authoritative 5c chunk."""

    __tablename__ = "rp_mech_prose_bindings"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    component_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    chunk_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    irreducibility_reason_code: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )


class MechanicalRelationshipORM(_ProjectionScoped):
    """A typed relationship between two records."""

    __tablename__ = "rp_mech_relationships"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    source_record_key: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, index=True
    )
    target_record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class MechanicalReferenceORM(_ProjectionScoped):
    """A build-time-resolved source reference."""

    __tablename__ = "rp_mech_references"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    from_record_key: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, index=True
    )
    from_component_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    source_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    scope_key: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    target_record_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)


class MechanicalProvenanceORM(_ProjectionScoped):
    """One exact leaf-subspan claim by a representation element."""

    __tablename__ = "rp_mech_provenance"

    projection_uuid: Mapped[str] = _ProjectionScoped._projection_fk()
    target_kind: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    target_key: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False)
    span_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(sa.String(16), nullable=False)
