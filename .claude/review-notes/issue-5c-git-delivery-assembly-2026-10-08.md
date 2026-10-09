# CRD Issue 5c Restart — isolated Git delivery assembly (2026-10-08)

Status: **assembled as an uncommitted staged index for Codex exact-tree review.**
Nothing is committed, pushed or published. This note is itself staged, as the
authorized assembly-report addition. The approved packet exports under
`.claude/review-notes/issue-5c-git-delivery/` are byte-exact and unchanged.

## Owner authorization

The Owner authorized two stages on 2026-10-08:

1. Bounded isolated assembly of the Git delivery packet in the linked worktree
   `D:\AI\Claude\5c-restart-delivery\afterworlds`. The branch is
   `codex/5c-restart-delivery` and the base is
   `f5a78aa638243297ca2a280b8548f6f542c231dd`.
2. Two bounded packaging corrections from Codex's review of the first staged
   tree, followed by the applicable assembly proof.

These are packaging corrections. They are not semantic acceptance and not
supplement integration.

Still unauthorized: commit, push, PR, merge, external comments, runtime
publication or activation, shared-database writes, dependency repair, and any
restart-completion declaration.

The first staged tree, `b11bf825af81cd5a93f49639a6245371d4f612ad` (tree A), is
**not approved**. Its receipts are preserved, and later checks use new names.

## Correction 1 — raw evidence bytes

**Defect.** `* text=auto eol=lf` normalized 255 receipt blobs under
`.claude/review-notes/`. This broke 188 hash pins in clean-checkout bytes,
including the Owner receipt cited by the accepted oracle.

**Change.** A single rule was appended at the end of `.gitattributes`, so it
wins as the last match:

    .claude/review-notes/** -text

`git check-attr` reports `text: unset` for the `.json`, `.md` and `.log`
samples.

**Restaging.** All 763 delivered paths in the namespace were recopied from their
pinned originals and force-staged, which keeps raw `.log` files. The results:

- 0 copy mismatches;
- 0 index-blob mismatches against the manifest and export hashes.

No pins, expected digests, receipts or accepted oracles were edited.

**Proof.** Checked in a `git archive` checkout outside any repository:

| Check | Result |
|---|---|
| Namespace | 763/763 byte-match the manifest |
| Packet exports | 17/17 byte-exact |
| `issue-5c-release-order-recording/owner-acceptance.json` | sha256 `efe48d9b3f5c7f33591763ed823a2938519d276c2e5d6e3776ac22be6d4cd5e3` |
| Accepted oracle | `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c` |

## Correction 2 — Awakened Plant test independence

**Superseded claim.** This note previously said "no fixture missing". Codex
showed that was wrong: `test_the_awakened_plant_house_rule_appends_in_isolation`
read `docs/house-rules/awakened-plant.md` at test time (`HOUSE_RULE`,
`read_text`, test line 395), and that document is excluded from delivery.

**Change.** `HOUSE_RULE` now points at the checked-in, test-only fixture
`tests/ingestion/mechanical/data/awakened-plant-house-rule.md`. Everything else
is unchanged:

- the consumption expression, `read_text(encoding="utf-8").rstrip()`;
- every assertion;
- the line count.

The fixture is the consumed text plus one trailing LF.

| Item | sha256 |
|---|---|
| Source document | `72096d8e…dcdc89` |
| Consumed text (1679 characters), before and after | `7212304c2c45bb389582a5c5690e3f1519e8cbb1f8c0c0faacf7240095dccd6e` |

The document is not packaged. No production supplement was added, installed or
activated, and the test was neither skipped nor weakened.

**Sibling audit.** Defect family: test-time reads of a path that exists in the
source checkout but is absent from the delivery.

*Literal check.* Every non-comment string literal naming a file under `tests/`
and `src/` was resolved against the clean tree. Literals not found there were
resolved again against the source checkout, using the same rules: the repository
root, the referencing file's ancestor directories, and a basename/suffix match.

| Literals | Disposition and admission mechanism |
|---|---|
| The fixture (`__file__`-relative) | Already safe: present in the clean tree |
| 213 unresolved sites | Already safe: they resolve in neither tree, so no delivery exclusion can affect them (`tmp_path` names and metadata strings) |
| `afterworlds.db`, `release.db`, `chroma.sqlite3` | Resolve only in the source tree, by basename. Already safe: every site builds the path under `tmp_path`/`tmp_path_factory.mktemp(...)` and creates the file there |
| `frontend/dist` | Exists only in the source tree, as a build output. Already safe: `tests/api` builds it under `tmp_path` and monkeypatches `_DEFAULT_FRONTEND_DIST` |
| `data/srd/srd_5_2_1_structured.json` | Expected-absent: the test asserts it does not exist |
| `~/.cache/chroma` tokenizer | Already safe: skipped when absent |

*Directory check.* 497 non-private source files are absent from the delivery,
across 10 directories. Every non-comment mention of those directories in
`tests/` or `src/` refers to `.claude/review-notes` paths that are delivered.

All 52 directory-iteration sites (`glob`, `rglob`, `iterdir`) target one of:
- delivered oracle or pin directories;
- source or route modules;
- `tmp_path`.

The only excluded-filename matches are substrings of the delivered
`srd_table_inventory.json` and `regen_table_inventory.py`. The excluded house-rule
document is named only in comments.

No other excluded-path dependency was found (`path-audit-T1-1` to `-3`).

## Final-tree deviations from the manifest

| Path | Deviation |
|---|---|
| `.gitattributes` | Correction 1 rule |
| `tests/ingestion/mechanical/test_final_ten_references_candidate.py` | Correction 2 |
| `tests/ingestion/mechanical/data/awakened-plant-house-rule.md` | New fixture |
| `.secrets.baseline` | Reviewed rows, below |
| `docs/architecture/issue-5c-5d-clean-restart.md` | Status-only edit inside the existing "Immediate next step" bullet. No lines added; the historical body is unchanged. The index blob is LF; the source had one stray CR at line 15, outside the `-text` namespace. |
| This note | Authorized report addition |

All other paths are the manifest entries and packet exports. There are no
deletions.

## Secrets baseline

The real hook over tree A's paths (`secrets-hook-treeA-2`) reported 2097 Hex High
Entropy records in 29 delivered review-note files. Codex reviewed every record
and dispositioned it as reviewed-not-secret:

| Kind | Records |
|---|---|
| Content-derived fact keys | 1110 |
| Git object IDs | 18 |
| Integrity, proposal, schema or replay digests | 969 |

Only those exact rows were added, with `is_secret: false`. The semantic row
difference is exactly:

- 2097 additions over 29 new file keys;
- 0 removals;
- 0 changes to the 10459 existing rows;
- 0 changes to `generated_at`, `version`, the 25 plugins, the 10 filters or the
  settings.

`git diff --numstat` shows large deletions only because of misalignment on
repetitive JSON. All 77252 original lines appear, in order.

**Native-pruning attempt (reported, not accepted).** Re-serializing through
detect-secrets' native load would have:

- dropped 17 empty-list file keys;
- reordered the rows of 5 files.

`baseline-add-1` caught this and stopped before writing. `baseline-add-2` used an
additive merge that preserves existing bytes.

No detector was weakened. No `pragma: allowlist secret` or other exception was
added. The per-record evidence stays private.

## Tree identity

- **Payload tree before this note** (`git write-tree`):
  `a9178634fbce569aafb8ba791ced4d3e23256d20` (tree T1).
- **Final tree including this note:** recorded only in a private receipt, so this
  note does not have to embed its own hash.

## Native results on T1 (clean checkout, rtk disabled)

| Run | Exit | Result |
|---|---|---|
| `restore-namespace-1` | 0 | Correction 1 restaging |
| `make-fixture-1` | 0 | Fixture generated from the original document |
| `byte-proof-T1-1` | 0 | Byte proof above; the house-rule document is absent |
| `consumed-text-T1-1` | 0 | Consumed-text hash matches |
| `diag-focused-awakened-T1-1` | 0 | Focused Awakened Plant test: 1 passed. FOCUSED DIAGNOSTICS ONLY, coverage off. Not acceptance evidence. |
| `typing-changed-test-T1-1` | 0 | Strict mypy (`pyproject.toml`) on the changed test |
| `black-changed-test-T1-1` | 0 | |
| `ruff-changed-test-T1-1` | 0 | |
| `diag-packaging-pins-T1-1` | 0 | Bounded packaging proof: 151 passed, including the wheel and sdist build test. Diagnostic. |
| `diag-collect-T1-1` | 0 | 7538 tests collected; isolated imports from the clean tree |
| `path-audit-T1-1`, `path-audit-T1-2` | 0 | Sibling audit above |
| `baseline-add-2` | 0 | Additive baseline rows |

The final staged-relative hook result is recorded in the private final-tree
receipt.

## Failed or invalid attempts (preserved)

| Run | Exit | What happened |
|---|---|---|
| `secrets-hook-treeA-1` | 2 | Usage error: wrong relative script path; it never scanned |
| `secrets-hook-treeA-2` | 1 | The real finding, resolved above |
| `secrets-hook-treeA-3` | 1 | Invalid: run inside the original checkout, so Git resolved to that repository and stopped on an unstaged baseline. Read-only; the original was verified intact afterwards. |
| `verify-sources-2` | 1 | Usage error: the interpreter was passed twice; reran clean |
| `baseline-add-1` | 1 | Refused native re-serialization, as described above |

Tree A is not approved.

## Evidence reuse

**Whole-delivery scan.** `secrets-hook-treeA-2` scanned the raw worktree bytes of
all 947 paths. Those bytes equal the restored index blobs, so the CRLF restore
changes nothing the scan saw, and the roughly 16-minute full scan was not
repeated.

The final hook reruns on the changed inputs only:

- the 29 dispositioned files;
- `.gitattributes`;
- the changed test and its fixture;
- the restart document;
- this note.

**Full gate and typing.** The full gate (7397 passed, 141 skipped, 92.48%
coverage) and main-config typing (235 production modules, 42 tests) are reused
for unchanged inputs. Neither was rerun, and no broad suite ran.

**Historical limitation.** `RECORD.py` replay needs private database, leaf and
pickle inputs that are not delivered. No production code or test invokes it.
Private stores are not shipped, and no replay was attempted.

**Correction (8 October, PR #178 CI).** The claim that no test invokes private
inputs was wrong. Pinned replay scripts loaded by tests read the superseded
release `5.2.1-corpus.3fe24ff6-4e3` from the private
`.claude/_rc/msc/rel/afterworlds.db` (their `SCRATCH_DB`). That file existed in
the source checkout, so the reused Windows full gate passed. It is absent from a
clean checkout, so 11 *Animals* tests failed on CI. The path audit above
resolved string literals only and missed this computed path. The test-side
correction rebuilds that release from delivered inputs and refuses any other
identity (`tests/ingestion/superseded_release.py`, rebound in
`tests/ingestion/conftest.py`, which also fails any test-time open of a private
`.claude/_*` path). The *Equipment/spell references* tests load scripts with
the same `SCRATCH_DB`, so they depended on the store as well. The historical
text above is kept unchanged.

The same CI run also showed that the backend suite exceeds one hosted job's
six-hour limit. The prepared correction therefore runs it as 8 shards of the
files pytest collects, requires the shards' tests to equal a full collection
exactly once, and enforces the unchanged 80% threshold on combined coverage.
Local Linux results are diagnostic only. The complete aggregate gate has not
passed.

## Remaining boundaries

- Exact committed-head CI, including frontend and E2E.
- Full-PR Codex review.
- Audit.
- Owner publication decisions.
- Deferred dependency-vulnerability findings, which remain deferred until the
  restart is complete.

## Evidence location

Private receipts (raw output, native exit codes, input pins, the disposition and
the final-tree receipt) are under `.claude/_sp/git-delivery-assembly-20261008/`
in the original checkout. They are never staged.
