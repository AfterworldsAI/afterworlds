"""CRD Issue 21 spine harness: the real ``create_app`` with the production
``ProviderResolver``, readiness and binding, and only the external provider
transport (``scripts/scripted_provider.py``) and credential storage (the
in-memory keyring) replaced. ``AFTERWORLDS_FAKE_PROVIDER`` is unset, so no
``FakeProviderResolver`` or fake credential check is involved.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import keyring
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.entitlement.payloads import (
    ByokLicenseActivatedPayload,
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from scripts.e2e_memory_keyring import install as install_memory_keyring
from scripts.scripted_provider import SYNTHETIC_HOSTED_KEY, ScriptedProvider

BYOK_ANTHROPIC_KEY = "sk-ant-SYNTHETIC-byok-0123456789"  # pragma: allowlist secret
BYOK_OPENROUTER_KEY = "sk-or-SYNTHETIC-byok-0123456789"  # pragma: allowlist secret


@dataclass
class Spine:
    client: TestClient
    provider: ScriptedProvider

    @property
    def session_factory(self) -> Any:
        return self.client.app.state.session_factory  # type: ignore[attr-defined]

    @property
    def sojourner_id(self) -> UUID:
        return self.client.app.state.sojourner_id  # type: ignore[attr-defined,no-any-return]

    # -- entitlement -------------------------------------------------------

    def _events(self, *events: tuple[EntitlementEventType, Any]) -> None:
        with self.session_factory() as session:
            service = EntitlementService(session)
            for event_type, payload in events:
                service.receive_entitlement_event(
                    self.sojourner_id, event_type, payload
                )

    def seed_hosted(self, credits: str = "1000") -> None:
        self._events(
            (
                EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
                HostedAccessActivatedPayload(
                    plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
                ),
            ),
            (
                EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal(credits)),
            ),
        )

    def seed_byok(self, *, openrouter: bool = False) -> None:
        """A BYOK license plus a stored key through the real settings API
        (its live credential check runs over the scripted transport)."""
        self._events(
            (
                EntitlementEventType.BYOK_LICENSE_ACTIVATED,
                ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
            )
        )
        resp = self.client.put(
            "/api/account/byok/anthropic/credential",
            json={"api_key": BYOK_ANTHROPIC_KEY},
        )
        assert resp.status_code == 200, resp.text
        if openrouter:
            resp = self.client.put(
                "/api/account/byok/openrouter/credential",
                json={"api_key": BYOK_OPENROUTER_KEY},
            )
            assert resp.status_code == 200, resp.text
            resp = self.client.put(
                "/api/account/byok/openrouter/model",
                json={"model_identifier": "anthropic/claude-haiku-4-5"},
            )
            assert resp.status_code == 200, resp.text

    def deductions(self) -> dict[str, Decimal]:
        """turn_id -> total hosted credit deducted, from the event log."""
        out: dict[str, Decimal] = {}
        with self.session_factory() as session:
            rows = session.scalars(
                select(EntitlementEvent).where(
                    EntitlementEvent.event_type
                    == EntitlementEventType.CREDIT_DEDUCTION.value
                )
            ).all()
            for row in rows:
                payload = json.loads(row.payload_json)
                total = abs(Decimal(str(payload["hosted_credit_delta"]))) + abs(
                    Decimal(str(payload["top_up_credit_delta"]))
                )
                out[str(row.turn_id)] = total
        return out

    # -- stories -----------------------------------------------------------

    def create(self, mode: str) -> str:
        resp = self.client.post("/api/stories", json={"title": "Spine", "mode": mode})
        assert resp.status_code == 201, resp.text
        return str(resp.json()["story_id"])

    def setup_branching(
        self, story_id: str, style: str, count_range: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "mode": "branching",
            "interaction_style": style,
            "branching_cadence": "balanced",
        }
        if count_range is not None:
            body["branch_count_range"] = count_range
        resp = self.client.post(f"/api/stories/{story_id}/setup", json=body)
        assert resp.status_code == 200, resp.text
        return resp.json()  # type: ignore[no-any-return]

    def begin(self, story_id: str) -> dict[str, Any]:
        resp = self.client.post(f"/api/stories/{story_id}/begin")
        assert resp.status_code == 200, resp.text
        return resp.json()  # type: ignore[no-any-return]

    def turn(self, story_id: str, text: str) -> dict[str, Any]:
        resp = self.client.post(
            f"/api/stories/{story_id}/turns", json={"user_input": text}
        )
        assert resp.status_code == 200, resp.text
        return resp.json()  # type: ignore[no-any-return]

    def visible(self, story_id: str) -> dict[str, Any] | None:
        resp = self.client.get(f"/api/stories/{story_id}/visible-state")
        assert resp.status_code == 200, resp.text
        return resp.json()["visible_state"]  # type: ignore[no-any-return]

    def transcript(self, story_id: str) -> list[dict[str, Any]]:
        resp = self.client.get(f"/api/stories/{story_id}/turns?limit=200")
        assert resp.status_code == 200, resp.text
        return resp.json()["turns"]  # type: ignore[no-any-return]


@pytest.fixture()
def spine(
    app_settings: ApiSettings, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Spine]:
    monkeypatch.delenv("AFTERWORLDS_FAKE_PROVIDER", raising=False)
    monkeypatch.delenv("AFTERWORLDS_CI", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", SYNTHETIC_HOSTED_KEY)
    previous = keyring.get_keyring()
    install_memory_keyring()
    provider = ScriptedProvider().install()
    try:
        with TestClient(create_app(app_settings)) as client:
            yield Spine(client, provider)
    finally:
        provider.uninstall()
        keyring.set_keyring(previous)
