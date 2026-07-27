"""First-party transform identity + source manifest — CRD Issue 5c, Component B.

The transform source/configuration hash (Component B) must change whenever *any*
first-party code that can affect the candidate corpus or its canonical
identities (Component K steps a0–a3, and the canonical-payload/identity code in
step b) changes — not only when the extractor version or the frozen policy
changes. Otherwise a segmentation fix in ``ledger`` or a chunk-generation change
in ``transform`` keeps the same ``transform_config_hash`` → same ``package_uuid``
/ ``release_version`` → ``finalize_release`` reuses the *old* persisted corpus as
a no-op instead of minting the new immutable draft the changed code requires
(PR #134 P1, ``bundle.py:40``).

This module derives that identity **automatically** from the actual committed
source bytes of a fixed, audited set of first-party modules. There is no
manually bumped version whose omission could silently bypass detection: the
aggregate ``transform_source_hash`` is a pure function of those files' bytes, so
editing any of them moves the hash with no human action. ``TRANSFORM_TOOL_VERSION``
is a descriptive label only and gates nothing.

Manifest audit (bounded transitive walk of Component K steps a0–b; each first-
party corpus module inspected and dispositioned — see the review-note remediation
log for the full table). A module is *included* iff its source bytes can change
the candidate corpus or a canonical identity; *already-covered* iff its effect is
bound some other way; *verification-only* iff it cannot change the candidate bytes:

    included         pdf_source, ledger, tables, transform, reconcile, policy,
                     bundle, hashing, models, pipeline, transform_identity
    already-covered  models.retrieval.rules_corpus_vector_identity (its *output*,
                     the vector identity, is bound into transform_config directly)
    verification-only  concordance, report, gate, persistence, vector_publication,
                     source_completeness  (verification / post-persistence /
                     runtime only)

``tables`` reached the manifest via ``ledger`` (a1→a2 segmentation): it owns table
segmentation, cell contents/ids, and row/column metadata, so a change there must
mint a new release (PR #134 R15 F1). The Finding-4 expected-table inventory is a
candidate-affecting *data* input; its hash is bound into the transform config
payload alongside this source hash (see ``bundle.transform_config_payload``).
"""

from __future__ import annotations

from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj, sha256_hex

# Descriptive label for the transform toolchain. Change detection does NOT rely
# on this string — it relies on TRANSFORM_SOURCE_MODULES' actual bytes below.
TRANSFORM_TOOL_NAME = "afterworlds-srd-corpus-transform"
TRANSFORM_TOOL_VERSION = "1"

# The audited first-party modules whose source bytes are bound into the transform
# identity. Ordering here is irrelevant to the aggregate hash (entries are sorted
# by canonical path before hashing) but is kept alphabetical for readability.
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

# Canonical repository-relative directory these modules live in. Recorded in the
# manifest so the paths are stable across checkouts and machines.
_CORPUS_PKG_REL = "src/afterworlds/ingestion/corpus"
_CORPUS_DIR = Path(__file__).resolve().parent


class TransformSourceMissingError(RuntimeError):
    """Raised when an audited transform-source module is absent — fail closed."""


def _source_sha256(data: bytes) -> str:
    """SHA-256 of source *data* with newlines normalized to ``\\n``.

    Normalization (matching the pipeline's canonical ``\\n`` discipline) makes
    the identity insensitive to a CRLF checkout while still moving on any real
    content change — the same reasoning as geometry rounding for extraction.
    ``.gitattributes`` already pins ``*.py`` to ``eol=lf``; this is belt-and-
    suspenders.
    """
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_hex(normalized)


def aggregate_source_hash(entries: list[tuple[str, str]]) -> str:
    """Pure aggregate over ``(repo_relative_path, source_sha256)`` pairs.

    Deterministic and independent of input ordering (entries are sorted by path).
    Any change to any covered file's ``source_sha256`` — hence any change to its
    bytes — changes the aggregate.
    """
    ordered = sorted(entries)
    return hash_obj([{"path": p, "sha256": h} for p, h in ordered])


def transform_source_manifest(root: Path | None = None) -> dict[str, object]:
    """Read the audited modules from *root* and return their manifest + aggregate.

    *root* defaults to the real corpus package directory; a caller may pass a
    copy of the tree to prove byte-sensitivity in a test. Repo-relative paths are
    always canonical regardless of *root*, so the identity is location-stable.
    Fails closed if any audited module is missing.
    """
    # ponytail: `root` param exists only so tests can point at a mutated copy of
    # the source tree; production always uses the real package dir.
    base = root if root is not None else _CORPUS_DIR
    modules: list[dict[str, str]] = []
    entries: list[tuple[str, str]] = []
    for name in sorted(TRANSFORM_SOURCE_MODULES):
        path = base / name
        if not path.is_file():
            raise TransformSourceMissingError(
                f"audited transform-source module missing: {path}"
            )
        rel = f"{_CORPUS_PKG_REL}/{name}"
        digest = _source_sha256(path.read_bytes())
        modules.append({"path": rel, "sha256": digest})
        entries.append((rel, digest))
    return {
        "modules": modules,
        "transform_source_hash": aggregate_source_hash(entries),
    }


def transform_identity(root: Path | None = None) -> dict[str, object]:
    """The complete first-party transform identity (Component B).

    Tool label + auto-derived source manifest/hash + the deterministic Component
    B invocation + whether an intermediate representation is committed. This is
    embedded in the transform source/configuration payload and drives the
    transform hash, package UUID, and release version.
    """
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
        # No intermediate representation is committed to the repository; the
        # corpus is regenerated deterministically from the PDF + these sources.
        "intermediate_representation_committed": False,
    }
