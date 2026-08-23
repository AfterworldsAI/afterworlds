"""Option scope survives every identity-bearing and persistence seam — PR #155.

Codex review round 3, first of two merge-blocking families. ``option_key`` was
added to :class:`MechanicalTarget` in memory only: the canonical payload omitted
it, neither override table could store it, both loaders reconstructed ``None``,
and retention never copied it. An override authored against an option fact
therefore either could not be stored at all or came back retargeted at the
component's direct-fact scope, and two in-memory targets differing only by
option shared one override-set identity.

The compatibility constraint is as load-bearing as the fix. Emitting
``"option_key": None`` on every target would have carried the scope correctly
*and* reminted the identity of every override set already authored against a
direct fact — the same authority under a new identifier, no longer naming the
retained version it was recorded against. The canonical payload of a direct
target is therefore pinned here against literals captured before the change.
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
from afterworlds.services.rules_authority.application import apply_override_set
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    OverrideStateError,
    override_set_identity,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
    target_payload,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_FACT_TARGET,
    DISABLE_PAYLOAD,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
)

# ---------------------------------------------------------------------------
# Targets under test
# ---------------------------------------------------------------------------

_SCOPE_UUID = uuid5(UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40"), "option-scope-proof")

CHOICE_KEY = "movement-choice"
CRAWL_OPTION = "crawl"
STAND_OPTION = "stand"
CRAWL_FACT = MovementPermissionFact(mode=MovementMode.CRAWL)
STAND_FACT = MovementCostFact(
    kind=MovementCostKind.EXPENDITURE,
    amount=MovementAmount.HALF_SPEED,
    payer=ParticipantRole.SUBJECT,
    rounding=RoundingRule.DOWN,
)
CRAWL_FACT_KEY = fact_key(CRAWL_FACT)
STAND_FACT_KEY = fact_key(STAND_FACT)

#: The same fact key in two options, and once directly on a component. These
#: three are the whole point: nothing downstream may conflate them.
SHARED_FACT = MovementPermissionFact(mode=MovementMode.CRAWL)
SHARED_FACT_KEY = fact_key(SHARED_FACT)


def _fact_target(option_key: str | None) -> MechanicalTarget:
    return MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key=SPELL_KEY,
        component_key=CHOICE_KEY,
        fact_key=SHARED_FACT_KEY,
        option_key=option_key,
    )


DIRECT_TARGET = _fact_target(None)
CRAWL_TARGET = _fact_target(CRAWL_OPTION)
STAND_TARGET = _fact_target(STAND_OPTION)


def _entry(
    target: MechanicalTarget, override_id: str = "ov-1"
) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=override_id,
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=target,
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=DISABLE_PAYLOAD,
    )


# ---------------------------------------------------------------------------
# 1. Identity: option-qualified targets differ; legacy direct targets do not
# ---------------------------------------------------------------------------


def test_a_direct_fact_target_keeps_the_canonical_payload_it_always_had() -> None:
    """Pinned against literals captured on the reviewed head before the change.

    This is the whole compatibility claim, and it is unfalsifiable if both
    sides are computed by post-change code — so the expected value is written
    out rather than derived.
    """
    assert target_payload(DESCRIPTOR_FACT_TARGET) == {
        "kind": "fact",
        "record_key": DESCRIPTOR_FACT_TARGET.record_key,
        "component_key": DESCRIPTOR_FACT_TARGET.component_key,
        "fact_key": DESCRIPTOR_FACT_TARGET.fact_key,
    }
    assert "option_key" not in target_payload(DESCRIPTOR_FACT_TARGET)


def test_legacy_direct_target_identities_are_not_reminted() -> None:
    """Captured at ``f6d2813`` before ``option_key`` reached the payload."""
    legacy = MechanicalTarget(
        kind=MechanicalTargetKind.FACT,
        record_key="rec",
        component_key="comp",
        fact_key="f1",
    )
    assert override_set_identity((_entry(legacy),)) == (
        "8404b420-e92e-5c5a-968d-5e676de881e6"
    )
    assert EMPTY_OVERRIDE_SET_UUID == "521a6242-e6bc-5e76-9564-323c4c0deacb"


def test_the_same_fact_in_two_options_has_three_distinct_identities() -> None:
    """Direct, crawl-scoped, and stand-scoped are three authorities, not one."""
    identities = {
        override_set_identity((_entry(t),))
        for t in (DIRECT_TARGET, CRAWL_TARGET, STAND_TARGET)
    }
    assert len(identities) == 3


def test_only_an_option_qualified_target_carries_the_fifth_key() -> None:
    assert target_payload(CRAWL_TARGET)["option_key"] == CRAWL_OPTION
    assert target_payload(STAND_TARGET)["option_key"] == STAND_OPTION
    assert "option_key" not in target_payload(DIRECT_TARGET)


# ---------------------------------------------------------------------------
# 2. Storage and replay round-trip the scope exactly
# ---------------------------------------------------------------------------


def test_a_mutable_authoring_row_round_trips_the_option_scope(
    runtime: RuntimeFixture,
) -> None:
    for override_id, target in (
        ("ov-direct", DIRECT_TARGET),
        ("ov-crawl", CRAWL_TARGET),
        ("ov-stand", STAND_TARGET),
    ):
        author_override(
            runtime.session,
            override_id=override_id,
            target=target,
            operation=OverrideOperationEnum.DISABLE,
            payload=DISABLE_PAYLOAD,
        )

    stored = {
        row.override_id: row.target_option_key
        for row in runtime.session.execute(select(MechanicalOverrideORM))
        .scalars()
        .all()
    }
    assert stored == {
        "ov-direct": None,
        "ov-crawl": CRAWL_OPTION,
        "ov-stand": STAND_OPTION,
    }

    state = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    reloaded = {e.override_id: e.target.option_key for e in state.entries}
    assert reloaded == {
        "ov-direct": None,
        "ov-crawl": CRAWL_OPTION,
        "ov-stand": STAND_OPTION,
    }


def test_retained_replay_survives_editing_and_deleting_the_current_row(
    runtime: RuntimeFixture,
) -> None:
    """The retained version is evidence, not a view of today's authoring rows.

    Retention is verified after the mutable row it was collected from has been
    retargeted to another option and then deleted outright — which is exactly
    the case ADR-005d's retention exists for, and the case a loader
    reconstructing ``option_key=None`` would answer with the wrong scope.
    """
    author_override(
        runtime.session,
        override_id="ov-crawl",
        target=CRAWL_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    state = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    identity = retain_override_set(runtime.session, state, now=NOW)

    (entry_row,) = runtime.session.execute(select(OverrideSetEntryORM)).scalars().all()
    assert entry_row.target_option_key == CRAWL_OPTION

    # Retarget, then delete. Neither may reach the retained evidence.
    row = runtime.session.get(MechanicalOverrideORM, "ov-crawl")
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
    assert [e.target.option_key for e in replayed.entries] == [CRAWL_OPTION]
    # And it still derives the identity it is stored under, which is what
    # proves the scope participated in that identity rather than riding along.
    assert replayed.override_set_uuid == identity


def test_two_options_retain_as_two_versions_not_one(
    runtime: RuntimeFixture,
) -> None:
    crawl = EffectiveOverrideSet(
        package_uuid=str(runtime.package_uuid),
        release_version=runtime.release_version,
        entries=(_entry(CRAWL_TARGET),),
    )
    stand = EffectiveOverrideSet(
        package_uuid=str(runtime.package_uuid),
        release_version=runtime.release_version,
        entries=(_entry(STAND_TARGET),),
    )
    assert retain_override_set(runtime.session, crawl, now=NOW) != retain_override_set(
        runtime.session, stand, now=NOW
    )


def test_a_stored_option_scope_on_a_non_fact_target_fails_closed(
    runtime: RuntimeFixture,
) -> None:
    """A record target has no option axis; a stored value for one is unreadable.

    Refused rather than ignored, for the reason the module docstring gives: a
    skipped row would make the override-set identity depend on which rows
    happened to parse.
    """
    author_override(
        runtime.session,
        override_id="ov-record",
        target=MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    row = runtime.session.get(MechanicalOverrideORM, "ov-record")
    assert row is not None
    row.target_option_key = CRAWL_OPTION
    runtime.session.flush()

    with pytest.raises(OverrideStateError, match="option_key"):
        collect_current_override_state(
            runtime.session, str(runtime.package_uuid), runtime.release_version
        )


# ---------------------------------------------------------------------------
# 3. An option-fact DISABLE removes only the scoped fact
# ---------------------------------------------------------------------------
#
# Built as a standalone candidate rather than by growing the shared runtime
# fixture: that fixture's element counts are asserted across the suite, and this
# proof is about the application seam, not about the persisted projection.


#: A standalone scope for the application-seam proofs. Content-free on purpose:
#: nothing below reads it, and identifying a real release would imply this proof
#: depends on one.
_BINDING = ReleaseBinding(
    package_uuid=str(_SCOPE_UUID),
    release_version="5.2.1-option-scope.fixture",
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


def _choice_candidate() -> ProjectionCandidate:
    """One record, one direct-fact component, one exhaustive-choice component.

    ``SHARED_FACT`` appears in both options *and* directly on the sibling
    component, so a scope-blind disable would be visible as collateral damage
    rather than having to be inferred.
    """
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key="direct",
                handling=ComponentHandling.STRUCTURED,
                facts=(SHARED_FACT,),
            ),
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=CHOICE_KEY,
                handling=ComponentHandling.STRUCTURED,
                options=(
                    ComponentOption(
                        semantic_key=CRAWL_OPTION, facts=(SHARED_FACT, STAND_FACT)
                    ),
                    ComponentOption(semantic_key=STAND_OPTION, facts=(SHARED_FACT,)),
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


def _resolved(target: MechanicalTarget):  # type: ignore[no-untyped-def]
    state = EffectiveOverrideSet(
        package_uuid=_BINDING.package_uuid,
        release_version=_BINDING.release_version,
        entries=(_entry(target),),
    )
    return apply_override_set(_choice_candidate(), state, _PACKAGE_BINDING)


def _choice(view):  # type: ignore[no-untyped-def]
    (record,) = view.records
    return next(c for c in record.components if c.semantic_key == CHOICE_KEY)


def _direct(view):  # type: ignore[no-untyped-def]
    (record,) = view.records
    return next(c for c in record.components if c.semantic_key == "direct")


def _keys(option) -> list[str]:  # type: ignore[no-untyped-def]
    return [f.fact_key for f in option.facts]


def test_disabling_one_option_fact_leaves_its_siblings_alone() -> None:
    view = _resolved(CRAWL_TARGET)
    crawl, stand = _choice(view).options
    assert crawl.semantic_key == CRAWL_OPTION and stand.semantic_key == STAND_OPTION
    # Removed from crawl only.
    assert SHARED_FACT_KEY not in _keys(crawl)
    # The other fact of the *same* option survives — this is a fact disable,
    # not an option disable.
    assert STAND_FACT_KEY in _keys(crawl)
    # The sibling option's identical fact survives.
    assert _keys(stand) == [SHARED_FACT_KEY]
    # And so does the same fact held directly on another component.
    assert [f.fact_key for f in _direct(view).facts] == [SHARED_FACT_KEY]


def test_the_filtered_options_reach_the_assembled_view() -> None:
    """``_finalize_component`` computed them and then dropped them.

    Without this the disable was recorded, the handling derivation accounted
    for it, and the fact was still published.
    """
    crawl, _ = _choice(_resolved(CRAWL_TARGET)).options
    assert SHARED_FACT_KEY not in _keys(crawl)


def test_a_direct_scoped_disable_does_not_reach_inside_the_choice() -> None:
    """The inverse direction of the same boundary."""
    view = _resolved(
        MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key="direct",
            fact_key=SHARED_FACT_KEY,
        )
    )
    assert _direct(view).facts == ()
    crawl, stand = _choice(view).options
    assert SHARED_FACT_KEY in _keys(crawl)
    assert SHARED_FACT_KEY in _keys(stand)


def test_an_option_fact_disable_is_accepted_at_all() -> None:
    """A choice component has no direct facts, so a scope-blind existence
    check rejected every valid option-fact disable as ``INVALID_OVERRIDE``."""
    (applied,) = _resolved(CRAWL_TARGET).applied_overrides
    assert applied.applied is True
    assert applied.note == "fact suppressed"


def test_a_disable_naming_a_fact_absent_from_that_option_still_fails() -> None:
    """Scoping the lookup must not weaken it into accepting anything."""
    from afterworlds.services.rules_authority.application import (
        OverrideApplicationError,
    )

    with pytest.raises(OverrideApplicationError):
        _resolved(
            MechanicalTarget(
                kind=MechanicalTargetKind.FACT,
                record_key=SPELL_KEY,
                component_key=CHOICE_KEY,
                fact_key=STAND_FACT_KEY,
                option_key=STAND_OPTION,
            )
        )
