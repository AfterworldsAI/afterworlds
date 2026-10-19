"""Control-store ORM (ADR-021 D5) -- identity, sessions, closure, suppression.

A separate declarative base and database from the content store, so restoring
a content snapshot cannot revive a revoked session, reopen a closed account or
resurrect a suppressed Story. Every column is on the accepted field/store
retention matrix's proposed remote allowlist (``docs/architecture/
remote-identity-and-storage.md`` maps each one); nothing holds profile JSON,
a raw token, a raw recovery code or a BYOK key.

Timestamps are ISO-8601 UTC strings, like the content store.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ControlBase(DeclarativeBase):
    """Declarative base for the control store only."""


class HostedAccountORM(ControlBase):
    """Hosted account (matrix: hosted account record)."""

    __tablename__ = "hosted_accounts"

    account_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    identity_subject_ref: Mapped[str] = mapped_column(
        sa.String(36), nullable=False, unique=True
    )
    # "active" | "closed"
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    closed_at: Mapped[str | None] = mapped_column(sa.String(64))
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class IdentityPrincipalORM(ControlBase):
    """Authenticating principal (matrix: authentication record + profile contact).

    ``contact_address`` is both the matrix profile's ``contact_address`` (account
    notices/recovery) and the credential locator. ``account_id`` is null until
    the address is verified at enrollment.
    """

    __tablename__ = "identity_principals"

    principal_ref: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    account_id: Mapped[str | None] = mapped_column(
        sa.String(36), sa.ForeignKey("hosted_accounts.account_id"), unique=True
    )
    contact_address: Mapped[str] = mapped_column(
        sa.String(320), nullable=False, unique=True
    )
    password_verifier: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    address_verified_at: Mapped[str | None] = mapped_column(sa.String(64))
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class AuthSessionORM(ControlBase):
    """Server-side session; only the token's SHA-256 verifier is stored."""

    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    principal_ref: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("identity_principals.principal_ref"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    # "sojourner" | "staff" -- distinct contexts, never interchangeable.
    context: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    token_verifier: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, unique=True
    )
    issued_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    expires_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    revoked_at: Mapped[str | None] = mapped_column(sa.String(64))
    status_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class VerificationOperationORM(ControlBase):
    """Enrollment verification or account recovery operation (hashed code)."""

    __tablename__ = "verification_operations"

    operation_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    principal_ref: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("identity_principals.principal_ref"),
        nullable=False,
        index=True,
    )
    # "enrollment" | "recovery"
    kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    code_verifier: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    issued_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    expires_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    used_at: Mapped[str | None] = mapped_column(sa.String(64))
    revoked_at: Mapped[str | None] = mapped_column(sa.String(64))


class AdminBindingORM(ControlBase):
    """Sole administrator binding (matrix: sole administrator binding)."""

    __tablename__ = "admin_bindings"

    binding_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    principal_ref: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("identity_principals.principal_ref"),
        nullable=False,
    )
    role_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    provisioned_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    provisioning_operation_ref: Mapped[str] = mapped_column(
        sa.String(36), nullable=False
    )
    revoked_at: Mapped[str | None] = mapped_column(sa.String(64))
    reason_code: Mapped[str | None] = mapped_column(sa.String(32))
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class IdentityAuditEventORM(ControlBase):
    """Minimized identity/administrator-action receipt (append-only by trigger).

    Codes and opaque references only: no address, password, token, code or
    free text beyond the bounded ``reason_text``.
    """

    __tablename__ = "identity_audit_events"

    event_order: Mapped[int] = mapped_column(
        sa.Integer, primary_key=True, autoincrement=True
    )
    event_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, unique=True)
    operation_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    actor_ref: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    action_code: Mapped[str] = mapped_column(sa.String(48), nullable=False)
    target_ref: Mapped[str | None] = mapped_column(sa.String(36))
    reason_code: Mapped[str | None] = mapped_column(sa.String(32))
    reason_text: Mapped[str | None] = mapped_column(sa.String(280))
    outcome_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    recorded_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)


class DeletionSuppressionORM(ControlBase):
    """Deletion suppression (matrix: deletion suppression / restore owner).

    The authoritative instruction CRD Issue 22 supplies; held outside the
    content snapshot it protects. ``story_refs`` is a JSON list of Story IDs.
    """

    __tablename__ = "deletion_suppressions"

    suppression_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    schema_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    subject_ref: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    story_refs: Mapped[str] = mapped_column(sa.Text, nullable=False)
    request_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    # "story" | "account"
    scope: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    effective_boundary_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    last_verified_at: Mapped[str | None] = mapped_column(sa.String(64))
    backup_horizon_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    replay_horizon_at: Mapped[str | None] = mapped_column(sa.String(64))
    # "active" | "released"
    status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    release_verified_at: Mapped[str | None] = mapped_column(sa.String(64))
    annual_review_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class BackupInventoryORM(ControlBase):
    """Object/backup inventory (matrix: object/backup inventory / storage owner)."""

    __tablename__ = "backup_inventory"

    backup_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    store_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    # Protected locator: a server path; never an auth URL or token.
    storage_locator: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # "content_snapshot"
    class_code: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    original_capture_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    copied_from_backup_id: Mapped[str | None] = mapped_column(sa.String(36))
    policy_version: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    expires_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    disposed_at: Mapped[str | None] = mapped_column(sa.String(64))
    # "verified" | "unverified" | "inaccessible"
    verification_status: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    #: "removed" | "verified_absent" -- the proof recorded with ``disposed_at``.
    disposal_evidence: Mapped[str | None] = mapped_column(sa.String(16))
    #: JSON list of suppression IDs whose content this capture proved absent.
    clean_suppression_ids: Mapped[str] = mapped_column(
        sa.Text, nullable=False, default="[]"
    )


class RestoreRecordORM(ControlBase):
    """A restore of a content snapshot; the app will not serve while pending."""

    __tablename__ = "restore_records"

    restore_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    backup_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("backup_inventory.backup_id"), nullable=False
    )
    restored_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # "copying" | "pending_enforcement" | "verified" | "superseded"
    status: Mapped[str] = mapped_column(sa.String(24), nullable=False)
    verified_at: Mapped[str | None] = mapped_column(sa.String(64))


class DeploymentMarkerORM(ControlBase):
    """Binds this control store to the one content store it governs.

    Written only when a fresh deployment's initialization completes, so every
    reader of the binding sees a completed deployment or none."""

    __tablename__ = "deployment_marker"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    content_store_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    initialized_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class DeploymentInitializationORM(ControlBase):
    """A fresh deployment's initialization in progress (ADR-021 D7).

    Committed while the recorded content and vector targets are proven empty,
    before anything is created; its id is the deployment identity every
    resumed attempt on those same targets completes. Removed in the
    transaction that writes :class:`DeploymentMarkerORM`."""

    __tablename__ = "deployment_initialization"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    content_store_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
    started_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    # The physical targets proven fresh (normalized absolute paths).
    content_target: Mapped[str] = mapped_column(sa.Text, nullable=False)
    vector_target: Mapped[str] = mapped_column(sa.Text, nullable=False)
