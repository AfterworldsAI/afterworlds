# CRD Issue 15c — implementation status

- **Branch and head:** `codex/issue-15c-bounded-d20`. Local commits: `eb60d9f` (implementation), `abca92d` (review notes) and a C2 review-notes commit. Baseline `e83018c` = remote main.
- **Not pushed. No PR.** Stopped at the semantic-acceptance gate for Codex review.
- **Scope:** #191 as updated (body SHA-256 `8225e1b6…57a2`). It adds creature attacks, bounded Multiattack and their saves/effects, the tool-addressing and omitted-source repair, and individual conditional-creature assessment. The G1 oracle `2ccbaeba…1258` is unchanged.
- **Process:** Opus 5.5 at medium effort, with the separate Opus 5.5 Advisor consulted on the approach, the candidate scope and completion.

## Candidate

**C2 is current.** C1 is superseded but preserved; its JSON files are byte-identical.

| Part | SHA-256 | Holds |
| --- | --- | --- |
| C2-A | `a15aab18…` | Rules, weapons, all 25 tools, the stat-block conventions |
| C2-B | `0dd7538f…` | All 336 creature records: per-entry classification, section anchoring, block-level rollup |
| C2-C | `a21a5e89…` | Armor and character AC |

See `candidate-c2/README.md`: concordance, classification, assessed creatures, the schema and addressing delta, transition cost, holds, and the surfaced prerequisite.

**Nothing has been accepted. Native minting has not started** (cost stated: 7 of 24 batches).

## Implementation on `eb60d9f` (unchanged by C2)

See `review-handoff.md`. It covers:

- wiring;
- the manifest and certification;
- typed refusals;
- certified fixed-DC checks;
- player-roll refusal;
- the setup-turn ordering fix;
- prompt v2;
- the ADR and status reconciliations.

Every operation that depends on C2 is `HELD` and refuses visibly. The manifest's "monster stat-block actions" exclusion and its record-only tool wording predate the scope update. They are **superseded by #191 as updated** and are to be revised in the dependent implementation once C2 is accepted. That code was not touched, because candidate work is held.

## Evidence

**Gates passed:**
- Black, Ruff and mypy strict are clean.
- detect-secrets is clean, with documented false positives.
- pip-audit is clean with CI's ignore set.

**Focused diagnostics** are green. These are not acceptance:
- 51 bounded-check tests;
- 54 service and adapter tests;
- 330 orchestrator and API tests;
- 8 E2E tests on G1 published in a disposable store.

**Full `pytest -q` on `eb60d9f`: NO RESULT.**
- The serial run was stopped at the 2-hour background limit before finishing.
- Its log (`gates/pytest-full.log`) holds only buffered progress, about 6%. No pass or fail is recorded.
- Per the dispatch, it was not rerun for candidate-only work.
- Exact-head CI, which has 8 shards, has not run.

**C2 checks:**
- deterministic re-derivation;
- the C1 digests are verified unchanged;
- the two-sided creature census matched 336 of 336;
- the attack count equals the source's 423;
- every A and C fact anchors to an accepted component.

## Open, not yet applied

These are drafts held outside the repo, to be applied after review or a new full run:

- tests for stale-binding and missing-authority messages;
- the setup-turn sheet-skip test;
- a no-settlement-warning assertion;
- a BYOK E2E.

## Exact blockers

1. Codex independent review of C2 (content, classification rule, deltas).
2. A native mint of the reviewed C2, then Owner acceptance of the exact native identity.
3. Surfaced prerequisite: the Vampire Familiar's master relation. The default is to refuse.
4. A full-suite and CI result for the implementation head.
