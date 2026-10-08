"""The ``movement-closure`` proposal, as it is offered for review — CRD Issue 5d.

The batch is five complete glossary entries -- Difficult Terrain, Falling
[Hazard], High Jump, Hover and Long Jump -- proposed by
``.claude/review-notes/issue-5d-movement-closure-generator.py`` from the release
5c actually publishes. Nothing here accepts it: the Owner's acceptance is
recorded by the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_movement_closure_acceptance``; these tests hold the proposal itself.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the accepted-context targets and nothing else;
* the review-sensitive meanings are the facts, qualifiers and governing prose
  the source review expects, read back from the proposal;
* omissions and moved qualifiers are reported by production checks, and every
  word of every spanned leaf is claimed; and
* composed *in this test only* with the 44-entry acceptance this proposal was
  offered against, the four glossary targets it leaves unresolved close and
  Playing the Game ("Combat") is the whole remaining set.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    ProposalLoadError,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ActionCost,
    ActionEconomyFact,
    ApplicabilityKind,
    AutomaticOutcome,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DistanceUnit,
    MovementCostFact,
    MovementCostKind,
    Rational,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    Skill,
    fact_key,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
    validate_representation,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from tests.ingestion.mechanical._replacement_chain import (
    current,
    identity,
    proposal_path,
    through,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-movement-closure-generator.py"
BATCH = "movement-closure"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)


def _unknown(text: str, slug: str) -> str:
    return (
        f"reference srd-5.2.1/rules-glossary:'{text}': "
        f"unknown target record glossary.{slug}"
    )


COMBAT = (
    "reference srd-5.2.1/playing-the-game:'Combat': unknown target record play.combat"
)
#: What the accepted 44 entries leave unresolved, read independently.
ACCEPTED_UNRESOLVED = sorted(
    [_unknown("Difficult Terrain", "difficult_terrain")] * 3
    + [
        _unknown("Falling", "falling"),
        _unknown("High Jump", "high_jump"),
        _unknown("Long Jump", "long_jump"),
        COMBAT,
    ]
)
#: The proposal alone: Hover's *See also* and the two Prone consequences.
ACCEPTED_CONTEXT = sorted(
    [_unknown("Flying", "flying")] + [_unknown("Prone", "prone")] * 2
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("movement_closure", GENERATOR)
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


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (f"glossary.{record}", key)
    ]
    return c


def _prose(built, record: str, key: str) -> str:  # type: ignore[no-untyped-def]
    spans = {s.span_id: s for s in built.ledger.spans}
    out = []
    for b in built.proposal.proposed_representation.prose_bindings:
        if (b.record_key, b.component_key) == (f"glossary.{record}", key):
            s = spans[b.span_id]
            out.append(built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end])
    return " ".join(out)


def _check(ability: AbilityScore, skill: Skill, dc: int) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability,
        DcKind.FIXED,
        context=RollContext.ABILITY_CHECK,
        dc_value=dc,
        skill=skill,
    )


PRONE = ConditionEffectFact(ConditionKind.PRONE, ConditionEffectKind.APPLIES)
HALVED = DamageModificationFact(DamageModDirection.REDUCE, Rational(1, 2))


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


def test_the_artifact_is_an_unaccepted_proposal_by_shape(tmp_path: Path) -> None:
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert (
        json.loads(PROPOSAL.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    )
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)
    tampered = tmp_path / "p.json"
    tampered.write_text(
        PROPOSAL.read_text("utf-8").replace('"dc_value": 15', '"dc_value": 16', 1),
        encoding="utf-8",
    )
    with pytest.raises(ProposalLoadError, match="this caller named"):
        load_proposal(tampered, expected_identity=IDENTITY)


def test_scope_is_the_five_peer_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [u.unit_id for u in units] == [
        f"movement-closure/{slug}" for slug, _, _ in GEN.ENTRIES
    ]
    assert [len(u.leaf_ids) for u in units] == [4, 3, 3, 2, 4]
    assert {r.semantic_key for r in built.proposal.proposed_representation.records} == {
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    }


def test_the_batch_checks_report_only_the_accepted_context_targets(built) -> None:  # type: ignore[no-untyped-def]
    assert GEN.batch_findings(built) == {
        "partition": [],
        "review_units": [],
        "representation": ACCEPTED_CONTEXT,
    }
    assert GEN.expected_representation_findings() == ACCEPTED_CONTEXT
    assert GEN.OUTSTANDING_TARGETS == ()


def test_every_reference_is_native_exact_scope_and_target(built) -> None:  # type: ignore[no-untyped-def]
    refs = {
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in built.proposal.proposed_representation.references
    }
    g = "srd-5.2.1/rules-glossary"
    assert refs == {
        ("glossary.falling", "prone_on_landing", "Prone", g, "glossary.prone"),
        ("glossary.long_jump", "difficult_landing", "Prone", g, "glossary.prone"),
        (
            "glossary.long_jump",
            "difficult_landing",
            "Difficult Terrain",
            g,
            "glossary.difficult_terrain",
        ),
        ("glossary.hover", "", "Flying", g, "glossary.flying"),
    }


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_difficult_terrain_costs_one_extra_foot_and_does_not_stack(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "difficult_terrain", "extra_cost")
    (cost,) = c.facts
    assert isinstance(cost, MovementCostFact)
    assert (cost.kind, cost.feet) == (MovementCostKind.PER_FOOT_SURCHARGE, 1)
    prose = _prose(built, "difficult_terrain", "extra_cost")
    assert "in that space" in prose
    assert "isn't cumulative; either a space is Difficult Terrain or it isn't" in prose


def test_the_trigger_list_stays_open_ended_and_complete(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "difficult_terrain", "difficult_spaces")
    assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    assert c.irreducibility_reason_code == "contextual_applicability"
    prose = _prose(built, "difficult_terrain", "difficult_spaces")
    assert "any of the following or something similar" in prose
    for item in GEN.DIFFICULT_SPACES[1:]:
        assert item in prose
    assert len(GEN.DIFFICULT_SPACES) == 7


def test_fall_damage_is_per_ten_feet_with_a_twenty_dice_ceiling(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "falling", "fall_damage")
    assert c.facts == (
        DamageFact(
            DamageType.BLUDGEONING,
            dice=DiceExpression(1, DieSize.D6),
            maximum_dice=20,
            per=DamageInterval(ScalingBasis.DISTANCE_FALLEN, 10, DistanceUnit.FOOT),
        ),
    )
    assert "at the end of the fall" in _prose(built, "falling", "fall_damage")


def test_landing_prone_is_governed_by_the_no_damage_exception(built) -> None:  # type: ignore[no-untyped-def]
    # No production check reports a dropped component applies_when (it carries
    # no provenance claim), so the exception is pinned here by meaning.
    c = _component(built, "falling", "prone_on_landing")
    assert c.facts == (PRONE,)
    assert c.applies_when.kind is ApplicabilityKind.DAMAGE_OUTCOME
    assert c.applies_when.damage_outcome is DamageOutcome.ANY_DAMAGE
    assert c.applies_when.negated is False
    assert c.fact_qualifiers == ()
    prose = _prose(built, "falling", "prone_on_landing")
    assert "When the creature lands" in prose
    assert "unless it avoids taking any damage from the fall" in prose


def test_the_liquid_reaction_offers_two_checks_and_halves_on_success(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "falling", "falling_into_liquid")
    assert c.irreducibility_reason_code == "contextual_applicability"
    economy, check, halved = c.facts
    assert economy == ActionEconomyFact(ActionCost.REACTION)
    assert (check.dc_kind, check.dc_value, check.context) == (
        DcKind.FIXED,
        15,
        RollContext.ABILITY_CHECK,
    )
    assert set(check.alternatives) == {
        RollSpec(
            RollActor.SUBJECT,
            RollContext.ABILITY_CHECK,
            AbilityScore.STRENGTH,
            Skill.ATHLETICS,
        ),
        RollSpec(
            RollActor.SUBJECT,
            RollContext.ABILITY_CHECK,
            AbilityScore.DEXTERITY,
            Skill.ACROBATICS,
        ),
    }
    assert halved == HALVED
    (q,) = c.fact_qualifiers
    assert q.fact_key == fact_key(HALVED)
    assert q.applies_when.kind is ApplicabilityKind.ROLL_OUTCOME
    assert q.applies_when.outcome is AutomaticOutcome.SUCCESS
    prose = _prose(built, "falling", "falling_into_liquid")
    assert "falls into water or another liquid can use its Reaction" in prose


@pytest.mark.parametrize(
    ("record", "rule", "standing"),
    [
        (
            "high_jump",
            "3 plus your Strength modifier (minimum of 0 feet) if you move at least "
            "10 feet on foot immediately before the jump",
            "you can jump only half that distance",
        ),
        (
            "long_jump",
            "up to your Strength score if you\n"
            "move at least 10 feet immediately before the jump",
            "you can leap only half that distance",
        ),
    ],
)
def test_jump_distance_keeps_its_formula_prerequisite_halving_and_cost(
    built: Built, record: str, rule: str, standing: str
) -> None:
    key = "jump_height" if record == "high_jump" else "jump_distance"
    c = _component(built, record, key)
    assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    prose = _prose(built, record, key)
    assert rule in prose
    assert standing in prose
    assert "Either way, each foot" in prose and "costs a foot of movement" in prose


def test_high_jump_reach_adds_one_and_a_half_heights(built) -> None:  # type: ignore[no-untyped-def]
    prose = _prose(built, "high_jump", "reach")
    assert "half your height above yourself" in prose
    assert "the height of the jump plus 1½ times your height" in prose


def test_hover_is_limited_and_points_at_flying(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "hover", "hovering")
    assert c.handling is ComponentHandling.PROSE_BOUND
    prose = _prose(built, "hover", "hovering")
    assert "as noted in their stat blocks" in prose
    assert "prevents you from falling in certain circumstances" in prose


def test_a_failed_landing_check_in_difficult_terrain_is_prone(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "long_jump", "difficult_landing")
    assert c.facts == (_check(AbilityScore.DEXTERITY, Skill.ACROBATICS, 10), PRONE)
    (q,) = c.fact_qualifiers
    assert q.fact_key == fact_key(PRONE)
    assert q.applies_when.outcome is AutomaticOutcome.FAILURE
    assert "If you land in Difficult Terrain" in _prose(
        built, "long_jump", "difficult_landing"
    )


def test_the_low_obstacle_check_is_the_gms_option_with_its_consequence(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "long_jump", "low_obstacle")
    assert c.irreducibility_reason_code == "gamemaster_latitude"
    assert c.facts == (_check(AbilityScore.STRENGTH, Skill.ATHLETICS, 10),)
    prose = _prose(built, "long_jump", "low_obstacle")
    assert "assumes that the height of the jump doesn't matter" in prose
    assert "At your GM's option" in prose
    assert "no taller than a quarter of the jump's distance" in prose
    assert "Otherwise, you hit the obstacle." in prose


def test_examples_and_see_also_support_and_state_no_rule(built) -> None:  # type: ignore[no-untyped-def]
    texts = {
        built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]: s
        for s in built.ledger.spans
    }
    supporting = {
        t
        for t, s in texts.items()
        if s.disposition is SemanticDisposition.SUPPORTING_AUTHORITY
    }
    assert supporting == {
        "For example, moving 5 feet through Difficult Terrain costs 10 feet of "
        "movement.",
        '_See also_ "Flying."',
    }
    bound = {b.span_id for b in built.proposal.proposed_representation.prose_bindings}
    assert not bound & {texts[t].span_id for t in supporting}


# ---------------------------------------------------------------------------
# Negative controls: each is reported by a production check
# ---------------------------------------------------------------------------


def _authoring_findings(session, monkeypatch, **tables) -> list[str]:  # type: ignore[no-untyped-def]
    for name, keep in tables.items():
        monkeypatch.setattr(GEN, name, tuple(filter(keep, getattr(GEN, name))))
    found = GEN.batch_findings(GEN.build(session))
    return [f for v in found.values() for f in v if f not in set(ACCEPTED_CONTEXT)]


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    found = _authoring_findings(
        session,
        monkeypatch,
        COMPONENTS=lambda c: (c.entry, c.key) != ("long_jump", "low_obstacle"),
    )
    assert found[0] == (
        "review unit movement-closure/long_jump: expected rule "
        "glossary.long_jump/low_obstacle has no component"
    )


def _residue(built) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Non-whitespace text of a spanned leaf that no span covers."""
    out = {}
    for lid in {s.leaf_id for s in built.ledger.spans}:
        text = list(built.leaf_rows[lid].content)
        for s in built.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if "".join(text).strip():
            out[lid] = "".join(text).strip()
    return out


def test_every_spanned_leaf_is_claimed_to_the_last_word(built) -> None:  # type: ignore[no-untyped-def]
    # A sentence dropped from the source review is not a production batch
    # finding (partitions are checked incomplete-tolerant); this is its check.
    assert _residue(built) == {}


def test_a_dropped_trigger_is_residue(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    slope = "- A slope of 20 degrees or more"
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, x, tuple(t for t in ts if t != slope)) for e, k, x, ts in GEN.CLAUSES
        ),
    )
    assert list(_residue(GEN.build(session)).values()) == [slope]


def _violations(built, **draft_changes) -> list[str]:  # type: ignore[no-untyped-def]
    p = built.proposal
    draft = dataclasses.replace(p.proposed_representation, **draft_changes)
    return review_unit_violations(
        p.proposed_review_units, draft, p.policy_version, built.ledger.spans
    ) + [
        f
        for f in validate_representation(draft, built.ledger, built.corpus)
        if "unknown target" not in f
    ]


def _replace(built, key: str, **changes):  # type: ignore[no-untyped-def]
    return tuple(
        dataclasses.replace(c, **changes) if c.semantic_key == key else c
        for c in built.proposal.proposed_representation.components
    )


def test_dropping_a_typed_fact_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    found = _violations(built, components=_replace(built, "fall_damage", facts=()))
    assert any("damage" in f and "fall_damage" in f for f in found), found


def test_dropping_governing_prose_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    key = ("glossary.difficult_terrain", "extra_cost")
    found = _violations(
        built,
        prose_bindings=tuple(
            b for b in draft.prose_bindings if (b.record_key, b.component_key) != key
        ),
    )
    # The unit loses its expected rule, the mixed component its prose, and
    # both sentences fall unclaimed.
    assert "glossary.difficult_terrain/extra_cost" in found[0], found
    assert (
        "component glossary.difficult_terrain/extra_cost: mixed handling with no "
        "bound prose"
    ) in found
    assert sum(f.endswith("substantive but unclaimed") for f in found) == 2
    assert all(
        "extra_cost" in f or f.endswith("substantive but unclaimed") for f in found
    )


@pytest.mark.parametrize("key", ["falling_into_liquid", "difficult_landing"])
def test_dropping_a_roll_outcome_qualifier_is_reported(built, key: str) -> None:  # type: ignore[no-untyped-def]
    found = _violations(built, components=_replace(built, key, fact_qualifiers=()))
    assert found and all(
        "claim for an undeclared element" in f and key in f for f in found
    ), found


def test_moving_the_halving_qualifier_to_the_damage_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    q = _component(built, "falling", "falling_into_liquid").fact_qualifiers
    components = tuple(
        (
            dataclasses.replace(c, fact_qualifiers=q)
            if c.semantic_key == "fall_damage"
            else (
                dataclasses.replace(c, fact_qualifiers=())
                if c.semantic_key == "falling_into_liquid"
                else c
            )
        )
        for c in built.proposal.proposed_representation.components
    )
    found = _violations(built, components=components)
    assert (
        "component glossary.falling/fall_damage: states a roll outcome, but no fact "
        "in scope calls for a roll; the component names an outcome of nothing"
    ) in found
    assert any("names a fact this scope does not hold" in f for f in found)


def test_a_check_choice_of_one_is_refused(built) -> None:  # type: ignore[no-untyped-def]
    economy, check, halved = _component(built, "falling", "falling_into_liquid").facts
    single = dataclasses.replace(check, alternatives=check.alternatives[1:])
    found = _violations(
        built,
        components=_replace(
            built, "falling_into_liquid", facts=(economy, single, halved)
        ),
    )
    assert any("alternatives states one option" in f for f in found), found


# ---------------------------------------------------------------------------
# Test-only composition with the 44-entry acceptance it was proposed against
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _prior(recorded: MechanicalProposal) -> AcceptedInputs:
    """The three-batch acceptance this proposal was offered against.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch. Both sides are the
    superseded release's; its physical source is not available, so the
    composition below is representation-only.
    """
    inputs = through("reference-closure")
    assert inputs.oracle.binding == recorded.binding
    assert IDENTITY not in {b.proposal_identity for b in inputs.batches}
    return inputs


def test_the_proposal_is_disjoint_from_the_acceptance_it_was_offered_against(
    recorded: MechanicalProposal,
) -> None:
    inputs = _prior(recorded)
    assert sorted(b.batch_id for b in inputs.batches) == [
        "actions-pilot",
        "conditions-pilot",
        "reference-closure",
    ]
    assert not {r.semantic_key for r in inputs.oracle.representation.records} & {
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    }
    assert not {s.span_id for s in inputs.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }


def test_composed_the_four_close_and_combat_is_all_that_remains(
    recorded: MechanicalProposal,
) -> None:
    inputs = _prior(recorded)
    accepted = inputs.oracle.representation
    proposed = recorded.proposed_representation
    assert len(accepted.records) == 44

    alone = relationship_and_reference_violations(accepted)
    assert sorted(f for f in alone if "unknown target" in f) == ACCEPTED_UNRESOLVED

    composed = dataclasses.replace(
        accepted,
        **{
            f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
            for f in dataclasses.fields(accepted)
        },
    )
    # The entire remaining relationship and reference set: Combat, and no new
    # dependency. The prose and provenance checks need the superseded release's
    # physical source and are retired.
    assert sorted(relationship_and_reference_violations(composed)) == [COMBAT]


# ---------------------------------------------------------------------------
# Shared authoring: the emit gate
# ---------------------------------------------------------------------------


def test_emit_writes_only_what_its_gate_admits(
    built: Built,
    source_release_db: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from afterworlds.ingestion.mechanical.authoring import emit

    out = tmp_path / "p.json"
    expected = GEN.expected_representation_findings()
    assert emit(str(source_release_db), lambda _s: built, out, expected) == 0
    # The current build, under its current identity; not the recorded bytes.
    assert out.read_bytes() == GEN.render(built.proposal).encode("utf-8")
    assert proposal_identity(built.proposal) in capsys.readouterr().out

    refused = tmp_path / "refused.json"
    with pytest.raises(ValueError, match="glossary.flying"):
        emit(str(source_release_db), lambda _s: built, refused, expected[1:])
    assert not refused.exists()
