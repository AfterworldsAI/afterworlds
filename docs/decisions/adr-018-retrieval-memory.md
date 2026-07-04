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
`get_active_rule_slice` (Issue 5a) remains the sole deterministic mechanical authority (CLAUDE.md
invariant 8). Prose blocked by Safety, Contradiction, provider refusal, or pipeline error is never
written as ordinary retrieval memory.

## Context

Issue 8 reserved the seam: a `RetrievalMemoryProvider` protocol, a no-op default
(`NullRetrievalMemoryProvider`), and a named `retrieval_memory` field on `StablePrefix`. ADR-0010
Decision 4 explicitly deferred *real placement* of query-dependent retrieval results to Issue 18 and
flagged the cache-boundary tension this ADR resolves (see Decision 9 below). Issue 5b shipped an
interim rules-chunk vector path flagged for revision here. Issues 15–17 defined what a delivered turn
*is* per mode, including Writing's `WritingCanonEligibility` and RPG's `PendingRollRequest`.

Issue 18 is the one CRD issue with a mandatory ADR / owner checkpoint inside it. This document
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
  not a Phase 1 ADR defect, unless it exposes an actual contradiction between two parts of this
  document or between this document and the CRD Issue 18 spec.

---

## Decision 1 (D1) — Collection Topology

**Decision:** One shared `story_memory` collection with a mandatory `story_id` metadata filter on
every query, plus one `rules_corpus` collection per published Rules Package, absorbing/reindexing the
Issue 5b interim collection. Story memory and rules corpus are never mixed in one collection — that
separation is a spec constraint (narrative vs. mechanical canon authority), not an ADR choice.

**Rationale:** Per-story collections multiply Chroma overhead and make cross-story leakage a
*topology* property that silently degrades if any code path selects the wrong collection. A single
mandatory filter, enforced by one query-gate function every read path traverses, is testable in one
place rather than N.

## Decision 2 (D2) — Metadata Schema

**Decision:** Story-memory chunks carry `schema_version`, `story_id`, `node_id`, `turn_id`, `mode`,
`source_type`, `chunk_kind`, `chunk_index`, `chunk_count`, `created_at`, `content_hash`,
`embedding_model_id`. Rules-corpus chunks carry the Issue 5a provenance fields (`source_document`,
`source_locator_type`, `source_locator_value`) plus `rules_package_id`, `subsystem`,
`embedding_model_id`, `schema_version`.

`source_type` and `chunk_kind` are distinct typed fields and must not be collapsed into one:

- `source_type` is the provenance/origin class of the record — *where the content came from*. Typed
  enum, `DELIVERED_TURN_PROSE` in v1 (the only source Issue 18 ingests); extensible later to
  `STORY_BIBLE_ENTRY`, `CANON_PACK`, or other approved retrieval sources if and when those are scoped
  by a future issue, without schema migration. This field is reserved now so a future source-type
  addition is additive, not a schema change.
- `chunk_kind` is the semantic kind of chunk *within* that source — typed enum, `SCENE_PROSE` in v1
  (the only chunk kind Issue 18 produces, per Decision 3's one-chunk-per-turn-prose policy).

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
existing empty typed payload, which the Issue 12c renderer already omits — no placeholder block, no
cache-key pollution.

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
effective `WritingCanonEligibility == EXTRACTOR_ELIGIBLE`. Per Issue 17,
`WritingTurnRequest.canon_eligibility_override` is the only v1 carrier that can promote a turn — Writer
prose, classifier heuristics, prompt text, or `work_product_kind` alone never make a Writing turn
retrieval-indexable. `SETUP_CONFIRMATION` cannot carry `EXTRACTOR_ELIGIBLE`, so Writing setup
confirmations are excluded structurally without a second check.

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

Because no qualifying signal exists, Issue 18 adds the narrow RPG-only carrier described in the Owner
Decision below.

**RPG turn-category marker (Owner Decision):**

- A **sidecar table**, `rpg_turn_retrieval_markers` (do not add columns to the core `turns` table),
  written inside the existing Issue 12c outer transaction when the **narrative-path** Turn row is
  persisted — mirroring the Writing-mode pattern at `service.py:1651-1767` (a Phase-G-style block
  inside `_narrative_persist`, `service.py:1238`, gated on `story_mode is StoryMode.RPG`) — so a
  blocked/refused/errored narrative-path turn's marker rolls back with the turn. No orphan markers for
  never-delivered turns. **This write happens only on the narrative persist path, never on the OOC
  persist path (`_run_ooc()` / `_ooc_persist()`, `service.py:2142` / `service.py:2254`) — the two are
  separate persist functions, so the marker write is structurally absent for OOC turns, not merely
  unpopulated for them.**
- **Coverage is narrower than "every RPG turn."** The sidecar covers one row per **post-marker RPG
  narrative-path `DELIVERED` turn that reaches retrieval-eligibility classification** — i.e., the same
  turns Decision 6's write trigger considers for story-memory ingestion. RPG `OOC_HANDLED` turns are
  real persisted Turns, but they are persisted through `_ooc_persist()`, not `_narrative_persist()`, so
  they never reach the marker-writing block at all — the same D6 disposition/path gating that already
  excludes all `OOC_HANDLED` turns from retrieval (`RecentTurnReader` exclusion semantics) corresponds
  directly to which persist function runs. A missing marker on an RPG `OOC_HANDLED` turn is expected
  and is not an error; a missing marker on a post-marker RPG narrative-path `DELIVERED` turn that
  requires retrieval classification is an error (see the coverage invariant below).
- A typed category enum with exactly `ORDINARY_NARRATIVE`, `ROLL_REQUEST`, and `SETUP_CONFIRMATION` —
  unchanged; no OOC/non-indexed category is added. OOC turns do not need a fourth category because they
  are filtered out before marker classification, not classified into it.  No general cross-mode turn
  taxonomy, no new dispositions, no new passes, no prose heuristics, no UI/API surface.
- Rows are written once and never updated; deletion follows turn deletion.
- Consumed only by the Issue 18 retrieval eligibility predicate. No other reader in v1.
- **Forward-only.** Markers exist for turns created after the marker ships. Historical RPG turns are
  left unclassified rather than guessed — no retroactive classification from prose or current state.

**Era-boundary mechanism (pre-marker vs. post-marker), deterministic:**

| Turn era | Marker row | `PendingRollRequest.originating_turn_id` | Eligibility predicate outcome |
|---|---|---|---|
| Post-marker, ordinary narrative | `ORDINARY_NARRATIVE` | absent | Eligible |
| Post-marker, roll-request | `ROLL_REQUEST` | present | Excluded |
| Post-marker, setup confirmation | `SETUP_CONFIRMATION` | absent | Excluded |
| Post-marker, `OOC_HANDLED` | none (excluded before marker classification) | absent | Excluded (D6 disposition/path gating; never reaches marker lookup) |
| Pre-marker (no row exists) | absent (table did not exist / turn predates it) | absent | **Treated as `ORDINARY_NARRATIVE` — eligible** |
| Pre-marker roll-request | absent | present | Excluded (`PendingRollRequest` alone is sufficient and pre-dates the marker) |

Every post-marker RPG **narrative-path `DELIVERED` turn that reaches retrieval-eligibility
classification** gets exactly one marker row — this is the narrowed sidecar coverage rule stated
above — and it applies uniformly across all three categories, roll-request included. A post-marker
roll-request turn is never markerless: it carries `ROLL_REQUEST` in `rpg_turn_retrieval_markers` *and*
a `PendingRollRequest` row. These two signals are written independently (the marker at turn creation,
`PendingRollRequest` on the announce turn) but must agree for every such turn — that agreement is a
coverage invariant, not an eligibility mechanism. RPG `OOC_HANDLED` turns are outside this coverage
rule entirely: D6's disposition/path gating excludes them before marker classification is ever
reached, so they carry no marker row and none is required — this is not a gap in the sidecar, it is
the sidecar's scope.

**Predicate precedence vs. coverage invariant — two different things:**

- **Eligibility precedence:** `PendingRollRequest.originating_turn_id` is what the eligibility
  predicate actually checks to exclude roll-request turns, and it governs regardless of marker
  category. The marker governs setup-confirmation exclusion. `OOC_HANDLED` turns are excluded upstream
  of both signals by D6 disposition/path gating. An RPG turn with neither signal — i.e., a pre-marker
  historical turn — is treated as `ORDINARY_NARRATIVE` and is eligible.
- **Coverage invariant (post-marker, narrative-path `DELIVERED` turns only):** independent of which
  signal the predicate consults, every such turn must have exactly one marker row, and a post-marker
  roll-request turn's marker category must be `ROLL_REQUEST`. Marker coverage is a Phase 2 write-time
  obligation the eligibility predicate does not itself enforce; the predicate reads `PendingRollRequest`
  for its exclusion decision, but Phase 2 must not skip the sidecar write for roll-request turns on the
  theory that `PendingRollRequest` alone already gets the correct eligibility outcome. A pre-marker
  roll-request turn is the only case where marker absence is expected and correct for a narrative-path
  turn — it predates the sidecar entirely, so `PendingRollRequest` alone governs, per the era-boundary
  table above. RPG `OOC_HANDLED` turns are outside the coverage invariant's scope at every era, marker
  or no marker, because D6 gating removes them before classification, not because the sidecar failed to
  cover them.

**Rationale (ADR-ratified as a D6 sub-decision):** excluding unclassified turns would silently erase
retrieval memory for every pre-marker RPG story; including them admits at worst a bounded set of early
procedural chunks. Phase 2's consistency test must assert: (1) every post-marker RPG narrative-path
`DELIVERED` turn that reaches retrieval classification has exactly one marker row; (2) RPG
`OOC_HANDLED` turns do not require and do not receive marker rows, and are excluded before marker
lookup by D6 disposition/path gating rather than by an absent or mismatched marker; (3) for post-marker
narrative-path turns, a marker of category `ROLL_REQUEST` has a corresponding `PendingRollRequest` row
and vice versa, and marker category and `PendingRollRequest` presence never disagree. Pre-marker turns
are exempt from (1) and (3) by definition — the sidecar did not exist yet — and remain governed solely
by the era-boundary table's pre-marker rows.

This exclusion applies specifically to **RPG** setup confirmations, not all mode setup turns:
Branching setup confirmations remain eligible as ordinary story-architect narrative turns (Issue 16),
and Writing setup confirmations are already excluded structurally as described above. The consumed-roll
turn that narrates the outcome is the narrative record and is indexed normally. If RPG setup narration
proves worth indexing later, that requires a typed carrier, not prose inspection — a future D6
sub-decision.

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
recent-turn tail), mirroring the Issue 15 `RuleSliceRequest` precedent. The Context Builder gains no
inference logic; it must not infer retrieval-query contents itself. The `StablePrefix` envelope shape
does not change. Query-context discipline: the query builder applies the same narrative/OOC filtering
as recent-turn handling (`RecentTurnReader` exclusion semantics), so OOC, config, and support turns
never leak into retrieval-query context.

**Phase 1 source-inspection finding:** the live `RetrievalMemoryProvider.retrieve(story_id: UUID,
query: str)` protocol (`src/afterworlds/services/context_builder.py:150-163`) already accepts a
`query: str` parameter. `NullRetrievalMemoryProvider.retrieve()` (lines 194-202) ignores both
arguments and returns an empty payload, and `build_stable_prefix()` (lines 395-404) never calls
`self._retrieval_memory.retrieve(...)` at all — it always constructs `RetrievalMemoryPayload()`
literally. **The existing protocol signature already carries a query string; no additive parameter is
needed at the protocol level.** What Phase 2 must add is the call site (the orchestrator/Context
Builder actually invoking `retrieve()` with a built query) and, per the Issue 15 precedent, an
orchestrator-constructed request object analogous to `RuleSliceRequest`
(`src/afterworlds/models/rules_package.py:407-417`, built at
`src/afterworlds/pipeline/orchestrator/service.py:531` and threaded through `_build_context` /
`ContextBuilderService.assemble()` as an additional keyword parameter). This finding resolves the
spec's stated fork ("existing signature sufficed vs. additive pass-through") in favor of **existing
signature sufficed**, at the protocol level; the exact shape of the orchestrator-side request object
and its threading through `assemble()`/`build_stable_prefix()` remains Phase 2 implementation detail,
not an owner decision, per the spec's own framing of D8 as "repo-state-resolved at implementation
time."

## Decision 9 (D9) — Cache Interaction: Resolving ADR-0010 Decision 4

**Background:** ADR-0010 Decision 4 ("Retrieval Memory Cache Boundary Reconciliation") identified that
materializing query-dependent retrieval results inside the cacheable stable prefix is a
**cache-boundary violation**: stable-prefix cost economics assume a ~88% cache hit rate under extended
TTL, and a per-turn-varying retrieval block would collapse cross-turn cache reuse for every turn that
retrieves anything. ADR-0010 deliberately did **not** decide where retrieval belongs — it listed the
volatile suffix, a separate (non-cacheable) retrieval block, or "elsewhere" as candidate placements
and explicitly deferred the real decision to Issue 18: *"Issue 18 owns retrieval implementation and
cache-boundary reconciliation."*

**Phase 1 source-inspection finding:** the Issue 12c shared renderer places the cache breakpoint on
the **last block** in canonical stable-prefix order (Story Bible → Rolling Summary → Rules Slice →
Retrieval Memory), not a fixed position
(`src/afterworlds/pipeline/_stable_prefix_renderer.py:96-161`). Retrieval memory is last in that
order, so once Issue 18 populates a non-empty payload, it becomes the final block and **inherits the
cache breakpoint** — i.e., retrieval memory sits inside the cached/TTL'd stable prefix rather than
after it.

**Decision:** This ADR resolves the placement question ADR-0010 Decision 4 deferred, choosing to keep
retrieval memory inside the existing `StablePrefix` envelope, under the existing breakpoint, rather
than the volatile suffix or a second, separately-cached block.

**Owner Decision — retrieval pass scope:** Retrieval Memory is shared stable-prefix context, available
to every provider-backed pass that renders the stable prefix — Planner, Writer, Input Safety, Output
Safety, Extractor, and Contradiction. It is **not** Writer-only in v1; all-pass visibility is
intentional, not an unreviewed side effect of choosing `StablePrefix` placement. Phase 2 must not
create a separate Writer-only retrieval placement or channel. Concretely:

- Contradiction may use retrieval memory as part of continuity checking when Issue 18 supplies it, the
  same way it already reasons over the rest of the stable prefix (Story Bible, Rolling Summary, Rules
  Slice).
- Safety (Input Preflight and Output Audit) receives retrieval memory as context whenever its renderer
  includes the stable prefix, exactly as it already receives the rest of stable-prefix content. The
  Safety **target** text being evaluated remains the explicit input or output text under audit;
  retrieval content is contextual background for that evaluation, never itself the audited target.
- Planner and Extractor consume it as ordinary stable-prefix context, consistent with how they already
  consume the rest of `StablePrefix`.

**Rationale for `StablePrefix` over the volatile suffix or a second breakpoint:** the volatile suffix
and a second cache breakpoint are both rejected, but not on the grounds that retrieval is Writer-only
context — that rationale is incoherent once `StablePrefix` placement (and the all-pass visibility it
carries) is accepted. Instead:

- Issue 8 reserved the `StablePrefix.retrieval_memory` seam; this ADR fills the reserved seam rather
  than inventing a new one.
- Issue 12c already has one shared stable-prefix renderer that every provider-backed pass calls; a
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
  routing work — Issue 14-adjacent — not Phase 2 implementation license.

**Consequence, stated plainly:** a populated retrieval block varies per turn and **will reduce
cross-turn cache reuse** for any turn that retrieves non-empty results, working against the ~88% hit
rate the CRD cost model assumes for those turns specifically. Issue 18 accepts this consequence as the
cost of the simpler envelope. What is preserved is **intra-turn** stable-prefix reuse across the
provider-backed passes within a single turn — the economy the once-per-turn invariant (CLAUDE.md
invariant 7) actually guarantees, and which is orthogonal to cross-turn cache-hit economics. The Issue
12c structural-identity test must be extended to prove byte-identical rendering with a *populated*
retrieval block. Issue 18 does not move the breakpoint, add a second breakpoint, split stable-prefix
rendering, or change provider-adapter behavior. Any future optimization of breakpoint placement or
cache strategy (e.g., moving retrieval below a second breakpoint to restore cross-turn reuse for the
non-retrieval portion) is Issue 14-adjacent provider/cache work, not retrieval-memory implementation,
and would need its own ADR amendment.

## Decision 10 (D10) — Rules-Corpus Vector Use

**Decision:** Issue 18 finalizes the rules collection schema, reindexes the Issue 5b interim
collection into it, and exposes a typed semantic rules-lookup method that is internal/admin diagnostic
or discovery support only in v1. No Context Builder, RPG adjudication loop, Writer, Planner, pass
service, or runtime mechanical decision may consume semantic rules retrieval as authority. Runtime
rule inclusion remains exclusively through `get_active_rule_slice`. Wiring semantic rules discovery
into any runtime path — even as a "hint" — is a future issue plus ADR.

## Decision 11 (D11) — Update/Delete/Reindex Semantics

**Decision:** In-place re-upsert keyed by deterministic IDs, with orphan sweep by `story_id` filter,
over a rebuild-into-fresh-then-swap strategy. See the mutation table below.

| Operation | Semantics |
|---|---|
| Turn ingested | Upsert by deterministic ID; re-ingesting the same turn replaces byte-identically — zero duplicates. |
| Turn re-ingested after prose correction (future) | Upsert replaces document and its metadata bundle atomically. |
| Turn deleted | Delete all chunks whose IDs derive from that `turn_id`. |
| Story deleted / Issue 22 deletion request | Delete by `story_id` metadata filter across story-memory collections; a post-delete count-zero verification is part of the operation's contract. |
| Reindex (story or corpus) | Rebuild from SQLite-authoritative content; embedding-model change forces reindex. |
| Retrieval config change (top_k, threshold) | Configuration only; no vector mutation. |
| Rules package republished | Issue 5b re-ingestion remains idempotent; Issue 18 reindex refreshes the rules collection without mutating Issue 5a source records. |
| RPG turn-category marker written | Insert-once at turn creation inside the outer transaction; never updated; rolls back with a blocked turn. |
| RPG turn deleted | Marker row deleted with its turn; no orphaned markers. |
| Historical pre-marker RPG turn | No-op — never retroactively classified; predicate treats it as `ORDINARY_NARRATIVE`. |

**Idempotence keys are semantic, never generated.** Story-memory chunk ID:
`story:{story_id}:turn:{turn_id}:chunk:{index}`. Rules-corpus chunk ID derives from
`rules_package_id` + the Issue 5a chunk identity. Random UUIDs are prohibited as dedupe keys anywhere
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
  `BLOCKED_OUTPUT_SAFETY`, `BLOCKED_CONTRADICTION`, `REFUSED_BY_PROVIDER`, `PIPELINE_ERROR`, a commit
  failure, or any rolled-back turn.
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
above:** Phase 2 must add tests proving: (1) blocked/refused/error/rollback/commit-failure outcomes
never call retrieval ingestion; (2) `OOC_HANDLED` and `INTERACTION_REJECTED` turns never call
retrieval ingestion; (3) `DELIVERED` turns that are D6-ineligible (Writing turns without
`EXTRACTOR_ELIGIBLE`; RPG roll-request or setup-confirmation turns) never call retrieval ingestion; (4)
eligible, committed `DELIVERED` narrative turns call ingestion exactly once.

**The RPG turn-category marker is not Chroma ingestion and is not the retrieval write trigger; it does
not use the post-commit seam or the ingestion gate above.** Per Decision 6 above, the marker row is
written at Turn creation time inside the existing Issue 12c outer transaction — the same unit of work
as the provisional/surviving Turn — so a blocked/refused/errored Turn rolls back its marker with the
Turn. A post-marker RPG narrative-path Turn that requires retrieval classification must not commit
markerless. Chroma ingestion is failure-isolated by design (Decision 7: logged and swallowed, never
blocking or reversing delivery) once past the ingestion gate; the marker write is deliberately **not**
failure-isolated in that sense — it lives inside the Turn's own transaction and fails or commits with
it. The ingestion gate described above governs Chroma ingestion only, never marker writes — these
remain two separate mechanisms. `StablePrefix` envelope shape, the Issue 12c renderer's omission
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
no Issue 18 reference. No edit is made for this item; it is recorded here per CLAUDE.md's instruction
not to resolve or silently no-op a drift between the spec and current repository state.

---

## Consequences

- ChromaDB is added as a dependency in Phase 2 through normal dependency/pip-audit lanes; no dependency
  change accompanies this ADR.
- The cross-turn cache-hit-rate regression accepted in Decision 9 is a measurable, monitorable cost;
  Phase 2 or a follow-on provider/cache issue may revisit breakpoint placement if empirical cache
  metrics (Issue 14-adjacent) show the regression is unacceptable in practice.
- The RPG turn-category marker is the one schema addition Phase 2 makes to core RPG turn persistence;
  it is deliberately narrow (three values, one sidecar table, forward-only) to avoid becoming a
  general cross-mode turn taxonomy.
- Semantic rules retrieval remains non-authoritative in v1 (Decision 10); wiring it into any runtime
  decision path requires a future ADR, not a Phase 2 extension.
