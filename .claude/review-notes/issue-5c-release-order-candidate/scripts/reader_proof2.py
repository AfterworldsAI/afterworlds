"""Corrected reader, reconstruction and fail-closed proof (release-order candidate).

Usage: reader_proof2.py CANDIDATE_JSON OUT_JSON

Supersedes reader_proof.py (kept, with its attempt logs, as history). Reads a
small explicit record set through the unmodified production GameMaster view
(only binding resolution stood in), old oracle over a temp copy of the
old-order store and the candidate over a temp copy of the new-order store.

Comparison boundary: views are normalized (chunk id -> leaf id; package,
version and projection uuid -> placeholders; the release reading coordinate
``__occurrence__`` removed). Everything is then compared exactly and
positionally, except that each component's ``governing_prose`` sequence may
differ, and only as the two 14-file tuples dictate: the old sequence must be
in old file order, the new in new file order, and the new must equal the old
stably re-sorted by new file position (same passages, same within-file order).
"""

import dataclasses
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from uuid import UUID

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
from sqlalchemy import event  # noqa: E402

from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
    validate_candidate,
)
from afterworlds.models.rules_package import (  # noqa: E402
    RuleSliceRequest,
    RulesPackageBinding,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402
from afterworlds.services.rules_authority.application import SourceProse  # noqa: E402
from afterworlds.services.rules_authority.binding import BindingResolution  # noqa: E402
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome  # noqa: E402
from afterworlds.services.rules_authority.override_set import (  # noqa: E402
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import RulesAuthorityService  # noqa: E402

SP = REPO / ".claude/_sp/release-order-candidate"
LIVE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
CAND, OUT = Path(sys.argv[1]), Path(sys.argv[2])
assert not OUT.exists()
NOW = "2026-10-06T00:00:00Z"
ANIMALS = ("animals.wolf", "animals.giant_owl", "animals.swarm_of_insects")
MONSTERS = ("monsters.parts_of_a_stat_block", "monsters.aboleth.aboleth")
CONTROLS = (
    "character_origins.acolyte",
    "character_creation.level_advancement",  # route/destination-bearing
    "classes.barbarian.as_a_multiclass_character",
    "spells.casting_spells",
    "glossary.blinded",
    "equipment.adventuring_gear.acid",
    "magic_items.activating_a_magic_item",
    "feats.boon_of_spell_recall",  # route/destination-bearing
)
RECORDS = ANIMALS + MONSTERS + CONTROLS
results: dict = {"checks": {}}
ok = True


def check(label: str, cond: bool) -> None:
    global ok
    ok &= bool(cond)
    results["checks"][label] = bool(cond)
    print(label, bool(cond), flush=True)


def leafmap(rel: str) -> dict[str, dict]:
    leaves = json.loads((SP / rel / "leaves.json").read_text("utf-8"))
    return {x["chunk"]["chunk_id"]: x for x in leaves}


REL = {"old": ("rel-old", load_accepted_inputs(LIVE)), "new": ("rel-new", load_accepted_inputs(CAND))}
LEAF = {k: leafmap(v[0]) for k, v in REL.items()}
FILES = {k: json.loads((SP / v[0] / "identity.json").read_text("utf-8"))["corpus_files"]
         for k, v in REL.items()}
print("old files", FILES["old"])
print("new files", FILES["new"])
tmp = Path(tempfile.mkdtemp(prefix="release-order-proof-"))
engines: list = []


def copy(rel: str, name: str) -> Path:
    """Temp copy of an immutable scratch store, plus the 5d tables its
    5c-only build did not create (as the test conftest's create_all)."""
    p = tmp / name
    shutil.copyfile(SP / rel / "afterworlds.db", p)
    engine = create_engine(f"sqlite:///{p}")
    Base.metadata.create_all(engine)
    engine.dispose()
    return p


def session_for(db: Path):
    engine = create_engine(f"sqlite:///{db}")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _rec):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    engines.append(engine)
    return engine, create_session_factory(engine)()


# --------------------------------------------------------------------------
# Persist once per store; native reconstruction and verification
# --------------------------------------------------------------------------
services, sessions = {}, []
for tag, (rel, inputs) in REL.items():
    t0 = time.time()
    _, s = session_for(copy(rel, f"{tag}.db"))
    sessions.append(s)
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(s, identified, now=NOW)
    s.commit()
    findings = verify_reconstruction(s, identified)
    check(f"{tag}: verify_reconstruction reports no findings", findings == ())
    rebuilt = reconstruct_candidate(s, identified.projection_uuid)
    check(f"{tag}: reconstructed binding == persisted binding == oracle binding",
          rebuilt.binding == identified.candidate.binding == inputs.oracle.binding)
    check(f"{tag}: reconstructed candidate == identified candidate", rebuilt == identified.candidate)
    check(f"{tag}: reconstructed candidate re-identifies to the persisted projection",
          identify_projection(rebuilt).projection_uuid == identified.projection_uuid)
    results[f"{tag}_projection_uuid"] = identified.projection_uuid
    b = inputs.oracle.binding
    state = EffectiveOverrideSet(b.package_uuid, b.release_version, ())
    binding = RulesPackageBinding(
        package_uuid=UUID(b.package_uuid), release_version=b.release_version,
        mechanical_projection_uuid=UUID(identified.projection_uuid),
        override_set_uuid=UUID(state.override_set_uuid),
    )
    svc = RulesAuthorityService(s, now=NOW)
    svc.resolve = (lambda bd, st: (lambda **_: BindingResolution(  # binding resolution stood in
        AuthorityOutcome.RESOLVED, binding=bd, override_state=st)))(binding, state)
    services[tag] = (svc, b, identified.projection_uuid)
    print(f"{tag}: persisted/verified {identified.projection_uuid} in {time.time() - t0:.0f}s", flush=True)


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------
def norm(tag: str, x, b, proj):
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        d = {"__type__": type(x).__name__}
        for f in dataclasses.fields(x):
            d[f.name] = norm(tag, getattr(x, f.name), b, proj)
        if isinstance(x, SourceProse):
            leaf = LEAF[tag][x.chunk_id]
            d["chunk_id"] = "leaf:" + leaf["leaf_id"]
            d["__file__"] = FILES[tag][leaf["page_index"]]
            d["__occurrence__"] = leaf["occurrence_index"]
        return d
    if hasattr(x, "model_dump"):  # pydantic models, e.g. RulesPackageBinding
        d = {"__type__": type(x).__name__}
        d.update({k: norm(tag, getattr(x, k), b, proj) for k in type(x).model_fields})
        return d
    if isinstance(x, (tuple, list)):
        return [norm(tag, v, b, proj) for v in x]
    if isinstance(x, dict):
        return {str(norm(tag, k, b, proj)): norm(tag, v, b, proj) for k, v in x.items()}
    s = str(x) if isinstance(x, UUID) else x
    if isinstance(s, str):
        if s in LEAF[tag]:
            return "leaf:" + LEAF[tag][s]["leaf_id"]
        return {b.package_uuid: "<package>", b.release_version: "<version>", proj: "<projection>"}.get(s, s)
    return x


def view(tag: str, record: str):
    svc, b, proj = services[tag]
    v = svc.gamemaster_view(RuleSliceRequest(package_id=UUID(b.package_uuid), record_selectors=(record,)))
    assert v.outcome is AuthorityOutcome.RESOLVED, (tag, record, v.detail)
    return norm(tag, v.gamemaster_view, b, proj)


def ordered(seq: list[dict], tag: str) -> bool:
    """Sequence is in *tag*'s release reading order (file, then occurrence)."""
    keys = [e["__occurrence__"] for e in seq if "__occurrence__" in e]
    return keys == sorted(keys)


def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if k != "__occurrence__"}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x


def compare(a, b, path, moved: list) -> list[str]:
    """Exact positional comparison; governing_prose may differ only by file order."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k == "governing_prose" and isinstance(a.get(k), list) and isinstance(b.get(k), list):
                out += prose(a[k], b[k], f"{path}.{k}", moved)
            else:
                out += compare(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}.{k}", moved)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in compare(x, y, f"{path}[{i}]", moved)]
    return [] if a == b else [f"{path}: {str(a)[:120]!r} != {str(b)[:120]!r}"]


def prose(a: list, b: list, path: str, moved: list) -> list[str]:
    errs = []
    if not ordered(a, "old"):
        errs.append(f"{path}: old sequence not in old reading order")
    if not ordered(b, "new"):
        errs.append(f"{path}: new sequence not in new reading order")
    sa, sb = strip(a), strip(b)
    authored = [e for e in sa if "__file__" not in e]
    if authored:
        errs.append(f"{path}: authored prose present; not expected without overrides")
    expect = sorted(sa, key=lambda e: FILES["new"].index(e["__file__"]))  # stable
    if sa == sb:
        return errs
    if expect != sb:
        return errs + [f"{path}: new sequence is not the old re-sorted by the new file tuple"]
    moved.append({"path": path, "old_files": [e["__file__"] for e in sa],
                  "new_files": [e["__file__"] for e in sb]})
    return errs


reads: dict = {}
t0 = time.time()
for record in RECORDS:
    a, b = view("old", record), view("new", record)
    moved: list = []
    errs = compare(a, b, "$", moved)
    comps = [(c["record_key"] + "/" + c["component_key"], [e["__file__"] for e in c["governing_prose"] if "__file__" in e])
             for c in b["components"]]
    reads[record] = {"differences": errs, "reordered_components": moved,
                     "components": len(b["components"]),
                     "passages": sum(len(f) for _, f in comps),
                     "new_component_files": comps}
    print(f"{record}: components {len(b['components'])} passages {reads[record]['passages']} "
          f"reordered {len(moved)} differences {len(errs)}", flush=True)
    for e in errs[:5]:
        print("   ", e)
    check(f"{record}: identical apart from release-ordered governing prose", not errs)
    check(f"{record}: has governing prose to compare", reads[record]["passages"] > 0)
print(f"read {len(RECORDS)} records x2 in {time.time() - t0:.0f}s", flush=True)
results["reads"] = reads

monster_files = {"monsters.md", "monsters-A-Z.md"}
for record in ANIMALS:
    mixed = [m for m in reads[record]["reordered_components"]
             if "animals.md" in m["old_files"] and monster_files & set(m["old_files"])]
    check(f"{record}: at least one component reads both own Animals text and governing Monsters rules",
          bool(mixed))
    check(f"{record}: old release read own Animals text before the governing Monsters rules",
          bool(mixed) and all(m["old_files"][0] == "animals.md" for m in mixed))
    check(f"{record}: new release reads the governing Monsters rules before own Animals text",
          bool(mixed) and all(m["new_files"][0] in monster_files and m["new_files"][-1] == "animals.md"
                              for m in mixed))
for record in MONSTERS + CONTROLS:
    check(f"{record}: no component reordered (single-file or unchanged relative order)",
          not reads[record]["reordered_components"])

for s in sessions:
    s.close()
services.clear()


# --------------------------------------------------------------------------
# Fail closed
# --------------------------------------------------------------------------
def outcome(fn) -> str:
    try:
        return "ok: " + fn()
    except Exception as e:  # noqa: BLE001 - recording the refusal is the point
        return f"refused {type(e).__name__}: {str(e)[:240]}"


def bound(db: Path, inputs) -> str:
    engine, s = session_for(db)
    try:
        b = inputs.oracle.binding
        corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
        found = list(validate_candidate(candidate_from_accepted_inputs(inputs), corpus))
        if found:
            raise ValueError(f"{len(found)} findings, e.g. {found[0]}")
        return "0 findings"
    finally:
        s.close()


def persisted_into(db: Path, inputs) -> str:
    engine, s = session_for(db)
    try:
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(s, identified, now=NOW)
        s.commit()
        found = verify_reconstruction(s, identified)
        if found:
            raise ValueError(f"{len(found)} reconstruction findings, e.g. {found[0]}")
        return "persisted and verified"
    finally:
        s.close()


def swapped(src: Path, frm, to, name: str) -> Path:
    text = src.read_text("utf-8")
    for f in ("package_uuid", "release_version", "transform_config_hash",
              "bundle_root_hash", "persisted_corpus_digest"):
        text = text.replace(getattr(frm, f), getattr(to, f))
    p = tmp / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def loaded(path: Path):
    return load_accepted_inputs(path)


OB, NB = REL["old"][1].oracle.binding, REL["new"][1].oracle.binding
mixed_a = swapped(LIVE, OB, NB, "mixed-new-binding-old-chunks.json")
mixed_b = swapped(CAND, NB, OB, "mixed-old-binding-new-chunks.json")
cases = [
    ("control: live oracle validates on old store", "ok", lambda: bound(copy("rel-old", "c1.db"), REL["old"][1])),
    ("control: candidate validates on new store", "ok", lambda: bound(copy("rel-new", "c2.db"), REL["new"][1])),
    ("candidate (new binding) on old store", "refused", lambda: bound(copy("rel-old", "f1.db"), REL["new"][1])),
    ("live oracle (old binding) on new store", "refused", lambda: bound(copy("rel-new", "f2.db"), REL["old"][1])),
    ("persist candidate into old store", "refused", lambda: persisted_into(copy("rel-old", "f3.db"), REL["new"][1])),
    ("persist live oracle into new store", "refused", lambda: persisted_into(copy("rel-new", "f4.db"), REL["old"][1])),
    ("mixed: new binding + old chunk ids, on new store", "refused",
     lambda: bound(copy("rel-new", "f5.db"), loaded(mixed_a))),
    ("mixed: old binding + new chunk ids, on old store", "refused",
     lambda: bound(copy("rel-old", "f6.db"), loaded(mixed_b))),
]
results["fail_closed"] = {}
for label, want, fn in cases:
    got = outcome(fn)
    results["fail_closed"][label] = got
    print(f"{label}: {got}", flush=True)
    check(f"{label}: expected {want}", got.startswith(want))

for e in engines:
    e.dispose()
shutil.rmtree(tmp)
results.update({
    "candidate": {"path": str(CAND), "sha256": hashlib.sha256(CAND.read_bytes()).hexdigest()},
    "live": {"path": str(LIVE.relative_to(REPO)), "sha256": hashlib.sha256(LIVE.read_bytes()).hexdigest()},
    "records": list(RECORDS),
    "all_ok": ok,
})
OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("report", OUT, hashlib.sha256(OUT.read_bytes()).hexdigest())
print("ALL OK", ok)
raise SystemExit(0 if ok else 1)
