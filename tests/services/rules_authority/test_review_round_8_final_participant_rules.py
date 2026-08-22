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
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    MovementTransportFact,
    ParticipantRole,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RoundingRule,
    SizeComparison,
    SizeRelation,
    TransportKind,
    fact_key,
    fact_payload,
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
