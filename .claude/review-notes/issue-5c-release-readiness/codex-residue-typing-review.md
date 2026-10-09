# Expanded affected-test typing — finding and closure

**Closed, 7 October 2026.** `mypy-typing-final-1` reports native exit 0 on the final 42-file union of original and expanded affected tests. `codex-final-static-pins-1` verifies every checked hash unchanged. See the [final bounded review](codex-residue-final-review.md). The failed receipts and original finding below remain historical evidence; no typing deferral was granted.

## Original finding

`run/mypy-residue-post-1.log` and its native `.exit` record **76 errors in 15 files, checked 26 files, native exit 1**. The pre-copy check found 111 errors in 17 files. A decrease and zero newly introduced errors do not establish typing closure. The earlier original 16 and additional 105 errors remain closed; these expanded affected-test errors are also in scope for the Owner's current instruction. Only dependency-vulnerability repair is deferred.

Correct the finite 76-error inventory before completion. The private extracted inventory is `../../_sp/release-readiness-20261007/mypy-residue-post-1-inventory.json`; use the actual raw errors and current lines. Prefer imports from defining modules, properly typed direct helper imports, exact typed data forwarding/narrowing, and removal of genuinely unused ignores. Preserve deliberately malformed negative inputs through the appropriate raw/native seam. Do not add blanket Any/ignores, exempt files, relax strictness, or replace assertions to silence the checker. Existing diagnostics and accepted proof unaffected by pure typing/import edits remain reusable; run strict mypy on the affected 26-file map and preserve meaningful targeted diagnostics for any behavior-changing fix.

Do not call this check clean or record an unauthorized deferral. Use proper native exits and retain old failed receipts. Combine this finite typing correction with the native acceptance-evidence note before Codex review and coordinated final gates. No production, dependency, accepted-artifact or publication change is authorized by this note.
