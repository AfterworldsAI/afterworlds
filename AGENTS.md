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

## Boundary-over-patch rule

Agents must distinguish between:
- a concrete defect that should be fixed in the current PR, and
- a boundary problem indicating that the PR has drifted beyond issue scope or reached an unresolved ownership decision.

Trigger this check when:
- the same PR receives repeated review/fix/re-review cycles,
- the same file or function is revised across multiple review rounds,
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

## Comment labeling

- Prefix any comment that requires a design, architectural, ethical, policy, or ownership judgment with `[OWNER DECISION]:` at the start of that comment.
- If a review thread appears to have crossed from defect-fixing into boundary or ownership dispute, label the relevant comment with `[OWNER DECISION]:` rather than presenting it as an ordinary fix request.
