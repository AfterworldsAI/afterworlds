# CRD Issue 5d — `actions-1` discovery and schema-stop checkpoint

**Revision 2**, correcting Revision 1's authority classification, representation analysis,
and evidence completeness. Revision 1's conclusion — a schema stop — is unchanged and is
restated here on a stronger basis. Where this revision **rejects** a Revision 1 conclusion
it says so and cites the source or contract evidence that overturns it (§10).

**Return type: schema/boundary stop.** No acceptance-ready proposal, audit, or generator
has been authored. This checkpoint accepts nothing, decides no schema change, and claims
no Owner acceptance.

**Date:** 2026-09-05
**Issue:** #137 (CRD Issue 5d)
**Branch:** `feature/issue-5d-actions-1`
**Base:** `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` (verified `origin/main`, merge of #161)
**Hygiene:** `.claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md`

### Preserved from Revision 1, independently verified by Codex

The synchronized baseline, the frozen two-batch prior, the source binding, and the
13-record / 92-leaf boundary are unchanged and are restated in §1–§3 without alteration.
Nothing in this revision moves an identity, a count, or a boundary.

### Why the stop, in one line

**31 of 75 obligations, across 10 of the 13 records, must be classified `UNRESOLVED`** —
substantive source meaning with no typed home *and* no member of the closed irreducibility
catalog that is affirmatively true of it. `SemanticDisposition.UNRESOLVED` is documented as
*"an honest 'cannot classify safely yet'"* that **blocks publication**. The batch therefore
cannot yield an admissible proposal at all, whatever fidelity one were willing to trade.

### Page-number convention

The ledger's `page_index` is the **0-based PDF page index**; the printed page is
`page_index + 1`. Verified on four entries against the brief's citations (Attack 176 =
p.177; Dash 179 = p.180; Influence 183 = p.184; Friendly 181 = p.182). Every page number
below is a printed page number.

### Machine-checked evidence

Every coordinate, disposition, and count in this document is produced by
`.claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py` and recorded in
`.claude/review-notes/issue-5d-actions-1-obligation-coordinates.json`. The script derives
the repository root from its own location, asserts the source binding before reading
anything, resolves each quoted phrase against the leaf it claims (failing if absent or
ambiguous), refuses overlapping claims, and computes every tally from the disposition
table rather than from prose. It emits no proposal, no audit, and no representation.

```
venv/Scripts/python .claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py
-> records=13 leaves=92
   dispositions={'P': 21, 'R': 4, 'S': 8, 'T': 7, 'TP': 4, 'X': 31} unresolved=31 in 10 records
   blocking families=17
   interior gap characters still unassigned=74
   obligations=75 rows=132 leaves_with_an_obligation=79
```

---

## 1. Source binding

Re-derived at run time from the committed PDF through the real CRD Issue 5c pipeline
(`build_candidate`), not a geometry approximation and not a historical source-cut payload.

| Field | Expected | Observed | Evidence class |
|---|---|---|---|
| package UUID | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` | match | independently re-derived |
| release | `5.2.1-corpus.36b786d8-fa2` | match | independently re-derived |
| source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` | match | independently re-derived |
| transform/config hash | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` | match | independently re-derived |
| bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` | match | independently re-derived |
| persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` | match, read from the committed oracle | **retained published-release evidence** |

The persisted-corpus digest is a function of persisted `rp_sources` rows and verified
Chroma state; reproducing it requires a publish, which discovery must not do. It is
retained evidence, not a value re-derived here. `build_candidate` is the release-bound
source cut and is **not** persisted-state verification; nothing here republishes the
source or re-proves the CRD Issue 5c publication.

---

## 2. Frozen two-batch review prior

`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`, copied
byte-for-byte from the git object store (`git cat-file blob`, so LF-normalized stored
content rather than platform bytes).

| Identity | Expected | Observed |
|---|---|---|
| representation schema | `5d-representation-schema-5` | match |
| schema hash | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` | match |
| content SHA-256, LF-normalized | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` | match |
| Git blob | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` | match |
| `oracle_identity()` | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` | match |

Pinned by content digest and Git blob, not by absolute path or platform digest. Contents
verified exactly: 22 records, 281 spans, 69 components, 20 prose bindings, 0 relationships,
22 references, 281 provenance edges, 281 acceptance records, 22 obligations; batches
`conditions-1` / `hazards-1`; anchors at schema 3 (proposal `14587d5b…`) and schema 5
(proposal `f7ce4491…`); lifts `5d-lift-schema-3-to-4` then `5d-lift-schema-4-to-5`. The
live oracle was read only as an unchanged-byte sentinel and its blob is unchanged.

---

## 3. Batch boundary

Derived from the `[Action]` entry class under `Rules Definitions`, cross-checked against
the umbrella `Action` entry's own list — *"These actions are defined elsewhere in this
glossary:"* followed by twelve names across four leaves. Twelve names, twelve labels, no
residue in either direction.

**13 records, 92 represented leaves.** Two leaves inside the boundary are policy-excluded,
both `running_header_footer` (the p.184 footer in `Help`, the p.188 footer in `Ready`).
No substantive leaf is excluded.

| Record | Entry label | Printed page | Leaves | Obligations | of which `UNRESOLVED` |
|---|---|---|---|---|---|
| `glossary.action` | `Action` | 176 | 8 | 4 | 1 |
| `action.attack` | `Attack [Action]` | 177 | 6 | 7 | 4 |
| `action.dash` | `Dash [Action]` | 180 | 8 | 7 | 4 |
| `action.disengage` | `Disengage [Action]` | 181 | 2 | 3 | 2 |
| `action.dodge` | `Dodge [Action]` | 181 | 2 | 6 | 2 |
| `action.help` | `Help [Action]` | 182–183 | 7 | 7 | 6 |
| `action.hide` | `Hide [Action]` | 183 | 2 | 8 | 2 |
| `action.influence` | `Influence [Action]` | 184 | 20 | 11 | 3 |
| `action.magic` | `Magic [Action]` | 185 | 5 | 5 | 2 |
| `action.ready` | `Ready [Action]` | 186–187 | 3 | 10 | 5 |
| `action.search` | `Search [Action]` | 187 | 12 | 3 | 0 |
| `action.study` | `Study [Action]` | 189 | 15 | 2 | 0 |
| `action.utilize` | `Utilize [Action]` | 191 | 2 | 2 | 0 |
| | | | **92** | **75** | **31** |

Record keys are the shape discovery assumes; they are not authored authority.

### Leaf coverage

79 of the 92 leaves carry at least one obligation row. The remaining 13 are each record's
own **heading leaf**, accounted as record-owned supporting authority — the
`W = [(None, "R", None)]` shape the accepted `hazards-1` generator uses for exactly this —
and excluded from the obligation table by design, not by omission.

The 132 resolved spans are non-overlapping (checked, not assumed) and leave **74
characters** unassigned inside leaves, all of them inter-sentence separators between
consecutive claims. Those 74 are enumerated in the JSON so the exact per-leaf partition an
eventual proposal owes is checkable now rather than discovered later.

### Counts against the historical August canaries

| Canary | Historical | This derivation | Status |
|---|---|---|---|
| records | 13 | **13** | reproduced |
| leaves | 92 | **92** | reproduced |
| classification spans | 149 | — | not derived |
| components | 19 | — | not derived |
| facts | 16 | — | not derived |
| prose bindings | 7 | — | not derived |
| references | 12 | — | not derived |
| obligations | 39 | 75 (this ledger) | **not comparable** |

The two boundary counts reproduce independently from the bound source with no historical
payload read as input. The rest are **historical diagnostics**: they predate schema 5, and
deriving them is proposal work this checkpoint stops before. The obligation figure is
deliberately *not* reconciled against 39 — this ledger partitions leaf text at clause
grain, which the August artifact did not, so the two count different things. The August
proposal, audit, and generator (retained untracked, per the hygiene checkpoint) were not
read as generator input.

---

## 4. The classification test

Revision 1 applied the prose-bound catalog inconsistently. The test is stated once here
and applied uniformly, because it is what separates a genuine schema gap from an
enrichment:

> A component is honestly `PROSE_BOUND` or `MIXED` when a closed irreducibility reason is
> **affirmatively true of what the source says** — not when the union merely lacks a field.
> Operationally: if the claim is determinate and all of its operands are printed, closed
> vocabulary, then no catalog reason describes it, and a prose-bound classification would
> be hiding a schema gap. If what resists typing is *whether the rule applies* — fiction,
> an unbounded feature space, a GM judgement — the catalog reason is true and the
> classification is honest.

The decisive corollary, and the one Revision 1 got wrong in both directions:

> **The catalog reasons range over applicability, not over consequence.**
> `contextual_applicability` says *"Whether the rule applies depends on fiction the
> projection cannot enumerate."* A rule whose *condition* is unenumerable is prose-bound.
> A rule that applies determinately but whose *consequence* the union cannot express is
> **not** — no catalog member describes an inexpressible consequence, so its span is
> `UNRESOLVED`.

Worked both ways, on the two cases Revision 1 decided inconsistently:

* **B7, Attack's interleaving** — *"If you move on your turn **and have a feature, such as
  Extra Attack**, that gives you more than one attack … you can use some or all of that
  movement to move between those attacks."* The unenumerable element is the **gating
  feature**, i.e. the applicability. The consequence spends an *existing* movement budget
  and introduces no quantity. `contextual_applicability` is affirmatively true. This is the
  same shape the accepted `hazards-1` batch used for Burning's rolling clause — *"bound as
  affirmative governing prose under `contextual_applicability` because whether the
  extinguishing applies depends on an act the projection cannot enumerate."* → **P**, and
  in scope. The counter-reading is recorded in §10.4.
* **H3, Help's assist** — *"That ally has Advantage on the next ability check they make
  with the chosen skill or tool."* The rule applies whenever the actor takes the Help
  action and names an ally; nothing about its **applicability** is unenumerable. What the
  union cannot express is the **consequence**: a benefit on a roll `RollSpec` cannot
  identify. No catalog reason is true of that. → **X**.

---

## 5. Per-record obligation ledger

Disposition: **T** typed under schema 5 · **P** affirmatively prose-bound under a closed
reason · **S** supporting authority · **R** source-authored reference · **X**
`UNRESOLVED`, blocking.

Coordinates are `leafid[start:end]` against the bound release, leaf ids abbreviated to
eight hex characters; the full ids, the sliced source text, and the printed page are in
the coordinates JSON. Where an obligation spans several leaves, all of its spans are given.

### 5.1 `Action` — umbrella, p.176

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| A1 | *"On your turn, you can take one action."* | `1ab39be0[0:38]` | **X** | F1 | An allowance of one action per turn. `ActionEconomyFact` states what an effect *consumes*; `ActionRestrictionFact` states a slot the subject *cannot use*. The claim is fully determinate over the closed `ActionCost` vocabulary, so no catalog reason is true of it. **The cleanest instance of the stop:** substantive, no typed home, no honest prose classification. |
| A2 | *"Choose which action to take from those below or from the special actions provided by your features."* | `1ab39be0[39:138]` | **P** | — | `open_ended_effect`: the option space includes *"the special actions provided by your features"*, unbounded outside this record. |
| A3 | *"See also"* · *"'Playing the Game' ('Actions')."* | `47bce016[0:8]`, `f38c47eb[0:31]` | **S** | — | A section cross-reference with no record target. Not a reference — see §7. |
| A4 | *"These actions are defined elsewhere in this glossary:"* + the twelve names | `f38c47eb[32:85]`, `30194fe9[0:21]`, `eb323c9a[0:15]`, `cee71353[0:21]`, `b717e187[0:20]` | **R** | — | Twelve references, owned by the `action_choice` component (A2), matching `glossary.condition`'s accepted form. See §7. |

### 5.2 `Dash` — p.180

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| D1 | *"you gain extra movement"* | `2dc8c968[31:54]` | **X** | F1, F2 | A grant of movement budget. |
| D2 | *"The increase equals your Speed after applying any modifiers."* | `2dc8c968[77:137]` | **X** | F2 | The amount is *equal to post-modifier Speed*. `MovementAmount` admits only `FEET` and `HALF_SPEED`; `ScalingBasis` has no own-Speed member; `SpeedModificationFact` changes Speed rather than granting budget. Encoding as doubling, as a fixed number, or as a movement *cost* is false, not lossy. Fully determinate → no prose reason is true. |
| D3 | *"for the current turn"* | `2dc8c968[55:75]` | **X** | F3 | A duration. |
| D4 | *"With a"* · *"Speed of 30 feet, for example, you can move up to"* · *"60 feet … reduced to 15 feet, you can move up to 30 feet this turn if you Dash."* | `2dc8c968[138:144]`, `c5e32691[0:49]`, `4524429a[0:131]` | **S** | — | Worked examples. The printed 60 and 30 are illustrations of D2 and are not copied into a fact. |
| D5 | *"If you have a special speed, such as a Fly Speed or Swim Speed, you can use that speed instead of your"* · *"Speed when you take this action."* | `4524429a[132:234]`, `baa8bf30[0:32]` | **X** | F2 | A two-arm exhaustive choice — your Speed, or a special speed you have — which the option model expresses. *"such as"* illustrates the second arm, it does not enumerate arms. **Blocked only because each arm's fact is the missing grant**: `option_set_violations` rejects an option that states no typed facts (`representation.py:7441`). |
| D6 | *"You choose which"* · *"speed to use each time you take it."* | `baa8bf30[33:49]`, `e4ba97fe[0:35]` | **T** | — | Per-exercise re-selection is `ComponentOption`'s declared semantics: *"mutually exclusive with its siblings per exercise of the choice; selecting one does not permanently remove the others."* Not a gap. |
| D7 | *"See also"* · *"'Speed.'"* | `869c0a0b[0:8]`, `319ae274[0:8]` | **R** | — | Target `Speed`, p.188 — out of cut. |

### 5.3 `Disengage` — p.181

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| E1 | *"your movement doesn't provoke Opportunity Attacks"* | `e65d8a7b[34:83]` | **X** | F5 | Non-provocation of **another creature's** triggered reaction. `ActionRestrictionFact(REACTION)` would state that the *subject* cannot take a Reaction — a different and false claim. Determinate. |
| E2 | *"for the rest of the current turn"* | `e65d8a7b[84:116]` | **X** | F3 | Duration. |
| E3 | *"If you take the Disengage action,"* | `e65d8a7b[0:33]` | **S** | — | The action's own trigger clause. |

### 5.4 `Dodge` — p.181

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| G1 | *"any attack roll made against you has Disadvantage"* | `eed155ef[98:147]` | **T** | — | `AdvantageFact(DISADVANTAGE, RollSpec(AGAINST_SUBJECT, ATTACK_ROLL))`. Exactly the polarity `RollActor` exists for. |
| G2 | *"if you can see the attacker"* | `eed155ef[148:175]` | **P** | — | `contextual_applicability`, qualifying G1 alone. Whether the subject can see a particular attacker is fiction. |
| G3 | *"you make Dexterity saving throws with Advantage"* | `eed155ef[181:228]` | **T** | — | `AdvantageFact(ADVANTAGE, RollSpec(SUBJECT, SAVING_THROW, ability=DEXTERITY))`. |
| G4 | *"until the start of your next turn"* | `eed155ef[63:96]` | **X** | F3 | Duration. The `Recurrence` docstring names Dodge as stating *"an applicability and a duration at once"* — the axis is named, no field carries it. |
| G5 | *"You lose these benefits if you have the Incapacitated condition **or** if your Speed is 0."* | `eed155ef[230:316]` | **X** | F6a, F6b | Two termination conditions of **different kinds**, joined by `or`. `TrackedQuantity.SPEED` states the second; nothing states "has condition X"; and `Applicability.any_of` ranges over `SIZE_COMPARISON` only. Both operands are printed and closed → determinate → no prose reason is true. |
| G6 | *"If you take the Dodge action, you gain the following benefits:"* | `eed155ef[0:62]` | **S** | — | |

### 5.5 `Help` — pp.182–183

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| H1 | *"you do one of the following."* · *"Assist an Ability Check."* · *"Assist an Attack Roll."* | `7e1a032c[0:59]`, `08258187[0:24]`, `0c421a48[0:22]` | **X** | F17, F18 | An exhaustive two-arm actor choice, stated as such — the shape is right. It cannot be authored: `option_set_violations` rejects *"option states no typed facts"* (`representation.py:7441`), and **both arms' entire content is H3 and H6**, neither of which has a fact. |
| H2 | *"Choose one of your skill or tool proficiencies and one ally who is near"* · *"enough for you to assist verbally or physically when they make an ability check."* | `a6f0faa2[0:71]`, `6e7c9ae8[0:80]` | **P** | — | `contextual_applicability`: a proximity judgement over fiction, plus a use-time proficiency selection. Honest — but it is **option-specific prose**, see F19. |
| H3 | *"That ally has Advantage on the next ability check they make with the chosen skill or tool."* | `6e7c9ae8[81:171]` | **X** | F17, F18 | The rule applies determinately; the **consequence** is inexpressible. `RollActor` is closed at `SUBJECT` and `AGAINST_SUBJECT` — the ally's ability check is directed at nobody, so neither member names it. Two separable defects: the beneficiary (F17) and *"the **next** … check"*, a one-shot limiter (F18). **The `RollActor` precedent does not cover this — see §10.1.** |
| H4 | *"This benefit expires if the ally doesn't use it before the start of your next turn."* | `6e7c9ae8[172:255]` | **X** | F3 | Expiry. |
| H5 | *"The GM has final say on whether your assistance is possible."* | `6e7c9ae8[256:316]` | **X** | F19 | `gamemaster_latitude` is affirmatively true, so the **classification** is honest — but the clause governs the *first arm only*, and there is nowhere to bind it. `ProseBindingDraft` keys on `(record_key, component_key)`; `ProvenanceTargetKind` has no `OPTION` member; `FactQualifier` carries an `Applicability`, never prose. Bound at component grain it would govern the attack-roll arm too, which the source never says. |
| H6 | *"You momentarily distract an enemy within 5 feet of you, giving Advantage to the next attack roll by one of your allies against that enemy."* | `698a60f6[0:138]` | **X** | F17, F18, F19 | The ally's attack roll is against a **third** creature, not against the subject — `AGAINST_SUBJECT` is false of it. Plus the one-shot limiter, plus the 5-foot range and the *"that enemy"* coreference, which are option-scoped prose. |
| H7 | *"This benefit expires at the start of your next turn."* | `698a60f6[139:191]` | **X** | F3 | Expiry. |

### 5.6 `Hide` — p.183

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| I9 | *"With the Hide action, you try to hide yourself."* | `b2cdbf59[0:47]` | **S** | — | |
| I1 | *"you must succeed on a DC 15 Dexterity (Stealth) check"* | `b2cdbf59[58:111]` | **T** | — | `AbilityCheckFact(DEXTERITY, FIXED, 15, skill=STEALTH, context=ABILITY_CHECK)`. Every axis stated. |
| I2 | *"while you're Heavily Obscured **or** behind Three-Quarters Cover **or** Total Cover"* | `b2cdbf59[112:187]` | **X** | F6b, F6c | A three-way disjunctive prerequisite over **printed closed vocabularies** — `Heavily Obscured` is its own glossary entry (p.182) and `Cover` (p.179) prints exactly three degrees. Determinate operands, so `contextual_applicability` would be false and a prose classification would hide the gap. Contrast I7. |
| I3 | *"and you must be out of any enemy's line of sight"* | `b2cdbf59[189:237]` | **P** | — | `contextual_applicability`: line of sight is spatial fiction. Genuinely prose, unlike I2. |
| I4 | *"if you can see a creature, you can discern whether it can see you"* | `b2cdbf59[239:304]` | **P** | — | `contextual_applicability`. `SensoryCapabilityFact` states a sense grant or removal with an optional range; it cannot state a reciprocal discernment, and the referent is unenumerable. |
| I5 | *"On a successful check, you have the Invisible condition while hidden."* | `b2cdbf59[306:375]` | **T** | — | `ConditionEffectFact(INVISIBLE, APPLIES)` gated by `Applicability(ROLL_OUTCOME, SUCCESS)`. *"while hidden"* rides I7. |
| I6 | *"Make note of your check's total, which is the DC for a creature to find you with a Wisdom (Perception) check."* | `b2cdbf59[376:485]` | **X** | F7 | A DC sourced from a **recorded prior roll total**. `DcKind` admits `FIXED`, `SPELL_SAVE_DC`, `CONTESTED`, `GAMEMASTER_SET`. `CONTESTED` is the near miss and is false: a contest resolves two rolls against each other at one moment; this records a value now and reuses it as a fixed DC later, by a different creature, repeatedly. |
| I7 | *"You stop being hidden immediately after any of the following occurs: you make a sound louder than a whisper, an enemy finds you, you make an attack roll, or you cast a spell with a Verbal component."* | `b2cdbf59[486:684]` | **P** | — | `contextual_applicability`, and **honestly** so: the source states one four-way disjunction, and two of its arms (*"a sound louder than a whisper"*, *"an enemy finds you"*) are fiction no closed vocabulary reaches. Splitting into a typed half and a prose half would state two rules where the source states one. `EffectTerminationFact(OWNING_EFFECT)` may carry *that* it ends; the trigger set is the prose. See §6, F6b coverage. |

### 5.7 `Influence` — p.184

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| J1 | *"you urge a monster to do something. Describe or roleplay how you're communicating…"* | `ab01adba[0:192]` | **P** | — | `open_ended_effect`. |
| J2 | *"The GM then determines whether the monster feels willing, unwilling, or hesitant…"* | `ab01adba[193:388]` | **P** | — | `gamemaster_latitude`. **Not a gap:** the three branches need no option set. `options` is an *actor* choice, and using it for a GM determination would misstate who decides; three components, each `MIXED` with its own branch prose as applicability, is faithful under schema 5. |
| J3 | *"Willing."* · *"If your urging aligns with the monster's desires, no ability check is necessary; the monster fulfills your request in a way it prefers."* | `d1a853d4[0:8]`, `eeda1b62[0:135]` | **P** | — | `open_ended_effect`. *"No check is necessary"* is the absence of J6, not a fact. |
| J4 | *"Unwilling."* · *"If your urging is repugnant … it doesn't comply."* | `72e486bb[0:10]`, `2db001c2[0:121]` | **P** | — | `contextual_applicability`. |
| J6 | *"Hesitant."* · *"If you urge the monster to do something that it is hesitant to do, you must make an ability check,"* | `f45c09d8[0:9]`, `1fc21186[0:98]` | **X** | F8 | `AbilityCheckFact.ability` is **required and undefaulted**. The source fixes no ability, so the fact cannot be emitted — and with it the stated DC (J9) has no carrier. `gamemaster_latitude` is true of *which* ability, but the requirement that a check happens, and its DC, are determinate. |
| J5 | *"which is affected by the monster's attitude: Indifferent, Friendly, or Hostile, each of which is defined in this glossary."* | `1fc21186[99:221]` | **R** | — | Three references — out of cut. **The attitude effect is not unspecified**: `Friendly` (p.182) states *"You have Advantage on an ability check to influence a Friendly creature"* and `Hostile` (p.183) the Disadvantage; `Indifferent` (p.184) states the default attitude and no roll effect. Those facts belong to **those** records and are not imported. No numeric modifier is invented. |
| J7 | *"The Influence Checks table suggests which ability check to make based on how you're interacting with the monster."* + the title and all twelve cells | `1fc21186[222:335]`, `1fc21186[617:633]`, and 12 cell leaves | **P** | — | `gamemaster_latitude`, affirmatively true — *"suggests"*, and J8 states outright that the GM chooses. **Not a gap:** see §6, F9. |
| J8 | *"The GM chooses the check,"* | `1fc21186[336:361]` | **P** | — | `gamemaster_latitude`. |
| J9 | *"which has a default DC equal to 15 or the monster's Intelligence score, whichever is higher."* | `1fc21186[362:454]` | **X** | F10 | A DC of `max(15, the target's Intelligence **score**)`. `FIXED` states one number; `GAMEMASTER_SET` is false — the DC is stated, only the *check* is GM-chosen. `DerivedQuantityFact` is `base + own ability **modifier**` in a `TimeUnit`: wrong operand, wrong subject, wrong unit domain, and its floor is a minimum on a derived value rather than a maximum of two. Fully determinate. |
| J10 | *"On a successful check, the monster does as urged."* | `1fc21186[455:504]` | **T+P** | — | `Applicability(ROLL_OUTCOME, SUCCESS)` typed; *"does as urged"* is `open_ended_effect`. |
| J11 | *"On a failed check, you must wait 24 hours (or a duration set by the GM) before urging it in the same way again."* | `1fc21186[505:616]` | **X** | F11 | A retry cooldown. `RecoveryTrigger` admits only `SHORT_REST`, `LONG_REST`, `DAWN`, `RECHARGE_ROLL` — no elapsed-time trigger. `ConditionRemovalRestrictionFact` is scoped to a condition this record does not apply. `Applicability(ELAPSED_DURATION)` says when a component *applies*, not that a repeat is barred until a clock runs. The 24-hour default is determinate; the GM alternative is a stated override of it, not a reason the rule is unstated. |

### 5.8 `Magic` — p.185

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| K1 | *"you cast a spell that has a casting time of an action or use a feature or magic item that requires a Magic action to be activated."* | `e3f3f5e1[0:162]` | **T+P** | — | `ActionEconomyFact(ACTION)`; *"a feature or magic item"* is `open_ended_effect`. |
| K2 | *"you must take the Magic action on each turn of that casting,"* | `b196aa1b[0:127]` | **X** | F12 | A per-turn **obligation to act**. `Recurrence(START_OF_TURN)` would be **false**, not lossy: it states that an effect fires at a turn boundary, not that the subject must spend an action each turn for the effect to continue. Decided, not left borderline. |
| K3 | *"and you must maintain Concentration while you do so."* | `b196aa1b[128:180]` | **P** | — | `contextual_applicability`. `StateEffectFact(CONCENTRATION_BROKEN)` states the broken *state*, not a duty to sustain it. |
| K4 | *"If your Concentration is broken, the spell fails, but you don't expend a spell slot."* | `b196aa1b[181:265]` | **X** | F6a, F13 | Two defects. The trigger is a **state predicate** no `ApplicabilityKind` ranges over (F6a, over `StateEffectKind` rather than `ConditionKind`). The consequence is a **non-expenditure of a spell slot** (F13) — `SpellSlotProgressionFact` states a progression table, not an expenditure event. Both determinate. **Reclassified from a Known Unknown — see §10.2.** |
| K5 | *"See also"* · *"'Concentration.'"* | `a874caf3[0:8]`, `d407d33d[0:16]` | **R** | — | Target `Concentration`, p.179 — out of cut. |

### 5.9 `Ready` — pp.186–187

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| L1 | *"You take the Ready action to wait for a particular circumstance before you act. To do so, you take this action on your turn,"* | `af20f466[0:124]` | **T** | — | `ActionEconomyFact(ACTION)`. |
| L2 | *"which lets you act by taking a Reaction before the start of your next turn."* | `af20f466[125:200]` | **X** | F1, F3 | A **grant** of a Reaction slot, plus its window. |
| L3 | *"First, you decide what perceivable circumstance will trigger your Reaction."* | `af20f466[201:276]` | **P** | — | `open_ended_effect`: the trigger space is player-authored. |
| L4 | *"Then, you choose the action you will take in response to that trigger, **or** you choose to move up to your Speed in response to it."* | `af20f466[277:405]` | **X** | F2, F19 | A two-arm choice. Arm 1 is open-ended prose; arm 2 is the same own-Speed movement allowance as D2. Both arms are factless, so `option_set_violations` refuses the set — and arm 1's prose has no option-grain binding target (F19). |
| L5 | Examples: *"If the cultist steps on the trapdoor, I'll pull the lever that opens it,"* and *"If the zombie steps next to me, I move away."* | `af20f466[406:451]`, `1022361f[0:96]` | **S** | — | |
| L6 | *"When the trigger occurs, you can either take your Reaction right after the trigger finishes or ignore the trigger."* | `1022361f[97:211]` | **P** | — | `contextual_applicability`. |
| L7 | *"When you Ready a spell, you cast it as normal (expending any resources used to cast it) but hold its energy, which you release with your Reaction when the trigger occurs."* | `1022361f[212:382]` | **X** | F13 | The **positive** form of K4's expenditure: resources are expended at cast time. Same missing family. |
| L8 | *"To be readied, a spell must have a casting time of an action,"* | `1022361f[383:444]` | **P** | — | `contextual_applicability`: a prerequisite over another record's declared casting time. |
| L9 | *"and holding on to the spell's magic requires Concentration, which you can maintain up to the start of your next turn."* | `1022361f[445:562]` | **X** | F3 | Duration. |
| L10 | *"If your Concentration is broken, the spell dissipates without taking effect."* | `1022361f[563:639]` | **X** | F6a | `EffectTerminationFact(OWNING_EFFECT)` can carry the termination; its state-predicate trigger cannot be stated. |

### 5.10 `Search` — p.187

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| M1 | *"When you take the Search action, you make a Wisdom check"* | `47fb82fd[0:56]` | **T** | — | `AbilityCheckFact(WISDOM, GAMEMASTER_SET, context=ABILITY_CHECK)`. `GAMEMASTER_SET` says where the number comes from without inventing one — the case it exists for. |
| M2 | *"to discern something that isn't obvious."* | `47fb82fd[57:97]` | **P** | — | `subjective_judgment`. |
| M3 | *"The Search table suggests which skills are applicable … depending on what you're trying to detect."* + the title and all ten cells | `47fb82fd[98:221]`, `47fb82fd[222:228]`, and 10 cell leaves | **P** | — | `subjective_judgment` — *"suggests"*, and what is being detected is a judgement. **Not a gap:** §6, F9. |

### 5.11 `Study` — p.189

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| N1 | *"you make an Intelligence check to study your memory, a book, a clue, or another source of knowledge and call to mind an important piece of information about it."* | `e976a566[0:192]` | **T+P** | — | `AbilityCheckFact(INTELLIGENCE, GAMEMASTER_SET, context=ABILITY_CHECK)`; *"another source of knowledge"* and the recalled information are `open_ended_effect`. |
| N2 | *"The Areas of Knowledge table suggests which skills are applicable to various areas of knowledge."* + the title and all twelve cells | `e976a566[193:289]`, and 13 further leaves | **P** | — | `subjective_judgment`. **Not a gap:** §6, F9. |

### 5.12 `Utilize` — p.191

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| O1 | *"You normally interact with an object while doing something else, such as when you draw a sword as part of the Attack action."* | `08086c0d[0:124]` | **S** | — | A contrast that limits O2; the drawn sword is an example. |
| O2 | *"When an object requires an action for its use, you take the Utilize action."* | `08086c0d[125:200]` | **T+P** | — | `ActionEconomyFact(ACTION)`; whether a given object *requires* an action is a property of that object, `contextual_applicability`. |

### 5.13 `Attack` — p.177

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| B1 | *"When you take the Attack action, you can make one attack roll"* | `c33a980f[0:61]` | **X** | F1 | The basic attack entitlement. **`AttackRollFact` requires `to_hit_bonus: int` with no default** — the family exists to record a stat block's printed *"Melee Attack Roll: +5"*, so it cannot state *"you may make one attack roll"* without inventing a bonus this record never prints. Proof by construction. |
| B2 | *"with a weapon or an Unarmed Strike."* | `c33a980f[62:97]` | **X** | F1 | A stated, exhaustive, two-arm choice of instrument — the shape is right and the arms are factless for want of B1's fact, so `option_set_violations` refuses the set. |
| B3 | *"Equipping and Unequipping Weapons."* · *"You can either equip or unequip **one weapon** when you make an attack as part of this action."* | `e3f9e1e6[0:34]`, `50b01659[0:90]` | **X** | F1, F14 | Two defects: there is no equip/unequip family at all (`EquipmentDescriptorFact` is price and weight, `WeaponPropertyFact` is a printed property), and *"one weapon"* per attack is a per-attack allowance. |
| B4 | *"You do so either before or after the attack."* | `50b01659[91:135]` | **X** | F14 | A second binary axis over B3. The four-arm flattening — equip-before, equip-after, unequip-before, unequip-after — is exactly the permitted set and collapses no meaning, so **the option model is adequate**; the blocker is the missing equip fact. **Revision 1's component-model boundary is withdrawn — see §10.3.** |
| B5 | *"If you equip a weapon before an attack, you don't need to use it for that attack."* | `50b01659[136:217]` | **P** | — | An explicit non-requirement, conditioned on B4's timing arm. |
| B6 | *"Equipping a weapon includes drawing it from a sheath or picking it up. Unequipping a weapon includes sheathing, stowing, or dropping it."* | `50b01659[218:354]` | **S** | — | Definitional scope for B3. |
| B7 | *"Moving between Attacks."* · *"If you move on your turn and have a feature, such as Extra Attack, that gives you more than one attack as part of the Attack action, you can use some or all of that movement to move between those attacks."* | `7aed0944[0:23]`, `2a4a9331[0:204]` | **P** | — | `contextual_applicability`, by the §4 test: the unenumerable element is the gating feature, and the consequence spends an existing budget. **In scope — Revision 1's scope-leak label is withdrawn, see §10.4.** The counter-reading is recorded there. |

---

## 6. Gap families

17 blocking families. All 17 are **issue-scoped schema work**. **No Owner Decision, no
Known Unknown, and no scope exclusion survives Revision 2's reassessment**; §10 gives the
evidence for each removal.

ADR-005d Decision 4 establishes the mechanism these use: its own amendment history is a
sequence of *"admit a closed structure so mechanically distinct source meanings stop
collapsing"*, each carried by an Owner Decision **on the schema succession** — the normal
5d route, not a separate ADR.

Two admission bars apply, and they are different:

* **Vocabulary or fact-family additions** must clear `representation.py`'s stated bar —
  *"a member is admitted only with siblings in more than one section"*. This batch is one
  section (`Rules Definitions`), so **for every family below a corpus sweep is a
  precondition to admission, not a follow-up**. The batch evidence establishes that the
  gap is real; it does not establish that the family should be admitted.
* **Structural corrections** (F19) are provable by construction from the declared shapes
  and do not depend on a sibling count.

| ID | Family | Obligations | Records | Kind | Admission bar |
|---|---|---|---|---|---|
| **F3** | Duration / expiry axis | D3, E2, G4, H4, H7, L2, L9 (7) | 5 | vocabulary reuse | sweep |
| **F1** | Grant / entitlement — the inverse of consumption | A1, B1, B2, B3, D1, L2 (6) | 4 | new family | sweep |
| **F2** | Movement allowance quantified by the subject's own Speed | D1, D2, D5, L4 (4) | 2 | new family | sweep |
| **F6a** | Applicability over a state predicate | G5, K4, L10 (3) | 3 | new kind | sweep |
| **F19** | Governing prose at **option** grain | H5, H6, L4 (3) | 2 | **structural** | none — by construction |
| **F17** | A benefit conferred on another creature's roll | H1, H3, H6 (3) | 1 | new axis | sweep (weakest evidence) |
| **F18** | A one-shot *"next roll"* use limiter | H1, H3, H6 (3) | 1 | new field | sweep (weakest evidence) |
| **F6b** | Disjunction across applicability kinds | G5, I2 (2) | 2 | structural + kind | sweep |
| **F13** | Resource expenditure and non-expenditure as an event | K4, L7 (2) | 2 | new family | sweep |
| **F14** | Equipping / unequipping a weapon | B3, B4 (2) | 1 | new family | sweep |
| **F5** | Non-provocation of another creature's triggered reaction | E1 (1) | 1 | new family | sweep |
| **F6c** | Closed vocabularies for obscurement and cover degree | I2 (1) | 1 | new vocabularies | sweep |
| **F7** | A DC sourced from a recorded check total | I6 (1) | 1 | new `DcKind` | sweep |
| **F8** | `AbilityCheckFact.ability` required where the source fixes none | J6 (1) | 1 | field relaxation | sweep |
| **F10** | DC as `max(fixed, the target's ability score)` | J9 (1) | 1 | new `DcKind` | sweep |
| **F11** | Retry cooldown on an elapsed clock | J11 (1) | 1 | new family | sweep |
| **F12** | A per-turn obligation to act | K2 (1) | 1 | new family | sweep |

### Coverage of the proposed corrections against their motivating cases

The user-visible failure of Revision 1 was proposing a correction that could not express
its own example. Each proposal below is checked against **every** case it claims, and the
cases it does **not** cover are named.

**F3 — duration.** Smallest correction: a component-level duration over the existing
`RecurrenceBoundary` × `RollActor` pair, so *"until the start of your next turn"* is
`(START_OF_TURN, SUBJECT)` — reusing what `Recurrence` already declares rather than a
second spelling of a turn boundary.

| Case | Stated as | Covered |
|---|---|---|
| G4 Dodge, H7 Help | "until the start of your next turn" | ✅ `(START_OF_TURN, SUBJECT)` |
| L9 Ready | "up to the start of your next turn" | ✅ same |
| D3 Dash, E2 Disengage | "for the current turn" / "for the rest of the current turn" | ✅ `(END_OF_TURN, SUBJECT)` |
| L2 Ready | "before the start of your next turn" | ✅ same as G4 |
| H4 Help | "expires **if the ally doesn't use it** before the start of your next turn" | ⚠️ **partial** — the boundary is covered; the *use-consumption* half is F18, not F3 |

**F6a — state predicate.** Smallest correction: applicability kinds ranging over the
already-closed `ConditionKind` and `StateEffectKind` vocabularies. Two kinds, not one:
Incapacitated is a `ConditionKind`, Concentration-broken is a `StateEffectKind`, and one
kind spanning both would need a union vocabulary that is not closed today.

| Case | Stated as | Covered |
|---|---|---|
| K4 Magic, L10 Ready | "If your Concentration is broken" | ✅ `StateEffectKind.CONCENTRATION_BROKEN` |
| G5 Dodge, first arm | "if you have the Incapacitated condition" | ✅ `ConditionKind.INCAPACITATED` — but only with F6b for the `or` |

**F6b — disjunction across kinds.** Revision 1 proposed a *homogeneous* `any_of` mirroring
`SIZE_COMPARISON`. **That proposal is withdrawn: it cannot express its own motivating
case.** G5 disjoins a condition-state test with a quantity-threshold test — two different
kinds — so a within-one-kind generalization leaves G5 exactly as unrepresentable as before.

Corrected proposal, still strictly weaker than a predicate language: a **flat set of
complete `Applicability` values of possibly different kinds, satisfied when any member is**
— no nesting, no conjunction, no negation of a sub-term, no operators.

| Case | Stated as | Covered |
|---|---|---|
| G5 Dodge | "Incapacitated **or** Speed is 0" | ✅ with F6a — the case Revision 1's proposal failed |
| I2 Hide | "Heavily Obscured **or** Three-Quarters Cover **or** Total Cover" | ❌ **not covered** — the disjunction shape is fine, but no kind ranges over obscurement or cover degree. Needs F6c. |
| I7 Hide | four-way stop list | ❌ **not covered, and should not be** — two arms are fiction no closed vocabulary reaches. Flat disjunction cannot hold an untypeable arm, and splitting the set would state two rules where the source states one. I7 stays **P**. |

That I7 falls outside the correction is the correction behaving properly: the module
already refused a predicate language after its targeting-restrictions sweep, and any
proposal that swallowed I7 would be reopening exactly that.

**F1 — grant/entitlement.** Smallest correction: one closed family stating *an allowance of
N of a named economy slot per a named boundary*, reusing `ActionCost` and
`RecurrenceBoundary` rather than minting vocabularies.

| Case | Stated as | Covered |
|---|---|---|
| A1 `Action` | "one action" per turn | ✅ `(ACTION, 1, per turn)` |
| L2 Ready | a Reaction before the start of your next turn | ✅ `(REACTION, 1)` + F3 for the window |
| B1 Attack | "one attack roll" | ⚠️ **partial** — an attack roll is not an `ActionCost` member. Either the family's slot axis widens beyond action economy, or attack-count entitlement is a sibling family. **Unresolved engineering choice**, named in §8. |
| B3 Attack | "one weapon" equipped per attack | ⚠️ **partial** — same axis question, and it also needs F14's fact. |

**F2 — own-Speed movement allowance.** Smallest correction: a movement-allowance amount
whose basis is the subject's own Speed after modifiers, optionally naming one
`MovementMode`, composed with F1's grant rather than duplicating it.

| Case | Stated as | Covered |
|---|---|---|
| D1/D2 Dash | "extra movement … equals your Speed after applying any modifiers" | ✅ |
| D5 Dash | "use that speed instead of your Speed" | ✅ as the second option arm, once the arm has a fact |
| L4 Ready | "move up to your Speed" | ✅ |

**F19 — option-grain governing prose.** Provable by construction: `ProseBindingDraft` keys
on `(record_key, component_key)`; `ProvenanceTargetKind` declares `RECORD`, `COMPONENT`,
`FACT`, `FACT_QUALIFIER`, `PROSE_BINDING`, `RELATIONSHIP`, `REFERENCE` and **no `OPTION`**;
`FactQualifier` carries an `Applicability` and never prose. Smallest correction: an option
key on the prose binding plus an `OPTION` provenance target kind — the same widening
`FactQualifier.option_key` already performs for applicability, so it introduces no second
way to name an option.

| Case | Stated as | Covered |
|---|---|---|
| H5 Help | "The GM has final say" — governs arm 1 only | ✅ |
| H6 Help | 5-foot range and "that enemy" coreference — arm 2 only | ✅ |
| L4 Ready | arm 1's open action choice | ✅ |

Left unsolved by F19 alone, and stated so: an option must still carry **at least one typed
fact** (`option_set_violations`, `representation.py:7441`). An arm whose whole content is
prose remains unauthorable even with an option-grain binding. Whether that rule should
relax is an **unresolved engineering choice** (§8), not a gap this batch settles.

### Families that are *not* gaps

| ID | Why not |
|---|---|
| **F9** — suggested roll tables | **Enrichment, not a gap.** Schema 5 carries all three tables honestly as prose-bound components whose bindings are the tables' own spans: the mapping survives because it is *in the bound text*, and the non-binding character is stated by the introducing sentence. `gamemaster_latitude` is affirmatively true of Influence (*"The GM chooses the check"*); `subjective_judgment` of Search and Study (*"suggests which skills are applicable"*). A typed non-binding suggestion set would make the skills machine-readable — desirable, not required. **Revision 1 asserted a new family was needed; that is not established.** `alternatives` remains false here — it is documented as *"the complete set of equally-valid rolls the source offers for this one DC"*, a mandatory closed choice. |
| **F16** — attack interleaving | **Enrichment, and in scope.** See §4 and §10.4. |
| **F15** — option model | **Withdrawn.** Both motivating cases are representable as authored. See §10.3. |
| **F4** | Never defined; the identifier was unused in Revision 1. Recorded so the ID set is legible against the prior commit. |

---

## 7. Reference dependencies

### The criterion, from contract and precedent

ADR-005d **Decision 7**: *"Mechanical references resolve at build time through committed
source scope, aliases, and exact target semantic keys. **Unique destination names alone do
not establish source intent.**"* A bare in-text capitalized term is a unique destination
name; it is not, by itself, a citation.

The accepted authority shows exactly where the line falls:

* `glossary.condition` publishes 15 **component-owned** references from its in-text list
  *"This glossary defines these conditions:"* followed by the names — an explicit
  cross-reference apparatus, not a See-also.
* `glossary.hazard` publishes 5 **record-owned** references from its See-also list. It owns
  them at record grain because it has no component to hang them on, and *"a component
  invented for that purpose publishes a component the source never states"* (Decision 7 as
  amended).
* `hazard.dehydration` and `hazard.malnutrition` each publish exactly **one** reference to
  `condition.exhaustion`, with `source_text` = `"Exhaustion."` — **with the trailing
  period**, which is the See-also leaf's text, not the body's *"gains 1 Exhaustion level"*.
  Their bodies mention Exhaustion twice more and produce no further reference.
* `hazard.burning` applies the Prone condition in its body and publishes **no** reference:
  the in-text mention is represented as the `ConditionEffectFact`, not as a citation.

**Criterion:** a reference is emitted where the source's own cross-reference apparatus
points at another record — a See-also citation, or an explicit *"defined in this
glossary"*-style naming list. An in-text mention of a defined term used as a mechanical
operand is represented as the typed fact, not as a reference.

### The confirmed set — 17 references

| Owner | Grain | `source_text` | Target | Apparatus |
|---|---|---|---|---|
| `glossary.action` | component `action_choice` | each of the 12 printed names | the 12 action records | *"These actions are defined elsewhere in this glossary:"* |
| `action.dash` | record | `"Speed."` | `Speed`, p.188 | See also |
| `action.magic` | record | `"Concentration."` | `Concentration`, p.179 | See also |
| `action.influence` | component `influence_check` | `Indifferent`, `Friendly`, `Hostile` | the three attitude records, pp.182–184 | *"each of which is defined in this glossary"* |

Ownership note: the umbrella's references hang on `action_choice` (obligation A2), which is
an honestly prose-bound component, so no component is invented to carry them. This is
determinable now and does not wait on F1.

### Missing-target sets

`validation.py` emits `unknown target record` whenever `target_record_key` is absent from
the **draft's own** records. Both sets are therefore computable now:

| Validation | Missing targets |
|---|---|
| **Standalone** (`actions-1` alone) | `Speed`, `Concentration`, `Friendly [Attitude]`, `Hostile [Attitude]`, `Indifferent [Attitude]` — **5** |
| **Combined** (beside the frozen `conditions-1` + `hazards-1` prior) | the same **5** |

**The two sets are identical**, because none of the five is among the prior's 22 records.
An eventual proposal must assert exactly this set by source and target rather than
demanding a misleading standalone zero or allowing a broad exception.

### The two targets Revision 1 mishandled

Revision 1 listed `condition.invisible` (from `Hide`) and `condition.incapacitated` (from
`Dodge`) as references that *"resolve, and are therefore not missing"*. That was wrong
twice over, and both errors are corrected:

1. **They are not references at all.** Both are in-text operands of typed facts — I5's
   `ConditionEffectFact` and G5's applicability — which is exactly the `hazard.burning` /
   Prone case the accepted authority already decided.
2. **Had they been references, "not missing" would still have been false for standalone
   validation.** Neither condition record is in the `actions-1` draft, so standalone
   validation would report both as unknown targets; only combined validation resolves them
   against the prior. Recorded explicitly: if that authoring decision is ever revisited,
   the standalone set becomes 7 and the combined set stays 5, and the two stop being
   identical.

### Citations that are *not* references, with their reason

`Opportunity Attacks` (E1), `Ally` / `Enemy` / `Advantage` (H2, H3, H6), `Heavily
Obscured` / `Cover` (I2), `Reaction` and `Concentration` in `Ready`'s body (L2, L9),
`Unarmed Strike` (B2), `the Attack action` (O1, O2), and `Concentration` in `Magic`'s body
(K3, K4) are in-text operands with no cross-reference apparatus. `Magic` still publishes
its `Concentration` reference — from its See-also leaf (K5).

*"such as Extra Attack"* (B7) is **not a citation at all**: *"such as"* marks it as an
illustration of a feature class, the rule is stated over any such feature, and no Rules
Definitions record exists for it. Revision 1 treated its unresolvability as a scope
question; it is a reading question, and the reading settles it.

---

## 8. Unresolved engineering choices

Distinct from gaps. Each is a design question inside work that is already established as
in scope and issue-scoped; none blocks on an Owner or an ADR.

1. **F1's slot axis.** An action, a Bonus Action and a Reaction are `ActionCost` members;
   an attack roll and a weapon-equip are not. Either the grant family's slot axis widens
   past action economy, or attack-count entitlement is a sibling family. B1 and B3 are the
   forcing cases.
2. **F10's subject reference.** *"the monster's Intelligence score"* is a statistic of the
   action's target. Naming it needs some way to say *"the target of this action"*.
   `ParticipantRole` is not it — see §10.5 — so the question is what is.
3. **Whether a factless option arm should be legal.** `option_set_violations` refuses
   *"option states no typed facts"*. Help's and Ready's arms are factless only because
   their content is unrepresentable; if F17/F18/F2 land, the question disappears. It should
   not be relaxed to make this batch pass.
4. **F6a's two vocabularies.** `ConditionKind` and `StateEffectKind` as two kinds, or one
   kind over a union. Two is proposed here because no closed union vocabulary exists today.
5. **F9's shape, if it is ever enriched.** A typed non-binding suggestion set would need
   row keys, and the printed keys (*"Deceiving a monster that understands you"*,
   *"Traps, ciphers, riddles, and gadgetry"*) range over no closed vocabulary. Prose-bound
   is correct today; this is what a future enrichment would have to solve.

### Owner Decisions and Known Unknowns

**None.** Revision 1 recorded one `[OWNER DECISION]:` residue, one Known Unknown, one
ADR-level scope boundary and one scope exclusion. All four are withdrawn in §10 with
contract or source evidence. If Codex's review re-establishes any of them, that is a
finding against §10's evidence specifically, not against the ledger.

---

## 9. What any later schema step must separately address

1. **Version and hash succession.** The chain is `3 → 4 → 5` with `5d-lift-schema-3-to-4`
   and `5d-lift-schema-4-to-5`. A schema 6 needs its own lift, verified-collection set, and
   recorded from/to hashes, registered one step at a time and resolved as a path.
2. **Old-declaration legality.** `conditions-1` is anchored at schema 3, `hazards-1` at
   schema 5. Both anchors stay legal and byte-identical; neither review anchor is
   relabelled.
3. **Wire identity.** Declared-schema round trips and semantic identity checks for every
   changed shape, including the post-schema-3 omit-when-unset rule. F8 is the sharp case:
   relaxing a **required** field re-creates exactly the collapse the schema-5 amendment
   closed, because the omitted form would hash as the stated one.
4. **The invariant manifest.** Decision 4 as amended requires every intrinsic invariant a
   schema addition settles to be declared, executable, and asserted as a set equality.
   F6b's flat-disjunction rules and F19's option-grain coordinates are both invariant work,
   not only field work.
5. **Persistence and overrides** wherever a changed shape reaches them — including
   `option_set_violations` and `component_participant_violations`, which are stated over
   `(facts, options, …)` precisely so one rule governs both build time and the
   override-applied effective view.
6. **Unchanged accepted evidence.** All 22 records, 281 spans, 69 components, 20 prose
   bindings, 22 references, 281 provenance edges, 281 acceptance records, 22 obligations,
   every acceptance batch and diff, every proposal identity, every schema anchor and every
   lift must survive unchanged, unmoved, unreordered, and uncoalesced.
7. **The sweep precondition.** Every vocabulary and family in §6 needs corpus-wide sibling
   evidence before admission. This batch establishes that the gaps are real; it does not
   establish that the families should be admitted.

---

## 10. Review conclusions this revision rejects

Each rejection is Revision 1's own conclusion, overturned with source or contract evidence.

### 10.1 The `RollActor` precedent does **not** cover Help's ally rolls

*Revision 1 said:* H3 and H6 are *"already safe"* — the `RollActor` docstring decides them
as prose applicability on a `MIXED` component.

*Rejected.* The docstring's case is *"the charmer has Advantage on any ability check to
interact with you socially"*, and it describes that as **"a roll directed at the subject
whose actor restriction is applicability prose."** `AGAINST_SUBJECT` is documented as
*"Someone else makes the roll against the subject."* Help's rolls are neither:

* H3 is the ally's **own ability check**, directed at nobody;
* H6 is the ally's **attack roll against a third creature** — the distracted enemy — not
  against the subject.

No `RollActor` member names a beneficiary who is neither the subject nor rolling against
the subject, so `RollSpec` cannot identify either roll. And by §4's test the prose route is
closed: the rule's *applicability* is determinate, and the catalog reasons range over
applicability, not over consequence. → genuine gaps **F17** and **F18**.

Revision 1 also passed over two constraints entirely, both now in the ledger: the
one-shot *"next"* scope (F18) and the option-specific prose (F19).

### 10.2 Spell-slot expenditure is **not** the ADR-015b Known Unknown

*Revision 1 said:* K4 and L7 are a Known Unknown owned by an ADR-015b amendment.

*Rejected on the Known Unknown's own text.* `known_unknowns.md` scopes that entry to
*"validated typed **parameters** rather than selection through a fixed `option_id`"* —
casting-level selection and variable resource amounts — and states its resolution
requirement as *"an ADR-015b amendment defining a typed `RollAdjustmentOption` extension"*.
It then says outright: *"**Unchanged by CRD Issue 5d's schema work** … 5d **records** stated
scaling declaratively and evaluates none of it … no adjustment parameter was defined,
nothing selects a value at play time."*

K4 and L7 are declarative records of what the source states about expenditure. They define
no adjustment parameter and select nothing at play time. Recording them is precisely what
5d does. → ordinary issue-scoped schema work, **F13**, subject to the sweep bar.

### 10.3 The component option model is adequate — F15 withdrawn

*Revision 1 said:* B4 and D5 need a change to the option model, and that change is an
ADR-level scope boundary.

*Rejected twice.*

* **The cases do not need it.** B4's four-arm flattening — equip-before, equip-after,
  unequip-before, unequip-after — is exactly the set the source permits, exhaustive, one
  per attack; no mechanically distinct meaning collapses. D5 is a two-arm choice, *"that
  speed **instead of** your Speed"*, with *"such as a Fly Speed or Swim Speed"* illustrating
  the second arm rather than enumerating arms. Both blockers are the missing facts inside
  the arms (F14, F2), which `option_set_violations` reports as *"option states no typed
  facts"*.
* **It would not have been an ADR boundary anyway.** `ComponentDraft.options` documents its
  exhaustiveness as a property of *"this schema version"* and says *"a future version may
  add one when evidence requires it"* — an explicit succession seam, and every schema bump
  to date ran through an Owner Decision on the succession under Decision 4, not a new ADR.

### 10.4 Attack's interleaving is in scope — the scope-leak label is withdrawn

*Revision 1 said:* B7 is a scope leak into class-feature authority.

*Rejected on the source.* B7 resolves to `7aed0944[0:23]` and `2a4a9331[0:204]` — two
represented leaves **of `Attack [Action]` itself**, printed p.177, inside this batch's
boundary. Decision 1 requires complete source accounting, so no leaf of the batch can be
excluded from it. *"such as Extra Attack"* is an illustration, not a dependency: the rule
is stated over any feature granting more than one attack, and its unresolvability is a
reading question (§7), not a scope question.

Disposition, by §4's test: `contextual_applicability` is affirmatively true because the
gating feature is unenumerable, and the consequence spends an existing movement budget
without introducing a quantity. Same shape as the accepted `hazards-1` treatment of
Burning's rolling clause. → **P**, not blocking.

*The counter-reading, recorded rather than suppressed:* for a subject who does have such a
feature the permission is determinate, and one could argue a sequencing family is owed —
`representation.py`'s header lists sequencing among the untouched groups. This revision
takes the prose-bound reading because the accepted precedent is directly on point, and
because a family with one instance would not clear the sibling bar in any case. If Codex
takes the other reading, the consequence is one more sweep-gated family, not a change to
the stop.

### 10.5 The Influence DC is not an Owner Decision

*Revision 1 said:* J9 is `[OWNER DECISION]:` residue because it collides with the
`ParticipantRole.COUNTERPART` restriction and ADR-005d Decision 4's generic-actor boundary.

*Rejected on both.* `component_participant_violations` governs one thing: a fact that
*uses* `ParticipantRole.COUNTERPART` must sit in a component where a closed structure
establishes that counterpart. `AbilityCheckFact` has no `ParticipantRole` field at all, and
its docstring states why — *"A DC source has no actor polarity — the DC is the same value
whoever rolls against it"*, which is true of J9. Nothing collides.

Decision 4 forbids executable expressions, runtime-interpreted scripts, a general rules
DSL, model-authored logic, generic numeric/key-value escape hatches, and runtime-inferred
values. A closed `DcKind` member naming an ability score and a floor is none of those, and
Decision 4's own amendment history is a sequence of exactly such closed additions carried
by Owner Decision on the succession. → ordinary issue-scoped schema work, **F10**, with the
subject-reference question recorded as an engineering choice (§8.2).

### 10.6 Revision 1's F6 correction failed its own example

*Revision 1 proposed:* generalize `any_of` to a homogeneous set within a single
applicability kind, mirroring `SIZE_COMPARISON`.

*Rejected.* G5 — *"the Incapacitated condition **or** … Speed is 0"* — disjoins a
condition-state test with a quantity-threshold test. A within-one-kind generalization
leaves G5 exactly as unrepresentable as before, so the proposal did not cover the case it
was proposed for. §6 replaces it with a flat cross-kind disjunction and states the two
cases (I2, I7) it still does not cover.

### 10.7 Revision 1's counts and coverage

Revision 1 reported *"fifteen gap IDs across twelve of thirteen records"* from a hand
count, and its ledger carried no source coordinates. Both are replaced: every obligation
now resolves to exact `(leaf_id, char_start, char_end)` coordinates against the bound
release, and every tally is computed from the disposition table by the evidence script.
The figures moved — 17 blocking families, 31 `UNRESOLVED` obligations, 10 of 13 records —
principally because F9 was reclassified as an enrichment, which removes `Search` and
`Study` from the blocked set entirely.

---

## 11. Gates and evidence

No new production source code, so no new `black` / `ruff` / `mypy` surface. Full gate
evidence belongs to the remediation step that changes code.

| Check | Command | Result |
|---|---|---|
| Evidence script | `venv/Scripts/python .claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py` | exit 0 — 13 records, 92 leaves, 75 obligations, 132 non-overlapping spans, 31 `UNRESOLVED`, 17 blocking families |
| Determinism | three runs, `PYTHONHASHSEED` unset / `1` / `99991` | output byte-identical: `870058b8f69bd63e31a020046bdf9980bd1205fb27ce4c09d82454d0cc1e12a2` |
| Output hygiene | grep for an absolute checkout path; CRLF and UTF-8 check | 0 absolute paths, 0 CRLF, valid UTF-8 |
| Script formatting | `venv/Scripts/black --check <script>` | unchanged |
| Script lint | `venv/Scripts/ruff check <script>` | 43 findings, **all `E501`** on ledger rows where a quoted phrase must stay on one line or the matched string changes. Review-note scripts are outside the gates' scope (`ruff check src/ tests/`, `mypy files = ["src"]`), as the accepted `issue-5d-hazards-1-schema5-REGEN-generator.py` is — which itself reports 8. |
| Mechanical suite | `venv/Scripts/python -m pytest tests/ingestion/mechanical -q` | 1935 passed in 287.48 s |
| Ledger cross-check | §3's per-record obligation and `UNRESOLVED` columns recomputed from the coordinates JSON | all 13 rows match; totals 75 / 31 |

The pytest run reported `FAIL Required test coverage of 80% not reached. Total coverage:
45.56%`. That is an artifact of running **a subset** of the suite while `--cov` is
configured repository-wide, not a coverage regression: this branch adds no measurable
production source lines. Reported rather than suppressed. The full suite was not run, and
no unrun check is presented as passed.

**detect-secrets.** Baseline established at session start, before any artifact of this
work existed, so new findings are separable from pre-existing ones.

| | Blob | Content SHA-256 (LF) | Files | Findings |
|---|---|---|---|---|
| At session start (= baseline commit `b5d386ba…`) | `474ed2f15e2508d9cc31a0a4ead1b9afcf5f2cca` | `c95a0cb6555ad95c8ef8f0e7b27db060d65959600f67b2119ff83c98f15b9b9a` | 4 | 129 |
| At this branch head | recorded in the commit | recorded in the commit | 5 | 189 |

The single added entry is path-scoped to the frozen prior fixture, whose 60 findings are
the **same hashed secrets at the same line numbers** the baseline already carries for the
byte-identical committed oracle. Each was inspected: content hashes, span and proposal
identities, and UUIDs of accepted authority; none is a credential. The existing four
entries are untouched. Scanning was not disabled, no generated artifact was broadly
excluded, and the one `# pragma: allowlist secret` in the evidence script marks the SRD
source digest that script asserts against.

**Measurement scope.** The three scopes are kept apart:

| Scope | Comparison | Value |
|---|---|---|
| Whole-PR | `git diff --shortstat b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d...HEAD` | dominated by the 11,514-line frozen prior fixture, a byte-for-byte copy of accepted authority rather than authored content |
| Individual commits | three: the stop checkpoint and fixture; its accounting corrections; this revision | each stated in its own message |
| Runtime | one pytest invocation; one evidence-script invocation | 287.48 s; ~35 s |

Commits are named by role rather than by SHA: a document that cites the commit containing
it cannot stay correct after the commit that fixes it. Every figure above is re-derivable
from the command given.

Discovery **counts** (13 records, 92 leaves, 75 obligations, 31 `UNRESOLVED`) are source
measurements, not diff measurements, and are not comparable to the table above.

---

## 12. Architecture Notes

**Drift from design principles: none in what was built.** No accepted authority altered, no
acceptance recorded, nothing published, activated, retired, or merged; `accept_proposal`
was not called; #137 remains open. No schema change was implemented.

**The boundary this stop surfaces** is that representation schema 5 leaves 31 of 75
obligations, across 10 of 13 records, with no honest classification — `UNRESOLVED`, which
blocks publication by the schema's own definition. Seventeen blocking families are named,
all of them **issue-scoped schema work**; each carries a corpus-sweep precondition except
the one structural correction (F19), which is provable by construction.

**Corrections to Revision 1**, all recorded in §10 with evidence: one Known Unknown, one
Owner Decision residue, one ADR-level scope boundary and one scope exclusion are withdrawn;
one *"already safe"* precedent is rejected and becomes two gaps; one proposed correction
that failed its own example is replaced; the reference criterion is rebuilt from Decision 7
and the accepted authority, changing the confirmed set to 17 and making the standalone and
combined missing-target sets identical at 5.

**Deferred risk.** F17 and F18 rest on a single record's evidence and are the weakest
admissions proposed. F6c requires two new closed vocabularies whose corpus evidence is not
established here. F1's slot axis and F10's subject reference are open design questions
inside accepted scope. And the sweep precondition applies to sixteen of the seventeen
families: this batch proves the gaps are real, not that the families should be admitted.

---

## 13. Why regeneration has not begun

1. **The schema gate is not clear.** 31 obligations must be `UNRESOLVED`, which blocks
   publication by definition. No proposal can be admissible, at any fidelity trade.
2. **Authoring one now would require** either stating claims the source does not make — a
   doubled Speed, an invented attack bonus, a mandatory suggested check, a GM-set DC where
   one is stated, a component-grain prose binding that governs an arm it does not describe
   — or marking determinate mechanics prose-bound under reasons that are not true of them.
   Both are what the emission rule forbids, and a passing validator would prove
   admissibility rather than fidelity.
3. **Schema 5 was not widened**, no `issue-5d-actions-1-schema5-REGEN-` artifact exists,
   and the sibling map in §6 is complete enough to scope remediation once rather than as a
   sequence of one-clause changes.

Stop here for Codex's inspection and an independent semantic review. Completing `actions-1`
would complete this batch worklist, not the full-corpus or activation obligations of
CRD Issue 5d.
