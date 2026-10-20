"""Every content table that can hold Story-owned rows has a registered,
FK-safe owning-service disposal (CRD Issue 22 §6, ADR-0004 amendment): a new
``story_id`` table or Turn reference cannot silently become a retained
exception."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.operations.disposal import NOT_STORY_CONTENT, REGISTRY

#: Removed by the ``stories`` cascade and verified by the sweep's ID check.
CASCADED = {"arcs"}


def test_every_story_or_turn_bearing_table_is_registered(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'c.db'}"
    upgrade_to_head(url)
    inspector = sa.inspect(sa.create_engine(url))
    bearing = set()
    for table in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns(table)}
        turn_cols = {c for c in columns if c == "turn_id" or c.endswith("_turn_id")}
        turn_fk = any(
            fk["referred_table"] == "turns" for fk in inspector.get_foreign_keys(table)
        )
        if "story_id" in columns or turn_cols or turn_fk:
            bearing.add(table)
    registered = {item.table for item in REGISTRY}
    assert bearing - NOT_STORY_CONTENT - CASCADED - registered == set()
    assert registered <= set(inspector.get_table_names())


def test_restrictive_children_precede_their_parents() -> None:
    order = [item.table for item in REGISTRY]
    for child, parent in (
        ("rpg_roll_audit", "turns"),
        ("rolling_summaries", "turns"),
        ("pending_roll_requests", "rpg_character_sheet_bases"),
        ("action_resolution_sequences", "rpg_character_sheet_bases"),
        ("rpg_session_states", "rpg_character_sheet_bases"),
        ("provider_refusal_log", "turns"),
        ("turns", "stories"),
    ):
        assert order.index(child) < order.index(parent), (child, parent)
