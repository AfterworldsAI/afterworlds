"""Comprehensive tests for CRD Issue 5b — Rules Package Ingestion Pipeline.

Tests cover:
- Ingestion correctness: RuleSource, RuleChunk, MechanicalEntity records
- Per-record provenance (source_document, source_locator_type, source_locator_value)
- Manifest persistence, uniqueness, and field population
- Re-run idempotency (no duplicate records)
- Publication gate (fail on incomplete ingest/vector/missing manifest)
- Package transition to published on publish()
- Play-time query exclusion of draft packages
- Override immutability (source chunks unchanged after override)
- Read surface: get_chunks_by_subsystem, get_entity_by_type_and_name,
  get_active_rule_slice
- Vector index: ChromaDB collection populated; basic query returns results
"""

from __future__ import annotations

from typing import Any

import chromadb
import pytest
from sqlalchemy import select

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.ingestion.ingestion_service import (
    IngestionService,
    PublicationError,
)
from afterworlds.ingestion.srd_parser import ParseError, SRDParser
from afterworlds.ingestion.vector_writer import VectorWriter
from afterworlds.models.enums import (
    MechanicalEntityTypeEnum,
    PublicationStatusEnum,
    RuleSubsystemEnum,
)
from afterworlds.models.rules_package import IngestionConfig
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import (
    MechanicalEntityORM,
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageManifestORM,
    RulesPackageORM,
)
from afterworlds.services.rules_package import RulesPackageService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):  # type: ignore[no-untyped-def]
    """SQLAlchemy session bound to the in-memory engine."""
    factory = create_session_factory(engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def chroma_client() -> chromadb.ClientAPI:
    """Ephemeral in-memory ChromaDB client for test isolation."""
    return chromadb.EphemeralClient()


@pytest.fixture()
def ingestion_config() -> IngestionConfig:
    """Default IngestionConfig for tests."""
    return IngestionConfig(
        package_name="Test SRD",
        package_version="5.2.1",
        system="d20",
        source_name="Test Source",
        source_category="core_rulebook",
        source_precedence_rank=1,
        authoritative_source_document="Test SRD 5.2.1",
        authoritative_source_version="5.2.1",
        package_license="CC BY 4.0",
        transform_status="Test transform",
        parsing_convenience_source=None,
        attribution_text="Test attribution text for SRD 5.2.1",
    )


@pytest.fixture()
def srd_data_fixture() -> dict[str, Any]:
    """Minimal SRD data fixture with all 8 subsystems and required entity counts.

    Contains:
    - 3+ sections per subsystem (24+ total sections)
    - 3 spells, 3 conditions, 2 items, 1 stat_block, 1 action
    - All 8 subsystems represented
    """
    sections = [
        # COMBAT (3)
        {
            "heading": "Attack Rolls",
            "content": "Roll d20 + modifiers vs AC.",
            "subsystem": "combat",
            "section_path": "combat/attack-rolls",
            "page_ref": "p. 194",
        },
        {
            "heading": "Damage Rolls",
            "content": "Roll damage dice + modifiers.",
            "subsystem": "combat",
            "section_path": "combat/damage-rolls",
            "page_ref": "p. 196",
        },
        {
            "heading": "Death Saving Throws",
            "content": "Roll d20; 10+ succeeds. 3 successes = stable; 3 = death.",
            "subsystem": "combat",
            "section_path": "combat/death-saving-throws",
            "page_ref": "p. 197",
        },
        # SPELLS (3)
        {
            "heading": "Fireball",
            "content": "8d6 fire damage in 20-foot sphere.",
            "subsystem": "spells",
            "section_path": "spells/fireball",
            "page_ref": "p. 241",
        },
        {
            "heading": "Magic Missile",
            "content": "Three darts, 1d4+1 force each.",
            "subsystem": "spells",
            "section_path": "spells/magic-missile",
            "page_ref": "p. 257",
        },
        {
            "heading": "Cure Wounds",
            "content": "1d8 + modifier hit points restored.",
            "subsystem": "spells",
            "section_path": "spells/cure-wounds",
            "page_ref": "p. 230",
        },
        # CONDITIONS (3)
        {
            "heading": "Blinded",
            "content": "Cannot see; attacks against have advantage.",
            "subsystem": "conditions",
            "section_path": "conditions/blinded",
            "page_ref": "p. 290",
        },
        {
            "heading": "Charmed",
            "content": "Cannot attack charmer; charmer has social advantage.",
            "subsystem": "conditions",
            "section_path": "conditions/charmed",
            "page_ref": "p. 290",
        },
        {
            "heading": "Frightened",
            "content": "Disadvantage on attacks/checks near fear source.",
            "subsystem": "conditions",
            "section_path": "conditions/frightened",
            "page_ref": "p. 290",
        },
        # MOVEMENT (3)
        {
            "heading": "Movement and Position",
            "content": "You can move up to your speed on your turn.",
            "subsystem": "movement",
            "section_path": "movement/movement-and-position",
            "page_ref": "p. 190",
        },
        {
            "heading": "Difficult Terrain",
            "content": "Each foot of movement costs 1 extra foot.",
            "subsystem": "movement",
            "section_path": "movement/difficult-terrain",
            "page_ref": "p. 190",
        },
        {
            "heading": "Moving Between Attacks",
            "content": "You can split movement between attacks with Extra Attack.",
            "subsystem": "movement",
            "section_path": "movement/between-attacks",
            "page_ref": "p. 190",
        },
        # ITEMS (3)
        {
            "heading": "Longsword",
            "content": "1d8 slashing, versatile (1d10).",
            "subsystem": "items",
            "section_path": "items/longsword",
            "page_ref": "p. 149",
        },
        {
            "heading": "Chain Mail",
            "content": "AC 16, Str 13 required, stealth disadvantage.",
            "subsystem": "items",
            "section_path": "items/chain-mail",
            "page_ref": "p. 145",
        },
        {
            "heading": "Healing Potion",
            "content": "Regain 2d4+2 hit points.",
            "subsystem": "items",
            "section_path": "items/healing-potion",
            "page_ref": "p. 153",
        },
        # CLASSES (3)
        {
            "heading": "Fighter",
            "content": "Fighters are masters of weapons and armor.",
            "subsystem": "classes",
            "section_path": "classes/fighter",
            "page_ref": "p. 70",
        },
        {
            "heading": "Wizard",
            "content": "Wizards are supreme magic-users.",
            "subsystem": "classes",
            "section_path": "classes/wizard",
            "page_ref": "p. 112",
        },
        {
            "heading": "Cleric",
            "content": "Clerics are intermediaries between mortals and gods.",
            "subsystem": "classes",
            "section_path": "classes/cleric",
            "page_ref": "p. 56",
        },
        # RACES (3)
        {
            "heading": "Dwarf",
            "content": "Constitution +2, darkvision, dwarven resilience.",
            "subsystem": "races",
            "section_path": "races/dwarf",
            "page_ref": "p. 18",
        },
        {
            "heading": "Elf",
            "content": "Dexterity +2, darkvision, fey ancestry.",
            "subsystem": "races",
            "section_path": "races/elf",
            "page_ref": "p. 21",
        },
        {
            "heading": "Human",
            "content": "All ability scores +1.",
            "subsystem": "races",
            "section_path": "races/human",
            "page_ref": "p. 29",
        },
        # GENERAL (3)
        {
            "heading": "Ability Scores",
            "content": "Strength, Dexterity, Constitution, Intelligence, Wisdom, Cha.",
            "subsystem": "general",
            "section_path": "general/ability-scores",
            "page_ref": "p. 173",
        },
        {
            "heading": "Skills",
            "content": "Proficiency in a skill allows adding proficiency bonus.",
            "subsystem": "general",
            "section_path": "general/skills",
            "page_ref": "p. 174",
        },
        {
            "heading": "Resting",
            "content": "Short rest (1 hour) and long rest (8 hours) restore resources.",
            "subsystem": "general",
            "section_path": "general/resting",
            "page_ref": "p. 186",
        },
    ]

    entities = [
        # 3 spells
        {
            "entity_type": "spell",
            "name": "Fireball",
            "subsystem": "spells",
            "section_path": "spells/fireball",
            "page_ref": "p. 241",
            "data": {
                "casting_time": "1 action",
                "range": "150 feet",
                "duration": "Instantaneous",
                "components": ["V", "S", "M"],
                "effect_description": "8d6 fire damage in 20-foot sphere.",
            },
        },
        {
            "entity_type": "spell",
            "name": "Magic Missile",
            "subsystem": "spells",
            "section_path": "spells/magic-missile",
            "page_ref": "p. 257",
            "data": {
                "casting_time": "1 action",
                "range": "120 feet",
                "duration": "Instantaneous",
                "components": ["V", "S"],
                "effect_description": "Three darts, 1d4+1 force damage each.",
            },
        },
        {
            "entity_type": "spell",
            "name": "Cure Wounds",
            "subsystem": "spells",
            "section_path": "spells/cure-wounds",
            "page_ref": "p. 230",
            "data": {
                "casting_time": "1 action",
                "range": "Touch",
                "duration": "Instantaneous",
                "components": ["V", "S"],
                "effect_description": "Restore 1d8 + modifier hit points.",
            },
        },
        # 3 conditions
        {
            "entity_type": "condition",
            "name": "Blinded",
            "subsystem": "conditions",
            "section_path": "conditions/blinded",
            "page_ref": "p. 290",
            "data": {
                "effects": [
                    "Cannot see; auto-fail sight-based checks.",
                    "Attacks against have advantage.",
                    "Own attacks have disadvantage.",
                ]
            },
        },
        {
            "entity_type": "condition",
            "name": "Charmed",
            "subsystem": "conditions",
            "section_path": "conditions/charmed",
            "page_ref": "p. 290",
            "data": {
                "effects": [
                    "Cannot attack charmer.",
                    "Charmer has social advantage.",
                ]
            },
        },
        {
            "entity_type": "condition",
            "name": "Frightened",
            "subsystem": "conditions",
            "section_path": "conditions/frightened",
            "page_ref": "p. 290",
            "data": {
                "effects": [
                    "Disadvantage on attack rolls and ability checks near fear source.",
                    "Cannot willingly move closer to fear source.",
                ]
            },
        },
        # 2 items
        {
            "entity_type": "item",
            "name": "Longsword",
            "subsystem": "items",
            "section_path": "items/longsword",
            "page_ref": "p. 149",
            "data": {
                "item_type": "martial melee weapon",
                "properties": ["versatile (1d10)"],
                "weight": 3.0,
                "value": "15 gp",
            },
        },
        {
            "entity_type": "item",
            "name": "Chain Mail",
            "subsystem": "items",
            "section_path": "items/chain-mail",
            "page_ref": "p. 145",
            "data": {
                "item_type": "heavy armor",
                "properties": ["AC 16", "Str 13 required"],
                "weight": 55.0,
                "value": "75 gp",
            },
        },
        # 1 stat_block
        {
            "entity_type": "stat_block",
            "name": "Goblin",
            "subsystem": "general",
            "section_path": "monsters/goblin",
            "page_ref": "p. 315",
            "data": {
                "armor_class": 15,
                "hit_points": 7,
                "speed": "30 ft.",
                "strength": 8,
                "dexterity": 14,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 8,
                "charisma": 8,
                "actions": ["Scimitar: +4 to hit, 1d6+2 slashing."],
            },
        },
        # 1 action
        {
            "entity_type": "action",
            "name": "Attack",
            "subsystem": "combat",
            "section_path": "combat/actions/attack",
            "page_ref": "p. 192",
            "data": {
                "action_type": "action",
                "description": "Make one melee or ranged attack.",
                "attack_bonus": None,
                "effect": "Make one melee or ranged attack.",
            },
        },
    ]

    return {"sections": sections, "entities": entities}


@pytest.fixture()
def ingestion_service(ingestion_config: IngestionConfig) -> IngestionService:
    return IngestionService(ingestion_config)


@pytest.fixture()
def ingestion_result(
    session: Any,
    srd_data_fixture: dict[str, Any],
    chroma_client: chromadb.ClientAPI,
    ingestion_service: IngestionService,
) -> Any:
    """Run a full ingestion and return the IngestionResult."""
    return ingestion_service.ingest(
        session=session,
        srd_data=srd_data_fixture,
        source_file_name="test_srd.json",
        chroma_client=chroma_client,
    )


# ---------------------------------------------------------------------------
# Ingestion correctness
# ---------------------------------------------------------------------------


class TestIngestionCorrectness:
    def test_rule_source_created(self, session: Any, ingestion_result: Any) -> None:
        """RuleSource record created with required fields populated."""
        sources = session.execute(select(RuleSourceORM)).scalars().all()
        assert len(sources) == 1
        src = sources[0]
        assert src.rules_package_id == ingestion_result.package_id
        assert src.name == "Test Source"
        assert src.category == "core_rulebook"
        assert src.precedence_rank == 1
        assert src.created_at

    def test_rule_chunks_created(self, session: Any, ingestion_result: Any) -> None:
        """RuleChunk records created."""
        chunks = session.execute(select(RuleChunkORM)).scalars().all()
        assert len(chunks) == ingestion_result.chunks_written
        assert ingestion_result.chunks_written == 24  # 3 per subsystem × 8

    def test_mechanical_entities_created(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """MechanicalEntity records created."""
        entities = session.execute(select(MechanicalEntityORM)).scalars().all()
        assert len(entities) == ingestion_result.entities_written
        assert ingestion_result.entities_written == 10  # 3+3+2+1+1

    def test_no_orphaned_chunks(self, session: Any, ingestion_result: Any) -> None:
        """No chunks have null source_id."""
        chunks = session.execute(select(RuleChunkORM)).scalars().all()
        for chunk in chunks:
            assert chunk.source_id is not None
            assert chunk.source_id == ingestion_result.source_id

    def test_no_orphaned_entities(self, session: Any, ingestion_result: Any) -> None:
        """No entities have null source_id."""
        entities = session.execute(select(MechanicalEntityORM)).scalars().all()
        for ent in entities:
            assert ent.source_id is not None
            assert ent.source_id == ingestion_result.source_id

    def test_all_8_subsystems_have_chunks(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """All 8 subsystems have at least one chunk."""
        subsystems_in_db: set[str] = set(
            session.execute(
                select(RuleChunkORM.subsystem).where(
                    RuleChunkORM.rules_package_id == ingestion_result.package_id
                )
            )
            .scalars()
            .all()
        )
        expected = {e.value for e in RuleSubsystemEnum}
        assert (
            expected == subsystems_in_db
        ), f"Missing subsystems: {expected - subsystems_in_db}"


# ---------------------------------------------------------------------------
# Atomicity
# ---------------------------------------------------------------------------


class TestIngestionAtomicity:
    def test_parse_error_in_entities_leaves_no_partial_state(
        self,
        session: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """ParseError during entity parsing leaves zero rows in the session.

        Regression test for P1: previously parse_chunks() was called and its
        results flushed to the DB before parse_entities() ran.  A ParseError
        from bad entity data would then leave partial package/source/chunk rows
        committed to the transaction, violating the all-or-nothing ingest
        contract.

        Fix: both parse steps now run before any DB work, so a ParseError
        aborts with no partial state written.
        """
        bad_srd: dict[str, Any] = {
            "sections": [
                {
                    "heading": "Attack Rolls",
                    "content": "Roll d20.",
                    "subsystem": "combat",
                    "section_path": "combat/attack-rolls",
                    "page_ref": "p. 1",
                }
            ],
            "entities": [
                {
                    "entity_type": "spell",
                    "name": "Fireball",
                    "subsystem": "spells",
                    "section_path": "spells/fireball",
                    "page_ref": "p. 1",
                    "data": {},  # Missing required fields — triggers ParseError
                }
            ],
        }
        from afterworlds.ingestion.srd_parser import ParseError
        from afterworlds.persistence.orm.rules_package import (
            MechanicalEntityORM,
            RuleChunkORM,
            RuleSourceORM,
            RulesPackageManifestORM,
            RulesPackageORM,
        )

        with pytest.raises(ParseError):
            ingestion_service.ingest(
                session=session,
                srd_data=bad_srd,
                source_file_name="bad.json",
                chroma_client=chroma_client,
            )

        # No rows should have been written
        assert session.execute(select(RulesPackageORM)).scalars().all() == []
        assert session.execute(select(RuleSourceORM)).scalars().all() == []
        assert session.execute(select(RuleChunkORM)).scalars().all() == []
        assert session.execute(select(MechanicalEntityORM)).scalars().all() == []
        assert session.execute(select(RulesPackageManifestORM)).scalars().all() == []


# ---------------------------------------------------------------------------
# Per-record provenance
# ---------------------------------------------------------------------------


class TestProvenance:
    def test_chunk_provenance_fields_non_null(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """Every chunk has non-null source_document, locator_type, locator_value."""
        chunks = session.execute(select(RuleChunkORM)).scalars().all()
        for chunk in chunks:
            assert (
                chunk.source_document
            ), f"chunk {chunk.chunk_id} missing source_document"
            assert (
                chunk.source_locator_type
            ), f"chunk {chunk.chunk_id} missing source_locator_type"
            assert (
                chunk.source_locator_value
            ), f"chunk {chunk.chunk_id} missing source_locator_value"

    def test_entity_provenance_fields_non_null(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """Every entity has non-null source_document, locator_type, locator_value."""
        entities = session.execute(select(MechanicalEntityORM)).scalars().all()
        for ent in entities:
            assert (
                ent.source_document
            ), f"entity {ent.entity_id} missing source_document"
            assert (
                ent.source_locator_type
            ), f"entity {ent.entity_id} missing source_locator_type"
            assert (
                ent.source_locator_value
            ), f"entity {ent.entity_id} missing source_locator_value"

    def test_chunk_source_document_is_file_name(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """source_document on chunks equals the source_file_name passed to ingest."""
        chunks = session.execute(select(RuleChunkORM)).scalars().all()
        for chunk in chunks:
            assert chunk.source_document == "test_srd.json"

    def test_entity_source_document_is_file_name(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """source_document on entities equals the source_file_name passed to ingest."""
        entities = session.execute(select(MechanicalEntityORM)).scalars().all()
        for ent in entities:
            assert ent.source_document == "test_srd.json"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def test_manifest_persisted(self, session: Any, ingestion_result: Any) -> None:
        """Manifest row persisted as distinct row in rules_package_manifests."""
        manifests = session.execute(select(RulesPackageManifestORM)).scalars().all()
        assert len(manifests) == 1
        m = manifests[0]
        assert m.rules_package_id == ingestion_result.package_id

    def test_manifest_required_fields(
        self, session: Any, ingestion_result: Any
    ) -> None:
        """Manifest carries all required fields."""
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert m.authoritative_source_document == "Test SRD 5.2.1"
        assert m.authoritative_source_version == "5.2.1"
        assert m.package_license == "CC BY 4.0"
        assert m.transform_status == "Test transform"
        assert m.attribution_text == "Test attribution text for SRD 5.2.1"
        assert m.parsing_convenience_source is None

    def test_manifest_fk_to_package(self, session: Any, ingestion_result: Any) -> None:
        """Manifest FK points to the package row."""
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        pkg = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert m.rules_package_id == pkg.rules_package_id

    def test_rerun_does_not_create_duplicate_manifest(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Re-running ingestion does not create a duplicate manifest row."""
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        manifests = session.execute(select(RulesPackageManifestORM)).scalars().all()
        assert len(manifests) == 1

    def test_publication_fails_if_sql_incomplete(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """Publication fails if sql_ingest_complete is False."""
        # Manually set sql_ingest_complete = False
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        m.sql_ingest_complete = False
        session.commit()

        vector_writer = VectorWriter(chroma_client)
        with pytest.raises(PublicationError, match="sql_ingest_complete"):
            service = IngestionService(
                IngestionConfig(
                    package_name="Test SRD",
                    package_version="5.2.1",
                )
            )
            service.publish(
                session=session,
                package_id=ingestion_result.package_id,
                vector_writer=vector_writer,
            )

    def test_publication_fails_if_vector_incomplete(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """Publication fails if vector_write_complete is False."""
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        m.vector_write_complete = False
        session.commit()

        vector_writer = VectorWriter(chroma_client)
        service = IngestionService(
            IngestionConfig(package_name="Test SRD", package_version="5.2.1")
        )
        with pytest.raises(PublicationError, match="vector_write_complete"):
            service.publish(
                session=session,
                package_id=ingestion_result.package_id,
                vector_writer=vector_writer,
            )

    def test_publication_fails_if_vector_index_empty_despite_manifest_flag(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """publish() fails when manifest flag is True but live vector index is empty.

        Regression test for P1: gate 4 previously only checked the persisted
        manifest flag and would pass even if the Chroma collection was deleted or
        reset between ingest and publish.
        """
        # Verify manifest flag is True after ingest
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert m.vector_write_complete is True

        # Delete the Chroma collection to simulate a reset between ingest and publish
        from afterworlds.ingestion.vector_writer import _collection_name

        chroma_client.delete_collection(_collection_name(ingestion_result.package_id))

        vector_writer = VectorWriter(chroma_client)
        service = IngestionService(
            IngestionConfig(package_name="Test SRD", package_version="5.2.1")
        )
        with pytest.raises(PublicationError, match="vector index has 0 documents"):
            service.publish(
                session=session,
                package_id=ingestion_result.package_id,
                vector_writer=vector_writer,
            )

    def test_publication_fails_if_manifest_missing(
        self,
        session: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """Publication fails if manifest row is missing."""
        from datetime import UTC, datetime

        now = datetime.now(UTC).isoformat()
        pkg = RulesPackageORM(
            rules_package_id="aaaaaaaa-0000-0000-0000-000000000001",
            name="Orphan Package",
            system="d20",
            version="1.0",
            is_enabled=True,
            publication_status="draft",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(pkg)
        session.commit()

        vector_writer = VectorWriter(chroma_client)
        service = IngestionService(
            IngestionConfig(package_name="Orphan Package", package_version="1.0")
        )
        with pytest.raises(PublicationError, match="no manifest row"):
            service.publish(
                session=session,
                package_id="aaaaaaaa-0000-0000-0000-000000000001",
                vector_writer=vector_writer,
            )

    def test_publication_fails_on_partial_vector_loss(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """publish() fails when Chroma has fewer docs than SQL chunks.

        Regression test for P1 (line 203 / Gate 5): has_chunks() returns True
        in partial-loss, so the old non-empty check would let publication
        proceed while large parts of the index are missing.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Remove some (but not all) documents from Chroma to simulate partial loss
        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        all_ids = collection.get()["ids"]
        assert len(all_ids) > 1, "fixture must have multiple chunks"
        collection.delete(ids=all_ids[:3])  # delete first 3; rest remain

        # Collection is non-empty so has_chunks() would pass, but count < sql
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.has_chunks(ingestion_result.package_id)

        service = IngestionService(
            IngestionConfig(package_name="Test SRD", package_version="5.2.1")
        )
        with pytest.raises(PublicationError, match="vector index has"):
            service.publish(
                session=session,
                package_id=ingestion_result.package_id,
                vector_writer=vector_writer,
            )

    def test_publication_fails_on_surplus_vector_count(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """publish() fails when Chroma has more docs than SQL chunks.

        Regression test for P1 (Gate 5 !=): the old ``< sql_count`` check
        would let surplus-count packages through Gate 5.  A surplus means
        stale documents from a failed partial run are present; the collection
        is inconsistent and must be repaired before publishing.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Add an extra phantom document so Chroma count > SQL chunk count
        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        collection.upsert(
            documents=["phantom surplus doc"],
            metadatas=[
                {
                    "package_id": ingestion_result.package_id,
                    "chunk_id": "surplus-id",
                    "subsystem": "combat",
                    "source_document": "phantom.json",
                }
            ],
            ids=["surplus-id"],
        )

        vector_writer = VectorWriter(chroma_client)
        service = IngestionService(
            IngestionConfig(package_name="Test SRD", package_version="5.2.1")
        )
        with pytest.raises(PublicationError, match="vector index has"):
            service.publish(
                session=session,
                package_id=ingestion_result.package_id,
                vector_writer=vector_writer,
            )

    def test_empty_payload_sets_sql_ingest_incomplete_and_blocks_publish(
        self,
        session: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Empty payload sets sql_ingest_complete=False; publish() rejects.

        Regression test for P1: ingest() previously set sql_ingest_complete=True
        unconditionally, so an empty SRD payload (no sections, no entities) could
        produce a manifest with both gate flags true and allow publish() to succeed
        on a package containing no usable rules content.
        """
        empty_data: dict[str, Any] = {"sections": [], "entities": []}
        result = ingestion_service.ingest(
            session=session,
            srd_data=empty_data,
            source_file_name="empty.json",
            chroma_client=chroma_client,
        )
        assert result.chunks_written == 0
        assert result.entities_written == 0

        # Manifest must record sql_ingest_complete=False
        m = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == result.package_id
            )
        ).scalar_one()
        assert m.sql_ingest_complete is False

        # publish() must reject the package at Gate 3
        vector_writer = VectorWriter(chroma_client)
        with pytest.raises(PublicationError, match="sql_ingest_complete"):
            ingestion_service.publish(
                session=session,
                package_id=result.package_id,
                vector_writer=vector_writer,
            )


# ---------------------------------------------------------------------------
# Publication flow
# ---------------------------------------------------------------------------


class TestPublicationFlow:
    def test_package_transitions_to_published(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Package transitions from draft to published after publish()."""
        pkg_before = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert pkg_before.publication_status == PublicationStatusEnum.DRAFT.value

        vector_writer = VectorWriter(chroma_client)
        ingestion_service.publish(
            session=session,
            package_id=ingestion_result.package_id,
            vector_writer=vector_writer,
        )

        session.expire_all()
        pkg_after = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert pkg_after.publication_status == PublicationStatusEnum.PUBLISHED.value

    def test_published_at_populated_on_transition(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """published_at is populated when package is published."""
        vector_writer = VectorWriter(chroma_client)
        ingestion_service.publish(
            session=session,
            package_id=ingestion_result.package_id,
            vector_writer=vector_writer,
        )
        session.expire_all()
        pkg = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert pkg.published_at is not None

    def test_play_time_queries_exclude_draft_packages(
        self,
        session: Any,
        ingestion_result: Any,
    ) -> None:
        """Play-time queries (default) exclude draft packages."""
        from uuid import UUID

        rps = RulesPackageService(session)
        # Package is still draft — should not be accessible at play time
        result = rps.get_chunks_by_subsystem(
            package_id=UUID(ingestion_result.package_id),
            subsystem=RuleSubsystemEnum.COMBAT,
            include_non_published=False,
        )
        assert result.chunks == []

    def test_internal_queries_include_draft_packages(
        self,
        session: Any,
        ingestion_result: Any,
    ) -> None:
        """include_non_published=True exposes draft packages."""
        from uuid import UUID

        rps = RulesPackageService(session)
        result = rps.get_chunks_by_subsystem(
            package_id=UUID(ingestion_result.package_id),
            subsystem=RuleSubsystemEnum.COMBAT,
            include_non_published=True,
        )
        assert len(result.chunks) > 0


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_rerun_no_duplicate_chunks(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Re-running ingestion does not create duplicate RuleChunk records."""
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        chunks = session.execute(select(RuleChunkORM)).scalars().all()
        assert len(chunks) == 24  # same as first run

    def test_rerun_no_duplicate_entities(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Re-running ingestion does not create duplicate MechanicalEntity records."""
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        entities = session.execute(select(MechanicalEntityORM)).scalars().all()
        assert len(entities) == 10  # same as first run

    def test_rerun_no_duplicate_sources(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Re-running ingestion does not create duplicate RuleSource records."""
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        sources = session.execute(select(RuleSourceORM)).scalars().all()
        assert len(sources) == 1

    def test_second_run_skipped_counts(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Second ingestion run reports expected skipped counts."""
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        result2 = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        assert result2.chunks_written == 0
        assert result2.chunks_skipped == 24
        assert result2.entities_written == 0
        assert result2.entities_skipped == 10

    def test_second_source_with_overlapping_section_paths_creates_new_chunks(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Two sources with identical section paths each persist their own chunks.

        Regression test for P1 (line 385): before the fix, chunk deduplication
        was keyed only on source_locator_value at package scope, so a second
        source with overlapping paths would silently drop all its chunks.
        """
        # First ingest using the default source ("Test Source")
        result1 = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        assert result1.chunks_written == 24

        # Second ingest using a different source — same section paths
        second_config = IngestionConfig(
            package_name="Test SRD",
            package_version="5.2.1",
            system="d20",
            source_name="Supplement Source",
            source_category="supplement",
            source_precedence_rank=2,
        )
        second_service = IngestionService(second_config)
        result2 = second_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="supplement.json",
            chroma_client=chroma_client,
        )
        # Second source must write its own chunk rows, not skip them
        assert result2.chunks_written == 24
        assert result2.chunks_skipped == 0
        # Total in DB: 2 sources × 24 chunks each
        total = session.execute(select(RuleChunkORM)).scalars().all()
        assert len(total) == 48

    def test_second_source_with_overlapping_entity_names_creates_new_entities(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Two sources with the same entity names each persist their own rows.

        Regression test for P1 (line 440): before the fix, entity deduplication
        was keyed only on (entity_type, name) at package scope, so a second
        source with the same entity names would silently drop all its entities.
        """
        result1 = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        assert result1.entities_written == 10

        second_config = IngestionConfig(
            package_name="Test SRD",
            package_version="5.2.1",
            system="d20",
            source_name="Supplement Source",
            source_category="supplement",
            source_precedence_rank=2,
        )
        second_service = IngestionService(second_config)
        result2 = second_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="supplement.json",
            chroma_client=chroma_client,
        )
        # Second source must write its own entity rows
        assert result2.entities_written == 10
        assert result2.entities_skipped == 0
        total = session.execute(select(MechanicalEntityORM)).scalars().all()
        assert len(total) == 20

    def test_same_name_version_different_system_creates_separate_packages(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Packages with the same name+version but different system are distinct.

        Regression test for P1 (line 311): before the fix, _upsert_package
        keyed only on (name, version), so a second ruleset with the same
        name/version but a different system would silently reuse the first
        package row and merge both corpora under one rules_package_id.

        A pre-existing package with a hypothetical future system value is
        inserted directly (bypassing IngestionService) to simulate a second
        system that shares the same name/version as the default d20 package.
        """
        from datetime import UTC, datetime
        from uuid import uuid4

        # Insert a pre-existing package row with the same name/version but a
        # different system value (simulating a future system not yet in the enum)
        other_pkg_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        session.add(
            RulesPackageORM(
                rules_package_id=other_pkg_id,
                name="Test SRD",
                system="future_system",
                version="5.2.1",
                is_enabled=True,
                publication_status="draft",
                published_at=None,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        # Ingest with the default d20 system: must create a NEW package,
        # not reuse the pre-existing "future_system" row
        result = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )
        packages = session.execute(select(RulesPackageORM)).scalars().all()
        assert len(packages) == 2
        assert result.package_id != other_pkg_id


# ---------------------------------------------------------------------------
# Override immutability
# ---------------------------------------------------------------------------


class TestOverrideImmutability:
    def test_source_chunks_unchanged_after_override(
        self,
        session: Any,
        ingestion_result: Any,
    ) -> None:
        """Source RuleChunk content is unchanged by RuleOverride application."""
        from datetime import UTC, datetime
        from uuid import uuid4

        from afterworlds.persistence.orm.rules_package import RuleOverrideORM

        chunk = (
            session.execute(
                select(RuleChunkORM).where(
                    RuleChunkORM.rules_package_id == ingestion_result.package_id
                )
            )
            .scalars()
            .first()
        )
        assert chunk is not None
        original_content = chunk.content

        # Add a replace override
        now = datetime.now(UTC).isoformat()
        override = RuleOverrideORM(
            override_id=str(uuid4()),
            rules_package_id=ingestion_result.package_id,
            target_chunk_id=chunk.chunk_id,
            target_entity_id=None,
            override_origin="house_rule",
            override_operation="replace",
            override_payload='{"content": "Modified content"}',
            precedence=1,
            is_enabled=True,
            created_at=now,
        )
        session.add(override)
        session.commit()

        # Source chunk must be unchanged
        session.expire_all()
        refreshed_chunk = session.execute(
            select(RuleChunkORM).where(RuleChunkORM.chunk_id == chunk.chunk_id)
        ).scalar_one()
        assert refreshed_chunk.content == original_content

    def test_reingestion_does_not_mutate_existing_chunks(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """Re-ingestion does not mutate existing source chunk records."""
        chunk = (
            session.execute(
                select(RuleChunkORM).where(
                    RuleChunkORM.rules_package_id == ingestion_result.package_id
                )
            )
            .scalars()
            .first()
        )
        assert chunk is not None
        original_content = chunk.content
        original_created_at = chunk.created_at

        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        session.expire_all()
        refreshed = session.execute(
            select(RuleChunkORM).where(RuleChunkORM.chunk_id == chunk.chunk_id)
        ).scalar_one()
        assert refreshed.content == original_content
        assert refreshed.created_at == original_created_at


# ---------------------------------------------------------------------------
# Read surface
# ---------------------------------------------------------------------------


class TestReadSurface:
    def _publish(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Helper: publish the ingested package."""
        vector_writer = VectorWriter(chroma_client)
        ingestion_service.publish(
            session=session,
            package_id=ingestion_result.package_id,
            vector_writer=vector_writer,
        )

    def test_get_chunks_by_subsystem_combat(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_chunks_by_subsystem returns valid result for COMBAT."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        result = rps.get_chunks_by_subsystem(
            package_id=UUID(ingestion_result.package_id),
            subsystem=RuleSubsystemEnum.COMBAT,
        )
        assert result.subsystem == RuleSubsystemEnum.COMBAT
        assert len(result.chunks) == 3

    def test_get_chunks_by_subsystem_conditions(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_chunks_by_subsystem returns valid result for CONDITIONS."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        result = rps.get_chunks_by_subsystem(
            package_id=UUID(ingestion_result.package_id),
            subsystem=RuleSubsystemEnum.CONDITIONS,
        )
        assert result.subsystem == RuleSubsystemEnum.CONDITIONS
        assert len(result.chunks) == 3

    def test_get_chunks_by_subsystem_spells(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_chunks_by_subsystem returns valid result for SPELLS."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        result = rps.get_chunks_by_subsystem(
            package_id=UUID(ingestion_result.package_id),
            subsystem=RuleSubsystemEnum.SPELLS,
        )
        assert result.subsystem == RuleSubsystemEnum.SPELLS
        assert len(result.chunks) == 3

    def test_get_entity_by_type_and_name_spell(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_entity_by_type_and_name returns valid entity for a spell."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        entity = rps.get_entity_by_type_and_name(
            package_id=UUID(ingestion_result.package_id),
            entity_type=MechanicalEntityTypeEnum.SPELL,
            name="Fireball",
        )
        assert entity is not None
        assert entity.name == "Fireball"
        assert entity.entity_type == MechanicalEntityTypeEnum.SPELL

    def test_get_entity_by_type_and_name_condition(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_entity_by_type_and_name returns valid entity for a condition."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        entity = rps.get_entity_by_type_and_name(
            package_id=UUID(ingestion_result.package_id),
            entity_type=MechanicalEntityTypeEnum.CONDITION,
            name="Blinded",
        )
        assert entity is not None
        assert entity.name == "Blinded"
        assert entity.entity_type == MechanicalEntityTypeEnum.CONDITION

    def test_get_active_rule_slice(
        self,
        session: Any,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """get_active_rule_slice returns valid typed payload for multiple subsystems."""
        from uuid import UUID

        self._publish(session, ingestion_result, chroma_client, ingestion_service)
        rps = RulesPackageService(session)
        result = rps.get_active_rule_slice(
            package_id=UUID(ingestion_result.package_id),
            subsystem_tags=[
                RuleSubsystemEnum.COMBAT,
                RuleSubsystemEnum.CONDITIONS,
                RuleSubsystemEnum.SPELLS,
            ],
            entity_refs=[
                (MechanicalEntityTypeEnum.SPELL, "Fireball"),
                (MechanicalEntityTypeEnum.CONDITION, "Blinded"),
            ],
        )
        assert result.package_id == UUID(ingestion_result.package_id)
        assert len(result.chunks) == 9  # 3 per subsystem × 3 subsystems
        assert len(result.entities) == 2


# ---------------------------------------------------------------------------
# Vector index
# ---------------------------------------------------------------------------


class TestVectorIndex:
    def test_chroma_collection_populated_after_ingest(
        self,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """ChromaDB collection is populated after ingest."""
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.has_chunks(ingestion_result.package_id)

    def test_basic_semantic_query_returns_results(
        self,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """Basic semantic query returns results without error."""
        vector_writer = VectorWriter(chroma_client)
        result = vector_writer.query(
            query_text="fire damage spell",
            package_id=ingestion_result.package_id,
            n_results=3,
        )
        assert len(result.chunk_ids) > 0
        assert len(result.documents) > 0

    def test_vector_metadata_source_document_is_file_name(
        self,
        ingestion_result: Any,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """source_document metadata field stores the file name, not section path.

        Regression test: write_chunks() stored chunk.section_path in the
        source_document field instead of the source file name passed to ingest().
        Fix threads source_document_name through write_chunks() and reads
        source_document (not source_locator_value) in _repopulate_vector_index.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        result = collection.get(include=["metadatas"])
        metadatas = result["metadatas"]
        assert metadatas, "collection must contain documents after ingest"
        for meta in metadatas:
            assert meta is not None
            doc_name = meta.get("source_document")
            # Must be the source file name, not a section-path string
            assert (
                doc_name == "test_srd.json"
            ), f"source_document metadata should be 'test_srd.json', got {doc_name!r}"

    def test_vector_writer_no_chunks_has_chunks_false(
        self,
        chroma_client: chromadb.ClientAPI,
    ) -> None:
        """has_chunks returns False for a package with no vector data."""
        vector_writer = VectorWriter(chroma_client)
        assert not vector_writer.has_chunks("nonexistent-package-id")

    def test_reingest_repopulates_vector_index_after_collection_reset(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """Re-ingest repopulates Chroma when the collection is deleted/reset.

        Regression test for P1 (line 195): before the fix, re-ingest skipped
        all SQL-existing chunks, wrote 0 vectors, and left vector_write_complete
        stuck at False permanently.
        """
        # Verify the collection exists after the first ingest
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.has_chunks(ingestion_result.package_id)

        # Delete the Chroma collection to simulate a storage reset
        from afterworlds.ingestion.vector_writer import _collection_name

        chroma_client.delete_collection(_collection_name(ingestion_result.package_id))
        assert not vector_writer.has_chunks(ingestion_result.package_id)

        # Re-ingest: all SQL chunks will be skipped, but vector should repopulate
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        # Vector index must be repopulated and manifest flag must be True
        assert vector_writer.has_chunks(ingestion_result.package_id)
        manifest = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert manifest.vector_write_complete is True

    def test_distinct_packages_use_separate_collections(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
    ) -> None:
        """Two packages with the same UUID prefix write to separate collections.

        Regression test for P2 (vector_writer.py line 55): before the fix,
        _collection_name truncated to 8 hex chars, so two packages sharing
        the same 8-char prefix used the same Chroma collection, causing
        cross-contaminated results and incorrect has_chunks() gating.
        """
        # First ingest creates package A
        result_a = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="a.json",
            chroma_client=chroma_client,
        )

        # Craft package B whose UUID shares the same first 8 hex chars as A
        pid_a = result_a.package_id  # e.g. "aabbccdd-xxxx-..."
        prefix = pid_a.replace("-", "")[:8]
        # Build a distinct UUID that differs only after the 8th hex char
        colliding_suffix = "0" * 24
        pkg_b_id = (
            f"{prefix}{colliding_suffix[:4]}-"
            f"{colliding_suffix[4:8]}-"
            f"{colliding_suffix[8:12]}-"
            f"{colliding_suffix[12:16]}-"
            f"{colliding_suffix[16:]}"
        )
        if pkg_b_id == pid_a:
            # Extremely unlikely; ensure they differ
            colliding_suffix = "f" * 24
            pkg_b_id = (
                f"{prefix}{colliding_suffix[:4]}-"
                f"{colliding_suffix[4:8]}-"
                f"{colliding_suffix[8:12]}-"
                f"{colliding_suffix[12:16]}-"
                f"{colliding_suffix[16:]}"
            )
        assert pkg_b_id != pid_a

        vector_writer = VectorWriter(chroma_client)
        # Write a single doc directly to package B's collection
        vector_writer.write_chunks_raw(
            package_id=pkg_b_id,
            chunk_ids=["test-chunk-b"],
            contents=["Package B content"],
            subsystems=["combat"],
            source_documents=["b.json"],
        )

        # Package A's collection must report only package A's chunks
        collection_a = chroma_client.get_collection(
            f"rp_chunks_interim_{pid_a.replace('-', '')}"
        )
        ids_a = collection_a.get()["ids"]
        assert "test-chunk-b" not in ids_a

        # Package B must be independently queryable
        assert vector_writer.has_chunks(pkg_b_id)

    def test_partial_vector_loss_triggers_repopulation_on_reingest(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """Re-ingest restores full Chroma coverage after partial-loss.

        Regression test for P1 (line 203): the old repopulation trigger was
        `has_chunks() == False` (total-loss only). After partial deletion, Chroma
        is non-empty so repopulation was skipped, leaving the index incomplete
        and vector_complete potentially True despite missing chunks.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Simulate partial-loss by deleting some Chroma documents
        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        all_ids = collection.get()["ids"]
        sql_total = len(all_ids)
        collection.delete(ids=all_ids[:5])
        assert collection.count() == sql_total - 5

        # Re-ingest: SQL skips all existing chunks, but Chroma count < sql_count
        # triggers repopulation of the full set
        ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        # Full coverage must be restored
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.count_chunks(ingestion_result.package_id) == sql_total

        # Manifest must record completion
        manifest = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == ingestion_result.package_id
            )
        ).scalar_one()
        assert manifest.vector_write_complete is True

    def test_reingest_repopulates_when_single_document_survives_partial_loss(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """Re-ingest detects partial-loss via count-parity and restores full coverage.

        Scenario: all but one Chroma document are deleted (partial-loss that leaves
        the collection non-empty).  A subsequent ingest() must detect the shortfall
        via count_chunks() < sql_count, repopulate from SQL, and record
        vector_write_complete=True with the full chunk count in Chroma.

        Regression test for P1 (line 203): before the fix, vector_complete was
        derived from has_chunks(), so this single-survivor state would pass the
        completeness check and the missing chunks would never be recovered.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Partial-loss: delete all but one document
        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        all_ids = collection.get()["ids"]
        collection.delete(ids=all_ids[1:])  # keep exactly one
        assert collection.count() == 1

        # Ingest a fresh session with a new source to force a new ingest run
        # without adding any new SQL chunks (all 24 from original source exist)
        # — the count mismatch should still be detected and repopulated.
        result = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        # After re-ingest the manifest must be True (repopulation ran)
        session.expire_all()
        manifest = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == result.package_id
            )
        ).scalar_one()
        assert manifest.vector_write_complete is True
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.count_chunks(result.package_id) == len(all_ids)

    def test_vector_chunks_written_nonzero_after_repopulation(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """vector_chunks_written reflects repopulated count, not just new SQL inserts.

        Regression test for P2 (line 199): before the fix, vector_chunks_written
        was always set from len(written_chunks), so idempotent re-runs that
        triggered Chroma repopulation still reported 0 vector writes.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Delete the Chroma collection entirely (total-loss)
        chroma_client.delete_collection(_collection_name(ingestion_result.package_id))

        # Re-ingest: SQL skips all 24 chunks (written=0) but repopulates Chroma
        result = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        assert result.chunks_written == 0  # all SQL chunks already existed
        assert result.vector_chunks_written > 0  # repopulation count reported

    def test_surplus_vector_count_triggers_repopulation_on_reingest(
        self,
        session: Any,
        srd_data_fixture: dict[str, Any],
        chroma_client: chromadb.ClientAPI,
        ingestion_service: IngestionService,
        ingestion_result: Any,
    ) -> None:
        """Re-ingest detects surplus Chroma docs (count > sql_count) and rebuilds.

        Scenario: a run writes vectors and then fails before SQL commit, leaving
        extra Chroma documents with no corresponding SQL rows.  On the next run
        count > sql_count; upsert alone cannot remove the surplus so the
        repopulation path must delete-and-rebuild to restore exact parity.

        Regression test for P1: before this fix the trigger was
        ``count < sql_count``, so surplus was silently ignored and the package
        was left with ``vector_write_complete=False`` permanently.
        """
        from afterworlds.ingestion.vector_writer import _collection_name

        # Simulate surplus: manually add an extra doc that has no SQL row
        collection = chroma_client.get_collection(
            _collection_name(ingestion_result.package_id)
        )
        original_count = collection.count()
        collection.upsert(
            documents=["phantom doc with no SQL row"],
            metadatas=[
                {
                    "package_id": ingestion_result.package_id,
                    "chunk_id": "phantom-id",
                    "subsystem": "combat",
                    "source_document": "phantom.json",
                }
            ],
            ids=["phantom-id"],
        )
        assert collection.count() == original_count + 1

        # Re-ingest: count > sql_count should trigger delete-and-rebuild
        result = ingestion_service.ingest(
            session=session,
            srd_data=srd_data_fixture,
            source_file_name="test_srd.json",
            chroma_client=chroma_client,
        )

        # After re-ingest collection must match SQL exactly (no phantom)
        session.expire_all()
        manifest = session.execute(
            select(RulesPackageManifestORM).where(
                RulesPackageManifestORM.rules_package_id == result.package_id
            )
        ).scalar_one()
        assert manifest.vector_write_complete is True
        vector_writer = VectorWriter(chroma_client)
        assert vector_writer.count_chunks(result.package_id) == original_count


# ---------------------------------------------------------------------------
# SRD Parser unit tests
# ---------------------------------------------------------------------------


class TestSRDParser:
    def test_parse_chunks_valid(self, srd_data_fixture: dict[str, Any]) -> None:
        parser = SRDParser()
        chunks = parser.parse_chunks(srd_data_fixture)
        assert len(chunks) == 24

    def test_parse_entities_valid(self, srd_data_fixture: dict[str, Any]) -> None:
        parser = SRDParser()
        entities = parser.parse_entities(srd_data_fixture)
        assert len(entities) == 10

    def test_parse_chunks_blank_section_path_raises(self) -> None:
        """parse_chunks raises ParseError for missing/blank/whitespace section_path.

        Regression test: blank and whitespace-only section_path values collapse
        multiple sections onto the same dedup key in _persist_chunks, causing
        silent data loss during ingestion.
        """
        parser = SRDParser()
        for bad_path in ("", None, "   "):
            bad_data: dict[str, Any] = {
                "sections": [
                    {
                        "heading": "Attack Rolls",
                        "content": "Roll d20.",
                        "subsystem": "combat",
                        "section_path": bad_path,
                        "page_ref": "p. 1",
                    }
                ],
                "entities": [],
            }
            with pytest.raises(ParseError, match="section_path is missing or blank"):
                parser.parse_chunks(bad_data)

    def test_parse_entities_blank_section_path_raises(self) -> None:
        """parse_entities raises ParseError for missing/blank/whitespace section_path.

        Mirrors the same validation as parse_chunks: blank and whitespace-only
        section_path values collapse multiple entities onto the same dedup key
        in _persist_entities, causing silent data loss.
        """
        parser = SRDParser()
        for bad_path in ("", None, "   "):
            bad_data: dict[str, Any] = {
                "sections": [],
                "entities": [
                    {
                        "entity_type": "spell",
                        "name": "Fireball",
                        "subsystem": "spells",
                        "section_path": bad_path,
                        "page_ref": "p. 1",
                        "data": {
                            "casting_time": "1 action",
                            "range": "150 feet",
                            "components": "V, S, M",
                            "duration": "Instantaneous",
                            "description": "A bright streak flashes.",
                            "level": 3,
                            "school": "Evocation",
                        },
                    }
                ],
            }
            with pytest.raises(ParseError, match="section_path is missing or blank"):
                parser.parse_entities(bad_data)

    def test_parse_chunks_bad_subsystem_raises(self) -> None:
        parser = SRDParser()
        bad_data: dict[str, Any] = {
            "sections": [
                {
                    "heading": "Test",
                    "content": "Content",
                    "subsystem": "not_a_real_subsystem",
                    "section_path": "x/y",
                    "page_ref": "p. 1",
                }
            ],
            "entities": [],
        }
        with pytest.raises(ParseError, match="Unrecognised subsystem"):
            parser.parse_chunks(bad_data)

    def test_parse_entities_bad_entity_type_raises(self) -> None:
        parser = SRDParser()
        bad_data: dict[str, Any] = {
            "sections": [],
            "entities": [
                {
                    "entity_type": "dragon",
                    "name": "Test",
                    "subsystem": "combat",
                    "section_path": "x/y",
                    "page_ref": "p. 1",
                    "data": {},
                }
            ],
        }
        with pytest.raises(ParseError, match="Unrecognised entity_type"):
            parser.parse_entities(bad_data)

    def test_parse_entities_bad_data_raises(self) -> None:
        parser = SRDParser()
        bad_data: dict[str, Any] = {
            "sections": [],
            "entities": [
                {
                    "entity_type": "spell",
                    "name": "BadSpell",
                    "subsystem": "spells",
                    "section_path": "spells/bad",
                    "page_ref": "p. 1",
                    "data": {
                        # Missing required fields for SpellEntity
                    },
                }
            ],
        }
        with pytest.raises(ParseError, match="Entity data validation failed"):
            parser.parse_entities(bad_data)

    def test_subsystem_enum_values_match(
        self, srd_data_fixture: dict[str, Any]
    ) -> None:
        """All parsed subsystems are valid RuleSubsystemEnum values."""
        parser = SRDParser()
        chunks = parser.parse_chunks(srd_data_fixture)
        for chunk in chunks:
            assert chunk.subsystem in RuleSubsystemEnum

    def test_entity_type_enum_values_match(
        self, srd_data_fixture: dict[str, Any]
    ) -> None:
        """All parsed entity types are valid MechanicalEntityTypeEnum values."""
        parser = SRDParser()
        entities = parser.parse_entities(srd_data_fixture)
        for ent in entities:
            assert ent.entity_type in MechanicalEntityTypeEnum
