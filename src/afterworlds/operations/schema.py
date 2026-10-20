"""Frozen DDL for the CRD Issue 22 operations store (revision 1).

Shared by the content chain (``0046``: local deployments keep their
operational records beside the local owner's content) and the control chain
(``c0002``: remote records live outside the content snapshot). Also the
guarded-lifecycle triggers that replace plain "DELETE is forbidden" triggers:
UPDATE stays refused, and DELETE is refused unless the reviewed lifecycle
path recorded a grant for that row in the same transaction
(``afterworlds.operations.lifecycle``).
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

_TS = sa.String(64)

APPEND_ONLY = (
    "ops_support_events",
    "ops_data_request_events",
    "ops_phase_events",
    "ops_anomaly_events",
    "ops_receipts",
)


def guarded_delete_trigger(table: str, name: str | None = None) -> str:
    """DELETE refused unless a same-transaction lifecycle grant names the row."""
    trigger = name or f"prevent_{table}_delete"
    return (
        f"CREATE TRIGGER {trigger} BEFORE DELETE ON {table} "
        "WHEN NOT EXISTS (SELECT 1 FROM lifecycle_disposal_grants g "
        f"WHERE g.table_name = '{table}' AND g.row_key = OLD.rowid) "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only: DELETE is forbidden'); "
        "END"
    )


def plain_delete_trigger(table: str, name: str | None = None) -> str:
    """The original unconditional trigger (for downgrade)."""
    trigger = name or f"prevent_{table}_delete"
    return (
        f"CREATE TRIGGER {trigger} BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only: DELETE is forbidden'); "
        "END"
    )


def update_trigger(table: str) -> str:
    return (
        f"CREATE TRIGGER prevent_{table}_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only: UPDATE is forbidden'); "
        "END"
    )


def create_operations_schema(op: Any) -> None:
    op.create_table(
        "lifecycle_disposal_grants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("table_name", sa.String(64), nullable=False),
        sa.Column("row_key", sa.Integer, nullable=False),
        sa.Column("operation_ref", sa.String(36), nullable=False),
        sa.UniqueConstraint("table_name", "row_key"),
    )
    op.create_table(
        "ops_support_events",
        sa.Column("event_order", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("operation_id", sa.String(36), nullable=False, index=True),
        sa.Column("subject_ref", sa.String(36), nullable=False, index=True),
        sa.Column("actor_ref", sa.String(64), nullable=False),
        sa.Column("action_code", sa.String(48), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_ref", sa.String(36), nullable=False),
        sa.Column("reason_code", sa.String(32), nullable=False),
        sa.Column("reason_text", sa.String(280)),
        sa.Column("hosted_credit_delta", sa.String(32)),
        sa.Column("top_up_credit_delta", sa.String(32)),
        sa.Column("requested_at", _TS, nullable=False),
        sa.Column("recorded_at", _TS, nullable=False),
        sa.Column("outcome_code", sa.String(32), nullable=False),
        sa.Column("source_entitlement_event_id", sa.String(36)),
        sa.Column("idempotency_ref", sa.String(96), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("supersedes_event_id", sa.String(36)),
    )
    op.create_table(
        "ops_data_requests",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("subject_ref", sa.String(36), nullable=False, index=True),
        sa.Column("story_refs", sa.Text, nullable=False),
        sa.Column("requester_ref", sa.String(64), nullable=False),
        sa.Column("requested_at", _TS, nullable=False),
        sa.Column("verified_at", _TS, nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("export_deadline_at", _TS),
    )
    op.create_table(
        "ops_data_request_events",
        sa.Column("event_order", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("attempt_id", sa.String(36)),
        sa.Column("actor_ref", sa.String(64), nullable=False),
        sa.Column("authorization_code", sa.String(32)),
        sa.Column("confirmation_ref", sa.String(36)),
        sa.Column("scope_revision", sa.String(64)),
        sa.Column("reason_code", sa.String(32)),
        sa.Column("reason_text", sa.String(280)),
        sa.Column("recorded_at", _TS, nullable=False),
        sa.Column("confirmed_at", _TS),
        sa.Column("approved_at", _TS),
        sa.Column("closed_at", _TS),
        sa.Column("live_deadline_at", _TS),
        sa.Column("backup_deadline_at", _TS),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("supersedes_event_id", sa.String(36)),
        sa.UniqueConstraint("request_id", "revision"),
    )
    op.create_table(
        "ops_request_inventory",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            nullable=False,
        ),
        sa.Column("resource_class", sa.String(16), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("recorded_at", _TS, nullable=False),
        sa.UniqueConstraint("request_id", "resource_class", "resource_id"),
    )
    op.create_table(
        "ops_phase_events",
        sa.Column("event_order", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            nullable=False,
        ),
        sa.Column("attempt_id", sa.String(36), nullable=False),
        sa.Column("phase_code", sa.String(32), nullable=False),
        sa.Column("outcome_code", sa.String(32), nullable=False),
        sa.Column("counts_json", sa.Text, nullable=False),
        sa.Column("detail_code", sa.String(48)),
        sa.Column("observed_at", _TS, nullable=False),
        sa.Column("deadline_at", _TS),
    )
    op.create_table(
        "ops_receipts",
        sa.Column("receipt_id", sa.String(36), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            nullable=False,
        ),
        sa.Column("receipt_kind", sa.String(24), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("attempt_id", sa.String(36), nullable=False),
        sa.Column("body_json", sa.Text, nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
    )
    op.create_table(
        "ops_export_artifacts",
        sa.Column("artifact_id", sa.String(36), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            nullable=False,
        ),
        sa.Column("attempt_id", sa.String(36), nullable=False),
        sa.Column("storage_locator", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("available_at", _TS),
        sa.Column("expires_at", _TS, nullable=False),
        sa.Column("removed_at", _TS),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("delivered_at", _TS),
    )
    op.create_table(
        "ops_receipt_credentials",
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("ops_data_requests.request_id"),
            primary_key=True,
        ),
        sa.Column("credential_verifier", sa.String(64), nullable=False, unique=True),
        sa.Column("issued_at", _TS, nullable=False),
    )
    op.create_table(
        "ops_anomaly_events",
        sa.Column("event_order", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("anomaly_id", sa.String(96), nullable=False, index=True),
        sa.Column("subject_ref", sa.String(36)),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("observed_at", _TS, nullable=False),
        sa.Column("safe_signal_code", sa.String(48), nullable=False),
        sa.Column("investigation_state", sa.String(16), nullable=False),
        sa.Column("actor_ref", sa.String(64), nullable=False),
        sa.Column("note_code", sa.String(32)),
        sa.Column("note_text", sa.String(280)),
        sa.Column("supersedes_event_id", sa.String(36)),
    )
    op.create_table(
        "ops_entitlement_expiries",
        sa.Column("subject_ref", sa.String(36), primary_key=True),
        sa.Column("closed_at", _TS, nullable=False),
        sa.Column("expired_at", _TS, nullable=False),
        sa.Column("event_count", sa.Integer, nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
    )
    op.create_table(
        "ops_restore_enforcements",
        sa.Column("restore_id", sa.String(36), primary_key=True),
        sa.Column("enforced_at", _TS, nullable=False),
        sa.Column("summary_json", sa.Text, nullable=False),
    )
    op.create_table(
        "ops_rights_evidence",
        sa.Column("rights_id", sa.String(36), primary_key=True),
        sa.Column("subject_ref", sa.String(36), nullable=False, index=True),
        sa.Column("right_kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("purchased_at", _TS, nullable=False),
        sa.Column("external_source", sa.String(64)),
        sa.Column("external_reference_id", sa.String(128)),
        sa.Column("source_event_id", sa.String(36), nullable=False),
        sa.Column("recorded_at", _TS, nullable=False),
        sa.Column("annual_review_at", _TS, nullable=False),
    )
    for table in APPEND_ONLY:
        op.execute(update_trigger(table))
        op.execute(guarded_delete_trigger(table))


def drop_operations_schema(op: Any) -> None:
    for table in APPEND_ONLY:
        op.execute(f"DROP TRIGGER IF EXISTS prevent_{table}_update")
        op.execute(f"DROP TRIGGER IF EXISTS prevent_{table}_delete")
    for table in (
        "ops_rights_evidence",
        "ops_restore_enforcements",
        "ops_entitlement_expiries",
        "ops_anomaly_events",
        "ops_receipt_credentials",
        "ops_export_artifacts",
        "ops_receipts",
        "ops_phase_events",
        "ops_request_inventory",
        "ops_data_request_events",
        "ops_data_requests",
        "ops_support_events",
        "lifecycle_disposal_grants",
    ):
        op.drop_table(table)
