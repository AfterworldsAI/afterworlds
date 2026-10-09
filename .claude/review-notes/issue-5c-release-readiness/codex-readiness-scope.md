# Codex bounded release-readiness scope — 7 October 2026

The Owner authorizes correction of the 16 test typing errors and other in-scope non-dependency defects before restart completion, then applicable final gates. Only dependency-vulnerability repairs retain the after-restart deferral. A pre-existing error is not automatically deferred.

## Authority reconciliation

The 21 September [Owner Decision](../../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md), especially Step 5 and its operating boundaries, already authorizes retirement of obsolete artifacts, paths and tests after checking useful lessons, references and active reachability. It forbids invented approval gates for settled engineering. Earlier current-status claims that retiring the superseded `3fe24ff6-4e3` oracle requires another Owner Decision are incorrect and must be corrected explicitly.

Live GitHub #132 and #137 were retrieved read-only to `.claude/_sp/release-readiness-20261007/issue-132.json` and `issue-137.json`. Their operational/practical-reliability amendments remain relevant; conflicting historical forensic topology and inherited-product clauses yield to the September 21 decision. Neither live issue has a September 21 restart banner. Prepare external synchronization through the established workflow when publication is authorized; do not edit GitHub in this increment.

## Concrete defect families

- **Typing:** the original 16 errors are repaired in three test/helper files. Expanded checking of their selected consumers reports 105 further diagnostics in seven files, including union narrowing, dataclass override typing, imports and deliberately malformed raw-state tests. Correct those concrete seams while preserving negative inputs and assertions. Do not expand checking to every unrelated test module merely to find more work.
- **Release fixture expectations:** Classes and Glossary rebuild tests combine the current `source_release_db` with the superseded `REPLACEMENT.ACCEPTED_PATH`. Inspect siblings in that same family. Preserve meaningful semantic, source, replay and failure checks; correct current-release expectations or retire assertions that only enshrine superseded bytes. Historical acceptance receipts must retain their actual historical binding.
- **Selector reachability:** the old `3fe` binding remains selectable by the exact committed-oracle directory scan. Inspect concrete dependencies and consumers, then retire/quarantine the obsolete selectable path with current-binding success and old-binding refusal coverage. No shared-store inspection or write, broad compatibility subsystem, or new semantic policy.
- **Stale status prose:** update the readiness test's opening description and current documentation to distinguish accepted working-tree authority from published/active authority.

The accepted current oracle, candidate, approval identity and semantic collections are immutable. Reuse the completed comparison, canonical persistence/reconstruction, reader and source-order evidence where the narrow correction leaves them unaffected. Selector changes invalidate their own resolution proof, not automatically every native persistence or reader proof. Reader-retention residue and supplemental-template integration remain outside this increment.

**Additional concrete selector finding:** the newly introduced superseded-version set check can be bypassed by a string subtype with a different hash. Codex's actual exported-helper reproduction returned the retired `3fe` inputs (raw exit 1). Correct the primitive/canonical identity boundary before final gates; see [the bounded finding and negative-control evidence](codex-selector-refusal-review.md). This is ordinary in-scope implementation correction, not an Owner Decision.

The initial 14-file fixture sweep took 23 minutes 52 seconds. Reuse its failure inventory and accepted native evidence. Use small representative checks during correction, then let the required full default suite cover the complete settled family; do not duplicate whole historical sweeps merely to re-establish the same pre-correction failures.

## Gate sequence and boundaries

Complete edits and formatting, strict selected-test typing and meaningful focused diagnostics first. Codex reviews that settled correction, then runs final local Black, Ruff, production `mypy src/`, selected-test strict mypy, full default pytest with the configured 80% coverage threshold, dependency audit and scoped secrets checks. Focused checks disable coverage and remain diagnostic only.

The real relative secrets hook remains non-green while `.secrets.baseline` is unstaged; a private-copy content pass does not replace it. Do not stage to cure that condition. Preserve baseline settings and existing entries; use immutable-payload byte identity to reuse completed expensive content scans.

The entire restart working tree includes persistence/schema/migration changes. Later exact committed PR-head CI must include all configured jobs, including frontend and E2E; those jobs cannot be described as green now. No automatic local frontend/E2E rerun is required solely for this narrow typing/test/selector correction. Full CI and fresh final-head review follow the Owner's publication authorization.

HEAD, index, stashes, unrelated dirty work and permanent settings remain preserved. No staging, commit, push, merge, publication, activation, shared-state operation or external authority write is authorized by this increment. Distinguish local release-readiness from completion of the whole restart and from published or active authority.
