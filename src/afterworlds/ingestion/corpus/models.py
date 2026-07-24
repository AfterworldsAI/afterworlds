"""Corpus-integrity pipeline vocabulary — CRD Issue 5c.

Frozen, deterministic in-memory artifacts for Completion Contract A. Every type
here is immutable and hash-stable: no wall-clock timestamps, no ``uuid4``, no
absolute paths. Identities are content-derived (see :mod:`.hashing`).

Layer boundaries (ADR-005c Decision 2, Owner Decision 2):
* This module models the **source-corpus layer** only — ledger leaves,
  containers, the reconciliation policy/member, declared projections, corpus
  chunks, and the release record.
* It does **not** model MechanicalEntity, executable projection, or runtime
  binding — those are Issue 5d/2b/15c.

These are new corpus concepts; they do not extend ``RuleChunk`` or any Issue 5a
model (projection linkage lives in its own tables referencing ``chunk_id``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ContainerType(StrEnum):
    """Structural container kinds (Component C). Excluded from the leaf count."""

    ENTRY = "entry"  # a named entry: spell, condition, action, item, stat block
    SECTION = "section"
    SUBSECTION = "subsection"
    TABLE = "table"
    LIST = "list"


class LeafType(StrEnum):
    """Atomic coverage-leaf kinds (Component C taxonomy).

    Every page-content occurrence is exactly one leaf of one of these types.
    ``HEADER_FOOTER`` marks running-header/footer margin lines that the frozen
    policy may exclude; it is still a leaf inside the accounting equation.
    """

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    STAT_FIELD = "stat_field"
    CAPTION = "caption"
    ATTRIBUTION = "attribution"
    HEADER_FOOTER = "header_footer"


class Disposition(StrEnum):
    """A leaf's single final reconciliation disposition (Component D)."""

    REPRESENTED = "represented"
    EXCLUDED = "excluded"
    UNRESOLVED = "unresolved"


# ---------------------------------------------------------------------------
# Frozen source ledger (Component C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Container:
    """A structural container identity with a nested path (Component C).

    Containers may nest and overlap structurally but do not participate in the
    leaf-count equation.
    """

    container_id: str
    container_type: ContainerType
    label: str
    printed_page: int
    parent_id: str | None


@dataclass(frozen=True)
class Leaf:
    """An atomic coverage leaf: one page-content occurrence (Component C).

    ``char_start``/``char_end`` are the half-open span within the page's
    canonical text; the ledger guarantees these spans are disjoint and exhaust
    every page. ``container_path`` is the full nested container id path
    (outermost first). ``content`` is the extracted source text of this leaf.
    """

    leaf_id: str
    printed_page: int
    page_index: int
    leaf_type: LeafType
    content: str
    char_start: int
    char_end: int
    occurrence_index: int
    container_path: tuple[str, ...]


@dataclass(frozen=True)
class SourceLedger:
    """The frozen pre-transform source ledger (Component C).

    Owns only source-side facts: leaves, containers, source identity, and the
    extraction identity that produced them. Carries no dispositions, exclusion
    reasons, or policy — those live in the reconciliation member and policy.
    """

    source_document: str
    source_version: str
    source_sha256: str
    extraction_config: dict[str, object]
    containers: tuple[Container, ...]
    leaves: tuple[Leaf, ...]


# ---------------------------------------------------------------------------
# Frozen reconciliation policy (Component B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExclusionReason:
    """A closed-set exclusion reason code with deterministic eligibility.

    ``eligible_leaf_types`` names the leaf types this reason may exclude; a leaf
    assigned this reason whose type is not eligible is rejected (→ unresolved).
    """

    code: str
    description: str
    eligible_leaf_types: tuple[LeafType, ...]


@dataclass(frozen=True)
class ProjectionRole:
    """A permitted projection role and its overlap semantics (Component B/D)."""

    name: str
    description: str
    allows_overlap: bool


@dataclass(frozen=True)
class ReconciliationPolicy:
    """The frozen reconciliation policy (Component B).

    Committed and frozen before any corpus output exists (K step a0); covered by
    the transform source/configuration hash. Defines the closed exclusion-reason
    set, permitted projection roles and overlap authorization, and the
    normalization/equivalence identity used for coverage and duplicate checks.
    """

    policy_version: str
    normalization_version: str
    exclusion_reasons: tuple[ExclusionReason, ...]
    projection_roles: tuple[ProjectionRole, ...]

    def reason(self, code: str) -> ExclusionReason | None:
        return next((r for r in self.exclusion_reasons if r.code == code), None)

    def role(self, name: str) -> ProjectionRole | None:
        return next((r for r in self.projection_roles if r.name == name), None)


# ---------------------------------------------------------------------------
# Canonical corpus members (Component K a2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorpusChunk:
    """A canonical authoritative source-text record generated from the ledger.

    Maps 1:1 to a persisted ``RuleChunk`` row (Issue 5a model, unextended).
    ``source_leaf_ids`` records which leaves it aggregates; the projection edges
    carry the exact covered subspans and role (Component D/G).

    ``source_document`` / ``source_locator_type`` / ``source_locator_value`` are
    the Issue 5a runtime-visible provenance fields (Component G). They are
    populated when a chunk is reconstructed from its persisted ``rp_chunks`` row
    so that the persisted-corpus digest binds the *actual* served citation, not a
    ledger-synthesized approximation of it — tampering any of them must break
    ``verify_persisted_digest`` and the final/reuse gate (PR #134 remediation,
    defect family 2). They default to empty for the pre-persistence build path
    (``transform.build_corpus``), which does not carry provenance into the
    bundle root; provenance enters the proof only through the persisted-state
    digest, and ``persistence._persist_bundle_rows`` derives the persisted
    values deterministically from the ledger + locator.
    """

    chunk_id: str
    subsystem: str
    content: str
    printed_page: int
    section_label: str | None
    container_path: tuple[str, ...]
    source_leaf_ids: tuple[str, ...]
    source_document: str = ""
    source_locator_type: str = ""
    source_locator_value: str = ""


@dataclass(frozen=True)
class DerivativeNote:
    """Non-authoritative derivative content (Component F).

    Kept strictly separate from the authoritative corpus; never counts toward
    publication and is never persisted as authoritative canon.
    """

    note_id: str
    kind: str
    content: str
    about_leaf_ids: tuple[str, ...]


@dataclass(frozen=True)
class CorpusBundleMembers:
    """The canonical corpus members produced from the frozen ledger."""

    chunks: tuple[CorpusChunk, ...]
    derivative_notes: tuple[DerivativeNote, ...]


# ---------------------------------------------------------------------------
# Reconciliation member (Component D)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectionEdge:
    """A declared-projection edge: leaf → chunk under a policy role (Component D).

    ``cover_start``/``cover_end`` are the covered subspan of the source leaf's
    content (half-open). The union of a represented leaf's edges must cover its
    whole content with no gaps.
    """

    projection_id: str
    leaf_id: str
    chunk_id: str
    role: str
    cover_start: int
    cover_end: int


@dataclass(frozen=True)
class LeafDisposition:
    """A leaf's single final disposition and (if excluded) its policy reason."""

    leaf_id: str
    disposition: Disposition
    exclusion_reason_code: str | None


@dataclass(frozen=True)
class ReconciliationFindings:
    """Identity-level reconciliation findings (Component D)."""

    gaps: tuple[str, ...]  # represented leaf ids with an uncovered subspan
    overlaps: tuple[str, ...]  # leaf ids with unauthorized overlapping coverage
    orphans: tuple[str, ...]  # chunk ids with no leaf link
    duplications: tuple[str, ...]  # duplicate projection / equivalent-output ids
    unresolved: tuple[str, ...]  # leaf ids left unresolved


@dataclass(frozen=True)
class ReconciliationMember:
    """The reconciliation member: policy application over ledger + output (D).

    Records the exact policy identity/version/hash applied, per-leaf
    dispositions, declared-projection edges, and the findings. The accounting
    equation ranges over atomic leaves only.
    """

    policy_version: str
    policy_hash: str
    dispositions: tuple[LeafDisposition, ...]
    projections: tuple[ProjectionEdge, ...]
    findings: ReconciliationFindings
    inventoried_leaves: int
    represented_leaves: int
    excluded_leaves: int
    unresolved_leaves: int


# ---------------------------------------------------------------------------
# Bundle, digest, report, release (Components K, A, H, I)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BundleMember:
    """One member listed in the ordered canonical bundle-member manifest."""

    name: str
    kind: str
    member_hash: str


@dataclass(frozen=True)
class CanonicalBundle:
    """The canonical bundle: ledger + corpus members + reconciliation (K).

    The bundle-root hash covers the members and the ordered member manifest and
    excludes itself and anything containing it (the evidence report).
    """

    member_manifest: tuple[BundleMember, ...]
    bundle_root_hash: str


@dataclass(frozen=True)
class ReleaseIdentity:
    """The five top-level immutable release identities (Component A)."""

    authoritative_source_hash: str
    transform_config_hash: str
    bundle_root_hash: str
    evidence_report_hash: str
    persisted_corpus_digest: str


@dataclass(frozen=True)
class ReleaseRecord:
    """External release/publication record (Component A/I).

    Holds the five top-level hashes and the derived-but-reproducible package
    UUID and release version (Owner Decision 1). This is where the final
    publication gate runs; it is not a bundle member.
    """

    package_uuid: str
    release_version: str
    identity: ReleaseIdentity
    transform_config: dict[str, object]
    ledger_hash: str
    policy_hash: str
    reconciliation_hash: str
    corpus_report_reference: str


@dataclass(frozen=True)
class GateResult:
    """Result of running the publication gate (Component I)."""

    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)
