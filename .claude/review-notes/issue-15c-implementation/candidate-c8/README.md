# CRD Issue 15c — raw candidate C8: target creature types

**RAW CANDIDATE ONLY.** Nothing here is accepted, minted, recorded or published, and no schema or `src` code is changed. **C7 stays the accepted authority**: `srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json`, `2853f30a…f373`, digest-checked and only read.

**Why** (`../codex-creature-type-boundary-classification.md`, adopted by the parent):
- Ghast and Ghoul Claw's typed rider saves exclude Undead (and, for the Ghoul, elf) targets.
- No accepted fact assigns any target its creature type.
- The two attacks remain promised, held and incomplete.
- `BOUNDARIES` is an interim disclosure. It is neither coverage nor an exclusion.

| File | SHA-256 |
| --- | --- |
| `c8.json` | `8199173955d5543665b03c2adbbff52554d6d50b4e6fba055909a9fb83720cd6` |
| `correspondence.json` (345 rows) | `5cd590097fc59d29bf6e441e83a7830e973220b9da9861e4b296e6448bb292b0` |
| `inventory.json` | `c49b6a58b102e7d3e4079c735e003a4712455cc89cf048f1cb5bda181a0e6320` |
| `validation.json` | `d6d9b42ea5f74a48fd69c55c53e8447b6d6d4d1b8467a83777f1dd601c8628a0` |

**Reproduce** (two runs are byte-identical):
```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c8/derive_c8.py
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c8/validate_c8.py
```

## Content: 345 `creature_type` facts (proposed family, `schema-21-delta.md`)

| Group | Records | Component | Source anchor | Basis |
| --- | --- | --- | --- | --- |
| Creature templates | 336: 235 monsters, 95 animals, 4 spell creatures, 2 magic-item creatures. That is every record with a `creature_size` fact, so every creature a Claw can target. | the profile component already holding `creature_size` | the stat block's italic line, for example `monsters-A-Z.md` "_Medium Undead, Chaotic Evil_" (`monsters.md:7`: "its size, creature type … and alignment") | 328 direct |
| Swarms | 7 (six animal swarms; Swarm of Crawling Claws) | as above | "_Medium Swarm of Tiny Beasts, …_" | **I1** |
| Find Steed's steed | 1 | as above | "_Large Celestial, Fey, or Fiend (Your Choice), Neutral_" (`spells.md:2323`) | direct: `type_choice` |
| Species | 9 (all accepted species) | the existing prose-bound `creature_type` component | "**Creature Type:** Humanoid" on each species page (`character-origins.md:99…327`) | direct |

**What each row carries:**
- the quote, which matches its cited line exactly;
- the existing record and component identity;
- the spans that component's existing facts already claim;
- the one batch those spans were accepted in.

**The type only.**
- Descriptive tags ("(Devil)", "(Dinosaur)", "(Wizard)") stay prose.
- `monsters.md:65–67` says tags "have no rules of their own".
- **Nothing in the candidate treats a missing tag as "not an elf".**

## Interpretations (for independent review)

- **I1 — a swarm's type is its members' type.**
  - Applies to "Swarm of Tiny Beasts" → Beast and "Swarm of Tiny Undead" → Undead.
  - No glossary rule names a swarm's type. The header line is the type entry (`monsters.md:7`).
- **I2 — a Shape-Shift that keeps "game statistics … the same in each form" keeps the type.**
  - Applies to 12 templates (see Forms below).
  - **Evidence:**
    - the type is a stat-block entry (`monsters.md:7`);
    - Wild Shape, which replaces game statistics, keeps the type explicitly (`classes.md:3505`).

## Forms, classified one by one (`c8.json` → `forms`)

| Disposition | Templates |
| --- | --- |
| **Kept (I2)** | Doppelganger, Imp, Mimic, Night Hag, Oni, Quasit, Succubus (Shape-Shift), Werebear, Wereboar, Wererat, Weretiger, Werewolf |
| **Another stat block** | Incubus's Succubus Form, Succubus's Incubus Form: that template's own type applies |
| **Held** | Vampire: its bat or mist form's type is not stated (`monsters-A-Z.md:17724`) and the form is not represented |

## Held (surfaced, not decided)

1. **Ghoul Claw against a creature that is not Undead.**
   - **The rule:** the exclusion includes an *elf* (`monsters-A-Z.md:6919`, "isn't an Undead or elf").
   - **What does and doesn't establish Elf status:**
     - A character's elf status is its validated exact `character_origins.elf` species identity. No new fact is needed.
     - A creature instance records no species.
     - Its template's header lists type and descriptive tags (`monsters.md:7, 65–67`), but no source statement makes the tags a statement of species.
     - Per the governing instruction, an absent tag is not evidence of not being an elf.
   - **Effect:** refuses before any die.
   - **Open point:** whether any source or state can establish a creature's elf status.
   - **Not affected:**
     - Ghast against any typed target;
     - Ghoul against characters;
     - Ghoul against Undead creatures, where Undead suppresses the rider conclusively.
2. **A Vampire target.** Form-dependent, as in Forms.
3. **A stored `creature_type` departing from a fixed template type** (a familiar's chosen type). The departure's source is not represented, and an unvalidated stored type is not trusted.
4. **Shapechange, Polymorph and other form-changing spells.** General spell execution is excluded; they refuse as unexecuted active effects. Wild Shape keeps a character's type (`classes.md:3505`).

No GameMaster type or species input is proposed.

## Affected batches and replay cost (`inventory.json`)

| Batch | Facts = components touched | Why |
| --- | --- | --- |
| monsters | 235 | every monster profile is a possible Claw target |
| animals | 95 | every animal profile |
| character-origins-feats | 9 | species types (characters as targets) |
| spell-descriptions | 4 | creatures a spell creates |
| magic-items | 2 | creatures a magic item creates |

**Untouched:** 19 of the 24 batches, whose ordered records and receipts are reused byte for byte.

**Native replay cost**, after raw clearance:
- 5 proposals rebuilt and re-declared at schema 21;
- 345 provenance claims and their expected rules;
- 5 batches excised and re-accepted in anchor order;
- one `20→21` lift;
- private-store round trips;
- a pinned packet.

**Comparison with C7:** C7's two batches took about 12 minutes per build, dominated by full-oracle validation. C8 also rebuilds the two largest creature proposals (monsters, animals), so expect a longer build; the exact time is measured at the native stage.

**Later, after acceptance:**
- the local successor recording;
- recertification (`creature_attack` gains the type components per subject);
- the execution in `schema-21-delta.md`, held until then.

## Gate

Stop here for Codex raw review. After clearance, the native stage makes only:
- a private SIMULATED preview;
- a pinned acceptance packet, in an isolated worktree.

There is no real recording and no type-dependent execution until the Owner accepts that exact packet.
