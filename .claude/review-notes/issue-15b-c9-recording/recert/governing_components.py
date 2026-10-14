"""Component-level recertification evidence on the C9 successor (CRD Issue 15b).

For every executable operation, writes the exact sorted list of
(record key, component key, component schema id) its shared procedure is
governed by under the production-selected C9 successor and the fingerprint
those entries hash to, and diffs each against the superseded C8 successor
(loaded explicitly), component by component. Creature templates are certified
per subject (``certify_template``) and are in no shared fingerprint; their
digest changes are counted separately. The C8 evidence
(``issue-15c-implementation/recert/governing-components.json``) is not
touched. Run from the repository root with ``src`` first on ``PYTHONPATH``:

    PYTHONPATH=src venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-c9-recording/recert/governing_components.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, ".")
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.models.rules_package import RulesPackageBinding  # noqa: E402
from afterworlds.pipeline.rpg.capability import (  # noqa: E402
    MANIFEST,
    CapabilityStatus,
    _governing,
)
from afterworlds.services.dnd5e_state.authority import (  # noqa: E402
    AuthorityIndex,
    component_schema_id,
)
from afterworlds.services.rules_authority.application import (  # noqa: E402
    EffectiveOverrideSet,
    apply_override_set,
)
from tests.services.dnd5e_state.builders import (  # noqa: E402
    EMPTY_OVERRIDE_SET_UUID,
    PACKAGE,
    RELEASE,
    real_index,
)

OUT = Path(__file__).with_name("governing-components.json")
C8 = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"


def index_of(path: Path) -> AuthorityIndex:
    candidate = candidate_from_accepted_inputs(load_accepted_inputs(path))
    binding = RulesPackageBinding(
        package_uuid=UUID(PACKAGE),
        release_version=RELEASE,
        mechanical_projection_uuid=UUID(identify_projection(candidate).projection_uuid),
        override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
    )
    leaves = {s.leaf_id: i for i, s in enumerate(candidate.classification.spans)}
    return AuthorityIndex.from_authority(
        apply_override_set(
            candidate,
            EffectiveOverrideSet(PACKAGE, RELEASE, ()),
            binding,
            leaf_order=leaves,
        )
    )


def entries(index: AuthorityIndex, operation: object) -> list[list[str]]:
    out = []
    for record_key, component_key in _governing(index, operation):  # type: ignore[arg-type]
        component = index.component(record_key, component_key)
        assert component is not None, (record_key, component_key)
        out.append([record_key, component_key, component_schema_id(component)])
    return sorted(out)


def fingerprint(rows: list[list[str]]) -> str:
    encoded = json.dumps(rows, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def main() -> None:
    new, old = real_index(), index_of(C8)
    evidence: dict[str, object] = {
        "binding": {
            "package_uuid": str(new.binding.package_uuid),
            "release_version": new.binding.release_version,
            "projection_uuid": str(new.binding.mechanical_projection_uuid),
            "override_set_uuid": str(new.binding.override_set_uuid),
        },
        "superseded_c8_projection": str(old.binding.mechanical_projection_uuid),
        "operations": {},
    }
    mismatched, moved = [], []
    for operation, capability in MANIFEST.items():
        if capability.status is not CapabilityStatus.EXECUTABLE:
            continue
        rows, before = entries(new, operation), entries(old, operation)
        changed = sorted(
            {tuple(r[:2]) for r in rows} ^ {tuple(r[:2]) for r in before}
            | {tuple(r[:2]) for r in rows if r not in before}
        )
        evidence["operations"][operation.value] = {  # type: ignore[index]
            "fingerprint": fingerprint(rows),
            "c8_fingerprint": fingerprint(before),
            "components_changed_from_c8": [list(k) for k in changed],
            "components": rows,
        }
        if changed:
            moved.append(operation.value)
        if fingerprint(rows) != capability.fingerprint:
            mismatched.append(operation.value)
    templates = sorted(
        k
        for k, r in new.records.items()
        if k.startswith(("monsters.", "animals."))
        and any(
            (b := old.component(k, c.semantic_key)) is None
            or component_schema_id(b) != component_schema_id(c)
            for c in r.components
        )
    )
    evidence["records_with_changed_components"] = {
        "count": len(templates),
        "outside_monsters_and_animals": sorted(
            k
            for k, r in new.records.items()
            if not k.startswith(("monsters.", "animals."))
            and any(
                (b := old.component(k, c.semantic_key)) is None
                or component_schema_id(b) != component_schema_id(c)
                for c in r.components
            )
        ),
    }
    evidence["operations_whose_governing_set_moved"] = moved
    OUT.write_text(
        json.dumps(evidence, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(OUT.name, hashlib.sha256(OUT.read_bytes()).hexdigest())
    print("executable operations:", len(evidence["operations"]))  # type: ignore[arg-type]
    print("governing sets moved from C8:", moved or "none")
    print("records changed:", evidence["records_with_changed_components"])
    print("pins differing from evidence:", mismatched or "none")


if __name__ == "__main__":
    main()
