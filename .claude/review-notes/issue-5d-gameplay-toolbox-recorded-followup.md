# CRD Issue 5d — Gameplay Toolbox recorded: follow-up (#132, #137)

**Status: RECORDED in the working tree, uncommitted.** Nothing was committed, pushed, merged, published or
activated. No shared DB or Chroma was written. Codex reviews this independently. Written 2026-09-27T10:16Z.

## Authorization recorded

- **Approval, verbatim:** "I accept this exact proposal and its one reference resolution."
- **Answers:** `gameplay-toolbox-owner-review.md` in
  `C:/Users/raven/.codex/visualizations/2026/09/21/01a0c27d-eef6-78f0-82cb-89e991b26cfe`
  (SHA-256 `bbceeadd434f42022813e205f96e0281f87dbfe7460cd16f51c71a764975a127`, read only).
- **Reviewer:** `Ravenlok (Owner)`, the same `OWNER` constant the replacement chain records.
- **Approved files** (pins rechecked before mutation):
  - `issue-5d-gameplay-toolbox-PROPOSAL.json`: SHA-256 `3a2751744b6350933f0c0aaec3cbb88761afcfb4f4d35434394bf70537fd49a6`,
    identity `8d4db7037b167648995d31bef6ad2f47ae31a19a2b48bf42406246517ee719eb` (33 records, 285 spans, 34 units).
  - `issue-5d-gameplay-toolbox-resolutions-DRAFTS.json`: SHA-256 `b87e6dcfdb29f4d02317a98e7b868cd12b122c3f5daf99d68ff5b9004a4528dd`.
    It holds one resolution, `resolve-glossary-challenge-rating-record-combat-encounters-gameplay-toolbox-1`:
    `glossary.challenge_rating` / empty component / "Combat Encounters" → `gameplay_toolbox.combat_encounters`.
- The acceptance's rule is the verbatim approval. Each record's `authorization_reference` names the owner review
  with its SHA, both packet files with their SHAs, and the approval text.

## Recording

`.claude/review-notes/issue-5d-gameplay-toolbox-ACCEPT.py` is the bounded helper. It uses the native seams only:
`accept_proposal`, then `resolve_references`, with `serialize_accepted_inputs` / `load_accepted_inputs`. The
eighteen-batch prior is rebuilt through `issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py` at its recorded
times and pinned to its bytes. The helper recognizes three states (prior, toolbox-accepted, resolved). It
replays an intermediate before continuing it, and it refuses anything else, fail-closed.

| Step | Real execution UTC | Oracle SHA-256 after |
|---|---|---|
| Initial (pinned before mutation) | — | `b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f` |
| `accept-toolbox` | 2026-09-27T09:46:01Z | `636b12758be98e614123080eb462da055d01d56a58d44e936014895801bc1086` |
| `resolve-toolbox` (replayed the intermediate first) | 2026-09-27T09:46:44Z | `671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95` |

- The times are the wall clock at execution. No simulation timestamp was recorded.
- `--simulate` ran first with a simulated reviewer and wrote nothing.
- **Final oracle:** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-574662e9-0ef.json`, SHA-256
  `671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95` (untracked, as before).
- The prior bytes are kept for audit at `.claude/_sp/gtrec/oracle-prior-b1f8718f.json`.

## Native replay, preservation and findings

`issue-5d-gameplay-toolbox-ACCEPT.py --verify` exited 0 (`.claude/_sp/gtrec/verify.log`). It checks:

- the prior rebuilt natively at its recorded times, equal to `b1f8718f…`;
- both steps rebuilt at the times read back from the file, byte-equal to the committed file, which reloads to the
  same bytes;
- counts: batches, records, spans, units and resolutions went (18, 947, 4826, 645, 1097) → (19, 980, 5111, 679, 1098);
- the prior payload is preserved as a multiset (`_preserved`), with 947 records, 1097 resolutions and 18 batches
  and every acceptance, identity, provenance entry and time unchanged;
- the only new acceptance and resolution are this batch's, so nothing was restamped or duplicated;
- findings: 166 reference findings (from 143), 5336 uncovered leaves (from 5621), 0 other findings and 0 resolution
  violations.

Two further checks:

- **Stale rerun:** a rerun of `accept-toolbox` on the resolved file refused with exit 1 (`rerun-refused.log`).
- **Replacement script:** `issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py --verify` now refuses the current
  file fail-closed, with "unrecognized batches" (`replacement-verify.log`). The helper's `--verify` is the
  whole-file replay. The replacement script is unchanged.

The 166 reference findings and the partial-publication block are retained. The release cannot publish.

## Dependency changes (settled only)

| File | Change |
|---|---|
| `.claude/review-notes/issue-5d-gameplay-toolbox-generator.py` | `current()` loads the file while it holds the pinned eighteen-batch bytes; otherwise it rebuilds them through the helper's `prior()` |
| `tests/.../test_gameplay_toolbox_proposal.py` | The prior fixture pins its rebuild to `b1f8718f…`; the final pin is the helper's `resolved` SHA; new `test_the_committed_oracle_records_the_owner_acceptance` checks bytes, state, times, preservation, approval/identity/rule, the one acceptance and resolution, and that the resolution equals DRAFTS |
| `tests/.../test_spell_descriptions_proposal.py` | The eighteen-batch pins are held against the replacement rebuild instead of the file, keeping the old-prefix byte, time-read-back and `_preserved` checks |
| `tests/.../_replacement_chain.py` | `LATEST` is the toolbox helper; `COMMITTED_SHA256` is its resolved SHA |
| `tests/.../test_character_origins_feats_acceptance.py` | The committed-bytes pin uses `COMMITTED_SHA256` |
| `tests/.../test_source_release_readiness.py` | The batch set adds `gameplay-toolbox`; 5111 spans, 1098 resolutions |
| `tests/.../test_committed_accepted_authority.py` | The toolbox proposal is added to the named identity set of `test_no_refused_candidate_is_selectable` |
| `src/.../oracles/README.md` | "Current" now reads nineteen batches, 980 records, 1098 resolutions, `671f47d7…` |
| `docs/architecture/issue-5c-5d-clean-restart.md` | A supersession entry is appended; closed entries are not edited |
| `.claude/review-notes/issue-5d-gameplay-toolbox-review.md` | A superseding status banner; the rest is unchanged |

No source, release, schema or `src/` code changed.

## Gates (raw logs in `.claude/_sp/gtrec/`)

All runs used `rtk proxy venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider --no-cov`, attached.

| Scope | Result | Log |
|---|---|---|
| `test_gameplay_toolbox_proposal.py` | 16 passed | `pytest-toolbox.log` |
| `test_spell_descriptions_proposal.py` | 21 passed | `pytest-sd.log` |
| COF / equipment / spellcasting acceptance and readiness | 36 passed | `pytest-acc.log` |
| oracle, packaging, accepted_inputs, committed_accepted_authority, quarantine | 1 failed (named identity set), 194 passed | `pytest-grp.log` |
| `test_committed_accepted_authority.py` after the fix | 20 passed | `pytest-grp2.log` |
| classes and glossary, `-k "committed or prior or recorded"` | 6 passed | `pytest-clsgl.log` |
| 10 reader suites (publication, production release, retained proposals, …) | 507 passed, 14 skipped | `pytest-readers.log` |
| 10 frozen-prior and schema reader suites | 241 passed | `pytest-readers2.log` |
| black `--check` / ruff on the 8 changed Python files; `mypy src/` | clean / clean / no issues in 235 files | `lint-deps.log` |

Not run:
- the unchanged full suite (not duplicated);
- a new source audit or batch authoring (out of scope);
- `pip-audit`, which is deferred non-green (31/11, as previously recorded).

## Secrets baseline (scoped)

| | |
|---|---|
| Before | `7d1e44bf2fff2247258d64bec90b823eed8194ddb6b65ccd45c6402c5ef2a9d9` (asserted before writing) |
| After | `11c24985f0d40ead2afcfe9c2c010c432829311c865129fea385133d422b8339` (staged; index = worktree) |
| Added / pruned / line-refreshed | 9 / 0 / 983 |
| Entries / files | 3281 → 3290 / 75 → 76 |
| Preserved | top-level settings, plugins, filters, version and `generated_at`; every other file's entries identical; existing key order; `is_verified` false on added entries |

The 12 changed files were rescanned under the baseline's own plugins and filters. Only two had new findings, and
all 9 were recovered from their lines and verified public by recomputation (`verify-baseline.log`, `verify.json`):

- **Oracle:** the toolbox `proposal_identity` (recomputed from the PROPOSAL) and its `semantic_diff_hash`
  (`batch_diff_hash` over the natively rebuilt batch).
- **ACCEPT.py:** the SHA-256 of the PROPOSAL, DRAFTS and owner review; the identity; and the three state SHAs
  (native rebuilds of prior, toolbox-accepted and resolved).

The 983 line refreshes are 975 in the oracle and 4 in each of the two proposal tests. No entry was obsolete, so none
was pruned. After the update, a rescan showed every file in sync: 0 new, 0 obsolete, lines equal.

Probing and hooks:
- **Scanner probe:** it used a baseline copy in `.claude/_sp/gtrec/`, which was deleted afterwards.
- **Hook:** after `git add -- .secrets.baseline`, `detect-secrets-hook --baseline .secrets.baseline` ran on the 12
  files plus the baseline, twice. Both runs exited 0 with the SHA stable and no rewrite (`hook.log`).
- **Not done:** no `scan --baseline` was run and no allowlist pragma was added.

The delta is in `.claude/_sp/gtrec/baseline-delta.json`; the before and after copies are `baseline-before.json` and
`baseline-after.json`.

Staging: `.secrets.baseline` was already staged (M) before this run. The 36 pre-existing staged deletions are still
staged and untouched, and nothing else was staged.

## Boundaries and blockers

- The replacement script's `--verify` now refuses outright. It was not narrowed to check only its
  eighteen-batch prefix, as earlier chain scripts were, because editing a prior recording script was out of
  scope. This is a deliberate boundary. The toolbox helper's `--verify` and the dependent tests hold that prefix
  to its bytes.
- Publication and activation stay blocked. There are 166 reference findings and 5336 uncovered leaves.
- `pip-audit` is deferred non-green (31/11).
- The full suite was not rerun.
- These stay untouched: the quarantined `srd-5-2-1-corpus-36b786d8-fa2.json` (`995976ac…`),
  `issue-5d-source-correction-REPLACEMENT-PACKET.md` (`e462e235…`), the unrelated ` M` files and the 4 stashes.
- These are deferred until after CRD Issue 5d: broad accepted review, Casting Spells and shared coverage.
