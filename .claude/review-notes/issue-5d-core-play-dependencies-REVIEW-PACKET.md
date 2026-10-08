# CRD Issue 5d — core-play-dependencies proposal: consolidated review packet (ACCEPTED by the Owner; Codex verification pending)

## Current state: accepted

**Owner decision, verbatim:** *"I accept this exact proposal with the twenty reference findings retained and partial publication/activation blocked."* It answers `core-play-dependencies-owner-review.md`, which is in the Codex task folder, not a repository file. No decision time was stated, so none is recorded. The recorded `accepted_at`, `2026-09-23T15:57:41Z`, is the UTC clock read in the executing shell immediately before the step: it records when the acceptance was *executed*.

Roles:
- **Decision:** the Owner's.
- **Execution:** Claude's, through `issue-5d-core-play-dependencies-ACCEPT.py`.
- **Independent verification:** Codex's, still pending.

What was accepted:
- **Proposal:** the exact proposal, identity `47a1a7a5…2b85`, file SHA256 `b7095130…6c16`, byte-unchanged.
- **Contents:** all 11 records and review units, 52 leaves and 66 spans.
- **How:** one native `accept_proposal` call. Its `prior` is the nine-batch acceptance *with* the attack-roll resolution, re-derived by `issue-5d-core-play-completion-ACCEPT.py`'s `accepted()`, which replays `79657e2a…0eb7` exactly.
- **Result:**
  - ten batches, 92 records and review units, 692 spans;
  - the same one resolution, `resolve-attack-roll-playing-the-game-1`, with its authorization byte-carried;
  - committed oracle SHA256 `78a29e3a1ed5d707475cbea10717d377f836e5428209ac896d45b2eead13615b`.
- **No reference resolution** is proposed, drafted or recorded.

Native validation of the committed artifact:
- 9 830 uncovered leaves and exactly 20 reference findings; no missing acceptance and nothing else. That is 9 850 findings unfiltered.
- The 20 are:
  - the 12 prior unresolved printed pointers;
  - the 5 new named missing glossary targets: Size, Creature Type, Alignment, Passive Perception and Experience Points;
  - the 3 broad Stat Block pointers: "Playing the Game" ×2 and "Monsters".
- There are no guessed targets, no stubs and no ambiguity.
- The recorded resolution still applies, with no violations. Stat Block's two same-wording pointers stay unresolved as distinct citations.
- The release cannot publish. Nothing is published or activated, partially or otherwise.

Everything below this section is the **historical review record**: the proposal as it was offered, the boundary it raised and how that was decided. Its "unaccepted", "composed in a test only" and "pending Owner decision" statements describe that time, not the current state.

## Historical: at proposal time

This is a proposal only. Nothing in it is accepted, resolved, published or activated, and no reference resolution is drafted or recorded. The committed nine-batch acceptance is unchanged: 81 records, 626 spans, 9 batches, one reference resolution (`resolve-attack-roll-playing-the-game-1`), oracle SHA256 `79657e2a751ee274b53f61d5ce76c26cefd4542439188a51144a76e474c10eb7`. The next steps are Codex's independent review, then one consolidated Owner decision (§6). **§5 raised one boundary that blocked accepting this proposal as it stood. The Owner has since decided it (option 1, citation identity), and the validator and ADR-005d Decision 7 are amended accordingly. That decision is not acceptance of this batch: the batch's semantic review by Codex and the Owner's decision on it are still pending.**

| Item | Value |
|---|---|
| Release | package `9717e288-c099-5217-b2d2-f89aeabd7b73` / `5.2.1-corpus.883aabdf-462` |
| Artifact | `issue-5d-core-play-dependencies-PROPOSAL.json` (112 597 bytes, `5d-proposal-2`, `5d-representation-schema-15`, LF) |
| proposal_identity | `47a1a7a57e49f0e5aa6e1f1578edd39cb507992c48822a8d79ede21a6d5e2b85` |
| file SHA256 | `b709513020a6fc011f2c93bb9ff6106bd87411acbfe439e19a039ad4d76c6b16` |
| Generator | `issue-5d-core-play-dependencies-generator.py`. It holds literal review data only and runs on the shared `authoring.py`. |
| Scope | 11 records, 52 leaves, 66 spans (51 substantive, 15 supporting), 11 ENTRY review units |
| Representation | 41 components (9 structured, 4 mixed, 28 prose), 16 facts, 40 prose bindings, 33 references, 106 provenance claims, 0 relationships, 48 expected rules |
| Batch checks | partition 0, review_units 0. Representation: exactly the expected out-of-batch findings (33), meaning the accepted context targets the batch alone cannot see plus the new unknowns and pointers in §3. |
| Tests | `tests/ingestion/mechanical/test_core_play_dependencies_proposal.py`: 26 tests |

**Reproduce:** `venv/Scripts/python .claude/review-notes/issue-5d-core-play-dependencies-generator.py <published afterworlds.db>`. `emit` writes nothing unless partition and review_units are empty and the representation findings exactly equal `expected_representation_findings()`.

## 1. Scope map

Each entry is the whole `Rules Glossary › Rules Definitions › <label>` container, re-resolved from `rp_ledger_leaves` and read against the official PDF (pp. 177–190). Each entry is one ENTRY unit. Only the 11 record headings are excluded; no rule-bearing leaf is excluded.

| Record | Container label | p. | Leaves | Cited by (accepted) |
|---|---|---|---|---|
| `glossary.attack_roll` | Attack Roll | 177 | 2 | `glossary.armor_class` |
| `glossary.blindsight` | Blindsight | 177 | 2 | `play.exploration/special_senses` |
| `glossary.burning` | Burning [Hazard] | 178 | 2 | `play.exploration/hazards` |
| `glossary.carrying_capacity` | Carrying Capacity | 178 | 4 | `play.exploration` (carrying objects) |
| `glossary.darkvision` | Darkvision | 180 | 2 | `play.exploration/special_senses` |
| `glossary.dehydration` | Dehydration [Hazard] | 181 | 3 | `play.exploration/hazards` |
| `glossary.malnutrition` | Malnutrition [Hazard] | 185 | 4 | `play.exploration/hazards` |
| `glossary.stat_block` | Stat Block | 188–189 | 21 | `glossary.challenge_rating` |
| `glossary.suffocation` | Suffocation [Hazard] | 189 | 2 | `play.exploration/hazards` |
| `glossary.tremorsense` | Tremorsense | 190 | 3 | `play.exploration/special_senses` |
| `glossary.truesight` | Truesight | 190 | 7 | `play.exploration/special_senses` |

The three tables are authored as printed: Carrying Capacity (with U+00D7 in every cell), Water Needs per Day and Food Needs per Day. Stat Block includes every subsection, from *Size* through *Damage Notation*, with the Damage Notation example. *Languages* and *CR* share one printed leaf, and each is its own clause. The *Areas of Knowledge* table printed beside Stat Block belongs to *Study* and is not in this container.

## 2. Scope and conditions: what each typed fact is read with

The typed facts appear only where the closed vocabulary states the source's condition. Where it cannot, the condition stays in the **same** component's governing prose.

| Component | Handling | Facts | Condition / cadence carried |
|---|---|---|---|
| `burning/burning_damage` | STRUCTURED | `Damage(FIRE, 1d4)` | `recurs = START_OF_TURN, SUBJECT` ("at the start of each of its turns") |
| `burning/self_extinguish` | MIXED CTX | `ActionEconomy(ACTION)`, `ConditionEffect(PRONE, APPLIES)`, `EffectTermination` | prose: "on yourself", "rolling on the ground" |
| `burning/ambient_extinguish` | MIXED CTX | `EffectTermination` | prose: doused, submerged or suffocated (no Applicability names these) |
| `dehydration/water_requirement` | STRUCTURED | `SizeKeyedQuantity(WATER, DAY, 1/4, 1, 1, 4, 16, 64 gal)` | the table |
| `dehydration/dehydration_exhaustion` | STRUCTURED | `ConditionLevel(EXHAUSTION, GAIN, 1)` | `applies_when` = water < 1/2 for the day; `recurs = END_OF_DAY` |
| `dehydration/dehydration_recovery` | STRUCTURED | `ConditionRemovalRestriction(EXHAUSTION, until water ≥ 1, cause_scoped)` | not gated by the accrual band |
| `malnutrition/food_requirement` | STRUCTURED | `SizeKeyedQuantity(FOOD, DAY, … lb)` | the table |
| `malnutrition/starvation_save` | STRUCTURED | `AbilityCheck(CON save, DC 10)`, `ConditionLevel(EXHAUSTION, GAIN, 1)` | `applies_when` = 0 < food < 1/2 ("eats **but**…"); the gain alone is qualified by a failed save; `recurs = END_OF_DAY` |
| `malnutrition/starvation_automatic` | STRUCTURED | `ConditionLevel(EXHAUSTION, GAIN, 1)` | `applies_when` = food = 0 sustained ≥ 5 days; `recurs = END_OF_DAY`. This covers "the end of the fifth day" and "each subsequent day without food" together, and the band does not overlap the save's band at zero. |
| `malnutrition/malnutrition_recovery` | STRUCTURED | `ConditionRemovalRestriction(EXHAUSTION, until food ≥ 1, cause_scoped)` | — |
| `suffocation/breath_duration` | STRUCTURED | `DerivedQuantity(1 + CON mod minutes, floor 30 s)` | — |
| `suffocation/suffocation_accrual` | MIXED CTX | `ConditionLevel(EXHAUSTION, GAIN, 1)` | `recurs = END_OF_TURN, SUBJECT`. Prose: "runs out of breath **or is choking**", a trigger no Applicability names. |
| `suffocation/suffocation_recovery` | MIXED CTX | `ConditionLevel(EXHAUSTION, REMOVE, all_levels, cause_scoped)` | removes **only** the levels suffocation caused. Prose: "can breathe again". |

**Required conditions, as the brief states them:**
- **Truesight: the range governs all benefits.** The lead ("…within a specified range. Within that range, your vision pierces through the following:") and all five benefits are **one** prose component (CTX). No benefit can be read apart from the range. Alternative considered and rejected: an `AutomaticOutcomeFact` for saves against visual illusions. No typed surface can carry "within range", so that fact would state an unranged automatic success, which is broader than the source.
- **Suffocation removes only what suffocation caused:** `cause_scoped=True` on the REMOVE fact.
- **Recurring effects keep their timing:** four hazards carry `recurs` (5 components); tested in the proposal and in the GameMaster view.

**Prose components (28), with reasons:**
- **Attack Roll** is `no_identified_structured_use`: it restates `play.d20_tests`, which already types the attack roll, so there is one typed copy.
- **Blindsight, Darkvision, Tremorsense and Truesight** are `contextual_applicability`:
  - `Sense` has only SIGHT and HEARING.
  - Blindsight is expressly *not* physical sight, and Tremorsense "doesn't count as a form of sight".
  - Range, cover and surface conditions stay beside what they limit.
  - No schema expansion is proposed.
- **Carrying Capacity** is prose (NO_USE):
  - No family multiplies Strength by a size factor.
  - The drag/lift/push rule is a Speed **ceiling** ("no more than 5 feet"). `SpeedChange.SET_TO` would raise a slower Speed, and there is no cap member.
- **Stat Block** has one prose component per subsection. It describes a printed format; reading a monster's numbers is the creature record's job.
  - Alignment is `gamemaster_latitude` ("with the GM determining its actual alignment").
  - Damage Notation is `gamemaster_latitude` ("The GM determines whether you use the static number or the die expression").
  - Attack Notation is `contextual_applicability` ("unless its entry says otherwise").
  - The rest are NO_USE.

**Shared-helper change (one field).** `EntryComponent.recurs` passes through to `ComponentDraft.recurs`, a field schema 15 already has. It defaults to `None`, so every earlier generator reproduces its committed bytes; the regression set passed, 204 tests. There is no schema change and no new family.

**Informative only, not authority:** the retired `hazards-1-schema5-REGEN` generator's typing (bands, cause-scoped restrictions, the derived breath quantity) was consulted. Every fact above was re-derived from the source text.

## 3. Reference map (33 references)

**Accepted targets (18 distinct).**
- **Glossary:** Blinded, Invisible (×2: Blindsight, Truesight), Prone, Exhaustion (×7), Unarmed Strike, Speed, Burrow, Climb, Fly and Swim Speed, Resistance, Vulnerability, Immunity, Challenge Rating.
- **Playing the Game:** "D20 Tests" → `play.d20_tests`, "Exploration" → `play.exploration`, "Proficiency" → `play.proficiency`, "Actions" → `play.actions`. Each is read from the parenthesized section of its `_See also_ "Playing the Game" (…)`.
- **Folding:** the Dehydration and Malnutrition `_See also_ "Exhaustion."` pointers fold into the component references with the same text and target (the shared fold). No duplicate is produced.

**New unknown targets (5).** These are named glossary entries that exist in the release but are not authored here or accepted. They are left as findings, not stubs:

| Target | Cited from |
|---|---|
| `glossary.size` | Stat Block `_See also_ "Size."` |
| `glossary.creature_type` | Stat Block `_See also_ "Creature Type."` |
| `glossary.alignment` | Stat Block `_See also_ "Alignment."` |
| `glossary.passive_perception` | Stat Block `_See also_ "Passive Perception."` |
| `glossary.experience_points` | Stat Block `_See also_ "Challenge Rating" and "Experience Points."` |

**New unresolved part pointers (3).** Each names a part rather than a record, so no destination is guessed:
- `stat_block/ac_initiative_hp` "Playing the Game" (scope `playing-the-game`). The AC, Initiative and HP it points to live in several records.
- `stat_block/ability_scores` "Playing the Game" (scope `playing-the-game`). Ability scores and modifiers live in `six_abilities`; saving throws live in `d20_tests`.
- `stat_block/challenge_rating` "Monsters" (scope `srd-5.2.1/monsters`, formed from the release's part name).

**Mentions left unreferenced:** Total Cover, Darkness and Dim Light (the glossary has no *Total Cover* entry; Darkness is a Light term), Ethereal Plane (no entry), "such as Darkvision" in *Senses*, and "this glossary" in *Actions*.

## 4. Composition against the 81 accepted records (test-only)

| | Accepted alone | Accepted + this batch |
|---|---|---|
| Glossary unknowns cited by accepted records | 11 | 0 (all closed) |
| New glossary unknowns | — | 5 (§3) |
| Accepted unresolved pointers | 12 | 12 (unchanged) |
| New unresolved pointers | — | 3 |
| **Ambiguity** | 0 | **0** under the citation-identity amendment (§5). Before it: 1, `playing-the-game:'Playing the Game': ambiguous — resolves to ['', 'play.d20_tests']` |
| Reference findings in total | 23 (11 glossary unknowns + 12 unresolved) | 20 (12 accepted unresolved + 5 new unknown + 3 new unresolved) |
| Uncovered leaves | 9 882 | 9 830 (exactly the batch's 52) |
| Spans without acceptance | — | 66 (this batch's) |

No accepted record, span, unit or batch is reauthored or shares an identity with this batch.

## 5. Boundary: the attack-roll resolution and the Stat Block pointers (decided: citation identity)

**Status (decided).** The Owner chose option 1: *"I agree we should identify a citation by where it occurs as well as what it says."* That authorizes the contract and validator correction only. It does not accept this batch and it records no resolution. No decision date was stated, so none is recorded. The written decision note named in the brief was not in the repository; the Owner's sentence is recorded as the brief quotes it.

- **Authority:** ADR-005d Decision 7 now carries an Owner-decision amendment. The 2026-09-19 text is kept as history.
- **Implementation:** `relationship_and_reference_violations` keys ambiguity by the citation's four coordinates, `reference_target_key(ref)[:4]` (source record, owning component, printed wording, committed scope). Those are the same coordinates `ReferenceResolution.citation_key()` already uses. The Decision 5 ownership check (a record stating one citation both directly and through a component) is now judged without the target, so the amendment cannot open a gap there. There is no new validator, schema field or resolution.
- **Result on this batch:** the composed view reports no ambiguity. Its 20 reference findings are exactly the 12 accepted plus the 8 new ones in §3. The 66 spans are without acceptance, and 9 830 leaves are uncovered. The recorded resolution's applicability is `[]` on both the accepted authority and the composition. In the loader's effective view the combat citation resolves to `play.d20_tests`, while both Stat Block pointers stay unresolved and still block publication.
- **Unchanged:** the proposal bytes, identity and file SHA, the nine-batch oracle, and the resolution bytes.

The finding and options below are the record of what was raised.


**Finding.**
- `relationship_and_reference_violations` (`validation.py`, around lines 435–500) judges ambiguity by `(scope_key, source_text)` alone.
- The recorded resolution gives the accepted `play.combat/attack_structure` "Playing the Game" citation the effective target `play.d20_tests`.
- This batch's two Stat Block "Playing the Game" pointers are honestly unresolved (`""`) in the same scope with the same wording.
- Composed, the effective view therefore reports that key as ambiguous. `reference_resolution_violations` then refuses the recorded resolution:

  > applying these resolutions would make the effective references state something publication refuses: reference srd-5.2.1/playing-the-game:'Playing the Game': ambiguous — resolves to ['', 'play.d20_tests']

On the accepted authority alone it reports `[]`. The resolution's bytes are untouched, and this batch drafts no resolution. But **accepting this proposal as it stands would make the recorded resolution inapplicable**, which the brief does not permit. Both results were pinned in `test_the_recorded_resolution_is_untouched_but_composed_would_be_refused`. It is now `test_the_recorded_resolution_still_applies_beside_the_stat_block_pointers`, which pins `[]` on both views.

**Classification:** owner decision needed, a specification contradiction. It is not a listed Known Unknown: `docs/architecture/known_unknowns.md` has no reference-resolution or ambiguity entry. The ambiguity rule in effect generalizes the one attack-roll resolution to every "Playing the Game" pointer in that scope. That was invisible while only one such citation existed.

**Not taken, because each is ruled out by the brief:**
- Resolving the two Stat Block pointers to a target. Each spans several records, so this would be a guessed broad-pointer resolution.
- Demoting them to mentions. That erases explicit citations, and `ReferenceResolution`'s own docstring rejects it.
- Changing their scope or wording, or changing the validator, to dodge the key.

**Options for the Owner:**
1. **(Recommended, as my reading; the Owner's call.)** Judge ambiguity per citation, not per `(scope, wording)`: an unresolved sibling would not conflict with a separately resolved citation. `ReferenceResolution` already identifies "the exact accepted citation by four coordinates". **This reverses a deliberate design premise, not an oversight.** `validation.py` states that "Unique destination names alone never establish intent, so the scope is what disambiguates", which means the same wording in the same scope is taken as the same intent. Stat Block's pointers contradict that premise: same wording, same scope, different referents. The decision is therefore whether *wording plus scope* or *the citation* identifies intent. This is a validator change outside this batch and would need its own authorization and review.
2. Require every `playing-the-game:'Playing the Game'` pointer to share one target. That is wrong for Stat Block, whose pointers do not mean `play.d20_tests`.
3. Owner-reviewed resolutions for the two Stat Block pointers. There is no single faithful destination for either.
4. Accept the other ten entries now and hold Stat Block until (1) or another decision. **This option has a cost.** `accept_proposal` names the review units it accepts, but the representation is proposal-wide. The safe reading is that this means re-emitting a 10-entry proposal with a new identity and a fresh Codex round. It also runs against the brief's "one coherent batch".

Until decided, the proposal kept the honest pointers. It still does: option 1 needed no change to them.

## 6. Owner decision requested (historical; decided — see *Current state*)

1. ~~The §5 boundary: choose an option.~~ Decided: option 1, citation identity (§5). It is no longer a blocker to reviewing the batch as one piece.
2. The scope and conditions in §2, especially Truesight as a single ranged prose component, the cause-scoped Suffocation removal, the four cadences, the consumption bands and the save-only qualifier.
3. The reference map in §3: 5 new unknown targets and 3 new unresolved pointers left as findings.

## 7. Verification

**After the citation-identity amendment.**
- The proposal and the nine-batch acceptance are byte-unchanged:
  - PROPOSAL file SHA256 is `b7095130…`;
  - proposal_identity is `47a1a7a5…`;
  - the oracle SHA256 is `79657e2a…`;
  - `--verify` replays pass for the completion and checks/actions/rests acceptances.
- Focused tests, which now cover:
  - the combat resolution beside the two unresolved Stat Block pointers, through the loader;
  - distinct valid destinations for distinct citations of identical wording, from different components of one record and from different records;
  - a true same-citation conflict, which is still ambiguous;
  - an invalid joint decision hidden behind a valid sibling, which the loader refuses;
  - the inherited-resolution recheck;
  - atomic multi-resolution application;
  - record/component cross-form ownership.
- Shared-validator regression: the full test suite, 6708 passed, 141 skipped (coverage 92.30%).
- black, ruff and `mypy src/` are clean. detect-secrets passes on the changed files with the baseline unchanged. `pip-audit` remains deferred / non-green (31 findings in 11 packages).

**At proposal time (historical).**

- Generator reproduction: identical proposal identity and file SHA on rerun; `emit` exit 0.
- `test_core_play_dependencies_proposal.py` has 26 passed. It covers:
  - the bytes and identity;
  - the shape and scope;
  - the batch findings;
  - Truesight, Suffocation, the cadences, the bands and the qualifier;
  - the GameMaster view reading `recurs`, `applies_when`, qualifiers and prose;
  - the references and headings;
  - residue and omission: a dropped example, a Truesight benefit, each of the three tables, a component;
  - composition against the 81 records;
  - resolution applicability.
- Helper regression: every authoring-importing test file (11), 204 passed. That includes byte reproduction of every earlier generator. The full 3530-test suite was not rerun, because the only `src/` change is one defaulted passthrough field, and every consumer is in that set.
- Prior bytes, replay and resolution: the committed oracle SHA256 is still `79657e2a…`. The resolution is intact, with no violations on the accepted authority.
- black, ruff, `mypy src/` (235 files): clean.
- detect-secrets on the five batch files plus the baseline: hook exit 0.
  - **Baseline delta:** appended only, +137 / −0 lines, so it cannot be mistaken for other work. It adds two new keys: the PROPOSAL (17 entries: 11 public fact keys and 6 release-binding/policy hashes) and the test (2 entries: the accepted oracle SHA and this proposal identity).
  - **Preserved:** `generated_at`, the key order and every prior entry.
  - **Stability:** the baseline SHA256 is `76bb4550…` both before and after the hook.
- `pip-audit`: not rerun this session. Its 31 findings in 11 packages remain **deferred / non-green** by Owner decision.
