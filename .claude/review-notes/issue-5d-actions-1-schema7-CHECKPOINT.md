# CRD Issue 5d — batch `actions-1`, representation schema 7

Checkpoint for the regenerated proposal. Nothing here is accepted, published,
activated, retired, pushed or merged. Branch `feature/issue-5d-actions-1`.

## 1. What this run produced

| Artifact | sha256 |
| --- | --- |
| `issue-5d-actions-1-schema7-PROPOSAL.json` | `e08759e7202793a3fa61b6589f21eb68f1b0fdbb3e39743129918837b2633c03` |
| `issue-5d-actions-1-schema7-audit.json` | `a087c17e90271a4a94582cce117b4a3fe521c04559485d6ad85aa6a8e1bbeb72` |

* Proposal identity `62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c`
  — not pinned in advance; this is a fresh proposal, and the value is reported
  for review rather than asserted against a number chosen beforehand. It is
  asserted **different** from the superseded schema-1 identity
  `ff30c25a…41bf0`.
* Schema `5d-representation-schema-7` /
  `80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d` — the pin
  committed at `05800fc` and unchanged by the duration correction at `db2e612`.
* Both artifacts are LF on every platform (asserted: no CR byte). Determinism
  is a parent-vs-child byte comparison of the **final** files plus an identity
  match, not a self-report: `deterministic True`.
* Generator: `issue-5d-actions-1-schema7-PROPOSAL-generator.py`, a patched copy
  of the reviewed schema-6 generator. Every schema-6 judgment it does not
  mention is preserved by construction, not re-derived.

## 2. Counts

records 13 · represented leaves 92 (+2 enumerated 5c policy exclusions = 94
container leaves) · spans 182 = **84 substantive + 98 supporting authority + 0
non-mechanical + 0 unresolved** · components 37 (18 structured, 10 mixed, 9
prose-bound) · options 10 across 4 components · facts 48 (35 component-grain,
13 option-grain) · fact qualifiers 4 · prose bindings 27 (7 option-grain) ·
references 17 (2 record-owned) · provenance edges 199 (17 contextual extras) ·
obligations 78.

## 3. The one substantive change: S-1 closed

Schema stop **S-1** — Magic K2/K3/K4, leaf `b196aa1b` (SRD 5.2.1 p185) — is
recorded `closed at representation schema 7`, not deleted.

* **K2** the recurring Magic action, **K3** the Concentration duty: held by
  `action.magic/magic_long_casting`.
* **K4** the spell's failure and the unspent slot: held by
  `action.magic/magic_concentration_break`.
* Both components carry the **same** `applies_when` —
  `spell_casting_time at_least 1 minute`, negated `False`.
* K4's two facts each carry a `FactQualifier` on `concentration_broken`, so the
  break is a *further* condition inside the printed gate. Read outward:
  a long casting, whose Concentration is broken.

An applicability and not a fact, because K2 and K4 are two components of one
record inside one printed condition: a gate carried as a fact and restated on
both is refused by `_validate_duplicated_fact_authority`, while a repeated
applicability is admitted. That asymmetry is the whole reason for the choice.
A qualifier and not a second `applies_when`, because a component carries
exactly one — and a component stating only `concentration_broken` would have
reached every broken Concentration in the game.

Asserted through `_base_records`, reading values **off the projection
objects**: the three component keys, both gate dicts, the exact fact types
inside each gate, both qualifier kinds, zero break facts without a qualifier,
zero long-casting facts with one, and **zero** long-casting fact types
published outside the gate.

### Semantic diff from the reviewed schema-6 proposal

Computed from both payloads, not narrated; the schema-6 payload is read *after*
this proposal's identity is minted, so it feeds no authored value.

* components **+2**, both `action.magic/…`; **−0**
* facts **+4**: `recurring_action_requirement`, `sustained_state_requirement`,
  `effect_termination`, `resource_expenditure`; **−0**
* gates **+3**: two `applies_when=spell_casting_time`, one
  `qualifier=effect_state`; **−0**
* spans: `substantive 78 → 84`, `supporting_authority 98 → 98`,
  `unresolved 3 → 0`
* references `17 → 17`; the five unresolved targets are the same five

Asserted, not just reported: every added or removed component and fact must
start with `action.magic/`. A silent change anywhere else fails the run.

## 4. What is still true, and stays true

**Not publishable.** Five source-authored citations point at records no
accepted batch defines: `glossary.speed`, `glossary.concentration`,
`attitude.friendly`, `attitude.hostile`, `attitude.indifferent`. Both the
standalone and the merged validation columns report exactly these five,
asserted by **set equality on target keys**, not by count. They are listed in
`publishability.blocked_on` verbatim.

**Closing S-1 conferred no readiness.** A category batch is not a corpus;
acceptance is a separate Owner step that has not happened; the publication gate
was never executed by this run; general casting-time eligibility remains
deferred with exactly one `SPELL_CASTING_TIME` site in one record as its
evidence — the weakest closure evidence `known_unknowns.md` admits, asserted to
be exactly those two `action.magic` components.

**Preserved unchanged:** Dash's single allowance and standalone duration;
Magic/Ready/Utilize typed eligibility (admitted pairs exactly
`{(spell, action), (object, action)}`); Help's two option-scoped
qualifications; Influence's hesitancy binding; Attack L-1; the `R-help-reason`
residue; all thirteen judgment changes; the frozen conditions-1/hazards-1
prior (content sha `0925d796…73f7`, blob `6e65533f…b59a`, unchanged before and
after); the live accepted oracle (sentinel only, unchanged); all four retained
schema-6 artifacts (hash-guarded).

## 5. Truthfulness corrections made to the generator's reporting

The previous run let five different things wear the word "proof". The audit now
carries an `evidence_classes` section that separates them and says plainly
which did **not** run:

| Class | Executed here |
| --- | --- |
| source extraction and partition reconstruction (byte-exact leaf partitions from the bound PDF) | **yes** |
| structural validation (draft/held shape, component rules, reason codes, schema binding, standalone + merged `validate_representation`, wire round trip, 5→6→7 lift verified element by element) | **yes** |
| consumer projection assertion (`_base_records`, in memory) | **yes** |
| consumer prose resolution (which arm of Help a binding governs; Influence's hesitancy extent) | **partly** — the projection's `SourceProse` entries and span ids are read back, but the text is this run's own span map. Resolution through the GameMaster view, which fetches the authoritative `RuleChunk` by id from storage, did not run: the binding's **scope** is evidenced, its **delivered text** is not |
| executed comparison on constructed operands (`casting_time_meets` against the published gate) | **yes**, but they are hand-written operands — this generator reads no spell table |
| illustrative counterexample (what an ungated publication *would* have asserted) | **no** — reasoning, named `counterexample`/`illustrative` so it cannot pass for a check |
| stored-threshold reconstruction | **no** — needs a database. The threshold is never persisted and read back. The in-memory wire round trip is the nearest thing that ran and is strictly weaker |
| acceptance | **no** — an Owner step that merges a proposal into accepted authority and records the decision. This run reproduces the *merge* in memory to validate shape; it accepts nothing, writes nothing, records nothing |
| publication-gate execution | **no** — a separate check, downstream of acceptance, over a **persisted** projection. Nothing is persisted here, so its verdict on this batch is **unknown**, not favourable |

The schema-6 report printed a publication-gate outcome for the S-1 residue.
With S-1 closed there is no such residue, so no gate result is printed and none
is invented in its place; the gate imports were removed rather than left to
decorate the file.

**Obligations** are no longer reported as a flat "78 discharged", which counted
a clause handed to a supporting-authority span the same as one that entered the
typed vocabulary. Five disjoint buckets, derived from the emitted audit rows:

* accounted for: **78** (weakest claim — the text is inside the partition and
  claimed by some element; not a representation claim)
* represented in a typed structure: **36**
* represented by typed structure **and** bound prose: **8**
* represented as bound prose: **17**
* carried as supporting authority only: **17**
* unresolved: **0** (asserted empty)

The basis is **carriage**, not ownership. An earlier cut keyed on
`claimant_kind`, which answers *which element owns this text* — and
`claimant_kind == "component"` covers both `A` segments, where a component's own
typed structure is the mechanic, and `C` segments, which are supporting text a
component merely owns. That let a clause inherit a sibling's facts and reported
60/12/6. Classification now keys on the **emission kind**: `F`/`A`/`Q` typed,
`P` prose, `R`/`C`/`X` supporting, `U` unresolved. `A` is admitted as typed only
because it means the component itself holds an `Applicability` or an option set,
which the run asserts for **every** `A` row.

Four cases are asserted rather than described, and they are the ones the old
basis got wrong:

| Obligation | Rows | Bucket |
| --- | --- | --- |
| **N2** `action.study/study_areas` | 1 × `P`, 13 × `C` | prose only — the component is `PROSE_BOUND` with no fact and no option; the table is governing guidance plus supporting examples |
| **O1** `action.utilize/utilize_action` | 1 × `C` | supporting only — the component's two facts state **O2**, and O1 does not acquire them by sharing a component |
| **N1**, **B7** | `F`+`P` / `C`+`P`+`F` | both — a typed fact states part, a prose binding carries the rest |
| **K2**, **K3**, **K4** `action.magic` | `A`+`F` / `F` / `Q`+`F`+`F` | typed — K2's `A` span is `magic_long_casting`'s own casting-time gate |

**O2** is asserted typed alongside O1 to show the two clauses of the shared
component separate correctly, and no obligation reaches a `represented_*` bucket
on supporting text alone.

`publishability` also gained an explicit `state: "proposed"` and a
`what_closing_s_1_did_not_do` field, and `review_disposition` now separates
`open_schema_stops: []` from `closed_schema_stops: ["S-1"]` and names the
deferred eligibility question.

## 6. Gates

See the commit message for the exact observed results.

## 7. Not done, deliberately

No acceptance, publication, activation, retirement, push or merge. `#137` not
closed. Tables, settled classifications, a general rules engine and downstream
adapter ownership are not reopened. General casting-time eligibility remains an
open Known Unknown, narrowed rather than discharged.
