"""CRD Issue 22 operations records in the control store.

Support actions, data requests and their transitions, inventories, phase
progress, receipts, export artifacts, receipt credentials, anomalies, the
entitlement-expiry register and BYOK-rights evidence live here in a remote
deployment, outside the content snapshot (ADR-021 D5). The identity audit
stream's DELETE trigger becomes the guarded lifecycle trigger (24-month
expiry of minimized administrator receipts); UPDATE stays refused.
"""

from __future__ import annotations

from alembic import op

from afterworlds.operations.schema import (
    create_operations_schema,
    drop_operations_schema,
    guarded_delete_trigger,
    plain_delete_trigger,
)

revision: str = "c0002"
down_revision: str | None = "c0001"
branch_labels: str | None = None
depends_on: str | None = None

_AUDIT = "identity_audit_events"
_TRIGGER = "prevent_identity_audit_event_delete"


def upgrade() -> None:
    create_operations_schema(op)
    op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER}")
    op.execute(guarded_delete_trigger(_AUDIT, _TRIGGER))


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER}")
    op.execute(plain_delete_trigger(_AUDIT, _TRIGGER))
    drop_operations_schema(op)
