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
* **Retrieval never chooses a mechanical value.** Source governing prose
  resolves through the exact ``chunk_id`` recorded as the component's
  build-time prose binding. A retrieval layer may locate *candidates* to look
  at, but what comes back here is bound by identity, not by similarity, and a
  chunk that is not the bound one is simply not in the view (ADR-018, ADR-005c
  D4).

**Authored prose (Owner Decision 2026-08-08).** Governing prose is a closed
discriminated form: exact 5c source prose (:class:`~.application.SourceProse`,
resolved here from the bound package's own ``RuleChunk`` rows) ordered
alongside a distinct authored-authority overlay
(:class:`~.application.AuthoredProse`), whose text and provenance were already
resolved when the override was applied — see
:mod:`afterworlds.services.rules_authority.application`. Both views surface the
same ordered entries; only source entries need a text lookup here, because
authored text is already exact.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import Applicability, RecordKind
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.application import (
    AppliedOverride,
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveFact,
    EffectiveOption,
    EffectiveRecord,
    GoverningProseEntry,
    SourceProse,
)

__all__ = [
    "GameMasterAuthorityView",
    "GameMasterComponent",
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
class GameMasterComponent:
    """One component as a GameMaster reads it: prose, context, and handling.

    ``governing_prose`` is exact ordered source-and-authored authority. A
    :class:`~.application.SourceProse` entry's ``text`` is ``None`` when the
    bound chunk is not present in the store being read — reported as an
    absent passage rather than substituted with a similar one, because a
    nearby passage is not the governing passage. A
    :class:`~.application.AuthoredProse` entry's ``text`` is never ``None``:
    it is exact authored text, already resolved when the override applied.
    """

    record_key: str
    record_kind: RecordKind
    component_key: str
    handling: ComponentHandling
    irreducibility_reason_code: str | None
    governing_prose: tuple[GoverningProseEntry, ...]
    #: Typed facts, supplied as *context* for judgement. A GameMaster reading
    #: this view is adjudicating, not executing; the facts are here so the
    #: judgement is made against exact authority rather than recollection.
    #:
    #: **Direct facts only.** Facts belonging to an exhaustive actor choice are
    #: in :attr:`options` instead, because they are mutually exclusive: putting
    #: them here would present "you may crawl" and "you may stand up" as
    #: simultaneously applicable, which is not what the rule says.
    structured_context: tuple[EffectiveFact, ...]
    span_ids: tuple[str, ...]
    supplied_by_override_id: str | None
    #: The component's exhaustive actor choice, when it states one. Exactly one
    #: option applies per exercise of the choice; the reader picks.
    options: tuple[EffectiveOption, ...] = ()
    #: When the component applies at all, when the source conditions it.
    applies_when: Applicability | None = None


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


def _resolve_prose(
    entry: GoverningProseEntry, prose: Mapping[str, str]
) -> GoverningProseEntry:
    """Resolve one prose entry's text for the GameMaster view.

    A :class:`SourceProse` entry is resolved by its exact ``chunk_id`` against
    *prose* and then **sliced to its accepted governing span**. The whole chunk
    is what the source stores; the span is what the projection accepted as this
    component's authority, and returning the surrounding sentences would
    overstate what governs it (#137 contract 3).

    The slice is bounds-checked rather than trusted. Python would silently
    return a short string — or an empty one — for offsets past the end of the
    text, and a truncated passage presented as exact governing authority is
    worse than an absent one. A chunk whose stored text no longer contains the
    recorded extent therefore resolves to ``None``: the same "absent passage"
    the caller already handles, reported rather than papered over.

    An :class:`AuthoredProse` entry already carries exact text — it came from
    the override's own validated payload, not from a lookup — so it passes
    through unchanged.
    """
    if not isinstance(entry, SourceProse):
        return entry
    text = prose.get(entry.chunk_id)
    if text is None or entry.char_end > len(text):
        return replace(entry, text=None)
    return replace(entry, text=text[entry.char_start : entry.char_end])


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
            _resolve_prose(entry, prose) for entry in component.governing_prose
        ),
        structured_context=component.facts,
        options=component.options,
        applies_when=component.applies_when,
        span_ids=component.span_ids,
        supplied_by_override_id=component.supplied_by_override_id,
    )


def build_gamemaster_view(
    authority: EffectiveAuthority, prose: Mapping[str, str]
) -> GameMasterAuthorityView:
    """The GameMaster view of one effective authority.

    *prose* maps an authoritative 5c ``chunk_id`` to its exact text. It is
    supplied by the service seam, which reads it from the authoritative
    ``RuleChunk`` records of the bound package. Source prose is never copied
    into the projection; a distinct authored-authority overlay (Owner Decision
    2026-08-08) already carries its own exact text and never claims 5c
    provenance — see :mod:`afterworlds.services.rules_authority.application`.
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
