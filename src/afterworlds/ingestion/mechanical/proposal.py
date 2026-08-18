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

from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import span_payload
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import SemanticSpan
from afterworlds.ingestion.mechanical.projection import (
    ReleaseBinding,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import RepresentationDraft

__all__ = [
    "PROPOSAL_ARTIFACT_KIND",
    "PROPOSAL_SCHEMA_VERSION",
    "MechanicalProposal",
    "ProposedSpan",
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
        "proposed_representation": representation_payload(
            proposal.proposed_representation
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
