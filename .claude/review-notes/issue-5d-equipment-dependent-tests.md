# Issue 5d — Equipment post-recording dependencies (2026-09-25)

Scope: bring live tests, pins, replay and current docs that still assumed the
twelve-batch / 136-record artifact up to the recorded Equipment state. This is
not a semantic review. The oracle, proposal, drafts and acceptance helper were
not re-recorded, regenerated or edited. There is no commit, push, publication,
activation, shared-DB or Chroma write.

## Recorded state relied on (unchanged, re-verified)

- Oracle `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json`:
  SHA-256 `08cca0b7…03fb` (the full value is in the `--verify` output below).
- `rtk proxy venv\Scripts\python.exe .claude/review-notes/issue-5d-equipment-ACCEPT.py --verify`
  exited 0. It reports:
  - state `resolved`, 13 batches, last `equipment`;
  - 216 records, 1425 spans, 150 review units, 49 resolutions, 0 violations;
  - prior preserved (136 records, 6 resolutions, 12 batches);
  - `accepted_at 2026-09-25T05:47:17Z`, `resolved_at 2026-09-25T05:47:29Z`.
- Helper `issue-5d-equipment-ACCEPT.py` SHA-256 `24d00787…275a` (not edited).
  `issue-5d-source-correction-REPLACEMENT-PACKET.md` SHA-256 `e462e235…cae1`
  (not touched).

## Changes

Earlier-batch meaning is kept through native reconstructed prefixes
(`_replacement_chain.through(...)`), not historical-only copies.

- **`tests/ingestion/mechanical/test_equipment_acceptance.py` (new).**
  - It loads the unedited helper and rebuilds the twelve-batch prior through
    `EQ.prior()`, which uses the replacement chain and is pinned to `7b1d6f43…`.
  - It replays both Equipment steps with `EQ._state`.
  - It checks:
    - the committed bytes equal the replay, and equal the production
      resolver's `committed_inputs_for` output;
    - the read-back times;
    - the exact proposal identity, the rule "I accept it." and 409
      acceptances under the Owner;
    - that the prior is preserved: 12 batches, 136 records and 6
      resolutions, using `_check_preserved`, with lifts, policy transitions,
      schema and binding equal;
    - totals of 13 / 216 / 1425 / 150 / 49;
    - that the 43 new resolutions equal the generator's reviewed drafts, all
      scoped `srd-5.2.1/equipment` and targeting `equipment.*`;
    - that their authorizations are all (Owner, Owner, authorization
      reference, `resolved_at`), with 0 violations;
    - that publication is still blocked:
      - prior: 9443 leaf findings + 91 reference findings;
      - final: 9068 leaf findings + 58 reference findings;
      - the only non-"unresolved" reference is the unknown target
        `glossary.improvised_weapons`.
  - It adds no 64-hex literals.
  - It is untracked (`??`), as is `test_equipment_proposal.py`, so `git diff`
    does not show either one.
  - Diff attribution: the working-tree diffs of the tracked test files also
    contain earlier restart edits. This pass changed 3 lines in
    `test_committed_accepted_authority.py`: the import, the constant and the
    set member.
- **`test_character_origins_feats_acceptance.py`.**
  - `INPUTS = through(BATCH)` replaces reading the committed file.
  - The `7b1d6f43…` pin now holds `serialize_accepted_inputs(through(BATCH))`.
  - It was edited line-neutral, so the baselined literal stays at line 199.
- **`test_equipment_proposal.py`.**
  - `prior()` is `through()`, with no file-equality assert. The pin lives in
    the origins acceptance test.
  - Docstrings now point at `test_equipment_acceptance`.
  - The `IDENTITY` literal stays at line 136.
- **`test_source_release_readiness.py`.** Thirteen accepted batches. The span
  sum gains Equipment's `+ 409`, giving 1425.
- **`test_committed_accepted_authority.py`.**
  - `test_no_refused_candidate_is_selectable`'s committed-identity set gains
    `EQUIPMENT_PROPOSAL` (`NOTES / "issue-5d-equipment-REGEN-626c83f8-PROPOSAL.json"`,
    identity `e25f7a82…`).
  - `NOTES` is imported from `_replacement_chain`. `proposal_path` refuses
    non-replacement batches.
- **`src/afterworlds/ingestion/mechanical/oracles/README.md`.**
  - Thirteen batches and forty-nine resolutions.
  - A new `equipment` bullet and a paragraph on the 43 resolutions.
  - The replay pointer now names `issue-5d-equipment-ACCEPT.py --verify`, and
    says the REPLACEMENT script's own `--verify` checks only the pinned
    twelve-batch prefix (after the follow-up below).
  - The remaining-findings list is now 58: 18 broad + 30 catalogue members +
    9 Equipment pointers + 1 unknown target, with 9 068 uncovered leaves.
- **`docs/architecture/issue-5c-5d-clean-restart.md`.** One appended paragraph
  recording Equipment: 2026-09-25, `08cca0b7…03fb`, 13 / 216 / 49, and the
  `--verify` notes.

## Gates (exact; not a full-suite result)

All gates ran attached, through `rtk proxy venv\Scripts\python.exe`, with `-p no:cacheprovider`.

| Gate | Result |
|---|---|
| `pytest` (with coverage) on `test_equipment_acceptance`, `test_character_origins_feats_acceptance`, `test_source_release_readiness` | 31 passed, 0 failed; exit 1 from the global 80% coverage floor, which a partial run cannot meet. No separate `--no-cov` run of these three files was made. |
| `pytest --no-cov test_equipment_proposal.py` | 102 passed, exit 0 |
| `pytest --no-cov` on 10 dependent files: quarantine, accepted_inputs, committed_accepted_authority, oracle, packaging, production_release, publication, runtime_production_release, subclass_refusal, checks_actions_rests_proposal | 441 passed, 14 skipped, 1 failed. The failure was `test_no_refused_candidate_is_selectable`, fixed above. |
| `pytest --no-cov test_committed_accepted_authority.py`, after the fix | 20 passed, exit 0 |
| `black --check` and `ruff check` on the 5 changed test files | 5 unchanged / all checks passed |
| `issue-5d-equipment-ACCEPT.py --verify` | exit 0, as above |
| `issue-5d-source-correction-REPLACEMENT-ACCEPT.py --verify` | at the time: exit 1, `committed artifact drifted`. Resolved afterwards by the follow-up below; it now exits 0 on the pinned twelve-batch prefix. |

Not run:

- **Full `pytest` suite and coverage floor.** A full mechanical run projected
  at about 2.5 h was stopped, and nothing from it is cited. Full-green is not
  claimed.
- **`mypy src/`.** No `src/*.py` changed. A standalone `mypy` run on
  `test_equipment_acceptance.py` reported only 5 `import-untyped` errors, one
  for each `afterworlds` import (lines 24, 25, 31, 32, 35). That run is not
  the configured gate and is not counted.
- **pip-audit.** The 31 findings in 11 packages remain deferred and non-green.

## Secrets baseline (no mutation)

`.secrets.baseline` is still staged `M `, working-copy SHA-256
`971e66b2…4899` (CRLF). The index blob is its LF form, `b91eaac1…82a1`, per
`.gitattributes eol=lf`. Every check below read it or a temporary copy under
`.claude/_eqdep_bl/`.

- **Settings.**
  - Compared against `HEAD`: `version`, `generated_at`, `plugins_used` (25) and
    `filters_used` (10) are equal.
  - All remaining entries have no metadata changes other than line numbers.
- **Delta against `HEAD`.**
  - 65 files → 59, 1526 entries → 1533.
  - Against `HEAD` (multiset by file and metadata): 404 adds, 397 removals,
    13 moves.
  - `HEAD` predates the Owner pass's own starting copy (80 files / 1911
    entries, never committed). The counts still reconcile exactly with the
    Owner's report:
    - all 397 Owner removals are in files tracked at `HEAD`: 393 in the 25
      deleted files (all gone; none still in the index) plus the 4 public
      literals in `test_character_origins_feats_acceptance.py`;
    - so the Owner's start is `HEAD` plus 385 entries in 15 files that are
      untracked at `HEAD`: 1911 − 1526 = 385 = 404 − 19, and
      80 − 65 = 15 = 19 new-vs-`HEAD` files − 4 files new in the Owner pass;
    - check: 1911 − 397 + 19 = 1533 = 1526 − 397 + 404.
  - Git alone cannot attribute two things:
    - which 19 of the 404 adds the Owner made, and which 385 existed before;
    - the 129 oracle moves (the oracle is untracked, so all 151 of its
      entries show as adds against `HEAD`).
  - The fresh-scan check below is consistent with the Owner's account.
  - `docs/sources/community/dnd-5e-srd-markdown/source_pin.json` shows 13 line
    moves and 2 adds against `HEAD`, which the Owner's account does not
    mention. They match the working tree (the fresh scan finds no mismatch)
    and predate the Owner pass, since the Owner's starting copy is not `HEAD`.
- **Public-literal pruning.**
  - `ac1e2952`, `a4aae65e`, `bd7d5f53` and `f35615af` are gone from
    `test_character_origins_feats_acceptance.py`.
  - `a4aae65e` and `f35615af` are still listed under
    `test_character_origins_feats_proposal.py`; see stale entries below.
- **Hook over a temporary copy.**
  - Command: `python -m detect_secrets.pre_commit_hook --baseline <tmp copy>`
    over all 59 listed files plus the 7 files this pass edited or added.
  - It exited 0 twice. The copy's `results` stayed identical to the staged
    baseline, and the real baseline hash was unchanged.
  - This report was checked the same way on its own, after its only full
    64-hex value was truncated. That run also exited 0 with no change.
- **Fresh scan with the baseline's own settings.**
  - Every file this pass edited matches its entries exactly. The
    origins-acceptance literal is still at 199 and `test_equipment_proposal`
    at 136. The new test and the docs have no findings.
  - No unlisted finding in any of the 59 files.

**No new-hash finding came from these dependency updates, so no Owner-terminal
delta is required.**

**Optional removals-only cleanup for the Owner.** The entries below are listed
but no longer found; the hook does not fail on them. Earlier restart test
edits (working-tree ` M`) removed these literals; they are outside the eight
§6a files the Owner pass reconciled. If the Owner wants them pruned, the exact
removals (type Hex High Entropy String, hash prefix @ listed line) are:

- `test_movement_closure_proposal.py`: `340697ce`@83
- `test_reference_closure_proposal.py`: `d4505931`@85
- `test_actions_pilot_proposal.py`: `9909cac7`@78
- `test_combat_damage_breaking_proposal.py`: `30ad6523`@77
- `test_checks_actions_rests_proposal.py`: `20678442`@112
- `test_core_play_completion_proposal.py`: `4c4fe9a8`@105, `89fa8d0b`@106
- `test_core_play_completion_acceptance.py`: `4c4fe9a8`@144, `e4f41293`@173, `89fa8d0b`@177
- `test_core_play_dependencies_proposal.py`: `9951e00e`@101, `f64d7560`@102
- `test_core_play_dependencies_acceptance.py`: `9951e00e`@157, `f8a23d4a`@188, `f64d7560`@192
- `test_character_creation_foundations_proposal.py`: `2b92ca0b`@112, `c831fe09`@113
- `test_character_creation_foundations_acceptance.py`: `2b92ca0b`@171, `81a4a5d1`@205, `c831fe09`@209
- `test_character_origins_feats_proposal.py`: `a4aae65e`@161, `f35615af`@162

That is 22 entries in 12 files, all under `tests\ingestion\mechanical\`.
Removing them would change the baseline hash.

## Remaining / boundaries

- **Follow-up (2026-09-25): `REPLACEMENT-ACCEPT.py --verify` retargeted.**
  `verify()` now rebuilds `recorded()` and holds it to the Equipment helper's
  `PRIOR_SHA256` pin (the recorded twelve-batch bytes), then points at
  `issue-5d-equipment-ACCEPT.py --verify` for the current artifact.
  - `recorded()` and the imports are unchanged. Edits are below line 171,
    except for one line-neutral docstring line (19), so no baseline line moves.
  - Evidence: exit 0, `verified twelve-batch prefix 7b1d6f43…abdd8`.
  - The README and clean-restart doc wording was updated to match.
- **`docs/decisions/ADR-005d…:1624` is not edited.** It is a dated Owner
  Decision statement of the twelve-batch state.
- **Owner pass delta.** The counts reconcile. Only the 19/385 split and the
  129 oracle moves cannot be attributed from git, as noted above.
- **Not done:**
  - full suite, coverage floor, and a green pip-audit (31 findings / 11
    packages, deferred);
  - no commit, because the gates are not all resolved;
  - no broader audit of errors in accepted material (after 5d).
- **Scratch.** Scratch files are under `.claude/_eqdep_*` and
  `.claude/_eqdep_bl/`. They are never committed and can be deleted after
  Codex review.
