"""Counterpart establishment survives override application — PR #157, round 8.

Codex review on PR #157, P1. The schema-3 counterpart rule was enforced only
during base ``RepresentationDraft`` validation, so ``apply_override_set()``
could publish an effective Rules Package state the base schema rejects. Two
ways in, and both are exercised below:

* a ``REPLACE`` supplying a component whose facts name ``COUNTERPART`` with
  nothing establishing it; and
* a ``DISABLE`` removing the sole ``MovementTransportFact`` while the
  counterpart-paid cost that depended on it survives beside it.

Neither is visible to any per-scope operation. A complete component patch never
sees what it replaced, and a fact-scoped ``DISABLE`` is not resolved into
removal until ``_finalize_component`` — so, exactly like the option-set
contract before it, the rule has to be asked again of the *final* state.

The rule itself is not restated here: ``_verify_final_participant_rules``
projects the effective view back into the representation's own types and calls
``component_participant_violations``, the same function the corpus is built
under. A second copy would drift from the schema it enforces.
"""

from __future__ import annotations

from uuid import UUID, uuid5

import pytest

from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    applicability_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    FactQualifier,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    MovementTransportFact,
    ParticipantRole,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RoundingRule,
    SizeComparison,
    SizeRelation,
    TransportKind,
    fact_key,
    fact_payload,
    fact_qualifier_target_key,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.application import (
    OverrideApplicationError,
    apply_override_set,
)
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
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

_SCOPE_UUID = uuid5(UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40"), "final-participant")

RECORD_KEY = "condition.grappled"
MOVABLE_KEY = "movable"
CHOICE_KEY = "movement-choice"

SUBJECT, COUNTERPART = ParticipantRole.SUBJECT, ParticipantRole.COUNTERPART

#: Grappled > Movable, exactly as the corpus states it.
TRANSPORT = MovementTransportFact(
    carrier=COUNTERPART, carried=SUBJECT, kind=TransportKind.PERMITTED
)
SURCHARGE = MovementCostFact(
    kind=MovementCostKind.PER_FOOT_SURCHARGE,
    amount=MovementAmount.FEET,
    payer=COUNTERPART,
    feet=1,
)
#: Subject-paid, so it depends on nothing being established.
PRONE_STAND = MovementCostFact(
    kind=MovementCostKind.EXPENDITURE,
    amount=MovementAmount.HALF_SPEED,
    payer=SUBJECT,
    rounding=RoundingRule.DOWN,
)
CRAWL = MovementPermissionFact(mode=MovementMode.CRAWL)

SIZE_EXCEPTION = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    negated=True,
    any_of=(
        SizeComparison(
            relation=SizeRelation.SMALLER,
            at_least=2,
            measured=SUBJECT,
            reference=COUNTERPART,
        ),
    ),
)

_BINDING = ReleaseBinding(
    package_uuid="pkg-final-participant",
    release_version="5.2.1-final-participant.fixture",
    authoritative_source_hash="a" * 64,
    transform_config_hash="b" * 64,
    bundle_root_hash="c" * 64,
    persisted_corpus_digest="d" * 64,
)
_CLASSIFICATION = ClassificationLedger(
    package_uuid=_BINDING.package_uuid,
    release_version=_BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=(),
    batches=(),
    acceptances=(),
)
_PACKAGE_BINDING = RulesPackageBinding(
    package_uuid=_SCOPE_UUID,
    release_version=_BINDING.release_version,
    mechanical_projection_uuid=_SCOPE_UUID,
    override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
)


def _candidate(*components: ComponentDraft) -> ProjectionCandidate:
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.CONDITION),),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    return ProjectionCandidate(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=_BINDING,
        classification=_CLASSIFICATION,
        representation=draft,
    )


def _movable(*facts: object) -> ComponentDraft:
    return ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key=MOVABLE_KEY,
        handling=ComponentHandling.STRUCTURED,
        facts=facts,  # type: ignore[arg-type]
    )


def _entry(
    target: MechanicalTarget,
    operation: OverrideOperationEnum,
    payload: dict[str, object],
    *,
    override_id: str = "ov-1",
) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=override_id,
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=target,
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=payload,
    )


def _apply(candidate: ProjectionCandidate, *entries: EffectiveOverrideEntry):  # type: ignore[no-untyped-def]
    ordered = tuple(
        EffectiveOverrideEntry(
            override_id=e.override_id,
            origin=e.origin,
            target=e.target,
            operation=e.operation,
            precedence=e.precedence,
            apply_order=index,
            is_enabled=e.is_enabled,
            payload=e.payload,
        )
        for index, e in enumerate(entries)
    )
    state = EffectiveOverrideSet(
        package_uuid=_BINDING.package_uuid,
        release_version=_BINDING.release_version,
        entries=ordered,
    )
    return apply_override_set(candidate, state, _PACKAGE_BINDING)


COMPONENT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.COMPONENT,
    record_key=RECORD_KEY,
    component_key=MOVABLE_KEY,
)


def _fact_target(key: str, option_key: str | None = None) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key=RECORD_KEY,
        component_key=MOVABLE_KEY if option_key is None else CHOICE_KEY,
        option_key=option_key,
        fact_key=key,
    )


# ---------------------------------------------------------------------------
# The base state this all starts from is valid
# ---------------------------------------------------------------------------


def test_the_unmodified_grappled_component_applies_cleanly() -> None:
    """Transport beside its surcharge is exactly what the corpus states."""
    view = _apply(_candidate(_movable(TRANSPORT, SURCHARGE)))
    (record,) = view.records
    (component,) = record.components
    assert {f.fact_key for f in component.facts} == {
        fact_key(TRANSPORT),
        fact_key(SURCHARGE),
    }


# ---------------------------------------------------------------------------
# 1. A replacement introducing COUNTERPART with nothing establishing it
# ---------------------------------------------------------------------------


def test_replacing_a_component_cannot_introduce_an_unestablished_counterpart() -> None:
    """The patch never sees what it replaced, so only the final state can tell."""
    with pytest.raises(OverrideApplicationError) as excinfo:
        _apply(
            _candidate(_movable(TRANSPORT, SURCHARGE)),
            _entry(
                COMPONENT_TARGET,
                OverrideOperationEnum.REPLACE,
                {
                    "patch": "replace_component",
                    "component": {
                        "handling": "structured",
                        "facts": [fact_payload(SURCHARGE)],
                    },
                },
            ),
        )
    assert "counterpart reference nothing establishes" in excinfo.value.detail
    assert excinfo.value.override_id == "ov-1"


def test_a_replacement_carrying_its_own_transport_is_accepted() -> None:
    """The rule refuses an unestablished reference, not the counterpart role."""
    view = _apply(
        _candidate(_movable(TRANSPORT, SURCHARGE)),
        _entry(
            COMPONENT_TARGET,
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(TRANSPORT), fact_payload(SURCHARGE)],
                },
            },
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert len(component.facts) == 2


def test_a_replacement_with_no_counterpart_authority_is_accepted() -> None:
    """A subject-only component establishes nothing and needs nothing."""
    view = _apply(
        _candidate(_movable(TRANSPORT, SURCHARGE)),
        _entry(
            COMPONENT_TARGET,
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(PRONE_STAND)],
                },
            },
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert [f.fact_key for f in component.facts] == [fact_key(PRONE_STAND)]


def test_a_replacement_applicability_cannot_smuggle_in_a_counterpart() -> None:
    """The size exception is counterpart-bearing authority too, not just facts."""
    with pytest.raises(OverrideApplicationError) as excinfo:
        _apply(
            _candidate(_movable(TRANSPORT, SURCHARGE)),
            _entry(
                COMPONENT_TARGET,
                OverrideOperationEnum.REPLACE,
                {
                    "patch": "replace_component",
                    "component": {
                        "handling": "structured",
                        "facts": [fact_payload(PRONE_STAND)],
                        "applies_when": {
                            "kind": "size_comparison",
                            "negated": True,
                            "quantity": None,
                            "comparison": None,
                            "value": None,
                            "any_of": [
                                {
                                    "category": None,
                                    "relation": "smaller",
                                    "at_least": 2,
                                    "at_most": None,
                                    "measured": "subject",
                                    "reference": "counterpart",
                                }
                            ],
                            "trigger": None,
                            "phase": None,
                        },
                    },
                },
            ),
        )
    assert "counterpart reference nothing establishes" in excinfo.value.detail


# ---------------------------------------------------------------------------
# 2. Disabling the sole establishing transport
# ---------------------------------------------------------------------------


def test_disabling_the_sole_transport_fact_is_refused() -> None:
    """Suppression is only resolved at finalization, so nothing earlier sees it.

    The surcharge survives and still names the counterpart, but the relation
    that named it is gone — a claim about a creature the structure can no
    longer identify.
    """
    with pytest.raises(OverrideApplicationError) as excinfo:
        _apply(
            _candidate(_movable(TRANSPORT, SURCHARGE)),
            _entry(
                _fact_target(fact_key(TRANSPORT)),
                OverrideOperationEnum.DISABLE,
                {"patch": "disable"},
            ),
        )
    assert "counterpart reference nothing establishes" in excinfo.value.detail


def test_disabling_the_dependent_cost_instead_is_accepted() -> None:
    """Removing the dependant, not the relation, leaves a coherent state."""
    view = _apply(
        _candidate(_movable(TRANSPORT, SURCHARGE)),
        _entry(
            _fact_target(fact_key(SURCHARGE)),
            OverrideOperationEnum.DISABLE,
            {"patch": "disable"},
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert [f.fact_key for f in component.facts] == [fact_key(TRANSPORT)]


def test_disabling_transport_where_nothing_depends_on_it_is_accepted() -> None:
    """The rule is about surviving references, not about transport itself."""
    view = _apply(
        _candidate(_movable(TRANSPORT, PRONE_STAND)),
        _entry(
            _fact_target(fact_key(TRANSPORT)),
            OverrideOperationEnum.DISABLE,
            {"patch": "disable"},
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert [f.fact_key for f in component.facts] == [fact_key(PRONE_STAND)]


# ---------------------------------------------------------------------------
# 3. Option scope
# ---------------------------------------------------------------------------


def _choice(*options: ComponentOption) -> ComponentDraft:
    return ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key=CHOICE_KEY,
        handling=ComponentHandling.STRUCTURED,
        options=options,
    )


def test_appending_a_counterpart_cost_into_an_unestablished_arm_is_refused() -> None:
    """``(APPEND, OPTION)`` is the one way to add a fact into a choice arm."""
    with pytest.raises(OverrideApplicationError) as excinfo:
        _apply(
            _candidate(
                _choice(
                    ComponentOption(semantic_key="crawl", facts=(CRAWL,)),
                    ComponentOption(semantic_key="stand", facts=(PRONE_STAND,)),
                )
            ),
            _entry(
                MechanicalTarget(
                    kind=MechanicalTargetKind.OPTION,
                    record_key=RECORD_KEY,
                    component_key=CHOICE_KEY,
                    option_key="crawl",
                ),
                OverrideOperationEnum.APPEND,
                {"patch": "append_fact", "fact": fact_payload(SURCHARGE)},
            ),
        )
    assert "counterpart reference nothing establishes" in excinfo.value.detail
    assert "option crawl" in excinfo.value.detail


def test_an_arm_establishing_its_own_counterpart_is_accepted() -> None:
    """Within one arm, transport and the cost it carries resolve together."""
    view = _apply(
        _candidate(
            _choice(
                ComponentOption(semantic_key="carried", facts=(TRANSPORT,)),
                ComponentOption(semantic_key="stand", facts=(PRONE_STAND,)),
            )
        ),
        _entry(
            MechanicalTarget(
                kind=MechanicalTargetKind.OPTION,
                record_key=RECORD_KEY,
                component_key=CHOICE_KEY,
                option_key="carried",
            ),
            OverrideOperationEnum.APPEND,
            {"patch": "append_fact", "fact": fact_payload(SURCHARGE)},
        ),
    )
    (record,) = view.records
    (component,) = record.components
    carried = next(o for o in component.options if o.semantic_key == "carried")
    assert {f.fact_key for f in carried.facts} == {
        fact_key(TRANSPORT),
        fact_key(SURCHARGE),
    }


def test_a_sibling_arms_transport_does_not_establish_across_the_choice() -> None:
    """Mutually exclusive arms: the arm not taken established nothing.

    The build-time rule already refuses this; the point here is that the
    override path refuses it too, rather than being a looser second copy.
    """
    with pytest.raises(OverrideApplicationError) as excinfo:
        _apply(
            _candidate(
                _choice(
                    ComponentOption(semantic_key="carried", facts=(TRANSPORT,)),
                    ComponentOption(semantic_key="stand", facts=(PRONE_STAND,)),
                )
            ),
            _entry(
                MechanicalTarget(
                    kind=MechanicalTargetKind.OPTION,
                    record_key=RECORD_KEY,
                    component_key=CHOICE_KEY,
                    option_key="stand",
                ),
                OverrideOperationEnum.APPEND,
                {"patch": "append_fact", "fact": fact_payload(SURCHARGE)},
            ),
        )
    assert "option stand" in excinfo.value.detail


def test_component_level_transport_establishes_for_every_arm() -> None:
    """Component facts hold whichever arm is taken, so they establish for all."""
    view = _apply(
        _candidate(
            ComponentDraft(
                record_key=RECORD_KEY,
                semantic_key=MOVABLE_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(TRANSPORT, SURCHARGE),
                applies_when=SIZE_EXCEPTION,
            )
        )
    )
    (record,) = view.records
    (component,) = record.components
    assert component.applies_when == SIZE_EXCEPTION


# ---------------------------------------------------------------------------
# Fact-scoped qualifiers through the override path (PR #157, round 2)
# ---------------------------------------------------------------------------
#
# A qualifier lives on the fact it limits and never outlives it. REPLACE and
# DISABLE both remove it with that fact; APPEND adds an unqualified one; and a
# complete component patch states its own set or has none. So the qualifier's
# authorship always matches its fact's, and no operation can leave a
# source-authored limitation attached to authority that never declared it.

QUALIFIER_SPAN = "span-size-exception"


def _qualified_candidate(
    facts: tuple[object, ...] = (TRANSPORT, SURCHARGE),
    qualified: object = SURCHARGE,
) -> ProjectionCandidate:
    """Grappled as the source states it: unconditional transport, qualified cost."""
    component = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key=MOVABLE_KEY,
        handling=ComponentHandling.STRUCTURED,
        facts=facts,  # type: ignore[arg-type]
        fact_qualifiers=(
            FactQualifier(
                fact_key=fact_key(qualified),  # type: ignore[arg-type]
                applies_when=SIZE_EXCEPTION,
            ),
        ),
    )
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.CONDITION),),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                target_kind=ProvenanceTargetKind.FACT_QUALIFIER,
                target_key=fact_qualifier_target_key(
                    RECORD_KEY,
                    MOVABLE_KEY,
                    fact_key(qualified),  # type: ignore[arg-type]
                    "",
                ),
                span_id=QUALIFIER_SPAN,
                role=ProvenanceRole.PRIMARY,
            ),
        ),
    )
    return ProjectionCandidate(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=_BINDING,
        classification=_CLASSIFICATION,
        representation=draft,
    )


def _fact(view, key):  # type: ignore[no-untyped-def]
    (record,) = view.records
    (component,) = record.components
    return next(f for f in component.facts if f.fact_key == key)


def test_the_base_view_carries_the_qualifier_with_its_own_source_span() -> None:
    view = _apply(_qualified_candidate())
    transport = _fact(view, fact_key(TRANSPORT))
    surcharge = _fact(view, fact_key(SURCHARGE))
    assert transport.qualifier is None, "transport is unconditional"
    assert surcharge.qualifier is not None
    assert surcharge.qualifier.applies_when == SIZE_EXCEPTION
    assert surcharge.qualifier.span_ids == (QUALIFIER_SPAN,)
    # The qualifier's span is its own; it is not merged into the fact's set.
    assert QUALIFIER_SPAN not in surcharge.span_ids


def _all_span_ids(view) -> set[str]:  # type: ignore[no-untyped-def]
    """Every 5c span the effective view still cites, wherever it cites it."""
    seen: set[str] = set()
    for record in view.records:
        for component in record.components:
            seen.update(component.span_ids)
            facts = (
                *component.facts,
                *(f for option in component.options for f in option.facts),
            )
            for f in facts:
                seen.update(f.span_ids)
                if f.qualifier is not None:
                    seen.update(f.qualifier.span_ids)
    return seen


#: The families a replacement can arrive as. REPLACE constrains none of them,
#: which is why inheritance could not be made safe by a compatibility test: the
#: first is the closest possible relative of the fact it replaces, and is still
#: not evidence that a size exception written for the original applies to it.
REPLACEMENTS = [
    (
        "same family",
        MovementCostFact(
            kind=MovementCostKind.PER_FOOT_SURCHARGE,
            amount=MovementAmount.FEET,
            payer=COUNTERPART,
            feet=2,
        ),
    ),
    ("different family", MovementPermissionFact(mode=MovementMode.SWIM)),
]


@pytest.mark.parametrize(
    ("label", "replacement"), REPLACEMENTS, ids=[label for label, _ in REPLACEMENTS]
)
def test_fact_replace_drops_the_qualifier_with_the_fact_it_named(
    label: str, replacement: object
) -> None:
    """Owner decision, PR #157 finding 6.

    ``REPLACE`` supplies a *complete* validated fact, so the replacement is
    unqualified. Inheriting would preserve a source-authored limitation the
    replacement payload never declares — and since nothing constrains the
    replacement's family, Grappled's size exception could end up limiting
    unrelated authority while still citing the clause that states it.
    """
    view = _apply(
        _qualified_candidate(),
        _entry(
            _fact_target(fact_key(SURCHARGE)),
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_fact",
                "fact": fact_payload(replacement),  # type: ignore[arg-type]
            },
        ),
    )
    new = _fact(view, fact_key(replacement))  # type: ignore[arg-type]
    # Fact authority: the override, as before.
    assert new.supplied_by_override_id == "ov-1"
    assert new.span_ids == ()
    # And it carries no limitation the override did not state.
    assert new.qualifier is None, label
    # Nothing else picked the qualifier up either, and its source span is gone
    # from the view entirely — "qualifier is None" alone would not prove the
    # provenance had not leaked somewhere else.
    (record,) = view.records
    (component,) = record.components
    assert all(f.qualifier is None for f in component.facts), label
    assert QUALIFIER_SPAN not in _all_span_ids(view), label


def test_a_conditional_replacement_is_authored_as_a_component_patch() -> None:
    """The supported way to replace a fact and keep it conditional.

    Fact ``REPLACE`` cannot say "and it still only applies when…" — that is a
    two-part claim and the patch carries one fact. A component patch carries
    both, so a conditional replacement is authored there, and the qualifier is
    then the override's own authority rather than inherited source text.
    """
    view = _apply(
        _qualified_candidate(),
        _entry(
            COMPONENT_TARGET,
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(TRANSPORT), fact_payload(PRONE_STAND)],
                    "fact_qualifiers": [
                        {
                            "fact_key": fact_key(PRONE_STAND),
                            "option_key": "",
                            "applies_when": applicability_payload(SIZE_EXCEPTION),
                        }
                    ],
                },
            },
        ),
    )
    stand = _fact(view, fact_key(PRONE_STAND))
    assert stand.qualifier is not None
    assert stand.qualifier.applies_when == SIZE_EXCEPTION
    # Override authority: it names the override, and no 5c span anywhere.
    assert stand.qualifier.supplied_by_override_id == "ov-1"
    assert stand.qualifier.span_ids == ()
    assert QUALIFIER_SPAN not in _all_span_ids(view)


# Dropping a qualifier is a *widening*, and a qualifier can name COUNTERPART,
# so the final participant rule has to be asked of the dropped state. Both
# directions below: what the qualifier stops claiming, and what the
# replacement starts claiming.


def _counterpart_only_in_the_qualifier() -> ProjectionCandidate:
    """Transport, a subject-paid cost, and COUNTERPART named only by the qualifier.

    ``SIZE_EXCEPTION`` compares the subject *to the counterpart*, so with the
    cost beside it subject-paid, the qualifier is the sole counterpart
    reference.
    """
    return _qualified_candidate((TRANSPORT, PRONE_STAND), PRONE_STAND)


def test_a_qualifier_naming_the_counterpart_still_needs_it_established() -> None:
    """Control: the final rule reads qualifiers, so the next case means something."""
    with pytest.raises(OverrideApplicationError, match="nothing establishes"):
        _apply(
            _counterpart_only_in_the_qualifier(),
            _entry(
                _fact_target(fact_key(TRANSPORT)),
                OverrideOperationEnum.DISABLE,
                {"patch": "disable"},
            ),
        )


def test_dropping_a_qualifier_drops_the_counterpart_reference_it_carried() -> None:
    """And the final rule sees the dropped state, not the state before it.

    Replacing the qualified fact removes the only claim about the counterpart,
    so disabling transport afterwards is accepted where the control above
    refuses it. Pinned deliberately: that is the correct consequence of the
    owner's REPLACE semantics, not a weakened invariant.
    """
    view = _apply(
        _counterpart_only_in_the_qualifier(),
        _entry(
            _fact_target(fact_key(PRONE_STAND)),
            OverrideOperationEnum.REPLACE,
            {"patch": "replace_fact", "fact": fact_payload(CRAWL)},
        ),
        _entry(
            _fact_target(fact_key(TRANSPORT)),
            OverrideOperationEnum.DISABLE,
            {"patch": "disable"},
            override_id="ov-2",
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert [f.fact_key for f in component.facts] == [fact_key(CRAWL)]
    assert all(f.qualifier is None for f in component.facts)


def test_a_replacement_naming_the_counterpart_itself_is_still_checked() -> None:
    """The other direction: the replacement's own COUNTERPART needs establishing.

    Dropping the qualifier does not weaken the rule for what the override
    *does* say — the counterpart-paid replacement is accepted here only because
    transport survives beside it.
    """
    surcharge_2ft = MovementCostFact(
        kind=MovementCostKind.PER_FOOT_SURCHARGE,
        amount=MovementAmount.FEET,
        payer=COUNTERPART,
        feet=2,
    )
    replace_it = _entry(
        _fact_target(fact_key(PRONE_STAND)),
        OverrideOperationEnum.REPLACE,
        {"patch": "replace_fact", "fact": fact_payload(surcharge_2ft)},
    )
    view = _apply(_counterpart_only_in_the_qualifier(), replace_it)
    assert _fact(view, fact_key(surcharge_2ft)).qualifier is None

    # The same override, with nothing establishing the counterpart: refused.
    with pytest.raises(OverrideApplicationError, match="nothing establishes"):
        _apply(_qualified_candidate((PRONE_STAND,), PRONE_STAND), replace_it)


def test_fact_disable_removes_the_qualifier_with_its_fact() -> None:
    """No dangling qualifier can survive: it lives on the fact."""
    view = _apply(
        _qualified_candidate(),
        _entry(
            _fact_target(fact_key(SURCHARGE)),
            OverrideOperationEnum.DISABLE,
            {"patch": "disable"},
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert [f.fact_key for f in component.facts] == [fact_key(TRANSPORT)]
    assert all(f.qualifier is None for f in component.facts)


def test_fact_append_creates_an_unqualified_fact() -> None:
    added = MovementPermissionFact(mode=MovementMode.SWIM)
    view = _apply(
        _candidate(_movable(TRANSPORT, SURCHARGE)),
        _entry(
            MechanicalTarget(
                kind=MechanicalTargetKind.COMPONENT,
                record_key=RECORD_KEY,
                component_key=MOVABLE_KEY,
            ),
            OverrideOperationEnum.APPEND,
            {"patch": "append_fact", "fact": fact_payload(added)},
        ),
    )
    assert _fact(view, fact_key(added)).qualifier is None


def test_component_replacement_carries_its_complete_qualifier_set() -> None:
    """Complete, like every other field of a component patch."""
    view = _apply(
        _qualified_candidate(),
        _entry(
            COMPONENT_TARGET,
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(TRANSPORT), fact_payload(SURCHARGE)],
                    "fact_qualifiers": [
                        {
                            "fact_key": fact_key(SURCHARGE),
                            "option_key": "",
                            "applies_when": applicability_payload(SIZE_EXCEPTION),
                        }
                    ],
                },
            },
        ),
    )
    surcharge = _fact(view, fact_key(SURCHARGE))
    assert surcharge.qualifier is not None
    # Override-supplied authority names 5c spans nowhere.
    assert surcharge.qualifier.span_ids == ()
    assert surcharge.qualifier.supplied_by_override_id == "ov-1"


def test_a_replacement_omitting_a_qualifier_drops_it_rather_than_inheriting() -> None:
    view = _apply(
        _qualified_candidate(),
        _entry(
            COMPONENT_TARGET,
            OverrideOperationEnum.REPLACE,
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(TRANSPORT), fact_payload(SURCHARGE)],
                },
            },
        ),
    )
    assert _fact(view, fact_key(SURCHARGE)).qualifier is None


def test_a_component_patch_qualifier_naming_no_such_fact_is_refused() -> None:
    with pytest.raises(InvalidPatchError, match="does not hold"):
        patch_from_payload(
            {
                "patch": "replace_component",
                "component": {
                    "handling": "structured",
                    "facts": [fact_payload(TRANSPORT)],
                    "fact_qualifiers": [
                        {
                            "fact_key": fact_key(SURCHARGE),
                            "option_key": "",
                            "applies_when": applicability_payload(SIZE_EXCEPTION),
                        }
                    ],
                },
            },
            operation=OverrideOperationEnum.REPLACE,
            target=COMPONENT_TARGET,
        )
