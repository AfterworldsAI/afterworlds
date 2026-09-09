# CRD Issue 5d — batch `actions-1`, representation schema 6

Proposal preparation checkpoint, reconciled after the source-fidelity remediation
of the proposal reviewed at `e2c6c63`. **Nothing here is accepted, published,
activated, retired or merged.** `accept_proposal` was not called. The frozen review
prior and the live accepted oracle are unchanged; both were verified before and
after the run.

Branch `feature/issue-5d-actions-1`. Remediation base `e2c6c63`.

## 1. Artifacts

| Artifact | SHA-256 |
| --- | --- |
| `.claude/review-notes/issue-5d-actions-1-schema6-PROPOSAL.json` | `d7e8fcd240972651da238b887ede3f64803314f0c9077c580c6a05ab39b9fc89` |
| `.claude/review-notes/issue-5d-actions-1-schema6-audit.json` | `7236ad2eebf0838753566410952f36b65c715f13d079fd773fd33005c6ab2dac` |
| `.claude/review-notes/issue-5d-actions-1-schema6-PROPOSAL-generator.py` | the executable derivation of both |

Proposal identity: **`debd95ace5ec6ef7ecadfc511e9859764a8bed943e9ed88a4db9d469ed7365f2`**
(the reviewed predecessor was `b7420dae2deea72d75991615cad397881da4929c0d80266a8a20737a8fb660f2`;
the remediation changes the represented meaning, so the identity necessarily moves).

The identity is **not pinned** in the generator. Pinning it would make the script
assert its own output rather than derive it; the generator asserts only that the
identity differs from the superseded schema-1 proposal
`ff30c25a568836b3e44b60b692a713aa8da90cca3ffc8326fbc8adc0ff541bf0`, which it does.

Both files are LF-only (asserted: no CR byte). Regeneration reproducibility is
proved inside the run: the parent re-executes itself in a separate interpreter
under `ACTIONS6_RERUN=1` and compares the final bytes of both artifacts, and the
child's identity line must appear in its stdout. `deterministic True`.

The superseded schema-1 payload was **not** an input. It was neither imported,
edited, translated, restamped, cloned nor read as generator input; its identity is
recorded as historical evidence only. Every span, cut and text in this proposal is
re-derived from the bound source through `build_candidate`.

## 2. Source binding — six values verified live

| Value | |
| --- | --- |
| package UUID | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
| release | `5.2.1-corpus.36b786d8-fa2` |
| authoritative source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| transform/config hash | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` |
| bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` |
| persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` |

The first five are re-derived from the PDF by the run and asserted. The sixth is
carried from the 5c release record; it is not re-derivable from the candidate and
is recorded as a carried value, not as a computed one.

Schema pin: `5d-representation-schema-6` /
`0e4b4378bf1409ed3ffbbec61a279430689ce4a0d3b70b1b3e9d886f66ae20b7`, asserted
against `representation_schema_hash()` at run time — **unchanged by the
remediation.** No schema change and no re-pin was made.
Policy: `5d-semantic-policy-1` /
`e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454`.

## 3. The action boundary, in full

13 records · **94** container leaves · **92** represented · **2** policy exclusions.

The two exclusions are the running header/footer leaves, not the headings:

- `056d861c…` p187 `System Reference Document 5.2.1 187` (Ready)
- `891e92d8…` p183 `System Reference Document 5.2.1 183` (Help)

The 13 heading leaves **are** represented, each carrying whole-leaf supporting
authority, exactly as in the accepted hazards-1 batch. Each entry's leaf set is
reconstructed byte-for-byte from its span partition and asserted; no leaf is
partially claimed and none is silently dropped.

Records: `glossary.action`, `action.attack`, `action.dash`, `action.disengage`,
`action.dodge`, `action.help`, `action.hide`, `action.influence`, `action.magic`,
`action.ready`, `action.search`, `action.study`, `action.utilize` — all
`GLOSSARY_RULE`, the twelve named actions parented to the umbrella.

Emitted: **179 spans** (78 substantive, 98 supporting authority, 0 non-mechanical,
**3 unresolved**) · **35 components** · **44 facts** (31 component-grain + 13
option-grain) · **27 prose bindings** (7 option-grain) · **17 references**
(2 record-owned) · **191 provenance edges** (15 contextual extras) ·
0 relationships.

Movement against the reviewed predecessor (177 / 37 / 47 / 24 / 191 / 14):

| | before | after | why |
| --- | --- | --- | --- |
| spans | 177 | 179 | +3 Help/Influence qualification spans, +1 Magic K1 eligibility span, −2 net from Magic's long-casting leaf being cut in three instead of five |
| components | 37 | 35 | `dash_speed_choice` folded into `dash_movement` (+`dash_duration`); `magic_long_casting` and `magic_concentration_break` not authored |
| facts | 47 | 44 | −1 duplicated Dash `MovementAllowanceFact`; −2 Magic long-casting facts; +1 `ActivationCostEligibilityFact(spell, action)` shared by Magic and Ready |
| prose bindings | 24 | 27 | the three qualifications that had no governing prose |
| unresolved spans | 0 | 3 | the schema stop, §7 |

## 4. Obligation closure

78 distinct obligation IDs from `issue-5d-actions-1-obligation-coordinates.json`,
**all discharged, 0 open, 0 unknown**. The I-series runs I1–I7, I9, I10 — there is
no I8 in the source ledger, and the generator asserts the count is 78 so a silent
renumbering would fail the run.

Discharge is not the same as representation. `OBLIGATION_CLOSURE` records each
obligation's span dispositions, so K2, K3 and K4 read `unresolved` there rather
than being counted as covered. Full clause coverage is reported as what it is.

## 5. Substantive judgment changes from discovery

Stated as reasons. The discovery ledger was a first pass over the source and is
evidence, not a target; its counts are not treated as quotas. JC-1…JC-9 are
unchanged from the reviewed proposal and are restated in the audit; JC-10…JC-13 are
the remediation.

- **JC-1 — reference `source_text` is the bare name.**
- **JC-2 — the Influence/Search/Study table cells are supporting authority.** The
  Owner's clarification that suggested skill/ability tables are exemplars and
  guidance; the governing sentences J7, J8, M3, N2 keep their bindings. Not
  reopened here.
- **JC-3 — J10 is prose-bound,** not a typed ROLL_OUTCOME gate.
- **JC-4 — B2 is supporting authority, not a cross-reference.**
- **JC-5 — Help carries one reason for both arms** (residue R-help-reason, closed
  without change).
- **JC-6 — Dodge is three components, including a standalone duration.**
- **JC-7 — Study splits into `study_check` and `study_areas`.**
- **JC-8 — Utilize is fully STRUCTURED.**
- **JC-9 — the 13 headings are represented, not policy-excluded.**

### JC-10 — Dash is one allowance whose basis is chosen, plus its own duration

Before, `dash_movement` granted an `OWN_SPEED` allowance outright *and*
`dash_speed_choice` separately offered `OWN_SPEED` / `OWN_SPECIAL_SPEED`, so the
consumer view carried two movement allowances for one Dash. The source says the
opposite: "you can use that speed **instead of** your Speed when you take this
action" is a replacement. One allowance is measured per Dash, and the source only
says which speed measures it.

Now `dash_movement` holds the two bases as the two arms of one choice and no facts
of its own, and `dash_duration` holds the single `END_OF_TURN` duration. The
duration stands alone for the reason JC-6 gives: a component holds either facts or
options, never both, so the only alternative was to repeat the duration inside both
arms — a composition that validates under schema 6 but publishes two durations for
one allowance, and reads as reviewer-convenient rather than as the printed rule.

Provenance: D1 ("you gain extra movement") states the allowance before either basis
is named, so the owning component claims it PRIMARY and both option facts take
CONTEXTUAL edges there — the same shape L-1 uses for Attack. D2 grounds the
standard arm, D5 the special arm, D6 the choice itself, D3 the duration.

### JC-11 — Magic K1 and Ready L8 hold SPELL activation-cost eligibility

ADR-005d decides this in terms: **eligibility is substantive authority, not
supporting prose**, because "a spell must have a casting time of an action" states
*which spells the mechanic reaches* over a printed, enumerable field. The
`ActivationCostEligibilityFact` docstring names exactly three instances — `Magic`
p185, `Ready` p187, `Utilize` p191. Utilize O2 was already typed (JC-8); Magic K1
carried only `ActionEconomyFact(action)` and Ready L8 was supporting authority, so
the consumer view admitted **every** spell for both.

Both now hold `ActivationCostEligibilityFact(spell, action)`. K1 is cut in three —
the action's own cost, the eligibility limit, and the open-ended feature/magic-item
clause — instead of one span claimed by the cost fact alone. The same fact in two
records is admissible: `_validate_duplicated_fact_authority` refuses an equivalent
fact held by two components of *one* record, and these are two.

### JC-12 — Help's two narrowing clauses and Influence's hesitancy gate survive as governing prose

"with the chosen skill or tool", "against that enemy" and "that it is hesitant to
do" were each fully *covered* by a span whose claimant did not *state* them. Full
clause coverage is not full clause representation.

Each is now its own span, PRIMARY by a prose binding at exactly its clause — two at
option scope on `help_choice`, one on `influence_check`. None is a vocabulary gap
dressed as irreducibility: `AdvantageFact` enumerates neither a proficiency nor a
target because which proficiency was chosen and which enemy was distracted are
facts of the fiction, and J2 hands the hesitancy determination to the GM outright.
`contextual_applicability` and `gamemaster_latitude` are literally true of them,
and both were already the owning component's single reason, so no reason code was
invented and R-help-reason is unchanged.

### JC-13 — Magic K2, K3 and K4 are UNRESOLVED, and hold no components

See §7. `magic_long_casting` and `magic_concentration_break` are not authored at
all, so `action.magic` publishes `magic_activation` only.

## 6. Disclosed limits and residue

**L-1 — `action.attack/attack_equipment_change`, the equipment cross product.**
Closed without changes, as instructed. `EquipmentChangeFact` carries change and
timing in one fact while the source states the two axes in two separate sentences,
so the option set is the cross product and no single span states any one of the
four combinations. Accounted for by claiming each axis sentence PRIMARY by the
owning component and giving each of the four option facts a CONTEXTUAL edge on both
axis spans. Not a stop: the cross product is entailed by the two sentences read
together.

**R-help-reason — `action.help/help_choice`.** Closed without changes, as
instructed. H5 would take `gamemaster_latitude` on its own; the component carries
`contextual_applicability`, which both other bindings need. The two alternatives
were rejected on the merits: demoting H5 to supporting authority would be false (it
is substantive), and a sibling PROSE_BOUND component would falsely claim to govern
both arms, since no `ApplicabilityKind` can scope a component to one arm of a
choice. `contextual_applicability` is true of H5 and only less specific — a
coarsening of a label, not a false statement about the rule. The two bindings added
by JC-12 sit under this same reason and do not disturb it.

## 7. Schema stop S-1 — Magic's long-casting gate

**Where.** `action.magic`, leaf `b196aa1b` (SRD 5.2.1 p185), obligations K2/K3/K4.

**Clause.** *"If you cast a spell that has a casting time of 1 minute or longer,
you must take the Magic action on each turn of that casting, and you must maintain
Concentration while you do so. If your Concentration is broken, the spell fails,
but you don't expend a spell slot."*

**What cannot be expressed.** The qualification "a casting time of 1 minute or
longer" — a comparison against the **elapsed-time arm** of a spell's printed
casting time. The three mechanics it governs are all typed already
(`RecurringActionRequirementFact`, `SustainedStateRequirementFact`,
`EffectTerminationFact`, `ResourceExpenditureFact`). Only the gate has no shape.

**Attempted admissible shapes.**

1. `ActivationCostEligibilityFact(subject=SPELL, cost=…)` — `cost` is `ActionCost`
   (action · bonus_action · reaction · legendary_action · none · special). No member
   denotes "1 minute or longer", and the fact has no arm for `SpellCastingTime`'s
   `amount`/`unit` pair at all. This is the fact that carries the sibling clause in
   K1 and L8, which is exactly why its ceiling is the right place to look: it ranges
   over the cost arm only.
2. `Applicability(kind=ELAPSED_DURATION, value=1, unit=MINUTE)` — **false**, not
   merely lossy. `ELAPSED_DURATION` is about time that has passed in play. A spell's
   stated casting time is a printed property of the spell, and the gate reads it
   before any time elapses: a 1-minute casting qualifies at the instant it begins.
3. `Applicability(kind=QUANTITY_THRESHOLD, quantity=…)` — `TrackedQuantity` is
   speed · condition_level · weight. Casting time is not among them, and
   `Applicability` is deliberately not a predicate language: no operator, no
   nesting, no way to build a third predicate from two of these.
4. A MIXED component holding the three facts plus a prose binding carrying the gate
   under an irreducibility reason — **refused**. An irreducibility reason is an
   affirmative claim that the clause cannot be reduced. This clause is determinate,
   and the schema itself enumerates the field it ranges over (`SpellCastingTime`
   carries an `amount`/`unit` arm). This would record a vocabulary gap as
   irreducibility, and the facts would still publish ungated beside it.

**Missing capability.** An eligibility fact — or an `ApplicabilityKind` — ranging
over the **elapsed-time arm** of `SpellCastingTime` with a comparison operator: the
exact analogue of `ActivationCostEligibilityFact` for `amount`/`unit` rather than
`cost`. Something of the shape `(subject=SPELL, at_least=(1, MINUTE))`. Nothing
weaker suffices: the clause is a threshold ("or longer"), not an equality, so an
enumerated casting-time member would not carry it either.

**Treatment taken instead.** K2, K3 and K4 are classified `UNRESOLVED`. The text is
read and its extents are recorded, no element claims it, and no component of
`action.magic` holds the facts it governs. This is what
`SemanticDisposition.UNRESOLVED` is for — an honest "cannot classify safely yet"
that blocks publication — and it is distinct from a missing span, which would mean
nobody looked.

**What it costs.** `action.magic`'s authority stops at K1. A consumer asking what a
1-minute casting requires gets nothing from this batch rather than something wrong.

**Not done here.** The schema and its pin are unchanged, the accepted prior is
unchanged, and no ruling is made about what the printed rules mean. Widening the
union is an Owner decision and a schema-7 question.

## 8. Consumer-boundary proofs

Span tallies are not the contract. Every proof below runs against
`services/rules_authority/application.py::_base_records` applied to the merged
candidate (accepted prior + this batch), in memory — no acceptance, no publication,
no persistence — and each is asserted in the generator, so a regression fails the
run.

| Proof | Asserted |
| --- | --- |
| **Dash, one allowance** | `dash_movement` holds 0 facts outside the choice; arms are exactly `standard_speed` → `own_speed` and `special_speed` → `own_special_speed`; **movement allowances reachable in one Dash = 1**; `dash_duration` holds exactly one `EffectDurationFact`; 0 duration facts inside either arm; 0 movement allowances anywhere else in `action.dash` |
| *counterexample* | Taking Dash once selects one arm, and no third `MovementAllowanceFact` exists in the record — so no reading grants both a Speed allowance and a special-speed allowance for one Dash. Exclusivity is what the option set *means* (`EffectiveOption`) |
| **Eligibility, eligible vs ineligible** | holders are exactly `action.magic/magic_activation`, `action.ready/ready_spell`, `action.utilize/utilize_action`; admitted pairs are exactly `{(spell, action), (object, action)}` |
| *counterexample* | a spell printed with a Bonus Action, Reaction, or 1-minute casting time matches no eligibility fact this batch publishes, so neither Magic nor Ready reaches it. Before the remediation the view admitted every spell |
| **Help, qualifying vs unrelated roll** | each arm's governing prose ends at its own qualification — `…with the chosen skill or tool.` and `…against that enemy.`; `AdvantageFact` has no `proficiency` field and no `target` field |
| *counterexample* | on the typed facts alone, an unrelated next roll (a different skill, an attack on a different enemy) would read as benefiting. The qualifying roll is distinguished only by the governing prose, which is why both phrases are carried at their own extents and at arm scope |
| **Influence, the condition on the check** | `influence_check`'s governing prose includes the extent ending `…hesitant to do,` |
| *counterexample* | `AbilityCheckFact` states which check and at what DC, never whether one is called for. Willing and Unwilling monsters need no check at all (J3, J4), so publishing it ungated would require a roll the source does not |
| **Magic, long casting** | `action.magic` publishes `magic_activation` only; none of `RecurringActionRequirementFact`, `SustainedStateRequirementFact`, `EffectTerminationFact`, `ResourceExpenditureFact` appears anywhere in the record; K2/K3/K4 resolve to exactly 3 spans, all `unresolved`; `publication._outcome_for` over those three `UNRESOLVED_RESIDUE` failures returns `PublicationOutcome.UNRESOLVED`, and the failing span ids are exactly those three |
| *counterexample* | published ungated, the facts would require a Magic action on every turn of every casting, Concentration for every Magic action, and would speak about a broken Concentration for spells that never had a casting to break — each false of the Action-casting-time spells K1 reaches |

## 9. Bounded sibling dispositions

Two review rounds hit the same two families, so the siblings were swept rather than
the two named instances patched. Full detail is in the audit under
`sibling_dispositions`.

**Family A — one grant published twice by two components of one record.** Trigger:
Dash. `action.dash` *patched* (JC-10). Already safe: `dodge_duration` and its two
benefits (the shape Dash now adopts), `ready_response`'s two arms (both take
`AE_REACTION` as CONTEXTUAL edges from `ready_reaction_grant`'s single PRIMARY
span), `help_choice`'s two arms, `glossary.action`'s allowance + choice.
`attack_equipment_change` already safe and disclosed as L-1, closed without change.
Regression coverage: the Dash consumer proof plus `SIBLING_PAIRS`, which asserts no
two components of one record hold an equivalent fact on a shared substantive span.

**Family B — a clause fully covered by a span whose claimant does not state it.**
Trigger: Ready L8, Help H3/H6, Influence J6. Patched: `ready_spell` L8 and
`magic_activation` K1 (JC-11), `help_choice` H3/H6 and `influence_check` J6
(JC-12). Schema stop: `action.magic` K2/K3/K4 (S-1). Already safe: `utilize_action`
O2 (the working sibling and the model for the other two), `hide_check` / `hide_end`
(both gates carried by a real `any_of` `Applicability`), `dodge_attack_disadvantage`
(a negated `any_of`), `attack_movement_interleave` B7 (prose-bound at its own extent
with the typed fact beside it). Out of scope: the Search and Study table rows —
guidance, closed by JC-2; random-table selection is not reopened. Regression
coverage: the eligibility, Help, Influence and Magic consumer proofs.

## 10. Validation and gates

Standalone and merged were both run with the registered lift
(`5d-lift-schema-5-to-6`, one step 5→6, 6 collections verified).

| Column | Findings |
| --- | --- |
| partition | 0 |
| structural | 0 |
| schema-6 component rules | 0 |
| reason codes | 0 |
| schema binding | 0 |
| representation (standalone) | 5 |
| representation (merged with accepted prior) | 5 |

The 5 findings are identical in both columns and are exactly the expected
cross-batch missing targets, each asserted by set equality against a declared
expectation rather than by count:

- `glossary.speed` — cited by `action.dash` (record-owned, `Speed`)
- `glossary.concentration` — cited by `action.magic` (record-owned, `Concentration`)
- `attitude.indifferent`, `attitude.friendly`, `attitude.hostile` — cited by
  `action.influence/influence_check`

None of the five exists in the 22-record prior. The five are preserved exactly as
before the remediation.

`detect-secrets` was run exactly as `.pre-commit-config.yaml` configures it
(`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <files>`)
over the regenerated proposal, audit and generator: **rc=0**. The baseline's
`plugins_used` and `filters_used` are unchanged, nothing is excluded, and no
scanning was disabled. Three entries moved and each was inspected individually:

| Change | Value | What it is |
| --- | --- | --- |
| added `a7f136df…` | `d389954c36659e07` | `fact_key(ActivationCostEligibilityFact(spell, action))`, recomputed from the type and confirmed equal |
| removed `1aa4631d…` | `096eddb9536f112a` | `fact_key(RecurringActionRequirementFact(action, turn))` — no longer published (JC-13) |
| removed `ce6d2eef…` | `f48175a8ab780dcd` | `fact_key(ResourceExpenditureFact(spell_slot, expended=False))` — no longer published (JC-13) |

All three are 16-hex deterministic content digests of public typed facts, not
credentials. Every other results section of the baseline is byte-identical, asserted
programmatically.

> **This batch is not publishable on its own,** for two independent reasons.
> `publishable_alone: false` in the audit. Five outbound citations await the batches
> that define their targets, **and** three spans are `UNRESOLVED` at schema stop
> S-1. Zero validator findings would be necessary and insufficient — and this batch
> does not even have zero. It must not be described as a publishable partial batch.

**Coverage.** `pytest tests/ingestion/mechanical` reports well below the 80%
project minimum when run as a subtree, because that subtree exercises only part of
`src/`. This change adds no `src/` code and no test, so it neither improves nor
regresses coverage; the number is a subtree-run artifact and is reported rather
than suppressed. The full-suite figure of record remains the one from the last
full run (94.07%).

## 11. Preservation evidence

- **Frozen review prior** `tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`
  — content SHA-256 `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7`
  and Git blob `6e65533f4a3523aba3d60cfc3c274ab22e66b59a`, identical before and
  after the run. Batches `['conditions-1','hazards-1']`, schema
  `5d-representation-schema-5`, 22 records, 281 spans, 69 components — all asserted.
- **Live accepted oracle** — read as a sentinel only, never as an input; digest
  unchanged across the run.
- **Zero overlap** with the accepted collections: span overlap `[]`, leaf overlap
  `[]`, and collection overlap 0 for records, components, prose bindings,
  relationships, references and provenance.
- **Zero movement** — every accepted record, span and edge is byte-identical in the
  merged view; the merge adds and never rewrites.
- **Retained artifacts** — the pre-existing untracked review notes are untouched.
  The run writes exactly two files, both named for actions-1 and schema 6, both
  already tracked.
- **Batch anchors and the five cross-batch missing references** are preserved
  exactly, asserted by set equality.
- **Ownership** — 78 substantive spans, each with exactly one primary claimant
  (component 9, fact 40, fact qualifier 2, prose binding 27); 98 supporting spans,
  none carrying a primary claim; 0 prose bindings over supporting text; 3 spans with
  no claim at all, asserted to be **exactly** the 3 `UNRESOLVED` spans, and 0
  `UNRESOLVED` spans carrying any claim — which is what `validation.py` requires,
  since `UNRESOLVED` admits the empty set of provenance claims.

## 12. Source and semantic proof limits

What is machine-proved: the cuts, the partition, the six binding values, the schema
pin, the structural and component rules, obligation closure, disjointness from the
accepted prior, byte-level regeneration, and — new in this pass — the five
consumer-boundary compositions of §8 and their counterexamples, read through the
same `_base_records` every consumer of mechanical authority goes through.

What is **not** machine-proved and remains for independent review: that each typed
fact means what the sentence it is bound to means, that each irreducibility reason is
the right member of the six-code catalog, and that the component seams cut the
entries where the source cuts them. `fact_invariant_violations` proves a fact is
well-formed, never that it is the correct reading. The exemplar tables (JC-2), the
Help reason (R-help-reason), and the judgement that S-1 is a genuine vocabulary gap
rather than a reading error are the places where a reviewer disagreeing would change
the artifact, and all are named here rather than buried.

## 13. Architecture Notes

No drift from design principles. This is proposal preparation under CRD Issue 5d and
ADR-005d against the bound CRD Issue 5c source; it adds no production code path,
changes no accepted contract, and touches no runtime module. The representation
schema is consumed at its pinned version and hash — **no schema meaning was changed
to make the batch author cleanly, and the pin was not moved.** Where the schema is
more specific than the source (L-1) or less specific than the source
(R-help-reason), the gap is disclosed rather than closed by editing the schema or
the reading.

One boundary is surfaced rather than resolved in code: **S-1**. Representation
schema 6 has no structure for a threshold over a spell's printed elapsed casting
time, so three clauses of `action.magic` are left `UNRESOLVED` and the batch
carries a second, named publication block. Widening the union is an Owner decision
and a schema-7 question; it is not taken here. This is the "surface, do not silently
resolve" rule of `CLAUDE.md` applied to a representation gap rather than to a
product-semantics one.

Rules Package / Story Bible separation is untouched: this is mechanical canon
authored through the mechanical ingestion path only.

## 14. Stop

Stopping at the completed remediation handoff for independent review, as instructed.
Not done, and not to be done without a further Owner authorization: `accept_proposal`,
publish, activate, retire, merge, closing #137, changing 5c or downstream ownership,
or changing the representation schema or its pin. The branch stays local — no push,
no PR.

## 15. Amendment — S-1 closed at representation schema 7

Independent review of this checkpoint cleared the `Dash` correction, the
`Magic`/`Ready` activation-cost eligibility reclassification and the
`Help`/`Influence` governing prose, and confirmed **S-1**. Schema 7 has since been
minted to close it. Everything above records the state at the schema-6 checkpoint
and is left standing; this section states what has changed and corrects three
pieces of language above that were imprecise or are now stale.

### 15.1 What schema 7 adds

One `ApplicabilityKind` member, `SPELL_CASTING_TIME`, over one closed value object,
`CastingTimeThreshold(at_least_amount, at_least_unit)` — the shape §7's *Missing
capability* named, chosen as an applicability rather than an eligibility fact for
the reason in 15.2. No fact family, no ownership form, no nullable field, no
predicate language, no executable rule. Destination pin
`80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d`; the committed
artifact still declares schema 5 and now reaches schema 7 across
`5d-lift-schema-5-to-6` then `5d-lift-schema-6-to-7`.

Two intrinsic invariants are declared inside schema identity: an amount below 1
states no duration, and `ROUND`/`TURN` are cadences of the initiative cycle rather
than units a casting time is printed in. `casting_time_meets` ranks unit *names* and
declares **no conversion constant**, so a shorter printed unit never meets the
threshold at any amount. That limitation is declared, not discovered, and recorded
in `known_unknowns.md`.

### 15.2 Why applicability rather than a fact

§7's *Missing capability* proposed `(subject=SPELL, at_least=(1, MINUTE))` — an
eligibility-shaped fact. That shape does not survive the composition. K2's
requirement and K4's consequences are two components of one record, both inside the
same printed condition. A gate carried as a *fact* and restated on both components
is refused by `_validate_duplicated_fact_authority`: one source statement would have
become two copies of the same authority. Applicability may repeat across components,
because a condition two structures share is one condition. That asymmetry is what
makes it the scope-preserving carrier, and it is asserted in test rather than argued.

*"If your Concentration is broken"* rides `FactQualifier` on each of the two
consequence facts, because a component has exactly one `applies_when` and the gate
occupies it. Qualifiers compose conjunctively inward — a long casting, whose
Concentration is broken — which is the reading the source prints. A component
stating only `CONCENTRATION_BROKEN` would reach every broken Concentration in the
game.

### 15.3 Corrections to the language above

* **§7 *Not done here* is stale.** "The schema and its pin are unchanged … Widening
  the union is an Owner decision and a schema-7 question" was true of that
  checkpoint. The schema *has* since been widened, under a subsequent authorization,
  and the pin has moved. §13's closing paragraph is stale in the same way and for the
  same reason. The accepted prior remains unchanged — it is **lifted, never
  rewritten** — and no ruling has been made about what the printed rules mean: this
  is representation work under contract 3, not a reading of the game rule.
* **"Obligations answered" is three states, not two.** §§2 and 11 count obligations
  as *accounted for* — read, extent recorded, disposition assigned. That is weaker
  than **represented** (a typed element or a prose binding claims the span) and both
  are distinct from **unresolved** (read, no claim, publication blocked). At the
  schema-6 checkpoint K2/K3/K4 were *accounted for* and **not** represented. They are
  now represented in the schema-7 test evidence; they are **not** accepted, because
  regeneration remains paused.
* **The §8 counterexamples are illustrative, not resolutions.** The
  *counterexample* rows are shape assertions against `_base_records` — they show what
  a differently-composed record *would* publish. They are not source-prose
  resolutions of the clauses they mention. In particular the Magic row's "a spell
  printed with a Bonus Action, Reaction, or 1-minute casting time matches no
  eligibility fact this batch publishes" is correct about the *batch* and was never a
  finding about the Magic action: **a one-minute spell falls outside `Magic` K1, not
  outside the Magic action.** K1 says which spells the action *reaches* by the cost
  they print; K2 states a further requirement *inside* the action. §12's list of what
  is machine-proved should be read with that distinction: the compositions are proved
  as shapes, and the readings behind them remain for review.

### 15.4 Evidence, and its limits

`tests/ingestion/mechanical/test_schema_7_casting_time_gate.py` — 44 tests, all
passing — carries the persisted-gate proof: the threshold's reach and its declared
limits; the two gated components validated by `validate_representation` against the
six-span partition of K2/K3/K4; the duplicated-fact refusal beside the admitted
shared gate; one primary owner per substantive span; the canonical round trip;
malformed-input refusal; the three sibling rebuilders (stored state, accepted
authority, override patches); and the omission rule that leaves accepted payloads
unmoved. Its literals are checked against
`.claude/review-notes/issue-5d-actions-1-obligation-coordinates.json` at pinned
source digest `8974902d…e3d87`, so a same-length paraphrase fails.

Limits, stated rather than left to be inferred: `actions-1` is **not accepted** and
the acceptance-ready regeneration stays **paused**; the ledger in that module carries
the six spans the demonstration claims, not `Magic`'s whole leaf partition; chunk ids
are local to the module; and the comparable-clause check that established the bounded
vocabulary was scoped to casting-time eligibility rather than run as a corpus sweep,
so `SPELL_CASTING_TIME` stands on one instance in one record and is **narrowed, still
deferred** in `known_unknowns.md` rather than discharged.

Nothing is accepted, published, activated, retired, pushed or merged by this
amendment. The five pending cross-batch references, both batch anchors and the frozen
prior are unchanged.
