# CRD Issue 5d — batch `actions-1`, representation schema 7

Checkpoint for the regenerated proposal. Nothing here is accepted, published,
activated, retired, pushed or merged. Branch `feature/issue-5d-actions-1`.

## 1. What this run produced

| Artifact | sha256 |
| --- | --- |
| `issue-5d-actions-1-schema7-PROPOSAL.json` | `e08759e7202793a3fa61b6589f21eb68f1b0fdbb3e39743129918837b2633c03` |
| `issue-5d-actions-1-schema7-audit.json` | `0824439031e895f6e8b2b54788baed1e982fc19e5596a0dbaab85cbf34761c9b` |

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
| real source-prose resolution (byte-exact leaf partitions from the bound PDF) | **yes** |
| structural validation (draft/held shape, component rules, reason codes, schema binding, standalone + merged `validate_representation`, wire round trip, 5→6→7 lift verified element by element) | **yes** |
| consumer projection assertion (`_base_records`, in memory) | **yes** |
| executed comparison on constructed operands (`casting_time_meets` against the published gate) | **yes**, but they are hand-written operands — this generator reads no spell table |
| illustrative counterexample (what an ungated publication *would* have asserted) | **no** — reasoning, named `counterexample`/`illustrative` so it cannot pass for a check |
| stored-threshold reconstruction | **no** — needs a database. The threshold is never persisted and read back. The in-memory wire round trip is the nearest thing that ran and is strictly weaker |
| publication-gate execution | **no** — it runs over a persisted projection during acceptance. Its verdict on this batch is **unknown** here, not favourable |

The schema-6 report printed a publication-gate outcome for the S-1 residue.
With S-1 closed there is no such residue, so no gate result is printed and none
is invented in its place; the gate imports were removed rather than left to
decorate the file.

**Obligations** are no longer reported as a flat "78 discharged", which counted
a clause handed to a supporting-authority span the same as one that entered the
typed vocabulary. Four disjoint buckets, derived from the emitted audit rows:

* accounted for: **78** (weakest claim — the text is inside the partition and
  claimed by some element)
* represented in a typed structure: **60**
* represented as bound prose: **12**
* carried as supporting authority only: **6**
* unresolved: **0** (asserted empty; K2/K3/K4 each asserted typed)

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
