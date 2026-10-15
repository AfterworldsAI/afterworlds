"""Database fixtures for the CRD Issue 2b state suite.

``runtime`` is the rules-authority suite's real published release with an
activated bounded projection (records ``spell:wish`` and
``creature:wish-scoped-servant``), reached through the genuine publish/activate
path, in a private SQLite file. Characters here hold state whose identities
that projection defines; the content rules for the full SRD are exercised
against the committed authority in ``test_state_validation.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rpg  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.api.story_bootstrap import ensure_story_turn_anchor_node
from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.character_sheet import RpgCharacterSheetBase
from afterworlds.models.dnd5e_state import (
    ConditionInstance,
    Dnd5eCharacterState,
    GrantSource,
    HitPoints,
    SpellAccess,
)
from afterworlds.models.enums import ConditionVisibility, IntentType, StoryMode
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.models.story import Story
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.character_sheet import create_rpg_base_sheet
from afterworlds.persistence.crud.node import create_turn
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.rpg import ActionResolutionSequenceORM
from tests.services.rules_authority.conftest import (  # noqa: F401 - fixture
    CREATURE_KEY,
    SPELL_KEY,
    RuntimeFixture,
    runtime,
)

NOW = "2026-10-11T00:00:00+00:00"


def wizardish(**updates: object) -> Dnd5eCharacterState:
    """A character whose identities the bounded projection defines."""
    base = Dnd5eCharacterState(
        hit_points=HitPoints(current=9, maximum=9, temporary=0),
        conditions=(),
        active_effects=(),
        hazards=(),
        spell_access=(
            SpellAccess(
                pool_id="wizard",
                spell_record_key=SPELL_KEY,
                mode="prepared",
                source=GrantSource(record_key=SPELL_KEY),
            ),
        ),
    )
    return base.model_copy(update=updates)


def poisoned(instance_id: str) -> ConditionInstance:
    return ConditionInstance(
        instance_id=instance_id,
        condition=ConditionKind.POISONED,
        visibility=ConditionVisibility.VISIBLE,
    )


@dataclass(frozen=True)
class Table:
    runtime: RuntimeFixture
    factory: sessionmaker[Session]

    @property
    def package(self) -> UUID:
        return self.runtime.package_uuid


def new_story(session: Session) -> UUID:
    now = datetime(2026, 10, 11, tzinfo=UTC)
    story = Story(title="2b", mode=StoryMode.RPG, created_at=now, updated_at=now)
    create_story(session, story)
    return story.story_id


def new_character(session: Session, story_id: UUID, name: str = "Ilse") -> UUID:
    now = datetime(2026, 10, 11, tzinfo=UTC)
    base = RpgCharacterSheetBase(
        story_id=story_id, character_name=name, created_at=now, updated_at=now
    )
    create_rpg_base_sheet(session, base)
    return base.sheet_id


def add_unresolved_sequence(
    session: Session, story_id: UUID, character_id: UUID
) -> str:
    """An unresolved action-resolution sequence of *story_id* (CRD Issue 15b):
    the durable event a held rule change or adoption waits for."""
    turn = Turn(
        user_input="x",
        assistant_output="x",
        timestamp=datetime(2026, 10, 11, tzinfo=UTC),
        intent_classification=IntentType.IN_CHARACTER_ACTION,
        node_id=None,
    )
    create_turn(session, turn)
    node_id = ensure_story_turn_anchor_node(session, story_id, StoryMode.RPG).node_id
    sequence_id = str(uuid4())
    session.add(
        ActionResolutionSequenceORM(
            sequence_id=sequence_id,
            story_id=str(story_id),
            session_id=str(uuid4()),
            node_id=str(node_id),
            character_id=str(character_id),
            originating_turn_id=str(turn.turn_id),
            status="active",
            current_interaction_kind="roll",
            plan_json="{}",
            reads_json="{}",
            records_json="[]",
            unattached_json="[]",
            resolved_steps_json="[]",
            projected_state_json="{}",
            provisional_effects_json="[]",
            revision=1,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    session.flush()
    return sequence_id


def complete_sequence(session: Session, sequence_id: str) -> None:
    row = session.get(ActionResolutionSequenceORM, sequence_id)
    assert row is not None
    row.status = "completed"
    session.flush()


@pytest.fixture()
def table(runtime: RuntimeFixture) -> Iterator[Table]:  # noqa: F811
    runtime.session.commit()
    yield Table(runtime, create_session_factory(runtime.engine))


@pytest.fixture()
def srd_content(table: Table) -> Iterator[Callable[..., None]]:  # noqa: F811
    """Give a binding the committed SRD records, alongside its own.

    The bounded projection a real database publishes here has no item records,
    and publishing the full SRD costs minutes. This seeds the binding-keyed
    authority cache instead: production code still resolves the holder's
    binding, requires it current and looks its authority up by that exact
    binding; only the *content* behind the binding is the committed SRD's.
    ``without`` drops record keys, to model a binding that lacks them.
    ``tests/ingestion/mechanical/test_srd_state_on_published_release.py``
    proves the same items against the genuinely published SRD.
    """
    from afterworlds.services.dnd5e_state import authority
    from tests.services.dnd5e_state.builders import real_index

    seeded: list[RulesPackageBinding] = []

    def seed(binding: RulesPackageBinding, *, without: tuple[str, ...] = ()) -> None:
        # Cold: another test may have cached this binding (identities are
        # content-derived), which would hide a version this test never retained.
        with authority._CACHE_LOCK:  # noqa: SLF001
            authority._CACHE.pop(binding, None)  # noqa: SLF001
        with table.factory() as s:
            own = authority.authority_index(s, binding, now=NOW)
        srd = real_index()
        records = {**own.records, **srd.records}
        for key in without:
            records.pop(key, None)
        with authority._CACHE_LOCK:  # noqa: SLF001
            authority._CACHE[binding] = authority.AuthorityIndex(  # noqa: SLF001
                binding=binding,
                records=records,
                members={**own.members, **srd.members},
            )
        seeded.append(binding)

    yield seed
    with authority._CACHE_LOCK:  # noqa: SLF001
        for binding in seeded:
            authority._CACHE.pop(binding, None)  # noqa: SLF001
