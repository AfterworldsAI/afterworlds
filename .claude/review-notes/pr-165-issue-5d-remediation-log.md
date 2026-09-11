# PR #165 — CRD Issue 5d `areas-of-effect-1` remediation log

Round 1, at head `2d5982a`. One P2 defect and two report inaccuracies. The accepted artifact,
the proposal, the frozen prior, the recorded acceptance metadata and the schema pin are
**unchanged**; independent native replay had already reproduced the complete accepted result
byte for byte, and nothing here reopens it.

| Identity | Value | State |
|---|---|---|
| `oracle_identity` | `8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40` | unchanged |
| artifact content SHA-256 (canonical LF) | `9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738` | unchanged |
| artifact Git blob | `467fcc62c8fb64e54cf74e73a6f55c384129eef7` | unchanged |
| proposal identity | `d602f4e59ab90dbb04852661f78f03e2e311025e80be03f39f4b324f2c6d6878` | unchanged |
| schema 9 pin | `f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e` | unchanged |
| frozen four-batch prior | blob `2346404005618b0389b4e4f66d2e96c5c35b200f` | unchanged |

---

## 1. Incomplete acceptance verification — P2

**The finding, restated as the defect.** `issue-5d-areas-of-effect-1-ACCEPT.py --verify` never
rebuilt the thing it claimed to check. Its `else:` branch read the committed proposal JSON,
hashed it, and built a small `_Reviewed` record per span — no `MechanicalProposal`, and
`accept_proposal` was never called in that mode at all. Everything after it loaded the
committed artifact and asserted *sampled* properties of it: the three identity pins, the
per-collection counts, the preservation sets, the blocker set, the diff tally. The checkpoint
and the PR both said it "re-derives the merge". It did not.

**Why sampling is not enough here, demonstrated rather than argued.** `resolved_scope` is the
one field acceptance retains verbatim; spans, diffs and every representation collection are
canonicalized on serialization. So accepting the *identical* span set in a different order
produces an artifact with:

* the same `oracle_identity` — acceptance evidence is deliberately outside it;
* the same counts in every collection, the same dispositions, the same schema anchors and
  lifts, the same unresolved citation targets, and no `validate_acceptance` findings;
* **different bytes**.

Every property the old `--verify` sampled agrees. That is the gap, and it is the exact shape
the finding names, because the generator emitted the scope in **manifest clause order** while
the proposal JSON sorts its spans canonically — the old branch derived the scope from the
latter.

### The fix

`--verify` now reproduces the full expected artifact from retained inputs and compares it
completely, writing nothing:

1. **Reconstructs the reviewed proposal** from the committed proposal JSON, through the
   loader's own field parsers (`oracle._span`, `oracle._representation`) rather than a second
   hand-written reader, then **proves it is that proposal** by round-tripping the result
   through `proposal_payload` back to the committed bytes and re-deriving the pinned proposal
   identity. A field the reconstruction failed to carry fails there instead of passing as a
   subset.
2. **Re-derives the accepted scope in its recorded order** from
   `issue-5d-areas-of-effect-1-source-manifest.json`, walked in file order, span ids computed
   through the same `derive_span_id` the generator uses. The manifest is pinned in ACCEPT.py by
   the same canonical-LF digest the generator asserts, `5932c353…0d8b9c`. The order is **not**
   read back from the artifact — an expected value copied from its own subject would make the
   comparison vacuous.
3. **Calls `accept_proposal`** over the frozen four-batch prior, in both modes. Only the
   *writing* stayed conditional.
4. **Compares byte for byte**, before the three identity pins rather than after, so the total
   comparison cannot be read as a consequence of them. A failure reports the top-level keys
   that differ.

The scope is not trusted from the manifest either: acceptance mode asserts the generator's
emission order equals the manifest order, verify mode asserts the manifest names exactly the
spans the reconstructed proposal proposed, and `accept_proposal` itself refuses a scope span the
proposal did not propose.

**What was not changed.** The accepted scope was not reordered to suit the verifier — the
recorded order is the manifest's and it is what both modes hand over. No acceptance or schema
redesign, no new private-file dependency: every input either mode needs is a tracked repository
file. The generator is still not run under `--verify`, because it writes the proposal and the
audit files and a verification that writes has verified nothing.

One consequence worth noting: the prior-prefix check that was previously guarded
`if not VERIFY_ONLY` — the "one claim that is acceptance-only" — is no longer acceptance-only,
because verification now computes the same in-memory merge. The guard is gone and the check
runs in both modes.

### Regression coverage

`tests/ingestion/mechanical/test_areas_of_effect_1_acceptance_reproduction.py`, four tests,
written as a **second independent implementation** that imports nothing from the ACCEPT script:

| Test | Claim |
|---|---|
| `test_the_committed_merge_is_reproducible_from_the_retained_inputs` | proposal + manifest + frozen prior → `accept_proposal` → serialized bytes equal the committed artifact |
| `test_the_recorded_scope_order_is_the_manifests_and_not_the_proposals` | the two candidate orders are the same span set and genuinely different, so the test above is not passing on a coincidence |
| `test_a_difference_the_sampled_properties_miss_is_still_refused` | the canonical-order merge matches the pinned `oracle_identity` and every sampled property, and the byte comparison still refuses it; the only differing field is `resolved_scope` |
| `test_the_merge_refuses_a_scope_the_reviewed_proposal_did_not_propose` | the manifest cannot become an unchecked second source of scope |

The one input the tests take from the artifact is the batch's recorded `rule` prose, which is
retained acceptance evidence with no second copy in the repository. The Owner's verbatim
authorization is a literal in the test module and is asserted to be inside it. Everything the
identity covers is rebuilt.

### Proof, run on this branch

```
$ python .claude/review-notes/issue-5d-areas-of-effect-1-ACCEPT.py --verify
exit 0
reconstructed_artifact_byte_identical_to_committed  true
accepted_artifact_matches_pinned_merged_identity    true
frozen_four_batch_prior_untouched                   true
source_manifest_sha256  5932c353dfd7d67756eeac72876705f5a60c5f2fe8175a7e78fdc0eb8c0d8b9c
scope.order_source      manifest clause order, re-derived from the pinned inventory

$ git status --porcelain -- src/ tests/ \
    .claude/review-notes/issue-5d-areas-of-effect-1-source-manifest.json \
    .claude/review-notes/issue-5d-batch-areas-of-effect-1-PROPOSAL.json \
    .claude/review-notes/issue-5d-batch-areas-of-effect-1-audit.json
(empty)
```

The refusal, shown on an unmodified artifact: an untracked copy of the script with
`RESOLVED_SCOPE` taken from the proposal's canonical order instead of the manifest's exits 1 on
the new comparison —

```
AssertionError: the merge rebuilt from the retained proposal, the pinned manifest and the
frozen prior is not the committed artifact; top-level keys that differ: ['acceptance']
```

Only the *expected* side moved there; the committed artifact is byte-unchanged and still
satisfies all three identity pins, which is what
`test_a_difference_the_sampled_properties_miss_is_still_refused` asserts directly.

The stale acceptance rerun still refuses, and refuses first:

```
$ python .claude/review-notes/issue-5d-areas-of-effect-1-ACCEPT.py
exit 1
assert _prior_content_sha == PRIOR_CONTENT_SHA256
AssertionError: (.../oracles/srd-5-2-1-corpus-36b786d8-fa2.json,
                 '9f380251…dec1e738')   # digest elided as elsewhere in this note
```

before the generator executes and before anything is written; `git status` is unchanged after
it.

---

## 2. Report inaccuracy — prose bindings

The PR acceptance-criteria table said the proposal "carries prose bindings and provenance for
all 43 spans". The batch has **zero prose bindings and 43 provenance claims** — every component
is `STRUCTURED`, so no clause is carried as quoted prose. `BATCH_COUNTS` in the ACCEPT script
and the checkpoint's per-batch counts table both already said 0; only the PR sentence was wrong.
Corrected to state the real figures.

---

## 3. Report inaccuracy — dependency-finding chronology

The PR and the checkpoint both said every `pip-audit` finding *predates* this change. The only
evidence offered was that the dependencies are unchanged, which does not establish when an
advisory was published. Supporting it would mean auditing `main` in the same environment and
reading advisory dates; that is not this change's work and was not asked for.

Both are now qualified to what was verified:

* the local audit is **nonzero, exit 1**, 22 findings across 9 packages, reported at that value;
* `git diff origin/main...HEAD` touches **no lock file, no requirements file and no dependency
  specification** — `pyproject.toml`'s only modification is a package-data comment;
* **no audit configuration, ignore list or suppression** was added or changed.

No dependency maintenance, no version bump, no suppression, no gate weakening.

---

## Sibling audit

**Not triggered.** This is review round 1 on this PR; the defect family (a verification that
samples where it claims to reproduce) has been hit once, and a narrow fix has not been followed
by a sibling. The `attitudes-1` and `actions-1` ACCEPT scripts are the obvious structural
siblings and were **not** inspected or run — their accepted authority is settled and rerunning
them is out of bounds. Disposition: **out of scope**. If a second round hits the same family,
that is the trigger to audit them as a set.

---

## Not done

Nothing here merges, publishes, activates, retires, changes accepted authority or begins another
batch. The PR stays **draft**; the Owner merges. Parent tracking issue #137 remains in progress.
