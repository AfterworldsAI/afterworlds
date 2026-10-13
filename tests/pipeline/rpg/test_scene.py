"""CRD Issue 15c — the mechanical scene: every id a proposal may name is put
in front of the GameMaster, in a GameMaster-only block after the unchanged
stable prefix; no target number or rolled interval is shown."""

from __future__ import annotations

import json

from afterworlds.models.dnd5e_state import (
    ActiveTurn,
    SubjectReference,
    TurnCoordination,
)
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.scene import render
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from tests.pipeline.rpg.test_adjudication_service import _make_assembled
from tests.pipeline.rpg.test_weapon_attacks import CLUB, _attacker, _creature
from tests.pipeline.rpg.test_zero_hp_lifecycle import _knocked_out, _stable


def _scene(text: str) -> dict[str, object]:
    return json.loads(text.split("\n", 1)[1])  # type: ignore[no-any-return]


def test_the_scene_lists_every_nameable_id_and_no_target_number() -> None:
    actor = _attacker(CLUB)
    wolf, knocked, stable = _creature(), _knocked_out(), _stable(interval=3)
    active = TurnCoordination(
        active=ActiveTurn(
            subject=SubjectReference(kind="creature", subject_id=wolf.subject_id),
            instance=2,
        )
    )
    text = render(actor, [wolf, knocked, stable], active)
    scene = _scene(text)
    subjects = scene["subjects"]
    assert isinstance(subjects, list)
    me, w, k, s = subjects
    assert me["acting"] and me["weapons"] == [
        {"item_id": str(CLUB.item_id), "record": CLUB.record_key, "equipped": True}
    ]
    assert w["subject_id"] == str(wolf.subject_id) and w["attack_entries"] == ["Bite"]
    assert k["conditions"][0]["instance_id"] == "ko"
    assert s["zero_hp"] == "stable" and s["stable_recovery_instance_id"] == "rec"
    assert scene["active_turn"] == {
        "kind": "creature",
        "subject_id": str(wolf.subject_id),
        "spent": [],
    }
    # No AC, DC, modifier or rolled interval.
    assert '"interval"' not in text and "armor" not in text.lower()


def test_the_scene_follows_the_unchanged_stable_prefix() -> None:
    service = RpgAdjudicationPassService(adapter=D20RulesSystemAdapter())
    context = _make_assembled()
    plain = service._render(context)  # noqa: SLF001
    with_scene = service._render(context, "Mechanical scene: {}")  # noqa: SLF001
    prefix = len(plain.rendered_blocks) - 1  # all but the current input
    assert with_scene.rendered_blocks[:prefix] == plain.rendered_blocks[:prefix]
    assert with_scene.rendered_blocks[prefix].text == "Mechanical scene: {}"
