# CRD Issue 2b — implementation status

**State: implementation in progress after Owner acceptance of G1. Not review-ready.**

## Blocker on the user: native G1 recording (do not route around)

The Owner accepted G1 proposal `8a8a737b0d1e47410de86bbeca44b66522b46511e078727d20760678943b5345`. The receipt is at `../authority/G1-OWNER-ACCEPTED-2026-10-11.md`, SHA-256 `14fe1da9…f780`.

Claude's attempt to write the Owner-acceptance receipt into the repository, the first step of native recording, was **denied by the session's permission classifier**. Claude will not pursue that outcome by another route. Recording, therefore, is a user step. That step can be authorizing it, for example with a permission rule allowing it, or performing it. It consists of:

1. Write `.claude/review-notes/issue-2b-g1-recording/` with the verbatim Owner receipt and a structured receipt.
2. Natively replay `issue-2b-g1-candidate/scripts/build_candidate.py`'s construction, which excises the Equipment batch and runs native `accept_proposal` of proposal `8a8a737b…`. Use reviewer `Ravenlok (Owner)` and a rule quoting the Owner's statement and the pinned hashes, in place of the SIMULATION evidence.
3. Write the result once as `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-g1.json` (new file; the prior `def7caa1…` stays byte-for-byte).
4. Prove the result differs from preview `bfd0d371…` only in `reviewer`, `accepted_at` and `rule`. Proposal identity `8a8a737b…`, oracle identity `3e7b27db…` and projection `efab27a9…` must be unchanged.
5. Add `def7caa1…` to `oracle.SUPERSEDED_ORACLE_SHA256`, exclude the prior from the wheel/sdist (`pyproject.toml`, `MANIFEST.in`), and update the oracles README and ADR-005d (schema 18).
6. Re-baseline the committed-oracle tests.

Until this lands, the following fail on this branch: the committed-oracle tests, production publication (the schema-17 prior is refused under the schema-18 build), the "all twelve resolve" 2b tests and therefore the full gates. The PR cannot be review-ready before it.

## Plan (Advisor-reviewed) and progress

1. [ ] Typed state, vocabularies, compare-and-swap revision, migration 0038 (empty-store only).
2. [ ] Exact binding on state rows, history, adoption.
3. [ ] Shared-change hold and in-flight markers.
4. [ ] Creatures, party, item instances.
5. [ ] Consumers (adapter refusal, sheet effects without HP floor, visible state, orchestrator binding check) and retirement of the old sheet.
6. [ ] Gates.

Checkpoint evidence (G1 candidate, 894 focused tests, typing/lint) is in `issue-2b-g1-candidate/README.md`.
