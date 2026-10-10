"""Release-level invariants on the published source corpus — Issue 5c.

Acceptance #10 (version canaries), the reconciliation accounting equation, the
five top-level release hashes and the evidence report's proof hashes, asserted on
the session-scoped source release. The PDF-geometric ledger assertions this
module used to carry (page partition, header/footer and stat-field leaves,
substring concordance, byte-for-byte rebuild through ``build_candidate``) graded
the retired corpus and were removed with it.
"""

from __future__ import annotations

import platform

import pytest

from afterworlds.ingestion.corpus.concordance import check_canaries
from afterworlds.ingestion.corpus.ledger import ledger_hash
from afterworlds.ingestion.corpus.models import Disposition
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.ingestion.corpus.report import (
    EvidenceReport,
    build_report,
    report_hash,
)

from .conftest import PDF_PATH


def test_all_six_version_canaries_pass(release: ReleaseArtifacts) -> None:
    results = check_canaries(release.pages)
    assert len(results) == 6
    for canary in results:
        assert canary.passed, f"{canary.name}: {canary.missing} / {canary.unexpected}"


def test_accounting_equation_and_zero_unresolved(release: ReleaseArtifacts) -> None:
    recon = release.reconciliation
    assert recon.inventoried_leaves == (
        recon.represented_leaves + recon.excluded_leaves + recon.unresolved_leaves
    )
    assert recon.unresolved_leaves == 0
    assert not any(d.disposition is Disposition.UNRESOLVED for d in recon.dispositions)


def test_every_leaf_has_exactly_one_disposition(release: ReleaseArtifacts) -> None:
    disp_ids = [d.leaf_id for d in release.reconciliation.dispositions]
    ledger_ids = [leaf.leaf_id for leaf in release.ledger.leaves]
    assert sorted(disp_ids) == sorted(ledger_ids)
    assert len(disp_ids) == len(set(disp_ids))


def test_release_binds_five_top_level_hashes(release: ReleaseArtifacts) -> None:
    ident = release.release.identity
    for value in (
        ident.authoritative_source_hash,
        ident.transform_config_hash,
        ident.bundle_root_hash,
        ident.evidence_report_hash,
        ident.persisted_corpus_digest,
    ):
        assert value and len(value) == 64


def test_evidence_report_carries_proof_hashes_but_not_its_own(
    release: ReleaseArtifacts,
) -> None:
    payload = release.report.payload
    assert "persisted_corpus_digest" in payload
    assert payload["bundle_root_hash"] == release.release.identity.bundle_root_hash
    # The report never contains its own hash.
    assert release.release.identity.evidence_report_hash not in payload.values()


def _rebuild_report(a: ReleaseArtifacts) -> EvidenceReport:
    """Rebuild the evidence report from a published release's own inputs."""
    citation_mapping = a.report.payload["source_citation_mapping"]
    assert isinstance(citation_mapping, dict)
    return build_report(
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
        persisted=True,
        citation_mapping=citation_mapping,
    )


def test_evidence_report_identity_is_host_independent(
    release: ReleaseArtifacts, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R16 F2: the identity-bearing evidence report is byte-identical for identical
    committed inputs across supported hosts — no runtime host OS/arch/python enters
    the hashed payload (they are operational diagnostics, logged only). So the
    evidence-report hash (one of the five release identities) does not drift by
    host, and a reuse — which reconstructs from the stored payload — is unaffected.
    Rebound from the retired PDF-geometric release to the published source release.
    """

    def build_under(
        system: str, machine: str, pyver: str
    ) -> tuple[dict[str, object], str]:
        monkeypatch.setattr(platform, "system", lambda: system)
        monkeypatch.setattr(platform, "machine", lambda: machine)
        monkeypatch.setattr(platform, "python_version", lambda: pyver)
        r = _rebuild_report(release)
        return r.payload, report_hash(r)

    p1, h1 = build_under("Linux", "x86_64", "3.12.1")
    p2, h2 = build_under("Windows", "AMD64", "3.12.9")
    assert p1 == p2  # byte-identical payload across hosts
    assert h1 == h2  # identical report hash (release identity component)
    # No host/OS/arch field leaked into the identity-bearing payload.
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
    # The rebuild reproduces the hash the release actually published.
    assert h1 == release.release.identity.evidence_report_hash
    assert release.release.identity.evidence_report_hash == report_hash(release.report)


def test_authoritative_pdf_path_is_the_canonical_spelling() -> None:
    assert PDF_PATH.name == "DnD5_5e_SRD_CC_v5_2_1.pdf"
    assert PDF_PATH.exists()


def test_no_derivative_content_counts_as_authoritative(
    release: ReleaseArtifacts,
) -> None:
    # Component F: derivative layer is empty; nothing paraphrased is persisted.
    assert release.members.derivative_notes == ()
