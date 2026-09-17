"""Accepted review units — CRD Issue 5d (#137), Owner Decision of 2026-09-16.

A review unit records that a human read one coherent stretch of source and what
they decided about it. Four separable obligations are proven here, and they
fail in different places on purpose:

* the inventory **persists, reconstructs and identifies** — it is part of what
  the projection means, so it enters the projection identity and the
  persisted-state digest and a tampered row is caught;
* the inventory is **checked into the representation**, never read out of it —
  an expected rule with no home is a finding, while representation content no
  unit expected is not;
* every leaf a unit names is **accounted for by some decision** — a rule read
  from it, a supporting group, or an excluded group with a reason. A unit that
  decided nothing certifies nothing, which is what stops blank accounting
  buying the partition relaxation; and
* a leaf a unit covers is **relieved of the complete-partition rule and of
  nothing else** — overlap, bad bounds and derived-id errors are still reported
  on exactly that leaf.

The precision an expectation buys is bounded, and the bound is deliberate:
naming the component, the family and the *source spans the rule was read from*
tells apart two exceptions of one family read from different sentences, and
catches a rule or passage substituted from the wrong source text. Two facts of
one family read from the same span remain the exact accepted-oracle comparison's
job, which already catches any changed build against an unchanged oracle.

Negative controls perturb one thing each. The oracle is never perturbed to make
a candidate pass.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import (
    derive_span_id,
    validate_partition,
)
from afterworlds.ingestion.mechanical.models import (
    ExcludedGroup,
    ExpectedRule,
    ReviewState,
    ReviewUnit,
    ReviewUnitKind,
    SemanticDisposition,
    SemanticSpan,
    SupportingGroup,
)
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    delete_projection,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    projection_payload,
    review_unit_payload,
    review_unit_violations,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ComponentHandling,
    MovementMode,
    MovementPermissionFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RepresentationDraft,
    fact_target_key,
)
from afterworlds.persistence.orm.mechanical import (
    REVIEW_GROUP_EXCLUDED,
    REVIEW_GROUP_SUPPORTING,
    MechanicalReviewExpectationORM,
    MechanicalReviewGroupORM,
    MechanicalReviewUnitORM,
)
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
    PROSE_LEAF,
    PROSE_SPAN,
    REVIEW_UNITS,
    SPELL_KEY,
    SPELL_LEAF,
    SPELL_SPAN,
    SUPPORT_LEAF,
    bound_corpus,
    build_candidate,
    build_ledger,
    build_representation,
    reviewed_candidate,
)

DESCRIPTOR_FAMILY = DESCRIPTOR_FACT.FAMILY.value

#: The declared policy of every candidate this module builds. Named once so the
#: policy-version negative controls below read as the deliberate substitutions
#: they are.
POLICY_2 = "5d-semantic-policy-2"
POLICY_1 = "5d-semantic-policy-1"

#: A span id no classification in this module states.
UNSTATED_SPAN = derive_span_id(SPELL_LEAF, 5, 9)


def _persist(session: Session, units: tuple[ReviewUnit, ...] = REVIEW_UNITS):  # type: ignore[no-untyped-def]
    identified = identify_projection(reviewed_candidate(units))
    persist_draft(session, identified, now=NOW)
    return identified


def _violations(
    units: tuple[ReviewUnit, ...],
    policy_version: str = POLICY_2,
    *,
    draft: RepresentationDraft | None = None,
    spans: tuple[SemanticSpan, ...] | None = None,
) -> list[str]:
    return review_unit_violations(
        units,
        build_representation() if draft is None else draft,
        policy_version,
        build_ledger().spans if spans is None else spans,
    )


def _entry_unit(*rules: ExpectedRule) -> ReviewUnit:
    """The entry unit narrowed to the spell leaf, stating *rules* and nothing else.

    Its excluded group is kept, so the leaf stays accounted for however the
    rule under test resolves and each control below reports exactly the one
    thing it perturbs.
    """
    return replace(REVIEW_UNITS[0], leaf_ids=(SPELL_LEAF,), expected_rules=rules)


def _wish_unit(*rules: ExpectedRule) -> ReviewUnit:
    """The entry unit over both its leaves — for rules read from the prose leaf."""
    return replace(REVIEW_UNITS[0], expected_rules=rules)


# ---------------------------------------------------------------------------
# Persistence, reconstruction and identity
# ---------------------------------------------------------------------------


def test_roundtrip_reconstructs_the_exact_review_inventory(session: Session) -> None:
    identified = _persist(session)
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)

    assert projection_payload(rebuilt) == projection_payload(identified.candidate)
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid

    units = {u.unit_id: u for u in rebuilt.review_units}
    entry = units["unit-wish-entry"]
    assert entry.kind is ReviewUnitKind.ENTRY
    assert entry.leaf_ids == (PROSE_LEAF, SPELL_LEAF)
    assert entry.expected_rules == (
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, (SPELL_SPAN,)),
        ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None, (PROSE_SPAN,)),
    )
    assert entry.excluded_groups == (
        ExcludedGroup(
            (SPELL_LEAF,),
            "the spell-list heading in this leaf is navigation, not a rule",
        ),
    )
    assert entry.supporting_groups == ()

    # The unit that states one supporting decision and no rule reconstructs as
    # that decision, not as an empty unit.
    support = units["unit-support-section"]
    assert support.supporting_groups == (
        SupportingGroup((SUPPORT_LEAF,), SPELL_KEY, ""),
    )
    assert support.expected_rules == ()
    assert support.excluded_groups == ()


def test_a_rule_accepted_as_governing_prose_reconstructs_as_such(
    session: Session,
) -> None:
    """``fact_family`` NULL is a recorded judgement, not a missing value."""
    identified = _persist(session)
    row = session.execute(
        select(MechanicalReviewExpectationORM).where(
            MechanicalReviewExpectationORM.component_key == OPEN_ENDED_KEY
        )
    ).scalar_one()
    assert row.fact_family is None
    assert row.source_span_ids == [PROSE_SPAN]

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    prose_rule = next(
        r
        for u in rebuilt.review_units
        for r in u.expected_rules
        if r.component_key == OPEN_ENDED_KEY
    )
    assert prose_rule.fact_family is None
    assert prose_rule.source_span_ids == (PROSE_SPAN,)


def test_a_non_canonical_inventory_still_verifies_and_reidentifies(
    session: Session,
) -> None:
    """Recorded order is not evidence here, so reordering must change nothing.

    Contrast the batch scope, whose recorded order *is* retained evidence. A
    unit persisted from a reversed source reconstructs canonically, and if
    verification compared anything order-bearing this would read as tamper.
    """
    reversed_units = tuple(
        replace(
            unit,
            leaf_ids=tuple(reversed(unit.leaf_ids)),
            expected_rules=tuple(reversed(unit.expected_rules)),
        )
        for unit in reversed(REVIEW_UNITS)
    )
    identified = _persist(session, reversed_units)

    assert verify_reconstruction(session, identified) == ()
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid
    assert (
        identified.projection_uuid
        == identify_projection(reviewed_candidate()).projection_uuid
    )


def test_an_honest_reviewed_draft_has_no_reconstruction_findings(
    session: Session,
) -> None:
    assert verify_reconstruction(session, _persist(session)) == ()


def test_the_review_inventory_is_inside_the_projection_identity() -> None:
    """Two builds that reviewed different scope are two authorities."""
    without = identify_projection(build_candidate()).projection_uuid
    with_units = identify_projection(reviewed_candidate()).projection_uuid
    assert without != with_units

    fewer = identify_projection(reviewed_candidate(REVIEW_UNITS[:1])).projection_uuid
    assert fewer not in {without, with_units}


def test_a_changed_coverage_decision_is_a_different_authority() -> None:
    """The decisions this round adds carry meaning, so they move identity.

    A different reason for excluding the same text, and the same rule with its
    source text forgotten, are each a different claim about what was reviewed.
    """
    reviewed = identify_projection(reviewed_candidate()).projection_uuid

    reworded = replace(
        REVIEW_UNITS[0],
        excluded_groups=(ExcludedGroup((SPELL_LEAF,), "boilerplate"),),
    )
    unsourced = replace(
        REVIEW_UNITS[0],
        expected_rules=tuple(
            replace(rule, source_span_ids=()) for rule in REVIEW_UNITS[0].expected_rules
        ),
    )
    relinked = replace(
        REVIEW_UNITS[1],
        supporting_groups=(
            SupportingGroup((SUPPORT_LEAF,), SPELL_KEY, DESCRIPTOR_KEY),
        ),
    )
    moved = {
        identify_projection(reviewed_candidate((unit, REVIEW_UNITS[1]))).projection_uuid
        for unit in (reworded, unsourced)
    }
    moved.add(
        identify_projection(
            reviewed_candidate((REVIEW_UNITS[0], relinked))
        ).projection_uuid
    )
    assert reviewed not in moved
    assert len(moved) == 3


def test_a_candidate_claiming_no_unit_identifies_exactly_as_before() -> None:
    """The additive proof: the key is omitted, not emitted empty.

    This is what keeps every one of the seven accepted batches — none of which
    states a review unit — at the identity it was accepted under.
    """
    payload = projection_payload(build_candidate())
    assert "review_units" not in payload


def test_tampering_an_expected_family_is_caught_by_the_digest(
    session: Session,
) -> None:
    identified = _persist(session)
    recorded = record_persisted_state_digest(session, identified.projection_uuid)

    row = session.execute(
        select(MechanicalReviewExpectationORM).where(
            MechanicalReviewExpectationORM.component_key == DESCRIPTOR_KEY
        )
    ).scalar_one()
    row.fact_family = "movement_cost"
    session.flush()

    assert (
        compute_persisted_state_digest(session, identified.projection_uuid) != recorded
    )
    findings = verify_persisted_state(session, identified.projection_uuid)
    assert findings != ()


def test_tampering_an_excluded_reason_is_caught_by_the_digest(
    session: Session,
) -> None:
    """The reason a stretch was excused is retained state, not a comment."""
    identified = _persist(session)
    recorded = record_persisted_state_digest(session, identified.projection_uuid)

    row = session.execute(
        select(MechanicalReviewGroupORM).where(
            MechanicalReviewGroupORM.role == REVIEW_GROUP_EXCLUDED
        )
    ).scalar_one()
    row.reason = "no rules here"
    session.flush()

    assert (
        compute_persisted_state_digest(session, identified.projection_uuid) != recorded
    )
    assert verify_persisted_state(session, identified.projection_uuid) != ()


def test_tampering_a_supporting_group_is_caught_by_reidentification(
    session: Session,
) -> None:
    identified = _persist(session)
    row = session.execute(
        select(MechanicalReviewGroupORM).where(
            MechanicalReviewGroupORM.role == REVIEW_GROUP_SUPPORTING
        )
    ).scalar_one()
    row.supports_record_key = "spell:fireball"
    session.flush()

    assert verify_reconstruction(session, identified) != ()


def test_tampering_a_unit_kind_is_caught_by_reidentification(
    session: Session,
) -> None:
    identified = _persist(session)
    row = session.execute(
        select(MechanicalReviewUnitORM).where(
            MechanicalReviewUnitORM.unit_id == "unit-wish-entry"
        )
    ).scalar_one()
    row.kind = ReviewUnitKind.TABLE.value
    session.flush()

    assert verify_reconstruction(session, identified) != ()


def test_dropping_a_unit_is_caught(session: Session) -> None:
    """Omission, not just tamper: a unit deleted after the fact is noticed."""
    identified = _persist(session)
    row = session.execute(
        select(MechanicalReviewUnitORM).where(
            MechanicalReviewUnitORM.unit_id == "unit-support-section"
        )
    ).scalar_one()
    session.delete(row)
    session.flush()

    assert verify_reconstruction(session, identified) != ()


def test_deleting_a_projection_removes_its_review_inventory(
    session: Session,
) -> None:
    identified = _persist(session)
    delete_projection(session, identified.projection_uuid)
    session.flush()

    assert session.execute(select(MechanicalReviewUnitORM)).scalars().all() == []
    assert session.execute(select(MechanicalReviewExpectationORM)).scalars().all() == []
    assert session.execute(select(MechanicalReviewGroupORM)).scalars().all() == []


# ---------------------------------------------------------------------------
# The inventory as coverage evidence
# ---------------------------------------------------------------------------


def test_an_honest_inventory_is_not_a_finding() -> None:
    assert _violations(REVIEW_UNITS) == []
    assert validate_candidate(reviewed_candidate(), bound_corpus()) == ()


def test_an_expected_rule_with_no_component_is_reported() -> None:
    """The omission this inventory exists to catch."""
    unit = _entry_unit(
        ExpectedRule(SPELL_KEY, "material-components", None, (SPELL_SPAN,))
    )
    (finding,) = _violations((unit,))
    assert "spell:wish/material-components has no component" in finding


def test_a_rule_accepted_as_prose_against_a_structured_component_is_reported() -> None:
    """A component silently resolved to structured has dropped the passage."""
    unit = _entry_unit(ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, None, (SPELL_SPAN,)))
    (finding,) = _violations((unit,))
    assert "accepted as governing prose, but the component is structured" in finding


def test_a_rule_naming_a_family_the_component_lacks_is_reported() -> None:
    unit = _entry_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, "movement_cost", (SPELL_SPAN,))
    )
    (finding,) = _violations((unit,))
    assert "requires fact family 'movement_cost'" in finding


def test_a_family_this_build_does_not_declare_is_a_finding_not_a_crash() -> None:
    """An expectation is a claim about the source, not about this build.

    A reviewer may legitimately name a family no released build implements. That
    has to be reportable, because a build that could not read the claim could
    not tell anyone it went unmet.
    """
    unit = _entry_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, "not_a_family", (SPELL_SPAN,))
    )
    (finding,) = _violations((unit,))
    assert "requires fact family 'not_a_family'" in finding


def test_an_expected_rule_naming_no_source_is_reported() -> None:
    """An expectation nobody can trace to source text is not review evidence."""
    unit = _entry_unit(ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, ()))
    (finding,) = _violations((unit,))
    assert "names no source span it was read from" in finding


def test_an_expected_rule_naming_an_unclassified_span_is_reported() -> None:
    """Reported twice on purpose: the link is bad *and* nothing was read there."""
    unit = _entry_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, (UNSTATED_SPAN,))
    )
    findings = _violations((unit,))
    assert any("which the classification does not state" in f for f in findings)
    assert any("carries that family from other source text only" in f for f in findings)


def test_a_rule_read_from_source_this_unit_does_not_review_is_reported() -> None:
    unit = _entry_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, (PROSE_SPAN,))
    )
    findings = _violations((unit,))
    assert any(
        f"of leaf {PROSE_LEAF}, which this unit does not review" in f for f in findings
    )


def test_a_rule_substituted_from_the_wrong_source_text_is_reported() -> None:
    """The family survives; the source link is what fails.

    Same component, same family, read from a different passage. Without the
    source link this is indistinguishable from the honest expectation.
    """
    unit = _wish_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, (PROSE_SPAN,))
    )
    (finding,) = _violations((unit,))
    assert "carries that family from other source text only" in finding


def test_prose_substituted_from_the_wrong_source_text_is_reported() -> None:
    """The prose half of the same substitution: bound, but to another passage."""
    unit = _entry_unit(ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None, (SPELL_SPAN,)))
    (finding,) = _violations((unit,))
    assert "binds no prose from" in finding


def test_representation_content_no_unit_expected_is_not_a_violation() -> None:
    """A unit states what review found, not a census of what may be there."""
    assert _violations((_entry_unit(),)) == []


def test_a_unit_covering_no_leaf_is_reported() -> None:
    unit = replace(REVIEW_UNITS[0], leaf_ids=())
    assert any("names no source leaves" in f for f in _violations((unit,)))


def test_a_unit_naming_one_leaf_twice_is_reported() -> None:
    unit = replace(REVIEW_UNITS[0], leaf_ids=(SPELL_LEAF, SPELL_LEAF))
    assert any("names a leaf twice" in f for f in _violations((unit,)))


def test_a_duplicate_unit_id_is_reported() -> None:
    twin = replace(REVIEW_UNITS[1], unit_id=REVIEW_UNITS[0].unit_id)
    assert any(
        "declared more than once" in f for f in _violations((REVIEW_UNITS[0], twin))
    )


# ---------------------------------------------------------------------------
# Two exceptions of one family, read from two sentences
# ---------------------------------------------------------------------------

EXCEPTIONS_KEY = "movement-exceptions"
CRAWL_SENTENCE = derive_span_id(SPELL_LEAF, 0, 20)
CLIMB_SENTENCE = derive_span_id(SPELL_LEAF, 20, 40)
CRAWL_EXCEPTION = MovementPermissionFact(mode=MovementMode.CRAWL)
CLIMB_EXCEPTION = MovementPermissionFact(mode=MovementMode.CLIMB)
MOVEMENT_FAMILY = CRAWL_EXCEPTION.FAMILY.value


def _sentence_spans() -> tuple[SemanticSpan, ...]:
    """The accepted ledger plus the two sentences of the spell leaf.

    Sub-leaf spans, so they overlap the leaf-wide span the fixture accepts.
    That is irrelevant here on purpose: ``review_unit_violations`` reads the
    classification only to learn which leaf a span belongs to, and partition
    soundness is :func:`validate_partition`'s question, proven separately below.
    """
    return build_ledger().spans + tuple(
        SemanticSpan(
            span_id=span_id,
            leaf_id=SPELL_LEAF,
            char_start=start,
            char_end=end,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        )
        for span_id, start, end in (
            (CRAWL_SENTENCE, 0, 20),
            (CLIMB_SENTENCE, 20, 40),
        )
    )


def _exceptions_draft(
    *facts: MovementPermissionFact,
) -> RepresentationDraft:
    """The shared draft plus one component stating *facts* as exceptions.

    Each exception carries its own provenance edge to the sentence that states
    it, through the same :func:`fact_target_key` every claim in this codebase
    is keyed by.
    """
    sources = {CRAWL_EXCEPTION: CRAWL_SENTENCE, CLIMB_EXCEPTION: CLIMB_SENTENCE}
    base = build_representation()
    return replace(
        base,
        components=(
            *base.components,
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=EXCEPTIONS_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=facts,
            ),
        ),
        provenance=(
            *base.provenance,
            *(
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT,
                    fact_target_key(SPELL_KEY, EXCEPTIONS_KEY, fact),
                    sources[fact],
                    ProvenanceRole.PRIMARY,
                )
                for fact in facts
            ),
        ),
    )


def _exception_unit() -> ReviewUnit:
    return _entry_unit(
        ExpectedRule(SPELL_KEY, EXCEPTIONS_KEY, MOVEMENT_FAMILY, (CRAWL_SENTENCE,)),
        ExpectedRule(SPELL_KEY, EXCEPTIONS_KEY, MOVEMENT_FAMILY, (CLIMB_SENTENCE,)),
    )


def test_two_exceptions_of_one_family_both_have_homes() -> None:
    assert (
        _violations(
            (_exception_unit(),),
            draft=_exceptions_draft(CRAWL_EXCEPTION, CLIMB_EXCEPTION),
            spans=_sentence_spans(),
        )
        == []
    )


def test_dropping_one_of_two_exceptions_fails_exactly_its_expectation() -> None:
    """The defect this round exists to close.

    A family-presence check passes here: the component still carries a
    ``movement_permission`` fact. The surviving exception answers for itself
    and for nothing else, because the dropped one was read from another
    sentence.
    """
    (finding,) = _violations(
        (_exception_unit(),),
        draft=_exceptions_draft(CRAWL_EXCEPTION),
        spans=_sentence_spans(),
    )
    assert CLIMB_SENTENCE in finding
    assert "carries that family from other source text only" in finding


def test_a_shared_representation_satisfies_a_rule_read_from_either_span() -> None:
    """One structure legitimately stated by two passages is not an omission.

    The contrast with the wrong-source control above is the extra edge: the
    fact really is claimed from the prose span, so the expectation read there
    has a home.
    """
    base = build_representation()
    shared = replace(
        base,
        provenance=(
            *base.provenance,
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FACT),
                PROSE_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        ),
    )
    unit = _wish_unit(
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY, (PROSE_SPAN,))
    )
    assert _violations((unit,), draft=shared) == []


# ---------------------------------------------------------------------------
# Supporting and excluded groups
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("group", "expected"),
    [
        (
            SupportingGroup((SUPPORT_LEAF,), ""),
            "names no authority it supports",
        ),
        (
            SupportingGroup((SUPPORT_LEAF,), "spell:fireball"),
            "supports record spell:fireball, which the representation does not carry",
        ),
        (
            SupportingGroup((SUPPORT_LEAF,), SPELL_KEY, "material-components"),
            "supports spell:wish/material-components, which the representation "
            "does not carry",
        ),
    ],
    ids=["unlinked", "unknown-record", "unknown-component"],
)
def test_supporting_material_must_link_to_the_authority_it_explains(
    group: SupportingGroup, expected: str
) -> None:
    """Useful text kept with nothing saying what it is useful *for* explains nothing."""
    unit = replace(REVIEW_UNITS[1], supporting_groups=(group,))
    (finding,) = _violations((unit,))
    assert expected in finding


@pytest.mark.parametrize("reason", ["", "   ", "\n"])
def test_an_excluded_group_with_a_blank_reason_is_reported(reason: str) -> None:
    unit = replace(
        REVIEW_UNITS[0],
        leaf_ids=(SPELL_LEAF,),
        expected_rules=(),
        excluded_groups=(ExcludedGroup((SPELL_LEAF,), reason),),
    )
    (finding,) = _violations((unit,))
    assert "excluded group ['leaf-spell'] states an empty reason" in finding


@pytest.mark.parametrize(
    "groups",
    [
        {"supporting_groups": (SupportingGroup((), SPELL_KEY),)},
        {
            "supporting_groups": (),
            "excluded_groups": (ExcludedGroup((), "page furniture"),),
        },
    ],
    ids=["supporting", "excluded"],
)
def test_a_group_naming_no_source_is_reported(groups: dict[str, object]) -> None:
    unit = replace(REVIEW_UNITS[1], **groups)
    assert any("group [] names no source leaves" in f for f in _violations((unit,)))


@pytest.mark.parametrize(
    "groups",
    [
        {"supporting_groups": (SupportingGroup((PROSE_LEAF,), SPELL_KEY),)},
        {
            "supporting_groups": (),
            "excluded_groups": (ExcludedGroup((PROSE_LEAF,), "page furniture"),),
        },
    ],
    ids=["supporting", "excluded"],
)
def test_a_group_deciding_source_outside_its_unit_is_reported(
    groups: dict[str, object],
) -> None:
    """A decision reaching past the source a human read covers nothing here."""
    unit = replace(REVIEW_UNITS[1], **groups)
    findings = _violations((unit,))
    assert any(
        f"names ['{PROSE_LEAF}'], which this unit does not review" in f
        for f in findings
    )
    # …and having decided nothing about its own leaf, the unit is unaccounted.
    assert any("named by no expected rule" in f for f in findings)


def test_a_wholly_supporting_or_wholly_excluded_unit_is_coverage() -> None:
    """Neither kind of coherent group has to state a rule to account for itself."""
    assert _violations((REVIEW_UNITS[1],)) == []

    excluded_only = ReviewUnit(
        unit_id="unit-prose-aside",
        kind=ReviewUnitKind.SECTION,
        leaf_ids=(PROSE_LEAF,),
        excluded_groups=(
            ExcludedGroup((PROSE_LEAF,), "the illustration caption states no rule"),
        ),
    )
    assert _violations((excluded_only,)) == []


def test_a_unit_that_decided_nothing_certifies_nothing() -> None:
    """Blank accounting must not buy the partition relaxation.

    A unit naming every leaf, with no rule, no supporting group and no
    exclusion, used to validate clean and relieve all three leaves of
    completeness. Now it reports the leaves it decided nothing about, and the
    text it never accounted for is uncovered again.
    """
    blank = ReviewUnit(
        unit_id="unit-blank",
        kind=ReviewUnitKind.ENTRY,
        leaf_ids=(SPELL_LEAF, PROSE_LEAF, SUPPORT_LEAF),
    )
    findings = validate_candidate(
        reviewed_candidate((blank,)), bound_corpus(leaf_lengths=LONGER_SPELL_LEAF)
    )
    assert (
        sum(
            "named by no expected rule, supporting group or excluded group" in f
            for f in findings
        )
        == 3
    )
    assert any("uncovered text [40,60)" in f for f in findings)


def test_a_unit_whose_membership_leaves_its_rules_behind_is_reported() -> None:
    """Narrowing the source a unit reviewed does not narrow what it certifies.

    Replacing the entry unit's leaves while keeping its rules used to be silent:
    the rules named a component and a family, and neither mentions source.
    """
    moved = replace(REVIEW_UNITS[0], leaf_ids=(SUPPORT_LEAF,), excluded_groups=())
    findings = _violations((moved,))
    assert sum("which this unit does not review" in f for f in findings) == 2
    assert any("named by no expected rule" in f for f in findings)


# ---------------------------------------------------------------------------
# The policy that admits a unit at all
# ---------------------------------------------------------------------------


def test_a_unit_declared_under_policy_1_is_refused() -> None:
    """Policy 1 recorded no review-unit catalog, so it admits no unit.

    The seven accepted batches declare policy 1. This is the check that stops
    an inventory being read back under a contract policy 1 never stated.
    """
    findings = _violations(REVIEW_UNITS, POLICY_1)
    assert all("is not admitted by semantic policy" in f for f in findings)
    assert len(findings) == len(REVIEW_UNITS)


def test_an_unrecognised_policy_is_reported_not_raised() -> None:
    """``review_unit_violations`` reports; it must not raise out of its contract.

    An unknown policy version is already a ``policy_meaning_violations``
    finding. Consulting the kind catalog here turned that finding into a
    ``ValueError`` out of a reporting API, which is why the guard exists.
    """
    (finding,) = _violations(REVIEW_UNITS, "5d-semantic-policy-0")
    assert "states no review-unit kinds" in finding


def test_an_empty_inventory_never_consults_the_policy_catalog() -> None:
    assert (
        review_unit_violations(
            (), build_representation(), "5d-semantic-policy-0", build_ledger().spans
        )
        == []
    )


# ---------------------------------------------------------------------------
# What a covered leaf is, and is not, relieved of
# ---------------------------------------------------------------------------

#: The spell leaf, longer than the span accepted over it. Without a unit the
#: trailing text is uncovered; with one it is reviewed.
LONGER_SPELL_LEAF = {SPELL_LEAF: 60, PROSE_LEAF: 30, SUPPORT_LEAF: 20}


def test_an_uncovered_leaf_still_demands_a_complete_partition() -> None:
    findings = validate_candidate(
        build_candidate(), bound_corpus(leaf_lengths=LONGER_SPELL_LEAF)
    )
    assert any("uncovered text [40,60)" in f for f in findings)


def test_a_leaf_a_unit_covers_is_relieved_of_completeness() -> None:
    findings = validate_candidate(
        reviewed_candidate(), bound_corpus(leaf_lengths=LONGER_SPELL_LEAF)
    )
    assert findings == ()


def test_a_covered_leaf_is_still_held_to_overlap() -> None:
    overlapping = build_ledger(
        build_ledger().spans
        + (
            SemanticSpan(
                span_id=derive_span_id(SPELL_LEAF, 20, 50),
                leaf_id=SPELL_LEAF,
                char_start=20,
                char_end=50,
                disposition=SemanticDisposition.SUBSTANTIVE,
                review_state=ReviewState.ACCEPTED,
            ),
        )
    )
    findings = validate_partition(
        SPELL_LEAF, 60, overlapping.spans, require_complete=False
    )
    assert any("overlap" in f for f in findings)


def test_a_covered_leaf_is_still_held_to_its_bounds_and_derived_id() -> None:
    out_of_bounds = (
        SemanticSpan(
            span_id=derive_span_id(SPELL_LEAF, 0, 99),
            leaf_id=SPELL_LEAF,
            char_start=0,
            char_end=99,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        ),
    )
    assert any(
        "outside leaf text" in f
        for f in validate_partition(
            SPELL_LEAF, 40, out_of_bounds, require_complete=False
        )
    )

    misderived = (
        SemanticSpan(
            span_id=derive_span_id(SPELL_LEAF, 0, 10),
            leaf_id=SPELL_LEAF,
            char_start=0,
            char_end=20,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        ),
    )
    assert any(
        "does not match its range" in f
        for f in validate_partition(SPELL_LEAF, 40, misderived, require_complete=False)
    )


def test_a_covered_leaf_with_no_spans_at_all_is_accepted() -> None:
    """The point of the amendment: exact subspans stay optional, not forbidden."""
    assert validate_partition(SPELL_LEAF, 40, (), require_complete=False) == ()


def test_a_unit_naming_a_leaf_the_release_does_not_have_is_reported() -> None:
    """Named as a membership error, so a reviewer looks at the unit not at spans."""
    stray = replace(
        REVIEW_UNITS[1],
        leaf_ids=("leaf-not-in-this-release",),
        supporting_groups=(SupportingGroup(("leaf-not-in-this-release",), SPELL_KEY),),
    )
    findings = validate_candidate(
        reviewed_candidate((REVIEW_UNITS[0], stray)), bound_corpus()
    )
    assert any(
        "leaf leaf-not-in-this-release: named by a review unit but not in the "
        "bound release" in f
        for f in findings
    )


# ---------------------------------------------------------------------------
# The committed accepted artifact
# ---------------------------------------------------------------------------


def _bounded_payload() -> dict[str, object]:
    return accepted_inputs_payload(load_accepted_inputs(BOUNDED_ORACLE_PATH))


def _write(tmp_path, payload: dict[str, object]):  # type: ignore[no-untyped-def]
    path = tmp_path / "reviewed_oracle.json"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        json.dump(payload, handle, indent=2)
    return path


def _accepted_by(payload: dict[str, object], units, batch_id="batch-wish") -> None:  # type: ignore[no-untyped-def]
    """State *units* in *payload* and record the action that accepted them.

    An inventory nobody is recorded as having accepted is refused, so a test
    that wants a legitimately reviewed artifact has to state both halves.
    """
    payload["review_units"] = review_unit_payload(units)
    acceptance = payload["acceptance"]
    acceptance["review_unit_records"] = [  # type: ignore[index]
        {
            "unit_id": u.unit_id,
            "batch_id": batch_id,
            "reviewer": "owner",
            "accepted_at": "2026-08-09T00:00:00Z",
        }
        for u in units
    ]


def test_an_accepted_artifact_carries_its_review_inventory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    payload = _bounded_payload()
    _accepted_by(payload, REVIEW_UNITS)
    expected_units = payload["review_units"]
    oracle = load_accepted_inputs(_write(tmp_path, payload)).oracle

    # Compared canonically, because that is the form the file states: the
    # writer sorts units, their leaves and their expected rules, and the loader
    # reads back exactly what is written. Canonical in, canonical out.
    assert review_unit_payload(oracle.review_units) == expected_units
    assert oracle_payload(oracle)["review_units"] == expected_units

    # And it is a real inventory afterwards, not just matching bytes: every
    # decision the reviewer recorded survives the committed form.
    entry = next(u for u in oracle.review_units if u.unit_id == "unit-wish-entry")
    assert entry.kind is ReviewUnitKind.ENTRY
    assert set(entry.leaf_ids) == {SPELL_LEAF, PROSE_LEAF}
    assert (
        ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None, (PROSE_SPAN,))
        in entry.expected_rules
    )
    assert entry.excluded_groups == REVIEW_UNITS[0].excluded_groups

    support = next(
        u for u in oracle.review_units if u.unit_id == "unit-support-section"
    )
    assert support.supporting_groups == REVIEW_UNITS[1].supporting_groups


def test_an_artifact_whose_expectation_has_no_home_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A passing parse is not semantic acceptance."""
    payload = _bounded_payload()
    payload["review_units"] = review_unit_payload(
        (
            _entry_unit(
                ExpectedRule(SPELL_KEY, "material-components", None, (SPELL_SPAN,))
            ),
        )
    )

    with pytest.raises(OracleLoadError) as exc:
        load_accepted_inputs(_write(tmp_path, payload))
    assert "the accepted review inventory is not coverage" in str(exc.value)


def test_an_artifact_whose_unit_accounts_for_nothing_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The accounting obligation reaches the committed form too."""
    payload = _bounded_payload()
    payload["review_units"] = review_unit_payload(
        (
            ReviewUnit(
                unit_id="unit-blank",
                kind=ReviewUnitKind.ENTRY,
                leaf_ids=(SPELL_LEAF,),
            ),
        )
    )

    with pytest.raises(OracleLoadError) as exc:
        load_accepted_inputs(_write(tmp_path, payload))
    assert "the accepted review inventory is not coverage" in str(exc.value)


def test_a_malformed_unit_is_refused_rather_than_coerced(tmp_path) -> None:  # type: ignore[no-untyped-def]
    payload = _bounded_payload()
    units = review_unit_payload(REVIEW_UNITS)
    units[0]["leaf_ids"] = [SPELL_LEAF, 7]
    payload["review_units"] = units

    with pytest.raises(OracleLoadError):
        load_accepted_inputs(_write(tmp_path, payload))


def test_an_artifact_stating_a_unit_no_action_accepted_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The widened-inventory refusal at the committed form.

    Adding a unit to a reviewed file is the cheap forgery this check exists for:
    the acceptance records name what a reviewer actually accepted, and a unit
    outside them inherits nothing.
    """
    payload = _bounded_payload()
    _accepted_by(payload, REVIEW_UNITS)
    payload["review_units"] = review_unit_payload(REVIEW_UNITS)
    records = payload["acceptance"]["review_unit_records"]  # type: ignore[index]
    payload["acceptance"]["review_unit_records"] = [  # type: ignore[index]
        r for r in records if r["unit_id"] != "unit-support-section"
    ]

    with pytest.raises(OracleLoadError) as exc:
        load_accepted_inputs(_write(tmp_path, payload))
    assert "no acceptance action records accepting them" in str(exc.value)


def test_the_committed_bounded_artifact_claims_no_unit() -> None:
    """The fixture is deliberately still an old-style complete partition.

    Every negative control above attaches an inventory explicitly, so nothing
    here depends on the committed file having one — and the file keeps proving
    that an artifact without units loads and identifies unchanged.
    """
    assert load_accepted_inputs(BOUNDED_ORACLE_PATH).oracle.review_units == ()
