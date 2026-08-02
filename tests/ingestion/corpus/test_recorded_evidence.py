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

from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.report import (
    CANONICAL_CANARY_NAMES,
    EVIDENCE_REPORT_SCHEMA_VERSION,
    OPEN_REPORT_MAPS,
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
        "reconciliation_policy_reference": {
            "policy_version": "v",
            "policy_hash": "f" * 64,
            "applied_policy_hash": "f" * 64,
        },
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
        "version_canaries": dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True),
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
            {
                "version_canaries": {
                    **dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True),
                    "counterspell": False,
                }
            },
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
        pytest.param(
            {
                "version_canaries": {
                    **dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True),
                    "exhaustion": "yes",
                }
            },
            id="canary-as-string",
        ),
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


# ---------------------------------------------------------------------------
# Closed inventories: the exact population, not merely the entries present
# ---------------------------------------------------------------------------
#
# The omission this closes: iterating whatever a map happens to contain and
# requiring each entry to be valid says nothing about the entries that are
# *absent*. An empty map is vacuously "all passed".


def test_the_canonical_canary_set_is_derived_not_restated() -> None:
    """The required population follows the committed definitions.

    A second hand-written list of six names would drift the first time a canary
    is added or retired, and drift silently in the safe-looking direction.
    """
    assert frozenset(c.name for c in VERSION_CANARIES) == CANONICAL_CANARY_NAMES
    assert len(CANONICAL_CANARY_NAMES) == 6


@pytest.mark.parametrize(
    "canaries",
    [
        pytest.param({}, id="empty"),
        pytest.param({"invented": True}, id="invented-only"),
        pytest.param(
            {n: True for n in sorted(CANONICAL_CANARY_NAMES)[1:]},
            id="missing-one-canonical",
        ),
        pytest.param(
            {
                **dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True),
                "invented": True,
            },
            id="canonical-plus-invented",
        ),
    ],
)
def test_a_version_canary_population_that_is_not_canonical_is_rejected(
    canaries: dict[str, Any],
) -> None:
    assert recorded_success_violations(payload(version_canaries=canaries)) != ()


def test_the_exact_canonical_canary_population_passes() -> None:
    """The positive control, so the rule above is not simply "reject"."""
    exact = dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True)
    assert recorded_success_violations(payload(version_canaries=exact)) == ()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        pytest.param("findings", {"gaps": 0, "overlaps": 0}, id="findings-partial"),
        pytest.param(
            "findings",
            {
                "gaps": 0,
                "overlaps": 0,
                "orphans": 0,
                "duplications": 0,
                "invented": 0,
            },
            id="findings-extra",
        ),
        pytest.param(
            "accounting",
            {
                "inventoried_leaves": 10,
                "represented_leaves": 8,
                "excluded_leaves": 2,
                "unresolved_leaves": 0,
                "invented": 0,
            },
            id="accounting-extra",
        ),
        pytest.param(
            "reproduction_target",
            {"python_target": "3.12", "host": "ci"},
            id="repro-extra",
        ),
        pytest.param("reproduction_target", {}, id="repro-empty"),
        pytest.param(
            "reconciliation_policy_reference",
            {"policy_version": "v", "invented": 1},
            id="policy-reference-wrong-keys",
        ),
    ],
)
def test_a_closed_sibling_map_with_the_wrong_population_is_rejected(
    key: str, value: dict[str, Any]
) -> None:
    """Every closed inventory, not only the one the finding landed on."""
    assert recorded_success_violations(payload(**{key: value})) != ()


def test_an_unknown_top_level_key_is_rejected() -> None:
    """A rehashed payload cannot smuggle a field in under the same schema."""
    violations = recorded_success_violations(payload(smuggled="value"))
    assert any("unrecognised keys" in v for v in violations)


@pytest.mark.parametrize("key", sorted(OPEN_REPORT_MAPS))
def test_an_open_diagnostic_map_may_carry_content_derived_keys(key: str) -> None:
    """Open maps stay open: their keys come from the corpus, not from code.

    A release with no table cells legitimately has no ``table_cell`` total.
    Requiring an exact population here would be requiring a particular corpus,
    which is why the closed/open split is declared rather than assumed.
    """
    assert recorded_success_violations(payload(**{key: {"anything_at_all": 1}})) == ()


def test_build_report_refuses_to_claim_success_over_an_incomplete_canary_run() -> None:
    """The same omission existed on the writing side, and is closed with it.

    ``all(c.passed for c in ())`` is vacuously true, so a report built from a
    partial canary run would have recorded ``"pass"``. It cannot now.
    """
    partial = payload(
        version_canaries={n: True for n in sorted(CANONICAL_CANARY_NAMES)[:3]}
    )
    assert verdict_violations(partial) != ()
