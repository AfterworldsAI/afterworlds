"""Deterministic mechanical-publication evidence report — CRD Issue 5d.

Generated from a completed gate run over reconstructed persisted state, never
hand-written and never assembled before the state it reports on exists. It
carries every identity an auditor needs to reproduce the decision:

* the exact 5c source release and the projection built over it;
* the accepted-oracle identity, so "which authority judged this" is on the
  record and a later oracle edit is detectable;
* the reconstructed-state and persisted-proof identities;
* the gate verdict, its categorized failures, and every obligation with its
  outcome — satisfied ones included, because a passing gate with no recorded
  obligations is an assertion rather than evidence; and
* drift diagnostics, explicitly labelled as such.

It does **not** contain its own hash (nothing can), and it contains no wall
clock, host, or reviewer identity. That is what makes it reproducible: the same
committed inputs and the same persisted state produce a byte-identical report,
and therefore the same report hash, on any host — the CRD Issue 5c determinism
rule applied to this artifact.

The projection's publication *status* is likewise absent. The report describes
whether the state is publishable, not what has since been done about it, so a
projection re-verified after publication reproduces the report hash recorded
when it was published. Publication relies on that: a recorded hash that no
longer matches the re-derived one means the evidence and the state have
diverged.

Counts live under ``drift_diagnostics`` and are named that way deliberately.
ADR-005d Decision 5 forbids proving completeness with totals; they are here to
make a regression visible between two releases, and nothing reads them to
decide anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.gate import GateResult
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM

__all__ = [
    "EVIDENCE_REPORT_SCHEMA_VERSION",
    "EvidenceReport",
    "build_evidence_report",
    "report_hash",
]

#: Canonical report shape. Bumped only on an intentional change to the payload's
#: canonical structure — never for a comment, docstring, or logging edit — so a
#: shape change is visible in the recorded evidence of every projection
#: published afterwards, and two reports carrying the same version are directly
#: comparable.
EVIDENCE_REPORT_SCHEMA_VERSION = "5d-mechanical-evidence-1"


@dataclass(frozen=True)
class EvidenceReport:
    """The completed report payload for one publication decision."""

    payload: dict[str, object]


def build_evidence_report(
    header: MechanicalProjectionORM, gate: GateResult
) -> EvidenceReport:
    """Build the evidence report for a completed gate run.

    Built for failures as well as successes. A refused publication is a
    decision that has to be auditable too, and the caller receives the report
    without it being persisted — recording evidence for a projection that was
    never published would be exactly the partial state atomic publication
    forbids.
    """
    payload: dict[str, object] = {
        "report_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        # Exact source release and projection: the two ends of the binding.
        "source_release": {
            "package_uuid": header.package_uuid,
            "release_version": header.release_version,
            "authoritative_source_hash": header.authoritative_source_hash,
            "transform_config_hash": header.transform_config_hash,
            "bundle_root_hash": header.bundle_root_hash,
            "persisted_corpus_digest": header.persisted_corpus_digest,
        },
        "mechanical_projection": {
            "projection_uuid": header.projection_uuid,
            "semantic_policy_version": header.semantic_policy_version,
            "semantic_policy_hash": header.semantic_policy_hash,
            "payload_hash": header.payload_hash,
            "persisted_state_digest": gate.persisted_state_digest,
        },
        # Which independent authority judged this, and what it derives.
        "accepted_oracle": {
            "oracle_identity": gate.oracle_identity,
            "derived_projection_uuid": gate.expected_projection_uuid,
        },
        "gate": {
            "passed": gate.passed,
            "failure_categories": sorted(c.value for c in gate.categories()),
            "failures": [
                {"category": f.category.value, "detail": f.detail}
                for f in gate.failures
            ],
        },
        "obligations": [
            {
                "record_key": o.record_key,
                "satisfied": o.satisfied,
                "failures": list(o.failures),
            }
            for o in gate.obligations
        ],
        # Regression canaries. Never a pass condition (ADR-005d Decision 5).
        "drift_diagnostics": dict(sorted(gate.diagnostics.items())),
    }
    return EvidenceReport(payload=payload)


def report_hash(report: EvidenceReport) -> str:
    """SHA-256 over the completed report payload."""
    return hash_obj(report.payload)
