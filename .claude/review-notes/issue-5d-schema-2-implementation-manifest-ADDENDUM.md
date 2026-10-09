# CRD Issue 5d — schema-2 implementation manifest (addendum to the Conditions zero-path checkpoint)

Addendum to `.claude/review-notes/issue-5d-conditions-zero-path-CHECKPOINT.md`, which is preserved
unchanged, as are all proposals, audits, generators, and earlier checkpoints. **No code was written.**
Nothing under `src/` or `tests/` was created or modified; no branch was created; nothing was accepted,
published, or activated.

Accepted going in: conditions-1 can reach zero `UNRESOLVED` spans; no Boolean-expression DSL is required; a
closed one-level choice structure stays within ADR-005d; no Owner Decision or ADR amendment is required;
*"(usually stone)"* remains exact governing prose under `open_ended_effect`; acceptance is a later explicit
action.

**Scope discipline applied.** This manifest contains **only** what conditions-1 needs to reach zero.
Everything the previous bundle carried for actions-1 or hazards-1 is listed in §1.4 as *excluded*, with the
batch that would later justify it. Cross-batch coverage is evidence that an addition is reusable; it is not
permission to enlarge this PR.

---

## 1. Schema-delta manifest

Legend: **Required** = conditions-1 cannot reach zero without it. Sibling counts are **distinct rules after
de-duplicating restatements**, with top-level sections; corpus occurrence counts are given separately only
where they differ materially.

### 1.1 Structural addition — `ComponentDraft`

```python
class ApplicabilityKind(StrEnum):
    QUANTITY_THRESHOLD = "quantity_threshold"
    SIZE_COMPARISON    = "size_comparison"
    TRIGGER            = "trigger"
    PHASE              = "phase"

class TrackedQuantity(StrEnum):
    SPEED           = "speed"
    CONDITION_LEVEL = "condition_level"
    WEIGHT          = "weight"

class Comparison(StrEnum):
    EQUALS  = "equals"    # "if your Exhaustion level is 6"
    REACHES = "reaches"   # "when your Exhaustion level reaches 0"

class Phase(StrEnum):
    WHILE_ACTIVE = "while_active"
    ON_END       = "on_end"

class CreatureSize(StrEnum):
    TINY = "tiny"; SMALL = "small"; MEDIUM = "medium"
    LARGE = "large"; HUGE = "huge"; GARGANTUAN = "gargantuan"

class SizeRelation(StrEnum):
    SMALLER = "smaller"
    LARGER  = "larger"

@dataclass(frozen=True)
class SizeComparison:
    """Either an absolute category, or a relative distance in categories."""
    category: CreatureSize | None = None      # absolute form: "Tiny"
    relation: SizeRelation | None = None      # relative form
    at_least: int | None = None               # "two or more sizes smaller"

@dataclass(frozen=True)
class Applicability:
    kind: ApplicabilityKind
    negated: bool = False
    quantity: TrackedQuantity | None = None
    comparison: Comparison | None = None
    value: int | None = None
    any_of: tuple[SizeComparison, ...] = ()
    trigger: RecoveryTrigger | None = None
    phase: Phase | None = None

@dataclass(frozen=True)
class ComponentOption:
    """One complete typed option of an actor choice. Holds no options of its own."""
    semantic_key: str
    facts: tuple[MechanicalFact, ...]
    applies_when: Applicability | None = None

# ComponentDraft gains exactly three optional fields:
    applies_when: Applicability | None = None
    options: tuple[ComponentOption, ...] = ()
    options_exhaustive: bool = False
```

| Item | Cardinality | Required? |
|---|---|---|
| `ComponentDraft.applies_when` | 0..1 | **yes** — R5c |
| `ComponentDraft.options` | 0, or ≥ 2 | **yes** — R7a |
| `ComponentDraft.options_exhaustive` | exactly 1 bool | **yes** — R7a (*"your **only** movement options"*) |
| `ComponentOption.semantic_key` | exactly 1, non-empty | **yes** — provenance addressing (§2.1) |
| `ComponentOption.facts` | ≥ 1 | **yes** |
| `ComponentOption.applies_when` | 0..1 | **yes** — R8 |
| `Applicability.negated` | exactly 1 bool | **yes** — R5c, R8 |

**Allowed / forbidden combinations**

| Rule | Rationale |
|---|---|
| `options` non-empty **and** `facts` non-empty → **rejected** | a component is a conjunction *or* a choice, never silently both |
| `len(options) == 1` → **rejected** | a one-element choice is a plain component misdescribed |
| `options_exhaustive=True` with empty `options` → **rejected** | vacuous |
| duplicate `ComponentOption.semantic_key` within one component → **rejected** | provenance keys must address exactly one element |
| two options with byte-identical canonical `facts` → **rejected** | a duplicate option is a modelling error, not a choice |
| `ComponentOption` containing options | **unrepresentable by construction** — the dataclass has no such field |
| `Applicability` populated fields not matching its `kind` → **rejected** | e.g. `QUANTITY_THRESHOLD` with `any_of` set |
| `Applicability` with `kind` set and no other field populated → **rejected** | vacuity, the guard class PR #153's review added |
| `SizeComparison` with neither `category` nor (`relation` and `at_least`) → **rejected** | vacuity |
| `SizeComparison` with both `category` and `relation` → **rejected** | absolute and relative are distinct forms |
| `Applicability.negated=True` on a sub-term | **unrepresentable by construction** — there are no sub-terms |

**Canonical serialization.** `Applicability`, `SizeComparison`, and `ComponentOption` are single nested
value objects the closed shape grammar already inlines; `options` and `any_of` render as `array`. No
`_shape` change and no tagged-union rendering is required — this is why `Applicability` is one
discriminated dataclass rather than a Python union.

**Ordering.** Not mechanically meaningful in any of the three collections. `options` is canonically ordered
by each option's `semantic_key`; `any_of` by its canonical form. Source order does not reach the hash. The
source's own order in Prone (*"crawl or to … right yourself"*) carries no precedence.

**Siblings.** `applies_when` — quantity threshold 5 distinct rules / 2 sections (Prone, Dropping Prone,
Exhaustion ×2, Instant Death); size comparison 9 / 4; trigger reuses the existing `RecoveryTrigger`; phase
34 occurrences / 4 sections. `options` — exclusive choice 55 occurrences / 9 sections.

**Resolves** R5c, R7a, R8, R9, and hosts R7b/R7c.

### 1.2 New fact families — required for Conditions closure

| Family | Fields (types, cardinality) | Invariants | Distinct rules / sections | Resolves |
|---|---|---|--:|---|
| `SENSORY_CAPABILITY` | `sense: Sense` (1); `can_perceive: bool` (1); `range_feet: int \| None` (0..1) | `range_feet` set only when `can_perceive=True`; `range_feet > 0` | vocabulary printed (4 glossary entries, 373 occ / 9 sec); the *removal* form is **2 rules / 1 section** | R1, R2 |
| `CONDITION_LEVEL` | `condition: ConditionKind` (1); `direction: LevelDirection` (1: GAIN\|REMOVE); `amount: int \| None` (0..1); `all_levels: bool` (1); `cumulative: bool` (1) | exactly one of `amount` / `all_levels`; `amount > 0`; `cumulative` only with GAIN | 20 / 6 | R3a, R4a |
| `MOVEMENT_COST` | `kind: MovementCostKind` (1: PER_FOOT_SURCHARGE\|EXPENDITURE); `amount: MovementAmount` (1: FEET\|HALF_SPEED); `feet: int \| None` (0..1) | `feet` set **exactly** for FEET; `feet > 0` | surcharge 8 / 2, expenditure 6 / 4 | R5b, R7c |
| `MOVEMENT_PERMISSION` | `mode: MovementMode` (1) | — | **2 / 2** (Prone; Tsunami *"can move by swimming"*) | R7b |
| `TRANSFORMATION` | `becomes: TransformedForm` (1: OBJECT\|CREATURE_FORM); `carried_nonmagical_included: bool` (1) | — | 14 occ / 3 sec; both `becomes` members and both inclusion values instantiated | R6a |
| `QUANTITY_MULTIPLIER` | `quantity: TrackedQuantity` (1); `factor: int` (1) | `factor >= 2` | 6 / 6 | R6b |

**`MOVEMENT_PERMISSION` is the thinnest addition and is flagged as such.** Two distinct rules in two
top-level sections meets PR #153's admission bar — the same bar `UNAWARE_OF_SURROUNDINGS` cleared in the
merged union — but only just. Its *vocabulary* is stronger than its family: `Playing the Game > Movement
and Position` prints the mode list (*"Your movement can include climbing, crawling, jumping, and
swimming"*) and `Rules Glossary > Speed` cross-references the same set, so `MovementMode += CRAWL` is a
printed-vocabulary extension rather than an invention. If review rejects the family, the alternative carrier
is a typed cross-record reference from the option to the `Crawling` glossary rule, which would require
`ReferenceDraft` to become option-addressable. **Prose-binding R7b is not an available fallback** — crawling
is a defined mode, so a prose binding would be a backlog state.

**`SENSORY_CAPABILITY` evidence, stated precisely.** The *vocabulary* is printed and closed — Blindsight,
Darkvision, Tremorsense and Truesight are glossary entries, and Blindsight's own text ties sight-capability
to the Blinded condition (*"you can see … even if you have the Blinded condition"*). The *imposed-removal
form* is 2 rules in 1 section (Blinded, Deafened). The family carries both poles, so the printed senses are
its extension seam rather than decoration.

### 1.3 Extensions to existing types — required

| Extension | Distinct rules / sections | Resolves |
|---|--:|---|
| `StateEffectKind += DIES` | 86 occurrences / 8 sections | R3b |
| `StateEffectKind += AGING_SUSPENDED` | 2 / 2 (Petrified, Imprisonment) — thin, at the `UNAWARE_OF_SURROUNDINGS` bar | R6c |
| `MovementMode += CRAWL` | printed mode list, `Playing the Game > Movement and Position` | R7b |
| `Sense` (new enum, 2 members: SIGHT, HEARING) | see §1.2 | R1, R2 |
| `LevelDirection`, `MovementCostKind`, `MovementAmount`, `TransformedForm` (new enums, 2 members each, all instantiated) | with their families | — |
| **`ConditionEffectKind`** | **no change** — `REMOVES` already exists | R4b, R7c |

### 1.4 Excluded — not required for Conditions closure

Carried in the previous bundle, **dropped from this PR**, with the batch that would justify it:

`ApplicabilityKind.ROLL_OUTCOME` (actions, hazards) · `ComponentDraft.lasts` + `DurationWindow` +
`TurnBoundary` (actions) · `ComponentDraft.recurs` + `Recurrence` (hazards) · `ALLOWANCE` (actions) ·
`OPPORTUNITY_ATTACK_EXEMPTION` (actions) · `CONCENTRATION_REQUIREMENT` (actions) · `Skill` enum +
`RollSpec.skill` + `AbilityCheckFact.skill` (actions, hazards) · `AbilityCheckFact.alternatives` (hazards) ·
`DcKind += NOT_STATED, DERIVED` (actions) · `RollActor += ALLY` (actions) · `DamageFact.maximum_dice`
(hazards) · `ScalingBasis += DISTANCE_FALLEN` (hazards) · `MovementAmount.ALL_REMAINING` (actions) ·
`TrackedQuantity.HIT_POINT_MAXIMUM` (evidence for the vocabulary's closure; no conditions obligation uses
it) · `Comparison.AT_OR_ABOVE` (hazards).

---

## 2. Conditions obligation map — all seventeen

`E` existing · `N` new in §1. Record keys follow the conditions-1 audit trail.

| # | Record | Exact source span | Representation | Provenance | Faithfulness | Siblings |
|---|---|---|---|---|---|---|
| R1 | `condition.blinded` | *"You can't see"* | `SensoryCapabilityFact(SIGHT, can_perceive=False)` **N** | FACT, PRIMARY | states the capability the rule removes and nothing more; the contextual consequences are already carried by the adjacent `AutomaticOutcomeFact` and its prose | printed sense vocabulary |
| R2 | `condition.deafened` | *"You can't hear"* | `SensoryCapabilityFact(HEARING, can_perceive=False)` **N** | FACT, PRIMARY | as R1 | as R1 |
| R3a | `condition.exhaustion` | *"This condition is cumulative. Each time you receive it, you gain 1 Exhaustion level."* | `ConditionLevelFact(EXHAUSTION, GAIN, amount=1, cumulative=True)` **N** | FACT, PRIMARY | carries the level delta the merged union could only state as bare application | 20 / 6 |
| R3b | `condition.exhaustion` | *"You die if your Exhaustion level is 6."* | `StateEffectFact(DIES)` **E family, N member** + `Applicability(QUANTITY_THRESHOLD, CONDITION_LEVEL, EQUALS, 6)` **N** | FACT PRIMARY; the applicability rides the component | threshold and consequence are separate and both stated | *dies* 86 / 8; threshold 5 / 2 |
| **R4a** | `condition.exhaustion` | *"Finishing a Long Rest removes 1 of your Exhaustion levels."* | `ConditionLevelFact(EXHAUSTION, REMOVE, amount=1)` **N** + `Applicability(TRIGGER, LONG_REST)` **N kind, E vocabulary** | FACT, PRIMARY | reuses the existing `RecoveryTrigger` vocabulary rather than a new rest concept | removal 4 / 3 |
| **R4b** | `condition.exhaustion` | *"When your Exhaustion level reaches 0, the condition ends."* | **`ConditionEffectFact(EXHAUSTION, REMOVES)` — existing, unchanged** + `Applicability(QUANTITY_THRESHOLD, CONDITION_LEVEL, REACHES, 0)` **N** | FACT, PRIMARY | "the condition ends" *is* removal of the condition, which the merged union already models | — |
| R5a | `condition.grappled` | *"The grappler can drag or carry you when it moves,"* | `SUPPORTING_AUTHORITY`, contextually linked to the movement component **E** | COMPONENT, CONTEXTUAL | identifies whose movement is surcharged; adding a forced-movement fact would claim a displacement the clause does not state | — |
| R5b | `condition.grappled` | *"but every foot of movement costs it 1 extra foot"* | `MovementCostFact(PER_FOOT_SURCHARGE, FEET, feet=1)` **N** | FACT, PRIMARY | states the rate change exactly | 8 / 2 |
| R5c | `condition.grappled` | *"unless you are Tiny or two or more sizes smaller than it."* | `Applicability(SIZE_COMPARISON, negated=True, any_of=(SizeComparison(category=TINY), SizeComparison(relation=SMALLER, at_least=2)))` **N** | rides the component carrying R5b | *unless* is one negation over a homogeneous set of size predicates — not a Boolean expression | 9 / 4 |
| R6a | `condition.petrified` | *"You are transformed, along with any nonmagical objects you are wearing and carrying, into a solid inanimate substance"* | `TransformationFact(becomes=OBJECT, carried_nonmagical_included=True)` **N** | FACT, PRIMARY | True Polymorph states the identical creature→object-with-carried-gear structure | 14 occ / 3 sec |
| R6b | `condition.petrified` | *"Your weight increases by a factor of ten,"* | `QuantityMultiplierFact(WEIGHT, factor=10)` **N** | FACT, PRIMARY | a multiplication, not a basis-driven scaling; `ScalingFact` would misstate it | 6 / 6 |
| R6c | `condition.petrified` | *"and you cease aging."* | `StateEffectFact(AGING_SUSPENDED)` **E family, N member** | FACT, PRIMARY | a state the subject is placed in, matching the family's existing members | 2 / 2 |
| R6d | `condition.petrified` | *"(usually stone)"* | governing prose, `open_ended_effect` → component `MIXED` **E** | PROSE_BINDING, PRIMARY | the source hedges with *"usually"*, so the substance space is unbounded; the load-bearing claim is typed by R6a | — |
| R7a | `condition.prone` | *"Your only movement options are"* | `options=(crawl, stand)`, `options_exhaustive=True` **N** | COMPONENT, CONTEXTUAL | *only* is the exhaustiveness flag; without it the set would read as illustrative | 55 occ / 9 sec |
| R7b | `condition.prone` | *"to crawl"* | option `crawl` = `(MovementPermissionFact(CRAWL),)` **N** | FACT, PRIMARY, addressed via the option's `semantic_key` | names a printed movement mode | 2 / 2 (thin, §1.2) |
| R7c | `condition.prone` | *"or to spend an amount of movement equal to half your Speed (round down) to right yourself and thereby end the condition."* | option `stand` = `(MovementCostFact(EXPENDITURE, HALF_SPEED), `**`ConditionEffectFact(PRONE, REMOVES)`**` )` **N + E** | FACT ×2, PRIMARY | cost and consequence are both stated and both typed; Mounting states the identical half-Speed expenditure | expenditure 6 / 4 |
| R8 | `condition.prone` | *"If your Speed is 0, you can't right yourself."* | option `stand`.`applies_when = Applicability(QUANTITY_THRESHOLD, SPEED, EQUALS, 0, negated=True)` **N** | rides the option | attaches the prohibition to the option it prohibits, so no act vocabulary is needed | 2 / 2 (Prone; `Playing the Game > Dropping Prone`, identical predicate) |
| R9 | `condition.unconscious` | *"When this condition ends, you remain Prone."* | **`ConditionEffectFact(PRONE, APPLIES)` — existing, unchanged** + `Applicability(PHASE, ON_END)` **N** | FACT, PRIMARY | phase separates "while Unconscious" from "after it ends" without a new effect family | 34 occ / 4 sec |

### 2.1 The two obligations already carried by `ConditionEffectKind.REMOVES`

**R4b** (*"When your Exhaustion level reaches 0, the condition ends"*) and **R7c** (*"…right yourself and
thereby end the condition"*). `ConditionEffectKind.REMOVES` has been in the merged union since before
conditions-1 was accounted (`representation.py:427`). Both were previously reported as blocked. Neither
needs any new fact family — only the applicability that says *when* removal happens (R4b) and the option
that carries it (R7c).

**Provenance addressing for facts inside options.** `fact_target_key(record_key, component_key, fact)`
cannot address two identical facts in different options, and index-based keys are unstable because options
are canonically ordered. The key therefore becomes
`(record_key, component_key, option_semantic_key, fact_key(fact))`, with `option_semantic_key` empty for
facts held directly on the component. This is why `ComponentOption` carries a `semantic_key` and why
duplicate keys are rejected.

---

## 3. Alternatives semantics — scoped to what Conditions requires

**What Prone's clause is.** Reading *"Your only movement options are to crawl or to spend … to right
yourself"*: the prone creature is the actor; it selects one option per exercise of movement; the source's
*"only"* makes the set complete. It is **not** a one-shot irrevocable selection — a creature may crawl on
one turn and stand on another — so the correct semantics is **an exhaustive set of mutually exclusive typed
options from which the actor selects one per exercise**, not "exactly one option holds for the duration".

Of the three readings offered:

| Reading | Verdict |
|---|---|
| an actor choice | **yes** — the prone creature chooses |
| exactly one selected option | **yes, per exercise** — not "one for all time" |
| mutually exclusive typed component variants | **yes** — each option is a complete typed variant, and no two apply simultaneously |

**Renamed from `alternatives` to `options`.** "Alternatives" is ambiguous between an actor choice and a
conditional branch. The field is `ComponentDraft.options`, holding `ComponentOption`s, and it means
**actor choice only**.

| Question | Answer |
|---|---|
| Minimum options | **2**. One is rejected |
| Maximum options | **no fixed cap**; the invariant that matters is ≥ 2 and pairwise-distinct |
| Nesting | **forbidden by construction** — `ComponentOption` has no `options` field, so the structure is exactly one level deep and no check is needed |
| Duplicate options | **forbidden** — duplicate `semantic_key`, and duplicate canonical `facts`, both rejected |
| Source or canonical order controls identity | **canonical**. Options are sorted by `semantic_key`; source order does not reach the hash. Prone's order carries no precedence |
| Selection ownership | the actor is the component's subject. Conditions-1 needs no other owner, so **no owner field is added**. A rule whose options are chosen by another party (a GM, an opposing creature) is out of scope and would force the field with its own evidence |
| Does it also represent conditional outcomes? | **No, and deliberately not.** *"On a successful check, you have the Invisible condition"* is a conditional outcome: no actor chooses, and the branch is selected by a roll. That is `Applicability(ROLL_OUTCOME)`, a **different** structure, and it is **excluded from this PR** (§1.4) because no conditions-1 obligation needs it |

Keeping those two concepts in separate structures is the point: one ambiguous tuple shape covering both
would let a conditional branch be authored as a choice, and nothing would catch it.

---

## 4. Open-referent correction

The previous checkpoint lumped all 18 remaining actions-1 / hazards-1 obligations as "open referent,
runtime". That was too coarse. Re-separated — and **all 18 remain `UNRESOLVED`**; none is reclassified as
prose-bound here, because affirmative prose-bound status needs independent support that this work has not
established.

| Category | Count | Members | Disposition |
|---|--:|---|---|
| **(a) crisp but presently unmodeled predicates** | **11** | Hide's *"Heavily Obscured or behind Three-Quarters Cover or Total Cover, and … out of any enemy's line of sight"* (the obscurement and cover grades are **printed closed vocabularies**, 54 occ / 8 sec); Help's *"within 5 feet"*; Help's proficiency selection; Magic's *"a spell that has a casting time of an action"*; Hide's reciprocal perception; Falling's *"unless it avoids taking any damage"*; Malnutrition/Dehydration consumption thresholds ×2; the three removal restrictions | **`UNRESOLVED`.** These are representable in principle — the vocabulary exists or is enumerable — and are unresolved only because this PR does not model them. **Not prose-bound.** |
| **(b) genuinely open-ended fictional judgment** | **4** | Burning's *"doused, submerged, or suffocated"*; Help's *"near enough … to assist verbally or physically"*; Hide's *"a sound louder than a whisper"* and *"an enemy finds you"*; Influence's attitude modifier (the source never states it) | **`UNRESOLVED`** pending a per-clause judgement. Some would likely qualify as `contextual_applicability`, but that is an affirmative claim requiring its own showing, not a default |
| **(c) player-authored arbitrary trigger** | **2** | Ready's *"you decide what perceivable circumstance will trigger your Reaction"* and its trigger-time branch | Ready's trigger sentence is **already** an affirmative `PROSE_BOUND` binding under `open_ended_effect` in the actions-1 accounting; the two remaining spans stay `UNRESOLVED` |
| **(d) represented but possibly not executable by an adapter** | **1** | Attack's *"you can use some or all of that movement to move between those attacks"* — ordering against an open feature set | **`UNRESOLVED` as representation.** Executability is CRD Issue 15c's boundary; per ADR-005d Decisions 1 and 11 **no 5d fact is admitted or withheld on the basis of what the adapter can execute**, and nothing here does so |

The material correction: **category (a) is the largest group, not (b).** Line of sight, cover grade, and
obscurement level are printed closed vocabularies, so calling them "unbounded fiction" was wrong. They are
ordinary unmodeled predicates awaiting a later batch's evidence. This correction does not make either batch
acceptable and is not intended to.

---

## 5. Proposed implementation boundary for the schema-2 PR

### 5.1 Files

| File | Change |
|---|---|
| `src/afterworlds/ingestion/mechanical/representation.py` | the §1.1 structural addition; the §1.2 families; the §1.3 extensions; `REPRESENTATION_SCHEMA_VERSION` → `5d-representation-schema-2`; correct the version docstring's acceptance-based stay-at-1 criterion to the merge-based one; extend `fact_target_key` for option-scoped facts |
| `src/afterworlds/ingestion/mechanical/validation.py` | every invariant in §1.1 and §1.2, each failing closed |
| `src/afterworlds/ingestion/mechanical/persistence.py` + one Alembic migration | `rp_mech_components` gains the three component fields; a child table for `ComponentOption` and its facts; `reconstruct_candidate` round-trips both |
| `tests/ingestion/mechanical/test_representation_schema_identity.py` | `EXPECTED_SCHEMA_HASH` |
| `tests/ingestion/mechanical/data/bounded_oracle.json` | the declared hash |
| `tests/ingestion/mechanical/test_conditions_zero_path.py` *(new)* | §5.2 items 3–7 |
| `docs/architecture/known_unknowns.md` | *choices* moves from untouched to discharged; *eligibility* and *sequencing* narrow to their §4(a)/(b) cores |

**Unchanged, and expected to need no edit:** `AcceptedOracle`, `ProjectionCandidate`, `projection_payload`,
`oracle_payload`, `accept_proposal`, the projection header columns, the publication gate, and the
`{version, hash}` declaration shape.

### 5.2 Test categories

1. **Canonical wire-contract identity** — the hash moves exactly once, with the version at `2`; renaming
   any new Python class, and permuting declaration order of any new enum or field, leaves it unmoved;
   changing an admitted vocabulary value or a serialized field moves it.
2. **Serialization** — `Applicability`, `SizeComparison`, and `ComponentOption` render inside the existing
   closed grammar with no `_shape` change; `options` and `any_of` render as `array`; options are
   canonically ordered by `semantic_key` so source order does not reach the hash.
3. **Options rejection** — one option; `facts` and `options` both non-empty; `options_exhaustive` with no
   options; duplicate `semantic_key`; two options with identical canonical facts; and a static assertion
   that `ComponentOption` exposes no options field, so nesting is unrepresentable rather than merely
   rejected.
4. **Validation** — every §1.1/§1.2 invariant, including each `Applicability` kind/field mismatch, both
   `SizeComparison` vacuity forms, `factor >= 2`, `feet` set exactly for `FEET`, and exactly one of
   `amount`/`all_levels` on `CONDITION_LEVEL`.
5. **Round trip** — every new family and extension through `fact_payload` → reconstruction (the generic
   machinery in `test_fact_families.py` covers these once each declares a corpus-grounded exemplar), plus
   component options through persistence → reconstruction → persisted-state digest.
6. **Semantic-honesty canaries** — `ConditionEffectFact(EXHAUSTION, APPLIES)` is not how *"gains 1
   Exhaustion level"* is represented; `SpeedModificationFact(HALVED)` is not how R7c's expenditure is
   represented; `ScalingFact` is not how R6b's ×10 is represented; and R4b/R7c **do** use the pre-existing
   `ConditionEffectKind.REMOVES`.
7. **Regenerated conditions-1 proposal**, against the exact production release, proving:
   * the release binding is **derived** — `build_candidate()` on the committed PDF reproduces
     `package_uuid` `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` and `release_version`
     `5.2.1-corpus.36b786d8-fa2` and the three other derivable values;
   * the **preserved boundary: exactly 16 records and 134 leaves**, unchanged from the accepted accounting;
   * `validate_partition` over all 134 leaves, `validate_reason_codes`, `validate_representation` — **0
     findings**;
   * **0 `UNRESOLVED` spans**;
   * `validate_acceptance` returns no findings — **without calling `accept_proposal`**;
   * actions-1 and hazards-1 regenerate and still carry **11** and **7** unresolved spans, so the PR cannot
     be misread as closing everything.

### 5.3 Explicitly out of scope

Everything in §1.4; any `ROLL_OUTCOME` applicability or other conditional-outcome structure; any duration or
recurrence field; modelling any §4 predicate; `accept_proposal`, `AcceptedInputs`, `oracles/`, publication,
activation, and legacy retirement.

---

## 6. Confirmations

Created: this file and nothing else. Modified: nothing. All proposals, audits, generators, matrices, and
prior checkpoints preserved byte-for-byte. `git status --porcelain src tests` empty. No branch created.
`accept_proposal` never called; no `AcceptedInputs`; `oracles/` still `README.md` only; nothing published or
activated; no legacy authority retired; no database written; PR #129 untouched; no Issue 2b / 15c work
begun; ADR-015b's adjustment-parameter Known Unknown unchanged.
