"""The ``core-play-completion`` proposal, as it is offered for review — CRD Issue 5d.

The four remaining *Playing the Game* sections -- Rhythm of Play, The Six
Abilities (with its two sidebars), Social Interaction and Exploration (less the
accepted Breaking Objects) -- plus the Rules Glossary's Armor Class, Challenge
Rating and Expertise entries, proposed by
``.claude/review-notes/issue-5d-core-play-completion-generator.py`` from the
release 5c actually publishes. Nothing here accepts it or records a resolution;
the Owner's acceptance is recorded by
the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_core_play_completion_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* Exploration leaves out exactly the leaves the accepted Breaking Objects
  record owns, and without that it would not build;
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings (the obscured areas, each travel pace as one
  option, restatements kept untyped) read back from the proposal, and a
  GameMaster reads each typed effect with the condition that governs it;
* every word of every spanned leaf is claimed, and only headings are excluded;
* composed *in this test only* with the eight-batch acceptance (and its
  attack-roll resolution) it was offered against, re-derived by its script
  since the committed artifact now also holds this batch, the three
  outstanding targets close, the seven
  accepted pointers with no destination stay unresolved, only the new unknowns
  and new pointers are added, and exactly the batch's 85 leaves gain coverage.
  Both sides are the superseded release's; its physical source is not
  available, so the composition is checked without a corpus: its uncovered-leaf
  counts are retired, while native acceptance, which needs none, still reports
  exactly each proposed span's missing approval and none for the accepted prior
  (``correction-followup.md``);
* no accepted empty-target reference points into this batch, so none is
  drafted for resolution.
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
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.bound_corpus import leaves_under
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
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ProvenanceTargetKind,
    RollActor,
    RollContext,
    RollSpec,
    Skill,
    fact_target_key,
    reference_target_key,
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
GENERATOR = NOTES / "issue-5d-core-play-completion-generator.py"
BATCH = "core-play-completion"
PROPOSAL = proposal_path(BATCH)
#: The eight-batch acceptance this proposal was offered against, as committed
#: in ``3160aa9``.
IDENTITY = identity(BATCH)

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
EQUIPMENT, TOOLBOX = "srd-5.2.1/equipment", "srd-5.2.1/gameplay-toolbox"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the committed acceptance leaves undefined: the three targets closed here.
CLOSED = sorted(
    [
        _glossary("Armor Class", "armor_class"),
        _glossary("Challenge Rating", "challenge_rating"),
        _glossary("Expertise", "expertise"),
    ]
)
#: The accepted pointers into parts with no record; each stays unresolved.
ACCEPTED_UNRESOLVED = sorted(
    [_unresolved("srd-5.2.1/character-creation", "Character Creation")] * 2
    + [_unresolved(EQUIPMENT, "Equipment")] * 2
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
)
#: What this batch adds that nothing accepted or proposed defines.
NEW = sorted(
    [_unresolved(EQUIPMENT, "Equipment")] * 3
    + [
        _unresolved(TOOLBOX, "Combat Encounters"),
        _unresolved(TOOLBOX, "Gameplay Toolbox"),
        _glossary("Attack Roll", "attack_roll"),
        _glossary("Blindsight", "blindsight"),
        _glossary("Burning", "burning"),
        _glossary("Darkvision", "darkvision"),
        _glossary("Dehydration", "dehydration"),
        _glossary("Malnutrition", "malnutrition"),
        _glossary("Stat Block", "stat_block"),
        _glossary("Suffocation", "suffocation"),
        _glossary("Tremorsense", "tremorsense"),
        _glossary("Truesight", "truesight"),
        _glossary("carrying capacity", "carrying_capacity"),
    ]
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("core_play_completion", GENERATOR)
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
    """The eight-batch acceptance, attack-roll resolution included.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("checks-actions-rests")
    return inputs


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (record, key)
    ]
    return c


def _check(state: AdvantageState, ability: AbilityScore, skill: Skill) -> AdvantageFact:
    return AdvantageFact(
        state, RollSpec(RollActor.SUBJECT, RollContext.ABILITY_CHECK, ability, skill)
    )


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


def test_scope_is_four_whole_sections_and_three_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, len(u.leaf_ids)) for u in units] == [
        ("core-play-completion/rhythm_of_play", 6),
        ("core-play-completion/six_abilities", 11),
        ("core-play-completion/social_interaction", 13),
        ("core-play-completion/exploration", 46),
        ("core-play-completion/armor_class", 3),
        ("core-play-completion/challenge_rating", 2),
        ("core-play-completion/expertise", 4),
    ]
    assert [u.kind for u in units] == [ReviewUnitKind.SECTION] * 4 + [
        ReviewUnitKind.ENTRY
    ] * 3
    assert [r.semantic_key for r in built.proposal.proposed_representation.records] == [
        "play.rhythm_of_play",
        "play.six_abilities",
        "play.social_interaction",
        "play.exploration",
        "glossary.armor_class",
        "glossary.challenge_rating",
        "glossary.expertise",
    ]


def test_exploration_leaves_out_exactly_the_accepted_breaking_objects(  # type: ignore[no-untyped-def]
    session, built, prior
) -> None:
    (breaking,) = [
        u
        for u in prior.oracle.review_units
        if u.unit_id == "combat-damage-breaking/exploration_breaking_objects"
    ]
    whole = leaves_under(
        session,
        built.binding.package_uuid,
        built.binding.release_version,
        ("Playing the Game", "Exploration"),
    )
    assert len(whole) == 49
    assert set(whole) - set(built.entry_leaves["exploration"]) == set(breaking.leaf_ids)
    assert len(breaking.leaf_ids) == 3
    # No leaf of this batch is owned by any accepted unit.
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & {leaf for ids in built.entry_leaves.values() for leaf in ids}
    # The chapter title sits outside every section and stays unowned.
    assert "# Playing the Game" not in {
        built.leaf_rows[leaf].content
        for ids in built.entry_leaves.values()
        for leaf in ids
    }


def test_without_the_omission_exploration_would_re_own_breaking_objects(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    placements = dict(GEN.PLACEMENTS)
    placements["exploration"] = dataclasses.replace(placements["exploration"], omit=())
    monkeypatch.setattr(GEN, "PLACEMENTS", placements)
    with pytest.raises(
        ValueError,
        match=r"^88 leaves \(88 distinct\) under the entries; the review read 85$",
    ):
        GEN.build(session)


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    # In-batch pointers resolve: nothing names this batch's own records.
    assert not [
        f
        for f in found["representation"]
        if f.endswith(
            (
                "glossary.armor_class",
                "glossary.challenge_rating",
                "glossary.expertise",
                "play.exploration",
            )
        )
    ]


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_the_obscured_areas(built) -> None:  # type: ignore[no-untyped-def]
    light = _component(built, "play.exploration", "lightly_obscured")
    assert light.handling is ComponentHandling.MIXED
    assert light.facts == (
        _check(AdvantageState.DISADVANTAGE, AbilityScore.WISDOM, Skill.PERCEPTION),
    )
    heavy = _component(built, "play.exploration", "heavily_obscured")
    assert heavy.facts == (
        ConditionEffectFact(ConditionKind.BLINDED, ConditionEffectKind.APPLIES),
    )
    # "when trying to see something there" is the seen area, not the
    # subject's own obscurement: no Applicability states it.
    assert heavy.applies_when is None


def test_each_travel_pace_is_one_option(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "play.exploration", "pace_effects")
    assert c.handling is ComponentHandling.MIXED and c.facts == ()
    dis, adv = AdvantageState.DISADVANTAGE, AdvantageState.ADVANTAGE
    wis, dex = AbilityScore.WISDOM, AbilityScore.DEXTERITY
    assert {o.semantic_key: o.facts for o in c.options} == {
        "fast": (
            _check(dis, wis, Skill.PERCEPTION),
            _check(dis, wis, Skill.SURVIVAL),
            _check(dis, dex, Skill.STEALTH),
        ),
        "normal": (_check(dis, dex, Skill.STEALTH),),
        "slow": (_check(adv, wis, Skill.PERCEPTION), _check(adv, wis, Skill.SURVIVAL)),
    }


def test_each_pace_option_cites_the_lead_and_its_own_paragraph(built) -> None:  # type: ignore[no-untyped-def]
    representation = built.proposal.proposed_representation
    c = _component(built, "play.exploration", "pace_effects")
    own = {"fast": GEN.FAST_PACE, "normal": GEN.NORMAL_PACE, "slow": GEN.SLOW_PACE}
    for option in c.options:
        for fact in option.facts:
            cited = {
                p.span_id
                for p in representation.provenance
                if p.target_kind is ProvenanceTargetKind.FACT
                and p.target_key
                == fact_target_key(
                    "play.exploration", "pace_effects", fact, option.semantic_key
                )
            }
            assert cited == {
                built.spans[("exploration", t)].span_id
                for t in (GEN.PACE_LEAD, own[option.semantic_key])
            }


def test_restatements_and_unmodelled_arithmetic_stay_untyped(built) -> None:  # type: ignore[no-untyped-def]
    # One typed copy per rule, and no family stretched to fit: the base AC
    # (play.d20_tests), the free interaction (play.combat), the attitudes (their
    # glossary entries), the modifier derivation, rounding, the Expertise
    # doubling, travel distances.
    for record, key in [
        ("glossary.armor_class", "base_ac"),
        ("play.exploration", "time_limited_interactions"),
        ("play.social_interaction", "attitudes"),
        ("play.six_abilities", "ability_modifiers"),
        ("play.six_abilities", "round_down"),
        ("glossary.expertise", "expertise"),
        ("play.exploration", "travel_pace"),
    ]:
        c = _component(built, record, key)
        assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    facts = [c for c in built.proposal.proposed_representation.components if c.facts]
    assert [(c.record_key, c.semantic_key) for c in facts] == [
        ("play.exploration", "lightly_obscured"),
        ("play.exploration", "heavily_obscured"),
    ]


def test_the_six_abilities_sidebars_are_authored_whole(built) -> None:  # type: ignore[no-untyped-def]
    # The release places both in The Six Abilities; their meaning is kept.
    for key in ("exceptions_supersede", "round_down"):
        (texts,) = [ts for _, k, _, ts in GEN.CLAUSES if k == key]
        bound = {
            b.span_id
            for b in built.proposal.proposed_representation.prose_bindings
            if b.component_key == key
        }
        assert bound == {built.spans[("six_abilities", t)].span_id for t in texts}


# ---------------------------------------------------------------------------
# What a GameMaster reads: each effect with the condition governing it
# ---------------------------------------------------------------------------


def _gamemaster(
    session: Session, built: Built
) -> dict[tuple[str, str], GameMasterComponent]:
    """The batch as the production GameMaster view presents it.

    The view resolves each component's *own* governing prose only; it infers no
    scope from a sibling, so an effect read apart from its condition would read
    as unconditional.
    """
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
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "core-play-completion"),
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
    assert len(view) == 36
    light = view[("play.exploration", "lightly_obscured")]
    assert "that rely on sight" in _read(light)
    assert [f.fact for f in light.structured_context] == list(
        _component(built, "play.exploration", "lightly_obscured").facts
    )
    heavy = view[("play.exploration", "heavily_obscured")]
    assert "when trying to see something there" in _read(heavy)
    assert heavy.applies_when is None
    paces = view[("play.exploration", "pace_effects")]
    assert paces.structured_context == ()
    options = _component(built, "play.exploration", "pace_effects").options
    assert [
        (o.semantic_key, tuple(f.fact for f in o.facts)) for o in paces.options
    ] == [(o.semantic_key, o.facts) for o in options]
    read = _read(paces)
    for text in (GEN.PACE_LEAD, GEN.FAST_PACE, GEN.NORMAL_PACE, GEN.SLOW_PACE):
        assert text in read


def test_each_list_is_read_with_the_lead_that_scopes_it(session, built) -> None:  # type: ignore[no-untyped-def]
    view = _gamemaster(session, built)
    for key, lead, item in [
        ("special_senses", "defines the following special senses:", "- Truesight"),
        ("hazards", "defines the following hazards:", "- Suffocation"),
        ("light", "as defined below.", "**Darkness.**"),
    ]:
        read = _read(view[("play.exploration", key)])
        assert lead in read and item in read, key
    rhythm = _read(view[("play.rhythm_of_play", "basic_pattern")])
    assert "according to this basic pattern:" in rhythm
    assert "**3: The GM Narrates the Results" in rhythm


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
        ("glossary.challenge_rating", "", "Combat Encounters", TOOLBOX),
        ("play.exploration", "travel_pace", "Equipment", EQUIPMENT),
        ("play.exploration", "travel_pace", "Gameplay Toolbox", TOOLBOX),
        ("play.exploration", "vehicles", "Equipment", EQUIPMENT),
        ("play.exploration", "weapons_beyond_battle", "Equipment", EQUIPMENT),
    ]


def test_a_record_pointer_cites_the_reference_already_stated(built) -> None:  # type: ignore[no-untyped-def]
    # The shared fold: the record's "See "Equipment"" and Travel's "see ...
    # "Combat"" pointers add no record-owned duplicate; their spans cite the
    # component reference the record already states with that text and target.
    representation = built.proposal.proposed_representation
    for component, text, pointer in [
        ("weapons_beyond_battle", "Equipment", GEN.EQUIPMENT_POINTER),
        ("time_limited_interactions", "Combat", GEN.TRAVEL_COMBAT_POINTER),
    ]:
        (ref,) = [
            r
            for r in representation.references
            if (r.from_record_key, r.from_component_key, r.source_text)
            == ("play.exploration", component, text)
        ]
        cited = {
            p.span_id
            for p in representation.provenance
            if p.target_kind is ProvenanceTargetKind.REFERENCE
            and p.target_key == reference_target_key(ref)
        }
        assert built.spans[("exploration", pointer)].span_id in cited
        assert len(cited) == 2


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------


def _excluded(built) -> list[str]:  # type: ignore[no-untyped-def]
    return [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]


def test_only_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    # 19 subsection headings plus the seven record headings.
    excluded = _excluded(built)
    assert len(excluded) == len(set(excluded)) == 26
    assert all(c.startswith("#") and "\n" not in c for c in excluded)
    assert "#### Breaking Objects" not in excluded


def test_an_excluded_heading_must_match_exactly(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "EXCLUDED",
        tuple(
            (e, tuple(c.replace("#### Vehicles", "#### Vehicle") for c in cs), r)
            for e, cs, r in GEN.EXCLUDED
        ),
    )
    with pytest.raises(ValueError, match="matches 0 leaves"):
        GEN.build(session)


# ---------------------------------------------------------------------------
# Omission checks
# ---------------------------------------------------------------------------


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


def test_a_dropped_sidebar_example_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    first, second = [
        t
        for _, t, k in GEN.SUPPORTING
        if k == "exceptions_supersede" and "example" in t
    ]
    monkeypatch.setattr(
        GEN, "SUPPORTING", tuple(s for s in GEN.SUPPORTING if s[1] != second)
    )
    assert list(_residue(GEN.build(session)).values()) == [second]
    assert first != second


def test_a_dropped_pace_leaves_its_leaf_unaccounted(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    (pace,) = [c for c in GEN.COMPONENTS if c.key == "pace_effects"]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if t != GEN.SLOW_PACE))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            (
                dataclasses.replace(
                    c,
                    options=c.options[:2],
                    option_sources=c.option_sources[:2],
                )
                if c is pace
                else c
            )
            for c in GEN.COMPONENTS
        ),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit core-play-completion/exploration: leaf ")


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(c for c in GEN.COMPONENTS if c.key != "round_down")
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit core-play-completion/six_abilities: expected rule "
        "play.six_abilities/round_down has no component"
    ) in found


def test_a_dropped_table_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if t != GEN.TRAVEL_PACE_TABLE))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit core-play-completion/exploration: leaf ")


# ---------------------------------------------------------------------------
# Test-only composition with the eight-batch acceptance
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


def test_composed_the_three_targets_close_and_85_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    assert len(prior.oracle.representation.records) == 74
    assert len(prior.oracle.spans) == 555
    assert len(prior.batches) == 8
    assert len(prior.oracle.reference_resolutions) == 1
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert len(recorded.proposed_spans) == 71
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
    assert len(mine) == 85


def test_no_accepted_empty_target_reference_points_into_this_batch(prior) -> None:  # type: ignore[no-untyped-def]
    # Every accepted pointer with no destination names a part this batch does
    # not author, so no resolution is drafted; the one recorded resolution
    # (attack roll -> play.d20_tests) is untouched.
    empty = sorted(
        (r.scope_key, r.source_text)
        for r in prior.oracle.representation.references
        if r.target_record_key == ""
    )
    assert empty == sorted(
        [
            ("srd-5.2.1/character-creation", "Character Creation"),
            ("srd-5.2.1/character-creation", "Character Creation"),
            (EQUIPMENT, "Equipment"),
            (EQUIPMENT, "Equipment"),
            (PLAY, "Playing the Game"),
            (GLOSSARY, "Rules Glossary"),
            ("srd-5.2.1/spells", "Spells"),
            ("srd-5.2.1/spells", "Spells"),
        ]
    )
    (resolution,) = prior.oracle.reference_resolutions
    assert (resolution.source_text, resolution.target_record_key) == (
        "Playing the Game",
        "play.d20_tests",
    )
    assert not hasattr(GEN, "draft_attack_roll_resolution")
