"""Pydantic models for the Rules Package — mechanical canon subsystem.

The Rules Package governs mechanical adjudication canon (rules, stats,
entities).  It is structurally separate from the Story Bible, which governs
narrative canon.

Architecture invariant: no field in these models carries a reference to
Story, Arc, Chapter, Node, Turn, or any Story Bible entity.  The Rules
Package is a standalone corpus with no cross-dependency on narrative state.

Final CRD Issue 5d cutover (#137 contract 6, AC22): the obsolete prose-only
``MechanicalEntity`` family (``SpellEntity``, ``ConditionEntity``,
``StatBlockEntity``, ``ActionEntity``, ``ItemEntity``, ``EntityData``) and the
legacy chunk/entity ``RuleOverride`` with its ``ChunkOverridePayload``,
``AppliedChunk`` and ``AppliedEntity`` are retired. Mechanical authority is the
accepted typed projection read through
:mod:`afterworlds.services.rules_authority`, and typed overrides live there.
``RuleSource``, ``RuleChunk``, ``RulesPackage`` and the manifest remain the
authoritative 5c source-corpus surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from afterworlds.models.enums import (
    PublicationStatusEnum,
    RuleSourceCategoryEnum,
    RulesSystemEnum,
    RuleSubsystemEnum,
    SourceLocatorTypeEnum,
)

# ---------------------------------------------------------------------------
# Source-document model — defined before RulesPackageDetail which references it
# ---------------------------------------------------------------------------


class RuleSource(BaseModel):
    """Source-document metadata within a RulesPackage.

    Records where rules came from to support traceability and explicit
    authority ordering.  Source records are immutable after creation.

    ``category`` classifies the source type.  ``precedence_rank`` determines
    authority ordering within the package.  These are separate concerns —
    do not infer winning-rule behaviour from ``category`` alone.
    """

    source_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    name: str
    category: RuleSourceCategoryEnum
    precedence_rank: int
    is_enabled: bool = True
    created_at: datetime


# ---------------------------------------------------------------------------
# Core package models
# ---------------------------------------------------------------------------


class RulesPackage(BaseModel):
    """Top-level Rules Package metadata record."""

    rules_package_id: UUID = Field(default_factory=uuid4)
    name: str
    system: RulesSystemEnum
    version: str
    is_enabled: bool = True
    publication_status: PublicationStatusEnum = PublicationStatusEnum.DRAFT
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RulesPackageDetail(BaseModel):
    """Full package metadata including its RuleSource records.

    Returned by ``RulesPackageService.get_package_by_id``.
    """

    rules_package_id: UUID
    name: str
    system: RulesSystemEnum
    version: str
    is_enabled: bool
    publication_status: PublicationStatusEnum
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sources: list[RuleSource]


# ---------------------------------------------------------------------------
# Atomic rule chunk
# ---------------------------------------------------------------------------


class RuleChunk(BaseModel):
    """Atomic unit of rule text within a RulesPackage.

    Source provenance is required and non-nullable.  There are no orphaned
    chunks — every chunk belongs to a named RuleSource.  Source records are
    immutable after creation.  A chunk is source text, not mechanical
    authority: governing prose reaches a consumer only through the typed
    projection's exact prose binding (#137 contract 6).
    """

    model_config = ConfigDict(frozen=True)

    chunk_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    source_id: UUID  # Required; no orphaned chunks
    subsystem: RuleSubsystemEnum
    content: str
    source_document: str  # Non-nullable provenance
    source_locator_type: SourceLocatorTypeEnum
    source_locator_value: str  # Non-nullable
    source_section_label: str | None = None
    is_enabled: bool = True
    created_at: datetime


# ---------------------------------------------------------------------------
# Service return types — stable named Pydantic models
# ---------------------------------------------------------------------------


class ChunksResult(BaseModel):
    """Return type for RulesPackageService.get_chunks_by_subsystem.

    Informational source-corpus read only; never mechanical authority.
    """

    package_id: UUID
    subsystem: RuleSubsystemEnum
    chunks: list[RuleChunk]


class RulesPackageManifest(BaseModel):
    """Manifest record for a RulesPackage — attribution, licensing, and gate flags.

    One manifest per package.  Publication is gated on ``sql_ingest_complete``
    and ``vector_write_complete`` both being True.
    """

    manifest_id: UUID = Field(default_factory=uuid4)
    rules_package_id: UUID
    authoritative_source_document: str  # e.g. "D&D SRD 5.2.1"
    authoritative_source_version: str  # e.g. "5.2.1"
    package_license: str  # e.g. "CC BY 4.0"
    transform_status: str  # description of transformation from source
    parsing_convenience_source: str | None = None  # markdown mirror identity if used
    attribution_text: str  # CC BY 4.0 attribution/change-indication text
    sql_ingest_complete: bool = False
    vector_write_complete: bool = False
    created_at: datetime
    updated_at: datetime


@dataclass
class IngestionConfig:
    """Configuration for a rules package ingestion run.

    Passed to ``IngestionService.ingest`` to parameterise the pipeline.
    """

    package_name: str
    package_version: str
    system: str = "d20"
    source_name: str = "SRD 5.2.1"
    source_category: str = "core_rulebook"
    source_precedence_rank: int = 1
    authoritative_source_document: str = "D&D SRD 5.2.1"
    authoritative_source_version: str = "5.2.1"
    package_license: str = "CC BY 4.0"
    transform_status: str = "Structured JSON derived from authoritative SRD PDF"
    parsing_convenience_source: str | None = None
    attribution_text: str = (
        "This work includes material from the Systems Reference Document 5.2.1 "
        "('SRD 5.2.1') by Wizards of the Coast LLC, available at "
        "https://www.dndbeyond.com/resources/1781-systems-reference-document-srd. "
        "The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 "
        "International License, available at "
        "https://creativecommons.org/licenses/by/4.0/legalcode."
    )
    extra_tags: list[str] = field(default_factory=list)


class RulesPackageBinding(BaseModel):
    """The exact four-component effective binding (ADR-005d Decision 9).

    ``mechanical_projection_uuid`` identifies the immutable base projection;
    ``override_set_uuid`` identifies the exact applied effective override set.
    The two are never collapsed into one value: an override change mints a new
    override-set identity and leaves the base projection identity untouched, and
    a binding that carried only one of them could resolve to different DCs,
    effects, or disabled mechanics over time.

    Every field is a ``UUID`` or an exact release string — never a slug, display
    name, or filename. A human-facing slug may resolve *to* a binding through
    one code-owned service, but it is never the binding itself.
    """

    model_config = ConfigDict(frozen=True)

    package_uuid: UUID
    release_version: str
    mechanical_projection_uuid: UUID
    override_set_uuid: UUID


class RuleSliceRequest(BaseModel):
    """Typed parameter bundle for RulesPackageService rule-slice reads.

    Introduced in Issue 8 (Context Builder) per the instruction to reuse this
    model from Issue 5a's namespace rather than creating a parallel model in
    the Context Builder.  The model was not defined during Issue 5a — it is
    added here now.  See PR Architecture Notes for scope rationale.

    CRD Issue 5d extends this same model rather than introducing a parallel
    request type (#137 contract 6).  These things changed:

    * **The package reference may be a UUID or a human-facing slug, and exactly
      one of them must be supplied.**  ``package_slug`` resolves through the one
      code-owned service in
      :mod:`afterworlds.services.rules_authority.binding`; it never becomes
      authority itself.  A caller that previously swallowed a non-UUID reference
      and silently omitted the request now states which form it holds.
    * **Deterministic mechanical selectors**, ``record_selectors`` and
      ``component_selectors``, name exact semantic keys in the bound projection.
    * **``whole_package`` is explicit.**  A request that selects nothing and
      does not set it is ``INVALID_SELECTOR`` — refused at construction, so the
      accidentally-empty selector cannot reach a service and come back as an
      empty result that reads like "no rules apply".
    * **The legacy selectors are gone** (final cutover).  ``subsystem_tags``,
      ``entity_refs`` and ``include_non_published`` selected obsolete chunk and
      ``MechanicalEntity`` content and had no meaning on the typed path;
      accepting and then ignoring them would let a request read as selecting
      something it does not.  A request built from them alone now fails as an
      empty selector set.
    """

    #: ``extra="forbid"``: a retired selector (``subsystem_tags``,
    #: ``entity_refs``, ``include_non_published``) or any other unknown field is
    #: refused rather than silently dropped.
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_id: UUID | None = None
    package_slug: str | None = None

    #: A previously recorded binding to revalidate.  Supplied by a consumer that
    #: stored one; runtime resolution reports ``STALE`` when it no longer
    #: matches, rather than silently re-resolving against current overrides.
    recorded_binding: RulesPackageBinding | None = None
    record_selectors: tuple[str, ...] = ()
    component_selectors: tuple[tuple[str, str], ...] = ()
    whole_package: bool = False

    @model_validator(mode="after")
    def exactly_one_package_reference(self) -> Self:
        """Exactly one of package_id or package_slug identifies the package."""
        by_id = self.package_id is not None
        by_slug = self.package_slug is not None and bool(self.package_slug.strip())
        if by_id == by_slug:
            raise ValueError(
                "exactly one of package_id or package_slug must be supplied; got "
                f"package_id={self.package_id!r}, package_slug={self.package_slug!r}"
            )
        return self

    @model_validator(mode="after")
    def selects_something_explicitly(self) -> Self:
        """Refuse the accidentally empty selector set (#137 contract 6)."""
        if self.whole_package:
            return self
        if self.record_selectors or self.component_selectors:
            return self
        raise ValueError(
            "rule slice request selects nothing: supply record/component "
            "selectors or set whole_package=True"
        )


class ActiveRuleSlice(BaseModel):
    """The binding-bearing rule slice the Context Builder consumes.

    Returned by ``RulesPackageService.get_active_rule_slice`` — the existing
    production path, extended at the final CRD Issue 5d cutover (#137 contract
    6) to read the accepted typed mechanical authority instead of legacy chunks
    and ``MechanicalEntity`` rows.

    * ``binding`` is the exact four-component effective binding that produced
      this slice.
    * ``request`` is the supplying request, unchanged: its package reference,
      selectors, ``whole_package`` flag and any recorded binding keep their
      identity and meaning, so a consumer can see exactly what was asked.
    * ``components`` lists the ``(record_key, component_key)`` pairs read, in
      the GameMaster view's source reading order.
    * ``authority_text`` is the deterministic rendering of the GameMaster
      authority view for prompt inclusion: exact governing prose (source or
      authored, with provenance) and structured context.

    A consumer that needs typed facts re-reads them through
    ``RulesAuthorityService`` with ``binding`` as the request's
    ``recorded_binding``; that read is also its stale check. The typed views
    themselves are not held here because the model layer cannot import the
    service layer.

    Frozen so that ``StablePrefix.rules_package_slice`` stays immutable across
    pipeline passes.
    """

    model_config = ConfigDict(frozen=True)

    binding: RulesPackageBinding
    request: RuleSliceRequest
    components: tuple[tuple[str, str], ...]
    authority_text: str
