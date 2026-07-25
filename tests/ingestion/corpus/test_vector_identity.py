"""Rules-corpus vector identity in the immutable release identity — PR #134 P1.

``embedding_model_id`` (and the vector logical schema/ID/metadata contract) change
the required vector metadata and the persisted digest, so they must also change
the package UUID / release version — otherwise a model change forces a reindex
whose digest describes the new model while ``finalize_release`` takes the
verify-only reuse path against the stale stored digest with no identity to mint a
replacement. Binding the vector identity into the transform config closes that
dead end.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
    transform_config_hash,
)
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256, extraction_config
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import RulesPackageORM

_NOW = "2026-01-01T00:00:00Z"


def test_identical_vector_identity_is_deterministic():
    assert rules_corpus_vector_identity("m") == rules_corpus_vector_identity("m")


def test_vector_identity_binds_only_identity_inputs():
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


def test_model_change_moves_transform_hash_uuid_and_version():
    ex = extraction_config()
    h_a = transform_config_hash(ex, FROZEN_POLICY, rules_corpus_vector_identity("A"))
    h_b = transform_config_hash(ex, FROZEN_POLICY, rules_corpus_vector_identity("B"))
    assert h_a != h_b
    assert derive_package_uuid(PDF_SHA256, h_a) != derive_package_uuid(PDF_SHA256, h_b)
    assert derive_release_version(PDF_SHA256, h_a) != derive_release_version(
        PDF_SHA256, h_b
    )


def test_model_change_creates_coexisting_release_without_collision():
    """Two releases differing only in embedding model get distinct
    (name, version, system) keys and coexist; neither mutates the other (the same
    DF3 collision surface — the fixed corpus name)."""
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    session = create_session_factory(eng)()
    ex = extraction_config()
    try:
        h_a = transform_config_hash(
            ex, FROZEN_POLICY, rules_corpus_vector_identity("A")
        )
        h_b = transform_config_hash(
            ex, FROZEN_POLICY, rules_corpus_vector_identity("B")
        )
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
