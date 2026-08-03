"""The canonical evidence report as a structurally immutable value — Issue 5c.

Two properties, proven separately.

**It cannot be changed after it is parsed.** Two earlier representations were
*conventionally* frozen and both were defeated by writing underneath the guard:
a frozen Pydantic ``BaseModel`` through ``vars(report)[...] = {}``, and a frozen
**slotted** dataclass through ``object.__setattr__(report, ...)``. The controls
here run both attacks — plus every container mutation the earlier rounds
surfaced — at the root and at every nested canonical value, and assert the
payload, the verdict, and the hash are unchanged afterwards. They fail because
the storage cannot be written, not because something later revalidates.

**It is not a document until one parser says so.** Identity is not sufficiency:
a report edited to ``"fail"`` and rehashed keeps its five proof identities and
still hashes to its recorded hash. ``success_violations`` is the one definition
of success in the report's own numbers; ``build_report`` derives
``prepublication_validation_status`` from the same predicate, so a contradictory
report cannot be *written* — these controls describe an edited or foreign
payload, which is exactly the provenance a recorded report has when read back.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest
from pydantic import ValidationError

from afterworlds.ingestion.corpus import report as report_module
from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.hashing import canonical_bytes, hash_obj, sha256_hex
from afterworlds.ingestion.corpus.models import (
    LeafType,
    ReconciliationFindings,
    ReconciliationMember,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import extraction_config
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY
from afterworlds.ingestion.corpus.report import (
    REPORT_PROOF_COLUMNS,
    recorded_success_violations,
    report_hash,
    state_derived_fields,
)
from afterworlds.ingestion.corpus.report_schema import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    PYTHON_TARGET,
    CorpusEvidenceReport,
    Pairs,
    canonical_report,
    parse_recorded_report,
)
from afterworlds.ingestion.corpus.transform_identity import transform_identity
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig


def payload(**overrides: Any) -> dict[str, Any]:
    """An honest successful report payload, with *overrides* applied.

    Built from the production identity builders rather than hand-written stubs.
    A fixture that cannot survive the checks it is used to test is not evidence
    of anything — every hand-written stand-in this suite has carried turned out
    to be exactly that.
    """
    base: dict[str, Any] = {
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        "authoritative_source_hash": "a" * 64,
        "transform_config_hash": "b" * 64,
        "bundle_root_hash": "c" * 64,
        "frozen_source_ledger_hash": "d" * 64,
        "persisted_corpus_digest": "e" * 64,
        "transform_identity": {
            "extractor": extraction_config(),
            **transform_identity(),
        },
        "rules_corpus_vector_identity": rules_corpus_vector_identity(
            RetrievalMemoryConfig().embedding_model_id
        ),
        "reproduction_target": {"python_target": PYTHON_TARGET},
        "reconciliation_policy_reference": {
            "policy_version": "v1",
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
        "version_canaries": {c.name: True for c in VERSION_CANARIES},
        "prepublication_validation_status": "pass",
    }
    base.update(overrides)
    return base


def parsed(**overrides: Any) -> CorpusEvidenceReport:
    return canonical_report(payload(**overrides))


def test_the_fixture_is_the_declared_shape() -> None:
    """Guards this module from drifting away from the canonical declaration."""
    assert set(payload()) == set(CorpusEvidenceReport._fields)


def test_an_honest_successful_report_is_accepted() -> None:
    assert recorded_success_violations(payload()) == ()
    assert parsed().verdict_violations() == ()
    assert parsed().success_violations() == ()


def test_a_stored_json_round_trip_parses_to_the_same_value() -> None:
    """A report read back out of a JSON column is the document it went in as."""
    assert canonical_report(json.loads(json.dumps(payload()))) == parsed()


# ---------------------------------------------------------------------------
# Structural immutability
# ---------------------------------------------------------------------------


def nested_values(report: CorpusEvidenceReport) -> dict[str, Any]:
    """Every canonical value in the tree, so no node is proven by proxy."""
    identity = report.transform_identity
    return {
        "transform_identity": identity,
        "transform_identity.extractor": identity.extractor,
        "transform_identity.source_manifest[0]": identity.source_manifest[0],
        "transform_identity.component_b_invocation": identity.component_b_invocation,
        "rules_corpus_vector_identity": report.rules_corpus_vector_identity,
        "reproduction_target": report.reproduction_target,
        "reconciliation_policy_reference": report.reconciliation_policy_reference,
        "accounting": report.accounting,
        "findings": report.findings,
        "report": report,
    }


@pytest.mark.parametrize("label", sorted(nested_values(parsed())))
def test_no_canonical_value_has_writable_backing_storage(label: str) -> None:
    """``vars()`` and the base setter both fail, at every node of the tree.

    ``object.__setattr__`` is the control that defeated the previous
    representation: a slotted dataclass has no ``__dict__``, but the inherited
    base setter still writes its slot storage. A ``NamedTuple`` has neither.
    """
    value = nested_values(parsed())[label]
    assert not hasattr(value, "__dict__")
    with pytest.raises(TypeError):
        vars(value)
    field = type(value)._fields[0]
    with pytest.raises(AttributeError):
        object.__setattr__(value, field, "forged")
    with pytest.raises(AttributeError):
        object.__setattr__(value, "novel_attribute", "forged")
    with pytest.raises(AttributeError):
        setattr(value, field, "forged")


def test_a_failed_mutation_leaves_the_payload_verdict_and_hash_unchanged() -> None:
    """The attack the previous round's finding named, and its consequences.

    ``object.__setattr__(report, "version_canaries", {})`` emptied the canary
    population, left ``success_violations()`` empty, and changed both the dump
    and the hash. It now raises — because there is no storage to write, not
    because something downstream revalidates.
    """
    report = parsed()
    before = report.dump()
    before_hash = report_hash(report)

    with pytest.raises(TypeError):
        vars(report)["version_canaries"] = {}
    with pytest.raises(AttributeError):
        object.__setattr__(report, "version_canaries", {})
    with pytest.raises(AttributeError):
        object.__setattr__(report, "accounting", None)
    with pytest.raises(AttributeError):
        object.__setattr__(report.findings, "gaps", 0)

    assert report.dump() == before
    assert report_hash(report) == before_hash
    assert report.success_violations() == ()


@pytest.mark.parametrize(
    "pick",
    [
        pytest.param(lambda r: r.version_canaries, id="canary-map"),
        pytest.param(lambda r: r.source_ledger_leaf_totals, id="totals-map"),
        pytest.param(lambda r: r.excluded_totals_by_reason, id="reason-map"),
        pytest.param(lambda r: r.transform_identity.source_manifest, id="manifest"),
        pytest.param(
            lambda r: r.transform_identity.component_b_invocation.steps, id="steps"
        ),
        pytest.param(
            lambda r: r.rules_corpus_vector_identity.metadata_fields, id="fields"
        ),
    ],
)
def test_no_container_in_the_tree_can_be_written(pick: Any) -> None:
    """Every map is a ``Pairs`` and every array a tuple — neither has a setter.

    A ``MappingProxyType`` would satisfy the first assertion and not the
    reachability question behind it: a proxy is a view onto a real dictionary
    that stays reachable through ``gc.get_referents``. There is no dictionary
    here to reach.
    """
    container = pick(parsed())
    assert isinstance(container, tuple)
    assert not isinstance(container, list | dict)
    with pytest.raises(TypeError):
        container[0] = "forged"
    with pytest.raises(AttributeError):
        container.append("forged")


def test_mutating_a_dump_cannot_reach_the_report() -> None:
    """``dump()`` renders a fresh document; it does not expose internal state."""
    report = parsed()
    dumped = report.dump()
    dumped["version_canaries"][VERSION_CANARIES[0].name] = False
    dumped["source_ledger_leaf_totals"]["paragraph"] = 99
    assert report.dump() == parsed().dump()
    assert report.success_violations() == ()


# ---------------------------------------------------------------------------
# One parser
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "bad"),
    [
        ("not-an-object", ["a", "list"]),
        ("a-string", "5c-evidence-3"),
        ("none", None),
        ("extra-key", payload(unexpected_field=1)),
        ("missing-key", {k: v for k, v in payload().items() if k != "accounting"}),
        ("wrong-scalar-type", payload(authoritative_source_hash=64)),
        ("true-for-a-count", payload(unresolved_leaves=True)),
        ("string-for-a-count", payload(unresolved_leaves="0")),
        ("float-for-a-count", payload(unresolved_leaves=0.0)),
        ("negative-count", payload(invalid_locators=-1)),
        ("nested-object-as-array", payload(accounting=[10, 8, 2, 0])),
        ("nested-extra-key", payload(findings={"gaps": 0, "zz": 1})),
        ("nested-missing-key", payload(findings={"gaps": 0})),
        ("map-as-array", payload(represented_totals=[["paragraph", 8]])),
        ("map-value-wrongly-typed", payload(represented_totals={"paragraph": "8"})),
        ("flag-map-value-wrongly-typed", payload(version_canaries={"wish": 1})),
        ("identity-replaced-wholesale", payload(transform_identity={})),
        ("vector-identity-replaced", payload(rules_corpus_vector_identity={})),
        ("unsupported-schema-version", payload(report_version="5c-evidence-2")),
        ("unknown-validation-status", payload(prepublication_validation_status="ok")),
    ],
)
def test_the_parser_refuses_anything_that_is_not_this_document(
    label: str, bad: Any
) -> None:
    report, violations = parse_recorded_report(bad)
    assert report is None
    assert violations
    # The construction-side counterpart raises on the same input: a build that
    # cannot describe itself is a defect now, not an auditable finding later.
    with pytest.raises(ValidationError):
        canonical_report(bad)


def test_a_positional_array_is_not_this_document() -> None:
    """Pydantic's native ``NamedTuple`` handling would otherwise accept one.

    The representation is a tuple tree, so without an explicit object-only guard
    at every node a stored report could arrive as a JSON *array* — positionally
    correct, structurally meaningless — and parse.
    """
    assert parse_recorded_report(list(payload().values()))[0] is None
    assert parse_recorded_report(payload(accounting=[10, 8, 2, 0]))[0] is None


# ---------------------------------------------------------------------------
# Closed populations and closed domains
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "canaries"),
    [
        ("empty", {}),
        ("one-missing", {c.name: True for c in VERSION_CANARIES[1:]}),
        ("one-extra", {**{c.name: True for c in VERSION_CANARIES}, "extra": True}),
        ("renamed", {f"{c.name}-x": True for c in VERSION_CANARIES}),
    ],
)
def test_the_canary_population_is_closed(label: str, canaries: dict[str, bool]) -> None:
    """Derived from the committed definitions, so it moves with them."""
    assert len(VERSION_CANARIES) > 1
    report, violations = parse_recorded_report(payload(version_canaries=canaries))
    assert report is None
    assert any("canonical population" in v for v in violations)


@pytest.mark.parametrize("field", ["source_ledger_leaf_totals", "represented_totals"])
def test_leaf_totals_may_not_name_types_outside_the_taxonomy(field: str) -> None:
    report, violations = parse_recorded_report(payload(**{field: {"not_a_leaf": 1}}))
    assert report is None
    assert any("outside the taxonomy" in v for v in violations)


def test_leaf_totals_may_be_any_subset_of_the_taxonomy() -> None:
    """A corpus with no tables legitimately reports no ``table_cell``."""
    assert canonical_report(payload(source_ledger_leaf_totals={}))
    every = {leaf.value: 1 for leaf in LeafType}
    assert canonical_report(
        payload(
            source_ledger_leaf_totals=every,
            represented_totals=every,
            excluded_totals_by_reason={},
            accounting={
                "inventoried_leaves": len(every),
                "represented_leaves": len(every),
                "excluded_leaves": 0,
                "unresolved_leaves": 0,
            },
        )
    )


def test_exclusion_reason_codes_stay_free_strings() -> None:
    """Reason validity is contextual: the frozen policy is not available here.

    Reaching for it at parse time would create a second policy definition.
    """
    assert canonical_report(payload(excluded_totals_by_reason={"anything": 1}))


# ---------------------------------------------------------------------------
# The reproduction target
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", ["99.0", "3.13", "", "3.12.1"])
def test_the_reproduction_target_is_bound_not_merely_declared(target: str) -> None:
    """An edited-and-rehashed report cannot record a false reproduction target.

    Bound on the field itself rather than compared somewhere downstream, so
    there is no path that reads the report without the binding having held.
    """
    report, violations = parse_recorded_report(
        payload(reproduction_target={"python_target": target})
    )
    assert report is None
    assert any("canonical reproduction target" in v for v in violations)


def test_the_reproduction_target_is_host_independent() -> None:
    assert parsed().reproduction_target.python_target == PYTHON_TARGET


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def test_a_failed_verdict_is_rejected_however_well_formed() -> None:
    """The original control: status edited to 'fail', nothing else touched."""
    violations = recorded_success_violations(
        payload(prepublication_validation_status="fail")
    )
    assert any("not 'pass'" in v for v in violations)


@pytest.mark.parametrize(
    ("label", "override"),
    [
        ("unresolved-leaves", {"unresolved_leaves": 3}),
        ("invalid-locators", {"invalid_locators": 1}),
        ("concordance-failures", {"concordance_failures": 2}),
        (
            "a-finding",
            {
                "findings": {
                    "gaps": 1,
                    "overlaps": 0,
                    "orphans": 0,
                    "duplications": 0,
                }
            },
        ),
        (
            "an-unbalanced-equation",
            {
                "accounting": {
                    "inventoried_leaves": 11,
                    "represented_leaves": 8,
                    "excluded_leaves": 2,
                    "unresolved_leaves": 0,
                }
            },
        ),
    ],
)
def test_a_report_claiming_success_over_contradictory_summaries_is_rejected(
    label: str, override: dict[str, Any]
) -> None:
    """Status "pass", numbers that say otherwise — the point of the check."""
    assert recorded_success_violations(payload(**override))


def test_a_failed_canary_is_not_a_successful_publication() -> None:
    canaries = {c.name: True for c in VERSION_CANARIES}
    canaries[VERSION_CANARIES[0].name] = False
    violations = recorded_success_violations(payload(version_canaries=canaries))
    assert any("did not pass" in v for v in violations)


def test_unresolved_leaves_inside_the_accounting_is_also_a_failure() -> None:
    """Both places the count appears are checked, not just the top-level one.

    Distinct from the disagreement control below: here the two agree, and the
    value they agree on is not zero.
    """
    violations = recorded_success_violations(
        payload(
            unresolved_leaves=2,
            accounting={
                "inventoried_leaves": 10,
                "represented_leaves": 6,
                "excluded_leaves": 2,
                "unresolved_leaves": 2,
            },
        )
    )
    assert any("accounting.unresolved_leaves is 2, not 0" in v for v in violations)


def test_accounting_must_agree_with_the_top_level_unresolved_count() -> None:
    violations = recorded_success_violations(
        payload(
            unresolved_leaves=1,
            accounting={
                "inventoried_leaves": 11,
                "represented_leaves": 8,
                "excluded_leaves": 2,
                "unresolved_leaves": 0,
            },
        )
    )
    assert any("disagrees with the top-level" in v for v in violations)


@pytest.mark.parametrize(
    "bad", [None, [], "text", {}, payload(accounting=None)], ids=str
)
def test_a_malformed_persisted_report_is_a_finding_not_an_exception(bad: Any) -> None:
    """Unknown provenance: a bad stored report is auditable, never a crash."""
    assert recorded_success_violations(bad)


# ---------------------------------------------------------------------------
# One serializer
# ---------------------------------------------------------------------------


def test_the_dump_round_trips_and_is_the_hashed_document() -> None:
    report = parsed()
    assert canonical_report(report.dump()) == report
    assert report_hash(report) == sha256_hex(canonical_bytes(report.dump()))


def test_serializing_the_value_directly_is_not_the_canonical_document() -> None:
    """The hazard this representation introduces, held down by a control.

    ``json.dumps`` raised ``TypeError`` on the previous dataclass. A
    ``NamedTuple`` serializes *successfully*, as a positional array — so an
    accidental ``canonical_bytes(report)`` would mint a wrong-but-plausible hash
    instead of failing. Every hash, column, and comparison goes through
    ``dump()``; this asserts the two cannot be confused.
    """
    report = parsed()
    assert canonical_bytes(report) != canonical_bytes(report.dump())
    assert json.loads(canonical_bytes(report)) == json.loads(
        json.dumps(list(report), default=list)
    )
    assert hash_obj(report) != report_hash(report)


def test_maps_serialize_as_objects_even_when_empty() -> None:
    """``Pairs`` is a type, not a heuristic over the pairs it happens to hold."""
    dumped = canonical_report(payload(excluded_totals_by_reason={})).dump()
    assert dumped["excluded_totals_by_reason"] == {}
    assert isinstance(dumped["excluded_totals_by_reason"], dict)


def test_arrays_serialize_as_arrays() -> None:
    dumped = parsed().dump()
    assert isinstance(dumped["transform_identity"]["source_manifest"], list)
    assert isinstance(
        dumped["transform_identity"]["component_b_invocation"]["steps"], list
    )


def test_every_report_field_has_an_owner_and_no_field_is_uncompared() -> None:
    """The completeness claim behind "one report-context verifier", as a test.

    ``report_state_violations`` is only the single definition of report-versus-
    state agreement if every field is actually routed somewhere. Nothing else
    fails if a field is added to the document and not to
    :func:`state_derived_fields` — it silently stops being compared, which is
    precisely how coherently rewritten summaries survived before.

    So the declaration is partitioned exactly three ways, with no remainder:
    recomputed from reconstructed state, compared against a release column, or
    on the explicit list of claims that are neither.
    """
    derived = set(
        state_derived_fields(
            ledger=SourceLedger(
                source_document="d",
                source_version="1",
                source_sha256="0" * 64,
                extraction_config={},
                containers=(),
                leaves=(),
            ),
            recon=ReconciliationMember(
                policy_version="v",
                policy_hash="0" * 64,
                dispositions=(),
                projections=(),
                findings=ReconciliationFindings((), (), (), (), ()),
                inventoried_leaves=0,
                represented_leaves=0,
                excluded_leaves=0,
                unresolved_leaves=0,
            ),
            policy=FROZEN_POLICY,
            transform_config={},
        )
    )
    identities = {key for key, _ in REPORT_PROOF_COLUMNS}
    #: Neither reconstructable from SQL nor a release column.
    #:
    #: - ``report_version``, ``reproduction_target`` and
    #:   ``prepublication_validation_status`` are intrinsic: the parser refuses
    #:   any other value, so there is nothing contextual left to compare.
    #: - ``invalid_locators``, ``concordance_failures`` and ``version_canaries``
    #:   are measured against the authoritative PDF, which SQL cannot reproduce.
    #:   They keep their recorded-successful-form treatment under the
    #:   2026-08-01 Owner Decision, and the paths holding pages re-run them.
    neither = {
        "report_version",
        "reproduction_target",
        "prepublication_validation_status",
        "invalid_locators",
        "concordance_failures",
        "version_canaries",
    }
    fields = set(CorpusEvidenceReport._fields)
    assert derived & identities == set()
    assert derived & neither == set()
    assert identities & neither == set()
    assert derived | identities | neither == fields


def test_the_evidence_report_name_is_the_canonical_class_not_a_wrapper() -> None:
    """``EvidenceReport`` survives as a name only — the same class object.

    A frozen ``EvidenceReport`` dataclass used to hold the canonical payload and
    *be* the hash-bearing authority, so ``object.__setattr__(report, "payload",
    forged)`` replaced the whole document after construction while the tuple
    tree inside stayed perfectly immutable. It protected the wrong thing.

    The name is retained because ``pipeline.py`` imports it and that module's
    source bytes are bound into the transform identity: retyping an annotation
    there would remint the package UUID and release version over a
    post-persistence plumbing edit. So this asserts the name resolves to the
    canonical class *itself* — not a subclass, not an adapter, nothing with a
    ``payload`` to substitute.
    """
    assert report_module.EvidenceReport is CorpusEvidenceReport
    assert not dataclasses.is_dataclass(report_module.EvidenceReport)
    assert not hasattr(report_module.EvidenceReport, "payload")
    assert not hasattr(report_module.EvidenceReport, "persisted")
    assert "payload" not in CorpusEvidenceReport._fields
    assert "persisted" not in CorpusEvidenceReport._fields
    # ``report_hash`` takes the canonical value; ``test_ledger_pipeline`` proves
    # ``build_report`` returns one, over a real release.
    assert report_hash(parsed()) == hash_obj(parsed().dump())


def test_the_original_wrapper_attack_has_no_field_to_target() -> None:
    """The exact escape from the previous round, run against the new design.

    ``object.__setattr__(completed_report, "payload", forged_payload)`` used to
    succeed and replace the document consumed by ``dump()``, ``report_hash()``,
    persistence, and the gate. It fails now for the strongest available reason:
    there is no ``payload`` field, on a type with no writable storage at all.
    """
    report = parsed()
    forged = parsed(declared_projection_count=99)
    before, before_hash = report.dump(), report_hash(report)

    with pytest.raises(AttributeError):
        object.__setattr__(report, "payload", forged)
    with pytest.raises(AttributeError):
        object.__setattr__(report, "persisted", False)

    assert report.dump() == before
    assert report_hash(report) == before_hash


def test_nothing_can_substitute_a_payload_between_construction_and_hashing() -> None:
    """The report handed to the hash is the one that was built.

    With a wrapper, "the report" and "the payload it carries" were two objects
    and only the inner one was safe. They are the same object now, so the only
    way to change what gets hashed is to change the canonical value — which
    every control above shows is impossible.
    """
    report = parsed()
    before = report_hash(report)
    forged = parsed(declared_projection_count=99)
    assert report_hash(forged) != before

    with pytest.raises(AttributeError):
        object.__setattr__(report, "declared_projection_count", 99)
    for field in CorpusEvidenceReport._fields:
        with pytest.raises(AttributeError):
            object.__setattr__(report, field, getattr(forged, field))
    assert report_hash(report) == before


def test_the_namedtuple_constructors_produce_new_values_never_edits() -> None:
    """``_replace`` and ``_make`` build separate objects; they change nothing.

    Worth stating because they are the two constructors a tuple tree adds. They
    are not the escape the mutation controls above are about — neither writes to
    an existing value — but a report they produce has bypassed the one parser
    and is therefore not a canonical document, which is why ``build_report``
    goes through ``canonical_report`` rather than constructing directly.
    """
    report = parsed()
    before, before_hash = report.dump(), hash_obj(report.dump())

    forged = report._replace(version_canaries=Pairs(()))
    remade = CorpusEvidenceReport._make(report)

    assert forged is not report
    assert remade == report
    assert report.dump() == before
    assert hash_obj(report.dump()) == before_hash
    assert report.success_violations() == ()
    # And such a value is not something the parser would have produced.
    assert parse_recorded_report(forged.dump())[0] is None


def test_a_parsed_map_is_pairs_and_a_parsed_array_is_a_plain_tuple() -> None:
    report = parsed()
    assert isinstance(report.version_canaries, Pairs)
    assert isinstance(report.transform_identity.source_manifest, tuple)
    assert not isinstance(report.transform_identity.source_manifest, Pairs)
