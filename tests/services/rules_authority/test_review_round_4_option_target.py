"""``OPTION`` is an APPEND-only container target — PR #155, round 4.

Codex review round 4, Owner Decision 2026-08-19. Schema 2 gave
``_apply_entry()`` option-aware append code that nothing could reach:
``(APPEND, FACT)`` is unsupported, ``(APPEND, COMPONENT)`` is the only fact
addition, and ``MechanicalTarget`` rejected ``option_key`` on every non-``FACT``
target. So appending a fact to either arm of a choice always fell into the
*"a fact must be appended to one of its options, not beside them"* refusal —
a schema-permitted operation with no encoding.

``OPTION`` is that encoding, and only that. ``(APPEND, OPTION)`` →
``FactAdditionPatch`` is the sole permitted pairing:

* ``DISABLE`` and ``REPLACE`` on an option stay unsupported. The source states
  the choice as **exhaustive**, so suppressing or rewriting one arm would
  publish a choice the source never states.
* ``(APPEND, FACT)`` stays unsupported for the older, different reason — a fact
  has no multiplicity to append into.

An option is therefore addressable as a fact container and in no other way. It
reuses the existing ``target_option_key`` column; there is no second scope
field and no new migration.
"""

from __future__ import annotations

from uuid import UUID, uuid5

import pytest
from sqlalchemy import select

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
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    ParticipantRole,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RoundingRule,
    fact_key,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.rules_authority import (
    MechanicalOverrideORM,
    OverrideSetEntryORM,
)
from afterworlds.services.rules_authority import (
    collect_current_override_state,
    load_override_set_version,
    retain_override_set,
)
from afterworlds.services.rules_authority.application import (
    OverrideApplicationError,
    apply_override_set,
)
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    override_set_identity,
)
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    required_patch_family,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
    TargetShapeError,
    target_payload,
)
from afterworlds.services.rules_authority.views import (
    build_gamemaster_view,
    build_typed_view,
)
from tests.services.rules_authority.conftest import (
    DISABLE_PAYLOAD,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
)

_SCOPE_UUID = uuid5(UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40"), "option-target-proof")

CHOICE_KEY = "movement-choice"
DIRECT_KEY = "direct"
CRAWL_OPTION = "crawl"
STAND_OPTION = "stand"

CRAWL_FACT = MovementPermissionFact(mode=MovementMode.CRAWL)
STAND_FACT = MovementCostFact(
    kind=MovementCostKind.EXPENDITURE,
    amount=MovementAmount.HALF_SPEED,
    payer=ParticipantRole.SUBJECT,
    rounding=RoundingRule.DOWN,
)
#: Appended by the overrides below. A family neither option already states.
ADDED_FACT = MovementPermissionFact(mode=MovementMode.SWIM)
ADDED_KEY = fact_key(ADDED_FACT)
#: Present in *both* options already, so an append of it must fail per-option
#: rather than globally — the isolation case.
SHARED_FACT = MovementPermissionFact(mode=MovementMode.CLIMB)
SHARED_KEY = fact_key(SHARED_FACT)


def option_target(option_key: str, component_key: str = CHOICE_KEY) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.OPTION,
        record_key=SPELL_KEY,
        component_key=component_key,
        option_key=option_key,
    )


CRAWL_TARGET = option_target(CRAWL_OPTION)
STAND_TARGET = option_target(STAND_OPTION)


def append_payload(fact: object = ADDED_FACT) -> dict[str, object]:
    return {"patch": "append_fact", "fact": fact_payload(fact)}


# ---------------------------------------------------------------------------
# Shape and matrix
# ---------------------------------------------------------------------------


def test_an_option_target_requires_its_record_component_and_option() -> None:
    assert CRAWL_TARGET.option_key == CRAWL_OPTION
    with pytest.raises(TargetShapeError, match="requires a component_key"):
        MechanicalTarget(
            kind=MechanicalTargetKind.OPTION,
            record_key=SPELL_KEY,
            option_key=CRAWL_OPTION,
        )
    for blank in (None, "", "   "):
        with pytest.raises(TargetShapeError, match="requires an option_key"):
            MechanicalTarget(
                kind=MechanicalTargetKind.OPTION,
                record_key=SPELL_KEY,
                component_key=CHOICE_KEY,
                option_key=blank,
            )


def test_an_option_target_must_not_name_a_fact() -> None:
    """A container and one of its members are two targets, not one."""
    with pytest.raises(TargetShapeError, match="must not carry a fact_key"):
        MechanicalTarget(
            kind=MechanicalTargetKind.OPTION,
            record_key=SPELL_KEY,
            component_key=CHOICE_KEY,
            option_key=CRAWL_OPTION,
            fact_key=ADDED_KEY,
        )


def test_append_is_the_only_operation_an_option_admits() -> None:
    from afterworlds.services.rules_authority.patches import PatchFamily

    assert (
        required_patch_family(OverrideOperationEnum.APPEND, MechanicalTargetKind.OPTION)
        is PatchFamily.APPEND_FACT
    )
    for operation in (OverrideOperationEnum.DISABLE, OverrideOperationEnum.REPLACE):
        with pytest.raises(InvalidPatchError, match="exhaustive arm of a choice"):
            required_patch_family(operation, MechanicalTargetKind.OPTION)


def test_append_on_a_fact_target_remains_unsupported() -> None:
    """Adding OPTION must not have opened the older, unrelated pairing."""
    with pytest.raises(InvalidPatchError, match="no multiplicity"):
        required_patch_family(OverrideOperationEnum.APPEND, MechanicalTargetKind.FACT)


# ---------------------------------------------------------------------------
# Canonical identity
# ---------------------------------------------------------------------------


def _entry(
    target: MechanicalTarget,
    *,
    override_id: str = "ov-1",
    operation: OverrideOperationEnum = OverrideOperationEnum.APPEND,
    payload: dict[str, object] | None = None,
) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=override_id,
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=target,
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=append_payload() if payload is None else payload,
    )


def test_an_option_target_canonicalizes_with_its_kind_and_scope() -> None:
    assert target_payload(CRAWL_TARGET) == {
        "kind": "option",
        "record_key": SPELL_KEY,
        "component_key": CHOICE_KEY,
        "fact_key": None,
        "option_key": CRAWL_OPTION,
    }
    assert (
        CRAWL_TARGET.describe() == f"option:{SPELL_KEY}/{CHOICE_KEY}/[{CRAWL_OPTION}]"
    )


def test_two_option_targets_are_distinct_authorities() -> None:
    assert override_set_identity((_entry(CRAWL_TARGET),)) != override_set_identity(
        (_entry(STAND_TARGET),)
    )


def test_legacy_direct_target_identity_is_still_unmoved() -> None:
    """The literals pinned in round 3, re-asserted after adding a target kind."""
    legacy = MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key="rec",
        component_key="comp",
        fact_key="f1",
    )
    assert (
        override_set_identity(
            (
                _entry(
                    legacy,
                    operation=OverrideOperationEnum.DISABLE,
                    payload=DISABLE_PAYLOAD,
                ),
            )
        )
        == "8404b420-e92e-5c5a-968d-5e676de881e6"
    )
    assert EMPTY_OVERRIDE_SET_UUID == "521a6242-e6bc-5e76-9564-323c4c0deacb"


def test_an_option_target_differs_from_the_option_qualified_fact_target() -> None:
    """Same record, component, and option — different grain, different identity."""
    qualified_fact = MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key=SPELL_KEY,
        component_key=CHOICE_KEY,
        fact_key=ADDED_KEY,
        option_key=CRAWL_OPTION,
    )
    assert target_payload(CRAWL_TARGET) != target_payload(qualified_fact)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

_BINDING = ReleaseBinding(
    package_uuid=str(_SCOPE_UUID),
    release_version="5.2.1-option-target.fixture",
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


def _candidate() -> ProjectionCandidate:
    """One choice component whose options share a fact key, plus a plain one."""
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DIRECT_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(SHARED_FACT,),
            ),
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=CHOICE_KEY,
                handling=ComponentHandling.STRUCTURED,
                options=(
                    ComponentOption(
                        semantic_key=CRAWL_OPTION, facts=(CRAWL_FACT, SHARED_FACT)
                    ),
                    ComponentOption(
                        semantic_key=STAND_OPTION, facts=(STAND_FACT, SHARED_FACT)
                    ),
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


def _resolved(*entries: EffectiveOverrideEntry):  # type: ignore[no-untyped-def]
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
    return apply_override_set(_candidate(), state, _PACKAGE_BINDING)


def _options(view):  # type: ignore[no-untyped-def]
    (record,) = view.records
    choice = next(c for c in record.components if c.semantic_key == CHOICE_KEY)
    return {o.semantic_key: [f.fact_key for f in o.facts] for o in choice.options}


@pytest.mark.parametrize("option", [CRAWL_OPTION, STAND_OPTION])
def test_a_fact_appends_into_the_named_option(option: str) -> None:
    view = _resolved(_entry(option_target(option)))
    scopes = _options(view)
    assert ADDED_KEY in scopes[option]
    other = STAND_OPTION if option == CRAWL_OPTION else CRAWL_OPTION
    assert ADDED_KEY not in scopes[other]


def test_the_appended_fact_names_its_override_not_a_5c_span() -> None:
    (record,) = _resolved(_entry(CRAWL_TARGET)).records
    choice = next(c for c in record.components if c.semantic_key == CHOICE_KEY)
    crawl = next(o for o in choice.options if o.semantic_key == CRAWL_OPTION)
    (added,) = [f for f in crawl.facts if f.fact_key == ADDED_KEY]
    assert added.supplied_by_override_id == "ov-1"
    assert added.option_key == CRAWL_OPTION
    assert added.span_ids == ()


def test_appending_into_both_options_keeps_them_separate() -> None:
    scopes = _options(
        _resolved(
            _entry(CRAWL_TARGET, override_id="ov-crawl"),
            _entry(STAND_TARGET, override_id="ov-stand"),
        )
    )
    assert ADDED_KEY in scopes[CRAWL_OPTION]
    assert ADDED_KEY in scopes[STAND_OPTION]
    # And neither lost what it already stated.
    assert fact_key(CRAWL_FACT) in scopes[CRAWL_OPTION]
    assert fact_key(STAND_FACT) in scopes[STAND_OPTION]


def test_duplicate_detection_is_scoped_to_the_named_option() -> None:
    """Both options already state ``SHARED_FACT``, so both appends must fail —
    each on its own scope, not because the other option holds it."""
    for option in (CRAWL_OPTION, STAND_OPTION):
        with pytest.raises(OverrideApplicationError, match="would duplicate"):
            _resolved(
                _entry(option_target(option), payload=append_payload(SHARED_FACT))
            )


def test_a_fact_a_sibling_option_holds_still_appends() -> None:
    """The isolation case: identical fact keys must not block one another.

    ``STAND_FACT`` lives in the stand option only, so appending it to crawl is
    a genuine addition — a scope-blind duplicate check would refuse it.
    """
    scopes = _options(
        _resolved(_entry(CRAWL_TARGET, payload=append_payload(STAND_FACT)))
    )
    assert fact_key(STAND_FACT) in scopes[CRAWL_OPTION]
    assert scopes[STAND_OPTION].count(fact_key(STAND_FACT)) == 1


def test_an_option_target_naming_no_such_option_fails() -> None:
    with pytest.raises(OverrideApplicationError, match="names no option"):
        _resolved(_entry(option_target("no-such-option")))


def test_an_option_target_on_a_component_with_no_choice_fails() -> None:
    with pytest.raises(OverrideApplicationError, match="names no option"):
        _resolved(_entry(option_target(CRAWL_OPTION, component_key=DIRECT_KEY)))


def test_an_option_target_naming_no_such_component_fails() -> None:
    with pytest.raises(OverrideApplicationError, match="names no component"):
        _resolved(_entry(option_target(CRAWL_OPTION, component_key="absent")))


@pytest.mark.parametrize(
    ("kind", "scope"),
    [
        (MechanicalTargetKind.RECORD, "record"),
        (MechanicalTargetKind.COMPONENT, "component"),
    ],
)
def test_an_earlier_disable_suppresses_a_later_option_append(
    kind: MechanicalTargetKind, scope: str
) -> None:
    """Suppression is inherited downward into the choice.

    Appending into an option of a suppressed record or component would
    resurrect authority the disable removed.
    """
    disable = MechanicalTarget(
        kind=kind,
        record_key=SPELL_KEY,
        component_key=None if kind is MechanicalTargetKind.RECORD else CHOICE_KEY,
    )
    view = _resolved(
        _entry(
            disable,
            override_id="ov-disable",
            operation=OverrideOperationEnum.DISABLE,
            payload=DISABLE_PAYLOAD,
        ),
        _entry(CRAWL_TARGET, override_id="ov-append"),
    )
    append = next(o for o in view.applied_overrides if o.override_id == "ov-append")
    assert append.applied is False
    assert f"suppressed by an earlier {scope} disable" in append.note


def test_a_prose_bound_component_still_refuses_an_option_append() -> None:
    """The handling guard is not bypassed by the new grain."""
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=CHOICE_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
                options=(
                    ComponentOption(semantic_key=CRAWL_OPTION, facts=(CRAWL_FACT,)),
                    ComponentOption(semantic_key=STAND_OPTION, facts=(STAND_FACT,)),
                ),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    candidate = ProjectionCandidate(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=_BINDING,
        classification=_CLASSIFICATION,
        representation=draft,
    )
    state = EffectiveOverrideSet(
        package_uuid=_BINDING.package_uuid,
        release_version=_BINDING.release_version,
        entries=(_entry(CRAWL_TARGET),),
    )
    with pytest.raises(OverrideApplicationError, match="prose-bound"):
        apply_override_set(candidate, state, _PACKAGE_BINDING)


# ---------------------------------------------------------------------------
# Persistence and retained replay
# ---------------------------------------------------------------------------


def test_an_option_target_round_trips_the_authoring_row(
    runtime: RuntimeFixture,
) -> None:
    """No new column: the existing ``target_option_key`` carries it."""
    author_override(
        runtime.session,
        override_id="ov-option",
        target=CRAWL_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_payload(),
    )
    (row,) = runtime.session.execute(select(MechanicalOverrideORM)).scalars().all()
    assert (row.target_kind, row.target_option_key, row.target_fact_key) == (
        "option",
        CRAWL_OPTION,
        None,
    )

    (entry,) = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    ).entries
    assert entry.target.kind is MechanicalTargetKind.OPTION
    assert entry.target.option_key == CRAWL_OPTION
    assert entry.target.fact_key is None


def test_retained_replay_survives_editing_and_deleting_the_authoring_row(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-option",
        target=CRAWL_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_payload(),
    )
    state = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    identity = retain_override_set(runtime.session, state, now=NOW)

    (retained,) = runtime.session.execute(select(OverrideSetEntryORM)).scalars().all()
    assert (retained.target_kind, retained.target_option_key) == (
        "option",
        CRAWL_OPTION,
    )

    row = runtime.session.get(MechanicalOverrideORM, "ov-option")
    assert row is not None
    row.target_option_key = STAND_OPTION
    runtime.session.flush()
    runtime.session.delete(row)
    runtime.session.flush()

    replayed = load_override_set_version(
        runtime.session,
        identity,
        package_uuid=str(runtime.package_uuid),
        release_version=runtime.release_version,
    )
    (entry,) = replayed.entries
    assert entry.target.kind is MechanicalTargetKind.OPTION
    assert entry.target.option_key == CRAWL_OPTION
    assert replayed.override_set_uuid == identity


def test_a_stored_option_row_carrying_a_fact_key_fails_closed(
    runtime: RuntimeFixture,
) -> None:
    """The shape rule is enforced on the way back in, not only on the way out."""
    from afterworlds.services.rules_authority.override_set import OverrideStateError

    author_override(
        runtime.session,
        override_id="ov-option",
        target=CRAWL_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_payload(),
    )
    row = runtime.session.get(MechanicalOverrideORM, "ov-option")
    assert row is not None
    row.target_fact_key = ADDED_KEY
    runtime.session.flush()

    with pytest.raises(OverrideStateError, match="must not carry a fact_key"):
        collect_current_override_state(
            runtime.session, str(runtime.package_uuid), runtime.release_version
        )


# ---------------------------------------------------------------------------
# The published views
# ---------------------------------------------------------------------------
#
# `views.py` does not branch on target kind — but that only proves no code path
# inspects the new grain, not that a fact arriving in an option via override
# renders correctly. These drive the append all the way to published output.


def test_the_gamemaster_view_publishes_the_appended_fact_inside_its_option() -> None:
    """Never as a simultaneous direct fact.

    Flattening an option into ``structured_context`` would publish "you may
    crawl **and** you may swim" as jointly applicable, which is exactly the
    mutual exclusivity the option boundary exists to preserve.
    """
    view = build_gamemaster_view(_resolved(_entry(CRAWL_TARGET)), {})
    choice = next(c for c in view.components if c.component_key == CHOICE_KEY)

    # The appended fact is in its own option and nowhere else.
    assert [f.fact_key for f in choice.structured_context] == []
    scopes = {o.semantic_key: [f.fact_key for f in o.facts] for o in choice.options}
    assert ADDED_KEY in scopes[CRAWL_OPTION]
    assert ADDED_KEY not in scopes[STAND_OPTION]

    # And it has not leaked onto the sibling component's direct facts.
    direct = next(c for c in view.components if c.component_key == DIRECT_KEY)
    assert ADDED_KEY not in [f.fact_key for f in direct.structured_context]


def test_the_typed_view_carries_the_appended_option_fact() -> None:
    view = build_typed_view(_resolved(_entry(STAND_TARGET)))
    (record,) = view.records
    choice = next(c for c in record.components if c.semantic_key == CHOICE_KEY)
    stand = next(o for o in choice.options if o.semantic_key == STAND_OPTION)
    assert ADDED_KEY in [f.fact_key for f in stand.facts]
    assert view.applied_overrides[0].target.kind is MechanicalTargetKind.OPTION
