"""Rules Package service — the production rule-slice path and source-corpus reads.

Rule slice (play time)
----------------------
:meth:`RulesPackageService.get_active_rule_slice` is the existing production
path the Context Builder consumes, extended at the final CRD Issue 5d cutover
(#137 contract 6). It takes the supplying :class:`RuleSliceRequest` whole —
package reference, record/component selectors, ``whole_package`` and any
recorded binding — reads the accepted typed mechanical authority through
:class:`~afterworlds.services.rules_authority.RulesAuthorityService`, and
returns a slice that names the exact four-part effective binding. Every
refusal is typed and fails closed: a non-resolving reference, an empty
selector set, a stale recorded binding or a missing selected element raises
:class:`RuleSliceResolutionError` with its :class:`AuthorityOutcome`, and a
quarantined identity raises
:class:`~afterworlds.quarantine.QuarantinedAuthorityError`. Nothing returns an
empty slice to mean "no rule applies".

Source-corpus reads (informational)
-----------------------------------
:meth:`get_package_by_id` and :meth:`get_chunks_by_subsystem` read the
authoritative 5c source records (``RulesPackage``, ``RuleSource``,
``RuleChunk``). They are informational/administrative reads of source text and
metadata, never mechanical authority: governing prose reaches a consumer only
through the projection's exact prose binding.

The obsolete prose-only ``MechanicalEntity`` family and the legacy chunk/entity
override authority (``rp_mechanical_entities``, ``rp_overrides``) were retired
at the same cutover (AC22); this module no longer reads, applies or falls back
to either.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    PublicationStatusEnum,
    RuleSourceCategoryEnum,
    RulesSystemEnum,
    RuleSubsystemEnum,
    SourceLocatorTypeEnum,
)
from afterworlds.models.rules_package import (
    ActiveRuleSlice,
    ChunksResult,
    RuleChunk,
    RuleSliceRequest,
    RuleSource,
    RulesPackageDetail,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.quarantine import refuse_quarantined
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.service import RulesAuthorityService
from afterworlds.services.rules_authority.views import render_gamemaster_view


class RuleSliceResolutionError(ValueError):
    """Raised when a rule-slice request's package reference does not resolve.

    Carries the typed :class:`AuthorityOutcome` so a caller reports *why* — an
    invalid selector, an ambiguous slug, or an absent package — rather than
    collapsing three distinct states into one failure string.
    """

    def __init__(self, outcome: AuthorityOutcome, detail: str) -> None:
        super().__init__(detail)
        self.outcome = outcome
        self.detail = detail


# ---------------------------------------------------------------------------
# Module-level helpers — ORM row → Pydantic model conversion
# These are pure functions with no side effects.
# ---------------------------------------------------------------------------


def _orm_to_package_detail(
    row: RulesPackageORM, sources: list[RuleSource]
) -> RulesPackageDetail:
    return RulesPackageDetail(
        rules_package_id=UUID(row.rules_package_id),
        name=row.name,
        system=RulesSystemEnum(row.system),
        version=row.version,
        is_enabled=row.is_enabled,
        publication_status=PublicationStatusEnum(row.publication_status),
        published_at=(
            datetime.fromisoformat(row.published_at) if row.published_at else None
        ),
        created_at=datetime.fromisoformat(row.created_at),
        updated_at=datetime.fromisoformat(row.updated_at),
        sources=sources,
    )


def _orm_to_source(row: RuleSourceORM) -> RuleSource:
    return RuleSource(
        source_id=UUID(row.source_id),
        rules_package_id=UUID(row.rules_package_id),
        name=row.name,
        category=RuleSourceCategoryEnum(row.category),
        precedence_rank=row.precedence_rank,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


def _orm_to_chunk(row: RuleChunkORM) -> RuleChunk:
    return RuleChunk(
        chunk_id=UUID(row.chunk_id),
        rules_package_id=UUID(row.rules_package_id),
        source_id=UUID(row.source_id),
        subsystem=RuleSubsystemEnum(row.subsystem),
        content=row.content,
        source_document=row.source_document,
        source_locator_type=SourceLocatorTypeEnum(row.source_locator_type),
        source_locator_value=row.source_locator_value,
        source_section_label=row.source_section_label,
        is_enabled=row.is_enabled,
        created_at=datetime.fromisoformat(row.created_at),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RulesPackageService:
    """The production rule-slice path plus informational source-corpus reads.

    Source records (RuleChunk) are never modified by this service.
    """

    def __init__(self, session: Session, *, now: str | None = None) -> None:
        self._session = session
        # Audit metadata for override-set retention only (ADR-005d Decision 9);
        # it never reaches an identity. ``None`` reads the clock per call.
        self._now = now

    # -- Accessibility helpers ----------------------------------------------

    def _package_accessible(
        self, row: RulesPackageORM, include_non_published: bool
    ) -> bool:
        """Return True if *row* is accessible under the given query policy.

        Both source-corpus reads route through here, so the Recorded Owner
        Decision 2026-09-21 quarantine is enforced once, at the point where a row
        becomes readable content. (The rule slice is refused by the typed
        binding path itself.)

        It raises rather than returning False. An empty chunk list or a ``None``
        package is what "nothing configured" looks like, so a silent exclusion
        here would be the fail-open shape the quarantine exists to remove. The
        refusal ignores ``include_non_published``: this service has no reference
        or diagnostic mode, so a draft read of a quarantined package is still
        this subsystem answering an authority question about it.
        """
        refuse_quarantined(
            "rules package read",
            package_uuid=row.rules_package_id,
            release_version=row.version,
        )
        if not row.is_enabled:
            return False
        if not include_non_published:
            return row.publication_status == PublicationStatusEnum.PUBLISHED.value
        return True

    def _enabled_source_ids_for_package(self, package_id: UUID) -> list[str]:
        """Return string source IDs for all enabled sources in *package_id*."""
        rows = (
            self._session.execute(
                select(RuleSourceORM.source_id).where(
                    RuleSourceORM.rules_package_id == str(package_id),
                    RuleSourceORM.is_enabled == True,  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    # -- Public read methods ------------------------------------------------

    def get_package_by_id(
        self,
        package_id: UUID,
        include_non_published: bool = False,
    ) -> RulesPackageDetail | None:
        """Fetch full package metadata including its RuleSource records.

        Returns None if the package does not exist or is not accessible under
        the current query policy.

        Administrative/internal callers may pass ``include_non_published=True``
        to access draft packages during ingestion validation and publication
        flow support (CRD Issue 5b).
        """
        row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if row is None:
            return None
        if not self._package_accessible(row, include_non_published):
            return None

        source_rows = (
            self._session.execute(
                select(RuleSourceORM)
                .where(
                    RuleSourceORM.rules_package_id == str(package_id),
                    RuleSourceORM.is_enabled == True,  # noqa: E712
                )
                .order_by(RuleSourceORM.precedence_rank, RuleSourceORM.source_id)
            )
            .scalars()
            .all()
        )
        sources = [_orm_to_source(src) for src in source_rows]
        return _orm_to_package_detail(row, sources)

    def get_chunks_by_subsystem(
        self,
        package_id: UUID,
        subsystem: RuleSubsystemEnum,
        include_non_published: bool = False,
    ) -> ChunksResult:
        """Retrieve source rule chunks for a package/subsystem.

        Informational/administrative source-corpus read: chunk text is source
        material, not mechanical authority, and no rule-slice or adjudication
        path reads it from here. Respects package, RuleSource, and chunk
        enable/disable state; by default only published, enabled content is
        surfaced.
        """
        pkg_row = self._session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == str(package_id)
            )
        ).scalar_one_or_none()

        if pkg_row is None or not self._package_accessible(
            pkg_row, include_non_published
        ):
            return ChunksResult(package_id=package_id, subsystem=subsystem, chunks=[])

        enabled_source_ids = self._enabled_source_ids_for_package(package_id)
        if not enabled_source_ids:
            return ChunksResult(package_id=package_id, subsystem=subsystem, chunks=[])

        chunk_rows = (
            self._session.execute(
                select(RuleChunkORM)
                .join(
                    RuleSourceORM,
                    RuleChunkORM.source_id == RuleSourceORM.source_id,
                )
                .where(
                    RuleChunkORM.rules_package_id == str(package_id),
                    RuleChunkORM.subsystem == subsystem.value,
                    RuleChunkORM.is_enabled == True,  # noqa: E712
                    RuleChunkORM.source_id.in_(enabled_source_ids),
                )
                .order_by(RuleSourceORM.precedence_rank, RuleChunkORM.chunk_id)
            )
            .scalars()
            .all()
        )
        return ChunksResult(
            package_id=package_id,
            subsystem=subsystem,
            chunks=[_orm_to_chunk(r) for r in chunk_rows],
        )

    def get_active_rule_slice(self, request: RuleSliceRequest) -> ActiveRuleSlice:
        """Resolve *request* against the accepted typed mechanical authority.

        The request is used whole and unchanged: its package reference (UUID or
        human-facing slug, resolved by the one code-owned service), its
        deterministic record/component selectors or explicit ``whole_package``,
        and its ``recorded_binding``. A recorded binding that no longer matches
        current override state is ``STALE`` and refused — never silently
        re-resolved against current authority — and selectors are never
        widened.

        Returns an :class:`ActiveRuleSlice` carrying the exact four-part
        binding, the supplying request, the components read and the
        deterministic GameMaster authority rendering.

        Raises :class:`RuleSliceResolutionError` for every non-``RESOLVED``
        outcome, and :class:`~afterworlds.quarantine.QuarantinedAuthorityError`
        for a retired identity.

        Binding resolution retains the override-set version it resolved, in
        this service's session (ADR-005d Decision 9). The caller owns the
        commit, so the binding the slice names stays replayable.
        """
        # Retired identities are refused at the entry, before any lookup, so a
        # quarantined package reads as quarantined rather than as merely absent
        # when its rows are gone (Recorded Owner Decision 2026-09-21). The typed
        # binding path refuses it again where a row exists.
        recorded = request.recorded_binding
        refuse_quarantined(
            "active rule slice",
            package_uuid=request.package_id,
        )
        if recorded is not None:
            refuse_quarantined(
                "active rule slice",
                package_uuid=recorded.package_uuid,
                release_version=recorded.release_version,
                projection_uuid=recorded.mechanical_projection_uuid,
            )
        now = self._now or datetime.now(UTC).isoformat()
        result = RulesAuthorityService(self._session, now=now).gamemaster_view(request)
        if result.outcome is not AuthorityOutcome.RESOLVED:
            raise RuleSliceResolutionError(
                result.outcome,
                f"rule slice for {_reference(request)} did not resolve: "
                f"{result.outcome.value}"
                + (f" ({result.detail})" if result.detail else ""),
            )
        assert result.binding is not None
        assert result.gamemaster_view is not None
        view = result.gamemaster_view
        return ActiveRuleSlice(
            binding=result.binding,
            request=request,
            components=tuple((c.record_key, c.component_key) for c in view.components),
            authority_text=render_gamemaster_view(view),
        )


def _reference(request: RuleSliceRequest) -> str:
    if request.package_id is not None:
        return f"package {request.package_id}"
    return f"package reference {request.package_slug!r}"
