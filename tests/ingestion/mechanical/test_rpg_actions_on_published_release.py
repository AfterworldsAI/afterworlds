"""CRD Issue 15b Phase 3: the action-resolution lifecycle through the product.

``create_app`` on a private copy of the published-release store
(``g1_store``), the fake provider (no real model call) and an entitled
Sojourner (the 15c ``client`` fixture). Only the GameMaster's adjudication
proposals, and where a test says so the backend dice or a failure, are
scripted. Every roll, adjustment, decision and resume goes through HTTP, and
every reload through ``GET .../rpg/pending-interaction``.

These prove reachability, the routes' contract and the end-to-end shape. What
the routes do not change (validation rules, event shapes and atomicity, the
audit projection, contest arithmetic, races under the service) stays proven by
the Phase 2 backend suites (``test_action_resolution_lifecycle`` and siblings).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from afterworlds.api.fake_pipeline import FakeProviderAdapter
from afterworlds.entitlement.enums import (
    EntitlementEventType,
    HostedAccessDeactivationReason,
)
from afterworlds.entitlement.payloads import HostedAccessDeactivatedPayload
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
from afterworlds.pipeline.provider import ByokCredentialReadinessProvider
from afterworlds.services.dnd5e_state import service, store
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, create_item
from tests.ingestion.mechanical.sequence_stack import s1, scripted_dice
from tests.ingestion.mechanical.test_action_resolution_on_published_release import (
    _keys,
)
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    NOW,
    PACKAGE,
    REQUESTS,
    _rows,
    _rpg_story,
    client,
    g1_store,
    gm,
)
from tests.services.dnd5e_state.builders import complete_character, real_index

__all__ = ["client", "g1_store", "gm"]  # fixtures used by pytest

GM = list[list[dict[str, Any]]]

#: Keys of the stored authority and backend references: none may reach a
#: player response (15b-17).
BACKEND_ONLY = {
    "dc",
    "roller",
    "natural_outcomes",
    "critical_on_success",
    "contest",
    "counterpart",
    "counterpart_instruction",
    "certificate",
    "operation_index",
    "die_index",
    "step_id",
    "source_rule_refs",
    "source_rule_ref",
    "modifier_components",
    "visibility",
    "source_kind",
    "source_reference",
    "ability_id",
    "provisional_effects_json",
    "decision_snapshot",
    "instruction_snapshot",
    "total",
    "outcome",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sheet(client: TestClient, story: str) -> str:
    with client.app.state.session_factory() as s:
        state = get_rpg_session_state_by_story(s, UUID(story))
        assert state is not None
        return str(state.character_sheet_id)


def _wolf(client: TestClient, story: str, hp: int) -> str:
    state = CreatureState(
        template_record_key="animals.wolf",
        hit_points=HitPoints(current=hp, maximum=hp, temporary=0),
        conditions=(),
        active_effects=(),
        death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
        zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster"),
    )
    with client.app.state.session_factory() as s:
        created = service.create_creature(
            s, UUID(story), "Wolf", PACKAGE, state, now=NOW
        )
        s.commit()
        return str(created.creature_id)


def _item(client: TestClient, story: str, record: str) -> str:
    with client.app.state.session_factory() as s:
        made = create_item(
            s,
            real_index(),
            Holder(HolderKind.CHARACTER, UUID(_sheet(client, story))),
            record,
            now=NOW,
            equipped=True,
        )
        s.commit()
        return str(made.item_id)


def _begin(client: TestClient, story: str) -> dict[str, Any]:
    return {
        "check_label": "Turn",
        "subsystem_tag": "turn",
        "visibility": "shown",
        "operation": "begin_turn",
        "subject": {"kind": "character", "subject_id": _sheet(client, story)},
    }


def _attack(
    client: TestClient, story: str, wolf: str, record: str, label: str, **extra: Any
) -> dict[str, Any]:
    weapon = _item(client, story, record)
    return {
        "check_label": label,
        "subsystem_tag": "attack",
        "visibility": "shown",
        "operation": "weapon_attack",
        "weapon_attack": {
            "weapon_item_id": weapon,
            "target": {"kind": "creature", "subject_id": wolf},
            "range": "within_reach",
            "cover": "none",
            "attacker_light": "bright",
            "target_light": "bright",
            "hands": {"held": [{"item_id": weapon, "hands": 1}], "free_hands": 1},
            **extra,
        },
    }


def _post(client: TestClient, path: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(path, json=body) if body is not None else client.post(path)


def _pending(client: TestClient, story: str) -> Any:
    resp = client.get(f"/api/stories/{story}/rpg/pending-interaction")
    assert resp.status_code == 200, resp.text
    return resp.json()["interaction"]


def _turn_raw(client: TestClient, story: str, text: str) -> Any:
    return client.post(f"/api/stories/{story}/turns", json={"user_input": text})


def _turn(client: TestClient, story: str, text: str) -> dict[str, Any]:
    resp = client.post(f"/api/stories/{story}/turns", json={"user_input": text})
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _roll(
    client: TestClient,
    story: str,
    view: dict[str, Any],
    *values: Any,
    revision: Any = None,
) -> Any:
    (term,) = view["terms"]
    return _post(
        client,
        f"/api/stories/{story}/rpg/rolls",
        {
            "source": "inline_ui",
            "pending_roll_request_id": view["pending_roll_request_id"],
            "expected_instruction_revision": (
                view["instruction_revision"] if revision is None else revision
            ),
            "term_results": [{"term_id": term["term_id"], "values": list(values)}],
        },
    )


def _advanced(resp: Any) -> dict[str, Any]:
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    return body


def _refused(resp: Any, status: int, code: str) -> None:
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["error_code"] == code, body
    assert set(body) == {"error_code", "message", "detail", "schema_version"}


def _resume(client: TestClient, story: str, sequence: str) -> Any:
    return client.post(f"/api/stories/{story}/rpg/sequences/{sequence}/resume")


def _writer_views(request: Any) -> list[dict[str, Any]]:
    """The ``rpg_adjudication`` pass-forward a Writer request carries: the
    visibility-filtered ``WriterAdjudicationView`` records, parsed."""
    text = "\n".join(
        block.text for block in (*request.system_blocks, *request.rendered_blocks)
    )
    start = text.index('{"pending_player_roll_instruction"')
    data, _ = json.JSONDecoder().raw_decode(text, start)
    views: list[dict[str, Any]] = data["views"]
    return views


def _count(pass_id: str) -> int:
    return len([r for r in REQUESTS if r.pass_id.value == pass_id])


def _state(client: TestClient, story: str) -> tuple[Any, ...]:
    """Everything an intermediate operation or a narration may change."""
    return (
        tuple(
            tuple(r)
            for r in _rows(
                client,
                "SELECT status, revision, current_interaction_kind,"
                " current_pending_roll_request_id, current_decision_request_id"
                " FROM action_resolution_sequences WHERE story_id = :s",
                s=story,
            )
        ),
        tuple(
            tuple(r)
            for r in _rows(
                client,
                "SELECT request_id, status, instruction_revision"
                " FROM pending_roll_requests WHERE story_id = :s ORDER BY request_id",
                s=story,
            )
        ),
        len(
            _rows(
                client,
                "SELECT 1 FROM action_resolution_events WHERE story_id = :s",
                s=story,
            )
        ),
        len(_rows(client, "SELECT 1 FROM rpg_roll_audit WHERE story_id = :s", s=story)),
        len(_rows(client, "SELECT 1 FROM turns")),
        len(_rows(client, "SELECT 1 FROM entitlement_event")),
    )


def _hp(client: TestClient, wolf: str) -> tuple[int, int, set[str]]:
    (row,) = _rows(
        client,
        "SELECT revision, document FROM dnd5e_creatures WHERE creature_id = :c",
        c=wolf,
    )
    doc = row.document if isinstance(row.document, dict) else json.loads(row.document)
    return (
        int(row.revision),
        int(doc["hit_points"]["current"]),
        {c["condition"] for c in doc["conditions"]},
    )


def _balance(client: TestClient) -> Any:
    with client.app.state.session_factory() as s:
        status = EntitlementService(s).get_access_path_status(
            client.app.state.sojourner_id
        )
        return status.total_hosted_credit_balance


def _audit(client: TestClient, story: str) -> list[tuple[Any, ...]]:
    return [
        tuple(r)
        for r in _rows(
            client,
            "SELECT check_label, source, total, outcome, submission_source,"
            " turn_id FROM rpg_roll_audit WHERE story_id = :s ORDER BY global_sequence",
            s=story,
        )
    ]


@pytest.fixture()
def readiness_calls(monkeypatch: pytest.MonkeyPatch) -> list[UUID]:
    """Every BYOK readiness probe: the access-path selection's input."""
    calls: list[UUID] = []
    real = ByokCredentialReadinessProvider.is_byok_runnable

    def probe(self: Any, sojourner_id: UUID) -> bool:
        calls.append(sojourner_id)
        return real(self, sojourner_id)

    monkeypatch.setattr(ByokCredentialReadinessProvider, "is_byok_runnable", probe)
    return calls


@pytest.fixture()
def no_backend_dice(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    def faces(expression: str) -> tuple[int, ...]:
        raise AssertionError(f"the backend rolled {expression}")

    return scripted_dice(monkeypatch, faces)


# ---------------------------------------------------------------------------
# A linked multi-step action: adjustment, two dice, a decision, one narration
# ---------------------------------------------------------------------------


def test_a_linked_action_with_an_adjustment_and_a_decision_is_narrated_once(
    client: TestClient,
    gm: GM,
    readiness_calls: list[UUID],
    no_backend_dice: list[str],
) -> None:
    """A finesse Dagger attack on a 4-HP wolf in a player-rolled story:
    the Sojourner switches the attack to Dexterity, rolls the attack and the
    damage, and the drop to 0 HP raises the stored knockout decision. Every
    step is reloaded. Between the announce and the resume nothing calls a
    provider, selects an access path, settles, writes a Turn or an audit row,
    or touches the live wolf. The resume narrates the whole action with one
    Writer call, applies every effect and audit with its Turn, and settles it
    once; a repeat is the success-equivalent already-completed contract."""
    story = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    wolf = _wolf(client, story, hp=4)
    dagger = _attack(client, story, wolf, "equipment.weapons.dagger", "Dagger attack")
    dagger["weapon_attack"]["ability"] = "strength"
    gm.append([_begin(client, story), dagger])
    assert _pending(client, story) is None

    announce = _turn(client, story, "I stab the wolf.")
    assert announce["disposition"] == "delivered", announce
    view = _pending(client, story)
    assert view["interaction_phase"] == "pending_roll"
    attack = view["pending_roll"]
    assert attack["display_expression"] == "1d20 + 1"  # Str -1, proficiency +2
    assert attack["progress"]["step_index"] == 1
    assert [o["option_id"] for o in attack["adjustment_options"]] == [
        "finesse_dexterity"
    ]
    assert not BACKEND_ONLY & _keys(view)
    assert _pending(client, story) == view  # reload: identical

    # Frozen from here until the resume.
    calls, probes, balance = len(REQUESTS), len(readiness_calls), _balance(client)
    live = _hp(client, wolf)
    before = _state(client, story)
    adjust = f"/api/stories/{story}/rpg/adjustments"

    def adjustment(option: str, revision: Any) -> dict[str, Any]:
        return {
            "pending_roll_request_id": attack["pending_roll_request_id"],
            "expected_instruction_revision": revision,
            "option_id": option,
        }

    rev = attack["instruction_revision"]
    _refused(
        _post(client, adjust, adjustment("finesse_dexterity", rev + 1)),
        409,
        "pending_roll_revision_mismatch",
    )
    for inexact in (True, 1.0, str(rev)):
        _refused(
            _post(client, adjust, adjustment("finesse_dexterity", inexact)),
            422,
            "validation_failed",
        )
    _refused(
        _post(client, adjust, adjustment("finesse_strength", rev)),
        422,
        "action_adjustment_not_allowed",
    )
    assert _state(client, story) == before

    revised_view = _advanced(
        _post(client, adjust, adjustment("finesse_dexterity", rev))
    )
    revised = revised_view["pending_roll"]
    assert revised_view["interaction_phase"] == "pending_roll"
    assert revised["instruction_id"] == attack["instruction_id"]
    assert revised["instruction_revision"] == rev + 1
    assert revised["display_expression"] == "1d20 + 4"  # Dex +2, proficiency +2
    assert _pending(client, story) == revised_view

    # Rejected rolls change nothing: the superseded instruction, an
    # impossible face, a foreign term, inexact values, an impossible total.
    _refused(_roll(client, story, attack, 15), 409, "pending_roll_revision_mismatch")
    _refused(_roll(client, story, revised, 21), 422, "pending_roll_invalid_value")
    wrong_term = {
        **revised,
        "terms": [{**revised["terms"][0], "term_id": str(uuid4())}],
    }
    _refused(_roll(client, story, wrong_term, 15), 422, "pending_roll_term_mismatch")
    for inexact in ("15", 15.0, True):
        _refused(_roll(client, story, revised, inexact), 422, "validation_failed")
    _refused(
        _post(
            client,
            f"/api/stories/{story}/rpg/rolls",
            {
                "source": "physical_self_report",
                "pending_roll_request_id": revised["pending_roll_request_id"],
                "expected_instruction_revision": revised["instruction_revision"],
                "reported_aggregate": 99,
            },
        ),
        422,
        "pending_roll_invalid_aggregate",
    )
    after_adjustment = _state(client, story)
    assert after_adjustment[2] == before[2] + 1  # the adjustment's one event

    damage_view = _advanced(_roll(client, story, revised, 15))  # 19 hits AC 12
    damage = damage_view["pending_roll"]
    assert damage["display_expression"] == "1d4 + 2"  # Dex, as the attack
    assert damage["progress"]["step_index"] == 2
    assert _pending(client, story) == damage_view
    # The accepted attack's duplicate is not this story's pending roll.
    _refused(_roll(client, story, revised, 15), 404, "pending_roll_not_found")
    # In-character input stays blocked; nothing advances.
    blocked = _turn(client, story, "I run away.")
    assert blocked["disposition"] == "blocked_pending_roll", blocked
    assert blocked["pending_roll_redirect_message"].startswith("Roll needed:")

    paused = _advanced(_roll(client, story, damage, 3))  # 5 damage: 4 HP -> 0
    assert paused["interaction_phase"] == "pending_mechanical_decision"
    decision = paused["pending_decision"]
    assert [o["option_id"] for o in decision["options"]] == [
        "knock_out",
        "no_knock_out",
    ]
    assert not BACKEND_ONLY & _keys(paused)
    assert _pending(client, story) == paused
    decide = f"/api/stories/{story}/rpg/decisions"

    def choice(option: str, revision: Any) -> dict[str, Any]:
        return {
            "decision_request_id": decision["decision_request_id"],
            "expected_decision_revision": revision,
            "option_id": option,
        }

    at_decision = _state(client, story)
    drev = decision["decision_revision"]
    _refused(
        _post(client, decide, choice("surrender", drev)),
        422,
        "mechanical_decision_invalid",
    )
    _refused(
        _post(client, decide, choice("knock_out", drev + 1)),
        409,
        "mechanical_decision_revision_mismatch",
    )
    _refused(_post(client, decide, choice("knock_out", True)), 422, "validation_failed")
    _refused(
        _post(
            client,
            decide,
            {**choice("knock_out", drev), "decision_request_id": str(uuid4())},
        ),
        422,
        "mechanical_decision_invalid",
    )
    blocked = _turn(client, story, "I run away.")
    assert blocked["disposition"] == "blocked_pending_roll", blocked
    assert _state(client, story) == at_decision

    ready = _advanced(_post(client, decide, choice("knock_out", drev)))
    assert ready == {
        "schema_version": 1,
        "sequence_id": ready["sequence_id"],
        "interaction_phase": "ready_for_narration",
        "pending_roll": None,
        "pending_decision": None,
    }
    assert _pending(client, story) == ready  # the reload's resume affordance
    blocked = _turn(client, story, "I run away.")
    assert blocked["disposition"] == "blocked_pending_roll", blocked

    # Between narrations: no provider call, access path or settlement, no
    # Turn or audit row, and the live wolf untouched. The three blocked
    # in-character turns are ordinary turns: each classified its input and
    # selected an access path, then stopped at the gate unsettled.
    assert [r.pass_id.value for r in REQUESTS[calls:]] == ["intent_classifier"] * 3
    assert len(readiness_calls) == probes + 3
    assert _balance(client) == balance
    ledger = _state(client, story)
    assert ledger[3:] == before[3:]
    assert ledger[2] == before[2] + 4  # adjustment, two rolls, decision
    assert _hp(client, wolf) == live

    writes, plans, intents = (
        _count("writer"),
        _count("planner"),
        _count("intent_classifier"),
    )
    resp = _resume(client, story, ready["sequence_id"])
    assert resp.status_code == 200, resp.text
    narrated = resp.json()
    assert narrated["disposition"] == "delivered", narrated
    assert narrated["settlement_warning"] is None
    assert narrated["delivered_output"]
    assert (_count("writer"), _count("planner"), _count("intent_classifier")) == (
        writes + 1,
        plans,
        intents,
    )
    assert _balance(client) < balance  # settled, once (asserted below)
    settled = _balance(client)
    assert _hp(client, wolf)[1:] == (1, {"unconscious"})
    assert _audit(client, story) == [
        ("Dagger attack", "player", 19, "success", "inline_ui", narrated["turn_id"]),
        (
            "Dagger damage",
            "player",
            5,
            "undetermined",
            "inline_ui",
            narrated["turn_id"],
        ),
    ]
    assert _pending(client, story) is None
    transcript = client.get(f"/api/stories/{story}/turns?latest=true").json()["turns"]
    assert transcript[-1]["turn_id"] == narrated["turn_id"]
    assert transcript[-1]["user_input"] == "I stab the wolf."  # the announce's
    assert no_backend_dice == []  # every die was the Sojourner's

    done = _state(client, story)
    _refused(
        _resume(client, story, ready["sequence_id"]),
        409,
        "action_sequence_already_completed",
    )
    assert _state(client, story) == done
    assert _balance(client) == settled


# ---------------------------------------------------------------------------
# Resume refusals, a blocked access path, failed narration and its retry
# ---------------------------------------------------------------------------


def _ready_club_attack(client: TestClient, gm: GM) -> tuple[str, str, str]:
    story = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    wolf = _wolf(client, story, hp=11)
    gm.append(
        [
            _begin(client, story),
            _attack(client, story, wolf, "equipment.weapons.club", "Club attack"),
        ]
    )
    assert _turn(client, story, "I swing my club.")["disposition"] == "delivered"
    attack = _pending(client, story)["pending_roll"]
    damage = _advanced(_roll(client, story, attack, 15))["pending_roll"]
    ready = _advanced(_roll(client, story, damage, 4))
    assert ready["interaction_phase"] == "ready_for_narration"
    return story, wolf, ready["sequence_id"]


@pytest.mark.parametrize("failure", ["writer_error", "writer_refusal"])
def test_resume_refusals_and_failures_keep_the_ready_facts_for_a_retry(
    client: TestClient,
    gm: GM,
    monkeypatch: pytest.MonkeyPatch,
    no_backend_dice: list[str],
    failure: str,
) -> None:
    """Typed refusals before any provider call (another node, an unknown
    sequence, a non-ready one in another story), no runnable access path, and
    a failed narration: each leaves the ready sequence, its ledger, the wolf,
    the audit and the balance as they were. The retry narrates the identical
    facts once and settles once."""
    from afterworlds.pipeline._refusal import PassIdentifier
    from tests.pipeline.orchestrator.conftest import make_refusal

    story, wolf, sequence = _ready_club_attack(client, gm)
    other, _, _ = _ready_club_attack(client, gm)
    before, balance, calls = _state(client, story), _balance(client), len(REQUESTS)

    # Another node: the story's current canonical node is not the one the
    # sequence was declared at (here, the other story's node).
    other_sequence = _pending(client, other)["sequence_id"]
    node, other_node = (_node(client, q) for q in (sequence, other_sequence))
    _set_node(client, sequence, other_node)
    _refused(_resume(client, story, sequence), 409, "action_sequence_state_conflict")
    _set_node(client, sequence, node)
    _refused(_resume(client, story, str(uuid4())), 404, "action_sequence_not_found")
    # Another story's sequence is not found from this story.
    _refused(_resume(client, story, other_sequence), 404, "action_sequence_not_found")
    assert len(REQUESTS) == calls
    assert _state(client, story) == before

    # No runnable access path: refused before the orchestrator.
    real_status = EntitlementService.get_access_path_status

    def blocked(self: Any, sojourner_id: UUID) -> Any:
        return real_status(self, sojourner_id).model_copy(
            update={"hosted_turn_available": False, "byok_turn_available": False}
        )

    monkeypatch.setattr(EntitlementService, "get_access_path_status", blocked)
    _refused(_resume(client, story, sequence), 403, "entitlement_blocked")
    monkeypatch.setattr(EntitlementService, "get_access_path_status", real_status)
    assert len(REQUESTS) == calls
    assert _state(client, story) == before

    real_call = FakeProviderAdapter.call
    once = [failure]

    def call(self: Any, request: Any) -> Any:
        if once and request.pass_id.value == "writer":
            once.pop()
            if failure == "writer_refusal":
                raise make_refusal(PassIdentifier.WRITER)
            raise RuntimeError("injected writer failure")
        return real_call(self, request)

    monkeypatch.setattr(FakeProviderAdapter, "call", call)
    resp = _resume(client, story, sequence)
    assert resp.status_code == 200, resp.text
    failed = resp.json()
    assert (
        failed["disposition"]
        == {
            "writer_error": "pipeline_error",
            "writer_refusal": "refused_by_provider",
        }[failure]
    ), failed
    assert failed["turn_id"] is None and failed["settlement_warning"] is None
    assert _state(client, story) == before
    assert _hp(client, wolf)[1] == 11
    assert _balance(client) == balance
    assert _pending(client, story)["interaction_phase"] == "ready_for_narration"

    retried = _resume(client, story, sequence).json()
    assert retried["disposition"] == "delivered", retried
    assert _audit(client, story) == [
        ("Club attack", "player", 16, "success", "inline_ui", retried["turn_id"]),
        ("Club damage", "player", 3, "undetermined", "inline_ui", retried["turn_id"]),
    ]
    assert _hp(client, wolf)[1] == 8
    assert _balance(client) < balance
    assert no_backend_dice == []

    # 15b-32 after access is gone (a real hosted deactivation; the Sojourner
    # has no BYOK): the replay is still the typed success-equivalent, with no
    # provider call, Turn, audit or settlement.
    with client.app.state.session_factory() as s:
        EntitlementService(s).receive_entitlement_event(
            client.app.state.sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_DEACTIVATED,
            HostedAccessDeactivatedPayload(
                effective_at=datetime.now(UTC),
                reason=HostedAccessDeactivationReason.SUBSCRIPTION_CANCELLED,
            ),
        )
        s.commit()
    _refused(_turn_raw(client, story, "I look around."), 403, "entitlement_blocked")
    done, settled, calls = _state(client, story), _balance(client), len(REQUESTS)
    _refused(_resume(client, story, sequence), 409, "action_sequence_already_completed")
    _refused(_resume(client, story, str(uuid4())), 404, "action_sequence_not_found")
    assert (_state(client, story), _balance(client), len(REQUESTS)) == (
        done,
        settled,
        calls,
    )


def _node(client: TestClient, sequence: str) -> str:
    (row,) = _rows(
        client,
        "SELECT node_id FROM action_resolution_sequences WHERE sequence_id = :q",
        q=sequence,
    )
    return str(row.node_id)


def _set_node(client: TestClient, sequence: str, node: str) -> None:
    with client.app.state.session_factory() as s:
        s.execute(
            sa.text(
                "UPDATE action_resolution_sequences SET node_id = :n"
                " WHERE sequence_id = :q"
            ),
            {"n": node, "q": sequence},
        )
        s.commit()


# ---------------------------------------------------------------------------
# Story scoping, out-of-character input, the gate on every state
# ---------------------------------------------------------------------------


def test_another_storys_pending_interaction_never_advances_from_this_story(
    client: TestClient, gm: GM, no_backend_dice: list[str]
) -> None:
    """Story A's routes refuse story B's pending roll, adjustment and
    decision ids; B is unchanged and still advances through its own routes."""
    a = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    b = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    for story in (a, b):
        wolf = _wolf(client, story, hp=3)
        gm.append(
            [
                _begin(client, story),
                _attack(client, story, wolf, "equipment.weapons.club", "Club attack"),
            ]
        )
        assert _turn(client, story, "I swing.")["disposition"] == "delivered"
    theirs = _pending(client, b)["pending_roll"]
    before = (_state(client, a), _state(client, b))
    _refused(_roll(client, a, theirs, 15), 404, "pending_roll_not_found")
    _refused(
        _post(
            client,
            f"/api/stories/{a}/rpg/adjustments",
            {
                "pending_roll_request_id": theirs["pending_roll_request_id"],
                "expected_instruction_revision": theirs["instruction_revision"],
                "option_id": "anything",
            },
        ),
        404,
        "pending_roll_not_found",
    )
    assert (_state(client, a), _state(client, b)) == before
    damage = _advanced(_roll(client, b, theirs, 15))["pending_roll"]
    decision = _advanced(_roll(client, b, damage, 4))["pending_decision"]
    assert decision is not None  # 3 damage drops the 3-HP wolf
    before = (_state(client, a), _state(client, b))
    _refused(
        _post(
            client,
            f"/api/stories/{a}/rpg/decisions",
            {
                "decision_request_id": decision["decision_request_id"],
                "expected_decision_revision": decision["decision_revision"],
                "option_id": "knock_out",
            },
        ),
        422,
        "mechanical_decision_invalid",
    )
    assert (_state(client, a), _state(client, b)) == before


def test_out_of_character_input_never_alters_the_sequence(
    client: TestClient,
    gm: GM,
    monkeypatch: pytest.MonkeyPatch,
    no_backend_dice: list[str],
) -> None:
    """OOC stays available at a pending roll and changes nothing of the
    sequence (15b-31)."""
    import afterworlds.api.fake_pipeline as fake

    real_intent = fake.fake_intent_model_caller

    def intent(prompt: str) -> str:
        if "(OOC)" in prompt:
            return json.dumps(
                {
                    "intent_type": "ooc",
                    "confidence": 0.9,
                    "ambiguous": False,
                    "secondary_intent": None,
                }
            )
        return real_intent(prompt)

    monkeypatch.setattr(fake, "fake_intent_model_caller", intent)
    story = _rpg_story(client, dice=DiceHandling.PLAYER_ROLLS)
    wolf = _wolf(client, story, hp=11)
    gm.append(
        [
            _begin(client, story),
            _attack(client, story, wolf, "equipment.weapons.club", "Club attack"),
        ]
    )
    assert _turn(client, story, "I swing.")["disposition"] == "delivered"
    view = _pending(client, story)
    sequence_row = _state(client, story)[:3]
    ooc = _turn(client, story, "(OOC) what does my roll need?")
    assert ooc["disposition"] == "ooc_handled", ooc
    assert _state(client, story)[:3] == sequence_row
    assert _pending(client, story) == view


# ---------------------------------------------------------------------------
# A contest (ADR-015b Group 17) through the product, hidden counterpart
# ---------------------------------------------------------------------------


def test_a_contest_against_a_hidden_counterpart_is_reachable_and_projected_as_a_check(
    client: TestClient, gm: GM, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Group 17's production reachability: a player-rolled Athletics contest
    against an Ape whose roll is hidden, with the S1 supplement applied in
    memory only. The player sees an ordinary roll of their own; the Ape's die
    is drawn when theirs is accepted; one narration delivers both audits."""
    index = s1(monkeypatch)
    queue = [15]
    rolled = scripted_dice(monkeypatch, lambda _e: (queue.pop(0),))
    resp = client.post(
        "/api/stories", json={"title": "15b", "mode": "rpg", "character_name": "Ilse"}
    )
    story = resp.json()["story_id"]
    with client.app.state.session_factory() as s:
        state = get_rpg_session_state_by_story(s, UUID(story))
        assert state is not None
        store.create_character_state(
            s,
            state.character_sheet_id,
            complete_character(index, "classes.wizard", 3),
            index.binding,
            now=NOW,
        )
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
        ape = store.create_creature(
            s,
            UUID(story),
            "Ape",
            CreatureState(
                template_record_key="animals.ape",
                hit_points=HitPoints(current=19, maximum=19, temporary=0),
                conditions=(),
                active_effects=(),
                death_state=DeathState(
                    successes=0, failures=0, stable=False, dead=False
                ),
                zero_hit_point_treatment=ZeroHitPointTreatment(subject="monster"),
            ),
            index.binding,
            now=NOW,
        )
        s.commit()
        sheet = str(state.character_sheet_id)
    gm.append(
        [
            {
                "check_label": "Arm wrestling",
                "subsystem_tag": "contest",
                "visibility": "shown",
                "operation": "contest",
                "contest": {
                    "initiator": {
                        "subject": {"kind": "character", "subject_id": sheet},
                        "ability": "strength",
                        "skill": "athletics",
                    },
                    "resister": {
                        "subject": {
                            "kind": "creature",
                            "subject_id": str(ape.creature_id),
                        },
                        "ability": "strength",
                        "skill": "athletics",
                        "roll_hidden": True,
                    },
                    "stakes": "the ring on the table",
                    "counterpart_perceived": True,
                },
            }
        ]
    )
    assert _turn(client, story, "I challenge the ape.")["disposition"] == "delivered"
    view = _pending(client, story)
    pending = view["pending_roll"]
    assert pending["display_expression"] == "1d20 - 1"
    assert not BACKEND_ONLY & _keys(view)
    assert "ape" not in json.dumps(view).lower()
    assert rolled == []
    ready = _advanced(_roll(client, story, pending, 12))
    assert ready["interaction_phase"] == "ready_for_narration"
    assert rolled == ["1d20"]  # the Ape's, in the accepting write
    assert not BACKEND_ONLY & _keys(ready)
    writes = _count("writer")
    narrated = _resume(client, story, ready["sequence_id"]).json()
    assert narrated["disposition"] == "delivered", narrated
    # The hidden participant's event and audit keep its whole internal total.
    assert [(a[1], a[2]) for a in _audit(client, story)] == [
        ("player", 11),
        ("hidden", 20),
    ]
    # The narration's mechanical projection: the Writer's views (ADR-015
    # redaction) carry the player's own check and nothing of the hidden die;
    # no public response field carries a mechanical value at all.
    (writer,) = [r for r in REQUESTS if r.pass_id.value == "writer"][writes:]
    (view_,) = _writer_views(writer)
    # The player's own check and total. The comparison against the hidden
    # total is not projected as a target or an outcome; the summary narrates
    # the loss (Phase 2's contest projection) without the Ape's number.
    assert (view_["visibility"], view_["total"], view_["outcome"]) == (
        "player",
        11,
        None,
    )
    assert view_["dc"] != 20
    assert "lost" in view_["player_facing_summary"]
    assert not re.search(r"(?<![\dd])20\b", view_["player_facing_summary"])
