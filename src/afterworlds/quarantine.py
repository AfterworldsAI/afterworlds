"""Tombstone for the retired original CRD Issue 5c/5d products.

Recorded Owner Decision 2026-09-21 (``docs/decisions/``
``owner-decision-2026-09-21-5c-5d-clean-restart.md``) quarantined the original 5c
corpus release and the 5d accepted authority built over it, and its Step 5
retires them once the replacement exists. The replacement source corpus and the
fresh 5d authority now exist, so the original artifacts and the PDF-geometric
transform code have been removed from the tree; Git history retains them.

What remains is this refusal. A database, vector store, operator command or copied
file can still name a retired identity after the code is gone, so the seams that
confer authority keep refusing it rather than treating it as merely absent. The
Owner Decision is explicit that removing files is not enough if a selector or
fallback could still load what they described.

Two deliberate boundaries:

* **Identity-scoped, not blanket.** Only the frozen identities below are refused.
  An unrelated custom Rules Package, a story-memory collection, or a synthetic
  test release is untouched — a blanket disable would be a bigger outage than the
  defect it prevents.
* **The retired transform is an identity too.** A published package UUID is
  content-derived, so changing an incidental input (the configurable embedding
  model label) mints a *different* UUID for the same obsolete extraction. Keying
  only on the published UUID therefore closes one build of the retired product
  rather than the product. :data:`QUARANTINED_TRANSFORM_SOURCE_HASHES` names the
  retired PDF-geometric transform recipe itself, which no incidental
  reconfiguration moves, so the replacement corpus is admitted by having a
  different transform rather than by having a different hash.
* **Loud, not empty.** Every seam raises :class:`QuarantinedAuthorityError`. A
  quarantined package that resolved to an empty rule slice would be
  indistinguishable from a package with genuinely no rules, which is the
  fail-open shape the 5d runtime authority work exists to remove.

This module imports nothing from ``afterworlds``: it is reached from ingestion,
services and the retrieval pipeline alike, and a leaf module cannot create an
import cycle between them.
"""

from __future__ import annotations

from uuid import UUID

__all__ = [
    "QUARANTINED_ARTIFACT_DIGESTS",
    "QUARANTINED_ARTIFACT_FILENAMES",
    "QUARANTINED_PACKAGE_UUIDS",
    "QUARANTINED_PROJECTION_UUIDS",
    "QUARANTINED_RELEASE_VERSIONS",
    "QUARANTINED_TRANSFORM_SOURCE_HASHES",
    "QuarantinedAuthorityError",
    "quarantined_identities",
    "refuse_quarantined",
]

#: The one 5c release identity published by the quarantined work. Derived by
#: ``bundle.derive_package_uuid(source_hash, transform_hash)``, so the fresh
#: corpus only collides with it if it reuses both the PDF-geometric transform
#: identity and the same source manifest — which the Owner Decision replaces.
QUARANTINED_PACKAGE_UUIDS = frozenset({"4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"})

#: The release version the quarantined corpus published. Content-keyed: any
#: rebuild that reproduces this release reproduces the quarantined product.
QUARANTINED_RELEASE_VERSIONS = frozenset({"5.2.1-corpus.36b786d8-fa2"})

#: The mechanical projection built over that release by the 5d work.
QUARANTINED_PROJECTION_UUIDS = frozenset({"82c75aad-b294-5b2e-a188-128cdcbada09"})

#: The retired transform recipe: ``transform_identity.transform_source_hash``, the
#: frozen digest of the v1 corpus transform's own source manifest. Every corpus
#: the PDF-geometric extraction builds records this value in its transform config
#: whatever embedding model, page subset or output identity it ends up with, so
#: this is the identity of the *obsolete production path* rather than of one of
#: its outputs. The replacement corpus reads a pinned Markdown source through a
#: different transform and therefore records a different hash. The recipe's code
#: has been removed, but stored releases and copies can still carry the hash, so
#: it stays refused here.
QUARANTINED_TRANSFORM_SOURCE_HASHES = frozenset(
    {"6332f201eba9cba19d699a06c6c12580de5ef1c7f349fadacd2045c0e5312cc0"}
)

#: The removed artifacts that stated the retired products, by former
#: repository-relative path and content SHA-256 (both files were deleted under
#: the Owner Decision's Step 5; Git history retains them). Recorded so a reviewer
#: can identify a stray copy exactly; the refusal itself is keyed on identity, not
#: on these digests.
QUARANTINED_ARTIFACT_FILENAMES = (
    "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json",
    "src/afterworlds/ingestion/corpus/srd_table_inventory.json",
)
QUARANTINED_ARTIFACT_DIGESTS = frozenset(
    {
        # accepted 5d authority (nine batches)
        "995976ac1c2b0227d419fc4a7b65a966358e311c7806a1a8f0457a535b4300d7",
        # 5c bundle root hash recorded by that artifact's release binding
        "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685",
        # 5c persisted corpus digest recorded by that artifact's release binding
        "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b",
    }
)

_DECISION = (
    "Owner Decision 2026-09-21 "
    "(docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md)"
)


class QuarantinedAuthorityError(RuntimeError):
    """A quarantined 5c/5d product was offered to an authority seam.

    Not a runtime state a caller can retry or route around: the product no longer
    exists as authority, so the only correct response is to build the replacement.
    """

    def __init__(self, seam: str, matched: tuple[str, ...]) -> None:
        self.seam = seam
        self.matched = matched
        super().__init__(
            f"{seam}: refusing quarantined 5c/5d product "
            f"({', '.join(matched)}) -- quarantined by {_DECISION}"
        )


def _canonical(value: object, label: str) -> str | None:
    """Admit *value* as a comparable identity string, or refuse its type.

    ``str.strip`` is called unbound so a ``str`` subclass cannot supply its own
    normalization and slip past the frozen sets.
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value).lower()
    if isinstance(value, str):
        return str.strip(value).lower()
    raise TypeError(f"{label} must be str, UUID or None, not {type(value).__name__}")


def quarantined_identities(
    *,
    package_uuid: object = None,
    release_version: object = None,
    projection_uuid: object = None,
    transform_source_hash: object = None,
) -> tuple[str, ...]:
    """Return the quarantined identities among the supplied ones, in order.

    Empty means nothing supplied is quarantined. Any non-empty result means the
    caller is holding part of a quarantined product, regardless of which field
    matched: the release, the package, the projection and the transform that
    produced them are one product.
    """
    checks = (
        ("package_uuid", package_uuid, QUARANTINED_PACKAGE_UUIDS),
        ("release_version", release_version, QUARANTINED_RELEASE_VERSIONS),
        ("projection_uuid", projection_uuid, QUARANTINED_PROJECTION_UUIDS),
        (
            "transform_source_hash",
            transform_source_hash,
            QUARANTINED_TRANSFORM_SOURCE_HASHES,
        ),
    )
    matched: list[str] = []
    for label, value, frozen in checks:
        text = _canonical(value, label)
        if text is not None and text in frozen:
            matched.append(f"{label}={text}")
    return tuple(matched)


def refuse_quarantined(
    seam: str,
    *,
    package_uuid: object = None,
    release_version: object = None,
    projection_uuid: object = None,
    transform_source_hash: object = None,
) -> None:
    """Raise :class:`QuarantinedAuthorityError` if any supplied identity is quarantined.

    *seam* names the production entry point doing the refusing, so a failure says
    which path was closed rather than only that something was refused.
    """
    matched = quarantined_identities(
        package_uuid=package_uuid,
        release_version=release_version,
        projection_uuid=projection_uuid,
        transform_source_hash=transform_source_hash,
    )
    if matched:
        raise QuarantinedAuthorityError(seam, matched)
