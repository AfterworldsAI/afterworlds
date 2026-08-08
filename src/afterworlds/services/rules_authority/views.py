"""The two authority views — CRD Issue 5d, contract 6.

#137 requires two exact source-linked read surfaces over the same effective
authority:

1. a **typed mechanical view** for deterministic consumers, carrying applied
   override provenance; and
2. a **GameMaster authority view** combining exact governing prose with
   structured context and handling.

Both are built from one :class:`EffectiveAuthority`, so they cannot disagree
about what the authority is, and both carry the complete four-component
effective binding that produced them.

Two boundaries are enforced by what these views *do not* contain:

* **Neither view implies adapter capability.** There is no "supported",
  "executable", or "certified" field anywhere here, and there is no place a
  consumer could read one. Representation and execution are independent
  (ADR-005d Decision 1); the bounded-d20 adapter declares and proves what it can
  execute, and that declaration is CRD Issue 15c's, not this view's.
* **Retrieval never chooses a mechanical value.** The GameMaster view resolves
  governing prose through the exact ``chunk_id`` recorded as the component's
  build-time prose binding. A retrieval layer may locate *candidates* to look
  at, but what comes back here is bound by identity, not by similarity, and a
  chunk that is not the bound one is simply not in the view (ADR-018, ADR-005c
  D4).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.application import (
    AppliedOverride,
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveFact,
    EffectiveRecord,
)

__all__ = [
    "GameMasterAuthorityView",
    "GameMasterComponent",
    "GoverningProse",
    "TypedAuthorityView",
    "build_gamemaster_view",
    "build_typed_view",
]


@dataclass(frozen=True)
class TypedAuthorityView:
    """Exact typed authority for a deterministic consumer.

    ``records`` is the effective view after override application: base
    authority with overrides layered on, each element carrying either its 5c
    span provenance or the identity and origin of the override that supplied
    it.
    """

    binding: RulesPackageBinding
    records: tuple[EffectiveRecord, ...]
    applied_overrides: tuple[AppliedOverride, ...]


@dataclass(frozen=True)
class GoverningProse:
    """One passage of exact governing prose, bound by identity.

    ``text`` is ``None`` when the bound chunk is not present in the store being
    read — reported as an absent passage rather than substituted with a similar
    one, because a nearby passage is not the governing passage.
    """

    chunk_id: str
    text: str | None


@dataclass(frozen=True)
class GameMasterComponent:
    """One component as a GameMaster reads it: prose, context, and handling."""

    record_key: str
    record_kind: RecordKind
    component_key: str
    handling: ComponentHandling
    irreducibility_reason_code: str | None
    governing_prose: tuple[GoverningProse, ...]
    #: Typed facts, supplied as *context* for judgement. A GameMaster reading
    #: this view is adjudicating, not executing; the facts are here so the
    #: judgement is made against exact authority rather than recollection.
    structured_context: tuple[EffectiveFact, ...]
    span_ids: tuple[str, ...]
    supplied_by_override_id: str | None


@dataclass(frozen=True)
class GameMasterAuthorityView:
    """Exact governing authority for GameMaster adjudication."""

    binding: RulesPackageBinding
    components: tuple[GameMasterComponent, ...]
    applied_overrides: tuple[AppliedOverride, ...]


def build_typed_view(authority: EffectiveAuthority) -> TypedAuthorityView:
    """The deterministic-consumer view of one effective authority."""
    return TypedAuthorityView(
        binding=authority.binding,
        records=tuple(authority.records),
        applied_overrides=authority.applied_overrides,
    )


def _gamemaster_component(
    record_key: str,
    record_kind: RecordKind,
    component: EffectiveComponent,
    prose: Mapping[str, str],
) -> GameMasterComponent:
    return GameMasterComponent(
        record_key=record_key,
        record_kind=record_kind,
        component_key=component.semantic_key,
        handling=component.handling,
        irreducibility_reason_code=component.irreducibility_reason_code,
        governing_prose=tuple(
            GoverningProse(chunk_id=chunk_id, text=prose.get(chunk_id))
            for chunk_id in component.prose_chunk_ids
        ),
        structured_context=component.facts,
        span_ids=component.span_ids,
        supplied_by_override_id=component.supplied_by_override_id,
    )


def build_gamemaster_view(
    authority: EffectiveAuthority, prose: Mapping[str, str]
) -> GameMasterAuthorityView:
    """The GameMaster view of one effective authority.

    *prose* maps an authoritative 5c ``chunk_id`` to its exact text. It is
    supplied by the service seam, which reads it from the authoritative
    ``RuleChunk`` records of the bound package — there is no second prose store
    and no text is copied into the projection.
    """
    return GameMasterAuthorityView(
        binding=authority.binding,
        components=tuple(
            _gamemaster_component(record.semantic_key, record.kind, component, prose)
            for record in authority.records
            for component in record.components
        ),
        applied_overrides=authority.applied_overrides,
    )
