# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **damage-and-hit-points** proposal: 7 complete glossary entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority: every entry is read afresh from the release.

Scope: Damage, Damage Roll, Hit Points, Immunity, Resistance, Temporary Hit
Points and Vulnerability -- seven peer entries under *Rules Glossary > Rules
Definitions*, 14 leaves (seven of them headings), one ``ENTRY`` review unit
each. Five entries point at *Playing the Game* ("Damage and Healing") and Hit
Points points at "Breaking Objects"; no accepted record defines either target,
so both stay unresolved and are cited, not retargeted.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the four accepted batches):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions.
* One source statement, one typed copy.
* Terms carried by closed code-owned vocabulary (the "(round down)" of
  Resistance, as the accepted Prone's) are bound by that type, not by a
  reference. *See also* pointers and in-batch glossary terms a rule depends on
  are references. Generic lowercase nouns stay unreferenced even where an entry
  of that name exists, as the accepted batches leave "damage" (Concentration,
  Falling) and "condition": here "damage", "healing", "a damage type" and "a
  condition".

Run: ``python issue-5d-damage-and-hit-points-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    RecordReference,
    Target,
    build_entry_batch,
    emit,
    unknown_target_findings,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    DamageModDirection,
    DamageModificationFact,
    Rational,
    RecordKind,
    RoundingRule,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-damage-and-hit-points-generator.py"
PROPOSAL_FILE = "issue-5d-damage-and-hit-points-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("damage", "Damage", RecordKind.GLOSSARY_RULE),
    ("damage_roll", "Damage Roll", RecordKind.GLOSSARY_RULE),
    ("hit_points", "Hit Points", RecordKind.GLOSSARY_RULE),
    ("immunity", "Immunity", RecordKind.GLOSSARY_RULE),
    ("resistance", "Resistance", RecordKind.GLOSSARY_RULE),
    ("temporary_hit_points", "Temporary Hit Points", RecordKind.GLOSSARY_RULE),
    ("vulnerability", "Vulnerability", RecordKind.GLOSSARY_RULE),
)

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
NO_USE = "no_identified_structured_use"
S, M, P = (
    ComponentHandling.STRUCTURED,
    ComponentHandling.MIXED,
    ComponentHandling.PROSE_BOUND,
)
PROSE = None

# ---------------------------------------------------------------------------
# Source review: what each printed clause must be read as
# ---------------------------------------------------------------------------

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # -- Damage (p180) ------------------------------------------------------
    (
        "damage",
        "definition",
        (PROSE,),
        (
            "Damage represents harm that causes a creature or an object to lose Hit Points.",
        ),
    ),
    # -- Damage Roll (p180) -------------------------------------------------
    (
        "damage_roll",
        "definition",
        (PROSE,),
        (
            "A damage roll is a die roll, adjusted by any applicable modifiers, that deals damage to a target.",
        ),
    ),
    # -- Hit Points (p183) --------------------------------------------------
    (
        "hit_points",
        "definition",
        (PROSE,),
        (
            "Hit Points (HP) are a measure of how difficult it is to kill or destroy a creature or an object.",
        ),
    ),
    (
        "hit_points",
        "loss_restoration_and_bounds",
        (PROSE,),
        (
            "Damage reduces Hit Points, and healing restores them.",
            "You can't have more Hit Points than your Hit Point maximum, and you can't have less than 0.",
        ),
    ),
    # -- Immunity (p183) ----------------------------------------------------
    (
        "immunity",
        "no_effect",
        (PROSE,),
        (
            "If you have Immunity to a damage type or a condition, it doesn't affect you in any way.",
        ),
    ),
    # -- Resistance (p187) --------------------------------------------------
    (
        "resistance",
        "halving",
        ("damage_modification", PROSE),
        (
            "If you have Resistance to a damage type, damage of that type is halved against you (round down).",
            "Resistance is applied only once to an instance of damage.",
        ),
    ),
    # -- Temporary Hit Points (p190) ----------------------------------------
    (
        "temporary_hit_points",
        "buffer",
        (PROSE,),
        (
            "Temporary Hit Points are granted by certain effects and act as a buffer against losing real Hit Points.",
        ),
    ),
    # -- Vulnerability (p191) -----------------------------------------------
    (
        "vulnerability",
        "doubling",
        ("damage_modification", PROSE),
        (
            "If you have Vulnerability to a damage type, damage of that type is doubled against you.",
            "Vulnerability is applied only once to an instance of damage.",
        ),
    ),
)

#: No whole-leaf framing: every non-heading leaf of these entries states a rule.
FRAMING: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# Representation proposed for the clauses above
# ---------------------------------------------------------------------------

C = EntryComponent

COMPONENTS: tuple[EntryComponent, ...] = (
    # Definitions. No family states what damage, a damage roll or Hit Points
    # *are*; the numeric families (DamageFact, DiceExpression) are used where a
    # rule states an amount, which none of these does.
    C("damage", "definition", P, NO_USE, refs=(("Hit Points", "hit_points"),)),
    C("damage_roll", "definition", P, NO_USE),
    C("hit_points", "definition", P, NO_USE),
    # Loss, restoration and the two bounds are one unit: the bounds limit the
    # very change the first sentence states. No typed family tracks Hit Points
    # (TrackedQuantity is Speed, condition level and weight only), so the
    # meaning is carried by this exact prose.
    C("hit_points", "loss_restoration_and_bounds", P, NO_USE),
    # "doesn't affect you in any way" is a nullification, not a scaled amount:
    # DamageModificationFact rejects a zero factor, and it could not speak to a
    # condition anyway. Possession of an immunity is typed where a record states
    # it (DamageResponseFact / ConditionEffectFact IMMUNITY); this record states
    # what that possession means, and its exact prose carries it.
    C("immunity", "no_effect", P, NO_USE),
    # The halving and its printed rounding are typed. The possession trigger
    # ("If you have Resistance to a damage type ... of that type ... against
    # you") has no ApplicabilityKind, and "applied only once to an instance of
    # damage" limits this same halving; both stay this component's own prose,
    # as the accepted Difficult Terrain surcharge keeps its trigger and its
    # noncumulative rule (M / NO_USE).
    C(
        "resistance",
        "halving",
        M,
        NO_USE,
        facts=(
            DamageModificationFact(
                DamageModDirection.REDUCE,
                Rational(1, 2),
                rounding=RoundingRule.DOWN,
            ),
        ),
    ),
    # "granted by certain effects" is open-ended, as Hover's "some spells and
    # other effects grant"; the buffer against "real Hit Points" is Hit Points.
    C(
        "temporary_hit_points",
        "buffer",
        P,
        CTX,
        refs=(("Hit Points", "hit_points"),),
    ),
    # As Resistance. The source states no rounding, and doubling an integer
    # yields none, so ``rounding`` stays unset.
    C(
        "vulnerability",
        "doubling",
        M,
        NO_USE,
        facts=(DamageModificationFact(DamageModDirection.INCREASE, Rational(2, 1)),),
    ),
)

DAMAGE_AND_HEALING_SEE_ALSO = '_See also_ "Playing the Game" ("Damage and Healing").'
HIT_POINTS_SEE_ALSO = (
    '_See also_ "Breaking Objects" and "Playing the Game" ("Damage and Healing").'
)

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). *See also* pointers identify another entry or section.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    ("damage_roll", DAMAGE_AND_HEALING_SEE_ALSO, None),
    ("hit_points", HIT_POINTS_SEE_ALSO, None),
    ("resistance", DAMAGE_AND_HEALING_SEE_ALSO, None),
    ("temporary_hit_points", DAMAGE_AND_HEALING_SEE_ALSO, None),
    ("vulnerability", DAMAGE_AND_HEALING_SEE_ALSO, None),
)

#: The *Playing the Game* ("Damage and Healing") section, keyed as the accepted
#: ``play.combat`` target is: its printed text is the section name, the chapter
#: is the scope. No batch has authored that chapter.
PLAY_DAMAGE_AND_HEALING = ("srd-5.2.1/playing-the-game", "play.damage_and_healing")

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from). The unqualified "Breaking Objects" is the glossary
#: entry: every unqualified *See also* name in the accepted batches is a
#: glossary entry, and chapter pointers are printed "Playing the Game" ("...").
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    (
        "damage_roll",
        "Damage and Healing",
        PLAY_DAMAGE_AND_HEALING,
        (DAMAGE_AND_HEALING_SEE_ALSO,),
    ),
    ("hit_points", "Breaking Objects", "breaking_objects", (HIT_POINTS_SEE_ALSO,)),
    (
        "hit_points",
        "Damage and Healing",
        PLAY_DAMAGE_AND_HEALING,
        (HIT_POINTS_SEE_ALSO,),
    ),
    (
        "resistance",
        "Damage and Healing",
        PLAY_DAMAGE_AND_HEALING,
        (DAMAGE_AND_HEALING_SEE_ALSO,),
    ),
    (
        "temporary_hit_points",
        "Damage and Healing",
        PLAY_DAMAGE_AND_HEALING,
        (DAMAGE_AND_HEALING_SEE_ALSO,),
    ),
    (
        "vulnerability",
        "Damage and Healing",
        PLAY_DAMAGE_AND_HEALING,
        (DAMAGE_AND_HEALING_SEE_ALSO,),
    ),
)

#: Targets outside this batch that no accepted record defines. Each citation is
#: an expected unresolved-reference finding, repeats included.
OUTSTANDING_TARGETS: tuple[Target, ...] = (
    "breaking_objects",
    PLAY_DAMAGE_AND_HEALING,
)
#: Targets outside this batch that the accepted inputs define: none. Hit Points,
#: the only glossary term cited, is in this batch.
ACCEPTED_CONTEXT_TARGETS: tuple[Target, ...] = ()


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh damage-and-hit-points batch; unaccepted)",
        unit_prefix="damage-and-hit-points",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=14,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the damage-and-hit-points proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def expected_representation_findings() -> list[str]:
    """Exactly the out-of-batch targets no accepted record defines."""
    return unknown_target_findings(
        RECORD_REFERENCES, COMPONENTS, (*OUTSTANDING_TARGETS, *ACCEPTED_CONTEXT_TARGETS)
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
