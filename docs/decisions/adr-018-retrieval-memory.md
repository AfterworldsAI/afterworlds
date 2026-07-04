# ADR-018 — Retrieval Memory: ChromaDB Schema, Eligibility, and Cache-Boundary Reconciliation

**Date:** 2026-07-03
**Issue:** CRD Issue 18 / GitHub #117 — ChromaDB Retrieval Memory: ADR Gate, Vector Service, and
Context Builder Integration
**Status:** Proposed — pending explicit owner acceptance on the Phase 1 PR (`feature/issue-18-adr`).
Per the CRD Issue 18 gate, silence, CI green, or Codex approval alone do not constitute acceptance.
Implementation (Phase 2, `feature/issue-18-retrieval-memory`) does not begin until an explicit owner
comment ("ADR-018 accepted" or "accepted with the following edits") is posted on the Phase 1 PR and
that PR is merged.

---

## Central Invariant

> **ChromaDB is a rebuildable projection of SQLite-authoritative content. It is never the sole home
> of any data, never an authority over narrative or mechanical canon, and never receives material
> that was not delivery-cleared.**

SQLite remains the source of truth for turns, canon, and session state. Every vector record must be
reconstructable from SQLite via reindex. Vector retrieval of rules content is a discovery aid only —
`get_active_rule_slice` (CRD Issue 5a) remains the sole deterministic mechanical authority (CLAUDE.md
invariant 8). Prose blocked by Safety, Contradiction, provider refusal, or pipeline error is never
written as ordinary retrieval memory.

## Context

CRD Issue 8 reserved the seam: a `RetrievalMemoryProvider` protocol, a no-op default
(`NullRetrievalMemoryProvider`), and a named `retrieval_memory` field on `StablePrefix`. ADR-0010
Decision 4 explicitly deferred *real placement* of query-dependent retrieval results to CRD Issue 18 and
flagged the cache-boundary tension this ADR resolves (see Decision 9 below). CRD Issue 5b shipped an
interim rules-chunk vector path flagged for revision here. CRD Issues 15–17 defined what a delivered turn
*is* per mode, including Writing's `WritingCanonEligibility` and RPG's `PendingRollRequest`.

CRD Issue 18 is the one CRD issue with a mandatory ADR / owner checkpoint inside it. This document
resolves Decision Items D1–D11 from the CRD Issue 18 spec, plus the Owner Decision on the RPG
turn-category marker, per the spec's Phase 1 documentation-only scope. No implementation code,
dependency, or migration accompanies this PR.

## Two-Phase Gate Record

- **Phase 1 (this PR):** `/docs/decisions/adr-018-retrieval-memory.md` (this document) plus the
  `known_unknowns.md` edit resolving the ChromaDB collection-schema entry. No code.
- **Acceptance:** owner comment on the Phase 1 PR — `<link to be added when posted>` — followed by
  merge of that PR.
- **Phase 2:** `feature/issue-18-retrieval-memory`, opened only after Phase 1 merges, implementing
  exactly what is accepted here. Any deviation discovered mid-implementation is a stop-and-flag event
  in that PR's Architecture Notes, not a silent amendment.
- **Split escape hatch:** not exercised. Nothing surfaced during Phase 1 review that the ADR could not
  settle; the default of one gated issue holds.
- **What this ADR fixes vs. what it leaves to Phase 2:** ADR-018 defines invariants, required
  metadata, eligibility gates, coverage rules, and the set of allowed implementation mechanisms (e.g.
  the two bounded ingestion-gate mechanisms in "Confirmation of Unchanged Structure" below). Phase 2
  chooses concrete helper names, callback names, module layout, and other local factoring so long as
  the accepted invariants hold — the ADR does not prescribe those. A review comment about exact helper
  placement, naming, or factoring inside an already-accepted mechanism is Phase 2 implementation review,
  not a Phase 1 ADR defect, unless it exposes a **materially new architectural contradiction** — a
  break in an accepted invariant, gate, or coverage rule stated elsewhere in this document, or a
  conflict with the CRD Issue 18 spec — rather than a naming, factoring, or helper-placement preference.

---

## Decision 1 (D1) — Collection Topology

**Decision:** One shared `story_memory` collection with a mandatory `story_id` metadata filter on
every query, plus one `rules_corpus` collection per published Rules Package, absorbing/reindexing the
CRD Issue 5b interim collection. Story memory and rules corpus are never mixed in one collection — that
separation is a spec constraint (narrative vs. mechanical canon authority), not an ADR choice.

**Rationale:** Per-story collections multiply Chroma overhead and make cross-story leakage a
*topology* property that silently degrades if any code path selects the wrong collection. A single
mandatory filter, enforced by one query-gate function every read path traverses, is testable in one
place rather than N.

**Phase 2 test obligation (leakage and integration, ties D1, D2, and D5 together):** "testable in one
place" above is a design property, not a substitute for the tests themselves — Phase 2 must add tests
proving:

- Seed at least two stories with similar or overlapping retrieval-memory content (e.g., near-duplicate
  or thematically similar prose across both), then prove a query scoped to Story A **never** returns
  Story B's chunks, and vice versa.
- The mandatory `story_id` query-gate filter (D1) is applied on **all** public read paths — every
  entry point that can query `story_memory`, not just the primary retrieval call — so no code path can
  bypass the gate function.
- D2's metadata filtering is honored **together with** D5's relevance/similarity scoring — a result
  must pass both the `story_id` filter and the configured similarity threshold, not one in place of the
  other.
- A populated retrieval-memory result enters `StablePrefix.retrieval_memory` through the existing
  Context Builder / `RetrievalMemoryProvider` seam (CRD Issue 8) **without changing the envelope shape** —
  proving the seam is used as reserved, not replaced or bypassed.
- An empty or fully-filtered-out result renders as the **existing omitted/empty payload behavior**
  (D5) — no placeholder block, no cache-key pollution, consistent with the CRD Issue 12c renderer's
  existing omission behavior for empty payloads.

## Decision 2 (D2) — Metadata Schema

**Decision:** Story-memory chunks carry `schema_version`, `story_id`, `node_id`, `turn_id`, `mode`,
`source_type`, `chunk_kind`, `chunk_index`, `chunk_count`, `created_at`, `content_hash`,
`embedding_model_id`. Rules-corpus chunks carry the CRD Issue 5a provenance fields (`source_document`,
`source_locator_type`, `source_locator_value`) plus `rules_package_id`, `subsystem`,
`embedding_model_id`, `schema_version`.

`source_type` and `chunk_kind` are distinct typed fields and must not be collapsed into one:

- `source_type` is the provenance/origin class of the record — *where the content came from*. Typed
  enum, `DELIVERED_TURN_PROSE` in v1 (the only source CRD Issue 18 ingests); extensible later to
  `STORY_BIBLE_ENTRY`, `CANON_PACK`, or other approved retrieval sources if and when those are scoped
  by a future issue, without schema migration. This field is reserved now so a future source-type
  addition is additive, not a schema change.
- `chunk_kind` is the semantic kind of chunk *within* that source — typed enum, `SCENE_PROSE` in v1
  (the only chunk kind CRD Issue 18 produces, per Decision 3's one-chunk-per-turn-prose policy).

Reserving `source_type` now does not authorize ingesting any source beyond delivered turn prose in v1;
it is a typed field with one populated value, not new ingestion behavior.

## Decision 3 (D3) — Chunking Policy

**Decision:** One chunk per delivered turn's prose when under a configured character ceiling
(starting value ~4,000 characters, held in `RetrievalMemoryConfig`); above it, split on paragraph
boundaries with `chunk_index`/`chunk_count`. No semantic chunker, no overlap windows in v1.

## Decision 4 (D4) — Embedding Strategy

**Decision:** A local, deterministic embedding function (ChromaDB's default ONNX MiniLM path) behind
an injectable `EmbeddingFunction` seam. Embedding requires no hosted or provider credentials — BYOK
and local-first paths embed identically. `embedding_model_id` is recorded in collection metadata and
per chunk. Changing the embedding model requires a full reindex; mixed-model collections are a
defect. Default CI injects a deterministic fake embedding function; the real model runs behind the
existing opt-in integration flag.

## Decision 5 (D5) — Retrieval Defaults

**Decision:** `top_k` (starting value: 4) and a minimum-similarity threshold, both in
`RetrievalMemoryConfig`, not code constants. An empty or fully-filtered result set returns the
existing empty typed payload, which the CRD Issue 12c renderer already omits — no placeholder block, no
cache-key pollution.

**Threshold semantics (deterministic, required before Phase 2 implements filtering):** naming a
configurable threshold is not itself a deterministic filtering rule — Chroma's query results expose a
distance/score whose scale and pass/fail direction depend on the collection's chosen metric, so this
ADR fixes that ownership and direction rather than leaving it to Phase 2 to infer:

- Phase 2 must choose and document the Chroma collection metric used for `story_memory` retrieval (this
  ADR does not pin the specific metric value; it pins the requirement that Phase 2 name one, once,
  in the code that configures the collection).
- Phase 2 must normalize whatever Chroma returns (a raw distance or a metric-specific score) into a
  single internal **similarity** value before comparing it to the configured threshold — the comparison
  must never operate on a raw, un-normalized Chroma distance directly, since distance and similarity
  can point in opposite directions depending on the metric.
- **Cutoff direction and inclusivity are fixed by this ADR:** a result is retained when
  `normalized_similarity >= minimum_similarity_threshold` — greater-than-or-equal, not strictly greater.
  A result exactly at the threshold is included, not excluded.
- The configured threshold is applied **after** mandatory metadata filters (D1's mandatory `story_id`
  filter first) and **before** the surviving results are rendered into `StablePrefix.retrieval_memory`
  — metadata filtering and relevance filtering are two distinct gates applied in that order, not one
  substituting for the other.
- **Phase 2 test obligation:** relevance/threshold tests must assert both a below-threshold result is
  excluded and a result exactly at the threshold is included, per the `>=` cutoff above — a test suite
  that only proves "above threshold survives, below threshold doesn't" without an exact-boundary case
  does not satisfy this Decision.

This ADR does not pin a specific numeric default for the threshold beyond what is already stated
elsewhere in this document (none is) — the fix here is metric/score-conversion ownership, cutoff
direction, and inclusivity, not a particular starting value.

## Decision 6 (D6) — Write Triggers and Eligibility

**Decision:** The write trigger fires only after the outer transaction has committed successfully, for
`DELIVERED` narrative turns only — reaching the post-transaction lifecycle point is not itself proof of
commit success; see the ingestion gate in "Confirmation of Unchanged Structure" below for the mechanism
Phase 2 must use to guarantee this, since the existing orchestration seam does not guarantee it
unmodified. Excluded: every blocked/refused/error disposition and any rolled-back turn (the ingestion
gate keeps these from ever reaching a Chroma write attempt). Excluded by rule: `OOC_HANDLED` turns
(`RecentTurnReader` already excludes them from narrative windows) and `INTERACTION_REJECTED` (no Turn
exists).

**Writing mode is affirmative, not exclusion-based:** a Writing-mode turn is eligible only when its
effective `WritingCanonEligibility == EXTRACTOR_ELIGIBLE`. Per CRD Issue 17,
`WritingTurnRequest.canon_eligibility_override` is the only v1 input that can *request* promotion of a
turn — Writer prose, classifier heuristics, prompt text, or `work_product_kind` alone never make a
Writing turn retrieval-indexable.

**Writing setup turns are not retrieval-indexable in v1, and this requires an explicit durable guard,
not just the request-validator check.** `WritingTurnRequest`'s own validator rejects `EXTRACTOR_ELIGIBLE`
for non-prose `work_product_kind`s (e.g. `SETUP_CONFIRMATION`), but that check has no knowledge of
`WritingPlayStatus.SETUP` — a caller can construct a request with a prose-like `work_product_kind`
(`DRAFT_PROSE`, `PROSE_CONTINUATION`, `REVISION`) and `canon_eligibility_override=EXTRACTOR_ELIGIBLE`
*while the Writing session is still in `SETUP`*, and the validator has no basis to reject it — request
shape alone cannot detect this, because the request object carries no play-status field. Per D6's
durable-carrier rule below, `_narrative_persist` takes `work_product_kind`/`effective_canon_eligibility`
directly from a supplied `WritingTurnRequest` without itself checking `play_status is
WritingPlayStatus.SETUP` (`service.py:1680-1689`) — that `SETUP`-aware defaulting applies only when no
request is supplied. So a setup-session turn with prose-like request metadata could be durably recorded
as `EXTRACTOR_ELIGIBLE`, violating ADR-017's setup-turn invariant, unless Phase 2 adds an explicit
guard. Phase 2 must ensure a Writing turn taken while the Writing session is still in setup cannot be
ingested or included in a retrieval-query tail even if the transient request supplied prose-like
`work_product_kind` and `EXTRACTOR_ELIGIBLE` — a setup-session turn must not become retrieval-eligible
solely because committed metadata says `canon_eligibility == EXTRACTOR_ELIGIBLE`, if a durable
SQLite-reconstructable setup signal says it was taken during setup. Phase 2 may satisfy this either by:

- making the persisted per-turn `WritingNodeMetadata` write itself enforce setup/non-canon (i.e., force
  `NON_CANON_SUPPORT` when `play_status is WritingPlayStatus.SETUP`, regardless of what the request
  supplied) before eligibility is ever evaluated; or
- adding an explicit durable setup-turn guard/carrier, readable from SQLite by both the live eligibility
  check and reindex/backfill, that overrides a request-supplied `EXTRACTOR_ELIGIBLE` for turns taken
  during setup.

Either mechanism is Phase 2 implementation detail, not an owner decision, so long as a setup-session
Writing turn is never retrieval-eligible on the strength of transient request shape alone.

**Durable-carrier rule (the eligibility check reads SQLite, never the transient request):**
`WritingTurnRequest` is an in-memory, per-call object — it is not itself SQLite-authoritative and does
not survive past the turn that constructed it. The durable carrier is the per-turn `WritingNodeMetadata`
record committed inside the outer transaction (`_narrative_persist`,
`src/afterworlds/pipeline/orchestrator/service.py:1640-1769`). Source inspection confirms this write is
**best-effort**: the entire block is wrapped in a bare `except Exception: pass` (`service.py:1768-1769`)
that logs nothing and does not abort the turn if the metadata write fails, so a committed, delivered
Writing turn can exist in SQLite without its `WritingNodeMetadata` row. For ingestion, retrieval-query-
tail inclusion, and reindex/backfill alike:

- Writing eligibility must be read from the **committed per-turn `WritingNodeMetadata`** in SQLite, not
  from the transient `WritingTurnRequest` that produced it. `canon_eligibility_override` may request
  promotion at turn time, but Phase 2 may index (or include in a retrieval-query tail) a Writing turn
  only after that requested eligibility has been durably recorded on the committed Turn — a request
  that was never persisted is not sufficient on its own.
- If the per-turn Writing metadata is **absent, malformed, or does not read `canon_eligibility ==
  EXTRACTOR_ELIGIBLE`**, the turn is treated as retrieval-ineligible — this is the safe default for the
  best-effort write's failure mode, and it holds regardless of what the original request asked for.
- Phase 2 must not ingest a Writing turn, or admit it to a retrieval-query tail, based solely on the
  transient request object having requested `EXTRACTOR_ELIGIBLE`.
- Phase 2 has two ways to satisfy this: either read committed per-turn metadata as the sole
  eligibility source (as required above), or make the `WritingNodeMetadata` write mandatory (not
  best-effort) for turns that request promotion, before the ingestion gate can admit them — either
  approach preserves the Central Invariant that every Chroma record is reconstructable from SQLite
  alone. Which of these two Phase 2 chooses is implementation detail, not an owner decision, so long as
  a turn is never indexed on the strength of a request that SQLite cannot later reproduce.

**Phase 2 test obligation (Writing setup-turn guard):** Phase 2 must add tests proving: (1) a Writing
turn taken while the Writing session is in `SETUP`, whose transient request supplied a prose-like
`work_product_kind` and `canon_eligibility_override=EXTRACTOR_ELIGIBLE`, is not ingested and does not
enter a retrieval-query tail — regardless of which of the two guard mechanisms above Phase 2 chose; (2)
reindex/backfill reaches the same exclusion decision from SQLite alone, without access to the original
`WritingTurnRequest`, using whichever durable signal (enforced metadata or explicit setup-turn carrier)
Phase 2 implemented.

**RPG roll-request and setup-confirmation turns** are `DELIVERED` but largely procedural. Only
`delivered_output` prose is indexed — never internal records (`ResolvedAdjudicationRecord`, audit
rows, sheet state, unselected branch options) — so hidden-roll information cannot leak into retrieval
beyond what the delivered prose already said. The limiting rule: such turns are eligible only to the
extent their delivered output is story-facing or durable narrative setup prose; purely procedural
prompts ("roll a Dexterity saving throw," "choose your dice mode," "confirm this setting") are not
indexed as scene memory. Both exclusions are realized through typed, turn-time-persisted signals and
are wholesale in v1:

- **Roll-request turns** are identified by `PendingRollRequest.originating_turn_id` — an existing
  turn-time SQLite record (confirmed at `src/afterworlds/models/rpg.py:212`, ORM table
  `pending_roll_requests` at `src/afterworlds/persistence/orm/rpg.py:86-90`, non-nullable FK to
  `turns.turn_id`, written on the announce turn inside the existing outer transaction). This is
  already replay-safe at any later reindex; no new carrier is needed for this exclusion.
- **RPG setup-confirmation exclusion** must be derived from turn-time persisted metadata or another
  SQLite-reconstructable signal, and must **not** infer historical setup status from current
  `RpgSessionState.play_status`, because reindex/backfill may run after the story has moved to
  `in_play`, at which point old setup turns become unidentifiable from current state.

**Phase 1 source-inspection outcome (required by the spec):** *No existing signal; owner-authorized
marker sidecar shipped.* Inspection findings, with citations:

- `Turn` (`src/afterworlds/models/turn.py:19-49`) carries no `turn_kind`/`turn_category`/phase field.
  `mode_metadata` is a typed discriminated union (`RpgNodeMetadata | BranchingNodeMetadata |
  WritingNodeMetadata`, `src/afterworlds/models/node.py:129-132`), not a raw JSON blob.
- `RpgNodeMetadata` (`src/afterworlds/models/node.py:44-49`) carries exactly `mechanical_notes` and
  `dice_results` — no kind/category/phase field — and has zero constructor call sites anywhere in
  `src/`; it is defined but never instantiated.
- No `TurnKind`, `TurnCategory`, `RpgTurnPhase`, `SetupPhase`, or equivalent symbol exists anywhere in
  `src/` or `docs/` for RPG turns.
- The exact pattern this exclusion needs *does* exist, but only for Writing mode: ADR-017 Decision 9
  and `src/afterworlds/pipeline/orchestrator/service.py:1651-1767` persist
  `WritingWorkProductKind.SETUP_CONFIRMATION` on a per-Turn `WritingNodeMetadata` record specifically
  because `NodeORM.turns` is a list and only a per-Turn record survives later turns on the same Node.
  RPG has no analogous hook: the only RPG setup-related logic
  (`service.py:526-534`) skips building a `RuleSliceRequest` when
  `pre_session_state.play_status is RpgPlayStatus.SETUP` but stamps nothing durable on the Turn.
- `RpgPlayStatus` and `RpgSetupPhase` live only on `RpgSessionState` (session-level, mutable; ADR-015
  §"play_status transitions"). This is precisely the signal the spec disqualifies for backfill use,
  confirmed by inspection: it mutates from `setup` to `in_play` in place, with no historical trace of
  which turns occurred under which status.

Because no qualifying signal exists, CRD Issue 18 adds the narrow RPG-only carrier described in the Owner
Decision below.

**RPG turn-category marker (Owner Decision):**

- A **sidecar table**, `rpg_turn_retrieval_markers` (do not add columns to the core `turns` table),
  written inside the existing CRD Issue 12c outer transaction when the **narrative-path** Turn row is
  persisted — at the same location and transaction-scoping as the Writing-mode block at
  `service.py:1651-1767` (a Phase-G-style block inside `_narrative_persist`, `service.py:1238`, gated
  on `story_mode is StoryMode.RPG`). **The marker import from that Writing-mode block is location and
  transaction-scoping only — explicitly *not* its swallow behavior.** The Writing block at
  `service.py:1651-1767` is best-effort (see D6's Writing durable-carrier rule below: the whole block is
  wrapped in `except Exception: pass`, `service.py:1768-1769`); the RPG marker write must **not** follow
  that pattern. The marker write is mandatory: if it fails, the failure must be **caught within the
  narrative-persist code path and mapped to a typed `PIPELINE_ERROR` `OrchestrationResult`** — the same
  way other in-pass exceptions in this codebase are already mapped to typed terminal results — so that
  `_finalize_transaction` receives a typed result and rolls back the transaction through its normal
  commit/rollback decision. The marker-write failure must **not** be left to escape as a raw exception
  from `inner(session)`: `_run_with_transaction`'s `except BaseException` handler
  (`service.py:3464-3470`) only rolls back and reraises — it does not itself produce a typed
  `PIPELINE_ERROR` result — so an uncaught marker-write exception would surface from
  `orchestrate_turn` as a raw exception rather than satisfying the exhaustive typed-terminal-state
  contract. A blocked/refused/errored turn's marker rolls back with the turn, and a marker-write
  failure on an otherwise-deliverable turn must itself cause that turn to become a typed
  `PIPELINE_ERROR` and roll back, never commit markerless. No orphan
  markers for never-delivered turns. **This write happens only on the narrative persist path, never on
  the OOC persist path (`_run_ooc()` / `_ooc_persist()`, `service.py:2142` / `service.py:2254`) — the
  two are separate persist functions, so the marker write is structurally absent for OOC turns, not
  merely unpopulated for them.**
- **Coverage is narrower than "every RPG turn."** The sidecar covers one row per **post-boundary RPG
  narrative-path `DELIVERED` turn that reaches retrieval-eligibility classification** — i.e., the same
  turns Decision 6's write trigger considers for story-memory ingestion, from the persisted marker-era
  boundary defined below onward. RPG `OOC_HANDLED` turns are real persisted Turns, but they are
  persisted through `_ooc_persist()`, not `_narrative_persist()`, so they never reach the
  marker-writing block at all — the same D6 disposition/path gating that already excludes all
  `OOC_HANDLED` turns from retrieval (`RecentTurnReader` exclusion semantics) corresponds directly to
  which persist function runs. A missing marker on an RPG `OOC_HANDLED` turn is expected and is not an
  error; a missing marker on a post-boundary RPG narrative-path `DELIVERED` turn that requires
  retrieval classification is an error (see the coverage invariant below).
- A typed category enum with exactly `ORDINARY_NARRATIVE`, `ROLL_REQUEST`, and `SETUP_CONFIRMATION` —
  unchanged; no OOC/non-indexed category is added. OOC turns do not need a fourth category because they
  are filtered out before marker classification, not classified into it.  No general cross-mode turn
  taxonomy, no new dispositions, no new passes, no prose heuristics, no UI/API surface.
- Rows are written once and never updated; deletion follows turn deletion.
- Consumed only by the CRD Issue 18 retrieval eligibility predicate. No other reader in v1.
- **Forward-only, with a persisted, SQLite-authoritative marker-era boundary.** Markers exist for turns
  created after the marker ships; historical RPG turns are left unclassified rather than guessed — no
  retroactive classification from prose or current state. This alone is not enough to make "no marker
  row" safe to interpret during reindex: a post-boundary marker-write bug leaves exactly the same
  SQLite shape as a legitimate legacy pre-marker turn (no marker row, no `PendingRollRequest`), so
  Phase 2 **must persist, in SQLite, the marker-era boundary itself** — a migration/epoch record,
  sentinel row, schema-version record, or equivalent SQLite-authoritative cutoff marking the point
  from which `rpg_turn_retrieval_markers` coverage became mandatory for RPG narrative-path `DELIVERED`
  turns. This boundary must be reconstructable during reindex/backfill, not inferred from application
  state or timing. With it persisted:
  - A markerless RPG narrative-path `DELIVERED` turn created **before** the persisted boundary is
    legacy/pre-marker and governed by the pre-boundary rows in the era-boundary table below (treated
    as `ORDINARY_NARRATIVE`, eligible) — unchanged from the original forward-only design.
  - A markerless RPG narrative-path `DELIVERED` turn created **at or after** the persisted boundary is
    a **data-integrity error**, not a legacy turn — the mandatory in-transaction marker write above
    should have prevented this shape from existing at all. Reindex/backfill must detect and flag (or
    exclude) such a turn rather than silently falling through to `ORDINARY_NARRATIVE` eligibility.

**Era-boundary mechanism (pre-boundary legacy vs. post-boundary mandatory-coverage), deterministic:**

| Turn era | Marker row | `PendingRollRequest.originating_turn_id` | Eligibility predicate outcome |
|---|---|---|---|
| At/after persisted boundary, ordinary narrative | `ORDINARY_NARRATIVE` | absent | Eligible |
| At/after persisted boundary, roll-request | `ROLL_REQUEST` | present | Excluded |
| At/after persisted boundary, setup confirmation | `SETUP_CONFIRMATION` | absent | Excluded |
| At/after persisted boundary, `OOC_HANDLED` | none (excluded before marker classification) | absent | Excluded (D6 disposition/path gating; never reaches marker lookup) |
| **At/after persisted boundary, narrative-path `DELIVERED`, marker row absent** | absent | absent | **Data-integrity error — ineligible; must not fall through to `ORDINARY_NARRATIVE`** |
| Before persisted boundary (legacy/pre-marker) | absent (turn predates the persisted boundary) | absent | **Treated as `ORDINARY_NARRATIVE` — eligible** |
| Before persisted boundary, roll-request | absent | present | Excluded (`PendingRollRequest` alone is sufficient and predates the boundary) |

The eligibility predicate must consult the persisted boundary **before** applying the marker/
`PendingRollRequest` signals below: a markerless narrative-path `DELIVERED` turn's era (before vs.
at/after the boundary) determines whether "no marker" means legacy-eligible or data-integrity-error,
and that determination is not derivable from the marker table alone without the boundary record.
**Narrative-path vs. `OOC_HANDLED` classification at reindex time is itself SQLite-reconstructable, not
inferred:** both dispositions leave a committed `Turn` row, and `Turn.intent_classification`
(`src/afterworlds/models/turn.py:46`) is persisted per-turn and already queried this way elsewhere
(`TurnORM.intent_classification != IntentType.OOC`, `src/afterworlds/services/context_builder.py:268`).
Reindex/backfill classifies a markerless committed RPG turn as the legitimately-markerless `OOC_HANDLED`
case when `intent_classification is IntentType.OOC`, and as the narrative-path data-integrity-error case
otherwise — this is the same signal the live codebase already uses to distinguish the two, not a new
inference the ADR invents.

Every post-boundary RPG **narrative-path `DELIVERED` turn that reaches retrieval-eligibility
classification** gets exactly one marker row — this is the narrowed sidecar coverage rule stated
above — and it applies uniformly across all three categories, roll-request included. A post-boundary
roll-request turn is never markerless: it carries `ROLL_REQUEST` in `rpg_turn_retrieval_markers` *and*
a `PendingRollRequest` row. These two signals are written independently (the marker at turn creation,
`PendingRollRequest` on the announce turn) but must agree for every such turn — that agreement is a
coverage invariant, not an eligibility mechanism. RPG `OOC_HANDLED` turns are outside this coverage
rule entirely: D6's disposition/path gating excludes them before marker classification is ever
reached, so they carry no marker row and none is required — this is not a gap in the sidecar, it is
the sidecar's scope.

**Predicate precedence vs. coverage invariant — two different things:**

- **Eligibility precedence:** the persisted marker-era boundary is checked first to establish turn era;
  within a post-boundary turn, `PendingRollRequest.originating_turn_id` is what the eligibility
  predicate actually checks to exclude roll-request turns, and it governs regardless of marker
  category. The marker governs setup-confirmation exclusion. `OOC_HANDLED` turns are excluded upstream
  of both signals by D6 disposition/path gating. An RPG turn with neither signal, era-checked as
  pre-boundary, is treated as `ORDINARY_NARRATIVE` and is eligible; the same shape at/after the boundary
  is a data-integrity error, not an eligibility outcome.
- **Coverage invariant (post-boundary, narrative-path `DELIVERED` turns only):** independent of which
  signal the predicate consults, every such turn must have exactly one marker row, and a post-boundary
  roll-request turn's marker category must be `ROLL_REQUEST`. Marker coverage is a Phase 2 write-time
  obligation the eligibility predicate does not itself enforce; the predicate reads `PendingRollRequest`
  for its exclusion decision, but Phase 2 must not skip the sidecar write for roll-request turns on the
  theory that `PendingRollRequest` alone already gets the correct eligibility outcome. A pre-boundary
  roll-request turn is the only case where marker absence is expected and correct for a narrative-path
  turn — it predates the persisted boundary entirely, so `PendingRollRequest` alone governs, per the
  era-boundary table above. RPG `OOC_HANDLED` turns are outside the coverage invariant's scope at every
  era, marker or no marker, because D6 gating removes them before classification, not because the
  sidecar failed to cover them.

**Rationale (ADR-ratified as a D6 sub-decision):** excluding unclassified turns would silently erase
retrieval memory for every pre-boundary RPG story; including them admits at worst a bounded set of
early procedural chunks. Without a persisted boundary, however, that same tolerance would also mask
post-boundary marker-write regressions as ordinary legacy turns — which is why the boundary itself,
not just the marker table, must be SQLite-authoritative. Phase 2's consistency test must assert: (1)
every post-boundary RPG narrative-path `DELIVERED` turn that reaches retrieval classification has
exactly one marker row; (2) RPG `OOC_HANDLED` turns do not require and do not receive marker rows, and
are excluded before marker lookup by D6 disposition/path gating rather than by an absent or mismatched
marker; (3) for post-boundary narrative-path turns, a marker of category `ROLL_REQUEST` has a
corresponding `PendingRollRequest` row and vice versa, and marker category and `PendingRollRequest`
presence never disagree; (4) a markerless RPG narrative-path `DELIVERED` turn created **at or after**
the persisted boundary is detected as a data-integrity error / treated as ineligible during
reindex/backfill, and is never silently treated as legacy `ORDINARY_NARRATIVE`. Pre-boundary turns are
exempt from (1), (3), and (4) by definition — the sidecar did not exist yet — and remain governed
solely by the era-boundary table's pre-boundary rows.

This exclusion applies specifically to **RPG** setup confirmations, not all mode setup turns:
Branching setup confirmations remain eligible as ordinary story-architect narrative turns (CRD Issue 16),
and Writing setup confirmations are excluded via D6's Writing setup-turn guard as described above —
not by structural exclusion alone, since a request-supplied prose-like `work_product_kind` and
`EXTRACTOR_ELIGIBLE` during setup requires the explicit durable guard, not just the request-validator
check, to keep the turn out of retrieval. The consumed-roll turn that narrates the outcome is the
narrative record and is indexed normally. If RPG setup narration proves worth indexing later, that
requires a typed carrier, not prose inspection — a future D6 sub-decision.

## Decision 7 (D7) — Write-Failure Semantics

**Decision:** A Chroma write failure is logged with story/turn identifiers and swallowed — delivery is
never blocked, reversed, or errored by retrieval ingestion. This applies strictly to a write attempted
*after* the ingestion gate in "Confirmation of Unchanged Structure" above has already confirmed a
successful commit and a delivery-cleared, D6-eligible disposition. The gate check itself is not a
"write" and is not covered by this swallow rule: a turn that fails the gate (rolled back, blocked,
refused, pipeline error, or D6-ineligible) must never reach a Chroma write attempt at all, so there is
nothing to swallow for it. "Swallowed" describes the failure mode of the Chroma client/write path for
an already-eligible, already-committed turn (e.g., the vector store is unreachable) — it is not a
substitute for gate enforcement, and must never be read as license to attempt ingestion for rolled-back
or undelivered prose and rely on the swallow to hide it. Because IDs are deterministic and upserts
idempotent, recovery is a re-run: v1 ships an idempotent manual backfill command (reindex a story from
SQLite) rather than an automatic retry queue.

## Decision 8 (D8) — Query Construction

**Decision:** Query construction is orchestration-owned and deterministic — a `RetrievalQueryBuilder`
composes the query text from the current Sojourner input and classified intent (optionally a bounded
recent-turn tail), mirroring the CRD Issue 15 `RuleSliceRequest` precedent. The Context Builder gains no
inference logic; it must not infer retrieval-query contents itself. The `StablePrefix` envelope shape
does not change. This ownership rule is unaffected by the query-context discipline fix below: query
construction stays orchestration-owned, the existing `RetrievalMemoryProvider.retrieve(story_id: UUID,
query: str)` protocol shape does not change, and Phase 2 adds only the call site and request
construction (see the Phase 1 source-inspection finding below).

**Query-context discipline (corrected — `RecentTurnReader` OOC exclusion alone is not sufficient):**
when the query builder includes the optional bounded recent-turn tail, each candidate tail entry must
pass **retrieval-query eligibility**, not merely OOC exclusion. The live `RecentTurnReader`-style
filter (`exclude_ooc`, `src/afterworlds/services/context_builder.py:242-268`) excludes only
`IntentType.OOC` turns — it does not exclude Writing turns whose per-turn metadata is
`WritingCanonEligibility.NON_CANON_SUPPORT`, and D6 above already establishes that Writing retrieval
eligibility is affirmative (only effective `EXTRACTOR_ELIGIBLE` is eligible), not exclusion-based.
Treating `exclude_ooc=True` as sufficient filtering for retrieval-query context would let
critique/brainstorm/config support turns steer story-memory query text even though D6 says those turns
never leak into retrieval. The rule:

- Retrieval-query tail entries must exclude OOC, config, support, non-canon, and D6-ineligible turns —
  the same eligibility rule D6 already applies to *ingestion*, applied here to *query construction*.
- For Writing mode, a prior turn may enter the retrieval-query tail only if its effective
  `WritingCanonEligibility == EXTRACTOR_ELIGIBLE`; `NON_CANON_SUPPORT` turns (critique, brainstorm,
  config, and any other support-turn kind) are excluded from the tail regardless of `exclude_ooc`. Per
  D6's durable-carrier rule above, this check reads the **committed per-turn `WritingNodeMetadata`** in
  SQLite, never the transient `WritingTurnRequest` — a prior turn whose request asked for
  `EXTRACTOR_ELIGIBLE` but whose metadata write did not durably record it is not tail-eligible. This
  includes D6's setup-turn guard: a turn taken while the Writing session was in `SETUP` is not
  tail-eligible even if its request-supplied `work_product_kind`/`EXTRACTOR_ELIGIBLE` looked
  prose-like, per whichever of D6's two guard mechanisms Phase 2 implements.
- Equivalent mode-specific support/config markers (present or future, for RPG or Branching) must be
  excluded before query composition, following the same D6-eligibility-not-OOC-alone principle.
- Existing `RecentTurnReader` behavior may be reused for ordering/window mechanics (recency, limit,
  story scoping) — Phase 2 is not required to build a new reader from scratch — but must add the
  missing eligibility filter on top of it; `exclude_ooc=True` alone does not satisfy this Decision.

**Phase 1 source-inspection finding:** the live `RetrievalMemoryProvider.retrieve(story_id: UUID,
query: str)` protocol (`src/afterworlds/services/context_builder.py:150-163`) already accepts a
`query: str` parameter. `NullRetrievalMemoryProvider.retrieve()` (lines 194-202) ignores both
arguments and returns an empty payload, and `build_stable_prefix()` (lines 395-404) never calls
`self._retrieval_memory.retrieve(...)` at all — it always constructs `RetrievalMemoryPayload()`
literally. **The existing protocol signature already carries a query string; no additive parameter is
needed at the protocol level.** What Phase 2 must add is the call site (the orchestrator/Context
Builder actually invoking `retrieve()` with a built query) and, per the CRD Issue 15 precedent, an
orchestrator-constructed request object analogous to `RuleSliceRequest`
(`src/afterworlds/models/rules_package.py:407-417`, built at
`src/afterworlds/pipeline/orchestrator/service.py:531` and threaded through `_build_context` /
`ContextBuilderService.assemble()` as an additional keyword parameter). This finding resolves the
spec's stated fork ("existing signature sufficed vs. additive pass-through") in favor of **existing
signature sufficed**, at the protocol level; the exact shape of the orchestrator-side request object
and its threading through `assemble()`/`build_stable_prefix()` remains Phase 2 implementation detail,
not an owner decision, per the spec's own framing of D8 as "repo-state-resolved at implementation
time."

**Phase 2 test obligation (retrieval-query-tail eligibility):** Phase 2 must add tests proving: (1)
Writing `NON_CANON_SUPPORT` turns — critique, brainstorm, config, and any other support-turn kind — do
not appear in retrieval-query tail text; (2) Writing turns with effective
`WritingCanonEligibility == EXTRACTOR_ELIGIBLE` may appear in the tail, subject to the bounded
recent-window rule; (3) OOC turns and mode-specific support/config turns (RPG, Branching) are excluded
from query-tail construction; (4) a test must fail if `exclude_ooc=True` alone is treated as sufficient
filtering for retrieval-query context — i.e., a fixture with a non-OOC, D6-ineligible support turn in
the recent window must prove that turn is absent from the composed query text, not merely that OOC
turns are absent.

**Phase 2 test obligation (Writing durable-carrier rule, D6 above):** Phase 2 must add tests proving:
(1) a Writing turn with committed per-turn `WritingNodeMetadata.canon_eligibility ==
EXTRACTOR_ELIGIBLE` may be ingested and may be retrieval-query-tail eligible, subject to the other D6
gates above; (2) a Writing turn with committed `NON_CANON_SUPPORT` metadata is not ingested and does
not enter the retrieval-query tail; (3) a Writing turn whose per-turn `WritingNodeMetadata` is missing
or malformed (simulating the best-effort write's failure mode) is treated as retrieval-ineligible for
both ingestion and query-tail purposes, regardless of what the originating `WritingTurnRequest`
requested; (4) reindex/backfill reaches the same eligibility decision from SQLite alone, without access
to the original `WritingTurnRequest` — proving the Central Invariant's rebuildability holds for Writing
eligibility specifically, not just for chunk content.

## Decision 9 (D9) — Cache Interaction: Resolving ADR-0010 Decision 4

**Background:** ADR-0010 Decision 4 ("Retrieval Memory Cache Boundary Reconciliation") identified that
materializing query-dependent retrieval results inside the cacheable stable prefix is a
**cache-boundary violation**: stable-prefix cost economics assume a ~88% cache hit rate under extended
TTL, and a per-turn-varying retrieval block would collapse cross-turn cache reuse for every turn that
retrieves anything. ADR-0010 deliberately did **not** decide where retrieval belongs — it listed the
volatile suffix, a separate (non-cacheable) retrieval block, or "elsewhere" as candidate placements
and explicitly deferred the real decision to CRD Issue 18: *"Issue 18 owns retrieval implementation and
cache-boundary reconciliation."*

**Phase 1 source-inspection finding:** the CRD Issue 12c shared renderer places the cache breakpoint on
the **last block** in canonical stable-prefix order (Story Bible → Rolling Summary → Rules Slice →
Retrieval Memory), not a fixed position
(`src/afterworlds/pipeline/_stable_prefix_renderer.py:96-161`). Retrieval memory is last in that
order, so once CRD Issue 18 populates a non-empty payload, it becomes the final block and **inherits the
cache breakpoint** — i.e., retrieval memory sits inside the cached/TTL'd stable prefix rather than
after it.

**Decision:** This ADR resolves the placement question ADR-0010 Decision 4 deferred, choosing to keep
retrieval memory inside the existing `StablePrefix` envelope, under the existing breakpoint, rather
than the volatile suffix or a second, separately-cached block.

**Owner Decision — retrieval pass scope:** Retrieval Memory is shared stable-prefix context, available
to **all provider-backed passes that render `StablePrefix`** — this is a structural rule keyed on
"does this pass render `StablePrefix`," not an enumerated allowlist of pass names, so it automatically
covers both base pipeline passes and mode-specific provider-backed passes. It is **not** Writer-only in
v1; all-pass visibility is intentional, not an unreviewed side effect of choosing `StablePrefix`
placement. Phase 2 must not create a separate Writer-only retrieval placement, nor any pass-specific
retrieval-visibility exclusion, without a later owner/ADR decision. Current known consumers of
`StablePrefix` (`render_stable_prefix_blocks(built_context.stable_prefix, ttl)`), and therefore of
Retrieval Memory once populated, include: Planner, Writer, Input Safety, Output Safety, Extractor,
Contradiction, **RPG Adjudication** (`RpgAdjudicationService._render`,
`src/afterworlds/pipeline/rpg/service.py:402-411`), and **Branching Writer**
(`BranchingWriterService._render`, `src/afterworlds/pipeline/branching/service.py:355-357`). This list
is illustrative of the rule's current reach, not the rule itself — if a future provider-backed pass is
added and renders `StablePrefix`, it receives Retrieval Memory under this same rule without requiring
an ADR amendment; a pass being *excluded* from retrieval is what requires a later owner/ADR decision.
Concretely:

- Contradiction may use retrieval memory as part of continuity checking when CRD Issue 18 supplies it, the
  same way it already reasons over the rest of the stable prefix (Story Bible, Rolling Summary, Rules
  Slice).
- Safety (Input Preflight and Output Audit) receives retrieval memory as context whenever its renderer
  includes the stable prefix, exactly as it already receives the rest of stable-prefix content. The
  Safety **target** text being evaluated remains the explicit input or output text under audit;
  retrieval content is contextual background for that evaluation, never itself the audited target.
- Planner and Extractor consume it as ordinary stable-prefix context, consistent with how they already
  consume the rest of `StablePrefix`.
- **RPG Adjudication and Branching Writer receive Retrieval Memory only as ordinary stable-prefix story
  context** — the same way they already receive Story Bible, Rolling Summary, and Rules Slice context
  today. This does not authorize a new RPG mechanical-memory channel, a dice-rule mutation path, a
  Branching graph feature, or any mode-specific retrieval policy; Decision 10's prohibition on semantic
  retrieval as mechanical authority is unaffected, and RPG adjudication's dice/rule mechanics remain
  governed exclusively by `get_active_rule_slice` and the code-owned adjudication rails (CLAUDE.md
  invariants 8, 10), never by retrieved narrative prose.

**Rationale for `StablePrefix` over the volatile suffix or a second breakpoint:** the volatile suffix
and a second cache breakpoint are both rejected, but not on the grounds that retrieval is Writer-only
context — that rationale is incoherent once `StablePrefix` placement (and the all-pass visibility it
carries) is accepted. Instead:

- CRD Issue 8 reserved the `StablePrefix.retrieval_memory` seam; this ADR fills the reserved seam rather
  than inventing a new one.
- CRD Issue 12c already has one shared stable-prefix renderer that every provider-backed pass calls; a
  volatile-suffix or pass-specific placement would require a second, differently-scoped context channel
  duplicating that renderer's job.
- Keeping retrieval in `StablePrefix` avoids introducing a new pass-specific, Writer-only context
  channel — unnecessary once all-pass visibility is the accepted v1 design.
- The cross-turn cache-hit-rate degradation for populated retrieval (stated plainly below) is accepted
  explicitly as a cost of this placement, not disguised as a reason to restrict which passes see it.
- A second cache breakpoint is rejected on separate grounds: it would violate CLAUDE.md invariant 7
  (stable prefix assembled once per turn and reused across provider-backed passes) by splitting
  stable-prefix rendering into two cached regions, adding provider-adapter complexity for no proven
  benefit at v1 scale.
- Any future optimization of breakpoint placement or pass-specific retrieval visibility (e.g., a
  Writer-only fast path, or moving retrieval below a second breakpoint) is later ADR/provider-cache/
  routing work — CRD Issue 14-adjacent — not Phase 2 implementation license.

**Phase 2 obligation (stable-prefix consumer inventory):** because the retrieval-visibility rule is
structural (every pass that renders `StablePrefix`) rather than an enumerated list, Phase 2 must
inspect all current `render_stable_prefix_blocks()` callsites when wiring retrieval — not just the
callsites named above — and document/test that Retrieval Memory visibility follows this rule
uniformly across all of them, base and mode-specific alike. If a future need arises for a pass to
*not* receive retrieval despite rendering `StablePrefix`, that is a contradiction of this accepted D9
placement rule and requires a later owner/ADR decision; it is not a Phase 2 implementation choice.

**Consequence, stated plainly:** a populated retrieval block varies per turn and **will reduce
cross-turn cache reuse** for any turn that retrieves non-empty results, working against the ~88% hit
rate the CRD cost model assumes for those turns specifically. CRD Issue 18 accepts this consequence as the
cost of the simpler envelope. What is preserved is **intra-turn** stable-prefix reuse across the
provider-backed passes within a single turn — the economy the once-per-turn invariant (CLAUDE.md
invariant 7) actually guarantees, and which is orthogonal to cross-turn cache-hit economics. The Issue
12c structural-identity test must be extended to prove byte-identical rendering with a *populated*
retrieval block. CRD Issue 18 does not move the breakpoint, add a second breakpoint, split stable-prefix
rendering, or change provider-adapter behavior. Any future optimization of breakpoint placement or
cache strategy (e.g., moving retrieval below a second breakpoint to restore cross-turn reuse for the
non-retrieval portion) is CRD Issue 14-adjacent provider/cache work, not retrieval-memory implementation,
and would need its own ADR amendment.

## Decision 10 (D10) — Rules-Corpus Vector Use

**Decision:** CRD Issue 18 finalizes the rules collection schema, reindexes the CRD Issue 5b interim
collection into it, and exposes a typed semantic rules-lookup method that is internal/admin diagnostic
or discovery support only in v1. No Context Builder, RPG adjudication loop, Writer, Planner, pass
service, or runtime mechanical decision may consume semantic rules retrieval as authority. Runtime
rule inclusion remains exclusively through `get_active_rule_slice`. Wiring semantic rules discovery
into any runtime path — even as a "hint" — is a future issue plus ADR.

## Decision 11 (D11) — Update/Delete/Reindex Semantics

**Decision:** In-place re-upsert keyed by deterministic IDs, with orphan sweep by `story_id` filter,
over a rebuild-into-fresh-then-swap strategy for story/corpus-level reindex. **Turn-level replacement is
a distinct case and does not get the same "upsert alone suffices" treatment:** deterministic chunk IDs
only overwrite the indexes that still exist in the new chunk set. If a prose correction, a
chunking-ceiling change, or any other operation that replaces a turn's vector representation reduces
that turn from *N* chunks to fewer, the old higher-index chunks are not addressed by the new upsert and
remain in Chroma, retrievable, unless explicitly deleted. Re-upsert alone is sufficient only when the
new chunk cardinality is identical to or greater than the old one, and this ADR must not rely on that
being true. **Turn-level replacement rule:** before writing a turn's current chunk set, Phase 2 must
first **delete all existing vector chunks for that `turn_id`**, then write the current chunk set —
delete-then-write, not upsert-only, for any operation that replaces a turn's vector representation.
Story-level reindex and the `story_id`-filtered orphan sweep are unaffected by this and remain as
already specified. See the mutation table below.

| Operation | Semantics |
|---|---|
| Turn ingested (first time) | Upsert by deterministic ID; re-ingesting the same turn replaces byte-identically — zero duplicates. |
| Turn re-ingested after prose correction, re-chunking, or any chunk-set-replacing operation (future) | **Delete all existing chunks for that `turn_id` first, then write the current chunk set** — not upsert-only. Required even when the new chunk count is unchanged, and mandatory when it is smaller, so old higher-index chunks from a prior, larger chunk set never survive. |
| Turn deleted | Delete all chunks whose IDs derive from that `turn_id`. |
| Story deleted / CRD Issue 22 deletion request | Delete by `story_id` metadata filter across story-memory collections; a post-delete count-zero verification is part of the operation's contract. |
| Reindex (story or corpus) | Rebuild from SQLite-authoritative content; embedding-model change forces reindex. |
| Retrieval config change (top_k, threshold) | Configuration only; no vector mutation. |
| Rules package republished | CRD Issue 5b re-ingestion remains idempotent; CRD Issue 18 reindex refreshes the rules collection without mutating CRD Issue 5a source records. |
| RPG turn-category marker written | Insert-once at turn creation inside the outer transaction; never updated; rolls back with a blocked turn. |
| RPG turn deleted | Marker row deleted with its turn; no orphaned markers. |
| Historical pre-boundary RPG turn | No-op — never retroactively classified; predicate treats it as `ORDINARY_NARRATIVE`. |

**Phase 2 test obligation (turn-level replacement):** Phase 2 must add a test proving that when a
turn's chunk count is reduced by re-ingestion (e.g., a corrected/shorter version of the same prose that
now fits in fewer chunks than the original), the old higher-index chunks are **absent** from the
collection after re-ingestion — not merely that the surviving lower-index chunks were overwritten.

**Idempotence keys are semantic, never generated.** Story-memory chunk ID:
`story:{story_id}:turn:{turn_id}:chunk:{index}`. Rules-corpus chunk ID derives from
`rules_package_id` + the CRD Issue 5a chunk identity. Random UUIDs are prohibited as dedupe keys anywhere
in this issue.

---

## Confirmation of Unchanged Structure

Core pipeline ordering, gating, dispositions, outer-transaction scope, and the `PipelineDisposition`
set are unchanged. Chroma retrieval-memory ingestion must run only after the outer transaction has
committed successfully, for a delivery-cleared disposition eligible under Decision 6 — it is not a
pass, not a disposition, and can neither block nor reverse delivery.

**Phase 1 correction: the existing `post_transaction_fn` seam, as it exists today, is not sufficient
as the retrieval-ingestion boundary.** `_run_with_transaction` invokes `post_transaction_fn()` from a
`finally` block, *after* `_finalize_transaction()` has already decided commit-vs-rollback and after
`session.close()` (`src/afterworlds/pipeline/orchestrator/service.py:3402-3483`). That `finally` fires
unconditionally — on successful commit, on rollback, on commit failure (mapped to `PIPELINE_ERROR`),
and even on the earlier `session.begin()` failure path before any turn exists — and the hook's own
exceptions are suppressed. It is a cleanup guarantee, not a commit-success / delivery-cleared boundary.
Its one current caller (the entitlement/credit proxy flush) tolerates this because a flush attempt
after a rolled-back turn is an accepted no-op for that use case; retrieval ingestion cannot tolerate
it, because ingesting rolled-back or blocked/refused prose as ordinary retrieval memory would violate
the Central Invariant above (delivery-cleared content only). An earlier Phase 1 draft of this ADR
stated Phase 2 could attach Chroma ingestion to this seam as-is; that statement is withdrawn.

**Ingestion gate (replaces the withdrawn "attach to `post_transaction_fn` as-is" language):** Chroma
retrieval-memory ingestion may be invoked only when all of the following hold:

- The outer transaction backing the turn has committed successfully — reaching the post-transaction
  `finally` block is not itself evidence of this.
- The committed result carries a delivery-cleared disposition eligible under Decision 6 — for v1
  story-memory ingestion, `DELIVERED` narrative turns only, further filtered by D6's mode-specific
  eligibility rules (Writing's `EXTRACTOR_ELIGIBLE` gate; RPG's roll-request and setup-confirmation
  marker/`PendingRollRequest` exclusions).
- Ingestion must never fire for `OOC_HANDLED`, `INTERACTION_REJECTED`, `BLOCKED_INPUT_SAFETY`,
  `BLOCKED_OUTPUT_SAFETY`, `BLOCKED_CONTRADICTION`, `BLOCKED_PENDING_ROLL`, `REFUSED_BY_PROVIDER`,
  `PIPELINE_ERROR`, a commit failure, or any rolled-back turn. `BLOCKED_PENDING_ROLL`
  (`src/afterworlds/pipeline/orchestrator/models.py:68`) is a pre-turn redirect returned before any
  Turn is persisted when the Sojourner owes a pending roll (`service.py:733-744`) — no Turn exists to
  ingest, the same structural reason `INTERACTION_REJECTED` is excluded. This is a disposition-deny-list
  completeness fix, not a change to the RPG roll-request marker rule above: a *delivered* roll-request
  announce turn (which does reach `_narrative_persist` and does get a `ROLL_REQUEST` marker) is a
  different case from this pre-turn redirect, and the two must not be conflated.
- The `turn_id` used to build ingestion IDs must be the **surviving** `OrchestrationResult.turn_id`
  returned after successful commit. A provisional `WriterResult.turn_id` is not sufficient — a
  provisional turn can still roll back before `_finalize_transaction` completes.

**Phase 2 implementation latitude, precisely bounded:** Phase 2 may satisfy this gate through either of
two mechanisms, and must not rely on the current `finally`-based `post_transaction_fn` unless its
semantics are changed to be success-only:

1. Introduce, or repurpose, a true after-commit / success-only orchestration callback that the
   orchestrator invokes conditionally — only once `_finalize_transaction()` has confirmed a commit and
   produced a delivery-cleared `OrchestrationResult` — rather than unconditionally from `finally`; or
2. Keep the existing post-transaction seam's timing, but gate the ingestion call inside it explicitly:
   inspect the final `OrchestrationResult` returned by `_finalize_transaction()` for the success
   disposition and a surviving `turn_id` before calling `retrieve`/upsert, and no-op otherwise.

Either mechanism must perform the gate check against the **post-finalization** result, never the
pre-transaction or provisional one. The current `post_transaction_fn`, unmodified, does not satisfy
either option on its own — it has no return-value inspection today and runs regardless of outcome.

**Phase 2 test obligation (ingestion gate), in addition to the Decision 6 marker-consistency test
above:** Phase 2 must add tests proving: (1) blocked/refused/error/rollback/commit-failure outcomes —
explicitly including `BLOCKED_PENDING_ROLL`, a pre-turn redirect with no Turn to ingest — never call
retrieval ingestion; (2) `OOC_HANDLED` and `INTERACTION_REJECTED` turns never call retrieval ingestion;
(3) `DELIVERED` turns that are D6-ineligible (Writing turns without `EXTRACTOR_ELIGIBLE`; RPG
roll-request or setup-confirmation turns) never call retrieval ingestion; (4) eligible, committed
`DELIVERED` narrative turns call ingestion exactly once.

**The RPG turn-category marker is not Chroma ingestion and is not the retrieval write trigger; it does
not use the post-commit seam or the ingestion gate above.** Per Decision 6 above, the marker row is
written at Turn creation time inside the existing CRD Issue 12c outer transaction — the same unit of work
as the provisional/surviving Turn — so a blocked/refused/errored Turn rolls back its marker with the
Turn. A post-boundary RPG narrative-path Turn that requires retrieval classification must not commit
markerless. Chroma ingestion is failure-isolated by design (Decision 7: logged and swallowed, never
blocking or reversing delivery) once past the ingestion gate; the marker write is deliberately **not**
failure-isolated in that sense — it lives inside the Turn's own transaction and fails or commits with
it. The ingestion gate described above governs Chroma ingestion only, never marker writes — these
remain two separate mechanisms. `StablePrefix` envelope shape, the CRD Issue 12c renderer's omission
behavior for empty payloads, and breakpoint placement (aside from what Decision 9 above already
resolves) are unchanged.

## `known_unknowns.md` Resolution Text

The **ChromaDB collection schema** entry moves from Open to Resolved: *"Collection topology, metadata
schema, chunking, embedding, retrieval defaults, eligibility/write-trigger rules, and
update/delete/reindex semantics are resolved by ADR-018 (this document). RPG setup-confirmation
turn-time classification required a new narrow sidecar carrier (`rpg_turn_retrieval_markers`) per the
Owner Decision recorded in ADR-018, since no existing signal qualified. Implementation proceeds only
after explicit owner acceptance of ADR-018 (Phase 2, CRD Issue 18)."*

The **stale FastAPI route-shape entry** the CRD Issue 18 spec asked Phase 1 to correct
("resolve before Issue 18 (or whenever the first route is needed)") no longer exists in
`known_unknowns.md` — it was already corrected in a prior commit
(`a076cc8`, predating this ADR) to read "Resolve during: Issue 19, before route implementation" with
no CRD Issue 18 reference. No edit is made for this item; it is recorded here per CLAUDE.md's instruction
not to resolve or silently no-op a drift between the spec and current repository state.

---

## Consequences

- **Correction: ChromaDB is not a new Phase 2 dependency — it is already a mandatory dependency today,
  with an open CVE gate Phase 2 must close.** `chromadb>=0.5` is already listed in `pyproject.toml`'s
  `[project].dependencies`, servicing the existing CRD Issue 5b interim rules-chunk vector path
  (`src/afterworlds/ingestion/vector_writer.py`, `ingestion_service.py`). `.github/workflows/ci.yml`'s
  `pip-audit` step currently carries `--ignore-vuln CVE-2026-45829` for ChromaDB, with a comment
  recording an owner decision (2026-06-05) that explicitly defers this CVE to CRD Issue 18: *"CRD Issue
  18, which owns the chromadb dependency design and will resolve it — either by upgrading to a patched
  release or by scoping chromadb as an optional dependency with a defined safe deployment path. Remove
  this `--ignore-vuln` only when Issue 18 closes this out."* Phase 2 must close this gate as part of
  CRD Issue 18 completion — it may not be silently left open or deferred again. Phase 2 must do one of:
  - Upgrade to a patched ChromaDB release (if one exists by Phase 2 implementation time) and remove the
    `--ignore-vuln CVE-2026-45829` entry from the `pip-audit` step; or
  - Move/scope ChromaDB behind an optional dependency, or an otherwise documented safe deployment path,
    with the audit ignore removed or explicitly re-justified according to the chosen path.

  If no patched release exists at Phase 2 implementation time, Phase 2 must record the owner-approved
  safe-deployment/optional-dependency decision in that PR's Architecture Notes rather than silently
  preserving the ignore. **CRD Issue 18 must not be considered complete while this CVE ignore remains
  unresolved or unaddressed.** This Phase 1 ADR does not resolve the dependency/security posture itself
  — it records the existing repo-state contradiction (this ADR previously said ChromaDB "is added...in
  Phase 2," which was incorrect) and the Phase 2 obligation to close it.
- The cross-turn cache-hit-rate regression accepted in Decision 9 is a measurable, monitorable cost;
  Phase 2 or a follow-on provider/cache issue may revisit breakpoint placement if empirical cache
  metrics (CRD Issue 14-adjacent) show the regression is unacceptable in practice.
- The RPG turn-category marker is the one schema addition Phase 2 makes to core RPG turn persistence;
  it is deliberately narrow (three values, one sidecar table, forward-only) to avoid becoming a
  general cross-mode turn taxonomy.
- Semantic rules retrieval remains non-authoritative in v1 (Decision 10); wiring it into any runtime
  decision path requires a future ADR, not a Phase 2 extension.
