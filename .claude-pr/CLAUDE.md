# CLAUDE.md — PR Review Overlay

Read the repository-root `/CLAUDE.md` first. It is the authoritative standing implementation guidance. This file adds only PR-review/remediation behavior and must not duplicate or contradict the root file.

## PR Review Posture

Treat Codex/reviewer comments as symptoms. Classify the underlying defect family before changing the quoted line. Preserve the governing CRD issue, accepted ADRs, architecture invariants, and issue scope.

For each actionable finding, determine whether it is:

- an issue-scoped implementation defect;
- a specification/documentation correction;
- a scope or ownership boundary problem;
- a Known Unknown;
- an Owner Decision;
- a non-blocking improvement.

Do not turn ordinary engineering choices into Owner Decisions. Do not silently fix out-of-scope or deferred behavior.

## Review-Loop Boundary Check

When repeated review rounds hit the same file/function/query/schema/service hotspot or the same defect family, or feedback shifts from concrete correctness into ownership, semantics, placement, or architecture:

1. Stop treating the newest comment as automatically the next patch.
2. Classify the remaining defect family and boundary.
3. Run a bounded sibling audit only when recurrence indicates that the defect may exist in parallel structures.
4. Fix the in-scope defect class once, not each symptom independently.
5. Surface scope, Known Unknown, or Owner Decision residue in PR comments or Architecture Notes before further remediation.

A sibling audit is diagnostic, not a license to broaden the PR. Inspect representative siblings only until the issue is confidently isolated or systemic; stop when more searching is unlikely to change the remedy.

## Claude/Opus 5.5 Remediation Guidance

Keep remediation prompts lean: outcome, authority, verified symptom, defect class, scope/non-goals, and observable proof. Let Claude choose ordinary investigation order, file/helper structure, and test organization from repository reality.

Use subagents by task topology. Parallelize genuinely independent, sizeable tracks when doing so improves wall-clock time or context quality; do not spawn an agent merely to repeat the lead agent's verification.

For unattended multi-part remediation, do not treat a text-only status/end turn as proof of completion. Completion means the requested findings are resolved and the stated evidence/gates are satisfied, or a real blocker is reported. Bound any automatic continuation rather than looping indefinitely.

Do not request private chain-of-thought. Use test evidence, diffs, concise reasoning summaries, and reviewer-visible facts.

Do not add a permanent lesson, checklist, gate, or process rule simply because one PR exposed one defect. Recommend durable process guidance only when recurrence shows the defect class is systemic and a process rule is cheaper than code or architecture prevention.

## PR Completion Evidence

Before requesting or re-requesting review, provide only the evidence relevant to the PR:

- what changed and which finding/acceptance obligation it closes;
- targeted regression and boundary/fail-closed coverage where applicable;
- applicable local/CI gate results on the exact head;
- Architecture Notes stating `No drift from design principles` or the explicit accepted deviation;
- any remaining scope, Known Unknown, or Owner Decision residue.

Do not create review diaries, invariant cards, mandatory advisor checkpoints, fixed test-count quotas, or phase-by-phase ceremony unless the governing issue/ADR explicitly requires them.

## Repository Rules

The root `/CLAUDE.md` governs branch, CI, Codex-review, architecture, business, naming, and tooling rules. In particular:

- no direct commits to `main`;
- no merge with failing CI or unresolved required review;
- use `CRD Issue N` for construction issues and `#N` for GitHub issues/PRs;
- `AGENTS.md` is reviewer-facing guidance, not ordinary implementer startup context.
