"""The conditions a subject has, recorded or implied — CRD Issue 15c.

A recorded condition can give its subject others: Unconscious *"has the
Incapacitated and Prone conditions"*; Paralyzed, Petrified and Stunned
Incapacitated. Those are typed ``condition_effect`` facts (``applies``) on
structured components with no circumstance, and their rules bind while the
recorded condition lasts. :func:`effective` returns each condition once,
recorded first, with where it came from.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    ActionCost,
    ActionRestrictionFact,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
)
from afterworlds.models.dnd5e_state import ConditionInstance
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import TurnSubject

__all__ = ["Effective", "cannot_act", "effective"]


@dataclass(frozen=True)
class Effective:
    condition: ConditionKind
    #: The recorded instance, or ``None`` for an implied condition.
    instance: ConditionInstance | None
    #: ``recorded`` or the ``record/component`` that implies it.
    origin: str


def effective(subject: TurnSubject, index: AuthorityIndex) -> tuple[Effective, ...]:
    """Every condition *subject* has, or a typed refusal when it records
    none."""
    recorded = subject.stored.state.conditions
    if recorded is None:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE, "the subject records no conditions"
        )
    out = [Effective(c.condition, c, "recorded") for c in recorded]
    seen = {c.condition for c in recorded}
    queue = list(seen)
    while queue:
        kind = queue.pop(0)
        record = index.record(f"glossary.{kind.value}")
        if record is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_AUTHORITY,
                f"condition {kind.value} has no governing record",
            )
        for component in record.components:
            if (
                component.handling is not ComponentHandling.STRUCTURED
                or component.applies_when is not None
            ):
                continue
            for ef in component.facts:
                fact = ef.fact
                if (
                    isinstance(fact, ConditionEffectFact)
                    and fact.effect is ConditionEffectKind.APPLIES
                    and ef.qualifier is None
                    and fact.condition not in seen
                ):
                    seen.add(fact.condition)
                    queue.append(fact.condition)
                    out.append(
                        Effective(
                            fact.condition,
                            None,
                            f"{record.semantic_key}/{component.semantic_key}",
                        )
                    )
    return tuple(out)


def cannot_act(subject: TurnSubject) -> str | None:
    """The condition component that keeps *subject* from taking actions."""
    assert subject.index is not None
    for eff in effective(subject, subject.index):
        record = subject.index.record(f"glossary.{eff.condition.value}")
        if record is None:
            continue
        for component in record.components:
            if (
                component.handling is ComponentHandling.STRUCTURED
                and component.applies_when is None
                and any(
                    isinstance(f.fact, ActionRestrictionFact)
                    and f.fact.cost is ActionCost.ACTION
                    for f in component.facts
                )
            ):
                return f"{record.semantic_key}/{component.semantic_key}"
    return None
