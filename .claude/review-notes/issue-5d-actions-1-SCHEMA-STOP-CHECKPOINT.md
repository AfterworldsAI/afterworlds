# CRD Issue 5d — `actions-1` discovery and schema-stop checkpoint

**Return type: schema/boundary stop.** Fresh discovery against the bound CRD Issue 5c
source establishes that representation schema 5 **cannot** faithfully represent this
batch. No acceptance-ready proposal, audit, or generator has been authored, and none
should be until the corrections below are decided.

**This checkpoint accepts nothing, proposes no schema change as decided, and claims no
Owner acceptance.** Passing validators would prove admissibility, not semantic truth;
none were run against an authored payload because no payload was authored.

**Date:** 2026-09-05
**Issue:** #137 (CRD Issue 5d)
**Branch:** `feature/issue-5d-actions-1`
**Base:** `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` (verified `origin/main`, merge of #161)
**Hygiene:** `.claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md` — complete,
no unresolved risk to unique work.

### Page-number convention

The ledger's `page_index` is the **0-based PDF page index**; the SRD's printed page
number is `page_index + 1`. Verified on four independent entries against the brief's own
citations (Attack `page_index` 176 = printed p.177; Dash 179 = p.180; Influence 183 =
p.184; Friendly 181 = p.182). **Every page number in this document is a printed page
number.** No coordinate here is off by one, and the brief's cited pages agree exactly.

---

## 1. Source binding

Re-derived at run time from the committed PDF via the real CRD Issue 5c pipeline
(`build_candidate(docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf, RetrievalMemoryConfig())`) —
not a geometry approximation and not a historical source-cut payload.

| Field | Expected | Observed | Evidence class |
|---|---|---|---|
| package UUID | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` | match | independently re-derived |
| release | `5.2.1-corpus.36b786d8-fa2` | match | independently re-derived |
| source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` | match | independently re-derived |
| transform/config hash | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` | match | independently re-derived |
| bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` | match | independently re-derived |
| persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` | match (read from the committed oracle's `release_binding`) | **retained published-release evidence** |

The persisted-corpus digest is a function of persisted `rp_sources` rows and verified
Chroma state; reproducing it requires an actual publish, which discovery must not do. It
is therefore retained evidence from the published CRD Issue 5c release record, not a
value re-derived here. `build_candidate` is used as the release-bound source cut, and is
**not** persisted-state verification; nothing here republishes the source or re-proves
the CRD Issue 5c publication.

---

## 2. Frozen two-batch review prior

The committed accepted artifact was copied byte-for-byte out of the git object store
(`git cat-file blob`, so the content is the LF-normalized stored content rather than
platform bytes) to an immutable review fixture outside the production oracle directory:

`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`

| Identity | Expected | Observed |
|---|---|---|
| representation schema | `5d-representation-schema-5` | match |
| schema hash | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` | match |
| content SHA-256, LF-normalized | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` | match |
| Git blob | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` | match |
| `oracle_identity()` | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` | match |

Pinned by content digest and Git blob, not by absolute path and not by a platform-specific
raw digest. The fixture contains 0 CRLF sequences; `.gitattributes` declares
`*.json text eol=lf`, so the blob and the on-disk bytes coincide here by construction
rather than by luck.

Contents verified against the brief's prior exactly: 22 records, 281 spans, 69 components,
20 prose bindings, 0 relationships, 22 references, 281 provenance edges, 281 acceptance
records, 22 obligations. `acceptance.batches` = `conditions-1`, `hazards-1`;
`acceptance.schema_anchors` records `conditions-1` under `5d-representation-schema-3`
(proposal `14587d5b…`) and `hazards-1` under `5d-representation-schema-5` (proposal
`f7ce4491…`); `acceptance.lifts` = `5d-lift-schema-3-to-4` then `5d-lift-schema-4-to-5`.
All obligations, acceptance batches and diffs, proposal identities, schema anchors, and
lift evidence are preserved in the fixture unchanged.

The live oracle `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json`
was **read only**, as an unchanged-byte sentinel, and its blob is unchanged. No retained
artifact is coupled to its future accumulating identity.

All identities in this section are unchanged by this stage.

---

## 3. Batch boundary, derived afresh

Derived from the source's own entry class — entries under `Rules Definitions` whose label
carries the `[Action]` tag — then cross-checked against the umbrella `Action` entry's own
See-also list, exactly as the accepted `hazards-1` boundary was derived from `[Hazard]`
plus its umbrella. Structural containment supplied the candidate set; the umbrella's
printed names are what confirm membership.

The umbrella (p.176) prints, across four continuation leaves: *"Attack Dash Disengage"*,
*"Dodge Help Hide"*, *"Influence Magic Ready"*, *"Search Study Utilize"* — twelve names,
matching the twelve `[Action]` labels with no residue in either direction.

**13 records, 92 represented leaves.**

| Record | Entry label | Printed page | Represented leaves |
|---|---|---|---|
| `glossary.action` | `Action` | 176 | 8 |
| `action.attack` | `Attack [Action]` | 177 | 6 |
| `action.dash` | `Dash [Action]` | 180 | 8 |
| `action.disengage` | `Disengage [Action]` | 181 | 2 |
| `action.dodge` | `Dodge [Action]` | 181 | 2 |
| `action.help` | `Help [Action]` | 182–183 | 7 |
| `action.hide` | `Hide [Action]` | 183 | 2 |
| `action.influence` | `Influence [Action]` | 184 | 20 |
| `action.magic` | `Magic [Action]` | 185 | 5 |
| `action.ready` | `Ready [Action]` | 186–187 | 3 |
| `action.search` | `Search [Action]` | 187 | 12 |
| `action.study` | `Study [Action]` | 189 | 15 |
| `action.utilize` | `Utilize [Action]` | 191 | 2 |

(Record keys above are the shape discovery assumes; they are not authored authority.)

Two leaves inside the boundary are policy-excluded, both benign and both
`running_header_footer`: the *"System Reference Document 5.2.1 183"* footer inside
`Help [Action]` and *"System Reference Document 5.2.1 187"* inside `Ready [Action]`. No
substantive leaf is excluded.

Continuation leaves and `stat_field` fragments were inspected as content, not skipped:
Dash's rule text runs across `paragraph`/`stat_field`/`paragraph`/`stat_field`/`paragraph`
(five leaves for one sentence-run), Help's option 1 crosses a page break at pp.182–183,
and Ready's single rule crosses pp.186–187. Influence, Search, and Study each carry a
table whose cells are individual `table_cell` leaves (Influence 12 cells, Search 10,
Study 12).

### Counts against the historical August canaries

| Canary | Historical | This derivation | Status |
|---|---|---|---|
| records | 13 | **13** | reproduced |
| leaves | 92 | **92** | reproduced |
| classification spans | 149 | — | **not derived** |
| components | 19 | — | **not derived** |
| facts | 16 | — | **not derived** |
| prose bindings | 7 | — | **not derived** |
| references | 12 | — | **not derived** |
| obligations | 39 | — | **not derived** |

The two boundary-derived counts reproduce independently, from the bound source, with no
historical payload read as input — which is evidence the batch boundary is stable, not
evidence the old semantics were right. The remaining six are **historical diagnostics
only**: they predate schema 5, and deriving them would require authoring the proposal
this checkpoint stops before. They are deliberately not reproduced, not forced, and not
used as targets. The August proposal, audit, and generator
(`.claude/review-notes/issue-5d-batch-actions-1-*`, retained untracked per the hygiene
checkpoint) were **not** read as generator input and their semantic payload is not reused.

---

## 4. Per-record obligation ledger

Each row maps one source meaning to its record and printed page, the proposed claimant,
the typed shape or affirmative governing-prose classification, and the rationale.
Disposition is one of **T** (typed under schema 5), **P** (affirmatively prose-bound
under a closed irreducibility reason), **S** (supporting authority), **R** (reference), or
**✗** (unsupported — the meaning has no faithful home; family in §5).

Classification is honest in both directions: a meaning is marked **✗** where the union
lacks a field, and is **not** relabelled **P** to make the ledger clear. Where **P** is
claimed it is because the source's own content is fiction-, judgement-, or GM-dependent —
not because a typed shape was merely inconvenient.

### 4.1 `Action` (umbrella, p.176)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| A1 | *"On your turn, you can take one action."* | `action_allowance` | — | **✗ F1** | An allowance of one action per turn. `ActionEconomyFact` states what an effect *consumes*; `ActionRestrictionFact` states a slot the subject *cannot use*. Neither states a per-turn entitlement, and no other family does. |
| A2 | *"Choose which action to take from those below or from the special actions provided by your features."* | `action_choice` | prose | **P** `open_ended_effect` | The option space includes *"the special actions provided by your features"* — unbounded outside this record. Any enumeration would narrow it. |
| A3 | *"See also"* / *"'Playing the Game' ('Actions'). These actions are defined elsewhere in this glossary:"* | record | — | **S** | Identifies where the collected entries live. |
| A4 | The twelve printed names across four leaves | record-owned | `ReferenceDraft` ×12, `RECORD_OWNED_REFERENCE` | **R** | Exactly the hazard-umbrella pattern (schema 4 widened `from_component_key` for this). All twelve targets are inside this batch. |

### 4.2 `Dash` (p.180)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| D1 | *"you gain extra movement for the current turn"* — a granted movement budget | `dash_movement` | — | **✗ F1 + F2** | A grant, and one quantified from the subject's own Speed. See §5.1 and §5.2. |
| D2 | *"The increase equals your Speed after applying any modifiers."* | `dash_movement` | — | **✗ F2** | The amount is *equal to post-modifier Speed*. `MovementAmount` admits only `FEET` and `HALF_SPEED`; `ScalingBasis` has no own-Speed member; `SpeedModificationFact` changes Speed rather than granting budget. Encoding this as doubling, as a fixed number, or as a movement *cost* would each be false rather than lossy. |
| D3 | *"for the current turn"* | `dash_movement` | — | **✗ F3** | A duration. `Recurrence` states repeats; `Phase` admits only `WHILE_ACTIVE`/`ON_END`; `EffectTerminationFact` carries no trigger. Nothing states "until the end of the current turn". |
| D4 | *"With a Speed of 30 feet, for example, you can move up to 60 feet on your turn if you Dash. If your Speed of 30 feet is reduced to 15 feet, you can move up to 30 feet this turn if you Dash."* | `dash_movement` | — | **S** | Worked examples. Substantive authority is D2; the printed 60 and 30 are illustrations of it and are **not** copied into a fact. |
| D5 | *"If you have a special speed, such as a Fly Speed or Swim Speed, you can use that speed instead of your Speed when you take this action."* | `dash_speed_choice` | — | **✗ F2 + F15** | The selection ranges over *the special speeds the subject happens to have* — *"such as"* is illustrative, not an enumeration. `ComponentDraft.options` is exhaustive by definition in this version, so a four-arm `MovementMode` set would state a closed choice the source does not. Each arm would also need the missing grant fact. |
| D6 | *"You choose which speed to use each time you take it."* | `dash_speed_choice` | — | **T** (once D5 is representable) | Per-exercise re-selection is already `ComponentOption`'s stated semantics (*"mutually exclusive with its siblings per exercise; selecting one does not permanently remove the others"*). This clause is **not** itself a gap. |
| D7 | *"See also"* / *"'Speed.'"* | record-owned | `ReferenceDraft` | **R — out of cut** | Target `Speed` (p.188). See §6. |

### 4.3 `Disengage` (p.181)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| E1 | *"your movement doesn't provoke Opportunity Attacks"* | `disengage_no_provocation` | — | **✗ F5** | A negation of a *triggered reaction by another creature*. `ActionRestrictionFact(REACTION)` would state that the **subject** cannot take a Reaction, which is a different and false claim. Nothing states non-provocation. |
| E2 | *"for the rest of the current turn"* | `disengage_no_provocation` | — | **✗ F3** | Duration; same family as D3. |
| E3 | *"Opportunity Attacks"* | component-owned | `ReferenceDraft` | **R — out of cut** | Target `Opportunity Attacks` (pp.185–186). |

### 4.4 `Dodge` (p.181)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| G1 | *"any attack roll made against you has Disadvantage"* | `dodge_benefits` | `AdvantageFact(DISADVANTAGE, RollSpec(AGAINST_SUBJECT, ATTACK_ROLL))` | **T** | Actor polarity is exactly what `RollActor` exists for. |
| G2 | *"if you can see the attacker"* | `dodge_benefits` | prose, `FactQualifier` scope | **P** `contextual_applicability` | Whether the subject can see a particular attacker depends on fiction the projection cannot enumerate. Qualifies G1 alone, not G3. |
| G3 | *"you make Dexterity saving throws with Advantage"* | `dodge_benefits` | `AdvantageFact(ADVANTAGE, RollSpec(SUBJECT, SAVING_THROW, ability=DEXTERITY))` | **T** | |
| G4 | *"until the start of your next turn"* | `dodge_benefits` | — | **✗ F3** | Duration. The `Recurrence` docstring itself notes *"Dodge states an applicability and a duration at once"* — the axis is named there but no field carries it. |
| G5 | *"You lose these benefits if you have the Incapacitated condition **or** if your Speed is 0."* | `dodge_benefits` | — | **✗ F6** | Two termination triggers joined by `or`. `Applicability` has no condition-state kind, and its only disjunction (`any_of`) ranges over `SIZE_COMPARISON` alone. `TrackedQuantity.SPEED` can state the second half; nothing states the first, and nothing joins them. |
| G6 | *"the Incapacitated condition"* | component-owned | `ReferenceDraft` | **R — resolves** | Target `condition.incapacitated`, present in the accepted prior. |

### 4.5 `Help` (pp.182–183)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| H1 | *"you do one of the following"* | `help_choice` | `ComponentDraft.options` ×2 | **T** | An exhaustive actor choice, stated as such. |
| H2 | *"Choose one of your skill or tool proficiencies and one ally who is near enough for you to assist verbally or physically"* | option `assist_check` | prose | **P** `contextual_applicability` | Proficiency selection plus a proximity judgement over fiction. |
| H3 | *"That ally has Advantage on the next ability check they make with the chosen skill or tool."* | option `assist_check` | prose | **P** `contextual_applicability` — **disclosed limitation, not a gap** | Advantage on a **third party's** roll. `RollActor` is closed at `SUBJECT`/`AGAINST_SUBJECT`, and its docstring already decides this case: *"A third-party actor … is a roll directed at the subject whose actor restriction is applicability prose on a MIXED component, which is the representation this module already defines."* Following accepted precedent rather than opening a gap. The *"next"* scoping is likewise not typed. |
| H4 | *"This benefit expires if the ally doesn't use it before the start of your next turn."* | option `assist_check` | — | **✗ F3** | Duration/expiry. |
| H5 | *"The GM has final say on whether your assistance is possible."* | option `assist_check` | prose | **P** `gamemaster_latitude` | Stated delegation. |
| H6 | *"You momentarily distract an enemy within 5 feet of you, giving Advantage to the next attack roll by one of your allies against that enemy."* | option `assist_attack` | prose | **P** `contextual_applicability` — disclosed, per H3 | Same third-party-actor precedent; the 5-foot range and the *"that enemy"* coreference are likewise prose here. |
| H7 | *"This benefit expires at the start of your next turn."* | option `assist_attack` | — | **✗ F3** | Duration/expiry. |
| H8 | *"ally"*, *"enemy"*, *"Advantage"* as glossary terms | component-owned | `ReferenceDraft` | **R — out of cut, authoring decision deferred** | Targets `Ally` (pp.176–177), `Enemy` (p.181), `Advantage` (p.176). Whether an in-text glossary term is a *source-authored mechanical reference* on a par with a See-also citation is an authoring judgement that belongs to the regeneration step; the targets are listed in §6 either way. |

### 4.6 `Hide` (p.183)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| I1 | *"you must succeed on a DC 15 Dexterity (Stealth) check"* | `hide_check` | `AbilityCheckFact(DEXTERITY, FIXED, 15, skill=STEALTH, context=ABILITY_CHECK)` | **T** | Every axis is stated. |
| I2 | *"while you're Heavily Obscured **or** behind Three-Quarters Cover **or** Total Cover"* | `hide_check` | — | **✗ F6** | A three-way disjunctive prerequisite over two closed glossary vocabularies (`Heavily Obscured`, `Cover`'s three printed degrees). Marking this **P** would hide a schema gap as prose: the operands are printed, closed, and enumerable — it is the disjunction and the state predicate that are missing, not the determinacy. |
| I3 | *"and you must be out of any enemy's line of sight"* | `hide_check` | prose | **P** `contextual_applicability` | Line of sight is spatial fiction the projection cannot enumerate. Genuinely prose, unlike I2. |
| I4 | *"if you can see a creature, you can discern whether it can see you"* | `hide_awareness` | prose | **P** `contextual_applicability` | A conditional perceptual entitlement over an unenumerable referent. `SensoryCapabilityFact` states a sense grant/removal with an optional range; it cannot state a reciprocal discernment. |
| I5 | *"On a successful check, you have the Invisible condition while hidden."* | `hide_result` | `ConditionEffectFact(INVISIBLE, APPLIES)` + `Applicability(ROLL_OUTCOME, outcome=SUCCESS)` | **T** | The *"while hidden"* scoping rides I7's termination once F3/F6 exist. |
| I6 | *"Make note of your check's total, which is the DC for a creature to find you with a Wisdom (Perception) check."* | `hide_find_dc` | — | **✗ F7** | A DC sourced from a **recorded prior roll total**. `DcKind` admits `FIXED`, `SPELL_SAVE_DC`, `CONTESTED`, `GAMEMASTER_SET`. `CONTESTED` is the near miss and is false: a contest is two rolls resolved against each other at one moment; this is a value recorded now and used as a fixed DC later, by a different creature, possibly many times. |
| I7 | *"You stop being hidden immediately after any of the following occurs: you make a sound louder than a whisper, an enemy finds you, you make an attack roll, or you cast a spell with a Verbal component."* | `hide_result` | — | **✗ F6** (partly **P**) | `EffectTerminationFact(OWNING_EFFECT)` can state *that* it ends; the four-way trigger set has no home. Two arms are mechanical and enumerable (*"you make an attack roll"*, *"cast a spell with a Verbal component"*), two are fiction-dependent (*"a sound louder than a whisper"*, *"an enemy finds you"*). The set is stated as one closed disjunction and splitting it across a typed half and a prose half would state two rules where the source states one. |
| I8 | *"the Invisible condition"*, *"Heavily Obscured"*, *"Three-Quarters Cover"*, *"Total Cover"* | component-owned | `ReferenceDraft` | **R — one resolves, rest out of cut** | `condition.invisible` is present in the accepted prior; `Heavily Obscured` (p.182) and `Cover` (p.179) are not. |

### 4.7 `Influence` (p.184)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| J1 | *"you urge a monster to do something. Describe or roleplay how you're communicating with the monster. Are you trying to deceive, intimidate, amuse, or gently persuade?"* | `influence_framing` | prose | **P** `open_ended_effect` | The urging's content is unbounded. |
| J2 | *"The GM then determines whether the monster feels willing, unwilling, or hesitant due to your interaction; this determination establishes whether an ability check is necessary"* | three components' `applies_when` | prose | **P** `gamemaster_latitude` | **Not a gap.** The three branches do not need `ComponentDraft.options` — using an *actor* choice for a GM determination would misstate who decides. Three components, each `MIXED` and each binding its own branch prose as its applicability, represents this faithfully within schema 5. |
| J3 | *"Willing. If your urging aligns with the monster's desires, no ability check is necessary; the monster fulfills your request in a way it prefers."* | `influence_willing` | prose | **P** `open_ended_effect` | Outcome unbounded; *"no check is necessary"* is the absence of J6, not a fact. |
| J4 | *"Unwilling. … no ability check is necessary; it doesn't comply."* | `influence_unwilling` | prose | **P** `contextual_applicability` | |
| J5 | *"which is affected by the monster's attitude: Indifferent, Friendly, or Hostile, each of which is defined in this glossary."* | component-owned | `ReferenceDraft` ×3 | **R — out of cut** | The attitude effect is **not** globally unspecified: `Friendly` (p.182) states *"You have Advantage on an ability check to influence a Friendly creature"* and `Hostile` (p.183) states the Disadvantage; `Indifferent` (p.184) states the default attitude and no roll effect. Those facts are authority of **those records** and are **not** imported here. No numeric modifier is invented. This is a scope boundary (§6), not a representation defect. |
| J6 | *"you must make an ability check"* — the ability is GM-chosen | `influence_check` | — | **✗ F8** | `AbilityCheckFact.ability` is **required and undefaulted**. The source fixes no ability, so the fact cannot be emitted at all without inventing one. |
| J7 | *"The Influence Checks table suggests which ability check to make based on how you're interacting with the monster."* + the 5 printed rows (Charisma (Deception) / Charisma (Intimidation) / Charisma (Performance) / Charisma (Persuasion) / Wisdom (Animal Handling), each paired with an interaction) | `influence_check` | — | **✗ F9** | `AbilityCheckFact.alternatives` is *"the complete set of equally-valid rolls the source offers for this one DC"* — a **closed, mandatory** choice. These rolls are *suggested*, keyed to an interaction kind, and explicitly subordinate to *"The GM chooses the check"*. Typing them as `alternatives` would state a mandatory closed choice; marking the whole table **S** would discard the ability/skill-to-interaction mapping the source prints as its operand. |
| J8 | *"The GM chooses the check"* | `influence_check` | prose | **P** `gamemaster_latitude` | |
| J9 | *"which has a default DC equal to 15 or the monster's Intelligence score, whichever is higher"* | `influence_check` | — | **✗ F10** | A DC that is `max(15, target's Intelligence **score**)`. `DcKind.FIXED` states one number; `GAMEMASTER_SET` is false (the DC is stated, only the *check* is GM-chosen). `DerivedQuantityFact` is `base + own ability **modifier**` in a `TimeUnit` — wrong operand (score, not modifier), wrong subject (the target, not the roller), wrong unit domain, and its `floor` is a minimum on a derived value rather than a maximum of two. |
| J10 | *"On a successful check, the monster does as urged."* | `influence_check` | `Applicability(ROLL_OUTCOME, SUCCESS)` + prose | **T + P** `open_ended_effect` | The gate is typed; *"does as urged"* is unbounded. |
| J11 | *"On a failed check, you must wait 24 hours (or a duration set by the GM) before urging it in the same way again."* | `influence_retry` | — | **✗ F11** | A retry cooldown. `ResourceRecoveryFact.recovers_on` admits only `SHORT_REST`/`LONG_REST`/`DAWN`/`RECHARGE_ROLL` — no elapsed-time trigger; `ConditionRemovalRestrictionFact` is scoped to a condition this record does not apply; `Applicability(ELAPSED_DURATION)` states when a component *applies*, not that a repeat is barred until a clock runs. |

### 4.8 `Magic` (p.185)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| K1 | *"you cast a spell that has a casting time of an action or use a feature or magic item that requires a Magic action to be activated"* | `magic_cost` | `ActionEconomyFact(ACTION)` + prose | **T + P** `open_ended_effect` | The slot is typed; *"a feature or magic item"* is unbounded. |
| K2 | *"If you cast a spell that has a casting time of 1 minute or longer, you must take the Magic action on each turn of that casting"* | `magic_extended_casting` | — | **✗ F12** | A per-turn **obligation to act**, not an effect repeating at a boundary. `Recurrence(START_OF_TURN)` would be **false**, not lossy: it would state that something happens at a turn boundary rather than that the subject must spend an action each turn for the effect to continue. Decided here rather than left borderline. |
| K3 | *"and you must maintain Concentration while you do so"* | `magic_extended_casting` | prose | **P** `contextual_applicability` | A maintenance requirement; `StateEffectFact(CONCENTRATION_BROKEN)` states the broken *state*, not a requirement to sustain it. |
| K4 | *"If your Concentration is broken, the spell fails, but you don't expend a spell slot."* | `magic_concentration_loss` | — | **✗ F13** | The trigger is `StateEffectFact(CONCENTRATION_BROKEN)`'s state used as a condition (no applicability kind ranges over it — F6), and neither consequence has a family: *"the spell fails"* and the **non**-expenditure of a spell slot. `SpellSlotProgressionFact` states a progression table, not an expenditure event. |
| K5 | *"See also"* / *"'Concentration.'"* | record-owned | `ReferenceDraft` | **R — out of cut** | Target `Concentration` (p.179). |

### 4.9 `Ready` (pp.186–187)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| L1 | *"You take the Ready action … you take this action on your turn"* | `ready_cost` | `ActionEconomyFact(ACTION)` | **T** | |
| L2 | *"which lets you act by taking a Reaction before the start of your next turn"* | `ready_grant` | — | **✗ F1 + F3** | A **grant** of a Reaction slot, plus its window. Same inverse-of-consumption family as A1. |
| L3 | *"First, you decide what perceivable circumstance will trigger your Reaction."* | `ready_trigger` | prose | **P** `open_ended_effect` | The trigger space is player-authored and unbounded. |
| L4 | *"Then, you choose the action you will take in response to that trigger, **or** you choose to move up to your Speed in response to it."* | `ready_response` | `options` ×2 (arm 1 only) | **✗ F2** for arm 2 | Arm 1 is an open action choice (prose, `open_ended_effect`). Arm 2 is *"move up to your Speed"* — the same own-Speed-quantified movement allowance as Dash's D2. |
| L5 | Examples: *"If the cultist steps on the trapdoor, I'll pull the lever that opens it,"* and *"If the zombie steps next to me, I move away."* | `ready_trigger` | — | **S** | Worked examples of L3/L4. |
| L6 | *"When the trigger occurs, you can either take your Reaction right after the trigger finishes or ignore the trigger."* | `ready_resolution` | prose | **P** `contextual_applicability` | |
| L7 | *"When you Ready a spell, you cast it as normal (expending any resources used to cast it) but hold its energy, which you release with your Reaction when the trigger occurs."* | `ready_spell` | — | **✗ F13** | Spell-slot/resource expenditure again, and a held-effect state with no family. |
| L8 | *"To be readied, a spell must have a casting time of an action"* | `ready_spell` | prose | **P** `contextual_applicability` | A prerequisite over another record's declared casting time; `SpellDescriptorFact` describes a spell, it cannot state a requirement about one. |
| L9 | *"holding on to the spell's magic requires Concentration, which you can maintain up to the start of your next turn"* | `ready_spell` | — | **✗ F3** | Duration. |
| L10 | *"If your Concentration is broken, the spell dissipates without taking effect."* | `ready_spell` | `EffectTerminationFact(OWNING_EFFECT)` + **✗ F6** | **partial** | The termination is typed; its condition-state trigger is not. |
| L11 | *"a Reaction"*, *"Concentration"* | component-owned | `ReferenceDraft` | **R — out of cut** | Targets `Reaction` (p.186), `Concentration` (p.179). |

### 4.10 `Search` (p.187)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| M1 | *"you make a Wisdom check to discern something that isn't obvious"* | `search_check` | `AbilityCheckFact(WISDOM, GAMEMASTER_SET, context=ABILITY_CHECK)` | **T** | The DC is unstated and `DcKind.GAMEMASTER_SET` says exactly *where the number comes from* without inventing one. **Not a gap.** |
| M2 | *"to discern something that isn't obvious"* | `search_check` | prose | **P** `subjective_judgment` | What is "obvious" is a judgement call. |
| M3 | *"The Search table suggests which skills are applicable when you take this action, depending on what you're trying to detect."* + the 4 printed rows (Insight / Medicine / Perception / Survival, each paired with a thing to detect) | `search_check` | — | **✗ F9** | Same family as J7: a *suggested*, non-binding skill table keyed to a detection target. `AbilityCheckFact.skill` is a single stated skill; `alternatives` is a mandatory closed set. |

### 4.11 `Study` (p.189)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| N1 | *"you make an Intelligence check to study your memory, a book, a clue, or another source of knowledge and call to mind an important piece of information about it"* | `study_check` | `AbilityCheckFact(INTELLIGENCE, GAMEMASTER_SET, context=ABILITY_CHECK)` + prose | **T + P** `open_ended_effect` | Typed check; *"another source of knowledge"* and the recalled information are unbounded. |
| N2 | *"The Areas of Knowledge table suggests which skills are applicable to various areas of knowledge."* + the 5 printed rows (Arcana / History / Investigation / Nature / Religion, each with its printed area list) | `study_check` | — | **✗ F9** | Same family as J7 and M3. The area lists name creature types and knowledge domains over no closed vocabulary. |

### 4.12 `Utilize` (p.191)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| O1 | *"You normally interact with an object while doing something else, such as when you draw a sword as part of the Attack action."* | `utilize_baseline` | — | **S** | Contextual contrast that limits O2; the drawn-sword clause is an example. |
| O2 | *"When an object requires an action for its use, you take the Utilize action."* | `utilize_cost` | `ActionEconomyFact(ACTION)` + prose applicability | **T + P** `contextual_applicability` | Whether a given object *requires* an action is a property of that object, outside this record and unenumerable here. |
| O3 | *"the Attack action"* | component-owned | `ReferenceDraft` | **R — resolves in batch** | Target `action.attack`. |

### 4.13 `Attack` (p.177)

| # | Source meaning | Claimant | Shape | Disposition | Rationale |
|---|---|---|---|---|---|
| B1 | *"When you take the Attack action, you can make **one** attack roll"* | `attack_entitlement` | — | **✗ F1** | The basic attack entitlement: an allowance of one attack roll. **`AttackRollFact` requires `to_hit_bonus: int` with no default** — the family exists to record a stat block's printed *"Melee Attack Roll: +5"*, so it cannot state "you may make one attack roll" without inventing a bonus this record never prints. That is a construction-level proof of the gap, not an argument about it. |
| B2 | *"with a weapon or an Unarmed Strike"* | `attack_entitlement` | `options` ×2 | **T** (once B1 is representable) | A stated, exhaustive, two-arm actor choice of instrument. The arms carry no fact today because B1 has none. |
| B3 | *"You can either equip or unequip **one weapon** when you make an attack as part of this action."* | `attack_equip` | — | **✗ F14** | Two problems. There is no equip/unequip family at all (`EquipmentDescriptorFact` is price and weight; `WeaponPropertyFact` is a printed weapon property). And the quantity *"one weapon"* per attack is a per-attack allowance — F1 again. |
| B4 | *"You do so either before or after the attack."* | `attack_equip` | — | **✗ F15** | A **second, orthogonal** binary axis (timing) over the first (equip/unequip). `ComponentOption` *"holds no options of its own, so the structure is exactly one level deep by construction"*. Flattening to four arms would state one four-way choice where the source states two independent binary choices; leaving timing as prose would discard a stated mechanical constraint. Component order is **not** execution order and is not used as one. |
| B5 | *"If you equip a weapon before an attack, you don't need to use it for that attack."* | `attack_equip` | prose | **P** `contextual_applicability` | An explicit non-requirement, conditioned on B4's timing arm. |
| B6 | *"Equipping a weapon includes drawing it from a sheath or picking it up. Unequipping a weapon includes sheathing, stowing, or dropping it."* | `attack_equip` | — | **S** | Definitional scope for B3. |
| B7 | *"If you move on your turn and have a feature, such as Extra Attack, that gives you more than one attack as part of the Attack action, you can use some or all of that movement to move between those attacks."* | `attack_interleave` | — | **✗ F16** | A permission to **interleave** already-budgeted movement with multiple attacks. Not a movement grant (*"that movement"* is the existing budget), not a locomotion mode, not a cost. Sequencing is named as untouched in `representation.py`'s own header. No extra movement and no extra attack is invented; the prerequisite feature is out of cut. |
| B8 | *"an Unarmed Strike"*, *"Extra Attack"* | component-owned | `ReferenceDraft` | **R — out of cut / unresolvable** | `Unarmed Strike` is a Rules Definitions entry (pp.190–191). `Extra Attack` is a class feature outside Rules Definitions and has no glossary record to target at all. |

---

## 5. Representability gaps, grouped by defect family

Grouped by defect family rather than by record, so the smallest correction is answerable
once per family instead of once per clause. For each: the mechanically distinct source
meanings the current shape would collapse, the existing types considered, the smallest
proposed closed typed correction, and the sibling rules that force it.

**None of these is decided here.** Each is a proposal for a separate, reviewed schema
step. §7 states what any such step must additionally address.

### F1 — Grant/entitlement: the inverse of consumption

* **Collapses:** an *allowance* and a *consumption* become the same payload, or the
  allowance is simply unrepresented. `ActionEconomyFact(ACTION)` on Ready's grant would
  claim the Reaction **costs** an action; on `Action`'s *"you can take one action"* it
  would claim the umbrella rule consumes an action.
* **Types considered:** `ActionEconomyFact` (consumption), `ActionRestrictionFact`
  (prohibition), `ResourceRecoveryFact` (cadence of a limited resource — its
  `recovers_on` vocabulary is rest-based and its `resource_key` is a free string, so
  spelling "one action per turn" through it would both invent a trigger and open the
  free-string namespace the union forbids).
* **Smallest correction:** one closed family stating *an allowance of N of a named
  economy slot per a named boundary*, reusing `ActionCost` and `RecurrenceBoundary`
  rather than minting new vocabularies.
* **Siblings in this batch:** A1 (`Action`, one action per turn), L2 (`Ready`, a granted
  Reaction), B1 (`Attack`, one attack roll), B3 (`Attack`, one weapon equip per attack).
  Four instances in four records.
* **Classification:** issue-scoped schema work.

### F2 — Movement allowance quantified by the subject's own Speed

* **Collapses:** Dash's grant against a Speed *change*, or against a movement *cost*.
  `SpeedModificationFact(SET_TO/REDUCED_BY/HALVED)` states what a rule does to Speed —
  Dash does not change Speed. `MovementCostFact` explicitly *"states the cost, never what
  the cost buys"*, and its `MovementAmount` admits only `FEET` and `HALF_SPEED`.
  Encoding Dash as ×2 (`QuantityMultiplierFact`) is an inference, not the statement: the
  source says the increase *equals Speed after modifiers*, and the doubling only
  coincides.
* **Types considered:** `SpeedModificationFact`, `MovementCostFact`,
  `MovementPermissionFact` (mode only), `QuantityMultiplierFact` (`TrackedQuantity` has
  `SPEED` but the factor is an inference), `ScalingFact` (`ScalingBasis` has no own-Speed
  member; `ScalingEffect.SPEED` scales Speed, not a movement budget),
  `DerivedQuantityFact` (derives from an ability *modifier*, in a `TimeUnit`).
* **Smallest correction:** a movement-allowance amount whose basis is the subject's own
  Speed after modifiers, optionally naming one `MovementMode` — composed with F1's grant
  rather than duplicating it.
* **Siblings:** D1/D2/D5 (`Dash`), L4 arm 2 (`Ready`, *"move up to your Speed"*).
* **Classification:** issue-scoped schema work.

### F3 — Duration / expiry axis

The densest family in the batch, and the one most likely to recur corpus-wide.

* **Collapses:** an effect that lasts a bounded window becomes indistinguishable from one
  that is permanent. Every affected component would publish its facts as unbounded.
* **Types considered:** `Recurrence` (how often something *repeats*; its own docstring
  names Dodge as stating a duration *and* an applicability and keeps the axes separate
  precisely so neither is lost — but no field carries the duration),
  `Applicability(PHASE)` (`WHILE_ACTIVE`/`ON_END` — relative position within an effect's
  life, not an extent), `EffectTerminationFact` (states *that* an effect stops and
  deliberately carries **no** trigger), `Applicability(ELAPSED_DURATION)` (a condition on
  whether a component applies, keyed to a count that has already elapsed).
* **Smallest correction:** a component-level duration expressed over the existing
  `RecurrenceBoundary` + `RollActor` pair — *"until the start of your next turn"* is
  exactly `(START_OF_TURN, SUBJECT)` — reusing the vocabularies `Recurrence` already
  declares rather than adding a second spelling of a turn boundary.
* **Siblings:** D3 (`Dash`), E2 (`Disengage`), G4 (`Dodge`), H4 and H7 (`Help`, both
  options), L2 and L9 (`Ready`). Seven instances in five records.
* **Classification:** issue-scoped schema work.

### F6 — Applicability: state predicates and disjunction

* **Collapses:** a two- or four-way alternative prerequisite becomes one arm of itself, or
  is dropped entirely. Dodge's *"Incapacitated **or** Speed 0"* would state only the
  Speed half; Hide's cover prerequisite would state one of three.
* **Types considered:** `Applicability.any_of` — disjunction **exists**, but ranges over
  `SIZE_COMPARISON` alone; `ApplicabilityKind` has no member for "the subject has
  condition X"; `negated` negates a whole predicate and *"there are no sub-terms to
  negate"*.
* **Smallest correction, deliberately narrow:** (a) one applicability kind over the
  already-closed `ConditionKind` vocabulary; and (b) generalize `any_of` to a
  **homogeneous** set within a single kind, exactly mirroring the existing
  `SIZE_COMPARISON` precedent. **Not** a Boolean expression language — no nesting, no
  operators, no mixing of kinds. This distinction is load-bearing: the module already
  refused a predicate language after the targeting-restrictions sweep, and any correction
  that reopened that is the wrong one.
* **Siblings:** G5 (`Dodge`), I2 and I7 (`Hide`), K4 and L10 (`Magic`, `Ready` — the
  Concentration-broken trigger).
* **Classification:** issue-scoped schema work, **with a standing risk** that the honest
  answer for some arms remains prose. The sweep that justified the existing refusal must
  be re-run before this is admitted, not assumed superseded.

### F9 — Suggested (non-binding) roll tables keyed to an interaction or target

* **Collapses:** a *suggestion* becomes a *mandate*. `AbilityCheckFact.alternatives` is
  documented as *"the complete set of equally-valid rolls the source offers for this one
  DC"* — a closed, mandatory choice sharing one DC. Influence's table is explicitly
  subordinate to *"The GM chooses the check"*; Search's and Study's say *"suggests which
  skills are applicable"*. Typing them as `alternatives` states a rule the source does not.
  Classifying the tables as supporting authority discards the skill-to-interaction mapping
  the source prints as the rule's operand.
* **Types considered:** `AbilityCheckFact.alternatives`, `AbilityCheckFact.skill` (one
  stated skill), `SizeKeyedQuantityFact` (the structural analogue — a printed table as the
  rule's operand — but keyed to `CreatureSize` and yielding a quantity, not a roll).
* **Smallest correction:** a suggested-roll table whose rows pair one `RollSpec` with one
  closed *interaction/target* key, marked non-binding. The blocker is that the row keys
  (*"Deceiving a monster that understands you"*, *"Creature's state of mind"*,
  *"Traps, ciphers, riddles, and gadgetry"*) range over no closed vocabulary — this may
  reduce to a typed roll set plus a prose-bound key, or may not be admissible at all.
* **Siblings:** J7 (`Influence`, 5 rows), M3 (`Search`, 4 rows), N2 (`Study`, 5 rows).
  Three instances in three records.
* **Classification:** issue-scoped schema work **whose shape is not yet determined**;
  the row-key vocabulary question is the open part.

### Singletons — no sibling in this batch

Each is stated with its own classification, because the brief requires the distinction and
because a family should not be minted for one clause.

| ID | Meaning | Records | Classification |
|---|---|---|---|
| **F5** | *"your movement doesn't provoke Opportunity Attacks"* — non-provocation of another creature's triggered reaction | `Disengage` (E1) | **Issue-scoped schema work.** A corpus-wide sweep for provocation/non-provocation siblings (Opportunity Attacks and other trigger waivers) must precede any family admission — one clause does not justify a family. |
| **F7** | *"your check's total … is the DC"* — a DC sourced from a recorded prior roll total | `Hide` (I6) | **Issue-scoped schema work**, pending the same sweep. `DcKind.CONTESTED` is the near miss and is false: a contest resolves two rolls against each other at one moment; this records a value now and reuses it as a fixed DC later, by a different creature. |
| **F8** | `AbilityCheckFact.ability` is required, but the source fixes no ability | `Influence` (J6) | **Issue-scoped schema work.** Interacts directly with F9 — if the suggested table is representable, the ability may be recoverable from the selected row rather than from a new optional field. Decide F9 first. |
| **F10** | DC = `max(15, the target's Intelligence score)` | `Influence` (J9) | **`[OWNER DECISION]:` residue.** Not a missing field but a missing *notion*: a DC computed from **another creature's** ability **score**. `ParticipantRole.COUNTERPART` is admissible only where a closed structure in the same component establishes the counterpart (`MovementTransportFact` and nothing else, enforced by `component_participant_violations`). Admitting a cross-creature statistic reference into a DC touches that restriction and the ADR-005d Decision 4 generic-actor boundary. Not an ordinary implementation detail. |
| **F11** | *"you must wait 24 hours … before urging it in the same way again"* | `Influence` (J11) | **Issue-scoped schema work.** A retry cooldown on an elapsed clock. `RecoveryTrigger` has no elapsed-time member and `ConditionRemovalRestrictionFact` is condition-scoped. *"in the same way"* may itself be irreducible. |
| **F12** | *"you must take the Magic action on each turn of that casting"* — a per-turn obligation to act | `Magic` (K2) | **Issue-scoped schema work.** Decided, not left borderline: `Recurrence(START_OF_TURN)` is **false** here, because it would state that an effect fires at a turn boundary rather than that the subject must spend an action each turn for the effect to continue. |
| **F13** | Spell-slot / resource expenditure and **non**-expenditure as an event | `Magic` (K4), `Ready` (L7) | **Known Unknown — do not decide in code.** ADR-015b's typed parameter contract for spell-slot upcasting and variable-resource recovery is the recorded Known Unknown named in `representation.py`'s own header. Expenditure semantics sit against that boundary. Flagged, not resolved. |
| **F14** | Equipping / unequipping a weapon | `Attack` (B3) | **Issue-scoped schema work**, but see F15 — the two are one clause and should be decided together. `EquipmentDescriptorFact` is price and weight; `WeaponPropertyFact` is a printed property. Neither is an equip event. |
| **F15** | The component **option model** itself: (a) two orthogonal binary choice axes over one clause — equip/unequip × before/after; (b) an option set that ranges over *what the subject happens to possess* rather than a source-enumerated closed set | `Attack` (B4), `Dash` (D5) | **Scope boundary.** `ComponentDraft.options` is one level deep *by construction*, and its exhaustiveness is a declared schema-version property (*"exhaustive by definition in this schema version"*, evidenced by Prone's *"your only movement options are"*). (a) needs a second axis or nesting; (b) needs a non-exhaustive or open-domain option set — Dash's *"such as a Fly Speed or Swim Speed"* is illustrative, so a four-arm `MovementMode` set would state a closed choice the source does not. Both change the component model rather than the fact union, which is a materially different structure to be reconciled at ADR level rather than patched in. Grouped as one entry because the cause is one: the option model's declared shape. |
| **F16** | Interleaving movement between multiple attacks | `Attack` (B7) | **Scope leak — out of scope for `actions-1`.** The permission is conditional on possessing a class feature (*"such as Extra Attack"*) that has no Rules Definitions record and lies outside this batch and outside Rules Definitions entirely. Sequencing is listed as untouched in `representation.py`'s header. Representing it here would require importing authority this batch never accounted. Not fixed, not silently dropped: disclosed. |

### Explicitly *not* gaps

Recorded so review does not re-litigate them, and so the ledger is not padded:

* **Third-party-actor advantage** (H3, H6, `Help`) — `RollActor`'s docstring already
  decides this: prose applicability on a `MIXED` component. **Already safe**, disclosed as
  a limitation.
* **Influence's willing/unwilling/hesitant branches** (J2) — representable as three
  components with prose applicability. `ComponentDraft.options` is an *actor* choice and
  would misstate who decides; not needing it is the correct outcome, not a gap.
* **Search and Study DCs** (M1, N1) — `DcKind.GAMEMASTER_SET` states where the number
  comes from without inventing one. Exactly the case it exists for.
* **Dash's per-use re-selection** (D6) — `ComponentOption`'s declared per-exercise
  semantics already say this. The gap in D5 is the option *set*, not the re-selection.
* **`condition.invisible`** (I5) and **`condition.incapacitated`** (G6) — cross-batch
  reference targets that **resolve** against the accepted prior.

---

## 6. Scope boundary: cross-batch reference targets

Stated separately from representation defects, per the brief. These are records the
batch's own text cites that lie **outside** the `actions-1` cut. They are a disclosed
scope boundary, not a defect, and **not** permission to add authority silently: no
attitude record, no `Speed` record, and no `Concentration` record is imported,
regenerated, or invented here.

The set is exactly the following, and is complete for this batch:

| Source record | Cited target | Target's printed page | Where the citation appears |
|---|---|---|---|
| `action.dash` | `Speed` | 188 | See-also (D7) |
| `action.disengage` | `Opportunity Attacks` | 185–186 | in-text (E3) |
| `action.help` | `Ally` | 176–177 | in-text (H8) |
| `action.help` | `Enemy` | 181 | in-text (H8) |
| `action.help` | `Advantage` | 176 | in-text (H8) |
| `action.hide` | `Heavily Obscured` | 182 | in-text (I8) |
| `action.hide` | `Cover` | 179 | in-text (I8, three degrees) |
| `action.influence` | `Indifferent [Attitude]` | 184 | in-text, explicit (J5) |
| `action.influence` | `Friendly [Attitude]` | 182 | in-text, explicit (J5) |
| `action.influence` | `Hostile [Attitude]` | 183 | in-text, explicit (J5) |
| `action.magic` | `Concentration` | 179 | See-also (K5) |
| `action.ready` | `Reaction` | 186 | in-text (L11) |
| `action.ready` | `Concentration` | 179 | in-text (L11) |
| `action.attack` | `Unarmed Strike` | 190–191 | in-text (B8) |
| `action.attack` | *Extra Attack* | — | in-text (B8) — **no Rules Definitions record exists**; a class feature outside this section entirely |

Targets that **resolve** against the frozen accepted prior, and are therefore not missing:
`condition.invisible` (from `action.hide`), `condition.incapacitated` (from
`action.dodge`).

Targets inside `actions-1` itself: the umbrella's twelve named actions, and
`action.utilize` → `action.attack`.

**Consequences.** Standalone validation of an eventual `actions-1` proposal must assert
*exactly* this missing-target set by source and target, rather than demanding a
misleading zero or allowing a broad exception. Combined validation beside the frozen
prior must reduce it by the two that resolve, and any remaining missing target is a
disclosed blocker — never a licence to add authority. The `Extra Attack` row is different
in kind from the rest: it has no candidate target anywhere in Rules Definitions, so it is
a scope question about what a mechanical reference may cite, not a batch-ordering question.

Whether an in-text glossary term (`Ally`, `Enemy`, `Advantage`, `Reaction`, `Cover`) is a
*source-authored mechanical reference* on a par with an explicit See-also citation is an
authoring judgement. It is listed here so the boundary is disclosed either way, and is
deferred to the regeneration step rather than decided in this checkpoint.

---

## 7. What any later schema step must separately address

Recorded now so that remediation does not become another sequence of one-clause schema
changes, and so the bounded sibling map is complete **before** patches are recommended.

1. **Version and hash succession.** The existing chain is `3 → 4 → 5` with
   `5d-lift-schema-3-to-4` and `5d-lift-schema-4-to-5`. A schema 6 needs its own lift,
   its own verified-collection set, and its own recorded from/to hashes.
2. **Old-declaration legality.** `conditions-1` was reviewed under schema 3 and
   `hazards-1` under schema 5. Both anchors must stay legal and byte-identical; neither
   review anchor may be relabelled.
3. **Wire identity.** Declared-schema round trips and semantic identity checks for every
   changed shape, including the post-schema-3 omit-when-unset rule that keeps inherited
   components byte-identical.
4. **Persistence and overrides** where a changed shape reaches them.
5. **Unchanged accepted evidence.** All 22 records, 281 spans, 69 components, 20 prose
   bindings, 22 references, 281 provenance edges, 281 acceptance records, 22 obligations,
   all acceptance batches and diffs, all proposal identities, all schema anchors and all
   lift evidence must survive unchanged, unmoved, unreordered, and uncoalesced.
6. **F6's predicate boundary specifically.** The corpus sweep that justified refusing a
   predicate language for targeting restrictions must be re-run against condition-state
   and disjunctive prerequisites before either is admitted. If the sweep says the same
   thing it said before, the honest answer stays prose for some arms.

---

## 8. Gates and evidence

No new source code, and therefore no new gate surface. Nothing was authored that
`black`, `ruff`, or `mypy` can measure. Full gate evidence belongs to the remediation
step that actually changes code.

One check was run because this branch adds a file under `tests/`: the mechanical suite,
to confirm the new fixture is inert and collides with nothing.

```
venv/Scripts/python -m pytest tests/ingestion/mechanical -q
-> 1935 passed in 287.48s
```

The run also printed `FAIL Required test coverage of 80% not reached. Total coverage:
45.56%`. That is an artifact of running **a subset** of the suite while `--cov` is
configured repository-wide, not a coverage regression: this branch adds no measurable
source lines. Reported rather than suppressed. The full suite was not run, and no
unrun check is presented as passed.

**Toolchain verified runnable** (Python 3.12.10 in `venv`): black 26.3.1, ruff 0.15.8,
mypy 1.19.1, pytest 9.0.3, pip-audit 2.10.0, detect-secrets 1.5.0. Recorded in the hygiene
checkpoint with the environment checks.

**detect-secrets.** The deterministic baseline was established at the start of the session,
**before any artifact of this work existed**, so new findings are separable from
pre-existing ones. This branch then adds exactly one path-scoped entry to it.

| | Blob | Content SHA-256 (LF) | Files | Findings |
|---|---|---|---|---|
| As established at session start (= baseline commit `b5d386ba…`) | `474ed2f15e2508d9cc31a0a4ead1b9afcf5f2cca` | `c95a0cb6555ad95c8ef8f0e7b27db060d65959600f67b2119ff83c98f15b9b9a` | 4 | 129 |
| At this branch head | `99de7d2e38f8ddfc5d7b68469e57790ed3a4cc6d` | `2cccfb4c0caf31629339d3b5986c648896649be6ca66cf75b2ba736ff4ff01d2` | 5 | 189 |

The hygiene checkpoint records the baseline as unmodified; that was accurate at hygiene
time and is superseded by the single addition below, not contradicted by it.

Three files are new on this branch, plus the baseline itself; each was scanned
individually against it:

| File | Result |
|---|---|
| `tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json` | 60 findings, all `Hex High Entropy String`. Individually inspected: the file is byte-for-byte identical to the committed oracle (verified), and its 60 findings are the **same 60 hashed secrets at the same line numbers** the baseline already carries for the oracle's own path — content hashes, span/proposal identities and UUIDs of the accepted authority. None is a credential. Treated as justified false positives by adding a **path-scoped** entry for this one file, copied from the audited oracle entry; the existing four entries are untouched (`git diff` on the baseline is 422 insertions, **0 deletions**). |
| `.claude/review-notes/issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md` (this file) | **No findings.** The hash literals it quotes are reproduced verbatim from the committed oracle and the brief. |
| `.claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md` | **No findings.** |

Scanning was not disabled, no generated artifact was broadly excluded, and no `pragma:
allowlist secret` was added. Gate result over exactly the staged files:

```
detect-secrets-hook --baseline .secrets.baseline \
  .claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md \
  .claude/review-notes/issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md \
  .secrets.baseline \
  tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json
-> exit 0

(paths shown with forward slashes; the actual invocation uses the platform
separators git reports, which is what the baseline's keys are stored with)
```

**Measurement scope.** The three scopes the brief requires kept apart:

| Scope | Comparison | Value |
|---|---|---|
| **Whole-PR** | `git diff --shortstat b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d...HEAD` | 4 files changed, **+12,959 / -0** |
| **Individual commit** — first | hygiene checkpoint, frozen prior fixture, baseline entry, this checkpoint | 4 files, +12,930 / -0 |
| **Individual commit** — second | corrections to this checkpoint's own summary accounting; no discovery finding changed | 1 file, +43 / -14 |
| **Runtime** | one `pytest tests/ingestion/mechanical -q` invocation | 287.48 s |

The whole-PR insertion count is dominated by the 11,514-line frozen prior fixture, which
is a byte-for-byte copy of already-accepted authority, not authored content; the two
checkpoints are 335 and ~700 lines, and the baseline addition 422.

Commits are named by role rather than by SHA, deliberately: a document that cites the
commit containing it can never be correct after the commit that fixes it. The comparison
command is given so every figure above is re-derivable rather than trusted.

Every **discovery** count in this document (13 records, 92 leaves, the per-record leaf
counts, the gap IDs) describes the batch boundary derived from the bound source at this
branch head. Those are source measurements, not diff measurements, and are not comparable
to the table above.

**Determinism.** The boundary derivation is a pure function of the committed PDF and the
committed pipeline; it was executed from a script whose repository root is derived from
its own location and which asserts the five independently derivable binding values before
reading anything. It produced identical results across runs. The discovery script itself
lives in the session scratchpad and is deliberately **not** a repository artifact: it is
not a generator, and §5's `issue-5d-actions-1-schema5-REGEN-` naming is reserved for the
regeneration path this checkpoint does not take.

---

## 9. Architecture Notes

**Drift from design principles: none in what was built.** No accepted authority was
altered, no acceptance was recorded, no proposal was authored, nothing was published,
activated, retired, or merged, and #137 remains open. `accept_proposal` was not called.
Invariant 12 (surface scope creep and Known Unknowns rather than resolving them silently)
is the reason this is a stop rather than a proposal.

**The boundary this stop surfaces** is that schema 5 is insufficient for `actions-1`
across **fifteen distinct gap IDs** (F1–F3, F5–F16; there is no F4) touching **twelve of
thirteen** records — every record except `Utilize` — grouped into five recurring defect
families and ten singletons. Counted as IDs rather than as clauses on purpose: several IDs
cover more than one ledger row (F3 alone covers seven), so a clause count would be a
different, larger number. Two of those are not ordinary
implementation work and are named as such: **F13** touches the recorded ADR-015b Known
Unknown; **F10** touches the `ParticipantRole.COUNTERPART` restriction and the ADR-005d
Decision 4 generic-actor boundary, and is marked `[OWNER DECISION]:` residue. **F15**
would change the component model rather than the fact union, and **F16** is a scope leak
into class-feature authority outside Rules Definitions. None of the four is decided here.

**Deferred risk.** The batch cannot be represented until at least F1, F2, F3, F6, F9 and
the singletons blocking a record's substantive meaning are resolved. F9's shape is
genuinely undetermined — its row keys range over no closed vocabulary — and it may not be
admissible in the form sketched. F6 carries the standing risk that re-running the
targeting-restrictions sweep reaffirms the existing refusal for some arms.

---

## 10. Why regeneration has not begun

Explicitly, per §4 of the brief:

1. **The schema gate is not clear.** Fifteen distinct gap IDs, touching twelve of the
   thirteen records, have no faithful home under schema 5. All three of the brief's named pressure
   points fail — Dash on F1/F2/F3, Influence on F8/F9/F10/F11 plus the attitude scope
   boundary, Attack on F1/F14/F15/F16 with `AttackRollFact.to_hit_bonus` proving the
   entitlement gap by construction.
2. **Governing boundaries remain unresolved.** One `[OWNER DECISION]:` residue (F10), one
   Known Unknown (F13), one component-model scope boundary (F15), and one scope leak
   (F16).
3. **Authoring a proposal now would require choosing** between stating claims the source
   does not make (a doubled Speed, an invented attack bonus, a mandatory suggested check,
   a GM-set DC where one is stated) and classifying substantive mechanics as prose-bound
   to make a validator pass. Both are exactly what the emission rule forbids, and a
   passing validator would prove admissibility rather than fidelity.
4. **Schema 5 was not silently widened**, no `issue-5d-actions-1-schema5-REGEN-` artifact
   was created, and the bounded sibling map in §5 is complete so that remediation can be
   scoped once rather than as a sequence of one-clause changes.

Stop here for Codex's inspection and an independent semantic review. Completing
`actions-1` would complete this batch worklist, not by itself the full-corpus or
activation obligations of CRD Issue 5d.
