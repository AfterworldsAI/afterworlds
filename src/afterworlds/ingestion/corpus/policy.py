"""Frozen reconciliation policy — CRD Issue 5c, Component B.

The reconciliation policy is a committed transform input, frozen before any
corpus output exists (K step a0) and covered by the transform
source/configuration hash. It defines, exhaustively and deterministically:

* the closed set of exclusion reason codes and their eligibility;
* the permitted projection roles and their overlap semantics;
* the normalization/equivalence rules for coverage-content and duplicate checks.

Because this policy lives in committed source, it is frozen by construction; the
pipeline records the hash it applied (K a3) and the gate (I) rejects any
reconciliation that applied a different policy hash — that is how "policy authored
after output" is caught.

The reconciler applies *only* this policy. It may not invent exclusion reasons,
roles, or overlap permissions after examining output (Component D).
"""

from __future__ import annotations

import unicodedata

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.models import (
    ExclusionReason,
    Leaf,
    LeafType,
    ProjectionRole,
    ReconciliationPolicy,
)

POLICY_VERSION = "5c-corpus-policy-1"
NORMALIZATION_VERSION = "nfkc-ws-1"

# ---------------------------------------------------------------------------
# Normalization / equivalence (frozen identity: NORMALIZATION_VERSION)
# ---------------------------------------------------------------------------

_LIGATURES = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "−": "-",  # minus sign → hyphen-minus
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",  # en dash
    "—": "-",  # em dash
}


def normalize(text: str) -> str:
    """Deterministic content normalization for coverage matching.

    NFKC-folds ligatures/typographic punctuation, collapses whitespace runs to a
    single space, and strips ends. Case is preserved — content fidelity depends
    on it. This is the ``normalization_version`` identity.
    """
    folded = "".join(_LIGATURES.get(ch, ch) for ch in text)
    folded = unicodedata.normalize("NFKC", folded)
    return " ".join(folded.split())


def equivalence_key(text: str) -> str:
    """Equivalence key for duplicate detection (adds case folding to normalize).

    Two outputs are policy-equivalent — hence a duplicate unless a genuinely
    policy-distinct role authorizes repetition — when their equivalence keys
    match. Relabeling never changes the key, so it can never legalize a duplicate.
    """
    return normalize(text).casefold()


# ---------------------------------------------------------------------------
# Closed exclusion-reason set (Component B / Source-Unit Taxonomy)
# ---------------------------------------------------------------------------

_EXCLUSION_REASONS: tuple[ExclusionReason, ...] = (
    ExclusionReason(
        code="running_header_footer",
        description=(
            "Repeated running header/footer margin line (page number and the "
            "'System Reference Document 5.2.1' running footer)."
        ),
        eligible_leaf_types=(LeafType.HEADER_FOOTER,),
    ),
    ExclusionReason(
        code="toc_or_index_listing",
        description=(
            "Table-of-contents or index listing that merely duplicates a "
            "substantive entry's heading."
        ),
        eligible_leaf_types=(LeafType.HEADING, LeafType.PARAGRAPH),
    ),
    ExclusionReason(
        code="decorative",
        description="Decorative, non-substantive content.",
        eligible_leaf_types=(LeafType.CAPTION,),
    ),
)

# ---------------------------------------------------------------------------
# Permitted projection roles (Component B/D)
# ---------------------------------------------------------------------------

_PROJECTION_ROLES: tuple[ProjectionRole, ...] = (
    ProjectionRole(
        name="authoritative",
        description=(
            "The single authoritative representation of a represented leaf. "
            "No overlapping coverage of the same subspan is permitted."
        ),
        allows_overlap=False,
    ),
    ProjectionRole(
        name="attribution_repeat",
        description=(
            "Required CC BY 4.0 attribution text that legitimately recurs. This "
            "is the only role that authorizes intentional repeated/overlapping "
            "coverage, and only for attribution leaves."
        ),
        allows_overlap=True,
    ),
)

FROZEN_POLICY = ReconciliationPolicy(
    policy_version=POLICY_VERSION,
    normalization_version=NORMALIZATION_VERSION,
    exclusion_reasons=_EXCLUSION_REASONS,
    projection_roles=_PROJECTION_ROLES,
)

AUTHORITATIVE_ROLE = "authoritative"
ATTRIBUTION_ROLE = "attribution_repeat"


def policy_payload(policy: ReconciliationPolicy) -> dict[str, object]:
    """Canonical, hashable representation of a policy (no in-memory addresses)."""
    return {
        "policy_version": policy.policy_version,
        "normalization_version": policy.normalization_version,
        "exclusion_reasons": [
            {
                "code": r.code,
                "description": r.description,
                "eligible_leaf_types": [t.value for t in r.eligible_leaf_types],
            }
            for r in policy.exclusion_reasons
        ],
        "projection_roles": [
            {
                "name": r.name,
                "description": r.description,
                "allows_overlap": r.allows_overlap,
            }
            for r in policy.projection_roles
        ],
    }


def policy_hash(policy: ReconciliationPolicy) -> str:
    """SHA-256 of the policy's canonical payload."""
    return hash_obj(policy_payload(policy))


# ---------------------------------------------------------------------------
# Deterministic exclusion predicates (Component D policy application)
# ---------------------------------------------------------------------------

_TOC_INDEX_LABELS = ("table of contents", "index")


def exclusion_reason_for(
    leaf: Leaf, container_labels: dict[str, str]
) -> ExclusionReason | None:
    """Return the frozen policy's exclusion reason for *leaf*, or None.

    This is the single deterministic policy application shared by the transform
    (which skips excluded leaves — K a2) and the reconciler (which assigns the
    final disposition — K a3), so the two can never disagree. A leaf with no
    reason is represented; a leaf the transform failed to represent yet matches
    no reason is left unresolved by the reconciler.
    """
    if leaf.leaf_type is LeafType.HEADER_FOOTER:
        return FROZEN_POLICY.reason("running_header_footer")
    path_labels = " ".join(
        container_labels.get(cid, "").casefold() for cid in leaf.container_path
    )
    if any(tag in path_labels for tag in _TOC_INDEX_LABELS) and leaf.leaf_type in (
        LeafType.HEADING,
        LeafType.PARAGRAPH,
    ):
        return FROZEN_POLICY.reason("toc_or_index_listing")
    return None
