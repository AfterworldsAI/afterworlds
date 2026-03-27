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
