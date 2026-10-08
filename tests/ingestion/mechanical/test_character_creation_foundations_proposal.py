"""The ``character-creation-foundations`` proposal, offered for review -- CRD Issue 5d.

The whole *Character Creation* part -- sheet, the five creation steps, Level
Advancement and Tiers of Play, Starting at Higher Levels, Multiclassing and
Trinkets -- and the five Rules Glossary foundations the accepted Stat Block
cites (Alignment, Creature Type, Experience Points, Passive Perception, Size),
proposed by
``.claude/review-notes/issue-5d-character-creation-foundations-generator.py``
from the release 5c actually publishes. Nothing here accepts it or records a
resolution; the Owner's acceptance and both resolutions are recorded by
the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_character_creation_foundations_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings read back from the proposal: every component
  stays prose-bound (the Multiclass Spellcaster table is not typed as a
  character-level progression); the multiclass spellcasting scope, slot
  arithmetic, rounding, lookup and table stay one component apart from Pact
  Magic; Proficiency Bonus follows total character level; GM latitude, the
  creation and advancement kinds and the examples stay distinguishable; and a
  GameMaster reads every spellcasting passage in printed order, and each
  tier's level range (printed only in its heading) immediately before its
  description -- and the accepted batches' passages read in printed order too;
* every word of every spanned leaf is claimed, only headings whose meaning the
  body restates are excluded -- re-excluding the tier ranges passes every
  coverage check, so the reader is what pins them -- and a dropped example,
  footnote, table, table row or component is reported;
* composed *in this test only* with the ten-batch acceptance it is offered
  against, re-derived by its script, the five Stat Block targets close, only
  the batch's own pointers are added, exactly the batch's 179 leaves gain
  coverage, and the recorded attack-roll resolution still applies. Both sides
  are the superseded release's; its physical source is not available, so the
  composition is checked without a corpus: its uncovered-leaf counts are
  retired, while native acceptance, which needs none, still reports exactly
  each proposed span's missing approval and none for the accepted prior
  (``correction-followup.md``);
* the two resolution drafts (recorded since, by the acceptance script) name
  the accepted "Character Creation" citations exactly, cannot apply while
  their targets are unaccepted, and -- in memory only -- resolve both once the
  batch is accepted.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
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
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
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
    ProvenanceTargetKind,
    RecordKind,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    SourceProse,
    _base_records,
)
from afterworlds.services.rules_authority.service import source_leaf_order
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

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-character-creation-foundations-generator.py"
BATCH = "character-creation-foundations"
PROPOSAL = proposal_path(BATCH)
#: The ten-batch acceptance this proposal is offered against, as committed in
#: ``d58273c``.
IDENTITY = identity(BATCH)

CC, PLAY = "srd-5.2.1/character-creation", "srd-5.2.1/playing-the-game"
GLOSSARY, EQUIPMENT = "srd-5.2.1/rules-glossary", "srd-5.2.1/equipment"
TOOLBOX, CLASSES = "srd-5.2.1/gameplay-toolbox", "srd-5.2.1/classes"
ORIGINS, FEATS = "srd-5.2.1/character-origins", "srd-5.2.1/feats"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the committed acceptance leaves undefined: the five targets closed here.
CLOSED = sorted(
    _glossary(label, slug)
    for label, slug in [
        ("Alignment", "alignment"),
        ("Creature Type", "creature_type"),
        ("Experience Points", "experience_points"),
        ("Passive Perception", "passive_perception"),
        ("Size", "size"),
    ]
)
#: The accepted pointers into parts with no record; composed, each stays
#: unresolved -- the two "Character Creation" citations included, since
#: nothing here records their drafted resolutions.
ACCEPTED_UNRESOLVED = sorted(
    [_unresolved(CC, "Character Creation")] * 2
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(TOOLBOX, "Combat Encounters")]
    + [_unresolved(TOOLBOX, "Gameplay Toolbox")]
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
    + [_unresolved(PLAY, "Playing the Game")] * 2
    + [_unresolved("srd-5.2.1/monsters", "Monsters")]
)
#: What this batch adds that nothing accepted or proposed defines.
NEW = sorted(
    [_unresolved(ORIGINS, "Character Origins")] * 2
    + [_unresolved(CLASSES, "Classes")] * 6
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(FEATS, "Feats")]
    + [_unresolved(PLAY, "Playing the Game")] * 2
)
#: The components where the source delegates to the Game Master.
GM_COMPONENTS = [
    ("character_creation.create_your_character", "starting_at_a_higher_level"),
    ("character_creation.create_your_character", "choose_background"),
    ("character_creation.create_your_character", "generate_scores"),
    ("character_creation.create_your_character", "choose_alignment"),
    ("character_creation.create_your_character", "passive_perception"),
    ("character_creation.starting_at_higher_levels", "higher_starting_level"),
    ("character_creation.starting_at_higher_levels", "bonus_feats_at_level_20"),
    ("character_creation.starting_at_higher_levels", "starting_equipment"),
    ("character_creation.trinkets", "trinkets"),
    ("glossary.experience_points", "experience_points"),
    ("glossary.passive_perception", "passive_perception"),
]


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("character_creation_foundations", GENERATOR)


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
    """The ten-batch acceptance, attack-roll resolution included.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("core-play-dependencies")
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


def test_scope_is_the_whole_part_and_five_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, u.kind, len(u.leaf_ids)) for u in units] == [
        ("character-creation-foundations/character_sheet", ReviewUnitKind.SECTION, 2),
        (
            "character-creation-foundations/create_your_character",
            ReviewUnitKind.SECTION,
            97,
        ),
        (
            "character-creation-foundations/level_advancement",
            ReviewUnitKind.SECTION,
            22,
        ),
        (
            "character-creation-foundations/starting_at_higher_levels",
            ReviewUnitKind.SECTION,
            9,
        ),
        ("character-creation-foundations/multiclassing", ReviewUnitKind.SECTION, 33),
        ("character-creation-foundations/trinkets", ReviewUnitKind.SECTION, 3),
        ("character-creation-foundations/alignment", ReviewUnitKind.ENTRY, 2),
        ("character-creation-foundations/creature_type", ReviewUnitKind.ENTRY, 4),
        ("character-creation-foundations/experience_points", ReviewUnitKind.ENTRY, 2),
        ("character-creation-foundations/passive_perception", ReviewUnitKind.ENTRY, 3),
        ("character-creation-foundations/size", ReviewUnitKind.ENTRY, 2),
    ]
    creation, advancement = RecordKind.CHARACTER_CREATION, (
        RecordKind.CHARACTER_ADVANCEMENT
    )
    assert [
        (r.semantic_key, r.kind) for r in built.proposal.proposed_representation.records
    ] == [
        ("character_creation.character_sheet", creation),
        ("character_creation.create_your_character", creation),
        ("character_creation.level_advancement", advancement),
        ("character_creation.starting_at_higher_levels", creation),
        ("character_creation.multiclassing", advancement),
        ("character_creation.trinkets", creation),
        ("glossary.alignment", RecordKind.GLOSSARY_RULE),
        ("glossary.creature_type", RecordKind.GLOSSARY_RULE),
        ("glossary.experience_points", RecordKind.GLOSSARY_RULE),
        ("glossary.passive_perception", RecordKind.GLOSSARY_RULE),
        ("glossary.size", RecordKind.GLOSSARY_RULE),
    ]
    # The part's six sections are contiguous and in printed order.
    part = [
        sorted(built.leaf_rows[leaf].occurrence_index for leaf in u.leaf_ids)
        for u in units[:6]
    ]
    flat = [i for ids in part for i in ids]
    assert flat == list(range(flat[0], flat[0] + 166))


def test_no_leaf_is_owned_by_an_accepted_unit(built, prior) -> None:  # type: ignore[no-untyped-def]
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & {leaf for ids in built.entry_leaves.values() for leaf in ids}


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    assert found["representation"] == sorted(
        NEW
        + [
            _glossary("Breaking Objects", "breaking_objects"),
            _glossary("Short Rest", "short_rest"),
            f"reference {PLAY}:'Combat': unknown target record play.combat",
        ]
    )


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_every_component_stays_faithful_prose(built) -> None:  # type: ignore[no-untyped-def]
    # No closed family states these rules; the Multiclass Spellcaster table in
    # particular is not a character-level ``SpellSlotProgressionFact``.
    components = built.proposal.proposed_representation.components
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    assert "SpellSlotProgressionFact" not in PROPOSAL.read_text("utf-8")


def test_multiclass_spellcasting_keeps_its_scope_arithmetic_and_table(built) -> None:  # type: ignore[no-untyped-def]
    texts = _texts(built, "character_creation.multiclassing", "spellcasting")
    assert texts[0].startswith("Your capacity for spellcasting depends partly")
    assert (
        "Once you have the Spellcasting feature from more than one class, "
        "use the rules below." in texts[0]
    )
    joined = "\n".join(texts)
    for rule in (
        "for each class individually, as if you were a single-classed member",
        "you use the spellcasting ability of that class",
        "based on your total character level, not your level in a particular "
        "class, unless the spell says otherwise",
        "- All your levels in the Bard, Cleric, Druid, Sorcerer, and Wizard classes",
        "- Half your levels (round up) in the Paladin and Ranger classes",
        "look up this total level in the Level column of the Multiclass "
        "Spellcaster table",
        "only to cast your lower-level spells",
    ):
        assert rule in joined
    assert texts[-1] == GEN.MULTICLASS_SPELLCASTER_TABLE
    assert GEN.MULTICLASS_SPELLCASTER_TABLE.count("<tr>") == 21
    # Pact Magic states its own condition, outside the multi-Spellcasting scope.
    (pact,) = _texts(built, "character_creation.multiclassing", "pact_magic")
    assert pact.startswith("_Pact Magic._ If you have the Pact Magic feature")
    assert pact not in texts


def test_proficiency_bonus_follows_total_character_level(built) -> None:  # type: ignore[no-untyped-def]
    (multiclass,) = _texts(
        built, "character_creation.multiclassing", "proficiency_bonus"
    )
    assert (
        "based on your total character level, not your level in a particular class"
        in (multiclass)
    )
    (xp,) = _texts(built, "character_creation.multiclassing", "experience_points")
    assert "based on your total character level" in xp
    table_refs = {
        (r.from_component_key, r.source_text, r.scope_key, r.target_record_key)
        for r in built.proposal.proposed_representation.references
        if r.from_record_key == "character_creation.multiclassing"
        and r.source_text == "Character Advancement table"
    }
    assert table_refs == {
        (key, "Character Advancement table", CC, "character_creation.level_advancement")
        for key in ("experience_points", "proficiency_bonus")
    }
    (step,) = _texts(built, "character_creation.level_advancement", "proficiency_bonus")
    assert step.startswith("**4: Adjust Proficiency Bonus.**")


def test_gamemaster_latitude_and_examples_stay_distinguishable(built) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    gm = [
        (c.record_key, c.semantic_key)
        for c in components
        if c.irreducibility_reason_code == "gamemaster_latitude"
    ]
    assert gm == GM_COMPONENTS
    # Examples are supporting authority, never a rule of the component.
    examples = {t for e, t, _ in GEN.SUPPORTING if "for example" in t.lower()}
    assert len(examples) == 14
    substantive = [
        (e, k)
        for e, k, _, texts in GEN.CLAUSES
        for t in texts
        if "for example" in t.lower()
    ]
    # Only where the example is the GM's own latitude (what equipment is on
    # sale) does it stay in a clause; it cannot be split from the rule sentence.
    assert substantive == [("starting_at_higher_levels", "starting_equipment")]


# ---------------------------------------------------------------------------
# What a GameMaster reads
# ---------------------------------------------------------------------------


def _gamemaster(
    session: Session, built: Built
) -> dict[tuple[str, str], GameMasterComponent]:
    candidate = ProjectionCandidate(
        binding=built.binding,
        classification=built.ledger,
        representation=built.proposal.proposed_representation,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )
    authority = EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=UUID(built.binding.package_uuid),
            release_version=built.binding.release_version,
            mechanical_projection_uuid=uuid5(
                NAMESPACE_URL, "character-creation-foundations"
            ),
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


def test_a_gamemaster_reads_every_component_whole(session, built) -> None:  # type: ignore[no-untyped-def]
    view = _gamemaster(session, built)
    assert len(view) == len(built.proposal.proposed_representation.components) == 69
    spell = view[("character_creation.multiclassing", "spellcasting")]
    read = " ".join(
        e.text for e in spell.governing_prose if isinstance(e, SourceProse) and e.text
    )
    assert "use the rules below" in read and "(round up)" in read
    assert "Multiclass Spellcaster: Spell Slots per Spell Level" in read
    # The passages read in printed order: scope first, the table last.
    assert read.startswith("Your capacity for spellcasting depends partly")
    assert read.index("(round up)") < read.index("Multiclass Spellcaster: Spell")

    # Every component reads its passages in the release's printed order --
    # ledger position, then position within the leaf -- which for most
    # multi-passage components is not the order of their opaque chunk ids.
    spans = {s.span_id: s for s in built.ledger.spans}
    unlike_chunks = set()
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
        if [e.chunk_id for e in passages] != sorted(e.chunk_id for e in passages):
            unlike_chunks.add(key)
    assert len([c for c in view.values() if len(c.governing_prose) > 1]) == 29
    # A property of the release's uuid5 chunk ids: 21 on the current
    # ``8781d4e0-a3b`` (18 on ``3fe24ff6-4e3``, 17 on ``574662e9-0ef``).
    assert len(unlike_chunks) == 21
    assert {
        ("character_creation.multiclassing", "spellcasting"),
        ("character_creation.level_advancement", "tiers_of_play"),
    } <= unlike_chunks
    # ...including two passages of one leaf, read in their order within it.
    hit_point_dice = view[("character_creation.multiclassing", "hit_point_dice")]
    one_leaf = [e for e in hit_point_dice.governing_prose if isinstance(e, SourceProse)]
    assert len(one_leaf) == 2
    assert len({spans[e.span_id].leaf_id for e in one_leaf}) == 1
    assert spell.structured_context == ()


#: Each tier's level range, printed only in its heading, and the description it
#: labels.
TIERS = [
    ("#### Tier 1 (Levels 1–4)", "In tier 1, characters are apprentice"),
    ("#### Tier 2 (Levels 5–10)", "In tier 2, characters are full-fledged"),
    ("#### Tier 3 (Levels 11–16)", "In tier 3, characters have reached"),
    ("#### Tier 4 (Levels 17–20)", "At tier 4, characters achieve the pinnacle"),
]


def _tiers_read(session: Session, built: Built) -> list[str]:
    """What a GameMaster reads for Tiers of Play, in the order it reads it.

    Every passage read carries its binding's provenance, so the order is the
    view's, not a reconstruction from the ledger.
    """
    tiers = _gamemaster(session, built)[
        ("character_creation.level_advancement", "tiers_of_play")
    ]
    assert tiers.structured_context == ()  # descriptive, never a mechanic
    passages = [
        e for e in tiers.governing_prose if isinstance(e, SourceProse) and e.text
    ]
    cited = {
        c.span_id
        for c in built.proposal.proposed_representation.provenance
        if c.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and c.target_key[:2]
        == ("character_creation.level_advancement", "tiers_of_play")
    }
    assert {e.span_id for e in passages} == cited
    return [e.text for e in passages if e.text]


def test_a_gamemaster_reads_each_tier_range_with_its_description(  # type: ignore[no-untyped-def]
    session, built
) -> None:
    read = _tiers_read(session, built)
    # The component reads as printed: the introduction, which says the tiers
    # carry no rules, then each range immediately before the description it
    # labels, tier 1 to 4.
    assert "These tiers don't have any rules associated with them" in read[0]
    expected = ["With each new level, characters acquire new capabilities"]
    for heading, description in TIERS:
        expected += [heading, description]
    assert len(read) == len(expected)
    assert [t.startswith(e) for t, e in zip(read, expected, strict=True)] == [
        True
    ] * len(expected)


def test_the_accepted_components_read_in_printed_order(  # type: ignore[no-untyped-def]
    session, built, prior
) -> None:
    # The ordering is shared: the ten accepted batches' records read the same way, from
    # the same release's ledger, through the loader the service uses. Read on the
    # current release with its current accepted authority: the recorded state binds the
    # superseded release's package, whose ledger the source DB does not hold
    # (``source_leaf_order`` is package-scoped; the leaf ids themselves are shared).
    # Record keys name no release.
    candidate = candidate_from_accepted_inputs(current())
    assert candidate.binding == built.binding
    every = _base_records(candidate, source_leaf_order(session, candidate))
    keys = {r.semantic_key for r in prior.oracle.representation.records}
    assert len(keys) == 92
    records = {key: every[key] for key in keys}
    spans = {s.span_id: s for s in candidate.classification.spans}
    position = {
        row.leaf_id: row.occurrence_index
        for row in session.query(LedgerLeafORM).filter(
            LedgerLeafORM.package_uuid == candidate.binding.package_uuid
        )
    }
    multi = unlike_chunks = 0
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
            chunks = [e.chunk_id for e in passages]
            unlike_chunks += chunks != sorted(chunks)
    # The current accepted authority no longer holds three of the ten's 100
    # multi-passage components; every other one reads here.
    bound = Counter(
        (b.record_key, b.component_key)
        for b in prior.oracle.representation.prose_bindings
    )
    assert sum(n > 1 for n in bound.values()) == 100
    held = {(key, c.semantic_key) for key, r in records.items() for c in r.components}
    assert {k for k, n in bound.items() if n > 1} - held == {
        ("play.exploration", "pace_effects"),
        ("play.exploration", "travel_pace"),
        ("play.proficiency", "skill_list"),
    }
    # 32 of the 97 are ones a chunk-id order misreads (chunk ids are uuid5 over
    # the release's package, so the count is its own: 32 on the current
    # ``8781d4e0-a3b``; 33 of 100 on ``3fe24ff6-4e3``, 34 on ``574662e9-0ef``,
    # 31 before it).
    assert (multi, unlike_chunks) == (97, 32)


def test_excluding_the_tier_ranges_again_passes_coverage_but_not_the_reader(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    # The defect this batch corrected: the ranges excluded as mere headings.
    # Every coverage check still passes -- only the consumer loses them.
    headings = tuple(h for h, _ in TIERS)
    for heading in headings:
        _replace_clause_text(monkeypatch, heading, None)
    monkeypatch.setattr(
        GEN,
        "EXCLUDED",
        tuple(
            (e, hs + headings if e == "level_advancement" else hs, why)
            for e, hs, why in GEN.EXCLUDED
        ),
    )
    regressed = GEN.build(session)
    found = GEN.batch_findings(regressed)
    assert found["partition"] == found["review_units"] == []
    assert _residue(regressed) == {}
    read = _tiers_read(session, regressed)
    assert not [t for t in read if "Levels" in t]


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def test_printed_pointers_without_a_destination_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    unresolved = sorted(
        (r.from_record_key.split(".")[1], r.from_component_key, r.source_text)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key == ""
    )
    assert unresolved == sorted(
        [
            ("create_your_character", "armor_class", "Equipment"),
            ("create_your_character", "armor_training", "Equipment"),
            ("create_your_character", "attacks", "Equipment"),
            ("create_your_character", "background_feat", "Feats"),
            ("create_your_character", "choose_background", "Character Origins"),
            ("create_your_character", "choose_class", "Classes"),
            ("create_your_character", "choose_species", "Character Origins"),
            ("create_your_character", "class_features", "Classes"),
            ("create_your_character", "class_proficiencies", "Classes"),
            ("create_your_character", "determine_ability_scores", "Playing the Game"),
            ("create_your_character", "starting_equipment", "Equipment"),
            ("create_your_character", "starting_proficiency_bonus", "Playing the Game"),
            ("level_advancement", "class_features", "Classes"),
            ("level_advancement", "proficiency_bonus", "Classes"),
            ("multiclassing", "proficiencies", "Classes"),
            ("starting_at_higher_levels", "starting_equipment", "Equipment"),
        ]
    )


def test_pointers_into_the_part_and_see_also_name_their_records(built) -> None:  # type: ignore[no-untyped-def]
    named = sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.target_record_key)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key
    )
    assert named == [
        (
            "character_creation.create_your_character",
            "hit_point_dice",
            "Short Rest",
            "glossary.short_rest",
        ),
        (
            "character_creation.create_your_character",
            "starting_at_a_higher_level",
            "Starting at Higher Levels",
            "character_creation.starting_at_higher_levels",
        ),
        (
            "character_creation.level_advancement",
            "choose_class",
            "Multiclassing",
            "character_creation.multiclassing",
        ),
        (
            "character_creation.multiclassing",
            "experience_points",
            "Character Advancement table",
            "character_creation.level_advancement",
        ),
        (
            "character_creation.multiclassing",
            "proficiency_bonus",
            "Character Advancement table",
            "character_creation.level_advancement",
        ),
        (
            "character_creation.starting_at_higher_levels",
            "creating_your_character",
            "Level Advancement",
            "character_creation.level_advancement",
        ),
        (
            "glossary.alignment",
            "",
            "Create Your Character",
            "character_creation.create_your_character",
        ),
        (
            "glossary.experience_points",
            "",
            "Level Advancement",
            "character_creation.level_advancement",
        ),
        ("glossary.size", "", "Breaking Objects", "glossary.breaking_objects"),
        ("glossary.size", "", "Combat", "play.combat"),
    ]
    # Mentions stay unreferenced; so does the broad part name Alignment's and
    # Multiclassing's pointers print before their precise destinations.
    texts = {r.source_text for r in built.proposal.proposed_representation.references}
    assert not texts & {
        "Character Creation",
        "Death Saving Throws",
        "Hit Point Dice",
        "Temporary Hit Points",
        "Playing the Game (Combat)",
    }


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
    assert len(excluded) == 11 + sum(len(h) for _, h, _ in GEN.EXCLUDED) == 43
    # Starting with "#" is not enough: no excluded heading carries a level
    # range, or any other number the body does not restate.
    assert [e for e in excluded if any(ch.isdigit() for ch in e)] == [
        "### Step 1: Choose Class",
        "### Step 2: Character Origin",
        "### Step 3: Ability Scores",
        "### Step 4: Alignment",
        "### Step 5: Character Creation Details",
    ]
    assert not {h for h, _ in TIERS} & set(excluded)
    # The five step numbers are restated where the steps are listed.
    (steps,) = _texts(
        built, "character_creation.create_your_character", "creation_steps"
    )
    assert [n for n in range(1, 6) if f"{n}. **" in steps] == [1, 2, 3, 4, 5]


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


def test_a_dropped_example_sharing_a_leaf_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    example = "For example, a score of 14 costs 7 of your 27 points."
    _drop_supporting(monkeypatch, example)
    assert list(_residue(GEN.build(session)).values()) == [example]


def test_a_dropped_whole_leaf_example_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    (example,) = [
        t
        for _, t, _ in GEN.SUPPORTING
        if t.startswith("For example, if you are a level 4 Ranger")
    ]
    _drop_supporting(monkeypatch, example)
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit character-creation-foundations/multiclassing")
    assert found.endswith(
        "named by no expected rule, supporting group or excluded group"
    )


def test_a_dropped_rare_languages_footnote_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _replace_clause_text(monkeypatch, GEN.RARE_LANGUAGES_FOOTNOTE, None)
    assert list(_residue(GEN.build(session)).values()) == [GEN.RARE_LANGUAGES_FOOTNOTE]


@pytest.mark.parametrize(
    ("table", "entry"),
    [
        ("MULTICLASS_SPELLCASTER_TABLE", "multiclassing"),
        ("TRINKETS_TABLE", "trinkets"),
        ("CHARACTER_ADVANCEMENT_TABLE", "level_advancement"),
        ("CREATURE_TYPE_TABLE", "creature_type"),
    ],
)
def test_a_dropped_table_is_reported(session, monkeypatch, table, entry) -> None:  # type: ignore[no-untyped-def]
    _replace_clause_text(monkeypatch, getattr(GEN, table), None)
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(
        f"review unit character-creation-foundations/{entry}: leaf "
    )


@pytest.mark.parametrize(
    ("table", "row"),
    [
        (
            "MULTICLASS_SPELLCASTER_TABLE",
            "".join(f"\n      <td>{c}</td>" for c in (9, 4, 3, 3, 3, 1)),
        ),
        (
            "TRINKETS_TABLE",
            "\n      <td>01</td>\n      <td>A mummified goblin hand</td>",
        ),
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
            if (c.entry, c.key) != ("multiclassing", "pact_magic")
        ),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit character-creation-foundations/multiclassing: expected rule "
        "character_creation.multiclassing/pact_magic has no component"
    ) in found


# ---------------------------------------------------------------------------
# Test-only composition with the committed ten-batch acceptance
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
        validate_acceptance(
            candidate_from_accepted_inputs(lifted(inputs)).classification
        )
    )


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


def test_composed_the_five_targets_close_and_179_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    assert len(prior.oracle.representation.records) == 92
    assert len(prior.oracle.spans) == 692
    assert len(prior.batches) == 10
    assert len(prior.oracle.reference_resolutions) == 1
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert len(recorded.proposed_spans) == 152
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }

    together = _composed(prior, recorded)
    assert sorted(_references(prior)) == sorted(CLOSED + ACCEPTED_UNRESOLVED)
    # Unfiltered and representation-only: nothing else is reported.
    assert sorted(_references(together)) == sorted(ACCEPTED_UNRESOLVED + NEW)
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(prior) == []
    assert _acceptance(together) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(together) - _covered(prior) == mine
    assert len(mine) == 179


def test_the_recorded_resolution_still_applies_composed(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    (resolution,) = prior.oracle.reference_resolutions
    assert resolution.resolution_id == "resolve-attack-roll-playing-the-game-1"
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
    assert ("play.combat", "attack_structure", "play.d20_tests") in {
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in effective.references
    }


# ---------------------------------------------------------------------------
# The two unrecorded "Character Creation" resolution drafts
# ---------------------------------------------------------------------------

DRAFTS = ("draft_armor_class_resolution", "draft_proficiency_bonus_resolution")


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


def test_once_accepted_both_drafts_resolve_through_the_native_seam(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # In memory only: nothing is written and no decision is recorded. The
    # recorded proposal over its recorded prior: both the superseded release's.
    oracle = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracle.glob("*.json")}
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="character-creation-foundations",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-23T00:00:00Z",
        prior=prior,
    )
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
        "resolve-attack-roll-playing-the-game-1",
        GEN.ARMOR_CLASS_RESOLUTION_ID,
        GEN.PROFICIENCY_BONUS_RESOLUTION_ID,
    ]
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    targets = {
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in effective.references
        if (r.source_text, r.scope_key) == ("Character Creation", CC)
    }
    assert targets == {
        ("play.d20_tests", "armor_class", "character_creation.create_your_character"),
        (
            "play.proficiency",
            "proficiency_bonus",
            "character_creation.level_advancement",
        ),
    }
    # The accepted citations themselves are not edited, and nothing is written.
    assert resolved.oracle.representation == accepted.oracle.representation
    assert {p.name: p.read_bytes() for p in oracle.glob("*.json")} == on_disk
