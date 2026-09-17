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

The question asked of every clause here is the one #137 contract 2 and ADR-005d
Decision 2 actually pose: **which identified code-owned operation — in play,
explanation, or correction — needs a separate structured field, and what
concretely fails if the field is absent?** Planned v1 uses count even before
their consumers are implemented, so neither "no closed vocabulary models it"
nor "nothing reads it today" is an answer. `no_identified_structured_use` says
what the policy catalog says it says — *the meaning is reducible, but no
identified code-owned use requires a separate structured field* — and each
group below has to earn that.

Answered per coherent group, not per field or per row. The thirteen components
fall into six groups:

| group | components | identified operation | consequence of omitting a field | disposition |
|---|---|---|---|---|
| **the bonus progression** | `proficiency_bonus_table` | resolve a level or CR to a bonus — the value a v1 character sheet renders and every later addition starts from | a consumer would have to read the number out of prose at runtime, which contract 2 forbids outright: *"choosing prose does not authorize runtime interpretation into trusted values"* | **STRUCTURED** — 8 `ProficiencyBonusBandFact`s |
| **where the bonus comes from, and what it can reach** | `proficiency_bonus_basis`, `proficiency_bonus_application` | explain why a creature's bonus is the number it is, and which D20 Tests the bonus can reach at all | none identified. The *value* is the group above; the *selection* — which skills, saves and items this creature is proficient with — is character-sheet state (Invariant 9), not corpus state, so a field here would state a condition whose operand this corpus does not hold | **PROSE_BOUND** |
| **applying it** | `skill_proficiency_application`, `saving_throw_proficiency`, `weapon_proficiency`, `tool_proficiency` (part) | add the bonus to the roll the proficiency covers | no v1 operation is blocked today, and the validated application path for a GameMaster-selected effect is **15c's** — named in contract 2 and listed in this issue's out-of-scope items. The honest limit is recorded as residue (§8 #8), not asserted away | **PROSE_BOUND** |
| **the stacking limits** | `bonus_does_not_stack` | correct a computation that would add, multiply or divide the bonus more than once | same 15c consumer as the group above; there is no computation in v1 to constrain until that path exists | **PROSE_BOUND** |
| **which skill is relevant** | `skill_relevance_sources`, `skill_relevance_judgment` | select the skill an action calls for | split between the two components, for two different reasons — see below | **PROSE_BOUND**, two reason codes |
| **pointers to data held elsewhere** | `skill_list`, `determining_skills`, `equipment_proficiency` | navigate to the Skills table, to character creation, to a class or a stat block | none here. The data is another unit's to represent; a field would pre-empt a batch that has not reviewed its source | **PROSE_BOUND** |

**What the inspection looked for and did not find.** Every existing family was
checked for one that could carry "add the Proficiency Bonus to *X*"; none can.
The closest, `DerivedQuantityFact`, derives a value from an ability modifier
over a `TimeUnit` and is not a proficiency application. That absence is *not*
the argument for prose — an absent vocabulary is exactly what minting a family
fixes, as the band table shows. The argument is the consequence column: the one
input in this section that a v1 consumer cannot derive and cannot get anywhere
else is the progression, and it is typed. **No concrete required input is
missing**, so nothing was added and the proposal's meaning and identity are
unchanged by this review.

Four choices still want a reviewer's attention directly.

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

**`tool_proficiency` is `MIXED`, and neither half certifies the other.** The
Advantage is typed — `AdvantageFact(ADVANTAGE, roll=SUBJECT/ABILITY_CHECK)` —
because Advantage on an ability check is exactly what the existing structured
vocabulary is for. Its *trigger*, "the skill that's also used with that check",
is in no closed applicability vocabulary. So the clause stays exact governing
prose, its binding is the `PRIMARY` owner, and the fact claims the same span
**`CONTEXTUAL`**.

What that combination does and does not license, stated exactly:

* The exact governing prose stays available for **explanation**. A GameMaster
  view can show this rule verbatim with its source reference, which is what
  Decision 2 means by prose being part of the bound rule authority rather than
  a footnote.
* **No consumer may infer trusted applicability from it.** An earlier draft of
  this packet said a runtime "may not infer *when* from anything but the
  prose", which permits precisely the inference contract 2 forbids —
  *"choosing prose does not authorize runtime interpretation into trusted
  values"*. Reading the sentence and concluding the rule applies to a
  particular check is that interpretation. The correct statement is that
  nothing here authorizes any consumer to decide applicability, from the prose
  or from anywhere else.
* **Nor may any consumer apply Advantage unconditionally from the fact.** The
  `CONTEXTUAL` provenance role records that the fact's meaning lives in that
  span; `MIXED` records that the component's meaning lives in both halves.
  Both are statements about *where meaning is recorded*. Neither certifies that
  the rule may be executed, and a fact carrying no trigger is not a fact that
  always fires.
* Any validated application of this Advantage to an actual check belongs to
  **15c's typed application path for GameMaster-selected effects** — a separate
  obligation that contract 2 names explicitly and that prose representation
  does not discharge. This branch adds no runtime consumer of this fact, and
  this finding does not by itself call for a new trigger family or any runtime
  code.

**One new family, and three new fields.** Schema 13 adds
`ProficiencyBonusBandFact` (§9) and nothing else. The family is new **and so
are its three fields** — `bonus: int`, `maximum: int`, `minimum: int | None` —
which is the minimum that states one printed row: a bonus, the top of the band,
and a bottom that the first row does not print. An earlier draft of this packet
said "no other field was added"; that was inaccurate. What is true is narrower:
**no existing family, vocabulary or component field was widened.**
`AdvantageFact`, `RollSpec`, `RollActor` and `RollContext` are reused
unchanged, and every other clause reuses an existing prose-retention code.

**Two 5c artifacts are bound, not repaired.** The table caption text
` Proficiency Bonus` was absorbed into the trailing end of the body paragraph
`ce26a9f7`, and the column header `Level or CR Bonus` is repeated at the head
of `f848a0fb`. Both are real printed text in a leaf this batch reviews, so both
get a supporting-authority span pointing at the component they caption. They
are *not* fixed: that would reopen 5c. See §8.

## 7. Outward references: authored, deferred, and navigational

The section makes five outward pointers and one internal one. They are not the
same kind of thing, and the distinction that decides each is contract 4's:
**a source-authored mechanical reference resolves at build time through
committed source scope, aliases and exact target semantic keys, and an
ambiguous, unresolved, invalid or cross-release one blocks publication.**
Navigation that names no mechanical input is not such a reference.

Three facts about the mechanism, because they do the work here:

1. **A `ReferenceDraft` targets a record.** Its fields are `scope_key` and
   `target_record_key`; there is no pointer-to-a-heading form. The Rules
   Glossary is a committed scope — 62 accepted references use
   `srd-5.2.1/rules-glossary`, and glossary entries are records. A section
   title and a table name are not records and have no committed scope here, so
   a key invented for one now would be a key no assembled record will ever
   carry: it would **misdirect** a later build rather than block it, and
   `validate_representation` would report it as unresolved for the wrong
   reason. Choosing the eventual key is an ordinary engineering choice for the
   batch that assembles that record. No policy or ownership is affected and no
   Owner naming decision is requested.
2. **Nothing validates an absence.** `validate_representation` reports a
   reference whose target record does not exist. It cannot report a pointer
   nobody authored. `RecordObligation`s are derived per record from its own
   membership and are refused unless the committed set matches exactly, so they
   are not a home for a note about a reference either.
3. **Build-time resolution is not waived for any of these.** The deferral is
   temporary by construction. Contract 2 makes inventory gaps and unreviewed
   units publication blockers, so the Skills table and the *Actions* section
   cannot stay unreviewed while the projection publishes; when they are
   reviewed, their pointers are ordinary source-authored mechanical references
   that must resolve like every other. **Nothing here creates a standing
   exception to build-time resolution, and nothing here authorizes a new corpus
   batch.**

| printed pointer | clause | kind | state and recommendation |
|---|---|---|---|
| "see 'Rules Glossary'" → **Challenge Rating** | `main.monster_cr` | authored mechanical reference | `glossary.challenge_rating`, scope `srd-5.2.1/rules-glossary`. The target record is not authored yet, so `validate_representation` reports one `unknown target record`. That is the intended state for a forward citation and matches speed-1's precedent — and under contract 4 it blocks publication until the glossary batch lands. |
| "see 'Rules Glossary'" → **Expertise** | `stack.expertise` | authored mechanical reference | `glossary.expertise`, same scope, same unresolved finding, same publication block. **Recommendation:** author the Expertise entry in a later glossary batch; this reference then resolves with no change here. |
| **the Skills table** | `list.skills_table` | **deferred mechanical link** | The pointer names mechanical content — the table "notes example uses for each skill proficiency as well as the ability check the skill most often applies to". It is a mechanical reference in substance and is simply not authorable yet: the table is not an assembled record (57 leaves, container `d818241d`, under *Actions* in *Playing the Game*, reviewed by no batch). **Recommendation:** review the Skills table as its own unit, give it a record key there, and author this reference at that time. See the correction below. |
| "see 'Actions' later in 'Playing the Game'" | `skill.sources` | **deferred mechanical link** | Also mechanical in substance — it says where the skill an action calls for is specified — and also not authorable as one edge: the sentence points at a whole series, and twelve per-action records already exist (`action.attack` … `action.utilize`, accepted by actions-1 over the Rules Glossary `[Action]` entries) with no single target among them. `AbilityCheckFact` already carries a `skill` field, currently `None` on all twelve. **Recommendation:** the durable representation is each action record naming its skill — no new field and no section-title key — decided by a future batch over the *Actions* section, not by changing accepted content. |
| "described in 'Character Creation'" | `main.character_levels` | **informational navigation** | The parenthetical says where character level advancement is described. This unit's rule is complete without it: the table gives the bonus for every level and CR it prints, and nothing in the clause needs a value from Character Creation. **Recommendation:** leave as governing prose; there is no deferred mechanical edge to record. |
| "The Proficiency Bonus table shows how the bonus is determined" | `main.table_pointer` | **internal navigation** | Points inside this same unit, at the component this proposal already contains, and is bound as supporting authority. No reference is needed or possible. |

In every unauthored case the pointer's **wording survives verbatim** inside the
bound governing prose, so nothing about the citation is lost — only the
machine-followable edge is deferred.

### How the two deferred links stay visible

Honestly, and with the limit stated: they are visible because they are written
down **here, in §8, and in the PR description** — and that is a documentation
mechanism, not a gate. No check fails today because `list.skills_table` has no
`ReferenceDraft`; as above, a validator cannot report a pointer nobody
authored. What bounds the window is not this packet but contract 2's coverage
rule, which will not let those sections stay unreviewed while a complete
projection publishes, and contract 4, which will not let their references stay
unresolved once authored. Until that batch exists, this packet is the only
place the obligation is recorded. It is named as residue (§8 #7), not decided.

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
7. **Two deferred mechanical links** (§7): the Skills table and the *Actions*
   section. Both are source-authored mechanical pointers that are not yet
   authorable as `ReferenceDraft`s because neither target is an assembled
   record. Nothing validates their absence, so this packet is the record. They
   are **not** a permanent exception to build-time resolution: contract 2 makes
   the unreviewed sections publication blockers and contract 4 makes the
   references resolve once authored. No batch is authorized here to fix it.
8. **The application rules are prose, and 15c owns what would change that.**
   `skill_proficiency_application`, `saving_throw_proficiency`,
   `weapon_proficiency`, `tool_proficiency` and `bonus_does_not_stack` state
   where the bonus is added and how often. No v1 operation reads them today and
   none is blocked, which is what `no_identified_structured_use` asserts — but
   the honest limit is that the assertion is about *today's* identified
   operations. When 15c defines its validated application path for
   GameMaster-selected effects, if that path needs typed eligibility or a typed
   stacking constraint, contract 2 requires the field to be supplied **before**
   the operation relies on the rule. Prose representation does not discharge
   that obligation and is not claimed to. Recorded so a later batch inherits the
   question rather than the conclusion.

## 9. What the pilot cost

Reported from run timestamps and the git history, with elapsed work, waiting,
and code footprint kept apart, because they scale for different reasons. No
throughput target, completion percentage or historical baseline is estimated
here. There is no recorded per-batch authoring time for any earlier batch, so
there is nothing to compare elapsed time against and none is invented.

### Elapsed time, waiting, and footprint are three different numbers

| what | measured | how |
|---|---|---|
| **elapsed on the branch** | **2 h 17 m** (`72fab6e` 2026-09-16 23:41:41 −07:00 → `23f49d2` 2026-09-17 01:58:25 −07:00) | commit timestamps. A **lower bound** on authoring: it excludes reading and source review before the first commit, and it includes one context compaction and at least two full-suite passes. It is *not* hands-on time. |
| **local gate wait, final pass** | **1,198 s ≈ 20 m** | `tests/ingestion` 867.97 s + `tests --ignore=tests/ingestion` 330.03 s. Waiting, not work, and it recurs on every pass. |
| **CI wait, final head** | **31 m 44 s** | run `35202642012`, created 08:59:15 Z, updated 09:30:59 Z, conclusion `success`. Also waiting. |
| **production footprint** | **199 insertions, 2 deletions, 3 files** | `representation.py` 128/1, `projection.py` 19/1, `schema_lift.py` 52/0. |
| **batch-specific footprint** | **1,109** generator + **224** proposal-test lines, no accept script | new files in `23f49d2`, plus the 1,744-line `PROPOSAL.json` and this packet, which are data and prose rather than program. |
| **mint maintenance** | **101 insertions, 41 deletions across 19 pre-existing files** | the schema-hash restamp; see the diagnosis below. |

The two waits are not interchangeable with the elapsed figure. The local suite
runs **inside** the 2 h 17 m window and ran more than once, so at least ~20 m
of that window is machine time, not authoring. CI ran **after** it — the run
was created at 01:59:15 local, fifty seconds after the final commit — so its
31 m 44 s sits outside the window entirely and is pure additional latency
before the branch could be reported as green.

**Batch-specific code: one generator, 1,109 lines.** Against the accepted
batches' generators — read as a footprint table, not a throughput result:

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

**These are file sizes, and a ratio between two of them is not a throughput
result.** Speed-1 is the nearest structural neighbour — the last batch authored
before the shared workflow merged — but its 3,604 lines and this batch's 1,109
are over different sections with different clause counts, authored under
different methods, and neither number is an hours figure. The line counts also
conflate two changes: the merged workflow removed the per-batch accept script
and reproduction test, *and* the earlier generators partitioned every character
of every leaf, which the Owner Decision of 2026-09-16 made optional. What can
be said without inventing a baseline is structural: proficiency-1's generator
is almost entirely *data* — a 47-row clause table, a 13-row component table, an
8-row band table — plus three calls into merged services, and it reimplements
nothing. There is no accept script at all, because `accept_proposal` is a
shared service and acceptance is the Owner's decision, not a script in this
directory. Whether that shape holds for a section with a harder source is the
question the next pilot answers, not this one.

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

### Diagnosis 1 — the schema restamp is the real recurring maintenance

**Test fallout from minting schema 13, measured in five passes:** 76 → 25 → 4 →
0, then 1. The 76 → 25 step was one surgical restamp of `bounded_oracle.json`'s
schema block; 25 → 4 was a 37-site pin pass across 17 test files; 4 → 0 was a
5-site residual pass. The full-suite gate then found one further canary outside
the ingestion tree — `tests/services/rules_authority/`'s patch-layer
schema-hash assertion, which exists precisely to move when the representation
does — and restamping it closed the sequence.

That cost is **not** proportional to the size of the schema change at either of
the two mints measured. The schema-12 mint at `eef9a08` added seven families
with their vocabularies — 612 insertions across 11 `src/` files — and modified
**19 pre-existing non-`src` files**, 769 insertions and 97 deletions. That
non-`src` delta is much larger than a restamp because schema 12 also changed
test *behaviour*: it minted the prose-retention reason codes, so those files
gained assertions as well as new hash literals. This mint added one family —
199 insertions across 3 `src/` files — and modified **19 pre-existing non-`src`
files**, 101 insertions and 41 deletions, which *is* restamp-sized. **17 files
appear in both sets.** So the honest reading is a floor, not a ratio: a mint
pays for the number of committed sites that pin a schema hash regardless of how
small the schema change is. Two mints is two data points, not a trend — but
both paid it.

Stated plainly rather than acted on: those pins exist deliberately — each one
is a canary that fails when representation meaning moves, which is exactly what
they are for, and an accepted batch's frozen-prior test *must* keep asserting a
literal. A sixth mint will pay the same price. Whether that is worth a
consolidated pin fixture is a real question, but **no tooling refactor is
requested or attempted here**, and none should be inferred from this paragraph.

### Diagnosis 2 — what is left that is batch-specific

The pilot did **not** need a large custom program. The entire batch-scoped
proof is three calls into merged services — `validate_partition(...,
require_complete=False)` per leaf, `review_unit_violations`, and standalone
`validate_representation` — plus the mutation check. Nothing about a regular
section, as opposed to a glossary entry list, required new machinery.

What remains genuinely per-batch, honestly:

* **The clause/component/fact tables in the generator.** This is source review
  written down. It is not removable tooling and should not be targeted.
* **A hand-written proposal test per batch** (224 lines here). It pins the
  identity and the source-reviewed expectations, which by contract 4 must not
  be regenerated from the output they check. Also not removable.
* **The schema restamp**, when a batch mints a schema — Diagnosis 1.
* **Nothing else.** No accept script, no reproduction implementation, no
  private-parser reload.

So the honest answer to "is this ready to scale?" is: the *tooling* obstacle is
gone for a section of this shape, and the remaining recurring cost is the
restamp plus roughly twenty minutes of local suite and half an hour of CI per
pass. The remaining *authoring* obstacle is judgment — which clauses are one
rule, and which prose retentions honestly earn their reason code — and this
pilot produced no evidence that judgment gets cheaper with repetition. One
section is one data point.

Final local gates on the branch head at the time the pilot was reported:
`black` and `ruff` clean over 478 files, `mypy` clean over 225 source files,
and the suite in two chunks — `tests/ingestion` **3,226 passed** in 867.97 s,
`tests --ignore=tests/ingestion` **2,775 passed, 10 skipped** in 330.03 s,
total coverage **94.39%**. `pip-audit` reports 29 pre-existing advisories
across 10 third-party packages, unchanged by this branch. Gates for the
correction round that produced this revision are reported in the PR
description, which can cite the CI run for a head this file is part of.

## 10. How to verify this packet

```bash
# regenerate the proposal (deterministic; overwrites with identical bytes)
python .claude/review-notes/issue-5d-batch-proficiency-1-generator.py

# the committed retained proposal, through the production path
pytest tests/ingestion/mechanical/test_proficiency_1_proposal.py -q --no-cov

# the new family's numeric contract and the schema-12/13 boundary
pytest tests/ingestion/mechanical/test_schema_13_proficiency.py -q --no-cov
```

The test pins the identity, runs `review_unit_violations` on the loaded
artifact, asserts **all eight bands** as an exact set, proves by mutation that
dropping the 29–30 band **is reported**, and exercises `accept_proposal`
in memory — with `reviewer="test-evidence-only"` — asserting the committed
oracle is byte-identical before and after. That acceptance is isolated test
evidence that the proposal is structurally acceptable. **It is not a semantic
acceptance and confers none.**

`test_schema_13_proficiency.py` covers what is specific to the new family and
deliberately does not repeat what the suite already has. Generic family
behaviour — payload round-tripping for every declared family, unknown-family
refusal, persistence — stays in `test_fact_families.py` and the per-schema
modules. What is here: every printed band including the one **open below**
(`minimum=None` survives the payload as an explicit null rather than
defaulting to 1); the numeric contract, one case each for a bonus that adds
nothing, an upper bound below the first level or CR, a lower bound below it,
and a band that runs backwards; non-integer field values including `bool`,
which matters because `isinstance(True, int)` is true in Python; and the schema
boundary asserted on the committed proposal itself — **schema 12 refuses it for
exactly the eight band facts and nothing else**, schema 13 admits it with no
violation, and the crossing is one registered lift step.
