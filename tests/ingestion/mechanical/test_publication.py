"""Atomic publication and activation — CRD Issue 5d, Decision 8.

The four contract properties, each proven by observing the database rather than
the return value alone: a failed gate leaves no partial active state, published
projections stop verifying once edited, an identical rebuild is idempotent, and
a competing projection cannot take a package's active authority.

Publication commits, so every test here gets its own database.
"""

from __future__ import annotations

import dataclasses
import inspect
import shutil
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.report import (
    CANONICAL_CANARY_NAMES,
    recorded_success_violations,
)
from afterworlds.ingestion.mechanical import publication
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedOracle,
    committed_oracle_for,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _activate_projection,
    _publish_projection,
    publish_from_committed_oracle,
    resolve_active_projection,
)
from afterworlds.ingestion.mechanical.report import EvidenceReport, report_hash
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    fact_key,
)
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalActiveProjectionORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
)
from afterworlds.persistence.orm.rules_package import RuleChunkORM, RulesPackageORM
from tests.ingestion.mechanical.conftest import (
    BOUND_REPORT,
    BOUNDED_ORACLE_PATH,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    NOW,
    PACKAGE_UUID,
    SPELL_KEY,
    build_candidate,
    build_ledger,
    build_representation,
)
from tests.ingestion.mechanical.test_gate import persist

LATER = "2026-08-01T00:00:00Z"


def header(session: Session, uuid: str) -> MechanicalProjectionORM:
    return session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()


def active_rows(session: Session) -> list[MechanicalActiveProjectionORM]:
    return list(session.execute(select(MechanicalActiveProjectionORM)).scalars().all())


def a_different_projection(
    session: Session, oracle: AcceptedOracle
) -> tuple[str, AcceptedOracle]:
    """A second projection over the same package, and the oracle that accepts it.

    Its spell descriptor states a different level, so it is a different
    projection identity — a genuinely *competing* authority rather than a
    rebuild. It comes with its own accepted oracle because that is the only way
    a second projection can pass the gate at all: the gate derives the expected
    identity from the oracle, so one oracle can bless exactly one projection.

    That is what makes the competing-activation branch reachable. Two committed
    oracles for one release are rejected at load, but publication takes the
    oracle it is given, and "someone published against a second accepted
    authority" is precisely the split the active-projection key exists to stop.
    """
    changed = dataclasses.replace(DESCRIPTOR_FACT, level=8)
    base = build_representation()
    representation = dataclasses.replace(
        base,
        components=(
            dataclasses.replace(base.components[0], facts=(changed,)),
            base.components[1],
        ),
        provenance=tuple(
            (
                dataclasses.replace(
                    p, target_key=(SPELL_KEY, DESCRIPTOR_KEY, fact_key(changed))
                )
                if p.target_kind is ProvenanceTargetKind.FACT
                else p
            )
            for p in base.provenance
        ),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=representation)
    )
    return uuid, dataclasses.replace(oracle, representation=representation)


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------


def test_a_complete_projection_publishes_and_becomes_active(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    result = _publish_projection(session, uuid, committed_oracle, now=NOW)

    assert result.outcome is PublicationOutcome.PUBLISHED
    assert result.report is not None
    assert result.evidence_report_hash == report_hash(result.report)

    row = header(session, uuid)
    assert row.publication_status == "published"
    assert row.published_at == NOW
    assert row.oracle_identity == oracle_identity(committed_oracle)
    assert row.evidence_report_hash == result.evidence_report_hash
    assert row.report_payload == result.report.payload

    active = resolve_active_projection(session, PACKAGE_UUID)
    assert active.outcome is PublicationOutcome.PUBLISHED
    assert active.projection_uuid == uuid
    assert active.activated_at == NOW


def test_publication_survives_a_new_session(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Publication commits, so it is durable rather than pending in a session."""
    uuid = persist(session)
    assert (
        _publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )
    session.expunge_all()
    assert resolve_active_projection(session, PACKAGE_UUID).projection_uuid == uuid


# ---------------------------------------------------------------------------
# A failed gate leaves nothing behind
# ---------------------------------------------------------------------------


def test_a_failed_gate_leaves_no_partial_active_state(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    ledger = build_ledger()
    unaccepted = dataclasses.replace(ledger, acceptances=())
    uuid = persist(
        session, dataclasses.replace(build_candidate(), classification=unaccepted)
    )

    result = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.outcome is PublicationOutcome.UNREVIEWED

    row = header(session, uuid)
    assert row.publication_status == "draft"
    assert row.published_at is None
    assert row.evidence_report_hash is None
    assert row.report_payload is None
    assert active_rows(session) == []
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.UNPUBLISHED
    )


def test_a_failed_gate_still_produces_an_auditable_report(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The refusal is returned as evidence, and is not written anywhere."""
    uuid = persist(session)
    session.execute(
        MechanicalFactORM.__table__.delete().where(
            MechanicalFactORM.projection_uuid == uuid
        )
    )
    session.flush()
    result = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.report is not None
    gate = result.report.payload["gate"]
    assert isinstance(gate, dict)
    assert gate["passed"] is False
    assert gate["failures"]
    assert header(session, uuid).report_payload is None


def test_activation_after_a_failed_gate_is_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Activation is fail-closed on its own, not because publication behaved.

    Called directly, with nothing between it and the database — the state a
    caller who skipped the gate, or ran it and ignored the answer, would be in.
    """
    uuid = persist(session)
    session.execute(
        MechanicalFactORM.__table__.delete().where(
            MechanicalFactORM.projection_uuid == uuid
        )
    )
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is not PublicationOutcome.PUBLISHED
    )

    direct = _activate_projection(session, uuid, now=NOW)
    assert direct.outcome is PublicationOutcome.UNPUBLISHED
    assert active_rows(session) == []


def test_activation_of_an_unknown_projection_is_absent(session: Session) -> None:
    assert (
        _activate_projection(session, "no-such-projection", now=NOW).outcome
        is PublicationOutcome.ABSENT
    )


# ---------------------------------------------------------------------------
# Idempotence and immutability
# ---------------------------------------------------------------------------


def test_publishing_the_same_projection_twice_is_idempotent(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """An identical rebuild is the same content-derived identity.

    The second attempt still runs the complete gate — reuse is never accepted
    on a status check alone — and leaves the activation record byte-identical.
    """
    uuid = persist(session)
    first = _publish_projection(session, uuid, committed_oracle, now=NOW)
    before = (
        active_rows(session)[0].projection_uuid,
        active_rows(session)[0].activated_at,
    )

    second = _publish_projection(session, uuid, committed_oracle, now=LATER)
    assert second.outcome is PublicationOutcome.ALREADY_PUBLISHED
    assert second.gate is not None and second.gate.passed
    assert second.evidence_report_hash == first.evidence_report_hash

    assert len(active_rows(session)) == 1
    assert (
        active_rows(session)[0].projection_uuid,
        active_rows(session)[0].activated_at,
    ) == before
    assert header(session, uuid).published_at == NOW


def test_a_published_projection_edited_afterwards_stops_verifying(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Published projections are immutable: an edit is detected, not absorbed."""
    uuid = persist(session)
    assert (
        _publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )

    row = session.execute(select(MechanicalFactORM)).scalars().one()
    payload = dict(row.payload)
    payload["level"] = 1
    row.payload = payload
    session.flush()

    again = _publish_projection(session, uuid, committed_oracle, now=LATER)
    assert again.outcome is PublicationOutcome.STALE


def test_a_published_projection_whose_evidence_was_rewritten_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Recorded evidence must still be the evidence this state derives."""
    uuid = persist(session)
    _publish_projection(session, uuid, committed_oracle, now=NOW)
    header(session, uuid).evidence_report_hash = "e" * 64
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


# ---------------------------------------------------------------------------
# Competing activation
# ---------------------------------------------------------------------------


def test_a_competing_projection_that_passes_its_own_gate_is_still_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The challenger passes a gate — against its own accepted oracle.

    This is the case that actually needs the active-projection key. The
    challenger is internally honest, proven, and blessed by an oracle that
    derives its exact identity, so nothing about *it* is wrong. It is refused
    solely because the package already has active authority, and it is refused
    before its own header is mutated, so it stays a draft rather than becoming
    a second published-but-inactive projection.
    """
    incumbent = persist(session)
    assert (
        _publish_projection(session, incumbent, committed_oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )

    challenger, challenger_oracle = a_different_projection(session, committed_oracle)
    assert challenger != incumbent
    assert run_publication_gate(session, challenger, challenger_oracle).passed

    result = _publish_projection(session, challenger, challenger_oracle, now=LATER)
    assert result.outcome is PublicationOutcome.ACTIVE_CONFLICT

    assert header(session, challenger).publication_status == "draft"
    assert header(session, challenger).evidence_report_hash is None
    assert len(active_rows(session)) == 1
    assert active_rows(session)[0].projection_uuid == incumbent
    assert active_rows(session)[0].activated_at == NOW


def test_a_competing_projection_judged_by_the_incumbents_oracle_is_incomplete(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """One oracle blesses exactly one projection.

    Judged by the authority that accepted the incumbent, the challenger is not
    the accepted content and never reaches the activation check at all.
    """
    incumbent = persist(session)
    _publish_projection(session, incumbent, committed_oracle, now=NOW)

    challenger, _ = a_different_projection(session, committed_oracle)
    result = _publish_projection(session, challenger, committed_oracle, now=LATER)
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert active_rows(session)[0].projection_uuid == incumbent


def test_activating_a_second_published_projection_is_an_active_conflict(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The activation seam itself refuses to split, whatever the caller did.

    The challenger is forced into a ``published`` header with recorded evidence
    — the state a bug, a partial migration, or a hand edit could produce — and
    activation still refuses, because one active projection per package is a
    primary key rather than a convention.
    """
    incumbent = persist(session)
    _publish_projection(session, incumbent, committed_oracle, now=NOW)

    challenger, _ = a_different_projection(session, committed_oracle)
    forced = header(session, challenger)
    forced.publication_status = "published"
    forced.evidence_report_hash = "f" * 64
    session.flush()

    result = _activate_projection(session, challenger, now=LATER)
    assert result.outcome is PublicationOutcome.ACTIVE_CONFLICT
    assert len(active_rows(session)) == 1
    assert active_rows(session)[0].projection_uuid == incumbent
    assert active_rows(session)[0].activated_at == NOW


# ---------------------------------------------------------------------------
# Typed outcomes, never None
# ---------------------------------------------------------------------------


def test_no_accepted_oracle_is_absent_not_a_pass(session: Session) -> None:
    """An absent oracle is never an empty one: nothing is published by default."""
    uuid = persist(session)
    result = _publish_projection(session, uuid, None, now=NOW)
    assert result.outcome is PublicationOutcome.ABSENT
    assert result.gate is None
    assert active_rows(session) == []


def test_the_committed_oracle_path_refuses_a_release_with_no_authority(
    session: Session,
) -> None:
    """The production entry resolves its own oracle and fails closed.

    Nothing is committed for this release, so the projection cannot be
    published — no caller can supply the authority that judges its own output.
    """
    uuid = persist(session)
    result = publish_from_committed_oracle(session, uuid, now=NOW)
    assert result.outcome is PublicationOutcome.ABSENT
    assert active_rows(session) == []


def test_publishing_an_unknown_projection_is_absent(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    result = _publish_projection(
        session, "no-such-projection", committed_oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.ABSENT


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            lambda c: dataclasses.replace(
                c, binding=dataclasses.replace(c.binding, bundle_root_hash="9" * 64)
            ),
            # Not "mismatched release": the declared binding names no published
            # 5c release at all, which is a statement about the record rather
            # than about which authority judges it.
            PublicationOutcome.STALE,
            id="binding-names-no-published-release",
        ),
        pytest.param(
            lambda c: dataclasses.replace(
                c,
                classification=dataclasses.replace(c.classification, acceptances=()),
            ),
            PublicationOutcome.UNREVIEWED,
            id="unreviewed-residue",
        ),
    ],
)
def test_each_refusal_has_its_own_typed_outcome(
    session: Session,
    committed_oracle: AcceptedOracle,
    mutate,  # type: ignore[no-untyped-def]
    expected: PublicationOutcome,
) -> None:
    """Refusals stay distinguishable rather than collapsing into one failure."""
    uuid = persist(session, mutate(build_candidate()))
    assert (
        _publish_projection(session, uuid, committed_oracle, now=NOW).outcome
        is expected
    )


def test_an_oracle_over_another_release_is_a_mismatched_release(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A well-bound projection judged by authority accepted elsewhere.

    Distinct from a binding that names no published release: here the record is
    sound and the *authority* is wrong, so the outcome must say so.
    """
    uuid = persist(session)
    elsewhere = dataclasses.replace(
        committed_oracle,
        binding=dataclasses.replace(
            committed_oracle.binding, release_version="rel-other"
        ),
    )
    assert (
        _publish_projection(session, uuid, elsewhere, now=NOW).outcome
        is PublicationOutcome.MISMATCHED_RELEASE
    )


def test_an_undrafted_projection_is_never_activated(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A draft with no recorded proof cannot reach publication at all."""
    identified = identify_projection(build_candidate())
    persist_draft(session, identified, now=NOW)
    result = _publish_projection(
        session, identified.projection_uuid, committed_oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.STALE
    assert active_rows(session) == []


def test_a_projection_in_an_unknown_status_is_refused(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Status no publication path produces is rejected, not interpreted."""
    uuid = persist(session)
    header(session, uuid).publication_status = "retired"
    session.flush()
    result = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.outcome is PublicationOutcome.STALE
    assert active_rows(session) == []


def test_record_digest_is_not_re_recorded_on_the_reuse_path(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Publishing twice must not try to record a proof that already exists."""
    uuid = persist(session)
    digest = header(session, uuid).persisted_state_digest
    _publish_projection(session, uuid, committed_oracle, now=NOW)
    _publish_projection(session, uuid, committed_oracle, now=LATER)
    assert header(session, uuid).persisted_state_digest == digest


def test_publication_leaves_the_projection_content_untouched(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Activation is package state, so it never changes a projection's proof."""
    uuid = persist(session)
    before = header(session, uuid).persisted_state_digest
    payload_hash = header(session, uuid).payload_hash
    _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert header(session, uuid).persisted_state_digest == before
    assert header(session, uuid).payload_hash == payload_hash


# ---------------------------------------------------------------------------
# The supported surface
# ---------------------------------------------------------------------------


def test_no_exported_publication_function_accepts_caller_authority() -> None:
    """The bypass is closed at the surface, not only on the paths tests take.

    Asserted over the module's public names rather than by calling one of them,
    because the defect this forecloses is *re-exporting*: a later change that
    made the gated path optional again would pass every behavioural test here
    and still hand a caller the authority that judges its own output.
    """
    exported = {
        name: getattr(publication, name)
        for name in publication.__all__
        if inspect.isfunction(getattr(publication, name))
    }
    assert exported, "nothing exported: the assertion below would be vacuous"
    for name, function in exported.items():
        supplied = set(inspect.signature(function).parameters)
        assert {"oracle", "directory"}.isdisjoint(supplied), name

    # The resolver is the sibling: an exported helper that accepts a directory
    # is the same bypass one step earlier.
    assert "directory" not in inspect.signature(committed_oracle_for).parameters
    assert not hasattr(publication, "publish_projection")
    assert not hasattr(publication, "activate_projection")


def test_the_production_entry_takes_no_oracle_directory(
    session: Session, tmp_path: Path
) -> None:
    """A writable directory holding a self-authored oracle cannot be pointed at.

    The oracle for this fixture release exists on disk and loads, so the only
    thing between it and a successful publication is that the production entry
    has no way to be told where to look.
    """
    shutil.copyfile(BOUNDED_ORACLE_PATH, tmp_path / "self-authored.json")
    uuid = persist(session)
    with pytest.raises(TypeError):
        publish_from_committed_oracle(  # type: ignore[call-arg]
            session, uuid, now=NOW, directory=tmp_path
        )
    assert (
        publish_from_committed_oracle(session, uuid, now=NOW).outcome
        is PublicationOutcome.ABSENT
    )
    assert active_rows(session) == []


# ---------------------------------------------------------------------------
# The bound 5c release must be an exactly-published, reconstructable release
# ---------------------------------------------------------------------------


def release_row(session: Session) -> CorpusReleaseORM:
    return session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == PACKAGE_UUID)
    ).scalar_one()


def package_row(session: Session) -> RulesPackageORM:
    return session.execute(
        select(RulesPackageORM).where(RulesPackageORM.rules_package_id == PACKAGE_UUID)
    ).scalar_one()


def a_chunk(session: Session) -> RuleChunkORM:
    return session.execute(select(RuleChunkORM)).scalars().first()  # type: ignore[return-value]


def _rewrite_release_report(session: Session, **overrides: object) -> None:
    """Edit the 5c release's recorded report *and* rehash it.

    Deliberately consistent: the payload still hashes to the recorded hash and
    every one of the five proof identities is untouched, so identity checking
    alone accepts it. Only the recorded verdict has changed.
    """
    release = release_row(session)
    payload = dict(release.report_payload or {})
    payload.update(overrides)
    release.report_payload = payload
    # Hashed as stored, exactly as the verifier rehashes it — the payload is
    # deliberately no longer parseable in some of these cases, so it cannot be
    # round-tripped through the canonical model first.
    release.evidence_report_hash = hash_obj(payload)
    release.corpus_report_reference = release.evidence_report_hash


def test_the_bounded_release_report_is_a_successful_5c_verdict() -> None:
    """The fixture's report is a real ``build_report`` output, and it passes.

    Its stored form re-parses through the canonical model, so the fixture
    exercises the same construct → dump → persist → parse path production does.
    """
    assert recorded_success_violations(BOUND_REPORT.dump()) == ()


def test_a_fabricated_binding_both_sides_agree_on_still_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The exact defect: two claims agreeing is not authority.

    The projection and the oracle carry the *same* six-value binding, so every
    comparison the gate makes between them succeeds and the oracle derives this
    projection's identity. It is refused because no published 5c release
    records that binding.
    """
    forged = dataclasses.replace(
        build_candidate().binding, persisted_corpus_digest="9" * 64
    )
    uuid = persist(session, dataclasses.replace(build_candidate(), binding=forged))
    agreeing = dataclasses.replace(committed_oracle, binding=forged)

    result = _publish_projection(session, uuid, agreeing, now=NOW)
    assert result.outcome is PublicationOutcome.STALE
    assert result.gate is not None
    assert result.gate.categories() == {GateFailureCategory.BOUND_RELEASE}
    assert active_rows(session) == []


@pytest.mark.parametrize(
    "tamper",
    [
        pytest.param(
            lambda s: setattr(release_row(s), "publication_status", "draft"),
            id="release-still-draft",
        ),
        pytest.param(
            lambda s: setattr(package_row(s), "publication_status", "draft"),
            id="package-not-published",
        ),
        pytest.param(
            lambda s: setattr(package_row(s), "is_enabled", False),
            id="package-disabled",
        ),
        pytest.param(
            lambda s: setattr(release_row(s), "report_payload", None),
            id="release-evidence-cleared",
        ),
        pytest.param(
            lambda s: setattr(release_row(s), "ledger_hash", "9" * 64),
            id="recorded-ledger-proof-does-not-reconstruct",
        ),
        pytest.param(
            lambda s: setattr(a_chunk(s), "content", a_chunk(s).content + "!"),
            id="release-content-edited-under-its-recorded-proof",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(
                s, prepublication_validation_status="fail"
            ),
            id="release-evidence-records-a-failed-verdict",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(s, unresolved_leaves=3),
            id="release-evidence-claims-pass-over-unresolved-leaves",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(
                s,
                findings={"gaps": 2, "overlaps": 0, "orphans": 0, "duplications": 0},
            ),
            id="release-evidence-claims-pass-over-coverage-gaps",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(s, concordance_failures=1),
            id="release-evidence-claims-pass-over-concordance-failures",
        ),
        # Closed-inventory population: an entry-by-entry check passes on all of
        # these, because every entry that *is* present is valid.
        pytest.param(
            lambda s: _rewrite_release_report(s, version_canaries={}),
            id="release-evidence-records-no-version-canaries",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(s, version_canaries={"invented": True}),
            id="release-evidence-records-only-an-invented-canary",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(
                s,
                version_canaries=dict.fromkeys(
                    sorted(CANONICAL_CANARY_NAMES)[1:], True
                ),
            ),
            id="release-evidence-omits-one-canonical-canary",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(
                s,
                version_canaries={
                    **dict.fromkeys(sorted(CANONICAL_CANARY_NAMES), True),
                    "invented": True,
                },
            ),
            id="release-evidence-adds-an-invented-canary",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(s, findings={"gaps": 0, "overlaps": 0}),
            id="release-evidence-findings-population-incomplete",
        ),
        pytest.param(
            lambda s: _rewrite_release_report(s, smuggled_field="value"),
            id="release-evidence-carries-an-unknown-top-level-key",
        ),
    ],
)
def test_an_unpublishable_5c_release_fails_even_when_everything_agrees(
    session: Session,
    committed_oracle: AcceptedOracle,
    tamper,  # type: ignore[no-untyped-def]
) -> None:
    """A projection that would otherwise publish, over a release that must not.

    Each control leaves the projection and the oracle untouched and exactly
    right, so the only thing refusing publication is the release itself.
    """
    uuid = persist(session)
    tamper(session)
    session.flush()
    result = _publish_projection(session, uuid, committed_oracle, now=NOW)
    assert result.outcome is PublicationOutcome.STALE
    assert result.gate is not None
    assert result.gate.categories() == {GateFailureCategory.BOUND_RELEASE}
    assert active_rows(session) == []


# ---------------------------------------------------------------------------
# Recorded evidence is verified before an already-published projection is reused
# ---------------------------------------------------------------------------


def published(session: Session, oracle: AcceptedOracle) -> str:
    uuid = persist(session)
    assert (
        _publish_projection(session, uuid, oracle, now=NOW).outcome
        is PublicationOutcome.PUBLISHED
    )
    return uuid


def test_reuse_with_a_cleared_evidence_payload_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The recorded evidence stopped being reconstructable from the database."""
    uuid = published(session, committed_oracle)
    header(session, uuid).report_payload = None
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


def test_reuse_with_an_edited_payload_under_an_unchanged_hash_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The hash column identifies a payload; it is not a substitute for it."""
    uuid = published(session, committed_oracle)
    row = header(session, uuid)
    edited = dict(row.report_payload or {})
    edited["drift_diagnostics"] = {"records": 999}
    row.report_payload = edited
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


def test_reuse_with_a_payload_and_hash_edited_together_is_still_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Internal consistency is not the test; deriving the same report is.

    Editing both columns so they agree defeats a rehash-only check. It does not
    defeat comparing the persisted payload with the report this reconstructed
    state and this committed oracle actually derive.
    """
    uuid = published(session, committed_oracle)
    row = header(session, uuid)
    edited = dict(row.report_payload or {})
    edited["drift_diagnostics"] = {"records": 999}
    row.report_payload = edited
    row.evidence_report_hash = report_hash(EvidenceReport(payload=edited))
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


def test_reuse_under_a_different_judging_oracle_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Which authority passed this projection is part of the evidence."""
    uuid = published(session, committed_oracle)
    header(session, uuid).oracle_identity = "f" * 64
    session.flush()
    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )


def test_a_hand_marked_published_header_cannot_become_active(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A status column and a non-NULL hash are not publication evidence.

    The state a partial migration or a direct row edit leaves behind: the
    header claims to be published, and there is no incumbent to collide with.
    Publication is the only door, and it refuses.
    """
    uuid = persist(session)
    row = header(session, uuid)
    row.publication_status = "published"
    row.evidence_report_hash = "e" * 64
    row.published_at = NOW
    session.flush()

    assert (
        _publish_projection(session, uuid, committed_oracle, now=LATER).outcome
        is PublicationOutcome.STALE
    )
    assert active_rows(session) == []
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.UNPUBLISHED
    )


@pytest.mark.parametrize(
    "clear",
    [
        pytest.param("evidence_report_hash", id="hash-cleared"),
        pytest.param("oracle_identity", id="judging-oracle-cleared"),
        pytest.param("published_at", id="published_at-cleared"),
        pytest.param("persisted_state_digest", id="persisted-state-proof-cleared"),
    ],
)
def test_a_missing_publication_evidence_field_makes_active_authority_stale(
    session: Session, committed_oracle: AcceptedOracle, clear: str
) -> None:
    """Publication evidence exists as a set; a partial one proves nothing.

    The state a partial migration or an interrupted write leaves behind — some
    columns populated, one NULL — which reads as published to anything that
    checks a status and one hash.
    """
    uuid = published(session, committed_oracle)
    setattr(header(session, uuid), clear, None)
    session.flush()
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.STALE
    )


def test_an_obsolete_evidence_schema_makes_active_authority_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A payload from a superseded report shape is not this schema's evidence."""
    uuid = published(session, committed_oracle)
    row = header(session, uuid)
    superseded = dict(row.report_payload or {})
    superseded["report_version"] = "5d-mechanical-evidence-0"
    row.report_payload = superseded
    row.evidence_report_hash = report_hash(EvidenceReport(payload=superseded))
    session.flush()
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.STALE
    )


def test_the_production_entry_is_absent_for_an_unknown_projection(
    session: Session,
) -> None:
    """It resolves the oracle from the header, so no header is no authority."""
    assert (
        publish_from_committed_oracle(session, "no-such-projection", now=NOW).outcome
        is PublicationOutcome.ABSENT
    )


def test_a_forged_activation_row_is_not_reported_as_valid_authority(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """An activation row is a pointer, not a claim that its target is proven."""
    uuid = persist(session)
    session.add(
        MechanicalActiveProjectionORM(
            package_uuid=PACKAGE_UUID, projection_uuid=uuid, activated_at=NOW
        )
    )
    session.flush()
    resolved = resolve_active_projection(session, PACKAGE_UUID)
    assert resolved.outcome is PublicationOutcome.STALE
    assert resolved.projection_uuid == uuid


def test_an_active_projection_whose_evidence_was_cleared_is_stale(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Resolution asserts recorded-evidence closure, not just row presence."""
    uuid = published(session, committed_oracle)
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.PUBLISHED
    )
    header(session, uuid).report_payload = None
    session.flush()
    assert (
        resolve_active_projection(session, PACKAGE_UUID).outcome
        is PublicationOutcome.STALE
    )
