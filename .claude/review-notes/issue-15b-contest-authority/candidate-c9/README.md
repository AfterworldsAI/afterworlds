# CRD Issue 15b — raw candidate C9 (revision r2): creature skills

**Revision r2** applies Codex's independent source check. That check confirmed all 336 profiles, 216 Skills entries, 429 bonuses and 120 empty lists, and found one qualification: a printed total is for the skill's usual ability pairing.
- Each entry now records that ability explicitly.
- S3 is qualified.
- An atypical pairing is held.

The printed totals are unchanged. r1 (`c9.json` `aa389aff…`, `validation.json` `993cf646…`) stays in history at `66f0deb4`.

**This is a raw candidate only.** Nothing here is accepted, minted, recorded or published, and no `src` code changes on this branch. **C8 stays the accepted authority**: `srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json`, `ead7fa9d…2d0d`. It is digest-checked and only read.

**Why C9 is needed.** A generic contest participant may be any creature of the story, making any ability check (ADR-015b Group 17, proposed). C8 types no creature skill. Each profile's printed Skills entry is the only authority for its skill bonuses. Without a typed fact, two cases cannot be told apart:
- a skill the creature is not proficient in;
- a skill whose data was never read.

| File | SHA-256 |
| --- | --- |
| `c9.json` (r2) | `a3d40545d1a0ea1b4a1e24a1e3831b12b972f50ea26981b0edf1b578fd0648db` |
| `correspondence.json` (336 rows) | `285ee055374edbcf75383b00e755aca2daa2d5f0363f57b6af368a27efeaf1e4` |
| `inventory.json` | `daab6ac2acd13d3b273995baff64e4ba8e0242f9817e7edf62b4965ea8de3d9b` |
| `validation.json` (19 checks, all true) | `ce47394016eb69626cdce325b596b6165e56c8791bf361668a93fb3dc0ad9532` |
| `schema-22-delta.md` | the proposed family, the consumer contract, why the schema is not in this PR, and the native-stage cost |

**Reproduce.** Run from the repository root. Two runs produce byte-identical output.

```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15b-contest-authority/candidate-c9/derive_c9.py
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15b-contest-authority/candidate-c9/validate_c9.py
```

## Content: 336 `creature_skills` facts (proposed family, schema 22)

Each fact is appended to the profile component that already holds the C8 `creature_size` and `creature_type` facts. That covers every accepted creature profile, so every creature a contest can name.

| Group | Profiles | With printed Skills | Positively empty |
| --- | --- | --- | --- |
| monsters (`monsters-A-Z.md`) | 235 | 154 | 81 |
| animals (`animals.md`) | 95 | 62 | 33 |
| spell creatures (`spells.md`) | 4 | 0 | 4 |
| magic-item creatures (`magic-items.md`) | 2 | 0 | 2 |
| **Total** | **336** | **216** | **120** |

There are 429 skill entries in all. A fact reads, for example:

```
{"family": "creature_skills", "skills": [{"ability": "dexterity", "bonus": 6, "skill": "stealth"}]}
```

Entries are sorted by skill and distinct. `bonus` is the printed total, and `ability` is the skill's usual ability (`SKILL_ABILITY`): the one pairing the total is printed for.

**Completeness.** The validator re-reads every source line independently and proves the following:

| Check | What it proves |
| --- | --- |
| Extent | Each profile's stat block runs from its `**AC**` line to its next heading (Traits/Actions or the next entry) and contains exactly one `**AC**` line |
| Bijection | All 216 `**Skills**` lines in the four template files map one-to-one onto 216 profiles. No profile holds two, and no extent contains another profile's line |
| Absence | Each of the 120 empty lists has no Skills line within its extent. Each cites its Senses line, where the details sit |
| No qualifiers | Every Skills line has the plain `Name ±N, …` shape: no parenthetical, condition, `or`, `plus` or PB parameter (so "preserve qualifiers" has nothing to preserve). Spell and magic-item profiles print no Skills entry at all |
| C8 alignment | Claim spans are the component's existing C8 claims, all in the one accepted batch per profile. The C8 correspondence (`43589153…`) supplies each profile's anchor line |
| Schema 21 | It cannot carry the family: `creature_skills` is not a `FactFamily` |

## Interpretations (for independent review)

- **S1: an absent Skills entry means proficient in no skill.** This makes the empty list a positive statement.
  - Evidence: `monsters.md`:13 ("If a monster lacks those details, entries for them don't appear."), `monsters.md`:149 ("…skill proficiencies, if any") and `rules-glossary.md`:1353.
  - Claim span: the raw stage lists the component's existing claim spans, as C8 did. The native stage claims the span holding the stat block's details lines, where the entry would appear.
- **S2: forms are carried from C8.**
  - A Shape-Shift that keeps game statistics keeps the Skills entry. So does the bat form.
  - "Another stat block" forms read their own template.
  - The Vampire's mist form stays held.
- **S3 (qualified in r2): the printed total is the complete bonus for the skill used with its usual ability.** It is never decomposed into ability modifier, PB or Expertise, nothing is re-added, and it says nothing about another pairing.
  - The rules permit Strength (Acrobatics) (`playing-the-game.md`:239).
  - The Assassin's Acrobatics +7 (`monsters-A-Z.md`:532) is Dexterity +4 plus 3; its Strength is +0. Reusing +7 for Strength (Acrobatics) would assume a decomposition the stat block does not state.
  - Evidence: `monsters.md`:149, "Other modifiers might apply".
  - Diagnostic only, never written into a fact. Of the 429 entries, 268 equal modifier + PB and 159 equal modifier + 2 × PB. Two fit neither: Giant Frog Stealth +4 (Dex +1, PB +2) and Shambling Mound Stealth +3 (Dex −1, PB +3).

## Held (surfaced, not decided)

- **A listed skill used with an ability other than its usual one.** This is a bounded adapter exclusion, not a claim that the source forbids the pairing. It refuses before any die unless separately supported authority exists. An unlisted skill under a complete list means no proficiency, so any pairing uses that ability's modifier.
- The Vampire's mist form (carried from C8).
- Traits and conditions that change a creature's check, such as Keen Senses, Sunlight Sensitivity, or Disadvantage from a condition. These are not part of the Skills entry. They are existing typed `creature_roll_modifier` and condition facts, and execution must apply or refuse them.
- Form-changing spells, such as Polymorph. General spell execution is excluded, as in C8.

## Affected batches (`inventory.json`)

| Batch | Facts, one per profile component |
| --- | --- |
| monsters | 235 |
| animals | 95 |
| spell-descriptions | 4 |
| magic-items | 2 |

The other 20 accepted batches are untouched.

## Gate

The native SIMULATED preview is built on the local preview branch `codex/issue-15b-c9-schema-preview` @ `002de94d`; see that branch's `issue-15b-c9-native/README.md` and `../README.md`. These steps follow in order:

1. Independent review of the native packet.
2. Owner acceptance of that exact packet.
3. Recording of the C9 successor.
4. Recertification of all 15c operations against the new projection.
5. Contest execution.
