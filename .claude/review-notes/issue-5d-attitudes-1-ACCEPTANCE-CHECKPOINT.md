# CRD Issue 5d — `attitudes-1` accepted

**Owner Decision, 2026-09-10.** Ravenlok accepts all 24 spans and the complete representation of
proposal `c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22` as batch `attitudes-1`,
extending the preserved `conditions-1`/`hazards-1`/`actions-1` prior through the registered schema
transitions. That authorization superseded the standing prohibition on accepting this batch and on
updating the committed accepted authority. It authorized nothing else: **no publication, activation,
retirement, push, merge, or closure of #137**, and no further corpus batch.

Performed through the repository's real `accept_proposal` path. Every claim below is executed by
`.claude/review-notes/issue-5d-attitudes-1-ACCEPT.py`, which is retained. **The Owner made the
decision; the script executed the recorded action and reviewed nothing** — the report says so in a
field of its own rather than leaving the distinction to a reader.

| | |
|---|---|
| Batch | `attitudes-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-10T18:53:49Z` — one timestamp across all 24 records |
| Proposal identity | `c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `b310565f…0763` / `5c86ef76…f106` — unchanged by the acceptance |
| Reviewed head | `1e6ecc95d0c830f4357de4c55502a51a606ffb7c` |
| Schema | `5d-representation-schema-8` / `8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff` |
| Scope | 24 spans · 16 leaves · 4 records · 5 substantive / 19 supporting / **0** unresolved / **0** non-mechanical |
| Accepted oracle identity | `c3b4d4b759441b05418fcbe1d90811e0d7c2535319aa005e64201ce29b5c74fa` |
| Accepted artifact content SHA-256 | `fd390d95dde74498142035d9dde00ccf7effadb372fc13f9662154841bb787ab` |
| Accepted artifact Git blob | `2346404005618b0389b4e4f66d2e96c5c35b200f` |

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings. Raw on-disk digests survive only as `..._raw_sha256_diagnostic`
fields in the report and decide nothing.

## The accepted timestamp is observed, not invented

`2026-09-10T18:53:49Z` is a UTC clock read taken in the same shell invocation that ran the script,
immediately before the run, **truncated — not rounded — to the second**, and written into the constant
before the interpreter started. It is not a wall-clock read at replay and it is not a synthetic
midnight; `actions-1` needed a correction round for exactly that, and this batch pinned an observed
value the first time.

The write it authorizes was observed **afterwards**, and both figures are recorded rather than one
being passed off as the other: the accepted artifact carries `LastWriteTimeUtc`
`2026-09-10T18:54:19.5767892Z`, read from that property directly, thirty seconds later — the time the
reviewed generator took to re-derive the proposal and the acceptance seam took to merge and serialize
it. The pinned value is therefore the moment the acceptance was **initiated**. The basis travels with
the value as `accepted_at_basis` in both the script and the report.

It stays a **constant**, not `now()`, because the three pins above are only assertable if the run is
reproducible.

## The acceptance authority, and what was retained beside it

The Owner's sentence is stored verbatim in the run as `AUTHORIZATION` and reported back.

**There is no `attitudes-1` review-scope manifest, and none was invented.** `actions-1` had
`actions-1-schema7-review-scope.json`, which enumerated its span ids and record keys; this batch's
retained independent evidence is a **probe** document,
`.codex/visualizations/2026/09/05/01a07071-8e0c-7502-b149-77574cc34096/attitudes-1-final-independent-probe.json`,
which carries the proposal identity, the file digests, the reviewed head and the counts but **no span
list**. The accepted scope is therefore derived from the proposal itself and never from the probe;
the probe is cross-checked on exactly the fourteen fields it actually carries, each reported
separately so a probe that had drifted fails by name rather than by total:

`proposal_identity` · `proposal_sha256` · `audit_sha256` · `prior_sha256` · `reviewed_head` ·
`spans` · `records` · `components` · `facts` · `prose_bindings` · `references` · `provenance` ·
`leaves` · `dispositions` — **all `true`**.

This is the one process deviation from the `actions-1` precedent. It is stated in the script's module
docstring as well as here, because "we cross-checked a manifest" and "we cross-checked a probe that
has no span list" are different claims and the weaker one is the true one.

The semantic diff is retained in full inside the batch record, 24 entries, tallying
`none → substantive: 5` and `none → supporting_authority: 19`. Nothing was previously judged, so no
prior disposition moved.

## How the proposal was supplied

Not hand-converted, not renamed, not reproduced. The reviewed `MechanicalProposal` is rebuilt by
**executing the reviewed generator**, and the run asserts its identity, its payload hash, that its
payload equals the committed proposal JSON, and that the proposal file's own canonical content
SHA-256 and Git blob are unchanged across the run — so the acceptance cannot be a covert
regeneration. A pre-mutation identity assertion over the proposal JSON runs *before* anything is
written. Accepted meaning was never re-derived from a builder's output.

**`--verify` reads the frozen prior, not the live artifact.** After acceptance the committed oracle
*is* the merged result; reading it and calling it "the prior" would make every preservation
comparison compare the artifact to itself. The prior is therefore
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1.json`, asserted
**first** by content SHA-256 `87864b6a…f46c` and Git blob `a729a797…7a2f` before anything is computed
from it. `frozen_three_batch_prior_untouched` is `true` in both modes; that fixture is byte-identical
to what it was and **no four-batch freeze was created**.

Acceptance mode's prior is the **live** artifact, pinned by content digest and Git blob. Re-running it
now stops at that pin before the generator executes and long before anything is written — verified by
running it: it refuses.

## Merged result

| collection | conditions-1 | hazards-1 | actions-1 | attitudes-1 | committed |
|---|---|---|---|---|---|
| spans | 185 | 96 | 182 | 24 | **487** |
| acceptance records | 185 | 96 | 182 | 24 | **487** |
| records | 16 | 6 | 13 | 4 | **39** |
| components | 54 | 15 | 37 | 3 | **109** |
| facts | 70 | 21 | 48 | 3 | **142** |
| prose bindings | 15 | 5 | 27 | 2 | **49** |
| relationships | 0 | 0 | 0 | 0 | **0** |
| references | 15 | 7 | 17 | 7 | **46** |
| provenance edges | 185 | 96 | 199 | 24 | **504** |

Facts are counted **recursively** — every object carrying a `family` discriminator, including facts
nested under component options — and reported as `merged_facts_recursive`. Each per-batch figure is
that same recursive count, so the column does sum to 142; a top-level `sum(len(c.facts))` over the
merged components gives **126**, because it drops the 16 facts that hang off component options.

Every prior batch record, acceptance record, span, representation element, obligation, schema anchor
and fact is preserved unchanged — reported element-wise with a count of missing elements beside each
collection, all **0**, and with `prior_facts_still_present` asserted separately. The four scopes are
pairwise disjoint. `validate_acceptance` returns **no findings**; the written artifact round-trips
exactly; it is written through `accepted_inputs_payload` in the same indent-2 / sort-keys / LF form
the file was already committed in. **One oracle file, extended** — never a second, which is what the
resolver's refusal of two artifacts per release requires.

**Schema anchors** keep `conditions-1` at schema 3, `hazards-1` at schema 5 and `actions-1` at
schema 7, where their reviews happened, and record `attitudes-1` at schema 8. The file now *declares*
schema 8, because that is the schema the newest acceptance was reviewed under. The **registered
succession** is retained in full: `3→4` → `4→5` → `5→6` → `6→7` → `7→8`, six collections verified at
each step, never collapsed into a transition the registry has no row for.

The three schema-8 components are reported by name with their handling and typed content, so the
acceptance states what the schema step was actually for:

| component | handling | fact | value | prose-bound |
|---|---|---|---|---|
| `attitude.indifferent/default_attitude` | `STRUCTURED` | `DefaultAttitudeFact` | `indifferent` | no |
| `attitude.friendly/influence_advantage` | `MIXED` | `AdvantageFact` | `advantage` | yes |
| `attitude.hostile/influence_disadvantage` | `MIXED` | `AdvantageFact` | `disadvantage` | yes |

Friendly and Hostile share one `roll`, asserted equal, and reuse `condition.charmed`'s accepted
composition rather than redefining it.

## Canonical order and acceptance order now disagree in both directions

`load_accepted_inputs` returns `batches` in **canonical id order**; `schema_anchors` is the only place
the artifact records **acceptance order**. With this batch the two lists differ at more than one
position for the first time:

```
batches        actions-1 · attitudes-1 · conditions-1 · hazards-1
schema_anchors conditions-1 · hazards-1 · actions-1 · attitudes-1
```

`actions-1` sorts first and was accepted third; `attitudes-1` sorts second and was accepted last.
This is a **note, not drift** — the divergence is the design, and it is now asserted directly:
`test_each_batch_still_states_the_schema_it_was_reviewed_under` asserts the two lists are *not*
equal, so a future round that read order out of `batches` fails instead of passing by coincidence.

## Three publication blockers closed, two asserted positively

`validate_representation` returns **exactly two** findings, and the run asserts the unresolved set is
**equal to** those two keys:

`glossary.concentration` · `glossary.speed`

They are asserted as present rather than merely tolerated. A run reporting zero would mean a target
had been **invented**, which is worse than the blocker it appears to remove — so the assertion is
written to fail in that direction too. `publication_blockers.still_blocked` is `true`; the corpus
stays incomplete and runtime-unpublished.

The prior carried **five** unresolved targets. `attitude.friendly`, `attitude.hostile` and
`attitude.indifferent` are now defined, and the run asserts the closed set is *exactly* those three —
`unresolved_before − unresolved_after == resolved_by_this_batch`. That closure is a **consequence of
accepting a complete source class, not the reason for accepting it**. `cross_batch_references_resolved`
reports seven newly-resolvable pairs in both directions: `action.influence` ↔ each of the three
attitude records, plus `glossary.attitude → action.influence`.

## Which committed checks changed, and why each had to

The acceptance moved facts, so **18 checks across 5 modules** stated something that is no longer true.
**No assertion was weakened or deleted**; each was retargeted at the authority the Owner accepted.

* **`test_committed_accepted_authority.py`** (14 of the 18) — new `ORACLE_IDENTITY`,
  `ARTIFACT_CONTENT_SHA256`, `ARTIFACT_BLOB`, `PROJECTION_UUID`, `PROJECTION_PAYLOAD_HASH`; an
  `ATTITUDES` count dict beside the other three, with `MERGED` still summed from all of them so a
  merged total that is right for the wrong reason still fails; four batch ids, four timestamps, four
  anchors, five lifts; the `attitude.*` record keys and `glossary.attitude` asserted by name; and the
  new not-equal assertion on canonical-versus-acceptance order.
* **`test_the_committed_artifact_is_lifted_rather_than_rewritten`** changed *meaning* and is renamed
  to **`test_accepted_authority_is_lifted_rather_than_restamped`**, recorded here rather than quietly
  adjusted. `attitudes-1` was reviewed under schema 8 — the schema this build implements — so the
  committed artifact declares current authority again and the lift to current is a **no-op** that
  returns the inputs unchanged and records no crossing. The fail-closed refusal it used to
  demonstrate is **not weakened**: it lives on the frozen schema-3 specimen in the same test, which
  still refuses, still names `REPRESENTATION_SCHEMA_VERSION` in its finding, and still resolves
  through the real chain. Both halves are written against `REPRESENTATION_SCHEMA_VERSION` rather than
  a literal, so the next succession moves this test instead of quietly passing it — which is exactly
  what schema 8 did to the revision `actions-1` left behind.
* **`test_attitudes_1_frozen_prior.py::test_the_frozen_copy_and_the_committed_artifact_are_the_same_bytes_today`**
  — its own docstring said the next Owner acceptance would end it and that the assertion should then
  be *deleted*. Deleting it would leave the frozen copy unattached to the thing it was copied from, so
  it is **replaced** by the stronger claim the freeze existed to make checkable, and renamed to
  `test_the_committed_artifact_extends_this_frozen_copy_by_exactly_one_batch`: the frozen digest is
  unchanged, the committed digest differs, the added batch set is exactly `{"attitudes-1"}`, and every
  earlier batch record is **equal** across the two files. All other pins in that module describe the
  *frozen* file and are untouched; the committed artifact's pins live in
  `test_committed_accepted_authority`.
* **`test_schema_6_succession.py`** — only `COMMITTED_CONTENT_SHA256` moved. The `FROZEN_*` constants
  there describe the **two**-batch fixture and are untouched. The property is unchanged: a *lift* may
  not rewrite either file; an Owner acceptance may extend the committed one — which is what the
  module's own comment already anticipated.
* **`test_accepted_inputs.py`** / **`test_production_release.py`** — the committed batch list, the
  anchor list, and the record and span counts the production refusal is measured against
  (35/463 → 39/487). The refusal itself is unchanged and was re-run rather than assumed.

## Acceptance status reconciled at every site

Using `issue-5d-accepted-status-sibling-AUDIT.md` as the map of where status is stated — that audit
exists because a round missed a site — every listed site was re-read and each that described *current
production authority* was corrected:

| site | correction |
|---|---|
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` | schema-8 amendment's "nothing is accepted" kept **as written** and followed by a `Historical — superseded by Owner Decision 2026-09-10` block, matching the schema-7 precedent |
| `docs/architecture/known_unknowns.md` §5d | four batches, 39 records / 487 spans, two remaining unresolved targets |
| `src/afterworlds/ingestion/mechanical/oracle.py` module docstring | four batches, 39 records / 487 spans |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | four batches; records the schema-7→8 crossing as a lift rather than a restamp |
| `src/afterworlds/ingestion/mechanical/publication.py` | four batches, 39 records over 487 spans |
| `pyproject.toml` package-data comment · `MANIFEST.in` | four batches |
| `tests/…/test_runtime_production_release.py` module docstring | four batches |
| `tests/…/test_accepted_inputs.py` publication docstring | four batches, 39/487 |
| `issue-5d-attitudes-1-SELECTION-CHECKPOINT.md` | status line kept **as written** — it is the evidence of what was put in front of the Owner — under a superseded banner pointing here; its §7 prior pins still describe the untouched frozen prior |

Left alone deliberately: `issue-5d-actions-1-ACCEPT.py` and `issue-5d-actions-1-ACCEPTANCE-CHECKPOINT.md`
pin `87864b6a…`/`a729a797…`/`8c41b01e…` as the result **that acceptance** produced. Those are correct
historical statements and rewriting them would destroy evidence — the same distinction the sibling
audit draws.

## The required secrets gate

Extending the accepted-authority artifact keeps it inside the required `detect-secrets` hook. The
artifact gained **5** new findings by `hashed_secret`, all `Hex High Entropy String`, all
deterministic mechanical authority. **No credential is present.**

| line | value | what it is |
|---|---|---|
| 1642 | `proposal_identity` `c571dfd6…bff22` | the accepted proposal, matched against the loaded batch record |
| 1670 | `semantic_diff_hash` `c0680852…2323` | the `attitudes-1` batch's own diff hash |
| 4006 | schema `to_hash` `8a125f6c…afff` | the registered schema-8 hash |
| 14224 | `6a9629fc758f68b4` | provenance `target_key[2]`, `target_kind: "fact"` — recomputed from the loaded typed objects through `representation.fact_target_key()` |
| 14234 | `390ab69baf5b1cf2` | same, `attitude.indifferent/default_attitude` |

`attitude.friendly`'s fact key `383043486420f221` recomputes identically and is simply not flagged by
the entropy plugin. All three were verified by re-deriving them from the loaded typed objects, not by
reading them back out of the file.

The baseline was **not** regenerated with `detect-secrets scan --baseline`, which rewrites the whole
file. `.claude/review-notes/_rebaseline_accepted_oracle.py` rescans the one artifact through the
`detect_secrets` API, replaces that file's results block, and asserts before writing that every other
file's block and `filters_used`, `plugins_used` and `version` are identical. Verified after the write
against `HEAD`: **90 → 95** entries for the artifact, **5 added and 0 removed by `hashed_secret`**,
all 90 prior entries carried over, every other file's block byte-identical, and `generated_at` the
only other top-level key that moved. Because the artifact grew, 88 carried-over entries have a shifted
`line_number` — that is a coordinate change, not a secret change, which is why the delta above is
stated by `hashed_secret` rather than by raw entry equality. No detector, filter, plugin, glob
exclusion or inline allowlist changed.

`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <files>` — the exact
invocation `.pre-commit-config.yaml` declares — exits **0** on every changed file.

## Gates

| gate | result |
|---|---|
| `black src/ tests/` | clean (one file reformatted during the change, then clean) |
| `ruff check src/ tests/` | `All checks passed!` |
| `mypy src/` | `Success: no issues found in 225 source files` |
| `pytest tests/ingestion/mechanical tests/services/rules_authority -q --no-cov` | **2766 passed**, 0 failed, 197.14s — run attached to completion |
| `detect-secrets` pre-commit hook form | exit **0** |

The full suite and PR preparation are Codex's after handoff, per the governing instruction; no
model-owned background full suite was started.

## Architecture Notes

**No drift from design principles.** Acceptance went through the single native `accept_proposal` seam;
the accepted representation is carried by identity through the registered schema-7→8 lift rather than
rewritten; evidence never became identity; the oracle identity stayed blind to reviewer and timestamp
while the two file-level pins covered them; and the corpus is honestly reported as incomplete and
unpublished.

One process deviation from the `actions-1` precedent, stated rather than papered over: **there is no
`attitudes-1` review-scope manifest**, so the independent cross-check is a probe document without a
span list, and the accepted scope comes from the proposal alone. Scope was verified against the probe
on the fourteen fields it does carry.

## Stop conditions honoured

`accept_proposal` called exactly once, for exactly the authorized batch and scope · the reviewed
proposal and the frozen three-batch prior fixture byte-identical afterwards · all earlier accepted
meanings, batch evidence, fact keys, provenance coordinates and original schema anchors preserved ·
accepted meaning never regenerated from a builder's output · no schema broadened, no settled meaning
revisited, no reference target fabricated · no partial acceptance: all 24 spans or none · only checks
whose accepted-authority expectations actually changed were touched · no four-batch frozen prior
created · nothing published, activated or retired · nothing pushed, branch not merged, #137 not
closed · no further corpus batch begun · the existing checkout and every retained review artifact
kept.
