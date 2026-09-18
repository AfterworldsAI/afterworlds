# `proficiency-1` review packet — CRD Issue 5d, first regular-section pilot

**Status: PROPOSED. Not accepted. Nothing in this branch accepts it.**

This packet is the human-readable half of an unaccepted proposal over
**SRD 5.2.1 > Playing the Game > Proficiency**. It exists so a reviewer can
check the proposal against the printed source without reading 55 KB of JSON,
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
| bytes | 55,439 |
| `proposal_identity` | `11481e020ce08119938dcfd7e9df6a9f84c945f6ad63de2d5a47bcfc45110417` |
| file sha256 | `a56829dde1db9281f8c3e1df78f0feb32f0496a2c50651739198deee8058a6c8` |
| superseded, never accepted | identity `c941c262…`, sha256 `b74b6056…`, 54,507 bytes — regenerated in this review round to author §7's two outstanding obligations |
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

An earlier version of this section asked of each clause "which **input** can the
hand-authored algorithm not derive?", and answered several rows with *the
algorithm is code's*. That argument is withdrawn, for two reasons in the
authority rather than a change of taste:

* ADR-005d rejects alternative **7**, *"Let adapter breadth decide
  representation breadth. Rejected: representation and execution are
  independent."*
* #137 states that *"prose cannot conceal a field required by such a use"*.

Code owning an *operation* says nothing about what declarative data that
operation consumes; the bounded d20 adapter is hand-authored **and** consumes
typed rule data, and those are not in tension. So the boundary is rebuilt below
out of what the accepted authority actually fixes.

### The four things a clause's operand can be

1. **Character state.** Level or CR, and which skills, saving throws, weapons
   and tools this creature is proficient with. Invariant 9 makes the sheet the
   first-class owner of those; this corpus does not hold them and must not
   pretend to.
2. **The rule authorizing the bonus.** Rules-Package content — this projection.
   What the bonus is worth, and what the source says proficiency entitles you
   to.
3. **Applicable rule overrides.** #137's In scope, quoted at ADR-005d:599 —
   *"Typed record/component/fact `RuleOverride` application with existing
   precedence semantics"* — plus the separate `prose` grain from Owner Decision
   2026-08-08. `services/rules_authority/targets.py` closes the addressable set
   at record, component, fact, prose, and option-as-fact-container; there is no
   path expression and no wildcard. So whether a clause is *behaviourally*
   overridable is a function of whether it carries a typed fact: a component
   with no facts admits only `DISABLE`/`REPLACE`/`APPEND` on its prose.
4. **Fixed adapter semantics.** ADR-015 Decision 7, exactly: assembly consumes
   *sheet + rule slice + `RuleOverride`s*, and the bounded adapter is
   hand-authored covering *d20 semantics only*. That fixes the **input list**
   and the adapter's **breadth**. It does not say which of those inputs carries
   the proficiency-kind → D20 Test mapping, and no accepted text places that
   mapping among the hand-authored semantics.

### What the current consumer shows, and what it cannot settle

`_assemble_modifiers`, `src/afterworlds/pipeline/rpg/adapter.py:188`. Its
`_rule_slice` and `_overrides` parameters are underscore-prefixed and never read
(lines 191-192). The skill branch takes `sheet.skills[label]`, which is the
already-summed number — *"skills stores the computed modifier (ability mod +
prof)"* (line 215). The save branch is ability-mod-only: *"v1: saves are
ability-mod-only; no save-proficiency in sheet"* (line 223).

Per CLAUDE.md that is evidence of the current implementation, not authority: an
unread `rule_slice` argument does not establish that the intended input contract
excludes rule data, and this packet does not argue from it in either direction.

It does expose a **third** live reading of the seam, which is the reason the
question below is not this pilot's to answer. A sheet that stores the summed
skill modifier has *already applied* proficiency before any adapter runs. Under
that shape neither the adapter nor the rule slice needs the mapping at all — and
which of them owns it is Character Sheet Model policy, #137's 2b, on this
pilot's stop-list.

### The one question this pilot cannot answer

> **Is the mapping from a proficiency kind to the D20 Test its bonus reaches —
> together with the add-once, multiply-or-divide-at-most-once constraint on that
> sum — Rules-Package-supplied typed data, or is it fixed by sheet or adapter
> semantics?**

**Reading A — fixed by sheet or adapter semantics.** ADR-015 Decision 7's
*"covers d20 semantics only"* permits the mapping to be one of those
hand-authored semantics, and nothing accepted excludes it; the stored-skill-
modifier shape above is a live implementation of exactly that. Under A the five
clauses held below are complete as exact prose for explanation, no input is
missing, and this pilot's representation is right as proposed.

**Reading B — Rules-Package-supplied.** Decision 7 names the *rule slice* as an
assembly input, and the rule slice is this projection's content, not the
adapter's. ADR-005d's rejected alternative 7 forbids letting adapter breadth
choose representation breadth, and #137 says prose *"cannot conceal a field
required by such a use"*. Under B a typed application fact on each of the five
is the missing input, and prose is concealing it.

**Why the citations do not decide it.** Contract 2's test is *which identified
code-owned operation needs a separate structured field*. Whether modifier
assembly needs the mapping as a field is precisely what the ownership call
determines, so the test is circular until that call is made. Neither reading can
be derived from the other's evidence, and both are consistent with everything
adopted. Classification: **`owner decision needed`**. Nothing is implemented
against it, no field is invented to close it, and no consumer is authorized to
read the mapping out of prose in the meantime.

**What Reading B would cost, for sizing only, not proposed here.**
`RollSpec`/`RollContext` already state which roll a fact is about —
`ATTACK_ROLL`, `ABILITY_CHECK`, `SAVING_THROW`, `D20_TEST`
(`representation.py:699`) — so the *target* vocabulary exists and would be
reused. What does not exist is a family carrying *add the Proficiency Bonus to
that roll*; the nearest, `DerivedQuantityFact`, derives a value from an ability
modifier over a `TimeUnit`. So B is one new fact family reusing existing roll
vocabulary, on the scale of the band family this pilot already minted — not a
widening of anything accepted.

### Every group against all four legs

*Play* is runtime use by an intended consumer. *Explanation* is showing a
Sojourner or GameMaster why a number is what it is. *Correction* is amending
Rules-Package content: before acceptance that is regeneration, the route
`conditions-1` took at schema 3; there is no post-acceptance supersede path, and
that gap is classified `out of scope` in §7. *Supported overrides* are the five
typed target grains in point 3 above.

| group | components | operand is | play | explanation | correction | supported overrides | disposition |
|---|---|---|---|---|---|---|---|
| **the bonus progression** | `proficiency_bonus_table` | the rule (2) | a v1 sheet cannot render without resolving level or CR to a bonus, and contract 2 forbids reading it from prose: *"choosing prose does not authorize runtime interpretation into trusted values"* | the caption and column-header spans stay bound (§4C) | regeneration restates a band | `REPLACE` any `ProficiencyBonusBandFact`; `APPEND` a band onto the component. Fully addressable | **STRUCTURED** — 8 band facts |
| **basis and umbrella** | `proficiency_bonus_basis`, `proficiency_bonus_application` | (1) plus (2) as a statement | none. The umbrella states *that* the bonus reaches D20 Tests a creature is proficient in; its two operands are the per-kind clauses below and sheet state, so a field here would restate one of those | exact prose bound, and the `Challenge Rating` pointer is authored (§7) | regeneration | prose grain only, and nothing behavioural depends on it under either reading | **PROSE_BOUND**, not held |
| **applying it, per kind** | `skill_proficiency_application` (`skill.proficient`), `saving_throw_proficiency` (`saves.bonus`), `weapon_proficiency` (`weapon.attack_rolls`), `tool_proficiency` (`tool.checks`) | **the subject of the question above** | depends on the answer: under A nothing, under B the mapping itself | not impaired either way — the exact governing prose is bound with span-exact provenance | under A an erratum moving where the bonus applies changes no trusted value, because no trusted value states it | under A only the prose grain exists on a fact-less component, and contract 2 bars any consumer from reading the changed prose as a trusted value, so a behavioural override of *where* the bonus applies is unrepresentable. That is a consequence of Reading A, not authority forcing B: #137's In scope establishes the override *mechanism*, not that any particular rule must be overridable | as proposed: **PROSE_BOUND** (`tool_proficiency` **MIXED**). The typed-field decision is **held — `owner decision needed`** |
| **the stacking limits** | `bonus_does_not_stack` (`stack.once`, `stack.scaling`, `stack.once_each`) | same subject: a constraint on the same sum | depends on the answer | exact prose bound; the `Expertise` pointer is authored (§7) | as above | as above | **held with the row above**, same question, same dependent decision |
| **which skill is relevant** | `skill_relevance_sources`, `skill_relevance_judgment` | judgment, and an unmodelled pointer | none; see the tool-Advantage note below for how the judgment enters | both clauses bound, one reason code each | regeneration | prose grain | **PROSE_BOUND**, two reason codes |
| **pointers to data held elsewhere** | `skill_list`, `determining_skills`, `equipment_proficiency` | another unit's content | none here; a field would pre-empt a batch that has not reviewed its source | exact prose bound | regeneration | prose grain | **PROSE_BOUND**; `skill_list` now also carries an **outstanding** `ReferenceDraft` to the Skills table, so the deferral is tracked rather than described (§7) |

**What the family inspection found.** No existing family can carry "add the
Proficiency Bonus to *X*"; the nearest is `DerivedQuantityFact`, above. That
absence is not an argument for prose — an absent vocabulary is what minting a
family fixes, as the band table shows — and it is not an argument for a field
either. It is the sizing note above. **Item 1 changed no representation:** no
field was added, no disposition moved, no vocabulary was widened. The proposal's
identity did move this round, for §7's two outstanding references alone.

### Tool Advantage: the judgment and the consequence are not one seam

An earlier version of this section routed the whole tool-Advantage consequence
through 15c because one of its inputs needs judgment. That was wrong, and is
replaced by the split the two halves actually have.

* **The consequence is deterministic and already typed.** Once relevance and the
  creature's proficiencies are known, the source states one outcome and no
  further choice: `AdvantageFact(ADVANTAGE, roll=SUBJECT/ABILITY_CHECK)`,
  `CONTEXTUAL` on `tool.advantage`. Nothing discretionary remains inside it.
* **The trigger has three operands, and only one of them is judgment.**
  Proficiency with the tool and proficiency in the skill are both sheet state —
  the source requires *both*, and says so in the supporting clause `tool.both`:
  *"you can benefit from both skill proficiency and tool proficiency on the same
  ability check"*. The third, whether that skill is *"also used with that
  check"*, is the GameMaster's relevance call, which is why
  `skill_relevance_judgment` carries `gamemaster_latitude` (§5 #9, #12).
* **So what is missing to fire this fact is trigger operands, not a
  discretionary application path.** 15c is one path that *supplies*
  GameMaster-selected judgments; it is not where a deterministic consequence
  goes to be executed, and routing the consequence there would misfile a fixed
  source rule as a GM-selected effect. No closed applicability vocabulary states
  that three-way conjunction, and this pilot mints none for it.
* **What `MIXED` plus `CONTEXTUAL` therefore record.** The component's meaning
  lives in both halves, and the fact's meaning lives in the span it claims. Both
  are statements about *where meaning is recorded*. Neither certifies that the
  rule may be executed, and a fact carrying no trigger is not a fact that always
  fires: **no consumer may apply this Advantage unconditionally from the fact,
  and none may decide applicability from the prose** — *"choosing prose does not
  authorize runtime interpretation into trusted values"*. An earlier draft said a
  runtime "may not infer *when* from anything but the prose", which licenses
  exactly the interpretation contract 2 forbids.
* This is a recorded representation gap, not a second Owner question, and it
  adds no runtime consumer, no trigger family and no runtime code.

### Two remaining choices, unchanged by this rebuild

**One new family, and three new fields.** Schema 13 adds
`ProficiencyBonusBandFact` (§9) and nothing else. The family is new **and so
are its three fields** — `bonus: int`, `maximum: int`, `minimum: int | None` —
which is the minimum that states one printed row: a bonus, the top of the band,
and a bottom that the first row does not print. An earlier draft of this packet
said "no other field was added"; that was inaccurate. What is true is narrower:
**no existing family, vocabulary or component field was widened.**
`AdvantageFact`, `RollSpec`, `RollActor` and `RollContext` are reused
unchanged, and every other clause reuses an existing prose-retention code. The
first band carries `minimum=None` (§5 #1).

**Two 5c artifacts are bound, not repaired.** The table caption text
` Proficiency Bonus` was absorbed into the trailing end of the body paragraph
`ce26a9f7`, and the column header `Level or CR Bonus` is repeated at the head
of `f848a0fb`. Both are real printed text in a leaf this batch reviews, so both
get a supporting-authority span pointing at the component they caption. They
are *not* fixed: that would reopen 5c. See §8.

## 7. Outward references: authored, deferred, and outstanding

The section makes five outward pointers and one internal one. They are not the
same kind of thing, and the distinction that decides each is contract 4's:
**a source-authored mechanical reference resolves at build time through
committed source scope, aliases and exact target semantic keys, and an
ambiguous, unresolved, invalid or cross-release one blocks publication.**
Navigation that names no mechanical input is not such a reference.

Two of the five were previously described in prose and tracked in this packet's
notes alone. That was the defect: reviewing the Skills table or *Actions* later
does not ensure the originating Proficiency pointers are ever completed, and a
note can be edited away. They are now **authored as outstanding obligations** in
the proposal itself.

### The mechanism, and why it is the existing one

1. **An outstanding obligation is a `ReferenceDraft` with an empty
   `target_record_key`.** Validation already distinguishes the two cases:
   `validation.py` reports `unresolved reference` when the target is empty and
   `unknown target record <key>` when the target names a record that does not
   exist. Both block; they are different findings, and the first is the one that
   says *this edge is not yet decided* rather than *this edge points somewhere
   wrong*.
2. **Empty, not a guessed key, because a guess can be discharged by accident.**
   A key invented now — for a table name or a section title, neither of which is
   a record — would resolve the moment some later batch happened to mint that
   spelling, whether or not anyone connected it to this pointer. An empty target
   cannot coincidentally match anything, so the obligation can only be closed by
   an explicit edit that names the real destination. Choosing that eventual key
   stays an ordinary engineering choice for the batch that assembles the record;
   no final semantic identifier is invented here and no Owner naming decision is
   requested.
3. **Build-time resolution is not waived for any of these.** The deferral is
   temporary by construction and fail-closed:
   `projection.validate_candidate` calls `validate_representation`, and
   `gate.py` maps its findings to `GateFailureCategory.SEMANTIC_VALIDATION`, so
   an outstanding obligation blocks publication exactly as an unresolved
   reference always did. Contract 2 independently makes unreviewed units
   publication blockers. **Nothing here creates a standing exception to
   build-time resolution, and nothing here authorizes a new corpus batch.**

| printed pointer | clause | kind | state |
|---|---|---|---|
| "see 'Rules Glossary'" → **Challenge Rating** | `main.monster_cr` | authored mechanical reference | `glossary.challenge_rating`, scope `srd-5.2.1/rules-glossary`. The target record is not authored yet, so validation reports one `unknown target record`. That is the intended state for a forward citation, matches speed-1's precedent, and blocks publication until the glossary batch lands. |
| "see 'Rules Glossary'" → **Expertise** | `stack.expertise` | authored mechanical reference | `glossary.expertise`, same scope, same finding, same block. Resolves with no change here once the Expertise entry is authored. |
| **the Skills table** | `list.skills_table` | **outstanding obligation** | Authored on `skill_list` with `source_text="Skills table"` and an empty target: validation reports `reference srd-5.2.1/rules-glossary:'Skills table': unresolved reference`. The pointer names mechanical content — the table "notes example uses for each skill proficiency as well as the ability check the skill most often applies to" — and is simply not authorable yet: the table is not an assembled record (57 leaves, container `d818241d`, under *Actions* in *Playing the Game*, reviewed by no batch). Closed by reviewing the Skills table as its own unit and filling in the key it mints. |
| "see 'Actions' later in 'Playing the Game'" | `skill.sources` | **outstanding obligation** | Authored on `skill_relevance_sources` with `source_text="Actions"`, empty target, same `unresolved reference` finding. Mechanical in substance — it says where the skill an action calls for is specified — and not authorable as one edge today: the sentence points at a whole series, and twelve per-action records already exist (`action.attack` … `action.utilize`, accepted by actions-1 over the Rules Glossary `[Action]` entries) with no single target among them. `AbilityCheckFact` already carries a `skill` field, currently `None` on all twelve, so the durable destination is each action record naming its skill — decided by a future batch over the *Actions* section, not by changing accepted content. |
| "described in 'Character Creation'" | `main.character_levels` | **informational navigation** | The parenthetical says where character level advancement is described. This unit's rule is complete without it: the table gives the bonus for every level and CR it prints, and nothing in the clause needs a value from Character Creation. It points outside the mechanical corpus, so there is no edge to record — it stays governing prose. |
| "The Proficiency Bonus table shows how the bonus is determined" | `main.table_pointer` | **internal navigation** | Points inside this same unit, at the component this proposal already contains, and is bound as supporting authority. No reference is needed or possible. |

In every case the pointer's **wording survives verbatim** inside the bound
governing prose, so nothing about the citation is lost.

### How the two outstanding obligations stay detectable

Each is two committed elements, not a note: the `ReferenceDraft` itself, and a
`ProvenanceClaim` binding it to the 5c leaf subspan the pointer was read from
(`list.skills_table`, `skill.sources`). `REFERENCE` is in
`PROVENANCE_REQUIRED_KINDS`, so neither half is optional. Verified against the
production validator and the production accept/load path:

| attempt | what happens |
|---|---|
| leave it as authored | `unresolved reference` on both, every build, alongside the two `unknown target record` findings. Four reference findings exactly, no more. |
| serialize and reconstruct | `accept_proposal` → `accepted_inputs_payload` → JSON → `load_accepted_inputs` returns both references with their empty targets and both provenance claims intact. The obligation survives persistence. |
| delete the reference, keep the provenance | `provenance reference[…]: claim for an undeclared element`. |
| delete the provenance, keep the reference | `reference […]: no provenance to a 5c leaf subspan`, **and** the `unresolved reference` finding persists. Removing the evidence does not remove the obligation. |
| review the destination and cite the same words elsewhere | a resolved sibling reference with the same `(scope, source_text)` does **not** close it: the `unresolved reference` finding stays, and validation adds `ambiguous … resolves to ['', 'play.proficiency']`. Destination coverage alone cannot discharge it. |
| fill in this reference's target | the finding disappears. This is the only thing that closes it. |

Covered by five tests in
`tests/ingestion/mechanical/test_proficiency_1_proposal.py`
(`test_the_deferred_links_are_authored_as_outstanding_obligations`,
`…_survives_serialization_and_reconstruction`,
`test_deleting_either_half_of_an_outstanding_link_is_reported`,
`test_a_resolved_sibling_citing_the_same_words_cannot_close_it`,
`test_filling_in_this_reference_is_the_only_thing_that_closes_it`), all through
production paths.

**What closing one costs, stated plainly.** Resolution is an edit to this
reference — that is, a change to Rules-Package content. Before acceptance the
route is regeneration, which is what `conditions-1` did at schema 3 when a
pre-acceptance identity was withdrawn. After acceptance there is no supersede
path: `acceptance._merged_collection` has no mechanism for replacing an accepted
reference, so an accepted outstanding obligation would have to be carried until
one exists. That limitation is pre-existing, is not introduced by this proposal,
and is **`out of scope`** for this pilot — it is not a defect this pilot may
implement away, and it is the reason this packet does not recommend accepting
the pilot before the two destinations are reviewed. The empty-target form does
not make that risk worse than the alternative: a guessed key carries the same
permanent-block risk *plus* the silent-coincidental-discharge risk above.

### Proposal identity after this change

The proposal was regenerated. Its meaning changed, so its identity changed:

| | before | after |
|---|---|---|
| proposal identity | `c941c262081eb2ba485ee6963b90c0a2bf79578662a2790baf703f5ed1cac219` | `11481e020ce08119938dcfd7e9df6a9f84c945f6ad63de2d5a47bcfc45110417` |
| file sha256 | `b74b6056688a1a6a3750cd1271fa7af6eb670cc05c16b6bf5f8e68f2442dadfa` | `a56829dde1db9281f8c3e1df78f0feb32f0496a2c50651739198deee8058a6c8` |
| bytes | 54,507 | 55,439 |

The exact semantic delta is **+2 `ReferenceDraft` elements with empty targets and
+2 `ProvenanceClaim` edges** (50 → 52). Nothing else moved: 47 spans, 13
components, 23 bindings, 8 bands, 22 expected rules, 30 leaves, the four-part
binding, and every prose/source binding are unchanged. **No new acceptance is
authorized by this packet, and none is claimed;** the delta is recorded here so
the new identity can be reviewed independently.

### Correction to the identification note

`.claude/review-notes/issue-5d-regular-section-pilot-IDENTIFICATION.md` states
that the Skills table "lives in actions-1's accepted territory." **It does
not.** Verified against the merged oracle:

* Skills table leaves: **57**, overlap with accepted leaves: **0**
* Proficiency section leaves: **31**, overlap with accepted leaves: **0**
* accepted leaves across the seven batches: **337**

`actions-1` accepted **Rules Glossary `[Action]` entries only** — 92 leaves, 13
records. The Skills table under *Playing the Game > Actions* is untouched
corpus. This does not change any decision in this proposal (the pointer is an
outstanding obligation either way), but it changes what a future batch may assume, so it is
recorded rather than quietly corrected.

## 8. Omissions, residue, and known boundaries

Stated plainly, because a review packet that omits its own residue is not
reviewable.

1. **Four reference findings, two of each kind** (§7): two `unknown target
   record` forward citations into the Rules Glossary, and two `unresolved
   reference` outstanding obligations. All four are expected, all four block
   publication, and the generator asserts the set as an exact tuple.
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
7. **Two outstanding mechanical links** (§7): the Skills table and the *Actions*
   section. Both are now authored in the proposal with empty targets, so both
   fail validation until the real destination is named, and neither can be
   discharged by a note or by coincidence. They are **not** a permanent exception
   to build-time resolution. No batch is authorized here to review those
   destinations. `patched` — the tracking defect is closed; the destinations
   themselves stay future work.
8. **No post-acceptance supersede path for an accepted reference** (§7).
   `acceptance._merged_collection` can merge accepted content but cannot replace
   an element of it, so an outstanding obligation accepted today would have to be
   carried until such a path exists; pre-acceptance the route is regeneration,
   as `conditions-1` did at schema 3. Pre-existing limitation, not introduced
   here, and **`out of scope`** for this pilot. It is why this packet does not
   recommend accepting the pilot ahead of the two destinations.
9. **Whether the per-kind application clauses need a typed field is held, not
   answered** (§6). `skill_proficiency_application`, `saving_throw_proficiency`,
   `weapon_proficiency`, `tool_proficiency` and `bonus_does_not_stack` state
   where the Proficiency Bonus is added and how often. Whether that mapping is
   Rules-Package-supplied typed data or fixed by sheet or adapter semantics is
   not settled by anything adopted: ADR-015 Decision 7 fixes the assembly
   **input list** and the adapter's d20-only **breadth**, not which input carries
   the mapping; ADR-005d's rejected alternative 7 and #137's *"prose cannot
   conceal a field required by such a use"* forbid deciding it from adapter
   coverage; and contract 2's own test is circular until the ownership call is
   made. **`owner decision needed`** — the exact question, both readings with
   their citations, and the cost of the affirmative answer are in §6. Nothing is
   implemented against it and no field was invented to close it.
10. **Prose does not discharge a later operation's field.** If an operation
   later needs an input this section holds only as prose — the
   class-construction constraint of `saves.class_minimum` ("at least two saving
   throws" per class), say, or the legality statement of `weapon.anyone` —
   contract 2 and ADR-005d Decision 2 require that field **before** the
   operation relies on the rule. That obligation is not claimed to be
   discharged here.
11. **The tool-Advantage trigger is unrepresented, deliberately** (§6). Its
   consequence is typed; its three operands are two sheet states and one
   GameMaster judgment, and no closed applicability vocabulary states that
   conjunction. Recorded as `MIXED` + `CONTEXTUAL`; no trigger family is minted
   and no consumer is authorized to fire the fact.

## 9. What the pilot cost

Reported from run timestamps and the git history, with elapsed work, waiting,
and code footprint kept apart, because they scale for different reasons. No
throughput target, completion percentage or historical baseline is estimated
here. There is no recorded per-batch authoring time for any earlier batch, so
there is nothing to compare elapsed time against and none is invented.

### Elapsed time, waiting, and footprint are three different numbers

| what | measured | how |
|---|---|---|
| **dispatch to final pilot commit** | **2 h 09 m 29 s** (dispatch 2026-09-17 06:48:56.155 Z → `23f49d2` 08:58:25 Z) | the launcher record `issue-5d-proficiency-pilot-sep16-launch.json` and the commit timestamp. An observable **run interval** — not hands-on time, and not a bound on work. |
| **whole pilot run** | **2 h 47 m 50 s** (dispatch → 09:36:46.529 Z) | the matching `…-usage.json` `finished_utc`: the same run carried through CI waiting and reporting after the commit. That file also records **seven** context compactions and 306 agent turns. |
| **local gate wait, final pass** | **1,198 s ≈ 20 m** | `tests/ingestion` 867.97 s + `tests --ignore=tests/ingestion` 330.03 s. Waiting, not work, and it recurs on every pass. |
| **CI wait, final head** | **31 m 44 s** | run `35202642012`, created 08:59:15 Z, updated 09:30:59 Z, conclusion `success`. Also waiting. |
| **production footprint** | **199 insertions, 2 deletions, 3 files** | `representation.py` 128/1, `projection.py` 19/1, `schema_lift.py` 52/0. |
| **batch-specific footprint** | **1,151** generator + **534** proposal-test lines, no accept script | the generator and test as they now stand (1,109 and 224 at `23f49d2`; the growth is §7's outstanding-obligation authoring and its five proofs), plus the 1,782-line `PROPOSAL.json` and this packet, which are data and prose rather than program. |
| **mint maintenance** | **101 insertions, 41 deletions across 19 pre-existing files** | the schema-hash restamp; see the diagnosis below. |

Neither wait is interchangeable with either interval. The final local gate pass
falls **inside** the 2 h 09 m interval, so ~20 m of it is machine time rather
than authoring. CI run `35202642012` was created at 08:59:15 Z, fifty seconds
**after** the final pilot commit: its 31 m 44 s is outside the 2 h 09 m interval
and inside the 2 h 47 m run. The branch parent `72fab6e` is the PR #170 merge,
not the start of this authoring, so parent-to-commit elapsed time bounds nothing
here and is not reported.

**The correction rounds are separate runs, and have cost more than the pilot
did.** From the same launcher records, so these are the same kind of number as
above — run intervals, not hands-on time:

| round | interval | what it produced |
|---|---|---|
| review remediation 1 | **2 h 22 m 53 s** (`duration_ms` 8,572,767; `23f49d2` → `63e0ceb`), 133 agent turns, 2 compactions | the five-part correction round |
| review remediation 2 | **1 h 54 m 11 s** (`duration_ms` 6,851,165; `63e0ceb` → `281cf54`), 76 agent turns, 2 compactions | the three-part correction round |
| this Owner-review round | started 2026-09-18 03:22:33 Z from `281cf54`; its `…-usage.json` is written when the run ends, so no total is claimed for it here | items 1–3 of the Owner's review |

Two things follow from those numbers rather than from optimism. **Review
correction has taken more elapsed time than authoring the batch did** — 4 h 17 m
across the two completed rounds against the 2 h 48 m pilot run, and this is a
third round. And **most of those rounds' commits were documentation**, not code:
the same packet sections rewritten. That is the maintenance evidence this pilot
actually produced, and it argues against any claim that a second section would
be cheap.

**Batch-specific code: one generator, 1,151 lines.** Against the accepted
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
| **proficiency-1** | **1,151** (+534 test, no accept script) |

**These are file sizes, and a ratio between two of them is not a throughput
result.** Speed-1 is the nearest structural neighbour — the last batch authored
before the shared workflow merged — but its 3,604 lines and this batch's 1,151
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
family, its projection wiring, and one lift step. Additive: it adds a family and
its wiring and widens no existing family, vocabulary or field.

### Diagnosis 1 — the schema restamp is the real recurring maintenance

**Test fallout from minting schema 13, measured in five passes:** 76 → 25 → 4 →
0, then 1. The 76 → 25 step was one surgical restamp of `bounded_oracle.json`'s
schema block; 25 → 4 was a 37-site pin pass across 17 test files; 4 → 0 was a
5-site residual pass. The full-suite gate then found one further canary outside
the ingestion tree — `tests/services/rules_authority/`'s patch-layer
schema-hash assertion, which exists precisely to move when the representation
does — and restamping it closed the sequence.

That cost tracks the number of committed sites that pin a schema hash, not the
size of the schema change. The schema-12 mint at `eef9a08` modified **19
pre-existing non-`src` files** by 204 insertions and 97 deletions; this mint
modified **19 pre-existing non-`src` files** by 101 insertions and 41 deletions;
**17 files appear in both sets.** The two `src` deltas are not comparable work,
and no ratio is drawn between them: `eef9a08` is 612 insertions and 29 deletions
across 9 files and, by its own commit message, *“mints no fact family, no
vocabulary, no vocabulary member, no ownership form, no required field and no
intrinsic invariant”* — it carries one distinction for retained prose into the
serialized grammar. This mint is 199/2 across 3 files and adds one family. What
the two share is the restamp, and two mints is two data points rather than a
trend.

A counting note, so the figures are not read as more than they are. All four
restamp numbers above are `--diff-filter=M` over pre-existing files only.
`eef9a08`'s *total* non-`src` delta is larger — 769/97 across 22 files — because
it also **added** test modules in the same commit; those additions are not
restamp and are excluded here. Neither figure is pure hash-literal churn:
a modified file may also have gained assertions in the same commit.

### Diagnosis 1a — what was consolidated, and what stays pinned

Those sites are not one kind of thing, and the earlier version of this section
treated them as if they were. Separated:

* **Immutable historical anchors.** Every `SCHEMA_<n>_VERSION`/`SCHEMA_<n>_HASH`
  pair in `schema_lift.py`, and every accepted batch's frozen-prior assertion of
  the schema *it* was accepted under. A mint must never move these, and none
  were touched.
* **Independent canaries.** Three literal current-schema hashes whose whole job
  is to fail when representation meaning moves without review. They must not be
  able to agree with a shared helper by construction, so they stay written out
  where they are.
* **Repeated expectations of the *current* schema.** Which contract this build
  declares, which registered crossings a prior must make to reach it, and which
  version string is still unminted. Every copy was transcribed from the same
  registry, so a mint edited twenty transcriptions of one decision. This is the
  duplication, and it is the only thing consolidated.

The consolidation is one 99-line module in the suite's existing style,
`tests/ingestion/mechanical/_schema_pins.py`, the same shape as
`tests/api/_fixtures.py`. It states the three facts and a `crossings_from()`
slice over a written-out crossing registry. No schema framework, no fixture
indirection, no new test machinery.

| site | what it pins | disposition |
|---|---|---|
| `_schema_pins.py` | the three current-schema facts, each written out rather than read back from the production value it checks | **new shared home** |
| `test_speed_1_frozen_prior.py`, `test_cover_1_frozen_prior.py`, `test_areas_of_effect_1_frozen_prior.py`, `test_attitudes_1_frozen_prior.py` | each prior's expected crossing chain | `patched` — `crossings_from(SCHEMA_<n>_VERSION)`; each module's own historical anchor untouched |
| `test_accept_across_schema_succession.py`, `test_schema_6_succession.py` | the chains from schema 3 and schema 5 | `patched` — same helper |
| `test_committed_accepted_authority.py` | the 11-to-current chain, **and** the whole schema-3-to-current chain | `patched` for the first; the second **stays written out** as the independent full-chain canary |
| `test_schema_4_invariant_closure.py`, `test_schema_5_representation_corrections.py`, `test_speed_1_frozen_prior.py` | the current version/hash pair | `patched` — `CURRENT_SCHEMA_*` |
| `test_review_round_9_schema_version_payloads.py`, `test_schema_10_cover.py`, `test_schema_11_speed.py` | the next unminted version string | `patched` — `UNMINTED_SCHEMA_VERSION`, so the probe moves once per mint in one place instead of three |
| `test_representation_schema_identity.py` (`EXPECTED_SCHEMA_HASH`), `test_review_round_7_draft_exact_types.py`, `tests/services/rules_authority/test_review_round_5_component_patch_schema2.py` | the current schema hash, as a literal | **stays fixed** — independent canaries |
| `test_schema_12_practical_reliability.py`, `test_review_round_9_schema_version_payloads.py` (merged key-set rows) | one named version's own semantics: the sibling-refusal subtraction, and each version's merged component fields | **stays fixed** — per-version decisions, not repeats of which schema is current |
| `test_schema_13_proficiency.py`, `data/bounded_oracle.json` | this mint's own contract, and the fixture artifact's declared schema block | **stays fixed** — the mint's own statement, restamped deliberately |

One new test guards the consolidation itself:
`test_the_shared_schema_pins_are_the_registry_and_the_live_contract` asserts that
the crossing list *is* `lift_path` over the whole succession, that the declared
pair *is* the live contract, and that the probe string is in no recognised
contract. A mint that updates production and forgets the pins fails there, in one
place, with the reason named — so mutation detection is preserved rather than
traded away.

**Measured effect.** Files under `tests/` that name a current-schema fact
literally: **15 before, 6 after** (`git grep` over `SCHEMA_13_HASH`,
`SCHEMA_13_VERSION`, `5d-representation-schema-14` and
`5d-lift-schema-12-to-13`). Of the six, four are deliberate — the full-chain
canary, the two per-version modules, and this mint's own module — one is the JSON
fixture, and one is `_schema_pins.py` itself. The three literal-hash canaries sit
outside that grep by construction and stay as they are. So a sixth mint's restamp
is the fixture's schema block, this module's two lines plus one crossing row and
one probe bump, the three canaries, the full-chain canary, and the per-version
modules that genuinely state their own semantics.

No historical test was weakened and no generic schema framework was introduced.
The pins that remain exist deliberately: each is a canary that fails when
representation meaning moves, which is exactly what they are for, and an accepted
batch's frozen-prior test *must* keep asserting a literal.

### Diagnosis 2 — what is left that is batch-specific

The pilot did **not** need a large custom program. The entire batch-scoped
proof is three calls into merged services — `validate_partition(...,
require_complete=False)` per leaf, `review_unit_violations`, and standalone
`validate_representation` — plus the mutation check. Nothing about a regular
section, as opposed to a glossary entry list, required new machinery.

What remains genuinely per-batch, honestly:

* **The clause/component/fact tables in the generator.** This is source review
  written down. It is not removable tooling and should not be targeted.
* **Independent source-reviewed expectations.** A batch's identity pin and its
  expectations must not be regenerated from the output they check — that is
  contract 4, and it is the requirement. An earlier version of this section said
  a *hand-written test program per batch* is inherently non-removable; that
  overstated it and is withdrawn. What is mandatory is the **independence** of
  the expectations, not their form: a data table, a shared parameterized test and
  hand-written code all satisfy it, and the schema-pin consolidation above is an
  instance of moving from one form to another without weakening anything. This
  batch's proposal test is a reasonable form, not the only admissible one — and
  no new test framework is proposed, because no batch has demonstrated the need
  for one.
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
across 10 third-party packages, unchanged by this branch.

For the round that produced this revision, proportional to its delta: the whole
changed area, `tests/ingestion/mechanical`, **3,019 passed** in 178.65 s, and
`black`/`ruff` clean over 480 files. `mypy src/` is not rerun and no result for
it is claimed for this round — `src/` is untouched, and every change is under
`tests/ingestion/mechanical` or `.claude/review-notes/`, so the second suite
chunk (`tests --ignore=tests/ingestion`) has no changed input either. Full-suite
and audit evidence for the final head is the CI run cited in the PR
description.

## 10. How to verify this packet

```bash
# regenerate the proposal (deterministic; overwrites with identical bytes)
python .claude/review-notes/issue-5d-batch-proficiency-1-generator.py

# the committed retained proposal, through the production path
pytest tests/ingestion/mechanical/test_proficiency_1_proposal.py -q --no-cov

# the new family's numeric contract and the schema-12/13 boundary
pytest tests/ingestion/mechanical/test_schema_13_proficiency.py -q --no-cov

# the consolidated schema pins, against the registry and the live contract
pytest tests/ingestion/mechanical/test_schema_6_succession.py -q --no-cov
```

`test_proficiency_1_proposal.py` pins the identity, runs
`review_unit_violations` on the loaded artifact, asserts **all eight bands** as
an exact set, proves by mutation that dropping the 29–30 band **is reported**,
covers §7's two outstanding obligations in five tests — authored state,
survival through `accepted_inputs_payload` and `load_accepted_inputs`, omission
of either half, a resolved sibling failing to discharge one, and the single edit
that does discharge one — and exercises `accept_proposal`
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
