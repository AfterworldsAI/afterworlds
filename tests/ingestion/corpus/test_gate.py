"""Publication-gate tests — Issue 5c, Component I / Acceptance #9.

The gate passes only when every condition holds, and fails on each listed
condition individually. Each failing case starts from the real passing release
and breaks exactly one thing via ``dataclasses.replace``.
"""

from __future__ import annotations

import dataclasses

from afterworlds.ingestion.corpus.gate import PublicationEvidence, run_gate
from afterworlds.ingestion.corpus.models import ReconciliationFindings


def _evidence(
    *,
    sql_persist_ok: bool = True,
    vector_write_ok: bool = True,
    membership: int = 0,
    source_membership: int = 0,
    vector_failures: tuple[str, ...] = (),
) -> PublicationEvidence:
    """Explicit all-passing evidence for gate unit tests (each scenario breaks
    exactly one input). This is a test helper, not a production caller — the
    production gate surface (``PublicationEvidence``) has no defaults, so real
    callers cannot hardcode success by omission."""
    return PublicationEvidence(
        sql_persist_ok=sql_persist_ok,
        vector_write_ok=vector_write_ok,
        chunk_membership_violations=membership,
        source_membership_violations=source_membership,
        vector_verification_failures=vector_failures,
    )


def _replace_identity(release, **kw):
    ident = dataclasses.replace(release.release.identity, **kw)
    rel = dataclasses.replace(release.release, identity=ident)
    return dataclasses.replace(release, release=rel)


def _replace_release(release, **kw):
    return dataclasses.replace(
        release, release=dataclasses.replace(release.release, **kw)
    )


def test_gate_passes_on_the_real_release(release):
    result = run_gate(release, _evidence())
    assert result.passed, result.failures


def test_gate_fails_on_source_hash_mismatch(release):
    broken = _replace_identity(release, authoritative_source_hash="0" * 64)
    assert not run_gate(broken, _evidence()).passed


def test_gate_fails_on_substituted_ledger_hash(release):
    broken = _replace_release(release, ledger_hash="0" * 64)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("ledger" in f for f in result.failures)


def test_gate_fails_on_tampered_digest(release):
    broken = _replace_identity(release, persisted_corpus_digest="0" * 64)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("digest" in f for f in result.failures)


def test_gate_fails_on_missing_release_hash(release):
    broken = _replace_identity(release, bundle_root_hash="")
    assert not run_gate(broken, _evidence()).passed


def test_gate_fails_on_incomplete_transform_config(release):
    """PR #134 P1: a recorded transform config with no first-party source
    manifest (the pre-fix payload) is rejected — the gate no longer accepts an
    identity that omits the transform-code manifest."""
    partial = {
        k: v
        for k, v in release.release.transform_config.items()
        if k != "transform_identity"
    }
    broken = _replace_release(release, transform_config=partial)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("transform identity incomplete" in f for f in result.failures)


def test_gate_fails_on_tampered_transform_config(release):
    """PR #134 P1: tampering the recorded transform config without updating its
    stored hash fails the internal-consistency check (the config is validated
    against its recorded hash, not reconstructed from ledger config + policy)."""
    tampered = {**release.release.transform_config, "extraction_config": {"tool": "x"}}
    broken = _replace_release(release, transform_config=tampered)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("transform config" in f for f in result.failures)


def test_gate_fails_on_unresolved_leaves(release):
    recon = dataclasses.replace(release.reconciliation, unresolved_leaves=1)
    broken = dataclasses.replace(release, reconciliation=recon)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("unresolved" in f for f in result.failures)


def test_gate_fails_on_gap_finding(release):
    findings = dataclasses.replace(release.reconciliation.findings, gaps=("some-leaf",))
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(
        dataclasses.replace(release, reconciliation=recon), _evidence()
    ).passed


def test_gate_fails_on_orphan_finding(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, orphans=("some-chunk",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    result = run_gate(dataclasses.replace(release, reconciliation=recon), _evidence())
    assert not result.passed
    assert any("orphan" in f for f in result.failures)


def test_gate_fails_on_duplication_finding(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, duplications=("dup",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(
        dataclasses.replace(release, reconciliation=recon), _evidence()
    ).passed


def test_gate_fails_when_reconciliation_hash_substituted(release):
    broken = _replace_release(release, reconciliation_hash="0" * 64)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("reconciliation" in f for f in result.failures)


def test_gate_fails_when_the_report_lacks_a_persisted_corpus_digest(release):
    """The structural replacement for the deleted ``report.persisted`` check.

    That flag lived on a wrapper outside the hashed payload and was supplied by
    the caller, so it asserted the post-persistence ordering rather than proving
    it. What proves it now is that ``persisted_corpus_digest`` cannot be
    computed before persistence — so a report without one did not come from a
    persisted release, whatever it claims."""
    report = release.report._replace(persisted_corpus_digest="")
    broken = dataclasses.replace(release, report=report)
    result = run_gate(broken, _evidence())
    assert not result.passed
    assert any("lacks persisted-corpus digest" in f for f in result.failures)


def test_gate_fails_when_sql_or_vector_persist_incomplete(release):
    assert not run_gate(release, _evidence(sql_persist_ok=False)).passed
    assert not run_gate(release, _evidence(vector_write_ok=False)).passed


def test_gate_fails_on_vector_verification_failure(release):
    result = run_gate(
        release, _evidence(vector_failures=("vector collection missing doc X",))
    )
    assert not result.passed
    assert any("vector verification" in f for f in result.failures)


def test_gate_fails_on_chunk_membership_violation(release):
    assert not run_gate(release, _evidence(membership=1)).passed


def test_gate_fails_on_source_membership_violation(release):
    # An extra/missing/altered/disabled/reassigned source raises the count
    # (persistence.verify_single_source); the gate must fail closed (PR #134 D3).
    result = run_gate(release, _evidence(source_membership=1))
    assert not result.passed
    assert any("source-membership" in f for f in result.failures)


def test_gate_fails_on_empty_findings_replaced_unresolved(release):
    findings = dataclasses.replace(
        release.reconciliation.findings, unresolved=("leaf",)
    )
    recon = dataclasses.replace(release.reconciliation, findings=findings)
    assert not run_gate(
        dataclasses.replace(release, reconciliation=recon), _evidence()
    ).passed


def test_findings_type_is_frozen():
    f = ReconciliationFindings((), (), (), (), ())
    try:
        f.gaps = ("x",)  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("ReconciliationFindings should be frozen")
