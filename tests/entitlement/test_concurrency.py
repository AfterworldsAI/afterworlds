"""Optimistic-concurrency regression tests — CRD Issue 13.

Three tests covering the P1 concurrency fix on ``receive_entitlement_event``:

1. Both concurrent top-up grants apply, both are in the event log, the
   projection reflects both, and replay matches the projection.
2. A stale conditional UPDATE (rowcount==0) is detected, retried, and never
   silently committed.
3. Retries exhausted → ``EntitlementConcurrencyError`` is raised, not a silent
   divergence.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.sql.dml import Update as _SqlUpdate

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.errors import EntitlementConcurrencyError
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.payloads import TopUpCreditGrantPayload
from afterworlds.entitlement.replay import rebuild_entitlement_state
from afterworlds.entitlement.service import _MAX_CONCURRENCY_RETRIES, EntitlementService
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
