# PR #119 (CRD Issue 18 Phase 2) — Codex Remediation Log

Local working note. Chronological record of Codex review rounds against
`feature/issue-18-retrieval-memory`, moved out of the PR Architecture Notes
per review-note hygiene: the PR description should carry only final durable
architecture facts, not remediation history. This file is the reference for
"what did Codex flag, how was it classified, what changed, and what proves
it" across rounds.

---

## Round 1 — initial Codex review (commit `f72ed07` reviewed)

### Codex comments
1. **P1** `pipeline/retrieval/eligibility.py` — "Exclude PendingRollRequest rows for legacy RPG turns": backfill/reindex treated every markerless pre-boundary RPG turn as eligible without consulting `PendingRollRequest.originating_turn_id`, so legacy roll-request turns would ingest procedural roll prompts into ordinary Retrieval Memory.
2. **P2** `pipeline/retrieval/query_builder.py` — "Reload full turns before Writing tail eligibility": with the real `SQLiteRecentTurnsProvider`, recent `Turn` models are projected without `mode_metadata`, but `gather_turn_eligibility_for_turn()` decided Writing eligibility from `turn.mode_metadata` — dropped committed `EXTRACTOR_ELIGIBLE` turns from the query tail in production.
3. **P2** `pipeline/retrieval/embedding.py` — "Do not default production retrieval to fake embeddings": omitted embedding functions defaulted to the deterministic hash fake unless an opt-in env var was set, contradicting the module's own "never used in production" contract and ADR-018 D4's local ONNX default.

### Defect classification
Three independent defects: (1) RPG legacy-turn eligibility gap, (2) production read-path eligibility bug (fake-provider tests masked it), (3) inverted embedding-default direction.

### Fixes (commit `c6af5c2`)
- `eligibility.py`: added `has_pending_roll_request` parameter to `decide_turn_eligibility`, checked before RPG marker classification; new `persistence/crud/retrieval.py::has_pending_roll_request_originating_from_turn` CRUD helper.
- `query_builder.py`: switched `gather_turn_eligibility_for_turn(session, turn, story_mode)` to `gather_turn_eligibility(session, turn.turn_id, story_mode)` — reloads the full committed turn instead of trusting the projection.
- `embedding.py`: `resolve_default_embedding_function()` now returns the real ONNX MiniLM default unconditionally; raises `RetrievalEmbeddingUnavailableError` if it can't initialize instead of falling back to fake. Removed the opt-in env-var gate. Every test call site that previously omitted an embedding function now injects `DeterministicFakeEmbeddingFunction()` explicitly.

### Regression tests added
- `test_eligibility.py`: pre-boundary markerless + pending-roll → excluded; without pending-roll → still eligible; post-boundary markerless remains data-integrity error; pending-roll governs regardless of marker category.
- `test_retrieval_markers_db.py`: DB-integrated versions of the above + `has_pending_roll_request_originating_from_turn` direct tests.
- `test_query_builder.py`: new `TestQueryTailWithProductionRecentTurnsProvider` class using the real `SQLiteRecentTurnsProvider` (EXTRACTOR_ELIGIBLE survives, NON_CANON_SUPPORT excluded, OOC excluded, mixed-tail regression proof).
- `test_embedding.py` (new file): omission resolves to real class not fake; real-init failure raises typed error; collection helpers never substitute fake on their own.

### Sibling audit notes
- Confirmed live ingestion, backfill, reindex, and query-tail all consult the single eligibility predicate (`gather_turn_eligibility`/`gather_turn_eligibility_for_turn`), no duplicated mode logic.
- Confirmed every `DeterministicFakeEmbeddingFunction` usage in the codebase is test-only/explicit injection; no collection helper silently substituted it.
- One pre-existing CRD Issue 15 fixture (`_make_orchestrator_with_pending`) needed no changes at this round (that came in round 2).

### Verification method
All three fixes verified by reverting the fix and confirming the corresponding new test failed against the pre-fix code before being counted as passing.

---

## Round 2 — second Codex review (commit `c6af5c2` reviewed)

### Codex comments
1. **P2** `services/context_builder.py` — "Validate retrieval requests against the active story": a `RetrievalQueryRequest.story_id` mismatched against the outer `story_id` would use the request's ID as the Chroma filter while the rest of `StablePrefix` built for the outer story — cross-story chunk leakage into the wrong story's context.
2. **P2** `pipeline/orchestrator/service.py` — "Keep RPG setup turns from defaulting to ordinary narrative": `rpg_play_status` stayed `None` whenever `_rpg_adjudication_service` was absent (even for RPG-mode stories), so SETUP-confirmation turns silently fell through to `ORDINARY_NARRATIVE` and became eligible for ingestion.
3. **P2** `pipeline/retrieval/eligibility.py` — "Treat persisted malformed Writing metadata as ineligible": `get_turn()` raised on a committed row with malformed `mode_metadata`, aborting query-tail building/backfill/the ingestion gate instead of returning `eligible=False` per ADR-018 D6's Writing rule.

### Defect classification
Cross-story retrieval guard defect; durable retrieval eligibility signal defect (adjudication-wiring coupling); fail-closed malformed-metadata defect.

### Fixes (commit `7e05f3e`)
- `context_builder.py`: `build_stable_prefix()`/`assemble()` now raise a typed `ValueError` when `retrieval_query_request.story_id != story_id`, before `RetrievalMemoryProvider.retrieve()` is ever called.
- `orchestrator/service.py`: added an `elif story_mode == StoryMode.RPG:` branch that resolves `rpg_play_status` directly from `self._rpg_session_sheet_resolver`, independent of whether `_rpg_adjudication_service` is wired. Marker classification now fails closed (typed `PIPELINE_ERROR`, rollback) when `rpg_play_status` cannot be resolved at all, instead of defaulting to `ORDINARY_NARRATIVE`.
- New `persistence/crud/retrieval.py::get_turn_for_eligibility()`: reads a Turn while tolerating a malformed/undeserializable `mode_metadata` column (returns `mode_metadata=None` instead of raising). Wired into `gather_turn_eligibility()`, `backfill_story()`, and the orchestrator's `_maybe_ingest_retrieval_memory()`. The general-purpose `get_turn()` is untouched for every other caller (Writer, Extractor, etc.).

### Regression tests added
- `test_context_builder.py`: matching request retrieves normally; mismatched request never calls `.retrieve()`; no cross-story chunk can enter `StablePrefix.retrieval_memory` through a malformed request.
- `test_retrieval_memory.py` (orchestrator): SETUP_CONFIRMATION and ORDINARY_NARRATIVE markers both resolve correctly without adjudication wired; fully-unresolvable case fails closed with no Turn row committed.
- `test_retrieval_markers_db.py`: malformed Writing metadata → `eligible=False` not raise; `get_turn_for_eligibility` doesn't raise; malformed RPG `mode_metadata` has zero effect on RPG eligibility; malformed `intent_classification_result` still raises (tolerance scoped to `mode_metadata` only).
- `test_backfill.py`: malformed Writing metadata row is skipped, not aborting the whole story's backfill.
- One pre-existing fixture fix: `_make_orchestrator_with_pending` (CRD Issue 15 test) needed a session/sheet resolver added, since it incidentally relied on the removed "unresolved play_status defaults to ORDINARY_NARRATIVE" behavior — a legitimate fixture correction under the new fail-closed semantics, not scope creep.

### Sibling audit notes
- Confirmed exactly one public retrieval query gate (`context_builder.py`), and it's now the sole choke point.
- Confirmed no other `_mode_metadata_from_dict` caller needed the wider tolerance; the two general-purpose `get_turn()` call sites in `persistence/crud/node.py` are untouched.
- Confirmed no retrieval-domain code (`pipeline/retrieval/`, `persistence/crud/retrieval.py`) reads `RpgPlayStatus`/current `RpgSessionState` — marker classification is turn-time durable only.

### Verification method
Each new regression test confirmed to fail against the pre-fix code (reproduced the wrong `ORDINARY_NARRATIVE` marker for SETUP, the incorrectly-`DELIVERED` unresolvable case, and the `DID NOT RAISE` cross-story-mismatch assertion).

---

## Round 3 — third Codex review (commit `7e05f3e` reviewed)

### Codex comments
1. **P2** `persistence/crud/retrieval.py` — "Treat non-object mode_metadata as ineligible": the round-2 tolerant read only caught `ValueError`, but malformed SQLite JSON is not guaranteed to be an object — `mode_metadata=[]` or a bare string/number raises `AttributeError` from `.get("mode")` before pydantic ever runs, bypassing the safe-default path entirely.
2. **P2** `pipeline/retrieval/collections.py` — "Reject collection/model mismatches before reuse": `get_story_memory_collection()` (and the rules-corpus equivalent) reused an existing persistent Chroma collection without recording/checking `config.embedding_model_id` — Chroma silently ignores the `metadata=` kwarg once a collection exists, so nothing verified compatibility on reuse; an embedding-model change could mix incompatible vector spaces instead of forcing the ADR-018 D4-mandated reindex.

### Defect classification
Both are hardening fixes to code this same PR introduced in round 2, not new defect classes: (1) tolerant-read exception-tuple gap, (2) missing collection-level embedding-model guard.

### Fixes (commit `2b98382`)
- `persistence/crud/retrieval.py`: widened `get_turn_for_eligibility()`'s except clause to `(ValueError, AttributeError)`. `intent_classification_result` deserialization remains deliberately unprotected — unrelated corruption, must still raise.
- `pipeline/retrieval/collections.py`: `get_story_memory_collection()` and `get_rules_corpus_collection()` now store `embedding_model_id` in collection metadata at creation and check it against `config.embedding_model_id` on every call (new `RetrievalCollectionReindexRequiredError` on mismatch, including a legacy collection with no `embedding_model_id` key at all — treated the same as a mismatch, never assumed compatible). Never auto-wipes or auto-reindexes.

### Regression tests added
- `test_retrieval_markers_db.py`: parametrized tests for `mode_metadata=[]`, `"junk"`, `123`; a non-object-metadata RPG test proving inertness; confirms `intent_classification_result` corruption still raises.
- `test_collections.py` (new file): new collection stores `embedding_model_id` (story-memory and rules-corpus); matching collection reuses cleanly; mismatched collection raises; legacy collection missing the key raises.
- `test_write_service.py` / `test_backfill.py`: `ingest_turn()` and `backfill_story()` both surface `RetrievalCollectionReindexRequiredError` instead of continuing to upsert.

### Sibling audit notes
- Confirmed no other `_mode_metadata_from_dict` caller needed the wider exception tuple.
- Confirmed every collection-creation call in the retrieval subsystem (`chroma_provider.py`, `write_service.py`, `rules_corpus_service.py` both call sites) routes through the two guarded helpers.
- The only other `get_or_create_collection` call in the repo is the already-deferred CRD Issue 5b interim path (`ingestion/vector_writer.py`) — out of this guard's scope per the round-1 Architecture Notes decision to leave it unmodified.

### Verification method
Reverted each fix and confirmed the new tests failed (reproduced the exact `AttributeError`, and an `ImportError` for the not-yet-existing `RetrievalCollectionReindexRequiredError` class).

---

## Round 4 — fourth Codex review (commit `2b98382` reviewed)

### Codex comments
1. **P2** `pipeline/retrieval/query_builder.py` — "Include classified intent in retrieval query text": ADR-018 D8 requires the query to be composed from current input AND classified intent, but `build_query_request()` only received `current_input`/`story_mode` — no caller could include `IntentClassificationResult`, making the vector lookup intent-blind.
2. **P2** `pipeline/retrieval/rules_corpus_service.py` — "Use stable chunk IDs for rules-corpus reindex": the per-run `locator_seen` ordinal became part of the Chroma ID even though the SQL query has no stable ordering and the ID omitted the row's durable `chunk_id`. Reindexing after row-order changes or source additions/removals could assign different vector IDs to the same rule chunks.

### Defect classification
Query-construction contract defect (ADR-018 D8); deterministic-ID/semantic-idempotence defect (ADR-018 D11).

### Fixes (commit `5dbdff1`)
- `query_builder.py`: `build_query_request()` now takes `classified_intent: IntentClassificationResult` and folds a deterministic `intent_type=<value>` fragment into `query_text` (not a `model_dump()` — a fixed textual fragment, so query text doesn't depend on Pydantic field order/defaults). `RetrievalQueryBuilderLike` protocol and the orchestrator call site (`orchestrator/service.py`) now thread the real `intent_result` through. `RetrievalQueryRequest` envelope unchanged (intent folded into `query_text`, not a new field).
- `models/retrieval.py` / `rules_corpus_service.py`: `build_rules_corpus_chunk_id`'s signature changed from `(package_id, locator_type, locator_value, chunk_index)` to `(package_id, chunk_id)`, keyed on `RuleChunkORM.chunk_id` — the row's own durable primary key. Removed `locator_seen` entirely.

### Regression tests added
- `test_query_builder.py`: new `TestClassifiedIntentInQueryText` class — intent appears in query text; two different intents produce distinguishable query text; tail-eligibility filtering unaffected by the intent fragment.
- `test_retrieval_memory.py` (orchestrator): new `TestOrchestratorPassesClassifiedIntentToQueryBuilder` — spy-based proof the orchestrator passes the real classified intent, not an omitted/synthesized one.
- `tests/models/test_retrieval.py`: rewrote `TestRulesCorpusChunkId` for the new 2-arg signature — deterministic; distinct per chunk_id; distinct per package; contains both IDs in the string.
- `test_rules_corpus_service.py`: new `TestRulesCorpusIdStability` class — same-locator/different-chunk-id → distinct stable IDs; reindex after reversed physical row insertion order → same ID set; adding/removing a sibling-locator chunk doesn't change an existing chunk's ID; reindex calls through the shared builder (monkeypatch-spied), not a local formula.

### Sibling audit notes
- Confirmed `build_query_request` has exactly one production call site, with matching intent-bearing signatures on both the protocol and implementation sides.
- Confirmed `build_rules_corpus_chunk_id` has exactly one production call site (reindex — no separate rules-corpus delete/update path exists to keep in sync).
- Confirmed Context Builder never touches intent classification for retrieval purposes (pass-through only) — no code change needed there this round.
- Confirmed `build_story_memory_chunk_id`/`build_story_memory_chunk_id_prefix` signatures are untouched — story-memory ID construction unaffected.

### Verification method
Reverted each fix and confirmed the new tests failed (reproduced the missing `classified_intent` argument as a `TypeError`, the exact same-locator ID collision, and a builder-bypass `TypeError` via the monkeypatched spy).

---

## Round 5 — fifth Codex review (commit `5dbdff1` reviewed)

### Codex comments
1. **P2** `pipeline/retrieval/write_service.py` — "Bypass the model guard for metadata-only deletes": normal query/write/upsert paths correctly reject embedding-model mismatches (round 3's guard), but `delete_turn()`/`delete_story()` also went through the strict `_collection()` path, so an operator couldn't scrub a mismatched or legacy collection's chunks ahead of a reindex — the very thing the guard's own error message told them to do.
2. **P2** `scripts/retrieval_backfill.py` — "Honor retrieval env config in the recovery CLI": the script built `RetrievalMemoryConfig(persist_directory=args.chroma_path)` directly, leaving every other field (`embedding_model_id`, `chunk_char_ceiling`, distance metric, top-k, threshold) at dataclass defaults instead of the environment-derived values the running application uses — reindex/backfill run through this script could recreate the exact mismatch it was meant to fix.

### Defect classification
Operational recovery/reindex correctness after an embedding-model/config mismatch: (1) a recovery-path guard defect (delete blocked by the same guard it exists to let operators route around), (2) a recovery-CLI config defect (partial/default config instead of the app's effective config).

### Fixes (commit `76c9d12`)
- `pipeline/retrieval/collections.py`: new `get_existing_story_memory_collection_for_delete(client)` opens the existing `story_memory` collection bypassing the `embedding_model_id` guard entirely; returns `None` (never creates) if the collection doesn't exist. Deletion by metadata filter never invokes the embedding function at all (verified against chromadb), so compatibility is irrelevant to a delete. `RetrievalCollectionReindexRequiredError`'s message now distinguishes the shared `story_memory` case (a single story's reindex cannot repair a collection-level mismatch — direct the caller to `wipe_collection()` + full rebuild) from the per-package `rules_corpus` case (a package's own `reindex_from_sql` already rebuilds its whole collection).
- `pipeline/retrieval/write_service.py`: `delete_turn()`/`delete_story()` now use the new bypass helper. `ingest_turn()`/`count_for_story()` are untouched — still strict via `get_story_memory_collection()`.
- `scripts/retrieval_backfill.py`: extracted `build_effective_config(chroma_path)`, which starts from `RetrievalMemoryConfig.from_env()` and applies `--chroma-path` as an explicit `persist_directory` override only when provided (argparse default changed from `.chroma_data` to `None` to make "not provided" detectable).
- No source change needed in `backfill.py`: `reindex_story()`'s `write_service.delete_story(story_id)` call now succeeds under mismatch via the bypass (deleting this story's stale entries safely), and the subsequent `backfill_story()` → `write_service.ingest_turn(...)` call still raises the same typed error through the unchanged strict path — already "fails clearly, without unsafe upsert" by construction once delete stopped blocking on the guard.

### Regression tests added
- `test_write_service.py`: new `TestDeleteBypassesEmbeddingModelGuard` class — `delete_story()`/`delete_turn()` succeed against a mismatched collection; delete also works against a legacy collection with no `embedding_model_id` key at all; delete on a missing collection is a no-op and creates nothing (`client.list_collections() == []`); a wrapper-spy proves `delete_story()` never calls `.upsert()`.
- `test_backfill.py`: new test proving `reindex_story()` deletes this story's stale entries (verified via a same-model write service afterward showing count 0) then raises `RetrievalCollectionReindexRequiredError` with a message matching `"shared"` — never silently completing as if the story-level reindex had fixed the collection.
- `tests/test_retrieval_backfill_script.py` (new file, imports the script via `importlib.util.spec_from_file_location` since `scripts/` isn't a package): env `AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID` honored; env chunk ceiling honored; `--chroma-path` overrides only `persist_directory` (env-derived `embedding_model_id`/`chunk_char_ceiling` survive); omitted `--chroma-path` uses the env-derived `persist_directory`; `parse_args()`'s `--chroma-path` defaults to `None`; an integration test proving a "recovery-script" config and an independently-built "app" config (both `from_env()`, same env) see the same collection as compatible.

### Sibling audit notes
- Confirmed `get_story_memory_collection` (strict) has exactly two callers: `write_service.py`'s `_collection()` (used only by `ingest_turn`/`count_for_story`) and `chroma_provider.py`'s query path — both correctly left strict.
- Confirmed the new bypass helper has exactly two callers: `delete_turn`, `delete_story`.
- Confirmed no other script or call site in the repo constructs `RetrievalMemoryConfig(...)` with partial/default fields — `scripts/ingest_srd.py` (the CRD Issue 5b interim path) never touches `RetrievalMemoryConfig` at all.
- One pre-existing, out-of-scope ruff finding surfaced in `scripts/ingest_srd.py` (an unsorted import block) once `scripts/` was added to the ruff gate command for this round — file untouched by this fix; flagged to the user rather than silently fixed or ignored.

### Verification method
Reverted the write_service/collections changes and confirmed all 5 new `TestDeleteBypassesEmbeddingModelGuard`-family assertions failed (guard blocking delete on mismatch, guard blocking delete on a legacy collection, a collection created as a delete side effect, and the not-yet-existing bypass function raising `ImportError`); reverted the script change and confirmed 5 of 6 new script tests failed (`AttributeError: no attribute 'build_effective_config'`, and `--chroma-path` defaulting to `.chroma_data` instead of `None`); reverted both together and confirmed the `reindex_story()` test failed at the delete step instead of the upsert step, with a message that didn't mention "shared".

---

## Round 6 — sixth Codex review (commit `76c9d12` reviewed)

### Codex comments
1. **P2** `pipeline/retrieval/eligibility.py` — "Validate post-boundary roll markers before shortcut": the `has_pending_roll_request` shortcut excluded post-boundary roll-request turns unconditionally, without checking that the marker row actually agreed (`ROLL_REQUEST`, present) — a post-boundary marker/`PendingRollRequest` mismatch (missing marker, wrong category, or a `ROLL_REQUEST` marker with no matching `PendingRollRequest` row) was silently treated as ordinary ineligible instead of the data-integrity error ADR-018 D6's coverage invariant requires.
2. **P2** `pipeline/retrieval/collections.py` — "Catch only missing-collection errors on delete": `get_existing_story_memory_collection_for_delete()` caught bare `Exception`, so an operational Chroma failure (locked store, permission error, client failure) was silently treated as "collection absent" — masking a real failure as a successful no-op delete.
3. **P2** `pipeline/retrieval/backfill.py` — "Abort reindex if the wipe leaves chunks": `reindex_story()` discarded `delete_story()`'s returned remaining-count and always proceeded to `backfill_story()`, so an incomplete wipe (e.g. a partial operational failure) could leave stale chunks alongside a freshly rebuilt set without any signal.

### Defect classification
RPG marker data-integrity reporting plus delete/reindex recovery correctness — three independent hardening fixes across the same recovery-path family as rounds 3 and 5, no scope change.

### Fixes (commit `fix: harden issue 18 reindex integrity checks`)
- `pipeline/retrieval/eligibility.py`: `decide_turn_eligibility()` restructured for RPG mode into an explicit pre-boundary/post-boundary split. Pre-boundary is unchanged (`has_pending_roll_request` alone governs, no data-integrity flag). Post-boundary now requires the two signals to agree: `has_pending_roll_request=True` + missing marker → data-integrity error; + marker present but not `ROLL_REQUEST` → data-integrity error; + `ROLL_REQUEST` marker → normal ineligible (agreement, not a defect). `has_pending_roll_request=False` + `ROLL_REQUEST` marker → data-integrity error (the inverse mismatch, per ADR-018 D6's explicit consistency invariant: "marker category and PendingRollRequest presence never disagree").
- `pipeline/retrieval/collections.py`: `get_existing_story_memory_collection_for_delete()` now catches only `chromadb.errors.NotFoundError` (confirmed empirically as chromadb's actual not-found exception type for `get_collection()`); every other exception propagates.
- `pipeline/retrieval/backfill.py`: new `RetrievalReindexWipeIncompleteError`. `reindex_story()` captures `delete_story()`'s return value and raises this typed error (never calling `backfill_story()`) if any chunks remain — distinct from a data-integrity error (a per-turn SQLite/marker defect reported in `BackfillReport`), this is an operational failure of the delete phase itself. The CLI (`scripts/retrieval_backfill.py`) needed no change: both new exception types are uncaught by `main()`, so they propagate as a nonzero exit with a traceback rather than a success-looking report — already correct by construction.

### Regression tests added
- `test_eligibility.py`: pure-predicate tests for all four post-boundary mismatch shapes (missing marker, `ORDINARY_NARRATIVE` marker, `SETUP_CONFIRMATION` marker, and the inverse `ROLL_REQUEST`-marker-without-`PendingRollRequest` case) plus the agreeing `ROLL_REQUEST`+pending-roll case proving it stays a normal (non-data-integrity) ineligible outcome. Updated the stale `test_pending_roll_request_governs_regardless_of_marker_category` test/docstring, since that exact shape (`ORDINARY_NARRATIVE` marker + pending-roll) is now a flagged mismatch rather than a silent exclusion.
- `test_retrieval_markers_db.py`: one DB-integrated test proving the mismatch is caught through the real `gather_turn_eligibility_for_turn` read path (marker row + `PendingRollRequestORM` row seeded directly), not just the pure predicate.
- `test_backfill.py`: `test_rpg_marker_pending_roll_mismatch_is_reported_as_data_integrity_error` proves `backfill_story()` reports the mismatched turn's ID in `data_integrity_errors` and does not ingest it. New `TestReindexAbortsOnIncompleteWipe` class — `delete_story` monkeypatched to return a nonzero remaining count, proving `reindex_story()` raises `RetrievalReindexWipeIncompleteError` and never calls `backfill_story` (spied via monkeypatch on the module-level name); a companion test proves the normal (`delete_story` returns 0) path still rebuilds.
- `test_collections.py`: new `TestGetExistingStoryMemoryCollectionForDelete` class — absent collection returns `None`; existing collection is returned; a monkeypatched operational `RuntimeError` from `client.get_collection` propagates rather than being swallowed.
- `test_write_service.py`: `test_delete_story_propagates_operational_error_not_remaining_zero` — proves `delete_story()` never reports `remaining=0` when the underlying collection-open call fails operationally.
- `tests/test_retrieval_backfill_script.py`: new `TestCliExitCodes` class driving the script's real `main()` end-to-end against a file-backed SQLite DB (a separate engine connection needs a real file, not `sqlite://`) — delete mode propagates an operational `RuntimeError` without printing "deleted story chunks"; reindex mode propagates `RetrievalReindexWipeIncompleteError` without printing a `scanned=...` report line.

### Sibling audit notes
- Grepped `has_pending_roll_request`, `PendingRollRequest`, `RpgTurnRetrievalCategory.ROLL_REQUEST`, `data_integrity_error`, `get_rpg_turn_retrieval_marker` — the eligibility predicate (`eligibility.py`) is confirmed as the only place marker/pending-roll consistency is decided; `gather_turn_eligibility_for_turn` is the only caller reading the marker/boundary/pending-roll signals, and `backfill_story`/the ingestion gate both route through it.
- Grepped `get_collection` repo-wide: one other call site, `ingestion/vector_writer.py:229` (the CRD Issue 5b interim rules-chunk path, a different subsystem outside `pipeline/retrieval/`) also broadly catches `Exception` for a `count_chunks()`/`has_chunks()` best-effort read (returns 0 on any failure, not a delete-path guard). Left as **out of scope** — not in the Issue 18 retrieval-memory module, not named in this round's sibling-audit list, and a materially different operation (a count fallback, not a delete/recovery guard) — flagged here rather than silently touched.
- Grepped `delete_story`/`delete_turn`: `persistence/crud/story.py`/`persistence/crud/node.py` have same-named functions but are unrelated SQL-level entity deletes, not Chroma retrieval siblings — out of scope, different domain.
- Confirmed `reindex_story` and the CLI's `--mode reindex`/`--mode delete` branches are the only two wipe-then-rebuild or delete-only paths; both now correctly propagate their respective typed failures without a success-looking print.

### Verification method
Reverted `eligibility.py` alone: all 6 new eligibility/DB/backfill tests for the marker-mismatch shapes failed as expected (wrong eligibility/data-integrity outcome). Reverted `collections.py` alone: the new operational-error-propagation test failed (bare `Exception` swallowed the injected `RuntimeError`). Reverted `backfill.py` alone: import of `RetrievalReindexWipeIncompleteError` failed (`ImportError`), confirming the type didn't yet exist. Reverted `backfill.py` + `collections.py` together: the CLI's reindex-exit-code test failed (no exception raised, script printed a `scanned=...` report instead of aborting).

---

## Round 7 — seventh Codex review (commit `bd03c74` reviewed)

### Codex comment
1. **P2** `pipeline/retrieval/rules_corpus_service.py` — "Propagate rules-corpus wipe failures": `reindex_from_sql()` wrapped `self._client.delete_collection(collection_name)` in `with suppress(Exception)`, so an operational Chroma failure (locked store, corrupt store, permission error) was silently treated the same as the expected "collection doesn't exist yet" case — reindex would then proceed straight into `get_rules_corpus_collection()` + `upsert()`, potentially leaving stale disabled/deleted chunks retrievable through the diagnostic query even though the wipe never actually happened.

### Defect classification
Chroma wipe/rebuild sibling-audit defect — the same family as round 6's collection-access narrowing, but for the *delete-collection* (not delete-by-metadata-filter) operation, across every wipe-then-rebuild path in the retrieval-memory module.

### Fixes (commit `fix: propagate rules corpus wipe failures`)
- `pipeline/retrieval/collections.py`: new shared `delete_collection_ignoring_absence(client, collection_name)` — `with suppress(NotFoundError)` around `client.delete_collection(...)` (confirmed empirically: chromadb's `delete_collection()` raises the same `chromadb.errors.NotFoundError` as `get_collection()` for a missing collection). Every other exception propagates.
- `pipeline/retrieval/rules_corpus_service.py`: `reindex_from_sql()` now calls the shared helper instead of its own `suppress(Exception)` block — an operational failure now propagates before `get_rules_corpus_collection()`/`collection.upsert()` are ever reached.
- `pipeline/retrieval/write_service.py`: sibling fix — `wipe_collection()` had the identical `suppress(Exception)` pattern around its own `delete_collection()` call. Even though nothing in this codebase currently chains an automatic rebuild after `wipe_collection()` (it's operator-driven: wipe, then separately run backfill per story per the guidance text in `collections.py`'s reindex-required error message), a silently-swallowed operational failure here would let an operator believe the collection was cleared and proceed to backfill on top of a still-populated (and, in the mismatch scenario, still-incompatible) collection — tightened to the same shared helper for consistency.

### Regression tests added
- `test_rules_corpus_service.py`: new `TestReindexPropagatesWipeFailure` class — operational `delete_collection()` failure propagates; `get_rules_corpus_collection()` is never called after the failure (monkeypatch-spied); a `diagnostic_query()` after the failed wipe shows the old content unchanged (loud failure, not a silent empty/stale "success"); a genuinely absent collection is still ignored and reindex rebuilds normally.
- `test_collections.py`: new `TestDeleteCollectionIgnoringAbsence` class exercising the shared helper directly — absent collection is a no-op; existing collection is deleted; an operational error propagates.
- `test_write_service.py`: new `TestWipeCollectionPropagatesOperationalFailure` class — absent collection is a no-op; an operational error propagates rather than being swallowed.

### Sibling audit notes
- Grepped `suppress(Exception)` / `except Exception` across `pipeline/retrieval/`: found exactly two wipe-then-rebuild sites (`rules_corpus_service.py`'s `reindex_from_sql`, `write_service.py`'s `wipe_collection`) — both patched to the shared helper. A third hit, `embedding.py`'s `except Exception as exc:` in `resolve_default_embedding_function()`, is not a wipe/delete path — it converts an embedding-function-init failure into a typed `RetrievalEmbeddingUnavailableError` and re-raises immediately (`raise ... from exc`), already loud by construction — confirmed **already safe**, no change needed.
- Grepped `delete_collection` repo-wide: one sibling outside `pipeline/retrieval/` — `ingestion/vector_writer.py::delete_collection()` (the CRD Issue 5b interim path) has the identical `with contextlib.suppress(Exception)` pattern, called from `ingestion_service.py::_repopulate_vector_index()` immediately before `write_chunks_raw()` (an upsert) — structurally the same defect family. Disposition: **out of scope / owner decision needed**. This is CRD Issue 5b's own ingestion pipeline, not part of the ADR-018 retrieval-memory module this PR owns; the PR body's round-5 cumulative note already flagged `ingestion/vector_writer.py` as "left in place, unmodified... worth a sibling-audit note if the owner wants it retired now rather than deferred." Patching it here would expand scope into a different subsystem's error-handling contract without an owner decision on whether 5b's interim path is being retired or kept — flagged, not silently fixed, per CLAUDE.md's sibling-audit gate.
- Confirmed `RetrievalMemoryWriteService.delete_turn()`/`delete_story()` (round 5/6's delete-only bypass) and `get_existing_story_memory_collection_for_delete()` are unaffected — they perform metadata-filtered `.get()`/`.delete()`, never `.delete_collection()`, so this round's fix is additive, not overlapping.

### Verification method
Reverted `rules_corpus_service.py` + `collections.py` + `write_service.py` together: all three new test classes failed at collection with `ImportError: cannot import name 'delete_collection_ignoring_absence'`, confirming the helper (and therefore the narrowing) did not yet exist. Re-ran the same three test files after restoring the fix (via `ruff`'s suggested `contextlib.suppress(NotFoundError)` refactor of the initial `try`/`except` draft) to confirm all pass cleanly.

---

## Round 8 — eighth Codex review (commit `34587a8` reviewed)

### Codex comment
1. **P2** `pipeline/orchestrator/service.py` — "Return a typed error when query construction fails": the orchestrator wrapped `self._retrieval_query_builder.build_query_request(...)` in a broad `try`/`except Exception` that logged a warning and proceeded to `_build_context(..., retrieval_query_request=None)` — treating a query-construction failure the same as the Null-builder no-retrieval case. ADR-018 D7's best-effort swallow is scoped to the post-commit Chroma ingestion/write path, not to this pre-context read/query-construction step.

### Defect classification
Retrieval read-path error-semantics defect: a configured `RetrievalQueryBuilder` failure is a context-assembly failure and must produce the same typed `PIPELINE_ERROR` behavior already used for other context-construction failures (e.g. the RPG session/sheet resolver failure a few lines above it), not a silent retrieval-memory omission.

### Fix (commit `fix: fail closed on retrieval query build errors`)
- `pipeline/orchestrator/service.py`: the `except Exception` around `build_query_request(...)` now returns `self._pipeline_error(..., f"retrieval query construction failed: {exc}")` instead of logging and continuing with `retrieval_query_request=None`. The `if self._retrieval_query_builder is not None:` guard is unchanged — no configured builder at all remains a valid, error-free no-retrieval turn (`retrieval_query_request` stays `None` in that case, same as before). `_build_context()` is now never reached at all once a configured builder has raised for this turn — not merely "not called with `None`".

### Regression tests added
`tests/pipeline/orchestrator/test_retrieval_memory.py`, new `TestRetrievalQueryConstructionFailureFailsClosed` class:
- A raising configured builder (`_RaisingRetrievalQueryBuilder`) causes `orchestrate_turn()` to return `PIPELINE_ERROR` with `"retrieval query construction failed"` in `pipeline_error_summary`.
- The Writer (`FakeWriterService.calls`) is never called after the failure.
- The Context Builder (`FakeContextBuilder.calls`) is never called at all after the failure (stronger than "not called with `None`").
- No configured builder (`retrieval_query_builder=None`) still delivers normally.
- A configured builder that succeeds (returns a request, doesn't raise) still delivers normally — only a raised exception is an error.
- Sibling contrast: a post-commit `ingest_turn()` failure (D7's actual best-effort-swallow path) still delivers normally, unaffected by this fix.

### Sibling audit notes
- Grepped `except Exception`/`suppress(Exception)` across `pipeline/orchestrator/service.py`, `pipeline/retrieval/query_builder.py`, `pipeline/retrieval/chroma_provider.py`, `services/context_builder.py`: the query builder and Chroma provider modules have no swallowing at all — a read failure inside `RetrievalMemoryProvider.retrieve()` (called from `ContextBuilderService.assemble()`) propagates naturally through `_build_context()` into the orchestrator's pre-existing `except Exception` at the context-assembly call site, which already maps to a typed `"context assembly failed: ..."` `PIPELINE_ERROR` — confirmed **already safe**, no change needed.
- Confirmed `_maybe_ingest_retrieval_memory()` (the post-commit ingestion gate) is the *only* legitimate best-effort-swallow site for retrieval memory — unchanged, still correctly D7-scoped.
- Confirmed the eligibility reads used for query-tail construction (`gather_turn_eligibility`/`get_recent_turns`, inside `RetrievalQueryBuilder.build_query_request()`) have no internal swallowing of their own — any failure there is exactly what now surfaces through this round's fix.
- Confirmed empty retrieval results (provider returns no chunks) and absent retrieval wiring (no builder/provider configured) both remain valid no-retrieval/normal-turn cases, proven by dedicated tests above — this fix narrows only the "configured builder raises" case.

### Verification method
Reverted `service.py` alone: `test_query_build_failure_returns_pipeline_error`, `test_writer_not_called_after_query_build_failure`, and `test_context_builder_not_called_after_query_build_failure` all failed (turn delivered instead of `PIPELINE_ERROR`); the no-builder, successful-builder, and post-commit-ingestion-failure tests still passed unchanged, confirming the fix is additive and doesn't touch those paths.

---

## Cumulative status as of round 8

- Commits on `feature/issue-18-retrieval-memory`: `f72ed07` → `c6af5c2` → `7e05f3e` → `2b98382` → `5dbdff1` → `76c9d12` → `bd03c74` → `34587a8` → (round 8 fix, pending commit).
- Test count progression: 2077 → 2079 → 2096 → 2107 → 2121 → 2131 → 2143 → 2157 → 2166 → 2172 passed (10 skipped throughout).
- Coverage progression: 90.63% → 90.69% → 90.76% → 90.77% → 90.79% → 90.81% → 90.83% → 90.90% → 90.92% → 90.97%.
- All 5 CI gates (black, ruff, mypy, pytest, pip-audit) green locally, modulo the one pre-existing out-of-scope `ingest_srd.py` ruff finding (unchanged by this branch, CI does not lint `scripts/`).
- Not yet merged; a ninth Codex review will be requested after round 8's push.
- Open sibling-audit item awaiting owner decision (unchanged from round 7): `ingestion/vector_writer.py::delete_collection()` / `ingestion_service.py::_repopulate_vector_index()` (CRD Issue 5b interim path) has the same broad-suppression wipe pattern round 7 fixed in the ADR-018 retrieval-memory module — not touched, since it's a different subsystem this PR doesn't own.
