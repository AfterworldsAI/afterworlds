"""Publication-gate tests — Issue 5c, Component I / Acceptance #9.

The gate passes only when every condition holds, and fails on each listed
condition individually. Each failing case starts from the real passing release
and breaks exactly one thing via ``dataclasses.replace``.
"""

from __future__ import annotations

import dataclasses

from afterworlds.ingestion.corpus.gate import run_gate
from afterworlds.ingestion.corpus.models import ReconciliationFindings


def _replace_identity(release, **kw):
    ident = dataclasses.replace(release.release.identity, **kw)
    rel = dataclasses.replace(release.release, identity=ident)
    return dataclasses.replace(release, release=rel)


def _replace_release(release, **kw):
    return dataclasses.replace(
        release, release=dataclasses.replace(release.release, **kw)
    )


def test_gate_passes_on_the_real_release(release):
    result = run_gate(release)
    assert result.passed, result.failures


def test_gate_fails_on_source_hash_mismatch(release):
    broken = _replace_identity(release, authoritative_source_hash="0" * 64)
    assert not run_gate(broken).passed


def test_gate_fails_on_substituted_ledger_hash(release):
    broken = _replace_release(release, ledger_hash="0" * 64)
    result = run_gate(broken)
    assert not result.passed
    assert any("ledger" in f for f in result.failures)


def test_gate_fails_on_tampered_digest(release):
    broken = _replace_identity(release, persisted_corpus_digest="0" * 64)
    result = run_gate(broken)
    assert not result.passed
    assert any("digest" in f for f in result.failures)


def test_gate_fails_on_missing_release_hash(release):
    broken = _replace_identity(release, bundle_root_hash="")
    assert not run_gate(broken).passed


def test_gate_fails_on_unresolved_leaves(release):
    recon = dataclasses.replace(release.reconciliation, unresolved_leaves=1)
    broken = dataclasses.replace(release, reconciliation=recon)
    result = run_gate(broken)
    assert not result.passed
    assert any("unresolved" in f for f in result.failures)


def test_gate_fails_on_gap_finding(release):
    findings = dataclasses.replace(release.reconciliation.findings, gaps=("some-leaf",))
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(dataclasses.replace(release, reconciliation=recon)).passed


def test_gate_fails_on_orphan_finding(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, orphans=("some-chunk",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    result = run_gate(dataclasses.replace(release, reconciliation=recon))
    assert not result.passed
    assert any("orphan" in f for f in result.failures)


def test_gate_fails_on_duplication_finding(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, duplications=("dup",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(dataclasses.replace(release, reconciliation=recon)).passed


def test_gate_fails_when_reconciliation_hash_substituted(release):
    broken = _replace_release(release, reconciliation_hash="0" * 64)
    result = run_gate(broken)
    assert not result.passed
    assert any("reconciliation" in f for f in result.failures)


def test_gate_fails_when_report_predates_persistence(release):
    report = dataclasses.replace(release.report, persisted=False)
    broken = dataclasses.replace(release, report=report)
    result = run_gate(broken)
    assert not result.passed
    assert any("predates persistence" in f for f in result.failures)


def test_gate_fails_on_legacy_reachability_violation(release):
    assert not run_gate(release, legacy_reachability_violations=1).passed


def test_gate_fails_when_sql_or_vector_persist_incomplete(release):
    assert not run_gate(release, sql_persist_ok=False).passed
    assert not run_gate(release, vector_write_ok=False).passed


def test_gate_fails_on_empty_findings_replaced_unresolved(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, unresolved=("leaf",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(dataclasses.replace(release, reconciliation=recon)).passed


def test_findings_type_is_frozen():
    f = ReconciliationFindings((), (), (), (), ())
    try:
        f.gaps = ("x",)  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("ReconciliationFindings should be frozen")
