"""Frozen semantic policy — CRD Issue 5d.

The semantic policy is a committed build input, frozen in source before any
projection output exists, exactly as CRD Issue 5c freezes its reconciliation
policy. It defines, exhaustively:

* the closed non-mechanical reason catalog;
* the closed prose-bound irreducibility catalog;
* the closed prose-retention reason catalog; and
* the canonicalization rules under which spans and payloads are compared.

Because it lives in committed source it is frozen by construction, and the
projection records the policy hash it applied. A reason code invented after
looking at output cannot pass: it is not in the catalog, so the span carrying
it fails accounting.

The policy is *versioned*, and every version this build recognizes is
reproducible here. ``5d-semantic-policy-1`` is what the seven accepted batches
were accepted under; ``5d-semantic-policy-2`` adds the prose-retention catalog
required by the Owner Decision of 2026-09-16 (ADR-005d, #137 contract 2), which
distinguishes prose retained because judgement is required from prose retained
because no separate structured use was identified. A historical payload is
reproduced key for key so its recorded hash still verifies: a superseded policy
keeps its original meaning rather than being reinterpreted under current code.

Canonicalization deliberately reuses CRD Issue 5c's ``normalize`` rather than
defining a second text-equivalence rule. Two normalization rules that drift
apart would let a span "cover" text the corpus layer considers different.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.policy import NORMALIZATION_VERSION, normalize
from afterworlds.ingestion.mechanical.models import (
    IrreducibilityReason,
    NonMechanicalReason,
    ProseRetentionReason,
)

__all__ = [
    "IRREDUCIBILITY_REASONS",
    "NON_MECHANICAL_REASONS",
    "POLICY_TRANSITIONS",
    "PROSE_RETENTION_REASONS",
    "SEMANTIC_POLICY_VERSION",
    "PolicyTransition",
    "PolicyTransitionRecord",
    "UnknownPolicyTransitionError",
    "accepted_policy_contracts",
    "canonical_span_text",
    "irreducibility_reason_for",
    "non_mechanical_reason_for",
    "policy_transition_for",
    "prose_retention_reason_for",
    "semantic_policy_hash",
    "semantic_policy_payload",
]

POLICY_1_VERSION = "5d-semantic-policy-1"
POLICY_2_VERSION = "5d-semantic-policy-2"

#: The policy this build applies to new proposals.
SEMANTIC_POLICY_VERSION = POLICY_2_VERSION

#: Pinned literally, for the same reason every representation-schema hash is:
#: a recognized contract must be a fact about a policy that was *committed*,
#: not about whatever the catalogs in this file currently hash to. Computing
#: them here would make the registry agree with any future edit, which is the
#: one thing a version registry exists to refuse.
POLICY_1_HASH = "e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454"  # noqa: E501  # pragma: allowlist secret
POLICY_2_HASH = "ce8464f8c9013a849ad8f73bacbac0305b54861daec361883f9b06e5be289ad3"  # noqa: E501  # pragma: allowlist secret

# ---------------------------------------------------------------------------
# Closed catalogs (#137 contract 2)
# ---------------------------------------------------------------------------

# Headings, examples, cross-references, explanatory clauses, GameMaster
# guidance, and repeated wording are deliberately *absent* here. They are not
# blanket non-mechanical categories (#137 contract 2) and may well be
# supporting authority, so nothing may be discarded merely for having one of
# those forms. Each instance is classified from its actual role: a particular
# heading or repeated item can still be non-mechanical under a valid closed
# reason such as ``navigation_only`` when its content supports that.
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

#: Why exact governing prose was retained when no judgement is required of the
#: reader — the second half of the distinction #137 contract 2 and ADR-005d
#: require a versioned policy change to make.
#:
#: **Deliberately a separate catalog, and deliberately not a sixth
#: irreducibility reason.** The six entries above each assert that the meaning
#: *cannot* be reduced; this one asserts only that no identified code-owned use
#: needs it reduced today. Relabelling reducible meaning with an irreducibility
#: code would make the catalog say something false about the source, and would
#: silently change what the six existing codes mean for the batches already
#: accepted under them.
PROSE_RETENTION_REASONS: tuple[ProseRetentionReason, ...] = (
    ProseRetentionReason(
        code="no_identified_structured_use",
        description=(
            "The meaning is reducible, but no identified code-owned use in "
            "play, explanation, or correction requires a separate structured "
            "field, so the exact governing prose carries it."
        ),
    ),
)

_NON_MECHANICAL_BY_CODE = {r.code: r for r in NON_MECHANICAL_REASONS}
_IRREDUCIBILITY_BY_CODE = {r.code: r for r in IRREDUCIBILITY_REASONS}
_PROSE_RETENTION_BY_CODE = {r.code: r for r in PROSE_RETENTION_REASONS}


def non_mechanical_reason_for(code: str) -> NonMechanicalReason | None:
    """Return the catalog entry for *code*, or ``None`` when it is not closed."""
    return _NON_MECHANICAL_BY_CODE.get(code)


def irreducibility_reason_for(code: str) -> IrreducibilityReason | None:
    """Return the catalog entry for *code*, or ``None`` when it is not closed."""
    return _IRREDUCIBILITY_BY_CODE.get(code)


def prose_retention_reason_for(code: str) -> ProseRetentionReason | None:
    """Return the catalog entry for *code*, or ``None`` when it is not closed.

    Always ``None`` for an irreducibility code, and vice versa: the two
    catalogs are disjoint, which is what lets a component's single recorded
    reason say which of the two claims is being made.
    """
    return _PROSE_RETENTION_BY_CODE.get(code)


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


def semantic_policy_payload(
    version: str = SEMANTIC_POLICY_VERSION,
) -> dict[str, object]:
    """Canonical, identity-bearing payload of a recognized semantic policy.

    Policy 1's payload is reproduced with *exactly* the keys it was hashed
    under. The prose-retention catalog is a policy-2 key and is absent from
    policy 1 rather than emitted empty: an added key changes the hash, and a
    superseded policy whose recorded hash no longer verifies is not a
    superseded policy — it is a lost one, and every batch accepted under it
    becomes unreadable.

    Both versions share the two catalogs above, element for element. That is
    what makes the 1 → 2 transition a strict superset rather than a
    redescription, and it is asserted in tests rather than assumed here.
    """
    if version not in {POLICY_1_VERSION, POLICY_2_VERSION}:
        raise ValueError(f"unrecognized semantic policy version {version!r}")
    payload: dict[str, object] = {
        "semantic_policy_version": version,
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
    if version == POLICY_2_VERSION:
        payload["prose_retention_reasons"] = [
            {"code": r.code, "description": r.description}
            for r in PROSE_RETENTION_REASONS
        ]
    return payload


def semantic_policy_hash(version: str = SEMANTIC_POLICY_VERSION) -> str:
    """SHA-256 of a recognized semantic policy payload."""
    return hash_obj(semantic_policy_payload(version))


# ---------------------------------------------------------------------------
# Recognized policy versions and their authorized successions
# ---------------------------------------------------------------------------


class UnknownPolicyTransitionError(ValueError):
    """No transition is registered for this exact policy succession."""

    def __init__(self, source: tuple[str, str], target: tuple[str, str]) -> None:
        super().__init__(
            f"no authorized semantic-policy transition from {source[0]!r} "
            f"({source[1]}) to {target[0]!r} ({target[1]}). A policy succession "
            "must be registered for its exact version and hash pair; a later "
            "version is not evidence that accepted authority may cross into it"
        )
        self.source = source
        self.target = target


@dataclass(frozen=True)
class PolicyTransition:
    """One authorized semantic-policy succession, keyed by its source pair.

    ``rationale`` records *why* accepted authority may cross, and in particular
    what the transition promises about the older policy's codes. It is evidence
    and never participates in any identity.
    """

    transition_id: str
    from_version: str
    from_hash: str
    to_version: str
    to_hash: str
    rationale: str


#: Every authorized succession. Explicit rows, never a rule over version order.
POLICY_TRANSITIONS: dict[tuple[str, str], PolicyTransition] = {
    (POLICY_1_VERSION, POLICY_1_HASH): PolicyTransition(
        transition_id="5d-policy-1-to-2",
        from_version=POLICY_1_VERSION,
        from_hash=POLICY_1_HASH,
        to_version=POLICY_2_VERSION,
        to_hash=POLICY_2_HASH,
        rationale=(
            "Policy 2 is a strict superset of policy 1: the non-mechanical and "
            "irreducibility catalogs are carried across element for element, "
            "with no code added, dropped, reordered, or redescribed, so every "
            "disposition and handling reason recorded under policy 1 means "
            "exactly what it meant when it was accepted. The transition adds "
            "one new closed catalog — prose retained with no identified "
            "structured use (Owner Decision 2026-09-16) — which no policy-1 "
            "acceptance can carry, because policy 1 admits no code from it."
        ),
    ),
}


@dataclass(frozen=True)
class PolicyTransitionRecord:
    """Evidence that an accepted artifact crossed a policy succession.

    Lives on the evidence half of ``AcceptedInputs``, beside
    :class:`~.schema_lift.SchemaLiftRecord`, and never on ``AcceptedOracle``:
    which policy an artifact was carried across is review process, and process
    is not identity-bearing (#137 acceptance criterion 11).

    It carries no counterpart to ``SchemaLiftRecord.verified_collections``,
    because a policy crossing proves nothing about this artifact's bytes. What
    it promises is a fact about the *policies* — that the carried catalogs are
    identical element for element — which is checked against the committed
    payloads themselves, not against whatever content happened to cross.
    """

    transition_id: str
    from_version: str
    from_hash: str
    to_version: str
    to_hash: str


def policy_transition_for(
    source: tuple[str, str], target: tuple[str, str]
) -> PolicyTransition:
    """The authorized transition from *source* to *target*, or fail closed.

    Both pairs are matched exactly, and only one registered step is followed.
    There is deliberately no multi-step walk: one succession exists, and a
    chain across two of them would need its own carried evidence rather than
    the concatenation of two rationales.

    # ponytail: single registered step; add a walk when a third policy version
    # makes a two-step crossing real.
    """
    transition = POLICY_TRANSITIONS.get(source)
    if transition is None or (transition.to_version, transition.to_hash) != target:
        raise UnknownPolicyTransitionError(source, target)
    return transition


def accepted_policy_contracts() -> frozenset[tuple[str, str]]:
    """Every ``(version, hash)`` pair this build accepts authority under.

    Two sources, and no rule over either: the policy this build *applies*, and
    the endpoints of the registered succession graph — accepted authority may
    legitimately still declare a source pair it has not been carried across,
    and one carried across declares the destination.
    """
    return frozenset(
        {(SEMANTIC_POLICY_VERSION, semantic_policy_hash())}
        | set(POLICY_TRANSITIONS)
        | {(t.to_version, t.to_hash) for t in POLICY_TRANSITIONS.values()}
    )
