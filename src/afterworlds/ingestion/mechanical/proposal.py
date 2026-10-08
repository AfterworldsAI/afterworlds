"""Machine proposals — CRD Issue 5d, the authoring side of contract 2.

A tool may *propose* semantic classification and representation. Nothing a tool
emits is authority until a human explicitly accepts it, and "silence is not
acceptance" only means something if an unaccepted proposal physically cannot be
loaded as accepted authority.

**Structural incompatibility, not a flag and not a directory.** Placing
proposals in a different folder is a convention a mistake can defeat; a single
``accepted: false`` field is one edit away from a lie. So a proposal is a
different *shape* at every level:

===========================  ==================================================
Accepted artifact            Proposal artifact
===========================  ==================================================
``artifact_kind``            ``accepted_authority``   vs ``machine_proposal``
spans under                  ``spans``                vs ``proposed_spans``
each span carries            no ``review_state``      vs ``proposal_origin`` and
                             (accepted by                ``rationale`` per span
                             construction)
representation under         ``representation``       vs ``proposed_representation``
review evidence              ``acceptance`` (required)   absent entirely
per-record obligations       ``obligations`` (required)  absent entirely
===========================  ==================================================

:func:`~afterworlds.ingestion.mechanical.oracle.load_accepted_inputs` rejects a
proposal on ``artifact_kind`` first, for a legible error — but that check is not
what protects the boundary. Even with ``artifact_kind`` edited to lie, a
proposal is missing ``spans``, ``acceptance``, ``obligations``, and
``representation`` while carrying four keys the accepted loader does not
declare, and its strict ``_require`` rejects both halves of that. There is no
edit short of *rewriting the file into the accepted shape* — which is what
acceptance is — that turns one into the other.

The reverse direction is equally closed: this module never reads
``oracles/``, never writes anywhere, and produces no accepted type. It emits a
payload; a reviewer decides what happens next.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import derive_span_id, span_payload
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import (
    ReviewState,
    ReviewUnit,
    SemanticDisposition,
    SemanticSpan,
)

# The committed readers, reused rather than re-implemented. They are private
# because nothing outside a loader should be turning raw payloads into accepted
# shapes, and that stays true here: this module wraps them, it does not move or
# rename them, and a second hand-rolled reader is exactly the drift a retained
# proposal cannot afford.
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    _object_list,
    _representation,
    _require,
    _review_unit,
    _span,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ReleaseBinding,
    representation_payload,
    review_unit_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    RepresentationDraft,
    representation_schema_hash,
)

__all__ = [
    "PROPOSAL_ARTIFACT_KIND",
    "PROPOSAL_SCHEMA_VERSION",
    "PROPOSAL_SCHEMA_VERSION_2",
    "MechanicalProposal",
    "ProposalLoadError",
    "ProposedSpan",
    "load_proposal",
    "locate_span",
    "proposal_identity",
    "proposal_payload",
    "seed_proposal",
]

#: The discriminator every proposal declares. Deliberately not the accepted
#: artifact's kind, and deliberately not something an accepted loader accepts.
PROPOSAL_ARTIFACT_KIND = "machine_proposal"

#: Bumped when the proposal shape changes. Proposals are disposable review
#: material, so this version has no relationship to semantic policy identity and
#: never reaches a projection.
#:
#: This is the shape all seven accepted batches were reviewed under, and it
#: stays the default so their retained files keep deriving the proposal
#: identities their acceptances recorded.
PROPOSAL_SCHEMA_VERSION = "5d-proposal-1"

#: The shape that also states the review inventory the reviewer is being asked
#: to accept. A ``5d-proposal-1`` file cannot carry one: the units would be
#: outside the identity the acceptance records, which is exactly the gap this
#: version closes.
PROPOSAL_SCHEMA_VERSION_2 = "5d-proposal-2"

#: Exactly what each version's envelope declares. Version-specific, because a
#: strict key set is the only thing that makes undeclared envelope content
#: detectable at all: a key nobody reads is a claim nobody checked, and a
#: proposal is read precisely to establish what a human was shown.
_ENVELOPE: dict[str, tuple[str, ...]] = {
    PROPOSAL_SCHEMA_VERSION: (
        "artifact_kind",
        "proposal_schema_version",
        "proposal_origin",
        "release_binding",
        "semantic_policy_version",
        "semantic_policy_hash",
        "representation_schema",
        "proposed_spans",
        "proposed_representation",
    ),
    PROPOSAL_SCHEMA_VERSION_2: (
        "artifact_kind",
        "proposal_schema_version",
        "proposal_origin",
        "release_binding",
        "semantic_policy_version",
        "semantic_policy_hash",
        "representation_schema",
        "proposed_spans",
        "proposed_representation",
        "proposed_review_units",
    ),
}


@dataclass(frozen=True)
class ProposedSpan:
    """One span a tool suggests, with why it suggested it.

    ``rationale`` and ``origin`` exist for the reviewer, and they are the point:
    a reviewer accepting a batch is accepting *claims*, and a claim with no
    stated basis is not reviewable. They also make the proposal shape
    permanently distinct from an accepted span, which carries neither.
    """

    span: SemanticSpan
    origin: str
    rationale: str


@dataclass(frozen=True)
class MechanicalProposal:
    """One tool's complete suggestion for one bound 5c release.

    Carries no obligations and no acceptance evidence — neither exists until a
    human acts. Carrying an empty version of either would be the proposal
    claiming a shape it has not earned.
    """

    binding: ReleaseBinding
    policy_version: str
    policy_hash: str
    #: The closed representation contract this proposal was generated under.
    #: A reviewer is accepting claims about what facts may say, so the union
    #: that defines that has to travel with the claims rather than being
    #: re-stamped from whatever the code implements at acceptance time.
    schema_version: str
    schema_hash: str
    proposed_spans: tuple[ProposedSpan, ...]
    proposed_representation: RepresentationDraft
    #: What produced this proposal — a tool name and version, a reviewer's
    #: manual draft, whatever the authoring path was. Audit metadata for the
    #: human reading it, never authority.
    proposal_origin: str
    #: The proposal shape this proposal states, declared rather than stamped
    #: from the current constant. A retained file loads as the version it was
    #: authored under; restamping it would make every recorded proposal identity
    #: a claim about today's code instead of about the bytes a human reviewed.
    proposal_schema_version: str = PROPOSAL_SCHEMA_VERSION
    #: The coherent units of source the author says this proposal covers, and
    #: what each must contain. Part of the payload — and so of
    #: :func:`proposal_identity` — under ``5d-proposal-2``, which is the point:
    #: an acceptance records the identity of what it accepted from, so a changed
    #: or unauthored inventory cannot inherit an existing acceptance claim.
    #:
    #: Empty by default and *refused* under ``5d-proposal-1``, whose payload
    #: states no inventory at all.
    proposed_review_units: tuple[ReviewUnit, ...] = ()


def proposal_payload(proposal: MechanicalProposal) -> dict[str, object]:
    """Canonical JSON payload of one machine proposal.

    Reuses the span and representation payload builders so a reviewer diffs the
    same canonical form the accepted artifact uses — the *content* is comparable
    even though the *envelope* is not interchangeable, which is exactly what
    makes a semantic diff meaningful at acceptance time.
    """
    version = proposal.proposal_schema_version
    if version not in _ENVELOPE:
        raise ValueError(
            f"proposal_schema_version {version!r} is not a shape this build "
            f"writes ({sorted(_ENVELOPE)})"
        )
    # Silently dropping them would mint an identity that covers the spans and
    # the representation but not the inventory — and an acceptance recording
    # that identity would attest to review of something it does not name. The
    # author picks the version that can state what they are proposing.
    if version == PROPOSAL_SCHEMA_VERSION and proposal.proposed_review_units:
        raise ValueError(
            f"this proposal states {len(proposal.proposed_review_units)} review "
            f"units but declares {version!r}, whose payload states none; an "
            f"inventory has to be proposed under {PROPOSAL_SCHEMA_VERSION_2!r} "
            "to be inside the identity an acceptance records"
        )

    by_span = {p.span.span_id: p for p in proposal.proposed_spans}
    payload: dict[str, object] = {
        "artifact_kind": PROPOSAL_ARTIFACT_KIND,
        "proposal_schema_version": version,
        "proposal_origin": proposal.proposal_origin,
        "release_binding": {
            "package_uuid": proposal.binding.package_uuid,
            "release_version": proposal.binding.release_version,
            "authoritative_source_hash": proposal.binding.authoritative_source_hash,
            "transform_config_hash": proposal.binding.transform_config_hash,
            "bundle_root_hash": proposal.binding.bundle_root_hash,
            "persisted_corpus_digest": proposal.binding.persisted_corpus_digest,
        },
        "semantic_policy_version": proposal.policy_version,
        "semantic_policy_hash": proposal.policy_hash,
        "representation_schema": {
            "version": proposal.schema_version,
            "hash": proposal.schema_hash,
        },
        "proposed_spans": canonical_order(
            {
                **payload,
                "proposal_origin": by_span[str(payload["span_id"])].origin,
                "rationale": by_span[str(payload["span_id"])].rationale,
            }
            for payload in span_payload(tuple(p.span for p in proposal.proposed_spans))
        ),
        # Under the proposal's own declaration. The batch that accepts a
        # proposal records its identity as evidence of what a human reviewed, so
        # that identity has to stay re-derivable from the retained proposal
        # artifact on a later build — otherwise the recorded value becomes
        # unverifiable the moment the union widens.
        "proposed_representation": representation_payload(
            proposal.proposed_representation,
            schema_version=proposal.schema_version,
        ),
    }
    if version != PROPOSAL_SCHEMA_VERSION:
        # The same canonical form the accepted artifact writes, so the
        # inventory a reviewer read and the inventory an acceptance records are
        # comparable element by element rather than by two orderings.
        payload["proposed_review_units"] = review_unit_payload(
            proposal.proposed_review_units
        )
    return payload


def proposal_identity(proposal: MechanicalProposal) -> str:
    """Content-derived identity of one proposal.

    Lets a review note name the exact proposal it reviewed, and lets acceptance
    record what it accepted *from*. It is not a projection identity and never
    becomes one — a proposal that is never accepted leaves no trace in any
    published authority.
    """
    return hash_obj(proposal_payload(proposal))


class ProposalLoadError(ValueError):
    """A retained proposal file that will not load as the proposal it claims.

    Distinct from :class:`~afterworlds.ingestion.mechanical.oracle.OracleLoadError`
    on purpose: a malformed proposal and a malformed oracle are different
    failures with different consequences. A proposal that will not load blocks
    a review; an oracle that will not load blocks a publication.
    """


def load_proposal(
    path: Path, *, expected_identity: str | None = None
) -> MechanicalProposal:
    """Load one retained machine proposal from JSON.

    The inverse of :func:`proposal_payload`, and the one reader for it. Every
    batch's acceptance evidence records the ``proposal_identity`` of what a
    human reviewed, and that recorded value is only worth something if the
    retained bytes still derive it on a later build — so reconstructing a
    reviewed proposal is a production concern, not something each reproduction
    re-derives its own way.

    Spans load as :attr:`ReviewState.PROPOSED`. A proposal is a claim nobody has
    accepted; :func:`~afterworlds.ingestion.mechanical.acceptance.accept_proposal`
    is what stamps acceptance, and it does so unconditionally, so this is an
    honest label rather than a behaviour change. Review state is absent from
    :func:`span_payload`, so it reaches no identity either way.

    The declared ``proposal_schema_version`` is honoured, not assumed. It is
    checked against the closed set of shapes this build reads, and the envelope
    is then checked against exactly what that version declares — both *before*
    anything is reconstructed and before ``expected_identity`` is compared.
    Order matters: a file declaring an unreadable version was restamped with
    the current constant and rebuilt under rules it never claimed, and because
    the restamped payload re-derived the old identity, supplying the expected
    identity confirmed it. A version this build cannot state the meaning of is
    a refusal, not a field to overwrite.

    ``expected_identity``, when given, is checked after the rebuild and refuses
    on mismatch. A caller naming the proposal it means to load gets the
    substitution caught here rather than several steps later, in a merge whose
    bytes no longer match anything retained.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProposalLoadError(f"{path.name}: {exc}") from exc

    if not isinstance(raw, dict) or raw.get("artifact_kind") != PROPOSAL_ARTIFACT_KIND:
        kind = raw.get("artifact_kind") if isinstance(raw, dict) else None
        raise ProposalLoadError(
            f"{path.name}: artifact_kind {kind!r} is not "
            f"{PROPOSAL_ARTIFACT_KIND!r}; this file is not a machine proposal"
        )

    declared = raw.get("proposal_schema_version")
    if type(declared) is not str:
        raise ProposalLoadError(
            f"{path.name}: proposal_schema_version {declared!r} is not a "
            "string; a proposal states the shape it was authored under, and a "
            "file that states none cannot be read as any of them"
        )
    if declared not in _ENVELOPE:
        raise ProposalLoadError(
            f"{path.name}: proposal_schema_version {declared!r} is not a shape "
            f"this build reads ({sorted(_ENVELOPE)})"
        )
    try:
        _require(raw, _ENVELOPE[declared], path.name)
    except OracleLoadError as exc:
        raise ProposalLoadError(
            f"{exc}; a {declared!r} proposal declares exactly "
            f"{list(_ENVELOPE[declared])}"
        ) from exc

    try:
        spans = tuple(
            ProposedSpan(
                span=replace(
                    _span(
                        {
                            key: value
                            for key, value in entry.items()
                            if key not in ("proposal_origin", "rationale")
                        },
                        index,
                    ),
                    review_state=ReviewState.PROPOSED,
                ),
                origin=str(entry["proposal_origin"]),
                rationale=str(entry["rationale"]),
            )
            for index, entry in enumerate(raw["proposed_spans"])
        )
        proposal = MechanicalProposal(
            binding=ReleaseBinding(**raw["release_binding"]),
            policy_version=str(raw["semantic_policy_version"]),
            policy_hash=str(raw["semantic_policy_hash"]),
            schema_version=str(raw["representation_schema"]["version"]),
            schema_hash=str(raw["representation_schema"]["hash"]),
            proposed_spans=spans,
            proposed_representation=_representation(raw["proposed_representation"]),
            proposal_origin=str(raw["proposal_origin"]),
            proposal_schema_version=declared,
            proposed_review_units=tuple(
                _review_unit(u, i, key="proposed_review_units")
                for i, u in enumerate(
                    _object_list(
                        raw.get("proposed_review_units", []), "proposed_review_units"
                    )
                )
            ),
        )
    except (OracleLoadError, KeyError, TypeError, AttributeError) as exc:
        raise ProposalLoadError(f"{path.name}: {exc}") from exc

    if expected_identity is not None:
        identity = proposal_identity(proposal)
        if identity != expected_identity:
            raise ProposalLoadError(
                f"{path.name}: derives proposal {identity}, not the "
                f"{expected_identity} this caller named"
            )
    return proposal


#: What a seeded proposal states about its own representation: nothing. A seed
#: has read no rule, so an empty draft is the only truthful thing it can carry
#: -- and it is a *stated* emptiness, inside the identity an acceptance would
#: record, not an absent key.
_EMPTY_REPRESENTATION = RepresentationDraft(
    records=(),
    components=(),
    prose_bindings=(),
    relationships=(),
    references=(),
    provenance=(),
)


def seed_proposal(
    snapshot: BoundCorpusSnapshot,
    leaf_ids: Sequence[str],
    *,
    binding: ReleaseBinding,
    origin: str,
    rationale: str,
) -> MechanicalProposal:
    """Derive an unreviewed proposal covering *leaf_ids* of the bound release.

    The repository-native start of the authoring path. Before this, a proposal
    over real source could only come from a throwaway generator script, and a
    throwaway script is the one input to acceptance that nobody reviews: the
    reviewer sees the artifact, not the code that emitted it, so the step that
    turns 5c leaves into proposed spans belongs in committed source where its
    behaviour is a contract.

    What it produces is deliberately the *weakest* honest proposal:

    * one whole-leaf span per requested leaf, at
      :attr:`SemanticDisposition.UNRESOLVED` -- the disposition that means "a
      human has not decided", not a guess dressed as one;
    * span ids from :func:`~.accounting.derive_span_id`, so the same leaves
      seed the same ids on any machine and a changed range is a changed span;
    * an empty representation; and
    * no review units. Naming a coherent unit and saying what it must contain
      is the reviewer's reading of the source, not a shape code can derive
      from offsets. Seeding placeholder units would put unauthored inventory
      inside the identity an acceptance records, which is exactly the
      fabricated-coverage failure ``5d-proposal-2`` exists to prevent.

    The result is therefore *inventory*, not interpretation: it says which
    source this proposal is about and nothing about what the source means. An
    author adds dispositions, representation and units; a reviewer accepts. It
    seeds under the current policy and representation contracts only: a
    historical hash belongs to the artifact that was reviewed under it, and new
    authoring has no reason to claim a superseded shape.
    Nothing here writes a file, reads ``oracles/``, or produces an accepted
    type -- this module still emits only proposals.

    Raises ``ValueError`` when a requested leaf is not in the snapshot's
    represented population: a span over a leaf 5c did not represent is a claim
    about text that has no authoritative length, and failing at the seed is
    where it is cheapest to see.
    """
    if binding.package_uuid != snapshot.package_uuid or (
        binding.release_version != snapshot.release_version
    ):
        raise ValueError(
            f"binding names {binding.package_uuid}/{binding.release_version} but the "
            f"snapshot is {snapshot.package_uuid}/{snapshot.release_version}; a "
            "proposal must be bound to the release it was seeded from"
        )
    if not leaf_ids:
        raise ValueError("a seeded proposal needs at least one leaf to be about")

    # Deduplicated and ordered here rather than trusting the caller: two spans
    # over one leaf would be an overlapping partition, and a repeated id would
    # be refused at acceptance with a much less obvious message.
    wanted = sorted(set(leaf_ids))
    if missing := [leaf for leaf in wanted if leaf not in snapshot.leaf_lengths]:
        raise ValueError(
            f"{len(missing)} requested leaf id(s) are not represented in "
            f"{snapshot.package_uuid}/{snapshot.release_version}: {missing[:5]}"
        )

    spans = tuple(
        ProposedSpan(
            span=SemanticSpan(
                span_id=derive_span_id(leaf_id, 0, snapshot.leaf_lengths[leaf_id]),
                leaf_id=leaf_id,
                char_start=0,
                char_end=snapshot.leaf_lengths[leaf_id],
                disposition=SemanticDisposition.UNRESOLVED,
                review_state=ReviewState.PROPOSED,
            ),
            origin=origin,
            rationale=rationale,
        )
        for leaf_id in wanted
    )
    return MechanicalProposal(
        binding=binding,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        proposed_spans=spans,
        proposed_representation=_EMPTY_REPRESENTATION,
        proposal_origin=origin,
        proposal_schema_version=PROPOSAL_SCHEMA_VERSION_2,
    )


def locate_span(
    leaf_contents: Mapping[str, str],
    text: str,
    disposition: SemanticDisposition,
    *,
    anchor: str | None = None,
) -> SemanticSpan:
    """The one PROPOSED span whose source text is *text*, among *leaf_contents*.

    An author names a clause by its exact printed text, never by offsets, and
    the text must occur exactly once across the leaves searched (normally one
    entry's). Where the bare text also occurs elsewhere -- a table cell's name
    in running prose -- *anchor* is a longer unique string containing it, and
    the span is *text*'s position inside that anchor.
    """
    needle = text if anchor is None else anchor
    if text not in needle:
        raise ValueError(f"anchor {anchor!r} does not contain {text!r}")
    found = sum(content.count(needle) for content in leaf_contents.values())
    if found != 1:
        raise ValueError(f"{needle!r} occurs {found} times; exactly one is required")
    leaf_id, content = next(
        (leaf, content) for leaf, content in leaf_contents.items() if needle in content
    )
    start = content.index(needle) + needle.index(text)
    end = start + len(text)
    return SemanticSpan(
        span_id=derive_span_id(leaf_id, start, end),
        leaf_id=leaf_id,
        char_start=start,
        char_end=end,
        disposition=disposition,
        review_state=ReviewState.PROPOSED,
    )
