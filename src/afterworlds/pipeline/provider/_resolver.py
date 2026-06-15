"""ProviderResolver — per-turn provider binding — CRD Issue 14a.

``resolve_for_turn`` is the single entry point for provider/platform selection.
No provider policy lives in HTTP handlers or entitlement code.

Hosted path:
  - Anthropic direct primary (``trusted_for_safety_skip=True``).
  - Optional OpenRouter fallback from hosted routing configuration
    (``trusted_for_safety_skip=False``).
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
construction (``ProviderConfigError``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._routing import (
    EligibleWriterRoute,
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


def _build_refusal_log_fn(session_factory: object) -> Callable[..., None]:
    """Build a refusal-event logging callback for ``RefusalFallbackRouter``."""

    def _log_fn(
        *,
        outcome: str,
        request: object,
        primary_refusal: object,
        fallback_provider: str | None,
        fallback_model: str | None,
    ) -> None:
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

    return _log_fn


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
    """

    def __init__(
        self,
        credential_store: CredentialStore,
        hosted_config: HostedRoutingConfig | None = None,
        session_factory: object = None,
    ) -> None:
        self._credential_store = credential_store
        self._hosted_config = hosted_config
        self._session_factory = session_factory

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
        log_fn = _build_refusal_log_fn(self._session_factory)
        cfg = self._hosted_config

        primary_adapter = AnthropicDirectAdapter(
            api_key=cfg.anthropic_api_key,
            profile=cfg.anthropic_profile,
        )
        # Derive model string for Writer route from the capability profile
        from afterworlds.entitlement.enums import PipelinePassId

        writer_model = cfg.anthropic_profile.model_for(PipelinePassId.WRITER)
        primary_route = EligibleWriterRoute(
            provider_name="anthropic",
            model_identifier=writer_model,
            is_openrouter=False,
            trusted_for_safety_skip=True,
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
            fallback_route = EligibleWriterRoute(
                provider_name="openrouter",
                model_identifier=cfg.openrouter_fallback_model,
                is_openrouter=True,
                trusted_for_safety_skip=False,
            )
            wrapped_adapter = RefusalFallbackRouter(
                primary=primary_adapter,
                fallback=fallback_adapter,
                refusal_log_fn=log_fn,
            )
            return TurnProviderBinding(
                adapter=wrapped_adapter,
                primary_writer_route=primary_route,
                eligible_writer_routes=(primary_route, fallback_route),
                access_path=RuntimeAccessPath.HOSTED,
            )

        return TurnProviderBinding(
            adapter=RefusalFallbackRouter(
                primary=primary_adapter,
                fallback=None,
                refusal_log_fn=log_fn,
            ),
            primary_writer_route=primary_route,
            eligible_writer_routes=(primary_route,),
            access_path=RuntimeAccessPath.HOSTED,
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
        log_fn = _build_refusal_log_fn(self._session_factory)

        # Find which providers have credentials for this Sojourner
        anthropic_key = self._credential_store.get(sojourner_id, "anthropic")
        openrouter_key = self._credential_store.get(sojourner_id, "openrouter")

        available: list[str] = []
        if anthropic_key:
            available.append("anthropic")
        if openrouter_key:
            available.append("openrouter")

        if not available:
            raise ProviderConfigError(
                f"BYOK: no configured credentials for Sojourner {sojourner_id}"
            )

        def _make_anthropic(
            api_key: str,
        ) -> tuple[AnthropicDirectAdapter, EligibleWriterRoute]:
            from afterworlds.entitlement.enums import PipelinePassId

            profile = AnthropicCapabilityProfile()
            adapter = AnthropicDirectAdapter(api_key=api_key, profile=profile)
            writer_model = profile.model_for(PipelinePassId.WRITER)
            route = EligibleWriterRoute(
                provider_name="anthropic",
                model_identifier=writer_model,
                is_openrouter=False,
                trusted_for_safety_skip=True,
            )
            return adapter, route

        def _make_openrouter(
            api_key: str, model_id: str
        ) -> tuple[OpenRouterAdapter, EligibleWriterRoute]:
            adapter = OpenRouterAdapter(model_identifier=model_id, api_key=api_key)
            route = EligibleWriterRoute(
                provider_name="openrouter",
                model_identifier=model_id,
                is_openrouter=True,
                trusted_for_safety_skip=False,
            )
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
            if row is None or not row.preferred_model_identifier:
                raise ProviderConfigError(
                    f"BYOK OpenRouter: no preferred_model_identifier configured "
                    f"for Sojourner {sojourner_id} — fail closed"
                )
            return row.preferred_model_identifier

        if len(available) == 1:
            provider = available[0]
            if provider == "anthropic":
                assert anthropic_key is not None
                adapter, route = _make_anthropic(anthropic_key)
                return TurnProviderBinding(
                    adapter=RefusalFallbackRouter(
                        primary=adapter, fallback=None, refusal_log_fn=log_fn
                    ),
                    primary_writer_route=route,
                    eligible_writer_routes=(route,),
                    access_path=RuntimeAccessPath.BYOK,
                )
            # openrouter only
            assert openrouter_key is not None
            model_id = _get_openrouter_model(sojourner_id)
            or_adapter, or_route = _make_openrouter(openrouter_key, model_id)
            return TurnProviderBinding(
                adapter=RefusalFallbackRouter(
                    primary=or_adapter, fallback=None, refusal_log_fn=log_fn
                ),
                primary_writer_route=or_route,
                eligible_writer_routes=(or_route,),
                access_path=RuntimeAccessPath.BYOK,
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
            refusal_log_fn=log_fn,
        )
        return TurnProviderBinding(
            adapter=wrapped,
            primary_writer_route=primary_route,
            eligible_writer_routes=(primary_route, fallback_route),
            access_path=RuntimeAccessPath.BYOK,
        )


__all__ = [
    "HostedRoutingConfig",
    "ProviderResolver",
]
