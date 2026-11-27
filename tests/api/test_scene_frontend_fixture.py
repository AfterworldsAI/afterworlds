"""The map view's test fixture is the server's own player view of the M1
encounter (issue #211), so the browser tests draw what the server sends.

Regenerate after a deliberate view change with::

    AW_WRITE_SCENE_FIXTURE=1 pytest tests/api/test_scene_frontend_fixture.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from afterworlds.mapper import fixture
from afterworlds.mapper.views import player_snapshot, player_view
from afterworlds.pipeline.rpg.movement import MoverProfile, allowance
from tests.pipeline.rpg.movement_support import rules

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "src"
    / "fixtures"
    / "millYardScene.json"
)


def _view() -> dict[str, object]:
    player = player_snapshot(fixture.build())
    hero = MoverProfile(token_id=fixture.HERO, walk_ft=30, strength=14)
    view = player_view(
        player,
        viewer=fixture.HERO,
        map_id="00000000-0000-0000-0000-000000000211",
        revision=4,
        label=fixture.LABEL,
        allowance=allowance(player, hero, rules()),
    )
    return {**view, "schema_version": 1}


def test_the_browser_fixture_is_the_servers_view() -> None:
    expected = json.dumps(_view(), indent=2, sort_keys=True) + "\n"
    if os.environ.get("AW_WRITE_SCENE_FIXTURE") == "1":
        FIXTURE.write_text(expected, encoding="utf-8")
    assert FIXTURE.read_text(encoding="utf-8") == expected
