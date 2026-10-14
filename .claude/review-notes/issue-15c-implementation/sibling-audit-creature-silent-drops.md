# CRD Issue 15c — sibling audit: printed creature mechanics silently dropped

**Trigger.** `codex-c7-recert-coverage-review.md` P1: Allosaurus Claws ran while its typed clauses were ignored. The narrow fix (clauses) turned up siblings of the same family in two review rounds: untyped entry mechanics, then target-side traits. So the family was audited as a whole (13 October 2026).

**Defect family.** A creature mechanic the source prints is not executed, yet the operation runs as though it had none.

| Sibling structure inspected | Finding | Disposition | Regression coverage |
| --- | --- | --- | --- |
| Same-entry typed `Clause*` facts on attack entries | 107 executing entries ignored them | **patched** (`b082262`): `creature_clauses.plan` executes the 10 C5-positive shapes and refuses every other clause before any die | `test_creature_clauses.py` |
| `Clause*` facts on save-effect entries | none C5-positive; all ignored | **patched** (`6526674`): `creature_effects._fact` refuses any clause | `test_creature_effects.py` (unchanged green), roster harness |
| Untyped entry mechanics (Balor no-Reactions, burning, Hit Point maximum loss, armor degradation, lycanthrope form) | invisible to typed facts; entries ran | **patched** (`bd5ef82`): code-owned roster (C5 Owner packet Decision 4) | `test_creature_roster.py` |
| A creature's own standing traits with non-Advantage effects | skipped | **patched** (`3741c60`): refuse | `test_creature_roster.py`, `test_creature_clauses.py` |
| A **target** creature's traits on attacks against it (Steam Mephit Blurred Form) | ignored by weapon and creature attacks | **patched** (`3741c60`): `attacks.creature_traits` on both sides | `test_blurred_form_hinders_attacks_against_the_mephit` |
| A creature's own traits on its saves | every one refused (safe, but C5-positive Berserker saves blocked) | **patched** (`10ddbfd`): own Advantage/Disadvantage under an evaluable circumstance executes; the rest refuse | `test_bloodied.py` |
| Multiattack optional uses of another entry; replacements | alternative skipped wholesale; replacements ignored | **patched** (`6526674`, `3741c60`) | `test_creature_clauses.py` |
| Hit-effect conditional damage (Advantage, Bloodied) | refused | **patched** (`3741c60`, `10ddbfd`) | `test_creature_clauses.py`, `test_bloodied.py` |
| Linked conditions (Grappled→Restrained) | refused | **patched** (`ae011bb`) per Codex classification | `test_linked_conditions.py`, E2E |
| Swallowing, engulfing, possession, teleport, lycanthropy, Reactions, legendary actions, spellcasting | not executed | **out of scope**: refused by the roster and by entry-section checks | roster harness (`every other entry refuses`) |
| Allegiance (who is an enemy or ally) | GameMaster identification | **owner decision needed** only if code should derive it; recorded as a residue | `bystanders.py` docstring |

**Positions now (`test_creature_roster.py`):**
- every C5 capability-positive attack and save-effect entry, and every Multiattack selection, passes the production preflight;
- every entry outside the roster refuses;
- no boundary remains.
