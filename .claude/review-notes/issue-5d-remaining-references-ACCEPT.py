"""Owner acceptance of the remaining-references replacement and its 29 drafts.

CRD Issue 5d remaining references (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`, evidence pinned in
:data:`OWNER_MANIFEST`, SHA-256 :data:`OWNER_MANIFEST_SHA256`) with
:data:`APPROVAL`, verbatim.

The acceptance module has no supersession, so the eight changed batches are
recorded as a fresh chain over no prior, as the reviewed
``issue-5d-remaining-references-REPLACEMENT.py`` (:data:`CONSTRUCTOR_SHA256`)
composes it: the twenty-two recorded proposals in their recorded order, the
eight of :data:`PROPOSALS` taking the reviewed candidates. That decision
authorizes exactly two native writes, in this order, each reading the UTC clock
when it runs:

1. ``record-remaining``: the twenty-two batches over no prior, each of the 14
   unchanged proposals (byte-identical) with its recorded rule, reviewer and
   time and every recorded resolution but the three re-keyed ones re-applied
   verbatim after its batch; the eight changed batches under the Owner, with
   :data:`APPROVAL` as their rule.
2. ``resolve-remaining``: :func:`resolve_references` with the 29 reviewed
   drafts (:data:`DRAFTS_SHA256`), three of them the re-keyed resolutions
   proposed afresh, under the Owner.

The candidate proposals are the constructor's, rendered from the release and
kept as :data:`PROPOSALS` so replay needs no release store; ``--simulate``
rebuilds them and holds them to those bytes. The prior (:data:`PRIOR_SHA256`) is
rebuilt through ``issue-5d-equipment-cited-targets-ACCEPT.py`` from its recorded
times, never read back from the artifact. Any artifact state other than the
prior or one of the two step results fails closed. The other 68 reference
findings and 29 uncovered leaves stay; nothing here publishes or activates, and
the release order is not corrected (tracked, not certified).
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
from afterworlds.ingestion.mechanical.authoring import (  # noqa: E402
    render,
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


#: The Equipment recording, the prior's authority; the reviewed constructor,
#: used as it was reviewed (its batches, re-keys, drafts and native steps, never
#: its simulated evidence); and the generator of the drafts.
EQUIPMENT_CITED = _load(
    "equipment_cited_accept", HERE / "issue-5d-equipment-cited-targets-ACCEPT.py"
)
CONSTRUCTOR = HERE / "issue-5d-remaining-references-REPLACEMENT.py"
CONSTRUCTOR_SHA256 = "7377fa566673df95fc49a764a33bd0b30d401c2d0a9fc28904b2f26df2266771"
assert _sha(CONSTRUCTOR.read_bytes()) == CONSTRUCTOR_SHA256, CONSTRUCTOR.name
RR = _load("remaining_references_replacement", CONSTRUCTOR)
GEN = RR.GEN
REPL = RR.REPL

ACCEPTED_PATH: Path = EQUIPMENT_CITED.ACCEPTED_PATH
PRIOR_SHA256: str = EQUIPMENT_CITED.RECORDED_SHA256["resolved"]
assert PRIOR_SHA256 == RR.ACCEPTED_SHA256

#: batch -> (identity the Owner review names, proposal file SHA-256), in the
#: recorded batch order. The file is the constructor's rendering.
PROPOSALS: dict[str, tuple[str, str]] = {
    "checks-actions-rests": (
        "fa6469518d225826ea5aeb16f491226fecbbcf3ec506b8950f1f482d50c62076",
        "389dd8ef40a54ceaadec146c259f9aca549c04fd76829da593856c413b86dd6b",
    ),
    "core-play-completion": (
        "cc0e3dd1efa51aa423eb6957a4d29c104226326e685d06ef275adf4ba239868e",
        "4d9fe61d0fffd298feb3e6e3435b9789fae778116df059acb18c6126da96cf8a",
    ),
    "core-play-dependencies": (
        "8fce546dfc78d37dfd98c68e1f4fe801602bdd0c84fe31d6a06ade6ad03e6c2b",
        "20387d70e4f314617930e974a58d26133083f199237e9179c822ce7f40a7197d",
    ),
    "character-creation-foundations": (
        "fcee4afb8ef79e11a76da0f12cd0a9f3a21a0508cbe3634dde9afa8ac919950e",
        "10d06eacf97d498a56f80f93d6c1627fcd8d4b350a353743c6c64410c381b189",
    ),
    "spellcasting": (
        "5cc2bd875f7ed798342c9fffd16160dc4bb2ef68bbbf81e622297056723cfadd",
        "7b0370d1c701cfe8611b0c80784739087ff1a08fab4b3be886de90e5e7307888",
    ),
    "gameplay-toolbox": (
        "fc81400f73c2d1dbdcc17d578c09ede0fe3946ef7061be19d514d37940418bd0",
        "52c8a194df253e58a5c3e6d63fad77eb0db5ec93c641cdfc5c36c6ad68d0e5ef",
    ),
    "magic-items": (
        "20e68a02a2dedfbeb43e56d505d216dc7d7b108b83a5dba589cc641c7da8c458",
        "626f80d9001419655d15e41b8403c56de2c598f672a21cf87e99d05427097319",
    ),
    "monsters": (
        "791b52c3cc3f899e716bc22e5feb053d27d679ad49307cb9a041a88432e9c3f5",
        "5bdd535eb7078c2c3bfb39195ae1fbe7cbe248be303e39b721738cc73a3c8773",
    ),
}
assert tuple(PROPOSALS) == RR.CHANGED
DRAFTS_FILE: Path = HERE / GEN.DRAFTS_FILE
DRAFTS_SHA256 = "8cf49706598b600d45822f05c3d6d5113a0d851f59e3d44542721f0d6148fad7"
#: Every new draft id carries this suffix, and none of the prior's 1,408.
SUFFIX = "-remaining-1"
#: The reviewed full-text, order-aware delta, evidence blanked.
DELTA_FILE = HERE / "issue-5d-remaining-references-DELTA.txt"
DELTA_SHA256 = "6e4e307d8567592a3371b76c5d651a25cc1464e1374f121ba58ff11854c98246"
#: The reviewed composition with simulated approval, never a recorded hash.
SIMULATED_SHA256 = "10cf83a6b4b97b1370fd46a15af267bcf0cd41ba2903652f0d099cfb00cc45f5"

SIMULATED_REVIEWER: str = RR.SIMULATED_REVIEWER
SIMULATED_RULE: str = RR.SIMULATED_RULE
SIMULATED_AT: str = RR.SIMULATED_AT

#: The Owner is the reviewer, the authorizer and the executor.
OWNER: str = EQUIPMENT_CITED.OWNER
OWNER_REVIEW = "remaining-references-owner-review.md"
OWNER_REVIEW_SHA256 = "64fe900c19300d9ffc6422f38f5f0859ebe29a6df2677bdd186373c9e489ab59"
OWNER_MANIFEST = "remaining-references-owner-manifest.json"
OWNER_MANIFEST_SHA256 = (
    "d4bf66e92e12619dbab6f9e3d434f1040ee42bee50f410055a3a10a6243818c2"
)
#: The Owner's acceptance, verbatim; the rule of every batch it accepts.
APPROVAL = (
    "I accept the exact remaining-references replacement candidate and its 29 "
    "reference resolutions, retaining 68 reference findings, 29 uncovered "
    "leaves, and the partial-publication block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}; manifest "
    f"{OWNER_MANIFEST}, SHA-256 {OWNER_MANIFEST_SHA256}), {CONSTRUCTOR.name} "
    f"(SHA-256 {CONSTRUCTOR_SHA256}; candidate identities "
    f"{', '.join(f'{b} {i}' for b, (i, _) in PROPOSALS.items())}) and "
    f"{DRAFTS_FILE.name} (SHA-256 {DRAFTS_SHA256}), replacing those batches of "
    f"{ACCEPTED_PATH.name} (SHA-256 {PRIOR_SHA256}): {APPROVAL!r}"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED: dict[str, tuple[tuple[int, int, int, int, int], tuple[int, int]]] = {
    "prior": ((22, 1826, 10484, 1459, 1408), (91, 29)),
    "remaining-recorded": ((22, 1832, 10484, 1459, 1405), (97, 29)),
    "resolved": ((22, 1832, 10484, 1459, 1434), (68, 29)),
}
STATES = tuple(EXPECTED)

#: The executed step times (recorded, resolved), as the recording wrote them,
#: and the artifact bytes after each step.
RECORDED_AT: tuple[str, ...] = ("2026-09-29T07:34:50Z", "2026-09-29T07:37:07Z")
RECORDED_SHA256: dict[str, str] = {
    "prior": PRIOR_SHA256,
    "remaining-recorded": (
        "b61493266453bd4107dc729fafdfa1891208bf269f018baf7b4a9802ee1bb009"
    ),
    "resolved": "e0fd7690f519ec34dabcbba320936c20faff402fd94b925a2d4453316a29b14c",
}


def _authorizer_blank(line: str) -> str:
    """A delta line with its resolution authorizer blanked, as its evidence is."""
    if "{" not in line:
        return line
    head, item = line[: line.index("{")], json.loads(line[line.index("{") :])
    for k in ("authorized_by", "authorization_reference"):
        if k in item:
            item[k] = "<evidence>"
    return head + REPL._key(item)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def proposal_path(batch: str) -> Path:
    return HERE / f"issue-5d-{batch}-remaining-references-PROPOSAL.json"


_PRIOR: list[AcceptedInputs] = []


def prior() -> AcceptedInputs:
    """The recorded chain, rebuilt through the Equipment recording."""
    if not _PRIOR:
        inputs: AcceptedInputs = EQUIPMENT_CITED.recorded()
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


def proposals() -> dict[str, MechanicalProposal]:
    """The eight candidates, read from their pinned files."""
    out = {}
    for batch, (identity, sha) in PROPOSALS.items():
        path = proposal_path(batch)
        assert _sha(path.read_bytes()) == sha, path.name
        out[batch] = load_proposal(path, expected_identity=identity)
    return out


def composed(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 1: :func:`RR.chain` over ``base``'s recorded evidence, the eight
    candidates accepted by ``reviewer`` at ``at``.

    The same loop as the reviewed composition; only the evidence of the changed
    batches is a parameter. :func:`_precheck` holds it to the reviewed bytes.
    """
    changed = proposals()
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

    for batch, proposal in REPL._proposals():
        assert proposal.binding == base.oracle.binding, batch
        rule, who, when = per[batch]
        if batch in changed:
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
    inputs = resolve(steps["equipment-cited"])
    return inputs


def resolved(
    base: AcceptedInputs, step1: AcceptedInputs, reviewer: str, at: str
) -> AcceptedInputs:
    """Step 2: the 29 reviewed drafts over step 1."""
    drafts = GEN.draft_resolutions(base.oracle.binding)
    raw = DRAFTS_FILE.read_bytes()
    assert _sha(raw) == DRAFTS_SHA256, DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert len(drafts) == 29, len(drafts)
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


def _is_new(resolution_id: str) -> bool:
    return resolution_id.endswith(SUFFIX)


def _read_back(inputs: AcceptedInputs) -> tuple[str | None, str | None]:
    """The executed step times recorded in ``inputs``: recorded, resolved."""
    identities = {b.batch_id: b.proposal_identity for b in inputs.batches}
    if all(identities[b] != i for b, (i, _) in PROPOSALS.items()):
        return None, None
    assert all(identities[b] == i for b, (i, _) in PROPOSALS.items()), identities
    acc = {
        a.accepted_at
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id in PROPOSALS
    }
    res = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_new(a.resolution_id)
    }
    return (
        _one(acc, "changed batches accepted_at"),
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
        state, result = "remaining-recorded", composed(base, OWNER, acc_at)
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
        if b.batch_id in PROPOSALS and b.rule != APPROVAL
    ]
    wrong += [
        f"{a.batch_id} {getattr(a, 'span_id', None) or getattr(a, 'unit_id', '')}"
        for a in (*inputs.acceptances, *inputs.review_unit_acceptances)
        if a.batch_id in PROPOSALS and a.reviewer != OWNER
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
    evidence included, or holds twice: the 14 unchanged batches' acceptances
    and the recorded resolutions but the three re-keyed ones (none may)."""
    old = accepted_inputs_payload(base)
    new = accepted_inputs_payload(inputs)
    gone = set(GEN.REKEYED)
    out = []
    for path in (
        ("acceptance", "batches"),
        ("acceptance", "records"),
        ("acceptance", "review_unit_records"),
        ("acceptance", "reference_resolution_records"),
        ("reference_resolutions",),
    ):

        def kept(item: dict[str, Any]) -> bool:
            return (
                item.get("batch_id") not in PROPOSALS
                and item.get("resolution_id") not in gone
                and not _is_new(str(item.get("resolution_id", "")))
            )

        a = Counter(REPL._key(x) for x in REPL._at(old, path) if kept(x))
        b = Counter(REPL._key(x) for x in REPL._at(new, path) if kept(x))
        out += [f"{'.'.join(path)} lost {k[:200]}" for k in (a - b).elements()]
        out += [f"{'.'.join(path)} added {k[:200]}" for k in (b - a).elements()]
    return out


def _expectations(base: AcceptedInputs, inputs: AcceptedInputs) -> tuple[int, ...]:
    """(reviewed, derived, re-owned, typed re-owned, lost, added) per span."""
    owner = {
        (
            RR._load(f"rr_{b.replace('-', '_')}", RR.GENERATORS[b])
            .batch()
            .record_key(entry),
            key,
        ): record
        for b, declared in RR.CANDIDATES.items()
        for record, entry, keys in declared
        for key in keys
    }
    reviewed, derived = RR.expectations(base), RR.expectations(inputs)
    moved = Counter(
        (u, owner.get((r, c), r), c, f, s)
        for (u, r, c, f, s), n in reviewed.items()
        for _ in range(n)
    )
    rehomed = Counter(k for k in reviewed.elements() if (k[1], k[2]) in owner)
    return (
        sum(reviewed.values()),
        sum(derived.values()),
        sum(rehomed.values()),
        sum(n for k, n in rehomed.items() if k[3]),
        sum((moved - derived).values()),
        sum((derived - moved).values()),
    )


def _rekeyed(base: AcceptedInputs, inputs: AcceptedInputs) -> list[str]:
    """Each re-keyed resolution: gone under its old identity, present under its
    new one with the same component, text, scope, target and spans."""
    old = {r.resolution_id: r for r in base.oracle.reference_resolutions}
    new = {r.resolution_id: r for r in inputs.oracle.reference_resolutions}
    by_text = {
        (r.from_record_key, r.source_text): r for i, r in new.items() if _is_new(i)
    }
    out = []
    for old_id, (record, component, text, scope, target, spans) in GEN.REKEYED.items():
        was, now = old[old_id], by_text[(record, text)]
        same = (
            (
                was.from_component_key,
                was.source_text,
                was.scope_key,
                was.target_record_key,
                was.provenance_span_ids,
            )
            == (
                now.from_component_key,
                now.source_text,
                now.scope_key,
                now.target_record_key,
                now.provenance_span_ids,
            )
            == (component, text, scope, target, spans)
        )
        out.append(f"{old_id} -> {now.resolution_id} unchanged {same}")
        assert same and old_id not in new and _is_new(now.resolution_id), out[-1]
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
        # Batch order is the recorded order; only the eight identities change.
        before = [(b.batch_id, b.proposal_identity) for b in base.batches]
        after = [(b.batch_id, b.proposal_identity) for b in inputs.batches]
        assert [b for b, _ in before] == [b for b, _ in after]
        assert [x for x in after if x[0] not in PROPOSALS] == [
            x for x in before if x[0] not in PROPOSALS
        ]
        lost = _kept(base, inputs)
        print(
            "  14 unchanged batches and 1405 resolutions kept, evidence included,"
            " none twice",
            not lost,
        )
        assert not lost, lost[:5]
        ex = _expectations(base, inputs)
        print(
            "  expectations per span (reviewed, derived, re-owned, typed,"
            " lost, added)",
            ex,
        )
        assert ex == (10432, 10432, 38, 10, 0, 0), ex
    if state == "resolved":
        for line in _rekeyed(base, inputs):
            print("  re-keyed", line)
        # The reviewed DELTA blanks REPL.EVIDENCE only, so it carries the
        # simulated authorizer of the 29 drafts; blank that on both sides.
        report: list[str] = REPL.Delta(base, inputs).report()
        raw = DELTA_FILE.read_bytes()
        assert _sha(raw) == DELTA_SHA256, DELTA_FILE.name
        reviewed = raw.decode("utf-8").rstrip("\n").split("\n")
        same = [_authorizer_blank(x) for x in report] == [
            _authorizer_blank(x) for x in reviewed
        ]
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
    """The candidates rebuild to their pinned bytes, and both steps in memory
    under the simulated reviewer are the reviewed composition, byte for byte."""
    rebuilt = RR.rebuilt(base, with_candidates=True)
    for batch, proposal in rebuilt.items():
        data = render(proposal).encode("utf-8")
        assert _sha(data) == PROPOSALS[batch][1], batch
        assert data == proposal_path(batch).read_bytes(), batch
    print("  the eight candidates rebuild from the release to their pinned bytes")
    step1 = composed(base, SIMULATED_REVIEWER, SIMULATED_AT)
    reviewed = RR.chain(base, rebuilt, rekeyed=True)
    same = serialize_accepted_inputs(step1) == serialize_accepted_inputs(reviewed)
    print("  step 1 is the reviewed REPLACEMENT composition, byte for byte", same)
    assert same
    _check("remaining-recorded", base, step1)
    final = resolved(base, step1, SIMULATED_REVIEWER, SIMULATED_AT)
    _check("resolved", base, final)
    data = serialize_accepted_inputs(final)
    same = (
        _sha(data)
        == SIMULATED_SHA256
        == _sha(serialize_accepted_inputs(RR.drafted(reviewed)))
    )
    print("  simulated bytes", _sha(data), "(reviewed; never recorded)", same)
    assert same


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
        "record-remaining": "prior",
        "resolve-remaining": "remaining-recorded",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | record-remaining | resolve-remaining | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["record-remaining"]:
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
