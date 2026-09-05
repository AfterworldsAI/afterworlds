# CRD Issue 5d — `actions-1` discovery and schema-stop checkpoint

**Revision 3.** Revision 2 corrected Revision 1's authority classification, representation
analysis, and evidence completeness. This revision corrects **Revision 2's own
classification rule**, which misstated the closed irreducibility catalog; reassesses every
disposition that rested on it; withdraws a sibling-count admission bar that no governing
authority states; and replaces the source-coverage measurement, which understated the
unassigned residue. The conclusion — a schema stop — is unchanged across all three
revisions. Where a revision **rejects** an earlier conclusion it says so and cites the
source or contract evidence that overturns it (§10).

**Return type: schema/boundary stop.** No acceptance-ready proposal, audit, or generator
has been authored. This checkpoint accepts nothing, decides no schema change, and claims
no Owner acceptance.

**Date:** 2026-09-05
**Issue:** #137 (CRD Issue 5d)
**Branch:** `feature/issue-5d-actions-1`
**Base:** `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` (verified `origin/main`, merge of #161)
**Hygiene:** `.claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md`

### Preserved from earlier revisions, independently verified by Codex

The synchronized baseline, the frozen two-batch prior, the source binding, and the
13-record / 92-leaf boundary are unchanged and are restated in §1–§3 without alteration.
Nothing in this revision moves an identity or a boundary. The obligation and disposition
counts do move, and §10.8–§10.10 say exactly why.

### Why the stop, in one line

**35 of 78 obligations, across 10 of the 13 records, are judged `UNRESOLVED`** —
substantive source meaning for which no declared family expresses the claim faithfully
*and* no member of the closed irreducibility catalog is affirmatively true of it.
`SemanticDisposition.UNRESOLVED` is documented as *"an honest 'cannot classify safely
yet'"* that **blocks publication**. On that judgment the batch cannot yield an admissible
proposal at all, whatever fidelity one were willing to trade.

**The tallies in this document measure reviewed judgments, not semantic correctness.**
"35 `UNRESOLVED`" means 35 obligations were *judged* to have no honest classification under
schema 5. It is not proof that each judgment is right, and three revisions have now moved
the figure. Every judgment is stated with its exact bound-source coordinates and its
reasoning so a reviewer can overturn it individually; §5.14 names the ones most open to
reversal.

### Page-number convention

The ledger's `page_index` is the **0-based PDF page index**; the printed page is
`page_index + 1`. Verified on four entries against the brief's citations (Attack 176 =
p.177; Dash 179 = p.180; Influence 183 = p.184; Friendly 181 = p.182). Every page number
below is a printed page number. The one exception is quoted footer text, which already
carries the printed number.

### Machine-checked evidence

Every coordinate, disposition, and count in this document is produced by
`.claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py` and recorded in
`.claude/review-notes/issue-5d-actions-1-obligation-coordinates.json`. The script derives
the repository root from its own location, asserts the source binding before reading
anything, resolves each quoted phrase against the leaf it claims (failing if absent or
ambiguous), refuses overlapping claims, measures coverage as a **full partition of every
non-heading leaf** and **fails** on any unassigned run containing a word character, and
computes every tally from its disposition table rather than from prose. It emits no
proposal, no audit, and no representation.

```
venv/Scripts/python .claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py
-> records=13 leaves=92
   dispositions={'P': 15, 'R': 4, 'S': 13, 'T': 7, 'TP': 4, 'X': 35} unresolved=35 in 10 records
   blocking families=19
   unassigned characters=59 across 53 run(s); substantive=0
   obligations=78 rows=135 leaves_with_an_obligation=79
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

Contents verified exactly: 22 records, 281 spans, 69 components, 20 prose bindings,
0 relationships, 22 references, 281 provenance edges, 281 acceptance records,
22 obligations; batches `conditions-1` / `hazards-1`; anchors at schema 3 (proposal
`14587d5b…`) and schema 5 (proposal `f7ce4491…`); lifts `5d-lift-schema-3-to-4` then
`5d-lift-schema-4-to-5`. The live oracle was read only as an unchanged-byte sentinel and
its blob is unchanged.

---

## 3. Batch boundary

Derived from the `[Action]` entry class under `Rules Definitions`, cross-checked against
the umbrella `Action` entry's own list — *"These actions are defined elsewhere in this
glossary:"* followed by twelve names across four leaves. Twelve names, twelve labels, no
residue in either direction.

**13 records, 92 represented leaves.** Two leaves inside the boundary are policy-excluded,
both `running_header_footer` — the leaves whose whole content is *"System Reference
Document 5.2.1 183"* (in `Help`) and *"…187"* (in `Ready`), i.e. the printed p.183 and
p.187 footers. No substantive leaf is excluded.

| Record | Entry label | Printed page | Leaves | Obligations | judged `UNRESOLVED` |
|---|---|---|---|---|---|
| `glossary.action` | `Action` | 176 | 8 | 4 | 1 |
| `action.attack` | `Attack [Action]` | 177 | 6 | 7 | 5 |
| `action.dash` | `Dash [Action]` | 180 | 8 | 8 | 4 |
| `action.disengage` | `Disengage [Action]` | 181 | 2 | 3 | 2 |
| `action.dodge` | `Dodge [Action]` | 181 | 2 | 7 | 2 |
| `action.help` | `Help [Action]` | 182–183 | 7 | 7 | 7 |
| `action.hide` | `Hide [Action]` | 183 | 2 | 9 | 2 |
| `action.influence` | `Influence [Action]` | 184 | 20 | 11 | 3 |
| `action.magic` | `Magic [Action]` | 185 | 5 | 5 | 3 |
| `action.ready` | `Ready [Action]` | 186–187 | 3 | 10 | 6 |
| `action.search` | `Search [Action]` | 187 | 12 | 3 | 0 |
| `action.study` | `Study [Action]` | 189 | 15 | 2 | 0 |
| `action.utilize` | `Utilize [Action]` | 191 | 2 | 2 | 0 |
| | | | **92** | **78** | **35** |

Record keys are the shape discovery assumes; they are not authored authority.

### Leaf coverage — corrected

**Revision 2's coverage measurement was wrong and its residue figure understated.** It
measured only the gaps *between* consecutive claims and reported **74** unassigned
characters. That ignored the **head** of a leaf, before its first claim, and its **tail**,
after the last — which is exactly where a whole clause can hide. Independent verification
put the figure at **106**; re-measuring as a full partition reproduces 106 exactly.

Three of those runs were substantive source text nobody had accounted:

| Run | Text | Now |
|---|---|---|
| `Dash`[1] `2dc8c968[0:30]` | *"When you take the Dash action,"* | obligation **D8**, supporting authority — the action's own trigger clause, matching E3, G6 and I9 |
| `Dodge`[1] `eed155ef[175:181]` | *", and "* | obligation **G7**, supporting authority — the conjunction joining Dodge's two benefits |
| `Hide`[1] `b2cdbf59[47:58]` | *" To do so, "* | obligation **I10**, supporting authority — the connective between the action and its requirement |

Coverage is now a **partition of every non-heading leaf**: each character is either claimed
by an obligation or reported as an unassigned run; each run is classified; and a run
containing a **word character fails the run** rather than being counted and passed over.
That is what makes it evidence rather than a statistic — Revision 2's number could not
have failed, whatever it counted.

After the three additions: **78 obligations, 135 spans, 79 of 92 leaves** carrying an
obligation, **59 unassigned characters across 53 runs, 0 of them substantive**. The entire
residue is inter-clause punctuation — 46 single spaces, three `". "`, two `", "`, one
`"."`, one `"; "` — and every run is enumerated in the coordinates JSON with its text, so
the exact per-leaf partition an eventual proposal owes is fully specified now.

The remaining 13 leaves are each record's own **heading leaf**, accounted as record-owned
supporting authority — the `W = [(None, "R", None)]` shape the accepted `hazards-1`
generator uses for exactly this — and excluded from the partition by design, not omission.

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
| obligations | 39 | 78 (this ledger) | **not comparable** |

The two boundary counts reproduce independently from the bound source with no historical
payload read as input. The rest are **historical diagnostics**: they predate schema 5, and
deriving them is proposal work this checkpoint stops before. The obligation figure is
deliberately *not* reconciled against 39 — this ledger partitions leaf text at clause
grain, which the August artifact did not, so the two count different things.

---

## 4. The classification rule, reconciled

**Revision 2's rule was wrong and is withdrawn.** It stated that *"the catalog reasons
range over applicability, not over consequence."* Three of the six closed reasons range
over consequence, and one is named for it:

| Reason | Description | Ranges over |
|---|---|---|
| `contextual_applicability` | *"Whether the rule applies depends on fiction the projection cannot enumerate."* | applicability |
| `subjective_judgment` | *"Resolution requires a judgement call, not a computation."* | **resolution** |
| `open_ended_effect` | *"The effect space is unbounded — any faithful reduction would narrow it."* | **consequence** |
| `gamemaster_latitude` | *"The source explicitly delegates the decision to the GM."* | either |
| `natural_language_exception` | *"A natural-language exception that cannot be reduced without executable interpretation."* | a qualifier |
| `fiction_dependent_consequence` | *"**The consequence** follows from established fiction rather than from stated mechanics."* | **consequence** |

Revision 2 built a discriminator on that false premise and used it to decide two cases in
opposite directions (§10.8). The reconciled rule takes both halves from governing authority
instead.

### The governing rule

**#137 contract 3**, verbatim:

> *"If a substantive family cannot be represented by the current union, add a specific
> typed family **or** classify the affected component honestly as prose-bound. Do not use
> untyped dictionaries, generic numeric/key-value attributes, arbitrary expressions, or
> free text while claiming structured coverage. Missing source values are never invented."*

**ADR-005d Decision 4:** *"A new mechanical family requires a typed schema and tests or an
honest prose-bound classification."*

`SemanticDisposition.UNRESOLVED` is the third state neither branch reaches: *"an honest
'cannot classify safely yet'"*, which **blocks publication**.

### Decompose first — the Burning precedent, in full

The accepted `hazards-1` batch is the worked example, and Revision 2 quoted only half of
it. Burning's `self_extinguish` is a **MIXED** component: the Action cost is a typed
`ActionEconomyFact`, the Prone application is a typed `ConditionEffectFact`, the
termination is a typed `EffectTerminationFact`, and **only** the required-physical-
performance clause is bound as prose under `contextual_applicability` — *"because whether
the extinguishing applies depends on an act the projection cannot enumerate, and the
consequence is not repeated inside the binding's span."*

The lesson Revision 2 missed: **an open-ended prerequisite does not make the whole mechanic
irreducible.** Burning keeps three typed consequences beside its contextual prose.

### The rule as applied here

1. **Decompose** the clause into the claims the source states.
2. For each claim, if a declared family expresses it faithfully → **typed**.
3. Otherwise, if a closed catalog reason is affirmatively true **of that claim** — over its
   applicability, its resolution, or its consequence → **prose-bound**, at the narrowest
   scope that carries it (fact qualifier, option, or component).
4. Otherwise → **`UNRESOLVED`**.
5. Component handling follows: any typed claim beside any prose claim is `MIXED`; all prose
   is `PROSE_BOUND`; all typed is `STRUCTURED`.

Step 3's phrase *affirmatively true of that claim* is the whole test. A reason is not
available because the union lacks a field; it is available because the reason's own
description is true of what the source says.

### The rule cutting both ways, in one document

* **B7, Attack's interleaving** — decomposes. The prerequisite (*"have a feature, such as
  Extra Attack, that gives you more than one attack"*) is `contextual_applicability`, true.
  The consequence (*"you can use some or all of that movement to move between those
  attacks"*) is a determinate sequencing permission: no family expresses it, and no reason
  is true of it — it is neither unbounded, nor a judgement call, nor fiction-derived. →
  **`UNRESOLVED`**, family F16. Revision 2's **P** is withdrawn (§10.8).
* **I7, Hide's stop list** — does **not** decompose. *"You stop being hidden immediately
  after any of the following occurs: …"* states one four-way disjunctive condition, not
  four claims. Two arms are fiction no closed vocabulary reaches, and splitting the set
  into a typed half and a prose half would state two rules where the source states one.
  `contextual_applicability` is true of the condition as stated. → **P**, unchanged.

The difference is not which side of the clause is unenumerable. It is whether the source
states separable claims.

---

## 5. Per-record obligation ledger

Disposition: **T** typed under schema 5 · **P** affirmatively prose-bound under a closed
reason · **S** supporting authority · **R** source-authored reference · **X**
`UNRESOLVED`. Coordinates are `leafid[start:end]` against the bound release, leaf ids
abbreviated to eight hex characters; full ids, sliced source text, and printed page are in
the coordinates JSON.

Rows marked **↺** changed disposition in Revision 3; the reason is in the rationale.

### 5.1 `Action` — umbrella, p.176

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| A1 | *"On your turn, you can take one action."* | `1ab39be0[0:38]` | **X** | F1 | An allowance of one action per turn. `ActionEconomyFact` states what an effect *consumes*; `ActionRestrictionFact` states a slot the subject *cannot use*. Determinate over the closed `ActionCost` vocabulary, so no catalog reason is true of it. The cleanest instance of the stop. |
| A2 | *"Choose which action to take from those below or from the special actions provided by your features."* | `1ab39be0[39:138]` | **P** | — | `open_ended_effect`, a consequence-side reason: the option space includes *"the special actions provided by your features"*, unbounded outside this record. |
| A3 | *"See also"* · *"'Playing the Game' ('Actions')."* | `47bce016[0:8]`, `f38c47eb[0:31]` | **S** | — | A section cross-reference with no record target. Not a reference — §7. |
| A4 | *"These actions are defined elsewhere in this glossary:"* + the twelve names | `f38c47eb[32:85]`, `30194fe9[0:21]`, `eb323c9a[0:15]`, `cee71353[0:21]`, `b717e187[0:20]` | **R** | — | Twelve references owned by the `action_choice` component (A2), matching `glossary.condition`'s accepted form. |

### 5.2 `Dash` — p.180

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| **D8 ↺** | *"When you take the Dash action,"* | `2dc8c968[0:30]` | **S** | — | **New in Revision 3.** The action's own trigger clause, unaccounted by Revisions 1–2 (§3, §10.10). Same disposition as E3, G6, I9. |
| D1 | *"you gain extra movement"* | `2dc8c968[31:54]` | **X** | F1, F2 | A grant of movement budget. |
| D2 | *"The increase equals your Speed after applying any modifiers."* | `2dc8c968[77:137]` | **X** | F2 | The amount equals post-modifier Speed. `MovementAmount` admits only `FEET` and `HALF_SPEED`; `ScalingBasis` has no own-Speed member; `SpeedModificationFact` changes Speed rather than granting budget. Encoding as doubling, as a fixed number, or as a movement *cost* is false, not lossy. |
| D3 | *"for the current turn"* | `2dc8c968[55:75]` | **X** | F3 | A duration. |
| D4 | *"With a"* · *"Speed of 30 feet, for example…"* · *"60 feet … 30 feet this turn if you Dash."* | `2dc8c968[138:144]`, `c5e32691[0:49]`, `4524429a[0:131]` | **S** | — | Worked examples. The printed 60 and 30 illustrate D2 and are not copied into a fact. |
| D5 | *"If you have a special speed, such as a Fly Speed or Swim Speed, you can use that speed instead of your"* · *"Speed when you take this action."* | `4524429a[132:234]`, `baa8bf30[0:32]` | **X** | F2 | A two-arm exhaustive choice, which the option model expresses. Blocked only because each arm's fact is the missing grant: `option_set_violations` rejects an option that states no typed facts (`representation.py:7441`). |
| D6 | *"You choose which"* · *"speed to use each time you take it."* | `baa8bf30[33:49]`, `e4ba97fe[0:35]` | **T** | — | Per-exercise re-selection is `ComponentOption`'s declared semantics. Not a gap. |
| D7 | *"See also"* · *"'Speed.'"* | `869c0a0b[0:8]`, `319ae274[0:8]` | **R** | — | Target `Speed`, p.188 — out of cut. |

### 5.3 `Disengage` — p.181

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| E1 | *"your movement doesn't provoke Opportunity Attacks"* | `e65d8a7b[34:83]` | **X** | F5 | Non-provocation of **another creature's** triggered reaction. `ActionRestrictionFact(REACTION)` would state that the *subject* cannot take a Reaction — a different and false claim. Determinate. |
| E2 | *"for the rest of the current turn"* | `e65d8a7b[84:116]` | **X** | F3 | Duration. |
| E3 | *"If you take the Disengage action,"* | `e65d8a7b[0:33]` | **S** | — | Trigger clause. |

### 5.4 `Dodge` — p.181

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| G6 | *"If you take the Dodge action, you gain the following benefits:"* | `eed155ef[0:62]` | **S** | — | |
| G4 | *"until the start of your next turn"* | `eed155ef[63:96]` | **X** | F3 | Duration. The `Recurrence` docstring names Dodge as stating *"an applicability and a duration at once"* — the axis is named, no field carries it. |
| G1 | *"any attack roll made against you has Disadvantage"* | `eed155ef[98:147]` | **T** | — | `AdvantageFact(DISADVANTAGE, RollSpec(AGAINST_SUBJECT, ATTACK_ROLL))`. |
| G2 | *"if you can see the attacker"* | `eed155ef[148:175]` | **P** | — | `contextual_applicability`, qualifying G1 alone. Typed facts beside prose — the Burning `MIXED` shape exactly. |
| **G7 ↺** | *", and "* | `eed155ef[175:181]` | **S** | — | **New in Revision 3.** The conjunction joining the two benefits; previously unaccounted. |
| G3 | *"you make Dexterity saving throws with Advantage"* | `eed155ef[181:228]` | **T** | — | `AdvantageFact(ADVANTAGE, RollSpec(SUBJECT, SAVING_THROW, ability=DEXTERITY))`. |
| G5 | *"You lose these benefits if you have the Incapacitated condition **or** if your Speed is 0."* | `eed155ef[230:316]` | **X** | F6a, F6b | Two termination conditions of **different kinds** joined by `or`. `TrackedQuantity.SPEED` states the second; nothing states "has condition X"; `Applicability.any_of` ranges over `SIZE_COMPARISON` only. Both operands printed and closed → no reason is true. |

### 5.5 `Help` — pp.182–183

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| H1 | *"you do one of the following."* · *"Assist an Ability Check."* · *"Assist an Attack Roll."* | `7e1a032c[0:59]`, `08258187[0:24]`, `0c421a48[0:22]` | **X** | F17, F18 | An exhaustive two-arm actor choice, stated as such — the shape is right. It cannot be authored: `option_set_violations` rejects *"option states no typed facts"*, and both arms' entire content is H3 and H6, neither of which has a fact. |
| H2 | *"Choose one of your skill or tool proficiencies and one ally who is near"* · *"enough for you to assist verbally or physically when they make an ability check."* | `a6f0faa2[0:71]`, `6e7c9ae8[0:80]` | **X** | F19 | `contextual_applicability` is affirmatively true, so the **classification** is honest. Blocking for H5's reason: this is **arm 1's** prose, and bound at component grain it would govern the attack-roll arm too. |
| H3 | *"That ally has Advantage on the next ability check they make with the chosen skill or tool."* | `6e7c9ae8[81:171]` | **X** | F17, F18 | **Re-justified in Revision 3 without Revision 2's discredited rule.** Decomposed: the consequence is *"Advantage"* — stated mechanics over the closed `AdvantageState` vocabulary — on a roll `RollSpec` cannot identify, because `RollActor` is closed at `SUBJECT` and `AGAINST_SUBJECT` and the ally's check is directed at nobody. Testing each reason against that claim: `fiction_dependent_consequence` is false (the consequence *is* stated mechanics); `open_ended_effect` is false (the effect is exactly Advantage); `subjective_judgment` is false (nothing is resolved by judgement); `contextual_applicability` is false of *this* claim — the rule applies whenever Help is taken, and the unenumerable ally is a parameter of the effect, which H2 carries as its own prose. Nothing in the catalog describes *stated mechanics the union cannot name*. → X. Two separable defects: the beneficiary (F17) and *"the **next** … check"*, a one-shot limiter (F18). §10.1 rejects the `RollActor` precedent claimed to cover this; §5.14 records the other reading. |
| H4 | *"This benefit expires if the ally doesn't use it before the start of your next turn."* | `6e7c9ae8[172:255]` | **X** | F3 | Expiry. |
| H5 | *"The GM has final say on whether your assistance is possible."* | `6e7c9ae8[256:316]` | **X** | F19 | `gamemaster_latitude` is affirmatively true, so the classification is honest — but the clause governs the *first arm only* and there is nowhere to bind it. `ProseBindingDraft` keys on `(record_key, component_key)`; `ProvenanceTargetKind` has no `OPTION` member; `FactQualifier` carries an `Applicability`, never prose. |
| H6 | *"You momentarily distract an enemy within 5 feet of you, giving Advantage to the next attack roll by one of your allies against that enemy."* | `698a60f6[0:138]` | **X** | F17, F18, F19 | The ally's attack roll is against a **third** creature, not against the subject — `AGAINST_SUBJECT` is false of it. Plus the one-shot limiter, plus the 5-foot range and the *"that enemy"* coreference, which are option-scoped prose. |
| H7 | *"This benefit expires at the start of your next turn."* | `698a60f6[139:191]` | **X** | F3 | Expiry. |

### 5.6 `Hide` — p.183

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| I9 | *"With the Hide action, you try to hide yourself."* | `b2cdbf59[0:47]` | **S** | — | |
| **I10 ↺** | *" To do so, "* | `b2cdbf59[47:58]` | **S** | — | **New in Revision 3.** The connective between the action and its requirement; previously unaccounted. |
| I1 | *"you must succeed on a DC 15 Dexterity (Stealth) check"* | `b2cdbf59[58:111]` | **T** | — | `AbilityCheckFact(DEXTERITY, FIXED, 15, skill=STEALTH, context=ABILITY_CHECK)`. Every axis stated. |
| I2 | *"while you're Heavily Obscured **or** behind Three-Quarters Cover **or** Total Cover"* | `b2cdbf59[112:187]` | **X** | F6b, F6c | A three-way disjunctive prerequisite over **printed closed vocabularies**: `Heavily Obscured` is its own glossary entry (p.182) and `Cover` (p.179) prints exactly three degrees. Determinate operands, so `contextual_applicability` would be false and a prose classification would hide the gap. Contrast I7. |
| I3 | *"and you must be out of any enemy's line of sight"* | `b2cdbf59[189:237]` | **P** | — | `contextual_applicability`: line of sight is spatial fiction. Genuinely prose, unlike I2. |
| I4 | *"if you can see a creature, you can discern whether it can see you"* | `b2cdbf59[239:304]` | **P** | — | `fiction_dependent_consequence` / `contextual_applicability`: the discernment and its referent are fiction. `SensoryCapabilityFact` states a sense grant or removal with an optional range; it cannot state a reciprocal discernment. |
| I5 | *"On a successful check, you have the Invisible condition while hidden."* | `b2cdbf59[306:375]` | **T** | — | `ConditionEffectFact(INVISIBLE, APPLIES)` gated by `Applicability(ROLL_OUTCOME, SUCCESS)`. |
| I6 | *"Make note of your check's total, which is the DC for a creature to find you with a Wisdom (Perception) check."* | `b2cdbf59[376:485]` | **X** | F7 | A DC sourced from a **recorded prior roll total**. `DcKind` admits `FIXED`, `SPELL_SAVE_DC`, `CONTESTED`, `GAMEMASTER_SET`. `CONTESTED` is the near miss and is false: a contest resolves two rolls against each other at one moment; this records a value now and reuses it as a fixed DC later, by a different creature, repeatedly. |
| I7 | *"You stop being hidden immediately after any of the following occurs: you make a sound louder than a whisper, an enemy finds you, you make an attack roll, or you cast a spell with a Verbal component."* | `b2cdbf59[486:684]` | **P** | — | `contextual_applicability`, honestly. See §4: the source states one four-way disjunctive condition, not four claims, and two arms are fiction no closed vocabulary reaches. `EffectTerminationFact(OWNING_EFFECT)` may carry *that* it ends; the trigger set is the prose. |

### 5.7 `Influence` — p.184

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| J1 | *"you urge a monster to do something. Describe or roleplay how you're communicating…"* | `ab01adba[0:192]` | **P** | — | `open_ended_effect`. |
| J2 | *"The GM then determines whether the monster feels willing, unwilling, or hesitant…"* | `ab01adba[193:388]` | **P** | — | `gamemaster_latitude`. **Not a gap**, and the structural claim is checked. The three branches need no option set: `options` is an *actor* choice and would misstate who decides. Three sibling components carry them, and a component with **no typed facts** is what `PROSE_BOUND` requires — `validation.py` refuses *"structured handling with no typed facts"* and *"mixed handling with no typed facts"*, while `PROSE_BOUND` is refused only *with* typed facts. So `influence_willing` and `influence_unwilling` are `PROSE_BOUND`; `influence_hesitant` becomes `MIXED` once F8 and F10 clear. A component's `applies_when` is a typed `Applicability` with no prose form, so each branch's condition rides its prose binding. |
| J3 | *"Willing."* · *"If your urging aligns with the monster's desires…"* | `d1a853d4[0:8]`, `eeda1b62[0:135]` | **P** | — | `open_ended_effect`. *"No check is necessary"* is the absence of J6, not a fact. |
| J4 | *"Unwilling."* · *"If your urging is repugnant … it doesn't comply."* | `72e486bb[0:10]`, `2db001c2[0:121]` | **P** | — | `contextual_applicability`. |
| J6 | *"Hesitant."* · *"If you urge the monster to do something that it is hesitant to do, you must make an ability check,"* | `f45c09d8[0:9]`, `1fc21186[0:98]` | **X** | F8 | `AbilityCheckFact.ability` is **required and undefaulted**. The source fixes no ability, so the fact cannot be emitted — and with it the stated DC (J9) has no carrier. `gamemaster_latitude` is true of *which* ability, but that a check is required, and its DC, are determinate. |
| J5 | *"which is affected by the monster's attitude: Indifferent, Friendly, or Hostile, each of which is defined in this glossary."* | `1fc21186[99:221]` | **R** | — | Three references — out of cut. The attitude effect is **not** unspecified: `Friendly` (p.182) states the Advantage and `Hostile` (p.183) the Disadvantage; `Indifferent` (p.184) states the default and no roll effect. Those facts belong to **those** records and are not imported. No numeric modifier is invented. |
| J7 | *"The Influence Checks table suggests which ability check to make…"* + the title and all twelve cells | `1fc21186[222:335]`, `1fc21186[617:633]`, 12 cell leaves | **P** | — | `gamemaster_latitude`, affirmatively true — *"suggests"*, and J8 states outright that the GM chooses. Prose-bound is contract 3's **second branch**, taken deliberately; §6, F9, records what remains owed. |
| J8 | *"The GM chooses the check,"* | `1fc21186[336:361]` | **P** | — | `gamemaster_latitude`. |
| J9 | *"which has a default DC equal to 15 or the monster's Intelligence score, whichever is higher."* | `1fc21186[362:454]` | **X** | F10 | `max(15, the target's Intelligence **score**)`. `FIXED` states one number; `GAMEMASTER_SET` is false — the DC is stated, only the *check* is GM-chosen. `DerivedQuantityFact` is `base + own ability **modifier**` in a `TimeUnit`: wrong operand, wrong subject, wrong unit domain, and its floor is a minimum on a derived value rather than a maximum of two. |
| J10 | *"On a successful check, the monster does as urged."* | `1fc21186[455:504]` | **T+P** | — | `Applicability(ROLL_OUTCOME, SUCCESS)` typed; *"does as urged"* is `open_ended_effect`. |
| J11 | *"On a failed check, you must wait 24 hours (or a duration set by the GM) before urging it in the same way again."* | `1fc21186[505:616]` | **X** | F11 | A retry cooldown. `RecoveryTrigger` admits only `SHORT_REST`, `LONG_REST`, `DAWN`, `RECHARGE_ROLL` — no elapsed-time trigger. `Applicability(ELAPSED_DURATION)` says when a component *applies*, not that a repeat is barred until a clock runs. The 24-hour default is determinate; the GM alternative is a stated override of it. |

### 5.8 `Magic` — p.185

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| K1 | *"you cast a spell that has a casting time of an action or use a feature or magic item that requires a Magic action to be activated."* | `e3f3f5e1[0:162]` | **T+P** | — | `ActionEconomyFact(ACTION)`; *"a feature or magic item"* is `open_ended_effect`. |
| K2 | *"you must take the Magic action on each turn of that casting,"* | `b196aa1b[0:127]` | **X** | F12 | A per-turn **obligation to act**. `Recurrence(START_OF_TURN)` would be **false**, not lossy: it states that an effect fires at a turn boundary, not that the subject must spend an action each turn for the effect to continue. |
| **K3 ↺** | *"and you must maintain Concentration while you do so."* | `b196aa1b[128:180]` | **X** | F20 | **Revision 2 said P under `contextual_applicability`. Withdrawn:** nothing about this clause's applicability depends on unenumerable fiction. It is a determinate **requirement to sustain a state** for an ongoing effect to continue — the state half of K2's obligation. `StateEffectFact(CONCENTRATION_BROKEN)` states the broken state, not a duty to sustain it, and no reason is true of the duty. → F20. |
| K4 | *"If your Concentration is broken, the spell fails, but you don't expend a spell slot."* | `b196aa1b[181:265]` | **X** | F6a, F13 | The trigger is a **state predicate** no `ApplicabilityKind` ranges over (F6a, over `StateEffectKind`). The consequence is a **non-expenditure of a spell slot** (F13) — `SpellSlotProgressionFact` states a progression table, not an expenditure event. §10.2 rejects the Known Unknown label. |
| K5 | *"See also"* · *"'Concentration.'"* | `a874caf3[0:8]`, `d407d33d[0:16]` | **R** | — | Target `Concentration`, p.179 — out of cut. |

### 5.9 `Ready` — pp.186–187

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| L1 | *"You take the Ready action to wait for a particular circumstance before you act. To do so, you take this action on your turn,"* | `af20f466[0:124]` | **T** | — | `ActionEconomyFact(ACTION)`. |
| L2 | *"which lets you act by taking a Reaction before the start of your next turn."* | `af20f466[125:200]` | **X** | F1, F3 | A **grant** of a Reaction slot, plus its window. |
| L3 | *"First, you decide what perceivable circumstance will trigger your Reaction."* | `af20f466[201:276]` | **P** | — | `open_ended_effect`: the trigger space is player-authored. |
| L4 | *"Then, you choose the action you will take in response to that trigger, **or** you choose to move up to your Speed in response to it."* | `af20f466[277:405]` | **X** | F2, F19 | A two-arm choice. Arm 1 is open-ended prose; arm 2 is D2's own-Speed movement allowance. Both arms factless, so `option_set_violations` refuses the set — and arm 1's prose has no option-grain binding target. |
| L5 | Examples: *"If the cultist steps on the trapdoor…"* and *"If the zombie steps next to me, I move away."* | `af20f466[406:451]`, `1022361f[0:96]` | **S** | — | |
| **L6 ↺** | *"When the trigger occurs, you can either take your Reaction right after the trigger finishes or ignore the trigger."* | `1022361f[97:211]` | **X** | F16 | **Revision 2 said P under `contextual_applicability`. Withdrawn:** the clause states *when* the granted Reaction resolves — immediately after the trigger finishes — and that taking it is optional. A determinate **sequencing** statement, the same family as B7, with nothing fiction-dependent about it. |
| L7 | *"When you Ready a spell, you cast it as normal (expending any resources used to cast it) but hold its energy, which you release with your Reaction when the trigger occurs."* | `1022361f[212:382]` | **X** | F13 | The **positive** form of K4's expenditure: resources are expended at cast time. Same missing family. |
| **L8 ↺** | *"To be readied, a spell must have a casting time of an action,"* | `1022361f[383:444]` | **S** | — | **Revision 2 said P under `contextual_applicability`. Withdrawn:** a spell's casting time is a printed, enumerable `SpellDescriptorFact` field, so nothing here is unenumerable fiction. The clause *limits which spells L7 applies to*, which is `SUPPORTING_AUTHORITY`'s stated role — *"material that identifies, limits, explains, exemplifies, or contextualizes a mechanic."* Flagged in §5.14 as open to reversal. |
| L9 | *"and holding on to the spell's magic requires Concentration, which you can maintain up to the start of your next turn."* | `1022361f[445:562]` | **X** | F3 | Duration. |
| L10 | *"If your Concentration is broken, the spell dissipates without taking effect."* | `1022361f[563:639]` | **X** | F6a | `EffectTerminationFact(OWNING_EFFECT)` can carry the termination; its state-predicate trigger cannot be stated. |

### 5.10 `Search` — p.187

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| M1 | *"When you take the Search action, you make a Wisdom check"* | `47fb82fd[0:56]` | **T** | — | `AbilityCheckFact(WISDOM, GAMEMASTER_SET, context=ABILITY_CHECK)`. `GAMEMASTER_SET` says where the number comes from without inventing one — the case it exists for. |
| M2 | *"to discern something that isn't obvious."* | `47fb82fd[57:97]` | **P** | — | `subjective_judgment`, a resolution-side reason. |
| M3 | *"The Search table suggests which skills are applicable…"* + the title and all ten cells | `47fb82fd[98:221]`, `47fb82fd[222:228]`, 10 cell leaves | **P** | — | `subjective_judgment`. Contract 3's second branch; §6, F9. |

### 5.11 `Study` — p.189

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| N1 | *"you make an Intelligence check to study your memory, a book, a clue, or another source of knowledge…"* | `e976a566[0:192]` | **T+P** | — | `AbilityCheckFact(INTELLIGENCE, GAMEMASTER_SET, context=ABILITY_CHECK)`; *"another source of knowledge"* and the recalled information are `open_ended_effect`. |
| N2 | *"The Areas of Knowledge table suggests which skills are applicable…"* + the title and all twelve cells | `e976a566[193:289]`, 13 further leaves | **P** | — | `subjective_judgment`. Contract 3's second branch; §6, F9. |

### 5.12 `Utilize` — p.191

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| O1 | *"You normally interact with an object while doing something else, such as when you draw a sword as part of the Attack action."* | `08086c0d[0:124]` | **S** | — | A contrast that limits O2; the drawn sword is an example. |
| O2 | *"When an object requires an action for its use, you take the Utilize action."* | `08086c0d[125:200]` | **T+P** | — | `ActionEconomyFact(ACTION)`; which objects require an action is a set the projection cannot enumerate from this record → `contextual_applicability`, true. |

### 5.13 `Attack` — p.177

| # | Source meaning | Coordinates | Disp. | Family | Rationale |
|---|---|---|---|---|---|
| B1 | *"When you take the Attack action, you can make one attack roll"* | `c33a980f[0:61]` | **X** | F1 | The basic attack entitlement. **`AttackRollFact` requires `to_hit_bonus: int` with no default** — the family records a stat block's printed *"Melee Attack Roll: +5"*, so it cannot state *"you may make one attack roll"* without inventing a bonus this record never prints. Proof by construction. |
| B2 | *"with a weapon or an Unarmed Strike."* | `c33a980f[62:97]` | **X** | F1 | A stated exhaustive two-arm choice of instrument; the arms are factless for want of B1's fact, so `option_set_violations` refuses the set. Derived from B1, not an independent instance. |
| B3 | *"Equipping and Unequipping Weapons."* · *"You can either equip or unequip **one weapon** when you make an attack as part of this action."* | `e3f9e1e6[0:34]`, `50b01659[0:90]` | **X** | F1, F14 | No equip/unequip family exists (`EquipmentDescriptorFact` is price and weight; `WeaponPropertyFact` is a printed property), and *"one weapon"* per attack is a per-attack allowance. |
| B4 | *"You do so either before or after the attack."* | `50b01659[91:135]` | **X** | F14 | A second binary axis over B3. The four-arm flattening is exactly the permitted set and collapses no meaning, so **the option model is adequate**; the blocker is the missing equip fact. §10.3. |
| **B5 ↺** | *"If you equip a weapon before an attack, you don't need to use it for that attack."* | `50b01659[136:217]` | **S** | — | **Revision 2 said P under `contextual_applicability`. Withdrawn:** nothing here is unenumerable fiction. The clause states an explicit non-requirement that *limits* B3's permission, which is `SUPPORTING_AUTHORITY`'s stated role. Flagged in §5.14 as open to reversal. |
| B6 | *"Equipping a weapon includes drawing it from a sheath or picking it up. Unequipping a weapon includes sheathing, stowing, or dropping it."* | `50b01659[218:354]` | **S** | — | Definitional scope for B3. |
| **B7 ↺** | *"Moving between Attacks."* · *"If you move on your turn and have a feature, such as Extra Attack, that gives you more than one attack as part of the Attack action, you can use some or all of that movement to move between those attacks."* | `7aed0944[0:23]`, `2a4a9331[0:204]` | **X** | F16 | **Revision 2 said P. Withdrawn — §10.8.** Decomposed per §4: the prerequisite is `contextual_applicability`, true; the consequence is a determinate sequencing permission over an already-budgeted resource, and no catalog reason is true of it. Contract 3 names *sequencing* among the families the projection must be capable of representing, and `known_unknowns.md` already records *"one sequencing clause"* as residue from the conditions batch. In scope, per §10.4. |

### 5.14 Dispositions most open to reversal

Stated so a reviewer can go to them first rather than diffing the whole ledger.

| Obligation | Judgment | The other reading |
|---|---|---|
| **B5**, **L8** → **S** | Both *limit* a mechanic, which is `SUPPORTING_AUTHORITY`'s stated role. | Both also state something a reader could call substantive — a non-requirement and a prerequisite. If read as substantive, neither has a family and neither has a true reason, so both become **X** and the family total rises. These two moved *away* from blocking in the same pass that moved three others toward it, which is exactly the asymmetry a reviewer should test. |
| **B7**, **L6** → **X** / F16 | The consequence is determinate sequencing and no reason is true of it. | One could hold that B7's gating feature makes the whole clause `contextual_applicability` (Revision 2's reading), and that L6 is supporting authority explaining L2's grant. Both are defensible readings of a *non-decomposed* clause; §4 decomposes, following Burning. |
| **K3** → **X** / F20 | A determinate duty to sustain a state. | Could be folded into F12 as one *continuation-requirement* family rather than a sibling — §8.6. Either way the obligation is blocking. |
| **J7 / M3 / N2** → **P** | `gamemaster_latitude` / `subjective_judgment` are true, so contract 3's second branch is available. | Contract 3 names *random-table selection* as a family the projection must be capable of representing, and this batch surfaces three instances. §6 records it as owed rather than dismissed. |
| **H3 / H6** → **X** | No catalog reason describes stated mechanics the union cannot name. | If `contextual_applicability` were read as ranging over the unenumerable *ally* rather than over the rule's applicability, these would be **P** and F17/F18 would vanish. §5.5 gives the reason-by-reason test; §10.1 rejects the precedent claimed for it. |

---

## 6. Gap families

19 blocking families, all **issue-scoped schema work**. No Owner Decision, no Known
Unknown, and no scope exclusion survives the reassessment; §10 gives the evidence.

### The admission rule, corrected

**Revisions 1–2 asserted a universal admission bar that no governing authority states.**
They said every vocabulary or family addition needs *"siblings in more than one section"*
as a **precondition to admission**. That is implementation commentary, generalized:

* the language lives in **`StateEffectKind`'s own docstring**, describing how *that*
  vocabulary was bounded;
* `known_unknowns.md` scopes it the same way — `StateEffectFact`, *"over a closed
  vocabulary **whose members each required** siblings in more than one section"*;
* and the module **admitted a family that a universal bar would have refused**.
  `MovementPermissionFact` calls itself *"the thinnest family admitted here"* with two
  instances, and says outright: *"Its vocabulary is stronger than its sibling count."*

CLAUDE.md is explicit that source and tests are *"evidence of the current implementation,
not authority to redefine an accepted contract."* The governing rule is **#137 contract 3**:

> *"If a substantive family cannot be represented by the current union, add a specific
> typed family or classify the affected component honestly as prose-bound."*

No sibling count, no sweep gate. **Corpus sibling evidence remains good discipline** — it
is how `StateEffectKind` and `Sense` were bounded, and it is what turned targeting
restrictions into an honest prose classification. This checkpoint still reports per-family
instance and record counts so a reviewer can weigh each admission. It is simply not the
gate, and presenting it as one both overstated the barrier and understated contract 3's
actual requirement.

Contract 3 also **names most of these families as ones the first projection must be capable
of representing** — *"prerequisites, eligibility, choices, sequencing … contests, explicit
probability, and random-table selection … action economy, triggers, reactions … duration/
concentration, recurrence, and movement … resources, recharge/rest cadence"* — and
`known_unknowns.md` records the untouched groups as *"added by batch-driven accounting as
the corpus surfaces them, due no later than full-corpus closure."* `actions-1` is the batch
that surfaces choices and sequencing.

### The families

| ID | Family | Obligations | Records | Contract-3 group |
|---|---|---|---|---|
| **F3** | Duration / expiry axis | D3, E2, G4, H4, H7, L2, L9 (7) | 5 | duration/concentration, recurrence |
| **F1** | Grant / entitlement — the inverse of consumption | A1, B1, B3, D1, L2, + B2 *derived from B1* (6) | 4 | action economy |
| **F19** | Governing prose at **option** grain | H2, H5, H6, L4 (4) | 2 | structural, not a family group |
| **F2** | Movement allowance quantified by the subject's own Speed | D1, D2, D5, L4 (4) | 2 | movement |
| **F17** | A benefit conferred on another creature's roll | H1, H3, H6 (3) | 1 | advantage/disadvantage |
| **F18** | A one-shot *"next roll"* use limiter | H1, H3, H6 (3) | 1 | duration/recurrence |
| **F6a** | Applicability over a state predicate | G5, K4, L10 (3) | 3 | prerequisites |
| **F6b** | Disjunction across applicability kinds | G5, I2 (2) | 2 | prerequisites |
| **F13** | Resource expenditure and non-expenditure as an event | K4, L7 (2) | 2 | resources |
| **F14** | Equipping / unequipping a weapon | B3, B4 (2) | 1 | equipment |
| **F16** | Sequencing — interleaving and stated resolution order | B7, L6 (2) | 2 | **sequencing**, named |
| **F5** | Non-provocation of another creature's triggered reaction | E1 (1) | 1 | triggers, reactions |
| **F6c** | Closed vocabularies for obscurement and cover degree | I2 (1) | 1 | prerequisites |
| **F7** | A DC sourced from a recorded check total | I6 (1) | 1 | DC sources |
| **F8** | `AbilityCheckFact.ability` required where the source fixes none | J6 (1) | 1 | checks |
| **F10** | DC as `max(fixed, the target's ability score)` | J9 (1) | 1 | DC sources |
| **F11** | Retry cooldown on an elapsed clock | J11 (1) | 1 | recharge/rest cadence |
| **F12** | A per-turn **action** obligation for an ongoing effect | K2 (1) | 1 | action economy |
| **F20** | A stated duty to **sustain a state** for an ongoing effect | K3 (1) | 1 | duration/concentration |

### Coverage of the proposed corrections against their motivating cases

Each proposal is checked against **every** case it claims, and the cases it does **not**
cover are named.

**F3 — duration.** A component-level duration over the existing `RecurrenceBoundary` ×
`RollActor` pair, so *"until the start of your next turn"* is `(START_OF_TURN, SUBJECT)`.

| Case | Stated as | Covered |
|---|---|---|
| G4 Dodge, H7 Help | "until the start of your next turn" | ✅ `(START_OF_TURN, SUBJECT)` |
| L9 Ready | "up to the start of your next turn" | ✅ same |
| D3 Dash, E2 Disengage | "for the current turn" / "for the rest of the current turn" | ✅ `(END_OF_TURN, SUBJECT)` |
| L2 Ready | "before the start of your next turn" | ✅ same as G4 |
| H4 Help | "expires **if the ally doesn't use it** before the start of your next turn" | ⚠️ **partial** — the boundary is covered; the *use-consumption* half is F18 |

**F6a — state predicate.** Applicability kinds over the already-closed `ConditionKind` and
`StateEffectKind`. Two kinds, not one: Incapacitated is a `ConditionKind`,
Concentration-broken is a `StateEffectKind`, and one kind spanning both needs a union
vocabulary that is not closed today.

| Case | Stated as | Covered |
|---|---|---|
| K4 Magic, L10 Ready | "If your Concentration is broken" | ✅ `StateEffectKind.CONCENTRATION_BROKEN` |
| G5 Dodge, first arm | "if you have the Incapacitated condition" | ✅ `ConditionKind.INCAPACITATED` — only with F6b for the `or` |

**F6b — disjunction across kinds.** Revision 1 proposed a *homogeneous* `any_of` mirroring
`SIZE_COMPARISON`. **Withdrawn: it could not express its own motivating case.** G5 disjoins
a condition-state test with a quantity-threshold test — two kinds — so a within-one-kind
generalization leaves G5 exactly as unrepresentable.

Corrected proposal, still strictly weaker than a predicate language: a **flat set of
complete `Applicability` values of possibly different kinds, satisfied when any member is**
— no nesting, no conjunction, no negation of a sub-term, no operators.

| Case | Stated as | Covered |
|---|---|---|
| G5 Dodge | "Incapacitated **or** Speed is 0" | ✅ with F6a — the case Revision 1's proposal failed |
| I2 Hide | "Heavily Obscured **or** Three-Quarters Cover **or** Total Cover" | ❌ **not covered** — the shape is fine, but no kind ranges over obscurement or cover degree. Needs F6c. |
| I7 Hide | four-way stop list | ❌ **not covered, and should not be** — two arms are fiction no closed vocabulary reaches, and flat disjunction cannot hold an untypeable arm. I7 stays **P**. |

I7 falling outside the correction is the correction behaving properly: the module already
refused a predicate language after its targeting-restrictions sweep, and a proposal that
swallowed I7 would reopen exactly that.

**F1 — grant/entitlement.** One closed family stating *an allowance of N of a named economy
slot per a named boundary*, reusing `ActionCost` and `RecurrenceBoundary`.

| Case | Stated as | Covered |
|---|---|---|
| A1 `Action` | "one action" per turn | ✅ `(ACTION, 1, per turn)` |
| L2 Ready | a Reaction before the start of your next turn | ✅ `(REACTION, 1)` + F3 for the window |
| B1 Attack | "one attack roll" | ⚠️ **partial** — an attack roll is not an `ActionCost` member. §8.1. |
| B3 Attack | "one weapon" equipped per attack | ⚠️ **partial** — same axis question, and it needs F14's fact |

B2 is counted among the six but is **derived from B1**: its arms are factless only because
B1 has no fact for them to carry. The independent instances are A1, B1, B3, D1 and L2.

**F2 — own-Speed movement allowance.** An allowance whose basis is the subject's own Speed
after modifiers, optionally naming one `MovementMode`, composed with F1's grant.

| Case | Stated as | Covered |
|---|---|---|
| D1/D2 Dash | "extra movement … equals your Speed after applying any modifiers" | ✅ |
| D5 Dash | "use that speed instead of your Speed" | ✅ as the second option arm, once the arm has a fact |
| L4 Ready | "move up to your Speed" | ✅ |

**F16 — sequencing.** Contract 3 names the group; no proposal shape is offered here,
deliberately — two instances in one batch establish the gap and do not design the family,
and `known_unknowns.md` already carries a sequencing clause from the conditions batch that
any proposal must be checked against.

| Case | Stated as | The shape it needs |
|---|---|---|
| B7 Attack | "use some or all of that movement to move between those attacks" | interleaving an already-budgeted resource with a repeated action |
| L6 Ready | "take your Reaction right after the trigger finishes or ignore the trigger" | stated resolution order relative to a trigger, plus optionality |

The two are the same contract-3 group but not obviously the same shape. Naming one family
for both without the corpus sweep would be the speculation contract 3's *"add a specific
typed family"* is meant to prevent.

**F19 — option-grain governing prose.** Provable by construction: `ProseBindingDraft` keys
on `(record_key, component_key)`; `ProvenanceTargetKind` declares `RECORD`, `COMPONENT`,
`FACT`, `FACT_QUALIFIER`, `PROSE_BINDING`, `RELATIONSHIP`, `REFERENCE` and **no `OPTION`**;
`FactQualifier` carries an `Applicability` and never prose. Smallest correction: an option
key on the prose binding plus an `OPTION` provenance target kind — the same widening
`FactQualifier.option_key` already performs for applicability.

| Case | Stated as | Covered |
|---|---|---|
| H2 Help | the proficiency and ally selection — governs arm 1 only | ✅ |
| H5 Help | "The GM has final say" — governs arm 1 only | ✅ |
| H6 Help | 5-foot range and "that enemy" coreference — arm 2 only | ✅ |
| L4 Ready | arm 1's open action choice | ✅ |

Left unsolved by F19 alone: an option must still carry **at least one typed fact**
(`option_set_violations`). An arm whose whole content is prose stays unauthorable even with
an option-grain binding. §8.3.

### F9 — suggested roll tables: deferred and owed, not dismissed

Revision 2 called this an *enrichment* and justified it as *"prose preserves the mapping"*.
Both are corrected.

**What is true:** contract 3 offers two branches, and the second is available here.
`gamemaster_latitude` is affirmatively true of Influence (*"The GM chooses the check"*) and
`subjective_judgment` of Search and Study (*"suggests which skills are applicable"*). There
is no determinate claim to decompose out: the table states what the GM *may* choose, and
nothing follows from it by itself. So J7, M3 and N2 are honestly prose-bound today, and the
batch is not blocked on them.

**What Revision 2 omitted:** contract 3 lists **random-table selection** among the families
the first projection must be *capable* of representing, and `known_unknowns.md` records it
among the *"untouched"* groups *"added by batch-driven accounting as the corpus surfaces
them, **due no later than full-corpus closure**."* This batch surfaces **three instances
across three records**. That is the corpus surfacing it.

**Disposition:** prose-bound under contract 3's second branch **for this batch**, and
recorded as a **surfaced contract-3 family group still owed at full-corpus closure**. Not
an enrichment, not dismissed. What a typed form would have to solve is in §8.5.

### Families that are not blocking

| ID | Why not |
|---|---|
| **F4** | Never defined; the identifier was unused in Revision 1. Kept visible so the ID set is legible against the earlier commits. |
| **F15** — option model | **Withdrawn.** Both motivating cases are representable as authored. §10.3. |

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

Ownership note: the umbrella's references hang on `action_choice` (obligation A2), an
honestly prose-bound component, so no component is invented to carry them. Determinable
now; it does not wait on F1.

### Missing-target sets

`validation.py` emits `unknown target record` whenever `target_record_key` is absent from
the **draft's own** records. Both sets are computable now:

| Validation | Missing targets |
|---|---|
| **Standalone** (`actions-1` alone) | `Speed`, `Concentration`, `Friendly [Attitude]`, `Hostile [Attitude]`, `Indifferent [Attitude]` — **5** |
| **Combined** (beside the frozen `conditions-1` + `hazards-1` prior) | the same **5** |

**The two sets are identical**, because none of the five is among the prior's 22 records.
An eventual proposal must assert exactly this set by source and target rather than
demanding a misleading standalone zero or allowing a broad exception.

### The two targets Revision 1 mishandled

Revision 1 listed `condition.invisible` (from `Hide`) and `condition.incapacitated` (from
`Dodge`) as references that *"resolve, and are therefore not missing"*. Wrong twice over:

1. **They are not references at all** — both are in-text operands of typed facts (I5's
   `ConditionEffectFact`, G5's applicability), exactly the `hazard.burning` / Prone case
   the accepted authority already decided.
2. **Had they been references, "not missing" would still have been false for standalone
   validation.** Neither condition record is in the `actions-1` draft, so standalone
   validation would report both as unknown targets; only combined validation resolves them
   against the prior. If that authoring decision is ever revisited, the standalone set
   becomes 7, the combined set stays 5, and the two stop being identical.

### Citations that are *not* references

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

Design questions inside work already established as in scope; none blocks on an Owner or
an ADR.

1. **F1's slot axis.** An action, a Bonus Action and a Reaction are `ActionCost` members;
   an attack roll and a weapon-equip are not. Either the grant family's slot axis widens
   past action economy, or attack-count entitlement is a sibling family. B1 and B3 force it.
2. **F10's subject reference.** *"the monster's Intelligence score"* is a statistic of the
   action's target. Naming it needs a way to say *"the target of this action"*.
   `ParticipantRole` is not it (§10.5), so the question is what is.
3. **Whether a factless option arm should be legal.** `option_set_violations` refuses
   *"option states no typed facts"*. Help's and Ready's arms are factless only because
   their content is unrepresentable; if F17, F18 and F2 land, the question disappears. It
   should not be relaxed to make this batch pass.
4. **F6a's two vocabularies.** `ConditionKind` and `StateEffectKind` as two kinds, or one
   kind over a union. Two is proposed because no closed union vocabulary exists today.
5. **F9's typed shape, if it is ever built.** A non-binding suggestion set needs row keys,
   and the printed keys (*"Deceiving a monster that understands you"*, *"Traps, ciphers,
   riddles, and gadgetry"*) range over no closed vocabulary. That is the open problem the
   owed contract-3 group has to solve.
6. **Whether F12 and F20 are one family.** K2 is a per-turn *action* obligation and K3 a
   duty to *sustain a state*; both are continuation requirements for the same ongoing
   effect, stated in one sentence. One family with two operand forms would need a kind
   discriminator over two different domains, which is close to the generic shape the union
   avoids. They are kept as siblings here; merging them is a legitimate outcome of the
   schema step. Either way both obligations are blocking.
7. **F16's shape.** Interleaving a resource (B7) and stating resolution order (L6) are the
   same contract-3 group but not obviously one family. §6.

### Owner Decisions and Known Unknowns

**None.** Revision 1 recorded one `[OWNER DECISION]:` residue, one Known Unknown, one
ADR-level scope boundary and one scope exclusion. All four are withdrawn in §10 with
contract or source evidence. If review re-establishes any of them, that is a finding
against §10's evidence specifically, not against the ledger.

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
   F6b's flat-disjunction rules and F19's option-grain coordinates are invariant work, not
   only field work.
5. **Persistence and overrides** wherever a changed shape reaches them — including
   `option_set_violations` and `component_participant_violations`, stated over
   `(facts, options, …)` precisely so one rule governs both build time and the
   override-applied effective view.
6. **Unchanged accepted evidence.** All 22 records, 281 spans, 69 components, 20 prose
   bindings, 22 references, 281 provenance edges, 281 acceptance records, 22 obligations,
   every acceptance batch and diff, every proposal identity, every schema anchor and every
   lift must survive unchanged, unmoved, unreordered, and uncoalesced.
7. **Corpus sibling evidence** for each vocabulary and family — good discipline, not the
   gate (§6). The gate is contract 3: a specific typed family with schema and tests, or an
   honest prose-bound classification.

---

## 10. Review conclusions this checkpoint rejects

Each is an earlier revision's own conclusion, overturned with source or contract evidence.
§10.1–§10.7 were established in Revision 2 and are unchanged; §10.8–§10.10 are new.

### 10.1 The `RollActor` precedent does not cover Help's ally rolls

*Revision 1 said:* H3 and H6 are *"already safe"* under the `RollActor` docstring.

*Rejected.* The docstring's case is *"the charmer has Advantage on any ability check to
interact with you socially"*, described as **"a roll directed at the subject whose actor
restriction is applicability prose."** `AGAINST_SUBJECT` is *"Someone else makes the roll
against the subject."* Help's rolls are neither: H3 is the ally's own ability check,
directed at nobody, and H6 is the ally's attack roll against a third creature. No
`RollActor` member names a beneficiary who is neither the subject nor rolling against the
subject. Revision 1 also passed over the one-shot *"next"* scope (F18) and the
option-specific prose (F19).

### 10.2 Spell-slot expenditure is not the ADR-015b Known Unknown

*Revision 1 said:* K4 and L7 are a Known Unknown owned by an ADR-015b amendment.

*Rejected on the Known Unknown's own text.* It is scoped to *"validated typed
**parameters** rather than selection through a fixed `option_id`"* and resolved by *"an
ADR-015b amendment defining a typed `RollAdjustmentOption` extension"*. It then states:
*"**Unchanged by CRD Issue 5d's schema work** … 5d **records** stated scaling declaratively
and evaluates none of it … no adjustment parameter was defined, nothing selects a value at
play time."* K4 and L7 are declarative records of stated expenditure. → F13.

### 10.3 The component option model is adequate — F15 withdrawn

*Rejected twice.* B4's four-arm flattening is exactly the permitted set and collapses no
meaning; D5 is a two-arm choice with *"such as"* illustrating the second arm. Both blockers
are the missing facts *inside* the arms (F14, F2), reported as *"option states no typed
facts"*. And it would not have been an ADR boundary anyway: `ComponentDraft.options`
documents its exhaustiveness as a property of *"this schema version"* and says *"a future
version may add one when evidence requires it."*

### 10.4 Attack's interleaving is in scope

*Revision 1 said:* B7 is a scope leak into class-feature authority.

*Rejected on the source.* B7 resolves to `7aed0944[0:23]` and `2a4a9331[0:204]` — two
represented leaves **of `Attack [Action]` itself**, printed p.177, inside this batch's
boundary. Decision 1 requires complete source accounting, so no leaf of the batch can be
excluded. *"such as Extra Attack"* is an illustration, not a dependency.

### 10.5 The Influence DC is not an Owner Decision

*Rejected on both grounds.* `component_participant_violations` governs facts that *use*
`ParticipantRole.COUNTERPART`; `AbilityCheckFact` has no such field, and its docstring says
why — *"A DC source has no actor polarity — the DC is the same value whoever rolls against
it"*, true of J9. Decision 4 forbids executable expressions, DSLs, model-authored logic,
generic key-value bags and runtime-inferred values; a closed `DcKind` member naming an
ability score and a floor is none of those, and Decision 4's own amendment history is a
sequence of exactly such closed additions.

### 10.6 Revision 1's F6 correction failed its own example

G5 disjoins a condition-state test with a quantity-threshold test, so a homogeneous
within-one-kind `any_of` left it exactly as unrepresentable. Replaced by a flat cross-kind
disjunction, with the two cases it still does not cover named.

### 10.7 Revision 1's counts and coverage

Revision 1 counted gap IDs by hand and its ledger carried no source coordinates. Both are
replaced by machine-derived coordinates and tallies.

### 10.8 Revision 2's classification rule misstated the catalog — **new**

*Revision 2 said:* *"The catalog reasons range over applicability, not over consequence …
A rule that applies determinately but whose consequence the union cannot express is not
[prose-bound], so its span is `UNRESOLVED`."*

*Rejected on the catalog itself.* `subjective_judgment` ranges over **resolution**,
`open_ended_effect` over the **effect space**, and `fiction_dependent_consequence` is
literally *"**The consequence** follows from established fiction rather than from stated
mechanics."* Three of six reasons are consequence-side. Revision 2 then applied its own
premise inconsistently: it prose-bound **B7** because an unenumerable *prerequisite*
swallowed the whole clause, and marked **H3** `UNRESOLVED` because the defect was on the
consequence side — two opposite treatments from one false rule.

Compounding it, Revision 2 quoted the Burning precedent by half. `self_extinguish` is
**MIXED**: three typed consequences — the Action cost, the Prone application, the
termination — beside one prose clause. An open-ended prerequisite does **not** make the
whole mechanic irreducible.

§4 replaces the rule with contract 3's two branches plus Burning's decomposition, and every
disposition that rested on the old rule is reassessed: **B7 P→X** (F16), **L6 P→X** (F16),
**K3 P→X** (F20), **B5 P→S**, **L8 P→S**. H3 and H6 keep `UNRESOLVED` but are re-justified
reason-by-reason (§5.5) rather than by the withdrawn rule, and the alternative reading is
recorded in §5.14.

### 10.9 The universal sibling-count admission bar is withdrawn — **new**

*Revisions 1–2 said:* for every family, *"a corpus sweep is a precondition to admission,
not a follow-up."*

*Rejected as implementation commentary promoted to governing requirement.* The phrase lives
in `StateEffectKind`'s docstring; `known_unknowns.md` scopes it to that vocabulary's
members; and `MovementPermissionFact` — admitted at two instances, calling itself *"the
thinnest family admitted here"* whose *"vocabulary is stronger than its sibling count"* —
is a family the module admitted that a universal bar would have refused. CLAUDE.md: source
and tests are *"evidence of the current implementation, not authority."* The governing rule
is contract 3's *"add a specific typed family or classify the affected component honestly
as prose-bound."* Sibling evidence stays good discipline and is still reported per family;
it is not the gate (§6).

### 10.10 Revision 2's coverage measurement understated the residue — **new**

*Revision 2 reported:* 74 unassigned characters, *"all of them inter-sentence separators"*.

*Rejected on measurement.* It measured only gaps **between** consecutive claims, ignoring
each leaf's head and tail. The true figure is **106**, and three of the runs were
substantive: Dash's `2dc8c968[0:31]` (*"When you take the Dash action, "*), Dodge's
`eed155ef[175:181]`, Hide's `b2cdbf59[47:58]`. All three are now obligations D8, G7 and I10.
D8 claims `[0:30]` — the clause without its trailing space, which joins the separator
residue — so the run is fully accounted either way.

The measurement is replaced by a **full partition** that classifies every unassigned run
and **fails** on any run containing a word character. Residue is now 59 characters in 53
runs, none substantive — and, unlike Revision 2's number, that figure is falsifiable.

---

## 11. Gates and evidence

No new production source code, so no new `black` / `ruff` / `mypy` surface. Full gate
evidence belongs to the remediation step that changes code.

| Check | Command | Result |
|---|---|---|
| Evidence script | `venv/Scripts/python .claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py` | exit 0 — 13 records, 92 leaves, 78 obligations, 135 non-overlapping spans, 35 `UNRESOLVED`, 19 blocking families, 0 substantive unassigned runs |
| Coverage failure mode | remove any obligation and re-run | the run **fails** with the unaccounted text and its coordinates — which is how D8, G7 and I10 were found |
| Determinism | three runs, `PYTHONHASHSEED` unset / `1` / `99991` | output byte-identical |
| Output hygiene | grep for an absolute checkout path; CRLF and UTF-8 check | 0 absolute paths, 0 CRLF, valid UTF-8 |
| Script formatting | `venv/Scripts/black --check <script>` | unchanged |
| Script lint | `venv/Scripts/ruff check <script>` | only `E501`, on ledger rows where a quoted phrase must stay on one line or the matched string changes. Review-note scripts are outside the gates' scope (`ruff check src/ tests/`, `mypy files = ["src"]`), as the accepted `issue-5d-hazards-1-schema5-REGEN-generator.py` is |
| Mechanical suite | `venv/Scripts/python -m pytest tests/ingestion/mechanical -q` | 1935 passed in 287.48 s |
| Ledger cross-check | §3's per-record columns recomputed from the coordinates JSON | all 13 rows match; totals 78 / 35 |

The pytest run reported `FAIL Required test coverage of 80% not reached. Total coverage:
45.56%` — an artifact of running **a subset** while `--cov` is configured repository-wide,
not a coverage regression: this branch adds no production source lines. Reported rather
than suppressed. The full suite was not run, and no unrun check is presented as passed.

**detect-secrets.** Baseline established at session start, before any artifact of this
work existed, so new findings are separable from pre-existing ones.

| | Blob | Content SHA-256 (LF) | Files | Findings |
|---|---|---|---|---|
| At session start (= baseline commit `b5d386ba…`) | `474ed2f15e2508d9cc31a0a4ead1b9afcf5f2cca` | `c95a0cb6555ad95c8ef8f0e7b27db060d65959600f67b2119ff83c98f15b9b9a` | 4 | 129 |
| At this branch head | recorded in the commit | recorded in the commit | 5 | 189 |

The single added entry is path-scoped to the frozen prior fixture, whose 60 findings are
the same hashed secrets at the same line numbers the baseline already carries for the
byte-identical committed oracle. Each was inspected: content hashes, span and proposal
identities, and UUIDs of accepted authority; none is a credential. Scanning was not
disabled and no generated artifact was broadly excluded.

**Measurement scope.**

| Scope | Comparison | Value |
|---|---|---|
| Whole-PR | `git diff --shortstat b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d...93438e9` | **6 files changed, +16,089 / −0.** Measured against `93438e9`, fixed history, so it cannot go stale; re-derive the current head's with the same command and `HEAD`. Dominated by the 11,514-line frozen prior fixture — a byte-for-byte copy of accepted authority, not authored content. |
| Individual commits | five: the stop checkpoint and fixture; its accounting corrections; the evidence rebuild; that revision's own corrections; this reconciliation | each stated in its own message |
| Runtime | one pytest invocation; one evidence-script invocation | 287.48 s; ~35 s |

Commits are named by role rather than by SHA: a document that cites the commit containing
it cannot stay correct after the commit that fixes it.

Discovery **counts** (13 records, 92 leaves, 78 obligations, 35 `UNRESOLVED`) are source
measurements of reviewed judgments, not diff measurements, and are not comparable to the
table above.

---

## 12. Architecture Notes

**Drift from design principles: none in what was built.** No accepted authority altered, no
acceptance recorded, nothing published, activated, retired, or merged; `accept_proposal`
was not called; #137 remains open. No schema change was implemented.

**The boundary this stop surfaces** is that representation schema 5 leaves 35 of 78
obligations, across 10 of 13 records, with no honest classification — `UNRESOLVED`, which
blocks publication by the schema's own definition. Nineteen blocking families are named,
all **issue-scoped schema work**, and most map to family groups #137 contract 3 already
requires the first projection to be capable of representing.

**Corrections in this revision**, all in §10 with evidence: Revision 2's classification
rule is withdrawn as a misstatement of the closed catalog, and the five dispositions that
rested on it are reassessed; the universal sibling-count admission bar is withdrawn as
implementation commentary and replaced by contract 3's actual rule; the coverage
measurement is replaced by a falsifiable full partition after it was found to understate
the residue by 32 characters and to miss three substantive runs. Earlier corrections —
one Known Unknown, one Owner Decision residue, one ADR-level scope boundary, one scope
exclusion, one *"already safe"* precedent, one self-failing correction proposal, and the
reference criterion — stand as recorded.

**Deferred risk.** F17 and F18 rest on a single record's evidence. F6c requires two new
closed vocabularies whose corpus evidence is not established here. F16's two instances
establish the gap without establishing one shape. F9 is prose-bound today and owed at
full-corpus closure. F1's slot axis, F10's subject reference and the F12/F20 boundary are
open design questions inside accepted scope. And the counts throughout are judgments a
reviewer may overturn — §5.14 says where to look first.

---

## 13. Why regeneration has not begun

1. **The schema gate is not clear.** 35 obligations are judged `UNRESOLVED`, which blocks
   publication by definition. On that judgment no proposal is admissible at any fidelity
   trade.
2. **Authoring one now would require** either stating claims the source does not make — a
   doubled Speed, an invented attack bonus, a mandatory suggested check, a GM-set DC where
   one is stated, a component-grain prose binding that governs an arm it does not describe
   — or marking determinate mechanics prose-bound under reasons that are not true of them,
   which is the specific error Revision 2 made and §10.8 corrects.
3. **Schema 5 was not widened**, no `issue-5d-actions-1-schema5-REGEN-` artifact exists,
   and §6 is complete enough to scope remediation once rather than as a sequence of
   one-clause changes.

Stop here for Codex's inspection and an independent semantic review. Completing `actions-1`
would complete this batch worklist, not the full-corpus or activation obligations of
CRD Issue 5d.
