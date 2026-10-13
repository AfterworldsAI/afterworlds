"""The correspondence T: reviewed C5 source facts -> schema-19 native payloads.

Every C5 source item is mapped by one deterministic function below. The
documented normalizations (``../correspondence.md``) are the only differences:

* absent and ``null`` are one state (a native optional field is ``null``);
* a printed phrase becomes its closed vocabulary member (tables below);
* a C5 union becomes two native fields (``attack_bonus`` / ``_formula`` ...);
* a nested accepted fact drops its ``family`` tag (its type is declared);
* a reserved word is renamed (``from`` -> ``from_skills`` / ``options`` /
  ``chosen_from``, ``while`` -> ``while_state``, ``class`` -> ``class_key``);
* clause pieces are prefixed ``clause_`` and carry their entry, section, part
  and piece index;
* profile lists use accepted families (``creature_ability_score``,
  ``damage_response``, ``condition_effect`` immunity) and a size family;
* moved, not minted: quotes, file/line, ``source_text``/``source_span``,
  headings, ``source_terms``, ``conditional`` phrases, clause/piece text,
  reaction triggers (governed prose and provenance), and capability.

Every output is rebuilt with ``fact_from_payload`` and re-serialized with
``fact_payload``; a payload that is not a fixed point is a mapping defect.
"""

from __future__ import annotations

import dataclasses
import json
import re
import typing
from collections.abc import Iterator
from typing import Any

import common as c

from afterworlds.ingestion.mechanical import representation as R
from afterworlds.ingestion.mechanical.representation import fact_from_payload, fact_payload

Native = dict[str, Any]
#: (record_key, component_key, native payload, provenance hint)
Item = tuple[str, str, Native, dict[str, Any]]

ADVANTAGE_WHEN = {
    "with Advantage if the target doesn't have all its Hit Points": "target_missing_hit_points",
    "with Advantage during the first round of each combat": "first_round_of_each_combat",
}
APPLIES_WHEN = {
    "the effect forcing the save is a spell or other magical effect":
        "forcing_effect_is_a_spell_or_magical",
    "the subject is in sunlight": "subject_in_sunlight",
}
COUNT_FORMULA = {
    "half this spell's level (round down)": "half_spell_level_rounded_down",
    "half the spell's level (round down)": "half_spell_level_rounded_down",
    "half the summoner's Proficiency Bonus (rounded up)":
        "half_summoner_proficiency_bonus_rounded_up",
}
OBSERVER_KIND = {"another creature": "another_creature",
                 "a creature that hears the sounds": "a_creature_that_hears_the_sounds",
                 "a hearer": "a_hearer"}
OBSERVER_PURPOSE = {"to discern the sounds are imitations": "to_discern_the_sounds_are_imitations",
                    "to notice the subject": "to_notice_the_subject"}
SURFACES = {"difficult surfaces, including along ceilings": "difficult_surfaces_including_ceilings",
            "icy surfaces": "icy_surfaces"}
CHOICE_SOURCE = {"the spirit's printed resistances": "this_creatures_resistances",
                 "this creature's Resistances": "this_creatures_resistances"}
ABBREVIATION = {"STR": "strength", "DEX": "dexterity", "CON": "constitution",
                "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma"}
ONE_WORD = {"two": 2, "three": 3, "four": 4, "six": 6, "eight": 8, "ten": 10}


def dice(d: dict[str, Any] | None) -> dict[str, Any] | None:
    """C5 prints a modifier-free term as ``{count, die}``: modifier 0."""
    if d is None:
        return None
    assert set(d) <= {"count", "die", "modifier"}, d
    return {"count": d["count"], "die": d["die"], "modifier": d.get("modifier", 0)}


def untag(o: dict[str, Any], family: str) -> dict[str, Any]:
    assert o["family"] == family, (o, family)
    return {k: v for k, v in o.items() if k != "family"}


def turn(t: dict[str, Any] | None) -> dict[str, Any] | None:
    """A turn boundary; C5's ``possessor`` (the record's own creature, asserted
    by prechecks) is redundant with ``turn_of`` and is not minted."""
    if t is None:
        return None
    assert set(t) <= {"until", "turn", "turn_of", "possessor"}, t
    return {"until": t["until"], "turn": t["turn"], "turn_of": t["turn_of"]}


def span(d: dict[str, Any] | None) -> dict[str, Any] | None:
    if d is None:
        return None
    assert set(d) <= {"amount", "unit", "or_until"}, d
    return {"amount": d["amount"], "unit": d["unit"], "or_until": d.get("or_until")}


def ending(events: list[Any]) -> list[dict[str, Any]]:
    return [{"event": e, "by_creature_within_ft": None} if isinstance(e, str)
            else {"event": e["event"], "by_creature_within_ft": e["by_creature_within_ft"]}
            for e in events]


def choice(d: dict[str, Any] | None) -> dict[str, Any] | None:
    if d is None:
        return None
    out = {k: None for k in ("chosen_for", "chosen_by", "chosen_from", "when", "celestial",
                             "fey", "fiend")}
    for k, v in d.items():
        if k == "from":
            out["chosen_from"] = CHOICE_SOURCE[v]
        elif k == "chosen_from":
            out["chosen_from"] = CHOICE_SOURCE[v]
        elif k == "chosen_for":
            out["chosen_for"] = {"Draconic Origin": "draconic_origin"}[v]
        elif k == "chosen_by":
            out["chosen_by"] = {"GM": "gamemaster"}.get(v, v)
        else:
            assert k in out, k
            out[k] = v
    return out


def term(t: dict[str, Any]) -> dict[str, Any]:
    assert set(t) <= {"average", "dice", "constant", "addends", "damage_type",
                      "damage_type_by_choice"}, t
    return {"average": t.get("average"), "dice": dice(t.get("dice")),
            "constant": t.get("constant"),
            "addends": [{"input": a["input"]} for a in t.get("addends", [])],
            "damage_type": t.get("damage_type"),
            "damage_type_by_choice": choice(t.get("damage_type_by_choice"))}


def when(w: dict[str, Any]) -> dict[str, Any]:
    keys = ("source_bloodied", "target_bloodied", "attack_roll_had_advantage",
            "target_grappled_by_source", "source_moved_straight_toward_target_ft_min",
            "target_maximum_size")
    assert set(w) <= set(keys), w
    return {k: w.get(k) for k in keys}


def conditional_damage(cd: dict[str, Any] | None) -> dict[str, Any] | None:
    if cd is None:
        return None
    assert set(cd) <= {"mode", "term", "when", "replaces_hit_damage_index"}, cd
    return {"mode": cd["mode"], "term": term(cd["term"]), "when": when(cd["when"]),
            "replaces_hit_damage_index": cd.get("replaces_hit_damage_index")}


def forced(f: dict[str, Any] | None) -> dict[str, Any] | None:
    if f is None:
        return None
    assert set(f) <= {"direction", "distance_ft", "distance_ft_up_to"}, f
    return {"direction": f["direction"], "distance_ft": f.get("distance_ft"),
            "distance_ft_up_to": f.get("distance_ft_up_to")}


def rider(r: dict[str, Any] | None) -> dict[str, Any] | None:
    if r is None:
        return None
    allowed = {"applies_to", "effect", "duration", "escape_dc", "maximum_size",
               "conditional_damage", "forced_movement", "linked", "rider_save"}
    assert set(r) <= allowed, set(r) - allowed
    eff = r.get("effect")
    out = {"applies_to": r.get("applies_to"), "condition": None, "speed": None,
           "duration": turn(r.get("duration")), "escape_dc": r.get("escape_dc"),
           "maximum_size": r.get("maximum_size"),
           "conditional_damage": conditional_damage(r.get("conditional_damage")),
           "forced_movement": forced(r.get("forced_movement")),
           "linked": None, "rider_save": None}
    if eff is not None:
        if eff["family"] == "condition_effect":
            out["condition"] = untag(eff, "condition_effect")
        else:
            out["speed"] = untag(eff, "speed_modification")
    if (lk := r.get("linked")) is not None:
        assert lk["until"] == "the grapple ends", lk
        out["linked"] = {"condition": untag(lk["effect"], "condition_effect"),
                         "until": "grapple_ends"}
    if (rs := r.get("rider_save")) is not None:
        out["rider_save"] = {"save": rs["save"], "dc": rs["dc"],
                             "on_failure": untag(rs["on_failure"], "condition_effect"),
                             "duration": turn(rs.get("duration")),
                             "target_excludes": rs.get("target_excludes", [])}
    return out


def formula(v: Any) -> tuple[Any, Any]:
    """An int, or ``{formula_ref, of}``: two native fields."""
    if isinstance(v, dict):
        assert set(v) == {"formula_ref", "of"}, v
        return None, {"formula_ref": v["formula_ref"], "of": v["of"]}
    return v, None


def entry_option(name: str) -> dict[str, Any]:
    m = re.fullmatch(r"(?P<e>.+?) to cast _(?P<s>[^_]+)_(?: \(level (?P<l>\d+) version\))?", name)
    if not m:
        return {"entry": name, "spell": None, "spell_level": None}
    return {"entry": m["e"], "spell": "spells." + re.sub(r"[^a-z0-9]+", "_", m["s"].lower()).strip("_"),
            "spell_level": int(m["l"]) if m["l"] else None}


def multiattack(ma: dict[str, Any]) -> dict[str, Any]:
    assert ma["residue"] == [], ma
    alternatives = []
    for alt in ma["alternatives"]:
        cond = alt["condition"]
        parts = []
        for p in alt["parts"]:
            cnt = p["count"]
            count, count_formula = (cnt, None) if isinstance(cnt, int) else (
                None, "per_head" if cnt.get("per") == "head" else COUNT_FORMULA[cnt["parameterized"]])
            parts.append({"count": count, "count_formula": count_formula,
                          "attack": p.get("attack"), "any_of": p.get("any_of", []),
                          "uses_one_of": [entry_option(x) for x in p.get("uses_one_of", [])],
                          "optional": p.get("optional"), "if_available": p.get("if_available")})
        alternatives.append({"condition": {None: None, "it used Hasten this turn":
                                           "used_hasten_this_turn"}[cond], "parts": parts})
    replacements = []
    for r in ma["replacements"]:
        rp = r["replaces"]
        replacements.append({
            "replaces": rp if isinstance(rp, int) else None,
            "replaces_attack": rp["attack"] if isinstance(rp, dict) else None,
            "replaces_any": True if rp == "any" else None,
            "with_one_of": [entry_option(x) for x in r["with_one_of"]],
            "if_available": r.get("if_available")})
    return {"alternatives": alternatives, "replacements": replacements}


def targets(t: dict[str, Any]) -> dict[str, Any]:
    keys = ("count", "each", "living", "maximum_size", "types", "has_conditions", "area",
            "origin", "origin_point_within_ft", "within_ft", "in_source_space",
            "related_to_source", "requires_source_sees_target", "requires_source_sees_point",
            "requires_target_sees_source", "source_environment", "swallow_capacity",
            "trigger", "excludes", "excludes_types", "automatic_failure_types",
            "automatic_success_types", "willing_or_conditions", "at_hit_points", "stated_by")
    lists = {"types", "has_conditions", "related_to_source", "excludes_types",
             "automatic_failure_types", "automatic_success_types", "willing_or_conditions"}
    out: dict[str, Any] = {k: ([] if k in lists else None) for k in keys}
    for k, v in t.items():
        if k == "count":
            if v == "each":
                out["each"] = True
            else:
                out["count"] = v
        elif k == "origin":
            if isinstance(v, dict):
                out["origin_point_within_ft"] = v["point_within_ft"]
            else:
                out["origin"] = v
        elif k == "area":
            out["area"] = {x: v[x] for x in ("shape", "size_ft", "radius", "width_ft",
                                             "height_ft")}
        elif k == "excludes":
            out["excludes"] = {"currently affected by this effect":
                               "currently_affected_by_this_effect"}[v]
        else:
            assert k in out, k
            out[k] = v
    return out


def locus(rk: str, e: dict[str, Any], part: str, i: int, typed: dict[str, Any]) -> Native:
    return {"entry": e["name"], "section": e["section"], "part": part, "piece": i,
            "branch": typed["branch"], "effect_id": typed.get("effect_id"),
            "bound_effect": typed.get("bound_effect"),
            "lasts_while_effect": typed.get("lasts_while_effect"),
            "ends_effects": typed.get("ends_effects", []),
            "duration_of_effects": typed.get("duration_of_effects", []),
            "under_predicates": typed.get("under_predicates", [])}


LOCUS_KEYS = {"family", "branch", "effect_id", "bound_effect", "lasts_while_effect",
              "ends_effects", "duration_of_effects", "under_predicates"}


def piece(typed: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """One typed clause piece -> (native family, its own fields)."""
    f = typed["family"]
    t = {k: v for k, v in typed.items() if k not in LOCUS_KEYS}

    def only(*keys: str) -> dict[str, Any]:
        assert set(t) <= set(keys), (f, set(t) - set(keys))
        return {k: t.get(k) for k in keys}

    if f in ("ability_disadvantage", "roll_disadvantage", "escape_disadvantage"):
        effects = [untag(x, "advantage") for x in t["effects"]]
        based = None
        if f == "ability_disadvantage":
            # "Disadvantage on Strength-based D20 Tests": the accepted roll
            # shape refuses an ability on the D20 Test umbrella, so it is the
            # dedicated closed value (correspondence.md, representation 1).
            (x,) = effects
            assert x["roll"]["context"] == "d20_test" and x["roll"]["actor"] == "subject", x
            based, effects = {"state": x["state"], "ability": x["roll"]["ability"]}, []
        return "clause_roll_modifier", {
            "subject": t["subject"], "effects": effects, "ability_based": based,
            "purpose": t.get("purpose")}
    if f == "predicate":
        out = only("target_maximum_size", "source_moved_straight_toward_target_ft_min",
                   "attack_roll_had_advantage", "target_is_creature", "target_type",
                   "target_reduced_to_0_hit_points_by_this", "target_hit_points_at_most",
                   "otherwise", "while_condition", "while", "refers_to", "duration", "at")
        out["while_state"] = out.pop("while")
        out["refers_to"] = {None: None, "this poison": "this_poison"}[out["refers_to"]]
        out["duration"] = turn(out["duration"])
        return "clause_predicate", out
    if f == "grapple":
        out = only("condition", "escape_dc", "appendages", "instead_of_damage")
        out["appendages"] = appendages(out["appendages"])
        return "clause_grapple", out
    if f == "condition":
        out = only("effects", "replaces_condition")
        out["effects"] = [untag(x, "condition_effect") for x in out["effects"]]
        return "clause_condition", out
    if f == "timed_condition":
        out = only("effects", "duration", "ends_early_when", "replaces_condition")
        d = out.pop("duration")
        return "clause_timed_condition", {
            "effects": [untag(x, "condition_effect") for x in out["effects"]],
            "duration_turn": turn(d) if "until" in d else None,
            "duration_span": span(d) if "amount" in d else None,
            "ends_early_when": ending(out["ends_early_when"] or []),
            "replaces_condition": out["replaces_condition"]}
    if f == "linked_condition":
        out = only("effects", "while")
        return "clause_linked_condition", {
            "effects": [untag(x, "condition_effect") for x in out["effects"]],
            "while_state": out["while"]}
    if f == "condition_until_repeat":
        out = only("effects", "duration", "repeat_save")
        out["effects"] = [untag(x, "condition_effect") for x in out["effects"]]
        out["duration"] = turn(out["duration"])
        return "clause_condition_until_repeat", out
    if f in ("condition_ends_early", "effect_ends"):
        out = only("ends_early_when")
        return "clause_" + f, {"ends_early_when": ending(out["ends_early_when"])}
    if f == "effect_lasts":
        out = only("duration", "scope")
        out["duration"] = turn(out["duration"])
        return "clause_effect_lasts", out
    if f == "repeat_save":
        return "clause_repeat_save", only("at", "turn_of", "ends_on", "only_if")
    if f == "temporary_immunity":
        out = only("to", "entry", "hours")
        return "clause_temporary_immunity", {"to": out["to"], "immune_to_entry": out["entry"],
                                             "hours": out["hours"]}
    if f == "timed_speed_change":
        out = only("change", "feet", "duration")
        out["duration"] = turn(out["duration"])
        return "clause_timed_speed_change", out
    if f == "timed_ac_modifier":
        out = only("modifier", "duration")
        out["duration"] = turn(out["duration"])
        return "clause_timed_ac_modifier", out
    if f == "next_roll_modifier":
        out = only("roll", "state", "uses", "expires")
        out["roll"] = {"actor": out["roll"]["actor"], "context": out["roll"]["context"],
                       "against": out["roll"].get("against")}
        out["expires"] = turn(out["expires"])
        return "clause_next_roll_modifier", out
    if f == "damage_roll_penalty":
        out = only("average", "dice")
        out["dice"] = dice(out["dice"])
        return "clause_damage_roll_penalty", out
    if f == "damage_branch":
        return "clause_damage_branch", {"terms": [term(x) for x in only("terms")["terms"]]}
    if f == "choice_typed_damage":
        out = only("average", "dice", "damage_type")
        return "clause_choice_typed_damage", {"average": out["average"],
                                              "dice": dice(out["dice"]),
                                              "damage_type": choice(out["damage_type"])}
    if f == "conditional_damage":
        out = only("mode", "term", "when", "replaces_hit_damage_index",
                   "unconditional_hit_damage_indices")
        out["term"] = term(out["term"])
        out["when"] = when(out["when"])
        out["unconditional_hit_damage_indices"] = out["unconditional_hit_damage_indices"] or []
        return "clause_conditional_damage", out
    if f == "periodic_damage":
        out = only("at", "term", "turn_of")
        assert out["at"] == "start_of_each_turn", out
        return "clause_periodic_damage", {"at": "start_of_turn", "term": term(out["term"]),
                                          "turn_of": out["turn_of"]}
    if f == "periodic_hit_point_loss":
        out = only("at", "average", "dice", "turn_of")
        assert out["at"] == "start_of_each_turn", out
        return "clause_periodic_hit_point_loss", {"at": "start_of_turn",
                                                  "average": out["average"],
                                                  "dice": dice(out["dice"]),
                                                  "turn_of": out["turn_of"]}
    if f == "zero_hit_point_outcome":
        return "clause_zero_hit_point_outcome", only("becomes", "when")
    if f == "named_effect":
        out = only("name", "duration")
        out["duration"] = span(out["duration"])
        return "clause_named_effect", out
    if f == "forced_movement":
        return "clause_forced_movement", only("direction", "distance_ft", "distance_ft_up_to")
    if f == "area_origin_point":
        return "clause_area_origin_point", only("within_ft", "requires_source_sees_point",
                                                "centered_on")
    if f == "aura":
        return "clause_aura", only("emanation_ft", "suspended_while_source_has",
                                   "targets_within")
    if f == "rescue_check":
        return "clause_rescue_check", only("actor_within_ft", "uses", "check", "ends")
    simple = {"branch": (), "nested_save_trigger": (), "condition_ends": ("condition",),
              "repeat_save_limit": ("automatic_success_after_minutes",),
              "nested_save": ("ability", "dc"), "d20_test_penalty_die": ("contexts", "count",
                                                                         "die"),
              "penalty_die_application": ("subtracts_from",),
              "hit_point_regain_prohibition": ("hit_points",), "hit_points_set": ("to",),
              "follow_up_attack": ("attack", "count", "optional"),
              "targeting_restriction": ("source_attack", "excludes"),
              "damage_qualification": ("underwater_fire_resistance_applies",),
              "returning_weapon": ("weapon", "or_hovers_within_ft"),
              "save_success": ("half_damage",), "save_timing": ("at", "turn", "turn_of"),
              "self_save_predicate": ("when",), "source_movement": ("up_to",),
              "trigger": ("on",)}
    out = only(*simple[f])
    if f == "targeting_restriction":
        out["excludes"] = {"the creature grappled by this attack":
                           "the_creature_grappled_by_this_attack"}[out["excludes"]]
    return "clause_" + f, out


def appendages(text: str | None) -> dict[str, Any] | None:
    if text is None:
        return None
    if m := re.fullmatch(r"one of (\w+) (\w+)", text):
        return {"use": "one", "of": ONE_WORD[m[1]], "appendage": m[2]}
    if m := re.fullmatch(r"all (\w+) (\w+)", text):
        return {"use": "all", "of": ONE_WORD[m[1]], "appendage": m[2]}
    if m := re.fullmatch(r"both (?:of the [\w' -]+?'s )?(\w+ ?\w*)", text):
        return {"use": "both", "of": None, "appendage": m[1].replace(" ", "_")}
    raise AssertionError(text)


def predicate(p: Any) -> dict[str, Any] | None:
    keys = ("stated", "subject_not", "subject_bloodied", "ally_not", "ally_within_ft_of_target",
            "target_missing_hit_points", "attack")
    if p is None:
        return None
    if isinstance(p, str):
        return {**{k: None for k in keys}, "stated": APPLIES_WHEN[p]}
    assert set(p) <= set(keys), p
    return {k: p.get(k) for k in keys}


def entry_items(rk: str, e: dict[str, Any]) -> Iterator[tuple[str, Native]]:
    base = {"entry": e["name"], "section": e["section"]}
    kind = e["kind"]
    if kind == "attack":
        a = e["attack"]
        bonus, bonus_formula = formula(a["attack_bonus"])
        adv = a["advantage_when"]
        if adv is not None and adv not in ADVANTAGE_WHEN:
            assert re.fullmatch(r"with Advantage if the target is Grappled by the \w+", adv), adv
            adv = "target_grappled_by_source"
        elif adv is not None:
            adv = ADVANTAGE_WHEN[adv]
        hd = a.get("hit_damage_by_size")
        yield "creature_attack", {
            **base, "kind": a["kind"], "attack_bonus": bonus,
            "attack_bonus_formula": bonus_formula, "automatic_hit": a.get("automatic_hit"),
            "reach_ft": a["reach_ft"], "normal_range_ft": a["normal_range_ft"],
            "long_range_ft": a["long_range_ft"], "advantage_when": adv,
            "hit_damage": [term(x) for x in a["hit_damage"]],
            "hit_damage_by_size": None if hd is None else {
                k: [term(x) for x in hd[k]] for k in ("medium_or_smaller", "large", "huge")},
            "size_input": {None: None, "the creature's recorded size": "recorded_size"}[
                a.get("size_input")],
            "hit_effect": rider(a["hit_effect"])}
        yield from clause_items(rk, e, a.get("clauses", []))
    elif kind == "save_effect":
        s = e["save"]
        dc, dc_formula = formula(s["dc"])
        yield "creature_save_effect", {
            **base, "save": s["save"], "dc": dc, "dc_formula": dc_formula,
            "targets": targets(s["targets"]),
            "failure_damage": [term(x) for x in s["failure_damage"]],
            "failure_effect": rider(s["failure_effect"]), "success": s["success"],
            "reuse_limit": (s.get("reuse_limit") or {}).get("kind")}
        yield from clause_items(rk, e, s.get("clauses", []))
    elif kind == "multiattack":
        yield "creature_multiattack", {**base, **multiattack(e["multiattack"])}
    elif kind == "entry_reference":
        yield "creature_entry_reference", {**base, "references": e["references"]}
    elif kind == "observer_check":
        o = e["observer_check"]
        yield "creature_observer_check", {
            **base, "check": o["check"], "made_by": OBSERVER_KIND[o["made_by"]],
            "purpose": OBSERVER_PURPOSE[o["purpose"]], "only_if": o.get("only_if")}
    if "usage" in e and "text" not in e["usage"]:
        u = e["usage"]
        yield "creature_entry_usage", {
            **base, "kind": u["kind"], "uses": u.get("uses"), "in_lair": u.get("in_lair"),
            "minimum_d6": u.get("minimum_d6"), "forms": u.get("forms", []),
            "recharge_after_long_rest": u.get("recharge_after_long_rest"),
            "requires_entry": u.get("entry")}
    if "grants_conditions" in e:
        yield "creature_condition_grant", {**base, "subject": e["subject"],
                                           "conditions": e["grants_conditions"]}
    if (con := e.get("contributor")) is not None:
        subj = {"subject": e["subject"]}
        if "save_override" in con:
            assert set(con) == {"save_override"}, con
            yield "creature_save_override", {**base, **subj, "save_override": con["save_override"]}
        elif "save_damage_override" in con:
            yield "creature_save_damage_override", {
                **base, **subj, "applies_when": predicate(con.get("applies_when")),
                "save_damage_override": con["save_damage_override"]}
        elif con.get("family") == "check_requirement_removal":
            yield "check_requirement_removal", {
                **base, **subj, "check": con["check"], "surfaces": SURFACES[con["surfaces"]],
                "also": con.get("also"), "applies_when": con.get("applies_when")}
        elif con.get("family") == "zero_hit_point_save":
            assert con["trigger"] == "damage reduces the subject to 0 Hit Points", con
            assert con["on_success"]["instead_of"] == "0 Hit Points", con
            yield "zero_hit_point_save", {
                **base, **subj, "trigger": "damage_reduces_subject_to_zero_hit_points",
                "save": con["save"], "dc": con["dc"], "unless": con["unless"],
                "on_success": {"set_hit_points": con["on_success"]["set_hit_points"],
                               "instead_of_zero_hit_points": True}}
        elif con["effects"][0]["family"] == "hit_point_regain_prohibition":
            (x,) = con["effects"]
            assert set(con) == {"effects"}, con
            yield "creature_hit_point_regain_prohibition", {
                **base, **subj, "hit_points": x["hit_points"],
                "temporary_hit_points": x.get("temporary_hit_points")}
        else:
            assert set(con) <= {"effects", "applies_when", "skill", "purpose"}, con
            yield "creature_roll_modifier", {
                **base, **subj, "applies_when": predicate(con.get("applies_when")),
                "effects": [untag(x, "advantage") for x in con["effects"]],
                "skill": con.get("skill"),
                "purpose": {None: None, "to ascertain the subject's intentions or sincerity":
                            "to_ascertain_intentions_or_sincerity"}[con.get("purpose")]}


def clause_items(rk: str, e: dict[str, Any], clauses: list[dict[str, Any]]
                 ) -> Iterator[tuple[str, Native]]:
    for cl in clauses:
        for i, p in enumerate(cl["pieces"]):
            if "typed" not in p:
                continue
            fam, own = piece(p["typed"])
            yield fam, {**locus(rk, e, cl["part"], i, p["typed"]), **own}


def profile_items(r: dict[str, Any]) -> Iterator[Native]:
    p = r["profile"]
    assert p["family"] == "creature_defensive_profile" and p["verbatim"] == [], p
    yield {"family": "creature_size", "sizes": p["sizes"]}
    for ability, v in p["abilities"].items():
        yield {"family": "creature_ability_score", "ability": ability, "score": v["score"],
               "modifier": None, "save_modifier": v["save"]}
    for kind, response in (("immunity", "immunity"), ("resistance", "resistance"),
                           ("vulnerability", "vulnerability")):
        for x in p[kind]:
            if isinstance(x, str):
                yield {"family": "damage_response", "response": response, "scope": "specific",
                       "damage_type": x, "except_types": []}
            else:
                yield conditional_defense(kind, x)
    for x in p["condition_immunity"]:
        if isinstance(x, str):
            yield {"family": "condition_effect", "condition": x, "effect": "immunity"}
        else:
            yield conditional_defense("condition_immunity", x)


def conditional_defense(kind: str, x: dict[str, Any]) -> Native:
    """A qualified defensive entry. The condition of a qualified condition
    immunity is read from its ``conditional`` phrase where the predicate does
    not repeat it (the Archmage's *"charmed, while under Mind Blank"*)."""
    pred = x.get("predicate", {})
    out: Native = {"family": "creature_conditional_defense", "kind": kind, "condition": None,
                   "damage_type": None, "while_active_effect": None,
                   "unless_source_is": None, "attack": None, "attacker_active_effect": None,
                   "selection": None}
    if kind == "condition_immunity":
        out["condition"] = pred.get("condition") or x["conditional"].split(",")[0].strip()
        out["while_active_effect"] = pred.get("active_effect_on_subject")
        out["unless_source_is"] = pred.get("unless_source_is")
    elif "selection" in x:
        s = x["selection"]
        out["selection"] = {"vocabulary": s["vocabulary"],
                            "chosen_by": {"GM": "gamemaster"}[s["chosen_by"]],
                            "chosen_for": {"Draconic Origin": "draconic_origin"}[s["chosen_for"]]}
    else:
        out["damage_type"] = pred["damage_type"]
        out["attack"] = pred["attack"]
        out["attacker_active_effect"] = pred["attacker_active_effect"]
    return out


def defense_item(r: dict[str, Any]) -> Native:
    d = r["defense"]
    if d["family"] == "creature_defense":
        return d
    ac, hp = d["armor_class"], d["hit_points"]
    hp_keys = ("base", "per_spell_level", "per_spell_level_above", "by_size", "half_of")
    return {"family": "creature_defense_parameterized",
            "armor_class": ac if isinstance(ac, int) else None,
            "armor_class_formula": None if isinstance(ac, int) else {
                "base": ac["base"], "per_spell_level": ac["per_spell_level"]},
            "hit_points": {k: hp.get(k) for k in hp_keys}}


def b_items() -> Iterator[Item]:
    b = json.loads(c.pinned(c.C5 / "c5b.json", c.C5_SHA256["c5b.json"]))
    for r in b["creatures"]:
        rk, dk = r["record_key"], r["defense_component_key"]
        yield rk, dk, defense_item(r), {"kind": "defense", "record": r}
        for p in profile_items(r):
            yield rk, dk, p, {"kind": "profile", "record": r}
        for e in r["entries"]:
            for fam, payload in entry_items(rk, e):
                yield rk, e["component_key"], {"family": fam, **payload}, {
                    "kind": "entry", "record": r, "entry": e}


# C5-A / C5-C ---------------------------------------------------------------


def progression(g: dict[str, Any] | None) -> dict[str, Any] | None:
    if g is None:
        return None
    return {"entitlement_key": untag(g, "progression_entry")["entitlement_key"]}


def ref(text: str) -> dict[str, str]:
    record, component = text.split("/")
    return {"record_key": record, "component_key": component}


def selector(o: dict[str, Any]) -> dict[str, Any]:
    return {"tool_variants_of": o.get("tool_variants_of"), "tool_category": o.get("tool_category"),
            "any_tool_entry": o.get("any_tool_entry")}


def a_fact(f: dict[str, Any]) -> Native:
    x = dict(f)
    fam = x["family"]

    def fill(*keys: str) -> Native:
        assert set(x) - {"family"} <= set(keys), (fam, set(x) - {"family"} - set(keys))
        return {"family": fam, **{k: x.get(k) for k in keys}}

    if fam == "weapon_property":
        out = {"family": "weapon_property", "weapon_property": x["property"]}
        if "two_handed_dice" in x:
            out["versatile_damage"] = dice(x["two_handed_dice"])
        if x["property"] == "thrown":
            out["thrown_range_normal_feet"] = x["normal_range_ft"]
            out["thrown_range_long_feet"] = x["long_range_ft"]
        out.setdefault("versatile_damage", None)
        out.setdefault("thrown_range_normal_feet", None)
        out.setdefault("thrown_range_long_feet", None)
        if x["property"] == "ammunition":
            out.update(ammunition=x["ammunition"], ammunition_range_normal_feet=x["normal_range_ft"],
                       ammunition_range_long_feet=x["long_range_ft"])
        if "except_when" in x:
            out["unless"] = x["except_when"]
        return out
    if fam in ("damage", "ability_check"):
        return x
    if fam == "skill_proficiency_choice":
        frm = x.get("from")
        el = x.get("eligibility")
        return {"family": fam, "count": x["count"],
                "from_skills": frm if isinstance(frm, list) else [],
                "from_reference": ref(frm) if isinstance(frm, str) else None,
                "context": x.get("context"),
                "eligibility": None if el is None else {
                    "class_key": el["class"], "subclass_key": el["subclass"],
                    "minimum_class_level": el["minimum_class_level"]},
                "gain_levels": progression(x.get("gain_levels")),
                "or_tools": None if "or_tools" not in x else selector(x["or_tools"]["from"]),
                "repeatable": x.get("repeatable")}
    if fam == "multiclass_skill_proficiency_choice":
        frm = x.get("from")
        return {"family": fam, "count": x["count"],
                "from_skills": frm if isinstance(frm, list) else [],
                "from_reference": ref(frm) if isinstance(frm, str) else None}
    if fam == "saving_throw_proficiency_grant":
        return {"family": fam, "abilities": [ABBREVIATION.get(a, a) for a in x["abilities"]],
                "context": x.get("context"), "gain_levels": progression(x.get("gain_levels"))}
    if fam == "weapon_proficiency_grant":
        return {"family": fam, "categories": x["categories"], "qualified": x.get("qualified", []),
                "context": x.get("context")}
    if fam == "armor_training_grant":
        return fill("armor", "shields", "context")
    if fam == "tool_proficiency_grant":
        return fill("tools", "context")
    if fam == "tool_proficiency_choice":
        frm = x["from"]
        return {"family": fam, "count": x["count"],
                "options": [selector(o) for o in (frm if isinstance(frm, list) else [frm])],
                "context": x.get("context")}
    if fam == "multiclass_proficiency_grant":
        tools = x.get("tools")
        choice_ = grant_ = None
        if tools and tools["family"] == "tool_proficiency_choice":
            choice_ = {"count": tools["count"], "options": [selector(tools["from"])]}
        elif tools:
            grant_ = tools["tools"]
        return {"family": fam, "saving_throws": x["saving_throws"], "weapons": x["weapons"],
                "armor_training": x["armor_training"], "tool_choice": choice_,
                "tool_grant": grant_ or []}
    if fam == "weapon_and_armor_grant":
        return {**fill("weapons", "armor_training", "chosen_option_of", "gain_levels"),
                "gain_levels": progression(x["gain_levels"])}
    if fam == "weapon_mastery_choice":
        cbl = x.get("count_by_level", {})
        return {"family": fam, "kinds_of_weapons": x["kinds_of_weapons"],
                "categories": x.get("categories", []), "melee_only": x.get("melee_only"),
                "requires_weapon_proficiency": x.get("requires_weapon_proficiency"),
                "count_by_level": [{"level": int(k), "count": v}
                                   for k, v in sorted(cbl.items(), key=lambda kv: int(kv[0]))],
                "rest_swap": x["rest_swap"], "gain_levels": progression(x["gain_levels"])}
    if fam == "feat_choice":
        return {**fill("count", "count_per_gain", "category", "named_feat",
                       "or_any_feat_whose_prerequisites_are_met", "gain_levels"),
                "gain_levels": progression(x.get("gain_levels"))}
    if fam == "feat_grant":
        return {"family": fam, "feat": x["feat"],
                "qualifier": None if "qualifier" not in x else x["qualifier"].lower()}
    if fam == "ability_increase_choice":
        ab = x["abilities"]
        return {"family": fam, "abilities": ab if isinstance(ab, list) else [],
                "any_ability": True if ab == "any" else None,
                "patterns": x.get("patterns", []), "distinct_abilities": x.get("distinct_abilities"),
                "maximum_score": x.get("maximum_score"), "repeatable": x.get("repeatable"),
                "rule": ref(x["rule"]) if "rule" in x else None}
    if fam == "expertise_choice":
        return {"family": fam, "count_per_gain": x["count_per_gain"],
                "from_proficient_skills": x["from_proficient_skills"],
                "from_skills": x.get("from", []), "gain_levels": progression(x["gain_levels"])}
    if fam == "mastery_effect":
        out = fill("mastery", "trigger", "optional", "applies_to", "against", "cost", "damage",
                   "damage_type", "increase", "ability_modifier_damage", "limit",
                   "second_target_within_ft", "second_target_within_reach", "direction",
                   "distance_ft_up_to", "maximum_size", "speed_reduction_ft",
                   "maximum_reduction_ft", "duration", "effect", "save", "dc", "on_failure")
        out["duration"] = turn(out["duration"])
        out["effect"] = None if out["effect"] is None else untag(out["effect"], "advantage")
        out["on_failure"] = [untag(o, "condition_effect") for o in (out["on_failure"] or [])]
        return out
    if fam == "usage_limit_rule":
        rg = x.get("regain", [])
        return {**fill("kind", "regain", "also_regain", "die", "roll_at", "turn_of"),
                "regain": rg if isinstance(rg, list) else [rg],
                "also_regain": x.get("also_regain", [])}
    if fam == "zero_hit_point_outcome":
        out = fill("subject", "outcome", "gamemaster_exception", "exception_scope", "trigger",
                   "until")
        out["exception_scope"] = {None: None, "individual monster": "individual_monster"}[
            out["exception_scope"]]
        return out
    if fam == "critical_damage":
        return {"family": fam, "applies_to": {"every damage die of the attack":
                                              "every_damage_die_of_the_attack"}[x["applies_to"]],
                "damage_dice_multiplier": x["damage_dice_multiplier"],
                "modifiers": {"added once": "added_once"}[x["modifiers"]]}
    if fam == "stable_state":
        out = dict(x)
        out["recovery"] = {**x["recovery"], "dice": dice(x["recovery"]["dice"])}
        return out
    if fam == "ammunition_expenditure":
        out = dict(x)
        out["loading_requires_free_hand"] = {"when": {"the weapon is one-handed":
                                                      "weapon_is_one_handed"}[
            x["loading_requires_free_hand"]["when"]]}
        return out
    if fam == "armor_training_penalty":
        return {**x, "applies_when": {"the wearer lacks training with the worn armor's category":
                                      "wearer_lacks_training_with_worn_armor_category"}[
            x["applies_when"]]}
    if fam == "death_save_natural_roll":
        return fill("face", "failures", "regain_hit_points")
    if fam == "light_extra_attack":
        return x
    return x


def complete(payload: Native) -> Native:
    """Absent and null are one state: fill every declared field a C5 payload
    leaves out with ``null`` (or an empty list for a sequence), except the
    registered omit-when-empty fields, which stay absent."""
    cls = R._FACT_TYPES[R.FactFamily(payload["family"])]
    omitted = R._POST_SCHEMA_3_FIELDS.get(cls.__name__, {})
    hints = typing.get_type_hints(cls)
    out = dict(payload)
    for f in dataclasses.fields(cls):
        if f.name not in out and f.name not in omitted:
            out[f.name] = [] if typing.get_origin(hints[f.name]) in (tuple, list) else None
    return out


def ac_items() -> Iterator[Item]:
    for part in ("c5a.json", "c5c.json"):
        for f in json.loads(c.pinned(c.C5 / part, c.C5_SHA256[part]))["facts"]:
            # A tool activity: the option of the component's choice this
            # fact belongs to (its printed text stays governed prose).
            option = (f.get("option") or {}).get("semantic_key", "")
            hint = {"kind": "quote", "part": part, "source": f["source"], "option": option}
            yield f["record_key"], f["component_key"], complete(a_fact(f["fact"])), hint
            if option:
                # The activity's selectable identity (correspondence.md, tool
                # activities): one per C5 activity option, on the same option
                # and source as the activity's check.
                yield f["record_key"], f["component_key"], {
                    "family": "tool_activity", "activity": option}, {
                    **hint, "derived": "tool_activity_identity",
                    "option_text": f["option"]["text"]}


def items() -> Iterator[Item]:
    yield from ac_items()
    yield from b_items()


def check_round_trip() -> dict[str, Any]:
    """Every mapped payload rebuilds under schema 19 and is a fixed point."""
    n, families = 0, {}
    for rk, ck, payload, _ in items():
        fact = fact_from_payload(payload)
        again = fact_payload(fact)
        assert again == payload, (rk, ck, payload["family"],
                                  {k: (payload.get(k), again.get(k)) for k in payload.keys() | again.keys()
                                   if payload.get(k) != again.get(k)})
        findings = R._FACT_INVARIANTS[R.FactFamily(payload["family"])](fact)
        assert not findings, (rk, ck, payload["family"], findings)
        n += 1
        families[payload["family"]] = families.get(payload["family"], 0) + 1
    return {"facts": n, "families": dict(sorted(families.items()))}


if __name__ == "__main__":
    print(json.dumps(check_round_trip(), indent=1))
