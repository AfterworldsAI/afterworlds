"""Corrected three-batch matrix at MECHANICAL-OBLIGATION granularity — CRD Issue 5d.

DISPOSABLE REVIEW MATERIAL. Supersedes `issue-5d-schema-closure-threebatch-matrix.py`,
which is preserved unchanged. Reads only; writes nothing; touches no database,
oracle, or projection.

WHY THIS EXISTS
The previous matrix classified whole *proposal spans*. Several spans bundle two or
more independently classifiable mechanics, so one blocked mechanic marked the whole
span blocked and hid the rest. It also treated "ComponentDraft has no slot for this"
as evidence that a Boolean-expression DSL was required, and treated "one printed
rule" as proof that a mechanic could not be represented at all. Both were wrong.

This matrix re-cuts every unresolved span into its distinct mechanical obligations
and classifies each obligation against a five-way test, of which only the last
presumptively crosses the architectural boundary:

  TYPED_FACT      an existing or evidence-backed fact family carries it
  CLOSED_VOCAB    it needs a new closed vocabulary whose members are printed or
                  enumerable in the corpus
  CLOSED_ALT      a bounded alternatives structure over complete typed component
                  variants: no nesting, no negation inside a variant, exactly one
                  variant chosen
  CLOSED_PRECOND  a single typed precondition/trigger/phase over a closed
                  vocabulary, optionally negated as a whole
  OPEN_REFERENT   the operand is supplied by runtime/world state and is not
                  enumerable
  BOOLEAN_DSL     arbitrary nested Boolean predicates -- the architectural boundary

The first four are closed typed constructions and do NOT cross the boundary.
OPEN_REFERENT is a runtime-evaluation question, not necessarily a representation
one, and is reported separately.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent

TYPED_FACT = "TYPED_FACT"
CLOSED_VOCAB = "CLOSED_VOCAB"
CLOSED_ALT = "CLOSED_ALT"
CLOSED_PRECOND = "CLOSED_PRECOND"
OPEN_REFERENT = "OPEN_REFERENT"
BOOLEAN_DSL = "BOOLEAN_DSL"

CLOSED = {TYPED_FACT, CLOSED_VOCAB, CLOSED_ALT, CLOSED_PRECOND}

# ---------------------------------------------------------------------------
# conditions-1 — every unresolved span re-cut into distinct obligations.
# (span_id, obligation, verdict, proposed representation, evidence)
# ---------------------------------------------------------------------------

CONDITIONS_OBLIGATIONS = [
    ("R1", "Blinded: sight capability is removed", CLOSED_VOCAB,
     "SensoryCapabilityFact(sense=SIGHT, can_perceive=False)",
     "Sense vocabulary: Blindsight/Darkvision/Tremorsense/Truesight are printed "
     "glossary entries; 373 occurrences / 9 sections"),
    ("R2", "Deafened: hearing capability is removed", CLOSED_VOCAB,
     "SensoryCapabilityFact(sense=HEARING, can_perceive=False)",
     "same vocabulary; Blindsight's own text ties sight-capability to the Blinded condition"),
    ("R3a", "Exhaustion levels accrue, 1 per application, cumulative", TYPED_FACT,
     "ConditionLevelFact(EXHAUSTION, GAIN, amount=1, cumulative=True)",
     "20 distinct rules / 6 sections (hazards, Gameplay Toolbox environmental effects)"),
    ("R3b", "At Exhaustion level 6 the creature dies", CLOSED_PRECOND,
     "StateEffectFact(DIES) + Applicability(QUANTITY_THRESHOLD, CONDITION_LEVEL, EQUALS, 6)",
     "'dies' 86 occurrences / 8 sections; quantity threshold: Speed 0, HP max 0, Exh 6/0"),
    ("R4a", "A Long Rest removes 1 Exhaustion level", TYPED_FACT,
     "ConditionLevelFact(EXHAUSTION, REMOVE, amount=1) + Applicability(TRIGGER, LONG_REST)",
     "RecoveryTrigger.LONG_REST already exists; removal 4 rules / 3 sections"),
    ("R4b", "At level 0 the Exhaustion condition ends", CLOSED_PRECOND,
     "ConditionEffectFact(EXHAUSTION, REMOVES) + Applicability(QUANTITY_THRESHOLD, CONDITION_LEVEL, REACHES, 0)",
     "ConditionEffectKind.REMOVES already exists; threshold vocabulary as R3b"),
    # R5a WITHDRAWN as a separate obligation. "The grappler can drag or carry you
    # when it moves" identifies *whose* movement the surcharge applies to; it is
    # SUPPORTING_AUTHORITY contextually linked to the movement component, matching
    # how conditions-1 already treats framing clauses. A ForcedMovementFact family
    # was drafted (11 occurrences / 4 sections) and dropped: those siblings state a
    # displacement of N feet, which is not what this clause states, so the family
    # would have been admitted on siblings it does not actually match.
    ("R5b", "Each foot of the grappler's movement costs 1 extra foot", TYPED_FACT,
     "MovementCostFact(PER_FOOT_SURCHARGE, FEET, feet=1)",
     "14 distinct rules / 5 sections"),
    ("R5c", "Waived if the grappled creature is Tiny, or two or more sizes smaller",
     CLOSED_PRECOND,
     "Applicability(SIZE_COMPARISON, negated=True, any_of=(SizeComparison(ABSOLUTE, TINY), "
     "SizeComparison(RELATIVE, SMALLER, at_least=2)))",
     "9 size-comparison instances / 4 sections; CreatureSize printed closed "
     "(Rules Glossary > Size: Tiny..Gargantuan)"),
    ("R6a", "The subject transforms into an inanimate object, carried nonmagical objects included",
     TYPED_FACT,
     "TransformationFact(becomes=OBJECT, carried_nonmagical_included=True)",
     "True Polymorph: 'If you turn a creature into an object, it transforms along with "
     "whatever it is wearing and carrying'; 14 occurrences / 3 sections, both "
     "`becomes` members and both inclusion values instantiated"),
    ("R6b", "The subject's weight is multiplied by ten", TYPED_FACT,
     "QuantityMultiplierFact(quantity=WEIGHT, factor=10)",
     "6 distinct rules / 6 sections (carrying capacity x5, range doubles, area x2, HP x Hit Dice)"),
    ("R6c", "The subject stops aging", CLOSED_VOCAB,
     "StateEffectFact(AGING_SUSPENDED)",
     "2 rules / 2 sections (Petrified, Imprisonment) - the same bar "
     "UNAWARE_OF_SURROUNDINGS cleared; thin, and stated as such"),
    ("R6d", "'(usually stone)' - which substance", OPEN_REFERENT,
     "prose binding under open_ended_effect -> the component is MIXED, not UNRESOLVED",
     "the source hedges with 'usually', so the substance space is unbounded; "
     "the mechanically load-bearing claim (creature -> object, carried gear "
     "included) is typed by R6a"),
    ("R7a", "Movement is restricted to exactly two options", CLOSED_ALT,
     "Component.alternatives = (variant_crawl, variant_stand); exhaustive=True",
     "exclusive choice 55 occurrences / 9 sections"),
    ("R7b", "Option 1: crawl", TYPED_FACT,
     "variant_crawl = (MovementPermissionFact(mode=CRAWL),)  # MovementMode += CRAWL",
     "Crawling is a printed glossary rule structurally parallel to Climbing and "
     "Swimming, whose modes CLIMB and SWIM are already MovementMode members"),
    ("R7c", "Option 2: spend half Speed (round down) to right yourself, ending the condition",
     TYPED_FACT,
     "variant_stand = (MovementCostFact(EXPENDITURE, HALF_SPEED), "
     "ConditionEffectFact(PRONE, REMOVES))",
     "expenditure 6 distinct rules / 4 sections; Mounting states the identical half-Speed form"),
    ("R8", "Option 2 is unavailable while Speed is 0", CLOSED_PRECOND,
     "variant_stand.applies_when = Applicability(QUANTITY_THRESHOLD, SPEED, EQUALS, 0, negated=True)",
     "2 distinct rules / 2 sections - Prone, and Playing the Game > Dropping Prone "
     "uses the identical predicate"),
    ("R9", "Prone persists after Unconscious ends", CLOSED_PRECOND,
     "ConditionEffectFact(PRONE, APPLIES) + Applicability(PHASE, ON_END)",
     "'when the spell/effect/condition ends' 34 occurrences / 4 sections"),
]

# ---------------------------------------------------------------------------
# actions-1 and hazards-1 — re-verdicted at obligation granularity.
# (count, verdict) per family, reusing the previous span mapping.
# ---------------------------------------------------------------------------

ACTIONS_REVERDICT = [
    ("allowance quantity", 3, TYPED_FACT),
    ("interleaving movement with attacks", 1, OPEN_REFERENT),
    ("movement grant", 1, CLOSED_VOCAB),
    ("movement-mode substitution / choice", 3, CLOSED_ALT),
    ("opportunity-attack exemption", 1, TYPED_FACT),
    ("effect duration and expiry", 3, TYPED_FACT),
    ("benefit-loss on a state", 1, CLOSED_PRECOND),
    ("exclusive choice, heterogeneous options", 3, CLOSED_ALT),
    ("eligibility: obscurement / cover / line of sight", 5, OPEN_REFERENT),
    ("third-party (ally) roll beneficiary", 2, TYPED_FACT),
    ("skill-qualified check", 1, TYPED_FACT),
    ("reciprocal perception", 1, OPEN_REFERENT),
    ("outcome-conditional effect", 2, CLOSED_PRECOND),
    ("DC derived from a score or roll total", 2, TYPED_FACT),
    ("state-exit trigger enumeration", 1, OPEN_REFERENT),
    ("attitude-modified check", 1, OPEN_REFERENT),
    ("concentration as a requirement", 4, TYPED_FACT),
    ("deferred action / arbitrary trigger", 2, OPEN_REFERENT),
    ("check with no stated DC", 2, TYPED_FACT),
]

HAZARDS_REVERDICT = [
    ("recurring per-turn cadence", 1, CLOSED_PRECOND),
    ("hazard termination by an act", 1, TYPED_FACT),
    ("disjunctive fictional exit triggers", 1, OPEN_REFERENT),
    ("size-keyed quantity requirement", 2, TYPED_FACT),
    ("consumption / duration threshold trigger", 2, OPEN_REFERENT),
    ("condition-level accrual / decrement", 4, TYPED_FACT),
    ("removal blocked until a fiction holds", 3, OPEN_REFERENT),
    ("distance-scaled damage", 1, TYPED_FACT),
    ("damage maximum / cap", 1, CLOSED_VOCAB),
    ("negative applicability condition", 1, OPEN_REFERENT),
    ("choose one of N same-shaped rolls", 1, CLOSED_ALT),
    ("outcome-conditional effect", 1, CLOSED_PRECOND),
    ("quantity from an ability modifier, with a floor", 1, TYPED_FACT),
]

# ---------------------------------------------------------------------------

SPANS = {"conditions-1": 9, "actions-1": 39, "hazards-1": 20}


def audit_spans(name: str) -> int:
    rows = json.loads((OUT / name).read_text(encoding="utf-8"))
    return sum(1 for r in rows if r["disposition"] == "unresolved")


assert audit_spans("issue-5d-batch-actions-1-audit.json") == 39
assert audit_spans("issue-5d-batch-hazards-1-audit.json") == 20

print("=" * 92)
print("CRD Issue 5d — corrected matrix at MECHANICAL-OBLIGATION granularity")
print("=" * 92)

print("\nCONDITIONS-1 — every obligation, re-cut from 9 proposal spans\n")
print(f"{'id':<5}{'verdict':<16}obligation")
print("-" * 92)
for sid, obl, verdict, _repr, _ev in CONDITIONS_OBLIGATIONS:
    print(f"{sid:<5}{verdict:<16}{obl[:70]}")
print("-" * 92)

c_tot = len(CONDITIONS_OBLIGATIONS)
c_ok = sum(1 for *_, v, _r, _e in [(o[0], o[1], o[2], o[3], o[4]) for o in CONDITIONS_OBLIGATIONS]
           if v in CLOSED)
c_ok = sum(1 for o in CONDITIONS_OBLIGATIONS if o[2] in CLOSED)
c_open = sum(1 for o in CONDITIONS_OBLIGATIONS if o[2] == OPEN_REFERENT)
c_dsl = sum(1 for o in CONDITIONS_OBLIGATIONS if o[2] == BOOLEAN_DSL)
print(f"obligations {c_tot}   closed-typed {c_ok}   open-referent {c_open}   boolean-DSL {c_dsl}")

print("\n\nPER-BATCH, obligations\n")
print(f"{'batch':<14}{'spans':>7}{'obligations':>13}{'closed':>8}{'open-ref':>10}{'DSL':>5}")
print("-" * 92)


def tally(rows):
    tot = sum(n for _, n, _ in rows)
    ok = sum(n for _, n, v in rows if v in CLOSED)
    op = sum(n for _, n, v in rows if v == OPEN_REFERENT)
    ds = sum(n for _, n, v in rows if v == BOOLEAN_DSL)
    return tot, ok, op, ds


rows_out = [("conditions-1", SPANS["conditions-1"], c_tot, c_ok, c_open, c_dsl)]
for name, rows in (("actions-1", ACTIONS_REVERDICT), ("hazards-1", HAZARDS_REVERDICT)):
    tot, ok, op, ds = tally(rows)
    rows_out.append((name, SPANS[name], tot, ok, op, ds))

for name, sp, tot, ok, op, ds in rows_out:
    print(f"{name:<14}{sp:>7}{tot:>13}{ok:>8}{op:>10}{ds:>5}")
print("-" * 92)
tt = [sum(r[i] for r in rows_out) for i in (1, 2, 3, 4, 5)]
print(f"{'TOTAL':<14}{tt[0]:>7}{tt[1]:>13}{tt[2]:>8}{tt[3]:>10}{tt[4]:>5}")

print("\nDOES CONDITIONS-1 REACH ZERO UNDER CLOSED TYPED STRUCTURES?")
print(f"  closed-typed obligations : {c_ok} / {c_tot}")
print(f"  requiring a Boolean DSL  : {c_dsl}")
print(f"  open referent            : {c_open}"
      f"  ({[o[0] for o in CONDITIONS_OBLIGATIONS if o[2] == OPEN_REFERENT]})")
print()
if c_dsl == 0 and c_open <= 1:
    print("  => YES, subject to the single open referent being a legitimate prose binding.")
else:
    print("  => NO.")

print("\nARCHITECTURAL BOUNDARY")
print(f"  obligations across all three batches requiring arbitrary nested Boolean "
      f"predicates: {tt[4]}")
