"""The ``cover-1`` merge, rebuilt from retained inputs — CRD Issue 5d.

``.claude/review-notes/issue-5d-cover-1-ACCEPT.py --verify`` claims to reproduce
the committed artifact rather than to spot-check it. This module is the
regression coverage for that claim, and it is deliberately independent of that
script: it re-derives the accepted scope and calls ``accept_proposal`` on its
own, importing nothing from it. Two independent paths arriving at the same bytes
is evidence; one shared helper agreeing with itself is not.

The reviewed proposal is loaded by ``load_proposal``, the production reader,
rather than rebuilt here. That is a consolidation, not a weakening: the ACCEPT
script this module checks does its own rebuild, so the two paths still meet only
at the bytes. The hand-written second rebuild is retained once, in
``test_speed_1_acceptance_reproduction``, which compares it against the loader.

This module follows ``test_areas_of_effect_1_acceptance_reproduction`` clause for
clause, because the property being covered is the same one.

**Where each input comes from, and why none of them is the artifact.**

* the reviewed proposal — ``issue-5d-batch-cover-1-PROPOSAL.json``, the
  committed bytes the Owner's authorization names by hash;
* the accepted scope **in its recorded order** —
  ``issue-5d-cover-1-source-manifest.json``, pinned by digest here and in the
  generator, walked in file order and turned into span ids through
  ``derive_span_id``. The proposal sorts its spans canonically, so it cannot
  state this order; the artifact retains it verbatim, so reading it back from
  there would make the comparison test nothing;
* the prior — the frozen five-batch fixture, never the live file. That the live
  artifact still carries that prior unchanged is asserted in
  ``test_cover_1_frozen_prior``.

The one thing taken from the artifact is the batch's recorded ``rule`` prose.
That is retained acceptance *evidence* with no second copy in the repository, and
it is not what these tests are about: the Owner's verbatim authorization is a
literal below and is asserted to be inside it. Everything the identity covers —
every span, disposition, component, fact, reference, obligation, anchor and lift
— is rebuilt.

**What the rebuild is compared against.** Not the live committed artifact: the
Owner accepted ``speed-1`` into it on 2026-09-12, so the live file is this
merge *plus a seventh batch* and a byte comparison against it would be false.
The comparison target is the frozen six-batch fixture, which is byte-for-byte
what this acceptance wrote — Git blob ``b7c01494…``, the live artifact's own
blob until the seventh acceptance moved it. That the live artifact still
carries this result unchanged is asserted in ``test_speed_1_frozen_prior``, which
is where the fixture is attached to the file it was copied from. Retargeting
here rather than loosening the comparison keeps it a byte comparison.

The third test is the one that earns the first. It shows that the merge can
differ in a way the committed artifact's own pins cannot see: handing
``accept_proposal`` the scope in the proposal's canonical order instead of the
recorded one produces an artifact with the **same** ``oracle_identity``, the same
counts, the same dispositions, the same unresolved citations and the same
acceptance findings — and different bytes. A verification that sampled those
properties would pass on it. This one refuses.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.accounting import (
    derive_span_id,
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
)

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
PROPOSAL_PATH = REVIEW_NOTES / "issue-5d-batch-cover-1-PROPOSAL.json"
MANIFEST_PATH = REVIEW_NOTES / "issue-5d-cover-1-source-manifest.json"
FROZEN_PRIOR = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "accepted_prior_conditions_1_hazards_1_actions_1"
    "_attitudes_1_areas_of_effect_1.json"
)
#: What this acceptance produced, frozen. See the module docstring: the live
#: artifact has moved on by one batch, this file has not.
FROZEN_RESULT = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "accepted_prior_conditions_1_hazards_1_actions_1"
    "_attitudes_1_areas_of_effect_1_cover_1.json"
)

BATCH_ID = "cover-1"
REVIEWER = "Ravenlok (Owner)"
#: The clock read when the Owner's acceptance was applied, observed rather
#: than invented; the write window it produced is recorded in
#: ``issue-5d-cover-1-ACCEPTANCE-CHECKPOINT.md``.
ACCEPTED_AT = "2026-09-11T17:14:44Z"

#: The Owner's authorization, verbatim, restated here rather than read from the
#: artifact, so the rule prose the artifact carries is checked against a value
#: this module holds independently.
AUTHORIZATION = (
    "I accept all 28 spans and the complete representation of proposal "
    "1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01 as batch "
    "cover-1, extending the preserved prior through the registered schema "
    "transitions."
)

PROPOSAL_IDENTITY = "1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01"  # noqa: E501  # pragma: allowlist secret

#: The reviewed inventory's canonical-LF digest, the same value the generator and
#: the ACCEPT script pin. A manifest that moved would change the recorded order
#: silently, so it is refused here before the order is used.
MANIFEST_SHA256 = "f82163ee2fc6b6c1805974e6e7404eca45fd6b48452a64a91f9e6a4f0e0cdcad"  # noqa: E501  # pragma: allowlist secret

#: Derived from the accepted semantic content alone. Acceptance *evidence* —
#: reviewer, timestamp, rule, resolved scope, anchors and lifts — is deliberately
#: outside it, which is exactly what the third test exploits.
MERGED_ORACLE_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret


def _canonical_bytes(path: pathlib.Path) -> bytes:
    """File content with LF newlines, which is what ``.gitattributes`` declares."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _recorded_scope() -> tuple[str, ...]:
    """The accepted scope in its recorded order, re-derived from the manifest."""
    assert (
        hashlib.sha256(_canonical_bytes(MANIFEST_PATH)).hexdigest() == MANIFEST_SHA256
    ), "the reviewed source manifest is not the one this order was recorded from"
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return tuple(
        derive_span_id(row["leaf_id"], int(row["char_start"]), int(row["char_end"]))
        for row in manifest["clauses"]
    )


def _proposal_order_scope() -> tuple[str, ...]:
    """The same spans in the proposal JSON's canonical order — a different order."""
    document = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    return tuple(span["span_id"] for span in document["proposed_spans"])


def _recorded_rule() -> str:
    """The batch rule prose, the one retained value with no second copy."""
    artifact = json.loads(FROZEN_RESULT.read_text(encoding="utf-8"))
    (batch,) = [
        b for b in artifact["acceptance"]["batches"] if b["batch_id"] == BATCH_ID
    ]
    rule = str(batch["rule"])
    assert AUTHORIZATION in rule, "the Owner's words are not in the recorded rule"
    return rule


def _merge(scope: tuple[str, ...]) -> AcceptedInputs:
    """One in-memory merge of the reviewed proposal over the frozen prior."""
    return accept_proposal(
        load_proposal(PROPOSAL_PATH, expected_identity=PROPOSAL_IDENTITY),
        batch_id=BATCH_ID,
        rule=_recorded_rule(),
        resolved_scope=scope,
        reviewer=REVIEWER,
        accepted_at=ACCEPTED_AT,
        prior=load_accepted_inputs(FROZEN_PRIOR),
    )


def _sampled_properties(accepted: AcceptedInputs) -> dict[str, object]:
    """The property surface a spot-checking verification looks at.

    Counts per collection, the batch set, the accepted dispositions, the
    unresolved citation targets and the acceptance findings — everything the
    ACCEPT script's report tabulates about the merge, minus the byte comparison.
    Gathered in one place so the second test can show it is not enough.
    """
    record_keys = {r.semantic_key for r in accepted.oracle.representation.records}
    return {
        "oracle_identity": oracle_identity(accepted.oracle),
        "batches": sorted(b.batch_id for b in accepted.batches),
        "spans": len(accepted.oracle.spans),
        "acceptances": len(accepted.acceptances),
        **{
            collection: len(getattr(accepted.oracle.representation, collection))
            for collection in sorted(REPRESENTATION_COLLECTIONS)
        },
        "dispositions": sorted(
            (span.span_id, span.disposition.value) for span in accepted.oracle.spans
        ),
        "unresolved_reference_targets": sorted(
            {
                ref.target_record_key
                for ref in accepted.oracle.representation.references
                if ref.target_record_key not in record_keys
            }
        ),
        "schema_anchors": [
            (a.batch_id, a.schema_version) for a in accepted.schema_anchors
        ],
        "lifts": [lift.lift_id for lift in accepted.lifts],
        "acceptance_findings": list(validate_acceptance(accepted.classification())),
    }


def test_the_committed_merge_is_reproducible_from_the_retained_inputs() -> None:
    """Rebuild the whole artifact from the proposal, the manifest and the prior.

    Byte equality, not identity equality: the oracle identity covers accepted
    content only, so an artifact matching it can still differ in the acceptance
    evidence beside it. This compares the committed file in full.
    """
    rebuilt = serialize_accepted_inputs(_merge(_recorded_scope()))

    assert rebuilt == _canonical_bytes(FROZEN_RESULT)
    # Stated separately so a failure says which half moved.
    assert oracle_identity(_merge(_recorded_scope()).oracle) == MERGED_ORACLE_IDENTITY


def test_the_recorded_scope_order_is_the_manifests_and_not_the_proposals() -> None:
    """The two candidate orders are genuinely different, over the same span set.

    Without this the test above could be passing on a coincidence, and the
    discrimination test below would be proving nothing.
    """
    recorded = _recorded_scope()
    canonical = _proposal_order_scope()

    assert set(recorded) == set(canonical)
    assert len(recorded) == len(canonical) == 28
    assert recorded != canonical


def test_a_difference_the_sampled_properties_miss_is_still_refused() -> None:
    """The proof the byte comparison is load-bearing rather than decorative.

    Accepting the identical span set in the proposal's canonical order instead of
    the recorded one is a real difference in the merged file — ``resolved_scope``
    is retained verbatim while everything else is canonicalized — and it is
    invisible to every property a spot-checking verification samples, including
    the ``oracle_identity`` the committed artifact is pinned by. So the sampled
    surface agrees, the pinned identity agrees, and the bytes do not.
    """
    recorded = _merge(_recorded_scope())
    reordered = _merge(_proposal_order_scope())

    # Every sampled property agrees, including the pinned oracle identity.
    assert _sampled_properties(reordered) == _sampled_properties(recorded)
    assert oracle_identity(reordered.oracle) == MERGED_ORACLE_IDENTITY
    assert not validate_acceptance(reordered.classification())

    # The bytes do not, and the difference is exactly the retained scope order.
    committed = _canonical_bytes(FROZEN_RESULT)
    assert serialize_accepted_inputs(recorded) == committed
    assert serialize_accepted_inputs(reordered) != committed

    expected = json.loads(committed.decode("utf-8"))
    produced = json.loads(serialize_accepted_inputs(reordered).decode("utf-8"))
    differing = sorted(key for key in expected if expected[key] != produced.get(key))
    assert differing == ["acceptance"], differing
    (expected_batch,) = [
        b for b in expected["acceptance"]["batches"] if b["batch_id"] == BATCH_ID
    ]
    (produced_batch,) = [
        b for b in produced["acceptance"]["batches"] if b["batch_id"] == BATCH_ID
    ]
    assert sorted(
        key for key in expected_batch if expected_batch[key] != produced_batch.get(key)
    ) == ["resolved_scope"]


def test_the_merge_refuses_a_scope_the_reviewed_proposal_did_not_propose() -> None:
    """The scope is checked against the proposal, not trusted from the manifest.

    A manifest row naming a clause the proposal never carried would be an input
    disagreement, and ``accept_proposal`` is the seam that refuses it. Asserted
    so the manifest cannot become an unchecked second source of scope.
    """
    invented = derive_span_id("srd-5.2.1/not-a-leaf", 0, 1)

    with pytest.raises(Exception, match="did not propose"):
        _merge((*_recorded_scope(), invented))
