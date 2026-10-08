"""The Playing the Game atoms candidate, composed in memory.

CRD Issue 5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. There
is deliberately no recording step.

ADR-005d Decision 7 names a citation by its source record, owning component,
exact printed wording and scope. Each row of :data:`EDITS` is a printed
"Playing the Game" pointer whose sentence names a finite list of rules
("detailed in" / "see"). As in the accepted finite-reference atoms
(``issue-5d-finite-reference-atoms-REPLACEMENT.py``), each printed destination
gets its own citation identity in the same component, in the pointer's scope,
authored with its target, and the unresolved chapter pointer is retired: it is
the qualifier of those destinations, not a further pointer. The targets are
the accepted Playing the Game records owning each rule, the ones the accepted
Monsters generator's singular qualifiers already name (``QUALIFIED``: Armor
Class -> ``play.d20_tests``, Initiative -> ``play.combat``, Hit Points ->
``play.damage_and_healing``). The component prose, its spans, bindings and
expectations are unchanged.

Two accepted batches change: core-play-dependencies, rebuilt from its
recorded generator batch through ``RR.candidate_batch``, and monsters, rebuilt
as the recorded finite-reference candidate (``FRA.edited``) with these edits
applied after. The chain is the recorded finite-reference chain
(``ACC.composed``): the four other finite-reference batches keep the Owner's
recorded acceptance; the two changed batches take the simulated reviewer.
Controls: each generator rebuilds its recorded proposal byte for byte, and
the chain with no candidate rebuilds the committed artifact byte for byte.

No resolution is drafted or re-keyed: every new atom is authored with its
target, and every retired pointer was unresolved.

Run: ``python issue-5d-playing-the-game-atoms-REPLACEMENT.py [--write]``.
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
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    reference_target_key,
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


#: The recorded chain, through its last recording (the finite-reference
#: atoms, whose ACCEPT script pins its reviewed constructor and candidates).
ACC = _load(
    "finite_reference_atoms_accept",
    HERE / "issue-5d-finite-reference-atoms-ACCEPT.py",
)
FRA = ACC.FRA
CHARACTER_CREATION = ACC.CHARACTER_CREATION
FRAMING = ACC.FRAMING
ANIMALS_CATALOGUE = ACC.ANIMALS_CATALOGUE
APC = ACC.APC
REMAINING = ACC.REMAINING
RR = ACC.RR
REPL = ACC.REPL

ACCEPTED_PATH: Path = ACC.ACCEPTED_PATH
ACCEPTED_SHA256 = "005768c282669c3acf564b3efd70d1c54aa7307f4e47505b77b67e8612d73b84"
assert ACC.RECORDED_SHA256["recorded"] == ACCEPTED_SHA256
assert ACC.RECORDED_AT is not None
SCRATCH_DB: Path = REPL.SCRATCH_DB

TAG = "playing-the-game-atoms"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"

SIMULATED_REVIEWER: str = FRA.SIMULATED_REVIEWER
SIMULATED_RULE: str = FRA.SIMULATED_RULE
SIMULATED_AT: str = FRA.SIMULATED_AT

PLAY = "srd-5.2.1/playing-the-game"
Edit = FRA.Edit

#: batch -> its edits, in the inventory's row order.
EDITS: dict[str, tuple[Any, ...]] = {
    "core-play-dependencies": (
        # 68: "A table provides the monster's ability scores, modifiers, and
        # saving throw modifiers, all of which are detailed in "Playing the
        # Game."" Bare "modifiers" also occurs inside "saving throw modifiers".
        Edit(
            "glossary.stat_block",
            "ability_scores",
            "Playing the Game",
            PLAY,
            "295ea07b",
            (
                ("ability scores, modifiers", (PLAY, "play.six_abilities")),
                ("saving throw modifiers", (PLAY, "play.d20_tests")),
            ),
            ("ability scores, modifiers", "saving throw modifiers"),
        ),
        # 69: "These entries give the monster's Armor Class, Initiative, and
        # Hit Points, which are detailed in "Playing the Game.""
        Edit(
            "glossary.stat_block",
            "ac_initiative_hp",
            "Playing the Game",
            PLAY,
            "92a3a2c3",
            (
                ("Armor Class", (PLAY, "play.d20_tests")),
                ("Initiative", (PLAY, "play.combat")),
                ("Hit Points", (PLAY, "play.damage_and_healing")),
            ),
            ("Armor Class", "Initiative", "Hit Points"),
        ),
    ),
    "monsters": (
        # 70: "For more information on ability scores and saving throws, see
        # "Playing the Game.""
        Edit(
            "monsters.parts_of_a_stat_block",
            "ability_scores",
            "Playing the Game",
            PLAY,
            "87bd3a1f",
            (
                ("ability scores", (PLAY, "play.six_abilities")),
                ("saving throws", (PLAY, "play.d20_tests")),
            ),
            ("ability scores", "saving throws"),
        ),
    ),
}

#: Target -> the accepted components it owns that state the cited rule: each
#: target is the record owning those rules (no narrower ``play.`` record does).
OWNS = {
    "play.six_abilities": {"ability_scores", "ability_modifiers"},
    "play.d20_tests": {
        "saving_throws",
        "save_ability_modifier",
        "save_proficiency",
        "armor_class",
    },
    "play.combat": {"initiative_roll", "initiative_order"},
    "play.damage_and_healing": {"hit_points"},
}

#: Real, non-empty overrides on the components whose citations change: the
#: service's reading must be the accepted one under each.
OVERRIDES = (
    RR._disable(MechanicalTargetKind.RECORD, "glossary.stat_block", None),
    RR._disable(
        MechanicalTargetKind.COMPONENT,
        "monsters.parts_of_a_stat_block",
        "ability_scores",
    ),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def proposal_file(batch: str) -> Path:
    return HERE / f"issue-5d-{batch}-{TAG}-PROPOSAL.json"


def recorded_file(batch: str) -> Path:
    """The proposal file the recorded chain accepted for *batch*."""
    if batch in ACC.PROPOSALS:
        return FRA.proposal_file(batch)  # type: ignore[no-any-return]
    return FRA.recorded_file(batch)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# The candidate batches
# ---------------------------------------------------------------------------
def edited(batch: str, base: EntryBatch) -> EntryBatch:
    """*base* with each edit's atoms authored in the retired pointer's place
    (``FRA.edited``, over this candidate's edits)."""
    edits = {(e.record, e.component): e for e in EDITS[batch]}
    seen: Counter[tuple[str, str]] = Counter()

    def refs(c: EntryComponent) -> tuple[tuple[str, Any], ...]:
        where = (c.record or base.record_key(c.entry), c.key)
        if where not in edits:
            return c.refs
        seen[where] += 1
        e = edits[where]
        (target,) = [t for x, t in c.refs if x == e.pointer]
        assert scoped(target) == (e.scope, ""), target
        assert not {x for x, _ in e.added} & {x for x, _ in c.refs}, where
        return tuple(
            r for x, t in c.refs for r in (e.added if x == e.pointer else ((x, t),))
        )

    components = tuple(dataclasses.replace(c, refs=refs(c)) for c in base.components)
    assert seen == Counter(edits.keys()), (batch, seen)
    # A record-owned reference would take a component's text over.
    texts = {(e.record, x) for e in EDITS[batch] for x in (e.pointer, *e.cover)}
    assert not [
        r for r in base.record_references if (base.record_key(r[0]), r[1]) in texts
    ], batch
    return dataclasses.replace(base, components=components)


def rebuilt(with_edits: bool) -> dict[str, bytes]:
    """Each changed batch's rendered proposal, rebuilt from the release as the
    recorded chain built it."""
    out: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                for batch in EDITS:
                    base = FRA.generator(batch).batch()
                    if batch in RR.CHANGED:
                        base = RR.candidate_batch(batch, base)
                    if batch in FRA.EDITS:
                        base = FRA.edited(batch, base)
                    if with_edits:
                        base = edited(batch, base)
                    whole = build_entry_batch(session, base, binding)
                    out[batch] = render(whole.proposal).encode("utf-8")
        finally:
            engine.dispose()
    return out


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------
def composed(changed: dict[str, MechanicalProposal]) -> AcceptedInputs:
    """The recorded chain (``ACC.composed`` at its recorded evidence), *changed*
    accepted under the simulated reviewer in their recorded places."""
    recorded = ACC.proposals()
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
            rule, who, when = ACC.APPROVAL, ACC.OWNER, ACC.RECORDED_AT
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

    # Controls: every generator rebuilds its recorded proposal; the chain
    # rebuilds the committed artifact.
    for batch, data in rebuilt(with_edits=False).items():
        same = data == recorded_file(batch).read_bytes()
        print("control:", batch, "rebuilds", recorded_file(batch).name, same)
        assert same, batch
    control = composed({})
    same = serialize_accepted_inputs(control) == committed
    print("control: the recorded chain rebuilds the committed artifact", same)
    assert same

    # Candidates.
    changed: dict[str, MechanicalProposal] = {}
    for batch, data in rebuilt(with_edits=True).items():
        path = proposal_file(batch)
        if write:
            path.write_bytes(data)
        assert path.read_bytes() == data, f"{path.name} drifted"
        recorded = load_proposal(recorded_file(batch))
        changed[batch] = load_proposal(path)
        print(
            "candidate",
            path.name,
            "sha256",
            _sha(data),
            "identity",
            proposal_identity(changed[batch]),
            "| recorded identity",
            proposal_identity(recorded),
        )
        for name, (lost, added) in APC.proposal_delta(recorded, changed[batch]).items():
            if lost or added:
                print(f"  proposal {name}: -{lost} +{len(added)}")
                assert name in (
                    "proposed_representation.references",
                    "proposed_representation.provenance",
                ), name

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
        f"reference {e.scope}:{e.pointer!r}: unresolved reference"
        for es in EDITS.values()
        for e in es
    )
    assert gone == expected, gone

    # Citation identities: per edit, the pointer is gone, each printed
    # destination has one new identity in the same component, citing exactly
    # the sentence's span, and the sentence prints the pointer and the text.
    delta = REPL.Delta(rec, final)
    old_t, new_t = FRA.targets(rec), FRA.targets(final)
    old_c, new_c = FRA.cited(rec), FRA.cited(final)
    owns = RR.owned_by_component(final)
    records = {r.semantic_key for r in o.representation.records}
    for es in EDITS.values():
        for e in es:
            (span,) = [s for s in delta.spans if s.startswith(e.span)]
            sentence = delta.text(span).replace("**", "")
            assert e.pointer in sentence
            assert (e.record, e.component, e.pointer, e.scope) in old_t
            assert (e.record, e.component, e.pointer, e.scope) not in new_t
            print(f"{e.record}/{e.component} [{span[:8]}]: retired {e.pointer!r}")
            added = dict(e.added)
            assert set(added) == set(e.cover)
            for text in e.cover:
                assert text in sentence, text
                key = (e.record, e.component, text, e.scope)
                assert key not in old_t and new_t[key] == {added[text][1]}, text
                (ref,) = [
                    r
                    for r in o.representation.references
                    if (r.from_record_key, r.from_component_key, r.source_text)
                    == (e.record, e.component, text)
                ]
                assert new_c[reference_target_key(ref)] == [span], text
                target = added[text][1]
                assert target in records
                assert OWNS[target] <= {c for c, _ in owns[target]}, target
                assert not [r for r in records if r.startswith(target + ".")], target
                print(
                    f"   new {text!r} -> {target}"
                    f" (printed {sentence.count(text)}x; target owns"
                    f" {sorted(OWNS[target])})"
                )
    others = {k: v for k, v in old_t.items() if k not in new_t}
    assert len(others) == sum(map(len, EDITS.values())), others
    added_keys = {k for k in new_t if k not in old_t}
    assert len(added_keys) == sum(len(e.added) for es in EDITS.values() for e in es)
    assert all(old_t[k] == new_t[k] for k in old_t if k in new_t)
    # Every kept identity keeps its provenance: "saving throw" (glossary) sits
    # beside the new "saving throws" (play) in the monsters component.
    kept = [k for k in old_c if k in new_c]
    assert all(sorted(old_c[k]) == sorted(new_c[k]) for k in kept)
    assert len(old_c) - len(kept) == len(others)
    print(
        "every other citation identity keeps its target and provenance",
        len(new_t) - len(added_keys),
    )

    # Projection: the service's candidate names each new atom's record.
    candidate = candidate_from_accepted_inputs(final)
    projected = {
        (r.from_record_key, r.from_component_key, r.source_text): r.target_record_key
        for r in candidate.representation.references
    }
    for es in EDITS.values():
        for e in es:
            for text, (_, dest) in e.added:
                assert projected[(e.record, e.component, text)] == dest
    print(
        "projection",
        identify_projection(candidate).projection_uuid,
        "| new atoms projected to their records",
        sum(len(e.added) for es in EDITS.values() for e in es),
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
    _, _, direct = RR.consumer(final, OVERRIDES[1:])
    ability = {
        s
        for c, s in RR.owned_by_component(final)["monsters.parts_of_a_stat_block"]
        if c == "ability_scores"
    }
    assert ability and not ability & set(direct["monsters.parts_of_a_stat_block"])

    # Semantic delta: references, their provenance, and the changed batches'
    # acceptance records (derived fields only).
    summary = {
        ".".join(p): (len(lost), len(add))
        for p, (lost, add) in delta.collections().items()
        if lost or add
    }
    print("delta by collection (-, +)", json.dumps(summary))
    assert set(summary) <= {
        "representation.references",
        "representation.provenance",
        "acceptance.batches",
        "acceptance.schema_anchors",
    }, summary
    derived = {"proposal_identity", "semantic_diff_hash", "diff"}
    for kind in ("batches", "schema_anchors"):
        lost, add = delta.collections()[("acceptance", kind)]
        assert sorted(x["batch_id"] for x in lost) == sorted(EDITS)
        for a in lost:
            (b,) = [x for x in add if x["batch_id"] == a["batch_id"]]
            assert {k: v for k, v in a.items() if k not in derived} == {
                k: v for k, v in b.items() if k not in derived
            }, a["batch_id"]
            assert b["proposal_identity"] == proposal_identity(changed[b["batch_id"]])
    print("  replaced: the changed batches' records and anchors, derived fields only")
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
