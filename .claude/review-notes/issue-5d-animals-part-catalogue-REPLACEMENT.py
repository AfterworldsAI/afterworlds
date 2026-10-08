"""The Animals part-catalogue candidate, composed in memory.

CRD Issue 5d Animals part catalogue (#132, #137). REVIEW MATERIAL: nothing
here is accepted, recorded, published or activated, and no Owner approval
exists for it. There is deliberately no recording step.

*Wild Shape* ("see "Animals" in "Monsters" for stat block options") and
*Polymorph* ("See the "Animals" section of "Monsters" for a sample of Beast
stat blocks") cite the *Animals* part as such: rows 1, 2, 47 and 63 of
``issue-5d-remaining-references-review.md``, held as U-part because the part
has no record. The recorded Animals batch reads every leaf below the
``# Animals`` heading and leaves the heading uncovered (leaf ``eb6c81a0``).

The candidate changes that one batch through the native seams the accepted
catalogue sections use (``spells.spell_descriptions``, a heading-only
``general_rule`` section, and ``magic_items.magic_items_a_z``): the part is a
placed section ``animals.animals`` over the release container ``("Animals",)``
with its heading as its one prose-bound component, and ``EntryBatch.members``
declares each of the 95 stat blocks it prints a ``CATALOGUE_MEMBER`` of it, in
printed order, checked by :func:`build_entry_batch` against the release's
containment. No stat block, component, reading or reference of the recorded
batch changes, and no other batch is touched.

The acceptance module has no supersession, so the chain is shown as the
remaining-references recording composed it
(``issue-5d-remaining-references-ACCEPT.py``): the twenty-two recorded
proposals over no prior, each with its recorded evidence and resolutions, the
Animals batch alone taking the candidate under the simulated reviewer; then
the 29 recorded remaining-references resolutions; then the four drafts,
simulated. A control run with no candidate must rebuild the committed
artifact byte for byte, and one with the recorded generator's batch must
rebuild the recorded Animals proposal byte for byte.

Run: ``python issue-5d-animals-part-catalogue-REPLACEMENT.py [--write]``.
Without ``--write`` it checks the three review files below against a fresh
construction; with it, it writes them. It writes nothing else.
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
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    batch_findings,
    build_entry_batch,
    read_accepted,
    render,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
    published_release_binding,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceResolution,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    validate_candidate,
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
    RecordKind,
    RelationshipKind,
    reference_target_key,
)
from afterworlds.models.enums import (  # noqa: E402
    OverrideOperationEnum,
    OverrideOriginEnum,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.services.rules_authority.override_set import (  # noqa: E402
    EffectiveOverrideEntry,
)
from afterworlds.services.rules_authority.targets import (  # noqa: E402
    MechanicalTarget,
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


#: The recorded remaining-references composition and its constructor.
REMAINING = _load(
    "remaining_references_accept", HERE / "issue-5d-remaining-references-ACCEPT.py"
)
RR = REMAINING.RR
REPL = REMAINING.REPL
#: The recorded Animals generator, read, never edited.
GEN = _load("issue_5d_animals_generator", HERE / "issue-5d-animals-generator.py")
MG = GEN.MG

ACCEPTED_PATH: Path = REMAINING.ACCEPTED_PATH
ACCEPTED_SHA256: str = REMAINING.RECORDED_SHA256["resolved"]
ANIMALS_PROPOSAL = HERE / GEN.PROPOSAL_FILE
ANIMALS_PROPOSAL_SHA256 = (
    "a3057b73ec23db2bf169286446e25047ef7d54ebc96061083e3c9a2d48045ebb"
)
SCRATCH_DB: Path = REPL.SCRATCH_DB

PROPOSAL_FILE = HERE / "issue-5d-animals-part-catalogue-PROPOSAL.json"
DRAFTS_FILE = HERE / "issue-5d-animals-part-catalogue-resolutions-DRAFTS.json"
DELTA_FILE = HERE / "issue-5d-animals-part-catalogue-DELTA.txt"

#: The part as a placed section: its slug, record key and heading leaf.
SECTION = "animals"
SECTION_KEY = "animals.animals"
HEADING = "# Animals"
#: Every new draft id carries this suffix, and none of the recorded 1,434.
SUFFIX = "-animals-part-1"
#: The held rows, in review order: (citing record, component, printed pointer,
#: scope), and the exact printed words of the one pointer each occurs in.
ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("classes.druid.wild_shape", "known_forms", "Animals", GEN.ANIMALS),
    ("spells.polymorph", "effect", "Animals", GEN.ANIMALS),
    ("classes.druid.wild_shape", "known_forms", "Monsters", MG.MONSTERS),
    ("spells.polymorph", "effect", "Monsters", MG.MONSTERS),
)
POINTERS = {
    "classes.druid.wild_shape": 'see "Animals" in "Monsters" for stat block options',
    "spells.polymorph": 'See the "Animals" section of "Monsters" for a sample of '
    "Beast stat blocks.",
}

SIMULATED_REVIEWER: str = REMAINING.SIMULATED_REVIEWER
SIMULATED_RULE: str = REMAINING.SIMULATED_RULE
SIMULATED_AT: str = REMAINING.SIMULATED_AT

#: Batches, records, spans, review units, resolutions; then reference and
#: uncovered-leaf findings on the release.
EXPECTED = {
    "accepted": ((22, 1832, 10484, 1459, 1434), (68, 29)),
    "candidate": ((22, 1833, 10485, 1460, 1434), (68, 28)),
    "drafted": ((22, 1833, 10485, 1460, 1438), (64, 28)),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    return REPL._counts(inputs)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# The candidate batch
# ---------------------------------------------------------------------------
def candidate_batch(base: EntryBatch) -> EntryBatch:
    """The recorded Animals batch with the part placed as a section before
    its stat blocks, each of them declared its member in printed order."""
    assert SECTION not in {e for e, _, _ in base.entries} | set(base.placements)
    assert not base.members and not base.edges and not base.records
    return dataclasses.replace(
        base,
        entries=((SECTION, GEN.PART, RecordKind.GENERAL_RULE), *base.entries),
        expected_leaves=base.expected_leaves + 1,
        clauses=((SECTION, SECTION, (None,), (HEADING,)), *base.clauses),
        components=(
            EntryComponent(SECTION, SECTION, GEN.P, GEN.NO_USE),
            *base.components,
        ),
        placements={
            SECTION: Placement(
                SECTION_KEY,
                (GEN.PART,),
                HEADING,
                ReviewUnitKind.SECTION,
                tuple((GEN.PART, n) for n in GEN.NAMES),
            ),
            **base.placements,
        },
        members=tuple((GEN.slug(n), SECTION) for n in GEN.NAMES),
    )


def build(with_candidate: bool) -> Built:
    """The recorded generator's build, on a copy of the release store: the
    batch, then each component's accepted governing reads."""
    batch = GEN.batch()
    if with_candidate:
        batch = candidate_batch(batch)
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                built = build_entry_batch(
                    session, batch, published_release_binding(session)
                )
                reads = GEN.reads(session)
                for cut, read in GEN._each_read(reads):
                    built = read_accepted(built, cut, read)
                found = batch_findings(built)
        finally:
            engine.dispose()
    # As ``emit`` checks: a clean partition and units, and only the findings
    # the packet alone cannot see (accepted targets and accepted reads).
    assert not found["partition"] and not found["review_units"], found
    assert found["representation"] == GEN.expected_representation_findings(
        GEN.ANIMALS_CHUNK, reads
    )
    return built


def proposal_delta(
    old: MechanicalProposal, new: MechanicalProposal
) -> dict[str, tuple[int, list[Any]]]:
    """Per proposal collection: (items lost, items added)."""
    a, b = json.loads(render_proposal(old)), json.loads(render_proposal(new))
    out: dict[str, tuple[int, list[Any]]] = {}
    for top in a:
        if isinstance(a[top], dict) and top == "proposed_representation":
            pairs = [(f"{top}.{k}", a[top][k], b[top][k]) for k in a[top]]
        else:
            pairs = [(top, a[top], b[top])]
        for name, x, y in pairs:
            if not isinstance(x, list):
                assert x == y or name == "proposal_origin", name
                continue
            ca = Counter(json.dumps(i, sort_keys=True) for i in x)
            cb = Counter(json.dumps(i, sort_keys=True) for i in y)
            out[name] = (
                sum((ca - cb).values()),
                [json.loads(k) for k in (cb - ca).elements()],
            )
    return out


def render_proposal(p: MechanicalProposal) -> str:
    return render(p)


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------
def composed(
    base: AcceptedInputs, animals: MechanicalProposal | None
) -> AcceptedInputs:
    """The committed chain rebuilt from its recorded evidence, as
    ``REMAINING.composed`` then ``REMAINING.resolved`` recorded it, the Animals
    batch taking *animals* under the simulated reviewer when given."""
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
        if batch == "animals" and animals is not None:
            seen = True
            proposal = animals
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
    assert seen or animals is None
    inputs = resolve(steps["equipment-cited"])
    return REMAINING.resolved(  # type: ignore[no-any-return]
        base, inputs, REMAINING.OWNER, REMAINING.RECORDED_AT[1]
    )


# ---------------------------------------------------------------------------
# The four drafts
# ---------------------------------------------------------------------------
def draft_resolutions(
    inputs: AcceptedInputs, texts: dict[str, str]
) -> tuple[ReferenceResolution, ...]:
    """Each held row to the part's record, cited from the spans the oracle
    cites its reference from, as ``GEN.draft_targets`` cites. Each span must
    print the one pointer the row's text occurs in (*texts*: span -> text)."""
    rep = inputs.oracle.representation
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in rep.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    unresolved = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): r
        for r in rep.references
        if not r.target_record_key
    }
    resolved = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in inputs.oracle.reference_resolutions
    }
    out = []
    for row in ROWS:
        record, component, text, scope = row
        assert row in unresolved and row not in resolved, row
        spans = tuple(cited[reference_target_key(unresolved[row])])
        assert len(spans) == 1 and POINTERS[record] in texts[spans[0]], row
        out.append(
            ReferenceResolution(
                resolution_id=(
                    f"resolve-{MG._slug(record)}-{MG._slug(component)}"
                    f"-{MG._slug(text)}{SUFFIX}"
                ),
                from_record_key=record,
                from_component_key=component,
                source_text=text,
                scope_key=scope,
                target_record_key=SECTION_KEY,
                release_binding=inputs.oracle.binding,
                provenance_span_ids=spans,
            )
        )
    ids = {r.resolution_id for r in out}
    assert len(ids) == len(out)
    assert not ids & {r.resolution_id for r in inputs.oracle.reference_resolutions}
    return tuple(out)


def drafted(
    inputs: AcceptedInputs, drafts: tuple[ReferenceResolution, ...]
) -> AcceptedInputs:
    return resolve_references(
        inputs,
        resolutions=drafts,
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def findings(inputs: AcceptedInputs) -> list[str]:
    candidate = candidate_from_accepted_inputs(inputs)
    binding = inputs.oracle.binding
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                corpus = load_bound_corpus(
                    session, binding.package_uuid, binding.release_version
                )
                found = list(validate_candidate(candidate, corpus))
        finally:
            engine.dispose()
    return found


def _split(found: list[str]) -> tuple[int, int]:
    refs = [f for f in found if f.startswith("reference ")]
    leaves = [f for f in found if f.startswith("leaf ")]
    assert len(refs) + len(leaves) == len(found), found[:5]
    return len(refs), len(leaves)


# ---------------------------------------------------------------------------
# Consumer: the rules-authority service's own reading
# ---------------------------------------------------------------------------
def _disable(kind: MechanicalTargetKind, record: str, component: str | None) -> Any:
    return EffectiveOverrideEntry(
        override_id=f"disable-{record}-{component or 'record'}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(kind=kind, record_key=record, component_key=component),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )


RIDING_HORSE = "animals.riding_horse"
#: Real, non-empty overrides: one member disabled whole, and the part's own
#: record disabled whole.
OVERRIDES = (
    _disable(MechanicalTargetKind.RECORD, RIDING_HORSE, None),
    _disable(MechanicalTargetKind.RECORD, SECTION_KEY, None),
)


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    assert _counts(rec) == EXPECTED["accepted"][0], _counts(rec)

    # Proposal: the recorded bytes, rebuilt; then the candidate over them.
    recorded_bytes = ANIMALS_PROPOSAL.read_bytes()
    assert _sha(recorded_bytes) == ANIMALS_PROPOSAL_SHA256
    recorded = load_proposal(ANIMALS_PROPOSAL)
    same = render(build(with_candidate=False).proposal).encode() == recorded_bytes
    print("control: the recorded generator rebuilds the recorded proposal", same)
    assert same
    rendered = render(build(with_candidate=True).proposal).encode("utf-8")
    if write:
        PROPOSAL_FILE.write_bytes(rendered)
    assert PROPOSAL_FILE.read_bytes() == rendered, "proposal file drifted"
    candidate = load_proposal(PROPOSAL_FILE)
    print(
        "candidate proposal",
        PROPOSAL_FILE.name,
        "sha256",
        _sha(rendered),
        "identity",
        proposal_identity(candidate),
        "| recorded identity",
        proposal_identity(recorded),
    )
    pdelta = proposal_delta(recorded, candidate)
    for name, (lost, added) in pdelta.items():
        if lost or added:
            print(f"  proposal {name}: -{lost} +{len(added)}")
    assert not any(lost for lost, _ in pdelta.values()), "a recorded item changed"
    added_rels = pdelta["proposed_representation.relationships"][1]
    assert {(r["target_record_key"], r["kind"]) for r in added_rels} == {
        (SECTION_KEY, RelationshipKind.CATALOGUE_MEMBER.value)
    } and len(added_rels) == len(GEN.NAMES)

    # Chain: control first, then the candidate.
    base = REMAINING.prior()
    control = composed(base, None)
    same = serialize_accepted_inputs(control) == committed
    print("control: the recorded chain rebuilds the committed artifact", same)
    assert same
    step = composed(base, candidate)
    texts = REPL.Delta(rec, step)
    span_text = {s: texts.text(s) for s in texts.spans}
    drafts = draft_resolutions(step, span_text)
    payload = reference_resolution_payload(drafts)
    raw = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    if write:
        DRAFTS_FILE.write_bytes(raw)
    assert DRAFTS_FILE.read_bytes() == raw, "drafts file drifted"
    print("drafts", DRAFTS_FILE.name, "sha256", _sha(raw), len(drafts))
    for d in drafts:
        print("  ", d.resolution_id, "->", d.target_record_key, d.provenance_span_ids)
    final = drafted(step, drafts)

    found: dict[str, list[str]] = {"accepted": findings(rec)}
    for state, inputs in (("candidate", step), ("drafted", final)):
        o = inputs.oracle
        violations = reference_resolution_violations(
            o.representation, o.reference_resolutions, o.binding
        )
        found[state] = findings(inputs)
        print(
            state,
            "counts",
            _counts(inputs),
            "violations",
            len(violations),
            "reference, uncovered-leaf findings",
            _split(found[state]),
        )
        assert not violations, violations[:5]
        assert (_counts(inputs), _split(found[state])) == EXPECTED[state]
    gone = Counter(found["accepted"]) - Counter(found["drafted"])
    assert not Counter(found["drafted"]) - Counter(found["accepted"])
    print("findings cleared", sum(gone.values()))
    for f, n in sorted(gone.items()):
        print("  ", n, f)
    print("simulated bytes sha256", _sha(serialize_accepted_inputs(final)))

    # Preservation: the whole semantic delta is additions, each the section's.
    delta = REPL.Delta(rec, final)
    (heading,) = (
        s["span_id"] for s in delta.new["spans"] if delta.text(s["span_id"]) == HEADING
    )
    summary = {
        ".".join(p): (len(lost), len(added))
        for p, (lost, added) in delta.collections().items()
        if lost or added
    }
    print("delta by collection (-, +)", json.dumps(summary))
    # The one replaced item per collection is the Animals batch's own batch
    # record and schema anchor, keyed by its proposal identity: the batch
    # diff keeps every recorded row and adds the heading's, the anchor keeps
    # its schema.
    replaced = {
        p: (lost, added) for p, (lost, added) in delta.collections().items() if lost
    }
    assert set(replaced) == {
        ("acceptance", "batches"),
        ("acceptance", "schema_anchors"),
    }
    (old_b,), (new_b,) = replaced[("acceptance", "batches")]
    (old_a,), (new_a,) = replaced[("acceptance", "schema_anchors")]
    assert old_b["batch_id"] == new_b["batch_id"] == old_a["batch_id"] == "animals"
    old_diff = Counter(json.dumps(x, sort_keys=True) for x in old_b["diff"])
    new_diff = Counter(json.dumps(x, sort_keys=True) for x in new_b["diff"])
    assert not old_diff - new_diff and sum((new_diff - old_diff).values()) == 1
    (added_row,) = (new_diff - old_diff).elements()
    assert json.loads(added_row)["span_id"] == heading
    # Derived only: the identity, the scope with the heading's span in its
    # place, and the diff's hash.
    derived = {"diff", "proposal_identity", "resolved_scope", "semantic_diff_hash"}
    assert {k: v for k, v in old_b.items() if k not in derived} == {
        k: v for k, v in new_b.items() if k not in derived
    }, "the batch record changed beyond its derived fields"
    assert [s for s in new_b["resolved_scope"] if s != heading] == old_b[
        "resolved_scope"
    ]
    assert new_b["proposal_identity"] == proposal_identity(candidate)
    assert {**old_a, "proposal_identity": ""} == {**new_a, "proposal_identity": ""}
    assert new_a["proposal_identity"] == proposal_identity(candidate)
    print("  replaced: the animals batch record (+1 diff row) and its schema anchor")
    report = delta.report()
    body = ("\n".join(report) + "\n").encode("utf-8")
    if write:
        DELTA_FILE.write_bytes(body)
    assert DELTA_FILE.read_bytes() == body, "delta file drifted"
    print("delta", DELTA_FILE.name, len(report), "lines, sha256", _sha(body))

    # Consumer: the section's members and reading, the members' direct reads.
    keys = tuple(GEN.ANIMAL_KEY[n] for n in GEN.NAMES)
    old_members, old_readings, old_direct = RR.consumer(rec)
    members, readings, direct = RR.consumer(final)
    owned = RR.owned(final)
    union = owned[SECTION_KEY].union(*(owned[k] for k in keys))
    order = sorted(union, key=delta.position)
    read = readings[SECTION_KEY]
    own_in_read = [s for s in read if s in union]
    print(
        SECTION_KEY,
        "members before",
        len(old_members.get(SECTION_KEY, ())),
        "after",
        len(members[SECTION_KEY]),
        "in printed order",
        tuple(members[SECTION_KEY]) == keys,
        "| direct read",
        [delta.text(s) for s in direct[SECTION_KEY]],
        "| reading",
        len(read),
        "spans, owned text in printed order",
        own_in_read == order,
        "| each span once",
        len(read) == len(set(read)),
        "| governing context read",
        len(read) - len(own_in_read),
    )
    assert SECTION_KEY not in old_members and SECTION_KEY not in old_direct
    assert tuple(members[SECTION_KEY]) == keys
    assert direct[SECTION_KEY] == [heading] and read[0] == heading
    assert own_in_read == order and len(read) == len(set(read))
    assert all(direct[k] == old_direct[k] for k in keys), "a stat block read changed"
    print("  every stat block's direct read unchanged", len(keys))
    for k in (keys[0], RIDING_HORSE):
        at = read.index(sorted(owned[k], key=delta.position)[0])
        print("  ", k, "reached at reading position", at)

    # Overrides: a disabled member leaves the reading; a disabled part leaves
    # every stat block readable directly.
    o_members, o_readings, o_direct = RR.consumer(final, OVERRIDES[:1])
    left = owned[RIDING_HORSE] & set(o_readings[SECTION_KEY])
    print(
        "override disable",
        RIDING_HORSE,
        "| in direct reads",
        RIDING_HORSE in o_direct,
        "| its spans left in the part's reading",
        len(left),
        "| rest of the reading kept",
        [s for s in read if s not in owned[RIDING_HORSE]]
        == [s for s in o_readings[SECTION_KEY] if s not in owned[RIDING_HORSE]],
    )
    assert RIDING_HORSE not in o_direct and not left
    o_members, o_readings, o_direct = RR.consumer(final, OVERRIDES[1:])
    print(
        "override disable",
        SECTION_KEY,
        "| in direct reads",
        SECTION_KEY in o_direct,
        "| a catalogue",
        SECTION_KEY in o_readings,
        "| stat blocks still read directly",
        all(o_direct[k] == direct[k] for k in keys),
    )
    assert SECTION_KEY not in o_direct and SECTION_KEY not in o_readings
    assert all(o_direct[k] == direct[k] for k in keys)

    # Projection: the four citations now name the part's record.
    projected = candidate_from_accepted_inputs(final).representation
    targets = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): (
            r.target_record_key
        )
        for r in projected.references
    }
    for row in ROWS:
        print("  projected", row, "->", targets[row])
        assert targets[row] == SECTION_KEY
    assert ACCEPTED_PATH.read_bytes() == committed
    print("committed artifact unchanged", ACCEPTED_SHA256)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
