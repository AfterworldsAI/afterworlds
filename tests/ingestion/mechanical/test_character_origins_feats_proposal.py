"""The ``character-origins-feats`` proposal, offered for review -- CRD Issue 5d.

The whole *Character Origins* part -- background and species structure, the
four backgrounds and nine species with their traits, lineages, legacies and
tables -- and the whole *Feats* part -- feat structure, categories,
prerequisites, repeatability and all seventeen feats -- proposed by
``.claude/review-notes/issue-5d-character-origins-feats-generator.py`` from
the release 5c actually publishes. Nothing here accepts it or records a
resolution; the Owner's acceptance and all three resolutions are recorded by
the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_character_origins_feats_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings read back from the proposal: every component
  stays prose-bound; each option keeps its choice, lineage table, scaling,
  uses and recovery with it; each feat's category line carries its
  prerequisite and each *Repeatable* stays its feat's own component; only the
  two fiction-bound traits are contextual; and a GameMaster reads every
  passage in printed order, each table after the trait prose that selects
  from it -- and the eleven accepted batches' passages read in printed order
  too;
* references: each background's feat and the Human's advice name their feat
  records, the part pointers name *Feat Descriptions*, accepted glossary terms
  are cited and unaccepted ones are not, and every spell, class and equipment
  catalogue member stays an explicit unresolved reference;
* every word of every spanned leaf is claimed, only headings are excluded, and
  a dropped example, advice, table, table row, prerequisite, *Repeatable* or
  component is reported;
* catalogue membership (Owner decision 2026-09-23): each of the three
  catalogue sections is ``CATALOGUE_MEMBER``-linked (schema 16) by exactly the
  4, 9 and 17 entries its container prints, and the authoring seam refuses any
  other list; through the rules-authority service, naming a section reaches
  exactly its surviving members and nothing else, introduction first and then
  the entries in printed order, in the slice and the GameMaster view alike; a
  component selector does not expand, mixed selectors order the same whatever
  their order, a disabled member is not resurrected, specific feat links stay
  specific, and eligibility stays each member's own printed text;
* composed *in this test only* with the committed eleven-batch acceptance, its
  three resolutions and 29 findings, re-derived by its script: every glossary
  target closes, only this batch's unresolved catalogue pointers are added,
  exactly the batch's 208 leaves gain coverage and the three recorded
  resolutions still apply. Both sides are the superseded release's; its
  physical source is not available, so the composition is checked without a
  corpus: its uncovered-leaf counts are retired, while native acceptance, which
  needs none, still reports exactly each proposed span's missing approval and
  none for the accepted prior (``correction-followup.md``);
* the three resolution drafts (recorded since, by the acceptance script) name
  the accepted "Character Origins" and "Feats" citations exactly, cannot apply
  while their targets are unaccepted, and -- in memory only -- resolve all
  three once the batch is accepted.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.accounting import validate_acceptance
from afterworlds.ingestion.mechanical.authoring import Built, build_entry_batch
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
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
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
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
    RelationshipDraft,
    RelationshipKind,
    reference_target_key,
    relationship_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
    SCHEMA_16_HASH,
    SCHEMA_16_VERSION,
    lift_accepted_inputs,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    SourceProse,
    _base_records,
    apply_override_set,
)
from afterworlds.services.rules_authority.binding import BindingResolution
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import (
    RulesAuthorityService,
    _select,
    source_leaf_order,
)
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

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-character-origins-feats-generator.py"
BATCH = "character-origins-feats"
PROPOSAL = proposal_path(BATCH)
#: The eleven-batch acceptance with three resolutions this proposal is offered
#: against, as committed in ``0dd25f9``.
IDENTITY = identity(BATCH)

GLOSSARY = "srd-5.2.1/rules-glossary"
ORIGINS, FEATS = "srd-5.2.1/character-origins", "srd-5.2.1/feats"
CLASSES, EQUIPMENT = "srd-5.2.1/classes", "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
PRIOR_RESOLUTIONS = [
    "resolve-attack-roll-playing-the-game-1",
    "resolve-armor-class-character-creation-1",
    "resolve-proficiency-bonus-character-creation-1",
]


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: The catalogue members this batch cites and no record defines, by scope.
NEW_UNRESOLVED = Counter({SPELLS: 23, EQUIPMENT: 35, CLASSES: 7})
#: Accepted glossary entries this batch cites; each is an unknown target to
#: the batch alone and closes composed.
GLOSSARY_TARGETS = {
    "armor_class",
    "attack",
    "attack_roll",
    "carrying_capacity",
    "charmed",
    "creature_type",
    "damage_types",
    "darkvision",
    "dash",
    "fly_speed",
    "frightened",
    "grappled",
    "hide",
    "hit_points",
    "incapacitated",
    "initiative",
    "invisible",
    "long_rest",
    "magic",
    "poisoned",
    "prone",
    "resistance",
    "short_rest",
    "size",
    "speed",
    "temporary_hit_points",
    "tremorsense",
    "truesight",
    "unarmed_strike",
    "unoccupied_space",
    "utilize",
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("character_origins_feats", GENERATOR)


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
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


@pytest.fixture(scope="module")
def prior() -> AcceptedInputs:
    """The eleven-batch acceptance, all three resolutions included.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("character-creation-foundations")
    return inputs


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (record, key)
    ]
    return c


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


def test_a_batch_is_stamped_only_with_a_schema_that_admits_it(session) -> None:  # type: ignore[no-untyped-def]
    # Earlier batches keep the schema they were reviewed under, so their
    # committed bytes still re-derive. This one states catalogue membership,
    # which schema 15 cannot, so pinning it there is refused, not restamped.
    pinned = dataclasses.replace(
        GEN.batch(), schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH)
    )
    with pytest.raises(ValueError, match="not admissible under it.*catalogue_member"):
        build_entry_batch(session, pinned, published_release_binding(session))


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
    ("backgrounds", ReviewUnitKind.SECTION, 15),
    ("acolyte", ReviewUnitKind.ENTRY, 2),
    ("criminal", ReviewUnitKind.ENTRY, 2),
    ("sage", ReviewUnitKind.ENTRY, 2),
    ("soldier", ReviewUnitKind.ENTRY, 2),
    ("species", ReviewUnitKind.SECTION, 16),
    ("dragonborn", ReviewUnitKind.ENTRY, 10),
    ("dwarf", ReviewUnitKind.ENTRY, 8),
    ("elf", ReviewUnitKind.ENTRY, 11),
    ("gnome", ReviewUnitKind.ENTRY, 8),
    ("goliath", ReviewUnitKind.ENTRY, 12),
    ("halfling", ReviewUnitKind.ENTRY, 7),
    ("human", ReviewUnitKind.ENTRY, 6),
    ("orc", ReviewUnitKind.ENTRY, 7),
    ("tiefling", ReviewUnitKind.ENTRY, 9),
    ("feat_descriptions", ReviewUnitKind.SECTION, 12),
    ("alert", ReviewUnitKind.ENTRY, 5),
    ("magic_initiate", ReviewUnitKind.ENTRY, 7),
    ("savage_attacker", ReviewUnitKind.ENTRY, 3),
    ("skilled", ReviewUnitKind.ENTRY, 4),
    ("ability_score_improvement", ReviewUnitKind.ENTRY, 4),
    ("grappler", ReviewUnitKind.ENTRY, 7),
    ("archery", ReviewUnitKind.ENTRY, 3),
    ("defense", ReviewUnitKind.ENTRY, 3),
    ("great_weapon_fighting", ReviewUnitKind.ENTRY, 3),
    ("two_weapon_fighting", ReviewUnitKind.ENTRY, 3),
    ("boon_of_combat_prowess", ReviewUnitKind.ENTRY, 5),
    ("boon_of_dimensional_travel", ReviewUnitKind.ENTRY, 5),
    ("boon_of_fate", ReviewUnitKind.ENTRY, 5),
    ("boon_of_irresistible_offense", ReviewUnitKind.ENTRY, 6),
    ("boon_of_spell_recall", ReviewUnitKind.ENTRY, 5),
    ("boon_of_the_night_spirit", ReviewUnitKind.ENTRY, 6),
    ("boon_of_truesight", ReviewUnitKind.ENTRY, 5),
]


def test_scope_is_both_whole_parts_less_their_titles(session, built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, u.kind, len(u.leaf_ids)) for u in units] == [
        (f"character-origins-feats/{s}", kind, n) for s, kind, n in UNITS
    ]
    part = {"backgrounds": "character_origins", "feat_descriptions": "feats"}
    prefix, kinds = "", []
    for s, _, _ in UNITS:
        prefix = part.get(s, prefix)
        kinds.append(f"{prefix}.{s}")
    records = built.proposal.proposed_representation.records
    assert [r.semantic_key for r in records] == kinds
    assert Counter(r.kind for r in records) == {
        RecordKind.CHARACTER_CREATION: 2,
        RecordKind.BACKGROUND: 4,
        RecordKind.SPECIES: 9,
        RecordKind.GENERAL_RULE: 1,
        RecordKind.FEAT: 17,
    }
    # Each part is contiguous (its category headings interleave with the feats
    # they head), and its title, the leaf before it, is owned by no unit.
    for block, size in ((units[:15], 117), (units[15:], 91)):
        flat = sorted(
            built.leaf_rows[leaf].occurrence_index for u in block for leaf in u.leaf_ids
        )
        assert flat == list(range(flat[0], flat[0] + size))
        (title,) = session.query(
            LedgerLeafORM.content, LedgerLeafORM.container_path
        ).filter(
            LedgerLeafORM.package_uuid == built.binding.package_uuid,
            LedgerLeafORM.occurrence_index == flat[0] - 1,
        )
        assert title.content in ("# Character Origins", "# Feats")
        # Both ends: every leaf under the part's title, less the title, is here.
        (root,) = title.container_path
        under = session.query(
            LedgerLeafORM.occurrence_index, LedgerLeafORM.container_path
        ).filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        assert sorted(o for o, path in under if path[0] == root) == [flat[0] - 1, *flat]
    assert sum(len(u.leaf_ids) for u in units) == 208


def test_no_leaf_is_owned_by_an_accepted_unit(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # Both sides are the superseded release's state, never mixed with the current.
    assert recorded.binding == prior.oracle.binding
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert len(mine) == 208
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
    assert unknown == GLOSSARY_TARGETS
    assert len(found["representation"]) == 165


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_every_component_stays_faithful_prose(built) -> None:  # type: ignore[no-untyped-def]
    # Uses equal to Proficiency Bonus, 5/11/17 scaling and Darkvision ranges
    # have no faithful closed family, so none is typed.
    components = built.proposal.proposed_representation.components
    assert len(components) == 149
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    text = PROPOSAL.read_text("utf-8")
    for family in ("ResourceRecoveryFact", "ScalingFact", "SenseFact"):
        assert family not in text


def test_only_the_fiction_bound_traits_are_contextual(built) -> None:  # type: ignore[no-untyped-def]
    reasons = Counter(
        c.irreducibility_reason_code or c.prose_retention_reason_code
        for c in built.proposal.proposed_representation.components
    )
    assert reasons == {
        "no_identified_structured_use": 147,
        "contextual_applicability": 2,
    }
    assert "gamemaster_latitude" not in PROPOSAL.read_text("utf-8")
    assert [
        (c.record_key, c.semantic_key)
        for c in built.proposal.proposed_representation.components
        if c.irreducibility_reason_code == "contextual_applicability"
    ] == [
        ("character_origins.dwarf", "stonecunning"),
        ("character_origins.goliath", "large_form"),
    ]


def test_each_option_keeps_its_scaling_uses_and_recovery(built) -> None:  # type: ignore[no-untyped-def]
    breath = _texts(built, "character_origins.dragonborn", "breath_weapon")
    assert len(breath) == 2
    assert "levels 5 (2d10), 11 (3d10), and 17 (4d10)" in breath[0]
    assert breath[1].startswith("You can use this Breath Weapon a number of times")
    assert "when you finish a Long Rest" in breath[1]
    for record, key, recovery in (
        ("dwarf", "stonecunning", "Long Rest"),
        ("orc", "adrenaline_rush", "Short or Long Rest"),
    ):
        texts = _texts(built, f"character_origins.{record}", key)
        assert len(texts) == 2
        assert "equal to your Proficiency Bonus" in texts[1]
        assert texts[1].endswith(f"when you finish a {recovery}.")
    # Giant Ancestry's shared uses clause precedes its six options, together.
    giant = _texts(built, "character_origins.goliath", "giant_ancestry")
    assert len(giant) == 7
    assert "equal to your Proficiency Bonus" in giant[0]
    assert [t.split(".**")[0] for t in giant[1:]] == [
        "**Cloud's Jaunt (Cloud Giant)",
        "**Fire's Burn (Fire Giant)",
        "**Frost's Chill (Frost Giant)",
        "**Hill's Tumble (Hill Giant)",
        "**Stone's Endurance (Stone Giant)",
        "**Storm's Thunder (Storm Giant)",
    ]
    # Level gates stay in the trait they gate.
    (flight,) = _texts(built, "character_origins.dragonborn", "draconic_flight")
    assert flight.startswith("_Draconic Flight._ When you reach character level 5")
    (large,) = _texts(built, "character_origins.goliath", "large_form")
    assert "Starting at character level 5" in large
    assert "big enough space" in large


@pytest.mark.parametrize(
    ("record", "key", "table", "choice"),
    [
        ("elf", "elven_lineage", "ELVEN_LINEAGES_TABLE", "when you select the lineage"),
        (
            "tiefling",
            "fiendish_legacy",
            "FIENDISH_LEGACIES_TABLE",
            "when you select the legacy",
        ),
    ],
)
def test_a_lineage_keeps_its_choice_levels_ability_and_table(  # type: ignore[no-untyped-def]
    built, record, key, table, choice
) -> None:
    texts = _texts(built, f"character_origins.{record}", key)
    assert len(texts) == 4
    assert "You gain the level 1 benefit" in texts[0]
    assert texts[1] == GEN.HIGHER_LEVEL_SPELLS
    assert choice in texts[2]
    assert texts[3] == getattr(GEN, table)
    assert getattr(GEN, table).count("<tr>") == 4


def test_lineage_exceptions_stay_with_their_rows(built) -> None:  # type: ignore[no-untyped-def]
    # The Drow's 120-foot Darkvision and the Wood Elf's 35-foot Speed modify
    # the species' own lines; both stay in the lineage table, not detached.
    (darkvision,) = _texts(built, "character_origins.elf", "darkvision")
    assert darkvision.endswith("range of 60 feet.")
    (speed,) = _texts(built, "character_origins.elf", "speed")
    assert speed == "**Speed:** 30 feet"
    table = _texts(built, "character_origins.elf", "elven_lineage")[-1]
    assert "Darkvision increases to 120 feet" in table
    assert "Speed increases to 35 feet" in table
    assert "replace that cantrip with a different cantrip" in table
    ancestors = _texts(built, "character_origins.dragonborn", "draconic_ancestry")
    assert ancestors[-1] == GEN.DRACONIC_ANCESTORS_TABLE
    assert GEN.DRACONIC_ANCESTORS_TABLE.count("<tr>") == 6


def test_gnomish_lineage_keeps_both_options_and_the_device_limits(built) -> None:  # type: ignore[no-untyped-def]
    texts = _texts(built, "character_origins.gnome", "gnomish_lineage")
    assert [t[:16] for t in texts] == [
        "_Gnomish Lineage",
        "**Forest Gnome.*",
        "**Rock Gnome.** ",
        "You can have thr",
    ]
    assert GEN.ROCK_GNOME_EXAMPLE not in "\n".join(texts)


def test_each_feat_carries_its_category_prerequisite_and_repeatability(built) -> None:  # type: ignore[no-untyped-def]
    categories = {
        slug: _texts(built, f"feats.{slug}", "category")[0]
        for slug, _, _ in GEN.FEAT_ENTRIES
    }
    assert Counter(categories.values()) == {
        "_Origin Feat_": 4,
        "_General Feat (Prerequisite: Level 4+)_": 1,
        "_General Feat (Prerequisite: Level 4+, Strength or Dexterity 13+)_": 1,
        "_Fighting Style Feat (Prerequisite: Fighting Style Feature)_": 4,
        "_Epic Boon Feat (Prerequisite: Level 19+)_": 6,
        "_Epic Boon Feat (Prerequisite: Level 19+, Spellcasting Feature)_": 1,
    }
    # The category heading each feat is printed under agrees with its line.
    for slug, _, heading in GEN.FEAT_ENTRIES:
        assert categories[slug].startswith("_" + heading.split(" Feats")[0])
    repeatable = sorted(
        c.record_key
        for c in built.proposal.proposed_representation.components
        if c.semantic_key == "repeatable"
    )
    assert repeatable == [
        "feats.ability_score_improvement",
        "feats.feat_descriptions",
        "feats.magic_initiate",
        "feats.skilled",
    ]
    (magic,) = _texts(built, "feats.magic_initiate", "repeatable")
    assert magic.endswith("you must choose a different spell list each time.")
    (spell_change,) = _texts(built, "feats.magic_initiate", "spell_change")
    assert spell_change.startswith("_Spell Change._ Whenever you gain a new level")


def test_background_lines_stay_one_component_each(built) -> None:  # type: ignore[no-untyped-def]
    lines = ("ability_scores", "feat", "skill_proficiencies", "tool_proficiency")
    for slug, _ in GEN.BACKGROUND_ENTRIES:
        keys = [
            c.semantic_key
            for c in built.proposal.proposed_representation.components
            if c.record_key == f"character_origins.{slug}"
        ]
        assert keys == [*lines, "equipment"]
    (soldier,) = _texts(built, "character_origins.soldier", "equipment")
    assert soldier.startswith("**Equipment:** _Choose A or B:_ (A) Spear")
    assert soldier.endswith("; or (B) 50 GP")


def test_examples_and_advice_are_supporting_never_rules(built) -> None:  # type: ignore[no-untyped-def]
    assert [(e, k) for e, _, k in GEN.SUPPORTING] == [
        ("species", "species"),
        ("gnome", "gnomish_lineage"),
        ("human", "versatile"),
    ]
    clauses = {t for _, _, _, ts in GEN.CLAUSES for t in ts}
    assert not {t for _, t, _ in GEN.SUPPORTING} & clauses
    assert not [t for t in clauses if "for example" in t.lower()]
    assert not [t for t in clauses if "recommended" in t]


# ---------------------------------------------------------------------------
# What a GameMaster reads
# ---------------------------------------------------------------------------


def _candidate(built: Built) -> ProjectionCandidate:
    return ProjectionCandidate(
        binding=built.binding,
        classification=built.ledger,
        representation=built.proposal.proposed_representation,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )


def _gamemaster(
    session: Session, built: Built
) -> dict[tuple[str, str], GameMasterComponent]:
    candidate = _candidate(built)
    authority = EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=UUID(built.binding.package_uuid),
            release_version=built.binding.release_version,
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "character-origins-feats"),
            override_set_uuid=uuid5(NAMESPACE_URL, "no-overrides"),
        ),
        records=tuple(
            _base_records(candidate, source_leaf_order(session, candidate)).values()
        ),
        applied_overrides=(),
    )
    prose = {
        row.chunk_id: row.content
        for row in session.query(RuleChunkORM).filter(
            RuleChunkORM.rules_package_id == str(built.binding.package_uuid)
        )
    }
    return {
        (c.record_key, c.component_key): c
        for c in build_gamemaster_view(authority, prose).components
    }


def _read(component: GameMasterComponent) -> list[str]:
    return [
        e.text
        for e in component.governing_prose
        if isinstance(e, SourceProse) and e.text
    ]


def test_a_gamemaster_reads_every_component_in_printed_order(session, built) -> None:  # type: ignore[no-untyped-def]
    view = _gamemaster(session, built)
    assert len(view) == len(built.proposal.proposed_representation.components)
    spans = {s.span_id: s for s in built.ledger.spans}
    multi = unlike_chunks = 0
    for key, component in view.items():
        passages = [e for e in component.governing_prose if isinstance(e, SourceProse)]
        printed = [
            (
                built.leaf_rows[spans[e.span_id].leaf_id].occurrence_index,
                spans[e.span_id].char_start,
            )
            for e in passages
        ]
        assert printed == sorted(printed), key
        multi += len(passages) > 1
        chunks = [e.chunk_id for e in passages]
        unlike_chunks += chunks != sorted(chunks)
        assert component.structured_context == ()
    assert (multi, unlike_chunks) == (MULTI, UNLIKE_CHUNKS)


#: Multi-passage components, and how many of them a chunk-id order misreads.
#: The second is a property of the release's uuid5 chunk ids: 5 on the
#: current ``8781d4e0-a3b`` (6 on ``574662e9-0ef``, 7 before it).
MULTI, UNLIKE_CHUNKS = 9, 5


@pytest.mark.parametrize(
    ("record", "key", "first", "last"),
    [
        (
            "character_origins.dragonborn",
            "draconic_ancestry",
            "_Draconic Ancestry._",
            "<table",
        ),
        (
            "character_origins.elf",
            "elven_lineage",
            "_Elven Lineage._",
            "<table",
        ),
        (
            "character_origins.tiefling",
            "fiendish_legacy",
            "_Fiendish Legacy._",
            "<table",
        ),
        (
            "character_origins.dragonborn",
            "breath_weapon",
            "_Breath Weapon._",
            "You can use this Breath Weapon",
        ),
        (
            "character_origins.gnome",
            "gnomish_lineage",
            "_Gnomish Lineage._",
            "You can have three such devices",
        ),
    ],
)
def test_a_gamemaster_reads_each_table_and_uses_clause_after_its_trait(  # type: ignore[no-untyped-def]
    session, built, record, key, first, last
) -> None:
    read = _read(_gamemaster(session, built)[(record, key)])
    assert read[0].startswith(first)
    assert last in read[-1]
    assert not [t for t in read[:-1] if last in t]


def test_the_accepted_components_read_in_printed_order(  # type: ignore[no-untyped-def]
    session, built, prior
) -> None:
    # The ordering is shared: the eleven accepted batches' records read the same way,
    # from the same release's ledger, through the loader the service uses. Read on the
    # current release with its current accepted authority: the recorded state binds the
    # superseded release's package, whose ledger the source DB does not hold
    # (``source_leaf_order`` is package-scoped; the leaf ids themselves are shared).
    # Record keys name no release.
    candidate = candidate_from_accepted_inputs(current())
    assert candidate.binding == built.binding
    every = _base_records(candidate, source_leaf_order(session, candidate))
    keys = {r.semantic_key for r in prior.oracle.representation.records}
    assert len(keys) == 103
    records = {key: every[key] for key in keys}
    spans = {s.span_id: s for s in candidate.classification.spans}
    position = {
        row.leaf_id: row.occurrence_index
        for row in session.query(LedgerLeafORM).filter(
            LedgerLeafORM.package_uuid == candidate.binding.package_uuid
        )
    }
    multi = 0
    for record in records.values():
        for component in record.components:
            passages = [
                e for e in component.governing_prose if isinstance(e, SourceProse)
            ]
            printed = [
                (position[spans[e.span_id].leaf_id], spans[e.span_id].char_start)
                for e in passages
            ]
            assert printed == sorted(printed), component.semantic_key
            multi += len(passages) > 1
    # The current accepted authority no longer holds three of the eleven's
    # multi-passage components; every other one reads here.
    bound = Counter(
        (b.record_key, b.component_key)
        for b in prior.oracle.representation.prose_bindings
    )
    assert sum(n > 1 for n in bound.values()) == ACCEPTED_MULTI
    held = {(key, c.semantic_key) for key, r in records.items() for c in r.components}
    assert {k for k, n in bound.items() if n > 1} - held == {
        ("play.exploration", "pace_effects"),
        ("play.exploration", "travel_pace"),
        ("play.proficiency", "skill_list"),
    }
    assert multi == ACCEPTED_MULTI - 3


#: Multi-passage components across the eleven accepted batches.
ACCEPTED_MULTI = 129


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def test_in_batch_pointers_name_their_records(built) -> None:  # type: ignore[no-untyped-def]
    named = sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.target_record_key)
        for r in built.proposal.proposed_representation.references
        if r.scope_key in (ORIGINS, FEATS)
    )
    assert named == [
        (
            "character_origins.acolyte",
            "feat",
            "Feats",
            "feats.magic_initiate",
        ),
        (
            "character_origins.backgrounds",
            "feat",
            "Feats",
            "feats.feat_descriptions",
        ),
        ("character_origins.criminal", "feat", "Feats", "feats.alert"),
        ("character_origins.human", "", "Skilled", "feats.skilled"),
        (
            "character_origins.human",
            "versatile",
            "Feats",
            "feats.feat_descriptions",
        ),
        ("character_origins.sage", "feat", "Feats", "feats.magic_initiate"),
        ("character_origins.soldier", "feat", "Feats", "feats.savage_attacker"),
    ]
    # Each background's named feat is the Origin feat it names.
    for slug, text in (
        ("acolyte", "Magic Initiate (Cleric)"),
        ("criminal", "Alert"),
        ("sage", "Magic Initiate (Wizard)"),
        ("soldier", "Savage Attacker"),
    ):
        (line,) = _texts(built, f"character_origins.{slug}", "feat")
        assert line == f'**Feat:** {text} (see "Feats")'
    # The part the species section belongs to is a mention, not a pointer.
    texts = {r.source_text for r in built.proposal.proposed_representation.references}
    assert "Character Origins" not in texts


def test_accepted_glossary_terms_are_cited_and_unaccepted_ones_are_not(built) -> None:  # type: ignore[no-untyped-def]
    refs = built.proposal.proposed_representation.references
    glossary = {r.target_record_key for r in refs if r.scope_key == GLOSSARY}
    assert glossary == {f"glossary.{s}" for s in GLOSSARY_TARGETS}
    (rules_glossary,) = [r for r in refs if r.source_text == "Rules Glossary"]
    assert (rules_glossary.from_record_key, rules_glossary.target_record_key) == (
        "character_origins.species",
        "glossary.creature_type",
    )
    texts = {r.source_text for r in refs}
    assert not texts & {
        "Advantage",
        "Bonus Action",
        "Reaction",
        "Heroic Inspiration",
        "Dim Light",
        "Proficiency Bonus",
        "D20 Test",
        "Cone",
        "Line",
        "Humanoid",
        "GP",
    }
    # "Short or Long Rest" cites each rest once, by distinct printed text.
    rush = {
        (r.source_text, r.target_record_key)
        for r in refs
        if (r.from_record_key, r.from_component_key)
        == ("character_origins.orc", "adrenaline_rush")
    }
    assert {
        ("Short or Long Rest", "glossary.short_rest"),
        ("Long Rest", "glossary.long_rest"),
    } <= rush


def test_catalogue_members_stay_explicit_unresolved_references(built) -> None:  # type: ignore[no-untyped-def]
    refs = built.proposal.proposed_representation.references
    unresolved = [r for r in refs if r.target_record_key == ""]
    assert Counter(r.scope_key for r in unresolved) == NEW_UNRESOLVED
    assert sorted(
        r.source_text
        for r in unresolved
        if r.from_record_key == "character_origins.elf"
    ) == sorted(
        [
            "Dancing Lights",
            "Darkness",
            "Detect Magic",
            "Druidcraft",
            "Faerie Fire",
            "Longstrider",
            "Misty Step",
            "Pass without Trace",
            "Prestidigitation",
            "Wizard spell list",
        ]
    )
    assert sorted(
        (r.from_record_key, r.source_text) for r in unresolved if r.scope_key == CLASSES
    ) == sorted(
        [
            ("character_origins.elf", "Wizard spell list"),
            ("feats.magic_initiate", "Cleric, Druid, or Wizard spell list"),
            ("feats.archery", "Fighting Style Feature"),
            ("feats.defense", "Fighting Style Feature"),
            ("feats.great_weapon_fighting", "Fighting Style Feature"),
            ("feats.two_weapon_fighting", "Fighting Style Feature"),
            ("feats.boon_of_spell_recall", "Spellcasting Feature"),
        ]
    )
    # No catalogue is stubbed: no record here belongs to one.
    assert not {r.kind for r in built.proposal.proposed_representation.records} & {
        RecordKind.SPELL,
        RecordKind.CLASS,
        RecordKind.EQUIPMENT,
    }


# ---------------------------------------------------------------------------
# Catalogue membership (Owner decision 2026-09-23)
# ---------------------------------------------------------------------------


def _catalogues() -> dict[str, list[str]]:
    """Each section record and the entries printed under it, from ``UNITS``."""
    part = {"backgrounds": "character_origins", "feat_descriptions": "feats"}
    prefix, section = "", ""
    out: dict[str, list[str]] = {}
    for slug, kind, _ in UNITS:
        prefix = part.get(slug, prefix)
        if kind is ReviewUnitKind.SECTION:
            section = f"{prefix}.{slug}"
            out[section] = []
        else:
            out[section].append(f"{prefix}.{slug}")
    return out


CATALOGUES = _catalogues()
FEAT_MEMBERS = set(CATALOGUES["feats.feat_descriptions"])
#: The five pointers that name one feat, which membership must not widen.
SPECIFIC_FEATS = {
    "feats.magic_initiate",
    "feats.alert",
    "feats.skilled",
    "feats.savage_attacker",
}


def test_each_section_lists_exactly_the_entries_its_container_prints(  # type: ignore[no-untyped-def]
    session, built
) -> None:
    assert {s: len(m) for s, m in CATALOGUES.items()} == {
        "character_origins.backgrounds": 4,
        "character_origins.species": 9,
        "feats.feat_descriptions": 17,
    }
    rep = built.proposal.proposed_representation
    assert [
        (r.source_record_key, r.target_record_key, r.kind) for r in rep.relationships
    ] == [
        (m, s, RelationshipKind.CATALOGUE_MEMBER)
        for s, members in CATALOGUES.items()
        for m in members
    ]
    # The release's own tree, read independently of the authoring seam: every
    # member leaf lies under the section heading's container, and no other
    # entry's does.
    units = {
        u.unit_id.rsplit("/", 1)[1]: u.leaf_ids
        for u in built.proposal.proposed_review_units
    }
    for section, members in CATALOGUES.items():
        slug = section.split(".", 1)[1]
        (path,) = [
            row.container_path
            for row in session.query(LedgerLeafORM).filter(
                LedgerLeafORM.package_uuid == built.binding.package_uuid,
                LedgerLeafORM.content == GEN.PLACEMENTS[slug].heading,
            )
        ]
        inside = {
            s
            for s, ids in units.items()
            if s != slug
            and all(built.leaf_rows[i].container_path[: len(path)] == path for i in ids)
        }
        assert sorted(inside) == sorted(m.split(".", 1)[1] for m in members)
    # Each edge cites, contextually, its member's first clause in printed order.
    spans = {s.span_id: s for s in built.ledger.spans}
    for rel in rep.relationships:
        (claim,) = [
            c
            for c in rep.provenance
            if c.target_kind is ProvenanceTargetKind.RELATIONSHIP
            and c.target_key == relationship_target_key(rel)
        ]
        assert claim.role is ProvenanceRole.CONTEXTUAL
        cited = {
            b.span_id
            for b in rep.prose_bindings
            if b.record_key == rel.source_record_key
        }
        first = min(
            cited,
            key=lambda i: (
                built.leaf_rows[spans[i].leaf_id].occurrence_index,
                spans[i].char_start,
            ),
        )
        assert claim.span_id == first
    # Carried by the kind schema 16 minted for it; containment is not reused.
    # Minted at schema 16, the pinned ``EntryBatch`` default since schema 17.
    assert built.proposal.schema_version == SCHEMA_16_VERSION
    assert built.proposal.schema_hash == SCHEMA_16_HASH
    assert RelationshipKind.SCOPED_WITHIN not in {r.kind for r in rep.relationships}


def _members_without(member: str) -> tuple[tuple[str, str], ...]:
    return tuple(m for m in GEN.MEMBERS if m[0] != member)


@pytest.mark.parametrize(
    ("members", "message"),
    [
        (_members_without("alert"), "section feat_descriptions prints"),
        ((*GEN.MEMBERS, ("human", "backgrounds")), "listed in both"),
        (
            (*_members_without("alert"), ("alert", "backgrounds")),
            "section backgrounds prints",
        ),
        ((*_members_without("alert"), ("alert", "nowhere")), "names no placed entry"),
        ((*GEN.MEMBERS, ("ghost", "feat_descriptions")), "names no placed entry"),
        ((*GEN.MEMBERS, ("species", "feat_descriptions")), "section feat_descriptions"),
    ],
    ids=["missing", "duplicate", "wrong-section", "unplaced", "unknown", "section"],
)
def test_the_authoring_seam_refuses_a_list_the_release_does_not_print(  # type: ignore[no-untyped-def]
    session, monkeypatch, members, message
) -> None:
    monkeypatch.setattr(GEN, "MEMBERS", members)
    with pytest.raises(ValueError, match=message):
        GEN.build(session)


def test_a_second_catalogue_citing_nothing_of_the_record_is_refused(built) -> None:  # type: ignore[no-untyped-def]
    # One record may be printed by two catalogues (Owner Decision 2026-09-27),
    # but only where each edge cites the record's own passages it prints; an
    # undeclared second parent is refused, never placed by guess.
    rep = built.proposal.proposed_representation
    before = relationship_and_reference_violations(rep)
    assert not [f for f in before if "catalogue member" in f]
    twice = dataclasses.replace(
        rep,
        relationships=(
            *rep.relationships,
            RelationshipDraft(
                "feats.alert",
                "character_origins.backgrounds",
                RelationshipKind.CATALOGUE_MEMBER,
            ),
        ),
    )
    after = relationship_and_reference_violations(twice)
    # Nor is what its first catalogue does not cite then read anywhere.
    keys = [c.semantic_key for c in rep.components if c.record_key == "feats.alert"]
    parents = "['character_origins.backgrounds', 'feats.feat_descriptions']"
    assert [f for f in after if f not in before] == [
        "record feats.alert: its catalogue edge to character_origins.backgrounds "
        "cites no span of its own components",
        *(
            f"record feats.alert: component {k} is printed by none of its "
            f"catalogues {parents}"
            for k in sorted(keys[1:])
        ),
    ]


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built):  # type: ignore[no-untyped-def]
    """The proposal persisted as a draft into a private copy of the release."""
    path = tmp_path_factory.mktemp("catalogue-membership") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(_candidate(built))
        persist_draft(s, identified, now="2026-09-23T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _disable(record_key: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"disable-{record_key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key=record_key
        ),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )


def _service(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, *entries: EffectiveOverrideEntry
) -> RulesAuthorityService:
    """The service over the persisted draft, from reconstruction onward.

    Only binding resolution is stood in: publishing or activating this
    unaccepted proposal is out of scope. Reconstruction, override application,
    selection, narrowing and the views are the production path.
    """
    session, projection_uuid = persisted
    state = EffectiveOverrideSet(
        built.binding.package_uuid, built.binding.release_version, entries
    )
    binding = RulesPackageBinding(
        package_uuid=UUID(built.binding.package_uuid),
        release_version=built.binding.release_version,
        mechanical_projection_uuid=UUID(projection_uuid),
        override_set_uuid=UUID(state.override_set_uuid),
    )
    service = RulesAuthorityService(session, now="2026-09-23T00:00:00Z")
    monkeypatch.setattr(
        service,
        "resolve",
        lambda **_: BindingResolution(
            AuthorityOutcome.RESOLVED, binding=binding, override_state=state
        ),
    )
    return service


def _request(built, *records: str, components=()) -> RuleSliceRequest:  # type: ignore[no-untyped-def]
    return RuleSliceRequest(
        package_id=UUID(built.binding.package_uuid),
        record_selectors=records,
        component_selectors=components,
    )


def _sliced(service, request) -> list[str]:  # type: ignore[no-untyped-def]
    result = service.rule_slice(request)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    return [r.semantic_key for r in result.slice.records]


def test_the_persisted_edges_rebuild_and_order_the_same(persisted, built) -> None:  # type: ignore[no-untyped-def]
    s, projection_uuid = persisted
    rebuilt = reconstruct_candidate(s, projection_uuid)
    rep = built.proposal.proposed_representation
    assert rebuilt.representation.relationships == rep.relationships
    relationship_claims = {
        c for c in rep.provenance if c.target_kind is ProvenanceTargetKind.RELATIONSHIP
    }
    assert len(relationship_claims) == 30
    assert relationship_claims <= set(rebuilt.representation.provenance)
    empty = EffectiveOverrideSet(
        built.binding.package_uuid, built.binding.release_version, ()
    )
    binding = RulesPackageBinding(
        package_uuid=UUID(built.binding.package_uuid),
        release_version=built.binding.release_version,
        mechanical_projection_uuid=UUID(projection_uuid),
        override_set_uuid=UUID(empty.override_set_uuid),
    )
    authorities = [
        apply_override_set(c, empty, binding, leaf_order=source_leaf_order(s, c))
        for c in (rebuilt, _candidate(built), rebuilt)
    ]
    assert authorities[0] == authorities[1] == authorities[2]
    assert dict(authorities[0].members) == {
        section: tuple(m) for section, m in CATALOGUES.items()
    }


@pytest.mark.parametrize("section", list(CATALOGUES))
def test_naming_a_catalogue_reaches_exactly_the_members_it_prints(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, section
) -> None:
    service = _service(persisted, built, monkeypatch)
    # Introduction first, then the entries exactly as the section prints them.
    expected = [section, *CATALOGUES[section]]
    assert _sliced(service, _request(built, section)) == expected
    view = service.gamemaster_view(_request(built, section))
    assert view.outcome is AuthorityOutcome.RESOLVED
    assert view.gamemaster_view is not None
    assert (
        list(dict.fromkeys(c.record_key for c in view.gamemaster_view.components))
        == expected
    )
    # One hop: the members bring no catalogue of their own with them.
    assert _sliced(service, _request(built, CATALOGUES[section][0])) == [
        CATALOGUES[section][0]
    ]


def test_the_feat_catalogue_reads_in_printed_not_key_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    """The one catalogue whose printed order is not its key order."""
    feats = CATALOGUES["feats.feat_descriptions"]
    assert feats[:4] == [
        "feats.alert",
        "feats.magic_initiate",
        "feats.savage_attacker",
        "feats.skilled",
    ]
    assert feats[4:6] == ["feats.ability_score_improvement", "feats.grappler"]
    assert feats != sorted(feats)
    service = _service(persisted, built, monkeypatch)
    request = _request(built, "feats.feat_descriptions")
    assert _sliced(service, request) == ["feats.feat_descriptions", *feats]
    view = service.gamemaster_view(request).gamemaster_view
    assert view is not None
    assert list(dict.fromkeys(c.record_key for c in view.components)) == [
        "feats.feat_descriptions",
        *feats,
    ]


def test_mixed_selectors_order_the_same_whatever_their_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    backgrounds = "character_origins.backgrounds"
    feats = "feats.feat_descriptions"
    service = _service(persisted, built, monkeypatch)
    records = (feats, "feats.grappler", backgrounds)
    components = (("character_origins.human", "versatile"),)
    expected = [
        backgrounds,
        *CATALOGUES[backgrounds],
        "character_origins.human",
        feats,
        *CATALOGUES[feats],
    ]
    for ordering in (records, tuple(reversed(records))):
        request = _request(built, *ordering, components=components)
        assert _sliced(service, request) == expected
        result = service.rule_slice(request)
        assert result.slice is not None
        (human,) = [
            r
            for r in result.slice.records
            if r.semantic_key == "character_origins.human"
        ]
        assert [c.semantic_key for c in human.components] == ["versatile"]


def test_every_catalogue_pointer_reaches_its_section_s_members(  # type: ignore[no-untyped-def]
    persisted, built, prior, monkeypatch
) -> None:
    drafted = {
        getattr(GEN, name)(prior.oracle.binding).target_record_key for name in DRAFTS
    }
    in_batch = sorted(
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key in CATALOGUES
    )
    assert drafted == set(CATALOGUES)
    assert in_batch == [
        ("character_origins.backgrounds", "feat", "feats.feat_descriptions"),
        ("character_origins.human", "versatile", "feats.feat_descriptions"),
    ]
    service = _service(persisted, built, monkeypatch)
    for target in drafted | {t for _, _, t in in_batch}:
        reached = _sliced(service, _request(built, target))
        assert set(CATALOGUES[target]) <= set(reached)
    # The specific links stay specific.
    links = [
        r.target_record_key
        for r in built.proposal.proposed_representation.references
        if r.scope_key == FEATS and r.target_record_key not in CATALOGUES
    ]
    assert len(links) == 5
    specific = set(links)
    assert specific == SPECIFIC_FEATS
    for target in sorted(specific):
        assert _sliced(service, _request(built, target)) == [target]


def test_reaching_a_catalogue_grants_no_eligibility(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    # Versatile reaches every feat; what it may choose is still its own text.
    (versatile,) = _texts(built, "character_origins.human", "versatile")
    assert (
        versatile
        == '_Versatile._ You gain an Origin feat of your choice (see "Feats").'
    )
    service = _service(persisted, built, monkeypatch)
    catalogue = service.rule_slice(_request(built, "feats.feat_descriptions"))
    assert catalogue.slice is not None
    members = [r for r in catalogue.slice.records if r.semantic_key in FEAT_MEMBERS]
    assert len(members) == 17
    for record in members:
        alone = service.rule_slice(_request(built, record.semantic_key))
        assert alone.slice is not None
        assert alone.slice.records == (record,)


def test_a_component_selector_on_a_section_reads_no_catalogue(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    request = _request(
        built,
        "feats.alert",
        components=(("feats.feat_descriptions", "prerequisite"),),
    )
    assert _sliced(service, request) == ["feats.alert", "feats.feat_descriptions"]
    result, scoped = service._scoped_authority(request)
    assert scoped is not None and scoped.members == ()


def test_a_disabled_member_or_section_is_not_resurrected(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch, _disable("feats.alert"))
    reached = _sliced(service, _request(built, "feats.feat_descriptions"))
    assert "feats.alert" not in reached and len(reached) == 17
    refused = service.rule_slice(_request(built, "feats.alert"))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE

    service = _service(
        persisted, built, monkeypatch, _disable("feats.feat_descriptions")
    )
    refused = service.rule_slice(_request(built, "feats.feat_descriptions"))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert _sliced(service, _request(built, "feats.alert")) == ["feats.alert"]
    _, authority = service._resolve_authority(_request(built, "feats.alert"))
    assert authority is not None
    assert "feats.feat_descriptions" not in dict(authority.members)


def test_an_edge_the_projection_cannot_honor_fails_closed(built, session) -> None:  # type: ignore[no-untyped-def]
    candidate = _candidate(built)
    rep = candidate.representation
    empty = EffectiveOverrideSet(
        built.binding.package_uuid, built.binding.release_version, ()
    )
    binding = RulesPackageBinding(
        package_uuid=UUID(built.binding.package_uuid),
        release_version=built.binding.release_version,
        mechanical_projection_uuid=uuid5(NAMESPACE_URL, "character-origins-feats"),
        override_set_uuid=UUID(empty.override_set_uuid),
    )
    order = source_leaf_order(session, candidate)
    # A member another release holds: this projection states no such record.
    stray = dataclasses.replace(
        candidate,
        representation=dataclasses.replace(
            rep,
            relationships=(
                *rep.relationships,
                RelationshipDraft(
                    "feats.lucky",
                    "feats.feat_descriptions",
                    RelationshipKind.CATALOGUE_MEMBER,
                ),
            ),
        ),
    )
    with pytest.raises(PersistedStateReconstructionError, match="feats.lucky"):
        apply_override_set(stray, empty, binding, leaf_order=order)
    # An edge whose own source claim was stripped has no printed place.
    alert = relationship_target_key(
        RelationshipDraft(
            "feats.alert",
            "feats.feat_descriptions",
            RelationshipKind.CATALOGUE_MEMBER,
        )
    )
    unplaced = dataclasses.replace(
        candidate,
        representation=dataclasses.replace(
            rep,
            provenance=tuple(
                c
                for c in rep.provenance
                if (c.target_kind, c.target_key)
                != (ProvenanceTargetKind.RELATIONSHIP, alert)
            ),
        ),
    )
    with pytest.raises(PersistedStateReconstructionError, match="feats.alert"):
        apply_override_set(unplaced, empty, binding, leaf_order=order)
    # A member needs no prose of its own: the edge places it.
    typed_only = dataclasses.replace(
        candidate,
        representation=dataclasses.replace(
            rep,
            prose_bindings=tuple(
                b for b in rep.prose_bindings if b.record_key != "feats.alert"
            ),
        ),
    )
    placed = apply_override_set(typed_only, empty, binding, leaf_order=order)
    assert dict(placed.members)["feats.feat_descriptions"] == tuple(
        CATALOGUES["feats.feat_descriptions"]
    )
    # And selection refuses a listed member it does not hold, rather than
    # returning the section as though it were the whole catalogue.
    authority = apply_override_set(candidate, empty, binding, leaf_order=order)
    torn = dataclasses.replace(
        authority,
        records=tuple(r for r in authority.records if r.semantic_key != "feats.alert"),
    )
    selected, missing = _select(torn, _request(built, "feats.feat_descriptions"))
    assert missing == {"member 'feats.alert' of record 'feats.feat_descriptions'"}


def test_the_accepted_authority_gains_no_membership(prior: AcceptedInputs) -> None:
    # Membership is read only from explicit ``CATALOGUE_MEMBER`` edges (``_members``),
    # the sole input of ``EffectiveAuthority.members``. The recorded state binds the
    # superseded release's package, whose ledger the source DB does not hold
    # (``source_leaf_order`` is package-scoped; the leaf ids themselves are shared). So
    # its edges are read directly rather than placed through a leaf order.
    candidate = candidate_from_accepted_inputs(prior)
    assert len(candidate.representation.records) == 103
    assert [
        r
        for r in candidate.representation.relationships
        if r.kind is RelationshipKind.CATALOGUE_MEMBER
    ] == []


# ---------------------------------------------------------------------------
# Headings and omission checks
# ---------------------------------------------------------------------------


def test_only_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    excluded = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert all(e.startswith("#") and "\n" not in e for e in excluded)
    assert len(excluded) == 33 + sum(len(h) for _, h, _ in GEN.EXCLUDED) == 51
    # No excluded heading states a number, a prerequisite or a category the
    # body does not restate.
    assert not [e for e in excluded if any(ch.isdigit() for ch in e)]
    assert not [e for e in excluded if "Prerequisite" in e]


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


def _drop_supporting(monkeypatch, text: str) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN, "SUPPORTING", tuple(s for s in GEN.SUPPORTING if s[1] != text)
    )


def _replace_clause_text(monkeypatch, old: str, new: str | None) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(new if t == old else t for t in ts if new or t != old))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )


@pytest.mark.parametrize("text", ["ROCK_GNOME_EXAMPLE", "SKILLED_ADVICE"])
def test_a_dropped_example_or_advice_sharing_a_leaf_is_residue(  # type: ignore[no-untyped-def]
    session, monkeypatch, text
) -> None:
    _drop_supporting(monkeypatch, getattr(GEN, text))
    if text == "SKILLED_ADVICE":
        monkeypatch.setattr(GEN, "RECORD_REFERENCES", ())
    assert list(_residue(GEN.build(session)).values()) == [getattr(GEN, text)]


def test_a_dropped_whole_leaf_introduction_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _drop_supporting(monkeypatch, GEN.SPECIES_GENESIS)
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit character-origins-feats/species: leaf ")
    assert found.endswith(
        "named by no expected rule, supporting group or excluded group"
    )


@pytest.mark.parametrize(
    ("text", "entry"),
    [
        ("DRACONIC_ANCESTORS_TABLE", "dragonborn"),
        ("ELVEN_LINEAGES_TABLE", "elf"),
        ("FIENDISH_LEGACIES_TABLE", "tiefling"),
        ("HIGHER_LEVEL_SPELLS", "elf"),
    ],
)
def test_a_dropped_table_or_level_paragraph_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, text, entry
) -> None:
    old = getattr(GEN, text)
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if not (e == entry and t == old)))
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
                c, refs=tuple(r for r in c.refs if r[0] in kept[(c.entry, c.key)])
            )
            for c in GEN.COMPONENTS
        ),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(f"review unit character-origins-feats/{entry}: leaf ")


@pytest.mark.parametrize(
    ("entry", "key"),
    [
        ("grappler", "category"),
        ("skilled", "repeatable"),
        ("magic_initiate", "repeatable"),
        ("feat_descriptions", "prerequisite"),
    ],
)
def test_a_dropped_prerequisite_or_repeatable_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, entry, key
) -> None:
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(c for c in GEN.CLAUSES if (c[0], c[1]) != (entry, key)),
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(c for c in GEN.COMPONENTS if (c.entry, c.key) != (entry, key)),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(f"review unit character-origins-feats/{entry}: leaf ")


@pytest.mark.parametrize(
    ("table", "row"),
    [
        ("DRACONIC_ANCESTORS_TABLE", "\n      <td>Black</td>"),
        ("ELVEN_LINEAGES_TABLE", "\n      <td>Wood Elf</td>"),
        ("FIENDISH_LEGACIES_TABLE", "\n      <td>Chthonic</td>"),
    ],
)
def test_a_table_missing_a_row_is_a_loud_locate_failure(  # type: ignore[no-untyped-def]
    session, monkeypatch, table, row
) -> None:
    text = getattr(GEN, table)
    start = text.index(row) - len("\n    <tr>")
    end = text.index("</tr>\n", start) + len("</tr>\n")
    shorter = text[:start] + text[end:]
    assert shorter.count("<tr>") == text.count("<tr>") - 1
    _replace_clause_text(monkeypatch, text, shorter)
    with pytest.raises(ValueError):
        GEN.build(session)


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            c
            for c in GEN.COMPONENTS
            if (c.entry, c.key) != ("grappler", "punch_and_grab")
        ),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit character-origins-feats/grappler: expected rule "
        "feats.grappler/punch_and_grab has no component"
    ) in found


# ---------------------------------------------------------------------------
# Test-only composition with the committed eleven-batch acceptance
# ---------------------------------------------------------------------------


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


def test_composed_every_glossary_target_closes_and_208_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    assert len(prior.oracle.representation.records) == 103
    assert len(prior.oracle.spans) == 844
    assert len(prior.batches) == 11
    assert [r.resolution_id for r in prior.oracle.reference_resolutions] == (
        PRIOR_RESOLUTIONS
    )
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert len(recorded.proposed_spans) == 172
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }

    # The accepted authority declares schema 15 and this proposal schema 16:
    # it is composed only after crossing the one registered lift, which
    # carries it by identity.
    current, crossed = lift_accepted_inputs(
        prior, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    # Validated at the build's schema, so it crosses every later registered
    # succession too: 16 -> 17, since CRD Issue 2b's G1 17 -> 18, and since
    # CRD Issue 15c's native C5 18 -> 19, and C7's 19 -> 20. Written
    # out as the literal chain so a new succession is reviewed here, not
    # inherited.
    assert [r.lift_id for r in crossed] == [
        "5d-lift-schema-15-to-16",
        "5d-lift-schema-16-to-17",
        "5d-lift-schema-17-to-18",
        "5d-lift-schema-18-to-19",
        "5d-lift-schema-19-to-20",
    ]
    assert current.oracle.representation is accepted
    composed = _composed(current, recorded)

    # The 29 retained findings stay, the three drafted citations among them.
    rest_before = sorted(_references(current))
    assert len(rest_before) == 29
    assert rest_before.count(_unresolved(ORIGINS, "Character Origins")) == 2
    assert rest_before.count(_unresolved(FEATS, "Feats")) == 1
    added = sorted(
        f for f in GEN.expected_representation_findings() if "unresolved reference" in f
    )
    # Unfiltered and representation-only: nothing else is reported.
    assert sorted(_references(composed)) == sorted(rest_before + added)
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(current) == []
    assert _acceptance(composed) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(composed) - _covered(current) == mine
    assert len(mine) == 208
    # The accepted part of the composition is the accepted bytes, unchanged.
    head = dataclasses.replace(
        composed,
        oracle=dataclasses.replace(
            composed.oracle,
            spans=composed.oracle.spans[:844],
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
    assert head == current


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
    effective = candidate_from_accepted_inputs(composed).representation
    assert {
        ("play.combat", "attack_structure", "play.d20_tests"),
        (
            "play.d20_tests",
            "armor_class",
            "character_creation.create_your_character",
        ),
        (
            "play.proficiency",
            "proficiency_bonus",
            "character_creation.level_advancement",
        ),
    } <= {
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in effective.references
    }


# ---------------------------------------------------------------------------
# The three "Character Origins" / "Feats" resolution drafts, as reviewed
# ---------------------------------------------------------------------------

DRAFTS = (
    "draft_choose_background_resolution",
    "draft_choose_species_resolution",
    "draft_background_feat_resolution",
)


@pytest.mark.parametrize("draft_name", DRAFTS)
def test_each_draft_names_an_accepted_citation_exactly(prior, draft_name) -> None:  # type: ignore[no-untyped-def]
    draft = getattr(GEN, draft_name)(prior.oracle.binding)
    accepted = prior.oracle.representation
    (ref,) = [
        r
        for r in accepted.references
        if (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        == (
            draft.from_record_key,
            draft.from_component_key,
            draft.source_text,
            draft.scope_key,
        )
    ]
    assert ref.target_record_key == ""
    cited = sorted(
        {
            c.span_id
            for c in accepted.provenance
            if c.target_kind is ProvenanceTargetKind.REFERENCE
            and c.target_key == reference_target_key(ref)
        }
    )
    assert tuple(cited) == draft.provenance_span_ids
    assert draft.resolution_id not in {
        r.resolution_id for r in prior.oracle.reference_resolutions
    }


def test_every_accepted_citation_into_these_parts_has_a_draft(prior) -> None:  # type: ignore[no-untyped-def]
    def key(r: ReferenceDraft | ReferenceResolution) -> tuple[str, str, str, str]:
        return (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)

    cited = [
        key(r)
        for r in prior.oracle.representation.references
        if r.scope_key in (ORIGINS, FEATS)
    ]
    drafted = [key(getattr(GEN, name)(prior.oracle.binding)) for name in DRAFTS]
    assert sorted(cited) == sorted(drafted)


def test_the_drafts_cannot_apply_to_the_accepted_authority_as_it_stands(prior) -> None:  # type: ignore[no-untyped-def]
    for name in DRAFTS:
        with pytest.raises(AcceptanceError, match="states no record for"):
            resolve_references(
                prior,
                resolutions=(getattr(GEN, name)(prior.oracle.binding),),
                authorized_by="test",
                authorization_reference="test",
                reviewer="test",
                resolved_at="2026-09-23T00:00:00Z",
            )


def test_once_accepted_all_three_drafts_resolve_through_the_native_seam(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # In memory only: nothing is written and no decision is recorded. The
    # recorded proposal over its recorded prior: both the superseded release's.
    oracle = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracle.glob("*.json")}
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="character-origins-feats",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-23T00:00:00Z",
        prior=prior,
    )
    # Accepting crosses the accepted authority over the one registered lift.
    assert accepted.oracle.schema_version == SCHEMA_16_VERSION
    assert [lift.lift_id for lift in accepted.lifts] == [
        *(lift.lift_id for lift in prior.lifts),
        "5d-lift-schema-15-to-16",
    ]
    binding = prior.oracle.binding
    resolved = resolve_references(
        accepted,
        resolutions=tuple(getattr(GEN, name)(binding) for name in DRAFTS),
        authorized_by="test",
        authorization_reference="test",
        reviewer="test",
        resolved_at="2026-09-23T00:00:00Z",
    )
    assert [r.resolution_id for r in resolved.oracle.reference_resolutions] == [
        *PRIOR_RESOLUTIONS,
        GEN.CHOOSE_BACKGROUND_RESOLUTION_ID,
        GEN.CHOOSE_SPECIES_RESOLUTION_ID,
        GEN.BACKGROUND_FEAT_RESOLUTION_ID,
    ]
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    targets = {
        (r.from_component_key, r.source_text, r.target_record_key)
        for r in effective.references
        if r.from_record_key == "character_creation.create_your_character"
        and r.scope_key in (ORIGINS, FEATS)
    }
    assert targets == {
        ("choose_background", "Character Origins", "character_origins.backgrounds"),
        ("choose_species", "Character Origins", "character_origins.species"),
        ("background_feat", "Feats", "feats.feat_descriptions"),
    }
    # The accepted citations themselves are not edited, and nothing is written.
    assert resolved.oracle.representation == accepted.oracle.representation
    assert {p.name: p.read_bytes() for p in oracle.glob("*.json")} == on_disk
