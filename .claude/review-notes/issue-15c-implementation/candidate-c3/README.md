# CRD Issue 15c — semantic candidate C3 (raw review packet)

**Candidate only.** Nothing here is accepted, recorded, minted, published or activated. C3 is not staged or committed, and none of its digests has a `.secrets.baseline` entry: those audited entries are required at commit time.

C3 supersedes the unaccepted C2. It corrects the eight findings and the qualification residue in `../codex-c2-review.md`. The governing scope is #191, body SHA-256 `8225e1b6…57a2`.

C1 and C2 are read, never written. `derive_c3.py` checks their six digests before and after every run.

## Identity

| Part | File | SHA-256 |
| --- | --- | --- |
| **C3-A**: rules, the 38 weapon rows, all 25 tools, the stat-block conventions | `c3a.json` | `aaa5a20fa59c8e4d9dbbd10120aa0b91e968cdb1bcd3616cb8b28632c2e49ff9` |
| **C3-B**: all 336 creature records | `c3b.json` | `bb086082b02e879706218a4ad016110d3c6d5b3f9cc095076adec1cc89095524` |
| **C3-C**: armor and character AC | `c3c.json` | `36be82a04ff2c587af754ed9430dfdfeb9b6053b8073d80add716313069e422b` |
| Concordance | `concordance.json` | `01ec9c36…` |
| Reviewed no-effect instances | `no-effect-review.json` | `252b3b42…` |
| Reuse validation | `reuse-validation.json` | `62e97986…` |
| Rule dispositions | `rules-disposition.json` | `9c0cc873…` |
| Batch map | `transition.json` | `18eb3d24…` |

**Reproduce:** run `venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c3/derive_c3.py` from the repository root.
- Two consecutive runs produced byte-identical output.
- The script ends in `regressions()`, which fails if any reported defect, or one of its cited siblings, reappears.
- C3 owns its `RULES` and `STAT_BLOCK_RULES` tables. It imports only C1's weapon-row and armor-table readers, which the review found correct.

## Findings → disposition

| # | Defect family | C3 correction | Proven by `regressions()` and the sibling scan |
| --- | --- | --- | --- |
| F1 | Timing owner | Every rider duration names its owner: `turn_of` is `target` when the source says "its next turn" and `source` when it says "the X's next turn". The start or end edge is kept. The shape is declared new (see "Reuse"), not a misused `effect_duration`. | Thundercloud, Trash Lob and Gouge are `target`; Poisonous Spittle is `source`. A source-owned possessor must name the block's own creature, or it becomes `unresolved` (0 found). `turn_of` is one closed vocabulary: `source` (the creature making the attack or using the entry or weapon), `target` (the creature affected) and `subject` (the creature a self-directed rule is about). Across all riders: 24 `source`, 7 `target`, and 2 rider saves that are `target`. |
| F2 | Target predicates | "can see" becomes `requires_source_sees_target`, and the save is conditional on a named visibility prerequisite. Area origins ("originating from", "centered on a point … can see") are typed. | Guardian Naga, Satyr and Constrictor are covered, plus 41 sight predicates in total (target or area point). The other **43** phrasings (grappled-by, type exclusions, willing, Prone, swallow capacity) are kept verbatim as conditional residue; none is consumed silently. |
| F3 | Multiattack | Each Multiattack is parsed as alternatives (made of parts) plus replacements. A replacement records its quantifier (`one`, `two`, `any` or `the X`) and the options it substitutes. Each **selectable composition** is certified separately. An unavailable optional substitution refuses only that substitution. | Guardian Naga replaces `any`; Dragon Turtle's Tail is present; Barbed Devil has two alternatives; Young Brass Dragon's Sleep Breath selection is not executable; Adult Black Dragon's base Rend ×3 survives. 240 selections; **30** Multiattacks keep a certified base composition beside an unavailable substitution. "In any combination" alternatives are certified **per option** (`certified_options`): a supported option stays selectable when a sibling option is conditional. Composition residue is 0. |
| F4 | Indirect contributors | Certification no longer depends on keywords. A trait counts as "no roster effect" only if it is on a **reviewed allowlist**, each name with its reason. The allowlist is pinned by **text**, not just by name: every instance's normalized text (71 in total, listed in `no-effect-review.json`) was read, and the build fails if any instance is added or changed. Swoop, which drops a grappled creature, was moved to the named deferrals. Every other untyped entry blocks every roll it could touch. A standing condition grant ("has the Invisible condition.") maps through G1's typed condition facts. Target-side blockers (rolls *against* the creature, and its own saves) are recorded per creature. | Wind Swipe is blocked; the Invisible Stalker has target-side blockers; 84 creatures carry them. Unreviewed entries: 0. |
| F5 | Fixed versus parameterized | Every record carries the ordinary defensive profile: sizes, the six scores and saves, defenses, and verbatim residue. Parameterized values are quote-verified `parameters` beside it. Assessed entries are parsed like any other and anchored to the accepted `actions`/`bonus_actions` components. | Avatar of Death keeps its Poison immunity. Animated Object keeps its Charmed immunity. Animated Object, Giant Insect and Draconic Spirit have anchored entries and six abilities. |
| F6 | Parser-driven exclusions | **Ghast/Ghoul:** the paralysis rider is a typed rider save with its type exclusion. **Caster-referenced values** (Fell Glare, Venomous Spew, the summon attack bonuses) are **missing inputs**, not spellcasting. **Multiattack:** alternative and repeated-use phrasings ("uses X twice", "or uses …") are parsed. **Spellcasting** is detected by meaning ("casts the _X_ spell"). | The Ghast and Ghoul riders are present. Fell Glare is a save effect whose reason is a missing input. |
| F7 | Tinker's Tools option | Utilize text is split on `(DC N)` boundaries, and the reconstruction is asserted to equal the source line. | "Assemble a Tiny item composed of scrap, which falls apart in 1 minute" (DC 20) |
| F8 | Native option identity | The option identity sits **beside** the fact: `option.semantic_key` is the `ComponentOption` grain, and the fact is the accepted `ability_check` payload, unchanged. | `reuse-validation.json`: **529** reused-family payloads parse with the accepted `fact_from_payload`, with **0** failures. That covers `ability_check` 34, `advantage` 65, `condition_effect` 61, `creature_defense` 331 and `damage` 38. No `option_key` appears in any fact. |
| — | Concordance | **429** attack-roll lines across all four files: 323 in Monsters, 100 in Animals, 5 in Spells and 1 in Magic Items. Of these, 423 are generic and 6 belong to assessed creatures. All 429 are parsed. | Asserted |

The same validator also caught C2's typed contributors carrying `applies_when` *inside* `advantage` payloads, a sibling of F8. In C3 the accepted payload sits under `effects` and its predicate beside it.

## Qualification residue

`rules-disposition.json` gives a disposition for all **58** hand-authored rules, checked against their full source sentences: 46 `RULES` against C1/C2, 8 `STAT_BLOCK_RULES` against C2, and 4 armor rules against C1-C/C2-C. 28 are unchanged and 30 are qualified. The residue the review named:

| Rule | C3 home |
| --- | --- |
| **Light** | `trigger: attack_action_on_own_turn`, `first_attack: with_a_light_weapon`, `when: later_on_the_same_turn`, `optional` |
| **Graze** | `increase: only_by_increasing_the_ability_modifier`, `trigger: miss_creature`, `optional` |
| **Armor training** (C3-C) | `applies_when: the wearer lacks training with the worn armor's category`. Trained armor causes no penalty. |
| **Cobbler's Tools** | `option.effect_on_success` on the native option: the wearer's next Dexterity (Acrobatics) check has Advantage (accepted `advantage` payload, `next_qualifying_roll`) |
| Other masteries | Each states `optional` and its precise trigger: `hit_melee_attack_roll`, `hit_creature`, `hit_and_damage` or `miss_creature`. Sap and Vex give their effect with an explicit `applies_to` and a duration owner. |

**Code-owned procedures.** These are source-bound and certified against the components that govern them, as already pinned in `pipeline/rpg/capability.py` for checks:

- the modifier formula;
- Advantage/Disadvantage cancellation;
- Expertise doubling;
- total ≥ target;
- the order damage modifiers apply in;
- Multiattack selection: certifying the chosen composition from the typed parts.

Every number is typed: the crit multiplier, half-damage rounding, death-save thresholds and DCs. No retained prose becomes executable authority.

## Coverage

| Class | Entries | Meaning |
| --- | --- | --- |
| supported | 459 | A bounded shape, fully typed |
| conditional | 591 | Typed, with an exact named prerequisite or verbatim predicate |
| deferred | 164 | Named individually: spellcasting (109), reactions (21), and named mechanics |
| no roster effect | 163 | On the reviewed allowlist, with pinned texts |

**Executable once accepted** means a block-level rollup with no blocker, and it still needs the shared position and actor-turn state:

| Entry kind | Executable |
| --- | --- |
| attacks | 205 of 429 |
| Multiattacks | 89 of 181 |
| Multiattack selections | 90 of 240 |
| save effects | **0** |

Every save effect carries a visibility, area, timing or Recharge prerequisite, so none is executable yet.

## Individually assessed creatures

- **Giant Fly:** fixed.
- **Parameterized (5):** Avatar of Death, Animated Object, Otherworldly Steed, Giant Insect, Draconic Spirit.
  - Each keeps its full fixed profile and anchored entries.
  - Each parameter is quote-verified on its line.
  - Each formula needs inputs that the summon, caster or summoner records: spell level, form, the caster's attack modifier and save DC, or the summoner's HP, PB and identity.
  - No spell is cast or upcast.
- **Conditional (4):** Half-Dragon, Archmage, Rakshasa, Vampire Familiar.
  - Each qualified term is an explicit `{"conditional": …}` member.
  - Each term carries its selection or predicate.
  - The other fields of these records are unaffected.

**Vampire Familiar: proposed relation, held, not implemented.** The proposal is the smallest typed addition:

- **Field:** a single `vampire_master` SubjectReference on the familiar's `CreatureState`.
- **Validation:** the referenced creature exists in the same story. The relation is never inferred from summoner or controller.
- **For Codex to confirm:** whether "its vampire master" means a creature whose template is `monsters.vampires.vampire`. That reading is an **interpretation**, not settled.
- **Effect:** it governs only the familiar's Charmed-immunity determination. If the relation is absent, only that determination refuses.

The proposal itself needs semantic acceptance. A permanent product exclusion, or a broader relationship or lifecycle policy, would be a new Owner Decision. **None is requested here.**

## Reuse, new families, schema delta

- **Reused unchanged and validated:** `damage`, `ability_check`, `condition_effect`, `advantage`, `effect_duration` (unused in C3), `creature_defense`.
- **Declared new (schema 19):** the C3-A, C3-C and stat-block rule families (`new_family_payloads` in `reuse-validation.json`).
- **Declared new (creature entries):** the per-entry shapes, namely attack, save effect, rider save, Multiattack alternatives and replacements and selections, usage, contributor wrapper and parameters.
- **Declared new (timing):** the local `{until, turn_of, turn}` turn boundary. The accepted `effect_duration.whose` is subject-relative and cannot name the other participant's clock, so the boundary is not forced into it.
- **Native option grain:** each tool Utilize option is a `ComponentOption` whose `semantic_key` and text are given, holding an unchanged `ability_check` fact. The Cobbler's effect rides on the option.
- **Handling:** as in G1, every component that receives a fact flips from `prose_bound` to `mixed`.
- **Tool addressing and variants:** unchanged from C2. The validation repair and the variant field are held 2b seam changes.

## Minimum transition (re-assessed, not run)

The facts still touch **7 of 24** accepted batches:

| Batch | Parts |
| --- | --- |
| equipment | A, C |
| checks-actions-rests | A, C |
| combat-damage-breaking | A |
| monsters | A, B |
| animals | B |
| spell-descriptions | B |
| magic-items | B |

C3 changed content within those batches but added none. The other 17 carry over and would be proved byte-identical.

**Minimum work:**
1. Add schema 19, with an 18→19 lift.
2. Regenerate those seven batch proposals against the isolated release store, with a script proving each minted fact equals the reviewed C3 content.
3. Produce one simulated-receipt preview.
4. Codex native review.
5. Owner acceptance of the exact native identity.
6. Record it.

The cost estimate is still Claude's own, not validated. **None of this has been prepared.**

## Holds and prerequisites

- **Dependent implementation is held.** That covers weapons, masteries, the zero-HP lifecycle, initiative, tools, difficulty checks, saves, creature attacks and targets, and character AC. It stays held until Codex review, native minting and Owner acceptance of the exact native identity.
- **Shared prerequisites, named per entry.** Each is held work; none is decided here:
  - explicit position;
  - visibility state;
  - actor-turn and elapsed-time authority;
  - recorded current form;
  - in-lair and sunlight state;
  - the GameMaster's recorded choices (damage notation, Legendary Resistance, Half-Dragon origin);
  - caster and summoner inputs.
- **The manifest in `eb60d9f`** still lists monster stat-block actions as excluded. That is superseded by #191 and is to be revised in the held implementation.
