"""Legacy quarantine and zero-reachability check — Issue 5c, Component L.

Owner Decision 1 requires the incomplete legacy SRD artifact, its package
identity, and its seeded rows to be unreachable from every executable path. This
module provides the machine check the publication gate consumes (Component I)
and the test suite asserts (Acceptance #12): it returns the list of reachability
violations, which must be empty.

A violation is any of:
* the legacy JSON still present at its former default ingestion location;
* an active-store row bound to the legacy package identity that is not a new
  Issue 5c corpus release;
* a Python source file that references the legacy ingestion path.

Marking a package "retired", renaming a directory, or excluding it from a
default query is *not* sufficient — this check fails if any executable path can
still reach the material.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM

# The legacy artifact's former default ingestion location and package identity.
LEGACY_DEFAULT_PATH = "data/srd/srd_5_2_1_structured.json"
LEGACY_PACKAGE_NAME = "D&D SRD 5.2.1"
LEGACY_PACKAGE_VERSION = "5.2.1"
LEGACY_ARTIFACT_SHA256 = (
    "3d1e7de02a2d37f6a4aadec01d8854aec7fda6a7c7ec765ca1d3a942b9187e02"
)


def check_active_store(session: Session) -> list[str]:
    """Return violations for active-store rows bound to the legacy package.

    A legacy row is a ``rp_packages`` row carrying the legacy name/version that
    is **not** registered as a new Issue 5c corpus release. New corpus releases
    are always registered in ``rp_corpus_releases`` and never carry the legacy
    name, so this can never flag the corrected corpus.
    """
    corpus_ids = {
        row.package_uuid for row in session.execute(select(CorpusReleaseORM)).scalars()
    }
    violations: list[str] = []
    for pkg in session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.name == LEGACY_PACKAGE_NAME,
            RulesPackageORM.version == LEGACY_PACKAGE_VERSION,
        )
    ).scalars():
        if pkg.rules_package_id not in corpus_ids:
            violations.append(
                f"active legacy package row {pkg.rules_package_id} "
                f"({pkg.name} {pkg.version})"
            )
    return violations


def check_filesystem(repo_root: Path) -> list[str]:
    """Return violations for legacy material at a discoverable ingestion path."""
    violations: list[str] = []
    if (repo_root / LEGACY_DEFAULT_PATH).exists():
        violations.append(
            f"legacy artifact still present at default ingestion path "
            f"{LEGACY_DEFAULT_PATH}"
        )
    return violations


def check_source_references(repo_root: Path) -> list[str]:
    """Return violations for executable references to the legacy ingestion path.

    Scans committed Python under ``src/`` and ``scripts/``. The quarantine
    documentation under ``docs/`` is inert evidence and is not scanned.
    """
    violations: list[str] = []
    self_path = Path(__file__).resolve()
    for base in ("src", "scripts"):
        root = repo_root / base
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            # This checker module necessarily names the path to scan for it.
            if path.resolve() == self_path:
                continue
            text = path.read_text(encoding="utf-8")
            if LEGACY_DEFAULT_PATH in text:
                violations.append(
                    f"{path.relative_to(repo_root)} references legacy path"
                )
    return violations


def check_legacy_reachability(session: Session | None, repo_root: Path) -> list[str]:
    """Aggregate all zero-reachability violations (Component L / Acceptance #12)."""
    violations = check_filesystem(repo_root) + check_source_references(repo_root)
    if session is not None:
        violations += check_active_store(session)
    return violations
