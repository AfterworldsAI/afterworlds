#!/usr/bin/env python
"""CLI script -- seed the M1 mill-yard encounter into an RPG story (issue #211).

For hand testing and the first player demo through the normal Sojourner
interface: it makes the story's active scene the mill yard (mapper.fixture),
with the story's own character as the hero token, so the map view and drawn
or spoken moves work on it. The record is written only through the mapper's
store; a place that already has a record is resumed, never replaced.

Creatures are passed in by reference (``--goblin-ref creature:<id>``). The
Rules Package holds no creature hit-point fact to start an instance from, so
this script creates no creature records itself; without a reference a token
carries the fixture's plain label ref.

Usage
-----
    python scripts/seed_mapper_encounter.py --db-url sqlite:///./afterworlds.db \
        --story-id <uuid> [--goblin-ref creature:<id>] [--lurker-ref creature:<id>]
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from afterworlds.mapper.models import MapRecord


def seed(
    session: Session,
    story_id: UUID,
    *,
    now: datetime,
    goblin_ref: str | None = None,
    lurker_ref: str | None = None,
) -> MapRecord:
    """Begin (or resume) the mill yard as *story_id*'s active scene."""
    from afterworlds.mapper import fixture, store
    from afterworlds.persistence.crud.session_state import (
        get_rpg_session_state_by_story,
    )

    state = get_rpg_session_state_by_story(session, story_id)
    if state is None:
        raise SystemExit(f"story {story_id} has no RPG session (is it an RPG story?)")
    defaults = fixture.FixtureRefs()
    refs = fixture.FixtureRefs(
        hero_ref=f"character:{state.character_sheet_id}",
        goblin_ref=goblin_ref or defaults.goblin_ref,
        lurker_ref=lurker_ref or defaults.lurker_ref,
    )
    return store.begin_scene(
        session,
        story_id=story_id,
        place_key=fixture.PLACE_KEY,
        label=fixture.LABEL,
        snapshot=fixture.build(refs),
        seed=fixture.SEED,
        now=now,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--story-id", required=True, type=UUID)
    parser.add_argument("--goblin-ref")
    parser.add_argument("--lurker-ref")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    import afterworlds.persistence.orm.spatial  # noqa: F401
    from afterworlds.persistence.database import create_engine, create_session_factory

    session = create_session_factory(create_engine(args.db_url))()
    try:
        record = seed(
            session,
            args.story_id,
            now=datetime.now(UTC),
            goblin_ref=args.goblin_ref,
            lurker_ref=args.lurker_ref,
        )
        session.commit()
    finally:
        session.close()
    print(
        f"active scene {record.label!r}: map {record.map_id},"
        f" revision {record.revision}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
