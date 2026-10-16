"""ByokSettingsService — CRD Issue 20.

Runs the production ``OSKeychainCredentialStore`` over a disposable in-memory
keyring backend, so the real credential-owner path is exercised without the
platform credential manager. Readiness/resolver agreement is checked through
the actual ``ByokCredentialReadinessProvider`` and ``ProviderResolver``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any
from uuid import UUID, uuid4

import keyring
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline.provider import (
    ByokCredentialReadinessProvider,
    ByokSettingsService,
    CredentialSettingsError,
    CredentialSettingsErrorKind,
    ProviderConfigError,
    ProviderResolver,
)
from afterworlds.pipeline.provider.credentials import (
    FallbackEnvCredentialStore,
    OSKeychainCredentialStore,
    ProviderCredentialMetadata,
    ValidationStatus,
)
from scripts.e2e_memory_keyring import MemoryKeyring
from scripts.e2e_memory_keyring import install as install_memory_keyring

SECRET = "sk-ant-SYNTHETIC-SECRET-0123456789abcdef"  # pragma: allowlist secret
SECRET_2 = "sk-ant-SYNTHETIC-REPLACEMENT-fedcba9876543210"  # pragma: allowlist secret
OR_SECRET = "sk-or-SYNTHETIC-SECRET-0123456789abcdef"  # pragma: allowlist secret


@pytest.fixture()
def backend() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    yield install_memory_keyring()
    keyring.set_keyring(previous)


@pytest.fixture()
def sf(engine):  # type: ignore[no-untyped-def]
    return create_session_factory(engine)


class Checker:
    """Records provider contacts; ``during`` runs inside the check."""

    def __init__(self, status: ValidationStatus = ValidationStatus.VALID) -> None:
        self.status = status
        self.calls: list[tuple[str, str]] = []
        self.during: Callable[[], None] | None = None

    def __call__(self, provider: str, key: str) -> tuple[ValidationStatus, None]:
        self.calls.append((provider, key))
        if self.during is not None:
            self.during()
        return self.status, None


def _service(sf: Any, checker: Checker | None = None) -> ByokSettingsService:
    return ByokSettingsService(OSKeychainCredentialStore(), sf, checker or Checker())


def _row(sf: Any, sid: UUID, provider: str) -> ProviderCredentialMetadata | None:
    with sf() as s:
        return s.scalars(  # type: ignore[no-any-return]
            select(ProviderCredentialMetadata).where(
                ProviderCredentialMetadata.sojourner_id == str(sid),
                ProviderCredentialMetadata.provider_name == provider,
            )
        ).one_or_none()


def _state(svc: ByokSettingsService, sid: UUID, provider: str) -> Any:
    return next(p for p in svc.read(sid).providers if p.provider_name == provider)


def _agreement(sf: Any, sid: UUID) -> tuple[bool, bool]:
    store = OSKeychainCredentialStore()
    runnable = ByokCredentialReadinessProvider(store, sf).is_byok_runnable(sid)
    try:
        ProviderResolver(store, session_factory=sf).resolve_for_turn(
            RuntimeAccessPath.BYOK, sid
        )
        resolved = True
    except ProviderConfigError:
        resolved = False
    return runnable, resolved


def test_add_stores_key_only_in_store_and_starts_untested(
    sf: Any, backend: MemoryKeyring, engine: Any
) -> None:
    sid = uuid4()
    checker = Checker()
    svc = _service(sf, checker)
    assert _state(svc, sid, "anthropic").credential_present is False

    svc.set_credential(sid, "anthropic", SECRET)

    state = _state(svc, sid, "anthropic")
    assert state.credential_present is True
    assert state.enabled is True
    assert state.validation_status is ValidationStatus.UNTESTED
    assert backend.secrets == {("afterworlds_byok.anthropic", str(sid)): SECRET}
    # SQLite holds non-secret metadata only.
    with engine.connect() as conn:
        for table in ("provider_credential_metadata", "provider_route_config"):
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                assert SECRET not in repr(tuple(row))
    # Reading and saving never contact the provider.
    assert checker.calls == []
    assert _agreement(sf, sid) == (True, True)


def test_replacement_starts_untested_and_never_inherits_validation(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    assert svc.validate(sid, "anthropic") is ValidationStatus.VALID
    first_revision = _row(sf, sid, "anthropic").credential_revision  # type: ignore[union-attr]

    svc.set_credential(sid, "anthropic", SECRET_2)

    row = _row(sf, sid, "anthropic")
    assert row is not None
    assert row.validation_status == ValidationStatus.UNTESTED
    assert row.last_validated_at is None
    assert row.credential_revision != first_revision
    assert backend.secrets[("afterworlds_byok.anthropic", str(sid))] == SECRET_2


def test_validation_is_explicit_and_records_verdict(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    checker = Checker(ValidationStatus.INVALID)
    svc = _service(sf, checker)
    svc.set_credential(sid, "anthropic", SECRET)
    svc.set_enabled(sid, "anthropic", True)
    svc.read(sid)
    assert checker.calls == []

    assert svc.validate(sid, "anthropic") is ValidationStatus.INVALID

    assert checker.calls == [("anthropic", SECRET)]
    state = _state(svc, sid, "anthropic")
    assert state.validation_status is ValidationStatus.INVALID
    assert state.last_validated_at is not None
    # INVALID is excluded by the shared predicate; UNTESTED was eligible.
    assert _agreement(sf, sid) == (False, False)


def test_late_validation_cannot_bless_a_replacement(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    checker = Checker(ValidationStatus.VALID)
    svc = _service(sf, checker)
    svc.set_credential(sid, "anthropic", SECRET)
    checker.during = lambda: svc.set_credential(sid, "anthropic", SECRET_2)

    with pytest.raises(CredentialSettingsError) as err:
        svc.validate(sid, "anthropic")

    assert err.value.kind is CredentialSettingsErrorKind.VALIDATION_SUPERSEDED
    assert checker.calls == [("anthropic", SECRET)]
    assert _state(svc, sid, "anthropic").validation_status is ValidationStatus.UNTESTED


def test_late_validation_cannot_revive_a_removed_key(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    checker = Checker()
    svc = _service(sf, checker)
    svc.set_credential(sid, "anthropic", SECRET)
    checker.during = lambda: svc.remove_credential(sid, "anthropic")

    with pytest.raises(CredentialSettingsError) as err:
        svc.validate(sid, "anthropic")

    assert err.value.kind is CredentialSettingsErrorKind.VALIDATION_SUPERSEDED
    assert _row(sf, sid, "anthropic") is None
    assert backend.secrets == {}
    assert _agreement(sf, sid) == (False, False)


def test_late_validation_after_remove_and_re_add_is_discarded(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    checker = Checker(ValidationStatus.VALID)
    svc = _service(sf, checker)
    svc.set_credential(sid, "anthropic", SECRET)

    def remove_and_re_add() -> None:
        svc.remove_credential(sid, "anthropic")
        svc.set_credential(sid, "anthropic", SECRET_2)

    checker.during = remove_and_re_add
    with pytest.raises(CredentialSettingsError) as err:
        svc.validate(sid, "anthropic")
    assert err.value.kind is CredentialSettingsErrorKind.VALIDATION_SUPERSEDED
    assert _state(svc, sid, "anthropic").validation_status is ValidationStatus.UNTESTED


def test_validation_without_a_key_is_not_configured(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    checker = Checker()
    svc = _service(sf, checker)
    for operation in (
        lambda: svc.validate(sid, "anthropic"),
        lambda: svc.set_enabled(sid, "anthropic", False),
    ):
        with pytest.raises(CredentialSettingsError) as err:
            operation()
        assert err.value.kind is CredentialSettingsErrorKind.NOT_CONFIGURED
    # Metadata without a retrievable key is not validated either.
    svc.set_credential(sid, "anthropic", SECRET)
    backend.secrets.clear()
    with pytest.raises(CredentialSettingsError) as err:
        svc.validate(sid, "anthropic")
    assert err.value.kind is CredentialSettingsErrorKind.NOT_CONFIGURED
    assert checker.calls == []


def test_checker_failure_records_nothing(sf: Any, backend: MemoryKeyring) -> None:
    sid = uuid4()

    def boom(provider: str, key: str) -> tuple[ValidationStatus, None]:
        raise RuntimeError(f"upstream echoed {key}")

    svc = ByokSettingsService(OSKeychainCredentialStore(), sf, boom)
    svc.set_credential(sid, "anthropic", SECRET)
    with pytest.raises(CredentialSettingsError) as err:
        svc.validate(sid, "anthropic")
    assert err.value.kind is CredentialSettingsErrorKind.VALIDATION_UNAVAILABLE
    assert SECRET not in str(err.value)
    assert err.value.__cause__ is None and err.value.__suppress_context__
    assert _state(svc, sid, "anthropic").validation_status is ValidationStatus.UNTESTED


def test_enable_disable_drives_the_shared_predicate(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    svc.set_enabled(sid, "anthropic", False)
    assert _state(svc, sid, "anthropic").enabled is False
    assert _agreement(sf, sid) == (False, False)
    svc.set_enabled(sid, "anthropic", True)
    assert _agreement(sf, sid) == (True, True)


def test_openrouter_model_is_the_resolver_model_and_fallback_order_holds(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    svc.set_credential(sid, "openrouter", OR_SECRET)
    # OpenRouter available without a model: fail closed, agreeing.
    assert _agreement(sf, sid) == (False, False)

    for bad in ("", "   ", "openrouter/auto", "x" * 257):
        with pytest.raises(CredentialSettingsError) as err:
            svc.set_openrouter_model(sid, bad)
        assert err.value.kind is CredentialSettingsErrorKind.INVALID_INPUT

    svc.set_openrouter_model(sid, "  mistralai/mistral-large-2411 ")
    assert svc.read(sid).openrouter_model == "mistralai/mistral-large-2411"
    assert _agreement(sf, sid) == (True, True)
    binding = ProviderResolver(
        OSKeychainCredentialStore(), session_factory=sf
    ).resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    assert [r.provider_name for r in binding.eligible_writer_routes] == [
        "anthropic",
        "openrouter",
    ]
    assert binding.eligible_writer_routes[1].model_identifier == (
        "mistralai/mistral-large-2411"
    )

    svc.set_openrouter_model(sid, None)
    assert svc.read(sid).openrouter_model is None
    assert _agreement(sf, sid) == (False, False)
    # Disabling OpenRouter leaves Anthropic alone runnable.
    svc.set_enabled(sid, "openrouter", False)
    assert _agreement(sf, sid) == (True, True)


def test_settings_changes_do_not_rebind_an_in_flight_turn(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    resolver = ProviderResolver(OSKeychainCredentialStore(), session_factory=sf)
    bound = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)

    svc.set_credential(sid, "anthropic", SECRET_2)
    assert bound.adapter._primary._api_key == SECRET  # type: ignore[attr-defined]
    svc.remove_credential(sid, "anthropic")
    assert bound.adapter._primary._api_key == SECRET  # type: ignore[attr-defined]

    svc.set_credential(sid, "anthropic", SECRET_2)
    rebound = resolver.resolve_for_turn(RuntimeAccessPath.BYOK, sid)
    assert rebound.adapter._primary._api_key == SECRET_2  # type: ignore[attr-defined]


def test_read_only_store_reports_writes_unavailable(sf: Any) -> None:
    sid = uuid4()
    svc = ByokSettingsService(FallbackEnvCredentialStore(), sf, Checker())
    assert svc.read(sid).store_writable is False
    for operation in (
        lambda: svc.set_credential(sid, "anthropic", SECRET),
        lambda: svc.remove_credential(sid, "anthropic"),
    ):
        with pytest.raises(CredentialSettingsError) as err:
            operation()
        assert err.value.kind is CredentialSettingsErrorKind.STORE_READ_ONLY
    assert _row(sf, sid, "anthropic") is None


def test_store_failure_on_replace_never_reports_the_old_verdict(
    sf: Any, backend: MemoryKeyring, caplog: pytest.LogCaptureFixture
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    svc.validate(sid, "anthropic")
    backend.fail_with = f"keychain echoed {SECRET_2}"

    with caplog.at_level(logging.DEBUG), pytest.raises(CredentialSettingsError) as err:
        svc.set_credential(sid, "anthropic", SECRET_2)

    assert err.value.kind is CredentialSettingsErrorKind.STORE_UNAVAILABLE
    assert SECRET_2 not in str(err.value) and SECRET_2 not in caplog.text
    assert err.value.__cause__ is None and err.value.__suppress_context__
    row = _row(sf, sid, "anthropic")
    assert row is not None and row.validation_status == ValidationStatus.UNTESTED
    # Unreadable store: presence is unknown, not absent.
    assert _state(svc, sid, "anthropic").credential_present is None
    backend.fail_with = None
    svc.set_credential(sid, "anthropic", SECRET_2)
    assert backend.secrets[("afterworlds_byok.anthropic", str(sid))] == SECRET_2


def test_store_failure_on_remove_leaves_nothing_runnable_and_can_retry(
    sf: Any, backend: MemoryKeyring
) -> None:
    sid = uuid4()
    svc = _service(sf)
    svc.set_credential(sid, "anthropic", SECRET)
    backend.fail_with = "keychain offline"
    with pytest.raises(CredentialSettingsError) as err:
        svc.remove_credential(sid, "anthropic")
    assert err.value.kind is CredentialSettingsErrorKind.STORE_UNAVAILABLE
    backend.fail_with = None
    assert _row(sf, sid, "anthropic") is None
    assert _agreement(sf, sid) == (False, False)
    svc.remove_credential(sid, "anthropic")
    assert backend.secrets == {}


@pytest.mark.parametrize(
    "key", ["", " ", f"{SECRET} trailing", f"{SECRET}\n", "k" * 513, "a\x00b"]
)
def test_malformed_keys_are_rejected_without_echo(
    sf: Any, backend: MemoryKeyring, key: str
) -> None:
    sid = uuid4()
    with pytest.raises(CredentialSettingsError) as err:
        _service(sf).set_credential(sid, "anthropic", key)
    assert err.value.kind is CredentialSettingsErrorKind.INVALID_INPUT
    assert SECRET not in err.value.message
    assert backend.secrets == {} and _row(sf, sid, "anthropic") is None


def test_unknown_provider_is_rejected(sf: Any, backend: MemoryKeyring) -> None:
    with pytest.raises(CredentialSettingsError) as err:
        _service(sf).set_credential(uuid4(), "openai", SECRET)
    assert err.value.kind is CredentialSettingsErrorKind.INVALID_INPUT


def test_database_failure_is_typed(backend: MemoryKeyring) -> None:
    def broken() -> Session:
        raise OperationalError("SELECT", {}, Exception("database is locked"))

    svc = ByokSettingsService(OSKeychainCredentialStore(), broken, Checker())
    for operation in (
        lambda: svc.read(uuid4()),
        lambda: svc.set_credential(uuid4(), "anthropic", SECRET),
        lambda: svc.set_openrouter_model(uuid4(), "mistralai/mistral-large-2411"),
    ):
        with pytest.raises(CredentialSettingsError) as err:
            operation()
        assert err.value.kind is CredentialSettingsErrorKind.METADATA_UNAVAILABLE
    assert backend.secrets == {}
