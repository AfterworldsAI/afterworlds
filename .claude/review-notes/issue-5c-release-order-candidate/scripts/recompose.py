"""Recompose the live oracle's native chain against the official-order release.

Usage: recompose.py CHAIN_PKL OUT_DIR

1. Control: re-execute the captured chain verbatim over no prior; the result
   must be the live oracle byte for byte (proves the capture is the chain).
2. Candidate: the same chain with every input mechanically rebound -- the
   six-coordinate ReleaseBinding old -> new (read back natively from each
   scratch store), every prose chunk_id old -> new through the leaf-keyed chunk
   maps -- and every reviewer/rule/authorization/timestamp replaced by
   clearly simulated values. No semantic input is edited. lift_to is kept.
3. Writes OUT_DIR/<live-name-for-new-release>.json, loads it back natively,
   reports counts, residual old identities and native findings against a temp
   copy of the new-order scratch store.
"""

import dataclasses
import hashlib
import json
import pickle
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
    published_release_binding,
)
from afterworlds.ingestion.mechanical.models import ReleaseBinding  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import validate_candidate  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)

SP = REPO / ".claude/_sp/release-order-candidate"
LIVE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
LIVE_SHA = "e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308"
SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_AT = "2026-10-06T00:00:00Z"
CHAIN, OUT = Path(sys.argv[1]), Path(sys.argv[2])
assert not OUT.exists()
assert hashlib.sha256(LIVE.read_bytes()).hexdigest() == LIVE_SHA


def store_binding(db: Path) -> ReleaseBinding:
    engine = create_engine(f"sqlite:///{db}")
    try:
        with create_session_factory(engine)() as s:
            return published_release_binding(s)
    finally:
        engine.dispose()


OLD = store_binding(SP / "rel-old/afterworlds.db")
NEW = store_binding(SP / "rel-new/afterworlds.db")
print("old binding", dataclasses.asdict(OLD))
print("new binding", dataclasses.asdict(NEW))


def chunks(rel: str) -> dict[str, str]:
    leaves = json.loads((SP / rel / "leaves.json").read_text("utf-8"))
    return {x["leaf_id"]: x["chunk"]["chunk_id"] for x in leaves}


old_c, new_c = chunks("rel-old"), chunks("rel-new")
assert old_c.keys() == new_c.keys()
CHUNK = {old_c[k]: new_c[k] for k in old_c}
assert len(CHUNK) == len(old_c) and not set(CHUNK) & set(CHUNK.values())

swapped: Counter[str] = Counter()


def rebind(x):
    if isinstance(x, ReleaseBinding):
        assert x == OLD, x
        swapped["release_binding"] += 1
        return NEW
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        changes = {}
        for f in dataclasses.fields(x):
            if not f.init:
                continue
            v = getattr(x, f.name)
            nv = rebind(v)
            if nv is not v:
                changes[f.name] = nv
        return dataclasses.replace(x, **changes) if changes else x
    if type(x) in (tuple, list):
        out = [rebind(v) for v in x]
        return x if all(a is b for a, b in zip(out, x)) else type(x)(out)
    if type(x) is dict:
        return {rebind(k): rebind(v) for k, v in x.items()}
    if type(x) is str and x in CHUNK:
        swapped["chunk_id"] += 1
        return CHUNK[x]
    return x


def run(steps, simulate: bool):
    inputs = None
    for n, (fn, proposal, kw) in enumerate(steps):
        kw = dict(kw)
        if simulate:
            kw = rebind(kw)
            if fn == "accept_proposal":
                proposal = rebind(proposal)
                kw.update(
                    reviewer=SIMULATED_REVIEWER,
                    accepted_at=SIMULATED_AT,
                    rule=f"SIMULATION ONLY: release-order replacement candidate, "
                    f"mechanical rebind of accepted batch {kw['batch_id']}; "
                    "not an Owner acceptance",
                )
            else:
                kw.update(
                    reviewer=SIMULATED_REVIEWER,
                    authorized_by=SIMULATED_REVIEWER,
                    resolved_at=SIMULATED_AT,
                    authorization_reference="SIMULATION ONLY: release-order "
                    f"replacement candidate, mechanical rebind of resolution step {n}; "
                    "not an Owner authorization",
                )
        if fn == "accept_proposal":
            inputs = accept_proposal(proposal, prior=inputs, **kw)
        else:
            inputs = resolve_references(inputs, **kw)
    return inputs


steps = pickle.loads(CHAIN.read_bytes())
print("chain", CHAIN, hashlib.sha256(CHAIN.read_bytes()).hexdigest(), "steps", len(steps))
control = serialize_accepted_inputs(run(steps, simulate=False))
print("control verbatim re-execution == live oracle", control == LIVE.read_bytes())
assert control == LIVE.read_bytes()

cand = run(steps, simulate=True)
print("rebound", dict(swapped))
data = serialize_accepted_inputs(cand)
OUT.mkdir(parents=True)
path = OUT / f"srd-5-2-1-corpus-{NEW.release_version.split('corpus.')[1]}.json"
path.write_bytes(data)
print("candidate", path, len(data), "bytes sha256", hashlib.sha256(data).hexdigest())
back = load_accepted_inputs(path)
print("load_accepted_inputs round trip bytes equal", serialize_accepted_inputs(back) == data)
assert serialize_accepted_inputs(back) == data
o = back.oracle
print("oracle binding == new", o.binding == NEW)
text = data.decode("utf-8")
for label, needle in [("old uuid", OLD.package_uuid), ("old version", OLD.release_version),
                      ("old transform", OLD.transform_config_hash),
                      ("old bundle", OLD.bundle_root_hash),
                      ("old digest", OLD.persisted_corpus_digest),
                      ("Owner name", "Ravenlok")]:
    print(f"residual {label}:", text.count(needle))
print("residual old chunk ids:", sum(text.count(c) for c in CHUNK))
print("new chunk ids present:", sum(1 for c in CHUNK.values() if c in text))


def findings(inputs, db: Path) -> list[str]:
    b = inputs.oracle.binding
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp) / "release.db"
        shutil.copyfile(db, t)
        engine = create_engine(f"sqlite:///{t}")
        try:
            with create_session_factory(engine)() as s:
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                return list(validate_candidate(candidate_from_accepted_inputs(inputs), corpus))
        finally:
            engine.dispose()


found = findings(back, SP / "rel-new/afterworlds.db")
refs = [f for f in found if f.startswith("reference ")]
leaves = [f for f in found if f.startswith("leaf ")]
print("native findings: reference", len(refs), "uncovered-leaf", len(leaves),
      "other", len(found) - len(refs) - len(leaves))
for f in found[:20]:
    print("  ", f)
assert not found
