"""Validate candidate S1 (CRD Issue 15b) against its pinned source and the
accepted C8 authority. REVIEW MATERIAL ONLY, and SIMULATED: the override is
applied in memory to the committed C8 inputs; nothing is authored into a
store, published or activated. Run from the repository root:

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-contest-authority/supplement-s1/validate_s1.py \
        [--pdf PATH]

With ``--pdf`` (or the scratch copy present) the raw page text is re-extracted
and must equal the committed ``page-77-extract.txt``. Writes
``validation.json``; exits non-zero if any check fails. Byte-identical across
runs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from uuid import UUID

REPO = Path.cwd()
HERE = REPO / ".claude/review-notes/issue-15b-contest-authority/supplement-s1"
C8_ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
)

_spec = importlib.util.spec_from_file_location("derive_s1", HERE / "derive_s1.py")
assert _spec and _spec.loader
derive = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(derive)

import afterworlds  # noqa: E402
from afterworlds.ingestion.mechanical.models import ComponentHandling  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    candidate_from_accepted_inputs,
    committed_inputs_for,
)
from afterworlds.ingestion.mechanical.projection import identify_projection  # noqa: E402
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum  # noqa: E402
from afterworlds.models.rules_package import RulesPackageBinding  # noqa: E402
from afterworlds.pipeline.rpg.capability import (  # noqa: E402
    CERTIFIED_RELEASE,
    MANIFEST,
    AdjudicationRefusal,
    CapabilityStatus,
    certify,
    governing_fingerprint,
)
from afterworlds.services.dnd5e_state.authority import (  # noqa: E402
    AuthorityIndex,
    component_schema_id,
)
from afterworlds.services.rules_authority.application import (  # noqa: E402
    AuthoredProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.override_set import (  # noqa: E402
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    override_set_identity,
)
from afterworlds.services.rules_authority.patches import (  # noqa: E402
    InvalidPatchError,
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.targets import (  # noqa: E402
    MechanicalTarget,
    MechanicalTargetKind,
)

PACKAGE, RELEASE = derive.RELEASE


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry_from(override: dict[str, object], **changes: object) -> EffectiveOverrideEntry:
    target = MechanicalTarget(
        kind=MechanicalTargetKind(override["target"]["kind"]),  # type: ignore[index]
        record_key=override["target"]["record_key"],  # type: ignore[index]
    )
    operation = OverrideOperationEnum(override["operation"])
    patch = patch_from_payload(override["payload"], operation=operation, target=target)
    entry = EffectiveOverrideEntry(
        override_id=str(override["override_id"]),
        origin=OverrideOriginEnum(override["origin"]),
        target=target,
        operation=operation,
        precedence=int(override["precedence"]),  # type: ignore[arg-type]
        apply_order=0,
        is_enabled=bool(override["is_enabled"]),
        payload=patch_payload(patch),
    )
    return replace(entry, **changes) if changes else entry


def index_for(candidate, entries: tuple[EffectiveOverrideEntry, ...]) -> AuthorityIndex:
    projection = identify_projection(candidate).projection_uuid
    binding = RulesPackageBinding(
        package_uuid=UUID(PACKAGE),
        release_version=RELEASE,
        mechanical_projection_uuid=UUID(projection),
        override_set_uuid=UUID(override_set_identity(entries)),
    )
    leaves = {s.leaf_id: i for i, s in enumerate(candidate.classification.spans)}
    authority = apply_override_set(
        candidate,
        EffectiveOverrideSet(PACKAGE, RELEASE, entries),
        binding,
        leaf_order=leaves,
    )
    return AuthorityIndex.from_authority(authority)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf", type=Path, default=derive.SCRATCH / "SRD_CC_v5.1-contest-source.pdf"
    )
    args = parser.parse_args()
    assert Path(afterworlds.__file__).resolve().is_relative_to(REPO / "src"), (
        "run with this checkout's src first"
    )
    checks: dict[str, object] = {}

    def check(name: str, ok: bool, detail: object = None) -> None:
        checks[name] = {"ok": bool(ok), **({"detail": detail} if detail is not None else {})}

    s1_bytes = (HERE / "s1.json").read_bytes()
    s1 = json.loads(s1_bytes)
    raw = (HERE / "page-77-extract.txt").read_bytes().decode("utf-8")

    # --- source -----------------------------------------------------------
    if args.pdf.exists():
        pdf = args.pdf.read_bytes()
        check("pdf_pinned", sha(pdf) == derive.PDF_SHA256 and len(pdf) == derive.PDF_BYTES)
        check("page_extract_reproduces", derive.page_text(args.pdf, derive.PAGE_INDEX) == raw)
        attribution = derive.attribution_from(
            derive.page_text(args.pdf, derive.LEGAL_PAGE_INDEX)
        )
        check("attribution_is_the_source_statement", attribution == s1["attribution"])
    else:
        check("pdf_pinned", False, "PDF not present: source re-extraction not run")
    check("page_extract_pinned", sha(raw.encode("utf-8")) == s1["source"]["page_extract_sha256"])
    excerpt, applied = derive.excerpt_from(raw)
    check("excerpt_reproduces", excerpt == s1["excerpt"]["text"])
    check("corrections_listed_exactly", applied == s1["excerpt"]["corrections"])
    flat = derive.WHITESPACE.sub(" ", raw)
    for wrong, right in derive.CORRECTIONS:
        flat = flat.replace(wrong, right)
    sentences = re.split(r"(?<=[.,]) (?=[A-Z])", excerpt)
    missing = [s for s in sentences if s not in flat]
    check("every_excerpt_sentence_in_source", not missing, {"sentences": len(sentences), "missing": missing})
    check(
        "excerpt_bounds",
        flat.index(excerpt) == flat.index("Contests Sometimes") + len("Contests ")
        and flat[flat.index(excerpt) + len(excerpt) :].lstrip().startswith("Skills "),
    )
    codepoints = sorted({f"U+{ord(c):04X}" for c in excerpt + s1["attribution"] if ord(c) > 0x7E})
    check(
        "no_replacement_characters",
        "U+FFFD" not in codepoints,
        {"non_ascii_codepoints": codepoints},
    )
    receipt = derive.RECEIPT.read_bytes()
    check("receipt_digest_recorded", sha(receipt) == s1["owner_policy"]["receipt_sha256"])
    check(
        "policy_points_verbatim_in_receipt",
        all(p in receipt.decode("utf-8") for p in s1["owner_policy"]["points"]),
    )
    check("proposal_pinned", sha(derive.PROPOSAL.read_bytes()) == derive.PROPOSAL_SHA256)
    prose = s1["override"]["payload"]["component"]["authored_prose"]
    check("prose_carries_excerpt_points_attribution", excerpt in prose and s1["attribution"] in prose and all(p in prose for p in s1["owner_policy"]["points"]))
    check("prose_digest", sha(prose.encode("utf-8")) == s1["authored_prose_sha256"])
    check("prose_reproduces", prose == derive.authored_prose(excerpt, s1["attribution"]))

    # --- override ---------------------------------------------------------
    override = s1["override"]
    entry = entry_from(override)
    check("payload_is_canonical_patch", entry.payload == override["payload"])
    check("deterministic_override_id", override["override_id"] == derive.OVERRIDE_ID)
    check("authored_against_c8_release", (override["package_uuid"], override["release_version"]) == derive.RELEASE)
    refused = {}
    for name, body in {
        "structured_with_prose": {**override["payload"]["component"], "handling": "structured"},
        "prose_bound_without_prose": {**override["payload"]["component"], "authored_prose": None},
        "unkeyed_addition": {
            k: v for k, v in override["payload"]["component"].items() if k != "semantic_key"
        },
    }.items():
        try:
            patch_from_payload(
                {"patch": "append_component", "component": body},
                operation=OverrideOperationEnum.APPEND,
                target=entry.target,
            )
            refused[name] = False
        except InvalidPatchError:
            refused[name] = True
    check("malformed_variants_refused", all(refused.values()), refused)

    # --- in-memory application to accepted C8 (SIMULATED) -------------------
    inputs = committed_inputs_for(PACKAGE, RELEASE)
    assert inputs is not None
    candidate = candidate_from_accepted_inputs(inputs)
    projection = identify_projection(candidate).projection_uuid
    check("c8_projection_is_certified", (UUID(PACKAGE), RELEASE, UUID(projection)) == CERTIFIED_RELEASE, projection)
    base = index_for(candidate, ())
    supplemented = index_for(candidate, (entry,))
    disabled = index_for(candidate, (replace(entry, is_enabled=False),))
    supplement_set = override_set_identity((entry,))
    check("base_binding_is_empty_set", str(base.binding.override_set_uuid) == EMPTY_OVERRIDE_SET_UUID)
    check("base_has_no_contest_component", base.component("play.d20_tests", "contest") is None)
    check("disabled_has_no_contest_component", disabled.component("play.d20_tests", "contest") is None)
    component = supplemented.component("play.d20_tests", "contest")
    ok = (
        component is not None
        and component.handling is ComponentHandling.PROSE_BOUND
        and not component.facts
        and component.supplied_by_override_id == entry.override_id
        and len(component.governing_prose) == 1
        and isinstance(component.governing_prose[0], AuthoredProse)
        and component.governing_prose[0].text == prose
        and component.governing_prose[0].supplied_by_override_id == entry.override_id
        and component.irreducibility_reason_code is None
    )
    check("supplement_component_effective", ok)
    schema_id = component_schema_id(component) if component else None
    altered = index_for(
        candidate,
        (
            entry_from(
                {
                    **override,
                    "payload": {
                        "patch": "append_component",
                        "component": {**override["payload"]["component"], "authored_prose": prose + " "},
                    },
                }
            ),
        ),
    ).component("play.d20_tests", "contest")
    check("text_change_moves_schema_id", altered is not None and component_schema_id(altered) != schema_id)
    base_ids = {
        (r, c.semantic_key): component_schema_id(c)
        for r, rec in base.records.items()
        for c in rec.components
    }
    sup_ids = {
        (r, c.semantic_key): component_schema_id(c)
        for r, rec in supplemented.records.items()
        for c in rec.components
    }
    added = sorted(set(sup_ids) - set(base_ids))
    changed = sorted(k for k in base_ids if sup_ids.get(k) != base_ids[k])
    check("only_the_contest_component_added", added == [("play.d20_tests", "contest")] and not changed, {"added": added, "changed": changed})
    check("overridden_records", sorted(supplemented.overridden) == ["play.d20_tests"], sorted(supplemented.overridden))

    fingerprints = {}
    for operation, capability in MANIFEST.items():
        b = governing_fingerprint(base, operation)
        s = governing_fingerprint(supplemented, operation)
        certified = None
        if capability.status is CapabilityStatus.EXECUTABLE:
            try:
                certify(operation, supplemented)
                certified = True
            except AdjudicationRefusal as exc:
                certified = str(exc)
        fingerprints[operation.value] = {
            "unchanged": b == s,
            "matches_manifest": (b == capability.fingerprint) if capability.fingerprint else None,
            "certifies_under_supplement": certified,
        }
    check(
        "every_15c_operation_unaffected",
        all(
            v["unchanged"]
            and v["matches_manifest"] is not False
            and v["certifies_under_supplement"] in (True, None)
            for v in fingerprints.values()
        ),
        fingerprints,
    )

    result = {
        "candidate": {"s1.json": sha(s1_bytes), "page-77-extract.txt": sha(raw.encode("utf-8"))},
        "simulated": "in-memory application to committed C8 inputs; no store, publication or activation",
        "c8_oracle_sha256": sha(C8_ORACLE.read_bytes()),
        "certified_release": [str(x) for x in CERTIFIED_RELEASE],
        "override_id": entry.override_id,
        "supplement_only_override_set_uuid": supplement_set,
        "contest_component_schema_id": schema_id,
        "checks": checks,
        "all_ok": all(v["ok"] for v in checks.values()),  # type: ignore[index]
    }
    out = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    (HERE / "validation.json").write_bytes(out.encode("utf-8"))
    print(f"validation.json {sha(out.encode('utf-8'))} all_ok={result['all_ok']}")
    for name, value in checks.items():
        if not value["ok"]:  # type: ignore[index]
            print("FAILED", name, value)
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
