"""CRD Issue 22 operations records and the guarded lifecycle exception.

Creates the operations store tables (used by a local deployment; a remote
content store's copies stay empty -- its operational records live in the
control store) and ``lifecycle_disposal_grants``. Replaces the unconditional
DELETE triggers on ``entitlement_event``, ``provider_refusal_log``,
``rpg_roll_audit`` and ``action_resolution_events`` with guarded ones: an
ordinary DELETE is still refused with the same message; only a row granted by
the reviewed lifecycle path (``afterworlds.operations.lifecycle``) in the same
transaction may be removed (accepted CRD Issue 22 lifecycle amendment). UPDATE
triggers are unchanged.
"""

from __future__ import annotations

from alembic import op

from afterworlds.operations.schema import (
    create_operations_schema,
    drop_operations_schema,
    guarded_delete_trigger,
    plain_delete_trigger,
)

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: str | None = None
depends_on: str | None = None

#: (table, existing DELETE trigger name)
GUARDED = (
    ("entitlement_event", "prevent_entitlement_event_delete"),
    ("provider_refusal_log", "prevent_provider_refusal_log_delete"),
    ("rpg_roll_audit", "prevent_rpg_roll_audit_delete"),
    ("action_resolution_events", "prevent_action_resolution_events_delete"),
)


def upgrade() -> None:
    create_operations_schema(op)
    for table, trigger in GUARDED:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        op.execute(guarded_delete_trigger(table, trigger))


def downgrade() -> None:
    for table, trigger in GUARDED:
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        op.execute(plain_delete_trigger(table, trigger))
    drop_operations_schema(op)
