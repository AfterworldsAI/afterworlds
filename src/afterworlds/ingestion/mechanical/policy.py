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

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

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
    "policy_meaning_violations",
    "policy_transition_violations",
    "prose_retention_reason_for",
    "semantic_policy_hash",
    "semantic_policy_payload",
]

if TYPE_CHECKING:  # pragma: no cover - imported for annotations only
    from afterworlds.ingestion.mechanical.representation import RepresentationDraft

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


def policy_transition_violations(
    transitions: Sequence[PolicyTransitionRecord], declared: tuple[str, str]
) -> list[str]:
    """Violations of a loaded policy-transition chain against the registry.

    The loader establishes that each record is well-formed and that the step it
    names is registered. That is a claim about each record alone, and says
    nothing about the sequence they form or about the artifact carrying them.
    Without this, a file declaring ``5d-semantic-policy-1`` while carrying a
    ``1 -> 2`` record loads clean: every individual record is authorized, and
    the artifact's own declaration contradicts all of them.

    Four properties, the same ones :func:`~.schema_lift.lift_chain_violations`
    checks, minus the proof extent :class:`PolicyTransitionRecord` deliberately
    does not carry:

    1. **Registered.** The source pair is a key in :data:`POLICY_TRANSITIONS`
       and the registered step's id and destination agree with the record.
    2. **Continuous, oldest first.** Each record's destination is the next
       record's source.
    3. **Terminal.** The last record's destination is the policy the artifact
       *declares*. Evidence ending elsewhere describes a different artifact.
    4. **Non-repeating.** No transition appears twice; a succession is crossed
       once.

    There is no policy counterpart to the schema regime's per-batch anchor, so
    there is no "crossed from somewhere nothing was reviewed under" rule here:
    a batch records the policy it was accepted under only through the artifact's
    declaration, and inventing a per-batch policy anchor would be asserting
    review history the seven accepted batches never stated.

    **Empty is legal.** The committed artifact has crossed nothing, so it has
    no evidence to carry and property 3 does not apply to it.
    """
    findings: list[str] = []
    if not transitions:
        return findings

    seen: set[tuple[str, str, str, str]] = set()
    for index, record in enumerate(transitions):
        at = f"policy_transitions[{index}] ({record.transition_id})"
        source = (record.from_version, record.from_hash)
        registered = POLICY_TRANSITIONS.get(source)
        if registered is None:
            findings.append(
                f"{at}: no transition is registered from {record.from_version!r} "
                f"({record.from_hash}); this succession was never authorized"
            )
        elif (registered.transition_id, registered.to_version, registered.to_hash) != (
            record.transition_id,
            record.to_version,
            record.to_hash,
        ):
            findings.append(
                f"{at}: the registered transition from {record.from_version!r} "
                f"is {registered.transition_id!r} to {registered.to_version!r} "
                f"({registered.to_hash}), not {record.transition_id!r} to "
                f"{record.to_version!r} ({record.to_hash})"
            )

        crossing = (*source, record.to_version, record.to_hash)
        if crossing in seen:
            findings.append(
                f"{at}: this transition is already recorded; a succession is "
                "crossed once"
            )
        seen.add(crossing)

        if index:
            previous = transitions[index - 1]
            if (previous.to_version, previous.to_hash) != source:
                findings.append(
                    f"{at}: does not continue the previous record, which ended "
                    f"at {previous.to_version!r} ({previous.to_hash}); policy "
                    "evidence is an ordered chain, oldest first"
                )

    last = transitions[-1]
    if (last.to_version, last.to_hash) != declared:
        findings.append(
            f"policy_transitions[{len(transitions) - 1}] ({last.transition_id}): "
            f"the chain ends at {last.to_version!r} ({last.to_hash}), but the "
            f"artifact declares {declared[0]!r} ({declared[1]})"
        )
    return findings


def prose_retention_codes(version: str = SEMANTIC_POLICY_VERSION) -> frozenset[str]:
    """The retention reasons *version*'s catalog admits.

    Empty under ``5d-semantic-policy-1``, which has no retention catalog at all
    — the distinction arrived with the Owner Decision of 2026-09-16. Derived
    from :func:`semantic_policy_payload` rather than restated, so a historical
    version answers with the catalog its recorded hash covers, and an
    unrecognized version raises there rather than resolving to an empty set
    that would read as "this policy admits nothing" instead of "nobody knows
    what this policy is". Callers that must report rather than refuse handle
    that distinction themselves; :func:`policy_meaning_violations` does.
    """
    payload = semantic_policy_payload(version)
    reasons = payload.get("prose_retention_reasons", ())
    assert isinstance(reasons, Sequence)
    return frozenset(str(r["code"]) for r in reasons)


def policy_meaning_violations(
    draft: RepresentationDraft, policy_version: str
) -> list[str]:
    """Meaning *draft* carries that its declared *policy* cannot state.

    The policy half of the invariant
    :func:`~.representation.declared_meaning_violations` states for the schema
    half, and it is a genuinely separate question rather than a second spelling
    of one. The two contracts are versioned independently on purpose: a schema
    says which *shapes* a payload may exhibit, a policy says which *reason
    codes* are closed. Schema 12 mints the ``prose_retention_reason_code`` key;
    ``5d-semantic-policy-2`` mints the catalog its values come from. Either can
    move without the other, so a schema-12 artifact declaring
    ``5d-semantic-policy-1`` is perfectly legal — it simply may not state a
    retention reason, because under that policy there is no such reason to
    state.

    Nothing here checks the *irreducibility* catalog per version: both
    recognized policies carry it identically, element for element, so a
    version-keyed rule over it would assert a distinction that does not exist.
    :mod:`~.validation` checks its closure, which is the rule that is real.

    Reported rather than raised, like every other ``*_violations`` reader here,
    so a caller decides whether this is a gate finding or a refusal.

    **An unrecognized declaration is answered, not escalated.** A file declares
    its own policy and the loader's job is to report honestly what it says, so
    a version this build does not know legitimately reaches here — the gate and
    ``validate_policy_binding`` are what refuse the declaration itself, and
    raising here would turn their finding into a crash on the way to it.
    Nothing is waved through: with no catalog to read, *every* stated retention
    code is unconfirmable, which is a violation reported in exactly those terms
    rather than as the false claim that a known catalog excluded it. A draft
    that states no retention code at all is unaffected, which is why a
    schema-11 artifact under a policy nobody recognizes still loads exactly as
    it did before schema 12.
    """
    try:
        admitted: frozenset[str] | None = prose_retention_codes(policy_version)
    except ValueError:
        admitted = None

    def unstatable(code: str | None) -> str | None:
        if code is None:
            return None
        if admitted is None:
            return (
                f"declares semantic policy {policy_version!r}, which this build "
                f"does not recognize, so its retention catalog cannot be shown "
                f"to admit {code!r}"
            )
        if code not in admitted:
            return (
                f"declares semantic policy {policy_version!r}, whose retention "
                f"catalog does not admit {code!r}"
            )
        return None

    findings: list[str] = []
    for component in draft.components:
        if reason := unstatable(component.prose_retention_reason_code):
            findings.append(
                f"component {component.record_key}/{component.semantic_key}: " + reason
            )
    for binding in draft.prose_bindings:
        if reason := unstatable(binding.prose_retention_reason_code):
            findings.append(
                f"prose binding {binding.record_key}/{binding.component_key}: " + reason
            )
    return findings
