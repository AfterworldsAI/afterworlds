# CRD Issue 15c — continue interrupted isolated native preparation

This continues the already authorized `codex-c8-native-preparation-request.md`; its scope, reviewed raw/schema inputs and all acceptance/runtime/merge boundaries remain unchanged. Read that request, the adopted changed-delta review and actual partial work before continuing. Main HEAD is still `1d4193c4b162e3db4df3a3240d00313f36dd918b`.

## Verified supervision interruption

`c8-native-preparation-run` returned exit 0 after a text-only lead result while the native worker had not finished. Its stderr explicitly states: `Background tasks still running after 600s; terminating. Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.` Approved CIM inspection found no remaining Claude CLI or original worker process. Native agent output is empty. The public stream contains partial schema/lift/validation/test edits, ending before their focused run; there is no complete native build, test or packet verdict. This explains this C8 interruption only; it does not establish the mechanism of the earlier 85-minute full pytest interruption.

The fresh hidden supervisor sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` only for its process and restores it afterward. It retains the existing same-session/model/Advisor, writer/CIM/head/import/accepted-source guards and auto permissions. This is an ordinary local supervision repair, not a new acceptance or shared-runtime permission.

## Continue, preserve and finish

Resume the SAME lead session. Continue the existing native work in `.claude/worktrees/agent-aa5b1ea6bf4ee4f39`, branch `codex/issue-15c-c8-preview`, from its partial edits; do not create another worktree or discard/regenerate valid partial work. If the native Agent's existing context can be resumed, resume that context instead of launching an independent new builder. Otherwise complete its remaining bounded work directly in this same isolated checkout. One native writer only.

The current source/schema/test edits are unfinished, not independently reviewed. Inspect the actual diff, verify preview-checkout imports and exact inputs, complete necessary focused schema/validation tests and then the guarded private SIMULATED build/replay/Owner packet. Reuse unchanged raw/source/old-C7 proof and preserve all r1/r2 evidence. No long full repository pytest here; it still waits for final accepted implementation. No speculative repetition of complete builds.

Do not end at “agent started.” Completion is an actual pinned native packet plus its build/test/replay evidence and durable status, or a concrete failure/true authority boundary. Wait for the native task's actual completion, verify its artifacts, and report actual results only. Keep main C7/schema20 and old C7 preview immutable. Never integrate schema21 into main, record real C8, execute new type-dependent mechanics or implement unapproved species input. No push/PR/merge, shared-runtime migration/publication/activation/app launch or gate weakening. #129 stays frozen; #132/#137 unchanged. Stop for independent Codex review at the exact native packet, then explicit Owner acceptance.
