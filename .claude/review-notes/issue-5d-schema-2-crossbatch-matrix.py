"""Cross-batch defect-family matrix — CRD Issue 5d schema-2 decision.

DISPOSABLE REVIEW MATERIAL. Reads the actions-1 audit trail, assigns every
unresolved span to exactly one defect family, folds in the conditions-1 residue
recorded by PR #153, and prints the matrix the consolidated checkpoint quotes.

Reads only. Writes nothing. Touches no database, no oracle, no projection.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent
AUDIT = json.loads(
    (OUT / "issue-5d-batch-actions-1-audit.json").read_text(encoding="utf-8")
)

# ---------------------------------------------------------------------------
# Defect families. `closed` records whether the *discriminating vocabulary* the
# family would need is closed in the source, or ranges over open referents.
#
# METHODOLOGY — duplicate printings. The SRD prints several rules twice: the
# `Playing the Game > Actions` summary table (p9-10) restates all twelve
# glossary actions, and Difficult Terrain appears in both Playing the Game and
# the Rules Glossary. `hits` counts printings; the admission rule requires
# siblings in >= 2 top-level sections, which means two *different rules*, not
# one rule in two places. `distinct` records the de-duplicated rule count where
# it changes the verdict. Two candidate families fail on exactly this:
#   movement_grant  2 hits / 2 sections -> 1 distinct rule (Dash), p9 is its
#                   own summary row. FAILS admission.
#   benefit_loss    2 hits / 2 sections -> 1 distinct rule (Dodge), p10 is its
#                   own summary row. Prone R8 is a prohibition on an act, a
#                   different shape, not a second instance. FAILS admission.
# ---------------------------------------------------------------------------

FAMILIES = {
    # key: (title, corpus hits, top-level sections, closed?)
    "skill_qualified_check": ("Skill-qualified ability check / save", 133, 11, True),
    "outcome_conditional": ("Outcome-conditional effect", 224, 10, True),
    "effect_duration": ("Effect duration and expiry", 109, 10, True),
    "exclusive_choice": ("Exclusive choice among alternatives", 55, 9, False),
    "exit_triggers": ("State-exit trigger enumeration", 38, 7, False),
    "allowance_quantity": ("Per-turn / per-use allowance quantity", 32, 8, True),
    "concentration_req": ("Concentration as a requirement", 32, 6, True),
    "opportunity_attack": ("Opportunity-attack exemption", 23, 5, True),
    "derived_dc": ("DC derived from a score or a roll total", 12, 4, True),
    "unstated_dc": ("Check with no stated DC", 133, 11, True),
    "eligibility": ("Eligibility precondition", 9, 4, False),
    "benefit_loss": ("Benefit-loss predicate (1 distinct rule)", 2, 1, False),
    "third_party_roll": ("Third-party (ally) roll beneficiary", 3, 2, True),
    "sensory_capability": ("Sensory capability (imposed 2/1, reciprocal 1/1)", 3, 3, False),
    "movement_grant": ("Movement grant (1 distinct rule)", 2, 1, False),
    "movement_cost": ("Movement cost — surcharge and expenditure", 20, 5, True),
    "movement_mode_choice": ("Movement-mode substitution / choice", 3, 2, False),
    "condition_counter": ("Condition-level counter, threshold, decrement", 3, 1, False),
    "transformation": ("Transformation and persistent state change", 4, 2, False),
    "attitude_modified": ("Attitude-modified check", 32, 5, False),
    "sequencing": ("Deferred action / cross-turn sequencing", 38, 7, False),
    "movement_interleave": ("Interleaving movement with other effects", 1, 1, False),
}

# ---------------------------------------------------------------------------
# actions-1: every UNRESOLVED span, keyed by the audit's ordinal, to one family.
# ---------------------------------------------------------------------------

ACTIONS_MAP = {
    1: "allowance_quantity",     # one action per turn
    2: "allowance_quantity",     # one attack roll
    3: "allowance_quantity",     # one weapon equip/unequip, and when
    4: "movement_interleave",    # move between attacks
    5: "movement_grant",         # Dash: extra movement equal to Speed
    6: "movement_mode_choice",
    7: "movement_mode_choice",
    8: "movement_mode_choice",
    9: "opportunity_attack",
    10: "effect_duration",       # "until the start of your next turn"
    11: "benefit_loss",          # Incapacitated or Speed 0 revokes the benefit
    12: "exclusive_choice",      # "you do one of the following"
    13: "eligibility",
    14: "eligibility",
    15: "third_party_roll",
    16: "effect_duration",
    17: "eligibility",
    18: "third_party_roll",
    19: "effect_duration",
    20: "skill_qualified_check",  # DC 15 Dexterity (Stealth)
    21: "eligibility",
    22: "sensory_capability",
    23: "outcome_conditional",
    24: "derived_dc",
    25: "exit_triggers",
    26: "attitude_modified",
    27: "derived_dc",
    28: "outcome_conditional",
    29: "eligibility",
    30: "concentration_req",
    31: "concentration_req",
    32: "sequencing",
    33: "exclusive_choice",
    34: "exclusive_choice",
    35: "sequencing",
    36: "concentration_req",
    37: "concentration_req",
    38: "unstated_dc",
    39: "unstated_dc",
}

# ---------------------------------------------------------------------------
# conditions-1: the nine unresolved spans preserved by PR #153, unchanged.
# ---------------------------------------------------------------------------

CONDITIONS = {
    "R1 Blinded 'You can't see'": "sensory_capability",
    "R2 Deafened 'You can't hear'": "sensory_capability",
    "R3 Exhaustion accrual + death threshold": "condition_counter",
    "R4 Exhaustion Long Rest removal + ends at 0": "condition_counter",
    "R5 Grappled surcharge + size waiver": "movement_cost",
    "R6 Petrified transformation": "transformation",
    "R7 Prone movement options + stand-up cost": "movement_cost",
    "R8 Prone 'If your Speed is 0, you can't right yourself'": "benefit_loss",
    "R9 Unconscious 'you remain Prone'": "exit_triggers",
}

# ---------------------------------------------------------------------------
# The proposed schema-2 bundle: only families whose discriminating vocabulary
# is closed in the source. Open-referent families stay UNRESOLVED, deliberately.
# ---------------------------------------------------------------------------

#   * a typed applicability qualifier on ComponentDraft (the structural core),
#     populated by two closed vocabularies: roll outcome and duration window;
#   * new fact families whose own vocabulary is closed;
#   * one RollActor member.
# `benefit_loss` rides the qualifier: its predicates are condition-membership
# (ConditionKind, closed) and Speed == 0 (a SpeedModification value, closed).
SCHEMA_2 = {
    "skill_qualified_check",
    "unstated_dc",
    "derived_dc",
    "outcome_conditional",
    "effect_duration",
    "allowance_quantity",
    "third_party_roll",
    "movement_cost",
    "opportunity_attack",
    "concentration_req",
}

# ---------------------------------------------------------------------------

unresolved = [r for r in AUDIT if r["disposition"] == "unresolved"]
assert len(unresolved) == len(ACTIONS_MAP), (len(unresolved), len(ACTIONS_MAP))

rows: dict[str, dict[str, list]] = defaultdict(lambda: {"actions": [], "conditions": []})
for i, row in enumerate(unresolved, 1):
    rows[ACTIONS_MAP[i]]["actions"].append((i, row["record"], row["text"].strip()))
for label, fam in CONDITIONS.items():
    rows[fam]["conditions"].append(label)

order = sorted(
    rows, key=lambda k: (-(len(rows[k]["actions"]) + len(rows[k]["conditions"])), k)
)

print("=" * 96)
print("CRD Issue 5d — cross-batch unresolved-span matrix (actions-1 x conditions-1)")
print("=" * 96)
print(f"{'family':<34}{'A':>3}{'C':>3}  {'hits':>5}{'sec':>4}  {'closed':<7}{'schema-2':<9}")
print("-" * 96)
for fam in order:
    title, hits, secs, closed = FAMILIES[fam]
    a, c = len(rows[fam]["actions"]), len(rows[fam]["conditions"])
    print(
        f"{title[:33]:<34}{a:>3}{c:>3}  {hits:>5}{secs:>4}  "
        f"{'yes' if closed else 'NO':<7}{'IN' if fam in SCHEMA_2 else '-':<9}"
    )
print("-" * 96)

a_in = sum(len(rows[f]["actions"]) for f in rows if f in SCHEMA_2)
c_in = sum(len(rows[f]["conditions"]) for f in rows if f in SCHEMA_2)
a_tot = sum(len(rows[f]["actions"]) for f in rows)
c_tot = sum(len(rows[f]["conditions"]) for f in rows)
print(f"actions-1    unresolved {a_tot:>3}  closed by schema-2 {a_in:>3}  remaining {a_tot - a_in:>3}")
print(f"conditions-1 unresolved {c_tot:>3}  closed by schema-2 {c_in:>3}  remaining {c_tot - c_in:>3}")
print()
print("Acceptance requires ZERO unresolved spans (accounting.validate_acceptance).")
print(f"actions-1 acceptance-ready after schema-2:    {a_tot - a_in == 0}")
print(f"conditions-1 acceptance-ready after schema-2: {c_tot - c_in == 0}")
print()
print("Families held OUT of schema-2 (discriminating vocabulary is not closed):")
for fam in order:
    if fam not in SCHEMA_2:
        a, c = len(rows[fam]["actions"]), len(rows[fam]["conditions"])
        print(f"  - {FAMILIES[fam][0]:<44} actions {a}, conditions {c}")
