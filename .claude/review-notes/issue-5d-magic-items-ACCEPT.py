"""Owner acceptance of the Magic Items batch and its one reference resolution.

CRD Issue 5d (#132, #137). The Owner answered :data:`OWNER_REVIEW` (SHA-256
:data:`OWNER_REVIEW_SHA256`), which names exactly :data:`PROPOSAL_FILE`
(:data:`PROPOSAL_SHA256`, identity :data:`IDENTITY`) and the one resolution in
:data:`DRAFTS_FILE` (:data:`DRAFTS_SHA256`), with :data:`APPROVAL`.

That decision authorizes exactly two native actions, each over the previous
result, and each reading the UTC clock when it runs:

1. ``accept-magic-items``: :func:`accept_proposal` of the whole proposal over
   the recorded nineteen-batch authority (``671f47d7…``), which is rebuilt
   through ``issue-5d-gameplay-toolbox-ACCEPT.py`` from its own recorded times,
   never read back from the artifact this script extends.
2. ``resolve-magic-items``: :func:`resolve_references` with the one draft,
   drafted over that nineteen-batch authority and held to the reviewed drafts
   file.

The prior is preserved whole but for the one reviewed derived delta: the
``prose_bound_components`` obligation of each of the two shared Equipment
records also names :data:`SHARED_COMPONENT`. The other 315 reference findings
stay; nothing here publishes or activates. ``--verify`` reads both step times
back from the artifact and rebuilds it, so the recorded bytes reproduce. Any
artifact state other than the nineteen-batch prior or one of the two step
results fails closed. ``--simulate`` composes both steps in memory under an
explicit simulated reviewer and writes nothing.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, cast

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


#: The recording of the nineteen-batch authority this batch extends.
TOOLBOX = _load("gameplay_toolbox_accept", HERE / "issue-5d-gameplay-toolbox-ACCEPT.py")
REPLACEMENT = TOOLBOX.REPLACEMENT
GEN = REPLACEMENT.generator("magic-items")
ACCEPTED_PATH: Path = TOOLBOX.ACCEPTED_PATH
#: The nineteen-batch authority's bytes, as TOOLBOX recorded them.
PRIOR_SHA256 = "671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95"

BATCH_ID = "magic-items"
PROPOSAL_FILE = HERE / "issue-5d-magic-items-PROPOSAL.json"
PROPOSAL_SHA256 = "e0f8c657cd0edebc22f8865a0ffffdf16f6a907d7f7d5cbb70f75a6ddf2ab1d0"
IDENTITY = "aecc9ea52a8af77a62a29ee720211489d29d64eece057d9927b754e3934dcc39"
DRAFTS_FILE = HERE / "issue-5d-magic-items-resolutions-DRAFTS.json"
DRAFTS_SHA256 = "2207ddc3db1fae22f8d65471ee2fbb88d6ed96e55fbe91e313a0bbd59548e23c"
RESOLUTION_ID = (
    "resolve-gameplay-toolbox-travel-pace-special-movement-carpet-of-flying"
    "-magic-items-1"
)
#: The two accepted Equipment records the batch extends, and the component each
#: gains: the one reviewed derived delta to the prior.
SHARED_KEYS = (
    "equipment.adventuring_gear.potion_of_healing",
    "equipment.adventuring_gear.spell_scroll",
)
SHARED_COMPONENT = "magic_items_table"

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_RULE = "SIMULATION ONLY: in-memory composition check; records no acceptance"
SIMULATED_AT = "2026-09-28T00:00:00Z"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = REPLACEMENT.OWNER
OWNER_REVIEW = "magic-items-owner-review.md"
OWNER_REVIEW_SHA256 = "16e6475f6092fa68113ee66119e7141aa78c41e3db31ec2ee71ec506955fe634"
#: The Owner's decision, verbatim; the rule of the batch it accepts.
APPROVAL = (
    "I accept this exact Magic Items proposal and its one reference resolution, "
    "retaining 315 reference findings and the partial-publication block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}), "
    f"exact packet {PROPOSAL_FILE.name} (SHA-256 {PROPOSAL_SHA256}) and "
    f"{DRAFTS_FILE.name} (SHA-256 {DRAFTS_SHA256}): {APPROVAL!r}"
)

#: (batches, records, spans, review units, resolutions); then reference and
#: uncovered-leaf findings on the release.
EXPECTED = {
    "prior": ((19, 980, 5111, 679, 1098), (166, 5336)),
    "magic-items-accepted": ((20, 1250, 6450, 950, 1098), None),
    "resolved": ((20, 1250, 6450, 950, 1099), (315, 4004)),
}

#: The executed step times (accepted, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, str] | None = ("2026-09-27T23:27:11Z", "2026-09-27T23:28:26Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "magic-items-accepted": (
        "27fde6663f4ecc52dd1ca8e280e303380e52dbb2ba728cbd6118267625a7adee"
    ),
    "resolved": "fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prior() -> AcceptedInputs:
    """The recorded nineteen-batch authority, rebuilt from its recorded times."""
    base = TOOLBOX.prior()
    at = TOOLBOX.RECORDED_AT
    inputs: AcceptedInputs = TOOLBOX.resolved(
        base, TOOLBOX.accepted(base, OWNER, at[0]), OWNER, at[1]
    )
    assert _sha(serialize_accepted_inputs(inputs)) == PRIOR_SHA256, "drifted"
    return inputs


def accepted(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: the whole proposal, accepted over the nineteen-batch authority."""
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

    Fails closed on anything but the nineteen-batch prior or a step result.
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
        state, result = "magic-items-accepted", accepted(base, OWNER, acc_at)
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


def obligation_delta(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Where ``inputs`` holds the prior's obligations other than as reviewed.

    Every prior obligation is kept unchanged, except that each shared record's
    ``prose_bound_components`` also names :data:`SHARED_COMPONENT`.
    """
    was = cast(list[dict[str, Any]], accepted_inputs_payload(base)["obligations"])
    now = {
        o["record_key"]: o
        for o in cast(
            list[dict[str, Any]], accepted_inputs_payload(inputs)["obligations"]
        )
    }
    wrong = []
    for o in was:
        want = o
        if o["record_key"] in SHARED_KEYS:
            want = {
                **o,
                "prose_bound_components": sorted(
                    [*o["prose_bound_components"], SHARED_COMPONENT]
                ),
            }
            if want == o:
                wrong.append(f"{o['record_key']}: already names {SHARED_COMPONENT}")
        if now.get(o["record_key"]) != want:
            wrong.append(f"{o['record_key']}: obligation not as reviewed")
    return wrong


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, prior preservation and findings for ``state``."""
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    )
    old, new = accepted_inputs_payload(base), accepted_inputs_payload(inputs)
    lost = REPLACEMENT._preserved(
        {**old, "obligations": []}, {**new, "obligations": []}
    )
    delta = obligation_delta(base, inputs) if state != "prior" else []
    print(state)
    print("  counts (batches, records, spans, units, resolutions)", _counts(inputs))
    print("  resolution violations", len(violations))
    print("  nineteen-batch authority preserved", not lost, _counts(base))
    print("  obligations: only the two reviewed enlargements", not delta)
    assert not violations, violations
    assert not lost, lost
    assert not delta, delta
    # The two shared records keep their accepted definitions.
    records = {r.semantic_key: r for r in oracle.representation.records}
    assert all(
        records[r.semantic_key] == r
        for r in base.oracle.representation.records
        if r.semantic_key in SHARED_KEYS
    )
    # Preserved as a multiset, and nothing added beside this batch's own: no
    # prior acceptance or resolution is duplicated or restamped.
    assert inputs.batches[: len(base.batches)] == base.batches
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
    _check("magic-items-accepted", base, step1)
    _check("resolved", base, resolved(base, step1, SIMULATED_REVIEWER, SIMULATED_AT))


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
    steps = ("magic-items-accepted", "resolved")
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
        assert REPLACEMENT._findings(base) == EXPECTED["prior"][1]
        _precheck(base)
        return
    state, base, inputs = _state()
    if argv == ["--verify"]:
        if state == "prior":
            raise SystemExit(f"{ACCEPTED_PATH.name} is {state}")
        verify(state, base, inputs)
        return
    steps = {
        "accept-magic-items": "prior",
        "resolve-magic-items": "magic-items-accepted",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | accept-magic-items | resolve-magic-items | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    _precheck(base)
    if argv == ["accept-magic-items"]:
        result = accepted(base, OWNER, _now())
    else:
        result = resolved(base, inputs, OWNER, _now())
    data = serialize_accepted_inputs(result)
    ACCEPTED_PATH.write_bytes(data)
    print(argv[0], ACCEPTED_PATH.name, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, _, _ = _state()
    assert after == {"accept-magic-items": "magic-items-accepted"}.get(
        argv[0], "resolved"
    )
    print(
        "  state after", after, "times", _read_back(load_accepted_inputs(ACCEPTED_PATH))
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
