"""Entitlement-owner retention expiry -- CRD Issue 13 under the accepted
CRD Issue 22 lifecycle amendment (ADR-013).

A closed account's minimized ledger is kept, replay-valid and unchanged,
while the account is active and for 24 calendar months after its recorded
closure; then the owner expires the whole subject -- projection and every
event together -- through the guarded lifecycle path, so no partial ledger
that would replay wrongly is ever left. Story deletion never calls this. The
minimum perpetual BYOK-rights evidence is recorded first and survives.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.operations.lifecycle import dispose_rows
from afterworlds.operations.orm import RightsEvidenceORM
from afterworlds.operations.policy import ANNUAL_REVIEW
from afterworlds.remote.control_store import iso


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


def record_rights_evidence_from_ledger(
    content: sessionmaker[Session],
    ops: sessionmaker[Session],
    subject_ref: str,
    *,
    now: datetime,
) -> tuple[str, dict[str, int]]:
    """Copy the minimum perpetual BYOK-rights evidence (right ID, opaque
    subject link, kind/status, purchase time, source/reference, verification
    metadata) from the subject's licence event; idempotent. Called before an
    erasure closes the account and before any closed-ledger expiry, so the
    right survives the cloud profile and the ledger."""
    with content() as s:
        event = s.scalars(
            sa.select(EntitlementEvent)
            .where(
                EntitlementEvent.sojourner_id == UUID(subject_ref),
                EntitlementEvent.event_type
                == EntitlementEventType.BYOK_LICENSE_ACTIVATED.value,
            )
            .order_by(EntitlementEvent.global_sequence)
        ).first()
        if event is None:
            return "not_applicable", {}
        payload = json.loads(event.payload_json)
        source_event = str(event.event_id)
    with ops.begin() as s:
        exists = s.scalar(
            sa.select(RightsEvidenceORM.rights_id).where(
                RightsEvidenceORM.source_event_id == source_event
            )
        )
        if exists is None:
            s.add(
                RightsEvidenceORM(
                    rights_id=str(uuid4()),
                    subject_ref=subject_ref,
                    right_kind="byok_perpetual_license",
                    status="active",
                    purchased_at=str(payload.get("purchased_at")),
                    external_source=payload.get("external_source"),
                    external_reference_id=payload.get("external_reference_id"),
                    source_event_id=source_event,
                    recorded_at=iso(now),
                    annual_review_at=iso(now + ANNUAL_REVIEW),
                )
            )
    return "succeeded", {"rights": 1}
