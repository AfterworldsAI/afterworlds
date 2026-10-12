# CRD Issue 15c — semantic candidate C1 (review packet)

**This is a candidate only.** Nothing in it has been accepted, recorded, committed, minted, published or activated. The accepted G1 oracle (`2ccbaeba…1258`) is read only; every script checks its digest. Scope approval of #191 does not accept this content.

## What is asked, and of whom

1. **Codex: independent review.**
   - The content of the three parts below.
   - The classification rule in `../gap-inventory.md`: printed numbers and per-record data are typed; universal arithmetic and sequencing are adapter procedure, certified against each procedure's governing component.
   - The default reading of the excluded monster stat-block actions.
2. **The Owner: explicit semantic acceptance, per part.** The parts are independent, so accepting one unblocks the work it holds.

| Part | File (SHA-256) | Content | Holds |
| --- | --- | --- | --- |
| **C1-A** | `candidate-c1.json` (`9e9645e8…3d38`) | 223 facts on accepted components (derived by `derive_candidate.py`); see C1-A detail below | Weapon attacks and damage, all 8 masteries, the zero-HP lifecycle, initiative, tool checks, GameMaster-difficulty checks |
| **C1-B** | `candidate-c1b.json` (`fbabf91a…9e8e`) | Creature defensive profile for 326 of 336 creature records; see C1-B detail below | Every attack or mastery whose target is a creature |
| **C1-C** | `candidate-c1c.json` (`82cfb6b9…d92f`) | 13 armor-class formulas plus the Shield bonus; base AC 10 + Dex; one base AC only; armor-training Disadvantage on Str/Dex D20 Tests; the Shield training requirement | Every attack whose target is a character; Str/Dex tests by a character wearing armor |

**C1-A detail.**
- **38 weapon rows** (source-derived):
  - Melee/Ranged class;
  - damage, using the accepted `damage` family unchanged;
  - 70 `weapon_property` facts with their printed parameters (range, versatile dice, ammunition type).
- **13 record-backed tools:**
  - each tool's ability;
  - 18 Utilize DCs, using the accepted `ability_check` family as component options.
- **Rules (hand-authored, each quote checked against its cited line):**
  - the Typical DC table;
  - attack-roll abilities;
  - natural 20 and natural 1 on attacks;
  - crit damage;
  - the damage-roll rule;
  - Initiative;
  - weapon-property rules;
  - the eight mastery effects, reusing `advantage`, `effect_duration` and `condition_effect` where they fit;
  - the zero-HP lifecycle: the bound, monster death with its GameMaster exception, Hit Point maximum 0, massive damage, falling Unconscious, death saves and their natural rolls, damage at 0 HP, stabilization, Stable and its 1d4-hour recovery, the knockout alternative and Short Rest length.

**C1-B detail.**
- **Typed fields:** AC, HP and HP dice (reusing the accepted `creature_defense` family, which G1 never populated); the printed size or size choice; the six ability scores with the printed SAVE modifiers; damage resistances, vulnerabilities and immunities; condition immunities.
- **Census:** a two-sided census against `monsters-A-Z.md` and `animals.md` matched every stat block. Nothing is invented.
- **Refused (not typed), each needing a choice or condition the roster does not record:**
  - Half-Dragon (chosen resistance);
  - Archmage (Mind Blank);
  - Rakshasa (Bless-conditional vulnerability);
  - Vampire Familiar (master exception).
- **Not matched:** six creature records whose stat blocks are printed in Spells or Magic Items and scale with level (Animated Object, Otherworldly Steed, Giant Insect, Draconic Spirit, Giant Fly, Avatar of Death). They are untyped, so they refuse as targets.

The weapon identities, categories and mastery assignments are the accepted G1 facts, used unchanged. Mastery eligibility uses the accepted `weapon_mastery` progression counts and class features.

## Provenance and determinism

- Each fact carries `source` (pinned Markdown file, line, and the row or an exact quote).
- The scripts refuse to emit if any of these holds:
  - a quote is not on its line;
  - a fact names a component the accepted authority lacks;
  - the weapon count differs from 38.
- Re-running each script reproduces the hashes above byte for byte.
- No PDF cross-check was run for C1. G1's `source_catalogue_check.py` already cross-checked the same Weapons table against the PDF. That catalogue is the source of the rows here.

## Scope boundary for Codex to confirm before the Owner sees it

**Monster stat-block actions are not "attacks using the 38 SRD weapons".** They print their own to-hit and damage. The default reading leaves them excluded: they refuse visibly, and no part of C1 types them.

The consequence is that a character reaches 0 HP only through weapon attacks made by a character or a creature that wields an SRD weapon. The zero-HP lifecycle is still fully exercised, because character-on-character and character-on-creature attacks, and damage at 0 HP, all qualify. If the Owner wants monster actions in scope, that is a scope change and a further candidate part.

## From content acceptance to recorded authority (the cost, stated before it is run)

The Owner previously accepted an exact native proposal identity (G1: `8a8a737b…`). C1 is offered here as exact content with exact hashes. Minting it natively means all of the following:

- Schema 19 in `representation.py`, `projection.py` and `schema_lift.py`, with the new families and vocabularies and a registered 18→19 lift proving every accepted payload byte-identical.
- Regenerated proposals for each affected batch (Equipment, Playing the Game, Rules Glossary, Monsters, Animals) against the isolated release store `../../../../g1-work/rel`, following `issue-2b-g1-candidate/scripts`.
- A successor oracle and its supersession entry.

**Estimated cost:** several engineering days, five batch generators, and a re-review of each regenerated proposal.

**Proposed sequence:**

1. Codex review and Owner acceptance of this content.
2. Native minting, with a check script proving that the minted facts equal the accepted content exactly.
3. Recording.

If the Owner instead requires acceptance of the minted native identity, step 2 runs first, and the hashes above become the review baseline the minted proposal must reproduce. **This is a process choice for Codex and the Owner; no semantic question depends on it.**

## What is not held

Independent work proceeds now, with every held operation refusing visibly:

- production wiring;
- the capability manifest and certification;
- the refusal taxonomy;
- player-roll refusal;
- the prompt;
- checks and saves against already-typed fixed-DC identities.

See `../status.md`.
