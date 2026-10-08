# Codex selector refusal finding — 7 October 2026

**P2 — the new superseded-release refusal is bypassable by a string subtype.** `oracle._resolve_committed_inputs` checks the caller's `release_version` directly against `SUPERSEDED_RELEASE_VERSIONS`. A `str` subtype with equal string contents but a different hash is not found in that set, yet compares equal to the artifact's plain release string during the directory scan. `committed_inputs_for` consequently returns the retired `3fe` accepted inputs instead of refusing them.

The read-only native reproduction is retained in `run/codex-selector-subclass-before.log` and its raw `.exit` file: `retired_binding_refused=false`, `retired_inputs_returned=true`, **exit 1**. The harness wrapper itself exits 0; that is not the selector diagnostic's result. No artifact or persistence was changed. Source of the diagnostic: `.claude/_sp/release-readiness-20261007/codex_selector_probe.py`.

Expected correction: establish the primitive/canonical identity domain before hashing or comparing caller-supplied identities, so string subtype behavior cannot select retired authority. Reuse the existing trust-boundary conventions where sufficient. Preserve ordinary current-binding success, absent/duplicate behavior and the quarantined-product refusal. Add a small negative regression covering both exported committed-input/oracle selectors through their shared implementation; do not repeat full native historical replays for this scalar check.

**Classification:** issue-scoped implementation defect in the newly added retirement boundary. No new ownership or semantic decision is needed. This is one concrete review finding, not a reason to redesign oracle loading or broaden source/semantic review.

## Verification economy

The initial 14-file fixture-family diagnostic took 23 minutes 52 seconds and already establishes its failure family. Reuse that evidence. During correction, choose small representative checks for the specific shared seams changed; the upcoming required full default suite will exercise the entire corrected family with coverage. Avoid repeating a whole historical replay sweep merely to prove it still failed before correction.
