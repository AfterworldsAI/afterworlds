"""Locate where reconstruct_candidate output differs from the in-memory
identified candidate (strict dataclass ==), per store. Diagnostic only.

Usage: reconstruct_diag.py CANDIDATE_JSON
"""

import dataclasses
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))
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
from afterworlds.ingestion.mechanical.projection import identify_projection  # noqa: E402
from afterworlds.persistence.database import create_engine, create_session_factory  # noqa: E402
from afterworlds.persistence.orm.base import Base  # noqa: E402

SP = REPO / ".claude/_sp/release-order-candidate"
LIVE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
CAND = Path(sys.argv[1])
diffs: Counter[str] = Counter()
samples: dict[str, tuple] = {}


def walk(a, b, path):
    if dataclasses.is_dataclass(a) and type(a) is type(b):
        for f in dataclasses.fields(a):
            walk(getattr(a, f.name), getattr(b, f.name), f"{path}.{f.name}")
    elif isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        if type(a) is not type(b):
            diffs[f"{path}: {type(a).__name__} vs {type(b).__name__}"] += 1
        if len(a) != len(b):
            diffs[f"{path}: len"] += 1
            samples.setdefault(f"{path}: len", (len(a), len(b)))
            return
        if a != b and sorted(map(repr, a)) == sorted(map(repr, b)):
            diffs[f"{path}: order only"] += 1
            samples.setdefault(f"{path}: order only", (repr(a)[:200], repr(b)[:200]))
            return
        for x, y in zip(a, b):
            walk(x, y, f"{path}[*]")
    elif a != b:
        key = f"{path}: {type(a).__name__} vs {type(b).__name__}"
        diffs[key] += 1
        samples.setdefault(key, (repr(a)[:200], repr(b)[:200]))


for tag, rel, src in (("old", "rel-old", LIVE), ("new", "rel-new", CAND)):
    diffs.clear()
    samples.clear()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "r.db"
        shutil.copyfile(SP / rel / "afterworlds.db", p)
        engine = create_engine(f"sqlite:///{p}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as s:
                identified = identify_projection(candidate_from_accepted_inputs(load_accepted_inputs(src)))
                persist_draft(s, identified, now="2026-10-06T00:00:00Z")
                s.commit()
                print(tag, "verify findings", verify_reconstruction(s, identified))
                rebuilt = reconstruct_candidate(s, identified.projection_uuid)
                print(tag, "strict ==", rebuilt == identified.candidate)
                walk(identified.candidate, rebuilt, "cand")
        finally:
            engine.dispose()
    print(tag, "difference patterns", len(diffs))
    for k, n in diffs.most_common():
        print(f"  {n:6d}  {k}")
        if k in samples:
            print("          identified:", samples[k][0])
            print("          rebuilt:   ", samples[k][1])
