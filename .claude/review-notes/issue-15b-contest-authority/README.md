# CRD Issue 15b — contest authority and contract amendment (review packet)

**Status.** This is a proposed PR for Codex review and then the Owner's whole-PR acceptance or rejection. Each of the following is a separate step:

| Step | Status |
| --- | --- |
| Policy and source adoption | **done** by the Owner (`docs/decisions/owner-decision-2026-10-14-contest-supplement.md`) |
| Exact native semantic acceptance of S1 and the C9 packet | **given** 2026-10-14, with this PR (`../issue-15b-c9-recording/owner-acceptance-2026-10-14.md`) |
| Acceptance of this PR | **given** 2026-10-14 at `5d05f473`, including the combat Action cost; CI run `38555377777` green |
| Recording | C9 recorded in the next 15b PR (`../issue-15b-c9-recording/`) |
| Publication, S1 activation, #129 resume | not done; separately gated |

**Out of scope here:**
- PR #129 stays frozen at `d8233a43`.
- No RPG resolver, #129 integration, Phase 3 route or UI is included.
- Graphify could not be refreshed: `.local-tools/` is absent from this worktree.

| Branch | Head | Role |
| --- | --- | --- |
| `codex/issue-15b-contest-authority` | this branch, based on main `c9de00f5` | **the proposed PR**: documentation, review notes and `.secrets.baseline` only. No `src`, `tests` or migrations |
| `codex/issue-15b-c9-schema-preview` | `002de94d` (worktree `../c9-schema-preview`) | **local preview only, not part of the PR**: the schema-22 code and tests, and the C9 native SIMULATED packet. It shows why schema 22 lands only with a recorded C9 successor |

## Contents

| Part | Path | What it is |
| --- | --- | --- |
| Owner policy record | `docs/decisions/owner-decision-2026-10-14-contest-supplement.md` | the adopted SRD 5.1 contest procedure, with source pin, receipt digest and boundaries |
| Contract | `docs/decisions/adr-015b-structured-rpg-roll-lifecycle.md`, Group 17 (15b-37, proposed) plus status notes | participants, authority, the qualified creature-skill pairing, timing, representation, tie, consequences, **combat action accounting**, **hidden-counterpart projection**, proof, **ordered gates**, ownership. AC8's text is unchanged |
| 15b-36 pointers | same ADR, Group 12, Revised PendingRollRequest, Consequences | recorded Owner Decision 15b-36 (empty-table cutover, fail before destruction) governs over the older nullable-preservation text. No migration change |
| Forward references | `docs/architecture/issue-15c-bounded-d20.md`, `docs/architecture/known_unknowns.md` | 15c's contest exclusion and the "contests untouched" representation group stay as history. Combat accounting and the one open policy are recorded |
| S1 supplement candidate | `supplement-s1/` | the exact SRD 5.1 excerpt, as one deterministic `package_patch` override appending `play.d20_tests/contest`. Validated against the pinned PDF and, in memory, against accepted C8 |
| C9 raw candidate (r2) | `candidate-c9/` | 336 `creature_skills` facts: printed totals for the usual ability pairing, and 120 positively empty lists. Includes the completeness proof and the schema-22 delta |
| C9 native packet | preview branch `.claude/review-notes/issue-15b-c9-native/` | SIMULATED native preview, its proofs and the verifier defect note |

## Identities

| Item | Identity |
| --- | --- |
| Accepted C8 successor (read only) | `ead7fa9d…2d0d`; projection `e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42` (= `CERTIFIED_RELEASE`) |
| SRD 5.1 PDF | `2504d2a0abb0a4d491a939be4f17910a2dde0312570ab8d208080225ccf0a1f0` |
| S1 `s1.json` | `c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a`; override `b9134dea-52c3-546a-b13c-795fe16bfe90`; component schema id `802ea03805060bb6d590a1d5a2d7343d4e6c672e8fe4659b2b5aaaf7cbd54ccb` |
| S1 `validation.json` | `22bd4d12…0b66` (28 of 28) |
| C9 r2 `c9.json` | `a3d40545d1a0ea1b4a1e24a1e3831b12b972f50ea26981b0edf1b578fd0648db`; correspondence `285ee055…f1e4`; inventory `daab6ac2…3d9b` |
| C9 r2 `validation.json` | `ce47394016eb69626cdce325b596b6165e56c8791bf361668a93fb3dc0ad9532` (19 of 19) |
| Schema 22 (preview) | `b073cd4f429631826efd628ed164a5ad680050c7e957e74680777922affb414f`; lift `5d-lift-schema-21-to-22` |
| C9 native preview oracle | `3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3`; oracle identity `924321df…ab0c`; projection `3703faf5-8b51-5c3f-b28c-b378b005f7bf`; payload `c7a52d55…2f` |
| C9 native packet report | `c9-packet.json` `d61ed1b435e539da7127373d387d2124167581b9df9b5fcc9afb146049e096d4` |

The C9 proposal identities, the input digests and the per-revision evidence are in the native packet README.

## Native evidence

Each revision is reported separately:

| Revision | Run | Result |
| --- | --- | --- |
| `2121a50e` | construction, Codex-supervised | built twice byte-identically; exit 1 in the malformed-input verifier |
| `31810c08` | `--verify-existing`, 714 s, Codex-supervised | every native and sequencing proof passed; exit 1 on one conservation boolean |
| `002de94d` | `--finish-report`, 43 s | the corrected preservation proof, with counterexample and negative controls, passes; native and sequencing results are carried under source-segment identity guards |

The two failures came from one defect family: proof code assumed construction fact order where the assembled order is canonical. The preview's `verifier-defect-note.md` records both rounds and their dispositions. Neither the construction nor the 714-second native block was repeated.

## Decisions for review

1. **The supplement uses the existing ADR-005d override mechanism**, not a new store, a `src` constant, or an SRD 5.2.1 fact.
   - The origin is `package_patch`, which is documented as an "administrative correction". This is disclosed; no new origin was minted.
2. **One `creature_skills` fact goes on each profile, holding the complete printed list.**
   - Empty means "prints no Skills entry"; a missing fact means missing authority.
   - Each total is bound to its usual ability (r2). An atypical pairing of a listed skill refuses before rolling. That is a bounded adapter exclusion, not a source prohibition.
3. **Schema 22 stays off the PR branch.** The preview's sequencing proof shows why:
   - main still selects C8, and every executable 15c operation certifies;
   - the preview projection is not `CERTIFIED_RELEASE`, so certification there refuses.

   The schema lands with the recorded C9 successor and recertification, as C8's did.
4. **Gates, in order:**
   - exact native acceptance and the #129 gate come before dependent lifecycle work;
   - recording, schema 22 and recertification form the authority landing gate;
   - S1 activation and publication are a later operational gate, not a prerequisite for writing or proving dependent code.

## Owner Decision proposed for whole-PR review (not implemented)

- **Contest action cost in an active turn.** The source says efforts "typically" take an action.
  - Proposed: v1 always charges the initiator's one action in an active turn, and refuses a GameMaster-declared costless contest.
  - Already source-backed: an off-turn initiation, or a Bonus Action, Reaction or free effort, refuses; with no active turn, nothing is recorded.

## Surfaced, not changed

- Admitted 15c check operations record no action use in an active turn (`economy.costs`).
- The GameMaster prompt contract must route Hide, Influence, Grapple and Shove to their own operations. That is Phase 2 prompt work.

## Gates and checks run

| Branch | Check | Result |
| --- | --- | --- |
| PR branch | `src`/`tests` diff against `c9de00f5` | none |
| PR branch | `black --check src tests`, `ruff check src tests`, `mypy src/` (268 files) | clean; no code has changed since |
| PR branch | review scripts (black, ruff) | clean |
| PR branch | S1 / C9 validators | 28 of 28 / 19 of 19, deterministic |
| PR branch | detect-secrets hook | passes on every commit, with narrow baseline entries for candidate JSON digests |
| Preview branch | black, ruff, `mypy src/` | clean |
| Preview branch | focused schema tests | 3,630 passed and 1 failed (a contract string containing the class name `Skill`). After the one-word fix, the affected 1,417 passed. Labelled FOCUSED DIAGNOSTICS ONLY; not a full-gate result |
| Preview branch | native packet | as above |

**Not run.** pytest full suite and pip-audit on the PR branch: there is no code or dependency change. The preview branch's full suite was not run either. Its `test_bounded_d20_on_published_release.py` and `test_bounded_checks.py` were not run on the preview, which is expected to be incompatible until recording; the native sequencing proof covers that boundary instead. Final exact-head CI belongs to Codex.

## Not done (held)

- Owner acceptance of S1, the C9 packet and the PR.
- Recording.
- Schema 22 on main.
- Recertification.
- S1 activation.
- The contest operation and lifecycle (15b Phase 2).
- The public API (Phase 3).
- Any push, PR, merge or shared-runtime operation.
