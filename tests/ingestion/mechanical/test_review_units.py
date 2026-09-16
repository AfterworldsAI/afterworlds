"""Accepted review units — CRD Issue 5d (#137), Owner Decision of 2026-09-16.

A review unit records that a human read one coherent stretch of source and what
they require to be present afterwards. Three separable obligations are proven
here, and they fail in different places on purpose:

* the inventory **persists, reconstructs and identifies** — it is part of what
  the projection means, so it enters the projection identity and the
  persisted-state digest and a tampered row is caught;
* the inventory is **checked into the representation**, never read out of it —
  an expected rule with no home is a finding, while representation content no
  unit expected is not; and
* a leaf a unit covers is **relieved of the complete-partition rule and of
  nothing else** — overlap, bad bounds and derived-id errors are still reported
  on exactly that leaf.

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
    ExpectedRule,
    ReviewState,
    ReviewUnit,
    ReviewUnitKind,
    SemanticDisposition,
    SemanticSpan,
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
from afterworlds.persistence.orm.mechanical import (
    MechanicalReviewExpectationORM,
    MechanicalReviewUnitORM,
)
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
    PROSE_LEAF,
    REVIEW_UNITS,
    SPELL_KEY,
    SPELL_LEAF,
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


def _persist(session: Session, units: tuple[ReviewUnit, ...] = REVIEW_UNITS):  # type: ignore[no-untyped-def]
    identified = identify_projection(reviewed_candidate(units))
    persist_draft(session, identified, now=NOW)
    return identified


def _violations(
    units: tuple[ReviewUnit, ...], policy_version: str = POLICY_2
) -> list[str]:
    return review_unit_violations(units, build_representation(), policy_version)


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
        ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FAMILY),
        ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None),
    )
    assert entry.excluded_group_reasons == (
        "the spell-list heading above this entry is navigation, not a rule",
    )
    # The unit that claims nothing beyond its membership reconstructs as empty
    # tuples rather than as a missing unit.
    assert units["unit-support-section"].expected_rules == ()
    assert units["unit-support-section"].excluded_group_reasons == ()


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

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    prose_rule = next(
        r
        for u in rebuilt.review_units
        for r in u.expected_rules
        if r.component_key == OPEN_ENDED_KEY
    )
    assert prose_rule.fact_family is None


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


# ---------------------------------------------------------------------------
# The inventory as coverage evidence
# ---------------------------------------------------------------------------


def test_an_honest_inventory_is_not_a_finding() -> None:
    assert _violations(REVIEW_UNITS) == []
    assert validate_candidate(reviewed_candidate(), bound_corpus()) == ()


def test_an_expected_rule_with_no_component_is_reported() -> None:
    """The omission this inventory exists to catch."""
    unit = replace(
        REVIEW_UNITS[0],
        expected_rules=(ExpectedRule(SPELL_KEY, "material-components", None),),
    )
    (finding,) = _violations((unit,))
    assert "spell:wish/material-components has no component" in finding


def test_a_rule_accepted_as_prose_against_a_structured_component_is_reported() -> None:
    """A component silently resolved to structured has dropped the passage."""
    unit = replace(
        REVIEW_UNITS[0],
        expected_rules=(ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, None),),
    )
    (finding,) = _violations((unit,))
    assert "accepted as governing prose, but the component is structured" in finding


def test_a_rule_naming_a_family_the_component_lacks_is_reported() -> None:
    unit = replace(
        REVIEW_UNITS[0],
        expected_rules=(ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, "movement_cost"),),
    )
    (finding,) = _violations((unit,))
    assert "requires fact family 'movement_cost'" in finding


def test_a_family_this_build_does_not_declare_is_a_finding_not_a_crash() -> None:
    """An expectation is a claim about the source, not about this build.

    A reviewer may legitimately name a family no released build implements. That
    has to be reportable, because a build that could not read the claim could
    not tell anyone it went unmet.
    """
    unit = replace(
        REVIEW_UNITS[0],
        expected_rules=(ExpectedRule(SPELL_KEY, DESCRIPTOR_KEY, "not_a_family"),),
    )
    (finding,) = _violations((unit,))
    assert "requires fact family 'not_a_family'" in finding


def test_representation_content_no_unit_expected_is_not_a_violation() -> None:
    """A unit states what review found, not a census of what may be there."""
    bare = replace(REVIEW_UNITS[0], expected_rules=())
    assert _violations((bare,)) == []


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


@pytest.mark.parametrize("reason", ["", "   ", "\n"])
def test_an_excluded_group_with_a_blank_reason_is_reported(reason: str) -> None:
    unit = replace(REVIEW_UNITS[0], excluded_group_reasons=(reason,))
    assert any(
        "an excluded group states an empty reason" in f for f in _violations((unit,))
    )


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
        review_unit_violations((), build_representation(), "5d-semantic-policy-0") == []
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
    stray = replace(REVIEW_UNITS[1], leaf_ids=("leaf-not-in-this-release",))
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


def test_an_accepted_artifact_carries_its_review_inventory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    payload = _bounded_payload()
    payload["review_units"] = review_unit_payload(REVIEW_UNITS)
    oracle = load_accepted_inputs(_write(tmp_path, payload)).oracle

    # Compared canonically, because that is the form the file states: the
    # writer sorts units, their leaves and their expected rules, and the loader
    # reads back exactly what is written. Canonical in, canonical out.
    assert review_unit_payload(oracle.review_units) == payload["review_units"]
    assert oracle_payload(oracle)["review_units"] == payload["review_units"]

    # And it is a real inventory afterwards, not just matching bytes.
    entry = next(u for u in oracle.review_units if u.unit_id == "unit-wish-entry")
    assert entry.kind is ReviewUnitKind.ENTRY
    assert set(entry.leaf_ids) == {SPELL_LEAF, PROSE_LEAF}
    assert ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None) in entry.expected_rules


def test_an_artifact_whose_expectation_has_no_home_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A passing parse is not semantic acceptance."""
    unit = replace(
        REVIEW_UNITS[0],
        expected_rules=(ExpectedRule(SPELL_KEY, "material-components", None),),
    )
    payload = _bounded_payload()
    payload["review_units"] = review_unit_payload((unit,))

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


def test_the_committed_bounded_artifact_claims_no_unit() -> None:
    """The fixture is deliberately still an old-style complete partition.

    Every negative control above attaches an inventory explicitly, so nothing
    here depends on the committed file having one — and the file keeps proving
    that an artifact without units loads and identifies unchanged.
    """
    assert load_accepted_inputs(BOUNDED_ORACLE_PATH).oracle.review_units == ()
