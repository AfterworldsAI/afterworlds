# CRD Issue 5d — spell corrections and Spell Descriptions: recorded follow-up (#132, #137)

Status, as of this note:

- Both exact Owner-approved items are recorded natively in
  `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-574662e9-0ef.json`.
- Nothing is committed, pushed, merged, published or activated. There are no shared-DB or Chroma writes.
- Partial publication/activation remains blocked: 143 reference findings and 5621 uncovered leaves are
  retained.
- **Retirement of the superseded `626c83f8-209` artifacts was denied by the permission layer** and was not
  retried (see *Blockers*). Those files are still on disk, and five directory-listing tests stay red until
  they go.
- This run staged only `.secrets.baseline`. The 36 pre-existing staged deletions remain staged and
  untouched. The protected `issue-5d-source-correction-REPLACEMENT-PACKET.md` was not touched.

## Authority

- **Owner statement (verbatim):** "I accept both exact items in this packet, approve their reference
  resolutions, and retain the 143 reference findings and partial-publication block."
- **Recorded as** the `rule` of every recorded batch and inside each resolution's
  `authorization_reference`:
  - reviewer and authorizer: `Ravenlok (Owner)`;
  - Owner review `spell-corrections-and-descriptions-owner-review.md`, SHA-256
    `fb0bf796ef255186771ad8869a073f6ac2ff15ccc72bb656a4d079f1079e2e6e`;
  - exact packet `spell-corrections-owner-manifest.json`, SHA-256
    `dd31842edb21cee90263e736a8c960177ed9b69dde0fcd1cf008331cd084d16b`, listing 23 JSON files in
    `.claude/review-notes`. All 23 were verified against it before the first write.
- No approval, time or rule from the superseded chain or from the simulation was copied onto a new
  binding. The per-batch rule literals of the earlier recordings are *not* carried over: every batch of the
  fresh chain carries this one consolidated approval.

## Native recording

**Script:** `.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`.

It builds a fresh chain over no prior, because the cross-release check refuses to extend `626c83f8-209`
onto the corrected release `ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` / `5.2.1-corpus.574662e9-0ef`.

Its steps, each failing closed on any unknown prior, intermediate or final state:

- `record` (fresh chain), `accept-spells` and `resolve-spells`;
- each recognises an existing exact intermediate and replays it rather than recording it twice;
- `--verify` reads the step times back from the artifact and rebuilds it.

| Step | Native seam | UTC time (executed) | Bytes after (SHA-256) |
|---|---|---|---|
| chain: 17 `REGEN-574662e9` proposals + 51 resolutions | `accept_proposal` ×17, `resolve_references` ×6 | 2026-09-27T03:34:02Z | `4f78fa80f6c28f5c5569581ad8fc9e0ce7a8e87c5df66aefdef8f75d75c2d35e` |
| spell-descriptions accepted (344 records) | `accept_proposal` | 2026-09-27T03:34:46Z | `c13c33ba446d93f50405cd01b39e25502e5bdc963faa39278078d331f0ca6907` |
| 1046 drafts resolved | `resolve_references` | 2026-09-27T03:35:13Z | `b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f` |

**Spell Descriptions inputs.** The proposal and drafts were not mutated.

- Proposal: SHA-256 `acf1965acebb8ee1e8c1801cddea4ce8d55bfd586659fecb40c30ce9bc13e4b2`, identity
  `6361cf7f6f5015cc43a2870df50647d76589fd4d0d68f93327804aa890049783`.
- Drafts: SHA-256 `5c4373a30a34b74d17a02be2cf3eadebe659e284e1cb7d63962dd3e0aeb75c3a`.

**Old oracle.** `srd-5-2-1-corpus-626c83f8-209.json` was verified at
`a3b81a03c41abf8495634f5118841db2b1f6cfb1759f06a5b88be05d3edaa1e7` before the writes and is unchanged. It
was not rewritten as if accepted against the new binding.

**Replay (final `--verify`, after every edit in this run; `.claude/_rc/rec/verify2.log`, exit 0):**

| Check | Result |
|---|---|
| state | `resolved`, `b1f8718f…639f`, times read back exactly |
| (batches, records, spans, units, resolutions) | (18, 947, 4826, 645, 1097) |
| resolution violations | 0 |
| 17-batch prefix preserved | yes; its (batches, records, spans, units, resolutions) are (17, 603, 2776, 305, 51) |
| reference findings / uncovered leaves / other findings | 143 / 5621 / 0 |
| serialize → load → serialize | same bytes |

The production resolver `committed_inputs_for(*RELEASE)` returns the file at these bytes
(`test_spell_descriptions_proposal::test_the_committed_oracle_records_the_owner_acceptance`).

## Semantic delta against the superseded chain

- **Seven Owner edits to the Level 2 class spell tables:**
  - *Flaming Sphere* is Conjuration in three tables;
  - *Mind Spike* is added for Sorcerers;
  - *Phantasmal Force* is added for Bard, Sorcerer and Wizard.
- **Resulting references:** four new class-table spell references. Chain reference findings and
  uncovered leaves go from (1153, 7657) to (1157, 7657). The Spell Descriptions batch then resolves 1046
  drafts, leaving 143 findings and 5621 uncovered leaves.
- **Everything else** in the seventeen batches is the same content, regenerated against the corrected
  release and accepted in the original order, with the same 51 resolutions.

## Dependent tests, generators and docs moved to the recorded authority

**Principle.** Pins now come from the recorded constants: `REPLACEMENT.RECORDED_SHA256`, `.RECORDED_AT`,
`.APPROVAL`, `.OWNER`, `.AUTHORIZATION_REFERENCE`, `.RELEASE`, `.ACCEPTED_PATH` and `.DRAFTS`. They are
reached through `tests/ingestion/mechanical/_replacement_chain.py`, whose `through(batch)` rebuilds any
prefix natively.

**Preserved-prefix checks replace intermediate SHA pins.** Every "committed file keeps this state" check
is `REPLACEMENT._preserved(...) == []`, a whole-payload multiset inclusion. It replaces:

- the dropped twelve-batch pin `7b1d6f43…`;
- the old `08cca0b7…` and `c5971b89…` prior pins;
- old-script `_check_preserved` calls.

These intermediates were never recorded under this approval, so pinning them would assert unapproved
literals.

**Tests changed:**

- `test_spell_descriptions_proposal.py`:
  - composes over `REPLACEMENT.recorded()`;
  - new `test_the_committed_oracle_records_the_owner_acceptance`, covering bytes, state, read-back times,
    preservation, approval, identity, reviewer, and 1046 resolutions under Owner authorization.
- `test_classes_proposal.py`:
  - the prior is `through("rules-glossary-completion")`;
  - drafts are held to `REPLACEMENT.DRAFTS["classes"][0]`;
  - the committed-oracle test uses `through("class-option-catalogues")` and holds chain refs/leaves at
    (1157, 7657).
- `test_equipment_acceptance.py`, `test_spellcasting_acceptance.py` and
  `test_character_origins_feats_acceptance.py`:
  - rewritten over `through(...)` and the production resolver;
  - counts are kept as they were.
- `test_rules_glossary_completion_proposal.py`, `test_spellcasting_proposal.py` and
  `test_equipment_proposal.py`:
  - the prior is `through(previous batch)`;
  - release and drafts come from `REPLACEMENT`.
  - `test_equipment_proposal`'s prior was `through()` (all 17 batches), which was wrong; it is now
    `through("character-origins-feats")`.
- `test_checks_actions_rests_proposal.py`: the no-write guard now reads `REPLACEMENT.ACCEPTED_PATH`.
- Readiness, oracle, packaging, `accepted_inputs` and committed-authority tests: these expect the
  directory to hold only the new file (see *Blockers*).
- 19 older acceptance/proposal docstrings now name the recording script and oracle. These are prose-only
  edits.

**Release-derived chunk-order statistics.** This defect family was found by the gate runs, and a sibling
audit covered every `unlike_chunks` site in `tests/`.

Why the counts are not approval values:

- Chunk ids are `uuid5` over the package and leaf. The corrected release has a new package UUID, so every
  chunk id changed.
- The number of multi-passage components whose chunk-id order differs from printed order is therefore a
  property of the release.
- The printed-order assertions, which are the real pins, pass unchanged. So does the named-example subset
  `{multiclassing/spellcasting, level_advancement/tiers_of_play}`.

Disposition: **patched**, with each file's comment recording the prior pin. These values come from
neither the recorded constants nor the owner-review delta; they are observed on the corrected release and
listed here for review.

| Site | Was | Now |
|---|---|---|
| `test_equipment_proposal.py` `UNLIKE_CHUNKS` | 81 | 68 |
| `test_character_origins_feats_proposal.py` `UNLIKE_CHUNKS` | 7 | 6 |
| `test_character_creation_foundations_proposal.py` `len(unlike_chunks)` | 18 | 17 |
| `test_character_creation_foundations_proposal.py` `(multi, unlike_chunks)` | (100, 31) | (100, 34) |

**Generators:**

- `issue-5d-spell-descriptions-generator.py`: `draft_targets` and `draft_resolutions` require the prior,
  and `main()` composes over `REPLACEMENT.recorded()`.
- `equipment`, `spellcasting`, `rules-glossary-completion` and `classes`:
  - `PROPOSAL_FILE` / `OPTIONS_PROPOSAL_FILE` / `DRAFTS_FILE` now name the `REGEN-574662e9` files;
  - the release line now names `ebdd9333-…` / `574662e9-0ef`.
- The twelve earlier generators already name non-REGEN files that are not being retired; they are left
  as they were (pre-existing).

**Docs.**

- `oracles/README.md`: a *Current* paragraph for `574662e9-0ef` is added above the existing section,
  which is marked superseded. The file's earlier diff is this branch's own prior work.
- `docs/architecture/issue-5c-5d-clean-restart.md`: an appended supersession entry. Closed entries are
  not edited.

## Retirement (not done: denied)

> **Superseded status (2026-09-27):** after a later Owner authorization, the 28 files were removed.
> See `issue-5d-spell-retirement-followup.md`. The text below records the state at the time of this note.

**Planned, all untracked, so deletion would be irreversible:**

- a scratch copy to `.claude/_rc/retired/`;
- a SHA-256 manifest;
- deletion by exact name, never glob.

**Candidates, with their current purpose:**

| Artifact | Current purpose | Live dependents |
|---|---|---|
| `oracles/srd-5-2-1-corpus-626c83f8-209.json` (`a3b81a03…`) | superseded authority | none that select it; it still makes 5 listing tests red and is still in `.secrets.baseline` (736 entries, kept) |
| `issue-5d-source-correction-REPLACEMENT-ACCEPT.py`, `-classes-ACCEPT.py`, `-equipment-ACCEPT.py`, `-spellcasting-ACCEPT.py`, `-rules-glossary-completion-ACCEPT.py` | replay the superseded chain | only each other; no test or generator imports them now |
| 15 `*-REGEN-626c83f8-PROPOSAL.json`, 3 `*-resolutions-REGEN-626c83f8-DRAFTS.json` | superseded chain inputs | the old ACCEPT scripts and COMPARE only |
| `issue-5d-classes-PROPOSAL.json`, `-class-option-catalogues-PROPOSAL.json`, `-classes-resolutions-DRAFTS.json` | superseded Classes inputs | old `classes-ACCEPT.py` and COMPARE only; the generator is repointed |
| `issue-5d-class-spell-tables-COMPARE.py` | reproduces the pre-acceptance old-vs-new comparison; its result is held in `...-REPLACEMENT-REVIEW.md` | none; it cannot run once its inputs go, so it retires with them |

**Kept:** review packets and `.md` records, including `issue-5d-equipment-REGEN-626c83f8-REVIEW-PACKET.md`
and the protected packet. These are records, not maintained copies.

## Gates (exact working tree; raw logs in `.claude/_rc/rec/`)

All pytest runs used `rtk proxy venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider --no-cov`.
Each ran attached, one chunk at a time, under 600 s.

| Run | Result | Log |
|---|---|---|
| `test_spell_descriptions_proposal.py` | 21 passed | `sd.log` |
| equipment / spellcasting / character-origins-feats acceptance | 21 passed | `acc2.log` |
| `test_classes_proposal.py` | 27 passed | `cls.log` |
| `test_rules_glossary_completion_proposal.py` | 34 passed | `gl.log` |
| spellcasting + equipment proposal | 140 passed, 1 failed (chunk-order 81→68, then repinned) | `sceq.log` |
| checks-actions-rests proposal + the repinned equipment test | 28 passed | `car.log` |
| 11 earlier acceptance suites (all `publication_stays_blocked…` included) | 38 + 42 passed | `accA.log`, `accB.log` |
| reference/movement/combat-damage/core-play ×2 proposals | 134 passed | `propA.log` |
| character-creation-foundations + character-origins-feats proposals | 101 passed, 3 failed (chunk-order family), then repinned: 3 passed | `propB.log`, `propB2.log` |
| oracle, packaging, accepted_inputs, readiness, committed-authority | **162 passed, 5 failed** (see *Blockers*) | `grpA.log` |
| `REPLACEMENT-ACCEPT.py --verify` | exit 0 | `verify2.log` |
| Black (tests/ingestion/mechanical, 6 scripts) | unchanged | `lint.log` |
| Ruff (same set) | clean after one E501 fix in `_replacement_chain.py` | `lint.log` |
| `mypy src/` | no issues in 235 files | `lint.log` |
| Final head: `black --check tests/ src/`, `ruff check tests/ src/`, the 5 repinned/rewrapped test files | 540 unchanged; all checks passed; 233 passed | `lint-final.log` |
| CR | 0 `\r` in every changed file | |

`mypy` over the changed test files is not a repository gate. It reports `import-untyped` for every
`afterworlds` import in this environment, so it is not evidence either way.

## Secrets baseline

Scoped update from the exact starting bytes. Scratch evidence (uncommitted) is in `.claude/_sp/sdrec/`:
`baseline-before.json`, `baseline-after.json`, `baseline-delta.json`, `scan.json`, `verify.json`,
`scan-after.json` and `hook.log`.

| | |
|---|---|
| Before | `a91b874db24e9015e4caeafe5b259eb86f56f4df87df8a4f5b8c2cd997017084` (verified before writing) |
| After | `b3d93d8d61a55866ade2dcd07188cee440bffd7468584d77711202f586dadc24` (git blob `ed5d38d0…`, index = worktree) |
| Scope | 43 scanned files: the 33 changed tests plus the ACCEPT script, 5 generators, this note, the clean-restart doc, the oracles README and the new oracle |
| Added | 1010: 1001 in `srd-5-2-1-corpus-574662e9-0ef.json` (new file), 8 in the ACCEPT script (named SHA/identity constants), 1 in `test_spell_descriptions_proposal.py` |
| Pruned | 31 verified obsolete: pins these tests no longer contain, in files that still exist; the rescan no longer finds them |
| Line-refreshed | 42 |
| Entries / files | 3901 → 4880 / 98 → 99 (3901 + 1010 − 31 = 4880) |

Every added value was recovered from its line (SHA-1 = `hashed_secret`) and recomputed natively as a
public value: 8 file SHA-256s, 19 proposal identities, 18 `semantic_diff_hash` values (`batch_diff_hash`
recomputed for every batch), 1 schema-lift hash pair, 5 release-binding/policy values of the reviewed
proposals, and 958 16-hex `fact_key` values. Those are admitted by membership in the set recomputed
via `fact_key(f)` over every reviewed proposal's components' `all_facts()`. A structural filter also
requires the value to be on a `"fact_key":` field or inside a `target_key` list; that filter is a
sanity check, not the admission. 0 were unverified.

Preserved: top-level settings/plugins/filters/version/`generated_at`; every untouched file's entries
byte-identical; existing key order; `is_verified: false` on additions. The old `626c83f8-209` oracle's
736 entries are kept because the file still exists.

Staging: `.secrets.baseline` was already staged (M) before this session's `git add`. I did not record the prior
index blob before replacing it, so I can't establish whether it equalled the a91b874d bytes
(blob `092924c5…`); the add replaced it with b3d93d8d. After: a rescan of all 43 files shows 0 new and
0 obsolete. It ran before this section's full SHAs were added. The edited note was then rechecked with the
hook, twice, with exit 0 and a stable SHA. `detect-secrets-hook --baseline .secrets.baseline`
was run twice on the staged set and twice on the 43 files plus the baseline. All four runs exited 0 and the
SHA stayed stable. The first attempt (before `git add -- .secrets.baseline`) exited 1 with "baseline is unstaged". That is
the expected ordering message, not a finding. The 36 pre-existing staged deletions are unchanged, and the only
other staged path is `.secrets.baseline` (M). No `scan --baseline` was run, and no new allowlist pragma was added.

## Blockers and boundaries

> **Superseded status (2026-09-27):** item 1 is resolved. The 28 files were removed under a later Owner
> authorization, and the five tests below now pass. See `issue-5d-spell-retirement-followup.md`.

1. **Retirement denied.** The permission layer denied the script that would have copied, deleted and
   manifested the 28 untracked superseded files. Per standing rule this was not retried or worked around.
   Consequences:
   - these tests stay red until the files are removed:
     - `test_oracle::test_the_committed_oracle_directory_holds_one_artifact_per_release`;
     - `test_packaging::test_the_production_oracle_directory_ships_only_reviewed_content`;
     - `test_accepted_inputs::test_exactly_one_accepted_artifact_is_committed_for_the_release`;
     - `test_committed_accepted_authority::test_the_release_resolves_to_this_sole_committed_artifact`;
     - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`, which globs the
       directory and so still sees the old identities;
   - the old oracle's 736 baseline entries are kept, because the file exists.

   Needed: Owner/operator permission for that exact deletion, or an Owner decision to keep the files.
2. **pip-audit:** 31 findings in 11 packages, explicitly deferred; not green.
3. **Publication/activation:** blocked; 143 reference findings are retained by the Owner's decision.
4. **No full suite** was run (over 600 s is not allowed). Coverage is the changed and dependent files
   above.
5. **Deferred as standing:** broader accepted-review, Casting Spells, and shared coverage (after 5d).
