# CRD Issue 5d — H-16 reopened and run through the real provenance gate

**Status: FINDING. Design only.** No production content accepted, no oracle change, no branch beyond
`feature/issue-5d-representation-schema-4`. Run at `4be6c24`.

**Result: the two-sibling-component shape is withdrawn**, and the structural gap that let it validate
is now closed in code. When first run it passed the validator while being dishonest; human rejection of
one instance would have left the gap open, so `_validate_duplicated_fact_authority` now refuses the
whole class. Shape A fails today — see §6. The correct representation is **one `MIXED` component whose whole disjunctive trigger is
affirmative governing prose**, which needs no new structure at all — no H-16 trigger family, no Boolean
predicate, no relationship, no wrapper, and no new provenance rule.

---

## 1. What was run

The candidate was built from the **actual bound corpus** and the **actual leaf**
(`7571f4e8-7845-564a-8e60-7c36c7f2fd97`, Suffocation), cut into real half-open subranges, and put
through `validate_partition` + `validate_reason_codes` + `validate_representation` — the full
representation and provenance gate, not duplicate-fact detection alone.

Source clause:

> *"When a creature runs out of breath or is choking, it gains 1 Exhaustion level at the end of each of
> its turns."*

Real span offsets in that leaf:

| range | text |
|---|---|
| `[147,182)` | `" When a creature runs out of breath"` |
| `[182,197)` | `" or is choking,"` |
| `[147,197)` | the whole trigger, uncut |
| `[197,225)` | `" it gains 1 Exhaustion level"` |
| `[225,258)` | `" at the end of each of its turns."` |

---

## 2. Gate results

Two columns, because the first run is *why* the rule exists and the second is the state that ships.

| Shape | As first run (pre-fix) | Now (§7 rule in place) |
|---|---|---|
| **A** — two sibling components; consequence `PRIMARY` on one, `CONTEXTUAL` on the other | **0 findings** ← the gap | **refused**: `fact a2dfac8bea01c536 is stated once by span c98bc898… but held by sibling components ['accrual_breath','accrual_choking']` |
| **A′** — two sibling components; both facts claim `PRIMARY` on the one consequence span | **refused**: conflicting primary claims | **refused twice**: conflicting primary claims **and** duplicated authority |
| **B** — one `MIXED` component; whole disjunctive trigger as governing prose | **0 findings** | **0 findings** |
| **NEG-1** — fact's primary provenance assigned to trigger-only wording | **refused**: conflicting primary claims **and** `substantive but unclaimed` | unchanged |
| **NEG-2** — consequence span only contextually linked, never claimed | **refused**: `substantive but unclaimed` | unchanged |

Both dishonest-provenance negative controls are caught. Neither primary-by-span uniqueness nor the
provenance-required kinds were weakened to obtain any of these results.

---

## 3. Why Shape A is wrong — the reasoning that became the rule

Three reasons. At the time none of them was visible to the validator, which is the finding; the first
two are now enforced by §7, and the third turned out to be a restatement of a rule that already held.

1. **It publishes a consequence the source states once, twice.** Shape A emits two
   `ConditionLevelFact(EXHAUSTION, GAIN, 1)` facts. A deterministic consumer reading the typed surface
   sees two accrual claims where the source made one. ADR-005d Decision 5 is explicit that *"an
   all-prose projection and a duplicated-fact projection must both fail"*.
2. **The `CONTEXTUAL` demotion is false about provenance.** Span `[197,225)` is the *sole and stating*
   source of `accrual_choking`'s fact. Recording it as contextual says that span *supports* the fact
   when in truth it *states* it. That is choosing a role to satisfy the validator, which is exactly
   what this exercise was told not to do.
3. **The cadence looked like the same defect** — `[225,258)` governs both arms equally while only one
   component may claim it `PRIMARY`. On inspection this is not a separate defect and not a general
   prohibition: it is the pre-existing primary-by-span rule doing its job. See the correction in §5.

Shape A′ shows the honest version of Shape A is *structurally impossible*: the gate refuses two primary
claims on one span, and manufacturing a second consequence span to get around it would be inventing
source text.

---

## 4. Shape B — the accepted representation

One component. The consequence is stated once. The source's **OR survives unreduced**, because it is
carried as prose rather than approximated by a typed predicate.

| target | key | role | span |
|---|---|---|---|
| `record` | `hazard.suffocation` | `contextual` | `[0,20)` `"Suffocation [Hazard]"` |
| `prose_binding` | `hazard.suffocation / suffocation_accrual` | **`primary`** | `[147,197)` `" When a creature runs out of breath or is choking,"` |
| `fact` | `hazard.suffocation / suffocation_accrual / a2dfac8bea01c536` | **`primary`** | `[197,225)` `" it gains 1 Exhaustion level"` |
| `component` | `hazard.suffocation / suffocation_accrual` | **`primary`** | `[225,258)` `" at the end of each of its turns."` |

```
handling      : MIXED / contextual_applicability
facts         : (ConditionLevelFact,)   ← stated ONCE
applies_when  : None
recurs        : Recurrence(END_OF_TURN, whose=SUBJECT)
```

Every substantive span has exactly one honest `PRIMARY` claimant, and each claimant is the element the
span actually states.

**Why prose is affirmative here and not a backlog state.** The predicate as a whole is not crisp. One
arm (*"runs out of breath"* — the H-15 breath duration expiring) is typed-able; the other (*"is
choking"*) is fiction the SRD never defines mechanically. Reducing `A or B` to typed `A` loses `B`;
carrying both as scopes asserts `A and B`, which is false, because component, option and fact-qualifier
scopes **compose conjunctively** by design. So the disjunction is irreducible under schema 4 and
`contextual_applicability` — *"whether the rule applies depends on fiction the projection cannot
enumerate"* — is the accurate closed reason. That is ADR-005d Decision 2's `MIXED`, correctly applied.

**Cost, stated plainly:** the typed breath-expiry arm is not separately typed. That is a real loss of
structure and it is the price of not falsifying the source. It is not hidden: the prose binding carries
the whole trigger, so nothing about the rule is missing from the projection.

---

## 5. A defect this run surfaced in H-1

**A recurrence has no provenance target kind.** `ProvenanceTargetKind` has no `RECURRENCE` member, so a
span stating a cadence cannot be claimed by the recurrence itself. The first gate run reported
`" at the end of each of its turns."` as **`substantive but unclaimed`**.

The resolution needs no new target kind: the recurrence is a property of its component, exactly as
`applies_when` is, so the **owning component** is the honest `PRIMARY` claimant of the cadence span.
That is symmetric with how an applicability's span is already claimed, and it is what Shape B does.

**Correction — the earlier universal claim is withdrawn.** A previous draft of this note said "two
components can never share one cadence span". That is not what was demonstrated and it is not true in
general: `primary_by_span` admits any number of `CONTEXTUAL` claims on one span, so two components may
legitimately both be *linked* to a cadence clause. What was actually demonstrated is narrower and is
about **duplicated fact authority**, not about cadence:

> Two different components of one record may not hold facts with the same content-derived key when both
> draw that fact from the **same substantive span**.

That is the rule now enforced by `_validate_duplicated_fact_authority`, and it is what refuses Shape A.
The cadence observation reduces to a consequence of the pre-existing provenance rule — only one element
may be the `PRIMARY` claimant of a given span — which was already enforced and needed no change.

---

## 6. Dispositions

* **H-16: typed family not admitted; obligation closed through `MIXED` governing prose.** The
  obligation the source states is *represented*, not deferred — the trigger is carried in full as
  affirmative governing prose under `contextual_applicability`, so nothing about the rule is missing
  from the projection. What is not admitted is a typed trigger-set vocabulary, because half its operand
  (*"is choking"*) is fiction the SRD never defines mechanically. "Rejected" alone was the wrong word:
  it described the vocabulary decision and left the obligation looking unmet.
* **The two-sibling-component replacement: WITHDRAWN**, on the grounds in §3. It duplicates a
  consequence and misstates provenance roles.
* **Shape B: ADOPTED** for `hazards-1` authoring in PR B. It requires **no schema addition**.
* **H-1: amended** — the owning component is the `PRIMARY` claimant of its recurrence span; no
  `ProvenanceTargetKind.RECURRENCE` is minted.

No Boolean predicate language, synthetic wrapper, relationship, or new provenance rule was added, and
no stop condition was crossed.


---

## 7. The validation gap, closed

Human rejection of this instance would not have closed the structural hole: any future batch could
author the same shape and validate clean. `validation._validate_duplicated_fact_authority` now refuses
it as a class.

**The rule.** Two *different* components of one record may not hold facts with the same content-derived
key when both draw that fact from the **same substantive span**. All three conditions are required:

| Condition | Why it is load-bearing |
|---|---|
| different components | two options of one component are mutually exclusive alternatives, not a repeat; option facts resolve to their owning component so a choice is never reported |
| equivalent fact | keyed by `fact_key`, the same content-derived key persistence and override targeting use — not family equality |
| shared substantive span | the same mechanic stated by two genuinely different rules is ordinary authority, so equivalent facts from *different* spans are left alone |

**Deliberately not** global cross-component fact uniqueness — the same mechanic may legitimately be
stated by separate rules. **Deliberately not** derived by reading positions out of a provenance target
key: the fact sites are built by walking the declared components, so a key's shape can change without
silently changing what the rule means. **The provenance role is not consulted at all** — the duplication
is the same defect whichever label it wears, and the `PRIMARY`/`CONTEXTUAL` labelling was the mechanism
that hid it.

Six durable tests in `tests/ingestion/mechanical/test_duplicated_fact_authority.py`: three shapes that
must now fail (Shape A, the same duplication with both edges `PRIMARY`, and Shape A′ still failing
for conflicting primary claims *as well as* duplication), and three that must keep passing (Shape B,
one mechanic stated by two different rules, and mutually exclusive options).

---

## 8. Focused sibling audit

**Defect family:** *a uniqueness check scoped to one container cannot see the same duplication across
sibling containers.*

**Trigger:** the Shape A finding — `_validate_components` compares facts per scope, so two sibling
components each holding an equivalent fact are two clean scopes.

Every uniqueness check in the representation layer inspected against that family:

| Check | Scope | Cross-sibling analogue | Disposition |
|---|---|---|---|
| duplicate record semantic key | draft | records are the top scope; no sibling container above them | already safe |
| duplicate component semantic key | draft, keyed `(record, semantic_key)` | already draft-wide, not per record | already safe |
| **duplicate typed fact** | **component's own list, and each option's list** | **two sibling components holding one fact from one span** | **patched** — §7 |
| `option_set_violations`: two options state the same typed facts | one component's option set | two components with identical fact sets — same family as the row above | **patched by the same rule**, when they share a span |
| duplicate provenance edge | draft, exact `(kind, key, span, role)` | none: the tuple is already global | already safe |
| conflicting primary claims per span | draft, per span | none: already global, and it is what refuses Shape A′ | already safe |
| ambiguous reference | one committed scope, by source wording | cross-scope repetition is two references by design | already safe |

Two adjacent structures checked and deliberately **not** patched:

* **prose bindings.** Two sibling components may bind the same chunk range — a clause that governs two
  mechanics is real, and a prose binding is governing text rather than typed authority, so citing it
  twice does not publish a mechanic twice. Out of scope.
* **references and relationships.** A reference is a *resolution* and a relationship is an edge; neither
  asserts a mechanic, so neither can duplicate fact authority. Already safe.

**Dispositions: 1 patched, 6 already safe, 2 out of scope.** No check was loosened, and no new global
uniqueness rule was introduced.

---

## 9. Sibling-component recommendation — WITHDRAWN

**Superseded by the merge-blocking finding the Owner accepted, and by `f2111ca`.**

An earlier draft of this note recommended Shape A — two sibling components, one holding the consequence
as `PRIMARY` and the other holding an equivalent fact demoted to `CONTEXTUAL` — as an acceptable
representation for H-16's heterogeneous trigger. That recommendation is withdrawn in full, on two
grounds, and it is recorded here rather than deleted so the reasoning that was rejected stays legible.

**Ground 1 — it is dishonest about the source.** The source states one consequence once. Shape A
publishes it twice, and the `CONTEXTUAL` demotion falsely describes the span that *states* the fact as
merely supporting it. Choosing one duplicated consequence as primary and the other as contextual to
satisfy the validator is not a representation decision; it is picking whichever assignment the validator
happens to accept.

**Ground 2 — ADR-005d Decision 5 forbids it, and the validator did not.** "A duplicated-fact projection
must fail." Shape A is one, and `validate_representation` reported zero findings against it. That gap is
the merge-blocking finding, and it is closed in §7 by the narrowest general rule: two *different*
components of one record may not hold facts with the same `fact_key` when both draw it from the **same
substantive span**. Fact equivalence plus shared source provenance — never fact equality alone, never
parsed target-key positions, and deliberately not global cross-component fact uniqueness.

**What was adopted instead.** Shape B: one `MIXED` component whose whole disjunctive trigger is carried
as governing prose, with the consequence stated once as a typed fact beneath it. It requires no schema
addition, no Boolean predicate language, no synthetic wrapper, no new relationship, and no new
provenance rule, and it does not weaken primary-by-span uniqueness or provenance-required kinds.

**H-16 disposition, final:** *typed family not admitted; obligation closed through MIXED governing
prose.* It is the one item of the sixteen that closes without a schema addition.

**Reference ownership is the same defect family, one element kind over.** H-8 admits a record-owned
reference, which made a second duplication shape reachable: a record citing something both directly and
through one of its own components. Record ownership *means* no component states it, so the pair
contradicts its own justification and publishes one citation twice. Refused in `validate_representation`
alongside the sibling-fact rule, and recorded in ADR-005d Decision 5 as amended. Two different
*components* citing the same wording stay legal — each is its own claim with its own provenance edge —
so the reference rule is scoped to the record-owned-versus-component-owned contradiction and no wider.
