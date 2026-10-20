"""Account view and BYOK settings seam — CRD Issue 20.

Composes the authoritative reads the account routes return, so the handlers
stay thin (Binding Decision 2):

- balances, hosted availability and Cloud Services from Issue 13's
  ``EntitlementService.get_access_path_status`` (read-only; creates no row);
- BYOK credential/configuration state from the credential layer's
  ``ByokSettingsService``;
- readiness and the would-be selection through the very probe and matrix a
  turn uses (``probe_byok_readiness`` + ``select_access_path``), so the view
  cannot disagree with turn selection.

Credential-settings failures are translated one-to-one into the typed error
envelope here; their messages are fixed service text, never key material.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.api.access_path import (
    AccessPathSelection,
    ByokReadinessProbe,
    probe_byok_readiness,
    select_access_path,
)
from afterworlds.api.dto import (
    AccountStatusResponse,
    AdminAccountViewResponse,
    ByokProvider,
    ByokProviderStateDTO,
    ByokReadinessSource,
    ByokStatusDTO,
    CloudServicesStatus,
    CredentialValidationRequest,
    CredentialWriteRequest,
    HostedCreditsDTO,
    OpenRouterModelRequest,
    ProviderEnabledRequest,
    ReplayCheckDTO,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.entitlement.enums import HostedUnavailableReason
from afterworlds.entitlement.inspection import (
    ReplayCheck,
    read_projection,
    replay_check,
)
from afterworlds.entitlement.models import AccessPathStatus
from afterworlds.entitlement.service import EntitlementService
from afterworlds.pipeline.provider import (
    ByokSettingsService,
    CredentialSettingsError,
    CredentialSettingsErrorKind,
)
from afterworlds.remote.access import owned_story_ids
from afterworlds.remote.identity import AccountRecord

_SETTINGS_ERRORS: dict[CredentialSettingsErrorKind, tuple[int, ApiErrorCode]] = {
    CredentialSettingsErrorKind.INVALID_INPUT: (422, ApiErrorCode.VALIDATION_FAILED),
    CredentialSettingsErrorKind.STORE_READ_ONLY: (
        409,
        ApiErrorCode.CREDENTIAL_STORE_READ_ONLY,
    ),
    CredentialSettingsErrorKind.STORE_UNAVAILABLE: (
        503,
        ApiErrorCode.CREDENTIAL_STORE_UNAVAILABLE,
    ),
    CredentialSettingsErrorKind.METADATA_UNAVAILABLE: (
        503,
        ApiErrorCode.CREDENTIAL_SETTINGS_UNAVAILABLE,
    ),
    CredentialSettingsErrorKind.NOT_CONFIGURED: (
        409,
        ApiErrorCode.CREDENTIAL_NOT_CONFIGURED,
    ),
    CredentialSettingsErrorKind.VALIDATION_SUPERSEDED: (
        409,
        ApiErrorCode.CREDENTIAL_VALIDATION_SUPERSEDED,
    ),
    CredentialSettingsErrorKind.VALIDATION_UNAVAILABLE: (
        503,
        ApiErrorCode.CREDENTIAL_VALIDATION_UNAVAILABLE,
    ),
}


def _utc(value: datetime | None) -> datetime | None:
    # SQLite returns the stored UTC timestamp naive; say so on the wire.
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _credits(value: Decimal | None) -> str | None:
    # Exact four-place decimal string; sign kept, never clamped or floated.
    return None if value is None else f"{value:.4f}"


def build_account_status(
    session: Session,
    sojourner_id: UUID,
    readiness_provider: ByokReadinessProbe,
    settings: ByokSettingsService | None,
) -> AccountStatusResponse:
    """``settings is None`` is the remote deployment (prerequisite #205 §3):
    no credential store exists there, so local BYOK readiness is reported as
    unavailable -- never probed, inferred or read from a device."""
    status = EntitlementService(session).get_access_path_status(sojourner_id)
    if settings is None:
        return _account_response(
            status,
            select_access_path(status, False),
            ByokStatusDTO(
                license_active=status.byok_turn_available,
                credential_store_writable=False,
                providers=[],
                openrouter_model=None,
                byok_ready=None,
                readiness_source=ByokReadinessSource.UNAVAILABLE_REMOTELY,
            ),
        )
    byok_ready = probe_byok_readiness(readiness_provider, sojourner_id)
    selection = select_access_path(status, byok_ready is True)
    byok = run_settings_operation(lambda: settings.read(sojourner_id))

    return _account_response(
        status,
        selection,
        ByokStatusDTO(
            license_active=status.byok_turn_available,
            credential_store_writable=byok.store_writable,
            providers=[
                ByokProviderStateDTO(
                    provider=ByokProvider(p.provider_name),
                    credential_present=p.credential_present,
                    enabled=p.enabled,
                    validation_status=p.validation_status,
                    last_validated_at=_utc(p.last_validated_at),
                )
                for p in byok.providers
            ],
            openrouter_model=byok.openrouter_model,
            byok_ready=byok_ready,
        ),
    )


def build_admin_account_view(
    session: Session, record: AccountRecord
) -> AdminAccountViewResponse:
    """Allowlisted operational view of one targeted hosted account (#205),
    with CRD Issue 22's owning-source lookup fields. Read-only: nothing is
    activated, repaired, probed or contacted."""
    status = EntitlementService(session).get_access_path_status(record.account_id)
    projection = read_projection(session, record.account_id)
    replay = replay_check(session, record.account_id)
    return AdminAccountViewResponse(
        account_id=record.account_id,
        status="closed" if record.status == "closed" else "active",
        created_at=record.created_at,
        closed_at=record.closed_at,
        owned_story_count=len(owned_story_ids(session, record.account_id)),
        credits=hosted_credits(status),
        cloud_services=cloud_services_status(status),
        byok_license_active=status.byok_turn_available,
        byok_readiness_source=ByokReadinessSource.UNAVAILABLE_REMOTELY,
        entitlement_state="absent" if projection is None else "present",
        hosted_access_active=bool(projection and projection.hosted_access_active),
        hosted_plan=(
            projection.hosted_access_plan.value
            if projection and projection.hosted_access_plan
            else None
        ),
        cloud_services_expires_at=_utc(
            projection.cloud_services_expires_at if projection else None
        ),
        byok_license_purchased_at=_utc(
            projection.byok_license_purchased_at if projection else None
        ),
        last_entitlement_event_id=(
            projection.last_entitlement_event_id if projection else None
        ),
        expected_conditions=expected_conditions(status),
        replay=replay_dto(replay),
    )


def expected_conditions(status: AccessPathStatus) -> list[str]:
    """Expected entitlement states support must not mistake for corruption."""
    found = []
    total = status.total_hosted_credit_balance
    if total is not None and total < 0:
        found.append("negative_balance")
    reason = status.hosted_unavailable_reason
    if reason is HostedUnavailableReason.CREDITS_EXHAUSTED:
        found.append("credits_exhausted")
    if reason is HostedUnavailableReason.SUBSCRIPTION_INACTIVE:
        found.append("hosted_inactive")
    if status.cloud_services_lapsed:
        found.append("cloud_services_lapsed")
    return found


def replay_dto(check: ReplayCheck) -> ReplayCheckDTO:
    return ReplayCheckDTO(
        status=check.status.value,
        detail_code=check.detail_code,
        through_sequence=check.through_sequence,
        mismatched_fields=list(check.mismatched_fields),
    )


def hosted_credits(status: AccessPathStatus) -> HostedCreditsDTO:
    return HostedCreditsDTO(
        included=_credits(status.hosted_credit_balance),
        top_up=_credits(status.top_up_credit_balance),
        total=_credits(status.total_hosted_credit_balance),
        hosted_turn_available=status.hosted_turn_available,
        hosted_unavailable_reason=status.hosted_unavailable_reason,
    )


def cloud_services_status(status: AccessPathStatus) -> CloudServicesStatus:
    if status.cloud_services_active:
        return CloudServicesStatus.ACTIVE
    if status.cloud_services_lapsed:
        return CloudServicesStatus.LAPSED
    return CloudServicesStatus.NOT_ACTIVATED


def _account_response(
    status: AccessPathStatus, selection: AccessPathSelection, byok: ByokStatusDTO
) -> AccountStatusResponse:
    return AccountStatusResponse(
        credits=hosted_credits(status),
        cloud_services=cloud_services_status(status),
        byok=byok,
        selected_access_path=selection.access_path,
        blocked_error_code=selection.blocked_error_code,
        refreshed_at=datetime.now(UTC),
    )


def run_settings_operation[T](operation: Callable[[], T]) -> T:
    """Run a ``ByokSettingsService`` call, translating its typed failures."""
    failure: CredentialSettingsError | None = None
    try:
        return operation()
    except CredentialSettingsError as exc:
        failure = exc
    # Raised after the handler, so the envelope chains nothing.
    assert failure is not None
    status_code, code = _SETTINGS_ERRORS[failure.kind]
    raise ApiErrorResponse(status_code, code, failure.message)


ACCOUNT_PATH_PREFIX = "/api/account"

#: Location parts a validation error on the account surface may name. Anything
#: else -- an unknown JSON property name, which a client could fill with a key
#: -- is reported generically, never echoed.
_KNOWN_LOCATION_PARTS = frozenset(
    {"body", "path", "query", "provider"}.union(
        *(
            model.model_fields
            for model in (
                CredentialWriteRequest,
                ProviderEnabledRequest,
                OpenRouterModelRequest,
                CredentialValidationRequest,
            )
        )
    )
)


def account_validation_location(loc: tuple[int | str, ...]) -> str:
    """Dotted error location for the account surface, with unrecognized
    components replaced so no client-chosen name is reflected."""
    return ".".join(
        (
            str(part)
            if isinstance(part, int) or part in _KNOWN_LOCATION_PARTS
            else "<unrecognized>"
        )
        for part in loc
    )
