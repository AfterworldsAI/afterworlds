"""Owner acceptance of the thirteen-finding reference-routes batch.

CRD Issue 5d (#132, #137). The Owner answered the reviewed packet
``issue-5d-reference-alternatives-review.md`` (:data:`REVIEW_SHA256`; the
files pinned in :data:`OWNER_MANIFEST`) with :data:`APPROVAL`, verbatim. The
approval preceded the parent's fresh verification at :data:`APPROVAL_BEFORE`;
no more precise approval time is known or recorded. The same decision accepts
the bounded schema/route reconciliation (ADR-005d Decision 7 amendment) and
nothing else.

The batch is one native action over the recorded artifact, as the reviewed
``issue-5d-reference-alternatives-REPLACEMENT.py`` (:data:`CONSTRUCTOR_SHA256`)
composes it: ``resolve_references(..., lift_to=...)`` crosses the registered
``5d-lift-schema-16-to-17`` and appends the thirteen reviewed resolutions
(#4, #7-12, #17-20, #22, #40) the constructor's ``drafts`` builds, under the
Owner, reading the UTC clock once when it runs. Nothing is re-accepted,
re-keyed, reordered or carried forward; no batch changes.

The prior (:data:`PRIOR_SHA256`) is the Equipment class-eligibility
recording. The oracle is not tracked, so after the write the prior exists only
as its replay through ``issue-5d-equipment-class-eligibility-ACCEPT.py``
(:func:`prior`), or as a saved copy of its bytes passed to ``--verify``.
Before the write, :func:`_precheck` holds the simulated action to the reviewed
bytes (:data:`SIMULATED_SHA256`) and runs every post-write check on the
Owner's evidence at a placeholder time. Any artifact state other than the
prior or its one step result fails closed. 33 reference findings and the
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
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    lift_accepted_inputs,
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


#: The reviewed constructor, used as it was reviewed (its drafts and source
#: check, never its simulated evidence).
CONSTRUCTOR = HERE / "issue-5d-reference-alternatives-REPLACEMENT.py"
CONSTRUCTOR_SHA256 = "2d8f7094dc96120032aeae5c5bca7c3d4ca6c35e355ecbf9f1f7ee2baf152be8"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
HARNESS = _load("reference_alternatives_replacement", CONSTRUCTOR)
ECE = HARNESS.ECE
APC = HARNESS.APC

ACCEPTED_PATH: Path = HARNESS.ACCEPTED_PATH
PRIOR_SHA256: str = ECE.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == HARNESS.ACCEPTED_SHA256

#: The reviewed resolutions (metadata-free), delta and packet.
PROPOSAL_FILE: Path = HARNESS.PROPOSAL_FILE
PROPOSAL_SHA256 = "17c5ac2562d5c67bd6434290fa3affddc86d6cd1721b4c654eb76bcbb677b7f0"
DELTA_FILE: Path = HARNESS.DELTA_FILE
DELTA_SHA256 = "7e5de293c33b91e80346d4b263cc90d76a6d9eb74efedd0fb2a3e8dddfaf9bf0"
REVIEW_FILE = HERE / "issue-5d-reference-alternatives-review.md"
REVIEW_SHA256 = "0a2ca621ec8ad36a2ca29cd7666b96caeacd8df9089d14add77d1f1ffd8b5166"
#: The reviewed action under the simulated reviewer, never a recorded hash.
SIMULATED_SHA256 = "f5721870b057f6455b98ca17f9455ddfdab1c8207fa65b1181e98e6467dd0439"
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer and the authorizer.
OWNER: str = ECE.OWNER
#: Parent-verified outside the repository; its SHA-256 is not available here,
#: so none is pinned.
OWNER_MANIFEST = "owner-directed-reference-owner-manifest.json"
#: The Owner's acceptance, verbatim.
APPROVAL = (
    "I accept the exact 13-finding reference batch and its schema/route "
    "reconciliation, retaining 33 reference findings, zero uncovered leaves, "
    "and the partial-publication block."
)
#: The approval came before this time (the parent's fresh verification). It
#: is not an acceptance time and is never recorded.
APPROVAL_BEFORE = "2026-10-01T18:15:15Z"
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {REVIEW_FILE.name} (SHA-256 {REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}), {CONSTRUCTOR.name} (SHA-256 {CONSTRUCTOR_SHA256}; "
    f"{PROPOSAL_FILE.name}, SHA-256 {PROPOSAL_SHA256}; {DELTA_FILE.name}, "
    f"SHA-256 {DELTA_SHA256}), lifted 16 -> 17 and appended to "
    f"{ACCEPTED_PATH.name} (SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)

#: batches, records, spans, review units, resolutions; then reference,
#: uncovered-leaf and other findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int, int]]] = {
    "prior": ((24, 1835, 10492, 1476, 1440), (46, 0, 0)),
    "recorded": ((24, 1835, 10492, 1476, 1453), (33, 0, 0)),
}
ROWS, ROUTES, DESTINATIONS = 13, 132, 197

#: The executed write time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: str | None = "2026-10-01T19:01:31Z"
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "cc994e1badee3baf733d2df5d5c88903ad96b4ddd0172f52111ecdf0b4c1f190",
}

CURRENT = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The Equipment class-eligibility recording, rebuilt from its recorded
    time (a historical replay)."""
    if not _PRIOR:
        inputs: AcceptedInputs = ECE.composed(ECE.OWNER, ECE.RECORDED_AT)
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
    assert proposal["representation_schema"] == list(CURRENT)
    return proposal


def recorded(base: AcceptedInputs, at: str) -> AcceptedInputs:
    """The one native action: lift and append the reviewed resolutions,
    authorized and reviewed by the Owner at ``at``."""
    HARNESS._origin_feats(base)
    return resolve_references(
        base,
        lift_to=CURRENT,
        resolutions=HARNESS.drafts(base),
        authorized_by=OWNER,
        authorization_reference=AUTHORIZATION_REFERENCE,
        reviewer=OWNER,
        resolved_at=at,
    )


def _new(base: AcceptedInputs, inputs: AcceptedInputs) -> list[Any]:
    """The resolution-acceptance records ``inputs`` adds over ``base``."""
    old = {a.resolution_id for a in base.reference_resolution_acceptances}
    return [
        a for a in inputs.reference_resolution_acceptances if a.resolution_id not in old
    ]


def _read_back(base: AcceptedInputs, inputs: AcceptedInputs) -> str | None:
    """The executed write time ``inputs`` records for the batch; None if it
    adds no resolution over ``base``."""
    new = _new(base, inputs)
    if not new:
        return None
    (at,) = {a.resolved_at for a in new}
    return str(at)


def _approvals(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Every new resolution acceptance that does not name the Owner and this
    decision."""
    return [
        f"resolution {a.resolution_id}"
        for a in _new(base, inputs)
        if (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    o = inputs.oracle
    return (
        len(inputs.batches),
        len(o.representation.records),
        len(o.spans),
        len(o.review_units),
        len(o.reference_resolutions),
    )


def _findings(inputs: AcceptedInputs) -> tuple[list[str], tuple[int, int, int]]:
    found: list[str] = APC.findings(inputs)
    refs = sum(f.startswith("reference ") for f in found)
    leaves = sum(f.startswith("leaf ") for f in found)
    return found, (refs, leaves, len(found) - refs - leaves)


def _kept(lifted: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Every part of the no-decision lift that ``inputs`` does not hold
    exactly: all but the resolutions and their acceptance records equal, and
    those two keep every prior item verbatim with exactly the new ones added.
    The no-decision lift returns its lift record apart; the action appends it,
    so the acceptance lifts keep every prior one in order plus exactly one
    (whose identity :func:`_check` holds to the reviewed PROPOSAL)."""
    old = accepted_inputs_payload(lifted)
    new = accepted_inputs_payload(inputs)
    grown = {"reference_resolutions"}
    out = [k for k in old.keys() | new.keys() if k not in grown | {"acceptance"}]
    out = [f"{k} differs" for k in out if old.get(k) != new.get(k)]
    acc_old, acc_new = old["acceptance"], new["acceptance"]
    assert isinstance(acc_old, dict) and isinstance(acc_new, dict)
    lifts_old, lifts_new = acc_old["lifts"], acc_new["lifts"]
    assert isinstance(lifts_old, list) and isinstance(lifts_new, list)
    if lifts_new[: len(lifts_old)] != lifts_old or len(lifts_new) != len(lifts_old) + 1:
        out.append("acceptance.lifts is not the prior lifts plus one")
    grown_acc = {"reference_resolution_records", "lifts"}
    out += [
        f"acceptance.{k} differs"
        for k in acc_old.keys() | acc_new.keys()
        if k not in grown_acc and acc_old.get(k) != acc_new.get(k)
    ]
    for label, a, b in (
        (
            "reference_resolutions",
            old["reference_resolutions"],
            new["reference_resolutions"],
        ),
        (
            "acceptance.reference_resolution_records",
            acc_old["reference_resolution_records"],
            acc_new["reference_resolution_records"],
        ),
    ):
        assert isinstance(a, list) and isinstance(b, list)
        ca = Counter(json.dumps(x, sort_keys=True) for x in a)
        cb = Counter(json.dumps(x, sort_keys=True) for x in b)
        out += [f"{label} lost {k[:200]}" for k in (ca - cb).elements()]
        if sum((cb - ca).values()) != ROWS:
            out.append(f"{label} added {sum((cb - ca).values())}, not {ROWS}")
    return out


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
    print("  counts (batches, records, spans, units, resolutions)", _counts(inputs))
    assert _counts(base) == EXPECTED["prior"][0], _counts(base)
    assert _counts(inputs) == EXPECTED[state][0], _counts(inputs)
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
    print("  representation schema", schema)
    assert schema == CURRENT
    # The comparison baseline: the same crossing, with no decision.
    lifted, _ = lift_accepted_inputs(base, CURRENT)
    before, split = _findings(lifted)
    after, now = _findings(inputs)
    print("  findings (reference, uncovered-leaf, other)", split, "->", now)
    assert split == EXPECTED["prior"][1] and now == EXPECTED[state][1]
    gone, added = Counter(before) - Counter(after), Counter(after) - Counter(before)
    print("  findings cleared", sum(gone.values()), "| new", dict(added))
    assert sum(gone.values()) == ROWS and not added
    proposal = reviewed()
    new_lifts = [r.lift_id for r in inputs.lifts[len(base.lifts) :]]
    print("  lift appended", new_lifts)
    assert new_lifts == proposal["lift"]
    assert inputs.lifts[: len(base.lifts)] == base.lifts
    # Split by identity, not position: a loaded artifact holds its resolutions
    # in the payload's canonical (resolution_id) order, not append order.
    ids = {r.resolution_id for r in base.oracle.reference_resolutions}
    head = tuple(r for r in oracle.reference_resolutions if r.resolution_id in ids)
    tail = tuple(r for r in oracle.reference_resolutions if r.resolution_id not in ids)
    same = reference_resolution_payload(head) == reference_resolution_payload(
        base.oracle.reference_resolutions
    )
    print("  1440 resolutions verbatim, canonical order", same)
    assert same
    same = reference_resolution_payload(tail) == proposal["reference_resolutions"]
    print("  13 new resolutions are the reviewed PROPOSAL's, canonical order", same)
    assert same
    routes = sum(len({d.alternative_label for d in r.destinations}) for r in tail)
    dests = sum(len(r.destinations) for r in tail)
    print("  resolutions, routes, destinations", (len(tail), routes, dests))
    assert (len(tail), routes, dests) == (ROWS, ROUTES, DESTINATIONS)
    same = [b.batch_id for b in inputs.batches] == [b.batch_id for b in base.batches]
    same = same and inputs.batches == base.batches
    print("  24 batches, identities and approvals unchanged", same)
    assert same
    lost = _kept(lifted, inputs)
    print("  everything else as lifted; prior items kept, 13 + 13 added", not lost)
    assert not lost, lost[:5]
    old = {a.resolution_id for a in base.reference_resolution_acceptances}
    kept = [
        a for a in inputs.reference_resolution_acceptances if a.resolution_id in old
    ]
    same = kept == list(base.reference_resolution_acceptances)
    print("  1440 historical resolution approvals verbatim, in order", same)
    assert same
    delta = HARNESS._delta(lifted, inputs).encode("utf-8")
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    print("  delta is the reviewed DELTA, byte for byte", delta == raw)
    assert delta == raw


def _precheck(base: AcceptedInputs) -> None:
    """Before any write: under the simulated reviewer the action is the
    reviewed one, byte for byte; under the Owner, at a placeholder time, every
    post-write check passes on the Owner's own evidence."""
    simulated = serialize_accepted_inputs(HARNESS.resolved(base))
    print("  simulated bytes", _sha(simulated), "(reviewed; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256
    final = recorded(base, PLACEHOLDER_AT)
    _check("recorded", base, final)
    wrong = _approvals(base, final)
    print("  under the Owner every new resolution names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(base, final) == PLACEHOLDER_AT
    assert serialize_accepted_inputs(final) != simulated


def _state(base: AcceptedInputs) -> tuple[str, AcceptedInputs]:
    """(state, inputs) of the artifact over ``base``. Fails closed on anything
    but the prior or its one step result."""
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    if _sha(data) == PRIOR_SHA256:
        return "prior", load_accepted_inputs(ACCEPTED_PATH)
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    at = _read_back(base, inputs)
    if at is None:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized state")
    assert data == serialize_accepted_inputs(recorded(base, at)), "drifted"
    return "recorded", inputs


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        if state == "recorded":
            assert _read_back(base, inputs) == RECORDED_AT, "not the recorded time"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  time (resolved)", _read_back(base, inputs))
    assert _sha(data) != SIMULATED_SHA256
    assert _read_back(base, inputs) != PLACEHOLDER_AT
    if state != "prior":
        wrong = _approvals(base, inputs)
        print("  every new resolution names the Owner and this decision", not wrong)
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
    if argv != ["record-reference-alternatives"]:
        raise SystemExit(
            "usage: --simulate | record-reference-alternatives | --verify [prior]"
        )
    base = saved_prior(ACCEPTED_PATH)
    _precheck(base)
    at = _now()
    data = serialize_accepted_inputs(recorded(base, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-reference-alternatives", ACCEPTED_PATH.name, at)
    print("  sha256", _sha(data))
    # Read the written artifact back: it must rebuild from its recorded time.
    after, inputs = _state(base)
    assert after == "recorded", after
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
