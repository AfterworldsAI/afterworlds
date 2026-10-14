"""Shared pins and helpers for the CRD Issue 15c native preview (review-only).

Nothing here writes outside this directory or a private temporary copy of the
isolated release store. Every pinned input is digest-checked on use.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
NOTES = NATIVE.parent
REPO = NOTES.parent.parent
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.models import ReleaseBinding  # noqa: E402
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)

ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
G1_PATH = ORACLES / "srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
G1_SHA256 = "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"
PREDECESSOR_PATH = ORACLES / "srd-5-2-1-corpus-8781d4e0-a3b.json"
PREDECESSOR_SHA256 = "def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c"
#: The prior release's committed authority: source of the old chunk ids.
OLD_RELEASE_PATH = ORACLES / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
OLD_RELEASE_SHA256 = "e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308"
#: The isolated release store; only ever copied, never opened in place.
G1_WORK = REPO.parent / "g1-work" / "rel"
STORE = G1_WORK / "afterworlds.db"
STORE_SHA256 = "9b427fff4d9ceebeff9ebe03f3d1d788cdb7ae1cb717786b48cb47c272e8c6f9"
LEAVES = G1_WORK / "leaves.json"

C5 = NOTES / "issue-15c-implementation" / "candidate-c5"
C5_SHA256 = {
    "c5a.json": "866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9",
    "c5b.json": "187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6",
    "c5c.json": "bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4",
    "capability.json": "6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6",
}

#: The eleven affected batches (C5 transition.json) and the retained proposal
#: each was last recorded from. Ten are old-release files, mechanically rebound
#: below exactly as the release-order recording did; Equipment is the G1
#: proposal, already at this release.
AFFECTED: dict[str, str] = {
    "animals": "issue-5d-animals-part-catalogue-PROPOSAL.json",
    "character-origins-feats": "issue-5d-character-origins-feats-finite-reference-atoms-PROPOSAL.json",
    "checks-actions-rests": "issue-5d-checks-actions-rests-remaining-references-PROPOSAL.json",
    "classes": "issue-5d-classes-finite-reference-atoms-PROPOSAL.json",
    "combat-damage-breaking": "issue-5d-combat-damage-breaking-finite-reference-routes-PROPOSAL.json",
    "core-play-completion": "issue-5d-core-play-completion-remaining-references-PROPOSAL.json",
    "equipment": "issue-2b-g1-candidate/candidate/issue-2b-g1-equipment-PROPOSAL.json",
    "magic-items": "issue-5d-magic-items-finite-reference-atoms-PROPOSAL.json",
    "monsters": "issue-5d-monsters-playing-the-game-atoms-PROPOSAL.json",
    "spell-descriptions": "issue-5d-spell-descriptions-finite-reference-atoms-PROPOSAL.json",
    "spellcasting": "issue-5d-spellcasting-remaining-references-PROPOSAL.json",
}

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_AT = "2026-10-12T00:00:00Z"
SIMULATED_RULE = ("SIMULATION ONLY - CRD Issue 15c native preview; not an Owner acceptance "
                  "or authorization")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, f"pinned input changed: {path}"
    return data


def g1() -> dict[str, Any]:
    return json.loads(pinned(G1_PATH, G1_SHA256))


def anchors() -> dict[str, dict[str, str]]:
    return {a["batch_id"]: a for a in g1()["acceptance"]["schema_anchors"]}


def chunk_map() -> dict[str, str]:
    """Old-release chunk id -> this release's, keyed by leaf.

    Span and leaf identities are equal across the two releases (only chunk ids
    and the binding differ); the old chunk of a leaf is read from the old
    release's accepted prose bindings, the new one from the isolated store's
    leaf export.
    """
    old = json.loads(pinned(OLD_RELEASE_PATH, OLD_RELEASE_SHA256))
    span_leaf = {s["span_id"]: s["leaf_id"] for s in old["spans"]}
    old_leaf_chunk: dict[str, str] = {}
    for pb in old["representation"]["prose_bindings"]:
        leaf = span_leaf[pb["span_id"]]
        assert old_leaf_chunk.setdefault(leaf, pb["chunk_id"]) == pb["chunk_id"], leaf
    new_leaf_chunk = {x["leaf_id"]: x["chunk"]["chunk_id"]
                      for x in json.loads(LEAVES.read_text("utf-8"))}
    out = {c: new_leaf_chunk[leaf] for leaf, c in old_leaf_chunk.items()}
    assert len(set(out.values())) == len(out)
    return out


def bindings() -> tuple[ReleaseBinding, ReleaseBinding]:
    old = json.loads(pinned(OLD_RELEASE_PATH, OLD_RELEASE_SHA256))["release_binding"]
    new = g1()["release_binding"]
    return ReleaseBinding(**old), ReleaseBinding(**new)


def rebind(x: Any, old: ReleaseBinding, new: ReleaseBinding, chunks: dict[str, str],
           seen: dict[str, int]) -> Any:
    """The release-order recording's mechanical rebind (recompose.py), verbatim
    in effect: the binding and chunk ids only; no semantic input changes."""
    if isinstance(x, ReleaseBinding):
        assert x == old, x
        seen["binding"] = seen.get("binding", 0) + 1
        return new
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        changes = {}
        for f in dataclasses.fields(x):
            if not f.init:
                continue
            v = getattr(x, f.name)
            nv = rebind(v, old, new, chunks, seen)
            if nv is not v:
                changes[f.name] = nv
        return dataclasses.replace(x, **changes) if changes else x
    if type(x) in (tuple, list):
        out = [rebind(v, old, new, chunks, seen) for v in x]
        return x if all(a is b for a, b in zip(out, x, strict=True)) else type(x)(out)
    if type(x) is dict:
        return {rebind(k, old, new, chunks, seen): rebind(v, old, new, chunks, seen)
                for k, v in x.items()}
    if type(x) is str and x in chunks:
        seen["chunk_id"] = seen.get("chunk_id", 0) + 1
        return chunks[x]
    return x


def replayed(batch: str) -> MechanicalProposal:
    """The batch's accepted proposal at this release, identity-matched to the
    accepted G1 anchor before any use."""
    proposal = load_proposal(NOTES / AFFECTED[batch])
    if batch != "equipment":
        old, new = bindings()
        proposal = rebind(proposal, old, new, chunk_map(), {})
    ident = proposal_identity(proposal)
    assert ident == anchors()[batch]["proposal_identity"], (batch, ident)
    return proposal


@contextlib.contextmanager
def private_store() -> Iterator[Path]:
    """A new private copy of the isolated store in a temporary directory.

    The original is never opened: its digest is asserted before the copy and
    again after the copy is discarded.
    """
    assert sha(STORE) == STORE_SHA256, "isolated store changed"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "afterworlds.db"
        shutil.copyfile(STORE, copy)
        try:
            yield copy
        finally:
            pass
    assert sha(STORE) == STORE_SHA256, "isolated store changed"


def leaf_texts() -> dict[str, str]:
    """Leaf content of this release, read from a private store copy."""
    package = g1()["release_binding"]["package_uuid"]
    with private_store() as db:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "select leaf_id, content from rp_ledger_leaves where package_uuid = ?",
                (package,),
            ).fetchall()
        finally:
            con.close()
    return dict(rows)


SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
_LINES: dict[str, list[str]] = {}


def lines(file: str) -> list[str]:
    """The pinned SRD markdown source the candidates cite, by physical line."""
    if file not in _LINES:
        _LINES[file] = (SRC / file).read_text("utf-8").splitlines()
    return _LINES[file]
