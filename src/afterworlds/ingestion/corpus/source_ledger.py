"""The fresh 5c source ledger, built from the qualified snapshot — Issue 5c/5d.

The retired path derived leaves from PDF geometry and then proved each chunk's
text appeared on its page. This path inverts that: structure comes from the
qualified Markdown/HTML snapshot, which already carries headings, list and table
boundaries and record ownership, and the official PDF is used only as the
**citation target** — the page every unit is mapped to, and the
``authoritative_source_hash`` the release is pinned to. No PDF geometry is
reconstructed downstream.

Two refusals stand in front of every build, before a single character is parsed:

* the official PDF must hash to :data:`PDF_SHA256` (wrong source);
* every pinned file must hash to the digest ``source_pin.json`` records for it
  (stale or locally edited input).

What the release binds
----------------------
``transform_config`` records the pin digests, the citation mode, and the exact
set of official pages the corpus cites. Gate condition 2 already tamper-checks
``transform_config`` against ``transform_config_hash``, so all three are
digest-bound: a release cannot claim ``source_partition`` verification, or a
different pinned byte, without minting a different package.

``citation_verification`` is what the gate dispatches on. The retired
``page_substring`` predicate — "this chunk's compacted text occurs on its page"
— cannot hold for Markdown chunks, whose markup never appears in the PDF's text
layer. Rather than weaken the check for everyone, a release declares which
verification it is qualified under, and
:func:`concordance.verify_citations` runs that one. A release that declares
nothing still gets the substring check.

What ``source_partition`` verification actually proves
-----------------------------------------------------
It re-derives the whole corpus from the digest-verified pinned bytes and the
freshly extracted PDF pages, and requires a **bijection**: every re-derived unit
has exactly one persisted chunk with the same text, the same section label and
the same page locator, and every persisted chunk matches exactly one unit. That
detects corruption, omission, duplication and locator reassignment in the
persisted state. It does not re-establish that the snapshot says what the PDF
says — that is the source qualification's result, carried by the pin digests and
by the version canaries, which read the real PDF.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from afterworlds.ingestion.corpus.hashing import hash_obj, sha256_hex
from afterworlds.ingestion.corpus.models import (
    CorpusChunk,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_REPO_PATH,
    PDF_SHA256,
    SOURCE_DOCUMENT,
    SOURCE_VERSION,
    ExtractedPage,
)
from afterworlds.ingestion.corpus.policy import (
    compact,
    exclusion_reason_for,
    policy_payload,
)
from afterworlds.ingestion.corpus.source_citations import (
    CitationReport,
    UnitCitation,
    build_report,
    cite_units,
    page_locator,
)
from afterworlds.ingestion.corpus.source_units import (
    CORPUS_FILES,
    build_leaves,
    build_structure,
    resolve_container_pages,
)
from afterworlds.ingestion.corpus.transform import section_label_for
from afterworlds.ingestion.source.community_compare import PIN_DIR, WINDOW

#: ``transform_config`` key naming the citation verification a release is
#: qualified under. Absent means the retired per-page substring predicate.
CITATION_VERIFICATION = "citation_verification"
#: Retired mode: every chunk's compacted text occurs in its page's text.
PAGE_SUBSTRING = "page_substring"
#: This path's mode: the corpus re-derives from the pinned bytes, bijectively.
SOURCE_PARTITION = "source_partition"
#: ``transform_config`` key carrying the pinned snapshot identity + digests.
SOURCE_PIN = "source_pin"
#: ``transform_config`` key carrying the official pages the ledger files a
#: leaf under. Deliberately the *primary* page of each unit, not every page
#: a unit cites: a unit printed across a break cites both pages but is filed
#: under the first, so a persisted ``printed_page`` column can never show the
#: continuation page, and claiming it would be claiming something no reader
#: of that column could ever satisfy. The full multi-page citation lives in
#: the chunk locator and is proven by the source-partition re-derivation.
LEAF_PRIMARY_PAGES = "leaf_primary_pages"

SOURCE_TRANSFORM_TOOL = "afterworlds-srd-source-corpus-transform"
#: Bump deliberately for a meaningful logical-corpus or compatibility change.
#:
#: Version 2: every chunk's ``section_label`` became the whole heading stack
#: rather than the nearest heading, and every leaf's ``occurrence_index`` became
#: the global emission order the reconstruction actually reads it under. Neither
#: field is an input to ``transform_config``, so without this bump the changed
#: corpus would mint the *same* ``package_uuid`` and ``release_version`` as the
#: output it replaces -- which is precisely the collision the version exists to
#: prevent. Same inputs still mean the same release; a changed recipe now means
#: a new one.
#:
#: Version 3: a table's trailing footnote joined the table's own unit (the note
#: defining a starred value is useless served apart from the values), and the
#: vector layer began embedding bounded derived windows of a chunk rather than
#: its whole text, because the embedding function truncates its own input at 256
#: tokens. Both change the published logical state, and the second changes the
#: persisted-corpus digest as well.
#:
#: Version 4: a unit is cited by its own whole wording in the official page
#: stream before the partition's position labels, so a window straddling a unit
#: boundary no longer lends a unit its neighbour's page. Citations change for
#: units whose pages the partition got wrong; the pinned bytes do not show it.
SOURCE_TRANSFORM_VERSION = "4"

_PIN_MANIFEST = "source_pin.json"


class SourceInputError(RuntimeError):
    """A build input is not the qualified one: wrong PDF, or a moved pin."""


# ---------------------------------------------------------------------------
# Pinned inputs and their refusals
# ---------------------------------------------------------------------------


def pinned_digests(root: Path) -> dict[str, str]:
    """The committed sha256 of each corpus file, from the pin manifest."""
    manifest = json.loads((root / PIN_DIR / _PIN_MANIFEST).read_text(encoding="utf-8"))
    # legal-information.md is a controlled addition, not an upstream file, so
    # the manifest records it in its own list; both are pinned bytes and both
    # are read the same way here.
    recorded = {
        str(entry["path"]): str(entry["sha256"])
        for entry in list(manifest["files"]) + list(manifest["controlled_additions"])
    }
    missing = [name for name in CORPUS_FILES if name not in recorded]
    if missing:
        raise SourceInputError(f"pin manifest does not record {missing}")
    return {name: recorded[name] for name in CORPUS_FILES}


def load_pinned_sources(root: Path) -> dict[str, str]:
    """Read the pinned corpus files, refusing anything the manifest disowns.

    This is the stale-input refusal, and it runs before parsing: an edited,
    truncated or re-pointed snapshot file never reaches the structure builder.
    """
    digests = pinned_digests(root)
    sources: dict[str, str] = {}
    for name in CORPUS_FILES:
        path = root / PIN_DIR / name
        raw = path.read_bytes()
        actual = sha256_hex(raw)
        if actual != digests[name]:
            raise SourceInputError(
                f"pinned source {name} hashes {actual}, manifest records "
                f"{digests[name]} — the snapshot is not the qualified one"
            )
        sources[name] = raw.decode("utf-8")
    return sources


def verify_official_pdf(pdf_path: Path) -> None:
    """Refuse a PDF that is not the official one the citations point at."""
    actual = sha256_hex(pdf_path.read_bytes())
    if actual != PDF_SHA256:
        raise SourceInputError(
            f"{pdf_path} hashes {actual}, not the official {PDF_SHA256}"
        )


def source_digest_failures(
    sources: dict[str, str], transform_config: dict[str, object]
) -> tuple[str, ...]:
    """Check supplied source texts against the digests the release recorded."""
    pin = transform_config.get(SOURCE_PIN)
    if not isinstance(pin, dict) or not isinstance(pin.get("files"), dict):
        return ("release records no pinned source digests",)
    recorded: dict[str, str] = {str(k): str(v) for k, v in dict(pin["files"]).items()}
    failures: list[str] = []
    for name, digest in sorted(recorded.items()):
        text = sources.get(name)
        if text is None:
            failures.append(f"pinned source {name} not supplied")
        elif sha256_hex(text.encode("utf-8")) != digest:
            failures.append(f"pinned source {name} does not match its digest")
    for extra in sorted(set(sources) - set(recorded)):
        failures.append(f"source {extra} is not part of the pinned release")
    return tuple(failures)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


def source_extraction_config(sources: dict[str, str]) -> dict[str, object]:
    """The source-side identity of this front end (Component B/C).

    Markdown-native: the snapshot it read, the exact bytes, and the citation
    instrument. It names no PDF geometry because none is used to build units.
    """
    return {
        "tool": SOURCE_TRANSFORM_TOOL,
        "tool_version": SOURCE_TRANSFORM_VERSION,
        "snapshot_directory": PIN_DIR,
        "files": [
            {"path": name, "sha256": sha256_hex(sources[name].encode("utf-8"))}
            for name in CORPUS_FILES
        ],
        "unit_boundaries": (
            "blank-line separated blocks; a caption above a table and a "
            "footnote below it merge into that table; a bullet run and a "
            "stat-field run are each one unit"
        ),
        "citation_instrument": (
            "the unit's whole text in the official page stream, bounded by "
            "community_tokens.partition anchors kept in document order, "
            f"window {WINDOW}; the partition's pages where the text cannot "
            "place the unit"
        ),
        "official_citation_target": {"path": PDF_REPO_PATH, "sha256": PDF_SHA256},
    }


def source_transform_identity(
    extraction_config: dict[str, object],
) -> dict[str, object]:
    """Declared semantic identity of the Markdown-native transform.

    ``transform_source_hash`` aggregates the pinned source bytes and this tool's
    declared version rather than implementation-file bytes, so an incidental code
    edit does not remint an unchanged corpus while a changed snapshot does. It is
    also what the quarantine refusal matches on, and it is by construction not
    the retired PDF-geometric recipe's hash.
    """
    return {
        "tool": SOURCE_TRANSFORM_TOOL,
        "tool_version": SOURCE_TRANSFORM_VERSION,
        "transform_source_hash": hash_obj(
            {
                "tool": SOURCE_TRANSFORM_TOOL,
                "tool_version": SOURCE_TRANSFORM_VERSION,
                "files": extraction_config["files"],
            }
        ),
        "component_b_invocation": {
            "entrypoint": (
                "afterworlds.ingestion.corpus.pipeline.build_source_candidate"
            ),
            "steps": (
                "a0:freeze_policy",
                "a1:parse_pinned_source+cite_official_pages",
                "a2:build_corpus",
                "a3:reconcile",
                "b:bundle_root",
            ),
            "deterministic": True,
        },
        "intermediate_representation_committed": False,
    }


def source_transform_config_payload(
    extraction_config: dict[str, object],
    policy: ReconciliationPolicy,
    vector_identity: dict[str, object],
    *,
    primary_pages: tuple[int, ...],
) -> dict[str, object]:
    """The committed transform inputs for a source-built release.

    Deliberately omits the retired path's expected-table-inventory hash and its
    v1 evidence-report identity key: neither describes this transform, and
    carrying them solely for compatibility would misreport what produced the
    corpus.
    """
    return {
        "extraction_config": extraction_config,
        "reconciliation_policy": policy_payload(policy),
        "transform_identity": source_transform_identity(extraction_config),
        "rules_corpus_vector_identity": vector_identity,
        CITATION_VERIFICATION: SOURCE_PARTITION,
        SOURCE_PIN: {
            "directory": PIN_DIR,
            "files": {
                str(entry["path"]): str(entry["sha256"])
                for entry in list(extraction_config["files"])  # type: ignore[call-overload]
            },
        },
        LEAF_PRIMARY_PAGES: list(primary_pages),
    }


def expected_leaf_pages(transform_config: dict[str, object]) -> frozenset[int] | None:
    """The official pages a source-built release files a leaf under, if it says.

    ``None`` for a release that does not record them, which is every release
    built by the retired PDF-geometric path.
    """
    raw = transform_config.get(LEAF_PRIMARY_PAGES)
    if not isinstance(raw, list):
        return None
    return frozenset(int(p) for p in raw)


def build_source_ledger(
    sources: dict[str, str], pages: list[ExtractedPage]
) -> tuple[SourceLedger, tuple[UnitCitation, ...], CitationReport]:
    """Parse the pinned snapshot into a cited ledger, or refuse.

    Refuses when the units do not tile their file (``SourceTilingError``, raised
    by :func:`build_structure`) or when any unit or body page went uncited: an
    incomplete corpus is never returned as a complete one.
    """
    structure = build_structure(sources)
    citations = cite_units(structure, sources, pages)
    report = build_report(citations, tuple(p.printed_page for p in pages))
    if not report.resolved:
        raise SourceInputError(
            f"citation did not resolve: {len(report.unresolved)} unresolved "
            f"units, {len(report.uncited_body_pages)} uncited body pages"
        )
    cited = {c.unit_index: c.pages for c in citations}
    ledger = SourceLedger(
        source_document=SOURCE_DOCUMENT,
        source_version=SOURCE_VERSION,
        source_sha256=PDF_SHA256,
        extraction_config=source_extraction_config(sources),
        containers=resolve_container_pages(structure, cited),
        leaves=build_leaves(structure, cited),
    )
    return ledger, citations, report


def chunk_locators(
    ledger: SourceLedger, citations: tuple[UnitCitation, ...]
) -> dict[str, tuple[str, str, str]]:
    """Per-leaf ``(document, locator_type, locator_value)`` for the transform.

    Leaves are emitted in unit order, so a leaf and its citation share an index.
    One formatter (:func:`page_locator`) produces the value here, in the report
    and in the re-derivation, so a multi-page unit cannot be persisted as a
    single-page citation.
    """
    return {
        leaf.leaf_id: (PDF_REPO_PATH, "page", citation.locator_value)
        for leaf, citation in zip(ledger.leaves, citations, strict=True)
    }


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def _chunk_key(chunk: CorpusChunk) -> tuple[str, str, str]:
    return (
        compact(chunk.content),
        chunk.section_label or "",
        chunk.source_locator_value or page_locator((chunk.printed_page,)),
    )


def verify_source_partition(
    chunks: tuple[CorpusChunk, ...],
    pages: list[ExtractedPage],
    transform_config: dict[str, object],
    source_texts: dict[str, str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Re-derive the corpus from the pinned bytes and require a bijection.

    Returns ``(content_failures, omissions)``: chunk ids that no re-derived unit
    accounts for, and re-derived units that no chunk carries. Plain tuples, so
    this module stays independent of the concordance result type that wraps it.

    Missing source texts are a **failure**, never a pass: a verification that
    cannot run has not run.

    Deliberately order-blind: it compares multisets, so it proves every unit is
    carried exactly once with its section and locator intact, and proves nothing
    about the *order* the chunks are stored in. Order is bound by
    ``bundle_root_hash`` and restored on reconstruction by sorting on
    ``Leaf.occurrence_index``; a reordering that left the multiset unchanged
    would pass here and fail there, which is where it should fail.
    """
    if source_texts is None:
        return (
            (),
            ("source_partition verification ran without the pinned sources",),
        )
    digest_failures = source_digest_failures(source_texts, transform_config)
    if digest_failures:
        return ((), digest_failures)

    ledger, citations, _report = build_source_ledger(source_texts, pages)
    labels = {c.container_id: c.label for c in ledger.containers}
    locators = chunk_locators(ledger, citations)
    expected: Counter[tuple[str, str, str]] = Counter()
    for leaf in ledger.leaves:
        if exclusion_reason_for(leaf, labels) is not None:
            continue
        section = section_label_for(leaf, labels) or ""
        expected[(compact(leaf.content), section, locators[leaf.leaf_id][2])] += 1

    actual: Counter[tuple[str, str, str]] = Counter(_chunk_key(c) for c in chunks)
    excess = actual - expected
    content_failures: list[str] = []
    for chunk in chunks:
        key = _chunk_key(chunk)
        if excess[key] > 0:
            excess[key] -= 1
            content_failures.append(chunk.chunk_id)
    omissions = tuple(
        f"{section or '(no section)'} {locator}: {text[:60]}"
        for (text, section, locator), count in sorted((expected - actual).items())
        for _ in range(count)
    )
    return tuple(content_failures), omissions


__all__ = [
    "CITATION_VERIFICATION",
    "LEAF_PRIMARY_PAGES",
    "PAGE_SUBSTRING",
    "SOURCE_PARTITION",
    "SOURCE_PIN",
    "SourceInputError",
    "build_source_ledger",
    "chunk_locators",
    "expected_leaf_pages",
    "load_pinned_sources",
    "pinned_digests",
    "source_digest_failures",
    "source_extraction_config",
    "source_transform_config_payload",
    "source_transform_identity",
    "verify_official_pdf",
    "verify_source_partition",
]
