"""The ``combat-damage-breaking`` proposal, as it is offered for review — CRD Issue 5d.

Three whole *Playing the Game* sections -- Combat, Damage and Healing, and
Exploration's Breaking Objects -- plus the Rules Glossary's Breaking Objects
and Damage Threshold entries, proposed by
``.claude/review-notes/issue-5d-combat-damage-breaking-generator.py`` from the
release 5c actually publishes. Nothing here accepts it; the Owner's acceptance
is recorded by the replacement chain
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``) and held by
``test_combat_damage_breaking_acceptance``.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* the batch checks report exactly the out-of-batch targets and nothing else;
* the review-sensitive meanings (Cover, the mount save, the underwater rules,
  object immunities, restatements kept untyped) read back from the proposal;
* omissions are reported, every word of every spanned leaf is claimed, and a
  whole leaf of example or pointer is accounted for by a supporting group; and
* composed *in this test only* with the six-batch acceptance it was offered
  against (re-derived by its script, since the committed artifact now also
  holds this batch), the
  three targets it cites close and only the five named outstanding targets
  and the three printed chapter pointers with no destination record remain,
  while exactly the batch's 168 leaves gain coverage. Both sides are the
  superseded release's; its physical source is not available, so the
  composition is checked without a corpus: its uncovered-leaf counts are
  retired, while native acceptance, which needs none, still reports exactly
  each proposed span's missing approval and none for the accepted prior
  (``correction-followup.md``).
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.accounting import validate_acceptance
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
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    AbilityCheckFact,
    AbilityScore,
    ApplicabilityKind,
    AutomaticOutcome,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    CoverDegree,
    CoverProvisionFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageType,
    DcKind,
    MovementAmount,
    MovementCostFact,
    ProvenanceTargetKind,
    RollContext,
    fact_key,
    reference_target_key,
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
from tests.ingestion.mechanical._schema_pins import lifted

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-combat-damage-breaking-generator.py"
BATCH = "combat-damage-breaking"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
#: What the committed acceptance leaves unresolved: the three targets closed here.
CLOSED = sorted(
    [f"reference {PLAY}:'Combat': unknown target record play.combat"] * 4
    + [
        f"reference {PLAY}:'Damage and Healing': unknown target record "
        "play.damage_and_healing"
    ]
    * 5
    + [
        f"reference {GLOSSARY}:'Breaking Objects': unknown target record "
        "glossary.breaking_objects"
    ]
)


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


#: The printed pointers into parts no record exists for yet: (record,
#: component, printed text, scope). Each is a real reference with no target.
UNRESOLVED = [
    ("play.combat", "attack_structure", "Playing the Game", PLAY),
    (
        "play.damage_and_healing",
        RECORD_OWNED_REFERENCE,
        "Equipment",
        "srd-5.2.1/equipment",
    ),
    ("play.damage_and_healing", RECORD_OWNED_REFERENCE, "Spells", "srd-5.2.1/spells"),
]

#: What remains once composed: the five outstanding targets, each citation, and
#: the three unresolved pointers.
OUTSTANDING = sorted(
    [
        f"reference {scope}:{text!r}: unresolved reference"
        for _, _, text, scope in UNRESOLVED
    ]
    + [
        f"reference {PLAY}:'Actions': unknown target record play.actions",
        _glossary("Damage types", "damage_types"),
        _glossary("dead", "dead"),
        _glossary("Long Rests", "long_rest"),
        _glossary("Short", "short_rest"),
        _glossary("Short Rest", "short_rest"),
    ]
    + [_glossary("Long Rest", "long_rest")] * 3
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("combat_damage_breaking", GENERATOR)
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
        if (c.record_key, c.semantic_key) == (record, key)
    ]
    return c


PRONE = ConditionEffectFact(ConditionKind.PRONE, ConditionEffectKind.APPLIES)


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


def test_scope_is_three_whole_sections_and_two_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, len(u.leaf_ids)) for u in units] == [
        ("combat-damage-breaking/exploration_breaking_objects", 3),
        ("combat-damage-breaking/combat", 90),
        ("combat-damage-breaking/damage_and_healing", 64),
        ("combat-damage-breaking/breaking_objects", 9),
        ("combat-damage-breaking/damage_threshold", 2),
    ]
    assert [u.kind for u in units] == [ReviewUnitKind.SECTION] * 3 + [
        ReviewUnitKind.ENTRY
    ] * 2
    assert [r.semantic_key for r in built.proposal.proposed_representation.records] == [
        "play.exploration.breaking_objects",
        "play.combat",
        "play.damage_and_healing",
        "glossary.breaking_objects",
        "glossary.damage_threshold",
    ]


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    # In-batch pointers resolve: none of the three closed targets is unknown.
    assert not {f for f in found["representation"] if f in set(CLOSED)}


# ---------------------------------------------------------------------------
# Review-sensitive meanings
# ---------------------------------------------------------------------------


def test_cover_is_typed_from_its_table_and_prose(built) -> None:  # type: ignore[no-untyped-def]
    degrees = _component(built, "play.combat", "cover_degrees")
    assert degrees.handling is ComponentHandling.STRUCTURED
    provisions = [f for f in degrees.facts if isinstance(f, CoverProvisionFact)]
    assert [p.degree for p in provisions] == [
        CoverDegree.HALF,
        CoverDegree.THREE_QUARTERS,
        CoverDegree.TOTAL,
    ]
    assert len(degrees.facts) == 6
    for key in ("cover_origin", "cover_selection"):
        assert len(_component(built, "play.combat", key).facts) == 1


def test_falling_off_a_mount_is_prone_only_on_a_failed_save(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "play.combat", "falling_off")
    save, prone = c.facts
    assert isinstance(save, AbilityCheckFact)
    assert (save.ability, save.dc_kind, save.context, save.dc_value) == (
        AbilityScore.DEXTERITY,
        DcKind.FIXED,
        RollContext.SAVING_THROW,
        10,
    )
    assert prone == PRONE
    (q,) = c.fact_qualifiers
    assert q.fact_key == fact_key(PRONE)
    assert q.applies_when.kind is ApplicabilityKind.ROLL_OUTCOME
    assert q.applies_when.outcome is AutomaticOutcome.FAILURE


def test_mounting_costs_half_speed_rounded_down(built) -> None:  # type: ignore[no-untyped-def]
    (cost,) = _component(built, "play.combat", "mounting").facts
    assert isinstance(cost, MovementCostFact)
    assert cost.amount is MovementAmount.HALF_SPEED


def test_underwater_fire_resistance_points_at_this_batchs_section(built) -> None:  # type: ignore[no-untyped-def]
    (resist,) = _component(built, "play.combat", "underwater_fire").facts
    assert resist == DamageResponseFact(
        DamageResponseKind.RESISTANCE, damage_type=DamageType.FIRE
    )
    targets = {
        r.target_record_key
        for r in built.proposal.proposed_representation.references
        if r.from_component_key == "underwater_fire"
    }
    assert targets == {"glossary.resistance", "play.damage_and_healing"}


def test_objects_are_immune_to_poison_and_psychic(built) -> None:  # type: ignore[no-untyped-def]
    facts = _component(built, "glossary.breaking_objects", "object_immunities").facts
    assert {(f.response, f.damage_type) for f in facts} == {
        (DamageResponseKind.IMMUNITY, DamageType.POISON),
        (DamageResponseKind.IMMUNITY, DamageType.PSYCHIC),
    }


def test_restatements_of_accepted_typed_rules_stay_untyped(built) -> None:  # type: ignore[no-untyped-def]
    # One typed copy per rule: the accepted glossary record owns the fact.
    for record, key in [
        ("play.combat", "surprise"),
        ("play.combat", "difficult_terrain"),
        ("play.damage_and_healing", "resistance_and_vulnerability"),
        ("play.damage_and_healing", "immunity"),
    ]:
        c = _component(built, record, key)
        assert c.handling is ComponentHandling.PROSE_BOUND and c.facts == ()


def test_the_breaking_objects_pointers_resolve_inside_the_batch(built) -> None:  # type: ignore[no-untyped-def]
    refs = {
        (r.from_record_key, r.source_text, r.target_record_key)
        for r in built.proposal.proposed_representation.references
    }
    assert (
        "play.exploration.breaking_objects",
        "breaking objects",
        "glossary.breaking_objects",
    ) in refs
    assert (
        "glossary.breaking_objects",
        "Damage Threshold",
        "glossary.damage_threshold",
    ) in refs


def test_printed_chapter_pointers_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    # "as detailed earlier in 'Playing the Game'" is part of the governing
    # attack clause; "See 'Equipment' ... and 'Spells'" is the damage-dice
    # pointer. Both are cited, from the span that prints them, with no target.
    representation = built.proposal.proposed_representation
    refs = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): r
        for r in representation.references
    }
    cited: dict[tuple[str, ...], set[str]] = {}
    for c in representation.provenance:
        if c.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(c.target_key, set()).add(c.span_id)
    (attack,) = [
        t
        for _, k, _, ts in GEN.CLAUSES
        if k == "attack_structure"
        for t in ts
        if '"Playing the Game."' in t
    ]
    printed = {
        "Playing the Game": built.spans[("combat", attack)].span_id,
        "Equipment": built.spans[("damage_and_healing", GEN.DICE_POINTER)].span_id,
        "Spells": built.spans[("damage_and_healing", GEN.DICE_POINTER)].span_id,
    }
    for key in UNRESOLVED:
        ref = refs[key]
        assert ref.target_record_key == ""
        assert cited[reference_target_key(ref)] == {printed[key[2]]}
    findings = GEN.expected_representation_findings()
    assert [f for f in findings if f.endswith("unresolved reference")] == sorted(
        f"reference {scope}:{text!r}: unresolved reference"
        for _, _, text, scope in UNRESOLVED
    )


MARCHING_RULES = [t for e, k, _, ts in GEN.CLAUSES if k == "marching_order" for t in ts]


def test_the_marching_order_sidebar_is_authored_whole(built) -> None:  # type: ignore[no-untyped-def]
    # A travel rule the release prints beside Breaking Objects: its meaning is
    # kept, not excluded as off-topic.
    c = _component(built, "play.exploration.breaking_objects", "marching_order")
    assert c.handling is ComponentHandling.PROSE_BOUND
    bound = {
        b.span_id
        for b in built.proposal.proposed_representation.prose_bindings
        if b.component_key == "marching_order"
    }
    assert bound == {
        built.spans[("exploration_breaking_objects", t)].span_id for t in MARCHING_RULES
    }
    assert any(
        t.startswith("You can change your marching order") for t in MARCHING_RULES
    )


def test_only_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    # An excluded leaf counts as reviewed with nothing authored, so only a
    # heading that states no rule may be one.
    excluded = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert len(excluded) == 54
    assert all(c.startswith("#") and "\n" not in c for c in excluded)


def test_a_dropped_marching_order_leaves_its_leaf_unaccounted(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    for name, keep in [
        ("CLAUSES", lambda r: r[1] != "marching_order"),
        ("COMPONENTS", lambda r: r.key != "marching_order"),
        ("SUPPORTING", lambda r: r[2] != "marching_order"),
    ]:
        monkeypatch.setattr(GEN, name, tuple(filter(keep, getattr(GEN, name))))
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith(
        "review unit combat-damage-breaking/exploration_breaking_objects: leaf "
    )
    assert found.endswith(
        "named by no expected rule, supporting group or excluded group"
    )


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
    (example,) = [t for e, t, k in GEN.SUPPORTING if k == "surprise"]
    monkeypatch.setattr(
        GEN, "SUPPORTING", tuple(s for s in GEN.SUPPORTING if s[2] != "surprise")
    )
    assert list(_residue(GEN.build(session)).values()) == [example]


def test_a_dropped_rule_leaves_its_leaf_unaccounted(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(GEN, "CLAUSES", tuple(c for c in GEN.CLAUSES if c[1] != "ties"))
    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(c for c in GEN.COMPONENTS if c.key != "ties")
    )
    (found,) = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found.startswith("review unit combat-damage-breaking/combat: leaf ")
    assert found.endswith(
        "named by no expected rule, supporting group or excluded group"
    )


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(c for c in GEN.COMPONENTS if c.key != "stabilizing")
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit combat-damage-breaking/damage_and_healing: expected rule "
        "play.damage_and_healing/stabilizing has no component"
    ) in found


def test_a_whole_supporting_leaf_is_accounted_by_its_group(  # type: ignore[no-untyped-def]
    session, built, monkeypatch
) -> None:
    (unit,) = [
        u
        for u in built.proposal.proposed_review_units
        if u.unit_id.endswith("/damage_and_healing")
    ]
    (worked,) = [g for g in unit.supporting_groups if g.supports_component_key]
    assert worked.supports_component_key == "order_of_application"
    # Glossary entries hold every example beside a clause: no extra group.
    assert all(
        not u.supporting_groups
        for u in built.proposal.proposed_review_units
        if "breaking_objects" in u.unit_id or "threshold" in u.unit_id
    )
    monkeypatch.setattr(
        GEN,
        "SUPPORTING",
        tuple(s for s in GEN.SUPPORTING if s[2] != "order_of_application"),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found == [
        "review unit combat-damage-breaking/damage_and_healing: leaf "
        f"{worked.leaf_ids[0]} is reviewed by this unit but named by no expected "
        "rule, supporting group or excluded group"
    ]


def test_an_excluded_heading_must_match_exactly(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # "#### Range" must not also claim "#### Ranged Attacks in Close Combat".
    monkeypatch.setattr(
        GEN,
        "EXCLUDED",
        tuple(
            (e, tuple(c.replace("#### Range", "#### Rang") for c in cs), r)
            for e, cs, r in GEN.EXCLUDED
        ),
    )
    with pytest.raises(ValueError, match="matches 0 leaves"):
        GEN.build(session)


# ---------------------------------------------------------------------------
# Test-only composition with the acceptance it was offered against
# ---------------------------------------------------------------------------


def _prior() -> AcceptedInputs:
    """The six-batch acceptance this proposal was offered against.

    The approved replacement chain through the previous batch, not the
    committed artifact, which also holds this batch.
    """
    inputs: AcceptedInputs = through("damage-and-hit-points")
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


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
    # The effective representation's own relationship and reference findings:
    # no corpus, so none of the superseded release's is needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


def test_composed_the_three_targets_close_and_168_leaves_gain_coverage(
    recorded: MechanicalProposal,
) -> None:
    inputs = _prior()
    assert inputs.oracle.binding == recorded.binding
    assert len(inputs.oracle.representation.records) == 62
    assert len(inputs.oracle.spans) == 268
    assert IDENTITY not in {b.proposal_identity for b in inputs.batches}
    proposed = recorded.proposed_representation
    accepted = inputs.oracle.representation
    assert not {r.semantic_key for r in accepted.records} & {
        r.semantic_key for r in proposed.records
    }
    spans = tuple(p.span for p in recorded.proposed_spans)
    assert len(spans) == 162
    assert not {s.span_id for s in inputs.oracle.spans} & {s.span_id for s in spans}

    oracle = inputs.oracle
    composed = dataclasses.replace(
        oracle,
        spans=(*oracle.spans, *spans),
        review_units=(*oracle.review_units, *recorded.proposed_review_units),
        representation=dataclasses.replace(
            accepted,
            **{
                f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
                for f in dataclasses.fields(accepted)
            },
        ),
    )
    together = dataclasses.replace(inputs, oracle=composed)

    assert sorted(_references(inputs)) == CLOSED
    # Unfiltered and representation-only: only the outstanding targets remain.
    assert sorted(_references(together)) == OUTSTANDING
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(inputs) == []
    assert _acceptance(together) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(together) - _covered(inputs) == mine
    assert len(mine) == 168
