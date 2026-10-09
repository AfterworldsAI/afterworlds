"""Record the Owner-accepted release-order replacement natively (CRD Issue 5c).

Usage (cwd = repository root):

    RECORD.py --simulate   reproduce the live oracle and the accepted candidate
                           byte for byte from the captured chain; writes nothing
    RECORD.py --record     replay the chain with fresh Owner evidence, prove it
                           differs from the accepted candidate only in approval
                           evidence, then write the new oracle once
    RECORD.py --verify     replay at the pinned recording time and require the
                           committed bytes and their SHA-256

The chain is the reviewed capture (``live-chain.pkl``, 24 ``accept_proposal`` +
19 ``resolve_references``). Its inputs are rebound to the official-order release
exactly as the reviewed ``recompose.py`` does (six-coordinate binding, leaf-keyed
chunk ids); only the evidence keyword arguments change. Nothing here rewrites
JSON: every byte comes from ``serialize_accepted_inputs``.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import pickle
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

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
    AcceptedInputs,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    validate_candidate,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)

NOTES = REPO / ".claude/review-notes"
HERE = NOTES / "issue-5c-release-order-recording"
SP = REPO / ".claude/_sp/release-order-candidate"
CHAIN = NOTES / "issue-5c-release-order-candidate/chain/live-chain.pkl"
CANDIDATE = NOTES / (
    "issue-5c-release-order-candidate/candidate/srd-5-2-1-corpus-8781d4e0-a3b.json"
)
RECEIPT = HERE / "owner-acceptance.json"
CODEX_REVIEW = NOTES / "issue-5c-release-order-candidate-codex-review.md"
PACKET = NOTES / "issue-5c-release-order-candidate.md"
PRIOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
TARGET = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b.json"

PINS = {
    CHAIN: "b5d82c71c6b42d3eb4d7b114f7f2c98dcbcaa986db65168925af0315efa72a0e",
    CANDIDATE: "8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf",
    RECEIPT: "efe48d9b3f5c7f33591763ed823a2938519d276c2e5d6e3776ac22be6d4cd5e3",
    CODEX_REVIEW: "51e826b75fe02a2a77c2e02d55a0163cc1da6ce73ce3e8e58150c60ba75b1820",
    PACKET: "ec044533f73475ec0f7474aea1707c62fce3a686e12d03db08ab6e14baaff4ce",
    PRIOR: "e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308",
}
OWNER = "Ravenlok (Owner)"
STATEMENT = "I accept this exact release-order candidate."
RECEIPT_AT = "2026-10-07T05:28:37Z"
SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_AT = "2026-10-06T00:00:00Z"
#: The only payload keys allowed to differ from the accepted candidate.
EVIDENCE = frozenset(
    {
        "reviewer",
        "accepted_at",
        "rule",
        "authorized_by",
        "authorization_reference",
        "resolved_at",
    }
)
#: Pinned from the --record run's printed, read-back values.
RECORDED_AT: str | None = "2026-10-07T05:39:49Z"
RECORDED_SHA256: str | None = (
    "def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c"
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_pins() -> None:
    for p, want in PINS.items():
        got = sha(p)
        print(f"pin {got == want} {got}  {p.relative_to(REPO).as_posix()}")
        assert got == want, p


def store_binding(db: Path) -> ReleaseBinding:
    engine = create_engine(f"sqlite:///{db}")
    try:
        with create_session_factory(engine)() as s:
            return published_release_binding(s)
    finally:
        engine.dispose()


OLD = store_binding(SP / "rel-old/afterworlds.db")
NEW = store_binding(SP / "rel-new/afterworlds.db")
_receipt = json.loads(RECEIPT.read_text("utf-8"))
assert dataclasses.asdict(NEW) == _receipt["binding"], "store != receipt binding"
assert _receipt["exact_user_message"] == STATEMENT and _receipt["owner"] == OWNER


def _chunks(rel: str) -> dict[str, str]:
    leaves = json.loads((SP / rel / "leaves.json").read_text("utf-8"))
    return {x["leaf_id"]: x["chunk"]["chunk_id"] for x in leaves}


_old_c, _new_c = _chunks("rel-old"), _chunks("rel-new")
assert _old_c.keys() == _new_c.keys()
CHUNK = {_old_c[k]: _new_c[k] for k in _old_c}
assert len(CHUNK) == len(_old_c) and not set(CHUNK) & set(CHUNK.values())
swapped: Counter[str] = Counter()


def rebind(x: Any) -> Any:
    """Same mechanical rebind as the reviewed recompose.py (sha 76e5b798)."""
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
        return x if all(a is b for a, b in zip(out, x, strict=True)) else type(x)(out)
    if type(x) is dict:
        return {rebind(k): rebind(v) for k, v in x.items()}
    if type(x) is str and x in CHUNK:
        swapped["chunk_id"] += 1
        return CHUNK[x]
    return x


def _decision(at: str) -> str:
    return (
        f"Owner exact acceptance, {OWNER}: {STATEMENT!r} Accepted candidate "
        f"sha256 {PINS[CANDIDATE]}; receipt "
        f"{RECEIPT.relative_to(REPO).as_posix()} sha256 {PINS[RECEIPT]}; "
        f"Codex review sha256 {PINS[CODEX_REVIEW]}; Owner packet sha256 "
        f"{PINS[PACKET]}; release {NEW.package_uuid}/{NEW.release_version}; "
        f"recorded {at}"
    )


def evidence(mode: str, at: str) -> tuple[dict[str, str], dict[str, str]]:
    """Per-step evidence templates: (accept_proposal, resolve_references)."""
    if mode == "simulated":
        return (
            {"reviewer": SIMULATED_REVIEWER, "accepted_at": SIMULATED_AT},
            {
                "reviewer": SIMULATED_REVIEWER,
                "authorized_by": SIMULATED_REVIEWER,
                "resolved_at": SIMULATED_AT,
            },
        )
    return (
        {"reviewer": OWNER, "accepted_at": at},
        {"reviewer": OWNER, "authorized_by": OWNER, "resolved_at": at},
    )


def run(steps: list[Any], mode: str, at: str = "") -> AcceptedInputs:
    """mode: 'control' (verbatim), 'simulated' (candidate) or 'owner'."""
    inputs: AcceptedInputs | None = None
    acc, res = evidence(mode, at) if mode != "control" else ({}, {})
    for n, (fn, proposal, kw) in enumerate(steps):
        kw = dict(kw)
        if mode != "control":
            kw = rebind(kw)
            if fn == "accept_proposal":
                proposal = rebind(proposal)
                kw.update(acc)
                kw["rule"] = (
                    "SIMULATION ONLY: release-order replacement candidate, "
                    f"mechanical rebind of accepted batch {kw['batch_id']}; "
                    "not an Owner acceptance"
                    if mode == "simulated"
                    else f"{_decision(at)}; accepted batch {kw['batch_id']}"
                )
            else:
                kw.update(res)
                kw["authorization_reference"] = (
                    "SIMULATION ONLY: release-order replacement candidate, "
                    f"mechanical rebind of resolution step {n}; "
                    "not an Owner authorization"
                    if mode == "simulated"
                    else f"{_decision(at)}; chain resolution step {n}"
                )
        if fn == "accept_proposal":
            inputs = accept_proposal(proposal, prior=inputs, **kw)
        else:
            assert inputs is not None
            inputs = resolve_references(inputs, **kw)
    assert inputs is not None
    return inputs


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def _blank(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("<evidence>" if k in EVIDENCE else _blank(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_blank(v) for v in x]
    return x


def compare(candidate: bytes, recorded: bytes) -> dict[str, Any]:
    """Accepted candidate vs recording: only the six evidence fields may differ.

    Everything outside ``acceptance`` must be exactly equal. Inside it, after
    blanking the six fields, a collection may differ only in order (the native
    canonical sort over the changed evidence); any other difference fails.
    ``proposal_identity`` is deliberately not blanked.
    """
    a, b = json.loads(candidate), json.loads(recorded)
    assert a.keys() == b.keys()
    outside = [k for k in a if k != "acceptance" and a[k] != b[k]]
    assert not outside, outside
    order_only: dict[str, int] = {}
    bad: list[str] = []

    def walk(x: Any, y: Any, path: str) -> None:
        if isinstance(x, dict) and isinstance(y, dict):
            if x.keys() != y.keys():
                bad.append(f"{path}: keys")
                return
            for k in x:
                walk(x[k], y[k], f"{path}.{k}")
        elif isinstance(x, list) and isinstance(y, list):
            if x == y:
                return
            if sorted(map(_canon, x)) == sorted(map(_canon, y)):
                order_only[path] = len(x)
                return
            if len(x) != len(y):
                bad.append(f"{path}: length {len(x)} != {len(y)}")
                return
            for i, (u, v) in enumerate(zip(x, y, strict=True)):
                walk(u, v, f"{path}[{i}]")
        elif x != y:
            bad.append(f"{path}: {str(x)[:80]!r} != {str(y)[:80]!r}")

    walk(_blank(a["acceptance"]), _blank(b["acceptance"]), "$.acceptance")
    changed: Counter[str] = Counter()

    def count(x: Any, y: Any, path: str) -> None:
        if isinstance(x, dict) and isinstance(y, dict):
            for k in x:
                if k in EVIDENCE:
                    changed[f"{path}.{k}"] += x[k] != y[k]
                else:
                    count(x[k], y[k], f"{path}.{k}")
        elif isinstance(x, list) and isinstance(y, list):
            key = next(
                (
                    k
                    for k in ("span_id", "unit_id", "resolution_id", "batch_id")
                    if x and isinstance(x[0], dict) and k in x[0]
                ),
                None,
            )
            if key is not None and len({e[key] for e in x}) == len(x):
                by = {e[key]: e for e in y}
                for e in x:
                    count(e, by[e[key]], f"{path}[*]")
            else:
                for u, v in zip(x, y, strict=True):
                    count(u, v, f"{path}[*]")

    count(a["acceptance"], b["acceptance"], "$.acceptance")
    return {
        "outside_acceptance_differences": outside,
        "unaccounted": bad,
        "order_only": order_only,
        "evidence_changed": dict(changed),
    }


def findings(inputs: AcceptedInputs) -> list[str]:
    b = inputs.oracle.binding
    src = SP / "rel-new/afterworlds.db"
    before = sha(src)
    with tempfile.TemporaryDirectory(prefix="release-order-recording-") as tmp:
        t = Path(tmp) / "release.db"
        shutil.copyfile(src, t)
        engine = create_engine(f"sqlite:///{t}")
        try:
            with create_session_factory(engine)() as s:
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                out = list(
                    validate_candidate(candidate_from_accepted_inputs(inputs), corpus)
                )
        finally:
            engine.dispose()
    assert sha(src) == before
    return out


def main(mode: str) -> None:
    check_pins()
    print("old binding", dataclasses.asdict(OLD))
    print("new binding", dataclasses.asdict(NEW))
    steps = pickle.loads(CHAIN.read_bytes())
    print("steps", len(steps), Counter(s[0] for s in steps))
    assert len(steps) == 43
    control = serialize_accepted_inputs(run(steps, "control"))
    print("control == prior live oracle", control == PRIOR.read_bytes())
    assert control == PRIOR.read_bytes()
    simulated = serialize_accepted_inputs(run(steps, "simulated"))
    print("simulated == accepted candidate", simulated == CANDIDATE.read_bytes())
    assert simulated == CANDIDATE.read_bytes()
    print("rebound", dict(swapped))
    if mode == "--simulate":
        return

    if mode == "--record":
        assert RECORDED_AT is None and not TARGET.exists()
        at = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert at > RECEIPT_AT, at
    else:
        assert RECORDED_AT is not None and RECORDED_SHA256 is not None
        at = RECORDED_AT
    print("recording time", at)
    data = serialize_accepted_inputs(run(steps, "owner", at))
    report = compare(CANDIDATE.read_bytes(), data)
    print(json.dumps(report, indent=1))
    assert not report["unaccounted"] and not report["outside_acceptance_differences"]
    text = data.decode("utf-8")
    prior_acc = json.loads(PRIOR.read_text("utf-8"))["acceptance"]
    prior_values = {
        e[k]
        for coll in prior_acc.values()
        if isinstance(coll, list)
        for e in coll
        if isinstance(e, dict)
        for k in ("accepted_at", "resolved_at", "rule", "authorization_reference")
        if k in e
    }
    survivors = sorted(v for v in prior_values if json.dumps(v)[1:-1] in text)
    print("SIMULATION residue", text.count("SIMULATION"))
    print("prior evidence values surviving", len(survivors), survivors[:3])
    assert "SIMULATION" not in text and not survivors
    for label, needle in [
        ("old uuid", OLD.package_uuid),
        ("old version", OLD.release_version),
        ("old bundle", OLD.bundle_root_hash),
        ("old digest", OLD.persisted_corpus_digest),
    ]:
        print(f"residual {label}:", text.count(needle))
        assert needle not in text
    print("residual old chunk ids:", sum(text.count(c) for c in CHUNK))

    if mode == "--record":
        assert not TARGET.exists()
        with TARGET.open("xb") as f:
            f.write(data)
        print("wrote", TARGET.relative_to(REPO).as_posix())
    got = TARGET.read_bytes()
    print("on disk == recomposed", got == data)
    assert got == data
    digest = hashlib.sha256(got).hexdigest()
    print("recorded sha256", digest, len(got), "bytes")
    if mode == "--verify":
        assert digest == RECORDED_SHA256
    back = load_accepted_inputs(TARGET)
    print("reload bytes equal", serialize_accepted_inputs(back) == got)
    assert serialize_accepted_inputs(back) == got
    print("binding == new", back.oracle.binding == NEW)
    assert back.oracle.binding == NEW
    resolved = committed_inputs_for(NEW.package_uuid, NEW.release_version)
    print("committed selection (new binding) == recorded", resolved == back)
    assert resolved is not None and serialize_accepted_inputs(resolved) == got
    stale = committed_inputs_for(OLD.package_uuid, OLD.release_version)
    assert stale is not None and serialize_accepted_inputs(stale) == PRIOR.read_bytes()
    print("stale binding resolves only to the unchanged prior file", sha(PRIOR))
    o = back.oracle
    print(
        "counts batches",
        len(back.batches),
        "records",
        len(o.records) if hasattr(o, "records") else "n/a",
        "resolutions",
        len(o.reference_resolutions),
    )
    found = findings(back)
    refs = [f for f in found if f.startswith("reference ")]
    leaves = [f for f in found if f.startswith("leaf ")]
    print(
        "native findings: reference",
        len(refs),
        "uncovered-leaf",
        len(leaves),
        "other",
        len(found) - len(refs) - len(leaves),
    )
    assert not found
    print("OK", mode)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("--simulate", "--record", "--verify")
    main(sys.argv[1])
