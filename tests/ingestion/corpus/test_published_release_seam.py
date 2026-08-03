"""One published-release seam, and every lifecycle path that must use it.

CRD Issue 5c. The defect these controls close is not a missing check but a
missing *shared* one: ``verify_published_release`` accumulated row-level
publication invariants one review round at a time while ``finalize_release``'s
verified-reuse path checked the package row's status inline and nothing else. So
a release that downstream 5d verification refused was still handed back as
``published=True, reused=True`` — two authorities on one published release.

Every control below therefore asserts the *same* tampering is refused by **both**
paths, and the parametrisation is the point: a new invariant added to the seam
is automatically demanded of reuse and of downstream consumption, and cannot be
added to one of them alone.

The seam's unit is the package/release **pair**. An earlier field-by-field audit
of ``rp_corpus_releases`` alone missed ``rp_packages.version``, because a
cross-row equality has no single row to be filed under.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

import afterworlds.ingestion.corpus.persistence as persistence
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.persistence import (
    _finalize_core,
    load_published_release,
    verify_published_release,
)
from afterworlds.persistence.orm.corpus import (
    CorpusReleaseORM,
    ReconciliationPolicyORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM

_NOW = "2026-07-23T00:00:00Z"
_LATER = "2026-07-24T00:00:00Z"

Tamper = Callable[[Session, str], None]


def release_row(session: Session, pkg: str) -> CorpusReleaseORM:
    return session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one()


def package_row(session: Session, pkg: str) -> RulesPackageORM:
    return session.execute(
        select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
    ).scalar_one()


@pytest.fixture()
def published(  # type: ignore[no-untyped-def]
    session, compact_candidate, chroma_client, retrieval_config, fake_embedding
):
    """An honestly published compact release, and the tools to re-drive it."""
    first = _finalize_core(
        session,
        compact_candidate,
        now=_NOW,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert first.published and not first.reused and first.artifacts is not None
    return first, compact_candidate, chroma_client, retrieval_config, fake_embedding


def downstream(session: Session, first) -> tuple[str, ...]:  # type: ignore[no-untyped-def]
    """What a 5d consumer sees, declaring exactly what the release recorded."""
    identity = first.artifacts.release.identity
    return verify_published_release(
        session,
        first.artifacts.release.package_uuid,
        release_version=first.artifacts.release.release_version,
        authoritative_source_hash=identity.authoritative_source_hash,
        transform_config_hash=identity.transform_config_hash,
        bundle_root_hash=identity.bundle_root_hash,
        corpus_digest=identity.persisted_corpus_digest,
    )


# ---------------------------------------------------------------------------
# The positive control: one honest release, both paths, same semantics
# ---------------------------------------------------------------------------


def test_an_honest_release_passes_the_seam_and_downstream(session, published) -> None:  # type: ignore[no-untyped-def]
    first, *_ = published
    pkg = first.artifacts.release.package_uuid

    proven, violations = load_published_release(session, pkg)
    assert violations == ()
    assert proven is not None
    assert proven.package.version == proven.release.release_version
    assert proven.report.prepublication_validation_status == "pass"

    assert downstream(session, first) == ()


def test_honest_fresh_publication_and_honest_reuse_share_these_semantics(  # type: ignore[no-untyped-def]
    session, full_candidate, chroma_client, retrieval_config, fake_embedding
) -> None:
    """Both lifecycle outcomes pass the same seam, on the complete corpus.

    The full candidate rather than the compact one because verified reuse also
    demands complete persisted page coverage, which a six-page fixture cannot
    satisfy — the compact controls below are therefore asserted on the specific
    pair refusal rather than on reuse failing for any reason at all.
    """
    first = _finalize_core(
        session,
        full_candidate,
        now=_NOW,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert first.published and not first.reused
    assert load_published_release(session, full_candidate.package_uuid)[1] == ()
    assert downstream(session, first) == ()

    second = _finalize_core(
        session,
        full_candidate,
        now=_LATER,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert second.published and second.reused
    assert load_published_release(session, full_candidate.package_uuid)[1] == ()


def test_an_honest_fresh_publication_leaves_rows_that_satisfy_the_seam(  # type: ignore[no-untyped-def]
    session, published
) -> None:
    """The committed rows prove themselves, with no later repair."""
    first, *_ = published
    assert (
        load_published_release(session, first.artifacts.release.package_uuid)[1] == ()
    )


def test_a_fresh_publication_the_seam_refuses_is_rolled_back_not_committed(  # type: ignore[no-untyped-def]
    session,
    compact_candidate,
    chroma_client,
    retrieval_config,
    fake_embedding,
    monkeypatch,
) -> None:
    """Fault injection on the *fresh* path, which no other control reaches.

    Both other callers can be driven by editing rows after publication; a fresh
    publication has to be made to write a bad pair while it runs. Here the
    package row is given a version the release does not carry — the exact
    invariant a field-by-field audit of the release row could not surface —
    after the draft rows are persisted and before the gate.

    The refusal is only half the property. The other half is that nothing was
    committed: a fresh publication the seam declines must leave no published
    package or release behind, which is why the row assertions matter more than
    the failure text.
    """
    original = persistence._persist_package_and_source

    def forge_package_version(session_, pkg, release_version, *, now):  # type: ignore[no-untyped-def]
        source_id = original(session_, pkg, release_version, now=now)
        package_row(session_, pkg).version = "forged-version"
        session_.flush()
        return source_id

    monkeypatch.setattr(
        persistence, "_persist_package_and_source", forge_package_version
    )

    result = _finalize_core(
        session,
        compact_candidate,
        now=_NOW,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert not result.published and not result.reused
    assert result.gate is not None
    assert any("refusing to publish" in f for f in result.gate.failures)
    assert any("is not the release's" in f for f in result.gate.failures)

    pkg = compact_candidate.package_uuid
    assert (
        session.execute(
            select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
        ).scalar_one_or_none()
        is None
    )
    assert (
        session.execute(
            select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
        ).scalar_one_or_none()
        is None
    )


# ---------------------------------------------------------------------------
# Every row-level invariant, refused by both paths
# ---------------------------------------------------------------------------


def _coordinated_transform_edit(session: Session, pkg: str) -> None:
    """Edit the stored transform configuration and keep everything agreeing.

    Nothing else moves: the recorded ``transform_config_hash``, the report, and
    the package identity are all untouched and mutually consistent. Only
    recomputing the configuration's own hash catches it.
    """
    release = release_row(session, pkg)
    config = dict(release.transform_config)
    config["evidence_report_schema_version"] = "forged"
    release.transform_config = config


def _stale_report_reference(session: Session, pkg: str) -> None:
    """The reference names a real report — the one before this one."""
    release = release_row(session, pkg)
    payload = dict(release.report_payload or {})
    stale = release.evidence_report_hash
    payload["declared_projection_count"] = 99
    release.report_payload = payload
    release.evidence_report_hash = hash_obj(payload)
    release.corpus_report_reference = stale


TAMPERS: list[tuple[str, Tamper]] = [
    (
        "package-published_at-cleared",
        lambda s, p: setattr(package_row(s, p), "published_at", None),
    ),
    (
        "package-not-published",
        lambda s, p: setattr(package_row(s, p), "publication_status", "draft"),
    ),
    (
        "package-disabled",
        lambda s, p: setattr(package_row(s, p), "is_enabled", False),
    ),
    (
        "package-version-edited-away-from-the-release",
        lambda s, p: setattr(package_row(s, p), "version", "forged-version"),
    ),
    (
        "release-not-published",
        lambda s, p: setattr(release_row(s, p), "publication_status", "draft"),
    ),
    (
        "transform-config-does-not-hash-to-its-recorded-hash",
        _coordinated_transform_edit,
    ),
    (
        "report-payload-cleared",
        lambda s, p: setattr(release_row(s, p), "report_payload", None),
    ),
    (
        "evidence-report-hash-cleared",
        lambda s, p: setattr(release_row(s, p), "evidence_report_hash", None),
    ),
    (
        "persisted-corpus-digest-cleared",
        lambda s, p: setattr(release_row(s, p), "persisted_corpus_digest", None),
    ),
    (
        "report-reference-cleared",
        lambda s, p: setattr(release_row(s, p), "corpus_report_reference", None),
    ),
    (
        "report-reference-names-an-unrelated-report",
        lambda s, p: setattr(release_row(s, p), "corpus_report_reference", "9" * 64),
    ),
    ("report-reference-names-the-previous-report", _stale_report_reference),
    (
        "report-does-not-hash-to-its-recorded-hash",
        lambda s, p: setattr(
            release_row(s, p),
            "report_payload",
            {**(release_row(s, p).report_payload or {}), "invalid_locators": 7},
        ),
    ),
    (
        "report-identity-disagrees-with-its-release-column",
        lambda s, p: _rehashed(s, p, bundle_root_hash="9" * 64),
    ),
    (
        "report-records-a-failed-verdict",
        lambda s, p: _rehashed(s, p, prepublication_validation_status="fail"),
    ),
    (
        "report-claims-pass-over-unresolved-leaves",
        lambda s, p: _rehashed(s, p, unresolved_leaves=3),
    ),
]


def _rehashed(session: Session, pkg: str, **overrides: object) -> None:
    """Edit the recorded report *and* rehash it, so identity alone accepts it."""
    release = release_row(session, pkg)
    payload = dict(release.report_payload or {})
    payload.update(overrides)
    release.report_payload = payload
    release.evidence_report_hash = hash_obj(payload)
    release.corpus_report_reference = release.evidence_report_hash


@pytest.mark.parametrize("tamper", [pytest.param(t, id=label) for label, t in TAMPERS])
def test_a_refused_release_is_refused_by_downstream_consumption_and_by_reuse(
    session,  # type: ignore[no-untyped-def]
    published,  # type: ignore[no-untyped-def]
    tamper: Tamper,
) -> None:
    """One tampering, both paths — the property a per-caller check cannot give.

    The reuse half is the finding this module exists for: before the seam, a
    release rejected here was still returned as ``published=True, reused=True``.
    """
    first, candidate, chroma_client, retrieval_config, fake_embedding = published
    pkg = first.artifacts.release.package_uuid

    tamper(session, pkg)
    session.commit()

    assert load_published_release(session, pkg)[0] is None
    assert downstream(session, first) != ()

    second = _finalize_core(
        session,
        candidate,
        now=_LATER,
        chroma_client=chroma_client,
        retrieval_config=retrieval_config,
        embedding_function=fake_embedding,
    )
    assert not second.published
    assert not second.reused
    assert second.gate is not None
    # Asserted on the *pair* refusal specifically, not merely on reuse failing:
    # the compact fixture cannot satisfy full page coverage either, so "reuse
    # returned False" alone would be true no matter what this control did. A
    # release row edited out of ``published`` never reaches the reuse branch —
    # the older non-published-row guard refuses to touch it at all, which is the
    # same fail-closed answer one step earlier.
    assert any(
        "refusing to reuse" in f or "refusing to mutate" in f
        for f in second.gate.failures
    )


def test_the_seam_returns_the_pair_it_proved(session, published) -> None:  # type: ignore[no-untyped-def]
    """Callers get the proven rows, so nothing re-reads them unproven."""
    first, *_ = published
    pkg = first.artifacts.release.package_uuid
    proven, _ = load_published_release(session, pkg)
    assert proven is not None
    assert proven.release.package_uuid == pkg
    assert proven.package.rules_package_id == pkg
    assert proven.report.dump() == release_row(session, pkg).report_payload


def test_a_proven_pair_that_no_longer_reconstructs_is_still_refused_downstream(  # type: ignore[no-untyped-def]
    session, published
) -> None:
    """The seam and reconstruction own different halves, and both must hold.

    Deleting the frozen policy row leaves the pair perfectly self-consistent —
    every column, hash, and recorded identity still agrees — so the seam passes
    it. What fails is the half the seam deliberately does not restate:
    reconstruction from the persisted rows.
    """
    first, *_ = published
    pkg = first.artifacts.release.package_uuid
    session.execute(
        delete(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == pkg
        )
    )
    session.flush()

    assert load_published_release(session, pkg)[1] == ()
    violations = downstream(session, first)
    assert any("does not reconstruct from persisted rows" in v for v in violations)


def test_an_absent_release_is_refused_without_deriving_further_findings(
    session,  # type: ignore[no-untyped-def]
) -> None:
    """A missing pair yields the real finding, not a cascade derived from it."""
    proven, violations = load_published_release(session, "no-such-package")
    assert proven is None
    assert len(violations) == 2
    assert any("rp_corpus_releases" in v for v in violations)
    assert any("rp_packages" in v for v in violations)
