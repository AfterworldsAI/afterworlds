# Codex corrected mypy invocation — 7 October 2026

The ad-hoc single-file Checks/Actions/Rest mypy command omitted `MYPYPATH=src` and reported 35 diagnostics, including installed-package `import-untyped` errors. That output is an invocation/configuration failure, not a successful check and not an authorized typing deferral.

Codex reran the exact current test file through the retained native command harness, which explicitly sets `MYPYPATH=src`, `PYTHONUTF8=1` and `RTK_DISABLED=1`. `run/codex-mypy-checks-valid-invocation.log` and `.exit` show **strict mypy clean, exit 0**, on the input hash recorded in the raw log. No source, typing strictness, ignore settings or dependency installation was changed to obtain that result.

Use the same repository-source resolution for applicable final strict checks. If this file changes later, its captured result describes the earlier hash and the final affected check must use the settled file. Preserve the original diagnostic in the Claude stream; do not relabel it as passing evidence.
