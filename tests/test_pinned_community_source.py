"""The pinned community source snapshot is the bytes its manifest claims.

Step 2 of the Recorded Owner Decision of 21 September 2026 establishes one
Afterworlds-controlled copy of ``downfallx/dnd-5e-srd-markdown`` so that later
corrections are reviewable diffs against a known baseline. That only holds if
the baseline cannot drift: an edit to a vendored file, a file removed, or a file
added must fail here rather than become an unrecorded change to a pinned source.

Corrections are expected — the snapshot is provisional until its final
boundary has been reviewed independently. A correction updates the manifest in
the same commit as the file, which is exactly the reviewable event this test
forces into existence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

PIN_DIR = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "sources"
    / "community"
    / "dnd-5e-srd-markdown"
)
MANIFEST_PATH = PIN_DIR / "source_pin.json"

#: Files this directory holds that describe the pin rather than being pinned
#: content. They are Afterworlds documents, not upstream bytes.
OUR_OWN = {"source_pin.json", "PINNED-SOURCE.md"}

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
VENDORED = [f for f in MANIFEST["files"] if f["vendored"]]
ADDITIONS = MANIFEST["controlled_additions"]
OFFICIAL_PAGES = MANIFEST["official_source"]["pages"]


def test_the_manifest_pins_an_exact_upstream_commit() -> None:
    """A moving reference is not a pin."""
    assert MANIFEST["upstream_commit"] == "1b4b99dcb786cdd1a2fb26f8acec1551191f1ca4"
    assert len(MANIFEST["upstream_commit"]) == 40
    assert MANIFEST["upstream_repository"] == (
        "https://github.com/downfallx/dnd-5e-srd-markdown"
    )
    # Corrected against the official PDF and reviewed independently at the head
    # the review names, which is what the manifest records. What it must never
    # say is that a later consumer reading these bytes is what qualifies them,
    # or that qualification of the bytes settles what the rules mean.
    assert MANIFEST["status"] == "qualified"
    review = MANIFEST["qualification_review"]
    assert review["reviewed_head"] == "b70d016"
    assert review["artifact"] == "source-structure-final-review.md"
    assert "semantic acceptance" in review["not_established"]


def test_the_manifest_records_the_whole_upstream_commit() -> None:
    """Every upstream tracked file is accounted for, vendored or not.

    A manifest listing only what was copied cannot distinguish "upstream has no
    such file" from "we chose not to copy it", so each exclusion states a
    reason.
    """
    assert MANIFEST["upstream_tracked_files"] == len(MANIFEST["files"]) == 21
    assert MANIFEST["vendored_files"] == len(VENDORED) == 16
    for entry in MANIFEST["files"]:
        assert len(entry["sha256"]) == len(entry["upstream_sha256"]) == 64
        assert entry["bytes"] > 0 and entry["upstream_bytes"] > 0
        assert entry["role"] in {"content", "license", "upstream-process"}
        if not entry["vendored"]:
            assert entry["excluded_because"].strip()
    assert MANIFEST["vendored_bytes"] == sum(f["upstream_bytes"] for f in VENDORED)
    assert MANIFEST["controlled_vendored_bytes"] == sum(f["bytes"] for f in VENDORED)


@pytest.mark.parametrize("entry", VENDORED, ids=lambda e: e["path"])
def test_a_vendored_file_is_byte_identical_to_its_manifest_entry(
    entry: dict[str, object],
) -> None:
    data = (PIN_DIR / str(entry["path"])).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]


@pytest.mark.parametrize("entry", VENDORED, ids=lambda e: e["path"])
def test_a_file_differs_from_upstream_only_where_a_correction_says_so(
    entry: dict[str, object],
) -> None:
    """Correction must not mean silently overwriting the expected upstream digest.

    ``upstream_sha256`` is the immutable baseline; ``sha256`` is what this
    repository controls. Letting them drift apart with no recorded correction is
    the failure this guards: the diff would still be reviewable in git, but the
    manifest would have stopped saying that the snapshot had been changed at
    all, and the next reader would take corrected bytes for upstream bytes.
    """
    corrections = entry["corrections"]
    assert isinstance(corrections, list)
    changed = entry["sha256"] != entry["upstream_sha256"]
    assert changed == bool(corrections), (
        f"{entry['path']}: {'changed bytes' if changed else 'upstream bytes'} "
        f"with {len(corrections)} correction(s) recorded"
    )
    for correction in corrections:
        pages = correction["official_pages"]
        assert pages and all(1 <= p <= OFFICIAL_PAGES for p in pages)
        assert correction["section"].strip()
        assert correction["change"].strip()
        assert correction["why"].strip()


def test_every_correction_is_counted_where_a_reader_looks_first() -> None:
    """A per-file list nobody totals is a list nobody reads."""
    assert MANIFEST["corrections_applied"] == sum(
        len(f["corrections"]) for f in MANIFEST["files"]
    )


@pytest.mark.parametrize("entry", ADDITIONS, ids=lambda e: e["path"])
def test_a_controlled_addition_is_the_bytes_its_entry_claims(
    entry: dict[str, object],
) -> None:
    """Content held here that upstream never had is still pinned content.

    The snapshot omits the official Legal Information page, and CC-BY-4.0
    requires the attribution to travel with the work, so the page is added under
    Afterworlds control. Added under control still means pinned: it carries no
    ``upstream_sha256`` because there is no upstream blob to name, and the pages
    of the official document it comes from are recorded instead.
    """
    data = (PIN_DIR / str(entry["path"])).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    assert b"\r\n" not in data
    assert "upstream_sha256" not in entry
    pages = entry["official_pages"]
    assert pages and all(1 <= p <= OFFICIAL_PAGES for p in pages)
    assert entry["why"].strip()


@pytest.mark.parametrize("entry", VENDORED, ids=lambda e: e["path"])
def test_a_vendored_file_carries_the_upstream_line_endings(
    entry: dict[str, object],
) -> None:
    """The digests are of upstream Git blobs, so no checkout may rewrite them.

    Vendoring from a working copy with ``core.autocrlf=true`` produces CRLF
    files whose digests verify on that one platform and nowhere else. The pin
    directory is marked ``-text`` in ``.gitattributes`` to prevent that; this
    asserts the outcome rather than trusting the configuration, because a pin
    that only holds on the machine that wrote it is not a pin.
    """
    assert b"\r\n" not in (PIN_DIR / str(entry["path"])).read_bytes()


def test_the_manifest_states_what_its_digests_are_of() -> None:
    """A bare checksum does not say which rendering of the file it covers."""
    assert "Git blob" in MANIFEST["digest_basis"]
    assert "-text" in MANIFEST["digest_basis"]


def test_the_directory_holds_nothing_the_manifest_does_not_name() -> None:
    """An unlisted file in a pinned source directory is unpinned content."""
    present = {
        str(p.relative_to(PIN_DIR)).replace("\\", "/")
        for p in PIN_DIR.rglob("*")
        if p.is_file()
    }
    named = {str(f["path"]) for f in VENDORED} | {str(a["path"]) for a in ADDITIONS}
    assert present - OUR_OWN == named


def test_the_official_pdf_is_still_the_source_authority() -> None:
    """The manifest names the PDF it is provisional against, and that PDF is it.

    A different checksum here is a discrepancy to resolve, never a number to
    update: the whole point of recording it is that the pinned Markdown is
    checked against *this* document.
    """
    official = MANIFEST["official_source"]
    pdf = Path(__file__).resolve().parents[1] / official["path"]
    data = pdf.read_bytes()
    assert len(data) == official["bytes"]
    assert hashlib.sha256(data).hexdigest() == official["sha256"]
