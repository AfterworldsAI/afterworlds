"""The Character Creation catalogue candidate and two resolution drafts.

CRD Issue 5d remaining-references inventory #3 and #5 (#132, #137). REVIEW
MATERIAL: nothing here is accepted, recorded, published or activated, and no
Owner approval exists for it. There is deliberately no recording step.

``glossary.character_sheet`` and ``glossary.player_character`` each end
*See also* "Character Creation" -- the part as such, unqualified. No record is
titled by that part, so both references are held. This one additive batch,
``character-creation-catalogue``, adds it:

* a placed section ``character_creation.character_creation``
  (``general_rule``) on the part heading ``# Character Creation`` (@841), its
  one component heading-only and prose-bound, reason
  ``no_identified_structured_use``, as the recorded Animals part catalogue
  places ``animals.animals``. The six accepted sections under the part are
  omitted from its placement: each keeps its own.
* six ``catalogue_member`` edges, one per accepted section, in printed order:
  ``character_sheet`` @843, ``create_your_character`` @846,
  ``level_advancement`` @942, ``starting_at_higher_levels`` @964,
  ``multiclassing`` @973, ``trinkets`` @1006. Each edge's contextual
  provenance cites its member's first accepted primary span, found by the
  release's own leaf order, which is what orders members for the consumer.

The heading leaf keeps the accepted ``framing-coverage/character_creation``
unit, which excludes it as a part opening and declares nothing about a later
catalogue; this batch adds its own unit and one span over it. The native
:class:`EntryBatch` cannot state the edges, since its edges must cite this
batch's own entry and the members are accepted elsewhere; they are appended
to its proposal, as ``framing-coverage`` appended its units. Acceptance and
validation of the merged candidate are native.

#4 (``glossary.hit_point_dice``, the same scope, M-dynamic) stays held.

The candidate is accepted once, in memory, under the simulated reviewer, over
the committed accepted inputs as loaded: the historical chain is not rebuilt.
The two drafts are then applied in memory over that.

Run: ``python issue-5d-character-creation-catalogue-generator.py [--write]``.
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

from sqlalchemy import text  # noqa: E402

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
    render,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    published_release_binding,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ComponentHandling,
    ReferenceResolution,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    load_accepted_inputs,
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
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    RelationshipDraft,
    RelationshipKind,
    reference_target_key,
    relationship_target_key,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    relationship_and_reference_violations,
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


#: The framing-coverage constructor, for its findings; under it the
#: remaining-references constructor (consumer), Equipment (delta, texts) and
#: Monsters (counts, preservation). Each is read, never edited.
FC = _load(
    "framing_coverage_generator", HERE / "issue-5d-framing-coverage-generator.py"
)
RR = FC.RR
EQ = FC.EQ
MC = FC.MC

ACCEPTED_PATH: Path = FC.ACCEPTED_PATH
#: The framing-coverage recording.
ACCEPTED_SHA256 = "15478aa5ea712b9946999ff865283cd12b36dd4f917137a76c225543066b8922"
SCRATCH_DB: Path = FC.SCRATCH_DB

BATCH_ID = "character-creation-catalogue"
ORIGIN = "issue-5d-character-creation-catalogue-generator.py"
PROPOSAL_FILE = HERE / "issue-5d-character-creation-catalogue-PROPOSAL.json"
DRAFTS_FILE = HERE / "issue-5d-character-creation-catalogue-resolutions-DRAFTS.json"
DELTA_FILE = HERE / "issue-5d-character-creation-catalogue-DELTA.txt"

SIMULATED_REVIEWER: str = FC.SIMULATED_REVIEWER
SIMULATED_RULE: str = FC.SIMULATED_RULE
SIMULATED_AT: str = FC.SIMULATED_AT

PART = "Character Creation"
SECTION = "character_creation"
SECTION_KEY = "character_creation.character_creation"
HEADING = "# Character Creation"
#: The accepted sections under the part, in printed order: (slug, printed
#: heading label, occurrence index of the member's first primary span).
MEMBERS: tuple[tuple[str, str, int], ...] = (
    ("character_sheet", "Choose a Character Sheet", 843),
    ("create_your_character", "Create Your Character", 846),
    ("level_advancement", "Level Advancement", 942),
    ("starting_at_higher_levels", "Starting at Higher Levels", 964),
    ("multiclassing", "Multiclassing", 973),
    ("trinkets", "Trinkets", 1006),
)
MEMBER_KEYS = tuple(f"{SECTION}.{slug}" for slug, _, _ in MEMBERS)
#: The accepted framing-coverage unit over the heading, kept as it is.
FRAMING_UNIT = "framing-coverage/character_creation"
#: The held rows, in review order: (citing record, component, printed pointer,
#: scope); record-owned, so the component is empty.
ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("glossary.character_sheet", "", PART, "srd-5.2.1/character-creation"),
    ("glossary.player_character", "", PART, "srd-5.2.1/character-creation"),
)
#: Every new draft id carries this suffix, and none of the recorded 1,438.
SUFFIX = "-character-creation-catalogue-1"

#: Batches, records, spans, review units, resolutions; then reference and
#: uncovered-leaf findings on the release.
EXPECTED = {
    "accepted": ((23, 1834, 10491, 1475, 1438), (64, 0)),
    "candidate": ((24, 1835, 10492, 1476, 1438), (64, 0)),
    "drafted": ((24, 1835, 10492, 1476, 1440), (62, 0)),
}


def batch() -> EntryBatch:
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=ORIGIN,
        unit_prefix=BATCH_ID,
        parent=(PART,),
        entries=((SECTION, PART, RecordKind.GENERAL_RULE),),
        expected_leaves=1,
        clauses=((SECTION, SECTION, (None,), (HEADING,)),),
        framing=(),
        components=(
            EntryComponent(
                SECTION,
                SECTION,
                ComponentHandling.PROSE_BOUND,
                "no_identified_structured_use",
            ),
        ),
        supporting=(),
        record_references=(),
        placements={
            SECTION: Placement(
                SECTION_KEY,
                (PART,),
                HEADING,
                ReviewUnitKind.SECTION,
                tuple((PART, label) for _, label, _ in MEMBERS),
            )
        },
    )


def first_spans(session: Any, prior: AcceptedInputs) -> dict[str, str]:
    """member -> its first accepted primary span, by (leaf order, offset)."""
    o = prior.oracle
    order = dict(
        session.execute(
            text(
                "select leaf_id, occurrence_index from rp_ledger_leaves"
                " where package_uuid = :p"
            ),
            {"p": o.binding.package_uuid},
        ).all()
    )
    spans = {s.span_id: s for s in o.spans}
    first: dict[str, tuple[tuple[int, int], str]] = {}
    for c in o.representation.provenance:
        if (
            c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and c.role is ProvenanceRole.PRIMARY
            and c.target_key[0] in MEMBER_KEYS
        ):
            s = spans[c.span_id]
            at = (order[s.leaf_id], s.char_start)
            if c.target_key[0] not in first or at < first[c.target_key[0]][0]:
                first[c.target_key[0]] = (at, c.span_id)
    assert [first[k][0][0] for k in MEMBER_KEYS] == [i for _, _, i in MEMBERS], first
    return {k: sid for k, (_, sid) in first.items()}


def build(prior: AcceptedInputs) -> Built:
    """The batch on a copy of the release store, the member edges appended."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                built = build_entry_batch(
                    session, batch(), published_release_binding(session)
                )
                found = batch_findings(built)
                first = first_spans(session, prior)
        finally:
            engine.dispose()
    assert not any(found.values()), found
    p = built.proposal
    edges = tuple(
        RelationshipDraft(key, SECTION_KEY, RelationshipKind.CATALOGUE_MEMBER)
        for key in MEMBER_KEYS
    )
    claims = tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.RELATIONSHIP,
            relationship_target_key(e),
            first[e.source_record_key],
            ProvenanceRole.CONTEXTUAL,
        )
        for e in edges
    )
    rep = p.proposed_representation
    rep = dataclasses.replace(
        rep,
        relationships=(*rep.relationships, *edges),
        provenance=(*rep.provenance, *claims),
    )
    # Alone, the proposal knows no member: exactly that, and nothing else.
    # The merged candidate is validated natively in main().
    assert relationship_and_reference_violations(rep) == [
        f"relationship {e.source_record_key}->{SECTION_KEY}: unknown record"
        f" {e.source_record_key}"
        for e in edges
    ]
    proposal = dataclasses.replace(p, proposed_representation=rep)
    return dataclasses.replace(built, proposal=proposal)


def accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    """The candidate accepted once over *prior*, under the simulated reviewer."""
    return accept_proposal(
        proposal,
        batch_id=BATCH_ID,
        rule=SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=SIMULATED_REVIEWER,
        accepted_at=SIMULATED_AT,
        prior=prior,
    )


def draft_resolutions(
    inputs: AcceptedInputs, texts: dict[str, str]
) -> tuple[ReferenceResolution, ...]:
    """Each held row to the part's section, cited from the one span the oracle
    cites its reference from, which must print the pointer."""
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
        record, component, printed, scope = row
        assert row in unresolved and row not in resolved, row
        spans = tuple(cited[reference_target_key(unresolved[row])])
        assert len(spans) == 1 and "See also" in texts[spans[0]], row
        assert printed in texts[spans[0]], row
        out.append(
            ReferenceResolution(
                resolution_id=(
                    f"resolve-{_slug(record)}-record-{_slug(printed)}{SUFFIX}"
                ),
                from_record_key=record,
                from_component_key=component,
                source_text=printed,
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


def _slug(value: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in value.lower()).split())


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


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def membership_report(delta: Any, first: dict[str, str]) -> list[str]:
    lines = [f"## {SECTION_KEY} members, printed order, first span full text"]
    for key in MEMBER_KEYS:
        sid = first[key]
        leaf = delta.spans[sid]["leaf_id"]
        lines.append(f"+ member {key} @{delta.leaves[leaf][0]} span {sid}")
        lines.extend(f"    | {line}" for line in delta.text(sid).split("\n"))
    return lines


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)

    # The candidate proposal.
    built = build(rec)
    assert built.proposal.binding == rec.oracle.binding
    rendered = render(built.proposal).encode("utf-8")
    if write:
        PROPOSAL_FILE.write_bytes(rendered)
    assert PROPOSAL_FILE.read_bytes() == rendered, "proposal file drifted"
    candidate = load_proposal(PROPOSAL_FILE)
    assert render(candidate).encode("utf-8") == rendered
    print(
        "candidate proposal",
        PROPOSAL_FILE.name,
        "sha256",
        _sha(rendered),
        "identity",
        proposal_identity(candidate),
        "| spans",
        len(candidate.proposed_spans),
        "units",
        [u.unit_id for u in candidate.proposed_review_units],
        "| edges",
        len(candidate.proposed_representation.relationships),
    )

    # One acceptance over the committed inputs, as loaded; then the drafts.
    final = accepted(rec, candidate)
    texts = EQ.Delta(rec, final)
    drafts = draft_resolutions(final, {s: texts.text(s) for s in texts.spans})
    raw = (json.dumps(reference_resolution_payload(drafts), indent=2) + "\n").encode(
        "utf-8"
    )
    if write:
        DRAFTS_FILE.write_bytes(raw)
    assert DRAFTS_FILE.read_bytes() == raw, "drafts file drifted"
    print("drafts", DRAFTS_FILE.name, "sha256", _sha(raw))
    for d in drafts:
        print(
            "  draft", d.resolution_id, "->", d.target_record_key, d.provenance_span_ids
        )
    resolved = drafted(final, drafts)

    states = {"accepted": rec, "candidate": final, "drafted": resolved}
    found = {state: FC.findings(inputs) for state, inputs in states.items()}
    for state, inputs in states.items():
        o = inputs.oracle
        violations = reference_resolution_violations(
            o.representation, o.reference_resolutions, o.binding
        )
        refs = [f for f in found[state] if f.startswith("reference ")]
        leaves = [f for f in found[state] if f.startswith("leaf ")]
        assert len(refs) + len(leaves) == len(found[state]), found[state][:5]
        counts = MC._counts(inputs)
        print(
            state,
            "counts",
            counts,
            "violations",
            len(violations),
            "reference, uncovered-leaf findings",
            (len(refs), len(leaves)),
        )
        assert not violations, violations[:5]
        assert (counts, (len(refs), len(leaves))) == EXPECTED[state]
    assert found["candidate"] == found["accepted"], "the batch alone moves a finding"
    gone = Counter(found["accepted"]) - Counter(found["drafted"])
    assert not Counter(found["drafted"]) - Counter(found["accepted"]), "new finding"
    print("findings cleared by the drafts", sorted(gone.elements()))
    assert sum(gone.values()) == 2 and all(PART in f for f in gone)

    # Preservation: nothing the committed inputs hold is lost or changed.
    delta = EQ.Delta(rec, resolved)
    lost = MC._preserved(delta.old, delta.new)
    print("committed content lost or changed", lost)
    assert not lost
    summary = {
        ".".join(p): (len(a), len(b))
        for p, (a, b) in delta.collections().items()
        if a or b
    }
    print("delta by collection (-, +)", json.dumps(summary))
    assert not any(a for a, _ in delta.collections().values())
    heading_leaf = candidate.proposed_spans[0].span.leaf_id
    (framing,) = [u for u in rec.oracle.review_units if u.unit_id == FRAMING_UNIT]
    assert framing.leaf_ids == (heading_leaf,)
    assert framing in resolved.oracle.review_units
    assert not {s["leaf_id"] for s in delta.old["spans"]} & {heading_leaf}
    print("heading leaf", heading_leaf, "| accepted", FRAMING_UNIT, "kept as is")

    first = {
        e.target_key[0]: e.span_id
        for e in candidate.proposed_representation.provenance
        if e.target_kind is ProvenanceTargetKind.RELATIONSHIP
    }
    report = [*delta.report(), *membership_report(delta, first)]
    body = ("\n".join(report) + "\n").encode("utf-8")
    if write:
        DELTA_FILE.write_bytes(body)
    assert DELTA_FILE.read_bytes() == body, "delta file drifted"
    print("delta", DELTA_FILE.name, len(report), "lines, sha256", _sha(body))

    # Consumer: membership in printed order, the direct read, dedup, and every
    # other member, reading and direct read unchanged.
    old_members, old_readings, old_direct = RR.consumer(rec)
    members, readings, direct = RR.consumer(resolved)
    assert SECTION_KEY not in old_members and SECTION_KEY not in old_direct
    print("members before", old_members.get(SECTION_KEY))
    print("members after", members[SECTION_KEY])
    assert members[SECTION_KEY] == MEMBER_KEYS
    read = [delta.text(s) for s in direct[SECTION_KEY]]
    print(SECTION_KEY, "direct read", read)
    assert read == [HEADING]
    reading = readings[SECTION_KEY]
    # Each passage at its own printed position: the section's and every
    # member's direct read, merged into source order.
    expected = sorted(
        {s for k in (SECTION_KEY, *MEMBER_KEYS) for s in direct[k]},
        key=delta.position,
    )
    print(
        SECTION_KEY,
        "reading",
        len(reading),
        "spans, each once",
        len(reading) == len(set(reading)),
        "| = own and members' direct reads, in printed order",
        reading == expected,
    )
    assert len(reading) == len(set(reading))
    assert reading == expected
    assert {k: v for k, v in members.items() if k != SECTION_KEY} == old_members
    assert {k: v for k, v in readings.items() if k != SECTION_KEY} == old_readings
    assert {k: v for k, v in direct.items() if k != SECTION_KEY} == old_direct
    print(
        "every other membership, reading and direct read unchanged",
        (len(old_members), len(old_readings), len(old_direct)),
    )

    # Overrides: one member disabled, then the section disabled.
    member = MEMBER_KEYS[4]
    disable = RR._disable(MechanicalTargetKind.RECORD, member, None)
    m_members, m_readings, m_direct = RR.consumer(resolved, (disable,))
    print(
        "override disable",
        member,
        "| members",
        m_members[SECTION_KEY],
        "| its spans in the reading",
        bool(set(direct[member]) & set(m_readings[SECTION_KEY])),
    )
    assert m_members[SECTION_KEY] == tuple(k for k in MEMBER_KEYS if k != member)
    assert m_readings[SECTION_KEY] == [
        s for s in reading if s not in set(direct[member])
    ]
    disable = RR._disable(MechanicalTargetKind.RECORD, SECTION_KEY, None)
    s_members, s_readings, s_direct = RR.consumer(resolved, (disable,))
    print(
        "override disable",
        SECTION_KEY,
        "| in members, readings, direct reads",
        (SECTION_KEY in s_members, SECTION_KEY in s_readings, SECTION_KEY in s_direct),
        "| rest as accepted",
        (s_members, s_readings, s_direct) == (old_members, old_readings, old_direct),
    )
    assert (s_members, s_readings, s_direct) == (old_members, old_readings, old_direct)
    assert ACCEPTED_PATH.read_bytes() == committed
    print("committed artifact unchanged", ACCEPTED_SHA256)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
