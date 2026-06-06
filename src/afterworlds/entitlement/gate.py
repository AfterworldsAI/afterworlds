"""Cloud Services gate — CRD Issue 13.

``CloudServicesGate`` is event-state driven.  It checks ``cloud_services_active``
and ``cloud_services_expires_at`` from ``RuntimeEntitlementState`` — and nothing
else.  It must never inspect ``hosted_access_active``, ``hosted_access_plan``, or
any other field to infer Cloud Services entitlement.

If a hosted subscription plan bundles Cloud Services, Issue 23 (payment webhooks)
or Issue 19/20 (policy wiring) is responsible for translating that bundle into an
explicit ``CLOUD_SERVICES_ACTIVATED`` event.  Issue 13 does not implement bundling
inference.

Read / export / download are not in ``CloudServiceOperation`` and must never be
passed here.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import CloudServiceOperation
from afterworlds.entitlement.errors import CloudServicesLapsedError
from afterworlds.entitlement.orm import RuntimeEntitlementState
from afterworlds.entitlement.time_utils import to_utc_naive


class CloudServicesGate:
    """Guards cloud service operations behind entitlement state checks.

    v1: stub for live callers; raises correctly in tests and when wired.
    """

    def __init__(
        self,
        session: Session,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._clock: Callable[[], datetime] = (
            clock if clock is not None else datetime.utcnow
        )

    def require_cloud_services(
        self,
        sojourner_id: UUID,
        operation: CloudServiceOperation,
    ) -> None:
        """Raise ``CloudServicesLapsedError`` if Cloud Services are not active.

        Checks ``cloud_services_active`` and ``cloud_services_expires_at`` only
        (Owner Decision #5).  Never infers Cloud Services entitlement from
        ``hosted_access_active`` or ``hosted_access_plan``.

        Read / export / download must never be passed here — they are not in
        ``CloudServiceOperation``.
        """
        state = self._session.get(RuntimeEntitlementState, sojourner_id)
        now = self._clock()

        if not self._cloud_services_effective(state, now):
            raise CloudServicesLapsedError(
                f"Cloud Services not active for sojourner_id={sojourner_id} "
                f"operation={operation!r}"
            )

    @staticmethod
    def _cloud_services_effective(
        state: RuntimeEntitlementState | None,
        now: datetime,
    ) -> bool:
        """True iff Owner Decision #5 conditions are all met."""
        if state is None:
            return False
        if not state.cloud_services_active:
            return False
        if state.cloud_services_expires_at is None:
            return False
        return to_utc_naive(state.cloud_services_expires_at) > to_utc_naive(now)
