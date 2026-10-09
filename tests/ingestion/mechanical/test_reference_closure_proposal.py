"""The ``reference-closure`` proposal, as it is offered for review — CRD Issue 5d.

The batch is 14 complete glossary entries -- Concentration, the three
``[Attitude]`` entries, Speed, the four special speeds and Climbing, Crawling,
Flying, Jumping and Swimming -- proposed by
``.claude/review-notes/issue-5d-reference-closure-generator.py`` from the
release 5c actually publishes. Nothing here accepts it: the Owner's acceptance
is recorded by the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_reference_closure_acceptance``; these tests hold the proposal itself.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings are the facts, qualifiers and governing prose
  the source review expects, read back from the proposal;
* omissions made while authoring are reported by production checks; and
* composed *in this test only* with the historical Conditions + Actions
  acceptance it was proposed against, the five targets that acceptance leaves
  unresolved close, the accepted-context targets resolve, and the batch's own
  out-of-scope targets stay explicit.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    unknown_target_findings,
)
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
from afterworlds.ingestion.mechanical.projection import (
    review_unit_violations,
)
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
    AdvantageFact,
    ApplicabilityKind,
    Attitude,
    ConditionKind,
    DcKind,
    DefaultAttitudeFact,
    EffectTerminationFact,
    MovementCostFact,
    MovementCostKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    Skill,
    SpeedChangePropagationFact,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSwitchAccounting,
    SpeedSwitchLimitFact,
    SpeedSwitchOutcome,
    StateEffectFact,
    StateEffectKind,
    SustainedStateRequirementFact,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from tests.ingestion.mechanical._replacement_chain import (
    current,
    identity,
    proposal_path,
    through,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-reference-closure-generator.py"
BATCH = "reference-closure"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)


def _unknown(text: str, slug: str) -> str:
    return (
        f"reference srd-5.2.1/rules-glossary:'{text}': "
        f"unknown target record glossary.{slug}"
    )


#: What the Conditions + Actions acceptance leaves unresolved.
CLOSING = sorted(
    _unknown(t, s)
    for t, s in [
        ("Concentration", "concentration"),
        ("Friendly", "friendly"),
        ("Hostile", "hostile"),
        ("Indifferent", "indifferent"),
        ("Speed", "speed"),
    ]
)
#: Speed's *See also* "Playing the Game" ("Combat"): the chapter is the scope
#: and the Combat section the exact target, which no batch has authored.
COMBAT = (
    "reference srd-5.2.1/playing-the-game:'Combat': "
    "unknown target record play.combat"
)
#: Independently read from the source: one per pointer, so Difficult Terrain,
#: printed in three cost rules, is three.
REMAINING = sorted(
    [_unknown("Difficult Terrain", "difficult_terrain")] * 3
    + [
        _unknown("Falling", "falling"),
        _unknown("High Jump", "high_jump"),
        _unknown("Long Jump", "long_jump"),
        COMBAT,
    ]
)
ACCEPTED_CONTEXT = sorted(
    [_unknown("Incapacitated", "incapacitated")] * 2
    + [_unknown("Influence", "influence")] * 3
    + [_unknown("Prone", "prone")]
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("reference_closure", GENERATOR)
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


def test_scope_is_the_fourteen_peer_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [u.unit_id for u in units] == [
        f"reference-closure/{slug}" for slug, _, _ in GEN.ENTRIES
    ]
    assert sum(len(u.leaf_ids) for u in units) == 33
    assert {r.semantic_key for r in built.proposal.proposed_representation.records} == {
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    }


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    assert GEN.batch_findings(built) == {
        "partition": [],
        "review_units": [],
        "representation": sorted(REMAINING + ACCEPTED_CONTEXT),
    }
    assert GEN.expected_representation_findings() == sorted(
        REMAINING + ACCEPTED_CONTEXT
    )


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_concentration_effects_end_only_when_concentration_breaks(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "concentration", "concentration_effects")
    sustained, ends = c.facts
    assert isinstance(sustained, SustainedStateRequirementFact)
    assert isinstance(ends, EffectTerminationFact)
    (q,) = c.fact_qualifiers
    assert q.applies_when.effect_state is StateEffectKind.CONCENTRATION_BROKEN


def test_concentration_can_be_ended_with_no_action(built) -> None:  # type: ignore[no-untyped-def]
    (fact,) = _component(built, "concentration", "end_at_will").facts
    assert fact == ActionEconomyFact(ActionCost.NONE)
    assert "at any time (no action required)" in _prose(
        built, "concentration", "end_at_will"
    )


def test_another_effect_breaks_at_the_start_of_casting(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "concentration", "another_concentration_effect")
    assert c.handling is ComponentHandling.PROSE_BOUND
    assert "the moment you start casting" in _prose(
        built, "concentration", "another_concentration_effect"
    )


def test_the_damage_dc_is_exact_governing_prose_not_a_model_number(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "concentration", "damage")
    assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()
    prose = _prose(built, "concentration", "damage")
    assert "Constitution saving throw" in prose
    assert (
        "10 or half the damage taken (round down), whichever number is higher" in prose
    )
    assert "maximum DC of 30" in prose


def test_concentration_ends_on_incapacitated_or_death(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "concentration", "incapacitated_or_dead")
    assert c.facts == (StateEffectFact(StateEffectKind.CONCENTRATION_BROKEN),)
    assert c.applies_when.kind is ApplicabilityKind.ANY_OF
    incapacitated, dies = c.applies_when.any_of_terms
    assert incapacitated.condition is ConditionKind.INCAPACITATED
    assert dies.effect_state is StateEffectKind.DIES


def test_attitude_bias_stays_restricted_to_influence(built) -> None:  # type: ignore[no-untyped-def]
    for record, key, state in (
        ("friendly", "influence_advantage", "Advantage"),
        ("hostile", "influence_disadvantage", "Disadvantage"),
    ):
        c = _component(built, record, key)
        assert c.handling is ComponentHandling.PROSE_BOUND
        assert c.irreducibility_reason_code == "contextual_applicability"
        assert f"{state} on an ability check to influence" in _prose(built, record, key)
    # No attitude states an unqualified bias on every check.
    assert not [
        c
        for c in built.proposal.proposed_representation.components
        if c.record_key in {"glossary.friendly", "glossary.hostile"}
        and any(isinstance(f, AdvantageFact) for f in c.facts)
    ]


def test_indifferent_is_the_default_attitude(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "indifferent", "default_attitude")
    assert c.facts == (DefaultAttitudeFact(Attitude.INDIFFERENT),)


def test_switching_speeds_subtracts_and_refuses_a_spent_speed(built) -> None:  # type: ignore[no-untyped-def]
    (fact,) = _component(built, "speed", "switching").facts
    assert fact == SpeedSwitchLimitFact(
        SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED,
        SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED,
    )
    assert "0 or less" in _prose_or_rule(built, "speed", "switching")


def _prose_or_rule(built, record: str, key: str) -> str:  # type: ignore[no-untyped-def]
    """The source text a component's provenance cites, prose-bound or typed."""
    spans = {s.span_id: s for s in built.ledger.spans}
    cited = [
        spans[p.span_id]
        for p in built.proposal.proposed_representation.provenance
        if f"glossary.{record}" in p.target_key and key in p.target_key
    ]
    return " ".join(
        built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end] for s in cited
    )


def test_speed_changes_reach_every_special_speed_equally_and_as_long(built) -> None:  # type: ignore[no-untyped-def]
    (fact,) = _component(built, "speed", "changes_propagate").facts
    assert fact == SpeedChangePropagationFact(
        SpeedPropagationScope.EVERY_SPECIAL_SPEED,
        SpeedPropagationMagnitude.EQUAL_AMOUNT,
        SpeedPropagationDuration.SAME_DURATION,
    )


def test_speed_examples_support_and_state_no_rule(built) -> None:  # type: ignore[no-untyped-def]
    examples = [
        s
        for s in built.ledger.spans
        if built.leaf_rows[s.leaf_id]
        .content[s.char_start : s.char_end]
        .startswith(("For example", "Similarly"))
    ]
    assert len(examples) == 3
    for s in examples:
        assert s.disposition is SemanticDisposition.SUPPORTING_AUTHORITY, s
    bound = {b.span_id for b in built.proposal.proposed_representation.prose_bindings}
    assert not bound & {s.span_id for s in examples}


@pytest.mark.parametrize(
    ("record", "exception"),
    [
        ("climbing", "You ignore this extra cost if you have a Climb Speed and use it"),
        ("crawling", None),
        ("swimming", "You ignore this extra cost if you have a Swim Speed and use it"),
    ],
)
def test_the_movement_surcharge_governs_with_its_own_exceptions(
    built: Built, record: str, exception: str | None
) -> None:
    c = _component(built, record, "extra_cost")
    assert c.handling is ComponentHandling.MIXED
    (cost,) = c.facts
    assert isinstance(cost, MovementCostFact)
    assert (cost.kind, cost.feet) == (MovementCostKind.PER_FOOT_SURCHARGE, 1)
    prose = _prose(built, record, "extra_cost")
    assert "(2 extra feet in Difficult Terrain)" in prose
    if exception:
        assert exception in prose
    # No sibling states the surcharge outside that governing prose.
    assert [
        s.semantic_key
        for s in built.proposal.proposed_representation.components
        if s.record_key == f"glossary.{record}"
        and any(isinstance(f, MovementCostFact) for f in s.facts)
    ] == ["extra_cost"]


@pytest.mark.parametrize(
    ("record", "key"), [("climbing", "difficult_climb"), ("swimming", "rough_water")]
)
def test_the_athletics_check_is_the_gms_option(built, record: str, key: str) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, record, key)
    assert c.irreducibility_reason_code == "gamemaster_latitude"
    (check,) = c.facts
    assert isinstance(check, AbilityCheckFact)
    assert (check.ability, check.skill, check.dc_kind, check.dc_value) == (
        AbilityScore.STRENGTH,
        Skill.ATHLETICS,
        DcKind.FIXED,
        15,
    )
    assert "At the GM's option" in _prose(built, record, key)


def test_flying_falls_unless_it_can_hover(built) -> None:  # type: ignore[no-untyped-def]
    prose = _prose(built, "flying", "falling")
    assert "Incapacitated or Prone condition or your Fly Speed is reduced to 0" in prose
    assert "if you can hover" in prose


def test_burrowing_keeps_its_materials_and_the_solid_rock_exception(built) -> None:  # type: ignore[no-untyped-def]
    prose = _prose(built, "burrow_speed", "burrowing")
    assert "sand, earth, mud, or ice" in prose
    assert "can't burrow through solid rock unless" in prose


# ---------------------------------------------------------------------------
# Negative controls: each is reported by a production check
# ---------------------------------------------------------------------------


def _authoring_findings(session, monkeypatch, **tables) -> list[str]:  # type: ignore[no-untyped-def]
    for name, keep in tables.items():
        monkeypatch.setattr(GEN, name, tuple(filter(keep, getattr(GEN, name))))
    found = GEN.batch_findings(GEN.build(session))
    expected = set(REMAINING + ACCEPTED_CONTEXT)
    return [f for v in found.values() for f in v if f not in expected]


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    found = _authoring_findings(
        session,
        monkeypatch,
        COMPONENTS=lambda c: (c.entry, c.key) != ("concentration", "damage"),
    )
    assert found[0] == (
        "review unit reference-closure/concentration: expected rule "
        "glossary.concentration/damage has no component"
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
    assert _residue(built) == {}


def _violations(built, **draft_changes) -> list[str]:  # type: ignore[no-untyped-def]
    p = built.proposal
    return review_unit_violations(
        p.proposed_review_units,
        dataclasses.replace(p.proposed_representation, **draft_changes),
        p.policy_version,
        built.ledger.spans,
    )


def test_dropping_a_typed_fact_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    components = tuple(
        (
            dataclasses.replace(c, facts=())
            if (c.record_key, c.semantic_key) == ("glossary.speed", "switching")
            else c
        )
        for c in draft.components
    )
    found = _violations(built, components=components)
    assert found and all("speed_switch_limit" in f for f in found), found


def test_dropping_the_governing_exception_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    key = ("glossary.climbing", "extra_cost")
    found = _violations(
        built,
        prose_bindings=tuple(
            b for b in draft.prose_bindings if (b.record_key, b.component_key) != key
        ),
    )
    assert found and all("extra_cost" in f for f in found), found


def test_moving_the_exception_to_a_sibling_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    # The Magic lesson: the Climb Speed exception must govern the surcharge it
    # qualifies, not sit beside it. Rebinding it to the sibling GM check leaves
    # the surcharge's expected source without its exception.
    spans = {s.span_id: s for s in built.ledger.spans}
    draft = built.proposal.proposed_representation

    def moved(b):  # type: ignore[no-untyped-def]
        s = spans[b.span_id]
        text = built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]
        if (b.record_key, b.component_key) == (
            "glossary.climbing",
            "extra_cost",
        ) and text.startswith("You ignore"):
            return dataclasses.replace(b, component_key="difficult_climb")
        return b

    rebound = tuple(map(moved, draft.prose_bindings))
    assert rebound != draft.prose_bindings
    found = _violations(built, prose_bindings=rebound)
    assert found and all("extra_cost" in f for f in found), found


# ---------------------------------------------------------------------------
# Test-only composition with the Conditions + Actions acceptance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _committed(recorded: MechanicalProposal) -> AcceptedInputs:
    """The two-batch acceptance this proposal was offered against.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch. Both sides are the
    superseded release's; its physical source is not available, so the
    compositions below are representation-only and the prose and provenance
    checks that need it are retired.
    """
    inputs = through("actions-pilot")
    assert inputs.oracle.binding == recorded.binding
    return inputs


def test_composed_the_five_close_and_only_out_of_scope_targets_remain(
    recorded: MechanicalProposal,
) -> None:
    inputs = _committed(recorded)
    accepted = inputs.oracle.representation
    proposed = recorded.proposed_representation

    accepted_alone = relationship_and_reference_violations(accepted)
    assert sorted(f for f in accepted_alone if "unknown target" in f) == CLOSING

    composed = dataclasses.replace(
        accepted,
        **{
            f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
            for f in dataclasses.fields(accepted)
        },
    )
    assert sorted(relationship_and_reference_violations(composed)) == REMAINING


def _composed_with(
    recorded: MechanicalProposal, **extra: tuple[object, ...]
) -> list[str]:
    """Test-only composition with *extra* appended to the proposal's fields."""
    inputs = _committed(recorded)
    accepted = inputs.oracle.representation
    proposed = dataclasses.replace(
        recorded.proposed_representation,
        **{
            k: (*getattr(recorded.proposed_representation, k), *v)
            for k, v in extra.items()
        },
    )
    composed = dataclasses.replace(
        accepted,
        **{
            f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
            for f in dataclasses.fields(accepted)
        },
    )
    return sorted(relationship_and_reference_violations(composed))


def _combat_reference(proposal: MechanicalProposal) -> ReferenceDraft:
    (ref,) = [
        r
        for r in proposal.proposed_representation.references
        if r.scope_key != "srd-5.2.1/rules-glossary"
    ]
    return ref


def test_the_combat_pointer_is_a_native_scoped_reference(built) -> None:  # type: ignore[no-untyped-def]
    ref = _combat_reference(built.proposal)
    assert (
        ref.from_record_key,
        ref.from_component_key,
        ref.source_text,
        ref.scope_key,
        ref.target_record_key,
    ) == ("glossary.speed", "", "Combat", "srd-5.2.1/playing-the-game", "play.combat")

    # Read from the same See also span as Speed's five glossary pointers.
    def cited(text: str) -> set[str]:
        return {
            p.span_id
            for p in built.proposal.proposed_representation.provenance
            if p.target_kind.value == "reference"
            and p.target_key[:3] == ("glossary.speed", "", text)
        }

    assert len(cited("Combat")) == 1
    assert cited("Combat") == cited("Climbing")


def test_the_combat_pointer_resolves_only_through_native_target_validation(
    recorded: MechanicalProposal,
) -> None:
    # Authoring the exact target closes exactly that finding and no other.
    stub = RecordDraft(semantic_key="play.combat", kind=RecordKind.GENERAL_RULE)
    assert _composed_with(recorded, records=(stub,)) == [
        f for f in REMAINING if f != COMBAT
    ]
    # A glossary record of the same name is not the target: scope and key are exact.
    near = RecordDraft(semantic_key="glossary.combat", kind=RecordKind.GLOSSARY_RULE)
    assert _composed_with(recorded, records=(near,)) == REMAINING


def test_the_combat_pointer_takes_part_in_scope_and_ambiguity_checks(
    recorded: MechanicalProposal,
) -> None:
    ref = _combat_reference(recorded)
    other = dataclasses.replace(ref, target_record_key="play.actions")
    assert (
        "reference srd-5.2.1/playing-the-game:'Combat': ambiguous — resolves to "
        "['play.actions', 'play.combat']"
    ) in _composed_with(recorded, references=(other,))
    unscoped = dataclasses.replace(ref, scope_key=" ")
    assert "reference  :'Combat': no committed resolution scope" in _composed_with(
        recorded, references=(unscoped,)
    )


# ---------------------------------------------------------------------------
# Shared authoring: the finding count and the emit gate
# ---------------------------------------------------------------------------


def test_a_pointer_held_by_several_records_is_one_finding_each() -> None:
    component = GEN.C("a", "k", GEN.P, GEN.NO_USE, refs=(("T", "t"),))
    refs = (
        ("a", "T", "t", ("x",)),  # stated by a's component: not a second pointer
        ("b", "T", "t", ("x",)),
        ("c", "T", "t", ("x",)),
        ("c", "U", "u", ("x",)),
    )
    assert (
        unknown_target_findings(refs, (component,), ("t",))
        == ["reference srd-5.2.1/rules-glossary:'T': unknown target record glossary.t"]
        * 3
    )


def test_a_pointer_out_of_the_glossary_names_its_exact_scope_and_target() -> None:
    target = ("srd-5.2.1/playing-the-game", "play.combat")
    refs = (("a", "Combat", target, ("x",)), ("a", "Combat", "combat", ("x",)))
    assert unknown_target_findings(refs, (), (target,)) == [
        "reference srd-5.2.1/playing-the-game:'Combat': unknown target record "
        "play.combat"
    ]


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
    with pytest.raises(ValueError, match="play.combat"):
        emit(str(source_release_db), lambda _s: built, refused, expected[1:])
    assert not refused.exists()
