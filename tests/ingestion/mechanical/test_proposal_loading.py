"""The production proposal loader on retained review evidence — CRD Issue 5d.

``load_proposal`` is how a reviewed proposal is read back, so it must stamp no
acceptance, refuse a file other than the one the caller named, and refuse a file
whose declared shape it cannot read rather than restamping it. Exercised on the
Owner-approved ``conditions-pilot`` proposal of the clean restart and on copies of
it; the retained file itself is accepted review evidence and is never modified.

This module used to load the nine reviewed proposals of the original 5d
artifact ``srd-5-2-1-corpus-36b786d8-fa2.json``. That artifact was removed under
Step 5 of the Recorded Owner Decision of 21 September 2026, so the per-batch
derivability check over it went with it; the current chain's proposal
identities are derived in ``test_committed_accepted_authority``.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.proposal import (
    ProposalLoadError,
    load_proposal,
)
from tests.ingestion.mechanical._replacement_chain import identity, proposal_path

#: The retained proposal these tests read, and one other to mistake it for.
PROPOSAL = proposal_path("conditions-pilot")
OTHER = proposal_path("actions-pilot")
RECORDED = identity("conditions-pilot")


def test_a_loaded_proposal_is_proposed_not_accepted() -> None:
    """The one field the loader supplies rather than reads.

    A proposal file states no review state, and it must not: a file that could
    declare its own spans accepted would be acceptance by authorship. The loader
    stamps PROPOSED, ``accept_proposal`` is what stamps ACCEPTED, and review
    state reaches no identity either way.
    """
    proposal = load_proposal(PROPOSAL)
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }


def test_loading_a_proposal_the_caller_did_not_mean_is_refused() -> None:
    """Naming one proposal and reading another is caught at the load.

    Swapping two retained files is a single-character mistake in a path. Caught
    here, it is a refusal; caught nowhere, it is a merge whose bytes match
    nothing retained and whose cause is several steps upstream.
    """
    with pytest.raises(ProposalLoadError, match="not the .* this caller named"):
        load_proposal(OTHER, expected_identity=RECORDED)


def test_a_malformed_proposal_fails_as_a_proposal(tmp_path: pathlib.Path) -> None:
    """The inner readers are the oracle's; the failure reported is not.

    ``load_proposal`` reuses the committed readers rather than growing a second
    one, so a structural failure originates as an ``OracleLoadError``. What
    reaches the caller says a proposal would not load, because that is what
    happened — nothing here was an oracle.
    """
    source = PROPOSAL
    with open(source, encoding="utf-8") as handle:
        document = json.load(handle)
    del document["proposed_representation"]["components"][0]["semantic_key"]
    broken = tmp_path / source.name
    with open(broken, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle)

    with pytest.raises(ProposalLoadError, match=source.name):
        load_proposal(broken)


# -- the declared shape is honoured, not assumed ------------------------------
#
# ``load_proposal`` used to read ``proposal_schema_version`` nowhere. A retained
# file declaring a shape this build cannot state the meaning of was rebuilt
# under the current rules and restamped with the current constant — and because
# the restamped payload re-derived the old identity, passing the recorded
# ``expected_identity`` *confirmed* the forgery rather than catching it. Every
# case below is refused before reconstruction and before the identity check, so
# supplying the recorded identity changes nothing.


def _copy(tmp_path: pathlib.Path, **mutations: object) -> pathlib.Path:
    """The retained proposal, byte-for-byte except *mutations*.

    A ``None`` value deletes the key. The original is never touched: it is
    accepted review evidence.
    """
    with open(PROPOSAL, encoding="utf-8") as handle:
        document = json.load(handle)
    for key, value in mutations.items():
        if value is None:
            del document[key]
        else:
            document[key] = value
    path = tmp_path / "proposal-copy.json"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle)
    return path


def test_a_version_this_build_cannot_read_is_refused_despite_a_matching_identity(
    tmp_path: pathlib.Path,
) -> None:
    """The exact probe: one field changed, the recorded identity supplied."""
    path = _copy(tmp_path, proposal_schema_version="unsupported-proposal-999")
    with pytest.raises(ProposalLoadError, match="not a shape this build reads"):
        load_proposal(path, expected_identity=RECORDED)


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
    path = _copy(tmp_path, proposal_schema_version=declared)
    with pytest.raises(ProposalLoadError, match="is not a string"):
        load_proposal(path, expected_identity=RECORDED)


def test_envelope_content_the_declared_version_does_not_state_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A key nobody reads is a claim nobody checked.

    A proposal is read precisely to establish what a human was shown, so a file
    carrying content outside its declared envelope is refused rather than
    loaded with that content dropped on the floor.
    """
    path = _copy(tmp_path, reviewer_note="read in full, looks fine")
    with pytest.raises(ProposalLoadError, match="unexpected \\['reviewer_note'\\]"):
        load_proposal(path, expected_identity=RECORDED)


def test_an_inventory_carried_under_the_shape_that_states_none_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """The file-side twin of the writer's refusal.

    ``5d-proposal-1`` states no review inventory, so units carried under it
    would sit outside the identity an acceptance records — which is precisely
    the gap that made a widened inventory inherit an acceptance. The copy keeps
    the retained proposal's own review units and declares the older shape.
    """
    path = _copy(tmp_path, proposal_schema_version="5d-proposal-1")
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
    with open(PROPOSAL, encoding="utf-8") as handle:
        spans = json.load(handle)["proposed_spans"]
    del spans[0]["rationale"]

    with pytest.raises(ProposalLoadError, match="rationale"):
        load_proposal(_copy(tmp_path, proposed_spans=spans))
