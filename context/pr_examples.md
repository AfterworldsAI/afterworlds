# PR Examples — What Good Looks Like

**Purpose:** This file teaches Claude Code what a well-scoped, well-documented
PR looks like for the Afterworlds project. Use it as a reference when writing
PR descriptions and when evaluating whether a PR is ready to submit for
Codex review.

**When to use:** Before opening any PR; when writing the Architecture Notes
section; when assessing whether scope has crept beyond issue boundaries.

---

## What Makes a PR Good

- **Scope matches issue exactly.** Nothing in, nothing out.
- **Every acceptance criterion is addressed explicitly.** Not implied — named.
- **Architecture Notes is never blank.** Either confirms no drift, or describes
  it with rationale and a resolution path.
- **Test summary is specific.** States what was tested and what was not,
  not just "tests pass."
- **Out-of-scope items are named and deferred.** Shows awareness of boundaries,
  not just compliance.

---

## Example 1 — Issue 1: Repo Skeleton

*This is the first merged PR in the Afterworlds repository, reviewed and
approved by Codex. Use it as the baseline pattern for all subsequent PRs.*

---

**PR Title:** `chore(repo): establish project skeleton, CI scaffold, and tooling`

**Branch:** `feature/issue-1-repo-skeleton`

---

### What Was Built

Established the complete project skeleton per Issue 1 scope:

- Directory structure: `src/`, `tests/`, `docs/architecture/`, `docs/prompts/`,
  `docs/decisions/`, `context/`
- `pyproject.toml` with Black, Ruff, mypy (strict), pytest, pip-audit
  configured to project spec
- GitHub Actions CI pipeline: format → lint → type check → test → pip-audit,
  all blocking
- Branch protection rules on `main`: direct commits rejected, CI must pass,
  PR required
- PR template with Architecture Notes section
- `detect-secrets` pre-commit hook, baseline committed
- Trivial smoke test confirming pytest runs on empty suite
- `CLAUDE.md` at repo root

---

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| CI passes on a trivial commit | ✅ Confirmed — green on first push |
| Direct commits to main are rejected | ✅ Branch protection active, tested |
| PR template appears on all new PRs | ✅ Template in `.github/PULL_REQUEST_TEMPLATE.md` |

---

### Test Summary

- Trivial smoke test (`tests/test_smoke.py`) confirms pytest harness runs
- No application logic tests — none in scope for Issue 1
- CI pipeline confirmed passing end-to-end on this PR itself

---

### Out of Scope (Explicitly Deferred)

- Application models — Issue 2
- Story Bible schema — Issue 4
- Any routes or services — Issue 3+
- Context seed files — added separately outside issue scope

---

### Architecture Notes

No drift from design principles. This issue contains no application logic.
Tooling choices (Black, Ruff, mypy strict, pytest, pip-audit, detect-secrets)
match the CI gates defined in the Construction Readiness Document, "CI Gates as Quality Handoff Contract" section, exactly.

---

## What to Watch For (Anti-Patterns)

**Vague architecture notes:**
> "No issues found."

This tells Codex nothing. If there's genuinely no drift, say so explicitly:
> "No drift from design principles. This PR contains only [X] and does not
> touch any of the six non-negotiable architecture principles."

**Scope creep disguised as helpfulness:**
> "While implementing the models I also added the CRUD routes since they were
> trivial."

Routes are Issue 3. Adding them in Issue 2 means Codex is reviewing untested,
out-of-spec code. Scope creep is a review failure regardless of quality.

**Acceptance criteria addressed implicitly:**
> "All tests pass."

Name each criterion from the issue and confirm it individually. "Tests pass"
does not confirm that the tiered inclusion policy works correctly or that
partition isolation is enforced.

**Architecture Notes missing entirely:**
The section must be present in every PR. A missing section is itself a
review failure — it signals that architectural awareness was not applied
during implementation.

---

## Lessons

<!-- Claude Code appends dated one-line lessons here as they are learned -->
