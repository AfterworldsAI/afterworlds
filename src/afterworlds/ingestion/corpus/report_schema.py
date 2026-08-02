"""The canonical evidence-report payload, as one typed object — CRD Issue 5c.

Four review rounds tried to close this schema with constants and loops:
required-key sets, closed-inventory maps, an "open map" list, a violations
walker. Each round shut one hole and left the next one — because the builder
held the real shape in a dict literal while the validator held a second,
partial description of it. Two definitions of one document is the defect, not
the individual omissions.

So there is now exactly one definition. :class:`CorpusEvidenceReport` *is* the
`5c-evidence-3` payload: ``build_report`` constructs it, ``report_hash`` hashes
its canonical dump, SQL persists that same dump, and a stored report is parsed
back through it. A field that is not on this model does not exist in the
schema, and a field on it cannot be omitted, retyped, or shadowed by an extra
key — ``extra="forbid"`` and ``strict=True`` are doing that work, not a
hand-maintained inventory.

**Intrinsic versus contextual.** This module owns what the document must be on
its own: shape, types, closed populations, and the cross-field semantics of a
successful verdict. It deliberately owns *nothing* about whether the document
agrees with the release it describes — that comparison needs the release row
and reconstructed 5c state, and lives in
:func:`persistence.verify_published_release`.

**Strictness that matters at a JSON boundary.** ``strict=True`` is what makes
``true`` fail an integer field (``bool`` is an ``int`` subclass), ``"0"`` fail
an integer, and ``0.0`` fail an integer. Arrays are declared ``list`` rather
than ``tuple`` because a JSON round-trip produces lists, and hashing is
unaffected: :func:`hashing.canonical_bytes` renders both as the same JSON
array.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_core import ErrorDetails

from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.models import LeafType

__all__ = [
    "CANONICAL_CANARY_NAMES",
    "EVIDENCE_REPORT_SCHEMA_VERSION",
    "Accounting",
    "ComponentBInvocation",
    "CorpusEvidenceReport",
    "ExtractorConfig",
    "Findings",
    "PolicyReference",
    "ReproductionTarget",
    "RulesCorpusVectorIdentity",
    "SourceManifestEntry",
    "TransformIdentity",
    "parse_recorded_report",
]

# Canonical evidence-report schema version. Bumped across canonical-shape
# changes: "2" for the R16 host-independent ``reproduction_target`` change; "3"
# for the R18 pre-release clean-baseline change that removed the
# legacy-reachability status (Issue 5c Rev7 / Issue 18 Rev6 supersede the strict
# cross-store quarantine contract). This version is bound into
# ``transform_config_payload`` (hence the transform hash / package UUID /
# release version), so an evidence-report *schema* change mints a NEW immutable
# release instead of being reused under a predecessor's identity (R17
# mechanism). It is deliberately an *explicit* schema identity rather than a
# byte-level hash of this module: only an intentional canonical-shape change
# should remint, never a comment/docstring/annotation edit.
#
# Typing this payload did **not** change it. The emitted document and its hash
# are byte-identical to the untyped implementation, so the version stands.
EVIDENCE_REPORT_SCHEMA_VERSION = "5c-evidence-3"

#: The canonical version-canary population, derived from the committed canary
#: definitions. Never a second hand-written list: adding or retiring a canary
#: moves the required population with it.
CANONICAL_CANARY_NAMES = frozenset(canary.name for canary in VERSION_CANARIES)

#: Leaf-type totals may cover any *subset* of the taxonomy — a corpus with no
#: tables legitimately reports no ``table_cell`` — but never a name outside it.
#: Derived from the enum, so the universe cannot drift from the taxonomy.
_LEAF_TYPE_NAMES = frozenset(leaf_type.value for leaf_type in LeafType)

Count = Annotated[int, Field(ge=0)]
#: Arrays accept a tuple as well as a list. The identity builders return
#: tuples in memory and JSON round-trips them to lists, and both canonicalize
#: to the same bytes — so this admits the two encodings of one value without
#: admitting a *string*, which lax mode still refuses.
Array = Annotated[list[str], Field(strict=False)]


class _Canonical(BaseModel):
    """Frozen, closed, and strict: the three properties this schema needs."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ExtractorConfig(_Canonical):
    """The frozen extraction identity, exactly as ``extraction_config()`` emits."""

    tool: str
    tool_version: str
    engine: str
    engine_version: str
    use_text_flow: bool
    keep_blank_chars: bool
    line_y_tolerance: float
    geometry_decimals: int
    reading_order: str


class SourceManifestEntry(_Canonical):
    """One audited first-party transform module and its content hash."""

    path: str
    sha256: str


class ComponentBInvocation(_Canonical):
    """The deterministic Component B invocation the transform identity records."""

    entrypoint: str
    steps: Array
    deterministic: bool


class TransformIdentity(_Canonical):
    """The complete first-party transform identity carried by the report.

    Closed, not content-populated: every key here comes from
    ``extraction_config()`` and ``transform_identity()``, both of which return
    fixed schemas. Treating it as open let an edited-and-rehashed report replace
    the whole identity with ``{}``.
    """

    extractor: ExtractorConfig
    tool: str
    tool_version: str
    source_manifest: Annotated[list[SourceManifestEntry], Field(strict=False)]
    transform_source_hash: str
    component_b_invocation: ComponentBInvocation
    intermediate_representation_committed: bool


class RulesCorpusVectorIdentity(_Canonical):
    """The identity-bearing rules-corpus vector configuration (ADR-018 D2/D4/D11).

    Also closed: ``rules_corpus_vector_identity()`` returns a fixed schema.
    """

    embedding_model_id: str
    metadata_schema_version: int
    metadata_fields: Array
    chunk_id_scheme: str
    collection_name_scheme: str


class ReproductionTarget(_Canonical):
    """The declared, host-independent reproduction target (PR #134 R16)."""

    python_target: str


class PolicyReference(_Canonical):
    """Which reconciliation policy was frozen, and which was actually applied."""

    policy_version: str
    policy_hash: str
    applied_policy_hash: str


class Accounting(_Canonical):
    """The leaf accounting equation's terms."""

    inventoried_leaves: Count
    represented_leaves: Count
    excluded_leaves: Count
    unresolved_leaves: Count

    @property
    def balances(self) -> bool:
        return self.inventoried_leaves == (
            self.represented_leaves + self.excluded_leaves + self.unresolved_leaves
        )


class Findings(_Canonical):
    """Identity-level reconciliation findings, as counts."""

    gaps: Count
    overlaps: Count
    orphans: Count
    duplications: Count

    def nonzero(self) -> tuple[str, ...]:
        return tuple(
            f"findings.{name} is {value}, not 0"
            for name, value in sorted(self.__dict__.items())
            if value
        )


class CorpusEvidenceReport(_Canonical):
    """The complete canonical `5c-evidence-3` evidence-report payload."""

    report_version: str
    # Proof identities (never this report's own hash — it cannot contain it).
    authoritative_source_hash: str
    transform_config_hash: str
    bundle_root_hash: str
    frozen_source_ledger_hash: str
    persisted_corpus_digest: str
    # Closed identity structures.
    transform_identity: TransformIdentity
    rules_corpus_vector_identity: RulesCorpusVectorIdentity
    reproduction_target: ReproductionTarget
    reconciliation_policy_reference: PolicyReference
    # Content-derived populations: the *key set* varies with the corpus, but the
    # mapping and its value types do not. "Open" never meant "unvalidated".
    source_ledger_leaf_totals: dict[str, Count]
    represented_totals: dict[str, Count]
    #: Keys are policy reason codes. Left as free strings here on purpose: the
    #: frozen policy is not available at parse time, and reaching for it would
    #: create a second policy definition. Reason validity is proven
    #: contextually, against the reconstructed policy.
    excluded_totals_by_reason: dict[str, Count]
    # Verdict-bearing summaries.
    unresolved_leaves: Count
    declared_projection_count: Count
    accounting: Accounting
    findings: Findings
    invalid_locators: Count
    concordance_failures: Count
    version_canaries: dict[str, bool]
    prepublication_validation_status: str

    @model_validator(mode="after")
    def _canonical_populations(self) -> CorpusEvidenceReport:
        """Closed populations and closed value domains, at parse time."""
        if self.report_version != EVIDENCE_REPORT_SCHEMA_VERSION:
            raise ValueError(
                f"report_version {self.report_version!r} is not the supported "
                f"{EVIDENCE_REPORT_SCHEMA_VERSION!r}"
            )
        if self.prepublication_validation_status not in ("pass", "fail"):
            raise ValueError(
                "prepublication_validation_status must be 'pass' or 'fail', got "
                f"{self.prepublication_validation_status!r}"
            )
        if set(self.version_canaries) != CANONICAL_CANARY_NAMES:
            missing = sorted(CANONICAL_CANARY_NAMES - set(self.version_canaries))
            unexpected = sorted(set(self.version_canaries) - CANONICAL_CANARY_NAMES)
            raise ValueError(
                "version_canaries is not the canonical population "
                f"(missing {missing}, unexpected {unexpected})"
            )
        for field in ("source_ledger_leaf_totals", "represented_totals"):
            outside = sorted(set(getattr(self, field)) - _LEAF_TYPE_NAMES)
            if outside:
                raise ValueError(
                    f"{field} names leaf types outside the taxonomy: {outside}"
                )
        return self

    def verdict_violations(self) -> tuple[str, ...]:
        """Why these numbers do not state a successful publication.

        The one definition of success in the report's own terms, read off typed
        fields. ``build_report`` derives the recorded status from it, so a
        report cannot be *written* claiming success over contradictory
        summaries; a stored report is measured against the same rule.
        """
        violations: list[str] = []
        for name in ("unresolved_leaves", "invalid_locators", "concordance_failures"):
            value: int = getattr(self, name)
            if value:
                violations.append(f"{name} is {value}, not 0")
        violations.extend(self.findings.nonzero())
        for canary, passed in sorted(self.version_canaries.items()):
            if not passed:
                violations.append(f"version canary {canary} did not pass")
        if self.accounting.unresolved_leaves:
            violations.append(
                "accounting.unresolved_leaves is "
                f"{self.accounting.unresolved_leaves}, not 0"
            )
        if not self.accounting.balances:
            violations.append("accounting equation does not balance")
        if self.accounting.unresolved_leaves != self.unresolved_leaves:
            violations.append(
                "accounting.unresolved_leaves disagrees with the top-level "
                "unresolved_leaves"
            )
        return tuple(violations)

    def success_violations(self) -> tuple[str, ...]:
        """Why this recorded report is not a successful publication verdict.

        Identity is not sufficiency: a report edited to ``"fail"`` and rehashed
        keeps every proof identity intact while recording that publication did
        not succeed.
        """
        violations = []
        if self.prepublication_validation_status != "pass":
            violations.append(
                "prepublication_validation_status is "
                f"{self.prepublication_validation_status!r}, not 'pass' — the "
                "recorded evidence states this release did not publish successfully"
            )
        return (*violations, *self.verdict_violations())

    def dump(self) -> dict[str, Any]:
        """The canonical JSON-compatible payload: hashed, persisted, compared.

        One serialization path. ``report_hash``, the SQL column, and every
        downstream comparison read this, so there is no second rendering of the
        document that could drift from the model.
        """
        return self.model_dump(mode="json")


def _where(error: ErrorDetails) -> str:
    location = ".".join(str(part) for part in error["loc"]) or "evidence report"
    return f"{location}: {error['msg']}"


def parse_recorded_report(
    payload: object,
) -> tuple[CorpusEvidenceReport | None, tuple[str, ...]]:
    """Parse a stored payload, returning violations rather than raising.

    A recorded report has unknown provenance — JSON round-tripped, possibly
    hand-edited — so a malformed one is an auditable finding, not an exception
    escaping into the publication path. Callers turn these strings into typed
    refusals.
    """
    try:
        return CorpusEvidenceReport.model_validate(payload), ()
    except ValidationError as exc:
        return None, tuple(_where(error) for error in exc.errors())
