"""The retained ``proficiency-1`` proposal is loadable coverage — CRD Issue 5d.

``proficiency-1`` is the first regular-section pilot: *Playing the Game >
Proficiency*, proposed and **not accepted**. Nothing here accepts it. The
acceptance exercised below is in-memory evidence that the proposal is
structurally acceptable through the production path — it writes no file, and
this module asserts that the committed accepted artifact is byte-identical
afterwards.

What is pinned, and why each pin is the one that would catch a real regression:

* the retained bytes still derive the identity a reviewer would be shown;
* the section's review unit is coverage the representation actually satisfies
  (``review_unit_violations``, the production check, on the loaded artifact);
* **all eight Proficiency Bonus bands are present**, four from the table
  container and four from the paragraph 5c represents *outside* it. The
  progression is the thing a table-shaped review silently truncates, so the
  band set is asserted as an exact set of triples rather than a count; and
* dropping one of those later rows is *reported*. That is the whole claim the
  review unit makes, so it is proved by mutation rather than assumed; and
* the two links whose destination this build has not represented yet are
  **outstanding obligations**, not notes. Each is a reference with an empty
  ``target_record_key``, so ``validate_representation`` reports it as
  ``unresolved reference`` and the publication gate is fail-closed on it. The
  mutations below prove the properties that make it an obligation rather than a
  comment: it survives serialization and reconstruction, deleting either half of
  it is reported, a *resolved sibling* citing the same words cannot close it,
  and the only thing that does close it is filling in this reference's own
  destination.

Deliberately not added to ``test_retained_proposals.py``: that module is over
proposals an accepted batch names, and no batch names this one.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.bound_corpus import (
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.policy import SEMANTIC_POLICY_VERSION
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    PROPOSAL_SCHEMA_VERSION_2,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentHandling,
    FactFamily,
    ProficiencyBonusBandFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import validate_representation

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
PROPOSAL_PATH = REVIEW_NOTES / "issue-5d-batch-proficiency-1-PROPOSAL.json"
COMMITTED_ARTIFACT = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: The identity the review packet reports and a reviewer would be shown.
PROPOSAL_IDENTITY = "c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4"  # noqa: E501  # pragma: allowlist secret

RECORD = "play.proficiency"
UNIT_ID = "proficiency-1-section"
SCOPE = "srd-5.2.1/rules-glossary"
#: The two outstanding pointers resolve into *Playing the Game*, not the
#: Rules Glossary: the Skills table is printed in that part and the Actions
#: pointer names its section. ``scope_key`` is the committed resolution
#: scope, so authoring them under the glossary scope would have stated that
#: a glossary entry is the thing that closes them, and a later glossary
#: review could then have looked like the discharge of an obligation it
#: never carried. Neither destination is minted here.
PLAYING_SCOPE = "srd-5.2.1/playing-the-game"

#: The section's five printed pointers, as authored, with the scope each
#: resolves in. Two name a Rules Glossary entry no accepted batch has minted;
#: two name nothing yet, in Playing the Game, and are the outstanding links; the
#: fifth ("Character Creation") points outside this build's corpus and is prose,
#: so it is absent here by design.
EXPECTED_REFERENCES = {
    ("proficiency_bonus_basis", "Challenge Rating", "glossary.challenge_rating"),
    ("bonus_does_not_stack", "Expertise", "glossary.expertise"),
    ("skill_list", "Skills table", ""),
    ("skill_relevance_sources", "Actions", ""),
}

#: Which scope each pointer is committed to resolve in, keyed by its printed
#: wording. Written out rather than derived from the draft: the whole point of
#: the correction is that the two are not the same scope.
EXPECTED_SCOPES = {
    "Challenge Rating": SCOPE,
    "Expertise": SCOPE,
    "Skills table": PLAYING_SCOPE,
    "Actions": PLAYING_SCOPE,
}

#: The exact standalone report for the untampered proposal. Two unminted
#: destinations and two outstanding links, and nothing else: a fifth finding of
#: any kind, or an outstanding link quietly acquiring a target, fails here.
EXPECTED_FINDINGS = (
    f"reference {PLAYING_SCOPE}:'Actions': unresolved reference",
    f"reference {PLAYING_SCOPE}:'Skills table': unresolved reference",
    f"reference {SCOPE}:'Challenge Rating': unknown target record "
    "glossary.challenge_rating",
    f"reference {SCOPE}:'Expertise': unknown target record glossary.expertise",
)

#: ``(bonus, minimum, maximum)``. The first row prints "Up to 4", which states
#: no lower bound, so the band is open below rather than starting at 1. The
#: last four are the rows 5c represents outside the table container.
EXPECTED_BANDS = {
    (2, None, 4),
    (3, 5, 8),
    (4, 9, 12),
    (5, 13, 16),
    (6, 17, 20),
    (7, 21, 24),
    (8, 25, 28),
    (9, 29, 30),
}


def _proposal():  # type: ignore[no-untyped-def]
    return load_proposal(PROPOSAL_PATH)


def _ledger(proposal) -> ClassificationLedger:  # type: ignore[no-untyped-def]
    """The proposal's own spans, under the release and policy it declares."""
    return ClassificationLedger(
        package_uuid=proposal.binding.package_uuid,
        release_version=proposal.binding.release_version,
        policy_version=proposal.policy_version,
        policy_hash=proposal.policy_hash,
        spans=tuple(p.span for p in proposal.proposed_spans),
        batches=(),
        acceptances=(),
    )


def _corpus(proposal) -> BoundCorpusSnapshot:  # type: ignore[no-untyped-def]
    """A snapshot of the bound release over exactly the leaves this batch reads.

    Derived from the proposal rather than re-parsed from the PDF: 5c's own
    ``build_candidate`` is a full release parse, far too heavy for a test, and
    the reference checks under test read no release state at all. Each chunk is
    given the whole of the leaf it binds, so every prose binding is covered and
    the report below is the reference report, not coverage noise. That the
    untampered draft yields exactly :data:`EXPECTED_FINDINGS` is what shows the
    snapshot is not manufacturing or hiding a finding.
    """
    spans = [p.span for p in proposal.proposed_spans]
    leaf_lengths: dict[str, int] = {}
    for span in spans:
        leaf_lengths[span.leaf_id] = max(
            leaf_lengths.get(span.leaf_id, 0), span.char_end
        )
    leaf_of = {span.span_id: span.leaf_id for span in spans}
    edges = {
        (binding.chunk_id, leaf_of[binding.span_id]): ChunkCoverage(
            chunk_id=binding.chunk_id,
            leaf_id=leaf_of[binding.span_id],
            cover_start=0,
            cover_end=leaf_lengths[leaf_of[binding.span_id]],
            role="authoritative",
            projection_id="proficiency-1-proposal-test",
        )
        for binding in proposal.proposed_representation.prose_bindings
    }
    return BoundCorpusSnapshot(
        package_uuid=proposal.binding.package_uuid,
        release_version=proposal.binding.release_version,
        leaf_lengths=leaf_lengths,
        chunk_coverage=tuple(edges.values()),
    )


def _findings(proposal, draft) -> tuple[str, ...]:  # type: ignore[no-untyped-def]
    return tuple(
        sorted(validate_representation(draft, _ledger(proposal), _corpus(proposal)))
    )


def _outstanding(draft, source_text: str):  # type: ignore[no-untyped-def]
    (ref,) = [
        r
        for r in draft.references
        if r.source_text == source_text and not r.target_record_key
    ]
    return ref


def _claim_for(draft, ref):  # type: ignore[no-untyped-def]
    key = reference_target_key(ref)
    (claim,) = [
        c
        for c in draft.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE and c.target_key == key
    ]
    return claim


def test_the_retained_bytes_still_derive_the_reviewed_identity() -> None:
    """A proposal nobody can reproduce is not evidence of what was reviewed."""
    proposal = _proposal()
    assert proposal_identity(proposal) == PROPOSAL_IDENTITY
    assert proposal.proposal_schema_version == PROPOSAL_SCHEMA_VERSION_2
    assert proposal.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert proposal.schema_hash == representation_schema_hash()
    assert proposal.policy_version == SEMANTIC_POLICY_VERSION


def test_nothing_in_this_proposal_is_accepted() -> None:
    """It is a proposal. Every proposed row says so, and no batch names it."""
    proposal = _proposal()
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    named = {
        batch.proposal_identity
        for batch in load_accepted_inputs(COMMITTED_ARTIFACT).batches
    }
    assert PROPOSAL_IDENTITY not in named


def test_the_section_is_reviewed_as_one_unit_over_thirty_leaves() -> None:
    """One SECTION unit. The table container alone would have truncated it."""
    proposal = _proposal()
    (unit,) = proposal.proposed_review_units
    assert unit.unit_id == UNIT_ID
    assert unit.kind is ReviewUnitKind.SECTION
    assert len(unit.leaf_ids) == 30
    assert len(set(unit.leaf_ids)) == 30
    # 5c excludes the running footer on page 8 of this stretch; a unit naming it
    # would claim review of source the accounting population does not contain.
    assert "bda26fa3-3c42-57a6-93bf-69506f41b67c" not in unit.leaf_ids


def test_the_unit_is_coverage_the_representation_satisfies() -> None:
    """The production coverage check, on the loaded artifact, reports nothing."""
    proposal = _proposal()
    assert (
        review_unit_violations(
            proposal.proposed_review_units,
            proposal.proposed_representation,
            proposal.policy_version,
            tuple(p.span for p in proposal.proposed_spans),
        )
        == []
    )


def test_every_proficiency_bonus_band_is_present() -> None:
    """All eight rows, including the four represented outside the table."""
    proposal = _proposal()
    (table,) = [
        c
        for c in proposal.proposed_representation.components
        if c.semantic_key == "proficiency_bonus_table"
    ]
    assert table.handling is ComponentHandling.STRUCTURED
    bands = [f for f in table.all_facts() if isinstance(f, ProficiencyBonusBandFact)]
    assert {(b.bonus, b.minimum, b.maximum) for b in bands} == EXPECTED_BANDS
    assert len(bands) == len(EXPECTED_BANDS)

    # Each band is expected by the unit under its own family, so an omitted row
    # is a missing expected rule rather than an unnoticed gap.
    band_rules = [
        rule
        for unit in proposal.proposed_review_units
        for rule in unit.expected_rules
        if rule.fact_family == FactFamily.PROFICIENCY_BONUS_BAND.value
    ]
    assert len(band_rules) == 8
    assert all(rule.record_key == RECORD for rule in band_rules)


def test_dropping_a_later_row_is_reported() -> None:
    """The rows outside the table container are exactly the ones at risk."""
    from dataclasses import replace

    proposal = _proposal()
    draft = proposal.proposed_representation
    shortened = replace(
        draft,
        components=tuple(
            (
                replace(
                    c,
                    facts=tuple(
                        f
                        for f in c.facts
                        if not (
                            isinstance(f, ProficiencyBonusBandFact) and f.minimum == 29
                        )
                    ),
                )
                if c.semantic_key == "proficiency_bonus_table"
                else c
            )
            for c in draft.components
        ),
    )
    findings = review_unit_violations(
        proposal.proposed_review_units,
        shortened,
        proposal.policy_version,
        tuple(p.span for p in proposal.proposed_spans),
    )
    assert findings
    assert all("proficiency_bonus_table" in finding for finding in findings)


def test_in_memory_acceptance_is_evidence_and_writes_nothing() -> None:
    """Structurally acceptable through the production path. Not an acceptance.

    ``accept_proposal`` returns an in-memory :class:`AcceptedInputs`; it has no
    output path and persists nothing. The digest comparison is what makes that
    claim checkable here rather than trusted, because this module would
    otherwise be the one place a stray write could hide.
    """
    before = hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest()
    proposal = _proposal()
    prior = load_accepted_inputs(COMMITTED_ARTIFACT)

    accepted = accept_proposal(
        proposal,
        batch_id="proficiency-1-test-evidence-only",
        rule="every span and the one review unit this proposal proposes",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="test-evidence-only",
        accepted_at="2026-09-17T00:00:00Z",
        prior=prior,
        resolved_review_units=(UNIT_ID,),
    )

    # The prior was accepted under an earlier schema, so reaching schema 13 is a
    # verified lift path rather than a re-declaration.
    assert accepted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert accepted.oracle.schema_hash == representation_schema_hash()
    assert len(accepted.batches) == len(prior.batches) + 1
    assert {u.unit_id for u in accepted.oracle.review_units} == {UNIT_ID}

    assert hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest() == before


def test_the_deferred_links_are_authored_as_outstanding_obligations() -> None:
    """A note about a missing link cannot fail. An unresolved reference does.

    Both links are committed with their citing component, their printed wording
    and their span; only the destination is absent. The report distinguishes
    that from a named destination nothing has minted, which is the distinction
    that makes accidental closure impossible: no key exists that a later batch
    could mint to resolve these.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    assert {
        (r.from_component_key, r.source_text, r.target_record_key)
        for r in draft.references
    } == EXPECTED_REFERENCES
    assert {(r.source_text, r.scope_key) for r in draft.references} == set(
        EXPECTED_SCOPES.items()
    )
    assert _findings(proposal, draft) == EXPECTED_FINDINGS
    # Each outstanding link carries its own provenance to the span the pointer
    # is printed in, so it is evidence of where the obligation came from.
    for text, clause_leaf in (
        ("Skills table", "skill_list"),
        ("Actions", "skill_relevance_sources"),
    ):
        ref = _outstanding(draft, text)
        assert ref.from_component_key == clause_leaf
        assert _claim_for(draft, ref).role is ProvenanceRole.CONTEXTUAL


def test_an_outstanding_link_survives_serialization_and_reconstruction(
    tmp_path: pathlib.Path,
) -> None:
    """Through the production writer and loader, not a copy of the draft.

    An obligation that lives only in the in-memory draft would be discharged by
    the next persistence round trip. This writes the accepted payload the
    production serializer produces to a temporary path and reads it back with
    the production loader.
    """
    proposal = _proposal()
    accepted = accept_proposal(
        proposal,
        batch_id="proficiency-1-test-evidence-only",
        rule="every span and the one review unit this proposal proposes",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="test-evidence-only",
        accepted_at="2026-09-17T00:00:00Z",
        prior=load_accepted_inputs(COMMITTED_ARTIFACT),
        resolved_review_units=(UNIT_ID,),
    )
    path = tmp_path / "reconstructed.json"
    path.write_text(
        json.dumps(accepted_inputs_payload(accepted), indent=1, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    reloaded = load_accepted_inputs(path)
    assert {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in reloaded.oracle.representation.references
        if not r.target_record_key
    } == {
        (RECORD, "skill_list", "Skills table", PLAYING_SCOPE),
        (RECORD, "skill_relevance_sources", "Actions", PLAYING_SCOPE),
    }


def test_deleting_either_half_of_an_outstanding_link_is_reported() -> None:
    """Omission is a finding, in both directions, through the closed relation.

    Dropping the reference leaves its provenance claiming an element nobody
    declared. Dropping the provenance leaves a reference with no evidence of
    where it was read. Either way the report names the exact link, so the
    obligation cannot be removed quietly.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    ref = _outstanding(draft, "Skills table")
    key = reference_target_key(ref)

    without_reference = _findings(
        proposal,
        dataclasses.replace(
            draft, references=tuple(r for r in draft.references if r != ref)
        ),
    )
    assert any(
        f.startswith("provenance reference") and "undeclared element" in f
        for f in without_reference
    )
    assert f"reference {PLAYING_SCOPE}:'Skills table': unresolved reference" not in (
        without_reference
    )

    without_provenance = _findings(
        proposal,
        dataclasses.replace(
            draft,
            provenance=tuple(
                c
                for c in draft.provenance
                if not (
                    c.target_kind is ProvenanceTargetKind.REFERENCE
                    and c.target_key == key
                )
            ),
        ),
    )
    assert f"reference {list(key)}: no provenance to a 5c leaf subspan" in (
        without_provenance
    )
    assert f"reference {PLAYING_SCOPE}:'Skills table': unresolved reference" in (
        without_provenance
    )


def test_a_resolved_sibling_citing_the_same_words_cannot_close_it() -> None:
    """The realistic premature closure, and it is refused twice over.

    A later batch authoring the same printed wording with a real destination
    does not resolve *this* link. The report keeps the unresolved finding and
    adds an ambiguity finding, because one scope and one wording now resolve
    two ways.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    ref = _outstanding(draft, "Skills table")
    # ``play.proficiency`` stands in for a real destination: it is the one
    # record this draft declares, so the sibling is resolved and *known*, which
    # is the strongest form the premature closure could take.
    sibling = dataclasses.replace(ref, target_record_key=RECORD)
    findings = _findings(
        proposal,
        dataclasses.replace(
            draft,
            references=draft.references + (sibling,),
            provenance=draft.provenance
            + (
                ProvenanceClaim(
                    ProvenanceTargetKind.REFERENCE,
                    reference_target_key(sibling),
                    _claim_for(draft, ref).span_id,
                    ProvenanceRole.CONTEXTUAL,
                ),
            ),
        ),
    )
    assert f"reference {PLAYING_SCOPE}:'Skills table': unresolved reference" in findings
    (ambiguous,) = [f for f in findings if "ambiguous" in f]
    assert ambiguous.startswith(f"reference {PLAYING_SCOPE}:'Skills table': ")
    assert f"['', '{RECORD}']" in ambiguous


def test_filling_in_this_reference_is_the_only_thing_that_closes_it() -> None:
    """And when it is filled in, the obligation is gone — not suppressed.

    The closing edit is to this reference's own destination, which is an
    accepted-content change and reviewed as one.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    ref = _outstanding(draft, "Skills table")
    key = reference_target_key(ref)
    resolved = dataclasses.replace(ref, target_record_key=RECORD)
    findings = _findings(
        proposal,
        dataclasses.replace(
            draft,
            references=tuple(resolved if r == ref else r for r in draft.references),
            provenance=tuple(
                (
                    ProvenanceClaim(
                        ProvenanceTargetKind.REFERENCE,
                        reference_target_key(resolved),
                        c.span_id,
                        c.role,
                    )
                    if (
                        c.target_kind is ProvenanceTargetKind.REFERENCE
                        and c.target_key == key
                    )
                    else c
                )
                for c in draft.provenance
            ),
        ),
    )
    assert findings == tuple(f for f in EXPECTED_FINDINGS if "'Skills table'" not in f)
