"""CRD Issue 5d — batch `areas-of-effect-1`, **source-discovery run only**.

Reads the committed SRD through the 5c pipeline, re-derives the complete
``[Area of Effect]`` entry class from the source's own tag, cuts every
represented leaf of every member into an exact clause partition, and writes one
deterministic LF manifest. It builds no draft, proposes nothing, accepts
nothing, publishes nothing, lifts nothing, executes no schema change and
touches no database.

What this run establishes, and what it does not
-----------------------------------------------
It establishes three things a reviewer can re-derive:

1. **Membership**, from the tag rather than from a remembered count. The
   attitudes-1 selection checkpoint observed a seven-record candidate; that is
   an observation, and this run measures it.
2. **Exact coverage**, as ``leaf_id`` plus leaf-local half-open character
   ranges, with the partition asserted to reconstruct each leaf byte for byte.
   Every clause the checkpoint judges is addressable here.
3. **The unchanged accepted prior**, by two independent identities before and
   after the run, and the live accepted artifact as a mutation sentinel that is
   never an input.

It establishes nothing about representation. The schema-adequacy judgments live
in ``issue-5d-areas-of-effect-1-DISCOVERY-CHECKPOINT.md`` and cite the clause
ids this run emits; no disposition is encoded here, because a discovery run
that shipped its own conclusions would be proposing.

Clause cuts
-----------
A cut names the text a segment **ends with**; ``None`` means "to the end of the
leaf". Cuts are located in the bound leaf content at run time and fail loudly if
the source moved, so a re-extraction cannot silently re-cut a clause under a
judgment that was written about the old one. Separator runs are absorbed as the
*leading* text of the next segment, exactly as the accepted batch generators do,
so the partition reconstructs each leaf byte for byte.

The cuts are sentence-level except in three places, each for a stated reason:
the umbrella's three enumeration leaves are cut per member, because each member
is a distinct citation; the umbrella's definitional paragraph is cut before its
enumeration lead-in; and the "See also" leaf is cut after the cited term, which
is the only span that is a citation rather than the rule that follows it.
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
#: review: conditions-1, hazards-1, actions-1 and attitudes-1, representation
#: schema 8. Read only, by content identity, and asserted unchanged at the end.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json"
)

#: **A mutation sentinel, never an input.** Bytes captured before the run and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
MANIFEST_PATH = OUT / "issue-5d-areas-of-effect-1-source-manifest.json"

PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (SOURCE_PDF, REVIEW_PRIOR_PATH, LIVE_ORACLE_PATH, PACKAGE_ROOT):
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
REVIEW_PRIOR_CONTENT_SHA256 = "fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "2346404005618b0389b4e4f66d2e96c5c35b200f"  # pragma: allowlist secret
)
REVIEW_PRIOR_IDENTITY = "c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = ["actions-1", "attitudes-1", "conditions-1", "hazards-1"]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-8"

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
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import oracle_identity  # noqa: E402
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

import afterworlds  # noqa: E402  # isort: skip

IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == REVIEW_PRIOR_SCHEMA_VERSION, SCHEMA

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


RULES_DEFINITIONS = next(
    c.container_id for c in LEDGER_OBJ.containers if c.label == "Rules Definitions"
)
ENTRY_BY_LABEL = {
    c.label: c.container_id
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry" and RULES_DEFINITIONS in _ancestry(c.container_id)
}

by_container: dict[str, list[Any]] = defaultdict(list)
for _leaf in LEDGER_OBJ.leaves:
    for _cid in _leaf.container_path:
        by_container[_cid].append(_leaf)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

# ---------------------------------------------------------------------------
# Membership, re-derived from the source's own tag
# ---------------------------------------------------------------------------
#
# The five tag values the Rules Glossary's preamble names, counted rather than
# narrated, so a class that gained or lost an entry upstream fails this run.
TAG_CLASSES = {
    tag: sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(f" [{tag}]"))
    for tag in ("Action", "Area of Effect", "Attitude", "Condition", "Hazard")
}

UMBRELLA = "Area of Effect"
assert UMBRELLA in ENTRY_BY_LABEL, "the untagged umbrella entry is missing"
SHAPE_LABELS = TAG_CLASSES[UMBRELLA]
SHAPE_NAMES = [lab.split(" [")[0] for lab in SHAPE_LABELS]
BATCH_LABELS = [UMBRELLA, *SHAPE_LABELS]

#: Policy exclusions inside this boundary, **listed with their reasons** rather
#: than asserted away: a member that silently lost a body leaf would otherwise
#: look identical to one that lost a running header.
POLICY_EXCLUDED = [
    {
        "label": lab,
        "leaf_id": leaf.leaf_id,
        "page_index": leaf.page_index,
        "reason": exclusion_reason_for(leaf, LABELS),
        "content": leaf.content,
    }
    for lab in BATCH_LABELS
    for cid in [ENTRY_BY_LABEL[lab]]
    for leaf in by_container[cid]
    if leaf.leaf_id not in REPRESENTED
]

#: The umbrella's own enumeration leaves — "These shapes are defined elsewhere
#: in this glossary:" followed by a flattened two-column list. Cross-checked
#: against the tag-derived membership in both directions below.
ENUMERATION_LEAVES = ["Cone Cube", "Cylinder Emanation", "Line Sphere"]

# ---------------------------------------------------------------------------
# Clause cuts — the text each segment ends with, located at run time
# ---------------------------------------------------------------------------
#
# Keyed by leaf content rather than by leaf id so the table is readable against
# the source; the ids are resolved and emitted below.
RSQ = "’"  # right single quotation mark
LDQ, RDQ = "“", "”"  # double quotation marks
DASH = "—"  # em dash

CUTS: dict[str, list[str | None]] = {
    # --- umbrella -----------------------------------------------------------
    "Area of Effect": [None],
    (
        "The descriptions of many spells and other features specify that they "
        "have an area of effect, which typically has one of six shapes. These "
        "shapes are defined elsewhere in this glossary:"
    ): ["one of six shapes.", None],
    "Cone Cube": ["Cone", None],
    "Cylinder Emanation": ["Cylinder", None],
    "Line Sphere": ["Line", None],
    (
        f"An area of effect has a point of origin, a location from which the "
        f"effect{RSQ}s energy erupts. The rules for each shape specify how to "
        f"position its point of origin. If all straight lines extending from "
        f"the point of origin to a location in the area of effect are blocked, "
        f"that location isn{RSQ}t included in the area of effect. To block a "
        f"line, an obstruction must provide Total Cover."
    ): [
        f"the effect{RSQ}s energy erupts.",
        "how to position its point of origin.",
        f"isn{RSQ}t included in the area of effect.",
        None,
    ],
    "See also": [None],
    (
        f"{LDQ}Cover.{RDQ} If the creator of an area of effect places it at an "
        f"unseen point and an obstruction{DASH}such as a wall{DASH} is between "
        f"the creator and that point, the point of origin comes into being on "
        f"the near side of the obstruction."
    ): [f"{LDQ}Cover.{RDQ}", None],
    # --- Cone ---------------------------------------------------------------
    "Cone [Area of Effect]": [None],
    (
        f"A Cone is an area of effect that extends in straight lines from a "
        f"point of origin in a direction its creator chooses. A Cone{RSQ}s "
        f"width at any point along its length is equal to that point{RSQ}s "
        f"distance from the point of origin. For example, a Cone is 15 feet "
        f"wide at a point along its length that is 15 feet from the point of "
        f"origin. The effect that creates a Cone specifies its maximum length. "
        f"A Cone{RSQ}s point of origin isn{RSQ}t included in the area of "
        f"effect unless its creator decides otherwise."
    ): [
        "in a direction its creator chooses.",
        f"that point{RSQ}s distance from the point of origin.",
        "15 feet from the point of origin.",
        "specifies its maximum length.",
        None,
    ],
    # --- Cube ---------------------------------------------------------------
    "Cube [Area of Effect]": [None],
    (
        f"A Cube is an area of effect that extends in straight lines from a "
        f"point of origin located anywhere on a face of the Cube. The effect "
        f"that creates a Cube specifies its size, which is the length of each "
        f"side. A Cube{RSQ}s point of origin isn{RSQ}t included in the area of "
        f"effect unless its creator decides otherwise."
    ): [
        "located anywhere on a face of the Cube.",
        "which is the length of each side.",
        None,
    ],
    # --- Cylinder -----------------------------------------------------------
    "Cylinder [Area of Effect]": [None],
    (
        f"A Cylinder is an area of effect that extends in straight lines from "
        f"a point of origin located at the center of the circular top or "
        f"bottom of the Cylinder. The effect that creates a Cylinder specifies "
        f"the radius of the Cylinder{RSQ}s base and the Cylinder{RSQ}s height. "
        f"A Cylinder{RSQ}s point of origin is included in the area of effect."
    ): [
        "circular top or bottom of the Cylinder.",
        f"base and the Cylinder{RSQ}s height.",
        None,
    ],
    # --- Emanation ----------------------------------------------------------
    "Emanation [Area of Effect]": [None],
    (
        f"An Emanation is an area of effect that extends in straight lines "
        f"from a creature or an object in all directions. The effect that "
        f"creates an Emanation specifies the distance it extends. An Emanation "
        f"moves with the creature or object that is its origin unless it is an "
        f"instantaneous or a stationary effect. An Emanation{RSQ}s origin "
        f"(creature or object) isn{RSQ}t included in the area of effect unless "
        f"its creator decides otherwise."
    ): [
        "from a creature or an object in all directions.",
        "specifies the distance it extends.",
        "an instantaneous or a stationary effect.",
        None,
    ],
    # --- Line ---------------------------------------------------------------
    "Line [Area of Effect]": [None],
    (
        f"A Line is an area of effect that extends from a point of origin in a "
        f"straight path along its length and covers an area defined by its "
        f"width. The effect that creates a Line specifies its length and "
        f"width. A Line{RSQ}s point of origin isn{RSQ}t included in the area "
        f"of effect unless its creator decides otherwise."
    ): [
        "covers an area defined by its width.",
        "specifies its length and width.",
        None,
    ],
    # --- Sphere -------------------------------------------------------------
    "Sphere [Area of Effect]": [None],
    (
        f"A Sphere is an area of effect that extends in straight lines from a "
        f"point of origin outward in all directions. The effect that creates a "
        f"Sphere specifies the distance it extends as the radius of the "
        f"Sphere. A Sphere{RSQ}s point of origin is included in the Sphere"
        f"{RSQ}s area of effect."
    ): [
        "outward in all directions.",
        "the distance it extends as the radius of the Sphere.",
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
# Derive the record table
# ---------------------------------------------------------------------------

RECORDS: list[dict[str, Any]] = []
CLAUSES: list[dict[str, Any]] = []
seen_content: set[str] = set()

for label in BATCH_LABELS:
    container_id = ENTRY_BY_LABEL[label]
    leaves = [lf for lf in by_container[container_id] if lf.leaf_id in REPRESENTED]
    name = label.split(" [")[0]
    record_key = (
        "glossary.area_of_effect" if label == UMBRELLA else f"area_of_effect.{name.lower()}"
    )
    leaf_rows: list[dict[str, Any]] = []
    for ordinal, leaf in enumerate(leaves):
        assert leaf.content in CUTS, f"uncut leaf in the boundary: {leaf.content!r}"
        assert leaf.content not in seen_content, f"ambiguous cut key: {leaf.content!r}"
        seen_content.add(leaf.content)
        spans = _partition(leaf.content, CUTS[leaf.content])
        leaf_rows.append(
            {
                "leaf_id": leaf.leaf_id,
                "ordinal": ordinal,
                "page_index": leaf.page_index,
                "leaf_type": leaf.leaf_type,
                "length": len(leaf.content),
                "content": leaf.content,
                "clause_ids": [
                    f"{name}/{ordinal}/{i}" for i in range(len(spans))
                ],
            }
        )
        for i, (start, end) in enumerate(spans):
            CLAUSES.append(
                {
                    "clause_id": f"{name}/{ordinal}/{i}",
                    "record_key": record_key,
                    "label": label,
                    "leaf_id": leaf.leaf_id,
                    "page_index": leaf.page_index,
                    "char_start": start,
                    "char_end": end,
                    "text": leaf.content[start:end],
                }
            )
    RECORDS.append(
        {
            "label": label,
            "candidate_record_key": record_key,
            "container_id": container_id,
            "pages": sorted({lf["page_index"] for lf in leaf_rows}),
            "leaves": leaf_rows,
        }
    )

# ---------------------------------------------------------------------------
# Cross-checks: the umbrella and the tag must name the same six shapes
# ---------------------------------------------------------------------------

_umbrella_leaves = {lf["content"]: lf for lf in RECORDS[0]["leaves"]}
for _enum in ENUMERATION_LEAVES:
    assert _enum in _umbrella_leaves, f"the umbrella no longer prints {_enum!r}"
ENUMERATED = [
    clause["text"].strip()
    for clause in CLAUSES
    if clause["label"] == UMBRELLA
    and clause["leaf_id"] in {_umbrella_leaves[e]["leaf_id"] for e in ENUMERATION_LEAVES}
]
CROSS_CHECK = {
    "tag_derived": SHAPE_NAMES,
    "umbrella_enumerated": sorted(ENUMERATED),
    "agree": sorted(ENUMERATED) == sorted(SHAPE_NAMES),
    #: Each shape's body uses the umbrella's term definitionally; none of the
    #: six prints a "See also" leaf, so no back-citation is derivable here and
    #: none is asserted.
    "shapes_printing_a_see_also": [
        rec["label"]
        for rec in RECORDS[1:]
        if any(lf["content"] == "See also" for lf in rec["leaves"])
    ],
    "shape_bodies_naming_the_umbrella_term": [
        rec["label"]
        for rec in RECORDS[1:]
        if any("area of effect" in lf["content"] for lf in rec["leaves"])
    ],
}
assert CROSS_CHECK["agree"], CROSS_CHECK

# ---------------------------------------------------------------------------
# Reference targets, enumerated without closing any of them
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

#: Terms this boundary cites as **defined terms** — printed enumerations and the
#: "See also" list — separated from terms it merely uses. Nothing here is
#: resolved: a target is reported as present in the frozen prior, present as a
#: source entry this batch would define, or absent from both.
CITED_TERMS = {
    "Cone": "area_of_effect.cone",
    "Cube": "area_of_effect.cube",
    "Cylinder": "area_of_effect.cylinder",
    "Emanation": "area_of_effect.emanation",
    "Line": "area_of_effect.line",
    "Sphere": "area_of_effect.sphere",
    "Cover": "glossary.cover",
}
IN_BATCH_KEYS = {rec["candidate_record_key"] for rec in RECORDS}
REFERENCE_TARGETS = {
    term: {
        "candidate_target_key": key,
        "in_this_batch": key in IN_BATCH_KEYS,
        "in_frozen_prior": key in PRIOR_DEFINED,
        "source_entry_exists": any(
            lab == term or lab.startswith(f"{term} [") for lab in ENTRY_BY_LABEL
        ),
    }
    for term, key in CITED_TERMS.items()
}

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

MANIFEST = {
    "artifact_kind": "source_discovery_manifest",
    "batch_id": "areas-of-effect-1",
    "issue": "CRD Issue 5d (#137)",
    "generated_by": Path(__file__).name,
    "note": (
        "Discovery only. No draft, proposal, acceptance, lift, publication or "
        "schema change is produced by this run, and no disposition is encoded "
        "here; the checkpoint document carries the judgments and cites these "
        "clause ids."
    ),
    "input_paths": {
        "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
        "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
        "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
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
    "review_prior": {
        "path": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "content_sha256": REVIEW_PRIOR_CONTENT_SHA256,
        "blob": REVIEW_PRIOR_BLOB,
        "oracle_identity": REVIEW_PRIOR_IDENTITY,
        "batch_ids": REVIEW_PRIOR_BATCH_IDS,
        "record_keys": PRIOR_KEYS,
        "unresolved_targets": PRIOR_DANGLING,
    },
    "tag_class_sizes": {tag: len(labels) for tag, labels in TAG_CLASSES.items()},
    "tag_classes": TAG_CLASSES,
    "membership": {
        "umbrella": UMBRELLA,
        "tagged": SHAPE_LABELS,
        "record_count": len(RECORDS),
        "leaf_count": sum(len(rec["leaves"]) for rec in RECORDS),
        "clause_count": len(CLAUSES),
        "policy_excluded": POLICY_EXCLUDED,
    },
    "membership_cross_check": CROSS_CHECK,
    "records": RECORDS,
    "clauses": CLAUSES,
    "reference_targets": REFERENCE_TARGETS,
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

print(f"records            {len(RECORDS)}")
print(f"leaves             {sum(len(rec['leaves']) for rec in RECORDS)}")
print(f"clauses            {len(CLAUSES)}")
print(f"policy exclusions  {len(POLICY_EXCLUDED)}")
print(f"tag class sizes    {MANIFEST['tag_class_sizes']}")
print(f"cross-check        {CROSS_CHECK['agree']}")
print(f"manifest sha256    {_lf_sha256(MANIFEST_PATH)}")
