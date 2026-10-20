"""CRD Issue 22 (#206, bounded verification concern): an in-play RPG Story's
export carries the player's own visible state (character sheet HUD) and
setup view, exactly as the app shows them, and no hidden mechanics.

Reuses the #205 provisioned-Rules deployment fixture unchanged (expensive:
one published-release build per run).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.api._remote import make_remote
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import gm
from tests.ingestion.mechanical.test_remote_rpg_on_published_release import (
    _in_play,
    provisioned,
)
from tests.operations._data import plant, unzip

__all__ = ["gm", "provisioned"]  # fixtures used by pytest


def test_in_play_rpg_story_export_matches_the_players_view(
    provisioned: Path, gm: list[list[dict[str, Any]]]
) -> None:
    remote = make_remote(provisioned)
    try:
        a = remote.enroll("a@example.test")
        remote.seed_hosted(remote.account_id(a))
        story = a.post(
            "/api/stories",
            json={"title": "Isles", "mode": "rpg", "character_name": "Ilse"},
        ).json()["story_id"]
        turn = a.post(
            f"/api/stories/{story}/turns",
            json={"user_input": "A storm-wracked archipelago."},
        )
        assert turn.status_code == 200, turn.text
        _in_play(remote, story)
        plant(
            remote.app.state.session_factory,
            story,
            "RPGHIDDENMARK",
            orphan_marker="RPGORPHANOK",
        )
        shown = a.get(f"/api/stories/{story}/visible-state").json()["visible_state"]
        assert shown is not None  # the in-play character sheet HUD
        setup = a.get(f"/api/stories/{story}/setup").json()["setup_state"]

        staff = remote.staff()
        rid = a.post(
            "/api/data-requests",
            json={"kind": "export", "scope": "story", "story_id": story},
        ).json()["request_id"]
        view = staff.get(f"/api/admin/data-requests/{rid}").json()
        staff.post(
            f"/api/admin/data-requests/{rid}/approve",
            json={"expected_revision": view["revision"], "reason": "verified owner"},
        )
        view = staff.get(f"/api/admin/data-requests/{rid}").json()
        done = staff.post(
            f"/api/admin/data-requests/{rid}/execute",
            json={"expected_revision": view["revision"]},
        ).json()
        assert done["state"] == "completed", done
        files = unzip(a.get(f"/api/data-requests/{rid}/artifact").content)
        record = files[f"stories/{story}/story.json"]
        assert record["story"]["mode"] == "rpg"
        assert record["visible_state"] == shown
        assert record["setup_state"] == setup
        everything = str(files)
        assert "RPGHIDDENMARK" not in everything
        assert "RPGORPHANOK" in everything
        codes = {e["code"] for e in files["manifest.json"]["exclusions"]}
        assert "hidden_rpg_mechanics" in codes
    finally:
        remote.close()
