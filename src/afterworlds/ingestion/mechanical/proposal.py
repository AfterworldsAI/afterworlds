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
from dataclasses import dataclass, replace
from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import span_payload
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import ReviewState, SemanticSpan

# The committed readers, reused rather than re-implemented. They are private
# because nothing outside a loader should be turning raw payloads into accepted
# shapes, and that stays true here: this module wraps them, it does not move or
# rename them, and a second hand-rolled reader is exactly the drift a retained
# proposal cannot afford.
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    _representation,
    _span,
)
from afterworlds.ingestion.mechanical.projection import (
    ReleaseBinding,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import RepresentationDraft

__all__ = [
    "PROPOSAL_ARTIFACT_KIND",
    "PROPOSAL_SCHEMA_VERSION",
    "MechanicalProposal",
    "ProposalLoadError",
    "ProposedSpan",
    "load_proposal",
    "proposal_identity",
    "proposal_payload",
]

#: The discriminator every proposal declares. Deliberately not the accepted
#: artifact's kind, and deliberately not something an accepted loader accepts.
PROPOSAL_ARTIFACT_KIND = "machine_proposal"

#: Bumped when the proposal shape changes. Proposals are disposable review
#: material, so this version has no relationship to semantic policy identity and
#: never reaches a projection.
PROPOSAL_SCHEMA_VERSION = "5d-proposal-1"


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


def proposal_payload(proposal: MechanicalProposal) -> dict[str, object]:
    """Canonical JSON payload of one machine proposal.

    Reuses the span and representation payload builders so a reviewer diffs the
    same canonical form the accepted artifact uses — the *content* is comparable
    even though the *envelope* is not interchangeable, which is exactly what
    makes a semantic diff meaningful at acceptance time.
    """
    by_span = {p.span.span_id: p for p in proposal.proposed_spans}
    return {
        "artifact_kind": PROPOSAL_ARTIFACT_KIND,
        "proposal_schema_version": PROPOSAL_SCHEMA_VERSION,
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
