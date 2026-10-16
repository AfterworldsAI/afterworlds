#!/usr/bin/env python
"""E2E only -- the built app for the CRD Issue 20 account/BYOK flows.

Serves ``create_app`` on a disposable SQLite store in a fresh temp directory
with ``AFTERWORLDS_FAKE_PROVIDER=1`` (fake narrative passes and the fake
credential check: no provider is ever contacted) and ``frontend/dist``.

The production ``OSKeychainCredentialStore`` runs unchanged over the
in-memory keyring backend of ``scripts/e2e_memory_keyring.py``; the launcher
refuses to serve unless that backend is the active one, so no synthetic key
can reach the platform credential manager. ``AFTERWORLDS_CI`` is removed, as
it would select the read-only env-var store.

Test-only routes (inserted ahead of the frontend mount, never in
``create_app``):

* ``POST /__e2e__/account/{scenario}`` seeds entitlement events through
  Issue 13's ``receive_entitlement_event`` path;
* ``POST /__e2e__/keyring?fail=<text>`` makes the keyring backend raise with
  that text (empty clears it); ``GET /__e2e__/keyring`` returns only the
  number of stored keys.

Usage (from the repository root, ``src`` and the root on ``PYTHONPATH``)::

    python scripts/e2e_account_server.py --port 8002
"""

from __future__ import annotations

import argparse
import os
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_app(work: Path) -> Any:
    from fastapi import FastAPI
    from fastapi.routing import APIRoute

    from afterworlds.api.app import create_app
    from afterworlds.api.config import ApiSettings
    from afterworlds.entitlement.enums import EntitlementEventType as E
    from afterworlds.entitlement.enums import HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        ByokLicenseActivatedPayload,
        CloudServicesActivatedPayload,
        HostedAccessActivatedPayload,
        ManualCreditAdjustmentPayload,
        SubscriptionCreditGrantPayload,
        TopUpCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService
    from scripts.e2e_memory_keyring import install

    backend = install()
    app: FastAPI = create_app(
        ApiSettings(
            database_url=f"sqlite:///{work / 'store.db'}",
            frontend_dist_dir=REPO_ROOT / "frontend" / "dist",
        )
    )
    now = datetime.now(UTC)
    scenarios: dict[str, list[tuple[E, Any]]] = {
        # Paid Starter Access with a negative included balance, a tiny top-up,
        # a BYOK license and naturally expired Cloud Services.
        "starter_negative": [
            (
                E.HOSTED_ACCESS_ACTIVATED,
                HostedAccessActivatedPayload(
                    plan=HostedAccessPlan.STARTER_ACCESS, effective_at=now
                ),
            ),
            (
                E.SUBSCRIPTION_CREDIT_GRANT,
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1")),
            ),
            (
                E.MANUAL_CREDIT_ADJUSTMENT,
                ManualCreditAdjustmentPayload(
                    hosted_credit_delta=Decimal("-13.3456"),
                    reason="e2e",
                    adjusted_by="e2e",
                ),
            ),
            (
                E.TOP_UP_CREDIT_GRANT,
                TopUpCreditGrantPayload(top_up_credit_delta=Decimal("0.0001")),
            ),
            (E.BYOK_LICENSE_ACTIVATED, ByokLicenseActivatedPayload(purchased_at=now)),
            (
                E.CLOUD_SERVICES_ACTIVATED,
                CloudServicesActivatedPayload(expires_at=now - timedelta(days=1)),
            ),
        ],
        # Fresh restore of runnable hosted access on top of the above.
        "hosted_credits": [
            (
                E.HOSTED_ACCESS_ACTIVATED,
                HostedAccessActivatedPayload(
                    plan=HostedAccessPlan.SUBSCRIPTION, effective_at=now
                ),
            ),
            (
                E.SUBSCRIPTION_CREDIT_GRANT,
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
            ),
        ],
    }

    def seed(scenario: str) -> dict[str, str]:
        with app.state.session_factory() as s:
            service = EntitlementService(s)
            for event_type, payload in scenarios[scenario]:
                service.receive_entitlement_event(
                    app.state.sojourner_id, event_type, payload
                )
        return {"seeded": scenario}

    def set_failure(fail: str = "") -> dict[str, bool]:
        backend.fail_with = fail or None
        return {"failing": backend.fail_with is not None}

    def count() -> dict[str, int]:
        return {"stored_keys": len(backend.secrets)}

    # Ahead of the frontend's StaticFiles mount at "/", which matches every
    # path it is offered.
    for route in (
        APIRoute("/__e2e__/account/{scenario}", seed, methods=["POST"]),
        APIRoute("/__e2e__/keyring", set_failure, methods=["POST"]),
        APIRoute("/__e2e__/keyring", count, methods=["GET"]),
    ):
        app.router.routes.insert(0, route)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()

    work = Path(tempfile.mkdtemp(prefix="afterworlds-e2e-account-"))
    os.environ.pop("AFTERWORLDS_CI", None)
    os.environ["AFTERWORLDS_FAKE_PROVIDER"] = "1"
    os.environ["AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"] = str(work / "chroma")
    app = build_app(work)

    import keyring

    from scripts.e2e_memory_keyring import MemoryKeyring

    if not isinstance(keyring.get_keyring(), MemoryKeyring):
        raise SystemExit("refusing to serve: the in-memory keyring is not active")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
