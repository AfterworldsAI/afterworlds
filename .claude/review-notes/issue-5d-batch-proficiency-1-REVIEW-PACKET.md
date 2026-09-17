# `proficiency-1` review packet — CRD Issue 5d, first regular-section pilot

**Status: PROPOSED. Not accepted. Nothing in this branch accepts it.**

This packet is the human-readable half of an unaccepted proposal over
**SRD 5.2.1 > Playing the Game > Proficiency**. It exists so a reviewer can
check the proposal against the printed source without reading 54 KB of JSON,
and so the Owner's later semantic acceptance decision is made on the actual
reviewed artifact rather than on a summary of it.

The pilot's second purpose is to test the proposal/loading/coverage workflow
merged in PR #170 on a *regular section* — prose with headings, a table, and
outward citations — rather than on a Rules Glossary entry list. §9 reports what
that cost.

## 1. The artifact

| | |
|---|---|
| proposal | `.claude/review-notes/issue-5d-batch-proficiency-1-PROPOSAL.json` |
| generator | `.claude/review-notes/issue-5d-batch-proficiency-1-generator.py` |
| bytes | 54,507 |
| `proposal_identity` | `c941c262081eb2ba485ee6963b90c0a2bf79578662a2790baf703f5ed1cac219` |
| file sha256 | `b74b6056688a1a6a3750cd1271fa7af6eb670cc05c16b6bf5f8e68f2442dadfa` |
| proposal schema | `5d-proposal-2` |
| representation schema | `5d-representation-schema-13` |
| source | `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, printed pages 8–9 |
| binding | `5.2.1-corpus.36b786d8-fa2` / `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |

The generator is deterministic: re-running it produces byte-identical output
(verified by diffing against a retained first-run copy). Five of the six parts
of the release binding are re-derived from the PDF and asserted against the
accepted oracle's binding. The sixth, `persisted_corpus_digest`, is taken from
the accepted oracle's binding and not restated by this batch: it is a digest
over persisted corpus state — the reconstructed SQL ledger, members,
reconciliation, sources and the read-back vector logical state
(`corpus/bundle.py:329`) — none of which this batch reads or touches.

## 2. Scope

**One `SECTION` review unit, `proficiency-1-section`, over 30 leaves.**

The section's leaves are 31 in the 5c ledger. One — the running footer
`bda26fa3` on the page break between printed pages 8 and 9 — is excluded by 5c
from the represented population, so naming it in the unit would claim review of
source the accounting population does not contain. The generator asserts both
directions: the footer is *not* in the represented set, and all 30 named leaves
*are*.

**Why a SECTION unit and not a TABLE unit.** The obvious shape for this pilot
is a unit over the Proficiency Bonus table container `84b342e6`. That shape is
wrong here, and wrong in a way that would not have been visible from the
proposal: 5c represents the table's later rows — levels/CRs 17 through 30 —
**outside** the table container, as a single paragraph leaf `f848a0fb` in the
*subsection* container alongside the body prose. A table-scoped unit would have
reviewed a proficiency progression that stops at +5 and reported no gap. The
generator asserts this containment fact rather than trusting the identification
note: `f848a0fb`'s `container_path` equals the body paragraph's, and differs
from the table cells'.

No accepted content is touched. The generator proves disjointness against the
seven accepted batches directly: no span id in this proposal appears in the
accepted oracle's spans, and no leaf this proposal spans appears among the 337
leaves those batches accepted.

## 3. Coverage at a glance

| | count |
|---|---|
| leaves in the unit | 30 |
| leaves excluded by 5c (running footer) | 1 |
| proposed spans | 47 |
| — substantive | 35 |
| — supporting authority | 11 |
| — non-mechanical (`flavor_setting`) | 1 |
| headings excluded by the unit | 7 |
| leaves carried as supporting groups (no spans) | 4 |
| components | 13 |
| prose bindings | 23 |
| typed facts | 9 (8 bonus bands + 1 advantage) |
| expected rules on the unit | 22 |
| provenance claims | 50 |
| references | 2 |

Findings from the merged services, on this batch's scope:

* `validate_partition(..., require_complete=False)` per leaf — **0 findings**
* `validate_reason_codes` — **0 findings**
* `review_unit_violations` — **0 findings**
* `validate_representation` — **2 findings**, both the expected
  `unknown target record` for glossary citations whose target records are not
  yet authored (§7).

## 4. Source versus disposition

Every leaf, then every proposed span with its exact source text, then the full
bonus progression. Generated from the same tables the generator uses, so this
section cannot drift from the artifact.

### A. Every leaf in scope

| # | leaf | page | type | container | chars | spans |
|---|------|------|------|-----------|-------|-------|
| 1 | `e00cea37` | 8 | heading | Proficiency | 11 | heading (excluded) |
| 2 | `ce26a9f7` | 8 | paragraph | Proficiency | 889 | SUB:5, SUP:2, NON:1 |
| 3 | `34cf6220` | 8 | table_cell | Level or CR \| Bonus | 11 | supporting group -> proficiency_bonus_table |
| 4 | `2a6af63f` | 8 | table_cell | Level or CR \| Bonus | 5 | supporting group -> proficiency_bonus_table |
| 5 | `b002753c` | 8 | table_cell | Level or CR \| Bonus | 7 | SUB:1 |
| 6 | `69ae5a1b` | 8 | table_cell | Level or CR \| Bonus | 2 | SUB:1 |
| 7 | `8a6fc1a5` | 8 | table_cell | Level or CR \| Bonus | 3 | SUB:1 |
| 8 | `d58940db` | 8 | table_cell | Level or CR \| Bonus | 2 | SUB:1 |
| 9 | `515f45ef` | 8 | table_cell | Level or CR \| Bonus | 4 | SUB:1 |
| 10 | `19340146` | 8 | table_cell | Level or CR \| Bonus | 2 | SUB:1 |
| 11 | `9b1cee59` | 8 | table_cell | Level or CR \| Bonus | 5 | SUB:1 |
| 12 | `df4629be` | 8 | table_cell | Level or CR \| Bonus | 2 | SUB:1 |
| 13 | `f848a0fb` | 8 | paragraph | Proficiency | 53 | SUB:4, SUP:1 |
| 14 | `fcf9878a` | 8 | heading | The Bonus Doesn’t Stack | 23 | heading (excluded) |
| 15 | `940239fe` | 8 | paragraph | The Bonus Doesn’t Stack | 620 | SUB:3, SUP:2 |
| 16 | `192c232c` | 8 | heading | Skill Proficiencies | 19 | heading (excluded) |
| 17 | `5954cb89` | 8 | paragraph | Skill Proficiencies | 615 | SUB:4, SUP:1 |
| 18 | `e45739f5` | 9 | paragraph | Skill Proficiencies | 363 | SUB:1, SUP:1 |
| 19 | `bddf4800` | 9 | heading | Skill List | 10 | heading (excluded) |
| 20 | `9b012d75` | 9 | paragraph | Skill List | 155 | SUB:1 |
| 21 | `491ef243` | 9 | heading | Determining Skills | 18 | heading (excluded) |
| 22 | `91e1341f` | 9 | paragraph | Determining Skills | 142 | SUB:1 |
| 23 | `6269641e` | 9 | heading | Saving Throw Proficiencies | 26 | heading (excluded) |
| 24 | `6b6df866` | 9 | paragraph | Saving Throw Proficiencies | 540 | SUB:3, SUP:2 |
| 25 | `8a9c1d4c` | 9 | heading | Equipment Proficiencies | 23 | heading (excluded) |
| 26 | `b1d1ef1a` | 9 | paragraph | Equipment Proficiencies | 144 | SUB:1, SUP:1 |
| 27 | `6c8871c3` | 9 | paragraph | Equipment Proficiencies | 8 | supporting group -> weapon_proficiency |
| 28 | `3576be8e` | 9 | paragraph | Equipment Proficiencies | 179 | SUB:2 |
| 29 | `df4e6013` | 9 | paragraph | Equipment Proficiencies | 6 | supporting group -> tool_proficiency |
| 30 | `e9d9f35f` | 9 | paragraph | Equipment Proficiencies | 332 | SUB:2, SUP:1 |

### B. Every proposed span

| clause | leaf | kind | component | source text |
|--------|------|------|-----------|-------------|
| `main.flavor` | `ce26a9f7` | NON | - | Characters and monsters are good at various things. Some are skilled with many weapons, while others can use only a few. Some are better at understanding people’s motives, and others are better at unlocking the secrets of the multiverse. |
| `main.all_creatures` | `ce26a9f7` | SUB | proficiency_bonus_basis | All creatures have a Proficiency Bonus, which reflects the impact that training has on the creature’s capabilities. |
| `main.character_levels` | `ce26a9f7` | SUB | proficiency_bonus_basis | A character’s Proficiency Bonus increases as the character gains levels (described in “Character Creation”). |
| `main.monster_cr` | `ce26a9f7` | SUB | proficiency_bonus_basis | A monster’s Proficiency Bonus is based on its Challenge Rating (see “Rules Glossary”). |
| `main.table_pointer` | `ce26a9f7` | SUP | - | The Proficiency Bonus table shows how the bonus is determined. |
| `main.d20_test` | `ce26a9f7` | SUB | proficiency_bonus_application | This bonus is applied to a D20 Test when the creature has proficiency in a skill, in a saving throw, or with an item that the creature uses to make the D20 Test. |
| `main.spells` | `ce26a9f7` | SUB | proficiency_bonus_application | The bonus is also used for spell attacks and for calculating the DC of saving throws for spells. |
| `main.caption` | `ce26a9f7` | SUP | - | Proficiency Bonus |
| `cell.upto4` | `b002753c` | SUB | proficiency_bonus_table | Up to 4 |
| `cell.p2` | `69ae5a1b` | SUB | proficiency_bonus_table | +2 |
| `cell.5_8` | `8a6fc1a5` | SUB | proficiency_bonus_table | 5–8 |
| `cell.p3` | `d58940db` | SUB | proficiency_bonus_table | +3 |
| `cell.9_12` | `515f45ef` | SUB | proficiency_bonus_table | 9–12 |
| `cell.p4` | `19340146` | SUB | proficiency_bonus_table | +4 |
| `cell.13_16` | `9b1cee59` | SUB | proficiency_bonus_table | 13–16 |
| `cell.p5` | `df4629be` | SUB | proficiency_bonus_table | +5 |
| `later.header` | `f848a0fb` | SUP | - | Level or CR Bonus |
| `later.17_20` | `f848a0fb` | SUB | proficiency_bonus_table | 17–20 +6 |
| `later.21_24` | `f848a0fb` | SUB | proficiency_bonus_table | 21–24 +7 |
| `later.25_28` | `f848a0fb` | SUB | proficiency_bonus_table | 25–28 +8 |
| `later.29_30` | `f848a0fb` | SUB | proficiency_bonus_table | 29–30 +9 |
| `stack.once` | `940239fe` | SUB | bonus_does_not_stack | Your Proficiency Bonus can’t be added to a die roll or another number more than once. |
| `stack.example` | `940239fe` | SUP | - | For example, if a rule allows you to make a Charisma (Deception or Persuasion) check, you add your Proficiency Bonus if you’re proficient in either skill, but you don’t add it twice if you’re proficient in both skills. |
| `stack.scaling` | `940239fe` | SUB | bonus_does_not_stack | Occasionally, a Proficiency Bonus might be multiplied or divided (doubled or halved, for example) before being added. |
| `stack.expertise` | `940239fe` | SUP | - | For example, the Expertise feature (see “Rules Glossary”) doubles the Proficiency Bonus for certain ability checks. |
| `stack.once_each` | `940239fe` | SUB | bonus_does_not_stack | Whenever the bonus is used, it can be multiplied only once and divided only once. |
| `skill.definition` | `5954cb89` | SUP | - | Most ability checks involve using a skill, which represents a category of things creatures try to do with an ability check. |
| `skill.sources` | `5954cb89` | SUB | skill_relevance_sources | The descriptions of the actions you take (see “Actions” later in “Playing the Game”) specify which skill applies if you make an ability check for that action, and many other rules note when a skill is relevant. |
| `skill.gm_say` | `5954cb89` | SUB | skill_relevance_judgment | The GM has the ultimate say on whether a skill is relevant in a situation. |
| `skill.proficient` | `5954cb89` | SUB | skill_proficiency_application | If a creature is proficient in a skill, the creature applies its Proficiency Bonus to ability checks involving that skill. |
| `skill.without_a` | `5954cb89` | SUB | skill_proficiency_application | Without proficiency in a skill, a creature can still make ability checks involving |
| `skill.without_b` | `e45739f5` | SUB | skill_proficiency_application | that skill but doesn’t add its Proficiency Bonus. |
| `skill.example` | `e45739f5` | SUP | - | For example, if a character tries to climb a cliff, the GM might ask for a Strength (Athletics) check. If the character has Athletics proficiency, the character adds their Proficiency Bonus to the Strength check. If the character lacks that proficiency, they make the check without adding their Proficiency Bonus. |
| `list.skills_table` | `9b012d75` | SUB | skill_list | The skills are shown on the Skills table, which notes example uses for each skill proficiency as well as the ability check the skill most often applies to. |
| `determining.sources` | `91e1341f` | SUB | determining_skills | A character’s starting skill proficiencies are determined at character creation, and a monster’s skill proficiencies appear in its stat block. |
| `saves.bonus` | `6b6df866` | SUB | saving_throw_proficiency | Proficiency in a saving throw lets a character add their Proficiency Bonus to saves that use a particular ability. |
| `saves.example` | `6b6df866` | SUP | - | For example, proficiency in Wisdom saves lets you add your Proficiency Bonus to your Wisdom saves. |
| `saves.monsters` | `6b6df866` | SUB | saving_throw_proficiency | Some monsters also have saving throw proficiencies, as noted in their stat blocks. |
| `saves.class_minimum` | `6b6df866` | SUB | saving_throw_proficiency | Each class gives proficiency in at least two saving throws, representing that class’s training in evading or resisting certain threats. |
| `saves.wizard_example` | `6b6df866` | SUP | - | Wizards, for example, are proficient in Intelligence and Wisdom saves; they train to resist mental assault. |
| `equipment.sources` | `b1d1ef1a` | SUB | equipment_proficiency | A character gains proficiency with various weapons and tools from their class and background. |
| `equipment.two_categories` | `b1d1ef1a` | SUP | - | There are two categories of equipment proficiency: |
| `weapon.anyone` | `3576be8e` | SUB | weapon_proficiency | Anyone can wield a weapon, but proficiency makes you better at wielding it. |
| `weapon.attack_rolls` | `3576be8e` | SUB | weapon_proficiency | If you have proficiency with a weapon, you add your Proficiency Bonus to attack rolls you make with it. |
| `tool.checks` | `e9d9f35f` | SUB | tool_proficiency | If you have proficiency with a tool, you can add your Proficiency Bonus to any ability check you make that uses the tool. |
| `tool.advantage` | `e9d9f35f` | SUB | tool_proficiency | If you have proficiency in the skill that’s also used with that check, you have Advantage on the check too. |
| `tool.both` | `e9d9f35f` | SUP | - | This means you can benefit from both skill proficiency and tool proficiency on the same ability check. |

### C. Proficiency Bonus progression

| bonus | minimum level/CR | maximum | represented in |
|-------|------------------|---------|----------------|
| +2 | (none stated) | 4 | `69ae5a1b`, `b002753c` (cell.upto4, cell.p2) |
| +3 | 5 | 8 | `8a6fc1a5`, `d58940db` (cell.5_8, cell.p3) |
| +4 | 9 | 12 | `19340146`, `515f45ef` (cell.9_12, cell.p4) |
| +5 | 13 | 16 | `9b1cee59`, `df4629be` (cell.13_16, cell.p5) |
| +6 | 17 | 20 | `f848a0fb` (later.17_20) |
| +7 | 21 | 24 | `f848a0fb` (later.21_24) |
| +8 | 25 | 28 | `f848a0fb` (later.25_28) |
| +9 | 29 | 30 | `f848a0fb` (later.29_30) |

## 5. Every qualification and exception, and where it survives

The section's rules are mostly conditional. This table is the checklist a
reviewer should read against the printed page: each row is a qualification the
source states, and the clause that carries it.

| # | qualification / exception (exact source text in §4 B) | carried by | how |
|---|---|---|---|
| 1 | "Up to 4" names **no lower bound** on the first band | `cell.upto4` | band fact with `minimum=None`. Not 1 — the source does not say 1, and a defaulted 1 would be an invented claim about level 0 / CR 0 creatures. |
| 2 | a character's bonus tracks **levels**, a monster's tracks **Challenge Rating** | `main.character_levels`, `main.monster_cr` | two separate governing-prose clauses, so neither is generalized into the other |
| 3 | the bonus applies to a D20 Test **when** the creature has proficiency in a skill, in a saving throw, or with an item it uses to make that test | `main.d20_test` | exact prose; the applicability condition is not reduced |
| 4 | it is **also** used for spell attacks and spell save DCs | `main.spells` | exact prose, separate clause |
| 5 | the bonus can't be added **more than once** to a roll or number | `stack.once` | exact prose; its own expected rule |
| 6 | **exception:** it may occasionally be multiplied or divided before being added | `stack.scaling` | exact prose |
| 7 | **limit on that exception:** multiplied only once and divided only once | `stack.once_each` | exact prose, same expected rule as #6, so the exception and its limit cannot be accepted apart |
| 8 | Expertise doubles the bonus for certain ability checks | `stack.expertise` (supporting) + reference | the example is retained verbatim and cites the glossary record (§7) |
| 9 | the **GM has the ultimate say** on whether a skill is relevant | `skill.gm_say` | its own component, `gamemaster_latitude` — see §6 |
| 10 | without proficiency a creature **can still** make the check, but adds no bonus | `skill.without_a` + `skill.without_b` | one rule stated across the page break; both fragments are in one expected rule, so half of it cannot be accepted alone |
| 11 | tool proficiency adds the bonus to **any ability check that uses the tool** | `tool.checks` | exact prose |
| 12 | **and Advantage too**, **if** you have proficiency in the skill that's also used with that check | `tool.advantage` | typed `AdvantageFact` **and** exact prose — see §6 |
| 13 | both skill and tool proficiency can benefit the **same** check | `tool.both` (supporting) | retained verbatim as supporting authority |
| 14 | monsters' saving throw proficiencies live in **stat blocks** | `saves.monsters` | exact prose |
| 15 | each class gives **at least two** saving throw proficiencies | `saves.class_minimum` | exact prose |
| 16 | starting skill proficiencies come from character creation; monsters' from stat blocks | `determining.sources` | exact prose |

Nothing in the section was summarized, merged, or paraphrased. Every
substantive clause is either a typed fact or the source's own words bound to a
component.

## 6. Representation choices worth a reviewer's attention

Most of the 13 components are unremarkable: a clause states a rule, no closed
vocabulary models it, so the clause is retained as exact governing prose under
`no_identified_structured_use`. Four choices are not unremarkable.

**The bonus table is the only fully typed component.** Eight
`ProficiencyBonusBandFact`s, no prose bindings, `STRUCTURED`. The bands are the
one thing in this section a v1 consumer demonstrably needs at runtime: a
character sheet cannot render without resolving level → bonus. The first band
carries `minimum=None` (§5 #1).

**`skill_relevance_sources` and `skill_relevance_judgment` are deliberately two
components, not one paragraph's worth of one.** A component states exactly one
reason why its meaning is prose, and every binding on it must state the same
one. These two clauses do not share a reason. "The descriptions of the actions
you take … specify which skill applies" is *reducible and simply not modelled
yet* — someday an action record could name its skill. "The GM has the ultimate
say" is not reducible at all; it is the source handing the decision to a human,
which is `gamemaster_latitude`. Collapsing them would have forced one honest
reason to be replaced by a convenient one.

**`tool_proficiency` is `MIXED`, and the fact does not displace the prose.** The
Advantage is typed — `AdvantageFact(ADVANTAGE, roll=SUBJECT/ABILITY_CHECK)` —
because Advantage on an ability check is exactly what the existing structured
vocabulary is for. Its *trigger*, "the skill that's also used with that check",
is in no closed applicability vocabulary and would have to be guessed. So the
clause stays exact governing prose, its binding is the `PRIMARY` owner, and the
fact claims the same span **`CONTEXTUAL`**. A runtime may use the fact to know
Advantage is in play; it may not infer *when* from anything but the prose.

**Exactly one new fact family, for one identified use.** Schema 13 adds
`ProficiencyBonusBandFact` (§9) and nothing else: the level/CR → bonus lookup a
v1 character sheet cannot render without. No other field was added:
`AdvantageFact`, `RollSpec`, `RollActor` and `RollContext` are reused as-is, and
every other clause reuses an existing prose-retention code. Nothing was invented
for tidiness, and no field here is speculative.

**Two 5c artifacts are bound, not repaired.** The table caption text
` Proficiency Bonus` was absorbed into the trailing end of the body paragraph
`ce26a9f7`, and the column header `Level or CR Bonus` is repeated at the head
of `f848a0fb`. Both are real printed text in a leaf this batch reviews, so both
get a supporting-authority span pointing at the component they caption. They
are *not* fixed: that would reopen 5c. See §8.

## 7. Outward references, and what is recommended for each

The section makes five outward pointers. Two are authored as `ReferenceDraft`s;
three are not. The line drawn is deliberate and is the main thing this pilot
asks the Owner to confirm.

**A reference is authored exactly where the printed pointer names a *record*
under a key convention already committed.** The Rules Glossary is such a
convention: 62 accepted references already use scope `srd-5.2.1/rules-glossary`,
and glossary entries are records. Section titles and table names are not
records; minting keys for them would pin a naming decision the Owner has not
made and would silently widen this pilot.

| printed pointer | clause | authored? | disposition and recommendation |
|---|---|---|---|
| "see 'Rules Glossary'" → **Challenge Rating** | `main.monster_cr` | **yes** | `glossary.challenge_rating`, scope `srd-5.2.1/rules-glossary`. Target record not authored yet, so `validate_representation` reports one `unknown target record`. That is the intended state for a forward citation and matches speed-1's precedent. |
| "see 'Rules Glossary'" → **Expertise** | `stack.expertise` | **yes** | `glossary.expertise`, same scope, same unresolved finding. **Recommendation:** author the Expertise glossary entry in a later glossary batch; this reference then resolves with no change here. |
| **the Skills table** | `list.skills_table` | no | The pointer names a table, not a record. **Recommendation:** treat the Skills table as its own future batch (57 leaves, container `d818241d`, under *Actions* in *Playing the Game*) and give it a record key at that time; add the reference then. See the correction below. |
| "see 'Actions' later in 'Playing the Game'" | `skill.sources` | no | Names a section title. **Recommendation:** do not mint a section-title key. Twelve per-action records already exist (`action.attack` … `action.utilize`, accepted by actions-1 over the Rules Glossary `[Action]` entries) and `AbilityCheckFact` already carries a `skill` field, currently `None` on them. The durable representation is therefore an action record naming its skill — no new field and no section-title key — decided by a future batch over the *Actions* section, not by changing accepted content. |
| "described in 'Character Creation'" | `main.character_levels` | no | Names a section that no accepted or proposed batch covers. **Recommendation:** leave as governing prose until a batch covers Character Creation. |

In all three unauthored cases the pointer's **wording survives verbatim** inside
the bound governing prose, so nothing about the citation is lost — only the
machine-followable edge is deferred.

### Correction to the identification note

`.claude/review-notes/issue-5d-regular-section-pilot-IDENTIFICATION.md` states
that the Skills table "lives in actions-1's accepted territory." **It does
not.** Verified against the merged oracle:

* Skills table leaves: **57**, overlap with accepted leaves: **0**
* Proficiency section leaves: **31**, overlap with accepted leaves: **0**
* accepted leaves across the seven batches: **337**

`actions-1` accepted **Rules Glossary `[Action]` entries only** — 92 leaves, 13
records. The Skills table under *Playing the Game > Actions* is untouched
corpus. This does not change any decision in this proposal (the reference is
deferred either way), but it changes what a future batch may assume, so it is
recorded rather than quietly corrected.

## 8. Omissions, residue, and known boundaries

Stated plainly, because a review packet that omits its own residue is not
reviewable.

1. **Two unresolved references** (§7). Expected, reported by the standalone
   validator, asserted as an exact tuple by the generator.
2. **The absorbed table caption.** `ce26a9f7` ends with the caption text
   ` Proficiency Bonus` rather than carrying it in the table container. A 5c
   extraction artifact. Bound as supporting authority; not repaired.
3. **The repeated column header.** `f848a0fb` begins with `Level or CR Bonus`,
   a second printing of the table's column header. Same treatment, same reason.
4. **Three single-space separator gaps in `f848a0fb`** are left unspanned. The
   Owner Decision of 2026-09-16 made complete character partition optional, and
   `require_complete=False` permits this; a space between two band rows states
   nothing.
5. **The `Skill` enum docstring** in production code says its source is
   "Playing the Game > Proficiency". That is accepted content and remains
   correct prose; nothing here rewrites it. Noted as residue only because a
   future Skills-table batch will want to revisit where that enum's authority
   actually sits.
6. **No consumer is wired.** The band facts are proposed, not published; no
   runtime reads them. That is the correct state for an unaccepted proposal.

## 9. What the pilot cost

Reported as measured. No review time, throughput target or completion
percentage is estimated here, because none was measured.

**Batch-specific code: one generator, 1,109 lines.** Against the accepted
batches' generators:

| batch | generator lines |
|---|---|
| hazards-1 | 562 |
| actions-1 | 734 |
| conditions-1 | 787 |
| attitudes-1 | 2,249 |
| areas-of-effect-1 | 2,796 |
| cover-1 | 3,308 |
| **speed-1** | **3,604** (+1,846 accept script, +327 reproduction test) |
| **proficiency-1** | **1,109** (+224 test, no accept script) |

Speed-1 is the fair comparison: it was the last batch authored before the
shared workflow merged, and it is a comparable regular-corpus batch. **1,109 vs
3,604 is a 69% reduction**, and the shape of the difference matters more than
the ratio: proficiency-1's generator is almost entirely *data* — a 47-row clause
table, a 13-row component table, an 8-row band table — plus three calls into
merged services. It reimplements nothing. There is no accept script at all,
because `accept_proposal` is now a shared service and acceptance is the Owner's
decision, not a script in this directory.

**Supporting engineering: schema 13, one fact family.**

```
src/afterworlds/ingestion/mechanical/representation.py  | 129 +++-
src/afterworlds/ingestion/mechanical/projection.py      |  20 +-
src/afterworlds/ingestion/mechanical/schema_lift.py     |  52 ++
3 files changed, 199 insertions(+), 2 deletions(-)
```

That is the whole production footprint: a new `ProficiencyBonusBandFact`
family, its projection wiring, and one lift step. Additive — the same bounded
shape as the schema-12 mint at `eef9a08`.

**Schema-13 test fallout, measured in five passes:** 76 → 25 → 4 → 0, then 1.
The 76 → 25 step was one surgical restamp of `bounded_oracle.json`'s schema
block; 25 → 4 was a 37-site pin pass across 17 test files; 4 → 0 was a 5-site
residual pass. The full-suite gate then found one further canary outside the
ingestion tree — `tests/services/rules_authority/`'s patch-layer schema-hash
assertion, which exists precisely to move when the representation does — and
restamping it closed the sequence.

Final gates on the branch head: `black` and `ruff` clean over 478 files, `mypy`
clean over 225 source files, and the suite in two chunks — `tests/ingestion`
**3,226 passed** in 867.97s, `tests --ignore=tests/ingestion` **2,775 passed,
10 skipped** in 330.03s, total coverage **94.39%**.

**Diagnosis the brief asks for: the pilot did *not* need a large custom
program.** The entire batch-scoped proof is three calls into merged services —
`validate_partition(..., require_complete=False)` per leaf,
`review_unit_violations`, and standalone `validate_representation` — plus the
mutation check. Nothing about a regular section, as opposed to a glossary entry
list, required new machinery. The one thing that *did* need a code change was a
new fact family for a table the section prints, which is the expected cost of
typing a new kind of rule, not an obstacle to scaling. The obstacle to scaling
another section is authoring judgment (which clauses are one rule, what reason
a prose retention honestly states), not tooling.

## 10. How to verify this packet

```bash
# regenerate the proposal (deterministic; overwrites with identical bytes)
python .claude/review-notes/issue-5d-batch-proficiency-1-generator.py

# the committed retained proposal, through the production path
pytest tests/ingestion/mechanical/test_proficiency_1_proposal.py -q --no-cov
```

The test pins the identity, runs `review_unit_violations` on the loaded
artifact, asserts **all eight bands** as an exact set, proves by mutation that
dropping the 29–30 band **is reported**, and exercises `accept_proposal`
in memory — with `reviewer="test-evidence-only"` — asserting the committed
oracle is byte-identical before and after. That acceptance is isolated test
evidence that the proposal is structurally acceptable. **It is not a semantic
acceptance and confers none.**
