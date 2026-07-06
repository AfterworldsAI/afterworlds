"""Tests for `ByokCredentialReadinessProvider` — CRD Issue 14a follow-up (#122).

Formalizes the BYOK readiness seam ahead of Issue 19 DoR-E: `is_byok_runnable`
must agree with `ProviderResolver._resolve_byok` (success vs. `ProviderConfigError`)
for every case below, since both read through the same shared predicate in
`_readiness.py`.

Covers:
  - no credential metadata → not runnable
  - inactive/invalid/error credential metadata → not runnable
  - eligible metadata but unretrievable/empty key material → not runnable
  - eligible metadata + retrievable key + required route config → runnable
  - missing required OpenRouter route config → not runnable
  - agreement between `_resolve_byok` and `is_byok_runnable` for all of the above
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.provider._errors import ProviderConfigError
from afterworlds.pipeline.provider._readiness import ByokCredentialReadinessProvider
from afterworlds.pipeline.provider._resolver import ProviderResolver
from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM
from afterworlds.pipeline.provider.credentials._metadata import (
    ProviderCredentialMetadata,
    ValidationStatus,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _add_metadata(
    sf: object,
    sid: UUID,
    provider: str,
    *,
    is_active: bool = True,
    validation_status: str = ValidationStatus.UNTESTED,
) -> None:
    assert callable(sf)
    sess = sf()
    sess.add(
        ProviderCredentialMetadata(
            sojourner_id=str(sid),
            provider_name=provider,
            is_active=is_active,
            validation_status=validation_status,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    sess.commit()
    sess.close()


def _add_route_config(
    sf: object, sid: UUID, *, preferred_model_identifier: str | None
) -> None:
    assert callable(sf)
    sess = sf()
    sess.add(
        ProviderRouteConfigORM(
            sojourner_id=str(sid),
            provider_name="openrouter",
            preferred_model_identifier=preferred_model_identifier,
            is_active=True,
        )
    )
    sess.commit()
    sess.close()


def _store(keys: dict[str, str | None]) -> MagicMock:
    store = MagicMock()
    store.get.side_effect = lambda _sid, provider: keys.get(provider)
    return store


def _agreement(store: MagicMock, sf: object, sid: UUID) -> tuple[bool, bool]:
    """Return (is_byok_runnable(...), resolve_for_turn succeeded)."""
    readiness = ByokCredentialReadinessProvider(
        credential_store=store, session_factory=sf
    )
    runnable = readiness.is_byok_runnable(sid)
    resolver = ProviderResolver(
        credential_store=store, hosted_config=None, session_factory=sf
    )
    try:
        resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
        resolvable = True
    except ProviderConfigError:
        resolvable = False
    return runnable, resolvable


# ---------------------------------------------------------------------------
# No credential metadata at all
# ---------------------------------------------------------------------------


def test_no_metadata_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    store = _store({"anthropic": "sk-ant-test", "openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


# ---------------------------------------------------------------------------
# Inactive / invalid / error metadata
# ---------------------------------------------------------------------------


def test_inactive_metadata_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", is_active=False)
    store = _store({"anthropic": "sk-ant-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_invalid_status_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.INVALID)
    store = _store({"anthropic": "sk-ant-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_error_status_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic", validation_status=ValidationStatus.ERROR)
    store = _store({"anthropic": "sk-ant-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


# ---------------------------------------------------------------------------
# Eligible metadata but unretrievable / empty key material
# ---------------------------------------------------------------------------


def test_eligible_metadata_unretrievable_key_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    """Metadata is eligible (active, UNTESTED) but the keychain has no key."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    store = _store({"anthropic": None})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_eligible_metadata_empty_key_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    """Metadata is eligible but the retrieved key is an empty string."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    store = _store({"anthropic": ""})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


# ---------------------------------------------------------------------------
# Eligible metadata + retrievable key (+ route config where required) → runnable
# ---------------------------------------------------------------------------


def test_anthropic_only_eligible_and_retrievable_is_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    """Anthropic needs no route config — eligible metadata + key is enough."""
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    store = _store({"anthropic": "sk-ant-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is True
    assert resolvable is True


def test_openrouter_eligible_key_and_route_config_is_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    _add_route_config(sf, sid, preferred_model_identifier="anthropic/claude-haiku-4-5")
    store = _store({"openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is True
    assert resolvable is True


# ---------------------------------------------------------------------------
# Missing required BYOK route config (OpenRouter only, no/blank model id)
# ---------------------------------------------------------------------------


def test_openrouter_missing_route_config_row_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    store = _store({"openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_openrouter_blank_route_config_model_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    _add_route_config(sf, sid, preferred_model_identifier="   ")
    store = _store({"openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_openrouter_dynamic_alias_route_config_not_runnable(engine) -> None:  # type: ignore[no-untyped-def]
    """`preferred_model_identifier` set to a dynamic alias (e.g. "openrouter/auto")
    is rejected at `OpenRouterAdapter` construction — the readiness predicate
    must agree, not just check that a model id is present.
    """
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "openrouter")
    _add_route_config(sf, sid, preferred_model_identifier="openrouter/auto")
    store = _store({"openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


def test_both_providers_but_openrouter_route_config_missing_not_runnable(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    """Anthropic alone would be runnable, but `_resolve_byok` always needs the
    OpenRouter model id once OpenRouter is in the available pool (primary +
    fallback) — the readiness predicate mirrors that exactly, not a "best
    available provider" relaxation.
    """
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    _add_metadata(sf, sid, "openrouter")
    store = _store({"anthropic": "sk-ant-test", "openrouter": "sk-or-test"})
    runnable, resolvable = _agreement(store, sf, sid)
    assert runnable is False
    assert resolvable is False


# ---------------------------------------------------------------------------
# Readiness method exposes no key material
# ---------------------------------------------------------------------------


def test_readiness_result_is_a_plain_bool_not_leaking_key_material(
    engine,  # type: ignore[no-untyped-def]
) -> None:
    sf = create_session_factory(engine)
    sid = uuid4()
    _add_metadata(sf, sid, "anthropic")
    store = _store({"anthropic": "sk-ant-super-secret"})
    readiness = ByokCredentialReadinessProvider(
        credential_store=store, session_factory=sf
    )
    result = readiness.is_byok_runnable(sid)
    assert result is True
    assert "sk-ant" not in repr(result)
