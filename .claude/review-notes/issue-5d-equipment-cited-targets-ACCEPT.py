"""Owner acceptance of the replacement Equipment proposal and its 161 drafts.

CRD Issue 5d Equipment cited-targets (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`, evidence pinned in
:data:`OWNER_MANIFEST`, SHA-256 :data:`OWNER_MANIFEST_SHA256`) with
:data:`APPROVAL`, verbatim.

The acceptance module has no supersession, so the changed Equipment batch is
recorded as a fresh chain over no prior, as the reviewed
``issue-5d-equipment-cited-targets-REPLACEMENT.py`` composes it: its own
proposals, recorded evidence and resolution steps, with only ``equipment``
taking the replacement proposal. That decision authorizes exactly two native
writes, in this order, each reading the UTC clock when it runs:

1. ``record-equipment``: the twenty-two batches over no prior, each of the 21
   unchanged proposals (byte-identical) with its recorded rule, reviewer and
   time and every recorded resolution re-applied verbatim after its batch;
   ``equipment`` takes :data:`PROPOSAL_SHA256` (identity :data:`IDENTITY`)
   under the Owner, with :data:`APPROVAL` as its rule.
2. ``resolve-equipment-cited``: :func:`resolve_references` with the 161
   reviewed drafts (:data:`DRAFTS_SHA256`) under the Owner.

The prior (:data:`PRIOR_SHA256`) is rebuilt through
``issue-5d-animals-ACCEPT.py`` from its recorded times, never read back from the
artifact. The recorded evidence each step re-applies is read from that rebuilt
prior. Any artifact state other than the prior or one of the two step results
fails closed. The other 91 reference findings stay; nothing here publishes or
activates, and the release order is not corrected (tracked, not certified).
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


#: The Animals recording, the prior's authority; the reviewed composition; and
#: the generator, used for its drafts exactly as reviewed.
ANIMALS = _load("animals_accept", HERE / "issue-5d-animals-ACCEPT.py")
REPL = _load(
    "equipment_cited_targets_replacement",
    HERE / "issue-5d-equipment-cited-targets-REPLACEMENT.py",
)
GEN = _load(
    "equipment_cited_targets_generator",
    HERE / "issue-5d-equipment-cited-targets-generator.py",
)

ACCEPTED_PATH: Path = ANIMALS.ACCEPTED_PATH
PRIOR_SHA256: str = ANIMALS.RECORDED_SHA256["resolved"]
BATCH_ID = "equipment"

PROPOSAL_FILE: Path = REPL.CANDIDATE
PROPOSAL_SHA256 = "13271e035f76316a6f78cf90ccca1f68ec233738ce31a93c7303052bc5bb02e0"
IDENTITY = "309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680"
DRAFTS_FILE: Path = REPL.CITED_DRAFTS
DRAFTS_SHA256 = "bfbf5a7ac78fa96fd568148d26bd2690415a4add9196d8ca393ef7b4f0c139eb"
#: Every new draft id carries this suffix, and none of the prior's 1,247.
SUFFIX: str = REPL.CITED_SUFFIX

SIMULATED_REVIEWER: str = REPL.SIMULATED_REVIEWER
SIMULATED_RULE: str = REPL.SIMULATED_RULE
SIMULATED_AT: str = REPL.SIMULATED_AT

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = ANIMALS.OWNER
OWNER_REVIEW = "equipment-cited-targets-owner-review.md"
OWNER_REVIEW_SHA256 = "248a8fc6f38e5e686357ec075a91a73c459022cbd2f88ecd769b04112da314e9"
OWNER_MANIFEST = "equipment-cited-targets-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "32da2d9e87231c64d0006916e39a73bac611e3d45d2b38899dba87ab7ae9459d"
)
#: The Owner's acceptance, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept the exact replacement Equipment proposal and its 161 reference "
    "resolutions, retaining 91 reference findings and the partial-publication "
    "block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}, SHA-256 {OWNER_MANIFEST_SHA256}), {PROPOSAL_FILE.name} "
    f"(SHA-256 {PROPOSAL_SHA256}, identity {IDENTITY}) and {DRAFTS_FILE.name} "
    f"(SHA-256 {DRAFTS_SHA256}), replacing the equipment batch of "
    f"{ACCEPTED_PATH.name} (SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int] | None]] = {
    "prior": ((22, 1759, 10424, 1459, 1247), (252, 29)),
    "equipment-recorded": ((22, 1826, 10484, 1459, 1247), None),
    "resolved": ((22, 1826, 10484, 1459, 1408), (91, 29)),
}
STATES = tuple(EXPECTED)

#: The executed step times (recorded, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, ...] = ("2026-09-28T21:51:03Z", "2026-09-28T21:52:52Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "equipment-recorded": (
        "a820243f7dd0e0d34cdad35dcfbc761ccf2e88eb82625b02a86d0848c1151fde"
    ),
    "resolved": "76a16103a08db564ee00b9c8d493d2f5dd48b05e312c77780dd3a74639da86ac",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The recorded twenty-two batches, rebuilt through the Animals recording."""
    if not _PRIOR:
        inputs: AcceptedInputs = ANIMALS.recorded()
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def recorded() -> AcceptedInputs:
    """The recorded chain, rebuilt from its recorded times."""
    base = prior()
    inputs = resolved(
        base, composed(base, OWNER, RECORDED_AT[0]), OWNER, RECORDED_AT[1]
    )
    assert _sha(serialize_accepted_inputs(inputs)) == RECORDED_SHA256["resolved"]
    return inputs


def composed(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: :func:`REPL.replayed` over ``base``'s recorded evidence, with the
    Equipment batch accepted by ``reviewer`` at ``at``.

    The same loop as the reviewed composition; only the Equipment evidence is a
    parameter. :func:`_precheck` holds it to the reviewed bytes.
    """
    assert _sha(PROPOSAL_FILE.read_bytes()) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    per, res = REPL._evidence(base)
    steps = REPL._steps(base)
    inputs: AcceptedInputs | None = None
    for batch, proposal in REPL._proposals():
        assert proposal.binding == base.oracle.binding, batch
        rule, who, when = per[batch]
        if batch == BATCH_ID:
            rule = APPROVAL if reviewer == OWNER else SIMULATED_RULE
            who, when = reviewer, at
        inputs = accept_proposal(
            proposal,
            batch_id=batch,
            rule=rule,
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            resolved_review_units=tuple(
                u.unit_id for u in proposal.proposed_review_units
            ),
            reviewer=who,
            accepted_at=when,
            prior=inputs,
        )
        if batch in steps:
            step = steps[batch]
            (ev,) = {
                (
                    res[r.resolution_id].authorized_by,
                    res[r.resolution_id].authorization_reference,
                    res[r.resolution_id].reviewer,
                    res[r.resolution_id].resolved_at,
                )
                for r in step
            }
            inputs = resolve_references(
                inputs,
                resolutions=step,
                authorized_by=ev[0],
                authorization_reference=ev[1],
                reviewer=ev[2],
                resolved_at=ev[3],
            )
    assert inputs is not None
    assert {b.batch_id: b.proposal_identity for b in inputs.batches}[BATCH_ID] == (
        IDENTITY
    )
    return inputs


def resolved(
    base: AcceptedInputs, step1: AcceptedInputs, reviewer: str, at: str
) -> AcceptedInputs:
    """Step 2: the 161 reviewed drafts over step 1."""
    drafts = GEN.draft_cited_resolutions(base.oracle.binding)
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert len(drafts) == 161, len(drafts)
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


def _is_cited(resolution_id: str) -> bool:
    return resolution_id.endswith(SUFFIX)


def _identity(inputs: AcceptedInputs) -> str:
    return _one(
        {b.proposal_identity for b in inputs.batches if b.batch_id == BATCH_ID},
        "equipment identity",
    )


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: recorded, resolved."""
    if _identity(inputs) != IDENTITY:
        return None, None
    acc = {
        a.accepted_at
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id == BATCH_ID
    }
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_cited(a.resolution_id)
    }
    return (
        _one(acc, "equipment accepted_at"),
        _one(res, "cited resolved_at") if res else None,
    )


def _state() -> tuple[str, AcceptedInputs, AcceptedInputs]:
    """(state, prior, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but the prior or one of the two step results.
    """
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    base = prior()
    # Batches serialize in canonical order, so they are compared as sets.
    got = sorted(b.batch_id for b in inputs.batches)
    if got != sorted(b.batch_id for b in base.batches):
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {got}")
    acc_at, res_at = _read_back(inputs)
    cited = any(_is_cited(r.resolution_id) for r in inputs.oracle.reference_resolutions)
    result: AcceptedInputs
    if not acc_at and not cited:
        state, result = "prior", base
    elif acc_at and not res_at and not cited:
        state, result = "equipment-recorded", composed(base, OWNER, acc_at)
    elif acc_at and res_at:
        state = "resolved"
        result = resolved(base, composed(base, OWNER, acc_at), OWNER, res_at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every new acceptance that does not name the Owner and this decision."""
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
        if _is_cited(a.resolution_id)
        and (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    return wrong


def _outside(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Every non-Equipment item that differs, evidence included (none may)."""
    delta = REPL.Delta(base, inputs)
    old = accepted_inputs_payload(base)
    new = accepted_inputs_payload(inputs)
    out = []
    for path in REPL.COLLECTIONS:
        a = Counter(REPL._key(x) for x in REPL._at(old, path) if not delta.equipment(x))
        b = Counter(REPL._key(x) for x in REPL._at(new, path) if not delta.equipment(x))
        out += [f"{'.'.join(path)} lost {k[:200]}" for k in (a - b).elements()]
        out += [f"{'.'.join(path)} added {k[:200]}" for k in (b - a).elements()]
    out += delta.kept_outside_equipment()
    before, after = delta.coverage()
    if before != after:
        out.append("Equipment's accepted text changed")
    return out


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, preservation and findings for ``state``."""
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    )
    counts = REPL._counts(inputs)
    print(state)
    print("  counts (batches, records, spans, units, resolutions)", counts)
    print("  resolution violations", len(violations))
    assert not violations, violations[:5]
    assert REPL._counts(base) == EXPECTED["prior"][0], REPL._counts(base)
    assert counts == EXPECTED[state][0], counts
    if state != "prior":
        lost = _outside(base, inputs)
        print("  outside Equipment kept, evidence included", not lost)
        assert not lost, lost[:5]
        # Nothing of the prior's evidence is recorded twice.
        for got, want in (
            (inputs.acceptances, base.acceptances),
            (inputs.review_unit_acceptances, base.review_unit_acceptances),
        ):
            assert sum(a.batch_id != BATCH_ID for a in got) == sum(
                a.batch_id != BATCH_ID for a in want
            )
        assert sum(
            not _is_cited(a.resolution_id)
            for a in inputs.reference_resolution_acceptances
        ) == len(base.reference_resolution_acceptances)
    findings = EXPECTED[state][1]
    if findings is not None:
        got = REPL._findings(inputs)
        print("  reference, uncovered-leaf findings", got, "other 0")
        assert got == findings, got


def _precheck(base: AcceptedInputs) -> None:
    """Both steps in memory under the simulated reviewer; step 1 is the
    reviewed composition, byte for byte."""
    step1 = composed(base, SIMULATED_REVIEWER, SIMULATED_AT)
    reviewed = REPL.replayed(base)
    same = serialize_accepted_inputs(step1) == serialize_accepted_inputs(reviewed)
    print("  step 1 is the reviewed REPLACEMENT composition, byte for byte", same)
    assert same
    _check("equipment-recorded", base, step1)
    final = resolved(base, step1, SIMULATED_REVIEWER, SIMULATED_AT)
    _check("resolved", base, final)
    print("  simulated bytes", _sha(serialize_accepted_inputs(final)))


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
    print("  times (recorded, resolved)", _read_back(inputs))
    if state != "prior":
        wrong = _approvals(inputs)
        print("  every new acceptance names the Owner and this decision", not wrong)
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
    steps = {
        "record-equipment": "prior",
        "resolve-equipment-cited": "equipment-recorded",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | record-equipment | resolve-equipment-cited | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["record-equipment"]:
        _precheck(base)
        result = composed(base, OWNER, _now())
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
