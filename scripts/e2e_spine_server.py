#!/usr/bin/env python
"""E2E only -- the built app for the CRD Issue 21 narrative-spine proof.

Serves ``create_app`` with the PRODUCTION provider resolver, readiness and
binding (``AFTERWORLDS_FAKE_PROVIDER`` unset, a synthetic hosted key), on a
disposable copy of the published-release store, with ``frontend/dist``.
Replaced, and only these:

* the provider HTTP transport -- ``scripts/scripted_provider.py`` answers the
  real Anthropic/OpenAI SDK clients in each provider's wire format;
* credential storage -- the production keychain store over the in-memory
  keyring of ``scripts/e2e_memory_keyring.py`` (the launcher refuses to serve
  otherwise).

Test-only routes (inserted ahead of the frontend mount, never in
``create_app``):

* ``POST /__e2e__/access/{hosted|byok}`` seeds entitlement events through
  Issue 13's ``receive_entitlement_event`` (the BYOK key itself is entered in
  the built app's Account panel);
* ``POST /__e2e__/provider/{pass_name}`` queues one scripted reply
  (``{"text"|"tool_input"|"refusal"|"status": ...}``);
* ``GET /__e2e__/provider/calls`` lists recorded calls: pass, path kind
  (hosted/byok, from the key the binding sent) and rendered texts;
* ``GET /__e2e__/stories/{story_id}/summaries`` and ``GET /__e2e__/deductions``
  read the persisted Rolling Summary rows and hosted credit deductions;
* ``GET /__e2e__/fixtures/character`` returns a complete character in the
  existing schema for a test to queue as the scripted GM's reading of a
  pasted completed sheet. GM-led creation never uses it: the scripted GM
  composes from the conversation (``scripts/e2e_gm_led.py``). RPG stories
  start through the product's setup sequence (ADR-015c); nothing seeds
  character state or forces play.

Usage (repository root, ``src`` and the root on ``PYTHONPATH``)::

    python scripts/e2e_spine_server.py --port 8003

``CRD21_G1_STORE`` may name an already built published-release store to copy
(local iteration only); otherwise it is built fresh (minutes).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-10-16T00:00:00+00:00"


def build_app(work: Path, provider: Any) -> Any:
    import sqlalchemy as sa
    from fastapi import FastAPI
    from fastapi.routing import APIRoute

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
    from afterworlds.persistence.orm.rolling_summary import RollingSummaryORM
    from scripts.scripted_provider import SYNTHETIC_HOSTED_KEY, Reply
    from tests.services.dnd5e_state.builders import complete_character, real_index

    real = real_index()  # built once here, not inside a timed request
    from scripts.e2e_gm_led import responder as gm_led_responder

    # GM-led creation composes only from what the Sojourner said (PR #204).
    provider.responders["rpg_setup_writer"] = gm_led_responder(real)
    app: FastAPI = create_app(
        ApiSettings(
            database_url=f"sqlite:///{work / 'store.db'}",
            frontend_dist_dir=REPO_ROOT / "frontend" / "dist",
        )
    )
    factory = app.state.session_factory
    sojourner = app.state.sojourner_id

    def access(path: str) -> dict[str, str]:
        with factory() as s:
            entitlements = EntitlementService(s)
            if path == "hosted":
                entitlements.receive_entitlement_event(
                    sojourner,
                    EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
                    HostedAccessActivatedPayload(
                        plan=HostedAccessPlan.SUBSCRIPTION,
                        effective_at=datetime.now(UTC),
                    ),
                )
                entitlements.receive_entitlement_event(
                    sojourner,
                    EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
                    SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
                )
            elif path == "byok":
                entitlements.receive_entitlement_event(
                    sojourner,
                    EntitlementEventType.BYOK_LICENSE_ACTIVATED,
                    ByokLicenseActivatedPayload(purchased_at=datetime.now(UTC)),
                )
            else:
                raise ValueError(f"unknown access path {path!r}")
        return {"seeded": path}

    def push(pass_name: str, reply: dict[str, Any]) -> dict[str, str]:
        provider.push(pass_name, Reply(**reply))
        return {"queued": pass_name}

    def calls() -> list[dict[str, Any]]:
        return [
            {
                "pass_name": c.pass_name,
                "path": "hosted" if c.api_key == SYNTHETIC_HOSTED_KEY else "byok",
                "texts": c.texts,
            }
            for c in provider.calls
        ]

    def summaries(story_id: UUID) -> list[dict[str, Any]]:
        with factory() as s:
            rows = s.scalars(
                sa.select(RollingSummaryORM)
                .where(RollingSummaryORM.story_id == str(story_id))
                .order_by(RollingSummaryORM.version_number)
            ).all()
            return [
                {
                    "version_number": r.version_number,
                    "is_current": r.is_current,
                    "text": r.text,
                    "compressed_from_turn_id": r.compressed_from_turn_id,
                    "compressed_through_turn_id": r.compressed_through_turn_id,
                }
                for r in rows
            ]

    def deductions() -> dict[str, str]:
        with factory() as s:
            rows = s.scalars(
                sa.select(EntitlementEvent).where(
                    EntitlementEvent.event_type
                    == EntitlementEventType.CREDIT_DEDUCTION.value
                )
            ).all()
            out: dict[str, str] = {}
            for r in rows:
                payload = json.loads(r.payload_json)
                total = abs(Decimal(str(payload["hosted_credit_delta"]))) + abs(
                    Decimal(str(payload["top_up_credit_delta"]))
                )
                out[str(r.turn_id)] = str(total)
            return out

    def accepted_character(story_id: UUID) -> dict[str, Any]:
        """The accepted, stored character and its binding, read through the
        character store, beside the candidate the Sojourner reviewed (test
        seam, PR #204): the browser proof checks what persisted."""
        from afterworlds.models.dnd5e_state import Dnd5eCharacterState
        from afterworlds.services import rpg_setup
        from afterworlds.services.dnd5e_state import store as character_store

        with factory() as s:
            state = rpg_setup._state(s, story_id)
            stored = character_store.get_character(s, state.character_sheet_id)
            setup = rpg_setup.load_setup(s, rpg_setup.anchor_node_id(s, story_id))
            if stored is None or setup.candidate is None:
                return {"accepted": False}
            return {
                "accepted": True,
                "state": stored.state.model_dump(mode="json"),
                "binding": stored.binding.model_dump(mode="json"),
                "selected_package_uuid": str(setup.selected_package_uuid),
                "equals_reviewed_candidate": stored.state
                == Dnd5eCharacterState.model_validate(setup.candidate.proposal),
                "binding_is_reviewed_binding": stored.binding.model_dump(mode="json")
                == setup.candidate.binding,
            }

    def character_fixture() -> dict[str, Any]:
        """A complete character in the existing schema: the scripted model's
        proposal for a setup turn (transport data). Code still validates and
        binds it through the product's Accept character operation."""
        return complete_character(real, "classes.wizard", 1).model_dump(mode="json")

    # Ahead of the frontend's StaticFiles mount at "/", which matches every
    # path it is offered.
    for route in (
        APIRoute("/__e2e__/access/{path}", access, methods=["POST"]),
        APIRoute("/__e2e__/provider/{pass_name}", push, methods=["POST"]),
        APIRoute("/__e2e__/provider/calls", calls, methods=["GET"]),
        APIRoute("/__e2e__/stories/{story_id}/summaries", summaries, methods=["GET"]),
        APIRoute("/__e2e__/deductions", deductions, methods=["GET"]),
        APIRoute("/__e2e__/fixtures/character", character_fixture, methods=["GET"]),
        APIRoute(
            "/__e2e__/stories/{story_id}/character", accepted_character, methods=["GET"]
        ),
    ):
        app.router.routes.insert(0, route)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()

    from scripts.e2e_memory_keyring import MemoryKeyring
    from scripts.e2e_memory_keyring import install as install_keyring
    from scripts.e2e_rpg_server import build_store
    from scripts.scripted_provider import SYNTHETIC_HOSTED_KEY, ScriptedProvider

    work = Path(tempfile.mkdtemp(prefix="afterworlds-e2e-spine-"))
    for name in ("AFTERWORLDS_FAKE_PROVIDER", "AFTERWORLDS_CI", "OPENROUTER_API_KEY"):
        os.environ.pop(name, None)
    os.environ["ANTHROPIC_API_KEY"] = SYNTHETIC_HOSTED_KEY
    os.environ["AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"] = str(work / "chroma")
    cached = os.environ.get("CRD21_G1_STORE")
    if cached:
        shutil.copyfile(cached, work / "store.db")
    else:
        build_store(work / "store.db")
    print(f"e2e spine store ready at {work}", flush=True)

    install_keyring()
    provider = ScriptedProvider().install()
    app = build_app(work, provider)

    import keyring

    if not isinstance(keyring.get_keyring(), MemoryKeyring):
        raise SystemExit("refusing to serve: the in-memory keyring is not active")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
