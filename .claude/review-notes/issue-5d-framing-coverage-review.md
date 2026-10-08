# CRD Issue 5d — framing-coverage candidate (UNACCEPTED)

Review material for independent Codex review before any Owner decision
(#132, #137). Nothing here is accepted, recorded, published or activated. No
Owner approval exists for it, and this note makes no offer.

Governing authority: CRD Issue 5d; ADR-005d Decision 2, as amended
2026-09-16 (unit-only coverage); the existing native `ReviewUnit`,
`MechanicalProposal` and `accept_proposal` contracts. Standing policies apply
unchanged: `source-error-policy.md` and `release-order-owner-decision.md`
(no reordering now).

## Artifacts

| File | sha256 |
|---|---|
| `issue-5d-framing-coverage-generator.py` | `e64617cb220a615228220a588aacf3ef0cec15a9ae15360d48c539708b1bc56c` |
| `issue-5d-framing-coverage-PROPOSAL.json` | `5589a26251db0c62cb55f09afb8f9f1075ccb53fc4a2fceeca7be34cdc1fcb51` |
| `issue-5d-framing-coverage-DELTA.txt` (326 lines) | `67d6f798df81f47760bbb3b2ca204becf9213481acbb1532386ba39d9ac95ca7` |

- Proposal identity: `a7a98598b751dd495b28312b854cf16c4bd7db06739c56bee662c84bd6107a70`.
- Batch `framing-coverage`, schema `5d-representation-schema-16` (hash `7fb9254b…`), policy `5d-semantic-policy-2`.
- Binding: package `67c81736-15fd-5e82-8523-e84922f0a7c6`, release `3fe24ff6-4e3`. The generator asserts it matches the committed oracle's binding.
- To rerun: `python issue-5d-framing-coverage-generator.py`. It rebuilds the proposal and delta, checks both byte for byte, and runs every check below. `--write` writes only these two files.

## Starting state

- Committed oracle: `srd-5-2-1-corpus-3fe24ff6-4e3.json`, sha256 `96e90f71…594a91b` (the Animals catalogue recording). The generator asserts this sha before it runs and again after.
- Counts: 22 batches, 1833 records, 10485 spans, 1460 units, 1438 resolutions.
- Findings: 64 reference findings and 28 uncovered leaves; there are no other findings.
- The 28 leaves are the 29 IDs in `.claude/_sp/rr/leaves.txt` minus the recorded Animals heading `eb6c81a0`; the generator asserts this against the covered set. The ledger (`.claude/_rc/msc/rel/afterworlds.db`) confirms all 28 as represented and without spans.

## Construction

- One new additive batch. It is accepted once, in memory, under the simulated reviewer, over `load_accepted_inputs(committed)`.
- The historical chain is not rebuilt, and no accepted batch is replaced.
- The native `EntryBatch` builds the one entry that has a record.
- The 14 unit-only units are appended to that proposal's `proposed_review_units` (`dataclasses.replace`).
  - `EntryBatch` states one record for every entry. None of these 20 leaves has a record to state, so they are not forced through it, and no dummy record is created.
  - Each unit-only leaf is located by exact whole-leaf text under its container.
  - `review_unit_violations` passes on the amended proposal.

## Leaf dispositions: 28 leaves, 15 units

The occurrence index is shown as @n. The DELTA prints every leaf in full, including the whole table, next to its decision.

### `framing-coverage/glossary_conventions`: 8 leaves, 6 spans

The one new record is `glossary.glossary_conventions` (kind `general_rule`, no parent). It has five prose-bound components with reason `no_identified_structured_use`, as follows.

| @ | Leaf | Disposition |
|---|---|---|
| 7857 | `6514f550` `## Glossary Conventions` | excluded: section heading (the native automatic group) |
| 7858 | `69f82978` "The glossary uses the following conventions:" | supporting: framing for the record, no span |
| 7859 | `5d8e3e9c` Tags in Brackets | expected rule `tags_in_brackets`, span `92cf3dde` |
| 7860 | `6b8dc958` "You." | expected rule `you`, span `514d49df` |
| 7861 | `c48715d7` See Also | expected rule `see_also`, span `2ed9ecb1` |
| 7862 | `0b8d0b3f` No Obsolete Terms | expected rule `no_obsolete_terms`, span `c32e4a92` |
| 7863 | `37509aef` Abbreviations intro | expected rule `abbreviations`, span `a0103739` |
| 7864 | `7f4799fe` abbreviation table, 2273 chars | expected rule `abbreviations`, span `4d536c41`, covering the whole leaf |

### `framing-coverage/legal_information`: 5 leaves, no spans

Each leaf gets its own excluded group:

- @0 heading;
- @1 licence terms (CC-BY-4.0, conditional on the attribution statement);
- @2 the attribution statement;
- @3 attribution limits and the permitted "5E compatible" statement;
- @4 the Section 5 liability notice.

The reasons for @1–@3 state that the exclusion is from mechanical canon only. The attribution obligation still applies to any publication.

### Part openings: 12 units, 13 leaves, no spans

Each of the 12 part headings is its own unit:

| @ | Part |
|---|---|
| 841 | Character Creation |
| 1008 | Character Origins |
| 1126 | Classes |
| 2301 | Equipment |
| 2677 | Feats |
| 2769 | Gameplay Toolbox |
| 3055 | Magic Items |
| 4389 | Monsters |
| 4505 | Monsters A–Z |
| 7530 | Playing the Game |
| 7856 | Rules Glossary |
| 8349 | Spells |

- The Magic Items unit also covers @3056, the flavour introduction ("gleaned from the hoards…"). Its reason is that it neither states nor contextualizes the rule of any item.
- Every heading reason says it is coverage only: it is not a verdict that the heading cannot name a catalogue or section record, and it claims no membership or reference resolution.
- The Character Creation, Classes, Equipment and Spells reasons add that the whole-part citations naming those parts stay unresolved: #3/#5, #7, #24/#35 and #87/#88.

### `framing-coverage/rules_definitions`: 2 leaves, no spans

Two excluded groups: @7865 is the heading and @7866 is "Here are definitions of various rules."

## Observed results (the generator asserts all of these)

**Counts.** Before: (22, 1833, 10485, 1460, 1438). After: (23, 1834, 10491, 1475, 1438). The candidate adds 1 batch, 1 record, 6 spans and 15 units; it adds no resolutions.

**Reference-resolution violations:** 0 before and 0 after.

**Findings:**
- Uncovered leaves go from 28 to 0. Reference findings stay at 64, identical string for string.
- Exactly 28 findings clear, all of them "no semantic spans". The leaves they name equal the leaves of the 15 units.
- No finding is new.

**Delta.** Removals: 0 in every collection. Additions:

| Collection | Added |
|---|---|
| spans | 6 |
| review_units | 15 |
| obligations | 1 (the new record's prose-bound obligation, not the legal notice) |
| records | 1 |
| components | 5 |
| prose_bindings | 6 |
| provenance | 6 |
| acceptance.batches | 1 |
| acceptance.records | 6 |
| review_unit_records | 15 |
| schema_anchors | 1 (schema-16) |

**Preservation.** The monsters-corrections `_preserved` check walks the whole old oracle payload recursively (every top-level key; lists compared as multisets) and finds nothing lost or changed. `Delta.collections()` shows 0 removals in all 16 collections it enumerates, including `reference_resolutions`, `acceptance.reference_resolution_records` and `acceptance.lifts`. No recorded PROPOSAL, ACCEPT or approval file on disk is modified. Source leaves and release order are untouched.

**Titles stay unlocked.** None of the 20 unit-only leaves has a span, and none of the 28 had a prior span. A later batch can still add a span or record over any heading, for example when the held whole-part citations get their targets.

**Consumer.** The remaining-references `consumer`, before and after:
- the new key's direct read is the six spans, in printed order;
- all 1833 other direct reads, and every reading and membership, are unchanged;
- a native `DISABLE` override on the new record removes its direct read and leaves everything else unchanged.

## Disclosures and limits

- **Reversal.** The accepted `issue-5d-rules-glossary-completion-generator.py` (lines 18–19) chose not to author Glossary Conventions ("states how the glossary is written, not a rule") or the Rules Definitions heading and intro. This candidate reverses that choice for Glossary Conventions under the Owner's instruction for this packet. The Rules Definitions leaves are covered but still carry no rule.
- **Record key and kind.** The kind is `general_rule`, not `glossary_rule`, because the section defines no term. The key uses the `glossary.` prefix of the entry-batch helper. No code routes on that prefix.
- **Prose-bound components.** No structured fact family or consumer uses them yet.
- **Tags in Brackets.** It names five tag families (Action, Area of Effect, Attitude, Condition, Hazard), and each has a glossary record. No reference is drafted from it, so no membership is established.
- **Abbreviation table.** The rows that hold only "component", "character" or "Point(s)" continue a two-line meaning from the row above ("Material component", "Nonplayer character", and so on). This is the release's layout as captured. It is kept verbatim: it is not a correction, and it is not a source-error notice.
- **Held items.** Other multi-target, Origin Feats and dynamic-policy items remain held. The whole-part citation targets listed above are reserved for future target construction. This coverage resolves none of them.
- **What was not done.** No broad accepted-content audit, source correction, reordering, schema change or general carry-forward. Source qualification was not repeated, and the broad test suites were not rerun; the qualified evidence is reused.
- **Committed artifacts.** No test, oracle or committed artifact was changed.
- **What recording would need.** Recording would need an Owner acceptance and a separate recording step, which would move the oracle and its pinned tests. Neither exists.
