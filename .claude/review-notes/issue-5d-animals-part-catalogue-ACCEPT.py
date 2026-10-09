"""Owner acceptance of the Animals part catalogue and its four drafts.

CRD Issue 5d Animals part catalogue (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`, evidence pinned in
:data:`OWNER_MANIFEST`, SHA-256 :data:`OWNER_MANIFEST_SHA256`) with
:data:`APPROVAL`, verbatim.

The acceptance module has no supersession, so the changed Animals batch is
recorded as a fresh chain over no prior, as the reviewed
``issue-5d-animals-part-catalogue-REPLACEMENT.py`` (:data:`CONSTRUCTOR_SHA256`)
composes it: the twenty-two recorded proposals in their recorded order, each
with its recorded evidence and resolutions, the Animals batch alone taking the
reviewed candidate (:data:`PROPOSAL_SHA256`); then the 29 recorded
remaining-references resolutions at their recorded time. That decision
authorizes exactly two native writes, in this order, each reading the UTC clock
when it runs:

1. ``record-animals``: that chain, the Animals batch under the Owner with
   :data:`APPROVAL` as its rule.
2. ``resolve-animals``: :func:`resolve_references` with the four reviewed
   drafts (:data:`DRAFTS_SHA256`) under the Owner.

The prior (:data:`PRIOR_SHA256`) is rebuilt through
``issue-5d-remaining-references-ACCEPT.py`` from its recorded times, never read
back from the artifact. The candidate and drafts are read from their pinned
files; the constructor already rebuilt them from the release. Before any write,
:func:`_precheck` holds the same composition under the simulated reviewer to
the reviewed simulated bytes (:data:`SIMULATED_SHA256`), and runs every
post-write check on the composition under the Owner at a placeholder time, so
the Owner's evidence (not the simulated one) is what those checks see. Any
artifact state other than the prior or one of the two step results fails
closed. The other 64 reference findings and 28 uncovered leaves stay; nothing
here publishes or activates, and the release order is not corrected (tracked,
not certified).
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
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    _reference_resolution,
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


#: The reviewed constructor, used as it was reviewed (its rows, section and
#: files, never its simulated evidence), and through it the
#: remaining-references recording, the prior's authority.
CONSTRUCTOR = HERE / "issue-5d-animals-part-catalogue-REPLACEMENT.py"
CONSTRUCTOR_SHA256 = "3fd3da99f4792555b3488e0778c5cb212e5ed47055c92bae98dbe70d7ea30b24"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
APC = _load("animals_part_catalogue_replacement", CONSTRUCTOR)
REMAINING = APC.REMAINING
RR = REMAINING.RR
REPL = REMAINING.REPL

ACCEPTED_PATH: Path = REMAINING.ACCEPTED_PATH
PRIOR_SHA256: str = REMAINING.RECORDED_SHA256["resolved"]
assert PRIOR_SHA256 == APC.ACCEPTED_SHA256

BATCH = "animals"
#: The recorded Animals proposal the candidate replaces.
REPLACED_IDENTITY = "19685bc2b3c9a22d484b0435ba78950185dab00590a58bae36c8f41ca2fb53cd"
PROPOSAL_FILE: Path = APC.PROPOSAL_FILE
PROPOSAL_SHA256 = "7f067f7417ad0dd69fd6f86410b2f6704aacc92ffb955e4c3383413597b1425d"
IDENTITY = "228726d29769fcdb88e874c79b1a0685c8e1b18c59ce538011d8978d57645e38"
DRAFTS_FILE: Path = APC.DRAFTS_FILE
DRAFTS_SHA256 = "371dadb97b21a831e2c383bcb6602e14ce69cf143060aa123f2b8ef648e7be87"
#: Every new draft id carries this suffix, and none of the prior's 1,434.
SUFFIX: str = APC.SUFFIX
#: The reviewed full-text, order-aware delta, evidence blanked.
DELTA_FILE: Path = APC.DELTA_FILE
DELTA_SHA256 = "801678436a0fbf9a770d093e881bbb68b18d0ec34e9f21b511e89393fadfa813"
#: The reviewed composition with simulated approval, never a recorded hash.
SIMULATED_SHA256 = "e702cbc427716695bf54dc7ef2b0dc6d76f8e03d57104b166aed06e0fd6080f4"

SIMULATED_REVIEWER: str = APC.SIMULATED_REVIEWER
SIMULATED_RULE: str = APC.SIMULATED_RULE
SIMULATED_AT: str = APC.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = REMAINING.OWNER
OWNER_REVIEW = "animals-part-catalogue-owner-review.md"
OWNER_REVIEW_SHA256 = "01aeb9796dd71b7e721169c68dbacc5f26b38416c0a16f9a92837e977485a053"
OWNER_MANIFEST = "animals-part-catalogue-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "f779c986f3a351bbabec70fe2bf9a5a44c2261b076b349868b7dc15b4670d223"
)
#: The Owner's acceptance, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept the exact Animals catalogue replacement proposal and its four "
    "reference resolutions, retaining 64 reference findings, 28 uncovered "
    "leaves, and the partial-publication block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}, SHA-256 {OWNER_MANIFEST_SHA256}), {CONSTRUCTOR.name} "
    f"(SHA-256 {CONSTRUCTOR_SHA256}; candidate {PROPOSAL_FILE.name}, SHA-256 "
    f"{PROPOSAL_SHA256}, identity {IDENTITY}) and {DRAFTS_FILE.name} (SHA-256 "
    f"{DRAFTS_SHA256}), replacing the {BATCH} batch of {ACCEPTED_PATH.name} "
    f"(SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int]]] = {
    "prior": ((22, 1832, 10484, 1459, 1434), (68, 29)),
    "animals-recorded": ((22, 1833, 10485, 1460, 1434), (68, 28)),
    "resolved": ((22, 1833, 10485, 1460, 1438), (64, 28)),
}
STATES = tuple(EXPECTED)

#: The executed step times (recorded, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, ...] = ("2026-09-29T10:41:28Z", "2026-09-29T10:44:29Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "animals-recorded": (
        "8af13cb727ec941dc5c36229fd6d731d43fbb66fa0661e2b4c6336065237b4f4"
    ),
    "resolved": "96e90f71ddde22da6424eef9875b51eb36620876dfee635546e1d6872594a91b",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The recorded chain, rebuilt through the remaining-references recording."""
    if not _PRIOR:
        inputs: AcceptedInputs = REMAINING.recorded()
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def recorded() -> AcceptedInputs:
    """The recorded chain, rebuilt from its recorded times."""
    inputs = resolved(composed(OWNER, RECORDED_AT[0]), OWNER, RECORDED_AT[1])
    assert _sha(serialize_accepted_inputs(inputs)) == RECORDED_SHA256["resolved"]
    return inputs


def candidate() -> MechanicalProposal:
    """The reviewed candidate, read from its pinned file."""
    assert _sha(PROPOSAL_FILE.read_bytes()) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal: MechanicalProposal = load_proposal(
        PROPOSAL_FILE, expected_identity=IDENTITY
    )
    return proposal


def composed(reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: the reviewed composition (``APC.composed``) over the recorded
    evidence of the Equipment recording (``REMAINING.prior()``, which the
    remaining-references recording composed over) and that recording's own,
    the candidate accepted by ``reviewer`` at ``at``.

    The same loop as the reviewed composition; only the evidence of the
    Animals batch is a parameter. :func:`_precheck` holds it to the reviewed
    bytes.
    """
    animals = candidate()
    base = REMAINING.prior()
    changed = REMAINING.proposals()
    per, res = REPL._evidence(base)
    steps = RR._steps(base, rekeyed=True)
    inputs: AcceptedInputs | None = None

    def resolve(step: tuple[Any, ...]) -> AcceptedInputs:
        assert inputs is not None
        (ev,) = {
            (
                res[r.resolution_id].authorized_by,
                res[r.resolution_id].authorization_reference,
                res[r.resolution_id].reviewer,
                res[r.resolution_id].resolved_at,
            )
            for r in step
        }
        return resolve_references(
            inputs,
            resolutions=step,
            authorized_by=ev[0],
            authorization_reference=ev[1],
            reviewer=ev[2],
            resolved_at=ev[3],
        )

    seen = False
    for batch, proposal in REPL._proposals():
        assert proposal.binding == base.oracle.binding, batch
        rule, who, when = per[batch]
        if batch in changed:
            proposal = changed[batch]
            rule = REMAINING.APPROVAL
            who, when = REMAINING.OWNER, REMAINING.RECORDED_AT[0]
        if batch == BATCH:
            seen = True
            proposal = animals
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
        if steps.get(batch):
            inputs = resolve(steps[batch])
    assert seen
    inputs = resolve(steps["equipment-cited"])
    result: AcceptedInputs = REMAINING.resolved(
        base, inputs, REMAINING.OWNER, REMAINING.RECORDED_AT[1]
    )
    return result


def drafts() -> tuple[ReferenceResolution, ...]:
    """The four reviewed drafts, read from their pinned file by the loader's
    own strict parser and held to its bytes."""
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    payload = json.loads(raw)
    out = tuple(_reference_resolution(item, i) for i, item in enumerate(payload))
    assert list(reference_resolution_payload(out)) == payload
    # The payload is in canonical order, not review order.
    assert sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in out
    ) == sorted(APC.ROWS)
    assert all(
        r.resolution_id.endswith(SUFFIX) and r.target_record_key == APC.SECTION_KEY
        for r in out
    )
    return out


def resolved(step1: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 2: the four reviewed drafts over step 1."""
    reference = AUTHORIZATION_REFERENCE if reviewer == OWNER else SIMULATED_RULE
    inputs: AcceptedInputs = resolve_references(
        step1,
        resolutions=drafts(),
        authorized_by=reviewer,
        authorization_reference=reference,
        reviewer=reviewer,
        resolved_at=at,
    )
    return inputs


def _one(values: set[str], what: str) -> str:
    assert len(values) == 1, f"{what}: {sorted(values)}"
    return next(iter(values))


def _is_new(resolution_id: str) -> bool:
    return resolution_id.endswith(SUFFIX)


def _acceptances(inputs: AcceptedInputs) -> list[Any]:
    """Every span and review-unit acceptance."""
    return [*inputs.acceptances, *inputs.review_unit_acceptances]


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: recorded, resolved."""
    (identity,) = {b.proposal_identity for b in inputs.batches if b.batch_id == BATCH}
    if identity == REPLACED_IDENTITY:
        return None, None
    assert identity == IDENTITY, identity
    acc = {a.accepted_at for a in _acceptances(inputs) if a.batch_id == BATCH}
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_new(a.resolution_id)
    }
    return (
        _one(acc, "animals accepted_at"),
        _one(res, "new resolutions resolved_at") if res else None,
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
    new = any(_is_new(r.resolution_id) for r in inputs.oracle.reference_resolutions)
    result: AcceptedInputs
    if not acc_at and not new:
        state, result = "prior", base
    elif acc_at and not res_at and not new:
        state, result = "animals-recorded", composed(OWNER, acc_at)
    elif acc_at and res_at:
        state = "resolved"
        result = resolved(composed(OWNER, acc_at), OWNER, res_at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every new acceptance that does not name the Owner and this decision."""
    wrong = [
        f"batch {b.batch_id}: rule {b.rule!r}"
        for b in inputs.batches
        if b.batch_id == BATCH and b.rule != APPROVAL
    ]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in _acceptances(inputs)
        if a.batch_id == BATCH and a.reviewer != OWNER
    ]
    wrong += [
        f"resolution {a.resolution_id}"
        for a in inputs.reference_resolution_acceptances
        if _is_new(a.resolution_id)
        and (a.reviewer, a.authorized_by, a.authorization_reference)
        != (OWNER, OWNER, AUTHORIZATION_REFERENCE)
    ]
    return wrong


def _kept(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Every unchanged item of ``base`` that ``inputs`` does not hold exactly,
    evidence included, or holds twice: the 21 other batches' acceptances, and
    all 1,434 recorded resolutions with their records (the Animals recording's
    own included)."""
    old = accepted_inputs_payload(base)
    new = accepted_inputs_payload(inputs)
    out = []
    for path in (
        ("acceptance", "batches"),
        ("acceptance", "records"),
        ("acceptance", "review_unit_records"),
        ("acceptance", "reference_resolution_records"),
        ("reference_resolutions",),
    ):
        resolutions = "resolution" in path[-1]

        def kept(item: dict[str, Any], resolutions: bool = resolutions) -> bool:
            if resolutions:
                return not _is_new(str(item["resolution_id"]))
            return bool(item["batch_id"] != BATCH)

        a = Counter(REPL._key(x) for x in REPL._at(old, path) if kept(x))
        b = Counter(REPL._key(x) for x in REPL._at(new, path) if kept(x))
        if resolutions:
            assert sum(a.values()) == EXPECTED["prior"][0][4], path
        out += [f"{'.'.join(path)} lost {k[:200]}" for k in (a - b).elements()]
        out += [f"{'.'.join(path)} added {k[:200]}" for k in (b - a).elements()]
    return out


def _reowned(inputs: AcceptedInputs) -> tuple[int, int]:
    """(span, review-unit) acceptances of the Animals batch: each re-recorded
    under this decision, the replaced proposal's evidence kept in the prior."""
    return (
        sum(a.batch_id == BATCH for a in inputs.acceptances),
        sum(a.batch_id == BATCH for a in inputs.review_unit_acceptances),
    )


def _expectations(base: AcceptedInputs, inputs: AcceptedInputs) -> tuple[int, ...]:
    """(reviewed, derived, lost, added) expected rules per span; the one added
    is the heading's, under the part's record."""
    reviewed, derived = RR.expectations(base), RR.expectations(inputs)
    added = derived - reviewed
    assert {(u, r, c, f) for u, r, c, f, _ in added} <= {
        ("animals/animals", APC.SECTION_KEY, APC.SECTION, "")
    }, added
    return (
        sum(reviewed.values()),
        sum(derived.values()),
        sum((reviewed - derived).values()),
        sum(added.values()),
    )


def _blank(line: str) -> str:
    return str(REMAINING._authorizer_blank(line))


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
        # Batch order is the recorded order; only the Animals identity changes.
        before = [(b.batch_id, b.proposal_identity) for b in base.batches]
        after = [(b.batch_id, b.proposal_identity) for b in inputs.batches]
        assert [b for b, _ in before] == [b for b, _ in after]
        assert [x for x in after if x[0] != BATCH] == [
            x for x in before if x[0] != BATCH
        ]
        assert (BATCH, REPLACED_IDENTITY) in before and (BATCH, IDENTITY) in after
        lost = _kept(base, inputs)
        print(
            "  21 other batches and 1434 resolutions kept, evidence included,"
            " none twice",
            not lost,
        )
        assert not lost, lost[:5]
        print("  animals acceptances re-recorded (spans, units)", _reowned(inputs))
        ex = _expectations(base, inputs)
        print("  expectations per span (reviewed, derived, lost, added)", ex)
        assert ex == (10432, 10433, 0, 1), ex
    if state == "resolved":
        # The reviewed DELTA blanks REPL.EVIDENCE only, so it carries the
        # simulated authorizer of the four drafts; blank that on both sides.
        report: list[str] = REPL.Delta(base, inputs).report()
        raw = DELTA_FILE.read_bytes()
        assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
        reviewed = raw.decode("utf-8").rstrip("\n").split("\n")
        same = [_blank(x) for x in report] == [_blank(x) for x in reviewed]
        print(
            "  delta (evidence and authorizer blanked) is the reviewed DELTA,"
            " line for line",
            same,
            len(report),
        )
        assert same
    got = REPL._findings(inputs)
    print("  reference, uncovered-leaf findings", got, "other 0")
    assert got == EXPECTED[state][1], got
    dangling = RR.dangling_component_claims(inputs)
    assert not dangling, dangling[:5]


def _precheck(base: AcceptedInputs) -> None:
    """Before any write: under the simulated reviewer both steps are the
    reviewed composition, byte for byte; under the Owner, at a placeholder
    time, every post-write check passes on the Owner's own evidence."""
    simulated = resolved(
        composed(SIMULATED_REVIEWER, SIMULATED_AT),
        SIMULATED_REVIEWER,
        SIMULATED_AT,
    )
    got = _sha(serialize_accepted_inputs(simulated))
    print(
        "  simulated bytes", got, "(reviewed; never recorded)", got == SIMULATED_SHA256
    )
    assert got == SIMULATED_SHA256
    step1 = composed(OWNER, PLACEHOLDER_AT)
    _check("animals-recorded", base, step1)
    final = resolved(step1, OWNER, PLACEHOLDER_AT)
    _check("resolved", base, final)
    wrong = _approvals(final)
    print("  under the Owner every new acceptance names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == (PLACEHOLDER_AT, PLACEHOLDER_AT)
    assert _sha(serialize_accepted_inputs(final)) != SIMULATED_SHA256


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
    assert _sha(data) != SIMULATED_SHA256
    assert PLACEHOLDER_AT not in _read_back(inputs)
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
        "record-animals": "prior",
        "resolve-animals": "animals-recorded",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | record-animals | resolve-animals | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["record-animals"]:
        _precheck(base)
        result = composed(OWNER, _now())
    else:
        result = resolved(inputs, OWNER, _now())
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
