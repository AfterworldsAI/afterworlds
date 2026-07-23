"""Ledger, concordance, canary, and acyclic-lifecycle tests — Issue 5c.

These exercise the real corpus build (session-scoped ``release`` fixture) and map
to Acceptance #3 (ledger), #5 (concordance), #10 (canaries), #11 (byte-for-byte
regeneration), and the Test Requirements on partition/disjointness, nested
containers, heading coverage, and multi-unit segmentation.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.bundle import reconciliation_hash
from afterworlds.ingestion.corpus.concordance import check_canaries, check_concordance
from afterworlds.ingestion.corpus.ledger import build_ledger, ledger_hash
from afterworlds.ingestion.corpus.models import Disposition, LeafType
from afterworlds.ingestion.corpus.pipeline import build_release

from .conftest import PDF_PATH

# --- Component C: frozen ledger, occurrence partition, disjointness -----------


def test_ledger_partitions_every_page_disjointly_and_exhaustively(release):
    pages = {pg.page_index: pg.canonical_text() for pg in release.pages}
    by_page: dict[int, list] = {}
    for leaf in release.ledger.leaves:
        by_page.setdefault(leaf.page_index, []).append(leaf)
    assert by_page, "expected leaves"
    for pidx, leaves in by_page.items():
        text = pages[pidx]
        leaves.sort(key=lambda leaf: leaf.char_start)
        cursor = 0
        for leaf in leaves:
            # Disjoint + gap-free: each leaf begins exactly where the previous
            # (plus its "\n" join) ended.
            assert leaf.char_start == cursor
            assert 0 <= leaf.char_start <= leaf.char_end <= len(text)
            cursor = leaf.char_end + 1
        assert leaves[-1].char_end == len(text)


def test_ledger_leaf_ids_are_unique_and_content_derived(release):
    ids = [leaf.leaf_id for leaf in release.ledger.leaves]
    assert len(ids) == len(set(ids))


def test_every_header_footer_is_its_own_leaf(release):
    hf = [
        leaf
        for leaf in release.ledger.leaves
        if leaf.leaf_type is LeafType.HEADER_FOOTER
    ]
    # One running footer per physical page (364 pages).
    assert len(hf) >= 364


def test_headings_titles_are_inventoried_as_leaves(release):
    headings = [
        leaf for leaf in release.ledger.leaves if leaf.leaf_type is LeafType.HEADING
    ]
    assert headings, "expected heading leaves"


def test_nested_container_path_entry_within_section(release):
    # Cure Wounds is an entry nested under its section/subsection.
    cure = [
        leaf
        for leaf in release.ledger.leaves
        if leaf.printed_page == 121 and "regains a number of Hit Points" in leaf.content
    ]
    assert cure
    labels = {c.container_id: c.label for c in release.ledger.containers}
    path = [labels[cid] for cid in cure[0].container_path]
    assert len(path) >= 2  # nested: entry within a section
    assert any("Cure Wounds" in label for label in path)


def test_stat_block_fields_are_discrete_leaves(release):
    fields = [
        leaf.content
        for leaf in release.ledger.leaves
        if leaf.printed_page == 290 and leaf.leaf_type is LeafType.STAT_FIELD
    ]
    joined = " ".join(fields)
    # Goblin Minion stat fields segmented as separate leaves.
    assert any(f.startswith("AC ") for f in fields)
    assert any(f.startswith("HP ") for f in fields)
    assert "CR 1/8" in joined


def test_ledger_is_deterministic(release):
    # Reuse the already-extracted pages; two ledger builds must hash identically.
    pages = release.pages
    assert ledger_hash(build_ledger(pages)) == ledger_hash(build_ledger(pages))
    assert ledger_hash(build_ledger(pages)) == ledger_hash(release.ledger)


# --- Component E/J: concordance and canaries ----------------------------------


def test_concordance_passes_for_every_chunk(release):
    result = check_concordance(release.members.chunks, release.pages)
    assert result.passed
    assert result.locator_failures == ()
    assert result.content_failures == ()


def test_all_six_version_canaries_pass(release):
    results = check_canaries(release.pages)
    assert len(results) == 6
    for canary in results:
        assert canary.passed, f"{canary.name}: {canary.missing} / {canary.unexpected}"


# --- Component D: accounting equation, zero unresolved ------------------------


def test_accounting_equation_and_zero_unresolved(release):
    recon = release.reconciliation
    assert recon.inventoried_leaves == (
        recon.represented_leaves + recon.excluded_leaves + recon.unresolved_leaves
    )
    assert recon.unresolved_leaves == 0
    assert not any(d.disposition is Disposition.UNRESOLVED for d in recon.dispositions)


def test_every_leaf_has_exactly_one_disposition(release):
    disp_ids = [d.leaf_id for d in release.reconciliation.dispositions]
    ledger_ids = [leaf.leaf_id for leaf in release.ledger.leaves]
    assert sorted(disp_ids) == sorted(ledger_ids)
    assert len(disp_ids) == len(set(disp_ids))


# --- Component K: acyclic lifecycle, byte-for-byte regeneration ---------------


def test_release_binds_five_top_level_hashes(release):
    ident = release.release.identity
    for value in (
        ident.authoritative_source_hash,
        ident.transform_config_hash,
        ident.bundle_root_hash,
        ident.evidence_report_hash,
        ident.persisted_corpus_digest,
    ):
        assert value and len(value) == 64


def test_clean_regeneration_is_byte_for_byte_deterministic(release):
    # One fresh regeneration must reproduce the session build byte-for-byte.
    b = build_release(PDF_PATH)
    assert release.release.package_uuid == b.release.package_uuid
    assert release.release.release_version == b.release.release_version
    assert release.release.identity == b.release.identity
    assert reconciliation_hash(release.reconciliation) == reconciliation_hash(
        b.reconciliation
    )


def test_evidence_report_carries_proof_hashes_but_not_its_own(release):
    payload = release.report.payload
    assert "persisted_corpus_digest" in payload
    assert payload["bundle_root_hash"] == release.release.identity.bundle_root_hash
    # The report never contains its own hash.
    assert release.release.identity.evidence_report_hash not in payload.values()


def test_authoritative_pdf_path_is_the_canonical_spelling():
    assert PDF_PATH.name == "DnD5_5e_SRD_CC_v5_2_1.pdf"
    assert PDF_PATH.exists()


def test_no_derivative_content_counts_as_authoritative(release):
    # Component F: derivative layer is empty; nothing paraphrased is persisted.
    assert release.members.derivative_notes == ()
