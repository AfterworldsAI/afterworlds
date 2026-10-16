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

from afterworlds.api.access_path import probe_byok_readiness, select_access_path
from afterworlds.api.dto import (
    AccountStatusResponse,
    ByokProvider,
    ByokProviderStateDTO,
    ByokStatusDTO,
    CloudServicesStatus,
    CredentialValidationRequest,
    CredentialWriteRequest,
    HostedCreditsDTO,
    OpenRouterModelRequest,
    ProviderEnabledRequest,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.entitlement.service import EntitlementService
from afterworlds.pipeline.provider import (
    ByokCredentialReadinessProvider,
    ByokSettingsService,
    CredentialSettingsError,
    CredentialSettingsErrorKind,
)

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
    readiness_provider: ByokCredentialReadinessProvider,
    settings: ByokSettingsService,
) -> AccountStatusResponse:
    status = EntitlementService(session).get_access_path_status(sojourner_id)
    byok_ready = probe_byok_readiness(readiness_provider, sojourner_id)
    selection = select_access_path(status, byok_ready is True)
    byok = run_settings_operation(lambda: settings.read(sojourner_id))

    if status.cloud_services_active:
        cloud = CloudServicesStatus.ACTIVE
    elif status.cloud_services_lapsed:
        cloud = CloudServicesStatus.LAPSED
    else:
        cloud = CloudServicesStatus.NOT_ACTIVATED

    return AccountStatusResponse(
        credits=HostedCreditsDTO(
            included=_credits(status.hosted_credit_balance),
            top_up=_credits(status.top_up_credit_balance),
            total=_credits(status.total_hosted_credit_balance),
            hosted_turn_available=status.hosted_turn_available,
            hosted_unavailable_reason=status.hosted_unavailable_reason,
        ),
        cloud_services=cloud,
        byok=ByokStatusDTO(
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
