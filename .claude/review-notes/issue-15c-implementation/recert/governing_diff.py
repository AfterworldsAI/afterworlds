"""Diff every component governing the executable fixed-DC check between the G1
authority and the recorded CRD Issue 15c successor (Advisor: recertification
is a review, not a re-pin). Prints, per changed component, the schema id and
fact families before and after. Run from the repository root.
"""

from __future__ import annotations

import sys
from uuid import UUID

sys.path.insert(0, ".")
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import identify_projection  # noqa: E402
from afterworlds.models.rules_package import RulesPackageBinding  # noqa: E402
from afterworlds.pipeline.rpg import capability  # noqa: E402
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
)


def index_of(name: str) -> AuthorityIndex:
    candidate = candidate_from_accepted_inputs(load_accepted_inputs(COMMITTED_ORACLE_DIR / name))
    binding = RulesPackageBinding(
        package_uuid=UUID(PACKAGE), release_version=RELEASE,
        mechanical_projection_uuid=UUID(identify_projection(candidate).projection_uuid),
        override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID))
    leaves = {s.leaf_id: i for i, s in enumerate(candidate.classification.spans)}
    return AuthorityIndex.from_authority(apply_override_set(
        candidate, EffectiveOverrideSet(PACKAGE, RELEASE, ()), binding, leaf_order=leaves))


old = index_of("srd-5-2-1-corpus-8781d4e0-a3b-g1.json")
new = index_of("srd-5-2-1-corpus-8781d4e0-a3b-15c.json")
print("projections", old.binding.mechanical_projection_uuid, new.binding.mechanical_projection_uuid)
changed = 0
for rk, ck in sorted(set(capability._governing(old)) | set(capability._governing(new))):
    a, b = old.component(rk, ck), new.component(rk, ck)
    if a is None or b is None or component_schema_id(a) != component_schema_id(b):
        changed += 1
        fam = lambda c: sorted({type(f.fact).__name__ for f in c.facts}) if c else None  # noqa: E731
        print(f"{rk}/{ck}: {fam(a)} -> {fam(b)}; options "
              f"{[o.semantic_key for o in a.options] if a else None} -> "
              f"{[o.semantic_key for o in b.options] if b else None}")
print("changed governing components:", changed)
print("new fingerprint", capability.governing_fingerprint(new))
