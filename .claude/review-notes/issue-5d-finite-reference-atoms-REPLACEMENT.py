"""The finite-reference-atoms candidate, composed in memory.

CRD Issue 5d finite reference atoms (#132, #137). REVIEW MATERIAL: nothing
here is accepted, recorded, published or activated, and no Owner approval
exists for it. There is deliberately no recording step.

ADR-005d Decision 7 names a citation by its source record, owning component,
exact printed wording and scope. Each row of :data:`EDITS` is a printed
chapter pointer ("see Monsters", "appear in Rules Glossary") whose sentence
names a finite list of destinations. Each destination the sentence prints gets
its own citation identity in the same component: most already have one; the
candidate authors the missing ones (:data:`EDITS` ``added``) with their target,
as the same components already author ``Speed`` and ``Potions of Healing``.
Once every printed destination has its own resolved identity
(:data:`EDITS` ``cover``), the unresolved chapter pointer is retired from the
component's references: it is the qualifier of those destinations, not a
further pointer (the #34/#38 reading, applied here to accepted proposals).
A multi-class spell-list pointer ("the Cleric, Druid, or Wizard spell list")
is the same shape: each class it prints is cited by its name and targets that
class's record, which holds the class's Spell List, as the accepted
classes generator already targets a singular "<Class> spell list".
The component prose, its spans, bindings and expectations are unchanged.

Five accepted batches change, each rebuilt from its recorded generator batch
(``RR.candidate_batch`` first where the remaining-references recording
replaced it). The changed batches are shown in the recorded chain rebuilt
from its recorded evidence (``APC.composed``), then the later recordings
reapplied: the remaining-references drafts, the Animals catalogue drafts,
framing coverage and the Character Creation catalogue. Controls: each
generator rebuilds its recorded proposal byte for byte, and the chain with no
candidate rebuilds the committed artifact byte for byte.

No resolution is drafted or re-keyed: every new atom is authored with its
target, and every retired pointer was unresolved.

Run: ``python issue-5d-finite-reference-atoms-REPLACEMENT.py [--write]``.
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
    read_accepted,
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
    ProvenanceTargetKind,
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


#: The recorded chain, through its last recording.
CHARACTER_CREATION = _load(
    "character_creation_catalogue_accept",
    HERE / "issue-5d-character-creation-catalogue-ACCEPT.py",
)
FRAMING = CHARACTER_CREATION.FRAMING
ANIMALS_CATALOGUE = FRAMING.ANIMALS_CATALOGUE
APC = ANIMALS_CATALOGUE.APC
REMAINING = APC.REMAINING
RR = REMAINING.RR
REPL = REMAINING.REPL

ACCEPTED_PATH: Path = CHARACTER_CREATION.ACCEPTED_PATH
ACCEPTED_SHA256 = "ea0c219feec8571142c797ebd127713d55595db7309c64670a1436756b4413de"
assert CHARACTER_CREATION.RECORDED_SHA256["recorded"] == ACCEPTED_SHA256
SCRATCH_DB: Path = REPL.SCRATCH_DB

TAG = "finite-reference-atoms"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"

SIMULATED_REVIEWER: str = REMAINING.SIMULATED_REVIEWER
SIMULATED_RULE: str = REMAINING.SIMULATED_RULE
SIMULATED_AT: str = REMAINING.SIMULATED_AT

EQUIPMENT = "srd-5.2.1/equipment"
MONSTERS = "srd-5.2.1/monsters"
GLOSSARY = "srd-5.2.1/rules-glossary"
CLASSES = "srd-5.2.1/classes"

#: The classes a printed spell-list alternative names, in printed order.
LIST_6 = ("Bard", "Cleric", "Druid", "Wizard")
LIST_14 = ("Cleric", "Druid", "Wizard")


@dataclasses.dataclass(frozen=True)
class Edit:
    """One printed chapter pointer and the destinations its sentence names."""

    record: str
    component: str
    #: The accepted unresolved pointer retired, and its scope.
    pointer: str
    scope: str
    #: The span printing the sentence (prefix of its id).
    span: str
    #: New atoms: (exact printed text, (scope, target record)).
    added: tuple[tuple[str, tuple[str, str]], ...]
    #: Every destination the sentence prints, each its own resolved identity
    #: in the component once ``added`` is authored.
    cover: tuple[str, ...]


#: batch -> its edits, in the review's row order.
EDITS: dict[str, tuple[Edit, ...]] = {
    "classes": (
        # 26: "Choose one type of Artisan's Tools or Musical Instrument (see
        # Equipment)".
        Edit(
            "classes.monk",
            "core_traits",
            "Equipment",
            EQUIPMENT,
            "ffecf855",
            (),
            ("Artisan's Tools", "Musical Instrument"),
        ),
        # 6: "the Bard, Cleric, Druid, and Wizard spell lists ... (see a class's
        # section for its spell list)". Each class record holds its Spell List,
        # as the accepted singular "<Class> spell list" citations target.
        Edit(
            "classes.bard.magical_secrets",
            "magical_secrets",
            "Bard, Cleric, Druid, and Wizard spell lists",
            CLASSES,
            "d7211994",
            tuple((n, (CLASSES, f"classes.{n.lower()}")) for n in LIST_6),
            LIST_6,
        ),
        # 14: "the Cleric, Druid, or Wizard spell list or any combination thereof
        # (see a class's section for its spell list)".
        Edit(
            "classes.bard.college_of_lore.magical_discoveries",
            "magical_discoveries",
            "Cleric, Druid, or Wizard spell list",
            CLASSES,
            "f800d93d",
            tuple((n, (CLASSES, f"classes.{n.lower()}")) for n in LIST_14),
            LIST_14,
        ),
    ),
    "character-origins-feats": (
        # 15: "two cantrips of your choice from the Cleric, Druid, or Wizard
        # spell list".
        Edit(
            "feats.magic_initiate",
            "two_cantrips",
            "Cleric, Druid, or Wizard spell list",
            CLASSES,
            "647b8905",
            tuple((n, (CLASSES, f"classes.{n.lower()}")) for n in LIST_14),
            LIST_14,
        ),
    ),
    "spell-descriptions": (
        # 56: a Skeleton ... or a Zombie ... (see "Monsters" for the stat blocks).
        Edit(
            "spells.animate_dead",
            "effect",
            "Monsters",
            MONSTERS,
            "07dc161d",
            (),
            ("Skeleton", "Zombie"),
        ),
        # 59: Ghouls, Ghasts, Wights, Mummies. See "Monsters" for these stat blocks.
        Edit(
            "spells.create_undead",
            "using_a_higher_level_spell_slot",
            "Monsters",
            MONSTERS,
            "44b9874b",
            (),
            ("Ghouls", "Ghasts", "Wights", "Mummies"),
        ),
    ),
    "magic-items": (
        # 28: "Equipment" contains rules on brewing _Potions of Healing_ and
        # scribing _Spell Scrolls_. The rules, not the items they make.
        Edit(
            "magic_items.crafting_magic_items",
            "crafting_magic_items",
            "Equipment",
            EQUIPMENT,
            "58be38f3",
            (
                (
                    "brewing _Potions of Healing_",
                    (EQUIPMENT, "equipment.brewing_potions_of_healing"),
                ),
                (
                    "scribing _Spell Scrolls_",
                    (EQUIPMENT, "equipment.scribing_spell_scrolls"),
                ),
            ),
            ("brewing _Potions of Healing_", "scribing _Spell Scrolls_"),
        ),
        # 31: Statistics for the Rowboat and Keelboat appear in "Equipment."
        Edit(
            "magic_items.folding_boat",
            "folding_boat",
            "Equipment",
            EQUIPMENT,
            "9fc720fe",
            (),
            ("Rowboat", "Keelboat"),
        ),
    ),
    "monsters": (
        # 74: the following speeds: Burrow, Climb, Fly, Swim. Rules for Speed
        # and these special speeds appear in "Rules Glossary."
        Edit(
            "monsters.parts_of_a_stat_block",
            "speed",
            "Rules Glossary",
            GLOSSARY,
            "fa7f80a7",
            (
                ("Burrow", (GLOSSARY, "glossary.burrow_speed")),
                ("Climb", (GLOSSARY, "glossary.climb_speed")),
                ("Fly", (GLOSSARY, "glossary.fly_speed")),
                ("Swim", (GLOSSARY, "glossary.swim_speed")),
            ),
            ("Speed", "Burrow", "Climb", "Fly", "Swim"),
        ),
        # 75: the Magic action ... and maintain Concentration ..., as described
        # in "Rules Glossary."
        Edit(
            "monsters.parts_of_a_stat_block",
            "spellcasting",
            "Rules Glossary",
            GLOSSARY,
            "5bbea148",
            (),
            ("Magic action", "Concentration"),
        ),
    ),
}

#: batch -> (generator, its batch function).
BUILD = {
    "classes": ("classes", "batch"),
    "character-origins-feats": ("character-origins-feats", "batch"),
    "spell-descriptions": ("spell-descriptions", "batch"),
    "magic-items": ("magic-items", "batch"),
    "monsters": ("monsters", "batch"),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def proposal_file(batch: str) -> Path:
    return HERE / f"issue-5d-{batch}-{TAG}-PROPOSAL.json"


def recorded_file(batch: str) -> Path:
    """The proposal file the recorded chain accepted for *batch*."""
    if batch in REMAINING.PROPOSALS:
        return REMAINING.proposal_path(batch)  # type: ignore[no-any-return]
    return HERE / f"issue-5d-{batch}-{REPL.REPLACEMENT.TAG}-PROPOSAL.json"


def generator(name: str) -> ModuleType:
    return _load(f"rr_{name.replace('-', '_')}", HERE / f"issue-5d-{name}-generator.py")


# ---------------------------------------------------------------------------
# The candidate batches
# ---------------------------------------------------------------------------
def edited(batch: str, base: EntryBatch) -> EntryBatch:
    """*base* with each edit's atoms authored in the retired pointer's place."""
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
    # A record-owned reference would take the retired text over (authoring
    # reuses a component's pointer only while the component states it).
    pointers = {(e.record, e.pointer) for e in EDITS[batch]}
    assert not [
        r for r in base.record_references if (base.record_key(r[0]), r[1]) in pointers
    ], batch
    return dataclasses.replace(base, components=components)


def rebuilt(rec: AcceptedInputs, with_edits: bool) -> dict[str, bytes]:
    """Each changed batch's rendered proposal, rebuilt from the release as its
    recorded generator (and the remaining-references candidate) builds it."""
    out: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                for batch, (name, fn) in BUILD.items():
                    module = generator(name)
                    base = getattr(module, fn)()
                    if batch in RR.CHANGED:
                        base = RR.candidate_batch(batch, base)
                    if with_edits:
                        base = edited(batch, base)
                    whole = build_entry_batch(session, base, binding)
                    if batch == "magic-items":
                        whole = read_accepted(
                            whole, rec.oracle.representation, module.CROSS_READS
                        )
                    out[batch] = render(whole.proposal).encode("utf-8")
        finally:
            engine.dispose()
    return out


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------
def composed(changed: dict[str, MechanicalProposal]) -> AcceptedInputs:
    """The committed chain rebuilt from its recorded evidence, *changed*
    accepted under the simulated reviewer in their recorded places."""
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


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    return REPL._counts(inputs)  # type: ignore[no-any-return]


def targets(inputs: AcceptedInputs) -> dict[tuple[str, str, str, str], set[str]]:
    """(record, component, text, scope) -> its targets: authored, else resolved;
    ``""`` for an unresolved pointer."""
    rep = inputs.oracle.representation
    resolved = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): (
            r.target_record_key
        )
        for r in inputs.oracle.reference_resolutions
    }
    out: dict[tuple[str, str, str, str], set[str]] = {}
    for r in rep.references:
        k = (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        out.setdefault(k, set()).add(r.target_record_key or resolved.get(k, ""))
    return out


def cited(inputs: AcceptedInputs) -> dict[tuple[str, ...], list[str]]:
    out: dict[tuple[str, ...], list[str]] = {}
    for claim in inputs.oracle.representation.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            out.setdefault(tuple(claim.target_key), []).append(claim.span_id)
    return out


#: Real, non-empty overrides on components whose citations change: the
#: service's reading must be the accepted one under each.
OVERRIDES = (
    RR._disable(MechanicalTargetKind.RECORD, "magic_items.folding_boat", None),
    RR._disable(
        MechanicalTargetKind.COMPONENT, "monsters.parts_of_a_stat_block", "speed"
    ),
)


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    print("accepted counts", _counts(rec))

    # Controls: every generator rebuilds its recorded proposal; the chain
    # rebuilds the committed artifact.
    for batch, data in rebuilt(rec, with_edits=False).items():
        same = data == recorded_file(batch).read_bytes()
        print("control:", batch, "rebuilds", recorded_file(batch).name, same)
        assert same, batch
    control = composed({})
    same = serialize_accepted_inputs(control) == committed
    print("control: the recorded chain rebuilds the committed artifact", same)
    assert same

    # Candidates.
    changed: dict[str, MechanicalProposal] = {}
    for batch, data in rebuilt(rec, with_edits=True).items():
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
    print("candidate counts", _counts(final), "violations", len(violations))
    assert not violations, violations[:5]
    assert _counts(final) == _counts(rec)
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
    # destination resolves in the same component, each new atom cites exactly
    # the sentence's span, and the sentence prints every covered text.
    delta = REPL.Delta(rec, final)
    old_t, new_t, new_c = targets(rec), targets(final), cited(final)
    for es in EDITS.values():
        for e in es:
            (span,) = [s for s in delta.spans if s.startswith(e.span)]
            sentence = delta.text(span)
            assert (e.record, e.component, e.pointer, e.scope) in old_t
            assert (e.record, e.component, e.pointer, e.scope) not in new_t
            print(f"{e.record}/{e.component}: retired {e.pointer!r} ({e.scope})")
            for text in e.cover:
                (hit,) = [
                    (k, t)
                    for k, t in new_t.items()
                    if k[:3] == (e.record, e.component, text)
                ]
                (target,) = hit[1]
                assert target and text in sentence.replace("**", ""), text
                fresh = text in {x for x, _ in e.added}
                if fresh:
                    (ref,) = [
                        r
                        for r in o.representation.references
                        if (r.from_record_key, r.from_component_key, r.source_text)
                        == (e.record, e.component, text)
                    ]
                    assert new_c[reference_target_key(ref)] == [span], text
                    assert hit[0] not in old_t
                else:
                    assert old_t[hit[0]] == new_t[hit[0]], text
                print(f"   {'new' if fresh else 'kept'} {text!r} -> {target}")
    others = {k: v for k, v in old_t.items() if k not in new_t}
    assert len(others) == sum(map(len, EDITS.values())), others
    added = {k for k in new_t if k not in old_t}
    assert len(added) == sum(len(e.added) for es in EDITS.values() for e in es)
    assert all(old_t[k] == new_t[k] for k in old_t if k in new_t)
    print("every other citation identity and target unchanged", len(new_t) - len(added))

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
                assert dest in {r.semantic_key for r in o.representation.records}
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
    speed = {
        s
        for c, s in RR.owned_by_component(final)["monsters.parts_of_a_stat_block"]
        if c == "speed"
    }
    assert speed and not speed & set(direct["monsters.parts_of_a_stat_block"])

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
