"""Semantic accounting types — CRD Issue 5d, span-exact classification.

ADR-005d Decision 2 partitions every 5c ``REPRESENTED`` leaf into accepted
semantic spans. This module holds the frozen value types for that partition and
for the acceptance evidence that makes a span publishable. It holds no policy
(see :mod:`policy`) and performs no validation (see :mod:`accounting`).

Two separations are load-bearing and appear here as distinct fields rather than
as one status:

* **semantic disposition** — what the text *is* (substantive, supporting,
  non-mechanical, unresolved);
* **review state** — whether a human accepted that claim. A proposal is not an
  acceptance, and silence is never acceptance (#137 contract 2).

Reviewer identity, acceptance timestamps, and comments are audit metadata: they
travel with the record but are excluded from every identity payload, so a
re-review that changes nothing semantic does not mint a new projection
(#137 acceptance criterion 11).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticDisposition(StrEnum):
    """The mechanical role of one accepted span (#137 contract 2).

    ``UNRESOLVED`` is an honest "cannot classify safely yet" and blocks
    publication; it is not a bucket for text nobody looked at, which is what
    a missing span means instead.
    """

    SUBSTANTIVE = "substantive"
    # Material that identifies, limits, explains, exemplifies, or contextualizes
    # a mechanic. Form does not decide this: a heading may be supporting
    # authority here or non-mechanical under a closed reason there, depending on
    # what it actually does.
    SUPPORTING_AUTHORITY = "supporting_authority"
    NON_MECHANICAL = "non_mechanical"
    UNRESOLVED = "unresolved"


class ReviewState(StrEnum):
    """Whether a proposal has been explicitly accepted by review."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"


class ComponentHandling(StrEnum):
    """How a publishable component's meaning is represented (#137 contract 2).

    ``PROSE_BOUND`` is an affirmative judgement backed by exactly one closed
    reason — never a backlog state and never a synonym for "the adapter cannot
    execute it". Since schema 12 there are two catalogs it may be backed by,
    and which one applies is itself the judgement: an
    :class:`IrreducibilityReason` says the meaning requires judgement to apply,
    and a :class:`ProseRetentionReason` says the meaning is reducible but no
    identified code-owned use in play, explanation or correction needs a
    separate structured field for it. Stating the first for the second is the
    relabelling ADR-005d forbids (Owner Decision 2026-09-16); stating both is a
    contradiction, and :mod:`~afterworlds.ingestion.mechanical.validation`
    refuses each.
    """

    STRUCTURED = "structured"
    PROSE_BOUND = "prose_bound"
    MIXED = "mixed"


class ReviewUnitKind(StrEnum):
    """The coherent source boundary one review unit was reviewed at.

    ADR-005d Decision 2 names exactly these three: "meaningful section, entry,
    or table boundaries". A closed catalog rather than free text, and carried in
    the semantic policy payload beside the reason catalogs, because a unit's
    kind is a claim stated in accepted authority — the boundary a reviewer says
    they read the source at — and a build that admitted a fourth kind would be
    validating coverage under a contract nothing recorded.
    """

    SECTION = "section"
    ENTRY = "entry"
    TABLE = "table"


@dataclass(frozen=True)
class ReviewUnitKindEntry:
    """One entry of the closed, identity-bound review-unit kind catalog."""

    code: str
    description: str


@dataclass(frozen=True)
class NonMechanicalReason:
    """One entry of the closed, identity-bound non-mechanical reason catalog."""

    code: str
    description: str


@dataclass(frozen=True)
class IrreducibilityReason:
    """One entry of the closed prose-bound irreducibility catalog."""

    code: str
    description: str


@dataclass(frozen=True)
class ProseRetentionReason:
    """One entry of the closed prose-retention catalog.

    Distinct from :class:`IrreducibilityReason` and never interchangeable with
    it: an irreducibility reason claims the meaning cannot be reduced, a
    retention reason claims only that nothing identified needs it reduced.
    """

    code: str
    description: str


@dataclass(frozen=True)
class SemanticSpan:
    """One accepted-or-proposed classification of an exact leaf subspan.

    ``char_start``/``char_end`` are a half-open range over the leaf's canonical
    text, so a leaf's spans form a gap-free non-overlapping partition
    (validated in :mod:`accounting`, not here).

    ``span_id`` is content-derived from the leaf and range, so an unrelated
    edit elsewhere in the corpus never churns it (#137 acceptance criterion 6).
    """

    span_id: str
    leaf_id: str
    char_start: int
    char_end: int
    disposition: SemanticDisposition
    review_state: ReviewState
    # Required exactly when disposition is NON_MECHANICAL; must name a code in
    # the frozen catalog.
    non_mechanical_reason_code: str | None = None


@dataclass(frozen=True)
class ExpectedRule:
    """One rule a reviewer read in the source and requires to have a home.

    Derived from the source during review and checked against the
    representation — never read back out of it. ADR-005d Decision 2 is explicit
    that expected entries and table rows "must be derived from the source and
    checked in review, not inferred from the output being tested", which is why
    nothing in this codebase derives an :class:`ExpectedRule` from a
    ``RepresentationDraft``. An expectation that an omission could not violate
    is not coverage evidence.

    Granularity is the component plus, where the reviewer decided it, the
    structured family that must carry the meaning, plus the exact source text
    the rule was read from. The component and family alone cannot carry the
    obligation: one paragraph may state two exceptions of one family in one
    component, and a check that asked only whether *some* fact of that family
    survived would pass while one of them was dropped. ``source_span_ids`` is
    what tells them apart, and it costs the reviewer nothing to state — the
    spans are the ones already being proposed and accepted.

    Still nothing here predicts a fact identity. The expectation names source
    text; the build is what decides which structure carries it.
    """

    record_key: str
    component_key: str
    #: The structured family that must carry this rule, or ``None`` when the
    #: reviewer accepted exact governing prose as its home. ``None`` is a
    #: judgement, not an absence: it says the component must exist and must be
    #: prose-bound or mixed, so dropping the passage still fails.
    fact_family: str | None = None
    #: The accepted spans, inside this unit's leaves, whose text states this
    #: rule. Required in substance — an expectation naming none is reported as
    #: a violation rather than refused at construction, because an inventory
    #: that cannot be read cannot be reported on. Several spans are legitimate:
    #: a rule stated across two sentences is one rule, and **each named span
    #: is required, not an alternative** — every one of them must have the
    #: appropriate actual authority home, or the rule is reported as unmet
    #: naming exactly the spans that do not.
    #:
    #: A structure may legitimately be the home of more than one expectation —
    #: one shared representation of a statement the source repeats — because a
    #: fact may carry a provenance claim to each span that states it.
    source_span_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupportingGroup:
    """Source text inside a unit that explains authority rather than stating it.

    The Owner Decision of 2026-09-16 removed the obligation to partition every
    character of a reviewed leaf, not the obligation to say what the reviewer
    decided about the text. Supporting material is the case that decision makes
    easiest to lose: an example, a worked calculation, or a "see also" is not a
    rule, so nothing requires it to have a home, and under unit accounting it
    could vanish from the record entirely.

    So it keeps one decision per *group* — not per character and not per
    fragment — naming which leaves it covers and which authority it supports.
    ``supports_component_key`` is empty when the group supports the record as a
    whole, which is what a section's introductory example usually does.
    """

    leaf_ids: tuple[str, ...]
    supports_record_key: str
    supports_component_key: str = ""


@dataclass(frozen=True)
class ExcludedGroup:
    """Source text inside a unit the reviewer decided carries no mechanic.

    The sibling of :class:`SupportingGroup`, and deliberately the same shape:
    exact leaf membership plus one honest decision about it. ``reason`` is free
    prose, one sentence per group, because the amendment asks for "a reason for
    the applicable group" and a closed catalog here would force a reviewer to
    pick the nearest wrong word. The excluded text remains in the immutable 5c
    source either way.
    """

    leaf_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ReviewUnit:
    """One coherent stretch of source that a human actually reviewed.

    ADR-005d Decision 2, as amended by the Owner Decision of 2026-09-16. The
    inventory of units is the review scope and the coverage evidence; it is not
    a second copy of the source, and a unit "need not become a record or
    component" (Decision 3). What it must do is resolve to *exact* source
    membership, which is why ``leaf_ids`` names 5c leaves rather than a title
    or a page range.

    A unit is the alternative to partitioning every character interval of a
    leaf into accepted spans: the amendment says such rows "are not required",
    while existing accepted partitions "remain valid and are not rewritten".
    Both therefore count as coverage, and a leaf may be covered by either.
    Exact subspans remain where a fact, rule, qualification, citation, or
    correction needs one.

    **A unit relaxes the partition only to the extent it accounts for itself.**
    Three kinds of decision, and every leaf the unit names must be reached by at
    least one of them: a rule read from source text inside the unit, a
    supporting group, or an excluded group. Accounting at group granularity is
    the whole point of the amendment — one decision may cover a whole coherent
    group, and nothing here asks for a row per character or per extraction
    fragment. What it does not permit is a unit that names leaves and decides
    nothing about them: blank accounting is not review, and accepting it as
    coverage would drop exactly the heading, example and explanation links the
    span partition used to hold.

    Audit metadata — who reviewed it, when, and their comments — is deliberately
    absent. A unit states what was reviewed and what must be there, and those
    are the only parts that bear on identity.
    """

    unit_id: str
    kind: ReviewUnitKind
    #: Exact 5c leaf membership. Held sorted in every payload so that two
    #: reviewers naming the same leaves in different orders record one unit.
    leaf_ids: tuple[str, ...]
    expected_rules: tuple[ExpectedRule, ...] = ()
    supporting_groups: tuple[SupportingGroup, ...] = ()
    excluded_groups: tuple[ExcludedGroup, ...] = ()


@dataclass(frozen=True)
class SemanticDiffEntry:
    """One span's transition under a batch acceptance.

    ``prior_*`` is ``None`` when the batch accepted a claim that had no prior
    proposed disposition, which is different from a batch that changed one.
    """

    span_id: str
    prior_disposition: SemanticDisposition | None
    prior_reason_code: str | None
    accepted_disposition: SemanticDisposition
    accepted_reason_code: str | None


@dataclass(frozen=True)
class AcceptanceBatch:
    """A rule-scoped batch acceptance (#137 contract 2).

    Batch acceptance is what makes full-corpus review tractable, but it has to
    stay auditable afterwards, which means retaining what was accepted — not a
    recipe for recomputing it later:

    * ``rule`` explains *how* the batch was selected. It is evidence, not
      authority, and it is never re-run: a selector re-evaluated against
      changed inputs would resolve to a different set than the reviewer saw.
    * ``resolved_scope`` is the exact span set the reviewer accepted.
    * ``diff`` is the canonical semantic diff itself, retained in full.
    * ``semantic_diff_hash`` identifies and verifies that diff; it never
      substitutes for it.
    * ``proposal_identity`` is the content-derived identity of the exact
      :class:`~afterworlds.ingestion.mechanical.proposal.MechanicalProposal`
      that was reviewed.

    **Scope and proposal identity answer different questions, and both are
    needed.** ``resolved_scope`` and ``diff`` scope the *classification*
    acceptance — which spans, and what their disposition and reason became.
    They say nothing about records, components, facts, prose bindings,
    relationships, references, or provenance, because two proposals can state
    identical span dispositions while stating completely different mechanical
    authority. ``proposal_identity`` closes exactly that gap: it identifies the
    complete proposed representation the reviewer had in front of them, so the
    retained evidence establishes that the accepted authority is the authority
    somebody actually reviewed — not merely that some spans were accepted.

    All five fields are retained audit evidence. None reaches projection or
    oracle identity — see ``accounting.classification_payload`` — so
    re-reviewing an unchanged classification cannot remint a projection.
    """

    batch_id: str
    rule: str
    resolved_scope: tuple[str, ...]
    diff: tuple[SemanticDiffEntry, ...]
    semantic_diff_hash: str
    proposal_identity: str


@dataclass(frozen=True)
class AcceptanceRecord:
    """Evidence that one span's semantic claim was explicitly accepted.

    ``batch_id`` is ``None`` for an individually reviewed span and otherwise
    names an :class:`AcceptanceBatch`. ``reviewer`` and ``accepted_at`` record
    who took the acceptance action and when; both are required evidence of an
    explicit action, and neither reaches projection identity.
    """

    span_id: str
    batch_id: str | None
    reviewer: str
    accepted_at: str


@dataclass(frozen=True)
class ReviewUnitAcceptance:
    """Evidence that one :class:`ReviewUnit` was explicitly accepted.

    The exact sibling of :class:`AcceptanceRecord`, and deliberately a separate
    record rather than a field on :class:`AcceptanceBatch`. A unit is accepted
    by the same kind of action a span is — a named reviewer, at a named time,
    as part of a named batch — and giving it the same shape means the two
    halves of one acceptance are audited by the same rules instead of by a
    second mechanism that would eventually disagree.

    Without this, a batch that accepted only review units recorded nobody: its
    scope was empty, so it produced no :class:`AcceptanceRecord`, and the
    reviewer and timestamp handed to ``accept_proposal`` reached no retained
    evidence at all. It also carries the attribution a span-bearing batch
    already has — which action accepted *this* unit — which the merged
    inventory on its own cannot state.

    ``batch_id`` is ``None`` for an individually reviewed unit and otherwise
    names an :class:`AcceptanceBatch`, exactly as it is on the sibling: being
    audited by the same rules means having the same shape, and a ledger whose
    span acceptances predate batches has review-unit acceptances that do too.
    ``accept_proposal`` always names the batch it is taking, so every unit
    accepted through the production path carries its attribution.
    """

    unit_id: str
    batch_id: str | None
    reviewer: str
    accepted_at: str


@dataclass(frozen=True)
class ReferenceResolution:
    """A reviewed destination for one accepted reference that had none.

    Owner Decision of 2026-09-19 (ADR-005d Decision 7). An accepted reference
    whose ``target_record_key`` is empty is an honest unresolved obligation: the
    source authored the citation, review found no destination key it could state
    exactly, and erasing the citation to avoid the finding would lose source
    authority. Acceptance is append-only and keyed, so the destination cannot
    arrive as a second reference — ``representation.reference_target_key``
    includes the target, so a resolved sibling is a *different* key and the empty
    edge survives beside it, reported both unresolved and ambiguous.

    This record is the bounded resolution: it names the exact accepted citation
    by the four coordinates that identify it independently of its target, and
    the destination review approved. The original reference is not edited, and
    the seven accepted batches are not rewritten —
    ``reference_resolution.effective_representation`` derives the resolved view
    the build, gate, query and override paths see, while the accepted
    representation keeps stating exactly what each reviewer accepted.

    **Identity-bearing, and deliberately so.** A resolution changes what the
    accepted authority *means*: one reference now has a destination. Its
    sibling :class:`ReferenceResolutionAcceptance` carries who authorized it and
    when, which is evidence and reaches no identity — the same split
    :class:`ReviewUnit` and :class:`ReviewUnitAcceptance` already make.

    ``package_uuid`` and ``release_version`` restate the release this resolution
    was reviewed against. They are not redundant with the oracle's binding: they
    are what makes a resolution pasted into another release's artifact a
    mismatch rather than a silent re-application of a decision nobody made about
    that release.

    ``provenance_span_ids`` names the source spans the accepted citation's
    provenance claims cite, sorted. Review approved a destination *for a citation
    read out of exactly those spans*; if the accepted citation's provenance later
    cites others, this decision no longer describes it and must not be applied.
    """

    resolution_id: str
    from_record_key: str
    from_component_key: str
    source_text: str
    scope_key: str
    target_record_key: str
    package_uuid: str
    release_version: str
    provenance_span_ids: tuple[str, ...]

    def citation_key(self) -> tuple[str, str, str, str]:
        """The accepted citation this resolves, independently of its target.

        The first four elements of ``reference_target_key`` — which is exactly
        the part of a reference's identity a resolution may not change.
        """
        return (
            self.from_record_key,
            self.from_component_key,
            self.source_text,
            self.scope_key,
        )


@dataclass(frozen=True)
class ReferenceResolutionAcceptance:
    """Evidence that one :class:`ReferenceResolution` was explicitly authorized.

    The third instance of the shape :class:`AcceptanceRecord` and
    :class:`ReviewUnitAcceptance` already have, for the same reason: a
    resolution is taken by a named person, at a named time, under a named
    authority, and auditing it by the same rules means giving it the same shape.

    ``authorized_by`` and ``authorization_reference`` are the pair that keeps a
    machine suggestion from becoming authority implicitly. A resolution is only
    applied where the record says who decided it and cites the decision —
    Owner Decision, review, or issue — rather than inheriting the acceptance of
    the batch that authored the unresolved citation.
    """

    resolution_id: str
    authorized_by: str
    authorization_reference: str
    reviewer: str
    resolved_at: str


@dataclass(frozen=True)
class ClassificationLedger:
    """The complete accepted semantic accounting for one bound 5c release.

    This is a committed, meaning-bearing input to the build — never a product
    of it (#137 contract 4: the oracle is not regenerated from the output it
    checks).

    The ledger carries both the accepted semantic *result* (``spans``) and the
    review evidence that produced it (``batches``, ``acceptances``). Only the
    result is identity-bearing; the evidence is immutable, persisted, and
    reconstructable for audit, but two ledgers that reviewed their way to the
    same accepted classification are the same authority.

    ``policy_version`` and ``policy_hash`` are the ledger's own declaration of
    the semantic policy it was accepted under. They are retained and travel
    with the projection, so a historical projection states the policy it used
    instead of being reinterpreted under whatever policy code is current later;
    the build verifies the declaration against the committed policy and fails
    when they disagree.
    """

    package_uuid: str
    release_version: str
    policy_version: str
    policy_hash: str
    spans: tuple[SemanticSpan, ...]
    batches: tuple[AcceptanceBatch, ...]
    acceptances: tuple[AcceptanceRecord, ...]
    #: Empty for every ledger accepted before review units existed, which is all
    #: seven accepted batches. The canonical evidence payload omits the key when
    #: it is empty, so their committed bytes and recorded persisted-state
    #: digests are unchanged.
    review_unit_acceptances: tuple[ReviewUnitAcceptance, ...] = ()
