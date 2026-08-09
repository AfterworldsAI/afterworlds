"""The runtime mechanical-authority seam — CRD Issue 5d, contract 6.

One service, and every runtime read of mechanical authority goes through it:
binding resolution, rule slices, the deterministic-consumer view, the GameMaster
authority view, and audit replay. Each returns a typed result carrying the
complete four-component effective binding that produced it, or a typed refusal.
Nothing returns ``None``, an empty collection, or a bare exception to mean
"no authority" (#137 contract 5).

**Runtime and replay are different operations, and this is where that shows.**

* :meth:`RulesAuthorityService.resolve` and the view methods recompute the
  override-set identity from *current* override state. A recorded binding that
  no longer matches is ``STALE`` and fails; it is never silently re-resolved
  against current overrides.
* :meth:`RulesAuthorityService.replay` resolves the *retained* immutable
  override-set version named by the recorded binding and reconstructs the exact
  effective authority originally applied — after the current override rows have
  been edited, disabled, reprioritized, retargeted, or deleted. ``STALE`` is not
  a possible answer there; a failure to reconstruct is a retention defect and
  raises rather than returning an outcome an auditor could read as ordinary
  divergence.

The obsolete ``MechanicalEntity`` authority path is untouched by this module.
Nothing here reads it, falls back to it, or combines with it: a caller resolves
either the typed mechanical authority below or the legacy slice, never a mixture
of the two.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    ProjectionNotPersistedError,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import ProjectionCandidate
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveRecord,
    OverrideApplicationError,
    SourceProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.binding import (
    BindingResolution,
    resolve_effective_binding,
    resolve_package_reference,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import EffectiveOverrideSet
from afterworlds.services.rules_authority.retention import load_override_set_version
from afterworlds.services.rules_authority.views import (
    GameMasterAuthorityView,
    TypedAuthorityView,
    build_gamemaster_view,
    build_typed_view,
)

__all__ = [
    "AuthorityResult",
    "IncoherentBindingError",
    "MechanicalRuleSlice",
    "RulesAuthorityService",
]


class IncoherentBindingError(RuntimeError):
    """Raised when a recorded binding's four components describe two authorities.

    Distinct from ``STALE``, which means the world moved on from a coherent
    binding. This means the binding was never coherent: its projection was built
    over a different package or release than the binding names, so replaying it
    would label one package's mechanics with another's provenance.
    """


@dataclass(frozen=True)
class MechanicalRuleSlice:
    """A deterministic selection of the effective mechanical authority.

    Carries the complete effective binding, so a slice can always state which
    base projection and which override set produced it — the ambiguity
    ADR-005d Decision 9 exists to remove.
    """

    binding: RulesPackageBinding
    records: tuple[EffectiveRecord, ...]
    whole_package: bool


@dataclass(frozen=True)
class AuthorityResult:
    """One typed authority read.

    Exactly one of the payload fields is populated, and only when ``outcome`` is
    ``RESOLVED``. ``binding`` is populated alongside every successful read and,
    where resolution got far enough to know it, alongside a refusal too.
    """

    outcome: AuthorityOutcome
    binding: RulesPackageBinding | None = None
    slice: MechanicalRuleSlice | None = None
    typed_view: TypedAuthorityView | None = None
    gamemaster_view: GameMasterAuthorityView | None = None
    detail: str = ""


class RulesAuthorityService:
    """Typed runtime reads of a package's effective mechanical authority."""

    def __init__(self, session: Session, *, now: str) -> None:
        self._session = session
        # Retention records when a version was first observed. It is audit
        # metadata on the version row and never reaches the identity, so a
        # caller-supplied clock cannot change what a binding resolves to.
        self._now = now

    # -- Binding ------------------------------------------------------------

    def resolve(
        self,
        *,
        package_uuid: UUID | None = None,
        package_reference: str | None = None,
        expected_release: str | None = None,
        recorded: RulesPackageBinding | None = None,
        retain: bool = True,
    ) -> BindingResolution:
        """Resolve the effective binding from a UUID or a human-facing slug.

        Both forms funnel into the same code-owned path: a slug is resolved to a
        package UUID first and never becomes authority itself, so a valid slug
        and the matching UUID resolve to the same exact binding.
        """
        if (package_uuid is None) == (package_reference is None):
            return BindingResolution(
                AuthorityOutcome.INVALID_SELECTOR,
                detail=(
                    "exactly one of package_uuid or package_reference must be "
                    "supplied"
                ),
            )
        if package_uuid is None:
            assert package_reference is not None
            resolved = resolve_package_reference(self._session, package_reference)
            if resolved.outcome is not AuthorityOutcome.RESOLVED:
                return BindingResolution(resolved.outcome, detail=resolved.detail)
            assert resolved.package_uuid is not None
            package_uuid = resolved.package_uuid

        return resolve_effective_binding(
            self._session,
            package_uuid,
            now=self._now,
            expected_release=expected_release,
            recorded=recorded,
            retain=retain,
        )

    # -- Effective authority ------------------------------------------------

    def _reconstruct(self, binding: RulesPackageBinding) -> ProjectionCandidate:
        return reconstruct_candidate(
            self._session, str(binding.mechanical_projection_uuid)
        )

    def _effective(
        self, binding: RulesPackageBinding, state: EffectiveOverrideSet
    ) -> EffectiveAuthority:
        return apply_override_set(self._reconstruct(binding), state, binding)

    def _resolve_authority(
        self, request: RuleSliceRequest
    ) -> tuple[AuthorityResult, EffectiveAuthority | None]:
        """Shared front half: resolve the binding, then apply the override set.

        Returns the refusal and no authority, or a placeholder result and the
        effective authority. Both view methods and the slice method use it, so
        all three refuse identically and none can drift into a softer failure.
        """
        if request.package_id is not None:
            resolution = self.resolve(
                package_uuid=request.package_id,
                recorded=request.recorded_binding,
            )
        else:
            assert request.package_slug is not None
            resolution = self.resolve(
                package_reference=request.package_slug,
                recorded=request.recorded_binding,
            )
        if resolution.outcome is not AuthorityOutcome.RESOLVED:
            return (
                AuthorityResult(
                    resolution.outcome,
                    binding=resolution.current_binding,
                    detail=resolution.detail,
                ),
                None,
            )

        assert resolution.binding is not None
        assert resolution.override_state is not None
        binding = resolution.binding
        try:
            authority = self._effective(binding, resolution.override_state)
        except OverrideApplicationError as exc:
            return (
                AuthorityResult(
                    AuthorityOutcome.INVALID_OVERRIDE,
                    binding=binding,
                    detail=exc.detail,
                ),
                None,
            )
        except (ProjectionNotPersistedError, PersistedStateReconstructionError) as exc:
            # The activation row named a projection whose persisted state no
            # longer rebuilds. That is exactly what STALE means here: the
            # authority is not what the record says it is.
            return (
                AuthorityResult(
                    AuthorityOutcome.STALE, binding=binding, detail=str(exc)
                ),
                None,
            )
        return AuthorityResult(AuthorityOutcome.RESOLVED, binding=binding), authority

    # -- Rule slice ---------------------------------------------------------

    def rule_slice(self, request: RuleSliceRequest) -> AuthorityResult:
        """Resolve a deterministic slice of the effective mechanical authority.

        Selection is deterministic lookup against the exact semantic keys the
        request names, or the explicit ``whole_package`` flag. A selector naming
        an element the bound projection does not contain is
        ``INVALID_REFERENCE`` — not an empty slice, which would read as "that
        rule does not apply".

        The accidentally-empty selector cannot reach this method: the request
        model refuses to construct without either a selector or the explicit
        flag.
        """
        result, scoped = self._scoped_authority(request)
        if scoped is None:
            return result
        assert result.binding is not None
        return AuthorityResult(
            AuthorityOutcome.RESOLVED,
            binding=result.binding,
            slice=MechanicalRuleSlice(
                binding=result.binding,
                records=scoped.records,
                whole_package=request.whole_package,
            ),
        )

    def _scoped_authority(
        self, request: RuleSliceRequest
    ) -> tuple[AuthorityResult, EffectiveAuthority | None]:
        """Resolve the effective authority and narrow it to the request.

        One resolution shared by the slice and both views, so a slice and the
        views built for the same request cannot disagree — and so resolution,
        which retains an override-set version, happens once per read rather than
        once per surface.
        """
        result, authority = self._resolve_authority(request)
        if authority is None:
            return result, None
        assert result.binding is not None
        if request.whole_package:
            return result, authority
        selected, missing = _select(authority, request)
        if missing:
            return (
                AuthorityResult(
                    AuthorityOutcome.INVALID_REFERENCE,
                    binding=result.binding,
                    detail="the bound projection contains no "
                    + "; ".join(sorted(missing)),
                ),
                None,
            )
        return result, replace(authority, records=selected)

    # -- Views --------------------------------------------------------------

    def typed_view(self, request: RuleSliceRequest) -> AuthorityResult:
        """The deterministic-consumer view over the requested authority."""
        result, scoped = self._scoped_authority(request)
        if scoped is None:
            return result
        return AuthorityResult(
            AuthorityOutcome.RESOLVED,
            binding=result.binding,
            typed_view=build_typed_view(scoped),
        )

    def gamemaster_view(self, request: RuleSliceRequest) -> AuthorityResult:
        """The GameMaster authority view over the requested authority.

        Governing prose is read from the authoritative 5c ``RuleChunk`` records
        of the bound package, by the exact chunk identity the projection
        recorded. No retrieval, similarity, or model selection participates.
        """
        result, scoped = self._scoped_authority(request)
        if scoped is None:
            return result
        assert result.binding is not None
        return AuthorityResult(
            AuthorityOutcome.RESOLVED,
            binding=result.binding,
            gamemaster_view=build_gamemaster_view(
                scoped, self._prose_for(result.binding, scoped)
            ),
        )

    def _prose_for(
        self, binding: RulesPackageBinding, authority: EffectiveAuthority
    ) -> dict[str, str]:
        # Only SourceProse entries name a 5c chunk to resolve; AuthoredProse
        # entries already carry their exact text (Owner Decision 2026-08-08).
        chunk_ids = {
            entry.chunk_id
            for record in authority.records
            for component in record.components
            for entry in component.governing_prose
            if isinstance(entry, SourceProse)
        }
        if not chunk_ids:
            return {}
        rows = (
            self._session.execute(
                select(RuleChunkORM).where(
                    RuleChunkORM.rules_package_id == str(binding.package_uuid),
                    RuleChunkORM.chunk_id.in_(sorted(chunk_ids)),
                )
            )
            .scalars()
            .all()
        )
        return {row.chunk_id: row.content for row in rows}

    # -- Audit and replay ---------------------------------------------------

    def replay(self, recorded: RulesPackageBinding) -> EffectiveAuthority:
        """Reconstruct the exact effective authority a recorded binding named.

        Resolves the retained immutable override-set version rather than current
        override rows, so this keeps working — and keeps returning the *original*
        authority — after those rows are edited, disabled, reprioritized,
        retargeted, or deleted.

        Raises rather than returning an outcome. ``STALE`` is not a valid answer
        to a replay: divergence from current state is expected and is the whole
        point. A version that cannot be resolved is a retention defect
        (:class:`OverrideSetRetentionError`), a projection that cannot be
        reconstructed is a persistence defect, and a binding whose components do
        not describe one authority is an :class:`IncoherentBindingError`. None of
        the three is a divergence signal.

        **The four components are checked against each other, not just resolved
        individually.** The override set and the projection are loaded from
        different tables by different identities, so nothing about loading both
        proves they belong together — and because the override-set identity is
        content-derived and package-independent, the empty set is legitimately
        shared by every package. A binding that paired package B with package A's
        projection would otherwise replay A's mechanics under B's provenance,
        which is exactly the ambiguity the four-component binding exists to
        remove.
        """
        candidate = self._reconstruct(recorded)
        bound = candidate.binding
        if bound.package_uuid != str(recorded.package_uuid):
            raise IncoherentBindingError(
                f"recorded binding names package {recorded.package_uuid}, but "
                f"projection {recorded.mechanical_projection_uuid} was built over "
                f"package {bound.package_uuid}"
            )
        if bound.release_version != recorded.release_version:
            raise IncoherentBindingError(
                f"recorded binding names release {recorded.release_version!r}, but "
                f"projection {recorded.mechanical_projection_uuid} was built over "
                f"release {bound.release_version!r}"
            )
        state = load_override_set_version(
            self._session,
            str(recorded.override_set_uuid),
            package_uuid=str(recorded.package_uuid),
            release_version=recorded.release_version,
        )
        return apply_override_set(candidate, state, recorded)


def _select(
    authority: EffectiveAuthority, request: RuleSliceRequest
) -> tuple[tuple[EffectiveRecord, ...], set[str]]:
    """Apply the request's deterministic selectors to *authority*.

    A record selector takes the whole record; a component selector takes exactly
    the named components. Selecting a record and one of its components yields
    the whole record — the broader selector wins rather than the last one
    written, so selector order cannot change what a slice contains.
    """
    by_key = {record.semantic_key: record for record in authority.records}
    missing: set[str] = set()
    whole: set[str] = set()
    partial: dict[str, dict[str, EffectiveComponent]] = {}

    for record_key in request.record_selectors:
        if record_key not in by_key:
            missing.add(f"record {record_key!r}")
            continue
        whole.add(record_key)

    for record_key, component_key in request.component_selectors:
        record = by_key.get(record_key)
        if record is None:
            missing.add(f"record {record_key!r}")
            continue
        chosen = [c for c in record.components if c.semantic_key == component_key]
        if not chosen:
            missing.add(f"component {component_key!r} of record {record_key!r}")
            continue
        partial.setdefault(record_key, {})[component_key] = chosen[0]

    selected = tuple(
        (
            by_key[key]
            if key in whole
            else replace(
                by_key[key],
                components=tuple(
                    sorted(partial[key].values(), key=lambda c: c.semantic_key)
                ),
            )
        )
        for key in sorted(whole | set(partial))
    )
    return selected, missing
