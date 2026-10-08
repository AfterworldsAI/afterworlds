# CRD Issue 5d — Spellcasting accepted-recording handoff (#132, #137)

**Status: prepared, not executed.** Nothing has been recorded. Claude did not run `accept` or `resolve` against the repository artifact, did not edit or stage `.secrets.baseline`, and made no commit. The coordinating Codex review of this preparation is separate and has not happened yet.

## 1. Decision (settled; do not ask again)

- The Owner answered `spellcasting-owner-review.md` (SHA-256 `3bbb3a258805a697771d59357cc60742053d03190345153c0434747239e172ee`): *"I accept the exact **19-record proposal** and approve its **one reference resolution**, retaining **59 reference findings**."*
- In the helper:
  - `RULE` is those words **without the bold markup**: `I accept the exact 19-record proposal and approve its one reference resolution, retaining 59 reference findings.`
  - `DECISION_ITEM` is the review's line 40, verbatim, including its rendered spacing: `…retaining all59reference findings and blocking partial publication/activation.`
  - `REVIEWER` (the authorizer, reviewer and executor) is `Ravenlok (Owner)`.
  - `AUTHORIZATION_REFERENCE` is `Owner decision on spellcasting-owner-review.md: <repr RULE>, answering <repr DECISION_ITEM>`.
  - Every approval value is a non-empty literal.
- **Both text choices are open to Owner objection before recording:** stripping the `**` markers, and keeping `all59reference` as the review renders it. Changing either one changes only the recorded strings; the semantics stay the same.
- No renewed semantic approval is needed. Partial publication and activation remain blocked.

## 2. Inputs and helper

| Item | Path | SHA-256 |
|---|---|---|
| Proposal (identity `0b7f14ffbea2240adbbd7a88ac439a3955ca417b563f89ee1b35e15f94ec1d55`) | `.claude/review-notes/issue-5d-spellcasting-REGEN-626c83f8-PROPOSAL.json` | `3dbdae694829b37cae91f929e3fe552f750178276f5f338f80e208c341764af3` |
| Resolution draft (1) | `.claude/review-notes/issue-5d-spellcasting-resolutions-REGEN-626c83f8-DRAFTS.json` | `72bcdc5ff1849acef5c15bb1606921ee8a2cd61ab5756ddac7841122e852fc2a` |
| Prior artifact (13 batches, 216 records, 49 resolutions) | `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json` | `08cca0b77b6554f585af471de242c81f58502490f9832840a44c32998c7803fb` |
| Secrets baseline (staged `M`; not touched by recording) | `.secrets.baseline` | `971e66b2f8fc326788d6462fb76e5697863a45c18496c089835d105430c34899` |
| Recording helper | `.claude/review-notes/issue-5d-spellcasting-ACCEPT.py` | `2bed9d9bf1e8606911ba21d6aacef8a1ce8eb7da37518f2fcb6177b939ac22f6` |
| Draft source (unchanged) | `.claude/review-notes/issue-5d-spellcasting-generator.py` | `20c759dcf0f9c5097238b942e60429d5c72e186fba80803f8c55e657d6258aae` |
| Equipment helper (unchanged; replayed, not edited) | `.claude/review-notes/issue-5d-equipment-ACCEPT.py` | `24d00787b368970add0fda3c3c0c313a79802bb5b4f9ef2d6b41a18f514c275a` |

The helper uses only the native seams, in this order: `accept_proposal`, then `resolve_references`, then `serialize_accepted_inputs`.

**How `prior()` rebuilds the prefix.** It replays the Equipment helper's own `accepted` and `resolved` steps over `REPLACEMENT.recorded()`. It uses the pinned recorded Equipment times (`2026-09-25T05:47:17Z` and `2026-09-25T05:47:29Z`, as in `test_equipment_acceptance.py`) and pins the result to `08cca0b7…`.
- It never reads the artifact, and it never calls `EQUIPMENT._state()`.
- The Equipment prefix therefore still rebuilds after this batch is appended. The dry run below confirms this.
- The replacement chain's `recorded()` and Equipment's step functions are reused unchanged.

**Modes:**
- **`--simulate`** runs both steps in memory as `SIMULATION - not an Owner approval` and writes nothing in the repository.
- **`accept`** refuses unless the artifact is exactly the prior state: SHA `08cca0b7…` and byte-equal to the rebuilt prefix. It also pre-checks the drafts. It then reads the UTC clock (to the second, with `Z`) as `accepted_at`, checks preservation, and writes.
- **`resolve`** refuses unless the artifact is exactly the accepted state, which it checks by reading `accepted_at` back and rebuilding. It then reads the UTC clock as `resolved_at`, applies the one draft, checks preservation, and writes.
- **`--verify`** reports `prior`, `accepted` or `resolved`. It reads both times back, rebuilds, and compares the bytes exactly.

**Preservation** reuses Equipment's `_check_preserved`:
- every list item in the 13-batch payload is still present, compared as a multiset;
- every scalar is equal;
- the first 13 batches are identical.

This covers the 216 records, the 49 resolutions and their authorizations.

## 3. Terminal Claude prompt (Owner pastes this; one prompt covers recording and the scanner pass)

> CRD Issue 5d spellcasting recording and scanner pass. The Owner has already accepted the 19-record proposal and its one resolution; **do not ask for semantic approval again.** Follow `.claude/review-notes/issue-5d-spellcasting-accepted-recording-handoff.md` §2–§6 exactly. Run Python as `.\venv\Scripts\python.exe` with `$env:PYTHONIOENCODING='utf-8'`.
>
> 1. **Check hashes.** `Get-FileHash` the helper, the proposal, the drafts, the oracle and `.secrets.baseline`, and compare them with §2 (`Get-FileHash` prints uppercase). Stop if any differs.
> 2. **Simulate.** Run the helper with `--simulate`. The output must equal §4 line for line.
> 3. **Record.** Run `--verify`, then `accept`, `--verify`, `resolve`, `--verify`.
>    - The first `--verify` must print `state prior 08cca0b7…`.
>    - After `accept`: `state accepted`, `batches 14 last spellcasting`, `records 235`, `spans 1497 review units 169`, `resolutions 49`, `resolution violations 0`.
>    - After `resolve`: `state resolved`, the same counts with `resolutions 50`, and both timestamps read back.
> 4. **Scanner pass**, under §6:
>    - Reconcile the §6a files as they are now, using the baseline's own `plugins_used` and `filters_used`, by type and hash. Expected: exactly the 16 §6b rows plus the two §6c oracle rows. Oracle line moves are expected. Stop and report any other difference.
>    - Run `detect_secrets.pre_commit_hook --json` against a **temporary copy** of the baseline, as evidence only.
>    - Edit the baseline once, by script:
>      - add the 18 rows;
>      - refresh line numbers in the scope files;
>      - prune only entries that are verified obsolete (§6d);
>      - preserve `version`, `plugins_used`, `filters_used`, all flags and every other entry.
>
>      Never use `detect-secrets scan --baseline`.
>    - `git add -- .secrets.baseline`.
>    - Run the normal staged hook: `.\venv\Scripts\python.exe -m detect_secrets.pre_commit_hook --baseline .secrets.baseline` followed by the §6a paths. It must exit 0.
>      - On exit 3, inspect `git diff -- .secrets.baseline`. Accept only line refreshes and §6d trims, re-stage, and rerun.
>      - The gate is stable when two consecutive runs exit 0 with an unchanged `Get-FileHash .\.secrets.baseline`.
> 5. **Report:**
>    - the final oracle SHA and both timestamps;
>    - the `--verify` output;
>    - `git diff --cached --stat -- .secrets.baseline`;
>    - the added and pruned entries and the count of moved lines;
>    - the final baseline SHA.
>
> **If a step refuses, fails, or any action or permission is denied, stop and report it verbatim.** Do not retry another way, use an alternate writer or tool, bypass, or change permissions. `--verify` names the artifact's state. Do not commit, push, publish or activate. Do not touch `issue-5d-source-correction-REPLACEMENT-PACKET.md`, including deleting it. Make no other edits.

**Notes for the Owner:**
- The final oracle SHA cannot be predicted, because the runtime timestamps are part of the bytes.
- If `accept` succeeded and `resolve` failed, the artifact is in the `accepted` state, and `resolve` may be rerun once the cause is known.
- The oracle is untracked, so `git restore` cannot recover it. The prior bytes are reproducible from `prior()`. No restore is prescribed here.

## 4. Native evidence (preparation, 2026-09-25 UTC, `claude-opus-5-5`)

`rtk proxy venv\Scripts\python.exe .claude\review-notes\issue-5d-spellcasting-ACCEPT.py --simulate`, verbatim:

```
SIMULATED (in memory; nothing written; not an acceptance)
  reviewer 'SIMULATION - not an Owner approval' at 2026-09-25T00:00:00Z
  artifact state prior
  deterministic across two runs True
  bytes sha256 e19944780cf16b2d3212da740f6b230c015cde412c486da205170dc37b29ea04 3741098
  after accept:
  batches 14 last spellcasting
  records 235
  spans 1497 review units 169
  resolutions 49
  resolution violations 0
  prior preserved (216 records, 49 resolutions, 13 batches) True
  after resolve:
  batches 14 last spellcasting
  records 235
  spans 1497 review units 169
  resolutions 50
  resolution violations 0
  prior preserved (216 records, 49 resolutions, 13 batches) True
  reloads to the same bytes True
  findings 9023 leaf/uncovered 8964
  reference findings 59 unresolved 58
    reference srd-5.2.1/rules-glossary:'Improvised Weapons': unknown target record glossary.improvised_weapons
  artifact unchanged 08cca0b77b6554f585af471de242c81f58502490f9832840a44c32998c7803fb
```

This matches Codex's independent simulation: 235 records, 1497 spans, 14 batches, 50 resolutions, 0 violations, 59 reference findings (58 unresolved and one unknown target), and 8964 uncovered leaves. Review units go from 150 to 169. The oracle and the shared database were not written.

**Dry run of every state.** `main()` was driven against a copy of the oracle in a temporary directory outside the repository:

| Step | Result |
|---|---|
| `--verify` | prior `08cca0b7…` |
| `resolve` | refused (prior, not accepted) |
| `accept` | wrote `ee315567…` |
| `--verify` | accepted, 14/235/1497/169/49/0 |
| `accept` | refused |
| `resolve` | wrote `64ee4367…` |
| `--verify` | resolved, 50 resolutions, 0 violations, both times read back |
| `resolve` | refused |
| `accept` | refused |
| unknown argument | usage |

After the append:
- `prior()` still rebuilt `08cca0b7…`.
- `REPLACEMENT.verify()` still passed. It pins the twelve-batch prefix `7b1d6f43…` only.
- `issue-5d-equipment-ACCEPT.py --verify` failed on the appended copy, as expected (§5).
- The real oracle stayed `08cca0b7…`.

**Gates:**
- Black and Ruff are clean on the helper, and it has zero `\r`.
- `mypy --strict` on this `.claude` script reports only `import-untyped` for the `src` package. That is not a repository gate (`mypy src/`), the same as for the Equipment helper.
- No broad suite was run for this preparation, as instructed. Earlier partial-suite coverage exits are not all-green evidence.
- pip-audit (31 findings in 11 packages) remains deferred and non-green.

## 5. Post-recording boundaries (not fixed here; need a Codex-reviewed follow-up)

Appending changes the artifact, so the following consumers of the *current* artifact fail by construction:
- **`issue-5d-equipment-ACCEPT.py --verify` / `_state()`** asserts, with `equipment resolved_at: [05:47:29Z, <spellcasting time>]`. The replacement for whole-artifact verification is `issue-5d-spellcasting-ACCEPT.py --verify`. The Equipment helper is not edited.
- **`tests/ingestion/mechanical/test_equipment_acceptance.py`** (untracked) calls `EQ._state` at import and pins the 13-batch bytes.
- **`tests/ingestion/mechanical/test_spellcasting_proposal.py:185-188`**: `prior()` asserts the oracle SHA is `08cca0b7…`. The follow-up should rebuild through this helper's `prior()`.
- **`.claude/review-notes/issue-5d-source-correction-REPLACEMENT-ACCEPT.py` `verify()`** still passes, but its printed pointer names the Equipment helper.
- **`tests/ingestion/mechanical/test_source_release_readiness.py:370-379`** pins the accepted span sum as ending `+ 409` (thirteen batches). Spellcasting adds 72.
- **`tests/ingestion/mechanical/test_committed_accepted_authority.py:949-984`**: the committed-identity set in `test_no_refused_candidate_is_selectable` has no spellcasting proposal. Equipment's follow-up added `EQUIPMENT_PROPOSAL` at line 141.
- **`src/afterworlds/ingestion/mechanical/oracles/README.md:18-26`** and **`docs/architecture/issue-5c-5d-clean-restart.md:1404-1405`** describe 13 batches and `08cca0b7…`.
- Any other consumer is found by running the gates after recording. `test_character_origins_feats_acceptance.py:199` and `test_equipment_proposal.py` `prior()` are prefix-pinned and unaffected.

## 6. Scanner scope and public-identifier inventory

Every finding here is a public SHA-256 content hash or identity, not a secret, and all are `Hex High Entropy String`. The "hashed" column is detect-secrets' SHA-1 of the literal (first 8 characters).

**Observed 2026-09-25, before recording:**
- Each file was scanned under the baseline's own `plugins_used` and `filters_used` and compared with its baseline entries by type and hash.
- The non-mutating hook was also run against a temporary copy of the baseline (exit 1). It reported exactly the 16 rows in §6b, and the copy was unchanged.
- The staged baseline has version 1.5.0, 59 files and 1533 results, SHA `971e66b2…4899`. It was not changed.

### 6a. Final scanner scope (the hook takes exactly this list)

Prior outstanding scope, now fully reconciled (0 new, 0 obsolete, 0 moved):
1. `.claude/review-notes/issue-5d-equipment-ACCEPT.py` (4 live / 4 baselined)
2. `.claude/review-notes/issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json` (6/6)
3. `.claude/review-notes/issue-5d-equipment-resolutions-REGEN-626c83f8-DRAFTS.json` (4/4)
4. `tests/ingestion/mechanical/test_equipment_proposal.py` (1/1)
5. `.claude/review-notes/issue-5d-equipment-accepted-recording-handoff.md` (0/0)
6. `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json` (151/151)
7. `tests/ingestion/mechanical/test_character_origins_feats_acceptance.py` (1/1)
8. `.claude/review-notes/issue-5d-source-correction-REPLACEMENT-ACCEPT.py` (26/26)
9. `tests/ingestion/mechanical/test_equipment_acceptance.py` (0/0)

Spellcasting and its consumer changes:

10. `.claude/review-notes/issue-5d-spellcasting-REGEN-626c83f8-PROPOSAL.json`
11. `.claude/review-notes/issue-5d-spellcasting-resolutions-REGEN-626c83f8-DRAFTS.json`
12. `tests/ingestion/mechanical/test_spellcasting_proposal.py`
13. `.claude/review-notes/issue-5d-spellcasting-generator.py` (clean)
14. `.claude/review-notes/issue-5d-spellcasting-REVIEW-PACKET.md` (clean)
15. `.claude/review-notes/issue-5d-spellcasting-ACCEPT.py`
16. `.claude/review-notes/issue-5d-spellcasting-accepted-recording-handoff.md`: this file. Hashes are backtick-quoted, so it should be clean; the terminal pass confirms that.
17. `src/afterworlds/services/rules_authority/application.py` (clean)
18. `src/afterworlds/services/rules_authority/service.py` (clean)
19. `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` (clean)
20. `src/afterworlds/ingestion/mechanical/oracles/README.md` (clean)

### 6b. Observed now: live findings not in the baseline (16)

| # | Line | Literal | Hashed |
|---|---|---|---|
| 10 | 4659 | `authoritative_source_hash 8974902d…` | `1084eace` |
| 10 | 4660 | `bundle_root_hash 0f49f740…` | `76945542` |
| 10 | 4662 | `persisted_corpus_digest 81009ec8…` | `005930e0` |
| 10 | 4664 | `transform_config_hash eaa19d76…` | `542b7433` |
| 10 | 4667 | schema `hash 7fb9254b…` | `ab13bf07` |
| 10 | 4670 | `semantic_policy_hash da63b894…` | `cc66b4ed` |
| 11 | 12 | `authoritative_source_hash 8974902d…` | `1084eace` |
| 11 | 13 | `transform_config_hash eaa19d76…` | `542b7433` |
| 11 | 14 | `bundle_root_hash 0f49f740…` | `76945542` |
| 11 | 15 | `persisted_corpus_digest 81009ec8…` | `005930e0` |
| 12 | 128 | `IDENTITY 0b7f14ff…` | `a72a76a5` |
| 12 | 136 | `ORACLE_SHA256 08cca0b7…` | `8c7b4bc6` |
| 15 | 79 | `PRIOR_SHA256 08cca0b7…` | `8c7b4bc6` |
| 15 | 85 | `PROPOSAL_FILE_SHA256 3dbdae69…` | `7433cc07` |
| 15 | 87 | `PROPOSAL_IDENTITY 0b7f14ff…` | `a72a76a5` |
| 15 | 89 | `DRAFTS_SHA256 72bcdc5f…` | `01ecef9b` |

### 6c. Expected after recording (predicted from the dry-run bytes, not observed)

- **File 6 (the oracle)** goes from 151 findings to 153. Two are new:
  - line 12042, `proposal_identity 0b7f14ff…` (`a72a76a5`);
  - line 12118, the spellcasting `semantic_diff_hash e341beb7…` (`7730ac0c`).
- None of the 151 existing hashes disappears; 125 of them change line number.
- The runtime times and the reviewer string do not change which literals exist or where they sit.
- The expected total of new findings is 18.
- If a §5 follow-up edits a scope file before the scanner pass (for example, file 12), reconcile that file's contents at that time instead of using these line numbers.

### 6d. Verified-obsolete pruning (standing Owner approval; no historical-only retention)

An entry may be pruned only if one of these mechanisms verifies it:
- **(a) Absent file.** The path does not exist in the working tree.
- **(b) Hash gone from a live file.** Rescanning the file under the baseline's own settings no longer yields that type and hash.

**Observed now: none.** No baseline key names an absent file; the 25 absent files were pruned in the Equipment pass. No scope file has an obsolete hash.

**Retain:**
- every live finding;
- `version`, `plugins_used`, `filters_used`;
- all flags;
- every other entry.

Do no unrelated cleanup.

**Hazards:**
- `detect-secrets scan --baseline .secrets.baseline <paths>` would drop every other file's entries.
- The hook refuses an unstaged baseline.
- With nothing new to report, the hook may rewrite the baseline to refresh lines and return 3. The rerun-until-stable rule in §3 covers this.
