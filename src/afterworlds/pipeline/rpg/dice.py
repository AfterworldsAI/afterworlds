"""Dice: the DiceService, described roll requests and the term engine.

CRD Issues 15 and 15b.

* :class:`DiceService` owns randomness. It rolls an ``NdS`` or ``NdSkhK``/
  ``NdSklK`` expression; it knows no modifier, target or rule.
* :class:`RollRequest` describes one roll at the adapter's call site: who
  rolls, why (a bounded :class:`~afterworlds.models.enums.RollPurpose`), its
  code-derived modifiers and target. :func:`request` hands it to a dice
  source that understands it (an action-resolution sequence, which turns it
  into a persisted ``RollInstructionSnapshot``) and otherwise rolls the bare
  expression, so a synchronous 15c turn is unchanged.
* The term engine (:func:`derive`, :func:`aggregate_range`,
  :func:`outcome`) derives selections, subtotals, totals and outcomes from a
  structured instruction and raw values. Kept and omitted dice stay
  reconstructable from ``values`` and ``selected_indices``.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from afterworlds.models.enums import DiceSelectionRule, RollContribution, RollPurpose
from afterworlds.models.rpg import (
    DerivedRollTermResult,
    DiceResult,
    RollInstructionSnapshot,
    RollTerm,
    SheetEffect,
)

_EXPRESSION_RE = re.compile(r"^(\d+)d(\d+)(?:(kh|kl)(\d+))?$", re.IGNORECASE)


def parse_expression(expression: str) -> tuple[int, int, str | None, int | None]:
    """``(count, sides, keep_op, keep_n)`` of ``NdS``, ``NdSkhK`` or
    ``NdSklK``; ``ValueError`` for anything else, including a keep count
    outside ``[1, count]``. No arithmetic is accepted: modifiers are
    code-owned components, never expression text."""
    m = _EXPRESSION_RE.match(expression.strip())
    if not m:
        raise ValueError(f"Unrecognised dice expression: {expression!r}")
    count, sides = int(m.group(1)), int(m.group(2))
    keep_op = m.group(3).lower() if m.group(3) else None
    keep_n = int(m.group(4)) if m.group(4) else None
    if count < 1 or sides < 1:
        raise ValueError(f"Invalid dice expression: {expression!r}")
    if keep_n is not None and not 1 <= keep_n <= count:
        raise ValueError(f"keep count outside [1, {count}]: {expression!r}")
    return count, sides, keep_op, keep_n


def selected_indices(
    values: tuple[int, ...], rule: DiceSelectionRule, keep: int | None
) -> tuple[int, ...]:
    """The kept dice's indexes, in roll order. Ties keep the earlier die,
    which never changes the subtotal."""
    if rule is DiceSelectionRule.SUM_ALL:
        return tuple(range(len(values)))
    assert keep is not None
    order = sorted(
        range(len(values)),
        key=lambda i: (
            -values[i] if rule is DiceSelectionRule.KEEP_HIGHEST else values[i],
            i,
        ),
    )
    return tuple(sorted(order[:keep]))


def _rule(keep_op: str | None) -> DiceSelectionRule:
    if keep_op is None:
        return DiceSelectionRule.SUM_ALL
    return (
        DiceSelectionRule.KEEP_HIGHEST
        if keep_op == "kh"
        else DiceSelectionRule.KEEP_LOWEST
    )


@runtime_checkable
class DiceService(Protocol):
    """Injectable randomness: no modifiers, targets or rules."""

    def roll(self, expression: str) -> DiceResult:
        """Roll *expression*; ``chosen`` is the sum of the kept dice."""
        ...


class SystemRandomDiceService:
    """Production dice (``secrets.SystemRandom``); seedable for tests."""

    def __init__(self, seed: int | None = None) -> None:
        if seed is not None:
            import random  # noqa: PLC0415

            self._rng = random.Random(seed)  # noqa: S311 - test seeding only
        else:
            self._rng = secrets.SystemRandom()

    def roll(self, expression: str) -> DiceResult:
        count, sides, keep_op, keep_n = parse_expression(expression)
        raw = tuple(self._rng.randint(1, sides) for _ in range(count))
        kept = selected_indices(raw, _rule(keep_op), keep_n)
        return DiceResult(
            expression=expression, raw_rolls=raw, chosen=sum(raw[i] for i in kept)
        )


@dataclass(frozen=True)
class RollRequest:
    """One roll as the adapter describes it: never authored by a model.

    ``roller`` is the subject key (``("character", id)``/``("creature",
    id)``) whose die it is. ``modifiers`` are ``(label, value, source)``.
    ``naturals`` maps a die face to the outcome the rules fix for it.
    ``options`` are parameterless pre-roll adjustments ``(option_id,
    ability_id, label)`` the roller may choose (15b-9, 15b-10).
    """

    purpose: RollPurpose
    roller: tuple[str, str]
    label: str
    modifiers: tuple[tuple[str, int, str | None], ...] = ()
    dc: int | None = None
    naturals: tuple[tuple[int, str], ...] = ()
    critical_on_success: bool = False
    source_refs: tuple[str, ...] = ()
    options: tuple[tuple[str, str, str], ...] = ()
    #: Backend-only contest linkage (ADR-015b Group 17), a ``ContestLinkage``.
    contest: object | None = None


@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    label: str
    effects: tuple[SheetEffect, ...]


@dataclass(frozen=True)
class DecisionRequest:
    """A result-triggered choice the acting character makes (15b-35): code
    computes each option's effects; the Sojourner selects one by id."""

    decider: tuple[str, str]
    prompt: str
    options: tuple[DecisionOption, ...]
    source_refs: tuple[str, ...]


def decide(dice: object, described: DecisionRequest) -> str | None:
    """The option an action-resolution sequence's decision source returns,
    or ``None`` when *dice* carries no decision source (a direct adapter
    call), in which case the caller keeps its own selection."""
    method = getattr(type(dice), "decide", None)
    if method is None:
        return None
    choice: str | None = method(dice, described)
    return choice


class DescribedDice(Protocol):
    def roll_described(self, expression: str, request: RollRequest) -> DiceResult: ...


def request(dice: DiceService, expression: str, described: RollRequest) -> DiceResult:
    """Roll *expression*, handing *described* to a dice source that records
    rolls (a sequence). Any other source just rolls the expression."""
    # Looked up on the type: a source either implements it or not (a test
    # double answering any attribute must not count).
    method = getattr(type(dice), "roll_described", None)
    if method is not None:
        result: DiceResult = method(dice, expression, described)
        return result
    return dice.roll(expression)


def term_of(expression: str, term_id: object, label: str | None = None) -> RollTerm:
    """The structured term of a bare dice expression."""
    count, sides, keep_op, keep_n = parse_expression(expression)
    return RollTerm(
        term_id=term_id,  # type: ignore[arg-type]
        count=count,
        sides=sides,
        selection_rule=_rule(keep_op),
        keep_count=keep_n,
        label=label,
    )


def derive(
    instruction: RollInstructionSnapshot, values: dict[object, tuple[int, ...]]
) -> tuple[DerivedRollTermResult, ...]:
    """Each term's selection and signed subtotal from validated raw values."""
    out = []
    for term in instruction.terms:
        raw = values[term.term_id]
        kept = selected_indices(raw, term.selection_rule, term.keep_count)
        subtotal = sum(raw[i] for i in kept)
        if term.contribution is RollContribution.SUBTRACT:
            subtotal = -subtotal
        out.append(
            DerivedRollTermResult(
                term_id=term.term_id,
                values=raw,
                selected_indices=kept,
                contribution_applied_subtotal=subtotal,
            )
        )
    return tuple(out)


def modifier_total(instruction: RollInstructionSnapshot, *, visible: bool) -> int:
    from afterworlds.models.enums import ModifierVisibility

    return sum(
        m.value
        for m in instruction.modifier_components
        if (m.visibility is ModifierVisibility.PLAYER_VISIBLE) is visible
    )


def aggregate_range(instruction: RollInstructionSnapshot) -> tuple[int, int]:
    """The legal range of a physical aggregate report: every term's kept
    dice (``keep_count`` dice for a keep rule, not the whole pool; a
    subtracted term reverses its extremes) plus the visible modifiers."""
    low = high = modifier_total(instruction, visible=True)
    for term in instruction.terms:
        kept = term.keep_count or term.count
        lo, hi = kept, kept * term.sides
        if term.contribution is RollContribution.SUBTRACT:
            lo, hi = -hi, -lo
        low, high = low + lo, high + hi
    return low, high


def single_face(instruction: RollInstructionSnapshot) -> bool:
    """Whether the instruction keeps exactly one die of one term: the only
    shape where a natural face is a single die's value."""
    if len(instruction.terms) != 1:
        return False
    term = instruction.terms[0]
    return (term.keep_count or term.count) == 1


def outcome(instruction: RollInstructionSnapshot, total: int, face: int | None) -> str:
    """The bounded outcome of one roll: ``undetermined`` with no target, a
    natural face's fixed outcome, else the total against ``dc``."""
    if instruction.dc is None:
        return "undetermined"
    if face is not None:
        for natural in instruction.natural_outcomes:
            if natural.face == face:
                return natural.outcome
    if total >= instruction.dc:
        return "critical_success" if instruction.critical_on_success else "success"
    return "failure"


__all__ = [
    "DecisionOption",
    "DecisionRequest",
    "DiceService",
    "decide",
    "RollRequest",
    "SystemRandomDiceService",
    "aggregate_range",
    "derive",
    "modifier_total",
    "outcome",
    "parse_expression",
    "request",
    "selected_indices",
    "single_face",
    "term_of",
]
