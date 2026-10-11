"""CRD Issue 2b state on the genuinely published accepted SRD release.

The 2b service suite runs on a bounded projection (fast, per test). This module
proves the same production paths against the committed accepted authority,
published through the real lifecycle into a private store: a complete
character is created under the package's current exact binding, and every G1
item and an accepted poison are held, applied and resolved through the
holder's own authority.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.ingestion.mechanical.oracle import (
    candidate_from_accepted_inputs,
    committed_inputs_for,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    publish_from_committed_oracle,
)
from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.dnd5e_state import holdings, service
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind
from tests.services.dnd5e_state.builders import complete_character, real_index
from tests.services.dnd5e_state.test_holdings import G1_ITEMS

NOW = "2026-10-11T00:00:00+00:00"
PACKAGE = UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2")
RELEASE = "5.2.1-corpus.8781d4e0-a3b"


@pytest.fixture(scope="module")
def srd_store(
    tmp_path_factory: pytest.TempPathFactory, source_release_db: Path
) -> Iterator[sessionmaker[Session]]:
    path = tmp_path_factory.mktemp("srd-2b") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    factory = create_session_factory(engine)
    inputs = committed_inputs_for(str(PACKAGE), RELEASE)
    assert inputs is not None
    with factory() as session:
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(session, identified, now=NOW)
        record_persisted_state_digest(session, identified.projection_uuid)
        session.commit()
        result = publish_from_committed_oracle(
            session, identified.projection_uuid, now=NOW
        )
        assert result.outcome is PublicationOutcome.PUBLISHED
    yield factory
    engine.dispose()


def test_a_complete_character_holds_every_g1_item_and_a_poison(
    srd_store: sessionmaker[Session],
) -> None:
    created = datetime(2026, 10, 11, tzinfo=UTC)
    with srd_store() as s, s.begin():
        story = Story(
            title="2b", mode=StoryMode.RPG, created_at=created, updated_at=created
        )
        create_story(s, story)
        base = RpgCharacterSheetBase(
            story_id=story.story_id,
            character_name="Ilse",
            created_at=created,
            updated_at=created,
        )
        create_rpg_base_sheet(s, base)
        state = complete_character(real_index(), "classes.wizard", 3)
        stored = service.create_character(s, base.sheet_id, PACKAGE, state, now=NOW)
        assert service.readiness(s, stored, now=NOW) == ()
        holder = Holder(HolderKind.CHARACTER, base.sheet_id)
        index = holdings.holder_authority(s, holder, now=NOW)
        assert index.binding == stored.binding
        for key in G1_ITEMS:
            holdings.create_item(s, index, holder, key, now=NOW)
        holdings.create_item(
            s,
            index,
            holder,
            "gameplay_toolbox.poison.assassins_blood",
            quantity=3,
            now=NOW,
        )
        dart = next(
            i
            for i in holdings.items_held_by(s, holder)
            if i.record_key.endswith("dart")
        )
        holdings.update_item_use(
            s,
            dart.item_id,
            expected_revision=dart.revision,
            equipped=False,
            attuned=False,
            charges_remaining=None,
            applied_poison_record_key="gameplay_toolbox.poison.assassins_blood",
            now=NOW,
        )
    with srd_store() as s:
        held = holdings.items_held_by(s, holder)
        read = service.read_character(s, base.sheet_id)
    assert read.state == state
    assert {i.record_key for i in held} == set(G1_ITEMS) | {
        "gameplay_toolbox.poison.assassins_blood"
    }
    assert all(index.record(i.record_key) is not None for i in held)
