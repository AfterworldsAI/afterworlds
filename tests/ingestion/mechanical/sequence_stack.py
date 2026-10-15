"""An isolated backend stack for CRD Issue 15b Phase 2 sequence proofs.

A private copy of the published-release store (``g1_store``: the app's own
Alembic chain, the real source release finalized, the accepted C9 authority
published; nothing shared is read or written), the unchanged existing
``build_orchestrator`` services with the fake provider, and a test-owned
``ActionResolutionService`` constructed from the same backend services and
given to that orchestrator. No ``create_app``, HTTP route or product wiring is
used: those are CRD Issue 15b Phase 3's. Only the GameMaster's adjudication
proposals and, where a test says so, backend dice are scripted.

``s1`` applies the Owner-adopted S1 contest supplement in memory only: subjects
created with its binding are written at the store layer (no rules-authority
row names S1; nothing is published or activated), and the authority reads of
that one binding answer with ``s1_index()``.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.deps import provision_sojourner_id
from afterworlds.api.pipeline_wiring import build_orchestrator
from afterworlds.api.story_bootstrap import (
    ensure_mode_session_state,
    ensure_story_turn_anchor_node,
)
from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.dnd5e_state import (
    CreatureState,
    DeathState,
    HitPoints,
    ZeroHitPointTreatment,
)
from afterworlds.models.enums import DiceHandling, RpgPlayStatus, StoryMode
from afterworlds.models.rpg import (
    DiceResult,
    PlayerRollTermResult,
    RawPlayerRollSubmission,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.models.story import Story
from afterworlds.persistence.crud.session_state import (
    get_rpg_session_state_by_story,
    update_rpg_session_state,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.orchestrator.models import OrchestrationResult
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
from afterworlds.pipeline.rpg.sequence import ActionResolutionService
from afterworlds.services.dnd5e_state import holdings, service, store, turn
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, create_item
from tests.services.dnd5e_state.builders import complete_character, real_index, s1_index

NOW = "2026-10-14T00:00:00+00:00"
PACKAGE = UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2")
MONSTER = ZeroHitPointTreatment(subject="monster")


@dataclass
class Story_:
    story_id: UUID
    node_id: UUID
    sheet_id: UUID


@dataclass
class Stack:
    factory: sessionmaker[Session]
    orchestrator: OrchestratorService
    sequences: ActionResolutionService
    sojourner_id: UUID

    # -- setup -------------------------------------------------------------

    def story(
        self,
        dice: DiceHandling = DiceHandling.PLAYER_ROLLS,
        character: Any = None,
        binding: RulesPackageBinding | None = None,
    ) -> Story_:
        now = datetime.now(UTC)
        with self.factory() as s:
            story = create_story(
                s,
                Story(title="15b", mode=StoryMode.RPG, created_at=now, updated_at=now),
            )
            ensure_mode_session_state(
                s, story.story_id, StoryMode.RPG, character_name="Ilse"
            )
            anchor = ensure_story_turn_anchor_node(s, story.story_id, StoryMode.RPG)
            state = get_rpg_session_state_by_story(s, story.story_id)
            assert state is not None
            sheet = character or complete_character(real_index(), "classes.wizard", 3)
            if binding is None:
                service.create_character(
                    s, state.character_sheet_id, PACKAGE, sheet, now=NOW
                )
            else:
                store.create_character_state(
                    s, state.character_sheet_id, sheet, binding, now=NOW
                )
            update_rpg_session_state(
                s,
                state.model_copy(
                    update={
                        "play_status": RpgPlayStatus.IN_PLAY,
                        "dice_handling": dice,
                        "gm_cheating": False,
                    }
                ),
            )
            s.commit()
            return Story_(story.story_id, anchor.node_id, state.character_sheet_id)

    def creature(
        self,
        story: Story_,
        template: str = "animals.wolf",
        hp: int = 11,
        treatment: ZeroHitPointTreatment = MONSTER,
        name: str = "Wolf",
        binding: RulesPackageBinding | None = None,
    ) -> UUID:
        state = CreatureState(
            template_record_key=template,
            hit_points=HitPoints(current=hp, maximum=hp, temporary=0),
            conditions=(),
            active_effects=(),
            death_state=DeathState(successes=0, failures=0, stable=False, dead=False),
            zero_hit_point_treatment=treatment,
        )
        with self.factory() as s:
            if binding is None:
                created = service.create_creature(
                    s, story.story_id, name, PACKAGE, state, now=NOW
                )
            else:
                created = store.create_creature(
                    s, story.story_id, name, state, binding, now=NOW
                )
            s.commit()
            return created.creature_id

    def item(self, story: Story_, record: str, **facts: Any) -> UUID:
        with self.factory() as s:
            made = create_item(
                s,
                real_index(),
                Holder(HolderKind.CHARACTER, story.sheet_id),
                record,
                now=NOW,
                **facts,
            )
            s.commit()
            return made.item_id

    # -- play ---------------------------------------------------------------

    def turn(self, story: Story_, text: str = "I act.") -> OrchestrationResult:
        return self.orchestrator.orchestrate_turn(
            story.story_id,
            story.node_id,
            text,
            self.sojourner_id,
            RuntimeAccessPath.HOSTED,
        )

    def resume(self, story: Story_, node_id: UUID | None = None) -> OrchestrationResult:
        sequence_id = self.sequence(story)["sequence_id"]
        return self.orchestrator.orchestrate_rpg_resume(
            story.story_id,
            node_id or story.node_id,
            UUID(sequence_id),
            access_path=RuntimeAccessPath.HOSTED,
            sojourner_id=self.sojourner_id,
        )

    def roll(self, view: Any, *values: int, revision: int | None = None) -> Any:
        """Submit raw inline values for the pending roll's one term."""
        (term,) = view.terms
        return self.sequences.consume_roll(
            RawPlayerRollSubmission(
                source="inline_ui",
                pending_roll_request_id=view.pending_roll_request_id,
                expected_instruction_revision=(
                    view.instruction_revision if revision is None else revision
                ),
                term_results=(
                    PlayerRollTermResult(term_id=term.term_id, values=values),
                ),
            )
        )

    # -- inspection ---------------------------------------------------------

    def rows(self, sql: str, **params: object) -> list[Any]:
        with self.factory() as s:
            return list(s.execute(sa.text(sql), params).all())

    def sequence(self, story: Story_) -> dict[str, Any]:
        (row,) = self.rows(
            "SELECT * FROM action_resolution_sequences WHERE story_id = :s",
            s=str(story.story_id),
        )
        return dict(row._mapping)

    def events(self, story: Story_) -> list[Any]:
        return self.rows(
            "SELECT kind, event_order, payload_json, provisional_effects_json,"
            " mechanical_provenance FROM action_resolution_events"
            " WHERE story_id = :s ORDER BY event_order",
            s=str(story.story_id),
        )

    def audit(self, story: Story_) -> list[Any]:
        return self.rows(
            "SELECT * FROM rpg_roll_audit WHERE story_id = :s ORDER BY global_sequence",
            s=str(story.story_id),
        )

    def hp(self, creature_id: UUID) -> tuple[int, int]:
        (row,) = self.rows(
            "SELECT revision, document FROM dnd5e_creatures WHERE creature_id = :c",
            c=str(creature_id),
        )
        document = (
            row.document if isinstance(row.document, dict) else json.loads(row.document)
        )
        return int(row.revision), int(document["hit_points"]["current"])

    def turns(self) -> int:
        return len(self.rows("SELECT 1 FROM turns"))


def wire(
    orchestrator: OrchestratorService, factory: sessionmaker[Session]
) -> ActionResolutionService:
    """Give *orchestrator* an action-resolution service built from its own
    adjudication service, dice and sheet resolver (test-owned construction;
    the product construction is Phase 3's)."""
    adjudication = orchestrator._rpg_adjudication_service  # noqa: SLF001
    dice = orchestrator._rpg_dice_service  # noqa: SLF001
    resolver = orchestrator._rpg_session_sheet_resolver  # noqa: SLF001
    assert adjudication is not None and dice is not None and resolver is not None
    sequences = ActionResolutionService(
        adjudication, D20RulesSystemAdapter(), dice, factory, resolver
    )
    orchestrator._rpg_sequence_service = sequences  # noqa: SLF001
    return sequences


@pytest.fixture()
def stack(
    g1_store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Stack]:
    db = tmp_path / "store.db"
    shutil.copyfile(g1_store, db)
    monkeypatch.setenv("AFTERWORLDS_FAKE_PROVIDER", "1")
    monkeypatch.setenv(
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY", str(tmp_path / "chroma")
    )
    engine = create_engine(f"sqlite:///{db}")
    factory = create_session_factory(engine)
    orchestrator = build_orchestrator(factory)
    sequences = wire(orchestrator, factory)
    try:
        yield Stack(factory, orchestrator, sequences, provision_sojourner_id(factory))
    finally:
        orchestrator.close()
        engine.dispose()


def scripted_dice(
    monkeypatch: pytest.MonkeyPatch, faces: Callable[[str], tuple[int, ...]]
) -> list[str]:
    """Backend dice returning *faces(expression)*; records each expression."""
    rolled: list[str] = []

    def roll(self: object, expression: str) -> DiceResult:
        from afterworlds.pipeline.rpg.dice import (
            _rule,  # noqa: PLC2701
            parse_expression,
            selected_indices,
        )

        rolled.append(expression)
        raw = faces(expression)
        _, _, op, keep = parse_expression(expression)
        kept = selected_indices(raw, _rule(op), keep)
        return DiceResult(
            expression=expression, raw_rolls=raw, chosen=sum(raw[i] for i in kept)
        )

    monkeypatch.setattr(SystemRandomDiceService, "roll", roll)
    return rolled


def s1(monkeypatch: pytest.MonkeyPatch) -> AuthorityIndex:
    """Apply S1 in memory: the authority reads of its one binding answer with
    ``s1_index()``; every other binding reads the store as before."""
    index = s1_index()
    real_index_of = service.authority_index
    real_current = service.require_current

    def index_of(session: Session, binding: RulesPackageBinding, **kw: Any) -> Any:
        if binding == index.binding:
            return index
        return real_index_of(session, binding, **kw)

    def current(session: Session, binding: RulesPackageBinding, **kw: Any) -> Any:
        if binding != index.binding:
            real_current(session, binding, **kw)

    for module in (service, turn, holdings):
        monkeypatch.setattr(module, "authority_index", index_of)
    for module in (service, holdings):
        monkeypatch.setattr(module, "require_current", current)
    return index


def no_backend_dice(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    def faces(expression: str) -> tuple[int, ...]:
        raise AssertionError(f"the backend rolled {expression}")

    return scripted_dice(monkeypatch, faces)


def unique() -> str:
    return str(uuid4())
