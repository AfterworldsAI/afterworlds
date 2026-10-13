"""CRD Issue 15c end to end: the production app, the accepted G1 authority.

A disposable store is migrated with the app's own Alembic chain, the real 5c
source release is finalized into it, and the committed G1 oracle is published
through the real lifecycle. Isolated test setup only: no shared runtime store
is read or written, and nothing is published or activated outside ``tmp``.

Each test copies that store, starts ``create_app`` on the copy (fake provider:
no real model call) and submits turns through ``POST /turns``. Only the
GameMaster's adjudication proposals are scripted; Planner, Writer, Extractor,
Contradiction, the adjudication service, adapter, dice, delivery transaction
and audit are the production ones.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.api.fake_pipeline import FakeProviderAdapter
from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.payloads import (
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from afterworlds.ingestion.corpus.persistence import finalize_source_release
from afterworlds.ingestion.corpus.pipeline import CandidateRelease
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
from afterworlds.models.enums import DiceHandling, RpgPlayStatus
from afterworlds.persistence.crud.session_state import (
    get_rpg_session_state_by_story,
    update_rpg_session_state,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.services.dnd5e_state import service
from tests.services.dnd5e_state.builders import complete_character, real_index

NOW = "2026-10-11T00:00:00+00:00"
PACKAGE = UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2")
RELEASE = "5.2.1-corpus.8781d4e0-a3b"
CLIMB = "glossary.climbing/difficult_climb"


@pytest.fixture(scope="module")
def g1_store(
    tmp_path_factory: pytest.TempPathFactory, source_candidate: CandidateRelease
) -> Path:
    path = tmp_path_factory.mktemp("bounded-d20") / "store.db"
    upgrade_to_head(f"sqlite:///{path}")
    engine = create_engine(f"sqlite:///{path}")
    factory = create_session_factory(engine)
    chroma = build_isolated_test_chroma_client(tempfile.mkdtemp(prefix="15c-chroma-"))
    try:
        with factory() as session:
            finalized = finalize_source_release(
                session,
                source_candidate,
                now=NOW,
                chroma_client=chroma,
                retrieval_config=RetrievalMemoryConfig(),
                embedding_function=DeterministicFakeEmbeddingFunction(),
            )
            assert finalized.published, finalized.gate
        inputs = committed_inputs_for(str(PACKAGE), RELEASE)
        assert inputs is not None
        with factory() as session:
            identified = identify_projection(candidate_from_accepted_inputs(inputs))
            persist_draft(session, identified, now=NOW)
            record_persisted_state_digest(session, identified.projection_uuid)
            session.commit()
            published = publish_from_committed_oracle(
                session, identified.projection_uuid, now=NOW
            )
            assert published.outcome is PublicationOutcome.PUBLISHED
            session.commit()
    finally:
        engine.dispose()
    return path


#: Every provider request of the current test, in order.
REQUESTS: list[ProviderCallRequest] = []


def _request_text(pass_id: str) -> str:
    return "\n".join(
        block.text
        for request in REQUESTS
        if request.pass_id.value == pass_id
        for block in request.rendered_blocks
    )


@pytest.fixture()
def gm(monkeypatch: pytest.MonkeyPatch) -> list[list[dict[str, Any]]]:
    """The GameMaster's scripted proposals, one list per adjudication call."""
    script: list[list[dict[str, Any]]] = []
    real_call = FakeProviderAdapter.call
    REQUESTS.clear()

    def call(self: FakeProviderAdapter, request: ProviderCallRequest) -> Any:
        REQUESTS.append(request)
        if request.pass_id.value != "rpg_adjudication":
            return real_call(self, request)
        rolls = script.pop(0) if script else []
        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name="afterworlds-fake",
            model_identifier="afterworlds-fake:test-model",
            model_tier=real_call(self, request).model_tier,
            content_parts=[
                ProviderToolCallPart(
                    tool_name="produce_adjudication_proposals",
                    tool_input={"rolls": rolls},
                )
            ],
            latency_ms=1,
            input_token_count=100,
            output_token_count=50,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
        )

    monkeypatch.setattr(FakeProviderAdapter, "call", call)
    return script


@pytest.fixture()
def client(
    g1_store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    db = tmp_path / "store.db"
    shutil.copyfile(g1_store, db)
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    app = create_app(
        ApiSettings(database_url=f"sqlite:///{db}", frontend_dist_dir=tmp_path / "x")
    )
    with TestClient(app) as c:
        factory = c.app.state.session_factory
        with factory() as s:
            entitlements = EntitlementService(s)
            sojourner = c.app.state.sojourner_id
            entitlements.receive_entitlement_event(
                sojourner,
                EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
                HostedAccessActivatedPayload(
                    plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
                ),
            )
            entitlements.receive_entitlement_event(
                sojourner,
                EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
                SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
            )
            s.commit()
        yield c


def _rpg_story(
    client: TestClient,
    *,
    in_play: bool = True,
    dice: DiceHandling = DiceHandling.AI_ROLLS,
) -> str:
    resp = client.post(
        "/api/stories", json={"title": "15c", "mode": "rpg", "character_name": "Ilse"}
    )
    assert resp.status_code == 201, resp.text
    story_id = resp.json()["story_id"]
    if not in_play:
        return str(story_id)
    with client.app.state.session_factory() as s:
        state = get_rpg_session_state_by_story(s, UUID(story_id))
        assert state is not None
        service.create_character(
            s,
            state.character_sheet_id,
            PACKAGE,
            complete_character(real_index(), "classes.wizard", 3),
            now=NOW,
        )
        update_rpg_session_state(
            s,
            state.model_copy(
                update={
                    "play_status": RpgPlayStatus.IN_PLAY,
                    "dice_handling": dice,
                    "gm_cheating": False,
                }
            ),
        )
        s.commit()
    return str(story_id)


def _turn(client: TestClient, story_id: str, text: str) -> dict[str, Any]:
    resp = client.post(f"/api/stories/{story_id}/turns", json={"user_input": text})
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _roll(
    visibility: str = "shown",
    operation: str = "fixed_dc_check",
    identity: str | None = CLIMB,
) -> dict[str, Any]:
    return {
        "check_label": "Athletics Check",
        "subsystem_tag": "climb",
        "visibility": visibility,
        "operation": operation,
        "check_identity": identity,
    }


def _rows(client: TestClient, sql: str, **params: object) -> list[Any]:
    with client.app.state.session_factory() as s:
        return list(s.execute(sa.text(sql), params).all())


def _audit(client: TestClient, story_id: str) -> list[Any]:
    return _rows(
        client,
        "SELECT check_label, visibility, dc, outcome, total, modifiers_json,"
        " gm_cheating_at_roll, source FROM rpg_roll_audit WHERE story_id = :s",
        s=story_id,
    )


def _turns(client: TestClient) -> int:
    """Turns in this test's private store (it holds exactly one story)."""
    return len(_rows(client, "SELECT 1 FROM turns"))


def test_a_certified_check_resolves_and_commits_with_the_delivered_turn(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    gm.append([_roll()])
    body = _turn(client, story, "I climb the rain-slick wall.")
    assert body["disposition"] == "delivered", body
    (row,) = _audit(client, story)
    assert (row.dc, row.outcome in ("success", "failure")) == (15, True)
    provenance = json.loads(row.modifiers_json)
    assert provenance["check_identity"] == CLIMB
    assert provenance["certificate"]["projection_uuid"] == str(
        real_index().binding.mechanical_projection_uuid
    )
    assert provenance["visible_total"] == -1  # Str 8, no Athletics proficiency
    assert 1 <= row.total - provenance["visible_total"] <= 20  # one backend d20
    assert row.outcome == ("success" if row.total >= 15 else "failure")
    assert not row.gm_cheating_at_roll  # gm_cheating = off, snapshotted
    assert _turns(client) == 1


def test_a_hidden_check_is_audited_but_filtered_from_the_player(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    gm.append([_roll(visibility="hidden")])
    body = _turn(client, story, "I keep climbing.")
    assert body["disposition"] == "delivered", body
    (row,) = _audit(client, story)
    assert (row.visibility, row.source, row.dc) == ("hidden", "hidden", 15)
    assert "Athletics" not in json.dumps(body)
    assert CLIMB not in json.dumps(body)


@pytest.mark.parametrize(
    ("roll", "kind"),
    [
        (_roll(operation="saving_throw", identity=None), "unsupported_capability"),
        (_roll(identity="glossary.hide/hide_check"), "invalid_selection"),
        ({"check_label": "Stealth", "subsystem_tag": "stealth", "visibility": "shown"},
         "unsupported_capability"),
    ],
)  # fmt: skip
def test_a_refused_mechanic_fails_the_turn_visibly_and_leaves_nothing(
    client: TestClient,
    gm: list[list[dict[str, Any]]],
    roll: dict[str, Any],
    kind: str,
) -> None:
    story = _rpg_story(client)
    gm.append([_roll(), roll])  # a valid check first: nothing may survive
    body = _turn(client, story, "I attack.")
    assert body["disposition"] == "pipeline_error", body
    assert f"[{kind}]" in body["pipeline_error_summary"]
    assert _audit(client, story) == []
    assert _turns(client) == 0


def test_player_roll_configuration_refuses_before_any_pending_request(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    gm.append([_roll()])
    body = _turn(client, story, "I climb.")
    assert body["disposition"] == "pipeline_error", body
    assert "[player_roll_unsupported]" in body["pipeline_error_summary"]
    assert _rows(client, "SELECT 1 FROM pending_roll_requests") == []
    assert _audit(client, story) == []


def test_a_non_mechanical_in_play_turn_is_delivered_unchanged(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    gm.append([])
    body = _turn(client, story, "I ask the innkeeper about rumors.")
    assert body["disposition"] == "delivered", body
    assert _audit(client, story) == []


def test_a_setup_turn_never_reaches_adjudication(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client, in_play=False)
    gm.append([_roll(operation="weapon_attack", identity=None)])
    body = _turn(client, story, "I want to play a half-elf ranger.")
    assert body["disposition"] == "delivered", body
    assert gm == [[_roll(operation="weapon_attack", identity=None)]]  # never asked


# ---------------------------------------------------------------------------
# Weapon attacks: independent subjects, atomic delivery (CRD Issue 15c)
# ---------------------------------------------------------------------------


def _wolf_and_club(client: TestClient, story_id: str) -> tuple[str, str]:
    """A Wolf of the story (recorded monster treatment) and a Club the
    character wields, created through the 2b services."""
    from afterworlds.models.dnd5e_state import (
        CreatureState,
        DeathState,
        HitPoints,
        ZeroHitPointTreatment,
    )
    from afterworlds.services.dnd5e_state.holdings import (
        Holder,
        HolderKind,
        create_item,
    )

    with client.app.state.session_factory() as s:
        state = get_rpg_session_state_by_story(s, UUID(story_id))
        assert state is not None
        wolf = service.create_creature(
            s,
            UUID(story_id),
            "Wolf",
            PACKAGE,
            CreatureState(
                template_record_key="animals.wolf",
                hit_points=HitPoints(current=11, maximum=11, temporary=0),
                conditions=(),
                active_effects=(),
                death_state=DeathState(
                    successes=0, failures=0, stable=False, dead=False
                ),
                zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster"),
            ),
            now=NOW,
        )
        club = create_item(
            s,
            real_index(),
            Holder(HolderKind.CHARACTER, state.character_sheet_id),
            "equipment.weapons.club",
            equipped=True,
            now=NOW,
        )
        s.commit()
        return str(wolf.creature_id), str(club.item_id)


def _attack(target: str, weapon: str, kind: str = "creature") -> dict[str, Any]:
    return {
        "check_label": "Club attack",
        "subsystem_tag": "attack",
        "visibility": "shown",
        "operation": "weapon_attack",
        "weapon_attack": {
            "weapon_item_id": weapon,
            "target": {"kind": kind, "subject_id": target},
            "range": "within_reach",
            "cover": "none",
            "attacker_light": "bright",
            "target_light": "bright",
        },
    }


def _creature_row(client: TestClient, creature_id: str) -> Any:
    (row,) = _rows(
        client,
        "SELECT revision, document FROM dnd5e_creatures WHERE creature_id = :c",
        c=creature_id,
    )
    return row


def test_a_weapon_attack_commits_the_targets_damage_with_the_delivered_turn(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    wolf, club = _wolf_and_club(client, story)
    gm.append([_attack(wolf, club)])
    body = _turn(client, story, "I swing my club at the wolf.")
    assert body["disposition"] == "delivered", body
    (row,) = _audit(client, story)
    provenance = json.loads(row.modifiers_json)
    assert (provenance["operation"], row.dc) == ("weapon_attack", 12)
    assert provenance["certificate"]["projection_uuid"] == str(
        real_index().binding.mechanical_projection_uuid
    )
    creature = _creature_row(client, wolf)
    document = (
        creature.document
        if isinstance(creature.document, dict)
        else json.loads(creature.document)
    )
    if row.outcome == "failure":
        assert creature.revision == 1
        assert document["hit_points"]["current"] == 11
    else:
        damage = provenance["damage"]
        assert creature.revision == 2
        assert document["hit_points"]["current"] == max(0, 11 - damage["taken"])
    assert "12" not in json.dumps(body.get("adjudication", ""))
    assert _turns(client) == 1


def test_a_hits_subject_addressed_effects_are_audited_and_committed(
    client: TestClient,
    gm: list[list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A certain hit: the target's effects carry its subject id, and the audit
    row and the target's state commit with the delivered Turn."""
    from afterworlds.models.rpg import DiceResult
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

    def roll(self: object, expression: str) -> DiceResult:
        face = 15 if "d20" in expression else 3
        return DiceResult(expression=expression, raw_rolls=(face,), chosen=face)

    monkeypatch.setattr(SystemRandomDiceService, "roll", roll)
    story = _rpg_story(client)
    wolf, club = _wolf_and_club(client, story)
    gm.append([_attack(wolf, club)])
    body = _turn(client, story, "I swing my club at the wolf.")
    assert body["disposition"] == "delivered", body
    (row,) = _rows(
        client,
        "SELECT sheet_effects_json FROM rpg_roll_audit WHERE story_id = :s",
        s=story,
    )
    (effect,) = json.loads(row.sheet_effects_json)
    assert (effect["subject_kind"], effect["subject_id"]) == ("creature", wolf)
    # The production GameMaster was shown the ids it named; the Writer was not.
    scene = _request_text("rpg_adjudication")
    assert wolf in scene and club in scene and "Bite" in scene
    assert wolf not in _request_text("writer")
    assert _creature_row(client, wolf).revision == 2


def test_a_target_from_another_story_refuses_and_leaves_nothing(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    other = _rpg_story(client)
    wolf, _ = _wolf_and_club(client, other)
    _, club = _wolf_and_club(client, story)
    gm.append([_attack(wolf, club)])
    body = _turn(client, story, "I swing at the wolf from the other tale.")
    assert body["disposition"] != "delivered", body
    assert _audit(client, story) == []
    assert _creature_row(client, wolf).revision == 1


# ---------------------------------------------------------------------------
# Actor-turn edges (contract G1), committed with the delivered Turn
# ---------------------------------------------------------------------------


def _edge_roll(operation: str, subject: str, kind: str = "creature") -> dict[str, Any]:
    return {
        "check_label": operation,
        "subsystem_tag": "turn",
        "visibility": "shown",
        "operation": operation,
        "subject": {"kind": kind, "subject_id": subject},
    }


def _edges(client: TestClient, story_id: str) -> list[Any]:
    return _rows(
        client,
        "SELECT sequence, kind, subject_id, turn_instance FROM rpg_turn_edges"
        " WHERE story_id = :s ORDER BY sequence",
        s=story_id,
    )


def test_actor_turn_edges_commit_with_the_delivered_turn(
    client: TestClient, gm: list[list[dict[str, Any]]]
) -> None:
    story = _rpg_story(client)
    wolf, club = _wolf_and_club(client, story)
    gm.append([_edge_roll("begin_turn", wolf), _attack(wolf, club)])
    assert _turn(client, story, "The wolf's turn; I strike.")["disposition"] == (
        "delivered"
    )
    assert [tuple(r) for r in _edges(client, story)] == [(1, "begin", wolf, 1)]
    (coordination,) = _rows(
        client,
        "SELECT revision, document FROM rpg_turn_coordination WHERE story_id = :s",
        s=story,
    )
    document = coordination.document
    if not isinstance(document, dict):
        document = json.loads(document)
    assert coordination.revision == 1
    assert document["active"]["subject"]["subject_id"] == wolf

    # Beginning another turn while the wolf's is active refuses, leaving the
    # coordination, the edge log and the turn count as they were.
    gm.append([_edge_roll("begin_turn", wolf)])
    body = _turn(client, story, "The wolf goes again.")
    assert body["disposition"] != "delivered", body
    assert len(_edges(client, story)) == 1 and _turns(client) == 1

    gm.append([_edge_roll("end_turn", wolf)])
    assert _turn(client, story, "The wolf's turn ends.")["disposition"] == ("delivered")
    assert [tuple(r) for r in _edges(client, story)][-1] == (2, "end", wolf, 1)
