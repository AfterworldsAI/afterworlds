# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""The framing-coverage candidate: the release's last 28 uncovered leaves.

CRD Issue 5d framing coverage (#132, #137). REVIEW MATERIAL: nothing here is
accepted, recorded, published or activated, and no Owner approval exists for
it. There is deliberately no recording step.

The committed oracle (the Animals catalogue recording, ``96e90f71...``) leaves
28 represented leaves with no span and no review unit. This one additive batch,
``framing-coverage``, covers exactly them, in four groups:

* **Glossary Conventions** (8 leaves): how the glossary's rules are to be read
  -- bracketed tags, "you", *See also*, current terms only, and the whole
  abbreviation table. Its interpretation is kept, not excluded: a placed
  section ``glossary.glossary_conventions`` (``general_rule``; it is not a
  definition) whose five conventions are prose-bound components the rules
  authority reads directly, its introduction a framing (supporting) leaf and
  its heading excluded. The accepted rules-glossary-completion generator
  declined to author it ("states how the glossary is written, not a rule");
  this batch reverses that under the Owner's instruction for this packet.
* **Legal Information** (5 leaves): one unit, each leaf a specific licensing
  exclusion. Exclusion from mechanical canon does not waive the attribution
  obligations the text states for any publication.
* **Part openings** (13 leaves): the twelve part headings with no accepted
  record, each its own unit, and *Magic Items* with its flavour introduction.
  Coverage only: no heading is declared unable to name a catalogue later, and
  no membership or reference resolution is claimed. The held whole-part
  citations of *Character Creation*, *Classes*, *Equipment* and *Spells* stay
  unresolved.
* **Rules Definitions** (2 leaves): its heading and one-line introduction.

Only the Glossary Conventions leaves carry spans. The other 20 are covered by
review units alone (ADR-005d Decision 2 as amended 2026-09-16), so no
non-mechanical span is accepted over a title a later catalogue may need.
The native :class:`EntryBatch` builds the one entry with a record; the
unit-only units are appended to its proposal, since an entry there always
states a record and none of these 20 leaves has one to state.

The candidate is accepted once, in memory, under the simulated reviewer, over
the committed accepted inputs as loaded: the historical chain is not rebuilt.

Run: ``python issue-5d-framing-coverage-generator.py [--write]``. Without
``--write`` it checks the two review files below against a fresh
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

from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
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
    leaves_under,
    load_bound_corpus,
    published_release_binding,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ComponentHandling,
    ExcludedGroup,
    ReviewUnit,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    review_unit_violations,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import RecordKind  # noqa: E402
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


#: The remaining-references constructor, for its consumer reading; the
#: Equipment constructor under it, for the delta and the release texts; the
#: Monsters constructor under that, for counts and the preservation check.
#: Each is read, never edited.
RR = _load(
    "remaining_references_replacement",
    HERE / "issue-5d-remaining-references-REPLACEMENT.py",
)
EQ = RR.REPL
MC = EQ.REPLACEMENT

ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
)
#: The Animals catalogue recording.
ACCEPTED_SHA256 = "96e90f71ddde22da6424eef9875b51eb36620876dfee635546e1d6872594a91b"
SCRATCH_DB: Path = EQ.SCRATCH_DB
#: The one leaf of the original 29 the Animals recording covered.
ANIMALS_HEADING = "eb6c81a0"

ORIGIN = "issue-5d-framing-coverage-generator.py"
BATCH_ID = "framing-coverage"
PROPOSAL_FILE = HERE / "issue-5d-framing-coverage-PROPOSAL.json"
DELTA_FILE = HERE / "issue-5d-framing-coverage-DELTA.txt"

SIMULATED_REVIEWER: str = EQ.SIMULATED_REVIEWER
SIMULATED_RULE: str = EQ.SIMULATED_RULE
SIMULATED_AT: str = EQ.SIMULATED_AT

# ---------------------------------------------------------------------------
# Glossary Conventions: the one entry with a record
# ---------------------------------------------------------------------------
GC = "glossary_conventions"
GC_KEY = "glossary.glossary_conventions"
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND

TAGS = '**Tags in Brackets.** Some entries have a tag in brackets after the entry\'s name, as in "Attack [Action]." A tag—Action, Area of Effect, Attitude, Condition, or Hazard—indicates that a rule is part of a family of rules. The tags also have glossary entries.'
YOU = '**"You."** The game\'s rules—in this glossary and elsewhere—often talk about something happening to you in the game world. That "you" refers to the creature or object that the rule applies to in a particular moment of play. For example, the "you" in the Prone condition is a creature that currently has that condition.'
SEE_ALSO = '**"See Also."** Some glossary entries include a _See also_ section that points to other entries in the glossary, to other parts of this document, or both.'
NO_OBSOLETE = "**No Obsolete Terms.** The glossary contains definitions of current rules terms only. If you're looking for a term from an earlier version of the fifth edition rules, consult the index."
ABBREVIATIONS = "**Abbreviations.** The abbreviations listed below appear in this glossary and elsewhere in the rules."
#: The abbreviation table as the release prints it: 21 rows of four cells,
#: two abbreviation/meaning pairs a row. A meaning printed on two lines in the
#: source ("Material / component") continues on the next row's fourth cell.
ABBREVIATION_ROWS = (
    ("AC", "Armor Class", "M", "Material"),
    ("C", "Concentration", "", "component"),
    ("CE", "Chaotic Evil", "N", "Neutral"),
    ("CG", "Chaotic Good", "NE", "Neutral Evil"),
    ("Cha.", "Charisma", "NG", "Neutral Good"),
    ("CN", "Chaotic Neutral", "NPC", "Nonplayer"),
    ("Con.", "Constitution", "", "character"),
    ("CP", "Copper Piece(s)", "PB", "Proficiency Bonus"),
    ("CR", "Challenge Rating", "PP", "Platinum Piece(s)"),
    ("DC", "Difficulty Class", "R", "Ritual"),
    ("Dex.", "Dexterity", "S", "Somatic"),
    ("", "", "", "component"),
    ("EP", "Electrum Piece(s)", "SP", "Silver Piece(s)"),
    ("GM", "Game Master", "", ""),
    ("GP", "Gold Piece(s)", "Str.", "Strength"),
    ("HP", "Hit Point(s)", "V", "Verbal"),
    ("", "", "", "component"),
    ("Int.", "Intelligence", "Wis.", "Wisdom"),
    ("LE", "Lawful Evil", "XP", "Experience"),
    ("LG", "Lawful Good", "", "Point(s)"),
)
#: Its last row prints two cells, the second spanning two columns.
ABBREVIATION_LAST = '    <tr>\n      <td>LN</td>\n      <td>Lawful Neutral</td>\n      <td colspan="2"></td>\n    </tr>\n'
ABBREVIATION_TABLE = (
    "<table>\n  <tbody>\n"
    + "".join(
        "    <tr>\n" + "".join(f"      <td>{c}</td>\n" for c in row) + "    </tr>\n"
        for row in ABBREVIATION_ROWS
    )
    + ABBREVIATION_LAST
    + "  </tbody>\n</table>"
)

#: (component, texts), in printed order: each convention one rule.
CONVENTIONS = (
    ("tags_in_brackets", (TAGS,)),
    ("you", (YOU,)),
    ("see_also", (SEE_ALSO,)),
    ("no_obsolete_terms", (NO_OBSOLETE,)),
    ("abbreviations", (ABBREVIATIONS, ABBREVIATION_TABLE)),
)


def batch() -> EntryBatch:
    return EntryBatch(
        origin=ORIGIN,
        proposal_origin=f"{ORIGIN} (CRD Issue 5d framing-coverage batch; unaccepted)",
        unit_prefix=BATCH_ID,
        parent=("Rules Glossary",),
        entries=((GC, "Glossary Conventions", RecordKind.GENERAL_RULE),),
        expected_leaves=8,
        clauses=tuple((GC, key, (None,), texts) for key, texts in CONVENTIONS),
        framing=((GC, "The glossary uses the following conventions:"),),
        components=tuple(EntryComponent(GC, key, P, NO_USE) for key, _ in CONVENTIONS),
        supporting=(),
        record_references=(),
        placements={
            GC: Placement(
                GC_KEY,
                ("Rules Glossary", "Glossary Conventions"),
                "## Glossary Conventions",
                ReviewUnitKind.SECTION,
            )
        },
    )


# ---------------------------------------------------------------------------
# The unit-only units: (unit slug, container, ((exact leaf text, reason), ...))
# ---------------------------------------------------------------------------
LEGAL = (
    (
        "# Legal Information",
        "Heading of the SRD 5.2.1 legal notice: names the notice and states no game rule.",
    ),
    (
        "The System Reference Document 5.2.1 (“SRD 5.2.1”) is provided to you free of charge by Wizards of the Coast LLC (“Wizards”) under the terms of the Creative Commons Attribution 4.0 International License (“CC-BY-4.0”). You are free to use the content in this document in any manner permitted under CC-BY-4.0, provided that you include the following attribution statement in any of your work:",
        "Licence terms: the SRD 5.2.1 is offered under CC-BY-4.0 on condition that any work using it includes the attribution statement that follows; a licensing obligation, not a game mechanic, excluded from mechanical canon only and never from publication, which must honour it.",
    ),
    (
        "This work includes material from the System Reference Document 5.2.1 (“SRD 5.2.1”) by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode.",
        "The attribution statement CC-BY-4.0 requires any work using this material to include: legal text, not a game mechanic; excluded from mechanical canon only, and still required, verbatim, wherever this material is published.",
    ),
    (
        "Please do not include any other attribution to Wizards or its parent or affiliates other than that provided above. You may, however, include a statement on your work indicating that it is “compatible with fifth edition” or “5E compatible.”",
        "Attribution limits: no other attribution to Wizards or its parent or affiliates, and the permitted “compatible with fifth edition” or “5E compatible” statement; a publication obligation, not a game mechanic, which exclusion from mechanical canon does not waive.",
    ),
    (
        "Section 5 of CC-BY-4.0 includes a Disclaimer of Warranties and Limitation of Liability that limits our liability to you.",
        "Liability notice: CC-BY-4.0 Section 5's disclaimer of warranties and limitation of liability; legal text that states no game rule.",
    ),
)
COVERAGE_ONLY = (
    "Coverage only: this is not a verdict that the heading cannot name a "
    "catalogue or section record, and no membership or reference resolution "
    "is claimed."
)
HELD = " The whole-part citations that name this part stay unresolved."
#: (slug, label, the part's citations are held): the twelve part headings.
PARTS = (
    ("character_creation", "Character Creation", True),
    ("character_origins", "Character Origins", False),
    ("classes", "Classes", True),
    ("equipment", "Equipment", True),
    ("feats", "Feats", False),
    ("gameplay_toolbox", "Gameplay Toolbox", False),
    ("magic_items", "Magic Items", False),
    ("monsters", "Monsters", False),
    ("monsters_a_z", "Monsters A–Z", False),
    ("playing_the_game", "Playing the Game", False),
    ("rules_glossary", "Rules Glossary", False),
    ("spells", "Spells", True),
)
MAGIC_ITEMS_INTRO = "Magic items are gleaned from the hoards of felled monsters or discovered in long-lost vaults. Such items grant capabilities a character could rarely have otherwise, or they complement their owner's capabilities in wondrous ways."


def part_heading_reason(label: str, held: bool) -> str:
    return (
        f"Part heading: names the {label} part and states no rule; the accepted "
        f"batches below it review its content. {COVERAGE_ONLY}" + (HELD if held else "")
    )


UNIT_ONLY: tuple[tuple[str, tuple[str, ...], tuple[tuple[str, str], ...]], ...] = (
    ("legal_information", ("Legal Information",), LEGAL),
    *(
        (
            slug,
            (label,),
            (
                (f"# {label}", part_heading_reason(label, held)),
                *(
                    (
                        (
                            MAGIC_ITEMS_INTRO,
                            "Introductory flavour: where magic items are found and that they grant uncommon capabilities; it neither states nor contextualizes the rule of any item.",
                        ),
                    )
                    if slug == "magic_items"
                    else ()
                ),
            ),
        )
        for slug, label, held in PARTS
    ),
    (
        "rules_definitions",
        ("Rules Glossary", "Rules Definitions"),
        (
            (
                "## Rules Definitions",
                "Section heading: names the Rules Definitions section, whose entries the accepted glossary batches author, and states no rule. "
                + COVERAGE_ONLY,
            ),
            (
                "Here are definitions of various rules.",
                "One-line introduction: announces the definitions that follow and states, qualifies or contextualizes no rule of any of them.",
            ),
        ),
    ),
)


def unit_only(session: Any, binding: Any) -> tuple[ReviewUnit, ...]:
    """Each unit-only unit, its leaves found by exact text in its container:
    one per excluded group, each leaf its own specific decision."""
    pkg, rel = binding.package_uuid, binding.release_version
    content = dict(
        session.execute(
            text(
                "select leaf_id, content from rp_ledger_leaves where package_uuid = :p"
            ),
            {"p": pkg},
        ).all()
    )
    units = []
    for slug, container, decisions in UNIT_ONLY:
        under = leaves_under(session, pkg, rel, container)
        groups = []
        for printed, reason in decisions:
            (leaf,) = [lid for lid in under if content[lid] == printed]
            groups.append(ExcludedGroup((leaf,), reason))
        units.append(
            ReviewUnit(
                unit_id=f"{BATCH_ID}/{slug}",
                kind=ReviewUnitKind.SECTION,
                leaf_ids=tuple(g.leaf_ids[0] for g in groups),
                excluded_groups=tuple(groups),
            )
        )
    return tuple(units)


def build() -> Built:
    """The batch on a copy of the release store, the unit-only units appended."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                built = build_entry_batch(session, batch(), binding)
                found = batch_findings(built)
                extra = unit_only(session, binding)
        finally:
            engine.dispose()
    assert not any(found.values()), found
    p = built.proposal
    proposal = dataclasses.replace(
        p, proposed_review_units=(*p.proposed_review_units, *extra)
    )
    assert not review_unit_violations(
        proposal.proposed_review_units,
        proposal.proposed_representation,
        proposal.policy_version,
        tuple(s.span for s in proposal.proposed_spans),
    )
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
                return list(validate_candidate(candidate, corpus))
        finally:
            engine.dispose()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: Batches, records, spans, review units, resolutions; then reference and
#: uncovered-leaf findings on the release.
EXPECTED = {
    "accepted": ((22, 1833, 10485, 1460, 1438), (64, 28)),
    "candidate": ((23, 1834, 10491, 1475, 1438), (64, 0)),
}


def unit_report(delta: Any, units: tuple[ReviewUnit, ...]) -> list[str]:
    """Each new unit, in printed order: every leaf's position and full text,
    and the decision that accounts for it."""
    lines = ["## framing-coverage units, printed order, full leaf text"]
    decided: dict[tuple[str, str], list[str]] = {}
    for u in units:
        for g in u.excluded_groups:
            for leaf in g.leaf_ids:
                decided.setdefault((u.unit_id, leaf), []).append(
                    f"excluded: {g.reason}"
                )
        for s in u.supporting_groups:
            for leaf in s.leaf_ids:
                decided.setdefault((u.unit_id, leaf), []).append(
                    f"supporting: {s.supports_record_key}"
                )
        for r in u.expected_rules:
            for sid in r.source_span_ids:
                leaf = delta.spans[sid]["leaf_id"]
                decided.setdefault((u.unit_id, leaf), []).append(
                    f"expected rule: {r.record_key}/{r.component_key} (span {sid[:8]})"
                )
    for u in sorted(units, key=lambda u: min(delta.leaves[x][0] for x in u.leaf_ids)):
        lines.append(f"+ unit {u.unit_id} ({u.kind.value}), {len(u.leaf_ids)} leaves")
        for leaf in sorted(u.leaf_ids, key=lambda x: delta.leaves[x][0]):
            index, text = delta.leaves[leaf]
            lines.append(f"    leaf {leaf} @{index}")
            lines.extend(f"      {d}" for d in decided[(u.unit_id, leaf)])
            lines.extend(f"      | {line}" for line in text.split("\n"))
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
    built = build()
    assert built.proposal.binding == rec.oracle.binding
    rendered = render(built.proposal).encode("utf-8")
    if write:
        PROPOSAL_FILE.write_bytes(rendered)
    assert PROPOSAL_FILE.read_bytes() == rendered, "proposal file drifted"
    candidate = load_proposal(PROPOSAL_FILE)
    assert render(candidate).encode("utf-8") == rendered
    units = candidate.proposed_review_units
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
        len(units),
        "(unit-only",
        sum(not u.expected_rules for u in units),
        ")",
    )

    # One acceptance over the committed inputs, as loaded.
    final = accepted(rec, candidate)
    found = {"accepted": findings(rec), "candidate": findings(final)}
    for state, inputs in (("accepted", rec), ("candidate", final)):
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

    # Findings: exactly the 28 uncovered leaves clear; every reference finding
    # is kept, string for string.
    gone = Counter(found["accepted"]) - Counter(found["candidate"])
    assert not Counter(found["candidate"]) - Counter(found["accepted"]), "new finding"
    uncovered = {f.split()[1].rstrip(":") for f in gone}
    covered = {leaf for u in units for leaf in u.leaf_ids}
    assert all(f.endswith(": no semantic spans") for f in gone)
    assert uncovered == covered and len(covered) == 28, uncovered ^ covered
    # ... and they are the named input: the original 29 minus the recorded
    # Animals heading.
    named = (REPO / ".claude/_sp/rr/leaves.txt").read_text(encoding="utf-8")
    listed = {
        ln.split()[1].rstrip(":") for ln in named.splitlines() if ln.startswith("leaf ")
    }
    (animals,) = listed - covered
    assert len(listed) == 29 and animals.startswith(ANIMALS_HEADING), listed ^ covered
    print("findings cleared", sum(gone.values()), "= the batch's 28 leaves exactly")
    print("= leaves.txt's 29 minus the recorded Animals heading", animals)
    print("reference findings unchanged, string for string", len(found["candidate"]))

    # Preservation: nothing the committed inputs hold is lost or changed.
    delta = EQ.Delta(rec, final)
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
    # Titles stay unlocked: only the eight Glossary Conventions leaves are
    # read; no span lies on the 20 unit-only leaves.
    spanned = {s.span.leaf_id for s in candidate.proposed_spans}
    unit_only_leaves = {
        leaf for u in units if not u.expected_rules for leaf in u.leaf_ids
    }
    assert len(unit_only_leaves) == 20 and not spanned & unit_only_leaves
    assert not {s["leaf_id"] for s in delta.old["spans"]} & covered
    print("spans on the 20 unit-only leaves: none; prior spans on the 28: none")

    report = [*delta.report(), *unit_report(delta, units)]
    body = ("\n".join(report) + "\n").encode("utf-8")
    if write:
        DELTA_FILE.write_bytes(body)
    assert DELTA_FILE.read_bytes() == body, "delta file drifted"
    print("delta", DELTA_FILE.name, len(report), "lines, sha256", _sha(body))

    # Consumer: the new record's direct read, every other read unchanged.
    old_members, old_readings, old_direct = RR.consumer(rec)
    members, readings, direct = RR.consumer(final)
    assert GC_KEY not in old_direct
    read = [delta.text(s) for s in direct[GC_KEY]]
    printed = [t for _, texts in CONVENTIONS for t in texts]
    print(
        GC_KEY,
        "direct read",
        len(read),
        "spans, the five conventions in printed order",
        read == printed,
    )
    assert read == printed
    assert members == old_members and readings == old_readings
    assert {k: v for k, v in direct.items() if k != GC_KEY} == old_direct
    print("every other direct read, reading and membership unchanged", len(old_direct))
    disable = RR._disable(MechanicalTargetKind.RECORD, GC_KEY, None)
    _, o_readings, o_direct = RR.consumer(final, (disable,))
    print(
        "override disable",
        GC_KEY,
        "| in direct reads",
        GC_KEY in o_direct,
        "| rest unchanged",
        o_direct == old_direct and o_readings == old_readings,
    )
    assert GC_KEY not in o_direct and o_direct == old_direct
    assert o_readings == old_readings
    assert ACCEPTED_PATH.read_bytes() == committed
    print("committed artifact unchanged", ACCEPTED_SHA256)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
