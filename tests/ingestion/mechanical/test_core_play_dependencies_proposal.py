"""The ``core-play-dependencies`` proposal, as it is offered for review — CRD Issue 5d.

The eleven Rules Glossary entries the accepted core play cites and no accepted
record defines -- Attack Roll, Stat Block, Carrying Capacity, the four special
senses and the four hazards -- proposed by
``.claude/review-notes/issue-5d-core-play-dependencies-generator.py`` from the
release 5c actually publishes. Nothing here accepts it or records a resolution;
the Owner's acceptance is recorded by
the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_core_play_dependencies_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings read back from the proposal: Truesight's range
  governs all five benefits, Suffocation removes only the Exhaustion it caused,
  each recurring effect keeps its cadence, the consumption bands and the save
  failure keep their scope, and a GameMaster reads each typed effect with the
  condition that governs it;
* every word of every spanned leaf is claimed, only headings are excluded, and
  a dropped clause, table, example or component is reported;
* composed *in this test only* with the nine-batch acceptance it was offered
  against, re-derived by its script since the committed artifact now also
  holds this batch, the eleven targets close, only the new unknowns and
  pointers are added, and exactly the batch's 52 leaves gain coverage. Both
  sides are the superseded release's; its physical source is not available, so
  the composition is checked without a corpus: its uncovered-leaf counts are
  retired, while native acceptance, which needs none, still reports exactly
  each proposed span's missing approval and none for the accepted prior
  (``correction-followup.md``);
* **the boundary, as the Owner decided it**: the two Stat Block "Playing the
  Game" pointers share wording and scope with the accepted attack-roll citation
  the recorded resolution resolves, but a citation is identified by where it
  occurs as well as what it says, so composed that resolution still applies and
  both pointers stay unresolved. Nothing here accepts or resolves anything.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import validate_acceptance
from afterworlds.ingestion.mechanical.authoring import Built, EntryComponent
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
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ConditionKind,
    ConditionLevelFact,
    LevelDirection,
    RecurrenceBoundary,
    RollActor,
    fact_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
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
GENERATOR = NOTES / "issue-5d-core-play-dependencies-generator.py"
BATCH = "core-play-dependencies"
PROPOSAL = proposal_path(BATCH)
#: The nine-batch acceptance this proposal was offered against, as committed
#: in ``9ca37e9``.
IDENTITY = identity(BATCH)

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
EQUIPMENT, TOOLBOX = "srd-5.2.1/equipment", "srd-5.2.1/gameplay-toolbox"
MONSTERS = "srd-5.2.1/monsters"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the committed acceptance leaves undefined: the eleven targets closed here.
CLOSED = sorted(
    _glossary(text, slug)
    for text, slug in [
        ("Attack Roll", "attack_roll"),
        ("Blindsight", "blindsight"),
        ("Burning", "burning"),
        ("Darkvision", "darkvision"),
        ("Dehydration", "dehydration"),
        ("Malnutrition", "malnutrition"),
        ("Stat Block", "stat_block"),
        ("Suffocation", "suffocation"),
        ("Tremorsense", "tremorsense"),
        ("Truesight", "truesight"),
        ("carrying capacity", "carrying_capacity"),
    ]
)
#: The accepted pointers into parts with no record; each stays unresolved.
ACCEPTED_UNRESOLVED = sorted(
    [_unresolved("srd-5.2.1/character-creation", "Character Creation")] * 2
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(TOOLBOX, "Combat Encounters")]
    + [_unresolved(TOOLBOX, "Gameplay Toolbox")]
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
)
#: What this batch adds that nothing accepted or proposed defines.
NEW = sorted(
    [_unresolved(MONSTERS, "Monsters")]
    + [_unresolved(PLAY, "Playing the Game")] * 2
    + [
        _glossary("Alignment", "alignment"),
        _glossary("Creature Type", "creature_type"),
        _glossary("Experience Points", "experience_points"),
        _glossary("Passive Perception", "passive_perception"),
        _glossary("Size", "size"),
    ]
)
#: The recorded resolution's citation: it shares its wording and scope with the
#: two new Stat Block pointers, and is a different citation from either.
COMBAT_CITATION = ("play.combat", "attack_structure", "Playing the Game", PLAY)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("core_play_dependencies", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _generator()


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
    """The nine-batch acceptance, attack-roll resolution included.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("core-play-completion")
    return inputs


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (record, key)
    ]
    return c


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


def test_scope_is_eleven_whole_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, len(u.leaf_ids)) for u in units] == [
        ("core-play-dependencies/attack_roll", 2),
        ("core-play-dependencies/blindsight", 2),
        ("core-play-dependencies/burning", 2),
        ("core-play-dependencies/carrying_capacity", 4),
        ("core-play-dependencies/darkvision", 2),
        ("core-play-dependencies/dehydration", 3),
        ("core-play-dependencies/malnutrition", 4),
        ("core-play-dependencies/stat_block", 21),
        ("core-play-dependencies/suffocation", 2),
        ("core-play-dependencies/tremorsense", 3),
        ("core-play-dependencies/truesight", 7),
    ]
    assert {u.kind for u in units} == {ReviewUnitKind.ENTRY}
    assert [r.semantic_key for r in built.proposal.proposed_representation.records] == [
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    ]
    # Printed order: the rendered records follow the pages.
    pages = [
        min(built.leaf_rows[leaf].printed_page for leaf in u.leaf_ids) for u in units
    ]
    assert pages == sorted(pages)


def test_no_leaf_is_owned_by_an_accepted_unit(built, prior) -> None:  # type: ignore[no-untyped-def]
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & {leaf for ids in built.entry_leaves.values() for leaf in ids}


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    own = {f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES}
    assert not [f for f in found["representation"] if f.split()[-1] in own]


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_truesight_range_governs_every_benefit(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "glossary.truesight", "truesight")
    # No typed fact: an unranged automatic success on saving throws against
    # illusions would be broader than the source.
    assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    # One clause group: the lead cannot be split from a benefit.
    (texts,) = [ts for e, _, _, ts in GEN.CLAUSES if e == "truesight"]
    assert texts == (GEN.TRUESIGHT_LEAD, *GEN.TRUESIGHT_BENEFITS)
    bound = {
        b.span_id
        for b in built.proposal.proposed_representation.prose_bindings
        if (b.record_key, b.component_key) == ("glossary.truesight", "truesight")
    }
    assert bound == {built.spans[("truesight", t)].span_id for t in texts}


def test_suffocation_removes_only_the_exhaustion_it_caused(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "glossary.suffocation", "suffocation_recovery")
    assert c.facts == (
        ConditionLevelFact(
            ConditionKind.EXHAUSTION,
            LevelDirection.REMOVE,
            all_levels=True,
            cause_scoped=True,
        ),
    )
    # "can breathe again" stays the component's governing prose.
    assert c.handling is ComponentHandling.MIXED
    assert c.recurs is None


def test_each_recurring_effect_keeps_its_cadence(built) -> None:  # type: ignore[no-untyped-def]
    cadence = {
        (c.record_key, c.semantic_key): (
            c.recurs and (c.recurs.boundary, c.recurs.whose)
        )
        for c in built.proposal.proposed_representation.components
        if c.recurs is not None
    }
    assert cadence == {
        ("glossary.burning", "burning_damage"): (
            RecurrenceBoundary.START_OF_TURN,
            RollActor.SUBJECT,
        ),
        ("glossary.dehydration", "dehydration_exhaustion"): (
            RecurrenceBoundary.END_OF_DAY,
            None,
        ),
        ("glossary.malnutrition", "starvation_save"): (
            RecurrenceBoundary.END_OF_DAY,
            None,
        ),
        ("glossary.malnutrition", "starvation_automatic"): (
            RecurrenceBoundary.END_OF_DAY,
            None,
        ),
        ("glossary.suffocation", "suffocation_accrual"): (
            RecurrenceBoundary.END_OF_TURN,
            RollActor.SUBJECT,
        ),
    }


def test_the_consumption_bands_keep_their_scope(built) -> None:  # type: ignore[no-untyped-def]
    dehydration = _component(built, "glossary.dehydration", "dehydration_exhaustion")
    assert dehydration.applies_when == GEN.DEHYDRATION_BAND
    partial = _component(built, "glossary.malnutrition", "starvation_save")
    zero = _component(built, "glossary.malnutrition", "starvation_automatic")
    assert partial.applies_when == GEN.STARVATION_PARTIAL_BAND
    assert zero.applies_when == GEN.STARVATION_ZERO_BAND
    # "eats but consumes less than half" excludes eating nothing, which the
    # automatic rule owns: the two bands do not overlap at zero.
    p, z = partial.applies_when.band, zero.applies_when.band
    assert p.lower == z.upper and not p.lower_inclusive and z.upper_inclusive
    assert (z.sustained_at_least, p.sustained_at_least) == (5, None)
    # The recovery restriction is not gated by the accrual's band.
    for record, key in [
        ("glossary.dehydration", "dehydration_recovery"),
        ("glossary.malnutrition", "malnutrition_recovery"),
    ]:
        c = _component(built, record, key)
        assert c.applies_when is None and c.recurs is None
        (fact,) = c.facts
        assert fact.until.band.lower_inclusive and fact.until.band.upper is None


def test_only_the_exhaustion_waits_on_the_failed_save(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "glossary.malnutrition", "starvation_save")
    save, gain = c.facts
    (qualifier,) = c.fact_qualifiers
    assert qualifier.applies_when == GEN.FAILED
    assert gain == GEN.GAIN_1
    assert qualifier.fact_key == fact_key(gain) != fact_key(save)


def test_restatements_and_unmodelled_arithmetic_stay_untyped(built) -> None:  # type: ignore[no-untyped-def]
    # Attack Roll restates play.d20_tests; the carrying-capacity multiplier and
    # speed ceiling, the senses and the stat-block format have no family.
    typed = [
        (c.record_key, c.semantic_key)
        for c in built.proposal.proposed_representation.components
        if c.facts
    ]
    assert typed == [
        ("glossary.burning", "burning_damage"),
        ("glossary.burning", "self_extinguish"),
        ("glossary.burning", "ambient_extinguish"),
        ("glossary.dehydration", "water_requirement"),
        ("glossary.dehydration", "dehydration_exhaustion"),
        ("glossary.dehydration", "dehydration_recovery"),
        ("glossary.malnutrition", "food_requirement"),
        ("glossary.malnutrition", "starvation_save"),
        ("glossary.malnutrition", "starvation_automatic"),
        ("glossary.malnutrition", "malnutrition_recovery"),
        ("glossary.suffocation", "breath_duration"),
        ("glossary.suffocation", "suffocation_accrual"),
        ("glossary.suffocation", "suffocation_recovery"),
    ]


# ---------------------------------------------------------------------------
# What a GameMaster reads: each effect with the condition governing it
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
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "core-play-dependencies"),
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


def _read(component: GameMasterComponent) -> str:
    texts = [e.text for e in component.governing_prose if isinstance(e, SourceProse)]
    assert texts and None not in texts
    return " ".join(t for t in texts if t is not None)


def test_each_typed_effect_is_read_with_its_condition(session, built) -> None:  # type: ignore[no-untyped-def]
    view = _gamemaster(session, built)
    assert len(view) == 41
    truesight = _read(view[("glossary.truesight", "truesight")])
    assert "Within that range, your vision pierces through the following:" in truesight
    for benefit in GEN.TRUESIGHT_BENEFITS:
        assert benefit in truesight
    accrual = view[("glossary.suffocation", "suffocation_accrual")]
    assert "runs out of breath or is choking" in _read(accrual)
    assert accrual.recurs == GEN.END_OF_OWN_TURN
    assert "it gained from suffocating" in _read(
        view[("glossary.suffocation", "suffocation_recovery")]
    )
    assert "on yourself" in _read(view[("glossary.burning", "self_extinguish")])
    burn = view[("glossary.burning", "burning_damage")]
    assert burn.recurs == GEN.START_OF_OWN_TURN and burn.governing_prose == ()
    save = view[("glossary.malnutrition", "starvation_save")]
    assert save.applies_when == GEN.STARVATION_PARTIAL_BAND
    assert save.recurs == GEN.END_OF_DAY
    assert [
        (f.fact, f.qualifier.applies_when)
        for f in save.structured_context
        if f.qualifier is not None
    ] == [(GEN.GAIN_1, GEN.FAILED)]
    assert view[("glossary.dehydration", "dehydration_exhaustion")].applies_when == (
        GEN.DEHYDRATION_BAND
    )
    speed = _read(view[("glossary.carrying_capacity", "dragging_lifting_pushing")])
    assert "can be no more than 5 feet" in speed


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def test_printed_pointers_without_a_destination_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    unresolved = sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key == ""
    )
    assert unresolved == [
        ("glossary.stat_block", "ability_scores", "Playing the Game", PLAY),
        ("glossary.stat_block", "ac_initiative_hp", "Playing the Game", PLAY),
        ("glossary.stat_block", "challenge_rating", "Monsters", MONSTERS),
    ]


def test_every_see_also_pointer_is_cited_from_its_span(built) -> None:  # type: ignore[no-untyped-def]
    refs = {
        (r.from_record_key, r.source_text): (r.scope_key, r.target_record_key)
        for r in built.proposal.proposed_representation.references
    }
    for entry, text, target, _ in GEN.RECORD_REFERENCES:
        scope, key = (
            (GLOSSARY, f"glossary.{target}") if isinstance(target, str) else target
        )
        assert refs[(f"glossary.{entry}", text)] == (scope, key)
    # Mentions stay unreferenced.
    texts = {t for _, t in refs}
    assert not texts & {"Total Cover", "Darkness", "Dim Light", "Ethereal Plane"}


# ---------------------------------------------------------------------------
# Headings and omission checks
# ---------------------------------------------------------------------------


def test_only_the_entry_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    excluded = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert sorted(excluded) == sorted(f"#### {label}" for _, label, _ in GEN.ENTRIES)


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


def test_a_dropped_example_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "SUPPORTING",
        tuple(s for s in GEN.SUPPORTING if s[1] != GEN.DAMAGE_NOTATION_EXAMPLE),
    )
    assert list(_residue(GEN.build(session)).values()) == [GEN.DAMAGE_NOTATION_EXAMPLE]


def _drop_clause_text(monkeypatch, text: str) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if t != text)) for e, k, f, ts in GEN.CLAUSES
        ),
    )


def test_a_dropped_truesight_benefit_leaves_its_leaf_unaccounted(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    _drop_clause_text(monkeypatch, GEN.TRUESIGHT_BENEFITS[2])
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit core-play-dependencies/truesight: leaf ")


@pytest.mark.parametrize(
    ("table", "entry"),
    [
        ("CARRYING_CAPACITY_TABLE", "carrying_capacity"),
        ("WATER_TABLE", "dehydration"),
        ("FOOD_TABLE", "malnutrition"),
    ],
)
def test_a_dropped_table_is_reported(session, monkeypatch, table, entry) -> None:  # type: ignore[no-untyped-def]
    _drop_clause_text(monkeypatch, getattr(GEN, table))
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(f"review unit core-play-dependencies/{entry}: leaf ")


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(c for c in GEN.COMPONENTS if c.key != "suffocation_recovery"),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit core-play-dependencies/suffocation: expected rule "
        "glossary.suffocation/suffocation_recovery has no component"
    ) in found


def test_entry_component_states_no_cadence_by_default() -> None:
    # The shared helper's one change: ``recurs`` passes through, and a batch
    # that never names it (every earlier generator) emits what it always did.
    assert EntryComponent("e", "k", ComponentHandling.PROSE_BOUND, None).recurs is None


# ---------------------------------------------------------------------------
# Test-only composition with the committed nine-batch acceptance
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


def test_composed_the_eleven_targets_close_and_52_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    assert len(prior.oracle.representation.records) == 81
    assert len(prior.oracle.spans) == 626
    assert len(prior.batches) == 9
    assert len(prior.oracle.reference_resolutions) == 1
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert len(recorded.proposed_spans) == 66
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }

    together = _composed(prior, recorded)
    assert sorted(_references(prior)) == sorted(CLOSED + ACCEPTED_UNRESOLVED)
    # Only the new findings: citation identity leaves no false ambiguity.
    # Unfiltered and representation-only: nothing else is reported.
    assert sorted(_references(together)) == sorted(ACCEPTED_UNRESOLVED + NEW)
    assert len(ACCEPTED_UNRESOLVED + NEW) == 20
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(prior) == []
    assert _acceptance(together) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(together) - _covered(prior) == mine
    assert len(mine) == 52


def test_the_recorded_resolution_still_applies_beside_the_stat_block_pointers(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # Before the Owner's citation-identity decision the two Stat Block "Playing
    # the Game" pointers shared the (scope, wording) key ambiguity was judged by,
    # and composed they made this resolution inapplicable. Now each citation is
    # its own: the resolution applies, and this batch drafts no resolution.
    (resolution,) = prior.oracle.reference_resolutions
    assert (
        resolution.resolution_id,
        resolution.from_record_key,
        resolution.from_component_key,
        resolution.source_text,
        resolution.target_record_key,
    ) == (
        "resolve-attack-roll-playing-the-game-1",
        "play.combat",
        "attack_structure",
        "Playing the Game",
        "play.d20_tests",
    )
    resolutions, binding = prior.oracle.reference_resolutions, prior.oracle.binding
    assert (
        reference_resolution_violations(
            prior.oracle.representation, resolutions, binding
        )
        == []
    )
    composed = _composed(prior, recorded)
    assert (
        reference_resolution_violations(
            composed.oracle.representation, resolutions, binding
        )
        == []
    )
    # The loader's effective view: the combat citation resolves, and the two
    # Stat Block pointers of the same wording stay honest obligations.
    effective = candidate_from_accepted_inputs(composed).representation
    targets = sorted(
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in effective.references
        if (r.source_text, r.scope_key) == ("Playing the Game", PLAY)
    )
    assert targets == [
        ("glossary.stat_block", "ability_scores", ""),
        ("glossary.stat_block", "ac_initiative_hp", ""),
        (COMBAT_CITATION[0], COMBAT_CITATION[1], "play.d20_tests"),
    ]
    assert not hasattr(GEN, "draft_resolution")


def test_no_accepted_empty_target_reference_points_into_this_batch(prior) -> None:  # type: ignore[no-untyped-def]
    empty = sorted(
        (r.scope_key, r.source_text)
        for r in prior.oracle.representation.references
        if r.target_record_key == ""
    )
    assert empty == sorted(
        [("srd-5.2.1/character-creation", "Character Creation")] * 2
        + [(EQUIPMENT, "Equipment")] * 5
        + [(TOOLBOX, "Combat Encounters"), (TOOLBOX, "Gameplay Toolbox")]
        + [(PLAY, "Playing the Game"), (GLOSSARY, "Rules Glossary")]
        + [("srd-5.2.1/spells", "Spells")] * 2
    )
