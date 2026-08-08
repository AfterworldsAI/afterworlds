"""Canonical override state and its content-derived identity — Decision 9.

The ``override_set_uuid`` is derived from the **canonical ordered effective
override state**, per entry:

* stable override identity;
* override origin;
* exact typed target identity;
* operation;
* precedence and resolved apply order;
* enablement state; and
* the complete validated payload.

Three consequences of that list are load-bearing and are each proven by a
negative control:

* Deleting and recreating an otherwise identical override under a different
  ``override_id`` mints a different identity — the identity is
  provenance-exact, not merely mechanically equivalent.
* Changing only the origin — a house rule becoming a package patch — mints a
  different identity, because those are not the same authority.
* Disabling an override mints a different identity. **Disabled overrides stay
  in the canonical state, carrying ``is_enabled=False``.** Enablement is a
  per-entry field in ADR-005d Decision 9's enumeration, so it must be able to
  vary; if disabled entries were filtered out instead, the field would be
  constant ``True`` and would carry no information, and *authoring* a
  disabled override — an addition that changes nothing yet — would leave the
  identity unmoved. They are retained for identity and provenance and are
  skipped at application time.

What is deliberately **outside** the identity: creation timestamps, authors,
comments, and proposal history. They are audit metadata and do not participate
in applicability, ordering, or resolution. Package scope is not repeated inside
an entry either — the enclosing binding already supplies it.

The empty override set has its own deterministic identity, computed from an
empty entry list. It is a value, not the absence of one, so a binding never has
to represent "no overrides" as a null the next caller can misread as "not yet
resolved".
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import content_id
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
    TargetShapeError,
    target_payload,
)

__all__ = [
    "EMPTY_OVERRIDE_SET_UUID",
    "EffectiveOverrideEntry",
    "EffectiveOverrideSet",
    "OverrideStateError",
    "collect_current_override_state",
    "override_set_identity",
    "override_set_payload",
]


class OverrideStateError(ValueError):
    """Raised when a stored override row cannot be read as canonical state.

    Covers a row whose typed columns do not parse — an unknown origin or
    operation, a target whose key set does not match its kind, a release the
    package does not publish — and a payload that is not a valid member of the
    closed patch union, because a payload with no canonical form cannot
    participate in a content-derived identity.

    Such a row is never skipped. Skipping would make the override-set identity
    depend on which rows happened to parse, so a package with a malformed
    override would silently share the identity of one that never had it.
    """


@dataclass(frozen=True)
class EffectiveOverrideEntry:
    """One override as it participates in identity, order, and provenance.

    ``payload`` is the **canonical form of the validated typed patch**, not the
    bytes that happened to be stored. ADR-005d Decision 9 says the identity
    covers the complete *validated* payload, and the difference is load-bearing:
    a stored payload could list the same facts in a different order, and hashing
    it directly would mint two identities for one patch. Canonicalizing first
    means an equivalent patch is one authority, while any genuine content change
    still moves the identity.

    It is kept as the canonical mapping rather than as a rebuilt patch object so
    that identity derivation never depends on a patch type's ``__eq__``; the
    typed patch is rebuilt again at application time from this canonical form.
    """

    override_id: str
    origin: OverrideOriginEnum
    target: MechanicalTarget
    operation: OverrideOperationEnum
    precedence: int
    apply_order: int
    is_enabled: bool
    payload: dict[str, object]

    def entry_payload(self) -> dict[str, object]:
        """Canonical identity-bearing payload of this entry."""
        return {
            "override_id": self.override_id,
            "origin": self.origin.value,
            "target": target_payload(self.target),
            "operation": self.operation.value,
            "precedence": self.precedence,
            "apply_order": self.apply_order,
            "is_enabled": self.is_enabled,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class EffectiveOverrideSet:
    """The complete canonical ordered override state and its identity.

    ``package_uuid`` and ``release_version`` are the scope this state was
    collected for. They are retained for retrieval and diagnosis and are not
    part of :meth:`identity`'s payload — see the module docstring for why the
    empty set has one identity rather than one per package.
    """

    package_uuid: str
    release_version: str
    entries: tuple[EffectiveOverrideEntry, ...]

    @property
    def override_set_uuid(self) -> str:
        return override_set_identity(self.entries)

    def applicable(self) -> tuple[EffectiveOverrideEntry, ...]:
        """The entries that actually apply, in resolved order."""
        return tuple(e for e in self.entries if e.is_enabled)


def override_set_payload(
    entries: tuple[EffectiveOverrideEntry, ...],
) -> dict[str, object]:
    """The exact payload an override-set identity is derived from."""
    return {"entries": [e.entry_payload() for e in entries]}


def override_set_identity(entries: tuple[EffectiveOverrideEntry, ...]) -> str:
    """Content-derived identity of one canonical ordered override state."""
    return content_id("mechanical_override_set", override_set_payload(entries))


#: The identity of the no-overrides state. A deterministic value, not a null.
EMPTY_OVERRIDE_SET_UUID = override_set_identity(())


def _parse_row(
    row: MechanicalOverrideORM,
) -> tuple[OverrideOriginEnum, OverrideOperationEnum, MechanicalTarget]:
    """Parse one stored row's typed columns, refusing anything unreadable."""
    try:
        origin = OverrideOriginEnum(row.override_origin)
    except ValueError as exc:
        raise OverrideStateError(
            f"override {row.override_id}: origin {row.override_origin!r} is not "
            "a declared override origin"
        ) from exc
    try:
        operation = OverrideOperationEnum(row.override_operation)
    except ValueError as exc:
        raise OverrideStateError(
            f"override {row.override_id}: operation {row.override_operation!r} is "
            "not a declared override operation"
        ) from exc
    try:
        kind = MechanicalTargetKind(row.target_kind)
    except ValueError as exc:
        raise OverrideStateError(
            f"override {row.override_id}: target kind {row.target_kind!r} is not "
            "a declared target kind"
        ) from exc
    try:
        target = MechanicalTarget(
            kind=kind,
            record_key=row.target_record_key,
            component_key=row.target_component_key,
            fact_key=row.target_fact_key,
        )
    except TargetShapeError as exc:
        raise OverrideStateError(f"override {row.override_id}: {exc}") from exc
    return origin, operation, target


def collect_current_override_state(
    session: Session, package_uuid: str, release_version: str
) -> EffectiveOverrideSet:
    """Read the package's current override rows as canonical ordered state.

    Ordering is ``(precedence, override_id)`` — the same rule the existing
    chunk-override path applies, preserved unchanged as ADR-005d Decision 10
    requires. ``override_id`` is the tie-break rather than insertion order or a
    row id, so two databases holding the same overrides resolve the same order
    and therefore the same identity.

    A row authored against a different release fails here, closed, rather than
    being filtered out. Filtering would make a cross-release override invisible:
    the identity would silently equal that of a package with no such override,
    and the explicit failure #137 contract 6 requires for a cross-release patch
    would never be reported.
    """
    rows = (
        session.execute(
            select(MechanicalOverrideORM)
            .where(MechanicalOverrideORM.package_uuid == package_uuid)
            .order_by(
                MechanicalOverrideORM.precedence,
                MechanicalOverrideORM.override_id,
            )
        )
        .scalars()
        .all()
    )
    entries: list[EffectiveOverrideEntry] = []
    for order, row in enumerate(rows):
        origin, operation, target = _parse_row(row)
        if row.release_version != release_version:
            raise OverrideStateError(
                f"override {row.override_id} was authored against release "
                f"{row.release_version!r}; the package publishes "
                f"{release_version!r}"
            )
        try:
            patch = patch_from_payload(row.payload, operation=operation, target=target)
        except InvalidPatchError as exc:
            raise OverrideStateError(f"override {row.override_id}: {exc}") from exc
        entries.append(
            EffectiveOverrideEntry(
                override_id=row.override_id,
                origin=origin,
                target=target,
                operation=operation,
                precedence=row.precedence,
                apply_order=order,
                is_enabled=bool(row.is_enabled),
                payload=patch_payload(patch),
            )
        )
    return EffectiveOverrideSet(
        package_uuid=package_uuid,
        release_version=release_version,
        entries=tuple(entries),
    )
