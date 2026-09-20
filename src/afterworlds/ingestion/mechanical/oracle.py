"""Committed accepted authority — CRD Issue 5d, Decisions 4 and 5.

This module owns both halves of what a reviewer commits: the accepted
**oracle** the publication gate judges persisted state against, and the
accepted **inputs** the production build consumes, which are the oracle plus the
review evidence that accepted it (:class:`AcceptedInputs`).

The only property that makes the gate's comparison worth anything is
independence: an oracle derived from the projection it checks proves nothing but
that the code is self-consistent.

Independence is structural here, not a convention:

* this module imports no session, no ORM, and nothing from
  :mod:`persistence`, :mod:`raw_state`, or :mod:`gate`. There is no code path,
  public or private, that builds an ``AcceptedOracle`` from a persisted
  projection or from a :class:`ProjectionCandidate`.
  :func:`candidate_from_accepted_inputs` runs the *other* way — committed bytes
  become a candidate — and the oracle those bytes also carry is what later judges
  it;
* :func:`load_accepted_inputs` reads a committed JSON file and nothing else. Its
  whole input is bytes on disk that a reviewer accepted and a commit records; and
* the declared semantic policy comes from the *file*, never from the current
  :mod:`policy` constants. Reading current code here would let a policy change
  silently re-bless an oracle nobody re-reviewed — the exact self-attestation
  this file exists to prevent. When the frozen policy changes, every committed
  oracle fails its binding check until a reviewer re-accepts it. That is the
  intended cost.

**What the oracle does not carry.** The represented-leaf population is *not*
declared here. It is read from the bound CRD Issue 5c release, which is already
independent accepted authority with its own publication proof. Re-declaring
28,109 leaf ids in a committed file would add a second place to drift from 5c
without adding a second opinion.

**What is committed today.** ``oracles/`` holds accepted authority for the
production SRD 5.2.1 release covering CRD Issue 5d batches ``conditions-1``,
``hazards-1``, ``actions-1``, ``attitudes-1``, ``areas-of-effect-1``, ``cover-1``
and ``speed-1`` — 48 records and 594 spans — so that release resolves to a
committed oracle, but not to full-corpus authority: the corpus remains
incomplete. A projection over the
whole release therefore fails the gate as incomplete rather than as unjudged,
and nothing over it has been published or activated. Later content batches
extend that same artifact through the propose → review → accept workflow
(:mod:`proposal`, :mod:`acceptance`), which merges over prior accepted inputs
rather than replacing them; the machinery that judges the result lives here.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import (
    acceptance_evidence_payload,
    span_payload,
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ClassificationLedger,
    ComponentHandling,
    ExcludedGroup,
    ExpectedRule,
    ReferenceResolution,
    ReferenceResolutionAcceptance,
    ReviewState,
    ReviewUnit,
    ReviewUnitAcceptance,
    ReviewUnitKind,
    SemanticDiffEntry,
    SemanticDisposition,
    SemanticSpan,
    SupportingGroup,
)
from afterworlds.ingestion.mechanical.policy import (
    POLICY_TRANSITIONS,
    PolicyTransitionRecord,
    policy_meaning_violations,
    policy_transition_violations,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    applicability_payload_violations,
    representation_payload,
    review_unit_payload,
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    COMPONENT_WIDE_PROSE,
    RECURRENCE_KEYS,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ComponentOption,
    ConditionKind,
    CoverDegree,
    CreatureSize,
    DamageOutcome,
    FactFamily,
    FactQualifier,
    MalformedFactPayloadError,
    ObscurementState,
    ParticipantRole,
    Phase,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RecoveryTrigger,
    Recurrence,
    RecurrenceBoundary,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    RollActor,
    SizeComparison,
    SizeRelation,
    StateEffectKind,
    TimeUnit,
    TrackedQuantity,
    UnknownFactFamilyError,
    applicability_violations,
    build_casting_time_threshold,
    build_consumption_band,
    fact_from_payload,
    recurrence_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    BatchSchemaAnchor,
    SchemaLiftRecord,
    schema_binding_violations,
    succession_evidence_violations,
)

__all__ = [
    "ACCEPTED_ARTIFACT_KIND",
    "COMMITTED_ORACLE_DIR",
    "AcceptedInputs",
    "AcceptedOracle",
    "OracleLoadError",
    "RecordObligation",
    "accepted_inputs_payload",
    "candidate_from_accepted_inputs",
    "committed_inputs_for",
    "committed_oracle_for",
    "derive_obligations",
    "load_accepted_inputs",
    "load_oracle",
    "obligation_payload",
    "oracle_identity",
    "oracle_payload",
    "serialize_accepted_inputs",
]

#: Committed accepted authority, one JSON file per published 5c release.
COMMITTED_ORACLE_DIR = Path(__file__).resolve().parent / "oracles"

#: The discriminator a committed accepted-inputs artifact must declare. A
#: machine proposal declares something else and has a different shape besides
#: (:mod:`afterworlds.ingestion.mechanical.proposal`), so it cannot be loaded as
#: accepted authority by renaming it, moving it, or editing one field.
ACCEPTED_ARTIFACT_KIND = "accepted_authority"


class OracleLoadError(ValueError):
    """A committed oracle file that will not load as accepted authority.

    Raised rather than reported: an oracle that cannot be read is not a weaker
    oracle, it is no oracle, and a gate run against a half-parsed one would
    compare persisted state to a shape nobody accepted.
    """


@dataclass(frozen=True)
class RecordObligation:
    """What a reviewer accepted that one record must actually carry.

    Element-set equality already rejects a projection whose contents differ
    from the accepted inventory. Obligations exist because equality alone
    cannot say *why* a projection is wrong, and because they are the accepted
    claim in reviewable form: "this record is represented by structured
    authority of these families, and these components remain prose-bound".

    That shape is what makes two specific defects fail by name rather than as
    an anonymous set difference:

    * **all-prose under-extraction** — a record whose facts were dropped and
      re-described as prose fails ``structured_fact_families``; and
    * **reference-only coverage** — a record covered by references alone
      satisfies no obligation at all, because a reference is not a fact.

    ``prose_bound_components`` names components whose accepted handling is
    ``PROSE_BOUND`` or ``MIXED``; each must still carry exact governing prose.
    """

    record_key: str
    kind: RecordKind
    structured_fact_families: frozenset[FactFamily]
    prose_bound_components: frozenset[str]


@dataclass(frozen=True)
class AcceptedOracle:
    """The complete accepted authority one projection is judged against.

    ``binding`` is the exact 5c release the accepted semantics were reviewed
    over. A projection bound to any other release is judged by nothing and
    fails as mismatched rather than being compared anyway.
    """

    binding: ReleaseBinding
    policy_version: str
    policy_hash: str
    #: The closed representation contract this accepted authority was reviewed
    #: under. Committed alongside the semantics it governs, so an artifact
    #: cannot be replayed under a union that means something else.
    schema_version: str
    schema_hash: str
    spans: tuple[SemanticSpan, ...]
    representation: RepresentationDraft
    obligations: tuple[RecordObligation, ...]
    #: The accepted review inventory (ADR-005d Decision 2, as amended by the
    #: Owner Decision of 2026-09-16): which coherent sections, entries and
    #: tables a human reviewed, their exact leaf membership, and the rules that
    #: review found and requires to have a home.
    #:
    #: **Authored, unlike its neighbour.** ``obligations`` is *derived* —
    #: :func:`derive_obligations` is the single definition and
    #: :func:`load_oracle` refuses a committed file whose declared obligations
    #: are not exactly that derivation, because two hand-written derivations
    #: would eventually disagree. A review unit is the opposite by requirement:
    #: ADR-005d Decision 2 says expected entries and table rows "must be derived
    #: from the source and checked in review, not inferred from the output being
    #: tested". There is deliberately no ``derive_review_units``, and nothing
    #: here checks the inventory for equality against the representation — an
    #: expectation read back out of the thing it is meant to test could not
    #: catch an omission, which is the entire obligation.
    #:
    #: Empty for all seven accepted batches, and omitted from the payload when
    #: empty, so their recorded identities do not move.
    review_units: tuple[ReviewUnit, ...] = ()
    #: Reviewed destinations for accepted references that had none — the bounded
    #: capability the Owner Decision of 2026-09-19 authorizes, under ADR-005d
    #: Decision 7. See :mod:`reference_resolution` for what it is and is not.
    #:
    #: **Identity-bearing, and beside the representation rather than inside it.**
    #: A resolution changes what the accepted authority means, so
    #: :func:`oracle_identity` moves when one is recorded and the effective
    #: reference is what the build persists and the gate judges. It lives here
    #: and not in :class:`~.representation.RepresentationDraft` because it is a
    #: *decision about* accepted content, not accepted content: keeping it out
    #: means no representation schema succession is needed, ``schema_binding_
    #: violations`` never sees it, and every accepted batch's representation
    #: canonicalizes under schema 15 exactly as reviewed.
    #:
    #: Empty for all seven accepted batches and omitted from the payload when
    #: empty, on the same terms as :attr:`review_units` and for the same reason:
    #: their committed bytes and recorded identities do not move.
    reference_resolutions: tuple[ReferenceResolution, ...] = ()


@dataclass(frozen=True)
class AcceptedInputs:
    """One committed artifact: the accepted result *and* the review evidence.

    The two halves are deliberately separable. :attr:`oracle` is the accepted
    semantics the publication gate judges against, and it excludes evidence
    because review process is not identity-bearing. :attr:`batches` and
    :attr:`acceptances` are the auditable record of the explicit acceptance
    action — exact scope, full semantic diff, who accepted it and when — which
    the build carries into persistence so the gate can see that every span was
    actually acted on.

    Keeping them in one file means they cannot drift apart; keeping them in
    separate fields means the evidence cannot leak into identity.
    """

    oracle: AcceptedOracle
    batches: tuple[AcceptanceBatch, ...]
    acceptances: tuple[AcceptanceRecord, ...]
    #: The acceptance action that accepted each unit of :attr:`oracle`'s review
    #: inventory. Empty for the seven batches accepted before
    #: ``proficiency-destinations-1``, which recorded no inventory, and omitted
    #: from the written file when empty — so their committed bytes and recorded
    #: digests are exactly as reviewed. The two Proficiency batches are the
    #: first to record one: five units, four discharged by the destinations
    #: batch and one by ``proficiency-1``.
    review_unit_acceptances: tuple[ReviewUnitAcceptance, ...] = ()
    #: The representation schema each retained batch was *reviewed* under.
    #: Empty only for the legacy pre-schema-4 form, where absence has one
    #: possible meaning; see ``schema_lift.succession_evidence_violations``.
    schema_anchors: tuple[BatchSchemaAnchor, ...] = ()
    #: Schema successions this artifact was carried across, oldest first.
    #: Evidence, never identity: which contract an artifact was lifted through is
    #: migration process, and process does not remint a projection (#137
    #: acceptance criterion 11), so this sits beside the acceptance batches
    #: rather than inside :class:`AcceptedOracle`.
    lifts: tuple[SchemaLiftRecord, ...] = ()
    #: Semantic-policy successions this artifact was carried across, oldest
    #: first. Evidence on exactly the same terms as :attr:`lifts`, and kept in
    #: its own field rather than folded into them because a schema lift and a
    #: policy transition authorize different things: one says the accepted
    #: *representation* is byte-identical under a wider type contract, the
    #: other says the accepted *reason codes* still mean what they meant.
    policy_transitions: tuple[PolicyTransitionRecord, ...] = ()
    #: Who authorized each of :attr:`oracle`'s reference resolutions, under what
    #: authority, and when. The evidence half of the same split
    #: :attr:`review_unit_acceptances` makes: the decision is identity-bearing
    #: because it changes meaning, while the reviewer and timestamp that recorded
    #: it are audit metadata and must not remint a projection.
    reference_resolution_acceptances: tuple[ReferenceResolutionAcceptance, ...] = ()

    def classification(self) -> ClassificationLedger:
        """The complete accepted ledger, result and evidence together."""
        return ClassificationLedger(
            package_uuid=self.oracle.binding.package_uuid,
            release_version=self.oracle.binding.release_version,
            policy_version=self.oracle.policy_version,
            policy_hash=self.oracle.policy_hash,
            spans=self.oracle.spans,
            batches=self.batches,
            acceptances=self.acceptances,
            review_unit_acceptances=self.review_unit_acceptances,
        )


#: Handlings whose accepted meaning is carried, wholly or partly, by governing
#: prose — so the component must still resolve to exact prose.
_PROSE_BOUND_HANDLINGS = frozenset(
    {ComponentHandling.PROSE_BOUND, ComponentHandling.MIXED}
)


def derive_obligations(
    representation: RepresentationDraft,
) -> tuple[RecordObligation, ...]:
    """The exact obligations one accepted representation states, one per record.

    The single definition of "what this accepted authority claims about record
    R", used twice for one reason: :func:`load_oracle` requires a committed
    file's declared obligations to equal it exactly, and :mod:`gate` evaluates
    obligations against *persisted* state. Deriving the expectation in one place
    means an obligation that loads is an obligation the gate can actually
    satisfy — two hand-written derivations would eventually disagree and produce
    an oracle nothing can pass.

    Requiring equality does not make obligations redundant. The independence
    that matters is oracle-versus-projection, and it is untouched; what this
    forecloses is a committed file whose per-record claim silently understates
    or overstates the representation it ships with, which would let the gate
    report satisfied obligations that assert less than the accepted authority.
    """
    families: dict[str, set[FactFamily]] = {}
    prose: dict[str, set[str]] = {}
    for component in representation.components:
        for fact in component.all_facts():
            family = getattr(fact, "FAMILY", None)
            if isinstance(family, FactFamily):
                families.setdefault(component.record_key, set()).add(family)
        if component.handling in _PROSE_BOUND_HANDLINGS:
            prose.setdefault(component.record_key, set()).add(component.semantic_key)
    return tuple(
        RecordObligation(
            record_key=record.semantic_key,
            kind=record.kind,
            structured_fact_families=frozenset(families.get(record.semantic_key, ())),
            prose_bound_components=frozenset(prose.get(record.semantic_key, ())),
        )
        for record in representation.records
    )


def obligation_payload(obligation: RecordObligation) -> dict[str, object]:
    """Canonical payload of one accepted per-record obligation."""
    return {
        "record_key": obligation.record_key,
        "kind": obligation.kind.value,
        "structured_fact_families": sorted(
            f.value for f in obligation.structured_fact_families
        ),
        "prose_bound_components": sorted(obligation.prose_bound_components),
    }


def oracle_payload(oracle: AcceptedOracle) -> dict[str, object]:
    """Canonical payload of the accepted oracle.

    Reuses the projection's own payload builders for spans, representation and
    the review inventory, so "the oracle and the projection agree" is a
    comparison of one canonical form rather than of two hand-written
    serializations that could drift.

    ``review_units`` is emitted only when the artifact states one, the same
    omit-when-empty discipline ``lifts`` and ``policy_transitions`` follow in
    :func:`accepted_inputs_payload`, which composes this function — so this
    single branch keeps both the oracle identity and the committed accepted-
    inputs bytes of all seven batches exactly as they were reviewed.
    """
    payload: dict[str, object] = {
        "release_binding": {
            "package_uuid": oracle.binding.package_uuid,
            "release_version": oracle.binding.release_version,
            "authoritative_source_hash": oracle.binding.authoritative_source_hash,
            "transform_config_hash": oracle.binding.transform_config_hash,
            "bundle_root_hash": oracle.binding.bundle_root_hash,
            "persisted_corpus_digest": oracle.binding.persisted_corpus_digest,
        },
        "semantic_policy_version": oracle.policy_version,
        "semantic_policy_hash": oracle.policy_hash,
        "representation_schema": {
            "version": oracle.schema_version,
            "hash": oracle.schema_hash,
        },
        "spans": span_payload(oracle.spans),
        # Under the schema this ACCEPTED AUTHORITY declares, never the one the
        # build happens to implement. The two coincided until schema 4 existed,
        # which is why defaulting here was invisible: a schema-3 artifact loaded
        # by a schema-4 build would have been canonicalized under schema-4 keys
        # and silently re-identified — the same failure Owner Decision
        # 2026-08-20 addressed for components, reappearing at this seam.
        "representation": representation_payload(
            oracle.representation, schema_version=oracle.schema_version
        ),
        "obligations": canonical_order(
            obligation_payload(o) for o in oracle.obligations
        ),
    }
    if oracle.review_units:
        payload["review_units"] = review_unit_payload(oracle.review_units)
    if oracle.reference_resolutions:
        # Identity-bearing, and emitted on exactly the same omit-when-empty
        # terms: a reviewed destination changes what one accepted reference
        # means, so it belongs in the identity, and an artifact that states no
        # resolution says nothing about one.
        payload["reference_resolutions"] = reference_resolution_payload(
            oracle.reference_resolutions
        )
    return payload


def oracle_identity(oracle: AcceptedOracle) -> str:
    """Content-derived identity of the accepted oracle.

    Recorded in the evidence report and on the published projection, so an
    audit can name which accepted authority passed the gate — and detect a
    later oracle edit, because an edited oracle is a different identity.
    """
    return hash_obj(oracle_payload(oracle))


# ---------------------------------------------------------------------------
# Committed-file loading
# ---------------------------------------------------------------------------
#
# Strict throughout, in the same spirit as fact reconstruction: a missing key,
# an unknown enum value, or an extra key is rejected rather than defaulted.
# An oracle that silently accepts an unrecognised shape would let a typo widen
# what publication tolerates.


#: The six keys a release binding states on the wire. Named once because two
#: payloads carry one — the artifact's own binding and every reference
#: resolution's — and a loader that spelled the set twice is how a resolution
#: came to be admitted on two of the six (#137 round 13).
_RELEASE_BINDING_FIELDS: tuple[str, ...] = (
    "package_uuid",
    "release_version",
    "authoritative_source_hash",
    "transform_config_hash",
    "bundle_root_hash",
    "persisted_corpus_digest",
)


def _require(
    payload: object,
    keys: tuple[str, ...],
    where: str,
    optional: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Check a payload's key set exactly.

    ``optional`` names keys that may be absent *and* may be present. It is used
    only where absence is an unambiguous real state rather than lost content —
    a component with no applicability and no options is exactly a schema-1
    component. Everything else stays strict: an unknown key is still rejected,
    so a misspelling cannot enter as silently ignored.
    """
    if not isinstance(payload, dict):
        raise OracleLoadError(
            f"{where}: expected an object, got {type(payload).__name__}"
        )
    supplied = set(payload)
    if missing := sorted(set(keys) - supplied):
        raise OracleLoadError(f"{where}: missing {missing}")
    if extra := sorted(supplied - set(keys) - set(optional)):
        raise OracleLoadError(f"{where}: unexpected {extra}")
    return payload


def _string(value: object, where: str) -> str:
    """A JSON string, exactly. No coercion — ``0`` is not ``"0"``."""
    if type(value) is not str:
        raise OracleLoadError(
            f"{where}: expected a string, got {type(value).__name__} {value!r}"
        )
    return value


def _optional_string(value: object, where: str) -> str | None:
    """A JSON string or ``null``, for a declared ``str | None`` field."""
    return None if value is None else _string(value, where)


def _offset(value: object, where: str) -> int:
    """A non-negative JSON integer character offset.

    ``bool`` is rejected explicitly: it is an ``int`` subclass, so ``true``
    would otherwise load as the offset ``1``. Floats are rejected too — ``0.0``
    is not the integer the span contract declares.

    Negativity is a *type-domain* violation and belongs here. Ordering, gap-free
    coverage, and whether a span partitions its leaf belong to the semantic
    validator, which already owns partition validity; this boundary does not
    state a second opinion about it.
    """
    if type(value) is not int:
        raise OracleLoadError(
            f"{where}: expected an integer, got {type(value).__name__} {value!r}"
        )
    if value < 0:
        raise OracleLoadError(
            f"{where}: character offsets cannot be negative ({value})"
        )
    return value


def _list(value: object, where: str) -> list[Any]:
    """A JSON array, exactly. A string is not an array of its characters."""
    if not isinstance(value, list):
        raise OracleLoadError(
            f"{where}: expected an array, got {type(value).__name__} {value!r}"
        )
    return value


def _string_list(value: object, where: str) -> list[str]:
    """A JSON array of strings.

    Guards the constructors that would otherwise manufacture accepted authority
    out of a bare string: ``tuple("abc")`` and ``frozenset("abc")`` both succeed
    and silently invent three elements.
    """
    return [
        _string(item, f"{where}[{i}]") for i, item in enumerate(_list(value, where))
    ]


def _recurrence(raw: object, where: str) -> Recurrence | None:
    """Load one stored recurrence, or ``None``.

    Absent is the declared default: the canonical payload omits this key when
    the component states no recurrence, which is what keeps a schema-3 component
    byte-identical under schema 4. Present is held to the same typed invariants
    the build side uses.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: recurrence must be an object or null")
    # Both keys, exactly. The canonical payload emits ``whose`` unconditionally,
    # so a stored object without it is not "a recurrence with no actor" — it is a
    # shape the serializer never wrote, and reading it as an explicit null would
    # invent a claim the file does not make (#137 round 9).
    payload = _require(raw, tuple(sorted(RECURRENCE_KEYS)), where)
    built = Recurrence(
        boundary=_enum(RecurrenceBoundary, payload["boundary"], f"{where}.boundary"),
        whose=(
            None
            if payload["whose"] is None
            else _enum(RollActor, payload["whose"], f"{where}.whose")
        ),
    )
    if findings := recurrence_violations(built):
        raise OracleLoadError(f"{where}: {'; '.join(findings)}")
    return built


def _applicability(raw: object, where: str) -> Applicability | None:
    """Load one stored applicability, or ``None``.

    Delegates the shape contract to the same invariant checker the build side
    uses, so a payload the builder would have refused cannot enter through the
    loader instead.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: applicability must be an object or null")
    # The key set first: a misspelled or missing key never reaches the typed
    # invariants as the field it was meant to be, so it has to be refused
    # before anything is constructed.
    if shape := applicability_payload_violations(raw):
        raise OracleLoadError(f"{where}: {'; '.join(shape)}")
    # A disjunction's terms are whole applicabilities, so they are rebuilt by
    # this same loader: one statement of the shape, one layer's error type, and
    # a term that is not an object was already refused by the key-set gate.
    terms = []
    for index, raw_term in enumerate(raw.get("any_of_terms") or ()):
        at = f"{where}.any_of_terms[{index}]"
        term = _applicability(raw_term, at)
        if term is None:
            raise OracleLoadError(f"{at}: a disjunction term may not be null")
        terms.append(term)
    try:
        built = Applicability(
            kind=ApplicabilityKind(raw["kind"]),
            # Carried through exactly as stored, never coerced: ``bool("false")``
            # is ``True``, so coercion here would publish the opposite
            # applicability from what the malformed input states. The exact-type
            # rule is stated once, by the invariant checker below.
            negated=raw["negated"],
            quantity=(
                None if raw["quantity"] is None else TrackedQuantity(raw["quantity"])
            ),
            comparison=(
                None if raw["comparison"] is None else Comparison(raw["comparison"])
            ),
            value=raw["value"],
            any_of=tuple(
                SizeComparison(
                    category=(
                        None if c["category"] is None else CreatureSize(c["category"])
                    ),
                    relation=(
                        None if c["relation"] is None else SizeRelation(c["relation"])
                    ),
                    at_least=c["at_least"],
                    at_most=c["at_most"],
                    measured=ParticipantRole(c["measured"]),
                    reference=(
                        None
                        if c["reference"] is None
                        else ParticipantRole(c["reference"])
                    ),
                )
                for c in _object_list(raw["any_of"], f"{where}.any_of")
            ),
            trigger=(
                None if raw["trigger"] is None else RecoveryTrigger(raw["trigger"])
            ),
            phase=None if raw["phase"] is None else Phase(raw["phase"]),
            # The schema-4 operands. Read with ``.get`` because they are
            # post-schema-3 keys: the canonical payload omits one that carries
            # no meaning, so a legal schema-3 payload has no such key at all and
            # ``raw["outcome"]`` would fail on content that is entirely honest.
            # Dropping them instead — which is what this builder did before —
            # reconstructs an applicability whose required operand is absent, so
            # ``applicability_violations`` rejects the rebuilt value and the
            # artifact cannot load at all.
            outcome=(
                None if raw.get("outcome") is None else AutomaticOutcome(raw["outcome"])
            ),
            damage_outcome=(
                None
                if raw.get("damage_outcome") is None
                else DamageOutcome(raw["damage_outcome"])
            ),
            unit=None if raw.get("unit") is None else TimeUnit(raw["unit"]),
            # Schema 6's operands, read the same way and for the same reason.
            condition=(
                None
                if raw.get("condition") is None
                else ConditionKind(raw["condition"])
            ),
            effect_state=(
                None
                if raw.get("effect_state") is None
                else StateEffectKind(raw["effect_state"])
            ),
            obscurement=(
                None
                if raw.get("obscurement") is None
                else ObscurementState(raw["obscurement"])
            ),
            cover=None if raw.get("cover") is None else CoverDegree(raw["cover"]),
            any_of_terms=tuple(terms),
            band=(
                None
                if raw.get("band") is None
                else build_consumption_band(raw["band"], f"{where}.band")
            ),
            # Schema 7's threshold, read the same way and for the same
            # reason: the key is omitted when it carries no meaning, so a
            # payload written under any earlier contract has no such key
            # and dropping it would rebuild an applicability whose
            # required operand is absent.
            casting_time=(
                None
                if raw.get("casting_time") is None
                else build_casting_time_threshold(
                    raw["casting_time"], f"{where}.casting_time"
                )
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OracleLoadError(f"{where}: {exc}") from exc
    violations = applicability_violations(built)
    if violations:
        raise OracleLoadError(f"{where}: {'; '.join(violations)}")
    return built


def _component_option(raw: object, where: str) -> ComponentOption:
    """Load one option of an exhaustive actor choice."""
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: option must be an object")
    o = _require(raw, ("semantic_key", "facts"), where, optional=("applies_when",))
    try:
        facts = tuple(
            fact_from_payload(f) for f in _object_list(o["facts"], f"{where}.facts")
        )
    except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
        raise OracleLoadError(f"{where}: {exc}") from exc
    return ComponentOption(
        semantic_key=_string(o["semantic_key"], f"{where}.semantic_key"),
        facts=facts,
        applies_when=_applicability(o.get("applies_when"), f"{where}.applies_when"),
    )


def _fact_qualifier(raw: object, where: str) -> FactQualifier:
    """Load one fact's own condition.

    ``applies_when`` is required here, unlike on a component or an option: a
    qualifier whose condition is absent states nothing and would be a row of
    pure noise, where an absent component qualifier is the real, meaningful
    state "applies unconditionally".
    """
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: fact qualifier must be an object")
    q = _require(raw, ("fact_key", "applies_when"), where, optional=("option_key",))
    applies_when = _applicability(q["applies_when"], f"{where}.applies_when")
    if applies_when is None:
        raise OracleLoadError(f"{where}.applies_when: a fact qualifier states none")
    return FactQualifier(
        fact_key=_string(q["fact_key"], f"{where}.fact_key"),
        option_key=_string(q.get("option_key", ""), f"{where}.option_key"),
        applies_when=applies_when,
    )


def _object_list(value: object, where: str) -> list[dict[str, Any]]:
    """A JSON array of objects, checked before anything indexes an element."""
    items = _list(value, where)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise OracleLoadError(
                f"{where}[{i}]: expected an object, got {type(item).__name__} {item!r}"
            )
    return items


def _enum[E: StrEnum](enum_cls: type[E], value: object, where: str) -> E:
    """Read one closed enum out of a committed file, or reject the file.

    The stored value must be a plain string naming a declared member. No
    coercion: a number, a null, or a look-alike is a file a reviewer did not
    write in the accepted shape, and guessing what it meant would be this
    layer inventing accepted authority.
    """
    if type(value) is not str:
        raise OracleLoadError(
            f"{where}: expected a string {enum_cls.__name__}, got "
            f"{type(value).__name__} {value!r}"
        )
    try:
        return enum_cls(value)
    except ValueError:
        raise OracleLoadError(
            f"{where}: {value!r} is not a declared {enum_cls.__name__}"
        ) from None


def _span(payload: object, index: int) -> SemanticSpan:
    where = f"spans[{index}]"
    p = _require(
        payload,
        (
            "span_id",
            "leaf_id",
            "char_start",
            "char_end",
            "disposition",
            "non_mechanical_reason_code",
        ),
        where,
    )
    return SemanticSpan(
        span_id=_string(p["span_id"], f"{where}.span_id"),
        leaf_id=_string(p["leaf_id"], f"{where}.leaf_id"),
        char_start=_offset(p["char_start"], f"{where}.char_start"),
        char_end=_offset(p["char_end"], f"{where}.char_end"),
        disposition=_enum(SemanticDisposition, p["disposition"], where),
        # An oracle span is accepted authority by construction: an unaccepted
        # claim has no business in a committed oracle, so the review state is
        # not a field a file may set to something else.
        review_state=ReviewState.ACCEPTED,
        non_mechanical_reason_code=_optional_string(
            p["non_mechanical_reason_code"], f"{where}.non_mechanical_reason_code"
        ),
    )


def _representation(payload: object) -> RepresentationDraft:
    p = _require(
        payload,
        (
            "records",
            "components",
            "prose_bindings",
            "relationships",
            "references",
            "provenance",
        ),
        "representation",
    )

    records = []
    for i, raw in enumerate(_object_list(p["records"], "representation.records")):
        where = f"representation.records[{i}]"
        r = _require(raw, ("semantic_key", "kind", "parent_key"), where)
        records.append(
            RecordDraft(
                semantic_key=_string(r["semantic_key"], f"{where}.semantic_key"),
                kind=_enum(RecordKind, r["kind"], where),
                parent_key=_optional_string(r["parent_key"], f"{where}.parent_key"),
            )
        )

    components = []
    for i, raw in enumerate(_object_list(p["components"], "representation.components")):
        where = f"representation.components[{i}]"
        c = _require(
            raw,
            (
                "record_key",
                "semantic_key",
                "handling",
                "irreducibility_reason_code",
                "facts",
            ),
            where,
            optional=(
                "applies_when",
                "options",
                "fact_qualifiers",
                "recurs",
                # Schema 12, and absent from every payload written before it.
                # The canonical form omits it when the component states no
                # retention reason, so its absence has exactly one reading.
                "prose_retention_reason_code",
            ),
        )
        # The fact list is shape-checked here *before* delegation, because the
        # closed-union parser reads a mapping and a non-object element would
        # reach it as an unclassified AttributeError rather than this loader's
        # documented error. Family validation itself stays where it is owned.
        raw_facts = _object_list(c["facts"], f"{where}.facts")
        try:
            facts = tuple(fact_from_payload(f) for f in raw_facts)
        except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
            # Both halves of the closed union's rejection: a payload that will
            # not rebuild its declared family, and a family outside the union.
            # The second is a TypeError, so catching ValueError alone would let
            # an undeclared family escape as an unclassified crash.
            raise OracleLoadError(f"{where}: {exc}") from exc
        components.append(
            ComponentDraft(
                record_key=_string(c["record_key"], f"{where}.record_key"),
                semantic_key=_string(c["semantic_key"], f"{where}.semantic_key"),
                handling=_enum(ComponentHandling, c["handling"], where),
                irreducibility_reason_code=_optional_string(
                    c["irreducibility_reason_code"],
                    f"{where}.irreducibility_reason_code",
                ),
                facts=facts,
                # Optional, unlike the required keys above, and deliberately:
                # absence is an unambiguous real state — a component with no
                # applicability and no options is exactly a schema-1 component,
                # which remains valid schema-2 content. Nothing is hidden by
                # the leniency: ``projection_payload`` always emits both keys,
                # and the gate rebuilds and re-hashes the payload, so a key
                # dropped or misspelled anywhere upstream fails there rather
                # than loading as silently empty.
                recurs=_recurrence(c.get("recurs"), f"{where}.recurs"),
                prose_retention_reason_code=_optional_string(
                    c.get("prose_retention_reason_code"),
                    f"{where}.prose_retention_reason_code",
                ),
                applies_when=_applicability(
                    c.get("applies_when"), f"{where}.applies_when"
                ),
                options=tuple(
                    _component_option(o, f"{where}.options[{j}]")
                    for j, o in enumerate(
                        _object_list(c.get("options", []), f"{where}.options")
                    )
                ),
                fact_qualifiers=tuple(
                    _fact_qualifier(q, f"{where}.fact_qualifiers[{j}]")
                    for j, q in enumerate(
                        _object_list(
                            c.get("fact_qualifiers", []), f"{where}.fact_qualifiers"
                        )
                    )
                ),
            )
        )

    prose_bindings = []
    for i, raw in enumerate(
        _object_list(p["prose_bindings"], "representation.prose_bindings")
    ):
        where = f"representation.prose_bindings[{i}]"
        b = _require(
            raw,
            (
                "record_key",
                "component_key",
                "chunk_id",
                "span_id",
                "chunk_char_start",
                "chunk_char_end",
                # Required *as a key* under every contract, and nullable since
                # schema 12. A binding retained for a reducibility reason
                # writes ``null`` here rather than omitting the key, so
                # "retained for a different reason" and "written before this
                # distinction existed" never share a payload shape.
                "irreducibility_reason_code",
            ),
            where,
            # Schema 6 and schema 12 respectively, and each absent from every
            # payload written before it. The canonical form omits ``option_key``
            # when the binding governs the whole component and
            # ``prose_retention_reason_code`` when the binding states no
            # retention reason, so each absence has exactly one reading.
            optional=("option_key", "prose_retention_reason_code"),
        )
        prose_bindings.append(
            ProseBindingDraft(
                record_key=_string(b["record_key"], f"{where}.record_key"),
                component_key=_string(b["component_key"], f"{where}.component_key"),
                chunk_id=_string(b["chunk_id"], f"{where}.chunk_id"),
                span_id=_string(b["span_id"], f"{where}.span_id"),
                chunk_char_start=_offset(
                    b["chunk_char_start"], f"{where}.chunk_char_start"
                ),
                chunk_char_end=_offset(b["chunk_char_end"], f"{where}.chunk_char_end"),
                irreducibility_reason_code=_optional_string(
                    b["irreducibility_reason_code"],
                    f"{where}.irreducibility_reason_code",
                ),
                prose_retention_reason_code=_optional_string(
                    b.get("prose_retention_reason_code"),
                    f"{where}.prose_retention_reason_code",
                ),
                option_key=(
                    COMPONENT_WIDE_PROSE
                    if b.get("option_key") is None
                    else _string(b["option_key"], f"{where}.option_key")
                ),
            )
        )

    relationships = []
    for i, raw in enumerate(
        _object_list(p["relationships"], "representation.relationships")
    ):
        where = f"representation.relationships[{i}]"
        rel = _require(raw, ("source_record_key", "target_record_key", "kind"), where)
        relationships.append(
            RelationshipDraft(
                source_record_key=_string(
                    rel["source_record_key"], f"{where}.source_record_key"
                ),
                target_record_key=_string(
                    rel["target_record_key"], f"{where}.target_record_key"
                ),
                kind=_enum(RelationshipKind, rel["kind"], where),
            )
        )

    references = []
    reference_fields = (
        "from_record_key",
        "from_component_key",
        "source_text",
        "scope_key",
        "target_record_key",
    )
    for i, raw in enumerate(_object_list(p["references"], "representation.references")):
        where = f"representation.references[{i}]"
        ref = _require(raw, reference_fields, where)
        references.append(
            ReferenceDraft(
                **{k: _string(ref[k], f"{where}.{k}") for k in reference_fields}
            )
        )

    provenance = []
    for i, raw in enumerate(_object_list(p["provenance"], "representation.provenance")):
        where = f"representation.provenance[{i}]"
        pr = _require(raw, ("target_kind", "target_key", "span_id", "role"), where)
        provenance.append(
            ProvenanceClaim(
                target_kind=_enum(ProvenanceTargetKind, pr["target_kind"], where),
                target_key=tuple(_string_list(pr["target_key"], f"{where}.target_key")),
                span_id=_string(pr["span_id"], f"{where}.span_id"),
                role=_enum(ProvenanceRole, pr["role"], where),
            )
        )

    return RepresentationDraft(
        records=tuple(records),
        components=tuple(components),
        prose_bindings=tuple(prose_bindings),
        relationships=tuple(relationships),
        references=tuple(references),
        provenance=tuple(provenance),
    )


def _obligation(payload: object, index: int) -> RecordObligation:
    where = f"obligations[{index}]"
    o = _require(
        payload,
        ("record_key", "kind", "structured_fact_families", "prose_bound_components"),
        where,
    )
    return RecordObligation(
        record_key=_string(o["record_key"], f"{where}.record_key"),
        kind=_enum(RecordKind, o["kind"], where),
        structured_fact_families=frozenset(
            _enum(FactFamily, f, f"{where}.structured_fact_families")
            for f in _list(
                o["structured_fact_families"], f"{where}.structured_fact_families"
            )
        ),
        # A bare string here would become a frozenset of its characters, which
        # is accepted authority invented out of a typo.
        prose_bound_components=frozenset(
            _string_list(o["prose_bound_components"], f"{where}.prose_bound_components")
        ),
    )


def _expected_rule(payload: object, where: str) -> ExpectedRule:
    r = _require(
        payload,
        ("record_key", "component_key", "source_span_ids"),
        where,
        # Omitted when the reviewer accepted exact governing prose as the
        # rule's home, exactly as the canonical payload writes it.
        optional=("fact_family",),
    )
    return ExpectedRule(
        record_key=_string(r["record_key"], f"{where}.record_key"),
        component_key=_string(r["component_key"], f"{where}.component_key"),
        # Named by its wire value rather than parsed into ``FactFamily``: an
        # expectation is a claim about the source, and a reviewer may legitimately
        # expect a family this build does not implement — that is a finding for
        # ``review_unit_violations`` to report against the representation, not a
        # reason this file cannot be read at all.
        fact_family=(
            _string(r["fact_family"], f"{where}.fact_family")
            if "fact_family" in r
            else None
        ),
        # The exact accepted spans the rule was read from. Named rather than
        # derived: the whole point is that this came from a reviewer reading
        # source text, and anything this file could compute from the
        # representation would be the output vouching for itself.
        source_span_ids=tuple(
            _string_list(r["source_span_ids"], f"{where}.source_span_ids")
        ),
    )


def _supporting_group(payload: object, where: str) -> SupportingGroup:
    g = _require(
        payload,
        ("leaf_ids", "supports_record_key", "supports_component_key"),
        where,
    )
    return SupportingGroup(
        leaf_ids=tuple(_string_list(g["leaf_ids"], f"{where}.leaf_ids")),
        supports_record_key=_string(
            g["supports_record_key"], f"{where}.supports_record_key"
        ),
        # Empty when the group supports the record as a whole. Written rather
        # than omitted, unlike ``fact_family``, because "" is a real value here
        # and not a second way of saying nothing.
        supports_component_key=_string(
            g["supports_component_key"], f"{where}.supports_component_key"
        ),
    )


def _excluded_group(payload: object, where: str) -> ExcludedGroup:
    g = _require(payload, ("leaf_ids", "reason"), where)
    return ExcludedGroup(
        leaf_ids=tuple(_string_list(g["leaf_ids"], f"{where}.leaf_ids")),
        reason=_string(g["reason"], f"{where}.reason"),
    )


def _review_unit(
    payload: object, index: int, *, key: str = "review_units"
) -> ReviewUnit:
    # ``key`` only names the field in the error message. A proposal states its
    # inventory under ``proposed_review_units`` and an accepted artifact under
    # ``review_units``; a refusal that named the wrong one would send a reader
    # looking for a key their file does not have.
    where = f"{key}[{index}]"
    u = _require(
        payload,
        (
            "unit_id",
            "kind",
            "leaf_ids",
            "expected_rules",
            "supporting_groups",
            "excluded_groups",
        ),
        where,
    )
    return ReviewUnit(
        unit_id=_string(u["unit_id"], f"{where}.unit_id"),
        kind=_enum(ReviewUnitKind, u["kind"], f"{where}.kind"),
        leaf_ids=tuple(_string_list(u["leaf_ids"], f"{where}.leaf_ids")),
        expected_rules=tuple(
            _expected_rule(r, f"{where}.expected_rules[{i}]")
            for i, r in enumerate(
                _object_list(u["expected_rules"], f"{where}.expected_rules")
            )
        ),
        supporting_groups=tuple(
            _supporting_group(g, f"{where}.supporting_groups[{i}]")
            for i, g in enumerate(
                _object_list(u["supporting_groups"], f"{where}.supporting_groups")
            )
        ),
        excluded_groups=tuple(
            _excluded_group(g, f"{where}.excluded_groups[{i}]")
            for i, g in enumerate(
                _object_list(u["excluded_groups"], f"{where}.excluded_groups")
            )
        ),
    )


def _reference_resolution(payload: object, index: int) -> ReferenceResolution:
    """One reviewed reference resolution, as strictly as any other element.

    Strict on the same terms as its neighbours, and the strictness matters more
    here than almost anywhere: a defaulted coordinate would resolve a citation
    nobody reviewed, and a silently ignored misspelling would apply a decision
    to the wrong one.

    ``release_binding`` is required as a nested object stating all six
    coordinates. A payload written before this stated ``package_uuid`` and
    ``release_version`` loose beside the citation; it is refused as missing its
    binding rather than completed from the artifact that happens to hold it.
    Filling in the four absent coordinates from the surrounding file would be
    the defect itself: it would produce, on load, exactly the agreement the
    decision never proved (#137 round 13).
    """
    where = f"reference_resolutions[{index}]"
    r = _require(
        payload,
        (
            "resolution_id",
            "from_record_key",
            "from_component_key",
            "source_text",
            "scope_key",
            "target_record_key",
            "release_binding",
            "provenance_span_ids",
        ),
        where,
    )
    binding = _require(
        r["release_binding"], _RELEASE_BINDING_FIELDS, f"{where}.release_binding"
    )
    return ReferenceResolution(
        resolution_id=_string(r["resolution_id"], f"{where}.resolution_id"),
        from_record_key=_string(r["from_record_key"], f"{where}.from_record_key"),
        from_component_key=_string(
            r["from_component_key"], f"{where}.from_component_key"
        ),
        source_text=_string(r["source_text"], f"{where}.source_text"),
        scope_key=_string(r["scope_key"], f"{where}.scope_key"),
        target_record_key=_string(r["target_record_key"], f"{where}.target_record_key"),
        release_binding=ReleaseBinding(
            **{
                k: _string(binding[k], f"{where}.release_binding.{k}")
                for k in _RELEASE_BINDING_FIELDS
            }
        ),
        provenance_span_ids=tuple(
            _string_list(r["provenance_span_ids"], f"{where}.provenance_span_ids")
        ),
    )


def _check_obligations_closed(
    representation: RepresentationDraft,
    obligations: tuple[RecordObligation, ...],
    where: str,
) -> None:
    """Reject a committed oracle whose obligation relation is not total and exact.

    Shape validation cannot catch this. A file that parses perfectly but omits
    an obligation — or all of them — yields an oracle the gate evaluates against
    an emptier claim than the reviewer accepted, and an otherwise-matching
    projection then passes with less per-record evidence than ADR-005d
    Decision 5 requires. So the relation must be *closed*: exactly one
    obligation per accepted record, each reconciling exactly with what that
    record's accepted representation states.
    """
    accepted = {o.record_key: o for o in derive_obligations(representation)}
    seen: set[str] = set()
    for obligation in obligations:
        if obligation.record_key in seen:
            raise OracleLoadError(
                f"{where}: duplicate obligation for record "
                f"{obligation.record_key!r}"
            )
        seen.add(obligation.record_key)
        expected = accepted.get(obligation.record_key)
        if expected is None:
            raise OracleLoadError(
                f"{where}: obligation targets record {obligation.record_key!r}, "
                "which the accepted representation does not declare"
            )
        if obligation != expected:
            raise OracleLoadError(
                f"{where}: obligation for record {obligation.record_key!r} does "
                f"not reconcile with the accepted representation: declared "
                f"{obligation_payload(obligation)}, accepted "
                f"{obligation_payload(expected)}"
            )
    if uncovered := sorted(set(accepted) - seen):
        raise OracleLoadError(
            f"{where}: accepted records carry no obligation: {uncovered}"
        )


# ---------------------------------------------------------------------------
# Acceptance evidence and the committed accepted-inputs artifact
# ---------------------------------------------------------------------------
#
# **Why one artifact and not two.** #137 contract 4 names five committed
# meaning-bearing inputs the production build consumes; the oracle carries four
# of them but deliberately omits the fifth, acceptance evidence, because review
# process is not identity-bearing (:mod:`accounting`). Something still has to
# supply that evidence to the build, or the gate reports UNREVIEWED_RESIDUE
# against reconstructed state that no committed input could have filled in.
#
# Two files — build inputs and oracle — would need a third mechanism to prove
# they still describe the same accepted semantics. One file cannot disagree with
# itself, so the drift check has nothing to check and the whole class of
# input/oracle skew stops existing. The independence that actually matters is
# untouched: this is committed bytes a reviewer accepted, never something
# derived from a candidate or from persisted output, and the oracle projected
# out of it drops the evidence before identity is computed.


def _acceptance(payload: object, where: str) -> tuple[
    tuple[AcceptanceBatch, ...],
    tuple[AcceptanceRecord, ...],
    tuple[SchemaLiftRecord, ...],
    tuple[BatchSchemaAnchor, ...],
    tuple[PolicyTransitionRecord, ...],
    tuple[ReviewUnitAcceptance, ...],
    tuple[ReferenceResolutionAcceptance, ...],
]:
    """Load the review evidence half of a committed accepted-inputs file."""
    p = _require(
        payload,
        ("batches", "records"),
        where,
        optional=(
            "lifts",
            "schema_anchors",
            "policy_transitions",
            # Absent from all seven accepted batches on the same terms as the
            # inventory they accept: absent rather than empty, so their
            # committed bytes are exactly what was reviewed.
            "review_unit_records",
            # And absent on the same terms again: no accepted batch resolved a
            # reference, so none of them states who authorized one.
            "reference_resolution_records",
        ),
    )

    resolution_records = []
    for i, raw_decision in enumerate(
        _object_list(
            p.get("reference_resolution_records", []),
            f"{where}.reference_resolution_records",
        )
    ):
        at = f"{where}.reference_resolution_records[{i}]"
        entry = _require(
            raw_decision,
            (
                "resolution_id",
                "authorized_by",
                "authorization_reference",
                "reviewer",
                "resolved_at",
            ),
            at,
        )
        resolution_records.append(
            ReferenceResolutionAcceptance(
                resolution_id=_string(entry["resolution_id"], f"{at}.resolution_id"),
                authorized_by=_string(entry["authorized_by"], f"{at}.authorized_by"),
                authorization_reference=_string(
                    entry["authorization_reference"], f"{at}.authorization_reference"
                ),
                reviewer=_string(entry["reviewer"], f"{at}.reviewer"),
                resolved_at=_string(entry["resolved_at"], f"{at}.resolved_at"),
            )
        )

    unit_records = []
    for i, raw_unit in enumerate(
        _object_list(p.get("review_unit_records", []), f"{where}.review_unit_records")
    ):
        at = f"{where}.review_unit_records[{i}]"
        entry = _require(
            raw_unit, ("unit_id", "batch_id", "reviewer", "accepted_at"), at
        )
        unit_records.append(
            ReviewUnitAcceptance(
                unit_id=_string(entry["unit_id"], f"{at}.unit_id"),
                batch_id=_optional_string(entry["batch_id"], f"{at}.batch_id"),
                reviewer=_string(entry["reviewer"], f"{at}.reviewer"),
                accepted_at=_string(entry["accepted_at"], f"{at}.accepted_at"),
            )
        )

    anchors = []
    for i, raw_anchor in enumerate(
        _object_list(p.get("schema_anchors", []), f"{where}.schema_anchors")
    ):
        at = f"{where}.schema_anchors[{i}]"
        entry = _require(
            raw_anchor,
            ("batch_id", "proposal_identity", "schema_version", "schema_hash"),
            at,
        )
        anchors.append(
            BatchSchemaAnchor(
                batch_id=_string(entry["batch_id"], f"{at}.batch_id"),
                proposal_identity=_string(
                    entry["proposal_identity"], f"{at}.proposal_identity"
                ),
                schema_version=_string(entry["schema_version"], f"{at}.schema_version"),
                schema_hash=_string(entry["schema_hash"], f"{at}.schema_hash"),
            )
        )

    lifts = []
    for i, raw_lift in enumerate(_object_list(p.get("lifts", []), f"{where}.lifts")):
        at = f"{where}.lifts[{i}]"
        entry = _require(
            raw_lift,
            (
                "lift_id",
                "from_version",
                "from_hash",
                "to_version",
                "to_hash",
                "verified_collections",
            ),
            at,
        )
        lifts.append(
            SchemaLiftRecord(
                lift_id=_string(entry["lift_id"], f"{at}.lift_id"),
                from_version=_string(entry["from_version"], f"{at}.from_version"),
                from_hash=_string(entry["from_hash"], f"{at}.from_hash"),
                to_version=_string(entry["to_version"], f"{at}.to_version"),
                to_hash=_string(entry["to_hash"], f"{at}.to_hash"),
                verified_collections=tuple(
                    _string_list(
                        entry["verified_collections"], f"{at}.verified_collections"
                    )
                ),
            )
        )

    transitions = []
    for i, raw_step in enumerate(
        _object_list(p.get("policy_transitions", []), f"{where}.policy_transitions")
    ):
        at = f"{where}.policy_transitions[{i}]"
        entry = _require(
            raw_step,
            ("transition_id", "from_version", "from_hash", "to_version", "to_hash"),
            at,
        )
        step = PolicyTransitionRecord(
            transition_id=_string(entry["transition_id"], f"{at}.transition_id"),
            from_version=_string(entry["from_version"], f"{at}.from_version"),
            from_hash=_string(entry["from_hash"], f"{at}.from_hash"),
            to_version=_string(entry["to_version"], f"{at}.to_version"),
            to_hash=_string(entry["to_hash"], f"{at}.to_hash"),
        )
        # A file can claim any crossing it likes; only a registered one
        # actually authorizes carrying policy-1 reason codes forward. Checked
        # on the same terms the schema chain is: against the committed
        # registry, by exact pair, with no rule over version order.
        registered = POLICY_TRANSITIONS.get((step.from_version, step.from_hash))
        if registered is None or (
            registered.transition_id,
            registered.to_version,
            registered.to_hash,
        ) != (step.transition_id, step.to_version, step.to_hash):
            raise OracleLoadError(
                f"{at}: claims a semantic-policy transition "
                f"{step.transition_id!r} from {step.from_version!r} to "
                f"{step.to_version!r} that this build does not authorize"
            )
        transitions.append(step)

    batches = []
    for i, raw in enumerate(_object_list(p["batches"], f"{where}.batches")):
        at = f"{where}.batches[{i}]"
        b = _require(
            raw,
            (
                "batch_id",
                "rule",
                "resolved_scope",
                "diff",
                "semantic_diff_hash",
                "proposal_identity",
            ),
            at,
        )
        diff = []
        for j, raw_entry in enumerate(_object_list(b["diff"], f"{at}.diff")):
            entry_at = f"{at}.diff[{j}]"
            d = _require(
                raw_entry,
                (
                    "span_id",
                    "prior_disposition",
                    "prior_reason_code",
                    "accepted_disposition",
                    "accepted_reason_code",
                ),
                entry_at,
            )
            prior = d["prior_disposition"]
            diff.append(
                SemanticDiffEntry(
                    span_id=_string(d["span_id"], f"{entry_at}.span_id"),
                    prior_disposition=(
                        None
                        if prior is None
                        else _enum(SemanticDisposition, prior, entry_at)
                    ),
                    prior_reason_code=_optional_string(
                        d["prior_reason_code"], f"{entry_at}.prior_reason_code"
                    ),
                    accepted_disposition=_enum(
                        SemanticDisposition, d["accepted_disposition"], entry_at
                    ),
                    accepted_reason_code=_optional_string(
                        d["accepted_reason_code"], f"{entry_at}.accepted_reason_code"
                    ),
                )
            )
        batches.append(
            AcceptanceBatch(
                batch_id=_string(b["batch_id"], f"{at}.batch_id"),
                rule=_string(b["rule"], f"{at}.rule"),
                resolved_scope=tuple(
                    _string_list(b["resolved_scope"], f"{at}.resolved_scope")
                ),
                diff=tuple(diff),
                semantic_diff_hash=_string(
                    b["semantic_diff_hash"], f"{at}.semantic_diff_hash"
                ),
                proposal_identity=_string(
                    b["proposal_identity"], f"{at}.proposal_identity"
                ),
            )
        )

    records = []
    for i, raw in enumerate(_object_list(p["records"], f"{where}.records")):
        at = f"{where}.records[{i}]"
        r = _require(raw, ("span_id", "batch_id", "reviewer", "accepted_at"), at)
        records.append(
            AcceptanceRecord(
                span_id=_string(r["span_id"], f"{at}.span_id"),
                batch_id=_optional_string(r["batch_id"], f"{at}.batch_id"),
                reviewer=_string(r["reviewer"], f"{at}.reviewer"),
                accepted_at=_string(r["accepted_at"], f"{at}.accepted_at"),
            )
        )
    return (
        tuple(batches),
        tuple(records),
        tuple(lifts),
        tuple(anchors),
        tuple(transitions),
        tuple(unit_records),
        tuple(resolution_records),
    )


def load_accepted_inputs(path: Path) -> AcceptedInputs:
    """Load one committed accepted-inputs artifact from JSON.

    The whole input is the file. Nothing is read from the database, from a
    candidate, or from the current semantic policy.

    ``artifact_kind`` is checked first and must be exactly
    :data:`ACCEPTED_ARTIFACT_KIND`. That check is a fast, legible rejection of a
    machine proposal — but it is not what makes a proposal unloadable. A
    proposal has a different key set at every level (see
    :mod:`afterworlds.ingestion.mechanical.proposal`), so it fails ``_require``
    in several places even if someone edits its ``artifact_kind`` to lie.
    Structural incompatibility, not a flag and not a directory.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleLoadError(f"{path.name}: {exc}") from exc

    if isinstance(raw, dict) and raw.get("artifact_kind") != ACCEPTED_ARTIFACT_KIND:
        raise OracleLoadError(
            f"{path.name}: artifact_kind {raw.get('artifact_kind')!r} is not "
            f"{ACCEPTED_ARTIFACT_KIND!r}; this file is not accepted authority"
        )

    p = _require(
        raw,
        (
            "artifact_kind",
            "release_binding",
            "semantic_policy_version",
            "semantic_policy_hash",
            "representation_schema",
            "spans",
            "acceptance",
            "representation",
            "obligations",
        ),
        path.name,
        # Absent from all seven accepted batches, and absent rather than empty
        # from any artifact that states no review inventory — which is what
        # keeps their committed bytes and recorded identities exactly as
        # reviewed.
        optional=("review_units", "reference_resolutions"),
    )
    binding = _require(p["release_binding"], _RELEASE_BINDING_FIELDS, "release_binding")
    schema = _require(
        p["representation_schema"], ("version", "hash"), "representation_schema"
    )
    representation = _representation(p["representation"])
    obligations = tuple(
        _obligation(o, i)
        for i, o in enumerate(_object_list(p["obligations"], "obligations"))
    )
    _check_obligations_closed(representation, obligations, path.name)
    # Deliberately no closure check against the representation. See
    # ``AcceptedOracle.review_units``: an expectation derived from the output it
    # exists to test could not catch an omitted rule.
    review_units = tuple(
        _review_unit(u, i)
        for i, u in enumerate(_object_list(p.get("review_units", []), "review_units"))
    )
    reference_resolutions = tuple(
        _reference_resolution(r, i)
        for i, r in enumerate(
            _object_list(p.get("reference_resolutions", []), "reference_resolutions")
        )
    )
    spans = tuple(_span(s, i) for i, s in enumerate(_object_list(p["spans"], "spans")))
    (
        batches,
        acceptances,
        lifts,
        anchors,
        transitions,
        unit_records,
        resolution_records,
    ) = _acceptance(p["acceptance"], "acceptance")
    oracle = AcceptedOracle(
        binding=ReleaseBinding(
            **{
                k: _string(binding[k], f"release_binding.{k}")
                for k in _RELEASE_BINDING_FIELDS
            }
        ),
        policy_version=_string(p["semantic_policy_version"], "semantic_policy_version"),
        policy_hash=_string(p["semantic_policy_hash"], "semantic_policy_hash"),
        schema_version=_string(schema["version"], "representation_schema.version"),
        schema_hash=_string(schema["hash"], "representation_schema.hash"),
        spans=spans,
        representation=representation,
        obligations=obligations,
        review_units=review_units,
        reference_resolutions=reference_resolutions,
    )
    # Committed bytes are not self-proving either. The wire-shape checks above
    # establish that this file parses into the declared types; they say nothing
    # about whether its content is legal under the schema it names, or whether
    # that schema is one this build accepts authority under. Without this, a
    # schema-3 file carrying a schema-4 fact family loaded clean — its
    # obligations reconciled, and with no lifts the chain check below had
    # nothing to object to — and became committed accepted authority no
    # schema-3 reviewer could have reviewed (#137 round 4).
    if illegal := schema_binding_violations(
        oracle.representation, (oracle.schema_version, oracle.schema_hash)
    ):
        raise OracleLoadError(
            f"{path.name}: this artifact declares representation schema "
            f"{oracle.schema_version!r} but is not admissible under it: "
            + "; ".join(illegal)
        )

    # The policy contract is versioned independently of the schema one, so its
    # legality is a separate question with its own answer: a schema-12 file
    # declaring ``5d-semantic-policy-1`` passes the check above and may still
    # carry a retention reason that policy has no catalog for.
    if unstatable := policy_meaning_violations(
        oracle.representation, oracle.policy_version
    ):
        raise OracleLoadError(
            f"{path.name}: this artifact declares semantic policy "
            f"{oracle.policy_version!r} but carries meaning that policy cannot "
            "state: " + "; ".join(unstatable)
        )

    # The review inventory is held to the same two questions, and for the same
    # reason: a unit declared under ``5d-semantic-policy-1`` names a boundary
    # kind that policy has no catalog for, and an expected rule with no home is
    # an inventory claiming coverage it does not have. Neither is a weaker
    # oracle — an inventory that cannot be trusted to catch an omission is not
    # coverage evidence at all.
    if uncovered := review_unit_violations(
        oracle.review_units,
        oracle.representation,
        oracle.policy_version,
        oracle.spans,
    ):
        raise OracleLoadError(
            f"{path.name}: the accepted review inventory is not coverage: "
            + "; ".join(uncovered)
        )

    # Loaded evidence is read from a file, so the wire-shape checks above prove
    # only that it is well-formed — never that the succession it claims was
    # authorized, happened, or could have happened. Validated against the
    # registry and against this artifact's own declaration before it becomes
    # part of the loaded inputs.
    # Every accepted unit names one this artifact states, and every unit this
    # artifact states was accepted by a recorded action. Without the second
    # half, an inventory could be widened after the fact — new units, new
    # expectations — and inherit the acceptance of the ones beside them, which
    # is the claim the review-unit contract exists to make checkable.
    inventory = {u.unit_id for u in oracle.review_units}
    claimed = {a.unit_id for a in unit_records}
    if stranded := sorted(claimed - inventory):
        raise OracleLoadError(
            f"{path.name}: acceptance records name review units this artifact "
            f"does not state: {stranded}"
        )
    if unaccepted := sorted(inventory - claimed):
        raise OracleLoadError(
            f"{path.name}: review units {unaccepted} are stated but no "
            "acceptance action records accepting them; an inventory nobody "
            "accepted is not review evidence"
        )

    # The reference resolutions, held to both halves of the same question and
    # for the same reasons. A resolution that does not apply to this accepted
    # authority — wrong release, no such unresolved citation, a citation already
    # resolved, provenance that is not what review read, or an effective view
    # publication would refuse — is not a weaker artifact: applying it would
    # change what one accepted reference means on the strength of a decision
    # nobody could have made about it.
    if inapplicable := reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    ):
        raise OracleLoadError(
            f"{path.name}: the stated reference resolutions do not apply to this "
            "accepted authority: " + "; ".join(inapplicable)
        )
    # And an authorized decision is the only kind there is. Without the second
    # half a resolution could be added to a committed file after the fact and
    # inherit the authorization of the ones beside it, which is exactly what
    # "machine suggestions never become authority implicitly" forbids.
    decided = {r.resolution_id for r in oracle.reference_resolutions}
    authorized = {a.resolution_id for a in resolution_records}
    if stranded := sorted(authorized - decided):
        raise OracleLoadError(
            f"{path.name}: acceptance records authorize reference resolutions "
            f"this artifact does not state: {stranded}"
        )
    if unauthorized := sorted(decided - authorized):
        raise OracleLoadError(
            f"{path.name}: reference resolutions {unauthorized} are stated but "
            "no acceptance action records authorizing them; a resolution nobody "
            "authorized is not a reviewed decision"
        )
    if repeated := sorted(
        i
        for i, count in Counter(a.resolution_id for a in resolution_records).items()
        if count > 1
    ):
        raise OracleLoadError(
            f"{path.name}: reference resolutions {repeated} are authorized more "
            "than once; two authorizations of one decision cannot both be the "
            "one that took it"
        )
    for authority in resolution_records:
        blank = sorted(
            field
            for field, value in (
                ("authorized_by", authority.authorized_by),
                ("authorization_reference", authority.authorization_reference),
                ("reviewer", authority.reviewer),
                ("resolved_at", authority.resolved_at),
            )
            if not value.strip()
        )
        if blank:
            raise OracleLoadError(
                f"{path.name}: the authorization of reference resolution "
                f"{authority.resolution_id!r} states no {blank}; an unattributed "
                "authorization is not evidence that anyone decided it"
            )

    inputs = AcceptedInputs(
        oracle=oracle,
        batches=batches,
        acceptances=acceptances,
        review_unit_acceptances=unit_records,
        schema_anchors=anchors,
        lifts=lifts,
        policy_transitions=transitions,
        reference_resolution_acceptances=resolution_records,
    )

    # Evidence is validated as strictly as the result it justifies. A file whose
    # batch retains a digest but not the diff it names, or that accepts a span
    # nobody acted on, is not a weaker acceptance — it is a claim of acceptance
    # with the acceptance missing.
    if violations := validate_acceptance(inputs.classification()):
        raise OracleLoadError(
            f"{path.name}: acceptance evidence is not complete: "
            f"{'; '.join(violations)}"
        )

    # After completeness, because this reads the batches and their proposal
    # identities: an artifact whose evidence does not reconcile with itself
    # should say so in those terms rather than through a succession finding.
    if drift := succession_evidence_violations(
        batches, anchors, lifts, (oracle.schema_version, oracle.schema_hash)
    ):
        raise OracleLoadError(
            "acceptance evidence does not describe an authorized succession of "
            "this artifact: " + "; ".join(drift)
        )

    # The same question for the policy half. The parse loop above proved each
    # claimed step is a registered one; that is a statement about records, not
    # about the chain they form or about the policy this artifact declares.
    if crossings := policy_transition_violations(
        transitions, (oracle.policy_version, oracle.policy_hash)
    ):
        raise OracleLoadError(
            "acceptance evidence does not describe an authorized policy "
            "succession of this artifact: " + "; ".join(crossings)
        )
    return inputs


def load_oracle(path: Path) -> AcceptedOracle:
    """Load one committed accepted oracle from JSON.

    The oracle is the accepted-inputs artifact with its review evidence dropped:
    two files that reviewed their way to the same accepted classification are
    the same authority, so reviewer, timestamp, batch grouping, and diff never
    reach projection identity (#137 acceptance criterion 11).
    """
    return load_accepted_inputs(path).oracle


def candidate_from_accepted_inputs(inputs: AcceptedInputs) -> ProjectionCandidate:
    """The build candidate one committed accepted-inputs artifact states.

    This is the *input* direction: committed bytes a reviewer accepted become
    the candidate that is persisted, reconstructed, and then judged. It is not
    the forbidden direction — nothing here derives accepted authority from a
    candidate or from persisted output, and :func:`load_oracle` reads the same
    committed bytes rather than anything this function produced.

    Unlike the oracle, the candidate *does* carry the acceptance evidence: the
    publication gate requires an explicit acceptance record for every span in
    reconstructed persisted state, and that evidence has to reach persistence
    from a committed input or no build could ever satisfy it.
    """
    return ProjectionCandidate(
        binding=inputs.oracle.binding,
        classification=inputs.classification(),
        # The **effective** view, not the stored one. This is the single seam
        # every production consumer of accepted authority reaches persistence
        # through, so a reviewed resolution has to apply here or it would apply
        # nowhere: the build would persist the empty edge, the query path would
        # read it, and an override would address a citation with no destination.
        # The stored representation keeps stating what each reviewer accepted;
        # ``effective_representation`` is the identity function for all seven
        # accepted batches, which state no resolution.
        representation=effective_representation(
            inputs.oracle.representation, inputs.oracle.reference_resolutions
        ),
        schema_version=inputs.oracle.schema_version,
        schema_hash=inputs.oracle.schema_hash,
        # Carried, not re-derived. The inventory is identity-bearing on both
        # sides, so a candidate that dropped it would persist a projection whose
        # UUID could never match the oracle that judges it.
        review_units=inputs.oracle.review_units,
    )


def committed_oracle_for(
    package_uuid: str, release_version: str
) -> AcceptedOracle | None:
    """Return the committed oracle for one 5c release, or ``None``.

    Resolves from :data:`COMMITTED_ORACLE_DIR` and nowhere else. There is no
    directory argument, because an exported helper that accepts one is the same
    bypass as a publication entry that accepts one: a caller could resolve a
    self-authored oracle from a writable directory and hand it to the gate as
    committed authority.

    ``None`` here means "no accepted authority is committed for this release",
    which callers turn into a typed ``ABSENT`` publication outcome. It is never
    an empty oracle: an empty oracle would compare equal to an empty projection
    and publish nothing as if it were everything.
    """
    inputs = _resolve_committed_inputs(
        package_uuid, release_version, COMMITTED_ORACLE_DIR
    )
    return None if inputs is None else inputs.oracle


def committed_inputs_for(
    package_uuid: str, release_version: str
) -> AcceptedInputs | None:
    """Return the committed accepted inputs for one 5c release, or ``None``.

    Same resolution and same directory as :func:`committed_oracle_for`; this is
    the build-side view, which additionally carries the acceptance evidence.
    """
    return _resolve_committed_inputs(
        package_uuid, release_version, COMMITTED_ORACLE_DIR
    )


def _resolve_committed_inputs(
    package_uuid: str, release_version: str, directory: Path
) -> AcceptedInputs | None:
    """Resolution semantics, parameterized by directory for tests only.

    Two committed artifacts for one release is a rejection, not a choice.
    Picking one would make publication depend on filesystem ordering.
    """
    matches = [
        inputs
        for inputs in (
            load_accepted_inputs(p) for p in sorted(directory.glob("*.json"))
        )
        if inputs.oracle.binding.package_uuid == package_uuid
        and inputs.oracle.binding.release_version == release_version
    ]
    if len(matches) > 1:
        raise OracleLoadError(
            f"{len(matches)} committed oracles claim release "
            f"{package_uuid}/{release_version}"
        )
    return matches[0] if matches else None


def _resolve_committed_oracle(
    package_uuid: str, release_version: str, directory: Path
) -> AcceptedOracle | None:
    """Directory-parameterized oracle resolution, for tests only."""
    inputs = _resolve_committed_inputs(package_uuid, release_version, directory)
    return None if inputs is None else inputs.oracle


# ---------------------------------------------------------------------------
# Writing committed artifacts
# ---------------------------------------------------------------------------


def serialize_accepted_inputs(inputs: AcceptedInputs) -> bytes:
    """The one committed serialization form: indented, key-sorted, UTF-8, LF.

    Every committed accepted-inputs artifact in ``oracles/`` is written this
    way, and every reproduction of one compares against these exact bytes. That
    made the form load-bearing while it existed only as a line each acceptance
    program and each reproduction spelled out for itself — a stray ``indent``
    would have shown up as an artifact that no longer reproduces, blamed on the
    merge. It is stated once, here, beside the payload builder it serializes.

    Bytes rather than ``str`` because the comparison this exists for is a byte
    comparison against a file, and because the newline is part of the form.
    """
    return (
        json.dumps(
            accepted_inputs_payload(inputs),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def accepted_inputs_payload(inputs: AcceptedInputs) -> dict[str, object]:
    """Canonical JSON payload of one accepted-inputs artifact.

    Reuses :func:`oracle_payload` for the accepted result and
    :func:`accounting.acceptance_evidence_payload` for the evidence, so the file
    a reviewer commits is written in the same canonical form the loader expects
    and the identity functions already agree on.
    """
    payload: dict[str, object] = {"artifact_kind": ACCEPTED_ARTIFACT_KIND}
    payload.update(oracle_payload(inputs.oracle))
    evidence = acceptance_evidence_payload(inputs.classification())
    acceptance: dict[str, object] = {
        "batches": evidence["batches"],
        "records": evidence["acceptances"],
    }
    if "review_unit_records" in evidence:
        # Present exactly when the evidence payload states it, which is exactly
        # when a review unit was accepted. Same omit-when-empty discipline as
        # the three fields below, and the reason the seven committed batches
        # still round-trip byte-identically.
        acceptance["review_unit_records"] = evidence["review_unit_records"]
    if inputs.schema_anchors:
        # Emitted only when stated, so the committed legacy artifact keeps the
        # exact bytes it was reviewed and committed with.
        acceptance["schema_anchors"] = [
            {
                "batch_id": anchor.batch_id,
                "proposal_identity": anchor.proposal_identity,
                "schema_version": anchor.schema_version,
                "schema_hash": anchor.schema_hash,
            }
            for anchor in inputs.schema_anchors
        ]
    if inputs.lifts:
        # Emitted only when there is one, so an artifact that never crossed a
        # succession keeps the exact bytes it was committed with. Same
        # omit-when-empty discipline the post-schema-3 fields follow, and the
        # reason the committed conditions-1 file still round-trips unchanged.
        acceptance["lifts"] = [
            {
                "lift_id": lift.lift_id,
                "from_version": lift.from_version,
                "from_hash": lift.from_hash,
                "to_version": lift.to_version,
                "to_hash": lift.to_hash,
                "verified_collections": list(lift.verified_collections),
            }
            for lift in inputs.lifts
        ]
    if inputs.policy_transitions:
        # Same omit-when-empty discipline, and it is what keeps the committed
        # seven-batch artifact byte-identical while this build applies a newer
        # policy: an artifact that never crossed a policy succession says
        # nothing about one.
        acceptance["policy_transitions"] = [
            {
                "transition_id": step.transition_id,
                "from_version": step.from_version,
                "from_hash": step.from_hash,
                "to_version": step.to_version,
                "to_hash": step.to_hash,
            }
            for step in inputs.policy_transitions
        ]
    if inputs.reference_resolution_acceptances:
        # Same omit-when-empty discipline as every field above, and the reason
        # the seven committed batches still round-trip byte-identically while
        # this build can record a resolution at all.
        acceptance["reference_resolution_records"] = [
            {
                "resolution_id": decision.resolution_id,
                "authorized_by": decision.authorized_by,
                "authorization_reference": decision.authorization_reference,
                "reviewer": decision.reviewer,
                "resolved_at": decision.resolved_at,
            }
            for decision in sorted(
                inputs.reference_resolution_acceptances,
                key=lambda d: d.resolution_id,
            )
        ]
    payload["acceptance"] = acceptance
    return payload
