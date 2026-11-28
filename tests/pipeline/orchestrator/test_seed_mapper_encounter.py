"""The M1 seeding script (issue #211): the mill yard becomes the story's
active scene with the story's own character as the hero, and seeding twice
resumes rather than replaces it."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import pytest

from afterworlds.mapper import fixture, store
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.session_state import create_rpg_session_state
from tests.persistence.conftest import make_base_sheet
from tests.pipeline.orchestrator.test_spatial_turn import (
    NOW,
    _seed_story,
    _session_state,
)

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "seed_mapper_encounter.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("seed_mapper_encounter", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seeding_makes_the_mill_yard_the_active_scene(session_factory: Any) -> None:
    script = _load()
    story_id, _ = _seed_story(session_factory)
    with session_factory() as s:
        sheet = make_base_sheet(str(story_id))
        create_rpg_base_sheet(s, sheet)
        state = _session_state(story_id).model_copy(
            update={"character_sheet_id": sheet.sheet_id}
        )
        create_rpg_session_state(s, state)
        first = script.seed(s, story_id, now=NOW, goblin_ref="creature:abc")
        s.commit()
    with session_factory() as s:
        record, revision = store.active_scene(s, story_id)  # type: ignore[misc]
        again = script.seed(s, story_id, now=NOW)
        s.commit()
    assert record.map_id == first.map_id == again.map_id
    hero = revision.snapshot.token(fixture.HERO)
    goblin = revision.snapshot.token(fixture.GOBLIN)
    assert hero is not None and hero.ref == f"character:{state.character_sheet_id}"
    assert goblin is not None and goblin.ref == "creature:abc"


def test_seeding_needs_an_rpg_story(session_factory: Any) -> None:
    with session_factory() as s, pytest.raises(SystemExit, match="no RPG session"):
        _load().seed(s, uuid4(), now=NOW)
