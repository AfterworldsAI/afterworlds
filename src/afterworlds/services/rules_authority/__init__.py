"""Runtime mechanical authority — CRD Issue 5d, Decisions 9 and 10.

The infrastructure planned in PR #139's delivery sequence: the exact
four-component effective binding, one code-owned resolution path, deterministic
selectors, typed record/component/fact overrides with immutable replayable
override-set versions, and the two authority views.

This is infrastructure, not completed CRD Issue 5d. No production mechanical
projection is published yet, so every production resolution through this package
currently reports ``UNPUBLISHED`` — honestly, and by construction.
"""

from afterworlds.services.rules_authority.application import (
    AppliedOverride,
    AuthoredProse,
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveFact,
    EffectiveRecord,
    GoverningProseEntry,
    OverrideApplicationError,
    SourceProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.binding import (
    BindingResolution,
    PackageResolution,
    package_slug,
    resolve_effective_binding,
    resolve_package_reference,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    OverrideStateError,
    collect_current_override_state,
    override_set_identity,
)
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    MechanicalPatch,
    PatchFamily,
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.retention import (
    OverrideSetRetentionError,
    load_override_set_version,
    retain_override_set,
)
from afterworlds.services.rules_authority.service import (
    AuthorityResult,
    IncoherentBindingError,
    MechanicalRuleSlice,
    RulesAuthorityService,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
    TargetShapeError,
)
from afterworlds.services.rules_authority.views import (
    GameMasterAuthorityView,
    GameMasterComponent,
    TypedAuthorityView,
)

__all__ = [
    "EMPTY_OVERRIDE_SET_UUID",
    "AppliedOverride",
    "AuthoredProse",
    "AuthorityOutcome",
    "AuthorityResult",
    "BindingResolution",
    "EffectiveAuthority",
    "EffectiveComponent",
    "EffectiveFact",
    "EffectiveOverrideEntry",
    "EffectiveOverrideSet",
    "EffectiveRecord",
    "GameMasterAuthorityView",
    "GameMasterComponent",
    "GoverningProseEntry",
    "IncoherentBindingError",
    "InvalidPatchError",
    "MechanicalPatch",
    "MechanicalRuleSlice",
    "MechanicalTarget",
    "MechanicalTargetKind",
    "OverrideApplicationError",
    "OverrideSetRetentionError",
    "OverrideStateError",
    "PackageResolution",
    "PatchFamily",
    "RulesAuthorityService",
    "SourceProse",
    "TargetShapeError",
    "TypedAuthorityView",
    "apply_override_set",
    "collect_current_override_state",
    "load_override_set_version",
    "override_set_identity",
    "package_slug",
    "patch_from_payload",
    "patch_payload",
    "resolve_effective_binding",
    "resolve_package_reference",
    "retain_override_set",
]
