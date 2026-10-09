"""Canonical corpus transform — CRD Issue 5c, Component K step a2 / Component F.

Generates the canonical corpus members (authoritative ``CorpusChunk`` records,
mapping 1:1 to unextended Issue 5a ``RuleChunk`` rows) **from the frozen source
ledger**. Because each chunk is derived from exactly one represented leaf and
covers that leaf's full span, declared-projection coverage is gap-free by
construction — the reconciler (D) then verifies this independently.

Layer separation (Component F): only deterministic structural transformation of
official source text enters the authoritative corpus. Any rewrite/annotation
would belong to a separate non-authoritative derivative layer; this transform
emits none, so the derivative layer is empty and never counts toward
publication.

A leaf the frozen policy excludes (running header/footer, TOC/index listing) is
not emitted as a chunk — the reconciler assigns it the excluded disposition
using the same shared predicate, so transform and reconciliation never disagree.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.ingestion.corpus.models import (
    CorpusBundleMembers,
    CorpusChunk,
    Leaf,
    SourceLedger,
)
from afterworlds.ingestion.corpus.policy import exclusion_reason_for

# Deterministic subsystem tagging from the leaf's container path (informational;
# subsystem does not carry mechanical authority — Decision 2/4).
_SUBSYSTEM_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("spell", "spells"),
    ("condition", "conditions"),
    ("glossary", "conditions"),
    ("equipment", "items"),
    ("item", "items"),
    ("class", "classes"),
    ("species", "races"),
    ("lineage", "races"),
    ("monster", "combat"),
    ("stat block", "combat"),
    ("combat", "combat"),
    ("attack", "combat"),
    ("movement", "movement"),
)


def _subsystem_for(leaf: Leaf, container_labels: dict[str, str]) -> str:
    path = " ".join(
        container_labels.get(cid, "").casefold() for cid in leaf.container_path
    )
    for keyword, subsystem in _SUBSYSTEM_KEYWORDS:
        if keyword in path:
            return subsystem
    return "general"


def section_label_for(leaf: Leaf, container_labels: dict[str, str]) -> str | None:
    """The whole heading stack that owns a leaf, not just its nearest heading.

    Hundreds of records repeat the same innermost heading (every creature has
    an ``Actions``), so the nearest label alone does not tell a consumer which
    record a chunk came from. The verification that re-derives the corpus calls
    this same function, so the persisted label and the expected one cannot
    drift apart.
    """
    labels = [
        label
        for cid in leaf.container_path
        if (label := container_labels.get(cid, "").strip())
    ]
    return " > ".join(labels) if labels else None


def build_corpus(
    ledger: SourceLedger,
    package_uuid: str,
    *,
    locators: dict[str, tuple[str, str, str]] | None = None,
) -> CorpusBundleMembers:
    """Generate canonical corpus members from the frozen ledger (K a2).

    One authoritative chunk per represented leaf, covering the leaf's full span.
    Policy-excluded leaves are skipped. The derivative layer is empty.

    The output ``chunk_id`` is a deterministic function of the immutable
    ``package_uuid`` **and** the source ``leaf_id`` — so two releases differing
    only in an identity-bearing input (source, transform config, transform-source
    manifest, or embedding model) mint distinct chunk IDs and coexist in the
    global ``rp_chunks`` primary key instead of colliding (PR #134 P1). The
    source-side ``leaf_id`` stays release-independent (it is the provenance
    identity later work consumes); only the *output* chunk identity is
    release-scoped. ``package_uuid`` is computed before a2 and passed in
    explicitly — there is no package-less default.
    """
    # ``locators`` maps a leaf id to the (document, locator_type, locator_value)
    # the chunk should carry. The PDF-geometric path passes none and persistence
    # derives ``p. N`` from the leaf's page; the source path knows the whole
    # citation at build time -- including the multi-page ``pp. N-M`` form a
    # single page number cannot express -- and supplies it here. Either way the
    # locator stays out of ``corpus_members_payload``, so the bundle root hash is
    # unchanged and the locator is bound by the persisted-corpus digest alone.
    container_labels = {c.container_id: c.label for c in ledger.containers}
    chunks: list[CorpusChunk] = []
    for leaf in ledger.leaves:
        if exclusion_reason_for(leaf, container_labels) is not None:
            continue
        chunk_id = content_id("chunk", package_uuid, leaf.leaf_id)
        document, locator_type, locator_value = (locators or {}).get(
            leaf.leaf_id, ("", "", "")
        )
        chunks.append(
            CorpusChunk(
                chunk_id=chunk_id,
                subsystem=_subsystem_for(leaf, container_labels),
                content=leaf.content,
                printed_page=leaf.printed_page,
                section_label=section_label_for(leaf, container_labels),
                container_path=leaf.container_path,
                source_leaf_ids=(leaf.leaf_id,),
                source_document=document,
                source_locator_type=locator_type,
                source_locator_value=locator_value,
            )
        )
    return CorpusBundleMembers(chunks=tuple(chunks), derivative_notes=())
