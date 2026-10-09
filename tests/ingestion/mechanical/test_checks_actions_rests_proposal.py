"""The ``checks-actions-rests`` proposal, as it is offered for review — CRD Issue 5d.

Three whole *Playing the Game* sections -- D20 Tests (with its Heroic
Inspiration sidebar), Proficiency and Actions -- plus the Rules Glossary's
Damage Types, Dead, Long Rest and Short Rest entries, proposed by
``.claude/review-notes/issue-5d-checks-actions-rests-generator.py`` from the
release 5c actually publishes. Nothing here accepts it; the Owner's acceptance
and the attack-roll resolution are recorded by
the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_checks_actions_rests_acceptance``.

What is pinned, and why:

* the committed artifact is the superseded release's recorded proposal, by
  shape; the generator builds over the current release (that it no longer
  derives the recorded bytes is retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings (proficiency bands, applications and limits,
  the tool-and-skill Advantage, the rest facts, restatements kept untyped)
  read back from the proposal;
* a heading the section prints more than once is excluded once per printing;
* omissions are reported and every word of every spanned leaf is claimed;
* the recorded proposal, composed *in this test only* with the seven-batch
  acceptance it was offered against (re-derived by its script, since the
  committed artifact now also holds this batch; both the superseded
  release's): the five outstanding targets close, only the new unknowns and
  the printed pointers with no destination remain, and exactly the batch's 118
  leaves gain coverage (judging the composition against a corpus needs the
  superseded release's, which is not rebuilt; that check is retired); and
* the accepted attack-roll pointer stays unresolved: its drafted resolution
  is refused by the accepted authority as it stands and applies, in memory
  only, once the recorded proposal is accepted.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import sys
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
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ActionAllowanceFact,
    ActionCost,
    AdvantageFact,
    AllowanceScope,
    ConditionLevelFact,
    HealingFact,
    ProficiencyApplicationFact,
    ProficiencyBonusBandFact,
    ProficiencyKind,
    ProvenanceTargetKind,
    RetryRestrictionFact,
    RollContext,
    TimeUnit,
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
    REPLACEMENT,
    current,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-checks-actions-rests-generator.py"
BATCH = "checks-actions-rests"
PROPOSAL = proposal_path(BATCH)
ACCEPTED = REPLACEMENT.ACCEPTED_PATH
IDENTITY = identity(BATCH)

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the committed acceptance leaves undefined: the five targets closed here.
CLOSED = sorted(
    [
        f"reference {PLAY}:'Actions': unknown target record play.actions",
        _glossary("Damage types", "damage_types"),
        _glossary("dead", "dead"),
        _glossary("Long Rests", "long_rest"),
        _glossary("Short", "short_rest"),
        _glossary("Short Rest", "short_rest"),
    ]
    + [_glossary("Long Rest", "long_rest")] * 3
)
#: The accepted pointers into parts with no record; each stays unresolved.
ACCEPTED_UNRESOLVED = sorted(
    [
        _unresolved("srd-5.2.1/equipment", "Equipment"),
        _unresolved(PLAY, "Playing the Game"),
        _unresolved("srd-5.2.1/spells", "Spells"),
    ]
)
#: What this batch adds that nothing accepted or proposed defines.
NEW = sorted(
    [
        _glossary("Armor Class", "armor_class"),
        _glossary("Challenge Rating", "challenge_rating"),
        _glossary("Expertise", "expertise"),
        _unresolved("srd-5.2.1/character-creation", "Character Creation"),
        _unresolved("srd-5.2.1/character-creation", "Character Creation"),
        _unresolved("srd-5.2.1/equipment", "Equipment"),
        _unresolved(GLOSSARY, "Rules Glossary"),
        _unresolved("srd-5.2.1/spells", "Spells"),
    ]
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("checks_actions_rests", GENERATOR)
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
    """The seven-batch acceptance this proposal was offered against.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("combat-damage-breaking")
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (record, key)
    ]
    return c


def _clause(key: str) -> tuple[str, ...]:
    (texts,) = [ts for _, k, _, ts in GEN.CLAUSES if k == key]
    return texts  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_generator_builds_over_the_current_release(built) -> None:  # type: ignore[no-untyped-def]
    assert built.binding == current().oracle.binding
    assert b"\r" not in PROPOSAL.read_bytes()


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


def test_scope_is_three_whole_sections_and_four_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, len(u.leaf_ids)) for u in units] == [
        ("checks-actions-rests/d20_tests", 55),
        ("checks-actions-rests/proficiency", 22),
        ("checks-actions-rests/actions", 15),
        ("checks-actions-rests/damage_types", 3),
        ("checks-actions-rests/dead", 3),
        ("checks-actions-rests/long_rest", 12),
        ("checks-actions-rests/short_rest", 8),
    ]
    assert [u.kind for u in units] == [ReviewUnitKind.SECTION] * 3 + [
        ReviewUnitKind.ENTRY
    ] * 4
    assert [r.semantic_key for r in built.proposal.proposed_representation.records] == [
        "play.d20_tests",
        "play.proficiency",
        "play.actions",
        "glossary.damage_types",
        "glossary.dead",
        "glossary.long_rest",
        "glossary.short_rest",
    ]


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    # In-batch pointers resolve: Proficiency, Actions and Short Rest.
    assert not [
        f
        for f in found["representation"]
        if f.endswith(("play.proficiency", "play.actions", "glossary.short_rest"))
    ]


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_the_proficiency_bonus_table_is_eight_bands(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "play.proficiency", "proficiency_bonus_bands")
    assert c.handling is ComponentHandling.STRUCTURED
    assert all(isinstance(f, ProficiencyBonusBandFact) for f in c.facts)
    assert [(f.bonus, f.minimum, f.maximum) for f in c.facts] == [
        (2, None, 4),
        (3, 5, 8),
        (4, 9, 12),
        (5, 13, 16),
        (6, 17, 20),
        (7, 21, 24),
        (8, 25, 28),
        (9, 29, 30),
    ]


def test_each_kind_of_proficiency_applies_to_its_own_roll(built) -> None:  # type: ignore[no-untyped-def]
    applied = {
        (f.proficiency, f.roll.context)
        for c in built.proposal.proposed_representation.components
        for f in c.facts
        if isinstance(f, ProficiencyApplicationFact)
    }
    assert applied == {
        (ProficiencyKind.SKILL, RollContext.ABILITY_CHECK),
        (ProficiencyKind.SAVING_THROW, RollContext.SAVING_THROW),
        (ProficiencyKind.WEAPON, RollContext.ATTACK_ROLL),
        (ProficiencyKind.TOOL, RollContext.ABILITY_CHECK),
    }


def test_tool_and_skill_together_grant_advantage(built) -> None:  # type: ignore[no-untyped-def]
    (advantage,) = [
        f
        for f in _component(built, "play.proficiency", "tool_proficiency").facts
        if isinstance(f, AdvantageFact)
    ]
    assert advantage.roll.context is RollContext.ABILITY_CHECK
    assert advantage.requires_proficiencies == (
        ProficiencyKind.SKILL,
        ProficiencyKind.TOOL,
    )


def test_the_bonus_is_added_multiplied_and_divided_at_most_once(built) -> None:  # type: ignore[no-untyped-def]
    facts = _component(built, "play.proficiency", "bonus_operation_limits").facts
    assert [(f.operation.value, f.maximum_applications) for f in facts] == [
        ("add", 1),
        ("multiply", 1),
        ("divide", 1),
    ]


def test_d20_test_restatements_stay_untyped(built) -> None:  # type: ignore[no-untyped-def]
    # One typed copy per rule: the Proficiency section types the proficiency
    # rules; the accepted glossary types the actions and Exhaustion removal.
    for record, key in [
        ("play.d20_tests", "check_proficiency"),
        ("play.d20_tests", "save_proficiency"),
        ("play.d20_tests", "attack_proficiency"),
        ("play.actions", "main_actions"),
    ]:
        c = _component(built, record, key)
        assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    # Exhaustion Reduced is prose inside the Long Rest benefits: the only fact
    # there is the full healing, never a second Exhaustion removal.
    assert _component(built, "glossary.long_rest", "benefits").facts == (
        HealingFact(restores_all_hit_points=True),
    )


def test_the_rest_and_revival_facts(built) -> None:  # type: ignore[no-untyped-def]
    assert _component(built, "glossary.long_rest", "frequency").facts == (
        RetryRestrictionFact(16, TimeUnit.HOUR, False),
    )
    assert _component(built, "glossary.long_rest", "benefits").facts == (
        HealingFact(restores_all_hit_points=True),
    )
    (revival,) = _component(built, "glossary.dead", "exhaustion_on_revival").facts
    assert isinstance(revival, ConditionLevelFact) and revival.amount == 1
    assert _component(built, "play.actions", "one_bonus_action").facts == (
        ActionAllowanceFact(1, AllowanceScope.TURN, ActionCost.BONUS_ACTION),
    )
    # A Short Rest's healing depends on each die rolled: governing prose.
    assert _component(built, "glossary.short_rest", "benefits").facts == ()


# ---------------------------------------------------------------------------
# What a GameMaster reads: each rest benefit with the condition granting it
# ---------------------------------------------------------------------------


def _gamemaster_rest_components(
    session: Session, built: Built
) -> dict[tuple[str, str], GameMasterComponent]:
    """The rest records as the production GameMaster view presents them.

    The view resolves each component's *own* governing prose only; it infers no
    scope from a sibling component, so a benefit read apart from its lead
    would read as unconditional.
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
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "checks-actions-rests"),
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
        if c.record_key in ("glossary.long_rest", "glossary.short_rest")
    }


def _read(component: GameMasterComponent) -> str:
    texts = [e.text for e in component.governing_prose if isinstance(e, SourceProse)]
    assert texts and None not in texts
    return " ".join(t for t in texts if t is not None)


FINISH = "When you finish the rest, you gain the following benefits:"


def test_each_rest_benefit_is_read_with_the_finish_that_grants_it(  # type: ignore[no-untyped-def]
    session, built
) -> None:
    view = _gamemaster_rest_components(session, built)
    read = {k: _read(c) for k, c in view.items()}
    # Every printed benefit is governed, in the component that carries it, by
    # the lead that grants it.
    for label in (
        "**Regain All HP.**",
        "**Ability Scores Restored.**",
        "**Exhaustion Reduced.**",
        "**Special Feature.** Some features are recharged by a Long Rest.",
        "**Spend Hit Point Dice.**",
        "**Special Feature.** Some features are recharged by a Short Rest.",
    ):
        (holder,) = [k for k, text in read.items() if label in text]
        assert FINISH in read[holder], (holder, label)
    # The typed full healing is structured context of that same component.
    healing = view[("glossary.long_rest", "benefits")]
    assert [f.fact for f in healing.structured_context] == [
        HealingFact(restores_all_hit_points=True)
    ]
    assert FINISH in read[("glossary.long_rest", "benefits")]
    # What an interruption does to the benefits is read with the interruptions.
    long_stop = read[("glossary.long_rest", "interruptions")]
    assert "A Long Rest is stopped by the following interruptions:" in long_stop
    assert "you gain the benefits of a Short Rest." in long_stop
    short_stop = read[("glossary.short_rest", "interruptions")]
    assert "A Short Rest is stopped by the following interruptions:" in short_stop
    assert "An interrupted Short Rest confers no benefits." in short_stop


def test_a_benefit_split_from_its_lead_is_read_unconditioned(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    # The detached shape this batch corrected: the lead alone in one component,
    # the healing in another. The view then shows the healing with no finish.
    lead, heal, *rest = next(
        ts for e, k, _, ts in GEN.CLAUSES if (e, k) == ("long_rest", "benefits")
    )
    (benefits,) = [
        c for c in GEN.COMPONENTS if (c.entry, c.key) == ("long_rest", "benefits")
    ]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(c for c in GEN.CLAUSES if (c[0], c[1]) != ("long_rest", "benefits"))
        + (
            ("long_rest", "benefits", (None,), (lead, *rest)),
            ("long_rest", "regain_all_hp", ("healing", None), (heal,)),
        ),
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(c for c in GEN.COMPONENTS if c is not benefits)
        + (
            dataclasses.replace(
                benefits,
                handling=ComponentHandling.PROSE_BOUND,
                facts=(),
                refs=(("Exhaustion", "exhaustion"),),
            ),
            dataclasses.replace(
                benefits, key="regain_all_hp", refs=(("Hit Points", "hit_points"),)
            ),
        ),
    )
    healing = _gamemaster_rest_components(session, GEN.build(session))[
        ("glossary.long_rest", "regain_all_hp")
    ]
    assert healing.structured_context
    assert FINISH not in _read(healing)


def test_the_heroic_inspiration_sidebar_is_authored_whole(built) -> None:  # type: ignore[no-untyped-def]
    # The release places it in D20 Tests; its meaning is kept, not excluded.
    for key in (
        "heroic_inspiration",
        "only_one_heroic_inspiration",
        "gaining_heroic_inspiration",
    ):
        bound = {
            b.span_id
            for b in built.proposal.proposed_representation.prose_bindings
            if b.component_key == key
        }
        assert bound == {built.spans[("d20_tests", t)].span_id for t in _clause(key)}


def test_printed_pointers_without_a_destination_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    unresolved = {
        (r.from_record_key, r.source_text, r.scope_key)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key == ""
    }
    assert unresolved == {
        ("play.d20_tests", "Rules Glossary", GLOSSARY),
        ("play.d20_tests", "Spells", "srd-5.2.1/spells"),
        ("play.d20_tests", "Equipment", "srd-5.2.1/equipment"),
        ("play.d20_tests", "Character Creation", "srd-5.2.1/character-creation"),
        ("play.proficiency", "Character Creation", "srd-5.2.1/character-creation"),
    }


def test_the_proficiency_pointers_cite_the_reference_already_stated(  # type: ignore[no-untyped-def]
    built,
) -> None:
    # The two supporting "See "Proficiency"..." pointers add no record-owned
    # duplicate: the record already states that pointer (step 5's list), so
    # their spans cite that reference beside the list item that prints it.
    representation = built.proposal.proposed_representation
    proficiency = [
        r
        for r in representation.references
        if (r.from_record_key, r.source_text) == ("play.d20_tests", "Proficiency")
    ]
    assert sorted(r.from_component_key for r in proficiency) == [
        "add_modifiers",
        "save_proficiency",
    ]
    assert {r.target_record_key for r in proficiency} == {"play.proficiency"}
    (step_5,) = [r for r in proficiency if r.from_component_key == "add_modifiers"]
    cited = {
        c.span_id
        for c in representation.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
        and c.target_key == reference_target_key(step_5)
    }
    item = next(t for t in _clause("add_modifiers") if '"Proficiency"' in t)
    assert cited == {
        built.spans[("d20_tests", t)].span_id
        for t in (
            item,
            GEN.CHECK_PROFICIENCY_POINTER,
            GEN.ATTACK_PROFICIENCY_POINTER,
        )
    }


# ---------------------------------------------------------------------------
# Headings, including those printed more than once
# ---------------------------------------------------------------------------


def _excluded(built) -> list[str]:  # type: ignore[no-untyped-def]
    return [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]


def test_only_headings_are_excluded_each_printing_once(built) -> None:  # type: ignore[no-untyped-def]
    # 26 subsection headings plus the seven record headings.
    excluded = _excluded(built)
    assert len(excluded) == 33
    assert all(c.startswith("#") and "\n" not in c for c in excluded)
    leaves = [
        leaf
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert len(set(leaves)) == len(leaves)
    assert excluded.count("#### Ability Modifier") == 3
    assert excluded.count("#### Proficiency Bonus") == 3
    assert excluded.count("#### Difficulty Class") == 2


def test_a_repeated_heading_listed_too_few_times_is_refused(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    d20, rest = GEN.EXCLUDED[0], GEN.EXCLUDED[1:]
    contents = list(d20[1])
    contents.remove("#### Ability Modifier")
    monkeypatch.setattr(GEN, "EXCLUDED", ((d20[0], tuple(contents), d20[2]), *rest))
    with pytest.raises(ValueError, match="matches 3 leaves; the review lists it 2"):
        GEN.build(session)


def test_an_excluded_heading_must_match_exactly(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "EXCLUDED",
        tuple(
            (e, tuple(c.replace("#### Armor Class", "#### Armor") for c in cs), r)
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


def test_a_dropped_example_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    (example,) = [t for e, t, k in GEN.SUPPORTING if k == "skill_proficiency"]
    monkeypatch.setattr(
        GEN,
        "SUPPORTING",
        tuple(s for s in GEN.SUPPORTING if s[2] != "skill_proficiency"),
    )
    assert list(_residue(GEN.build(session)).values()) == [example]


def test_a_dropped_rule_leaves_its_leaf_unaccounted(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN, "CLAUSES", tuple(c for c in GEN.CLAUSES if c[1] != "resuming")
    )
    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(c for c in GEN.COMPONENTS if c.key != "resuming")
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit checks-actions-rests/long_rest: leaf ")
    assert found.endswith(
        "named by no expected rule, supporting group or excluded group"
    )


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(c for c in GEN.COMPONENTS if c.key != "natural_1")
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit checks-actions-rests/d20_tests: expected rule "
        "play.d20_tests/natural_1 has no component"
    ) in found


def test_a_dropped_table_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The Damage Types table is part of its clause: dropping it leaves its
    # leaf reviewed by nothing.
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if t != GEN.DAMAGE_TYPES_TABLE))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit checks-actions-rests/damage_types: leaf ")


# ---------------------------------------------------------------------------
# Test-only composition with the committed acceptance
# ---------------------------------------------------------------------------


def _composed(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    oracle, accepted = prior.oracle, prior.oracle.representation
    proposed = proposal.proposed_representation
    return dataclasses.replace(
        prior,
        oracle=dataclasses.replace(
            oracle,
            spans=(*oracle.spans, *(p.span for p in proposal.proposed_spans)),
            review_units=(*oracle.review_units, *proposal.proposed_review_units),
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


def _references(inputs: AcceptedInputs) -> list[str]:
    # The representation's own reference findings (resolutions applied): no
    # corpus, so none of the superseded release's is needed.
    rep = candidate_from_accepted_inputs(lifted(inputs)).representation
    return sorted(
        f
        for f in relationship_and_reference_violations(rep)
        if f.startswith("reference ")
    )


def test_composed_the_five_targets_close_and_118_leaves_gain_coverage(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert prior.oracle.binding == recorded.binding
    assert len(prior.oracle.representation.records) == 67
    assert len(prior.oracle.spans) == 430
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted = prior.oracle.representation
    proposed = recorded.proposed_representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }

    composed = _composed(prior, recorded)
    assert _references(prior) == sorted(CLOSED + ACCEPTED_UNRESOLVED)
    assert _references(composed) == sorted(ACCEPTED_UNRESOLVED + NEW)
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert len(recorded.proposed_spans) == 125
    assert _covered(composed) - _covered(prior) == mine
    assert len(mine) == 118


# ---------------------------------------------------------------------------
# The accepted attack-roll pointer and its drafted resolution
# ---------------------------------------------------------------------------


def test_the_accepted_attack_roll_pointer_is_the_drafts_citation(prior) -> None:  # type: ignore[no-untyped-def]
    draft = GEN.draft_attack_roll_resolution(prior.oracle.binding)
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
    assert prior.oracle.reference_resolutions == ()


def test_the_draft_cannot_apply_to_the_accepted_authority_as_it_stands(prior) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(AcceptanceError, match="states no record for"):
        resolve_references(
            prior,
            resolutions=(GEN.draft_attack_roll_resolution(prior.oracle.binding),),
            authorized_by="test",
            authorization_reference="test",
            reviewer="test",
            resolved_at="2026-09-22T00:00:00Z",
        )


def test_once_accepted_the_draft_resolves_through_the_native_seam(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    # In memory only: nothing is written and no decision is recorded.
    on_disk = hashlib.sha256(ACCEPTED.read_bytes()).hexdigest()
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="checks-actions-rests",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-22T00:00:00Z",
        prior=prior,
    )
    resolved = resolve_references(
        accepted,
        resolutions=(GEN.draft_attack_roll_resolution(prior.oracle.binding),),
        authorized_by="test",
        authorization_reference="test",
        reviewer="test",
        resolved_at="2026-09-22T00:00:00Z",
    )
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    assert (
        "play.combat",
        "attack_structure",
        "Playing the Game",
        "play.d20_tests",
    ) in {
        (r.from_record_key, r.from_component_key, r.source_text, r.target_record_key)
        for r in effective.references
    }
    # The accepted citation itself is not edited.
    assert resolved.oracle.representation == accepted.oracle.representation
    assert hashlib.sha256(ACCEPTED.read_bytes()).hexdigest() == on_disk
