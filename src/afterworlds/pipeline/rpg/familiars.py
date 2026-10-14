"""A familiar's source-specific limits, enforced before any die — CRD Issue
15c (codex-c8-execution-review).

Find Familiar (``spells.md`` "Find Familiar"): *"A familiar can't attack"*;
*"When the familiar drops to 0 Hit Points, it disappears"*, leaving behind
what it wore or carried; and it can be dismissed to a pocket dimension. C8
types a familiar; it grants no attack and no familiar lifecycle. So, for a
creature summoned by any familiar source (``validation.FAMILIAR_SOURCES``):

* it never makes an attack;
* while not recorded as present, nothing names it;
* damage to it, and every zero-HP operation on it (death saves, first aid,
  recovery), refuse: its zero-HP consequence is not executed here, and the
  ordinary monster or character path is not that consequence.

These are holds, not coverage. Every other creature is unaffected.
"""

from __future__ import annotations

from afterworlds.models.dnd5e_state import CreaturePresence
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.turn import TurnCreature, TurnSubject
from afterworlds.services.dnd5e_state.validation import FAMILIAR_SOURCES

__all__ = ["is_familiar", "no_attack", "no_zero_hp_path", "require_present"]


def is_familiar(subject: TurnSubject) -> bool:
    if not isinstance(subject, TurnCreature):
        return False
    summon = subject.stored.state.summon
    return summon is not None and summon.source.record_key in FAMILIAR_SOURCES


def require_present(subject: TurnSubject) -> None:
    """Refuse naming a familiar that is not recorded as present."""
    if not is_familiar(subject):
        return
    presence = subject.stored.state.presence  # type: ignore[union-attr]
    if presence is None:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE,
            f"familiar {subject.subject_id}'s presence is not recorded",
        )
    if presence is not CreaturePresence.PRESENT:
        raise AdjudicationRefusal(
            RefusalKind.INVALID_SELECTION,
            f"familiar {subject.subject_id} is not present ({presence.value})",
        )


def no_attack(subject: TurnSubject) -> None:
    """Find Familiar: "A familiar can't attack"."""
    if is_familiar(subject):
        raise AdjudicationRefusal(
            RefusalKind.INVALID_SELECTION,
            f"familiar {subject.subject_id} can't attack (Find Familiar)",
        )


def no_zero_hp_path(subject: TurnSubject, what: str) -> None:
    """Refuse *what* on a familiar: damage can drop it to 0 Hit Points, where
    it disappears, and its zero-HP states are that disappearance, neither of
    which is executed here."""
    if is_familiar(subject):
        require_present(subject)
        raise AdjudicationRefusal(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{what} on familiar {subject.subject_id} is not executable: at 0 Hit "
            "Points a familiar disappears, leaving what it carried (Find "
            "Familiar), which is not executed here",
        )
