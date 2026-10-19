#!/usr/bin/env python
"""E2E only -- the built app as a remote deployment (prerequisite #205).

Serves ``create_app`` with ``AFTERWORLDS_DEPLOYMENT=remote`` on disposable
content, control, Chroma and notice-outbox stores in a fresh temp directory,
with ``AFTERWORLDS_FAKE_PROVIDER=1`` and ``frontend/dist``. Session cookies
stay ``Secure``: Chromium treats ``http://127.0.0.1`` as a secure context.

Test-only routes (inserted ahead of the frontend mount, never in
``create_app``; outside ``/api``, so not part of the product contract):

* ``GET /__e2e__/outbox?address=&kind=`` -- the latest code mailed to an
  address (stands in for the user's mailbox);
* ``POST /__e2e__/bootstrap`` ``{contact_address, password}`` -- runs the real
  ``python -m afterworlds.remote.bootstrap`` command against this server's
  control store, as an operator on the host would;
* ``POST /__e2e__/entitlement/{account_id}`` -- grants hosted credits through
  Issue 13's ``receive_entitlement_event``.

Usage (from the repository root, ``src`` and the root on ``PYTHONPATH``)::

    python scripts/e2e_remote_server.py --port 8004
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_app(work: Path) -> Any:
    from fastapi import Body, FastAPI
    from fastapi.routing import APIRoute

    from afterworlds.api.app import create_app
    from afterworlds.api.config import ApiSettings
    from afterworlds.entitlement.enums import EntitlementEventType as E
    from afterworlds.entitlement.enums import HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        HostedAccessActivatedPayload,
        SubscriptionCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService

    control_url = f"sqlite:///{work / 'control.db'}"
    outbox = work / "outbox"
    app: FastAPI = create_app(
        ApiSettings(
            database_url=f"sqlite:///{work / 'content.db'}",
            frontend_dist_dir=REPO_ROOT / "frontend" / "dist",
            deployment="remote",
            control_database_url=control_url,
            notice_outbox_dir=outbox,
        )
    )

    def latest_code(address: str, kind: str) -> dict[str, str]:
        app.state.identity.drain_notices()  # notices are written in the background
        notices = sorted(
            outbox.glob(f"{kind}-*.json"), key=lambda p: p.stat().st_mtime_ns
        )
        for path in reversed(notices):
            notice = json.loads(path.read_text(encoding="utf-8"))
            if notice["to"] == address.strip().lower():
                return {"code": notice["code"]}
        return {"code": ""}

    def bootstrap(body: dict[str, str] = Body(...)) -> dict[str, Any]:  # noqa: B008
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "afterworlds.remote.bootstrap",
                "--contact-address",
                body["contact_address"],
                "--control-db",
                control_url,
                "--password-stdin",
            ],
            input=body["password"] + "\n",
            capture_output=True,
            text=True,
            check=False,
        )
        return {"exit_code": result.returncode, "stdout": result.stdout.strip()}

    def entitlement(account_id: str) -> dict[str, str]:
        with app.state.session_factory() as s:
            service = EntitlementService(s)
            service.receive_entitlement_event(
                UUID(account_id),
                E.HOSTED_ACCESS_ACTIVATED,
                HostedAccessActivatedPayload(
                    plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
                ),
            )
            service.receive_entitlement_event(
                UUID(account_id),
                E.SUBSCRIPTION_CREDIT_GRANT,
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
            )
        return {"seeded": account_id}

    for route in (
        APIRoute("/__e2e__/outbox", latest_code, methods=["GET"]),
        APIRoute("/__e2e__/bootstrap", bootstrap, methods=["POST"]),
        APIRoute("/__e2e__/entitlement/{account_id}", entitlement, methods=["POST"]),
    ):
        app.router.routes.insert(0, route)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8004)
    args = parser.parse_args()

    work = Path(tempfile.mkdtemp(prefix="afterworlds-e2e-remote-"))
    os.environ.pop("AFTERWORLDS_CI", None)
    os.environ["AFTERWORLDS_FAKE_PROVIDER"] = "1"
    os.environ["AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"] = str(work / "chroma")
    app = build_app(work)

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
