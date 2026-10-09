# CRD Issue 5d: Animals part-catalogue candidate (UNACCEPTED, for Codex review)

Status: this candidate is prepared for review only. Nothing is accepted, recorded, committed or published. The committed oracle
`e0fd7690f519ec34dabcbba320936c20faff402fd94b925a2d4453316a29b14c`
(22 batches, 1832 records, 10484 spans, 1459 units, 1434 resolutions; findings 68 refs, 29 uncovered) is unchanged. This packet is not an acceptance offer.

## Artifacts

| File | SHA-256 |
|---|---|
| `issue-5d-animals-part-catalogue-REPLACEMENT.py` (constructor and checks) | `3fd3da99f4792555b3488e0778c5cb212e5ed47055c92bae98dbe70d7ea30b24` |
| `issue-5d-animals-part-catalogue-PROPOSAL.json` (identity `228726d29769fcdb88e874c79b1a0685c8e1b18c59ce538011d8978d57645e38`) | `7f067f7417ad0dd69fd6f86410b2f6704aacc92ffb955e4c3383413597b1425d` |
| `issue-5d-animals-part-catalogue-resolutions-DRAFTS.json` (4 drafts) | `371dadb97b21a831e2c383bcb6602e14ce69cf143060aa123f2b8ef648e7be87` |
| `issue-5d-animals-part-catalogue-DELTA.txt` (328 lines; full-text, order-aware) | `801678436a0fbf9a770d093e881bbb68b18d0ec34e9f21b511e89393fadfa813` |

- `venv\Scripts\python.exe .claude/review-notes/issue-5d-animals-part-catalogue-REPLACEMENT.py` checks every artifact and every claim below. Adding `--write` regenerates the files.
- The script works only in memory and on a temp copy of `.claude/_rc/msc/rel/afterworlds.db`.
- It asserts that the committed artifact's bytes are unchanged.

## Source meaning

The heading `# Animals` (leaf `eb6c81a0-515f-599f-aa85-7e5511fa796b`) is the release's own part that holds the 95 animal stat blocks. Both citing spans point at that collection, as a place to pick stat blocks from:

- **Wild Shape, Known Forms** (`a7c5ecfd-ae74-55ec-8c0d-26e2510edcdd`) prints: `see "Animals" in "Monsters" for stat block options`.
- **Polymorph, Effect** (`b48c9505-cb38-5925-9489-64cb6408d07a`) prints: `See the "Animals" section of "Monsters" for a sample of Beast stat blocks.`

Each pointer is one compound pointer. "Animals" names the collection; "Monsters" says where it sits in the printed book. In this release, Animals is its own `#` part, which follows the tracked Animals/Monsters release-order defect (`release-order-owner-decision.md`; no reorder is made here). This is a structure question, not a text error, so no errata or source-error issue is suspected.

## Candidate: the smallest native shape

Only the Animals batch is affected. The recorded generator and proposal are untouched. The candidate is built by `candidate_batch`, which applies `dataclasses.replace` to the recorded Animals batch. It adds:

- the `general_rule` record `animals.animals`. It has one heading-only `prose_bound` component, `animals`, reason `no_identified_structured_use`, covering span `33896055` `'# Animals'`.
- the review unit `animals/animals`, with kind `section`.
- 95 `catalogue_member` relationships, one from each existing `animals.<slug>` record to `animals.animals`, in printed order. Each cites its member's first clause.

This is the same `EntryBatch.members` / `CATALOGUE_MEMBER` seam as the accepted precedents `spells.spell_descriptions` (339 members) and `magic_items.magic_items_a_z` (258 members). The 95 records had no catalogue parent before this, so no multiple-parent or recursive policy comes into play. No stat block is copied, reauthored or re-read: every stat block's direct read is unchanged (95 of 95).

Proposal delta against the recorded proposal: additions only.

| Collection | Change |
|---|---|
| components | +1 |
| prose_bindings | +1 |
| provenance | +96 |
| records | +1 |
| relationships | +95 |
| review_units | +1 |
| spans | +1 |
| anything lost | 0 |

## Drafts: held rows

All four drafts target `animals.animals`, with suffix `-animals-part-1`. Each cites the single span that contains the printed pointer.

| Row | From | Text / scope | Draft id |
|---|---|---|---|
| 1 | `classes.druid.wild_shape` / `known_forms` | Animals / `srd-5.2.1/animals` | `resolve-classes-druid-wild-shape-known-forms-animals-animals-part-1` |
| 2 | `spells.polymorph` / `effect` | Animals / `srd-5.2.1/animals` | `resolve-spells-polymorph-effect-animals-animals-part-1` |
| 47 | `classes.druid.wild_shape` / `known_forms` | Monsters / `srd-5.2.1/monsters` | `resolve-classes-druid-wild-shape-known-forms-monsters-animals-part-1` |
| 63 | `spells.polymorph` / `effect` | Monsters / `srd-5.2.1/monsters` | `resolve-spells-polymorph-effect-monsters-animals-part-1` |

## Chain replay and delta

- **Controls.** The recorded generator rebuilds the recorded proposal byte for byte. Replaying the recorded chain rebuilds the committed e0fd7690 bytes. Every other batch is reused byte for byte.
- **Counts.**

  | State | Counts | Findings (refs, uncovered) | Violations |
  |---|---|---|---|
  | Candidate | (22, 1833, 10485, 1460, 1434) | (68, 28) | 0 |
  | With drafts | (22, 1833, 10485, 1460, 1438) | (64, 28) | 0 |

- **Findings cleared: exactly 5.**
  - Leaf eb6c81a0.
  - 2 × `srd-5.2.1/animals:'Animals'`.
  - 2 × `srd-5.2.1/monsters:'Monsters'`.

  The other 64 references and the other 28 uncovered leaves are untouched.
- **Simulated bytes.** `e702cbc427716695bf54dc7ef2b0dc6d76f8e03d57104b166aed06e0fd6080f4`.
- **Oracle delta by collection.**
  - Additions only, except two replacements.
  - The Animals `acceptance.batches` record is replaced. Only its derived fields change:
    - `proposal_identity`, which now equals the candidate identity;
    - `resolved_scope`, which is the old scope in order plus the heading span;
    - `semantic_diff_hash`;
    - `diff`, which gains one row, the heading span.
  - The Animals `acceptance.schema_anchors` entry is replaced (identity only).

## Consumer evidence (native `RR.consumer` / `apply_override_set` and projection)

- **Members.** `animals.animals` has 0 members before and 95 after, in printed order.
- **Direct read.** Its direct read is `['# Animals']`.
- **Reading.** The catalogue reading is 859 spans:
  - the owned text in printed order, each span once;
  - plus 23 governing Parts-of-a-Stat-Block context spans.

  Allosaurus is at position 1 and Riding Horse at position 692.
- **Disabling `animals.riding_horse`.** It leaves the direct reads, and 0 of its spans remain in the part's reading. The rest of the reading is kept.
- **Disabling `animals.animals`.** It is neither a direct read nor a catalogue. The stat blocks are still read directly.
- **Projection.** `representation.references` sends all four rows to `animals.animals`.

## Unresolved boundaries (for Codex, then Owner; not decided here)

1. **First part-level record.** `animals.animals` would be the first `#`-level catalogue record. The `<part>.<section>` key convention and a heading-only `general_rule` for a part are review points.
2. **Rows #47/#63 (Monsters qualifier).** The drafts send the printed qualifier "Monsters" to the Animals record. This follows the existing review's reading ("the part as such: Animals"). The alternative is to carry only the qualifier, as #34/#38 were handled, which would leave 66 references open. Codex should weigh this.
3. **Release order.** Animals is printed "in Monsters" but released as a separate part. This is the tracked release-order defect. It is held for the single bounded release-order pass.
4. **Other held boundaries, unchanged.** Origin Feats, multi-destination and dynamic boundaries remain held.

## Verification (explicit venv python, `RTK_DISABLED=1`)

| Check | Exit |
|---|---|
| black `--check` (script) | 0 |
| ruff check (script) | 0 |
| mypy `--strict`, `MYPYPATH=src` (script) | 0 |
| constructor, verify-only; output identical to the `--write` run; the four files' SHAs stable | 0 |
| `pytest --no-cov tests/ingestion/mechanical/test_animals_proposal.py` (14 passed) | 0 |

**Secrets baseline.** The update is scoped to this packet's files and their public values; settings, filters, flags and entry order are kept.
- It adds 20 entries, prunes none and moves none.
- SHA before: `83348db4f892877b21f922a71fb69e35856d480ca8367d0160e14125b6e58f92`.
- SHA after: `eeea9c0f3feb860e3ca475619a1704625e75b99e95d50590e9348d9d36243884`.
- The baseline is staged by name only.
- `detect-secrets-hook --baseline .secrets.baseline` ran twice on the five packet files, with exit 0 both times and the SHA stable.

**Not green or deferred:**
- pip-audit and expanded mypy remain deferred and not green.
- No full suite was run: the committed chain is unchanged and the chain control proves the replay.
