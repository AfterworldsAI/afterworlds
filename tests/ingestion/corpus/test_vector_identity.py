"""Rules-corpus vector identity in the immutable release identity — PR #134 P1.

``embedding_model_id`` (and the vector logical schema/ID/metadata contract) change
the required vector metadata and the persisted digest, so they must also change
the package UUID / release version — otherwise a model change forces a reindex
whose digest describes the new model while finalization takes the verify-only
reuse path against the stale stored digest with no identity to mint a
replacement. Binding the vector identity into the transform config closes that
dead end. Asserted on the source-built release's transform config, which is the
only one the build produces.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
)
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY
from afterworlds.ingestion.corpus.source_ledger import source_transform_config_payload
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import RulesPackageORM

_NOW = "2026-01-01T00:00:00Z"

#: The shape of a pinned-source extraction config, with one synthetic file.
_EXTRACTION: dict[str, object] = {
    "files": [{"path": "synthetic.md", "sha256": "0" * 64}]
}


def _transform_config_hash(vector_identity: dict[str, object]) -> str:
    return hash_obj(
        source_transform_config_payload(
            _EXTRACTION, FROZEN_POLICY, vector_identity, primary_pages=(1,)
        )
    )


def test_identical_vector_identity_is_deterministic() -> None:
    assert rules_corpus_vector_identity("m") == rules_corpus_vector_identity("m")


def test_vector_identity_binds_only_identity_inputs() -> None:
    """Contract shape + embedding model only — never operational settings or
    embedding bytes (those don't change the persisted vector logical state)."""
    vid = rules_corpus_vector_identity("chroma-onnx-minilm-l6-v2")
    assert vid["embedding_model_id"] == "chroma-onnx-minilm-l6-v2"
    assert vid["metadata_fields"]  # metadata schema shape present
    assert vid["chunk_id_scheme"] and vid["collection_name_scheme"]
    for banned in (
        "persist_directory",
        "top_k",
        "minimum_similarity_threshold",
        "batch_size",
        "distance_metric",
        "embeddings",
    ):
        assert banned not in vid


def test_model_change_moves_transform_hash_uuid_and_version() -> None:
    h_a = _transform_config_hash(rules_corpus_vector_identity("A"))
    h_b = _transform_config_hash(rules_corpus_vector_identity("B"))
    assert h_a != h_b
    assert derive_package_uuid(PDF_SHA256, h_a) != derive_package_uuid(PDF_SHA256, h_b)
    assert derive_release_version(PDF_SHA256, h_a) != derive_release_version(
        PDF_SHA256, h_b
    )


def test_model_change_yields_distinct_name_version_keys() -> None:
    """Narrow scope: two embedding-model-differing releases get distinct
    (name, version, system) keys on ``rp_packages``; neither mutates the other.
    This proves ONLY the package-key constraint — full chunk/projection
    coexistence is never claimed from ``rp_packages`` alone (PR #134 P1)."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    session = create_session_factory(eng)()
    try:
        h_a = _transform_config_hash(rules_corpus_vector_identity("A"))
        h_b = _transform_config_hash(rules_corpus_vector_identity("B"))
        for h in (h_a, h_b):
            session.add(
                RulesPackageORM(
                    rules_package_id=derive_package_uuid(PDF_SHA256, h),
                    name="SRD 5.2.1 Corpus",  # fixed corpus name
                    system="d20",
                    version=derive_release_version(PDF_SHA256, h),
                    is_enabled=True,
                    publication_status="published",
                    created_at=_NOW,
                    updated_at=_NOW,
                )
            )
        session.commit()  # distinct versions -> no IntegrityError
        assert session.query(RulesPackageORM).count() == 2
    finally:
        session.close()
        eng.dispose()
