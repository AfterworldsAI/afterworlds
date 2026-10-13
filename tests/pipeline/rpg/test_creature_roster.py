"""The creature roster — CRD Issue 15c (codex-c7-recert-coverage-review):
code executes exactly the admitted creature entries and Multiattack
selections, and refuses every other entry before any die."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CAPABILITY = (
    Path(__file__).resolve().parents[3]
    / ".claude/review-notes/issue-15c-implementation/candidate-c5/capability.json"
)

#: C5 blockers settled since by an approved contract, executed in code; the
#: value names the contract and the test proving it.
SETTLED: dict[str, str] = {
    "Pack Tactics": "bystanders, named allies "
    "(test_creature_attacks::test_pack_tactics_needs_a_named_ally_that_can_act)",
    "Recharge needs explicit start-of-turn authority": "OD-15c-2 actor edges, "
    "Recharge at the creature's turn start (test_creature_effects)",
    "area membership needs explicit position authority": "OD-15c-1 targets "
    "selection (test_creature_effects)",
    "range needs explicit position authority": "OD-15c-1 range band "
    "(test_creature_attacks)",
    "timed effect needs explicit actor-turn authority": "OD-15c-2 turn-bounded "
    "condition ends (test_creature_effects)",
    "timed/linked effect needs explicit actor-turn authority": "OD-15c-2 "
    "turn-bounded hit-effect ends (test_creature_attacks)",
}


def _blockers(entry: dict[str, Any]) -> set[str]:
    out = set(entry.get("blocked_by") or ())
    for d in entry.get("dependencies") or ():
        out.add(d.get("cluster") or d["detail"])
    return out


def admitted(entries: dict[str, Any]) -> set[str]:
    """``template:entry`` for every attack or save effect C5 marks
    executable, or whose every blocker is :data:`SETTLED`."""
    out = set()
    for key, entry in entries.items():
        if entry.get("entry_kind") not in ("attack", "save_effect"):
            continue
        blockers = _blockers(entry)
        if entry.get("executable_once_accepted") or (
            blockers and blockers <= SETTLED.keys()
        ):
            template, name = key.split("#")[0], key.split(":", 1)[1]
            out.add(f"{template}:{name}")
    return out


def test_the_roster_is_generated_from_the_accepted_capability() -> None:
    from afterworlds.pipeline.rpg import roster

    data = CAPABILITY.read_bytes()
    assert hashlib.sha256(data).hexdigest() == roster.CAPABILITY_SHA256
    assert admitted(json.loads(data)["entries"]) == roster.EXECUTABLE


# ---------------------------------------------------------------------------
# Every admitted shape, through the adapter's own preflight
# ---------------------------------------------------------------------------

#: C5-positive shapes code does not execute, each a named boundary surfaced
#: for Codex (status.md), not coverage: the refusal must say why.
BOUNDARIES: dict[str, str] = {
    # Restrained "until the grapple ends": no state contract links one
    # condition instance's end to another's.
    "monsters.purple_worm.purple_worm#2:Bite": "linked condition",
    "monsters.remorhaz.remorhaz#1:Bite": "linked condition",
    "monsters.purple_worm.purple_worm#1:Multiattack | alternative 1": (
        "linked condition"
    ),
}


def _scenario(key: str, creature: Any, target: Any) -> Any:
    """A target in the state an entry's own targeting requires."""
    if key == "monsters.glabrezu.glabrezu#4:Pummel":
        import dataclasses

        from afterworlds.models.dnd5e_state import (
            ConditionInstance,
            SubjectReference,
        )
        from afterworlds.models.enums import ConditionVisibility

        grappled = ConditionInstance(
            instance_id="g",
            condition="grappled",  # type: ignore[arg-type]
            visibility=ConditionVisibility.VISIBLE,
            escape_dc=15,
            referent=SubjectReference(kind="creature", subject_id=creature.subject_id),
        )
        state = target.stored.state.model_copy(update={"conditions": (grappled,)})
        return dataclasses.replace(
            target, stored=dataclasses.replace(target.stored, state=state)
        )
    return target


def _results() -> dict[str, tuple[bool, bool, str | None]]:
    """For each C5 attack/save entry and Multiattack selection: (C5
    executable, admitted, refusal or None)."""
    from afterworlds.ingestion.mechanical.representation import (
        CreatureAttackFact,
        CreatureAttackRange,
        CreatureMultiattackFact,
    )
    from afterworlds.models.enums import RollVisibility
    from afterworlds.models.rpg import CreatureSaveEffectSelection, RollProposal
    from afterworlds.pipeline.rpg import creature_clauses
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.capability import AdjudicationRefusal
    from afterworlds.pipeline.rpg.creature_attacks import check_multiattack
    from afterworlds.pipeline.rpg.defense import facts_of
    from afterworlds.pipeline.rpg.roster import EXECUTABLE
    from tests.pipeline.rpg.test_creature_attacks import (
        _bite,
        _medium_wizard,
        _ref,
        _subjects,
    )
    from tests.pipeline.rpg.test_weapon_attacks import _creature

    adapter, wizard = D20RulesSystemAdapter(), _medium_wizard()

    def attack(creature: Any, entry: str) -> None:
        template = creature.stored.state.template_record_key
        fact = next(
            f
            for f in facts_of(creature.index, template)
            if isinstance(f, CreatureAttackFact) and f.entry == entry
        )
        facts: dict[str, Any] = {"target_within_5_feet": True}
        if fact.kind is CreatureAttackRange.RANGED:
            facts = {"range": "within_normal_range", "hostiles_within_5_feet": ()}
        try:
            if creature_clauses.plan(creature, fact).charge_ft:
                facts["moved_straight_toward_target"] = True
        except AdjudicationRefusal:
            pass
        proposal = _bite(creature, wizard, entry=entry, **facts)
        adapter.require_supported(proposal, wizard, _subjects(creature))

    def save(key: str, creature: Any, entry: str) -> None:
        target = _scenario(key, creature, wizard)
        proposal = RollProposal(
            check_label="save effect",
            subsystem_tag="save",
            visibility=RollVisibility.SHOWN,
            operation="creature_save_effect",
            creature_save_effect=CreatureSaveEffectSelection(
                source=_ref(creature),
                entry=entry,
                targets=(_ref(target),),
                auras_in_range=(),
            ),
        )
        adapter.require_supported(proposal, target, _subjects(creature))

    out: dict[str, tuple[bool, bool, str | None]] = {}
    for key, entry in json.loads(CAPABILITY.read_bytes())["entries"].items():
        kind = entry.get("entry_kind")
        template, name = key.split("#")[0], key.split(":", 1)[1]
        if kind not in ("attack", "save_effect", "multiattack"):
            continue
        creature = _creature(template, hp=150)
        why: str | None
        if kind != "multiattack":
            try:
                if kind == "attack":
                    attack(creature, name)
                else:
                    save(key, creature, name)
                why = None
            except AdjudicationRefusal as exc:
                why = f"{exc.kind.value}: {exc.detail}"
            out[key] = (
                bool(entry.get("executable_once_accepted")),
                f"{template}:{name}" in EXECUTABLE,
                why,
            )
            continue
        multiattack = next(
            f
            for f in facts_of(creature.index, template)
            if isinstance(f, CreatureMultiattackFact)
        )
        for selection in entry["selections"]:
            label = selection["selection"]
            alternative = multiattack.alternatives[int(label.split()[1]) - 1]
            certified = {o for g in selection.get("certified_options", []) for o in g}
            entries: list[str] = []
            for part in alternative.parts:
                part_name = part.attack or next(
                    (o for o in part.any_of if not certified or o in certified), None
                )
                if not part.optional and part.count and part_name:
                    entries += [part_name] * part.count
            if " with replacement " in label:
                index = int(label.split(" with replacement ")[1].split(":")[0]) - 1
                replacement = multiattack.replacements[index]
                for _ in range(replacement.replaces or 1):
                    entries.remove(replacement.replaces_attack or entries[-1])
                entries.append(label.split(": ", 1)[1])
            try:
                check_multiattack(creature, entries)
                for part_entry in dict.fromkeys(entries):
                    attack(creature, part_entry)
                why = None
            except AdjudicationRefusal as exc:
                why = f"{exc.kind.value}: {exc.detail}"
            except StopIteration:
                why = "a part is not an attack entry"
            out[f"{key} | {label}"] = (
                bool(selection.get("executable_once_accepted")),
                True,
                why,
            )
    return out


def test_every_admitted_shape_executes_and_every_other_entry_refuses() -> None:
    """C5-positive shapes execute (or are a named boundary); entries outside
    the roster refuse before any die; nothing else is claimed."""
    results = _results()
    failing = {k: why for k, (positive, _, why) in results.items() if positive and why}
    assert set(failing) == set(BOUNDARIES), sorted(set(failing) ^ set(BOUNDARIES))
    for key, why in failing.items():
        assert BOUNDARIES[key] in why, (key, why)
    for key, (positive, admitted_, why) in results.items():
        if not positive and not admitted_:
            assert why is not None, key  # outside the roster: refused
    # Nothing beyond C5 executes unless the roster admits it.
    assert all(admitted_ for _, admitted_, why in results.values() if why is None)
