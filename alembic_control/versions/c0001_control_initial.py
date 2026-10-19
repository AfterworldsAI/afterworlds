"""Initial remote control store -- prerequisite #205 (ADR-021 D5).

Accounts, principals, sessions, verification/recovery operations, the sole
administrator binding, identity audit events, deletion suppressions, backup
inventory, restore records and the deployment marker. The audit stream is
append-only at the database layer, like ``entitlement_event``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "c0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

_TS = sa.String(64)


def upgrade() -> None:
    op.create_table(
        "hosted_accounts",
        sa.Column("account_id", sa.String(36), primary_key=True),
        sa.Column("identity_subject_ref", sa.String(36), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.Column("closed_at", _TS),
        sa.Column("policy_version", sa.String(32), nullable=False),
    )
    op.create_table(
        "identity_principals",
        sa.Column("principal_ref", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("hosted_accounts.account_id"),
            unique=True,
        ),
        sa.Column("contact_address", sa.String(320), nullable=False, unique=True),
        sa.Column("password_verifier", sa.String(256), nullable=False),
        sa.Column("address_verified_at", _TS),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column(
            "principal_ref",
            sa.String(36),
            sa.ForeignKey("identity_principals.principal_ref"),
            nullable=False,
            index=True,
        ),
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("context", sa.String(16), nullable=False),
        sa.Column("token_verifier", sa.String(64), nullable=False, unique=True),
        sa.Column("issued_at", _TS, nullable=False),
        sa.Column("expires_at", _TS, nullable=False),
        sa.Column("revoked_at", _TS),
        sa.Column("status_code", sa.String(32), nullable=False),
    )
    op.create_table(
        "verification_operations",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column(
            "principal_ref",
            sa.String(36),
            sa.ForeignKey("identity_principals.principal_ref"),
            nullable=False,
            index=True,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("code_verifier", sa.String(64), nullable=False),
        sa.Column("issued_at", _TS, nullable=False),
        sa.Column("expires_at", _TS, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("used_at", _TS),
        sa.Column("revoked_at", _TS),
    )
    op.create_table(
        "admin_bindings",
        sa.Column("binding_id", sa.String(36), primary_key=True),
        sa.Column(
            "principal_ref",
            sa.String(36),
            sa.ForeignKey("identity_principals.principal_ref"),
            nullable=False,
        ),
        sa.Column("role_code", sa.String(32), nullable=False),
        sa.Column("provisioned_at", _TS, nullable=False),
        sa.Column("provisioning_operation_ref", sa.String(36), nullable=False),
        sa.Column("revoked_at", _TS),
        sa.Column("reason_code", sa.String(32)),
        sa.Column("policy_version", sa.String(32), nullable=False),
    )
    # The sole initial administrator: at most one active binding, ever.
    op.create_index(
        "uq_admin_bindings_active",
        "admin_bindings",
        ["role_code"],
        unique=True,
        sqlite_where=sa.text("revoked_at IS NULL"),
    )
    op.create_table(
        "identity_audit_events",
        sa.Column("event_order", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("operation_id", sa.String(36), nullable=False),
        sa.Column("actor_ref", sa.String(64), nullable=False),
        sa.Column("action_code", sa.String(48), nullable=False),
        sa.Column("target_ref", sa.String(36)),
        sa.Column("reason_code", sa.String(32)),
        sa.Column("reason_text", sa.String(280)),
        sa.Column("outcome_code", sa.String(32), nullable=False),
        sa.Column("recorded_at", _TS, nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
    )
    for verb in ("UPDATE", "DELETE"):
        op.execute(
            f"""
            CREATE TRIGGER prevent_identity_audit_event_{verb.lower()}
            BEFORE {verb} ON identity_audit_events
            BEGIN
                SELECT RAISE(ABORT,
                    'identity_audit_events is append-only: {verb} is forbidden');
            END
            """
        )
    op.create_table(
        "deletion_suppressions",
        sa.Column("suppression_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("subject_ref", sa.String(36), nullable=False),
        sa.Column("story_refs", sa.Text, nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("effective_boundary_at", _TS, nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("last_verified_at", _TS),
        sa.Column("backup_horizon_at", _TS, nullable=False),
        sa.Column("replay_horizon_at", _TS),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("release_verified_at", _TS),
        sa.Column("annual_review_at", _TS, nullable=False),
    )
    op.create_table(
        "backup_inventory",
        sa.Column("backup_id", sa.String(36), primary_key=True),
        sa.Column("store_id", sa.String(36), nullable=False),
        sa.Column("storage_locator", sa.Text, nullable=False),
        sa.Column("class_code", sa.String(32), nullable=False),
        sa.Column("original_capture_at", _TS, nullable=False),
        sa.Column("copied_from_backup_id", sa.String(36)),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("expires_at", _TS, nullable=False),
        sa.Column("disposed_at", _TS),
        sa.Column("verification_status", sa.String(16), nullable=False),
        sa.Column("disposal_evidence", sa.String(16)),
        sa.Column(
            "clean_suppression_ids", sa.Text, nullable=False, server_default="[]"
        ),
    )
    op.create_table(
        "restore_records",
        sa.Column("restore_id", sa.String(36), primary_key=True),
        sa.Column(
            "backup_id",
            sa.String(36),
            sa.ForeignKey("backup_inventory.backup_id"),
            nullable=False,
        ),
        sa.Column("restored_at", _TS, nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("verified_at", _TS),
    )
    op.create_table(
        "deployment_marker",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content_store_id", sa.String(36), nullable=False),
        sa.Column("initialized_at", _TS, nullable=False),
    )
    op.create_table(
        "deployment_initialization",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("content_store_id", sa.String(36), nullable=False),
        sa.Column("started_at", _TS, nullable=False),
        sa.Column("content_target", sa.Text, nullable=False),
        sa.Column("vector_target", sa.Text, nullable=False),
    )


def downgrade() -> None:
    for table in (
        "deployment_initialization",
        "deployment_marker",
        "restore_records",
        "backup_inventory",
        "deletion_suppressions",
    ):
        op.drop_table(table)
    for verb in ("update", "delete"):
        op.execute(f"DROP TRIGGER IF EXISTS prevent_identity_audit_event_{verb}")
    op.drop_table("identity_audit_events")
    op.drop_index("uq_admin_bindings_active", table_name="admin_bindings")
    for table in (
        "admin_bindings",
        "verification_operations",
        "auth_sessions",
        "identity_principals",
        "hosted_accounts",
    ):
        op.drop_table(table)
