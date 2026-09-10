# CRD Issue 5d — `actions-1` accepted

**Owner Decision, 2026-09-09.** Ravenlok accepts all 182 spans and the complete representation of
proposal `62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c` as batch `actions-1`,
extending the preserved `conditions-1`/`hazards-1` prior through the registered schema transitions.
That authorization superseded the standing prohibition on accepting this batch and on updating the
committed accepted authority. It authorized nothing else: **no publication, activation, retirement,
push, merge, or closure of #137**, and no further corpus batch.

Performed through the repository's real `accept_proposal` path. Every claim below is executed by
`.claude/review-notes/issue-5d-actions-1-ACCEPT.py`, which is retained. **The Owner made the
decision; the script executed the recorded action and reviewed nothing** — the report says so in a
field of its own rather than leaving the distinction to a reader.

| | |
|---|---|
| Batch | `actions-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-09T00:00:00Z` — one timestamp across all 182 records |
| Proposal identity | `62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `e08759e7…33c03` / `dcb8e2bb…3ad` — unchanged by the acceptance |
| Reviewed head | `377d52e` |
| Schema | `5d-representation-schema-7` / `80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d` |
| Scope | 182 spans · 92 leaves · 13 records · 84 substantive / 98 supporting / **0** unresolved / **0** non-mechanical |
| Accepted oracle identity | `8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee` |
| Accepted artifact content SHA-256 | `d247aed8ab98dab8e71da322de224449f0fe7a46b782c6447010f330d8e87987` |
| Accepted artifact Git blob | `b0bb88a3d1f245141f5c2d60cacb68869ab9440c` |

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings. Raw on-disk digests survive only as `..._raw_sha256_diagnostic`
fields in the report and decide nothing.

## The acceptance authority, and what was retained beside it

The Owner's sentence is stored verbatim in the run as `AUTHORIZATION` and reported back. The exact
182 span ids and 13 record keys were enumerated in the review manifest
`.codex/visualizations/2026/09/05/01a07071-8e0c-7502-b149-77574cc34096/actions-1-schema7-review-scope.json`,
which stays **historical review evidence, not the authorization**. The run cross-checks the accepted
scope against it and reports all eight comparisons separately, so a manifest that had drifted from
what was accepted fails by name rather than by total:

`proposal_identity` · `proposal_sha256` · `span_ids` · `span_count` · `record_keys` ·
`prior_sha256` · `schema` · `missing_reference_targets` — **all `true`**.

The semantic diff is retained in full inside the batch record, 182 entries, tallying
`none → substantive: 84` and `none → supporting_authority: 98`. Nothing was previously judged, so no
prior disposition moved.

## How the proposal was supplied

Not hand-converted, not renamed, not reproduced. The reviewed `MechanicalProposal` is rebuilt by
**executing the reviewed generator** under `ACTIONS7_RERUN=1`, and the run asserts its identity, its
payload hash, that its payload equals the committed proposal JSON, and that the proposal file's own
canonical content SHA-256 and Git blob are unchanged across the run — so the acceptance cannot be a
covert regeneration. Accepted meaning was never re-derived from a builder's output.

**`--verify` reads the frozen prior, not the live artifact.** After acceptance the committed oracle
*is* the merged result; reading it and calling it "the prior" would make every preservation
comparison compare the artifact to itself, which is the exact defect the `hazards-1` checkpoint
records. The prior is therefore
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`, asserted **first** by
content SHA-256 `0925d796…73f7` and Git blob `6e65533f…b59a` before anything is computed from it, and
asserted to hold exactly `conditions-1` and `hazards-1`, with **no** unresolved reference among them.
That fixture is untouched by this acceptance and is byte-identical to what it was.

## Merged result

| collection | conditions-1 | hazards-1 | actions-1 | committed |
|---|---|---|---|---|
| spans | 185 | 96 | 182 | **463** |
| acceptance records | 185 | 96 | 182 | **463** |
| records | 16 | 6 | 13 | **35** |
| components | 54 | 15 | 37 | **106** |
| facts | 70 | 21 | 48 | **139** |
| prose bindings | 15 | 5 | 27 | **47** |
| relationships | 0 | 0 | 0 | **0** |
| references | 15 | 7 | 17 | **39** |
| provenance edges | 185 | 96 | 199 | **480** |

Every prior batch record, acceptance record, span, representation element and obligation is preserved
unchanged — reported element-wise with a count of missing elements beside each collection, all **0**.
The three scopes are pairwise disjoint. `validate_acceptance` returns **no findings**; the written
artifact round-trips exactly; it is written through `accepted_inputs_payload` in the same
indent-2 / sort-keys / LF form the file was already committed in. **One oracle file, extended** —
never a second, which is what the resolver's refusal of two artifacts per release requires.

**Schema anchors** keep `conditions-1` at schema 3 and `hazards-1` at schema 5, where their reviews
happened, and record `actions-1` at schema 7. The file now *declares* schema 7, because that is the
schema the newest acceptance was reviewed under. The **registered succession** is retained in full:
`3→4` → `4→5` → `5→6` → `6→7`, six collections verified at each step, never collapsed into a
transition the registry has no row for.

The two schema-7 gated components are reported by name with their gate and fact counts —
`action.magic/magic_long_casting` and `action.magic/magic_concentration_break`, each carrying
`applies_when` and 2 facts — so the acceptance states what the schema step was actually for.

## The five publication blockers, asserted positively

`validate_representation` returns **exactly five** findings, one per unresolved cross-batch reference
target, and the run asserts the unresolved set is **equal to** those five keys:

`attitude.friendly` · `attitude.hostile` · `attitude.indifferent` · `glossary.concentration` ·
`glossary.speed`

They are asserted as present rather than merely tolerated. A run reporting zero would mean a target
had been **invented**, which is worse than the blocker it appears to remove — so the assertion is
written to fail in that direction too. No target was fabricated by this acceptance, and
`cross_batch_references_resolved` is empty. `publication_blockers.still_blocked` is `true`.

## Batch ordering, corrected during the run

`load_accepted_inputs` returns `batches` in **canonical id order**, not acceptance order, so the
committed artifact reads `['actions-1', 'conditions-1', 'hazards-1']` while acceptance order is
`conditions-1 → hazards-1 → actions-1`. The `hazards-1` script's positional assertion passed only by
alphabetical coincidence. Everything that asserts order now reads `schema_anchors`, which is where
the artifact actually records it; everything that asserts membership reads an id-keyed dict and
separately asserts no id appears twice.

## Which committed checks changed, and why each had to

The acceptance moved facts, so seventeen checks across four modules stated something that is no
longer true. **No assertion was weakened or deleted**; each was retargeted at the authority the Owner
accepted.

* **`test_committed_accepted_authority.py`** — new `ORACLE_IDENTITY`, `ARTIFACT_CONTENT_SHA256`,
  `ARTIFACT_BLOB`, `PROJECTION_UUID`, `PROJECTION_PAYLOAD_HASH`; an `ACTIONS` count dict beside
  `CONDITIONS` and `HAZARDS`, with `MERGED` summed from all three so a merged total that is right for
  the wrong reason still fails; positional batch unpacking replaced by id-keyed lookup; three batch
  ids, three timestamps, three anchors, four lifts; disjointness generalized from a pair to pairwise.
* **`test_the_committed_artifact_is_buildable_and_the_legacy_form_is_not`** changed *meaning*, and is
  recorded here rather than quietly adjusted. `actions-1` was reviewed under schema 7 — the schema
  this build implements — so the committed artifact is again admitted as current authority and
  `validate_schema_binding` returns `()`. The fail-closed refusal it used to demonstrate is **not
  weakened**: it moved to the artifact that still declares a superseded contract, the frozen schema-3
  specimen, where the same test asserts the refusal, the finding text, and the lift that resolves it.
  The permitted half is now asserted against `REPRESENTATION_SCHEMA_VERSION` rather than a literal, so
  the next succession moves this test instead of quietly passing it.
* **`test_schema_6_succession.py`** — the sentinel parametrizes over the frozen prior and the
  committed artifact and pinned **both** to `FROZEN_CONTENT_SHA256`. That only ever worked because
  the two files were byte-identical, which stopped being true the moment the Owner accepted into one
  of them. The committed artifact now has its own `COMMITTED_CONTENT_SHA256`, and the test asserts
  the two constants differ, so it can fail for one file and pass for the other — which is the whole
  point of a sentinel read after every lift has run. The property is unchanged: a *lift* may not
  rewrite either file; an Owner acceptance may extend the committed one.
* **`test_accepted_inputs.py`** / **`test_production_release.py`** — the committed batch list, and
  the record and span counts the production refusal is measured against (22/281 → 35/463). The
  refusal itself is unchanged and was re-run rather than assumed.

## The required secrets gate

Extending the accepted-authority artifact keeps it inside the required `detect-secrets` hook. The
artifact gained **30** new findings, all `Hex High Entropy String`, all deterministic mechanical
authority. **No credential is present.**

| category | count | what it is |
|---|---|---|
| provenance `target_key` terms | 23 | content-derived fact keys, every one `target_kind: "fact"` and every one recomputed from the loaded typed objects through `representation.fact_key()` |
| serialized `fact_key` fields | 3 | same values, in their stored position |
| schema `to_hash` | 2 | `0e4b4378…20b7` and `80e853ef…f43d` — the registered schema 6 and schema 7 hashes |
| `proposal_identity` | 1 | `62202e9a…3b5c`, matched against the loaded batch record |
| `semantic_diff_hash` | 1 | `a816d5dd…76b8`, the `actions-1` batch's own diff hash |

The baseline was **not** regenerated with `detect-secrets scan --baseline`, which rewrites the whole
file. `.claude/review-notes/_rebaseline_accepted_oracle.py` rescans the one artifact through the
`detect_secrets` API, replaces that file's results block, and asserts before writing that every other
file's block and `filters_used`, `plugins_used` and `version` are identical. Verified after the write
against `HEAD`: 60 → 90 entries for the artifact, **0 removed**, **30 added**, every other block
byte-identical, only `generated_at` otherwise moved. No detector, filter, plugin, glob exclusion or
inline allowlist changed.

`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <files>` — the exact
invocation `.pre-commit-config.yaml` declares — exits **0** on all five changed files.

## Stop conditions honoured

`accept_proposal` called exactly once, for exactly the authorized batch and scope · the reviewed
proposal and the frozen prior fixture byte-identical · all earlier accepted meanings, batch evidence
and original schema anchors preserved · accepted meaning never regenerated from a builder's output ·
no schema broadened, no settled meaning revisited, no reference target fabricated · no partial
acceptance: all 182 spans or none · only checks whose accepted-authority expectations actually
changed were touched · nothing published, activated or retired · nothing pushed, branch not merged,
#137 not closed · no further corpus batch begun · the existing checkout and every retained review
artifact kept.
