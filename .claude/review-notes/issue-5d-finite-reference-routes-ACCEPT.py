"""Owner acceptance of the ten-reference route batch and its combat replacement.

CRD Issue 5d (#132, #137). The Owner answered the reviewed packet
``issue-5d-finite-reference-routes-review.md`` (:data:`REVIEW_SHA256`; the
seven files pinned in :data:`OWNER_MANIFEST`) with :data:`APPROVAL`, verbatim.
The approval preceded the parent's fresh verification at
:data:`APPROVAL_BEFORE`; no more precise approval time is known or recorded.

The acceptance module has no supersession, so the batch is recorded as the
reviewed ``issue-5d-finite-reference-routes-REPLACEMENT.py``
(:data:`CONSTRUCTOR_SHA256`) composes it: the recorded chain at its recorded
evidence, the combat-damage-breaking replacement (:data:`COMBAT_SHA256`,
identity :data:`COMBAT_IDENTITY`) accepted in combat's recorded place under
the Owner with :data:`APPROVAL` as its rule, the recorded schema-17 step
verbatim, then the ten reviewed resolutions the constructor's ``drafts``
builds, under the Owner. One write, ``record-finite-reference-routes``, reads
the UTC clock once; the combat acceptance and the resolutions carry that time.
Nothing else is re-accepted, re-keyed, reordered or lifted.

The prior (:data:`PRIOR_SHA256`) is the reference-alternatives recording. The
oracle is not tracked, so after the write the prior exists only as its replay
(:func:`prior`), or as a saved copy of its bytes passed to ``--verify``.
Before the write, :func:`_precheck` holds the simulated composition to the
reviewed bytes (:data:`SIMULATED_SHA256`) and runs every post-write check on
the Owner's evidence at a placeholder time. Any artifact state other than the
prior or its one step result fails closed. 23 reference findings and the
partial-publication block stay; nothing here publishes or activates, and the
release order is not corrected (one bounded order pass comes after the
packets and before publication; it is not a recording prerequisite).
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
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
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


#: The reviewed constructor, used as it was reviewed (its chain, combat file
#: and drafts, never its simulated evidence).
CONSTRUCTOR = HERE / "issue-5d-finite-reference-routes-REPLACEMENT.py"
CONSTRUCTOR_SHA256 = "afb1cf886296c59693aebd07fa97fb29a3bab85621e3d94fa57622b83e9fe3ec"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
HARNESS = _load("finite_reference_routes_replacement", CONSTRUCTOR)
RA = HARNESS.RA
REPL = HARNESS.REPL
APC = HARNESS.APC

ACCEPTED_PATH: Path = HARNESS.ACCEPTED_PATH
PRIOR_SHA256: str = RA.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == HARNESS.ACCEPTED_SHA256

COMBAT_BATCH: str = HARNESS.COMBAT_BATCH
COMBAT_FILE: Path = HARNESS.COMBAT_FILE
COMBAT_SHA256 = "1cc561616526b271728f0d8b0b5f2c7490b76ee76cf684e33903512daecf48f5"
COMBAT_IDENTITY = "cfd193513e8c769d45b42f4a6dfa420481b43f064b45fef564f1e5c5eaac8c23"
COMBAT_REPLACES = "ce7a80ff95d8ae361d2a76612b85d7f5d546c57755588d3084a6a41a4f8a7de2"
#: The reviewed resolutions (metadata-free), delta and packet.
PROPOSAL_FILE: Path = HARNESS.PROPOSAL_FILE
PROPOSAL_SHA256 = "404bee285f9695bfdffe5ff5b21d2a2ef2b443cf370a1bdfb3df5332470482d8"
DELTA_FILE: Path = HARNESS.DELTA_FILE
DELTA_SHA256 = "e90abfff64caae94ac4f0fe16f5bc8ef2099ccb702e874fc41a6b874a01d9bca"
REVIEW_FILE = HERE / "issue-5d-finite-reference-routes-review.md"
REVIEW_SHA256 = "17fc80f63e0f956229fb63733629802a2eb2e884c5d586c27ac8f80f28ea6b15"
#: The reviewed composition under the simulated reviewer, never recorded.
SIMULATED_SHA256 = "b6caeb91e7886d3e0747290751315e59a2852f6e904090b34c2f5a7d14f00f28"
SIMULATED_REVIEWER: str = HARNESS.SIMULATED_REVIEWER
SIMULATED_RULE: str = HARNESS.SIMULATED_RULE
SIMULATED_AT: str = HARNESS.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = RA.OWNER
#: Parent-verified outside the repository; its SHA-256 is not available here,
#: so none is pinned.
OWNER_MANIFEST = "finite-reference-routes-owner-manifest.json"
#: The Owner's acceptance, verbatim; the rule of the combat batch it accepts.
APPROVAL = (
    "I accept the exact ten-reference route batch and its combat-batch "
    "replacement, retaining 23 reference findings, zero uncovered leaves, and "
    "the partial-publication block."
)
#: The approval came before this time (the parent's fresh verification). It
#: is not an acceptance time and is never recorded.
APPROVAL_BEFORE = "2026-10-02T09:16:10Z"
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {REVIEW_FILE.name} (SHA-256 {REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}), {CONSTRUCTOR.name} (SHA-256 {CONSTRUCTOR_SHA256}; "
    f"{PROPOSAL_FILE.name}, SHA-256 {PROPOSAL_SHA256}; {COMBAT_FILE.name}, "
    f"SHA-256 {COMBAT_SHA256}, identity {COMBAT_IDENTITY}; {DELTA_FILE.name}, "
    f"SHA-256 {DELTA_SHA256}), recorded over {ACCEPTED_PATH.name} (SHA-256 "
    f"{PRIOR_SHA256}): {APPROVAL!r}"
)

#: batches, records, spans, review units, resolutions; then reference,
#: uncovered-leaf and other findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int, int]]] = {
    "prior": ((24, 1835, 10492, 1476, 1453), (33, 0, 0)),
    "recorded": ((24, 1835, 10493, 1476, 1463), (23, 0, 0)),
}
ROWS, ROUTES, DESTINATIONS = 10, 94, 121
#: The evidence fields a recording may set, and nothing else may differ from
#: the simulated composition.
EVIDENCE = {
    "rule",
    "reviewer",
    "accepted_at",
    "authorized_by",
    "authorization_reference",
    "resolved_at",
}

#: The executed write time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: str | None = "2026-10-02T10:00:20Z"
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The reference-alternatives recording, rebuilt from its recorded time
    (a historical replay)."""
    if not _PRIOR:
        inputs: AcceptedInputs = RA.recorded(RA.prior(), RA.RECORDED_AT)
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def saved_prior(path: Path) -> AcceptedInputs:
    """The prior from a saved copy of its bytes, checked by SHA-256."""
    assert _sha(path.read_bytes()) == PRIOR_SHA256, f"{path} is not the prior"
    return load_accepted_inputs(path)


def combat() -> MechanicalProposal:
    """The reviewed combat replacement, read from its pinned file."""
    assert _sha(COMBAT_FILE.read_bytes()) == COMBAT_SHA256, COMBAT_FILE.name
    return load_proposal(COMBAT_FILE, expected_identity=COMBAT_IDENTITY)


def reviewed() -> dict[str, Any]:
    """The reviewed PROPOSAL, read from its pinned file."""
    raw = PROPOSAL_FILE.read_bytes()
    assert _sha(raw) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal: dict[str, Any] = json.loads(raw)
    assert proposal["accepted_sha256"] == PRIOR_SHA256
    assert proposal["combat_replacement"] == {
        "batch_id": COMBAT_BATCH,
        "file": COMBAT_FILE.name,
        "sha256": COMBAT_SHA256,
        "proposal_identity": COMBAT_IDENTITY,
        "replaces": COMBAT_REPLACES,
    }
    return proposal


def composed(reviewer: str, at: str) -> AcceptedInputs:
    """The reviewed chain, combat's replacement accepted by ``reviewer`` at
    ``at`` in its recorded place, before the routes.

    ``HARNESS.composed`` reads the combat evidence from its module globals;
    they are set for the call and restored. :func:`_precheck` holds the
    simulated evidence to the reviewed bytes.
    """
    g: dict[str, Any] = vars(HARNESS)
    names = ("SIMULATED_RULE", "SIMULATED_REVIEWER", "SIMULATED_AT")
    saved = {name: g[name] for name in names}
    rule = APPROVAL if reviewer == OWNER else SIMULATED_RULE
    g.update(zip(names, (rule, reviewer, at), strict=True))
    try:
        return HARNESS.composed(combat())  # type: ignore[no-any-return]
    finally:
        g.update(saved)


def recorded(reviewer: str, at: str) -> AcceptedInputs:
    """The one native action: the replacement and the ten reviewed
    resolutions, reviewed and authorized by ``reviewer`` at ``at``."""
    base = composed(reviewer, at)
    if reviewer == OWNER:
        who, ref = OWNER, AUTHORIZATION_REFERENCE
    else:
        who, ref = SIMULATED_REVIEWER, SIMULATED_RULE
    return resolve_references(
        base,
        resolutions=HARNESS.drafts(base),
        authorized_by=who,
        authorization_reference=ref,
        reviewer=who,
        resolved_at=at,
    )


def _new_ids() -> set[str]:
    return {r["resolution_id"] for r in reviewed()["reference_resolutions"]}


def _combat_acceptances(inputs: AcceptedInputs) -> list[Any]:
    every: list[Any] = [*inputs.acceptances, *inputs.review_unit_acceptances]
    return [a for a in every if a.batch_id == COMBAT_BATCH]


def _read_back(inputs: AcceptedInputs) -> str | None:
    """The executed write time ``inputs`` records; None if combat is not the
    replacement (the prior)."""
    (identity,) = {
        b.proposal_identity for b in inputs.batches if b.batch_id == COMBAT_BATCH
    }
    if identity != COMBAT_IDENTITY:
        assert identity == COMBAT_REPLACES, identity
        return None
    new = _new_ids()
    at = {a.accepted_at for a in _combat_acceptances(inputs)}
    at |= {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id in new
    }
    assert len(at) == 1, sorted(at)
    return str(next(iter(at)))


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every combat or new-resolution acceptance that does not name the Owner
    and this decision."""
    new = _new_ids()
    wrong = [
        f"batch {b.batch_id}: rule {b.rule!r}"
        for b in inputs.batches
        if b.batch_id == COMBAT_BATCH and b.rule != APPROVAL
    ]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in _combat_acceptances(inputs)
        if a.reviewer != OWNER
    ]
    wrong += [
        f"resolution {a.resolution_id}"
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id in new
        and (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    return wrong


def _findings(inputs: AcceptedInputs) -> tuple[list[str], tuple[int, int, int]]:
    found: list[str] = APC.findings(inputs)
    refs = sum(f.startswith("reference ") for f in found)
    leaves = sum(f.startswith("leaf ") for f in found)
    return found, (refs, leaves, len(found) - refs - leaves)


def _canonical(inputs: AcceptedInputs) -> AcceptedInputs:
    """``inputs`` as its file loads: the loader holds batches, records and
    resolutions in the payload's canonical order, a replay in append order."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(serialize_accepted_inputs(inputs))
        return load_accepted_inputs(path)


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, findings, preservation and the reviewed delta, with
    both sides compared in their canonical (as-loaded) form."""
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
    before, split = _findings(base)
    after, now = _findings(inputs)
    print("  findings (reference, uncovered-leaf, other)", split, "->", now)
    assert split == EXPECTED["prior"][1] and now == EXPECTED[state][1]
    gone, added = Counter(before) - Counter(after), Counter(after) - Counter(before)
    print("  findings cleared", sum(gone.values()), "| new", dict(added))
    assert sum(gone.values()) == ROWS and not added
    identities = {b.batch_id: b.proposal_identity for b in inputs.batches}
    was = {b.batch_id: b.proposal_identity for b in base.batches}
    same = list(identities) == list(was) and {
        k: v for k, v in identities.items() if k != COMBAT_BATCH
    } == {k: v for k, v in was.items() if k != COMBAT_BATCH}
    print("  23 batch identities unchanged", same)
    assert same
    print("  combat", was[COMBAT_BATCH], "->", identities[COMBAT_BATCH])
    assert (was[COMBAT_BATCH], identities[COMBAT_BATCH]) == (
        COMBAT_REPLACES,
        COMBAT_IDENTITY,
    )
    proposal = reviewed()
    new_ids = _new_ids()
    changes = HARNESS._preserved(base, inputs, new_ids)
    print("  outside combat everything kept, evidence included; (lost, added):")
    for collection, n in changes.items():
        print("   ", collection, n)
    same = [b for b in inputs.batches if b.batch_id != COMBAT_BATCH] == [
        b for b in base.batches if b.batch_id != COMBAT_BATCH
    ]
    print("  23 batches' approvals and evidence verbatim", same)
    assert same
    # Split by identity, not position: a loaded artifact holds its resolutions
    # in the payload's canonical (resolution_id) order, not append order.
    head = tuple(
        r for r in oracle.reference_resolutions if r.resolution_id not in new_ids
    )
    tail = tuple(r for r in oracle.reference_resolutions if r.resolution_id in new_ids)
    same = reference_resolution_payload(head) == reference_resolution_payload(
        base.oracle.reference_resolutions
    )
    print("  1453 resolutions verbatim, canonical order", same)
    assert same
    kept = [
        a
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id not in new_ids
    ]
    same = kept == list(base.reference_resolution_acceptances)
    print("  1453 historical resolution approvals verbatim, in order", same)
    assert same
    same = reference_resolution_payload(tail) == proposal["reference_resolutions"]
    print("  10 new resolutions are the reviewed PROPOSAL's, canonical order", same)
    assert same
    routes = sum(len({d.alternative_label for d in r.destinations}) for r in tail)
    dests = sum(len(r.destinations) for r in tail)
    print("  resolutions, routes, destinations", (len(tail), routes, dests))
    assert (len(tail), routes, dests) == (ROWS, ROUTES, DESTINATIONS)
    same = inputs.policy_transitions == base.policy_transitions
    print("  lifts and policy history unchanged", same)
    assert same
    delta = (
        "# Full-text delta from the accepted artifact (evidence blanked)\n"
        + "".join(f"{x}\n" for x in REPL.Delta(base, inputs).report())
        + "# Effective reference lines\n"
        + HARNESS._delta(base, inputs)
    ).encode("utf-8")
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
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
    expected = raw.replace(sim, own)
    print(
        "  delta is the reviewed DELTA, byte for byte, the ten new resolutions'",
        "authorizer and reference the Owner's",
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
    that is not combat or new-resolution evidence."""
    a = _aligned(accepted_inputs_payload(load_accepted_inputs_bytes(simulated)))
    b = _aligned(accepted_inputs_payload(load_accepted_inputs_bytes(actual)))
    la, lb = list(_leaves(a)), list(_leaves(b))
    assert [x[:-1] for x in la] == [x[:-1] for x in lb], "payload shape differs"
    new_ids = _new_ids()
    allowed = {SIMULATED_RULE, SIMULATED_REVIEWER, SIMULATED_AT}
    owner = {APPROVAL, OWNER, AUTHORIZATION_REFERENCE, at}
    out: Counter[tuple[str, ...]] = Counter()
    for x, y in zip(la, lb, strict=True):
        if x[-1] == y[-1]:
            continue
        path = x[:-2]
        item: Any = b
        for k in path:
            item = item[k]
        mine = item.get("batch_id") == COMBAT_BATCH or (
            item.get("resolution_id") in new_ids
        )
        field = x[-2]
        assert field in EVIDENCE and mine, x[:-1]
        assert x[-1] in allowed and y[-1] in owner, (x, y[-1])
        where = ".".join(str(k) for k in path if not isinstance(k, int))
        out[(where, str(field), str(x[-1])[:40], str(y[-1])[:40])] += 1
    return out


def load_accepted_inputs_bytes(data: bytes) -> AcceptedInputs:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        return load_accepted_inputs(path)


def _precheck(base: AcceptedInputs) -> bytes:
    """Before any write: under the simulated reviewer the composition is the
    reviewed one, byte for byte; under the Owner, at a placeholder time, every
    post-write check passes on the Owner's own evidence. Returns the
    simulated bytes."""
    sim = recorded(SIMULATED_REVIEWER, SIMULATED_AT)
    simulated = serialize_accepted_inputs(sim)
    print("  simulated bytes", _sha(simulated), "(reviewed; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256
    final = recorded(OWNER, PLACEHOLDER_AT)
    same = [b.batch_id for b in prior().batches] == [b.batch_id for b in final.batches]
    print("  acceptance order is the recorded chain's", same)
    assert same
    _check("recorded", base, final)
    wrong = _approvals(final)
    print("  under the Owner every changed acceptance names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == PLACEHOLDER_AT
    assert serialize_accepted_inputs(final) != simulated
    return simulated


def _state() -> tuple[str, AcceptedInputs]:
    """(state, inputs) of the artifact. Fails closed on anything but the prior
    or its one step result."""
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    at = _read_back(inputs)
    if at is None:
        if _sha(data) != PRIOR_SHA256:
            raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized prior")
        return "prior", inputs
    assert data == serialize_accepted_inputs(recorded(OWNER, at)), "drifted"
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
    print("  time (accepted, resolved)", _read_back(inputs))
    assert _sha(data) != SIMULATED_SHA256
    assert _read_back(inputs) != PLACEHOLDER_AT
    if state != "prior":
        wrong = _approvals(inputs)
        print("  every changed acceptance names the Owner and this decision", not wrong)
        assert not wrong, wrong[:5]
    _check(state, base, inputs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        assert serialize_accepted_inputs(load_accepted_inputs(path)) == data
    print("  reloads to the same bytes True")


def main(argv: list[str]) -> None:
    for path, sha in ((DELTA_FILE, DELTA_SHA256), (REVIEW_FILE, REVIEW_SHA256)):
        assert _sha(path.read_bytes()) == sha, path.name
    reviewed()
    combat()
    if argv == ["--simulate"]:
        base = saved_prior(ACCEPTED_PATH)
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    if argv[:1] == ["--verify"] and len(argv) <= 2:
        # The oracle is not tracked: the prior is its replay, or saved bytes.
        base = saved_prior(Path(argv[1])) if len(argv) == 2 else prior()
        state, inputs = _state()
        verify(state, base, inputs)
        return
    if argv != ["record-finite-reference-routes"]:
        raise SystemExit(
            "usage: --simulate | record-finite-reference-routes | --verify [prior]"
        )
    base = saved_prior(ACCEPTED_PATH)
    simulated = _precheck(base)
    at = _now()
    data = serialize_accepted_inputs(recorded(OWNER, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-finite-reference-routes", ACCEPTED_PATH.name, at)
    print("  sha256", _sha(data))
    # Read the written artifact back: it must rebuild from its recorded time.
    after, inputs = _state()
    assert after == "recorded", after
    verify(after, base, inputs)
    print("actual vs simulated: differing leaves (collection, field, sim, actual)")
    for key, n in sorted(sim_diff(simulated, data, at).items()):
        print("  ", n, key)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
