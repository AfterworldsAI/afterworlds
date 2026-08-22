"""Final effective option invariants — PR #155, round 6, finding 1.

Codex review round 6. The local checks inside the fact operations are
*per-scope*: an `APPEND` or `REPLACE` inside one option sees only that option's
facts, and a fact-scoped `DISABLE` is not resolved into removal until
`_finalize_component()`. None of them can see that two arms have become
indistinguishable, or that an arm has been emptied — those are component-wide
properties of the **final** state.

So `{A}` and `{A, B}` become two identical arms once `B` is appended to the
first, and `option_set_violations()` — the rule the corpus is built under —
rejects exactly that. The gap was that nothing asked it after the override set
had been applied.

Validation now runs once, after the whole ordered set is assembled and
suppression resolved, so a shape an intermediate entry creates and a later
entry legitimately repairs is never rejected. A violation fails the entire
application through `OverrideApplicationError`; no malformed partial view is
published.
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
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    MovementMode,
    MovementPermissionFact,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
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
from tests.services.rules_authority.conftest import DISABLE_PAYLOAD

_SCOPE = uuid5(UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40"), "final-option-invariants")

RECORD = "spell:wish"
CHOICE = "movement-choice"
LEFT = "left"
RIGHT = "right"

A = MovementPermissionFact(mode=MovementMode.CRAWL)
B = MovementPermissionFact(mode=MovementMode.SWIM)
C = MovementPermissionFact(mode=MovementMode.CLIMB)

_BINDING = ReleaseBinding(
    package_uuid=str(_SCOPE),
    release_version="5.2.1-final-invariants.fixture",
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
    package_uuid=_SCOPE,
    release_version=_BINDING.release_version,
    mechanical_projection_uuid=_SCOPE,
    override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
)


def candidate(
    left: tuple[object, ...], right: tuple[object, ...]
) -> ProjectionCandidate:
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=RECORD,
                semantic_key=CHOICE,
                handling=ComponentHandling.STRUCTURED,
                options=(
                    ComponentOption(semantic_key=LEFT, facts=left),  # type: ignore[arg-type]
                    ComponentOption(semantic_key=RIGHT, facts=right),  # type: ignore[arg-type]
                ),
            ),
        ),
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


def option_target(key: str) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.OPTION,
        record_key=RECORD,
        component_key=CHOICE,
        option_key=key,
    )


def fact_target(option_key: str, fact: object) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key=RECORD,
        component_key=CHOICE,
        fact_key=fact_key(fact),
        option_key=option_key,
    )


def entry(  # type: ignore[no-untyped-def]
    override_id: str,
    target: MechanicalTarget,
    operation: OverrideOperationEnum,
    payload: dict[str, object],
    order: int = 0,
):
    return EffectiveOverrideEntry(
        override_id=override_id,
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=target,
        operation=operation,
        precedence=100,
        apply_order=order,
        is_enabled=True,
        payload=payload,
    )


def append(fact: object) -> dict[str, object]:
    return {"patch": "append_fact", "fact": fact_payload(fact)}


def replace_fact(fact: object) -> dict[str, object]:
    return {"patch": "replace_fact", "fact": fact_payload(fact)}


def resolve(cand: ProjectionCandidate, *entries: EffectiveOverrideEntry):  # type: ignore[no-untyped-def]
    ordered = tuple(
        EffectiveOverrideEntry(
            override_id=e.override_id,
            origin=e.origin,
            target=e.target,
            operation=e.operation,
            precedence=e.precedence,
            apply_order=i,
            is_enabled=e.is_enabled,
            payload=e.payload,
        )
        for i, e in enumerate(entries)
    )
    state = EffectiveOverrideSet(
        package_uuid=_BINDING.package_uuid,
        release_version=_BINDING.release_version,
        entries=ordered,
    )
    return apply_override_set(cand, state, _PACKAGE_BINDING)


# ---------------------------------------------------------------------------
# 1. APPEND makes two arms identical
# ---------------------------------------------------------------------------


def test_an_append_that_makes_two_arms_identical_is_refused() -> None:
    """`{A}` and `{A, B}` — appending `B` to the first leaves two arms the
    source could not have distinguished."""
    with pytest.raises(OverrideApplicationError, match="same typed facts"):
        resolve(
            candidate(left=(A,), right=(A, B)),
            entry(
                "ov-append",
                option_target(LEFT),
                OverrideOperationEnum.APPEND,
                append(B),
            ),
        )


def test_an_append_that_keeps_the_arms_distinct_is_accepted() -> None:
    """The negative control: the check must not refuse every append."""
    view = resolve(
        candidate(left=(A,), right=(B,)),
        entry(
            "ov-append", option_target(LEFT), OverrideOperationEnum.APPEND, append(C)
        ),
    )
    (record,) = view.records
    (component,) = record.components
    scopes = {o.semantic_key: {f.fact_key for f in o.facts} for o in component.options}
    assert scopes == {LEFT: {fact_key(A), fact_key(C)}, RIGHT: {fact_key(B)}}


# ---------------------------------------------------------------------------
# 2. REPLACE makes two arms identical
# ---------------------------------------------------------------------------


def test_a_replace_that_makes_two_arms_identical_is_refused() -> None:
    """`{A}` and `{B}` — replacing `A` with `B` collapses them into one."""
    with pytest.raises(OverrideApplicationError, match="same typed facts"):
        resolve(
            candidate(left=(A,), right=(B,)),
            entry(
                "ov-replace",
                fact_target(LEFT, A),
                OverrideOperationEnum.REPLACE,
                replace_fact(B),
            ),
        )


# ---------------------------------------------------------------------------
# 3. DISABLE — including facts removed only at _finalize_component()
# ---------------------------------------------------------------------------


def test_a_disable_that_makes_two_arms_identical_is_refused() -> None:
    """`{A, B}` and `{A}` — suppressing `B` leaves two identical arms.

    A fact `DISABLE` is not resolved into removal until final assembly, so this
    is exactly the case a per-operation check cannot see.
    """
    with pytest.raises(OverrideApplicationError, match="same typed facts"):
        resolve(
            candidate(left=(A, B), right=(A,)),
            entry(
                "ov-disable",
                fact_target(LEFT, B),
                OverrideOperationEnum.DISABLE,
                DISABLE_PAYLOAD,
            ),
        )


def test_a_disable_that_empties_an_arm_is_refused() -> None:
    """An arm with nothing in it is not a choice the actor can take."""
    with pytest.raises(OverrideApplicationError, match="states no typed facts"):
        resolve(
            candidate(left=(A,), right=(B,)),
            entry(
                "ov-disable",
                fact_target(LEFT, A),
                OverrideOperationEnum.DISABLE,
                DISABLE_PAYLOAD,
            ),
        )


def test_a_later_entry_may_legitimately_repair_an_intermediate_shape() -> None:
    """**Final** state, not intermediate state.

    After the first entry alone the arms are `{A}` and `{A}` — invalid. The
    second entry appends `C` to the right arm and the final state is valid, so
    the set must be accepted. A per-operation check would have rejected the
    first entry and never seen the repair.
    """
    view = resolve(
        candidate(left=(A, B), right=(A,)),
        entry(
            "ov-disable",
            fact_target(LEFT, B),
            OverrideOperationEnum.DISABLE,
            DISABLE_PAYLOAD,
        ),
        entry(
            "ov-repair", option_target(RIGHT), OverrideOperationEnum.APPEND, append(C)
        ),
    )
    (record,) = view.records
    (component,) = record.components
    scopes = {o.semantic_key: {f.fact_key for f in o.facts} for o in component.options}
    assert scopes == {LEFT: {fact_key(A)}, RIGHT: {fact_key(A), fact_key(C)}}


def test_the_failure_names_the_last_override_to_touch_the_component() -> None:
    """Attribution is stated, not implied to be the sole cause."""
    with pytest.raises(OverrideApplicationError) as excinfo:
        resolve(
            candidate(left=(A, B), right=(A,)),
            entry(
                "ov-first",
                option_target(RIGHT),
                OverrideOperationEnum.APPEND,
                append(C),
            ),
            entry(
                "ov-last",
                fact_target(RIGHT, C),
                OverrideOperationEnum.DISABLE,
                DISABLE_PAYLOAD,
            ),
            entry(
                "ov-culprit",
                fact_target(LEFT, B),
                OverrideOperationEnum.DISABLE,
                DISABLE_PAYLOAD,
            ),
        )
    assert excinfo.value.override_id == "ov-culprit"
    assert "last override to touch it" in excinfo.value.detail


# ---------------------------------------------------------------------------
# 4. Siblings that must stay unaffected
# ---------------------------------------------------------------------------


def test_a_component_level_disable_does_not_trip_the_option_check() -> None:
    """A suppressed component publishes nothing, so it states no bad choice."""
    view = resolve(
        candidate(left=(A,), right=(B,)),
        entry(
            "ov-suppress",
            MechanicalTarget(
                kind=MechanicalTargetKind.COMPONENT,
                record_key=RECORD,
                component_key=CHOICE,
            ),
            OverrideOperationEnum.DISABLE,
            DISABLE_PAYLOAD,
        ),
    )
    (record,) = view.records
    assert record.components == ()


def test_a_record_level_disable_does_not_trip_the_option_check() -> None:
    view = resolve(
        candidate(left=(A,), right=(B,)),
        entry(
            "ov-suppress",
            MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=RECORD),
            OverrideOperationEnum.DISABLE,
            DISABLE_PAYLOAD,
        ),
    )
    assert view.records == ()


def test_a_component_with_direct_facts_and_no_options_is_untouched() -> None:
    """The check early-returns on a component that states no choice."""
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=RECORD,
                semantic_key="direct",
                handling=ComponentHandling.STRUCTURED,
                facts=(A,),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    cand = ProjectionCandidate(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=_BINDING,
        classification=_CLASSIFICATION,
        representation=draft,
    )
    view = resolve(
        cand,
        entry(
            "ov-append",
            MechanicalTarget(
                kind=MechanicalTargetKind.COMPONENT,
                record_key=RECORD,
                component_key="direct",
            ),
            OverrideOperationEnum.APPEND,
            append(B),
        ),
    )
    (record,) = view.records
    (component,) = record.components
    assert {f.fact_key for f in component.facts} == {fact_key(A), fact_key(B)}


def test_a_base_projection_with_no_overrides_is_unaffected() -> None:
    """The check must not reject authority the corpus already accepted."""
    view = resolve(candidate(left=(A,), right=(B,)))
    (record,) = view.records
    (component,) = record.components
    assert len(component.options) == 2


def test_option_fact_provenance_survives_the_check() -> None:
    """Validation projects into representation types; it must not rewrite the view."""
    view = resolve(
        candidate(left=(A,), right=(B,)),
        entry(
            "ov-append", option_target(LEFT), OverrideOperationEnum.APPEND, append(C)
        ),
    )
    (record,) = view.records
    (component,) = record.components
    left = next(o for o in component.options if o.semantic_key == LEFT)
    added = next(f for f in left.facts if f.fact_key == fact_key(C))
    assert added.supplied_by_override_id == "ov-append"
    assert added.option_key == LEFT
    original = next(f for f in left.facts if f.fact_key == fact_key(A))
    assert original.supplied_by_override_id is None
