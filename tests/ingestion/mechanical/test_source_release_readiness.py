"""Shared 5d tooling, proved against the replacement 5c release — CRD Issue 5d.

**This module is testing, not acceptance.** Every disposition its fixtures
state is ``UNRESOLVED``, every reviewer name is obviously synthetic, and no SRD
semantics are asserted anywhere. Nothing here creates a pilot semantic record,
writes to ``oracles/``, or publishes or activates a projection. Synthetic
fixture acceptance is testing; the real acceptance of SRD meaning is a human
action. The Owner has taken it over this release, as the recorded chain the
committed oracle holds; this module reads that authority's identity and counts
and deliberately cannot add to it.

What it does prove, against the *actual* new corpus
(``1299484e-c72d-509b-bd8d-d0169ee1f8d2`` / ``5.2.1-corpus.8781d4e0-a3b``) rather
than a synthetic fixture, is that the shared machinery is ready for fresh
authoring over it:

1. **Source/proposal binding.** ``load_bound_corpus`` resolves the replacement
   release's own population, ``leaves_under`` selects a named section of it, and
   the proposal ``seed_proposal`` derives is bound to that release on all six
   coordinates of :class:`ReleaseBinding`.
2. **Truthful unreviewed status.** The accepted authority for the replacement
   release is exactly the Owner's recorded chain, and publishing a draft nobody
   has reviewed against it is refused with a typed outcome,
   ``PublicationOutcome.UNRESOLVED`` — not an exception or a silently-passing
   publication.
3. **Refusal of old or mismatched authority.** The quarantined release is
   refused by identity at the load and oracle seams, and an oracle accepted
   over a different release is refused by the gate as ``MISMATCHED_RELEASE``.
   (The superseded release's committed binding is refused by the oracle
   selector itself; ``test_oracle.py`` proves that.)
4. **Meaningful changes invalidate stale reuse.** ``proposal_identity`` is stable
   across two independent seeds of the same source and moves the moment the
   content a reviewer would read changes.
5. **Review and acceptance stay separate.** A proposal artifact cannot be loaded
   as accepted authority — not by a flag, by shape.

This module is the successor, over the qualified source, of the retired
release's ``test_production_release.py``, which was removed under Step 5 of the
21 September Owner Decision (see
``.claude/review-notes/issue-5c-quarantine-retirement.md``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.bound_corpus import (
    leaves_under,
    load_bound_corpus,
)
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceRecord,
    ClassificationLedger,
    ReleaseBinding,
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedOracle,
    OracleLoadError,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import (
    PROPOSAL_SCHEMA_VERSION_2,
    proposal_identity,
    proposal_payload,
    seed_proposal,
)
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    publish_from_committed_oracle,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    RepresentationDraft,
    representation_schema_hash,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.quarantine import (
    QUARANTINED_PACKAGE_UUIDS,
    QUARANTINED_RELEASE_VERSIONS,
    QuarantinedAuthorityError,
)
from tests.ingestion.mechanical.conftest import NOW, candidate_of

#: One real section of the new corpus, used to exercise the shared tools.
#: Selected by the label the source itself prints, not by a depth or an offset
#: range — see ``leaves_under`` for why a suffix match is what keeps that honest.
#: It is a member of the Conditions family this increment proposes as the pilot,
#: which is why it is a realistic shape to exercise. It is *not* pilot authoring:
#: the seeded span is whole-leaf and ``UNRESOLVED``, carries no review unit, and
#: asserts nothing about what Blinded means. The pilot's scope is a review
#: decision that has not been made, and nothing here presumes it.
PROBE_SECTION = ("Blinded [Condition]",)

#: Another member of the same family, selected to exercise how a label is
#: qualified by its real ancestors. It reached this module for the opposite
#: reason: ``### Swim Speed`` was the glossary's sole ``h3``, so it owned
#: ``Unconscious`` and twelve other entries, and this module asserted that
#: ownership as faithful 5c structure. It was neither — official pp.189—191 print
#: Swim Speed, Target and Unconscious as peer glossary entries — and the source
#: is corrected at its own 5c layer rather than worked around here. What the
#: suffix match is for is unchanged: qualifying a printed label by the labels
#: above it, without assuming a depth.
PEER_SECTION = ("Unconscious [Condition]",)

#: The entry that used to own the run, kept as the negative: it is a peer, so
#: qualifying by it selects nothing at all.
FORMER_OWNER = ("Swim Speed",)

#: Obviously not a person. A reviewer name in a test fixture must never be
#: mistakable for evidence that someone reviewed SRD meaning.
FIXTURE_REVIEWER = "fixture-not-a-reviewer"

FIXTURE_ORIGIN = "test-seed/readiness-probe"
FIXTURE_RATIONALE = "seeded by a test; no human has read this source"

EMPTY_REPRESENTATION = RepresentationDraft(
    records=(),
    components=(),
    prose_bindings=(),
    relationships=(),
    references=(),
    provenance=(),
)

#: The replacement chain's batches, in acceptance order.
REPLACEMENT_CHAIN = (
    "conditions-pilot",
    "actions-pilot",
    "reference-closure",
    "movement-closure",
    "combat-turn-1",
    "damage-and-hit-points",
    "combat-damage-breaking",
    "checks-actions-rests",
    "core-play-completion",
    "core-play-dependencies",
    "character-creation-foundations",
    "character-origins-feats",
    "equipment",
    "spellcasting",
    "rules-glossary-completion",
    "classes",
    "class-option-catalogues",
)

OLD_PACKAGE = next(iter(QUARANTINED_PACKAGE_UUIDS))
OLD_RELEASE = next(iter(QUARANTINED_RELEASE_VERSIONS))


def _published_binding(session: Session) -> ReleaseBinding:
    """The six coordinates of the one release this store published.

    Read back from ``rp_corpus_releases`` rather than carried over from the
    in-memory build artifacts: what 5d binds to is what 5c *persisted*, and
    taking the binding from anywhere else would let a test pass while the
    published row said something different.
    """
    row = session.execute(select(CorpusReleaseORM)).scalars().one()
    assert row.persisted_corpus_digest is not None
    return ReleaseBinding(
        package_uuid=row.package_uuid,
        release_version=row.release_version,
        authoritative_source_hash=row.authoritative_source_hash,
        transform_config_hash=row.transform_config_hash,
        bundle_root_hash=row.bundle_root_hash,
        persisted_corpus_digest=row.persisted_corpus_digest,
    )


@dataclass(frozen=True)
class Readiness:
    """A live session over the published replacement release, and its binding."""

    session: Session
    binding: ReleaseBinding


@pytest.fixture(scope="module")
def readiness(source_release_db: Path):  # type: ignore[no-untyped-def]
    """A session on the file the 5c lifecycle actually published into.

    Not a re-persist: the point of this module is that 5d reads back what 5c
    published, so the state under test is the state ``finalize_source_release``
    committed. Module-scoped because nothing here publishes successfully — every
    publication attempt is refused — so no test can leave state another reads.
    """
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as session:
        yield Readiness(session=session, binding=_published_binding(session))
    engine.dispose()


def _seeded(readiness: Readiness):  # type: ignore[no-untyped-def]
    """The probe section's leaves and an unreviewed proposal over them."""
    corpus = load_bound_corpus(
        readiness.session,
        readiness.binding.package_uuid,
        readiness.binding.release_version,
    )
    leaf_ids = leaves_under(
        readiness.session,
        readiness.binding.package_uuid,
        readiness.binding.release_version,
        PROBE_SECTION,
    )
    proposal = seed_proposal(
        corpus,
        leaf_ids,
        binding=readiness.binding,
        origin=FIXTURE_ORIGIN,
        rationale=FIXTURE_RATIONALE,
    )
    return corpus, leaf_ids, proposal


# ---------------------------------------------------------------------------
# 1. Source and proposal are bound to the same release
# ---------------------------------------------------------------------------


def test_the_replacement_release_supplies_its_own_population(
    readiness: Readiness,
) -> None:
    """The binding seam works against the new release with no change.

    The totals are drift canaries, not contracts: what matters is that the
    population is read from 5c's published state rather than supplied by 5d.
    """
    corpus = load_bound_corpus(
        readiness.session,
        readiness.binding.package_uuid,
        readiness.binding.release_version,
    )
    assert corpus.package_uuid == readiness.binding.package_uuid
    assert corpus.release_version == readiness.binding.release_version
    assert len(corpus.leaf_lengths) > 10_000
    assert corpus.authoritative_chunk_ids


def test_selection_qualifies_a_label_by_the_labels_above_it(
    readiness: Readiness,
) -> None:
    """A printed label is selected, and an ancestor narrows it — nothing invents one.

    The corrected source is what makes the three reads below agree: the official
    document prints these as peer glossary entries, so qualifying by the real
    ancestor selects the same leaves and qualifying by a peer selects none. This
    is also the regression for the ownership defect — if a rank outlier ever
    captures the run again, the peer qualification stops returning nothing.
    """

    def _under(labels: tuple[str, ...]) -> tuple[str, ...]:
        return leaves_under(
            readiness.session,
            readiness.binding.package_uuid,
            readiness.binding.release_version,
            labels,
        )

    leaf_ids = _under(PEER_SECTION)
    assert leaf_ids
    # The real ancestor narrows to the same leaves rather than to a subset.
    assert _under(("Rules Definitions", *PEER_SECTION)) == leaf_ids
    # A peer is not an ancestor, so it selects nothing rather than approximating.
    assert _under((*FORMER_OWNER, *PEER_SECTION)) == ()
    # And the peer has its own leaves, disjoint from these.
    former = _under(FORMER_OWNER)
    assert former
    assert not set(former) & set(leaf_ids)


def test_a_named_section_selects_real_leaves_of_that_release(
    readiness: Readiness,
) -> None:
    """Selection resolves a printed heading to represented leaves, or nothing.

    Every selected leaf is in the snapshot's represented population, because
    both reads go through the same predicate. A label the source does not print
    selects nothing rather than approximating.
    """
    corpus, leaf_ids, _ = _seeded(readiness)
    assert leaf_ids
    assert set(leaf_ids) <= set(corpus.leaf_lengths)
    assert (
        leaves_under(
            readiness.session,
            readiness.binding.package_uuid,
            readiness.binding.release_version,
            ("No Such Heading In The SRD",),
        )
        == ()
    )


def test_a_seeded_proposal_is_bound_on_every_coordinate(
    readiness: Readiness,
) -> None:
    """All six coordinates, and spans that index the release's own leaves.

    A proposal that named only the package and version would still be
    ambiguous: two builds of one version differ in their digests, and the digest
    is what makes the acceptance that follows re-derivable.
    """
    corpus, leaf_ids, proposal = _seeded(readiness)
    assert proposal.binding == readiness.binding
    assert proposal.proposal_schema_version == PROPOSAL_SCHEMA_VERSION_2
    assert {span.span.leaf_id for span in proposal.proposed_spans} == set(leaf_ids)
    for proposed in proposal.proposed_spans:
        span = proposed.span
        assert span.review_state is ReviewState.PROPOSED
        assert span.disposition is SemanticDisposition.UNRESOLVED
        assert span.char_end == corpus.leaf_lengths[span.leaf_id]


def test_a_seed_refuses_a_binding_for_a_different_release(
    readiness: Readiness,
) -> None:
    """A proposal cannot be bound to a release it was not seeded from."""
    corpus, leaf_ids, _ = _seeded(readiness)
    elsewhere = replace(readiness.binding, release_version="5.2.1-corpus.deadbeef-000")
    with pytest.raises(ValueError, match="must be bound to the release"):
        seed_proposal(
            corpus,
            leaf_ids,
            binding=elsewhere,
            origin=FIXTURE_ORIGIN,
            rationale=FIXTURE_RATIONALE,
        )


def test_a_seed_refuses_a_leaf_the_release_does_not_represent(
    readiness: Readiness,
) -> None:
    """A span over unrepresented text has no authoritative length to index."""
    corpus, leaf_ids, _ = _seeded(readiness)
    with pytest.raises(ValueError, match="not represented"):
        seed_proposal(
            corpus,
            (*leaf_ids, "leaf-that-does-not-exist"),
            binding=readiness.binding,
            origin=FIXTURE_ORIGIN,
            rationale=FIXTURE_RATIONALE,
        )


# ---------------------------------------------------------------------------
# 2. Unreviewed is a typed status, not an exception and not an empty oracle
# ---------------------------------------------------------------------------


def test_the_replacement_release_has_only_the_two_pilot_authorities(
    readiness: Readiness,
) -> None:
    """Nothing but the Owner's recorded chain is accepted over the release.

    The published release is the Owner-corrected one (the Monsters
    correction). The Owner accepted the twenty-batch replacement chain on it
    under one approval (6450 spans, 1099 resolutions), then the Monsters batch
    and its 83 resolutions over that, then Animals and its 65 resolutions,
    then the same chain with only the Equipment proposal replaced and its 161
    cited resolutions, then with eight proposals replaced, three resolutions
    re-keyed and 29 resolved, then with the Animals proposal replaced and its
    four resolutions, then with the framing-coverage batch appended and no
    resolution, then with the Character Creation catalogue batch appended and
    its two resolutions (later recordings replaced proposals in place), then
    lifted to schema 17 with the thirteen reference-routes resolutions, then
    with the combat-damage-breaking proposal replaced (one ranged prose span
    added) and the ten finite-reference-routes resolutions, then with the
    thirteen Equipment, cursed-item and spell resolutions, then with the final
    ten reference resolutions. The Owner then accepted that chain natively
    rebound to the official-order release, recorded with fresh approvals:
    exactly those twenty-four batches, 10493 spans and 1486 resolutions
    resolve.
    """
    inputs = committed_inputs_for(
        readiness.binding.package_uuid, readiness.binding.release_version
    )
    assert inputs is not None
    assert inputs.oracle.binding == readiness.binding
    assert {b.batch_id for b in inputs.batches} == {
        *REPLACEMENT_CHAIN,
        "spell-descriptions",
        "gameplay-toolbox",
        "magic-items",
        "monsters",
        "animals",
        "framing-coverage",
        "character-creation-catalogue",
    }
    assert len(inputs.oracle.spans) == 10495  # CRD Issue 2b G1 split two shared rows
    assert len(inputs.oracle.reference_resolutions) == 1486


def test_publishing_an_unreviewed_projection_is_typed_refused(
    readiness: Readiness, unreviewed_projection: str
) -> None:
    """The publication path refuses with a typed outcome, never publishing.

    ABSENT until the Conditions pilot was accepted over this release; now the
    gate judges the draft against the accepted pilots and reports its
    UNRESOLVED spans.
    """
    result = publish_from_committed_oracle(
        readiness.session, unreviewed_projection, now=NOW
    )
    assert result.outcome is PublicationOutcome.UNRESOLVED


@pytest.fixture(scope="module")
def unreviewed_projection(readiness: Readiness) -> str:
    """One persisted draft over the probe section, every span UNRESOLVED.

    The spans carry the synthetic reviewer name and no disposition anyone has
    decided, which is what makes this a test of the machinery rather than an
    authoring action: an UNRESOLVED span states that nobody has read the source.

    Module-scoped because its identity is content-derived: the same section over
    the same release *is* the same projection, so persisting it per test would
    collide rather than isolate. Every test below refuses it, so none can leave
    state another reads.
    """
    _, leaf_ids, proposal = _seeded(readiness)
    spans = tuple(
        replace(proposed.span, review_state=ReviewState.ACCEPTED)
        for proposed in proposal.proposed_spans
    )
    classification = ClassificationLedger(
        package_uuid=readiness.binding.package_uuid,
        release_version=readiness.binding.release_version,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=spans,
        batches=(),
        acceptances=tuple(
            AcceptanceRecord(span.span_id, None, FIXTURE_REVIEWER, NOW)
            for span in spans
        ),
    )
    identified = identify_projection(
        candidate_of(
            binding=readiness.binding,
            classification=classification,
            representation=EMPTY_REPRESENTATION,
        )
    )
    persist_draft(readiness.session, identified, now=NOW)
    record_persisted_state_digest(readiness.session, identified.projection_uuid)
    return identified.projection_uuid


# ---------------------------------------------------------------------------
# 3. Old and mismatched authority are refused
# ---------------------------------------------------------------------------


def test_the_superseded_release_is_refused_by_identity(
    readiness: Readiness,
) -> None:
    """Both 5d seams refuse the quarantined product before doing any work.

    Loading it would be the fresh build silently inheriting the corpus the
    Owner Decision retired, so the refusal is loud and names the seam.
    """
    for seam in (
        lambda: load_bound_corpus(readiness.session, OLD_PACKAGE, OLD_RELEASE),
        lambda: committed_oracle_for(OLD_PACKAGE, OLD_RELEASE),
    ):
        with pytest.raises(QuarantinedAuthorityError):
            seam()


def test_authority_accepted_over_another_release_judges_nothing_here(
    readiness: Readiness, unreviewed_projection: str
) -> None:
    """The gate refuses an oracle bound to a different release.

    Synthetic rather than the committed artifact on purpose: the committed one
    is refused by quarantine before the gate sees it, so proving the *gate's*
    own release check needs an oracle that is merely wrong, not retired. The
    gate reads the bound release from the persisted header, so this cannot be
    faked by handing it a different snapshot.
    """
    elsewhere = replace(
        readiness.binding,
        release_version="5.2.1-corpus.not-this-one",
        persisted_corpus_digest="0" * 64,
    )
    foreign = AcceptedOracle(
        binding=elsewhere,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        spans=(),
        representation=EMPTY_REPRESENTATION,
        obligations=(),
    )
    result = run_publication_gate(readiness.session, unreviewed_projection, foreign)
    assert not result.passed
    assert GateFailureCategory.MISMATCHED_RELEASE in {
        failure.category for failure in result.failures
    }


# ---------------------------------------------------------------------------
# 4. A meaningful change invalidates stale reuse
# ---------------------------------------------------------------------------


def test_the_same_source_seeds_the_same_identity(readiness: Readiness) -> None:
    """Two independent seeds of one section derive one identity.

    Without this, "the reviewer read proposal X" would be unverifiable on a
    later build, and every acceptance record would be a claim about bytes
    nobody can reproduce.
    """
    _, _, first = _seeded(readiness)
    _, _, second = _seeded(readiness)
    assert proposal_identity(first) == proposal_identity(second)


def test_a_changed_disposition_derives_a_different_identity(
    readiness: Readiness,
) -> None:
    """Editing what a reviewer would read moves the identity.

    So an acceptance recorded against the old identity cannot be reused as
    evidence for the edited proposal — which is what stops a stale review from
    silently covering changed content.
    """
    _, _, proposal = _seeded(readiness)
    first, *rest = proposal.proposed_spans
    edited = replace(
        proposal,
        proposed_spans=(
            replace(
                first,
                span=replace(
                    first.span,
                    disposition=SemanticDisposition.SUBSTANTIVE,
                ),
            ),
            *rest,
        ),
    )
    assert proposal_identity(edited) != proposal_identity(proposal)


def test_a_changed_binding_derives_a_different_identity(
    readiness: Readiness,
) -> None:
    """A proposal over a rebuilt corpus is a different proposal.

    The digest is inside the identity, so the same words over a different build
    of 5c cannot inherit the earlier review.
    """
    _, _, proposal = _seeded(readiness)
    rebuilt = replace(
        proposal, binding=replace(proposal.binding, bundle_root_hash="0" * 64)
    )
    assert proposal_identity(rebuilt) != proposal_identity(proposal)


# ---------------------------------------------------------------------------
# 5. Review and acceptance are separate shapes
# ---------------------------------------------------------------------------


def test_a_proposal_cannot_be_loaded_as_accepted_authority(
    readiness: Readiness, tmp_path: Path
) -> None:
    """Refused on shape, not on a flag or a folder.

    Written to a temporary path, never to ``oracles/``: this proves the loader
    refuses the artifact, and committing one would be the very confusion the
    separation exists to prevent.
    """
    path = tmp_path / "seeded-proposal.json"
    _, _, proposal = _seeded(readiness)
    path.write_text(json.dumps(proposal_payload(proposal)), encoding="utf-8")
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(path)


def test_the_proposal_states_no_acceptance_to_edit(readiness: Readiness) -> None:
    """Even with the discriminator forged, the accepted keys are simply absent.

    ``artifact_kind`` is the legible error, not the protection: a proposal has
    no ``spans``, ``acceptance`` or ``obligations`` to lie with, and carries
    four keys the accepted loader does not declare.
    """
    _, _, proposal = _seeded(readiness)
    payload = proposal_payload(proposal)
    assert payload["artifact_kind"] == "machine_proposal"
    assert not {"spans", "acceptance", "obligations", "representation"} & set(payload)
    assert {
        "proposed_spans",
        "proposed_representation",
        "proposed_review_units",
    } <= set(payload)
    assert proposal.proposed_review_units == ()
