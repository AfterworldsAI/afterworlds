"""The creature roster — CRD Issue 15c (codex-c7-recert-coverage-review):
code executes exactly the admitted creature entries and Multiattack
selections, and refuses every other entry before any die."""

from __future__ import annotations

import dataclasses
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

#: Admitted entries code does not execute, each a named boundary surfaced
#: for Codex (status.md), not coverage: the refusal must say why. None
#: remain: the Ghast's and Ghoul's Claw exclusions execute from the accepted
#: C8 creature types (test_creature_types), against the harness's Elf target.
BOUNDARIES: dict[str, str] = {}


def _scenario(key: str, creature: Any, target: Any) -> Any:
    """A target in the state the entry's own typed targeting requires: the
    conditions it must have, and those it must have from the source."""
    import dataclasses

    from afterworlds.ingestion.mechanical.representation import (
        ConditionKind,
        CreatureSaveEffectFact,
    )
    from afterworlds.models.dnd5e_state import ConditionInstance, SubjectReference
    from afterworlds.models.enums import ConditionVisibility
    from afterworlds.pipeline.rpg.defense import facts_of

    template, entry = key.split("#")[0], key.split(":", 1)[1]
    fact = next(
        (
            f
            for f in facts_of(creature.index, template)
            if isinstance(f, CreatureSaveEffectFact) and f.entry == entry
        ),
        None,
    )
    if fact is None:
        return target
    source = SubjectReference(kind="creature", subject_id=creature.subject_id)
    conditions = [
        ConditionInstance(
            instance_id=f"has-{kind.value}",
            condition=kind,
            visibility=ConditionVisibility.VISIBLE,
        )
        for kind in fact.targets.has_conditions
    ] + [
        ConditionInstance(
            instance_id=f"from-{kind.value}",
            condition=kind,
            visibility=ConditionVisibility.VISIBLE,
            referent=source,
            escape_dc=15 if kind is ConditionKind.GRAPPLED else None,
        )
        for kind in fact.targets.related_to_source
    ]
    if not conditions:
        return target
    state = target.stored.state.model_copy(update={"conditions": tuple(conditions)})
    return dataclasses.replace(
        target, stored=dataclasses.replace(target.stored, state=state)
    )


def _enemy_only(creature: Any, entry: str) -> bool:
    from afterworlds.ingestion.mechanical.representation import CreatureSaveEffectFact
    from afterworlds.pipeline.rpg.creature_effects import enemy_only
    from afterworlds.pipeline.rpg.defense import facts_of

    template = creature.stored.state.template_record_key
    return any(
        isinstance(f, CreatureSaveEffectFact) and f.entry == entry and enemy_only(f)
        for f in facts_of(creature.index, template)
    )


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
    from tests.pipeline.rpg.test_weapon_attacks import _creature, _dice

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
        adapter.resolve_roll(
            proposal, wizard, None, _dice((15, 15), (1,)), False, _subjects(creature)
        )

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
                # "each enemy": the target is named as the source's enemy.
                enemies_in_area=(
                    (_ref(target),) if _enemy_only(creature, entry) else None
                ),
            ),
        )
        adapter.require_supported(proposal, target, _subjects(creature))
        adapter.resolve_roll(
            proposal, target, None, _dice((15, 15), (1,)), False, _subjects(creature)
        )

    out: dict[str, tuple[bool, bool, str | None]] = {}
    for key, entry in json.loads(CAPABILITY.read_bytes())["entries"].items():
        kind = entry.get("entry_kind")
        template, name = key.split("#")[0], key.split(":", 1)[1]
        if kind not in ("attack", "save_effect", "multiattack"):
            continue
        creature = _creature(template, hp=150)
        # A limited entry's counter is recorded (none expended yet).
        creature = dataclasses.replace(
            creature,
            stored=dataclasses.replace(
                creature.stored,
                state=creature.stored.state.model_copy(update={"usage_counters": ()}),
            ),
        )
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
    """Every admitted attack and save-effect entry (C5-positive, or every
    blocker settled) prepares and resolves in a valid scenario, except the
    named BOUNDARIES; every C5-positive Multiattack selection composes and
    its parts resolve; every entry outside the roster refuses before any
    die."""
    results = _results()
    failing = {
        k: why
        for k, (positive, admitted_, why) in results.items()
        if why and (admitted_ if " | " not in k else positive)
    }
    assert set(failing) == set(BOUNDARIES), sorted(set(failing) ^ set(BOUNDARIES))
    for key, why in failing.items():
        assert BOUNDARIES[key] in why, (key, why)
    for key, (_positive, admitted_, why) in results.items():
        if " | " not in key and not admitted_:
            assert why is not None, key  # outside the roster: refused
