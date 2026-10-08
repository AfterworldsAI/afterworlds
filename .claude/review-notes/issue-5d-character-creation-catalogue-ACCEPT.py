"""Owner acceptance of the Character Creation catalogue and its two drafts.

CRD Issue 5d remaining-references inventory #3 and #5 (#132, #137). The Owner
answered :data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`, evidence
pinned in :data:`OWNER_MANIFEST`, SHA-256 :data:`OWNER_MANIFEST_SHA256`) with
:data:`APPROVAL`, verbatim.

That decision authorizes exactly one native write,
``record-character-creation-catalogue``, of two native steps, each reading the
UTC clock when it runs:

1. the reviewed candidate (:data:`PROPOSAL_SHA256`, built by
   ``issue-5d-character-creation-catalogue-generator.py``,
   :data:`GENERATOR_SHA256`) accepted once by :func:`accept_proposal` over the
   committed inputs as loaded, under the Owner with :data:`APPROVAL` as its
   rule: one batch appended;
2. :func:`resolve_references` with the two reviewed drafts
   (:data:`DRAFTS_SHA256`) under the Owner.

No accepted batch or resolution is replaced and no chain is rebuilt for the
write. The prior (:data:`PRIOR_SHA256`) is the framing-coverage recording; the
oracle is not tracked, so after the write :func:`prior` exists only as its
replay through ``issue-5d-framing-coverage-ACCEPT.py``, which ``--verify`` and
the tests use. Before the write, :func:`_precheck` holds the simulated
composition to the reviewed bytes (:data:`SIMULATED_SHA256`) and runs every
post-write check on the Owner's evidence at a placeholder time. Any artifact
state other than the prior or its one step result fails closed. The other 62
reference findings and the partial-publication block stay; nothing here
publishes or activates, and the release order is not corrected (tracked, not
certified).
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
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    ProvenanceTargetKind,
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
GENERATOR = HERE / "issue-5d-character-creation-catalogue-generator.py"
GENERATOR_SHA256 = "7ffb2a6f969c5d7d23592b2cfc5e1cbd6c1367bef1239a2274b4d381e99c3433"
assert _sha(GENERATOR.read_bytes()) == GENERATOR_SHA256, GENERATOR.name
GEN = _load("character_creation_catalogue_generator", GENERATOR)
FC = GEN.FC
EQ = GEN.EQ
MC = GEN.MC
#: The framing-coverage recording, the prior's authority.
FRAMING = _load("framing_coverage_accept", HERE / "issue-5d-framing-coverage-ACCEPT.py")

ACCEPTED_PATH: Path = GEN.ACCEPTED_PATH
PRIOR_SHA256: str = FRAMING.RECORDED_SHA256["recorded"]
assert PRIOR_SHA256 == GEN.ACCEPTED_SHA256

BATCH: str = GEN.BATCH_ID
PROPOSAL_FILE: Path = GEN.PROPOSAL_FILE
PROPOSAL_SHA256 = "98864a96933a3c967d0728b5bc2252f12a2af5e43accadf89595325e363adc2c"
IDENTITY = "cee3b640f955a34ed627fb720b8f9ec121d605dda6f792ba469ebe7ac429a5be"
DRAFTS_FILE: Path = GEN.DRAFTS_FILE
DRAFTS_SHA256 = "47167c97d16436905aee4149be1c56d1ee7cc98ea8778696bdec46bdc1597ae5"
#: The reviewed full-text delta and membership report, evidence blanked.
DELTA_FILE: Path = GEN.DELTA_FILE
DELTA_SHA256 = "d48ce267966e85bb218f0bdfe4b25a0e89d0363e40a43148cf0d011a4c556dc8"
REVIEW_FILE = HERE / "issue-5d-character-creation-catalogue-review.md"
REVIEW_SHA256 = "2efbe02be979374f4c9e93c7e0552b151ac017cf18eb318a4284ee2ef2c925f0"
#: The reviewed composition with simulated approval, never a recorded hash.
SIMULATED_SHA256 = "5dc89b9585450040d1227f98831ea5b288d1c03daee7bafbafec345f02a982a9"

SIMULATED_REVIEWER: str = GEN.SIMULATED_REVIEWER
SIMULATED_RULE: str = GEN.SIMULATED_RULE
SIMULATED_AT: str = GEN.SIMULATED_AT
#: The time the pre-write checks compose the Owner's evidence at; never
#: recorded (a recording reads the clock).
PLACEHOLDER_AT = "2000-01-01T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = FRAMING.OWNER
OWNER_REVIEW = "character-creation-catalogue-owner-review.md"
OWNER_REVIEW_SHA256 = "8897f37bd8a5d5f1d5c7f44bdb290faad3545a98bae05601f90d1b3c53a87ffd"
OWNER_MANIFEST = "character-creation-catalogue-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "234eb06333f3b04d424639d9388a5757c92f36006ff44f6c93c7719d7b83db1b"
)
#: The Owner's acceptance, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept the exact Character Creation catalogue proposal and its two "
    "reference resolutions, retaining 62 reference findings, zero uncovered "
    "leaves, and the partial-publication block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}, SHA-256 {OWNER_MANIFEST_SHA256}), {GENERATOR.name} "
    f"(SHA-256 {GENERATOR_SHA256}; candidate {PROPOSAL_FILE.name}, SHA-256 "
    f"{PROPOSAL_SHA256}, identity {IDENTITY}) and {DRAFTS_FILE.name} (SHA-256 "
    f"{DRAFTS_SHA256}), appended to {ACCEPTED_PATH.name} "
    f"(SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)
#: The one finding the two drafts clear, twice; no other finding moves.
CLEARED = (
    "reference srd-5.2.1/character-creation:'Character Creation': unresolved reference"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int]]] = {
    "prior": ((23, 1834, 10491, 1475, 1438), (64, 0)),
    "recorded": ((24, 1835, 10492, 1476, 1440), (62, 0)),
}
STATES = tuple(EXPECTED)

#: The executed step times (accepted, resolved), as the recording wrote them,
#: and the artifact bytes in each state.
RECORDED_AT: tuple[str, ...] = ("2026-09-29T18:51:30Z", "2026-09-29T18:51:34Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "recorded": "ea0c219feec8571142c797ebd127713d55595db7309c64670a1436756b4413de",
}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The framing-coverage recording, rebuilt from its recorded time."""
    if not _PRIOR:
        base = FRAMING.prior()
        inputs: AcceptedInputs = FRAMING.composed(
            base, FRAMING.OWNER, FRAMING.RECORDED_AT[0]
        )
        assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256
        _PRIOR.append(inputs)
    return _PRIOR[0]


def loaded_prior() -> AcceptedInputs:
    """The committed file as loaded, while it is still the prior."""
    assert _sha(ACCEPTED_PATH.read_bytes()) == PRIOR_SHA256, "not the prior"
    return load_accepted_inputs(ACCEPTED_PATH)


def candidate() -> MechanicalProposal:
    """The reviewed candidate, read from its pinned file."""
    assert _sha(PROPOSAL_FILE.read_bytes()) == PROPOSAL_SHA256, PROPOSAL_FILE.name
    proposal: MechanicalProposal = load_proposal(
        PROPOSAL_FILE, expected_identity=IDENTITY
    )
    return proposal


def drafts() -> tuple[ReferenceResolution, ...]:
    """The two reviewed drafts, read from their pinned file by the loader's
    own strict parser and held to its bytes."""
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    payload = json.loads(raw)
    out = tuple(_reference_resolution(item, i) for i, item in enumerate(payload))
    assert list(reference_resolution_payload(out)) == payload
    assert sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in out
    ) == sorted(GEN.ROWS)
    assert all(
        _is_new(r.resolution_id) and r.target_record_key == GEN.SECTION_KEY for r in out
    )
    return out


def composed(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: the candidate accepted once over ``base`` by ``reviewer`` at
    ``at``: the generator's own acceptance, only the evidence a parameter."""
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


def resolved(step1: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 2: the two reviewed drafts over step 1."""
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


def _is_new(resolution_id: str) -> bool:
    return resolution_id.endswith(GEN.SUFFIX)


def _acceptances(inputs: AcceptedInputs) -> list[Any]:
    """Every span and review-unit acceptance."""
    return [*inputs.acceptances, *inputs.review_unit_acceptances]


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: accepted, resolved."""
    acc = {a.accepted_at for a in _acceptances(inputs) if a.batch_id == BATCH}
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_new(a.resolution_id)
    }
    assert len(acc) <= 1 and len(res) <= 1, (sorted(acc), sorted(res))
    return (
        str(next(iter(acc))) if acc else None,
        str(next(iter(res))) if res else None,
    )


def _state(base: AcceptedInputs) -> tuple[str, AcceptedInputs]:
    """(state, result) of the artifact over ``base``, after checking it
    rebuilds. Fails closed on anything but the prior or its one step result."""
    if not ACCEPTED_PATH.exists():
        raise SystemExit(f"{ACCEPTED_PATH.name} is absent")
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    # Batches serialize in canonical order, so they are compared as sets.
    got = sorted(b.batch_id for b in inputs.batches)
    before = sorted(b.batch_id for b in base.batches)
    new = any(_is_new(r.resolution_id) for r in inputs.oracle.reference_resolutions)
    acc_at, res_at = _read_back(inputs)
    result: AcceptedInputs
    if got == before and not (acc_at or res_at or new):
        state, result = "prior", base
    elif got == sorted([*before, BATCH]) and acc_at and res_at and new:
        state = "recorded"
        result = resolved(composed(base, OWNER, acc_at), OWNER, res_at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized state {got}")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, result


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


def _members(inputs: AcceptedInputs) -> list[Any]:
    """The six members' records, components and prose bindings, and the
    accepted framing unit over the part heading."""
    rep = inputs.oracle.representation
    keys = set(GEN.MEMBER_KEYS)
    return sorted(
        [
            *(repr(r) for r in rep.records if r.semantic_key in keys),
            *(repr(c) for c in rep.components if c.record_key in keys),
            *(repr(b) for b in rep.prose_bindings if b.record_key in keys),
            *(
                repr(u)
                for u in inputs.oracle.review_units
                if u.unit_id == GEN.FRAMING_UNIT
            ),
        ]
    )


def _blank(line: str) -> str:
    return str(FRAMING.ANIMALS_CATALOGUE.REMAINING._authorizer_blank(line))


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
    found = FC.findings(inputs)
    refs = [f for f in found if f.startswith("reference ")]
    leaves = [f for f in found if f.startswith("leaf ")]
    print("  reference, uncovered-leaf findings", (len(refs), len(leaves)), end="")
    print(" other", len(found) - len(refs) - len(leaves))
    assert len(refs) + len(leaves) == len(found), found[:5]
    assert (len(refs), len(leaves)) == EXPECTED[state][1]
    if state == "prior":
        return
    # Finding order follows set iteration, so they are compared as multisets.
    old = Counter(FC.findings(base))
    gone, added = old - Counter(found), Counter(found) - old
    print("  findings cleared", dict(gone), "| new", dict(added))
    assert gone == Counter({CLEARED: 2}) and not added
    # Every other batch is kept, identity included; one is appended.
    before = sorted((b.batch_id, b.proposal_identity) for b in base.batches)
    after = sorted((b.batch_id, b.proposal_identity) for b in inputs.batches)
    assert after == sorted([*before, (BATCH, IDENTITY)]), after
    new = sorted(
        r.resolution_id
        for r in oracle.reference_resolutions
        if _is_new(r.resolution_id)
    )
    assert new == sorted(d.resolution_id for d in drafts()), new
    lost = MC._preserved(accepted_inputs_payload(base), accepted_inputs_payload(inputs))
    print("  prior content lost or changed, evidence included", lost)
    assert not lost
    kept = _members(base) == _members(inputs)
    print("  six members and", GEN.FRAMING_UNIT, "unchanged", kept, len(_members(base)))
    assert kept
    # The reviewed DELTA blanks evidence (reviewer, times, rule) but carries
    # the simulated authorizer of the two drafts; blank that on both sides.
    delta = EQ.Delta(base, inputs)
    first = {
        c.target_key[0]: c.span_id
        for c in candidate().proposed_representation.provenance
        if c.target_kind is ProvenanceTargetKind.RELATIONSHIP
    }
    report: list[str] = [*delta.report(), *GEN.membership_report(delta, first)]
    raw = DELTA_FILE.read_bytes()
    assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
    reviewed = raw.decode("utf-8").rstrip("\n").split("\n")
    same = [_blank(x) for x in report] == [_blank(x) for x in reviewed]
    print(
        "  delta (evidence and authorizer blanked) is the reviewed DELTA,"
        " line for line",
        same,
    )
    print("   ", len(report), "lines")
    assert same
    assert not any(a for a, _ in delta.collections().values())


def _precheck(base: AcceptedInputs) -> None:
    """Before any write: under the simulated reviewer the two steps are the
    reviewed composition, byte for byte; under the Owner, at a placeholder
    time, every post-write check passes on the Owner's own evidence."""
    simulated = serialize_accepted_inputs(
        resolved(
            composed(base, SIMULATED_REVIEWER, SIMULATED_AT),
            SIMULATED_REVIEWER,
            SIMULATED_AT,
        )
    )
    # The generator's own simulated steps, as reviewed, give the same bytes.
    reviewed = GEN.drafted(GEN.accepted(base, candidate()), drafts())
    same = simulated == serialize_accepted_inputs(reviewed)
    print("  simulated composition = the generator's own steps", same)
    assert same
    # --verify and the tests compose over the replayed prior: prove it now.
    replay = prior()
    same = simulated == serialize_accepted_inputs(
        resolved(
            composed(replay, SIMULATED_REVIEWER, SIMULATED_AT),
            SIMULATED_REVIEWER,
            SIMULATED_AT,
        )
    )
    print("  composition over the replay = over the committed file", same)
    assert same
    print("  simulated bytes", _sha(simulated), "(pinned here; never recorded)")
    assert _sha(simulated) == SIMULATED_SHA256, "simulated bytes not pinned"
    final = resolved(composed(base, OWNER, PLACEHOLDER_AT), OWNER, PLACEHOLDER_AT)
    _check("recorded", base, final)
    wrong = _approvals(final)
    print("  under the Owner every new acceptance names this decision", not wrong)
    assert not wrong, wrong[:5]
    assert _read_back(final) == (PLACEHOLDER_AT, PLACEHOLDER_AT)
    assert serialize_accepted_inputs(final) != simulated


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    if state in RECORDED_SHA256:
        assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
        expected = RECORDED_AT if state == "recorded" else (None, None)
        assert _read_back(inputs) == tuple(expected), "not the recorded times"
    else:
        print("  (no pin yet for", state, "- record it before relying on --verify)")
    print("  times (accepted, resolved)", _read_back(inputs))
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
    for path, sha in (
        (PROPOSAL_FILE, PROPOSAL_SHA256),
        (DRAFTS_FILE, DRAFTS_SHA256),
        (DELTA_FILE, DELTA_SHA256),
        (REVIEW_FILE, REVIEW_SHA256),
    ):
        assert _sha(path.read_bytes()) == sha, path.name
    if argv == ["--simulate"]:
        base = loaded_prior()
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    if argv == ["--verify"]:
        # The oracle is not tracked: the prior is its replay.
        base = prior()
        state, inputs = _state(base)
        verify(state, base, inputs)
        return
    if argv != ["record-character-creation-catalogue"]:
        raise SystemExit(
            "usage: --simulate | record-character-creation-catalogue | --verify"
        )
    # The append reads the committed inputs as loaded; no chain is rebuilt.
    base = loaded_prior()
    state, _ = _state(base)
    if state != "prior":
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not prior")
    _precheck(base)
    acc_at = _now()
    step1 = composed(base, OWNER, acc_at)
    res_at = _now()
    data = serialize_accepted_inputs(resolved(step1, OWNER, res_at))
    ACCEPTED_PATH.write_bytes(data)
    print("record-character-creation-catalogue", ACCEPTED_PATH.name, acc_at, res_at)
    print("  sha256", _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, inputs = _state(base)
    assert after == "recorded", after
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
