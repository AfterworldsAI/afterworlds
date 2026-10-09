# CRD Issue 5d — replacement-dependent tests (#132, #137)

Handoff for Codex's independent review. It covers moving the live acceptance,
replay, proposal and test dependencies onto the Owner-approved replacement
chain, `srd-5-2-1-corpus-626c83f8-209.json` (SHA-256
`7b1d6f43c322adbd662f94cb941c58a9ec54dde0fca5bef42465c940459abdd8`, recorded
2026-09-24T10:02:36Z). Nothing is committed, pushed, published or activated.
`issue-5d-source-correction-REPLACEMENT-PACKET.md` was not touched: its
scanner-status edits were denied and stay unresolved. `.secrets.baseline` is
unchanged at `ba147840…099f`, the Owner's staged pass.

## Changed dependencies

- **New `tests/ingestion/mechanical/_replacement_chain.py`.** It loads
  `issue-5d-source-correction-REPLACEMENT-ACCEPT.py` and exposes:
  - `through(batch)`: the approved chain, cached, up to and including a batch
    and its resolutions;
  - `accepted_only(batch)`: that batch's `accept_proposal` step before its
    resolutions;
  - `proposal_path` and `identity`: the REGEN proposal paths and identities
    from the script's `BATCHES`, not re-typed literals.
- **The twelve `test_*_acceptance.py` files.** The per-batch `ACCEPT.py`
  loaders are replaced with `through(prev)`, `through(BATCH)` and
  `accepted_only(BATCH)`.
  - Timestamps, rule, reviewer and authorization reference are asserted
    against the one approval: `REPLACEMENT.ACCEPTED_AT`, `APPROVAL` and
    `AUTHORIZATION_REFERENCE`.
  - `test_character_origins_feats_acceptance` holds the final bytes:
    `serialize_accepted_inputs(through(BATCH))` is byte-equal to the committed
    oracle, and its SHA is `7b1d6f43…`.
- **The ten `test_*_proposal.py` files.** Proposal paths, identities and file
  digests come from the chain; priors are `through(prev)`. combat-turn-1 and
  damage-and-hit-points have no proposal tests.
- **Listing and authority tests.** `test_committed_accepted_authority` builds
  its twelve proposal paths with `proposal_path`. The committed-directory
  listings in `test_committed_accepted_authority`, `test_accepted_inputs`,
  `test_oracle` and `test_packaging` name `626c83f8-209`, and
  `test_source_release_readiness` binds the new package and release.
- **Docs.**
  - `oracles/README.md`'s clean-restart heading names the new file, package and
    release. A paragraph says the per-batch bullets describe content, while
    their identities, digests, commits and `--verify` commands belong to the
    retired chain.
  - Retired per-batch material was later removed from those bullets: the
    `--verify` replay sentences and the intermediate-pin claims.
  - `issue-5c-5d-clean-restart.md`'s uncommitted supersession paragraph no
    longer says `883aabdf` "stays the accepted authority".

## Assertions changed, and why

The changes below are the whole of what the tests lost; nothing else was
relaxed.

- **Eleven intermediate-bytes tests dropped.** `test_the_seam(s)_still_records_the_committed_N_batch_bytes`
  goes in every acceptance file except origins-feats, and
  `…_retained_and_still_reproduce` becomes `…_retained`.
  - Each pinned a per-batch intermediate SHA of the retired chain. The approval
    pins only the final bytes and has no intermediate digests, so new pins
    would be unapproved literals.
  - The final-bytes replay above covers the whole chain. The per-batch
    "retained" tests still check that every prior batch survives unchanged.
- **Per-batch rule literals removed.** The Owner's verbatim per-batch rules are
  not lost: they remain in each `issue-5d-<batch>-ACCEPT.py` at `5ed0657`. The
  replacement records one rule, "I approve this exact replacement packet.",
  and the tests assert that rule.
- **Chunk-order counts moved.** `character_creation_foundations` goes from
  `(100, 22)` to `(100, 31)`, and Equipment's `MULTI, UNLIKE_CHUNKS` becomes
  `119, 68`.
  - Chunk ids are `uuid5(package_uuid, leaf_id)` (`corpus/transform.py:110`), so
    the order of chunk ids is package-specific.
  - The real pin, `printed == sorted(printed)` per component, is unchanged and
    passes.
- **`len(raw)` pins** now use the regenerated files' sizes.
- **Per-batch timestamp ordering collapsed.** The old tests asserted distinct,
  ordered per-batch stamps. They used `len(prior_stamps) == N`,
  `ACCEPTED_AT not in prior_stamps` and `previous.RESOLVED_AT < ACCEPTED_AT`.
  The replacement records every batch and resolution under one stamp, so each
  file now asserts that the set of stamps is exactly `{REPLACEMENT.ACCEPTED_AT}`.
- **Authorization substring checks became equality.** `RULE in authorization_reference`
  and origins-feats' `DECISION_ITEM in …` are now
  `authorization_reference == REPLACEMENT.AUTHORIZATION_REFERENCE`.
- **Repointed, not dropped.** The generator-output equality
  `out.read_bytes() == <proposal>` is now checked against the REGEN proposal in
  all 10 files. The proposal identity and file digest are checked against the
  chain's `BATCHES`, and `batch_id` against `BATCH`.

Audit: `git diff -U0 -- tests/ingestion/mechanical | grep '^-\s*assert'`
gives 152 removed lines. Every one falls into a category above:
- the retired `ACCEPT` module loader;
- an intermediate SHA pin;
- a per-batch rule or stamp;
- an old proposal literal or digest, now repointed;
- the chunk count.

## Equipment (still UNACCEPTED)

`test_equipment_proposal.py` is untracked, like the rest of the Equipment work.
It now reads `issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json` (identity
`a581b388…`) over `through()`, which is held byte-equal to the committed oracle.

It is adapted to the corrected source:
- 21 food table rows;
- the Lodging groups under one two-column header;
- the "Airborne and Waterborne Vehicles" caption.

No Equipment semantics, drafts or scope were accepted or broadened. The tests
build the 43 drafts with `GEN.draft_resolutions` and do not read the DRAFTS
file.

## Removed (`git rm` by name unless noted)

| File(s) | Why retired now |
| --- | --- |
| `oracles/srd-5-2-1-corpus-883aabdf-462.json` | Binds the superseded release. Every consumer now reads `626c83f8-209`, and the directory listings require its absence. |
| 12 × `issue-5d-<batch>-ACCEPT.py` | They only loaded each other and the old proposals and oracle. No test, `src` or script consumer remains (grep of tracked and untracked files). |
| 12 × `issue-5d-<batch>-PROPOSAL.json` | Consumed only by those scripts. The REGEN proposals replace them. |
| `issue-5d-equipment-PROPOSAL.json` (untracked, `rm`) | The old-build Equipment proposal, replaced by the REGEN one. No consumer. |
| 11 × `issue-5d-<batch>-REVIEW-PACKET.md` | Retired under the Owner's current-purpose policy: they describe the superseded chain's proposals and scripts, and the approved replacement is the current authority. No src, test, script or doc depends on them. The only cross-reference was between two of the retired packets. |

**Kept.**
- The per-batch generators: the chain and the tests call them.
- The REGEN proposals and DRAFTS, and `REPLACEMENT-ACCEPT.py`.
- `issue-5d-core-play-dependencies-REVIEW-PACKET.md`, because accepted
  ADR-005d (line 1371) cites its §5 as the evidence for the citation-identity
  Owner decision. That is a live dependency. Its own replay references
  (`ACCEPT.py --verify`) are retired.
- The two `batch-proficiency` packets. They belong to another chain and are
  outside this work.
- The quarantined `36b786d8-fa2` oracle and its reproduction tests are
  untouched.

## Verification

Replay and headline counts:
- `REPLACEMENT-ACCEPT.py --verify` gives `verified srd-5-2-1-corpus-626c83f8-209.json 7b1d6f43…abdd8`,
  and `sha256sum` of the committed file matches.
- The artifact holds 12 batches, 136 records, obligations and review units,
  1016 spans and acceptance records, and 6 reference resolutions.
- The 91 unresolved references and 9 443 uncovered leaves are asserted through
  the production resolver in `test_character_origins_feats_acceptance`.

Gates:
- Black and Ruff are clean on `src/` and `tests/`. `mypy src/` is clean (235
  files).
- The authority, listing and readiness group passed 167/167, including
  `test_no_refused_candidate_is_selectable`.
- The full mechanical suite (`pytest tests/ingestion/mechanical -q --no-cov`,
  one run, final tree): **3771 passed, 14 skipped** in 11 min 38 s, exit 0.
  The skips are the existing quarantined-reconstruction skip
  (`tests/ingestion/conftest.py:144`) and the `build` importorskip in
  `test_packaging`, which predate this work.

## Scanner (no baseline change)

I ran `detect_secrets.pre_commit_hook --baseline .secrets.baseline` over this
work's changed and new files, excluding the denied packet. The baseline SHA was
unchanged before and after. It found 13 findings:

- **The ten known Equipment findings, deliberately excluded.**
  `issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json` has six, at 17461, 17462,
  17464, 17466, 17469 and 17472. The DRAFTS file has four, at 12–15.
- **Three new findings for a later Owner terminal pass:**
  - `tests/ingestion/mechanical/test_equipment_proposal.py:107`: the Equipment
    REGEN identity `a581b388…`.
  - `tests/ingestion/mechanical/test_character_origins_feats_acceptance.py:199`:
    the approved oracle SHA `7b1d6f43…`.
  - `.claude/review-notes/issue-5d-source-correction-REPLACEMENT-ACCEPT.py:171`:
    `fd19dcab…74fd`. This is the review manifest hash inside
    `AUTHORIZATION_REFERENCE`, which was filled in at recording. The staged
    baseline has 26 entries for this file but not this line. I cannot tell
    whether the pass missed it or the line changed after the pass.

The baseline still lists findings for 25 retired files: the 12 `ACCEPT.py`,
the 12 `PROPOSAL.json` and `srd-5-2-1-corpus-883aabdf-462.json`. They are
harmless to the hook, and pruning them is left to the Owner's pass.

## Working tree (nothing committed)

- **Staged:** the 36 `git rm` deletions (25 chain files and 11 REVIEW-PACKETs) and the Owner's `.secrets.baseline`. The baseline has no entries for the retired packets.
- **Modified, unstaged:** the test and doc files above.
- **Untracked, and must enter the same commit as the test changes:**
  - `_replacement_chain.py`;
  - `issue-5d-source-correction-REPLACEMENT-ACCEPT.py`;
  - the 12 batch REGEN proposals;
  - `issue-5d-reference-resolutions-REGEN-626c83f8-DRAFTS.json`;
  - `oracles/srd-5-2-1-corpus-626c83f8-209.json`.

  The tests import or read all of these, so a commit without them fails CI.
- **Keep out of that commit:** the Equipment REGEN proposal, its DRAFTS and
  `test_equipment_proposal.py`. They carry the ten excluded findings and the
  new `:107` one, so the hook refuses them by design. The hook would also
  refuse `REPLACEMENT-ACCEPT.py:171` and the origins-feats `:199` until the
  Owner's pass.
- Four stashes are preserved.
- The full-suite log is at `.claude/_rc/full-mechanical.log`, and the scanner
  output at `.claude/_rc/detect-secrets-hook.txt`. The suite ran detached with
  `run_in_background`, and its output was captured to that log. It was not
  run attached; I disclose this rather than run it a second time.

## Remaining blockers

- The three new scanner findings above, and the stale baseline entries, need an
  Owner terminal pass.
- `REPLACEMENT-PACKET.md` scanner-status edits are denied and unresolved.
  The file is left untouched and is stale: it still calls `883aabdf-462` the
  accepted authority and the replacement UNACCEPTED. This file and the
  Equipment packet record the current state.
- `pip-audit` is deferred and not green; no dependency was changed.
- Nothing is committed. Equipment and the rest of 5d wait for Codex review.
