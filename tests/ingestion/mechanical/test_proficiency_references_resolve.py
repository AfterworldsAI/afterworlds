"""Proficiency's four printed pointers resolve, once — CRD Issue 5d.

``proficiency-1`` cites *Challenge Rating*, *Expertise*, the *Skills table* and
*Actions*. ``proficiency-destinations-1`` reviews those four destinations from
source. Each proposal alone reports the other's records as unknown, which is
what the two proposal modules pin; what neither of them can show is the thing
the batch pair exists for: that **in the combined data the four links resolve,
each to exactly one reviewed record, and that a missing, blanked or repointed
destination fails.**

So this module merges the three through the production acceptance service — the
committed accepted authority, then the destinations, then the revised
Proficiency — and checks the merged representation. Nothing is accepted into the
corpus here: ``accept_proposal`` returns an in-memory value, has no output path,
and the committed artifact is asserted byte-identical afterwards.

``_validate_relationships_and_references`` is called directly rather than through
``validate_representation``, because the merged draft's prose extent is over 5c's
whole release and the reference relation is the only part of the report this
module is about. The proposal modules each run the full ``validate_representation``
on their own draft, so the extent checks are covered where they can be answered;
importing one private validator to ask one question is the repository's existing
practice for exactly this (see ``test_conditions_schema_2.py``).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import (
    load_proposal,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.validation import (
    _validate_relationships_and_references,
)

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
DESTINATIONS_PATH = (
    REVIEW_NOTES / "issue-5d-batch-proficiency-destinations-1-PROPOSAL.json"
)
PROFICIENCY_PATH = REVIEW_NOTES / "issue-5d-batch-proficiency-1-PROPOSAL.json"
COMMITTED_ARTIFACT = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

PROFICIENCY = "play.proficiency"
GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"
PLAYING_SCOPE = "srd-5.2.1/playing-the-game"

DESTINATIONS_UNITS = (
    "proficiency-destinations-1-actions-section",
    "proficiency-destinations-1-challenge-rating",
    "proficiency-destinations-1-expertise",
    "proficiency-destinations-1-skills-table",
)
PROFICIENCY_UNIT = "proficiency-1-section"

#: The four links this task closes: ``(scope, printed wording) -> destination``.
#: All four are authored by ``proficiency-1``; the destination of each is minted
#: by ``proficiency-destinations-1``.
ORIGINATING_LINKS = {
    (GLOSSARY_SCOPE, "Challenge Rating"): "glossary.challenge_rating",
    (GLOSSARY_SCOPE, "Expertise"): "glossary.expertise",
    (PLAYING_SCOPE, "Skills table"): "play.skills",
    (PLAYING_SCOPE, "Actions"): "play.actions",
}

#: The ten outward pointers the **already accepted** ``glossary.speed`` entry
#: authors from source at destinations no batch has reviewed yet. They are
#: reported, which is the honest state: 5c prints them, ``speed-1`` represented
#: them, and the movement entries they name are a later batch's work and outside
#: this task. The merged report must be *exactly* these ten — this task neither
#: silences one nor adds an eleventh, and a later movement batch closing them
#: has to change this list to do it.
PREEXISTING_OUTWARD = tuple(
    f"reference {GLOSSARY_SCOPE}:{text!r}: unknown target record {target}"
    for text, target in sorted(
        {
            "Burrow Speed": "glossary.burrow_speed",
            "Climb Speed": "glossary.climb_speed",
            "Climbing": "glossary.climbing",
            "Concentration": "glossary.concentration",
            "Crawling": "glossary.crawling",
            "Fly Speed": "glossary.fly_speed",
            "Flying": "glossary.flying",
            "Jumping": "glossary.jumping",
            "Swim Speed": "glossary.swim_speed",
            "Swimming": "glossary.swimming",
        }.items()
    )
)


def _merged():  # type: ignore[no-untyped-def]
    """The committed authority, the destinations and the revised Proficiency.

    In acceptance order: a destination has to exist before the batch that points
    at it can be accepted, which is the ordering this task's handoff states.
    """
    accepted = load_accepted_inputs(COMMITTED_ARTIFACT)
    for path, batch_id, units in (
        (
            DESTINATIONS_PATH,
            "proficiency-destinations-1-test-evidence-only",
            DESTINATIONS_UNITS,
        ),
        (PROFICIENCY_PATH, "proficiency-1-test-evidence-only", (PROFICIENCY_UNIT,)),
    ):
        proposal = load_proposal(path)
        accepted = accept_proposal(
            proposal,
            batch_id=batch_id,
            rule="every span and every review unit this proposal proposes",
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            reviewer="test-evidence-only",
            accepted_at="2026-09-17T00:00:00Z",
            prior=accepted,
            resolved_review_units=units,
        )
    return accepted


def _targets_by_citation(draft) -> dict[tuple[str, str], set[str]]:  # type: ignore[no-untyped-def]
    """Every destination each ``(scope, printed wording)`` resolves to.

    A citation resolving to more than one record is the ambiguity the production
    check reports; collecting it as a set is what lets "resolves uniquely" be
    asserted rather than assumed from a passing report.
    """
    targets: dict[tuple[str, str], set[str]] = {}
    for ref in draft.references:
        targets.setdefault((ref.scope_key, ref.source_text), set()).add(
            ref.target_record_key
        )
    return targets


def _reference(draft, source_text: str, from_record_key: str):  # type: ignore[no-untyped-def]
    (ref,) = [
        r
        for r in draft.references
        if r.source_text == source_text and r.from_record_key == from_record_key
    ]
    return ref


def _replace_reference(draft, old, new):  # type: ignore[no-untyped-def]
    """Swap one reference, leaving its provenance claim behind deliberately.

    The provenance key includes the destination, so a repointed reference has a
    claim addressing an element nobody declared. That is a second, separate
    finding these tests do not assert on; each asserts the reference finding it
    is about, and the report carrying more than one finding for one broken edit
    is the fail-closed behaviour, not a surprise.
    """
    return dataclasses.replace(
        draft,
        references=tuple(new if r == old else r for r in draft.references),
    )


def test_all_four_originating_links_resolve_in_the_merged_data() -> None:
    """The point of the batch pair: no finding of this task's survives the merge.

    Each of the four resolves to exactly one record and that record is carried
    by the merged representation. The report is then asserted whole, against the
    accepted corpus's own ten pre-existing outward pointers, rather than filtered
    for the four words this task is about: a filtered assertion would pass while
    this task's thirteen destination links quietly broke something else.
    """
    merged = _merged().oracle.representation
    record_keys = {r.semantic_key for r in merged.records}
    targets = _targets_by_citation(merged)

    for citation, destination in ORIGINATING_LINKS.items():
        assert targets[citation] == {destination}, citation
        assert destination in record_keys

    assert tuple(sorted(_validate_relationships_and_references(merged))) == (
        PREEXISTING_OUTWARD
    )


def test_every_citation_in_the_merged_data_resolves_uniquely() -> None:
    """Not just the four: one scope and one wording mean one record, corpus-wide.

    The twelve Action-table links repeat printed words the accepted
    ``glossary.action`` entry already cites. Repeating a citation is legitimate —
    several records may point at one rule — but resolving it two ways is not, so
    the whole merged reference relation is checked rather than this task's own
    additions.
    """
    accepted = load_accepted_inputs(COMMITTED_ARTIFACT)
    merged = _merged().oracle.representation

    multiply_resolved = {
        citation: sorted(targets)
        for citation, targets in _targets_by_citation(merged).items()
        if len(targets) > 1
    }
    assert multiply_resolved == {}

    # Every accepted citation still resolves where it did, and the merge is
    # additive: the four new links plus the destinations' thirteen.
    before = _targets_by_citation(accepted.oracle.representation)
    after = _targets_by_citation(merged)
    assert all(after[citation] == targets for citation, targets in before.items())
    assert len(merged.references) == len(accepted.oracle.representation.references) + 17


def test_a_missing_destination_record_reopens_the_link() -> None:
    """The link is checked against records that exist, not against a key list."""
    merged = _merged().oracle.representation
    without_skills = dataclasses.replace(
        merged,
        records=tuple(r for r in merged.records if r.semantic_key != "play.skills"),
    )
    findings = _validate_relationships_and_references(without_skills)
    assert (
        f"reference {PLAYING_SCOPE}:'Skills table': unknown target record play.skills"
        in findings
    )


def test_a_blanked_destination_reopens_the_link_as_unresolved() -> None:
    """Losing a destination is a different failure and still a failure."""
    merged = _merged().oracle.representation
    ref = _reference(merged, "Actions", PROFICIENCY)
    findings = _validate_relationships_and_references(
        _replace_reference(merged, ref, dataclasses.replace(ref, target_record_key=""))
    )
    assert f"reference {PLAYING_SCOPE}:'Actions': unresolved reference" in findings


def test_repointing_a_link_at_the_wrong_record_is_ambiguous() -> None:
    """A wrong destination that happens to exist is caught by the collision.

    ``play.actions`` cites "Attack" at ``action.attack``, the same record the
    accepted glossary entry cites for the same word in the same scope. Pointing
    this build's copy at ``action.dash`` instead leaves a record that exists, so
    "unknown target" cannot catch it — what catches it is that one printed word
    in one scope would now resolve two ways.
    """
    merged = _merged().oracle.representation
    ref = _reference(merged, "Attack", "play.actions")
    assert ref.target_record_key == "action.attack"
    findings = _validate_relationships_and_references(
        _replace_reference(
            merged, ref, dataclasses.replace(ref, target_record_key="action.dash")
        )
    )
    (ambiguous,) = [f for f in findings if "ambiguous" in f]
    assert ambiguous.startswith(f"reference {GLOSSARY_SCOPE}:'Attack': ")
    assert "['action.attack', 'action.dash']" in ambiguous


def test_the_resolution_survives_the_production_writer_and_loader(
    tmp_path: pathlib.Path,
) -> None:
    """Both proposals and the merged authority, through production serialization.

    A resolution that only holds in memory would be undone by the next
    persistence round trip. Each proposal is rebuilt from its own canonical
    payload and must derive the same identity; the merged authority is written
    with the production serializer, read back with the production loader, and
    rechecked.
    """
    for path in (DESTINATIONS_PATH, PROFICIENCY_PATH):
        proposal = load_proposal(path)
        rebuilt = tmp_path / f"rebuilt-{path.name}"
        rebuilt.write_text(
            json.dumps(
                proposal_payload(proposal), indent=1, sort_keys=True, ensure_ascii=False
            ),
            encoding="utf-8",
            newline="\n",
        )
        assert proposal_identity(load_proposal(rebuilt)) == proposal_identity(proposal)

    merged = _merged()
    written = tmp_path / "merged.json"
    written.write_text(
        json.dumps(accepted_inputs_payload(merged), indent=1, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    reloaded = load_accepted_inputs(written)
    assert (
        tuple(
            sorted(
                _validate_relationships_and_references(reloaded.oracle.representation)
            )
        )
        == PREEXISTING_OUTWARD
    )
    assert _targets_by_citation(reloaded.oracle.representation) == (
        _targets_by_citation(merged.oracle.representation)
    )


def test_the_accepted_corpus_is_untouched_by_all_of_this() -> None:
    """Seven accepted batches, forty-eight records, and the same bytes on disk.

    This module's whole subject is a merge that has not been accepted. If the
    merge ever became a write, this is the assertion that would say so.
    """
    before = hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest()
    accepted = load_accepted_inputs(COMMITTED_ARTIFACT)
    merged = _merged()

    assert len(merged.batches) == len(accepted.batches) + 2
    assert merged.batches[: len(accepted.batches)] == accepted.batches
    assert {r.semantic_key for r in accepted.oracle.representation.records} < {
        r.semantic_key for r in merged.oracle.representation.records
    }
    assert (
        len(merged.oracle.representation.records)
        == len(accepted.oracle.representation.records) + 5
    )
    assert hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest() == before
