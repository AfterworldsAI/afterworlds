"""CRD Issue 5d — batch `cover-1`, **source-discovery run only**.

Reads the committed SRD through the 5c pipeline, re-derives the complete
``Cover`` source population from the source's own containers, cuts every
represented leaf into an exact clause partition, enumerates the boundary the
population excludes, and writes one deterministic LF manifest. It builds no
draft, proposes nothing, accepts nothing, publishes nothing, lifts nothing,
executes no schema change and touches no database.

Membership has no tag to read
-----------------------------
``areas-of-effect-1`` re-derived its class from a printed tag: the Rules
Glossary's preamble names five tag values and ``[Area of Effect]`` is one of
them, so the six shapes are a query. ``Cover`` has no tag. What the source does
print is two containers it labels ``Cover`` — a Rules Glossary entry (p179 as
printed, page index 178) and a ``Playing the Game > Combat`` entry (p15 printed,
page index 14) — and a ``See also`` leaf in the first that names the chapter and
subsection of the second. So membership here is a structural claim, and this run
states it as one and fails loudly if the structure moved:

* exactly two ``entry`` containers in the bound release are labeled ``Cover``;
* one descends from ``Rules Definitions``, the other from ``Combat``;
* the glossary entry's last two leaves are a bare ``See also`` and the
  citation that names them.

**The source owns the boundary.** A record is in this population because the
source *attaches* it to a container labeled ``Cover``, not because it prints the
word. Thirty other leaves in the bound release contain ``Cover`` — spells, class
features, magic items, monster stat blocks, ``Making an Attack``, ``Targets``,
``Blindsight``, ``Hide [Action]`` and the ``Area of Effect`` entry that already
cites it in accepted authority. Every one of them *uses* the rule; none of them
*states* it. They are enumerated in the manifest with their containers so the
exclusion is checkable rather than asserted, and pulling any of them in would be
a batch expansion the governing issue forbids.

What this run establishes, and what it does not
-----------------------------------------------
1. **Membership**, from the source's containers rather than from a remembered
   count, with the boundary enumerated rather than waved at.
2. **Exact coverage**, as ``leaf_id`` plus leaf-local half-open character
   ranges, with the partition asserted to reconstruct each leaf byte for byte.
   Every clause the checkpoint judges is addressable here.
3. **The unchanged accepted prior**, by two independent identities before and
   after the run, and the live accepted artifact as a mutation sentinel that is
   never an input.

It establishes nothing about representation. Whether ``Cover`` is one record or
an umbrella over three degrees, which clauses are typeable under schema 9 and
which are irreducible prose, and what the printed citations resolve to are
judgments; they live in ``issue-5d-cover-1-DISCOVERY-CHECKPOINT.md`` and cite
the clause ids this run emits. No disposition and no candidate record key is
encoded here, because a discovery run that shipped its own conclusions would be
proposing.

Clause cuts
-----------
A cut names the text a segment **ends with**; ``None`` means "to the end of the
leaf". Cuts are located in the bound leaf content at run time and fail loudly if
the source moved, so a re-extraction cannot silently re-cut a clause under a
judgment that was written about the old one. Separator runs are absorbed as the
*leading* text of the next segment, exactly as the accepted batch generators do,
so the partition reconstructs each leaf byte for byte.

The cuts are sentence-level except in four places, each for a stated reason. The
glossary definition's degree list is cut per degree, because each degree is a
distinct claim about a distinct benefit. The Combat paragraph's final segment is
the table caption ``Cover``, which the extraction absorbed into the end of the
prose leaf — cut apart so a judgment about the rule cannot accidentally cover a
caption. And the Half and Total rows' cells arrive fused, benefit run together
with ``Offered By`` — cut at the printed column boundary, which restores the
printed structure without altering a byte.

Two extraction artifacts are carried verbatim rather than smoothed, because the
manifest must describe the bound release and not a tidied reading of it: the
Three-Quarters degree label extracts as ``ThreeQuarters`` where the source
prints *Three-Quarters*, and the printed Cover table arrives as two logical
tables plus three leaves attached directly to the entry. Both are properties of
the frozen 5c release — the committed table inventory independently records the
same two logical tables — and neither is repaired here.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
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
#: review: conditions-1, hazards-1, actions-1, attitudes-1 and
#: areas-of-effect-1, representation schema 9. Read only, by content identity,
#: and asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1.json"
    )
)

#: **A mutation sentinel, never an input.** Bytes captured before the run and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: The frozen 5c expected-table oracle, read only, as an independent witness
#: that the Cover table's fragmentation is a property of the bound release.
TABLE_INVENTORY_PATH = (
    REPO / "src/afterworlds/ingestion/corpus/srd_table_inventory.json"
)

MANIFEST_PATH = OUT / "issue-5d-cover-1-source-manifest.json"

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
REVIEW_PRIOR_CONTENT_SHA256 = "9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "467fcc62c8fb64e54cf74e73a6f55c384129eef7"  # pragma: allowlist secret
)
REVIEW_PRIOR_IDENTITY = "8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = [
    "actions-1",
    "areas-of-effect-1",
    "attitudes-1",
    "conditions-1",
    "hazards-1",
]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-9"

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

#: The only binding value NOT independently derivable here: a function of the
#: persisted `rp_sources` rows and verified Chroma state, so reproducing it
#: requires an actual publish, which this run must not do. Taken from the
#: published CRD Issue 5c release record and disclosed as such.
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

# ---------------------------------------------------------------------------
# Membership, re-derived from the source's own containers
# ---------------------------------------------------------------------------

COVER_ENTRIES = sorted(
    (
        c
        for c in LEDGER_OBJ.containers
        if c.container_type == "entry" and c.label == "Cover"
    ),
    key=lambda c: min(lf.page_index for lf in by_container[c.container_id]),
)
assert len(COVER_ENTRIES) == 2, [c.container_id for c in COVER_ENTRIES]

COMBAT_ENTRY, GLOSSARY_ENTRY = COVER_ENTRIES
assert "Combat" in _path_of(COMBAT_ENTRY.container_id), _path_of(
    COMBAT_ENTRY.container_id
)
assert "Rules Definitions" in _path_of(GLOSSARY_ENTRY.container_id), _path_of(
    GLOSSARY_ENTRY.container_id
)

#: The two source sites, in the order a reader reaches them from the glossary:
#: the untagged glossary entry the accepted ``Area of Effect`` umbrella cites,
#: and the governing section its ``See also`` leaf directs to.
SITES = [
    ("glossary", GLOSSARY_ENTRY.container_id),
    ("combat", COMBAT_ENTRY.container_id),
]

#: Policy exclusions inside this boundary, **listed with their reasons** rather
#: than asserted away: a site that silently lost a body leaf would otherwise
#: look identical to one that lost a running header.
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
# readable against the source. The site is part of the key because both entries
# print the heading ``Cover``, so content alone is ambiguous here in a way it was
# not for the tagged classes.
RSQ = "’"  # right single quotation mark
LDQ, RDQ = "“", "”"  # double quotation marks
ELL = "…"  # horizontal ellipsis

CUTS: dict[tuple[str, str], list[str | None]] = {
    # --- Rules Glossary > Rules Definitions > Cover (page index 178) --------
    ("glossary", "Cover"): [None],
    (
        "glossary",
        f"Cover provides a degree of protection to a target behind it. There "
        f"are three degrees of cover, each of which provides a different "
        f"benefit to a target: Half Cover (+2 bonus to AC and Dexterity saving "
        f"throws), Three-Quarters Cover (+5 bonus to AC and Dexterity saving "
        f"throws), and Total Cover (can{RSQ}t be targeted directly). If behind "
        f"more than one degree of cover, a target benefits only from the most "
        f"protective degree.",
    ): [
        "protection to a target behind it.",
        "a different benefit to a target:",
        "Half Cover (+2 bonus to AC and Dexterity saving throws),",
        "Three-Quarters Cover (+5 bonus to AC and Dexterity saving throws),",
        f"and Total Cover (can{RSQ}t be targeted directly).",
        None,
    ],
    ("glossary", "See also"): [None],
    ("glossary", f"{LDQ}Playing the Game{RDQ} ({LDQ}Combat{RDQ})."): [None],
    # --- Playing the Game > Combat > Cover (page index 14) ------------------
    ("combat", "Cover"): [None],
    (
        "combat",
        f"Walls, trees, creatures, and other obstacles can provide cover, "
        f"making a target more difficult to harm. As detailed in the Cover "
        f"table, there are three degrees of cover, each of which gives a "
        f"different benefit to a target. A target can benefit from cover only "
        f"when an attack or other effect originates on the opposite side of "
        f"the cover. If a target is behind multiple sources of cover, only the "
        f"most protective degree of cover applies; the degrees aren{RSQ}t added "
        f"together. For example, if a target is behind a creature that gives "
        f"Half Cover and a tree trunk that gives Three-Quarters Cover, the "
        f"target has Three-Quarters Cover. Cover",
    ): [
        "making a target more difficult to harm.",
        "each of which gives a different benefit to a target.",
        "originates on the opposite side of the cover.",
        f"the degrees aren{RSQ}t added together.",
        "the target has Three-Quarters Cover.",
        None,
    ],
    ("combat", "Degree"): [None],
    ("combat", "Benefit to Target"): [None],
    ("combat", f"Offered By {ELL}"): [None],
    ("combat", "Half"): [None],
    (
        "combat",
        "+2 bonus to AC and Dexterity saving throws Another creature or an "
        "object that covers at least half of the target",
    ): ["+2 bonus to AC and Dexterity saving throws", None],
    ("combat", "ThreeQuarters"): [None],
    ("combat", "+5 bonus to AC and Dexterity saving throws"): [None],
    ("combat", "An object that covers at least three-quarters of the target"): [None],
    ("combat", "Total"): [None],
    (
        "combat",
        f"Can{RSQ}t be targeted directly An object that covers the whole target",
    ): [f"Can{RSQ}t be targeted directly", None],
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
        # Where the leaf sits relative to the entry: attached directly to it, or
        # inside a table container beneath it. The printed Cover table does not
        # arrive as one container, and the manifest has to show that.
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
            CLAUSES.append(
                {
                    "clause_id": f"{site}/{ordinal}/{i}",
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

# ---------------------------------------------------------------------------
# The direction the glossary entry itself prints
# ---------------------------------------------------------------------------
#
# The two sites are one population because the source joins them, not because a
# reader judges them related. The glossary entry's last two leaves are a bare
# "See also" and a citation naming the other site's chapter and subsection; the
# run asserts both, so a release in which the glossary entry stopped pointing at
# Combat would fail here rather than be silently carried.

_glossary_leaves = SOURCE_SITES[0]["leaves"]
SEE_ALSO = _glossary_leaves[-2]["content"]
CITATION = _glossary_leaves[-1]["content"]
assert SEE_ALSO == "See also", SEE_ALSO
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]] in CITATION, CITATION
assert LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]] in CITATION, CITATION

DIRECTION = {
    "from_site": "glossary",
    "see_also_leaf_id": _glossary_leaves[-2]["leaf_id"],
    "citation_leaf_id": _glossary_leaves[-1]["leaf_id"],
    "citation_text": CITATION,
    "names_section": LABELS[_ancestry(COMBAT_ENTRY.container_id)[2]],
    "names_subsection": LABELS[_ancestry(COMBAT_ENTRY.container_id)[1]],
    "to_site": "combat",
}

# ---------------------------------------------------------------------------
# The boundary: every other leaf that prints the word
# ---------------------------------------------------------------------------
#
# Enumerated, not summarized. The membership rule is structural — a leaf is in
# the population when the source attaches it to a container labeled ``Cover`` —
# so the honest way to show a mere occurrence does not pull a record in is to
# list every mere occurrence and the container that owns it.

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

# Which accepted records already own which source containers, derived from the
# frozen prior rather than transcribed: every accepted span names a leaf, every
# provenance claim names a span and a record key, and this release says which
# container owns that leaf. Composing the three maps container -> accepted keys,
# so "accepted authority already represents the citing entry" is read out of the
# prior instead of asserted about it.

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

BOUNDARY = [
    {
        "leaf_id": leaf.leaf_id,
        "page_index": leaf.page_index,
        "leaf_type": leaf.leaf_type,
        "container_label": LABELS[leaf.container_path[-1]],
        "container_path": _path_of(leaf.container_path[-1]),
        "section": LABELS[_ancestry(leaf.container_path[-1])[-1]],
        "represented_by_5c": leaf.leaf_id in REPRESENTED,
        "already_accepted_as": sorted(
            _PRIOR_KEYS_BY_CONTAINER.get(leaf.container_path[-1], ())
        ),
        "content": leaf.content,
    }
    for leaf in sorted(LEDGER_OBJ.leaves, key=lambda x: (x.page_index, x.char_start))
    if "Cover" in leaf.content and leaf.leaf_id not in MEMBER_LEAF_IDS
]
for _row in BOUNDARY:
    assert _row["container_label"] != "Cover", _row
    assert all(key in PRIOR_DEFINED for key in _row["already_accepted_as"]), _row

BOUNDARY_BY_SECTION: dict[str, int] = defaultdict(int)
for _row in BOUNDARY:
    BOUNDARY_BY_SECTION[_row["section"]] += 1

#: The case-insensitive figure too, disclosed rather than quietly narrowed: the
#: table above is the capitalized term, and the source also uses the lowercase
#: common noun inside the population's own prose and elsewhere.
LOWERCASE_ONLY_OCCURRENCES = sum(
    1
    for leaf in LEDGER_OBJ.leaves
    if "cover" in leaf.content.lower()
    and "Cover" not in leaf.content
    and leaf.leaf_id not in MEMBER_LEAF_IDS
)

# ---------------------------------------------------------------------------
# The printed table, as the frozen 5c oracle independently records it
# ---------------------------------------------------------------------------

_inventory = json.loads(TABLE_INVENTORY_PATH.read_text(encoding="utf-8"))
_table_ids = {
    row["owning_container_id"]
    for site in SOURCE_SITES
    for row in site["leaves"]
    if row["attached_to"] == "table"
}
TABLE_WITNESS = sorted(
    (
        {
            "logical_table_id": entry["logical_table_id"],
            "printed_pages": entry["printed_pages"],
            "header": entry["header"],
            "column_count": entry["column_count"],
            "logical_row_count": entry["logical_row_count"],
        }
        for entry in _inventory["tables"]
        if entry["logical_table_id"] in _table_ids
    ),
    key=lambda e: str(e["logical_table_id"]),
)
assert len(TABLE_WITNESS) == len(_table_ids) == 2, (TABLE_WITNESS, _table_ids)

#: Degree-row leaves the extraction attached to the entry rather than to either
#: table. Counted from the partition rather than narrated, because "the table is
#: fragmented" is exactly the kind of claim a checkpoint should be able to point
#: at a number for.
ENTRY_ATTACHED_BODY_LEAVES = [
    row["leaf_id"]
    for row in SOURCE_SITES[1]["leaves"]
    if row["attached_to"] == "entry" and row["leaf_type"] != "heading"
]

# ---------------------------------------------------------------------------
# Reference scope, enumerated without closing anything
# ---------------------------------------------------------------------------

#: **The schema this discovery ran against**, read off the frozen prior rather
#: than off the checkout, for the reason ``areas-of-effect-1``'s run records:
#: source discovery states nothing in typed facts, so the binding that belongs
#: in its manifest is the frozen one and not the one that moves with every mint.
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
#: Reported, not resolved: whether representing the population closes it is a
#: judgment the checkpoint makes and this run must not pre-empt.
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
        if ref.target_record_key == "glossary.cover"
    ),
    key=lambda r: (str(r["from_record_key"]), str(r["source_text"])),
)

#: The scope keys accepted authority has ever used for a reference. One, so far.
#: Whether a population that draws from ``Playing the Game`` needs a second is a
#: judgment; the fact that only one exists is not.
PRIOR_SCOPE_KEYS = sorted(
    {ref.scope_key for ref in PRIOR.oracle.representation.references}
)

#: A **substring scan**, reported as one. Every Rules Glossary entry label that
#: occurs anywhere in this population's clause text, with the clauses it occurs
#: in. It is deliberately not a citation list: the same rule that governs the
#: boundary governs here, and an occurrence is not a citation. What each
#: occurrence is — a citation, a column header, or ordinary use — is a judgment
#: the checkpoint makes from the clause text this table points at.
_GLOSSARY_ENTRY_LABELS = {
    c.label
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry"
    and any(LABELS[a] == "Rules Definitions" for a in _ancestry(c.container_id))
}
_CANDIDATE_TERMS = sorted(
    {
        term
        for clause in CLAUSES
        for term in _GLOSSARY_ENTRY_LABELS
        if " [" not in term and term != "Cover" and term in clause["text"]
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
    "batch_id": "cover-1",
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
            "Not independently derivable here: a function of persisted "
            "rp_sources rows and verified Chroma state. Taken from the "
            "published CRD Issue 5c release record and disclosed as such. The "
            "five values above are re-derived from the committed PDF by this "
            "run and asserted."
        ),
    },
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "representation_schema_note": (
        "The frozen review prior's binding, which this discovery ran against. "
        "The checkout's own representation schema is not recorded here: source "
        "discovery is independent of representation, and recording a value "
        "that moves with every schema mint would rot this manifest against "
        "evidence that had not moved. The run asserts separately that the "
        "checkout is that binding or a registered successor of it."
    ),
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
        "A leaf is in this population when the bound release attaches it to an "
        "entry container labeled 'Cover', directly or through a table beneath "
        "it. There is no tag to read, so membership is the structural claim the "
        "run asserts: exactly two such containers exist, one beneath 'Rules "
        "Definitions' and one beneath 'Combat', and the first directs to the "
        "second through its own printed See-also citation. Printing the word "
        "'Cover' is use, not definition, and pulls nothing in."
    ),
    "membership": {
        "entry_container_count": len(COVER_ENTRIES),
        "sites": [s["site"] for s in SOURCE_SITES],
        "leaf_count": sum(len(s["leaves"]) for s in SOURCE_SITES),
        "clause_count": len(CLAUSES),
        "policy_excluded": POLICY_EXCLUDED,
    },
    "direction": DIRECTION,
    "source_sites": SOURCE_SITES,
    "clauses": CLAUSES,
    "extraction_artifacts": {
        "note": (
            "Properties of the frozen 5c release, carried verbatim rather than "
            "repaired. No source-corpus change is proposed or made here."
        ),
        "printed_table_arrives_as_logical_tables": TABLE_WITNESS,
        "table_inventory_agrees": True,
        "degree_rows_attached_to_the_entry_not_a_table": ENTRY_ATTACHED_BODY_LEAVES,
        "fused_cells": [
            {
                "leaf_id": row["leaf_id"],
                "clause_ids": row["clause_ids"],
                "note": (
                    "Two printed columns arrive as one leaf; the partition cuts "
                    "at the printed column boundary without altering a byte."
                ),
            }
            for site in SOURCE_SITES
            for row in site["leaves"]
            if row["attached_to"] == "table" and len(row["clause_ids"]) > 1
        ],
        "degree_label_as_extracted": next(
            row["content"]
            for site in SOURCE_SITES
            for row in site["leaves"]
            if row["content"] == "ThreeQuarters"
        ),
        "degree_label_as_printed": "Three-Quarters",
        "caption_absorbed_into_prose_leaf": {
            "leaf_id": SOURCE_SITES[1]["leaves"][1]["leaf_id"],
            "clause_id": SOURCE_SITES[1]["leaves"][1]["clause_ids"][-1],
        },
    },
    "boundary_count": len(BOUNDARY),
    "boundary_by_section": dict(sorted(BOUNDARY_BY_SECTION.items())),
    "boundary_lowercase_only_leaf_count": LOWERCASE_ONLY_OCCURRENCES,
    "boundary": BOUNDARY,
    "inbound_citations": INBOUND_CITATIONS,
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

print(f"entry containers   {len(COVER_ENTRIES)}")
print(f"leaves             {sum(len(s['leaves']) for s in SOURCE_SITES)}")
print(f"clauses            {len(CLAUSES)}")
print(f"policy exclusions  {len(POLICY_EXCLUDED)}")
print(f"boundary leaves    {len(BOUNDARY)}")
print(f"boundary sections  {dict(sorted(BOUNDARY_BY_SECTION.items()))}")
print(f"logical tables     {[t['logical_table_id'] for t in TABLE_WITNESS]}")
print(f"inbound citations  {len(INBOUND_CITATIONS)}")
print(f"manifest sha256    {_lf_sha256(MANIFEST_PATH)}")
