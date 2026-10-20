"""Terminal content disposal registry -- CRD Issue 22 §6, ADR-0004 amendment.

Every content table that holds Story-owned rows is listed here with its
owning service, the receipt class it reports under and how its rows are
selected: by plain ``story_id`` or by the pre-detachment Turn inventory. The
order is FK-safe (RESTRICT/NO ACTION children first; ``stories`` last, whose
cascade then removes Arcs, Chapters and Nodes). Trigger-protected tables go
through the guarded lifecycle path; nothing disables a trigger.
``tests/operations/test_disposal_registry.py`` fails when a content table
with a ``story_id`` column or a Turn reference is not registered.

Disposal runs in one content transaction and is followed by an independent
verification sweep over every ``story_id`` table, the inventoried Turns and
Turn-keyed rows, plus ``PRAGMA foreign_key_check``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.operations.lifecycle import dispose_rows

STORY = "story_id"
TURN = "turn_id"


@dataclass(frozen=True)
class Disposal:
    table: str
    owner: str
    receipt_class: str
    #: "story_id": rows whose story_id is inventoried; "turn_id": rows whose
    #: ``column`` names an inventoried Turn.
    selector: str
    column: str = "story_id"


#: FK-safe order. ``owner`` names the owning service (ADR record).
REGISTRY: tuple[Disposal, ...] = (
    Disposal("rpg_roll_audit", "rpg_adjudication", "rpg_audit", STORY),
    Disposal("action_resolution_events", "action_resolution", "rpg_audit", STORY),
    Disposal("rolling_summaries", "rolling_summary", "rolling_summaries", STORY),
    Disposal("pending_roll_requests", "action_resolution", "rpg_pending", STORY),
    Disposal("action_resolution_sequences", "action_resolution", "rpg_pending", STORY),
    Disposal("rpg_session_states", "rpg_session", "session_setup_state", STORY),
    Disposal("dnd5e_item_instances", "dnd5e_state", "character_sheets", STORY),
    Disposal("dnd5e_character_states", "dnd5e_state", "character_sheets", STORY),
    Disposal("dnd5e_binding_history", "dnd5e_state", "character_sheets", STORY),
    Disposal("dnd5e_adoption_requests", "dnd5e_state", "character_sheets", STORY),
    Disposal("dnd5e_creatures", "dnd5e_state", "character_sheets", STORY),
    Disposal("rpg_parties", "dnd5e_state", "character_sheets", STORY),
    Disposal("rpg_turn_coordination", "rpg_turns", "rpg_turn_state", STORY),
    Disposal("rpg_turn_edges", "rpg_turns", "rpg_turn_state", STORY),
    Disposal("rpg_turn_leases", "rpg_turns", "rpg_turn_state", STORY),
    Disposal(
        "rpg_turn_retrieval_markers", "retrieval_memory", "retrieval_markers", STORY
    ),
    Disposal(
        "rpg_character_sheet_bases", "character_sheets", "character_sheets", STORY
    ),
    Disposal(
        "branching_session_states", "branching_session", "session_setup_state", STORY
    ),
    Disposal("writing_session_states", "writing_session", "session_setup_state", STORY),
    Disposal("world_states", "story_state", "story_state", STORY),
    Disposal("character_states", "story_state", "story_state", STORY),
    Disposal("sb_settings", "story_bible", "story_bible", STORY),
    Disposal("sb_cast_entries", "story_bible", "story_bible", STORY),
    Disposal("sb_locked_facts", "story_bible", "story_bible", STORY),
    Disposal("sb_forbidden_facts", "story_bible", "story_bible", STORY),
    Disposal("sb_events", "story_bible", "story_bible", STORY),
    Disposal("sb_relationship_ledger", "story_bible", "story_bible", STORY),
    Disposal("sb_unresolved_threads", "story_bible", "story_bible", STORY),
    Disposal("sb_provisional_staging", "story_bible", "story_bible", STORY),
    Disposal("sb_dynamic_field_history", "story_bible", "story_bible_history", STORY),
    Disposal("provider_refusal_log", "provider_router", "provider_refusal_rows", TURN),
    Disposal("turns", "story_crud", "turns", TURN),
    Disposal("stories", "story_crud", "stories", STORY),
)

#: Tables whose ``story_id``/Turn columns are not Story-owned content.
NOT_STORY_CONTENT = frozenset({"entitlement_event"})


def _where(
    item: Disposal, stories: list[str], turns: list[str]
) -> sa.ColumnElement[bool] | None:
    if item.selector == STORY:
        return sa.column(item.column).in_(stories) if stories else None
    column = "turn_id" if item.table != "turns" else "turn_id"
    return sa.column(column).in_(turns) if turns else None


def dispose_story_content(
    session: Session, stories: Iterable[str], turns: Iterable[str]
) -> dict[str, int]:
    """Remove every registered row of the inventoried Stories/Turns in the
    caller's transaction; returns rows removed per receipt class."""
    story_list, turn_list = sorted(set(stories)), sorted(set(turns))
    counts: dict[str, int] = {}
    for item in REGISTRY:
        removed = dispose_rows(session, item.table, _where(item, story_list, turn_list))
        counts[item.receipt_class] = counts.get(item.receipt_class, 0) + removed
    return counts


def remaining_story_content(
    session: Session,
    stories: Iterable[str],
    turns: Iterable[str],
    *,
    extra_ids: dict[str, Iterable[str]] | None = None,
) -> dict[str, int]:
    """Independent sweep: rows still present per table for the inventory --
    every table with a ``story_id`` column, every inventoried Turn and
    Turn-keyed row, and the inventoried Arc/Chapter/Node IDs. Empty means
    verified."""
    story_list, turn_list = sorted(set(stories)), sorted(set(turns))
    remaining: dict[str, int] = {}
    inspector = sa.inspect(session.get_bind())
    for table in inspector.get_table_names():
        if table in NOT_STORY_CONTENT:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        conditions = []
        if "story_id" in columns and story_list:
            conditions.append(sa.column("story_id").in_(story_list))
        if turn_list:
            for col in sorted(columns):
                if col == "turn_id" or col.endswith("_turn_id"):
                    conditions.append(sa.column(col).in_(turn_list))
        if not conditions:
            continue
        count = session.scalar(
            sa.select(sa.func.count())
            .select_from(sa.table(table))
            .where(sa.or_(*conditions))
        )
        if count:
            remaining[table] = int(count)
    for table, ids in (extra_ids or {}).items():
        id_list = sorted(set(ids))
        if not id_list:
            continue
        key = {"arcs": "arc_id", "chapters": "chapter_id", "nodes": "node_id"}[table]
        count = session.scalar(
            sa.select(sa.func.count())
            .select_from(sa.table(table))
            .where(sa.column(key).in_(id_list))
        )
        if count:
            remaining[table] = int(count)
    violations = session.execute(sa.text("PRAGMA foreign_key_check")).all()
    if violations:
        remaining["foreign_key_check"] = len(violations)
    return remaining


def referenced_turn_ids(session: Session, stories: Iterable[str]) -> set[str]:
    """Turn IDs referenced from Story-scoped rows: attribute Turns that a
    Node link would no longer reach (``SET NULL`` orphans)."""
    story_list = sorted(set(stories))
    if not story_list:
        return set()
    found: set[str] = set()
    inspector = sa.inspect(session.get_bind())
    for table in inspector.get_table_names():
        if table in NOT_STORY_CONTENT:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if "story_id" not in columns:
            continue
        for col in sorted(columns):
            if col == "turn_id" or col.endswith("_turn_id"):
                found |= {
                    str(v)
                    for v in session.scalars(
                        sa.select(sa.column(col, sa.String))
                        .select_from(sa.table(table))
                        .where(
                            sa.column("story_id").in_(story_list),
                            sa.column(col).is_not(None),
                        )
                    )
                }
    return found
