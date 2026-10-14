"""Identity-level reconciliation of the mapped C5 items against the native
proposal facts (Codex native proof review, item 1; tool-selection review).

For every mapped item the expected native address is (batch, record,
component, option) -- after the two disclosed relocations, with a tool's
common facts replicated onto each activity option of a choice -- and the
expected payload is its complete mapped payload. The facts each new proposal
adds over its replayed proposal must equal that multiset exactly: nothing
missing, nothing extra, no multiplicity off. Also:

* the tool activity table: each C5 activity -> its native selectable address
  (an option, or the component directly for a single activity), its check,
  and how many times each common tool fact is stated;
* ``tool_activity`` vocabulary == the 34 C5 activity option keys, each on
  its own C5 tool only;
* negative controls: two options carrying the same activity identity (and
  the three identical-numeric pairs without it) are still refused by the
  unchanged ``option_set_violations``;
* every dropped duration ``possessor`` sits on a boundary whose retained
  ``turn_of`` is ``source`` (prechecks proves it names the record's creature).

FOCUSED DIAGNOSTICS ONLY. Writes ../reports/reconcile.json.
"""

from __future__ import annotations

import collections
import json
from typing import Any

import build_proposals
import common as c
import native_map as m

from afterworlds.ingestion.mechanical import representation as R


def canon(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def added(old: Any, new: Any) -> collections.Counter[tuple[str, str, str, str]]:
    """(record, component, option, payload) of every fact *new* states over *old*."""
    out: collections.Counter[tuple[str, str, str, str]] = collections.Counter()
    before = {(x.record_key, x.semantic_key): x for x in old.components}

    def facts(comp: Any) -> collections.Counter[tuple[str, str]]:
        n: collections.Counter[tuple[str, str]] = collections.Counter(
            ("", canon(R.fact_payload(f))) for f in comp.facts)
        for o in comp.options:
            n.update((o.semantic_key, canon(R.fact_payload(f))) for f in o.facts)
        return n

    for comp in new.components:
        key = (comp.record_key, comp.semantic_key)
        prior = before.get(key)
        delta = facts(comp) - (facts(prior) if prior else collections.Counter())
        lost = (facts(prior) - facts(comp)) if prior else collections.Counter()
        assert not lost, ("a replayed fact disappeared", key, lost)
        for (option, payload), n in delta.items():
            out[(key[0], key[1], option, payload)] += n
    assert len(new.components) == len(old.components)
    return out


def main() -> None:
    proposals, preport = build_proposals.build()
    owners = build_proposals.owner_map()
    relocated = {(r["family"], tuple(r["c5_component"]), r["quote"]): tuple(r["native_component"])
                 for r in preport.get("relocations", [])}

    # Expected, item by item.
    placed: dict[tuple[str, str], list[tuple[str, dict[str, Any], str]]] = (
        collections.defaultdict(list))
    items = 0
    for rk, ck, payload, hint in m.items():
        items += 1
        target = relocated.get((payload["family"], (rk, ck), (hint.get("source") or {})
                                .get("quote", "")), (rk, ck))
        placed[target].append((owners[(rk, ck)], payload, hint.get("option", "")))
    expected: dict[str, collections.Counter[tuple[str, str, str, str]]] = (
        collections.defaultdict(collections.Counter))
    for (rk, ck), xs in placed.items():
        options = sorted({o for _, _, o in xs if o})
        choice = len(options) > 1
        for batch, payload, option in xs:
            for o in (options if choice and not option else [option if choice else ""]):
                expected[batch][(rk, ck, o, canon(payload))] += 1

    batches, ok = {}, True
    for batch in c.AFFECTED:
        got = added(c.replayed(batch).proposed_representation,
                    proposals[batch].proposed_representation)
        missing, extra = expected[batch] - got, got - expected[batch]
        batches[batch] = {"expected": sum(expected[batch].values()), "added": sum(got.values()),
                          "missing": len(missing), "extra": len(extra)}
        ok &= not missing and not extra

    # Tool activity table.
    tools = []
    for (rk, ck), xs in sorted(placed.items()):
        acts = sorted({o for _, _, o in xs if o})
        if not acts:
            continue
        choice = len(acts) > 1
        common = collections.Counter(p["family"] for _, p, o in xs if not o)
        tools.append({
            "record": rk, "component": ck,
            "shape": "choice" if choice else "direct (single activity)",
            "activities": [{
                "c5_option": a,
                "native_address": f"option {a}" if choice else "component (direct)",
                "facts": sorted(p["family"] if p["family"] != "ability_check" else
                                f"ability_check {p['ability']} DC {p['dc_value']}"
                                for _, p, o in xs if o == a)} for a in acts],
            "common_facts": {f: {"c5": n, "native": n * (len(acts) if choice else 1)}
                             for f, n in sorted(common.items())}})
    c5_keys = {f["option"]["semantic_key"] for f in json.loads(
        c.pinned(c.C5 / "c5a.json", c.C5_SHA256["c5a.json"]))["facts"] if f.get("option")}
    vocab_ok = {x.value for x in R.ToolActivity} == c5_keys and len(c5_keys) == 34
    own_tool = all(len({(t["record"], t["component"]) for t in tools
                        if any(a["c5_option"] == k for a in t["activities"])}) == 1
                   for k in c5_keys)

    # Negative controls on the unchanged option validator.
    check = R.fact_from_payload({"family": "ability_check", "ability": "intelligence",
                                 "context": "ability_check", "dc_kind": "fixed", "dc_value": 15})
    entry = R.fact_from_payload({"family": "tool_entry", "ability": "intelligence",
                                 "category": "artisans_tools"})

    def opts(*acts: str | None) -> tuple[Any, ...]:
        return tuple(R.ComponentOption(semantic_key=f"o{i}", facts=tuple(
            [entry, check] + ([R.ToolActivityFact(activity=R.ToolActivity(a))] if a else [])))
            for i, a in enumerate(acts))

    negatives = {
        "same activity identity on two options refused": bool(R.option_set_violations(
            (), opts("identify_a_substance", "identify_a_substance"), "t")),
        "identical-numeric pair without identities refused": bool(R.option_set_violations(
            (), opts(None, None), "t")),
        "distinct identities admitted": not R.option_set_violations(
            (), opts("identify_a_substance", "start_a_fire"), "t"),
        "single option refused": bool(R.option_set_violations(
            (), opts("identify_a_substance"), "t")),
    }

    # Dropped possessors agree with the retained role.
    pairs: collections.Counter[str] = collections.Counter()

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            if "possessor" in o:
                pairs[o.get("turn_of", "MISSING")] += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(c.pinned(c.C5 / "c5b.json", c.C5_SHA256["c5b.json"])))
    possessor_ok = set(pairs) == {"source"}

    report = {
        "label": "FOCUSED DIAGNOSTICS ONLY", "mapped_items": items, "batches": batches,
        "identity_reconciled": ok, "relocations": preport.get("relocations", []),
        "tool_activities": tools, "tool_activity_vocabulary_equals_c5_keys": vocab_ok,
        "each_activity_on_its_own_tool_only": own_tool, "negative_controls": negatives,
        "dropped_possessors_by_retained_turn_of": dict(pairs),
        "proposal_report": {k: v for k, v in preport.items() if k != "relocations"},
    }
    (c.NATIVE / "reports" / "reconcile.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("tool_activities", "proposal_report")}, indent=1))
    assert ok and vocab_ok and own_tool and all(negatives.values()) and possessor_ok


if __name__ == "__main__":
    main()
