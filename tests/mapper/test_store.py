"""The spatial record's store: revisions, scenes and the migration (#211)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.spatial  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.mapper import fixture, store
from afterworlds.mapper.models import MarkExplored, MoveToken
from afterworlds.mapper.updates import MAP_MOVED_ON, UpdateRefused
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base

NOW = datetime(2026, 11, 27, tzinfo=UTC)
_REPO = Path(__file__).resolve().parents[2]


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sess = create_session_factory(engine)()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def _story(session: Session) -> UUID:
    story = Story(title="mill", mode=StoryMode.RPG, created_at=NOW, updated_at=NOW)
    create_story(session, story)
    return story.story_id


def test_begin_stage_and_consult(session: Session) -> None:
    story_id = _story(session)
    assert store.active_scene(session, story_id) is None
    record = store.begin_scene(
        session,
        story_id=story_id,
        place_key=fixture.PLACE_KEY,
        label=fixture.LABEL,
        snapshot=fixture.build(),
        seed=fixture.SEED,
        now=NOW,
    )
    assert record.revision == 0 and record.status == "active"
    found = store.active_scene(session, story_id)
    assert found is not None and found[1].snapshot == fixture.build()
    rev = store.stage_revision(
        session,
        map_id=record.map_id,
        updates=[MoveToken(base_revision=0, token_id="hero", route=((1, 4), (2, 4)))],
        base_revision=0,
        now=NOW,
    )
    assert rev.revision == 1 and rev.parent_revision == 0
    assert rev.snapshot.token("hero").square == (2, 4)  # type: ignore[union-attr]
    again = store.active_scene(session, story_id)
    assert again is not None and again[0].revision == 1 and again[1] == rev
    assert [r.revision for r in store.revisions(session, record.map_id)] == [0, 1]


def test_a_stale_or_refused_update_stages_nothing(session: Session) -> None:
    story_id = _story(session)
    record = store.begin_scene(
        session,
        story_id=story_id,
        place_key="p",
        label="p",
        snapshot=fixture.build(),
        seed=1,
        now=NOW,
    )
    with pytest.raises(UpdateRefused) as exc:
        store.stage_revision(
            session,
            map_id=record.map_id,
            updates=[MarkExplored(base_revision=0, squares=((0, 0),))],
            base_revision=3,
            now=NOW,
        )
    assert exc.value.reason == MAP_MOVED_ON
    with pytest.raises(UpdateRefused):
        store.stage_revision(
            session,
            map_id=record.map_id,
            updates=[
                MoveToken(base_revision=0, token_id="hero", route=((1, 4), (9, 4)))
            ],
            base_revision=0,
            now=NOW,
        )
    with pytest.raises(UpdateRefused):
        store.stage_revision(
            session, map_id=uuid4(), updates=[], base_revision=0, now=NOW
        )
    assert [r.revision for r in store.revisions(session, record.map_id)] == [0]


def test_scenes_resume_by_place_key(session: Session) -> None:
    story_id = _story(session)
    mill = store.begin_scene(
        session,
        story_id=story_id,
        place_key="mill",
        label="mill",
        snapshot=fixture.build(),
        seed=1,
        now=NOW,
    )
    store.stage_revision(
        session,
        map_id=mill.map_id,
        updates=[MoveToken(base_revision=0, token_id="hero", route=((1, 4), (2, 4)))],
        base_revision=0,
        now=NOW,
    )
    road = store.begin_scene(
        session,
        story_id=story_id,
        place_key="road",
        label="road",
        snapshot=fixture.build(),
        seed=2,
        now=NOW,
    )
    active = store.active_scene(session, story_id)
    assert active is not None and active[0].map_id == road.map_id
    back = store.resume_scene(session, story_id=story_id, place_key="mill")
    assert back is not None and back.map_id == mill.map_id and back.revision == 1
    active = store.active_scene(session, story_id)
    assert active is not None and active[0].map_id == mill.map_id
    assert active[1].snapshot.token("hero").square == (2, 4)  # type: ignore[union-attr]
    # Beginning a place that has a record resumes it; nothing is replaced.
    same = store.begin_scene(
        session,
        story_id=story_id,
        place_key="mill",
        label="other",
        snapshot=fixture.build(with_hidden=False),
        seed=9,
        now=NOW,
    )
    assert same.map_id == mill.map_id and same.revision == 1
    assert store.resume_scene(session, story_id=story_id, place_key="nowhere") is None
    store.archive_map(session, mill.map_id)
    assert store.active_scene(session, story_id) is None


def test_migration_0047_matches_the_orm(tmp_path: Path) -> None:
    db = tmp_path / "store.db"
    cfg = Config(str(_REPO / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(_REPO / "src" / "afterworlds" / "migrations" / "content")
    )
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    command.upgrade(cfg, "0047")
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    inspector = sa.inspect(engine)
    for table in ("spatial_maps", "spatial_map_revisions"):
        assert sorted(c["name"] for c in inspector.get_columns(table)) == sorted(
            c.name for c in Base.metadata.tables[table].columns
        )
    engine.dispose()
    command.downgrade(cfg, "0046")
    engine = sa.create_engine(f"sqlite:///{db.as_posix()}")
    assert "spatial_maps" not in sa.inspect(engine).get_table_names()
    engine.dispose()


def test_story_disposal_removes_the_spatial_record(tmp_path: Path) -> None:
    """Deleting a Story removes its scenes and their revisions, including a
    revision that points at one of its Turns (CRD Issue 22 disposal)."""
    from afterworlds.api.db_bootstrap import upgrade_to_head
    from afterworlds.models.enums import IntentType
    from afterworlds.models.node import (
        BranchingNodeMetadata,
        Node,
        NodeMetadata,
        StateDelta,
    )
    from afterworlds.models.story import Arc, Chapter
    from afterworlds.operations.disposal import (
        dispose_story_content,
        remaining_story_content,
    )
    from afterworlds.persistence.crud.node import create_node
    from afterworlds.persistence.crud.story import create_arc, create_chapter

    url = f"sqlite:///{(tmp_path / 'c.db').as_posix()}"
    upgrade_to_head(url)
    engine = create_engine(url)
    with create_session_factory(engine)() as s:
        story_id = _story(s)
        arc = Arc(story_id=story_id, title="Arc", order=0)
        create_arc(s, arc)
        chapter = Chapter(arc_id=arc.arc_id, title="Chapter", order=0)
        create_chapter(s, chapter)
        node = Node(
            chapter_id=chapter.chapter_id,
            content="",
            state_delta=StateDelta(),
            branching_logic=[],
            intent_type=IntentType.IN_CHARACTER_ACTION,
            metadata=NodeMetadata(timestamp=NOW),
            mode_metadata=BranchingNodeMetadata(),
        )
        create_node(s, node)
        turn_id = str(uuid4())
        s.execute(
            sa.text(
                "INSERT INTO turns (turn_id, node_id, user_input, assistant_output,"
                " timestamp, intent_classification) VALUES (:t, :n, 'go', 'went',"
                " '2026-11-27T00:00:00+00:00', 'in_character_action')"
            ),
            {"t": turn_id, "n": str(node.node_id)},
        )
        record = store.begin_scene(
            s,
            story_id=story_id,
            place_key=fixture.PLACE_KEY,
            label=fixture.LABEL,
            snapshot=fixture.build(),
            seed=fixture.SEED,
            now=NOW,
        )
        store.stage_revision(
            s,
            map_id=record.map_id,
            updates=[
                MoveToken(base_revision=0, token_id="hero", route=((1, 4), (2, 4)))
            ],
            base_revision=0,
            now=NOW,
            turn_id=UUID(turn_id),
        )
        s.commit()

        dispose_story_content(s, [str(story_id)], [turn_id])
        s.commit()
        assert remaining_story_content(s, [str(story_id)], [turn_id]) == {}
        for table in ("spatial_maps", "spatial_map_revisions"):
            count = s.scalar(sa.text(f"SELECT count(*) FROM {table}"))  # noqa: S608
            assert count == 0, table
    engine.dispose()
