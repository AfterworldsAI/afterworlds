"""The reviewed lifecycle exception to append-only history (CRD Issue 22).

Accepted lifecycle amendment, common clause: ordinary operation keeps every
append-only, immutable and replay rule; only a verified, confirmed terminal
deletion or an approved record's retention expiry may remove inventoried
in-scope rows, through the owning service, never by disabling a trigger.

:func:`dispose_rows` is the only writer of ``lifecycle_disposal_grants``
(``tests/operations/test_lifecycle.py`` guards that): inside the caller's
transaction it grants exactly the selected rows, deletes them and removes the
grants again, so no permission outlives the transaction and an ordinary
DELETE on a guarded table is still refused by its trigger. UPDATE triggers
are never touched.
"""

from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

#: Tables whose DELETE trigger honours a lifecycle grant (content chain 0046,
#: control chain c0002) -- plus the operations streams themselves.
GUARDED_TABLES = frozenset(
    {
        "entitlement_event",
        "provider_refusal_log",
        "rpg_roll_audit",
        "action_resolution_events",
        "identity_audit_events",
        "ops_support_events",
        "ops_data_request_events",
        "ops_phase_events",
        "ops_anomaly_events",
        "ops_receipts",
    }
)


def dispose_rows(
    session: Session, table: str, where: sa.ColumnElement[bool] | None
) -> int:
    """Delete the rows of *table* matching *where* (``None``: none) in the
    caller's transaction, granting a guarded table's trigger exactly those
    rows. Returns the number removed. The caller commits."""
    if where is None:
        return 0
    target = sa.table(table, sa.column("rowid"))
    rowids = [
        int(r)
        for r in session.scalars(
            sa.select(sa.column("rowid")).select_from(sa.table(table)).where(where)
        )
    ]
    if not rowids:
        return 0
    operation = str(uuid4())
    guarded = table in GUARDED_TABLES
    grants = sa.table(
        "lifecycle_disposal_grants",
        sa.column("table_name"),
        sa.column("row_key"),
        sa.column("operation_ref"),
    )
    for chunk_start in range(0, len(rowids), 500):
        chunk = rowids[chunk_start : chunk_start + 500]
        if guarded:
            session.execute(
                sa.insert(grants),
                [
                    {"table_name": table, "row_key": rowid, "operation_ref": operation}
                    for rowid in chunk
                ],
            )
        session.execute(sa.delete(target).where(sa.column("rowid").in_(chunk)))
    if guarded:
        session.execute(sa.delete(grants).where(grants.c.operation_ref == operation))
    return len(rowids)
