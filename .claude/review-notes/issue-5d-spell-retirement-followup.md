# CRD Issue 5d — superseded `626c83f8-209` artifact retirement (#132, #137)

**Status: complete.** The exact 28 superseded files are removed and verified absent. The five directory and
authority tests are green, native replay is unchanged, and the scoped baseline prune is staged. Nothing was
committed, pushed, published or activated. No acceptance was recorded or restamped, and no proposal was
mutated.

## Authority

- **Scope:** the exact 28 paths in the taskdir file `spell-retirement-blocked-operation.md`, extracted to
  `.claude/_rc/rec/retire-list.txt` (28 unique paths).
- **Removal:** Owner, verbatim: "I authorize the resumed removal of these exact 28 superseded files through
  normal permission checks, after rechecking that live dependencies use the new accepted artifacts. This is
  in alignment with my previous instruction to remove obsolete construction material once it has no
  current or forward-looking purpose."
- **Resumption after the verification denial:** Owner, verbatim: "Claude must resume the read-only checks,
  then finish the already-authorized scanner maintenance and tests."

## Before removal

- **Current authority:** `srd-5-2-1-corpus-574662e9-0ef.json` has SHA-256
  `b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f`.
- **Native replay:** `issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py --verify` exited 0
  (`.claude/_rc/rec/ret-verify-pre.log`).
- **All 28 targets:** each existed, was untracked, was a regular file and resolved under
  `D:\AI\Claude\afterworlds\`. None matched `574662e9`, `REPLACEMENT-PACKET` or `36b786d8`.
  `.claude/_rc/rec/retire-manifest.json` holds each target's absolute path, byte count and full SHA-256;
  it is hashes only.
- **Dependency recheck:** searched `src`, `tests`, `scripts`, `pyproject.toml`, `.github` and every
  `.claude/review-notes/*.py` for each target's stem. Outside the 28 themselves, the only references were:
  - `oracles/README.md` prose;
  - closed entries in `docs/architecture/issue-5c-5d-clean-restart.md`;
  - one docstring sentence in `REPLACEMENT-ACCEPT.py` (line 28), with no runtime use;
  - stale `__pycache__/*.pyc` bytecode.

  No live test, generator, helper or production path loaded any of them. There was nothing to move.
- **Recovery copy:** none kept, since there was no short-term operational need. A scratch list of the 28
  removal lines (`.claude/_rc/rec/retire-cmds.txt`) was generated and not used, then removed as having no
  forward purpose.

## Removal

1. The first `Remove-Item` call built each path from variables inside a loop. The tool's path guard blocked
   it before execution ("Remove-Item on system path `\` is blocked"). A read-back showed 28/28 still present.
2. The removal was then issued once as 28 explicit `Remove-Item -LiteralPath '<absolute path>' -Confirm:$false`
   lines, with no variables, loops, globs or recursion. It completed with no error.
3. The read-only post-removal check was denied by the auto-mode classifier with no reason given. I stopped
   and reported. After the Owner's resumption instruction it ran through normal permission checks, and the
   deletion was not repeated.

## Post-removal verification (read-only, before any further change)

| Check | Result |
|---|---|
| The 28 manifest paths | 0 present |
| `oracles/` directory | `README.md`; `srd-5-2-1-corpus-574662e9-0ef.json` = `b1f8718f…d639f` (exact); `srd-5-2-1-corpus-36b786d8-fa2.json` = `995976ac1c2b0227…` |
| Quarantined `36b786d8-fa2` | Untouched; it equals the SHA pinned in `src/afterworlds/quarantine.py` |
| Protected `issue-5d-source-correction-REPLACEMENT-PACKET.md` | `e462e235b01f8d3f…` (unchanged, never named in any command) |
| `*574662e9*` review-note artifacts | 21 present |
| Pre-existing staged deletions / other staged | 36 / `M .secrets.baseline` only |
| Stashes | 4 |
| `.secrets.baseline` at that point | `b3d93d8d…dc24` (unchanged) |

The 21 `574662e9` artifacts are also hash-checked by the replay below, not only counted. `--verify`
asserts each of the 17 REGEN proposal files' SHA-256 against `BATCHES` (`REPLACEMENT-ACCEPT.py:318`) and
each reviewed `REGEN-574662e9` drafts file's SHA-256 against `DRAFTS` (`:357`). It also asserts the Spell
Descriptions proposal and drafts against `SD_FILE_SHA256` / `SD_DRAFTS_SHA256` (`:401`, `:424`).

## Replay and gates (after removal)

| Gate | Result | Log |
|---|---|---|
| `REPLACEMENT-ACCEPT.py --verify` | exit 0: state `b1f8718f…`; times 03:34:02Z / 03:34:46Z / 03:35:13Z; 18 batches, 947 records, 4826 spans, 645 units, 1097 resolutions; 0 violations; 17-batch prefix preserved (17, 603, 2776, 305, 51); 143 refs / 5621 uncovered / 0 other; reloads to same bytes | `.claude/_rc/rec/ret-verify-post.log` |
| The five previously red tests (`test_oracle` one-artifact-per-release, `test_packaging` production directory, `test_accepted_inputs` exactly-one-artifact, `test_committed_accepted_authority` sole-artifact and no-refused-candidate) | 5 passed | `.claude/_rc/rec/ret-five.log` |
| Their full files plus `test_schema_6_succession.py` (quarantine pin) | 164 passed | `.claude/_rc/rec/ret-deps.log` |
| Black / Ruff / mypy | Not rerun: this session changed no tracked Python, only `.claude/_sp/ret/*.py` scratch. The prior head's evidence stands | `.claude/_rc/rec/lint-final.log`, `lint.log` |

These are raw runs of `rtk proxy venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider --no-cov`.
No broad suite was rerun, per the task.

## Secrets baseline

The evidence is in `.claude/_sp/ret/` (uncommitted scratch): `baseline-before.json`, `baseline-after.json`,
`baseline-delta.json`, `scan.json` and `hook.log`.

| | |
|---|---|
| Before | `b3d93d8d61a55866ade2dcd07188cee440bffd7468584d77711202f586dadc24` (verified before writing) |
| After | `db14e4a2e9894a189072dfab299d36e00e4b0323e6d0141ea89d185b6d7e451b` (staged; index = worktree) |
| Pruned | 1614 entries under the 28 retired paths' keys. Each file was asserted absent first, so the entries are verified obsolete by absence. 736 of them are the old oracle's |
| Added / line-refreshed | 0 / 0 |
| Entries / files | 4880 → 3266 / 99 → 71 |
| Preserved | top-level settings, filters, version and `generated_at`; every remaining file's entries identical, in the same order; no retired key left |

Scan: the four edited docs have 0 findings, both as scanned and in the baseline:
- `oracles/README.md`;
- `docs/architecture/issue-5c-5d-clean-restart.md`;
- the spell-corrections followup;
- this note.

No new identifiers were introduced. The probe baseline copy was deleted.

Hook: `detect-secrets-hook --baseline .secrets.baseline` ran twice on the staged set and twice on the edited
files plus the baseline. All four runs exited 0, and the SHA stayed stable at `db14e4a2…`. The 36 staged
deletions are unchanged. No `scan --baseline` was run and no allowlist pragma was added.

## Live-doc status updates

- `oracles/README.md`: "superseded and awaits retirement" now says it was retired on 2026-09-27, citing this note.
- `docs/architecture/issue-5c-5d-clean-restart.md`: one sentence appended to the supersession entry. Closed
  entries were not edited.
- `issue-5d-spell-corrections-and-descriptions-recorded-followup.md`: a dated superseded-status pointer
  above its "Retirement (not done: denied)" section. The original text is kept as the record of that time.

## Remaining boundaries

- pip-audit 31/11 stays deferred and non-green.
- Partial publication and activation stay blocked.
- Broad accepted review, Casting Spells and shared coverage come after 5d.
- Stale `__pycache__` bytecode mentioning the old names was left alone. It is regenerated from source and
  no source references it.
- Codex independent review is pending before 5d continues.
