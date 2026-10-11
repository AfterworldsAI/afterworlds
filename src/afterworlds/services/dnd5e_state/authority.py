"""Exact Rules Package authority for 2b state — bindings and the index.

Two questions, answered through the one code-owned resolver
(:class:`~afterworlds.services.rules_authority.service.RulesAuthorityService`):

* :func:`current_binding` — the package's current exact four-part binding, the
  only binding new state is created under;
* :func:`require_current` — whether a *recorded* binding is still current. A
  binding whose projection or override set moved is ``STALE``; unpublished,
  quarantined, mismatched or invalid authority is refused with its own outcome.

:func:`authority_index` reconstructs the exact effective authority a binding
names — current or historical — through ``replay``, so historical replay and
recorded-binding maintenance keep working after the package moves on. A
binding is immutable identity, so its index is cached by value.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.representation import (
    ProgressionEntryFact,
    RecordKind,
    SpellSlotProgressionFact,
)
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.dnd5e_state.errors import BindingRefusedError
from afterworlds.services.rules_authority.application import (
    AuthoredProse,
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveRecord,
    SourceProse,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.service import RulesAuthorityService

__all__ = [
    "AuthorityIndex",
    "authority_index",
    "component_schema_id",
    "current_binding",
    "require_current",
]


def current_binding(
    session: Session, package_uuid: UUID, *, now: str
) -> RulesPackageBinding:
    """The package's current exact binding, or a typed refusal."""
    resolution = RulesAuthorityService(session, now=now).resolve(
        package_uuid=package_uuid
    )
    if resolution.outcome is not AuthorityOutcome.RESOLVED:
        raise BindingRefusedError(resolution.outcome, resolution.detail)
    assert resolution.binding is not None
    return resolution.binding


def require_current(
    session: Session, recorded: RulesPackageBinding, *, now: str
) -> None:
    """Refuse unless *recorded* is exactly the package's current binding."""
    resolution = RulesAuthorityService(session, now=now).resolve(
        package_uuid=recorded.package_uuid,
        expected_release=recorded.release_version,
        recorded=recorded,
    )
    if resolution.outcome is not AuthorityOutcome.RESOLVED:
        raise BindingRefusedError(resolution.outcome, resolution.detail)


def component_schema_id(component: EffectiveComponent) -> str:
    """Content-derived identity of one effective component's schema.

    Built from what the component *is* in the effective view: its handling,
    reason codes, every fact and option by key, its governing prose by span or
    by authored text, and the override that supplied it. A choice recorded
    under one identity is refused under a target whose component differs.
    """
    prose: list[object] = []
    for entry in component.governing_prose:
        if isinstance(entry, SourceProse):
            prose.append(["source", entry.span_id, entry.option_key])
        elif isinstance(entry, AuthoredProse):
            prose.append(["authored", entry.text, entry.supplied_by_override_id])
    payload = {
        "record": component.record_key,
        "component": component.semantic_key,
        "handling": component.handling.value,
        "irreducibility": component.irreducibility_reason_code,
        "retention": component.prose_retention_reason_code,
        "facts": sorted([f.fact_key, f.option_key or ""] for f in component.facts),
        "options": sorted(
            [o.semantic_key, sorted(f.fact_key for f in o.facts)]
            for o in component.options
        ),
        "prose": sorted(prose, key=json.dumps),
        "supplied_by": component.supplied_by_override_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorityIndex:
    """Lookup over one binding's exact effective authority."""

    binding: RulesPackageBinding
    records: Mapping[str, EffectiveRecord]
    members: Mapping[str, frozenset[str]] = field(default_factory=dict)

    @classmethod
    def from_authority(cls, authority: EffectiveAuthority) -> AuthorityIndex:
        return cls(
            binding=authority.binding,
            records={r.semantic_key: r for r in authority.records},
            members={k: frozenset(v) for k, v in authority.members},
        )

    def record(self, key: str) -> EffectiveRecord | None:
        return self.records.get(key)

    def component(
        self, record_key: str, component_key: str
    ) -> EffectiveComponent | None:
        record = self.records.get(record_key)
        if record is None:
            return None
        for c in record.components:
            if c.semantic_key == component_key:
                return c
        return None

    def kind(self, key: str) -> RecordKind | None:
        record = self.records.get(key)
        return None if record is None else record.kind

    def is_member(self, section: str, member: str) -> bool:
        return member in self.members.get(section, frozenset())

    def progression(self, class_key: str) -> tuple[ProgressionEntryFact, ...]:
        return tuple(
            f.fact
            for c in self._components(class_key)
            for f in c.facts
            if isinstance(f.fact, ProgressionEntryFact)
        )

    def slot_progression(self, class_key: str) -> tuple[SpellSlotProgressionFact, ...]:
        return tuple(
            f.fact
            for c in self._components(class_key)
            for f in c.facts
            if isinstance(f.fact, SpellSlotProgressionFact)
        )

    def _components(self, key: str) -> tuple[EffectiveComponent, ...]:
        record = self.records.get(key)
        return () if record is None else record.components


_CACHE: dict[RulesPackageBinding, AuthorityIndex] = {}
_CACHE_LOCK = Lock()


def authority_index(
    session: Session, binding: RulesPackageBinding, *, now: str
) -> AuthorityIndex:
    """The exact effective authority *binding* names (current or historical).

    ponytail: unbounded in-process cache keyed by the immutable binding; a
    process sees a handful of bindings. Bound it if that stops being true.
    """
    with _CACHE_LOCK:
        cached = _CACHE.get(binding)
    if cached is not None:
        return cached
    authority = RulesAuthorityService(session, now=now).replay(binding)
    index = AuthorityIndex.from_authority(authority)
    with _CACHE_LOCK:
        _CACHE[binding] = index
    return index
