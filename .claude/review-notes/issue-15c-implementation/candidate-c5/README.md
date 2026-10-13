# CRD Issue 15c — semantic candidate C5 (raw review packet)

**Candidate only.** C5 is not accepted, recorded, minted, published or activated, and it is not staged or committed. Its digests have no `.secrets.baseline` entries yet; audited entries are needed at commit time.

C5 supersedes the unaccepted final C4 (A `901083ec…`, B `f679b06c…`, C `2c34a6f0…`, capability `2d884ffb…`). It applies:
- `../codex-c4-review.md`: all five findings;
- `../codex-c5-provisional-roster.md`: observer checks, Undead Fortitude, exact tool selectors and honest assertion labels;
- `../codex-c5-grant-family-addendum.md`: save, weapon, armor, tool and mastery entitlements;
- `../codex-c5-provisional-linkage.md`: effect, branch and termination association, and Mimic's unconditional Acid damage.

The governing scope is #191, as read back in `../../issue-15c-preparation/issue-draft.md`.

**Preservation.** `derive_c5.py` checks C1, C2, C3 and final C4 (all part files, the C4 capability, `derive_c3.py` and `derive_c4.py`) byte-for-byte before and after every run. G1 `2ccbaeba…1258` is read only and digest-checked.

## Identity

| Part | File | SHA-256 |
| --- | --- | --- |
| **C5-A**: rules, weapons, tools, stat-block conventions, spellcasting formulas, grant and entitlement authority | `c5a.json` | `866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9` |
| **C5-B**: all 336 creature records (source only) | `c5b.json` | `187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6` |
| **C5-C**: armor and character AC; content unchanged from C4-C, header only | `c5c.json` | `bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4` |
| **Capability**: execution evidence, *not* source | `capability.json` | `6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6` |

**Supporting files:**

| File | Hash prefix | Contents |
| --- | --- | --- |
| `invariants.json` | `f9ebd4ac…` | Conservation, fidelity and the general checks |
| `source-key-review.json` | `3574abc9…` | The pinned, reviewed source key names |
| `entitlement-examples.json` | `5857ccb4…` | Source-rule assertions and grant-vocabulary resolution |
| `concordance.json` | `2c1bb1d5…` | Coverage counts |
| `reuse-validation.json` | `adff1f07…` | Accepted-family payloads, re-parsed |
| `transition.json` | `73d30455…` | Accepted batches a mint would touch |
| `rules-disposition.json` | `b65fbdd9…` | Hand-authored rule dispositions |
| `no-effect-review.json` | `673d4d8d…` | Unchanged from C4 |
| `derive_c5.diff` | `139ceb6b…` | Diff of the script against `derive_c4.py` |

**Reproduce:** `venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c5/derive_c5.py`. Two consecutive runs were byte-identical.

## 1. Complete logical entries (finding 2)

**Fix.** An entry is its head line plus every directly following continuation line: a wrapped line or an `&emsp;` paragraph. Earlier, each physical line was read alone, which dropped 135 continuation lines. Examples:
- Bronze Dragon Thunderclap: "Thunder damage … Deafened";
- Ghost Possession: lines 6844–6845;
- Nalfeshnee: its 24-hour immunity.

**What each entry carries.** Every source entry has `source_text`, the complete logical text, and `source_span` (file, first line, last line). Source `kind` is now only the printed shape: `attack`, `save_effect`, `multiattack`, `usage_header`, `entry_reference`, `reaction` or `prose`. Roles such as contributor or named mechanic are capability.

**Normalization.** One rule applies throughout: the `&emsp;` prefix and `<br>` are removed, and physical lines are joined with one space.

**Independent conservation.** `invariants.json` → `logical_entry_conservation` re-reads the raw files without the entry or clause parsers.
- After each block's CR line, every non-blank line other than a heading or `<hr>` belongs to exactly one entry span.
- Each span reproduces its `source_text`.
- Raw head lines and entries correspond one to one.
- No stray lines sit in any profile region.
- **Result: 1,377 entries and 1,512 content lines, with 0 problems.**

**Sibling check.** I checked whether any of the 379 quote-based C5-A/C rule facts sits on a wrapped line: none does. The new Ranger Weapon Mastery fact quotes a sentence wrapped at `classes.md` 6347–6348, and records both lines.

## 2. Source families and per-piece dispositions (finding 1)

**How clauses are split.** Every clause the entry parsers leave untyped is split into exact pieces: sentences, conjuncts, leading predicates and branch labels. The pieces rebuild the clause byte for byte, which is asserted. Each piece then gets exactly one disposition:

| Disposition | Count | Where it lives |
| --- | --- | --- |
| typed | 433 | The fact is in source, under `clauses[].pieces[].typed` |
| unsupported (named engine) | 189 | Capability, with its cluster |
| no mechanical consequence | 6 | Capability; narrative only, such as Heart Sight |
| punctuation | 101 | Separators |
| **untyped (missing source authority)** | **0** | |

**Mixed clauses are split, not labelled whole.** A cluster is matched against a single piece. A piece inherits a cluster only when its own sentence names that engine; such pieces are marked `by_sentence_context`. Two examples:
- Bearded and Bone Devil: the timed Poisoned condition and "can't regain Hit Points" are typed. That keeps them relevant to the approved zero-HP recovery path.
- Ice Devil: its Speed decrease is typed, while its action-economy pieces are named as unsupported.

**Typed families.** Each is shown with representatives.

| Family | Representatives |
| --- | --- |
| "feet" reach and range wording | Eagle, Giant Rat, Djinni |
| Grapple: size, escape DC, appendages, linked or "while Grappled" conditions, escape Disadvantage, Tail targeting restriction | Crocodile, Giant Crocodile, Chain Devil, Kraken, Mimic, T. rex |
| Conditional replacement damage | Chimera (with Advantage), Mimic (the target is Grappled by it) |
| Pushes and pulls, up to N or exactly N, optional Prone | Balor, Merrow, Satyr, Shambling Mound |
| Charge Prone, with a follow-up attack | Allosaurus, Elephant, Gorgon |
| Timed Speed and AC changes | Frost Giant, White and Green Dragons, Brass Dragon |
| Next-roll Advantage or Disadvantage, on either side | Ettin, Pirate Captain, Worg |
| Combined and timed conditions in minutes or hours, with ending events | Storm Giant, Rakshasa, Kraken, Incubus, Nalfeshnee |
| d20 penalty die and damage-roll penalty | Copper and Gold Dragons |
| Repeat saves, with automatic success after a time | Chuul, Doppelganger, Quasit, Silver Dragon, Sphinx |
| 24-hour immunity to this creature's feature | Cloaker, Ghast, Ghost, Sea Hag, the lycanthropes |
| Failure-by-5, and First, Second or Subsequent Failure branches | Homunculus, Pseudodragon, Cockatrice, Basilisk, Medusa, Gorgon |
| Hit-point threshold branches, including "drops to 0 Hit Points" | Incubus, Sea Hag, Solar |
| Zero-HP outcomes: becomes Stable, or dies if reduced to 0 by this attack | Phase Spider, Umbral Dagger, Gibbering Mouther, Mummy |
| Damage whose type comes from a choice | Half-Dragon (Draconic Origin), Draconic Spirit |
| Underwater Fire Resistance qualification | Dragon Turtle, Steam Mephit |
| Returning weapon | Merfolk, Salamander, Solar, Ice Devil |
| Periodic damage or HP loss at the start of a named creature's turn | Pit Fiend, Vrock, Invisible Stalker |
| Saves inside a framing sentence | Death Burst, Death Throes, Boulder Toss, Fear Aura, Paralyzing and Petrifying Breath |

The 25 former `special_effect` entries are now `save_effect`s whose frame and outcomes are disposed piece by piece.

**Named engines (unsupported).** These are genuinely different mechanics, not ordinary wording:
- possession;
- swallowing, engulfing, attachment and suffocation;
- Hit Point maximum changes;
- lycanthropy and creature transformation;
- rest benefits;
- teleport, banishment and planar travel;
- object burning, and armor or object degradation;
- object targeting;
- Reactions and action economy;
- spellcasting, including Concentration and Verbal components;
- Exhaustion and aging;
- death caused directly by an effect;
- the source regaining Hit Points;
- infernal wound;
- Holy Water as an item interaction;
- charm control and telepathy;
- the random behaviour table;
- compelling song or babbling;
- encounter movement and placement;
- halved damage sharing;
- grapple capacity across several targets.

Every piece in these engines keeps its full source text, and an applicable unsupported piece refuses its entry. Ghost Possession is in the possession engine.

**Source-to-field fidelity, without the readers** (`invariants.json` → `source_to_field_fidelity`). The closed-vocabulary tokens of each typed piece's raw text must all be present, as a multiset, in its serialized fields. The vocabulary is sizes, conditions, damage types, abilities, numbers and dice, and duration units. Two further checks:
- **Turn owner:** every timed piece's printed owner ("its" or "the target's" means the target; "the <name>'s" means the source; "this turn") must equal a typed `turn_of`.
- **Grant facts:** each must hold its quote's abilities, armor words, weapon categories and properties, tool words and numbers.

**Result: 433 typed pieces (42 with a turn owner) and 83 grant facts, with 0 failures.** This would catch a dropped "Medium or smaller", which the number check could not.

**Linkage** (`codex-c5-provisional-linkage.md`). Associations are explicit, entry-local fields; they are never runtime identifiers, and execution never recovers them from prose.

| Field | Meaning |
| --- | --- |
| `effect_id` | An entry-local id (E1, E2, …) on each effect-creating piece |
| `branch` | The branch every typed piece belongs to |
| `bound_effect` | Which effect a "While X" or "Until X ends" predicate or linked condition refers to |
| `lasts_while_effect` | On an effect stated under such a predicate |
| `ends_effects` | Exactly what a termination or repeat-save success ends |
| `duration_of_effects` | Exactly what a sentence-level duration governs |

Examples:
- **Bearded Devil.** "Until this poison ends" binds to E1, the Poisoned condition from this entry, and the regain prohibition lasts while E1 lasts.
- **Pseudodragon.** Unconscious E2 belongs to `failure_by_5_or_more`, and damage or waking ends E2 only. The one-hour Poisoned E1 stays.
- **Sleep Breath.** The second failure's Unconscious E2 is the only effect its ending clause ends.
- **Mimic.** Mimic now uses the same form as its sibling Venomous Snakes. The unconditional 4 (1d8) Acid is in `hit_damage`, and the piece points to it (`unconditional_hit_damage_indices`). `when` governs only the replacement of `hit_damage[replaces_hit_damage_index]`.
- **Unbound predicate.** Exactly one predicate is unbound: Aboleth Dominate Mind's "While Charmed". Its Charmed piece belongs to a named engine (charm control and a planar duration), so no typed effect exists for it to bind to.

## 3. Source versus policy (finding 3)

- **Swarm.** The source prohibition is unconditional: no Hit Point regain and no Temporary Hit Points. Its zero-HP relevance and the exceptions rule (`playing-the-game.md` 109) are in capability.
- **Half-Dragon.** `recorded_as` has been removed. The source keeps the choice vocabulary, `chosen_for` (Draconic Origin) and `chosen_by` (the GM).
- **Key review.** Every key name in C5-A/B/C was read once as a source fact, a source location, an entry-local link or candidate packaging. The sorted list is pinned (`source-key-review.json`), so a new key fails the derivation until it is reviewed. The review moved or removed four more items:
  - the `grants_conditions` roll-context mapping, moved to capability;
  - Vampire Familiar `requires`, moved to capability;
  - Swarm `applies_when`/`precedence`, moved to capability;
  - legendary `blocked_by`, renamed `not_while_has_conditions`.
- **Observer checks** (Codex roster note) are admitted skill checks that another creature makes, typed as `observer_check`:
  - Raven Mimicry: DC 10 Wisdom (Insight), made by "a hearer";
  - Green Hag Mimicry: DC 14 Wisdom (Insight);
  - Gelatinous Cube Transparent: DC 15 Wisdom (Perception), only if the checker hasn't witnessed the cube move or act.
  
  Missing state: whether the creature heard the sounds, or witnessed the cube. They are no longer named as outside the roster. C4 had wrongly given Raven DC 14.
- **Undead Fortitude** (Zombie, Ogre Zombie) is typed as `zero_hit_point_save`:
  - trigger: damage reduces the subject to 0 HP;
  - a Constitution save, DC 5 plus the damage taken;
  - unless the damage is Radiant or from a Critical Hit;
  - on a success, the subject drops to 1 HP instead.
  
  It applies whatever the subject's zero-HP treatment, and it is not healing. Capability: it needs the triggering damage event (amount, type, critical identity), resolved synchronously.
- **Inscrutable** is typed in source: Disadvantage on Wisdom (Insight) checks against the subject, with its purpose, "to ascertain the subject's intentions or sincerity". The payload re-parses as the accepted `advantage` family.

## 4. Contributing grants (finding 4 and the addendum)

**C5-A** holds the earlier repaired skill, ASI, expertise and feat facts, plus:

| Grant | Facts | Source |
| --- | --- | --- |
| Starting-class saving throws, weapons and armor | 12 classes × 3, `context: level_1_character` | Core Traits tables |
| Starting-class tool rows | Bard, Druid, Monk, Rogue | Core Traits tables |
| Multiclass entry grants | 12; only what is printed, never saving throws | "As a Multiclass Character" |
| Saving throws from features | Monk Disciplined Survivor (all six), Rogue Slippery Mind (Wisdom and Charisma) | With exact G1 gain levels |
| Weapons and armor from a chosen option | Cleric Divine Order Protector, Druid Primal Order Warden | With exact G1 gain levels |
| Weapon Mastery | 5 classes: count, eligible kinds (Barbarian melee only; Paladin, Ranger and Rogue need proficiency), Long Rest swap qualifier ("one" or "any") | Barbarian and Fighter count by level from their own Features tables |
| Background tools | 4, including Soldier's one Gaming Set choice | Backgrounds |
| Skilled | Its tool alternative names its vocabulary | Feats |
| Primal Knowledge | Exact G1 progression entry | Classes |
| College of Lore Bonus Proficiencies | Eligibility: subclass and Bard level 3, read from its source headings | Classes |

**Not a G1 defect claim.** G1's quantity-bearing `weapon_mastery` progression entry merges the Barbarian and Fighter counts under one unqualified key. It is preserved and not relied on, and this is recorded under `observations` in capability.

**Rest swaps** are kept as source qualifiers and refuse explicitly at execution; there is no rest-resource engine.

**Exact selectors.** Choice vocabularies are typed selectors, never prose strings:
- tools as `{record_key, component_key}` of a typed `tool_entry`;
- `tool_variants_of` a typed `tool_variants` fact (Musical Instrument, Gaming Set);
- `tool_category` of `tool_entry` membership (`artisans_tools`);
- `any_tool_entry` (Skilled);
- skill lists, or the record/component of a class skill list.

**Checks.**
- `entitlement-examples.json` → `vocabulary_resolution` resolves all 89 vocabulary fields against typed C5 or G1 facts: tools, variants, categories, skills, G1 `weapon_category` (simple, martial), weapon properties, the melee range class, armor categories and record/component references.
- Every gain-level reference resolves to an accepted G1 `progression_entry`.
- Every A-part grant passes the fidelity check.
- `source_rule_assertions` holds 12 **source-rule assertions** checked against the candidate's own facts. Examples: a Barbarian multiclass entry gives Martial weapons and Shields but no saves; Monk Martial proficiency only for weapons with the Light property. They are **not runtime entitlement validation**, which stays held.

**Grant sibling audit** (required because the grant family drew review findings in two rounds):
- **Trigger:** the Codex grant-trust finding and the C5 addendum.
- **Inspected:** every "proficien" line in classes, feats and character origins, besides the Core Traits, multiclass, Weapon Mastery, background and feature structures above.
- **Dispositions:**
  - **Patched:** every Core Traits row, multiclass line, Disciplined Survivor, Slippery Mind, Protector, Warden, the five Weapon Mastery features, background tools, Skilled, Primal Knowledge and College of Lore.
  - **Already safe:** Expertise features, Scholar, Keen Senses and Skillful (C4 repairs).
  - **Out of scope:** Warlock Pact of the Blade (`classes.md` 9116). Its weapon proficiency lasts "until the bond ends", and the bond is an invocation feature with its own conjure, distance, time and death lifecycle, which is general feature execution. A weapon proficiency recorded through it cannot be validated and refuses. It is not typed in C5.

**Still held.** Runtime validation of recorded grants against these facts, and the `checks.py` corrections, wait for native acceptance. **No general build-legality sweep is proposed.**

## 5. Vampire Familiar

The source qualification "vampire" is kept, as `unless_source_is: {relation: master_of_the_subject, qualification: vampire}`. The capability proposal requires the related creature's vampire qualification to be validated: a same-story reference alone does not qualify it. A missing relation, or a missing or unvalidated qualification, refuses only the Charmed determination. How a creature is validated as a vampire is a held determination. No exact template rule is invented, and no Owner Decision is requested.

## Coverage (capability)

| Class | Entries |
| --- | --- |
| supported | 552 |
| conditional | 527 |
| deferred (named) | 161 |
| no effect (reviewed) | 137 |

**Dependencies:** `missing_state` 852, `unsupported_mechanic` 398 (all named), `missing_runtime_input` 21, `missing_source_authority` **0**.

**Executable once accepted** (still needs the shared position and actor-turn state): attacks 282 of 429, Multiattacks 121 of 181, saves 1. These counts are not the readiness argument; the conservation and fidelity checks above are.

## General invariants

| Invariant | Result |
| --- | --- |
| Logical-entry conservation | 0 problems |
| Source-to-field fidelity | 0 failures |
| Scope vocabulary in the source parts | 0 leaks |
| Printed numbers accounted for in the source entry's fields and explicit clause residue | 0 unaccounted. `source_text` and `source_span` are excluded, so this is not vacuous. It is a set comparison; fidelity is the multiset check |
| Grant vocabulary resolution | 89 fields, all resolved |
| Formula references | 2, both resolved |
| Target-phrase residue | 13, each kept verbatim and given a disposition |
| Parameterized attacks without a formula | 0 |
| Reused accepted-family payloads | 672, with 0 failures |
| Reviewed source key names | 445, pinned. Each change since the first pin is proven against the pinned reviewed set |
| Control characters in the derivation | None; the script asserts this about itself |

## Minimum native transition (not prepared)

The facts still touch **11 of 24** accepted batches, the same set as C4: animals, character-origins-feats, checks-actions-rests, classes, combat-damage-breaking, core-play-completion, equipment, magic-items, monsters, spell-descriptions and spellcasting.

The grant addendum lands in classes and character-origins-feats, which were already affected.

**Minimum work, none of it prepared:**
1. Schema 19 with an 18→19 lift.
2. Regenerate those 11 batches with a minted-equals-reviewed check on the source parts only.
3. A simulated-receipt preview.
4. Codex native review.
5. Owner acceptance of the exact native identity.
6. Recording.

## Holds and boundaries

**Held:** all dependent implementation, meaning gameplay execution, grant validation, the state tables and `checks.py`.

**Missing state:** position, visibility, actor-turn and elapsed time, current form, lair, lighting and sunlight, and the recorded head count.

**Missing runtime input:** caster values, choices and GM selections.

**Named unsupported engines:** listed in §2.

**No Owner Decision is required to review C5.**
