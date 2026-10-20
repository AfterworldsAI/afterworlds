"""Operations-store ORM -- CRD Issue 22 operational records.

One declarative base for the records CRD Issue 22 owns: support actions,
data-request lifecycle, inventories, phase progress, receipts, export
artifacts, anomaly investigation, receipt credentials, entitlement-expiry
register and perpetual BYOK-rights evidence. Every column is on the accepted
field/store retention matrix's proposed allowlist, or is recorded as an
"Extra" in ``docs/architecture/crd-issue-22-operations.md`` with its owner,
purpose and disposition.

The operations store is the control store in a remote deployment (so a
content restore can never rewind a request, its inventory or a receipt --
ADR-021 D5) and the local content store in a local deployment, whose single
owner has no separate authority store. Both chains create the same tables
(``afterworlds.operations.schema``); a remote content store's copies stay
empty.

Append-only streams (``*_events``) refuse UPDATE always and DELETE unless the
reviewed lifecycle path (``afterworlds.operations.lifecycle``) granted it in
the same transaction. Timestamps are ISO-8601 UTC strings.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_TS = sa.String(64)


class OperationsBase(DeclarativeBase):
    """Declarative base for the CRD Issue 22 operations store only."""


class SupportActionEventORM(OperationsBase):
    """Support action event (matrix: support action event / support owner)."""

    __tablename__ = "ops_support_events"

    event_order: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, unique=True)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    operation_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    subject_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    actor_ref: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    action_code: Mapped[str] = mapped_column(sa.String(48), nullable=False)
    target_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    target_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    reason_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    reason_text: Mapped[str | None] = mapped_column(sa.String(280))
    #: Exact signed effect summary (4 dp strings); the entitlement event
    #: remains the authority.
    hosted_credit_delta: Mapped[str | None] = mapped_column(sa.String(32))
    top_up_credit_delta: Mapped[str | None] = mapped_column(sa.String(32))
    requested_at: Mapped[str] = mapped_column(_TS, nullable=False)
    recorded_at: Mapped[str] = mapped_column(_TS, nullable=False)
    #: requested | committed | rejected_precondition | rejected_stale |
    #: conflict | failed
    outcome_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_entitlement_event_id: Mapped[str | None] = mapped_column(sa.String(36))
    idempotency_ref: Mapped[str] = mapped_column(sa.String(96), nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    supersedes_event_id: Mapped[str | None] = mapped_column(sa.String(36))


class DataRequestORM(OperationsBase):
    """Data request header: what was asked, by whom, when. Immutable; every
    state change is a :class:`DataRequestEventORM`."""

    __tablename__ = "ops_data_requests"

    request_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: export | deletion
    kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    #: remote | local
    environment: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    #: story | account
    scope: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    subject_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    #: JSON list of Story IDs named at request time (Story scope: one).
    story_refs: Mapped[str] = mapped_column(sa.Text, nullable=False)
    requester_ref: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    requested_at: Mapped[str] = mapped_column(_TS, nullable=False)
    #: Identity/ownership verification (the authenticated owner session).
    verified_at: Mapped[str] = mapped_column(_TS, nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    #: Export: verified_at + 7 days. Deletion deadlines start at confirmation.
    export_deadline_at: Mapped[str | None] = mapped_column(_TS)


class DataRequestEventORM(OperationsBase):
    """Data request transition (matrix: data request/transition)."""

    __tablename__ = "ops_data_request_events"
    __table_args__ = (sa.UniqueConstraint("request_id", "revision"),)

    event_order: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, unique=True)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), nullable=False
    )
    revision: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    state: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    attempt_id: Mapped[str | None] = mapped_column(sa.String(36))
    actor_ref: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    authorization_code: Mapped[str | None] = mapped_column(sa.String(32))
    confirmation_ref: Mapped[str | None] = mapped_column(sa.String(36))
    scope_revision: Mapped[str | None] = mapped_column(sa.String(64))
    reason_code: Mapped[str | None] = mapped_column(sa.String(32))
    reason_text: Mapped[str | None] = mapped_column(sa.String(280))
    recorded_at: Mapped[str] = mapped_column(_TS, nullable=False)
    confirmed_at: Mapped[str | None] = mapped_column(_TS)
    approved_at: Mapped[str | None] = mapped_column(_TS)
    closed_at: Mapped[str | None] = mapped_column(_TS)
    live_deadline_at: Mapped[str | None] = mapped_column(_TS)
    backup_deadline_at: Mapped[str | None] = mapped_column(_TS)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    supersedes_event_id: Mapped[str | None] = mapped_column(sa.String(36))


class RequestInventoryORM(OperationsBase):
    """Durable pre-detachment inventory (ADR-0004 amendment): opaque IDs
    only, recorded before any parent link is removed. Extra record."""

    __tablename__ = "ops_request_inventory"
    __table_args__ = (
        sa.UniqueConstraint("request_id", "resource_class", "resource_id"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), nullable=False
    )
    #: story | arc | chapter | node | turn
    resource_class: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    resource_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    recorded_at: Mapped[str] = mapped_column(_TS, nullable=False)


class PhaseEventORM(OperationsBase):
    """Per-store/per-attempt progress (matrix receipt ``store_id``/``phase``/
    ``phase_observed_at``/``verification_ref``). Append-only."""

    __tablename__ = "ops_phase_events"

    event_order: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, unique=True)
    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), nullable=False
    )
    attempt_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    phase_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    #: pending | succeeded | failed | unverified | not_applicable |
    #: dependency_unavailable
    outcome_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    #: JSON object of class -> count (opaque counts only).
    counts_json: Mapped[str] = mapped_column(sa.Text, nullable=False, default="{}")
    detail_code: Mapped[str | None] = mapped_column(sa.String(48))
    observed_at: Mapped[str] = mapped_column(_TS, nullable=False)
    deadline_at: Mapped[str | None] = mapped_column(_TS)


class ReceiptORM(OperationsBase):
    """Export manifest / deletion receipt (matrix). ``body_json`` is built
    only from the allowlisted receipt fields (``operations.receipts``)."""

    __tablename__ = "ops_receipts"

    receipt_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), nullable=False
    )
    #: export_manifest | deletion_receipt
    receipt_kind: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    attempt_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    body_json: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[str] = mapped_column(_TS, nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class ExportArtifactORM(OperationsBase):
    """Service-managed export artifact inventory (matrix object inventory /
    artifact owner). The locator is a server path, never a URL or token."""

    __tablename__ = "ops_export_artifacts"

    artifact_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), nullable=False
    )
    attempt_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    storage_locator: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: staging | available | failed | expired | removed
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    created_at: Mapped[str] = mapped_column(_TS, nullable=False)
    available_at: Mapped[str | None] = mapped_column(_TS)
    expires_at: Mapped[str] = mapped_column(_TS, nullable=False)
    removed_at: Mapped[str | None] = mapped_column(_TS)
    size_bytes: Mapped[int | None] = mapped_column(sa.Integer)
    #: When a download to the authenticated owner completed (the response
    #: body was fully sent). Account erasure waits for it (#206 §5).
    delivered_at: Mapped[str | None] = mapped_column(_TS)


class ReceiptCredentialORM(OperationsBase):
    """Post-closure receipt access: only the SHA-256 verifier of a 256-bit
    credential issued once at confirmation. Extra record (Required
    Behavior 5: status/receipt stays reachable after closure, never by a
    guessable request ID)."""

    __tablename__ = "ops_receipt_credentials"

    request_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("ops_data_requests.request_id"), primary_key=True
    )
    credential_verifier: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, unique=True
    )
    issued_at: Mapped[str] = mapped_column(_TS, nullable=False)


class AnomalyEventORM(OperationsBase):
    """Anomaly/investigation event (matrix). Append-only."""

    __tablename__ = "ops_anomaly_events"

    event_order: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, unique=True)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    anomaly_id: Mapped[str] = mapped_column(sa.String(96), nullable=False, index=True)
    subject_ref: Mapped[str | None] = mapped_column(sa.String(36))
    source_kind: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    observed_at: Mapped[str] = mapped_column(_TS, nullable=False)
    safe_signal_code: Mapped[str] = mapped_column(sa.String(48), nullable=False)
    #: open | investigating | closed
    investigation_state: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    actor_ref: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    note_code: Mapped[str | None] = mapped_column(sa.String(32))
    note_text: Mapped[str | None] = mapped_column(sa.String(280))
    supersedes_event_id: Mapped[str | None] = mapped_column(sa.String(36))


class EntitlementExpiryORM(OperationsBase):
    """Register of closed subjects whose entitlement history expired through
    the entitlement owner's governed path, kept outside the content snapshot
    so a restore re-applies the expiry. Extra record."""

    __tablename__ = "ops_entitlement_expiries"

    subject_ref: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    closed_at: Mapped[str] = mapped_column(_TS, nullable=False)
    expired_at: Mapped[str] = mapped_column(_TS, nullable=False)
    event_count: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class RestoreEnforcementORM(OperationsBase):
    """Proof that every active deletion and retention expiry was re-applied
    to a restored store before it is verified and served. Extra record
    (control store); opaque counts only."""

    __tablename__ = "ops_restore_enforcements"

    restore_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    enforced_at: Mapped[str] = mapped_column(_TS, nullable=False)
    summary_json: Mapped[str] = mapped_column(sa.Text, nullable=False)


class RightsEvidenceORM(OperationsBase):
    """Minimum perpetual BYOK-rights evidence (matrix: right/license ID,
    opaque subject-link token, right kind/status, purchase time,
    source/reference ID, verification metadata). Written by the entitlement
    owner from the licence event before closure; survives the cloud profile."""

    __tablename__ = "ops_rights_evidence"

    rights_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    subject_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    right_kind: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    purchased_at: Mapped[str] = mapped_column(_TS, nullable=False)
    external_source: Mapped[str | None] = mapped_column(sa.String(64))
    external_reference_id: Mapped[str | None] = mapped_column(sa.String(128))
    source_event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    recorded_at: Mapped[str] = mapped_column(_TS, nullable=False)
    annual_review_at: Mapped[str] = mapped_column(_TS, nullable=False)


class DisposalGrantORM(OperationsBase):
    """A one-transaction permission for the reviewed lifecycle path to delete
    one row of an append-only table (by ``rowid``). Inserted and removed by
    ``operations.lifecycle`` inside the deleting transaction, so no grant
    outlives it and ordinary DELETE stays refused."""

    __tablename__ = "lifecycle_disposal_grants"
    __table_args__ = (sa.UniqueConstraint("table_name", "row_key"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    table_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    row_key: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    operation_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False)
