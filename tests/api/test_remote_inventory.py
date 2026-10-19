"""Prerequisite #205 §2: account-wide ownership is enumerable before any
detachment, and no ordinary path detaches Story children."""

from __future__ import annotations

import ast
from pathlib import Path

from afterworlds.remote.inventory import account_inventory
from tests.api._remote import RemoteHarness
from tests.api.test_remote_isolation import _branching_in_play, _seed_hosted

SRC = Path(__file__).resolve().parents[2] / "src" / "afterworlds"
_DETACHING = {"delete_story", "delete_arc", "delete_chapter", "delete_node"}


def test_inventory_covers_every_owned_story_and_turn(remote: RemoteHarness) -> None:
    a = remote.enroll("a@example.test")
    b = remote.enroll("b@example.test")
    account = remote.account_id(a)
    _seed_hosted(remote, account)
    sid = _branching_in_play(a)
    assert (
        a.post(f"/api/stories/{sid}/turns", json={"user_input": "Hi."}).status_code
        == 200
    )
    other = a.post("/api/stories", json={"title": "2", "mode": "rpg"}).json()[
        "story_id"
    ]
    b.post("/api/stories", json={"title": "B", "mode": "branching"})
    with remote.app.state.session_factory() as s:
        inv = account_inventory(s, account)
    assert set(inv.story_ids) == {sid, other}
    assert inv.arc_ids and inv.chapter_ids and inv.node_ids
    assert len(inv.turn_ids) >= 2  # the opening and the played turn
    assert inv.story_id_rows  # plain story_id tables (sessions, RPG state, ...)


def test_no_ordinary_path_detaches_story_children() -> None:
    """Only the persistence CRUD layer defines these deletions; nothing in the
    product calls them, so Turns are orphaned only by terminal erasure."""
    offenders = []
    for path in SRC.rglob("*.py"):
        if "persistence" in path.parts and "crud" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == (
                "afterworlds.persistence.crud.story"
            ):
                offenders += [
                    f"{path.name}:{a.name}" for a in node.names if a.name in _DETACHING
                ]
            if isinstance(node, ast.ImportFrom) and node.module == (
                "afterworlds.persistence.crud.node"
            ):
                offenders += [
                    f"{path.name}:{a.name}" for a in node.names if a.name in _DETACHING
                ]
    assert offenders == []
