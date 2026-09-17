"""Every accepted batch's reviewed proposal still loads — CRD Issue 5d.

Each accepted batch records the ``proposal_identity`` of what a human read. That
recorded value is evidence only while the retained bytes still derive it: the
moment they do not, the artifact names a proposal nobody can produce, and "the
Owner accepted proposal ``bd9d4942…``" stops being checkable.

Nothing checked that for the corpus as a whole. Three reproduction modules each
rebuilt *their own* batch's proposal, with their own copy of the rebuild, and
the four batches with no reproduction module were unchecked. This is the one
parameterized check over all seven, through the production loader.

It is deliberately not a reproduction: it loads and derives, it does not merge.
The byte-level proof that a loaded proposal still produces the committed
artifact lives in the per-batch reproduction modules, which remain independent
of each other.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import (
    ProposalLoadError,
    load_proposal,
    proposal_identity,
)

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
COMMITTED_ARTIFACT = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: Which retained file each accepted batch was reviewed from, stated rather than
#: searched for. Three of these are not the batch's first proposal: ``conditions-1``
#: was accepted from its schema-3 remediation, ``hazards-1`` from its schema-5
#: regeneration, ``actions-1`` from its schema-7 regeneration. The superseded
#: drafts beside them are retained review history and are deliberately not listed
#: — several no longer load at all under the current closed representation union,
#: which is the correct outcome for a draft nobody accepted.
REVIEWED_PROPOSALS = {
    "conditions-1": "issue-5d-conditions-1-schema3-REMEDIATION-PROPOSAL.json",
    "hazards-1": "issue-5d-hazards-1-schema5-REGEN-PROPOSAL.json",
    "actions-1": "issue-5d-actions-1-schema7-PROPOSAL.json",
    "attitudes-1": "issue-5d-batch-attitudes-1-PROPOSAL.json",
    "areas-of-effect-1": "issue-5d-batch-areas-of-effect-1-PROPOSAL.json",
    "cover-1": "issue-5d-batch-cover-1-PROPOSAL.json",
    "speed-1": "issue-5d-batch-speed-1-PROPOSAL.json",
}


def _recorded_proposal_identities() -> dict[str, str]:
    """What the committed artifact says each batch's reviewer accepted from."""
    with open(COMMITTED_ARTIFACT, encoding="utf-8") as handle:
        document = json.load(handle)
    return {
        batch["batch_id"]: batch["proposal_identity"]
        for batch in document["acceptance"]["batches"]
    }


def test_every_accepted_batch_names_a_retained_proposal() -> None:
    """No accepted batch is missing from the table below.

    Without this, accepting an eighth batch and forgetting to retain its
    proposal would leave the parameterization quietly covering seven of eight.
    """
    assert set(_recorded_proposal_identities()) == set(REVIEWED_PROPOSALS)


@pytest.mark.parametrize("batch_id", sorted(REVIEWED_PROPOSALS))
def test_a_batchs_recorded_proposal_identity_is_still_derivable(batch_id: str) -> None:
    """Load the retained bytes and re-derive what acceptance recorded.

    ``expected_identity`` makes the loader itself refuse a mismatch, so this
    would fail at the call rather than at an assertion; the assertion after it
    states the property for a reader.
    """
    path = REVIEW_NOTES / REVIEWED_PROPOSALS[batch_id]
    recorded = _recorded_proposal_identities()[batch_id]
    proposal = load_proposal(path, expected_identity=recorded)
    assert proposal_identity(proposal) == recorded


def test_a_loaded_proposal_is_proposed_not_accepted() -> None:
    """The one field the loader supplies rather than reads.

    A proposal file states no review state, and it must not: a file that could
    declare its own spans accepted would be acceptance by authorship. The loader
    stamps PROPOSED, ``accept_proposal`` is what stamps ACCEPTED, and review
    state reaches no identity either way.
    """
    proposal = load_proposal(REVIEW_NOTES / REVIEWED_PROPOSALS["speed-1"])
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }


def test_loading_a_proposal_the_caller_did_not_mean_is_refused() -> None:
    """Naming one proposal and reading another is caught at the load.

    Swapping two retained files is a single-character mistake in a path. Caught
    here, it is a refusal; caught nowhere, it is a merge whose bytes match
    nothing retained and whose cause is several steps upstream.
    """
    recorded = _recorded_proposal_identities()
    with pytest.raises(ProposalLoadError, match="not the .* this caller named"):
        load_proposal(
            REVIEW_NOTES / REVIEWED_PROPOSALS["cover-1"],
            expected_identity=recorded["speed-1"],
        )


def test_a_malformed_proposal_fails_as_a_proposal(tmp_path: pathlib.Path) -> None:
    """The inner readers are the oracle's; the failure reported is not.

    ``load_proposal`` reuses the committed readers rather than growing a second
    one, so a structural failure originates as an ``OracleLoadError``. What
    reaches the caller says a proposal would not load, because that is what
    happened — nothing here was an oracle.
    """
    source = REVIEW_NOTES / REVIEWED_PROPOSALS["speed-1"]
    with open(source, encoding="utf-8") as handle:
        document = json.load(handle)
    del document["proposed_representation"]["components"][0]["semantic_key"]
    broken = tmp_path / source.name
    with open(broken, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle)

    with pytest.raises(ProposalLoadError, match=source.name):
        load_proposal(broken)


def test_the_committed_artifact_is_what_the_production_writer_writes() -> None:
    """The committed bytes and the one serialization form, compared directly.

    The reproduction modules rebuild a merge and compare it to a file; this
    compares the file to itself through the writer, which is the narrower claim
    and the one that isolates the form. If ``serialize_accepted_inputs`` ever
    disagreed with the committed corpus, every reproduction would fail at once
    and blame its merge.
    """
    written = serialize_accepted_inputs(load_accepted_inputs(COMMITTED_ARTIFACT))
    assert written == COMMITTED_ARTIFACT.read_bytes().replace(b"\r\n", b"\n")


# -- the declared shape is honoured, not assumed ------------------------------
#
# ``load_proposal`` used to read ``proposal_schema_version`` nowhere. A retained
# file declaring a shape this build cannot state the meaning of was rebuilt
# under the current rules and restamped with the current constant — and because
# the restamped payload re-derived the old identity, passing the recorded
# ``expected_identity`` *confirmed* the forgery rather than catching it. Every
# case below is refused before reconstruction and before the identity check, so
# supplying the recorded identity changes nothing.


def _speed_copy(tmp_path: pathlib.Path, **mutations: object) -> pathlib.Path:
    """The retained Speed proposal, byte-for-byte except *mutations*.

    A ``None`` value deletes the key. The original is never touched: it is
    accepted review evidence.
    """
    with open(REVIEW_NOTES / REVIEWED_PROPOSALS["speed-1"], encoding="utf-8") as handle:
        document = json.load(handle)
    for key, value in mutations.items():
        if value is None:
            del document[key]
        else:
            document[key] = value
    path = tmp_path / "speed-1-copy.json"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle)
    return path


def test_a_version_this_build_cannot_read_is_refused_despite_a_matching_identity(
    tmp_path: pathlib.Path,
) -> None:
    """The exact probe: one field changed, the recorded identity supplied."""
    path = _speed_copy(tmp_path, proposal_schema_version="unsupported-proposal-999")
    recorded = _recorded_proposal_identities()["speed-1"]

    with pytest.raises(ProposalLoadError, match="not a shape this build reads"):
        load_proposal(path, expected_identity=recorded)


@pytest.mark.parametrize(
    "declared", [None, 999, ["5d-proposal-1"]], ids=["missing", "int", "list"]
)
def test_a_proposal_that_states_no_readable_version_is_refused(
    tmp_path: pathlib.Path, declared: object
) -> None:
    """Absent and mistyped are the same failure: the file states no shape.

    Not coerced, and not defaulted to the current constant — defaulting is what
    let the restamp happen.
    """
    path = _speed_copy(tmp_path, proposal_schema_version=declared)
    with pytest.raises(ProposalLoadError, match="is not a string"):
        load_proposal(
            path, expected_identity=_recorded_proposal_identities()["speed-1"]
        )


def test_envelope_content_the_declared_version_does_not_state_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A key nobody reads is a claim nobody checked.

    A proposal is read precisely to establish what a human was shown, so a file
    carrying content outside its declared envelope is refused rather than
    loaded with that content dropped on the floor.
    """
    path = _speed_copy(tmp_path, reviewer_note="read in full, looks fine")
    with pytest.raises(ProposalLoadError, match="unexpected \\['reviewer_note'\\]"):
        load_proposal(
            path, expected_identity=_recorded_proposal_identities()["speed-1"]
        )


def test_an_inventory_carried_under_the_shape_that_states_none_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """The file-side twin of the writer's refusal.

    ``5d-proposal-1`` states no review inventory, so units carried under it
    would sit outside the identity an acceptance records — which is precisely
    the gap that made a widened inventory inherit an acceptance.
    """
    path = _speed_copy(
        tmp_path,
        proposed_review_units=[
            {
                "unit_id": "unit-forged",
                "kind": "entry",
                "leaf_ids": ["leaf-speed"],
                "expected_rules": [],
                "supporting_groups": [],
                "excluded_groups": [],
            }
        ],
    )
    with pytest.raises(
        ProposalLoadError, match="unexpected \\['proposed_review_units'\\]"
    ):
        load_proposal(path)


def test_a_readable_version_still_reaches_the_shape_checks(
    tmp_path: pathlib.Path,
) -> None:
    """The version check screens; it does not replace what it screens for.

    A file declaring a shape this build reads is still read as that shape, and
    a proposed span missing the rationale its author stated still fails there.
    """
    with open(REVIEW_NOTES / REVIEWED_PROPOSALS["speed-1"], encoding="utf-8") as handle:
        spans = json.load(handle)["proposed_spans"]
    del spans[0]["rationale"]

    with pytest.raises(ProposalLoadError, match="rationale"):
        load_proposal(_speed_copy(tmp_path, proposed_spans=spans))
