"""Declared semantic transform identity — CRD Issue 5c (#145).

Release identity follows the authoritative source and the approved logical
corpus, not every byte of every implementation file.  The original Issue 5c
implementation hashed eleven Python modules; comments, annotations, logging,
and other incidental edits therefore reminted an unchanged corpus.

``TRANSFORM_TOOL_VERSION`` is now the explicit semantic compatibility version.
It must be bumped when extraction, segmentation, canonical corpus content,
provenance, or compatibility changes meaningfully.  The frozen v1 manifest is
retained in the payload solely to preserve the honest identity of the already
approved v1 logical corpus.  It is historical identity metadata, not a claim
that current source bytes still equal those pre-amendment hashes.
"""

from __future__ import annotations

from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj

TRANSFORM_TOOL_NAME = "afterworlds-srd-corpus-transform"
# Bump deliberately for a meaningful logical-corpus or compatibility change.
TRANSFORM_TOOL_VERSION = "1"

# Historical v1 source set retained for API compatibility and for the exact
# pre-amendment transform payload.  It no longer drives automatic byte checks.
TRANSFORM_SOURCE_MODULES: tuple[str, ...] = (
    "bundle.py",
    "hashing.py",
    "ledger.py",
    "models.py",
    "pdf_source.py",
    "pipeline.py",
    "policy.py",
    "reconcile.py",
    "tables.py",
    "transform.py",
    "transform_identity.py",
)

_V1_SOURCE_MANIFEST: tuple[tuple[str, str], ...] = (
    ("bundle.py", "9b3578de32454b3e87b7f7760c76128b6452a5cbc152e9ec4ae7e315d162db33"),
    ("hashing.py", "dfbb8e9eaaded95c7aa2a72351e9301953ee5f15fa332dbc706a9307828b2915"),
    ("ledger.py", "6717e8e4ab908aa02d8df0e87a453d1e1032f911cb26075168f2ac0e2b8610b3"),
    ("models.py", "d6de262fd9235253de7dc1c7c2163726fd0ce0b26b7dba8ee7ecf06902abb190"),
    (
        "pdf_source.py",
        "a205eafd02e9f754bfaca7e629b7de646a074b476f16066c6af2bb4caddf7453",
    ),
    ("pipeline.py", "f0af4fdb86fe76b957ab82f74dd26968d70ac3593634136d093c8584482773bc"),
    ("policy.py", "a58a3e03b28289d5a4c6869d7e3171676924e5090f305afe8b4e79eb1a37198f"),
    (
        "reconcile.py",
        "e24184fdc5ef556c9f9b401b74c19d94cf0c98400f3f8a6e0ca43fb02fe2f277",
    ),
    ("tables.py", "db88f21111892c9cb607e756a94df2ef315426bf84ec6733938e79fe2073cfa0"),
    (
        "transform.py",
        "a74bf829bdbdf94fec30cb0124e8d42f42a4837588d039afdf9f8325142610a7",
    ),
    (
        "transform_identity.py",
        "77b50cb8c835f7ea12a5e786172d9dd03035fafb3cf5a7593dd1ee15fd6b2a18",
    ),
)
_V1_TRANSFORM_SOURCE_HASH = (
    "6332f201eba9cba19d699a06c6c12580de5ef1c7f349fadacd2045c0e5312cc0"
)
_CORPUS_PKG_REL = "src/afterworlds/ingestion/corpus"


class TransformSourceMissingError(RuntimeError):
    """Legacy public exception retained for import compatibility."""


def aggregate_source_hash(entries: list[tuple[str, str]]) -> str:
    """Canonical aggregate helper retained for diagnostic tooling."""
    ordered = sorted(entries)
    return hash_obj([{"path": path, "sha256": digest} for path, digest in ordered])


def transform_source_manifest(root: Path | None = None) -> dict[str, object]:
    """Return the frozen v1 manifest used by the approved logical corpus.

    ``root`` remains accepted so older callers do not break, but source-tree
    inspection is intentionally no longer part of release identity.
    """
    del root
    return {
        "modules": [
            {"path": f"{_CORPUS_PKG_REL}/{name}", "sha256": digest}
            for name, digest in _V1_SOURCE_MANIFEST
        ],
        "transform_source_hash": _V1_TRANSFORM_SOURCE_HASH,
    }


def transform_identity(root: Path | None = None) -> dict[str, object]:
    """Return the explicit semantic identity of the corpus transformation."""
    manifest = transform_source_manifest(root)
    return {
        "tool": TRANSFORM_TOOL_NAME,
        "tool_version": TRANSFORM_TOOL_VERSION,
        "source_manifest": manifest["modules"],
        "transform_source_hash": manifest["transform_source_hash"],
        "component_b_invocation": {
            "entrypoint": "afterworlds.ingestion.corpus.pipeline.build_candidate",
            "steps": (
                "a0:freeze_policy",
                "a1:extract_pdf+build_ledger",
                "a2:build_corpus",
                "a3:reconcile",
                "b:bundle_root",
            ),
            "deterministic": True,
        },
        "intermediate_representation_committed": False,
    }
