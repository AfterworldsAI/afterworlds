"""Owner acceptance of the Animals packet over the recorded Monsters authority.

CRD Issue 5d (#132, #137). The Owner answered :data:`OWNER_REVIEW` (SHA-256
:data:`OWNER_REVIEW_SHA256`) with :data:`OWNER_STATEMENT`, whose release-order
half is :data:`RELEASE_ORDER` (SHA-256 :data:`RELEASE_ORDER_SHA256`).

That decision authorizes exactly two native actions, in this order, each over
the previous result, and each reading the UTC clock when it runs:

1. ``accept-animals``: :func:`accept_proposal` of the whole Animals proposal
   (:data:`PROPOSAL_SHA256`, identity :data:`IDENTITY`) over the twenty-one
   batches ``issue-5d-monsters-corrections-ACCEPT.py`` recorded (the prior,
   :data:`PRIOR_SHA256`), appending 95 records.
2. ``resolve-animals``: :func:`resolve_references` with its 65 drafts, drafted
   over the prior and held to :data:`DRAFTS_SHA256`.

The other 252 reference findings stay; nothing here publishes or activates, and
the known cross-file release-order defect (Animals read before its governing
Monsters rules) is tracked, not corrected. The prior is rebuilt from the
Monsters recording's times, never read back from the artifact, which also holds
Animals once step 1 runs. Any artifact state other than the prior or one of the
two step results fails closed. The executed times and the bytes after each step
are pinned in :data:`RECORDED_AT` and :data:`RECORDED_SHA256`.

``accept-animals`` and ``resolve-animals`` each refuse unless the artifact is
in the state before them. ``accept-animals`` first runs both steps in memory
under the simulated reviewer; ``resolve-animals`` holds the drafts to their
reviewed bytes before any are written.
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


#: The Monsters recording, the prior's authority; and the Animals generator,
#: used for its drafts exactly as reviewed.
RECORDING = _load(
    "monsters_corrections_accept", HERE / "issue-5d-monsters-corrections-ACCEPT.py"
)
REPLACEMENT = RECORDING.REPLACEMENT
GEN = _load("issue_5d_animals_generator", HERE / "issue-5d-animals-generator.py")

ACCEPTED_PATH: Path = RECORDING.ACCEPTED_PATH
PRIOR_SHA256: str = RECORDING.RECORDED_SHA256["resolved"]
PRIOR_BATCH_IDS = (*RECORDING.BATCH_IDS, RECORDING.MONSTERS_BATCH_ID)

BATCH_ID = "animals"
PROPOSAL_FILE = HERE / "issue-5d-animals-PROPOSAL.json"
PROPOSAL_SHA256 = "a3057b73ec23db2bf169286446e25047ef7d54ebc96061083e3c9a2d48045ebb"
IDENTITY = "19685bc2b3c9a22d484b0435ba78950185dab00590a58bae36c8f41ca2fb53cd"
DRAFTS_FILE = HERE / "issue-5d-animals-resolutions-DRAFTS.json"
DRAFTS_SHA256 = "924ef579a879f73c1281d1263ba8c49f166302a11578808814a3d05f776766ac"
#: Every Animals draft id carries this suffix, and none of the prior's 1,182.
SUFFIX = "-animals-1"

SIMULATED_REVIEWER: str = REPLACEMENT.SIMULATED_REVIEWER
SIMULATED_RULE: str = REPLACEMENT.SIMULATED_RULE
SIMULATED_AT: str = REPLACEMENT.SIMULATED_AT

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = RECORDING.OWNER
OWNER_REVIEW = "animals-owner-review.md"
OWNER_REVIEW_SHA256 = "bb7a341bc6e3ca70f6d5afe911e961188613d8f045a6baff6710245cdf9e231a"
RELEASE_ORDER = "release-order-owner-decision.md"
RELEASE_ORDER_SHA256 = (
    "8854e1bc03692ea9601080e2319d291ccad291982d0ff8024b687be7e5548fce"
)
#: The Owner's acceptance, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept the exact Animals proposal and its 65 reference resolutions, "
    "retaining 252 reference findings and the partial-publication block."
)
#: The Owner's whole statement, verbatim.
OWNER_STATEMENT = (
    f"{APPROVAL} Furthermore, we will finish the packets, tracking the known "
    "cross-file ordering defects explicitly, then correct the release order in "
    "one bounded pass before publication or activation."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}) and "
    f"{RELEASE_ORDER} (SHA-256 {RELEASE_ORDER_SHA256}), {PROPOSAL_FILE.name} "
    f"(SHA-256 {PROPOSAL_SHA256}, identity {IDENTITY}) and {DRAFTS_FILE.name} "
    f"(SHA-256 {DRAFTS_SHA256}), over {ACCEPTED_PATH.name} (SHA-256 "
    f"{PRIOR_SHA256}): {OWNER_STATEMENT!r}"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int] | None]] = {
    "prior": ((21, 1664, 9589, 1364, 1182), (317, 864)),
    "animals-accepted": ((22, 1759, 10424, 1459, 1182), None),
    "resolved": ((22, 1759, 10424, 1459, 1247), (252, 29)),
}
STATES = tuple(EXPECTED)

#: The executed step times (accepted, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, ...] = ("2026-09-28T17:28:00Z", "2026-09-28T17:28:58Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "animals-accepted": (
        "bc11be6ee4dbc56d7f90d9d06d220cfc7ab4e31bcaaafaf84a27d78c15894f16"
    ),
    "resolved": "4ad85dab4ec9e5967779a0bb24f22c099e0aafdc9762088e340f7796b86290ba",
}


def recorded() -> AcceptedInputs:
    """The recorded twenty-two batches, rebuilt from their recorded times."""
    base = prior()
    inputs = resolved(
        base, accepted(base, OWNER, RECORDED_AT[0]), OWNER, RECORDED_AT[1]
    )
    assert _sha(serialize_accepted_inputs(inputs)) == RECORDED_SHA256["resolved"]
    return inputs


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def prior() -> AcceptedInputs:
    """The recorded twenty-one batches, rebuilt from the Monsters recording."""
    inputs: AcceptedInputs = GEN.current()
    assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
    return inputs


def accepted(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: the Animals proposal, accepted whole, over the prior."""
    assert _sha(PROPOSAL_FILE.read_bytes()) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal = load_proposal(PROPOSAL_FILE, expected_identity=IDENTITY)
    assert proposal.binding == base.oracle.binding
    return accept_proposal(
        proposal,
        batch_id=BATCH_ID,
        rule=APPROVAL if reviewer == OWNER else SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=reviewer,
        accepted_at=at,
        prior=base,
    )


def resolved(
    base: AcceptedInputs, step1: AcceptedInputs, reviewer: str, at: str
) -> AcceptedInputs:
    """Step 2: the reviewed drafts, drafted over the prior ``base``, over step 1."""
    drafts = GEN.draft_resolutions(base.oracle.binding, prior=base)
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert len(drafts) == 65, len(drafts)
    assert all(d.resolution_id.endswith(SUFFIX) for d in drafts)
    reference = AUTHORIZATION_REFERENCE if reviewer == OWNER else SIMULATED_RULE
    inputs: AcceptedInputs = resolve_references(
        step1,
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


def _is_animals(resolution_id: str) -> bool:
    return resolution_id.endswith(SUFFIX)


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: accepted, resolved."""
    acc = {
        a.accepted_at
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id == BATCH_ID
    }
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_animals(a.resolution_id)
    }
    return (
        _one(acc, "animals accepted_at") if acc else None,
        _one(res, "animals resolved_at") if res else None,
    )


def _state() -> tuple[str, AcceptedInputs, AcceptedInputs]:
    """(state, prior, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but the prior or one of the two step results.
    """
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    # Batches serialize in canonical order, so they are compared as sets.
    got = sorted(b.batch_id for b in inputs.batches)
    prior_only = got == sorted(PRIOR_BATCH_IDS)
    if not prior_only and got != sorted((*PRIOR_BATCH_IDS, BATCH_ID)):
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {got}")
    acc_at, res_at = _read_back(inputs)
    base = prior()
    result: AcceptedInputs
    if prior_only and not acc_at and not res_at:
        state, result = "prior", base
    elif not prior_only and acc_at and not res_at:
        state, result = "animals-accepted", accepted(base, OWNER, acc_at)
    elif not prior_only and acc_at and res_at:
        state = "resolved"
        result = resolved(base, accepted(base, OWNER, acc_at), OWNER, res_at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every Animals acceptance that does not name the Owner and this decision."""
    wrong = [
        f"batch {b.batch_id}: rule {b.rule!r}"
        for b in inputs.batches
        if b.batch_id == BATCH_ID and b.rule != APPROVAL
    ]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id == BATCH_ID and a.reviewer != OWNER
    ]
    wrong += [
        f"resolution {a.resolution_id}"
        for a in inputs.reference_resolution_acceptances
        if _is_animals(a.resolution_id)
        and (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    return wrong


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    counts: tuple[int, int, int, int, int] = REPLACEMENT._counts(inputs)
    return counts


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, prior preservation and findings for ``state``."""
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
    print("  twenty-one-batch prior preserved", not lost, _counts(base))
    assert not violations, violations
    assert not lost, lost
    # The prior is a prefix: kept whole (above), and nothing of it duplicated.
    assert [b for b in inputs.batches if b.batch_id != BATCH_ID] == list(base.batches)
    for got, want in (
        (inputs.acceptances, base.acceptances),
        (inputs.review_unit_acceptances, base.review_unit_acceptances),
    ):
        assert sum(a.batch_id != BATCH_ID for a in got) == len(want)
    assert sum(
        not _is_animals(a.resolution_id)
        for a in inputs.reference_resolution_acceptances
    ) == len(base.reference_resolution_acceptances)
    assert _counts(base) == EXPECTED["prior"][0], _counts(base)
    counts, findings = EXPECTED[state]
    assert _counts(inputs) == counts, _counts(inputs)
    if findings is not None:
        got = REPLACEMENT._findings(inputs)
        assert got == findings, got


def _precheck(base: AcceptedInputs) -> None:
    """The Animals steps, in memory under the simulated reviewer, over ``base``."""
    step1 = accepted(base, SIMULATED_REVIEWER, SIMULATED_AT)
    _check("animals-accepted", base, step1)
    _check("resolved", base, resolved(base, step1, SIMULATED_REVIEWER, SIMULATED_AT))


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        n = STATES.index(state)
        assert _read_back(inputs) == tuple(
            (*RECORDED_AT[:n], *(None,) * (2 - n))
        ), "not the recorded times"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  times (accepted, resolved)", _read_back(inputs))
    wrong = _approvals(inputs)
    print("  every Animals acceptance names the Owner and this decision", not wrong)
    assert not wrong, wrong[:5]
    _check(state, base, inputs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        assert serialize_accepted_inputs(load_accepted_inputs(path)) == data
    print("  reloads to the same bytes True")


def main(argv: list[str]) -> None:
    if argv == ["--simulate"]:
        base = prior()
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    state, base, inputs = _state()
    if argv == ["--verify"]:
        verify(state, base, inputs)
        return
    steps = {"accept-animals": "prior", "resolve-animals": "animals-accepted"}
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | accept-animals | resolve-animals | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["accept-animals"]:
        _precheck(base)
        result = accepted(base, OWNER, _now())
    else:
        result = resolved(base, inputs, OWNER, _now())
    data = serialize_accepted_inputs(result)
    ACCEPTED_PATH.write_bytes(data)
    print(argv[0], ACCEPTED_PATH.name, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, base, inputs = _state()
    assert after == STATES[STATES.index(state) + 1], after
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
