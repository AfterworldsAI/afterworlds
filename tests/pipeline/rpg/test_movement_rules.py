"""Every movement rule cites its Rules Package record (issue #211 acceptance
10). Structured facts are read from the package; each prose-encoded rule
checks its sentence in the package's qualified prose source, so a change to
either fails here."""

from __future__ import annotations

import pytest

from afterworlds.pipeline.rpg import movement
from afterworlds.pipeline.rpg.movement import (
    CITATIONS,
    HOUSE_RULE_SQUEEZING,
    PROSE,
    MovementRules,
    RulesChanged,
    load_rules,
)
from tests.pipeline.rpg.movement_support import (
    PROSE_DIR,
    has_component,
    oracle_lookup,
    rules,
)


@pytest.mark.parametrize("rule", sorted(CITATIONS))
def test_every_rule_cites_a_record_that_exists(rule: str) -> None:
    record, component = CITATIONS[rule]
    assert has_component(record, component), f"{rule}: {record} › {component} is gone"


@pytest.mark.parametrize("rule", sorted(PROSE))
def test_every_prose_rule_still_reads_the_same(rule: str) -> None:
    source, sentence = PROSE[rule]
    text = " ".join((PROSE_DIR / source).read_text(encoding="utf-8").split())
    assert " ".join(sentence.split()) in text, f"{rule}: its record's prose changed"


def test_prose_encoded_rules_have_no_structured_facts_yet() -> None:
    """If the package starts stating these as facts, adjudication should read
    them instead of the code's encoding."""
    for rule in (
        "square_size",
        "corners",
        "moving_around_creatures",
        "long_jump",
        "high_jump",
        "prone_movement",
        "dash_special_speed",
    ):
        record, component = CITATIONS[rule]
        assert oracle_lookup(record, component) == (), rule


def test_structured_facts_load_as_encoded() -> None:
    r = rules()
    assert r == MovementRules(
        difficult_extra_per_ft=1,
        climb_extra_per_ft=1,
        swim_extra_per_ft=1,
        crawl_extra_per_ft=1,
        dash_adds_own_speed=True,
        disengage_avoids_opportunity_attacks=True,
        fall_die="d6",
        fall_dice_per_ft=10,
        fall_max_dice=20,
        fall_leaves_prone=True,
        difficult_landing_dc=10,
    )
    # Prose-encoded numbers, from the sentences above.
    assert (r.square_ft, r.jump_run_up_ft, r.high_jump_base_ft) == (5, 10, 3)


def _without(record: str, component: str) -> movement.FactLookup:
    def lookup(rec: str, comp: str) -> tuple[object, ...]:
        if (rec, comp) == (record, component):
            return ()
        return oracle_lookup(rec, comp)

    return lookup


@pytest.mark.parametrize(
    "rule",
    [
        "difficult_terrain_cost",
        "climbing_cost",
        "swimming_cost",
        "dash",
        "disengage",
        "fall_damage",
        "prone_on_landing",
        "difficult_landing",
    ],
)
def test_a_missing_structured_fact_fails_loudly(rule: str) -> None:
    with pytest.raises(RulesChanged):
        load_rules(_without(*CITATIONS[rule]))


def test_a_changed_structured_fact_fails_loudly() -> None:
    import dataclasses

    def swapped(rec: str, comp: str) -> tuple[object, ...]:
        facts = oracle_lookup(rec, comp)
        if (rec, comp) == CITATIONS["disengage"]:
            return tuple(
                (
                    dataclasses.replace(f, provokes=True)  # type: ignore[type-var]
                    if hasattr(f, "provokes")
                    else f
                )
                for f in facts
            )
        return facts

    with pytest.raises(RulesChanged):
        load_rules(swapped)


def test_squeezing_is_labelled_a_house_rule() -> None:
    assert HOUSE_RULE_SQUEEZING.startswith("House rule (Owner, Nov 26)")
    assert movement.squeeze_effects(True) == (
        ("attack_rolls", "disadvantage"),
        ("dexterity_saving_throws", "disadvantage"),
        ("attacks_against", "advantage"),
    )
    assert movement.squeeze_effects(False) == ()
