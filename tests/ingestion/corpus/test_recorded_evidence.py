"""The canonical evidence-report schema as one typed object — Issue 5c, PR #142.

Four rounds of hand-maintained validation each shut one hole and left the next,
because the builder held the real shape in a dict literal and the validator held
a second, partial description of it. These tests exercise the replacement: one
typed model that *is* the `5c-evidence-3` payload.

Two boundaries, tested separately:

* **intrinsic** — what the document must be on its own: shape, types, closed
  populations, value domains, and the cross-field semantics of a successful
  verdict. Owned by :mod:`report_schema` and covered here;
* **contextual** — whether the document agrees with the release it describes.
  Owned by ``verify_published_release`` and covered by the mechanical
  bound-release controls, which drive it through real publication.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.models import LeafType
from afterworlds.ingestion.corpus.pdf_source import extraction_config
from afterworlds.ingestion.corpus.report import (
    CANONICAL_CANARY_NAMES,
    EVIDENCE_REPORT_SCHEMA_VERSION,
    parse_recorded_report,
    recorded_success_violations,
)
from afterworlds.ingestion.corpus.report_schema import CorpusEvidenceReport
from afterworlds.ingestion.corpus.transform_identity import transform_identity
from afterworlds.models.retrieval import rules_corpus_vector_identity


def payload(**overrides: Any) -> dict[str, Any]:
    """An honest successful report payload, with *overrides* applied.

    Built from the real production identity builders and round-tripped through
    JSON, so it is the shape a stored report actually has — not a hand-written
    approximation that could drift from what ``build_report`` emits.
    """
    identity = transform_identity()
    base: dict[str, Any] = {
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        "authoritative_source_hash": "a" * 64,
        "transform_config_hash": "b" * 64,
        "bundle_root_hash": "c" * 64,
        "frozen_source_ledger_hash": "d" * 64,
        "persisted_corpus_digest": "e" * 64,
        "transform_identity": {"extractor": extraction_config(), **identity},
        "rules_corpus_vector_identity": rules_corpus_vector_identity("model-x"),
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
    stored: dict[str, Any] = json.loads(json.dumps(base))
    stored.update(overrides)
    return stored


def at(path: str, value: object) -> dict[str, Any]:
    """A payload with one dotted *path* replaced."""
    document = payload()
    target: Any = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    return document


# ---------------------------------------------------------------------------
# Positive controls
# ---------------------------------------------------------------------------


def test_an_honest_successful_report_parses_and_passes() -> None:
    parsed, violations = parse_recorded_report(payload())
    assert violations == ()
    assert parsed is not None
    assert parsed.success_violations() == ()
    assert recorded_success_violations(payload()) == ()


def test_the_typed_dump_round_trips_exactly() -> None:
    """One serialization: what parses out is what would be hashed and stored."""
    parsed, _ = parse_recorded_report(payload())
    assert parsed is not None
    assert parsed.dump() == payload()


def test_the_canonical_canary_set_is_derived_not_restated() -> None:
    assert frozenset(c.name for c in VERSION_CANARIES) == CANONICAL_CANARY_NAMES
    assert len(CANONICAL_CANARY_NAMES) == 6


# ---------------------------------------------------------------------------
# The closed identity maps — the two fields wrongly classified as open
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param("transform_identity", {}, id="transform-identity-empty"),
        pytest.param("transform_identity", "deleted", id="transform-identity-scalar"),
        pytest.param("transform_identity", None, id="transform-identity-null"),
        pytest.param("transform_identity", [], id="transform-identity-array"),
        pytest.param("transform_identity.tool", 7, id="identity-scalar-wrong-type"),
        pytest.param("transform_identity.extractor", {}, id="extractor-empty"),
        pytest.param("transform_identity.extractor", None, id="extractor-null"),
        pytest.param(
            "transform_identity.extractor.tool_version",
            3,
            id="extractor-field-wrong-type",
        ),
        pytest.param(
            "transform_identity.source_manifest",
            [{"path": "x"}],
            id="manifest-entry-incomplete",
        ),
        pytest.param(
            "transform_identity.source_manifest",
            [{"path": "x", "sha256": "y", "extra": 1}],
            id="manifest-entry-extra-key",
        ),
        pytest.param(
            "transform_identity.source_manifest",
            [{"path": 1, "sha256": "y"}],
            id="manifest-entry-wrong-type",
        ),
        pytest.param(
            "transform_identity.source_manifest", "modules", id="manifest-as-string"
        ),
        pytest.param(
            "transform_identity.component_b_invocation",
            {"entrypoint": "x"},
            id="component-b-incomplete",
        ),
        pytest.param(
            "transform_identity.component_b_invocation.deterministic",
            "yes",
            id="component-b-wrong-type",
        ),
        pytest.param(
            "transform_identity.component_b_invocation.steps",
            "a0",
            id="component-b-steps-as-string",
        ),
        pytest.param("rules_corpus_vector_identity", {}, id="vector-identity-empty"),
        pytest.param("rules_corpus_vector_identity", None, id="vector-identity-null"),
        pytest.param(
            "rules_corpus_vector_identity", "gone", id="vector-identity-scalar"
        ),
        pytest.param(
            "rules_corpus_vector_identity.metadata_fields",
            [1, 2],
            id="vector-fields-wrong-element-type",
        ),
        pytest.param(
            "rules_corpus_vector_identity.metadata_schema_version",
            "1",
            id="vector-schema-version-as-string",
        ),
    ],
)
def test_a_malformed_identity_map_fails_to_parse(path: str, value: object) -> None:
    """These are fixed production schemas, not content-populated maps.

    Calling them open let an edited-and-rehashed report replace canonical
    evidence with ``{}`` — the omission that ended the hand-maintained approach.
    """
    parsed, violations = parse_recorded_report(at(path, value))
    assert parsed is None
    assert violations


def test_an_extra_key_inside_a_closed_identity_map_fails() -> None:
    document = payload()
    document["transform_identity"]["smuggled"] = 1
    assert parse_recorded_report(document)[0] is None


# ---------------------------------------------------------------------------
# Variable-population maps: variable keys, never absent structure
# ---------------------------------------------------------------------------


VARIABLE_MAPS = (
    "source_ledger_leaf_totals",
    "represented_totals",
    "excluded_totals_by_reason",
)


@pytest.mark.parametrize("field", VARIABLE_MAPS)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="null"),
        pytest.param("none", id="string"),
        pytest.param([], id="array"),
        pytest.param(3, id="scalar"),
    ],
)
def test_a_variable_map_supplied_as_a_non_object_fails(
    field: str, value: object
) -> None:
    """ "Open" meant a variable key population, never absent structure."""
    assert parse_recorded_report(at(field, value))[0] is None


@pytest.mark.parametrize("field", VARIABLE_MAPS)
@pytest.mark.parametrize(
    "count",
    [
        pytest.param(True, id="boolean"),
        pytest.param(1.5, id="float"),
        pytest.param("1", id="string"),
        pytest.param(None, id="null"),
        pytest.param(-1, id="negative"),
        pytest.param({"nested": 1}, id="object"),
    ],
)
def test_a_variable_map_with_a_non_count_value_fails(field: str, count: object) -> None:
    key = "reason" if field == "excluded_totals_by_reason" else "paragraph"
    assert parse_recorded_report(at(field, {key: count}))[0] is None


@pytest.mark.parametrize("field", ["source_ledger_leaf_totals", "represented_totals"])
def test_a_leaf_total_outside_the_taxonomy_fails(field: str) -> None:
    """The key universe is derived from ``LeafType``, so it cannot be invented.

    Any *subset* is legitimate — a corpus with no tables reports no
    ``table_cell`` — but a name the taxonomy does not define is not a leaf type.
    """
    assert parse_recorded_report(at(field, {"invented_type": 1}))[0] is None
    every = {leaf_type.value: 1 for leaf_type in LeafType}
    assert parse_recorded_report(at(field, every))[0] is not None


def test_excluded_reason_keys_stay_free_strings() -> None:
    """Reason validity is contextual, against the reconstructed policy.

    Deriving the universe here would need the frozen policy at parse time and
    would create the second policy definition this refactor exists to avoid.
    """
    assert parse_recorded_report(at("excluded_totals_by_reason", {"any": 1}))[0]


# ---------------------------------------------------------------------------
# Top-level shape, counters, and the canary population
# ---------------------------------------------------------------------------


def test_an_unknown_top_level_field_fails() -> None:
    assert parse_recorded_report(payload(smuggled="value"))[0] is None


def test_a_missing_top_level_field_fails() -> None:
    document = payload()
    del document["findings"]
    assert parse_recorded_report(document)[0] is None


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param("unresolved_leaves", True, id="counter-boolean"),
        pytest.param("unresolved_leaves", "0", id="counter-string"),
        pytest.param("invalid_locators", 1.0, id="counter-float"),
        pytest.param("concordance_failures", None, id="counter-null"),
        pytest.param("declared_projection_count", -1, id="counter-negative"),
        pytest.param("accounting.inventoried_leaves", "10", id="accounting-string"),
        pytest.param("findings.gaps", True, id="finding-boolean"),
        pytest.param("report_version", "5c-evidence-2", id="obsolete-schema-version"),
        pytest.param("prepublication_validation_status", "maybe", id="bad-status"),
        pytest.param("reproduction_target", {}, id="reproduction-target-empty"),
        pytest.param(
            "reconciliation_policy_reference",
            {"policy_version": "v"},
            id="policy-reference-incomplete",
        ),
    ],
)
def test_a_wrongly_typed_or_domain_invalid_field_fails(
    path: str, value: object
) -> None:
    assert parse_recorded_report(at(path, value))[0] is None


@pytest.mark.parametrize(
    "canaries",
    [
        pytest.param({}, id="empty"),
        pytest.param({"invented": True}, id="invented-only"),
        pytest.param(
            dict.fromkeys(sorted(CANONICAL_CANARY_NAMES)[1:], True), id="missing-one"
        ),
        pytest.param(
            {**dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True), "invented": True},
            id="canonical-plus-invented",
        ),
        pytest.param(
            {**dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True), "exhaustion": "y"},
            id="non-boolean-value",
        ),
    ],
)
def test_a_non_canonical_canary_population_fails(canaries: dict[str, Any]) -> None:
    assert parse_recorded_report(payload(version_canaries=canaries))[0] is None


# ---------------------------------------------------------------------------
# The verdict, on a document that has already proven its shape
# ---------------------------------------------------------------------------


def test_a_failed_verdict_is_rejected_however_well_formed() -> None:
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
                    "inventoried_leaves": 99,
                    "represented_leaves": 8,
                    "excluded_leaves": 2,
                    "unresolved_leaves": 0,
                }
            },
            id="accounting-unbalanced",
        ),
    ],
)
def test_a_pass_verdict_over_contradictory_summaries_is_rejected(
    override: dict[str, Any],
) -> None:
    """A "pass" is not a licence to ignore the numbers underneath it."""
    assert recorded_success_violations(payload(**override)) != ()


def test_the_accounting_total_must_agree_with_the_top_level_count() -> None:
    contradictory = payload(
        unresolved_leaves=0,
        accounting={
            "inventoried_leaves": 10,
            "represented_leaves": 7,
            "excluded_leaves": 2,
            "unresolved_leaves": 1,
        },
    )
    assert any(
        "disagrees with the top-level" in v
        for v in recorded_success_violations(contradictory)
    )


@pytest.mark.parametrize(
    "value", [None, "report", 7, [], pytest.param({}, id="empty-object")]
)
def test_a_payload_that_is_not_this_report_is_rejected(value: object) -> None:
    parsed, violations = parse_recorded_report(value)
    assert parsed is None
    assert violations
    assert recorded_success_violations(value) != ()


def test_parsing_reports_violations_rather_than_raising() -> None:
    """A malformed stored report is an auditable finding, not an exception.

    Publication has to refuse it with a typed outcome, so the parse boundary
    never lets a ``ValidationError`` escape toward the caller.
    """
    parsed, violations = parse_recorded_report({"report_version": 1})
    assert parsed is None
    assert all(isinstance(v, str) for v in violations)
    with pytest.raises(Exception, match="validation error"):
        CorpusEvidenceReport.model_validate({"report_version": 1})
