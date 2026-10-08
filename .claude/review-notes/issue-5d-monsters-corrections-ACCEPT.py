"""Owner acceptance of the Monsters-corrected replacement and the Monsters packet.

CRD Issue 5d, bounded Monsters source correction (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`), whose exact
replacement manifest is section 4 of :data:`MANIFEST` (SHA-256
:data:`MANIFEST_SHA256`), with :data:`APPROVAL`.

That decision authorizes exactly three native actions, in this order, each over
the previous result, and each reading the UTC clock when it runs:

1. ``record``: the fresh twenty-batch chain and its 1,099 resolutions of
   ``issue-5d-monsters-corrections-REPLACEMENT.py`` (:data:`REPLACEMENT_SHA256`),
   over no prior (1250 records, 6450 spans, 950 review units), into the new
   :data:`ACCEPTED_PATH`.
2. ``accept-monsters``: :func:`accept_proposal` of the whole Monsters proposal
   (:data:`MONSTERS_FILE_SHA256`, identity :data:`MONSTERS_IDENTITY`) over step 1.
3. ``resolve-monsters``: :func:`resolve_references` with its 83 drafts, drafted
   over step 1's chain and held to :data:`MONSTERS_DRAFTS_SHA256`.

The other 317 reference findings stay; nothing here publishes or activates. The
accepted ``srd-5-2-1-corpus-574662e9-0ef.json`` binds the superseded release and
is historical input: it is neither read as a prior nor rewritten. ``--verify``
reads the step times back from the artifact and rebuilds it, so the recorded
bytes reproduce, and checks every acceptance names the Owner and this decision.
Any artifact state other than absent or one of the three step results fails
closed. The executed times and the bytes after each step are pinned in
:data:`RECORDED_AT` and :data:`RECORDED_SHA256`; :func:`recorded` rebuilds the
twenty-batch chain from them.

``record``, ``accept-monsters`` and ``resolve-monsters`` each refuse unless the
artifact is in the state before them, and first run the remaining steps in
memory under the simulated reviewer so a drafts mismatch surfaces before bytes
are written.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal  # noqa: E402
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


#: The approved composition script, used as it was reviewed: its batches,
#: proposals, drafts and native steps, never its simulated evidence.
REPLACEMENT_FILE = HERE / "issue-5d-monsters-corrections-REPLACEMENT.py"
REPLACEMENT_SHA256 = "fb11995a067bd52ca5227508d4a7da7be0059b901789c9a82d76b3c9a0cdc568"
assert (
    hashlib.sha256(REPLACEMENT_FILE.read_bytes()).hexdigest() == REPLACEMENT_SHA256
), REPLACEMENT_FILE.name
REPLACEMENT = _load("monsters_corrections_replacement", REPLACEMENT_FILE)

RELEASE: tuple[str, str] = REPLACEMENT.RELEASE
ACCEPTED_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
BATCH_IDS = tuple(b for b, _, _ in REPLACEMENT.BATCHES)

MONSTERS_BATCH_ID: str = REPLACEMENT.MONSTERS_BATCH_ID
MONSTERS_FILE: Path = REPLACEMENT.MONSTERS_FILE
MONSTERS_FILE_SHA256: str = REPLACEMENT.MONSTERS_FILE_SHA256
MONSTERS_IDENTITY: str = REPLACEMENT.MONSTERS_IDENTITY
MONSTERS_DRAFTS_FILE: Path = REPLACEMENT.MONSTERS_DRAFTS_FILE
MONSTERS_DRAFTS_SHA256: str = REPLACEMENT.MONSTERS_DRAFTS_SHA256
#: Every Monsters draft id carries this suffix, and none of the chain's 1,099.
MONSTERS_SUFFIX = "-monsters-1"

SIMULATED_REVIEWER: str = REPLACEMENT.SIMULATED_REVIEWER
SIMULATED_RULE: str = REPLACEMENT.SIMULATED_RULE
SIMULATED_AT: str = REPLACEMENT.SIMULATED_AT

#: The Owner is the reviewer, the authorizer and the executor.
OWNER = "Ravenlok (Owner)"
OWNER_REVIEW = "monsters-corrections-owner-review.md"
OWNER_REVIEW_SHA256 = "8b9437d9e11a230973217152b626b3b8306bc54738100abc70db995f9124958b"
#: The exact replacement manifest the Owner review names (its section 4).
MANIFEST = "issue-5d-monsters-corrections-integration-review.md"
MANIFEST_SHA256 = "3a6ef7259ca4c9c57096a4fd2fb01e8d4d9e215ca3633916a0d2a29bb232dd17"
#: The Owner's decision, verbatim; the rule of every batch it accepts.
APPROVAL = (
    "I accept both exact items in the corrected Monsters packet and approve "
    "their reference resolutions, retaining 317 reference findings and the "
    "partial-publication block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}), "
    f"exact replacement manifest {MANIFEST} section 4 (SHA-256 {MANIFEST_SHA256}), "
    f"{REPLACEMENT_FILE.name} (SHA-256 {REPLACEMENT_SHA256}), "
    f"{MONSTERS_FILE.name} (SHA-256 {MONSTERS_FILE_SHA256}, identity "
    f"{MONSTERS_IDENTITY}) and {MONSTERS_DRAFTS_FILE.name} (SHA-256 "
    f"{MONSTERS_DRAFTS_SHA256}): {APPROVAL!r}"
)

#: What each step must produce: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int] | None]] = {
    "chain": ((20, 1250, 6450, 950, 1099), (315, 4003)),
    "monsters-accepted": ((21, 1664, 9589, 1364, 1099), None),
    "resolved": ((21, 1664, 9589, 1364, 1182), (317, 864)),
}
STATES = tuple(EXPECTED)

#: The executed step times (chain, Monsters accepted, Monsters resolved), as the
#: recording wrote them, and the artifact bytes after each step.
RECORDED_AT: tuple[str, ...] = (
    "2026-09-28T09:39:56Z",
    "2026-09-28T09:41:27Z",
    "2026-09-28T09:42:23Z",
)
RECORDED_SHA256: dict[str, str] = {
    "chain": "86652ac92dd9eae2f2d40388594ad41e8c63f8aa51dd9145044659d6f0d149fa",
    "monsters-accepted": (
        "57c23b57e9d90aa7fef971a7128822652969036c8b5f626fba8e3f274c93edfa"
    ),
    "resolved": "02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


#: The names the per-batch tests read, as the earlier recordings exposed them.
ACCEPTED_AT = RECORDED_AT[0]
TAG: str = REPLACEMENT.TAG
BATCHES = REPLACEMENT.BATCHES
DRAFTS = REPLACEMENT.DRAFTS
drafts_path = REPLACEMENT.drafts_path
_preserved = REPLACEMENT._preserved


def owner_chain(at: str, through: str | None = None) -> AcceptedInputs:
    """Step 1 under the Owner's decision at ``at``, whole or ``through`` a batch."""
    inputs: AcceptedInputs = REPLACEMENT.chain(
        OWNER, APPROVAL, AUTHORIZATION_REFERENCE, at, through=through
    )
    return inputs


def recorded() -> AcceptedInputs:
    """The recorded twenty-batch chain, rebuilt from its recorded time.

    It is the prior the Monsters steps composed over, and is never read back
    from the artifact, which now also holds them.
    """
    inputs = owner_chain(RECORDED_AT[0])
    assert _sha(serialize_accepted_inputs(inputs)) == RECORDED_SHA256["chain"]
    return inputs


def monsters_accepted(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 2: the Monsters proposal, accepted whole, over the chain."""
    assert _sha(MONSTERS_FILE.read_bytes()) == MONSTERS_FILE_SHA256, MONSTERS_FILE.name
    proposal = load_proposal(MONSTERS_FILE, expected_identity=MONSTERS_IDENTITY)
    assert proposal.binding == base.oracle.binding
    return accept_proposal(
        proposal,
        batch_id=MONSTERS_BATCH_ID,
        rule=APPROVAL if reviewer == OWNER else SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=reviewer,
        accepted_at=at,
        prior=base,
    )


def monsters_resolved(
    base: AcceptedInputs, accepted: AcceptedInputs, reviewer: str, at: str
) -> AcceptedInputs:
    """Step 3: the reviewed drafts, drafted over the chain ``base``, over step 2."""
    drafts = REPLACEMENT.generator("monsters").draft_resolutions(
        base.oracle.binding, prior=base
    )
    raw = MONSTERS_DRAFTS_FILE.read_bytes()
    assert _sha(raw) == MONSTERS_DRAFTS_SHA256, MONSTERS_DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert len(drafts) == 83, len(drafts)
    assert all(d.resolution_id.endswith(MONSTERS_SUFFIX) for d in drafts)
    reference = AUTHORIZATION_REFERENCE if reviewer == OWNER else SIMULATED_RULE
    inputs: AcceptedInputs = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by=reviewer,
        authorization_reference=reference,
        reviewer=reviewer,
        resolved_at=at,
    )
    return inputs


def _one(values: set[str], what: str) -> str:
    assert len(values) == 1, f"{what}: {sorted(values)}"
    return next(iter(values))


def _is_monsters(resolution_id: str) -> bool:
    return resolution_id.endswith(MONSTERS_SUFFIX)


def _read_back(inputs: AcceptedInputs) -> tuple[str, str | None, str | None]:
    """The executed step times recorded in ``inputs``: chain, accepted, resolved."""
    chain_at = _one(
        {a.accepted_at for a in inputs.acceptances if a.batch_id in BATCH_IDS}
        | {
            a.accepted_at
            for a in inputs.review_unit_acceptances
            if a.batch_id in BATCH_IDS
        }
        | {
            a.resolved_at
            for a in inputs.reference_resolution_acceptances
            if not _is_monsters(a.resolution_id)
        },
        "chain times",
    )
    acc = {
        a.accepted_at
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id == MONSTERS_BATCH_ID
    }
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_monsters(a.resolution_id)
    }
    return (
        chain_at,
        _one(acc, "monsters accepted_at") if acc else None,
        _one(res, "monsters resolved_at") if res else None,
    )


def _state() -> tuple[str, AcceptedInputs | None, AcceptedInputs | None]:
    """(state, chain, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but absent or one of the three step results.
    """
    if not ACCEPTED_PATH.exists():
        return "absent", None, None
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    # Batches serialize in canonical order, so they are compared as sets.
    got = sorted(b.batch_id for b in inputs.batches)
    chain_only = got == sorted(BATCH_IDS)
    if not chain_only and got != sorted((*BATCH_IDS, MONSTERS_BATCH_ID)):
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {got}")
    chain_at, acc_at, res_at = _read_back(inputs)
    base = owner_chain(chain_at)
    result: AcceptedInputs
    if chain_only and not acc_at and not res_at:
        state, result = "chain", base
    elif not chain_only and acc_at and not res_at:
        state, result = "monsters-accepted", monsters_accepted(base, OWNER, acc_at)
    elif not chain_only and acc_at and res_at:
        state = "resolved"
        result = monsters_resolved(
            base, monsters_accepted(base, OWNER, acc_at), OWNER, res_at
        )
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every acceptance that does not name the Owner and this one decision."""
    rules = {b.batch_id: b.rule for b in inputs.batches}
    wrong = [f"batch {b}: rule {r!r}" for b, r in rules.items() if r != APPROVAL]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.reviewer != OWNER or a.batch_id not in rules
    ]
    wrong += [
        f"resolution {a.resolution_id}"
        for a in inputs.reference_resolution_acceptances
        if (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    return wrong


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    counts: tuple[int, int, int, int, int] = REPLACEMENT._counts(inputs)
    return counts


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, chain preservation and findings for ``state``."""
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    )
    lost = REPLACEMENT._preserved(
        accepted_inputs_payload(base), accepted_inputs_payload(inputs)
    )
    print(state)
    print("  counts (batches, records, spans, units, resolutions)", _counts(inputs))
    print("  resolution violations", len(violations))
    print("  twenty-batch chain preserved", not lost, _counts(base))
    assert not violations, violations
    assert not lost, lost
    # The chain is a prefix: kept whole (above), and nothing of it duplicated.
    assert [b for b in inputs.batches if b.batch_id != MONSTERS_BATCH_ID] == list(
        base.batches
    )
    for got, want in (
        (inputs.acceptances, base.acceptances),
        (inputs.review_unit_acceptances, base.review_unit_acceptances),
    ):
        assert sum(a.batch_id != MONSTERS_BATCH_ID for a in got) == len(want)
    assert sum(
        not _is_monsters(a.resolution_id)
        for a in inputs.reference_resolution_acceptances
    ) == len(base.reference_resolution_acceptances)
    assert _counts(base) == EXPECTED["chain"][0], _counts(base)
    counts, findings = EXPECTED[state]
    assert _counts(inputs) == counts, _counts(inputs)
    if findings is not None:
        got = REPLACEMENT._findings(inputs)
        assert got == findings, got


def _precheck(base: AcceptedInputs) -> None:
    """The Monsters steps, in memory under the simulated reviewer, over ``base``."""
    step2 = monsters_accepted(base, SIMULATED_REVIEWER, SIMULATED_AT)
    _check("monsters-accepted", base, step2)
    _check(
        "resolved",
        base,
        monsters_resolved(base, step2, SIMULATED_REVIEWER, SIMULATED_AT),
    )


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        assert _sha(serialize_accepted_inputs(base)) == RECORDED_SHA256["chain"]
        n = STATES.index(state) + 1
        assert _read_back(inputs) == tuple(
            (*RECORDED_AT[:n], *(None,) * (3 - n))
        ), "not the recorded times"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  times (chain, accepted, resolved)", _read_back(inputs))
    wrong = _approvals(inputs)
    print("  every acceptance names the Owner and this decision", not wrong)
    assert not wrong, wrong[:5]
    _check(state, base, inputs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        assert serialize_accepted_inputs(load_accepted_inputs(path)) == data
    print("  reloads to the same bytes True")


def main(argv: list[str]) -> None:
    if argv == ["--simulate"]:
        base = REPLACEMENT.simulated()
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("chain", base, base)
        _precheck(base)
        return
    state, base, inputs = _state()
    if argv == ["--verify"]:
        if base is None or inputs is None:
            raise SystemExit(f"{ACCEPTED_PATH.name} is {state}")
        verify(state, base, inputs)
        return
    steps = {
        "record": "absent",
        "accept-monsters": "chain",
        "resolve-monsters": "monsters-accepted",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | record | accept-monsters | resolve-monsters | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["record"]:
        _precheck(REPLACEMENT.simulated())
        result = owner_chain(_now())
    elif argv == ["accept-monsters"]:
        assert base is not None
        _precheck(base)
        result = monsters_accepted(base, OWNER, _now())
    else:
        assert base is not None and inputs is not None
        result = monsters_resolved(base, inputs, OWNER, _now())
    data = serialize_accepted_inputs(result)
    ACCEPTED_PATH.write_bytes(data)
    print(argv[0], ACCEPTED_PATH.name, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, base, inputs = _state()
    assert after == dict(zip(steps, STATES, strict=True))[argv[0]], after
    assert base is not None and inputs is not None
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
