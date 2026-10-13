# CRD Issue 15c — raw candidate C8 (revision r2): target creature types

**Revision r2** applies `../codex-c8-raw-review.md`:
- profile handling is preserved;
- the Vampire is split into base, bat and mist;
- the Find Familiar source-qualified type choice is consolidated in, per the parent's direction.

The 345 base type facts are byte-identical to r1. The reviewed r1 artifacts are preserved unchanged in `r1/`: `c8.json` `81991739…`, correspondence `5cd59009…`, inventory `c49b6a58…`, validation `d6d9b42e…`.

**RAW CANDIDATE ONLY.** Nothing here is accepted, minted, recorded or published, and no schema or `src` code is changed. **C7 stays the accepted authority**: `srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json`, `2853f30a…f373`, digest-checked and only read.

**Why** (`../codex-creature-type-boundary-classification.md`, adopted by the parent):
- Ghast and Ghoul Claw's typed rider saves exclude Undead (and, for the Ghoul, elf) targets.
- No accepted fact assigns any target its creature type.
- The two attacks remain promised, held and incomplete.
- `BOUNDARIES` is an interim disclosure. It is neither coverage nor an exclusion.

| File | SHA-256 |
| --- | --- |
| `c8.json` (r2) | `7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628` |
| `correspondence.json` (346 rows) | `43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24` |
| `inventory.json` | `3f05591efa78656132db3a179f174b560ca3e8f3d3ebfd525e56b400e87ce55d` |
| `validation.json` | `c4e1c3ecbaf162cac3fb8f30e4625fca46ec8aa2084a000280168d0b9fb03e61` |

**Changed from r1:**
- the `schema` metadata (both families; handling preserved);
- `forms` (the Vampire split);
- `held` (the Vampire, departures, Challenge Rating 0 forms);
- the new `source_type_choices`.

In the correspondence, the Vampire row's `form` changes (`held` → `bat:kept;mist:held_form_state`) and one row is added. No other row changes.

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

## Source-qualified type choice: Find Familiar (r2, family `summoned_creature_type`)

| Record / component | Source anchor | Fact |
| --- | --- | --- |
| `spells.find_familiar/effect`: prose-bound, becomes `mixed` | `spells.md:2290` "…though it is a Celestial, Fey, or Fiend (your choice) instead of a Beast" | `type_choice` celestial/fey/fiend, `instead_of` beast, `forms`: the eleven named animal profiles (Bat, Cat, Frog, Hawk, Lizard, Octopus, Owl, Rat, Raven, Spider, Weasel), each a Beast in C8 |

**Scope:** it is target authority for an existing familiar: a creature whose `summon.source` is this spell, a named form, and a stored type within the choice. It is not casting, creation, lifecycle or an attack grant. No template's fixed type is generically overridden.

**Held:** "another Beast that has a Challenge Rating of 0" (no typed Challenge Rating).

**Cost:** it lands in the already changed `spell-descriptions` batch, 4 → 5 components. No new batch.

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
| **Kept (I2)** | Doppelganger, Imp, Mimic, Night Hag, Oni, Quasit, Succubus (Shape-Shift), Werebear, Wereboar, Wererat, Weretiger, Werewolf; **Vampire bat form** (r2): `monsters-A-Z.md:17725`, "Its game statistics, other than its size and Speed, are unchanged" |
| **Another stat block** | Incubus's Succubus Form, Succubus's Incubus Form: that template's own type applies |
| **Held: form state only** (r2) | Vampire mist form (`:17726`). The paragraph lists specific changes (no actions or speech, weightless, Resistance to all damage) and states nothing about the type. `CreatureState` records no current form. The base Vampire (Undead, direct `:17626`) and its bat form are **not** held; a vampire target is read by its recorded template. |

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
2. **A Vampire in mist form.** The form state is not represented and the mist type is unstated. No refusal is claimed, since nothing records or executes the form. The base and bat targets are not held.
3. **A stored `creature_type` departing from a fixed template type without a represented source.** An unvalidated stored type is not trusted. A familiar's chosen type is now represented by the Find Familiar source choice, for its named forms.
   - **Familiar in another form:** a Challenge Rating 0 Beast form other than the eleven named stays held (no typed Challenge Rating).
4. **Shapechange, Polymorph and other form-changing spells.** General spell execution is excluded; they refuse as unexecuted active effects. Wild Shape keeps a character's type (`classes.md:3505`).

No GameMaster type input is proposed. A species input for creatures whose stat block leaves species open is **proposed separately for the Owner** (`owner-proposal-creature-species.md`). It is not approved and not part of this candidate.

## Affected batches and replay cost (`inventory.json`)

| Batch | Facts = components touched | Why |
| --- | --- | --- |
| monsters | 235 | every monster profile is a possible Claw target |
| animals | 95 | every animal profile |
| character-origins-feats | 9 | species types (characters as targets) |
| spell-descriptions | 5 | 4 creatures a spell creates, plus the Find Familiar source choice (r2) |
| magic-items | 2 | creatures a magic item creates |

**Untouched:** 19 of the 24 batches, whose ordered records and receipts are reused byte for byte.

**Native replay cost**, after raw clearance:
- 5 proposals rebuilt and re-declared at schema 21;
- 346 provenance claims and their expected rules (345 base facts plus one source choice);
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
