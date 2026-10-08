# Gate results — CRD Issue 5c/5d clean restart, increment 1

Run on the branch head of `codex/5c-5d-clean-restart` before the increment commit.
Every figure below is copied from a completed attached run; nothing here was
backgrounded, and nothing was re-stated from an earlier branch.

## Formatting, lint, types

| Gate | Command | Result |
| --- | --- | --- |
| Black | `black src/ tests/` | 493 files unchanged |
| Ruff | `ruff check src/ tests/` | passed, no findings |
| mypy strict | `mypy src/` | success, 229 source files |

## Tests

Split into two attached halves, run sequentially — not in parallel, and not
backgrounded. `pytest-xdist` and `pytest-timeout` are not installed in this
environment, so there is no parallel or per-test-timeout mode available.

| Command | Result |
| --- | --- |
| `pytest tests/ingestion` | 3,421 passed, 109 skipped, 381.95s |
| `pytest tests --ignore=tests/ingestion --cov-append` | 2,843 passed, 10 skipped, 341.64s |

Totals: **6,264 passed, 119 skipped, 0 failed.**

Coverage, from the second half's `--cov-append` report:
`Required test coverage of 80% reached. Total coverage: 92.45%`.

New-code coverage, which is the figure the increment is measured against:

| New module | Statements | Covered |
| --- | --- | --- |
| `src/afterworlds/ingestion/source/community_compare.py` | 118 | 118 (100%) |
| `src/afterworlds/quarantine.py` | 34 | 34 (100%) |

The three new test files were also re-run alone after the commit, against the
committed tree: 92 passed in 64.26s (`tests/test_pinned_community_source.py`,
`tests/test_quarantine_5c_5d.py`, `tests/ingestion/source`).

The `named_evidence` fixture in `tests/ingestion/source/test_community_compare.py`
is module-scoped and calls `extract_pages` across all 364 PDF pages to compare the
13 named-check pages, which is most of that 64 seconds. Accepted as-is for this
increment: correctness is unaffected and the alternative is a page-filtered
extraction path that exists only to make a test faster.

## detect-secrets

Invoked exactly as `.pre-commit-config.yaml` configures the hook — the files were
`git add`ed first, and `.secrets.baseline` was never passed as a scanned file:

```
python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <files>
```

First run: **30 hits across 5 files.** Every hit is a SHA-256 digest of public
content — upstream Git blob digests of the pinned community snapshot, the official
PDF's digest, the quarantined artifact's content digests, and the pinned upstream
commit. None is a credential, and none can be removed from the source, because a
recorded digest exists in order to be read and checked.

Registered with the additive splice (`.claude/review-notes/_clean_restart_baseline_splice.py`):
the real baseline is never handed to `detect_secrets scan`, which rewrites what it
is given and drops every entry whose file it was not asked to scan. Only the five
new files were scanned, into a throwaway probe baseline, and only their blocks
were inserted before re-sorting.

| Check | Result |
| --- | --- |
| `git diff --numstat .secrets.baseline` | 220 insertions, **0 deletions** |
| `version`, `plugins_used`, `filters_used`, `generated_at` | unchanged |
| Pre-existing entries | all preserved |
| Re-run of the hook | **exit 0** |
| Baseline md5 | `3f12148f…` → `aecdce96b3cdde4e368b5ff87d1be40d` |

No detector setting was relaxed and no hit was silenced by growing the baseline
around it. CI does not run detect-secrets; this is a local gate only.

## pip-audit

`pip-audit` exits 1 with **24 vulnerabilities across 10 packages**: chromadb (5),
urllib3 (4), pytest (2), pip (2), msgpack (2), mako (2), idna (2), cryptography (2),
anyio (2), pydantic-settings (1).

All 24 are pre-existing on the branch base `cf26e25`. This increment adds no
dependency and changes no pin, so it introduces none of them. They are not
suppressed, not silenced, and not remediated here: dependency remediation is
unrelated work and outside this increment's scope.

## Not run

* No PR, CI, push or remote gate — the operating boundary forbids all four.
* No shared database or Chroma operation of any kind. The quarantine tests use
  isolated per-test stores; no shared state was read, reset or mutated.

# Gate results — increment 1 remediation (Codex review round 1)

Run on the settled tree before the remediation commit. Same rules: every figure is
copied from a completed attached run; nothing backgrounded, nothing restated.

## Formatting, lint, types

| Gate | Command | Result |
| --- | --- | --- |
| Black | `black src/ tests/ scripts/` | 2 files reformatted, 497 unchanged |
| Ruff | `ruff check src/ tests/ scripts/` | all checks passed |
| mypy strict | `mypy src/` | success, 229 source files |

## Tests

Two attached halves, run sequentially.

| Command | Result |
| --- | --- |
| `pytest tests --ignore=tests/ingestion -rs` | 2,856 passed, 10 skipped, 270.97s |
| `pytest tests/ingestion -rs` | 3,423 passed, 109 skipped, 214.00s |

Totals: **6,279 passed, 119 skipped, 0 failed** (+15 passing tests, same skip
count — no skip was converted back by weakening a guard).

Focused suites, attached:
`pytest tests/test_quarantine_5c_5d.py tests/ingestion/source/test_community_compare.py tests/ingestion/corpus/test_persistence_quarantine.py -rs`
→ **81 passed, 45 skipped, 69.59s**.

Skip accounting from `-rs`: **109** skips carry `QUARANTINED_RECONSTRUCTION` —
every skip in `tests/ingestion`. The remaining 10 skips in the other half are
pre-existing and unrelated.

## Coverage of the changed modules

Measured over `tests/test_quarantine_5c_5d.py`,
`tests/ingestion/source/test_community_compare.py`,
`tests/ingestion/test_ingestion.py`, `tests/services/test_rules_package.py` and
`tests/ingestion/corpus` (293 passed, 95 skipped):

| Module | Stmts | Miss | Cover |
| --- | --- | --- | --- |
| `src/afterworlds/quarantine.py` | 35 | 0 | 100% |
| `src/afterworlds/ingestion/source/community_compare.py` | 119 | 0 | 100% |
| `src/afterworlds/ingestion/ingestion_service.py` | 175 | 2 | 99% |
| `src/afterworlds/services/rules_package.py` | 149 | 12 | 92% |
| `src/afterworlds/ingestion/corpus/persistence.py` | 317 | 256 | 19% |

The `persistence.py` figure is the retired finalization suite being skipped; the
changed lines (the step-0 refusal, 1123–1136) are covered. `rules_package.py`
487–501 is the slug branch of `resolve_slice_package`, defence in depth behind
`resolve_package_reference`, whose own refusal is covered. `ingestion_service.py`
misses two pre-existing lines (package-not-found raise, empty-rows return).

## detect-secrets

Invoked exactly as the hook is configured, on the `git add`ed files, with
`.secrets.baseline` never passed as a scanned file:

```
python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <files>
```

One new hit: `Hex High Entropy String` at `src/afterworlds/quarantine.py:79` —
the retired transform recipe's source-manifest SHA-256. It is public content
recorded in order to be compared against, not a credential, and it cannot be
removed from the source.

Registered with the additive splice again
(`.claude/review-notes/_clean_restart_baseline_splice_r2.py`, untracked): only
`src\afterworlds\quarantine.py` was rescanned, into a throwaway probe baseline,
and its block merged with the recorded one so no previously registered
`hashed_secret` could be dropped.

| Check | Result |
| --- | --- |
| `git diff --numstat .secrets.baseline` | 12 insertions, 5 deletions |
| What the 5 deletions are | line-number moves only — the three pre-existing `quarantine.py` entries shifted 70/72/74 → 92/94/96, and `test_community_compare.py` 247 → 283 |
| Net new entries | 1 (the recipe checksum at line 79) |
| Pre-existing `hashed_secret` values | all preserved; no block other than those two files changed |
| `version`, `plugins_used`, `filters_used` | unchanged |
| `generated_at` | `2026-09-18T04:19:09Z` → `2026-09-21T09:24:03Z` — rewritten by the **hook itself** when it re-synced line numbers. The splice preserved it; the hook does not. Recorded rather than reverted. |
| Re-run of the hook after `git add` | **exit 0** |
| Baseline blob md5 | `aecdce96…` → `b8f9b1f6…` |

No detector setting was relaxed, and no hit was silenced by growing the baseline
around it. CI does not run detect-secrets; this is a local gate only.

## Not run again

* Total-suite coverage was **not** re-measured *by me* in this remediation.
  Neither half emitted a coverage summary, so the `addopts` `--cov-fail-under=80`
  gate was not exercised here — the halves were run for pass/fail and skip
  accounting, and a split run reports two partial totals rather than one true
  one. The changed modules were measured separately in the table above, from a
  single targeted run, and their changed lines are covered.
* **The missing coverage gate was afterwards run by Codex on this same head,
  `d817dd4`, and passed.** Recorded here as Codex's evidence, not as a fresh
  measurement of mine:

  | | |
  | --- | --- |
  | Command | `venv/Scripts/python.exe -m pytest tests --cov=src/afterworlds --cov-report=term --cov-fail-under=80` |
  | Head | `d817dd4` |
  | Exit | 0 |
  | Result | 6279 passed, 119 skipped, 248 warnings in 706.40s |
  | Total coverage | **92.46%** |
  | Evidence | `remediation1-final-coverage.log`, held by the reviewer |

  92.46% is Codex's figure on `d817dd4`. Increment 1's 92.45% is a different,
  earlier measurement; the two are not the same run and neither is restated as
  the other.
* pip-audit — no dependency, pin or environment change in this remediation, so the
  increment-1 finding (24 pre-existing vulnerabilities in 10 packages) stands
  unchanged. Not re-run for ceremony.
* The 364-page comparison regeneration — re-run earlier in this increment when the
  verdict rename and sub-floor fields changed the record; coverage identical.
* No PR, CI, push or remote gate. No shared database or Chroma operation.

# Gate results — increment 2, source qualification

Run on the working tree of `codex/5c-5d-clean-restart` immediately before the
qualification commit, with every change of this increment present. Every figure
is copied from a completed run. The suite was started detached because it runs
longer than the foreground cap, and was then waited on to completion in the
same turn — the exit code and totals below are the run's own, not a partial
read.

## Formatting, lint, types

| Gate | Command | Result |
| --- | --- | --- |
| Black | `venv/Scripts/python.exe -m black --check src/ tests/ scripts/` | 503 files would be left unchanged |
| Ruff | `venv/Scripts/python.exe -m ruff check src/ tests/ scripts/` | All checks passed |
| mypy strict | `venv/Scripts/python.exe -m mypy src/` | Success, 230 source files |

`scripts/` is outside the repository's documented gate command (`black src/
tests/`) and outside mypy's `files = ["src"]`. It is included in black and ruff
here because this increment adds a script to it; mypy's configured scope was
not changed.

Two findings were fixed rather than ignored: ruff `F821`/`F841` on a loop
variable read before its first assignment in `community_tokens._sequence`, and
three mypy `assignment` errors from reusing an `int` loop variable as
`int | None` and from an `object` sentinel. The sentinel was removed rather
than typed around.

## Tests

| | |
| --- | --- |
| Command | `venv/Scripts/python.exe -m pytest tests --cov=src/afterworlds --cov-report=term --cov-fail-under=80 -q` |
| Exit | 0 |
| Result | **6312 passed, 119 skipped**, 248 warnings in 708.89s (11:48) |
| Total coverage | **92.50%** |

This is a fresh whole-suite measurement of the working tree, distinct from
Codex's 92.46% on `d817dd4` and from increment 1's 92.45%. The three are
different runs on different trees and none is restated as another.

33 tests are new since `d817dd4`: 6279 -> 6312, and they account for the
whole difference. Collected counts for the three touched files, old versions
against new: `tests/ingestion/source/test_community_source_structure.py`
0 -> 14, `tests/ingestion/source/test_community_compare.py` 27 -> 28 (the
live-versus-committed check that fails if the source is edited without
regenerating the coverage record), `tests/test_pinned_community_source.py`
37 -> 55 (one new per-file test that a vendored file differs from upstream
only where a correction says so, 16 cases; one that every correction is
counted where a reader looks first; one that the controlled addition is the
bytes its entry claims). 64 -> 97 over the three files. The package
`conftest.py` added by this increment holds the shared extraction fixture and
contributes no test of its own.

## pip-audit

| | |
| --- | --- |
| Command | `venv/Scripts/python.exe -m pip_audit` |
| Result | 31 known vulnerabilities in 11 packages; `afterworlds` itself skipped (not on PyPI) |

**This gate is not green and is not claimed as green.**

No dependency, pin, `pyproject.toml` or environment change was made in this
increment — nothing was installed, upgraded or removed, and
`git diff d817dd4 HEAD -- pyproject.toml` is empty. The count differs from
increment 1's 24-in-10, and what caused the difference was not established:
a changed advisory count is consistent with new advisories, with a changed
advisory database, and with other causes, and none of those was checked. The
count is reported as the count. No suppression, no `--fix`, no unrelated
environment maintenance.

## detect-secrets

Invoked exactly as `.pre-commit-config.yaml` configures it, on the staged set,
never passing `.secrets.baseline` as a scanned file:

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>
```

First run: **exit 1**, five new hits, all in
`docs/sources/community/dnd-5e-srd-markdown/source_pin.json` — the four
corrected files' new `sha256` values and the controlled addition's. All five
are SHA-256 digests of public SRD Markdown, which is what that manifest exists
to record.

Re-registered with the additive splice,
`.claude/review-notes/_clean_restart_baseline_splice_r3.py` (untracked), which
rescans that one file alone into a throwaway probe baseline and merges the
result with the block already recorded:

| | |
| --- | --- |
| `source_pin.json` entries | 23 → 28 |
| Previously registered hits dropped | **0** |
| Other files' blocks | unchanged except two `line_number` re-syncs the hook itself wrote for the two edited test files, same `hashed_secret`, no additions |
| `version`, `plugins_used`, `filters_used` | unchanged |
| `generated_at` | `2026-09-21T09:24:03Z` → `2026-09-21T12:24:42Z` — rewritten by the **hook**, as in increment 1. Recorded rather than reverted. |
| Baseline line endings | the hook wrote CRLF; normalised back to LF before staging |
| Re-run after `git add` | **exit 0** |

No detector setting was relaxed and no hit was silenced by growing the baseline
around it. CI does not run detect-secrets; this is a local gate only.

## Not run

* No push, PR, CI, remote gate, shared database or Chroma operation.
* The quarantine increment was not re-run: it is unchanged at `d817dd4` and
  Codex's coverage gate on that head is recorded above.


# Gate results — increment 3, record-ownership remediation

Run on the working tree of `codex/5c-5d-clean-restart` immediately before the
remediation commit, with every change of this increment present. Every figure
is copied from a completed run. The suite was started detached because it runs
longer than the foreground cap and then waited on to completion in the same
turn — the exit code and totals below are that run's own, not a partial read.

## Formatting, lint, types

| Gate | Command | Result |
| --- | --- | --- |
| Black | `venv/Scripts/python.exe -m black src/ tests/ scripts/regen_community_source_coverage.py` | 497 files left unchanged |
| Ruff | `venv/Scripts/python.exe -m ruff check src/ tests/ scripts/` | All checks passed |
| mypy strict | `venv/Scripts/python.exe -m mypy src/` | Success, 230 source files |

Black was run over `src/`, `tests/` and the one script this increment edits,
which is why its file count is 497 rather than increment 2's 503 over all of
`scripts/`. That is the command that ran; it is not a restatement of the
earlier figure. mypy's configured scope (`files = ["src"]`) was not changed,
so the edited script is outside it, as before.

## Tests

| | |
| --- | --- |
| Command | `venv/Scripts/python.exe -m pytest tests --cov=src/afterworlds --cov-report=term --cov-fail-under=80 -q` |
| Exit | 0 |
| Result | **6343 passed, 119 skipped**, 248 warnings in 725.74s (12:05) |
| Total coverage | **92.50%** |

31 tests are new since `a4531a2`: 6312 → 6343, and they account for the whole
difference. All 31 are in
`tests/ingestion/source/test_community_source_structure.py`, 14 → 45, in a new
"Record ownership" section: which stat blocks the source embeds and where,
which entry owns each embedded block, that a creature-file block is the record
itself rather than an embedded one, that the entry printed after a block still
belongs to its own section, that each figurine variant belongs to the figurine,
and that a block's Traits/Actions labels stay inside the block.

A targeted run of the source tests alone was also completed after the coverage
record was regenerated: `pytest tests/ingestion/source
tests/test_pinned_community_source.py -q --no-cov` → **128 passed in 34.70s**.
That includes the live-versus-committed token check, which fails if the source
is edited without regenerating the record.

## pip-audit

**Not re-run in this increment, and not claimed as green.**

Nothing in this increment touches a dependency, a pin, `pyproject.toml` or the
environment: the change is Markdown headings, one script, two test modules and
documentation. The increment-2 result stands as the last measured one — 31
known vulnerabilities in 11 packages, `afterworlds` itself skipped as not on
PyPI — and it was not green then either. What caused its difference from
increment 1's 24-in-10 was not established and is not asserted here. No
suppression, no `--fix`, no unrelated environment maintenance.

## detect-secrets

Invoked exactly as `.pre-commit-config.yaml` configures it, on the staged set,
never passing `.secrets.baseline` as a scanned file:

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>
```

First run: **exit 1**, two new hits, both in
`docs/sources/community/dnd-5e-srd-markdown/source_pin.json` (lines 197 and
322) — the new corrected `sha256` values for `spells.md` and `magic-items.md`,
which this increment's edits changed. Both are SHA-256 digests of public SRD
Markdown, which is what that manifest exists to record.

Re-registered with the additive splice,
`.claude/review-notes/_clean_restart_baseline_splice_r4.py` (untracked, copied
from `_r3` with only the target's description changed), which rescans that one
file alone into a throwaway probe baseline and merges the result with the block
already recorded:

| | |
| --- | --- |
| `source_pin.json` entries | 28 → 30 after the splice |
| Previously registered hits dropped by the splice | **0** |
| Other files' blocks | untouched |
| `version`, `plugins_used`, `filters_used` | unchanged |

The hook then rewrote the baseline itself on the next run, as it did in the two
earlier increments, and its rewrite did drop two entries: 30 → 28. Those two
are exactly the `sha256` values that `source_pin.json` carried at `a4531a2` and
no longer carries, because this increment replaced them. That was checked
rather than assumed — their SHA-1s equal the two dropped `hashed_secret`s, and
no dropped hash matches any digest still in the file. Nothing live was dropped
and no detector setting was relaxed.

| | |
| --- | --- |
| `generated_at` | `2026-09-21T12:24:42Z` → `2026-09-21T13:38:19Z` — rewritten by the **hook**. Recorded rather than reverted, as in both earlier increments |
| Baseline line endings | the hook wrote CRLF; normalised back to LF before staging |
| Re-run after `git add` | **exit 0** |

CI does not run detect-secrets; this is a local gate only.

## Not run

* No push, PR, CI, remote gate, shared database or Chroma operation.
* pip-audit, for the reason above.
* The quarantine and comparison increments were not re-run: they are unchanged
  and their gates are recorded in the sections above.

# Increment 4 — replacement 5c construction (commits `05e8492`…`1c311e9`, docs `1cb51f3`, follow-up this commit)

Numbered 4: the record-ownership remediation above already took 3.

All run locally on the branch head, attached, after the final code commit.

| Gate | Result |
| --- | --- |
| `black --check src/ tests/` | **clean** — 502 files unchanged (2 files reformatted mid-work and committed) |
| `ruff check src/ tests/` | **All checks passed** |
| `mypy src/` (strict) | **Success**, 233 source files |
| `pytest tests/ -q --no-cov` | **6,370 passed, 141 skipped**, exit 0, 662.90s |
| `pytest tests/ingestion -q --no-cov` | **3,496 passed, 131 skipped**, 386.50s |
| `detect-secrets` pre-commit hook | **exit 0**, baseline unchanged, nothing added |
| `pip-audit` | **not green**, unchanged: 24 findings in 10 packages (`anyio`, `chromadb`, `cryptography`, `idna`, `mako`, `msgpack`, `pip`, `pydantic-settings`, `pytest`, `urllib3`), all pre-existing and unrelated to this work |

## Coverage of the new modules

`--no-cov` was used on the gate runs above so single-module runs would not
trip the repo's global `--cov-fail-under=80`, so coverage was measured
separately: `pytest tests/ingestion/corpus --cov=afterworlds.ingestion.corpus
--cov-report=term-missing --cov-fail-under=0` → **111 passed, 117 skipped**,
exit 0, 495.47s, then `coverage report --include="*/ingestion/corpus/*"`.

| Module | Cover |
| --- | --- |
| `source_units.py` | **98%** |
| `source_citations.py` | **95%** |
| `source_ledger.py` | **94%** |
| `report.py` | **94%** |
| `pipeline.py` | **82%** |
| `persistence.py` | **81%** |

Every module this increment wrote or changed clears the 80% CLAUDE.md floor on
its own. The package total is 76%, dragged there by the retired machinery whose
suites are now skipped — `tables.py` 27%, `ledger.py` 26%, `table_inventory.py`
69%, `source_completeness.py` 62% (its PDF-extraction assertions stay live but
this narrow run does not reach its reporting helpers). That figure is reported
as found and is not a regression in new code; it is the arithmetic consequence
of retiring the product those lines belong to. The whole suite was **not**
re-measured for coverage here; the last whole-suite measurement is the 92.50%
recorded above for increments 2 and 3. An earlier draft of this paragraph said
92.45%, which is increment 1's figure, not the most recent one.

New code is exercised by `tests/ingestion/corpus/test_source_lifecycle.py`
(12 tests), the 20 in `test_source_release.py` and the 17 in
`test_source_units.py`, each asserting about the real build rather than a
fixture stand-in.

Skips: all 131 in `tests/ingestion` carry `QUARANTINED_RECONSTRUCTION`; the
remaining 10 predate this work. The per-file map and each disposition are in
`docs/architecture/issue-5c-5d-clean-restart.md` §8.6.

## Not run

* No push, PR, CI, remote gate, shared database or Chroma operation. Every
  publication in this increment is into a throwaway SQLite database and a
  private Chroma directory.
* No production publication or activation; the corpus is not selectable.
* No dependency maintenance — `pip-audit`'s non-green status is reported as
  found, not remediated.

## Follow-up commits

Corrections found in review of the increment, not new work. The first three
landed in `cf9b39c`; the fourth is the commit after it.

* §8.1 claimed the source is `docs/community/dnd-5e-srd-markdown/`, "all 24
  files". Both are wrong: the path is `docs/sources/community/dnd-5e-srd-markdown/`
  and `CORPUS_FILES` is **14** — 13 content files plus the controlled
  `legal-information.md`. The pin directory holds 19 entries; the other five are
  the manifest, licence, README and changelog, which carry no units.
* §8.6 blamed `test_persistence_quarantine.py`'s 45 → 52 on `a8de466`. That does
  not survive the commit order, and the real cause is this increment: moving the
  refusal out of `finalize_in_fresh_db` into the `full_candidate` fixture makes
  it fire for every test that builds the retired candidate, not only those that
  finalize it. 109 → 131 decomposes exactly: `test_tables.py` 0 → 9,
  `test_table_inventory.py` 0 → 6, `test_persistence_quarantine.py` 45 → 52.
* `test_the_evidence_report_names_the_verification_that_actually_ran` did not
  assert the `source_citation_mapping` field §8.2 is about, and the reuse test
  did not check it survives the round trip through the persisted row. Both now
  do.
* This increment's record then said the last whole-suite coverage figure
  "remains the earlier 92.45%", in §8.6 and in this log. That is increment 1's
  number. Increments 2 and 3 — source qualification and the record-ownership
  remediation — each recorded a fresh whole-suite **92.50%** (both tables
  above), so 92.50% is the last measurement. Corrected in both places.
  §5's 92.45% is *not* stale and was left alone: §5 records the quarantine
  remediation, whose previous increment really was increment 1.
* `f6aa5f0`, the commit that fixed the figure, got that chronology wrong — it
  rewrote §5's correct sentence and described the two 92.50% increments as
  "the two before the record-ownership remediation", when the record-ownership
  remediation is itself one of them. Reverted and reworded in the commit after
  it. Both `cf9b39c` and `f6aa5f0` carry wrong figures in their immutable
  commit messages; this log is the corrected record.

Gates re-run on `cf9b39c`: black, ruff, mypy strict clean;
`pytest tests/ingestion/corpus -q --no-cov` **111 passed, 117 skipped**;
detect-secrets exit 0, baseline unchanged. `pip-audit` unchanged and still
**not** green. The figure correction is Markdown only ? no source or test file
changes ? so the suite was not re-run for it; black, ruff, mypy and
detect-secrets were.


# Gate results — increment 5, retrieval reachability and the baseline reset

Run on the working tree of `codex/5c-5d-clean-restart` with all three of this
increment's code commits present (`d0c59dd`, `864d65d`, `6d76759`) and only the
documentation commit after them. Every figure is copied from a completed run
that was waited on to completion in the same turn; nothing here is a partial
read of a backgrounded job, and nothing is restated from an earlier increment.

## Formatting, lint, types

| Gate | Command | Result |
| --- | --- | --- |
| Black | `venv/Scripts/python.exe -m black src/ tests/` | 1 file reformatted (`tests/ingestion/corpus/test_source_lifecycle.py`), 504 unchanged; re-run clean. The increment-5 test module was reformatted the same way before its commit |
| Ruff | `venv/Scripts/python.exe -m ruff check src/ tests/ scripts/` | All checks passed |
| mypy strict | `venv/Scripts/python.exe -m mypy src/` | Success, 234 source files |

## Tests — the required aggregate gate

The previous full run used `--no-cov`. This one does not: the repository's
configured coverage flags and floor are in force.

| | |
| --- | --- |
| Command | `venv/Scripts/python.exe -m pytest -q` (config appends `--cov=src/afterworlds --cov-fail-under=80`) |
| Exit | 0 |
| Result | **6,395 passed, 141 skipped, 0 failed**, 248 warnings in 1290.72s (21:30) |
| Total coverage | **92.20%**, `Required test coverage of 80% reached` |

The suite was started detached because it runs past the foreground cap, then
waited on to completion in the same turn. The 21:30, the exit code and the
totals are that one run's own.

## Coverage of the changed modules

Measured on a second completed run over `tests/ingestion`,
`tests/pipeline/retrieval` and `tests/models/test_retrieval.py`:
**3,654 passed, 131 skipped** in 871.50s (14:31), exit 0.

| Module | Coverage |
| --- | --- |
| `pipeline/retrieval/corpus_windows.py` (new) | 90% |
| `models/retrieval.py` | 100% |
| `pipeline/retrieval/rules_corpus_service.py` | 96% |
| `ingestion/corpus/vector_publication.py` | 98% |
| `ingestion/corpus/source_units.py` | 98% |
| `ingestion/corpus/source_ledger.py` | 94% |
| `ingestion/corpus/persistence.py` | 82% |

Each clears the 80% new-code floor on its own. This is reported *in addition to*
the aggregate gate above, not in place of it.

`scripts/reset_corpus_baseline.py` is outside mypy's configured scope
(`files = ["src"]`) and outside the coverage source, as it has been all along;
it is covered behaviorally by `tests/ingestion/corpus/test_source_baseline_reset.py`,
which loads and runs the real `main()`.

## New and changed test modules

| Module | Result |
| --- | --- |
| `tests/pipeline/retrieval/test_corpus_windows.py` (new, 9) | passed, 5.8s — real cached ONNX MiniLM embedder |
| `tests/ingestion/corpus/test_retrieval_windows.py` (new, 6) | passed, 32.7s — whole corpus measured through the model's own tokenizer |
| `tests/ingestion/corpus/test_source_baseline_reset.py` (new, 8) | passed, 60.76s |
| `tests/ingestion/corpus/test_source_lifecycle.py` (12) | passed, 109.14s |
| `tests/ingestion/corpus/test_baseline_reset_script.py` (8) | **still 8 skipped**, 0.02s — the retired module was not un-skipped |

Both real-embedder modules skip rather than fail when the ONNX model is not
cached (`~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/`), which is how they run
offline here and how they will behave on a runner that has never embedded. That
is a real limitation of this evidence on CI and is named rather than hidden: the
guarantee they prove is measured here, on this machine, with the model present.

The page-coverage fix was verified by reverting it: with
`validate_corpus_payload` back to its pre-fix form, the positive control and the
canonical-proof test both fail with `persisted ledger omits authoritative
printed pages [2, 3, 4, 27]`. The fix was restored and the module re-run green
before the commit.

## pip-audit

**Re-run and still not green.**

```
venv/Scripts/python.exe -m pip_audit   —   exit 1
Found 31 known vulnerabilities in 11 packages
```

Environment: `D:\AI\Claude\afterworlds\venv\Scripts\python.exe`, pip-audit
2.10.0. Per package: `pip` 8, `chromadb` 5, `urllib3` 4, `setuptools` 2,
`msgpack` 2, `mako` 2, `idna` 2, `cryptography` 2, `anyio` 2,
`pydantic-settings` 1, `click` 1. `afterworlds` itself is skipped as not on
PyPI.

This reproduces the 31-in-11 that increment 2 recorded and that Codex's review
reported; increment 1's 24-in-10 was measured earlier, against whatever
advisories were published then. **The cause of the difference is still not
established** and is not asserted. Nothing in this increment touches a
dependency, a pin, `pyproject.toml` or the environment. No suppression, no
`--fix`, no unrelated dependency work.

## detect-secrets

Invoked exactly as `.pre-commit-config.yaml` configures it, on the staged set,
never passing `.secrets.baseline` as a scanned file:

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>
```

Exit 0 on each of the three code commits' staged sets. The baseline was not
modified and was not grown.

## Corrections this increment makes to the record

* §8.1's identity block was stale the moment `SOURCE_TRANSFORM_VERSION` went
  to 3. The replacement corpus is now package `4f1bf24f-b64e-5706-924d-b50c2753e67e`,
  release `5.2.1-corpus.6a11f2c0-393`, transform hash `041d839a…`, ledger hash
  `72ddaf29…`, bundle root `758b7b63…`, 10,465 units. No test pinned the old
  values; the only pins were in that document.
* §8.2's inherited-unit breakdown (314 short / 92 repeated / 23 neither) does
  not reproduce. Re-measured with the same probe on the current corpus:
  **344 / 72 / 13**, still summing to 429. The corrected figures are in the
  document; the earlier ones were measured against an earlier state of the
  snapshot and were not re-measured when it changed.
* §8.7 boundary 1 (oversized units versus the production embedder) is
  **resolved**, not merely restated: the suspicion was correct, the truncation
  was measured at 256 tokens over 494 units, and the fix is
  §8.8.2. Boundary 2 now names obligation (5) alone.


# Sibling audit — increment 5

Three defect families were fixed this increment. CLAUDE.md requires each to name
the family, the trigger, the sibling structures inspected, the regression
coverage and a disposition per sibling. This audit controls scope; it does not
expand it, and nothing classified below as `out of scope` or `Known Unknown` was
silently fixed.

## Family 1 — a logical table's note served as a separate unit

**Trigger.** Codex's consolidated review named Magic Item Rarities and Values
(magic-items.md, official p.206) and four more sites, and asked whether the
family was bounded.

**Structure at fault.** `_block_ranges` ends a table at `</table>`, and
`_merge_captions` bound only the block *above* a table. A block below it that
defines a marker used inside it became its own unit.

**Siblings inspected.** Every block that follows a `</table>` close in all
fourteen pinned files, classified by a closure probe: **footnote 5, other prose
374, heading 183, another table 15, end of file 2**. The five are
character-creation.md (languages, p.20), gameplay-toolbox.md (travel pace,
p.192) and magic-items.md three times (rarities p.206, crafting p.207, Deck of
Illusions p.218) — exactly the sites the review named, with no sixth.

| Sibling | Disposition |
| --- | --- |
| The five footnote blocks | `patched` — `_merge_captions` became `_merge_table_context` and binds both sides |
| 374 prose / 183 heading / 15 table / 2 EOF blocks after a `</table>` | `already safe` — admission mechanism: the probe reads each block's own text and classifies it, and the merge predicate the fix installs rejects all four classes; the unit count moved by exactly 5 (10,470 to 10,465), which is the count the probe predicted |
| Captions *above* tables | `already safe` — admission mechanism: they were already merged by the pre-existing caption rule, and `build_structure`'s tiling assertion (`"".join(pieces) == whole`) still passes, so no span was dropped or double-counted by the widened merge |

**Regression coverage.** The merge is span-contiguous, so the tiling assertion
covers completeness; the unit tests assert the p.206 note is inside the table's
unit and that the unit keeps the table's own citation rather than minting a new
one.

## Family 2 — whole `row.content` sent to a 256-token embedder

**Trigger.** Codex's offline cached-tokenizer probe measured 492 oversized
units; reproduced here at **494 of 10,465**. The two-unit difference is
accounted for, not unexplained: Codex measured the pre-R1 structure. Building
both structures from the same sources through the same tokenizer gives 492 of
10,470 before the family-1 merge and 494 of 10,465 after it, and the two units
that gained the label are named — magic-items.md "Magic Item Values by Rarity"
(269 tokens) and "Time and Cost" (283), each a table that sat just under 256
until its own footnote joined it. The merge did not make anything less
reachable; both are windowed by the family-2 fix.

**Structure at fault.** `chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py`
calls `enable_truncation(max_length=256)` on its own input. Any writer that hands
that embedding function a document longer than 256 tokens embeds only its
opening, and nothing downstream can see it: the stored document reads back
complete, so document hashes match, and the deterministic fake embedder used by
the lifecycle tests has no ceiling at all.

**Siblings inspected.** Every `collection.upsert(...)` call site in `src/`.

| Sibling | Disposition |
| --- | --- |
| `pipeline/retrieval/rules_corpus_service.py` (`reindex_from_sql`) | `patched` — routed through `derive_retrieval_documents` |
| `ingestion/corpus/vector_publication.py` (`expected_vector_state_from_sql`) | `patched` — same function, so published and expected state cannot drift into a tautology |
| `pipeline/retrieval/write_service.py:104` (story-memory turns) | `out of scope` — see below |
| `ingestion/vector_writer.py:137` (`write_chunks`) and `:175` (`write_chunks_raw`) | `Known Unknown` — admission mechanism: the module docstring (`vector_writer.py:16-22`) already designates **embedding model selection and chunking strategy** for CRD Issue 18 revision and forbids downstream dependence on this schema. It is the legacy 5b re-ingest path for the PDF-geometric packages the clean restart retires; it is not the 5c corpus path and no 5c release is written through it |

**The story-memory exposure, named rather than hidden.** `write_service` bounds a
turn by `chunk_turn_prose(text, config.chunk_char_ceiling)`, whose default is
**4,000 characters** (`pipeline/retrieval/config.py:23`, "Starting value per the
ADR"), and ADR-018 D3 deliberately keeps a single over-ceiling paragraph whole
rather than splitting mid-paragraph. It embeds through the same model: its
`embedding_function` argument defaults to `None`, and `get_story_memory_collection`
then calls `resolve_default_embedding_function()`, which is the real local ONNX
MiniLM of ADR-018 D4 — the same 256-token ceiling this family is about, not a
different embedder. What a 4,000-character chunk costs in tokens depends on how
much markup it carries: measured on this corpus, units containing a table run
2.24 characters per token (median of 579) and units without one run 3.87 (median
of 5,700), so 4,000 characters is roughly 1,000 tokens of plain narration —
about four times the ceiling — and up to about 1,800 if it were as dense as
table markup. **Both ends are arithmetic from ratios measured on rules text, not
a probe run against story-memory data** — the exposure is stated to be
checked, not asserted as a measured defect. It is left unfixed deliberately:
the Owner brief scopes this increment to the replacement corpus's production
retrieval path, the
story-memory chunk ceiling is an accepted ADR-018 decision, and retrieval
scoring/chunking for that surface is CRD Issue 18's own product. Surfaced here
for Issue 18 rather than decided in code.

**Regression coverage.** `tests/pipeline/retrieval/test_corpus_windows.py`
drives the real cached ONNX embedder end to end, including a negative control
that writes unwindowed documents to its own collection and fails to retrieve the
same late facts. `tests/ingestion/corpus/test_retrieval_windows.py` measures
every window of the real corpus through the model's own tokenizer: 11,077
windows, densest 189 tokens against the 256 ceiling. Both skip rather than fail
when the ONNX model is not cached, which is named in the gate record above.

## Family 3 — page coverage checked without the release's own page override

**Trigger.** The restored obligation-6 module's positive control failed on the
genuine published corpus: `persisted ledger omits authoritative printed pages
[2, 3, 4, 27]`. A gate that rejects real data looks green in every negative test
and fails only when an operator runs the command.

**Structure at fault.** `verify_persisted_page_coverage` defaults to demanding
every printed page of the book unless the caller passes the `expected_pages`
override that `finalize_source_release` records in `transform_config`
(`leaf_primary_pages`). The source-built corpus legitimately files no leaf on
four TOC-only pages.

**Siblings inspected.** Both production call sites of
`verify_persisted_page_coverage`, and both readers of `expected_leaf_pages`.

| Sibling | Disposition |
| --- | --- |
| `scripts/reset_corpus_baseline.py:208` (`validate_corpus_payload`) | `patched` — reads the release's own `transform_config` and passes `expected_leaf_pages(...)` |
| `ingestion/corpus/persistence.py:1352` | `already safe` — admission mechanism: it passes `expected_pages=expected_leaf_pages(artifacts.release.transform_config)` at line 1355, and the replacement corpus — which omits pages 2, 3, 4 and 27 — publishes through it green in `test_source_lifecycle.py`. A corpus that would trip the defect passes this caller in a live test |
| Retired PDF-geometric releases (no `leaf_primary_pages` recorded) | `already safe` — admission mechanism: `expected_leaf_pages` returns `None` for a release that records none (`source_ledger.py:302-311`), which restores the original all-printed-pages behaviour those releases were verified under. The fix cannot loosen a check for a release that never declared an override |

**Regression coverage.** Proven load-bearing by reverting it: with
`validate_corpus_payload` back to its pre-fix form, the positive control and the
canonical-proof test both fail with exactly that message. Restored and re-run
green (8 passed, 60.76s) before the commit.

# Gate results — increment 6, shared 5d tooling against the replacement corpus

Code head `f07a36d` for the implementation; this entry and the §8.9
reconciliation land in a `docs` follow-up, and the final head is reported in
the handoff.

**The aggregate suite below ran on the tree committed as `f07a36d`, and was
not re-run on the follow-up head.** That is stated rather than papered over,
and it is sufficient here for a checkable reason: the follow-up touches two
markdown files and five `#:` comment lines in one test module, and
`git diff f07a36d <follow-up> -- tests/` contains no changed line that is not
a comment. `src/` is byte-identical between the two heads, so `mypy src/`
carries over unchanged. What could move was re-run on the follow-up head: the
three affected test modules (43 passed in 56.61s), `black --check` and `ruff
check`. A 22-minute aggregate re-run would have re-proved the same tree.

## Formatting, lint, types

| Gate | Result |
| --- | --- |
| `black --check src/ tests/` | 507 files unchanged |
| `ruff check src/ tests/` | All checks passed |
| `mypy src/` | Success: no issues found in 234 source files |

## Tests — the required aggregate gate

`venv/Scripts/python.exe -m pytest tests/ -q`, run attached, exit 0:

**6,419 passed, 141 skipped, 248 warnings in 1353.76s (22:33). Total coverage
92.22%.**

Against the stated baseline of 6,395 passed / 141 skipped / 92.20%, that is
**+24 tests and +0.02%**. The 24 are accounted for exactly:

| Module | New tests |
| --- | ---: |
| `tests/ingestion/mechanical/test_source_release_readiness.py` (new) | 15 |
| `tests/ingestion/mechanical/test_bound_corpus.py` | 6 |
| `tests/ingestion/mechanical/test_proposal_boundary.py` | 3 |

**Skips: 141, unchanged from baseline.** That is *count parity*, not an
individual re-audit — the skip set was not inspected test by test. The
real-embedder coverage that skips on uncached hosts is included in that count;
this host has the model cache, so those tests ran rather than skipped, which is
consistent with the count not moving. No skip was introduced by this increment
and none was silently accepted.

## Coverage of the changed modules

New-code minimum is 80%. Both changed source modules are far above it:

| Module | Stmts | Miss | Cover | Missing |
| --- | ---: | ---: | ---: | --- |
| `ingestion/mechanical/bound_corpus.py` | 92 | 1 | 99% | 172 |
| `ingestion/mechanical/proposal.py` | 88 | 3 | 97% | 214, 333-334 |

## Diff size — what is actually new code

`git diff --numstat d128103..f07a36d`:

| Path | + | - |
| --- | ---: | ---: |
| `src/afterworlds/ingestion/mechanical/bound_corpus.py` | 107 | 10 |
| `src/afterworlds/ingestion/mechanical/proposal.py` | 122 | 2 |
| `tests/ingestion/mechanical/test_source_release_readiness.py` | 560 | 0 |
| `tests/ingestion/mechanical/test_bound_corpus.py` | 123 | 3 |
| `tests/ingestion/mechanical/test_proposal_boundary.py` | 78 | 0 |
| `tests/ingestion/conftest.py` | 64 | 1 |
| `tests/ingestion/corpus/conftest.py` | 7 | 19 |
| `docs/architecture/issue-5c-5d-clean-restart.md` | 160 | 0 |

**Production source is 229 added / 12 removed across two files** — two
functions and one factored-out helper. The remaining 1,000-odd added lines are
tests, fixtures and the architecture record. That ratio is the point of the
increment: the shared path needed one small piece of code and a large amount of
evidence that it behaves against the real replacement corpus.

## pip-audit

`Found 31 known vulnerabilities in 11 packages` — **unchanged from the stated
baseline of 31/11**, and non-green there as here. No dependency was added,
removed or pinned by this increment, and no audit suppression or dependency
cleanup was performed; the brief explicitly did not request it.

## detect-secrets

Run exactly as `.pre-commit-config.yaml` configures it, on the eight staged
files after `git add`:

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook \
  --baseline .secrets.baseline <the eight staged paths>
```

Exit 0, no output. `.secrets.baseline` is unmodified in `git status`. The
baseline was not passed as a scanned file and was not grown.

**One invocation returned 1, and is reported with its cause rather than
dropped.** Scanning the follow-up commit's gates-log file immediately after a
`git add`, the hook exited 1; consecutive re-runs on the identical file then
exited 0. It was diagnosed at the source, not assumed away.

`pre_commit_hook.main` has exactly two exit-1 paths: a printed secret
diagnostic, and `parse_args` raising `ValueError` from
`raise_exception_if_baseline_file_is_unstaged`. No diagnostic was printed, so it
is the second — the hook refusing to run because it believed
`.secrets.baseline` had unstaged changes. It did not. The baseline is checked
out CRLF on this Windows host and stored LF (`git add` emits *"in the working
copy of '.secrets.baseline', CRLF will be replaced by LF"*), so a `git add` of
another path invalidates git's stat cache for it and the very next
`git diff --name-only` reports it dirty until the content compare refreshes the
cache. The hook makes that first call; the refreshed cache is why every
subsequent run is clean.

This is a Windows line-ending artifact of the local checkout, not a finding and
not a baseline rewrite. Verified rather than asserted: `git diff HEAD --
.secrets.baseline` is empty, `generated_at` still reads `2026-09-21T14:03:33Z`
— the value already in `HEAD` — and `detect_secrets.util.git`'s own
changed-but-unstaged list contains no baseline entry once the cache is warm.
Nothing was added to the baseline to silence anything.

## Not run, and why

* **Remote CI.** Nothing was pushed; no PR exists for this branch. No remote CI
  result is claimed.
* **`/code-review ultra`.** User-triggered and billed; cannot be launched from
  here.
* **Publication and activation of a 5d projection.** Deliberately not run. The
  obligation-5 publish/activate/runtime proof is retained as a later obligation;
  satisfying it now with a partial projection is exactly what the brief
  forbids.

## Reconciliations this increment makes to the record

1. **§8.9.1 said "four of the five behaviours"** over a six-row table in which
   every row was already-ready. Corrected: every behaviour the brief asks to be
   proved was already implemented, and the gap closed here is *authoring*, not
   proof. The old-authority and mismatched-authority rows are two mechanisms at
   two seams, not one behaviour listed twice.
2. **"The seven accepted batches"** is the count at the 16 September decision.
   `known_unknowns.md`:284 records seven then and **nine by the restart**. The
   doc now states both; the commit message of `f07a36d` carries the stale
   "seven" and is corrected here rather than by rewriting a pushed-adjacent
   commit.
3. **`PROBE_SECTION`'s comment said it was "deliberately not named for the
   pilot."** Blinded *is* a member of the Conditions family §8.9.5 proposes as
   the pilot. Corrected to what is true: it is a realistic member, seeded
   whole-leaf and `UNRESOLVED` with no review unit, asserting nothing about what
   Blinded means and presuming nothing about pilot scope.
4. **The five open interpretation questions had no proposed answers.** Each now
   carries a one-line default, explicitly marked a proposal rather than a
   decision, with the review-unit-kind question first because it constrains the
   other four.

## Standing constraints honoured

No push, no PR, no merge. No production semantic acceptance, publication or
activation — `COMMITTED_ORACLE_DIR` holds the same two entries it held at
`d128103`, and `git status` shows the directory unchanged. No file under it was
written. The one file under it was *read* once, outside the code path: the
superseded oracle was `json.load`ed at a shell to check the accepted-batch
count for reconciliation 2 above. No committed code reads it — `proposal.py`
does not touch `oracles/` at all, and nothing in this increment loads accepted
authority. All build and persistence
went to `tmp_path_factory` stores and isolated Chroma clients. The four stashes
(`{0}` hygiene-pass, `{1}` issue-60, `{2}` decommission-auto-fix-loop, `{3}`
issue-3-sqlite-persistence) are intact and verified after the commit; 605
untracked scratch files remain untracked. Files were staged by name; `git add
-A` was not used. No `git gc`, `prune` or `reflog expire`.

# Gate results — increment 7, the glossary ownership correction

Head: the commit this entry lands in. One commit: the source byte, its manifest
entry, the evidence that names it, the release identity it moved, and the two
test modules that asserted the old ownership. They are one commit because
`load_pinned_sources` refuses a build whose bytes do not hash to the manifest,
so splitting the edit from the manifest would commit a tree that cannot build.

## What this increment changed, and what it did not

**No production code was added.** The only `src/` change is two numbers in a
`#:` comment in `pipeline/retrieval/corpus_windows.py`. The new-code coverage
minimum therefore has nothing to measure: there is no new production statement
in the diff. What changed is one byte of pinned source, its manifest entry,
three architecture documents, and two test modules.

| Path | + | - | What |
| --- | ---: | ---: | --- |
| `docs/sources/community/dnd-5e-srd-markdown/rules-glossary.md` | 1 | 1 | `### Swim Speed` — `#### Swim Speed` |
| `docs/sources/community/dnd-5e-srd-markdown/source_pin.json` | 16 | 5 | digest, bytes, the family-H correction entry, two totals |
| `docs/architecture/issue-5c-5d-community-source-corrections.md` | 47 | 5 | family H, the trigger, the sibling evidence, the dispositions |
| `docs/architecture/issue-5c-5d-community-source-coverage.json` | 2 | 1 | regenerated |
| `docs/architecture/issue-5c-5d-clean-restart.md` | 172 | 38 | §8.1 identity, §8.8.2 windows, §8.9.2, §8.9.3, §8.9.5, new §8.10 |
| `src/afterworlds/pipeline/retrieval/corpus_windows.py` | 2 | 2 | measured window figures in a comment |
| `tests/ingestion/source/test_community_source_structure.py` | 35 | 0 | the glossary entry-run regression |
| `tests/ingestion/mechanical/test_source_release_readiness.py` | 37 | 33 | correct ownership replaces the wrong-ownership assertion |

## The new release identity

Built in isolation through `build_source_candidate`, no persistence:

| | Superseded | Current |
| --- | --- | --- |
| Package UUID | `4f1bf24f-b64e-5706-924d-b50c2753e67e` | `9717e288-c099-5217-b2d2-f89aeabd7b73` |
| Release version | `5.2.1-corpus.6a11f2c0-393` | `5.2.1-corpus.883aabdf-462` |
| `transform_config_hash` | `041d839a…` | `08cbcb4f9b1bb86a272def982a6f3416e200d227f1e4beda0c116ad70f8d0155` |
| Frozen source ledger hash | `72ddaf29…` | `301a1d6a502789f3e905b050072be91cc77e86517991196fdc14c8b5024bdaf4` |
| Bundle root hash | `758b7b63…` | `c3b3668bb7dc5220eee9e7191008cfe92103b7e5eb6e003e97eebc7708f50cf1` |
| `rules-glossary.md` sha256 | `9b25315e…` (72,860 B) | `3fa8904be1e84bfafda24bf673c5e30ad899bd4135809a4c4dfd1d738f0d5ead` (72,861 B) |
| Units / chunks | 10,465 | 10,465 |
| Embedding windows | 11,077 | 11,076 |

`SOURCE_TRANSFORM_VERSION` stays at 3. The pin manifest's per-file digest is
inside `SOURCE_PIN` in the transform config, so the changed byte moved
`transform_config_hash` and both derived identities on its own. A bump is for a
changed *recipe*; this was a changed *input*.

## Bounded source evidence

| Measurement | Before | After |
| --- | ---: | ---: |
| `rules-glossary.md` heading-rank census | `{1: 1, 2: 2, 3: 1, 4: 154}` | `{1: 1, 2: 2, 4: 155}` |
| Units whose ancestors include `Swim Speed` | 47 | 0 |
| Glossary entries captured | 13 | 0 |
| Glossary units by container-path depth | `{1: 1, 2: 10, 3: 435, 4: 47}` | `{1: 1, 2: 10, 3: 482}` |

Official pages read off the built ledger rather than transcribed: Swim Speed and
Swimming cite p.189, Target and Telepathy p.190, Unconscious and Weapon Attack
p.191. The correction entry records pp.189–191 on that basis.

Bounded to `rules-glossary.md` deliberately. The census *is* the proof for a flat
entry run, and `spells.md` and `magic-items.md` legitimately mix heading ranks
(a stat block sits one level under the entry that summons it), so a corpus-wide
rank census would report noise rather than residue. No unrelated settled source
was re-audited.

## Formatting, lint, types

| Gate | Result |
| --- | --- |
| `black --check src/ tests/` | 507 files unchanged (two files were reformatted first and are committed formatted) |
| `ruff check src/ tests/` | All checks passed |
| `mypy src/` | Success: no issues found in 234 source files |

## Tests — the required aggregate gate

`venv/Scripts/python.exe -m pytest tests/ -q`, run attached, exit 0:

**6,420 passed, 141 skipped, 248 warnings in 1,386.46s. Total
coverage 92.22%.**

Against increment 6's 6,419 passed / 141 skipped / 92.22%, the move is **+1
test** — `test_every_glossary_entry_is_a_peer_of_every_other`. The readiness
module's replaced test is a rename, not an addition: 15 tests before and 15
after.

**What tree those figures measure, stated rather than assumed.** The run
launched at roughly 13:42 local, after every `src/`, `tests/`, pinned-source and
manifest edit of this increment was already in the tree; the only edits that
landed after the launch were markdown, in `issue-5c-5d-clean-restart.md` and in
this log. Two checks rather than an assurance: `find src tests -name '*.py'
-newermt '2026-09-21 13:41:00'` returns nothing, and `git status --porcelain --
src tests` is empty at `6e18d1d`, so `src/` and `tests/` are byte-identical
between the tree the suite ran on and the committed head. No test reads
`issue-5c-5d-clean-restart.md`: `grep -rl` finds it only inside a `#:` comment
and a skip-reason string in `tests/ingestion/conftest.py`, neither of which
opens the file. The markdown that moved after the launch is therefore outside
what any gate here measures. This disclosure lands in a follow-up `docs` commit
of its own, which touches this log and nothing else.

**The regression was run against the defect, not only against the fix.** With
the uncorrected byte restored in a scratch copy of the working tree, the new
assertion fails with `rules-glossary.md:1445 Target is owned by ['Rules
Glossary', 'Rules Definitions', 'Swim Speed']`; the byte was restored
immediately afterwards and the file's sha256 re-verified. A regression that has
never seen the defect is a restatement of the source, not a guard.

`tests/pipeline/retrieval/test_corpus_windows.py` re-measures every window of
the corrected corpus through the real ONNX MiniLM tokenizer and passes, which is
what keeps the 448-character budget claim true after the window count moved.

## pip-audit

`Found 31 known vulnerabilities in 11 packages` — **unchanged from the stated
baseline of 31/11**, and non-green there as here. No dependency was added,
removed or pinned, and no audit suppression or dependency maintenance was
performed.

## detect-secrets

Run exactly as `.pre-commit-config.yaml` configures it, on the staged files
after `git add`:

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook \
  --baseline .secrets.baseline <the staged paths>
```

**Resolved and green.** Before the baseline update the hook reported one
finding:

```
ERROR: Potential secrets about to be committed to git repo!
Secret Type: Hex High Entropy String
Location:    docs/sources/community/dnd-5e-srd-markdown/source_pin.json:319
```

Line 319 is the glossary's new sha256. The finding is the changed digest, not a
credential: `source_pin.json` holds 28 baselined hex digests already, and this is
one more public content digest of a file this repository ships.

**Correction: the required change is an addition, count 28 → 29.** This entry
previously prescribed the `b70d016` remedy — an in-place splice holding the count
at 28, one `hashed_secret` replaced and the rest renumbered — and that
prescription was wrong here. It assumed the digest being replaced leaves the
manifest. It does not: the pre-correction upstream glossary digest is still
recorded in `source_pin.json` alongside the corrected one, so removing its
baseline entry would make the baseline disagree with the file it describes.
Codex re-measured the target with a real same-settings scan (the candidate
baseline and its generator sit beside the September 21 review prompt) and the
structural diff is:

* **added** — `Hex High Entropy String` on
  `docs\sources\community\dnd-5e-srd-markdown\source_pin.json`,
  `hashed_secret` `ca34922fc056524570e06577d58b4a54255d7aba`,
  `is_verified` false, `line_number` 319. That hash is detect-secrets' SHA1 of
  the corrected glossary's public SHA256 string, not a credential.
* **moved** — `1b921204…` 327 → 338, `95f325d9…` 329 → 340,
  `fb3c2e3b…` 428 → 439.
* **removed** — nothing. All 28 existing target hits are preserved.
* **unchanged** — `generated_at`, `version`, `plugins_used`, `filters_used`, and
  every other file's findings.

The splice therefore asserts 28 -> 29 with exactly one addition and an empty
removal set, not a stable count.

**It has now been performed, under the Owner's explicit authorization, in an
interactive session that could carry the write.** The approved semantic change
was applied to `.secrets.baseline` by replacing it with the reviewed candidate
(`proposed-secrets-baseline.json`), which a byte-level `diff` against the
pre-change file showed to differ only in the four hunks of the reviewed patch:
the seven added lines of the new finding and the three renumbered
`line_number` values. `git diff --numstat -- .secrets.baseline` reads `10 3`.
The file remains CRLF with a trailing newline (350,554 bytes; 7,898 line
terminators, all CRLF), so no line-ending churn was introduced.

Three independent confirmations were made before applying it:

* `rules-glossary.md` on disk is 72,861 bytes and hashes to
  `3fa8904be1e84bfafda24bf673c5e30ad899bd4135809a4c4dfd1d738f0d5ead`, the value
  recorded at `source_pin.json:319`.
* detect-secrets' SHA1 of that string is
  `ca34922fc056524570e06577d58b4a54255d7aba`, the added `hashed_secret`; SHA1 of
  the pre-correction upstream digest `9b25315e...` is
  `a7403244a9203ce678e4cc712cb7cca20db22fe9`, which is the *existing* entry at
  `line_number` 317. Both digests remain in the manifest, which is why the
  correct change is one addition and not a replacement.
* All 29 recorded `line_number` values were resolved against `source_pin.json`
  and each one lands on a hex token whose SHA1 equals its `hashed_secret`. No
  finding is stale, so the hook has nothing to renumber.

The gate was then run exactly as configured, on the target source file, with the
baseline staged (the hook's ordinary staging requirement; its first invocation
exited 1 with `Your baseline file (.secrets.baseline) is unstaged.` and no
finding):

```
venv/Scripts/python.exe -m detect_secrets.pre_commit_hook \
  --baseline .secrets.baseline \
  docs/sources/community/dnd-5e-srd-markdown/source_pin.json
```

**exit 0.** The baseline's SHA256 is
`1ecf841cc71291f9feb63eb59ae0fb49c79c8833c78858757fd84a5ace6415f9` both before
and after the scan, so the hook rewrote nothing — `generated_at`, `version`,
`plugins_used`, `filters_used` and every other file's findings are byte-identical
to the reviewed candidate. This document was scanned the same way and also exits
0, despite quoting the digests above.

Nothing was bypassed. `--no-verify` was not used and was not needed (this
repository has no installed git pre-commit hook — `.git/hooks` holds only the
samples — and CI does not run detect-secrets). No detector or filter setting was
changed, no suppression or allowlist pragma was added, and `.secrets.baseline`
was never passed to the scanner as a source file. Staging was by explicit path;
the untracked `.claude/_*` scratch files in the tree were not added.

**This gate is passed for the source correction.** It says nothing about
`pip-audit`, which remains non-green at the unchanged 31 vulnerabilities in 11
packages.

## Not run, and why

* **Remote CI.** Nothing was pushed; no PR exists for this branch. No remote CI
  result is claimed.
* **`/code-review ultra`.** User-triggered and billed; cannot be launched from
  here.
* **Publication or activation of a 5d projection, and any semantic acceptance.**
  Deliberately not run. The brief holds pilot authoring until the corrected
  source/consumer boundary has been reviewed.

## What this entry corrects in the record

1. **The readiness record asserted the defect as fidelity.**
   `test_selection_survives_the_sources_own_irregular_depth` asserted that
   `("Swim Speed", "Unconscious [Condition]")` selected Unconscious's leaves,
   and its comment called the `h3` faithful 5c structure that it would be 5d
   overreach to change. Both are gone. The replacement,
   `test_selection_qualifies_a_label_by_the_labels_above_it`, asserts the
   official ownership: the real ancestor `Rules Definitions` narrows to the same
   leaves, the former owner selects nothing, and the two label sets are
   disjoint. Suffix matching is kept and is now justified by what it is actually
   for — qualifying a printed label without assuming a depth — not by
   accommodating bad source.
2. **§8.9.5 said Exhaustion is a list of six enumerated levels.** Official p.181
   prints one condition with four labelled effects: cumulative level, death at
   6, D20 Tests reduced by 2 × level, Speed reduced by 5 feet × level, a Long
   Rest removing 1 and the condition ending at 0. The claim and the proposal
   built on it are withdrawn, and the replacement proposal is written from the
   glossary text with the consumer benefit it earns.
3. **§8.9.5's five questions read as an approval gate** — "authoring can begin"
   if a reviewer "accepts all five defaults". They are ordinary
   proposal-organisation choices and are now recorded as such, each with its
   source and its consumer benefit. What remains explicit and held is semantic
   acceptance, which no proposal or default in that section can perform.
4. **Family G's "already safe" row for record ownership is superseded**, and the
   reason is its admission mechanism: the evidence was a *per-stat-block*
   report, which admits nothing about a run holding no stat block. The glossary
   is exactly that run. The row now says so and family H carries the residue.
5. **The window figures moved and are re-measured, not carried forward.** A
   window's 448-character budget is shared with its section-label prefix;
   dropping `Swim Speed > ` from 47 units' label stacks freed 13 characters and
   one unit that needed two windows now needs one. 11,077 windows became 11,076
   and 500 multi-window chunks became 499, in the identity table, §8.8.2 and the
   `WINDOW_CHAR_BUDGET` comment. The increment-5 and increment-6 entries keep
   the figures they measured; those were true when written.

## The superseded identity is not quarantined

Quarantine refuses *persisted* authority by identity.
`4f1bf24f-b64e-5706-924d-b50c2753e67e` / `5.2.1-corpus.6a11f2c0-393` was only
ever built into `tmp_path_factory` stores inside a test session. Nothing
accepted it, nothing published it outside an isolated store, `oracles/` holds no
artifact bound to it (its two entries are `README.md` and the quarantined
`srd-5-2-1-corpus-36b786d8-fa2.json`), and `scripts/reset_corpus_baseline.py`
does not name it. There is nothing persisted for a quarantine entry to refuse,
so adding one would be ceremony rather than a guard. The existing quarantine
sets are untouched.

## Standing constraints honoured

No push, no PR, no merge. No semantic acceptance, publication or activation. All
building went to isolated stores — the identity and window probes build in
memory and persist nothing, and the test suites use `tmp_path_factory` SQLite
files and private Chroma directories. No file under `COMMITTED_ORACLE_DIR` was
read or written by this increment. The four stashes (`{0}` hygiene-pass, `{1}`
issue-60, `{2}` decommission-auto-fix-loop, `{3}` issue-3-sqlite-persistence)
are intact. Untracked scratch remains untracked; files were staged by name and
`git add -A` was not used. No `git gc`, `prune` or `reflog expire`.
