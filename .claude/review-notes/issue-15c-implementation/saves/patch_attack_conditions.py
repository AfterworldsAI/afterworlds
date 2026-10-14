"""One-off patch: replace attacks._condition_sources with the reviewed
condition classification (CRD Issue 15c sibling audit)."""

from pathlib import Path

p = Path("src/afterworlds/pipeline/rpg/attacks.py")
t = p.read_text(encoding="utf-8")
start = t.index("def _condition_sources(")
end = t.index("def _one[T](")
new = Path(__file__).with_name("attack_conditions_block.py.txt").read_text(
    encoding="utf-8"
)
t = t[:start] + new + t[end:]


def sub(old: str, new: str) -> None:
    global t
    assert t.count(old) == 1, old
    t = t.replace(old, new)


sub(
    """    # Advantage and Disadvantage.
    advantage, disadvantage = _condition_sources(actor, RollActor.SUBJECT, ability)
    a2, d2 = _condition_sources(target, RollActor.AGAINST_SUBJECT, ability)
    advantage += a2
    disadvantage += d2
""",
    """    # Advantage and Disadvantage. A melee attack with a 5-foot reach is made
    # from within 5 feet; otherwise the GameMaster's fact says (OD-15c-1).
    within_5_feet = sel.target_within_5_feet
    if not ranged and WeaponProperty.REACH not in props:
        if within_5_feet is False:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                "a melee attack with a 5-foot reach is made from within 5 feet",
            )
        within_5_feet = True
    mods = _Modifiers()
    _conditions(actor, RollActor.SUBJECT, target, within_5_feet, mods)
    _conditions(target, RollActor.AGAINST_SUBJECT, actor, within_5_feet, mods)
    advantage, disadvantage = mods.advantage, mods.disadvantage
""",
)
sub(
    """        ac_breakdown=ac_breakdown,
    )""",
    """        ac_breakdown=ac_breakdown,
        automatic_critical=tuple(mods.automatic_critical),
    )""",
)
sub(
    """    ac_breakdown: dict[str, int] = field(default_factory=dict)

    @property""",
    """    ac_breakdown: dict[str, int] = field(default_factory=dict)
    #: Rules that make any hit a Critical Hit (Paralyzed, Unconscious).
    automatic_critical: tuple[str, ...] = ()

    @property""",
)
sub(
    """    else:
        hit, critical = total >= prepared.target_ac, False
""",
    """    else:
        hit, critical = total >= prepared.target_ac, False
    if hit and prepared.automatic_critical:
        critical = True
""",
)
sub(
    """                "disadvantage_sources": list(p.disadvantage_sources),
                "hit": self.hit,""",
    """                "disadvantage_sources": list(p.disadvantage_sources),
                "automatic_critical": list(p.automatic_critical),
                "hit": self.hit,""",
)
sub(
    "from afterworlds.pipeline.rpg.checks import proficiency_bonus\n",
    "from afterworlds.pipeline.rpg.checks import proficiency_bonus\n"
    "from afterworlds.pipeline.rpg.conditions import effective\n",
)
sub(
    "    CoverDefensiveBonusFact,\n",
    "    CoverDefensiveBonusFact,\n    CriticalHitChange,\n    CriticalHitRuleFact,\n",
)
p.write_text(t, encoding="utf-8", newline="\n")
