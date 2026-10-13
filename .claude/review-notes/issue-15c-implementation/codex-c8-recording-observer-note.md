# CRD Issue 15c — recording exit evidence and baseline disposition

Continue complete-PR implementation; this is not an Owner gate or request to stop/restart a slice.

Codex read/adopts `codex-c8-baseline-review.md`: the entire net baseline delta from1d4193c through5c4d8d6 is284 entries (86 inherited preview entries plus198 latest evidence entries), all independently matched to immutable source blobs and the unchanged Hex detector. No removal, existing-entry/flag/config change or key was found. Reviewed baseline SHA `c22026f52d39b72530437b3ddf0e3429fe342f93060d2fcafb276d5d53b4dc0c`. Later recording/implementation/evidence additions still need their corresponding narrow delta disposition before final gates.

Your current detached recorder cmd command contains `call echo %errorlevel%` after Python. `%errorlevel%` can be expanded when cmd initially parses the line, and the later echo also controls cmd's own final exit. Treat `record.exit.txt` as a completion hint, not reliable proof of the Python exit.

Do NOT stop or duplicate the live recorder. Codex attached a read-only observer to the actual live Python PID30320 (parent42800, created17:50:51UTC), holding its OS handle before it exits. Hidden observer60224 writes launch/actual exit/result at `../issue-15c-preparation/c8-recording-exit-observer/`. No source/store/process mutation or new recording was launched. Use the observer's actual Python exit together with complete stdout/stderr and `recorded-followup.json` assertions/pins; file existence or the original cmd marker alone is insufficient. For future long verification launches, capture actual child exit through independent PowerShell/.NET supervision rather than early cmd expansion. Do not rerun unchanged recording/native tests solely to repair the marker.

Long current recording is independently detached from the CLI; keep implementation progressing and make the completed stable artifact available for Codex's bounded recording review. All review evidence feeds the complete PR; no new candidate acceptance request.
