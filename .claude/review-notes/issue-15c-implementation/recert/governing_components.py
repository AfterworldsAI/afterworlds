"""Component-level certification evidence (CRD Issue 15c).

For every executable operation, writes the exact sorted list of
(record key, component key, override-aware component schema id) its shared
procedure is governed by under the recorded successor, and the fingerprint
those entries hash to. The manifest's pins must equal these fingerprints; a
reviewer diffs this file, component by component, instead of trusting a bare
hash. Creature templates are certified per subject (``certify_template``) and
are not part of any shared fingerprint. Run from the repository root:

    venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/recert/governing_components.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from afterworlds.pipeline.rpg.capability import (  # noqa: E402
    MANIFEST,
    CapabilityStatus,
    _governing,
)
from afterworlds.services.dnd5e_state.authority import (  # noqa: E402
    component_schema_id,
)
from tests.services.dnd5e_state.builders import real_index  # noqa: E402

OUT = Path(__file__).with_name("governing-components.json")


def main() -> None:
    index = real_index()
    evidence: dict[str, object] = {
        "binding": {
            "package_uuid": str(index.binding.package_uuid),
            "release_version": index.binding.release_version,
            "projection_uuid": str(index.binding.mechanical_projection_uuid),
            "override_set_uuid": str(index.binding.override_set_uuid),
        },
        "operations": {},
    }
    mismatched = []
    for operation, capability in MANIFEST.items():
        if capability.status is not CapabilityStatus.EXECUTABLE:
            continue
        entries = []
        for record_key, component_key in _governing(index, operation):
            component = index.component(record_key, component_key)
            assert component is not None, (record_key, component_key)
            entries.append([record_key, component_key, component_schema_id(component)])
        entries.sort()
        encoded = json.dumps(entries, separators=(",", ":"))
        fingerprint = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        evidence["operations"][operation.value] = {  # type: ignore[index]
            "fingerprint": fingerprint,
            "components": entries,
        }
        if fingerprint != capability.fingerprint:
            mismatched.append(operation.value)
    OUT.write_text(json.dumps(evidence, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(OUT.name, hashlib.sha256(OUT.read_bytes()).hexdigest())
    print("pins differing from evidence:", mismatched or "none")


if __name__ == "__main__":
    main()
