# CRD Issue 5d — Pre-implementation architecture checkpoint

**Scope:** production authoring and schema closure (the next bounded CRD Issue 5d PR).
**Status:** discovery and analysis only. Nothing here is an accepted decision. No branch, commit, PR,
or production change was made. Every classification below is a **recommendation for external review**.

---

## 0. Starting state — verified, not assumed

**Repository.** `origin/main` is `e36912456160ee7269280edb029238d0c5297e7f`, the merge commit of PR #150
(`feat(rules): first-class authored prose overlay for typed overrides (#137)`). The local `main` ref is
stale at `b8b42cd` and should be fast-forwarded before any branch is cut. Analysis was run on the working
tree at `HEAD` (`ac5c723`), whose tree hash `41a3d7f79a7c851190a736a9dc37190a8513f208` is **byte-identical**
to `origin/main`'s tree, so the content analysed is exactly post-#150 `main`.

**Production binding.** Rebuilt from the committed PDF via `build_candidate` → `finalize_release`
(the same path `tests/ingestion/conftest.py::full_release` uses), into a private on-disk store. All five
prompt-supplied values reproduce exactly:

| Value | Prompt | Measured | |
|---|---|---|---|
| `package_uuid` | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` | same | ✅ |
| `release_version` | `5.2.1-corpus.36b786d8-fa2` | same | ✅ |
| source SHA-256 | `8974902d…5e3d87` | same | ✅ |
| transform-config SHA-256 | `77720c2f…81ef3e` | same | ✅ |
| corpus contract | `5c-operational-1` | `gate.py:102` ∩ `corpus/operational.py:35` | ✅ |

Also measured (not supplied in the prompt, recorded for the authoring PR's binding):
`bundle_root_hash 03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685`,
`evidence_report_hash a03eaf0c707382ee07e6ea983c865268dfb070736cc612fb0487f4e50264322a`,
`persisted_corpus_digest c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b`.
These come from one build; this session did not attempt a second build to prove cross-build stability.

The transform-config hash appears **nowhere in committed source** — it exists only in a built release's
identity. `test_runtime_production_release.py:51-52` carries the package UUID and release version as
*expectations*, not as authority; both now have independent confirmation.

---

## 1. Production inventory

Counts are diagnostics. None of them is completeness authority, and the publication gate already treats
them that way (`gate.py` puts every count in `GateResult.diagnostics` and no count is a pass condition).

### The three prompt-named baselines — no drift

| Measure | Prior baseline | Measured | |
|---|---|---|---|
| Represented leaves | 28,109 | **28,109** | ✅ |
| `ENTRY` containers | 2,422 | **2,422** | ✅ |
| Logical tables | 683 | **683** | ✅ |

The 683 is independently confirmed twice: the live container count, and the committed frozen oracle
`src/afterworlds/ingestion/corpus/srd_table_inventory.json` (`table_count: 683`,
`inventory_hash 60b4df42…`).

### Full inventory

**Leaves** — 28,474 inventoried: 28,109 `REPRESENTED`, 365 `EXCLUDED`, 0 `UNRESOLVED`.
Exclusions: 364 `running_header_footer`, 1 `toc_or_index_listing`. (5c-owned; not reclassifiable here.)

Represented leaves by type:

| Leaf type | Count | Share |
|---|---:|---:|
| `table_cell` | 15,715 | 55.9% |
| `paragraph` | 7,254 | 25.8% |
| `heading` | 2,863 | 10.2% |
| `stat_field` | 2,121 | 7.5% |
| `list_item` | 155 | 0.6% |
| `attribution` | 1 | — |

**Containers** — 3,369 total: 2,422 `entry`, 683 `table`, 246 `subsection`, 18 `section`.

**Chunks and projection** — 28,109 chunks, 28,109 projection edges, all role `authoritative`.
The relation is a strict **bijection**: 0 leaves covered by more than one chunk, 0 chunks covering more
than one leaf, and **0 edges covering less than a whole leaf**. This is the single most consequential
structural fact for §3: the exact-governing-prose grain is *one whole leaf*.

**Leaf placement** — 26,786 represented leaves sit inside an `ENTRY` container; **1,323 sit outside any
`ENTRY`** (808 `table_cell`, 263 `heading`, 248 `paragraph`, 3 `list_item`, 1 `attribution`).
15,715 sit inside a `TABLE` container.

**Per top-level section** (represented leaves / named `ENTRY` containers):

| Section | Leaves | Named entries |
|---|---:|---:|
| Monsters A–Z | 7,883 | 235 |
| Classes | 7,008 | 345 |
| Magic Items | 3,125 | 286 |
| Animals | 2,570 | 95 |
| Spells | 2,308 | 366 |
| Equipment | 1,325 | 165 |
| Rules Glossary | 1,024 | 155 |
| Creation | 878 | 36 |
| Gameplay Toolbox | 695 | 72 |
| Playing the Game | 640 | 91 |
| Monsters | 246 | 28 |
| Character Origins | 223 | 26 |
| Feats | 137 | 22 |
| Contents / Blocks / Legal / Character | 47 | — |

Of the 2,422 `ENTRY` containers, ≈1,922 carry a **name** and ≈500 carry a **structural role**
(`Actions` ×220, `Traits` ×159, `Bonus Actions` ×71, `Reactions` ×25, `Legendary Actions` ×25).

**Legacy state** — a fresh production build writes **0 rows** to `rp_mechanical_entities` and **0 rows**
to `rp_overrides`. Legacy retirement is therefore a code/migration problem, not a data-migration one.

### Drift on the two ADR-005d Context figures the prompt did not name

Both are recorded in ADR-005d lines 43–45 as discovery measurements. Neither has a committed definition
anywhere in the repository, so neither is reproducible by committed tooling.

**"1,533 represented leaves with at least two lexical mechanical-signal families."** The signal-family
taxonomy is not in `src/`, `scripts/`, or `tests/`. Re-derived under a **stated ten-family regex
heuristic of my own** (dice, DC/save, check, action economy, typed damage, condition, range/area,
duration/concentration, advantage, resource/rest): **1,438** leaves with ≥2 families
(distribution: 0→23,869, 1→2,802, 2→648, 3→338, 4→185, 5→149, 6→69, 7→47, 8→2).
This is a **re-derivation under a different definition, not a reproduction**. It is not evidence of drift
in either direction, and it is not offered as a replacement figure.

**"203 colliding names among 1,893 distinct container names."** Not reproduced exactly under any
definition tried. Measured variants (label stripped; casefolding and raw-label variants gave identical
results):

| Population | Distinct | Colliding |
|---|---:|---:|
| all containers | 2,424 | 266 |
| non-table (entry+section+subsection) | 1,912 | 212 |
| entry + subsection | **1,898** | **208** |
| entry only | 1,801 | 63 |
| table only | 512 | 54 |

The ADR figure sits just below the `entry+subsection` variant. The qualitative finding it supports —
scoped name collision is real and material — is confirmed independently in §2 (canary 6).
**Recommendation:** either record the measuring definition in ADR-005d, or mark both figures as
superseded discovery measurements. Neither is merge-blocking.

---

## 2. Observed semantic shapes

All evidence below is from the production release, cited by container id / printed page / literal text.

### A. `ENTRY` is not a record, in *both* directions

- **Record smaller than entry:** 90 of 2,422 `ENTRY` containers hold more than one `heading` leaf; the
  worst holds six. Entry `1f56cabc-ac33-5533-940a-5d54817f6794` (p259, label `'Actions'`, 83 leaves)
  contains three separate `Actions` headings and the actions of *three different creatures* — `Slam.`
  (Animated Armor), `Slash.` (Flying Sword), `Smother.` (Rug of Smothering).
- **Record larger than entry:** ≈500 entries are structural-role fragments (`Traits`/`Actions`/…) that
  belong to a creature record defined by a *sibling* entry.

Record membership is therefore a **sub-entry, order-dependent assembly** that must be explicitly accepted.
It cannot be derived from container nesting, container label, or entry identity. ADR-005d Decision 3
predicted this; the corpus confirms it at scale.

### B. Composite creature — canary 3 ✅ located

`Mummy` (entry `d8cf54fa-07cc-5309-bbc9-6d5c7b3d473a`, p309): 57 leaves = 1 heading + 55 `table_cell` +
1 `stat_field`. Siblings under subsection `Mummies`, in document order:

```
entry  p309  'Mummy'              57 leaves
entry  p309  'Actions'             2 leaves     → belongs to Mummy
entry  p309  'Mummy Lord'         14 leaves
entry  p310  'Traits'              2 leaves     ┐
entry  p310  'Actions'             2 leaves     │ → belong to Mummy Lord
entry  p310  'Reactions'           2 leaves     │
entry  p310  'Legendary Actions'   2 leaves     ┘
```

Only **document order** distinguishes which fragment belongs to which creature. There is no containment
edge to rely on. This is the accepted-assembly case the Issue requires and it is unambiguous only to a
human reviewer.

### C. Table-cell fragmentation is at **word** grain

15,715 `table_cell` leaves; mean 8.2 characters, median 5; **10,771 are a single word**; only 254 have
≥8 words. The Mummy ability grid arrives as:

```
'S tr 16' '+3' '+3'   'D ex 8' '−1' '−1'   'C on 15' '+2' '+2'
'I nt 6'  '−2' '−2'   'W IS 12' '+1' '+3'  'C ha 12' '+1' '+1'
```

and one creature action sentence is twelve leaves:

```
'Smother.' 'Melee' 'Attack' 'Roll:' '+5,' 'reach' '5 ft. Hit:' '10' '(2d6' '+ 3) Bludgeoning' 'damage.'
```

Consequence: one typed fact draws primary provenance from many word-grain spans, and one governing-prose
surface is many chunks. Both are supported by the current schema (`prose_binding_target_key` includes the
chunk, so several bindings per component are legal) — but the **edge volume** is large; see §3.

### D. Several facts share one leaf, and only one may claim it primarily

Every spell's descriptor line is a single `paragraph` leaf, e.g. Wish:

```
'Level 9 Conjuration (Sorcerer, Wizard) Casting Time: Action Range: Self Components: V
 Duration: Instantaneous'
```

`validation.py::_validate_provenance` rejects `span … conflicting primary claims` — at most one element
may claim a span with `PRIMARY` role. So the accepted **span partition must be cut at phrase granularity**
wherever more than one typed fact is drawn from one leaf. The partition granularity is therefore driven by
fact granularity, not by semantic disposition alone. This is an authoring-cost and policy-documentation
finding, **not** a schema defect.

### E. Canary 1 — Wish ✅ (entry `c940a3ab-…`, p175, 27 leaves)

Structured, fixed consequences present and enumerable: `Object Creation` (one object ≤ 25,000 GP,
≤ 300 feet), `Instant Health` (≤ 20 creatures, all Hit Points), `Resistance` (≤ 10 creatures, one damage
type), `Spell Immunity` (≤ 10 creatures, 8 hours), `Sudden Learning`, `Roll Redo` (reroll within the last
round, with Advantage/Disadvantage).
Prose-bound: `Reshape Reality` — *"You may wish for something not included in any of the other effects.
To do so, state your wish to the GM as precisely as you can"* — plus the post-cast stress clause.
`MIXED` handling. No free-form outcome becomes executable.

### F. Canary 2 — illusion ✅

38 entries carry `Illusion` school. Cleanest instances: `Phantasmal Force` (p151, 4 leaves),
`Phantasmal Killer` (p152, 5 leaves), `Major Image` (p147, 6 leaves). Each pairs a typed check/DC source
(target's check against the caster's spell save DC → `AbilityCheckFact(ability, DcKind.SPELL_SAVE_DC)`)
with contextual GM judgement about what the illusion can plausibly do and when the target "realizes the
phantasm is an illusion". Representable with the **existing** `AbilityCheckFact`/`DcKind` families.

### G. Canary 4 — spell-scoped creature ✅ located (both halves)

*Embedded stat block:* `Otherworldly Steed` (entry, p131, **35 leaves**) with its own sibling `Traits`
(2), `Actions` (2), `Bonus Actions` (2) entries, immediately following the spell `Find Steed` (p130,
12 leaves), whose body reads *"…`Otherworldly Steed` stat block."* A second instance sits at p136 for
the spell `Giant Insect` (p135) — and its container label is a **run-on line**:
`"slot's level for the spell's level in the stat block. Giant "` (24 leaves). The Spells section carries
4 `Actions`, 3 `Traits`, and 2 `Bonus Actions` structural entries in total.

*External reference:* at least 8 spell leaves say *"see 'Monsters' for the stat block(s)"* —
p108/p109 (Animate Dead), p121 (Animate Objects, Conjure Minor Elementals), p130, p135/p136.

Both halves of the canary have real instances. Note the corrupted label at p136: **membership cannot be
derived from container labels**, only accepted.

*(An initial AC/HP/STR co-occurrence heuristic reported zero spell-scoped stat blocks. That was the
heuristic's fault, not the corpus's — the stat blocks are separate sibling entries, not text inside the
spell entry. Corrected on inspection.)*

### H. Canary 5 — progression tables ✅

683 table containers; 27 carry `Level`/`Features` in their header-derived label. Instances:
`'Level | Class Features | Cantrips | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9'` (p31, p36, p41, …),
`'Barbarian | Features'` (p28), `'Druid Level | Circle Spells'` (p46),
`'Level | Experience Points | Proficiency Bonus'` (p23), `'Level or CR | Bonus'` (p8).
Cells are word-grain (`'Up to 4'`, `'+2'`, `'5–8'`, `'+3'`, …). The **spell-slot columns are two-dimensional**
— (class level × slot level → count) — which the current `ProgressionEntryFact` cannot index. See §3.

### I. Canary 6 — scoped collision ✅

63 colliding `ENTRY` labels. Cross-record collisions with genuinely different targets:

| Label | Instances | Pages (sample) |
|---|---:|---|
| `Actions` | 220 | 109, 131, 136, 166, 232, 256… |
| `Traits` | 159 | 131, 136, 166, 232, 256… |
| `Level 4: Ability Score Improvement` | 12 | 29, 32, 37, 43, 48, 51, 55, 59 |
| `Level 19: Epic Boon` | 12 | 30, 33, 38, 43, 48, 52, 55, 59 |
| `Level 1: Spellcasting` | 7 | 32, 36, 41, 54, 57, 64, 77 |
| `Level 5: Extra Attack` | 5 | 29, 48, 51, 55, 59 |
| `Armor Class` | 4 | 7, 25, 177, 254 |
| `Proficiency Bonus` | 4 | 6, 7, 25, 256 |

`Armor Class` at p177 (Rules Glossary) and p254 (Monsters) are different authorities under one name —
exactly the case `ReferenceDraft.scope_key` exists for.

### J. Canary 7 — supporting authority ✅

14 leaves begin with `Example`/`Examples` (p9 `'Example Uses'`, p180 ×2, plus in-body examples at p10,
p103). 36 leaves carry a `"see …"` cross-reference (p6 ability-check naming, p15 *"see the next
section"*, p19 *"See the 'Starting…'"*). 2,863 represented `heading` leaves, 263 of them outside any
`ENTRY`. Ample real instances for `SUPPORTING_AUTHORITY` spans that are preserved rather than discarded.

### K. Non-`ENTRY` rules ✅

1,323 represented leaves sit outside every `ENTRY`. Concentration: Creation 269 (in tables),
Monsters A–Z 177 (in subsections), Classes 164, Equipment 159, Playing the Game 109 (153 total).
Example: the whole `Rhythm of Play` procedure at p5 — *"1: The Game Master Describes a Scene."*,
*"2: The Players Describe What Their Characters Do."*, *"3: The GM Narrates the Results…"* — is
non-`ENTRY` paragraphs under a subsection. `GENERAL_RULE` records must assemble from subsection and table
membership, with no entry to anchor them.

### L. Free-standing and lookup tables ✅

683 tables, 512 distinct labels, 54 colliding. Distribution of non-`ENTRY` table leaves: Creation 269,
Classes 164, Equipment 159, Playing the Game 109, Rules Glossary 66, Magic Items 20, Spells 11, Blocks 10.

### M. Equipment / magic items

165 Equipment + 286 Magic Items named entries. Weapon *properties* are their own entries
(`Ammunition`, `Finesse`, `Heavy`, `Light`, …, p89) — rule records — while the weapon *rows* (cost,
damage, weight, properties) live in tables. This is a record-kind judgement (`GLOSSARY_RULE` vs
`EQUIPMENT`), not a missing kind.

### N. Rules Glossary

155 entries, 2–8 leaves each, almost entirely paragraphs: `Ability Check`, `Ability Score and Modifier`,
`Action`, `Advantage`, `Alignment`, `Ally`, `Area of Effect`, `Armor Class`, `Armor Training`,
`Attack [Action]`, `Attack Roll`, … The cleanest assembly shape in the corpus.

### O. Source-text artifacts that bear on authoring (5c-owned; **out of 5d scope**)

- Top-level section labels split across lines: `'Index of Stat'` + `'Blocks'`, `'Character'` +
  `'Creation'` — 18 section containers for ≈15 real sections.
- Broken intra-word glyph spacing in content: `'S tr 16'`, `'W IS 12'`, `'C ha 12'`,
  `'i MprovisEd w Eapons'`.
- A run-on line became a container label (p136, canary 4).

Issue #137 puts "Changes to 5c extraction, leaf segmentation, containers, reconciliation, publication, or
identity" **out of scope**. 5d must assemble around these, and the semantic policy's canonicalization
(which reuses 5c's `normalize`) must be checked against them at authoring time.

---

## 3. Schema-pressure findings

Adapter capability did **not** influence any judgement below. No family was proposed, widened, or withheld
because of what the bounded-d20 adapter can or cannot execute (ADR-005d Decision 1; #137 contract 4).

### 3a. Already sufficient

| Element | Verdict | Evidence |
|---|---|---|
| `RecordKind` (15 values) | Sufficient as observed | Every observed domain maps: `CREATURE`, `SPELL`, `CLASS`, `CLASS_FEATURE`, `EQUIPMENT`, `MAGIC_ITEM`, `CONDITION`, `GLOSSARY_RULE`, `GENERAL_RULE`, `GAMEPLAY_TOOL`, `SPECIES`, `BACKGROUND`, `FEAT`, `CHARACTER_CREATION`, `CHARACTER_ADVANCEMENT`. No shape needed a 16th. |
| `RelationshipKind` (3) | Sufficient as observed | `SCOPED_WITHIN` covers canary 4; `GRANTS` covers canary 5; `PREREQUISITE` covers feats/multiclassing. Creature-fragment assembly (§2B) is **record membership**, not a relationship. |
| `ComponentHandling` + `IRREDUCIBILITY_REASONS` (6) | Sufficient as observed | Wish → `open_ended_effect` + `gamemaster_latitude`; illusion → `subjective_judgment` + `contextual_applicability`; Gameplay Toolbox → `gamemaster_latitude`. No observed shape lacked a reason. |
| `NON_MECHANICAL_REASONS` (5) | Sufficient as observed | Contents (23 leaves) → `navigation_only`; Legal Information (5) → `legal_licensing`; the single `attribution` leaf → `governed_attribution`. |
| `AbilityCheckFact` + `DcKind` | Sufficient | Canary 2, and creature saving throws. `DcKind` already names the source rather than inventing a number. |
| `ProvenanceClaim` / roles / `ProseBindingDraft` multiplicity | Sufficient | Several bindings per component are legal because `prose_binding_target_key` carries chunk + reason. |
| Override/patch layer (`patches.py`, `targets.py`) | Sufficient, no change needed | Patches rebuild facts through `fact_from_payload`, so new families flow through automatically. |

### 3b. Concrete new closed families or fields apparently required

Each is grounded in observed corpus text, and each has a named counterpart in #137 contract 3's required
family groups.

1. **Dice term** — a closed `(count, faces, modifier)` form. Prerequisite for 2, 3, and 8.
   Evidence: `'HP 58 (9d8'`,`'+'`,`'18)'`; `'(2d6'`,`'+ 3) Bludgeoning'`; *"increases by 1d10 for each
   spell slot level above 4"*. Contract 3: *"dice"*.
2. **Attack** — kind (melee/ranged, weapon/spell), to-hit bonus, reach/range.
   Evidence: `'Melee'`,`'Attack'`,`'Roll:'`,`'+5,'`,`'reach'`,`'5 ft.'`. Contract 3: *"attacks"*,
   *"range/reach/area/origin"*.
3. **Damage** — dice term + damage type + stated average.
   Evidence: `'10'`,`'(2d6'`,`'+ 3) Bludgeoning'`,`'damage.'`. Contract 3: *"damage"*.
4. **Creature defence block** — AC, HP, hit dice, Speed, Initiative, CR, size/type/alignment,
   vulnerabilities / immunities / condition immunities, senses, languages, proficiency bonus.
   Evidence (Mummy): `'AC 11'`,`'Initiative'`,`'−1'`,`'(9)'`,`'HP 58 (9d8'`,`'Speed 20'`,`'ft.'`,
   `'Vulnerabilities'`,`'Fire'`,`'Immunities'`,`'Necrotic,'`,`'Poison;'`,`'Charmed,'`.
   Contract 3: *"creature/stat-block … authority"*, *"resistances/immunities/vulnerabilities"*.
5. **Creature save modifier** — either a `save_modifier: int | None` field on
   `CreatureAbilityScoreFact` or a sibling family. Evidence: the grid carries **three** columns per
   ability (score, MOD, SAVE) and they diverge — Mummy Wisdom is `12 / +1 / +3`. The save bonus has no
   home in the current family, and it is a trust-relevant value.
6. **Spell descriptor completion** — casting time, range/area, components (V/S/M + material), duration.
   `SpellDescriptorFact`'s own docstring says these are *"deliberately absent … Until those families are
   justified by accounting, that authority is prose-bound."* Accounting now justifies them: **366** spell
   entries each carry the line. Contract 3: *"timing, targeting, and space"*, *"spell … authority"*.
7. **Action economy and timing** — action / bonus action / reaction + trigger; duration, concentration,
   recurrence. Evidence: `'Casting Time: Action'`, `Bonus Actions` entries ×71, `Reactions` ×25,
   `'Duration: Concentration, up to …'`. Contract 3: *"action economy, triggers, reactions … duration/
   concentration, recurrence"*.
8. **Condition application / typed state effect** — the 15 Rules Glossary conditions and their
   application by spells and creature actions. Contract 3: *"conditions … typed state effects"*.
9. **Spell-slot progression** — the class table's slot columns are `(class_level, slot_level, count)`.
   `ProgressionEntryFact(level, entitlement_key, quantity)` can express this **only** by encoding the slot
   level into `entitlement_key`, which is precisely the stringly-typed escape hatch ADR-005d Decision 4
   forbids. Either a typed second index on the existing family or a `spell_slot_progression` family is
   required. **This is the one place where a lazy choice produces a Decision-4 violation.**
10. **Resources and rest cadence** — spell slots, Hit Dice, Long/Short Rest, Recharge, limited uses.
    Contract 3: *"resources, recharge/rest cadence"*.
11. **Equipment descriptors** — cost, weight, damage, weapon properties, armour AC formula, don/doff.
    Contract 3: *"equipment … authority"*.

### 3b-bis. Coverage against contract 3's capability floor

Contract 3 requires the first projection to be *"capable of representing at least"* five named family
groups. The eleven proposals above are the **observed-pressure subset**, not the contract's full list.
This is the reconciliation:

| Contract 3 group | Named items | Status after §3b |
|---|---|---|
| Roll and resolution | dice, attacks, saves, checks, **contests**, DC sources, **advantage/disadvantage**, **critical changes**, **explicit probability**, **random-table selection** | Items 1–3 + existing `AbilityCheckFact`/`DcKind` cover dice, attacks, saves, checks, DC sources. **Contests, advantage/disadvantage, critical changes, explicit probability, random-table selection are not yet proposed.** |
| Timing, targeting, space | action economy, triggers, reactions, range/reach/area/origin, **targeting restrictions**, duration/concentration, recurrence, **movement** | Items 2 and 7 cover action economy, triggers, reactions, range/reach, duration/concentration, recurrence. **Targeting restrictions and movement are not yet proposed.** |
| Effects and state | damage, **healing**, resistances/immunities/vulnerabilities, conditions, resources, recharge/rest cadence, typed state effects | Items 3, 4, 8, 10 cover damage, resistances/immunities/vulnerabilities, conditions, resources, recharge/rest. **Healing is not yet proposed** (Wish's `Instant Health` is a direct instance). |
| Identity and relationships | typed references, **membership/classification**, prerequisites, **eligibility**, **choices**, **sequencing**, dependencies, **scaling**, progression | `ReferenceDraft` + `RelationshipKind` cover references, prerequisites, dependencies; item 9 covers progression. **Membership/classification, eligibility, choices, sequencing, and scaling are not yet proposed.** |
| Domain descriptors | spell, creature/stat-block, equipment, class, species, background, feat, level-progression | Items 4, 5, 6, 9, 11 cover spell, creature, equipment, level-progression. **Class, species, background, and feat descriptors are not yet proposed.** |

Two of the gaps have direct corpus evidence already in hand:

- **Membership/classification — spell-list tables.** 73 table containers labelled
  `'Spell | School | Special'`, **all in the Classes section**, are the class spell lists. This is exactly
  the "spells and spell-list tables" shape #137's Required Real-Corpus Proof names, and it is a
  membership relation between a class record and many spell records — not a `RelationshipKind` value that
  exists today (`GRANTS` is level-indexed entitlement, not list membership).
- **Scaling.** The `"Using a Higher-Level Spell Slot."` clause on nearly every spell (see §3e).

One gap could **not** be confirmed in this checkpoint: **random-table selection**. Of the 683 table
containers, **zero** carry a `dN` column header in their label, and the 8 Gameplay Toolbox tables have
badly corrupted labels (`'levels by | increasing the damage and | the save DC, | as'`). Whether the SRD's
`dN`-indexed random tables are present under other labels was not established. Flagged, not claimed.

**Recommendation (for review, not a decision):** the authoring PR proposes the eleven families in §3b
plus healing, advantage/disadvantage, and list-membership — the three with unambiguous instances above —
and explicitly defers the remainder to batch-driven accounting, on the record that contract 3's
*"capable of representing"* obligation must be met **no later than full-corpus closure (B7)**, not at the
authoring PR. Deferral here has a deadline, and the deadline is what makes it honest rather than a
narrowing of completed 5d (a Boundary Stop condition).

### 3c. Shapes honestly requiring prose-bound treatment (with proposed reasons)

| Shape | Instance | Proposed reason code(s) | Handling |
|---|---|---|---|
| Open-ended wish effect | Wish → `Reshape Reality`, p175 | `open_ended_effect` (+ `gamemaster_latitude`) | `MIXED` |
| Post-cast stress clause | Wish, p175 | `fiction_dependent_consequence` | `MIXED` (probability may be typed) |
| Illusion plausibility / realisation | `Phantasmal Force` p151, `Major Image` p147 | `subjective_judgment`, `contextual_applicability` | `MIXED` |
| Configurable ward effects | `Guards and Wards` p137 (43 leaves), `Glyph of Warding` p136 (14), `Forbiddance` p133 (11), `Geas` p135 (11) | `open_ended_effect`, `contextual_applicability` | `MIXED` |
| GM-facing procedures | Gameplay Toolbox, 72 entries / 695 leaves | `gamemaster_latitude` | `PROSE_BOUND` |
| Procedural play rules | `Rhythm of Play`, p5 | `contextual_applicability` | `PROSE_BOUND`, or `SUPPORTING_AUTHORITY` spans with no component |
| Natural-language exceptions in class features | `Level 1: Spellcasting` ×7 and siblings | `natural_language_exception` | `MIXED` |

None of these is a backlog state; each is an affirmative judgement about source meaning, as contract 2
requires.

### 3d. Unresolved representational pressure (surfaced, not resolved)

**P1 — Prose grain versus span grain.** Every chunk is exactly one whole leaf (0 partial-coverage edges
measured), so a `ProseBindingDraft` binds a *whole leaf*, while classification and provenance are
sub-leaf. A component whose governing prose is one clause inside a paragraph can only bind the entire
paragraph, and the GameMaster view (`views.py::_resolve_prose`) returns that entire chunk's text. This does
**not** affect canaries 1 or 2 — their prose-bound clauses happen to be whole leaves — but it is a fidelity
question that will recur across the corpus. Whether whole-leaf grain is accepted fidelity, or prose
bindings need a subspan, is not decided here.

**P2 — Provenance edge volume.** One creature action ≈ 12 word-grain leaves; 15,715 of 28,109 represented
leaves are word-grain table cells. Full-corpus provenance-edge counts plausibly land in the 10⁵ range.
No ceiling is stated anywhere, and persistence/identity cost at that scale is unmeasured. Diagnostic, but
it should be sized before a batch plan is committed to.

**P3 — `stat_field` is not a reliable stat-block signal.** 2,121 leaves carry the type, but samples
include ordinary rules prose (`'Speed. Rather than moving foot by foot, move'` p13,
`'Saving Throws.'` p22) alongside genuine grid headers (`'MOD SAVE MOD SAVE MOD SAVE'` p309). Assembly
must not key on leaf type.

**P4 — Two-dimensional table facts as a general shape.** Item 9 above is the class-table instance;
equipment tables (cost/damage/weight/properties per row) are the same shape. Whether the union grows one
family per table shape, or gains a typed row/column-indexed family, is an open modelling question that
will recur across batches B5 and B6.

### 3e. Conflicts with the Issue, ADR, Known Unknowns, or existing ownership

- **No conflict** between the §3b additions and #137 contract 3 or ADR-005d Decision 4. Both explicitly
  authorise adding a typed family when accounting surfaces one; Decision 4's exact words are *"A new
  mechanical family requires a typed schema and tests or an honest prose-bound classification."*
- **Known Unknown touched — do not resolve.** `known_unknowns.md` → *"Parameterized adjustments
  (spell-slot-level upcasting, variable-amount resource recovery)"*. Nearly every spell carries a
  `"Using a Higher-Level Spell Slot."` clause (`Phantasmal Killer`: *"The damage increases by 1d10 for
  each spell slot level above 4"*; `Find Steed` / `Giant Insect`: *"Use the spell slot's level for the
  spell's level in the stat block"*). **Representing** that clause is 5d work — contract 3 lists
  *"scaling, and progression"* in scope. **Defining the typed adjustment parameter** (a
  `chosen_slot_level`-shaped `RollAdjustmentOption` extension) is the open Known Unknown, owned by an
  ADR-015b amendment. Recommended boundary: represent the clause in 5d; do not define the parameter here.
  Do not over-defer the representation.
- **Issue obligation currently unmet.** #137 requires *"Update `known_unknowns.md` to show typed Rules
  Package authority as in progress until the complete issue lands."* The file's Rules Package entry still
  reads *"Implementation remains pending CRD Issue 5d"* and records neither #137 as in progress nor PRs
  #139/#149/#150. This needs to be assigned to a 5d PR.
- **No ownership conflict** with CRD Issue 2b or 15c was observed. Nothing above decides character-sheet
  storage or adapter capability.

### 3f. Provisional classification of every proposal

**These are recommendations for external review, not accepted decisions.**

| # | Proposal | Classification | Evidence for the classification |
|---|---|---|---|
| 1–4, 6–8, 10, 11 | New `FactFamily` members (dice, attack, damage, creature defence, spell descriptors, timing, conditions, resources, equipment) | **Implementation modelling already authorized by Issue 5d** | Contract 3 names each family group verbatim as something the first projection *"must be capable of representing"*; Decision 4 authorises adding a typed family. |
| 5 | `save_modifier` field on `CreatureAbilityScoreFact` (or sibling family) | **Implementation modelling already authorized** | Same authority; the field is intrinsic to the observed three-column grid, and the value diverges from the derived modifier. |
| 9 | Spell-slot progression indexing | **Implementation modelling already authorized** — but flag in Architecture Notes | Authorised as a family; flagged because the alternative (encoding into `entitlement_key`) would violate Decision 4, so the choice is contractually constrained, not free. |
| — | New `RecordKind` value | **None required.** If one becomes required → **specification reconciliation required** | The vocabulary is declared closed and enumerated in contract 3 with *"must cover"*; widening it is a visible change to a closed vocabulary and belongs in Architecture Notes at minimum. |
| — | New `RelationshipKind` value | **Implementation modelling** — but likely unnecessary | Creature-fragment assembly is record membership; `SCOPED_WITHIN` already covers the nested-record case. Add only if a batch proves a real gap. |
| — | New `NON_MECHANICAL_REASONS` or `IRREDUCIBILITY_REASONS` entry | **Specification reconciliation required** | Contract 2 requires the catalogs stay *"closed and identity-bound"*; `semantic_policy_hash()` is identity-bearing and `oracle.py` states that a policy change re-fails **every** committed oracle until re-review. None appears required. |
| P1 | Prose-binding sub-span grain | **Owner Decision required** (only if pursued) | Contract 3 fixes *"Exact governing prose resolves through the authoritative 5c `RuleChunk` source"*; changing the grain touches the 5c seam and ADR-005d Decision 3. |
| — | Upcasting / variable-resource **parameter contract** | **Known Unknown — defer** | `known_unknowns.md` "Parameterized adjustments" requires an owner decision and an ADR-015b amendment *before* implementation. |
| — | Representation of the upcast **clause** | **Implementation modelling already authorized** | Contract 3 lists *"scaling, and progression"* in 5d representation scope. |
| — | Whether any family is adapter-executable | **Downstream-owned (CRD Issue 15c) — defer** | Decision 1 and contract 4; capability manifest and certification are 15c's. |
| — | `known_unknowns.md` 5d status update | **Specification reconciliation required** | Directly mandated by #137's Downstream Seams section and currently unmet. |
| P2 | Provenance-edge volume ceiling | **Known Unknown / to defer with measurement** | No authority states a ceiling; this is an engineering-sizing question, not a semantic one. Measure before the batch plan is fixed. |

---

## 4. Natural content batches

Basis: reference closure, record-assembly difficulty, and semantic dependency — not a target PR count.
Referenced-by-everything material comes first; the hardest assembly shape comes when the vocabulary it
needs already exists.

| # | Batch | Named entries | Leaves | Introduces | Depends on |
|---|---|---:|---:|---|---|
| **B1** | Rules Glossary + conditions | 155 | 1,024 | The reference-target vocabulary everything else cites. Simplest shape (2–8 paragraph leaves each). | — |
| **B2** | Playing the Game (core resolution) | 91 | 640 (incl. 153 non-`ENTRY`) | First non-`ENTRY` record assembly (§2K). | B1 |
| **B3** | Spells | 366 | 2,308 | Canaries 1, 2, and the outward half of 4. Descriptor + effect families. | B1; forward-references creatures |
| **B4** | Creatures (Monsters A–Z + Animals + Monsters) | 235 + 95 + 28 named, ≈500 structural-role | 10,699 | Canary 3: composite assembly, word-grain cells, the Mummy/Mummy Lord ordering problem. Closes B3's creature references and canary 4's inward half. | B1, B3 |
| **B5** | Classes + progression | 345 | 7,008 | Canary 5 (progression tables) and canary 6 (the 12×-repeated feature names). | B1, B3, and item 9 of §3b |
| **B6** | Origins, Feats, Creation, Equipment, Magic Items, Gameplay Toolbox | 26+22+36+165+286+72 | 6,383 | No new assembly shape — grouped for that reason. | B1, B3, B5 |
| **B7** | Residue and closure | — | 47 + any unclaimed | Contents, Legal Information, fragmented section headings, the attribution leaf, and every leaf no earlier batch claimed. | all |

**Order:** B1 → B2 → B3 → B4 → B5 → B6 → B7.

Every batch before B7 leaves the projection unpublishable **by construction**: the gate compares the
accepted classification against the release's entire `REPRESENTED` population and reports
`POPULATION_MISMATCH` per uncovered leaf, with no count or threshold in the decision. That is the correct
intermediate state and it is already how `test_production_release.py` proves an incomplete projection is
refused.

**Caveat, stated as a diagnostic:** B4 and B5 are each larger in leaves than B1+B2+B3 combined. If review
capacity rather than structure forces a split, split **inside** B4 or B5 on whole-record boundaries —
never mid-creature and never mid-class — so reference closure is never broken by the split itself.

---

## 5. Proposal and acceptance workflow

The lowest-complexity repository-native workflow is **almost entirely existing machinery**. The honest
finding is that very little new needs to be built.

### The three stages

**Machine proposal.** A *disposable, uncommitted* tool run — the same class of thing as the analysis
scripts used for this checkpoint. It lives in `scripts/`, reads the bound release, and emits (a) a
candidate oracle JSON in exactly `oracle.load_oracle`'s shape and (b) a human-readable semantic diff. It
writes to a working path, never to `oracles/`. `oracles/README.md` already states the invariant:
*"Nothing in `src/` writes to this directory."*

**Human semantic review.** Review scope and semantic-diff evidence already have a typed home:
`AcceptanceBatch(batch_id, rule, resolved_scope, diff, semantic_diff_hash)` in `models.py`. Its design
already does exactly what the checkpoint asks for — `rule` is retained as *evidence, never re-run*
(*"a selector re-evaluated against changed inputs would resolve to a different set than the reviewer
saw"*), `resolved_scope` is the exact accepted span set, `diff` is the full canonical diff retained in
full, and `semantic_diff_hash` identifies it without substituting for it.
`accounting.validate_acceptance` already enforces that a batch retains its diff rather than only a digest.
**No new type is required for review scope or diff evidence.**

**Explicit acceptance.** Acceptance is the reviewed commit of the accepted authority, plus the
classification ledger's `AcceptanceRecord` / `AcceptanceBatch` rows. The proposed/accepted boundary is
already load-bearing in code: `ReviewState.PROPOSED` yields `UNREVIEWED_RESIDUE` and blocks publication,
a span with no `AcceptanceRecord` blocks publication, and only committed accepted bytes count as
authority. Silence is not acceptance, exactly as contract 2 requires.

### Open design question the authoring PR must answer: where the committed *build inputs* live

The oracle file **cannot** be the build's accepted input artifact, and the code says so:

- `oracle_payload` carries binding, policy, spans, representation, and obligations — and deliberately
  **omits acceptance evidence**. `gate._accepted_identity` constructs its `ClassificationLedger` with
  `batches=()` and `acceptances=()`, because review process is not identity-bearing.
- But the gate simultaneously requires an `AcceptanceRecord` for every span in **reconstructed persisted
  state**, or it reports `UNREVIEWED_RESIDUE`.

So the accepted acceptance evidence has to reach the build from somewhere that is not the oracle.
Contract 4 names five committed accepted input categories the production build consumes — semantic policy
and canonicalization; the classification ledger; record assembly and membership; components/facts/prose
bindings/obligations/provenance; and reference scope, aliases, and exact targets. Of these, only the
policy currently has a committed home (`policy.py`, frozen in source).

**This checkpoint does not decide the shape.** The question the authoring PR must answer explicitly is:

1. **One artifact or two?** A single committed accepted-inputs file per batch from which the oracle is
   *also* loaded, or two files — build inputs (with acceptance evidence) and oracle (without) — committed
   side by side.
2. If **two**, note that the gate's element-level multiset comparison plus the single identity comparison
   (`_accepted_identity` vs the persisted projection UUID) is *exactly* the mechanism that catches drift
   between them, so two artifacts are not an unguarded duplication. What must be preserved is that the
   oracle is never generated **from the candidate or from persisted state** — deriving it from a
   *committed sibling input file* does not breach independence, but deriving it from the build does.
3. If **one**, the loader must strip acceptance evidence before oracle identity is computed, or a
   re-review that changes nothing semantic would remint the projection UUID and violate acceptance
   criterion 11.

Recommendation offered for review, not adopted: **two committed files per batch under a new
`accepted_inputs/` sibling of `oracles/`**, because it keeps `oracle.py`'s strict loader and its
"reads committed bytes and nothing else" property untouched, and it makes the drift check a real
comparison rather than a tautology.

### Oracle independence — already structural, and what must not break it

`oracle.py` imports no session, no ORM, and nothing from `persistence`, `raw_state`, or `gate`;
`load_oracle` reads committed bytes and nothing else; and the declared semantic policy comes from the
*file*, never from current `policy` constants — so a policy change re-fails every committed oracle until
a reviewer re-accepts it. `_accepted_identity` in `gate.py` derives the expected projection UUID from the
oracle alone.

The one rule the authoring PR must not break: **the proposal tool must not become a path by which a
candidate can generate the oracle that will judge it.** Recommended guard — keep the tool in `scripts/`,
and keep a test asserting that nothing under `src/` writes to `oracles/`.

### What belongs in the authoring/schema PR

- New closed `FactFamily` members with their intrinsic invariants, JSON builders, and per-family tests
  (`representation.py` is already factored one-checker-and-one-builder per family, so this is additive).
- Any `RecordKind` / `RelationshipKind` widening actually required, recorded explicitly in Architecture
  Notes.
- Persistence round-trip and reconstruction coverage for the new families (`persistence.py`,
  `test_fact_field_types.py`, `test_persisted_evidence.py`).
- Override-path coverage proving new families flow through `patches.py` (they rebuild via
  `fact_from_payload`, so this is a test obligation, not new code).
- The proposal tool in `scripts/` plus its output format.
- **The committed accepted-build-input format and its strict loader** (the open question above), with the
  same missing-key / extra-key / undeclared-enum strictness `oracle.load_oracle` already applies.
- Short workflow documentation extending `oracles/README.md`.
- **No committed production oracle content**, and no change to `POLICY`/catalog contents unless §3f's
  reconciliation path is taken first.

### What must remain outside it

- **Accepted-content batches (B1–B6):** the oracle JSON slices, the classification ledger, record
  assembly, and per-batch review evidence.
- **Full-corpus closure (B7):** the residue batch and the first oracle stating the complete population —
  the first point at which the gate can pass.
- **Final cutover:** activation of the complete projection; removal of `MechanicalEntity`, `SpellEntity`,
  `ConditionEntity`, `StatBlockEntity`, `ActionEntity`, `ItemEntity`, `EntityData`, the ORM/table, and
  legacy-only callers; removal of the legacy `rp_overrides` chunk-targeting prose path; and the
  `known_unknowns.md` status update. #137's Boundary Stop bars all of this from earlier PRs.
  Useful fact for that PR: a fresh production build writes **0 rows** to both `rp_mechanical_entities`
  and `rp_overrides`, so legacy removal is a code/migration change, not a data migration.

---

## 6. Feasibility and boundary verdict

### Is the authoring/workflow/schema unit reviewable as one PR?

**Yes — conditional on it committing no production oracle content.** Concrete reasons:

- the schema work is additive to a closed union whose validators and builders are already factored
  one-per-family, so each family is an independently reviewable unit;
- the proposal tool is a script, not a service or a new subsystem;
- the acceptance machinery (`AcceptanceBatch`, `AcceptanceRecord`, `ReviewState`, oracle loading,
  `UNREVIEWED_RESIDUE`) already exists and needs no new types;
- the override layer needs no code change at all.

**One concrete risk, not a blocker:** ≈10 new fact families is a large diff. If review capacity forces a
split, the natural cut is **(a) stat-block families** (dice, attack, damage, creature defence, creature
save) and **(b) descriptor families** (spell descriptors, timing, conditions, resources, equipment,
progression). That split has no semantic dependency in either direction, so it is a review-capacity
choice rather than a structural requirement.

**No structural reason was found** that prevents one PR.

### Items that would block implementation until dispositioned

| # | Item | Type |
|---|---|---|
| 1 | **Prose-binding grain** — whole-leaf (measured: 0 partial-coverage edges) vs subspan. Needs either an explicit acceptance of whole-leaf fidelity or an Owner Decision. Touches contract 3 and Decision 3. | Owner Decision / disputed semantic |
| 2 | **Spell-slot progression shape** — typed second index vs new family. Doing it the easy way (encoding into `entitlement_key`) is a direct ADR-005d Decision 4 violation, so the choice is contractually constrained. | Specification-constrained modelling |
| 3 | **Upcasting boundary** — confirm: represent the `"Using a Higher-Level Spell Slot"` clause in 5d, leave the typed adjustment parameter to the ADR-015b amendment. | Known Unknown — must not be resolved here |
| 4 | **`known_unknowns.md` 5d status** — issue-mandated update, currently unmet; needs assigning to a PR. | Specification reconciliation |
| 5 | **ADR-005d Context figures** — "203 colliding names among 1,893" and "1,533 two-signal leaves" do not reproduce and have no committed definition. Recommend recording the definition or marking them superseded discovery measurements. | Documentation reconciliation (non-blocking) |
| 6 | **Provenance-edge volume (P2)** — unsized at word-cell grain; measure before fixing the batch plan. | Engineering sizing |
| 7 | **Committed build-input artifact (§5)** — the oracle omits acceptance evidence the gate demands, so a second committed input shape is required. One artifact or two, and where it lives. | Design decision the authoring PR must make explicitly |
| 8 | **Contract 3 capability floor (§3b-bis)** — ≈12 named family items have no proposal yet. Confirm that deferral to batch-driven accounting, with full-corpus closure as the deadline, is the accepted path. | Scope confirmation |

### Non-blocking, recorded for completeness

Source-text artifacts (§2O — broken glyph spacing, the run-on container label at p136, split section
headings) are 5c-owned and explicitly out of 5d scope. 5d must assemble around them, and the semantic
policy's canonicalization should be checked against them at authoring time. They are **not** a reason to
touch 5c.

### No conflict found with

ADR-005d Decisions 1–11 as amended (2026-07-30, 2026-08-01/03, 2026-08-08, 2026-08-09); #137 contracts
1–6 and acceptance criteria 1–25; ADR-005c and its operational-reliability amendment; ADR-0007, ADR-015,
ADR-018; the architecture invariants and business/access invariants in `CLAUDE.md`.

---

## Hard stop

This report is delivered for Owner/Codex review. **This checkpoint is not approved by its own author.**
No implementation, branch, commit, PR, schema change, test, or documentation change follows from it
until a new prompt carries the reviewed disposition of these findings.

*Analysis artifacts (corpus build + query scripts) were written to the session scratchpad and are
deliberately not committed. They are diagnostics, not proposed implementation.*
