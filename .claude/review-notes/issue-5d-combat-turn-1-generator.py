# ruff: noqa: E501  -- clause literals are verbatim source text, kept whole to be greppable
"""Author the fresh **combat-turn-1** proposal: 6 complete glossary entries.

REVIEW MATERIAL for CRD Issue 5d (#137) over the qualified 5c release
``9717e288-c099-5217-b2d2-f89aeabd7b73`` / ``5.2.1-corpus.883aabdf-462``. It
emits an *unaccepted* ``5d-proposal-2`` artifact. It accepts nothing, publishes
nothing, writes nothing under ``oracles/``, and imports no earlier batch's
content, identity or authority: every entry is read afresh from the release.

Scope: Initiative, Occupied Space, Opportunity Attacks, Reach, Surprise and
Unoccupied Space -- six peer entries under *Rules Glossary > Rules
Definitions*, 13 leaves (six of them headings), one ``ENTRY`` review unit
each. They do not close Combat: three of them point at *Playing the Game*
("Combat"), the exact section ``play.combat`` in scope
``srd-5.2.1/playing-the-game`` that the accepted reference-closure batch
already cites and no batch has authored. Those pointers stay explicit unknown
targets; the batch opens no other.

This file is literal review data only; the assembly is the committed shared
:mod:`afterworlds.ingestion.mechanical.authoring`. ``CLAUSES`` is the source
review; ``COMPONENTS`` is the representation proposed for it; expected rules
come from ``CLAUSES`` alone.

Authoring conventions (as the accepted batches):

* A typed fact is used only where it is true under the conditions the typed
  surface states. A condition the closed vocabulary cannot state stays in the
  same component's governing prose, beside the fact it conditions.
* One source statement, one typed copy.
* Terms carried by closed code-owned vocabulary (Reaction, Bonus Action,
  Initiative inside a fact, the speeds a creature moves by) are bound by that
  type, not by a reference. *See also* pointers and glossary terms a rule
  depends on (reach, Unarmed Strike) are references.

Run: ``python issue-5d-combat-turn-1-generator.py <published afterworlds.db>``
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
    ActionAllowanceFact,
    ActionCost,
    ActionEconomyFact,
    AdvantageFact,
    AdvantageState,
    AllowanceScope,
    GrantedActivity,
    RecordKind,
    RollActor,
    RollContext,
    RollSpec,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
)

ORIGIN = "issue-5d-combat-turn-1-generator.py"
PROPOSAL_FILE = "issue-5d-combat-turn-1-PROPOSAL.json"
PARENT = ("Rules Glossary", "Rules Definitions")

#: (record slug, printed container label, record kind), in printed order.
ENTRIES: tuple[tuple[str, str, RecordKind], ...] = (
    ("initiative", "Initiative", RecordKind.GLOSSARY_RULE),
    ("occupied_space", "Occupied Space", RecordKind.GLOSSARY_RULE),
    ("opportunity_attacks", "Opportunity Attacks", RecordKind.GLOSSARY_RULE),
    ("reach", "Reach", RecordKind.GLOSSARY_RULE),
    ("surprise", "Surprise", RecordKind.GLOSSARY_RULE),
    ("unoccupied_space", "Unoccupied Space", RecordKind.GLOSSARY_RULE),
)

# ---------------------------------------------------------------------------
# Reason codes and handling
# ---------------------------------------------------------------------------
CTX = "contextual_applicability"
GM = "gamemaster_latitude"
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

#: The three sentences of Opportunity Attacks: the trigger, the Reaction and
#: its one attack, and the timing. The trigger and the timing condition the
#: typed facts, so all three are one component's clauses.
OA_TRIGGER = "You can make an Opportunity Attack when a creature that you can see leaves your reach using its action, its Bonus Action, its Reaction, or one of its speeds."
OA_ATTACK = "To make the Opportunity Attack, take a Reaction to make one melee attack with a weapon or an Unarmed Strike against the provoking creature."
OA_TIMING = "The attack occurs right before the creature leaves your reach."

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts). Every rule-stating sentence of the batch is named here.
CLAUSES: tuple[tuple[str, str, tuple[str | None, ...], tuple[str, ...]], ...] = (
    # -- Initiative -----------------------------------------------------------
    (
        "initiative",
        "turn_order",
        (PROSE,),
        ("Initiative determines the order of turns during combat.",),
    ),
    (
        "initiative",
        "score_instead_of_roll",
        (PROSE,),
        (
            "Sometimes a GM might have combatants use their Initiative scores instead of rolling Initiative.",
        ),
    ),
    (
        "initiative",
        "initiative_score",
        (PROSE,),
        (
            "Your Initiative score equals 10 plus your Dexterity modifier.",
            "If you have Advantage on Initiative rolls, increase your Initiative score by 5.",
            "If you have Disadvantage on those rolls, decrease that score by 5.",
        ),
    ),
    # -- Occupied Space -------------------------------------------------------
    (
        "occupied_space",
        "definition",
        (PROSE,),
        (
            "A space is occupied if a creature is in it or if it is completely filled by objects.",
        ),
    ),
    # -- Opportunity Attacks --------------------------------------------------
    (
        "opportunity_attacks",
        "opportunity_attack",
        ("action_economy", "action_allowance", PROSE),
        (OA_TRIGGER, OA_ATTACK, OA_TIMING),
    ),
    # -- Reach ----------------------------------------------------------------
    (
        "reach",
        "default_reach",
        (PROSE,),
        ("A creature has a reach of 5 feet unless a rule says otherwise.",),
    ),
    # -- Surprise -------------------------------------------------------------
    (
        "surprise",
        "surprised",
        ("advantage", PROSE),
        (
            "If a creature is caught unawares by the start of combat, that creature is surprised, which causes it to have Disadvantage on its Initiative roll.",
        ),
    ),
    # -- Unoccupied Space -----------------------------------------------------
    (
        "unoccupied_space",
        "definition",
        (PROSE,),
        (
            "A space is unoccupied if no creatures are in it and it isn't completely filled by objects.",
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
    # Initiative. What Initiative does is one prose unit. The score option is
    # the GM's; the score's formula (10 plus the Dexterity modifier) and its
    # +5/-5 adjustments have no faithful family -- DerivedQuantityFact derives a
    # time, not a score -- so they are exact prose, as the jump formulas are.
    C("initiative", "turn_order", P, NO_USE),
    C("initiative", "score_instead_of_roll", P, GM),
    C("initiative", "initiative_score", P, NO_USE),
    # Occupied / Unoccupied Space: mirror definitions, each one prose unit.
    C("occupied_space", "definition", P, NO_USE),
    C("unoccupied_space", "definition", P, NO_USE),
    # Opportunity Attacks. The Reaction the attacker spends and the one attack
    # it buys are typed (as Falling's Reaction and Attack's one attack roll);
    # the trigger (a creature you can see leaving your reach using its action,
    # its Bonus Action, its Reaction, or one of its speeds), "melee", "with a weapon or an Unarmed Strike", "against the provoking
    # creature" and "right before" stay the component's governing prose.
    C(
        "opportunity_attacks",
        "opportunity_attack",
        M,
        CTX,
        facts=(
            ActionEconomyFact(ActionCost.REACTION),
            ActionAllowanceFact(
                1, AllowanceScope.OWNING_EFFECT, activity=GrantedActivity.ATTACK_ROLL
            ),
        ),
        refs=(
            ("reach", "reach"),
            ("Unarmed Strike", "unarmed_strike"),
        ),
    ),
    # Reach. A creature's default reach has no carrier: AttackRollFact states a
    # reach only on a stated attack roll with its bonus. Exact prose.
    C("reach", "default_reach", P, NO_USE),
    # Surprise. Disadvantage on the subject's own Initiative roll is exactly the
    # accepted Incapacitated "Surprised" fact; being caught unawares by the
    # start of combat is fiction and stays the component's prose.
    C(
        "surprise",
        "surprised",
        M,
        CTX,
        facts=(
            AdvantageFact(
                AdvantageState.DISADVANTAGE,
                RollSpec(RollActor.SUBJECT, RollContext.INITIATIVE),
            ),
        ),
    ),
)

SEE_ALSO_COMBAT = '_See also_ "Playing the Game" ("Combat").'

#: Supporting spans: (entry, text, component supported or ``None`` for the
#: record). *See also* pointers identify another section; Initiative's second
#: sentence points at where rolling Initiative is explained.
SUPPORTING: tuple[tuple[str, str, str | None], ...] = (
    (
        "initiative",
        'The combat rules in "Playing the Game" explain how to roll Initiative.',
        "turn_order",
    ),
    ("initiative", SEE_ALSO_COMBAT, None),
    ("opportunity_attacks", SEE_ALSO_COMBAT, None),
    ("surprise", SEE_ALSO_COMBAT, None),
)

#: The exact out-of-glossary destination of the "Playing the Game" ("Combat")
#: pointers, as the accepted reference-closure batch states it for Speed.
PLAY_COMBAT = ("srd-5.2.1/playing-the-game", "play.combat")

#: Record-owned references: (entry, printed text, target, texts of the spans the
#: pointer is read from).
RECORD_REFERENCES: tuple[RecordReference, ...] = (
    ("initiative", "Combat", PLAY_COMBAT, (SEE_ALSO_COMBAT,)),
    ("opportunity_attacks", "Combat", PLAY_COMBAT, (SEE_ALSO_COMBAT,)),
    ("surprise", "Combat", PLAY_COMBAT, (SEE_ALSO_COMBAT,)),
)

#: Targets outside this batch that no accepted record defines. Only the
#: pre-existing Combat dependency; it stays an explicit unknown target,
#: composed or not.
OUTSTANDING_TARGETS: tuple[Target, ...] = (PLAY_COMBAT,)
#: Targets outside this batch that the accepted inputs define. The proposal
#: alone reports them; composed with them they resolve.
ACCEPTED_CONTEXT_TARGETS = ("unarmed_strike",)


def batch() -> EntryBatch:
    """The tables above, read at call time so tests can mutate them."""
    return EntryBatch(
        origin=ORIGIN,
        schema=(SCHEMA_15_VERSION, SCHEMA_15_HASH),
        proposal_origin=f"{ORIGIN} (CRD Issue 5d fresh combat-turn-1 batch; unaccepted)",
        unit_prefix="combat-turn-1",
        parent=PARENT,
        entries=ENTRIES,
        expected_leaves=13,
        clauses=CLAUSES,
        framing=FRAMING,
        components=COMPONENTS,
        supporting=SUPPORTING,
        record_references=RECORD_REFERENCES,
    )


def build(session: Session) -> Built:
    """Derive the combat-turn-1 proposal from the release *session* published."""
    return build_entry_batch(session, batch(), published_release_binding(session))


def expected_representation_findings() -> list[str]:
    """Exactly the out-of-batch targets, accepted-context and outstanding."""
    return unknown_target_findings(
        RECORD_REFERENCES, COMPONENTS, (*OUTSTANDING_TARGETS, *ACCEPTED_CONTEXT_TARGETS)
    )


def main(db: str) -> int:
    out = Path(__file__).resolve().parent / PROPOSAL_FILE
    return emit(db, build, out, expected_representation_findings())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
