"""Ledger, concordance, canary, and acyclic-lifecycle tests — Issue 5c.

These exercise the real corpus build (session-scoped ``release`` fixture) and map
to Acceptance #3 (ledger), #5 (concordance), #10 (canaries), #11 (byte-for-byte
regeneration), and the Test Requirements on partition/disjointness, nested
containers, heading coverage, and multi-unit segmentation.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.corpus.bundle import reconciliation_hash
from afterworlds.ingestion.corpus.concordance import check_canaries, check_concordance
from afterworlds.ingestion.corpus.ledger import build_ledger, ledger_hash
from afterworlds.ingestion.corpus.models import Disposition, LeafType
from afterworlds.ingestion.corpus.pipeline import build_candidate
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig

from .conftest import PDF_PATH, finalize_in_fresh_db

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
            # Disjoint + exhaustive: each leaf begins either exactly where the
            # previous one ended (adjacent — sibling TABLE_CELL leaves splitting a
            # single line at column boundaries) or one char later (the "\n" that
            # joins two lines). A skipped char is always that line-boundary "\n".
            assert leaf.char_start in (cursor, cursor + 1)
            if leaf.char_start == cursor + 1:
                assert text[cursor] == "\n"
            assert 0 <= leaf.char_start <= leaf.char_end <= len(text)
            cursor = leaf.char_end
        assert cursor == len(text)


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
    # One fresh regeneration — full candidate build + finalize into a brand-new
    # DB — must reproduce the session build byte-for-byte, including the
    # post-persistence proof hashes (Component K's full acyclic c-g order).
    fresh_candidate = build_candidate(
        PDF_PATH, retrieval_config=RetrievalMemoryConfig()
    )
    result = finalize_in_fresh_db(fresh_candidate)
    assert result.published and result.artifacts is not None, result.gate
    b = result.artifacts
    assert release.release.package_uuid == b.release.package_uuid
    assert release.release.release_version == b.release.release_version
    assert release.release.identity == b.release.identity
    assert reconciliation_hash(release.reconciliation) == reconciliation_hash(
        b.reconciliation
    )


def test_evidence_report_carries_proof_hashes_but_not_its_own(release):
    payload = release.report.dump()
    assert "persisted_corpus_digest" in payload
    assert payload["bundle_root_hash"] == release.release.identity.bundle_root_hash
    # The report never contains its own hash.
    assert release.release.identity.evidence_report_hash not in payload.values()


def test_evidence_report_records_complete_transform_identity(release):
    """PR #134 P1: the report records the full Component B identity — extractor
    config + first-party source manifest/hash + deterministic invocation + IR
    flag — not just ledger.extraction_config."""
    ti = release.report.dump()["transform_identity"]
    assert isinstance(ti, dict)
    assert ti["extractor"]  # extractor config present
    assert ti["source_manifest"]  # first-party source manifest present
    assert len(ti["transform_source_hash"]) == 64
    assert ti["component_b_invocation"]["deterministic"] is True
    assert ti["intermediate_representation_committed"] is False


def _rebuild_report(a, **overrides):
    """Rebuild the evidence report from a release's inputs (R16 F2 host test)."""
    from afterworlds.ingestion.corpus.report import build_report

    kwargs = dict(
        ledger=a.ledger,
        members=a.members,
        recon=a.reconciliation,
        policy=a.policy,
        authoritative_source_hash=a.release.identity.authoritative_source_hash,
        transform_config_hash=a.release.identity.transform_config_hash,
        transform_config=a.release.transform_config,
        bundle_root_hash=a.release.identity.bundle_root_hash,
        ledger_hash_value=ledger_hash(a.ledger),
        persisted_corpus_digest=a.release.identity.persisted_corpus_digest,
        concordance=a.concordance,
        canaries=a.canaries,
    )
    kwargs.update(overrides)
    return build_report(**kwargs)


def test_the_gate_and_persistence_consume_the_canonical_report_directly(release):
    """No indirection between the artifacts and the hashed document.

    ``ReleaseArtifacts.report`` is the canonical value itself, so the gate reads
    its fields and persistence stores its dump without unwrapping anything.
    Asserted on a real finalized release rather than on annotations."""
    from afterworlds.ingestion.corpus.report import EvidenceReport, report_hash
    from afterworlds.ingestion.corpus.report_schema import CorpusEvidenceReport

    assert EvidenceReport is CorpusEvidenceReport
    assert type(release.report) is CorpusEvidenceReport
    assert not hasattr(release.report, "payload")
    assert release.report.prepublication_validation_status == "pass"
    assert report_hash(release.report) == release.release.identity.evidence_report_hash


def test_build_report_returns_the_canonical_value_itself(release):
    """No completed-report wrapper stands between construction and hashing.

    The wrapper this replaces was the hash-bearing authority every consumer
    read, so replacing its ``payload`` after construction replaced the whole
    document. ``build_report`` now returns the structurally immutable value, and
    ``report_hash`` takes that value."""
    from afterworlds.ingestion.corpus.report import report_hash
    from afterworlds.ingestion.corpus.report_schema import CorpusEvidenceReport

    built = _rebuild_report(release)
    assert isinstance(built, CorpusEvidenceReport)
    assert report_hash(built) == release.release.identity.evidence_report_hash


def test_a_report_that_cannot_describe_itself_fails_at_build_time(release):
    """The construction side goes through the one parser too.

    A NamedTuple constructor runs no validators, so `build_report` assembling
    the payload as a plain dict and handing it to `canonical_report` is what
    makes construction a validated path at all. Without it, an incomplete canary
    run would be *written* into a release rather than caught when someone later
    read it back."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _rebuild_report(release, canaries=release.canaries[1:])


def test_evidence_report_identity_is_host_independent(release, monkeypatch):
    """R16 F2: the identity-bearing evidence report is byte-identical for identical
    committed inputs across supported hosts — no runtime host OS/arch/python enters
    the hashed payload (they were operational diagnostics, now logged only). So the
    evidence-report hash (one of the five release identities) does not drift by
    host, and a reuse — which reconstructs from the stored payload — is unaffected."""
    import afterworlds.ingestion.corpus.report as report_mod
    from afterworlds.ingestion.corpus.report import report_hash

    def build_under(system, machine, pyver):
        monkeypatch.setattr(report_mod.platform, "system", lambda: system)
        monkeypatch.setattr(report_mod.platform, "machine", lambda: machine)
        monkeypatch.setattr(report_mod.platform, "python_version", lambda: pyver)
        r = _rebuild_report(release)
        return r.dump(), report_hash(r)

    p1, h1 = build_under("Linux", "x86_64", "3.12.1")
    p2, h2 = build_under("Windows", "AMD64", "3.12.9")
    assert p1 == p2  # byte-identical payload across hosts
    assert h1 == h2  # identical report hash (release identity component)
    # No host/OS/arch/path/time field leaked into the identity-bearing payload.
    blob = repr(p1).lower()
    for banned in (
        "linux",
        "windows",
        "x86_64",
        "amd64",
        "platform_system",
        "platform_machine",
    ):
        assert banned not in blob
    # Only the declared, host-independent reproduction target remains.
    assert p1["reproduction_target"] == {"python_target": "3.12"}
    # The report the release actually published carries this same host-independent
    # hash as its identity component (so reuse, which reads the stored payload, is
    # host-independent too).
    assert release.release.identity.evidence_report_hash == report_hash(release.report)


def test_authoritative_pdf_path_is_the_canonical_spelling():
    assert PDF_PATH.name == "DnD5_5e_SRD_CC_v5_2_1.pdf"
    assert PDF_PATH.exists()


def test_no_derivative_content_counts_as_authoritative(release):
    # Component F: derivative layer is empty; nothing paraphrased is persisted.
    assert release.members.derivative_notes == ()
