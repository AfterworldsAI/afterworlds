# `proficiency-1` review packet — CRD Issue 5d, first regular-section pilot

**Status: ACCEPTED 2026-09-20 (UTC) by the Owner, as reviewed.** This
packet described an unaccepted proposal when it was written and is kept as
written; the proposal it describes is now accepted authority, recorded in
`issue-5d-proficiency-ACCEPTANCE-CHECKPOINT.md` and committed in
`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json`.
Nothing here was edited to match the acceptance, so every claim below is
still the claim the reviewer read. Acceptance published, activated and
merged **nothing**.

This packet is the human-readable half of the proposal over
**SRD 5.2.1 > Playing the Game > Proficiency**. It exists so a reviewer can
check the proposal against the printed source without reading 60 KB of JSON,
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
| bytes | 61,375 |
| `proposal_identity` | `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` |
| file sha256 | `c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d` |
| reviewed and approved in PR #171, superseded by §7's Round 4, **never accepted into the corpus** | identity `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4`, sha256 `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324`, 61,329 bytes — those are the bytes the Owner approved, and they are reproducible from the current ones by blanking exactly two target strings (§7, Round 4), which a test does |
| superseded, never accepted | identity `c941c262…`, sha256 `b74b6056…`, 54,507 bytes — the first regeneration, which authored §7's two outstanding obligations; then identity `11481e02…`, sha256 `a56829dd…`, 55,439 bytes — superseded by the typed rule inputs and the scope-key correction; then identity `a6fc5285…`, sha256 `eb0fafb0…`, 60,468 bytes — superseded by the two stated bonus uses (§6) |
| proposal schema | `5d-proposal-2` |
| representation schema | `5d-representation-schema-15` |
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
| typed facts | 18 (8 bonus bands + 4 applications + 3 operation limits + 2 bonus uses + 1 advantage) |
| expected rules on the unit | 30 |
| provenance claims | 63 |
| references | 4 |

Findings from the merged services, on this batch's scope:

* `validate_partition(..., require_complete=False)` per leaf — **0 findings**
* `validate_reason_codes` — **0 findings**
* `review_unit_violations` — **0 findings**
* `validate_representation` — **4 findings**, all `unknown target record`: two
  glossary citations and two *Playing the Game* citations, naming the four
  records `proficiency-destinations-1` proposes (§7, Round 4). All four block
  publication of this proposal alone; all four resolve in the merged data.

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
| 3 | the bonus applies to a D20 Test **when** the creature has proficiency in a skill, in a saving throw, or with an item it uses to make that test | `main.d20_test` | exact prose on the umbrella clause; the applicability condition is not reduced. The four per-kind clauses below it each carry one `ProficiencyApplicationFact` naming the roll the source states that kind's bonus reaches (§6) |
| 4 | it is **also** used for spell attacks and spell save DCs | `main.spells` | exact prose, separate clause, **and** two `ProficiencyBonusUseFact`s — `spell_attack` and `spell_save_dc`. Neither is an application: the sentence names no proficiency kind, and a spell save DC is not a roll (§6) |
| 5 | the bonus can't be added **more than once** to a roll or number | `stack.once` | exact prose **and** `ProficiencyBonusOperationLimitFact(add, maximum_applications=1)`; its own expected rule |
| 6 | **exception:** it may occasionally be multiplied or divided before being added | `stack.scaling` | exact prose, and the printed order is carried by `precedes=add` on both scaling limits — the source says *before* being added, and halving after adding is a different number |
| 7 | **limit on that exception:** multiplied only once and divided only once | `stack.once_each` | exact prose **and** two limit facts, `multiply` and `divide`, each `maximum_applications=1`; same expected rule as #6, so the exception and its limit cannot be accepted apart |
| 8 | Expertise doubles the bonus for certain ability checks | `stack.expertise` (supporting) + reference | the example is retained verbatim and cites the glossary record (§7) |
| 9 | the **GM has the ultimate say** on whether a skill is relevant | `skill.gm_say` | its own component, `gamemaster_latitude` — see §6 |
| 10 | without proficiency a creature **can still** make the check, but adds no bonus | `skill.without_a` + `skill.without_b` | one rule stated across the page break; both fragments are in one expected rule, so half of it cannot be accepted alone |
| 11 | tool proficiency adds the bonus to **any ability check that uses the tool** | `tool.checks` | exact prose **and** `ProficiencyApplicationFact(tool → ability_check)`. Which tools the creature is proficient with, and whether this check uses one, stay off this corpus |
| 12 | **and Advantage too**, **if** you have proficiency in the skill that's also used with that check | `tool.advantage` | typed `AdvantageFact` carrying `requires_proficiencies=(skill, tool)` — the conjunction the source prints, stated explicitly rather than left to a reader — **and** exact prose. The relevance half stays the GameMaster's; see §6 |
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

It did expose a **third** live reading of the seam, which is why the question
below was not this pilot's to answer. A sheet that stores the summed skill
modifier has *already applied* proficiency before any adapter runs. Under that
shape neither the adapter nor the rule slice needs the mapping at all — and which
of them owns it is Character Sheet Model policy, #137's 2b, still on this pilot's
stop-list and **not** decided by the Owner decision below, which settles what the
Rules Package supplies and nothing about how a sheet stores it.

### The question this pilot put, and the Owner's answer

> **Is the mapping from a proficiency kind to the D20 Test its bonus reaches —
> together with the add-once, multiply-or-divide-at-most-once constraint on that
> sum — Rules-Package-supplied typed data, or is it fixed by sheet or adapter
> semantics?**

**Reading A — fixed by sheet or adapter semantics.** ADR-015 Decision 7's
*"covers d20 semantics only"* permits the mapping to be one of those
hand-authored semantics, and nothing accepted excludes it; the stored-skill-
modifier shape above is a live implementation of exactly that. Under A the five
clauses held below would be complete as exact prose for explanation, no input
would be missing, and the pilot's representation would have been right as first
proposed.

**Reading B — Rules-Package-supplied.** Decision 7 names the *rule slice* as an
assembly input, and the rule slice is this projection's content, not the
adapter's. ADR-005d's rejected alternative 7 forbids letting adapter breadth
choose representation breadth, and #137 says prose *"cannot conceal a field
required by such a use"*. Under B a typed application fact on each of the five
is the missing input, and prose is concealing it. **This is the reading the Owner
took**, in the bounded form stated below.

**Why the citations did not decide it.** Contract 2's test is *which identified
code-owned operation needs a separate structured field*. Whether modifier
assembly needs the mapping as a field is precisely what the ownership call
determines, so the test was circular until that call was made. Neither reading
could be derived from the other's evidence, and both were consistent with
everything adopted. That is why the question was put to the Owner rather than
settled here.

**Resolved by Owner Decision 2026-09-18**, recorded at ADR-005d Decision 4 as an
amendment. Verbatim:

> "For the Proficiency section, the Rules Package supplies structured inputs
> governing where proficiency applies, its addition and scaling limits, and the
> fixed condition granting tool-related Advantage. Character-specific
> proficiencies remain on the sheet; relevance judgment remains with the
> GameMaster; handwritten code performs validation and execution.
> This authorizes the smallest bounded representation and tests needed for those
> uses. It does not require structuring every reducible passage or implementing
> downstream sheet/adapter behavior in 5d."

The authority for the change is that decision and nothing else. The adapter
evidence above is not re-read as support for it — it was not evidence for either
reading before, and a decision does not turn it into evidence after. **Reading A
is superseded, Reading B is authorized in the bounded form the decision states,
and neither is reopened here.** The held alternatives that this packet and the PR
Architecture Notes carried are superseded with it.

What that authorizes is narrower than Reading B as posed. The decision names
three uses — where proficiency applies, the addition and scaling limits, and the
tool-Advantage condition — and explicitly does not require structuring every
reducible passage or any downstream sheet or adapter behavior. So schema 14 minted
exactly those three and stopped.

A later source review of the decision's *first* clause — **where** proficiency
applies — found that clause incompletely represented. The opening paragraph's
last sentence states two further uses of the bonus and was left as prose alone:
*"The bonus is also used for spell attacks and for calculating the DC of saving
throws for spells."* The four per-kind pairings do not restate it; none of them
mentions a spell. Schema 15 mints one family for those two uses and nothing else.
The two mints together are the whole of what this decision authorizes on this
section; §8 residue 10 still stands for everything else it holds as prose.

### What schemas 14 and 15 add, and why each field has to exist

Three families and one field on an existing one: two families and the field at
schema 14, one family at schema 15. The justification for each is its
**required use** and the **consequence of omitting it** — not that the prose
happens to be reducible, and not that no vocabulary existed for it. Reducibility
alone would justify structuring the whole section, which the decision declines;
an absent vocabulary is a cost of minting, not a reason to mint.

| field | required use | consequence of omission |
|---|---|---|
| `ProficiencyApplicationFact.proficiency` × `.roll` | The Rules Package is now the supplier of *which roll a kind of proficiency reaches*. Validation of an assembled D20 Test modifier reads the pairing from here. | The mapping would live only in this section's prose, and contract 2 bars a consumer from reading a trusted value out of prose: *"choosing prose does not authorize runtime interpretation into trusted values"*. An erratum moving where the bonus applies would then change no trusted value at all, and the pairing would be addressable only as prose. What typing it does *not* buy is re-pairing by override — the pairing is closed by invariant, and the paragraph below states exactly what that leaves an override able to do. |
| `ProficiencyBonusOperationLimitFact.operation` × `.maximum_applications` | Validation of a sum: *"can't be added to a roll or another number more than once."* | Nothing in the projection would state the limit, so two effects each adding the bonus would be indistinguishable from one legal addition. The rule would be enforceable only by an adapter that had been told it out of band. |
| `ProficiencyBonusOperationLimitFact.precedes` | Fixes the printed order: the multiplication or division happens **before** the addition. | The count alone leaves the arithmetic underdetermined. Halving after adding and adding after halving are different numbers, and the source prints one of them. A limit fact without the ordering would look complete and permit the wrong result. |
| `ProficiencyBonusUseFact.use` | The same decision clause — **where** the bonus applies — read against the sentence that states two uses outside every pairing: spell attacks, and the DC of saving throws for spells. A consumer asking whether the Rules Package states that the bonus reaches a spell attack gets an answer from data. | The sentence would remain prose alone while the four sentences beside it were typed, so the section would state *where the bonus applies* in four places and be silent on the two the same paragraph prints. Contract 2 bars reading the missing two out of prose, so the asymmetry would read as a deliberate exclusion. The fact states the use and nothing more: no formula, no spellcasting ability, no target DC, no proficiency that grants it, and no consumer. |
| `AdvantageFact.requires_proficiencies` | States the section's one conjunction — proficiency in a skill **and** a tool that both apply to the check — on the fact whose consequence it gates. | The `AdvantageFact` would read as an unconditional Advantage on ability checks, which the source does not print. The alternative, leaving the condition to prose, is the same contract-2 problem: a consumer would have to interpret the sentence to know whether the typed consequence applies. |

The three fields that are **not** here matter as much. `ProficiencyApplicationFact`
carries no ability and no skill, and no field naming *which* skills, saving
throws, weapons or tools a creature has: Invariant 9 makes the sheet the owner of
that, and this corpus does not hold it. `ProficiencyBonusUseFact` is narrower
still — it carries a `use` and no `roll`, because a spell attack is a roll and a
spell save DC is not, and a family that forced both into one roll-shaped field
would state something the sentence does not. It reuses neither `AttackKind`,
whose members would impose a melee/ranged distinction the sentence never draws,
nor `DcKind.SPELL_SAVE_DC`, which is a vocabulary of *how a DC is set* rather
than a statement that the bonus is used in setting one. There is no relevance field, because
whether a skill is *"also used with that check"* is the GameMaster's call
(`skill_relevance_judgment`, `gamemaster_latitude`). And there is no trigger
family and no evaluator: nothing here computes, fires, or decides applicability.

The pairing is closed by invariant, not merely by what was authored:
`ProficiencyApplicationFact(skill → attack_roll)` is refused with *"a skill
proficiency is stated as applying to ability_check, not attack_roll"*, so a
combination the source never prints cannot be stored. `requires_proficiencies`
is likewise canonical — ordered, non-repeating, and never of length one, because
a conjunction of one is the plain conditional the governing prose already states.

**What that leaves an override able to do, exactly.** `REPLACE` on a fact target
carries a complete replacement fact and rebuilds it through the same builder and
the same family invariants as an authored one, so the admitted shapes are the
invariants' and not the override layer's:

* **Every** fact in this record is `DISABLE`-addressable by its content-derived
  key, and any component is `APPEND`-addressable.
* A `ProficiencyBonusOperationLimitFact` may be replaced or appended by any limit
  with `maximum_applications >= 1` and `precedes` not itself — so a house rule
  raising the multiplication ceiling, or changing which operation precedes which,
  applies. A limit of zero does not: the source states how many times an
  operation may happen, not that it may not.
* An `AdvantageFact` may be replaced by one whose `requires_proficiencies` is an
  ordered, non-repeating conjunction of `ProficiencyKind` members of length 0 or
  2+.
* A `ProficiencyApplicationFact` may be replaced only by one of the four pairings
  `_PROFICIENCY_APPLICATION_ROLLS` already states. **An erratum moving a
  proficiency kind's roll is therefore not reachable by override**; it needs a
  later authorized change to that table — a new schema — and the same is true of
  a fifth proficiency kind or a third bonus use, each of which is a closed
  vocabulary. The family is deliberately *not* widened to make the override
  route work: widening it to satisfy an authoring convenience would admit
  pairings the source never prints.
* A `ProficiencyBonusUseFact` may be replaced by the other member of its
  vocabulary, which given a two-member closure is equivalent to disabling one and
  duplicating the other; there is nothing else in its shape to vary.

Both the supported replacement and the refused re-pairing are proved against the
real override ingress rather than described — see §10's test list.

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
| **basis and umbrella** | `proficiency_bonus_basis`, `proficiency_bonus_application` | (1) plus (2) as a statement | the umbrella sentence itself has none — it states *that* the bonus reaches D20 Tests a creature is proficient in, and its two operands are the per-kind clauses below and sheet state, so a field for it would restate the four `ProficiencyApplicationFact`s. The clause beside it is a different matter: `main.spells` states two uses no pairing restates, and those are typed | exact prose bound, and the `Challenge Rating` pointer is authored (§7) | regeneration restates a use | the two `ProficiencyBonusUseFact`s are `DISABLE`-addressable and replaceable within their two-member closure; the umbrella prose is addressable at the prose grain | **MIXED** — two `ProficiencyBonusUseFact`s plus the governing prose, which the umbrella keeps because it states more than those two uses |
| **applying it, per kind** | `skill_proficiency_application` (`skill.proficient`), `saving_throw_proficiency` (`saves.bonus`), `weapon_proficiency` (`weapon.attack_rolls`), `tool_proficiency` (`tool.checks`) | the rule (2), per Owner Decision 2026-09-18 | the pairing of a proficiency kind with the roll its bonus reaches, supplied as typed data rather than read from prose | unchanged — the exact governing prose stays bound with span-exact provenance beside the fact | regeneration restates a pairing, and an erratum moving where the bonus applies now changes a trusted value that states it — by regeneration before acceptance, or by a later authorized schema change, not by override | `DISABLE` any `ProficiencyApplicationFact`; `REPLACE` or `APPEND` one **within the four pairings the invariant admits**; the prose grain is unaffected. Addressable, but not re-pairable — see the paragraph above | **MIXED** — one `ProficiencyApplicationFact` each, plus the governing prose. `tool_proficiency` also keeps its `AdvantageFact` |
| **the stacking limits** | `bonus_does_not_stack` (`stack.once`, `stack.scaling`, `stack.once_each`) | the rule (2), same decision | the add-once limit, the at-most-once multiply and divide, and the printed order between them | exact prose bound; the `Expertise` pointer is authored (§7) | regeneration restates a limit | `REPLACE` or `APPEND` a `ProficiencyBonusOperationLimitFact` | **MIXED** — three limit facts plus the governing prose |
| **which skill is relevant** | `skill_relevance_sources`, `skill_relevance_judgment` | judgment, and an unmodelled pointer | none; see the tool-Advantage note below for how the judgment enters | both clauses bound, one reason code each | regeneration | prose grain | **PROSE_BOUND**, two reason codes |
| **pointers to data held elsewhere** | `skill_list`, `determining_skills`, `equipment_proficiency` | another unit's content | none here; a field would pre-empt a batch that has not reviewed its source | exact prose bound | regeneration | prose grain | **PROSE_BOUND**; `skill_list` now also carries an **outstanding** `ReferenceDraft` to the Skills table, so the deferral is tracked rather than described (§7) |

**What the family inspection found.** No existing family could carry "add the
Proficiency Bonus to *X*": the nearest, `DerivedQuantityFact`, derives a value
from an ability modifier over a `TimeUnit`. `RollSpec`/`RollContext` already
state which roll a fact is about — `ATTACK_ROLL`, `ABILITY_CHECK`,
`SAVING_THROW`, `D20_TEST` — so the *target* vocabulary existed and is reused
unchanged; what did not exist is the pairing family and the kinds it pairs. That
absence was never itself the argument for minting, in either direction: the
justification is the required-use table above. **The rebuild of this section
changed no representation on its own** — the representation moved with Owner
Decision 2026-09-18, and §7 records the resulting identity.

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
* **The conjunction of the two sheet-state operands is now explicit**, per Owner
  Decision 2026-09-18: `requires_proficiencies=(skill, tool)` on the same
  `AdvantageFact` that carries the consequence. It states *that both are
  required*, in the source's order of mention made canonical; it does not name
  which skill or which tool, and it does not carry the relevance operand. A
  reader of the fact can no longer mistake the Advantage for unconditional, and
  a consumer still cannot fire it, because the two proficiencies are sheet state
  and the third operand is a judgment.
* **So what is missing to fire this fact is trigger operands, not a
  discretionary application path.** 15c is one path that *supplies*
  GameMaster-selected judgments; it is not where a deterministic consequence
  goes to be executed, and routing the consequence there would misfile a fixed
  source rule as a GM-selected effect. The decision is explicit on this: the
  consequence "must neither become unconditional nor be assigned to
  discretionary 15c simply because relevance requires judgment." No closed
  applicability vocabulary states the relevance operand, and this pilot mints
  none for it.
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

**Three new families, and one widened one.** Schema 13 added
`ProficiencyBonusBandFact` — `bonus: int`, `maximum: int`, `minimum: int | None`,
the minimum that states one printed row, with the first band carrying
`minimum=None` (§5 #1). Schema 14 adds `ProficiencyApplicationFact` and
`ProficiencyBonusOperationLimitFact` with the two vocabularies they need,
`ProficiencyKind` and `ProficiencyBonusOperation`.

**`AdvantageFact` is widened, and that is a change from what this packet
previously claimed.** Earlier revisions said "no existing family, vocabulary or
component field was widened"; that was true of schema 13 and is **no longer
true**. `requires_proficiencies: tuple[ProficiencyKind, ...]` is a new field on
an accepted family. It is registered omit-when-empty under ADR-005d Decision 6's
post-schema-3 rule, so every one of the 26 `AdvantageFact`s in the committed
accepted authority still serializes as exactly `['family', 'roll', 'state']` and
keeps its fact key and its identity: **no accepted artifact is restamped by this
mint.** `RollSpec`, `RollActor` and `RollContext` are reused unchanged, and every
other clause reuses an existing prose-retention code.

**The widened field refuses a malformed value instead of erasing it, and that is
a correction to how it was first written.** The builder read
`payload.get("requires_proficiencies") or ()` before checking the type, so a
*present* value that happened to be falsy — `false`, `0`, `""`, `{}` or an
explicit `null` — was read as *"no conjunction"* and canonicalized into a payload
with the key absent. A malformed condition disappeared silently, and the record
that came back out looked well-formed. All five are now refused with the same
*"is not a list"* message that a non-empty wrong type already raised, at each of
the three ingresses that can carry one: the fact builder, the override patch
builder, and reconstruction from the store. An **absent** key and an explicit
**empty list** both still build the same fact with the same key and canonicalize
back to the accepted three keys, because that is what every accepted
`AdvantageFact` means and restamping one would be a contract change nobody
authorized.

**Sibling audit — silent coercion of a present structured value.**

| | |
|---|---|
| **family** | a truthiness test standing in for a type check, so a present malformed value is coerced to a default rather than refused |
| **trigger** | one review finding on `requires_proficiencies`; the family, not the line, is what the fix had to cover — hence three ingresses and six values rather than the one non-empty string the earlier test probed |
| **siblings inspected** | `AbilityCheckFact.alternatives`, the nearest structural neighbour: an optional sequence field on an accepted family, read through the same builder. **Already safe** — it takes an explicit default and type-checks before use. `any_of_terms`, which does use the truthiness form: **out of scope.** It predates this change, no part of this mint reaches it, and one finding on a field this change introduced is not authority for a parser-wide cleanup. Recorded here so it is visible rather than quietly carried. |
| **coverage** | six values × the builder, six × the override patch builder, one × reconstruction, plus the absent/empty-list compatibility pair; §10 lists them |

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

> **Read Round 4 first.** Everything below that calls those two pointers
> *outstanding* records the state the Owner approved in PR #171. All four
> pointers now name a reviewed destination. The rows, the finding block and the
> five test names in the rest of §7 are superseded by **Round 4** at the end of
> this section; they are kept because the approved bytes are still reproducible
> from the current ones, and because the reasoning for the empty-target
> mechanism is what constrains the keys that replaced it.

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
| **the Skills table** | `list.skills_table` | **outstanding obligation** | Authored on `skill_list` with `source_text="Skills table"`, scope `srd-5.2.1/playing-the-game` and an empty target: validation reports `reference srd-5.2.1/playing-the-game:'Skills table': unresolved reference`. The pointer names mechanical content — the table "notes example uses for each skill proficiency as well as the ability check the skill most often applies to" — and is simply not authorable yet: the table is not an assembled record (57 leaves, container `d818241d`, under *Actions* in *Playing the Game*, reviewed by no batch). Closed by reviewing the Skills table as its own unit and filling in the key it mints. |
| "see 'Actions' later in 'Playing the Game'" | `skill.sources` | **outstanding obligation** | Authored on `skill_relevance_sources` with `source_text="Actions"`, scope `srd-5.2.1/playing-the-game`, empty target, same `unresolved reference` finding. Mechanical in substance — it says where the skill an action calls for is specified — and not authorable as one edge today: the sentence points at a whole series, and twelve per-action records already exist (`action.attack` … `action.utilize`, accepted by actions-1 over the Rules Glossary `[Action]` entries) with no single target among them. `AbilityCheckFact` already carries a `skill` field, currently `None` on all twelve, so the durable destination is each action record naming its skill — decided by a future batch over the *Actions* section, not by changing accepted content. |
| "described in 'Character Creation'" | `main.character_levels` | **informational navigation** | The parenthetical says where character level advancement is described. This unit's rule is complete without it: the table gives the bonus for every level and CR it prints, and nothing in the clause needs a value from Character Creation. It points outside the mechanical corpus, so there is no edge to record — it stays governing prose. |
| "The Proficiency Bonus table shows how the bonus is determined" | `main.table_pointer` | **internal navigation** | Points inside this same unit, at the component this proposal already contains, and is bound as supporting authority. No reference is needed or possible. |

In every case the pointer's **wording survives verbatim** inside the bound
governing prose, so nothing about the citation is lost.

### Correction: the two outstanding pointers resolve in *Playing the Game*

Both outstanding obligations were authored with
`scope_key = "srd-5.2.1/rules-glossary"`. That was wrong, and is corrected to
`srd-5.2.1/playing-the-game` for those two only.

`ReferenceDraft.scope_key` is the **committed resolution scope** — where this
edge is to be resolved, not where the citing text sits. Both of these point into
*Playing the Game*: the Skills table is printed in that part, under *Actions*,
and the *Actions* pointer names a section of it in so many words ("see 'Actions'
later in 'Playing the Game'"). Committing them to the glossary scope stated that
a glossary entry is the thing that closes them, which is false in both cases and
carries a specific hazard: a later Rules Glossary batch reviewed in that scope
could have looked like the discharge of an obligation it never carried. The
originating obligation must not be silently discharged by a destination reviewed
elsewhere.

The two genuinely glossary-directed references, `Challenge Rating` and
`Expertise`, are **unchanged** — those really do resolve against glossary
records, and their `unknown target record` findings are unchanged too.

Nothing else moves with this. Both destinations stay **empty**; no final target
identifier is invented, no destination is ingested, and no acceptance is
implied. The standalone finding set changes only in which scope it names:

```
reference srd-5.2.1/playing-the-game:'Actions': unresolved reference
reference srd-5.2.1/playing-the-game:'Skills table': unresolved reference
reference srd-5.2.1/rules-glossary:'Challenge Rating': unknown target record glossary.challenge_rating
reference srd-5.2.1/rules-glossary:'Expertise': unknown target record glossary.expertise
```

`test_proficiency_1_proposal.py` asserts the `(source_text, scope_key)` set
exactly, so the correction cannot silently revert, and the five
outstanding-obligation proofs above run against the corrected scope.

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

### Proposal identity after each change

The proposal was regenerated in each round. Its meaning changed, so its identity
changed. Both steps are recorded; neither intermediate artifact was accepted.

**Round 1 — authoring the two outstanding obligations.**

| | before | after |
|---|---|---|
| proposal identity | `c941c262081eb2ba485ee6963b90c0a2bf79578662a2790baf703f5ed1cac219` | `11481e020ce08119938dcfd7e9df6a9f84c945f6ad63de2d5a47bcfc45110417` |
| file sha256 | `b74b6056688a1a6a3750cd1271fa7af6eb670cc05c16b6bf5f8e68f2442dadfa` | `a56829dde1db9281f8c3e1df78f0feb32f0496a2c50651739198deee8058a6c8` |
| bytes | 54,507 | 55,439 |

The delta was **+2 `ReferenceDraft` elements with empty targets and +2
`ProvenanceClaim` edges** (50 → 52). Nothing else moved.

**Round 2 — the typed rule inputs and the scope-key correction.**

| | before | after |
|---|---|---|
| proposal identity | `11481e020ce08119938dcfd7e9df6a9f84c945f6ad63de2d5a47bcfc45110417` | `a6fc5285ced73ea55901ad6fbcbc94c399ca44491791385d5e28132359517fba` |
| file sha256 | `a56829dde1db9281f8c3e1df78f0feb32f0496a2c50651739198deee8058a6c8` | `eb0fafb06c8891aeee0e9ccf416f46067b855b6504c6653c2172cdbd3bb71055` |
| bytes | 55,439 | 60,468 |
| representation schema | `5d-representation-schema-13` / `39710a37…` | `5d-representation-schema-14` / `14284d53…` |

The exact semantic delta, component by component:

| change | where |
|---|---|
| **+4 `ProficiencyApplicationFact`** | `skill_proficiency_application` (skill → ability_check), `saving_throw_proficiency` (saving_throw → saving_throw), `weapon_proficiency` (weapon → attack_roll), `tool_proficiency` (tool → ability_check) |
| **+3 `ProficiencyBonusOperationLimitFact`** | `bonus_does_not_stack`: `add`/1, `multiply`/1 `precedes=add`, `divide`/1 `precedes=add` |
| **+1 field on 1 existing fact** | `requires_proficiencies=('skill','tool')` on `tool_proficiency`'s `AdvantageFact` |
| **4 components move `prose_bound` → `mixed`** | the four above; `tool_proficiency` was already `mixed` |
| **+9 `ProvenanceClaim` edges** | 52 → 61, one per new fact, each `CONTEXTUAL` onto the span its clause was read from |
| **+7 expected rules** | 22 → 29 |
| **2 `scope_key` corrections** | the two outstanding obligations, `rules-glossary` → `playing-the-game` |

Unchanged: 47 spans, 13 components, 23 prose bindings, 8 bands, 30 leaves (1
excluded by 5c), 4 references, the four-part release binding, the Speed-style
data/scope order, and every prose/source binding. **No new acceptance is
authorized by this packet, and none is claimed;** the delta is recorded here so
the new identity can be reviewed independently.

**Round 3 — the two stated bonus uses.**

| | before | after |
|---|---|---|
| proposal identity | `a6fc5285ced73ea55901ad6fbcbc94c399ca44491791385d5e28132359517fba` | `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4` |
| file sha256 | `eb0fafb06c8891aeee0e9ccf416f46067b855b6504c6653c2172cdbd3bb71055` | `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324` |
| bytes | 60,468 | 61,329 |
| representation schema | `5d-representation-schema-14` / `14284d53…` | `5d-representation-schema-15` / `e87e0bac…` |

The exact semantic delta:

| change | where |
|---|---|
| **+2 `ProficiencyBonusUseFact`** | `proficiency_bonus_application`: `spell_attack`, `spell_save_dc`, both read from `main.spells` |
| **1 component moves `prose_bound` → `mixed`** | `proficiency_bonus_application`; its governing prose is retained, because the umbrella states more than these two uses |
| **+2 `ProvenanceClaim` edges** | 61 → 63, one per new fact, each `CONTEXTUAL` onto `main.spells` |
| **+1 expected rule** | 29 → 30, family-granular on `main.spells`; per-use omission is caught by the source-reviewed expectation in `test_schema_14_proficiency_inputs.py`, because `ExpectedRule` states a family's presence on a span and both uses are read from one span |

Unchanged: 47 spans, 13 components, 23 prose bindings, 8 bands, 30 leaves (1
excluded by 5c), 4 references, the four-part release binding, the Speed-style
data/scope order, every prose/source binding, and every fact schema 14 minted.
**No new acceptance is authorized by this packet, and none is claimed.**

### Round 4 — all four pointers name a reviewed destination

The Owner approved the Round 3 bytes and authorized reviewing and authoring the
four destinations. They are proposed in a second batch,
`.claude/review-notes/issue-5d-batch-proficiency-destinations-1-PROPOSAL.json`
(identity `01603c7f9a3b14f9c90e63e03e32da7c75b119109f0c251e8b428d91b0765a5d`),
reviewed in its own packet,
`.claude/review-notes/issue-5d-batch-proficiency-destinations-1-REVIEW-PACKET.md`.
This proposal changes only to point at them.

| | before | after |
|---|---|---|
| proposal identity | `c71f81044f003e2845e33e95a844c995aeee00282b0808303320200f164e8ec4` | `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` |
| file sha256 | `55ac577f1ff25f37c8676a49c63e246588ec5c52cff58bb79205a4a459be8324` | `c4c12fd321019e28d8eb05c986c80cc4d3b4f206fd50fdb26c04fb17ace85d5d` |
| bytes | 61,329 | 61,375 |
| representation schema | `5d-representation-schema-15` / `e87e0bac…` | **unchanged** |

**The whole delta is four scalars.** Diffed leaf by leaf against the committed
Round 3 JSON: `references[2].target_record_key` and `references[3]` gain
`play.skills` and `play.actions`, and the two `ProvenanceClaim.target_key`
tuples that identify those same references gain the same two strings in their
fifth position. +46 bytes is exactly `play.skills` and `play.actions` twice.
No span, component, fact, band, prose binding, expected rule, leaf or binding
part moves, and no schema is restamped — which is why the approved bytes are
still reproducible, and `test_exactly_two_target_strings_separate_this_from_the_reviewed_bytes`
blanks those two targets and their two provenance tuples and derives
`c71f8104…` again.

The standalone finding set is now four of one kind rather than two of each:

```
reference srd-5.2.1/playing-the-game:'Actions': unknown target record play.actions
reference srd-5.2.1/playing-the-game:'Skills table': unknown target record play.skills
reference srd-5.2.1/rules-glossary:'Challenge Rating': unknown target record glossary.challenge_rating
reference srd-5.2.1/rules-glossary:'Expertise': unknown target record glossary.expertise
```

All four are `unknown target record` because this proposal stands alone in the
test: the destination records exist in the other proposal, not in the accepted
oracle. In the merged data — accepted corpus plus both proposals — all four
resolve to exactly one existing record each, which is what
`test_proficiency_references_resolve.py` proves. The two scope keys corrected
above are a **semantic** correction and not a mechanical one, and the earlier
draft of this paragraph got that wrong. The checker resolves
`target_record_key` against the whole merged record set — `validation.py`'s
`elif ref.target_record_key not in record_keys` — so both pointers would report
resolved under either scope; repointing either one back at
`srd-5.2.1/rules-glossary` in the merged data leaves the finding list
byte-identical. What the corrected scope fixes is which review can legitimately
discharge them, and mechanically it is `(scope_key, source_text)` that the
ambiguity grouping keys on, so the scope still has to be right for a genuine
collision *in that scope* to be detectable.

**The `Actions` destination is not the one Round 1 predicted.** That row said the
durable destination would be "each action record naming its skill", with
`AbilityCheckFact.skill` filled in on the twelve accepted `action.*` records.
That is not what was done, and deliberately so. The printed sentence points at
the *Actions section of Playing the Game* — a named part of the book — not at the
Rules Glossary `[Action]` entries `actions-1` accepted, and the two are different
source material. So the destination is `play.actions`, one record over that
section, and the twelve accepted records are left untouched. Typing each action's
skill would also mean writing a skill the source does not print for that action;
it has no identified use under this task's authority, and it would rewrite
accepted content. It stays available to a later batch that has a use for it.

**Unit size, 57 versus 58.** The two counts below (Skills table "57 leaves,
container `d818241d`") are the container's leaves. The destinations batch reviews
**58**: the same 57 plus the paragraph leaf `707fa349`, which is the printed
*Skills* heading — 5c captured it as a paragraph sibling of the container rather
than opening a subsection, so a unit over the container alone would leave the
heading reviewed by nobody. That packet's §2 carries the container evidence.

**The five detectability tests are replaced by six**, over named links rather
than empty ones:
`test_all_four_printed_pointers_name_a_reviewed_destination`,
`test_exactly_two_target_strings_separate_this_from_the_reviewed_bytes`,
`test_a_named_link_survives_serialization_and_reconstruction`,
`test_deleting_either_half_of_a_named_link_is_reported`,
`test_a_sibling_citing_the_same_words_elsewhere_is_ambiguous`, and
`test_blanking_a_destination_reopens_it_as_unresolved`. The sibling row's
reported value changes with them: a resolved sibling citing "Skills table" in
this scope now reports `ambiguous … resolves to ['play.proficiency',
'play.skills']`, not `['', 'play.proficiency']`. The last test is the old
mechanism kept as a failure case: blanking a target reopens `unresolved
reference`, so a destination cannot be dropped silently.

**Nothing here is accepted.** Both proposals are proposed; the accepted oracle is
byte-identical before and after every test in this batch, and formal corpus
acceptance waits on independent review of these exact artifacts.

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

1. **Four reference findings, all `unknown target record`** (§7, Round 4): two
   forward citations into the Rules Glossary and two into *Playing the Game*.
   All four are expected of this proposal *standing alone*, all four block
   publication, and the generator asserts the set as an exact tuple. All four
   resolve in the merged data once `proficiency-destinations-1` is in it, and
   nothing in either batch is accepted.
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
   section. Both were authored with empty targets, so both failed validation
   until the real destination was named, and neither could be discharged by a
   note or by coincidence. **Closed in Round 4** under the Owner's later
   authorization: both now name `play.skills` and `play.actions`, records
   reviewed in `proficiency-destinations-1`, and the empty-target form survives
   as a failure case a test still exercises. `patched`.
8. **No post-acceptance supersede path for an accepted reference** (§7).
   `acceptance._merged_collection` can merge accepted content but cannot replace
   an element of it, so an outstanding obligation accepted today would have to be
   carried until such a path exists; pre-acceptance the route is regeneration,
   as `conditions-1` did at schema 3. Pre-existing limitation, not introduced
   here, and **`out of scope`** for this pilot. It is why this packet did not
   recommend accepting the pilot ahead of the two destinations — and why Round 4
   closes them by pre-acceptance regeneration rather than by superseding an
   accepted reference. The limitation itself is untouched.
9. **The per-kind application question is answered, and the answer is bounded**
   (§6). Owner Decision 2026-09-18 makes the Rules Package the supplier of where
   proficiency applies, its addition and scaling limits, and the tool-Advantage
   condition; ADR-005d Decision 4 carries the amendment. Schema 14 represents
   those three and stops. What the decision explicitly does **not** do is require
   structuring every reducible passage or settle any downstream sheet or adapter
   behavior — Character Sheet Model policy (#137's 2b) and adapter execution
   (15c) are untouched, and ADR-005d Decision 11 is unchanged. `patched` for the
   question; the downstream seams stay where Decision 11 leaves them.
10. **Prose does not discharge a later operation's field.** If an operation
   later needs an input this section holds only as prose — the
   class-construction constraint of `saves.class_minimum` ("at least two saving
   throws" per class), say, or the legality statement of `weapon.anyone` —
   contract 2 and ADR-005d Decision 2 require that field **before** the
   operation relies on the rule. That obligation is not claimed to be
   discharged here.
11. **The tool-Advantage trigger is partly represented, deliberately** (§6). The
   consequence is typed, and the conjunction of its two sheet-state operands is
   now explicit on the fact — `requires_proficiencies=('skill','tool')`. The
   third operand, whether the skill is *"also used with that check"*, is the
   GameMaster's relevance call and stays unrepresented: no closed applicability
   vocabulary states it, no trigger family is minted, and **no consumer is
   authorized to fire the fact**. The consequence is neither made unconditional
   nor moved to discretionary 15c handling.

12. **`AdvantageFact` is widened, and the widening is invisible to accepted
   content by construction** (§6). `requires_proficiencies` is registered
   omit-when-empty under ADR-005d Decision 6's post-schema-3 rule. All 26
   `AdvantageFact`s in the committed accepted authority still serialize as
   exactly `['family', 'roll', 'state']` and read back with an empty
   requirement; `test_schema_14_proficiency_inputs.py` asserts that over the
   committed artifact, and `test_committed_accepted_authority.py` separately
   asserts that the oracle identity survives the schema-14 lift unchanged. No
   accepted artifact is restamped. Stated as residue because "no accepted family was
   widened" was true of schema 13 and is no longer true of this proposal.

13. **The two outstanding pointers' `scope_key` was wrong and is corrected**
   (§7). Both were authored under `srd-5.2.1/rules-glossary` though both point
   into *Playing the Game*. `scope_key` is the committed resolution scope, so the
   original authoring stated that a glossary entry would close them — which would
   have let a later glossary review look like the discharge of an obligation it
   never carried. `patched`; both destinations stay empty, the two genuinely
   glossary-directed references are unchanged, and nothing is ingested.

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
| **production footprint, schema 13** | **199 insertions, 2 deletions, 3 files** | `representation.py` 128/1, `projection.py` 19/1, `schema_lift.py` 52/0. |
| **production footprint, schema 14** | **454 insertions, 4 deletions, the same 3 files** | `representation.py` 375/3, `schema_lift.py` 61/0, `projection.py` 18/1. Two families, two vocabularies, one widened field, one lift step — **and** the manifest-rendering repair diagnosed below, which is maintenance rather than mint. |
| **production footprint, schema 15** | **222 insertions, 4 deletions, the same 3 files** | `representation.py` 158/3, `schema_lift.py` 47/0, `projection.py` 17/1. One family, one two-member vocabulary, one lift step — and, again, the hand-extension of five silent per-schema tables diagnosed below. |
| **batch-specific footprint** | **1,393** generator + **555** proposal-test + **1,214** typed-input-test lines, no accept script | the generator and tests as they now stand (1,110 / 222 at `23f49d2`; the growth is §7's outstanding-obligation authoring and its five proofs, then the typed inputs and their 35 proofs, then this round's bonus uses, malformed-input refusals and override reconciliation, at 53 proofs), plus the 2,028-line `PROPOSAL.json` and this packet, which are data and prose rather than program. |
| **mint maintenance, schema 13** | **101 insertions, 41 deletions across 19 pre-existing files** | the schema-hash restamp; see the diagnosis below. |
| **mint maintenance, schema 14** | **201 insertions, 44 deletions across 13 pre-existing non-`src` files** | of which 7 files are restamp or probe-bump and 6 gained real new assertions; see the diagnosis below. |
| **mint maintenance, schema 15** | **121 insertions, 29 deletions across 12 pre-existing non-`src` files** | measured the same way — modified files under `tests/`, with this batch's own `test_schema_14_proficiency_inputs.py` (376/25) excluded as batch-specific proof rather than maintenance. The same seven restamp/probe sites recur, plus the two that failed on their own: `test_schema_12_practical_reliability.py`'s `EARLIER_CONTRACTS` and `test_schema_13_proficiency.py`'s partitioned schema-12 refusal. |

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
| Owner-review round | **1 h 38 m 55 s** (`duration_ms` 5,934,751; started 2026-09-18 03:22:33 Z from `281cf54`, `finished_utc` 05:01:33.902 Z), 241 agent turns, 4 compactions | items 1–3 of the Owner's review, ending at `7e7ed28` |
| typed-inputs round, first attempt | **stopped about three minutes in, with no final result.** `…-sep18-launch.json` records `started_utc` 05:55:43.100 Z; its stream's first event is 05:55:55.755 Z and its last is 05:58:45.370 Z; **no `…-usage.json` was ever written** and stderr is empty. | nothing. The tracked tree was clean at `7e7ed28` when it stopped, so no work was lost and none was silently carried forward. Because the usage record does not exist, **no duration, token count or cost is claimed for it** — not even a zero. |
| typed-inputs round, retry | **2 h 51 m 21 s** (`duration_ms` 10,281,179 in `…-retry1-sep18-usage.json`; `started_utc` 06:11:09.696 Z, last stream event 09:02:33.195 Z, `finished_utc` 09:02:35.058 Z), 396 agent turns, **8** compactions, 7 advisor calls, `head_before` `7e7ed28` → `head_after` `503dd3b` | Owner Decision 2026-09-18, schema 14, the scope-key correction and that round's reconciliation |
| this correction round | started 2026-09-18 09:12:34.228 Z from `503dd3b`; the `…-usage.json` is written when a run ends, so **no total is claimed for it here** | schema 15, the three corrections in this update |

Every figure in the two tables above is an **elapsed run interval** read from a
launcher or usage record. None of them is hands-on time, and none is a
subscription charge: the usage records' own `limits` field says their dollar
figure is *"a CLI estimate, not subscription credit deductions,"* and it is
reported here under that label or not at all. The retry's estimate is
`cli_estimated_usd_not_invoice` **$46.09**; the stopped attempt has none and
none is inferred for it.

The stopped attempt is recorded rather than dropped: a failed run is part of
the cost even when it produced no commit, and the honest figure for it is
*unknown*, not *zero*. No elapsed time is invented for it.

Two things follow from those numbers rather than from optimism. **Review
correction has taken more elapsed time than authoring the batch did** — the
three completed correction rounds total **5 h 55 m 59 s** (8,572,767 +
6,851,165 + 5,934,751 ms) against the 2 h 47 m 50 s pilot run, and this is a
fourth. Counting the round that produced schema 14 as well, which was
Owner-authorized authoring rather than correction, the post-pilot total reaches
**8 h 47 m 20 s**. And **most of the correction rounds' commits were
documentation**, not code: the same packet sections rewritten. That is the
maintenance evidence this pilot actually produced, and it argues against any
claim that a second section would be cheap.

**Batch-specific code: one generator.** Against the accepted batches'
generators — read as a footprint table, not a throughput result. Every other
row is that batch's generator at the commit that accepted it; proficiency-1's
is shown at both ends, because the pilot has since absorbed two Owner-authorized
mints and the growth is the point:

| batch | generator lines |
|---|---|
| hazards-1 | 562 |
| actions-1 | 734 |
| conditions-1 | 787 |
| attitudes-1 | 2,249 |
| areas-of-effect-1 | 2,796 |
| cover-1 | 3,308 |
| **speed-1** | **3,604** (+1,846 accept script, +327 reproduction test) |
| **proficiency-1**, pilot commit `23f49d2` | **1,110** (+222 proposal test, no accept script) |
| **proficiency-1**, now | **1,393** (+555 proposal test, +1,214 typed-input test, no accept script) |

**These are file sizes, and a ratio between two of them is not a throughput
result.** Speed-1 is the nearest structural neighbour — the last batch authored
before the shared workflow merged — but its 3,604 lines and this batch's 1,110
at the comparable point are over different sections with different clause counts, authored under
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

That was the whole schema-13 production footprint: a new
`ProficiencyBonusBandFact` family, its projection wiring, and one lift step.
Additive, and widening no existing family, vocabulary or field.

**Supporting engineering: schema 14, two families, two vocabularies and one
widened field.**

```
src/afterworlds/ingestion/mechanical/representation.py  | 378 +++-
src/afterworlds/ingestion/mechanical/schema_lift.py     |  61 ++
src/afterworlds/ingestion/mechanical/projection.py      |  19 +-
3 files changed, 454 insertions(+), 4 deletions(-)
```

The same three files, and roughly twice the delta for a mint that is, in schema
terms, about twice the size. Three things inside that number are worth separating
from the mint itself: the widened `AdvantageFact` field and its omit-when-empty
registration; the manifest-rendering repair diagnosed below, which is maintenance
of a pre-existing table rather than new contract; and black's reformatting of
neighbouring checker and builder code, which the gate applied to pre-existing
lines in the same file. The line count is therefore an upper bound on what the
two new families cost, not a measurement of them.

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

**Schema 14 is the third data point, and it is not smaller.** 13 pre-existing
non-`src` files, 201 insertions and 44 deletions, measured the same way. Seven of
those files are restamp or probe-bump in the narrow sense — `bounded_oracle.json`
(**not** a single hash edit: its `representation_schema` block moved to version
*and* hash 14, **and** a whole `5d-lift-schema-13-to-14` record with its six
`verified_collections` was appended to the fixture's lift chain — an added
record, not a restamp),
`test_representation_schema_identity.py`,
`test_review_round_7_draft_exact_types.py`,
`tests/services/rules_authority/test_review_round_5_component_patch_schema2.py`
(one literal each), `_schema_pins.py`'s declared pair, and the two unminted-probe
bumps. The other six gained real new assertions. So the consolidation did what it
was meant to do — the repeats moved to one place — and the **literal canaries
still cost one edit each, by design.**

**And the restamp happened twice this round**, which is the part worth reading.
The schema-14 hash was first pinned as `c0e5a4d3…` across five files, then moved
to `14284d53…` when the manifest-rendering gap below was repaired, and all five
were edited again. Nothing detected the first value as wrong, because the hash is
computed over the same manifest the rendering produces: a self-consistent wrong
answer.

### Diagnosis 1b — the mint had to hand-extend a table, and nothing noticed

This is the clearest piece of repeated-schema-maintenance evidence the pilot
produced, and it was found by review rather than by a test.

`representation.py` carries two hand-maintained per-schema tables:
`_vocabulary_shape`, which renders each declared-meaning manifest row, and
`_collect_post_schema_3`, which holds one member index per schema so
`declared_meaning_violations` can refuse a *member* an earlier contract never
admitted. Every schema from 3 onward has an entry in both. **The schema-14 mint
had to add both by hand, and the first version of it added neither.**

The consequence was silent. All seven schema-14 `vocabulary_member` manifest
rows rendered `vocabulary: null` — contradicting the manifest's own rule that a
vocabulary is identified by its complete admitted value set — and the schema hash
computed over that manifest matched its pin exactly, because the pin had been
generated from the same broken rendering. No test failed. The declared-meaning
refusals that should have fired at member level did not fire, so
`declared_meaning_violations(draft, SCHEMA_13_VERSION)` reported 8 findings where
it should have reported 19.

Repairing it cost: two table entries, a new module-level member index, one
`_vocabulary_shape` chain link, the second restamp of five files above — and
then a **second** latent gap surfaced immediately.
`test_schema_version_legality.py::test_every_manifest_row_has_an_exemplar_here`
began failing on `['add', 'divide', 'multiply']`: the `ProficiencyBonusOperation`
vocabulary group had no exemplar, and had been invisible to that check for as
long as the rows rendered null. Closing it took a new `SCHEMA_14_ONLY` exemplar
set and two directional tests, one per direction of the succession.

Neither gap was a legality hole in accepted content — no accepted artifact
declares schema 14 — but both were false statements by the code about its own
contract, and both were reachable only by reading the manifest a mint produces.
**A fourth mint should expect the same two hand-extensions, and there is still no
check that fails when a mint forgets them.** Building one is not in this pilot's
scope, and it is named here so the cost is not rediscovered a fourth time.

**The fourth mint happened, and the prediction held.** Schema 15 —
`ProficiencyBonusUseFact` and the two-member `ProficiencyBonusUse` vocabulary —
had to hand-extend exactly the same two tables, plus a third set the earlier
version of this diagnosis did not name: `projection.py` carries **four**
hand-maintained per-schema sets (`_MERGED_COMPONENT_FIELDS`,
`_RECORD_OWNED_REFERENCE_VERSIONS`, `_OPTION_SCOPED_PROSE_VERSIONS`,
`_RETENTION_REASON_PROSE_VERSIONS`), each of which a new version must be added
to or the new contract silently loses a capability its predecessor had. A sixth
table lives in the tests: `test_schema_12_practical_reliability.py`'s
`EARLIER_CONTRACTS`, which subtracts the contracts that are *not* earlier by
name, so a newly minted version is parametrized as an earlier one until it is
subtracted by hand. That one **did** fail — two tests, immediately, naming
`5d-representation-schema-15`. The other five were extended by reading the
schema-14 mint and copying its shape.

A seventh site then failed on the full suite rather than on the batch's own
module, and it is a different shape again:
`test_schema_13_proficiency.py::test_schema_12_refuses_the_reviewed_draft_for_exactly_the_eight_bands`
partitions schema 12's refusal into *the part schema 13 added* and *the
remainder*, and asserted the remainder by naming schema 14 as the only later
contract. The assertion was true when it was written and became false the moment
a second later contract existed. It is now written as the disjunction it always
meant, with the exact two-step transition asserted once in the batch's own
module rather than restated here. The count of hand-maintained per-schema sites
a mint must touch is therefore **seven**, not two; **two** of them fail when a
mint forgets, and **five** are still silent.

A counting note, so the figures are not read as more than they are. All the
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
| `test_schema_13_proficiency.py`, `data/bounded_oracle.json` | this mint's own contract, and the fixture artifact's declared schema block **plus its lift chain** | **stays fixed** — the mint's own statement, restamped deliberately. Each mint moves the fixture's declared `representation_schema` version/hash *and* appends one lift record; schema 15 did both again (`5d-lift-schema-14-to-15`, same six `verified_collections`) |

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
outside that grep by construction and stay as they are.

**Re-measured after the schema-14 mint**, over the equivalent terms
(`SCHEMA_14_HASH`, `SCHEMA_14_VERSION`, `5d-representation-schema-15`,
`5d-lift-schema-13-to-14`): **8 files**. Seven are the same categories one
schema later — `_schema_pins.py`, the fixture, the full-chain canary, the two
unminted-probe sites, and the two per-version modules that state their own
semantics — plus `test_schema_version_legality.py`, which now names schema 14
because it holds the manifest exemplars. The eighth is this mint's own module,
`test_schema_14_proficiency_inputs.py`. The consolidation held: the count did not
grow back toward 15, and the growth that did occur is one new per-version module,
which is the pattern the packet already describes as deliberate.

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

So the honest answer to "is this ready to scale?" is narrower than an earlier
revision of this section claimed. That revision said the *tooling obstacle is
gone*. **That conclusion is withdrawn; it is not supported by what was
measured.** What is supported:

* **Shared reuse is demonstrated on one section.** The merged services carried
  this batch with no new machinery: `validate_partition`, `review_unit_violations`
  and standalone `validate_representation`, plus the mutation check. No accept
  script, no reproduction implementation, no private-parser reload.
* **Cheap scaling and improved throughput are unproven.** One section is one data
  point, and nothing here measures throughput. The generator line counts in the
  table above are **file sizes**, not hours and not output rate; code footprint is
  not throughput, and a smaller generator than speed-1's is not evidence that the
  next section will be faster to author.
* **The recurring cost is visible and did not shrink.** Three mints, three
  restamps — the third of them done twice (Diagnosis 1 and 1b) — plus two
  hand-maintained per-schema tables with no check that fails when a mint forgets
  them, roughly twenty minutes of local suite and half an hour of CI per pass,
  and a correction overhead that has now exceeded the authoring interval: 4 h 17 m
  across the two completed correction rounds against the 2 h 48 m pilot run,
  before this round and its stopped attempt.
* **The remaining *authoring* obstacle is judgment** — which clauses are one
  rule, which prose retentions honestly earn their reason code, and which rule
  inputs a decision actually requires — and this pilot produced no evidence that
  judgment gets cheaper with repetition.

Final local gates on the branch head at the time the pilot was reported:
`black` and `ruff` clean over 478 files, `mypy` clean over 225 source files,
and the suite in two chunks — `tests/ingestion` **3,226 passed** in 867.97 s,
`tests --ignore=tests/ingestion` **2,775 passed, 10 skipped** in 330.03 s,
total coverage **94.39%**. `pip-audit` reports 29 pre-existing advisories
across 10 third-party packages, unchanged by this branch.

For the round that produced this revision, the full set was rerun again, because
this round also changes `src/`: `black src/ tests/` and `ruff check src/ tests/`
are clean over **481 files** with nothing to fix, and `mypy src/` succeeds over
**225 source files**. The suite ran in the usual two chunks — `tests/ingestion`
**3,347 passed** in 868.81 s, then
`tests --ignore=tests/ingestion --cov-append` **2,775 passed, 10 skipped** in
333.53 s, total coverage **94.31%**. (The first chunk's own coverage gate fails
on a partial run by design; the figure that counts is the appended total.)

**The first attempt at that run failed, and the failure is the evidence.**
`test_schema_13_proficiency.py::test_schema_12_refuses_the_reviewed_draft_for_exactly_the_eight_bands`
partitions schema 12's refusal of this draft into *the part schema 13 added* and
*the remainder*, and asserted the remainder by naming schema 14 as the only
later contract — true when it was written, false the moment schema 15 existed.
It is now written as the disjunction it always meant, with the exact two-step
transition asserted once in the batch's own module. That is the seventh
hand-maintained per-schema site counted in Diagnosis 1b, and the second of the
seven that fails when a mint forgets.

`pip-audit` reports **29 advisories across the same 10 third-party packages** —
chromadb, click, cryptography, idna, mako, msgpack, pip, pydantic-settings,
setuptools, urllib3 — all pre-existing. The count moved from 28 by one new `pip`
advisory published upstream between the two rounds; no dependency was added,
removed, upgraded or excluded by this branch. `detect-secrets` was run exactly as
`.pre-commit-config.yaml` configures it, over the staged change, and exits clean
after the two already-registered blocks
(`issue-5d-batch-proficiency-1-PROPOSAL.json`, `bounded_oracle.json`) were
rescanned additively; CI does not run that hook, so this local invocation is its
only evidence. The generator was rerun and produced byte-identical output —
61,329 bytes, sha256 `55ac577f…`, identity `c71f8104…` — which is the determinism
check, not `git diff --quiet` against a HEAD that still holds the previous
proposal. Full-suite and audit evidence for the final head is the CI run cited in
the PR description.

## 10. How to verify this packet

```bash
# regenerate the proposal (deterministic; overwrites with identical bytes)
python .claude/review-notes/issue-5d-batch-proficiency-1-generator.py

# the committed retained proposal, through the production path
pytest tests/ingestion/mechanical/test_proficiency_1_proposal.py -q --no-cov

# the band family's numeric contract and the schema-12/13 boundary
pytest tests/ingestion/mechanical/test_schema_13_proficiency.py -q --no-cov

# the typed rule inputs, the 13 -> 14 -> 15 boundary, and the override view
pytest tests/ingestion/mechanical/test_schema_14_proficiency_inputs.py -q --no-cov

# both directions of the schema-14 and schema-15 successions, and exemplars
pytest tests/ingestion/mechanical/test_schema_version_legality.py -q --no-cov

# the consolidated schema pins, against the registry and the live contract
pytest tests/ingestion/mechanical/test_schema_6_succession.py -q --no-cov

# Round 4's four destinations: identity, unit shape, the seventeen links
pytest tests/ingestion/mechanical/test_proficiency_destinations_1_proposal.py -q --no-cov

# Round 4: all four pointers resolving uniquely in the merged data, and the failures
pytest tests/ingestion/mechanical/test_proficiency_references_resolve.py -q --no-cov
```

`test_proficiency_1_proposal.py` pins the identity, runs
`review_unit_violations` on the loaded artifact, asserts **all eight bands** as
an exact set, proves by mutation that dropping the 29–30 band **is reported**,
covers §7's four named links in six tests (Round 4) — all four naming a reviewed
destination, the two target strings that reproduce PR #171's approved bytes,
survival through `accepted_inputs_payload` and `load_accepted_inputs`, omission
of either half, a sibling citing the same words elsewhere turning ambiguous, and
blanking a destination reopening it — and exercises `accept_proposal`
in memory — with `reviewer="test-evidence-only"` — asserting the committed
oracle is byte-identical before and after. That acceptance is isolated test
evidence that the proposal is structurally acceptable. **It is not a semantic
acceptance and confers none.**

`test_schema_13_proficiency.py` covers what is specific to the band family and
deliberately does not repeat what the suite already has. Generic family
behaviour — payload round-tripping for every declared family, unknown-family
refusal, persistence — stays in `test_fact_families.py` and the per-schema
modules. What is here: every printed band including the one **open below**
(`minimum=None` survives the payload as an explicit null rather than
defaulting to 1); the numeric contract, one case each for a bonus that adds
nothing, an upper bound below the first level or CR, a lower bound below it,
and a band that runs backwards; non-integer field values including `bool`,
which matters because `isinstance(True, int)` is true in Python; and the schema
boundary asserted on the committed proposal itself. That last claim is now made
as a **partition**, because the same draft has moved on to schema 14: schema 12
refuses it for exactly the eight band facts *plus* the schema-14 reasons, so the
module asserts the schema-13 share by the version each finding names, asserts
that schema 13 refuses exactly the remainder and refuses it for the later reason,
and asserts that schema 14 admits the whole draft. Nothing is dropped from the
older claim; it is stated over the share schema 13 is responsible for.

`test_schema_14_proficiency_inputs.py` is the typed-input module, **53 tests**
over the committed proposal and the production paths. It keeps its filename and
covers both mints, because they type one section and splitting them would give
the same draft two suites that have to agree. Its docstring states each new
field's required use and the consequence of omitting it, and names what is
deliberately absent: no evaluation, no character state, no adapter or sheet
behaviour, no spell formula, ability, target DC or consumer, nothing accepted.

What it proves, from schema 14: the four printed applications and the three
operation limits exactly as §5 lists them; the tool conjunction with its prose
binding retained; typed round-tripping of every new fact; seven invariant
refusals and one builder refusal per closed vocabulary — five when schema 14
landed, six now that the bonus-use closure is among them; that all 26 accepted `AdvantageFact`s still
carry the schema-3 payload; span-exact `CONTEXTUAL` provenance for every new
fact and the finding reported when a claim is stripped; persistence and
reconstruction with the projection identity preserved, and the identity moving
when the conjunction is dropped; `DISABLE` override addressing through
`apply_override_set` and the effective view; the one-step schema-13→14 crossing;
and that schema 13 refuses the draft by the field **and** by its vocabulary
members, which is what proves the member index of Diagnosis 1b is actually
wired.

And from this round, three groups that did not exist before:

* **A present malformed requirement is refused at all three ingresses.** Six
  values — `"skill"`, `false`, `0`, `""`, `{}` and an explicit `null` — each
  through `fact_from_payload`, and each again through `patch_from_payload` on a
  `REPLACE`/`FACT` target, which is the authoring surface; plus one through
  reconstruction, by rewriting the advantage's own persisted row and reading it
  back. Every one asserts `match="is not a list"`, so what fires is this
  refusal and not a later rejection of some other shape. The falsy four are the
  point: a truthiness test read each of them as *"no conjunction"* and
  canonicalized it to a payload without the key. Beside them, the
  historical-compatibility half: an **absent** key and an explicit **empty
  list** both build the same fact, with the same `fact_key`, canonicalizing back
  to the accepted three keys — so nothing already accepted has to be restamped
  and nothing genuinely empty is rejected.
* **The two bonus uses, against the sentence rather than the draft.** The
  expectation names `{spell_attack, spell_save_dc}` as a module constant, so
  dropping either or growing a third fails; the umbrella keeps `MIXED` handling
  and its prose binding; neither use is an application; `spell_damage` is
  refused at the builder as outside the closure; the family joins the
  round-trip, provenance-omission, persistence and consumer tests through the
  shared `NEW_FAMILIES` union rather than through a parallel suite.
* **The override claim, reconciled.** One supported `REPLACE` — the
  multiplication limit raised to two, an admitted shape — applied through
  `apply_override_set`, with the effective view carrying the replacement,
  attributing it to the override, and leaving the other two limits sourced. And
  one refused `REPLACE` moving `skill → attack_roll`, raising
  `OverrideApplicationError` at the real ingress, which is what substantiates
  §6's statement that re-pairing needs a schema change rather than an override.

The succession test is now the whole transition rather than one step: schema 13
refuses everything with each finding naming the schema that introduced what it
refuses, schema 14 refuses **exactly** schema 15's contribution and no part of
its own, and schema 15 admits the draft.
