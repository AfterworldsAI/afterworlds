"""Reader and fail-closed proof for the release-order candidate.

Usage: reader_proof.py CANDIDATE_JSON OUT_JSON

Persists the live oracle into a temp copy of the old-order store and the
candidate into a temp copy of the new-order store (immutable sources), then
reads every accepted record through the production RulesAuthorityService
GameMaster view (binding resolution stood in, as the existing reader tests do).
Each record's view is normalized (chunk ids -> leaf ids, package uuid/version
-> placeholders) and compared old/new. Also proves old, new and mixed bindings
fail closed against the wrong store.
"""

import dataclasses
import hashlib
import json
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from uuid import UUID

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft  # noqa: E402
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
    validate_candidate,
)
from sqlalchemy import event  # noqa: E402

from afterworlds.persistence.orm.base import Base  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.services.rules_authority.application import SourceProse  # noqa: E402
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome  # noqa: E402
from afterworlds.models.rules_package import (  # noqa: E402
    RuleSliceRequest,
    RulesPackageBinding,
)
from afterworlds.services.rules_authority.binding import BindingResolution  # noqa: E402
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
ok = True


def check(label: str, cond: bool) -> None:
    global ok
    ok &= bool(cond)
    print(label, bool(cond))


def leafmap(rel: str) -> dict[str, dict]:
    leaves = json.loads((SP / rel / "leaves.json").read_text("utf-8"))
    return {x["chunk"]["chunk_id"]: x for x in leaves}


REL = {"old": ("rel-old", load_accepted_inputs(LIVE)), "new": ("rel-new", load_accepted_inputs(CAND))}
LEAF = {k: leafmap(v[0]) for k, v in REL.items()}
FILES = {k: json.loads((SP / v[0] / "identity.json").read_text("utf-8"))["corpus_files"]
         for k, v in REL.items()}
tmp = Path(tempfile.mkdtemp(prefix="release-order-reader-"))


def copy(rel: str, name: str) -> Path:
    """A temp copy of an immutable scratch store, with the 5d tables the
    store's 5c-only build did not create (as the test conftest's create_all)."""
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

    return engine, create_session_factory(engine)()


# --------------------------------------------------------------------------
# Persist and read
# --------------------------------------------------------------------------
services, keys = {}, {}
for tag, (rel, inputs) in REL.items():
    t0 = time.time()
    engine, s = session_for(copy(rel, f"{tag}.db"))
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    persist_draft(s, identified, now=NOW)
    s.commit()
    b = inputs.oracle.binding
    state = EffectiveOverrideSet(b.package_uuid, b.release_version, ())
    binding = RulesPackageBinding(
        package_uuid=UUID(b.package_uuid), release_version=b.release_version,
        mechanical_projection_uuid=UUID(identified.projection_uuid),
        override_set_uuid=UUID(state.override_set_uuid),
    )
    svc = RulesAuthorityService(s, now=NOW)
    svc.resolve = (lambda bd, st: (lambda **_: BindingResolution(
        AuthorityOutcome.RESOLVED, binding=bd, override_state=st)))(binding, state)
    services[tag] = (svc, b, identified.projection_uuid)
    keys[tag] = [r.semantic_key for r in inputs.oracle.representation.records]
    print(f"persisted {tag} projection {identified.projection_uuid} in {time.time() - t0:.0f}s")
check("same record keys in the same order", keys["old"] == keys["new"])


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
    if hasattr(x, "model_dump"):  # pydantic models (e.g. RulesPackageBinding)
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


def strip_reading(x):
    """Drop release reading coordinates and sort prose; what remains is semantic."""
    if isinstance(x, dict):
        y = {k: strip_reading(v) for k, v in x.items() if k not in ("__occurrence__",)}
        if "governing_prose" in y:
            y["governing_prose"] = sorted(y["governing_prose"], key=lambda e: json.dumps(e, sort_keys=True))
        return y
    if isinstance(x, list):
        return [strip_reading(v) for v in x]
    return x


def first_diff(a, b, path) -> str:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                return first_diff(a.get(k), b.get(k), f"{path}.{k}")
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return first_diff(x, y, f"{path}[{i}]")
    return f"{path}: {json.dumps(a, ensure_ascii=False)[:250]} != {json.dumps(b, ensure_ascii=False)[:250]}"


def prose_runs(v) -> list[list[tuple[str, str]]]:
    return [[(e.get("__file__", "<authored>"), e["text"]) for e in c["governing_prose"]]
            for c in v["components"]]


t0 = time.time()
if len(sys.argv) > 3:  # diagnostic subset; never the proof run
    keys["old"] = sys.argv[3].split(",")
summary: Counter[str] = Counter()
reordered: dict[str, list] = {}
for record in keys["old"]:
    a, b = view("old", record), view("new", record)
    if a == b:
        summary["identical"] += 1
        continue
    if strip_reading(a) != strip_reading(b):
        summary["SEMANTIC DIFFERENCE"] += 1
        print("SEMANTIC DIFFERENCE", record, first_diff(strip_reading(a), strip_reading(b), "")[:600])
        continue
    # Same content; only prose order differs. Each release must read each
    # component's prose in its own file order, with within-file order intact.
    fine = True
    for ra, rb in zip(prose_runs(a), prose_runs(b)):
        for runs, tag in ((ra, "old"), (rb, "new")):
            idx = [FILES[tag].index(f) for f, _ in runs]
            fine &= idx == sorted(idx)
        fine &= sorted(ra) == sorted(rb)
        for f in {f for f, _ in ra}:
            fine &= [t for g, t in ra if g == f] == [t for g, t in rb if g == f]
    files = sorted({f for r in prose_runs(b) for f, _ in r})
    summary["prose order only" if fine else "UNEXPLAINED ORDER"] += 1
    reordered[record] = files
    if not fine:
        print("UNEXPLAINED ORDER", record)
print(f"read {len(keys['old'])} records x2 in {time.time() - t0:.0f}s:", dict(summary))
pairs = Counter(tuple(v) for v in reordered.values())
print("reordered records by files read:", {" + ".join(k): n for k, n in pairs.items()})
check("no semantic difference in any read", not summary["SEMANTIC DIFFERENCE"])
check("every order difference is a file-order difference", not summary["UNEXPLAINED ORDER"])
moved = {"animals.md", "monsters.md", "monsters-A-Z.md"}
check("every reordered record reads Animals with a Monsters file",
      all("animals.md" in f and set(f) & (moved - {"animals.md"}) for f in reordered.values()))

# Animals: governing Monsters rules now precede the animal's own text.
for record in ANIMALS:
    a, b = view("old", record), view("new", record)
    for tag, v, first in (("old", a, "animals.md"), ("new", b, None)):
        for run in prose_runs(v):
            fs = [f for f, _ in run]
            if "animals.md" in fs and len(set(fs)) > 1:
                if tag == "old":
                    check(f"old {record}: own Animals text before governing Monsters rules",
                          fs[0] == "animals.md")
                else:
                    check(f"new {record}: governing Monsters rules before own Animals text",
                          fs[-1] == "animals.md" and fs[0] != "animals.md")
    check(f"{record} same texts both releases",
          sorted(t for r in prose_runs(a) for _, t in r) == sorted(t for r in prose_runs(b) for _, t in r))
for record in MONSTERS:
    check(f"monsters direct read identical {record}", record not in reordered)
controls = [k for k in keys["old"] if k.split(".")[0] in
            {"spells", "rules_glossary", "classes", "equipment", "feats", "magic_items"}]
check(f"cross-file controls identical ({len(controls)} records)", not set(controls) & set(reordered))
routes = {r.from_record_key for r in REL["new"][1].oracle.reference_resolutions}
print("resolution-bearing records:", len(routes), "identical", len(routes - set(reordered)),
      "file-order-only", len(routes & set(reordered)))


# --------------------------------------------------------------------------
# Fail closed
# --------------------------------------------------------------------------
def outcome(fn) -> str:
    try:
        r = fn()
    except Exception as e:  # noqa: BLE001 - recording the refusal is the point
        return f"refused {type(e).__name__}: {str(e)[:200]}"
    return f"ACCEPTED {r!r}"[:300]


def bound(db: Path, inputs):
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
        engine.dispose()


def persisted_into(db: Path, inputs):
    engine, s = session_for(db)
    try:
        persist_draft(s, identify_projection(candidate_from_accepted_inputs(inputs)), now=NOW)
        s.commit()
        return "persisted"
    finally:
        s.close()
        engine.dispose()


def swapped(src: Path, frm, to, name: str) -> Path:
    text = src.read_text("utf-8")
    for f in ("package_uuid", "release_version", "transform_config_hash",
              "bundle_root_hash", "persisted_corpus_digest"):
        text = text.replace(getattr(frm, f), getattr(to, f))
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p


OB, NB = REL["old"][1].oracle.binding, REL["new"][1].oracle.binding
fails = {}
fails["control: live oracle on old store"] = outcome(lambda: bound(copy("rel-old", "c1.db"), REL["old"][1]))
fails["control: candidate on new store"] = outcome(lambda: bound(copy("rel-new", "c2.db"), REL["new"][1]))
fails["candidate (new binding) on old store"] = outcome(lambda: bound(copy("rel-old", "f1.db"), REL["new"][1]))
fails["live oracle (old binding) on new store"] = outcome(lambda: bound(copy("rel-new", "f2.db"), REL["old"][1]))
fails["persist candidate into old store"] = outcome(lambda: persisted_into(copy("rel-old", "f3.db"), REL["new"][1]))
fails["persist live oracle into new store"] = outcome(lambda: persisted_into(copy("rel-new", "f4.db"), REL["old"][1]))
mixed_a = swapped(LIVE, OB, NB, "mixed-new-binding-old-chunks.json")
mixed_b = swapped(CAND, NB, OB, "mixed-old-binding-new-chunks.json")
fails["mixed: new binding + old chunk ids, on new store"] = outcome(
    lambda: bound(copy("rel-new", "f5.db"), load_accepted_inputs(mixed_a)))
fails["mixed: old binding + new chunk ids, on old store"] = outcome(
    lambda: bound(copy("rel-old", "f6.db"), load_accepted_inputs(mixed_b)))
for k, v in fails.items():
    print(f"{k}: {v}")
    want = "0 findings" if k.startswith("control") else "refused"
    check(f"  expected {want}", v.startswith(f"ACCEPTED '{want}'") if want == "0 findings" else v.startswith("refused"))

OUT.write_text(json.dumps({
    "candidate": {"path": str(CAND), "sha256": hashlib.sha256(CAND.read_bytes()).hexdigest()},
    "live": {"path": str(LIVE), "sha256": hashlib.sha256(LIVE.read_bytes()).hexdigest()},
    "read_summary": dict(summary),
    "reordered_records": reordered,
    "fail_closed": fails,
    "all_ok": ok,
}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
shutil.rmtree(tmp, ignore_errors=True)
print("ALL OK", ok)
raise SystemExit(0 if ok else 1)
