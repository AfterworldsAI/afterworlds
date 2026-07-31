"""Frozen semantic policy — CRD Issue 5d.

The semantic policy is a committed build input, frozen in source before any
projection output exists, exactly as CRD Issue 5c freezes its reconciliation
policy. It defines, exhaustively:

* the closed non-mechanical reason catalog;
* the closed prose-bound irreducibility catalog; and
* the canonicalization rules under which spans and payloads are compared.

Because it lives in committed source it is frozen by construction, and the
projection records the policy hash it applied. A reason code invented after
looking at output cannot pass: it is not in the catalog, so the span carrying
it fails accounting.

Canonicalization deliberately reuses CRD Issue 5c's ``normalize`` rather than
defining a second text-equivalence rule. Two normalization rules that drift
apart would let a span "cover" text the corpus layer considers different.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.policy import NORMALIZATION_VERSION, normalize
from afterworlds.ingestion.mechanical.models import (
    IrreducibilityReason,
    NonMechanicalReason,
)

__all__ = [
    "IRREDUCIBILITY_REASONS",
    "NON_MECHANICAL_REASONS",
    "SEMANTIC_POLICY_VERSION",
    "canonical_span_text",
    "irreducibility_reason_for",
    "non_mechanical_reason_for",
    "semantic_policy_hash",
    "semantic_policy_payload",
]

SEMANTIC_POLICY_VERSION = "5d-semantic-policy-1"

# ---------------------------------------------------------------------------
# Closed catalogs (#137 contract 2)
# ---------------------------------------------------------------------------

# Headings, examples, cross-references, explanatory clauses, GameMaster
# guidance, and repeated wording are deliberately *absent* here: they are
# supporting authority, not blanket non-mechanical categories. Classifying them
# away is the failure mode this catalog exists to prevent.
NON_MECHANICAL_REASONS: tuple[NonMechanicalReason, ...] = (
    NonMechanicalReason(
        code="legal_licensing",
        description="Licence text, copyright, or legal notice.",
    ),
    NonMechanicalReason(
        code="navigation_only",
        description=(
            "Purely navigational material — running headers/footers, page "
            "numbers, table-of-contents entries — carrying no rule meaning."
        ),
    ),
    NonMechanicalReason(
        code="flavor_setting",
        description=(
            "Setting or flavour prose that neither states nor contextualizes a "
            "mechanic."
        ),
    ),
    NonMechanicalReason(
        code="governed_attribution",
        description=("Attribution already governed by the 5c corpus attribution role."),
    ),
    NonMechanicalReason(
        code="authoring_guidance",
        description=(
            "Guidance addressed to the document's authors or publishers rather "
            "than to play."
        ),
    ),
)

IRREDUCIBILITY_REASONS: tuple[IrreducibilityReason, ...] = (
    IrreducibilityReason(
        code="contextual_applicability",
        description=(
            "Whether the rule applies depends on fiction the projection cannot "
            "enumerate."
        ),
    ),
    IrreducibilityReason(
        code="subjective_judgment",
        description="Resolution requires a judgement call, not a computation.",
    ),
    IrreducibilityReason(
        code="open_ended_effect",
        description=(
            "The effect space is unbounded — any faithful reduction would narrow it."
        ),
    ),
    IrreducibilityReason(
        code="gamemaster_latitude",
        description="The source explicitly delegates the decision to the GM.",
    ),
    IrreducibilityReason(
        code="natural_language_exception",
        description=(
            "A natural-language exception that cannot be reduced without "
            "executable interpretation."
        ),
    ),
    IrreducibilityReason(
        code="fiction_dependent_consequence",
        description=(
            "The consequence follows from established fiction rather than from "
            "stated mechanics."
        ),
    ),
)

_NON_MECHANICAL_BY_CODE = {r.code: r for r in NON_MECHANICAL_REASONS}
_IRREDUCIBILITY_BY_CODE = {r.code: r for r in IRREDUCIBILITY_REASONS}


def non_mechanical_reason_for(code: str) -> NonMechanicalReason | None:
    """Return the catalog entry for *code*, or ``None`` when it is not closed."""
    return _NON_MECHANICAL_BY_CODE.get(code)


def irreducibility_reason_for(code: str) -> IrreducibilityReason | None:
    """Return the catalog entry for *code*, or ``None`` when it is not closed."""
    return _IRREDUCIBILITY_BY_CODE.get(code)


# ---------------------------------------------------------------------------
# Canonicalization + policy identity
# ---------------------------------------------------------------------------


def canonical_span_text(leaf_content: str, char_start: int, char_end: int) -> str:
    """Return the canonical text of a leaf subspan.

    Slicing happens on the raw leaf text so offsets stay meaningful against the
    persisted 5c leaf; normalization applies afterwards, so equivalence follows
    the corpus rule rather than a second one.
    """
    return normalize(leaf_content[char_start:char_end])


def semantic_policy_payload() -> dict[str, object]:
    """Canonical, identity-bearing payload of the frozen semantic policy."""
    return {
        "semantic_policy_version": SEMANTIC_POLICY_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "non_mechanical_reasons": [
            {"code": r.code, "description": r.description}
            for r in NON_MECHANICAL_REASONS
        ],
        "irreducibility_reasons": [
            {"code": r.code, "description": r.description}
            for r in IRREDUCIBILITY_REASONS
        ],
    }


def semantic_policy_hash() -> str:
    """SHA-256 of the frozen semantic policy payload."""
    return hash_obj(semantic_policy_payload())
