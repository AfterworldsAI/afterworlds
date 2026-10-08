"""The ``equipment`` proposal, offered for review -- CRD Issue 5d.

The whole *Equipment* part -- coins, weapons with their properties, mastery
and table, armor and armor training, tools and tool proficiency, adventuring
gear with packs and foci, mounts and vehicles, lifestyle, food, lodging,
hirelings and spellcasting services, the general magic-item rules, and
crafting, brewing and scribing -- proposed by
``.claude/review-notes/issue-5d-equipment-generator.py`` from the release 5c
actually publishes. Nothing here records it; its acceptance is held by
``test_equipment_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* scope is the whole part less its title, one section record each, and no
  leaf is owned by an accepted unit;
* the batch checks report exactly the out-of-batch targets and nothing else;
* fidelity: every component stays prose-bound; each table is the release's
  own rows, with the prose that introduces it; each priced heading stays with
  its item; each artisan's tool keeps its ability, weight, utilize and craft
  lines; and a GameMaster reads every passage in printed order;
* references: in-batch pointers name the record of what they cite, accepted
  glossary terms are cited, unauthored parts stay explicit unresolved
  references, and "Improvised Weapons" is an unknown target;
* membership (Owner Decision 2026-09-24): each named item or rule is a
  ``CATALOGUE_MEMBER`` of its section, which no longer reads the member's
  prose; through the production service a section reads its own passages and
  its members interleaved in printed order, table rows included, a member
  selected with its section reads once, a disabled member stays gone and a
  replaced one reads replaced where it is printed;
* every word of every spanned leaf is claimed, only headings are excluded,
  and a dropped table, table row, priced heading, tool line or component is
  reported;
* composed *in this test only* with the twelve-batch acceptance it was
  reviewed over, re-derived through the approved chain: every accepted glossary
  target closes, exactly the batch's 375 leaves gain coverage and the six
  recorded resolutions still apply;
* the forty-three resolution drafts name accepted citations exactly, cannot
  apply while their targets are unaccepted, and -- in memory only -- resolve
  once the batch is accepted, leaving exactly the two whole-part citations.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.accounting import validate_acceptance
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    ReferenceDraft,
    RelationshipKind,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.services.rules_authority.application import (
    AuthoredProse,
    EffectiveAuthority,
    SourceProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import source_leaf_order
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from afterworlds.services.rules_authority.views import (
    GameMasterComponent,
    build_gamemaster_view,
)
from tests.ingestion.mechanical._replacement_chain import (
    current,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _disable,
    _request,
    _service,
    _sliced,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-equipment-generator.py"
#: Regenerated over the corrected release; the Owner accepted it exactly.
PROPOSAL = proposal_path("equipment")
IDENTITY = identity("equipment")

GLOSSARY = "srd-5.2.1/rules-glossary"
EQUIPMENT = "srd-5.2.1/equipment"
PRIOR_RESOLUTIONS = [
    "resolve-attack-roll-playing-the-game-1",
    "resolve-armor-class-character-creation-1",
    "resolve-proficiency-bonus-character-creation-1",
    "resolve-choose-background-character-origins-1",
    "resolve-choose-species-character-origins-1",
    "resolve-background-feat-feats-1",
]


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: The pointers into unauthored parts, by scope.
NEW_UNRESOLVED = Counter(
    {
        "srd-5.2.1/classes": 3,
        "srd-5.2.1/gameplay-toolbox": 2,
        "srd-5.2.1/magic-items": 2,
        "srd-5.2.1/monsters": 1,
        "srd-5.2.1/spells": 1,
    }
)
#: Accepted glossary entries this batch cites; each is an unknown target to
#: the batch alone and closes composed.
GLOSSARY_TARGETS = {
    "armor_class",
    "attack",
    "attack_roll",
    "burning",
    "carrying_capacity",
    "damage_roll",
    "damage_threshold",
    "dehydration",
    "grappled",
    "high_jump",
    "hit_points",
    "immunity",
    "incapacitated",
    "indifferent",
    "long_jump",
    "malnutrition",
    "opportunity_attacks",
    "poisoned",
    "prone",
    "reach",
    "restrained",
    "short_rest",
    "speed",
    "stat_block",
    "unconscious",
    "utilize",
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("equipment", GENERATOR)


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.fixture(scope="module")
def built(session):  # type: ignore[no-untyped-def]
    return GEN.build(session)


@pytest.fixture(scope="module")
def prior() -> AcceptedInputs:
    """The twelve-batch acceptance, all six resolutions included.

    Re-derived through the recorded replacement chain, not read from the
    committed file, which now also holds this batch and later ones;
    ``test_character_origins_feats_acceptance`` holds it inside that file.
    """
    inputs: AcceptedInputs = through("character-origins-feats")
    return inputs


#: The clauses a named record owns whole; its section no longer reads them.
WHOLE = {(e, k) for e, k, _ in GEN.NAMED_CLAUSES}


def _holder(entry: str, key: str) -> str:
    """The record whose component reads clause *key* of *entry*."""
    return f"equipment.{entry}.{key}" if (entry, key) in WHOLE else f"equipment.{entry}"


def _texts(built, record: str, key: str) -> list[str]:  # type: ignore[no-untyped-def]
    """The source texts one component's prose bindings are read from."""
    spans = {s.span_id: s for s in built.ledger.spans}
    out = []
    for b in built.proposal.proposed_representation.prose_bindings:
        if (b.record_key, b.component_key) == (record, key):
            s = spans[b.span_id]
            out.append(built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end])
    return out


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_committed_bytes_are_the_recorded_proposal(built) -> None:  # type: ignore[no-untyped-def]
    assert proposal_identity(load_proposal(PROPOSAL, expected_identity=IDENTITY)) == (
        IDENTITY
    )
    assert b"\r" not in PROPOSAL.read_bytes()
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding


def test_the_artifact_is_an_unaccepted_proposal_by_shape() -> None:
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert (
        json.loads(PROPOSAL.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    )
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)


UNITS = [
    ("coins", 4),
    ("weapons", 35),
    ("armor", 13),
    ("tools", 51),
    ("adventuring_gear", 178),
    ("mounts_and_vehicles", 23),
    ("lifestyle_expenses", 18),
    ("food_drink_and_lodging", 3),
    ("hirelings", 3),
    ("spellcasting", 3),
    ("magic_items", 22),
    ("crafting_nonmagical_items", 11),
    ("brewing_potions_of_healing", 2),
    ("scribing_spell_scrolls", 9),
]


def test_scope_is_the_whole_part_less_its_title(session, built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, u.kind, len(u.leaf_ids)) for u in units] == [
        (f"equipment/{s}", ReviewUnitKind.SECTION, n) for s, n in UNITS
    ]
    records = built.proposal.proposed_representation.records
    sections, named = records[:14], records[14:]
    assert [r.semantic_key for r in sections] == [f"equipment.{s}" for s, _ in UNITS]
    assert [r.kind for r in sections] == [RecordKind.EQUIPMENT] * 10 + [
        RecordKind.GENERAL_RULE
    ] * 4
    # Then the items and rules a citation names, and the rules the cited
    # weapon and armor rows print, each a member of its own section.
    assert [(r.semantic_key, r.kind) for r in named] == [
        (k, kind) for k, kind, _ in GEN.batch().records
    ]
    assert len(named) == 66
    # Contiguous, in printed order, and the title before it is owned by no unit.
    flat = [
        built.leaf_rows[leaf].occurrence_index for u in units for leaf in u.leaf_ids
    ]
    assert sorted(flat) == list(range(flat[0], flat[0] + 375))
    (title,) = session.query(
        LedgerLeafORM.content, LedgerLeafORM.container_path
    ).filter(
        LedgerLeafORM.package_uuid == built.binding.package_uuid,
        LedgerLeafORM.occurrence_index == min(flat) - 1,
    )
    assert title.content == "# Equipment"
    (root,) = title.container_path
    under = session.query(
        LedgerLeafORM.occurrence_index, LedgerLeafORM.container_path
    ).filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
    assert sorted(o for o, path in under if path[0] == root) == [
        min(flat) - 1,
        *sorted(flat),
    ]
    # Each unit's leaves are its own section's, in printed order.
    for u in units:
        order = [built.leaf_rows[leaf].occurrence_index for leaf in u.leaf_ids]
        assert order == sorted(order), u.unit_id


def test_no_leaf_is_owned_by_an_accepted_unit(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # Both sides are the superseded release's state, never mixed with the current.
    assert recorded.binding == prior.oracle.binding
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert len(mine) == 375
    assert not owned & mine


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    unresolved = [f for f in found["representation"] if "unresolved" in f]
    assert Counter(f.split(":")[0].removeprefix("reference ") for f in unresolved) == (
        NEW_UNRESOLVED
    )
    unknown = {
        f.rsplit("glossary.", 1)[1]
        for f in found["representation"]
        if "unknown target record" in f
    }
    assert unknown == GLOSSARY_TARGETS | {"improvised_weapons"}
    assert len(found["representation"]) == 86


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def test_every_component_stays_faithful_prose(built) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    assert len(components) == 207
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    text = PROPOSAL.read_text("utf-8")
    for family in ("EquipmentDescriptorFact", "WeaponPropertyFact"):
        assert family not in text


def test_latitude_and_context_are_only_where_the_rule_leaves_them(built) -> None:  # type: ignore[no-untyped-def]
    by_reason: dict[str, list[tuple[str, str]]] = {}
    for c in built.proposal.proposed_representation.components:
        reason = c.irreducibility_reason_code or c.prose_retention_reason_code
        by_reason.setdefault(reason, []).append(
            (c.record_key.removeprefix("equipment."), c.semantic_key)
        )
    assert Counter({k: len(v) for k, v in by_reason.items()}) == {
        "no_identified_structured_use": 194,
        "contextual_applicability": 7,
        "gamemaster_latitude": 6,
    }

    # Each clause is read once, where it lives: a named item keeps its
    # clause's reason, and its section no longer reads it.
    def where(clauses: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
        return sorted((_holder(e, k).removeprefix("equipment."), k) for e, k in clauses)

    assert sorted(by_reason["gamemaster_latitude"]) == where(GEN.GM_LATITUDE)
    assert sorted(by_reason["contextual_applicability"]) == where(GEN.CONTEXTUAL)
    assert len([c for c in GEN.CONTEXTUAL if c in WHOLE]) == 5


#: Each table: its clause, the prose it follows (``None``: the table is the
#: whole component), its position in the component reading it and its printed
#: row count (header, group and data rows). A named item's component reads its
#: gear row under the table head first.
TABLES = [
    ("COIN_VALUES_TABLE", "coins", "coin_values", "Characters often find coins", 1, 6),
    ("WEAPONS_TABLE", "weapons", "weapons_table", "The Weapons table", 1, 43),
    ("ARMOR_TABLE", "armor", "armor_table", "The Armor table", 1, 18),
    (
        "ADVENTURING_GEAR_TABLE",
        "adventuring_gear",
        "adventuring_gear_table",
        "The Adventuring Gear table",
        1,
        83,
    ),
    ("AMMUNITION_TABLE", "adventuring_gear", "ammunition", "#### Ammunition", 2, 6),
    ("ARCANE_FOCUSES_TABLE", "adventuring_gear", "arcane_focus", "#### Arcane", 4, 6),
    (
        "DRUIDIC_FOCUSES_TABLE",
        "adventuring_gear",
        "druidic_focus",
        "#### Druidic",
        4,
        4,
    ),
    ("HOLY_SYMBOLS_TABLE", "adventuring_gear", "holy_symbol", "#### Holy Symbol", 5, 4),
    ("MOUNTS_TABLE", "mounts_and_vehicles", "mounts", "A mount can help", 1, 9),
    (
        "TACK_TABLE",
        "mounts_and_vehicles",
        "tack_harness_and_drawn_vehicles",
        None,
        0,
        12,
    ),
    (
        "VEHICLES_TABLE",
        "mounts_and_vehicles",
        "large_vehicles",
        "The Airborne and Waterborne Vehicles table",
        1,
        8,
    ),
    (
        "FOOD_DRINK_AND_LODGING_TABLE",
        "food_drink_and_lodging",
        "food_drink_and_lodging",
        "The Food, Drink, and Lodging table",
        1,
        21,
    ),
    ("HIRELINGS_TABLE", "hirelings", "hirelings", "Skilled hirelings", 1, 4),
    (
        "SPELLCASTING_SERVICES_TABLE",
        "spellcasting",
        "spellcasting_services",
        "Most settlements",
        1,
        8,
    ),
    (
        "SPELL_SCROLL_COSTS_TABLE",
        "scribing_spell_scrolls",
        "time_and_cost",
        "Scribing a scroll",
        1,
        11,
    ),
]


#: The tables a citation names a row of, and their pieces.
SPLIT = {
    "WEAPONS_TABLE": "WEAPONS_PIECES",
    "ARMOR_TABLE": "ARMOR_PIECES",
    "ADVENTURING_GEAR_TABLE": "GEAR_PIECES",
    "AMMUNITION_TABLE": "AMMUNITION_PIECES",
}


@pytest.mark.parametrize(("name", "entry", "key", "intro", "at", "rows"), TABLES)
def test_each_table_is_the_release_s_own_rows_after_its_prose(  # type: ignore[no-untyped-def]
    session, built, name, entry, key, intro, at, rows
) -> None:
    table = getattr(GEN, name)
    record = _holder(entry, key)
    texts = _texts(built, record, key)
    # A table with a named row is read as its contiguous pieces, which rejoin
    # to the whole table byte for byte. A named record owns its rows; the
    # clause reads every other piece in order, the head and group rows the
    # named rows are read under included.
    pieces = getattr(GEN, SPLIT[name]) if name in SPLIT else (table,)
    assert "".join(pieces) == table
    owned = {t for c in GEN.COMPONENTS if c.record for t in c.texts} - {
        t for c in GEN.COMPONENTS for t in c.context
    }
    kept = [p for p in pieces if p not in owned]
    assert texts[at : at + len(kept)] == kept
    # Written as rows, located verbatim: the release's own leaf, byte for byte.
    assert (
        session.query(LedgerLeafORM.content)
        .filter(
            LedgerLeafORM.package_uuid == built.binding.package_uuid,
            LedgerLeafORM.content == table,
        )
        .count()
        == 1
    )
    if intro is not None:
        assert any(t.startswith(intro) for t in texts[:at])
    assert table.count("<tr>") == rows
    # No other section component holds any of it: a named row is read by its
    # record alone, and another piece only by this clause and, as the rows
    # they are read under, by named records.
    named = {k for k, _, _ in GEN.batch().records}
    for piece in pieces:
        holders = [
            (c.record_key, c.semantic_key)
            for c in built.proposal.proposed_representation.components
            if piece in _texts(built, c.record_key, c.semantic_key)
        ]
        if piece in owned:
            ((holder, _),) = holders
            assert holder in named, piece[:40]
        else:
            assert (record, key) in holders
            assert {r for r, _ in holders} - {record} <= named, piece[:40]


@pytest.mark.parametrize(
    ("needle", "table"),
    [
        # Cost, weight, damage, properties and mastery on one weapon row.
        (
            "<td>Longbow</td>\n      <td>1d8 Piercing</td>\n      <td>Ammunition"
            " (Range 150/600; Arrow), Heavy, Two-Handed</td>\n      <td>Slow</td>",
            "WEAPONS_TABLE",
        ),
        # Armor Class formula, Strength, Stealth, weight and cost on one row.
        ("<td>Plate Armor</td>", "ARMOR_TABLE"),
        ("<td>1,500 GP</td>", "ARMOR_TABLE"),
        # Group rows that scope the rows beneath them.
        ('<th colspan="6"><em>Simple Melee Weapons</em></th>', "WEAPONS_TABLE"),
        ('<th colspan="6"><em>Martial Ranged Weapons</em></th>', "WEAPONS_TABLE"),
        (
            '<th colspan="6"><em>Heavy Armor'
            " (10 Minutes to Don and 5 Minutes to Doff)</em></th>",
            "ARMOR_TABLE",
        ),
    ],
)
def test_table_rows_keep_their_cells_and_groups_together(needle, table) -> None:  # type: ignore[no-untyped-def]
    assert needle in getattr(GEN, table)


def test_each_priced_heading_stays_with_its_item(built) -> None:  # type: ignore[no-untyped-def]
    # A gear item's price is printed only in its heading; dropping the heading
    # would drop the price. A named item reads it after its gear row.
    gear = [
        k
        for e, k, _, _ in GEN.CLAUSES
        if e == "adventuring_gear" and k != "adventuring_gear_table"
    ]
    assert len(gear) == 81
    assert len([k for k in gear if ("adventuring_gear", k) in WHOLE]) == 29
    for key in gear:
        context, rows = GEN.ROWS_OF.get(("adventuring_gear", key), ((), ()))
        texts = _texts(built, _holder("adventuring_gear", key), key)
        assert texts[: len(context) + len(rows)] == [*context, *rows], key
        head, *body = texts[len(context) + len(rows) :]
        assert head.startswith("#### ") and head.endswith(")"), key
        # "(Varies)" items price each form in their own table.
        assert any(unit in head for unit in ("GP", "SP", "CP", "(Varies)")), key
        assert body, key
    heads = [
        _texts(built, "equipment.lifestyle_expenses", key)[0]
        for key in (
            "wretched",
            "squalid",
            "poor",
            "modest",
            "comfortable",
            "wealthy",
            "aristocratic",
        )
    ]
    assert heads == [
        "### Wretched (Free)",
        "### Squalid (1 SP per Day)",
        "### Poor (2 SP per Day)",
        "### Modest (1 GP per Day)",
        "### Comfortable (2 GP per Day)",
        "### Wealthy (4 GP per Day)",
        "### Aristocratic (10 GP per Day)",
    ]


ARTISANS = (
    "alchemists_supplies",
    "brewers_supplies",
    "calligraphers_supplies",
    "carpenters_tools",
    "cartographers_tools",
    "cobblers_tools",
    "cooks_utensils",
    "glassblowers_tools",
    "jewelers_tools",
    "leatherworkers_tools",
    "masons_tools",
    "painters_supplies",
    "potters_tools",
    "smiths_tools",
    "tinkers_tools",
    "weavers_tools",
    "woodcarvers_tools",
)


@pytest.mark.parametrize("key", ARTISANS)
def test_each_artisan_s_tool_keeps_its_price_ability_weight_utilize_and_craft(  # type: ignore[no-untyped-def]
    built, key
) -> None:
    # Its own clause, past the shared tool rules a named tool reads first.
    shared = (*GEN.TOOL_RULES, *GEN.clause("tools", "artisans_tools"))
    own = [t for t in _texts(built, _holder("tools", key), key) if t not in shared]
    joined = "\n".join(own)
    assert joined.startswith("**") and " GP)**" in joined.split("\n")[0]
    for label in ("**Ability:**", "**Weight:**", "**Utilize:**", "**Craft:**"):
        assert joined.count(label) == 1, label


def test_the_corrected_release_renders_the_lodging_groups_and_vehicle_caption() -> None:
    # The source correction (issue-5c-5d-community-source-corrections.md):
    # the lodging table is one ``Item | Cost`` list in page order, its three
    # groups as body rows rather than a second header row, and the vehicles
    # table carries its "Airborne and Waterborne Vehicles" caption.
    food = GEN.FOOD_DRINK_AND_LODGING_TABLE
    head, body = food.split("</thead>")
    assert head.count("<tr>") == 1 and head.count("<th>") == 2
    assert [g for g in ("Inn Stay per Day", "Meal", "Wine (bottle)") if g in body] == [
        "Inn Stay per Day",
        "Meal",
        "Wine (bottle)",
    ]
    assert body.index("Inn Stay per Day") < body.index("<em>Meal</em>")
    assert body.index("<em>Meal</em>") < body.index("Wine (bottle)")
    assert GEN.VEHICLES_TABLE.startswith("**Airborne and Waterborne Vehicles**")


def _candidate(built: Built) -> ProjectionCandidate:
    return ProjectionCandidate(
        binding=built.binding,
        classification=built.ledger,
        representation=built.proposal.proposed_representation,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )


def _gamemaster(
    session: Session, built: Built, *entries: EffectiveOverrideEntry
) -> list[GameMasterComponent]:
    """The whole batch's GameMaster view, sections read with their members."""
    return list(
        build_gamemaster_view(
            _authority(session, built, *entries), _prose(session, built)
        ).components
    )


def _prose(session: Session, built: Built) -> dict[str, str]:
    return {
        row.chunk_id: row.content
        for row in session.query(RuleChunkORM).filter(
            RuleChunkORM.rules_package_id == str(built.binding.package_uuid)
        )
    }


def _authority(
    session: Session, built: Built, *entries: EffectiveOverrideEntry
) -> EffectiveAuthority:
    candidate = _candidate(built)
    state = EffectiveOverrideSet(
        built.binding.package_uuid, built.binding.release_version, entries
    )
    return apply_override_set(
        candidate,
        state,
        RulesPackageBinding(
            package_uuid=UUID(built.binding.package_uuid),
            release_version=built.binding.release_version,
            mechanical_projection_uuid=UUID(
                identify_projection(candidate).projection_uuid
            ),
            override_set_uuid=UUID(state.override_set_uuid),
        ),
        leaf_order=source_leaf_order(session, candidate),
    )


#: Multi-passage components, and how many of them a chunk-id order misreads.
#: Chunk ids are ``uuid5`` over the package and leaf, so the second count is a
#: property of this release's ids; the printed-order assertion is the pin.
#: 62 on the current ``8781d4e0-a3b`` (72 on ``3fe24ff6-4e3``, 68 on
#: ``574662e9-0ef``).
MULTI, UNLIKE_CHUNKS = 120, 62


def test_a_gamemaster_reads_every_component_in_printed_order(session, built) -> None:  # type: ignore[no-untyped-def]
    # A component can read in runs, split where another is printed between its
    # passages; together the runs are what it owns, once. Context a member
    # reads -- its table head -- is read by its owner, where it is printed.
    whole = _gamemaster(session, built)
    view: dict[tuple[str, str], list[GameMasterComponent]] = {}
    for part in whole:
        view.setdefault((part.record_key, part.component_key), []).append(part)
    assert sorted(view) == sorted(
        (c.record_key, c.semantic_key)
        for c in built.proposal.proposed_representation.components
    )
    primary = _primary(built)
    read = [
        (c.record_key, c.component_key, e.span_id)
        for c in whole
        for e in c.governing_prose
        if isinstance(e, SourceProse)
    ]
    assert sorted(read) == sorted(primary)
    spans = {s.span_id: s for s in built.ledger.spans}
    multi = unlike_chunks = 0
    for key, parts in view.items():
        passages = [
            e for c in parts for e in c.governing_prose if isinstance(e, SourceProse)
        ]
        printed = [primary[(*key, e.span_id)] for e in passages]
        assert printed == sorted(printed), key
        assert Counter(e.text for e in passages) == Counter(
            built.leaf_rows[spans[s].leaf_id].content[
                spans[s].char_start : spans[s].char_end
            ]
            for r, c, s in primary
            if (r, c) == key
        ), key
        multi += len(passages) > 1
        chunks = [e.chunk_id for e in passages]
        unlike_chunks += chunks != sorted(chunks)
        assert all(c.structured_context == () for c in parts)
    assert (multi, unlike_chunks) == (MULTI, UNLIKE_CHUNKS)


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def test_in_batch_pointers_name_the_record_of_what_they_cite(built) -> None:  # type: ignore[no-untyped-def]
    refs = built.proposal.proposed_representation.references
    named = [r for r in refs if r.scope_key == EQUIPMENT]
    records = {r.semantic_key for r in built.proposal.proposed_representation.records}
    assert {r.target_record_key for r in named} <= records
    row_refs = [t for *_, refs_ in GEN.NAMED_ROWS for _, t in refs_]
    assert len(named) == len(row_refs) + sum(
        1
        for refs_ in GEN.EXPLICIT_REFS.values()
        for _, t in refs_
        if isinstance(t, tuple) and t[0] == EQUIPMENT
    )
    assert len(row_refs) == 53
    by = {
        (
            r.from_record_key.removeprefix("equipment."),
            r.from_component_key,
            r.source_text,
        ): (r.target_record_key.removeprefix("equipment."))
        for r in named
    }
    assert by[("tools", "craft", "Crafting Nonmagical Items")] == (
        "crafting_nonmagical_items"
    )
    assert by[("mounts_and_vehicles", "crew", "Hirelings")] == "hirelings"
    assert by[("mounts_and_vehicles", "barding", "Armor table")] == "armor"
    assert by[("crafting_nonmagical_items", "tools", "Tools")] == "tools"
    # A pointer naming an item or rule this batch authors names that record.
    assert by[("adventuring_gear", "ammunition", "Ammunition property")] == (
        "weapons.ammunition"
    )
    assert by[("tools", "smiths_tools", "Medium armor")] == "armor.category"
    assert by[("tools", "smiths_tools", "Melee weapon")] == "weapons.melee_or_ranged"
    assert by[("adventuring_gear", "lock", "Thieves' Tools")] == "tools.thieves_tools"
    assert by[("adventuring_gear.arcane_focus", "arcane_focus", "Quarterstaff")] == (
        "weapons.quarterstaff"
    )
    # Items named inside Equipment are cited items too.
    assert by[("tools", "carpenters_tools", "Club")] == "weapons.club"
    assert by[("tools", "woodcarvers_tools", "Club")] == "weapons.club"
    assert by[("adventuring_gear.holy_symbol", "holy_symbol", "Shield")] == (
        "armor.shield"
    )
    assert by[("tools", "tinkers_tools", "Musket")] == "weapons.musket"
    assert by[("tools", "weavers_tools", "Padded Armor")] == "armor.padded_armor"
    assert by[("adventuring_gear", "spikes_iron", "Light Hammer")] == (
        "weapons.light_hammer"
    )
    assert by[("weapons.sling", "sling", "Bullet")] == "adventuring_gear.bullets_sling"
    assert by[("weapons.musket", "musket", "Bullet")] == (
        "adventuring_gear.bullets_firearm"
    )
    assert by[("armor.padded_armor", "padded_armor", "Disadvantage")] == (
        "armor.stealth"
    )
    assert by[("weapons.shortbow", "shortbow", "Arrow")] == "adventuring_gear.arrows"
    assert by[("weapons.spear", "spear", "Sap")] == "weapons.sap"
    # "Simple Melee weapon" names both halves of a weapon's classification:
    # *Category* defines Simple, *Melee or Ranged* defines Melee (printed 89).
    assert by[("adventuring_gear", "torch", "Simple")] == "weapons.category"
    assert by[("adventuring_gear", "torch", "Melee")] == "weapons.melee_or_ranged"
    assert by[
        (
            "brewing_potions_of_healing",
            "brewing_potions_of_healing",
            "Potion of Healing",
        )
    ] == ("adventuring_gear.potion_of_healing")
    # A pointer names a whole section only when it cites the section itself.
    assert {t for t in by.values() if "." not in t} == {
        "armor",
        "brewing_potions_of_healing",
        "crafting_nonmagical_items",
        "hirelings",
        "lifestyle_expenses",
        "scribing_spell_scrolls",
        "tools",
    }
    # No self-pointer: a record's own item is not a reference.
    assert not [r for r in named if r.from_record_key == r.target_record_key]


def test_unauthored_parts_stay_explicit_unresolved_references(built) -> None:  # type: ignore[no-untyped-def]
    assert GEN.unresolved() == [
        ("srd-5.2.1/classes", "Cleric or Paladin"),
        ("srd-5.2.1/classes", "Druid or Ranger"),
        ("srd-5.2.1/classes", "Sorcerer, Warlock, or Wizard"),
        ("srd-5.2.1/gameplay-toolbox", "Gameplay Toolbox"),
        ("srd-5.2.1/gameplay-toolbox", "Gameplay Toolbox"),
        ("srd-5.2.1/magic-items", "Magic Items"),
        ("srd-5.2.1/magic-items", "Magic Items"),
        ("srd-5.2.1/monsters", "Monsters"),
        ("srd-5.2.1/spells", "Identify"),
    ]
    # No stub record is authored for any of them.
    kinds = {r.semantic_key for r in built.proposal.proposed_representation.records}
    assert all(k.startswith("equipment.") for k in kinds)


def test_accepted_glossary_terms_are_cited_from_prose_only(built) -> None:  # type: ignore[no-untyped-def]
    cited = {
        r.target_record_key.removeprefix("glossary.")
        for r in built.proposal.proposed_representation.references
        if r.scope_key == GLOSSARY
    }
    assert cited == GLOSSARY_TARGETS | {"improvised_weapons"}
    # Examples and unaccepted terms are not references.
    texts = {r.source_text for r in built.proposal.proposed_representation.references}
    for example in (
        "Weapon Mastery",
        "Ring of Swimming",
        "Plate Armor",
        "Advantage",
        "Bonus Action",
        "Spellcasting Focus",
    ):
        assert example not in texts


def test_each_named_record_is_a_catalogue_member_of_its_section(built) -> None:  # type: ignore[no-untyped-def]
    # Owner Decision 2026-09-24: the section reaches the record where it is
    # printed. Only the cited records are members; the uncited entries stay
    # the section's own components.
    rels = built.proposal.proposed_representation.relationships
    assert {r.kind for r in rels} == {RelationshipKind.CATALOGUE_MEMBER}
    assert sorted((r.source_record_key, r.target_record_key) for r in rels) == sorted(
        (k, f"equipment.{e}") for k, _, e in GEN.batch().records
    )
    assert "scoped_within" not in PROPOSAL.read_text("utf-8")


# ---------------------------------------------------------------------------
# Coverage and omission
# ---------------------------------------------------------------------------


def test_only_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    excluded = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert all(e.startswith("#") and "\n" not in e for e in excluded)
    assert len(excluded) == 14 + sum(len(h) for _, h, _ in GEN.EXCLUDED) == 45
    # No excluded heading states a price, a number or a unit.
    assert not [e for e in excluded if any(ch.isdigit() for ch in e)]
    assert not [e for e in excluded if " GP" in e or " SP" in e or " CP" in e]


def _residue(built) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Text of a spanned leaf no span covers, blockquote markers aside."""
    out = {}
    for lid in {s.leaf_id for s in built.ledger.spans}:
        text = list(built.leaf_rows[lid].content)
        for s in built.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if left := "".join(text).replace(">", "").strip():
            out[lid] = left
    return out


def test_every_spanned_leaf_is_claimed_to_the_last_word(built) -> None:  # type: ignore[no-untyped-def]
    assert _residue(built) == {}


def _drop_text(monkeypatch, entry: str, *old: str) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if not (e == entry and t in old)))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )
    # The references the dropped text printed go with it.
    kept = {(e, k): "\n".join(ts) for e, k, _, ts in GEN.CLAUSES}
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            dataclasses.replace(
                c,
                texts=tuple(t for t in c.texts if not (c.entry == entry and t in old)),
                context=tuple(
                    t for t in c.context if not (c.entry == entry and t in old)
                ),
                refs=tuple(
                    r
                    for r in c.refs
                    if r[0] in ("\n".join(c.texts) or kept[(c.entry, c.key)])
                ),
            )
            for c in GEN.COMPONENTS
        ),
    )


def _unnamed_pieces(name: str) -> tuple[str, ...]:
    """A table's text, less any piece a named record reads."""
    table = getattr(GEN, name)
    if name not in SPLIT:
        return (table,)
    read = {t for c in GEN.COMPONENTS if c.record for t in c.texts}
    return tuple(p for p in getattr(GEN, SPLIT[name]) if p not in read)


@pytest.mark.parametrize(
    ("entry", "text"),
    [
        ("weapons", "WEAPONS_TABLE"),
        ("armor", "ARMOR_TABLE"),
        ("adventuring_gear", "ADVENTURING_GEAR_TABLE"),
        ("food_drink_and_lodging", "FOOD_DRINK_AND_LODGING_TABLE"),
        ("scribing_spell_scrolls", "SPELL_SCROLL_COSTS_TABLE"),
        ("adventuring_gear", "#### Potion of Healing (50 GP)"),
        ("tools", "**Calligrapher's Supplies (10 GP)**"),
        ("lifestyle_expenses", "### Aristocratic (10 GP per Day)"),
    ],
)
def test_a_dropped_table_or_priced_heading_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, entry, text
) -> None:
    if text in SPLIT:
        # Part of a reviewed leaf left unspanned is admitted by the batch
        # checks (Owner Decision 2026-09-16, ADR-005d Decision 2): the residue
        # check is what reports the rows no named record reads.
        _drop_text(monkeypatch, entry, *_unnamed_pieces(text))
        built = GEN.build(session)
        assert GEN.batch_findings(built)["review_units"] == []
        (left,) = _residue(built).values()
        assert left.startswith("<tr")
        return
    _drop_text(monkeypatch, entry, getattr(GEN, text, text))
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(f"review unit equipment/{entry}: leaf ")


@pytest.mark.parametrize(
    ("table", "row"),
    [
        ("WEAPONS_TABLE", "\n      <td>Hand Crossbow</td>"),
        ("ARMOR_TABLE", "\n      <td>Chain Mail</td>"),
        ("ADVENTURING_GEAR_TABLE", "\n      <td>Lamp</td>"),
        ("VEHICLES_TABLE", "\n      <td>Airship</td>"),
        ("SPELL_SCROLL_COSTS_TABLE", "\n      <td>Cantrip</td>"),
    ],
)
def test_a_table_missing_a_row_is_a_loud_locate_failure(  # type: ignore[no-untyped-def]
    session, monkeypatch, table, row
) -> None:
    # The row is cut from the text the clause actually reads: the whole table,
    # or the piece of a split table that prints it.
    (text,) = [t for t in (*_unnamed_pieces(table), getattr(GEN, table)) if row in t][
        :1
    ]
    # The row's own opening tag ends where *row* begins.
    start = text.rindex("    <tr>\n", 0, text.index(row) + 1)
    end = text.index("</tr>\n", start) + len("</tr>\n")
    shorter = text[:start] + text[end:]
    assert shorter.count("<tr>") == text.count("<tr>") - 1
    assert shorter not in getattr(GEN, table)  # a gap, not a shorter piece
    clauses = tuple(
        (e, k, f, tuple(shorter if t == text else t for t in ts))
        for e, k, f, ts in GEN.CLAUSES
    )
    assert clauses != GEN.CLAUSES
    monkeypatch.setattr(GEN, "CLAUSES", clauses)
    # A component naming the pieces it reads reads the shorter one too.
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            dataclasses.replace(
                c, texts=tuple(shorter if t == text else t for t in c.texts)
            )
            for c in GEN.COMPONENTS
        ),
    )
    with pytest.raises(ValueError, match="occurs 0 times"):
        GEN.build(session)


@pytest.mark.parametrize(
    ("entry", "key"),
    [
        ("magic_items", "no_more_than_three_items"),
        ("weapons", "heavy"),
        ("scribing_spell_scrolls", "prerequisites_for_the_scribe"),
        ("mounts_and_vehicles", "ship_repair"),
    ],
)
def test_a_dropped_constraint_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, entry, key
) -> None:
    monkeypatch.setattr(
        GEN, "CLAUSES", tuple(c for c in GEN.CLAUSES if (c[0], c[1]) != (entry, key))
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(c for c in GEN.COMPONENTS if (c.entry, c.key) != (entry, key)),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(f"review unit equipment/{entry}: leaf ")


def test_a_dropped_named_clause_fails_loudly(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A named record left with no reviewed span cannot be proposed.
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(c for c in GEN.CLAUSES if (c[0], c[1]) != ("weapons", "two_handed")),
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            c for c in GEN.COMPONENTS if (c.entry, c.key) != ("weapons", "two_handed")
        ),
    )
    with pytest.raises(ValueError, match="weapons.two_handed owns no reviewed span"):
        GEN.build(session)


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(c for c in GEN.COMPONENTS if (c.entry, c.key) != ("armor", "strength")),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit equipment/armor: expected rule equipment.armor/strength "
        "has no component"
    ) in found


# ---------------------------------------------------------------------------
# Test-only composition with the twelve-batch acceptance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _composed(prior: AcceptedInputs, recorded: MechanicalProposal) -> AcceptedInputs:
    oracle, accepted = prior.oracle, prior.oracle.representation
    proposed = recorded.proposed_representation
    return dataclasses.replace(
        prior,
        oracle=dataclasses.replace(
            oracle,
            spans=(*oracle.spans, *(p.span for p in recorded.proposed_spans)),
            review_units=(*oracle.review_units, *recorded.proposed_review_units),
            representation=dataclasses.replace(
                accepted,
                **{
                    f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
                    for f in dataclasses.fields(accepted)
                },
            ),
        ),
    )


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _acceptance(inputs: AcceptedInputs) -> list[str]:
    # Native acceptance evidence (#137 contract 2) reads only the
    # classification ledger: no corpus either.
    return sorted(
        validate_acceptance(candidate_from_accepted_inputs(inputs).classification)
    )


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(inputs).representation
    )


def test_composed_every_glossary_target_closes_and_375_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    # The replayed chain keeps the schema it was accepted under; it is
    # judged, and composed, at the build's.
    prior = lifted(prior)
    assert prior.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert len(prior.oracle.representation.records) == 136
    assert len(prior.oracle.spans) == 1016
    assert len(prior.batches) == 12
    assert [r.resolution_id for r in prior.oracle.reference_resolutions] == (
        PRIOR_RESOLUTIONS
    )
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert len(recorded.proposed_spans) == 409
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }
    composed = _composed(prior, recorded)

    # The 91 retained findings stay, the 45 Equipment citations among them.
    rest_before = sorted(_references(prior))
    assert len(rest_before) == 91
    assert len([f for f in rest_before if f"reference {EQUIPMENT}:" in f]) == 45
    added = sorted(
        f
        for f in GEN.expected_representation_findings()
        if "unresolved reference" in f or "glossary.improvised_weapons" in f
    )
    # Unfiltered and representation-only: nothing else is reported.
    assert sorted(_references(composed)) == sorted(rest_before + added)
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(prior) == []
    assert _acceptance(composed) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(composed) - _covered(prior) == mine
    assert len(mine) == 375
    # The accepted part of the composition is the accepted bytes, unchanged.
    head = dataclasses.replace(
        composed,
        oracle=dataclasses.replace(
            composed.oracle,
            spans=composed.oracle.spans[:1016],
            review_units=composed.oracle.review_units[: len(prior.oracle.review_units)],
            representation=dataclasses.replace(
                composed.oracle.representation,
                **{
                    f.name: getattr(composed.oracle.representation, f.name)[
                        : len(getattr(accepted, f.name))
                    ]
                    for f in dataclasses.fields(accepted)
                },
            ),
        ),
    )
    assert head == prior


def test_the_recorded_resolutions_still_apply_composed(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    composed = _composed(prior, recorded)
    assert (
        reference_resolution_violations(
            composed.oracle.representation,
            prior.oracle.reference_resolutions,
            prior.oracle.binding,
        )
        == []
    )


# ---------------------------------------------------------------------------
# The forty-three "Equipment" resolution drafts, unrecorded
# ---------------------------------------------------------------------------


def _key(r: ReferenceDraft | ReferenceResolution) -> tuple[str, str, str, str]:
    return (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)


def test_each_draft_names_an_accepted_citation_exactly(prior) -> None:  # type: ignore[no-untyped-def]
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    assert len(drafts) == 43
    assert len({d.resolution_id for d in drafts}) == 43
    assert not {d.resolution_id for d in drafts} & set(PRIOR_RESOLUTIONS)
    accepted = prior.oracle.representation
    for draft in drafts:
        (ref,) = [r for r in accepted.references if _key(r) == _key(draft)]
        assert ref.target_record_key == ""
        cited = sorted(
            {
                c.span_id
                for c in accepted.provenance
                if c.target_kind is ProvenanceTargetKind.REFERENCE
                and c.target_key == reference_target_key(ref)
            }
        )
        assert tuple(cited) == draft.provenance_span_ids, draft.resolution_id


def test_every_accepted_equipment_citation_is_drafted_or_left_whole_part(prior) -> None:  # type: ignore[no-untyped-def]
    cited = sorted(
        _key(r)
        for r in prior.oracle.representation.references
        if r.scope_key == EQUIPMENT
    )
    drafted = [_key(d) for d in GEN.draft_resolutions(prior.oracle.binding)]
    left = [(*c, EQUIPMENT) for c in GEN.UNRESOLVED_CITATIONS]
    assert len(cited) == 45
    assert sorted(drafted + left) == cited


def test_the_drafts_cannot_apply_to_the_accepted_authority_as_it_stands(prior) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(AcceptanceError, match="states no record for"):
        resolve_references(
            prior,
            resolutions=GEN.draft_resolutions(prior.oracle.binding),
            authorized_by="test",
            authorization_reference="test",
            reviewer="test",
            resolved_at="2026-09-23T00:00:00Z",
        )


def test_once_accepted_all_drafts_resolve_through_the_native_seam(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # In memory only: nothing is written and no decision is recorded. The
    # recorded proposal over its recorded prior: both the superseded release's.
    oracle = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracle.glob("*.json")}
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="equipment",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-23T00:00:00Z",
        prior=prior,
    )
    assert [lift.lift_id for lift in accepted.lifts] == [
        lift.lift_id for lift in prior.lifts
    ]
    binding = prior.oracle.binding
    drafts = GEN.draft_resolutions(binding)
    resolved = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test",
        reviewer="test",
        resolved_at="2026-09-23T00:00:00Z",
    )
    assert [r.resolution_id for r in resolved.oracle.reference_resolutions] == [
        *PRIOR_RESOLUTIONS,
        *(d.resolution_id for d in drafts),
    ]
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    outside = [
        r
        for r in effective.references
        if r.scope_key == EQUIPMENT and not r.from_record_key.startswith("equipment.")
    ]
    assert sorted(
        (r.from_record_key, r.from_component_key, r.source_text)
        for r in outside
        if r.target_record_key == ""
    ) == sorted(GEN.UNRESOLVED_CITATIONS)
    assert {
        (r.from_record_key, r.source_text, r.target_record_key)
        for r in outside
        if r.from_component_key == "equipment" and r.target_record_key
    } >= {
        ("character_origins.criminal", "Daggers", "equipment.weapons.dagger"),
        (
            "character_origins.criminal",
            "Thieves' Tools",
            "equipment.tools.thieves_tools",
        ),
        (
            "character_origins.soldier",
            "Healer's Kit",
            "equipment.adventuring_gear.healers_kit",
        ),
    }
    # The accepted citations themselves are not edited, and nothing is written.
    assert resolved.oracle.representation == accepted.oracle.representation
    assert {p.name: p.read_bytes() for p in oracle.glob("*.json")} == on_disk


#: The defect this pins: a citation naming an item or rule targeted the whole
#: section that merely contains it. Each draft's target, and for a named one
#: the printed text its record owns (PRIMARY) that makes it that item or rule.
S = "equipment."
DRAFT_TARGETS = {
    ("play.d20_tests", "", "Equipment"): (S + "weapons", None),
    ("play.damage_and_healing", "", "Equipment"): (S + "weapons", None),
    ("feats.archery", "archery", "Ranged weapons"): (
        S + "weapons.melee_or_ranged",
        "Melee or Ranged",
    ),
    ("character_creation.create_your_character", "armor_class", "Equipment"): (
        S + "armor",
        None,
    ),
    ("character_creation.create_your_character", "armor_training", "Equipment"): (
        S + "armor",
        None,
    ),
    ("character_creation.create_your_character", "attacks", "Equipment"): (
        S + "weapons",
        None,
    ),
    ("feats.defense", "defense", "Light, Medium, or Heavy armor"): (
        S + "armor.category",
        "Category",
    ),
    **{
        (f"character_origins.{bg}", "equipment", text): (S + target, needle)
        for bg, text, target, needle in (
            (
                "acolyte",
                "Calligrapher's Supplies",
                "tools.calligraphers_supplies",
                "Calligrapher's Supplies",
            ),
            ("acolyte", "Book", "adventuring_gear.book", "<td>Book</td>"),
            (
                "acolyte",
                "Holy Symbol",
                "adventuring_gear.holy_symbol",
                "<td>Holy Symbol</td>",
            ),
            (
                "acolyte",
                "Parchment",
                "adventuring_gear.parchment",
                "<td>Parchment</td>",
            ),
            ("acolyte", "Robe", "adventuring_gear.robe", "<td>Robe</td>"),
            ("criminal", "Daggers", "weapons.dagger", "<td>Dagger</td>"),
            ("criminal", "Thieves' Tools", "tools.thieves_tools", "Thieves' Tools"),
            ("criminal", "Crowbar", "adventuring_gear.crowbar", "<td>Crowbar</td>"),
            ("criminal", "Pouches", "adventuring_gear.pouch", "<td>Pouch</td>"),
            (
                "criminal",
                "Traveler's Clothes",
                "adventuring_gear.clothes_travelers",
                "<td>Clothes, Traveler's</td>",
            ),
            ("sage", "Quarterstaff", "weapons.quarterstaff", "<td>Quarterstaff</td>"),
            (
                "sage",
                "Calligrapher's Supplies",
                "tools.calligraphers_supplies",
                "Calligrapher's Supplies",
            ),
            ("sage", "Book", "adventuring_gear.book", "<td>Book</td>"),
            ("sage", "Parchment", "adventuring_gear.parchment", "<td>Parchment</td>"),
            ("sage", "Robe", "adventuring_gear.robe", "<td>Robe</td>"),
            ("soldier", "Spear", "weapons.spear", "<td>Spear</td>"),
            ("soldier", "Shortbow", "weapons.shortbow", "<td>Shortbow</td>"),
            ("soldier", "Arrows", "adventuring_gear.arrows", "<td>Arrows</td>"),
            ("soldier", "Gaming Set", "tools.gaming_set", "Gaming Set"),
            (
                "soldier",
                "Healer's Kit",
                "adventuring_gear.healers_kit",
                "<td>Healer's Kit</td>",
            ),
            ("soldier", "Quiver", "adventuring_gear.quiver", "<td>Quiver</td>"),
            (
                "soldier",
                "Traveler's Clothes",
                "adventuring_gear.clothes_travelers",
                "<td>Clothes, Traveler's</td>",
            ),
        )
    },
    **{
        ("feats.great_weapon_fighting", "great_weapon_fighting", text): (
            S + target,
            needle,
        )
        for text, target, needle in (
            ("Melee weapon", "weapons.melee_or_ranged", "Melee or Ranged"),
            ("Two-Handed", "weapons.two_handed", "Two-Handed"),
            ("Versatile", "weapons.versatile", "Versatile"),
        )
    },
    (
        "character_creation.starting_at_higher_levels",
        "starting_equipment",
        "Equipment",
    ): (S + "weapons", None),
    **{
        (f"character_origins.{bg}", "tool_proficiency", text): (S + target, needle)
        for bg, text, target, needle in (
            (
                "acolyte",
                "Calligrapher's Supplies",
                "tools.calligraphers_supplies",
                "Calligrapher's Supplies",
            ),
            (
                "backgrounds",
                "Artisan's Tools",
                "tools.artisans_tools",
                "Artisan's Tools",
            ),
            ("backgrounds", "Equipment", "tools", None),
            ("criminal", "Thieves' Tools", "tools.thieves_tools", "Thieves' Tools"),
            (
                "sage",
                "Calligrapher's Supplies",
                "tools.calligraphers_supplies",
                "Calligrapher's Supplies",
            ),
            ("soldier", "Gaming Set", "tools.gaming_set", "Gaming Set"),
            ("soldier", "Equipment", "tools", None),
        )
    },
    ("play.exploration", "travel_pace", "Equipment"): (
        S + "mounts_and_vehicles",
        None,
    ),
    ("feats.two_weapon_fighting", "two_weapon_fighting", "Light property"): (
        S + "weapons.light",
        "Light",
    ),
    ("play.exploration", "vehicles", "Equipment"): (S + "mounts_and_vehicles", None),
}


def test_a_citation_naming_an_item_or_rule_targets_that_record(built, prior) -> None:  # type: ignore[no-untyped-def]
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    assert {
        (d.from_record_key, d.from_component_key, d.source_text): d.target_record_key
        for d in drafts
    } == {k: t for k, (t, _) in DRAFT_TARGETS.items()}
    representation = built.proposal.proposed_representation
    sections = {f"equipment.{s}" for s, _ in UNITS}
    spans = {s.span_id: s for s in built.ledger.spans}
    bindings = {prose_binding_target_key(b): b for b in representation.prose_bindings}
    owned: dict[str, list[str]] = {}
    for c in representation.provenance:
        if (
            c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and c.role is ProvenanceRole.PRIMARY
        ):
            s = spans[c.span_id]
            owned.setdefault(bindings[c.target_key].record_key, []).append(
                built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]
            )
    for target, needle in DRAFT_TARGETS.values():
        if needle is None:
            # A citation printing only "Equipment" names its section.
            assert target in sections
            continue
        # Its own record, not the section merely containing it ...
        assert target not in sections and target.rsplit(".", 1)[0] in sections
        # ... owning the printed item or rule, and not the whole section.
        assert any(needle in text for text in owned[target]), target
        assert len(owned[target]) < len(owned[target.rsplit(".", 1)[0]]), target


SPEAR = ("equipment.weapons.spear", "spear")


@pytest.mark.parametrize(
    ("target", "change", "message"),
    [
        (SPEAR, {"record": "equipment.weapons.undeclared"}, "is not a declared record"),
        # Membership is the declared section's, never another's.
        (
            SPEAR,
            {"record": "equipment.armor.shield"},
            "equipment.armor.shield is not a declared record of weapons",
        ),
        (SPEAR, {"texts": ("not a reviewed text",)}, "reads unreviewed"),
        # A row of another section is not located in this one's source.
        (SPEAR, {"texts": (GEN.ARMOR_ROWS["Shield"],)}, "reads unreviewed"),
        (SPEAR, {"context": ("not a reviewed text",)}, "has context it does not read"),
        (
            SPEAR,
            {"handling": ComponentHandling.STRUCTURED},
            "must keep its governing prose",
        ),
        # The section may not reread what a member owns: here its table
        # component reads the whole table again, named rows included.
        (
            (None, "weapons_table"),
            {"texts": ()},
            r"section weapons rereads .* owned by equipment\.weapons\.",
        ),
    ],
)
def test_a_named_component_outside_its_declaration_fails_loudly(  # type: ignore[no-untyped-def]
    session, monkeypatch, target, change, message
) -> None:
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            (dataclasses.replace(c, **change) if (c.record, c.key) == target else c)
            for c in GEN.COMPONENTS
        ),
    )
    with pytest.raises(ValueError, match=message):
        GEN.build(session)


# ---------------------------------------------------------------------------
# Membership through the production service (Owner Decision 2026-09-24)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built):  # type: ignore[no-untyped-def]
    """The proposal persisted as a draft into a private copy of the release."""
    path = tmp_path_factory.mktemp("equipment-membership") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(_candidate(built))
        persist_draft(s, identified, now="2026-09-24T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _read(service, built, *records: str, components=()):  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records, components=components))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return view.gamemaster_view.components


def _primary(built) -> dict[tuple[str, str, str], tuple[int, int]]:  # type: ignore[no-untyped-def]
    """Each span a component owns (not reads as context), at its printed position."""
    spans = {s.span_id: s for s in built.ledger.spans}
    rep = built.proposal.proposed_representation
    bindings = {prose_binding_target_key(b): b for b in rep.prose_bindings}
    out = {}
    for c in rep.provenance:
        if (
            c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and c.role is ProvenanceRole.PRIMARY
        ):
            b = bindings[c.target_key]
            span = spans[c.span_id]
            out[(b.record_key, b.component_key, c.span_id)] = (
                built.leaf_rows[span.leaf_id].occurrence_index,
                span.char_start,
            )
    return out


SECTIONS_WITH_MEMBERS = sorted({f"equipment.{e}" for _, _, e in GEN.batch().records})


@pytest.mark.parametrize("section", SECTIONS_WITH_MEMBERS)
def test_a_section_reads_its_members_where_they_are_printed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, section
) -> None:
    service = _service(persisted, built, monkeypatch)
    members = sorted(
        (min(p for p in _owned(built, k)), k)
        for k, _, e in GEN.batch().records
        if f"equipment.{e}" == section
    )
    assert _sliced(service, _request(built, section)) == [
        section,
        *(k for _, k in members),
    ]
    records = {section, *(k for _, k in members)}
    # The complete passage sequence: every passage the section and its members
    # own, each once, in printed order -- nothing moved to where another part
    # of its record is printed, and no member's table head read again.
    assert _sequence(built, _read(service, built, section)) == sorted(
        position
        for (record, _, _), position in _primary(built).items()
        if record in records
    )


def _sequence(built, view) -> list[tuple[int, int]]:  # type: ignore[no-untyped-def]
    """The printed position of each passage *view* reads, in reading order."""
    primary = _primary(built)
    read = [
        (c.record_key, c.component_key, e.span_id)
        for c in view
        for e in c.governing_prose
        if isinstance(e, SourceProse)
    ]
    assert all(r in primary for r in read), "a passage read as context"
    return [primary[r] for r in read]


def _owned(built, record: str) -> list[tuple[int, int]]:  # type: ignore[no-untyped-def]
    spans = {s.span_id: s for s in built.ledger.spans}
    bindings = {
        prose_binding_target_key(b): b
        for b in built.proposal.proposed_representation.prose_bindings
    }
    return [
        (
            built.leaf_rows[spans[c.span_id].leaf_id].occurrence_index,
            spans[c.span_id].char_start,
        )
        for c in built.proposal.proposed_representation.provenance
        if c.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and c.role is ProvenanceRole.PRIMARY
        and bindings[c.target_key].record_key == record
    ]


def test_the_weapons_table_reads_its_rows_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    rows = [
        (c.record_key, name)
        for c in _read(service, built, "equipment.weapons")
        for e in c.governing_prose
        if isinstance(e, SourceProse)
        for name in re.findall(r"<tr>\s*<td>([^<]+)</td>", e.text or "")
    ]
    simple_melee = [name for _, name in rows][:10]
    assert simple_melee == [
        "Club",
        "Dagger",
        "Greatclub",
        "Handaxe",
        "Javelin",
        "Light Hammer",
        "Mace",
        "Quarterstaff",
        "Sickle",
        "Spear",
    ]
    assert rows[0] == ("equipment.weapons.club", "Club")
    assert rows[2] == ("equipment.weapons", "Greatclub")
    assert rows[9] == ("equipment.weapons.spear", "Spear")


def test_direct_section_and_combined_selections_read_a_member_once(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    spear = "equipment.weapons.spear"
    # Directly: the row under the rules governing it, the table head and its
    # group row, once.
    (direct,) = _read(service, built, spear)
    texts = [e.text for e in direct.governing_prose]
    assert texts == [
        *GEN.clause("weapons", "mastery"),
        *GEN.clause("weapons", "weapon_proficiency"),
        GEN.WEAPONS_HEAD,
        GEN.WEAPON_GROUPS["Simple Melee Weapons"],
        GEN.WEAPON_ROWS["Spear"],
    ]
    section = _read(service, built, "equipment.weapons")
    for records in (
        ("equipment.weapons", spear),
        (spear, "equipment.weapons"),
    ):
        both = _read(service, built, *records)
        assert both == section
        assert [c.record_key for c in both].count(spear) == 1
    assert _sliced(service, _request(built, "equipment.weapons", spear)) == _sliced(
        service, _request(built, "equipment.weapons")
    )


def test_a_component_selector_on_a_section_reads_no_member(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    armor = [k for k, _, e in GEN.batch().records if e == "armor"]
    narrowed = _read(service, built, components=(("equipment.armor", "strength"),))
    assert [(c.record_key, c.component_key) for c in narrowed] == [
        ("equipment.armor", "strength")
    ]
    # Naming every member as well reads each once, and still only the one
    # component of the section.
    both = _read(service, built, *armor, components=(("equipment.armor", "strength"),))
    assert sorted({c.record_key for c in both}) == sorted(["equipment.armor", *armor])
    assert [c.component_key for c in both if c.record_key == "equipment.armor"] == [
        "strength"
    ]
    # Shield reads in two runs, its row and its later rule; no passage twice.
    read = [(c.record_key, e.span_id) for c in both for e in c.governing_prose]
    assert len(read) == len(set(read))


def test_a_disabled_member_is_not_brought_back_by_its_section(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    spear = "equipment.weapons.spear"
    service = _service(persisted, built, monkeypatch, _disable(spear))
    assert spear not in _sliced(service, _request(built, "equipment.weapons"))
    section = _read(service, built, "equipment.weapons")
    assert spear not in {c.record_key for c in section}
    assert GEN.WEAPON_ROWS["Spear"] not in {
        e.text for c in section for e in c.governing_prose
    }
    # The rows around it are still read.
    assert GEN.WEAPON_ROWS["Club"] in {
        e.text for c in section for e in c.governing_prose
    }
    direct = service.rule_slice(_request(built, spear))
    assert direct.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_a_replaced_member_reads_replaced_where_it_is_printed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    spear = "equipment.weapons.spear"
    replaced = EffectiveOverrideEntry(
        override_id="replace-spear",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=spear,
            component_key="spear",
        ),
        operation=OverrideOperationEnum.REPLACE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "A house spear.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, replaced)
    section = _read(service, built, "equipment.weapons")
    at = [c.record_key for c in section].index(spear)
    (entry,) = section[at].governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "A house spear."
    assert GEN.WEAPON_ROWS["Spear"] not in {
        e.text for c in section for e in c.governing_prose
    }
    # Between the Sickle row the section reads and the Simple Ranged group row.
    before, after = section[at - 1], section[at + 1]
    assert (
        before.governing_prose[-1]
        .text.lstrip()
        .startswith("<tr>\n      <td>Sickle</td>")
    )
    assert after.governing_prose[0].text == GEN.WEAPON_GROUPS["Simple Ranged Weapons"]


GEAR = "equipment.adventuring_gear"


def _replaced(record: str, key: str, text: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"replace-{record}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT, record_key=record, component_key=key
        ),
        operation=OverrideOperationEnum.REPLACE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": text,
            },
        },
    )


def _runs(view, record: str) -> list[int]:  # type: ignore[no-untyped-def]
    return [i for i, c in enumerate(view) if c.record_key == record]


def test_a_gear_item_reads_its_row_and_description_each_where_printed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    section = _read(service, built, GEAR)
    texts = [e.text for c in section for e in c.governing_prose]
    # The table head and each item row are read once, the head by the section.
    assert texts.count(GEN.GEAR_HEAD) == 1
    head = next(
        c for c in section if GEN.GEAR_HEAD in {e.text for e in c.governing_prose}
    )
    assert head.record_key == GEAR
    # Antitoxin's row reads inside the table; its description after the
    # Ammunition table, where it is printed -- two runs of one record.
    row, description = _runs(section, f"{GEAR}.antitoxin")
    assert [e.text for e in section[row].governing_prose] == list(
        GEN.GEAR_ROWS["antitoxin"]
    )
    assert (section[row - 1].record_key, section[row - 1].component_key) == (
        GEAR,
        "adventuring_gear_table",
    )
    assert section[row + 1].record_key == f"{GEAR}.arcane_focus"
    assert (
        section[description - 1].record_key,
        section[description - 1].component_key,
    ) == (
        GEAR,
        "ammunition",
    )
    assert section[description + 1].record_key == f"{GEAR}.arcane_focus"
    assert len(section[description].governing_prose) == 2
    # Acid is its mirror: the description is printed before the table.
    description, row = _runs(section, f"{GEAR}.acid")
    assert [e.text for e in section[row].governing_prose] == list(GEN.GEAR_ROWS["acid"])
    assert section[row - 1].governing_prose[0].text == GEN.GEAR_HEAD
    assert row - description > 1
    # Read directly, the item keeps the head its row is read under.
    (direct,) = _read(service, built, f"{GEAR}.antitoxin")
    assert [e.text for e in direct.governing_prose] == [
        GEN.GEAR_HEAD,
        *GEN.GEAR_ROWS["antitoxin"],
        *(
            e.text
            for e in section[_runs(section, f"{GEAR}.antitoxin")[1]].governing_prose
        ),
    ]
    # Named with its section, it is the section's reading, once.
    assert _read(service, built, GEAR, f"{GEAR}.antitoxin") == section


def test_a_disabled_or_replaced_gear_item_leaves_the_sequence_whole(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    item = f"{GEAR}.antitoxin"
    whole = _read(_service(persisted, built, monkeypatch), built, GEAR)
    row, description = _runs(whole, item)
    printed = {e.text for i in (row, description) for e in whole[i].governing_prose}
    disabled = _read(
        _service(persisted, built, monkeypatch, _disable(item)), built, GEAR
    )
    assert item not in {c.record_key for c in disabled}
    assert not printed & {e.text for c in disabled for e in c.governing_prose}
    assert _sequence(built, disabled) == [
        p for p in _sequence(built, whole) if p not in set(_owned(built, item))
    ]
    replaced = _read(
        _service(
            persisted,
            built,
            monkeypatch,
            _replaced(item, "antitoxin", "House antitoxin."),
        ),
        built,
        GEAR,
    )
    # One authored passage, read where the item is first printed: its row.
    (at,) = _runs(replaced, item)
    (entry,) = replaced[at].governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "House antitoxin."
    assert replaced[at - 1] == whole[row - 1]
    assert replaced[at + 1] == whole[row + 1]
    assert not printed & {e.text for c in replaced for e in c.governing_prose}
    assert _sequence(built, replaced) == _sequence(built, disabled)


def test_a_suppressed_row_is_not_read_again_as_another_row_s_context(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    # Authoring admits a row read as another row's context; the Club row stays
    # Club's authority, read once, and gone wherever Club is suppressed.
    club, spear = "equipment.weapons.club", "equipment.weapons.spear"
    context = (
        GEN.WEAPONS_HEAD,
        GEN.WEAPON_GROUPS["Simple Melee Weapons"],
        GEN.WEAPON_ROWS["Club"],
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            (
                dataclasses.replace(
                    c, texts=(*context, GEN.WEAPON_ROWS["Spear"]), context=context
                )
                if (c.record, c.key) == SPEAR
                else c
            )
            for c in GEN.COMPONENTS
        ),
    )
    built = GEN.build(session)

    def reads(authority: EffectiveAuthority, record: str) -> list[str | None]:
        (found,) = (r for r in authority.records if r.semantic_key == record)
        return [
            e.text if isinstance(e, AuthoredProse) else e.span_id
            for c in found.components
            for e in c.governing_prose
        ]

    row = next(
        s.span_id
        for s in built.ledger.spans
        if built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]
        == GEN.WEAPON_ROWS["Club"]
    )
    assert row in reads(_authority(session, built), spear)
    view = _gamemaster(session, built)
    assert [
        c.record_key
        for c in view
        for e in c.governing_prose
        if isinstance(e, SourceProse) and e.span_id == row
    ] == [club]
    for entry in (_disable(club), _replaced(club, "club", "A house club.")):
        authority = _authority(session, built, entry)
        assert row not in reads(authority, spear)
        overridden = build_gamemaster_view(authority, _prose(session, built))
        assert row not in {
            e.span_id
            for c in overridden.components
            for e in c.governing_prose
            if isinstance(e, SourceProse)
        }


def _direct(service, built, record: str) -> list[str | None]:  # type: ignore[no-untyped-def]
    return [e.text for c in _read(service, built, record) for e in c.governing_prose]


def _rules(entry: str, *keys: str) -> list[str]:
    return [t for k in keys for t in GEN.clause(entry, k)]


def test_a_named_record_read_directly_keeps_the_rules_governing_it(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    tools, weapons, armor = "equipment.tools", "equipment.weapons", "equipment.armor"
    # A Gaming Set's Utilize is one listed thing per action, and each variant
    # it lists needs its own proficiency (printed 93-94).
    assert _direct(service, built, f"{tools}.gaming_set") == [
        *_rules("tools", "utilize", "variants", "tool_proficiency"),
        *GEN.clause("tools", "gaming_set"),
    ]
    assert _direct(service, built, f"{tools}.thieves_tools") == [
        *_rules("tools", "utilize", "tool_proficiency"),
        *GEN.clause("tools", "thieves_tools"),
    ]
    # An artisan's tool also reads that each such tool is its own proficiency.
    assert _direct(service, built, f"{tools}.calligraphers_supplies") == [
        *_rules("tools", "utilize", "tool_proficiency", "artisans_tools"),
        *GEN.clause("tools", "calligraphers_supplies"),
    ]
    # A mastery is usable only through a feature that unlocks it (printed 90).
    for mastery in ("sap", "nick", "slow", "topple", "vex"):
        assert _direct(service, built, f"{weapons}.{mastery}") == [
            *_rules("weapons", "mastery_properties"),
            *GEN.clause("weapons", mastery),
        ]
    # A weapon row: its Mastery column needs a feature, and proficiency decides
    # its Proficiency Bonus (printed 89).
    assert _direct(service, built, f"{weapons}.club") == [
        *_rules("weapons", "mastery", "weapon_proficiency"),
        GEN.WEAPONS_HEAD,
        GEN.WEAPON_GROUPS["Simple Melee Weapons"],
        GEN.WEAPON_ROWS["Club"],
    ]
    # An armor row: training, what lacking it costs, and one at a time
    # (printed 92).
    assert _direct(service, built, f"{armor}.padded_armor") == [
        GEN.ARMOR_HEAD,
        GEN.ARMOR_GROUPS["Light Armor"],
        GEN.ARMOR_ROWS["Padded Armor"],
        *_rules("armor", "armor_training", "light_medium_or_heavy_armor"),
        *_rules("armor", "one_at_a_time"),
    ]
    assert _direct(service, built, f"{armor}.shield") == [
        GEN.ARMOR_HEAD,
        GEN.ARMOR_GROUPS["Shield"],
        GEN.ARMOR_ROWS["Shield"],
        *_rules("armor", "armor_training", "shield", "one_at_a_time"),
    ]
    # Each of those rules stays its section's, read once in the section view.
    for section, keys in (
        (tools, ("utilize", "variants", "tool_proficiency")),
        (weapons, ("mastery", "weapon_proficiency", "mastery_properties")),
        (armor, ("armor_training", "light_medium_or_heavy_armor", "one_at_a_time")),
    ):
        view = _read(service, built, section)
        for key in keys:
            (passage,) = GEN.clause(section.split(".")[1], key)[:1]
            assert [
                (c.record_key, c.component_key)
                for c in view
                for e in c.governing_prose
                if e.text == passage
            ] == [(section, key)]


def test_a_pointer_cites_its_own_words_before_its_context(built: Built) -> None:
    rep = built.proposal.proposed_representation
    spans = {s.span_id: s for s in built.ledger.spans}
    bindings = {prose_binding_target_key(b): b for b in rep.prose_bindings}
    reads: dict[tuple[str, str], dict[str, ProvenanceRole]] = {}
    cited: dict[tuple[str, ...], set[str]] = {}
    for c in rep.provenance:
        if c.target_kind is ProvenanceTargetKind.PROSE_BINDING:
            b = bindings[c.target_key]
            reads.setdefault((b.record_key, b.component_key), {})[c.span_id] = c.role
        elif c.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(tuple(c.target_key), set()).add(c.span_id)

    def text(span_id: str) -> str:
        s = spans[span_id]
        return built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]

    for key, found in cited.items():
        record, component, source = key[:3]
        read = reads[(record, component)]
        own = {s for s, r in read.items() if r is ProvenanceRole.PRIMARY}
        printing = {s for s in read if source in text(s)}
        # Its own texts that print the pointer, or else every context text
        # that does -- never a context passage beside its own words.
        assert found == (printing & own or printing), key
    ref = next(
        k
        for k in cited
        if k[:3] == ("equipment.armor.padded_armor", "padded_armor", "Disadvantage")
    )
    (row,) = cited[ref]
    assert text(row) == GEN.ARMOR_ROWS["Padded Armor"]


def test_a_suppressed_governing_rule_is_not_read_through_a_named_record(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    calligraphy, padded = (
        "equipment.tools.calligraphers_supplies",
        "equipment.armor.padded_armor",
    )
    (artisans,) = GEN.clause("tools", "artisans_tools")
    (training,) = GEN.clause("armor", "armor_training")
    for entry, record, passage in (
        (_disable("equipment.tools.artisans_tools"), calligraphy, artisans),
        (
            _replaced("equipment.armor", "armor_training", "House training."),
            padded,
            training,
        ),
    ):
        service = _service(persisted, built, monkeypatch, entry)
        read = _direct(service, built, record)
        assert passage not in read
        assert read  # the record itself still reads
        assert "House training." not in read
