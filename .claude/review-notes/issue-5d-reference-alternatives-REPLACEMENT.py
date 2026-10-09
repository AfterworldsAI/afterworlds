"""The reference-routes candidate, composed in memory.

CRD Issue 5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. There
is deliberately no recording step.

Inventory rows #4, #7-12, #17-20, #22 and #40 (``issue-5d-remaining-
references-review.md``) are thirteen accepted unresolved citations whose
destination differs by class, class level or the reader's situation, or which
name a group. Under the Owner Decisions of 2026-10-01 (ADR-005d Decision 7,
proposed amendment) each is resolved to labelled routes -- one reviewed
decision per citation. A route's destinations are read together, landing
first and supporting text after; routes are not exclusive. Every destination
is a record the accepted authority already states, at component grain where
the source points into one. Row #40 is one route over the four Origin feats
``feats.md`` lists under its heading, checked against the source by
``_origin_feats``; their catalogue ownership is unchanged.

The chain is the accepted artifact itself: nothing is re-accepted or rebuilt.
``resolve_references(..., lift_to=...)`` lifts it 16 -> 17 (the registered
``5d-lift-schema-16-to-17``, because a schema-16 artifact cannot state a
route) and resolves it in one action under the simulated reviewer.

Run: ``python issue-5d-reference-alternatives-REPLACEMENT.py [--write]``.
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceDestination,
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    AlternativeSelection,
    effective_representation,
    reference_resolution_payload,
    select_alternatives,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceTargetKind,
    ReferenceSituation,
    RelationshipKind,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    lift_accepted_inputs,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: The recorded findings reader and scratch release (read-only copies).
ECE = _load(
    "equipment_class_eligibility_accept",
    HERE / "issue-5d-equipment-class-eligibility-ACCEPT.py",
)
APC = ECE.APC
SCRATCH_DB: Path = ECE.REPL.SCRATCH_DB
SIMULATED_REVIEWER: str = ECE.SIMULATED_REVIEWER
SIMULATED_RULE: str = ECE.SIMULATED_RULE
SIMULATED_AT = "2026-10-01T00:00:00Z"

ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
)
ACCEPTED_SHA256 = "5f37fb080a8493a1acb6584ef9bd2297c388d34683200bd7f486007ade668676"

TAG = "reference-alternatives"
PROPOSAL_FILE = HERE / f"issue-5d-{TAG}-PROPOSAL.json"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"

CLASSES = (
    "barbarian",
    "bard",
    "cleric",
    "druid",
    "fighter",
    "monk",
    "paladin",
    "ranger",
    "rogue",
    "sorcerer",
    "warlock",
    "wizard",
)
CC = "character_creation.create_your_character"
LA = "character_creation.level_advancement"
MC = "character_creation.multiclassing"

INITIAL = ReferenceSituation.INITIAL_CHARACTER.value
LATER = ReferenceSituation.LATER_LEVEL.value
ENTERING = ReferenceSituation.ENTERING_CLASS.value
ADVANCING = ReferenceSituation.ADVANCING_CLASS.value
SINGLE = ReferenceSituation.SINGLE_CLASS.value
MULTI = ReferenceSituation.MULTICLASS.value


def _d(
    record: str,
    component: str,
    label: str,
    situation: str = "",
    cls: str = "",
    level: int = 0,
) -> ReferenceDestination:
    return ReferenceDestination(
        target_record_key=record,
        target_component_key=component,
        alternative_label=label,
        situation=situation,
        class_record_key=f"classes.{cls}" if cls else "",
        minimum_class_level=level,
    )


def _title(cls: str) -> str:
    return cls.capitalize()


#: Fighting Style: the granting feature's description, by class and the class
#: level it is gained at (classes.md 4713, 5576, 6360). The Champion's
#: Additional Fighting Style (4801) is a different feature and is excluded.
FIGHTING_STYLE = tuple(
    _d(
        f"classes.{c}.fighting_style",
        "fighting_style",
        f"{_title(c)} level {n}: Fighting Style",
        cls=c,
        level=n,
    )
    for c, n in (("fighter", 1), ("paladin", 2), ("ranger", 2))
)
#: Spellcasting, level 1 in every class that has the feature (classes.md 824,
#: 2146, 3416, 5552, 6321, 7530, 10144). Warlock Pact Magic (8909) is not
#: Spellcasting and is excluded; class membership alone grants nothing.
SPELLCASTING = tuple(
    _d(
        f"classes.{c}.spellcasting",
        "spellcasting",
        f"{_title(c)} level 1: Spellcasting",
        cls=c,
        level=1,
    )
    for c in ("bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "wizard")
)


def _per_class(
    *rows: tuple[str, str, str, str],
) -> tuple[ReferenceDestination, ...]:
    """Each row (record suffix, component, label, situation) per class.

    Rows sharing a label are one route, read in row order: the first is where
    the reader lands, the rest is what that route needs read with it.
    """
    return tuple(
        _d(f"classes.{c}{suffix}", component, f"{_title(c)}: {label}", sit, c)
        for c in CLASSES
        for suffix, component, label, sit in rows
    )


#: Entering a class lands on its "As a Multiclass Character" instructions:
#: only the listed Core Traits, plus the level 1 features (classes.md 4547).
ENTERING_LABEL = "entering as a multiclass character"
ENTER_FIRST = (
    ".as_a_multiclass_character",
    "as_a_multiclass_character",
    ENTERING_LABEL,
    ENTERING,
)

#: feats.md 19-58: the "Origin Feats" group, in source order.
ORIGIN_FEATS = ("alert", "magic_initiate", "savage_attacker", "skilled")
ORIGIN_FEATS_LABEL = "Origin Feats (examples; not every Origin feat)"
FEATS_MD = REPO / "docs/sources/community/dnd-5e-srd-markdown/feats.md"


#: citation (from_record_key, from_component_key, source_text, scope_key)
#: -> (inventory row, destinations in reviewed order).
DRAFTS: dict[
    tuple[str, str, str, str], tuple[str, tuple[ReferenceDestination, ...]]
] = {
    **{
        (f"feats.{feat}", "category", "Fighting Style Feature", "srd-5.2.1/classes"): (
            row,
            FIGHTING_STYLE,
        )
        for row, feat in (
            ("#17", "archery"),
            ("#18", "defense"),
            ("#19", "great_weapon_fighting"),
            ("#20", "two_weapon_fighting"),
        )
    },
    (
        "feats.boon_of_spell_recall",
        "category",
        "Spellcasting Feature",
        "srd-5.2.1/classes",
    ): ("#22", SPELLCASTING),
    (
        "glossary.hit_point_dice",
        "hit_point_dice",
        "Character Creation",
        "srd-5.2.1/character-creation",
    ): (
        "#4",
        (
            _d(
                CC,
                "hit_points",
                "Initial character (total level 1): maximum die + Constitution",
                INITIAL,
            ),
            # One route, two texts: the roll-or-fixed rule with its minimum,
            # and the multiclass rule that a new class's first level is a
            # later level unless total character level is 1 (899).
            *(
                _d(
                    record,
                    component,
                    "Later levels, including a first level in an added class: "
                    "roll or fixed value + Constitution, minimum 1",
                    LATER,
                )
                for record, component in (
                    (LA, "hit_points_and_hit_point_dice"),
                    (MC, "hit_points"),
                )
            ),
        ),
    ),
    # #7 (Owner-decided): the Class Overview table this component owns is the
    # landing for every reader, and each class's own description is its route.
    (CC, "choose_class", "Classes", "srd-5.2.1/classes"): (
        "#7",
        (
            _d(CC, "choose_class", "Class Overview table (summary of every class)"),
            *(_d(f"classes.{c}", "", f"{_title(c)} (details)", cls=c) for c in CLASSES),
        ),
    ),
    # A whole-class destination reaches the class table and, one
    # CATALOGUE_MEMBER hop away, every Level N feature description (576, 806).
    (CC, "class_features", "Classes", "srd-5.2.1/classes"): (
        "#8",
        _per_class(
            ("", "", "level 1 character: features table and descriptions", INITIAL),
            ENTER_FIRST,
            ("", "", ENTERING_LABEL, ENTERING),
        ),
    ),
    (CC, "class_proficiencies", "Classes", "srd-5.2.1/classes"): (
        "#9",
        _per_class(
            (
                "",
                "as_a_level_1_character",
                "level 1 character: all Core Traits",
                INITIAL,
            ),
            ("", "core_traits", "level 1 character: all Core Traits", INITIAL),
            ENTER_FIRST,
            ("", "core_traits", ENTERING_LABEL, ENTERING),
        ),
    ),
    (LA, "class_features", "Classes", "srd-5.2.1/classes"): (
        "#10",
        _per_class(
            ("", "", "advancing: features table and descriptions", ADVANCING),
            ENTER_FIRST,
            ("", "", ENTERING_LABEL, ENTERING),
        ),
    ),
    (LA, "proficiency_bonus", "Classes", "srd-5.2.1/classes"): (
        "#11",
        (
            *_per_class(("", "progression", "single class: class table", SINGLE)),
            # One route: the table, read by total character level (905).
            *(
                _d(
                    record,
                    component,
                    "Multiclass: Character Advancement by total character level",
                    MULTI,
                )
                for record, component in (
                    (LA, "character_advancement"),
                    (MC, "proficiency_bonus"),
                )
            ),
        ),
    ),
    (MC, "proficiencies", "Classes", "srd-5.2.1/classes"): (
        "#12",
        _per_class(ENTER_FIRST, ("", "core_traits", ENTERING_LABEL, ENTERING)),
    ),
    # #40: one route read as a unit -- the "Origin Feats" group in source
    # order. The four are examples, not every Origin feat and not four choices;
    # the heading is navigation and owns nothing. Checked by _origin_feats.
    (
        "gameplay_toolbox.creating_a_background",
        "step_2_choose_a_feat",
        "Origin Feats",
        "srd-5.2.1/feats",
    ): (
        "#40",
        tuple(_d(f"feats.{f}", "", ORIGIN_FEATS_LABEL) for f in ORIGIN_FEATS),
    ),
}


def drafts(inputs: AcceptedInputs) -> tuple[ReferenceResolution, ...]:
    """One reviewed resolution per drafted citation, keyed from the artifact."""
    oracle = inputs.oracle
    view = effective_representation(oracle.representation, oracle.reference_resolutions)
    spans: dict[tuple[str, ...], set[str]] = {}
    for claim in view.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            spans.setdefault(claim.target_key, set()).add(claim.span_id)
    by_citation = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): r
        for r in view.references
        if not r.target_record_key
    }
    out = []
    for citation, (row, destinations) in DRAFTS.items():
        ref = by_citation[citation]
        out.append(
            ReferenceResolution(
                resolution_id=f"alternatives-{row[1:]}-{citation[0]}-{citation[1]}",
                from_record_key=citation[0],
                from_component_key=citation[1],
                source_text=citation[2],
                scope_key=citation[3],
                target_record_key="",
                release_binding=oracle.binding,
                provenance_span_ids=tuple(sorted(spans[reference_target_key(ref)])),
                destinations=destinations,
            )
        )
    return tuple(out)


def _origin_feats(inputs: AcceptedInputs) -> None:
    """#40's group is the source's, and the catalogue still owns every member.

    Release: checked against the pinned ``feats.md``. Containment and order:
    each member's heading lies between ``### Origin Feats`` and ``### General
    Feats``, in this order and with no other. Category: each states "_Origin
    Feat_" before the next heading. Ownership: each is a CATALOGUE_MEMBER of
    ``feats.feat_descriptions`` and of nothing else, so the route adds no owner.
    """
    lines = FEATS_MD.read_text(encoding="utf-8").splitlines()
    start, stop = lines.index("### Origin Feats"), lines.index("### General Feats")
    headings = [i for i in range(start, stop) if lines[i].startswith("#### ")]
    names = [lines[i][5:].strip().lower().replace(" ", "_") for i in headings]
    assert names == list(ORIGIN_FEATS), names
    for i, j in zip(headings, [*headings[1:], stop], strict=True):
        assert "_Origin Feat_" in lines[i:j], lines[i]
    r = inputs.oracle.representation
    for feat in ORIGIN_FEATS:
        owners = {
            e.target_record_key
            for e in r.relationships
            if e.source_record_key == f"feats.{feat}"
            and e.kind is RelationshipKind.CATALOGUE_MEMBER
        }
        assert owners == {"feats.feat_descriptions"}, (feat, owners)


def resolved(inputs: AcceptedInputs) -> AcceptedInputs:
    """Lift to the build's schema and resolve, as one native action."""
    return resolve_references(
        inputs,
        lift_to=(REPRESENTATION_SCHEMA_VERSION, representation_schema_hash()),
        resolutions=drafts(inputs),
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _delta(before: AcceptedInputs, after: AcceptedInputs) -> str:
    """Every reference line that differs between the effective views."""

    def lines(inputs: AcceptedInputs) -> Counter[str]:
        o = inputs.oracle
        view = effective_representation(o.representation, o.reference_resolutions)
        return Counter(
            json.dumps(
                list(reference_target_key(r))
                + [
                    r.situation.value if r.situation else "",
                    r.class_record_key,
                    r.minimum_class_level,
                ],
                ensure_ascii=False,
            )
            for r in view.references
        )

    b, a = lines(before), lines(after)
    removed = sorted((b - a).elements())
    added = sorted((a - b).elements())
    return "".join(f"- {x}\n" for x in removed) + "".join(f"+ {x}\n" for x in added)


def _persisted_round_trip(inputs: AcceptedInputs) -> bool:
    """Build, persist on a scratch copy of the release, and reconstruct.

    The scratch release carries no mechanical tables, so they are created from
    the ORM on the copy; migration 0036 itself is exercised by the test suite.
    """
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as session:
                persist_draft(session, identified, now=SIMULATED_AT)
                session.flush()
                rebuilt = reconstruct_candidate(session, identified.projection_uuid)
                session.rollback()
        finally:
            engine.dispose()
    built = identified.candidate.representation.references
    return bool(
        rebuilt.representation.references == built
        and identify_projection(rebuilt).projection_uuid == identified.projection_uuid
    )


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    _origin_feats(rec)
    final = resolved(rec)
    lifts = final.lifts[len(rec.lifts) :]
    print("lift", [r.lift_id for r in lifts], "->", current[0], current[1])
    # The comparison baseline: the same crossing, with no decision.
    lifted, _ = lift_accepted_inputs(rec, current)
    lifted = dataclasses.replace(lifted, lifts=final.lifts)
    print("lifted (no decision)", _sha(serialize_accepted_inputs(lifted)))

    final_bytes = serialize_accepted_inputs(final)
    print("candidate (simulated)", _sha(final_bytes))
    assert (
        serialize_accepted_inputs(load_accepted_inputs_bytes(final_bytes))
        == final_bytes
    ), "reload"
    print("  reloads to the same bytes True")

    before, after = APC.findings(lifted), APC.findings(final)
    print("findings (refs, leaves)", APC._split(before), "->", APC._split(after))
    cleared = Counter(before) - Counter(after)
    new = Counter(after) - Counter(before)
    print("  cleared", sum(cleared.values()), "new", dict(new))
    assert not new, new
    assert not [f for f in after if "'Origin Feats'" in f], "#40"

    resolutions = final.oracle.reference_resolutions[
        len(rec.oracle.reference_resolutions) :
    ]
    rows = Counter(
        DRAFTS[(r.from_record_key, r.from_component_key, r.source_text, r.scope_key)][0]
        for r in resolutions
    )
    print(
        "resolutions",
        len(resolutions),
        "destinations",
        sum(len(r.destinations) for r in resolutions),
        "routes",
        sum(len({d.alternative_label for d in r.destinations}) for r in resolutions),
        dict(sorted(rows.items())),
    )

    o = final.oracle
    view = effective_representation(o.representation, o.reference_resolutions)
    style = tuple(
        r
        for r in view.references
        if r.from_record_key == "feats.archery" and r.from_component_key == "category"
    )
    split = AlternativeSelection(
        class_levels={"classes.fighter": 0, "classes.paladin": 1, "classes.ranger": 3}
    )
    print(
        "consumer: archery prerequisite, Paladin 1 / Ranger 3 ->",
        [r.alternative_label for r in select_alternatives(style, split)],
    )
    print(
        "consumer: unknown selection keeps",
        len(select_alternatives(style, AlternativeSelection())),
    )
    print("persisted round trip", _persisted_round_trip(final))

    proposal = (
        json.dumps(
            {
                "accepted_sha256": ACCEPTED_SHA256,
                "lift": [r.lift_id for r in lifts],
                "representation_schema": list(current),
                "reference_resolutions": reference_resolution_payload(resolutions),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    delta = _delta(lifted, final).encode("utf-8")
    for path, data in ((PROPOSAL_FILE, proposal), (DELTA_FILE, delta)):
        if write:
            path.write_bytes(data)
        assert path.read_bytes() == data, f"{path.name} is stale; run --write"
        print(path.name, _sha(data), f"{data.count(b'\n')} lines")
    print("OK")


def load_accepted_inputs_bytes(data: bytes) -> AcceptedInputs:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "candidate.json"
        path.write_bytes(data)
        return load_accepted_inputs(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
