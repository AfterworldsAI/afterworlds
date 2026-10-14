"""Current compatibility of the accepted S1 override with the recorded C9
successor (CRD Issue 15b). In memory only: S1 is applied to the
production-selected inputs as an isolated fixture; nothing is authored into a
store, published or activated.

The accepted S1 report (``issue-15b-contest-authority/supplement-s1/
validation.json``, 28 checks on C8) is historical and is neither rerun nor
rewritten here: its validator selects whatever authority is current and would
overwrite it. Its source, extraction, attribution and payload checks do not
depend on the corpus and are reused. Only what recording C9 invalidated is
checked, and written to ``s1-on-c9.json``. Run from the repository root with
``src`` first on ``PYTHONPATH``:

    PYTHONPATH=src venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-c9-recording/s1-on-c9/check_s1_on_c9.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path.cwd()
HERE = Path(__file__).resolve().parent
S1_DIR = REPO / ".claude/review-notes/issue-15b-contest-authority/supplement-s1"
_spec = importlib.util.spec_from_file_location("validate_s1", S1_DIR / "validate_s1.py")
assert _spec and _spec.loader
v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v)  # helpers only; its main() is not run

import afterworlds  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import oracle_identity  # noqa: E402
from afterworlds.pipeline.rpg.capability import (  # noqa: E402
    CERTIFIED_RELEASE,
    MANIFEST,
    CapabilityStatus,
    certify,
    governing_fingerprint,
)

S1_SHA256 = "c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a"  # noqa: E501  # pragma: allowlist secret
#: Accepted S1 report (C8) and the identities it recorded that do not depend
#: on the corpus: override, supplement-only set, contest component schema id.
VALIDATION_SHA256 = "22bd4d12d0ac43e27226c82e42efc7abe980840460db32f302aff7cc8ed80b66"  # noqa: E501  # pragma: allowlist secret
C9_ORACLE_IDENTITY = "924321dff5ab1821de3a4cdf464e3db1aa28859238458ddd6a58663ddf15ab0c"  # noqa: E501  # pragma: allowlist secret
C9_PROJECTION = "3703faf5-8b51-5c3f-b28c-b378b005f7bf"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    assert Path(afterworlds.__file__).resolve().is_relative_to(REPO / "src")
    checks: dict[str, object] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = {"ok": bool(ok), **({"detail": detail} if detail else {})}

    s1_bytes = (S1_DIR / "s1.json").read_bytes()
    report_bytes = (S1_DIR / "validation.json").read_bytes()
    accepted = json.loads(report_bytes)
    check("s1_exact", sha(s1_bytes) == S1_SHA256)
    check(
        "accepted_c8_report_preserved",
        sha(report_bytes) == VALIDATION_SHA256
        and accepted["all_ok"]
        and len(accepted["checks"]) == 28,
    )
    s1 = json.loads(s1_bytes)
    entry = v.entry_from(s1["override"])
    check("override_id", entry.override_id == accepted["override_id"])

    inputs = v.committed_inputs_for(v.PACKAGE, v.RELEASE)
    assert inputs is not None
    check(
        "selected_is_c9",
        oracle_identity(inputs.oracle) == C9_ORACLE_IDENTITY
        and inputs.oracle.schema_version == "5d-representation-schema-22",
    )
    candidate = v.candidate_from_accepted_inputs(inputs)
    base = v.index_for(candidate, ())
    supplemented = v.index_for(candidate, (entry,))
    b, s = base.binding, supplemented.binding
    check(
        "binding_is_c9_certified_release",
        (b.package_uuid, b.release_version, b.mechanical_projection_uuid)
        == CERTIFIED_RELEASE
        and str(b.mechanical_projection_uuid) == C9_PROJECTION
        and s.mechanical_projection_uuid == b.mechanical_projection_uuid,
    )
    check(
        "override_set_identity",
        str(b.override_set_uuid) == v.EMPTY_OVERRIDE_SET_UUID
        and str(s.override_set_uuid) == accepted["supplement_only_override_set_uuid"],
        str(s.override_set_uuid),
    )
    component = supplemented.component("play.d20_tests", "contest")
    check(
        "base_has_no_contest_component",
        base.component("play.d20_tests", "contest") is None,
    )
    check(
        "contest_component_schema_id_unchanged",
        component is not None
        and v.component_schema_id(component) == accepted["contest_component_schema_id"],
    )
    check("overridden_records", sorted(supplemented.overridden) == ["play.d20_tests"])
    operations = {}
    for operation, capability in MANIFEST.items():
        if capability.status is not CapabilityStatus.EXECUTABLE:
            continue
        unsupplemented = governing_fingerprint(base, operation)
        under = governing_fingerprint(supplemented, operation)
        certificate = certify(operation, supplemented)
        operations[operation.value] = {
            "fingerprint_unchanged_and_pinned": unsupplemented
            == under
            == capability.fingerprint,
            "certifies_under_s1": str(certificate.projection_uuid) == C9_PROJECTION
            and certificate.override_set_uuid == s.override_set_uuid,
        }
    check(
        "all_14_operations_unaffected_and_certified",
        len(operations) == 14 and all(all(x.values()) for x in operations.values()),
        operations,
    )
    result = {
        "simulated": "S1 applied in memory to the production-selected C9 inputs; "
        "no store, publication or activation",
        "s1_sha256": S1_SHA256,
        "certified_release": [str(x) for x in CERTIFIED_RELEASE],
        "supplement_only_override_set_uuid": str(s.override_set_uuid),
        "checks": checks,
        "all_ok": all(c["ok"] for c in checks.values()),  # type: ignore[index]
    }
    out = json.dumps(result, indent=1, sort_keys=True) + "\n"
    (HERE / "s1-on-c9.json").write_text(out, "utf-8", newline="\n")
    print("s1-on-c9.json", sha(out.encode()), "all_ok", result["all_ok"])
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
