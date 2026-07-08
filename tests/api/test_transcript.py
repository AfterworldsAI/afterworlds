from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from afterworlds.models.enums import IntentType
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_turn
from afterworlds.persistence.crud.story import get_story


def _create_story(client) -> str:  # type: ignore[no-untyped-def]
    resp = client.post("/api/stories", json={"title": "T", "mode": "writing"})
    assert resp.status_code == 201, resp.text
    return resp.json()["story_id"]  # type: ignore[no-any-return]


def _seed_turn(
    client,  # type: ignore[no-untyped-def]
    story_id: str,
    *,
    when: datetime,
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> UUID:
    """Insert a Turn directly via CRUD, tied to the story's turn-anchor node.

    Turn submission's actual DB write is the real orchestrator's job
    (covered by tests/pipeline/orchestrator/); this route only reads
    whatever turns already exist, so seeding directly (not through a
    stubbed-orchestrator POST, which writes nothing) is the correct test
    boundary for the transcript GET.
    """
    session = client.app.state.session_factory()
    try:
        story = get_story(session, UUID(story_id))
        assert story is not None
        # The anchor node was created at story-creation time (Phase 1).
        from afterworlds.persistence.orm.node import NodeORM
        from afterworlds.persistence.orm.story import ArcORM, ChapterORM

        node_id = (
            session.query(NodeORM.node_id)
            .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
            .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
            .filter(ArcORM.story_id == story_id)
            .scalar()
        )
        assert node_id is not None
        turn = Turn(
            user_input="input",
            assistant_output="output",
            timestamp=when,
            intent_classification=intent,
            node_id=UUID(node_id),
        )
        create_turn(session, turn)
        session.commit()
        return turn.turn_id
    finally:
        session.close()


def test_transcript_empty_for_new_story(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.get(f"/api/stories/{story_id}/turns")
    assert resp.status_code == 200
    assert resp.json()["turns"] == []


def test_transcript_reflects_seeded_turns_in_persisted_order(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    turn_id_1 = _seed_turn(client, story_id, when=datetime(2026, 1, 1, tzinfo=UTC))
    turn_id_2 = _seed_turn(
        client,
        story_id,
        when=datetime(2026, 1, 2, tzinfo=UTC),
        intent=IntentType.OOC,
    )

    resp = client.get(f"/api/stories/{story_id}/turns")
    assert resp.status_code == 200
    turns = resp.json()["turns"]
    assert [t["turn_id"] for t in turns] == [str(turn_id_1), str(turn_id_2)]
    assert turns[1]["intent_classification"] == "ooc"


def test_transcript_missing_story_404(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(f"/api/stories/{uuid4()}/turns")
    assert resp.status_code == 404


def test_transcript_rejects_invalid_limit(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.get(f"/api/stories/{story_id}/turns", params={"limit": 0})
    assert resp.status_code == 422


def test_transcript_turn_items_carry_schema_version(client) -> None:  # type: ignore[no-untyped-def]
    # Round 10 remediation (PR #126 P2): TranscriptTurnDTO (embedded in
    # TranscriptResponse) lacked schema_version, unlike every other DTO.
    story_id = _create_story(client)
    _seed_turn(client, story_id, when=datetime(2026, 1, 1, tzinfo=UTC))

    resp = client.get(f"/api/stories/{story_id}/turns")
    assert resp.status_code == 200
    turns = resp.json()["turns"]
    assert len(turns) == 1
    assert turns[0]["schema_version"] == 1


def test_transcript_latest_returns_most_recent_turns_in_chronological_order(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # Round 11 remediation (PR #126 P2): the default GET .../turns page is
    # the FIRST `limit` turns (oldest-first, offset 0) -- once a story has
    # more than the default page size, a plain refresh always re-shows the
    # oldest turns and never surfaces newly delivered output, even though it
    # was correctly persisted. latest=true must return the most recent
    # `limit` turns, still in chronological (oldest-to-newest) order within
    # that page.
    story_id = _create_story(client)
    turn_ids = [
        _seed_turn(
            client,
            story_id,
            when=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i),
        )
        for i in range(1, 61)
    ]

    resp = client.get(
        f"/api/stories/{story_id}/turns", params={"limit": 50, "latest": "true"}
    )
    assert resp.status_code == 200, resp.text
    turns = resp.json()["turns"]
    assert len(turns) == 50
    # The latest 50 of 60 turns = turns[10:60] (0-indexed), still oldest-first.
    assert [t["turn_id"] for t in turns] == [str(tid) for tid in turn_ids[10:60]]


def test_transcript_after_turn_51_latest_page_includes_it(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # Round 11 remediation (PR #126 P2) regression: submitting turn 51 (past
    # the default 50-turn page) must be visible on the very next latest-page
    # refresh.
    story_id = _create_story(client)
    for i in range(1, 51):
        _seed_turn(
            client,
            story_id,
            when=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i),
        )
    turn_51_id = _seed_turn(client, story_id, when=datetime(2026, 1, 2, 0, tzinfo=UTC))

    resp = client.get(
        f"/api/stories/{story_id}/turns", params={"limit": 50, "latest": "true"}
    )
    assert resp.status_code == 200, resp.text
    turns = resp.json()["turns"]
    assert turns[-1]["turn_id"] == str(turn_51_id)


def test_transcript_latest_rejects_nonzero_offset(client) -> None:  # type: ignore[no-untyped-def]
    story_id = _create_story(client)
    resp = client.get(
        f"/api/stories/{story_id}/turns",
        params={"latest": "true", "offset": 10},
    )
    assert resp.status_code == 422


def test_transcript_default_pagination_unchanged_by_latest_support(
    client,  # type: ignore[no-untyped-def]
) -> None:
    # Explicit oldest-first limit/offset pagination (no latest param) must
    # be unaffected by adding latest=true support.
    story_id = _create_story(client)
    turn_ids = [
        _seed_turn(
            client,
            story_id,
            when=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i),
        )
        for i in range(1, 6)
    ]

    resp = client.get(
        f"/api/stories/{story_id}/turns", params={"limit": 2, "offset": 1}
    )
    assert resp.status_code == 200, resp.text
    turns = resp.json()["turns"]
    assert [t["turn_id"] for t in turns] == [str(tid) for tid in turn_ids[1:3]]
