# CRD Issue 5d — rules-glossary-completion — accepted-recording handoff

Status: **prepared, not executed.** The Owner has settled semantic acceptance. Nothing is recorded,
committed, published or activated. The coordinating Codex reviews this handoff independently before
any execution step is presented to the Owner.

## Authority

| Item | Value |
|---|---|
| Owner review | `rules-glossary-owner-review.md` (Codex visualizations, 2026-09-25), SHA-256 `c62cd2536162d02aeb23efbddbae41f8cb9c62d1535baacd8ec7a66fbc201d83` |
| Owner decision, verbatim (bold removed) | "I accept this exact proposal, retaining 66 reference findings." |
| Decision item, quoted from the review | "Accept this exact 60-record Rules Glossary completion proposal, retaining 66 reference findings and blocking partial publication/activation. No new reference-resolution approval is needed." |
| Authorized action | one: `accept_proposal` over the recorded Spellcasting chain. There are no resolution drafts and no `resolve` step. |
| Still blocked | partial publication/activation (66 reference findings, 8831 uncovered leaves) |

## Pinned inputs (rehashed 2026-09-26; unchanged throughout preparation)

| Input | SHA-256 |
|---|---|
| Proposal `issue-5d-rules-glossary-completion-REGEN-626c83f8-PROPOSAL.json` | `b31621c0bf97834dad28e136ad6516687d63010cf675ab87226d1527787658bd` (identity `6cafaf579049783f32566cc695a5171f7809ebcf6bb8524129fbca05edfece16`) |
| Accepted oracle `oracles/srd-5-2-1-corpus-626c83f8-209.json` | `c5971b894a0e0f76bbb89956232cd2cddd306099002bb4079fe733641571572f` (14 batches, 235 records, 1497 spans, 50 resolutions) |
| `.secrets.baseline` | `4554f802f2d69a8dd870ff53c15aaa018b0f12337d361bd57d246dd6e69efb2f` |
| Helper `issue-5d-rules-glossary-completion-ACCEPT.py` | `16ad411a396687060b26dbc4c651dd0cb88003819690303bb27cd6c06ee72c4c` (11,603 bytes) |
| Replay chain it imports (untracked; must not change) | `issue-5d-spellcasting-ACCEPT.py` `2bed9d9b…22f6`; `issue-5d-equipment-ACCEPT.py` `458dcee7…c312`; `issue-5d-source-correction-REPLACEMENT-ACCEPT.py` `791ef715…1044`; and their generators and drafts |

## The helper

It uses only the native `accept_proposal`, `serialize_accepted_inputs` and `load_accepted_inputs`
contracts, with no new acceptance or carry-forward machinery.

- **`prior()`** replays the Spellcasting script's own steps at that recording's times
  (`2026-09-25T18:05:59Z` / `18:06:11Z`). The result is pinned to `c5971b89…` and is never read from
  the artifact, so the 14-batch prefix still reproduces after the append.
- **`accept`**
  - Refuses unless the artifact is byte-exactly the prior.
  - Records `batch_id` `rules-glossary-completion`, the verbatim Owner wording as `rule`, and reviewer
    `Ravenlok (Owner)`. `accepted_at` is runtime UTC, truncated to the second.
  - Asserts that the prior is preserved and the counts are 15/295/1613/50, then writes the artifact.
  - Reads the artifact back and must rebuild it (`state accepted`).
- **`--verify`**
  - `prior`: the bytes equal the replayed prior.
  - `accepted`: reads back `accepted_at`, rebuilds, and requires byte equality, 0 resolution violations,
    the prior preserved, 66 reference findings and 8831 uncovered leaves. Findings are computed against
    a temporary copy of the scratch release DB.
  - Any other bytes: `recorded artifact drifted`.
- **`--simulate`** runs the acceptance in memory under `SIMULATION - not an Owner approval`. It writes
  nothing to the repository.

## Evidence (Opus 5.5, medium effort; raw logs in `.claude/_sp/`, rerun on the final helper bytes `16ad411a…`)

**`--simulate`** (`gl_accept_simulate.log`)
- Deterministic across two runs; bytes `12af1ca9…cad9`, 4,064,290 bytes.
- 15 batches, 295 records, 1613 spans, 229 review units, 50 resolutions, 0 violations.
- Prior preserved.
- The bytes reload to themselves, and the 14 recorded batches read back unchanged beside the new one.
- Validation: **66 reference findings, 8831 uncovered leaves.**
- The artifact stayed at `c5971b89…`.
- This matches the independent final simulation. The source review (official PDF pp. 176–191) was not
  rerun.

**State checks on a private temporary copy of the oracle only** (`gl_accept_states.py` /
`gl_accept_states.log`). The temp directory was removed afterwards and the real artifact stayed
unchanged at `c5971b89…`.

| Case | Result |
|---|---|
| `--verify` on the prior copy | `state prior` |
| Unknown action | refused (usage) |
| `accept` on the prior copy | written, then read back as `state accepted` |
| `--verify` on the accepted copy | 15/295/1613/50, 0 violations, prior preserved, 66 refs / 8831 uncovered |
| Second `accept` | refused: `is accepted, not the prior chain` |
| Tampered `rule` | `--verify` and `accept` both refuse: `recorded artifact drifted` |
| Spellcasting `_state` on the appended copy | `recorded artifact drifted` (see dependencies) |

**Lint and protected files**
- Black and Ruff (helper): clean.
- `\r` count: 0.
- Protected hashes unchanged: oracle `c5971b89…`, proposal `b31621c0…`, baseline `4554f802…`, scratch
  DB `5a9cfc2f…`.

## Owner terminal: short Claude prompt (recording step only)

> Record the Owner-accepted rules-glossary-completion batch. Use only
> `rtk proxy venv\Scripts\python.exe .claude/review-notes/issue-5d-rules-glossary-completion-ACCEPT.py`.
>
> 1. Confirm the pinned SHA-256s in `issue-5d-rules-glossary-completion-accepted-recording-handoff.md`.
> 2. Run `--simulate`.
> 3. Run `accept` once.
> 4. Run `--verify`, and report its raw output and the new artifact SHA-256.
>
> Stop at the first failure or denial. Do not retry, do not use another writer, and do not change
> permissions. Do not edit `.secrets.baseline`, do not commit, and do not push.

The new artifact SHA depends on the runtime `accepted_at`, so it is not predictable.

## Post-recording dependencies (settled follow-up; no semantic change)

Each row is marked observed or predicted.

| Dependency | After the append | Basis |
|---|---|---|
| `issue-5d-spellcasting-ACCEPT.py` `_state` / `--verify` | `recorded artifact drifted`. It needs an `appended` branch that delegates to this helper, as Equipment's already does for Spellcasting. | **observed** on the temp copy |
| `issue-5d-equipment-ACCEPT.py --verify` | fails through its `appended` branch, which calls Spellcasting `_state` | predicted (same call) |
| `test_spellcasting_acceptance.py:56` (`SC._state`), `:105` (counts `(14, 235, 1497, 169, 50)`) | fail | predicted |
| `test_equipment_acceptance.py:83`, `test_spellcasting_proposal.py:198` (`SC._state`) | fail | predicted |
| `test_rules_glossary_completion_proposal.py` | fail: the `prior` fixture pins `ORACLE_SHA256` `c5971b89…` and the 14/235/1497 counts, and the in-memory accept would find the batch already recorded. The fix is to rebuild the prior via this helper's `prior()`. | predicted |
| `REPLACEMENT-ACCEPT.py` `verify()` text | still names Spellcasting as the current-artifact verifier (text only) | observed |
| `oracles/README.md` recorded-state text | needs the fifteen-batch state. The file is already ` M` (pre-existing), so it is not touched here. | observed |
| Tests loading the committed oracle (`test_committed_accepted_authority`, `test_accepted_inputs`, `test_oracle`, `test_packaging`, `_replacement_chain`, `test_character_origins_feats_acceptance`) | need a run after recording | predicted |

Any commit waits until these gates are resolved.

## Scanner scope and public-hash inventory

The hook was run against a copy of `.secrets.baseline`. The copy was not modified by the hook and was
deleted afterwards (`gl_gate_secrets_accept.log`). **Observed: 12 findings, all public SHA-256 or
identity values.**

| File | Lines | Values |
|---|---|---|
| Proposal JSON (outstanding 8 of glossary) | 7943, 7944, 7946, 7948, 7951, 7954 | release-binding hashes |
| Test (outstanding 8 of glossary) | 118, 125 | proposal identity, oracle SHA |
| New helper | 75, 81, 83, 88 | prior oracle SHA, proposal SHA, proposal identity, Owner-review SHA |
| Current oracle | none | already covered by the baseline |

**Predicted for the future oracle.** This is a plain `detect-secrets scan` of the current oracle versus
the simulated 15-batch bytes, both in a temp dir (`gl_future_scan.log`).
- 2 new hashed secrets:
  - the schema anchor `proposal_identity` `6cafaf57…` (simulated line 12350);
  - the new batch's `semantic_diff_hash` `7b522be5…` (simulated line 12470).
- 0 removed.
- Existing oracle entries shift line numbers.
- The exact lines depend on the recorded bytes. Take them from the Owner-terminal hook run after
  recording.

Baseline reconciliation is an Owner terminal step after recording:
- Add exactly the live findings.
- Standing-approved verified-obsolete pruning is permitted (for example, entries for staged-deleted
  files).
- Preserve settings, metadata and flags. No pragma.
- Then the normal staged hook must pass twice with 0 findings and a stable baseline.

No baseline edit, staging or mutating scanner command was run here.

## Not changed or deferred

- The accepted material, the 14-batch chain helpers, `.secrets.baseline`, and
  `issue-5d-source-correction-REPLACEMENT-PACKET.md` (untouched, not deleted) were not changed.
- After 5d:
  - the *Casting Spells* structural follow-up;
  - the shared review-unit coverage follow-up;
  - the broader accepted-material review.
- pip-audit (31 findings in 11 packages) remains deferred and not green.
