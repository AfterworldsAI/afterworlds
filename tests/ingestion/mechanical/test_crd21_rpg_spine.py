"""CRD Issue 21: RPG through the product on hosted and BYOK, with the
production provider resolver, readiness and binding.

``create_app`` runs on a private copy of the published-release store
(``g1_store``). Unlike the CRD Issue 15b/15c product suites, the fake
provider is off: only the provider HTTP transport
(``scripts/scripted_provider.py``) and credential storage (in-memory keyring)
are replaced, and the GameMaster's proposals arrive as scripted transport
replies to the real adjudication pass. The character is seeded at the store
level exactly as those suites do (no conversational character-creation
product path exists; see the CRD Issue 21 evidence matrix).
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import keyring
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from afterworlds.api.app import create_app
from afterworlds.api.config import ApiSettings
from afterworlds.models.enums import DiceHandling
from afterworlds.persistence.orm.rolling_summary import RollingSummaryORM
from afterworlds.services.rolling_summary import ROLLING_SUMMARY_N
from scripts.e2e_memory_keyring import install as install_memory_keyring
from scripts.scripted_provider import SYNTHETIC_HOSTED_KEY, Reply, ScriptedProvider
from tests.api._spine import Spine
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    _roll,
    _rpg_story,
    g1_store,
)
from tests.ingestion.mechanical.test_rpg_actions_on_published_release import (
    _attack,
    _begin,
    _wolf,
)

__all__ = ["g1_store"]  # fixture used by pytest


@pytest.fixture()
def rpg_spine(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Spine]:
    # Diagnostic iteration only: CRD21_G1_STORE may name an already built
    # copy of the same published-release store (scripts/e2e_rpg_server.py
    # build_store); gates run without it and build g1_store fresh.
    cached = os.environ.get("CRD21_G1_STORE")
    source = Path(cached) if cached else request.getfixturevalue("g1_store")
    db = tmp_path / "store.db"
    shutil.copyfile(source, db)
    monkeypatch.delenv("AFTERWORLDS_FAKE_PROVIDER", raising=False)
    monkeypatch.delenv("AFTERWORLDS_CI", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", SYNTHETIC_HOSTED_KEY)
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    previous = keyring.get_keyring()
    install_memory_keyring()
    provider = ScriptedProvider().install()
    try:
        app = create_app(
            ApiSettings(
                database_url=f"sqlite:///{db}", frontend_dist_dir=tmp_path / "x"
            )
        )
        with TestClient(app) as client:
            yield Spine(client, provider)
    finally:
        provider.uninstall()
        keyring.set_keyring(previous)


def _rows(spine_: Spine, sql: str, **params: object) -> list[Any]:
    with spine_.session_factory() as session:
        return list(session.execute(sa.text(sql), params).all())


def _eligibility(s: Spine, turn_id: str) -> Any:
    ((raw,),) = _rows(
        s, "SELECT mode_metadata FROM turns WHERE turn_id = :t", t=turn_id
    )
    meta = raw if isinstance(raw, dict) else json.loads(raw)
    return meta.get("rolling_summary_eligible")


def _gm(s: Spine, *rolls: dict[str, Any]) -> None:
    s.provider.push("rpg_adjudication", Reply(tool_input={"rolls": list(rolls)}))


def _pending(s: Spine, story: str) -> Any:
    resp = s.client.get(f"/api/stories/{story}/rpg/pending-interaction")
    assert resp.status_code == 200, resp.text
    return resp.json()["interaction"]


def _submit_roll(s: Spine, story: str, view: dict[str, Any], value: int) -> Any:
    (term,) = view["terms"]
    resp = s.client.post(
        f"/api/stories/{story}/rpg/rolls",
        json={
            "source": "inline_ui",
            "pending_roll_request_id": view["pending_roll_request_id"],
            "expected_instruction_revision": view["instruction_revision"],
            "term_results": [{"term_id": term["term_id"], "values": [value]}],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _seed(s: Spine, path: str) -> None:
    if path == "hosted":
        s.seed_hosted()
    else:
        s.seed_byok()


@pytest.mark.parametrize("path", ["hosted", "byok"])
def test_rpg_backend_checks_commit_with_the_turn_and_hide_hidden_rolls(
    rpg_spine: Spine, path: str
) -> None:
    s = rpg_spine
    _seed(s, path)
    story = _rpg_story(s.client)

    _gm(s, _roll())
    shown = s.turn(story, "I climb the rain-slick wall.")
    assert shown["disposition"] == "delivered", shown
    _gm(s, _roll(visibility="hidden"))
    hidden = s.turn(story, "I keep climbing.")
    assert hidden["disposition"] == "delivered", hidden

    audit = _rows(
        s,
        "SELECT visibility, dc, turn_id FROM rpg_roll_audit WHERE story_id = :s"
        " ORDER BY global_sequence",
        s=story,
    )
    assert [(a.visibility, a.dc) for a in audit] == [("shown", 15), ("hidden", 15)]
    assert [str(a.turn_id) for a in audit] == [shown["turn_id"], hidden["turn_id"]]
    assert "Athletics" not in json.dumps(hidden)  # hidden check filtered
    # Production binding on the selected path.
    keys = {c.api_key for c in s.provider.calls}
    assert len(keys) == 1 and (("byok" in next(iter(keys)).lower()) is (path == "byok"))
    deductions = s.deductions()
    if path == "hosted":
        assert {shown["turn_id"], hidden["turn_id"]} <= set(deductions)
    else:
        assert deductions == {}
    assert _eligibility(s, shown["turn_id"]) is True


@pytest.mark.parametrize("path", ["hosted", "byok"])
def test_player_roll_lifecycle_counts_only_the_narration_toward_the_summary(
    rpg_spine: Spine, path: str
) -> None:
    s = rpg_spine
    _seed(s, path)
    story = _rpg_story(s.client, dice=DiceHandling.PLAYER_ROLLS)
    # Eligible #1..#9: ordinary in-play turns with no mechanic.
    for i in range(1, ROLLING_SUMMARY_N):
        assert s.turn(story, f"Beat {i}: I scout the ruin.")["disposition"] == (
            "delivered"
        )
    wolf = _wolf(s.client, story, hp=30)
    _gm(
        s,
        _begin(s.client, story),
        _attack(
            s.client,
            story,
            wolf,
            "equipment.weapons.dagger",
            "Dagger attack",
            ability="strength",
        ),
    )
    announce = s.turn(story, "I stab the wolf.")
    assert announce["disposition"] == "delivered", announce["pipeline_error_summary"]
    assert _eligibility(s, announce["turn_id"]) is False  # a pending roll
    blocked = s.turn(story, "I run away.")
    assert blocked["disposition"] == "blocked_pending_roll"
    assert s.turn(story, "[OOC] how many hit points do I have?")["disposition"] == (
        "ooc_handled"
    )
    assert _rows(s, "SELECT 1 FROM rolling_summaries") == []

    view = _pending(s, story)["pending_roll"]
    damage = _submit_roll(s, story, view, 15)["pending_roll"]
    ready = _submit_roll(s, story, damage, 2)
    assert ready["interaction_phase"] == "ready_for_narration", ready
    resp = s.client.post(
        f"/api/stories/{story}/rpg/sequences/{ready['sequence_id']}/resume"
    )
    assert resp.status_code == 200, resp.text
    narrated = resp.json()
    assert narrated["disposition"] == "delivered", narrated
    assert _eligibility(s, narrated["turn_id"]) is True  # counted once

    # The resume narration is eligible #10: the summary commits with it.
    (summary,) = _rows(
        s,
        "SELECT compressed_through_turn_id, version_number FROM rolling_summaries"
        " WHERE story_id = :s",
        s=story,
    )
    assert (summary.compressed_through_turn_id, summary.version_number) == (
        narrated["turn_id"],
        1,
    )
    (call,) = s.provider.calls_for("rolling_summary")
    joined = "\n".join(call.texts)
    # Hidden adjudication state never reaches the summary pass, though the
    # resume Writer received its visibility-filtered views.
    assert "pending_player_roll_instruction" not in joined
    writer = "\n".join(s.provider.calls_for("writer")[-1].texts)
    assert "rpg_adjudication" in writer
    window = next(
        t for t in call.texts if t.startswith("[Rolling Summary Compression]")
    )
    assert window.count("--- turn ") == ROLLING_SUMMARY_N
    assert "I run away" not in window and "hit points" not in window
    # The resume narration's Sojourner input once; the announce never.
    assert window.count("Sojourner: I stab the wolf") == 1

    deductions = s.deductions()
    if path == "hosted":
        assert narrated["turn_id"] in deductions
    else:
        assert deductions == {}
    with s.session_factory() as session:
        assert (
            session.scalar(sa.select(sa.func.count(RollingSummaryORM.summary_id))) == 1
        )
