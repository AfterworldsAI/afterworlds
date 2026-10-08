"""Owner acceptance of the two Playing the Game replacement proposals.

CRD Issue 5d Playing the Game atoms (#132, #137). The Owner answered the
reviewed packet ``issue-5d-playing-the-game-atoms-review.md``
(:data:`REVIEW_SHA256`; the five files pinned in :data:`OWNER_MANIFEST`,
SHA-256 :data:`OWNER_MANIFEST_SHA256`) with :data:`APPROVAL`, verbatim.

The acceptance module has no supersession, so the two changed batches are
recorded as a fresh chain over no prior, as the reviewed
``issue-5d-playing-the-game-atoms-REPLACEMENT.py`` (:data:`CONSTRUCTOR_SHA256`)
composes it: the twenty-four recorded batches in their recorded order and at
their recorded evidence (the four other finite-reference batches at the
Owner's finite-reference acceptance), every recorded resolution step
re-applied verbatim, the two of :data:`PROPOSALS` taking the reviewed
candidates under the Owner with :data:`APPROVAL` as their rule. That decision
authorizes exactly one native write, ``record-playing-the-game-atoms``,
reading the UTC clock once when it runs. No resolution is drafted, re-keyed
or dropped.

The prior (:data:`PRIOR_SHA256`) is the finite-reference atoms recording; the
oracle is not tracked, so after the write :func:`prior` exists only as its
replay through ``issue-5d-finite-reference-atoms-ACCEPT.py``, which
``--verify`` and the tests use. Before the write, :func:`_precheck` holds the
simulated composition to the reviewed bytes (:data:`SIMULATED_SHA256`) and
runs every post-write check on the Owner's evidence at a placeholder time. Any
artifact state other than the prior or its one step result fails closed. The
other 49 reference findings and the partial-publication block stay; nothing
here publishes or activates, and the release order is not corrected (tracked,
not certified).
"""

from __future__ import annotations

import hashlib
import importlib.util
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


#: The reviewed constructor, used as it was reviewed (its edits, files and
#: chain, never its simulated evidence), and through it the recorded chain.
CONSTRUCTOR = HERE / "issue-5d-playing-the-game-atoms-REPLACEMENT.py"
CONSTRUCTOR_SHA256 = "23a9442c19eb0a39e01a351da1b89a41b62730f0940983a1f93547b77bcc8ea9"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
PGA = _load("playing_the_game_atoms_replacement", CONSTRUCTOR)
FINITE_REFERENCE = PGA.ACC
CHARACTER_CREATION = PGA.CHARACTER_CREATION
FRAMING = PGA.FRAMING
ANIMALS_CATALOGUE = PGA.ANIMALS_CATALOGUE
APC = PGA.APC
REMAINING = PGA.REMAINING
RR = PGA.RR
REPL = PGA.REPL

ACCEPTED_PATH: Path = FINITE_REFERENCE.ACCEPTED_PATH
PRIOR_SHA256: str = FINITE_REFERENCE.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == PGA.ACCEPTED_SHA256

#: batch -> (identity the Owner review names, proposal file SHA-256).
PROPOSALS: dict[str, tuple[str, str]] = {
    "core-play-dependencies": (
        "9aa7d0097fcf4cd64cbed630828eeca72606fc9c1818cde42a44f106accf6eac",
        "7a2344959a133319b60d720b7eab9d407c5c34907b5c585952a969bec510d210",
    ),
    "monsters": (
        "d6eff4f4858efd5da983dbdbbce85c2b9ddd6d20ed810c10d044087b3b66f91d",
        "69de9bc2875f0fed9483654d296a3ff3480f13da8a87345143d4a90d3640b633",
    ),
}
assert set(PROPOSALS) == set(PGA.EDITS)
#: The reviewed full-text delta, evidence blanked, and the reviewed packet.
DELTA_FILE: Path = PGA.DELTA_FILE
DELTA_SHA256 = "e34690675925d6a08ff233e479104a531255e4e7c2fda06dee4045ebf28ef8b9"
REVIEW_FILE = HERE / "issue-5d-playing-the-game-atoms-review.md"
REVIEW_SHA256 = "cc90bad0ae7a14dbe5487dd0151eafe03aaa5af5a803c609064f09763fa9a8f5"
#: The reviewed composition with simulated approval, never a recorded hash.
SIMULATED_SHA256 = "7254578d708261c14e3a33935e505af01a4a0b0c15b8c73c84e23db134d25a08"

SIMULATED_REVIEWER: str = PGA.SIMULATED_REVIEWER
SIMULATED_RULE: str = PGA.SIMULATED_RULE
SIMULATED_AT: str = PGA.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = FINITE_REFERENCE.OWNER
OWNER_MANIFEST = "playing-the-game-atoms-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "27271be7f3b14f7b6111da5f46d26751f842c2eb6773894ed253f7bbd10a679d"
)
#: The Owner's acceptance, verbatim; the rule of every batch it accepts.
APPROVAL = (
    "I accept the exact two Playing the Game replacement proposals, retaining "
    "49 reference findings, zero uncovered leaves, and the partial-publication "
    "block."
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int]]] = {
    "prior": ((24, 1835, 10492, 1476, 1440), (52, 0)),
    "recorded": ((24, 1835, 10492, 1476, 1440), (49, 0)),
}
STATES = tuple(EXPECTED)
#: The findings the two candidates clear; no other finding moves.
CLEARED = Counter(
    f"reference {e.scope}:{e.pointer!r}: unresolved reference"
    for es in PGA.EDITS.values()
    for e in es
)

#: The executed write time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: str | None = "2026-09-30T05:09:01Z"
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "92b7a68fcd6ea622ac3ef79b1dacd939f7be52fa445fcbdafd5adc8c77352e19",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The finite-reference atoms recording, rebuilt from its recorded time."""
    if not _PRIOR:
        fr = FINITE_REFERENCE
        inputs: AcceptedInputs = fr.composed(fr.OWNER, fr.RECORDED_AT)
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def loaded_prior() -> AcceptedInputs:
    """The committed file as loaded, while it is still the prior."""
    assert _sha(ACCEPTED_PATH.read_bytes()) == PRIOR_SHA256, "not the prior"
    return load_accepted_inputs(ACCEPTED_PATH)


def proposals() -> dict[str, MechanicalProposal]:
    """The two candidates, read from their pinned files."""
    out = {}
    for batch, (identity, sha) in PROPOSALS.items():
        path = PGA.proposal_file(batch)
        assert _sha(path.read_bytes()) == sha, path.name
        out[batch] = load_proposal(path, expected_identity=identity)
    return out


def composed(reviewer: str, at: str) -> AcceptedInputs:
    """The recorded chain, the two candidates accepted by ``reviewer`` at
    ``at`` in their recorded places.

    The same loop as the reviewed ``PGA.composed``; only the evidence of the
    changed batches is a parameter. :func:`_precheck` holds it to the reviewed
    bytes.
    """
    changed = proposals()
    fr = FINITE_REFERENCE
    recorded = fr.proposals()
    base = REMAINING.prior()
    remaining = REMAINING.proposals()
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

    seen = set()
    for batch, proposal in REPL._proposals():
        assert proposal.binding == base.oracle.binding, batch
        rule, who, when = per[batch]
        if batch in remaining:
            proposal = remaining[batch]
            rule = REMAINING.APPROVAL
            who, when = REMAINING.OWNER, REMAINING.RECORDED_AT[0]
        if batch == ANIMALS_CATALOGUE.BATCH:
            proposal = ANIMALS_CATALOGUE.candidate()
            rule = ANIMALS_CATALOGUE.APPROVAL
            who, when = ANIMALS_CATALOGUE.OWNER, ANIMALS_CATALOGUE.RECORDED_AT[0]
        if batch in recorded:
            proposal = recorded[batch]
            rule, who, when = fr.APPROVAL, fr.OWNER, fr.RECORDED_AT
        if batch in changed:
            seen.add(batch)
            proposal = changed[batch]
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
    assert seen == set(changed), seen
    inputs = resolve(steps["equipment-cited"])
    inputs = REMAINING.resolved(base, inputs, REMAINING.OWNER, REMAINING.RECORDED_AT[1])
    inputs = ANIMALS_CATALOGUE.resolved(
        inputs, ANIMALS_CATALOGUE.OWNER, ANIMALS_CATALOGUE.RECORDED_AT[1]
    )
    inputs = FRAMING.composed(inputs, FRAMING.OWNER, FRAMING.RECORDED_AT[0])
    cc = CHARACTER_CREATION
    inputs = cc.composed(inputs, cc.OWNER, cc.RECORDED_AT[0])
    return cc.resolved(inputs, cc.OWNER, cc.RECORDED_AT[1])  # type: ignore[no-any-return]


def _acceptances(inputs: AcceptedInputs) -> list[Any]:
    """Every span and review-unit acceptance."""
    return [*inputs.acceptances, *inputs.review_unit_acceptances]


def _read_back(inputs: AcceptedInputs) -> str | None:
    """The executed write time recorded in ``inputs``, if the two candidates
    are its batches; None if neither is."""
    identities = {b.batch_id: b.proposal_identity for b in inputs.batches}
    if all(identities[b] != i for b, (i, _) in PROPOSALS.items()):
        return None
    assert all(identities[b] == i for b, (i, _) in PROPOSALS.items()), identities
    acc = {a.accepted_at for a in _acceptances(inputs) if a.batch_id in PROPOSALS}
    assert len(acc) == 1, sorted(acc)
    return str(next(iter(acc)))


def _state() -> tuple[str, AcceptedInputs]:
    """(state, inputs) of the artifact, after checking its bytes. Fails closed
    on anything but the prior or its one step result."""
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    got = sorted(b.batch_id for b in inputs.batches)
    if len(got) != EXPECTED["prior"][0][0] or not set(PROPOSALS) <= set(got):
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {got}")
    at = _read_back(inputs)
    if at is None:
        if _sha(data) != PRIOR_SHA256:
            raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized prior")
        return "prior", inputs
    assert data == serialize_accepted_inputs(composed(OWNER, at)), "drifted"
    return "recorded", inputs


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every acceptance of a changed batch that does not name the Owner and
    this decision."""
    wrong = [
        f"batch {b.batch_id}: rule {b.rule!r}"
        for b in inputs.batches
        if b.batch_id in PROPOSALS and b.rule != APPROVAL
    ]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in _acceptances(inputs)
        if a.batch_id in PROPOSALS and a.reviewer != OWNER
    ]
    return wrong


def _kept(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Every item of ``base`` outside the two changed batches that ``inputs``
    does not hold exactly, evidence included, or holds twice: the twenty-two
    unchanged batches' acceptances and all 1440 resolutions with their
    approval records."""
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
        a = Counter(
            REPL._key(x)
            for x in REPL._at(old, path)
            if x.get("batch_id") not in PROPOSALS
        )
        b = Counter(
            REPL._key(x)
            for x in REPL._at(new, path)
            if x.get("batch_id") not in PROPOSALS
        )
        out += [f"{'.'.join(path)} lost {k[:200]}" for k in (a - b).elements()]
        out += [f"{'.'.join(path)} added {k[:200]}" for k in (b - a).elements()]
    return out


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, findings, preservation and the reviewed delta."""
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
    found = APC.findings(inputs)
    refs = [f for f in found if f.startswith("reference ")]
    leaves = [f for f in found if f.startswith("leaf ")]
    print("  reference, uncovered-leaf findings", (len(refs), len(leaves)), end="")
    print(" other", len(found) - len(refs) - len(leaves))
    assert len(refs) + len(leaves) == len(found), found[:5]
    assert (len(refs), len(leaves)) == EXPECTED[state][1]
    if state == "prior":
        return
    # Finding order follows set iteration, so they are compared as multisets.
    old = Counter(APC.findings(base))
    gone, added = old - Counter(found), Counter(found) - old
    print("  findings cleared", sum(gone.values()), dict(gone), "| new", dict(added))
    assert gone == CLEARED and not added
    # Only the two identities change (a loaded artifact lists batches by id,
    # so order is checked on the in-memory chain in _precheck).
    before = sorted((b.batch_id, b.proposal_identity) for b in base.batches)
    after = sorted((b.batch_id, b.proposal_identity) for b in inputs.batches)
    assert [b for b, _ in before] == [b for b, _ in after]
    assert [x for x in after if x[0] not in PROPOSALS] == [
        x for x in before if x[0] not in PROPOSALS
    ]
    assert {b: i for b, i in after if b in PROPOSALS} == {
        b: i for b, (i, _) in PROPOSALS.items()
    }
    lost = _kept(base, inputs)
    print(
        "  twenty-two unchanged batches and 1440 resolutions kept, evidence"
        " included, none twice",
        not lost,
    )
    assert not lost, lost[:5]
    same = reference_resolution_payload(
        base.oracle.reference_resolutions
    ) == reference_resolution_payload(oracle.reference_resolutions)
    print("  resolutions verbatim, in order", same)
    assert same
    same = RR.owned(base) == RR.owned(inputs) and RR.expectations(
        base
    ) == RR.expectations(inputs)
    print("  prose bindings and reviewed expectations unchanged", same)
    assert same
    for overrides in ((), PGA.OVERRIDES[:1], PGA.OVERRIDES[1:]):
        same = RR.consumer(base, overrides) == RR.consumer(inputs, overrides)
        names = [x.override_id for x in overrides]
        print("  consumer reading unchanged", names, same)
        assert same
    report: list[str] = REPL.Delta(base, inputs).report()
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    same = report == raw.decode("utf-8").rstrip("\n").split("\n")
    print("  delta (evidence blanked) is the reviewed DELTA, line for line", same)
    print("   ", len(report), "lines")
    assert same


def _precheck(base: AcceptedInputs) -> None:
    """Before any write: under the simulated reviewer the composition is the
    reviewed one, byte for byte; under the Owner, at a placeholder time, every
    post-write check passes on the Owner's own evidence."""
    simulated = serialize_accepted_inputs(composed(SIMULATED_REVIEWER, SIMULATED_AT))
    print("  simulated bytes", _sha(simulated), "(reviewed; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256
    final = composed(OWNER, PLACEHOLDER_AT)
    same = [b.batch_id for b in prior().batches] == [b.batch_id for b in final.batches]
    print("  acceptance order is the recorded chain's", same)
    assert same
    _check("recorded", base, final)
    wrong = _approvals(final)
    print("  under the Owner every changed acceptance names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == PLACEHOLDER_AT
    assert serialize_accepted_inputs(final) != simulated


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        expected = RECORDED_AT if state == "recorded" else None
        assert _read_back(inputs) == expected, "not the recorded time"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  time (accepted)", _read_back(inputs))
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
    for path, sha in (
        (DELTA_FILE, DELTA_SHA256),
        (REVIEW_FILE, REVIEW_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
    proposals()
    if argv == ["--simulate"]:
        base = loaded_prior()
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    if argv == ["--verify"]:
        # The oracle is not tracked: the prior is its replay.
        state, inputs = _state()
        verify(state, prior(), inputs)
        return
    if argv != ["record-playing-the-game-atoms"]:
        raise SystemExit("usage: --simulate | record-playing-the-game-atoms | --verify")
    state, _ = _state()
    if state != "prior":
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not prior")
    base = loaded_prior()
    _precheck(base)
    at = _now()
    data = serialize_accepted_inputs(composed(OWNER, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-playing-the-game-atoms", ACCEPTED_PATH.name, at)
    print("  sha256", _sha(data))
    # Read the written artifact back: it must rebuild from its recorded time.
    after, inputs = _state()
    assert after == "recorded", after
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
