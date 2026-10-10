"""The quarantined 5c/5d products cannot reenter as active authority.

Recorded Owner Decision 2026-09-21. These are seam tests, not unit tests of a
helper: each one calls a *production entry point* with the quarantined identity
and asserts the typed refusal. Most of them pass ``None`` where a session,
Chroma client or config would go, which is deliberate evidence rather than
laziness — a refusal that happens before any store handle is touched cannot have
read, written, or reset shared state. The two seams that must consult the
database first use their own in-memory SQLite engine.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

import afterworlds.persistence.orm.rules_package  # noqa: F401
from afterworlds.ingestion.corpus import (
    gate,
    operational,
    persistence,
    vector_publication,
)
from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
)
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256
from afterworlds.ingestion.ingestion_service import IngestionService
from afterworlds.ingestion.mechanical import bound_corpus, oracle, publication
from afterworlds.models.enums import RuleSubsystemEnum
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.models.rules_package import IngestionConfig, RuleSliceRequest
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageManifestORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.rules_corpus_service import RulesCorpusService
from afterworlds.quarantine import (
    QUARANTINED_ARTIFACT_FILENAMES,
    QUARANTINED_PACKAGE_UUIDS,
    QUARANTINED_PROJECTION_UUIDS,
    QUARANTINED_RELEASE_VERSIONS,
    QUARANTINED_TRANSFORM_SOURCE_HASHES,
    QuarantinedAuthorityError,
    quarantined_identities,
    refuse_quarantined,
)
from afterworlds.services.rules_authority.binding import resolve_package_reference
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_package import (
    RuleSliceResolutionError,
    RulesPackageService,
)

PKG = next(iter(QUARANTINED_PACKAGE_UUIDS))
REL = next(iter(QUARANTINED_RELEASE_VERSIONS))
PROJ = next(iter(QUARANTINED_PROJECTION_UUIDS))
RECIPE = next(iter(QUARANTINED_TRANSFORM_SOURCE_HASHES))
OTHER_PKG = "11111111-2222-5333-8444-555555555555"
OTHER_REL = "5.2.1-corpus.deadbeef-000"
REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# The refusal itself
# ---------------------------------------------------------------------------


def test_unrelated_identities_are_not_quarantined() -> None:
    """A custom Rules Package and a synthetic release are untouched."""
    assert quarantined_identities(package_uuid=OTHER_PKG) == ()
    assert quarantined_identities(release_version=OTHER_REL) == ()
    assert quarantined_identities(projection_uuid=OTHER_PKG) == ()
    assert quarantined_identities() == ()
    refuse_quarantined("unrelated", package_uuid=OTHER_PKG, release_version=OTHER_REL)


@pytest.mark.parametrize(
    ("field", "value"),
    [("package_uuid", PKG), ("release_version", REL), ("projection_uuid", PROJ)],
)
def test_each_quarantined_identity_matches(field: str, value: str) -> None:
    assert quarantined_identities(**{field: value}) == (f"{field}={value}",)


def test_every_component_of_one_product_is_reported() -> None:
    assert quarantined_identities(
        package_uuid=PKG, release_version=REL, projection_uuid=PROJ
    ) == (
        f"package_uuid={PKG}",
        f"release_version={REL}",
        f"projection_uuid={PROJ}",
    )


def test_uuid_objects_and_casing_and_padding_all_resolve() -> None:
    """The seams hand over ``UUID`` objects as often as strings."""
    assert quarantined_identities(package_uuid=UUID(PKG)) == (f"package_uuid={PKG}",)
    assert quarantined_identities(package_uuid=f"  {PKG.upper()}  ") == (
        f"package_uuid={PKG}",
    )


def test_a_str_subclass_cannot_supply_its_own_normalization() -> None:
    """Admission never calls a method on the value being admitted."""

    class Liar(str):
        def strip(self, chars: str | None = None) -> str:
            return "not quarantined"

        def lower(self) -> str:
            return "not quarantined"

    assert quarantined_identities(package_uuid=Liar(PKG)) == (f"package_uuid={PKG}",)


def test_a_non_identity_type_is_refused_rather_than_coerced() -> None:
    with pytest.raises(TypeError, match="package_uuid must be str, UUID or None"):
        quarantined_identities(package_uuid=object())


def test_the_error_names_the_seam_and_the_decision() -> None:
    with pytest.raises(QuarantinedAuthorityError) as excinfo:
        refuse_quarantined("some seam", package_uuid=PKG)
    assert excinfo.value.seam == "some seam"
    assert excinfo.value.matched == (f"package_uuid={PKG}",)
    assert "owner-decision-2026-09-21-5c-5d-clean-restart.md" in str(excinfo.value)


def test_the_retired_artifacts_are_removed_and_still_refused() -> None:
    """Step 5 removed the files; the identities they stated stay refused.

    Git history retains the bytes. What must not follow the files out of the tree
    is the refusal: a copied file, stored row or operator command naming the
    retired release still meets ``QuarantinedAuthorityError``, not ``None``.
    """
    for relative in QUARANTINED_ARTIFACT_FILENAMES:
        assert not (REPO_ROOT / relative).exists(), relative
    with pytest.raises(QuarantinedAuthorityError):
        oracle.committed_inputs_for(PKG, REL)


# ---------------------------------------------------------------------------
# Selection and direct loading of the accepted 5d authority
# ---------------------------------------------------------------------------


def test_committed_oracle_resolution_refuses_the_quarantined_release() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        oracle.committed_oracle_for(PKG, REL)


def test_committed_inputs_resolution_refuses_the_quarantined_release() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        oracle.committed_inputs_for(PKG, REL)


def test_the_directory_parameterized_test_seam_refuses_too(tmp_path: Any) -> None:
    """The test-only directory argument is not a way back in."""
    with pytest.raises(QuarantinedAuthorityError):
        oracle._resolve_committed_inputs(PKG, REL, tmp_path)
    with pytest.raises(QuarantinedAuthorityError):
        oracle._resolve_committed_oracle(PKG, REL, tmp_path)


# ---------------------------------------------------------------------------
# Publication, activation and reuse
# ---------------------------------------------------------------------------


def test_publication_entry_refuses_the_quarantined_projection() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        publication.publish_from_committed_oracle(None, PROJ, now=_now())  # type: ignore[arg-type]


def test_activation_refuses_the_quarantined_projection() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        publication._activate_projection(None, PROJ, now=_now())  # type: ignore[arg-type]


def test_active_projection_resolution_refuses_the_quarantined_package() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        publication.resolve_active_projection(None, PKG)  # type: ignore[arg-type]


def test_the_corpus_publication_gate_refuses_the_quarantined_release() -> None:
    class _Release:
        package_uuid = PKG
        release_version = REL

    class _Artifacts:
        release = _Release()

    with pytest.raises(QuarantinedAuthorityError):
        gate.run_gate(_Artifacts(), None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 5c corpus loading and the 5d fallback that binds it
# ---------------------------------------------------------------------------


def test_operational_corpus_load_refuses_the_quarantined_release() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        operational.load_verified_operational_corpus(
            None,  # type: ignore[arg-type]
            PKG,
            release_version=REL,
            authoritative_source_hash="",
            transform_config_hash="",
            bundle_root_hash="",
            persisted_corpus_digest="",
            supported_contract_versions=frozenset(),
        )


def test_bound_corpus_load_refuses_the_quarantined_release() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        bound_corpus.load_bound_corpus(None, PKG, REL)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Runtime selection and retrieval
# ---------------------------------------------------------------------------


@pytest.fixture()
def session() -> Any:
    """An isolated in-memory database. No shared store is opened or mutated."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sess = create_session_factory(engine)()
    try:
        yield sess
    finally:
        sess.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _package_row(package_uuid: str, name: str, version: str = REL) -> RulesPackageORM:
    """A published, enabled package row.

    ``version`` defaults to the quarantined release because most callers here are
    probing the quarantined product. An unrelated package must be given an
    unrelated version: a row carrying the quarantined release version under a
    fresh UUID is the same retired authority, and the read seam refuses it.
    """
    stamp = datetime.now(UTC).isoformat()
    return RulesPackageORM(
        rules_package_id=package_uuid,
        name=name,
        system="dnd5e",
        version=version,
        is_enabled=True,
        publication_status="published",
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )


def test_active_rule_slice_raises_instead_of_returning_an_empty_slice(
    session: Any,
) -> None:
    """An empty slice would read as "no rule applies" — the fail-open shape."""
    session.add(_package_row(PKG, "SRD 5.2.1 Corpus"))
    session.commit()
    with pytest.raises(QuarantinedAuthorityError):
        RulesPackageService(session).get_active_rule_slice(
            RuleSliceRequest(package_id=UUID(PKG), whole_package=True)
        )


def test_an_unrelated_package_is_not_refused_by_the_quarantine(session: Any) -> None:
    """Quarantine is identity-scoped: custom Rules Packages are not refused.

    Since the final CRD Issue 5d cutover the slice reads typed authority, so an
    unrelated package with no published projection gets the typed authority's
    own refusal, never the quarantine's — and never an empty slice.
    """
    session.add(_package_row(OTHER_PKG, "House Rules", OTHER_REL))
    session.commit()
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        RulesPackageService(session).get_active_rule_slice(
            RuleSliceRequest(package_id=UUID(OTHER_PKG), whole_package=True)
        )
    assert excinfo.value.outcome is not AuthorityOutcome.RESOLVED


def test_rule_slice_package_resolution_refuses_a_direct_reference(
    session: Any,
) -> None:
    with pytest.raises(QuarantinedAuthorityError):
        RulesPackageService(session).get_active_rule_slice(
            RuleSliceRequest(package_id=UUID(PKG), whole_package=True)
        )


def test_package_reference_resolution_refuses_the_uuid_form(session: Any) -> None:
    session.add(_package_row(PKG, "SRD 5.2.1 Corpus"))
    session.commit()
    with pytest.raises(QuarantinedAuthorityError):
        resolve_package_reference(session, PKG)


def test_package_reference_resolution_refuses_the_slug_form(session: Any) -> None:
    """A slug is not a way around a quarantined UUID."""
    session.add(_package_row(PKG, "SRD 5.2.1 Corpus"))
    session.commit()
    with pytest.raises(QuarantinedAuthorityError):
        resolve_package_reference(session, "srd-5-2-1-corpus")


def test_an_unrelated_slug_still_resolves(session: Any) -> None:
    session.add(_package_row(OTHER_PKG, "House Rules", OTHER_REL))
    session.commit()
    resolution = resolve_package_reference(session, "house-rules")
    assert resolution.package_uuid == UUID(OTHER_PKG)


def test_retrieval_reindex_refuses_the_quarantined_package() -> None:
    service = RulesCorpusService(None, None)  # type: ignore[arg-type]
    with pytest.raises(QuarantinedAuthorityError):
        service.reindex_from_sql(None, UUID(PKG))  # type: ignore[arg-type]


def test_retrieval_diagnostic_query_refuses_the_quarantined_package() -> None:
    service = RulesCorpusService(None, None)  # type: ignore[arg-type]
    with pytest.raises(QuarantinedAuthorityError):
        service.diagnostic_query(None, UUID(PKG), "grappled")  # type: ignore[arg-type]


def test_vector_reindex_refuses_the_quarantined_package() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        vector_publication.reindex_and_verify(None, PKG, None, None)  # type: ignore[arg-type]


def test_vector_verify_only_refuses_the_quarantined_package() -> None:
    with pytest.raises(QuarantinedAuthorityError):
        vector_publication.verify_only(None, PKG, None, None)  # type: ignore[arg-type]


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# The retired transform, independent of the identity it produces
# ---------------------------------------------------------------------------


def _alternate_identity_candidate(embedding_label: str) -> Any:
    """A candidate recording the retired recipe under a freshly minted identity.

    Only the three fields the finalization refusal reads are populated. The
    retired transform's code is gone, so the transform config is synthetic: it
    records the retired recipe hash beside the given embedding label, and the
    production identity functions mint a package UUID and release version from
    it, as a stored or copied release could carry.
    """
    payload = {
        "transform_identity": {"transform_source_hash": RECIPE},
        "rules_corpus_vector_identity": rules_corpus_vector_identity(embedding_label),
    }
    digest = hash_obj(payload)
    return SimpleNamespace(
        package_uuid=derive_package_uuid(PDF_SHA256, digest),
        release_version=derive_release_version(PDF_SHA256, digest),
        transform_config=payload,
    )


def test_an_alternate_embedding_label_mints_an_unquarantined_identity() -> None:
    """The gap this regression closes, stated as a measurement.

    Changing the configurable embedding model label produces a package UUID and
    release version no frozen identity set contains -- with the same retired
    recipe. Identity alone therefore cannot close this path.
    """
    alternate = _alternate_identity_candidate("independent-review-alternate-embedding")
    assert alternate.package_uuid != PKG
    assert alternate.release_version != REL
    assert (
        quarantined_identities(
            package_uuid=alternate.package_uuid,
            release_version=alternate.release_version,
        )
        == ()
    )


@pytest.mark.parametrize(
    "embedding_label",
    ["chroma-onnx-minilm-l6-v2", "independent-review-alternate-embedding"],
)
def test_finalization_refuses_the_retired_transform_whatever_its_identity(
    embedding_label: str,
) -> None:
    """Both labels are refused by the transform recipe alone.

    ``session``, ``chroma_client`` and ``retrieval_config`` are ``None``: step 0
    sits above the idempotency select, so a refusal that reaches no store handle
    cannot have read or written one.
    """
    candidate = _alternate_identity_candidate(embedding_label)
    with pytest.raises(QuarantinedAuthorityError) as refused:
        persistence._finalize_core(
            None,  # type: ignore[arg-type]
            candidate,
            now=_now(),
            chroma_client=None,  # type: ignore[arg-type]
            retrieval_config=None,  # type: ignore[arg-type]
        )
    assert refused.value.seam == "corpus release finalization"
    assert any(m.startswith("transform_source_hash=") for m in refused.value.matched)


def test_a_replacement_transform_recipe_is_not_refused() -> None:
    """Scoped to the retired recipe, not to corpus finalization as such.

    A candidate recording a different transform source hash is not matched; the
    fresh corpus is admitted by having a different transform rather than by
    having a different output hash.
    """
    assert quarantined_identities(transform_source_hash="0" * 64) == ()


def test_the_obsolete_cli_refuses_before_migrating_or_opening_any_store(
    tmp_path: Any,
) -> None:
    """The real command, as a subprocess, with a database URL it must not touch.

    Asserted on the observable consequence rather than on a monkeypatched call
    order: ``--db-url`` names a SQLite file ``upgrade_to_head`` would create on
    contact, and it does not exist afterwards. The second invocation passes a
    path that is not the authoritative PDF and still fails with the quarantine
    refusal, which places the refusal above the PDF check too.
    """
    db_path = tmp_path / "probe.db"
    for pdf_arg in ("docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf", str(tmp_path / "no.pdf")):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/ingest_srd.py",
                "--db-url",
                f"sqlite:///{db_path}",
                "--pdf-path",
                pdf_arg,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "QuarantinedAuthorityError" in result.stderr
        assert "obsolete corpus ingestion command" in result.stderr
        assert "owner-decision-2026-09-21" in result.stderr
        assert not db_path.exists(), "the retired command migrated the database"
        assert not list(tmp_path.glob("chroma*")), "a vector store was created"


def test_the_baseline_reset_refuses_before_deleting_any_collection(
    tmp_path: Any,
) -> None:
    """The sibling command, which deletes every collection then rebuilds.

    Not obsolete — it stays usable for the replacement corpus — but it refuses a
    quarantined release, and where it refuses is the whole point.

    Its rebuild seam refuses the quarantined package, but by then the whole store
    — ``story_memory`` included — is gone and this command rebuilds rules corpora
    only, so the refusal has to land in preflight. Asserted on a sentinel file in
    the configured persist directory: a store that had been opened and reset would
    not leave it untouched.
    """
    db_path = tmp_path / "published.db"
    store = tmp_path / "chroma"
    store.mkdir()
    sentinel = store / "chroma.sqlite3"
    sentinel.write_text("sentinel", encoding="utf-8")

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        _seed_ingested_package(session, PKG, REL)
        session.add(
            CorpusReleaseORM(
                package_uuid=PKG,
                release_version=REL,
                authoritative_source_hash="0" * 64,
                transform_config_hash="0" * 64,
                bundle_root_hash="0" * 64,
                ledger_hash="0" * 64,
                policy_hash="0" * 64,
                reconciliation_hash="0" * 64,
                transform_config={
                    "transform_identity": {"transform_source_hash": RECIPE}
                },
                publication_status="published",
                created_at=_now(),
            )
        )
        session.commit()
    engine.dispose()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/reset_corpus_baseline.py",
            "--db-url",
            f"sqlite:///{db_path}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY": str(store)},
    )
    assert result.returncode != 0
    assert "QuarantinedAuthorityError" in result.stderr
    assert "corpus baseline reset" in result.stderr
    assert "transform_source_hash=" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "sentinel"


# ---------------------------------------------------------------------------
# The generic ingestion service and the default read surface
# ---------------------------------------------------------------------------


class _CountOnlyReadback:
    """Enough of a vector writer for the publication gate; opens nothing."""

    def count_chunks(self, package_id: str) -> int:
        return 1


def _seed_ingested_package(session: Any, package_uuid: str, version: str) -> str:
    """A complete, gate-passing draft package: row, source, chunk, entity, manifest.

    Returns the chunk id, which the override read needs.
    """
    stamp = _now()
    source_id = str(uuid4())
    chunk_id = str(uuid4())
    session.add(
        RulesPackageORM(
            rules_package_id=package_uuid,
            name="SRD 5.2.1 Corpus",
            system="d20",
            version=version,
            is_enabled=True,
            publication_status="draft",
            created_at=stamp,
            updated_at=stamp,
        )
    )
    session.flush()  # rows are unrelated mappers, so each parent flushes first
    session.add(
        RuleSourceORM(
            source_id=source_id,
            rules_package_id=package_uuid,
            name="SRD 5.2.1",
            category="core_rulebook",
            precedence_rank=0,
            created_at=stamp,
        )
    )
    session.flush()  # the chunk composite key needs the source row
    session.add(
        RuleChunkORM(
            chunk_id=chunk_id,
            rules_package_id=package_uuid,
            source_id=source_id,
            subsystem="conditions",
            content="Probe content.",
            source_document="SRD 5.2.1",
            source_locator_type="page",
            source_locator_value="9",
            created_at=stamp,
        )
    )
    session.add(
        RulesPackageManifestORM(
            manifest_id=str(uuid4()),
            rules_package_id=package_uuid,
            authoritative_source_document="SRD 5.2.1",
            authoritative_source_version="5.2.1",
            package_license="CC BY 4.0",
            transform_status="probe",
            attribution_text="probe",
            sql_ingest_complete=True,
            vector_write_complete=True,
            created_at=stamp,
            updated_at=stamp,
        )
    )
    session.commit()
    return chunk_id


def test_generic_publication_refuses_the_quarantined_package(session: Any) -> None:
    """The reproduced bypass: a parallel service published the quarantined row."""
    _seed_ingested_package(session, PKG, REL)
    service = IngestionService(
        IngestionConfig(package_name="SRD 5.2.1 Corpus", package_version=REL)
    )
    with pytest.raises(QuarantinedAuthorityError) as refused:
        service.publish(session, PKG, _CountOnlyReadback())  # type: ignore[arg-type]
    assert refused.value.seam == "generic package publication"
    assert session.get(RulesPackageORM, PKG).publication_status == "draft"


def test_generic_publication_refuses_the_retired_release_under_a_new_uuid(
    session: Any,
) -> None:
    """A fresh package UUID does not launder the retired release version."""
    _seed_ingested_package(session, OTHER_PKG, REL)
    service = IngestionService(
        IngestionConfig(package_name="SRD 5.2.1 Corpus", package_version=REL)
    )
    with pytest.raises(QuarantinedAuthorityError):
        service.publish(session, OTHER_PKG, _CountOnlyReadback())  # type: ignore[arg-type]
    assert session.get(RulesPackageORM, OTHER_PKG).publication_status == "draft"


def test_generic_ingestion_refuses_before_parsing_or_writing(session: Any) -> None:
    """Configured for the quarantined release, ``ingest`` writes nothing.

    ``chroma_client`` is ``None`` and ``srd_data`` is empty: the refusal precedes
    the parse, so neither is reached.
    """
    service = IngestionService(
        IngestionConfig(package_name="SRD 5.2.1 Corpus", package_version=REL)
    )
    with pytest.raises(QuarantinedAuthorityError) as refused:
        service.ingest(session, {}, "srd.json", None)  # type: ignore[arg-type]
    assert refused.value.seam == "generic package ingestion"
    assert session.execute(select(RulesPackageORM)).scalars().all() == []


def test_every_default_read_refuses_the_quarantined_package(session: Any) -> None:
    """The reproduced read bypass, across the whole by-id surface.

    ``get_active_rule_slice`` is guarded at its own entry; the two source-corpus
    reads share ``_package_accessible``, which is where their refusal lives.
    (The entity and legacy-override reads were retired at the final CRD Issue 5d
    cutover.)
    """
    _seed_ingested_package(session, PKG, REL)
    session.get(RulesPackageORM, PKG).publication_status = "published"
    session.commit()
    reads = RulesPackageService(session)
    calls = (
        lambda: reads.get_package_by_id(UUID(PKG)),
        lambda: reads.get_chunks_by_subsystem(UUID(PKG), RuleSubsystemEnum.CONDITIONS),
    )
    for call in calls:
        with pytest.raises(QuarantinedAuthorityError) as refused:
            call()
        assert refused.value.seam == "rules package read"


def test_an_administrative_draft_read_is_not_a_way_around_the_refusal(
    session: Any,
) -> None:
    """``include_non_published`` is a lifecycle policy, not a reference mode.

    This service has no diagnostic surface, so a draft read of a quarantined
    package is still this subsystem answering an authority question about it. The
    committed artifacts stay readable as bytes -- see the oracle reference test
    above; that is where explicit reference access lives.
    """
    _seed_ingested_package(session, PKG, REL)
    with pytest.raises(QuarantinedAuthorityError):
        RulesPackageService(session).get_package_by_id(
            UUID(PKG), include_non_published=True
        )


# ---------------------------------------------------------------------------
# Unrelated packages keep working
# ---------------------------------------------------------------------------


def test_an_unrelated_package_still_publishes_and_reads(session: Any) -> None:
    """Identity-scoped, demonstrated on the seams that now refuse.

    A custom package with its own UUID and version publishes through the generic
    service and stays readable across the default read surface, so these guards
    are not a subsystem outage.
    """
    _seed_ingested_package(session, OTHER_PKG, OTHER_REL)
    service = IngestionService(
        IngestionConfig(package_name="SRD 5.2.1 Corpus", package_version=OTHER_REL)
    )
    service.publish(session, OTHER_PKG, _CountOnlyReadback())  # type: ignore[arg-type]
    row = session.get(RulesPackageORM, OTHER_PKG)
    assert row.publication_status == "published" and row.published_at

    reads = RulesPackageService(session)
    detail = reads.get_package_by_id(UUID(OTHER_PKG))
    assert detail is not None and detail.rules_package_id == UUID(OTHER_PKG)
    chunks = reads.get_chunks_by_subsystem(
        UUID(OTHER_PKG), RuleSubsystemEnum.CONDITIONS
    )
    assert [c.content for c in chunks.chunks] == ["Probe content."]


def test_an_unrelated_ingestion_configuration_is_not_refused(session: Any) -> None:
    """The ``ingest`` entry guard is scoped to the quarantined release version.

    An unrelated configuration gets past it and ingests normally, which is what
    "unaffected" means here. Empty SRD data keeps the probe cheap: the point is
    that the package row is created and carries the configured version.
    """
    service = IngestionService(
        IngestionConfig(package_name="House Rules", package_version=OTHER_REL)
    )
    result = service.ingest(session, {}, "srd.json", None)  # type: ignore[arg-type]
    row = session.get(RulesPackageORM, result.package_id)
    assert row.version == OTHER_REL
    assert row.publication_status == "draft"
