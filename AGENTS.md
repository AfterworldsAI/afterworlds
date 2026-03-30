# AGENTS.md

## Review guidelines

- Review as Codex reviewer, not primary implementer.
- Flag issues in correctness, security, maintainability, test coverage, and architecture drift.
- Check changes against /docs/architecture/construction_readiness.md and /docs/architecture/design.md.
- Enforce separation of Story Bible from prose history.
- Enforce stable-prefix-once-per-turn prompt assembly rule.
- Enforce that Extractor proposes canon updates and does not write canon directly.
- Enforce that no PR merges with failing CI.
- Prefer high-signal comments over nitpicks.
- Call out missing tests when acceptance criteria mention tests.

## Comment labeling
- Prefix any comment that requires a design, architectural, ethical, or policy
  judgment with `[OWNER DECISION]:` at the start of that comment.

## Auto-fix trigger
- After posting any review that requests changes, post a follow-up comment with
  exactly this text:
  `@claude fix the concrete issues in this review. Skip any comment prefixed with [OWNER DECISION].`
