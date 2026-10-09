# CRD Issue 5d — Equipment accepted-recording handoff (#132, #137)

**Status: prepared, not executed.** Nothing has been recorded. The Owner runs the statements in §3. Claude did not run `accept` or `resolve` against the repository artifact. It did not edit or stage `.secrets.baseline`, and it made no commit.

**Review consultation during this Claude run (`codex exec --sandbox read-only`, 2026-09-25).** This is not the independent coordinating Codex review. That review is separate and still in progress, and none of this preparation has passed it yet.

The consultation found nothing in checks 2–6 and 8. It raised two P2 findings:
- **Fixed:** `prior()` now pins the rebuilt base to `7b1d6f43…` before any state is judged.
- **Superseded:** its suggestion to verify §7 only against a temporary copy was replaced. §7 now keeps the temporary-copy probe as evidence and makes the normal staged-baseline hook the final gate.

The consultation did not see the later §6/§7 corrections.

## 1. Decision (settled)

- The Owner answered `equipment-owner-review.md` (SHA-256 `77f22285b0cc251e36d87bd968702ba78623d3c31c81bb389d53a363c45343c5`) with **"I accept it."**
- The decision item, verbatim: *"Accept the exact 80-record Equipment proposal and approve the exact 43 reference resolutions, retaining all 58 remaining reference findings and blocking partial publication/activation."*
- In the helper:
  - `RULE = "I accept it."`
  - `REVIEWER` (authorizer, reviewer and executor) = `"Ravenlok (Owner)"`
  - `AUTHORIZATION_REFERENCE = "Owner decision on equipment-owner-review.md: 'I accept it.', answering '<decision item>'"`
- Codex rechecked the proposal after approval. Semantics are unchanged by this handoff.

## 2. Inputs and helper

| Item | Path | SHA-256 |
|---|---|---|
| Proposal (identity `e25f7a82617ccca7bdf3282d775917d716fd37c83d35cdebf7bceea8c2758b87`) | `.claude/review-notes/issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json` | `c33e7473c881624a0bc5700369899df69567672bb4cb220e751303f98ce19430` |
| Resolution drafts (43) | `.claude/review-notes/issue-5d-equipment-resolutions-REGEN-626c83f8-DRAFTS.json` | `1d92207bf791833464083a77081801eae54fbdbd69f37f897829e32bc6b5c569` |
| Prior artifact (12 batches, 136 records, 6 resolutions) | `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json` | `7b1d6f43c322adbd662f94cb941c58a9ec54dde0fca5bef42465c940459abdd8` |
| Secrets baseline (not touched by recording) | `.secrets.baseline` | `ba1478408976dc11aa18103aad3f7bbd5efbe262f45257d40f224fd91420099f` |
| Recording helper | `.claude/review-notes/issue-5d-equipment-ACCEPT.py` | `24d00787b368970add0fda3c3c0c313a79802bb5b4f9ef2d6b41a18f514c275a` |

The helper uses only the native seams: `accept_proposal` → `resolve_references` → `serialize_accepted_inputs`. It rebuilds the prior chain through `issue-5d-source-correction-REPLACEMENT-ACCEPT.py`'s `recorded()`. It does not call that script's `verify()`, which pins the 12-batch bytes.

- **`--simulate`** runs both steps in memory as `"SIMULATION - not an Owner approval"`. It writes nothing in the repository.
- **Every step** first rebuilds the prior chain and pins its serialized bytes to `7b1d6f43…`.
- **`accept`** refuses unless both of these hold:
  - the artifact's SHA is `7b1d6f43…` and it equals the rebuilt prior chain;
  - the proposal SHA/identity, the drafts SHA and the drafts payload all check.

  It reads the UTC clock (to the second, `Z`) as `accepted_at`, checks that the prior chain is preserved, then writes.
- **`resolve`** refuses unless the artifact is exactly the accepted state. It checks this by reading `accepted_at` back from the file and rebuilding. It then reads the UTC clock as `resolved_at`, applies all 43 drafts as one action, checks preservation, and writes.
- **`--verify`** reports the state (`prior`, `accepted` or `resolved`). It reads both timestamps back, rebuilds the bytes, and compares them exactly.

**Prior preservation** means two things:
- every list item in the 12-batch payload is still present, compared as a multiset;
- every scalar is equal, and the first 12 batches are identical.

This was checked after each step.

## 3. Owner statements (PowerShell, run one at a time)

Uppercase hashes are expected: `Get-FileHash` prints uppercase.

```powershell
Set-Location D:\AI\Claude\afterworlds
```
```powershell
$env:PYTHONIOENCODING = 'utf-8'
```
```powershell
Get-FileHash -Algorithm SHA256 .\.claude\review-notes\issue-5d-equipment-ACCEPT.py, .\.claude\review-notes\issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json, .\.claude\review-notes\issue-5d-equipment-resolutions-REGEN-626c83f8-DRAFTS.json, .\src\afterworlds\ingestion\mechanical\oracles\srd-5-2-1-corpus-626c83f8-209.json, .\.secrets.baseline | Format-List Hash, Path
```
Expect the five hashes in §2. **Stop if any differs.**

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py --simulate
```
Expect exactly the §4 simulation output. The bytes SHA `21430c3d…` belongs to the simulated reviewer and time only.

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py --verify
```
Expect `state prior 7b1d6f43c322adbd662f94cb941c58a9ec54dde0fca5bef42465c940459abdd8`.

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py accept
```
Expect `accept srd-5-2-1-corpus-626c83f8-209.json <sha>`.

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py --verify
```
Expect all of the following:
- `state accepted <same sha>`
- `batches 13 last equipment`
- `records 216`
- `spans 1425 review units 150`
- `resolutions 6`
- `resolution violations 0`
- `accepted_at <UTC> resolved_at None`

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py resolve
```
Expect `resolve srd-5-2-1-corpus-626c83f8-209.json <final sha>`.

```powershell
.\venv\Scripts\python.exe .\.claude\review-notes\issue-5d-equipment-ACCEPT.py --verify
```
Expect all of the following:
- `state resolved <final sha>`
- `batches 13 last equipment`
- `records 216`
- `spans 1425 review units 150`
- `resolutions 49`
- `resolution violations 0`
- `accepted_at <UTC> resolved_at <UTC>`

```powershell
Get-FileHash -Algorithm SHA256 .\src\afterworlds\ingestion\mechanical\oracles\srd-5-2-1-corpus-626c83f8-209.json, .\.secrets.baseline | Format-List Hash, Path
```
Expect:
- the oracle hash equals `<final sha>`;
- `.secrets.baseline` is still `BA1478408976DC11AA18103AAD3F7BBD5EFBE262F45257D40F224FD91420099F`.

Report `<final sha>` and both timestamps to Claude. The final SHA cannot be predicted: the runtime timestamps are part of the bytes. Do not commit.

**If a step refuses or fails, stop and report its output. Do not retry another way.** `--verify` names the state the artifact is in:
- If `accept` succeeded and `resolve` failed, the artifact is in the `accepted` state. `resolve` may be rerun once the cause is known.
- The prior bytes are reproducible from `REPLACEMENT.recorded()`. The oracle file is untracked (`git status`: `??`), so `git restore` cannot recover it. `REPLACEMENT-ACCEPT.py record` refuses while the file exists. No restore is prescribed here; report the state instead.

## 4. Native evidence (preparation, 2026-09-25 UTC)

`--simulate` output, verbatim:

```
SIMULATED (in memory; nothing written; not an acceptance)
  reviewer 'SIMULATION - not an Owner approval' at 2026-09-24T00:00:00Z
  deterministic across two runs True
  bytes sha256 21430c3d67513085b47d362783526a6cab7d847a5af195f04042f74af80ca3fd 3558080
  after accept:
  batches 13 last equipment
  records 216
  spans 1425 review units 150
  resolutions 6
  resolution violations 0
  prior preserved (136 records, 6 resolutions, 12 batches) True
  after resolve:
  batches 13 last equipment
  records 216
  spans 1425 review units 150
  resolutions 49
  resolution violations 0
  prior preserved (136 records, 6 resolutions, 12 batches) True
  reloads to the same bytes True
  findings 9126 leaf/uncovered 9068
  reference findings 58 unresolved 57
    reference srd-5.2.1/rules-glossary:'Improvised Weapons': unknown target record glossary.improvised_weapons
  artifact unchanged 7b1d6f43c322adbd662f94cb941c58a9ec54dde0fca5bef42465c940459abdd8
```

- **Counts:** 12 → 13 batches; 136 → 216 records; 1016 → 1425 spans; 136 → 150 review units; 6 → 49 resolutions.
- **Findings:** 58 reference findings retained (57 unresolved and one unknown target). There are 9068 leaf/uncovered findings and 0 resolution violations.
- **Dry run of every state.** Every step and refusal was run against a copy of the prior artifact in a temporary directory outside the repository:

  | Step | Result |
  |---|---|
  | `--verify` | prior |
  | `resolve` | refused (prior, not accepted) |
  | `accept` | wrote `d24877a8…` |
  | `--verify` | accepted, 13/216/1425/150/6/0 |
  | `accept` | refused |
  | `resolve` | wrote `7e3b47f4…` |
  | `--verify` | resolved, 49 resolutions, 0 violations, both timestamps read back |
  | `resolve` | refused |
  | `accept` | refused |
  | unknown argument | usage |

  The real artifact stayed `7b1d6f43…`. The dry run and `--simulate` were both rerun on the final helper; the transcript above is identical.
- **Gates:** Black and Ruff are clean on the helper, and it has no `\r`. The existing gate A (739) and gate B (424) passes stand; no broad suite was rerun for this preparation.
- **Unchanged after all preparation:** oracle `7b1d6f43…abdd8`, baseline `ba147840…099f`.

## 5. Post-recording boundaries (not fixed here)

Recording changes the artifact's bytes, so these pins fail by construction. They need a Codex-reviewed follow-up mirroring `fe5d5fe`: pin the historical 12-batch bytes by SHA, add an Equipment acceptance test, and update the docs. Nothing is committed while gates are unresolved.

- `tests/ingestion/mechanical/test_character_origins_feats_acceptance.py:195-200` asserts that the artifact equals `through(BATCH)` and has SHA `7b1d6f43…`.
- `tests/ingestion/mechanical/test_equipment_proposal.py:230`: `prior()` asserts the 12-batch chain equals the artifact's bytes.
- `issue-5d-source-correction-REPLACEMENT-ACCEPT.py --verify` compares the artifact with the 12-batch chain.
- `src/afterworlds/ingestion/mechanical/oracles/README.md:18-23` and `docs/architecture/issue-5c-5d-clean-restart.md:1397` describe 12 batches and SHA `7b1d6f43…`.
- Any further consumer of the committed artifact is found by running the gates after recording.

## 6. Scanner scope and public-hash inventory

Every finding below is a **public SHA-256 content hash or identity**, not a secret. All are `Hex High Entropy String`. The "hashed" column is detect-secrets' SHA-1 of the literal (first 8 characters).

**How this was observed (2026-09-25, before recording):**
- Each scope file was scanned under the baseline's own `plugins_used` (25) and `filters_used` (10). The result was compared with that file's baseline entries by type and hash.
- The non-mutating hook was also run against a **temporary copy** of the baseline. The copy came back unchanged.
- The baseline at observation: version 1.5.0, `generated_at 2026-09-21T14:03:33Z`, 80 files, 1911 results. It is staged (`M `) with SHA `ba147840…099f`, and this run did not change it.

### 6a. Final scanner scope (the full intended scope; the hook takes exactly this list)

1. `.claude/review-notes/issue-5d-equipment-ACCEPT.py`
2. `.claude/review-notes/issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json`
3. `.claude/review-notes/issue-5d-equipment-resolutions-REGEN-626c83f8-DRAFTS.json`
4. `tests/ingestion/mechanical/test_equipment_proposal.py`
5. `.claude/review-notes/issue-5d-equipment-accepted-recording-handoff.md`
6. `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json`
7. `tests/ingestion/mechanical/test_character_origins_feats_acceptance.py`
8. `.claude/review-notes/issue-5d-source-correction-REPLACEMENT-ACCEPT.py`

Files 7 and 8 carry the public-hash findings still outstanding from the previous coordination. Both are reconciled below against their current contents.

### 6b. Observed now: live findings not in the baseline (17)

| # | Line | Literal | Hashed |
|---|---|---|---|
| 1 | 83 | `PRIOR_SHA256 7b1d6f43…` | `a136004c` |
| 1 | 86 | proposal file SHA `c33e7473…` | `acecbf0b` |
| 1 | 88 | `PROPOSAL_IDENTITY e25f7a82…` | `8a509b0f` |
| 1 | 90 | `DRAFTS_SHA256 1d92207b…` | `1f3a13e1` |
| 2 | 24925 | `authoritative_source_hash 8974902d…` | `1084eace` |
| 2 | 24926 | `bundle_root_hash 0f49f740…` | `76945542` |
| 2 | 24928 | `persisted_corpus_digest 81009ec8…` | `005930e0` |
| 2 | 24930 | `transform_config_hash eaa19d76…` | `542b7433` |
| 2 | 24933 | schema `hash 7fb9254b…` | `ab13bf07` |
| 2 | 24936 | `semantic_policy_hash da63b894…` | `cc66b4ed` |
| 3 | 12 | `authoritative_source_hash 8974902d…` | `1084eace` |
| 3 | 13 | `transform_config_hash eaa19d76…` | `542b7433` |
| 3 | 14 | `bundle_root_hash 0f49f740…` | `76945542` |
| 3 | 15 | `persisted_corpus_digest 81009ec8…` | `005930e0` |
| 4 | 136 | `IDENTITY e25f7a82…` | `8a509b0f` |
| 7 | 199 | 12-batch pin `7b1d6f43…` | `a136004c` |
| 8 | 171 | approval manifest `fd19dcab…` | `09e81d57` |

Reconciliation per file:

| # | Current | Baselined | New | Verified-obsolete | Moved |
|---|---|---|---|---|---|
| 1 | 4 | 0 | 4 | 0 | 0 |
| 2 | 6 | 0 | 6 | 0 | 0 |
| 3 | 4 | 0 | 4 | 0 | 0 |
| 4 | 1 | 0 | 1 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 |
| 6 | 149 | 149 | 0 | 0 | 0 |
| 7 | 1 | 4 | 1 | 4 (lines 192 `ac1e2952`, 202 `a4aae65e`, 252 `bd7d5f53`, 256 `f35615af`) | 0 |
| 8 | 26 | 25 | 1 | 0 | 0 |

File 5, this handoff, is clean: its hashes are backtick-quoted, and the hex plugin matches only quoted strings. None of file 7's four obsolete hashes is in its current contents.

### 6c. Expected after recording (predicted, not observed)

The prediction comes from scanning the simulated final bytes in a temporary directory. The runtime timestamps and the reviewer string do not change which literals exist or their lines.

- **File 6 (oracle):** 149 findings become 151. Two are new:
  - line 10443, `proposal_identity e25f7a82…` (`8a509b0f`);
  - line 10856, the Equipment `semantic_diff_hash a474c87e…` (`add76963`).

  None of the 149 hashes disappears. 129 of them change line number and 20 keep theirs. The accept-only state has the same two new findings.
- **Files 1–5, 7 and 8:** recording does not change them, so their §6b rows stand. The expected total of new findings is 19.
- **If the §5 follow-up edits a scope file before the scanner pass** (for example file 7's pin), reconcile that file's contents at that time instead of these line numbers.

### 6d. Verified-obsolete pruning (permitted under existing Owner approval)

The Owner approved pruning verified-obsolete public-hash entries. The Owner later rejected keeping content only for historical reasons during construction. `8f7c655`'s historical retention is therefore not current authority, and no further Owner decision is needed.

An entry is verified-obsolete only by one of these two mechanisms:

- **(a) Absent file.** The path does not exist in the working tree and is a staged deletion (`D `), so no current file can hold the literal.
  - Observed now: 25 files, 393 entries, all present in `HEAD`.
  - They are the old `issue-5d-*-ACCEPT.py` (12) and `*-PROPOSAL.json` (12) files, and `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-883aabdf-462.json` (149).
- **(b) Hash gone from a live file.** Rescanning the live file under the baseline's own settings no longer produces that type and hash.
  - Observed now: the 4 entries in file 7 (§6b).

**Retain:**
- every live finding;
- `version`, `plugins_used`, `filters_used`;
- all `is_verified` and other flags;
- every other entry for a file that exists.

Do no unrelated cleanup and no judgement-based pruning.

Pruning was **not performed in this run**. The baseline is unchanged.

### Scanner-pass hazards

- `detect-secrets scan --baseline .secrets.baseline <paths>` saves **only** the scanned paths' results; the old baseline supplies flags alone. It would drop every other file's entries (`detect_secrets/main.py:70-87`). Do not use it.
- The hook refuses an unstaged baseline (`pre_commit_hook.py:81-96`).
- When it finds nothing new, the hook may rewrite the baseline to refresh line numbers or trim entries; it then returns 3. The final gate therefore reruns until it is stable.

## 7. Terminal Claude prompt (final scanner pass, after Owner recording)

> CRD Issue 5d Equipment final scanner pass. The Owner has recorded; the final oracle SHA is `<paste>`. Existing Owner approval covers this pass, including verified-obsolete pruning; do not ask again. Read `.claude/review-notes/issue-5d-equipment-accepted-recording-handoff.md` §5–§6.
>
> 1. Confirm that `issue-5d-equipment-ACCEPT.py --verify` prints `state resolved` with that SHA.
> 2. Reconcile the eight §6a files as they are now, under the baseline's own `plugins_used` and `filters_used`, comparing by type and hash.
>    - Expected new findings: the §6b rows plus the two §6c oracle rows (19).
>    - Oracle line moves are expected.
>    - Stop and report any other difference.
> 3. As evidence only, not as the gate, run `detect_secrets.pre_commit_hook --json` against a temporary copy of `.secrets.baseline` on the eight files.
> 4. Edit the baseline once, by script:
>    - add the new rows in baseline `results` format;
>    - refresh moved line numbers in scope files;
>    - prune only the §6d entries, re-verifying each by mechanism (a) or (b);
>    - preserve `version`, `plugins_used`, `filters_used`, flags and every other entry.
>
>    Do not use `scan --baseline` with a path list.
> 5. `git add -- .secrets.baseline`
> 6. Run the normal gate on the staged baseline: `$env:PYTHONIOENCODING = 'utf-8'`, then `.\venv\Scripts\python.exe -m detect_secrets.pre_commit_hook --baseline .secrets.baseline` followed by the eight §6a paths. It must exit 0.
>    - If it exits 3, inspect `git diff -- .secrets.baseline`. Accept only line refreshes or trims of §6d entries, then `git add -- .secrets.baseline` and rerun.
>    - The gate is stable when two consecutive runs exit 0 and `Get-FileHash .\.secrets.baseline` is unchanged between them.
> 7. Report:
>    - `git diff --cached --stat -- .secrets.baseline`;
>    - the added hashes, the pruned entries and the line-move counts;
>    - the final baseline SHA.
>
> Do not commit or bypass staging or hooks, and make no other edits. Stop and report any denied action without retrying.
