"""The Equipment class-eligibility candidate, composed in memory.

CRD Issue 5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. There
is deliberately no recording step.

Inventory rows #13, #16 and #21 (``issue-5d-remaining-references-review.md``)
are three accepted unresolved classes-scope references in the Equipment
batch. Each printed sentence states who may use a spellcasting focus
(``equipment.md`` lines 1261, 1404 and 1461: "A Sorcerer, Warlock, or Wizard
can use such an item as a Spellcasting Focus"; "A Druid or Ranger can use such
an object ..."; "A Cleric or Paladin can use a Holy Symbol ..."). The class
names are eligibility subjects, not a direction to consult a class section,
and ADR-005d Decision 7 does not let a unique destination name alone establish
source intent. So the three references and their provenance are removed; the
component prose, spans, bindings, expectations and every other citation are
unchanged.

One accepted batch changes: equipment, rebuilt from its recorded generator
(``issue-5d-equipment-cited-targets-generator.py``) with the three references
dropped. The chain is the recorded Playing the Game chain (``ACC.composed``):
every other batch keeps its recorded acceptance; the changed batch takes the
simulated reviewer. Controls: the generator rebuilds the recorded proposal
byte for byte, and the chain with no candidate rebuilds the committed
artifact byte for byte.

No resolution is drafted or re-keyed: every removed reference was unresolved.

Run: ``python issue-5d-equipment-class-eligibility-REPLACEMENT.py [--write]``.
``--write`` regenerates the proposal and delta files; otherwise they are
checked.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
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
    EntryBatch,
    EntryComponent,
    build_entry_batch,
    render,
    scoped,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    published_release_binding,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.services.rules_authority.targets import (  # noqa: E402
    MechanicalTargetKind,
)


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The recorded chain, through its last recording (the Playing the Game
#: atoms, whose ACCEPT script pins its reviewed constructor and candidates).
ACC = _load(
    "playing_the_game_atoms_accept",
    HERE / "issue-5d-playing-the-game-atoms-ACCEPT.py",
)
PGA = ACC.PGA
FINITE_REFERENCE = ACC.FINITE_REFERENCE
FRA = PGA.FRA
CHARACTER_CREATION = PGA.CHARACTER_CREATION
FRAMING = PGA.FRAMING
ANIMALS_CATALOGUE = PGA.ANIMALS_CATALOGUE
APC = PGA.APC
REMAINING = PGA.REMAINING
RR = PGA.RR
REPL = PGA.REPL

ACCEPTED_PATH: Path = ACC.ACCEPTED_PATH
ACCEPTED_SHA256 = "92b7a68fcd6ea622ac3ef79b1dacd939f7be52fa445fcbdafd5adc8c77352e19"
assert ACC.RECORDED_SHA256["recorded"] == ACCEPTED_SHA256
assert ACC.RECORDED_AT is not None
RECORDED_AT: str = ACC.RECORDED_AT
SCRATCH_DB: Path = REPL.SCRATCH_DB

TAG = "equipment-class-eligibility"
BATCH = "equipment"
PROPOSAL_FILE = HERE / f"issue-5d-{TAG}-PROPOSAL.json"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"
#: The recorded Equipment proposal and the generator that built it.
RECORDED_FILE: Path = REPL.CANDIDATE
GENERATOR = "equipment-cited-targets"

SIMULATED_REVIEWER: str = PGA.SIMULATED_REVIEWER
SIMULATED_RULE: str = PGA.SIMULATED_RULE
SIMULATED_AT: str = PGA.SIMULATED_AT

CLASSES = "srd-5.2.1/classes"
#: (record, component, pointer, scope, span prefix): each accepted unresolved
#: reference removed, in the inventory's row order.
REMOVED = (
    # 13: "A Cleric or Paladin can use a Holy Symbol as a Spellcasting Focus."
    (
        "equipment.adventuring_gear.holy_symbol",
        "holy_symbol",
        "Cleric or Paladin",
        CLASSES,
        "0c3ee4b4",
    ),
    # 16: "A Druid or Ranger can use such an object as a Spellcasting Focus."
    (
        "equipment.adventuring_gear.druidic_focus",
        "druidic_focus",
        "Druid or Ranger",
        CLASSES,
        "bdaf8271",
    ),
    # 21: "A Sorcerer, Warlock, or Wizard can use such an item as a
    # Spellcasting Focus."
    (
        "equipment.adventuring_gear.arcane_focus",
        "arcane_focus",
        "Sorcerer, Warlock, or Wizard",
        CLASSES,
        "99385f2f",
    ),
)

#: Real, non-empty overrides on the components whose citations change: the
#: service's reading must be the accepted one under each.
OVERRIDES = (
    RR._disable(
        MechanicalTargetKind.RECORD, "equipment.adventuring_gear.arcane_focus", None
    ),
    RR._disable(
        MechanicalTargetKind.COMPONENT,
        "equipment.adventuring_gear.druidic_focus",
        "druidic_focus",
    ),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# The candidate batch
# ---------------------------------------------------------------------------
def edited(base: EntryBatch) -> EntryBatch:
    """*base* without the removed references."""
    removed = {(r, c): (p, s) for r, c, p, s, _ in REMOVED}
    seen: Counter[tuple[str, str]] = Counter()

    def refs(c: EntryComponent) -> tuple[tuple[str, Any], ...]:
        where = (c.record or base.record_key(c.entry), c.key)
        if where not in removed:
            return c.refs
        seen[where] += 1
        pointer, scope = removed[where]
        (target,) = [t for x, t in c.refs if x == pointer]
        assert scoped(target) == (scope, ""), target
        return tuple((x, t) for x, t in c.refs if x != pointer)

    components = tuple(dataclasses.replace(c, refs=refs(c)) for c in base.components)
    assert seen == Counter(removed.keys()), seen
    # A record-owned reference would carry the same text on.
    texts = {(r, p) for r, _, p, _, _ in REMOVED}
    assert not [
        r for r in base.record_references if (base.record_key(r[0]), r[1]) in texts
    ]
    return dataclasses.replace(base, components=components)


def rebuilt(with_edits: bool) -> bytes:
    """The rendered Equipment proposal, rebuilt from the release as the
    recorded chain built it."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                base = FRA.generator(GENERATOR).batch()
                if with_edits:
                    base = edited(base)
                whole = build_entry_batch(session, base, binding)
                return render(whole.proposal).encode("utf-8")
        finally:
            engine.dispose()


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------
def composed(changed: dict[str, MechanicalProposal]) -> AcceptedInputs:
    """The recorded chain (``ACC.composed`` at its recorded evidence), *changed*
    accepted under the simulated reviewer in their recorded places."""
    fr = FINITE_REFERENCE
    finite = fr.proposals()
    playing = ACC.proposals()
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
        if batch in finite:
            proposal = finite[batch]
            rule, who, when = fr.APPROVAL, fr.OWNER, fr.RECORDED_AT
        if batch in playing:
            proposal = playing[batch]
            rule, who, when = ACC.APPROVAL, ACC.OWNER, RECORDED_AT
        if batch in changed:
            seen.add(batch)
            proposal = changed[batch]
            rule, who, when = SIMULATED_RULE, SIMULATED_REVIEWER, SIMULATED_AT
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


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    print("accepted counts", REPL._counts(rec))

    # Controls: the generator rebuilds the recorded proposal; the chain
    # rebuilds the committed artifact.
    same = rebuilt(with_edits=False) == RECORDED_FILE.read_bytes()
    print("control:", BATCH, "rebuilds", RECORDED_FILE.name, same)
    assert same
    control = composed({})
    same = serialize_accepted_inputs(control) == committed
    print("control: the recorded chain rebuilds the committed artifact", same)
    assert same

    # Candidate.
    data = rebuilt(with_edits=True)
    if write:
        PROPOSAL_FILE.write_bytes(data)
    assert PROPOSAL_FILE.read_bytes() == data, f"{PROPOSAL_FILE.name} drifted"
    recorded = load_proposal(RECORDED_FILE)
    candidate = load_proposal(PROPOSAL_FILE)
    changed = {BATCH: candidate}
    print(
        "candidate",
        PROPOSAL_FILE.name,
        "sha256",
        _sha(data),
        "identity",
        proposal_identity(candidate),
        "| recorded identity",
        proposal_identity(recorded),
    )
    moved = {
        name: (lost, len(added))
        for name, (lost, added) in APC.proposal_delta(recorded, candidate).items()
        if lost or added
    }
    for name, (lost, added) in moved.items():
        print(f"  proposal {name}: -{lost} +{added}")
    assert moved == {
        "proposed_representation.references": (len(REMOVED), 0),
        "proposed_representation.provenance": (len(REMOVED), 0),
    }, moved

    final = composed(changed)
    o = final.oracle
    violations = reference_resolution_violations(
        o.representation, o.reference_resolutions, o.binding
    )
    print("candidate counts", REPL._counts(final), "violations", len(violations))
    assert not violations, violations[:5]
    assert REPL._counts(final) == REPL._counts(rec)
    print("simulated bytes sha256", _sha(serialize_accepted_inputs(final)))

    # Resolutions: every accepted one kept verbatim; none added.
    assert reference_resolution_payload(
        rec.oracle.reference_resolutions
    ) == reference_resolution_payload(o.reference_resolutions)
    print("resolutions kept verbatim", len(o.reference_resolutions), "| drafts 0")

    # Findings, as multisets.
    before, after = APC.findings(rec), APC.findings(final)
    gone, new = Counter(before) - Counter(after), Counter(after) - Counter(before)
    print("findings (refs, leaves)", APC._split(before), "->", APC._split(after))
    for f, n in sorted(gone.items()):
        print("  cleared", n, f)
    assert not new, new
    expected = Counter(
        f"reference {s}:{p!r}: unresolved reference" for _, _, p, s, _ in REMOVED
    )
    assert gone == expected, gone

    # Citation identities: each removed key is gone, printed in its sentence
    # and cited by it alone; nothing is added; every other identity keeps its
    # target and provenance.
    delta = REPL.Delta(rec, final)
    old_t, new_t = FRA.targets(rec), FRA.targets(final)
    old_c, new_c = FRA.cited(rec), FRA.cited(final)
    for record, component, pointer, scope, prefix in REMOVED:
        (span,) = [s for s in delta.spans if s.startswith(prefix)]
        sentence = delta.text(span).replace("**", "")
        assert pointer in sentence and "Spellcasting Focus" in sentence
        key = (record, component, pointer, scope)
        assert old_t[key] == {""} and key not in new_t, key
        (cited,) = [k for k in old_c if k not in new_c and k[:3] == key[:3]]
        assert old_c[cited] == [span], cited
        print(f"{record}/{component} [{span[:8]}]: removed {pointer!r} ({scope})")
    others = {k for k in old_t if k not in new_t}
    assert others == {(r, c, p, s) for r, c, p, s, _ in REMOVED}, others
    assert not [k for k in new_t if k not in old_t]
    assert all(old_t[k] == new_t[k] for k in new_t)
    kept = [k for k in old_c if k in new_c]
    assert all(sorted(old_c[k]) == sorted(new_c[k]) for k in kept)
    assert len(old_c) - len(kept) == len(REMOVED) and len(new_c) == len(kept)
    print("every other citation identity keeps its target and provenance", len(new_t))

    # Projection: the service's candidate loses exactly the removed keys.
    def projected(inputs: AcceptedInputs) -> Counter[tuple[str, ...]]:
        return Counter(
            (r.from_record_key, r.from_component_key, r.source_text)
            + (r.target_record_key or "",)
            for r in candidate_from_accepted_inputs(inputs).representation.references
        )

    lost_p = projected(rec) - projected(final)
    assert not projected(final) - projected(rec)
    assert {k[:3] for k in lost_p} <= {(r, c, p) for r, c, p, _, _ in REMOVED}
    print(
        "projection",
        identify_projection(candidate_from_accepted_inputs(final)).projection_uuid,
        "| projected references lost",
        sum(lost_p.values()),
        "| added 0",
    )

    # Preservation: prose, bindings, expectations and the service's reading.
    assert RR.owned(rec) == RR.owned(final)
    assert RR.expectations(rec) == RR.expectations(final)
    print("prose bindings and reviewed expectations unchanged")
    for overrides in ((), OVERRIDES[:1], OVERRIDES[1:]):
        same = RR.consumer(rec, overrides) == RR.consumer(final, overrides)
        names = [x.override_id for x in overrides]
        print("consumer reading (members, readings, direct) unchanged", names, same)
        assert same

    # Semantic delta: references, their provenance, and the changed batch's
    # acceptance records (derived fields only).
    summary = {
        ".".join(p): (len(lost), len(add))
        for p, (lost, add) in delta.collections().items()
        if lost or add
    }
    print("delta by collection (-, +)", json.dumps(summary))
    assert summary["representation.references"] == (len(REMOVED), 0)
    assert summary["representation.provenance"] == (len(REMOVED), 0)
    assert set(summary) <= {
        "representation.references",
        "representation.provenance",
        "acceptance.batches",
        "acceptance.schema_anchors",
    }, summary
    derived = {"proposal_identity", "semantic_diff_hash", "diff"}
    for kind in ("batches", "schema_anchors"):
        lost, add = delta.collections()[("acceptance", kind)]
        assert [x["batch_id"] for x in lost] == [BATCH]
        for a in lost:
            (b,) = [x for x in add if x["batch_id"] == a["batch_id"]]
            assert {k: v for k, v in a.items() if k not in derived} == {
                k: v for k, v in b.items() if k not in derived
            }, a["batch_id"]
            assert b["proposal_identity"] == proposal_identity(candidate)
    print("  replaced: the changed batch's record and anchor, derived fields only")
    report = delta.report()
    body = ("\n".join(report) + "\n").encode("utf-8")
    if write:
        DELTA_FILE.write_bytes(body)
    assert DELTA_FILE.read_bytes() == body, "delta file drifted"
    print("delta", DELTA_FILE.name, len(report), "lines, sha256", _sha(body))

    assert ACCEPTED_PATH.read_bytes() == committed
    print("committed artifact unchanged", ACCEPTED_SHA256)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
