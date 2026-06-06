"""Optimistic-concurrency regression tests — CRD Issue 13.

Four tests covering the P1 concurrency fix on ``receive_entitlement_event``:

1. Both concurrent top-up grants apply, both are in the event log, the
   projection reflects both, and replay matches the projection.
2. A stale conditional UPDATE (rowcount==0) is detected, retried, and never
   silently committed.
3. Retries exhausted → ``EntitlementConcurrencyError`` is raised, not a silent
   divergence.
4. First-row INSERT race: a competing session commits first; our service's INSERT
   gets IntegrityError on the PK, rolls back, retries via the UPDATE path, and
   succeeds.  Both events end up in the append-only log; replay matches the
   live projection.

How the concurrency guard works (for PR #95 Codex P1 response):
``receive_entitlement_event`` captures ``last_entitlement_event_id`` from the
current state row at the top of each attempt.  The conditional UPDATE is guarded
by ``WHERE sojourner_id == sojourner_id AND last_entitlement_event_id == <token>``.
If a concurrent writer committed between the read and this UPDATE, the version
token no longer matches → rowcount==0 → rollback → retry from a fresh DB read.
Stale-projection silent overwrite is structurally impossible: the UPDATE will not
commit unless the version token matches the live row.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update as _SqlUpdate

from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.errors import EntitlementConcurrencyError
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.payloads import (
    HostedAccessActivatedPayload,
    TopUpCreditGrantPayload,
)
from afterworlds.entitlement.replay import rebuild_entitlement_state
from afterworlds.entitlement.service import _MAX_CONCURRENCY_RETRIES, EntitlementService
from afterworlds.persistence.database import create_session_factory
from tests.entitlement.conftest import (
    activate_hosted,
    grant_subscription_credits,
    grant_top_up_credits,
)

# ---------------------------------------------------------------------------
# Test 1: Both concurrent top-up grants reach the DB; replay matches.
# ---------------------------------------------------------------------------


def test_concurrent_top_up_grants_both_applied(
    service: EntitlementService,
    sojourner_id: UUID,
    session: object,
) -> None:
    """Simulate two concurrent top-up grants; both events in log; replay matches.

    Grant A (25 credits) is committed first (the "earlier concurrent write").
    Grant B (50 credits) then attempts to commit, but the first UPDATE is
    intercepted and forced to return rowcount=0, simulating the stale-projection
    race.  The service retries, reads the state that now includes Grant A, and
    commits Grant B on top.  Both events must be present in the log and the
    projection must equal 75.  Replay must match.
    """
    from sqlalchemy.orm import Session

    assert isinstance(session, Session)

    # Setup: activate hosted and give subscription credits.
    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, amount="100")

    # Commit Grant A (the "first concurrent session's" write).
    grant_top_up_credits(service, sojourner_id, amount="25")

    session.expire_all()

    original_execute = session.execute
    first_update_intercepted = [False]

    def _intercept(stmt, *args, **kwargs):  # type: ignore[no-untyped-def]
        if not first_update_intercepted[0] and isinstance(stmt, _SqlUpdate):
            first_update_intercepted[0] = True
            # Simulate: Grant B read the same pre-A state, so its first UPDATE
            # is stale (Grant A has since committed, advancing the version token).
            fake = MagicMock()
            fake.rowcount = 0
            return fake
        return original_execute(stmt, *args, **kwargs)

    with patch.object(session, "execute", side_effect=_intercept):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.TOP_UP_CREDIT_GRANT,
            TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50")),
        )

    session.expire_all()

    # Both TOP_UP_CREDIT_GRANT events are in the append-only event log.
    top_up_events = session.scalars(  # type: ignore[union-attr]
        select(EntitlementEvent).where(
            EntitlementEvent.sojourner_id == sojourner_id,
            EntitlementEvent.event_type == EntitlementEventType.TOP_UP_CREDIT_GRANT,
        )
    ).all()
    assert (
        len(top_up_events) == 2
    ), f"Expected 2 TOP_UP_CREDIT_GRANT events; found {len(top_up_events)}"

    # Projection includes both grants (25 + 50 = 75).
    state = session.get(RuntimeEntitlementState, sojourner_id)  # type: ignore[union-attr]
    assert state is not None
    assert state.top_up_credit_balance == Decimal("75")

    # Replay of the ordered event log must match the live projection.
    all_events = session.scalars(  # type: ignore[union-attr]
        select(EntitlementEvent)
        .where(EntitlementEvent.sojourner_id == sojourner_id)
        .order_by(EntitlementEvent.global_sequence)
    ).all()
    snapshot = rebuild_entitlement_state(sojourner_id, all_events)
    assert snapshot.top_up_credit_balance == state.top_up_credit_balance


# ---------------------------------------------------------------------------
# Test 2: rowcount==0 is detected, retried, not silently committed.
# ---------------------------------------------------------------------------


def test_stale_projection_detected_and_retried(
    service: EntitlementService,
    sojourner_id: UUID,
    session: object,
) -> None:
    """rowcount==0 on conditional UPDATE triggers retry; stale write is not committed.

    The mock forces rowcount=0 on the first conditional UPDATE to prove:
    - the service detects the stale result (does not silently commit),
    - it issues at least one retry (UPDATE call count >= 2),
    - the final projection is correct (not the silently-overwritten stale value).
    """
    from sqlalchemy.orm import Session

    assert isinstance(session, Session)

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, amount="100")
    session.expire_all()

    original_execute = session.execute
    update_call_count = [0]

    def _intercept(stmt, *args, **kwargs):  # type: ignore[no-untyped-def]
        if isinstance(stmt, _SqlUpdate):
            update_call_count[0] += 1
            if update_call_count[0] == 1:
                # Force stale detection on the first attempt.
                fake = MagicMock()
                fake.rowcount = 0
                return fake
        return original_execute(stmt, *args, **kwargs)

    with patch.object(session, "execute", side_effect=_intercept):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.TOP_UP_CREDIT_GRANT,
            TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50")),
        )

    # The service must have retried: ≥2 conditional UPDATE calls.
    assert update_call_count[0] >= 2, (
        f"Expected ≥2 UPDATE attempts (stale detected → retry); "
        f"got {update_call_count[0]}"
    )

    # The stale write was never silently committed; the projection is correct.
    session.expire_all()
    state = session.get(RuntimeEntitlementState, sojourner_id)  # type: ignore[union-attr]
    assert state is not None
    assert state.top_up_credit_balance == Decimal("50")


# ---------------------------------------------------------------------------
# Test 3: Retries exhausted → EntitlementConcurrencyError.
# ---------------------------------------------------------------------------


def test_concurrency_error_raised_when_retries_exhausted(
    service: EntitlementService,
    sojourner_id: UUID,
    session: object,
) -> None:
    """EntitlementConcurrencyError is raised when all retry attempts see stale state."""
    from sqlalchemy.orm import Session

    assert isinstance(session, Session)

    activate_hosted(service, sojourner_id)
    grant_subscription_credits(service, sojourner_id, amount="100")
    session.expire_all()

    original_execute = session.execute

    def _always_stale_passthrough(stmt, *args, **kwargs):  # type: ignore[no-untyped-def]
        if isinstance(stmt, _SqlUpdate):
            fake = MagicMock()
            fake.rowcount = 0
            return fake
        return original_execute(stmt, *args, **kwargs)

    with (
        pytest.raises(EntitlementConcurrencyError) as exc_info,
        patch.object(session, "execute", side_effect=_always_stale_passthrough),
    ):
        service.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.TOP_UP_CREDIT_GRANT,
            TopUpCreditGrantPayload(top_up_credit_delta=Decimal("50")),
        )

    assert str(sojourner_id) in str(exc_info.value)
    assert "top_up_credit_grant" in str(exc_info.value).lower()
    # Verify retry count: the error message names _MAX_CONCURRENCY_RETRIES.
    assert str(_MAX_CONCURRENCY_RETRIES) in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 4: First-row creation race — IntegrityError → retry → UPDATE path.
# ---------------------------------------------------------------------------


def test_first_row_creation_race_retries_and_succeeds(
    session: object,
    engine: object,
    sojourner_id: UUID,
) -> None:
    """First-row INSERT race: competing session wins; service retries via UPDATE path.

    Simulates two services racing to create the very first entitlement event for a new
    Sojourner.  The "competing" service (separate session, same in-memory DB) wins the
    race and commits HOSTED_ACCESS_ACTIVATED + state row first.  Our service's first-row
    INSERT then collides on the PK, catches IntegrityError, rolls back, retries, and
    finds the competing row — taking the UPDATE path successfully.

    No threads.  Deterministic interleaving:
    - A competing session pre-commits the state row before our service call.
    - session.get is patched to return None on the first call, mimicking a stale
      in-memory snapshot that pre-dates the competing commit.
    - The subsequent INSERT collision produces IntegrityError; the retry succeeds via
      the existing-row UPDATE path.

    Assertions:
    - Both events (competing + retry) appear in the append-only log.
    - Live projection: hosted_access_active=True, correct plan.
    - Replay of ordered event log matches the live projection field-for-field.
    """
    assert isinstance(session, Session)
    assert isinstance(engine, sa.Engine)

    _FIXED = datetime(2026, 6, 5, 12, 0, 0)
    fixed_clock = lambda: _FIXED  # noqa: E731

    # Competing session: wins the race, commits HOSTED_ACCESS_ACTIVATED + state row.
    competing_sess = create_session_factory(engine)()
    competing_svc = EntitlementService(session=competing_sess, clock=fixed_clock)
    activate_hosted(competing_svc, sojourner_id)
    competing_sess.close()

    # Our service — same session as the fixture, shares the same in-memory DB.
    svc = EntitlementService(session=session, clock=fixed_clock)

    # Patch session.get to return None on the FIRST call only (simulates our
    # in-memory snapshot pre-dating the competing commit, causing the first-row
    # INSERT path rather than the UPDATE path).
    first_get_done = [False]
    original_get = session.get  # type: ignore[union-attr]

    def _stale_get_once(entity, ident, **kwargs):  # type: ignore[no-untyped-def]
        if entity is RuntimeEntitlementState and not first_get_done[0]:
            first_get_done[0] = True
            return None
        return original_get(entity, ident, **kwargs)

    with patch.object(session, "get", side_effect=_stale_get_once):
        svc.receive_entitlement_event(
            sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION,
                effective_at=_FIXED,
            ),
        )

    session.expire_all()  # type: ignore[union-attr]

    # Both the competing event and our retry's event are in the append-only log.
    all_events = session.scalars(  # type: ignore[union-attr]
        select(EntitlementEvent)
        .where(EntitlementEvent.sojourner_id == sojourner_id)
        .order_by(EntitlementEvent.global_sequence)
    ).all()
    assert (
        len(all_events) == 2
    ), f"Expected 2 events (competing + retry); found {len(all_events)}"

    # Live projection reflects both events applied in sequence.
    state = session.get(RuntimeEntitlementState, sojourner_id)  # type: ignore[union-attr]
    assert state is not None
    assert state.hosted_access_active is True
    assert state.hosted_access_plan == HostedAccessPlan.SUBSCRIPTION

    # Replay of the ordered event log must match the live projection field-for-field.
    snapshot = rebuild_entitlement_state(sojourner_id, all_events)
    assert snapshot.hosted_access_active == state.hosted_access_active
    assert snapshot.hosted_access_plan == state.hosted_access_plan
