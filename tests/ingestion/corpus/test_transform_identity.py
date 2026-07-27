"""First-party transform-identity tests — Issue 5c, PR #134 P1.

The transform source/configuration hash must move whenever any audited
first-party transform-source module changes, so a transform-code change mints a
new immutable release identity instead of reusing the predecessor. These tests
prove byte-sensitivity, the audited coverage set (the no-silent-bypass guard),
and the binding into package UUID / release version — without a full-corpus
rebuild.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

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
    TransformSourceMissingError,
    aggregate_source_hash,
    transform_identity,
    transform_source_manifest,
)

_CORPUS_DIR = Path(__file__).resolve().parents[3] / ("src/afterworlds/ingestion/corpus")


# --- aggregate purity --------------------------------------------------------


def test_aggregate_source_hash_is_order_independent():
    a = [("z.py", "1" * 64), ("a.py", "2" * 64)]
    assert aggregate_source_hash(a) == aggregate_source_hash(list(reversed(a)))


def test_aggregate_source_hash_changes_on_any_byte():
    base = [("a.py", "1" * 64), ("b.py", "2" * 64)]
    flipped = [("a.py", "1" * 64), ("b.py", "3" * 64)]
    assert aggregate_source_hash(base) != aggregate_source_hash(flipped)


# --- coverage set (no silent bypass) -----------------------------------------


def test_manifest_covers_exactly_the_audited_modules():
    """Locks the audit disposition: if a covered module silently drops out of
    coverage, this fails — the change-detection guarantee can't be bypassed by
    quietly removing a file from the manifest."""
    manifest = transform_source_manifest()
    got = {m["path"].rsplit("/", 1)[1] for m in manifest["modules"]}  # type: ignore[index]
    assert got == set(TRANSFORM_SOURCE_MODULES)


def test_manifest_reflects_real_source_bytes_not_a_constant():
    """Each recorded sha256 must be the real (newline-normalized) file digest, so
    the identity is derived from actual bytes rather than a hardcoded value."""
    import hashlib

    manifest = transform_source_manifest()
    for entry in manifest["modules"]:  # type: ignore[union-attr]
        name = entry["path"].rsplit("/", 1)[1]  # type: ignore[index]
        raw = (_CORPUS_DIR / name).read_bytes()
        norm = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        assert entry["sha256"] == hashlib.sha256(norm).hexdigest()  # type: ignore[index]


# --- byte-sensitivity via a mutated copy of the tree -------------------------


@pytest.mark.parametrize("target", TRANSFORM_SOURCE_MODULES)
def test_changing_any_covered_source_byte_moves_transform_source_hash(tmp_path, target):
    """Copy the corpus tree, flip one byte in each covered module in turn, and
    assert the aggregate transform-source hash moves — automatically, with no
    version bump."""
    real = transform_source_manifest()["transform_source_hash"]
    copy_dir = tmp_path / "corpus"
    copy_dir.mkdir()
    for name in TRANSFORM_SOURCE_MODULES:
        shutil.copy(_CORPUS_DIR / name, copy_dir / name)
    p = copy_dir / target
    p.write_bytes(p.read_bytes() + b"\n# tamper\n")
    changed = transform_source_manifest(copy_dir)["transform_source_hash"]
    assert changed != real


@pytest.mark.parametrize("mutated_module", ["ledger.py", "tables.py"])
def test_transform_code_change_moves_config_hash_uuid_and_version(
    tmp_path, mutated_module
):
    """A transform-source change (PDF + extractor config + policy fixed) moves the
    transform_config_hash and therefore both the package UUID and release
    version — so finalize_release cannot reuse the predecessor's identity.
    ``tables.py`` (table segmentation/ids/row-col metadata) is covered explicitly
    (PR #134 R15 F1)."""
    ex = extraction_config()
    vid = {"embedding_model_id": "m", "metadata_fields": ["subsystem"]}
    # Build the COMPLETE production transform payload (all identity fields —
    # extractor config, policy, transform identity, vector identity, expected-table
    # inventory hash, evidence-report schema version). Mutating only the transform
    # identity keeps every other field equal, so the inequality below is a genuine
    # difference in the transform-source hash, not an artifact of an omitted field
    # (R17: don't let a partial payload make the assertion vacuous).
    real_payload = transform_config_payload(ex, FROZEN_POLICY, vid)
    real_hash = transform_config_hash(ex, FROZEN_POLICY, vid)
    assert hash_obj(real_payload) == real_hash  # helper builds the production shape

    # Simulate a code-only change by recomputing the identity against a mutated
    # copy of the source tree (same PDF, extractor config, policy, and vector id).
    copy_dir = tmp_path / "corpus"
    copy_dir.mkdir()
    for name in TRANSFORM_SOURCE_MODULES:
        shutil.copy(_CORPUS_DIR / name, copy_dir / name)
    p = copy_dir / mutated_module
    p.write_bytes(p.read_bytes() + b"\n# segmentation tweak\n")
    mutated_identity = transform_identity(copy_dir)
    mutated_payload = {**real_payload, "transform_identity": mutated_identity}
    mutated_hash = hash_obj(mutated_payload)

    assert mutated_hash != real_hash
    assert derive_package_uuid(PDF_SHA256, mutated_hash) != derive_package_uuid(
        PDF_SHA256, real_hash
    )
    assert derive_release_version(PDF_SHA256, mutated_hash) != derive_release_version(
        PDF_SHA256, real_hash
    )


def test_report_schema_version_is_bound_into_identity():
    """R17: the canonical evidence-report schema version is part of the transform
    payload, so changing it moves the transform hash, package UUID, and release
    version — a report-schema change mints a new immutable release instead of
    being reused under a predecessor's identity."""
    ex = extraction_config()
    vid = {"embedding_model_id": "m", "metadata_fields": ["subsystem"]}
    base = transform_config_payload(ex, FROZEN_POLICY, vid)
    # Present in the production shape (and the inventory hash too — completeness).
    assert base["evidence_report_schema_version"]
    assert base["expected_table_inventory_hash"]
    variant = {**base, "evidence_report_schema_version": "5c-evidence-OTHER"}
    bh, vh = hash_obj(base), hash_obj(variant)
    assert bh != vh
    assert derive_package_uuid(PDF_SHA256, bh) != derive_package_uuid(PDF_SHA256, vh)
    assert derive_release_version(PDF_SHA256, bh) != derive_release_version(
        PDF_SHA256, vh
    )


def test_identical_sources_are_deterministic():
    assert (
        transform_source_manifest()["transform_source_hash"]
        == transform_source_manifest()["transform_source_hash"]
    )


# --- fail closed + Component B record -----------------------------------------


def test_missing_covered_module_fails_closed(tmp_path):
    with pytest.raises(TransformSourceMissingError):
        transform_source_manifest(tmp_path)  # empty dir → module missing


def test_transform_identity_records_component_b_invocation_and_ir_flag():
    ti = transform_identity()
    assert ti["transform_source_hash"]
    assert ti["intermediate_representation_committed"] is False
    inv = ti["component_b_invocation"]
    assert inv["deterministic"] is True  # type: ignore[index]
    assert "build_candidate" in inv["entrypoint"]  # type: ignore[index]
