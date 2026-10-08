"""The source-built candidate and its citation verification — Issue 5c/5d step 3.

Building the real corpus costs about half a minute (the official PDF has to be
extracted), so it is built once per session and every fact about it is asserted
from that one build. The failure cases are the point of this file: each one
takes the real corpus and breaks exactly one thing, because a verification is
only worth its green when a red is reachable.
"""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

import pytest

from afterworlds.ingestion.corpus.concordance import verify_citations
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_REPO_PATH,
    PDF_SHA256,
    extract_pages,
)
from afterworlds.ingestion.corpus.pipeline import (
    CandidateRelease,
    build_source_candidate,
)
from afterworlds.ingestion.corpus.source_ledger import (
    CITATION_VERIFICATION,
    LEAF_PRIMARY_PAGES,
    PAGE_SUBSTRING,
    SOURCE_PARTITION,
    SOURCE_PIN,
    SourceInputError,
    expected_leaf_pages,
    load_pinned_sources,
    pinned_digests,
    source_digest_failures,
    verify_official_pdf,
)
from afterworlds.ingestion.corpus.source_units import CORPUS_FILES
from afterworlds.ingestion.source.community_compare import PIN_DIR
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.quarantine import QUARANTINED_TRANSFORM_SOURCE_HASHES

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def candidate(source_candidate: CandidateRelease) -> CandidateRelease:
    """Shadow the PDF-path ``candidate`` with the source-built one.

    Session-scoped in the package conftest so the lifecycle suite asserts about
    the same build rather than paying for a second one.
    """
    return source_candidate


def _recipe(candidate: CandidateRelease) -> str:
    identity = candidate.transform_config["transform_identity"]
    assert isinstance(identity, dict)
    return str(identity["transform_source_hash"])


# ---------------------------------------------------------------------------
# Refusing the wrong inputs, before anything is parsed
# ---------------------------------------------------------------------------


def test_a_document_that_is_not_the_official_pdf_is_refused(tmp_path: Path) -> None:
    impostor = tmp_path / "not-the-srd.pdf"
    impostor.write_bytes(b"%PDF-1.7 not the official document")
    with pytest.raises(SourceInputError, match="not the official"):
        verify_official_pdf(impostor)
    verify_official_pdf(ROOT / PDF_REPO_PATH)


def test_an_edited_pinned_file_is_refused_before_parsing(tmp_path: Path) -> None:
    """A locally changed snapshot is a different source, not a newer one."""
    shutil.copytree(ROOT / PIN_DIR, tmp_path / PIN_DIR)
    load_pinned_sources(tmp_path)  # the faithful copy loads

    edited = tmp_path / PIN_DIR / "legal-information.md"
    edited.write_text(
        edited.read_text(encoding="utf-8") + "\nLocal note.\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(SourceInputError, match="not the qualified one"):
        load_pinned_sources(tmp_path)


def test_every_corpus_file_including_the_attribution_is_pinned() -> None:
    digests = pinned_digests(ROOT)
    assert set(digests) == set(CORPUS_FILES)
    assert "legal-information.md" in digests


# ---------------------------------------------------------------------------
# What the candidate is
# ---------------------------------------------------------------------------


def test_the_candidate_is_pinned_to_the_official_pdf(
    candidate: CandidateRelease,
) -> None:
    assert candidate.authoritative_source_hash == PDF_SHA256
    assert len(candidate.pages) == 364


def test_the_candidate_declares_the_verification_it_is_qualified_under(
    candidate: CandidateRelease,
) -> None:
    """The gate dispatches on this, and transform_config_hash binds it."""
    assert candidate.transform_config[CITATION_VERIFICATION] == SOURCE_PARTITION
    pin = candidate.transform_config[SOURCE_PIN]
    assert isinstance(pin, dict)
    assert set(dict(pin["files"])) == set(CORPUS_FILES)
    assert (
        source_digest_failures(candidate.source_texts or {}, candidate.transform_config)
        == ()
    )


def test_the_candidate_is_not_the_quarantined_transform(
    candidate: CandidateRelease,
) -> None:
    assert _recipe(candidate) not in QUARANTINED_TRANSFORM_SOURCE_HASHES


def test_the_candidate_names_no_pdf_geometry_oracle(
    candidate: CandidateRelease,
) -> None:
    """The retired path's table oracle grades a reconstruction this never does."""
    assert "expected_table_inventory_hash" not in candidate.transform_config


def test_every_unit_becomes_one_chunk_carrying_its_own_citation(
    candidate: CandidateRelease,
) -> None:
    chunks = candidate.members.chunks
    assert len(chunks) == len(candidate.ledger.leaves)
    assert all(c.source_document == PDF_REPO_PATH for c in chunks)
    assert all(c.source_locator_type == "page" for c in chunks)
    assert all(c.source_locator_value.startswith("p") for c in chunks)
    # A unit printed across a page break cites the range, which a single
    # printed_page cannot express -- which is why the locator is built here and
    # not derived from the page number downstream.
    ranged = [c for c in chunks if c.source_locator_value.startswith("pp. ")]
    assert ranged
    assert all(str(c.printed_page) in c.source_locator_value for c in ranged)


def test_the_recorded_page_claim_is_one_a_persisted_leaf_can_satisfy(
    candidate: CandidateRelease,
) -> None:
    """The reuse check reads one ``printed_page`` per leaf, so this claims that.

    A unit printed across a page break cites both pages but is filed under the
    first, so recording every *cited* page would demand of the leaf table a page
    no leaf is ever filed under -- an unsatisfiable expectation that fails a
    perfectly published release the moment it tries to re-verify itself.
    """
    claimed = expected_leaf_pages(candidate.transform_config)
    assert claimed is not None
    assert 1 in claimed  # the licence page, carried by the attribution file
    assert claimed.isdisjoint({2, 3, 4})  # the table of contents cites nothing
    assert len(claimed) == len(list(candidate.transform_config[LEAF_PRIMARY_PAGES]))
    assert claimed == {leaf.printed_page for leaf in candidate.ledger.leaves}
    # Strictly narrower than the full citation, and knowingly so: the
    # continuation pages are cited by the locators and proven by the
    # re-derivation, not by this coarse backstop.
    report = candidate.citation_report
    assert report is not None
    assert set(report.cited_pages) >= claimed
    assert report.multi_page_units > 0


def test_the_same_inputs_mint_the_same_release(candidate: CandidateRelease) -> None:
    again = build_source_candidate(ROOT, retrieval_config=RetrievalMemoryConfig())
    assert again.package_uuid == candidate.package_uuid
    assert again.release_version == candidate.release_version
    assert again.bundle.bundle_root_hash == candidate.bundle.bundle_root_hash
    assert again.ledger_hash == candidate.ledger_hash


# ---------------------------------------------------------------------------
# Citation verification: the green, and every red it can reach
# ---------------------------------------------------------------------------


def _verify(candidate: CandidateRelease, chunks=None, sources=None, config=None):
    return verify_citations(
        candidate.members.chunks if chunks is None else chunks,
        candidate.pages,
        candidate.transform_config if config is None else config,
        source_texts=candidate.source_texts if sources is None else sources,
    )


def test_the_persisted_corpus_re_derives_from_the_pinned_bytes(
    candidate: CandidateRelease,
) -> None:
    result = _verify(candidate)
    assert result.passed
    assert result.chunks_checked == len(candidate.members.chunks)
    assert result.content_failures == () and result.omissions == ()


def test_a_corrupted_chunk_is_detected(candidate: CandidateRelease) -> None:
    chunks = list(candidate.members.chunks)
    chunks[500] = dataclasses.replace(chunks[500], content="tampered text")
    result = _verify(candidate, chunks=tuple(chunks))
    assert not result.passed
    assert result.content_failures == (chunks[500].chunk_id,)
    # The original unit is now carried by nothing, and the report says so
    # rather than reporting only the chunk that changed.
    assert len(result.omissions) == 1


def test_an_omitted_chunk_is_detected(candidate: CandidateRelease) -> None:
    """A chunk-by-chunk check alone cannot see this: the chunk is simply gone."""
    chunks = tuple(c for i, c in enumerate(candidate.members.chunks) if i != 900)
    result = _verify(candidate, chunks=chunks)
    assert not result.passed
    assert result.content_failures == ()
    assert len(result.omissions) == 1


def test_a_reassigned_locator_is_detected(candidate: CandidateRelease) -> None:
    chunks = list(candidate.members.chunks)
    chunks[1200] = dataclasses.replace(chunks[1200], source_locator_value="p. 999")
    result = _verify(candidate, chunks=tuple(chunks))
    assert not result.passed
    assert result.content_failures == (chunks[1200].chunk_id,)


def test_a_duplicated_chunk_is_detected(candidate: CandidateRelease) -> None:
    chunks = candidate.members.chunks + (candidate.members.chunks[7],)
    result = _verify(candidate, chunks=chunks)
    assert not result.passed
    assert len(result.content_failures) == 1


def test_verification_without_the_pinned_source_fails_rather_than_passes(
    candidate: CandidateRelease,
) -> None:
    """A check that could not run has not run, and must not read as a pass."""
    result = _verify(candidate, sources={})
    assert not result.passed
    result = verify_citations(
        candidate.members.chunks,
        candidate.pages,
        candidate.transform_config,
        source_texts=None,
    )
    assert not result.passed
    assert "without the pinned sources" in result.omissions[0]


def test_a_source_that_does_not_match_the_release_digests_is_refused(
    candidate: CandidateRelease,
) -> None:
    sources = dict(candidate.source_texts or {})
    sources["legal-information.md"] += "\nnot the pinned bytes\n"
    result = _verify(candidate, sources=sources)
    assert not result.passed
    assert any("does not match its digest" in o for o in result.omissions)


def test_a_release_declaring_nothing_gets_the_retired_substring_check(
    candidate: CandidateRelease,
) -> None:
    """Existing releases keep their own verification; nothing is grandfathered."""
    config = {k: v for k, v in candidate.transform_config.items()}
    del config[CITATION_VERIFICATION]
    result = _verify(candidate, config=config)
    # Markdown chunks cannot satisfy the PDF substring predicate -- which is
    # exactly why this path declares a different one rather than weakening it.
    assert not result.passed
    assert result.content_failures


def test_an_unknown_verification_mode_fails_rather_than_falling_back(
    candidate: CandidateRelease,
) -> None:
    config = dict(candidate.transform_config)
    config[CITATION_VERIFICATION] = "something-else"
    result = _verify(candidate, config=config)
    assert not result.passed
    assert "unknown citation verification mode" in result.omissions[0]


def test_the_substring_mode_still_works_for_a_pdf_built_release() -> None:
    """The retired predicate is dispatched to, not left dead, for old releases."""
    from afterworlds.ingestion.corpus.concordance import compact
    from afterworlds.ingestion.corpus.models import CorpusChunk

    pages = extract_pages(ROOT / PDF_REPO_PATH)[6:7]
    text = pages[0].canonical_text()
    excerpt = text[:60]
    chunk = CorpusChunk(
        chunk_id="c1",
        subsystem="general",
        content=excerpt,
        printed_page=pages[0].printed_page,
        section_label=None,
        container_path=(),
        source_leaf_ids=("l1",),
    )
    assert compact(excerpt) in compact(text)
    assert verify_citations(
        (chunk,), pages, {CITATION_VERIFICATION: PAGE_SUBSTRING}
    ).passed
    assert verify_citations((chunk,), pages, {}).passed
    off_page = dataclasses.replace(chunk, printed_page=999)
    assert not verify_citations((off_page,), pages, {}).passed
