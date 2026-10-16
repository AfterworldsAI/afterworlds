"""/api/account -- billing, Cloud Services and BYOK settings (CRD Issue 20).

The app is the real ``create_app`` on a migrated tmp SQLite file. The
production ``OSKeychainCredentialStore`` runs over a disposable in-memory
keyring backend; ``AFTERWORLDS_FAKE_PROVIDER`` makes explicit validation use
the fake checker, so no provider is ever contacted.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import keyring
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.entitlement.enums import (
    CloudServicesDeactivationReason,
    EntitlementEventType,
    HostedAccessDeactivationReason,
    HostedAccessPlan,
)
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.payloads import (
    ByokLicenseActivatedPayload,
    CloudServicesActivatedPayload,
    CloudServicesLapsedPayload,
    HostedAccessActivatedPayload,
    HostedAccessDeactivatedPayload,
    ManualCreditAdjustmentPayload,
    SubscriptionCreditGrantPayload,
    TopUpCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from scripts.e2e_memory_keyring import MemoryKeyring
from scripts.e2e_memory_keyring import install as install_memory_keyring

SECRET = "sk-ant-SYNTHETIC-SECRET-0123456789abcdef"  # pragma: allowlist secret
OR_SECRET = "sk-or-SYNTHETIC-SECRET-0123456789abcdef"  # pragma: allowlist secret
INVALID_SECRET = "sk-ant-SYNTHETIC-invalid-key-000"  # pragma: allowlist secret
NOW = datetime.now(UTC)


@pytest.fixture()
def backend(monkeypatch: pytest.MonkeyPatch) -> Iterator[MemoryKeyring]:
    monkeypatch.delenv("AFTERWORLDS_CI", raising=False)
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    previous = keyring.get_keyring()
    yield install_memory_keyring()
    keyring.set_keyring(previous)


@pytest.fixture()
def client(app_settings: ApiSettings, backend: MemoryKeyring) -> Iterator[TestClient]:
    with TestClient(create_app(app_settings)) as c:
        yield c


def _events(client: TestClient, *events: tuple[EntitlementEventType, Any]) -> None:
    session = client.app.state.session_factory()  # type: ignore[attr-defined]
    try:
        service = EntitlementService(session)
        for event_type, payload in events:
            service.receive_entitlement_event(
                client.app.state.sojourner_id,  # type: ignore[attr-defined]
                event_type,
                payload,
            )
    finally:
        session.close()


def _hosted(plan: HostedAccessPlan = HostedAccessPlan.SUBSCRIPTION) -> Any:
    return (
        EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
        HostedAccessActivatedPayload(plan=plan, effective_at=NOW),
    )


def _grant(amount: str) -> Any:
    return (
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal(amount)),
    )


def _top_up(amount: str) -> Any:
    return (
        EntitlementEventType.TOP_UP_CREDIT_GRANT,
        TopUpCreditGrantPayload(top_up_credit_delta=Decimal(amount)),
    )


def _adjust(hosted: str | None = None, top_up: str | None = None) -> Any:
    return (
        EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
        ManualCreditAdjustmentPayload(
            hosted_credit_delta=Decimal(hosted) if hosted else None,
            top_up_credit_delta=Decimal(top_up) if top_up else None,
            reason="test",
            adjusted_by="test",
        ),
    )


_BYOK = (
    EntitlementEventType.BYOK_LICENSE_ACTIVATED,
    ByokLicenseActivatedPayload(purchased_at=NOW),
)


def _cloud(expires_at: datetime) -> Any:
    return (
        EntitlementEventType.CLOUD_SERVICES_ACTIVATED,
        CloudServicesActivatedPayload(expires_at=expires_at),
    )


def _db_bytes(settings: ApiSettings) -> list[bytes]:
    """The SQLite file and its WAL, whichever exist."""
    db = Path(settings.database_url.removeprefix("sqlite:///"))
    return [p.read_bytes() for p in (db, Path(f"{db}-wal")) if p.exists()]


def _account(client: TestClient) -> dict[str, Any]:
    resp = client.get("/api/account")
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Billing and Cloud Services
# ---------------------------------------------------------------------------


def test_no_plan_is_null_not_zero(client: TestClient) -> None:
    body = _account(client)
    assert body["credits"] == {
        "included": None,
        "top_up": None,
        "total": None,
        "hosted_turn_available": False,
        "hosted_unavailable_reason": "no_subscription",
        "schema_version": 1,
    }
    assert body["cloud_services"] == "not_activated"
    assert body["byok"]["license_active"] is False
    assert body["selected_access_path"] is None
    assert body["blocked_error_code"] == "entitlement_blocked"
    assert body["usage_estimate_available"] is False
    assert body["purchase_available"] is False
    assert body["trial_enrollment_available"] is False


@pytest.mark.parametrize(
    ("events", "included", "top_up", "total", "available", "reason"),
    [
        (
            [_grant("99999999.9999")],
            "99999999.9999",
            "0.0000",
            "99999999.9999",
            True,
            None,
        ),
        ([_grant("0.0001")], "0.0001", "0.0000", "0.0001", True, None),
        (
            [_grant("1"), _adjust(hosted="-1")],
            "0.0000",
            "0.0000",
            "0.0000",
            False,
            "credits_exhausted",
        ),
        (
            [_grant("1"), _adjust(hosted="-13.3456"), _top_up("0.0001")],
            "-12.3456",
            "0.0001",
            "-12.3455",
            False,
            "credits_exhausted",
        ),
        (
            [_grant("1"), _adjust(hosted="-1.0001")],
            "-0.0001",
            "0.0000",
            "-0.0001",
            False,
            "credits_exhausted",
        ),
        ([_top_up("2.5")], "0.0000", "2.5000", "2.5000", True, None),
    ],
)
def test_balances_keep_four_place_precision_and_sign(
    client: TestClient,
    events: list[Any],
    included: str,
    top_up: str,
    total: str,
    available: bool,
    reason: str | None,
) -> None:
    _events(client, _hosted(), *events)
    credits = _account(client)["credits"]
    assert (credits["included"], credits["top_up"], credits["total"]) == (
        included,
        top_up,
        total,
    )
    assert credits["hosted_turn_available"] is available
    assert credits["hosted_unavailable_reason"] == reason


def test_inactive_hosted_access_retains_balances(client: TestClient) -> None:
    _events(
        client,
        _hosted(),
        _grant("40.5"),
        _top_up("3.25"),
        (
            EntitlementEventType.HOSTED_ACCESS_DEACTIVATED,
            HostedAccessDeactivatedPayload(
                effective_at=NOW, reason=HostedAccessDeactivationReason.PAYMENT_FAILED
            ),
        ),
    )
    credits = _account(client)["credits"]
    assert (credits["included"], credits["top_up"], credits["total"]) == (
        "40.5000",
        "3.2500",
        "43.7500",
    )
    assert credits["hosted_turn_available"] is False
    assert credits["hosted_unavailable_reason"] == "subscription_inactive"


def test_cloud_services_states_are_independent_of_byok(
    client: TestClient, backend: MemoryKeyring
) -> None:
    _events(client, _BYOK, _cloud(NOW + timedelta(days=30)))
    assert _account(client)["cloud_services"] == "active"

    # Natural expiry lapses Cloud Services; the BYOK license is untouched.
    _events(client, _cloud(NOW - timedelta(seconds=1)))
    body = _account(client)
    assert body["cloud_services"] == "lapsed"
    assert body["byok"]["license_active"] is True

    _events(
        client,
        _cloud(NOW + timedelta(days=30)),
        (
            EntitlementEventType.CLOUD_SERVICES_LAPSED,
            CloudServicesLapsedPayload(
                effective_at=NOW, reason=CloudServicesDeactivationReason.NON_RENEWAL
            ),
        ),
    )
    client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
    body = _account(client)
    assert body["cloud_services"] == "lapsed"
    assert body["byok"]["license_active"] is True
    # Lapse gates neither BYOK settings nor BYOK selection.
    assert body["byok"]["byok_ready"] is True
    assert body["selected_access_path"] == "byok"


def test_starter_access_state_is_not_presented_as_a_trial(client: TestClient) -> None:
    _events(client, _hosted(HostedAccessPlan.STARTER_ACCESS), _grant("10"))
    resp = client.get("/api/account")
    assert "trial" not in resp.text.replace("trial_enrollment_available", "")
    body = resp.json()
    assert body["credits"]["total"] == "10.0000"
    assert body["trial_enrollment_available"] is False


def test_reads_and_settings_do_not_touch_entitlements(
    client: TestClient, backend: MemoryKeyring
) -> None:
    factory = client.app.state.session_factory  # type: ignore[attr-defined]

    def snapshot() -> tuple[int, int]:
        with factory() as s:
            return (
                s.scalar(select(func.count()).select_from(EntitlementEvent)),
                s.scalar(select(func.count()).select_from(RuntimeEntitlementState)),
            )

    assert snapshot() == (0, 0)
    _account(client)
    assert snapshot() == (0, 0)  # an absent Sojourner gets no row

    _events(client, _hosted(), _grant("5"))
    before = snapshot()
    client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
    client.put("/api/account/byok/anthropic/enabled", json={"enabled": False})
    client.put(
        "/api/account/byok/openrouter/model",
        json={"model_identifier": "mistralai/mistral-large-2411"},
    )
    client.post(
        "/api/account/byok/anthropic/validate",
        json={"acknowledge_provider_contact": True},
    )
    client.delete("/api/account/byok/anthropic/credential")
    _account(client)
    assert snapshot() == before
    assert _account(client)["credits"]["total"] == "5.0000"


# ---------------------------------------------------------------------------
# BYOK settings over HTTP
# ---------------------------------------------------------------------------


def _provider(body: dict[str, Any], name: str) -> dict[str, Any]:
    return next(p for p in body["byok"]["providers"] if p["provider"] == name)


def test_settings_lifecycle_survives_reload_and_matches_selection(
    app_settings: ApiSettings, backend: MemoryKeyring
) -> None:
    with TestClient(create_app(app_settings)) as client:
        _events(client, _BYOK, _hosted(), _grant("1"))
        resp = client.put(
            "/api/account/byok/anthropic/credential", json={"api_key": SECRET}
        )
        assert resp.status_code == 200, resp.text
        assert SECRET not in resp.text
        anthropic = _provider(resp.json(), "anthropic")
        assert anthropic["credential_present"] is True
        assert anthropic["validation_status"] == "untested"
        # BYOK-first when both paths are runnable; untested is eligible.
        assert resp.json()["selected_access_path"] == "byok"
        assert resp.json()["byok"]["byok_ready"] is True

        resp = client.put(
            "/api/account/byok/openrouter/credential", json={"api_key": OR_SECRET}
        )
        # OpenRouter key without a model: BYOK not ready, hosted selected.
        assert resp.json()["byok"]["byok_ready"] is False
        assert resp.json()["selected_access_path"] == "hosted"
        resp = client.put(
            "/api/account/byok/openrouter/model",
            json={"model_identifier": "mistralai/mistral-large-2411"},
        )
        assert resp.json()["byok"]["openrouter_model"] == (
            "mistralai/mistral-large-2411"
        )
        assert resp.json()["byok"]["byok_ready"] is True

        resp = client.post("/api/account/byok/anthropic/validate", json={})
        assert resp.status_code == 422
        resp = client.post(
            "/api/account/byok/anthropic/validate",
            json={"acknowledge_provider_contact": True},
        )
        assert resp.status_code == 200, resp.text
        assert _provider(resp.json(), "anthropic")["validation_status"] == "valid"

        resp = client.put(
            "/api/account/byok/openrouter/enabled", json={"enabled": False}
        )
        assert _provider(resp.json(), "openrouter")["enabled"] is False
        readiness = client.app.state.byok_readiness_provider  # type: ignore[attr-defined]
        sid = client.app.state.sojourner_id  # type: ignore[attr-defined]
        assert readiness.is_byok_runnable(sid) is resp.json()["byok"]["byok_ready"]

    with TestClient(create_app(app_settings)) as reloaded:
        body = _account(reloaded)
        anthropic = _provider(body, "anthropic")
        openrouter = _provider(body, "openrouter")
        assert (anthropic["credential_present"], anthropic["validation_status"]) == (
            True,
            "valid",
        )
        assert (openrouter["credential_present"], openrouter["enabled"]) == (
            True,
            False,
        )
        assert body["byok"]["openrouter_model"] == "mistralai/mistral-large-2411"

        resp = reloaded.delete("/api/account/byok/anthropic/credential")
        assert resp.status_code == 200
        assert _provider(resp.json(), "anthropic")["credential_present"] is False
        assert _provider(resp.json(), "anthropic")["validation_status"] is None


def test_invalid_verdict_makes_byok_not_ready(client: TestClient) -> None:
    _events(client, _BYOK)
    client.put(
        "/api/account/byok/anthropic/credential",
        json={"api_key": INVALID_SECRET},
    )
    resp = client.post(
        "/api/account/byok/anthropic/validate",
        json={"acknowledge_provider_contact": True},
    )
    assert _provider(resp.json(), "anthropic")["validation_status"] == "invalid"
    assert resp.json()["byok"]["byok_ready"] is False
    assert resp.json()["blocked_error_code"] == "byok_credentials_required"


@pytest.mark.parametrize(
    ("method", "path", "payload", "status", "code"),
    [
        (
            "post",
            "anthropic/validate",
            {"acknowledge_provider_contact": True},
            409,
            "credential_not_configured",
        ),
        (
            "put",
            "anthropic/enabled",
            {"enabled": True},
            409,
            "credential_not_configured",
        ),
        ("put", "anthropic/enabled", {"enabled": "yes"}, 422, "validation_failed"),
        (
            "put",
            "openrouter/model",
            {"model_identifier": "openrouter/auto"},
            422,
            "validation_failed",
        ),
        ("put", "openai/credential", {"api_key": SECRET}, 422, "validation_failed"),
        (
            "put",
            "anthropic/credential",
            {"api_key": f"{SECRET} x"},
            422,
            "validation_failed",
        ),
        (
            "put",
            "anthropic/credential",
            {"api_key": SECRET, "note": SECRET},
            422,
            "validation_failed",
        ),
        (
            "put",
            "anthropic/credential",
            {"api_key": SECRET * 20},
            422,
            "validation_failed",
        ),
        ("put", "anthropic/credential", {"api_key": 12345}, 422, "validation_failed"),
    ],
)
def test_typed_failures_never_echo_secrets(
    client: TestClient,
    backend: MemoryKeyring,
    method: str,
    path: str,
    payload: dict[str, Any],
    status: int,
    code: str,
) -> None:
    resp = getattr(client, method)(f"/api/account/byok/{path}", json=payload)
    assert resp.status_code == status, resp.text
    assert resp.json()["error_code"] == code
    assert SECRET not in resp.text
    assert backend.secrets == {}


def test_keychain_failure_is_typed_and_leaks_nothing(
    client: TestClient,
    backend: MemoryKeyring,
    app_settings: ApiSettings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    backend.fail_with = f"backend echoed {SECRET}"
    with caplog.at_level(logging.DEBUG):
        put = client.put(
            "/api/account/byok/anthropic/credential", json={"api_key": SECRET}
        )
        read = client.get("/api/account")
    assert put.status_code == 503
    assert put.json()["error_code"] == "credential_store_unavailable"
    # Unreadable store: presence and readiness are unknown, not absent.
    assert read.status_code == 200
    assert _provider(read.json(), "anthropic")["credential_present"] is None
    assert read.json()["byok"]["byok_ready"] is None
    for text in (put.text, read.text, caplog.text):
        assert SECRET not in text
    for data in _db_bytes(app_settings):
        assert SECRET.encode() not in data


def test_secret_never_reaches_sqlite_after_full_lifecycle(
    client: TestClient, app_settings: ApiSettings
) -> None:
    client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
    client.post(
        "/api/account/byok/anthropic/validate",
        json={"acknowledge_provider_contact": True},
    )
    client.delete("/api/account/byok/anthropic/credential")
    for data in _db_bytes(app_settings):
        assert SECRET.encode() not in data
        assert SECRET[:20].encode() not in data


def test_read_only_store_reports_writes_unavailable(
    app_settings: ApiSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AFTERWORLDS_CI", "1")
    with TestClient(create_app(app_settings)) as client:
        assert _account(client)["byok"]["credential_store_writable"] is False
        resp = client.put(
            "/api/account/byok/anthropic/credential", json={"api_key": SECRET}
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "credential_store_read_only"
        assert SECRET not in resp.text


def test_fake_mode_validation_never_builds_a_provider_client(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anthropic
    import openai

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider client constructed in fake mode")

    monkeypatch.setattr(anthropic, "Anthropic", forbidden)
    monkeypatch.setattr(openai, "OpenAI", forbidden)
    client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
    resp = client.post(
        "/api/account/byok/anthropic/validate",
        json={"acknowledge_provider_contact": True},
    )
    assert resp.status_code == 200, resp.text


def test_product_mode_uses_the_live_credential_validator(
    app_settings: ApiSettings, backend: MemoryKeyring, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AFTERWORLDS_FAKE_PROVIDER")
    from afterworlds.pipeline.provider.credentials import (
        CredentialValidator,
        ValidationStatus,
    )

    calls: list[str] = []
    monkeypatch.setattr(
        CredentialValidator,
        "_check",
        staticmethod(
            lambda provider, key: (
                calls.append(provider),
                (ValidationStatus.VALID, None),
            )[1]
        ),
    )
    with TestClient(create_app(app_settings)) as client:
        client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
        assert calls == []
        client.post(
            "/api/account/byok/anthropic/validate",
            json={"acknowledge_provider_contact": True},
        )
    assert calls == ["anthropic"]


def test_validation_superseded_is_a_typed_conflict(
    client: TestClient, backend: MemoryKeyring
) -> None:
    settings = client.app.state.byok_settings  # type: ignore[attr-defined]
    original = settings._check

    def replace_mid_check(provider: str, key: str) -> Any:
        settings.set_credential(
            client.app.state.sojourner_id,  # type: ignore[attr-defined]
            provider,
            "sk-ant-SYNTHETIC-REPLACEMENT-0000",
        )
        return original(provider, key)

    settings._check = replace_mid_check
    client.put("/api/account/byok/anthropic/credential", json={"api_key": SECRET})
    resp = client.post(
        "/api/account/byok/anthropic/validate",
        json={"acknowledge_provider_contact": True},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "credential_validation_superseded"
    assert _provider(_account(client), "anthropic")["validation_status"] == "untested"


def test_account_routes_publish_typed_error_contract(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    put = schema["paths"]["/api/account/byok/{provider}/credential"]["put"]
    assert set(put["responses"]) >= {"200", "409", "422", "503"}
    assert "sojourner_id" not in str(put)
    request = schema["components"]["schemas"]["CredentialWriteRequest"]
    assert request["properties"]["api_key"]["format"] == "password"
    unused = str(schema["components"]["schemas"]["AccountStatusResponse"])
    assert "fallback_model" not in unused
