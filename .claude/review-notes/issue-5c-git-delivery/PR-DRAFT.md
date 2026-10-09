# Deliver the qualified SRD source and accepted restart recording (#132, #137)

The retired SRD corpus and mechanical authority could still shape source selection
and inherited acceptance. This restart isolates those products, qualifies a pinned
community source against the official SRD 5.2.1, constructs cited coherent source
units, and delivers freshly reviewed mechanical authority with native persistence,
reference resolution and reader integration.

The Owner accepted the exact release-order candidate. Its recorded replacement is
`5.2.1-corpus.8781d4e0-a3b`, with 24 accepted batches, 1,835 records,
1,486 reference resolutions, schema 17 and zero native findings. Superseded
`3fe24ff6-4e3` and `574662e9-0ef` releases cannot resolve as current committed
authority; useful historical replay evidence is retained. Current-source tests
compare current inputs, and historical tests replay their matching historical
inputs. Native missing-approval negatives retain exact failure multisets.

The delivery includes corrected source relationships and coverage evidence,
source-order handling, quarantine and retrieval behavior, authoring/acceptance
contracts, the reference-alternatives migration and typed persistence, packaging,
and relevant regressions. Original and additional in-scope test typing errors are
closed without blanket `Any`, new skips or weakened coverage/checkers.

## Authority and Architecture Notes

This implements the [21 September Owner Decision](docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md)
and its reconciled CRD Issue 5c/5d and ADR requirements. The corrected community
source is a machine-readable transformation; the official PDF remains ultimate
rules authority. Old acceptance, identities and geometry are not inherited into
the replacement. The Decision explicitly authorizes those changes from the
superseded specification. Source qualification, semantic acceptance, implementation
capability and runtime activation remain distinct.

No drift from governing design principles. The service and transaction boundaries,
quarantine/refusal behavior, official-source citations, release identities and
native approvals remain explicit. Reader-retention residue and supplemental
template integration are outside this delivery. Dependency-vulnerability repairs
remain Owner-deferred until restart completion; no audit gate is silently waived.

## Validation

- Completed default backend pytest/coverage: **7,397 passed, 141 skipped,
  no failures/errors, 92.48% coverage** against 80%.
- Root Black/Ruff passed. Strict typing passes 235 production files and the
  42-file affected-test union, including fresh checks using current main's mypy
  configuration. Accepted reconstruction/persistence, reader, source-order and
  approval-negative evidence is retained.
- [Final local review](.claude/review-notes/issue-5c-release-readiness/codex-final-readiness.md)
  and [delivery packet](.claude/review-notes/issue-5c-git-delivery/PACKET.md)
  distinguish complete gates, failed historical receipts and outstanding gates.

Before actual PR publication, replace this paragraph with the exact assembled
commit/tree, whole-delivery secrets/hook result and any newly invalidated local
checks. Exact-head backend/frontend/E2E CI and fresh whole-PR Codex review are
required before merge; they are not yet claimed green.

This is a code/artifact delivery. Nothing here authorizes runtime publication,
activation, shared-state writes or a declaration that the restart is complete.
The partial-publication block remains in force. Do not close #137 or change #132's
state automatically.
