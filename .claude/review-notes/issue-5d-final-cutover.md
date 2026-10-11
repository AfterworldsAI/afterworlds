# CRD Issue 5d — final cutover (evidence, 10 October 2026)

**Current status (10 October 2026 UTC): merged and verified against the actual runtime.**
- **Merged:** PR #182, `2026-10-10T23:24:27Z`, at `47b80c0ba2eccd2d3bcc1985bca771ede4446574`, tree
  `1abd7888…`, identical to the reviewed head `75b540e`.
- **CI:** all 11 required jobs passed in run 38079785975: 7,300 passed, 17 skipped, 94.146% coverage.
- **Runtime:** migration `0037` and the production consumer were verified against
  `D:\AI\Claude\afterworlds-runtime`; Codex's independent review passed. See the
  [runtime cutover record](issue-5d-runtime-cutover.md).

- **Completion:** on 10 October 2026 the Owner declared "The 5c/5d restart is complete." The declaration is recorded in the
  runtime cutover record.

The sections below record the implementation and its pre-merge review evidence as they stood. This
note makes no issue-state change. Current restart status is in the
[restart opening](../../docs/architecture/issue-5c-5d-clean-restart.md).

## Authority

- **Owner request:** "Let's prepare the bounded final 5d cutover PR for those two blockers."
- **Blockers:** the two P1 findings of Codex's completion assessment, confirmed by the
  [runtime smoke](issue-5c-5d-runtime-smoke.md).
- **Governing text:** #137 contract 6 ([draft](../../docs/architecture/issue-5d-practical-reliability-draft.md)
  lines 443-454 and 510-552), AC16, AC18, AC19, AC21, AC22 and AC25, ADR-005d Decisions 9–11, and the
  [21 September decision](../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md).
- **Classification:** settled, issue-scoped implementation. No new Owner Decision; no Known Unknown touched.

## Blocker 1 — the production consumer reads exact typed authority

**Before** (merged main `71c77b2`, as observed by the smoke):
- `ContextBuilderService` forwarded only the package, `subsystem_tags`, `entity_refs` and
  `include_non_published`.
- `get_active_rule_slice` read legacy chunks and `MechanicalEntity` rows.
- `ActiveRuleSlice` carried no binding.

**Now:**
- **The request goes whole.** `ContextBuilderService` passes the supplying `RuleSliceRequest` whole to
  `RulesPackageService.get_active_rule_slice(request)`.
- **Resolution is typed.** The service resolves the request through
  `RulesAuthorityService.gamemaster_view`, a single resolution covering both the binding and the
  narrowed authority. Its GameMaster view keeps the catalogue and source/authored reading order from
  the 24 and 27 September amendments.
- **The slice carries its provenance.** `ActiveRuleSlice` now holds:
  - `binding`, the exact four-part binding;
  - `request`, the unchanged supplying request;
  - `components`, the `(record, component)` pairs read;
  - `authority_text`, from the new `render_gamemaster_view`.
- **The prompt uses that text.** The deterministic rendering states the binding, then exact source or
  authored prose with provenance, an absent-passage marker rather than any substitute, typed facts,
  qualifiers, options and ordered applied overrides. The stable prefix renders it verbatim.
- **The model layer stays separate.** Typed views are not held on the model, because `models/__init__`
  loads `models.context` and the model layer cannot import the service layer. A consumer that needs
  typed facts re-reads them with `binding` as `recorded_binding`, and that read doubles as its stale
  check.
- **Refusals fail closed.** Every non-`RESOLVED` outcome raises `RuleSliceResolutionError` carrying its
  outcome (`STALE`, `INVALID_REFERENCE`, `UNPUBLISHED`, `AMBIGUOUS`, `ABSENT`, `INVALID_SELECTOR`,
  `INVALID_OVERRIDE`).
- **Retired identities are refused at the entry.** The request UUID and every recorded-binding
  identity are checked there, so a retired package reads as quarantined rather than absent.
- **Removed:**
  - the legacy selectors (`subsystem_tags`, `entity_refs`, `include_non_published`);
  - `resolve_slice_package`, the UUID-passthrough path;
  - unknown request fields are refused (`extra="forbid"`) rather than silently dropped.
- **Retention is committed.** Binding resolution retains its override-set version in the context
  session, and `_PerTurnContextBuilder` commits it after assembly so the named binding replays.
  Context assembly runs before the orchestrator opens the turn's outer transaction.
- **No gameplay selector policy was added.** The orchestrator still builds no request; selector policy
  is 15c's.

## Blocker 2 — the legacy authority is retired

**Removed:**
- `MechanicalEntity`, `SpellEntity`, `ConditionEntity`, `StatBlockEntity`, `ActionEntity`, `ItemEntity`,
  `EntityData`;
- the legacy `RuleOverride`, `ChunkOverridePayload`, `AppliedChunk` and `AppliedEntity`;
- `MechanicalEntityORM`, `RuleOverrideORM` and `MechanicalEntityTypeEnum`;
- `SRDParser.parse_entities` and `ParsedEntity`; an `entities` key is now refused whenever present,
  even as an empty array, rather than ignored;
- `IngestionService._persist_entities` and the entity counts;
- the `RulesPackageService` entity and override readers and the legacy chunk-override application;
- the unused legacy `overrides` parameter threaded through the RPG adapter and service. This is
  dependency reconciliation only; no 15b or 15c mechanics changed.

**Retained:**
- `RuleSource`, `RuleChunk`, `RulesPackage` and the manifest;
- chunk ingestion, the vector writer and publication;
- `get_package_by_id` and `get_chunks_by_subsystem`, now documented as informational source reads;
- the typed override service, its exact target operations, its precedence, and retained, immutable
  replay;
- every quarantine guard.

**Migration `0037`:**
- **Upgrade** drops `rp_overrides`, then `rp_mechanical_entities`, the order the foreign key requires.
  Under the clean-baseline policy their rows are deleted and never mapped.
- **Downgrade** recreates both tables exactly as 0003 defined them, empty. The rows are not restorable.
- Historical migrations are unchanged.
- ADR-0007, ADR-0008 and ADR-0010 carry short supersession banners. ADR-0010 Decision 3 names the
  removed selectors. The banners were written before Codex's first review limited status edits to
  the restart opening, so they are offered for Codex to keep or drop.

## Verification at pre-merge review (native, isolated checkout)

| Check | Result |
|---|---|
| Production consumer (`test_rule_slice_consumer_cutover.py`) | 14 passed. Record, component and whole-package selection; binding on each slice; slug equals UUID; consistency with `RulesAuthorityService` for the same request; refusals for `STALE`, `INVALID_REFERENCE`, `UNPUBLISHED`, `AMBIGUOUS` and quarantine (including a recorded binding naming the retired projection); the empty selector; app wiring commits a replayable binding; app wiring refuses a stale binding |
| Renderer (`test_gamemaster_view_rendering.py`) | 2 passed: every view element appears in order, and rendering is deterministic |
| Retirement and migration (`test_legacy_authority_retirement.py`) | 17 passed. Surface; tokenizer scan finding no retired identifier used as code; ORM metadata; then the 0036→0037 upgrade, detailed below |
| Migration 0037 upgrade | A 0036 store is seeded through the bounded fixture's genuine publish and activate path. Before upgrading, all 15 protected tables are non-empty: source corpus, projection, activation, typed override, and retained version, entries and scope. `foreign_key_check` is empty. Only the final step runs, under a test-scoped `PRAGMA foreign_keys=ON` hook, and every migration connection reported 1. Afterwards: exactly the two tables are gone; all other schema and rows are identical; `foreign_key_check` is empty; the retained binding replays with its override applied; and it is still current. |
| Migration 0037 downgrade and head schema | Downgrade equals a fresh 0036 schema, with empty legacy tables; re-upgrade succeeds. The head `rp_*` tables equal the ORM's. |
| Updated suites | `rules_authority/` with the context-builder and rules-package tests: 547 passed. Ingestion, quarantine, schema separation, persistence quarantine, RPG, Alembic, db bootstrap, pipeline wiring, orchestrator, writer renderer, rules corpus and stable-prefix tests: 558 passed. Pipeline pass tests: 619 passed, 10 skipped. Touched-file rerun: 110 passed. Ingestion and quarantine after the final parser tightening: 90 passed |
| Black, Ruff (`src/ tests/`), strict mypy (232 files), detect-secrets on every changed file (baseline unchanged), `git diff --check`, pip-audit as CI configures it | All exit 0 on the final files |

**Not counted:**
- A coverage diagnostic using dotted `--cov=afterworlds.<module>` targets produced spurious failures.
  It is not acceptance evidence. The repository's path-based coverage mode passed: 189 tests, with
  100% coverage of the changed `rules_package` service and model, `context_builder` and `srd_parser`.
- Codex intentionally stopped two local runs of the unchanged accepted-release publication test. Its
  test file and the accepted inputs are unchanged, so the full backend and accepted-corpus gate is left
  to required exact-head CI.

**Test accounting** (no coverage or baseline rule weakened):
- **`test_rules_package.py` (77→26 tests).** The deleted tests graded entity models, entity lookup,
  legacy override layering, precedence, payloads and the gate, and the legacy slice. Their replacements
  are the typed-authority suites and the consumer and retirement tests above.
- **`test_ingestion.py` (62→48 tests).** Entity ingestion, provenance, dedup and parsing, the legacy
  override non-mutation test, and the legacy entity and slice reads were deleted. The entity-parse
  atomicity test became the refusal of an `entities` array with no partial state. A new parser test
  refuses an empty `entities` key, and the two remaining inputs of the retired shape lost that key.
- **`test_context_builder.py` (61→60 tests).** `test_rule_chunk_is_immutable` was deleted. It checked
  `RuleChunk` immutability through the retired `AppliedChunk` nesting; `RuleChunk` itself is still
  frozen and unchanged.
- **Per-test inventory:** the private `prune-test_rules_package.log` and `prune-test_ingestion.log`,
  plus the context-builder deletion above.
- **Rewritten, not removed:**
  - the remaining context-builder slice tests: the request goes whole, and slice immutability;
  - the seam tests: retired selectors are refused;
  - the quarantine tests: the entity and override reads are gone;
  - AC25's legacy negative test, which became "no legacy override surface remains".
- The immutable inputs are unchanged: oracle SHA-256
  `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`, with no change under
  `oracles/`, `docs/sources/` or the release-order receipts.

## Boundaries

- **At implementation, no runtime store was opened, migrated or launched against.** `create_app`
  runs `upgrade_to_head` at startup, so the runtime migration needed separate authorization.
  - The smoke's private receipt recorded 0 rows in both legacy tables.
  - **Since done:** after PR #182 merged, the migration was run as a separately authorized,
    harness-driven operation without app startup, and verified. See the
    [runtime cutover record](issue-5d-runtime-cutover.md).
- **Untouched:**
  - no HTTP endpoint, gameplay selector policy, 2b sheet storage or 15c adapter behavior;
  - the frozen #129/15b/19b work;
  - the citation-liveness and suppress-all policies;
  - Awakened Plant;
  - dependency policy.
- **The protected original checkout is unchanged**: HEAD, status, stashes and index match the snapshot.
- **Nothing persists a slice.** `StablePrefix.rules_package_slice` is not serialised, hashed or
  persisted anywhere. It is rendered into prompts, and the orchestrator only copies it into derived
  prefixes.
- **No entity seed or fixture data remains** in the repository (`data/srd/` was removed earlier).
- Private logs are in Codex's evidence directory under `final-5d-cutover/`.

## Architecture Notes

No drift from design principles. The change implements settled #137 contract 6 and AC22 within
ADR-005d Decisions 9–11:
- the existing `RuleSliceRequest` / `get_active_rule_slice` path is extended, not replaced;
- the typed authority remains the single runtime mechanical authority, and retrieval stays
  informational;
- Rules Package and Story Bible authority stay separate;
- downstream deferrals (2b, 15c, frozen work) are unchanged.

ADR-0007, ADR-0008 and ADR-0010 carry supersession banners that reconcile references to the removed
surfaces; their historical decisions are unchanged.
