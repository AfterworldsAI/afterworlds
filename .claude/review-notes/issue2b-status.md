# CRD Issue 2b — implementation status

**State: the implementation is complete for the approved scope and all Codex review findings, including the final identity-domain family. Local static gates and focused checks pass. Full tests, the collection census and the aggregate coverage gate are delegated to the eight-shard CI run on the exact head of the draft PR.**

Branch `codex/issue2b-character-state`, base `c90a690`. The exact head is reported in the PR handoff.

## Delivered

- **G1 successor.** Recorded natively from the real Owner receipt (`dca4af3`).
  - Successor `srd-5-2-1-corpus-8781d4e0-a3b-g1.json`, SHA-256 `2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258`.
  - Proposal `8a8a737b…5345`, oracle `3e7b27db…` and projection `efab27a9…` are unchanged.
  - The prior `def7caa1…` is preserved byte-for-byte and superseded by digest.
  - Codex checked the recording independently. There is no recording blocker.
- **Typed state and services** (`10b621a`, plus the review fixes). Typed state, persistence, bindings, adoption, the shared-change hold, holdings, consumers and retirement. Traceability and Architecture Notes are in `docs/architecture/issue-2b-character-state.md`.
- **Review 1 findings, all resolved:**
  1. Turn-lease owner proof.
  2. Typed selections.
  3. State parameters.
  4. Poison items.
  5. Item operations under the holder's authority, and adoption of held items.
  6. Display reads through the binding and never manufactures conditions.
  7. A closed pure ability-check shape, with every proposal checked before any roll.
- **Lease boundary review.** The deletion proof is held through commit, a starting owner refuses, and concurrent recoverers behave correctly. Defect family: ownership proof separated from the deletion transaction. Sibling dispositions are in commit `e4dee9a`.
- **Review 2 findings, all resolved:**
  - Unleased owner proof files are kept.
  - A party's package context joins the hold.
  - Turn HP and slot effects preserve their other fields.
  - Turn writes check references.
  - Familiar readiness is source-specific.
  - Hazards are a typed family.
- **Final structural identity review.** Weapon, tool and sense grants are now checked against their own identity domains (`8c64c2a`). The family disposition is in that commit and in the Architecture Notes.
- **Advisor items.**
  - The readiness gate.
  - Adoption takes the write lock first.
  - The shared-change trial applies the whole effective set.
  - Summon references are story-scoped.

## Checks on source head `f303e870f11d573000fa0e4d65495d1467ccc23a`

These ran on Windows with the clone's Python 3.12 virtualenv. The status commit on top of this head is docs-only.

- **Static gates.** All pass:
  - Black (check);
  - Ruff;
  - mypy strict (247 files);
  - pip-audit with the CI ignores (no known vulnerabilities);
  - the detect-secrets hook over every file changed since `c90a690` (exit 0, baseline unchanged).
- **Focused tests** (`--no-cov`): 2043 passed, 10 skipped. They cover:
  - `tests/services/dnd5e_state`;
  - `tests/pipeline`, `tests/models`, `tests/api` and `tests/persistence`;
  - the published-SRD state test, `test_oracle_succession` and `test_srd_equipment_catalogue`.
- **Codex probes:** all eight files as written, 17 tests, passed.
- **Frontend.** All pass:
  - `npm ci`, typecheck, ESLint and Prettier;
  - Vitest, 45 passed;
  - `npm audit`;
  - the OpenAPI drift check (no drift);
  - the production build.
- **Not run locally:**
  - the full suite with its census and coverage;
  - E2E, which launches the app; the spine covers Writing and Branching only.

  The draft PR's exact-head CI runs both.

## Exact-head CI on `432a0a6` (run 38130325519) and its remediation

The run failed: frontend and E2E passed, and shards 1–7 had failures. Every failure falls into one of three families. All are remediated with tests and the boundary only; no production module, artifact or recorded hash changed.

**1. Historical schema contract versus the build's current schema.**
- **Root cause.** `issue-5d-reference-alternatives-ACCEPT.py` (byte-pinned at `7a959255…`) lifts to the build's current schema. That schema was 17 when the script was recorded and is 18 now, so the replayed `e9678ab3…` drifted, along with every later recorded prior.
- **Remedy at the replay boundary** (`_replacement_chain`):
  - a written-out per-script registry pins that script's target to schema 17, and the script's own `reviewed()` re-asserts it;
  - the schema-17 checks' release findings are judged at the build's schema, after each registered crossing is proved over the candidate's representation.
- **Siblings patched:**
  - `test_reference_alternatives`: schema 17 is pinned for the historical lift and pre-fix identity, and the current 16→17→18 lift has its own assertion;
  - `test_spell_descriptions_proposal`: an explicit forward lift;
  - `test_character_origins_feats_proposal`: the literal current lift chain;
  - `test_schema_12_practical_reliability`: schema 18 added to its earlier-contract set;
  - `test_committed_accepted_authority`: the G1 proposal `8a8a737b…`, asserted against its reviewed file and against the Owner receipt.
- **Already safe:**
  - every other written-out version registry;
  - the G1 scripts;
  - the shared findings judge, which affects only the four schema-17 checks.

**2. The new table's census.**
- `rp_mech_shared_changes` is added to both closed `rp_*` censuses.
- Its proof policy is `runtime_coordination`, which keeps it outside projection identity and digest.

**3. Fixture transaction isolation.**
- The holdings adoption test now commits its target resolution.
- The seeder now starts cold.
- Proof that the masking is closed: with the commit removed, the whole-file run fails.

**Targeted evidence** (clone venv, `PYTHONDONTWRITEBYTECODE=1`, task-private basetemp):
- The four recording rebuilds, the class-eligibility rebuild and the committed-authority file: 7 passed.
- The 2b suite, both censuses, the proof-policy inventory, schema 12, reference alternatives, the origins-feats composition and the committed authority: 348 passed.
- The cold single node: passed.
- `test_spell_descriptions_proposal`: 22 passed.
- The G1 receipt identity node: passed.
- Static gates pass: Black, Ruff and `mypy src`.
- The secrets scan finds no unaudited findings. The one new audited entry is the G1 identity literal.

The new exact-head CI run is reported in the PR handoff.

## Remaining

- A fully green exact-head CI run on the new head: eight shards, the census, coverage of at least 80%, the frontend gates and E2E.
- Codex's independent review of the draft PR.
- No merge, runtime publication or activation, app launch, CRD Issue 15c work, or #132/#137 changes.

## Advisor contribution

- The hold design: a lease plus activation that takes the write lock first.
- Adoption semantics: held, revalidated fresh, no substitution.
- The readiness gate.
- For review 1:
  - Leases: liveness proved per owner with an OS lock.
  - Selections: one typed selection union, reused for effect parameters.
  - HP: no reduced-maximum bound.
  - Adapter: every proposal validated before any dice.
  - The OOC path stays binding-enforcing.
