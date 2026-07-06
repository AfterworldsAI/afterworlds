"""BYOK readiness seam — CRD Issue 14a follow-up (#122), pre-Issue-19 DoR-E.

Issue 19 Rev3 DoR-E requires access-path selection to compute *runnable* paths,
not merely *licensed* paths. BYOK runnable = Issue 13's ``byok_turn_available``
AND this module reports usable BYOK credentials/route configuration for the
Sojourner. This module is the single source of truth for the latter half of
that predicate.

``_compute_byok_runnable`` is the one implementation of BYOK runnability. Both
``ProviderResolver._resolve_byok`` (which raises ``ProviderConfigError`` on
failure) and ``ByokCredentialReadinessProvider.is_byok_runnable`` (which
returns ``False`` on failure) call through the same helpers in this module —
there is no second copy of the eligibility/retrievability/route-config logic.

This is a seam formalization, not a new access-path policy: it exposes a
read-only check, it does not change entitlement, provider routing, or
fallback behavior.
"""

from __future__ import annotations

from uuid import UUID

from afterworlds.pipeline.provider.credentials._store import CredentialStore

_BYOK_PROVIDER_NAMES: tuple[str, ...] = ("anthropic", "openrouter")


def _is_credential_eligible(
    session_factory: object, sojourner_id: UUID, provider_name: str
) -> bool:
    """Return True iff the credential row exists, is active, and is not INVALID/ERROR.

    VALID and UNTESTED are eligible (permissive default for unchecked keys).
    INVALID and ERROR are excluded to prevent routing to known-bad credentials.
    Absent row or is_active=False both return False.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from afterworlds.pipeline.provider.credentials._metadata import (
        ProviderCredentialMetadata,
        ValidationStatus,
    )

    _factory = session_factory
    assert callable(_factory)
    session_obj = _factory()
    assert isinstance(session_obj, Session)
    with session_obj as session:
        stmt = select(ProviderCredentialMetadata).where(
            ProviderCredentialMetadata.sojourner_id == str(sojourner_id),
            ProviderCredentialMetadata.provider_name == provider_name,
            ProviderCredentialMetadata.is_active.is_(True),
        )
        row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return False
    return row.validation_status not in (
        ValidationStatus.INVALID,
        ValidationStatus.ERROR,
    )


def _fetch_openrouter_preferred_model(
    session_factory: object, sojourner_id: UUID
) -> str | None:
    """Return the active, non-blank OpenRouter ``preferred_model_identifier``.

    Returns None (never raises) if no active route-config row exists or the
    identifier is missing/blank — the caller decides whether that is a hard
    failure (``_resolve_byok``) or a readiness ``False`` (readiness provider).
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM

    _factory = session_factory
    assert callable(_factory)
    session_obj = _factory()
    assert isinstance(session_obj, Session)
    with session_obj as session:
        stmt = select(ProviderRouteConfigORM).where(
            ProviderRouteConfigORM.sojourner_id == str(sojourner_id),
            ProviderRouteConfigORM.provider_name == "openrouter",
            ProviderRouteConfigORM.is_active.is_(True),
        )
        row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    model = (row.preferred_model_identifier or "").strip()
    return model or None


def _collect_available_byok_keys(
    credential_store: CredentialStore,
    session_factory: object,
    sojourner_id: UUID,
) -> dict[str, str]:
    """Return ``{provider_name: key}`` for providers with eligible metadata AND a
    retrievable, non-empty key. Keys for ineligible providers are never fetched.
    """
    available: dict[str, str] = {}
    for provider_name in _BYOK_PROVIDER_NAMES:
        if _is_credential_eligible(session_factory, sojourner_id, provider_name):
            key = credential_store.get(sojourner_id, provider_name)
            if key:
                available[provider_name] = key
    return available


def _compute_byok_runnable(
    credential_store: CredentialStore,
    session_factory: object,
    sojourner_id: UUID,
) -> bool:
    """The single BYOK runnability predicate shared by resolver and readiness provider.

    Runnable iff at least one provider has eligible metadata plus a retrievable
    key, and — whenever OpenRouter is among the available providers, since
    ``_resolve_byok`` always needs its model id (as sole provider or as
    fallback) — a usable, non-dynamic-alias route-config model id exists for
    it. ``_is_dynamic_alias`` is imported from ``adapters/_openrouter.py``
    rather than re-implemented: that is the same check
    ``OpenRouterAdapter.__init__`` enforces, so a Sojourner whose
    ``preferred_model_identifier`` is a dynamic alias (rejected at adapter
    construction) is correctly reported as not runnable.

    Does not evaluate 14b ``OpenRouterCapabilityRegistry`` admission (whitelist/
    capability). That registry is not wired into any production
    ``ProviderResolver`` construction as of this seam; if/when it is, capability
    rejection remains a resolve-time concern documented as a residual gap in
    ADR-014a Decision 13, not one this predicate covers.
    """
    available = _collect_available_byok_keys(
        credential_store, session_factory, sojourner_id
    )
    if not available:
        return False
    if "openrouter" not in available:
        return True
    model = _fetch_openrouter_preferred_model(session_factory, sojourner_id)
    if model is None:
        return False
    from afterworlds.pipeline.provider.adapters._openrouter import _is_dynamic_alias

    return not _is_dynamic_alias(model)


class ByokCredentialReadinessProvider:
    """Public, read-only BYOK runnability check owned by the provider-routing package.

    Exposes exactly the predicate ``ProviderResolver._resolve_byok`` enforces
    for credential eligibility, key retrievability, and (for OpenRouter)
    route-config presence/validity — without raw key material, provider
    secrets, or route internals. Issue 19 DoR-E uses this to compute a
    runnable BYOK path instead of inspecting ``_resolver.py`` privates or
    duplicating ``ProviderResolver`` policy.

    Residual gap (see ADR-014a Decision 13): this does not evaluate a 14b
    ``OpenRouterCapabilityRegistry``, which is not wired into production
    ``ProviderResolver`` construction today. If that changes, a registry-admitted
    model could still be reported runnable here yet be rejected at resolve time.
    """

    def __init__(
        self, credential_store: CredentialStore, session_factory: object
    ) -> None:
        self._credential_store = credential_store
        self._session_factory = session_factory

    def is_byok_runnable(self, sojourner_id: UUID) -> bool:
        """Return True iff BYOK has usable credentials and route config for
        this Sojourner.

        Never raises on missing/ineligible credentials or config — returns
        False instead.
        """
        if self._session_factory is None:
            return False
        return _compute_byok_runnable(
            self._credential_store, self._session_factory, sojourner_id
        )


__all__ = ["ByokCredentialReadinessProvider"]
