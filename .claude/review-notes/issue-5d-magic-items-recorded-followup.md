# CRD Issue 5d — Magic Items recorded: follow-up (#132, #137)

**Status: RECORDED in the working tree, uncommitted.** Nothing was committed, pushed, merged, published or
activated. No shared DB or Chroma was written. The partial-publication block stays. Codex reviews this
independently. Written 2026-09-28T00:43Z (last revised after the split rerun and mypy recheck).

## Authorization recorded

- **Approval, verbatim:** "I accept this exact Magic Items proposal and its one reference resolution, retaining
  315 reference findings and the partial-publication block."
- **Answers:** `magic-items-owner-review.md` in
  `C:/Users/raven/.codex/visualizations/2026/09/21/01a0c27d-eef6-78f0-82cb-89e991b26cfe`
  (SHA-256 `16e6475f6092fa68113ee66119e7141aa78c41e3db31ec2ee71ec506955fe634`, read only).
- **Reviewer:** `Ravenlok (Owner)`, the same `OWNER` constant the replacement chain records.
- **Approved files** (pins rechecked at 2026-09-27T23:26:52Z, immediately before mutation; `pins-pre.log`):
  - `issue-5d-magic-items-PROPOSAL.json`: SHA-256 `e0f8c657cd0edebc22f8865a0ffffdf16f6a907d7f7d5cbb70f75a6ddf2ab1d0`,
    identity `aecc9ea52a8af77a62a29ee720211489d29d64eece057d9927b754e3934dcc39`.
  - `issue-5d-magic-items-resolutions-DRAFTS.json`: SHA-256
    `2207ddc3db1fae22f8d65471ee2fbb88d6ed96e55fbe91e313a0bbd59548e23c`. It holds one resolution,
    `resolve-gameplay-toolbox-travel-pace-special-movement-carpet-of-flying-magic-items-1` →
    `magic_items.carpet_of_flying`.
  - Prior oracle `671f47d7…` (19 batches, 980 records, 1098 resolutions); baseline `5f5a5f19…`.
- The acceptance's rule is the verbatim approval. Each record's `authorization_reference` names the owner review
  with its SHA, both packet files with their SHAs, and the approval text.

## Recording

`.claude/review-notes/issue-5d-magic-items-ACCEPT.py` is the bounded helper, patterned on
`issue-5d-gameplay-toolbox-ACCEPT.py`. It uses the native seams only: `accept_proposal`, then
`resolve_references`, with `serialize_accepted_inputs` / `load_accepted_inputs`. The nineteen-batch prior is
rebuilt through the toolbox helper at its recorded times and pinned to `671f47d7…`. The helper recognizes three
states (prior, magic-items-accepted, resolved). It replays an intermediate before continuing it, and it refuses
anything else, fail-closed.

| Step | Real execution UTC | Oracle SHA-256 after |
|---|---|---|
| Initial (pinned before mutation) | — | `671f47d706f5eb484c70d8bacaa9d169801c014689d7fd400e018e3d999eae95` |
| `accept-magic-items` | 2026-09-27T23:27:11Z | `27fde6663f4ecc52dd1ca8e280e303380e52dbb2ba728cbd6118267625a7adee` |
| `resolve-magic-items` (replayed the intermediate first) | 2026-09-27T23:28:26Z | `fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62` |

- The times are the wall clock at execution. `--simulate` ran first with a simulated reviewer and wrote nothing.
- **Final oracle:** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-574662e9-0ef.json`, SHA-256
  `fc62c47c…` (untracked, as before).
- For audit, the prior bytes are at `.claude/_sp/mirec/oracle-prior-671f47d7.json` and the intermediate at
  `oracle-intermediate-27fde666.json`.

## Native replay, preservation and findings

`issue-5d-magic-items-ACCEPT.py --verify` exited 0 (`.claude/_sp/mirec/verify.log`). It checks:

- the prior rebuilt natively at its recorded times, equal to `671f47d7…`;
- both steps rebuilt at the times read back from the file, byte-equal to the committed file, which reloads to the
  same bytes;
- counts: batches, records, spans, units and resolutions went (19, 980, 5111, 679, 1098) → (20, 1250, 6450, 950,
  1099);
- the prior payload is preserved as a multiset (`_preserved`, with obligations checked separately below): 980
  records, 1098 resolutions and 19 batches, with every acceptance, identity, provenance entry and time unchanged;
- the two shared Equipment records keep their accepted definitions;
- the only new acceptance and resolution are this batch's, so nothing was restamped or duplicated;
- findings: 315 reference findings (from 166), 4004 uncovered leaves (from 5336), 0 other findings and 0
  resolution violations.

Two further checks:

- **Stale rerun:** a rerun of `accept-magic-items` on the resolved file refused with exit 1 (`rerun-refused.log`).
- **Toolbox script:** `issue-5d-gameplay-toolbox-ACCEPT.py --verify` now refuses the current file fail-closed, with
  "unrecognized batches" (`toolbox-verify.log`). The Magic Items helper's `--verify` is the whole-file replay. The
  toolbox script is unchanged.

## Exact derived-obligation delta

The proposal adds 270 new records (all `magic_items.*`) and a disjoint `magic_items_table` component to each of two
accepted Equipment records. Of the 980 prior obligations, exactly two changed, and only in
`prose_bound_components`:

| Record | Before | After |
|---|---|---|
| `equipment.adventuring_gear.potion_of_healing` | `["potion_of_healing"]` | `["magic_items_table", "potion_of_healing"]` |
| `equipment.adventuring_gear.spell_scroll` | `["spell_scroll"]` | `["magic_items_table", "spell_scroll"]` |

The other 978 are byte-identical, and the 270 new obligations belong to the new records. The helper pins this
exactly with `obligation_delta` (`SHARED_KEYS`, `SHARED_COMPONENT`). It is not a generalized carry-forward: any
other obligation change fails.

## Dependency changes (settled only)

| File | Change |
|---|---|
| `.claude/review-notes/issue-5d-magic-items-generator.py` | `current()` loads the file while it holds the pinned nineteen-batch bytes; otherwise it rebuilds them through the helper's `prior()`. SHA now `72029c25…` (was `5b5277b9…`) |
| `tests/.../_replacement_chain.py` | `LATEST` is the Magic Items helper, so `COMMITTED_SHA256` is its resolved SHA. New `kept_whole(prior, committed)`: `_preserved` with obligations blanked, plus `LATEST.obligation_delta` |
| `tests/.../test_magic_items_proposal.py` | The in-memory test pins the live file to the helper's `resolved` SHA. New `test_the_committed_oracle_records_the_owner_acceptance` checks bytes, state, times, preservation, the exact obligation delta, approval/identity/rule, the one acceptance and resolution, and that the resolution equals DRAFTS |
| `tests/.../test_gameplay_toolbox_proposal.py` | The committed-oracle test rebuilds its recording at `RECORDED_AT` and pins it to its `resolved` SHA. It holds it against the committed file by batch set, `_preserved` with obligations blanked, and the exact obligation delta. The live-file pin was dropped |
| `tests/.../test_spell_descriptions_proposal.py` | The committed-file preservation check blanks obligations and asserts the exact obligation delta |
| `tests/.../test_classes_proposal.py`, `test_rules_glossary_completion_proposal.py`, `test_spellcasting_proposal.py`, `test_equipment_acceptance.py`, `test_spellcasting_acceptance.py` | Each "the committed file keeps the prior whole" check (6 sites) now uses `kept_whole` |
| `tests/.../test_source_release_readiness.py` | The batch set adds `magic-items`; 6450 spans, 1099 resolutions |
| `tests/.../test_committed_accepted_authority.py` | The Magic Items proposal is added to the named identity set of `test_no_refused_candidate_is_selectable` |
| `src/.../oracles/README.md` | "Current" now reads twenty batches, 1250 records, 1099 resolutions, `fc62c47c…`; the toolbox paragraph notes that its `--verify` now refuses |
| `docs/architecture/issue-5c-5d-clean-restart.md` | A supersession entry is appended; closed entries are not edited |
| `.claude/review-notes/issue-5d-magic-items-review.md` | A superseding status banner; the rest is unchanged |

No source, release, schema or `src/` code changed.

### Sibling audit: committed-file preservation (defect family)

- **Trigger:** the gates showed the same failure in several tests: `.obligations lost 2 of N` wherever a prior
  that holds the Equipment batch is held whole against the committed file.
- **Structures inspected:** every `_preserved(` call, every `committed_inputs_for(` / `load_accepted_inputs(ORACLE`
  / `ACCEPTED_PATH` reader, and every `.obligations` reader under `tests/`.

| Site | Disposition |
|---|---|
| The 6 sites above, plus Spell Descriptions and toolbox | patched: `kept_whole`, or the same explicit pattern |
| `test_character_origins_feats_acceptance.py:205` | already safe: its prior predates Equipment, so the two shared Equipment records are absent from the prior's obligations and there is nothing for the file to extend |
| prior→final `_preserved` in the equipment and spellcasting acceptance tests (in-memory, never the file) | already safe: both sides are native rebuilds that stop before Magic Items, so neither holds the delta |
| `test_character_creation_foundations_acceptance.py:188` | already safe: it admits the file's obligations by subset (`PRIOR ⊆ INPUTS`), and the delta only adds families to existing obligations |
| `test_checks_actions_rests_proposal.py` | already safe: its prior is a native in-memory rebuild; it reads the committed file only as a SHA-256 before and after its in-memory test (lines 809, 843), never its obligations |
| `test_oracle.py:424` | already safe: it admits the file's obligations by recomputation, `set(obligations) == set(derive_obligations(representation))`, and the delta is exactly what derivation yields for the accepted Magic Items records |
| `test_committed_accepted_authority.py:868, 1108` | already safe: a load-and-lift round trip of the same file (`lifted == inputs`), and one obligation per accepted record keyed by record, which the delta does not change |
| packaging / production-release / readiness suites | already safe: they build their own fixture payloads with `obligations=()` or `[]`, never the committed file's |
| frozen-prior and schema readers | already safe: they read frozen fixture oracles under `tests/ingestion/mechanical/data/`, not the committed file |

Batch-order defect in the new tests themselves:

- A loaded file holds its batches in canonical order, and its `resolved_scope` tuples differ from an in-memory
  rebuild.
- The first versions of the new committed-file tests compared loaded batches to rebuilt ones, and failed.
- Disposition: patched. They now compare rebuilt against rebuilt (MI) or by batch set (toolbox). Batch
  preservation is carried by `_preserved`.

## Gates (raw logs in `.claude/_sp/mirec/`)

All runs used `rtk proxy venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider --no-cov`, attached. Each log
starts with the command line and ends with `exit=`.

| Scope | Result | Log |
|---|---|---|
| MI proposal: 11 static tests | 11 passed, exit 0 (207 s) | `pytest-mi-a.log` |
| MI proposal: in-memory, ten-sections and committed-oracle tests | 2 passed, 1 failed (batch order, above), exit 1 | `pytest-mi-b.log` |
| MI committed-oracle test after the fix | 1 passed, exit 0 | `pytest-mi-b2.log` |
| MI proposal: 20 service tests, first run | 20 passed, exit 0, but 834 s, over the 600 s per-group target, and moved to the background by the tool, so not counted as a gate | `pytest-mi-c.log` |
| MI proposal: the same 20 tests split in two, attached | 9 passed, exit 0 (419 s); 11 passed, exit 0 (597 s) | `pytest-mi-c1.log`, `pytest-mi-c2.log` |
| `test_gameplay_toolbox_proposal.py` | 15 passed, 1 failed (batch order), exit 1 | `pytest-toolbox.log` |
| toolbox committed-oracle test after the fix | 1 passed, exit 0 | `pytest-toolbox2.log` |
| `test_spell_descriptions_proposal.py` | 20 passed, 1 failed (obligation family), exit 1 | `pytest-sd.log` |
| COF / equipment / spellcasting acceptance and readiness | 2 failed (family), 34 passed, exit 1 → after the fix 36 passed, exit 0 | `pytest-acc.log`, `pytest-acc2.log` |
| classes, glossary and spellcasting proposals, `-k "committed or prior or recorded"` | 1 failed, 4 errors (family), exit 1 → after the fix 9 passed, exit 0 | `pytest-clsgl.log`, `pytest-clsgl2.log` |
| spell descriptions and checks-actions-rests, `-k "committed or prior or recorded"` (after the fix) | 3 passed, exit 0 | `pytest-sd2.log` |
| oracle, packaging, accepted_inputs, committed_accepted_authority, CCF acceptance, quarantine | 204 passed, exit 0 | `pytest-grp.log` |
| 10 reader suites (publication, production release, retained proposals, …) | 507 passed, 14 skipped, exit 0 | `pytest-readers.log` |
| 10 frozen-prior and schema reader suites | 241 passed, exit 0 | `pytest-readers2.log` |
| black `--check` / ruff on all changed Python files | clean / clean | `lint-final.log`, `lint-family2.log` |
| `mypy src/` | no issues in 235 files, exit 0 | `mypy-final.log` |
| expanded mypy (`src/` + MI source, generator, ACCEPT, MI test) | the 3 pre-existing COF errors only, exit 1 | `mypy-final.log` |

A wider mypy scope, rerun after `kept_whole` landed, adds `_replacement_chain.py` and every changed test
(`mypy-wider2.log`, 13 targets). It reports 22 errors in 6 files, exit 1:

- `_replacement_chain.py` and the two acceptance tests: none.
- 11 are established by earlier raw logs: 3 COF, 3 classes, 1 glossary, 4 spellcasting.
- The other 11 (8 Spell Descriptions, 3 toolbox) were first observed in this expanded scope. They look unrelated
  and are inferred to be pre-existing, but no comparable earlier log exists. That none sits on an edited line
  (the imports, the `kept_whole` sites at classes 832, glossary 183 and 1032, spellcasting 199, and the committed
  tests at Spell Descriptions 643–650, toolbox 630–642) does not prove their history.
- All 22 are deferred, not fixed, and the gate stays non-green.

One error this change had introduced (a reused `new` name in the toolbox test) was fixed.

The generator's committed-bytes test (`test_the_committed_bytes_are_what_the_published_release_derives`, in
`pytest-mi-a.log`) still passes, so regeneration stays byte-identical to the approved PROPOSAL and DRAFTS.

Not run:
- the unchanged full suite (not duplicated);
- a new source audit or batch authoring (out of scope);
- `pip-audit`, which is deferred non-green (31/11, as previously recorded).

## Secrets baseline (scoped)

| | |
|---|---|
| Before | `5f5a5f1983be261d80e0618fc627e2c5beb1ef1aed7d29354ad5b896eda9c9db` (asserted before writing) |
| After | `5e69a1089df279deea90e7682eee8338133af04c599ed5a9000422537448cead` (staged; index = worktree, blob `77d95960…`) |
| Added / pruned / line-refreshed | 9 / 0 / 983 (975 in the oracle, 4 in each of the two proposal tests) |
| Entries / files | 3305 → 3314 / 80 → 81 |
| Preserved | top-level settings, plugins, filters, version and `generated_at`; every other file's entries identical; existing key order; `is_verified` false on added entries |

The changed files were rescanned under the baseline's own plugins and filters, on a copy under
`.claude/_sp/mirec/` that was deleted afterwards. Only two had new findings, and all 9 were recovered from their
lines and verified public by recomputation (`verify-baseline.log`, `verify.json`):

- **Oracle:** the Magic Items `proposal_identity` (recomputed from the PROPOSAL) and its `semantic_diff_hash`
  (`batch_diff_hash` over the natively rebuilt batch).
- **ACCEPT.py:** the SHA-256 of the PROPOSAL, DRAFTS and owner review; the identity; and the three state SHAs
  (native rebuilds of prior, magic-items-accepted and resolved).

No entry was obsolete, so none was pruned. After the update, a rescan showed every file in sync: 0 new, 0 obsolete,
lines equal (`scan-after.log`). A second pass over all 18 changed files, including the family-fix tests and this
note, found nothing to add, prune or move (`scan2.log`, `apply2.log`).

- **Hook:** after `git add -- .secrets.baseline`, `detect-secrets-hook --baseline .secrets.baseline` ran on the 18
  files plus the baseline, twice. Both runs exited 0 with the SHA stable and no rewrite (`hook2.log`; the first
  pass is in `hook.log`, the rerun after this note's final edit in `hook4.log`).
- The delta is in `apply.log` (pass 1) and `apply2.log` (pass 2). The copies are `baseline-before.json` and
  `baseline-after.json`.

- **Not done:** no `scan --baseline` was run and no allowlist pragma was added.
- **Staging:** `.secrets.baseline` was already staged (M) before this run and was re-staged by name. The 36
  pre-existing staged deletions are still staged and untouched, and nothing else was staged.

## Boundaries and blockers

- The toolbox script's `--verify` now refuses outright, as the replacement script's did before it. It was not
  narrowed, because editing a prior recording script was out of scope. This is a deliberate boundary. The Magic
  Items helper's `--verify` and the dependent tests hold its nineteen-batch prefix to its bytes.
- The obligation delta is a reviewed, exact exception, not a carry-forward rule. `kept_whole` allows only the two
  named enlargements.
- Publication and activation stay blocked: 315 reference findings and 4004 uncovered leaves remain.
- Non-green and deferred (not an all-green result):
  - the expanded mypy scope, with 3 pre-existing COF errors (22 in the wider 13-target scope: 11 established
    by earlier logs, 11 newly observed with no comparable earlier evidence);
  - `pip-audit` (31/11).
- The full suite was not rerun.
- These stay untouched: the quarantined `srd-5-2-1-corpus-36b786d8-fa2.json`,
  `issue-5d-source-correction-REPLACEMENT-PACKET.md`, the earlier quarantine, the unrelated ` M` files and the 4
  stashes.
- These are deferred until after CRD Issue 5d: broad accepted review, Casting Spells and shared coverage.
