"""ProviderResolver — per-turn provider binding — CRD Issue 14a/14b.

``resolve_for_turn`` is the single entry point for provider/platform selection.
No provider policy lives in HTTP handlers or entitlement code.

Hosted path:
  - Anthropic direct primary (WHITELISTED + capable via AFTERWORLDS_VERIFIED profile).
  - Optional OpenRouter fallback from hosted routing configuration; whitelist status
    and capability resolved via ``OpenRouterCapabilityRegistry`` when injected.
  - Wrapped in ``RefusalFallbackRouter`` when fallback exists.

BYOK path:
  - Pool = adapters whose credentials exist for this Sojourner in
    ``CredentialStore``.
  - Zero credentials → ``ProviderConfigError``.
  - One credential → that adapter, no fallback.
  - Two+ credentials → primary + first eligible fallback.
  - BYOK OpenRouter model id comes from
    ``ProviderRouteConfig.preferred_model_identifier``;
    absent → ``ProviderConfigError`` (fail closed).

Cross-boundary rule: hosted/BYOK pools never cross.
Dynamic alias rule: dynamic aliases are rejected at ``OpenRouterAdapter``
construction (``ProviderConfigError``) and additionally by the registry.

14b: ``OpenRouterCapabilityRegistry`` is optional.  When absent, OpenRouter routes
default to UNKNOWN and ``supports_required_capabilities=False``
(fail-safe; Safety always runs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._registry import (
    OpenRouterCapabilityRegistry,
    make_anthropic_capability_profile,
)
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)
from afterworlds.pipeline.provider.adapters._anthropic import (
    AnthropicCapabilityProfile,
    AnthropicDirectAdapter,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.provider.adapters._openrouter import OpenRouterAdapter
from afterworlds.pipeline.provider.credentials._store import CredentialStore

# ---------------------------------------------------------------------------
# Hosted routing configuration
# ---------------------------------------------------------------------------


@dataclass
class HostedRoutingConfig:
    """Configuration for the hosted Anthropic-direct path.

    ``anthropic_api_key``: Afterworlds-hosted Anthropic API key.
    ``openrouter_api_key``: Optional hosted OpenRouter fallback key.
    ``openrouter_fallback_model``: Model id for the hosted OpenRouter fallback;
        required when ``openrouter_api_key`` is set.
    """

    anthropic_api_key: str
    openrouter_api_key: str | None = None
    openrouter_fallback_model: str | None = None
    anthropic_profile: AnthropicCapabilityProfile = field(
        default_factory=AnthropicCapabilityProfile
    )


# ---------------------------------------------------------------------------
# Refusal logging
# ---------------------------------------------------------------------------


def _write_refusal_event(
    session_factory: object,
    *,
    outcome: str,
    request: object,
    primary_refusal: object,
    fallback_provider: str | None,
    fallback_model: str | None,
) -> None:
    """Write one ProviderRefusalEvent row using a fresh session.

    Called either directly (DIRECT mode) or by RefusalLogProxy.flush() after
    the outer narrative session has closed and its write lock released.
    """
    from datetime import UTC, datetime

    from sqlalchemy.orm import Session

    from afterworlds.pipeline._refusal import ProviderRefusalError
    from afterworlds.pipeline.provider._models import ProviderCallRequest
    from afterworlds.pipeline.provider._refusal_log import ProviderRefusalEvent

    if not isinstance(request, ProviderCallRequest):
        return
    if not isinstance(primary_refusal, ProviderRefusalError):
        return
    refusal = primary_refusal.refusal
    event = ProviderRefusalEvent(
        turn_id=str(request.turn_id) if request.turn_id is not None else None,
        sojourner_id=(
            str(request.sojourner_id) if request.sojourner_id is not None else None
        ),
        pass_id=request.pass_id.value,
        primary_provider_name=refusal.provider,
        primary_model_identifier=refusal.model or "",
        refusal_category=(
            refusal.refusal_category.value
            if refusal.refusal_category is not None
            else "unknown"
        ),
        fallback_outcome=outcome,
        fallback_provider_name=fallback_provider,
        fallback_model_identifier=fallback_model,
        created_at=datetime.now(UTC),
    )
    _factory = session_factory
    assert callable(_factory)
    session_obj = _factory()
    assert isinstance(session_obj, Session)
    with session_obj as session:
        session.add(event)
        session.commit()


class RefusalLogProxy:
    """Per-turn refusal-event callback with defer-and-flush support.

    Starts in DIRECT mode: ``__call__`` writes immediately via a fresh
    session.  The orchestrator calls ``start_buffering()`` before opening
    the outer narrative transaction so that any refusal during post-Writer
    passes (Output Safety, Extractor, Contradiction) is queued in memory
    instead of opening a competing SQLite write session.  ``flush()`` is
    called after the outer session closes — the write lock is released before
    any new write is attempted, so lock contention is structurally impossible.

    Audit rows survive narrative rollback: the outer transaction is rolled
    back for story-state failures; the refusal IS the event that caused the
    rollback, so the audit record must outlive it.  Rows are committed in a
    separate session after the boundary.

    ``raw_response_excerpt``, prompt text, system block content, and key
    material are never passed to this callback; see ``RefusalFallbackRouter``
    and the security invariants in CLAUDE.md.
    """

    def __init__(self, session_factory: object) -> None:
        self._session_factory = session_factory
        self._buffer: list[dict[str, object]] | None = None

    def start_buffering(self) -> None:
        """Switch to buffered mode; called before session.begin()."""
        self._buffer = []

    def flush(self) -> None:
        """Write buffered rows and return to direct mode.

        Called by the orchestrator after session.close() so no write lock
        is held when the fresh session opens.
        """
        pending, self._buffer = self._buffer or [], None
        for kwargs in pending:
            _write_refusal_event(self._session_factory, **kwargs)  # type: ignore[arg-type]

    def __call__(
        self,
        *,
        outcome: str,
        request: object,
        primary_refusal: object,
        fallback_provider: str | None,
        fallback_model: str | None,
    ) -> None:
        if self._buffer is not None:
            self._buffer.append(
                {
                    "outcome": outcome,
                    "request": request,
                    "primary_refusal": primary_refusal,
                    "fallback_provider": fallback_provider,
                    "fallback_model": fallback_model,
                }
            )
        else:
            _write_refusal_event(
                self._session_factory,
                outcome=outcome,
                request=request,
                primary_refusal=primary_refusal,
                fallback_provider=fallback_provider,
                fallback_model=fallback_model,
            )


def _build_refusal_log_fn(session_factory: object) -> RefusalLogProxy:
    """Build a per-turn refusal-event logging proxy for ``RefusalFallbackRouter``."""
    return RefusalLogProxy(session_factory)


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


# ---------------------------------------------------------------------------
# ProviderResolver
# ---------------------------------------------------------------------------


class ProviderResolver:
    """Long-lived provider resolver injected into ``OrchestratorService``.

    ``resolve_for_turn`` is called once at the start of each turn and returns
    a ``TurnProviderBinding`` valid for that turn only.

    Args:
        credential_store: Sojourner-scoped BYOK credential store.
        hosted_config: Configuration for the hosted Anthropic-direct path.
            Required when serving hosted-access Sojourners.
        session_factory: Factory returning SQLAlchemy sessions for reading
            ``ProviderRouteConfig`` rows.  Optional; required for BYOK path.
        capability_registry: OpenRouter model-route capability registry (14b).
            When None, OpenRouter routes resolve to UNKNOWN + not capable;
            Safety always runs for those routes.
    """

    def __init__(
        self,
        credential_store: CredentialStore,
        hosted_config: HostedRoutingConfig | None = None,
        session_factory: object = None,
        capability_registry: OpenRouterCapabilityRegistry | None = None,
    ) -> None:
        self._credential_store = credential_store
        self._hosted_config = hosted_config
        self._session_factory = session_factory
        self._capability_registry = capability_registry

    def resolve_for_turn(
        self,
        access_path: RuntimeAccessPath,
        sojourner_id: UUID,
    ) -> TurnProviderBinding:
        """Resolve a ``TurnProviderBinding`` for the given turn.

        Raises:
            ProviderConfigError: if no valid provider configuration exists.
        """
        if access_path is RuntimeAccessPath.HOSTED:
            return self._resolve_hosted(sojourner_id)
        return self._resolve_byok(sojourner_id)

    # -----------------------------------------------------------------------
    # Private: hosted
    # -----------------------------------------------------------------------

    def _resolve_hosted(self, sojourner_id: UUID) -> TurnProviderBinding:
        if self._hosted_config is None:
            raise ProviderConfigError(
                "ProviderResolver: hosted_config is required for HOSTED access path"
            )
        if self._session_factory is None:
            raise ProviderConfigError(
                "ProviderResolver: session_factory is required for refusal logging"
            )
        proxy = _build_refusal_log_fn(self._session_factory)
        cfg = self._hosted_config

        primary_adapter = AnthropicDirectAdapter(
            api_key=cfg.anthropic_api_key,
            profile=cfg.anthropic_profile,
        )
        # Derive model string for Writer route from the capability profile
        from afterworlds.entitlement.enums import PipelinePassId

        writer_model = cfg.anthropic_profile.model_for(PipelinePassId.WRITER)
        primary_route = EligibleModelRoute(
            provider_name="anthropic",
            model_identifier=writer_model,
            whitelist_status=SafetyWhitelistStatus.WHITELISTED,
            supports_required_capabilities=True,
            capability_profile=make_anthropic_capability_profile(writer_model),
        )

        if cfg.openrouter_api_key:
            if (
                not cfg.openrouter_fallback_model
                or not cfg.openrouter_fallback_model.strip()
            ):
                raise ProviderConfigError(
                    "HostedRoutingConfig: openrouter_api_key is set but "
                    "openrouter_fallback_model is missing or blank — fail closed"
                )
            fallback_adapter = OpenRouterAdapter(
                model_identifier=cfg.openrouter_fallback_model,
                api_key=cfg.openrouter_api_key,
            )
            fallback_route = self._resolve_openrouter_route(
                cfg.openrouter_fallback_model
            )
            wrapped_adapter = RefusalFallbackRouter(
                primary=primary_adapter,
                fallback=fallback_adapter,
                refusal_log_fn=proxy,
            )
            return TurnProviderBinding(
                adapter=wrapped_adapter,
                primary_writer_route=primary_route,
                eligible_writer_routes=(primary_route, fallback_route),
                access_path=RuntimeAccessPath.HOSTED,
                pre_transaction_fn=proxy.start_buffering,
                post_transaction_fn=proxy.flush,
            )

        return TurnProviderBinding(
            adapter=RefusalFallbackRouter(
                primary=primary_adapter,
                fallback=None,
                refusal_log_fn=proxy,
            ),
            primary_writer_route=primary_route,
            eligible_writer_routes=(primary_route,),
            access_path=RuntimeAccessPath.HOSTED,
            pre_transaction_fn=proxy.start_buffering,
            post_transaction_fn=proxy.flush,
        )

    # -----------------------------------------------------------------------
    # Private: BYOK
    # -----------------------------------------------------------------------

    def _resolve_byok(self, sojourner_id: UUID) -> TurnProviderBinding:
        from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM

        if self._session_factory is None:
            raise ProviderConfigError(
                "ProviderResolver: session_factory is required for refusal logging"
            )
        proxy = _build_refusal_log_fn(self._session_factory)

        # Build available pool: requires both active credential metadata row
        # AND retrievable key.  Keys for inactive providers are not fetched.
        available_keys: dict[str, str] = {}
        for _pname in ("anthropic", "openrouter"):
            if _is_credential_eligible(self._session_factory, sojourner_id, _pname):
                _key = self._credential_store.get(sojourner_id, _pname)
                if _key:
                    available_keys[_pname] = _key

        anthropic_key: str | None = available_keys.get("anthropic")
        openrouter_key: str | None = available_keys.get("openrouter")
        available: list[str] = list(available_keys)

        if not available:
            raise ProviderConfigError(
                f"BYOK: no configured credentials for Sojourner {sojourner_id}"
            )

        def _make_anthropic(
            api_key: str,
        ) -> tuple[AnthropicDirectAdapter, EligibleModelRoute]:
            from afterworlds.entitlement.enums import PipelinePassId

            profile = AnthropicCapabilityProfile()
            adapter = AnthropicDirectAdapter(api_key=api_key, profile=profile)
            writer_model = profile.model_for(PipelinePassId.WRITER)
            route = EligibleModelRoute(
                provider_name="anthropic",
                model_identifier=writer_model,
                whitelist_status=SafetyWhitelistStatus.WHITELISTED,
                supports_required_capabilities=True,
                capability_profile=make_anthropic_capability_profile(writer_model),
            )
            return adapter, route

        def _make_openrouter(
            api_key: str, model_id: str
        ) -> tuple[OpenRouterAdapter, EligibleModelRoute]:
            adapter = OpenRouterAdapter(model_identifier=model_id, api_key=api_key)
            route = self._resolve_openrouter_route(model_id)
            return adapter, route

        def _get_openrouter_model(sojourner_id: UUID) -> str:
            if self._session_factory is None:
                raise ProviderConfigError(
                    "BYOK OpenRouter: session_factory required to read"
                    " ProviderRouteConfig"
                )
            from sqlalchemy import select
            from sqlalchemy.orm import Session

            _factory = self._session_factory
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
                raise ProviderConfigError(
                    f"BYOK OpenRouter: no preferred_model_identifier configured "
                    f"for Sojourner {sojourner_id} — fail closed"
                )
            model = (row.preferred_model_identifier or "").strip()
            if not model:
                raise ProviderConfigError(
                    f"BYOK OpenRouter: no preferred_model_identifier configured "
                    f"for Sojourner {sojourner_id} — fail closed"
                )
            return model

        if len(available) == 1:
            provider = available[0]
            if provider == "anthropic":
                assert anthropic_key is not None
                adapter, route = _make_anthropic(anthropic_key)
                return TurnProviderBinding(
                    adapter=RefusalFallbackRouter(
                        primary=adapter, fallback=None, refusal_log_fn=proxy
                    ),
                    primary_writer_route=route,
                    eligible_writer_routes=(route,),
                    access_path=RuntimeAccessPath.BYOK,
                    pre_transaction_fn=proxy.start_buffering,
                    post_transaction_fn=proxy.flush,
                )
            # openrouter only
            assert openrouter_key is not None
            model_id = _get_openrouter_model(sojourner_id)
            or_adapter, or_route = _make_openrouter(openrouter_key, model_id)
            return TurnProviderBinding(
                adapter=RefusalFallbackRouter(
                    primary=or_adapter, fallback=None, refusal_log_fn=proxy
                ),
                primary_writer_route=or_route,
                eligible_writer_routes=(or_route,),
                access_path=RuntimeAccessPath.BYOK,
                pre_transaction_fn=proxy.start_buffering,
                post_transaction_fn=proxy.flush,
            )

        # Two providers available: use Anthropic as primary, OpenRouter as fallback
        assert anthropic_key is not None
        assert openrouter_key is not None
        primary_adapter, primary_route = _make_anthropic(anthropic_key)
        or_model_id = _get_openrouter_model(sojourner_id)
        fallback_adapter, fallback_route = _make_openrouter(openrouter_key, or_model_id)
        wrapped = RefusalFallbackRouter(
            primary=primary_adapter,
            fallback=fallback_adapter,
            refusal_log_fn=proxy,
        )
        return TurnProviderBinding(
            adapter=wrapped,
            primary_writer_route=primary_route,
            eligible_writer_routes=(primary_route, fallback_route),
            access_path=RuntimeAccessPath.BYOK,
            pre_transaction_fn=proxy.start_buffering,
            post_transaction_fn=proxy.flush,
        )

    # -----------------------------------------------------------------------
    # Private: OpenRouter route resolution (14b)
    # -----------------------------------------------------------------------

    def _resolve_openrouter_route(self, model_identifier: str) -> EligibleModelRoute:
        """Resolve capability and whitelist status for an OpenRouter model route.

        If no ``capability_registry`` was injected, falls back to fail-safe
        defaults: UNKNOWN status, not capable, no profile.  This preserves the
        14a behaviour (Safety always runs for OpenRouter) when the registry is
        not yet configured.

        Raises:
            ProviderConfigError: if the registry rejects the model (dynamic alias
                or positively incapable of serving the Writer pass).
        """
        if self._capability_registry is None:
            return EligibleModelRoute(
                provider_name="openrouter",
                model_identifier=model_identifier,
                whitelist_status=SafetyWhitelistStatus.UNKNOWN,
                supports_required_capabilities=False,
                capability_profile=None,
            )
        whitelist_status, profile, supports_required = (
            self._capability_registry.resolve_route(model_identifier)
        )
        return EligibleModelRoute(
            provider_name="openrouter",
            model_identifier=model_identifier,
            whitelist_status=whitelist_status,
            supports_required_capabilities=supports_required,
            capability_profile=profile,
        )


__all__ = [
    "HostedRoutingConfig",
    "ProviderResolver",
    "RefusalLogProxy",
]
