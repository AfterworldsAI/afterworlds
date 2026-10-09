"""Three-batch schema-closure matrix — CRD Issue 5d (conditions-1 x actions-1 x hazards-1).

DISPOSABLE REVIEW MATERIAL. Reads the actions-1 and hazards-1 audit trails, folds
in the conditions-1 residue recorded by PR #153, assigns every unresolved span a
defect family AND a closure verdict, then reports per batch how many spans a
truthful reusable bundle could close and what exactly blocks the rest.

Reads only. Writes nothing. Touches no database, oracle, or projection.

VERDICTS
  CLOSEABLE  a closed typed representation exists: >= 2 distinct rules (after
             de-duplicating restatements) in >= 2 top-level sections, over a
             vocabulary already closed in the source or closable without a
             general predicate expression.
  ALTERNATION the rule states OR over heterogeneous alternatives. Encoding it as
             AND would be false; encoding it generally needs a Boolean-expression
             DSL. ARCHITECTURAL boundary.
  OPEN_REF   the precondition or trigger ranges over unbounded fiction.
             ARCHITECTURAL boundary (same root as ALTERNATION).
  SINGULAR   fewer than 2 distinct rules, or all in 1 top-level section. Typing it
             would be clause-specific vocabulary. EVIDENCE shortfall, not
             architecture.

A homogeneous "choose one of these N rolls" set (Falling's Strength (Athletics)
or Dexterity (Acrobatics)) is deliberately NOT counted as ALTERNATION: a closed
set of same-shaped alternatives is a set, not an expression tree.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent


def audit(name: str) -> list[dict]:
    rows = json.loads((OUT / name).read_text(encoding="utf-8"))
    return [r for r in rows if r["disposition"] == "unresolved"]


ACTIONS = audit("issue-5d-batch-actions-1-audit.json")
HAZARDS = audit("issue-5d-batch-hazards-1-audit.json")

CLOSEABLE, ALTERNATION, OPEN_REF, SINGULAR = "CLOSEABLE", "ALTERNATION", "OPEN_REF", "SINGULAR"

# (family, verdict, distinct rules, top-level sections)
FAM = {
    "recurrence":        ("Recurring per-turn effect cadence",      CLOSEABLE, 107, 7),
    "outcome_cond":      ("Outcome-conditional effect",             CLOSEABLE, 224, 10),
    "skill_check":       ("Skill-qualified check",                  CLOSEABLE, 133, 11),
    "unstated_dc":       ("Check with no stated DC",                 CLOSEABLE, 133, 11),
    "duration":          ("Effect duration and expiry",              CLOSEABLE, 109, 10),
    "allowance":         ("Per-turn / per-use allowance quantity",   CLOSEABLE, 32, 8),
    "concentration":     ("Concentration as a requirement",          CLOSEABLE, 32, 6),
    "opportunity":       ("Opportunity-attack exemption",            CLOSEABLE, 23, 5),
    "movement_cost":     ("Movement cost (surcharge, expenditure)",  CLOSEABLE, 14, 5),
    "derived_dc":        ("DC derived from a score or roll total",   CLOSEABLE, 12, 4),
    "level_delta":       ("Condition-level accrual / decrement",     CLOSEABLE, 20, 6),
    "roll_choice":       ("Choose one of N same-shaped rolls",       CLOSEABLE, 3, 2),
    "distance_damage":   ("Distance-scaled damage",                  CLOSEABLE, 3, 3),
    "third_party":       ("Third-party (ally) roll beneficiary",     CLOSEABLE, 3, 2),

    "eligibility":       ("Eligibility precondition",                OPEN_REF, 9, 4),
    "exit_trigger":      ("State-exit trigger enumeration",          OPEN_REF, 38, 7),
    "exclusive_choice":  ("Exclusive choice, heterogeneous options",  ALTERNATION, 55, 9),
    "mode_choice":       ("Movement-mode substitution / choice",      ALTERNATION, 3, 2),
    "sequencing":        ("Deferred action / cross-turn sequencing",  OPEN_REF, 38, 7),
    "negative_cond":     ("Negative applicability condition",         OPEN_REF, 3, 2),
    "removal_restrict":  ("Removal blocked until a fiction holds",    OPEN_REF, 2, 1),
    "threshold_trigger": ("Consumption / duration threshold trigger", OPEN_REF, 4, 1),
    "hazard_end":        ("Hazard termination by an act",             OPEN_REF, 2, 1),

    "sensory":           ("Imposed sensory-capability loss",          SINGULAR, 2, 1),
    # Upgraded on re-sweep. "A creature dies if its Hit Point maximum reaches 0"
    # and "the character dies if the remainder equals or exceeds their Hit Point
    # maximum" (Playing the Game > Instant Death) join Exhaustion's level-6 rule:
    # 3 distinct rules / 2 sections over a closed quantity vocabulary.
    "counter_death":     ("Threshold on a tracked quantity causing death", CLOSEABLE, 3, 2),
    "transformation":    ("Transformation / persistent state change", SINGULAR, 1, 1),
    # Upgraded on re-sweep. Playing the Game > Dropping Prone: "you can give
    # yourself the Prone condition ... but you can't do so if your Speed is 0."
    # Identical closed predicate to Prone's R8, in a different top-level section.
    "prohibition":       ("Conditional prohibition on an act",        CLOSEABLE, 2, 2),
    "exit_residual":     ("State persisting after another ends",      SINGULAR, 1, 1),
    # Upgraded on a symmetric re-sweep (the first pass searched conditions-1 for
    # upgrades and not hazards-1). "Your size and Strength score determine the
    # maximum weight ... as shown in the Carrying Capacity table" (Rules Glossary),
    # the two hazard tables, "one additional vial is required for each size
    # category above Medium" (Oil of Etherealness, Oil of Slipperiness), and
    # "five times its base carrying capacity" (Equipment > Mounts and Cargo):
    # 5 distinct rules / 4 sections over the printed closed size vocabulary
    # (Rules Glossary > Size: Tiny, Small, Medium, Large, Huge, Gargantuan).
    "size_quantity":     ("Size-keyed quantity requirement",          CLOSEABLE, 5, 4),
    "size_waiver":       ("Relative-size waiver of a cost",           SINGULAR, 1, 1),
    "damage_cap":        ("Damage maximum / cap",                     SINGULAR, 1, 1),
    "movement_grant":    ("Movement grant",                           SINGULAR, 1, 1),
    "attitude":          ("Attitude-modified check",                  SINGULAR, 1, 1),
    "interleave":        ("Interleaving movement with other effects", SINGULAR, 1, 1),
    # Upgraded on the same re-sweep, and it was self-inconsistent before: 2 rules
    # in 2 sections already met the stated threshold. The real shape is broader
    # than duration -- "a quantity equal to an ability modifier, with a floor" --
    # and appears 16 times across 5 sections (Bardic Inspiration, Sear Undead,
    # Wholeness of Body, Tireless, Nature's Veil, Suffocation, ...).
    "derived_duration":  ("Quantity from an ability modifier, with a floor", CLOSEABLE, 16, 5),
}

# --- conditions-1: the nine spans preserved by PR #153, unchanged -------------
CONDITIONS = [
    ("R1 Blinded 'You can't see'", "sensory"),
    ("R2 Deafened 'You can't hear'", "sensory"),
    ("R3 Exhaustion accrual + 'You die if ... is 6'", "counter_death"),
    ("R4 Long Rest removes 1 + ends at 0", "level_delta"),
    ("R5 Grappled surcharge + Tiny/two-sizes waiver", "size_waiver"),
    ("R6 Petrified transformation", "transformation"),
    ("R7 Prone crawl-or-stand + half-Speed cost", "exclusive_choice"),
    ("R8 Prone 'If your Speed is 0, you can't right yourself'", "prohibition"),
    ("R9 Unconscious 'you remain Prone'", "exit_residual"),
]

# --- actions-1: audit ordinal -> family --------------------------------------
ACTIONS_MAP = {
    1: "allowance", 2: "allowance", 3: "allowance", 4: "interleave",
    5: "movement_grant", 6: "mode_choice", 7: "mode_choice", 8: "mode_choice",
    9: "opportunity", 10: "duration", 11: "exclusive_choice", 12: "exclusive_choice",
    13: "eligibility", 14: "eligibility", 15: "third_party", 16: "duration",
    17: "eligibility", 18: "third_party", 19: "duration", 20: "skill_check",
    21: "eligibility", 22: "sensory", 23: "outcome_cond", 24: "derived_dc",
    25: "exit_trigger", 26: "attitude", 27: "derived_dc", 28: "outcome_cond",
    29: "eligibility", 30: "concentration", 31: "concentration",
    32: "sequencing", 33: "exclusive_choice", 34: "exclusive_choice",
    35: "sequencing", 36: "concentration", 37: "concentration",
    38: "unstated_dc", 39: "unstated_dc",
}

# --- hazards-1: audit ordinal -> family --------------------------------------
HAZARDS_MAP = {
    1: "recurrence", 2: "hazard_end", 3: "exclusive_choice",
    4: "size_quantity", 5: "threshold_trigger", 6: "level_delta",
    7: "removal_restrict",
    8: "distance_damage", 9: "damage_cap", 10: "negative_cond",
    11: "roll_choice", 12: "outcome_cond",
    13: "size_quantity", 14: "threshold_trigger", 15: "level_delta",
    16: "level_delta", 17: "removal_restrict",
    18: "derived_duration", 19: "level_delta", 20: "removal_restrict",
}

assert len(ACTIONS) == len(ACTIONS_MAP), (len(ACTIONS), len(ACTIONS_MAP))
assert len(HAZARDS) == len(HAZARDS_MAP), (len(HAZARDS), len(HAZARDS_MAP))

BATCHES = {
    "conditions-1": [(lbl, fam) for lbl, fam in CONDITIONS],
    "actions-1": [(f"A{i} {r['text'].strip()[:52]}", ACTIONS_MAP[i])
                  for i, r in enumerate(ACTIONS, 1)],
    "hazards-1": [(f"H{i} {r['text'].strip()[:52]}", HAZARDS_MAP[i])
                  for i, r in enumerate(HAZARDS, 1)],
}

print("=" * 100)
print("CRD Issue 5d — three-batch schema-closure matrix")
print("=" * 100)

per_fam: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
for batch, spans in BATCHES.items():
    for _, fam in spans:
        per_fam[fam][batch] += 1

print(f"\n{'family':<44}{'verdict':<12}{'rules':>6}{'sec':>4}   {'C':>3}{'A':>3}{'H':>3}")
print("-" * 100)
for fam in sorted(per_fam, key=lambda f: (FAM[f][1] != CLOSEABLE, -FAM[f][2])):
    title, verdict, rules, secs = FAM[fam]
    b = per_fam[fam]
    print(f"{title[:43]:<44}{verdict:<12}{rules:>6}{secs:>4}   "
          f"{b.get('conditions-1', 0):>3}{b.get('actions-1', 0):>3}{b.get('hazards-1', 0):>3}")
print("-" * 100)

print("\nPER-BATCH CLOSURE\n")
print(f"{'batch':<16}{'unresolved':>11}{'closeable':>11}{'remaining':>11}   blocked by")
print("-" * 100)
rows = []
for batch, spans in BATCHES.items():
    tot = len(spans)
    ok = sum(1 for _, f in spans if FAM[f][1] == CLOSEABLE)
    blockers: dict[str, int] = defaultdict(int)
    for _, f in spans:
        if FAM[f][1] != CLOSEABLE:
            blockers[FAM[f][1]] += 1
    rows.append((batch, tot, ok, tot - ok))
    desc = ", ".join(f"{k} {v}" for k, v in sorted(blockers.items())) or "nothing"
    print(f"{batch:<16}{tot:>11}{ok:>11}{tot - ok:>11}   {desc}")
print("-" * 100)
t = [sum(r[i] for r in rows) for i in (1, 2, 3)]
print(f"{'TOTAL':<16}{t[0]:>11}{t[1]:>11}{t[2]:>11}")

print("\nDOES ANY BATCH REACH ZERO?")
for batch, tot, ok, rem in rows:
    print(f"  {batch:<16} {'YES' if rem == 0 else f'NO — {rem} spans remain'}")

print("\nMINIMUM OBSTRUCTION, per batch (the exact blocked spans)")
for batch, spans in BATCHES.items():
    blocked = [(lbl, f) for lbl, f in spans if FAM[f][1] != CLOSEABLE]
    print(f"\n  {batch} — {len(blocked)} blocked")
    seen: set[str] = set()
    for lbl, f in blocked:
        if f in seen:
            continue
        seen.add(f)
        print(f"    [{FAM[f][1]:<11}] {FAM[f][0]:<42} x{sum(1 for _, g in blocked if g == f)}")

print("\nROOT OBSTRUCTIONS")
arch = {f for f in FAM if FAM[f][1] in (ALTERNATION, OPEN_REF)}
ev = {f for f in FAM if FAM[f][1] == SINGULAR}
used = {f for spans in BATCHES.values() for _, f in spans}
print(f"  architectural (needs alternation / predicate expression): "
      f"{sum(1 for spans in BATCHES.values() for _, f in spans if f in arch)} spans, "
      f"{len(arch & used)} families")
print(f"  evidence shortfall (singular; typing = clause-specific vocabulary): "
      f"{sum(1 for spans in BATCHES.values() for _, f in spans if f in ev)} spans, "
      f"{len(ev & used)} families")
