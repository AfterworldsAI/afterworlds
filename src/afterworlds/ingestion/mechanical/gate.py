"""The exact completeness gate — CRD Issue 5d, Decisions 5 and 8.

Runs over **reconstructed persisted state**, never over the in-memory candidate
that produced it, and compares it against two independent authorities:

* the bound CRD Issue 5c release, for the represented-leaf population; and
* the committed accepted oracle (:mod:`oracle`), for the accepted semantics.

Neither is derived from the projection under test. That is the whole point: a
gate whose expectations come from the output it checks reports only that the
build is self-consistent.

The bound release is verified through CRD Issue 5c's versioned operational trust
seam before anything is read from it. A projection and an oracle can state the
same six-value binding and still describe a release that was never published
or whose authoritative rows were corrupted; agreement between two claims is
not authority.

**What this module does not re-implement.** The persisted-state proof
(:func:`verify_persisted_state`) and the candidate's internal honesty
(:func:`validate_candidate`) already exist and already run against reconstructed
state; the gate calls them and categorizes what they report. Its own new work
is exactly the part nothing else can do — comparing persisted state to
independent accepted authority:

* exact represented-leaf population equality against the bound release;
* exact accepted-classification equality against the oracle;
* exact element-level equality of records, components, facts, prose bindings,
  relationships, references, and provenance, as *multisets* — so a duplicated
  element is a distinct failure from an unexpected one, and neither can pad
  coverage;
* the accepted per-record obligations; and
* one semantic identity comparison that proves all of the above at once.

Counts appear only in :attr:`GateResult.diagnostics`, which the evidence report
carries as drift signal. No count is ever a pass condition: an all-prose
projection and a duplicated-fact projection both have plausible totals.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.corpus.operational import (
    OperationalCorpusVerificationError,
    load_verified_operational_corpus,
)
from afterworlds.ingestion.mechanical.accounting import span_payload
from afterworlds.ingestion.mechanical.bound_corpus import (
    bound_corpus_from_operational,
)
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle, oracle_identity
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    reconstruct_candidate,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
    representation_payload,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.representation import (
    FactFamily,
    RepresentationDraft,
    fact_payload,
)
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM

__all__ = [
    "GateFailure",
    "GateFailureCategory",
    "GateResult",
    "ObligationOutcome",
    "PUBLISHABLE_STATUSES",
    "SUPPORTED_CORPUS_CONTRACT_VERSIONS",
    "run_publication_gate",
]

#: The only two statuses a projection may be gated in. Anything else is state
#: no publication path produces, so it is rejected rather than interpreted.
PUBLISHABLE_STATUSES = ("draft", "published")

#: Corpus-contract versions whose shape and semantics this 5d transformation
#: has explicitly reviewed. This is downstream-owned compatibility policy:
#: importing 5c's current producer version here would make a future 5c bump
#: silently compatible instead of failing closed pending 5d review.
SUPPORTED_CORPUS_CONTRACT_VERSIONS = frozenset({"5c-operational-1"})


class GateFailureCategory(StrEnum):
    """Why publication was refused.

    Categories exist so a failure is actionable and so the publication layer
    can map a result to a typed outcome without parsing prose. They are
    deliberately about *what kind of authority is wrong*, not about which
    function noticed.
    """

    #: No persisted header, an unreadable row set, a status outside
    #: PUBLISHABLE_STATUSES, or a missing/mismatched persisted-state digest.
    PERSISTED_STATE = "persisted_state"
    #: The 5c release the projection binds is not published and operationally
    #: trustworthy: absent, draft, incompatible, binding-mismatched, or no
    #: longer matching its direct authoritative SQLite digest.
    BOUND_RELEASE = "bound_release"
    #: The oracle was accepted over a different 5c release than the projection
    #: is bound to, so it judges nothing here.
    MISMATCHED_RELEASE = "mismatched_release"
    #: The oracle declares a different semantic policy than the projection.
    POLICY_MISMATCH = "policy_mismatch"
    #: Classified leaves are not exactly the bound release's REPRESENTED set.
    POPULATION_MISMATCH = "population_mismatch"
    #: The accepted span partition differs from the oracle's.
    CLASSIFICATION_MISMATCH = "classification_mismatch"
    #: A span is still unreviewed or only proposed.
    UNREVIEWED_RESIDUE = "unreviewed_residue"
    #: A span's classification is still UNRESOLVED.
    UNRESOLVED_RESIDUE = "unresolved_residue"
    #: Accepted authority the projection does not carry.
    MISSING_AUTHORITY = "missing_authority"
    #: Authority the projection carries that no accepted input declares.
    UNEXPECTED_AUTHORITY = "unexpected_authority"
    #: An accepted element repeated, inflating coverage without adding meaning.
    DUPLICATE_AUTHORITY = "duplicate_authority"
    #: An accepted per-record obligation is not satisfied.
    UNSATISFIED_OBLIGATION = "unsatisfied_obligation"
    #: The candidate is not internally honest (partition, acceptance evidence,
    #: handling, provenance closure, reference resolution).
    SEMANTIC_VALIDATION = "semantic_validation"
    #: Persisted state does not derive the identity the accepted authority does.
    IDENTITY_MISMATCH = "identity_mismatch"


@dataclass(frozen=True)
class GateFailure:
    """One categorized reason publication was refused."""

    category: GateFailureCategory
    detail: str


@dataclass(frozen=True)
class ObligationOutcome:
    """The result of one accepted per-record obligation.

    Recorded whether or not it was satisfied: the evidence report has to show
    which obligations were *met*, not only which failed, or a passing gate
    would be an assertion with no evidence behind it.
    """

    record_key: str
    satisfied: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class GateResult:
    """The complete, deterministic verdict for one persisted projection."""

    passed: bool
    projection_uuid: str
    oracle_identity: str
    failures: tuple[GateFailure, ...]
    obligations: tuple[ObligationOutcome, ...]
    #: Identity the accepted authority derives, and the one persisted state
    #: derives. Equal exactly when every meaning-bearing comparison above holds.
    expected_projection_uuid: str | None
    persisted_state_digest: str | None
    #: Regression canaries only — never a pass condition (ADR-005d Decision 5).
    diagnostics: dict[str, int]

    def categories(self) -> frozenset[GateFailureCategory]:
        """The distinct failure categories present."""
        return frozenset(f.category for f in self.failures)


def _fail(
    findings: list[GateFailure], category: GateFailureCategory, *details: str
) -> None:
    findings.extend(GateFailure(category, d) for d in details)


#: The three ways one collection can differ, in the categories used for the
#: representation. Spans get their own triple: a classification difference is
#: not "authority the projection carries", it is the accounting disagreeing.
_AUTHORITY_CATEGORIES = (
    GateFailureCategory.MISSING_AUTHORITY,
    GateFailureCategory.UNEXPECTED_AUTHORITY,
    GateFailureCategory.DUPLICATE_AUTHORITY,
)
_CLASSIFICATION_CATEGORIES = (
    GateFailureCategory.CLASSIFICATION_MISMATCH,
    GateFailureCategory.CLASSIFICATION_MISMATCH,
    GateFailureCategory.CLASSIFICATION_MISMATCH,
)


def _compare_elements(
    persisted: list[dict[str, object]],
    accepted: list[dict[str, object]],
    collection: str,
    findings: list[GateFailure],
    categories: tuple[
        GateFailureCategory, GateFailureCategory, GateFailureCategory
    ] = _AUTHORITY_CATEGORIES,
) -> None:
    """Compare one collection as a multiset of canonical element payloads.

    Multiset, not set: an element repeated in the projection but declared once
    is duplicate-as-coverage, which is a different defect from carrying
    something nobody accepted, and collapsing the two would let the first hide
    inside the second.

    Comparing whole canonical payloads means a change to any field of any
    element is caught, including fields added to the representation later —
    the same reason :mod:`canonical` orders by whole payload rather than by a
    hand-picked key.
    """
    missing, unexpected, duplicate = categories
    p_by_key = {canonical_bytes(e): e for e in persisted}
    a_by_key = {canonical_bytes(e): e for e in accepted}
    p_counts = Counter(canonical_bytes(e) for e in persisted)
    a_counts = Counter(canonical_bytes(e) for e in accepted)

    for key in sorted(a_counts.keys() - p_counts.keys()):
        _fail(
            findings,
            missing,
            f"{collection}: accepted element absent from persisted state: "
            f"{a_by_key[key]}",
        )
    for key in sorted(p_counts.keys() - a_counts.keys()):
        _fail(
            findings,
            unexpected,
            f"{collection}: persisted element outside accepted authority: "
            f"{p_by_key[key]}",
        )
    for key in sorted(p_counts.keys() & a_counts.keys()):
        if p_counts[key] > a_counts[key]:
            _fail(
                findings,
                duplicate,
                f"{collection}: accepted element persisted {p_counts[key]} times, "
                f"accepted {a_counts[key]}: {p_by_key[key]}",
            )
        elif p_counts[key] < a_counts[key]:
            _fail(
                findings,
                missing,
                f"{collection}: accepted element persisted {p_counts[key]} times, "
                f"accepted {a_counts[key]}: {a_by_key[key]}",
            )


def _comparable_collections(
    draft: RepresentationDraft,
) -> dict[str, list[dict[str, object]]]:
    """Flatten the representation into the collections the gate compares.

    Two departures from :func:`representation_payload`, which exists to derive
    identity and must not change:

    * **facts are their own collection**, keyed by their owning record and
      component. Nested inside a component, one fact persisted twice reads as a
      *different component* — reported as one missing and one unexpected
      element, which is precisely the duplicate-as-coverage inflation this gate
      has to name.
    * **components carry no facts**, so the same difference is not reported
      twice under two categories.
    """
    payload = representation_payload(draft)
    collections: dict[str, list[dict[str, object]]] = {}
    for key in (
        "records",
        "prose_bindings",
        "relationships",
        "references",
        "provenance",
    ):
        elements = payload[key]
        assert isinstance(elements, list)
        collections[key] = elements

    collections["components"] = canonical_order(
        {
            "record_key": c.record_key,
            "semantic_key": c.semantic_key,
            "handling": c.handling.value,
            "irreducibility_reason_code": c.irreducibility_reason_code,
        }
        for c in draft.components
    )
    collections["facts"] = canonical_order(
        {
            "record_key": c.record_key,
            "component_key": c.semantic_key,
            **fact_payload(f),
        }
        for c in draft.components
        for f in c.facts
    )
    return collections


def _check_obligations(
    candidate: ProjectionCandidate, oracle: AcceptedOracle
) -> tuple[ObligationOutcome, ...]:
    """Evaluate every accepted per-record obligation against persisted state.

    An obligation is satisfied only by the authority it names. A record covered
    by references, or re-described entirely as prose, satisfies nothing — which
    is how reference-only coverage and all-prose under-extraction fail here by
    name rather than as an anonymous element difference.

    Reads structured families and prose-bound handling the same way
    :func:`oracle.derive_obligations` does, which is what makes every obligation
    that survives loading one this evaluation can actually satisfy.
    """
    draft = candidate.representation
    records = {r.semantic_key: r for r in draft.records}
    components = {(c.record_key, c.semantic_key): c for c in draft.components}
    bound_prose = {(b.record_key, b.component_key) for b in draft.prose_bindings}

    families_by_record: dict[str, set[FactFamily]] = {}
    for component in draft.components:
        for fact in component.facts:
            family = getattr(fact, "FAMILY", None)
            if isinstance(family, FactFamily):
                families_by_record.setdefault(component.record_key, set()).add(family)

    outcomes: list[ObligationOutcome] = []
    for obligation in oracle.obligations:
        failures: list[str] = []
        record = records.get(obligation.record_key)
        if record is None:
            failures.append("accepted record absent from persisted state")
        elif record.kind is not obligation.kind:
            failures.append(
                f"record kind {record.kind.value!r}, accepted as "
                f"{obligation.kind.value!r}"
            )

        present = families_by_record.get(obligation.record_key, set())
        for family in sorted(obligation.structured_fact_families - present, key=str):
            failures.append(
                f"no {family.value} fact: accepted structured authority is not "
                "represented by typed facts"
            )

        for component_key in sorted(obligation.prose_bound_components):
            bound = components.get((obligation.record_key, component_key))
            if bound is None:
                failures.append(f"component {component_key!r} absent")
                continue
            if bound.handling is ComponentHandling.STRUCTURED:
                failures.append(
                    f"component {component_key!r} is structured, accepted as "
                    "prose-bound authority"
                )
            if (obligation.record_key, component_key) not in bound_prose:
                failures.append(
                    f"component {component_key!r} carries no exact governing prose"
                )

        outcomes.append(
            ObligationOutcome(
                record_key=obligation.record_key,
                satisfied=not failures,
                failures=tuple(failures),
            )
        )
    return tuple(outcomes)


def _accepted_identity(oracle: AcceptedOracle) -> str:
    """The projection identity the accepted authority alone derives.

    Built from the oracle's own binding, declared policy, accepted spans, and
    accepted representation — never from the persisted state it is compared
    with. Acceptance evidence is empty because it is not identity-bearing
    (:mod:`accounting`), so an oracle need not — and must not — restate how
    review happened in order to say what was accepted.
    """
    return identify_projection(
        ProjectionCandidate(
            binding=oracle.binding,
            classification=ClassificationLedger(
                package_uuid=oracle.binding.package_uuid,
                release_version=oracle.binding.release_version,
                policy_version=oracle.policy_version,
                policy_hash=oracle.policy_hash,
                spans=oracle.spans,
                batches=(),
                acceptances=(),
            ),
            representation=oracle.representation,
        )
    ).projection_uuid


def _failed(
    projection_uuid: str, oracle: AcceptedOracle, *failures: GateFailure
) -> GateResult:
    return GateResult(
        passed=False,
        projection_uuid=projection_uuid,
        oracle_identity=oracle_identity(oracle),
        failures=failures,
        obligations=(),
        expected_projection_uuid=None,
        persisted_state_digest=None,
        diagnostics={},
    )


def run_publication_gate(
    session: Session, projection_uuid: str, oracle: AcceptedOracle
) -> GateResult:
    """Judge one persisted projection against independent accepted authority.

    Read-only. It never writes, never activates, and never repairs: a caller
    that receives a failing result has exactly the state it had before.

    The bound release is read from the *persisted header*, and the corpus
    snapshot is resolved from that. A caller cannot supply the snapshot, so it
    cannot hand the gate a different release than the projection actually
    claims.
    """
    identity = oracle_identity(oracle)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == projection_uuid
        )
    ).scalar_one_or_none()
    if header is None:
        return _failed(
            projection_uuid,
            oracle,
            GateFailure(
                GateFailureCategory.PERSISTED_STATE,
                f"projection {projection_uuid}: no persisted header row",
            ),
        )
    if header.publication_status not in PUBLISHABLE_STATUSES:
        return _failed(
            projection_uuid,
            oracle,
            GateFailure(
                GateFailureCategory.PERSISTED_STATE,
                f"projection {projection_uuid}: publication_status "
                f"{header.publication_status!r} is outside "
                f"{list(PUBLISHABLE_STATUSES)}",
            ),
        )

    try:
        candidate = reconstruct_candidate(session, projection_uuid)
    except PersistedStateReconstructionError as exc:
        return _failed(
            projection_uuid,
            oracle,
            GateFailure(
                GateFailureCategory.PERSISTED_STATE,
                f"projection {projection_uuid}: persisted state does not "
                f"reconstruct: {exc}",
            ),
        )

    # 0. The 5c release itself, before anything derived from it is read. The
    #    binding comes from *reconstructed* state, never from the oracle, so
    #    this is the one comparison the candidate and the oracle cannot satisfy
    #    between themselves: a six-value binding both of them state is checked
    #    against the authoritative published release through 5c's versioned,
    #    direct SQLite seam. A release that fails here has no trustworthy
    #    represented-leaf population, so the gate stops before reading it.
    binding = candidate.binding
    try:
        operational_corpus = load_verified_operational_corpus(
            session,
            binding.package_uuid,
            release_version=binding.release_version,
            authoritative_source_hash=binding.authoritative_source_hash,
            transform_config_hash=binding.transform_config_hash,
            bundle_root_hash=binding.bundle_root_hash,
            persisted_corpus_digest=binding.persisted_corpus_digest,
            supported_contract_versions=SUPPORTED_CORPUS_CONTRACT_VERSIONS,
        )
    except OperationalCorpusVerificationError as exc:
        return _failed(
            projection_uuid,
            oracle,
            *(
                GateFailure(GateFailureCategory.BOUND_RELEASE, detail)
                for detail in exc.violations
            ),
        )

    findings: list[GateFailure] = []

    # 1. The persisted-state proof itself: tamper, omission, stale identity,
    #    corrupted derived IDs, and a recorded digest that no longer matches.
    _fail(
        findings,
        GateFailureCategory.PERSISTED_STATE,
        *verify_persisted_state(
            session, projection_uuid, expected_status=header.publication_status
        ),
    )
    if header.persisted_state_digest is None:
        _fail(
            findings,
            GateFailureCategory.PERSISTED_STATE,
            f"projection {projection_uuid}: no persisted-state digest recorded",
        )

    # 2. The oracle must be accepted over this exact release, under this exact
    #    policy. Comparing accepted semantics across either boundary would be
    #    judging one release's content by another's authority.
    if oracle.binding != binding:
        _fail(
            findings,
            GateFailureCategory.MISMATCHED_RELEASE,
            f"accepted oracle binds {oracle.binding.package_uuid}/"
            f"{oracle.binding.release_version} with source "
            f"{oracle.binding.authoritative_source_hash[:12]}…, projection binds "
            f"{binding.package_uuid}/{binding.release_version} with source "
            f"{binding.authoritative_source_hash[:12]}…",
        )
    ledger = candidate.classification
    if (oracle.policy_version, oracle.policy_hash) != (
        ledger.policy_version,
        ledger.policy_hash,
    ):
        _fail(
            findings,
            GateFailureCategory.POLICY_MISMATCH,
            f"accepted oracle declares semantic policy {oracle.policy_version!r}/"
            f"{oracle.policy_hash[:12]}…, projection declares "
            f"{ledger.policy_version!r}/{ledger.policy_hash[:12]}…",
        )

    # 3. Population equality against the bound 5c release — the one authority
    #    that is neither the oracle nor the candidate. This is what makes an
    #    incomplete production projection fail structurally: a projection that
    #    classified a handful of leaves is not "mostly complete", it simply is
    #    not the release's REPRESENTED population.
    corpus = bound_corpus_from_operational(operational_corpus)
    represented = set(corpus.leaf_lengths)
    classified = {s.leaf_id for s in ledger.spans}
    for leaf_id in sorted(represented - classified):
        _fail(
            findings,
            GateFailureCategory.POPULATION_MISMATCH,
            f"leaf {leaf_id}: represented by the bound 5c release, absent from the "
            "accepted classification",
        )
    for leaf_id in sorted(classified - represented):
        _fail(
            findings,
            GateFailureCategory.POPULATION_MISMATCH,
            f"leaf {leaf_id}: classified, but not a represented leaf of the bound "
            "5c release",
        )

    # 4. Residue. Classified explicitly rather than read out of the validator's
    #    findings below, because the publication outcome is typed on these two
    #    and a typed outcome must not depend on matching a message string.
    for span in ledger.spans:
        if span.disposition is SemanticDisposition.UNRESOLVED:
            _fail(
                findings,
                GateFailureCategory.UNRESOLVED_RESIDUE,
                f"span {span.span_id}: unresolved classification",
            )
        if span.review_state is not ReviewState.ACCEPTED:
            _fail(
                findings,
                GateFailureCategory.UNREVIEWED_RESIDUE,
                f"span {span.span_id}: review state {span.review_state.value}",
            )
    accepted_span_ids = {a.span_id for a in ledger.acceptances}
    for span in ledger.spans:
        if span.span_id not in accepted_span_ids:
            _fail(
                findings,
                GateFailureCategory.UNREVIEWED_RESIDUE,
                f"span {span.span_id}: no acceptance record",
            )

    # 5. Internal honesty of the reconstructed candidate — partition, closed
    #    reason codes, acceptance evidence, handling, provenance closure,
    #    reference resolution. Reused, not re-derived.
    #
    #    An unclassified leaf is reported twice: once above as a population
    #    mismatch, and once here as a leaf with no spans. That overlap is
    #    accepted deliberately. Suppressing either would mean the gate holding
    #    an opinion about which findings the candidate validator is allowed to
    #    report, which is how two validators start disagreeing about what
    #    "covered" means.
    _fail(
        findings,
        GateFailureCategory.SEMANTIC_VALIDATION,
        *validate_candidate(candidate, corpus),
    )

    # 6. Exact equality against accepted authority, element by element.
    _compare_elements(
        span_payload(ledger.spans),
        span_payload(oracle.spans),
        "spans",
        findings,
        _CLASSIFICATION_CATEGORIES,
    )
    persisted_collections = _comparable_collections(candidate.representation)
    accepted_collections = _comparable_collections(oracle.representation)
    for key in sorted(persisted_collections):
        _compare_elements(
            persisted_collections[key], accepted_collections[key], key, findings
        )

    # 7. Accepted per-record obligations.
    obligations = _check_obligations(candidate, oracle)
    for outcome in obligations:
        _fail(
            findings,
            GateFailureCategory.UNSATISFIED_OBLIGATION,
            *(f"record {outcome.record_key}: {f}" for f in outcome.failures),
        )

    # 8. One identity comparison that proves 2, 3, and 6 together. The
    #    element diffs above say *what* differs; this says whether the
    #    projection is the accepted authority at all.
    expected_uuid = _accepted_identity(oracle)
    if expected_uuid != projection_uuid:
        _fail(
            findings,
            GateFailureCategory.IDENTITY_MISMATCH,
            f"accepted authority derives projection {expected_uuid}, persisted "
            f"state is {projection_uuid}",
        )

    draft = candidate.representation
    diagnostics = {
        "represented_leaves": len(represented),
        "classified_leaves": len(classified),
        "accepted_spans": len(ledger.spans),
        "records": len(draft.records),
        "components": len(draft.components),
        "facts": sum(len(c.facts) for c in draft.components),
        "prose_bindings": len(draft.prose_bindings),
        "relationships": len(draft.relationships),
        "references": len(draft.references),
        "provenance_edges": len(draft.provenance),
        "obligations": len(obligations),
    }

    return GateResult(
        passed=not findings,
        projection_uuid=projection_uuid,
        oracle_identity=identity,
        failures=tuple(findings),
        obligations=obligations,
        expected_projection_uuid=expected_uuid,
        persisted_state_digest=header.persisted_state_digest,
        diagnostics=diagnostics,
    )
