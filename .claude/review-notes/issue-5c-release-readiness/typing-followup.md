# CRD Issue 5c restart — release-readiness: test typing correction

## Authority

- The [21 September restart Owner Decision](../../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md), `CLAUDE.md` and the ADRs.
- The [owner deferral clarification](../issue-5c-release-order-recording/owner-deferral-clarification.json): only dependency-vulnerability repairs keep the after-restart deferral.
- The current restart opening.

This increment grants no staging, commit, push, merge, publication, activation or shared-store write authority. The accepted oracle `srd-5-2-1-corpus-8781d4e0-a3b.json` (`def7caa1…`) was not touched.

## Result

All 16 strict mypy errors from `gates-mypy-tests-2` are closed. Only test code changed; no production code or checker settings did. No assertion was removed, and no `Any` or `type: ignore` was added. Eight `type: ignore` comments at the edited sites were removed. In `mypy-before`, 5 of them were reported unused and 2 did not cover the error on their line.

| File | Errors | Change |
|---|---|---|
| `tests/ingestion/mechanical/conftest.py` | 3 | `build_candidate` narrows popped `ledger`/`representation` overrides with `isinstance` asserts instead of two ignores. Its `**overrides: object` signature is kept because five helpers forward `**overrides` through it. The `session` fixture is typed `(tmp_path: Path) -> Iterator[Session]`. Added `json_object`/`json_array` narrowing helpers (`isinstance` assert, then return). |
| `tests/ingestion/mechanical/test_oracle.py` | 9 | `_payload()` narrows `json.loads` through `json_object`. The `mutate` parameter is typed `Callable[[dict[str, object]], None]`. Nested payload edits narrow each level through the helpers. |
| `tests/ingestion/mechanical/test_accepted_inputs.py` | 4 | `acceptance` and `review_units` are narrowed through the helpers. The two used ignores at lines 1212–1213 are untouched. |

A wrong-shaped payload still fails, now through an assertion in a helper rather than a `TypeError` in the test body. Each mutating test still asserts the same native refusal or identity outcome.

## Evidence

All raw logs and exits are under [`run/`](run/). `run/run.py` refuses to overwrite. The wrapper sets `RTK_DISABLED=1 PYTHONUTF8=1 MYPYPATH=src`, and each `.exit` file holds the raw command exit.

| Run | Raw exit | Result |
|---|---|---|
| `mypy-before` | 1 | 16 errors in the three files |
| `mypy-before-vs-recording` | 0 | [`compare_mypy_logs.py`](run/compare_mypy_logs.py): the recording's `gates-mypy-tests-2` and `mypy-before` have identical (file, message) multisets, 16 = 16 |
| `mypy-after-1` | 1 | Intermediate: typed `build_candidate` keywords broke the `**overrides` forwarder at `conftest.py:883`; that approach was replaced |
| `mypy-after-2` | 0 | `--strict`, three files: no issues |
| `mypy-consumers` | 1 | `--strict`, the three files plus 12 consumers: 105 errors in 7 consumer files, none in the three repaired files, `test_committed_accepted_authority.py` or `test_source_release_readiness.py` |
| `mypy-consumers-preedit-copies` | 1 | The same 15 files with the three repaired files at their pre-edit bytes (input SHAs equal `mypy-before`'s), under `.claude/_sp/release-readiness-20261007/consumer-preedit/`: 121 errors |
| `mypy-compare` | 0 | [`compare_mypy.py`](run/compare_mypy.py): 121 → 105. The 16 removed are exactly the target errors; none were added |
| `black-check` / `ruff-check` | 0 / 0 | The three files |
| `secrets-typing-private-copy` | 0 | Hook against a private copy of `.secrets.baseline` (`7d7738f6…`, equal to the pre-edit snapshot): the restart doc, the three test files, and this folder before this row was written. A read-only `SecretsCollection` scan of the same files found 0 detector hits, so no baseline change was needed; the copy was left unchanged |
| `secrets-typing-real-hook` | 1 | **Not green**: "Your baseline file (.secrets.baseline) is unstaged." Nothing was staged, and the baseline is unchanged |
| `focused-typing` | 0 | `scripts/run_focused_tests.py --check` on the three files. Ran all of `test_oracle.py`, the two edited `test_accepted_inputs.py` tests, and all of `test_persistence`, `test_persisted_evidence`, `test_projection`, `test_review_units`, `test_gate`, `test_canonical_ordering`, `test_digest_recording` and `test_raw_state_closure`: **305 passed. FOCUSED DIAGNOSTICS ONLY**, not acceptance or full-gate evidence |
| `focused-typing-2` | 0 | The remaining `build_candidate` callers: `test_schema_12_practical_reliability` and `test_review_round_3_applicability_types`, which pass `representation=`/`ledger=` directly into the new asserts, plus `test_publication`, `test_concurrent_publication` and `test_report`. **174 passed. FOCUSED DIAGNOSTICS ONLY** |

Together, the two focused runs cover every file that calls the mechanical conftest's `build_candidate` or `reviewed_candidate`. The `build_candidate` in `tests/ingestion/conftest.py` and `test_ledger_pipeline.py` is a separate production function from `afterworlds.ingestion.corpus.pipeline`. The `session` fixture change is annotation-only and has no runtime effect.

Line endings: the child tools wrote CRLF into the logs, and the original `run.py` wrote CRLF into the `.exit` files. Twenty files were later normalized from CRLF to LF, with no other bytes changed:
- the 17 files from the runs before `secrets-typing-private-copy`;
- `secrets-typing-real-hook.log`, `focused-typing-2.log` and `mypy-before-vs-recording.log`.

A Python byte check then found no CR anywhere in this folder. The repository's `.gitattributes` (`eol=lf`) would normalize these files the same way.

`run.py` was edited during this increment, after the `mypy-*`, `black-check`, `ruff-check`, `focused-typing` and `mypy-compare` runs. The only change makes it write `.exit` files with LF. Its docstring's "copied from … sha 2f51f230" describes the original copy; apart from the docstring's provenance line, the current file differs from that copy only on that line.

After the final edits, the read-only `SecretsCollection` scan was repeated over 35 files: the restart doc, the three test files and this folder. It found 0 detector hits, so the hook was not rerun.

No full suite or coverage run was launched. These proofs are reused unchanged because this increment touches neither the oracle nor production code: native persistence, the 40-check payload comparison, the reader proofs and source order. Their evidence is in the [recorded follow-up](../issue-5c-release-order-recording/recorded-followup.md) and the Codex recording review.

## Remaining gate and ownership inventory

| Item | Classification | Owner | Smallest remedy |
|---|---|---|---|
| 105 pre-existing strict mypy errors in 7 test files (`test_persistence` 72, 71 of them one `.level` access over the fact union at line 91; `test_review_units` 13; `test_raw_state_closure` 8; `test_canonical_ordering` 4; `test_schema_12_practical_reliability` 4; `test_review_round_3_applicability_types` 3; `test_gate` 1) | Discovered non-dependency defect, not deferrable; outside this increment's three-file scope | Restart implementing engineer, next bounded increment | Narrow at each site with `isinstance`, typed forwarders or the new `json_*` helpers, and remove the 5 unused ignores. These errors carry no runtime or production change. **Closed 2026-10-07:** see [the readiness correction](correction-followup.md) |
| Generator-rebuild tests that pin the old binding's bytes (about 25 files, for example `test_classes_proposal.py:166,825`) | Fails before and after the recording | Owner Decision on intent, then the engineer | Repin them to the superseded binding as history, or retire them with the superseded release. **Superseded 2026-10-07:** no Owner Decision was needed; corrected per file in [the readiness correction](correction-followup.md) |
| Superseded `srd-5-2-1-corpus-3fe24ff6-4e3.json` | Owner Decision needed | Owner | Retire or quarantine it. **Superseded 2026-10-07:** the 21 September Decision already authorizes retirement; resolution now refuses the release, see [the readiness correction](correction-followup.md) |
| Used ignores at `test_accepted_inputs.py:1212–1213` | Non-blocking cleanup | Engineer | Narrow with `json_object`/`json_array` |
| Full suite, coverage and repository-wide mypy | Outstanding final gates | Codex is reconciling scope | Run on the exact final head |
| Real relative-path secrets hook (exit 1: `.secrets.baseline` unstaged) | Not green; resolves only at authorized staging | Delivery workflow | Stage with the delivery; nothing is staged here |
| Dependency-vulnerability repairs | Deferred until restart completion | — | — |

## Architecture Notes

No drift from design principles. Test-only typing changes keep the existing runtime acceptance semantics and production types. Narrowing uses assertions in the existing shared conftest, not checker exemptions.
