"""Owner acceptance of the Gameplay Toolbox batch and its one reference resolution.

CRD Issue 5d (#132, #137). The Owner answered :data:`OWNER_REVIEW` (SHA-256
:data:`OWNER_REVIEW_SHA256`), which names exactly :data:`PROPOSAL_FILE`
(:data:`PROPOSAL_SHA256`, identity :data:`IDENTITY`) and the one resolution in
:data:`DRAFTS_FILE` (:data:`DRAFTS_SHA256`), with :data:`APPROVAL`.

That decision authorizes exactly two native actions, each over the previous
result, and each reading the UTC clock when it runs:

1. ``accept-toolbox``: :func:`accept_proposal` of the whole proposal over the
   recorded eighteen-batch authority (``b1f8718f…``), which is rebuilt through
   ``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`` from its own recorded
   times, never read back from the artifact this script extends.
2. ``resolve-toolbox``: :func:`resolve_references` with the one draft, drafted
   over that eighteen-batch authority and held to the reviewed drafts file.

The other 166 reference findings stay; nothing here publishes or activates.
``--verify`` reads both step times back from the artifact and rebuilds it, so
the recorded bytes reproduce. Any artifact state other than the eighteen-batch
prior or one of the two step results fails closed. ``--simulate`` composes both
steps in memory under an explicit simulated reviewer and writes nothing.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
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


#: The recording of the eighteen-batch authority this batch extends.
REPLACEMENT = _load(
    "class_spell_tables_replacement",
    HERE / "issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py",
)
GEN = REPLACEMENT.generator("gameplay-toolbox")
ACCEPTED_PATH: Path = REPLACEMENT.ACCEPTED_PATH
#: The eighteen-batch authority's bytes, as REPLACEMENT recorded them.
PRIOR_SHA256 = "b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f"

BATCH_ID = "gameplay-toolbox"
PROPOSAL_FILE = HERE / "issue-5d-gameplay-toolbox-PROPOSAL.json"
PROPOSAL_SHA256 = "3a2751744b6350933f0c0aaec3cbb88761afcfb4f4d35434394bf70537fd49a6"
IDENTITY = "8d4db7037b167648995d31bef6ad2f47ae31a19a2b48bf42406246517ee719eb"
DRAFTS_FILE = HERE / "issue-5d-gameplay-toolbox-resolutions-DRAFTS.json"
DRAFTS_SHA256 = "b87e6dcfdb29f4d02317a98e7b868cd12b122c3f5daf99d68ff5b9004a4528dd"
RESOLUTION_ID = (
    "resolve-glossary-challenge-rating-record-combat-encounters-gameplay-toolbox-1"
)

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_RULE = "SIMULATION ONLY: in-memory composition check; records no acceptance"
SIMULATED_AT = "2026-09-27T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = REPLACEMENT.OWNER
OWNER_REVIEW = "gameplay-toolbox-owner-review.md"
OWNER_REVIEW_SHA256 = "bbceeadd434f42022813e205f96e0281f87dbfe7460cd16f51c71a764975a127"
#: The Owner's decision, verbatim; the rule of the batch it accepts.
APPROVAL = "I accept this exact proposal and its one reference resolution."
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}), "
    f"exact packet {PROPOSAL_FILE.name} (SHA-256 {PROPOSAL_SHA256}) and "
    f"{DRAFTS_FILE.name} (SHA-256 {DRAFTS_SHA256}): {APPROVAL!r}"
)

#: (batches, records, spans, review units, resolutions); then reference and
#: uncovered-leaf findings on the release.
EXPECTED = {
    "prior": ((18, 947, 4826, 645, 1097), (143, 5621)),
    "toolbox-accepted": ((19, 980, 5111, 679, 1097), None),
    "resolved": ((19, 980, 5111, 679, 1098), (166, 5336)),
}

#: The executed step times (accepted, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, str] | None = ("2026-09-27T09:46:01Z", "2026-09-27T09:46:44Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "toolbox-accepted": (
        "636b12758be98e614123080eb462da055d01d56a58d44e936014895801bc1086"
    ),
    "resolved": "671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prior() -> AcceptedInputs:
    """The recorded eighteen-batch authority, rebuilt from its recorded times."""
    base = REPLACEMENT.recorded()
    at = REPLACEMENT.RECORDED_AT
    inputs: AcceptedInputs = REPLACEMENT.spells_resolved(
        base, REPLACEMENT.spells_accepted(base, OWNER, at[1]), OWNER, at[2]
    )
    assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256, "drifted"
    return inputs


def accepted(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: the whole proposal, accepted over the eighteen-batch authority."""
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
    """Step 2: the reviewed draft, drafted over ``base``, over step 1."""
    drafts = GEN.draft_resolutions(base.oracle.binding, prior=base)
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert [d.resolution_id for d in drafts] == [RESOLUTION_ID], drafts
    reference = AUTHORIZATION_REFERENCE if reviewer == OWNER else SIMULATED_RULE
    return resolve_references(
        step1,
        resolutions=drafts,
        authorized_by=reviewer,
        authorization_reference=reference,
        reviewer=reviewer,
        resolved_at=at,
    )


def _one(values: set[str], what: str) -> str:
    assert len(values) == 1, f"{what}: {sorted(values)}"
    return next(iter(values))


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: accepted, resolved."""
    acc = {a.accepted_at for a in inputs.acceptances if a.batch_id == BATCH_ID}
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if a.resolution_id == RESOLUTION_ID
    }
    return (
        _one(acc, "accepted_at") if acc else None,
        _one(res, "resolved_at") if res else None,
    )


def _state() -> tuple[str, AcceptedInputs, AcceptedInputs]:
    """(state, prior, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but the eighteen-batch prior or a step result.
    """
    base = prior()
    data = ACCEPTED_PATH.read_bytes()
    if _sha(data) == PRIOR_SHA256:
        return "prior", base, base
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    got = {b.batch_id for b in inputs.batches}
    if got != {b.batch_id for b in base.batches} | {BATCH_ID}:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {sorted(got)}")
    acc_at, res_at = _read_back(inputs)
    if acc_at and not res_at:
        state, result = "toolbox-accepted", accepted(base, OWNER, acc_at)
    elif acc_at and res_at:
        state = "resolved"
        result = resolved(base, accepted(base, OWNER, acc_at), OWNER, res_at)
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    oracle = inputs.oracle
    return (
        len(inputs.batches),
        len(oracle.representation.records),
        len(oracle.spans),
        len(oracle.review_units),
        len(oracle.reference_resolutions),
    )


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
    print("  eighteen-batch authority preserved", not lost, _counts(base))
    assert not violations, violations
    assert not lost, lost
    # Preserved as a multiset, and nothing added beside this batch's own: no
    # prior acceptance or resolution is duplicated or restamped.
    assert len([a for a in inputs.acceptances if a.batch_id != BATCH_ID]) == len(
        base.acceptances
    )
    assert len(
        [
            a
            for a in inputs.reference_resolution_acceptances
            if a.resolution_id != RESOLUTION_ID
        ]
    ) == len(base.reference_resolution_acceptances)
    assert _counts(base) == EXPECTED["prior"][0], _counts(base)
    counts, findings = EXPECTED[state]
    assert _counts(inputs) == counts, _counts(inputs)
    if findings is not None:
        assert REPLACEMENT._findings(inputs) == findings


def _precheck(base: AcceptedInputs) -> None:
    """Both steps, in memory under the simulated reviewer, over ``base``."""
    step1 = accepted(base, SIMULATED_REVIEWER, SIMULATED_AT)
    _check("toolbox-accepted", base, step1)
    _check("resolved", base, resolved(base, step1, SIMULATED_REVIEWER, SIMULATED_AT))


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
    steps = ("toolbox-accepted", "resolved")
    assert RECORDED_AT is not None
    assert _read_back(inputs) == tuple(
        t if state in steps[i:] else None for i, t in enumerate(RECORDED_AT)
    ), "not the recorded times"
    print("  times (accepted, resolved)", _read_back(inputs))
    _check(state, base, inputs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        assert serialize_accepted_inputs(load_accepted_inputs(path)) == data
    print("  reloads to the same bytes True")


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str]) -> None:
    if argv == ["--simulate"]:
        base = prior()
        print("SIMULATED (in memory; nothing written; not an acceptance)")
        _check("prior", base, base)
        _precheck(base)
        return
    state, base, inputs = _state()
    if argv == ["--verify"]:
        if state == "prior":
            raise SystemExit(f"{ACCEPTED_PATH.name} is {state}")
        verify(state, base, inputs)
        return
    steps = {"accept-toolbox": "prior", "resolve-toolbox": "toolbox-accepted"}
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | accept-toolbox | resolve-toolbox | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["accept-toolbox"]:
        _precheck(base)
        result = accepted(base, OWNER, _now())
    else:
        _precheck(base)
        result = resolved(base, inputs, OWNER, _now())
    data = serialize_accepted_inputs(result)
    ACCEPTED_PATH.write_bytes(data)
    print(argv[0], ACCEPTED_PATH.name, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, _, _ = _state()
    assert after == {"accept-toolbox": "toolbox-accepted"}.get(argv[0], "resolved")
    print(
        "  state after", after, "times", _read_back(load_accepted_inputs(ACCEPTED_PATH))
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
