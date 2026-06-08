# AGENTS.md

## Review guidelines

- Review as Codex reviewer, not primary implementer.
- Flag issues in correctness, security, maintainability, test coverage, and architecture drift.
- Check changes against `/docs/architecture/construction_readiness.md` and `/docs/architecture/design.md`.
- Enforce separation of Story Bible from prose history.
- Enforce stable-prefix-once-per-turn prompt assembly rule.
- Enforce that Extractor proposes canon updates and does not write canon directly.
- Enforce that no PR merges with failing CI.
- Prefer high-signal comments over nitpicks.
- Call out missing tests when acceptance criteria mention tests.

## Graphify Review Preflight

Before reviewing a non-trivial PR, consult Graphify for codebase orientation when it is available in the local environment.

Graphify is a construction/review aid only. It is not an Afterworlds runtime dependency, not an architectural authority, and not a replacement for the PR diff, issue spec, ADRs, `AGENTS.md`, `CLAUDE.md`, or architecture docs.

Required review preflight:

1. Read `AGENTS.md` and the PR diff first.
2. Query Graphify before broad manual spelunking.
3. Use narrow, review-specific queries to identify changed-file impact, ownership boundaries, downstream callers, related tests, and architecture seams.
4. Verify all Graphify output against source, tests, issue specs, and architecture docs before writing review findings.
5. 5. If Graphify is blocked by the sandbox, request approval/escalation to run the Graphify preflight once. If Graphify is still unavailable, stale, or failing after that, state it explicitly and continue with normal source inspection.

Current local code-only Graphify workflow:

```powershell
cd D:\AI\Claude\afterworlds\src
graphify query "Summarize the files, services, models, tests, and ownership seams relevant to this PR."
```

## Boundary-over-patch rule

Agents must distinguish between:
- a concrete defect that should be fixed in the current PR, and
- a boundary problem indicating that the PR has drifted beyond issue scope or reached an unresolved ownership decision.

Trigger this check when:
- the same PR receives repeated review/fix/re-review cycles,
- the same file, function, query path, schema hotspot, or service hotspot is revised across multiple review rounds,
- review feedback shifts from correctness defects to questions of semantics, ownership, architectural placement, or where behavior belongs,
- a proposed fix would move behavior into an issue that does not clearly own it.

When triggered:
1. Stop treating the latest review comment as automatically “the next patch.”
2. Classify the remaining feedback as:
   - merge-blocking defect,
   - scope/boundary problem,
   - Known Unknown,
   - non-blocking improvement.
3. Surface the boundary problem explicitly in the PR.
4. Require Architecture Notes to describe the boundary problem before further implementation continues.
5. Defer implementation until the owner decides whether to narrow the PR, defer behavior, or define the missing ownership rule.

Repeated review churn on one hotspot is a coordination signal, not just a coding task.

## Hotspot audit rule

If a PR has already gone through two or more review rounds on the same hotspot, do not keep issuing isolated patch comments indefinitely.

Instead:
1. Treat the hotspot as a defect family, not as unrelated one-off comments.
2. Ask whether the implementation has addressed the whole defect class or only the latest symptom.
3. Prefer one bundled hotspot audit over a long sequence of micro-fix comments.
4. Evaluate likely sibling defects in the same area, including:
   - nondeterministic selection or ordering,
   - missing tie-breakers on precedence-based queries,
   - package/scope/isolation leaks across related tables or services,
   - missing integrity constraints for cross-table references,
   - play-time reads that may behave inconsistently across equivalent inputs.
5. If the remaining work is still concrete and in scope, request that the hotspot be fixed as a bundled pass.
6. If the remaining work is no longer clearly concrete and in scope, switch to `[OWNER DECISION]:` handling instead of continuing the patch loop.

The goal is to prevent infinite review churn on one hotspot while still catching real sibling defects in the same defect family.

## Comment labeling

- Prefix any comment that requires a design, architectural, ethical, policy, or ownership judgment with `[OWNER DECISION]:` at the start of that comment.
- If a review thread appears to have crossed from defect-fixing into boundary or ownership dispute, label the relevant comment with `[OWNER DECISION]:` rather than presenting it as an ordinary fix request.
- If repeated comments on the same hotspot suggest a bundled hotspot audit is needed, say so explicitly rather than continuing to drip-feed one new patch comment per review round.
