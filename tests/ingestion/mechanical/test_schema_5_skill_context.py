"""A skill qualifies an ability check, and nothing else — CRD Issue 5d, schema 5.

Schema 5 introduced the check/save distinction. This is that distinction applied
consistently: the SRD prints a skill in parentheses after the ability of a
*check* — *"a DC 15 Dexterity (Acrobatics) check"* — and never after a saving
throw, an attack roll, Initiative, or the ``D20_TEST`` umbrella. Proficiency in a
skill applies to the check it names; a save adds save proficiency, which is a
different bonus from a different column of the sheet.

**Two structures carry a skill, so the rule is one function read by both.**
:class:`AbilityCheckFact` states the roll a DC is set for;
:class:`RollSpec` states the roll a stated modification applies to. Refusing the
combination on one and admitting it on the other is the asymmetry that kept this
rule out of schema 5's first cut, so what these tests actually protect is that
``_check_skill_context`` is the single statement both reach.

Everything here is about the grammar. Nothing accepts, publishes, or activates.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    ComponentDraft,
    DcKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    Skill,
    _dataclass_payload,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    schema_binding_violations,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.services.rules_authority.patches import InvalidPatchError
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: Every context a skill may not qualify. ``ABILITY_CHECK`` is the sole
#: exception and is asserted separately, so this list is the whole complement.
SKILL_FREE_CONTEXTS = [
    RollContext.SAVING_THROW,
    RollContext.ATTACK_ROLL,
    RollContext.INITIATIVE,
    RollContext.D20_TEST,
]


def _check(**kw: object) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability=kw.pop("ability", AbilityScore.STRENGTH),  # type: ignore[arg-type]
        dc_kind=DcKind.FIXED,
        dc_value=15,
        **kw,  # type: ignore[arg-type]
    )


def _spec(context: RollContext, skill: Skill | None = None) -> RollSpec:
    return RollSpec(
        actor=RollActor.SUBJECT,
        context=context,
        # An ability is stated only where the source states one, so an attack
        # roll and Initiative carry none — this keeps each case failing for the
        # skill rule rather than for an unrelated one.
        ability=(
            AbilityScore.STRENGTH
            if context in (RollContext.ABILITY_CHECK, RollContext.SAVING_THROW)
            else None
        ),
        skill=skill,
    )


def _advantage(spec: RollSpec) -> AdvantageFact:
    """A family that carries a ``RollSpec``, so the shared rule is reached."""
    return AdvantageFact(state=AdvantageState.ADVANTAGE, roll=spec)


# ---------------------------------------------------------------------------
# What must stay valid
# ---------------------------------------------------------------------------


def test_a_constitution_saving_throw_without_a_skill_is_valid() -> None:
    """Malnutrition's roll, which is what schema 5 exists to be able to state."""
    save = AbilityCheckFact(
        ability=AbilityScore.CONSTITUTION,
        dc_kind=DcKind.FIXED,
        dc_value=10,
        context=RollContext.SAVING_THROW,
    )
    assert fact_invariant_violations(save) == ()
    assert save.skill is None
    assert save.alternatives == ()
    assert fact_from_payload(fact_payload(save)) == save


def test_a_skilled_ability_check_remains_valid() -> None:
    """Falling's surface check. The rule narrows nothing a check may state."""
    check = _check(context=RollContext.ABILITY_CHECK, skill=Skill.ATHLETICS)
    assert fact_invariant_violations(check) == ()
    assert fact_from_payload(fact_payload(check)) == check


def test_a_roll_spec_ability_check_may_carry_a_skill() -> None:
    spec = _spec(RollContext.ABILITY_CHECK, Skill.ATHLETICS)
    assert fact_invariant_violations(_advantage(spec)) == ()


@pytest.mark.parametrize("context", SKILL_FREE_CONTEXTS, ids=lambda c: c.value)
def test_an_unskilled_roll_spec_is_valid_in_every_context(
    context: RollContext,
) -> None:
    """The control. The rule is about the *skill*, not about the context."""
    assert fact_invariant_violations(_advantage(_spec(context))) == ()


#: Falling's *"Strength (Athletics) or Dexterity (Acrobatics)"*, canonically
#: ordered. Authoring order must not reach the fact key, so the set is sorted by
#: the payload the validator itself compares.
ALTERNATIVES = tuple(
    sorted(
        (
            _spec(RollContext.ABILITY_CHECK, Skill.ATHLETICS),
            replace(
                _spec(RollContext.ABILITY_CHECK, Skill.ACROBATICS),
                ability=AbilityScore.DEXTERITY,
            ),
        ),
        key=lambda r: canonical_bytes(_dataclass_payload(r)),
    )
)


def test_alternative_checks_remain_valid_and_canonically_ordered() -> None:
    """Every member is a skilled *check*, so nothing in the set is refused."""
    check = _check(
        context=RollContext.ABILITY_CHECK,
        skill=Skill.ATHLETICS,
        alternatives=ALTERNATIVES,
    )
    assert fact_invariant_violations(check) == ()
    assert [(a.ability, a.skill) for a in check.alternatives] == [
        (AbilityScore.DEXTERITY, Skill.ACROBATICS),
        (AbilityScore.STRENGTH, Skill.ATHLETICS),
    ]
    assert all(a.context is RollContext.ABILITY_CHECK for a in check.alternatives)
    # Canonical order is *required* rather than imposed: the serializer is
    # generic over every family and must not acquire per-family ordering rules,
    # so the invariant refuses an authoring order instead of normalizing it.
    # That is what keeps two authorings of one closed choice from being two
    # identities.
    reversed_authoring = _check(
        context=RollContext.ABILITY_CHECK,
        skill=Skill.ATHLETICS,
        alternatives=tuple(reversed(ALTERNATIVES)),
    )
    assert any(
        "not in canonical order" in v
        for v in fact_invariant_violations(reversed_authoring)
    )


# ---------------------------------------------------------------------------
# What must fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("skill", "ability"),
    [
        (Skill.ATHLETICS, AbilityScore.STRENGTH),
        (Skill.ACROBATICS, AbilityScore.DEXTERITY),
    ],
    ids=["athletics", "acrobatics"],
)
def test_a_saving_throw_carrying_a_skill_is_refused(
    skill: Skill, ability: AbilityScore
) -> None:
    """Both skills the brief names, each correctly paired with its own ability.

    Correctly paired on purpose: the refusal has to be about the *context*, not
    a pairing failure that would mask it.
    """
    violations = fact_invariant_violations(
        _check(ability=ability, context=RollContext.SAVING_THROW, skill=skill)
    )
    assert any(
        "a skill qualifies an ability check" in v for v in violations
    ), violations


def test_a_saving_throw_offering_alternatives_is_refused_for_its_context() -> None:
    """The defect, not the symptom.

    A saving throw offering a choice of checks also fails the alternatives
    *completeness* rule, and reporting that first would say "no member states
    the fact's own pair" — true, and not what is wrong.
    """
    violations = fact_invariant_violations(
        _check(context=RollContext.SAVING_THROW, alternatives=ALTERNATIVES)
    )
    assert any("does not govern two kinds of roll" in v for v in violations), violations


@pytest.mark.parametrize("context", SKILL_FREE_CONTEXTS, ids=lambda c: c.value)
def test_a_roll_spec_carrying_a_skill_outside_an_ability_check_is_refused(
    context: RollContext,
) -> None:
    """The same rule on the other structure that carries a skill."""
    violations = fact_invariant_violations(_advantage(_spec(context, Skill.ATHLETICS)))
    assert any(
        "a skill qualifies an ability check" in v for v in violations
    ), violations


def test_both_carriers_refuse_the_combination_in_the_same_words() -> None:
    """One statement of the rule, so the two cannot drift into disagreeing.

    Asserted on the shared wording rather than on two independent refusals: two
    validators that happen to agree today are not one rule.
    """
    fact = _check(context=RollContext.SAVING_THROW, skill=Skill.ATHLETICS)
    spec = _advantage(_spec(RollContext.SAVING_THROW, Skill.ATHLETICS))
    shared = "a skill qualifies an ability check, and a saving throw adds save"
    assert any(shared in v for v in fact_invariant_violations(fact))
    assert any(shared in v for v in fact_invariant_violations(spec))


def test_the_pairing_rule_survives_context_admission() -> None:
    """Context admitted, and the older rule still applies to what it admits."""
    violations = fact_invariant_violations(
        _check(
            ability=AbilityScore.DEXTERITY,
            context=RollContext.ABILITY_CHECK,
            skill=Skill.ATHLETICS,
        )
    )
    assert any("governed by strength" in v for v in violations), violations


# ---------------------------------------------------------------------------
# Every authority seam refuses it
# ---------------------------------------------------------------------------


def _skilled_save_payload() -> dict[str, object]:
    """A wire payload for the refused combination, built by hand.

    Construction admits it — the dataclass is a container — so the payload is
    written directly rather than serialized from an instance, which is how a
    tampered row or a hand-edited artifact would really arrive.
    """
    payload = dict(fact_payload(_check(context=RollContext.SAVING_THROW)))
    payload["skill"] = Skill.ATHLETICS.value
    return payload


def test_the_wire_builder_rebuilds_it_and_the_validator_refuses_it() -> None:
    """Where this rule is enforced, and — deliberately — where it is not.

    ``fact_from_payload`` rebuilds the *declared shape*: it refuses an unknown
    family, a missing field, an extra field and a mistyped value, and it runs no
    family invariant at all. That is not an omission this rule introduced — the
    pre-existing fixed-DC rule behaves identically — and changing it here would
    put a per-family contract on a generic seam that every family shares.

    Enforcement lives in ``fact_invariant_violations``, which
    ``_validate_components`` calls, and which the publication gate, acceptance,
    and the reconstructed-candidate path all reach through
    ``validate_representation``. So the payload rebuilds, and the authority it
    would become is refused.
    """
    rebuilt = fact_from_payload(_skilled_save_payload())
    assert isinstance(rebuilt, AbilityCheckFact)
    assert rebuilt.skill is Skill.ATHLETICS
    assert any(
        "a skill qualifies an ability check" in v
        for v in fact_invariant_violations(rebuilt)
    )


def _draft_with(fact: object) -> RepresentationDraft:
    return RepresentationDraft(
        records=(
            RecordDraft(semantic_key="hazard.falling", kind=RecordKind.GLOSSARY_RULE),
        ),
        components=(
            ComponentDraft(
                record_key="hazard.falling",
                semantic_key="surface_check",
                handling=ComponentHandling.STRUCTURED,
                facts=(fact,),  # type: ignore[arg-type]
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


@pytest.mark.parametrize(
    ("label", "fact"),
    [
        (
            "ability check fact",
            _check(context=RollContext.SAVING_THROW, skill=Skill.ATHLETICS),
        ),
        (
            "roll spec",
            _advantage(_spec(RollContext.SAVING_THROW, Skill.ATHLETICS)),
        ),
    ],
)
def test_the_representation_validator_refuses_both_carriers(
    label: str, fact: object
) -> None:
    """The seam the gate, acceptance and the reconstructed candidate all reach.

    Both structures are asked through one call, because "the two cannot
    disagree" is a claim about the validator they share rather than about two
    validators that happen to agree.
    """
    representation = build_representation()
    components = list(representation.components)
    components[0] = replace(
        components[0], facts=(*components[0].facts, fact)  # type: ignore[arg-type]
    )
    findings = validate_representation(
        replace(representation, components=tuple(components)),
        build_ledger(),
        bound_corpus(),
    )
    assert any("a skill qualifies an ability check" in f for f in findings), (
        label,
        findings,
    )


def test_the_schema_binding_seam_refuses_it_too() -> None:
    """So acceptance, the committed loader and ``verify_lift`` all refuse it.

    ``schema_binding_violations`` reaches the family invariants through
    ``held_structure_violations``, which is why one rule stated once covers
    every seam that *admits* authority rather than only the publication gate.
    That is the whole point of putting it in a shared validator: the seams
    cannot disagree because there is nothing for them to disagree about.
    """
    draft = _draft_with(_check(context=RollContext.SAVING_THROW, skill=Skill.ATHLETICS))
    findings = schema_binding_violations(draft, (SCHEMA_5_VERSION, SCHEMA_5_HASH))
    assert any("a skill qualifies an ability check" in f for f in findings), findings
    # And the honest control: a skilled *check* passes the same seam.
    clean = _draft_with(
        _check(context=RollContext.ABILITY_CHECK, skill=Skill.ATHLETICS)
    )
    assert schema_binding_violations(clean, (SCHEMA_5_VERSION, SCHEMA_5_HASH)) == []


def test_persistence_reconstruction_refuses_a_tampered_row(session: Session) -> None:
    """A stored payload is authority only if it still says what it said."""
    from afterworlds.persistence.orm.mechanical import MechanicalFactORM

    representation = build_representation()
    components = list(representation.components)
    components[0] = replace(
        components[0],
        facts=(
            *components[0].facts,
            _check(context=RollContext.SAVING_THROW),
        ),
    )
    identified = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            replace(representation, components=tuple(components)),
        )
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    row = session.scalars(
        select(MechanicalFactORM).where(MechanicalFactORM.family == "ability_check")
    ).one()
    session.execute(
        update(MechanicalFactORM)
        .where(MechanicalFactORM.fact_id == row.fact_id)
        .values(payload={**row.payload, "skill": Skill.ATHLETICS.value})
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


def test_the_override_patch_builder_refuses_it() -> None:
    """The effective-view path reads the same contract as the corpus."""
    from afterworlds.services.rules_authority.patches import _build_fact

    with pytest.raises(InvalidPatchError):
        _build_fact(_skilled_save_payload(), "probe")


def test_the_committed_loader_refuses_it(tmp_path: object) -> None:
    """End to end, through the file the Owner actually signs off."""
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    raw["representation"]["components"][0]["facts"] = [_skilled_save_payload()]
    raw["representation_schema"] = {"version": SCHEMA_5_VERSION, "hash": SCHEMA_5_HASH}
    raw["acceptance"]["schema_anchors"] = [
        {
            "batch_id": batch["batch_id"],
            "proposal_identity": batch["proposal_identity"],
            "schema_version": SCHEMA_5_VERSION,
            "schema_hash": SCHEMA_5_HASH,
        }
        for batch in raw["acceptance"]["batches"]
    ]
    path = Path(str(tmp_path)) / "skilled-save.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(path)


# ---------------------------------------------------------------------------
# Nothing earlier moved
# ---------------------------------------------------------------------------


def test_the_pinned_schema_5_hash_covers_this_correction() -> None:
    """The rule is declared, so it is inside the identity that governs it."""
    assert representation_schema_hash() == SCHEMA_5_HASH


def test_schema_4_is_untouched_by_this_correction() -> None:
    """Its pin, and its legality answer for content it really admitted."""
    assert SCHEMA_4_HASH == (
        "241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9"  # noqa: E501  # pragma: allowlist secret
    )
    # A skilled ability check is schema-4 content and stays legal under it.
    skilled = _spec(RollContext.ABILITY_CHECK, Skill.ATHLETICS)
    assert (
        declared_meaning_violations(_draft_with(_advantage(skilled)), SCHEMA_4_VERSION)
        == []
    )


def test_every_accepted_element_is_still_byte_identical() -> None:
    """The correction adds a rule, not a field, so nothing accepted can move."""
    from afterworlds.ingestion.mechanical.projection import representation_payload
    from afterworlds.ingestion.mechanical.schema_lift import lift_accepted_inputs

    inputs = load_accepted_inputs(ARTIFACT_PATH)
    lifted, records = lift_accepted_inputs(inputs, (SCHEMA_5_VERSION, SCHEMA_5_HASH))
    before = representation_payload(
        inputs.oracle.representation, schema_version=inputs.oracle.schema_version
    )
    after = representation_payload(
        lifted.oracle.representation, schema_version=SCHEMA_5_VERSION
    )
    assert set(before) == set(after)
    for collection in sorted(before):
        assert canonical_bytes(before[collection]) == canonical_bytes(after[collection])
    assert [r.lift_id for r in records] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
    ]
