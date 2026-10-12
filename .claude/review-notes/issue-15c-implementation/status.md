# CRD Issue 15c — implementation status

- **Branch and head:** `codex/issue-15c-bounded-d20`, local commit `eb60d9f` on baseline `e83018c` (also remote main).
- **Not pushed.** There is no PR. Stopped for Codex independent review.
- **Scope:** #191 as posted (draft SHA-256 `e7dfbcbd…b3d5`). The G1 oracle `2ccbaeba…1258` is unchanged.
- **Orientation:** Graphify was refreshed and queried. The Advisor was consulted on the approach and on the scope of the candidate.

## Accepted scope and what is held

All 38 weapons, all 8 masteries and the bounded zero-HP lifecycle stay in the manifest. They are `HELD` on semantic candidate C1 and refuse visibly. The approved scope is not shrunk.

| Part | SHA-256 | Holds |
| --- | --- | --- |
| C1-A | `9e9645e8…` | Rules, weapons, masteries, the zero-HP lifecycle, initiative, tools, difficulty checks |
| C1-B | `fbabf91a…` | Creature targets |
| C1-C | `82cfb6b9…` | Character AC and armor |

## Changed surfaces

See `review-handoff.md`. In summary:

- wiring;
- manifest and certification;
- refusal taxonomy;
- the fixed-DC check executor;
- player-roll refusal;
- the setup-turn resolution order;
- prompt v2;
- the ADR and status reconciliations.

## Acceptance coverage

| AC | State |
| --- | --- |
| AC1, AC2, AC3 | Met for the executable scope |
| AC5 | Met for the executable scope |
| AC4 | Partial: checks are covered; everything else is held on C1 |
| AC6 | Single-subject only; multi-subject held |
| AC7 | Partial: E2E covers checks and failure paths; held operations await C1 |

## Commands and evidence

| Check | Result |
| --- | --- |
| Black, Ruff, mypy strict | Clean |
| detect-secrets | Clean, with documented false positives |
| pip-audit (CI ignore set) | Clean |
| Focused diagnostics | Green (see the handoff) |
| Full `pytest -q` | Running on `eb60d9f`; output in `gates/pytest-full.log` |
| Exact-head CI | Not run; needs a push after review |

## Exact blockers

1. Codex independent review of C1 and of the classification rule, then explicit Owner semantic acceptance of C1-A, C1-B and C1-C. Each part unblocks the work it holds.
2. A process choice for Codex and the Owner: does the Owner accept the content before native minting, or the minted identity after it?
3. Codex review of this branch before any push or PR.
