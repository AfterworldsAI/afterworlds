"""The Proficiency section's typed rule inputs — CRD Issue 5d (#137).

Schemas 14 and 15, kept in one module because they type one section: 14 minted
the three inputs below, and 15 minted the fourth after a source review found two
stated uses of the bonus still sitting in prose. Splitting them would give the
same section two suites that have to agree about the same draft.

Schema 13 gave the *Playing the Game > Proficiency* section its one numeric
input, the bonus band. Schema 14 gives it the three the Rules Package still
could not state: **where** the bonus applies, **how many times** each arithmetic
operation may touch it and in what order, and the **conjunction** that grants
Advantage on a tool-and-skill check.

**What each field is for, and what its absence would cost.**

* ``ProficiencyApplicationFact`` pairs a proficiency kind with the roll the
  section says it is added to. Without it the four printed sentences collapse
  into one umbrella permission, and nothing in the corpus distinguishes *"add
  your Proficiency Bonus to attack rolls with weapons you're proficient with"*
  from a bonus on any roll at all. The pairing is closed by
  ``_PROFICIENCY_APPLICATION_ROLLS``, so a combination the section never prints
  cannot be authored.
* ``ProficiencyBonusOperationLimitFact`` carries *"don't add it more than
  once"*, *"don't multiply it more than once"* and *"don't divide it more than
  once"*, plus the printed order — a multiplication or division happens
  **before** the addition. Without the limits a consumer has no statement that
  stacking is bounded; without ``precedes`` it has no statement of which
  arithmetic runs first, and halving after adding is a different number from
  adding after halving.
* ``AdvantageFact.requires_proficiencies`` carries the section's one
  conjunction: *"if you have proficiency in a skill and a tool that both apply
  to a check, you have Advantage"*. The consequence is deterministic and stays
  deterministic; what is discretionary is only whether both apply, and that
  judgment belongs to the GameMaster. So the requirement is represented and the
  relevance is not, and the fact is **not** moved to discretionary handling
  merely because a human decides the antecedent.
* ``ProficiencyBonusUseFact`` carries the two uses the section's opening
  paragraph states without pairing either to a proficiency kind: *"The bonus is
  also used for spell attacks and for calculating the DC of saving throws for
  spells."* Neither is an application — that sentence names no proficiency, and
  a spell save DC is not a roll — so schema 15 mints a family rather than
  widening one. Without it the corpus states where the bonus applies in four
  places and stays silent about the two the same paragraph prints.

**What is deliberately not here.** Nothing evaluates a roll, sums a bonus,
halves anything or decides relevance. Which proficiencies a creature has is
character state and lives on the sheet, never in this corpus. No adapter, sheet
model or runtime judgment is implemented by these mints, and nothing in this
module accepts the proposal or publishes anything. Neither bonus use carries a
formula, an ability, a target DC, a spellcasting proficiency or a consumer: the
source states that the bonus is used there, and that is the whole of what is
represented.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import get_args
from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import load_proposal
from afterworlds.ingestion.mechanical.representation import (
    _FACT_TYPES,
    AdvantageFact,
    AdvantageState,
    ComponentHandling,
    FactFamily,
    MalformedFactPayloadError,
    MechanicalFact,
    ProficiencyApplicationFact,
    ProficiencyBonusOperation,
    ProficiencyBonusOperationLimitFact,
    ProficiencyBonusUse,
    ProficiencyBonusUseFact,
    ProficiencyKind,
    ProvenanceRole,
    ProvenanceTargetKind,
    RollActor,
    RollContext,
    RollSpec,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    fact_target_key,
    introduction_manifest,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_13_HASH,
    SCHEMA_13_VERSION,
    SCHEMA_14_HASH,
    SCHEMA_14_VERSION,
    SCHEMA_15_VERSION,
    lift_path,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.orm.mechanical import MechanicalFactORM
from afterworlds.services.rules_authority.application import (
    OverrideApplicationError,
    _base_records,
    apply_override_set,
)
from afterworlds.services.rules_authority.binding import RulesPackageBinding
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    patch_from_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.ingestion.mechanical.conftest import NOW, RELEASE_BINDING, candidate_of
from tests.ingestion.mechanical.test_proficiency_1_proposal import _corpus

PROPOSAL_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-batch-proficiency-1-PROPOSAL.json"
)

#: The committed accepted authority — the seven accepted batches — read here
#: only to prove the widened ``AdvantageFact`` left every one of them alone.
ACCEPTED_AUTHORITY_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

RECORD = "play.proficiency"

#: ``component key -> (kind, the roll the section says it applies to)``, written
#: out from the four printed sentences rather than read back off the draft. A
#: draft that paired ``weapon`` with a saving throw would satisfy a derived
#: expectation and fail this one.
PRINTED_APPLICATIONS = {
    "skill_proficiency_application": (
        ProficiencyKind.SKILL,
        RollContext.ABILITY_CHECK,
    ),
    "saving_throw_proficiency": (
        ProficiencyKind.SAVING_THROW,
        RollContext.SAVING_THROW,
    ),
    "weapon_proficiency": (ProficiencyKind.WEAPON, RollContext.ATTACK_ROLL),
    "tool_proficiency": (ProficiencyKind.TOOL, RollContext.ABILITY_CHECK),
}

#: ``(operation, maximum applications, what it precedes)``, as printed. The
#: addition precedes nothing; the two scaling operations precede it.
PRINTED_LIMITS = {
    (ProficiencyBonusOperation.ADD, 1, None),
    (ProficiencyBonusOperation.MULTIPLY, 1, ProficiencyBonusOperation.ADD),
    (ProficiencyBonusOperation.DIVIDE, 1, ProficiencyBonusOperation.ADD),
}

#: The conjunction the tool sentence states, in canonical order.
PRINTED_CONJUNCTION = (ProficiencyKind.SKILL, ProficiencyKind.TOOL)

#: The two uses the opening paragraph states, written out from the sentence
#: rather than read back off the draft: *"The bonus is also used for spell
#: attacks and for calculating the DC of saving throws for spells."* Dropping
#: either one, or adding a third the sentence never prints, fails against this.
PRINTED_BONUS_USES = {
    ProficiencyBonusUse.SPELL_ATTACK,
    ProficiencyBonusUse.SPELL_SAVE_DC,
}

#: The component the two uses hang on — the section's umbrella paragraph, which
#: keeps its prose because the umbrella itself is not reduced to these facts.
BONUS_USE_COMPONENT = "proficiency_bonus_application"

SCHEMA_14_FAMILIES = (
    FactFamily.PROFICIENCY_APPLICATION,
    FactFamily.PROFICIENCY_BONUS_OPERATION_LIMIT,
)

SCHEMA_15_FAMILIES = (FactFamily.PROFICIENCY_BONUS_USE,)

#: Every family these two mints made statable. The split above is what the
#: declaration tests need — each schema's manifest rows are its own — and this
#: union is what the round-trip, provenance, consumer and identity tests walk,
#: so a family added to one mint is covered by all of them without a second
#: suite.
NEW_FAMILIES = SCHEMA_14_FAMILIES + SCHEMA_15_FAMILIES


def _proposal():  # type: ignore[no-untyped-def]
    return load_proposal(PROPOSAL_PATH)


def _draft():  # type: ignore[no-untyped-def]
    return _proposal().proposed_representation


def _ledger(proposal) -> ClassificationLedger:  # type: ignore[no-untyped-def]
    """The proposal's own spans, under the release and policy it declares."""
    return ClassificationLedger(
        package_uuid=proposal.binding.package_uuid,
        release_version=proposal.binding.release_version,
        policy_version=proposal.policy_version,
        policy_hash=proposal.policy_hash,
        spans=tuple(p.span for p in proposal.proposed_spans),
        batches=(),
        acceptances=(),
    )


def _candidate(proposal=None, draft=None):  # type: ignore[no-untyped-def]
    """The proposal's own content, under the fixture release this suite seeds.

    The binding is the seeded one rather than the proposal's: persistence has a
    foreign key onto the published release, and this module is about the
    representation contract, not about which release the batch was read from.
    """
    proposal = proposal if proposal is not None else _proposal()
    ledger = dataclasses.replace(
        _ledger(proposal),
        package_uuid=RELEASE_BINDING.package_uuid,
        release_version=RELEASE_BINDING.release_version,
    )
    return candidate_of(
        RELEASE_BINDING,
        ledger,
        draft if draft is not None else proposal.proposed_representation,
    )


def _component(draft, semantic_key):  # type: ignore[no-untyped-def]
    (component,) = [c for c in draft.components if c.semantic_key == semantic_key]
    return component


def _application(draft, semantic_key) -> ProficiencyApplicationFact:  # type: ignore[no-untyped-def]
    (fact,) = [
        f
        for f in _component(draft, semantic_key).facts
        if isinstance(f, ProficiencyApplicationFact)
    ]
    return fact


def _tool_advantage(draft) -> AdvantageFact:  # type: ignore[no-untyped-def]
    (fact,) = [
        f
        for f in _component(draft, "tool_proficiency").facts
        if isinstance(f, AdvantageFact)
    ]
    return fact


def _bonus_uses(draft) -> list[ProficiencyBonusUseFact]:  # type: ignore[no-untyped-def]
    return [
        f
        for f in _component(draft, BONUS_USE_COMPONENT).facts
        if isinstance(f, ProficiencyBonusUseFact)
    ]


def _new_facts(draft):  # type: ignore[no-untyped-def]
    """Every fact this mint made statable, with the component that holds it."""
    return [
        (component.semantic_key, fact)
        for component in draft.components
        for fact in component.facts
        if fact.FAMILY in NEW_FAMILIES
        or (isinstance(fact, AdvantageFact) and fact.requires_proficiencies)
    ]


_PACKAGE_BINDING = RulesPackageBinding(
    package_uuid=uuid5(NAMESPACE_URL, "pkg-proficiency-1"),
    release_version="rel-proficiency-1",
    mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-proficiency-1"),
    override_set_uuid=uuid5(NAMESPACE_URL, "ovs-proficiency-1"),
)


# ---------------------------------------------------------------------------
# What the mint declares
# ---------------------------------------------------------------------------


def test_the_declared_union_is_exactly_the_families_the_builder_knows() -> None:
    """A family reachable by one seam and not the other is a silent hole.

    ``MechanicalFact`` is what every consumer annotation and every ``isinstance``
    narrowing reads; ``_FACT_TYPES`` is what the payload builder dispatches on.
    A mint that extends one and forgets the other leaves a family that either
    cannot be typed or cannot be built, and no existing test asks the two to
    agree.
    """
    assert set(get_args(MechanicalFact)) == set(_FACT_TYPES.values())


def test_no_vocabulary_member_row_is_rendered_without_its_closure() -> None:
    """Every member row names the whole value set it belongs to, or none does.

    The manifest identifies a vocabulary by its complete admitted value set,
    because no payload carries a type tag and identity may not depend on what a
    payload cannot show. A mint that registers members without extending the
    rendering table gets rows with a null value set — well-formed, covered by
    the schema hash, and stating that the vocabulary admits nothing. This is the
    detector for that, across the whole manifest rather than this schema's rows.
    """
    members = [
        row for row in introduction_manifest() if row["kind"] == "vocabulary_member"
    ]
    assert members
    assert all(row["vocabulary"] for row in members), [
        row["name"] for row in members if not row["vocabulary"]
    ]


def test_the_mint_declares_two_families_and_two_whole_vocabularies() -> None:
    """The extension claim, stated where the schema hash covers it.

    Both vocabularies are minted whole, so each member row carries the complete
    closure rather than a widening of something an earlier schema had. A third
    family, a widened accepted vocabulary or a member that arrives without its
    closure would land a row here and fail.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_14_VERSION
    ]
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows
    assert {row["name"] for row in rows if row["kind"] == "fact_family"} == {
        family.value for family in SCHEMA_14_FAMILIES
    }

    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    kinds = tuple(sorted(kind.value for kind in ProficiencyKind))
    operations = tuple(sorted(op.value for op in ProficiencyBonusOperation))
    assert {row["name"] for row in members} == set(kinds) | set(operations)
    for row in members:
        expected = kinds if row["name"] in kinds else operations
        assert tuple(row["vocabulary"]) == expected, row

    # ``requires_proficiencies`` is a post-schema-3 *field* on a family schema 3
    # already had. Its legality is the field registry's, not the manifest's, so
    # it deliberately has no row of its own.
    assert "requires_proficiencies" not in {row["name"] for row in rows}


def test_the_later_mint_declares_one_family_and_one_whole_vocabulary() -> None:
    """The second mint's claim, in the same place and on the same terms.

    Schema 15 adds exactly one family and the vocabulary minted with it. A row
    here for anything else — a second family, a member of an accepted
    vocabulary widened to carry a spell use, a member arriving without its
    closure — is the detector for a mint that grew past the sentence it was
    read from.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_15_VERSION
    ]
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows
    assert {row["name"] for row in rows if row["kind"] == "fact_family"} == {
        family.value for family in SCHEMA_15_FAMILIES
    }

    uses = tuple(sorted(use.value for use in ProficiencyBonusUse))
    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    assert {row["name"] for row in members} == set(uses)
    for row in members:
        assert tuple(row["vocabulary"]) == uses, row


def test_the_crossing_from_schema_13_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_13_VERSION, SCHEMA_13_HASH),
        (SCHEMA_14_VERSION, SCHEMA_14_HASH),
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-13-to-14"]


# ---------------------------------------------------------------------------
# What the section prints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("component_key", "kind", "context"),
    [(key, kind, context) for key, (kind, context) in PRINTED_APPLICATIONS.items()],
    ids=list(PRINTED_APPLICATIONS),
)
def test_each_printed_sentence_pairs_its_proficiency_with_its_own_roll(
    component_key: str, kind: ProficiencyKind, context: RollContext
) -> None:
    """Four sentences, four pairs, and no creature-specific fact among them.

    The roll belongs to the proficient creature, and that is all the fact says
    about who is rolling. Which skill, which ability and which weapon are
    character state; a fact naming one would be a sheet fact living in the
    rules corpus.
    """
    fact = _application(_draft(), component_key)
    assert fact.proficiency is kind
    assert fact.roll.context is context
    assert fact.roll.actor is RollActor.SUBJECT
    assert fact.roll.skill is None
    assert fact.roll.ability is None
    assert fact_invariant_violations(fact) == ()
    assert set(fact_payload(fact)) == {"family", "proficiency", "roll"}


def test_the_four_applications_are_the_whole_of_what_the_section_states() -> None:
    """No fifth pairing, and no printed one missing."""
    draft = _draft()
    assert {
        (fact.proficiency, fact.roll.context)
        for _, fact in _new_facts(draft)
        if isinstance(fact, ProficiencyApplicationFact)
    } == set(PRINTED_APPLICATIONS.values())


def test_the_three_limits_keep_the_printed_counts_and_the_printed_order() -> None:
    """*"more than once"* three times, and the order the two scalings run in.

    ``precedes`` is the half a count alone cannot state. Halving a bonus and
    then adding it is a different number from adding it and then halving, so a
    limit without the order would leave the arithmetic underdetermined while
    looking complete.
    """
    component = _component(_draft(), "bonus_does_not_stack")
    limits = [
        f for f in component.facts if isinstance(f, ProficiencyBonusOperationLimitFact)
    ]
    assert {(f.operation, f.maximum_applications, f.precedes) for f in limits} == (
        PRINTED_LIMITS
    )
    for fact in limits:
        assert fact_invariant_violations(fact) == ()
        assert set(fact_payload(fact)) == {
            "family",
            "operation",
            "maximum_applications",
            "precedes",
        }


def test_the_tool_advantage_states_both_halves_of_its_condition() -> None:
    """*"proficiency in a skill and a tool that both apply"* — a conjunction.

    The requirement is explicit and the consequence stays exactly what the
    source prints: Advantage on the check, deterministically, once both
    proficiencies are held and the GameMaster judges both relevant. Nothing
    here makes the Advantage unconditional, and nothing here moves it to
    discretionary handling because the antecedent needs judgment.
    """
    draft = _draft()
    fact = _tool_advantage(draft)
    assert fact.requires_proficiencies == PRINTED_CONJUNCTION
    assert fact.state is AdvantageState.ADVANTAGE
    assert fact.roll.context is RollContext.ABILITY_CHECK
    assert fact.roll.actor is RollActor.SUBJECT
    assert fact_invariant_violations(fact) == ()

    # The relevance judgment is what stays with the GameMaster, so the
    # component keeps its prose beside the typed condition rather than being
    # reduced to it.
    component = _component(draft, "tool_proficiency")
    assert component.handling is ComponentHandling.MIXED
    assert [b for b in draft.prose_bindings if b.component_key == "tool_proficiency"]


def test_the_two_bonus_uses_are_the_whole_of_what_the_paragraph_states() -> None:
    """*"also used for spell attacks and for calculating the DC …"* — two uses.

    The expectation is the sentence, written out above rather than derived from
    the draft: a draft that dropped the save DC and kept the attack, or that
    grew a third use, satisfies a derived check and fails this one. Both uses
    come off one clause, and ``ExpectedRule`` detects a *family* missing from a
    span, so this is where per-use omission is actually caught.

    Nothing else is asserted about either use, because the source says nothing
    else: no formula, no ability, no target DC, no proficiency that grants it.
    """
    draft = _draft()
    uses = _bonus_uses(draft)
    assert {fact.use for fact in uses} == PRINTED_BONUS_USES
    assert len(uses) == len(PRINTED_BONUS_USES)
    for fact in uses:
        assert fact_invariant_violations(fact) == ()
        assert set(fact_payload(fact)) == {"family", "use"}

    # The umbrella paragraph states more than these two uses, so it keeps its
    # prose beside them rather than being reduced to them.
    component = _component(draft, BONUS_USE_COMPONENT)
    assert component.handling is ComponentHandling.MIXED
    assert [b for b in draft.prose_bindings if b.component_key == BONUS_USE_COMPONENT]

    # And neither use was smuggled in as an application: that would name a
    # proficiency kind the sentence does not name, and a save DC is not a roll.
    assert not [f for f in component.facts if isinstance(f, ProficiencyApplicationFact)]


def test_every_new_fact_round_trips_through_the_canonical_payload() -> None:
    """Serialization is the wire, so every new shape crosses it and comes back."""
    for component_key, fact in _new_facts(_draft()):
        payload = fact_payload(fact)
        rebuilt = fact_from_payload(payload)
        assert rebuilt == fact, component_key
        assert fact_payload(rebuilt) == payload, component_key


# ---------------------------------------------------------------------------
# Typed validation: one case per refusing branch
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        (
            ProficiencyApplicationFact(
                proficiency=ProficiencyKind.WEAPON,
                roll=RollSpec(
                    actor=RollActor.SUBJECT, context=RollContext.SAVING_THROW
                ),
            ),
            "is stated as applying to attack_roll, not saving_throw",
        ),
        (
            ProficiencyApplicationFact(
                proficiency=ProficiencyKind.SKILL,
                roll=RollSpec(
                    actor=RollActor.AGAINST_SUBJECT,
                    context=RollContext.ABILITY_CHECK,
                ),
            ),
            "applies to the proficient creature's own roll",
        ),
        (
            ProficiencyBonusOperationLimitFact(
                operation=ProficiencyBonusOperation.ADD,
                maximum_applications=0,
                precedes=None,
            ),
            "forbids the operation outright",
        ),
        (
            ProficiencyBonusOperationLimitFact(
                operation=ProficiencyBonusOperation.MULTIPLY,
                maximum_applications=1,
                precedes=ProficiencyBonusOperation.MULTIPLY,
            ),
            "is stated as preceding itself",
        ),
        (
            AdvantageFact(
                state=AdvantageState.ADVANTAGE,
                roll=RollSpec(
                    actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK
                ),
                requires_proficiencies=(
                    ProficiencyKind.TOOL,
                    ProficiencyKind.SKILL,
                ),
            ),
            "not in canonical order",
        ),
        (
            AdvantageFact(
                state=AdvantageState.ADVANTAGE,
                roll=RollSpec(
                    actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK
                ),
                requires_proficiencies=(
                    ProficiencyKind.TOOL,
                    ProficiencyKind.TOOL,
                ),
            ),
            "repeats a proficiency kind",
        ),
        (
            AdvantageFact(
                state=AdvantageState.ADVANTAGE,
                roll=RollSpec(
                    actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK
                ),
                requires_proficiencies=(ProficiencyKind.TOOL,),
            ),
            "a conjunction of one",
        ),
    ],
    ids=[
        "weapon-on-a-save",
        "not-the-subjects-roll",
        "zero-applications",
        "precedes-itself",
        "out-of-order",
        "repeated-kind",
        "conjunction-of-one",
    ],
)
def test_a_well_typed_fact_that_states_nothing_printed_is_refused(
    fact: MechanicalFact, expected: str
) -> None:
    """Every case here rebuilds without complaint; what is wrong is the meaning."""
    violations = fact_invariant_violations(fact)
    assert violations
    assert any(expected in v for v in violations), violations


@pytest.mark.parametrize(
    ("component_key", "field", "value", "expected"),
    [
        ("skill_proficiency_application", "proficiency", "expertise", "proficiency"),
        ("bonus_does_not_stack", "maximum_applications", True, "maximum_applications"),
        ("bonus_does_not_stack", "operation", "subtract", "operation"),
        ("bonus_does_not_stack", "precedes", "subtract", "precedes"),
        (BONUS_USE_COMPONENT, "use", "spell_damage", "use"),
    ],
    ids=[
        "unknown-kind",
        "bool-count",
        "unknown-operation",
        "unknown-precedes",
        "unknown-use",
    ],
)
def test_a_payload_field_outside_its_closure_is_refused_at_the_builder(
    component_key: str, field: str, value: object, expected: str
) -> None:
    """``bool`` matters on its own: ``isinstance(True, int)`` is true in Python."""
    fact = next(
        f
        for key, f in _new_facts(_draft())
        if key == component_key and field in (fact_payload(f))
    )
    payload = dict(fact_payload(fact)) | {field: value}
    with pytest.raises(MalformedFactPayloadError) as raised:
        fact_from_payload(payload)
    assert expected in str(raised.value)


#: Every shape a *present* ``requires_proficiencies`` can take that is not a
#: list of kinds. The falsy four are the ones a truthiness test silently erases:
#: each states something — ``false`` and ``0`` and ``""`` and ``{}`` are written
#: values, not omissions — and each would have been read as "no conjunction",
#: canonicalized to a payload without the key, and given the ``fact_key`` of an
#: advantage that was never authored. ``None`` is the same erasure spelled as an
#: explicit null. The string is the older hazard: it is iterable, so a builder
#: that only checked truthiness would read it letter by letter.
MALFORMED_REQUIREMENTS = [
    pytest.param("skill", id="a-string-is-iterable"),
    pytest.param(False, id="explicit-false"),
    pytest.param(0, id="explicit-zero"),
    pytest.param("", id="empty-string"),
    pytest.param({}, id="empty-object"),
    pytest.param(None, id="explicit-null"),
]


def _fact_target(component_key: str, fact: MechanicalFact) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key=RECORD,
        component_key=component_key,
        fact_key=fact_key(fact),
    )


def _malformed_advantage_payload(value: object) -> dict[str, object]:
    payload = dict(fact_payload(_tool_advantage(_draft())))
    payload["requires_proficiencies"] = value
    return payload


@pytest.mark.parametrize("value", MALFORMED_REQUIREMENTS)
def test_a_present_requirement_of_the_wrong_type_is_refused_not_coerced(
    value: object,
) -> None:
    """The serialization ingress: what a stored or authored payload crosses."""
    with pytest.raises(MalformedFactPayloadError, match="is not a list"):
        fact_from_payload(_malformed_advantage_payload(value))


@pytest.mark.parametrize("value", MALFORMED_REQUIREMENTS)
def test_a_malformed_requirement_is_refused_at_the_override_ingress(
    value: object,
) -> None:
    """The authoring ingress, which is where a hand-written payload arrives.

    ``REPLACE`` on a fact target carries a complete replacement fact, so the
    override surface reaches the same builder. It is asserted separately rather
    than assumed: a patch layer that rebuilt facts its own way would refuse
    nothing here while the test above still passed, and the ``match`` is what
    shows this is the requirement's own refusal rather than a later rejection
    of an unrelated shape.
    """
    payload = {
        "patch": "replace_fact",
        "fact": _malformed_advantage_payload(value),
    }
    with pytest.raises(InvalidPatchError, match="is not a list"):
        patch_from_payload(
            payload,
            operation=OverrideOperationEnum.REPLACE,
            target=_fact_target("tool_proficiency", _tool_advantage(_draft())),
        )


def test_a_malformed_requirement_is_refused_when_read_back_from_the_store(
    session: Session,
) -> None:
    """The reconstruction ingress: rows that were written before the fix.

    Only the advantage's own row is rewritten, so the refusal that fires is the
    one this test is about. Reconstruction refuses rather than repairing: a row
    whose requirement cannot be read is not an advantage with no conjunction,
    and silently becoming one is exactly the erasure being closed.
    """
    identified = identify_projection(_candidate())
    persist_draft(session, identified, now=NOW)
    session.flush()

    advantage = _tool_advantage(_draft())
    result = session.execute(
        update(MechanicalFactORM)
        .where(
            MechanicalFactORM.projection_uuid == identified.projection_uuid,
            MechanicalFactORM.fact_key == fact_key(advantage),
        )
        .values(payload=_malformed_advantage_payload(None))
    )
    assert result.rowcount == 1
    session.flush()

    with pytest.raises(PersistedStateReconstructionError, match="is not a list"):
        reconstruct_candidate(session, identified.projection_uuid)


# ---------------------------------------------------------------------------
# The field is omitted when empty, so nothing accepted moves
# ---------------------------------------------------------------------------


def test_an_advantage_without_the_requirement_keeps_its_schema_3_payload() -> None:
    """Every accepted ``AdvantageFact`` predates this field and must not move.

    ``requires_proficiencies`` is registered as a post-schema-3 field whose
    empty value is its absence, so an advantage that states no conjunction
    serializes to exactly the three keys the accepted corpus already holds. If
    the key were written as an empty list, every accepted advantage fact's
    ``fact_key`` would move and seven accepted batches would need restamping.
    """
    plain = AdvantageFact(
        state=AdvantageState.ADVANTAGE,
        roll=RollSpec(actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK),
    )
    assert plain.requires_proficiencies == ()
    assert set(fact_payload(plain)) == {"family", "roll", "state"}

    # And a schema-3-shaped payload still reads back as the empty requirement
    # rather than as a missing field.
    assert fact_from_payload(fact_payload(plain)) == plain
    assert fact_from_payload(fact_payload(plain)).requires_proficiencies == ()

    # The conjunction is what makes the two different facts with different keys.
    assert fact_key(plain) != fact_key(_tool_advantage(_draft()))

    # Refusing *present* malformed values must not refuse the two spellings an
    # advantage with no conjunction has ever had. The absent key is what the
    # accepted corpus carries; an explicit empty list is what a payload written
    # by hand against the schema-14 field most plainly says. Both build the same
    # fact, with the same key, and both canonicalize back to the accepted three
    # keys — so nothing already accepted has to be restamped and nothing
    # genuinely empty is rejected.
    explicit_empty = fact_from_payload(
        dict(fact_payload(plain)) | {"requires_proficiencies": []}
    )
    assert explicit_empty == plain
    assert fact_key(explicit_empty) == fact_key(plain)
    assert set(fact_payload(explicit_empty)) == {"family", "roll", "state"}


def test_no_accepted_advantage_fact_gained_a_key_from_this_widening() -> None:
    """The rule above, asserted over the artifact it exists to protect.

    The previous test proves the shape on a fact this module builds. That is
    the contract; this is the evidence. The committed accepted authority holds
    ``AdvantageFact``s reviewed under schema 11, and every one of them must
    still serialize to the three keys it was accepted with — a widened family
    whose new field were written unconditionally would move all of them, and
    with them the oracle identity seven batches were accepted against.
    """
    inputs = load_accepted_inputs(ACCEPTED_AUTHORITY_PATH)
    payloads = [
        fact_payload(fact)
        for component in inputs.oracle.representation.components
        for fact in component.facts
        if isinstance(fact, AdvantageFact)
    ]
    assert payloads, "the accepted corpus should hold advantage facts"
    assert all(set(p) == {"family", "roll", "state"} for p in payloads)
    assert all(fact_from_payload(p).requires_proficiencies == () for p in payloads)


# ---------------------------------------------------------------------------
# Provenance, persistence, identity
# ---------------------------------------------------------------------------


def test_every_new_fact_cites_the_clause_that_states_it() -> None:
    """A typed input nobody can trace back to printed text is an invention.

    Each claim is ``CONTEXTUAL``: the component's own binding carries the
    primary claim on the sentence, and the fact cites the same text as the
    authority that bounds it.
    """
    draft = _draft()
    spans = {p.span.span_id for p in _proposal().proposed_spans}
    claims = {
        (claim.target_kind, tuple(claim.target_key)): claim
        for claim in draft.provenance
    }
    for component_key, fact in _new_facts(draft):
        key = tuple(fact_target_key(RECORD, component_key, fact, None))
        matching = [
            claim
            for claim in draft.provenance
            if claim.target_kind is ProvenanceTargetKind.FACT
            and tuple(claim.target_key) == key
        ]
        assert matching, (component_key, fact.FAMILY.value)
        for claim in matching:
            assert claim.role is ProvenanceRole.CONTEXTUAL
            assert claim.span_id in spans
    assert claims


@pytest.mark.parametrize(
    "component_key",
    ["weapon_proficiency", BONUS_USE_COMPONENT],
    ids=["schema-14-application", "schema-15-bonus-use"],
)
def test_dropping_a_new_fact_s_provenance_is_reported(component_key: str) -> None:
    """The omission check reaches the families these mints added, not just old ones."""
    proposal = _proposal()
    draft = proposal.proposed_representation
    fact: MechanicalFact = (
        _bonus_uses(draft)[0]
        if component_key == BONUS_USE_COMPONENT
        else _application(draft, component_key)
    )
    key = tuple(fact_target_key(RECORD, component_key, fact, None))
    kept = tuple(
        claim
        for claim in draft.provenance
        if not (
            claim.target_kind is ProvenanceTargetKind.FACT
            and tuple(claim.target_key) == key
        )
    )
    assert len(kept) < len(draft.provenance)
    stripped = dataclasses.replace(draft, provenance=kept)

    findings = validate_representation(stripped, _ledger(proposal), _corpus(proposal))
    assert any(component_key in f for f in findings), findings


def test_the_typed_inputs_survive_persistence_and_reconstruction(
    session: Session,
) -> None:
    """Typed rows in, typed rows out, and the same projection identity.

    Reconstruction reads the database and nothing else, so a family the store
    cannot round trip fails here rather than the first time a real corpus
    carries it. ``requires_proficiencies`` is the load-bearing part: it is the
    first tuple this mint adds, and a conjunction that came back reordered or
    emptied would be a different rule. The bonus-use component is in the loop
    for the same reason: a family the store cannot round trip is exactly as
    broken whether it arrived with schema 14 or with 15.
    """
    proposal = _proposal()
    identified = identify_projection(_candidate(proposal))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    by_key = {
        (c.record_key, c.semantic_key): c for c in rebuilt.representation.components
    }
    for component_key in (*PRINTED_APPLICATIONS, BONUS_USE_COMPONENT):
        assert (
            by_key[(RECORD, component_key)].facts
            == _component(proposal.proposed_representation, component_key).facts
        )

    (advantage,) = [
        f
        for f in by_key[(RECORD, "tool_proficiency")].facts
        if isinstance(f, AdvantageFact)
    ]
    assert advantage.requires_proficiencies == PRINTED_CONJUNCTION
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


@pytest.mark.parametrize(
    ("component_key", "replacement", "why"),
    [
        (
            "weapon_proficiency",
            ProficiencyApplicationFact(
                proficiency=ProficiencyKind.WEAPON,
                roll=RollSpec(actor=RollActor.SUBJECT, context=RollContext.ATTACK_ROLL),
            ),
            "the same fact is the same identity",
        ),
        (
            "tool_proficiency",
            AdvantageFact(
                state=AdvantageState.ADVANTAGE,
                roll=RollSpec(
                    actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK
                ),
            ),
            "dropping the conjunction makes the Advantage unconditional",
        ),
    ],
    ids=["unchanged", "conjunction-dropped"],
)
def test_a_changed_requirement_changes_the_projection_identity(
    component_key: str, replacement: MechanicalFact, why: str
) -> None:
    """Identity covers the new fields, so weakening one cannot pass unnoticed."""
    proposal = _proposal()
    draft = proposal.proposed_representation
    original = identify_projection(_candidate(proposal)).projection_uuid

    component = _component(draft, component_key)
    swapped = dataclasses.replace(
        component,
        facts=tuple(
            replacement if type(f) is type(replacement) else f for f in component.facts
        ),
    )
    changed = dataclasses.replace(
        draft,
        components=tuple(
            swapped if c.semantic_key == component_key else c for c in draft.components
        ),
    )
    moved = identify_projection(_candidate(proposal, changed)).projection_uuid
    if why == "the same fact is the same identity":
        assert moved == original
    else:
        assert moved != original, why


# ---------------------------------------------------------------------------
# The historical contract still refuses what it cannot state
# ---------------------------------------------------------------------------


def test_each_earlier_contract_refuses_exactly_what_arrived_after_it() -> None:
    """The succession is real in the refusing direction, on the reviewed artifact.

    Two mints, so the transition is asserted as two steps rather than one. What
    schema 13 refuses is the narrowest statement of everything added since: the
    three families, the three vocabularies wherever their members appear, and
    the ``requires_proficiencies`` key — each finding naming the schema that
    introduced the thing it refuses, 14 or 15, never a blanket "not current".
    What schema 14 refuses is exactly schema 15's contribution and nothing else,
    which is what shows the second mint is additive rather than a restatement of
    the first. Schema 15 admits the whole draft.
    """
    draft = _draft()
    violations = declared_meaning_violations(draft, SCHEMA_13_VERSION)
    assert violations
    assert all(
        SCHEMA_14_VERSION in v or SCHEMA_15_VERSION in v for v in violations
    ), violations

    families = [v for v in violations if "closed union has no" in v]
    assert len(families) == len(_new_facts(draft)) - 1  # the advantage is old
    assert {
        f.FAMILY.value for _, f in _new_facts(draft) if f.FAMILY in NEW_FAMILIES
    } == {family.value for family in NEW_FAMILIES}

    # Schema 14 was the current contract when the first three inputs landed, so
    # what it still refuses is the whole of the later mint and no part of its
    # own.
    later = declared_meaning_violations(draft, SCHEMA_14_VERSION)
    assert later
    assert all(SCHEMA_15_VERSION in v for v in later), later
    assert {v for v in later if "closed union has no" in v} and all(
        FactFamily.PROFICIENCY_BONUS_USE.value in v
        for v in later
        if "closed union has no" in v
    ), later

    assert declared_meaning_violations(draft, SCHEMA_15_VERSION) == []


def test_the_requirement_is_refused_by_its_field_and_by_its_members() -> None:
    """Two gates, and the member gate is the one a field rule cannot cover.

    The field registry refuses ``requires_proficiencies`` on a schema-13
    declaration because the key is new. That alone would not refuse a
    ``ProficiencyKind`` member reaching an *older* field, so the member index
    exists as well and names the same schema. Asserting both here is what shows
    the second gate is wired rather than merely declared.
    """
    fact = _tool_advantage(_draft())
    findings = declared_meaning_violations(
        dataclasses.replace(
            _draft(),
            components=tuple(
                c for c in _draft().components if c.semantic_key == "tool_proficiency"
            ),
        ),
        SCHEMA_13_VERSION,
    )
    by_field = [v for v in findings if "has no 'requires_proficiencies' key" in v]
    by_member = [
        v
        for v in findings
        if "ProficiencyKind does not admit" in v and ".requires_proficiencies[" in v
    ]
    assert len(by_field) == 1, findings
    assert len(by_member) == len(fact.requires_proficiencies), findings
    assert all(SCHEMA_14_VERSION in v for v in by_field + by_member)


# ---------------------------------------------------------------------------
# The consumer boundary: addressing, not evaluation
# ---------------------------------------------------------------------------


def test_the_new_facts_reach_a_consumer_as_declared_members() -> None:
    """``_base_records`` is what every reader of mechanical authority goes through.

    Each new fact arrives as its closed vocabulary members with the span ids
    that state it. No bonus is summed and no relevance is decided: the whole
    consumer-visible effect of this mint is that these rules are now addressable
    and traceable.
    """
    records = _base_records(_candidate())
    by_key = {c.semantic_key: c for c in records[RECORD].components}
    for component_key, fact in _new_facts(_draft()):
        (entry,) = [e for e in by_key[component_key].facts if e.fact == fact]
        assert entry.span_ids
        assert entry.fact_key == fact_key(fact)


def test_an_override_can_address_a_new_fact_by_its_key() -> None:
    """A new family is addressable by override without per-family registration.

    Override addressing resolves a fact by its content-derived key, so the
    authoring surface reaches these rules the day they exist. The sibling
    application in the same component is untouched, which is what shows the
    disable landed on the target rather than on the component.
    """
    draft = _draft()
    advantage = _tool_advantage(draft)
    sibling = _application(draft, "tool_proficiency")

    entry = EffectiveOverrideEntry(
        override_id="ov-tool-advantage",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=RECORD,
            component_key="tool_proficiency",
            fact_key=fact_key(advantage),
        ),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )
    state = EffectiveOverrideSet(
        package_uuid=_PACKAGE_BINDING.package_uuid,
        release_version=_PACKAGE_BINDING.release_version,
        entries=(entry,),
    )
    view = apply_override_set(_candidate(), state, _PACKAGE_BINDING)

    (applied,) = view.applied_overrides
    assert applied.applied
    (record,) = [r for r in view.records if r.semantic_key == RECORD]
    (component,) = [
        c for c in record.components if c.semantic_key == "tool_proficiency"
    ]
    keys = {f.fact_key for f in component.facts}
    assert fact_key(advantage) not in keys
    assert fact_key(sibling) in keys


def _override_view(
    component_key: str,
    fact: MechanicalFact,
    operation: OverrideOperationEnum,
    payload: dict[str, object],
):  # type: ignore[no-untyped-def]
    """One enabled entry against one fact of the reviewed draft, applied."""
    entry = EffectiveOverrideEntry(
        override_id=f"ov-{component_key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=_fact_target(component_key, fact),
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=payload,
    )
    state = EffectiveOverrideSet(
        package_uuid=_PACKAGE_BINDING.package_uuid,
        release_version=_PACKAGE_BINDING.release_version,
        entries=(entry,),
    )
    return apply_override_set(_candidate(), state, _PACKAGE_BINDING)


def test_a_limit_can_be_replaced_within_the_shape_its_family_admits() -> None:
    """What ``REPLACE`` actually reaches, shown rather than claimed.

    A replacement fact is rebuilt through the same builder and the same family
    invariants as anything else, so a limit may be replaced by *any* limit those
    invariants admit — here a house rule raising the multiplication ceiling from
    the printed one to two, which is an admitted shape because the family's rule
    is ``maximum_applications >= 1``, not ``== 1``. The effective view carries
    the replacement, the other two limits are untouched, and the change is
    attributed to the override that supplied it rather than to the source.
    """
    draft = _draft()
    (original,) = [
        f
        for f in _component(draft, "bonus_does_not_stack").facts
        if isinstance(f, ProficiencyBonusOperationLimitFact)
        and f.operation is ProficiencyBonusOperation.MULTIPLY
    ]
    replacement = dataclasses.replace(original, maximum_applications=2)
    assert fact_invariant_violations(replacement) == ()

    view = _override_view(
        "bonus_does_not_stack",
        original,
        OverrideOperationEnum.REPLACE,
        {"patch": "replace_fact", "fact": dict(fact_payload(replacement))},
    )

    (applied,) = view.applied_overrides
    assert applied.applied
    (record,) = [r for r in view.records if r.semantic_key == RECORD]
    (component,) = [
        c for c in record.components if c.semantic_key == "bonus_does_not_stack"
    ]
    by_key = {f.fact_key: f for f in component.facts}
    assert fact_key(original) not in by_key
    assert by_key[fact_key(replacement)].fact == replacement
    assert by_key[fact_key(replacement)].supplied_by_override_id == applied.override_id

    # The printed addition and division limits are still the source's own.
    others = [f for f in component.facts if f.fact_key != fact_key(replacement)]
    assert others
    assert all(f.supplied_by_override_id is None for f in others)


def test_moving_a_proficiency_kind_s_roll_is_not_reachable_by_override() -> None:
    """The pairing is closed by the schema, so an erratum moving it is a schema change.

    ``_PROFICIENCY_APPLICATION_ROLLS`` states one roll per printed proficiency
    kind, and the family invariant runs on a replacement fact exactly as it runs
    on an authored one. So the one thing an override cannot do to these facts is
    re-pair them: authoring *"skill proficiency applies to attack rolls"* fails
    at the patch builder, before anything is applied, and stays failing however
    the override is spelled. Re-pairing requires a later authorized change to
    that table — a new schema — not an override.
    """
    application = _application(_draft(), "skill_proficiency_application")
    moved = dataclasses.replace(
        application,
        roll=RollSpec(actor=RollActor.SUBJECT, context=RollContext.ATTACK_ROLL),
    )
    assert fact_invariant_violations(moved)

    with pytest.raises(
        OverrideApplicationError,
        match="is stated as applying to ability_check, not attack_roll",
    ):
        _override_view(
            "skill_proficiency_application",
            application,
            OverrideOperationEnum.REPLACE,
            {"patch": "replace_fact", "fact": dict(fact_payload(moved))},
        )
