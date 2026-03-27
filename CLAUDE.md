# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.
Read it fully at the start of every session before taking any action.

## Project

Afterworlds is an interactive storytelling platform built on the Sojourn Story
State Machine. It lets users inhabit and continue narrative worlds across three
modes: RPG, Branching, and Writing. The target users are called Sojourners.
This is a solo-developer project operated under AfterworldsAI, LLC.

The authoritative design documents are in /docs/architecture/. Read them before
making any architectural decision. If your implementation would deviate from
anything in those documents, flag it in your PR description — do not resolve it
silently.

## Language & Tooling

- **Language:** Python 3.12 only
- **Package management:** pip + virtualenv only — do not introduce Poetry, PDM,
  uv, or any alternative dependency manager
- **Testing:** pytest (minimum 80% coverage on new code)
- **Type checking:** mypy strict mode — zero tolerance
- **Formatting:** Black — zero tolerance
- **Linting:** Ruff — zero tolerance
- **Dependency scanning:** pip-audit (blocking CI gate)
- **Secret scanning:** detect-secrets (pre-commit hook)

## Build & Test Commands
```bash
# Create and activate virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/

# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Dependency audit
pip-audit
```

## Architecture Principles — Non-Negotiable

These must not be violated. Any code that breaks them is an architectural
violation and must be flagged in the PR, not silently resolved.

1. Story Bible is structurally separate from prose history
2. Six memory layers have distinct roles: Immediate / Rolling Summary /
   Story Bible / Rules Package / Retrieval Memory / Contradiction Checker
3. Intent is classified before context is assembled
4. Pipeline is staged: Planner → Writer → Extractor → Contradiction → Safety
5. Extractor proposes canon updates — it does not write canon directly
6. Stable prompt prefix is assembled once per turn and shared across all
   passes for caching efficiency

## Repository & PR Rules

- Feature branches per issue: `feature/issue-N-short-description`
- No direct commits to main under any circumstances
- Open a PR for every issue; PRs are not merged without Codex review passing
- No PR merges with failing CI
- Every PR description must include an **Architecture Notes** section:
  either "No drift from design principles" or an explicit description of
  any deviation and rationale
- Scope creep is a review failure — stay within issue boundaries

## Commit Format

Conventional commits:
`type(scope): description`
Types: feat, fix, refactor, test, docs, chore
Example: `feat(story-bible): implement tiered inclusion policy for events ledger`

## Known Unknowns — Do Not Resolve Silently

These are open decisions. If you encounter them, flag and pause — do not
make a load-bearing choice without explicit approval:

- React vs. Svelte for the frontend (resolve before Issue 19)
- Exact ChromaDB collection schema (resolve before Issue 18)
- Exact FastAPI route shapes (resolve before Issue 18)
- Rolling summary compression trigger N value (start at 10, tune with testing)
- Events Ledger tiered inclusion N value (start at 15, tune with testing)

## Business Model Constraints — Architectural Invariants

- Free tier turn cap: 50/month — enforced at API layer, not UI
- Free tier pipeline: lightweight Planner + Writer + lightweight Contradiction
  + Safety only — never the full five-pass pipeline
- Paid tier: full five-pass pipeline
- BYOK is a first-class path — all features must work identically under BYOK
- Extended TTL caching must be enabled by default wherever provider supports it
- Free tier must preserve basic continuity dignity — silent continuity failure
  is not acceptable at any tier