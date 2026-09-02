"""The authored-authority prose overlay — Owner Decision 2026-08-08.

ADR-005d Decisions 3, 6, 9, and 10 (amended) and #137 contracts 3 and 6
(amended) narrow the blanket prohibition on a second prose store to the
invariant that there is no duplicated store for what the SRD source says. A
distinct authored-authority prose overlay is a first-class runtime authority
layer: it targets a dedicated ``PROSE`` grain scoped by stable record and
component identity, never a raw chunk, and it never claims 5c chunk identity,
span provenance, or an irreducibility reason copied from base authority.

This module proves the effective behavior contract 6 defines: ``REPLACE``
replaces effective governing prose, ``APPEND`` preserves it and adds one more
passage in deterministic order, ``DISABLE`` suppresses it without deleting
base state, prose operations never touch typed facts, and the whole overlay
participates in override-set identity and replay exactly like every other
typed override.

**Effective-content classification (Owner Decision 2026-08-09).**
``EffectiveComponent.handling`` describes the authority surviving after
ordered override application, never authority that existed earlier in the
sequence — a promotion to ``MIXED`` is not sticky. This module's
STRUCTURED/MIXED-transition tests are the ones that pin that: they assert
handling *reverts* when prose is suppressed and facts survive, which a
sticky-promotion implementation gets wrong.
"""

from __future__ import annotations

import re
from pathlib import Path

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    DcKind,
    RollContext,
    fact_key,
    fact_payload,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM
from afterworlds.persistence.orm.rules_package import RuleOverrideORM
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    MechanicalTarget,
    MechanicalTargetKind,
    RulesAuthorityService,
    collect_current_override_state,
)
from afterworlds.services.rules_authority.application import AuthoredProse, SourceProse
from tests.services.rules_authority.conftest import (
    CHECK_FACT_KEY,
    CREATURE_KEY,
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_KEY,
    DISABLE_PAYLOAD,
    MIXED_KEY,
    MIXED_PROSE_TARGET,
    NOW,
    OPEN_ENDED_KEY,
    PACKAGE_UUID,
    PROSE_TEXT,
    RELEASE_VERSION,
    SPELL_KEY,
    WISH_CHUNK,
    RuntimeFixture,
    append_fact_payload,
    author_override,
)

#: The prose-bound component's prose authority: source-only until an override
#: replaces, appends to, or disables it.
PROSE_BOUND_PROSE_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.PROSE, record_key=SPELL_KEY, component_key=OPEN_ENDED_KEY
)
#: A purely structured component's (previously prose-free) prose authority —
#: attaching prose here is the STRUCTURED -> MIXED promotion case.
STRUCTURED_PROSE_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.PROSE, record_key=SPELL_KEY, component_key=DESCRIPTOR_KEY
)


def replace_prose_payload(text: str = "authored replacement text") -> dict[str, object]:
    return {"patch": "replace_prose", "text": text}


def append_prose_payload(text: str = "authored addendum text") -> dict[str, object]:
    return {"patch": "append_prose", "text": text}


def service(runtime: RuntimeFixture) -> RulesAuthorityService:
    return RulesAuthorityService(runtime.session, now=NOW)


def whole(runtime: RuntimeFixture) -> RuleSliceRequest:
    return RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)


def identity(runtime: RuntimeFixture) -> str:
    return collect_current_override_state(
        runtime.session, PACKAGE_UUID, RELEASE_VERSION
    ).override_set_uuid


def typed_component(runtime: RuntimeFixture, record_key: str, component_key: str):  # type: ignore[no-untyped-def]
    result = service(runtime).typed_view(whole(runtime))
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    view = result.typed_view
    assert view is not None
    (record,) = [r for r in view.records if r.semantic_key == record_key]
    (component,) = [c for c in record.components if c.semantic_key == component_key]
    return component


def refusal(runtime: RuntimeFixture):  # type: ignore[no-untyped-def]
    return service(runtime).typed_view(whole(runtime))


def gm_component(runtime: RuntimeFixture, component_key: str):  # type: ignore[no-untyped-def]
    result = service(runtime).gamemaster_view(whole(runtime))
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    view = result.gamemaster_view
    assert view is not None
    (component,) = [c for c in view.components if c.component_key == component_key]
    return component


# ---------------------------------------------------------------------------
# Override-set identity
# ---------------------------------------------------------------------------


def test_authored_text_change_moves_the_override_set_identity(
    runtime: RuntimeFixture,
) -> None:
    """#137 acceptance criterion 25: changing authored text moves the identity."""
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("first authored text"),
    )
    before = identity(runtime)

    row = runtime.session.get(MechanicalOverrideORM, "ov-prose")
    assert row is not None
    row.payload = replace_prose_payload("a different authored text")
    runtime.session.flush()

    assert identity(runtime) != before


def test_two_replace_component_patches_differing_only_in_prose_are_distinct(
    runtime: RuntimeFixture,
) -> None:
    """Regression: ``_component_body_payload`` must not drop authored_prose.

    Two whole-component REPLACE patches identical except for authored text
    must not canonicalize to the same bytes and share an identity.
    """
    author_override(
        runtime.session,
        override_id="ov-component-prose",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=OPEN_ENDED_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "text one",
            },
        },
    )
    first = identity(runtime)

    row = runtime.session.get(MechanicalOverrideORM, "ov-component-prose")
    assert row is not None
    row.payload = {
        "patch": "replace_component",
        "component": {
            "handling": "prose_bound",
            "facts": [],
            "authored_prose": "text two",
        },
    }
    runtime.session.flush()

    assert identity(runtime) != first


def test_prose_target_change_moves_the_override_set_identity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload(),
    )
    before = identity(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-prose")
    assert row is not None
    row.target_component_key = DESCRIPTOR_KEY
    runtime.session.flush()
    assert identity(runtime) != before


def test_prose_origin_change_moves_the_override_set_identity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload(),
        origin=OverrideOriginEnum.HOUSE_RULE,
    )
    before = identity(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-prose")
    assert row is not None
    row.override_origin = OverrideOriginEnum.PACKAGE_PATCH.value
    runtime.session.flush()
    assert identity(runtime) != before


def test_prose_operation_change_moves_the_override_set_identity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("same text"),
    )
    before = identity(runtime)
    row = runtime.session.get(MechanicalOverrideORM, "ov-prose")
    assert row is not None
    row.override_operation = OverrideOperationEnum.REPLACE.value
    row.payload = replace_prose_payload("same text")
    runtime.session.flush()
    assert identity(runtime) != before


def test_reordering_two_prose_overrides_moves_the_identity(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-a",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("first"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-b",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("second"),
        precedence=20,
    )
    before = identity(runtime)
    first = runtime.session.get(MechanicalOverrideORM, "ov-a")
    second = runtime.session.get(MechanicalOverrideORM, "ov-b")
    assert first is not None and second is not None
    first.precedence, second.precedence = 20, 10
    runtime.session.flush()
    assert identity(runtime) != before


def test_base_projection_identity_is_unaffected_by_authored_prose(
    runtime: RuntimeFixture,
) -> None:
    before = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert before.binding is not None
    author_override(
        runtime.session,
        override_id="ov-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload(),
    )
    after = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert after.binding is not None
    assert (
        after.binding.mechanical_projection_uuid
        == before.binding.mechanical_projection_uuid
    )
    assert after.binding.override_set_uuid != before.binding.override_set_uuid


# ---------------------------------------------------------------------------
# REPLACE / APPEND / DISABLE over PROSE_BOUND
# ---------------------------------------------------------------------------


def test_replace_prose_on_prose_bound_replaces_source_prose(
    runtime: RuntimeFixture,
) -> None:
    """PROSE REPLACE removes all source prose *and* the source-derived
    irreducibility reason it justified: what remains is authored-only
    authority, and a reason claiming the discarded source prose's
    irreducibility no longer honestly describes it (ADR-005d Decision 10).
    Checked in both views — they must agree, the same way they agree on
    governing prose itself.
    """
    author_override(
        runtime.session,
        override_id="ov-replace",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("the authored replacement"),
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.handling is ComponentHandling.PROSE_BOUND
    assert component.facts == ()
    assert component.irreducibility_reason_code is None
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the authored replacement"
    assert entry.supplied_by_override_id == "ov-replace"
    assert entry.supplied_by_origin is OverrideOriginEnum.HOUSE_RULE

    gm = gm_component(runtime, OPEN_ENDED_KEY)
    assert gm.irreducibility_reason_code is None


def test_append_prose_on_prose_bound_preserves_source_and_adds_authored(
    runtime: RuntimeFixture,
) -> None:
    """APPEND only adds to existing governing prose — the source prose (and
    the reason that justifies it) remains effective, unlike REPLACE.
    """
    author_override(
        runtime.session,
        override_id="ov-append",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("an authored addendum"),
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.handling is ComponentHandling.PROSE_BOUND
    assert component.irreducibility_reason_code == "open_ended_effect"
    source, authored = component.governing_prose
    assert isinstance(source, SourceProse)
    assert source.chunk_id == WISH_CHUNK
    assert isinstance(authored, AuthoredProse)
    assert authored.text == "an authored addendum"
    assert authored.supplied_by_override_id == "ov-append"

    gm = gm_component(runtime, OPEN_ENDED_KEY)
    assert gm.irreducibility_reason_code == "open_ended_effect"


def test_replace_prose_on_a_base_mixed_component_clears_only_the_reason(
    runtime: RuntimeFixture,
) -> None:
    """A base ``MIXED`` component (facts and source prose both declared at
    build time) keeps its facts and its effective ``MIXED`` handling when its
    source prose is replaced by authored-only prose — only the now-obsolete
    source-derived reason is cleared, nothing else.
    """
    before = typed_component(runtime, CREATURE_KEY, MIXED_KEY)
    assert before.handling is ComponentHandling.MIXED
    assert before.irreducibility_reason_code == "open_ended_effect"
    assert [f.fact_key for f in before.facts] == [CHECK_FACT_KEY]
    (before_source,) = before.governing_prose
    assert isinstance(before_source, SourceProse)

    author_override(
        runtime.session,
        override_id="ov-replace-mixed-prose",
        target=MIXED_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("the authored replacement for the mixed clause"),
    )
    component = typed_component(runtime, CREATURE_KEY, MIXED_KEY)
    assert component.handling is ComponentHandling.MIXED
    assert [f.fact_key for f in component.facts] == [CHECK_FACT_KEY]
    assert component.irreducibility_reason_code is None
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the authored replacement for the mixed clause"

    gm = gm_component(runtime, MIXED_KEY)
    assert gm.irreducibility_reason_code is None


def test_replace_then_disable_leaves_the_reason_cleared(
    runtime: RuntimeFixture,
) -> None:
    """``REPLACE`` -> ``DISABLE`` (ascending precedence 10, 20) on a
    ``PROSE_BOUND`` component (no facts, so nothing here rides on the
    settled handling-driven demotion): ``REPLACE`` applies and clears the
    reason; the later ``DISABLE`` only empties ``governing_prose`` further
    and leaves the already-cleared reason alone. Final reason: ``None``.
    Paired with the suppressed-``REPLACE`` case below to pin that clearing
    depends on whether ``REPLACE`` itself applies, not on a value read
    mid-resolution.
    """
    author_override(
        runtime.session,
        override_id="ov-replace-then-disable",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("replaced before the disable"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-after-replace",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.governing_prose == ()
    assert component.irreducibility_reason_code is None


def test_disable_then_suppressed_replace_leaves_the_reason_untouched(
    runtime: RuntimeFixture,
) -> None:
    """``DISABLE`` -> ``REPLACE`` (10, 20) on the *same* ``PROSE_BOUND``
    target: ``DISABLE`` applies first and suppresses the target; the
    unchanged precedence rule then refuses the later ``REPLACE`` on that same
    target (``_suppressed_by``), so it never applies and never clears
    anything. Final reason: the base ``"open_ended_effect"``, unchanged —
    the already-settled ``PROSE_BOUND``-with-suppressed-prose exception, not
    a new effect of this remediation. The suppressed entry's own ``applied``
    flag is asserted so the reason for the divergence from the sibling test
    above is visible here, not just inferred.
    """
    author_override(
        runtime.session,
        override_id="ov-disable-then-replace-disable",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-then-replace-replace",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("should never apply"),
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.governing_prose == ()
    assert component.irreducibility_reason_code == "open_ended_effect"
    result = service(runtime).typed_view(whole(runtime))
    assert result.typed_view is not None
    applied = {a.override_id: a for a in result.typed_view.applied_overrides}
    assert applied["ov-disable-then-replace-disable"].applied is True
    assert applied["ov-disable-then-replace-replace"].applied is False


def test_replay_reconstructs_the_cleared_reason_after_current_rows_change(
    runtime: RuntimeFixture,
) -> None:
    """The recorded binding names an override-set version whose cleared
    reason must reconstruct exactly, even after the current override row that
    produced it is edited or deleted — the same replay guarantee every other
    applied change gets.
    """
    author_override(
        runtime.session,
        override_id="ov-replace-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("the first authored replacement"),
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    recorded = resolution.binding
    assert recorded is not None
    original = service(runtime).replay(recorded)
    (original_record,) = [r for r in original.records if r.semantic_key == SPELL_KEY]
    (original_component,) = [
        c for c in original_record.components if c.semantic_key == OPEN_ENDED_KEY
    ]
    assert original_component.irreducibility_reason_code is None
    assert original_component.handling is ComponentHandling.PROSE_BOUND

    row = runtime.session.get(MechanicalOverrideORM, "ov-replace-prose")
    assert row is not None
    row.is_enabled = False
    runtime.session.flush()

    # Current state, unlike the replayed one, resolves back to the base
    # source prose and its reason once REPLACE is disabled — the point is
    # that replay ignores this and reconstructs the original cleared reason.
    current_after_edit = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert current_after_edit.irreducibility_reason_code == "open_ended_effect"

    runtime.session.delete(row)
    runtime.session.flush()

    current_after_delete = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert current_after_delete.irreducibility_reason_code == "open_ended_effect"

    replayed = service(runtime).replay(recorded)
    (record,) = [r for r in replayed.records if r.semantic_key == SPELL_KEY]
    (component,) = [c for c in record.components if c.semantic_key == OPEN_ENDED_KEY]
    assert component.irreducibility_reason_code is None
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the first authored replacement"


def test_disable_prose_suppresses_it_without_deleting_the_component(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.governing_prose == ()
    # No facts survive either, so PROSE_BOUND is still the only honest
    # category (Owner Decision 2026-08-09's named exception) — not because
    # suppression is exempt from recomputing handling, but because recomputing
    # it here lands on the same value: no facts, no prose.
    assert component.handling is ComponentHandling.PROSE_BOUND
    assert component.facts == ()


def test_disabling_prose_does_not_suppress_the_components_facts(
    runtime: RuntimeFixture,
) -> None:
    """Prose and facts are siblings: disabling one leaves the other alone.

    Exercised on a component that actually holds both: an earlier APPEND
    promotes DESCRIPTOR_KEY to effective MIXED, then a later DISABLE removes
    only the prose. The facts must survive untouched regardless of what the
    disable does to handling (covered separately below).
    """
    author_override(
        runtime.session,
        override_id="ov-append-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.governing_prose == ()
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]


def test_append_then_disable_prose_returns_a_promoted_component_to_structured(
    runtime: RuntimeFixture,
) -> None:
    """Owner Decision 2026-08-09: effective-content classification, not sticky.

    ``handling`` describes the authority surviving after ordered override
    application, never authority that existed earlier in the sequence. An
    earlier promotion to MIXED is not remembered once its only prose is gone:
    facts survive, prose does not, so the component reads STRUCTURED again —
    exactly what a sticky "once MIXED, always MIXED" implementation gets
    wrong.
    """
    author_override(
        runtime.session,
        override_id="ov-append-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
        precedence=10,
    )
    # Confirm the promotion actually happened before disabling it, so the
    # transition this test pins is real rather than a no-op.
    promoted = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert promoted.handling is ComponentHandling.MIXED

    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.governing_prose == ()
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.irreducibility_reason_code is None


def test_replace_then_disable_prose_returns_a_promoted_component_to_structured(
    runtime: RuntimeFixture,
) -> None:
    """The REPLACE path to promotion demotes the same way APPEND does."""
    author_override(
        runtime.session,
        override_id="ov-replace-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("an authored replacement"),
        precedence=10,
    )
    promoted = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert promoted.handling is ComponentHandling.MIXED

    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.governing_prose == ()
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.irreducibility_reason_code is None


def test_a_mixed_component_becomes_effectively_structured_when_prose_is_suppressed(
    runtime: RuntimeFixture,
) -> None:
    """A component that is MIXED going in demotes the same way a promoted one
    does: suppressing its only prose while its facts survive leaves STRUCTURED,
    never a handling that remembers the MIXED it used to be.
    """
    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-become-mixed",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "mixed",
                "facts": [fact_payload(check_fact)],
                "authored_prose": "mixed from the start",
            },
        },
        precedence=10,
    )
    mixed = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert mixed.handling is ComponentHandling.MIXED
    assert mixed.facts != ()

    author_override(
        runtime.session,
        override_id="ov-suppress-its-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.governing_prose == ()
    assert component.facts != ()
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.irreducibility_reason_code is None


def test_disable_prose_stops_later_processing_of_the_same_prose_target(
    runtime: RuntimeFixture,
) -> None:
    """Unchanged precedence: a DISABLE still stops later processing of the
    *exact same target* — a later APPEND aimed at the same prose target does
    not resurrect it. #137/ADR-005d Decision 10's "first winning disable wins"
    rule, already established for record/component/fact targets, applies to
    prose exactly the same way; this remediation does not loosen it.
    """
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-append-after-disable",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("should never apply"),
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.governing_prose == ()
    assert component.handling is ComponentHandling.STRUCTURED
    result = service(runtime).typed_view(whole(runtime))
    assert result.typed_view is not None
    applied = {a.override_id: a for a in result.typed_view.applied_overrides}
    assert applied["ov-disable-prose"].applied is True
    assert applied["ov-append-after-disable"].applied is False


def test_a_whole_component_replace_after_prose_suppression_promotes_again(
    runtime: RuntimeFixture,
) -> None:
    """ "Later higher-precedence prose introduced after suppression must
    promote the effective view again" (Owner Decision 2026-08-09) — reached
    through a whole-component REPLACE, a different target kind that a prior
    PROSE-target DISABLE does not suppress. The stale suppression against the
    old component's prose target must not hold back the replacement's own
    prose.
    """
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    suppressed = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert suppressed.governing_prose == ()
    assert suppressed.handling is ComponentHandling.STRUCTURED

    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-replace-whole-component",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "mixed",
                "facts": [fact_payload(check_fact)],
                "authored_prose": "the replacement's own prose",
            },
        },
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.handling is ComponentHandling.MIXED
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the replacement's own prose"


def test_replace_component_clears_prose_suppression_so_a_later_append_applies(
    runtime: RuntimeFixture,
) -> None:
    """The most literal reading of "promote again": a whole-component REPLACE
    clears the stale PROSE-target suppression (existing ``disabled_prose``
    clearing, unchanged by this remediation), so a *subsequent* prose APPEND
    on the same target — which would have been suppressed had the REPLACE not
    intervened — now applies.
    """
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-replace-whole-component",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "structured",
                "facts": [fact_payload(check_fact)],
            },
        },
        precedence=20,
    )
    author_override(
        runtime.session,
        override_id="ov-append-after-replace",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("now applies"),
        precedence=30,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "now applies"
    result = service(runtime).typed_view(whole(runtime))
    assert result.typed_view is not None
    applied = {a.override_id: a for a in result.typed_view.applied_overrides}
    assert applied["ov-append-after-replace"].applied is True


def test_a_fact_disable_after_prose_promotion_revises_handling_to_prose_bound(
    runtime: RuntimeFixture,
) -> None:
    """A later, unrelated FACT ``DISABLE`` on the same component resolves
    *after* an earlier prose promotion in ordering. Handling must reflect what
    survives at the very end, not only what the prose operation itself saw:
    losing the last fact after a MIXED promotion leaves prose without facts,
    which Owner Decision 2026-08-09's third bullet makes ``PROSE_BOUND`` — not
    a handling that keeps claiming facts it no longer has.
    """
    from tests.services.rules_authority.conftest import DESCRIPTOR_FACT_TARGET

    author_override(
        runtime.session,
        override_id="ov-append-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
        precedence=10,
    )
    promoted = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert promoted.handling is ComponentHandling.MIXED
    before = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert before.binding is not None

    author_override(
        runtime.session,
        override_id="ov-disable-the-only-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.facts == ()
    assert component.governing_prose != ()
    assert component.handling is ComponentHandling.PROSE_BOUND

    # Re-derivation at final assembly must not lose either override's own
    # provenance, and must not touch the immutable base projection identity —
    # both overrides still resolved and applied against their real targets.
    after = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert after.binding is not None
    assert (
        after.binding.mechanical_projection_uuid
        == before.binding.mechanical_projection_uuid
    )
    result = service(runtime).typed_view(whole(runtime))
    assert result.typed_view is not None
    applied = {a.override_id: a for a in result.typed_view.applied_overrides}
    assert applied["ov-append-prose"].applied is True
    assert applied["ov-disable-the-only-fact"].applied is True


# ---------------------------------------------------------------------------
# Path-independent final-effective-handling derivation (Owner Decision
# 2026-08-09, generalized): the same facts+prose -> handling invariant holds
# regardless of which override family declared the authority, or whether a
# prose operation was ever involved at all.
# ---------------------------------------------------------------------------


def test_component_replace_declaring_mixed_then_fact_disable_finishes_prose_bound(
    runtime: RuntimeFixture,
) -> None:
    """The exact regression from the path-dependent residue: a whole-component
    ``REPLACE`` that declares ``MIXED`` directly (never processed by a prose
    entry) must still demote to ``PROSE_BOUND`` when a later ``FACT``
    ``DISABLE`` strips its only fact, with its authored prose intact.
    """
    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-declare-mixed",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "mixed",
                "facts": [fact_payload(check_fact)],
                "authored_prose": "declared mixed directly",
            },
        },
        precedence=10,
    )
    mixed = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert mixed.handling is ComponentHandling.MIXED
    before = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert before.binding is not None

    author_override(
        runtime.session,
        override_id="ov-disable-the-declared-fact",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
            fact_key=fact_key(check_fact),
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.facts == ()
    assert component.governing_prose != ()
    assert component.handling is ComponentHandling.PROSE_BOUND

    after = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert after.binding is not None
    assert (
        after.binding.mechanical_projection_uuid
        == before.binding.mechanical_projection_uuid
    )
    result = service(runtime).typed_view(whole(runtime))
    assert result.typed_view is not None
    applied = {a.override_id: a for a in result.typed_view.applied_overrides}
    assert applied["ov-declare-mixed"].applied is True
    assert applied["ov-disable-the-declared-fact"].applied is True

    replayed = service(runtime).replay(after.binding)
    (record,) = [r for r in replayed.records if r.semantic_key == SPELL_KEY]
    (replayed_component,) = [
        c for c in record.components if c.semantic_key == DESCRIPTOR_KEY
    ]
    assert replayed_component.handling is ComponentHandling.PROSE_BOUND
    assert replayed_component.facts == ()
    assert replayed_component.governing_prose != ()


def test_record_replace_declaring_mixed_then_fact_disable_finishes_prose_bound(
    runtime: RuntimeFixture,
) -> None:
    """The same invariant through a whole-record ``REPLACE`` containing an
    authored-prose ``MIXED`` component — a different override family from
    both the prose path and the whole-component-``REPLACE`` path above.
    """
    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-replace-record",
        target=MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_record",
            "record_kind": "spell",
            "components": [
                {
                    "semantic_key": DESCRIPTOR_KEY,
                    "handling": "mixed",
                    "facts": [fact_payload(check_fact)],
                    "authored_prose": "record-replaced mixed component",
                }
            ],
        },
        precedence=10,
    )
    mixed = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert mixed.handling is ComponentHandling.MIXED

    author_override(
        runtime.session,
        override_id="ov-disable-the-record-replaced-fact",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
            fact_key=fact_key(check_fact),
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.facts == ()
    assert component.governing_prose != ()
    assert component.handling is ComponentHandling.PROSE_BOUND


def test_component_append_declaring_mixed_then_fact_disable_finishes_prose_bound(
    runtime: RuntimeFixture,
) -> None:
    """The same invariant for a newly ``APPEND``-ed component declaring
    ``MIXED`` directly — a fourth distinct override family exercising the
    same final derivation.
    """
    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    new_component_key = "house-rider"
    author_override(
        runtime.session,
        override_id="ov-append-mixed-component",
        target=MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY),
        operation=OverrideOperationEnum.APPEND,
        payload={
            "patch": "append_component",
            "component": {
                "semantic_key": new_component_key,
                "handling": "mixed",
                "facts": [fact_payload(check_fact)],
                "authored_prose": "appended mixed component",
            },
        },
        precedence=10,
    )
    mixed = typed_component(runtime, SPELL_KEY, new_component_key)
    assert mixed.handling is ComponentHandling.MIXED

    author_override(
        runtime.session,
        override_id="ov-disable-the-appended-fact",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=new_component_key,
            fact_key=fact_key(check_fact),
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, new_component_key)
    assert component.facts == ()
    assert component.governing_prose != ()
    assert component.handling is ComponentHandling.PROSE_BOUND


def test_reusing_a_semantic_key_after_a_prose_operation_does_not_inherit_stale_state(
    runtime: RuntimeFixture,
) -> None:
    """A semantic key a prose operation touched, later reincarnated by a
    whole-component ``REPLACE`` that declares fresh authority with no prose,
    must reflect only its own final facts/prose — nothing carried over from
    the earlier prose operation against the same key. There is no tracking
    set this could leak from (final handling is derived from each component's
    own current fields, not from any operation-keyed record of what happened
    to that key before), but the observable behavior is what matters.
    """
    author_override(
        runtime.session,
        override_id="ov-promote-via-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
        precedence=10,
    )
    promoted = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert promoted.handling is ComponentHandling.MIXED

    check_fact = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-reincarnate-the-key",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "structured",
                "facts": [fact_payload(check_fact)],
            },
        },
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.governing_prose == ()
    assert [f.fact_key for f in component.facts] == [fact_key(check_fact)]


def test_all_empty_fallback_does_not_depend_on_fact_vs_prose_disable_order(
    runtime: RuntimeFixture,
) -> None:
    """The all-authority-empty fallback (declared handling, untouched) must
    not depend on operation order: two component REPLACE/APPEND declarations
    that both declare ``MIXED`` and both end up with facts=()/prose=() report
    the same handling whether their prose or their fact was disabled first.
    Before ``_apply_prose_entry`` stopped mutating ``handling`` mid-loop,
    reversing this order changed the answer (``STRUCTURED`` vs
    ``PROSE_BOUND``) even though the final surviving authority — nothing — was
    identical either way.
    """
    check_fact_a = AbilityCheckFact(
        ability=AbilityScore.WISDOM,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-declare-mixed-a",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "mixed",
                "facts": [fact_payload(check_fact_a)],
                "authored_prose": "will be fully suppressed, prose disabled first",
            },
        },
        precedence=0,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-prose-a",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-fact-a",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=DESCRIPTOR_KEY,
            fact_key=fact_key(check_fact_a),
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )

    check_fact_b = AbilityCheckFact(
        ability=AbilityScore.STRENGTH,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        context=RollContext.ABILITY_CHECK,
    )
    second_key = "house-rider"
    author_override(
        runtime.session,
        override_id="ov-declare-mixed-b",
        target=MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY),
        operation=OverrideOperationEnum.APPEND,
        payload={
            "patch": "append_component",
            "component": {
                "semantic_key": second_key,
                "handling": "mixed",
                "facts": [fact_payload(check_fact_b)],
                "authored_prose": "will be fully suppressed, fact disabled first",
            },
        },
        precedence=0,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-fact-b",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.FACT,
            record_key=SPELL_KEY,
            component_key=second_key,
            fact_key=fact_key(check_fact_b),
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-prose-b",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.PROSE,
            record_key=SPELL_KEY,
            component_key=second_key,
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )

    component_a = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    component_b = typed_component(runtime, SPELL_KEY, second_key)
    assert component_a.facts == ()
    assert component_a.governing_prose == ()
    assert component_b.facts == ()
    assert component_b.governing_prose == ()
    assert component_a.handling is component_b.handling is ComponentHandling.MIXED


# ---------------------------------------------------------------------------
# STRUCTURED -> effective MIXED promotion, and MIXED-safety
# ---------------------------------------------------------------------------


def test_authored_prose_on_a_structured_component_promotes_effective_handling(
    runtime: RuntimeFixture,
) -> None:
    """An honest effective view, not prose smuggled into a typed fact."""
    author_override(
        runtime.session,
        override_id="ov-promote",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.handling is ComponentHandling.MIXED
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "a house-rule clarification"


def test_promotion_to_mixed_does_not_remint_the_base_projection(
    runtime: RuntimeFixture,
) -> None:
    before = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert before.binding is not None
    author_override(
        runtime.session,
        override_id="ov-promote",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload(),
    )
    after = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert after.binding is not None
    assert (
        after.binding.mechanical_projection_uuid
        == before.binding.mechanical_projection_uuid
    )


def test_mixed_component_prose_operations_do_not_alter_typed_facts(
    runtime: RuntimeFixture,
) -> None:
    """On a MIXED component, prose ops leave the facts array untouched."""
    author_override(
        runtime.session,
        override_id="ov-promote",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("first"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-append-again",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("second"),
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert component.handling is ComponentHandling.MIXED
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]
    assert len(component.governing_prose) == 2


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def test_append_append_replace_the_later_replace_wins(
    runtime: RuntimeFixture,
) -> None:
    """A REPLACE resolved after two APPENDs wipes them, not just the source."""
    author_override(
        runtime.session,
        override_id="ov-append-1",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("first addendum"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-append-2",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("second addendum"),
        precedence=20,
    )
    author_override(
        runtime.session,
        override_id="ov-replace",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("the only surviving text"),
        precedence=30,
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the only surviving text"
    assert entry.supplied_by_override_id == "ov-replace"


def test_replace_then_append_preserves_only_the_replacement_and_the_append(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-replace",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("replacement text"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-append",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("appended after replacement"),
        precedence=20,
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert [e.text for e in component.governing_prose] == [
        "replacement text",
        "appended after replacement",
    ]


# ---------------------------------------------------------------------------
# GameMaster view: exact ordered source/authored authority and provenance
# ---------------------------------------------------------------------------


def test_the_gamemaster_view_returns_ordered_source_then_authored_prose(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-append",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("an authored addendum"),
    )
    component = gm_component(runtime, OPEN_ENDED_KEY)
    source, authored = component.governing_prose
    assert isinstance(source, SourceProse)
    assert source.chunk_id == WISH_CHUNK
    assert source.text == PROSE_TEXT
    assert isinstance(authored, AuthoredProse)
    assert authored.text == "an authored addendum"
    assert authored.supplied_by_override_id == "ov-append"
    assert authored.supplied_by_origin is OverrideOriginEnum.HOUSE_RULE


def test_typed_and_gamemaster_views_report_the_same_prose_provenance(
    runtime: RuntimeFixture,
) -> None:
    """Same entries, same order, same provenance — only source text differs.

    Uses APPEND so both a SourceProse and an AuthoredProse entry are present:
    a REPLACE here would leave only the authored entry, which passes through
    both views unresolved and would make this pass without exercising the
    typed view's "no text lookup" contract at all.
    """
    author_override(
        runtime.session,
        override_id="ov-append",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("shared authored text"),
    )
    typed = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    gm = gm_component(runtime, OPEN_ENDED_KEY)

    typed_source, typed_authored = typed.governing_prose
    gm_source, gm_authored = gm.governing_prose
    assert isinstance(typed_source, SourceProse) and isinstance(gm_source, SourceProse)
    assert typed_source.chunk_id == gm_source.chunk_id == WISH_CHUNK
    # The typed (deterministic-consumer) view never resolves source text; only
    # the GameMaster view does, by reading the bound package's RuleChunk rows.
    assert typed_source.text is None
    assert gm_source.text == PROSE_TEXT
    assert typed_authored == gm_authored
    assert isinstance(typed_authored, AuthoredProse)
    assert typed_authored.text == "shared authored text"


# ---------------------------------------------------------------------------
# Deterministic consumers are unaffected by authored prose
# ---------------------------------------------------------------------------


def test_the_fact_bearing_surface_is_identical_with_and_without_prose_overlay(
    runtime: RuntimeFixture,
) -> None:
    """Not a tautology: proves the *facts* consumers execute against, not just
    that a prose field exists, are byte-identical whether or not authored
    prose is attached — a deterministic consumer reading only ``facts`` can
    never observe the overlay at all.
    """
    without = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    author_override(
        runtime.session,
        override_id="ov-prose-only",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("purely informational to a deterministic reader"),
    )
    with_prose = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert with_prose.facts == without.facts
    assert with_prose.record_key == without.record_key
    assert with_prose.semantic_key == without.semantic_key
    # Only the honestly-promoted handling and the added prose differ.
    assert with_prose.handling != without.handling
    assert with_prose.governing_prose != without.governing_prose


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_replay_reconstructs_authored_prose_after_the_current_row_is_edited(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-historic-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload("the original authored text"),
        precedence=10,
        origin=OverrideOriginEnum.HOUSE_RULE,
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    recorded = resolution.binding
    assert recorded is not None
    original = service(runtime).replay(recorded)

    row = runtime.session.get(MechanicalOverrideORM, "ov-historic-prose")
    assert row is not None
    row.payload = replace_prose_payload("a completely different current text")
    row.is_enabled = False
    row.precedence = 999
    row.override_origin = OverrideOriginEnum.PACKAGE_PATCH.value
    runtime.session.flush()

    replayed = service(runtime).replay(recorded)
    assert replayed.applied_overrides == original.applied_overrides
    (record,) = [r for r in replayed.records if r.semantic_key == SPELL_KEY]
    (component,) = [c for c in record.components if c.semantic_key == OPEN_ENDED_KEY]
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "the original authored text"


def test_replay_reconstructs_authored_prose_after_the_current_row_is_deleted(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-historic-prose",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("the original addendum"),
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    recorded = resolution.binding
    assert recorded is not None
    original = service(runtime).replay(recorded)

    row = runtime.session.get(MechanicalOverrideORM, "ov-historic-prose")
    assert row is not None
    runtime.session.delete(row)
    runtime.session.flush()

    replayed = service(runtime).replay(recorded)
    assert replayed.applied_overrides == original.applied_overrides
    assert replayed.records == original.records


def test_replay_reconstructs_the_demoted_handling_after_current_rows_change(
    runtime: RuntimeFixture,
) -> None:
    """Effective-content classification is recorded evidence, not a live query.

    The recorded binding names an override-set version whose derived handling
    (STRUCTURED, after a promotion was disabled) must reconstruct exactly, even
    after the current override rows that produced it are edited or deleted —
    the same replay guarantee every other applied change gets.
    """
    author_override(
        runtime.session,
        override_id="ov-append-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_prose_payload("a house-rule clarification"),
        precedence=10,
    )
    author_override(
        runtime.session,
        override_id="ov-disable-prose",
        target=STRUCTURED_PROSE_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
        precedence=20,
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.RESOLVED
    recorded = resolution.binding
    assert recorded is not None
    original = service(runtime).replay(recorded)
    (original_record,) = [r for r in original.records if r.semantic_key == SPELL_KEY]
    (original_component,) = [
        c for c in original_record.components if c.semantic_key == DESCRIPTOR_KEY
    ]
    assert original_component.handling is ComponentHandling.STRUCTURED

    disable_row = runtime.session.get(MechanicalOverrideORM, "ov-disable-prose")
    assert disable_row is not None
    runtime.session.delete(disable_row)
    append_row = runtime.session.get(MechanicalOverrideORM, "ov-append-prose")
    assert append_row is not None
    append_row.payload = append_prose_payload("current state is now unsuppressed")
    runtime.session.flush()

    # Current state, unlike the replayed one, would resolve MIXED again — the
    # point is that replay ignores this and reconstructs the original STRUCTURED.
    current = typed_component(runtime, SPELL_KEY, DESCRIPTOR_KEY)
    assert current.handling is ComponentHandling.MIXED

    replayed = service(runtime).replay(recorded)
    (record,) = [r for r in replayed.records if r.semantic_key == SPELL_KEY]
    (component,) = [c for c in record.components if c.semantic_key == DESCRIPTOR_KEY]
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.governing_prose == ()
    assert [f.fact_key for f in component.facts] == [DESCRIPTOR_FACT_KEY]


# ---------------------------------------------------------------------------
# Invalid, blank, malformed, and cross-release prose overrides fail closed
# ---------------------------------------------------------------------------


def test_blank_authored_prose_text_is_refused(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-blank",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload={"patch": "replace_prose", "text": "   "},
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "non-blank" in result.detail


def test_missing_text_field_is_refused(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-missing-text",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload={"patch": "append_prose"},
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "missing" in result.detail


def test_a_prose_override_naming_no_such_component_is_refused(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-missing-target",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.PROSE,
            record_key=SPELL_KEY,
            component_key="no-such-component",
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload(),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "names no component" in result.detail


def test_a_cross_release_prose_override_is_refused(runtime: RuntimeFixture) -> None:
    author_override(
        runtime.session,
        override_id="ov-cross-release",
        target=PROSE_BOUND_PROSE_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_prose_payload(),
        release_version="5.2.1-some-other-release",
    )
    resolution = service(runtime).resolve(package_uuid=runtime.package_uuid)
    assert resolution.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "authored against release" in resolution.detail


def test_appending_prose_onto_a_fact_target_is_type_incompatible(
    runtime: RuntimeFixture,
) -> None:
    """A prose patch aimed at a fact target is outside the closed pairing."""
    from tests.services.rules_authority.conftest import DESCRIPTOR_FACT_TARGET

    author_override(
        runtime.session,
        override_id="ov-wrong-kind",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload={"patch": "append_prose", "text": "should never apply"},
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE


def test_append_onto_a_fact_target_remains_unpermitted_alongside_prose(
    runtime: RuntimeFixture,
) -> None:
    """APPEND has no honest family for a fact target — unchanged by this PR.

    Adding the ``prose`` target kind and its two new families must not loosen
    the existing rule that a fact has no multiplicity to append into.
    """
    from tests.services.rules_authority.conftest import DESCRIPTOR_FACT_TARGET

    author_override(
        runtime.session,
        override_id="ov-append-fact-family-mismatch",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(),
    )
    result = refusal(runtime)
    assert result.outcome is AuthorityOutcome.INVALID_OVERRIDE
    assert "no multiplicity" in result.detail


# ---------------------------------------------------------------------------
# Whole-component authored prose (REPLACE_COMPONENT / APPEND_COMPONENT)
# ---------------------------------------------------------------------------


def test_replace_component_may_declare_prose_bound_with_authored_prose(
    runtime: RuntimeFixture,
) -> None:
    author_override(
        runtime.session,
        override_id="ov-whole-component-prose",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key=OPEN_ENDED_KEY,
        ),
        operation=OverrideOperationEnum.REPLACE,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "a completely authored component",
            },
        },
    )
    component = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    assert component.handling is ComponentHandling.PROSE_BOUND
    assert component.irreducibility_reason_code is None
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "a completely authored component"


def test_append_component_may_declare_mixed_with_facts_and_authored_prose(
    runtime: RuntimeFixture,
) -> None:
    check_fact = AbilityCheckFact(
        ability=AbilityScore.STRENGTH,
        dc_kind=DcKind.FIXED,
        dc_value=12,
        context=RollContext.ABILITY_CHECK,
    )
    author_override(
        runtime.session,
        override_id="ov-whole-mixed-add",
        target=MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY),
        operation=OverrideOperationEnum.APPEND,
        payload={
            "patch": "append_component",
            "component": {
                "semantic_key": "house-mixed-rider",
                "handling": "mixed",
                "facts": [fact_payload(check_fact)],
                "authored_prose": "context for the added mixed component",
            },
        },
    )
    component = typed_component(runtime, SPELL_KEY, "house-mixed-rider")
    assert component.handling is ComponentHandling.MIXED
    assert len(component.facts) == 1
    (entry,) = component.governing_prose
    assert isinstance(entry, AuthoredProse)
    assert entry.text == "context for the added mixed component"


# ---------------------------------------------------------------------------
# Legacy chunk-targeting overrides never alter the new views
# ---------------------------------------------------------------------------


def test_a_legacy_chunk_override_does_not_alter_the_new_authority_views(
    runtime: RuntimeFixture,
) -> None:
    """The service never reads ``rp_overrides`` (docstring guarantee, pinned)."""
    typed_before = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    gm_before = gm_component(runtime, OPEN_ENDED_KEY)

    runtime.session.add(
        RuleOverrideORM(
            override_id="legacy-chunk-override",
            rules_package_id=str(runtime.package_uuid),
            target_chunk_id=WISH_CHUNK,
            target_entity_id=None,
            override_origin="house_rule",
            override_operation="replace",
            override_payload='{"content": "a legacy chunk edit"}',
            precedence=1,
            is_enabled=True,
            created_at=NOW,
        )
    )
    runtime.session.flush()

    typed_after = typed_component(runtime, SPELL_KEY, OPEN_ENDED_KEY)
    gm_after = gm_component(runtime, OPEN_ENDED_KEY)
    assert typed_after == typed_before
    assert gm_after == gm_before
    (source,) = gm_after.governing_prose
    assert isinstance(source, SourceProse)
    assert source.text == PROSE_TEXT


# ---------------------------------------------------------------------------
# house_rules is never silently promoted to trusted mechanical authority
# ---------------------------------------------------------------------------


def test_house_rules_is_never_referenced_by_the_typed_override_system(
    tmp_path: Path,
) -> None:
    """Owner Decision 2026-08-08: no implicit promotion path.

    The free-form session ``house_rules`` string is a wholly different model
    (``models/session.py``); this pins that the typed override system never
    reads it, so no future edit can wire it in without this test noticing.
    """
    package_dir = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "afterworlds"
        / ("services/rules_authority")
    )
    assert package_dir.is_dir()
    offenders = [
        path
        for path in package_dir.glob("*.py")
        if re.search(r"house_rules", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
