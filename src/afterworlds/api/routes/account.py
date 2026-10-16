"""/api/account -- billing, Cloud Services and BYOK settings (CRD Issue 20).

Thin handlers: every read/write goes through ``api/account.py`` to the
owning services. Each successful operation returns the refreshed
authoritative account view; a failure returns the typed error envelope and
confirms nothing. Only ``.../validate`` contacts a provider.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.account import build_account_status, run_settings_operation
from afterworlds.api.deps import (
    get_byok_readiness_provider,
    get_byok_settings,
    get_session,
    get_sojourner_id,
)
from afterworlds.api.dto import (
    AccountStatusResponse,
    ByokProvider,
    CredentialValidationRequest,
    CredentialWriteRequest,
    OpenRouterModelRequest,
    ProviderEnabledRequest,
)
from afterworlds.api.errors import ApiError
from afterworlds.pipeline.provider import (
    ByokCredentialReadinessProvider,
    ByokSettingsService,
)

router = APIRouter(prefix="/api/account", tags=["account"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (409, 422, 503)
}


@router.get("", response_model=AccountStatusResponse, responses=_RESPONSES)
def get_account(
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    return build_account_status(session, sojourner_id, readiness, settings)


@router.put(
    "/byok/{provider}/credential",
    response_model=AccountStatusResponse,
    responses=_RESPONSES,
)
def put_credential(
    provider: ByokProvider,
    body: CredentialWriteRequest,
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    run_settings_operation(
        lambda: settings.set_credential(
            sojourner_id, provider.value, body.api_key.get_secret_value()
        )
    )
    return build_account_status(session, sojourner_id, readiness, settings)


@router.delete(
    "/byok/{provider}/credential",
    response_model=AccountStatusResponse,
    responses=_RESPONSES,
)
def delete_credential(
    provider: ByokProvider,
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    run_settings_operation(
        lambda: settings.remove_credential(sojourner_id, provider.value)
    )
    return build_account_status(session, sojourner_id, readiness, settings)


@router.put(
    "/byok/{provider}/enabled",
    response_model=AccountStatusResponse,
    responses=_RESPONSES,
)
def put_enabled(
    provider: ByokProvider,
    body: ProviderEnabledRequest,
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    run_settings_operation(
        lambda: settings.set_enabled(sojourner_id, provider.value, body.enabled)
    )
    return build_account_status(session, sojourner_id, readiness, settings)


@router.put(
    "/byok/openrouter/model",
    response_model=AccountStatusResponse,
    responses=_RESPONSES,
)
def put_openrouter_model(
    body: OpenRouterModelRequest,
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    run_settings_operation(
        lambda: settings.set_openrouter_model(sojourner_id, body.model_identifier)
    )
    return build_account_status(session, sojourner_id, readiness, settings)


@router.post(
    "/byok/{provider}/validate",
    response_model=AccountStatusResponse,
    responses=_RESPONSES,
)
def validate_credential(
    provider: ByokProvider,
    body: CredentialValidationRequest,
    sojourner_id: UUID = Depends(get_sojourner_id),
    session: Session = Depends(get_session),
    readiness: ByokCredentialReadinessProvider = Depends(get_byok_readiness_provider),
    settings: ByokSettingsService = Depends(get_byok_settings),
) -> AccountStatusResponse:
    # body.acknowledge_provider_contact is Literal[True]: validation already
    # rejected a request without the explicit acknowledgement.
    run_settings_operation(lambda: settings.validate(sojourner_id, provider.value))
    return build_account_status(session, sojourner_id, readiness, settings)
