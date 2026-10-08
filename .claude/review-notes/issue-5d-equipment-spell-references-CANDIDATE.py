"""The Equipment, cursed-item and spell reference candidate, in memory.

CRD Issue 5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. There
is deliberately no recording step.

Thirteen of the 23 unresolved citations in the accepted oracle
(``issue-5d-current-reference-disposition-2026-10-03.md`` rows 24, 35, 37,
46, 79-86 and 89) are resolved to labelled routes under the accepted schema-17
semantics (ADR-005d Decision 7): one reviewed decision per citation, a route's
destinations read together in source order (landing first), routes not
exclusive, no destination class-gated. Every destination is an existing
record; the reader reaches a record's one-hop ``CATALOGUE_MEMBER`` records.
``_sources`` checks each drafted group against the pinned source markdown and
the accepted representation.

The candidate is additive: no batch is replaced, so it is the accepted
artifact with ``resolve_references`` applied once under the simulated
reviewer. The other ten citations are deferred and not drafted.

Run: ``python issue-5d-equipment-spell-references-CANDIDATE.py [--write]``.
``--write`` regenerates the proposal and delta files; otherwise they are
checked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceDestination,
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    effective_representation,
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceTargetKind,
    reference_target_key,
    representation_schema_hash,
)


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: The finite-reference-routes harness: its route helpers, delta, round trip
#: and, through it, the findings reader and the scratch release (read-only).
FRR = _load(
    "finite_reference_routes_replacement",
    HERE / "issue-5d-finite-reference-routes-REPLACEMENT.py",
)
REPL = FRR.REPL
APC = FRR.APC
SIMULATED_REVIEWER: str = FRR.SIMULATED_REVIEWER
SIMULATED_RULE: str = FRR.SIMULATED_RULE
SIMULATED_AT = "2026-10-03T00:00:00Z"
_route = FRR._route

ACCEPTED_PATH: Path = FRR.ACCEPTED_PATH
ACCEPTED_SHA256 = "e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca"

TAG = "equipment-spell-references"
PROPOSAL_FILE = HERE / f"issue-5d-{TAG}-PROPOSAL.json"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"
SRC: Path = FRR.SRC

# --- Rows 24, 35 and 37: general "Equipment" pointers. The
# chapter is read whole: its fourteen ``##`` sections in printed order
# (equipment.md 3-2223), Coins the landing; the reader adds each section's
# one-hop catalogue members (weapons, armor, tools, gear, vehicles), which with
# the sections are every ``equipment.`` record (``_sources``).
EQUIPMENT_SECTIONS = tuple(
    f"equipment.{k}"
    for k in (
        "coins",
        "weapons",
        "armor",
        "tools",
        "adventuring_gear",
        "mounts_and_vehicles",
        "lifestyle_expenses",
        "food_drink_and_lodging",
        "hirelings",
        "spellcasting",
        "magic_items",
        "crafting_nonmagical_items",
        "brewing_potions_of_healing",
        "scribing_spell_scrolls",
    )
)
EQUIPMENT = _route(
    "Equipment: the whole chapter, in printed order",
    *((k, "") for k in EQUIPMENT_SECTIONS),
)

# --- Row 46 gameplay-toolbox.md 197: "Such items are detailed in "Magic
# Items."" -- the item descriptions that specify a curse (magic-items.md 247),
# each its own route as for other finite item tables. Euryale curses the
# drawer, not the Deck; the Cursed Items rule (``magic_items.cursed_items``) is
# not an item description and is not routed.
CURSED = (
    ("Armor of Vulnerability", "magic_items.armor_of_vulnerability"),
    ("Berserker Axe", "magic_items.berserker_axe"),
    ("Demon Armor", "magic_items.demon_armor"),
    ("Shield of Missile Attraction", "magic_items.shield_of_missile_attraction"),
)
CURSED_ITEMS = tuple(
    d for name, key in CURSED for d in _route(f"Cursed item: {name}", (key, ""))
)

# --- Rows 79-86: "See "Spells" for the rules on spellcasting." Gaining Spells
# (spells.md 3, preparation included) then Casting Spells (71, with its nine
# entry sections as catalogue members); Spell Descriptions is not the rules.
SPELLCASTING_RULES = _route(
    "Spellcasting rules: Gaining Spells, then Casting Spells",
    ("spells.gaining_spells", ""),
    ("spells.casting_spells", ""),
)
SPELLCASTING_FEATURES = (
    ("classes.bard.spellcasting", "spellcasting", 826),
    ("classes.cleric.spellcasting", "spellcasting", 2148),
    ("classes.druid.spellcasting", "spellcasting", 3418),
    ("classes.paladin.spellcasting", "spellcasting", 5554),
    ("classes.ranger.spellcasting", "spellcasting", 6323),
    ("classes.sorcerer.spellcasting", "spellcasting", 7532),
    ("classes.warlock.pact_magic", "pact_magic", 8911),
    ("classes.wizard.spellcasting", "spellcasting", 10146),
)

# --- Row 89 rules-glossary.md 1317: "the characteristics described in
# "Spells."" -- spells.md 73: Casting Spells explains each entry. A single
# destination is stated as the plain target (``drafts``); the label is review
# text only.
SPELL_CHARACTERISTICS = _route(
    "Spell characteristics: Casting Spells", ("spells.casting_spells", "")
)

EQ = "srd-5.2.1/equipment"
SPELLS = "srd-5.2.1/spells"
#: Equipment and cursed-item drafts, then spell drafts: separately reviewable.
EQUIPMENT_DRAFTS: dict[
    tuple[str, str, str, str], tuple[str, tuple[ReferenceDestination, ...]]
] = {
    (
        "character_creation.create_your_character",
        "starting_equipment",
        "Equipment",
        EQ,
    ): ("#24", EQUIPMENT),
    (
        "monsters.parts_of_a_stat_block",
        "equipping_a_monster_with_other_items",
        "Equipment",
        EQ,
    ): ("#35", EQUIPMENT),
    ("play.exploration", "", 'See "Equipment" for rules on many items', EQ): (
        "#37",
        EQUIPMENT,
    ),
    (
        "gameplay_toolbox.curses_and_magical_contagions",
        "cursed_magic_items",
        "Magic Items",
        "srd-5.2.1/magic-items",
    ): ("#46", CURSED_ITEMS),
}
SPELL_DRAFTS: dict[
    tuple[str, str, str, str], tuple[str, tuple[ReferenceDestination, ...]]
] = {
    **{
        (record, component, "Spells", SPELLS): (f"#{row}", SPELLCASTING_RULES)
        for row, (record, component, _) in enumerate(SPELLCASTING_FEATURES, 79)
    },
    ("glossary.spell", "spell", "Spells", SPELLS): ("#89", SPELL_CHARACTERISTICS),
}
DRAFTS = {**EQUIPMENT_DRAFTS, **SPELL_DRAFTS}
#: Row 36: the same record, text and scope as #35; deferred, not drafted.
DEFERRED_GEAR = ("monsters.parts_of_a_stat_block", "gear", "Equipment", EQ)


def drafts(
    inputs: AcceptedInputs,
    which: dict[
        tuple[str, str, str, str], tuple[str, tuple[ReferenceDestination, ...]]
    ] = DRAFTS,
) -> tuple[ReferenceResolution, ...]:
    """One reviewed resolution per drafted citation, keyed from the artifact."""
    oracle = inputs.oracle
    view = effective_representation(oracle.representation, oracle.reference_resolutions)
    spans: dict[tuple[str, ...], set[str]] = {}
    for claim in view.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            spans.setdefault(claim.target_key, set()).add(claim.span_id)
    by_citation = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): r
        for r in view.references
        if not r.target_record_key
    }
    out = []
    for citation, (row, destinations) in which.items():
        ref = by_citation[citation]
        # The native shape: one destination is the plain target, unlabelled.
        single = destinations if len(destinations) == 1 else ()
        out.append(
            ReferenceResolution(
                resolution_id=f"cited-{row[1:]}-{citation[0]}-{citation[1]}",
                from_record_key=citation[0],
                from_component_key=citation[1],
                source_text=citation[2],
                scope_key=citation[3],
                target_record_key=single[0].target_record_key if single else "",
                release_binding=oracle.binding,
                provenance_span_ids=tuple(sorted(spans[reference_target_key(ref)])),
                destinations=() if single else destinations,
            )
        )
    return tuple(out)


def members(inputs: AcceptedInputs) -> dict[str, set[str]]:
    """catalogue -> its one-hop ``CATALOGUE_MEMBER`` records."""
    out: dict[str, set[str]] = {}
    for rel in inputs.oracle.representation.relationships:
        if rel.kind.value == "catalogue_member":
            out.setdefault(rel.target_record_key, set()).add(rel.source_record_key)
    return out


def _sources(inputs: AcceptedInputs) -> None:
    """Every drafted group is the source's, and every destination is stated."""
    r = inputs.oracle.representation
    kinds = {x.semantic_key: x.kind.value for x in r.records}
    for _, destinations in DRAFTS.values():
        for d in destinations:
            assert d.target_record_key in kinds and not d.target_component_key, d
            assert not (d.situation or d.class_record_key or d.minimum_class_level)
    assert DEFERRED_GEAR not in DRAFTS
    cat = members(inputs)

    # Equipment: the chapter's ## headings are the sections, in order, and the
    # sections with their one-hop members are every equipment. record.
    md = (SRC / "equipment.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", md, re.M)
    slug = [
        "equipment." + re.sub(r"\W+", "_", h.lower().replace(",", "")).strip("_")
        for h in headings
    ]
    assert slug == list(EQUIPMENT_SECTIONS), slug
    reached = set(EQUIPMENT_SECTIONS).union(
        *(cat.get(k, set()) for k in EQUIPMENT_SECTIONS)
    )
    equipment = {k for k in kinds if k.startswith("equipment.")}
    assert reached == equipment, sorted(reached ^ equipment)
    for path, at, needle in (
        ("character-creation.md", 179, 'spent on equipment from "Equipment."'),
        ("character-creation.md", 181, 'Equipment is described in "Equipment,"'),
        ("monsters.md", 183, 'using the items in "Equipment" for inspiration'),
        ("playing-the-game.md", 734, 'See "Equipment" for rules on many items'),
    ):
        text = (SRC / path).read_text(encoding="utf-8").splitlines()[at - 1]
        assert needle in text, (path, at, needle)

    # Cursed items: exactly the four descriptions with a Curse paragraph, each
    # under its own #### heading, in source order.
    toolbox = (SRC / "gameplay-toolbox.md").read_text(encoding="utf-8")
    assert 'Such items are detailed in "Magic Items."' in toolbox
    lines = (SRC / "magic-items.md").read_text(encoding="utf-8").splitlines()
    assert "A magic item's description specifies whether it bears a curse." in (
        lines[246]
    )
    cursed = []
    for i, line in enumerate(lines):
        if line.startswith("_Curse._"):
            heading = next(
                lines[j] for j in range(i, -1, -1) if lines[j].startswith("#### ")
            )
            cursed.append((i + 1, heading[5:]))
    assert cursed == [
        (861, "Armor of Vulnerability"),
        (1177, "Berserker Axe"),
        (1741, "Demon Armor"),
        (4050, "Shield of Missile Attraction"),
    ], cursed
    assert [n for _, n in cursed] == [n for n, _ in CURSED]
    for _, key in CURSED:
        assert kinds[key] == "magic_item", key
    assert lines[2910].startswith("_Euryale._"), lines[2910][:40]

    # Spells: Gaining precedes Casting; Casting's members are its nine entry
    # sections (## headings after it, before Spell Descriptions).
    spells = (SRC / "spells.md").read_text(encoding="utf-8").splitlines()
    assert spells[2] == "## Gaining Spells" and spells[70] == "## Casting Spells"
    assert "The following sections explain each of those entries" in spells[72]
    entries = []
    for line in spells[71:]:
        if line == "## Spell Descriptions":
            break
        if line.startswith("## "):
            entries.append("spells." + re.sub(r"\W+", "_", line[3:].lower()))
    assert set(entries) == cat["spells.casting_spells"] and len(entries) == 9, entries
    assert "spells.gaining_spells" not in cat
    classes = (SRC / "classes.md").read_text(encoding="utf-8").splitlines()
    for _, _, n in SPELLCASTING_FEATURES:
        assert 'See "Spells" for the rules on spellcasting.' in classes[n - 1], n
    glossary = (SRC / "rules-glossary.md").read_text(encoding="utf-8").splitlines()
    assert glossary[1316] == (
        "A spell is a magical effect that has the characteristics described in "
        '"Spells."'
    ), glossary[1316]


def resolved(inputs: AcceptedInputs, which: dict = DRAFTS) -> AcceptedInputs:  # type: ignore[type-arg]
    """Resolve the accepted schema-17 artifact, as one native action."""
    return resolve_references(
        inputs,
        resolutions=drafts(inputs, which),
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _preserved(
    before: AcceptedInputs, after: AcceptedInputs, new_ids: set[str]
) -> dict[str, tuple[int, int]]:
    """Every accepted item is carried verbatim; the only additions are the new
    resolutions, their approval records and the references they resolve."""
    old, new = accepted_inputs_payload(before), accepted_inputs_payload(after)
    out: dict[str, tuple[int, int]] = {}
    for path in REPL.COLLECTIONS:
        a = Counter(REPL._key(x) for x in REPL._at(old, path))
        b = Counter(REPL._key(x) for x in REPL._at(new, path))
        lost, added = a - b, b - a
        assert not lost, (path, next(iter(lost))[:300])
        for k in added:
            assert json.loads(k).get("resolution_id") in new_ids, (path, k[:300])
        if added:
            out[".".join(path)] = (0, sum(added.values()))
    assert before.batches == after.batches
    assert before.acceptances == after.acceptances
    assert before.policy_transitions == after.policy_transitions
    o, p = before.oracle, after.oracle
    for name in ("binding", "schema_version", "schema_hash", "representation"):
        assert getattr(o, name) == getattr(p, name), name
    olds = {r.resolution_id: r for r in o.reference_resolutions}
    news = {r.resolution_id: r for r in p.reference_resolutions}
    assert all(news.get(k) == v for k, v in olds.items()), "resolution changed"
    assert set(news) - set(olds) == new_ids, set(news) - set(olds)
    old_acc = set(before.reference_resolution_acceptances)
    assert old_acc <= set(after.reference_resolution_acceptances), "approval changed"
    return out


def _report(name: str, before: list[str], after: list[str]) -> None:
    print(
        f"findings {name} (refs, leaves)", APC._split(before), "->", APC._split(after)
    )
    cleared = Counter(before) - Counter(after)
    new = Counter(after) - Counter(before)
    print("  cleared", sum(cleared.values()), "new", dict(new))
    assert not new, new
    for line in sorted(cleared.elements()):
        print("  cleared", line[:200])


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    assert (rec.oracle.schema_version, rec.oracle.schema_hash) == current, current
    assert serialize_accepted_inputs(rec) == committed, "accepted does not round-trip"
    print("schema", current[0], "accepted", ACCEPTED_SHA256)
    _sources(rec)
    print("sources: every drafted group matches the pinned markdown")

    before = APC.findings(rec)
    print("control: accepted, proposed resolutions absent", APC._split(before))
    stage = resolved(rec, EQUIPMENT_DRAFTS)
    _report("Equipment and cursed items alone", before, APC.findings(stage))
    final = resolved(rec)
    after = APC.findings(final)
    _report("all thirteen", before, after)
    for line in sorted(after):
        print("  remains", line[:200])

    final_bytes = serialize_accepted_inputs(final)
    print("candidate (simulated)", _sha(final_bytes))
    reloaded = FRR.load_accepted_inputs_bytes(final_bytes)
    assert serialize_accepted_inputs(reloaded) == final_bytes, "reload"
    print("  reloads to the same bytes True")
    new_ids = {r.resolution_id for r in drafts(rec)}
    assert len(new_ids) == 13
    changes = _preserved(rec, reloaded, new_ids)
    print(
        "preserved: every accepted item verbatim, including",
        len(rec.oracle.reference_resolutions),
        "resolutions with",
        len(rec.reference_resolution_acceptances),
        "approvals; added:",
    )
    for collection, n in changes.items():
        print("  ", collection, n)
    print("counts", REPL._counts(rec), "->", REPL._counts(reloaded))

    resolutions = tuple(
        r for r in final.oracle.reference_resolutions if r.resolution_id in new_ids
    )
    print(
        "resolutions",
        len(resolutions),
        "destinations",
        sum(len(r.destinations) for r in resolutions),
    )
    for r in resolutions:
        row = DRAFTS[
            (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        ][0]
        labels = list(dict.fromkeys(d.alternative_label for d in r.destinations))
        print(f"  {row} {r.resolution_id} routes {len(labels)}", end="")
        print(f" destinations {len(r.destinations)}")
    print("persisted round trip", FRR._persisted_round_trip(final))

    proposal = (
        json.dumps(
            {
                "accepted_sha256": ACCEPTED_SHA256,
                "representation_schema": list(current),
                "reference_resolutions": reference_resolution_payload(resolutions),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    delta = (
        "# Full-text delta from the accepted artifact (evidence blanked)\n"
        + "".join(f"{x}\n" for x in REPL.Delta(rec, reloaded).report())
        + "# Effective reference lines\n"
        + FRR._delta(rec, final)
    ).encode("utf-8")
    for path, data in ((PROPOSAL_FILE, proposal), (DELTA_FILE, delta)):
        if write:
            path.write_bytes(data)
        assert path.read_bytes() == data, f"{path.name} is stale; run --write"
        print(path.name, _sha(data), f"{data.count(b'\n')} lines")
    print("OK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
