"""CRD Issue 5d — batch `speed-1`, **source-discovery run only**.

Reads the committed SRD through the 5c pipeline, re-derives the ``Speed`` source
population from the source's own containers and its own printed cross-citations,
cuts every represented leaf into an exact clause partition, enumerates the
boundary the population excludes, and writes one deterministic LF manifest. It
builds no draft, proposes nothing, accepts nothing, publishes nothing, lifts
nothing, executes no schema change and touches no database.

Why a label query is not the membership rule here
-------------------------------------------------
``cover-1`` could read membership off labels: exactly two ``entry`` containers in
the bound release are labeled ``Cover``, and both state the rule. ``Speed`` has
**four** containers labeled ``Speed``, and three of them are not this rule:

* ``Character Origins > Character Species > Speed`` — a pointer saying a
  character's species determines the value;
* ``Equipment > Mounts and Vehicles > Speed`` — a homonym, vehicle speed in
  miles per hour;
* ``Monsters > Parts of a Stat Block > Speed`` — a pointer that explicitly
  defers, *"Rules for Speed and these specials speeds appear in 'Rules
  Glossary'"*.

So the label is not the query, and this run does not pretend it is. What the
source does print is a **reciprocal citation**: the Rules Glossary's ``Speed``
entry ends ``See also`` / a citation naming ``"Playing the Game" ("Combat")``,
and exactly one leaf in the entire bound release prints the sentence *See "Rules
Glossary" for more about Speed*. That leaf belongs to ``Playing the Game >
Combat > Movement and Position``, which is the section the glossary entry points
at and the only entry in it that points back.

**The reciprocal query is narrower than a co-occurrence query, deliberately.**
Three ``Combat`` entries mention both ``Rules Glossary`` and ``Speed`` —
``Movement and Position``, ``Dropping Prone`` and ``Mounting and Dismounting`` —
because the other two cite the glossary for *something else*. A naive
co-occurrence test would pull in two entries that never state a Speed rule. The
run locates the exact citation sentence, asserts it occurs in exactly one leaf,
and records the wider co-occurrence figure so the narrowing is checkable rather
than asserted.

**The source owns the boundary.** A leaf is in this population because the
source attaches it to one of those two entries, not because it prints the word.
557 leaves outside the population print ``speed`` in some case — every one of
them represented by 5c — across monster stat blocks, animals, spells, magic items,
class features, species traits and travel rules. Every one of them *uses* the
quantity; none of them *states* what it is. They are enumerated in the manifest
with their containers so the exclusion is checkable, and pulling any of them in
would be the batch expansion the governing issue forbids.

Adjudicated boundary
--------------------
Enumeration alone does not settle the hard cases, so the manifest carries a
second, named table of the containers whose exclusion a reader would actually
question — the three other ``Speed`` labels, the four special-speed glossary
entries the population's own prose names, the five glossary entries its
``See also`` citation names, the ``Combat`` siblings that spend Speed, and the
two travel-pace sites that convert it. Each row carries facts only: its path,
its leaf count, whether it prints the reciprocal citation sentence, whether the
population's citation leaf names it, and whether it names ``Speed`` back. What
each one *is* — an outbound reference, an incidental use, or a sibling record for
a later batch — is a judgment, and it lives in the checkpoint.

What this run establishes, and what it does not
-----------------------------------------------
1. **Membership**, from the source's containers and its own printed
   cross-citation rather than from a remembered count, with the boundary
   enumerated rather than waved at.
2. **Exact coverage**, as ``leaf_id`` plus leaf-local half-open character
   ranges, with the partition asserted to reconstruct each leaf byte for byte.
   Every clause the checkpoint judges is addressable here.
3. **The unchanged accepted prior**, by two independent identities before and
   after the run, and the live accepted artifact as a mutation sentinel that is
   never an input.

It establishes nothing about representation. Whether ``Speed`` is one record or
an umbrella, which clauses are typeable under schema 10 and which are irreducible
prose, whether the citation leaf emits references, and whether a schema 11 is
needed are judgments; they live in
``issue-5d-speed-1-DISCOVERY-CHECKPOINT.md`` and cite the clause ids this run
emits. No disposition and no candidate record key is encoded here, because a
discovery run that shipped its own conclusions would be proposing.

Clause cuts
-----------
A cut names the text a segment **ends with**; ``None`` means "to the end of the
leaf". Cuts are located in the bound leaf content at run time and fail loudly if
the source moved, so a re-extraction cannot silently re-cut a clause under a
judgment that was written about the old one. Separator runs are absorbed as the
*leading* text of the next segment, exactly as the accepted batch generators do,
so the partition reconstructs each leaf byte for byte.

The cuts are sentence-level except in three places, each for a stated reason.
The definition sentence is cut after ``A creature has a Speed,`` because the
possession claim and the measure that follows it are separately representable and
a judgment about one should not silently cover the other. The ``See also``
citation leaf is cut per cited term, which is the shape ``actions-1`` used for
its own multi-term citation leaf, so each cited term is separately addressable
without deciding here what it resolves to. And the speed-switching sentence is
cut at its semicolon, because selecting a speed and switching between speeds
mid-move are two claims.

Sentences that cross leaves
---------------------------
Three printed sentences arrive split across leaves — a property of the frozen 5c
extraction at column and page boundaries, carried verbatim rather than smoothed.
The manifest names each group of clause ids that reconstructs one sentence and
the run asserts the reconstruction, so a judgment written about a whole sentence
can cite the exact subspans it rests on instead of implying a leaf boundary that
the source does not print.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

#: The repository this run reads everything from, derived from where this file
#: actually lives: `<repo>/.claude/review-notes/<this file>`.
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
assert OUT.name == "review-notes" and OUT.parent.name == ".claude", OUT
sys.path.insert(0, str(REPO / "src"))

SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"

#: **The frozen review prior.** Accepted authority as it stands for this batch's
#: review: conditions-1, hazards-1, actions-1, attitudes-1, areas-of-effect-1
#: and cover-1, representation schema 10. Read only, by content identity, and
#: asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1_cover_1.json"
    )
)

#: **A mutation sentinel, never an input.** Bytes captured before the run and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: The frozen 5c expected-table oracle, read only, as an independent witness for
#: the claim that this population owns no printed table.
TABLE_INVENTORY_PATH = (
    REPO / "src/afterworlds/ingestion/corpus/srd_table_inventory.json"
)

MANIFEST_PATH = OUT / "issue-5d-speed-1-source-manifest.json"

PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (
    SOURCE_PDF,
    REVIEW_PRIOR_PATH,
    LIVE_ORACLE_PATH,
    TABLE_INVENTORY_PATH,
    PACKAGE_ROOT,
):
    assert _required.exists(), f"missing beneath the derived root: {_required}"


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _blob_id(path: Path) -> str:
    body = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()  # noqa: S324


#: The frozen review prior, identified by **content** rather than by whatever
#: bytes a working copy holds. `.gitattributes` declares `* text=auto eol=lf`,
#: so a raw digest is a property of a checkout; the canonical (CRLF -> LF)
#: SHA-256 and the Git blob id are properties of the authority.
REVIEW_PRIOR_CONTENT_SHA256 = "391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "b7c0149432072d4a3b151d0f9b2c458252e584da"  # pragma: allowlist secret
)
REVIEW_PRIOR_IDENTITY = "86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "cover-1",
    "hazards-1",
]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-10"

assert _lf_sha256(REVIEW_PRIOR_PATH) == REVIEW_PRIOR_CONTENT_SHA256
assert _blob_id(REVIEW_PRIOR_PATH) == REVIEW_PRIOR_BLOB
_PRIOR_BEFORE = _lf_sha256(REVIEW_PRIOR_PATH)
_LIVE_BEFORE = _lf_sha256(LIVE_ORACLE_PATH)

# --- Retained-evidence guard ------------------------------------------------
# Every other file beside this one records authority or prior discovery. This
# run writes exactly one path and asserts afterwards that nothing else moved.
RETAINED = tuple(
    sorted(
        p.name
        for p in OUT.iterdir()
        if p.is_file() and p.name not in {Path(__file__).name, MANIFEST_PATH.name}
    )
)
_RETAINED_BEFORE = {
    n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in RETAINED
}

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import lift_path  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

import afterworlds  # noqa: E402  # isort: skip

IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)

# ---------------------------------------------------------------------------
# Bound release — derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # noqa: E501  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # noqa: E501  # pragma: allowlist secret

#: The one binding value this run does not re-derive. Recomputing it needs a
#: session over the persisted ``rp_sources`` rows plus read-back vector state
#: (``persistence.recompute_persisted_digest``); verifying a published release
#: against declared values is ``operational.load_verified_operational_corpus``,
#: the narrower downstream trust seam. Neither requires a publish — this run
#: simply performs neither, and does no operational database work at all. The
#: value is carried from the published CRD Issue 5c release record and disclosed
#: as carried rather than derived.
PERSISTED_CORPUS_DIGEST = "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"  # noqa: E501  # pragma: allowlist secret

CAND = build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())
assert CAND.package_uuid == PACKAGE_UUID, CAND.package_uuid
assert CAND.release_version == RELEASE_VERSION, CAND.release_version
assert CAND.authoritative_source_hash == SOURCE_SHA256, CAND.authoritative_source_hash
assert CAND.transform_config_hash == TRANSFORM_CONFIG_HASH, CAND.transform_config_hash
assert CAND.bundle.bundle_root_hash == BUNDLE_ROOT_HASH, CAND.bundle.bundle_root_hash

LEDGER_OBJ = CAND.ledger
LABELS = {c.container_id: c.label for c in LEDGER_OBJ.containers}
CONTAINERS = {c.container_id: c for c in LEDGER_OBJ.containers}
REPRESENTED = {
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if exclusion_reason_for(leaf, LABELS) is None
}


def _ancestry(cid: str) -> list[str]:
    out, cur = [], CONTAINERS.get(cid)
    while cur:
        out.append(cur.container_id)
        cur = CONTAINERS.get(cur.parent_id) if cur.parent_id else None
    return out


def _path_of(cid: str) -> str:
    return " > ".join(LABELS[c] for c in reversed(_ancestry(cid)))


by_container: dict[str, list[Any]] = defaultdict(list)
for _leaf in LEDGER_OBJ.leaves:
    for _cid in _leaf.container_path:
        by_container[_cid].append(_leaf)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))


def _one_container(path: str) -> Any:
    """The single container at *path*, or a loud failure."""
    found = [c for c in LEDGER_OBJ.containers if _path_of(c.container_id) == path]
    assert len(found) == 1, (path, len(found))
    return found[0]


# ---------------------------------------------------------------------------
# Membership — the label is not the query; the printed reciprocal citation is
# ---------------------------------------------------------------------------

RSQ = "’"  # right single quotation mark
LDQ, RDQ = "“", "”"  # double quotation marks

#: Every container the bound release labels exactly ``Speed``. Asserted as a set
#: of paths rather than a count, because the interesting failure is a release
#: that renamed one of these or grew a fifth, not one that changed the total.
SPEED_LABELLED_PATHS = sorted(
    _path_of(c.container_id) for c in LEDGER_OBJ.containers if c.label == "Speed"
)
assert SPEED_LABELLED_PATHS == [
    "Character Origins > Character Species > Speed",
    "Equipment > Mounts and Vehicles > Speed",
    "Monsters > Parts of a Stat Block > Speed",
    "Rules Glossary > Rules Definitions > Speed",
], SPEED_LABELLED_PATHS

GLOSSARY_ENTRY = _one_container("Rules Glossary > Rules Definitions > Speed")
assert GLOSSARY_ENTRY.container_type == "entry", GLOSSARY_ENTRY.container_type

#: The sentence the governing section prints to point back at the glossary. The
#: query is this exact sentence, asserted unique across the whole release, so a
#: release in which the reciprocity disappeared fails here rather than being
#: silently carried under a wider test.
RECIPROCAL_CITATION = f"See {LDQ}Rules Glossary{RDQ} for more about Speed"
_reciprocal = [lf for lf in LEDGER_OBJ.leaves if RECIPROCAL_CITATION in lf.content]
assert len(_reciprocal) == 1, [lf.leaf_id for lf in _reciprocal]
RECIPROCAL_LEAF = _reciprocal[0]
COMBAT_ENTRY = CONTAINERS[RECIPROCAL_LEAF.container_path[-1]]
assert COMBAT_ENTRY.container_type == "entry", COMBAT_ENTRY.container_type
assert (
    _path_of(COMBAT_ENTRY.container_id)
    == "Playing the Game > Combat > Movement and Position"
), _path_of(COMBAT_ENTRY.container_id)

#: Third-party corroboration, printed by neither member. ``Your Turn`` restates
#: the per-turn allowance in almost the population's words and then hands the
#: movement rules to the governing section by name. Asserted unique release-wide
#: and asserted to name the ``combat`` site, so it is a derived witness rather
#: than a remembered one, and it is boundary rather than membership: it owns its
#: own entry, and what it states is the turn's action economy.
DEFERRAL = (
    f"{LDQ}Movement and Position{RDQ} later in {LDQ}Playing the Game{RDQ} "
    f"gives the rules for movement."
)
_deferring = [lf for lf in LEDGER_OBJ.leaves if DEFERRAL in lf.content]
assert len(_deferring) == 1, [lf.leaf_id for lf in _deferring]
DEFERRAL_LEAF = _deferring[0]
assert LABELS[DEFERRAL_LEAF.container_path[-1]] == "Your Turn", _path_of(
    DEFERRAL_LEAF.container_path[-1]
)
assert DEFERRAL_LEAF.container_path[-1] != COMBAT_ENTRY.container_id

#: How much wider a co-occurrence test would have been. Every ``entry`` beneath
#: ``Playing the Game > Combat`` whose text mentions both the glossary and
#: ``Speed`` — three, not one. Recorded because the narrowing is the whole
#: derivation and an unstated narrowing is indistinguishable from luck.
COMBAT_ENTRIES = [
    c
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry"
    and _path_of(c.container_id).startswith("Playing the Game > Combat > ")
]
NAIVE_COOCCURRENCE = sorted(
    LABELS[c.container_id]
    for c in COMBAT_ENTRIES
    if all(
        term in " ".join(lf.content for lf in by_container[c.container_id])
        for term in ("Rules Glossary", "Speed")
    )
)
assert NAIVE_COOCCURRENCE == [
    "Dropping Prone",
    "Mounting and Dismounting",
    "Movement and Position",
], NAIVE_COOCCURRENCE

#: The two source sites, in the order a reader reaches them from the glossary:
#: the defining entry, and the governing section its ``See also`` leaf directs to
#: and which directs back.
SITES = [
    ("glossary", GLOSSARY_ENTRY.container_id),
    ("combat", COMBAT_ENTRY.container_id),
]

#: Policy exclusions inside this boundary, **listed with their reasons** rather
#: than asserted away: a site that silently lost a body leaf would otherwise look
#: identical to one that lost a running header.
POLICY_EXCLUDED = [
    {
        "site": site,
        "leaf_id": leaf.leaf_id,
        "page_index": leaf.page_index,
        "reason": exclusion_reason_for(leaf, LABELS),
        "content": leaf.content,
    }
    for site, cid in SITES
    for leaf in by_container[cid]
    if leaf.leaf_id not in REPRESENTED
]

# ---------------------------------------------------------------------------
# Clause cuts — the text each segment ends with, located at run time
# ---------------------------------------------------------------------------
#
# Keyed by ``(site, leaf content)`` rather than by leaf id so the table stays
# readable against the source.

CUTS: dict[tuple[str, str], list[str | None]] = {
    # --- Rules Glossary > Rules Definitions > Speed (page index 187) --------
    ("glossary", "Speed"): [None],
    (
        "glossary",
        "A creature has a Speed, which is the distance in feet the creature can "
        "cover when it moves on its turn.",
    ): ["A creature has a Speed,", None],
    ("glossary", "See also"): [None],
    (
        "glossary",
        f"{LDQ}Climbing,{RDQ} {LDQ}Crawling,{RDQ} {LDQ}Flying,{RDQ} "
        f"{LDQ}Jumping,{RDQ} {LDQ}Swimming{RDQ} and {LDQ}Playing the Game{RDQ} "
        f"({LDQ}Combat{RDQ}).",
    ): [
        f"{LDQ}Climbing,{RDQ}",
        f"{LDQ}Crawling,{RDQ}",
        f"{LDQ}Flying,{RDQ}",
        f"{LDQ}Jumping,{RDQ}",
        f"{LDQ}Swimming{RDQ}",
        None,
    ],
    ("glossary", "Special Speeds."): [None],
    (
        "glossary",
        "Some creatures have special speeds, such as a Burrow Speed, Climb "
        "Speed, Fly",
    ): [None],
    ("glossary", "Speed, or Swim Speed, each of which is defined"): [None],
    (
        "glossary",
        f"in this glossary. If you have more than one speed, choose which one to "
        f"use when you move; you can switch between the speeds during your move. "
        f"Whenever you switch, subtract the distance already moved from the new "
        f"speed. The result determines how much farther you can move. If the "
        f"result is 0 or less, you can{RSQ}t use the new speed during the current "
        f"move. For example, if you have a Speed of 30 and a Fly Speed of 40, you "
        f"could fly 10 feet, walk 10 feet, and leap into the air to fly 20 feet "
        f"more.",
    ): [
        "in this glossary.",
        "choose which one to use when you move;",
        "you can switch between the speeds during your move.",
        "subtract the distance already moved from the new speed.",
        "The result determines how much farther you can move.",
        f"you can{RSQ}t use the new speed during the current move.",
        None,
    ],
    ("glossary", "Changes to Your Speeds."): [None],
    (
        "glossary",
        "If an effect increases or decreases your Speed for a time, any special "
        "speed you have increases or decreases by an equal amount for the same "
        "duration. For example, if your Speed is reduced to 0 and you have a "
        "Climb Speed, your Climb Speed is also reduced to 0. Similarly, if your",
    ): [
        "by an equal amount for the same duration.",
        "your Climb Speed is also reduced to 0.",
        None,
    ],
    ("glossary", "Speed is halved and you have a Fly Speed, your Fly"): [None],
    ("glossary", "Speed is also halved."): [None],
    # --- Playing the Game > Combat > Movement and Position (page index 13) ---
    ("combat", "Movement and Position"): [None],
    ("combat", "On your turn, you can move a distance equal to your"): [None],
    ("combat", "Speed or less. Or you can decide not to move."): [
        "Speed or less.",
        None,
    ],
    (
        "combat",
        f"Your movement can include climbing, crawling, jumping, and swimming "
        f"(each explained in {LDQ}Rules Glossary{RDQ}). These different modes of "
        f"movement can be combined with your regular movement, or they can "
        f"constitute your entire move. However you{RSQ}re moving with your Speed, "
        f"you deduct the distance of each part of your move from it until it is "
        f"used up or until you are done moving, whichever comes first. A "
        f"character{RSQ}s Speed is determined during character creation. A "
        f"monster{RSQ}s Speed is noted in the monster{RSQ}s stat block. See "
        f"{LDQ}Rules Glossary{RDQ} for more about Speed as well as about special "
        f"speeds, such as a Climb Speed, Fly Speed, or Swim Speed.",
    ): [
        f"(each explained in {LDQ}Rules Glossary{RDQ}).",
        "or they can constitute your entire move.",
        "until you are done moving, whichever comes first.",
        f"A character{RSQ}s Speed is determined during character creation.",
        f"A monster{RSQ}s Speed is noted in the monster{RSQ}s stat block.",
        None,
    ],
}


def _partition(content: str, ends: list[str | None]) -> list[tuple[int, int]]:
    """Cut *content* at each end-marker, absorbing separators leftward."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for index, marker in enumerate(ends):
        if marker is None:
            assert index == len(ends) - 1, "only the final cut may run to the end"
            spans.append((cursor, len(content)))
            break
        at = content.find(marker, cursor)
        assert at >= 0, f"cut not found in the bound source: {marker!r}"
        assert (
            content.find(marker, at + 1) < 0
        ), f"cut is not unique in this leaf: {marker!r}"
        spans.append((cursor, at + len(marker)))
        cursor = at + len(marker)
    assert "".join(content[s:e] for s, e in spans) == content, "partition is not exact"
    return spans


# ---------------------------------------------------------------------------
# Derive the site table
# ---------------------------------------------------------------------------

SOURCE_SITES: list[dict[str, Any]] = []
CLAUSES: list[dict[str, Any]] = []
CLAUSE_TEXT: dict[str, str] = {}
MEMBER_LEAF_IDS: set[str] = set()
used_cuts: set[tuple[str, str]] = set()

for site, container_id in SITES:
    leaves = [lf for lf in by_container[container_id] if lf.leaf_id in REPRESENTED]
    leaf_rows: list[dict[str, Any]] = []
    for ordinal, leaf in enumerate(leaves):
        MEMBER_LEAF_IDS.add(leaf.leaf_id)
        key = (site, leaf.content)
        assert key in CUTS, f"uncut leaf in the population: {key!r}"
        assert key not in used_cuts, f"ambiguous cut key: {key!r}"
        used_cuts.add(key)
        spans = _partition(leaf.content, CUTS[key])
        owner = leaf.container_path[-1]
        leaf_rows.append(
            {
                "leaf_id": leaf.leaf_id,
                "ordinal": ordinal,
                "page_index": leaf.page_index,
                "leaf_type": leaf.leaf_type,
                "attached_to": "entry" if owner == container_id else "table",
                "owning_container_id": owner,
                "owning_container_label": LABELS[owner],
                "length": len(leaf.content),
                "content": leaf.content,
                "clause_ids": [f"{site}/{ordinal}/{i}" for i in range(len(spans))],
            }
        )
        for i, (start, end) in enumerate(spans):
            clause_id = f"{site}/{ordinal}/{i}"
            CLAUSE_TEXT[clause_id] = leaf.content[start:end]
            CLAUSES.append(
                {
                    "clause_id": clause_id,
                    "site": site,
                    "leaf_id": leaf.leaf_id,
                    "page_index": leaf.page_index,
                    "char_start": start,
                    "char_end": end,
                    "text": leaf.content[start:end],
                }
            )
    SOURCE_SITES.append(
        {
            "site": site,
            "container_id": container_id,
            "container_path": _path_of(container_id),
            "pages": sorted({lf["page_index"] for lf in leaf_rows}),
            "leaves": leaf_rows,
        }
    )

assert used_cuts == set(CUTS), sorted(set(CUTS) - used_cuts)

#: This population owns no printed table, asserted rather than assumed: every
#: member leaf hangs directly off its entry. The frozen table inventory is the
#: independent witness — it lists the logical tables on the population's own
#: printed pages, and none of them is owned by either member container.
assert all(
    row["attached_to"] == "entry" for site in SOURCE_SITES for row in site["leaves"]
), "a member leaf is attached to a table"
_MEMBER_PRINTED_PAGES = sorted(
    {row["page_index"] + 1 for site in SOURCE_SITES for row in site["leaves"]}
)
_inventory = json.loads(TABLE_INVENTORY_PATH.read_text(encoding="utf-8"))
_member_container_ids = {cid for _, cid in SITES}
TABLES_ON_POPULATION_PAGES = sorted(
    (
        {
            "logical_table_id": entry["logical_table_id"],
            "printed_pages": entry["printed_pages"],
            "header": entry["header"],
            "owned_by_a_member_container": entry["logical_table_id"]
            in _member_container_ids,
        }
        for entry in _inventory["tables"]
        if set(entry["printed_pages"]) & set(_MEMBER_PRINTED_PAGES)
    ),
    key=lambda e: str(e["logical_table_id"]),
)
assert not any(t["owned_by_a_member_container"] for t in TABLES_ON_POPULATION_PAGES)

# ---------------------------------------------------------------------------
# The reciprocity the source itself prints, in both directions
# ---------------------------------------------------------------------------

_glossary_leaves = SOURCE_SITES[0]["leaves"]
_SEE_ALSO_ROW = next(row for row in _glossary_leaves if row["content"] == "See also")
_CITATION_ROW = _glossary_leaves[_glossary_leaves.index(_SEE_ALSO_ROW) + 1]
CITATION = _CITATION_ROW["content"]
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]] in CITATION, CITATION
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]] in CITATION, CITATION

RECIPROCAL_CLAUSE_ID = next(
    clause["clause_id"] for clause in CLAUSES if RECIPROCAL_CITATION in clause["text"]
)

DIRECTION = {
    "corroboration": {
        "from_container": _path_of(DEFERRAL_LEAF.container_path[-1]),
        "leaf_id": DEFERRAL_LEAF.leaf_id,
        "sentence": DEFERRAL,
        "occurrences_in_the_whole_release": 1,
        "in_the_population": False,
    },
    "outbound": {
        "from_site": "glossary",
        "see_also_leaf_id": _SEE_ALSO_ROW["leaf_id"],
        "citation_leaf_id": _CITATION_ROW["leaf_id"],
        "citation_text": CITATION,
        "names_section": LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]],
        "names_subsection": LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]],
        "to_site": "combat",
    },
    "inbound": {
        "from_site": "combat",
        "leaf_id": RECIPROCAL_LEAF.leaf_id,
        "clause_id": RECIPROCAL_CLAUSE_ID,
        "sentence": RECIPROCAL_CITATION,
        "occurrences_in_the_whole_release": 1,
        "to_site": "glossary",
    },
    "naive_cooccurrence_would_have_matched": NAIVE_COOCCURRENCE,
    "note": (
        "Membership is not a label query. Four containers are labeled 'Speed' "
        "and three of them are not this rule, so the derivation is the printed "
        "reciprocal citation: the glossary entry names the other site's section "
        "and subsection, and exactly one leaf in the release prints the sentence "
        "pointing back. A co-occurrence test over the same subsection would have "
        "matched three entries; the two it adds cite the glossary for something "
        "other than Speed."
    ),
}

#: Each term the population's ``See also`` citation names, as its own clause,
#: with the plain fact of whether the glossary defines an entry by that label.
#: **Not a reference list.** Whether a cited term becomes a reference, and to
#: what key, is a judgment the checkpoint makes; recording it here would be
#: proposing.
_GLOSSARY_ENTRY_LABELS = {
    c.label
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry"
    and any(LABELS[a] == "Rules Definitions" for a in _ancestry(c.container_id))
}
CITED_TERMS = [
    {
        "clause_id": clause_id,
        "text": CLAUSE_TEXT[clause_id],
        "quoted_term": re.findall(f"{LDQ}([^{RDQ}]+){RDQ}", CLAUSE_TEXT[clause_id]),
        "glossary_entry_with_that_label_exists": [
            term.rstrip(".,")
            for term in re.findall(f"{LDQ}([^{RDQ}]+){RDQ}", CLAUSE_TEXT[clause_id])
            if term.rstrip(".,") in _GLOSSARY_ENTRY_LABELS
        ],
    }
    for clause_id in _CITATION_ROW["clause_ids"]
]

# ---------------------------------------------------------------------------
# Sentences that cross leaves
# ---------------------------------------------------------------------------
#
# A clause id is leaf-local by construction. Where the frozen extraction split a
# printed sentence at a column or page boundary, the group of clause ids that
# reconstructs it is named here and the reconstruction is asserted, so a judgment
# about a whole sentence can cite its exact subspans.

CROSS_LEAF_SENTENCES: list[list[str]] = [
    ["glossary/5/0", "glossary/6/0", "glossary/7/0"],
    ["glossary/9/2", "glossary/10/0", "glossary/11/0"],
    ["combat/1/0", "combat/2/0"],
]
CROSS_LEAF_ROWS: list[dict[str, Any]] = []
for _group in CROSS_LEAF_SENTENCES:
    _parts = [CLAUSE_TEXT[cid] for cid in _group]
    for _part in _parts[:-1]:
        assert not _part.rstrip().endswith("."), _part
    assert _parts[-1].rstrip().endswith("."), _parts[-1]
    _leaves_crossed = {
        clause["leaf_id"] for clause in CLAUSES if clause["clause_id"] in _group
    }
    assert len(_leaves_crossed) == len(_group), _group
    CROSS_LEAF_ROWS.append(
        {
            "clause_ids": list(_group),
            "leaf_ids": sorted(_leaves_crossed),
            "reconstructed_sentence": " ".join(_part.strip() for _part in _parts),
        }
    )

# ---------------------------------------------------------------------------
# The frozen prior, read for what it already says about this population's term
# ---------------------------------------------------------------------------

PRIOR = load_accepted_inputs(REVIEW_PRIOR_PATH)
assert oracle_identity(PRIOR.oracle) == REVIEW_PRIOR_IDENTITY
assert sorted(b.batch_id for b in PRIOR.batches) == REVIEW_PRIOR_BATCH_IDS
PRIOR_KEYS = sorted(r.semantic_key for r in PRIOR.oracle.representation.records)
PRIOR_DEFINED = set(PRIOR_KEYS)
PRIOR_DANGLING = sorted(
    {
        ref.target_record_key
        for ref in PRIOR.oracle.representation.references
        if ref.target_record_key not in PRIOR_DEFINED
    }
)

_SPAN_LEAF = {span.span_id: span.leaf_id for span in PRIOR.oracle.spans}
_LEAF_OWNER = {
    leaf.leaf_id: leaf.container_path[-1]
    for leaf in LEDGER_OBJ.leaves
    if leaf.container_path
}
_PRIOR_KEYS_BY_CONTAINER: defaultdict[str, set[str]] = defaultdict(set)
for _claim in PRIOR.oracle.representation.provenance:
    _leaf = _SPAN_LEAF.get(_claim.span_id)
    _owner = _LEAF_OWNER.get(_leaf) if _leaf else None
    if _owner is not None:
        _PRIOR_KEYS_BY_CONTAINER[_owner].add(str(_claim.target_key[0]))
assert _PRIOR_KEYS_BY_CONTAINER, "no accepted provenance resolved to this release"

#: The provenance shapes accepted authority already uses, counted rather than
#: recalled, so the checkpoint can say whether a shape it reaches for is
#: precedent or invention.
PRIOR_PROVENANCE_SHAPES = dict(
    sorted(
        Counter(
            f"{claim.target_kind.value}/{claim.role.value}"
            for claim in PRIOR.oracle.representation.provenance
        ).items()
    )
)

#: **No member leaf is already represented.** The two sites are untouched by
#: accepted authority, asserted rather than assumed: a batch that re-represented
#: a leaf another batch already owns would be a duplicate, not a new record.
_ALREADY_REPRESENTED_MEMBERS = sorted(
    leaf_id for leaf_id in MEMBER_LEAF_IDS if leaf_id in set(_SPAN_LEAF.values())
)
assert not _ALREADY_REPRESENTED_MEMBERS, _ALREADY_REPRESENTED_MEMBERS

# ---------------------------------------------------------------------------
# The boundary: every other leaf that prints the word, enumerated
# ---------------------------------------------------------------------------

WORD = re.compile(r"speed", re.IGNORECASE)
BOUNDARY = [
    {
        "leaf_id": leaf.leaf_id,
        "page_index": leaf.page_index,
        "leaf_type": leaf.leaf_type,
        "container_label": LABELS[leaf.container_path[-1]],
        "container_path": _path_of(leaf.container_path[-1]),
        "section": LABELS[_ancestry(leaf.container_path[-1])[-1]],
        "represented_by_5c": leaf.leaf_id in REPRESENTED,
        "prints_capitalized_term": bool(re.search(r"\bSpeed\b", leaf.content)),
        "already_accepted_as": sorted(
            _PRIOR_KEYS_BY_CONTAINER.get(leaf.container_path[-1], ())
        ),
        "content": leaf.content,
    }
    for leaf in sorted(LEDGER_OBJ.leaves, key=lambda x: (x.page_index, x.char_start))
    if WORD.search(leaf.content) and leaf.leaf_id not in MEMBER_LEAF_IDS
]
for _row in BOUNDARY:
    assert _row["container_path"] != SOURCE_SITES[0]["container_path"], _row
    assert _row["container_path"] != SOURCE_SITES[1]["container_path"], _row
    assert all(key in PRIOR_DEFINED for key in _row["already_accepted_as"]), _row

#: Every boundary leaf is represented by 5c — so the word is emphatically not a
#: proxy for the population, and the exclusion is a judgment about what the
#: source *states*, never an artifact of what 5c dropped.
BOUNDARY_ALL_REPRESENTED = all(row["represented_by_5c"] for row in BOUNDARY)
assert BOUNDARY_ALL_REPRESENTED

BOUNDARY_BY_SECTION: dict[str, int] = defaultdict(int)
for _row in BOUNDARY:
    BOUNDARY_BY_SECTION[_row["section"]] += 1

#: The lowercase-only figure, disclosed rather than folded in: the source uses
#: ``speed`` as a common noun as well as ``Speed`` as the defined term, and both
#: are inside the enumerated boundary above.
BOUNDARY_LOWERCASE_ONLY = sum(
    1 for row in BOUNDARY if not row["prints_capitalized_term"]
)

# ---------------------------------------------------------------------------
# Adjudicated boundary — the containers a reader would actually question
# ---------------------------------------------------------------------------
#
# Facts only. Each row says where the container is, how large it is, whether the
# population's own citation leaf names it, whether it prints the reciprocal
# citation sentence, and whether it names ``Speed`` back. What each one *is*
# belongs to the checkpoint.

ADJUDICATED_PATHS = [
    # The three other containers the release labels ``Speed``.
    "Character Origins > Character Species > Speed",
    "Equipment > Mounts and Vehicles > Speed",
    "Monsters > Parts of a Stat Block > Speed",
    # The four special speeds the population's own prose names.
    "Rules Glossary > Rules Definitions > Burrow Speed",
    "Rules Glossary > Rules Definitions > Climb Speed",
    "Rules Glossary > Rules Definitions > Fly Speed",
    "Rules Glossary > Rules Definitions > Swim Speed",
    # The five glossary entries the population's ``See also`` citation names.
    "Rules Glossary > Rules Definitions > Climbing",
    "Rules Glossary > Rules Definitions > Crawling",
    "Rules Glossary > Rules Definitions > Flying",
    "Rules Glossary > Rules Definitions > Jumping",
    "Rules Glossary > Rules Definitions > Swimming",
    # The nearest ``Combat`` sibling: it restates the per-turn allowance in almost
    # the population's words, and then defers the movement rules to the population.
    "Playing the Game > Combat > Your Turn",
    # The ``Combat`` siblings that spend Speed without stating it.
    "Playing the Game > Combat > Difficult Terrain",
    "Playing the Game > Combat > Breaking Up Your Move",
    "Playing the Game > Combat > Dropping Prone",
    "Playing the Game > Combat > Moving around Other Creatures",
    "Playing the Game > Combat > Creature Size",
    "Playing the Game > Combat > Mounting and Dismounting",
    # The two sites that convert Speed into a travel rate.
    "Playing the Game > Exploration > Travel Pace",
    "Gameplay Toolbox > Travel Pace > Special Movement",
]

ADJUDICATED_BOUNDARY = []
for _path in ADJUDICATED_PATHS:
    _container = _one_container(_path)
    _leaves = by_container[_container.container_id]
    _text = " ".join(lf.content for lf in _leaves)
    ADJUDICATED_BOUNDARY.append(
        {
            "container_path": _path,
            "container_id": _container.container_id,
            "container_type": _container.container_type,
            "leaf_count": len(_leaves),
            "pages": sorted({lf.page_index for lf in _leaves}),
            "policy_excluded_leaves": [
                lf.leaf_id for lf in _leaves if lf.leaf_id not in REPRESENTED
            ],
            "named_by_the_populations_citation_leaf": bool(
                LABELS[_container.container_id] in CITATION
            ),
            "prints_the_reciprocal_citation": RECIPROCAL_CITATION in _text,
            "defers_the_movement_rules_to_the_population": DEFERRAL in _text,
            "names_the_capitalized_term": bool(re.search(r"\bSpeed\b", _text)),
            "cites_the_glossary_speed_entry_in_a_see_also": bool(
                re.search(f"{LDQ}Speed\\.{RDQ}", _text)
            ),
            "already_accepted_as": sorted(
                _PRIOR_KEYS_BY_CONTAINER.get(_container.container_id, ())
            ),
            "leaves": [
                {
                    "leaf_id": lf.leaf_id,
                    "page_index": lf.page_index,
                    "leaf_type": lf.leaf_type,
                    "represented_by_5c": lf.leaf_id in REPRESENTED,
                    "content": lf.content,
                }
                for lf in _leaves
            ],
        }
    )
assert not any(
    row["prints_the_reciprocal_citation"] for row in ADJUDICATED_BOUNDARY
), "an adjudicated-boundary container prints the membership citation"

# ---------------------------------------------------------------------------
# Reference scope, enumerated without closing anything
# ---------------------------------------------------------------------------

#: **The schema this discovery ran against**, read off the frozen prior rather
#: than off the checkout, for the reason ``areas-of-effect-1``'s run records:
#: source discovery states nothing in typed facts, so the binding that belongs in
#: its manifest is the frozen one and not the one that moves with every mint.
SCHEMA = (PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash)
assert SCHEMA[0] == REVIEW_PRIOR_SCHEMA_VERSION, SCHEMA

CURRENT_SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
CURRENT_SCHEMA_REACHED_BY = (
    []
    if CURRENT_SCHEMA == SCHEMA
    else [step.lift_id for step in lift_path(SCHEMA, CURRENT_SCHEMA)]
)
assert CURRENT_SCHEMA == SCHEMA or CURRENT_SCHEMA_REACHED_BY, (
    SCHEMA,
    CURRENT_SCHEMA,
)

#: Every citation accepted authority makes of this population's term, whole.
#: Reported, not resolved.
INBOUND_CITATIONS = sorted(
    (
        {
            "from_record_key": ref.from_record_key,
            "from_component_key": ref.from_component_key,
            "scope_key": ref.scope_key,
            "source_text": ref.source_text,
            "target_record_key": ref.target_record_key,
            "target_defined_in_prior": ref.target_record_key in PRIOR_DEFINED,
        }
        for ref in PRIOR.oracle.representation.references
        if ref.target_record_key == "glossary.speed"
    ),
    key=lambda r: (str(r["from_record_key"]), str(r["source_text"])),
)

#: The precedent the checkpoint's outbound judgment is measured against, read out
#: of the prior rather than remembered. ``Dash`` prints *"such as a Fly Speed or
#: Swim Speed"* in its own substantive prose and emitted **no** reference for
#: either; the reference it did emit came from its ``See also`` citation leaf.
#: Stated as the two facts that make it checkable: every reference the prior
#: holds whose source text names a speed, and the count of references targeting
#: anything other than ``glossary.speed`` whose key mentions a speed.
DASH_PRECEDENT = {
    "references_whose_source_text_names_a_speed": sorted(
        (
            {
                "from_record_key": ref.from_record_key,
                "source_text": ref.source_text,
                "target_record_key": ref.target_record_key,
            }
            for ref in PRIOR.oracle.representation.references
            if WORD.search(ref.source_text)
        ),
        key=lambda r: (str(r["from_record_key"]), str(r["source_text"])),
    ),
    "references_targeting_a_special_speed": [
        ref.target_record_key
        for ref in PRIOR.oracle.representation.references
        if WORD.search(ref.target_record_key)
        and ref.target_record_key != "glossary.speed"
    ],
    "note": (
        "Accepted authority already read a named example inside substantive "
        "prose as part of the rule rather than as a citation: action.dash prints "
        "'such as a Fly Speed or Swim Speed' and emitted no reference for "
        "either. Recorded as a fact about the prior. Whether this population's "
        "own 'such as' clauses follow it is the checkpoint's judgment."
    ),
}

#: The scope keys accepted authority has ever used for a reference.
PRIOR_SCOPE_KEYS = sorted(
    {ref.scope_key for ref in PRIOR.oracle.representation.references}
)

#: A **substring scan**, reported as one. Every Rules Glossary entry label that
#: occurs anywhere in this population's clause text, with the clauses it occurs
#: in. Deliberately not a citation list: an occurrence is not a citation, which
#: is the same rule that governs the boundary.
_CANDIDATE_TERMS = sorted(
    {
        term
        for clause in CLAUSES
        for term in _GLOSSARY_ENTRY_LABELS
        if " [" not in term and term != "Speed" and term in clause["text"]
    }
)
GLOSSARY_LABEL_OCCURRENCES = {
    term: {
        "glossary_entry_label": True,
        "clause_ids": [c["clause_id"] for c in CLAUSES if term in c["text"]],
    }
    for term in _CANDIDATE_TERMS
}

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

MANIFEST = {
    "artifact_kind": "source_discovery_manifest",
    "batch_id": "speed-1",
    "issue": "CRD Issue 5d (#137)",
    "generated_by": Path(__file__).name,
    "note": (
        "Discovery only. No draft, proposal, acceptance, lift, publication or "
        "schema change is produced by this run, and no disposition and no "
        "candidate record key is encoded here; the checkpoint document carries "
        "the judgments and cites these clause ids."
    ),
    "input_paths": {
        "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
        "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
        "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "table_inventory": TABLE_INVENTORY_PATH.relative_to(REPO).as_posix(),
        "afterworlds_package": IMPORTED_FROM.relative_to(REPO).as_posix(),
        "output": MANIFEST_PATH.relative_to(REPO).as_posix(),
    },
    "release_binding": {
        "package_uuid": CAND.package_uuid,
        "release_version": CAND.release_version,
        "authoritative_source_hash": CAND.authoritative_source_hash,
        "transform_config_hash": CAND.transform_config_hash,
        "bundle_root_hash": CAND.bundle.bundle_root_hash,
        "persisted_corpus_digest": PERSISTED_CORPUS_DIGEST,
        "persisted_corpus_digest_note": (
            "The five values above are re-derived from the committed PDF by this "
            "run and asserted. This sixth is carried from the published CRD "
            "Issue 5c release record and disclosed as carried: recomputing it "
            "needs a session over the persisted rp_sources rows plus read-back "
            "vector state (persistence.recompute_persisted_digest), and "
            "verifying a published release against declared values is "
            "operational.load_verified_operational_corpus, the narrower "
            "downstream trust seam. Neither requires a publish; this run "
            "performs neither, and no operational database evidence was "
            "produced by it -- no session, no rp_sources, no Chroma, no "
            "persistence layer was touched."
        ),
    },
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "representation_schema_note": (
        "The frozen review prior's binding, which this discovery ran against. "
        "The checkout's own representation schema is not recorded here: source "
        "discovery is independent of representation, and recording a value that "
        "moves with every schema mint would rot this manifest against evidence "
        "that had not moved. The run asserts separately that the checkout is "
        "that binding or a registered successor of it; for this batch it is the "
        "same binding, so no crossing exists and none is claimed."
    ),
    "current_schema_reached_by": CURRENT_SCHEMA_REACHED_BY,
    "review_prior": {
        "path": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "content_sha256": REVIEW_PRIOR_CONTENT_SHA256,
        "blob": REVIEW_PRIOR_BLOB,
        "oracle_identity": REVIEW_PRIOR_IDENTITY,
        "batch_ids": REVIEW_PRIOR_BATCH_IDS,
        "record_keys": PRIOR_KEYS,
        "unresolved_targets": PRIOR_DANGLING,
        "reference_scope_keys": PRIOR_SCOPE_KEYS,
    },
    "membership_rule": (
        "A leaf is in this population when the bound release attaches it to one "
        "of the two entry containers the source itself joins by a reciprocal "
        "citation: 'Rules Glossary > Rules Definitions > Speed', and the one "
        "entry in the whole release that prints the sentence 'See \"Rules "
        "Glossary\" for more about Speed'. The label is NOT the query -- four "
        "containers are labeled 'Speed' and three of them are a species "
        "pointer, a vehicle-speed homonym and a stat-block pointer that defers "
        "to the glossary. Printing the word 'speed' is use, not definition, and "
        "pulls nothing in."
    ),
    "membership": {
        "containers_labeled_speed": SPEED_LABELLED_PATHS,
        "member_entry_count": len(SITES),
        "sites": [s["site"] for s in SOURCE_SITES],
        "leaf_count": sum(len(s["leaves"]) for s in SOURCE_SITES),
        "clause_count": len(CLAUSES),
        "policy_excluded": POLICY_EXCLUDED,
        "member_leaves_already_represented_by_accepted_authority": (
            _ALREADY_REPRESENTED_MEMBERS
        ),
    },
    "direction": DIRECTION,
    "source_sites": SOURCE_SITES,
    "clauses": CLAUSES,
    "cited_terms_in_the_see_also_citation": CITED_TERMS,
    "cited_terms_note": (
        "The citation leaf is cut per cited term so each is separately "
        "addressable, which is the shape actions-1 used for its own multi-term "
        "citation leaf. Whether a cited term becomes a reference, and to what "
        "key, is the checkpoint's judgment; only the existence of a glossary "
        "entry by that label is a fact and only that is recorded."
    ),
    "cross_leaf_sentences": CROSS_LEAF_ROWS,
    "extraction_artifacts": {
        "note": (
            "Properties of the frozen 5c release, carried verbatim rather than "
            "repaired. No source-corpus change is proposed or made here."
        ),
        "sentences_split_across_leaves": len(CROSS_LEAF_ROWS),
        "prose_continuations_typed_stat_field": [
            row["leaf_id"]
            for site in SOURCE_SITES
            for row in site["leaves"]
            if row["leaf_type"] == "stat_field"
        ],
        "prose_continuations_typed_stat_field_note": (
            "Mid-sentence continuations the extraction typed as stat_field "
            "rather than paragraph. Recorded because the leaf_type is carried "
            "into evidence and a reader should not mistake it for a stat block."
        ),
        "population_owns_no_printed_table": True,
        "logical_tables_on_the_populations_printed_pages": (TABLES_ON_POPULATION_PAGES),
    },
    "boundary_count": len(BOUNDARY),
    "boundary_all_represented_by_5c": BOUNDARY_ALL_REPRESENTED,
    "boundary_by_section": dict(sorted(BOUNDARY_BY_SECTION.items())),
    "boundary_lowercase_only_leaf_count": BOUNDARY_LOWERCASE_ONLY,
    "boundary_note": (
        "Every leaf outside the population whose text contains 'speed' in any "
        "case, enumerated with its container so the exclusion is checkable "
        "rather than asserted. All of them are represented by 5c, so the word is "
        "not a proxy for the population and the exclusion is a judgment about "
        "what the source states, never an artifact of what 5c dropped."
    ),
    "adjudicated_boundary": ADJUDICATED_BOUNDARY,
    "adjudicated_boundary_note": (
        "The containers a reader would actually question, with full leaf text "
        "and facts only: the three other 'Speed' labels, the four special-speed "
        "glossary entries this population's prose names, the five glossary "
        "entries its See-also citation names, the Combat siblings that spend "
        "Speed, and the two sites that convert it into a travel rate. What each "
        "one is -- an outbound reference, an incidental use, or a sibling record "
        "for a later batch -- is the checkpoint's judgment."
    ),
    "prior_provenance_shapes": PRIOR_PROVENANCE_SHAPES,
    "boundary": BOUNDARY,
    "inbound_citations": INBOUND_CITATIONS,
    "outbound_reference_precedent": DASH_PRECEDENT,
    "glossary_entry_labels_occurring_in_population_text": GLOSSARY_LABEL_OCCURRENCES,
    "glossary_entry_labels_occurring_in_population_text_note": (
        "A substring scan over the clause text above, not a citation list. An "
        "occurrence is not a citation -- the same rule that governs the "
        "boundary. What each occurrence is belongs to the checkpoint's "
        "judgment, and the clause ids are how it is checked."
    ),
}

MANIFEST_PATH.write_text(
    json.dumps(MANIFEST, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
    encoding="utf-8",
    newline="\n",
)

# --- Nothing else moved -----------------------------------------------------
assert _lf_sha256(REVIEW_PRIOR_PATH) == _PRIOR_BEFORE, "the frozen prior moved"
assert _lf_sha256(LIVE_ORACLE_PATH) == _LIVE_BEFORE, "the live accepted artifact moved"
for _name, _digest in _RETAINED_BEFORE.items():
    assert (
        hashlib.sha256((OUT / _name).read_bytes()).hexdigest() == _digest
    ), f"retained evidence moved: {_name}"

print(f"containers labeled Speed  {len(SPEED_LABELLED_PATHS)}")
print(f"member entries            {len(SITES)}")
print(f"leaves                    {sum(len(s['leaves']) for s in SOURCE_SITES)}")
print(f"clauses                   {len(CLAUSES)}")
print(f"policy exclusions         {len(POLICY_EXCLUDED)}")
print(f"naive co-occurrence       {NAIVE_COOCCURRENCE}")
print(f"cross-leaf sentences      {len(CROSS_LEAF_ROWS)}")
print(f"boundary leaves           {len(BOUNDARY)}")
print(f"boundary all represented  {BOUNDARY_ALL_REPRESENTED}")
print(f"boundary sections         {dict(sorted(BOUNDARY_BY_SECTION.items()))}")
print(f"lowercase-only boundary   {BOUNDARY_LOWERCASE_ONLY}")
print(f"adjudicated containers    {len(ADJUDICATED_BOUNDARY)}")
print(f"prior prov shapes         {PRIOR_PROVENANCE_SHAPES}")
print(f"inbound citations         {INBOUND_CITATIONS}")
print(f"current schema reached by {CURRENT_SCHEMA_REACHED_BY}")
print(f"manifest sha256           {_lf_sha256(MANIFEST_PATH)}")
