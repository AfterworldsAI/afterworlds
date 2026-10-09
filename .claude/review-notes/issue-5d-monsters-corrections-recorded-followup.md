# CRD Issue 5d — Monsters corrections recorded: follow-up (#132, #137)

**Status: RECORDED in the working tree, uncommitted.** Nothing was committed, pushed, merged, published or
activated. No shared DB or Chroma was written. The partial-publication block stays. Animals is not in this run.
Codex verifies this independently. Written 2026-09-28.

## Authorization recorded

- **Approval, verbatim:** "I accept both exact items in the corrected Monsters packet and approve their reference
  resolutions, retaining 317 reference findings and the partial-publication block."
- **Answers:** `monsters-corrections-owner-review.md` in
  `C:/Users/raven/.codex/visualizations/2026/09/21/01a0c27d-eef6-78f0-82cb-89e991b26cfe` (SHA-256
  `8b9437d9e11a230973217152b626b3b8306bc54738100abc70db995f9124958b`, read only). The helper exposes it as
  `OWNER_REVIEW_SHA256` and names it in every `authorization_reference`.
- **Request:** `monsters-corrections-recording.md` (SHA-256
  `2a520e97d97e6574b79bbc637cef35a80e7e8583381568199e375bd077961941`). `source-error-policy.md` applies.
- **Reviewer:** `Ravenlok (Owner)`, the chain's `OWNER` constant. No simulated reviewer or time was copied into
  the recorded file.

### Manifest: 32 rows checked, 30 approved

`.claude/_rc/msc/rec_manifest_check.py` exited 0 before and after the writes. All 32 rows matched disk:

- §4's 28 rows: the 27 REGEN proposals/DRAFTS plus `issue-5d-monsters-corrections-REPLACEMENT.py`;
- §5's four: the Monsters proposal, drafts, generator and source.

The approval covers 30 of them (the 28 plus the Monsters proposal and drafts). The generator and source rows are
checked but are not approved items. The oracle was still `fc62…5a62` and the release DB `ffeb731f…17e0`.

**Rerun after this run's edits:** raw exit **1** (`.claude/_rc/msc/manifest-final.log`). 32 entries, 1 bad: the
Monsters generator is now `92eed920…` because of the lazy-import edit (see Generators below). This mismatch is
expected. All 30 approved rows still match, and so do the source row, the oracle `fc62…5a62` and the release DB
`ffeb731f…17e0`.

The review packet elides the REPLACEMENT helper hash. In full it is
`fb11995a067bd52ca5227508d4a7da7be0059b901789c9a82d76b3c9a0cdc568`, unchanged since the check.

## Recording

`.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py` (SHA-256 `ddae94c7…796e126d`) uses the native
seams only: `accept_proposal` then `resolve_references`, with `serialize_accepted_inputs` /
`load_accepted_inputs`. It fails closed on any state it does not recognize. It re-exports the REPLACEMENT helper's
pins (`RELEASE`, `TAG`, `BATCHES`, `DRAFTS`, the `MONSTERS_*` pins) as aliases. The test hub and the two
generators bind to it alone.

It records the fresh 20-batch replacement first, over no prior. Then it records Monsters over that.

| Step | Real execution UTC | Oracle SHA-256 after |
|---|---|---|
| `record` (20 batches, 1099 resolutions) | 2026-09-28T09:39:56Z | `86652ac9…` (chain) |
| `accept-monsters` (414 records) | 2026-09-28T09:41:27Z | intermediate |
| `resolve-monsters` (83 resolutions) | 2026-09-28T09:42:23Z | `02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54` |

- **Release:** `67c81736-15fd-5e82-8523-e84922f0a7c6` / `5.2.1-corpus.3fe24ff6-4e3`.
- **File:** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json` (untracked).
- **Order:** `--simulate` ran first (exit 0) and wrote nothing.

### Disclosure: `record` exited 1 after writing

`record` wrote `86652ac9…` and then exited **1**. The post-write `_state()` compared the batch tuple order
positionally, but the artifact serializes batches canonically.

I made two helper edits:

- the check now compares sorted batch-id sets;
- the prefix check filters by batch id.

I did not re-record. The written bytes were reused as the intermediate: `--verify` rebuilds them natively at the
times it reads back (09:39:56Z) and matches them byte-for-byte. `accept-monsters` and `resolve-monsters` each
exited 0.

### Replay

`--verify` was rerun on the final helper and exited 0 (`.claude/_rc/msc/verify-final.log`):

```
state resolved 02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54
  times (chain, accepted, resolved) ('2026-09-28T09:39:56Z', '2026-09-28T09:41:27Z', '2026-09-28T09:42:23Z')
  every acceptance names the Owner and this decision True
  counts (batches, records, spans, units, resolutions) (21, 1664, 9589, 1364, 1182)
  resolution violations 0
  twenty-batch chain preserved True (20, 1250, 6450, 950, 1099)
  reference findings 317 leaf/uncovered 864
  other findings 0 []
  reloads to the same bytes True
```

The 20-batch prefix is preserved as a multiset, with its acceptances, identities, provenance and times unchanged.

## Live dependency move

**Hub.** `tests/ingestion/mechanical/_replacement_chain.py` (SHA-256 `3fc2d936…`) now loads the monsters-corrections
ACCEPT as `REPLACEMENT`:

- `through(batch)` is `owner_chain(ACCEPTED_AT, through=batch)`;
- `through()` is the 20-batch `recorded()`;
- `kept_whole` keeps the Magic Items obligation enlargement from the historical `issue-5d-magic-items-ACCEPT.py`
  (`MAGIC_ITEMS`).

`kept_whole` is only meaningful when `prior` predates magic-items. The magic-items committed test therefore uses a
full `_preserved` plus `kept_whole(prior, committed)`.

**Per-batch tests** now bind to the recorded authority:

- **gameplay-toolbox, magic-items, spell-descriptions and classes:** `ORACLE = REPLACEMENT.ACCEPTED_PATH`; prior
  from `through(...)`; the committed-oracle tests are rewritten to check the recorded times and authorizations and
  that the resolution payloads equal the DRAFTS. Their local copies of proposal hashes were removed.
- **readiness:** the pilot-authority set gains `monsters`, with 9589 spans and 1182 resolutions.
- **directory listings** (`test_accepted_inputs`, `test_committed_accepted_authority`, `test_oracle`,
  `test_packaging`): `srd-5-2-1-corpus-3fe24ff6-4e3.json` is added. The 574662e9 entries were **kept**, because
  retiring that file needs its own Owner authorization.
- **docstrings:** the acceptance-test docstrings name the new ACCEPT and file. Historical references are left as
  written.
- **monsters committed test** (failed in the targeted gate, fixed after):
  - `kept_whole(prior, committed)` becomes the full `_preserved`, as in magic-items;
  - the positional batch-list compare becomes a compare of canonical `acceptance.batches` payloads. The file
    serializes batches, and each batch's `diff`, canonically. A probe showed every one of the 20 batches differed
    only in `diff` order (`.claude/_rc/msc/probe_batches.py`).
- **`test_no_refused_candidate_is_selectable`** (failed in the targeted gate, fixed after): the expected identity set
  adds the 21 identities the new file names (from the hub's `BATCHES` plus `MONSTERS_IDENTITY`). The hub's
  `proposal_path` now points at `REGEN-3fe24ff6`, so the set also names the 17 `REGEN-574662e9` proposal
  identities for the still-present superseded file. The refused-identity check is unchanged.

### Sibling audit (two defect families, each hit twice)

| Family | Trigger | Siblings inspected | Disposition |
|---|---|---|---|
| `kept_whole` with a prior that already holds the Magic Items enlargement | magic-items, then monsters | all 10 `kept_whole(` callers | `patched` (magic-items, monsters); `already safe` for the rest. Each passes a prior composed before magic-items (`through(≤"gameplay-toolbox")`, or the pre-magic-items `FINAL`/`rebuilt`/`replayed`), so `obligation_delta` has an enlargement to find. All passed in the targeted gate. |
| Positional batch order against a reloaded file | `record` exit 1, then monsters | every `.batches ==` / `batch_id for b in … ==` compare under `tests/ingestion/mechanical` | `patched` (helper, monsters); `already safe` for the rest. They compare in-memory `owner_chain`/`accept_proposal` results, which keep acceptance order; or they already sort; or (`test_accepted_inputs.py:280/559`) they round-trip synthetic fixtures whose one-`diff` batches are already in canonical order. |

**Generators.** `current()` in the magic-items and gameplay-toolbox generators now reads the recorded chain lazily,
through `owner_chain(..., through="gameplay-toolbox" / "spell-descriptions")`. This is the same substitution
`.claude/_rc/msc/regen.py` made when it produced the approved REGEN proposals. The evidence is that the
magic-items proposal-bytes test (`committed_bytes`, which differed at index 467872 before the change) passes in the
targeted gate. Without the change, the tests composed over the old release and failed on stale chunk ids
(`text=None`, "not authoritative prose of release 67c81736…"). The
old `ORACLE_FILE`/`ORACLE_SHA256` constants stay as history. File hashes changed:

| Generator | SHA-256 now |
|---|---|
| `issue-5d-monsters-generator.py` | `92eed920…9e850781` (§5 manifest row was `760dfb96…`; lazy import edit after recording) |
| `issue-5d-gameplay-toolbox-generator.py` | `6090bc07…84cb930b45` |
| `issue-5d-magic-items-generator.py` | `6085b791…488eabc154` |

The approved proposal and DRAFTS bytes did not change.

**Pins.** The new release has one leaf fewer, from the reviewed Succubus merge. Every uncovered-leaf total drops by
exactly 1. Each changed primary pin carries the comment "One leaf fewer on ``3fe24ff6-4e3``: the reviewed Succubus
merge." The files touched:

- character-creation-foundations, character-origins-feats, checks-actions-rests, combat-damage-breaking,
  combat-turn-1, core-play-completion, core-play-dependencies, damage-and-hit-points, equipment,
  movement-closure, spellcasting, magic-items (5335/4003), spell-descriptions and classes (7656);
- their secondary `len(after) + n` totals;
- rules-glossary-completion (`(66, 8830)`, line 1064). The targeted gate did not cover it; the final
  `tests/ingestion` run caught it (the one failure there), and it was fixed after.

One further pin changed: the chunk-order count in `test_character_creation_foundations_proposal.py` is now
`(100, 33)` (34 on 574662e9, 31 before it), with a comment. No assertion was removed or loosened. The classes test
dropped only its `EXPECTED["chain"]` equality, which now denotes the 20-batch state rather than the 17-batch one.
The same pin stays asserted directly.

**README.** `oracles/README.md` has a "Current: `srd-5-2-1-corpus-3fe24ff6-4e3.json`" section. The 574662e9
section is renamed **Superseded**, not retired.

## Secrets baseline

- **Starting baseline:** `ffc66c346a4db95084d3a9cbd7f4eb8c74a7b2bd68939be1cfed445e24d9b190`.
- **Method:** a scoped rescan of this run's files only (`.claude/_sp/p5_delta.py`). Settings, plugins, filters and
  `generated_at` are unchanged. No `scan --baseline` was run, and there is no new `pragma: allowlist secret`.
- **Machine-readable delta:** `.claude/_sp/p5_baseline_delta.json`. The pre-change copy is
  `.claude/_sp/p5_baseline_before.json`.

| File | Added | Moved | Pruned |
|---|---|---|---|
| `oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json` | 1007 | 0 | 0 |
| `issue-5d-monsters-corrections-ACCEPT.py` | 6 | 0 | 0 |
| `issue-5d-gameplay-toolbox-generator.py` | 0 | 1 | 0 |
| `issue-5d-magic-items-generator.py` | 0 | 1 | 0 |
| `test_monsters_proposal.py` | 0 | 3 | 0 |
| `test_gameplay_toolbox_proposal.py` | 0 | 0 | 4 (hash constants moved to the hub) |
| `test_magic_items_proposal.py` | 0 | 0 | 4 (same) |
| `test_spell_descriptions_proposal.py` | 0 | 0 | 4 (same) |
| **Total** | **1013** | **5** | **12** |

- The 574662e9 oracle has 1005 baselined findings; the new file has 1007.
- **Hook:** `detect-secrets-hook --baseline .secrets.baseline` ran twice on 37 files. These are the files modified
  since 2026-09-28 local (`.claude/_sp/p5_hook_files.txt`), which includes every in-scope file and one earlier-phase
  file (`test_community_source_structure.py`, 05:50Z, no findings). It ran twice more after the late test fixes, and
  twice again after the glossary pin fix. Every run exited 0, and the baseline SHA-256 stayed stable at
  `81e2f7a77127ab560b05300dd0d597f30e37e8f987dd0b98cfa6a7ba716bef4d`. `.secrets.baseline` is staged by name.
- **Out of scope, left alone:** one obsolete entry for `test_actions_pilot_proposal.py`, from an earlier phase's
  edit (mtime 2026-09-24); several pre-existing untracked historical generators with unbaselined findings.

## Gates (raw)

This is not an all-green claim. In order:

| Gate | Result | Exit |
|---|---|---|
| monsters-corrections ACCEPT `--verify` | as recorded above | 0 |
| targeted pytest (touched tests) | 2 failed, 346 passed, 38:32 (monsters `kept_whole`; refused set) | 1 |
| monsters + refused reruns 1–3 | failed (positional order, missing 574662e9 identities; `diff` order; `KeyError 'batches'`) | 1, 1, 1 |
| monsters + refused rerun 4 | passed | 0 |
| full `tests/ingestion` | 1 failed, 4270 passed, 131 skipped, 2 warnings, 3598.96s (0:59:58); the failure was the glossary pin (`.claude/_rc/msc/final.log`) | 1 |
| glossary committed test after the pin fix | 1 passed, 112.18s | 0 |
| Black `--check` / Ruff on touched tests and generators | clean | 0 / 0 |
| `detect-secrets-hook` ×2 (37 files, including the glossary test); once more on this followup | baseline stable at `81e2f7a7…ef4d` | 0, 0; 0 |
| §5 manifest rerun | one expected BAD (monsters generator, `92eed920…`) | 1 |
| `detect-secrets-hook` ×2 on the final Monsters generator (closed separately by the parent) | baseline stable at `81e2f7a7…ef4d` | 0, 0 |
| mypy (`src/`) | not run: no `src/` file changed | — |
| expanded mypy | deferred, non-green | — |
| pip-audit | deferred, non-green | — |

The full `tests/ingestion` suite was not rerun after the glossary fix. Only that test was rerun.

## Retention: obsolete candidates, all kept

Nothing was deleted. Each candidate below is review/replay evidence or is covered by a separate authorization:

- `oracles/srd-5-2-1-corpus-574662e9-0ef.json` (the fc62 bytes, superseded). Its current purpose, determined
  only, with no cleanup:
  - the directory-listing tests name it (`test_accepted_inputs.py`, `test_committed_accepted_authority.py`,
    `test_packaging.py`, `test_oracle.py`);
  - it is the `ACCEPTED_PATH` the monsters-corrections REPLACEMENT refuses to extend;
  - the historical REGEN generators and ACCEPT replays bind to it.

  Its retirement needs its own Owner authorization.
- The REGEN proposals and DRAFTS over 574662e9, and the historical per-batch ACCEPT replay scripts (for example
  `issue-5d-magic-items-ACCEPT.py`, `issue-5d-gameplay-toolbox-ACCEPT.py`). They bind to their own pinned
  574662e9 path, whose bytes are unchanged (`fc62…5a62`, rechecked this session). They were not rerun in this
  run.
- Scratch under `.claude/_rc/` (`corr/`, `owncorr/`, `cand/`, `newrel/`, `rec/`, `msc/{old,rel,sim}/`) and
  `.claude/_sp/` (never committed). `msc/rel/afterworlds.db` (`ffeb731f…17e0`) is the
  REPLACEMENT helper's `SCRATCH_DB`. It serves the existing `REPLACEMENT._findings` verifier/simulation seam, which
  the ACCEPT `--verify`/replay paths call (monsters-corrections, magic-items and gameplay-toolbox ACCEPT). The live
  tests do not read it: they rebuild native fixtures from the `source_release_db` fixture. It is retained while
  replay needs it. This records no new product decision and no broad retirement.
- Quarantined `srd-5-2-1-corpus-36b786d8-fa2.json` and `issue-5d-source-correction-REPLACEMENT-PACKET.md` were not
  touched. Root `afterworlds.db` is still `7a3a1814…dc2e`. The 4 stashes and the pre-existing staged deletions are
  unchanged.

## Blockers and deferrals

- **Deferred, non-green:** pip-audit and expanded mypy.
- **Partial publication:** stays blocked (317 reference findings).
- **Awaiting Owner authorization:** retiring 574662e9.

## Process disclosures

- Earlier sessions of this run used `cd` in Bash twice. This session used `Set-Location`/`Push-Location` in
  PowerShell, which moved the working directory to `D:\AI\Claude\afterworlds`.
- Nothing was committed, pushed or published. The only staged change is `.secrets.baseline`, staged by name.
  There was no activation and no shared DB or Chroma write.
- No task-dir permissions were probed or changed. There was no `git gc`/`prune`, no `--no-verify` and no history
  rewrite.
- **Connectors:** Context7, Expedia, Google Calendar, Intuit TurboTax and Shopify need authorization in claude.ai
  connector settings. They were not used.

## Sources

- https://www.dndbeyond.com/srd
- https://media.dndbeyond.com/compendium-images/errata/MM-25/MM-2025_v1.pdf
- https://www.dndbeyond.com/sources/dnd/sae/monster-manual
- https://www.dndbeyond.com/posts/1950-sage-advice-and-errata-for-the-new-core-rules-is
