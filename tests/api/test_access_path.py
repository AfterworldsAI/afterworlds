"""DoR-E: the full runnable-path selection matrix, in one tested helper."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from afterworlds.api.access_path import select_access_path
from afterworlds.api.errors import ApiErrorCode
from afterworlds.entitlement.enums import HostedUnavailableReason, RuntimeAccessPath
from afterworlds.entitlement.models import AccessPathStatus


def _status(
    *,
    hosted: bool,
    byok_licensed: bool,
    hosted_unavailable_reason: HostedUnavailableReason | None = None,
) -> AccessPathStatus:
    return AccessPathStatus(
        sojourner_id=uuid4(),
        hosted_turn_available=hosted,
        byok_turn_available=byok_licensed,
        cloud_services_active=False,
        hosted_credit_balance=Decimal("0"),
        top_up_credit_balance=Decimal("0"),
        total_hosted_credit_balance=Decimal("0"),
        hosted_unavailable_reason=hosted_unavailable_reason,
        cloud_services_lapsed=False,
    )


@pytest.mark.parametrize(
    ("hosted", "byok_licensed", "byok_ready", "expected_path", "expected_error"),
    [
        (False, True, True, RuntimeAccessPath.BYOK, None),
        (False, True, False, None, ApiErrorCode.BYOK_CREDENTIALS_REQUIRED),
        (True, True, False, RuntimeAccessPath.HOSTED, None),
        (True, True, True, RuntimeAccessPath.BYOK, None),
        (True, False, False, RuntimeAccessPath.HOSTED, None),
        (False, False, False, None, ApiErrorCode.ENTITLEMENT_BLOCKED),
    ],
)
def test_dor_e_runnable_path_matrix(
    hosted: bool,
    byok_licensed: bool,
    byok_ready: bool,
    expected_path: RuntimeAccessPath | None,
    expected_error: ApiErrorCode | None,
) -> None:
    status = _status(hosted=hosted, byok_licensed=byok_licensed)
    selection = select_access_path(status, byok_ready)
    assert selection.access_path == expected_path
    assert selection.blocked_error_code == expected_error


def test_blocked_selection_carries_hosted_unavailable_reason() -> None:
    status = _status(
        hosted=False,
        byok_licensed=False,
        hosted_unavailable_reason=HostedUnavailableReason.CREDITS_EXHAUSTED,
    )
    selection = select_access_path(status, byok_credential_ready=False)
    assert selection.access_path is None
    assert selection.blocked_error_code == ApiErrorCode.ENTITLEMENT_BLOCKED
    assert (
        selection.hosted_unavailable_reason == HostedUnavailableReason.CREDITS_EXHAUSTED
    )
