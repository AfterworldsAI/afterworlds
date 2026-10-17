"""CRD Issue 21 RPG product startup (ADR-015c) through the product.

Fresh RPG stories on a private copy of the published-release store, with the
production provider resolver, readiness and binding; only the provider HTTP
transport and credential storage are doubled (``rpg_spine`` fixture). No test
seeds character state or forces play: every phase advances through the
product's setup turns and typed setup operations.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

import pytest
import sqlalchemy as sa

from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.pipeline.provider._routing import CapabilityProfileAwareSafetyPolicy
from afterworlds.services import rpg_setup
from afterworlds.services.dnd5e_state import store as character_store
from afterworlds.services.dnd5e_state.authority import current_binding
from scripts.scripted_provider import SCRIPTED_SAFETY_BLOCK, Reply
from tests.api._spine import Spine
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    PACKAGE,
    _roll,
    g1_store,
)
from tests.ingestion.mechanical.test_crd21_rpg_spine import rpg_spine
from tests.services.dnd5e_state.builders import complete_character, real_index

__all__ = ["g1_store", "rpg_spine"]  # fixtures used by pytest

_CONFIG = {
    "dice_handling": "player_rolls",
    "gm_cheating": False,
    "tone": "gritty",
    "session_type": "campaign",
    "house_rules": None,
    "acceptable_content": "no gore",
}


def _character() -> dict[str, Any]:
    return complete_character(real_index(), "classes.wizard", 1).model_dump(mode="json")


def _view(s: Spine, story: str) -> dict[str, Any]:
    resp = s.client.get(f"/api/stories/{story}/rpg/setup")
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def _op(s: Spine, story: str, name: str, body: dict[str, Any]) -> Any:
    return s.client.post(f"/api/stories/{story}/rpg/setup/{name}", json=body)


def _ok(resp: Any) -> dict[str, Any]:
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[no-any-return]


def _propose(
    s: Spine, path: str, character: dict[str, Any], unresolved: list[str] | None = None
) -> None:
    s.provider.push(
        "rpg_setup_writer",
        Reply(
            tool_input={
                "schema_version": 1,
                "gm_text": "Here is the character as I have it.",
                "result": {
                    "kind": "character_proposal",
                    "path": path,
                    "character": character,
                    "unresolved": unresolved or [],
                },
            }
        ),
    )


def _save_config(s: Spine, story: str, fields: dict[str, Any]) -> None:
    resp = s.client.post(
        f"/api/stories/{story}/setup",
        json={
            "mode": "rpg",
            **{k: v for k, v in fields.items() if v is not None},
            "expected_configuration_revision": _view(s, story)[
                "configuration_revision"
            ],
        },
    )
    assert resp.status_code == 200, resp.text


def _rows(s: Spine, sql: str, **params: object) -> list[Any]:
    with s.session_factory() as session:
        return list(session.execute(sa.text(sql), params).all())


def _eligible(s: Spine, turn_id: str) -> Any:
    ((raw,),) = _rows(
        s, "SELECT mode_metadata FROM turns WHERE turn_id = :t", t=turn_id
    )
    meta = raw if isinstance(raw, dict) else json.loads(raw or "{}")
    return (meta or {}).get("rolling_summary_eligible")


def _new_story(s: Spine) -> str:
    resp = s.client.post(
        "/api/stories",
        json={"title": "Startup", "mode": "rpg", "character_name": "Ilse"},
    )
    assert resp.status_code == 201, resp.text
    return str(resp.json()["story_id"])


def _through_world(s: Spine, story: str) -> dict[str, Any]:
    first = s.turn(
        story, "A storm-wracked archipelago ruled by rival lighthouse guilds."
    )
    assert first["disposition"] == "delivered", first
    assert _eligible(s, first["turn_id"]) is False  # setup is never summary input
    view = _view(s, story)
    assert view["phase"] == "world_setup" and view["play_status"] == "setup"
    target = view["world_target"]
    assert target["turn_id"] == first["turn_id"]
    return _ok(
        _op(
            s,
            story,
            "confirm-world",
            {"expected_world_revision": target["world_revision"]},
        )
    )


@pytest.mark.parametrize("access", ["hosted", "byok"])
@pytest.mark.parametrize("path", ["gm_led", "completed_sheet"])
def test_fresh_story_completes_setup_and_plays_through_both_paths(
    rpg_spine: Spine, access: str, path: str
) -> None:
    s = rpg_spine
    s.seed_hosted() if access == "hosted" else s.seed_byok()
    story = _new_story(s)
    assert _view(s, story)["phase"] == "world_setup"

    view = _through_world(s, story)
    assert view["phase"] == "character_creation"
    assert [p["package_uuid"] for p in view["packages"]] == [str(PACKAGE)]

    if path == "gm_led":
        # Conversational creation: the GM gathers choices over turns.
        s.turn(story, "I want to play a wizard; a sage background.")
        _propose(s, path, {**_character(), "ability_scores": None}, ["ability scores"])
        s.turn(story, "Let me think about my stats.")
    else:
        _propose(s, path, {**_character(), "ability_scores": None}, ["ability scores"])
        s.turn(story, "Here is my sheet: Wizard 1, Elf, Sage ... (stats missing)")
    candidate = _view(s, story)["candidate"]
    assert candidate["path"] == path
    assert "select a supported Rules Package first" in candidate["problems"]
    assert "unresolved: ability scores" in candidate["problems"]

    before_calls = len(s.provider.calls)
    view = _ok(_op(s, story, "rules-package", {"package_uuid": str(PACKAGE)}))
    assert view["selected_package_uuid"] == str(PACKAGE)
    assert view["candidate"]["revision"] == candidate["revision"] + 1
    assert any("ability_scores" in p for p in view["candidate"]["problems"])
    refused = _op(
        s, story, "accept-character",
        {"expected_candidate_revision": view["candidate"]["revision"]},
    )  # fmt: skip
    assert refused.status_code == 422
    assert "ability_scores" in refused.json()["detail"]["problems"]

    _propose(s, path, _character())
    s.turn(story, "Ability scores: 8, 14, 13, 15, 12, 10.")
    candidate = _view(s, story)["candidate"]
    assert candidate["problems"] == [], candidate
    # Every populated proposed value is reviewable in full before acceptance:
    # formerly omitted fields too, and values longer than 300 characters.
    proposed = {k: v for k, v in _character().items() if v is not None}
    shown = {r["label"]: r["value"] for r in candidate["sheet"]}
    assert len(candidate["sheet"]) == len(proposed)
    assert sorted(shown.values()) == sorted(
        json.dumps(v, sort_keys=True, ensure_ascii=False) for v in proposed.values()
    )
    assert "Spell access" in shown and "Usage counters" in shown
    assert max(len(v) for v in shown.values()) > 300
    stale = _op(
        s, story, "accept-character",
        {"expected_candidate_revision": candidate["revision"] - 1},
    )  # fmt: skip
    assert stale.status_code == 409
    accepted = _ok(
        _op(
            s,
            story,
            "accept-character",
            {"expected_candidate_revision": candidate["revision"]},
        )
    )
    assert accepted["phase"] == "play_configuration"
    assert accepted["character_accepted"] is True
    again = _ok(
        _op(
            s,
            story,
            "accept-character",
            {"expected_candidate_revision": candidate["revision"]},
        )
    )
    assert again == accepted  # repeated acceptance returns current state

    # The accepted sheet is first-class, under the package's exact binding.
    with s.session_factory() as session:
        state = rpg_setup._state(session, UUID(story))
        stored = character_store.get_character(session, state.character_sheet_id)
        assert stored is not None
        assert stored.binding == current_binding(session, PACKAGE, now=rpg_setup_now())
        # Exactly the reviewed candidate, under the binding it was validated in.
        assert stored.state == Dnd5eCharacterState.model_validate(_character())
        setup = rpg_setup.load_setup(
            session, rpg_setup.anchor_node_id(session, UUID(story))
        )
        assert setup.candidate is not None
        assert stored.binding.model_dump(mode="json") == setup.candidate.binding
        assert len(_rows(s, "SELECT 1 FROM dnd5e_character_states")) >= 1

    # Configuration: saved through the typed setup route, summarized by the
    # GM, and confirmed exactly as summarized.
    assert (
        _op(s, story, "complete", {"expected_configuration_revision": 0}).status_code
        == 409
    )
    _save_config(s, story, _CONFIG)
    assert _view(s, story)["configuration_target"] is None
    summary = s.turn(story, "Ready to confirm settings.")
    assert summary["disposition"] == "delivered"
    assert _eligible(s, summary["turn_id"]) is False
    target = _view(s, story)["configuration_target"]
    assert target["turn_id"] == summary["turn_id"] and target["summary"]
    assert target["configuration"]["tone"] == "gritty"
    assert "tone: gritty" in target["summary"]  # the GM saw the saved values
    early = s.turn(story, "I attack the guild master.")  # still setup: no mechanics
    assert early["disposition"] == "delivered"
    assert not [
        c for c in s.provider.calls[before_calls:] if c.pass_name == "rpg_adjudication"
    ]
    # An edit after the summary invalidates it: Complete refuses the stale one.
    target = _view(s, story)["configuration_target"]
    _save_config(s, story, {"tone": "forgiving"})
    assert _view(s, story)["configuration_target"] is None
    stale = _op(
        s, story, "complete",
        {"expected_configuration_revision": target["configuration_revision"]},
    )  # fmt: skip
    assert stale.status_code == 409
    assert _view(s, story)["phase"] == "play_configuration"
    _save_config(s, story, {"tone": "gritty"})
    s.turn(story, "Please confirm my settings now.")
    target = _view(s, story)["configuration_target"]
    calls = len(s.provider.calls)
    confirm = {"expected_configuration_revision": target["configuration_revision"]}
    done = _ok(_op(s, story, "complete", confirm))
    assert (done["phase"], done["play_status"]) == ("complete", "in_play")
    assert done["configuration"]["tone"] == "gritty"
    assert done["configuration"]["gm_cheating"] is False
    assert _ok(_op(s, story, "complete", confirm)) == done
    assert len(s.provider.calls) == calls  # confirmations call no provider
    assert _rows(s, "SELECT 1 FROM rolling_summaries") == []

    # First ordinary interaction: a player-rolled check pauses, then resumes.
    s.provider.push("rpg_adjudication", Reply(tool_input={"rolls": [_roll()]}))
    announce = s.turn(story, "I climb the rain-slick lighthouse wall.")
    assert announce["disposition"] == "delivered", announce
    pending = s.client.get(f"/api/stories/{story}/rpg/pending-interaction").json()
    instruction = pending["interaction"]["pending_roll"]
    (term,) = instruction["terms"]
    ready = s.client.post(
        f"/api/stories/{story}/rpg/rolls",
        json={
            "source": "inline_ui",
            "pending_roll_request_id": instruction["pending_roll_request_id"],
            "expected_instruction_revision": instruction["instruction_revision"],
            "term_results": [{"term_id": term["term_id"], "values": [17]}],
        },
    ).json()
    assert ready["interaction_phase"] == "ready_for_narration", ready
    narrated = s.client.post(
        f"/api/stories/{story}/rpg/sequences/{ready['sequence_id']}/resume"
    ).json()
    assert narrated["disposition"] == "delivered", narrated
    assert _eligible(s, narrated["turn_id"]) is True

    # Reload: the authoritative state comes back.
    assert _view(s, story) == done
    visible = s.client.get(f"/api/stories/{story}/visible-state").json()
    assert visible["visible_state"]["character"]["character_name"] == "Ilse"
    deductions = s.deductions()
    if access == "hosted":
        assert summary["turn_id"] in deductions and narrated["turn_id"] in deductions
    else:
        assert deductions == {}


def rpg_setup_now() -> str:
    from afterworlds.api.rpg_setup import now

    return now()


def test_world_edits_invalidate_confirmation_and_order_is_enforced(
    rpg_spine: Spine,
) -> None:
    s = rpg_spine
    s.seed_hosted()
    story = _new_story(s)
    for op, body in (
        ("accept-character", {"expected_candidate_revision": 0}),
        ("complete", {"expected_configuration_revision": 0}),
    ):
        assert _op(s, story, op, body).status_code == 409  # out of order
    s.turn(story, "A desert of glass.")
    first = _view(s, story)["world_target"]
    s.provider.push(
        "rpg_setup_writer",
        Reply(
            tool_input={
                "schema_version": 1,
                "gm_text": "Who rules the glass?",
                "result": {"kind": "clarification", "questions": ["Who rules?"]},
            }
        ),
    )
    s.turn(story, "Actually, make it a jungle.")
    view = _view(s, story)
    assert view["world_target"] is None and view["world_revision"] == 2
    stale = _op(
        s, story, "confirm-world", {"expected_world_revision": first["world_revision"]}
    )
    assert stale.status_code == 409
    assert (
        _op(s, story, "rules-package", {"package_uuid": str(PACKAGE)}).status_code
        == 409
    )
    s.turn(story, "A jungle ruled by a serpent queen.")
    target = _view(s, story)["world_target"]
    _ok(
        _op(
            s,
            story,
            "confirm-world",
            {"expected_world_revision": target["world_revision"]},
        )
    )
    again = _op(s, story, "confirm-world", {"expected_world_revision": 1})
    assert again.status_code == 200  # already confirmed: current state
    bogus = _op(
        s,
        story,
        "rules-package",
        {"package_uuid": "00000000-0000-0000-0000-000000000001"},
    )
    assert bogus.status_code == 422


@pytest.mark.parametrize(
    ("reply", "disposition"),
    [
        (Reply(refusal=True), "refused_by_provider"),
        (Reply(status=500), "pipeline_error"),
        (
            # A character proposal is not allowed in world setup.
            Reply(
                tool_input={
                    "schema_version": 1,
                    "gm_text": "A character!",
                    "result": {
                        "kind": "character_proposal",
                        "path": "gm_led",
                        "character": {},
                    },
                }
            ),
            "pipeline_error",
        ),
        (Reply(text="No tool call at all."), "pipeline_error"),
    ],
)
def test_failed_setup_exchanges_expose_nothing_and_charge_nothing(
    rpg_spine: Spine, reply: Reply, disposition: str
) -> None:
    s = rpg_spine
    s.seed_hosted()
    story = _new_story(s)
    s.provider.push("rpg_setup_writer", reply)
    failed = s.turn(story, "A frozen sea.")
    assert failed["disposition"] == disposition, failed
    assert failed["delivered_output"] is None
    view = _view(s, story)
    assert (view["world_revision"], view["world_target"]) == (0, None)
    assert _rows(s, "SELECT 1 FROM turns") == []
    assert s.deductions() == {}
    retried = s.turn(story, "A frozen sea.")
    assert retried["disposition"] == "delivered"
    assert _view(s, story)["world_target"] is not None


def _to_candidate(s: Spine, story: str) -> int:
    _through_world(s, story)
    _ok(_op(s, story, "rules-package", {"package_uuid": str(PACKAGE)}))
    _propose(s, "completed_sheet", _character())
    s.turn(story, "My completed sheet.")
    candidate = _view(s, story)["candidate"]
    assert candidate["problems"] == []
    return int(candidate["revision"])


def test_acceptance_commit_failure_and_changed_authority_leave_setup_intact(
    rpg_spine: Spine, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = rpg_spine
    s.seed_hosted()
    story = _new_story(s)
    revision = _to_candidate(s, story)

    real_update = rpg_setup.update_rpg_session_state

    def failing(*a: Any, **kw: Any) -> Any:
        raise RuntimeError("disk I/O error")

    monkeypatch.setattr(rpg_setup, "update_rpg_session_state", failing)
    with pytest.raises(RuntimeError):
        _op(s, story, "accept-character", {"expected_candidate_revision": revision})
    monkeypatch.setattr(rpg_setup, "update_rpg_session_state", real_update)
    view = _view(s, story)
    assert view["phase"] == "character_creation" and view["character_accepted"] is False

    real_binding = rpg_setup.current_binding

    def moved(session: Any, package_uuid: UUID, *, now: str) -> Any:
        binding = real_binding(session, package_uuid, now=now)
        return binding.model_copy(update={"release_version": "moved"})

    monkeypatch.setattr(rpg_setup, "current_binding", moved)
    changed = _op(
        s, story, "accept-character", {"expected_candidate_revision": revision}
    )
    assert changed.status_code == 409
    monkeypatch.setattr(rpg_setup, "current_binding", real_binding)
    assert _view(s, story)["character_accepted"] is False
    _ok(_op(s, story, "accept-character", {"expected_candidate_revision": revision}))


def test_concurrent_acceptance_is_serialized(rpg_spine: Spine) -> None:
    s = rpg_spine
    s.seed_hosted()
    story = _new_story(s)
    revision = _to_candidate(s, story)
    lock = s.client.app.state.story_locks[UUID(story)]  # type: ignore[attr-defined]
    asyncio.run(lock.acquire())
    try:
        held = _op(
            s, story, "accept-character", {"expected_candidate_revision": revision}
        )
        assert held.status_code == 409
        assert held.json()["error_code"] == "turn_in_flight"
    finally:
        lock.release()
    assert _view(s, story)["character_accepted"] is False
    _ok(_op(s, story, "accept-character", {"expected_candidate_revision": revision}))


def test_blocked_setup_output_exposes_no_candidate(rpg_spine: Spine) -> None:
    """BYOK with an OpenRouter route runs Output Safety; a blocked character
    exchange leaves no Turn and no candidate."""
    s = rpg_spine
    s.seed_byok(openrouter=True)
    story = _new_story(s)
    _through_world(s, story)
    _ok(_op(s, story, "rules-package", {"package_uuid": str(PACKAGE)}))
    _propose(s, "gm_led", _character())
    s.provider.push(
        "safety",
        Reply(tool_input={"concerns": []}),
        Reply(
            tool_input={
                "concerns": [
                    {
                        "category": "OTHER",
                        "description": "scripted",
                        "evidence_summary": "scripted",
                    }
                ]
            }
        ),
    )
    blocked = s.turn(story, "Make my character.")
    assert blocked["disposition"] == "blocked_output_safety", blocked
    assert _view(s, story)["candidate"] is None


def _setup_state(s: Spine, story: str) -> tuple[Any, ...]:
    """The authoritative state a blocked setup exchange must leave intact."""
    return (
        _view(s, story),
        s.deductions(),
        _rows(s, "SELECT turn_id, assistant_output FROM turns ORDER BY timestamp"),
        _rows(s, "SELECT count(*) FROM sb_events"),
    )


@pytest.mark.parametrize(
    "field", ["world_understanding", "character_value", "unresolved_note"]
)
def test_output_safety_audits_every_visible_setup_field(
    rpg_spine: Spine, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    """PR #204 P1: with Output Safety required, content confined to a field
    the setup view displays -- never the benign ``gm_text`` -- reaches the
    audit and fails closed: no Turn, target, candidate, phase change, canon
    event or hosted deduction. The same exchange without it then delivers."""
    s = rpg_spine
    s.seed_hosted()
    # The existing policy, made to require the audit on this hosted route.
    monkeypatch.setattr(
        CapabilityProfileAwareSafetyPolicy,
        "should_run_output_audit",
        lambda self, ctx: True,
    )
    story = _new_story(s)
    if field != "world_understanding":
        _through_world(s, story)
        _ok(_op(s, story, "rules-package", {"package_uuid": str(PACKAGE)}))

    def push(marked: bool) -> None:
        mark = f" {SCRIPTED_SAFETY_BLOCK}" if marked else ""
        if field == "world_understanding":
            result: dict[str, Any] = {
                "kind": "world_confirmation",
                "understanding": f"Lighthouse guilds rule the isles.{mark}",
            }
        else:
            character = _character()
            unresolved = ["Which cantrips?"]
            if field == "character_value":
                character["backstory_hooks"] = [f"Owes the guild a debt.{mark}"]
            else:
                unresolved = [f"Which cantrips?{mark}"]
            result = {
                "kind": "character_proposal",
                "path": "gm_led",
                "character": character,
                "unresolved": unresolved,
            }
        s.provider.push(
            "rpg_setup_writer",
            Reply(
                tool_input={
                    "schema_version": 1,
                    "gm_text": "Here is what I have so far.",
                    "result": result,
                }
            ),
        )

    before = _setup_state(s, story)
    push(marked=True)
    blocked = s.turn(story, "Go on.")
    assert blocked["disposition"] == "blocked_output_safety", blocked
    audited = s.provider.calls_for("safety")[-1]
    assert any(SCRIPTED_SAFETY_BLOCK in text for text in audited.texts)
    assert _setup_state(s, story) == before  # reload shows nothing new

    push(marked=False)
    delivered = s.turn(story, "Go on.")
    assert delivered["disposition"] == "delivered", delivered
    (turn_text,) = _rows(
        s, "SELECT assistant_output FROM turns WHERE turn_id = :t",
        t=delivered["turn_id"],
    )[0]  # fmt: skip
    # The transcript keeps the GM's text alone; the audit saw the rest.
    assert turn_text == "Here is what I have so far."
    shown = s.provider.calls_for("safety")[-1].texts
    expected = (
        "Lighthouse guilds rule the isles."
        if field == "world_understanding"
        else "Which cantrips?"
    )
    assert any(expected in text for text in shown)
    view = _view(s, story)
    if field == "world_understanding":
        assert view["world_target"]["turn_id"] == delivered["turn_id"]
    else:
        assert before[0]["candidate"] is None and view["candidate"]["revision"] == 1


def test_setup_output_audit_follows_the_existing_policy(rpg_spine: Spine) -> None:
    """When the policy does not require Output Safety (hosted Anthropic, no
    risk signal), no audit runs and the setup turn delivers as before."""
    s = rpg_spine
    s.seed_hosted()
    story = _new_story(s)
    audits = len(s.provider.calls_for("safety"))
    _through_world(s, story)
    assert len(s.provider.calls_for("safety")) == audits
