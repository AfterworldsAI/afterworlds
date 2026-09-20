"""Both Proficiency merges, rebuilt from retained inputs — CRD Issue 5d.

``.claude/review-notes/issue-5d-batch-proficiency-destinations-1-and-proficiency-1-ACCEPT.py
--verify`` claims to reproduce the committed artifact rather than to spot-check
it. This module is the regression coverage for that claim, and it is
deliberately independent of that script: it re-derives both accepted scopes and
calls ``accept_proposal`` twice on its own, importing nothing from it. Two
independent paths arriving at the same bytes is evidence; one shared helper
agreeing with itself is not.

It follows ``test_cover_1_acceptance_reproduction`` and
``test_areas_of_effect_1_acceptance_reproduction`` clause for clause, with two
differences the batches themselves cause.

**One acceptance action, two batches.** The Owner authorized both proposals in
one action, destinations before Proficiency, and that order is load-bearing
rather than cosmetic: the ``Expertise`` destination cites ``Proficiency``, so
after the first merge and before the second the artifact names a target no
accepted batch defines. The third test asserts that intermediate state exactly,
because an acceptance that silently reordered the two would produce the same
final bytes by a route the Owner did not authorize — and because "the forward
citation is closed by the next batch" is a claim about an intermediate state, not
about the file.

**No source manifest, so no second scope order.** The five earlier batches
recorded their accepted scope in a reviewed inventory whose file order differs
from the proposal's canonical order, and their reproduction modules exploit that
to show the byte comparison is load-bearing. These two batches were authorized
"with full explicit span scopes … not derived from persisted candidate output",
and the explicit scopes are the reviewed proposals' own order. There is
therefore no second order to discriminate against here; the discrimination
property is covered once, over ``cover-1`` and ``areas-of-effect-1``, and is not
restated.

**Where each input comes from, and why none of them is the artifact.**

* the two reviewed proposals — the committed bytes the Owner's authorization
  names by identity and SHA-256, loaded through ``load_proposal`` with
  ``expected_identity`` so a substituted file is refused before it is merged;
* each accepted scope, in the order the reviewed proposal states it, read from
  the proposal JSON rather than from the artifact's retained ``resolved_scope``
  — reading it back from there would make the comparison test nothing;
* the prior — the frozen seven-batch fixture, never the live file, pinned below
  by content digest, Git blob and oracle identity.

The one thing taken from the artifact is each batch's recorded ``rule`` prose.
That is retained acceptance *evidence* with no second copy in the repository:
the ACCEPT script composes it from the Owner's authorization and Codex's
verdict, and both of those are asserted below to be inside it from literals this
module holds independently. Everything the identity covers — every span,
disposition, component, fact, reference, obligation, review unit, anchor, lift
and policy transition — is rebuilt.

**What the rebuild is compared against.** The live committed artifact, which is
what these two acceptances wrote and nothing has moved since. The second test is
the other half of that: the seven earlier acceptances must be carried into it
byte-identically, which is the property the Owner's "preserve original seven
batches/history and Speed order" names.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from tests.ingestion.mechanical.test_committed_accepted_authority import (
    ARTIFACT_PATH,
    FROZEN_PRIOR,
    ORACLE_IDENTITY,
    PRIOR_ORACLE_IDENTITY,
)

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
DEST_PROPOSAL_PATH = (
    REVIEW_NOTES / "issue-5d-batch-proficiency-destinations-1-PROPOSAL.json"
)
PROF_PROPOSAL_PATH = REVIEW_NOTES / "issue-5d-batch-proficiency-1-PROPOSAL.json"

DEST_BATCH_ID = "proficiency-destinations-1"
PROF_BATCH_ID = "proficiency-1"
REVIEWER = "Ravenlok (Owner)"

#: The two clock reads taken when the Owner's acceptance was applied, observed
#: rather than invented; the write window they produced and the reverted first
#: run that preceded them are recorded in
#: ``issue-5d-proficiency-ACCEPTANCE-CHECKPOINT.md``.
DEST_ACCEPTED_AT = "2026-09-20T02:50:55Z"
PROF_ACCEPTED_AT = "2026-09-20T02:50:58Z"

#: The review units each batch discharged. Authorized explicitly rather than
#: derived, which is why they are literals here too.
DEST_UNITS = (
    "proficiency-destinations-1-actions-section",
    "proficiency-destinations-1-challenge-rating",
    "proficiency-destinations-1-expertise",
    "proficiency-destinations-1-skills-table",
)
PROF_UNITS = ("proficiency-1-section",)

DEST_PROPOSAL_IDENTITY = "723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e"  # noqa: E501  # pragma: allowlist secret
PROF_PROPOSAL_IDENTITY = "f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a"  # noqa: E501  # pragma: allowlist secret
DEST_PROPOSAL_SHA256 = "6a88c886f320aa05cb6c9363b9a5bd1ab5d5c0b551d21832ab2dd2daf035fe1d"  # noqa: E501  # pragma: allowlist secret
PROF_PROPOSAL_SHA256 = "c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d"  # noqa: E501  # pragma: allowlist secret

#: The sentence the Owner's authorization opens with, restated here rather than
#: read from the artifact, so the rule prose the artifact carries is checked
#: against a value this module holds independently.
AUTHORIZATION_OPENING = (
    "Perform the already Owner-authorized formal acceptance of the two "
    "independently reviewed Proficiency batches under CRD Issue 5d."
)
#: Likewise the verdict the independent review recorded, which the Owner's
#: authorization required be attributed in the evidence.
CODEX_VERDICT = (
    "Verdict: ready for the already Owner-authorized formal acceptance of the "
    "exact two reviewed proposals. This does not authorize publication, "
    "activation or merge."
)

#: The frozen seven-batch prior, by the three identities that pin it. The live
#: artifact's own content digest and blob were these until this acceptance moved
#: them, which is why the fixture exists rather than a re-derivation.
PRIOR_CONTENT_SHA256 = "eed7df0476445fc6e5d1d9cd6bdd67977f72372bc67b01808eaa240b69a7e619"  # noqa: E501  # pragma: allowlist secret
PRIOR_BLOB = "4fcfab6f667923acbaa98345b56a405061287643"  # pragma: allowlist secret

#: The reference obligation that exists only between the two merges: the
#: ``Expertise`` destination cites ``Proficiency``, and ``proficiency-1`` is the
#: batch that defines it.
FORWARD_CITATION = (
    "reference srd-5.2.1/playing-the-game:'Proficiency': "
    "unknown target record play.proficiency"
)


def _canonical_bytes(path: pathlib.Path) -> bytes:
    """File content with LF newlines, which is what ``.gitattributes`` declares."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _scope(path: pathlib.Path) -> tuple[str, ...]:
    """The accepted scope, in the order the reviewed proposal states it."""
    document = json.loads(path.read_text(encoding="utf-8"))
    return tuple(span["span_id"] for span in document["proposed_spans"])


def _recorded_rule(batch_id: str) -> str:
    """One batch's rule prose, the one retained value with no second copy."""
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    (batch,) = [
        b for b in artifact["acceptance"]["batches"] if b["batch_id"] == batch_id
    ]
    rule = str(batch["rule"])
    assert AUTHORIZATION_OPENING in rule, "the Owner's words are not in the rule"
    assert CODEX_VERDICT in rule, "the independent review is not attributed"
    return rule


def _merge_destinations(prior: AcceptedInputs | None = None) -> AcceptedInputs:
    """The first of the two authorized merges, over the frozen prior."""
    return accept_proposal(
        load_proposal(DEST_PROPOSAL_PATH, expected_identity=DEST_PROPOSAL_IDENTITY),
        batch_id=DEST_BATCH_ID,
        rule=_recorded_rule(DEST_BATCH_ID),
        resolved_scope=_scope(DEST_PROPOSAL_PATH),
        reviewer=REVIEWER,
        accepted_at=DEST_ACCEPTED_AT,
        prior=prior if prior is not None else load_accepted_inputs(FROZEN_PRIOR),
        resolved_review_units=DEST_UNITS,
    )


def _merge_proficiency(prior: AcceptedInputs) -> AcceptedInputs:
    """The second merge, over whatever the first produced."""
    return accept_proposal(
        load_proposal(PROF_PROPOSAL_PATH, expected_identity=PROF_PROPOSAL_IDENTITY),
        batch_id=PROF_BATCH_ID,
        rule=_recorded_rule(PROF_BATCH_ID),
        resolved_scope=_scope(PROF_PROPOSAL_PATH),
        reviewer=REVIEWER,
        accepted_at=PROF_ACCEPTED_AT,
        prior=prior,
        resolved_review_units=PROF_UNITS,
    )


def _merge_both() -> AcceptedInputs:
    """Both merges in the authorized order, destinations first."""
    return _merge_proficiency(_merge_destinations())


def test_the_reviewed_proposals_are_the_bytes_the_authorization_names() -> None:
    """Identity and SHA-256, both, before either file is merged.

    ``load_proposal`` refuses a mismatched identity, which covers the accepted
    content. The Owner's authorization also named a file digest, and that covers
    the whole committed proposal including the review prose beside the content —
    so it is asserted too rather than assumed to follow.
    """
    for path, sha256 in (
        (DEST_PROPOSAL_PATH, DEST_PROPOSAL_SHA256),
        (PROF_PROPOSAL_PATH, PROF_PROPOSAL_SHA256),
    ):
        assert hashlib.sha256(_canonical_bytes(path)).hexdigest() == sha256, path.name


def test_the_committed_merge_is_reproducible_from_the_retained_inputs() -> None:
    """Rebuild the whole artifact from the two proposals and the frozen prior.

    Byte equality, not identity equality: the oracle identity covers accepted
    content only, so an artifact matching it can still differ in the acceptance
    evidence beside it. This compares the committed file in full.
    """
    merged = _merge_both()
    assert serialize_accepted_inputs(merged) == _canonical_bytes(ARTIFACT_PATH)
    # Stated separately so a failure says which half moved.
    assert oracle_identity(merged.oracle) == ORACLE_IDENTITY


def test_the_seven_earlier_acceptances_are_carried_in_unchanged() -> None:
    """ "Preserve original seven batches/history and Speed order", as a test.

    A merge is the only representable way to add a batch, but it is a merge into
    a mutable-looking file: nothing structural stops an acceptance from also
    rewriting an earlier batch's rule, restamping its acceptance, or reordering
    the anchors that record acceptance order. Compared element by element
    against the frozen prior, keyed by id rather than by position, because
    ``batches`` comes back canonically ordered and the two new ids sort into the
    middle of it.
    """
    prior = load_accepted_inputs(FROZEN_PRIOR)
    assert hashlib.sha256(_canonical_bytes(FROZEN_PRIOR)).hexdigest() == (
        PRIOR_CONTENT_SHA256
    )
    canonical = _canonical_bytes(FROZEN_PRIOR)
    assert (
        hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
            b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
        ).hexdigest()
        == PRIOR_BLOB
    )
    assert oracle_identity(prior.oracle) == PRIOR_ORACLE_IDENTITY

    live = load_accepted_inputs(ARTIFACT_PATH)
    prior_batches = {b.batch_id: b for b in prior.batches}
    live_batches = {b.batch_id: b for b in live.batches}
    assert len(prior_batches) == 7
    assert set(prior_batches) < set(live_batches)
    for batch_id, batch in prior_batches.items():
        assert live_batches[batch_id] == batch, batch_id

    prior_acceptances = {a.span_id: a for a in prior.acceptances}
    live_acceptances = {a.span_id: a for a in live.acceptances}
    assert set(prior_acceptances) < set(live_acceptances)
    for span_id, acceptance in prior_acceptances.items():
        assert live_acceptances[span_id] == acceptance, span_id

    # Acceptance order and the registered succession are append-only, so these
    # compare by position — ``speed-1`` must still be the seventh anchor.
    assert live.schema_anchors[: len(prior.schema_anchors)] == prior.schema_anchors
    assert live.schema_anchors[6].batch_id == "speed-1"
    assert live.lifts[: len(prior.lifts)] == prior.lifts
    assert prior.policy_transitions == ()

    prior_spans = {s.span_id: s for s in prior.oracle.spans}
    live_spans = {s.span_id: s for s in live.oracle.spans}
    for span_id, span in prior_spans.items():
        assert live_spans[span_id] == span, span_id


def test_the_destinations_batch_alone_leaves_the_forward_citation_open() -> None:
    """The intermediate state the authorized order exists to produce.

    ``Expertise`` cites ``Proficiency``, and no accepted batch defined it until
    ``proficiency-1`` was accepted three seconds later. So the destinations
    merge carries exactly one obligation the finished artifact does not, and the
    finished artifact carries none the destinations merge did not resolve. That
    is a property of an intermediate value, invisible in the committed file,
    which is why it is asserted here rather than left to the acceptance script.
    """
    after_destinations = sorted(
        relationship_and_reference_violations(
            _merge_destinations().oracle.representation
        )
    )
    after_both = sorted(
        relationship_and_reference_violations(_merge_both().oracle.representation)
    )

    assert set(after_destinations) - set(after_both) == {FORWARD_CITATION}
    assert set(after_both) - set(after_destinations) == set()
    assert len(after_destinations) == len(after_both) + 1


def test_the_merge_refuses_a_scope_the_reviewed_proposal_did_not_propose() -> None:
    """The scope is checked against the proposal, not trusted from the literal.

    The Owner authorized explicit span scopes rather than scopes derived from
    persisted output, so the literal is the claim — and ``accept_proposal`` is
    the seam that refuses a claim the reviewed proposal does not support.
    """
    invented = derive_span_id("srd-5.2.1/not-a-leaf", 0, 1)

    with pytest.raises(Exception, match="did not propose"):
        accept_proposal(
            load_proposal(DEST_PROPOSAL_PATH, expected_identity=DEST_PROPOSAL_IDENTITY),
            batch_id=DEST_BATCH_ID,
            rule=_recorded_rule(DEST_BATCH_ID),
            resolved_scope=(*_scope(DEST_PROPOSAL_PATH), invented),
            reviewer=REVIEWER,
            accepted_at=DEST_ACCEPTED_AT,
            prior=load_accepted_inputs(FROZEN_PRIOR),
            resolved_review_units=DEST_UNITS,
        )
