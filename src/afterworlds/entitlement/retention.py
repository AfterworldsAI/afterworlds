"""Entitlement-owner retention expiry -- CRD Issue 13 under the accepted
CRD Issue 22 lifecycle amendment (ADR-013).

A closed account's minimized ledger is kept, replay-valid and unchanged,
while the account is active and for 24 calendar months after its recorded
closure; then the owner expires the whole subject -- projection and every
event together -- through the guarded lifecycle path, so no partial ledger
that would replay wrongly is ever left. Story deletion never calls this. The
minimum perpetual BYOK-rights evidence is recorded separately before closure
and survives.
"""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.entitlement.orm import RuntimeEntitlementState
from afterworlds.operations.lifecycle import dispose_rows


def expire_subject_history(session: Session, sojourner_id: UUID) -> int:
    """Remove the subject's projection and all its events in the caller's
    transaction; returns the number of events removed."""
    session.execute(
        sa.delete(RuntimeEntitlementState).where(
            RuntimeEntitlementState.sojourner_id == sojourner_id
        )
    )
    subject = sa.bindparam(
        "subject", sojourner_id, type_=sa.Uuid(as_uuid=True, native_uuid=False)
    )
    return dispose_rows(
        session, "entitlement_event", sa.column("sojourner_id") == subject
    )
