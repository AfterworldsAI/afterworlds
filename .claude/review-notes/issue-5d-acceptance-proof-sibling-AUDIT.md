# CRD Issue 5d — bounded sibling audit: acceptance-proof and determinism evidence

**Defect family.** *A proof reports success without having compared what it claims to compare —
because the value it measured is not the value it names.*

**Trigger.** Third instance in this batch's history, which is the boundary condition in `CLAUDE.md`.

| # | Instance | How it reported success falsely |
|---|---|---|
| 1 | `determinism.sha256` built by walking a `set` | The audit was not byte-stable across processes, while the run asserted it was — the comparison was real, the *thing compared* varied |
| 2 | The determinism child wrote an audit without the determinism section | The parent compared an intermediate artifact and then wrote a different one, so the proof did not cover the file that ships |
| 3 | `--verify` preservation (round 3) | `conditions_1_payload_elements_present` was a dict holding one explanatory string; `all()` over it is `True` for no reason. And the "prior" it measured was the merged file |
| 4 | The proposal and merged-artifact pins (#161 Codex round 1) | `PROPOSAL_SHA256` and `MERGED_SHA256` hold **canonical-LF** digests, and the assertions compared the **raw on-disk** digest against them. On a CRLF checkout, byte-identical JSON fails — verification exits before its acceptance checks and reports the checkout as an unreviewed edit |
| 5 | The regeneration generator's prior (#161 Codex round 2) | The generator read the **live accumulating oracle** as its review prior and pinned that file's *pre-acceptance* digest. Once the Owner accepted `hazards-1` into it, the generator refused to run at all against the committed tree — a retained proof that could no longer re-derive either artifact it is retained to prove. The refusal had been *described* as a deliberate freeze, which is the family's signature: prose asserting a property the code beneath it did not have |

The family is not "a wrong hash". It is **a label that outruns its evidence** — a name asserting a
comparison that the code beneath it did not perform.

**Instance 4 is why this audit is being corrected rather than merely extended.** Round 3 asked of
every hash label *which file did this value come from* and never asked *which digest class is it*.
Provenance was checked; class was not. That is how a correct value came to sit under a name that
decided verification wrongly — and it is why the two rows below moved from "already safe" to
"patched" on re-examination.

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
| `accepted_artifact_sha256` / `_content_sha256` / `_blob` | the merged artifact — right file, **wrong digest class**: the reported and asserted `..._sha256` was the raw on-disk digest, compared against a canonical-LF pin | **patched (round 3 marked this "already safe"; that disposition was wrong)** — the pin is renamed `MERGED_CONTENT_SHA256`, the assertion reads `_accepted_content_sha`, and the raw digest is reported as `accepted_artifact_raw_sha256_diagnostic` and decides nothing |
| `proposal_sha256` / `proposal_blob` | the proposal file, asserted unchanged across the run — same class error | **patched (round 3 marked this "already safe"; that disposition was wrong)** — `PROPOSAL_CONTENT_SHA256`, asserted against `_proposal_content_before` / `_after`, with `proposal_raw_sha256_diagnostic` beside it |
| `accepted_artifact_matches_pinned_merged_identity` | the raw digest was one of its three terms | **patched** — the Boolean is now canonical content SHA-256 **and** Git blob **and** oracle identity; no raw digest is a term |
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

**Round 3:** 14 patched · 9 already safe · 0 out of scope · 0 owner decisions.

**Round 4 (#161 Codex round 1, digest class):** 3 further patched — the two rows above that round 3
marked "already safe" in error, plus the composite Boolean built on one of them. No new surface was
opened; the same five surfaces were re-examined against the sharpened question.

**Round 5 (#161 Codex round 2, mutable prior):** 1 patched · 3 already safe. The generator now derives
from an immutable prior and executes from the final committed tree; the other retained proofs read
the live artifact as their subject rather than as an input, which is a different relationship and
does not expire.

No check was loosened, no assertion deleted, and no pinned identity moved. The accepted artifact, the
proposal, the audit and the frozen fixture are byte-identical throughout.

## What this audit deliberately did not do

* It did not rerun the one-time acceptance, and it did not modify the accepted artifact — the
  evidence-edit demonstration is done on an in-memory copy for exactly that reason.
* It did not change the proposal, the audit, the schema, the policy, or any mechanical meaning.
* It did not weaken the acceptance-only prefix check into something that would pass under `--verify`;
  that claim stays mode-specific and says why in place.
* It did not begin `actions-1`, and it published, activated, retired and merged nothing.

## Round 5 — the other retained executable proofs, swept for the same coupling

The question, asked of every retained executable proof in the repository: **does this proof read, or
pin, authority that later acceptances will change?** Three tracked scripts under
`.claude/review-notes/`, plus the test module that pins the same artifact.

| proof | what it reads / pins | disposition |
|---|---|---|
| `issue-5d-hazards-1-schema5-REGEN-generator.py` | read the live oracle as `PRIOR` and pinned its pre-acceptance digest | **patched** — reads the frozen `legacy_conditions_1_unanchored_schema3.json`, pinned by content SHA-256, Git blob, batch list and schema version; the live oracle is retained only as a raw-byte mutation sentinel, absent from the audit entirely |
| `issue-5d-hazards-1-ACCEPT.py` | loads the live oracle and pins its merged identity | **already safe** — the live artifact is this proof's **subject**, not an input: `--verify` exists to check that the committed acceptance is the one the Owner made. Its prior already comes from the frozen fixture. **Stated so it is not a surprise:** accepting `actions-1` will move the merged artifact, and this script's merged pins are then a record of a superseded state — which is correct for a one-time acceptance record, and is exactly why the *generator* must not work that way |
| `repin-schema-4.py` | nothing under `oracles/` | **already safe** — its own docstring names the committed production oracle as something it deliberately never touches |
| `tests/…/test_committed_accepted_authority.py` | pins the merged artifact's identities | **already safe** — same subject-not-input relationship, and it is the test whose job is to fail when accepted authority changes without review |

**The distinction the sweep turned on:** an artifact a proof *checks* may legitimately be the live
one; an artifact a proof *derives from* must be immutable, or the proof expires on someone else's
schedule. The generator was deriving from a live artifact and calling the resulting refusal a design
choice.

## The rule this family leaves behind

**A reported Boolean must be the result of the comparison its name describes, and a reported digest
must come from the file its name describes — and be the digest class its name describes.** Where a
proof cannot make a comparison in some mode, it says so in that mode's own words rather than emitting
a value that reads as success.

The second clause is what round 3 missed. A digest has a *provenance* (which file) and a *class*
(raw bytes, canonicalized content, or Git blob), and checking only the first leaves a correct number
under a name that makes the wrong comparison. Every digest label in the acceptance record now states
its class, and only checkout-independent classes decide anything: raw digests are labelled
`..._raw_sha256_diagnostic` and appear in the report as evidence, never in an assertion.

**Round 5 adds a third clause: a retained proof must derive from an immutable input.** A proof whose
input accumulates stops being reproducible the moment somebody else's work is accepted, and the
failure arrives disguised as a deliberate refusal. The test is temporal: *will this proof still
execute from the committed tree after the next batch is accepted?* If the answer depends on nobody
accepting anything, the input is wrong — pinning the mutable artifact's current identity only moves
the expiry date. Derive from a frozen artifact; keep the live one as a sentinel if the proof needs to
show it touched nothing.

**Executed, not argued.** `test_the_pinned_identities_survive_a_crlf_checkout_and_the_raw_digest_does_not`
in `tests/ingestion/mechanical/test_committed_accepted_authority.py` builds a CRLF copy of the
committed artifact in `tmp_path`, asserts the raw digest genuinely moves, and asserts the canonical
digest, the Git blob, the loaded payload and the oracle identity do not. The real case was run too:
`ACCEPT.py --verify` in a disposable worktree whose proposal and accepted JSON had been converted to
CRLF. Neither the CRLF copy nor the worktree is committed — a second artifact claiming one release is
what the resolver refuses outright.
