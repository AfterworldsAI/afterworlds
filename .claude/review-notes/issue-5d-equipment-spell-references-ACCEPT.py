"""Owner acceptance of the thirteen Equipment, cursed-item and spell references.

CRD Issue 5d (#132, #137). The Owner answered the reviewed candidate (the
packet :data:`REVIEW_SHA256`, the independent review :data:`OWNER_REVIEW_SHA256`)
with :data:`APPROVAL`, verbatim; ``issue-5d-equipment-spell-references-owner-
acceptance.md`` (:data:`ACCEPTANCE_SHA256`) records it and pins the artifacts.
The approval preceded Codex's verification at :data:`APPROVAL_BEFORE`; no more
precise approval time is known or recorded.

The recording is additive: no batch is replaced. It is the reviewed
``issue-5d-equipment-spell-references-CANDIDATE.py`` (:data:`CONSTRUCTOR_SHA256`)
action under the Owner: one ``resolve_references`` call over the prior with
the thirteen resolutions its ``drafts`` builds. One write,
``record-equipment-spell-references``, reads the UTC clock once; the thirteen
resolutions carry that time. Nothing else is re-accepted, re-keyed, reordered
or lifted.

The prior (:data:`PRIOR_SHA256`) is the finite-reference-routes recording. The
oracle is not tracked, so after the write the prior exists only as its replay
(:func:`prior`), or as a saved copy of its bytes passed to ``--verify``.
Before the write, :func:`_precheck` holds the simulated composition to the
reviewed bytes (:data:`SIMULATED_SHA256`) and runs every post-write check on
the Owner's evidence at a placeholder time. Any artifact state other than the
prior or its one step result fails closed. Ten reference findings and the
partial-publication block stay; nothing here publishes or activates, and the
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


#: The reviewed constructor, used as it was reviewed (its drafts and
#: preservation check, never its simulated evidence).
CONSTRUCTOR = HERE / "issue-5d-equipment-spell-references-CANDIDATE.py"
CONSTRUCTOR_SHA256 = "623f0509812dc64872d09f8fa98d09b07b9b5a6f28b197cdb451933817bd6b7e"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
HARNESS = _load("equipment_spell_references_candidate", CONSTRUCTOR)
#: The prior's recording script, for its replay and the Owner's name.
FRR = _load(
    "finite_reference_routes_accept",
    HERE / "issue-5d-finite-reference-routes-ACCEPT.py",
)
REPL = HARNESS.REPL
APC = HARNESS.APC

ACCEPTED_PATH: Path = HARNESS.ACCEPTED_PATH
PRIOR_SHA256: str = FRR.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == HARNESS.ACCEPTED_SHA256

#: The reviewed resolutions (metadata-free), delta, packets and acceptance.
PROPOSAL_FILE: Path = HARNESS.PROPOSAL_FILE
PROPOSAL_SHA256 = "b9bf5638902b2384da3875963f4846d794339e3656efd2c8321c4c6094d8056d"
DELTA_FILE: Path = HARNESS.DELTA_FILE
DELTA_SHA256 = "0e00a0d6cd7576ba43651f0b06d69062ed9e3ab7e40783b6bfc4ea48e2a8c601"
REVIEW_FILE = HERE / "issue-5d-equipment-spell-references-review.md"
REVIEW_SHA256 = "29caa23daee5eb78404d637ba8149bd4ebd2f4895f286a46646475b6bcfd646d"
OWNER_REVIEW_FILE = HERE / "issue-5d-equipment-spell-references-owner-review.md"
OWNER_REVIEW_SHA256 = "bd829a6c937efd994362da5946f754b99cba5bf92a5b325780ed663d0aa27d39"
ACCEPTANCE_FILE = HERE / "issue-5d-equipment-spell-references-owner-acceptance.md"
ACCEPTANCE_SHA256 = "de2a917bec119217fd2026214a732a8b76935b44e930d83bcb4820be34ca3e61"
#: The accepted reader correction and its tests. Checked before the write
#: only: later deferred work may change either without touching the oracle.
READER_FILE = REPO / "src/afterworlds/services/rules_authority/service.py"
READER_SHA256 = "4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d"
READER_TESTS_FILE = (
    REPO / "tests/ingestion/mechanical/test_equipment_spell_references_candidate.py"
)
READER_TESTS_SHA256 = "00111b870eb8f0c3e9fcc45da20ff2695fa6ac283c4b7a69abc876063fc7f8b5"
#: The reviewed composition under the simulated reviewer, never recorded.
SIMULATED_SHA256 = "faa46e9c5f4668bad2ed5ad764fccd9f1f8fb2f9471f5986186523961e418290"
SIMULATED_REVIEWER: str = HARNESS.SIMULATED_REVIEWER
SIMULATED_RULE: str = HARNESS.SIMULATED_RULE
SIMULATED_AT: str = HARNESS.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer and the authorizer.
OWNER: str = FRR.OWNER
#: The Owner's acceptance, verbatim.
APPROVAL = "I accept this exact thirteen-reference candidate and reader correction."
#: The approval came before this time (Codex's verification). It is not an
#: acceptance time and is never recorded.
APPROVAL_BEFORE = "2026-10-03T09:20:14Z"
AUTHORIZATION_REFERENCE = (
    f"Owner decision recorded in {ACCEPTANCE_FILE.name} (SHA-256 "
    f"{ACCEPTANCE_SHA256}) on {REVIEW_FILE.name} (SHA-256 {REVIEW_SHA256}) and "
    f"{OWNER_REVIEW_FILE.name} (SHA-256 {OWNER_REVIEW_SHA256}): "
    f"{CONSTRUCTOR.name} (SHA-256 {CONSTRUCTOR_SHA256}; {PROPOSAL_FILE.name}, "
    f"SHA-256 {PROPOSAL_SHA256}; {DELTA_FILE.name}, SHA-256 {DELTA_SHA256}; "
    f"simulated {SIMULATED_SHA256}), reader correction {READER_FILE.name} "
    f"(SHA-256 {READER_SHA256}), recorded over {ACCEPTED_PATH.name} (SHA-256 "
    f"{PRIOR_SHA256}): {APPROVAL!r}"
)

#: batches, records, spans, review units, resolutions; then reference,
#: uncovered-leaf and other findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int, int]]] = {
    "prior": ((24, 1835, 10493, 1476, 1463), (23, 0, 0)),
    "recorded": ((24, 1835, 10493, 1476, 1476), (10, 0, 0)),
}
ROWS, ROUTES, DESTINATIONS = 13, 15, 62
#: The evidence fields a recording may set; nothing else may differ from the
#: simulated composition.
EVIDENCE = {"reviewer", "authorized_by", "authorization_reference", "resolved_at"}

#: The executed write time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: str | None = "2026-10-03T09:30:23Z"
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The finite-reference-routes recording, rebuilt from its recorded time
    (a historical replay)."""
    if not _PRIOR:
        inputs: AcceptedInputs = FRR.recorded(FRR.OWNER, FRR.RECORDED_AT)
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
    """The one native action: the thirteen reviewed resolutions over ``base``,
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
    """The executed write time ``inputs`` records; None if none of the
    thirteen is recorded (the prior)."""
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
    for line in sorted(after):
        print("  remains", line[:200])
    new_ids = _new_ids()
    # Every accepted item verbatim; the only additions are the new
    # resolutions and their approvals; batches, batch acceptances, policy,
    # binding, schema and representation equal.
    changes = HARNESS._preserved(base, inputs, new_ids)
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
    # Split by identity, not position: a loaded artifact holds its resolutions
    # in the payload's canonical (resolution_id) order, not append order.
    head = tuple(
        r for r in oracle.reference_resolutions if r.resolution_id not in new_ids
    )
    tail = tuple(r for r in oracle.reference_resolutions if r.resolution_id in new_ids)
    same = reference_resolution_payload(head) == reference_resolution_payload(
        base.oracle.reference_resolutions
    )
    print("  1463 resolutions verbatim, canonical order", same)
    assert same
    kept = [
        a
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id not in new_ids
    ]
    same = kept == list(base.reference_resolution_acceptances)
    print("  1463 historical resolution approvals verbatim, in order", same)
    assert same
    same = reference_resolution_payload(tail) == reviewed()["reference_resolutions"]
    print("  13 new resolutions are the reviewed PROPOSAL's, canonical order", same)
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
        + HARNESS.FRR._delta(base, inputs)
    ).encode("utf-8")
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    # The delta blanks reviewer and resolved_at but shows a resolution's
    # authorizer and reference, so the reviewed (simulated) DELTA names the
    # simulation on the thirteen new resolution lines and nowhere else.
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
        "  delta is the reviewed DELTA, byte for byte, the thirteen new",
        "resolutions' authorizer and reference the Owner's",
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


def _precheck(base: AcceptedInputs) -> bytes:
    """Before any write: the accepted reader is in place; under the simulated
    reviewer the composition is the reviewed one, byte for byte; under the
    Owner, at a placeholder time, every post-write check passes on the
    Owner's own evidence. Returns the simulated bytes."""
    for path, sha in (
        (READER_FILE, READER_SHA256),
        (READER_TESTS_FILE, READER_TESTS_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
    print("  accepted reader correction and its tests in place True")
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
    assert data != simulated
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
    _check(state, base, inputs)
    assert serialize_accepted_inputs(load_accepted_inputs_bytes(data)) == data
    print("  reloads to the same bytes True")


def main(argv: list[str]) -> None:
    for path, sha in (
        (DELTA_FILE, DELTA_SHA256),
        (REVIEW_FILE, REVIEW_SHA256),
        (OWNER_REVIEW_FILE, OWNER_REVIEW_SHA256),
        (ACCEPTANCE_FILE, ACCEPTANCE_SHA256),
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
    if argv != ["record-equipment-spell-references"]:
        raise SystemExit(
            "usage: --simulate | record-equipment-spell-references | --verify [prior]"
        )
    base = saved_prior(ACCEPTED_PATH)
    simulated = _precheck(base)
    at = _now()
    data = serialize_accepted_inputs(recorded(base, OWNER, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-equipment-spell-references", ACCEPTED_PATH.name, at)
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
