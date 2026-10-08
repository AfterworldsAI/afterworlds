"""Owner acceptance of the framing-coverage batch.

CRD Issue 5d framing coverage (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`, evidence pinned in
:data:`OWNER_MANIFEST`, SHA-256 :data:`OWNER_MANIFEST_SHA256`) with
:data:`APPROVAL`, verbatim.

That decision authorizes exactly one native write, ``record-framing``: the
reviewed candidate (:data:`PROPOSAL_SHA256`, built by
``issue-5d-framing-coverage-generator.py``, :data:`GENERATOR_SHA256`) accepted
once by :func:`accept_proposal` over the committed inputs, under the Owner with
:data:`APPROVAL` as its rule, at the UTC clock when it runs. One batch is
appended; no accepted batch is replaced, no chain is rebuilt, and no reference
resolution is added.

The prior (:data:`PRIOR_SHA256`) is the Animals catalogue recording, rebuilt
through ``issue-5d-animals-part-catalogue-ACCEPT.py`` from its recorded times
(the oracle is not tracked, so after the write the prior exists only as that
replay). Before the write, :func:`_precheck` holds the composition over that
replay to the composition over the committed file as loaded, holds the
simulated composition to the reviewed bytes (:data:`SIMULATED_SHA256`) and the
reviewed DELTA, and runs every post-write check on the Owner's evidence at a
placeholder time. Any artifact state other than the prior or its one step
result fails closed. The 64 reference findings and the partial-publication
block stay; nothing here publishes or activates, and the release order is not
corrected (tracked, not certified).
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

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
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


#: The reviewed generator, used as it was reviewed (its files, findings and
#: report, never its simulated evidence).
GENERATOR = HERE / "issue-5d-framing-coverage-generator.py"
GENERATOR_SHA256 = "e64617cb220a615228220a588aacf3ef0cec15a9ae15360d48c539708b1bc56c"
assert _sha(GENERATOR.read_bytes()) == GENERATOR_SHA256, GENERATOR.name
GEN = _load("framing_coverage_generator", GENERATOR)
RR = GEN.RR
EQ = GEN.EQ
MC = GEN.MC
#: The Animals catalogue recording, the prior's authority.
ANIMALS_CATALOGUE = _load(
    "animals_part_catalogue_accept", HERE / "issue-5d-animals-part-catalogue-ACCEPT.py"
)

ACCEPTED_PATH: Path = GEN.ACCEPTED_PATH
PRIOR_SHA256: str = ANIMALS_CATALOGUE.RECORDED_SHA256["resolved"]
assert PRIOR_SHA256 == GEN.ACCEPTED_SHA256

BATCH: str = GEN.BATCH_ID
PROPOSAL_FILE: Path = GEN.PROPOSAL_FILE
PROPOSAL_SHA256 = "5589a26251db0c62cb55f09afb8f9f1075ccb53fc4a2fceeca7be34cdc1fcb51"
IDENTITY = "a7a98598b751dd495b28312b854cf16c4bd7db06739c56bee662c84bd6107a70"
#: The reviewed full-text delta and unit report, evidence blanked.
DELTA_FILE: Path = GEN.DELTA_FILE
DELTA_SHA256 = "67d6f798df81f47760bbb3b2ca204becf9213481acbb1532386ba39d9ac95ca7"
REVIEW_FILE = HERE / "issue-5d-framing-coverage-review.md"
REVIEW_SHA256 = "f460a9570b1f6158b6bee2c770f4942631a0bbd43e927e9a0c531b215544dd1e"
#: The reviewed composition with simulated approval, never a recorded hash.
SIMULATED_SHA256 = "0c7e85079ca56a7b6f7c79cf880ca378ee0409a2d442b640a3f17568b59b0097"

SIMULATED_REVIEWER: str = GEN.SIMULATED_REVIEWER
SIMULATED_RULE: str = GEN.SIMULATED_RULE
SIMULATED_AT: str = GEN.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = ANIMALS_CATALOGUE.OWNER
OWNER_REVIEW = "framing-coverage-owner-review.md"
OWNER_REVIEW_SHA256 = "7ed0ef9cddd70c592076f1c769c089fc4313a3d7b44594d7c72dd6134b130511"
OWNER_MANIFEST = "framing-coverage-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "461bf0e412221c3f95ad18df48766d89ab29f99fc0a7bf602bfbb99a781fd2cc"
)
#: The Owner's acceptance, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept the exact framing-coverage proposal, including its glossary "
    "conventions and reviewed framing exclusions."
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int]]] = {
    "prior": ((22, 1833, 10485, 1460, 1438), (64, 28)),
    "recorded": ((23, 1834, 10491, 1475, 1438), (64, 0)),
}
STATES = tuple(EXPECTED)

#: The executed step time, as the recording wrote it, and the artifact bytes
#: in each state.
RECORDED_AT: tuple[str, ...] = ("2026-09-29T12:47:38Z",)
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "15478aa5ea712b9946999ff865283cd12b36dd4f917137a76c225543066b8922",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The Animals catalogue recording, rebuilt from its recorded times."""
    if not _PRIOR:
        inputs: AcceptedInputs = ANIMALS_CATALOGUE.recorded()
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def candidate() -> MechanicalProposal:
    """The reviewed candidate, read from its pinned file."""
    assert _sha(PROPOSAL_FILE.read_bytes()) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal: MechanicalProposal = load_proposal(
        PROPOSAL_FILE, expected_identity=IDENTITY
    )
    return proposal


def composed(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """The candidate accepted once over ``base`` by ``reviewer`` at ``at``: the
    generator's own acceptance, only the evidence a parameter."""
    proposal = candidate()
    assert proposal.binding == base.oracle.binding
    inputs: AcceptedInputs = accept_proposal(
        proposal,
        batch_id=BATCH,
        rule=APPROVAL if reviewer == OWNER else SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=reviewer,
        accepted_at=at,
        prior=base,
    )
    return inputs


def _acceptances(inputs: AcceptedInputs) -> list[Any]:
    """Every span and review-unit acceptance."""
    return [*inputs.acceptances, *inputs.review_unit_acceptances]


def _read_back(inputs: AcceptedInputs) -> str | None:
    """The executed step time recorded in ``inputs``, if the batch is there."""
    acc = {a.accepted_at for a in _acceptances(inputs) if a.batch_id == BATCH}
    if not any(b.batch_id == BATCH for b in inputs.batches):
        assert not acc
        return None
    assert len(acc) == 1, sorted(acc)
    return str(next(iter(acc)))


def _state() -> tuple[str, AcceptedInputs, AcceptedInputs]:
    """(state, prior, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but the prior or its one step result.
    """
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    base = prior()
    # Batches serialize in canonical order, so they are compared as sets.
    got = sorted(b.batch_id for b in inputs.batches)
    before = sorted(b.batch_id for b in base.batches)
    at = _read_back(inputs)
    result: AcceptedInputs
    if got == before and at is None:
        state, result = "prior", base
    elif got == sorted([*before, BATCH]) and at:
        state, result = "recorded", composed(base, OWNER, at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {got}")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _approvals(inputs: AcceptedInputs) -> list[str]:
    """Every acceptance of the batch that does not name the Owner and this
    decision."""
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
    return wrong


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, preservation, findings and the reviewed delta."""
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    )
    counts = MC._counts(inputs)
    print(state)
    print("  counts (batches, records, spans, units, resolutions)", counts)
    print("  resolution violations", len(violations))
    assert not violations, violations[:5]
    assert MC._counts(base) == EXPECTED["prior"][0], MC._counts(base)
    assert counts == EXPECTED[state][0], counts
    found = GEN.findings(inputs)
    refs = [f for f in found if f.startswith("reference ")]
    leaves = [f for f in found if f.startswith("leaf ")]
    print("  reference, uncovered-leaf findings", (len(refs), len(leaves)), end="")
    print(" other", len(found) - len(refs) - len(leaves))
    assert len(refs) + len(leaves) == len(found), found[:5]
    assert (len(refs), len(leaves)) == EXPECTED[state][1]
    dangling = RR.dangling_component_claims(inputs)
    assert not dangling, dangling[:5]
    if state == "prior":
        return
    old_refs = [f for f in GEN.findings(base) if f.startswith("reference ")]
    # Finding order follows set iteration, so they are compared as multisets.
    same = Counter(refs) == Counter(old_refs)
    print("  reference findings are the prior's, string for string", same)
    assert same
    # Every other batch is kept, identity included; one is appended.
    before = sorted((b.batch_id, b.proposal_identity) for b in base.batches)
    after = sorted((b.batch_id, b.proposal_identity) for b in inputs.batches)
    assert after == sorted([*before, (BATCH, IDENTITY)]), after
    lost = MC._preserved(accepted_inputs_payload(base), accepted_inputs_payload(inputs))
    print("  prior content lost or changed, evidence included", lost)
    assert not lost
    # The reviewed DELTA blanks evidence (reviewer, times, rule), so it holds
    # for the Owner's evidence as for the simulated one.
    delta = EQ.Delta(base, inputs)
    units = candidate().proposed_review_units
    report: list[str] = [*delta.report(), *GEN.unit_report(delta, units)]
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    same = report == raw.decode("utf-8").rstrip("\n").split("\n")
    print("  delta (evidence blanked) is the reviewed DELTA, line for line", same)
    print("   ", len(report), "lines")
    assert same
    assert not any(a for a, _ in delta.collections().values())
    unit_only = {leaf for u in units if not u.expected_rules for leaf in u.leaf_ids}
    spanned = {s["leaf_id"] for s in delta.new["spans"]}
    print("  spans on the 20 unit-only leaves", len(spanned & unit_only))
    assert len(unit_only) == 20 and not spanned & unit_only


def _precheck(base: AcceptedInputs) -> None:
    """Before any write: the replayed prior composes as the committed file
    does; under the simulated reviewer the step is the reviewed composition,
    byte for byte; under the Owner, at a placeholder time, every post-write
    check passes on the Owner's own evidence."""
    simulated = serialize_accepted_inputs(
        composed(base, SIMULATED_REVIEWER, SIMULATED_AT)
    )
    if _sha(ACCEPTED_PATH.read_bytes()) == PRIOR_SHA256:
        loaded = load_accepted_inputs(ACCEPTED_PATH)
        same = simulated == serialize_accepted_inputs(
            composed(loaded, SIMULATED_REVIEWER, SIMULATED_AT)
        )
        print("  composition over the replay = over the committed file", same)
        assert same
    print("  simulated bytes", _sha(simulated), "(reviewed; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256, "simulated bytes not pinned"
    final = composed(base, OWNER, PLACEHOLDER_AT)
    _check("recorded", base, final)
    wrong = _approvals(final)
    print("  under the Owner every new acceptance names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == PLACEHOLDER_AT
    assert serialize_accepted_inputs(final) != simulated


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        expected = RECORDED_AT[0] if state == "recorded" else None
        assert _read_back(inputs) == expected, "not the recorded time"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  time (recorded)", _read_back(inputs))
    assert _sha(data) != SIMULATED_SHA256
    assert _read_back(inputs) != PLACEHOLDER_AT
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
    for path, sha in (
        (PROPOSAL_FILE, PROPOSAL_SHA256),
        (DELTA_FILE, DELTA_SHA256),
        (REVIEW_FILE, REVIEW_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
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
    if argv != ["record-framing"]:
        raise SystemExit("usage: --simulate | record-framing | --verify")
    if state != "prior":
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not prior")
    _precheck(base)
    at = _now()
    data = serialize_accepted_inputs(composed(base, OWNER, at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-framing", ACCEPTED_PATH.name, at, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded time.
    after, base, inputs = _state()
    assert after == "recorded", after
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
