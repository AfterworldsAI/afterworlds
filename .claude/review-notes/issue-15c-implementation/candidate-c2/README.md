# CRD Issue 15c — semantic candidate C2 (review packet)

**Candidate only.** Nothing here is accepted, recorded, minted, published or activated. No acceptance receipt, successor oracle or supersession entry exists. The accepted G1 oracle (`2ccbaeba…1258`) is read only and digest-checked.

**Scope.** C2 is prepared against #191 as updated (body SHA-256 `8225e1b6…57a2`). The Owner approved:

- ordinary monster and animal attacks;
- bounded Multiattack;
- the associated saves and effects;
- repair of the tool-addressing gap and the omitted-source gap;
- individual assessment of conditional creatures.

That approval is scope, not semantic acceptance.

## Identity

| Part | File | SHA-256 | Content |
| --- | --- | --- | --- |
| **C2-A** | `c2a.json` | `a15aab1839d6f86cc1fd4241b30b58dbdf9fa5d51cf2a8abd26ba48798df70d3` | Rules, the 38 weapon rows, all 25 tools, and the stat-block conventions (see C2-A below) |
| **C2-B** | `c2b.json` | `0dd7538f3efd1b63832ba5d1963d175a2f6c0cd7addd19c2ca19cff9114f65ed` | Every one of the 336 accepted creature records, wherever its stat block is printed (see C2-B below) |
| **C2-C** | `c2c.json` | `a21a5e893f8710fa9d109c1d84166571e264197979c98c8a62d89e58d3326f5a` | Armor and character AC. Content is identical to C1-C; only the identifier differs. |
| Concordance | `concordance.json` | `d63a6a3f…` | Hashes, the per-tool table, and the creature census and classification counts |
| Transition | `transition.json` | `e9307d2a…` | The accepted batches a native mint would touch |

**C2-A detail.**
- The rules and the 38 weapon rows are C1-A content, unchanged.
- **All 25 tools:**
  - 13 standalone records and 12 components of the `equipment.tools` section record;
  - each carries `tool_entry` (ability, plus category: artisan's or other);
  - 34 Utilize DCs, using the accepted `ability_check` family as component options;
  - Gaming Set and Musical Instrument also carry their printed variants, each needing a separate proficiency.
- **Stat-block conventions** (`monsters.md`): attack notation, save notation (half damage rounds down), damage notation (average or dice, chosen by the GM), Multiattack, X/Day, Recharge, Recharge after a rest, and Legendary Actions.

**C2-B detail.**
- **Sources:** `monsters-A-Z.md`, `animals.md`, `spells.md` and `magic-items.md`. The census is two-sided: 336 of 336 records matched, and no stat block is unmatched.
- **Typed per creature:** defenses (reusing the accepted `creature_defense` family) and the defensive profile.
- **Every action, bonus action, reaction, legendary action and trait is classified individually.**

C2 is re-derivable with `derive_c2.py` (byte-identical on rerun). It imports C1's weapon, rule and armor derivations unchanged. `transition.py` computes the batch map.

### C1 is superseded, not deleted

C1 (`../candidate/`, parts `9e9645e8…`, `fbabf91a…`, `82cfb6b9…`) is preserved byte for byte as unaccepted review evidence. **Correction:** the C1 files *are* committed, in the local commit `eb60d9f`. That commit makes them review material on the branch, not accepted or recorded authority.

## Supported / conditional / deferred (C2-B entries)

| Class | Count | Meaning |
| --- | --- | --- |
| supported | 445 | Fully typed bounded shape. For an attack this means bonus, reach/range, damage terms and a typed rider. For a save it means one target, DC, damage, typed condition and half-on-success. Multiattack composition is resolved. Still subject to the shared prerequisites below. |
| conditional | 564 | Typed, with an exact qualification that needs named state or a predicate. Each entry lists its own reasons. The recurring reasons: area membership (needs position); Recharge, Legendary or lair timing; a form-only entry (needs current form); an attack whose Advantage is qualified; an untyped rider, stated verbatim; and contributing traits. Magic Resistance, Legendary Resistance, Pack Tactics and Sunlight Sensitivity have typed predicates; the other 57 contributors are named individually. |
| deferred | 147 | Named individually, each with its reason: spellcasting (108, a non-goal), reactions (21, new trigger/response mechanics), and Shape-Shift, Berserk and Coven Magic. |
| no roster effect | 181 | Amphibious, Spider Climb, Flyby, Nimble Escape and similar. |

**Executable once accepted (block-level rollup).** A trait applies to every roll it names in its block. An attack is executable only if no conditional contributor in its own block bears on attack rolls; a Multiattack is executable only if every attack it resolves to is. Under that rule:

- 264 of 423 attacks are executable;
- 82 of 179 Multiattacks are executable;
- 6 of 159 save effects are executable (most are area or Recharge effects).

Each attack records its `blocked_by` list. For example, the Wolf's Bite is blocked by Pack Tactics. Even "executable" entries need the shared position and actor-turn state (below).

**Anchoring.** In the accepted authority, each creature's traits, actions, bonus actions, reactions and legendary actions are separate components, and the stat block's header is its own component. Accordingly:

- each entry is anchored to its section's component (`component_key`);
- defenses and the profile are anchored to the header component (`defense_component_key`);
- every entry has an anchor (0 unanchored; see the concordance).

**Assessed profiles are never flattened.** A conditional field carries an explicit `{"conditional": …}` term, never an empty list. The script asserts this.

Entry kinds: 423 attacks (equal to the source's count of attack-roll lines), 159 bounded save effects, 179 Multiattacks, 32 references to another entry, and 28 special effects. The special effects are staged failures, preamble movement and death or aura triggers; each is named.

### Individually assessed creatures (none dropped)

| Creature | Status | Exact meaning and prerequisite |
| --- | --- | --- |
| Giant Fly | fixed | AC 11, HP 19 (3d10 + 3). The C1 claim that all six such creatures scale with level was **false** and is corrected here. |
| Avatar of Death | parameterized | AC 20. HP is half the summoner's maximum. Its Scythe attack hits automatically. Its Multiattack count is half the summoner's Proficiency Bonus, rounded up. **Needs:** the summoner recorded on its summon origin. |
| Animated Object | parameterized | AC 15. HP and Slam damage depend on its recorded size. The attack bonus is the caster's spell attack modifier. |
| Otherworldly Steed | parameterized | AC 10 + spell level. HP 5 + 10 × spell level. Slam damage is 1d8 + spell level, with its type set by the creature-type choice. Its bonus actions are deferred individually. |
| Giant Insect | parameterized | AC 11 + spell level. HP 30 + 10 per level above 4. Multiattack count is half the spell level. Poison Jab and Web Bolt are typed. Venomous Spew is deferred. |
| Draconic Spirit | parameterized | AC 14 + spell level. HP 50 + 10 per level above 5. Fixed resistances and immunities. Rend is typed. Breath Weapon is deferred. |
| Half-Dragon | conditional | Resistance to the single Draconic Origin type the GM chooses (acid, cold, fire, lightning or poison). The same choice sets Claw's extra damage and the breath type. **Needs:** the creature's recorded `ChoiceRecord` (an existing 2b contract); if it is absent, the affected operations refuse. |
| Archmage | conditional | Immune to Charmed only while under Mind Blank. **Needs:** the creature's recorded active effect `spells.mind_blank` (existing contract). |
| Rakshasa | conditional | Vulnerable to Piercing damage only from a weapon wielded by a creature under Bless. **Needs:** the attacker's recorded active effects (existing contract). |
| Vampire Familiar | conditional | Immune to Charmed except from its vampire master. **Needs:** a recorded master identity. 2b records a summoner/controller, not a master, so a Charmed determination on it refuses until a master relation is recorded. This prerequisite is surfaced, not decided. |

**What every parameterized summon needs.** Each needs the cast level and choices recorded on its summon state. Each also needs the caster's spell attack modifier and spell save DC from recorded authority. This candidate does not type those (general spell execution is a non-goal). Until they are typed and accepted, attacks that use them refuse. Nothing here casts or upcasts a spell.

## Interpretation, schema and addressing delta (for Codex review)

- **Classification rule:** unchanged from C1 (`../gap-inventory.md`).
- **Reused accepted families:** `damage`, `ability_check`, `condition_effect`, `advantage`, `effect_duration`, `creature_defense`.
- **Proposed new schema-19 families:** the C1-A and C1-C families, plus `tool_entry`, `tool_variants`, `creature_attack_notation`, `creature_save_notation`, `damage_notation_option`, `multiattack_rule`, `usage_limit_rule`, `legendary_action_rule` and `creature_defensive_profile`, plus the per-entry creature shapes in `c2b.json`:
  - attack;
  - save effect;
  - Multiattack composition;
  - usage;
  - a contributor predicate (with `save_override`);
  - the parameterized formulas.
- **Handling flips.** As in G1, every component that receives a fact changes from `prose_bound` to `mixed`, and its governing prose is retained under its existing reason. Accepting C2 includes accepting those handling changes.
- **Tool addressing.** `ToolGrant` already records `(record_key, component_key)`. The gap is in 2b validation: `_is_tool` admits only catalogue *members*, so a grant on `equipment.tools/<component>` is refused. Nothing typed distinguished tool components from section components such as `ability`, `craft` and `utilize`.
  - **Repair:** `tool_entry` marks exactly the 25 tools. Validation would then admit `(equipment.tools, c)` exactly when `c` carries `tool_entry`.
  - **Variants:** variant tools need a variant identity on the grant, either a new `ToolGrant.variant` validated against `tool_variants` or a typed choice. This is a **2b state-contract addition**, recorded here for review. It is dependent implementation and is held.
  - No accepted identity is rewritten or promoted.
- **Creature-entry addressing.** An entry is addressed as `(record_key, component_key, entry name)`, where the name is the printed name with its usage qualifier stripped. Entry names are unique within a block.
- **Prerequisites shared by both character and creature attacks.** Explicit position, actor-turn and elapsed-time authority, recorded form, and in-lair and sunlight environment flags. These are proposed as an additive 15c-owned table; the 2b document schema is not bumped. This is dependent implementation and is held.

## Minimum transition work and cost (stated, not run)

A native mint would touch **7 of 24 accepted batches**:

| Batch | Parts |
| --- | --- |
| equipment | A, C |
| checks-actions-rests | A, C |
| combat-damage-breaking | A |
| monsters | A, B |
| animals | B |
| spell-descriptions | B |
| magic-items | B |

The other 17 batches would be carried over unchanged and proved byte-identical.

**Minimum work:**
1. Add schema 19 to `representation.py`, `projection.py` and `schema_lift.py`, with a registered 18→19 lift that proves prior payloads byte-identical.
2. Regenerate the seven affected batch proposals against the isolated release store (`g1-work/rel`), following the G1 method, and verify with a script that each minted fact equals the reviewed C2 content.
3. Produce one preview artifact under clearly *simulated* receipts.
4. Have Codex review the native preview.
5. Obtain Owner acceptance of that **exact native identity** (the G1 precedent).
6. Record it, with its supersession entry.

**Cost:** several engineering days. The creature batches are the largest: about 1,200 typed entries, plus reviewing all seven regenerated proposals. None of this has been started. The raw C2 files are review material, not an alternative acceptance system.

## Holds

| Work held | Until |
| --- | --- |
| Weapons, masteries, the zero-HP lifecycle, initiative, GameMaster-difficulty checks, saves | C2-A |
| All tool checks | C2-A, plus the tool-validation and variant repair |
| Creature attacks, Multiattack and saves, and every creature target | C2-B |
| Character targets; Str/Dex tests in armor | C2-C |
| The state for position, timing, form and environment, and multi-subject atomic application | The first accepted part that needs it |

Each hold lifts only after Codex independent review and explicit Owner acceptance of the minted native identity.

## Owner Decisions surfaced (new, precise)

**None is required to *review* C2.** One prerequisite is surfaced for the Owner to see:

- **Vampire Familiar.** Its Charmed immunity is conditional on a "vampire master" relation that 2b does not record. Either record a master relation, a small state addition, or accept that a Charmed determination on a Vampire Familiar refuses. The default, absent a decision, is to refuse.
