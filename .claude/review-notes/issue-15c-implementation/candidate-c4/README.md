# CRD Issue 15c — semantic candidate C4 (raw review packet)

**Candidate only.** C4 is not accepted, recorded, minted, published or activated. It is not staged or committed. Its digests have no `.secrets.baseline` entries yet; audited entries are needed at commit time.

C4 supersedes the unaccepted final C3. It applies Codex's settled source/capability contract (`../codex-c3-review.md`) and the grant trust-boundary finding (`../codex-grant-trust-review.md`). The governing scope is #191, body `8225e1b6…57a2`.

C1, C2 and final C3 are read only. `derive_c4.py` checks the C1/C2 digests, the three C3 part digests and the C3 script digest before and after every run. It writes no bytecode caches into those directories.

## Identity

| Part | File | SHA-256 |
| --- | --- | --- |
| **C4-A**: rules, weapons, tools, stat-block conventions, spellcasting formulas, grant and selection authority | `c4a.json` | `901083ec3c8c25e9cd95a638a537cf3db41d8277420e07f0fc2b5d023cd15e62` |
| **C4-B**: all 336 creature records (source only) | `c4b.json` | `f679b06c7e8e3513b9886716754db78b5a28c8cf254cb09d1e195b4f30765c08` |
| **C4-C**: armor and character AC | `c4c.json` | `2c34a6f03fc081a0adbe3abf8f9e50f0dcad55e9c07469cf3204ccb36e68fb5f` |
| **Capability**: execution evidence; *not* source | `capability.json` | `2d884ffbb254af6849a8bd0b61cc5f2f2c4a84dd568f664e3606fb02cb783a8e` |

**Supporting files:**

| File | Hash prefix | Contents |
| --- | --- | --- |
| `concordance.json` | `9af7f073…` | Coverage counts and the per-tool table |
| `invariants.json` | `ffbde180…` | Results of the general completeness checks |
| `reuse-validation.json` | `f9b86579…` | Reused-family payload validation |
| `rules-disposition.json` | `cb983c8e…` | Disposition of each hand-authored rule |
| `no-effect-review.json` | `673d4d8d…` | The 61 trait texts read and pinned as having no effect |
| `transition.json` | `77a89c4d…` | Accepted batches a native mint would touch |
| `derive_c4.diff` | `4f29bf0c…` | Diff of the script against `derive_c3.py` |

**Reproduce:** `venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c4/derive_c4.py`. Two consecutive runs were byte-identical.

## The contract C4 applies

- **Source parts** (`c4a/b/c.json`) hold only source facts, formulas and participant predicates. These are what a native mint would contain.
- **Capability** (`capability.json`) holds everything about execution:
  - each entry's classification;
  - its dependencies, typed as `missing_runtime_input`, `missing_state`, `missing_source_authority` or `unsupported_mechanic`;
  - each entry's applicability notes and its mapping to admitted contexts (`applicability`, `affects`); the source keeps only the subject and typed effects;
  - blockers, and the contributors that **apply**;
  - each selectable Multiattack composition and its certification;
  - per-creature target-side blockers and applying contributors;
  - the A/C execution exclusions and adapter procedures C3 had placed inside source payloads.

**General invariants.** These are the completeness evidence, not the old example asserts. The derivation fails unless every one holds.

| Invariant | Result |
| --- | --- |
| Source parts contain no scope or capability vocabulary (roster, adapter, excluded, certification, adjudication, executable, deferred, held, non-goal, "outside the") | 0 leaks |
| Every number printed in a typed attack, save or Multiattack sentence appears in the **source** entry: a field or a verbatim `untyped_clauses` item. Capability reasons do not count. | 0 unaccounted |
| Every formula reference resolves to a typed C4-A fact | 2 references, both resolved |
| Every save-target phrasing is read by the clause grammar, checked on source `untyped_clauses` | 1 residue (below) |
| Every parameterized attack has its formula | 0 missing |
| Every reused-family payload parses under the accepted `fact_from_payload` | 566 payloads, 0 failures, including the new `speed_modification` |
| Every gain-level reference (expertise, class ASI and Epic Boon feat choices) resolves to an accepted G1 `progression_entry` | 29 of 29 |
| No certified selection contains an unresolved, conditional or spellcasting part | Asserted in the rollup |

The C2 and C3 review examples are still asserted in `regressions()` as illustrations.

**Stated limitation:** number accounting compares sets of numbers. A dropped number that equals another printed number in the same entry would pass.

**Untyped source clauses.** Every clause the parsers do not type is kept verbatim in the source entry as `untyped_clauses` with its part (`targets`, `hit`, `miss`, `failure`, `success`, `failure_or_success`, `reach_or_range`). Only the judgment about it is in capability. Beyond single conditions, these recurring shapes are now typed:
- `reuse_limit` (19): "can't take this action again until the start of its next turn". It depends on actor-turn state.
- `conditional_damage` (25): extra or alternative damage when the attack roll had Advantage, the target or source is Bloodied, or a charge (the source moved N+ feet straight toward a target of a maximum size). Charges depend on position.
- Grappled with a linked condition "until the grapple ends" (6).
- `forced_movement` (8): pushed up to N feet straight away, optionally with a condition. It depends on position.

**Classifying the remaining clauses.** An untyped clause in a reviewed new-mechanic cluster is `unsupported_mechanic` with its cluster named (56). All 56 assignments were read; the labels were narrowed where a clause was mislabelled (web/rope restraints, the Aboleth's charm).

| Cluster | Count |
| --- | --- |
| Hit Point maximum reduction | 11 |
| Curses | 8 |
| Action-economy restriction | 7 |
| Armor or object degradation | 6 |
| Swallowing | 5 |
| Healing or HP regain | 4 |
| Instant death or petrification | 4 |
| Restraint by a breakable object (web, rope) | 3 |
| Teleport, banishment or planar travel | 3 |
| Concentration interaction | 2 |
| Exhaustion and aging | 2 |
| Duration bound to the source's death or plane | 1 |

Every other untyped clause is an ordinary source shape not yet typed, so it is `missing_source_authority`, never an exclusion. A reference to another entry under its own movement terms is `missing_state` (position and actor-turn).

## Family dispositions (Codex C3 review)

| # | Family | C4 correction |
| --- | --- | --- |
| 1 | Fixed values and formulas | See detail 1 below. |
| 2 | Dimensions and target syntax | See detail 2 below. |
| 3 | Exact selections | See detail 3 below. |
| 4 | Applicability by subject, trigger and context | See detail 4 below. |
| 5 | Source versus scope | See detail 5 below. |
| T | Grant trust boundary | See detail T below. |

**1. Fixed values and formulas.**
- **Defenses.** Each defense keeps its fixed value and its formula independently: Animated Object AC 15, Avatar AC 20, and the formula HP of all five. `creature_defense_parameterized` is declared new.
- **Summon entry formulas.** Hit and failure formulas are quote-verified overlays (`ENTRY_FORMULAS`) with the shape `{dice, constant, addends:[{input}], type | type_by_choice}`. They cover Slam by size, Otherworldly Slam, Poison Jab, Web Bolt, Rend and Breath Weapon.
- **Web Bolt.** Its Speed 0 uses the accepted `speed_modification` payload, which validates.
- **Bonuses and DCs.** "Your spell attack modifier" and "your spell save DC" are `formula_ref`s to **new typed C4-A facts**: `spells.attack_rolls/spell_attack_modifier`, `spells.saving_throws/spell_save_dc`, and the eight class `spellcasting_ability` facts. The caster's identity, level and scores are runtime input.
- **Turn owner.** "Your next turn" is owned by `turn_of: caster`.
- **Avatar's Scythe.** Its trailing-period misread is fixed.

**2. Dimensions and target syntax.**
- One order-independent clause grammar covers:
  - count;
  - size, type, living, Frightened and enemy;
  - the source seeing the target, and the target seeing the source;
  - range and space;
  - area shape and **all dimensions**, including height and radius;
  - origin point, with the requirement that the source sees it;
  - relations (Grappled or Charmed by the source);
  - willing-or-conditions and 0 HP;
  - type exclusions;
  - turn-start triggers;
  - automatic fail and success by type;
  - swallow capacity;
  - the source's environment.
- Storm Giant's 40-foot height, Gladiator's Shield Bash and Fell Glare are all read.
- **Residue:** one phrasing. Tarrasque's Thunderous Bellow targets "each object worn or carried", which is object targeting and remains a named boundary.

**3. Exact selections.**
- Every composition is enumerated and certified by its own parts:
  - fixed attacks;
  - "any combination" choices, by their certified options;
  - one selection per option of a mandatory use (Glabrezu: Pummel *or* Spellcasting; Kraken: three);
  - optional and if-available uses as the base plus a separate addition (Dryad's Charm Monster).
- 249 selections in all; 115 are executable once accepted.
- 35 Multiattacks keep a certified base beside an unavailable option.

**4. Applicability by subject, trigger and context.**
- **Only standing traits contribute.** Actions, bonus actions, reactions and legendary actions are separately selected and never block siblings (15 `separate_action`).
- **Every trait name has a reviewed row** (`CONTRIBUTOR_REVIEW`): subject (self, caster, rider, allies, others), the contexts it touches, and what it needs. Examples:
  - Shared Resistances: subject caster; affects none of the spirit's operations.
  - Healing Touch: no longer blocks Fell Glare.
  - Ten revival traits: no admitted context.
  - Bloodied Frenzy, Bloodied Fury, Blood Frenzy, Blurred Form and Evasion: typed, with predicates on recorded HP or conditions. They are recorded as **applies**, not blockers.
- **Reactions** are separately selected and deferred. The trigger is read in both source forms (`_Trigger:_` and plain `Trigger:`). It is matched to the context it touches: `rolls_against`, `damage_taken`, `target_save` or `own_check`. A trigger on the amulet wearer maps to `related_creature_rolls_against` (Shield Guardian Protection). Each reaction blocks only matching contexts. Four reactions touch no admitted context and block nothing: Unnerving Gaze, Shriek, Pursuit, and one Ink Cloud, triggered when a creature ends its turn nearby.
- **Closed context vocabulary.** Every `affects` value must belong to a closed set, and each member is rolled up as a `<context>_blocked_by` key (asserted). The set adds `own_check`, `others_check_about_subject`, `related_creature_damage_taken` and `related_creature_rolls_against`. Earlier, `own_check` was assigned but never rolled up.
- **Cross-creature contributors** (Pack Tactics, Aura of Authority) are disclosed in the creature's target-side rollup as `encounter_state`: they depend on other creatures' positions and conditions.
- **Spider Climb and Ice Walk** are typed `check_requirement_removal` against `glossary.climbing/difficult_climb`; Ice Walk is limited to icy surfaces.
- **The no-effect allowlist** was re-pinned (61 texts). The only change was the removal of those entries; nothing was added.

**5. Source versus scope.**
- **Ammunition** states the full source rule: one piece per attack, drawing is part of the attack, a **free hand to load a one-handed weapon**, and recovery of half the ammunition (rounded down) after a fight in 1 minute. The recovery *exclusion* is moved to `capability.scope`.
- **Removed from source payloads:** `multiattack_rule.certification` and `hit_point_bound.applied`. Both are now adapter procedures.
- **Armor training** states `cannot_cast_spells: true` as source; its scope note is in capability.

**T. Grant trust boundary.** 91 new C4-A grant and selection facts state what each contributing source **entitles**:
- **Class skill choices:** the 12 Core Traits rows, with count and list.
- **Backgrounds:** the 4 fixed skill grants, plus their listed abilities and the +2/+1 or +1/+1/+1 rule (cap 20).
- **Feats:** the Ability Score Improvement feat (+2 or +1/+1, cap 20, level 4+, repeatable), and Grappler and the 7 boons (+1, cap 20 or 30, with their ability lists). Skilled gives 3 skills or tools.
- **Multiclass entry:** all 12 classes' "As a Multiclass Character" grants. Bard gives one skill of any kind; Ranger and Rogue give one from their class list; the other nine give none.
- **Origin feats:** the four background feat grants (Acolyte: Magic Initiate (Cleric); Criminal: Alert; Sage: Magic Initiate (Wizard); Soldier: Savage Attacker), and Human Versatile's choice of one Origin feat.
- **Species:** Keen Senses (1 of 3 skills) and Skillful (any 1 skill).
- **Feat prerequisites** (9 `feat_prerequisite` facts, each on the feat's own category line): Ability Score Improvement (level 4+); Grappler (level 4+, Strength or Dexterity 13+); all seven Epic Boons (level 19+), with Spell Recall also requiring the Spellcasting feature. The ASI feat's adjustment no longer carries its own prerequisite.
- **Class ASI and Epic Boon features** (24 `feat_choice` facts): each gain entitles the named feat (the Ability Score Improvement feat, or an Epic Boon feat) or another feat whose prerequisites are met. Gain levels reference G1 `progression_entry`.
- **Sibling skill grants** found by the audit: Barbarian Primal Knowledge (one from the Barbarian list) and College of Lore Bonus Proficiencies (any three).
- **Boon provenance:** each boon's adjustment cites its own line (`feats.md` 117, 127, 137, 147, 159, 169, 181), not the first occurrence of an identical quote.
- **Expertise:** the glossary rule (requires proficiency, no duplicates, ×2), and Bard, Rogue, Deft Explorer, Ranger and Scholar, with a count per gain and Scholar's list. Gain levels are **not restated**: each references the accepted G1 `progression_entry` for its feature.

**Held: grant validation in runtime.** That means validating each recorded grant, adjustment and expertise against its source entitlement, level and linked `ChoiceRecord`, and correcting `checks.py`, whose current tests bless Wizard Expertise and arbitrary ability-score adjustments. It is dependent implementation and is held until native acceptance. **No general build-legality sweep is proposed.**

## Codex provisional C4 findings (folded into this pass)

`../codex-c4-provisional-findings.md` reviewed the earlier C4 snapshots (`6d540c50…`, `dc93c72c…`, `e5024134…`).

| Finding | Disposition |
| --- | --- |
| Feat prerequisites (Grappler, boons, Spell Recall) | Patched: typed `feat_prerequisite` (detail T) |
| Starting-class versus multiclass skill grants | Patched by the Advisor fix: 12 multiclass facts. `level_history` supplies which class came first; the source rule is now typed |
| Class ASI feature to ASI-or-qualified-feat link | Patched: 24 `feat_choice` facts, including Epic Boon |
| Boon source anchors | Patched: each cites its own line |
| Shield Guardian Bound | Patched: subject `amulet_wearer`, context `related_creature_damage_taken`. Unsupported damage transfer; missing relation (the wearer) and position. It refuses through `related_creature_damage_taken_blocked_by` and does not block the guardian's own rolls |
| Sphinx Inscrutable | Patched: subject `others`, context `others_check_about_subject`. Missing state: whether an Insight check is about the sphinx's intentions or sincerity. It refuses through `others_check_about_subject_blocked_by`; it is not called out of scope |
| Fire Aura (4 instances) | Patched: all four were read as end-of-turn Emanation damage, with no on-hit trigger. The invented `melee_hits_against` blocker is removed; the unsupported aura mechanic is recorded |
| Swarm and HP recovery | Patched: a typed `hit_point_regain_prohibition` (Hit Points and Temporary Hit Points). It applies only when `zero_hp_treatment` is `character_style`, and is listed under `applies_when_targeted.zero_hp_outcome`; it is not a blocker. The source resolves the conflict with "When an exception and a general rule disagree, the exception wins" (`playing-the-game.md` 109). So the natural-20 and Stable 1d4-hour 1 Hit Point regains do not happen, and the rest of the death-save rule is unchanged. The default monster death determination is unaffected |
| Eight Bloodied damage branches | Patched: Blood Hawk (target Bloodied), six animal swarms and the Swarm of Crawling Claws (source Bloodied, plus a Medium-or-smaller Prone). Venomous Snakes' em-dash form keeps its unconditional 10 (3d6) Poison in `hit_damage`. Each "instead" branch names the term it replaces (`replaces_hit_damage_index`) |
| Giant Insect `any_of=[]` | Patched: "a number of attacks" takes the block's attack-roll actions, Poison Jab and Web Bolt. Web Bolt keeps its source `form_only: spider` |
| Applicability judgments in source | Patched by the Advisor fix: `applicability` and `affects` are capability-only. A full-file sweep of C4-A/B/C finds none of the scope words |
| Tarrasque `excludes_types: ["being"]` | Patched: "each object that isn't being worn or carried" is kept verbatim as the named object-target residue. No type predicate is produced |

**Defect found and fixed in the sweep itself.** An earlier patch's escaping turned the scope sweep's `\bheld\b` into backspace characters, so "held" was not being checked. The earlier zero-leak claims therefore did not cover that word. The pattern is restored and a full-file sweep is clean. A scan for every control character (`\x00`–`\x08`, `\x0b`, `\x0c`, `\x0e`–`\x1f`, `\x7f`) finds none in `derive_c4.py`, this README, `status.md` or `review-handoff.md`.

**Contributors with unmet needs** are now always recorded with their dependency, even when they touch no admitted context. There are 18 such entries: Barbed Hide, Fire Aura, Fire Form, Heat Aura, Incorporeal Movement, Ooze Cube, Running Water, Stake to the Heart and Water Susceptibility. They are `conditional`, not `supported`. `affects` still decides what each one blocks, so they block nothing.

## Coverage (capability)

| Class | Entries |
| --- | --- |
| supported | 538 |
| conditional | 538 |
| deferred (named) | 164 |
| no effect (reviewed and pinned) | 137 |

**Dependencies:** `missing_state` 667, `unsupported_mechanic` 295 (all named), `missing_source_authority` 103, `missing_runtime_input` 18.

**Executable once accepted** still needs the shared position and actor-turn state:

| Entry kind | Executable |
| --- | --- |
| attacks | 269 of 429 |
| Multiattacks | 114 of 181 |
| saves | 1 (Glabrezu Pummel: its target is Grappled by the source, which is recorded state) |

**Attack-roll lines:** all 429 are parsed, 423 generic and 6 in assessed creatures.

## Vampire Familiar

- **What C4 proposes:** only an explicit `vampire_master` SubjectReference to a creature in the same story. It is never aliased to summoner or controller.
- **What C4 does not propose:** any template or type restriction. The source leaves the master's identity otherwise unconstrained.
- **Effect:** absent the relation, only the Charmed determination refuses.

The proposal is held, not implemented. Any broader relationship policy would be an Owner Decision; **none is requested.**

## Minimum native transition (re-assessed; not prepared)

The facts now touch **11 of 24** accepted batches:

| Batch | Parts |
| --- | --- |
| animals | B |
| character-origins-feats | A |
| checks-actions-rests | A, C |
| classes | A |
| combat-damage-breaking | A |
| core-play-completion | A (`glossary.expertise`) |
| equipment | A, C |
| magic-items | B |
| monsters | A, B |
| spell-descriptions | B |
| spellcasting | A |

The four batches added over C3 are classes, spellcasting, character-origins-feats and core-play-completion. Typing the spellcasting formulas and grant authority is what adds them. The cost is stated here rather than chosen silently: without them, the summon operations and the adjusted/proficiency/expertise path would stay held on missing source authority.

**Minimum work:**
1. Add schema 19, with an 18→19 lift.
2. Regenerate those 11 batch proposals against the isolated store, with a minted-equals-reviewed check covering source parts only (capability is not minted).
3. Produce a simulated-receipt preview.
4. Codex native review.
5. Owner acceptance of the exact native identity.
6. Record it.

**None of this has been prepared.**

## Holds and genuine remaining dependencies

All dependent implementation is held: gameplay execution, grant validation, the state tables and `checks.py` corrections.

| Dependency kind | What is missing |
| --- | --- |
| Missing state | Position, visibility, actor-turn and elapsed time, current form, lair, lighting and sunlight, the source's environment, the recorded head count |
| Missing runtime input | Caster and summoner values, spell level, form and type choices, GameMaster choices (Training skill, Draconic Origin, damage notation, Legendary Resistance) |
| Missing source authority | Ordinary untyped clauses (verbatim in source) still to type |
| Named unsupported mechanics | Spellcasting, reactions, special effects, auras, absorption, regeneration, object targeting, and the ten clause clusters above |

**No Owner Decision is required to review C4.**
