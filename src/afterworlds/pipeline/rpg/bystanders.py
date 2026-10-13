"""Subjects that contribute to an operation without taking part in it — CRD
Issue 15c (codex-c7-boundary-classification, "Bystanders").

A rule that turns on another creature names that creature: the GameMaster
identifies it (its presence within the source's distance is an approved
spatial fact, OD-15c-1), and code reads it under its own binding, checks the
state the rule qualifies it by, and rechecks its revision at commit like any
other subject the turn read. An anonymous yes/no never stands in for it.

* **Close combat** (``play.combat/close_combat``): Disadvantage on a ranged
  attack when an enemy within 5 feet that can see the attacker and isn't
  Incapacitated is present. Each named enemy is checked: not Incapacitated;
  sight that depends on a sense (a Blinded enemy, an Invisible attacker) is
  not executable and refuses.
* **Pack Tactics** (a creature trait): an ally within 5 feet of the target
  that isn't Incapacitated.
* **Auras** that change another creature's saves (Aura of Protection and its
  kin, Boon of Fate's Improve Fate, Countercharm): code finds every holder in
  the story; the GameMaster states which cover a saver. A covering aura is
  not executed here and refuses; a holder named out of range does not.

Who is an enemy or an ally is the GameMaster's identification; code does not
derive allegiance (no accepted state records it), and records the named
subjects in provenance.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.rpg import SubjectRef
from afterworlds.pipeline.rpg import familiars
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.conditions import cannot_act, effective
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
)

__all__ = ["AURAS", "allies", "aura_holders", "check_auras", "enemies"]

#: Features by which one creature changes another's saving throws, read from
#: the save-contributor scan (``saves/save-contributor-scan.md``).
AURAS: frozenset[str] = frozenset(
    {
        "classes.paladin.aura_of_protection",
        "classes.paladin.aura_of_courage",
        "classes.paladin.oath_of_devotion.aura_of_devotion",
        "classes.bard.countercharm",
        "feats.boon_of_fate",
    }
)


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _key(subject: TurnSubject) -> tuple[str, str]:
    kind = "creature" if isinstance(subject, TurnCreature) else "character"
    return kind, str(subject.subject_id)


def _read(
    refs: tuple[SubjectRef, ...] | None,
    what: str,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    excluded: tuple[TurnSubject, ...],
) -> list[TurnSubject]:
    if refs is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"name the {what} (an empty list if there are none)",
        )
    out: list[TurnSubject] = []
    for ref in refs:
        key = (ref.kind, str(ref.subject_id))
        subject = actor if key == _key(actor) else subjects.get(key)
        if subject is None or subject.index is None:
            raise _refuse(RefusalKind.MISSING_STATE, f"{ref.kind} {ref.subject_id}")
        # A named physical bystander must be here: a familiar not recorded
        # present (dismissed, gone, unknown) is no ally or enemy within 5 feet.
        familiars.require_present(subject)
        if any(_key(subject) == _key(e) for e in excluded):
            raise _refuse(
                RefusalKind.INVALID_SELECTION, f"a {what} must be another creature"
            )
        out.append(subject)
    return out


def enemies(
    refs: tuple[SubjectRef, ...] | None,
    attacker: TurnSubject,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> list[str]:
    """The named enemies within 5 feet that qualify for close combat: each
    can act (isn't Incapacitated) and sees the attacker by ordinary sight."""
    qualifying = []
    for enemy in _read(refs, "enemies within 5 feet", actor, subjects, (attacker,)):
        assert enemy.index is not None
        if cannot_act(enemy):
            continue
        blinded = any(
            e.condition is ConditionKind.BLINDED for e in effective(enemy, enemy.index)
        )
        if blinded:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                "whether a Blinded enemy sees the attacker depends on its senses, "
                "which is not executable here",
            )
        qualifying.append(f"{_key(enemy)[0]}:{enemy.subject_id}")
    return qualifying


def allies(
    refs: tuple[SubjectRef, ...] | None,
    attacker: TurnSubject,
    target: TurnSubject,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
) -> list[str]:
    """The named allies within 5 feet of the target that aren't
    Incapacitated."""
    found = _read(
        refs, "allies within 5 feet of the target", actor, subjects, (attacker, target)
    )
    return [f"{_key(a)[0]}:{a.subject_id}" for a in found if not cannot_act(a)]


def aura_holders(characters: list[TurnCharacter]) -> list[TurnCharacter]:
    """The story characters holding a feature in :data:`AURAS`."""
    from afterworlds.pipeline.rpg.saves import _held_keys

    out = []
    for character in characters:
        if character.index is None:
            continue
        if _held_keys(character, character.index, AURAS) & AURAS:
            out.append(character)
    return out


def check_auras(
    holders: list[TurnCharacter],
    savers: list[tuple[str, str]],
    in_range: tuple[SubjectRef, ...] | None,
) -> None:
    """Refuse a save an aura held by another creature could change: the
    GameMaster names which holders' auras cover the savers; a covering aura
    is not executed here."""
    others = [h for h in holders if ("character", str(h.subject_id)) not in savers]
    if not savers or not others:
        return
    if in_range is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            "name which of these aura holders cover the savers (an empty list if "
            "none): " + ", ".join(str(h.subject_id) for h in others),
        )
    known = {str(h.subject_id) for h in others}
    for ref in in_range:
        if str(ref.subject_id) not in known:
            raise _refuse(
                RefusalKind.INVALID_SELECTION, f"{ref.subject_id} holds no such aura"
            )
    if in_range:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            "an aura held by another creature can change this save and is not "
            "executable here",
        )
