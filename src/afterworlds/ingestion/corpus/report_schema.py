"""The canonical evidence-report payload, as one structurally immutable value.

CRD Issue 5c. This module owns the `5c-evidence-3` document: what it is, how a
stored one is parsed, and how it is rendered. There is exactly one definition —
:class:`CorpusEvidenceReport` *is* the payload. ``build_report`` produces it,
``report_hash`` hashes its dump, SQL persists that same dump, and a stored report
is parsed back through it. A field not declared here does not exist in the
schema, and a declared field cannot be omitted, retyped, or shadowed by an extra
key.

**Structural immutability, not a freeze.** Every canonical type is a
:class:`typing.NamedTuple` and every container is a tuple, because two
*conventionally* frozen representations were defeated in review by writing
underneath their guards: a frozen Pydantic ``BaseModel`` through
``vars(report)[...] = {}``, and a frozen **slotted** dataclass through
``object.__setattr__(report, ...)`` — slots remove ``__dict__`` but the
inherited base setter still writes slot storage. A ``NamedTuple`` keeps its
values in the tuple itself: no instance dictionary, no slot descriptor, nothing
for any setter to reach. Immutability is a property of the storage rather than
of a guard someone remembered to apply.

Maps are :class:`Pairs`, a tuple of sorted key/value pairs, for the same reason.
A ``MappingProxyType`` is a *view* onto a real dictionary that stays reachable
through ``gc.get_referents``; a pair tuple has no backing dictionary at all.

**Pydantic validates ingress and never holds the value.** One
:class:`~pydantic.TypeAdapter` parses raw JSON into the tree — strict scalars,
objects required at every node, closed populations. Nothing downstream holds a
Pydantic instance.

**Intrinsic versus contextual.** This module owns what the document must be on
its own: shape, types, closed populations, and the cross-field semantics of a
successful verdict. It owns *nothing* about whether the document agrees with the
release it describes — that comparison needs the release row and reconstructed
5c state, and lives in :mod:`persistence`.
"""

from __future__ import annotations

from typing import Annotated, Any, NamedTuple

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    TypeAdapter,
    ValidationError,
)
from pydantic_core import ErrorDetails

from afterworlds.ingestion.corpus.concordance import VERSION_CANARIES
from afterworlds.ingestion.corpus.models import LeafType

__all__ = [
    "CANONICAL_CANARY_NAMES",
    "EVIDENCE_REPORT_SCHEMA_VERSION",
    "PYTHON_TARGET",
    "Accounting",
    "ComponentBInvocation",
    "CorpusEvidenceReport",
    "ExtractorConfig",
    "Findings",
    "Pairs",
    "PolicyReference",
    "ReproductionTarget",
    "RulesCorpusVectorIdentity",
    "SourceManifestEntry",
    "TransformIdentity",
    "canonical_report",
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

#: The declared Python target (pyproject ``requires-python``; Python 3.12 only
#: per CLAUDE.md). Owned here, in the schema layer, because it is a *canonical
#: semantic constant of the document* — not a default the builder happens to
#: pass. A report recording any other target is not this schema.
PYTHON_TARGET = "3.12"

#: The canonical version-canary population, derived from the committed canary
#: definitions. Never a second hand-written list: adding or retiring a canary
#: moves the required population with it.
CANONICAL_CANARY_NAMES = frozenset(canary.name for canary in VERSION_CANARIES)

#: Leaf-type totals may cover any *subset* of the taxonomy — a corpus with no
#: tables legitimately reports no ``table_cell`` — but never a name outside it.
#: Derived from the enum, so the universe cannot drift from the taxonomy.
_LEAF_TYPE_NAMES = frozenset(leaf_type.value for leaf_type in LeafType)


class Pairs(tuple[tuple[str, Any], ...]):
    """A canonical JSON object, stored as sorted ``(key, value)`` pairs.

    A distinct type rather than a naming convention: :func:`_json` renders a
    ``Pairs`` as an object and every other tuple as an array, so an *empty* map
    still serializes to ``{}`` instead of being guessed at from its contents.
    """

    __slots__ = ()


def _object_only(value: object) -> object:
    """Refuse anything but a JSON object at a node that declares one.

    Pydantic's native ``NamedTuple`` handling accepts a positional sequence, so
    without this a stored report could arrive as a JSON *array* and parse.
    """
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object, got {type(value).__name__}")
    return value


def _sorted_pairs(value: object) -> object:
    """A JSON object as sorted pairs, ready for per-entry validation."""
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object, got {type(value).__name__}")
    return tuple(sorted(value.items()))


#: Applied at every node declaring a nested object.
_OBJ = BeforeValidator(_object_only)

#: Strict scalars. ``bool`` is an ``int`` subclass, so without these a JSON
#: ``true`` would load as the count ``1``; ``"0"`` and ``0.0`` are likewise not
#: integers, and a number is not a string.
Str = Annotated[str, Field(strict=True)]
Bool = Annotated[bool, Field(strict=True)]
Int = Annotated[int, Field(strict=True)]
Real = Annotated[float, Field(strict=True)]

Count = Annotated[int, Field(strict=True, ge=0)]

#: Content-derived count maps: variable key population, closed value domain.
CountMap = Annotated[
    tuple[tuple[Str, Count], ...],
    BeforeValidator(_sorted_pairs),
    AfterValidator(Pairs),
]
#: Boolean maps — the canary population.
FlagMap = Annotated[
    tuple[tuple[Str, Bool], ...],
    BeforeValidator(_sorted_pairs),
    AfterValidator(Pairs),
]
#: Canonical arrays are tuples, so a parsed report cannot be appended to or have
#: an element replaced. Lax about list-versus-tuple on the way in because the
#: identity builders return tuples in memory while JSON round-trips them to
#: lists, and both canonicalize to the same bytes. A bare string is still
#: refused.
Array = tuple[Str, ...]


def _supported_version(value: str) -> str:
    if value != EVIDENCE_REPORT_SCHEMA_VERSION:
        raise ValueError(
            f"report_version {value!r} is not the supported "
            f"{EVIDENCE_REPORT_SCHEMA_VERSION!r}"
        )
    return value


def _validation_status(value: str) -> str:
    if value not in ("pass", "fail"):
        raise ValueError(
            f"prepublication_validation_status must be 'pass' or 'fail', got {value!r}"
        )
    return value


def _canonical_python_target(value: str) -> str:
    if value != PYTHON_TARGET:
        raise ValueError(
            f"python_target {value!r} is not the canonical reproduction target "
            f"{PYTHON_TARGET!r}"
        )
    return value


def _canonical_canaries(value: Pairs) -> Pairs:
    names = {name for name, _ in value}
    if names != CANONICAL_CANARY_NAMES:
        raise ValueError(
            "version_canaries is not the canonical population (missing "
            f"{sorted(CANONICAL_CANARY_NAMES - names)}, unexpected "
            f"{sorted(names - CANONICAL_CANARY_NAMES)})"
        )
    return value


def _leaf_type_keys(value: Pairs) -> Pairs:
    outside = sorted({name for name, _ in value} - _LEAF_TYPE_NAMES)
    if outside:
        raise ValueError(f"names leaf types outside the taxonomy: {outside}")
    return value


class ExtractorConfig(NamedTuple):
    """The frozen extraction identity, exactly as ``extraction_config()`` emits."""

    tool: Str
    tool_version: Str
    engine: Str
    engine_version: Str
    use_text_flow: Bool
    keep_blank_chars: Bool
    line_y_tolerance: Real
    geometry_decimals: Int
    reading_order: Str


class SourceManifestEntry(NamedTuple):
    """One audited first-party transform module and its content hash."""

    path: Str
    sha256: Str


class ComponentBInvocation(NamedTuple):
    """The deterministic Component B invocation the transform identity records."""

    entrypoint: Str
    steps: Array
    deterministic: Bool


class TransformIdentity(NamedTuple):
    """The complete first-party transform identity carried by the report.

    Closed, not content-populated: every key comes from ``extraction_config()``
    and ``transform_identity()``, both of which return fixed schemas. Treating it
    as open let an edited-and-rehashed report replace the whole identity with
    ``{}``.
    """

    extractor: Annotated[ExtractorConfig, _OBJ]
    tool: Str
    tool_version: Str
    source_manifest: tuple[Annotated[SourceManifestEntry, _OBJ], ...]
    transform_source_hash: Str
    component_b_invocation: Annotated[ComponentBInvocation, _OBJ]
    intermediate_representation_committed: Bool


class RulesCorpusVectorIdentity(NamedTuple):
    """The identity-bearing rules-corpus vector configuration (ADR-018 D2/D4/D11).

    Also closed: ``rules_corpus_vector_identity()`` returns a fixed schema.
    """

    embedding_model_id: Str
    metadata_schema_version: Int
    metadata_fields: Array
    chunk_id_scheme: Str
    collection_name_scheme: Str


class ReproductionTarget(NamedTuple):
    """The declared, host-independent reproduction target (PR #134 R16).

    Bound to :data:`PYTHON_TARGET` on the field itself, not merely defaulted to
    it by the builder. A stored report recording any other target fails
    intrinsic parsing rather than being compared somewhere later and possibly
    not at all.
    """

    python_target: Annotated[Str, AfterValidator(_canonical_python_target)]


class PolicyReference(NamedTuple):
    """Which reconciliation policy was frozen, and which was actually applied."""

    policy_version: Str
    policy_hash: Str
    applied_policy_hash: Str


class Accounting(NamedTuple):
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


class Findings(NamedTuple):
    """Identity-level reconciliation findings, as counts."""

    gaps: Count
    overlaps: Count
    orphans: Count
    duplications: Count

    def nonzero(self) -> tuple[str, ...]:
        return tuple(
            f"findings.{name} is {value}, not 0"
            for name, value in sorted(self._asdict().items())
            if value
        )


class CorpusEvidenceReport(NamedTuple):
    """The complete canonical `5c-evidence-3` evidence-report payload."""

    report_version: Annotated[Str, AfterValidator(_supported_version)]
    # Proof identities (never this report's own hash — it cannot contain it).
    authoritative_source_hash: Str
    transform_config_hash: Str
    bundle_root_hash: Str
    frozen_source_ledger_hash: Str
    persisted_corpus_digest: Str
    # Closed identity structures.
    transform_identity: Annotated[TransformIdentity, _OBJ]
    rules_corpus_vector_identity: Annotated[RulesCorpusVectorIdentity, _OBJ]
    reproduction_target: Annotated[ReproductionTarget, _OBJ]
    reconciliation_policy_reference: Annotated[PolicyReference, _OBJ]
    # Content-derived populations: the *key set* varies with the corpus, but the
    # mapping and its value types do not. "Open" never meant "unvalidated".
    source_ledger_leaf_totals: Annotated[CountMap, AfterValidator(_leaf_type_keys)]
    represented_totals: Annotated[CountMap, AfterValidator(_leaf_type_keys)]
    #: Keys are policy reason codes. Left as free strings here on purpose: the
    #: frozen policy is not available at parse time, and reaching for it would
    #: create a second policy definition. Reason validity is proven contextually,
    #: against the reconstructed policy.
    excluded_totals_by_reason: CountMap
    # Verdict-bearing summaries.
    unresolved_leaves: Count
    declared_projection_count: Count
    accounting: Annotated[Accounting, _OBJ]
    findings: Annotated[Findings, _OBJ]
    invalid_locators: Count
    concordance_failures: Count
    version_canaries: Annotated[FlagMap, AfterValidator(_canonical_canaries)]
    prepublication_validation_status: Annotated[Str, AfterValidator(_validation_status)]

    def verdict_violations(self) -> tuple[str, ...]:
        """Why these numbers do not state a successful publication.

        The one definition of success in the report's own terms, read off typed
        fields. ``build_report`` derives the recorded status from it, so a report
        cannot be *written* claiming success over contradictory summaries; a
        stored report is measured against the same rule.
        """
        violations: list[str] = []
        for name in ("unresolved_leaves", "invalid_locators", "concordance_failures"):
            value: int = getattr(self, name)
            if value:
                violations.append(f"{name} is {value}, not 0")
        violations.extend(self.findings.nonzero())
        # Sorted explicitly: the parser sorts the pairs, but violation order is
        # asserted in tests and must not depend on that staying true.
        for canary, passed in sorted(self.version_canaries):
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

        The **only** serialization of this document. ``report_hash``, the SQL
        column, and every contextual comparison read this — including
        comparisons that need one nested fragment, which slice this dump rather
        than serializing the nested value separately.

        Note what this replaces rather than merely wraps: a ``NamedTuple`` *is*
        JSON-serializable by ``json.dumps``, as a positional **array**. So
        ``canonical_bytes(report)`` succeeds and mints a wrong-but-plausible
        hash. Every hash, column, and comparison goes through this method, and a
        control asserts the raw object's canonical bytes differ from the
        payload's so an accidental direct serialization fails loudly.
        """
        rendered: dict[str, Any] = _json(self)
        return rendered


def _json(value: object) -> Any:
    """Render the immutable value tree as canonical JSON-compatible data.

    Field names come off the ``NamedTuple`` itself, so the serializer cannot
    drift from the declaration the way a hand-maintained key list did.
    """
    if isinstance(value, Pairs):
        return {key: _json(item) for key, item in value}
    if isinstance(value, tuple):
        names: tuple[str, ...] | None = getattr(value, "_fields", None)
        if names is not None:
            return {name: _json(item) for name, item in zip(names, value, strict=True)}
        return [_json(item) for item in value]
    return value


#: The one parser for the canonical document.
_ADAPTER: TypeAdapter[CorpusEvidenceReport] = TypeAdapter(
    Annotated[CorpusEvidenceReport, _OBJ]
)


def _where(error: ErrorDetails) -> str:
    location = ".".join(str(part) for part in error["loc"]) or "evidence report"
    return f"{location}: {error['msg']}"


def canonical_report(payload: object) -> CorpusEvidenceReport:
    """Build the canonical value, raising on anything that is not this schema.

    The construction-side counterpart to :func:`parse_recorded_report`, and the
    *only* way production code makes one of these: a ``NamedTuple`` constructor
    runs no validators, so direct construction is never a production path. A
    build that cannot describe itself in the canonical shape is a defect here
    and now, not an auditable finding about someone else's stored bytes.
    """
    return _ADAPTER.validate_python(payload)


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
        return _ADAPTER.validate_python(payload), ()
    except ValidationError as exc:
        return None, tuple(_where(error) for error in exc.errors())
