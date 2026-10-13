"""The creature roster — CRD Issue 15c (codex-c7-recert-coverage-review):
code executes exactly the admitted creature entries and Multiattack
selections, and refuses every other entry before any die."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CAPABILITY = (
    Path(__file__).resolve().parents[3]
    / ".claude/review-notes/issue-15c-implementation/candidate-c5/capability.json"
)

#: C5 blockers settled since by an approved contract, executed in code; the
#: value names the contract and the test proving it.
SETTLED: dict[str, str] = {
    "Pack Tactics": "bystanders, named allies "
    "(test_creature_attacks::test_pack_tactics_needs_a_named_ally_that_can_act)",
    "Recharge needs explicit start-of-turn authority": "OD-15c-2 actor edges, "
    "Recharge at the creature's turn start (test_creature_effects)",
    "area membership needs explicit position authority": "OD-15c-1 targets "
    "selection (test_creature_effects)",
    "range needs explicit position authority": "OD-15c-1 range band "
    "(test_creature_attacks)",
    "timed effect needs explicit actor-turn authority": "OD-15c-2 turn-bounded "
    "condition ends (test_creature_effects)",
    "timed/linked effect needs explicit actor-turn authority": "OD-15c-2 "
    "turn-bounded hit-effect ends (test_creature_attacks)",
}


def _blockers(entry: dict[str, Any]) -> set[str]:
    out = set(entry.get("blocked_by") or ())
    for d in entry.get("dependencies") or ():
        out.add(d.get("cluster") or d["detail"])
    return out


def admitted(entries: dict[str, Any]) -> set[str]:
    """``template:entry`` for every attack or save effect C5 marks
    executable, or whose every blocker is :data:`SETTLED`."""
    out = set()
    for key, entry in entries.items():
        if entry.get("entry_kind") not in ("attack", "save_effect"):
            continue
        blockers = _blockers(entry)
        if entry.get("executable_once_accepted") or (
            blockers and blockers <= SETTLED.keys()
        ):
            template, name = key.split("#")[0], key.split(":", 1)[1]
            out.add(f"{template}:{name}")
    return out


def test_the_roster_is_generated_from_the_accepted_capability() -> None:
    from afterworlds.pipeline.rpg import roster

    data = CAPABILITY.read_bytes()
    assert hashlib.sha256(data).hexdigest() == roster.CAPABILITY_SHA256
    assert admitted(json.loads(data)["entries"]) == roster.EXECUTABLE
