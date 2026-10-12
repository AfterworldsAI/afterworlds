"""Story-scoped dynamic-field history (#50): writers, reads and retention."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from afterworlds.models.enums import StoryMode, TargetDomain
from afterworlds.models.extractor import ExtractorProposalSet, TransientStateProposal
from afterworlds.models.story import Story
from afterworlds.persistence.crud.story import create_story, delete_story
from afterworlds.persistence.orm.story_bible import SBCastEntryORM
from afterworlds.services.story_bible import StoryBibleService
from tests.services.conftest import make_cast_entry, make_relationship


def _story(session: Session) -> UUID:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(title="Other", mode=StoryMode.RPG, created_at=now, updated_at=now)
    create_story(session, story)
    session.commit()
    return story.story_id


def _cast(service: StoryBibleService, story_id: UUID, name: str) -> UUID:
    entry = make_cast_entry(story_id, name)
    service.add_cast_entry(story_id, entry)
    return entry.cast_id


def _relationship(service: StoryBibleService, story_id: UUID) -> UUID:
    rel = make_relationship(
        story_id, _cast(service, story_id, "Aldric"), _cast(service, story_id, "Mira")
    )
    service.add_relationship(story_id, rel)
    service.route_extractor_proposals(
        story_id,
        uuid4(),
        ExtractorProposalSet(
            proposals=[
                TransientStateProposal(
                    target_domain=TargetDomain.RELATIONSHIP,
                    target_natural_key="Aldric -> Mira",
                    target_field="current_status_description",
                    proposed_value="Estranged",
                )
            ]
        ),
    )
    return rel.relationship_id


def test_cast_writer_records_story_and_reads_are_story_scoped(
    service: StoryBibleService, session: Session, story_id: UUID
) -> None:
    other = _story(session)
    cast_id = _cast(service, story_id, "Aldric")
    service.update_dynamic_field(story_id, cast_id, "current_location", "Gate")

    history = service.get_dynamic_field_history(
        "cast_entry", cast_id, story_id=story_id
    )
    assert [h.story_id for h in history] == [story_id]
    assert (
        service.get_dynamic_field_history("cast_entry", cast_id, story_id=other) == []
    )
    assert service.get_dynamic_field_history("cast_entry", cast_id) == history


def test_relationship_writer_records_owning_story_not_a_namesake(
    service: StoryBibleService, session: Session, story_id: UUID
) -> None:
    other = _story(session)
    mine = _relationship(service, story_id)
    theirs = _relationship(service, other)

    for rel_id, owner, foreign in ((mine, story_id, other), (theirs, other, story_id)):
        history = service.get_dynamic_field_history(
            "relationship_ledger", rel_id, story_id=owner
        )
        assert [(h.story_id, h.old_value) for h in history] == [
            (owner, "Trusted comrade")
        ]
        assert (
            service.get_dynamic_field_history(
                "relationship_ledger", rel_id, story_id=foreign
            )
            == []
        )


def test_history_is_retained_and_readable_after_story_deletion(
    service: StoryBibleService, session: Session, story_id: UUID
) -> None:
    cast_id = _cast(service, story_id, "Bryn")
    service.update_dynamic_field(story_id, cast_id, "current_location", "Gate")
    rel_id = _relationship(service, story_id)
    session.commit()

    assert delete_story(session, story_id)
    session.commit()
    session.expire_all()
    assert session.get(SBCastEntryORM, str(cast_id)) is None  # cascade ran

    for entity_type, entity_id in (
        ("cast_entry", cast_id),
        ("relationship_ledger", rel_id),
    ):
        history = service.get_dynamic_field_history(
            entity_type, entity_id, story_id=story_id
        )
        assert len(history) == 1
        assert history[0].story_id == story_id
