"""Owner acceptance of the final-ten reference candidate.

CRD Issues 5c/5d (#132, #137). The Owner answered the reviewed candidate (the
packet :data:`PACKET_SHA256`, Codex's review :data:`CODEX_REVIEW_SHA256`) with
:data:`APPROVAL`, verbatim; ``issue-5d-final-ten-references-owner-acceptance.md``
(:data:`ACCEPTANCE_SHA256`) records it and pins the artifacts. Codex verified
the approval before :data:`APPROVAL_BEFORE`; no more precise approval time is
known or recorded.

The recording is additive: no batch is replaced. It is the reviewed
constructor (:data:`CONSTRUCTOR_SHA256`, kept byte for byte with its PROPOSAL
and DELTA under ``issue-5d-final-ten-references/candidate/``) acted on by the
Owner: one ``resolve_references`` call over the prior with the ten resolutions
its ``drafts`` builds. One write, ``record-final-ten-references``, reads the UTC
clock once; the ten approvals carry that time. Nothing else is re-accepted,
re-keyed, reordered or lifted. The simulated approvals are never copied: the
recorded file names no simulation.

The prior (:data:`PRIOR_SHA256`) is the equipment-spell-references recording.
The oracle is not tracked, so after the write the prior exists only as its
replay (:func:`prior`), or as a saved copy of its bytes passed to ``--verify``.
Before the write, :func:`_precheck` holds the simulated composition to the
reviewed bytes (:data:`SIMULATED_SHA256`) and runs every post-write check on
the Owner's evidence at a placeholder time. Any artifact state other than the
prior or its one step result fails closed. Zero findings remain; the
partial-publication block stands; nothing here publishes or activates, and the
release order is not corrected (one bounded Owner order pass comes before
publication; it is not a recording prerequisite).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    resolve_references,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_payload,
    reference_resolution_violations,
)


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: The reviewed constructor, used as it was reviewed (its drafts, never its
#: simulated evidence), from its committable byte-identical home.
CANDIDATE_DIR = HERE / "issue-5d-final-ten-references" / "candidate"
CONSTRUCTOR = CANDIDATE_DIR / "CANDIDATE.py"
CONSTRUCTOR_SHA256 = "2f84d877037b865121bd502a9c92ae365f44cf82dc6d312d814759200433fd57"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
HARNESS = _load("final_ten_references_candidate", CONSTRUCTOR)
#: The prior's recording script, for its replay and the Owner's name.
ESR = _load(
    "equipment_spell_references_accept",
    HERE / "issue-5d-equipment-spell-references-ACCEPT.py",
)
REPL = HARNESS.REPL
APC = HARNESS.APC

ACCEPTED_PATH: Path = HARNESS.ACCEPTED_PATH
PRIOR_SHA256: str = ESR.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == HARNESS.ACCEPTED_SHA256

#: The reviewed resolutions, delta, packets and acceptance.
PROPOSAL_FILE: Path = HARNESS.PROPOSAL_FILE
PROPOSAL_SHA256 = "46808846b0ad6712393b0f058a71e03d6e664a2ffdf8734de7d046bf4b4d68e3"
DELTA_FILE: Path = HARNESS.DELTA_FILE
DELTA_SHA256 = "465a17f7d749c512aed45848874576a6c2a839e1eaf0ea595da6a6c11c827851"
PACKET_FILE = HERE / "issue-5d-final-ten-references-candidate.md"
PACKET_SHA256 = "24a42c7321111b186dc090327ab0e43afc422720ed80cf83cc1d4d7c92d012b0"
CODEX_REVIEW_FILE = HERE / "issue-5d-final-ten-references-codex-review.md"
CODEX_REVIEW_SHA256 = "d5e1a9b2ea62a3d65c3a7acf0b3cab067acc0c617bb8754b1ca94ea5e25c80ab"
ACCEPTANCE_FILE = HERE / "issue-5d-final-ten-references-owner-acceptance.md"
ACCEPTANCE_SHA256 = "5166bb4092937c7679ca07ef74d8f3f44ff0dd8741af17391a2f9cf6efd6dc5e"
#: The reviewed reader test, kept byte for byte beside the constructor. The
#: live test was in these bytes at the write; fixtures change after it.
REVIEWED_TEST_FILE = (
    CANDIDATE_DIR / "reviewed-test_final_ten_references_candidate.py.txt"
)
REVIEWED_TEST_SHA256 = (
    "fec853b8ed1d84146248aa19d5f92b1c60b14aea226cf281a31dba6a07ba3dbe"
)
#: Checked before the write only: later work may change either.
LIVE_TEST_FILE = (
    REPO / "tests/ingestion/mechanical/test_final_ten_references_candidate.py"
)
READER_FILE = REPO / "src/afterworlds/services/rules_authority/service.py"
READER_SHA256 = "4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d"
#: The reviewed composition under the simulated reviewer, never recorded.
SIMULATED_SHA256 = "6302adbe7b09fab0a26d60e5526d72fa5269214e3911b0362486ad9e705d85ff"
SIMULATED_REVIEWER: str = HARNESS.SIMULATED_REVIEWER
SIMULATED_RULE: str = HARNESS.SIMULATED_RULE
SIMULATED_AT: str = HARNESS.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"
#: The reviewed DELTA's first line; the recorded delta has no simulation.
DELTA_HEADER = b"# SIMULATED candidate; no Owner approval\n"

#: The Owner is the reviewer and the authorizer.
OWNER: str = ESR.OWNER
assert OWNER == "Ravenlok (Owner)"
#: The Owner's acceptance, verbatim.
APPROVAL = "I accept this exact candidate."
#: Codex verified the approval before this time. It is not an acceptance time
#: and is never recorded.
APPROVAL_BEFORE = "2026-10-07T01:13:39Z"
AUTHORIZATION_REFERENCE = (
    f"Owner decision recorded in {ACCEPTANCE_FILE.name} (SHA-256 "
    f"{ACCEPTANCE_SHA256}) on {PACKET_FILE.name} (SHA-256 {PACKET_SHA256}) and "
    f"{CODEX_REVIEW_FILE.name} (SHA-256 {CODEX_REVIEW_SHA256}): "
    f"{CONSTRUCTOR.name} (SHA-256 {CONSTRUCTOR_SHA256}; {PROPOSAL_FILE.name}, "
    f"SHA-256 {PROPOSAL_SHA256}; {DELTA_FILE.name}, SHA-256 {DELTA_SHA256}; "
    f"simulated {SIMULATED_SHA256}), recorded over {ACCEPTED_PATH.name} "
    f"(SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)

#: batches, records, spans, review units, resolutions; then reference,
#: uncovered-leaf and other findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int, int]]] = {
    "prior": ((24, 1835, 10493, 1476, 1476), (10, 0, 0)),
    "recorded": ((24, 1835, 10493, 1476, 1486), (0, 0, 0)),
}
#: Resolutions, labelled routes (rows 39, 87 and 88 are plain targets, no
#: route) and destinations (a plain target counts one).
ROWS, ROUTES, DESTINATIONS = 10, 144, 201
#: The evidence fields a recording may set; nothing else may differ from the
#: simulated composition.
EVIDENCE = {"reviewer", "authorized_by", "authorization_reference", "resolved_at"}

#: The executed write time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: str | None = "2026-10-07T01:30:07Z"
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The equipment-spell-references recording, rebuilt from its recorded
    time over its own replayed prior (a historical replay)."""
    if not _PRIOR:
        inputs: AcceptedInputs = ESR.recorded(ESR.prior(), ESR.OWNER, ESR.RECORDED_AT)
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def saved_prior(path: Path) -> AcceptedInputs:
    """The prior from a saved copy of its bytes, checked by SHA-256."""
    assert _sha(path.read_bytes()) == PRIOR_SHA256, f"{path} is not the prior"
    return load_accepted_inputs(path)


def reviewed() -> dict[str, Any]:
    """The reviewed PROPOSAL, read from its pinned file."""
    raw = PROPOSAL_FILE.read_bytes()
    assert _sha(raw) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal: dict[str, Any] = json.loads(raw)
    assert proposal["accepted_sha256"] == PRIOR_SHA256
    return proposal


def recorded(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """The one native action: the ten reviewed resolutions over ``base``,
    reviewed and authorized by ``reviewer`` at ``at``."""
    if reviewer == OWNER:
        ref = AUTHORIZATION_REFERENCE
    else:
        assert reviewer == SIMULATED_REVIEWER, reviewer
        ref = SIMULATED_RULE
    return resolve_references(
        base,
        resolutions=HARNESS.drafts(base),
        authorized_by=reviewer,
        authorization_reference=ref,
        reviewer=reviewer,
        resolved_at=at,
    )


def _new_ids() -> set[str]:
    return {r["resolution_id"] for r in reviewed()["reference_resolutions"]}


def _read_back(inputs: AcceptedInputs) -> str | None:
    """The executed write time ``inputs`` records; None if none of the ten is
    recorded (the prior)."""
    new = _new_ids()
    at = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id in new
    }
    if not at:
        return None
    assert len(at) == 1, sorted(at)
    return str(next(iter(at)))


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every new-resolution acceptance that does not name the Owner and this
    decision, and every new resolution without exactly one."""
    new = _new_ids()
    mine = [
        a for a in inputs.reference_resolution_acceptances if a.resolution_id in new
    ]
    wrong = [
        f"resolution {a.resolution_id}"
        for a in mine
        if (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    counts = Counter(a.resolution_id for a in mine)
    wrong += [f"{k}: {counts[k]} approvals" for k in sorted(new) if counts[k] != 1]
    return wrong


def _findings(inputs: AcceptedInputs) -> tuple[list[str], tuple[int, int, int]]:
    found: list[str] = APC.findings(inputs)
    refs = sum(f.startswith("reference ") for f in found)
    leaves = sum(f.startswith("leaf ") for f in found)
    return found, (refs, leaves, len(found) - refs - leaves)


def load_accepted_inputs_bytes(data: bytes) -> AcceptedInputs:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        return load_accepted_inputs(path)


def _canonical(inputs: AcceptedInputs) -> AcceptedInputs:
    """``inputs`` as its file loads: the loader holds batches, records and
    resolutions in the payload's canonical order, a replay in append order."""
    return load_accepted_inputs_bytes(serialize_accepted_inputs(inputs))


def _preserved(
    before: AcceptedInputs, after: AcceptedInputs, new_ids: set[str]
) -> dict[str, tuple[int, int]]:
    """Every accepted item is carried verbatim; the only additions are the new
    resolutions and their approval records. (The reviewed constructor's own
    check also requires the additions to be simulated; this one leaves the
    approvals to :func:`_approvals`.)"""
    old, new = accepted_inputs_payload(before), accepted_inputs_payload(after)
    out: dict[str, tuple[int, int]] = {}
    for path in REPL.COLLECTIONS:
        a = Counter(REPL._key(x) for x in REPL._at(old, path))
        b = Counter(REPL._key(x) for x in REPL._at(new, path))
        lost, added = a - b, b - a
        assert not lost, (path, next(iter(lost))[:300])
        for k in added:
            assert json.loads(k).get("resolution_id") in new_ids, (path, k[:300])
        if added:
            out[".".join(path)] = (0, sum(added.values()))
    assert before.batches == after.batches
    assert before.acceptances == after.acceptances
    assert before.policy_transitions == after.policy_transitions
    o, p = before.oracle, after.oracle
    for name in ("binding", "schema_version", "schema_hash", "representation"):
        assert getattr(o, name) == getattr(p, name), name
    olds = {r.resolution_id: r for r in o.reference_resolutions}
    news = {r.resolution_id: r for r in p.reference_resolutions}
    assert all(news.get(k) == v for k, v in olds.items()), "resolution changed"
    assert set(news) - set(olds) == new_ids, set(news) - set(olds)
    old_acc = before.reference_resolution_acceptances
    new_acc = after.reference_resolution_acceptances
    assert set(old_acc) <= set(new_acc), "approval changed"
    assert {a.resolution_id for a in set(new_acc) - set(old_acc)} == new_ids
    return out


def _proposal_bytes(base: AcceptedInputs, tail: tuple[Any, ...]) -> bytes:
    """The PROPOSAL document the reviewed constructor writes, for ``tail``."""
    return (
        json.dumps(
            {
                "accepted_sha256": _sha(serialize_accepted_inputs(base)),
                "representation_schema": [
                    base.oracle.schema_version,
                    base.oracle.schema_hash,
                ],
                "simulated_only": True,
                "reference_resolutions": reference_resolution_payload(tail),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, findings, preservation and the reviewed PROPOSAL and
    delta, with both sides compared in their canonical (as-loaded) form."""
    base, inputs = _canonical(base), _canonical(inputs)
    print(state)
    print(
        "  counts (batches, records, spans, units, resolutions)", REPL._counts(inputs)
    )
    assert REPL._counts(base) == EXPECTED["prior"][0], REPL._counts(base)
    assert REPL._counts(inputs) == EXPECTED[state][0], REPL._counts(inputs)
    if state == "prior":
        print("  representation schema", inputs.oracle.schema_version)
        return
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation,
        oracle.reference_resolutions,
        oracle.binding,
        schema_version=oracle.schema_version,
    )
    print("  resolution violations", len(violations))
    assert not violations, violations[:5]
    schema = (oracle.schema_version, oracle.schema_hash)
    same = schema == (base.oracle.schema_version, base.oracle.schema_hash)
    print("  representation schema", schema[0], "unchanged, no lift", same)
    assert same and inputs.lifts == base.lifts
    same = oracle.binding == base.oracle.binding
    print("  release binding unchanged", same)
    assert same
    before, split = _findings(base)
    after, now = _findings(inputs)
    print("  findings (reference, uncovered-leaf, other)", split, "->", now)
    assert split == EXPECTED["prior"][1] and now == EXPECTED[state][1]
    gone, added = Counter(before) - Counter(after), Counter(after) - Counter(before)
    print("  findings cleared", sum(gone.values()), "| new", dict(added))
    assert sum(gone.values()) == ROWS and not added
    new_ids = _new_ids()
    changes = _preserved(base, inputs, new_ids)
    print("  every accepted item kept, evidence included; (lost, added):")
    for collection, n in changes.items():
        print("   ", collection, n)
    assert changes == {
        "reference_resolutions": (0, ROWS),
        "acceptance.reference_resolution_records": (0, ROWS),
    }, changes
    same = [b.proposal_identity for b in inputs.batches] == [
        b.proposal_identity for b in base.batches
    ]
    print("  24 batches, identities, approvals and evidence verbatim", same)
    assert same and inputs.batches == base.batches
    assert inputs.review_unit_acceptances == base.review_unit_acceptances
    head = tuple(
        r for r in oracle.reference_resolutions if r.resolution_id not in new_ids
    )
    tail = tuple(r for r in oracle.reference_resolutions if r.resolution_id in new_ids)
    same = reference_resolution_payload(head) == reference_resolution_payload(
        base.oracle.reference_resolutions
    )
    print("  1476 resolutions verbatim, canonical order", same)
    assert same
    kept = [
        a
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id not in new_ids
    ]
    same = kept == list(base.reference_resolution_acceptances)
    print("  1476 historical resolution approvals verbatim, in order", same)
    assert same
    same = reference_resolution_payload(tail) == reviewed()["reference_resolutions"]
    print("  10 new resolutions are the reviewed PROPOSAL's, canonical order", same)
    assert same
    same = _proposal_bytes(base, tail) == PROPOSAL_FILE.read_bytes()
    print("  the reviewed PROPOSAL rebuilds byte for byte", same)
    assert same
    routes = sum(len({d.alternative_label for d in r.destinations}) for r in tail)
    dests = sum(len(r.destinations) or 1 for r in tail)
    print("  resolutions, routes, destinations", (len(tail), routes, dests))
    assert (len(tail), routes, dests) == (ROWS, ROUTES, DESTINATIONS)
    same = inputs.policy_transitions == base.policy_transitions
    print("  lifts and policy history unchanged", same)
    assert same
    delta = (
        "# Full-text delta from the accepted artifact (evidence blanked)\n"
        + "".join(f"{x}\n" for x in REPL.Delta(base, inputs).report())
        + "# Effective reference lines\n"
        + HARNESS.FRR._delta(base, inputs)
    ).encode("utf-8")
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    assert raw.startswith(DELTA_HEADER) and raw.count(DELTA_HEADER) == 1
    # The delta blanks reviewer and resolved_at but shows a resolution's
    # authorizer and reference, so the reviewed (simulated) DELTA names the
    # simulation on the ten new resolution lines and nowhere else.
    sim, own = (
        json.dumps(
            {"authorization_reference": ref, "authorized_by": who}, ensure_ascii=False
        )[1:-1].encode("utf-8")
        for ref, who in (
            (SIMULATED_RULE, SIMULATED_REVIEWER),
            (AUTHORIZATION_REFERENCE, OWNER),
        )
    )
    assert raw.count(sim) == ROWS and own not in raw
    expected = raw[len(DELTA_HEADER) :].replace(sim, own)
    print(
        "  delta is the reviewed DELTA, byte for byte, without its simulation",
        "header and with the ten new resolutions' authorizer and reference the",
        "Owner's",
        delta == expected,
    )
    assert delta == expected


def _leaves(x: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(x, dict):
        for k in sorted(x):
            yield from _leaves(x[k], (*path, k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _leaves(v, (*path, i))
    else:
        yield (*path, x)


def _aligned(x: Any) -> Any:
    """``x`` with every list of objects ordered by the objects' non-evidence
    content: the payload orders some records by their evidence (a time), so
    the same item can sit at different positions in the two compositions."""
    if isinstance(x, dict):
        return {k: _aligned(v) for k, v in x.items()}
    if isinstance(x, list):
        items = [_aligned(v) for v in x]
        if items and all(isinstance(v, dict) for v in items):

            def key(v: dict[str, Any]) -> str:
                rest = {k: w for k, w in v.items() if k not in EVIDENCE}
                return json.dumps(rest, sort_keys=True, ensure_ascii=False)

            keys = [key(v) for v in items]
            assert len(set(keys)) == len(keys), "items differ only in evidence"
            items = [v for _, v in sorted(zip(keys, items, strict=True))]
        return items
    return x


def sim_diff(simulated: bytes, actual: bytes, at: str) -> Counter[tuple[str, ...]]:
    """Every leaf where the recording differs from the simulated composition,
    grouped by (collection, field, simulated, recorded). Fails on any leaf
    that is not new-resolution evidence."""
    a = _aligned(accepted_inputs_payload(load_accepted_inputs_bytes(simulated)))
    b = _aligned(accepted_inputs_payload(load_accepted_inputs_bytes(actual)))
    la, lb = list(_leaves(a)), list(_leaves(b))
    assert [x[:-1] for x in la] == [x[:-1] for x in lb], "payload shape differs"
    new_ids = _new_ids()
    allowed = {SIMULATED_RULE, SIMULATED_REVIEWER, SIMULATED_AT}
    owner = {OWNER, AUTHORIZATION_REFERENCE, at}
    out: Counter[tuple[str, ...]] = Counter()
    for x, y in zip(la, lb, strict=True):
        if x[-1] == y[-1]:
            continue
        path = x[:-2]
        item: Any = b
        for k in path:
            item = item[k]
        field = x[-2]
        assert field in EVIDENCE and item.get("resolution_id") in new_ids, x[:-1]
        assert x[-1] in allowed and y[-1] in owner, (x, y[-1])
        where = ".".join(str(k) for k in path if not isinstance(k, int))
        out[(where, str(field), str(x[-1])[:40], str(y[-1])[:40])] += 1
    assert sum(out.values()) == ROWS * len(EVIDENCE), sum(out.values())
    return out


def _no_simulation(data: bytes) -> None:
    """No simulated reviewer, rule or time reaches a recorded file."""
    for value in (SIMULATED_REVIEWER, SIMULATED_RULE, SIMULATED_AT, "SIMULATION"):
        assert value.encode("utf-8") not in data, value
    print("  names no simulation True")


def _precheck(base: AcceptedInputs) -> bytes:
    """Before any write: the reviewed reader and test are in place; under the
    simulated reviewer the composition is the reviewed one, byte for byte;
    under the Owner, at a placeholder time, every post-write check passes on
    the Owner's own evidence. Returns the simulated bytes."""
    for path, sha in (
        (READER_FILE, READER_SHA256),
        (LIVE_TEST_FILE, REVIEWED_TEST_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
    print("  reviewed reader and live reader test in place True")
    _no_simulation(serialize_accepted_inputs(base))
    sim = recorded(base, SIMULATED_REVIEWER, SIMULATED_AT)
    simulated = serialize_accepted_inputs(sim)
    print("  simulated bytes", _sha(simulated), "(reviewed; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256
    final = recorded(base, OWNER, PLACEHOLDER_AT)
    _check("recorded", base, final)
    wrong = _approvals(final)
    print("  under the Owner every new approval names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == PLACEHOLDER_AT
    data = serialize_accepted_inputs(final)
    _no_simulation(data)
    assert _sha(data) != SIMULATED_SHA256
    approvals = len(final.reference_resolution_acceptances)
    print("  under the Owner resolution approvals", approvals)
    assert approvals == EXPECTED["recorded"][0][4]
    assert serialize_accepted_inputs(load_accepted_inputs_bytes(data)) == data
    print("  under the Owner reloads to the same bytes True")
    same = HARNESS.FRR._persisted_round_trip(final)
    print("  under the Owner persisted round trip (scratch release copy)", same)
    assert same
    diff = sim_diff(simulated, data, PLACEHOLDER_AT)
    print("  owner vs simulated differing leaves", sum(diff.values()))
    return simulated


def _state(base: AcceptedInputs) -> tuple[str, AcceptedInputs]:
    """(state, inputs) of the artifact. Fails closed on anything but the prior
    or its one step result over ``base``."""
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    at = _read_back(inputs)
    if at is None:
        if _sha(data) != PRIOR_SHA256:
            raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized prior")
        return "prior", inputs
    assert data == serialize_accepted_inputs(recorded(base, OWNER, at)), "drifted"
    return "recorded", inputs


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        if state == "recorded":
            assert _read_back(inputs) == RECORDED_AT, "not the recorded time"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  time (resolved)", _read_back(inputs))
    assert _sha(data) != SIMULATED_SHA256
    assert _read_back(inputs) != PLACEHOLDER_AT
    if state != "prior":
        wrong = _approvals(inputs)
        print("  every new approval names the Owner and this decision", not wrong)
        assert not wrong, wrong[:5]
        approvals = len(inputs.reference_resolution_acceptances)
        print("  resolution approvals", approvals)
        assert approvals == EXPECTED[state][0][4]
        _no_simulation(data)
    _check(state, base, inputs)
    assert serialize_accepted_inputs(load_accepted_inputs_bytes(data)) == data
    print("  reloads to the same bytes True")
    same = HARNESS.FRR._persisted_round_trip(inputs)
    print("  persisted round trip (scratch release copy)", same)
    assert same


def main(argv: list[str]) -> None:
    for path, sha in (
        (DELTA_FILE, DELTA_SHA256),
        (PACKET_FILE, PACKET_SHA256),
        (CODEX_REVIEW_FILE, CODEX_REVIEW_SHA256),
        (ACCEPTANCE_FILE, ACCEPTANCE_SHA256),
        (REVIEWED_TEST_FILE, REVIEWED_TEST_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
    reviewed()
    if argv == ["--simulate"]:
        base = saved_prior(ACCEPTED_PATH)
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    if argv[:1] == ["--verify"] and len(argv) <= 2:
        # The oracle is not tracked: the prior is its replay, or saved bytes.
        base = saved_prior(Path(argv[1])) if len(argv) == 2 else prior()
        state, inputs = _state(base)
        verify(state, base, inputs)
        return
    if argv != ["record-final-ten-references"]:
        raise SystemExit(
            "usage: --simulate | record-final-ten-references | --verify [prior]"
        )
    base = saved_prior(ACCEPTED_PATH)
    print("  prior bytes", _sha(ACCEPTED_PATH.read_bytes()))
    simulated = _precheck(base)
    at = _now()
    # The recording follows the approval Codex verified.
    assert at > APPROVAL_BEFORE, at
    data = serialize_accepted_inputs(recorded(base, OWNER, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-final-ten-references", ACCEPTED_PATH.name, at)
    print("  sha256", _sha(data))
    # Read the written artifact back: it must rebuild from its recorded time.
    after, inputs = _state(base)
    assert after == "recorded", after
    verify(after, base, inputs)
    print("actual vs simulated: differing leaves (collection, field, sim, actual)")
    for key, n in sorted(sim_diff(simulated, data, at).items()):
        print("  ", n, key)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
