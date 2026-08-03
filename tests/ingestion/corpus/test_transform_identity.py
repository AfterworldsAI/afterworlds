"""Semantic transform-identity tests — CRD Issue 5c operational correction."""

from __future__ import annotations

from afterworlds.ingestion.corpus import report
from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
    transform_config_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.pdf_source import PDF_SHA256, extraction_config
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY
from afterworlds.ingestion.corpus.transform_identity import (
    TRANSFORM_SOURCE_MODULES,
    TRANSFORM_TOOL_VERSION,
    aggregate_source_hash,
    transform_identity,
    transform_source_manifest,
)


def test_aggregate_source_hash_is_order_independent():
    entries = [("z.py", "1" * 64), ("a.py", "2" * 64)]
    assert aggregate_source_hash(entries) == aggregate_source_hash(
        list(reversed(entries))
    )


def test_v1_manifest_is_frozen_identity_metadata():
    manifest = transform_source_manifest()
    assert manifest["transform_source_hash"] == (
        "6332f201eba9cba19d699a06c6c12580de5ef1c7f349fadacd2045c0e5312cc0"
    )
    assert {entry["path"].rsplit("/", 1)[1] for entry in manifest["modules"]} == set(
        TRANSFORM_SOURCE_MODULES
    )


def test_incidental_source_tree_location_or_bytes_do_not_move_identity(tmp_path):
    # The compatibility argument remains accepted for callers, but release
    # identity no longer reads arbitrary implementation bytes from it.
    (tmp_path / "transform.py").write_text("# comment-only change\n")
    assert transform_identity(tmp_path) == transform_identity()


def test_deliberate_semantic_version_change_moves_uuid_and_release_version():
    ex = extraction_config()
    vector_identity = {"embedding_model_id": "m", "metadata_fields": ["subsystem"]}
    base = transform_config_payload(ex, FROZEN_POLICY, vector_identity)
    changed_identity = {
        **base["transform_identity"],
        "tool_version": f"{TRANSFORM_TOOL_VERSION}-meaningful-change",
    }
    changed = {**base, "transform_identity": changed_identity}
    base_hash = hash_obj(base)
    changed_hash = hash_obj(changed)
    assert changed_hash != base_hash
    assert derive_package_uuid(PDF_SHA256, changed_hash) != derive_package_uuid(
        PDF_SHA256, base_hash
    )
    assert derive_release_version(PDF_SHA256, changed_hash) != derive_release_version(
        PDF_SHA256, base_hash
    )


def test_diagnostic_report_schema_does_not_move_corpus_identity(monkeypatch):
    ex = extraction_config()
    vector_identity = {"embedding_model_id": "m", "metadata_fields": ["subsystem"]}
    before = transform_config_hash(ex, FROZEN_POLICY, vector_identity)
    monkeypatch.setattr(report, "EVIDENCE_REPORT_SCHEMA_VERSION", "diagnostic-vNEXT")
    after = transform_config_hash(ex, FROZEN_POLICY, vector_identity)
    assert after == before


def test_transform_identity_records_declared_invocation():
    identity = transform_identity()
    assert identity["tool_version"] == TRANSFORM_TOOL_VERSION
    assert identity["transform_source_hash"]
    assert identity["intermediate_representation_committed"] is False
    invocation = identity["component_b_invocation"]
    assert invocation["deterministic"] is True  # type: ignore[index]
    assert "build_candidate" in invocation["entrypoint"]  # type: ignore[index]
