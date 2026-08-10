"""Exact typed override targets — CRD Issue 5d, Decision 10.

An override names one exact element of the mechanical projection: a record, one
component of a record, one fact of a component, or the prose authority of one
component. Nothing else is addressable. There is deliberately no JSON path, no
selector expression, and no wildcard — #137 contract 6 forbids them, and each
of those would let an override reach authority nobody reviewed it against.

**Prose is its own grain, not a component subtype.** A ``COMPONENT``-kind
``DISABLE`` already means "remove the whole component" (Decision 10). Prose
authority needs to be suppressible, replaceable, or extensible on its own —
Owner Decision 2026-08-08's authored-authority overlay — without disturbing
that component's typed facts, so it is a fourth ``MechanicalTargetKind``
scoped the same way a component is (record + component key), never a raw
chunk id.

**Semantic keys, not derived IDs.** A target names the committed semantic keys
(``record_key``, ``component_key``, and the content-derived ``fact_key``) rather
than the projection-scoped ``record_id``/``component_id``/``fact_id`` derived in
:mod:`afterworlds.ingestion.mechanical.projection`. Derived IDs are minted from
the projection UUID, so targeting them would expire every override the moment
the same release is reprojected — an override would silently stop applying
because an unrelated part of the projection changed. Semantic keys survive that;
what does *not* survive is a change of release, which is why every override
carries its authored ``release_version`` and a mismatch fails explicitly as
``INVALID_OVERRIDE`` rather than being applied or skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "MechanicalTarget",
    "MechanicalTargetKind",
    "TargetShapeError",
    "target_payload",
]


class MechanicalTargetKind(StrEnum):
    """What kind of element an override targets."""

    RECORD = "record"
    COMPONENT = "component"
    FACT = "fact"
    PROSE = "prose"


class TargetShapeError(ValueError):
    """Raised when a target's key set does not match its declared kind."""


@dataclass(frozen=True)
class MechanicalTarget:
    """One exact typed target inside a mechanical projection.

    The key set is exhaustively determined by ``kind``, and the constructor
    refuses any other combination. A component target carrying a ``fact_key``,
    or a fact target missing its component, is not a target that merely fails to
    resolve later — it is a target that does not identify anything, and
    accepting it would make the identity of an override set depend on fields
    that mean nothing.
    """

    kind: MechanicalTargetKind
    record_key: str
    component_key: str | None = None
    fact_key: str | None = None

    def __post_init__(self) -> None:
        if not self.record_key.strip():
            raise TargetShapeError("target record_key is blank")
        needs_component = self.kind in (
            MechanicalTargetKind.COMPONENT,
            MechanicalTargetKind.FACT,
            MechanicalTargetKind.PROSE,
        )
        if needs_component and not (self.component_key or "").strip():
            raise TargetShapeError(f"{self.kind.value} target requires a component_key")
        if not needs_component and self.component_key is not None:
            raise TargetShapeError(
                f"{self.kind.value} target must not carry a component_key"
            )
        if self.kind is MechanicalTargetKind.FACT:
            if not (self.fact_key or "").strip():
                raise TargetShapeError("fact target requires a fact_key")
        elif self.fact_key is not None:
            raise TargetShapeError(
                f"{self.kind.value} target must not carry a fact_key"
            )

    def describe(self) -> str:
        """Human-readable target, used in typed failure detail."""
        parts = [self.record_key]
        if self.component_key is not None:
            parts.append(self.component_key)
        if self.fact_key is not None:
            parts.append(self.fact_key)
        return f"{self.kind.value}:{'/'.join(parts)}"


def target_payload(target: MechanicalTarget) -> dict[str, object]:
    """Canonical identity-bearing payload of one target.

    Absent keys are serialized as ``None`` rather than omitted, so a component
    target and a fact target can never canonicalize to the same bytes through a
    missing key.
    """
    return {
        "kind": target.kind.value,
        "record_key": target.record_key,
        "component_key": target.component_key,
        "fact_key": target.fact_key,
    }
