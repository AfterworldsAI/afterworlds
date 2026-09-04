# CRD Issue 5d — bounded sibling audit: acceptance-proof and determinism evidence

**Defect family.** *A proof reports success without having compared what it claims to compare —
because the value it measured is not the value it names.*

**Trigger.** Third instance in this batch's history, which is the boundary condition in `CLAUDE.md`.

| # | Instance | How it reported success falsely |
|---|---|---|
| 1 | `determinism.sha256` built by walking a `set` | The audit was not byte-stable across processes, while the run asserted it was — the comparison was real, the *thing compared* varied |
| 2 | The determinism child wrote an audit without the determinism section | The parent compared an intermediate artifact and then wrote a different one, so the proof did not cover the file that ships |
| 3 | `--verify` preservation (this round) | `conditions_1_payload_elements_present` was a dict holding one explanatory string; `all()` over it is `True` for no reason. And the "prior" it measured was the merged file |

The family is not "a wrong hash". It is **a label that outruns its evidence** — a name asserting a
comparison that the code beneath it did not perform.

**Scope discipline.** This audit controls scope; it does not expand it. Nothing outside the five
named surfaces was changed, and the accepted artifact, the proposal and the audit were not touched.

---

## The five surfaces, each put to the family's own test

The test: **can this row report a true-looking value without the comparison it names having
happened?**

### 1. Hash labels in the report

| label | measured | disposition |
|---|---|---|
| `prior_artifact_sha256_before` / `_blob_before` | **the merged artifact** — the label said "prior", the value was the result | **patched** — renamed `prior_artifact_content_sha256` / `prior_artifact_blob`, sourced from `PRIOR_PATH`, and a `prior_artifact_source` field now names the file so the label cannot drift from the value again |
| `accepted_artifact_sha256` / `_content_sha256` / `_blob` | the merged artifact, correctly | already safe |
| `proposal_sha256` / `proposal_blob` | the proposal file, asserted unchanged across the run | already safe |
| `accepted_oracle_identity` | `oracle_identity(RESULT.oracle)` | already safe |
| `proposal_payload_hash` | `hash_obj(proposal_payload(...))`, asserted equal to the identity | already safe |

### 2. Every reported preservation Boolean

| entry | before | disposition |
|---|---|---|
| `conditions_1_payload_elements_present` | a dict with one string key under `--verify`; `all()` → `True` | **patched** — one real per-collection Boolean over six collections in both modes, plus `missing_prior_elements` counting what is absent, plus an assertion that six collections were actually compared |
| `conditions_1_batch_record_*` | count-and-field checks under `--verify` | **patched** — full record equality against the frozen prior |
| `conditions_1_acceptance_records_*` | count + reviewer set + one timestamp | **patched** — list equality over all 185 records; a count is not preservation, since 185 records with a rewritten reviewer is still 185 |
| `conditions_1_spans_*` | count + id set | **patched** — list equality over all 185 spans |
| `conditions_1_obligations_preserved` | `len(obligations) == 22` under `--verify` | **patched** — every prior obligation present in the merged payload |
| the in-memory byte-identical prefix | acceptance-only, correctly: there is no in-memory merge under `--verify`, and the serialized order is canonical rather than prior-first | already safe — the one claim that is honestly mode-specific, and it says so in place |
| merged element counts per collection | real | already safe |

### 3. Acceptance-evidence immutability

`oracle_identity` is content-only **by design** — reviewer and timestamp are evidence, not identity,
so re-reviewing an unchanged classification must not remint a projection. The consequence is that
pinning it alone leaves reviewer, timestamp, batch rule, resolved scope, anchors and lifts
unprotected: an edit to any of them is invisible to it.

**Patched, in two places.** `ACCEPT.py` asserts the merged file's content SHA-256, its Git blob
**and** the oracle identity. `test_committed_accepted_authority.py` gains a permanent regression:
`test_the_whole_acceptance_record_is_pinned_not_only_the_oracle` pins the same three and asserts the
evidence beside them, and
`test_the_oracle_identity_alone_would_not_have_caught_an_evidence_edit` demonstrates the gap **in
memory** — a forged reviewer leaves `oracle_identity` unchanged while the payload differs — without
mutating the committed artifact.

### 4. Checkpoint claims corresponding to those assertions

| claim | disposition |
|---|---|
| *"`--verify` re-checks every post-acceptance assertion"* | **patched** — it did not; the checkpoint now states exactly what is compared, against which file, and records the corrected claim rather than replacing it |
| the merged-count table, anchors, lifts, reference resolution, validator results | already safe — each is executed and each matches |
| *"asserted as a byte-identical prefix on the in-memory merge, and as element-wise presence plus exact counts on the file"* | already safe — accurate before and after |

### 5. The changed legacy-fixture test documentation

| module | stale text | disposition |
|---|---|---|
| `test_accept_across_schema_succession.py` | *"on the real committed artifact"* — it reads the frozen fixture | **patched** |
| `test_committed_accepted_authority.py` | *"it is not built as current authority here — `validate_schema_binding` refuses that"* — the preceding test proves the opposite | **patched** |
| `test_production_release.py` | *"covers 16 condition records"* — it covers 22 | **patched** |
| `test_schema_version_legality.py` | `LEGACY_PATH` defined and documented twice | **patched** — one definition, the accurate one |
| the other nine repointed modules | comment and constant name both say `LEGACY_PATH` / "legacy specimen" | already safe |

---

## Dispositions

**14 patched · 9 already safe · 0 out of scope · 0 owner decisions.**

No check was loosened, no assertion deleted, and no pinned identity moved. The accepted artifact, the
proposal, the audit and the frozen fixture are byte-identical throughout.

## What this audit deliberately did not do

* It did not rerun the one-time acceptance, and it did not modify the accepted artifact — the
  evidence-edit demonstration is done on an in-memory copy for exactly that reason.
* It did not change the proposal, the audit, the schema, the policy, or any mechanical meaning.
* It did not weaken the acceptance-only prefix check into something that would pass under `--verify`;
  that claim stays mode-specific and says why in place.
* It did not begin `actions-1`, and it published, activated, retired and merged nothing.

## The rule this family leaves behind

**A reported Boolean must be the result of the comparison its name describes, and a reported digest
must come from the file its name describes.** Where a proof cannot make a comparison in some mode,
it says so in that mode's own words rather than emitting a value that reads as success.
