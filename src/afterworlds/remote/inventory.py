"""Account-wide ownership inventory -- prerequisite #205 §2, ADR-0004 amendment.

``account_resources`` maps Story roots to accounts and survives parent
detachment; every other owned row hangs off its Story root. Turns carry only
a nullable ``node_id``, so they are attributable only while their Node links
exist. The accepted ADR-0004 amendment therefore requires the inventory to be
taken **before** detachment, and terminal erasure (CRD Issue 22) is the only
detaching operation: no ordinary remote path deletes a Story, Arc, Chapter or
Node (``tests/api/test_remote_inventory.py`` guards that). This read seam
returns the full owned-ID inventory for CRD Issue 22 to persist in its request
records before it detaches anything; it writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.persistence.orm.node import NodeORM, TurnORM
from afterworlds.persistence.orm.ownership import AccountResourceORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM


@dataclass(frozen=True)
class AccountInventory:
    """Every ID an account owns, taken from the live links at one moment."""

    story_ids: tuple[str, ...]
    arc_ids: tuple[str, ...]
    chapter_ids: tuple[str, ...]
    node_ids: tuple[str, ...]
    turn_ids: tuple[str, ...]
    #: Rows per content table keyed directly by a plain ``story_id`` column.
    story_id_rows: dict[str, int]


def account_inventory(session: Session, account_id: str) -> AccountInventory:
    """Inventory every Story the account has ever owned (retired mappings
    included) and everything linked beneath those Story roots."""
    stories = sorted(
        session.scalars(
            sa.select(AccountResourceORM.resource_id).where(
                AccountResourceORM.account_id == account_id,
                AccountResourceORM.resource_type == "story",
            )
        )
    )
    arcs = sorted(
        session.scalars(sa.select(ArcORM.arc_id).where(ArcORM.story_id.in_(stories)))
    )
    chapters = sorted(
        session.scalars(
            sa.select(ChapterORM.chapter_id).where(ChapterORM.arc_id.in_(arcs))
        )
    )
    nodes = sorted(
        session.scalars(
            sa.select(NodeORM.node_id).where(NodeORM.chapter_id.in_(chapters))
        )
    )
    turns = sorted(
        session.scalars(sa.select(TurnORM.turn_id).where(TurnORM.node_id.in_(nodes)))
    )
    rows: dict[str, int] = {}
    inspector = sa.inspect(session.get_bind())
    for table in inspector.get_table_names():
        if stories and "story_id" in {c["name"] for c in inspector.get_columns(table)}:
            count = session.scalar(
                sa.select(sa.func.count())
                .select_from(sa.table(table))
                .where(sa.column("story_id").in_(stories))
            )
            if count:
                rows[table] = int(count)
    return AccountInventory(
        story_ids=tuple(stories),
        arc_ids=tuple(arcs),
        chapter_ids=tuple(chapters),
        node_ids=tuple(nodes),
        turn_ids=tuple(turns),
        story_id_rows=rows,
    )
