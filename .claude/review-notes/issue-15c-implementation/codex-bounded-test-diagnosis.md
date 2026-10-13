# CRD Issue 15c — bounded diagnosis of the interrupted pytest run

Codex independently inspected the existing evidence on 12 October 2026 UTC. No tests were rerun, no processes were stopped, and no implementation or CI infrastructure was changed.

**Verdict:** the serial pytest run was externally killed without a verdict. The previously reported two-hour timeout is not supported by the timestamps. Session-end cleanup is a plausible explanation, not a proved root cause.

## Verified evidence

- Code under test: `eb60d9fd773b4e45f40d791a14e01af5175d0d81`, recorded in `gates/pytest-head.txt`. Current review head: `1473426762970dd532a01924dcfcb6183ccdf603`.
- Claude session: `0e66e7ef-76d3-41f4-bffb-e4af92ac5144`; background task: `b83n1om0k`.
- Saved Claude transcript line 1196 starts `venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`, redirects output to `gates/pytest-full.log`, and requests `timeout=7200000` with `run_in_background=true`. Its timestamp is `2026-10-12T03:06:12.810Z`; line 1197 confirms the task at `03:06:13.182Z`.
- `../issue-15c-preparation/implementation-run/stream.jsonl` lines 2402–2403 record `status=killed`, then `status=stopped`, with end time `2026-10-12T04:31:05.137Z`. Elapsed time from launch confirmation is **1:24:51.955**, about 35 minutes short of the requested timeout.
- The task output file ends with `[killed]`. There is no pytest summary, exit marker, coverage result, or recorded assertion failure. The shell's intended `echo "exit=$?"` never appears in the pytest log.
- The pytest log has 619 dots, progress through 7%, and another 43 dots. It advanced from 6% around 04:17 UTC to that later progress around 04:30. This argues against a continuously fixed hang, but quiet/buffered output cannot locate a particular test or rule out intermittent stalls.
- Claude's final assistant entry is timestamped `04:30:59.968Z`; its stream result says `stop_reason=end_turn`. The test task was killed about five seconds later. This temporal relationship suggests session cleanup; it does not establish which runner mechanism killed the process. No explicit `TaskStop` call for this task was found in the inspected tool-use records.

Transcript path: `C:\Users\raven\.claude\projects\D--AI-Claude-scratch-AW-docs-issue2b-implementation-afterworlds\0e66e7ef-76d3-41f4-bffb-e4af92ac5144.jsonl`. Inspection used tool/text/metadata only, not private reasoning.

## Baseline and limits

Existing `.claude/review-notes/issue-5c-release-readiness/run/final-pytest-coverage-2.log` records **7397 passed, 141 skipped in 19394.90s (5:23:14)**, ending `2026-10-07T21:42:29.566385+00:00`, exit 0. This is historical evidence that a serial suite can take hours; it is not acceptance evidence for the 15c head, nor a directly comparable performance benchmark.

The repository already runs eight CI shards, checks the combined collection census, and enforces combined configured coverage. `.github/workflows/ci.yml:45` already supplies `--durations=25` for slow-test visibility. The cached local node-ID list is incomplete and predates this run. Neither it nor the quiet log identifies the last executing test reliably.

## Disposition

- **Verification/process defect:** an interrupted background run was described with an unsupported timeout explanation. Correct its current status; preserve the original evidence.
- **No test or implementation defect established.** Do not invent a slow-test culprit, diagnose from the progress percentage, or broaden into CI remediation.
- **Next acceptance run:** after candidate acceptance and completion of dependent implementation, use the existing persistent exact-head CI shards and their duration reports. If a serial local run is required, its supervision must survive the Claude session and record completion/exit explicitly; verbose output can identify the last test. Do not launch that run now.
- Focused successes remain diagnostics only. Required repository gates, census, coverage and exact-head CI are unchanged. No permanent process-rule expansion is proposed from this one interruption.
