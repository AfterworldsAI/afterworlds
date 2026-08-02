"""A recorded evidence report as a *successful* verdict — Issue 5c, PR #141 R3.

Identity is not sufficiency. A report edited to ``"fail"`` and rehashed keeps
its five proof identities intact and still hashes to its recorded hash, so a
downstream consumer that checks only identity accepts a release whose own
evidence records that publication did not succeed.

``recorded_success_violations`` is the one definition of what success looks like
in the report's own numbers. ``build_report`` derives
``prepublication_validation_status`` from the same predicate, so a contradictory
report cannot be *written* here either — these controls therefore describe an
edited or foreign payload, which is exactly the provenance a recorded report
has when it is read back.
"""

from __future__ import annotations

from typing import Any

import pytest

from afterworlds.ingestion.corpus.report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    REQUIRED_REPORT_KEYS,
    recorded_success_violations,
    verdict_violations,
)


def payload(**overrides: Any) -> dict[str, Any]:
    """An honest successful report payload, with *overrides* applied."""
    base: dict[str, Any] = {
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        "authoritative_source_hash": "a" * 64,
        "transform_config_hash": "b" * 64,
        "bundle_root_hash": "c" * 64,
        "frozen_source_ledger_hash": "d" * 64,
        "persisted_corpus_digest": "e" * 64,
        "transform_identity": {"extractor": {}},
        "rules_corpus_vector_identity": {"embedding_model_id": "m"},
        "reproduction_target": {"python_target": "3.12"},
        "reconciliation_policy_reference": {"policy_version": "v"},
        "source_ledger_leaf_totals": {"paragraph": 10},
        "represented_totals": {"paragraph": 8},
        "excluded_totals_by_reason": {"running_header_footer": 2},
        "unresolved_leaves": 0,
        "declared_projection_count": 8,
        "accounting": {
            "inventoried_leaves": 10,
            "represented_leaves": 8,
            "excluded_leaves": 2,
            "unresolved_leaves": 0,
        },
        "findings": {"gaps": 0, "overlaps": 0, "orphans": 0, "duplications": 0},
        "invalid_locators": 0,
        "concordance_failures": 0,
        "version_canaries": {"wish": True, "true-polymorph": True},
        "prepublication_validation_status": "pass",
    }
    base.update(overrides)
    return base


def test_the_fixture_matches_the_declared_report_shape() -> None:
    """Guards this module from drifting away from what build_report produces."""
    assert set(payload()) == REQUIRED_REPORT_KEYS


def test_an_honest_successful_report_is_accepted() -> None:
    assert recorded_success_violations(payload()) == ()
    assert verdict_violations(payload()) == ()


# ---------------------------------------------------------------------------
# The verdict itself
# ---------------------------------------------------------------------------


def test_a_failed_verdict_is_rejected_however_well_formed() -> None:
    """The control the finding names: status edited to 'fail', nothing else."""
    violations = recorded_success_violations(
        payload(prepublication_validation_status="fail")
    )
    assert any("not 'pass'" in v for v in violations)


@pytest.mark.parametrize(
    "override",
    [
        pytest.param({"unresolved_leaves": 3}, id="unresolved-leaves"),
        pytest.param({"invalid_locators": 1}, id="invalid-locators"),
        pytest.param({"concordance_failures": 2}, id="concordance-failures"),
        pytest.param(
            {"findings": {"gaps": 1, "overlaps": 0, "orphans": 0, "duplications": 0}},
            id="findings-gap",
        ),
        pytest.param(
            {"findings": {"gaps": 0, "overlaps": 2, "orphans": 0, "duplications": 0}},
            id="findings-overlap",
        ),
        pytest.param(
            {"findings": {"gaps": 0, "overlaps": 0, "orphans": 1, "duplications": 0}},
            id="findings-orphan",
        ),
        pytest.param(
            {"findings": {"gaps": 0, "overlaps": 0, "orphans": 0, "duplications": 4}},
            id="findings-duplication",
        ),
        pytest.param(
            {"version_canaries": {"wish": True, "true-polymorph": False}},
            id="failed-canary",
        ),
        pytest.param(
            {
                "accounting": {
                    "inventoried_leaves": 10,
                    "represented_leaves": 8,
                    "excluded_leaves": 2,
                    "unresolved_leaves": 5,
                }
            },
            id="accounting-unresolved",
        ),
        pytest.param(
            {
                "accounting": {
                    "inventoried_leaves": 99,
                    "represented_leaves": 8,
                    "excluded_leaves": 2,
                    "unresolved_leaves": 0,
                }
            },
            id="accounting-equation-unbalanced",
        ),
    ],
)
def test_a_pass_verdict_over_contradictory_summaries_is_rejected(
    override: dict[str, Any],
) -> None:
    """ "pass" is not a licence to ignore the numbers underneath it.

    Each payload keeps the status at ``"pass"`` and makes exactly one
    success-bearing summary say otherwise. A verdict that survives its own
    contradicting evidence is not a verdict.
    """
    assert recorded_success_violations(payload(**override)) != ()


def test_a_disagreeing_accounting_total_is_rejected() -> None:
    """The duplicated unresolved count must agree with the top-level one."""
    contradictory = payload(
        unresolved_leaves=0,
        accounting={
            "inventoried_leaves": 10,
            "represented_leaves": 7,
            "excluded_leaves": 2,
            "unresolved_leaves": 1,
        },
    )
    violations = recorded_success_violations(contradictory)
    assert any("disagrees with the top-level" in v for v in violations)


# ---------------------------------------------------------------------------
# Shape and type closure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "override",
    [
        pytest.param({"unresolved_leaves": "0"}, id="counter-as-string"),
        pytest.param({"unresolved_leaves": True}, id="counter-as-boolean"),
        pytest.param({"invalid_locators": None}, id="counter-as-null"),
        pytest.param({"findings": "none"}, id="findings-as-string"),
        pytest.param({"findings": {"gaps": "0"}}, id="finding-as-string"),
        pytest.param({"version_canaries": []}, id="canaries-as-array"),
        pytest.param({"version_canaries": {"wish": "yes"}}, id="canary-as-string"),
        pytest.param({"accounting": None}, id="accounting-as-null"),
        pytest.param(
            {"accounting": {"inventoried_leaves": 10}}, id="accounting-incomplete"
        ),
    ],
)
def test_a_wrongly_typed_verdict_field_is_rejected(override: dict[str, Any]) -> None:
    """A verdict cannot rest on a field whose type was never checked.

    ``True`` is called out separately: it is an ``int`` subclass, so a boolean
    would otherwise read as the count ``1`` and could satisfy an equation.
    """
    assert recorded_success_violations(payload(**override)) != ()


def test_a_missing_verdict_field_is_rejected() -> None:
    incomplete = payload()
    del incomplete["findings"]
    violations = recorded_success_violations(incomplete)
    assert any("missing" in v for v in violations)


@pytest.mark.parametrize(
    "value", [None, "report", 7, [], pytest.param({}, id="empty-object")]
)
def test_a_payload_that_is_not_this_report_is_rejected(value: object) -> None:
    assert recorded_success_violations(value) != ()


def test_an_obsolete_schema_version_is_rejected() -> None:
    violations = recorded_success_violations(payload(report_version="5c-evidence-2"))
    assert any("not the supported" in v for v in violations)
