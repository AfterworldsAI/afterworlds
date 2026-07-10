"""DoR-E: the single tested access-path selection helper.

Access-path selection is server-derived per turn inside this one helper
(single choke point) -- route handlers never branch on access path directly
and the client never supplies ``access_path``.

The helper computes RUNNABLE paths, not merely licensed ones:
  - hosted runnable = ``AccessPathStatus.hosted_turn_available``
  - BYOK runnable = ``AccessPathStatus.byok_turn_available`` AND the Issue
    14a credential-readiness seam (``ByokCredentialReadinessProvider.
    is_byok_runnable``) reports usable BYOK credentials/route configuration

Selection: neither runnable -> typed block (``ENTITLEMENT_BLOCKED`` if no
entitlement path exists at all; ``BYOK_CREDENTIALS_REQUIRED`` if BYOK is
licensed but not credential-ready and hosted is not runnable either) ->
exactly one runnable -> that path -> both runnable -> BYOK over hosted (v1).
No user preference state (Issue 20 territory).
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.api.errors import ApiErrorCode
from afterworlds.entitlement.enums import HostedUnavailableReason, RuntimeAccessPath
from afterworlds.entitlement.models import AccessPathStatus


@dataclass(frozen=True)
class AccessPathSelection:
    """Result of the DoR-E selection matrix.

    ``access_path`` is None iff selection is blocked, in which case
    ``blocked_error_code`` names the typed error the caller must surface
    before any pipeline work runs.
    """

    access_path: RuntimeAccessPath | None
    blocked_error_code: ApiErrorCode | None
    hosted_unavailable_reason: HostedUnavailableReason | None


def select_access_path(
    status: AccessPathStatus, byok_credential_ready: bool
) -> AccessPathSelection:
    """Apply the DoR-E runnable-path matrix. Pure function -- no I/O."""
    byok_runnable = status.byok_turn_available and byok_credential_ready
    hosted_runnable = status.hosted_turn_available

    if hosted_runnable or byok_runnable:
        chosen = RuntimeAccessPath.BYOK if byok_runnable else RuntimeAccessPath.HOSTED
        return AccessPathSelection(chosen, None, None)

    if status.byok_turn_available and not byok_credential_ready:
        return AccessPathSelection(
            None,
            ApiErrorCode.BYOK_CREDENTIALS_REQUIRED,
            status.hosted_unavailable_reason,
        )
    return AccessPathSelection(
        None, ApiErrorCode.ENTITLEMENT_BLOCKED, status.hosted_unavailable_reason
    )
