"""Schema 6 against the source that forced it — CRD Issue 5d, batch ``actions-1``.

Every blocking obligation the ``actions-1`` schema-stop checkpoint recorded, as
the typed value schema 6 admits for it, with the printed clause it represents.
The checkpoint's ledger is discovery evidence; this is the executable half —
each case is built, validated by the production validator, round-tripped through
the canonical payload, and keyed.

**What the round-trip proves.** ``fact_payload`` → ``fact_from_payload`` is the
exact path persistence, the oracle loader and the override patch builder take,
so a family that survives it survives all three. ``fact_key`` is asserted stable
across it because a key derived from the payload is what provenance, override
targeting and the duplicate check all address a fact by.

**What the distinction cases prove.** A representation is false, not merely
lossy, when two things the source states differently produce one payload. The
distinction block below states each such pair the batch actually contains —
grants, timing, beneficiaries, sequencing, prerequisites — and asserts they stay
apart.

**What the refusals prove.** A widening that admits everything states nothing.
The refusal block holds the shapes schema 6 deliberately still cannot carry:
``Hide``'s four-way stop list, a nested disjunction, an ally's turn as a clock,
an eligibility threshold nothing could meet.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    COMPONENT_WIDE_PROSE,
    AbilityCheckFact,
    AbilityScore,
    ActionAllowanceFact,
    ActionCost,
    ActivationCostEligibilityFact,
    AdvantageFact,
    AdvantageState,
    AllowanceScope,
    Applicability,
    ApplicabilityKind,
    AttackRelativeTiming,
    BenefitUseLimit,
    Comparison,
    ComponentOption,
    ConditionKind,
    CoverDegree,
    DcKind,
    EffectDurationFact,
    EligibilitySubject,
    EquipmentChange,
    EquipmentChangeFact,
    ExpendableResource,
    GrantedActivity,
    InterleavePoint,
    MalformedFactPayloadError,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementInterleaveFact,
    ObscurementState,
    ProseBindingDraft,
    ReactionProvocationFact,
    RecurrenceBoundary,
    RecurringActionRequirementFact,
    ResolutionTiming,
    ResourceExpenditureFact,
    RetryRestrictionFact,
    RollActor,
    RollContext,
    RollSpec,
    Skill,
    StateEffectKind,
    SustainedState,
    SustainedStateRequirementFact,
    TimeUnit,
    TrackedQuantity,
    TriggeredReaction,
    TriggeredResolutionFact,
    _dataclass_payload,
    applicability_violations,
    canonical_bytes,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    option_set_violations,
    prose_binding_target_key,
)

# ---------------------------------------------------------------------------
# The disjunctions, in derived canonical order
# ---------------------------------------------------------------------------


def _canonical(*terms: Applicability) -> tuple[Applicability, ...]:
    """Canonical order, derived rather than written out.

    The invariant requires canonical order, so hand-sorting here would let a
    case pass by agreeing with itself about what canonical means.
    """
    return tuple(sorted(terms, key=lambda a: canonical_bytes(_dataclass_payload(a))))


#: ``Dodge`` G5 — *"You lose these benefits if you have the Incapacitated
#: condition **or** if your Speed is 0."* A condition state disjoined with a
#: quantity threshold: two kinds, which is the case a homogeneous set cannot
#: reach and the reason the disjunction is flat rather than within-one-kind.
DODGE_LOSS = Applicability(
    kind=ApplicabilityKind.ANY_OF,
    any_of_terms=_canonical(
        Applicability(
            kind=ApplicabilityKind.CONDITION_STATE,
            condition=ConditionKind.INCAPACITATED,
        ),
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            quantity=TrackedQuantity.SPEED,
            comparison=Comparison.EQUALS,
            value=0,
        ),
    ),
)

#: ``Hide`` I2 — *"while you're Heavily Obscured **or** behind Three-Quarters
#: Cover **or** Total Cover"*. Three printed states of two closed vocabularies.
HIDE_PREREQUISITE = Applicability(
    kind=ApplicabilityKind.ANY_OF,
    any_of_terms=_canonical(
        Applicability(
            kind=ApplicabilityKind.OBSCUREMENT,
            obscurement=ObscurementState.HEAVILY_OBSCURED,
        ),
        Applicability(kind=ApplicabilityKind.COVER, cover=CoverDegree.THREE_QUARTERS),
        Applicability(kind=ApplicabilityKind.COVER, cover=CoverDegree.TOTAL),
    ),
)

#: ``Magic`` K4 and ``Ready`` L10 — *"If your Concentration is broken"*.
CONCENTRATION_BROKEN = Applicability(
    kind=ApplicabilityKind.EFFECT_STATE,
    effect_state=StateEffectKind.CONCENTRATION_BROKEN,
)


# ---------------------------------------------------------------------------
# One case per blocking obligation
# ---------------------------------------------------------------------------
#
# Keyed by the checkpoint's own obligation id so a reviewer can go from a ledger
# row to the value that answers it without a second index.

CASES: dict[str, tuple[str, object]] = {
    # -- Action, p176 -------------------------------------------------------
    "A1": (
        "On your turn, you can take one action.",
        ActionAllowanceFact(count=1, per=AllowanceScope.TURN, cost=ActionCost.ACTION),
    ),
    # -- Attack, p177 -------------------------------------------------------
    "B1": (
        "When you take the Attack action, you can make one attack roll",
        ActionAllowanceFact(
            count=1,
            per=AllowanceScope.OWNING_EFFECT,
            activity=GrantedActivity.ATTACK_ROLL,
        ),
    ),
    "B3": (
        "You can either equip or unequip one weapon when you make an attack",
        ActionAllowanceFact(
            count=1,
            per=AllowanceScope.ATTACK,
            activity=GrantedActivity.EQUIPMENT_CHANGE,
        ),
    ),
    "B4": (
        "You do so either before or after the attack.",
        EquipmentChangeFact(
            change=EquipmentChange.EQUIP, timing=AttackRelativeTiming.BEFORE
        ),
    ),
    "B7": (
        "you can use some or all of that movement to move between those attacks",
        MovementInterleaveFact(between=InterleavePoint.REPEATED_ATTACKS),
    ),
    # -- Dash, p180 ---------------------------------------------------------
    "D2": (
        "The increase equals your Speed after applying any modifiers.",
        MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPEED),
    ),
    "D3": (
        "for the current turn",
        EffectDurationFact(
            until=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    "D5": (
        "you can use that speed instead of your Speed",
        MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPECIAL_SPEED),
    ),
    # -- Disengage, p181 ----------------------------------------------------
    "E1": (
        "your movement doesn't provoke Opportunity Attacks",
        ReactionProvocationFact(
            reaction=TriggeredReaction.OPPORTUNITY_ATTACK, provokes=False
        ),
    ),
    # -- Dodge, p181 --------------------------------------------------------
    "G4": (
        "until the start of your next turn",
        EffectDurationFact(
            until=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    # -- Help, pp182-183 ----------------------------------------------------
    "H3": (
        "That ally has Advantage on the next ability check they make with the "
        "chosen skill or tool.",
        AdvantageFact(
            state=AdvantageState.ADVANTAGE,
            roll=RollSpec(actor=RollActor.ALLY, context=RollContext.ABILITY_CHECK),
            use_limit=BenefitUseLimit.NEXT_QUALIFYING_ROLL,
        ),
    ),
    "H6": (
        "giving Advantage to the next attack roll by one of your allies against "
        "that enemy",
        AdvantageFact(
            state=AdvantageState.ADVANTAGE,
            roll=RollSpec(actor=RollActor.ALLY, context=RollContext.ATTACK_ROLL),
            use_limit=BenefitUseLimit.NEXT_QUALIFYING_ROLL,
        ),
    ),
    # -- Hide, p183 ---------------------------------------------------------
    "I6": (
        "Make note of your check's total, which is the DC for a creature to find "
        "you with a Wisdom (Perception) check.",
        AbilityCheckFact(
            ability=AbilityScore.WISDOM,
            dc_kind=DcKind.RECORDED_CHECK_TOTAL,
            skill=Skill.PERCEPTION,
            against_subject=True,
            context=RollContext.ABILITY_CHECK,
        ),
    ),
    # -- Influence, p184 ----------------------------------------------------
    "J6+J9": (
        "you must make an ability check ... which has a default DC equal to 15 "
        "or the monster's Intelligence score, whichever is higher",
        AbilityCheckFact(
            ability=None,
            dc_kind=DcKind.HIGHER_OF_FIXED_OR_TARGET_ABILITY_SCORE,
            dc_value=15,
            dc_ability=AbilityScore.INTELLIGENCE,
            context=RollContext.ABILITY_CHECK,
        ),
    ),
    "J11": (
        "you must wait 24 hours (or a duration set by the GM) before urging it "
        "in the same way again",
        RetryRestrictionFact(
            amount=24, unit=TimeUnit.HOUR, gamemaster_may_set_other=True
        ),
    ),
    # -- Magic, p185 --------------------------------------------------------
    "K1": (
        "you cast a spell that has a casting time of an action",
        ActivationCostEligibilityFact(
            subject=EligibilitySubject.SPELL, cost=ActionCost.ACTION
        ),
    ),
    "K2": (
        "you must take the Magic action on each turn of that casting",
        RecurringActionRequirementFact(cost=ActionCost.ACTION, per=TimeUnit.TURN),
    ),
    "K3": (
        "and you must maintain Concentration while you do so",
        SustainedStateRequirementFact(state=SustainedState.CONCENTRATION),
    ),
    "K4": (
        "the spell fails, but you don't expend a spell slot",
        ResourceExpenditureFact(resource=ExpendableResource.SPELL_SLOT, expended=False),
    ),
    # -- Ready, pp186-187 ---------------------------------------------------
    "L2": (
        "which lets you act by taking a Reaction before the start of your next turn",
        ActionAllowanceFact(
            count=1, per=AllowanceScope.OWNING_EFFECT, cost=ActionCost.REACTION
        ),
    ),
    "L4": (
        "you choose to move up to your Speed in response to it",
        MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPEED),
    ),
    "L6": (
        "you can either take your Reaction right after the trigger finishes or "
        "ignore the trigger",
        TriggeredResolutionFact(
            timing=ResolutionTiming.IMMEDIATELY_AFTER_TRIGGER, optional=True
        ),
    ),
    "L7": (
        "expending any resources used to cast it",
        ResourceExpenditureFact(
            resource=ExpendableResource.CASTING_RESOURCES, expended=True
        ),
    ),
    "L8": (
        "To be readied, a spell must have a casting time of an action",
        ActivationCostEligibilityFact(
            subject=EligibilitySubject.SPELL, cost=ActionCost.ACTION
        ),
    ),
    "L9": (
        "which you can maintain up to the start of your next turn",
        EffectDurationFact(
            until=RecurrenceBoundary.START_OF_TURN, whose=RollActor.SUBJECT
        ),
    ),
    # -- Utilize, p191 ------------------------------------------------------
    "O2": (
        "When an object requires an action for its use, you take the Utilize action.",
        ActivationCostEligibilityFact(
            subject=EligibilitySubject.OBJECT, cost=ActionCost.ACTION
        ),
    ),
}


@pytest.mark.parametrize("obligation", sorted(CASES))
def test_each_blocked_obligation_now_has_a_valid_typed_value(obligation: str) -> None:
    """Built, and admitted by the validator the production paths already call."""
    _, fact = CASES[obligation]
    assert list(fact_invariant_violations(fact)) == [], obligation


@pytest.mark.parametrize("obligation", sorted(CASES))
def test_each_case_round_trips_through_the_canonical_payload(
    obligation: str,
) -> None:
    """The exact path persistence, the oracle loader and overrides all take."""
    _, fact = CASES[obligation]
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload
    assert fact_key(rebuilt) == fact_key(fact)
    assert len(fact_key(fact)) == 16


@pytest.mark.parametrize("applicability", [DODGE_LOSS, HIDE_PREREQUISITE])
def test_each_cross_kind_disjunction_is_admitted(
    applicability: Applicability,
) -> None:
    """The two prerequisites the homogeneous set could not reach."""
    assert applicability_violations(applicability) == []


# ---------------------------------------------------------------------------
# Distinctions the source states and the representation must keep
# ---------------------------------------------------------------------------
#
# A representation is *false*, not merely lossy, when two things the source
# states differently produce one payload. Each group below is one the batch
# actually contains.

DISTINCT_GROUPS: dict[str, tuple[object, ...]] = {
    # Grants. An action per turn, a Reaction per exercise, an attack roll, and
    # a weapon change per attack are four different entitlements.
    "grants": (CASES["A1"][1], CASES["L2"][1], CASES["B1"][1], CASES["B3"][1]),
    # Timing. Attack states two binary axes over one permitted set, and the
    # four arms are the exact set it permits.
    "timing": tuple(
        EquipmentChangeFact(change=change, timing=timing)
        for change in EquipmentChange
        for timing in AttackRelativeTiming
    ),
    # Beneficiaries. Help's ally is neither the subject nor a roll against the
    # subject, which is the collapse RollActor.ALLY exists to prevent.
    "beneficiaries": tuple(
        AdvantageFact(
            state=AdvantageState.ADVANTAGE,
            roll=RollSpec(actor=actor, context=RollContext.ATTACK_ROLL),
        )
        for actor in RollActor
    ),
    # Sequencing. Movement placed inside a repeated action and a reaction
    # resolving after its trigger are different claims about different things.
    "sequencing": (CASES["B7"][1], CASES["L6"][1]),
    # Prerequisites. Two disjunctions over different vocabularies.
    "prerequisites": (DODGE_LOSS, HIDE_PREREQUISITE),
    # Durations. Which turn a benefit ends on is the whole content of the clause.
    "durations": (CASES["D3"][1], CASES["G4"][1]),
    # Expenditure, in both polarities the source states.
    "expenditure": (CASES["K4"][1], CASES["L7"][1]),
    # Eligibility, by what the rule ranges over.
    "eligibility": (CASES["K1"][1], CASES["O2"][1]),
    # Movement, by which of the subject's own speeds measures the grant.
    "movement": (CASES["D2"][1], CASES["D5"][1]),
}


def _canonical_form(value: object) -> bytes:
    payload = (
        fact_payload(value) if hasattr(value, "FAMILY") else _dataclass_payload(value)
    )
    return canonical_bytes(payload)


@pytest.mark.parametrize("axis", sorted(DISTINCT_GROUPS))
def test_the_source_distinctions_stay_apart_in_canonical_form(axis: str) -> None:
    """Distinct source meanings, distinct payloads — and therefore distinct keys."""
    values = DISTINCT_GROUPS[axis]
    forms = [_canonical_form(v) for v in values]
    assert len(set(forms)) == len(forms), axis


def test_the_settled_eligibility_correction_reads_alike_at_all_three_clauses() -> None:
    """L8's reclassification, and the sweep for the same error beside it.

    The checkpoint had ``Ready`` L8 as supporting authority. It is substantive
    eligibility: a spell's casting time is a printed, enumerable
    :class:`SpellDescriptorFact` field, so nothing in the clause is
    unenumerable fiction, and what it states is which spells the mechanic
    reaches.

    The sweep for comparable clauses found two — ``Magic`` K1 and ``Utilize``
    O2 — and both were already typed rather than misclassified, so only L8
    moved. K1 and L8 state the identical rule about spells and therefore have
    the identical key; O2 ranges over objects and does not.
    """
    magic, ready, utilize = CASES["K1"][1], CASES["L8"][1], CASES["O2"][1]
    assert fact_key(magic) == fact_key(ready)
    assert fact_key(utilize) != fact_key(magic)


# ---------------------------------------------------------------------------
# Malformed forms fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("obligation", sorted(CASES))
@pytest.mark.parametrize("damage", ["drop", "extra", "retype"])
def test_a_malformed_payload_is_refused_rather_than_repaired(
    obligation: str, damage: str
) -> None:
    """Three ways a stored payload can be wrong, and none of them rebuilds.

    A missing key would otherwise rebuild with a silently defaulted value; an
    extra key would be dropped, hiding whatever was added to the row; a retyped
    value would rebuild as something the source never stated.
    """
    _, fact = CASES[obligation]
    payload = dict(fact_payload(fact))
    keys = [k for k in payload if k != "family"]
    if damage == "drop":
        payload.pop(keys[0])
    elif damage == "extra":
        payload["invented"] = 1
    else:
        payload[keys[0]] = ["not a scalar"]
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)


@pytest.mark.parametrize(
    ("label", "fact"),
    [
        (
            "allowance-states-both-axes",
            ActionAllowanceFact(
                count=1,
                per=AllowanceScope.TURN,
                cost=ActionCost.ACTION,
                activity=GrantedActivity.ATTACK_ROLL,
            ),
        ),
        (
            "allowance-states-neither-axis",
            ActionAllowanceFact(count=1, per=AllowanceScope.TURN),
        ),
        (
            "allowance-of-none",
            ActionAllowanceFact(
                count=0, per=AllowanceScope.TURN, cost=ActionCost.ACTION
            ),
        ),
        (
            "duration-on-an-ally-clock",
            EffectDurationFact(
                until=RecurrenceBoundary.START_OF_TURN, whose=RollActor.ALLY
            ),
        ),
        (
            "duration-with-no-whose",
            EffectDurationFact(until=RecurrenceBoundary.START_OF_TURN),
        ),
        (
            "eligibility-by-a-cost-nothing-can-meet",
            ActivationCostEligibilityFact(
                subject=EligibilitySubject.SPELL, cost=ActionCost.NONE
            ),
        ),
        (
            "an-action-obligation-per-day",
            RecurringActionRequirementFact(cost=ActionCost.ACTION, per=TimeUnit.DAY),
        ),
        (
            "a-wait-that-bars-nothing",
            RetryRestrictionFact(
                amount=0, unit=TimeUnit.HOUR, gamemaster_may_set_other=False
            ),
        ),
        (
            "a-dc-against-the-subject-from-a-source-stating-no-such-roll",
            AbilityCheckFact(
                ability=AbilityScore.WISDOM,
                dc_kind=DcKind.GAMEMASTER_SET,
                against_subject=True,
                context=RollContext.ABILITY_CHECK,
            ),
        ),
        (
            "a-two-sided-dc-missing-the-score-it-yields-to",
            AbilityCheckFact(
                ability=None,
                dc_kind=DcKind.HIGHER_OF_FIXED_OR_TARGET_ABILITY_SCORE,
                dc_value=15,
                context=RollContext.ABILITY_CHECK,
            ),
        ),
        (
            "no-ability-but-a-skill-that-needs-one",
            AbilityCheckFact(
                ability=None,
                dc_kind=DcKind.FIXED,
                dc_value=15,
                skill=Skill.STEALTH,
                context=RollContext.ABILITY_CHECK,
            ),
        ),
    ],
)
def test_a_shape_schema_6_still_refuses_is_refused(label: str, fact: object) -> None:
    """A widening that admits everything states nothing."""
    assert fact_invariant_violations(fact), label


@pytest.mark.parametrize(
    ("label", "applicability"),
    [
        (
            "a-nested-disjunction",
            Applicability(
                kind=ApplicabilityKind.ANY_OF,
                any_of_terms=(HIDE_PREREQUISITE, CONCENTRATION_BROKEN),
            ),
        ),
        (
            "a-disjunction-of-one",
            Applicability(
                kind=ApplicabilityKind.ANY_OF, any_of_terms=(CONCENTRATION_BROKEN,)
            ),
        ),
        (
            "a-disjunction-in-authoring-order",
            Applicability(
                kind=ApplicabilityKind.ANY_OF,
                any_of_terms=tuple(reversed(HIDE_PREREQUISITE.any_of_terms)),
            ),
        ),
        (
            "a-disjunction-repeating-a-term",
            Applicability(
                kind=ApplicabilityKind.ANY_OF,
                any_of_terms=(CONCENTRATION_BROKEN, CONCENTRATION_BROKEN),
            ),
        ),
        (
            "a-condition-state-carrying-a-cover-degree",
            Applicability(
                kind=ApplicabilityKind.CONDITION_STATE,
                condition=ConditionKind.INCAPACITATED,
                cover=CoverDegree.TOTAL,
            ),
        ),
        (
            "an-obscurement-that-states-none",
            Applicability(kind=ApplicabilityKind.OBSCUREMENT),
        ),
    ],
)
def test_a_disjunction_shape_the_flat_set_refuses(
    label: str, applicability: Applicability
) -> None:
    """Flat, ordered, at least two, each distinct — the rules that bound it."""
    assert applicability_violations(applicability), label


# ---------------------------------------------------------------------------
# The two option sets the batch does *not* state
# ---------------------------------------------------------------------------
#
# Both were recorded in the checkpoint as blocked option sets, and both turn
# out to be the wrong model rather than a blocked one. Asserted here against
# ``option_set_violations`` so the decomposition is shown to be forced by the
# existing rule rather than chosen to make the batch pass.


def test_attacks_instrument_clause_is_not_an_option_set() -> None:
    """*"with a weapon or an Unarmed Strike."* — ``Attack``, p177.

    Both arms would state B1's single entitlement, and the rule refuses two
    options a consumer could not tell apart. The instrument clause is therefore
    bound prose on a ``MIXED`` component beside the allowance: which instruments
    qualify is not determined by this record, so
    ``contextual_applicability`` is affirmatively true of it.
    """
    entitlement = CASES["B1"][1]
    findings = option_set_violations(
        (),
        (
            ComponentOption(semantic_key="weapon", facts=(entitlement,)),
            ComponentOption(semantic_key="unarmed-strike", facts=(entitlement,)),
        ),
        "attack/instrument",
    )
    assert any("state the same typed facts" in f for f in findings), findings


def test_readys_action_choice_is_not_an_option_set() -> None:
    """*"you choose the action ... **or** ... move up to your Speed"* — Ready, p186.

    Arm one is open-ended prose: the action space includes whatever the
    subject's features provide, which no closed vocabulary reaches. An option
    must state at least one typed fact, so the set is unauthorable — and
    relaxing that rule to admit it is what would make the arm's emptiness
    indistinguishable from an authoring omission.
    """
    findings = option_set_violations(
        (),
        (
            ComponentOption(semantic_key="chosen-action", facts=()),
            ComponentOption(semantic_key="move", facts=(CASES["L4"][1],)),
        ),
        "ready/response",
    )
    assert any("states no typed facts" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Option-scoped governing prose
# ---------------------------------------------------------------------------
#
# ``Help`` (pp182-183) states an exhaustive actor choice and then governs one
# arm of it. Component-grain binding is *false* here rather than lossy, which
# is what these assert.

HELP_ABILITY_CHECK_ARM = "assist-an-ability-check"
HELP_ATTACK_ROLL_ARM = "assist-an-attack-roll"


def _help_binding(option_key: str) -> ProseBindingDraft:
    """*"The GM has final say on whether your assistance is possible."*"""
    return ProseBindingDraft(
        record_key="action.help",
        component_key="help-benefit",
        chunk_id="chunk-help-0001",
        span_id="span-help-gm-say",
        chunk_char_start=256,
        chunk_char_end=316,
        irreducibility_reason_code="gamemaster_latitude",
        option_key=option_key,
    )


def test_component_wide_prose_keeps_the_five_element_coordinate() -> None:
    """Every binding accepted before schema 6 addresses exactly as it did.

    The trailing element is appended only for an option-scoped binding, which
    is the same rule ``fact_target_key`` uses for its fourth. Nothing accepted
    moves, because nothing accepted is option-scoped.
    """
    binding = _help_binding(COMPONENT_WIDE_PROSE)
    assert prose_binding_target_key(binding) == (
        "action.help",
        "help-benefit",
        "chunk-help-0001",
        "span-help-gm-say",
        "gamemaster_latitude",
    )


def test_two_arms_of_one_choice_address_the_same_clause_distinctly() -> None:
    """The distinction component-grain binding cannot make.

    Bound to the component, the GM-latitude clause would govern the attack-roll
    arm as well — a false statement of scope. Bound to an option it governs the
    arm the source governs, and the two arms are separately addressable.
    """
    first = prose_binding_target_key(_help_binding(HELP_ABILITY_CHECK_ARM))
    second = prose_binding_target_key(_help_binding(HELP_ATTACK_ROLL_ARM))
    component_wide = prose_binding_target_key(_help_binding(COMPONENT_WIDE_PROSE))
    assert first != second
    assert len(first) == len(second) == len(component_wide) + 1
    assert first[:5] == second[:5] == component_wide


# An option key that names no option of its component is refused by the draft
# validator, and the binding's scope survives its own column and the raw
# closure check. Those are validator and storage paths rather than shapes, so
# they are proved in ``test_schema_6_reconstruction_paths`` against a real
# session — an assertion here could only restate this module's own fixtures.
