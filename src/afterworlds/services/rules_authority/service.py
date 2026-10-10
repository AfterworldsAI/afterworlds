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

The obsolete ``MechanicalEntity`` authority path and the legacy chunk/entity
overrides were retired at the final CRD Issue 5d cutover (#137 contract 6,
AC22). The production rule-slice path
(``RulesPackageService.get_active_rule_slice``) reads through this service, so
there is one runtime mechanical authority and no legacy fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.models import SemanticDisposition
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    ProjectionNotPersistedError,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import ProjectionCandidate
from afterworlds.ingestion.mechanical.reference_resolution import (
    AlternativeSelection,
    routes,
    select_alternatives,
)
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceRole,
    ProvenanceTargetKind,
    ReferenceDraft,
    RelationshipKind,
    reference_target_key,
    relationship_target_key,
)
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.orm.corpus import LedgerLeafORM
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
    #: :meth:`RulesAuthorityService.citation_view` only: each surviving route's
    #: label and its ``(record, component)`` destinations in reading order --
    #: landing first -- with ``""`` for a whole record. The view carries their
    #: effective text.
    routes: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()


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
        candidate = self._reconstruct(binding)
        return apply_override_set(
            candidate,
            state,
            binding,
            leaf_order=source_leaf_order(self._session, candidate),
        )

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
        return self._narrow(result, authority, request)

    def _narrow(
        self,
        result: AuthorityResult,
        authority: EffectiveAuthority,
        request: RuleSliceRequest,
    ) -> tuple[AuthorityResult, EffectiveAuthority | None]:
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
        keys = {record.semantic_key for record in selected}
        # A section narrowed to one component was not read as a catalogue.
        read = {
            container
            for container, found in authority.members
            if container in keys and keys.issuperset(found)
        }
        return result, replace(
            authority,
            records=selected,
            members=tuple(m for m in authority.members if m[0] in read),
            readings=tuple(r for r in authority.readings if r[0] in read),
        )

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

    def citation_view(
        self,
        request: RuleSliceRequest,
        *,
        citation: tuple[str, str, str, str],
        selection: AlternativeSelection,
    ) -> AuthorityResult:
        """The GameMaster view of where one resolved citation sends a reader.

        A reader, not a builder: *citation* is ``(from_record_key,
        from_component_key, source_text, scope_key)``, and the routes it states
        in the bound projection are filtered by
        :func:`~afterworlds.ingestion.mechanical.reference_resolution.select_alternatives`
        — every route *selection* does not rule out survives, since routes are
        not exclusive. Their destinations are then read through the ordinary
        selectors, so overrides apply and a disabled or missing destination is
        ``INVALID_REFERENCE``, exactly as for any other read. *request* supplies
        the package and any recorded binding; its own selectors are replaced.
        The view lists the surviving routes in their stated order, each route's
        landing before its supporting text, and each destination in its own
        source order.

        Refused: a citation the projection does not state, or states unresolved,
        or whose citing passage the effective source no longer reads (its
        record, component or prose disabled or replaced), is
        ``INVALID_REFERENCE``; one whose every route *selection* rules out is
        ``INVALID_SELECTOR``.
        """
        whole = request.model_copy(
            update={
                "whole_package": True,
                "record_selectors": (),
                "component_selectors": (),
            }
        )
        result, authority = self._resolve_authority(whole)
        if authority is None:
            return result
        assert result.binding is not None
        # ponytail: a second reconstruct for the references the effective
        # authority does not carry; thread the candidate out if reads get hot.
        candidate = self._reconstruct(result.binding)
        representation = candidate.representation
        stated = [
            ref
            for ref in representation.references
            if (
                ref.from_record_key,
                ref.from_component_key,
                ref.source_text,
                ref.scope_key,
            )
            == citation
        ]
        if not stated or not all(ref.target_record_key for ref in stated):
            return AuthorityResult(
                AuthorityOutcome.INVALID_REFERENCE,
                binding=result.binding,
                detail=f"the bound projection states no resolved citation {citation!r}",
            )
        if not _citation_in_effect(citation, stated, candidate, authority):
            return AuthorityResult(
                AuthorityOutcome.INVALID_REFERENCE,
                binding=result.binding,
                detail=f"the effective source no longer states citation {citation!r}",
            )
        kept = routes(select_alternatives(stated, selection))
        if not kept:
            return AuthorityResult(
                AuthorityOutcome.INVALID_SELECTOR,
                binding=result.binding,
                detail=f"the selection rules out every route of {citation!r}",
            )
        destinations = [
            (ref.target_record_key, ref.target_component_key)
            for _, members in kept
            for ref in members
        ]
        narrowed = request.model_copy(
            update={
                "whole_package": False,
                "record_selectors": tuple(
                    dict.fromkeys(r for r, c in destinations if not c)
                ),
                "component_selectors": tuple(
                    dict.fromkeys((r, c) for r, c in destinations if c)
                ),
            }
        )
        narrowed_result, scoped = self._narrow(result, authority, narrowed)
        if scoped is None:
            return narrowed_result
        view = build_gamemaster_view(scoped, self._prose_for(result.binding, scoped))
        # Routes read in their stated order, landing first: each component is
        # placed at the first destination that reads it. The sort is stable,
        # so within a destination the view keeps its own source order.
        rank: dict[tuple[str, str], int] = {}
        for index, (record_key, component_key) in enumerate(destinations):
            if component_key:
                rank.setdefault((record_key, component_key), index)
                continue
            one = narrowed.model_copy(
                update={"record_selectors": (record_key,), "component_selectors": ()}
            )
            for record in _select(authority, one)[0]:
                for component in record.components:
                    rank.setdefault(
                        (record.semantic_key, component.semantic_key), index
                    )
        view = replace(
            view,
            components=tuple(
                sorted(
                    view.components,
                    key=lambda c: rank.get(
                        (c.record_key, c.component_key), len(destinations)
                    ),
                )
            ),
        )
        return AuthorityResult(
            AuthorityOutcome.RESOLVED,
            binding=result.binding,
            gamemaster_view=view,
            routes=tuple(
                (
                    label,
                    tuple(
                        (ref.target_record_key, ref.target_component_key)
                        for ref in members
                    ),
                )
                for label, members in kept
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
        return apply_override_set(
            candidate,
            state,
            recorded,
            leaf_order=source_leaf_order(self._session, candidate),
        )


def _citation_in_effect(
    citation: tuple[str, str, str, str],
    stated: list[ReferenceDraft],
    candidate: ProjectionCandidate,
    authority: EffectiveAuthority,
) -> bool:
    """Whether the effective source still states *citation* (ADR-005d Decision 7).

    A citation is the source's, so it is in effect while the effective source
    still reads the passage that states it, and refused only once the citing
    record, component or prose is disabled or replaced. Appending prose or
    editing a fact leaves the passage, and the citation with it. Each citing
    span is retained by its own original source owner:

    * a span bound as governing prose must still be carried as effective
      ``SourceProse`` of the citing record or component;
    * an unbound ``SUPPORTING_AUTHORITY`` span is the citation owner's own
      explanatory text. It is retained while that owner is present and not
      supplied by an override: the record for a record-owned citation, the
      citing component for a component-owned one. A sibling's contextual
      provenance on the same span is not consulted, so the citation gains no
      dependency on a sibling;
    * an unbound ``SUBSTANTIVE`` span is structured authority. It is retained
      while its unique PRIMARY component owner, which must be the citing
      component or, for a record-owned citation, a component of the citing
      record, is present, not override-supplied and still claims the span.

    A replaced owner is refused by its supplier identity, not by span
    membership: a record REPLACE deliberately keeps the replaced record's old
    span ids while naming its supplier, so span ids alone would still match.
    An owner key that is not exactly ``(record, component)`` is malformed
    persisted state and is refused rather than unpacked. Any other disposition,
    an absent or ambiguous owner, or a supplied owner is refused, as before.
    """
    record_key, component_key = citation[0], citation[1]
    representation = candidate.representation
    keys = {reference_target_key(ref) for ref in stated}
    cited = {
        claim.span_id
        for claim in representation.provenance
        if claim.target_kind is ProvenanceTargetKind.REFERENCE
        and claim.target_key in keys
    }
    source = [r for r in authority.records if r.semantic_key == record_key]
    carried = {
        entry.span_id
        for record in source
        for component in record.components
        if not component_key or component.semantic_key == component_key
        for entry in component.governing_prose
        if isinstance(entry, SourceProse)
    }
    bound = {binding.span_id for binding in representation.prose_bindings}
    if not cited or not cited & bound <= carried:
        return False
    unbound = cited - bound
    if not unbound:
        return True
    if not source or any(r.supplied_by_override_id is not None for r in source):
        return False

    components = {c.semantic_key: c for r in source for c in r.components}

    def original(key: str) -> EffectiveComponent | None:
        component = components.get(key)
        if component is None or component.supplied_by_override_id is not None:
            return None
        return component

    disposition = {s.span_id: s.disposition for s in candidate.classification.spans}
    owners: dict[str, set[tuple[str, ...]]] = {}
    for claim in representation.provenance:
        if (
            claim.target_kind is ProvenanceTargetKind.COMPONENT
            and claim.role is ProvenanceRole.PRIMARY
        ):
            owners.setdefault(claim.span_id, set()).add(tuple(claim.target_key))

    for span_id in unbound:
        kind = disposition.get(span_id)
        if kind is SemanticDisposition.SUPPORTING_AUTHORITY:
            if component_key and original(component_key) is None:
                return False
        elif kind is SemanticDisposition.SUBSTANTIVE:
            owner = owners.get(span_id, set())
            if len(owner) != 1:
                return False
            (owner_key,) = owner
            if len(owner_key) != 2:
                return False
            owner_record, owner_component = owner_key
            if owner_record != record_key or (
                component_key and owner_component != component_key
            ):
                return False
            retained = original(owner_component)
            if retained is None or span_id not in retained.span_ids:
                return False
        else:
            return False
    return True


def source_leaf_order(
    session: Session, candidate: ProjectionCandidate
) -> dict[str, int]:
    """The bound release's reading order for every leaf a prose binding cites.

    Also every leaf a ``CATALOGUE_MEMBER`` edge's provenance cites, because
    that span is where the member is printed and is what members are ordered
    by. No other relationship kind is read.

    Read from the release's own persisted ledger: ``occurrence_index`` is the
    leaf's global emission order, the coordinate 5c reconstruction restores
    chunk order by and the one its digests bind. Scoped to the projection's own
    package, because leaf identities are content-derived and another release
    may hold the same leaf at a different position.

    A cited leaf with no ledger row means the persisted state no longer
    describes the projection, so it fails as reconstruction rather than
    presenting passages in some other order.
    """
    located = {span.span_id: span.leaf_id for span in candidate.classification.spans}
    cited: set[str] = set()
    for binding in candidate.representation.prose_bindings:
        leaf_id = located.get(binding.span_id)
        if leaf_id is None:
            raise PersistedStateReconstructionError(
                f"prose binding {binding.record_key}/{binding.component_key} cites "
                f"span {binding.span_id}, which the projection does not classify"
            )
        cited.add(leaf_id)
    catalogue = {
        relationship_target_key(rel)
        for rel in candidate.representation.relationships
        if rel.kind is RelationshipKind.CATALOGUE_MEMBER
    }
    for claim in candidate.representation.provenance:
        if (
            claim.target_kind is ProvenanceTargetKind.RELATIONSHIP
            and claim.target_key in catalogue
        ):
            leaf_id = located.get(claim.span_id)
            if leaf_id is None:
                raise PersistedStateReconstructionError(
                    f"catalogue membership {list(claim.target_key)} cites span "
                    f"{claim.span_id}, which the projection does not classify"
                )
            cited.add(leaf_id)
    if not cited:
        return {}
    rows = session.execute(
        select(LedgerLeafORM.leaf_id, LedgerLeafORM.occurrence_index).where(
            LedgerLeafORM.package_uuid == candidate.binding.package_uuid,
            LedgerLeafORM.leaf_id.in_(sorted(cited)),
        )
    ).all()
    order = {leaf_id: index for leaf_id, index in rows}
    if len(order) != len(rows):
        raise PersistedStateReconstructionError(
            f"release {candidate.binding.package_uuid} holds a cited leaf twice"
        )
    if missing := sorted(cited - order.keys()):
        raise PersistedStateReconstructionError(
            f"release {candidate.binding.package_uuid} has no ledger leaf for "
            f"cited leaves {missing}"
        )
    return order


def _select(
    authority: EffectiveAuthority, request: RuleSliceRequest
) -> tuple[tuple[EffectiveRecord, ...], set[str]]:
    """Apply the request's deterministic selectors to *authority*.

    A record selector takes the whole record; a component selector takes exactly
    the named components. Selecting a record and one of its components yields
    the whole record — the broader selector wins rather than the last one
    written, so selector order cannot change what a slice contains.

    A record selector also takes the records the effective authority lists as
    that record's members, one hop and whole: naming a catalogue section names
    the entries it prints, each read as its own effective record -- replaced as
    replaced, and absent when disabled -- and never again by the section; and
    of a member's member, only the parts it prints through that member
    (Owner Decision 2026-09-27), so the item's own authority reads there. A
    component selector narrows and so never expands. Membership decides only
    what is read; each member keeps its own eligibility and prerequisites.

    Selected records list in key order, and a section's reached members follow
    it in printed order; a member selected with its section is listed once.
    The GameMaster view reads the section's own passages and its members
    interleaved as the source prints them (Owner Decision 2026-09-24). A
    record's components keep the order the effective authority reads them in,
    narrowed or not. Neither depends on selector order.
    """
    by_key = {record.semantic_key: record for record in authority.records}
    members = dict(authority.members)
    readings = dict(authority.readings)
    missing: set[str] = set()
    whole: set[str] = set()
    reached: dict[str, tuple[str, ...]] = {}
    partial: dict[str, dict[str, EffectiveComponent]] = {}

    for record_key in request.record_selectors:
        if record_key not in by_key:
            missing.add(f"record {record_key!r}")
            continue
        whole.add(record_key)
        found: list[str] = []
        for member in members.get(record_key, ()):
            if member not in by_key:
                missing.add(f"member {member!r} of record {record_key!r}")
                continue
            whole.add(member)
            found.append(member)
        # What the section reads of a member's member -- the parts it prints
        # through that member -- narrowed to those parts.
        for run_key, key, _ in readings.get(record_key, ()):
            if run_key == record_key or run_key in members.get(record_key, ()):
                continue
            (part,) = [c for c in by_key[run_key].components if c.semantic_key == key]
            partial.setdefault(run_key, {})[key] = part
            if run_key not in found:
                found.append(run_key)
        reached[record_key] = tuple(found)

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

    order: dict[str, None] = {}

    def place(key: str) -> None:
        if key not in order:
            order[key] = None
            for member in reached.get(key, ()):
                place(member)

    keys = sorted(whole | set(partial))
    follows = {member for found in reached.values() for member in found}
    for key in keys:
        if key not in follows:
            place(key)
    for key in keys:  # anything reachable only through a membership cycle
        place(key)

    selected = tuple(
        (
            by_key[key]
            if key in whole
            else replace(
                by_key[key],
                components=tuple(
                    c for c in by_key[key].components if c.semantic_key in partial[key]
                ),
            )
        )
        for key in order
    )
    return selected, missing
