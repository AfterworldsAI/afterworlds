# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **Gameplay Toolbox** proposal: the whole part the SRD prints.

REVIEW MATERIAL for CRD Issue 5d (#137) over the corrected 5c release
``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``. It
emits one *unaccepted* ``5d-proposal-2`` artifact and one file of unrecorded
resolution drafts. It accepts nothing, publishes nothing, writes nothing under
``oracles/`` and records no resolution.

Scope, 285 leaves (pp192-203 of the official PDF): every leaf of the
*Gameplay Toolbox* part below its ``# Gameplay Toolbox`` heading, which stays
with the other part headings. None was accepted before. The qualified leaf
texts are ``issue-5d-gameplay-toolbox-source.py``; this file reads them from
there.

Record grain (every record ``gameplay_tool``; no consumer reads the kind):

* each of the nine top-level sections the release prints is one record,
  ``gameplay_toolbox.<section>``, its first component its heading and the
  prose before its first subheading, then one component per printed
  subheading in printed order. The *Travel Terrain* table the release prints
  inside *Vehicles* is its own ``travel_terrain`` component there: the part's
  opening cites "the Maximum Pace column of the Travel Terrain table";
* a printed catalogue entry -- a heading whose next line is its italic type
  (``_Ingested Poison_``, ``_Deadly Trap (Levels 1-4)_``, ``_Magical
  Contagion_``) -- is its own record and a ``CATALOGUE_MEMBER`` of its section,
  in printed order: 14 sample poisons, 8 example traps, 3 example contagions.
  Each is one prose-bound component, as the accepted
  ``equipment.adventuring_gear.poison_basic`` is; a trap's scaling table stays
  in it. Its section's components never bind a member's leaves;
* *Troubleshooting* is part of *Combat Encounters*: the PDF (pp202-203) sets
  it there, level with *Combat Encounter Difficulty*, though the release
  prints it at ``##``. It stays its own review unit over its own container and
  is read into ``gameplay_toolbox.combat_encounters``, its components after
  *Step 3*, in printed order. No record, edge or membership is added for it,
  and the release is read as it is.

Every component is prose-bound: no code-owned use is identified for travel
pace, poison, trap, contagion, fear or encounter-budget values, so none is
typed (ADR-005d Decision 4). A component whose text explicitly leaves a ruling
to whoever runs the game is ``gamemaster_latitude`` (``LATITUDE``, by the
delegating words); every other one states reducible meaning and is
``no_identified_structured_use``.

References, once per component: each accepted Rules Glossary term the prose
depends on; every spell named in italics, to its accepted record; the items the
accepted *Equipment* holds a record for, by the printed name (Herbalism Kit,
Thieves' Tools); the Net, Iron Spike and Poisoner's Kit, which hold no record
of their own, unresolved, and so the "Adventuring Gear" citation of the Net's
statistics, as printed; each creature named in bold, the *Carpet of Flying*
and the "Equipment", "Playing the Game", "Magic Items" and "Origin Feats"
pointers, unresolved; "Travel Pace" to its record here. A pointer inside its
own record ("Vehicles", "Frigid Water") names no other record and is not a
reference.

Run: ``python issue-5d-gameplay-toolbox-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Iterable
from functools import cache
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    Target,
    build_entry_batch,
    emit,
    scoped,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReleaseBinding,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import RecordKind

ORIGIN = "issue-5d-gameplay-toolbox-generator.py"
PROPOSAL_FILE = "issue-5d-gameplay-toolbox-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-gameplay-toolbox-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
PART = "Gameplay Toolbox"
TOOLBOX = "srd-5.2.1/gameplay-toolbox"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
MONSTERS = "srd-5.2.1/monsters"
MAGIC_ITEMS = "srd-5.2.1/magic-items"
FEATS = "srd-5.2.1/feats"
PLAYING = "srd-5.2.1/playing-the-game"
#: The target of a printed pointer whose destination has no record yet.
UNRESOLVED_TARGET = ""
#: The accepted authority this packet composes over, as the task pins it.
ORACLE_FILE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-574662e9-0ef.json"
ORACLE_SHA256 = "b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f"

GM = "gamemaster_latitude"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND
KIND = RecordKind.GAMEPLAY_TOOL
#: (entry, component key) -> the printed words by which the source explicitly
#: leaves the ruling to whoever runs the game (policy: "The source explicitly
#: delegates the decision to the GM"). Read by meaning, not by "you": the
#: background steps, a trap's "_At Higher Levels._" table, "You can make the
#: pit easier to escape" and the encounter-budget procedure state what to do
#: or offer a tabled option, and are reducible.
LATITUDE: dict[tuple[str, str], str] = {
    (
        "curses_and_magical_contagions",
        "cursed_creatures",
    ): "You decide how a spell like _Remove Curse_ affects a creature with accursed origins.",
    (
        "curses_and_magical_contagions",
        "narrative_curses",
    ): "How a spell like _Remove Curse_ affects a curse that's part of your adventure is up to you",
    # Whether the section's rules apply at all is the runner's choice.
    (
        "fear_and_mental_stress",
        "fear_and_mental_stress",
    ): "If you plan to use any of these rules",
    (
        "fear_and_mental_stress",
        "fear_effects",
    ): "At your discretion, a Frightened creature might be subject to other effects",
    (
        "fear_and_mental_stress",
        "mental_stress_effects",
    ): "a character might take half as much damage instead of no damage, at your discretion.",
    ("poison", "poison"): "You may decide that a partial dose has a reduced effect",
    ("troubleshooting", "adjustments"): "You can adjust an encounter on the fly",
}
#: A section the release prints apart from the one the source sets it in,
#: read into that section's record.
READ_INTO = {"Troubleshooting": "Combat Encounters"}


def _load(name: str) -> object:
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(f"{name}.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


def _source() -> tuple[tuple[tuple[str, ...], str], ...]:
    module = _load("issue-5d-gameplay-toolbox-source")
    return tuple(((PART, *p), t) for p, t in module.LEAVES)  # type: ignore[attr-defined]


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES = _source()
#: The accepted spell descriptions: their names, keys and glossary terms.
SD = _load("issue-5d-spell-descriptions-generator")
slug = SD.slug  # type: ignore[attr-defined]
spell_key = SD.spell_key  # type: ignore[attr-defined]


def texts_at(path: tuple[str, ...]) -> list[str]:
    """The leaves printed directly in *path*, not in a container below it."""
    return [t for p, t in LEAVES if p == path]


def containers(path: tuple[str, ...]) -> list[tuple[str, ...]]:
    """*path* and every container below it, in printed order."""
    return list(dict.fromkeys(p for p, _ in LEAVES if p[: len(path)] == path))


def children(path: tuple[str, ...]) -> list[str]:
    """The labels of *path*'s sub-containers, in printed order."""
    return list(
        dict.fromkeys(
            p[len(path)]
            for p, _ in LEAVES
            if p[: len(path)] == path and len(p) > len(path)
        )
    )


def key_of(label: str) -> str:
    """A component or member key: the label's slug, less a printed price."""
    k = slug(re.sub(r" \([\d,]+ GP\)$", "", label))
    return f"step_{k}" if k[0].isdigit() else k


SECTIONS = tuple(children((PART,)))
assert SECTIONS == (
    "Travel Pace",
    "Creating a Background",
    "Curses and Magical Contagions",
    "Environmental Effects",
    "Fear and Mental Stress",
    "Poison",
    "Traps",
    "Combat Encounters",
    "Troubleshooting",
), SECTIONS


def section_key(section: str) -> str:
    return f"gameplay_toolbox.{slug(section)}"


def section_record(section: str) -> str:
    """The record a printed section is read into."""
    return section_key(READ_INTO.get(section, section))


#: A printed catalogue entry's second line: its italic type.
TYPE_LINE = re.compile(r"_[^_\n]+_")


def is_member(path: tuple[str, ...]) -> bool:
    texts = texts_at(path)
    return (
        len(path) > 2
        and len(texts) > 1
        and texts[0] == f"#### {path[-1]}"
        and TYPE_LINE.fullmatch(texts[1]) is not None
    )


#: section -> its member containers, in printed order.
MEMBERS = {s: [c for c in containers((PART, s)) if is_member(c)] for s in SECTIONS}
assert {s: len(m) for s, m in MEMBERS.items() if m} == {
    "Curses and Magical Contagions": 3,
    "Poison": 14,
    "Traps": 8,
}, MEMBERS
assert all(children(m) == [] for ms in MEMBERS.values() for m in ms)


def member_key(path: tuple[str, ...]) -> str:
    return f"{section_key(path[1])}.{key_of(path[-1])}"


#: The table the release prints in *Vehicles*, read as its own component.
TRAVEL_TERRAIN = "**Travel Terrain**\n\n<table>"


#: Every LATITUDE row a component consumed, for the completeness check.
DELEGATED: set[tuple[str, str]] = set()


def reason(entry: str, key: str, texts: tuple[str, ...]) -> str:
    if (words := LATITUDE.get((entry, key))) is None:
        return NO_USE
    assert any(words in t for t in texts), (entry, key)
    DELEGATED.add((entry, key))
    return GM


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
#: The accepted spell generator's Rules Glossary alternation, with the one
#: accepted entry the toolbox prints that spells do not.
GLOSSARY_TERMS: tuple[tuple[str, str | None], ...] = (
    ("Damage Threshold", "damage_threshold"),
    *SD.GLOSSARY_TERMS,  # type: ignore[attr-defined]
)
_TERMS = re.compile("|".join(rf"(?<![_\w*])(?:{p})\b" for p, _ in GLOSSARY_TERMS))


def _term_slug(printed: str) -> str | None:
    return next(s for p, s in GLOSSARY_TERMS if re.fullmatch(p, printed))


def eq(key: str) -> Target:
    return (EQUIPMENT, f"equipment.{key}")


#: Items by the exact printed name. The Net and Iron Spike are priced inside
#: the accepted *Adventuring Gear* and the Poisoner's Kit is not a record: none
#: holds a record of its own, so each stays unresolved rather than widened.
ITEMS: tuple[tuple[str, Target], ...] = (
    ("Herbalism Kit", eq("tools.herbalism_kit")),
    ("Thieves' Tools", eq("tools.thieves_tools")),
    ("Poisoner's Kit", (EQUIPMENT, UNRESOLVED_TARGET)),
    ("Iron Spike", (EQUIPMENT, UNRESOLVED_TARGET)),
    ("Net", (EQUIPMENT, UNRESOLVED_TARGET)),
)
_ITEMS = re.compile(
    "|".join(rf"\b(?P<i{i}>{re.escape(n)})\b" for i, (n, _) in enumerate(ITEMS))
)
#: Every quoted pointer the part prints, by its printed name.
POINTERS: dict[str, Target] = {
    "Playing the Game": (PLAYING, UNRESOLVED_TARGET),
    "Equipment": (EQUIPMENT, UNRESOLVED_TARGET),
    # Cited for the Net's statistics, which hold no record of their own.
    "Adventuring Gear": (EQUIPMENT, UNRESOLVED_TARGET),
    "Magic Items": (MAGIC_ITEMS, UNRESOLVED_TARGET),
    # The Origin Feats the Feats part prints hold no record of their own.
    "Origin Feats": (FEATS, UNRESOLVED_TARGET),
    "Travel Pace": (TOOLBOX, section_key("Travel Pace")),
    # Both print inside the record they point into.
    "Vehicles": (TOOLBOX, section_key("Travel Pace")),
    "Frigid Water": (TOOLBOX, section_key("Environmental Effects")),
}
#: Quoted words that point nowhere.
NOT_POINTERS = frozenset({"fire"})
_QUOTED = re.compile(r'"(?P<n>[^"\n]+?)\.?"')
#: The creatures prose names in bold, with any printed count, as qualified
#: against the PDF; every other bold run is a label.
CREATURE_NAMES = frozenset(
    {
        "Adult Red Dragons",
        "Bugbear Warrior",
        "Druids",
        "Fire Giants",
        "Giant Rats",
        "Giant Wasps",
        "Ogre",
        "Skeletons",
        "Stirges",
        "Warhorse Skeleton",
        "Wight",
    }
)
#: Bold runs inside a line that are a formula's or a pace's label.
BOLD_LABELS = frozenset({"Miles per day", "Fast pace", "Slow pace"})
#: The one magic item prose names, in italics.
MAGIC_ITEM_NAMES = frozenset({"Carpet of Flying"})
#: Italic type lines: a poison's, a trap's or a contagion's.
_TYPE = re.compile(
    r"(?:Contact|Ingested|Inhaled|Injury) Poison|Magical Contagion|(?:Deadly|Nuisance) Trap \(.*\)"
)
_ITALIC = re.compile(r"(?<![\w*])_(?P<n>[A-Z][^_\n]*?)_(?!\w)")
_BOLD = re.compile(r"\*\*(?P<n>[^*]+?)\*\*")

#: Every name read, for the qualification check.
SEEN: set[str] = set()


def refs_of(own: str, texts: tuple[str, ...]) -> tuple[tuple[str, Target], ...]:
    """The references of one component of record *own*."""
    out: dict[tuple[str, Target], None] = {}
    terms: dict[str, str] = {}

    def add(text: str, target: Target) -> None:
        SEEN.add(text)
        if scoped(target)[1] != own:
            out.setdefault((text, target))

    for t in texts:
        if t.startswith("#"):
            continue
        for m in _ITALIC.finditer(t):
            name = m["n"]
            if name.endswith(".") or _TYPE.fullmatch(name):
                continue
            if name in MAGIC_ITEM_NAMES:
                add(name, (MAGIC_ITEMS, UNRESOLVED_TARGET))
                continue
            assert name in SD.SPELL_NAMES, name  # type: ignore[attr-defined]
            add(name, (SPELLS, spell_key(name)))
        for m in _BOLD.finditer(t):
            name = re.sub(r"^\d+ ", "", m["n"])
            if m.start() == 0 or name.endswith((".", ":")) or name in BOLD_LABELS:
                continue
            assert name in CREATURE_NAMES, name
            add(name, (MONSTERS, UNRESOLVED_TARGET))
        for m in _QUOTED.finditer(t):
            if m["n"] in NOT_POINTERS:
                continue
            add(m["n"], POINTERS[m["n"]])
        for m in _ITEMS.finditer(t):
            assert m.lastgroup is not None
            add(m.group(), ITEMS[int(m.lastgroup[1:])][1])
        for m in _TERMS.finditer(t):
            if (s := _term_slug(m.group())) is not None:
                terms.setdefault(s, m.group())
    for s, printed in terms.items():
        add(printed, s)
    return tuple(out)


# ---------------------------------------------------------------------------
# The chunk
# ---------------------------------------------------------------------------
class Chunk:
    """The literal review data of the packet, gathered in printed order."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str, RecordKind]] = []
        self.placements: dict[str, Placement] = {}
        self.clauses: list[tuple[str, str, tuple[str | None, ...], tuple[str, ...]]] = (
            []
        )
        self.components: list[EntryComponent] = []
        self.members: list[tuple[str, str]] = []
        self.leaves = 0

    def entry(
        self,
        slug_: str,
        key: str,
        container: tuple[str, ...],
        heading: str,
        *,
        unit: ReviewUnitKind = ReviewUnitKind.SECTION,
        omit: tuple[tuple[str, ...], ...] = (),
    ) -> None:
        self.entries.append((slug_, container[-1], KIND))
        self.placements[slug_] = Placement(key, container, heading, unit, omit)
        self.leaves += sum(
            1
            for p, _ in LEAVES
            if p[: len(container)] == container
            and not any(p[: len(o)] == o for o in omit)
        )

    def section(self, entry: str, key: str, texts: Iterable[str]) -> None:
        """A prose-bound component of the entry's own record."""
        ts = tuple(texts)
        assert ts, (entry, key)
        self.clauses.append((entry, key, (None,), ts))
        own = self.placements[entry].record_key
        self.components.append(
            EntryComponent(entry, key, P, reason(entry, key, ts), refs=refs_of(own, ts))
        )

    def batch(self) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d gameplay toolbox; unaccepted)",
            unit_prefix="gameplay-toolbox",
            parent=PARENT,
            entries=tuple(self.entries),
            expected_leaves=self.leaves,
            clauses=tuple(self.clauses),
            framing=(),
            components=tuple(self.components),
            supporting=(),
            record_references=(),
            placements=self.placements,
            members=tuple(self.members),
            records=(),
            record_containers={},
            scoped_records=(),
            edges=(),
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()}


def section_components(section: str) -> list[tuple[str, tuple[str, ...]]]:
    """(key, texts) of a section record: its own prose, then each printed
    subheading below it that is not a member, in printed order."""
    members = MEMBERS[section]
    out: list[tuple[str, tuple[str, ...]]] = []
    for path in containers((PART, section)):
        if any(path[: len(m)] == m for m in members):
            continue
        texts = texts_at(path)
        if path == (PART, "Travel Pace", "Vehicles"):
            (at,) = [i for i, t in enumerate(texts) if t.startswith(TRAVEL_TERRAIN)]
            assert at == len(texts) - 1
            out += [("vehicles", tuple(texts[:at])), ("travel_terrain", (texts[at],))]
            continue
        out.append((key_of(path[-1]), tuple(texts)))
    keys = [k for k, _ in out]
    assert len(keys) == len(set(keys)), (section, keys)
    return out


def toolbox_chunk() -> Chunk:
    chunk = Chunk()
    for section in SECTIONS:
        path = (PART, section)
        e = slug(section)
        members = MEMBERS[section]
        chunk.entry(
            e, section_record(section), path, f"## {section}", omit=tuple(members)
        )
        for key, texts in section_components(section):
            chunk.section(e, key, texts)
        for m in members:
            me = f"{e}.{key_of(m[-1])}"
            chunk.entry(
                me, member_key(m), m, f"#### {m[-1]}", unit=ReviewUnitKind.ENTRY
            )
            chunk.members.append((me, e))
            chunk.section(me, key_of(m[-1]), texts_at(m))
    return chunk


TOOLBOX_CHUNK = toolbox_chunk()
assert TOOLBOX_CHUNK.leaves == len(LEAVES) == 285
assert CREATURE_NAMES <= SEEN and MAGIC_ITEM_NAMES <= SEEN
assert set(POINTERS) <= SEEN and {n for n, _ in ITEMS} <= SEEN
assert set(LATITUDE) == DELEGATED, set(LATITUDE) - DELEGATED


def batch() -> EntryBatch:
    return TOOLBOX_CHUNK.batch()


def build(session: Session) -> Built:
    """Derive the gameplay toolbox proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def unresolved(chunk: Chunk) -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text)."""
    return sorted(
        (scoped(t)[0], text)
        for c in chunk.components
        for text, t in c.refs
        if scoped(t)[1] == UNRESOLVED_TARGET
    )


def outside(chunk: Chunk) -> set[Target]:
    """Every resolved target this chunk names and does not itself hold."""
    return {
        t
        for c in chunk.components
        for _, t in c.refs
        if scoped(t)[1] not in chunk.record_keys() and scoped(t)[1] != UNRESOLVED_TARGET
    }


def expected_representation_findings(chunk: Chunk) -> list[str]:
    """What the packet alone cannot see: accepted targets and open pointers.

    One finding per component reference to an accepted record and one per
    unresolved pointer -- each accepted target is valid once the packet is
    read over the accepted oracle, which the composition check shows.
    """
    targets = outside(chunk)
    return sorted(
        [
            *(
                f"reference {scoped(t)[0]}:{text!r}: unknown target record {scoped(t)[1]}"
                for c in chunk.components
                for text, t in c.refs
                if t in targets
            ),
            *(
                f"reference {s}:{t!r}: unresolved reference"
                for s, t in unresolved(chunk)
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
@cache
def current() -> AcceptedInputs:
    """The eighteen-batch chain this packet is composed over on the
    Monsters-corrected release, as the Owner's acceptance recorded it.

    Over the superseded release it was ``ORACLE_FILE`` at ``ORACLE_SHA256``,
    which ``issue-5d-gameplay-toolbox-ACCEPT.py`` recorded (historical).
    """
    recording = _load("issue-5d-monsters-corrections-ACCEPT")
    inputs: AcceptedInputs = recording.owner_chain(  # type: ignore[attr-defined]
        recording.ACCEPTED_AT,  # type: ignore[attr-defined]
        through="spell-descriptions",
    )
    return inputs


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_targets(
    prior: AcceptedInputs,
) -> tuple[
    list[tuple[str, str, str, str, tuple[str, ...]]], list[tuple[str, str, str]]
]:
    """(drafts, left): each accepted unresolved *Gameplay Toolbox* pointer whose
    printed text is exactly one section's name, to that section, with the spans
    the oracle cites it from; and every other one, left unresolved as printed.
    """
    from afterworlds.ingestion.mechanical.representation import (
        ProvenanceTargetKind,
        reference_target_key,
    )

    rep = prior.oracle.representation
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in rep.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    names = {s: section_record(s) for s in SECTIONS}
    resolved = {
        (r.from_record_key, r.from_component_key, r.source_text)
        for r in prior.oracle.reference_resolutions
    }
    drafts, left = [], []
    for ref in rep.references:
        if ref.scope_key != TOOLBOX or ref.target_record_key:
            continue
        where = (ref.from_record_key, ref.from_component_key, ref.source_text)
        assert where not in resolved, where
        if ref.source_text in names:
            spans = tuple(cited[reference_target_key(ref)])
            assert spans, where
            drafts.append((*where, names[ref.source_text], spans))
        else:
            left.append(where)
    return drafts, left


def draft_resolutions(
    binding: ReleaseBinding, prior: AcceptedInputs
) -> tuple[ReferenceResolution, ...]:
    drafts, _ = draft_targets(prior)
    out = tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{_slug(record)}-{_slug(component) or 'record'}-{_slug(text)}-gameplay-toolbox-1",
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=TOOLBOX,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, target, spans in drafts
    )
    assert len({r.resolution_id for r in out}) == len(out)
    return out


def main(db: str) -> int:
    here = Path(__file__).resolve().parent
    from afterworlds.persistence.database import create_engine, create_session_factory

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        binding = published_release_binding(session)
    engine.dispose()
    prior = current()
    # Only the release the accepted authority is bound to.
    assert binding == prior.oracle.binding, binding
    emit(
        db, build, here / PROPOSAL_FILE, expected_representation_findings(TOOLBOX_CHUNK)
    )
    drafts = draft_resolutions(binding, prior=prior)
    payload = reference_resolution_payload(drafts)
    (here / DRAFTS_FILE).write_bytes(
        (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    )
    print(f"drafts            {DRAFTS_FILE} ({len(drafts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
