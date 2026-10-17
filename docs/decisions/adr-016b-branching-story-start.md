# ADR-016b: Branching Story Start — Saved Setup, Distinct Begin Story, Atomic Opening

**Issue:** CRD Issue 21 Integration Prerequisite A ([contracts](../architecture/crd-issue-21-integration-prerequisites.md#prerequisite-a--branching-start-and-product-integration))
**Date:** 2026-10-16
**Status:** Accepted (Owner acceptance of the prerequisite contracts, 2026-10-16)
**Amends:** [ADR-016](adr-016-branching-mode.md) Decision 3 and the Branching setup route's promotion behavior. ADR-016's other decisions are unchanged.

---

## Context

ADR-016 Decision 3 routes Branching setup-phase turns through the prose Writer as ordinary
`DELIVERED` turns. The CRD Issue 19 setup route then promoted the story to `IN_PLAY` as soon as
interaction style and cadence were saved (PR #126 round 7). Nothing generated a first playable
beat or a first card set: a True CYOA story reached ordinary play with no selectable cards, so
its first input was always rejected, and Hybrid/True CYOA stayed disabled in the built app.

The Owner decided on 2026-10-16 that setup saves configuration and a separate **Begin story**
action starts play and generates the opening. This ADR records that extension. Decision 3 is
preserved as history: setup-phase turns remain lightweight setup-confirmation exchanges through
the prose Writer; they are not the playable opening.

## Decision 1: Setup saves; it never starts or resets play

`POST /api/stories/{id}/setup` validates and persists interaction style, cadence, length
preference and branch-count range. It never changes `play_status`.

- Freeform-only carries no branch-count range; saving Freeform-only clears it.
- A supplied range must be allowed for the effective style (`ALLOWED_RANGES_BY_STYLE`);
  otherwise `422 validation_failed` and nothing is written.
- A partially configured story may be saved. While it stays in `SETUP`, Begin reports what is
  missing. Once a story is `IN_PLAY`, a setup update must leave a complete, valid configuration
  (a card style keeps a valid range); it never demotes the story or clears its cards.

## Decision 2: Begin story is an explicit typed operation

`POST /api/stories/{id}/begin` means "generate the first playable beat". It is not a selection
against an empty card set, and it does not rely on the classifier finding a startup in prose.

Order of checks (no provider call or settlement before the last step):

1. Story exists, its mode is released (ADR-017b) and is Branching (`409 setup_state_conflict`
   otherwise).
2. Already `IN_PLAY` → `200` with `outcome = "already_started"` and the current persisted
   visible state. No access selection, provider call, Turn or deduction.
3. Configuration incomplete or invalid → `409 setup_required`, naming the missing field.
4. Ordinary access-path selection and turn anchor, then the orchestrator's start entry.

The route runs under the existing per-story lock, so repeated or concurrent Begin requests
serialize. Inside the turn's transaction the `SETUP → IN_PLAY` transition is a conditional
update of a row still in `SETUP`; if it is not, the opening rolls back typed.

## Decision 3: The opening runs the canonical pipeline with a code-owned start intent

The start entry resolves the production provider binding, then fixes a code-owned
`IntentClassificationResult` (`beat_milestone`, confidence 1.0) before context assembly. This
follows the RPG resume precedent (CRD Issue 15b, 15b-22): an operation with no new Sojourner
text is classified by code, not by asking the classifier about invented prose. Classification
still precedes context assembly (Architecture Invariant 3). The Turn's recorded input is the
code-owned marker `[Begin story]`.

Context is assembled once; the stable prefix is reused by every pass. A code-owned volatile
`story_start` ledger block tells the passes to open the story from persisted world/setup
context and any persisted story seeds, and that no player choice exists yet. Planner, Writer
(the typed `BranchingWriterService` for Hybrid/True CYOA, the prose Writer for Freeform-only),
conditional Safety, Extractor and Contradiction, and the existing transaction rules apply
unchanged.

## Decision 4: The opening, first cards and transition commit together

Only the start entry may generate cards without a preceding selection. The opening Turn, its
Story Bible changes, the first card set on the anchor Node's `BranchingNodeMetadata` (ADR-016
Phase G contract), the `SETUP → IN_PLAY` transition and its Rolling Summary eligibility fact
([ADR-006b](adr-006b-automatic-rolling-summary.md)) are written in the same outer transaction.
True CYOA's existing rule still applies: every beat, the opening included, must show a valid
card set.

A failed, refused or blocked opening rolls back: the saved configuration stays, the story stays
in `SETUP` with no opening or cards, nothing is ingested into Retrieval Memory and nothing is
deducted (existing non-billable failure rules). The typed outcome is shown without candidate
prose. A successful opening settles as an ordinary delivered hosted turn; BYOK never deducts.

## Decision 5: Committed cards are read back from persisted state

Turn responses and `GET .../visible-state` expose `play_status` and, for a card style, the
current committed card set and presentation state read from the anchor Node's
`BranchingNodeMetadata`. They are never assembled in the browser or scraped from prose. Reload
before start restores the ready-to-begin state; reload after start restores play and cards.

## Unchanged

True CYOA freeform rejection, selection and annotation validation, OOC configuration updates,
the classifier paraphrase limitation (Known Unknown), deferred `BranchTree` traversal and the
`branching_logic` labeled-edge boundary (ADR-016 Decision 6), Writing deferral (ADR-017b).

## Consequences

- `routes/setup.py` no longer requests `IN_PLAY`; the CRD Issue 19 tests that pinned promotion
  on setup change to pin non-promotion.
- New `POST /api/stories/{id}/begin` and `BeginStoryResponse`.
- `OrchestratorService.orchestrate_branching_start`.
- `BranchingVisibleState` gains `play_status`; its card fields are populated on reload.
- `create_app` wires `BranchingWriterService`, `BranchSelectionValidationService`,
  `BranchingOocConfigExtractorService` and `BranchingVisibleStateService`.
- The built app offers Hybrid and True CYOA with a range selector and a Begin story control.
