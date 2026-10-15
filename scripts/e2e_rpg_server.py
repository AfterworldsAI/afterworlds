#!/usr/bin/env python
"""E2E only -- the built app on a published-release store, for CRD Issue 19b.

The minimal spine's server (``playwright.config.ts``) has no published rules
authority, and the fake provider's GameMaster proposes no roll, so no RPG
pending interaction is reachable there. This launcher builds what the backend
product proofs use (``tests/ingestion/mechanical``): a disposable store
migrated with the app's own Alembic chain, the real source release finalized
into it and the committed G1 oracle published -- all inside a fresh temp
directory; nothing shared is read or written. It then serves ``create_app``
on that store with ``AFTERWORLDS_FAKE_PROVIDER=1`` and ``frontend/dist``.

Only test fixtures are added, never to ``create_app``:

* the GameMaster's adjudication proposals come from a FIFO that
  ``POST /__e2e__/rpg/{story_id}/{scenario}`` fills (Playwright runs one
  worker, so the next adjudication call is that story's announce);
* that route also seeds the story's character, ``IN_PLAY`` with player-rolled
  dice, creatures, items and hosted entitlement -- the DB-level setup the
  backend product tests perform;
* the Owner-adopted S1 contest supplement is applied in memory only, as in
  ``tests/ingestion/mechanical/sequence_stack.py::s1``.

Planner, Writer, Extractor, Contradiction, adjudication, dice, the action
sequence service, routes, locks and settlement are the production ones.

Usage (from the repository root, ``src`` and the root on ``PYTHONPATH``)::

    python scripts/e2e_rpg_server.py --port 8001
"""

from __future__ import annotations

import argparse
import os
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-10-15T00:00:00+00:00"
PACKAGE = UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2")
RELEASE = "5.2.1-corpus.8781d4e0-a3b"


def build_store(path: Path) -> None:
    """The published-release store of ``g1_store``, built into *path*."""
    from afterworlds.api.db_bootstrap import upgrade_to_head
    from afterworlds.ingestion.corpus.persistence import finalize_source_release
    from afterworlds.ingestion.corpus.pipeline import build_source_candidate
    from afterworlds.ingestion.mechanical.oracle import (
        candidate_from_accepted_inputs,
        committed_inputs_for,
    )
    from afterworlds.ingestion.mechanical.persistence import (
        persist_draft,
        record_persisted_state_digest,
    )
    from afterworlds.ingestion.mechanical.projection import identify_projection
    from afterworlds.ingestion.mechanical.publication import (
        PublicationOutcome,
        publish_from_committed_oracle,
    )
    from afterworlds.persistence.database import create_engine, create_session_factory
    from afterworlds.pipeline.retrieval.client import (
        build_isolated_test_chroma_client,
    )
    from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
    from afterworlds.pipeline.retrieval.embedding import (
        DeterministicFakeEmbeddingFunction,
    )

    url = f"sqlite:///{path}"
    upgrade_to_head(url)
    candidate = build_source_candidate(
        REPO_ROOT, retrieval_config=RetrievalMemoryConfig()
    )
    engine = create_engine(url)
    factory = create_session_factory(engine)
    chroma = build_isolated_test_chroma_client(str(path.parent / "corpus-chroma"))
    try:
        with factory() as session:
            finalized = finalize_source_release(
                session,
                candidate,
                now=NOW,
                chroma_client=chroma,
                retrieval_config=RetrievalMemoryConfig(),
                embedding_function=DeterministicFakeEmbeddingFunction(),
            )
            if not finalized.published:
                raise RuntimeError(f"source release not published: {finalized.gate}")
        inputs = committed_inputs_for(str(PACKAGE), RELEASE)
        if inputs is None:
            raise RuntimeError("committed G1 oracle inputs not found")
        with factory() as session:
            identified = identify_projection(candidate_from_accepted_inputs(inputs))
            persist_draft(session, identified, now=NOW)
            record_persisted_state_digest(session, identified.projection_uuid)
            session.commit()
            published = publish_from_committed_oracle(
                session, identified.projection_uuid, now=NOW
            )
            if published.outcome is not PublicationOutcome.PUBLISHED:
                raise RuntimeError(f"G1 oracle not published: {published}")
            session.commit()
    finally:
        engine.dispose()


def apply_s1() -> Any:
    """``sequence_stack.s1`` without pytest: S1 answers its one binding."""
    from afterworlds.services.dnd5e_state import holdings, service, turn
    from tests.services.dnd5e_state.builders import s1_index

    index = s1_index()
    real_index_of = service.authority_index  # type: ignore[attr-defined]
    real_current = service.require_current  # type: ignore[attr-defined]

    def index_of(session: Any, binding: Any, **kw: Any) -> Any:
        if binding == index.binding:
            return index
        return real_index_of(session, binding, **kw)

    def current(session: Any, binding: Any, **kw: Any) -> Any:
        if binding != index.binding:
            real_current(session, binding, **kw)

    for module in (service, turn, holdings):
        setattr(module, "authority_index", index_of)  # noqa: B010
    for module in (service, holdings):
        setattr(module, "require_current", current)  # noqa: B010
    return index


#: The GameMaster's scripted proposals, one list per adjudication call.
GM: list[list[dict[str, Any]]] = []


def script_gamemaster() -> None:
    from afterworlds.api.fake_pipeline import FakeProviderAdapter
    from afterworlds.pipeline.provider._models import (
        ProviderCallRequest,
        ProviderToolCallPart,
    )

    real_call = FakeProviderAdapter.call

    def call(self: FakeProviderAdapter, request: ProviderCallRequest) -> Any:
        result = real_call(self, request)
        if request.pass_id.value != "rpg_adjudication":
            return result
        rolls = GM.pop(0) if GM else []
        part = ProviderToolCallPart(
            tool_name="produce_adjudication_proposals", tool_input={"rolls": rolls}
        )
        return result.model_copy(update={"content_parts": [part]})

    FakeProviderAdapter.call = call  # type: ignore[method-assign]


def build_app(work: Path) -> Any:
    from fastapi import FastAPI
    from fastapi.routing import APIRoute

    from afterworlds.api.app import create_app
    from afterworlds.api.config import ApiSettings
    from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        HostedAccessActivatedPayload,
        SubscriptionCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService
    from afterworlds.models.dnd5e_state import (
        CreatureState,
        DeathState,
        HitPoints,
        ZeroHitPointTreatment,
    )
    from afterworlds.models.enums import DiceHandling, RpgPlayStatus
    from afterworlds.persistence.crud.session_state import (
        get_rpg_session_state_by_story,
        update_rpg_session_state,
    )
    from afterworlds.services.dnd5e_state import service, store
    from afterworlds.services.dnd5e_state.holdings import (
        Holder,
        HolderKind,
        create_item,
    )
    from tests.services.dnd5e_state.builders import complete_character, real_index

    s1 = apply_s1()
    real = real_index()  # built once here, not inside a timed request
    script_gamemaster()
    app: FastAPI = create_app(
        ApiSettings(
            database_url=f"sqlite:///{work / 'store.db'}",
            frontend_dist_dir=REPO_ROOT / "frontend" / "dist",
        )
    )
    factory = app.state.session_factory

    with factory() as s:
        entitlements = EntitlementService(s)
        entitlements.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        entitlements.receive_entitlement_event(
            app.state.sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("100000")),
        )
        s.commit()

    def creature(record: str, hp: int) -> CreatureState:
        return CreatureState(
            template_record_key=record,
            hit_points=HitPoints(current=hp, maximum=hp, temporary=0),
            conditions=(),
            active_effects=(),
            death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
            zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster"),
        )

    def seed(story_id: UUID, scenario: str) -> dict[str, str]:
        contest = scenario == "contest"
        index = s1 if contest else real
        with factory() as s:
            state = get_rpg_session_state_by_story(s, story_id)
            if state is None:
                raise ValueError("not an RPG story")
            sheet = state.character_sheet_id
            character = complete_character(index, "classes.wizard", 3)
            if contest:
                store.create_character_state(s, sheet, character, s1.binding, now=NOW)
            else:
                service.create_character(s, sheet, PACKAGE, character, now=NOW)
            update_rpg_session_state(
                s,
                state.model_copy(
                    update={
                        "play_status": RpgPlayStatus.IN_PLAY,
                        "dice_handling": DiceHandling.PLAYER_ROLLS,
                        "gm_cheating": False,
                    }
                ),
            )
            character_ref = {"kind": "character", "subject_id": str(sheet)}
            if contest:
                ape = store.create_creature(
                    s, story_id, "Ape", creature("animals.ape", 19), s1.binding, now=NOW
                )
                side = {"ability": "strength", "skill": "athletics"}
                proposals = [
                    {
                        "check_label": "Arm wrestling",
                        "subsystem_tag": "contest",
                        "visibility": "shown",
                        "operation": "contest",
                        "contest": {
                            "initiator": {"subject": character_ref, **side},
                            "resister": {
                                "subject": {
                                    "kind": "creature",
                                    "subject_id": str(ape.creature_id),
                                },
                                **side,
                                "roll_hidden": True,
                            },
                            "stakes": "the ring on the table",
                            "counterpart_perceived": True,
                        },
                    }
                ]
            else:
                # A Dagger attack on a 4-HP wolf: the finesse adjustment, the
                # attack, the damage and the stored knockout decision.
                wolf = service.create_creature(
                    s, story_id, "Wolf", PACKAGE, creature("animals.wolf", 4), now=NOW
                )
                dagger = create_item(
                    s,
                    index,
                    Holder(HolderKind.CHARACTER, sheet),
                    "equipment.weapons.dagger",
                    now=NOW,
                    equipped=True,
                )
                proposals = [
                    {
                        "check_label": "Turn",
                        "subsystem_tag": "turn",
                        "visibility": "shown",
                        "operation": "begin_turn",
                        "subject": character_ref,
                    },
                    {
                        "check_label": "Dagger attack",
                        "subsystem_tag": "attack",
                        "visibility": "shown",
                        "operation": "weapon_attack",
                        "weapon_attack": {
                            "weapon_item_id": str(dagger.item_id),
                            "target": {
                                "kind": "creature",
                                "subject_id": str(wolf.creature_id),
                            },
                            "range": "within_reach",
                            "cover": "none",
                            "attacker_light": "bright",
                            "target_light": "bright",
                            "hands": {
                                "held": [{"item_id": str(dagger.item_id), "hands": 1}],
                                "free_hands": 1,
                            },
                            "ability": "strength",
                        },
                    },
                ]
            s.commit()
        # Only the newest story's action is queued: a seeded story that
        # never announced (a failed test) leaves nothing for the next one.
        GM[:] = [proposals]
        return {"story_id": str(story_id)}

    def seed_route(story_id: UUID, scenario: str) -> dict[str, str]:
        if scenario not in ("dagger", "contest"):
            raise ValueError(f"unknown scenario {scenario!r}")
        return seed(story_id, scenario)

    # Ahead of the frontend's StaticFiles mount at "/", which matches every
    # path it is offered.
    app.router.routes.insert(
        0,
        APIRoute("/__e2e__/rpg/{story_id}/{scenario}", seed_route, methods=["POST"]),
    )
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()

    work = Path(tempfile.mkdtemp(prefix="afterworlds-e2e-rpg-"))
    os.environ["AFTERWORLDS_FAKE_PROVIDER"] = "1"
    os.environ["AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY"] = str(work / "chroma")
    build_store(work / "store.db")
    print(f"e2e RPG store ready at {work}", flush=True)
    if args.build_only:
        return 0

    import uvicorn

    uvicorn.run(build_app(work), host="127.0.0.1", port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
